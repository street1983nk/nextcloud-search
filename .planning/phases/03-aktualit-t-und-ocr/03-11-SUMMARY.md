---
phase: 03-aktualit-t-und-ocr
plan: 11
subsystem: api
tags: [nextcloud, ocs, exapp, reconcile, php, python, etag]

# Dependency graph
requires:
  - phase: 03-07
    provides: "Requeue-Schreibweg (POST /queues/documents/requeue), den der Abgleich mitbenutzt statt einen zweiten Mechanismus zu erfinden"
  - phase: 02-indexkern-und-volltextsuche
    provides: "nc/client.py als einzige Grenzschicht, nc/queue.py als Muster für eine Client-Schale, Gate A"
provides:
  - "GET /ocs/v2.php/apps/findling/mounts: die Mountliste des Crawls, lesend"
  - "GET /ocs/v2.php/apps/findling/files/slice: eine nach fileId aufsteigende Seite mit fileId, etag, size, mtime, mime plus final-Kennzeichen"
  - "StorageService::getFileSlice: Projektion der Crawl-Abfrage auf die fünf Vergleichsfelder, ohne zweite Abfrage"
  - "nc/client.py: mounts() und files_slice(), beide lesend, Pfad als Literal am Aufrufort"
  - "nc/files.py: FileList mit Mount, FileRow, MountResult, SliceResult (final und complete)"
