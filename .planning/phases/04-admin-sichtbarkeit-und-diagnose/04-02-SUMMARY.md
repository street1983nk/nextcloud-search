---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 02
subsystem: api
tags: [fastapi, pydantic, sqlite, status, privacy, php-docblock]

# Dependency graph
requires:
  - phase: 02-storage-und-index
    provides: "StatusResponse, Store.counts/reasons_by_state/acl_totals, resources.low_disk, schema.sql"
  - phase: 03-ocr-und-reconcile
    provides: "indexed(truncated) als Verdikt (D-08), FileStateService als Rueckkanal"
provides:
  - "GET /status liefert siebzehn Felder: die elf bisherigen plus truncated, reasons, diskFreeBytes, diskTotalBytes, indexBytes, maxFileBytes"
  - "resources.disk_bytes() als Rohzahlen des Volumes neben dem lowDisk-Flag"
  - "repo.index_bytes() als Groesse des Index-Verzeichnisses auf Platte"
  - "Index files_indexed_at fuer die Durchsatz-Fensterabfrage der Admin-Seite"
  - "Eine einzige, auf beiden Seiten woertlich gleiche Aufteilung der Wahrheit ueber skipped und failed"
affects: [04-03-php-controller, 04-04-statusseite, admin-ui, diagnose]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Antwortfelder werden einzeln benannt aufgebaut, nie durch Spread einer Datenbankzeile"
    - "Volume-Zahlen als eigene StatusResponse-Basis, die alle drei Zweige von report() erweitern"
    - "JSON-stabile Schluessel: der abwesende Grund heisst leerer String, nicht null"

key-files:
  created: []
  modified:
    - backend/src/findling/api/status.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/store/schema.sql
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_store_repo.py
    - php/lib/Service/FileStateService.php

key-decisions:
  - "maxFileBytes kommt aus settings() und wird auch ohne Zustandsdatenbank gemeldet, weil die PHP-Einstellung daran geklemmt wird"
  - "reasons normalisiert den Grund None auf den leeren String, damit die Antwort JSON-stabil ist"
  - "low_disk() bleibt unveraendert; disk_bytes() ist ein zweiter, eigener Leser statt einer Ableitung"
  - "index_bytes ist eine Modulfunktion in repo.py mit Pfad als Argument, keine Store-Methode, weil sie keine Verbindung braucht"
  - "_volume() baut eine Basis-Antwort, die alle drei Zweige von report() erweitern, statt die Volume-Felder dreimal zu wiederholen"

patterns-established:
  - "Feldmengen-Sperre: set(answer) == FIELDS im Test, damit ein neues Feld eine bewusste Testaenderung erzwingt"
  - "Privacy-Test laeuft rekursiv ueber alle Strings der Antwort, Schluessel verschachtelter Abbildungen eingeschlossen"
  - "Logzeilen von Groessen- und Platzlesern nennen nur den Ausnahmetyp, nie einen Pfad"

requirements-completed: [ADM-01, ADM-04]

# Metrics
duration: 10 min
completed: 2026-09-02
---

# Phase 04 Plan 02: Container-Zahlen fuer die Admin-Seite Summary

