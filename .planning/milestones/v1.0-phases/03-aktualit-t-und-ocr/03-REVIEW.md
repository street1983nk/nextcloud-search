---
phase: 03-aktualit-t-und-ocr
reviewed: 2026-09-01T18:15:11Z
depth: standard
files_reviewed: 59
files_reviewed_list:
  - .github/workflows/integration.yml
  - backend/appinfo/info.xml
  - backend/pyproject.toml
  - backend/src/findling/config.py
  - backend/src/findling/extract/dispatch.py
  - backend/src/findling/extract/errors.py
  - backend/src/findling/extract/image.py
  - backend/src/findling/extract/ocr.py
  - backend/src/findling/extract/pdf.py
  - backend/src/findling/extract/raster.py
  - backend/src/findling/extract/sandbox.py
  - backend/src/findling/extract/text.py
  - backend/src/findling/index/writer.py
  - backend/src/findling/main.py
  - backend/src/findling/nc/client.py
  - backend/src/findling/nc/files.py
  - backend/src/findling/nc/queue.py
  - backend/src/findling/store/repo.py
  - backend/src/findling/store/schema.sql
  - backend/src/findling/worker/poller.py
  - backend/src/findling/worker/reconcile.py
  - backend/tests/test_acl_prefilter.py
  - backend/tests/test_allowlist_parity.py
  - backend/tests/test_config.py
  - backend/tests/test_extract_documents.py
  - backend/tests/test_extract_errors.py
  - backend/tests/test_files_client.py
  - backend/tests/test_index_writer.py
  - backend/tests/test_lifecycle.py
  - backend/tests/test_ocr.py
  - backend/tests/test_php_trust_boundary.py
  - backend/tests/test_poller.py
  - backend/tests/test_queue_client.py
  - backend/tests/test_readonly_gate.py
  - backend/tests/test_reconcile.py
  - backend/tests/test_sandbox.py
  - backend/tests/test_store_repo.py
  - docs/german-analyzer.md
  - docs/ocr.md
  - docs/reconcile.md
  - docs/testing.md
  - php/lib/AppInfo/Application.php
  - php/lib/BackgroundJobs/SubtreeExpandJob.php
  - php/lib/Controller/GatewayController.php
  - php/lib/Controller/QueueController.php
  - php/lib/Controller/ReconcileController.php
  - php/lib/Db/QueueFile.php
  - php/lib/Db/QueueMapper.php
  - php/lib/Listener/FileEventListener.php
  - php/lib/Listener/ShareEventListener.php
  - php/lib/Migration/Version001000Date20260902000000.php
  - php/lib/Search/Provider.php
  - php/lib/Service/FileStateService.php
  - php/lib/Service/QueueService.php
  - php/lib/Service/StorageService.php
  - scripts/ci/slow_backend.py
  - scripts/dev/build_corpus.py
  - testdata/CORPUS.md
  - testdata/fonts/COPYING.dejavu
findings:
  critical: 2
  warning: 4
  info: 3
  total: 9
status: issues_found
---

# Phase 3: Code-Review-Bericht (Aktualität und OCR)

**Geprüft:** 2026-09-01T18:15:11Z
**Tiefe:** standard
**Dateien:** 59
**Status:** issues_found

## Narrative Findings (AI-Reviewer)

### Zusammenfassung

Die Phase-3-Implementierung ist handwerklich ungewöhnlich sorgfältig: geschlossene Listen an jeder Grenze, Fail-closed-Validierung der OCS-Antworten, die Reihenfolge Commit vor Verdikt vor Acknowledgement ist konsequent durchgezogen, die Sandbox- und OCR-Deckelkaskade ist gemessen statt geraten, und die Trust-Boundary der PHP-Routen ist per Gate abgesichert. Die Tests decken Fehler- und Negativpfade breit ab.

