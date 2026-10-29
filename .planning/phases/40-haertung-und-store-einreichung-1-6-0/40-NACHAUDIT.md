---
phase: 40-haertung-und-store-einreichung-1-6-0
audited: 2026-10-29
diff: efcf26c5..91a0603f
files_reviewed: 13
findings:
  critical: 0
  high: 0
  medium: 2
  low: 2
  info: 2
  total: 6
status: issues_found
recommendation: 1.6.1
---

# Phase 40: Nachaudit 1.6.0 (Security, Bugs, Performance)

**Stand:** 29.10.2026, **0 CRIT / 0 HIGH / 2 MEDIUM / 2 LOW / 2 INFO**. Keine
Rechte-Umgehung und kein Datenleck gefunden. Die zwei MEDIUM-Befunde betreffen
die Verfügbarkeit der Indexierung bei einem kaputten Mount, also genau den
Fall von Issue #36. Nach der Faustregel "ab MEDIUM" ist ein **1.6.1 nötig**.
Code ist nicht geändert, dieses Dokument ist der ganze Beitrag.

## Umfang

Anlass: 40-AUDIT.md deckte `v1.5.1..336ccae7` ab (Code-Kopf efcf26c5). Danach
gingen die Pläne 40-02 (Migration) und 40-06 (Issue-#36-Paket, Kandidat F,
Nachtrag W-1/W-2) ohne eigenes Audit in den Tag `v1.6.0` (91a0603f). Der
Nachtrag 991b1eff kam nach 40-06-VERIFICATION.md und war unabhängig
ungeprüft.

`git diff --stat efcf26c5..91a0603f -- backend/src php/lib php/js
php/templates backend/appinfo php/appinfo`: **13 Dateien, 579 Zeilen dazu, 63
weg** (die Zahl im Auftrag, 11 Dateien, zählt die beiden info.xml nicht mit;
dort ändern sich nur Version, Image-Tag und Doku-Links). Gelesen:

- `backend/src/findling/nc/client.py` (GatewayRefused, `_OUTAGE_STATUS`)
- `backend/src/findling/worker/poller.py` (`_work`, `_read_in_slots`,
  `_handle`, `_scan`, `_fetch_file`/`_fetch_once`, `_count_refusal`, `_abort`,
  Strähnen-Zustand `_GATEWAY_UNAVAILABLE_SINCE`, `run`, `run_once`)
- `backend/src/findling/index/writer.py` (`rollback`, `flush`)
- `backend/src/findling/api/status.py`, `backend/src/findling/api/resources.py`
  (`filled_languages_as_of`, `_start_fill_refresh`, `_refresh_fill`,
  `reset_read_side`)
- `php/lib/Controller/GatewayController.php`, `php/lib/Service/SearchService.php`,
  `php/lib/Service/AdminViewService.php`, `php/js/admin.js`,
  `php/templates/admin.php`, `php/lib/Migration/Version001600Date20261028000000.php`
- Gegenlesen außerhalb des Diffs, weil die neuen Pfade darauf bauen:
  `php/lib/Service/QueueService.php` (claim, MAX_DELIVERIES, KIND_BATCH),
  `php/lib/Db/QueueMapper.php` (LOCK_TIMEOUTS, Sortierung), `php/lib/Service/FileStateService.php`,
  `php/lib/Service/StorageService.php`, `backend/src/findling/nc/queue.py`
  (`unlock`), `backend/src/findling/worker/reconcile.py` (`_compare`),
  `backend/src/findling/store/repo.py` (`record`, `known_etags`),
  `backend/src/findling/config.py` (Batch- und Pausenwerte).

