---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 06
subsystem: extract/errors, store, worker/poller, api/diagnose, php diagnosis
tags: [D-29-09, "#18", T-02-56, T-29-18, T-29-19, diagnose]
requires: [29-05]
provides:
  - "ExtractionOutcome.detail (module.qualname der geworfenen Klasse, compare=False)"
  - "Tabelle file_errors (IF NOT EXISTS), Store.record(error_class=...), Store.error_class(file_id)"
  - "DiagnoseResponse.errorClass, AdminViewService::errorClass(), occ-Zeile 'error class'"
affects: [29-11, 29-12]
tech-stack:
  added: []
  patterns: ["Diagnosedatum in eigener IF-NOT-EXISTS-Tabelle statt Spalte", "Form-Prüfung statt Kürzen bei Werten über die Vertrauensgrenze"]
key-files:
  created: []
  modified:
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/schema.sql
    - backend/src/findling/store/repo.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/api/diagnose.py
    - php/lib/Command/DiagnoseCommand.php
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - backend/tests/test_extract_errors.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_poller.py
    - backend/tests/test_diagnose_endpoint.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "detail nimmt nicht an der Gleichheit teil (field(compare=False)): Verdikt = state+reason+text, Klasse ist Diagnosedatum; hält die Bestandstests mit == failed(...) gültig"
  - "Tombstone lässt die file_errors-Zeile stehen (wie das Verdikt), give_up und reset_for_reindex räumen sie ab"
  - "Ungültige Klassennamen werden als None gespeichert, das Verdikt wird trotzdem geschrieben"
  - "AdminViewService zeigt errorClass nur, wenn Karte UND Container failed sagen"
  - "errorClass reist nur über /diagnose, nie in der Quittung der Queue; daher kein K6-Rückfall nötig (alte Companion ignoriert den Schlüssel, alter Container liefert ihn nicht -> '')"
metrics:
  duration: "ca. 60 min"
  completed: 2026-10-06
  tasks: 2
  files: 13
---

# Phase 29 Plan 06: Fehlerdetail je Datei (Ausnahmeklasse) Summary

Jedes failed-Urteil aus einer Ausnahme trägt jetzt die geworfene Reader-Klasse als module.qualname (z. B. `zipfile.BadZipFile`, `PIL.UnidentifiedImageError`), gespeichert in der neuen Tabelle `file_errors` und sichtbar in `/diagnose` (`errorClass`) und `occ findling:diagnose` (`error class`), ohne Message, ohne Pfad, ohne Reindex.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | detail im Outcome, Tabelle file_errors und record() | 72da4c6c (RED), 6f4ec473 (GREEN) |
| 2 | errorClass in /diagnose, occ und Admin-Diagnose, Pins | 62900e47 (RED), d9a2b87c (GREEN) |

## Was gebaut wurde

- `errors.py`: `detail: str | None = field(default=None, compare=False)` am Ende des Outcomes (Pickle-Weg); `failed(reason, *, detail=None)`; `from_exception` setzt `type(error).__module__ + "." + __qualname__` der geworfenen Klasse in beiden Zweigen, nie `str(error)`.
- `schema.sql`: `CREATE TABLE IF NOT EXISTS file_errors(file_id INTEGER PRIMARY KEY, error_class TEXT NOT NULL, recorded_at INTEGER NOT NULL)` mit Kommentar; `SCHEMA_VERSION` unverändert "2".
- `repo.py`: `record(..., error_class=None)` prüft vor der Transaktion gegen `[A-Za-z0-9_.]{1,200}`, schreibt `INSERT OR REPLACE` bzw. `DELETE` im selben `_transaction()` wie das Verdikt; `error_class(file_id)` liefert None auch bei fehlender Tabelle (Lesepfad vor dem nächsten Schreib-Open); `give_up` löscht die Zeile, `reset_for_reindex` räumt verwaiste Zeilen ab.
- `poller.py`: `_record_verdicts` reicht `error_class=verdict.outcome.detail` durch; Quittung unverändert (`{queue_id: reason}`).
- `diagnose.py`: `errorClass: str = ""`, gefüllt aus `store.error_class(file_id)` im selben try-Block (sqlite3.Error -> NOT_JUDGED wie bisher).
- `AdminViewService.php`: `ERROR_CLASS_PATTERN`, `public static errorClass(?array): string`, `containerVerdict` liest das Feld, `diagnosis()` hat jetzt 15 Schlüssel (`errorClass` nach `remedy`), gesetzt nur bei Karten- und Container-Zustand failed.
- `DiagnoseCommand.php`: Zeile `error class` nach `reason code`, leer als `-`.
- Pins: `PHP_TREE_HASH_TODAY` 3f72f80d..., `PACKAGE_TREE_HASH_TODAY` 59653dff... (Dateizahlen 88/71 unverändert; schema.sql zählt nicht, Rezept liest `**/*.py`).

