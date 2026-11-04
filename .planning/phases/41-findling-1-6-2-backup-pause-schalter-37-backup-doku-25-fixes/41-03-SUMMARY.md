---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 03
subsystem: worker (poller, embedding, reconcile, watch, pause)
tags: [issue-37, backup-pause, wal-checkpoint, tree-hash]
requires:
  - 41-02 (Baumhash-Stand 906e72a0, 80 Dateien)
provides:
  - PauseCoordinator mit Zuständen running/pausing/paused/unknown, wants_pause(), attach_* , run(), tick()
  - checkpoint_wal(path, *, busy_timeout_ms) mit PRAGMA wal_checkpoint(TRUNCATE)
  - Backup-Hold (hold_for_backup/release_backup_hold/backup_held) in Poller, EmbedRunner, Reconcile
  - Poller.quiesce_for_backup / reopen_after_backup, Reconcile.in_flight, GuardWatch.suspend_persist/resume_persist
affects:
  - 41-04 (Verdrahtung Lifespan, /profile-Wunsch, Status, Probe, Rebuild should_stop)
  - 41-05/41-06 (Companion-Seite)
tech-stack:
  added: []
  patterns:
    - "Eigenes asyncio.Event je Schreiber neben arm/silence und Probe-Hold (bei Geburt gesetzt, Koordinator löscht beim attach)"
    - "Koordinator mit injizierbarem Checkpoint und Takt für Tests; tick() als ein Schritt"
key-files:
  created:
    - backend/src/findling/worker/pause.py
    - backend/tests/test_backup_pause.py
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/embedding.py
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/worker/watch.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Reconcile.in_flight gilt für die ganze Runde von run() (Gate, Kadenz, Scheiben, Sweep schreiben alle in state.db); der Hold beendet die Runde an der nächsten Scheibengrenze mit ROUND_HELD = 'held', Lesezeichen bleibt"
  - "on_resume läuft bei jedem Übergang aus einem gehaltenen Zustand (unknown, pausing, paused) nach running, auch beim ersten lesbaren Wunsch nach dem Start"
  - "Ein nicht lesbarer Wunsch (None oder Exception) ändert im Betrieb nichts; nur der Start ist gehalten (D-41-19)"
  - "Poller.reopen_after_backup öffnet beim Resume den Track vor dem Lösen der Holds, weil der EmbedRunner denselben Track fährt und vor dem nächsten Poller-Pass starten kann"
metrics:
  duration: "ca. 55 min"
  completed: 2026-11-04
  tasks: 2
  commits: 5
---

# Phase 41 Plan 03: Backup-Pause, Backend-Kern Summary

Jeder Schreiber des Volumes hat einen eigenen Backup-Hold, den weder Enable noch Probe-Ende noch Rebuild-Arm aufhebt, und ein PauseCoordinator meldet "paused" erst, nachdem der laufende Pass regulär endete, der Poller seinen Tantivy-Writer abgab und state.db und vectors.db per `wal_checkpoint(TRUNCATE)` auf eine 0-Byte-WAL gebracht wurden.

## Commits (RED vor feat)

