---
phase: 03-aktualit-t-und-ocr
verified: 2026-09-01T15:30:41Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
deferred:
  - truth: "Ein mehrseitiges TIFF als Inhaltsjob bekommt die lange OCR-Frist statt failed(timeout)"
    addressed_in: "Phase 4 oder Folgeplan am Poller"
    evidence: "deferred-items.md (Plan 03-10) benennt den Folgeplan; Phase-4-Ziel: 'kann für jede einzelne Datei begründen, warum sie auffindbar ist oder nicht'"
  - truth: "ocr_used wird auch für Bilder im Inhaltszweig gesetzt, damit die Statusseite den Aufwand ausweist"
    addressed_in: "Phase 4 oder Folgeplan am Poller"
    evidence: "deferred-items.md (Plan 03-10); die Marke dient der Phase-4-Diagnose (ADM-Anforderungen)"
---

# Phase 3: Aktualität und OCR Verification Report

**Phase Goal:** Was der Nutzer gerade ablegt, ändert, teilt oder löscht, ist kurz darauf korrekt im Index, und gescannte Dokumente sind durchsuchbar, ohne dass eine Originaldatei angefasst wird.
**Verified:** 2026-09-01T15:30:41Z (Stand: main, e517b51)
**Status:** passed
**Re-verification:** No, Erstverifikation

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Hochladen, Umbenennen, Verschieben: kurz darauf unter neuem Zustand findbar, ein einziger Ereignisweg über die PHP-App in die Pull-Queue | VERIFIED | `php/lib/AppInfo/Application.php:55-83` registriert 8 Datei-Events (Created, Written, Touched, Copied, Renamed, Deleted, MoveToTrash, NodeRestored) auf `FileEventListener` und 3 Share-Events auf `ShareEventListener`; beide münden ausschließlich in `QueueService::enqueueFile` (`FileEventListener.php:374`, `ShareEventListener.php:197`), kein zweiter Pfad. Fünf Job-Arten mit fester D-04-Reihenfolge `KINDS = [acl, delete, metadata, content, ocr]` (`QueueMapper.php:67-73`), Claim je Art (`claimBatch`, Zeile 289). Umbenennen ohne Download: Poller-Metadaten-Zweig liest den gespeicherten Text zurück (`poller.py:757` ruft `writer.stored_body`, definiert `writer.py:237`). Owner-Sichtprobe (03-13, Task 4) live bestanden: Upload beim ersten Poll findbar, neuer Name nach 45 s, alter Name 0 Treffer. |
| 2 | Text aus gescanntem PDF ohne Textlayer wird gefunden, ohne Admin-Konfiguration; Dokumente mit Textlayer werden extrahiert statt erneut OCR-t | VERIFIED | Zweitspur: `skipped(no_text_layer)` (`pdf.py:135`, Schwelle `_MIN_CHARS_PER_PAGE = 25`, an echten Dokumenten gemessen) wird per `queue.requeue(file_ids, kind=KIND_OCR)` requeued (`poller.py:674`), `KIND_OCR` überlebt die Queue-Grenze (`nc/queue.py:67-68`, Fix `21b2011` mit Regressionstest `test_an_ocr_job_keeps_its_kind_across_the_queue_boundary`). `kind=ocr` wählt `Route.OCR` (`poller.py:518,613`), tesseract als Subprozess mit deu+eng (`config.py:202`), `OCR_ENABLED = True` ab Werk (`config.py:197`). Mischdokument `14-pacht-mit-anhang.pdf` (2 Textseiten + 3 Scanseiten) endet als `indexed` über den Textpass, ohne OCR (CORPUS.md:69). CI-Dauergate: `Strasse`/`Straße`/`Jänner` treffen die gescannten Dateien 15/16 (integration.yml, Job reconcile-and-dach); Sichtprobe Schritt 3: `13-ratsvorlage-scan.pdf` mit echtem OCR-Snippet, `ocr_used=1`. Bilderspur (JPG/PNG/TIFF/WebP) über `dispatch.py:88-118` mit Plausibilitätsdeckel (`image.py`, `_MIN_LONG_EDGE_PIXELS = 640`, Icons enden als `skipped(image_not_ocrable)` ohne Enginestart). |
| 3 | Entzogener Share und gelöschte Datei verschwinden zeitnah aus den Trefferlisten aller nicht mehr berechtigten Nutzer | VERIFIED | Share/Unshare als `kind=acl` (`ShareEventListener.php:178,197`), Poller ruft `replace_acl` auch mit leerer Nutzerliste (`poller.py:556`); Löschzweig ohne Download über `drop_document` (`poller.py:704`, `writer.py`), Tombstone `deleted_at` in `store/schema.sql:58` und `repo.py`. Papierkorb-Events (MoveToTrash, NodeRestored) registriert. ACL/Delete stehen in der Claim-Reihenfolge VOR content/ocr (D-04). `SubtreeExpandJob` löst Ordner-Operationen in Bändern auf (acl/delete, `BATCH_SIZE`). Sichtprobe Schritte 5-6: Entzug sofort 0 Treffer für `kollegin`, Löschen sofort 0 Treffer für beide, Wiederherstellen nach 34 s wieder findbar. CI: Job reconcile-and-dach prüft die entfernte Datei für BEIDE Nutzer (integration.yml:1654-1656 mit Kontrollprobe vorher, Zeilen 1490-1496). |
| 4 | Bei komplett blockierten Events ist der Index nach genau einem ETag-Abgleichzyklus wieder korrekt (Abnahmetest wörtlich) | VERIFIED | `worker/reconcile.py` (551 Zeilen): Ruhe-Gate vor jeder Slice (Zeile 305-310), Cursor je Mount in der Tabelle `reconcile` (schema.sql:101, Abbruch kostet Wiederholung, nie Arbeit), `gone_in_range` (repo.py:601, genutzt reconcile.py:388), Abweichungen werden als Queue-Zeilen requeued (reconcile.py:407), seitenweises Lesen über `nc/files.py` -> `files_slice` (`client.py:428`) mit final-Flag gegen Lücken-als-Löschung. Leseweg über `ReconcileController` (GET mounts + files/slice, ExAppRequired, kein Allowlist-Eintrag, Negativtest in `test_readonly_gate.py`). CI-Job `reconcile-and-dach` führt den Abnahmetest wörtlich aus: Events über `occ files:scan` umgangen, Nachweis 0 Queue-Zeilen (integration.yml:1529-1538), `FINDLING_RECONCILE_ENABLED=false` auf Job-Ebene erzwingt genau EINEN Zyklus, danach alle drei Fälle (neu/geändert/entfernt) geprüft. |
| 5 | Nach OCR-Lauf über defekte/ungewöhnliche PDFs alle Originale bitweise unverändert, kein Job über Seiten-, Zeit- oder RAM-Deckel | VERIFIED | `readonly-gate`-Job: sha256 + stat (mtime, Größe) über alle 33 Korpusdateien vor und nach dem kompletten Index- und OCR-Lauf (integration.yml:442-447, 728-733), Verdikt-Zähler mit Referenz `testdata/CORPUS.md` (je Datei genau ein Verdikt, gemessen 22 indexed / 5 skipped / 6 failed, Cap-Verdikte 0), Berührungsnachweis vor der Prüfsummenaussage, Falsifikationsschalter `tamper_probe` + `missing_verdict_probe`. Deckel-Kaskade: `OCR_MAX_PAGES = 30`, `OCR_PAGE_SECONDS = 30` (hängende Seite kostet die Seite, nicht den Job), `OCR_JOB_SECONDS = 600` unter `LOCK_TIMEOUT = 900`, RLIMIT_AS 512 MB im Sandbox-Kind, `OMP_THREAD_LIMIT=1`; Limit gerissen ergibt `indexed(truncated)` (D-08). Gate A: dritter Allowlist-Eintrag `/queues/documents/requeue` mit Bedrohungsnotiz und `test_write_allowlist_has_exactly_three_entries` (`test_readonly_gate.py:208-212`). Korpus enthält 10 defekte PDFs (kaputte xref, Nullbytes, ohne Seiten, Riesenseitenzahl usw.), alle reproduzierbar aus `scripts/dev/build_corpus.py` (1181 Zeilen). |