**GET /status liefert sechs neue Zahlen (truncated, reasons, diskFreeBytes, diskTotalBytes, indexBytes, maxFileBytes) bei unveraendertem Privacy-Vertrag, plus einen Index auf indexed_at und zwei Docblocks, die dieselbe Aufteilung der Wahrheit behaupten.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-02T16:24:00Z
- **Completed:** 2026-09-02T16:34:29Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `StatusResponse` traegt siebzehn statt elf Felder. Die Admin-Seite kann jetzt aus einer einzigen Container-Antwort den Deckungsgrad, die gekuerzten Dokumente, die Grund-Aufschluesselung des Containers, den Platzbedarf, den freien und gesamten Platz sowie den geltenden Groessen-Cap lesen.
- `maxFileBytes` kommt aus `settings()` und wird in allen drei Zweigen von `report()` gemeldet, also auch ohne Zustandsdatenbank. Damit kann die PHP-Einstellung an den tatsaechlich durchgesetzten Deckel geklemmt werden statt eine Zahl anzuzeigen, die nicht gilt (Pitfall 2).
- Der Privacy-Vertrag ist strenger geworden statt schwaecher: der Test laeuft jetzt rekursiv ueber alle Strings der Antwort, also auch ueber die Schluessel von `reasons`. Kein Stringwert traegt einen Schraegstrich oder einen Korpus-Dateinamen.
- Der Widerspruch aus Pitfall 3 ist aufgeloest: `FileStateService` und der Modul-Docstring von `status.py` behaupten dieselbe Aufteilung, jeweils mit der Liste der Zahlen, die von dort kommen, und mit der Begruendung (die Nextcloud-Haelfte ist die, die ein Admin bei ausgeschaltetem Container noch lesen kann).
- Die falsche Behauptung, `access_level ADMIN` sei der durchsetzende Ort, ist praezisiert: das gilt fuer den AppAPI-Proxy-Weg, der wirksame Schutz der Admin-Seite ist die PHP-Route ohne `NoAdminRequired`.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Feldmenge und Privacy-Anspruch festnageln** - `da5ada8` (test)
2. **Task 1 (GREEN): sechs neue Zahlen, disk_bytes, index_bytes, files_indexed_at** - `11ad779` (feat)
3. **Task 2: Aufteilung der Wahrheit in beiden Docblocks** - `fdcaaed` (docs)

_Ein REFACTOR-Commit war nicht noetig: die GREEN-Fassung ist die, die auch nach dem Aufraeumen stehen bleibt._

## Files Created/Modified

- `backend/src/findling/api/status.py` - Sechs neue Felder mit Default, `_named_reasons()` (None auf leeren String), `_volume()` als Basis-Antwort ohne Datenbank, `_of(store, volume)` baut jedes Feld einzeln benannt; Modul-Docstring mit der Quellen-Aufteilung und der praezisierten Zugriffspruefung
- `backend/src/findling/api/resources.py` - `disk_bytes() -> tuple[int, int]` mit derselben OSError-Behandlung wie `low_disk()`, `(0, 0)` fuer ein nicht messbares Volumen
- `backend/src/findling/store/repo.py` - `index_bytes(directory)` summiert rekursiv alle Dateien unter dem Index-Verzeichnis, 0 plus pfadlose Warnung bei fehlendem oder unlesbarem Verzeichnis
- `backend/src/findling/store/schema.sql` - `CREATE INDEX IF NOT EXISTS files_indexed_at ON files (indexed_at)` mit Begruendung (Durchsatz-Fenster beim Polling, sonst Full Scan)
- `backend/tests/test_status_endpoint.py` - `FIELDS` um sechs Namen erweitert, `_strings()` fuer den rekursiven Privacy-Test, vier neue Tests (truncated in indexed, reasons-Aufschluesselung mit leerem Schluessel, Rohzahlen des Volumes, Groessen-Cap ohne Zustandsdatenbank)
- `backend/tests/test_store_repo.py` - Zwei Tests fuer `index_bytes` (verschachteltes Verzeichnis summiert, fehlendes Verzeichnis liefert 0 und loggt keinen Pfad)
- `php/lib/Service/FileStateService.php` - Klassen-Docblock nennt beide Quellen mit ihren Zahlen und das explizite "was NICHT passiert"; `REASONS`-Docblock verweist auf die verbindliche Label-Tabelle und den `Unbekannter Grund (%s)`-Fallback. `record()`, `counts()`, `STATES` und `REASONS` selbst sind Zeichen fuer Zeichen unveraendert

## Decisions Made

