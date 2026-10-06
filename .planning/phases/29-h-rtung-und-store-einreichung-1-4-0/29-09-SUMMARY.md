---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 09
subsystem: backend/worker
tags: [recheck, upgrade, sidecar, requeue, k6, issue-18, issue-22]
requires:
  - "29-01: VERDICTS_GENERATION und CompanionChoice.verdicts (K6-Signal), skipped-Codes system_file/legacy_format/unsupported_variant"
  - "29-05: Sidecar-Regel (_is_sidecar in poller.py)"
  - "29-07/29-08: Fixklassen TIFF/JPEG und OLE"
provides:
  - "backend/src/findling/worker/recheck.py: select_candidates(rows), async recheck_step(store, queue) -> bool"
  - "backend/src/findling/store/repo.py: RECHECK_MARK = 'recheck_1_4_0', Store.recheck_scan(after, limit) als Rohzeilen-Leser"
  - "backend/src/findling/extract/errors.py: is_sidecar_name(name), einzige Kopie der Sidecar-Regel"
  - "Poller ruft recheck_step vor dem Claim, nur bei choice.verdicts == VERDICTS_GENERATION"
affects:
  - "29-02/#18/#22-Antworten: Zusage 're-checked after the upgrade, no manual cleanup' ist jetzt gebaut"
  - "Upgrade 1.3.2 -> 1.4.0: einmaliger Requeue-Lauf nach dem Companion-Update"
tech-stack:
  added: []
  patterns:
    - "Meta-Marke als Sweep-Position (Leer/Ziffern/done) statt index_version, wie EMBEDDING_BACKLOG_MARK"
    - "Cursor erst nach ok eines Bandes (Bug-Audit M1), Bänder zu REQUEUE_BAND aus reconcile importiert"
    - "Auswahl in Python über den Basisnamen, kein SQL LIKE (T-29-17)"
key-files:
  created:
    - backend/src/findling/worker/recheck.py
    - backend/tests/test_recheck.py
  modified:
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_extract_errors.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_poller.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Cursor wird nach jedem ok-Band auf die letzte übergebene file_id geschrieben und nach jedem vollständigen Scanblock (2000 Zeilen) auf die letzte gelesene file_id; ein Wiederholungslauf scannt höchstens die Nicht-Kandidaten zwischen beiden erneut"
  - "Poller hält zusätzlich ein Prozess-Flag _recheck_done, damit nach 'done' keine Runde mehr die Meta-Tabelle liest; Wahrheit bleibt RECHECK_MARK"
  - "Sidecar-Prüfung in der Nachprüfung über PurePosixPath(path).name ohne Titel-Rückfall: recheck_scan liefert wie geplant vier Spalten; Zeilen mit leerem Pfad (reconcile give_up) tragen ohnehin title NULL"
  - "Poller-Verdrahtungstests liegen in test_poller.py (dort sind _FakeQueue/_poller-Fixtures), nicht in test_recheck.py"
metrics:
  duration: "ca. 40 min"
  completed: 2026-10-06
  tasks: 2
  files: 9
---

# Phase 29 Plan 09: Altbestands-Nachprüfung nach dem Upgrade Summary

Einmaliger, wiederaufnehmbarer Requeue-Lauf über die Fixklassen (failed corrupt/out_of_memory, skipped system_file/legacy_format/unsupported_variant, jede Sidecar-Zeile), in Bändern zu 200 mit Cursor in der Meta-Marke `recheck_1_4_0`, gestartet erst beim Companion-Signal `verdicts == 2`, ohne Vollreindex.

## Was gebaut wurde

- **Task 1** (`3d411e36` RED, `dd22a14b` GREEN): `is_sidecar_name` aus `poller.py` nach `extract/errors.py` verschoben (Körper unverändert, Poller importiert sie). `repo.py` bekommt `RECHECK_MARK` und `recheck_scan` (lebende Zeilen über dem Cursor, aufsteigend, Rohzeilen plus letzte gelesene id, kein Import aus `findling.extract`, kein LIKE). Neues Modul `worker/recheck.py` mit `_RECHECK_FAILED`, `_RECHECK_SKIPPED`, `select_candidates` und `recheck_step`; `REQUEUE_BAND` aus `reconcile` importiert; Store-Aufrufe per `asyncio.to_thread`; Logzeilen nur mit Zahlen.
- **Task 2** (`26cde98f` RED, `9a0dd014` GREEN): Poller ruft `recheck_step` direkt nach den `note_*`-Aufrufen und vor dem Claim, nur bei `choice.verdicts == VERDICTS_GENERATION`, in try/except mit Klassennamen im Log. Pins nachgezogen.

## Tests

- `test_recheck.py` (12): Auswahl (inkl. ocr_failed, `.hidden`, `a._b`, Sidecar-Ordner nicht), 450 Kandidaten = Bänder 200/200/50 kind content, not-ok bei Band 2 (Cursor 200, nächster Lauf ab 201), neuer Prozess setzt am Cursor fort, done-Endzustand ohne weiteren Requeue, frische Installation schreibt done, Cursor "abc" startet bei 0, Tombstones und normale Dokumente bleiben, Meta-Marken außer RECHECK_MARK und index_version unverändert, Logs ohne Pfad.
- `test_store_repo.py` (3): `recheck_scan` Reihenfolge/Tombstones/Blockende, RECHECK_MARK nicht in `_DEFAULT_META`.
- `test_extract_errors.py` (2) und die bestehenden Poller-Sidecar-Tests über den neuen Import.
- `test_poller.py` (3): ohne Signal kein Requeue und Marke leer; mit Signal wird eine als failed(corrupt) gespeicherte `._x.docx` neu eingereiht und endet als skipped(system_file), danach kein Requeue mehr; eine Ausnahme in `recheck_step` beendet die Runde nicht und wird in der nächsten Runde erneut versucht.

## Pins

Gemessen mit `run_the_recipe` über `backend/src/findling/**/*.py`: 73 Dateien, Hash `0289455f79e19fa30c51cf36855b1aa1e0546050fe7e2e05615418b3391252b7`. Ausgangsstand nach 29-08 war 72 / `266b49ea...`. `git diff --name-status 7db0966d -- backend/src php` belegt die einzige neue Datei `worker/recheck.py` (A) und drei geänderte (errors.py, repo.py, poller.py); php/ unverändert, PHP-Pin `3f72f80d...` bleibt. Keine Abweichung zur Erwartung 73.

## Gates

Volle Suite 4644 passed, 25 skipped (PYTHONUTF8=1); ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.

## Deviations from Plan

None in der Sache. Zwei Ausführungsdetails, beide im Rahmen des Plans:
- Cursor wird pro ok-Band (letzte übergebene id) und pro Scanblock (letzte gelesene id) geschrieben, damit der Behavior-Fall "Cursor steht nach Band 1" bei 450 Kandidaten innerhalb eines Scanblocks gilt.
- Die Poller-Verdrahtungstests stehen in `test_poller.py` statt `test_recheck.py`, weil dort die Fake-Queue und `_poller` liegen; `_FakeQueue` reicht dafür `verdicts_answer` durch.

## Threat Flags

Keine neue Oberfläche: keine neue Route, Übergabe über die bestehende requeue-Route (T-29-32), Bänder höchstens 200 (T-29-29), index_version und Vektor-Marken unberührt (T-29-30), Marke done verhindert Wiederholung (T-29-31).

## Self-Check: PASSED

- backend/src/findling/worker/recheck.py vorhanden
- backend/tests/test_recheck.py vorhanden
- Commits 3d411e36, dd22a14b, 26cde98f, 9a0dd014 im Log
