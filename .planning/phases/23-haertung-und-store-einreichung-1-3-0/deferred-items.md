# Phase 23: aufgeschobene Punkte

## Aus Plan 23-01 (27.09.2026)

- **tests/test_one_load.py, 7 Fälle rot** (`test_one_process_pays_for_one_engine_and_one_word_list`, `test_the_fourth_phase_releases_the_weights_and_fetches_them_back`, `test_the_cold_start_duration_is_a_line_of_its_own`, `test_the_entry_point_prints_its_numbers_and_exits_zero`, `test_it_goes_red_when_the_search_side_builds_its_own_engine`, `test_a_second_run_in_the_same_process_measures_a_load_and_not_a_cache_hit`, `test_it_goes_red_when_the_warm_up_loads_twice`).
  Ursache: `tools/one_load.py::drive_the_search_side` erwartet, dass `one_round` selbst lädt (`engine-loads-after-search=0` statt 1). Das ist die gewollte Folge von D-01.
  Zuständig: Plan 23-04, Task 1 (files_modified enthält `tools/one_load.py` und `tests/test_one_load.py`, Treiber bekommt den Handlerweg `warm_wanted()`/`warm()`). Nicht in 23-01 gefixt, damit die beiden Pläne nicht dieselben Dateien bearbeiten.

## Aus 23-04

- **Oberflaechentext der Admin-Seite (admin.php + 7 Sprachdateien) zum Zustand `cold`/`unloaded`:** Die Doku (`docs/admin-page.md`) ist praezisiert, der ausgelieferte Oberflaechentext selbst noch nicht. Owner-Frage am 23-08-Checkpoint: mitaendern (dann in 23-07/23-08 einarbeiten, 8 Dateien) oder so lassen (Doku erklaert den Unterschied)?
- **`docs/performance.md:3480` nennt noch `cold-search-ms=`:** datierter Messbericht, bewusst nicht angefasst.
