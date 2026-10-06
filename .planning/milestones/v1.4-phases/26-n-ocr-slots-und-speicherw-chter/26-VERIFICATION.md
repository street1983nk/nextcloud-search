---
phase: 26-n-ocr-slots-und-speicherw-chter
verified: 2026-09-29T00:00:00Z
status: passed
score: 4/4
overrides_applied: 0
---

# Phase 26: N OCR-Slots und Speicherwächter Verification Report

**Phase Goal:** Auf Mehrkern-Boxen teilt sich die OCR-Spur auf N Slots auf, die Zusagen "mindestens einmal ausliefern, höchstens einmal indexieren" halten unter Parallelität, und ein Speicherwächter bremst, bevor der Container stirbt.
**Verified:** 2026-09-29
**Status:** passed
**Re-verification:** Nein , Erstverifikation

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | N OCR-Slots lesen gleichzeitig (Semaphore, N Kinder mit eigener Pipe/Zähler, Sperre um IndexBatchWriter.add()); Anspruch liefert >= N OCR-Zeilen | VERIFIED | `extract/pool.py` `class SlotGate`/`class SlotPool` mit eigenem `ThreadPoolExecutor(thread_name_prefix="findling-slot")`; `index/writer.py` `self._lock = threading.RLock()` um add/drop_document/flush; `php/lib/Service/QueueService.php` `KIND_BATCH_INDEX_LANE[KIND_OCR] = 32` nur im Lane `index`, ausgewählt in `claim()` über `LANE_INDEX`; `config.py` `OCR_CLAIM_BATCH_INDEX_LANE = 32`, Paritätstest `test_config.py` liest den PHP-Quelltext und vergleicht live |
| 2 | Kill mitten in halber Staffel (N >= 4) + Neustart: jede Datei genau einmal im Index, keine Zeile verloren (Linux-CI) | VERIFIED | `backend/tests/slots_kill_harness.py` (477 Zeilen, echte SQLite-Warteschlange mit PHP-Lease-Semantik) + `backend/tests/test_slots_kill.py` mit `test_a_killed_main_process_mid_pass_loses_no_row_and_indexes_once` und `test_a_killed_child_mid_pass_is_retried_alone_and_indexed_once`, echtes `os.killpg(..., SIGKILL)`; unabhängig per `gh run view 36522819711 --repo street1983nk/nextcloud-search` bestätigt: Workflow "main Python gates", Job "ruff, format, pyright, vulture, pytest" grün auf `ubuntu-24.04` (einzige Skip-Bedingung `sys.platform != "linux"`, dort also ausgeführt) |
| 3 | Durchsatzfaktor N Slots gegen Sparsam auf arm64-CI gemessen und dokumentiert (Rauschgrenze 1,05); Sparsam bleibt bei 1 Slot, Pin-Test grün | VERIFIED | `scripts/ops/slot_ladder.py` treibt den echten `Poller.run_once`; `.github/workflows/measure.yml` Job "slots" mit cpuset 0/0-1/0-3; unabhängig per `gh run view 36523219615` bestätigt: Workflow "main Wave 0 measurements", Job "W4 slot curve on arm64" grün; Rohdaten und Auswertung unter `docs/measurements/2026-09-slot-leiter-ci/README.md` (Faktoren 2,000 und 1,979, beide über 1,05); `test_config.py` enthält weiterhin den Sparsam-Pin (`OCR_CLAIM_BATCH = 2` unverändert im Lane `all`) |
| 4 | Speicherwächter drosselt Slotzahl bei knapper cgroup; wiederholtes memory.events max oder OOM-Kill senkt Profil selbsttätig um eine Stufe; Statusroute und Adminseite nennen Stufe und Ursache | VERIFIED | `guard.py` `class Escalation` (Delta-Zählung, 235-MiB-Schwelle `GUARD_RESERVE_BYTES`, Fenster `GUARD_WINDOW_SECONDS=600`, Mindestabstand `GUARD_MIN_GAP_SECONDS=60`, `CAUSE_MEMORY_MAX_REPEATED`/`CAUSE_OOM_KILL`/`CAUSE_UNCLEAN_END`); `worker/watch.py` `class GuardWatch` mit `restore`/`run`/`run_once`/`note_shutdown_begins`; `api/status.py` `class GuardReport` mit Feldern chosen/effective/cap/cause/since/token/slotsTarget/slotsInForce/throttled; `php/lib/Service/AdminViewService.php` `guardField()`/`guardCause()` plus `php/templates/admin.php` Zeilen `guardLine`/`slotsLine`, die genau die geforderte Formulierung "gewählt X, wirksam Y (Ursache)" und "OCR-Slots x von y" erzeugen |