| Hash | Nachricht |
|------|-----------|
| 7d9a39a4 | test(41-03): a backup pause must hold every writer (#37) |
| 6dbfac39 | feat(41-03): a backup hold for every writer (#37) |
| a7009cef | test(41-03): the backup pause reports paused only after the checkpoint (#37) |
| 3ba6dd78 | feat(41-03): a coordinator that flushes everything before it reports paused (#37) |
| 9beebf41 | test(41-03): the package tree hash follows the backup pause |

Alle als street1983nk <k.cherif@outlook.de>, 0 Trailer-Zeilen. Kein Push.

## Task 1: Holds in allen Schreibern

- poller.py: `_backup_release` (bei Geburt gesetzt), `hold_for_backup`, `release_backup_hold`, `backup_held`; `run` wartet nach dem Probe-Block auf das Event. `quiesce_for_backup`: unlock_held, `writer.close()` im Thread, `track.close()`, KEIN `_armed.clear()`, idempotent über `_backup_quiesced` (von `_open()` zurückgesetzt). `reopen_after_backup` öffnet nur den Track wieder.
- embedding.py: gleiches Event, `run` wartet, `parked` bleibt gesetzt.
- reconcile.py: Event, `in_flight` (um `run_once` in `run`), Hold-Prüfung vor jeder Scheibe in `_walk` -> `ROUND_HELD`.
- watch.py: `suspend_persist` / `resume_persist`; `_persist_if_changed` schreibt während der Suspendierung nicht, die Revision bleibt im Guard und wird beim Resume einmal geschrieben.
- RED-Beleg: 7d9a39a4 scheiterte beim Import (`ROUND_HELD`, Methoden fehlten).

## Task 2: PauseCoordinator, checkpoint_wal

- pause.py: Konstanten E-41-03-02/04 (`PAUSE_POLL_SECONDS = 15`, `PAUSE_SETTLE_SECONDS = 1`), `PauseState`, Protocols für die vier Schreiberarten, `checkpoint_wal` (fehlende Datei True ohne Anlegen, busy_timeout aus repo.py, True bei busy 0 oder log -1, sqlite3.Error -> WARNING mit Klassenname, False), `PauseCoordinator` mit `attach_poller/runner/reconcile/guard_watch`, `state`, `paused_since`, `wants_pause`, `tick`, `run`.
- Wartebedingung vor quiesce: kein Pass, Runner geparkt, keine Reconcile-Runde, `rebuild_busy()` und `probe_busy()` False. Quiesce einmal je Eintritt, Checkpoint-Retry im Takt PAUSE_SETTLE_SECONDS; Wunsch nur alle PAUSE_POLL_SECONDS gelesen.
- Logzeilen nur "backup pause: pausing|paused|running" plus Klassennamen; `grep -nE "LOGGER\.(info|warning).*(path|db)"` leer.
- 19 neue Tests (Checkpoint mit echter SQLite inkl. Leser-Transaktion -> busy, ohne WAL, fehlende/kaputte Datei; alle Zustandsübergänge; Integrationsfall mit zwei echten WAL-Dateien -> beide 0 Byte nach "paused"; run-Schleife).

## Baumhash

| Paar | alt | neu |
|---|---|---|
| PACKAGE (80 -> 81 Dateien) | 906e72a0... | 9465a3ab... |

Zweimal gerechnet (40b-baumhash.py und find/sort/tr/sha256sum), `-k tree_hash` 4 passed. PHP-Paar unverändert.

## Verifikation

- tests/test_backup_pause.py: 30 passed.
- Bestehende Tests (Dateien unverändert): poller, reconcile, reconcile_vanished, embedding_runner, embedding_track, watch, probe_run vorher 546 passed / 3 skipped, nachher gleich.
- Sammellauf (13 Dateien inkl. main_lifespan, lifecycle, phase40_audit, measurement_scripts, catchup): 1345 passed, 10 skipped.
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture 80 grün.
- Kein neuer Meta-Schlüssel (`git diff v1.6.1 -- backend/src | grep -E '^\+.*(write_meta|set_meta)'` leer), keine U+2013/U+2014 im Delta.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] Track nach Resume vor dem Runner öffnen**
- **Found during:** Task 1
- **Issue:** `quiesce_for_backup` schließt den Track, den auch der EmbedRunner fährt. Nach dem Resume kann der Runner vor dem nächsten Poller-Pass (der `_open()` ruft) starten und träfe einen geschlossenen Track.
- **Fix:** `Poller.reopen_after_backup()`; der Koordinator ruft es beim Resume vor dem Lösen der Holds (Fehler nur geloggt, der nächste Pass öffnet ohnehin). `_open()` setzt das Quiesce-Flag zurück, damit die nächste Pause wieder abgibt.
- **Commits:** 6dbfac39, 3ba6dd78

**2. [Rule 3 - Blocking] in_flight nicht über Umbenennung von run_once**
- **Issue:** Erster Ansatz (run_once -> Wrapper, Rumpf in `_round`) brach den Quellprobe-Test `test_the_sweep_only_follows_a_full_walk_without_a_discard` (liest `inspect.getsource(Reconcile.run_once)`).
- **Fix:** `_in_flight` wird in `run()` um den Aufruf gesetzt (Muster des Pollers); `run_once` unverändert. Der Test der Scheibengrenze läuft deshalb über `run()` und prüft die Logzeile "reconcile round held".

**3. Checkpoint injizierbar, busy_timeout als Parameter**
- `PauseCoordinator(checkpoint=..., poll_seconds=..., settle_seconds=...)` und `checkpoint_wal(..., busy_timeout_ms=...)`, damit der Busy-Fall ohne 10 s Wartezeit testbar ist. Defaults wie im Plan.

**4. Hinweis zur Plan-Prüfzeile:** `sed -n '/def quiesce_for_backup/,/^    def /p' | grep -c _armed.clear` ergibt 1, weil der Bereich über `async def reopen_after_backup` hinaus bis in `stand_down` reicht. Präzise geprüft (`/async def quiesce_for_backup/,/async def reopen_after_backup/`): 0.

**5. Baumhash zwischen den Commits:** Zwischen 6dbfac39 und 9beebf41 ist `-k tree_hash` rot (Plan legt den Nachzug bewusst ans Ende von Task 2).

## Known Stubs

Keine. Der Koordinator ist noch nicht in der Lifespan verdrahtet; das ist der Auftrag von 41-04.

## Threat Flags

Keine neue Fläche: keine Route, kein Feld, kein Meta-Schlüssel. T-41-12 bis T-41-15 je mit Test (Checkpoint vor "paused", eigene Events gegen arm/Probe, kein Abbruch mit Quittung, Logzeilen ohne Pfad).

## Self-Check: PASSED

- pause.py, test_backup_pause.py vorhanden; Commits 7d9a39a4, 6dbfac39, a7009cef, 3ba6dd78, 9beebf41 vorhanden.