Trotzdem gibt es zwei kritische Lücken, beide an Nahtstellen zwischen zwei Komponenten, also genau dort, wo Einzeltests grün bleiben: Der Reconcile verkeilt sich dauerhaft, sobald eine Scheibe mehr als 256 Funde liefert (Slice-Größe 500 gegen Listen-Limit 256 des Controllers), und die OCR-Übergabe geht bei einem transienten Requeue-Fehler oder einem Absturz im falschen Fenster still und dauerhaft verloren. Dazu kommen vier Warnungen, darunter zwei, die die Reparaturgarantie des Reconcile (IDX-04/IDX-05) für Teilmengen der Dateien aushebeln. Die als zurückgestellt markierten Punkte (TIFF-Frist im Inhaltszweig, ocr_used für Bilder, wiederhergestellter Ordner, LOCK_TIMEOUTS) wurden nicht erneut gemeldet.

## Kritische Befunde

### CR-01: Reconcile verkeilt sich dauerhaft, wenn eine Scheibe mehr als 256 Funde liefert

**Datei:** `backend/src/findling/worker/reconcile.py:396-411`, `backend/src/findling/nc/queue.py:382-406`, `php/lib/Controller/QueueController.php:77` und `php/lib/Controller/QueueController.php:334-350`
**Problem:** `Reconcile._hand_over` reicht die stale- und missing-Listen einer Scheibe in je einem einzigen `requeue`-Aufruf ein, ohne zu chunken. `QueueController::MAX_LIST_LENGTH` ist seit Plan 03-14 auf 256 gesenkt (vorher 1000), `intList` lehnt längere Listen komplett mit HTTP 400 ab. Die Standard-Slice-Größe ist aber 500 (`RECONCILE_SLICE`, `config.py:287`), und die missing-Liste ist auf der letzten Seite eines Mounts sogar unbegrenzt: `gone_in_range` läuft bei `final=True` ohne obere Grenze über alle lokal bekannten Dateien des Storage.

Konsequenz: Bei mehr als 256 Funden pro Scheibe antwortet der Controller 400, `DocumentQueue.requeue` liefert `ok=False`, `_hand_over` beendet die Runde mit `ROUND_UNAVAILABLE` und der Cursor bewegt sich nicht (das ist bei einem Transportfehler richtig, hier aber deterministisch reproduzierbar). Jede folgende Runde liest dieselbe Seite, produziert dieselbe zu lange Liste und scheitert erneut, für immer, mit Backoff bis maximal eine Stunde. Das trifft exakt die Szenarien, für die der Reconcile existiert (docs/reconcile.md): Backup-Restore oder neuer Mount (bis zu 500 unbekannte Dateien pro Seite werden alle stale) und Massenlöschung von mehr als 256 Dateien bei verpassten Events (missing auf der letzten Seite unbeschränkt). Kein Test deckt Listen über 256 ab; der CI-Job `reconcile-and-dach` arbeitet mit drei Änderungen.
**Fix:**
```python
# reconcile.py, _hand_over: in Bänder unterhalb des Controller-Limits zerlegen
_REQUEUE_BAND = 200  # < QueueController::MAX_LIST_LENGTH (256)

for file_ids, kind in ((stale, KIND_CONTENT), (missing, KIND_DELETE)):
    for start in range(0, len(file_ids), _REQUEUE_BAND):
        band = list(file_ids[start : start + _REQUEUE_BAND])
        result = await queue.requeue(band, kind=kind)
        if not result.ok:
            ...
            return False
```
Zusätzlich einen Test mit mehr als 256 Funden pro Scheibe ergänzen und das Limit auf beiden Seiten aus einer benannten Konstante herleiten (dieselbe Drift-Klasse, gegen die die Allowlist-Parität schon ein Gate hat).

### CR-02: OCR-Übergabe geht bei Requeue-Fehler oder Absturz im Fenster zwischen Schritt 3 und 3b still und dauerhaft verloren

