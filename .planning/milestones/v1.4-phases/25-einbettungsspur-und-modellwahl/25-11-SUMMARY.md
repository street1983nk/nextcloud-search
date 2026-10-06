---
phase: 25-einbettungsspur-und-modellwahl
plan: 11
subsystem: backend/worker-precision
tags: [precision, fp32, engine-swap, drift-chain, procurement, sideload, mod-02]
requires:
  - 25-02 (swap_engine, engine_precision, EmbeddingModel.release)
  - 25-06 (weights.py: fp32_verified, procure_fp32, clear_leftovers, remove_fp32_weights; fetch_release_asset)
  - 25-08 (precision.py: note_chosen_precision, settle, decide, begin/end_procurement, note_active)
  - 25-09 (EmbeddingTrack mit Sperre, EmbedRunner)
provides:
  - "EmbeddingTrack: Präzisionsschritt im Markenschritt (Startzustand, Entscheid, Beschaffungs-Task, Engine-Tausch, Rückweg mit Löschen)"
  - "EmbeddingTrack.aclose(): bricht eine laufende Beschaffung ab und wartet auf sie"
  - "Poller.run_once: note_chosen_precision(choice.precision) je Runde"
  - "ENGINE_RELEASE_ATTEMPTS / ENGINE_RELEASE_PAUSE_SECONDS"
affects:
  - 25-12 (Status meldet Verdikt und aktive Präzision, die jetzt im Betrieb gesetzt werden)
tech-stack:
  added: []
  patterns:
    - "Präzisionswechsel als Drift: weicht das Ziel vom Halter ab, läuft die Kette unabhängig von der gespeicherten Marke"
    - "Beschaffung als eigener asyncio-Task außerhalb der Track-Sperre, höchstens einer"
key-files:
  created:
    - backend/tests/test_precision_wiring.py
  modified:
    - backend/src/findling/worker/embedding.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_semantic_search.py
decisions:
  - "Startzustand wird auch vor der ersten Zeile gesetzt (embed_row), nicht nur im Markenschritt, sonst entsteht ein int8-Vektor unter fp32-Marke"
  - "Ein abweichendes Ziel ist immer Drift, auch bei unbekannter Marke: ein int8-Bestand darf nie unter fp32-Marke beansprucht werden"
  - "Engine-Tausch in einem gemeinsamen Helfer _swap_the_engine für Startzustand und Kette; die Passage-Engine des Tracks folgt dem Halter"
  - "Beschaffung wird in EmbeddingTrack.aclose() abgebrochen (Poller.aclose); close() im Verzeichnistausch lässt sie laufen, weil sie nur models_dir beschreibt"
  - "Freigabe des alten Modells: 100 Versuche im Abstand von 50 ms, danach fällt es mit der letzten Suche"
metrics:
  duration: ca. 70 min
  completed: 2026-09-28
  tasks: 2
  files: 4
---

# Phase 25 Plan 11: Präzisionswahl im Betrieb Summary

Der Track entscheidet je Markenschritt über die Präzision: Startzustand aus Marke plus verifizierter Datei, Beschaffung als eigener Task nur nach beobachtetem Wechsel, Engine-Tausch als vierter Schritt der Driftkette unter der Track-Sperre, und auf dem Rückweg nach int8 wird die fp32-Datei gelöscht. Der Poller liest die Präzision je Runde.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Startzustand, Entscheid und Beschaffung im Track; Präzision je Runde im Poller | 61d6d95 (RED), 3cd03d1 (GREEN) |
| 2 | Engine-Tausch an der Spurgrenze, Rückweg mit Löschen, Suche während der Neueinbettung | afffd58 (RED), 42c5b33 (GREEN) |

## Was gebaut wurde

