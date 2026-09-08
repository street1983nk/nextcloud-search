---
phase: 03-aktualit-t-und-ocr
plan: 14
subsystem: security
tags: [exapp-boundary, ci-gate, acl-prefilter, asyncio, lxml, sqlite, logging]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: ExApp-Routen der Queue, Provider-Recheck, ACL-Vorfilter, Poller-Reihenfolge, die drei Audit-Berichte
  - phase: 03-aktualit-t-und-ocr
    provides: Requeue-Route (03-07), Reconcile-Leseseite mit /mounts und /files/slice (03-11), OCR-Zweig im Poller (03-09)
provides:
  - CI-Gate ueber die ExApp-Vertrauensgrenze aller acht Controller-Routen, mit zwei Selbsttests
  - Controller-Logs ohne Bibliotheksmeldungen, Ausnahme nur noch im exception-Feld
  - isReadable-Pruefung im finalen Recheck des Suchanbieters
  - Gedeckelte Nutzerlisten mit Kennzeichen und reservierter Sammelzeile im Vorfilter
  - Ordner-Cache je Claim und kuerzere Quittungstransaktionen
  - Poller ohne blockierendes Oeffnen, ohne gehaltenen Batch-Text, XHTML ohne Skript- und Stilinhalte
affects: [04-status-und-admin, 05-semantik, jede spaetere Phase, die eine ExApp-Route hinzufuegt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Statisches Textgate ueber PHP-Quellen aus einem Python-Test, in der Form von Gate A"
    - "Reservierte Sammelzeile im Vorfilter statt gekuerzter Nutzerliste"
    - "Ordner-Cache mit der Lebensdauer genau eines Claims, per Referenz durchgereicht"

key-files:
  created:
    - backend/tests/test_php_trust_boundary.py
  modified:
    - php/lib/Controller/GatewayController.php
    - php/lib/Controller/QueueController.php
    - php/lib/Controller/ReconcileController.php
    - php/lib/Search/Provider.php
    - php/lib/Service/QueueService.php
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/extract/text.py

key-decisions:
  - "Die Vertrauensgrenze wird textuell geprueft, weil es keine PHP-Testumgebung gibt; zwei Selbsttests belegen, dass das Gate beide Fehlerformen wirklich meldet"
  - "GatewayController bekommt rejectForeignCaller als Methode und die voll qualifizierte Attribut-Schreibweise der anderen Controller, damit alle Routen eine Form haben und die Zaehlung exakt bleibt"
  - "Eine gedeckelte Nutzerliste wird nie als Wahrheit geschrieben: der Container schreibt eine reservierte Sammelzeile, der Vorfilter ist damit grosszuegiger und nie strenger"
  - "Der reservierte Wert ist der Stern, weil Nextcloud ihn in einer Nutzerkennung verbietet und eine Kollision damit ausgeschlossen ist"
  - "Der Ordner-Cache lebt genau einen Claim und wird per Referenz gereicht, nicht als Feld gehalten; auch Fehlschlaege werden gemerkt"
  - "MAX_LIST_LENGTH faellt von 1000 auf 256, weil der Container nie mehr quittieren kann als er in einem Zug beansprucht"
  - "Skript und Stil werden mit dem Namensraum-Platzhalter entfernt, damit HTML- und XHTML-Zweig nicht wieder auseinanderlaufen"

patterns-established:
  - "Gate B: jede neue ExApp-Route braucht ExAppRequired und rejectForeignCaller als erste Anweisung, sonst faellt der Test"
  - "Controller-Logs tragen einen statischen Satz plus exception-Feld, nie eine Bibliotheksmeldung"
  - "Alle Schreibstellen des Vorfilters gehen durch eine Funktion, damit eine vierte das Kennzeichen nicht vergessen kann"

requirements-completed: [COMP-03]

# Metrics
duration: 45min
completed: 2026-09-01
---

# Phase 3 Plan 14: Verschobene Audit-Befunde Summary

**Die ExApp-Vertrauensgrenze aller acht Routen ist ab jetzt durch ein CI-Gate gegen Regression gesichert, die Controller-Logs tragen keine Bibliotheksmeldung mehr, gedeckelte Nutzerlisten kosten keine Megabyte je Batch, und der Poller haelt den Event-Loop beim Aktivieren frei.**

## Performance

- **Duration:** rund 45 Minuten
- **Started:** 2026-09-01T11:45:00Z (ungefaehr, erster Commit 12:12 Uhr UTC)
- **Completed:** 2026-09-01T12:29:00Z
- **Tasks:** 3 (jeweils TDD, also je ein Test- und ein Implementierungs-Commit)
- **Files modified:** 14 (13 aus dem Plan, plus tests/test_queue_client.py, das der Plan im files-Block der Aufgabe 2 bereits nennt)

## Accomplishments

- **Sec-L4 geschlossen:** `backend/tests/test_php_trust_boundary.py` liest alle Controller, findet jede Methode mit `ApiRoute` und verlangt `ExAppRequired` plus `rejectForeignCaller` als erste Anweisung. Es sind acht Routen, nicht sieben wie im Plankopf angenommen: fuenf an der Queue, zwei am Reconcile, eine am Content-Gateway. Die Zahl der geprueften Methoden ist gegen die Zahl der Attributzeilen in den Quellen abgeglichen, damit ein Parser, der etwas nicht mehr erkennt, nicht stumm gruen wird.
- **Sec-L6 geschlossen:** acht Logaufrufe in drei Controllern haben `$e->getMessage()` verloren. `grep -rn 'getMessage()' php/lib/Controller` liefert nichts mehr.
- **Sec-L5 geschlossen:** der Recheck im Suchanbieter stellt nach der Typpruefung die strengere Frage `isReadable()`, bevor Titel, Pfad oder Auszug ueberhaupt entstehen.
- **Perf-M5 mit der Entwurfsentscheidung aus dem Plan umgesetzt:** `usersFor` bricht bei 500 Nutzern ab und meldet das als `userIdsTruncated`. Der Container schreibt dann eine reservierte Sammelzeile statt der gekuerzten Liste, und der Vorfilter laesst die Datei fuer jeden als Kandidatin durch. Der Normalfall bleibt unveraendert streng, was der wichtigere der beiden Tests ist.
- **Perf-M8 und M9:** `getUserFolder` wird je Nutzer und Claim einmal aufgeloest, `MAX_LIST_LENGTH` faellt auf 256.
- **Perf-M1 und M2:** `_open` laeuft ueber `asyncio.to_thread`, und `_collect` gibt den Dokumenttext frei, sobald der Writer ihn hat.
- **Sec-L2 geschlossen:** Skript und Stil verschwinden auch im namensraumbehafteten XHTML-Zweig.

## Task Commits

1. **Task 1: Vertrauensgrenze, Logs, isReadable** , `f2c2013` (test, RED) und `da5321a` (fix, GREEN)
2. **Task 2: Gedeckelte Nutzerlisten, Ordner-Cache, kuerzere Transaktionen** , `e4c113f` (test, RED) und `a32b419` (perf, GREEN)
3. **Task 3: Poller entblockt, Speicher freigegeben, XHTML bereinigt** , `bf2dc34` (test, RED) und `1955438` (perf, GREEN)

Kein Refactor-Commit: in keiner der drei Runden gab es nach GREEN etwas aufzuraeumen, das nicht schon in der Implementierung stand.

## Files Created/Modified

- `backend/tests/test_php_trust_boundary.py` , neu. Gate B: statische Pruefung der ExApp-Vertrauensgrenze ueber alle Controller, mit vier Selbsttests gegen Textproben.
- `php/lib/Controller/GatewayController.php` , die Vergleichslogik wird zu `rejectForeignCaller()`, das Attribut-Trio voll qualifiziert, das Log ohne Bibliotheksmeldung.
- `php/lib/Controller/QueueController.php` , fuenf Logaufrufe bereinigt, `MAX_LIST_LENGTH` von 1000 auf 256 mit der Messung im Kommentar.
- `php/lib/Controller/ReconcileController.php` , zwei Logaufrufe bereinigt.
- `php/lib/Search/Provider.php` , `isReadable()` direkt nach der Typpruefung des Knotens.
- `php/lib/Service/QueueService.php` , `MAX_USERS = 500`, `usersFor` liefert Liste plus Kennzeichen, `describe` und `userFolder` bekommen den Ordner-Cache des Claims.
- `backend/src/findling/store/repo.py` , `ACL_ANY_USER` als reservierte Kennung, `prefilter_visible` fragt zwei Kennungen ab.
- `backend/src/findling/nc/queue.py` , `QueueJob.users_truncated`, gelesen aus `userIdsTruncated` und nur bei echtem `True`.
- `backend/src/findling/worker/poller.py` , `_acl_users` als einzige Schreibentscheidung fuer den Vorfilter, `_open` im Thread, Text im `_collect` freigegeben.
- `backend/src/findling/extract/text.py` , `_INVISIBLE_TAGS` mit Namensraum-Platzhalter.
- `backend/tests/test_acl_prefilter.py`, `backend/tests/test_queue_client.py`, `backend/tests/test_poller.py`, `backend/tests/test_extract_text.py` , die Behauptungen der drei Aufgaben.

## Decisions Made

- **Acht Routen statt sieben.** Der Plankopf rechnet mit sieben Routen. Gezaehlt sind es acht: `getDocuments`, `acknowledgeDocuments`, `unlockDocuments`, `requeue`, `documentStats`, `mounts`, `filesSlice` und `getFileContents`. Das Gate prueft die tatsaechliche Zahl und vergleicht sie gegen die Quellen, statt eine Zahl festzuschreiben.
- **Die voll qualifizierte Attribut-Schreibweise wird zur Pflicht.** QueueController und ReconcileController begruenden sie selbst damit, dass ein Grep-Gate sonst eine Importzeile mitzaehlt. Genau das war im GatewayController der Fall, und die Abnahmebedingung des Plans (geprüfte Methoden gleich Zahl der `ApiRoute`-Zeilen) ist nur mit einer Schreibweise erfuellbar. Die Importe von `ApiRoute` und `NoCSRFRequired` sind deshalb entfallen.
- **Der Stern als reservierte Kennung.** Nextcloud verbietet ihn in einer Nutzerkennung, also kann kein Konto mit der Sammelzeile kollidieren. Ein eigener Test haelt das fest.
- **Das Kennzeichen wird nur als echtes `True` gelesen.** `bool()` haette eine beliebige nichtleere Zeichenkette als "gedeckelt" gelesen und den Vorfilter durch einen Tippfehler auf der PHP-Seite geweitet. Die strenge Richtung ist hier die sichere.
- **Der Ordner-Cache merkt sich auch Fehlschlaege.** Sonst wuerde ein Nutzer ohne Heimatverzeichnis je Zeile des Batches erneut nachgeschlagen, und jeder dieser Versuche wuerde werfen, gefangen und geloggt.
- **Der Heartbeat-Fall wird als Eigenschaft geprueft, nicht als Sekundenzahl.** Der Test belegt, dass die Fabriken von `_open` auf einem Arbeitsthread laufen. Die 1,5 bis 3 Sekunden sind eine Messung des Audits und gehoeren nicht in eine Zusicherung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] GatewayController musste umgebaut werden, damit das Gate ueberhaupt gruen werden kann**
- **Found during:** Task 1
- **Issue:** Der Plan verlangt ein Gate, das `rejectForeignCaller` als erste Anweisung jeder Route sieht. Der GatewayController hatte den Vergleich inline im Methodenrumpf, dazu zwei Attribute als Import statt voll qualifiziert. Beides liess das Gate zu Recht rot werden, und beides ist nicht Teil der im Plan genannten Aenderung, sondern ihre Voraussetzung.
- **Fix:** Der Vergleich wurde zur privaten Methode `rejectForeignCaller()` mit dem vorhandenen Kommentar zum Restrisiko, das Attribut-Trio wurde voll qualifiziert, die beiden Importe sind entfallen.
- **Files modified:** `php/lib/Controller/GatewayController.php`
- **Verification:** `uv run python -m pytest tests/test_php_trust_boundary.py -q` gruen, `grep -rc 'ApiRoute' php/lib/Controller` liefert 8 wie die Zahl der geprueften Methoden, `php -l` ohne Fehler.
- **Committed in:** `da5321a`

