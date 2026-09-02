---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 07
subsystem: api
tags: [fastapi, pydantic, sqlite, php, nextcloud, appapi, vanilla-js, diagnostics]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "PathResolverService and FileStateService::forFile from plan 04-06, the error list with example path buttons"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "ExAppService::adminGet and the admin-only SettingsController from plan 04-03"
  - phase: 02-indexpfad-und-zustand
    provides: "findling_file_state as the verdict table of this side, the files table in the container"
provides:
  - "GET /diagnose in the container: the verdict of one file id, without a path, a title or any text"
  - "PathResolverService::resolveReference: a path or a numeric file id in one field, with .. refused"
  - "PathResolverService::inspect: storage, mimetype, size, owner and readable path of one file"
  - "AdminViewService::diagnose: the precedence rule over three sources as six named stages"
  - "QueueMapper::statusOfFile and QueueService::forFile: waiting or running by remaining claim time"
  - "SettingsController::diagnose: the admin-only JSON route of the lookup"
  - "Block four of the admin page: a form, a result card and the wiring of every example path"
affects: [04-08-ausschluesse-und-regeln, 04-09-exclusion-service, verify-work]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Precedence rule as a null-coalescing chain over six named private methods, so the order is readable"
    - "One HTTP call ahead of the chain, handed to the two stages that need it"
    - "Result card fully rendered in the template with all eight state icons hidden, script only shows one"
    - "One AbortController per caller, so a polling timer and a human lookup cannot cancel each other"

key-files:
  created:
    - backend/src/findling/api/diagnose.py
    - backend/tests/test_diagnose_endpoint.py
  modified:
    - backend/src/findling/main.py
    - backend/appinfo/info.xml
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_php_trust_boundary.py
    - php/lib/Service/PathResolverService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Controller/SettingsController.php
    - php/lib/Db/QueueMapper.php
    - php/lib/Service/QueueService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js
    - php/css/admin.css

key-decisions:
  - "The container verdict is fetched once before the six stages run, because stage one needs the tombstone to tell deleted from never seen and stage five needs the verdict; two calls would be a second round trip for one answer"
  - "Waiting and running are told apart by the remaining claim time, not by an empty lock column: a free row is marked with the epoch and an expired claim is free again without a write"
  - "A trashed file and a folder path get their own branch in stage two, because both would otherwise be answered with pending_crawl or with a mimetype verdict"
  - "PathResolverService gained inspect(), so AdminViewService needs no file system dependency of its own"
  - "The app version stays at 0.3.0 although the container gained a fifth route, because plan 04-05 already bumped it and both plans ship in one release"
  - "backendReachable is true for an input that resolved to nothing, so a reference that was never a file does not raise an outage banner"

patterns-established:
  - "Stage methods named stageOne to stageSix: the call site reads as the documented order and a new stage cannot be inserted invisibly"
  - "A refused admin input is counted and the counter is logged, never the value"

requirements-completed: [ADM-02]

# Metrics
duration: 25 min
completed: 2026-09-02
---

# Phase 04 Plan 07: Pro-Datei-Diagnose Summary

**Ein Pfad oder eine Datei-ID in einem Feld, und die Antwort ist genau ein Zustand mit Begruendung: sechs Stufen ueber drei Quellen entscheiden in fester Reihenfolge, ein stummes Backend sagt das statt "nicht indexiert" zu behaupten, und kein Dateiname verlaesst dabei den Container.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-02T18:20:24Z
- **Completed:** 2026-09-02T18:45:10Z
- **Tasks:** 3 (Task 1 als TDD-Zyklus, also 4 Commits)
- **Files created/modified:** 16

## Accomplishments