**Score:** 5/5 Roadmap-Erfolgskriterien verifiziert

### Deferred Items

Nicht erfüllte Punkte, die laut deferred-items.md ausdrücklich in spätere Arbeit gehören, keine Gaps dieser Phase.

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | Mehrseitiges TIFF als Inhaltsjob kann `failed(timeout)` statt `indexed(truncated)` bekommen (kurze 120-s-Frist statt OCR-Frist) | Phase 4 / Folgeplan am Poller | deferred-items.md, Plan 03-10; Einzelbilder (Regelfall) nicht betroffen |
| 2 | `ocr_used` wird für Bilder im Inhaltszweig nicht gesetzt (Aufwand für Phase-4-Statusseite unsichtbar) | Phase 4 / Folgeplan am Poller | deferred-items.md, Plan 03-10; dient der Phase-4-Diagnose |
| 3 | Wiederhergestellter Ordner wird erst beim nächsten Abgleichlauf wieder auffindbar, nicht binnen Sekunden | Bewusster Zwischenzustand, Mechanismus existiert (ETag-Abgleich) | deferred-items.md, Plan 03-04; Kommentar im Restore-Zweig von FileEventListener |

### Required Artifacts (alle 14 Pläne, Existenz + Substanz + Verdrahtung)

| Artifact | Erwartet | Status | Details |
|---|---|---|---|
| `php/lib/Listener/FileEventListener.php` | Der eine Ereignisweg | VERIFIED | 376 Zeilen, IEventListener, enqueueFile-Aufruf, in Application.php für 8 Events registriert |
| `php/lib/Listener/ShareEventListener.php` | Share/Unshare als ACL-Aufträge | VERIFIED | 199 Zeilen, ShareCreated/ShareDeleted/ShareDeletedFromSelf, kind=acl |
| `php/lib/Migration/Version001000Date20260902000000.php` | kind-Spalte + Claim-Index | VERIFIED | 104 Zeilen, 17 kind-Treffer |
| `php/lib/Db/QueueMapper.php` | KINDS, Claim je Art, requeueAs | VERIFIED | 681 Zeilen; `requeueAs` setzt retries auf 0 und gibt den Lock frei (Zeilen 467-493), Delete-Zeilen nie abwertbar |
| `php/lib/BackgroundJobs/SubtreeExpandJob.php` | Teilbaum in Bändern | VERIFIED | 212 Zeilen, nur acl/delete, KIND_RANK-Schutz |
| `php/lib/Controller/QueueController.php` | POST requeue, geschlossene Artenprüfung | VERIFIED | ExAppRequired + rejectForeignCaller vor der Arbeit |
| `php/lib/Controller/ReconcileController.php` | GET mounts + files/slice, nur lesend | VERIFIED | 222 Zeilen, ApiRoute, kein Allowlist-Eintrag nötig (Negativtest belegt) |
| `backend/src/findling/index/writer.py` | stored_body, drop_document | VERIFIED | Beide vorhanden und im Poller aufgerufen (Zeilen 704, 757) |
| `backend/src/findling/worker/poller.py` | Metadaten-, Lösch-, ACL-, OCR-Zweig | VERIFIED | 1077 Zeilen, alle vier Zweige verdrahtet, ocr_used/etag mitgeschrieben |
| `backend/src/findling/extract/ocr.py` | tesseract-Subprozess, Deckel-Kaskade | VERIFIED | 226 Zeilen, OMP_THREAD_LIMIT, Seiten-Timeout kostet die Seite, ocr_unavailable-Verdikt |
| `backend/src/findling/extract/raster.py` | pypdfium2-Rasterung, Graustufen | VERIFIED | 149 Zeilen, render_page_png von ocr.py aufgerufen |
| `backend/src/findling/extract/image.py` | Bildspur mit Plausibilitätsdeckeln | VERIFIED | 258 Zeilen, MAX_IMAGE_PIXELS, Mindestkante 640 px, EXIF-Drehung, Downscale |
| `backend/src/findling/extract/dispatch.py` | Route.OCR als vierter Zweig | VERIFIED | 4 Bildmimetypes -> Route.OCR, PDF-Weg unverändert über Textlayer-Urteil |
| `backend/src/findling/extract/errors.py` | Drei neue OCR-Verdikte | VERIFIED | OCR_FAILED, ocr_unavailable; Reason-Liste gespiegelt in `FileStateService.php:81-82` |
| `backend/src/findling/extract/sandbox.py` | Frist je Auftrag, route über die Pipe | VERIFIED | route als String durch run/extract_guarded (Fix 5a31261), Regressionstest `test_a_forced_route_survives_the_boundary` |
| `backend/src/findling/nc/files.py` | Seitenweise Dateiliste mit final-Flag | VERIFIED | 290 Zeilen, ruft `client.files_slice`, erzeugt keinen eigenen Client |
| `backend/src/findling/worker/reconcile.py` | Abgleich mit Ruhe-Gate und Cursor | VERIFIED | 551 Zeilen, run_once, in main.py als eigene Task verdrahtet |
| `backend/src/findling/store/repo.py` | gone_in_range, Tombstones, Cursor | VERIFIED | 914 Zeilen, deleted_at 9 Treffer, gone_in_range von reconcile genutzt |
| `backend/src/findling/config.py` | OCR- und Reconcile-Deckel, gemessen | VERIFIED | Messdatum 2026-09-01 im Kommentar, Ranges + Fallback auf Default bei unbrauchbarer Env-Variable; alle Variablen in info.xml deklariert (6x FINDLING_OCR, 5x RECONCILE) |
| `backend/Dockerfile` | tesseract + deu/eng, fail-closed | VERIFIED | 11 tesseract-ocr-Treffer, Prüfungen im Bau |
| `scripts/dev/build_corpus.py` | Korpus reproduzierbar | VERIFIED | 1181 Zeilen, erzeugt alle 33 Dateien inkl. gerenderter Scans |
| `testdata/CORPUS.md` | Verdikt-Referenz je Datei | VERIFIED | 225 Zeilen, maschinenlesbare Verdikt-Spalte, Suchbegriff je Datei |
| `testdata/corpus/` | 33 Dateien inkl. Scans, Bilder, defekte PDFs | VERIFIED | 33 Dateien vorhanden (01 bis 33) |
| `docs/ocr.md` (min 40), `docs/reconcile.md` (min 30), `docs/german-analyzer.md` | Messprotokolle, DACH-Grenze | VERIFIED | 421 / 173 / 238 Zeilen; Jänner-Grenze dokumentiert (3 Treffer) |
| `.github/workflows/integration.yml` | Gate B über OCR-Korpus, IDX-04-Test, DACH-Gates | VERIFIED | 1694 Zeilen, 4 Jobs (walking-skeleton, readonly-gate, index-search-e2e, reconcile-and-dach), timeout-minutes gesetzt |
| `backend/tests/test_php_trust_boundary.py` | CI-Gate ExApp-Vertrauensgrenze | VERIFIED | 272 Zeilen, statische Prüfung ExAppRequired + rejectForeignCaller über alle ApiRoute-Methoden |
| `backend/tests/test_allowlist_parity.py` | PHP/Python-Mimetype-Parität | VERIFIED | 114 Zeilen, ALLOWED_MIMETYPES beidseitig |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| FileEventListener | QueueService | enqueueFile mit Job-Art | WIRED | FileEventListener.php:374 |
| QueueService | QueueMapper | claimBatch je Art, feste Reihenfolge | WIRED | QueueService.php:147, KINDS-Budget-Schleife |
| ShareEventListener | QueueService | enqueue kind=acl | WIRED | ShareEventListener.php:197 |
| poller | writer | stored_body (Metadaten) / drop_document (Löschen) | WIRED | poller.py:757 / 704 |
| poller | repo | replace_acl auch mit leerer Liste | WIRED | poller.py:556 |
| poller | QueueController | skipped(no_text_layer) -> requeue als ocr | WIRED | poller.py:674, KIND_OCR in KINDS (Fix 21b2011) |
| ocr.py | raster.py | Seite für Seite rastern | WIRED | ocr.py:160 render_page_png |
| errors.py | FileStateService.php | Reason-Liste beidseitig identisch | WIRED | ocr_failed, ocr_unavailable in FileStateService.php:81-82 |
| dispatch | image.py | Bildmimetypes -> Route.OCR | WIRED | dispatch.py:88-118 |
| nc/files.py | nc/client.py | files_slice ohne eigenen Client | WIRED | files.py:54,266; client.py:428 |
| reconcile | nc/files.py / nc/queue.py | Seitenlesen + requeue der Abweichungen | WIRED | reconcile.py:317-320 (files.page) und 407 (queue.requeue) |
| config.py | info.xml | jede OCR-/Reconcile-Variable deklariert | WIRED | 6x FINDLING_OCR, 5x RECONCILE in info.xml |
| integration.yml | testdata/corpus/ | sha256 vor/nach + Verdikt-Zähler | WIRED | Zeilen 442-447, 728-733; CORPUS.md in den Pfad-Filtern |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Gesamte Backend-Suite inkl. der Phase-3-Regressionstests | `uv run python -m pytest` (backend/) | 686 passed, 11 skipped, 29 s | PASS |
| KIND_OCR überlebt die Queue-Grenze | `test_an_ocr_job_keeps_its_kind_across_the_queue_boundary` (in Suite) | grün | PASS |
| Erzwungene Route über die Sandbox-Grenze | `test_a_forced_route_survives_the_boundary` (in Suite) | grün | PASS |
| Gate-A-Allowlist hat genau drei Einträge | `test_write_allowlist_has_exactly_three_entries` (in Suite) | grün | PASS |
| Fix-Commits existieren | `git log` für 5a31261, 9adef25, d30b2c2, 8fdef47, d83d184, 21b2011 | alle vorhanden | PASS |

