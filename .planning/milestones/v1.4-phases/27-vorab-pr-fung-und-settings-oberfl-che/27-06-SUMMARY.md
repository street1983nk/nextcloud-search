---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 06
subsystem: backend
tags: [probe, pruef-01, fp32, spawn-child, hardening]
requires: ["27-02"]
provides:
  - "findling.embed.model_probe: MEASURE_OK/TIMEOUT/KILLED/FAILED/NO_MEMORY, MEASURE_OUTCOMES"
  - "ModelMeasure(outcome, rss_before, rss_after, rate_milli) frozen, delta"
  - "measure(precision, models_dir, *, timeout_seconds) -> ModelMeasure (blockierend)"
affects: [27-09]
tech-stack:
  added: []
  patterns: ["Spawn-Kind mit Sandbox-Härtung ohne RLIMIT_AS; Probenhaken nur über private _measure-Naht"]
key-files:
  created:
    - backend/src/findling/embed/model_probe.py
    - backend/tests/test_model_probe.py
  modified:
    - backend/tests/test_sandbox.py
decisions:
  - "rss_before/rss_after in Byte (RssAnon KiB x 1024), passend zu MODEL_PROBE_CHILD_BYTES"
  - "Rate aus dem ersten Batch: 8 x 1000 x 1000 / Batchdauer ms, mindestens 1"
  - "Das Kind nutzt _open_encoder/_open_session/_encode_batch/_run_encoded aus embed/model.py (Produktpfad statt Kopie); load_count des Elternteils bleibt unberührt"
  - "int8 = embed_model_dir/model.onnx aus dem Abbild, fp32 = fp32_weights_path(models_dir); Tokenizer immer aus embed_model_dir (config.settings())"
  - "Kind darf nur ok/failed/no_memory melden; timeout und killed sind Worte des Elternteils, jede andere Antwort wird failed"
  - "killed = EOF ohne Antwort und exitcode KILLED_EXIT_CODE; EOF mit anderem Exitcode = failed"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-29
  tasks: 1
  files: 3
---

# Phase 27 Plan 06: Modellprobe als gehärtetes Spawn-Kind Summary

Die fp32- bzw. int8-Modellprobe läuft in einem eigenen Spawn-Kind (setsid, nice 10, oom_score_adj 1000, Secrets geschält, kein RLIMIT_AS), misst RssAnon vor dem Laden und nach einem Batch aus 8 x 512 Token sowie die Rate in Milli-Passagen je Sekunde; der Elternteil erzwingt die Deadline mit Gruppenkill und trennt ok, timeout, killed, failed und no_memory.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Modell-Kind mit Härtung, Messung und Pipe-Protokoll | 714b58d7 (RED), e2b023fd (GREEN) |

## Verifikation

- `tests/test_model_probe.py`, `test_sandbox.py`, `test_one_load.py`: 83 passed, 8 skipped (Windows)
- Volle Suite: 3978 passed, 24 skipped; einzig rot ist der Baumhash-Pin (siehe unten)
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber
- Akzeptanz-greps: `from findling.extract.sandbox import` 1-mal, kein Modulebene-Import von onnxruntime/fastembed, kein `_limit_address_space`
- **Linux-Beleg im Abbild** (`localhost:5055/findling_backend:latB`, `--network none`, Worktree read-only gemountet): echter int8-Lauf `ok`, rss_before 320.401.408 B, rss_after 467.492.864 B (Delta 143.645 KiB, Messdoku 147.736 bis 148.400 KiB), rate_milli 4004, load_count im Elternteil 0; fehlende fp32-Datei `failed`; Rehearsal über Deadline `timeout`, Prozessgruppe danach weg; SIGKILL von außen `killed`

## Unter Windows geskippt

- `test_a_kill_from_outside_reads_as_killed` (POSIX-Signal)
- `test_a_real_int8_run_measures_memory_and_rate` (POSIX und FINDLING_EMBED_MODEL_DIR mit Modell); beide Fälle sind oben im Linux-Abbild nachgefahren

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] nice-Gate in test_sandbox.py kennt das zweite Kindmodul**
- **Found during:** Task 1
- **Issue:** `test_the_main_process_never_lowers_itself` verbietet `os.nice(` in jedem Modul außer sandbox.py; das Modellkind muss sich laut Plan selbst mit `os.nice(SANDBOX_NICE)` absenken.
- **Fix:** Gate auf eine explizite Kindermenge {sandbox.py, embed/model_probe.py} umgestellt, mit Begründung; der Hauptprozess bleibt weiterhin geschützt.
- **Files modified:** backend/tests/test_sandbox.py
- **Commit:** e2b023fd

## Offene Punkte für den Orchestrator

- `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` ist rot, weil `embed/model_probe.py` eine neue Paketdatei ist. Pin laut Auftrag nicht angefasst; nach dem Wellen-Merge nachmessen.

## Hinweise für 27-09

- `measure` blockiert bis zu `timeout_seconds` plus Beitrittsfrist (5 s); in einem eigenen Thread rufen, nie im Default-Executor.
- `measure` prüft keinen Digest; vorher `fp32_verified` bzw. `procure_fp32` (T-27-15).
- Vorab-Tor `model_child_admitted` mit `MODEL_PROBE_CHILD_BYTES` bleibt Sache des Orchestrators (T-27-16).

## Threat Flags

Keine neue Angriffsfläche über das Threat-Register hinaus (T-27-14 und die Deadline-Hälfte von T-27-16 sind umgesetzt).

## TDD Gate Compliance

RED `test(27-06)` 714b58d7 vor GREEN `feat(27-06)` e2b023fd vorhanden.

## Self-Check: PASSED

- FOUND: backend/src/findling/embed/model_probe.py, backend/tests/test_model_probe.py
- FOUND: 714b58d7, e2b023fd
