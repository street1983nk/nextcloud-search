---
phase: 21-niederlaendische-komposita
plan: 06
subsystem: index/rebuild, worker/poller, api/resources, tools
tags: [komposita, nl, version-mark, band-rebuild, d-06, komp-01]
requires: ["21-01", "21-03", "21-05"]
provides:
  - MARKS_A_REBUILD_ANSWERS mit DUTCH_MARK (an, neue Liste, aus beantwortet der Band-Umbau)
  - stamp_after_swap(store, languages, *, dutch_mark) ohne Default, vier Schreibvorgänge hinter dem Tausch
  - alle src-Aufrufer von expected_versions übergeben dutch_mark=dutch_mark(languages)
  - index_status-Schlüssel wordlistHashNl
  - AST-Gate test_every_caller_in_src_names_the_dutch_mark plus Gegenprobe
affects: [21-07]
tech-stack:
  added: []
  patterns: [keyword-only ohne Default gegen lügende Stempel, AST-Aufruf-Gate mit Selbsttest]
key-files:
  created: []
  modified:
    - backend/src/findling/index/rebuild.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/tools/one_load.py
    - backend/src/findling/tools/index_status.py
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_poller.py
    - backend/tests/test_read_side.py
    - backend/tests/test_index_status.py
    - backend/tests/test_index_open.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Adminseite (api/status.py) bekommt keinen eigenen nl-Schlüssel; das Banner über version_drift genügt, test_admin_ui_contract.py bleibt unberührt (Research Open Question 5)"
  - "Aufrufer einzeilig über eine lokale Variable languages, damit auch der grep-Check ohne Mehrzeilen-Ausnahme greift"
  - "Fallback-Zweig (fullreindex) unverändert, die nl-Marke erbt das D-08-Ergebnis aus 21-01"
metrics:
  duration: ca. 40 min
  completed: 2026-09-25
  tasks: 2 von 2
---

# Phase 21 Plan 06: Band-Umbau beantwortet die nl-Marke Summary

Jede nl-Drift (einschalten, neue Liste, ausschalten) wird jetzt vom Band-Umbau beantwortet und hebt beim Öffnen im Poller keine Generation; `stamp_after_swap` schreibt die Marke hinter dem Tausch, jeder src-Aufrufer von `expected_versions` baut den nl-Wert ausdrücklich, ein AST-Gate hält das fest, `ANALYZER_VERSION` bleibt 1.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Umbau beantwortet die Marke, Poller-Falle | ca7a2c8 | rebuild.py, test_index_rebuild.py, test_poller.py, test_read_side.py, test_measurement_scripts.py |
| 2 | Alle Aufrufer, siebter Berichtsschlüssel, Gate, Baumhash | 6f79777 | poller.py, resources.py, one_load.py, index_status.py, test_index_status.py, test_index_open.py, test_poller.py, test_read_side.py, test_measurement_scripts.py |

## Umsetzung

- `rebuild.py`: `DUTCH_MARK` in `MARKS_A_REBUILD_ANSWERS`, Kommentar begründet es (`_document_from` schreibt body_nl aus dem gespeicherten body_de-Text durch die Zielkette neu). `stamp_after_swap(..., *, dutch_mark: str)` ohne Default, Docstring "Four writes". `rebuild_the_index` baut `dutch = dutch_mark(resolved.languages)` einmal und reicht es an Erwartung und Stempel.
- `poller.py` (drei Stellen: `_open_state`, `_open_writer`, Stempel nach dem Crawl), `resources.py` (`expected_marks`), `one_load.py`: `dutch_mark=dutch_mark(languages)`. In resources.py nennt ein Kommentar, dass das bestehende `except OSError` auch ein fehlendes nl-Artefakt fängt (T-21-06-04).
- `index_status.py`: `"wordlistHashNl": "wordlist_hash_nl"` mit Kommentar.
- Baumhash zweimal nachgezogen (je Task im selben Commit), zuletzt `81587ca3...15149536`, `PACKAGE_FILES_TODAY` bleibt 57, Kommentare "Plan 21-06, task 1/2".

## Neue und erweiterte Tests