**Datei:** `backend/src/findling/worker/poller.py:633-662` (`_goes_to_the_ocr_track`), `backend/src/findling/worker/poller.py:664-678` (`_hand_over`), Ablauf in `run_once` (Zeilen 426-434)
**Problem:** Der Schutz gegen die Endlos-Übergabe (T-03-704) stützt sich auf das gespeicherte Verdikt: Steht in der State-DB bereits `skipped(no_text_layer)` mit demselben Content-Hash, antwortet `_goes_to_the_ocr_track` False. Das Verdikt wird aber in Schritt 3 (`_record_verdicts`) geschrieben, BEVOR in Schritt 3b der Requeue läuft. Schlägt der Requeue fehl (Netzwerkfehler; `_hand_over` gibt nur 0 zurück und loggt) oder stirbt der Container zwischen Schritt 3 und 3b, dann kommt die Zeile nach dem Lock-Timeout als content-Job zurück, die Textpasse liefert wieder `no_text_layer`, der Guard findet jetzt das gespeicherte Verdikt mit gleichem Hash, antwortet False, und die Zeile wandert in `done` und wird acknowledged. Der Scan bleibt für immer `skipped(no_text_layer)`, obwohl OCR eingeschaltet ist.

Der Log-Text in `_hand_over` ("they run into the lock timeout" und werden "handed over by a later pass") beschreibt ein Verhalten, das der Guard genau verhindert. Der Reconcile repariert das auch nicht: das ETag der Datei ist unverändert, `known_etags` liefert einen Treffer, die Datei ist nicht stale. Laut `testdata/CORPUS.md` (Zeilen 37-40) ist `skipped(no_text_layer)` seit Phase 3 ausdrücklich kein zulässiger Endzustand mehr; genau dieser tritt hier dauerhaft ein, ohne dass ein Zähler es zeigt. Das ist die stille Fehlerklasse, gegen die das Projekt gebaut ist. Der Test `test_a_requeue_that_does_not_reach_nextcloud_does_not_end_the_pass` prüft nur, dass der Pass weiterläuft, nicht, dass die Datei die OCR-Spur jemals erreicht.
**Fix:** Der Guard soll nur die Wiederholung innerhalb desselben Zustands verhindern, nicht die Nachholung einer fehlgeschlagenen Übergabe. Da `requeueAs` die Zeile bei Erfolg auf `kind=ocr` umstellt (sie kommt also nie wieder als content-Job zurück), kann ein erneut als content eintreffender Job mit gespeichertem `no_text_layer`-Verdikt bei aktivem OCR gefahrlos erneut übergeben werden:
```python
if outcome.state is not State.SKIPPED or outcome.reason is not Reason.NO_TEXT_LAYER:
    return False
if not self._ocr_enabled:
    return False
# Ein content-Job, der hier ankommt, ist entweder der erste Fund oder eine
# fehlgeschlagene Übergabe: bei Erfolg wäre die Zeile kind=ocr und liefe
# nie wieder durch diesen Zweig. Also immer übergeben.
return True
```
Falls der Guard aus anderen Gründen bleiben soll, muss die Übergabe alternativ VOR dem Verdikt-Schreiben laufen oder der Requeue-Fehler die Acknowledgement-Aufnahme der betroffenen Zeile verhindern. Test ergänzen: Requeue schlägt fehl, Zeile kommt als content zurück, zweiter Pass muss erneut übergeben.

## Warnungen

### WR-01: requeueAs-erzeugte Zeilen tragen storage_id/root_id 0 und vergiften den Zustand der reparierten Dateien

