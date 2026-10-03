---
phase: quick-261003-wxg
plan: 01
subsystem: reconcile, companion-app, measurements
tags: [reconcile, exclusions, D-06, IDX-04, T-28-03, 28-07, zaehltor]
requires: [ExclusionService::isExcluded, ExclusionService::mountRelativePath, FileRow.state/reason (Plan 05-03)]
provides: [Live-Markierung skipped(excluded) im File-Slice, excluded-Zweig in Reconcile._compare, teilkorpus-scharfer Vorrat am Zaehltor]
affects: [backend/src/findling/worker/reconcile.py, php/lib/Controller/ReconcileController.php, php/lib/Service/StorageService.php, docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh]
tech-stack:
  added: []
  patterns: [Live-Urteil ohne Persistenz, Prädikat-Closure gegen DI-Zyklus]
key-files:
  created:
    - php/tests/Unit/ReconcileControllerTest.php
  modified:
    - backend/src/findling/worker/reconcile.py
    - backend/tests/test_reconcile.py
    - php/lib/Service/StorageService.php
    - php/lib/Controller/ReconcileController.php
    - backend/tests/test_exclusion_path_space.py
    - backend/tests/test_measurement_scripts.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
    - backend/tests/test_v14_zelle.py
decisions:
  - "Kandidat 2 des Owner-Entscheids a: PHP markiert ausgeschlossene Zeilen live als skipped(excluded), der Container plant sie nicht ein und speichert nichts (Regelaufhebung wirkt in der nächsten Runde)"
  - "Bekannte Datei mit neuer etag bleibt content-Arbeit auch bei excluded-Markierung (CR-01: describe antwortet mit KIND_DELETE)"
  - "Zaehltor-Vorrat pfadscharf aus oc_findling_queue in der Doppellesung, globaler Vorrat nur protokolliert; Ende-Schritt bleibt global"
metrics:
  duration: "ca. 75 min"
  completed: 2026-10-04
  tasks: 3
  files: 9
---

# Quick 261003-wxg: Reconcile beachtet Ausschlüsse, Zaehltor teilkorpus-scharf

Der Reconcile plant Dateien unter Ausschlussregeln nicht mehr alle ~300 s neu ein: die PHP-Hälfte markiert sie im File-Slice live als skipped(excluded) über ExclusionService::isExcluded auf mountRelativePath, der Container lässt unbekannte markierte Zeilen ohne Speicherung liegen; das Zaehltor in 10-zelle.sh zählt den Vorrat nur noch unter files/teilkorpus (Lauf 7: 5549 -> 5000).

## Commits (nur lokal, kein Push)

| Task | Commit | Inhalt |
|------|--------|--------|
| 1 | 6dd65fc3 | fix(reconcile): leave files excluded by today's rules alone instead of requeueing them every round |
| 2 | 63762caa | fix(reconcile): mark files excluded by today's rules in the file slice |
| 3 | 12c659dd | docs(measurements): count the work stock of the partial corpus path sharp at the count gate (28-07) |

## RED-Belege

**Task 1** (zwei Stufen):
- Stufe 1, Konstanten fehlen: `ImportError: cannot import name 'EXCLUDED_REASON' from 'findling.worker.reconcile'` (Sammelfehler der ganzen Datei).
- Stufe 2, Konstanten da, Zweig fehlt: `4 failed, 83 passed`:
  - `test_an_excluded_unknown_file_is_not_requeued_by_two_cycles`: `assert [10, 11] == [11]`
  - `test_an_excluded_file_behind_a_tombstone_is_not_requeued`: `assert [([10], 'content')] == []`
  - `test_a_lifted_rule_makes_the_file_work_again_in_the_next_round`: `assert [10] == []` (Runde 1 plante 10 ein)
  - `test_a_round_of_only_excluded_files_closes_the_mount`: `assert (2, 0) == (0, 0)`
  - Schutzgeländer grün wie erwartet: Test D (CR-01, bekannte Datei mit neuer etag) und Test F (Vokabular).
- GREEN: `87 passed` (test_reconcile + test_extract_errors).

**Task 2**: `2 failed, 57 passed`:
- `test_the_reconcile_slice_marks_excluded_rows_through_the_helper`: `ReconcileController.php: never calls ExclusionService::isExcluded, so the reconcile requeues every excluded file it does not know on every quiet round`
- `test_the_slice_route_marks_excluded_rows_with_the_codes_of_the_closed_list`: `assert None is not None` (kein `= 'skipped';` im Controller)
- GREEN: `107 passed` (exclusion_path_space, reconcile, php_trust_boundary, readonly_gate).

**Task 3**: `3 failed, 7 passed` (teilkorpus-Zellentests):
- `test_cell_teilkorpus_passes_with_the_counters_of_run_7`: `... Zaehltor 5000 ist verfehlt (5549)`, `assert 71 == 0`
- `test_cell_teilkorpus_global_stock_fills_no_real_shortfall`: Zeile `zaehltor verfehlt 4951 statt 5000` fehlt (alt: 5500 aus 549 + 4951)
- `test_cell_teilkorpus_aborts_on_an_unreadable_partial_stock`: `assert 0 == 71` (alt lief die Zelle mit globalem Vorrat 0 durch)
- GREEN: `603 passed` (test_v14_zelle, test_v14_teilkorpus, test_measurement_scripts); `bash -n 10-zelle.sh` sauber.

## Testbilanz