- `test_a_finished_rebuild_stamps_the_dutch_mark`: unter de,en,nl mit Fixture-Liste steht die Marke nach dem Umbau auf `dutch_mark(...)`, `version_mismatch` leer; vor dem Tausch keine Marke.
- `test_a_dutch_drift_is_one_the_rebuild_answers` parametrisiert (switched-on, new-list, switched-off): nur die nl-Marke driftet, Ergebnis REBUILD_THROUGH statt NOTHING_TO_REBUILD, danach keine Drift.
- `test_a_dutch_drift_does_not_raise_the_generation` (Poller): Index unter de,en,nl mit Marke "1:alt", `_open_state()` lässt die Generation stehen, Drift genau `[wordlist_hash_nl]`.
- D-08-Test `test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were`: nl-Marke "1:an-older-list" bleibt unverändert und steht in der Drift.
- `test_every_caller_in_src_names_the_dutch_mark` plus `test_the_dutch_mark_gate_sees_a_caller_without_it` (Selbsttest mit einzeiligem, mehrzeiligem, Attribut- und Kommentar-Fall).
- `test_the_report_carries_seven_version_keys_and_the_dutch_mark_among_them`.
- Rot-Gegenprobe Task 1: ohne `DUTCH_MARK` in `MARKS_A_REBUILD_ANSWERS` scheitern die drei Drift-Fälle und der Poller-Test (4 failed), mit ihr grün.

## Verifikation

- Task 1: test_index_rebuild, test_poller, test_main_lifespan, test_upgrade_compatibility, test_read_side, test_measurement_scripts: 637 passed, 1 skipped
- `-k "dutch_mark or seven_version"` in test_index_open/test_index_status: 5 passed
- Volle Suite: 2965 passed, 15 skipped
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün
- grep: `DUTCH_MARK` in rebuild.py 5, `stamp_after_swap(store, languages, dutch_mark=dutch)` 1, Poller-Testname 1, `ANALYZER_VERSION = 1` 1, `wordlistHashNl` 1, "Plan 21-06" 2

## Deviations from Plan

**1. [Rule 3] `test_read_side.py` außerhalb von `<files>` geändert.** Ein Aufruf von `stamp_after_swap` steht dort (jetzt `dutch_mark="off"`), und `test_a_fresh_container_searches_the_chains_it_was_switched_on_with` läuft unter sechs Sprachen, braucht also nach Task 2 `write_wordlist_nl(volume)`.

**2. Tests mit `write_wordlist_nl` ergänzt (wie im Plan vorgesehen):** test_poller.py (`test_a_fresh_volume_carries_the_two_marks_of_the_directory_it_builds`, Helfer `_switch_dutch_on` nimmt jetzt das Volume und legt die Liste ab, trifft damit auch die beiden 21-01-Tests), test_read_side.py (siehe 1). Keine Erwartung gelockert: der Frisch-Volume-Test prüft zusätzlich die nl-Marke und vergleicht gegen die echte nl-Erwartung.

**3. grep-Kriterium "0 Aufrufer ohne dutch_mark="** liefert 3 Treffer, alles Prosa (Kommentar resources.py, Docstrings stopwords.py und poller.py, die `expected_versions()` nur nennen). Alle echten Aufrufe tragen `dutch_mark=`, das AST-Gate zählt 6 Aufrufe und 0 ohne Keyword.

**4. Baumhash zweimal:** die Ratsche verlangt den Hash im selben Commit wie jede src-Änderung, deshalb je Task ein Eintrag.

## Offener Befund (geerbt, weiterhin nicht gefixt)

`stamp_after_rebuild` leert `REBUILD_MARK` trotz verbleibender Verzeichnis-Drift (21-01). Unter dem fullreindex-Ausweg bleibt die nl-Drift deshalb stehen und hebt pro Start erneut die Generation; der D-08-Test hält das für die nl-Marke fest. Der Band-Umbau ist die reguläre Antwort und stempelt sie jetzt korrekt.

## Threat Flags

Keine neue Oberfläche. T-21-06-01 (keyword-only ohne Default, Stempel hinter dem Tausch, Test), T-21-06-02 (Marke in MARKS_A_REBUILD_ANSWERS, Poller-Test), T-21-06-03 (AST-Gate mit Gegenprobe), T-21-06-04 (Kommentar am `except OSError`) mitigiert.

## Self-Check: PASSED

- FOUND: alle elf geänderten Dateien
- FOUND: Commits ca7a2c8, 6f79777