## Verifikation

- Volle Suite: 4517 passed, 25 skipped (PYTHONUTF8=1).
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.
- Pfad-Leak-Test (`/geheim/pfad` in der Message), Pickle-Test, Bestands-DB-Test (Tabelle gedroppt -> Read-only liefert None, nächster `open_store` legt sie an, Meta/index_version/Schema-Marke unverändert), Shape-Tests (Pfad, Message, `<locals>`, 201 Zeichen, leer) grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] detail aus der Dataclass-Gleichheit genommen**
- **Found during:** Task 1 (volle Suite)
- **Issue:** 8 Tests in `test_extract_documents.py` vergleichen `outcome == ExtractionOutcome.failed(Reason.CORRUPT)`; mit detail im Vergleich wären gleiche Verdikte ungleich.
- **Fix:** `field(default=None, compare=False)`, eigener Test `test_the_detail_is_no_part_of_the_verdict`; Pickle-Test prüft detail explizit.
- **Commit:** 6f4ec473

**2. [Rule 2 - Korrektheit] give_up und reset_for_reindex räumen file_errors**
- **Issue:** Ein Verdikt der Gegenseite (repeatedly_stuck) oder ein Reindex hätte eine veraltete Klasse neben einem anderen bzw. fehlenden Verdikt stehen lassen.
- **Fix:** DELETE in derselben Transaktion; Tests für beide Pfade.
- **Commit:** 6f4ec473

**3. [Rule 2 - Korrektheit] error_class() übersteht eine Bestands-DB ohne Tabelle**
- **Issue:** `open_read_only` führt schema.sql nicht aus; `/diagnose` hätte bis zum nächsten Schreib-Open eine Bestands-DB als NOT_JUDGED gemeldet.
- **Fix:** `sqlite3.OperationalError` -> None; Tests in test_store_repo und test_diagnose_endpoint.
- **Commit:** 6f4ec473, d9a2b87c

**4. [Umfang] Poller-Tests ergänzt** (`test_the_class_of_the_reader_error_is_stored_and_stays_off_the_wire`, `test_a_verdict_without_an_exception_stores_no_error_class`) in `backend/tests/test_poller.py`, nicht in files_modified gelistet.

### Hinweis zur Vorgabe "errorClass nur bei verdicts=2"

errorClass reist ausschließlich über `/diagnose` (Container -> PHP auf Anfrage des Admins), nicht über die Queue-Quittung. Eine alte Companion baut ihre Diagnose Feld für Feld und ignoriert den Schlüssel; ein alter Container liefert ihn nicht und PHP fällt auf `''` zurück. Ein K6-Signal ist daher nicht nötig; die Quittung bleibt per Test unverändert.

## Deferred Issues

- `php -l` per Docker nicht ausführbar: Docker Desktop lief nicht, kein lokales PHP (wie 29-01). PHPUnit und Lint belegt CI php.yml beim Push in 29-11.
- Die Admin-Karte (php/js/admin.js, templates/admin.php) zeigt errorClass noch nicht an: Die JSON-Antwort der Settings-Route trägt das Feld, eine sichtbare Zeile bräuchte ein neues l10n-Label in 16 Katalogen. Außerhalb von files_modified, Kandidat für 29-12.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche über T-29-18..20 hinaus. T-29-18/19 umgesetzt: Form-Prüfung `[A-Za-z0-9_.]{1,200}` im Container (vor der Transaktion) und erneut in PHP, nie Message oder Pfad.

## TDD Gate Compliance

RED/GREEN je Task vorhanden: test 72da4c6c -> feat 6f4ec473, test 62900e47 -> feat d9a2b87c. Zwischen 6f4ec473 und d9a2b87c ist der Paket-Pin rot (Pin einmal am Ende gemessen, wie vorgegeben).

## Self-Check: PASSED

- FOUND: backend/src/findling/store/schema.sql (`CREATE TABLE IF NOT EXISTS file_errors`, 1 Treffer)
- FOUND: backend/src/findling/api/diagnose.py (`errorClass`), php/lib/Command/DiagnoseCommand.php (`'error class'`)
- FOUND: 72da4c6c, 6f4ec473, 62900e47, d9a2b87c
- SCHEMA_VERSION in repo.py unverändert