- Vorher (Stand 261003-d3y): 4408 Tests grün.
- Nachher volle Python-Suite (Endlauf nach Task 3): **4421 passed, 25 skipped** (7:49 min). Zwischenlauf nach Task 2: 4418 passed. Neu: 6 Tests Task 1, 2 Tests Task 2, 3 Tests Task 3 (Python) plus 5 PHPUnit-Fälle (CI).
- Gates vor jedem Commit grün: ruff check (Vollregelsatz), ruff format --check (186 Dateien), pyright latest 0/0/0, vulture 80.
- `grep -v '^\s*#' reconcile.py | grep -c startswith` vorher 0, nachher 0 (kein Präfixvergleich im Container).
- Neue PHP-Zeilen in StorageService.php ohne str_starts_with/strncmp/preg_match (0).

## Was gebaut wurde

**Task 1 (Container):** `EXCLUDED_STATE = "skipped"`, `EXCLUDED_REASON = "excluded"` als Draht-Codes neben GIVEN_UP_*/HANDOVER_* (Kommentar: nur erkannt, Regel gehört PHP, D-06; nie gespeichert, weil ein gespeichertes Urteil die Regelaufhebung über `stored == row.etag` überleben würde). `_compare`: nach `stored == row.etag` und vor dem Give-up-Zweig `stored is None` und excluded -> `continue` ohne Schreiben und ohne Zähler. Sechs Tests (A bis F) laut Plan.

**Task 2 (PHP):** `StorageService::getFileSlice(..., ?\Closure $isExcludedPath = null)` markiert jede Zeile mit `excluded`, filtert nie (final-Marke und Löschregel). `ReconcileController` bekommt ExclusionService injiziert; `exclusionPredicate()` liefert null ohne Präfixe, sonst `mountRootPath` einmal pro Seite und ein Closure über `isExcluded(mountRelativePath(...))`. `withVerdicts` setzt skipped(excluded) mit Vorrang vor dem findling_file_state-Urteil und entfernt `excluded` vor der Antwort (sieben Drahtfelder, T-wxg-01). Gate D: ReconcileController als vierte Aufrufstelle plus Anti-Vakuum. PHPUnit `ReconcileControllerTest` mit fünf Fällen (ohne Präfixe keine Markierung; nur loadtest-Zeile markiert; Zeile bleibt, final unverändert; Vorrang vor gespeichertem Urteil; sieben Felder).

**Task 3 (Werkzeug):** Vorrat am Zaehltor per `db_lesen` aus `oc_findling_queue JOIN oc_filecache ... like 'files/teilkorpus/%'` in der Doppellesungs-Schleife neben der Frisch-Query; `vorrat_global` aus occ nur protokolliert; Zeile `zaehlung vorrat-teilkorpus X vorrat-global Y ...`; unlesbar -> summe unlesbar -> Abbruch 71. Stub `STUB_VORRAT_TEIL` (Wert, `fehler`, sonst Rückfall auf STUB_SCHEDULED + STUB_HANDED der Zaehltor-Lesung, damit die alten Belegtests ihre Zahlen behalten).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash-Pins neu gesetzt**
- **Gefunden bei:** Task 2 (volle Suite)
- **Problem:** `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` rot, weil Task 1 reconcile.py geändert hat; PHP-Hash rot durch Task 2 (88 statt 87 Dateien).
- **Fix:** PACKAGE_TREE_HASH_TODAY (71 Dateien, a6ad7397...) per `--amend` in den noch lokalen Task-1-Commit, damit jeder Commit für sich grün ist; PHP_TREE_HASH_TODAY (88 Dateien, 2023c844...) im Task-2-Commit, beides mit Kommentar im Stil von d799ef53.
- **Dateien:** backend/tests/test_measurement_scripts.py
- **Commits:** 6dd65fc3, 63762caa

**2. Test-Kontext erweitert:** test_measurement_scripts.py stand nicht in der files-Liste von Task 1/2, die Neupinnung verlangt der Plan aber ausdrücklich ("Falls Tests Baum-Hashes ... pinnen, neu pinnen wie in d799ef53").

Sonst plangemäß.

## Vorbehalte und vorgemerkte Punkte

1. **CI-Vorbehalt:** `php -l` und PHPUnit (`ReconcileControllerTest.php`, Konstruktoränderung `ReconcileController`, neue Signatur `getFileSlice`) laufen lokal nicht (kein PHP, Docker-Daemon aus). Sie laufen nach dem Push in php.yml.
2. **Lauf 8 braucht ZWEI Dinge auf der Box:** ein NEUES Container-Abbild (CI baut nach dem Push, mit dem excluded-Zweig in `_compare`) UND die Companion-App aus `php/` erneut in `custom_apps/findling` (wie bei Lauf 7), sonst fehlt die excluded-Markierung im Slice und der Schub bleibt. Mit nur einer der beiden Hälften: altes PHP + neuer Container = Schub wie bisher (keine Markierung); neues PHP + alter Container = Container ignoriert die Codes, Schub wie bisher. Der Zaehltor-Fix (Task 3) greift unabhängig davon.
3. **Ende-Schritt von 10-zelle.sh** liest den Vorrat weiter global (nicht erbeten). Nach dem Produkt-Fix ohne Schub ausgeschlossener Dateien unkritisch; sollte Lauf 8 dort hängen, ist das der erste Verdacht.
4. Bestehende Queue-Zeilen ausgeschlossener Dateien räumt `--restart` (93i); danach entstehen keine neuen mehr aus dem Reconcile.

## Threat Flags

Keine neue Angriffsfläche: keine neue Route, das Prädikat sieht den internen Pfad nur in PHP, die Antwort bleibt bei sieben Feldern, Log nur Zähler.

## Self-Check: PASSED

- FOUND: php/tests/Unit/ReconcileControllerTest.php, 261003-wxg-SUMMARY.md
- FOUND: 6dd65fc3, 63762caa, 12c659dd
- Keine Löschungen seit 7a082907; volle Suite grün (4421 passed, 25 skipped); bash -n sauber.