- Die Container-Route `GET /diagnose` beantwortet eine fileid mit Zustand, Grundcode, `ocrUsed`, `indexedAt`, `attempts`, `textChars`, Grabstein und Indexversion, und mit keinem Pfad und keinem Titel, obwohl die Zeile beides traegt. Ein Test setzt Pfad und Titel in der Datenbank und fordert ihre Abwesenheit in der Antwort; ein zweiter fuegt der Tabelle eine Spalte hinzu und fordert dasselbe.
- Die Vorrangregel liegt als sechs benannte private Methoden vor und wird als Null-Coalescing-Kette in der Reihenfolge 1 bis 6 aufgerufen: Existenz, live berechnete Regeln von heute, Warteschlange, Verdikt dieser Seite, Verdikt des Containers, `pending_crawl`.
- Ein Grabstein wird nur nach bestaetigter Abwesenheit des Cache-Eintrags als Loeschung gelesen (Pitfall 6). Existiert die Datei und traegt der Container einen Grabstein, lautet die Antwort `pending_crawl` mit dem Zusatz, dass sie vorher indexiert war.
- Ein stummes Backend fuehrt zu `backendReachable = false` plus dem Satz "Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet". Live gegengeprueft: bei gestopptem Container antwortet die Karte genau so und niemals mit "nicht indexiert".
- Eine Eingabe mit `..` und eine Eingabe, die einen nicht existierenden Nutzer nennt, geben woertlich dieselbe Antwort wie eine nicht existierende Datei. Live gegengeprueft: die drei JSON-Antworten sind identisch.
- Block 4 der Seite nimmt Pfad oder Zahl in einem `<form>` (Enter ohne Tastatur-Handler), die Ergebniskarte ist Markup der Vorlage samt allen acht Zustands-Icons, und jeder Beispielpfad der Fehlerliste fuellt das Feld, scrollt hin und loest die Pruefung aus.

## Task Commits

1. **Task 1 (RED): failing tests for the container diagnose route** - `78c00b0` (test)
2. **Task 1 (GREEN): GET /diagnose, main.py, info.xml** - `92c6979` (feat)
3. **Task 2: the precedence rule, the resolution and the admin route** - `ea6af7c` (feat)
4. **Task 3: block four and the wiring of the example paths** - `9ad144f` (feat)

_Task 1 lief als TDD-Zyklus: RED zuerst (ImportError, kein Modul), dann GREEN. Ein REFACTOR-Commit war nicht noetig, weil der Zielcode aus 04-RESEARCH Beispiel 4 uebernommen wurde._

## Files Created/Modified

- `backend/src/findling/api/diagnose.py` - Die Route samt Privacy-Vertrag im Modul-Docstring; Felder werden einzeln aus der Zeile gelesen, kein Row-Spread
- `backend/tests/test_diagnose_endpoint.py` - 13 Tests: Feldmenge als Ganzes, Pfad-und-Titel-Abwesenheit, unbekannte Spalte, Grabstein als Zahl, 422, 401, read-only, Byte-Gleichheit, Montage
- `backend/src/findling/main.py` - Import und `include_router` fuer den fuenften Router
- `backend/appinfo/info.xml` - Fuenfter `<route>`-Eintrag mit `access_level ADMIN`, Zahl im Kommentar korrigiert, und die Begruendung, warum die Version bei 0.3.0 bleibt
- `backend/tests/test_status_endpoint.py` - Routen-Montage-Assertion um `/diagnose` erweitert
- `backend/tests/test_php_trust_boundary.py` - Gate-B-Untergrenze von 9 auf 10
- `php/lib/Service/PathResolverService.php` - `resolveReference()` (Zahl oder Pfad, `..` abgelehnt, `NoUserException` wie nicht gefunden) und `inspect()` (Storage, Mimetype, Groesse, Besitzer, Pfad); `IRootFolder` injiziert
- `php/lib/Service/AdminViewService.php` - `diagnose()` mit dreizehn festen Schluesseln, sechs Stufen-Methoden, `containerVerdict()` und `reasonVerdict()`
- `php/lib/Controller/SettingsController.php` - Zweite `FrontpageRoute` `/admin/diagnose`, Laengenklemme 4096, Ablehnung ohne den Wert im Log
- `php/lib/Db/QueueMapper.php` - `statusOfFile()`: Art, Versuche und Restsperrzeit einer Zeile per `file_id`
- `php/lib/Service/QueueService.php` - `forFile()` als Durchgriff, damit die Seite die Queue weiter ueber den Service liest
- `php/templates/admin.php` - Block 4 (Formular, Hilfe, No-JS-Satz, Ergebniskarte mit acht Icons); `disabled` und Ueberbrueckungs-`aria-describedby` der Beispielpfade entfernt, der Satz "noch nicht auf dieser Seite" geloescht
- `php/js/admin.js` - `chipOf`, `chipLabel`, `diagnosisCard`, `lookUpOneFile`, `setupDiagnosis`; `ask()` nimmt jetzt ein Abort-Signal, die Routen stehen als Konstanten vollstaendig da
- `php/l10n/de.json`, `php/l10n/de.js` - 24 neue Zeichenketten inklusive einer Pluralform, der abgekuendigte Satz entfernt
- `php/css/admin.css` - `.findling-lookup`, `.findling-card`, Chip-Varianten `indexed` und `unknown`, Block 4 in die Breitenregel aufgenommen

