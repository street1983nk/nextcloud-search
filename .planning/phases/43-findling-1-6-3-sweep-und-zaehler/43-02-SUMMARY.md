---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 02
subsystem: backend/worker/reconcile
tags: [reconcile, storage-sweep, quiet-gate, backup-pause, issue-25]
requires: []
provides:
  - "SWEEP_MARK = storage_sweep_at (store/repo.py)"
  - "Reconcile._cadence_due, Reconcile._sweep_due"
  - "_sweep_vanished -> bool | None (True vollständig, False Band abgelehnt, None Backup-Pause)"
affects:
  - backend/src/findling/worker/reconcile.py
  - backend/src/findling/store/repo.py
tech-stack:
  added: []
  patterns:
    - "eigener Meta-Stempel unter der Kadenzregel des Walks"
    - "Sweep vor dem Walk, hinter der unveränderten Bedingung found.mounts and not found.discarded"
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-02-SUMMARY.md
  modified:
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/store/repo.py
    - backend/tests/test_reconcile_vanished.py
    - backend/tests/test_catchup.py
    - backend/tests/test_phase36_audit.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "SWEEP_MARK liegt in store/repo.py neben CATCHUP_MARK (Plan-Vorgabe: dort, wo CATCHUP_MARK liegt)"
  - "Ein fälliger Sweep hinter leerer oder verworfener Mountliste ruft _back_off nur, wenn kein Walk fällig ist; ein erfolgreicher Sweep setzt den Cooldown zurück, ein abgelehntes Band behält den Back-off auch über einen folgenden Walk"
  - "Stempel wird als ganze Sekunden geschrieben und mit int() gelesen; '', 'inf', 'nan', '1.5' und Text gelten als nie gelaufen (sofort fällig)"
metrics:
  duration: "ca. 75 min (davon ca. 13 min Volltestsuite in zwei Hälften)"
  completed: 2026-11-07
  tasks: 2
  files: 6
---

# Phase 43 Plan 02: Storage-Sweep vom Quiet-Gate entkoppelt Summary

Der Storage-Sweep läuft jetzt einmal pro Abgleich-Takt unter dem eigenen Meta-Stempel `storage_sweep_at`, vor dem Walk und auch dann, wenn das Quiet-Gate den Walk blockiert (Crawl unfertig oder Warteschlange über quiet_max); T-36-13 bleibt wörtlich, eine unlesbare Warteschlange sweept nie.

## Umsetzung

- `run_once`: `_quiet` liefert ROUND_QUEUE_UNAVAILABLE -> sofort zurück (D-43-02). Catch-up (Schritt 1b, Rewind) nur bei `gate is None`. `walk_due = gate is None and _is_due`, `sweep_due = _sweep_due`; keins fällig -> `gate or ROUND_NOT_DUE` ohne Mountlisten-Abruf. Danach Mountliste, dann Schritt 3b: Sweep nur bei `sweep_due and found.mounts and not found.discarded and backup_release.is_set()`. Der alte Schritt 5 hinter dem Walk ist entfallen; genau ein Aufruf von `_sweep_vanished`.
- `_sweep_vanished`: filtert `storage_id > 0` vor `files.gone_storages`, prüft vor jedem Speicher die Backup-Pause (eigene Logzeile "storage sweep paused for a backup, %d storages handed over"), gibt True/False/None zurück. Logzeile sonst unverändert (nur Zähler und IDs).
- `_is_due` nutzt `_cadence_due(last_finished_at)`, Verhalten unverändert; `_sweep_due` liest den Stempel über `read_meta`.
- `VANISHED_STORAGE_GRACE_SECONDS: Final = 30 * 86_400` unverändert, keine Einstellung.

## TDD

