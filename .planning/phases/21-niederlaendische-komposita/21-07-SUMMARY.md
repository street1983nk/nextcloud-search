---
phase: 21-niederlaendische-komposita
plan: 07
subsystem: index/open, index/rebuild, worker/poller, api/resources, tools
tags: [komposita, nl, splitter, open-index, band-rebuild, komp-01]
requires: ["21-03", "21-05", "21-06"]
provides:
  - open_index(path, constituents, *, dutch=None) mit freier Registrierung register_tokenizer(TOKENIZER_NL, dutch_chain_for(dutch))
  - alle neun open_index-Aufrufer in src nennen dutch ausdrücklich
  - AST-Gate test_every_caller_in_src_names_the_dutch_choice plus Gegenprobe
  - Band-Umbau schreibt body_nl eines Bestandsindex mit der Splitterkette neu
affects: [21-08, 21-09]
tech-stack:
  added: []
  patterns: [Variante hinter freier Registrierung statt bedingter Registrierung, AST-Aufruf-Gate mit Selbsttest]
key-files:
  created: []
  modified:
    - backend/src/findling/index/open.py
    - backend/src/findling/index/rebuild.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/tools/one_load.py
    - backend/src/findling/tools/index_status.py
    - backend/src/findling/index/bench.py
    - backend/tests/test_index_open.py
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_read_side.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "dutch mit Default None statt Pflichtparameter (Discretion): rund hundert Testaufrufe öffnen deutsche Indizes; die Research-Absicht hält das AST-Gate für src, Begründung im Docstring von open_index"
  - "Selbsttest des Gates in Task 1, das src-Gate selbst erst im Task-2-Commit, damit kein Commit auf main rot ist"
  - "_write_index in one_load bekommt ein keyword-only dutch ohne Default, damit auch dieser interne Weg die Wahl nennen muss"
  - "rebuild_the_index reicht dutch_digest_for(resolved.languages) inline an _make_the_target_fit_this_code, weil der Name dutch dort schon die Marke trägt"
metrics:
  duration: ca. 35 min
  completed: 2026-09-25
  tasks: 2 von 2
---

# Phase 21 Plan 07: Splitterkette hinter der Sprachwahl Summary

Bei aktivem nl steht unter `TOKENIZER_NL` jetzt die Splitterkette, ohne nl die Snowball-Kette ohne Liste und ohne Automat; `belasting` findet `gemeentebelastingen` über body_nl im Index, im Band-Umbau und auf der Leseseite eines frischen Containers, die Registrierung bleibt frei (8 Ketten, keine unter einem if).

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Registrierung hinter der Sprachwahl, Verhaltensbeweis | 0c1dd08 | open.py, test_index_open.py, test_measurement_scripts.py |
| 2 | Alle Aufrufer, Re-Analyse-Beweis, Baumhash, volle Suite | 20eded8 | rebuild.py, poller.py, resources.py, one_load.py, index_status.py, bench.py, test_index_open.py, test_index_rebuild.py, test_read_side.py, test_measurement_scripts.py |

## Umsetzung

- `open.py`: `open_index(path, constituents, *, dutch: str | None = None)`, Registrierung `index.register_tokenizer(TOKENIZER_NL, dutch_chain_for(dutch))` frei, Kommentar zu 17,6 MB und D-07, Docstring um den Parameter und den Default-Entscheid.
- `poller.py` `_open_writer`, `resources.py` Leseseite, `one_load.py` `_write_index`: `dutch=dutch_digest_for(languages)`.
- `rebuild.py`: `transfer_documents` baut `dutch = dutch_digest_for(active)` einmal für Quelle und Ziel; `_make_the_target_fit_this_code(..., *, dutch)` reicht es an beide `open_index`-Aufrufe.
- `bench.py`, `index_status.py`: `dutch=None` mit je einer Begründung (Bench misst die deutsche Kette, index_status zählt nur).
- Baumhash zweimal nachgezogen (je Task im selben Commit), zuletzt `f2a0b1f8...0409f`, `PACKAGE_FILES_TODAY` bleibt 57, Kommentare "Plan 21-07, task 1/2". `ANALYZER_VERSION` bleibt 1, `EXPECTED_REGISTRATIONS = 8` unverändert.

## Neue Tests

- `test_with_dutch_the_constituent_finds_the_compound`, `test_without_the_dutch_splitter_the_constituent_finds_nothing` (beide Hälften in einem Test), `test_without_dutch_no_dutch_automaton_is_built` (Liste liegt auf dem Volume, Lese- und Baucounter unverändert), `test_two_openings_with_dutch_build_one_automaton`.
- `test_the_dutch_choice_gate_sees_a_caller_without_it` und `test_every_caller_in_src_names_the_dutch_choice` (9 Aufrufe, 0 ohne `dutch`).
- `test_the_rebuild_splits_the_dutch_compounds_of_an_existing_index`: Bestand unter Snowball, Drift "off" auf nl, danach Treffer über body_nl, `index_version` unverändert, `wordlist_hash_nl` gestempelt.
- `test_a_fresh_container_finds_a_dutch_compound_through_its_constituent`: Writer über `_open_writer`, Suche über `read_side()` und `build_query` mit dem Feldplan, Ergebnis `[41]`.
- RED belegt: Task 1 fünf Tests rot vor dem open.py-Eingriff; Umbau-Test `0 == 1` und Leseseiten-Test `[] == [41]` vor den src-Aufrufern.

## Verifikation

- test_index_rebuild, test_read_side, test_sandbox, test_poller, test_main_lifespan, test_index_open, test_measurement_scripts: 699 passed, 5 skipped
- Volle Suite: 2973 passed, 15 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün
- grep: Registrierungszeile 1, `EXPECTED_REGISTRATIONS = 8` 1, open_index-Zeilen ohne `dutch` 0, `ANALYZER_VERSION = 1` 1

## Deviations from Plan

**1. Gate-Test zwischen den Commits aufgeteilt.** `test_every_caller_in_src_names_the_dutch_choice` gehört laut Plan zu Task 1, kann aber erst grün sein, wenn die Aufrufer aus Task 2 umgestellt sind. Damit kein roter Commit auf main landet, trägt Task 1 den Selbsttest des Gates, das src-Gate selbst kam mit Task 2. Kein Test gelockert.

**2. Keine Bestandstests brauchten `write_wordlist_nl`.** Die volle Suite lief ohne weitere Anpassung grün; die sechs-Sprachen-Tests trugen die Liste schon seit 21-06.

## Threat Flags

Keine neue Oberfläche. T-21-07-01 (fail closed in `dutch_chain_for`, Digest aus `dutch_digest_for` wie die Marke, Leseseite fängt den Fehler im bestehenden except), T-21-07-02 (freie Registrierung, Gate 8), T-21-07-03 (Test auf `dutch_build_count` und `read_count_nl`) mitigiert.

## Self-Check: PASSED

- FOUND: alle elf geänderten Dateien
- FOUND: Commits 0c1dd08, 20eded8