**Score:** 4/4 Success Criteria verifiziert

### Owner-Entscheide D-26-01..16 (26-CONTEXT.md)

Stichprobenartig gegen den Code geprüft, alle bindenden Entscheide umgesetzt gefunden:

| Entscheid | Fundstelle | Status |
|---|---|---|
| D-26-01 (Kappe nur wirksam, nie gewählt, persistenter Merker) | `guard.py` `_set_cap`, `META_CAP`-Familie in state.db | VERIFIED |
| D-26-02 (rechnerische Slot-Drossel gegen headroom_bytes) | `guard.py` `throttled_slots()`, `(k-1) x OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES` | VERIFIED |
| D-26-03/D-26-15 (Delta-Zählung, 235 MiB, Fenster 600s/60s) | `guard.py` `class Escalation.observe` | VERIFIED |
| D-26-04 (Rückweg nur per Admin-Token) | `SettingsService::profileConfirmed`, `guard.note_confirmation`, admin.php `wayBackCommand` | VERIFIED |
| D-26-05/D-26-14 (KIND_BATCH_INDEX_LANE=32 nur Lane index, Lane all bleibt 2) | `QueueService.php` KIND_BATCH vs. KIND_BATCH_INDEX_LANE, Auswahl über `$lane === self::LANE_INDEX` | VERIFIED |
| D-26-06/D-26-13 (Zeilenbeschnitt statt Fristformel, Lease 1800s unverändert) | `config.py` `ocr_rows_to_keep`, `OCR_ROWS_PER_SLOT = 2`, `OCR_JOB_SECONDS_MAX` nicht negativ | VERIFIED |
| D-26-07 (K6-Übergang, Slots = min(N, gelieferte Zeilen)) | `worker/poller.py` Zeilenbeschnitt vor Extraktion | VERIFIED |
| D-26-08 (Kill-Test deckt beide Fälle) | `test_slots_kill.py` zwei Testfälle | VERIFIED |
| D-26-09 (arm64-CI-Messleiter, Rauschgrenze 1,05, Sparsam-Pin) | `docs/measurements/2026-09-slot-leiter-ci/` | VERIFIED |
| D-26-10 (AWS-Matrix erst Phase 28) | nicht Teil dieser Phase, docs verweisen auf Phase 28 | VERIFIED (Abgrenzung eingehalten) |
| D-26-11/D-26-12 (nice 10 überall, Live-Latenzprobe) | `sandbox.py` `SANDBOX_NICE = 10`, `os.nice(SANDBOX_NICE)` vor Dispatcher-Import; `docs/measurements/2026-09-nice-latenz/` mit Owner-Abnahme | VERIFIED |
| D-26-16 (externer Kill = OOM-Kill, oom_score_adj 1000, Solo-Wiederholung) | `sandbox.py` `oom_score_adj_path.write_text("1000", ...)`, `guard.report_child_kill()` im Poller | VERIFIED |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/findling/extract/sandbox.py` | SANDBOX_NICE, oom_score_adj, ChildKilled-Pfad, halt()-Fix | VERIFIED | CR-01-Fix bestätigt (Flag vor `process.start()`, Recheck nach Zuweisung) |
| `backend/src/findling/extract/errors.py` | ChildKilled, EngineKilled | VERIFIED | vorhanden |
| `backend/src/findling/extract/pool.py` | SlotGate, SlotPool, eigener Executor | VERIFIED | vorhanden, `findling-slot`-Executor bestätigt |
| `backend/src/findling/index/writer.py` | RLock um add/flush | VERIFIED | vorhanden |
| `backend/src/findling/worker/poller.py` | N-Slot-Staffel, Zeilenbeschnitt, Marker-Reihenfolge | VERIFIED | WR-01/WR-02-Fixes bestätigt |
| `backend/src/findling/worker/watch.py` | class GuardWatch | VERIFIED | vorhanden |
| `backend/src/findling/guard.py` | Escalation, CAUSE_*, META_* | VERIFIED | vorhanden |
| `backend/src/findling/memory_guard.py` | memory_events() | VERIFIED | vorhanden (Basis aus Phase 25) |
| `backend/src/findling/api/status.py` | class GuardReport | VERIFIED | vorhanden |
| `backend/src/findling/worker/embedding.py` | embed_slots-Semaphore, Sperren | VERIFIED | Plan 26-07 umgesetzt |
| `php/lib/Service/QueueService.php` | KIND_BATCH_INDEX_LANE | VERIFIED | vorhanden |
| `php/lib/Service/SettingsService.php` | profile_confirmed | VERIFIED | vorhanden |
| `php/lib/Controller/ProfileController.php` | confirmed-Feld | VERIFIED | vorhanden |
| `php/lib/Service/AdminViewService.php` + `php/templates/admin.php` | Wächter-/Slot-Zeilen, 8 Kataloge | VERIFIED | Felder und Anzeige bestätigt |
| `backend/tests/slots_kill_harness.py` + `test_slots_kill.py` | Kill-Test beider Fälle | VERIFIED | echtes SIGKILL, in Linux-CI grün (36522819711) |
| `scripts/ops/slot_ladder.py` + `measure.yml` | Messleiter | VERIFIED | in CI grün (36523219615), Rohdaten committet |
| `docs/measurements/2026-09-slot-leiter-ci/` | Auswertung | VERIFIED | README + 7 Rohdateien vorhanden |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `sandbox.py _child_main` | `os.nice(SANDBOX_NICE)` | direkt nach setsid, vor Dispatcher-Import | WIRED | bestätigt in Zeile 321 |
| `pool.py SlotPool.call` | `ThreadPoolExecutor(thread_name_prefix="findling-slot")` | `run_in_executor` statt `asyncio.to_thread` | WIRED | bestätigt |
| `pool.py SlotPool.close` | `ExtractionWorker.halt` | Sofort-Beendigung ohne Warten | WIRED | bestätigt (CR-01-Kontext) |
| `QueueService.php claim()` | `KIND_BATCH_INDEX_LANE` | `$lane === self::LANE_INDEX` | WIRED | bestätigt |
| `worker/poller.py run_once` | `DocumentQueue.unlock` | Überschuss nach `ocr_rows_to_keep` | WIRED | bestätigt über `unlock_held` |
| `worker/poller.py` Mehr-Slot-Pfad | `guard.report_child_kill` | `except ChildKilled` bei slots >= 2 | WIRED | bestätigt |
| `worker/watch.py run_once` | `guard.Escalation.observe`/`guard.lower` | Tick mit memory_events, headroom, child_kills | WIRED | bestätigt |
| `main.py lifespan finally` | `GuardWatch.note_shutdown_begins` | erste Zeile im finally | WIRED | vorhanden (IN-04 als bekannte, dokumentierte Restlücke im Zeitfenster, kein Blocker) |
| `api/status.py _guard_report` | `guard.snapshot()` | reiner Leser | WIRED | bestätigt |
| `AdminViewService.php` | `guard`-Feldnamen des Containers | Vertragstest `test_admin_ui_contract.py` | WIRED | Vertragstest vorhanden |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Zielgerichtete lokale Testauswahl (config/guard/memory_guard/watch/pool/index_writer) | `uv run pytest -q -k "config or guard or memory_guard or watch or pool or index_writer"` | 417 passed, 2 skipped | PASS |
| CI-Lauf SC2 (Kill-Test) unabhängig abgerufen | `gh run view 36522819711 --repo street1983nk/nextcloud-search` | "main Python gates" grün, Job pytest grün auf ubuntu-24.04 | PASS |
| CI-Lauf SC3 (Messleiter) unabhängig abgerufen | `gh run view 36523219615 --repo street1983nk/nextcloud-search` | "main Wave 0 measurements" grün, "W4 slot curve on arm64" grün | PASS |
| CI-Lauf PHPUnit unabhängig abgerufen | `gh run view 36522819728 --repo street1983nk/nextcloud-search` | "main PHP and store metadata gates" grün, PHPUnit-Job grün | PASS |
| Volle lokale Testsuite (3900+ Tests) | `uv run pytest -q` | Abgebrochen nach 240s Timeout (zu lang für dieses Zeitbudget, kein Fehlerbefund) | SKIP (Zeitbudget, durch CI-Beleg und Teilsuite abgedeckt) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PAR-02 | 26-01,02,03,04,06,07,09,11,12,13,14 | N OCR-Slots (Semaphore, N Kinder, Sperre um IndexBatchWriter.add()), Zusagen unter Parallelität | SATISFIED | SlotPool/SlotGate, RLock, Kill-Test, Messleiter alle vorhanden und grün |
| PAR-03 | 26-01,02,03,05,08,09,10,11,12,14 | Speicherwächter drosselt/senkt Profil, sichtbar gemeldet | SATISFIED | guard.py/watch.py/status.py/AdminViewService.php vollständig verdrahtet |

Anmerkung: `.planning/REQUIREMENTS.md` Traceability-Tabelle zeigt PAR-02/PAR-03 noch als "Pending" , das ist der übliche Nacharbeitsschritt von `phase.complete`, der nach dieser Verifikation läuft, kein Befund gegen den Code.

### Anti-Patterns Found

Keine TBD/FIXME/XXX in den 14 Kern-Backend- und PHP-Dateien der Phase. Keine Platzhalter-Returns, keine leeren Handler gefunden. Vier Info-Befunde aus dem Code-Review (IN-01..04) bleiben laut 26-REVIEW.md bewusst offen dokumentiert (kein Datenverlust, nur schmale Zeitfenster bzw. heute unerreichbare Zweige); das ist eine explizite Owner-/Review-Entscheidung, kein unentdeckter Gap.

### Human Verification Required

Keine. Die Owner-Abnahmen für die Latenzprobe (D-26-12, 26-13-SUMMARY) und die Phasen-Abnahme (26-14-SUMMARY, Signal "approved") liegen bereits vor und sind dokumentiert; der optionale Live-Blick auf `/status` im nc35-Harness wurde vom Owner ausdrücklich als nicht nötig markiert (SC4 bleibt testbelegt).

### Gaps Summary

Keine Gaps gefunden. Alle vier ROADMAP-Erfolgskriterien sind im Code nachweisbar umgesetzt und durch unabhängig abgerufene, grüne CI-Läufe bestätigt (nicht nur durch SUMMARY-Behauptungen). Die drei kritischen/wichtigen Code-Review-Befunde (CR-01, WR-01, WR-02) sind im HEAD-Commit gefixt und mit Regressionstests belegt (91fefe8f, 777f3a59, 15eb03d5). Die vier Info-Befunde (IN-01..04) sind schmale, dokumentierte Randfälle ohne Datenverlust und wurden vom Reviewer/Owner bewusst offen gelassen.

---

_Verified: 2026-09-29_
_Verifier: Claude (gsd-verifier)_
