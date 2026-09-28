---
phase: 25-einbettungsspur-und-modellwahl
plan: 02
subsystem: embed
tags: [engine, idle-guard, precision, fp32, embedding-mark, IN-02]
requires: []
provides:
  - "EmbeddingModel.release(*, idle_seconds: float | None = None)"
  - "EmbeddingModel(weights_path=..., precision=...) mit Properties weights_path und precision"
  - "embed.engine.swap_engine(weights_path, precision) -> EmbeddingModel | None"
  - "embed.engine.engine_precision() -> str"
  - "embedding_mark(model, *, tokens, weights) ohne Default"
affects:
  - backend/src/findling/worker/poller.py (Markenschritt)
  - backend/src/findling/api/resources.py (expected_marks)
tech-stack:
  added: []
  patterns:
    - "Halter gekeyt auf (tokenizer_dir, weights_path), aktive Gewichtswahl als Modul-Global _WEIGHTS"
    - "Idle-Prüfung unter der Modellsperre statt nur im Aufrufer"
key-files:
  created: []
  modified:
    - backend/src/findling/embed/model.py
    - backend/src/findling/embed/engine.py
    - backend/src/findling/store/vectors.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/api/resources.py
    - backend/tests/test_embed_engine.py
    - backend/tests/test_embed_model.py
    - backend/tests/test_vector_store.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_v13_ablauf.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "swap_engine auf denselben Schlüssel ist ein No-op und gibt None zurück (kein Tausch eines warmen Modells gegen eine kalte Kopie)"
  - "swap_engine(None, fp32) und unbekannte Präzisionen werfen ValueError ohne Wertnennung"
  - "expected_marks setzt die Einbettungsmarke bei jedem Aufruf frisch, der Cache hält nur noch die Index-Marken"
  - "_held matcht nur auf das Tokenizer-Verzeichnis; _ABSENT ist wie der Halter auf (tokenizer_dir, weights_path) gekeyt"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-28
  tasks: 3
  files: 12
requirements: [MOD-02, PAR-01]
---

# Phase 25 Plan 02: Engine-Seite (Idle-Guard, Gewichtspfad, Halter-Tausch, IN-02) Summary

Idle-Guard unter der Modellsperre in `EmbeddingModel.release(idle_seconds=...)`, Gewichtspfad und Präzision getrennt vom Tokenizer-Verzeichnis, ein ladefreier `swap_engine` mit `engine_precision`, und `embedding_mark` ohne `weights`-Default; beide Produktionsaufrufer übergeben `weights=engine_precision()`, die int8-Marke bleibt bytegleich zu 1.3.x.

## Umsetzung je Task

**Task 1: Idle-Guard (T-25-04, WR-02 aus Phase 23 geschlossen)**
- `release(self, *, idle_seconds: float | None = None) -> bool`: nach `_engine`- und `_in_flight`-Prüfung zusätzlich `time.monotonic() - _last_use < idle_seconds` unter `self._lock`.
- `release_if_idle` ruft `held.release(idle_seconds=ttl_seconds)`; WR-02-Kommentar umgeschrieben ("v1.4 backlog note" entfernt).
- T10: `test_a_use_between_the_second_reading_and_release_keeps_the_engine` schiebt eine Einbettung nach der zweiten `last_use`-Lesung ein; `release_if_idle` liefert False, `released_count()` unverändert.

**Task 2: Gewichtspfad, Präzision, Tausch (T-25-06)**
- `EmbeddingModel.__init__(..., weights_path=None, precision=WEIGHTS_INT8)`; Default `model_dir / MODEL_FILE`. `_artifacts_present(model_dir, weights_path)` prüft Tokenizer und Gewichte getrennt; `_load` öffnet `_weights_path`. Kein Importzyklus (`store.vectors` importiert nur `store.repo`).
- IDX-08-Kommentar in `_open_session` um PAR-04-Satz ergänzt.
- `engine.py`: `_ENGINE: tuple[tuple[Path, Path], EmbeddingModel]`, `_WEIGHTS: tuple[Path, str] | None`, Helfer `_chosen`/`_build`, `swap_engine`, `engine_precision`; `reset()` setzt `_WEIGHTS` zurück. Im Ruhezustand wird kein fp32-Pfad geprüft.

