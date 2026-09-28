---
phase: 25-einbettungsspur-und-modellwahl
plan: 09
subsystem: worker
tags: [embed-runner, lane, parallel, idx-08, abort-semantics, PAR-01, PAR-04]
requires: ["25-05", "25-06", "25-07", "25-08"]
provides:
  - "findling.lane: MODE_INLINE/MODE_PARALLEL, REASON_NONE/ECONOMY/OLD_COMPANION/MEMORY, LaneSnapshot, note_echo, note_refused, note_mode, snapshot, reset"
  - "findling.worker.embedding.EmbedRunner: arm, silence, run, run_once, stand_down, unlock_held, aclose, busy, cooldown, parked"
  - "findling.worker.embedding: LANE_PARKED, ROUND_EMPTY/WORKED/PAUSED/GATEWAY_UNAVAILABLE, EMBED_RUNNER_TICK_SECONDS, EMBED_RUNNER_BACKOFF_MAX_SECONDS, RUNNER_PARK_WAIT_SECONDS, RUNNER_STAND_DOWN_SECONDS"
  - "EmbeddingTrack.cutter_built"
  - "Poller.track, Poller.attach_runner, ROUND_PAUSED_STORE_ERROR, ROUND_WAITING_FOR_RUNNER"
affects:
  - "25-10 (Lifespan baut EmbedRunner über poller.track, attach_runner, arm/silence/stand_down/unlock_held)"
  - "25-12 (Status meldet lane.snapshot(): mode, reason)"
tech-stack:
  added: []
  patterns:
    - "Zweiter Nebenläufer nach dem Reconcile-Muster, Tor je Runde, Parken als asyncio.Event"
    - "Modulzustand mit reset() nur für Tests (wie profile.py/precision.py)"
key-files:
  created:
    - backend/src/findling/lane.py
    - backend/tests/test_embedding_runner.py
  modified:
    - backend/src/findling/worker/embedding.py
    - backend/src/findling/worker/poller.py
    - backend/tests/conftest.py
    - backend/tests/test_poller.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Läuft die Park-Wartezeit ab, beansprucht die Runde nichts (ROUND_WAITING_FOR_RUNNER, Backoff) statt ohne Parken zu beanspruchen: IDX-08 bleibt wörtlich"
  - "Der Poller wartet in Economy immer dann auf runner.parked, wenn ein Runner angehängt und nicht geparkt ist, nicht nur bei Modus parallel (Obermenge, sicherer)"
  - "SQLite-Fehler oder Plattenboden im Runner: alle gehaltenen Zeilen per unlock zurück, auch schon eingebettete, keine Quittung (Skizze der Research); Wiederholung ist über replace_chunks idempotent"
  - "Runner prüft die Stufe zusätzlich hinter der Track-Sperre und vor jeder Zeile; Zeilen fremder Art in einer Antwort mit Echo gehen unbeurteilt zurück"
  - "Byte-Deckel des Runner-Anspruchs = settings().batch_max_bytes, derselbe wie im Anspruch der Hauptschleife (eine eigene Konstante gab es nicht)"
  - "engine_state und Uhr am Runner injizierbar, damit die Ladekosten und die Flatter-Sperre deterministisch testbar sind"
metrics:
  duration: "ca. 60 min"
  completed: 2026-09-28
  tasks: 3
  files: 7
requirements: [PAR-01, PAR-04]
---

# Phase 25 Plan 09: EmbedRunner und Spurentscheid Summary

Zweiter Nebenläufer `EmbedRunner` nach dem Reconcile-Muster: Tor je Runde (Stufe, Echo, RAM statisch und live), Einbettung genau einer Zeile zur Zeit unter der Track-Sperre, Parken als Event, das die Hauptschleife in Economy vor ihrem Anspruch abwartet; jeder Ausstieg ohne Quittung gibt Zeilen per unlock zurück, ohne Verdikt.

## Umsetzung je Task