**2. [Rule 2 - Missing Critical] Der Deckel greift in der Schleife, nicht auf der fertigen Liste**
- **Found during:** Task 2
- **Issue:** Ein Deckel, der erst die fertige Liste kuerzt, spart die Uebertragung und nicht den Aufbau. Bei einem instanzweiten Team Folder loest die Schleife tausende Mount- und Nutzerobjekte auf, bevor irgendetwas gekuerzt wird, und genau dieser Aufbau ist der gemessene Speicherposten aus M5.
- **Fix:** Die Schleife bricht ab, sobald `MAX_USERS` erreicht ist, und setzt das Kennzeichen.
- **Files modified:** `php/lib/Service/QueueService.php`
- **Verification:** `php -l` ohne Fehler; die Wirkung ist auf der Containerseite durch die drei Vorfiltertests belegt.
- **Committed in:** `a32b419`

**3. [Rule 2 - Missing Critical] Alle drei Schreibstellen des Vorfilters gehen durch eine Funktion**
- **Found during:** Task 2
- **Issue:** Der Poller schreibt an drei Stellen in die ACL-Tabelle: im Schnellpfad, im acl-Zweig und beim Verbuchen der Verdikte. Das Kennzeichen an zwei von drei Stellen zu beachten waere ein Fehler, den kein Test findet, weil jede Stelle fuer sich plausibel aussieht.
- **Fix:** `_acl_users(job)` als einzige Entscheidung, alle drei Aufrufe gehen darueber.
- **Files modified:** `backend/src/findling/worker/poller.py`
- **Verification:** `grep -n 'replace_acl' poller.py` zeigt drei Aufrufe, alle mit `_acl_users(job)`; die volle Testsuite gruen.
- **Committed in:** `a32b419`