**Datei:** `php/lib/Db/QueueMapper.php:497-514`, `php/lib/Service/QueueService.php:440-441`, `backend/src/findling/store/repo.py:150-166`
**Problem:** `requeueAs` legt für Dateien ohne Queue-Zeile neue Zeilen mit `storage_id=0` und `root_id=0` an. `QueueService::describe` liefert `storageId`/`rootId` aus der Zeile (nicht aus dem aufgelösten Node), und der Container überschreibt beim `record()` per Upsert die bislang korrekte `storage_id` mit 0 (`_RECORD_SQL` setzt `storage_id = excluded.storage_id`). Der einzige Erzeuger solcher Zeilen ist ausgerechnet der Reconcile (Plan 03-12), dessen Kommentar in `requeueAs` das Problem selbst benennt ("has to widen this signature rather than letting a zero travel"), das aber nie umgesetzt wurde.

Konsequenzen: (a) Jede vom Reconcile reparierte Datei (stale oder Restore ohne vorhandene Queue-Zeile) steht danach mit `storage_id=0` in der State-DB. Die Löschregel `gone_in_range(storage_id, ...)` fragt aber je echtem Storage; eine spätere Löschung dieser Datei ohne Event wird nie mehr erkannt. Damit bricht IDX-05 genau für die Dateien, die der Reconcile schon einmal angefasst hat, und der Schaden akkumuliert mit jedem Zyklus. (b) `FIELD_STORAGE_ID` im Tantivy-Index wird 0, was jede spätere Pro-Storage-Auswertung oder einen Pro-Storage-Reset verfälscht. Verschärfend: Bei einem Ordner-Move über eine Mount-Grenze (Datei-Ids bleiben erhalten, Storage wechselt) laufen die betroffenen Dateien über den Umweg Löschung-plus-Restore ebenfalls in dieses Loch.
**Fix:** In `describe()` storage und root für content/metadata/ocr aus dem aufgelösten Node bzw. dessen Mountpoint ableiten, wenn die Zeile 0 trägt (oder grundsätzlich, der Node ist ohnehin da); alternativ die Requeue-Signatur um storage/root erweitern, wie der Kommentar es fordert.

### WR-02: Fast-Path aktualisiert das gespeicherte ETag nicht; berührte, inhaltsgleiche Dateien werden vom Reconcile jede Nacht neu heruntergeladen, für immer

**Datei:** `backend/src/findling/worker/poller.py:546-558`, `backend/src/findling/worker/reconcile.py:364-374`
**Problem:** Der Fast-Path (`is_unchanged` True) schreibt nur `replace_acl` und acknowledged die Zeile; `record()` läuft nicht, das gespeicherte ETag (und mtime/path) bleibt alt. Ein `touch`, ein Client-Sync mit identischen Bytes oder jede andere ETag-Änderung ohne Inhaltsänderung erzeugt so eine permanente Diskrepanz: Der nächtliche `_stale_of`-Vergleich sieht altes gespeichertes ETag gegen neues Live-ETag, reiht die Datei als content ein, der Poller lädt sie vollständig herunter, der Hash ist gleich, der Fast-Path acknowledged ohne ETag-Update, und der nächste Zyklus beginnt von vorn. Pro betroffener Datei ein voller Download je Reconcile-Zyklus, unbegrenzt oft. Auf einer Instanz mit periodischen touch-artigen Zugriffen wird der "billige" Abgleich so zum nächtlichen Massen-Download; das widerspricht der Selbstheilungs-Argumentation ("repariert sich mit der nächsten Runde").
**Fix:** Im Fast-Path das ETag (und die übrigen Metadaten) nachziehen, ohne den Verdikt-Zähler zu verfälschen, z. B. ein schmales `UPDATE files SET etag=?, mtime=?, path=?, title=? WHERE file_id=? AND deleted_at IS NULL` als eigene Store-Methode, aufgerufen direkt neben dem `replace_acl` des Fast-Path. Test: content-Job mit gleichem Hash, aber neuem ETag; danach darf `_stale_of` die Datei nicht mehr melden.

### WR-03: Eine per Seiten-Timeout verlorene Seite ist im Verdikt unsichtbar; das widerspricht D-08