**Task 1: lane.py und EmbedRunner** (d660f6b)
- `lane.py` neutral (stdlib, loggt nichts): Modi, geschlossene Gründe, `note_echo` (ignoriert nach Verweigerung), `note_refused` (prozesslebenslang), `note_mode` (wirft bei unbekanntem Wert), `snapshot`, `reset`; `lane.reset()` im autouse-Fixture neben profile und precision.
- `EmbedRunner`: Konstruktor ohne I/O, Client und Queue erst in der ersten offenen Runde. Tor in der Reihenfolge Stufe STANDARD/PERFORMANCE, `lane.supported`, `embed_lane_fits`, live `admits(headroom, need)` im Thread mit `need = EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES` plus `CUTTER_LOAD_BYTES` (Cutter nicht gebaut) plus `EMBED_WEIGHTS_LOAD_BYTES` (+ `FP32_EXTRA_BYTES` bei fp32), falls die Engine nicht `loaded` ist. Nach einem Speicher-Nein wird der Headroom erst nach einem vollen Tick wieder gelesen.
- Runde unter `async with track.lock`: `claim(limit=EMBED_CLAIM_BATCH, ..., lane=LANE_EMBED)`, fehlendes Echo gibt alles zurück und parkt dauerhaft, leere Antwort ruft den Markenschritt unter der Sperre, Zeilen seriell mit Stufenprüfung je Zeile, `except (sqlite3.Error, _DiskTight)` mit `_abort`-Semantik, am Ende acknowledge(done) und unlock(Rest). `run` gibt im Generalfang erst `unlock_held` frei und loggt dann nur den Typnamen.
- `EmbeddingTrack.cutter_built` als lesende Property.

**Task 2: Spurentscheid der Hauptschleife** (9016518)
- Nach `note_chosen`: in Economy mit angehängtem, nicht geparktem Runner Warten auf `runner.parked` (höchstens `RUNNER_PARK_WAIT_SECONDS = 60`); danach `lane=LANE_INDEX` nur bei Modus parallel und nicht Economy, sonst keine lane (T13 unverändert). `lane.note_echo(claim.lane_honored)` nach jeder Antwort.
- Rumpf der Runde nach `_work` ausgelagert; `except sqlite3.Error` davor mit `_abort` (unlock, Backoff, `ROUND_PAUSED_STORE_ERROR`, kein Verdikt).
- Nach erfolgreichem requeue verlassen die übergebenen queue_ids `_held` (Pattern 5.3).
- `Poller.track` und `Poller.attach_runner` für Plan 25-10.
- Tests: T1 (Economy, Runner-Task läuft mit, keine Überlappung), T2 (Standard, OCR blockiert bis der Embedder startet, Überlappung belegt), T4 (Wechsel auf Economy mitten in der Runner-Runde: Poller wartet, Rest per unlock, danach keine Überlappung) mit echtem Poller plus Runner; in test_poller.py Index-Spur bei Modus parallel, Echo, Parkwarten, Zeitdeckel, SQLite-Abbruch, Übergabe aus `_held` (beide Richtungen).

**Task 3: T3 und Pins** (7fba758)
- T3: Kindprozess mit CPU-Schleife (OCR-Stand-in) neben CPU-Schleife im Thread (Embedder) über Poller und Runner; CPU-Zeit über `os.times()` (Kinder) und `time.thread_time()`; Summe größer als die Wandzeit des Fensters; `skipif(sys.platform != "linux" or cores < 2)`. Lokal übersprungen; die Logik wurde einmal auf Windows mit abgeschalteter Plattformbedingung und angenommener Kind-CPU durchgespielt (grün), dann verworfen.
- `PACKAGE_FILES_TODAY = 64`, `PACKAGE_TREE_HASH_TODAY = a2a15da9...42fea8` über den Worktree-Baum (Welle 3 gemergt plus dieser Plan) gemessen, Kommentar "Measured again after the wave-3 merge ...".

## Verifikation