## Decisions Made

- **Der Container wird einmal vor der Kette gefragt.** Stufe 1 braucht den Grabstein, um "war indexiert, ist geloescht" von "noch nie gesehen" zu trennen, und Stufe 5 braucht das Verdikt. Zwei Aufrufe fuer eine Nachfrage waeren ein zweiter Roundtrip fuer dieselbe Antwort. Die Entscheidungsreihenfolge bleibt 1 bis 6, weil die Kette faul von links nach rechts auswertet.
- **Wartet oder laeuft entscheidet die Restsperrzeit.** Der Plan sagt "`locked_at IS NULL` heisst wartet"; das Schema kennt kein NULL mehr, eine freie Zeile traegt die Epoche (Index-Grund an `freeRowCondition`), und ein abgelaufener Anspruch ist ohne Schreibvorgang wieder frei. Die Restzeit ist die einzige Groesse, die beides richtig trennt, und sie ist die Zahl, die ein Admin bei "wird verarbeitet" wissen will.
- **Papierkorb und Ordner sind eigene Zweige der Stufe 2.** Eine Datei im Papierkorb loest sich auf und sieht voellig normal aus; ohne den Zweig faellt sie auf `pending_crawl` durch, also auf das Versprechen, sie werde gleich indexiert. Ein Ordnerpfad ist die Eingabe, die durch ein fehlendes letztes Segment entsteht, und "Dateityp nicht unterstuetzt" ist darauf keine Antwort.
- **`inspect()` gehoert in PathResolverService.** Der Plan sah `IFileAccess::getByFileIds` in `AdminViewService` vor. Dort waere es die erste Dateisystem-Abhaengigkeit dieses Dienstes; `PathResolverService` haelt `IFileAccess` schon und ist laut eigenem Docblock die einzige Stelle, an der eine Nummer zu einem Namen wird.
- **Die App-Version bleibt bei 0.3.0.** Plan 04-05 hat beide Haelften angehoben, beide Plaene liegen im selben Release, und ein zweiter Bump haette `docker.yml` gegen ein nie geschnittenes Git-Tag laufen lassen. Die Entscheidung steht als Kommentar in `info.xml`, damit der naechste Plan weiss, unter welcher der zwei Regeln er steht.
- **`backendReachable` ist `true`, wenn die Eingabe nichts benannte.** Es wurde nichts gefragt, also wurde nichts verpasst: die Antwort "keine solche Datei" kommt vollstaendig von dieser Seite. Ein `false` haette fuer eine Unsinnseingabe ein Ausfall-Banner gehoben.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Warteschlange hatte keinen Zugriff per file_id**

- **Found during:** Task 2 (Stufe 3 der Vorrangregel)
- **Issue:** `QueueMapper` kennt `findByIds` (Queue-IDs), `countScheduled` und `countRunning`, aber keine Suche per `file_id`. Stufe 3 war ohne sie nicht baubar.
- **Fix:** `QueueMapper::statusOfFile(int)` liefert Art, Versuche, ob gerade gehalten wird und die Restsperrzeit; `QueueService::forFile(int)` reicht sie durch, damit `AdminViewService` die Queue weiter ueber den Service liest, wie sein Docblock es festlegt. Die Sperr-Arithmetik bleibt in der Klasse, die die Sperre schreibt.
- **Files modified:** php/lib/Db/QueueMapper.php, php/lib/Service/QueueService.php
- **Verification:** CLI-Probe im Dev-Container, `php -l` ueber das ganze `lib`, Gate B gruen
- **Committed in:** `ea6af7c`

**2. [Rule 1 - Bug] Die Plan-Annahme "locked_at IS NULL" gilt fuer dieses Schema nicht**

