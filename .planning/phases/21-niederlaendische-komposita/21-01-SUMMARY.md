---
phase: 21-niederlaendische-komposita
plan: 01
subsystem: index/rebuild, worker/poller
tags: [komposita, nl, drift, generation, fullreindex, d-08]
status: angehalten (Task 2, Owner-Frage)
requires: []
provides:
  - D-08-Charakterisierungstests des fullreindex-Auswegs
  - fertiger, geprüfter Patch für die Poller-Drift-Falle (nicht eingespielt)
affects: [21-05]
tech-stack:
  added: []
  patterns: [Beobachtung zusichern statt Wunschverhalten]
key-files:
  created:
    - .planning/phases/21-niederlaendische-komposita/21-01-task2-angehalten.patch
  modified:
    - backend/tests/test_index_rebuild.py
decisions:
  - "D-08 beobachtet: der fullreindex-Ausweg stempelt die Verzeichnismarken NICHT (languages bleibt de,en, schema_version bleibt 1, Drift bleibt)"
  - "Task 2 laut Planvorgabe angehalten: CI-Zusicherung 8 von Store upgrade 6 erwartet genau einen Generationshub nach einem Sprachwechsel"
metrics:
  duration: ca. 35 min
  completed: 2026-09-25
  tasks: 1 von 2 committet, Task 2 fertig als Patch, angehalten
---

# Phase 21 Plan 01: D-08 und Poller-Drift-Falle Summary

D-08 per Test beantwortet (der Vollreindex-Ausweg stempelt die Verzeichnismarken nicht); die Poller-Drift-Falle ist rot belegt und gefixt, der Fix aber laut Planvorgabe NICHT eingespielt, weil eine CI-Zusicherung genau den Generationshub nach Sprachwechsel verlangt.

## Task 1: D-08 (Commit 88bc24a)

- **Ergebnis D-08 in einem Satz:** Nein, der Ausweg `FINDLING_REBUILD_FALLBACK=fullreindex` stempelt die Verzeichnismarken nicht: nach Generationshub, durchgelaufenem Crawl und `stamp_after_rebuild` steht `languages` weiter auf `de,en`, `schema_version` weiter auf `1`, und `version_mismatch` nennt weiterhin `languages`.
- Beobachtung entspricht der Erwartung aus PATTERNS.md, bis auf einen Zusatzbefund (unten).
- Tests: `test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were`, `test_the_full_reindex_way_out_raises_the_generation_once_per_drift` (2 passed). Docstring nennt `wordlist_hash_nl` und `_MARKS_OF_A_DIRECTORY`.
- **Zusatzbefund (per Test festgeschrieben):** `stamp_after_rebuild` leert `REBUILD_MARK`, obwohl die Sprachdrift bleibt. Der nächste Start (`_rebuild_is_due` fragt bei jedem Start) läuft wieder in den Fallback und hebt die Generation ERNEUT. Unter dem Ausweg bedeutet ein Sprachwechsel also einen Vollcrawl pro Start, bis die Einstellung zurückgenommen oder der Band-Umbau erlaubt wird. Mitten im Crawl hält der Fingerabdruck (zweiter Test), erst nach dem Abschluss beginnt die Schleife. Nicht gefixt (außerhalb des Plans), gehört vor Plan 21-05 entschieden, weil die nl-Marke das erbt.

## Task 2: Poller-Drift-Falle (angehalten, nicht committet)

- **RED belegt:** Test A `test_a_drift_the_band_rebuild_answers_does_not_raise_the_generation` vor dem Fix: `assert 2 == 1` (Generation 1 -> 2 beim bloßen `_open_state()` unter `de,en,nl`). Tests B und C waren schon grün.
- **Fix gebaut und geprüft:** `start_rebuild_on_drift(..., *, answered_elsewhere=frozenset())` in `open.py`, Aufruf `answered_elsewhere=MARKS_A_REBUILD_ANSWERS` in `poller._open_state` (Import auf Modulebene, kein Importkreis, `import findling.worker.poller, findling.main` ok), `rebuild.py` unverändert, Baumhash neu `a67a1aa1...fcc775`, `PACKAGE_FILES_TODAY` bleibt 56.
- Mit Fix: 3 passed; `test_poller.py test_index_rebuild.py test_index_open.py test_main_lifespan.py test_measurement_scripts.py` 630 passed, 1 skipped; ruff, ruff format, pyright (latest) 0 Fehler, vulture grün.
- **Warum angehalten (Planvorgabe "Owner-Frage, Zusicherung nicht ändern"):** `.github/workflows/deploy-harp.yml` Z. 4851-4868, "Store upgrade 6", Zusicherung 8 "exactly one drift line, not none and not two": nach dem Sprachsprung verlangt die CI genau EINE Logzeile `built by different code` von `start_rebuild_on_drift` und begründet das mit "the poller opens the state database at its start, finds the language mark of the old set and says so once". Das ist inhaltlich die Zusicherung "indexVersion wird 2 nach Sprachwechsel" (der grep auf `indexVersion` allein findet sie nicht, nur Z. 3608 und 4122, beide ohne Sprachwechsel). Mit dem Fix schreibt der Poller diese Zeile nicht mehr, Zusicherung 8 würde rot (0 statt 1).
- Der fertige Patch liegt unter `.planning/phases/21-niederlaendische-komposita/21-01-task2-angehalten.patch` (`git apply --check` ok) und enthält Tests A-C, beide src-Eingriffe und den Baumhash im selben Stand.

### Owner-Frage

Soll der Poller eine reine Sprach-/Schema-Drift künftig NICHT mehr mit einem Generationshub beantworten (Plan-Absicht, spart den Vollreindex hinter der Re-Analyse)? Dann Patch einspielen und Zusicherung 8 von Store upgrade 6 auf "keine Drift-Zeile" umstellen (Zählung 0, Begründung: der Band-Umbau beantwortet die Drift). Oder ist der Hub gewollt, dann entfällt Task 2 und die nl-Marke erbt den Vollreindex.

## Deviations from Plan

- Task 2 nicht committet, weil die im Plan vorgesehene Haltebedingung (CI-Zusicherung erwartet Generationshub nach Sprachwechsel) greift. Arbeit als Patch gesichert statt verworfen.
- Test 1 um einen dritten Schritt erweitert (zweiter Start nach dem Stempel), um den Zusatzbefund zur Wiederholungsschleife festzuschreiben.

## Threat Flags

Keine neuen Oberflächen. T-21-01-01 bleibt bis zur Owner-Entscheidung offen (Poller hebt bei Sprachdrift weiterhin).

## Self-Check: PASSED

- FOUND: backend/tests/test_index_rebuild.py (beide Testnamen je 1x)
- FOUND: .planning/phases/21-niederlaendische-komposita/21-01-task2-angehalten.patch
- FOUND: Commit 88bc24a