- **poller.py:** `note_chosen_precision(choice.precision)` direkt nach `note_chosen(choice.profile)`; `Poller.aclose` wartet auf `EmbeddingTrack.aclose()`.
- **embedding.py, Startzustand (`_prepare_the_precision`):** einmal je `open()` `clear_leftovers` (nicht während einer laufenden Beschaffung); einmal je Track `settle`: fp32 nur, wenn die Marke auf `/fp32` endet und `fp32_verified` wahr ist, dann `swap_engine` auf den fp32-Pfad. Läuft im Markenschritt und vor der ersten Zeile.
- **Entscheid (`_decide_the_precision`):** `fp32_verified` nur, wenn gewählt oder aktiv fp32 ist; `decide(fp32_ready=...)`; bei `procure` `begin_procurement()` und ein Task `_procure`, der `procure_fp32(models_dir, fetch_release_asset, min_free_bytes=...)` ausführt und in jedem Ausgang `end_procurement(succeeded=outcome == PROCURED)` meldet. Log nur mit Ergebnisnamen.
- **Kette (`_step_of_the_vector_mark(target)`):** weicht `decision.target` von `engine_precision()` ab, läuft forget_all, Cursor `BACKLOG_START`, Marke der neuen Präzision, `swap_engine`, Freigabe des alten Modells (`_let_go_of`, begrenzte Wiederholung), danach im Loop `note_active`. Von fp32 nach int8 wird `remove_fp32_weights` nach der Freigabe aufgerufen. Ein zweiter Wechsel während des Reindex läuft durch dieselbe Kette und beginnt bei Cursor 0.
- **Tests:** `test_precision_wiring.py` (15 Fälle, echte state.db und vectors.db in tmp_path, gepatchte `FP32_SHA256`/`FP32_BYTES`, Fake-fetch mit Tor, aufgezeichnete Reihenfolge); Suchfall in `test_semantic_search.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, T-24-02] Startzustand auch vor der ersten Zeile**
- **Gefunden in:** Task 1
- **Problem:** Der Plan setzt den Startzustand nur im Markenschritt. Der läuft erst in einer leeren Runde; eine erste Runde mit Zeilen hätte mit dem int8 des Abbilds unter einer fp32-Marke eingebettet, ein Mischbestand ohne Drift.
- **Fix:** `_embed` ruft `_prepare_the_precision()` vor dem Cutter; danach zwei Attributlesungen je Zeile. Test `test_the_start_state_is_settled_before_the_first_row_is_embedded`.
- **Commit:** 3cd03d1

**2. [Rule 1 - Bug, T-24-02] Abweichendes Ziel ist Drift, auch bei unbekannter Marke**
- **Gefunden in:** Task 2
- **Problem:** Mit unbekannter Marke hätte `_claim_a_whole_stock` einen int8-Bestand unter der fp32-Marke beansprucht.
- **Fix:** Der Präzisionswechsel wird vor den drei Markenfällen geprüft.
- **Commit:** 42c5b33

**3. [Rule 1 - Bug] Passage-Engine des Tracks folgt dem Halter**
- **Problem:** `self._model` des Tracks zeigte nach dem Tausch weiter auf das alte, freigegebene Modell; die nächste Zeile hätte es neu geladen und mit der alten Präzision eingebettet.
- **Fix:** In `_swap_the_engine` wird `self._model` auf `shared_model()` gesetzt, wenn es das alte Modell war.
- **Commit:** 3cd03d1

**4. [Rule 2 - Korrektheit] Abbruch der Beschaffung in `aclose()` statt `close()`**
- `close()` ist synchron und läuft beim Verzeichnistausch in einem Worker-Thread; ein Task lässt sich dort nicht abbrechen. Neue `EmbeddingTrack.aclose()` bricht ab und wartet, `Poller.aclose` ruft sie. Der Verzeichnistausch lässt die Beschaffung weiterlaufen (sie schreibt nur in `models_dir`). `clear_leftovers` wird nie während einer laufenden Beschaffung gerufen, sonst löschte es die `.part`-Datei im Schreiben.

**5. [Rule 2] Löschfehler beim Rückweg**
- `remove_fp32_weights` in try/except OSError, damit ein Löschfehler nicht `note_active` verhindert und Marke, Halter und Zustand auseinanderlaufen.

### Abweichung von der Grep-Abnahme

- `grep -c "swap_engine(" embedding.py` ergibt 1 statt mindestens 2: Startzustand und Kette nutzen denselben Helfer `_swap_the_engine`, damit die Freigabe und das Nachziehen der Passage-Engine an einer Stelle stehen. Beide Pfade tauschen nachweislich (Tests `test_a_stored_fp32_mark_and_a_verified_file_start_on_fp32_without_emptying`, `test_a_sideloaded_file_is_taken_up_in_the_recorded_order_without_a_request`).
- Übrige Greps: `note_chosen_precision(choice.precision)` 1, `procure_fp32(` 1, `fetch_release_asset` >= 1, `settle(` 2, `remove_fp32_weights(` 1.

## TDD Gate Compliance

- RED/GREEN je Task vorhanden (test 61d6d95 -> feat 3cd03d1, test afffd58 -> feat 42c5b33).
- Der Suchfall in `test_semantic_search.py` war im RED-Lauf bereits grün: er hält bestehendes Verhalten der Leseseite fest (leerer Bestand, lexikalisch vollständig), das dieser Plan nicht ändert, sondern voraussetzt.

## Verifikation

- `pytest --deselect tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package`: 3669 passed, 16 skipped, 1 deselected.
- Der deselektierte Paket-Pin-Test schlägt im Worktree erwartungsgemäß fehl (Bytes von worker/embedding.py und worker/poller.py geändert); Pin-Eigentümer dieser Welle ist Plan 25-10, die Neumessung erfolgt nach dem Wellen-Merge.
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest), vulture --min-confidence 80: grün.
- `git diff --stat 9e65150 -- php backend/src/findling/main.py backend/tests/test_measurement_scripts.py .planning/STATE.md .planning/ROADMAP.md`: leer.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche außerhalb des Threat-Modells: der Netzaufruf geht über `fetch_release_asset` (Host-Allowlist aus 25-06), gelöscht wird nur `fp32_weights_path(models_dir)`.

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_precision_wiring.py, backend/src/findling/worker/embedding.py, backend/src/findling/worker/poller.py, backend/tests/test_semantic_search.py
- Commits vorhanden: 61d6d95, 3cd03d1, afffd58, 42c5b33