**4. [Rule 1 - Bug] Ein zweiter Test sichert, dass der Thread die Ein-Client-Regel nicht kostet**
- **Found during:** Task 3
- **Issue:** `_open` in einen Thread zu verlegen beruehrt die Stelle, an der genau ein Client je Lauf gebaut wird. Ein Fehler dort waere teuer und unsichtbar: ein Client je Durchgang statt je Lauf.
- **Fix:** `test_the_resources_are_opened_only_once` belegt, dass zwei Durchgaenge einen Client bauen.
- **Files modified:** `backend/tests/test_poller.py`
- **Verification:** Test gruen.
- **Committed in:** `bf2dc34`

---

**Total deviations:** 4 automatisch behandelt (1 blockierend, 2 fehlende kritische Funktionalitaet, 1 Absicherung gegen einen Fehler, den die Aenderung selbst haette einfuehren koennen)
**Impact on plan:** Kein Umfangszuwachs. Alle vier liegen innerhalb der Dateien, die der Plan ohnehin nennt, und drei davon sind Voraussetzung dafuer, dass die Abnahmebedingungen des Plans ueberhaupt erfuellbar sind.

## Issues Encountered

- **`uv run pytest` gegen `uv run python -m pytest`.** Die Abnahmebedingungen des Plans nennen `uv run pytest`, CLAUDE.md schreibt `uv run python -m pytest` vor. Ausgefuehrt wurde durchgaengig die Form aus CLAUDE.md; das Ergebnis ist dasselbe.
- **PHP nur im Container.** Auf der Entwicklungsmaschine gibt es kein `php`. Der Lint lief als `MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd):/app" -w /app php:8.3-cli sh -c "find lib -name '*.php' -print0 | xargs -0 -n1 php -l"` und endete ohne Fehler. Das ist genau der Grund, aus dem das neue Gate textuell und in Python geschrieben ist.
- **Ein pyright-Fehler im neuen Poller-Test.** Die Fabrik als Klassenreferenz statt als Lambda mit `cast` ergab einen Typkonflikt gegen `GatewayClient`. Behoben in derselben Runde, bevor der Implementierungs-Commit lag.
- **Der Docblock von `KIND_BATCH` war kurzzeitig verwaist**, weil die neue Konstante zwischen Docblock und Konstante geriet. Vor dem Commit korrigiert.