- `uv run pytest -q`: 3654 passed, 16 skipped (T3 skipped mit Grund)
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 Fehler), vulture `src tests --min-confidence 80`: grün
- `git diff --stat -- php backend/src/findling/main.py`: leer
- Akzeptanz-Greps: `class EmbedRunner` 1, `lane=LANE_EMBED` 1, `memory.current` 0, `Semaphore|EMBED_SLOTS|embed_slots` 0 in embedding.py; `"companion_without_lane"` 1 in lane.py; `LANE_INDEX` 2, `note_echo(` 1, `def track` 1, `except sqlite3.Error` 1 in poller.py; `sys.platform != "linux"` und `wave-3 merge` vorhanden

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit, T-25-37] Zeitdeckel der Park-Wartezeit beansprucht nichts**
- **Gefunden in:** Task 2
- **Problem:** Der Plan sagt "höchstens RUNNER_PARK_WAIT_SECONDS; erst danach claim ohne lane". Nach Ablauf trotzdem zu beanspruchen hieße, OCR neben einer noch laufenden Einbettung zu starten.
- **Fix:** Neuer Rundenzustand `ROUND_WAITING_FOR_RUNNER`, Backoff, kein Anspruch; die nächste Runde fragt erneut. Test `test_a_runner_that_does_not_park_costs_the_pass_its_claim`.
- **Commit:** 9016518

**2. [Rule 2 - Korrektheit] Warten auf das Parken unabhängig vom Modus**
- **Problem:** Nur bei `mode == parallel` zu warten lässt ein Fenster offen, in dem der Runner sein Tor schon passiert, den Modus aber noch nicht geschrieben hat.
- **Fix:** Gewartet wird in Economy, sobald ein Runner angehängt und nicht geparkt ist; `parked` ist während jeder Runde gelöscht, auch während der Torprüfung.
- **Commit:** 9016518

**3. [Rule 2 - Korrektheit, T-25-39] Stufe hinter der Sperre, fremde Zeilenarten**
- Der Runner prüft die Stufe erneut, nachdem er die Track-Sperre bekommen hat (die Hauptschleife kann sie für eine Inline-Zeile gehalten haben), und gibt Zeilen, die in einer Antwort mit Echo nicht `embed` sind, unbeurteilt zurück.
- **Commit:** d660f6b

### Zusätze

- Eigener Rundenzustand `ROUND_PAUSED_STORE_ERROR` im Poller für den SQLite-Zweig (der Plan nannte keinen Namen).
- Rumpf von `Poller.run_once` nach `_work` ausgelagert, damit der SQLite-Zweig ihn ganz umschließt; verhaltensgleich, alle bestehenden Poller-Tests grün.
- `engine` und `clock` am Runner injizierbar, `RUNNER_STAND_DOWN_SECONDS = 120`, `EMBED_RUNNER_TICK_SECONDS = 15`, `EMBED_RUNNER_BACKOFF_MAX_SECONDS = 300` als benannte Konstanten.

## TDD Gate Compliance

Tests und Umsetzung je Task in einem Commit (`feat` für Task 1 und 2, `test` für Task 3), kein separater RED-Commit: die Tests zeigen auf neue Klassen und Namen (`EmbedRunner`, `findling.lane`, `ROUND_*`) und wären vor der Umsetzung nicht importierbar gewesen. Jeder Behavior-Fall hat einen eigenen Test; ein Testfehler während der Arbeit (Indizierung von `chunks_of`, Reihenfolge zweier gleichzeitiger Ansprüche in T2) wurde im Test behoben, nicht im Code.

## Offene Punkte

- **CI-Nachweis T3 (SC1) offen:** läuft im Job gates auf ubuntu-24.04 erst nach dem nächsten Push; der Push-Entscheid liegt beim Owner.
- Verdrahtung im Lifespan (Runner bauen über `poller.track`, `attach_runner`, arm/silence, stand_down beim Rebuild, `unlock_held` beim Abbau) folgt in Plan 25-10; bis dahin bleibt der Container Wert für Wert der heutige (kein Runner, Modus inline).

## Known Stubs

Keine. Der Runner ist bewusst noch nicht im Lifespan verdrahtet (Planschnitt zu 25-10).

## Threat Flags

Keine neue Oberfläche außerhalb des Threat Registers: der Runner nutzt dieselben Queue-Routen wie die Hauptschleife (claim mit lane, acknowledge, unlock), Logzeilen tragen nur Zähler und Typnamen.

## Self-Check: PASSED

- FOUND: backend/src/findling/lane.py, backend/tests/test_embedding_runner.py
- FOUND: d660f6b, 9016518, 7fba758