Kontext: 40-06-PLAN.md (Threat-Register T-40-20 bis T-40-27, "Warum kein
PHP-404"), 40-06-SUMMARY.md mit Nachtrag W-1/W-2, deferred-items.md, 40-AUDIT.md.

## Methode

- Jede Hypothese am Code verfolgt, über die Modulgrenze PHP/Python hinweg.
- Windows 11, ohne docker, freier RAM vor dem ersten Lauf 1,87 GB, seriell.
- `tests/test_poller.py` einmal komplett: **218 passed, 1 skipped**.
- Zwei Proben **außerhalb des Repos** (Scratch-Verzeichnis der Sitzung, nicht
  committet), beide auf den Fixtures und dem Queue-Modell `_QueueWithBudget`
  aus `tests/test_poller.py` bzw. den Helfern aus `tests/test_reconcile.py`:
  - **P-HOL:** Bestand aus N immer ablehnenden Dateien (GatewayRefused 500,
    niedrigste IDs, wie ein kaputter Mount, den der Crawl am Stück eingereiht
    hat) und 32 gesunden dahinter, Batch 32 wie `KIND_BATCH[content]`,
    `lock_rounds=8` (LOCK_TIMEOUT 900 s geteilt durch die Pausenkappe 120 s).
    Einmal mit der echten Schwelle, einmal mit abgeschalteter Zählung
    (`_count_refusal` als No-op; die erste Gegenprobe über
    `GATEWAY_SAME_STATUS_OUTAGE_AFTER = 10**9` war untauglich, weil
    `min(10**9, 32) = 32` bei 32 von 32 Ablehnungen trotzdem eskaliert).
  - **P-RECON:** `Store.record(..., "failed", "gateway_error")` mit Etag
    `aaa`, dann `Reconcile._compare` über eine Seite mit derselben Datei (Etag
    `aaa`) und einer unbekannten Datei als Positivkontrolle.

## Security

### S1 Rechte im Suchpfad (T-40-27)

`SearchService.php:459-463`, `:604-608`, `:668-673` fangen ausschließlich
`StorageNotAvailableException` und setzen den Knoten auf `null`; alle drei
Stellen gehen danach in den bestehenden `null`-Zweig (`continue` bzw.
`FAILURE_SOURCE_UNAVAILABLE`). Der Fang liegt um `readableFile()`, also um
Auflösung **und** `isReadable()` zusammen: wirft eine der beiden, gibt es
keinen Knoten und damit keinen Treffer. Fail-closed, **kein Treffer ohne
Leserecht**. `readableFile()`/`readableNode()` selbst sind unverändert
(`:723-742`), Gateway und Queue-Leserwahl sehen also weiter die Exception
(T-40-23 eingehalten). Kein Befund.

### S2 Neue Logzeilen (T-40-22)

- `poller.py:2167` Status und file id; `:2378` Anzahl und Status; `:2436`
  zwei Zählwerte; `_fetch_once` Klassenname und Status.
- `GatewayRefused`-Text: file id und Status (`client.py`), wird nirgends
  geloggt außer über die Zeilen oben; `run()` loggt nur den Klassennamen.
- `GatewayController.php:108` statischer Satz, `fileId` im Kontext; kein Pfad,
  kein Nutzer. Der `\Throwable`-Zweig ist unverändert (nur Kommentar).
- `resources.py` Refresh: nur Klassennamen.

Kein Pfad, Titel, Inhalt oder Nutzername. Kein Befund.

### S3 gatewayUnavailableSince, languagesFilledAsOf, Admin-Anzeige

Beide Felder hängen an `StatusResponse` der Route `^/status$` mit
`access_level ADMIN` (40-AUDIT S1). PHP-seitig liest sie nur
`AdminViewService` (`:2756`, `optionalCounter`, Zahl >= 0 oder null), erreicht
über `SettingsController` ohne `NoAdminRequired`, und `DiagnoseCommand` (occ).
Anzeige: Template `admin.php:303` mit `p($l->t(...))`, Script
`admin.js:452` mit `text()` = `textContent`; der Wert selbst wird nie als Text
gezeigt. Satz in allen 16 Katalogen. **Keine neue Route.** Kein Befund.

### S4 DoS über präparierte Dateien

- **Fremdes Budget:** nein. `_count_refusal` (`poller.py:2372`) trägt nur die
  Zeile ein, deren Datei das Gateway abgelehnt hat; `_abort` gibt
  `_held - charged` mit Gutschrift frei (`:2427`). Gesunde Zeilen im selben
  Batch verlieren keinen Versuch. Kein Befund.
- **Gesunde Indexierung pausieren:** nicht dauerhaft, aber für eine Zeit, die
  linear mit der Zahl kaputter Dateien wächst. Siehe **F-40N-01**.
  Voraussetzung für einen Angreifer: Dateien auf einem Speicher, den er
  unerreichbar machen kann (Externer Speicher mit Nutzer-Mounts, wenn der
  Admin beides erlaubt; Externer Speicher ist in Findling standardmäßig aus,
  `StorageService.php:79`). Ohne Angreifer reicht ein kaputter Team-Ordner,
  das ist der Fall des Reports.

## Bugs

### B1 Häufungs-Schwelle und Kopfblockade (Nachtrag 991b1eff)

Gelesen: Claim id-sortiert (`QueueMapper.php:354`), Content-Batch 32
(`QueueService.php:193`), Abschreibung erst bei `retries > 3` beim Claim
(`:325`), Lock 900 s, Pause nach jedem `_abort` über `_back_off` auf bis zu
120 s (`config.py:295-296`). Eine Eskalation belastet höchstens 5 Zeilen
(die fünfte Ablehnung wirft), die übrigen 27 gehen mit Gutschrift zurück und
stehen im nächsten Claim wieder vorn. Ergebnis P-HOL:

| Kaputte Dateien | Schwelle | Pässe bis zur 1. gesunden Datei | Pässe bis leer | Endverdikte |
|---|---|---|---|---|
| 40 | an (1.6.0) | 25 | 32 | 40 repeatedly_stuck, 32 done |
| 200 | an (1.6.0) | 121 | 128 | 200 repeatedly_stuck, 32 done |
| 40 | aus | 2 | 3 | 40 gateway_error, 32 done |
| 200 | aus | 7 | 8 | 200 gateway_error, 32 done |

Rund 0,6 Pässe je kaputter Datei, jeder eskalierte Pass mit 120 s Pause: etwa
72 s je kaputter Datei, also **200 Dateien rund 4 h, 1 000 rund 20 h, 10 000
rund 8 Tage**, in denen keine Datei mit höherer ID indexiert wird. Der
Test `test_files_that_always_refuse_reach_the_give_up_rule_and_the_queue_drains`
deckt nur 2 kaputte Dateien im Batch von 2 ab, die Größenordnung bleibt
ungeprüft. **F-40N-01 (MEDIUM).**

### B2 Was nach Lock-Timeout mit belasteten Zeilen passiert

Die belastete Zeile bleibt gesperrt, kommt nach 900 s (OCR 1800 s) mit
gezähltem Versuch zurück und wird beim vierten Ausgeben in
`QueueService::claim` (`:325`) zu `failed(repeatedly_stuck)`. Der Reconcile
übernimmt das als Endzustand mit dem Etag (`reconcile.py:695`, IN-03), der
Admin-Hinweis lautet "Findling does not try this file again". Ohne Eskalation
(1 bis 4 Ablehnungen je Batch) endet die Datei sofort als
`failed(gateway_error)`. Store.record schreibt den Etag mit, `_compare` hält
"bekannt + gleicher Etag" für erledigt (`reconcile.py:678`). P-RECON bestätigt:
die gateway_error-Datei ist **keine Arbeit**, nur die unbekannte
Positivkontrolle ist es. Damit wird ein **vorübergehender** Storage-Ausfall
in beiden Wegen dauerhaft, also genau die Regression, mit der "Warum kein
PHP-404" den 404 ausgeschlossen hat; nur steht sie jetzt sichtbar in der
Fehlerliste. Dort steht für `gateway_error` "The next run tries again."
(`AdminViewService.php:562-565`), was kein Lauf tut. 1.6.0 ist der erste
Erzeuger dieses Verdikts (`git grep` auf efcf26c5: kein Producer).
**F-40N-02 (MEDIUM).**

### B3 Verwaiste Zeilen nach `_abort(charged=...)`

Nein. Jede Zeile in `_held` wird entweder freigegeben (`handed_back`) oder ist
in `charged` und läuft in den Lock-Timeout; `_held.clear()` danach.
`DocumentQueue.unlock` wirft nicht (`queue.py:669-674`, Fehler = Lock-Timeout).
Einzige Lücke: eine Cancellation während `_abort` (Shutdown) lässt `_held`
voll, und `unlock_held()` gibt dann auch die belasteten Zeilen mit Gutschrift
zurück. Einmalig, kein Budgetverlust, kein Befund.

### B4 Rollback unter `self._lock`

`writer.py:442-465`: Rollback, dann Zähler auf 0, alles im Lock. Ein Fehler
(geschlossener Writer, tantivy) lässt `_pending` stehen und wird in `_abort`
geloggt, das Unlock läuft trotzdem (Test
`test_an_abort_hands_the_rows_back_even_when_the_rollback_fails`). Kein
Auto-Commit mitten im Pass (nur `bench.py` liest `pending_bytes`), der
Rollback erfasst also alles des Passes. Unter mehreren Slots läuft `_abort`
erst hinter der Barriere. Kein Befund.

### B5 Refresh-Thread (Kandidat F)

- Lock-Reihenfolge: nur `_LOCK` (RLock). `_start_fill_refresh` startet unter
  dem Lock, der Thread wartet in `read_side()` kurz auf ihn, misst ohne Lock
  und schreibt im Lock. `join_fill_refresh` joint außerhalb. Kein Deadlock.
- Generation-Guard: `reset_read_side` erhöht `_GENERATION` und leert
  `_FILLED` unter dem Lock, `_refresh_fill:1093` prüft Generation und
  Verzeichnis im Lock vor dem Schreiben. Kein Rennen.
- Exceptions im Thread: `except Exception` mit Klassennamen, `finally` löscht
  das Flag. Daemon-Thread, beim Shutdown verloren, nächster Start misst neu.
- **Lücke:** `_FILL_REFRESH = thread` steht vor `thread.start()`
  (`resources.py:1064-1065`). Wirft `start()` (RuntimeError "can't start new
  thread", auf einer 4-GB-Box unter Druck denkbar), bleibt das Flag für die
  Lebensdauer des Prozesses gesetzt, `languagesFilled` wird nie wieder
  gemessen, und genau dieser Status-Aufruf endet in 500. **F-40N-03 (LOW).**
- Nach `reset_read_side` (Rebuild-Swap) mit laufendem Refresh startet der
  nächste Poll nichts (Flag gesetzt), der alte Lauf schreibt nicht
  (Generation), erst danach misst ein neuer: die Sprachzeile ist zwei
  Messläufe lang leer. Erweiterung des bekannten G1-Kaltstarts. Teil von
  **F-40N-06 (INFO).**

### B6 Statusraster

`client.py:160`: nur 502/503/504 sind Ausfall, alles andere ab 400 außer
404/998 ist ein Urteil über die Datei. 429 (Rate-Limit eines Proxys oder WAF)
und 408 (Proxy-Timeout) sind Aussagen über die Instanz, landen aber als
`failed(gateway_error)` und sind nach B2 dauerhaft. **F-40N-04 (LOW).**

### B7 Strähnen-Anzeige

`_note_gateway_answered()` bei ROUND_EMPTY (`poller.py:1085`, `:1098`): nach
einer Eskalation sind die belasteten Zeilen gesperrt, ein leerer Claim löscht
die Anzeige, obwohl dieselben Dateien nach dem Lock-Timeout wieder ablehnen.
Die Zeile flackert im Takt von 900 s. Zusammen mit dem bekannten unscharfen
Satz (deferred-items, v1.7). **F-40N-05 (INFO).**

### B8 Migration Version001600

Nur `IAppConfig::getValueString`/`deleteKey`, kein Schema, also unabhängig von
Postgres/MySQL/SQLite. Zweiter Lauf findet `''` und tut nichts (idempotent).
Klassen- und Dateiname identisch. Gleiche Form wie Version001400, durch die
Upgrade-Strecke aus 40-03 bewiesen. Kein Befund.

### B9 Mischbetrieb

- Companion 1.5.1 + Backend 1.6.0: Suche über den Versionsabgleich aus
  (bekanntes Verhalten). Indexierung: `gateway_error` steht in
  `FileStateService` schon auf efcf26c5, die Quittung wird angenommen; neue
  Status-Felder ignoriert die alte Seite.
- Companion 1.6.0 + Backend 1.5.1: Feld fehlt, `optionalCounter` gibt null,
  Satz bleibt verborgen; die Migration verwirft die gespeicherte Version.

Kein Befund.

## Performance

- **Je Status-Poll:** keine neue DB-Abfrage. `gateway_unavailable_since()`
  ist eine Modulvariable, `filled_languages_as_of()` liest den Cache.
- **Threads:** single-flight, ein Thread nur bei veraltetem oder fehlendem
  Wert. Nebenbefund: die TTL zählt ab Messbeginn (`started`,
  `resources.py:1042`). Dauert der Lauf länger als 30 s (auf dem 110k-Index
  aus #19 rund 5,3 s je Kette), ist der Wert schon beim Schreiben veraltet,
  und jeder Poll der offenen Admin-Seite startet den nächsten Lauf direkt
  danach. Das ist die Last von vorher, nur nicht mehr blockierend. Teil von
  **F-40N-06 (INFO).**
- **Speicher:** `_refusals` hat höchstens so viele Schlüssel wie HTTP-Status,
  `_refused_rows` höchstens einen Batch, beides je Pass neu. Kein Wachstum.
- **Verschwendete Arbeit:** ein eskalierter Pass rollt alles zurück, auch
  bereits extrahierte gesunde Dateien; unter mehreren Slots laufen die
  OCR-Tasks bis zur Barriere fertig, bevor alles verworfen wird. Gehört zu
  F-40N-01.

## Befunde

### F-40N-01 (MEDIUM): Häufungs-Schwelle blockiert die Queue hinter einem kaputten Mount

- **Stelle:** `backend/src/findling/worker/poller.py:2362-2382`
  (`_count_refusal`), `:1238-1242` (`_work`), `:2427-2429` (`_abort`),
  Konstante `:215`.
- **Szenario:** Ein Team-Ordner (oder ein externer Speicher) mit 1 000
  Dateien fällt aus, die Dateien stehen am Stück vorn im Bestand. Jeder Pass
  holt 32 davon, die fünfte Ablehnung eskaliert, 5 Zeilen werden belastet,
  27 gehen zurück und stehen wieder vorn, Pause 120 s. Bis alle 1 000 je
  dreimal belastet und abgeschrieben sind, vergehen rund 600 Pässe, etwa 20 h.
  In dieser Zeit wird keine gesunde Datei mit höherer ID indexiert, die
  Admin-Seite sagt "The content gateway did not answer". Ohne die Schwelle
  wären es 30 Pässe in wenigen Minuten (P-HOL). Ein Nutzer, der Dateien auf
  einem eigenen externen Speicher anlegen und den Speicher abschalten kann,
  löst dasselbe gezielt aus.
- **Fix-Vorschlag:** Die Schwelle über Speicher zählen, nicht über Dateien:
  eskalieren nur, wenn derselbe Status aus mindestens zwei verschiedenen
  `storage_id` kommt (QueueJob trägt sie, `queue.py:268`). Ein einzelner
  kaputter Mount bleibt dann Datei für Datei `failed(gateway_error)` mit
  vollem Batch-Durchsatz; ein echter Instanzausfall (401 oder 500 für alles)
  trifft fast immer mehrere Speicher und eskaliert weiter. Alternative: bei
  401/403 eskalieren, bei 5xx nur über mehrere Speicher. Regressionstest:
  P-HOL mit 200 kaputten Dateien auf einem Speicher, erste gesunde Datei
  spätestens im zweiten Pass.

### F-40N-02 (MEDIUM): Vorübergehender Storage-Ausfall wird ein dauerhaftes Verdikt, der Hinweis sagt das Gegenteil

- **Stelle:** `backend/src/findling/nc/client.py:343` und
  `poller.py:1612-1626`/`:1791-1796` (Verdikt), `backend/src/findling/worker/reconcile.py:678`
  (gleicher Etag = keine Arbeit), `:695` (repeatedly_stuck übernommen),
  `php/lib/Service/AdminViewService.php:562-565` (Hinweis).
- **Szenario:** Ein SMB-Mount ist eine Stunde weg, in dieser Zeit laufen 300
  seiner Dateien durch die Queue. Bis 4 je Batch werden sofort
  `failed(gateway_error)`, ab 5 je Batch nach drei Lock-Timeouts
  `failed(repeatedly_stuck)`. Der Speicher kommt zurück, die Etags ändern
  sich nicht, der nächtliche Reconcile hält alle für erledigt (P-RECON). Die
  Dateien bleiben aus dem Index, bis sie sich ändern oder der Admin
  `occ findling:index --restart` fährt. Die Fehlerliste verspricht für
  gateway_error "The next run tries again." Das ist der Verlust, den
  "Warum kein PHP-404" für skipped(gone) ausgeschlossen hat, nur nicht still.
- **Fix-Vorschlag:** `failed(gateway_error)` im Reconcile als Arbeit lesen,
  auch bei gleichem Etag, gedeckelt über `files.attempts` (zum Beispiel
  höchstens 3 Wiederholungen, je eine pro Reconcile-Zyklus), damit es keine
  Dauerlast nach IN-03 wird. Belastete Zeilen der Eskalation sollten statt
  `repeatedly_stuck` dasselbe Verdikt bekommen (bekannter v1.7-Punkt "Endverdikt
  gateway_error", hier mit Grund für 1.6.1). Mindestens den Hinweis an das
  Verhalten anpassen. Regressionstest: P-RECON umgekehrt, gateway_error mit
  attempts < 3 ist stale.

### F-40N-03 (LOW): Fehlgeschlagener Thread-Start sperrt den Refresh für immer

- **Stelle:** `backend/src/findling/api/resources.py:1063-1065`.
- **Szenario:** `thread.start()` wirft unter Speicherdruck. Das Flag zeigt auf
  einen nie gestarteten Thread, der es nie löscht; jeder spätere Aufruf
  findet es und startet nichts. `languagesFilled` bleibt bis zum Neustart auf
  dem letzten Wert oder leer, der auslösende Status-Aufruf antwortet 500.
- **Fix-Vorschlag:** `thread.start()` in try, im except `_FILL_REFRESH = None`
  setzen und den Klassennamen loggen; die Antwort aus dem Cache geht trotzdem
  raus. Test: `threading.Thread.start` per monkeypatch werfen lassen, zweiter
  Aufruf startet wieder.

### F-40N-04 (LOW): 408 und 429 gelten als Urteil über die Datei

- **Stelle:** `backend/src/findling/nc/client.py:160`.
- **Szenario:** Ein Reverse-Proxy mit Rate-Limit antwortet einem schnellen
  Pass für einige Dateien 429. Bis 4 je Batch werden dauerhaft
  `failed(gateway_error)` (F-40N-02), ab 5 belastet.
- **Fix-Vorschlag:** `_OUTAGE_STATUS = frozenset({408, 429, 502, 503, 504})`,
  Kommentar und Rastertest nachziehen.

### F-40N-05 (INFO): Ausfall-Anzeige erlischt bei leerem Claim, während belastete Zeilen gesperrt sind

- **Stelle:** `backend/src/findling/worker/poller.py:1085`, `:1098`.
- **Szenario:** Nach einer Eskalation ist der Rest der Queue leer; der
  nächste Pass findet nichts und löscht `gatewayUnavailableSince`, 900 s
  später lehnen dieselben Dateien wieder ab. Die Zeile kommt und geht.
- **Fix-Vorschlag:** Mit dem neuen Satz aus v1.7 zusammen lösen, etwa die
  Strähne erst nach einem Pass mit mindestens einer gelieferten Datei
  beenden.

### F-40N-06 (INFO): Sprachzeile nach Rebuild zwei Messläufe leer, Dauerlauf bei langer Messung

- **Stelle:** `backend/src/findling/api/resources.py:1042-1045`, `:1093-1097`.
- **Szenario:** (a) Rebuild-Swap während eines Refreshs: die Zeile ist leer,
  bis der alte Lauf verworfen und ein neuer fertig ist. (b) Ein Lauf über
  30 s ist schon beim Schreiben veraltet, die offene Admin-Seite hält den
  Thread im Dauerlauf (wie vor 1.6.0, aber nicht mehr blockierend).
- **Fix-Vorschlag:** (a) in `reset_read_side` nichts ändern, aber nach einem
  verworfenen Lauf sofort neu starten; (b) TTL ab Messende zählen
  (`time.monotonic()` nach `_measure_fill`).

## Befundtabelle

| Befund | Schwere | Datei:Zeile | Kurztext | Fix |
|---|---|---|---|---|
| F-40N-01 | MEDIUM | poller.py:2362-2382, :1238-1242, :2427 | Häufungs-Schwelle blockiert die Queue hinter einem kaputten Mount, rund 72 s je kaputter Datei | Schwelle über verschiedene storage_id zählen |
| F-40N-02 | MEDIUM | reconcile.py:678, :695; client.py:343; AdminViewService.php:562-565 | vorübergehender Ausfall wird dauerhaft gateway_error/repeatedly_stuck, Hinweis "The next run tries again." falsch | gateway_error mit attempts-Deckel im Reconcile wiederholen, Hinweis anpassen |
| F-40N-03 | LOW | resources.py:1063-1065 | gescheiterter Thread-Start lässt das single-flight-Flag stehen | Flag bei Fehler zurücksetzen |
| F-40N-04 | LOW | client.py:160 | 408/429 als Datei-Urteil | in `_OUTAGE_STATUS` aufnehmen |
| F-40N-05 | INFO | poller.py:1085, :1098 | Ausfall-Anzeige flackert nach Eskalation | mit v1.7-Satz lösen |
| F-40N-06 | INFO | resources.py:1042-1045, :1093-1097 | Sprachzeile nach Rebuild leer, Dauerlauf bei Messung > TTL | Neustart nach verworfenem Lauf, TTL ab Messende |

## Urteil

- **Security:** sauber. Kein Treffer ohne Leserecht, keine Pfade oder Namen in
  den neuen Logzeilen, die neuen Felder nur über ADMIN-Route und Admin-Seite,
  keine neue Route, kein Verbrennen fremden Budgets.
- **Bugs:** zwei MEDIUM. Beide treffen den Fall, für den 40-06 gebaut wurde:
  1.6.0 beendet die Endlosschleife aus #36, ersetzt sie bei einem großen
  kaputten Mount aber durch eine Blockade von Stunden bis Tagen (F-40N-01)
  und schreibt Dateien eines nur kurz fehlenden Speichers dauerhaft ab
  (F-40N-02).
- **Performance:** keine Zusatzabfragen je Pass oder Poll, kein unbegrenzter
  Speicher, Thread single-flight.

**Empfehlung: 1.6.1** mit F-40N-01 und F-40N-02, F-40N-03 und F-40N-04 als
billige Beifänge. F-40N-05 und F-40N-06 können nach v1.7.