## Threat Flags

Keine. Dieser Plan legt keine neue Netz- oder Dateizugriffsflaeche an; er verengt bestehende. Die eine bewusst akzeptierte Weitung, T-03-1404, ist die Sammelzeile im Vorfilter, und sie ist im Bedrohungsregister des Plans als `accept` gefuehrt: der Vorfilter liefert nur Kandidaten, die Grenze bleibt der finale Recheck (COMP-04), und Auszuege entstehen weiterhin erst danach.

## Known Stubs

Keine.

## User Setup Required

Keine.

## Next Phase Readiness

- Jede Phase, die eine ExApp-Route hinzufuegt, faellt ab sofort im Test, wenn sie das Attribut oder den Vergleich vergisst. Wer eine Route hinzufuegt, muss die voll qualifizierte Attribut-Schreibweise verwenden, sonst weicht die Zaehlung ab.
- Der Statusseite von Phase 4 steht mit `Findling: capped the user list of a queued file` ein Zaehler zur Verfuegung, falls dort einmal sichtbar gemacht werden soll, wie viele Dateien den Vorfilter nicht mehr verengen.
- Offen und bewusst nicht in diesem Plan: die in `usersFor` beschriebene Optimierung, je Storage statt je Datei zu fragen. Sie gehoert hinter eine Messung in Phase 5, zusammen mit dem dort geplanten Paritaetstest.

## Self-Check: PASSED

- Alle angelegten und geaenderten Dateien existieren im Arbeitsbaum.
- Alle sieben Commits sind in `git log` auffindbar: `f2c2013`, `da5321a`, `e4c113f`, `a32b419`, `bf2dc34`, `1955438`, `4a43c67`.
- Gates gruen: `uv run python -m pytest -q` mit 684 bestanden und 11 uebersprungen, `ruff check`, `ruff format --check`, `pyright` mit 0 Fehlern, `vulture --min-confidence 80` ohne Befund, `php -l` ueber alle Dateien unter `php/lib` ohne Fehler.
- Kein Co-Authored-By-Trailer, keine Em-Dashes, keine Emojis.
- STATE.md und ROADMAP.md wurden nicht angefasst, nichts wurde gepusht.

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
