---
phase: 21-niederlaendische-komposita
plan: 01
subsystem: index/rebuild, worker/poller, ci
tags: [komposita, nl, drift, generation, fullreindex, d-08]
requires: []
provides:
  - D-08-Charakterisierungstests des fullreindex-Auswegs
  - start_rebuild_on_drift mit keyword-only answered_elsewhere
  - Poller hebt bei reiner Sprach-/Schemadrift keine Generation mehr
affects: [21-05]
tech-stack:
  added: []
  patterns: [Beobachtung zusichern statt Wunschverhalten, answered_elsewhere als Ausnahmemenge]
key-files:
  created: []
  modified:
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_poller.py
    - backend/src/findling/index/open.py
    - backend/src/findling/worker/poller.py
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/deploy-harp.yml
decisions:
  - "D-08 beobachtet: der fullreindex-Ausweg stempelt die Verzeichnismarken NICHT (languages bleibt de,en, schema_version bleibt 1, Drift bleibt)"
  - "Checkpoint Task 2, Owner-Entscheid 25.09.2026 Option 1: Patch eingespielt, CI Store upgrade 6 Zusicherung 8 erwartet jetzt KEINE Drift-Zeile mehr"
metrics:
  duration: ca. 60 min
  completed: 2026-09-25
  tasks: 2 von 2
---

# Phase 21 Plan 01: D-08 und Poller-Drift-Falle Summary

D-08 per Test beantwortet (der Vollreindex-Ausweg stempelt die Verzeichnismarken nicht) und die Poller-Drift-Falle geschlossen: eine reine Sprach- oder Schemadrift hebt beim Öffnen des Zustands keine Generation mehr, die nl-Marke kann damit ohne Vollreindex in diese Behandlung aufgenommen werden.

## Task 1: D-08 (Commit 88bc24a)

- **Ergebnis D-08 in einem Satz:** Nein, der Ausweg `FINDLING_REBUILD_FALLBACK=fullreindex` stempelt die Verzeichnismarken nicht: nach Generationshub, durchgelaufenem Crawl und `stamp_after_rebuild` steht `languages` weiter auf `de,en`, `schema_version` weiter auf `1`, und `version_mismatch` nennt weiterhin `languages`.
- Tests: `test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were`, `test_the_full_reindex_way_out_raises_the_generation_once_per_drift` (2 passed). Docstring nennt `wordlist_hash_nl` und `_MARKS_OF_A_DIRECTORY`.
- **Zusatzbefund (per Test festgeschrieben, nicht gefixt):** `stamp_after_rebuild` leert `REBUILD_MARK`, obwohl die Sprachdrift bleibt. Der nächste Start (`_rebuild_is_due` fragt bei jedem Start) läuft wieder in den Fallback und hebt die Generation ERNEUT. Unter dem Ausweg kostet ein Sprachwechsel also einen Vollcrawl pro Start, bis die Einstellung zurückgenommen oder der Band-Umbau erlaubt wird. Mitten im Crawl hält der Fingerabdruck, erst nach dem Abschluss beginnt die Schleife. Vor Plan 21-05 zu entscheiden, weil die nl-Marke das erbt.

## Task 2: Poller-Drift-Falle (Commit 19ea9d5)

- **RED belegt:** Test A `test_a_drift_the_band_rebuild_answers_does_not_raise_the_generation` vor dem Fix: `assert 2 == 1` (Generation 1 -> 2 beim bloßen `_open_state()` unter `de,en,nl`). Tests B und C waren schon grün.
- **Fix:** `start_rebuild_on_drift(..., *, answered_elsewhere=frozenset())` in `open.py` (Fingerabdruck weiter über die volle Erwartung), Aufruf `answered_elsewhere=MARKS_A_REBUILD_ANSWERS` in `poller._open_state` (Import auf Modulebene, kein Importkreis). `rebuild.py` unverändert, der Fallback-Zweig ruft weiter ohne Parameter.
- Baumhash neu `a67a1aa17a45...fcc775`, `PACKAGE_FILES_TODAY` bleibt 56, datierter Kommentar gesetzt.
- **Checkpoint-Ausgang:** Die Planvorgabe hielt Task 2 an, weil `deploy-harp.yml` "Store upgrade 6", Zusicherung 8 genau EINE `built by different code`-Zeile nach dem Sprachsprung verlangte. Owner-Entscheid 25.09.2026: Option 1. Zusicherung 8 erwartet jetzt 0 Zeilen, Kommentar, Fehlermeldung, Fensterkommentar und Step-Summary-Zeile nachgezogen. Der Language-proof-Schritt ist unberührt (Parallel-Plan 21-08).
- Textgates geprüft: `test_language_proof_steps.py` nagelt nur Präfix und Bedingung von "Store upgrade 6" fest, nicht die Drift-Zählung; kein weiteres Gate betroffen.

## Verifikation

- Tests A-C: 3 passed.
- Volle Backend-Suite: 2886 passed, 15 skipped.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün.
- `grep -c "answered_elsewhere=MARKS_A_REBUILD_ANSWERS" poller.py` = 1, `grep -c answered_elsewhere rebuild.py` = 0.

## Deviations from Plan

- Test 1 um einen dritten Schritt erweitert (zweiter Start nach dem Stempel), um den Zusatzbefund zur Wiederholungsschleife festzuschreiben.
- CI-Zusicherung 8 in `deploy-harp.yml` geändert: laut Plan wäre das eine Owner-Frage gewesen, der Owner hat Option 1 freigegeben.

## Threat Flags

Keine neuen Oberflächen. T-21-01-01 mitigiert (Tests A-C halten beide Richtungen), T-21-01-02 mitigiert (Test `..._raises_the_generation_once_per_drift`).

## Self-Check: PASSED

- FOUND: backend/tests/test_index_rebuild.py (beide Testnamen je 1x)
- FOUND: backend/tests/test_poller.py (drei Testnamen)
- FOUND: Commits 88bc24a, 19ea9d5