**Task 3: IN-02 (T-25-05) und Pins**
- `embedding_mark(model, *, tokens, weights)` ohne Default, Docstring nennt IN-02.
- `worker/poller.py` und `api/resources.py` übergeben `weights=engine_precision()`.
- Alle Testaufrufer übergeben `weights=WEIGHTS_INT8`; Signaturtest ergänzt; Gold-Test `test_upgrade_compatibility.py` grün.
- `PACKAGE_TREE_HASH_TODAY` neu gemessen: `64f4e1e6...841b9`, Kommentar im Hausstil; `PACKAGE_FILES_TODAY` bleibt 59; PHP-Pins unverändert.

## Verifikation

- `uv run pytest -q`: 3514 passed, 15 skipped
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 Fehler), vulture `src tests --min-confidence 80`: alle grün
- `git diff --stat -- php`: leer
- Akzeptanz-Greps: `weights=engine_precision()` je 1 in poller.py und resources.py; `weights: str = WEIGHTS_INT8` 0 in vectors.py; `v1.4 backlog note` 0 in engine.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Veraltete Präzision im Markencache der Leseseite**
- **Gefunden in:** Task 3
- **Problem:** `expected_marks()` cachte die Einbettungsmarke mit den Index-Marken pro Wörterbuchverzeichnis. Nach einem `swap_engine` hätte die Leseseite weiter die alte Präzision erwartet.
- **Fix:** Cache in `_index_marks()` ausgelagert (nur Index-Marken); `expected_marks()` setzt `EMBEDDING_MARK` bei jedem Aufruf mit `engine_precision()`. Test `test_the_read_side_expects_the_mark_of_the_held_model` belegt beide Richtungen.
- **Dateien:** backend/src/findling/api/resources.py, backend/tests/test_embedding_track.py
- **Commit:** 62a882c

**2. [Rule 3 - Blocking] Bestehender fp32-Wechseltest nutzte `functools.partial` auf `embedding_mark`**
- **Problem:** Da der Poller `weights` jetzt selbst übergibt, überschrieb der Aufruf das `partial`; der Test lief rot.
- **Fix:** `test_a_switch_from_int8_to_fp32_weights_re_embeds_the_stock` patcht nun `poller_module.engine_precision` (die neue Naht); `functools`-Import entfernt.
- **Commit:** c848e3b

**3. [Rule 3 - Blocking] Test-Fakes an neue Signaturen angepasst**
- `counting`/`counted`-Fakes von `artifacts_present`/`_artifacts_present` nehmen `weights_path`; Spy von `release` nimmt `idle_seconds`; `_held_for` und der direkte `_ENGINE`-Eintrag im Swap-Test nutzen den Tupel-Schlüssel.

### Hinweis zur TDD-Reihenfolge Task 3
Tests und Umsetzung entstanden in Task 3 im selben Arbeitsgang; committet wurde trotzdem in Reihenfolge `test(...)` (c848e3b) vor `feat(...)` (62a882c).

## TDD Gate Compliance

- Task 1: test 08a7388 -> feat a385b22
- Task 2: test 4e03582 -> feat 398ecc1
- Task 3: test c848e3b -> feat 62a882c

## Commits

| Task | Typ | Hash | Nachricht |
|------|-----|------|-----------|
| 1 | test | 08a7388 | add failing tests for the idle guard inside release |
| 1 | feat | a385b22 | idle guard inside EmbeddingModel.release |
| 2 | test | 4e03582 | add failing tests for weights path, precision and swap_engine |
| 2 | feat | 398ecc1 | weights path, precision and a swap of the holder that loads nothing |
| 3 | test | c848e3b | mark without a default and following the held precision |
| 3 | feat | 62a882c | embedding mark without a default, callers pass the held precision |

## Hinweise für Folgepläne

- Das von `swap_engine` zurückgegebene alte Modell liegt nicht mehr im Halter; `release_if_idle` erreicht es nicht. Der Aufrufer (Plan 25-11) muss es selbst freigeben, sobald keine Suche es hält.
- Tests, die `swap_engine` rufen, müssen `reset()` davor und danach aufrufen (Modul-Global `_WEIGHTS`); Fixtures `fp32_weights` und `swapped_to_fp32` tun das.
- Die PHP-Pins in `test_measurement_scripts.py` misst Plan 25-05 nach dem Merge der Welle 1 neu.

## Self-Check: PASSED