- **Found during:** Task 2 (Stufe 3)
- **Issue:** Der Plan beschreibt wartende Zeilen als `locked_at IS NULL`. Die Migration hat NULL auf die Epoche umgeschrieben (Perf-Audit H3), nichts schreibt seither NULL, und ein abgelaufener Anspruch ist ohne Schreibvorgang wieder frei. Eine Pruefung auf NULL haette jede Zeile als laufend gemeldet.
- **Fix:** Entscheidung ueber die Restsperrzeit gegen `LOCK_TIMEOUTS[kind]`, mit der Begruendung im Docblock von `statusOfFile`.
- **Files modified:** php/lib/Db/QueueMapper.php, php/lib/Service/AdminViewService.php
- **Verification:** Docblock nennt beide Faelle; die Probe zeigt fuer eine Datei ohne Queue-Zeile korrekt den Durchfall auf Stufe 4/5
- **Committed in:** `ea6af7c`

**3. [Rule 2 - Missing Critical] Papierkorb und Ordner haetten falsche Antworten bekommen**

- **Found during:** Task 2, aufgefallen in der CLI-Probe (fileid 1 ist der Heimatordner von `admin` und wurde als "Dateityp nicht unterstuetzt" gemeldet)
- **Issue:** Eine Datei im Papierkorb hat einen Cache-Eintrag und faellt bis Stufe 6 durch, also auf "noch nicht gesehen", was das Versprechen einer bevorstehenden Indexierung ist. Ein Ordnerpfad, die haeufigste Fehleingabe in genau diesem Feld, wurde mit dem Mimetype-Verdikt beantwortet.
- **Fix:** Zwei benannte Zweige in Stufe 2, beide mit Label und Abhilfe: "Im Papierkorb" plus Wiederherstellen, "Das ist ein Ordner" plus den Pfad einer Datei eingeben.
- **Files modified:** php/lib/Service/AdminViewService.php, php/l10n/de.json, php/l10n/de.js
- **Verification:** CLI-Probe: `1` und `testuser/files/corpus` antworten jetzt mit `excluded` und "Das ist ein Ordner"
- **Committed in:** `ea6af7c`

**4. [Rule 1 - Bug] Ein geteilter AbortController haette Diagnose und Polling gegeneinander abgebrochen**

- **Found during:** Task 3
- **Issue:** `ask()` legte den Controller selbst in die geteilte Variable `request`. Eine Diagnose haette die laufende Statusabfrage abgebrochen und die naechste Statusabfrage die Diagnose, obwohl der Plan ausdruecklich einen eigenen Controller fuer die Diagnose fordert.
- **Fix:** `ask(path, params, signal)` nimmt das Signal vom Aufrufer; `poll()` haelt `request`, die Diagnose haelt `lookupRequest`.
- **Files modified:** php/js/admin.js
- **Verification:** Gate C gruen (`AbortController` weiterhin vorhanden), beide Controller im Code getrennt sichtbar
- **Committed in:** `9ad144f`

**5. [Rule 3 - Blocking] PathResolverService brauchte IRootFolder, und AdminViewService StorageService**

- **Found during:** Task 2
- **Issue:** Die Richtung Pfad zu fileid geht nur ueber `getUserFolder($uid)`, weil die Mounts eines Nutzers erst dadurch stehen; Stufe 2 braucht `isIndexedStorage`, `ALLOWED_MIMETYPES` und den geltenden Cap.
- **Fix:** `IRootFolder` in `PathResolverService`, `StorageService` in `AdminViewService`; der Klassen-Docblock von `PathResolverService` erklaert jetzt beide Richtungen und warum die eine `getMountsForFileId` nimmt und die andere nicht.
- **Files modified:** php/lib/Service/PathResolverService.php, php/lib/Service/AdminViewService.php
- **Verification:** DI aufgeloest, CLI-Probe laeuft ohne Container-Fehler
- **Committed in:** `ea6af7c`

**6. [Rule 2 - Missing Critical] Block 4 hatte kein CSS**