**Datei:** `backend/src/findling/extract/ocr.py:161-170`, `backend/src/findling/extract/image.py:187-202`
**Problem:** Verliert der OCR-Lauf einzelne Seiten durch `PageTimeout` (nicht alle), wird `lost` gezählt, aber `cut` nicht gesetzt: Das Dokument endet als `indexed` ohne `truncated`. Ein Dokument, dem die Hälfte seiner Seiten fehlt, ist damit exakt das "quietly thin result", das der Modulkopf und D-08 ausschließen ("a partial result is visible as such"). Der Test `test_a_page_over_the_time_cap_is_dropped_and_the_loop_goes_on` pinnt `reason is None` und zementiert die Lücke. Der Nutzer und die Statusseite von Phase 4 können ein vollständiges nicht von einem löchrigen Dokument unterscheiden, und kein späterer Lauf holt die verlorene Seite nach (Hash unverändert).
**Fix:** In `_read_document` und `_read_frames` `truncated=cut or lost > 0` an `_verdict` übergeben (und den Test entsprechend anpassen):
```python
if attempted > 0 and lost == attempted:
    return ExtractionOutcome.failed(Reason.TIMEOUT)
return _verdict("\n".join(parts), truncated=cut or lost > 0)
```

### WR-04: Der zulässige Maximalwert von FINDLING_OCR_JOB_SECONDS kollidiert mit dem OCR-Lock-Timeout und reproduziert den Stuck-Claim-Fehler

**Datei:** `backend/src/findling/config.py:254` (`OCR_JOB_SECONDS_RANGE = (1, 1800)`), `backend/src/findling/config.py:239` (Margin 60), `php/lib/Db/QueueMapper.php:107-113` (`LOCK_TIMEOUTS[ocr] = 1800`), `php/lib/Service/QueueService.php:74-80` (`KIND_BATCH[ocr] = 2`)
**Problem:** Die Bounded-Range existiert laut eigenem Kommentar genau dafür, dass "a job budget above the queue lock timeout" nicht passieren kann (T-03-503). Sie lässt aber 1800 zu, und `info.xml` dokumentiert "zwischen 1 und 1800" als gültig. Bei 1800 ist schon die harte Frist eines EINZELNEN Jobs 1860 s und liegt über dem 1800-s-Lock; ein Claim von zwei OCR-Jobs (KIND_BATCH) kann bis etwa 3720 s legitim arbeiten. Die Zeilen erscheinen währenddessen wieder als frei, kassieren Retries und enden als `failed(repeatedly_stuck)`, während korrekt gearbeitet wird; das ist wortgleich der Fehler, den der Kommentar zu `LOCK_TIMEOUTS` beschreibt. Ein Admin, der den dokumentierten Maximalwert setzt, baut den Fehler also mit einer als gültig deklarierten Einstellung wieder ein.
**Fix:** Obergrenze so wählen, dass `KIND_BATCH[ocr] * (job + Margin) < LOCK_TIMEOUTS[ocr]` gilt (bei den heutigen Konstanten also maximal etwa 840), oder die Range-Verletzung wenigstens mit einer Warnung quittieren, die den Lock-Timeout benennt; `info.xml`-Beschreibung im selben Commit anpassen.

## Hinweise

### IN-01: Widersprüchliche Kommentare zur Zahl der kaputten PDFs im Workflow

**Datei:** `.github/workflows/integration.yml:863` und `.github/workflows/integration.yml:1212`, `testdata/CORPUS.md:17-18`
**Problem:** Zeile 863 spricht von "five of the twelve deliberately broken PDFs", Zeile 1212 von "five of the ten broken ones"; CORPUS.md nennt "ten more PDFs that are broken in ten different ways". Die Zähler selbst stimmen (failed=6), aber ein Leser, der den Kommentaren traut, rechnet falsch nach.
**Fix:** Beide Kommentare auf die Zählung von CORPUS.md vereinheitlichen.