### Probe Execution

Keine `scripts/*/tests/probe-*.sh` im Repository, konventionelle Probes entfallen. Die Falsifikations-Schalter der Phase (`tamper_probe`, `missing_verdict_probe`) sind workflow_dispatch-Eingaben von integration.yml und nur auf GitHub ausführbar; ihr absichtlicher Rot-Lauf steht noch aus (siehe Gaps Summary, Warnung 2). Der Verdikt-Zähler wurde laut 03-13 lokal in fünf Rot-Varianten gegengeprobt.

### Requirements Coverage

| Requirement | Quelle (Pläne) | Beschreibung | Status | Evidenz |
|---|---|---|---|---|
| COMP-03 | 03-01, 02, 03, 04, 07, 14 | Alle indexrelevanten Ereignisse (create/update/delete/move/rename, Share/Unshare) in die Pull-Queue, ein einziger Weg | SATISFIED | 8 Datei- + 3 Share-Events registriert, beide Listener münden ausschließlich in QueueService::enqueueFile; fünf Job-Arten mit D-04-Reihenfolge; Trust-Boundary-Gate über alle ExApp-Routen; Sichtprobe Schritte 1, 2, 5, 6 live bestanden |
| IDX-04 | 03-11, 12, 13 | Periodischer ETag-Abgleich garantiert Konsistenz ohne Events, Abnahmetest wörtlich | SATISFIED | reconcile.py mit Ruhe-Gate, Mount-Cursor, gone_in_range; CI-Job reconcile-and-dach: Events via occ files:scan umgangen, 0-Queue-Zeilen-Nachweis, genau ein Zyklus, drei Fälle korrekt |
| IDX-05 | 03-03, 04, 12 | Löschungen und Unshares räumen Inhalte und ACL zeitnah | SATISFIED | kind=delete/acl mit Vorrang, drop_document + Tombstone + replace_acl (auch leer), SubtreeExpandJob; Abgleich räumt zusätzlich verschwundene Dateien (Tombstones); Sichtprobe 5-6 und CI-Nachweis für beide Nutzer |
| OCR-01 | 03-05, 07, 08, 09, 10, 13 | Gescannte PDFs und Bilder automatisch per OCR, pypdfium2 + tesseract, DE+EN, rein index-seitig | SATISFIED | tesseract deu+eng im Image (fail-closed-Bau), Zweitspur PDF (requeue als ocr), Bildspur JPG/PNG/TIFF/WebP mit Plausibilitätsdeckeln, OCR_ENABLED ab Werk; Gate B beweist index-only bitweise; DACH-Suchgates in CI; Sichtprobe Schritte 3-4 |
| OCR-02 | 03-05, 06, 08, 09, 13 | Text-Layer-Erkennung (nie doppelt OCR), Seiten-Timeouts, RAM-Deckel je Job | SATISFIED | _MIN_CHARS_PER_PAGE = 25 gemessen, Mischdokument bleibt Textpass (Korpus 14), Seiten-Timeout 30 s (kostet die Seite), Job-Deadline 600 s < LOCK_TIMEOUT 900 s, RLIMIT_AS 512 MB, OMP_THREAD_LIMIT=1, indexed(truncated) beim Seitendeckel |