- **Found during:** Task 3
- **Issue:** `php/css/admin.css` stand nicht in `files_modified`, aber ohne Regeln fuer `.findling-lookup`, `.findling-card` und die Chip-Varianten `indexed` und `unknown` waere der Block ohne Breitenbegrenzung, ohne Flaeche und mit unsichtbaren Zustandsfarben gerendert worden.
- **Fix:** Vier Regelbloecke, ausschliesslich Theme-Variablen, Klickflaechen auf `var(--default-clickable-area)`.
- **Files modified:** php/css/admin.css
- **Verification:** Gate C gruen (kein Hexwert, keine Farbfunktion, kein entfernter Fokusring)
- **Committed in:** `9ad144f`

**7. [Rule 3 - Blocking] Die neue Admin-Route antwortete mit 404**

- **Found during:** Task 3, Plan-Verifikation
- **Issue:** `/apps/findling/admin/diagnose` gab 404, waehrend `/admin/overview` mit 401 antwortete: der Attribut-Routen-Cache haengt an der App-Version, und diese bleibt bewusst bei 0.3.0.
- **Fix:** App-Container neu gestartet; beide Routen antworten jetzt mit 401. Kein Code-Fix, aber ein Betriebsschritt, den der naechste Plan kennen muss.
- **Files modified:** keine
- **Verification:** `curl` gegen beide Routen: 401 und 401
- **Committed in:** kein Commit (Laufzeitschritt)

---

**Total deviations:** 6 auto-fixed (2 Bugs, 3 fehlende kritische Funktionalitaet, 1 Blocker) plus 1 Betriebsschritt
**Impact on plan:** Kein Scope-Creep. Zwei Deviations korrigieren Plan-Annahmen gegen den tatsaechlichen Code (Sperrspalte, Zugriff per file_id), drei schliessen Antworten, die sonst falsch oder unlesbar gewesen waeren, und eine ist der Abort-Controller, den der Plan selbst gefordert hat.

## Issues Encountered

- **Nicht ausgefuehrt, weil bereits erledigt:** Pitfall 10 nennt den unpraezisen Satz im Docstring von `backend/src/findling/api/status.py` ("where that decision is enforced"). Der Satz existiert nicht mehr; ein frueherer Plan der Phase hat ihn bereits praezisiert (`grep` ueber `backend/` und `php/` liefert null Treffer). Kein Handlungsbedarf.
- **`php/lib/Service/ExAppService.php` stand in `files_modified`, brauchte aber keine Aenderung.** `adminGet()` existiert seit Plan 04-03 mit `ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0`, der `is_array`-Pruefung als Fall 1 und den drei weiteren Faellen. Eine Aenderung waere eine Aenderung ohne Grund gewesen.
- **Die beiden `str_replace`-freien Pfadregeln:** `resolveReference` lehnt ein Segment `..` ab statt es zu filtern, und der Acceptance-Grep `str_replace('..'` steht bei null. Der eine `str_replace`-Aufruf in der Datei wandelt Backslashes in Schraegstriche, damit eine unter Windows kopierte Pfadangabe nicht als "kein Pfad" abgelehnt wird.

## Known Stubs

| Stub | Datei | Grund |
|------|-------|-------|
| `excludedByAPrefix()` gibt immer `null` zurueck | php/lib/Service/AdminViewService.php | Der Ausschluss-Praefix-Test der Stufe 2 braucht `ExclusionService`, der erst mit dem Regeln-Block entsteht; Plan 04-09 haengt ihn ein. Die Methode steht benannt und am richtigen Platz der Reihenfolge aufgerufen da, mit dem Verweis im Docblock, statt die Stufe unvollstaendig zu verstecken. Bis dahin beantwortet die `skipped(excluded)`-Zeile des Crawls diese Dateien auf Stufe 4. |

Der Stub verhindert das Ziel dieses Plans nicht: ADM-02 verlangt einen benannten Zustand mit Begruendung fuer jede Datei, und eine per Regel ausgeschlossene Datei bekommt ihn heute aus Stufe 4.

## Threat Flags

Keine. Die Oberflaeche dieses Plans steht vollstaendig im `<threat_model>`: die neue Container-Route (T-04-40, ADMIN deklariert), die Admin-Route (T-04-41, Gate B auf 10 angehoben), die Pfad-Auflösung (T-04-37) und die Nutzer-Aufzaehlung (T-04-38). Die zwei zusaetzlichen Lesezugriffe, `QueueMapper::statusOfFile` und `PathResolverService::inspect`, liegen hinter derselben Admin-Route und lesen drei Spalten der eigenen Tabelle beziehungsweise den Cache-Eintrag, den `describeMany` schon liest; keine neue Vertrauensgrenze.