### IN-02: FileEventListener liest die Dateigröße auch für Löschungen, vor der Ausnahme

**Datei:** `php/lib/Listener/FileEventListener.php:356`
**Problem:** `$size = (int)$node->getSize();` läuft unbedingt, also auch für `kind=delete`, wo der Wert gar nicht verwendet wird (Zeile 374 übergibt 0). Wirft `getSize()` auf einem bereits gelöschten Node (NonExistingFile ohne vollständige FileInfo, je nach Storage-Backend) eine Exception, fängt der äußere Guard sie ab und die Löschung geht bis zum nächsten Reconcile-Zyklus verloren, obwohl alle für die Löschung nötigen Daten längst vorlagen.
**Fix:** Die Größe nur im Nicht-Löschzweig lesen: `$size = $isDeletion ? 0 : (int)$node->getSize();`.

### IN-03: failed(repeatedly_stuck) erreicht die Container-State-DB nie; der Reconcile reiht solche Dateien jede Nacht erneut ein

**Datei:** `php/lib/Service/QueueService.php:151-154` und `php/lib/Service/QueueService.php:571-574`, `php/lib/Db/QueueMapper.php:487`, `backend/src/findling/worker/reconcile.py:364-374`
**Problem:** Gibt der Claim eine Zeile nach drei Versuchen als `failed(repeatedly_stuck)` auf, landet das Verdikt nur in `findling_file_state` (PHP). Die Container-State-DB hat für diese Datei keine Zeile (der Container hat sie nie fertig verarbeitet), also meldet `known_etags` nichts, `_stale_of` reiht sie als content ein, `requeueAs` setzt die Retries auf 0 zurück, und der Zyklus Claim, Aufgeben, nächtliches Wiedereinreihen wiederholt sich unbegrenzt. Pro Datei und Nacht ist das begrenzter Aufwand, aber die Give-up-Regel wird für Reconcile-gefundene Dateien nie final, und die Statusseite zählt dieselbe Datei potenziell wechselnd.
**Fix:** Entweder das PHP-seitige Verdikt beim Reconcile berücksichtigen (z. B. Slice-Antwort um "hat finalen failed-Zustand" ergänzen) oder bewusst dokumentieren, dass repeatedly_stuck-Dateien nächtlich einen erneuten Versuch bekommen; im zweiten Fall sollte der Retry-Reset in `requeueAs` für diesen Pfad überdacht werden.

---

## Behebung (01.09.2026, gsd-code-fixer)

Alle 6 Findings im Scope Critical + Warning wurden behoben, je Finding ein
atomarer Commit auf main, Gates grün (ruff check + format, 703 passed /
11 skipped, pyright 0 errors, php -l):

- CR-01: `7d334bf` requeue in Bändern von 200 unter MAX_LIST_LENGTH 256,
  Paritätstest liest die PHP-Konstante.
- CR-02: `bc371b0` Redelivery-Blockade in _goes_to_the_ocr_track entfernt;
  Begründung, warum T-03-704 nicht zurückkehren kann, steht im Commit-Text.
- WR-01: `77db129` storage_id/root_id=0 werden in QueueService::describe aus
  dem aufgelösten Node repariert.
- WR-02: `1ddc806` neue Store-Methode refresh_meta aktualisiert das ETag im
  is_unchanged-Fast-Path.
- WR-03: `6893af3` per Timeout verlorene Seiten/Frames setzen truncated
  (indexed(truncated), D-08).
- WR-04: `e4959c1` OCR_JOB_SECONDS_MAX abgeleitet: 1800/2 - 60 - 60 = 780,
  mit Paritäts- und Invariantentest; info.xml korrigiert.

Die 3 Info-Findings (IN-01 bis IN-03) bleiben offen und sind bewusst nicht
angefasst.

_Geprüft: 2026-09-01T18:15:11Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Tiefe: standard_
_Behoben: 2026-09-01, Commits 7d334bf..e4959c1_