- RED (a32b89f5): 16 failed, 16 passed in tests/test_reconcile_vanished.py (fehlendes SWEEP_MARK, Sweep nur nach Walk, kein Stempel, kein ID-Filter, keine Pause-Prüfung, alte Reihenfolge in der Quelltext-Sonde). Der Test "gehaltene Pause startet keine Runde" war schon vorher grün (bestehendes Verhalten aus #37, hier nur als Regression festgehalten).
- GREEN (d78416df): tests/test_reconcile_vanished.py 37 passed (inkl. neuem Test für unlesbare Stempel, 5 Parameter).
- W11-Messung: dauerhaft verworfene Mountliste bei busy-Gate über 12 simulierte Stunden mit run()-Schleife (Tick 300 s plus Cooldown): 14 Mountlisten-Abrufe statt 144 (Grenze im Test 18). Danach ist die Liste wieder gut: nächste Runde sweept, setzt Stempel, Cooldown 0.
- Takt-Test: 576 Runden über 48 h im crawling-Zustand: genau 2 Sweeps (t=0 und t=24 h), 2 Mountlisten-Abrufe, 0 Seitenabrufe.

## Gates und Tests

- ruff check: All checks passed; ruff format --check: 248 files already formatted; pyright (latest): 0 errors; vulture --min-confidence 80: leer.
- Betroffene Module (reconcile_vanished, reconcile, backup_pause, catchup, measurement_scripts, phase31/36/41_audit, lifecycle, main_lifespan, poller, recheck, upgrade_seed_steps): 1390 passed, 1 skipped.
- Volltestsuite in zwei Hälften mit den --ignore aus 40-01 (6,5 GB frei): `tests/test_[a-m]*.py` 3213 passed, 43 skipped; `tests/test_[n-z]*.py` 3547 passed, 288 skipped.
- Baumhash: PACKAGE_TREE_HASH_TODAY f6716e41... -> c9147c42c8ee727f0f23e6eda4f3319703fd277c9cb5f542f7c30b0acdb85af4, PACKAGE_FILES_TODAY bleibt 81. Zweimal gerechnet: Rezept 40b-baumhash.py und unabhängig find | LC_ALL=C sort | tr -d '\r' | sha256sum, beide c9147c42; Positivkontrolle: dieselbe Pipeline über `git archive HEAD` vor dem Schritt ergab f6716e41. PHP-Paare unberührt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] tests/test_phase36_audit.py an die neue Reihenfolge angepasst**
- **Found during:** Task 2
- **Issue:** Zwei Audit-Sonden aus Phase 36 (`test_the_sweep_is_reached_only_behind_a_full_walk_of_a_clean_list`, `test_the_sweep_runs_for_a_walked_round_only[ended_early]`) schrieben die alte Regel "Sweep nur nach vollem Walk" fest. Die Datei stand nicht in files_modified des Plans.
- **Fix:** Syntaxbaum-Sonde umbenannt in `test_the_sweep_is_reached_only_behind_a_clean_list`: ein Aufruf, Guard enthält `found.mounts and (not found.discarded)`, Guard vor der Walk-Schleife, kein Aufruf in der Schleife, `found.unavailable` vor dem Guard. Parametrisierter Test umbenannt in `test_the_sweep_runs_for_a_clean_list_only`; `ended_early` erreicht den Sweep jetzt (gewollt nach D-43-01), empty/discarded/unavailable weiterhin nicht. Die historischen Namen in 36-AUDIT.md bleiben als Archiv unverändert.
- **Commit:** d78416df

**2. [Rule 3 - Blocking] tests/test_catchup.py: Digest ohne Sweep-Stempel**
- **Found during:** Task 2
- **Issue:** `test_the_catch_up_cycle_leaves_every_known_row_byte_for_byte` hasht alle Meta-Werte außer CATCHUP_MARK; der neue Stempel `storage_sweep_at` veränderte den Digest.
- **Fix:** `_digest` lässt SWEEP_MARK zusätzlich aus (Buchhaltung des Reconcile, keine Dateizeile). Datei stand in files_modified.
- **Commit:** d78416df

**3. [Rule 2 - Korrektheit] Unlesbarer Stempel und Back-off nach Walk**
- Stempel wird mit `int()` gelesen, damit "inf"/"nan" den Sweep nicht dauerhaft sperren; Test `test_an_unreadable_stamp_reads_as_never_swept`.
- Ein abgelehntes Band behält den Back-off auch, wenn danach in derselben Runde ein Walk durchläuft (`if swept is not False: _reset_cooldown()`).
- Commit: d78416df

**4. Testanpassung in test_reconcile_vanished.py (Task 1)**
- `test_an_unsure_round_neither_deletes_nor_stamps` verliert den Parameter `ended_early` (abgebrochener Walk ist nach D-43-01 kein unsicherer Zustand für den Sweep mehr); Ersatz `test_a_walk_that_ended_early_has_already_swept`.

Sonst Plan wie geschrieben. Modul-Docstring von reconcile.py im Absatz zum Sweep nachgezogen.

## Nicht erledigt / Hinweise

- STATE.md und ROADMAP.md wurden NICHT aktualisiert (43-01 läuft parallel, Auftrag des Koordinators nennt nur SUMMARY); bitte durch den Koordinator.
- Nichts gepusht.

## Self-Check: PASSED

- backend/src/findling/worker/reconcile.py, backend/src/findling/store/repo.py: vorhanden, `"storage_sweep_at"` gefunden, genau 1 `await self._sweep_vanished`.
- Commits a32b89f5 (test) und d78416df (feat) im Log, Autor street1983nk <k.cherif@outlook.de>, kein Trailer, kein closes/fixes/resolves.