## Verification

| Gate | Ergebnis |
|------|----------|
| `cd backend && uv run python -m pytest -q` | 753 passed, 11 skipped |
| `uv run ruff check .` / `ruff format --check .` | All checks passed / 77 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | ohne Befund |
| `php -l` ueber `lib`, `appinfo`, `templates` im Container | 0 Dateien mit Fehler |
| Gate B (`test_php_trust_boundary.py`) | gruen, Untergrenze steht bei 10 |
| Gate C (`test_admin_ui_contract.py`) | 13 passed |
| Kein Em-Dash (U+2014), kein En-Dash (U+2013) | in allen 16 Dateien null Treffer |
| `info.xml` | genau fuenf `<route>`, der neue mit `ADMIN` |

**Sichtproben, headless gegen den Dev-Container (Port 8090, `testuser`, Testkorpus):**

- Sichtprobe 5 (Datenhaelfte): Fuer beide Beispielpfade der Fehlerliste nennt die Diagnose-Karte denselben Grund wie die Zeile. `06-zero-bytes.pdf` gibt `failed/empty_file` "File is empty", `99-riesenprotokoll.txt` gibt `skipped/too_large` "Too large". Die Klick-, Scroll- und Fuell-Haelfte ist Vanilla-JS ohne Testlauf und bleibt eine Sichtprobe im Browser.
- Sichtprobe 6: Zahl (`285`), Pfad (`testuser/files/99-riesenprotokoll.txt`) und Unsinn (`wasistdas`) ergeben drei Antworten: zweimal `skipped/too_large` mit Pfad und Abhilfe, einmal `found=false` mit `unknown` und ohne Fehlerfarben.
- Sichtprobe Backend gestoppt: eine regelkonforme Datei ergibt `state=unknown`, `backendReachable=false` und den Satz "The state of this file is unknown right now because the backend does not answer.", nicht "nicht indexiert".
- Sichtprobe Nutzer-Aufzaehlung: `nosuchuser:x.pdf` und `../../etc/passwd` liefern zeichengleich dieselbe JSON-Antwort.
- Sichtprobe Rendern: `OC_Template('findling','admin')->fetchPage()` laeuft ohne PHP-Notice, enthaelt Block 4 einmal, `<form` einmal, `aria-live="polite"` zweimal, `disabled` null mal, den abgekuendigten Satz null mal und zwei Beispielpfad-Buttons mit `data-findling-path`.
- Routen: `/apps/findling/admin/overview` und `/apps/findling/admin/diagnose` antworten beide mit 401 ohne Session. Vor dem Neustart des App-Containers antwortete die neue Route mit 404 (Attribut-Routen-Cache an der App-Version).

## User Setup Required

Keine. Es ist kein externer Dienst und keine Umgebungsvariable dazugekommen.

Ein Betriebshinweis fuer die Abnahme: die neue Admin-Route ist erst nach einem Neustart des App-Containers erreichbar, weil die App-Version bewusst bei 0.3.0 bleibt und der Attribut-Routen-Cache daran haengt.

## Next Phase Readiness

- ADM-02 ist erfuellt: eine beliebige Datei, ein benannter Zustand, eine Begruendung, eine Abhilfe.
- Fuer Plan 04-08 (Regeln und Grenzen) liegt der Groessen-Cap als `StorageCrawlJob::MAX_SIZE` in Stufe 2; sobald er eine Einstellung ist, liest ihn dieselbe Zeile aus der Einstellung statt aus der Konstante.
- Fuer Plan 04-09 steht `excludedByAPrefix()` benannt und aufgerufen bereit; einzuhaengen ist genau ein Methodenkoerper.
- Block 5 (Regeln) fehlt noch, damit vier von fuenf Bloecken der Seite stehen.

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*

## Self-Check: PASSED

Alle in `key-files.created` genannten Dateien liegen auf der Platte, und alle fuenf Commits dieses Plans (`78c00b0`, `92c6979`, `ea6af7c`, `9ad144f`, `ee2a71b`) stehen im Git-Log.
