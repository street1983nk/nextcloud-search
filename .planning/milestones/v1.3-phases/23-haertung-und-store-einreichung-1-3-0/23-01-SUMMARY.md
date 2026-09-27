---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 01
subsystem: embed, api
tags: [kaltstart, warmlauf, backgroundtasks, snippets, D-01, D-02, D-03, D-08]
requires: []
provides:
  - "query_may_load() antwortet bei jedem Schalterwert False"
  - "Warmlauf über BackgroundTasks nach dem Antwortversand"
  - "Einwortregel, Operatorregel und titleOnly auf /snippets"
affects:
  - "Plan 23-04 (one_load, integration.yml, probe_image_search, Doku)"
tech-stack:
  added: []
  patterns:
    - "FastAPI BackgroundTasks im Handler statt loser asyncio.create_task"
key-files:
  created:
    - .planning/phases/23-haertung-und-store-einreichung-1-3-0/deferred-items.md
  modified:
    - backend/src/findling/embed/engine.py
    - backend/src/findling/api/search.py
    - backend/src/findling/api/snippets.py
    - backend/tests/test_embed_engine.py
    - backend/tests/test_embed_model.py
    - backend/tests/test_search_endpoint.py
    - backend/tests/test_snippets_endpoint.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "/snippets fordert keinen Warmlauf an: eine Auslösestelle reicht, /search derselben Anfrage fordert bereits an (Claude's Discretion)"
  - "PARAPHRASE in test_snippets_endpoint.py ist jetzt zweiwortig, weil ein Wort auf /snippets keine semantische Seite mehr baut"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-27
  tasks: 2
  files: 8
---

# Phase 23 Plan 01: Kaltstart-Fix V-22-01/V-22-02 Summary

Die erste Suche nach einem Neustart lädt nie Modellgewichte im Request, bei keinem Schalterwert. `query_may_load()` antwortet konstant False, der Warmlauf läuft über `BackgroundTasks` nach dem Antwortversand, und `/snippets` baut für einwortige, Operator- und titleOnly-Zeilen keine semantische Seite.

## Umsetzung

**Task 1 (engine.py):** `query_may_load()` gibt False zurück. Der Docstring sagt jetzt, dass der allgemeine Fall mit Phase 23 geschlossen ist. Den Block „if query_may_load(): return False“ in `warm_wanted()` gibt es nicht mehr, es gelten drei Bedingungen. `warm()`, der Schutz über `_WARMING`, `model.py` und `main.py` sind unverändert (per `git diff 8b060e5` geprüft).
Tests: `query_may_load` ist bei „0“ und „900“ False. `warm_wanted` ist bei „0“ nach `request_warm()` True. Ohne Anforderung wird nichts gewärmt (D-03). Der Zehnerfall ist über beide Werte parametrisiert und erwartet genau 1 Ladevorgang. Neu ist der Ladefenster-Test (D-08) in `test_embed_model.py`: Thread A hält `_lock` 200 ms, und die Anfrage mit `may_load=False` wartet so lange.

**Task 2 (search.py, snippets.py):** Der Handler nimmt `background: BackgroundTasks` entgegen und ruft `background.add_task(warm)` hinter `warm_wanted()`. `_WARM_TASKS` gibt es nicht mehr. Der Kommentar begründet den Weg mit dem GIL beim Sessionaufbau in onnxruntime 1.30.0 und nennt das akzeptierte Ladefenster (D-08). `/snippets` setzt `lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only`. `may_load` bleibt `query_may_load()`.
Die Handlertests prüfen `background.tasks` statt `_WARM_TASKS`. Die AST-Prüfung verlangt genau einen `add_task(warm)`, kein `create_task` und einen Parameter vom Typ `BackgroundTasks`. Neu sind:
- der Einwort-Fall: kein Warmlauf
- die D-02-Parametrisierung auf `/snippets`
- ein Fall, der zeigt, dass `/snippets` keinen Warmlauf anfordert

Ledger: `PACKAGE_TREE_HASH_TODAY` = `31ae5df4...`, 57 Dateien, mit einem datierten Absatz.

## Commits

| Task | Commit | Art |
|------|--------|-----|
| 1 RED | b5ece13 | test(23-01) |
| 1 GREEN | 205272f | feat(23-01) |
| 2 RED | 4efe9f8 | test(23-01) |
| 2 GREEN | 8d079cb | feat(23-01) |

## Deviations from Plan

**1. [Rule 1 - Bug] Weitere Tests hingen am alten Verhalten**
- `test_search_endpoint.py`: Die Parametrisierung `[("0", True), ...]` und `off.seen == [True]` wurden umgedreht. `test_the_answer_does_not_wait_for_the_warm_run`, `test_ten_searches_in_a_row...` (jetzt über „0“ und „900“ und `== 1`) und der AST-Fall wurden auf `BackgroundTasks` umgestellt. `ARRIVAL_SECONDS` ist entfernt, weil nichts mehr lose läuft.
- `test_snippets_endpoint.py`: `PARAPHRASE` ist jetzt „Weltraumbahnhof Mondfähre“, weil eine einwortige Zeile den zweiten Auszugspfad nicht mehr erreicht.
- `test_measurement_scripts.py`: Der historische Ledgerabsatz nannte `_WARM_TASKS`. Er ist umformuliert, damit die Akzeptanzprüfung „kein Treffer in backend/tests“ gilt.

## Deferred Issues

- **tests/test_one_load.py: 7 Fälle sind rot.** `tools/one_load.py` erwartet, dass die Suche selbst lädt. Das ist die gewollte Folge von D-01 und laut `files_modified` ausdrücklich Aufgabe von Plan 23-04, Task 1. Eingetragen in `deferred-items.md`. Damit ist das Kriterium „pytest 0 failed“ dieses Plans nur ohne `test_one_load.py` erfüllt: 3329 passed, 15 skipped, 7 failed, alle 7 in `test_one_load.py`.
- Die CI-Stellen in `integration.yml` und `probe_image_search.py` folgen ebenfalls in Plan 23-04.

## Verifikation

- ruff check, ruff format --check, pyright latest (0 errors), vulture 80: grün
- pytest: 3329 passed, 15 skipped (Skipzahl wie vorher), 7 failed nur in `test_one_load.py` (siehe oben)
- Logzeilen unverändert: nur Typnamen und Zähler (T-23-04)

## Self-Check: PASSED

- Commits b5ece13, 205272f, 4efe9f8 und 8d079cb sind vorhanden
- Alle Dateien aus key-files sind vorhanden