Alle 5 in REQUIREMENTS.md für Phase 3 gelisteten IDs sind in mindestens einem PLAN-Frontmatter deklariert und im Code belegt. Keine verwaisten Requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| keine | - | Kein TODO/FIXME/XXX/TBD/HACK in backend/src, php/lib oder build_corpus.py | - | - |

Die `return None`/`return []`-Treffer in reconcile.py, files.py und image.py sind semantische Rückgaben (Gate offen, Seite fehlerhaft, Bild plausibel) mit Begründungskommentaren, keine Stubs.

### Human Verification Required

Keine offenen Punkte. Die Owner-Sichtprobe (03-13, Task 4) wurde bereits vollständig durchgeführt und bestanden (7/7 Schritte: Hochladen, Umbenennen, gescanntes PDF, Foto und Icon, Freigabe/Entzug, Löschen/Wiederherstellen, Laufzeit). Der dabei gefundene Gap (KIND_OCR fehlte in KINDS, PDF-OCR-Zweitspur tot) ist mit Commit `21b2011` auf main behoben, per Regressionstest abgesichert und live verifiziert (beide Scans `indexed` mit `ocr_used=1`), im Code an e517b51 nachgeprüft.

### Gaps Summary

Kein Gap blockiert das Phasenziel. Drei Warnungen aus den Known Gaps von 03-13, Stand dieser Verifikation:

1. **CI-Erstlauf auf GitHub:** Zum Zeitpunkt des 03-13-Summarys war integration.yml noch nie auf GitHub gelaufen (Push-Verbot des Executors). Inzwischen ist gepusht; der CI-Status wird laut Auftrag separat vom Orchestrator geprüft und ist hier bewusst kein Blocker. Lokal ist alles Prüfbare geprüft (YAML lädt, 62 run-Blöcke gültig, Verdikt-Zähler in fünf Rot-Varianten gegengeprobt, Trefferzahlen gegen den echten Abfrage-Parser nachgemessen).
2. **Falsifikations-Schalter nie auf GitHub rot gefahren:** `tamper_probe` und `missing_verdict_probe` sollten einmal per workflow_dispatch absichtlich rot laufen, damit die Aussage "das Gate wird rot" nicht nur lokal belegt ist. Offen, WARNING, operativer Folgeschritt für den Owner/Orchestrator.
3. **docs/dev-setup.md:** Der im Auftrag genannte Stand (veraltete Zahlen) ist bereits behoben: die Seite nennt jetzt 22/5/6 über 33 Dateien und die tesseract-Voraussetzung des Host-Prozesses (PATH + TESSDATA_PREFIX); deferred-items.md führt den Punkt als ERLEDIGT 01.09.2026. Kein Handlungsbedarf mehr.

Ferner drei bewusst zurückgestellte Punkte (siehe Deferred Items), alle in deferred-items.md dokumentiert und Phase 4 beziehungsweise dem nächsten Poller-Plan zugeordnet.

---

_Verified: 2026-09-01T15:30:41Z_
_Verifier: Claude (gsd-verifier)_