affects: [03-12, 03-14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Leseroute an der ExApp-Grenze: Attribut-Trias voll qualifiziert, rejectForeignCaller als erste Anweisung, kein Allowlist-Eintrag"
    - "Seitenende wird gemeldet statt geraten (final), damit eine Lücke nie zu einer Löschung wird"
    - "Eine Seite mit verworfener Zeile ist nicht vollständig (complete) und taugt nicht für eine Löschbestimmung"

key-files:
  created:
    - php/lib/Controller/ReconcileController.php
    - backend/src/findling/nc/files.py
    - backend/tests/test_files_client.py
  modified:
    - php/lib/Service/StorageService.php
    - php/lib/Controller/GatewayController.php
    - backend/src/findling/nc/client.py
    - backend/tests/test_readonly_gate.py

key-decisions:
  - "Der Abgleich bleibt ein Container-Pull: die PHP-Seite liefert nur Seiten, der Cursor liegt im Container, und ein verlorener Cursor kostet eine Wiederholung statt Arbeit"
  - "Das final-Kennzeichen kommt aus der Antwort und wird nie aus der Zeilenzahl geraten; alles, was nicht ausdrücklich true ist, gilt als nicht final"
  - "SliceResult.complete: eine Seite mit verworfener Zeile darf aktualisieren und requeuen, aber nicht löschen, weil eine verworfene Zeile genauso aussieht wie eine gelöschte Datei"
  - "Die GET-Routen bekommen keinen Eintrag in OCS_WRITE_ALLOWLIST; ein Eintrag würde die Pfade zusätzlich für POST und DELETE öffnen und das Gate ohne Not aufweichen"
  - "StorageService::getFileSlice baut auf getFilesInMount auf; Abgleich und Crawl sehen absichtlich dieselben Dateien samt Mime-Filter"
  - "GatewayController pinnt seinen Platzhalter auf Ziffern, sonst verschluckt /files/{fileId} je nach Dateisystemreihenfolge die neue Route /files/slice"

patterns-established:
  - "Reine Leseroute: keine Schreibmethode in der Datei, Grenzen als Konstanten mit Klemmung, Logs tragen Zähler, Storage-Id und Cursor, nie Pfad oder Name"
  - "Client-Schale nach dem Muster nc/queue.py: baut Objekte, verwirft und zählt, macht aus Transportfehlern Ergebnisse, erzeugt nie einen Client"

requirements-completed: [IDX-04]

# Metrics
duration: 35min
completed: 2026-09-01
---

# Phase 3 Plan 11: Leseseite des Abgleichs Summary

**Zwei bewachte Leserouten in der PHP-App (Mountliste und seitenweise Dateiliste mit final-Kennzeichen) plus die Client-Schale nc/files.py, die daraus Mount- und FileRow-Objekte baut, Unbrauchbares zählt und Transportfehler in Ergebnisse verwandelt.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-01T10:35:00Z
- **Completed:** 2026-09-01T11:12:00Z
- **Tasks:** 2 (Task 2 als TDD-Zyklus in zwei Commits)
- **Files modified:** 7

## Accomplishments

- Der Container kann fragen, welche Mounts es gibt und was wirklich darin liegt, ohne dass ein neuer Schreibweg entsteht: beide Routen sind GET, beide tragen die Attribut-Trias voll qualifiziert und rufen `rejectForeignCaller` als erste Anweisung.
- Eine Seite sagt selbst, ob sie die letzte ist. Damit kann die Löschbestimmung in Plan 03-12 ihre obere Grenze nur dort weglassen, wo es wirklich keine gibt, und eine Lücke wird nie mit einer Löschung verwechselt (T-03-1104).
- Die Antwort trägt ausschließlich fileId, etag, size, mtime und mime. Kein Pfad, kein Titel, kein Nutzername, weder in der Antwort noch im Log (T-03-1102).
- `nc/files.py` hält die nc-Grenze ein: weder die Nextcloud-Bibliothek noch ein HTTP-Client werden importiert oder auch nur genannt, was der bestehende Paketscan in `test_queue_client.py` mitprüft.
- Die Schreib-Allowlist bleibt bei drei Einträgen, und im Gate steht jetzt ausdrücklich, warum eine Leseroute keinen bekommt und keinen bekommen darf.

## Task Commits

1. **Task 1: Zwei lesende Routen in der PHP-App** - `f61440d` (feat)
2. **Task 2: Client-Schale für die Dateiliste** - `ff65d4a` (test, RED) und `15e090f` (feat, GREEN)

Ein REFACTOR-Schritt war nicht nötig; die GREEN-Fassung ist die, die auch nach Ruff, Ruff-Format, Pyright und Vulture unverändert bleibt.

## Files Created/Modified

- `php/lib/Controller/ReconcileController.php` (neu) - GET /mounts und GET /files/slice, DEFAULT_SLICE 500 und MAX_SLICE 2000 mit Klemmung, `badMount()` für eine Anfrage ohne Mount, `rejectForeignCaller()` wie in QueueController
- `php/lib/Service/StorageService.php` - `getFileSlice()` projiziert `getFilesInMount()` auf die fünf Vergleichsfelder; keine zweite Abfrage, damit Abgleich und Crawl nicht auseinanderlaufen können
- `php/lib/Controller/GatewayController.php` - Platzhalter `{fileId}` auf `\d+` festgelegt (siehe Abweichung 1)
- `backend/src/findling/nc/client.py` - `mounts()` und `files_slice()`, Pfade als Zeichenkettenliterale am Aufrufort, plus ein Kommentarblock, der festhält, warum diese beiden keine Allowlist brauchen
- `backend/src/findling/nc/files.py` (neu) - `Mount`, `FileRow`, `MountResult`, `SliceResult`, `FileList.mounts()`, `FileList.page()`
- `backend/tests/test_files_client.py` (neu) - 13 Tests gegen eine Session-Attrappe im Muster von `test_queue_client.py`
- `backend/tests/test_readonly_gate.py` - ein Test, der festhält, dass eine GET-Route keinen Allowlist-Eintrag braucht, und der die schreibende Gegenprobe für dieselben Pfade mitführt

## Decisions Made

- **Methodenname `page()` statt `slice()`:** `slice` ist ein Builtin, und der Ruff-Regelsatz dieses Projekts enthält `A` (flake8-builtins). `page` sagt dasselbe und kostet nichts.
- **`mounts as read_mounts` beim Import:** die Methode heißt `mounts()`, die Client-Funktion auch. Der Aufruf funktioniert zwar (Klassenscope liegt nicht im Namensraum einer Methode), liest sich aber wie eine Rekursion. Der Alias macht die Absicht sichtbar.
- **Die drei Typprüfer sind Kopien aus `nc/queue.py`:** sie sind dort privat, `queue.py` gehört nicht zu den Dateien dieses Plans, und ein gemeinsamer Ort wäre eine Änderung an einem Modul, das hier niemand anfassen soll. Der Grund steht als Kommentar über den Kopien.
- **`getFileSlice` liegt im StorageService, nicht im Controller:** der Plan verlangt beides ("die Slice-Route ruft getFilesInMount" und "StorageService bekommt nur, was fehlt"). Die Projektion auf fünf Felder ist das Fehlende, sie kennt `ICacheEntry`, und dieses Wissen gehört in den Dienst, der die Dateiaufzählung ohnehin besitzt. Der Controller ruft `getFileSlice`, das seinerseits `getFilesInMount` benutzt: eine Abfrage, kein Duplikat.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Routen-Kollision zwischen `/files/{fileId}` und `/files/slice` beseitigt**

- **Found during:** Task 1 (Zwei lesende Routen in der PHP-App)
- **Issue:** Nextcloud sammelt Attribut-Routen mit einem `DirectoryIterator` über `lib/Controller` (`lib/private/Route/Router.php`, `getAttributeRoutes`), die Reihenfolge in der Symfony-Sammlung ist also Dateisystemreihenfolge, und der erste Treffer gewinnt. Der Platzhalter `{fileId}` des Content-Gateways hatte keine Anforderung und passt damit auch auf das Wort `slice`. Die neue Slice-Route hätte je nach Reihenfolge funktioniert oder nicht, und im Fehlerfall wäre die Anfrage im Gateway gelandet.
- **Fix:** `#[ApiRoute(verb: 'GET', url: '/files/{fileId}', requirements: ['fileId' => '\d+'])]` im GatewayController, mit Begründung im Docblock darüber. Der Parameter existiert seit NC 29 (`OCP\AppFramework\Http\Attribute\ApiRoute`, im Testcontainer nachgelesen), und `RouteParser` reicht ihn an Symfony durch.
- **Files modified:** php/lib/Controller/GatewayController.php
- **Verification:** Gegenprobe mit der Symfony-Routing-Bibliothek des Testcontainers, Gateway zuerst registriert: ohne Anforderung matcht `/apps/findling/files/slice` die Route `gateway`, mit Anforderung die Route `slice`. Dazu `php -l` gegen PHP 8.2 und 8.3.
- **Committed in:** `f61440d` (Task-1-Commit)

**2. [Rule 2 - Missing Critical] `SliceResult.complete` ergänzt**

- **Found during:** Task 2 (Client-Schale für die Dateiliste)
- **Issue:** Der Plan verlangt, unbrauchbare Einträge zu verwerfen und zu zählen. Genau das erzeugt aber eine Datenverlustklasse: eine verworfene Zeile fehlt in der Seite, und "fehlt in der Seite" ist die Definition einer Löschung im Abgleich. Ein Zähler allein, den der Aufrufer ignorieren kann, hätte in Plan 03-12 zu gelöschten Dokumenten für Dateien geführt, die es noch gibt (Nachbarschaft von T-03-1104).
- **Fix:** `SliceResult.complete` (`not discarded and not unavailable`) plus ein Absatz im Modul-Docstring, der die Regel als Vertrag benennt: eine unvollständige Seite darf aktualisieren und requeuen, aber nicht löschen.
- **Files modified:** backend/src/findling/nc/files.py, backend/tests/test_files_client.py
- **Verification:** zwei Tests (`test_a_page_with_a_discarded_row_is_incomplete_and_says_so`, `test_a_page_without_a_discard_is_complete`) sowie die Zusicherung im Transportfehlertest
- **Committed in:** `15e090f` (Task-2-GREEN-Commit)

---

**Total deviations:** 2 auto-fixed (1 Bug, 1 fehlende kritische Funktionalität)
**Impact on plan:** Beide sind Korrektheit, kein Zuwachs an Umfang. Abweichung 1 betrifft eine Datei außerhalb der `files_modified`-Liste (GatewayController.php, eine Attributzeile plus Kommentar); ohne sie wäre die in diesem Plan gebaute Route nicht verlässlich erreichbar.

## Issues Encountered

- Ruff sortierte im RED-Commit die beiden `findling.nc.*`-Importe des Testmoduls auseinander, solange `nc/files.py` noch nicht existierte. Nach dem GREEN-Schritt ist die natürliche Reihenfolge wieder die, die Ruff verlangt; `ruff check .` und `ruff format --check .` sind am Endstand grün.
- Keine PHP-Testumgebung: Task 1 trug `tdd="true"`, aber die PHP-Hälfte hat weiterhin keine Testsuite (dokumentiert in `docs/testing.md`, und Plan 03-14 baut dafür ein textuelles Gate). Abgesichert wurde Task 1 daher über `php -l` gegen 8.2 und 8.3, die acht Greps der Abnahmekriterien und die Routing-Gegenprobe oben.

## Verification

- `find lib -name '*.php' -print0 | xargs -0 -n1 php -l` (php:8.3-cli und php:8.2-cli im Container): Exit 0
- Abnahme-Greps Task 1: Routen 2, GET 2, schreibende Verben 0, `rejectForeignCaller` 3, Grenzkonstanten 4, `'routes' => []` unverändert 1, kein Log mit Pfad oder Name
- Abnahme-Greps Task 2: die zwei neuen Pfade in `client.py` 2, `create_app_client` in `files.py` 0, Transportbibliotheken in `files.py` 0, `test_write_allowlist_has_exactly_three_entries` 1 und grün, kein Log mit Pfad, Name oder Titel
- `uv run python -m pytest -q`: 586 passed, 4 skipped
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (0 errors), `uv run vulture src tests --min-confidence 80`: alle Exit 0

## Threat Flags

Keine über den `<threat_model>` des Plans hinausgehende Angriffsfläche. Die beiden neuen Routen sind die dort geführten Leseflächen; T-03-1101 bis T-03-1105 sind wie geplant umgesetzt (ExAppRequired plus `rejectForeignCaller`, fünf Felder ohne Pfad, Klemmung an DEFAULT_SLICE/MAX_SLICE, final aus der Antwort, Allowlist unverändert bei drei Einträgen).

## User Setup Required

None - keine externe Konfiguration nötig.

## Next Phase Readiness

- Plan 03-12 kann die Leseseite unverändert benutzen: `FileList(nc).mounts()` und `FileList(nc).page(storage=..., root=..., after=..., limit=...)`. `root` ist der überschriebene Root des Mounts (`Mount.overridden_root`), nicht `root_id`.
- Zwei Vertragspunkte für 03-12, beide im Modul-Docstring festgehalten: eine Seite ohne `final` gilt als nicht final, und eine Seite mit `complete is False` darf keine Löschung begründen.
- Offen und bewusst nicht hier erledigt: die Sichtprobe gegen das Test-Nextcloud. Die Companion-App im laufenden Container ist aus dem Hauptcheckout eingehängt, nicht aus diesem Worktree; die Ende-zu-Ende-Probe gehört damit in `integration.yml` beziehungsweise in den Integrationsschritt aus Pattern 3 (IDX-04), zusammen mit dem Abgleichzyklus aus Plan 03-12.

## Self-Check: PASSED

Alle genannten Dateien liegen auf der Platte, alle vier Commits stehen auf `worktree-agent-03-11`, und kein Commit dieses Plans löscht eine verfolgte Datei.

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