- **`index_bytes` als Modulfunktion statt Store-Methode.** Der Plan gibt die Signatur `index_bytes(directory: Path) -> int` vor, und die Funktion braucht keine Datenbankverbindung. Sie liegt in `repo.py`, weil sie dieselbe Frage beantwortet wie die Zaehler dort ("wie gross ist der Zustand dieses Containers") und weil sie sich an die Modulregel haelt: der Pfad kommt als Argument.
- **`_volume()` als Basis-Antwort.** Die vier Volume-Felder plus `maxFileBytes` haengen nicht an der Datenbank und werden in allen drei Zweigen von `report()` gebraucht. Eine `StatusResponse` als Basis, die die Zweige per `model_copy(update=...)` beziehungsweise per benanntem Argument erweitern, vermeidet die dreifache Wiederholung ohne ein Feld unbenannt zu lassen.
- **`low_disk()` bleibt unangetastet.** Die Schwelle ist eine Entscheidung dieses Containers, die zwei Rohzahlen sind Messwerte. Getrennt gehalten kostet das einen zweiten `disk_usage`-Aufruf pro Poll und erlaubt, das gemeldete und das den Indexer pausierende Verhalten unabhaengig zu aendern.
- **Der abwesende Grund heisst leerer String.** `None` ist kein JSON-Objektschluessel. Die Normalisierung passiert im Container, damit die Seite nicht raten muss, welche von zwei Schreibweisen dieses Release liefert.

## Deviations from Plan

None - plan executed exactly as written.

Die vom Plan als Vorschlaege markierten Signaturen (`disk_bytes() -> tuple[int, int]`, `index_bytes(directory: Path) -> int`) wurden unveraendert uebernommen.

## Issues Encountered

- Der `php -l`-Aufruf im Dev-Container schlug zunaechst mit `Could not open input file: C:/Program Files/Git/var/www/...` fehl: Git Bash uebersetzt absolute Unix-Pfade in Windows-Pfade. Mit `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` meldet der Lint `No syntax errors detected`. Kein Codeproblem, nur eine Aufrufform, die fuer kuenftige Plaene notiert ist.

## Verification Results

- `cd backend && uv run python -m pytest -q`: **715 passed, 11 skipped**
- `cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run vulture src tests --min-confidence 80`: alle gruen (pyright `0 errors, 0 warnings`)
- `StatusResponse.model_fields`: **17 Felder**, genau die Menge, die `FIELDS` im Test festnagelt
- `php -l` im Dev-Container auf `FileStateService.php`: `No syntax errors detected`
- `grep -c "const REASONS = \["`: 1 (Regex-Leser der Parity-Tests finden die Konstante unveraendert, `test_extract_errors.py` und `test_allowlist_parity.py` sind gruen)
- Kein Em-Dash (U+2014) und kein En-Dash (U+2013) in den sieben geaenderten Dateien
- `status.py` enthaelt weiterhin `open_read_only` und kein `open_store`

## Known Stubs

Keine. Alle sechs neuen Felder sind an echte Quellen verdrahtet: `reasons_by_state()`, `shutil.disk_usage`, die Verzeichnissumme und `settings().max_file_bytes`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04-03 (admin-only PHP-Route und Controller) kann die siebzehn Felder als gegeben nehmen. Der Docstring von `status.py` nennt jetzt ausdruecklich, dass der wirksame Schutz an dieser Route haengt, also ist die Anforderung dort dokumentiert statt vorausgesetzt.
- Die Grund-Aufschluesselung des Containers steht getrennt von der Nextcloud-Sicht bereit. Die Statusseite muss beide zeigen und die Quelle benennen; die Aufteilung liegt woertlich in beiden Docblocks.
- Offen und bewusst nicht in diesem Plan: die Durchsatz-Fensterabfrage selbst. Der Index `files_indexed_at` liegt bereit, die Abfrage gehoert zu dem Plan, der den Durchsatz anzeigt.

## Self-Check: PASSED

Alle sieben geaenderten Dateien liegen auf Platte, alle vier Commits (`da5ada8`, `11ad779`, `fdcaaed`, `cb54df2`) sind im Log, und alle Acceptance-Criteria beider Tasks wurden nach der Umsetzung erneut ausgefuehrt und sind gruen.

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*
