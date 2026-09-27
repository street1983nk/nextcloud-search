---
phase: 17-owner-tor-und-analyseketten
plan: 07
subsystem: database
tags: [tantivy, versionsmarken, store, upgrade, reindex, ratchet]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: "Plan 17-04: vollzogenes Owner-Tor, E-17-7 Option a (lockern), mit fertigen Ersatztexten"
  - phase: 17-owner-tor-und-analyseketten
    provides: "Plaene 17-02/17-03/17-06: Kettentabellen und Waechtertests, die den aufgegebenen Teil der Absicherung halten"
provides:
  - "Store.version_mismatch vergleicht bei tantivy_version nur noch die index_format-Haelfte"
  - "_index_format_matches als zweiter Ausnahme-Vergleicher neben _generation_at_least, faellt geschlossen"
  - "Upgrade-Ratsche haelt gegen GOLD_INDEX_FORMAT statt gegen die Patchnummer, mit zwei neuen Selbstproben"
affects: [17-08, tantivy-pin, deploy-harp, dependabot]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zweite Ausnahme in der Vergleichsschleife nach dem Muster der index_version-Ausnahme"
    - "Vergleicher faellt geschlossen: None, leer und unlesbarer Banner sind Abweichungen"

key-files:
  created: []
  modified:
    - backend/src/findling/store/repo.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "E-17-7 Option a vollzogen: gespeichert wird der volle Banner, verglichen nur die index_format-Haelfte"
  - "Der Vergleicher faellt geschlossen: ein Banner ohne Formathaelfte ist eine Abweichung, kein Freibrief"
  - "TANTIVY_PIN bleibt in diesem Plan auf 0.26.0; der Pin wandert erst in Plan 17-08, damit die Lockerung fuer sich beweisbar bleibt"

patterns-established:
  - "Ausnahme-Vergleicher: private Modulfunktion neben _generation_at_least, Docstring nennt den Grund fuer das geschlossene Fallen"
  - "Jede Aenderung an backend/src/findling/**/*.py zieht PACKAGE_TREE_HASH_TODAY samt Begruendungsabsatz nach"

requirements-completed: [LEX-07]

# Metrics
duration: 35min
completed: 2026-09-23
---

# Phase 17 Plan 07: Die gelockerte Vergleichsregel fuer tantivy_version Summary

**`Store.version_mismatch` entscheidet bei `tantivy_version` nur noch ueber die `index_format`-Haelfte des Banners, faellt bei jedem unlesbaren Wert geschlossen, und die Upgrade-Ratsche haelt jetzt gegen `GOLD_INDEX_FORMAT` statt gegen die Patchnummer.**

## Performance

- **Duration:** ca. 35 min
- **Started:** 2026-09-23
- **Completed:** 2026-09-23
- **Tasks:** 2 (beide TDD, RED vor GREEN)
- **Files modified:** 4

## Accomplishments

- `_index_format_matches(stored, expected)` liegt neben `_generation_at_least` und liefert alle fuenf im Plan behaupteten Ergebnisse: gleiche Formathaelfte in beide Richtungen `True`, andere Haelfte `False`, `None` `False`, leer `False`, Banner ohne `index_format` `False`.
- `Store.version_mismatch` traegt genau eine neue `if`-Zeile (`key == "tantivy_version"`); die `index_version`-Ausnahme und der Satz "A mark that was never written counts as diverging" sind unveraendert.
- Der neue Docstring-Absatz nennt alle vier geforderten Punkte: voller Banner bleibt gespeichert, nur die Formathaelfte entscheidet, der aufgegebene Teil wird namentlich in `backend/tests/test_analyzer.py` und `backend/tests/test_language_analyzers.py` gehalten, Belege sind die Messung vom 2026-09-23 und `E-17-7 Option a`.
- `GOLD_V1_0_AND_V1_1["tantivy_version"]` ist `GOLD_INDEX_FORMAT`; die Zeichenkette `"0.26.0"` steht nicht mehr in der Gold-Tabelle. `GOLD_INDEX_FORMAT` steht jetzt vor dem Woerterbuch, mit einem Kommentarblock, der `E-17-7 Option a` vom 23.09.2026 und die vier Messbelege zitiert.
- Zwei neue Selbstproben: `test_a_patch_bump_with_the_same_index_format_is_no_drift` (gruen) und `test_a_changed_index_format_is_still_drift` (der rote Zustand, nachweislich erzeugbar). Volle Suite geht von 2507 auf 2514 passed, +7 Tests.
- `TANTIVY_PIN` steht unveraendert auf `"tantivy==0.26.0"` und traegt den Kommentar, dass der Pin erst in Plan 17-08 wandert.

## Task Commits

1. **Task 1 (RED): Tests fuer die gelockerte Regel** , `11af212` (test)
2. **Task 1 (GREEN): `_index_format_matches` + zweite Ausnahme + Docstring** , `242660c` (feat)
3. **Task 2 (RED): vierte und fuenfte Selbstprobe** , `2d9f5d6` (test)
4. **Task 2 (GREEN): Gold-Werte auf die Formathaelfte** , `b65f3ee` (feat)
5. **Rule-3-Nachzug: Baumhash der Paketquellen** , `658a19f` (fix)

## Files Created/Modified

- `backend/src/findling/store/repo.py` , `_index_format_matches` neben `_generation_at_least`, zweite Ausnahme in der Vergleichsschleife von `Store.version_mismatch`, neuer Docstring-Absatz mit Messbeleg und Entscheidkennung.
- `backend/tests/test_upgrade_compatibility.py` , `GOLD_INDEX_FORMAT` vor die Gold-Tabelle gezogen und als deren `tantivy_version`-Wert gesetzt, Kommentarblock mit `E-17-7 Option a` und den vier Messbelegen, Kommentar an der `held = ...`-Zeile gegen spaetere "Vereinheitlichung", Kommentar an `TANTIVY_PIN` zur Reihenfolge 17-07 vor 17-08, zwei neue Selbstproben.
- `backend/tests/test_store_repo.py` , fuenf neue Tests: Patch-Bump kein Drift, geaendertes Format bleibt Drift, Banner ohne Formathaelfte bleibt Drift, die fuenf Faelle des Vergleichers direkt, und eine Probe, dass die anderen Marken unberuehrt sind.
- `backend/tests/test_measurement_scripts.py` , `PACKAGE_TREE_HASH_TODAY` nachgezogen samt Begruendungsabsatz (siehe Deviation 1).

**Nicht angefasst, wie vom Plan verlangt:** `backend/pyproject.toml`, `backend/uv.lock`, `backend/src/findling/index/open.py` (per `git diff --quiet` gegen den Basis-Commit geprueft).

## Decisions Made

- Die Ersatztexte aus `17-GRUNDSATZ-ENTSCHEID.md` wurden woertlich uebernommen, mit `<VORLAGETAG>` = 2026-09-23, mit zwei bewussten Abweichungen zugunsten des Plans:
  - `TANTIVY_PIN` bleibt `"tantivy==0.26.0"` (der Entscheid-Text zeigt schon 0.26.2; der Plan 17-07 verbietet jede Pin-Bewegung, der Pin gehoert zu 17-08).
  - Die neuen Selbstproben sind zwei eigene Testfunktionen statt einer Ergaenzung innerhalb `test_the_drift_reader_fires_on_a_staged_sample`, wie der Plan es in Task 2 c) vorgibt.
- Der Docstring-Absatz nennt die Ersatz-Testdateien namentlich (T-17-29 im Threat Register verlangt das), ueber den Entscheid-Text hinaus, der nur von "chain tables of phase 17" spricht.
- `_index_format_matches` prueft `if not stored` statt `if stored is None`, damit der leere String denselben geschlossenen Weg nimmt; die Verhaltensbehauptung des Plans verlangt beides als `False`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash der Paketquellen nachgezogen**
- **Found during:** Task 2 (voller Suitenlauf nach dem GREEN-Commit)
- **Issue:** `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` war rot, weil `PACKAGE_TREE_HASH_TODAY` den Baum aller `backend/src/findling/**/*.py` festhaelt und die Aenderung an `store/repo.py` ihn bewegt hat. Die Dateizahl blieb bei 55, nur die Bytes einer Datei bewegten sich.
- **Fix:** Konstante auf `1a1eaf410435e501f704c7c6e4f9033939afe5ed297fa36ffdffeaa12b12d013` gesetzt und den Begruendungsabsatz nach dem Muster der sechzehn vorherigen Nachzuege ergaenzt (Plannummer, die eine bewegte Datei, die Entscheidkennung).
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` , 376 passed; volle Suite danach 2514 passed, 15 skipped.
- **Committed in:** `658a19f`
- **Hinweis fuer den Merge der Welle:** Diese Konstante ist ein Baumhash ueber den gesamten Paketbaum. Jeder andere Plan dieser Welle, der eine Datei unter `backend/src/findling/` bewegt, erzeugt hier denselben Konflikt. Der Merge braucht eine einzige neue Messung ueber den zusammengefuehrten Baum, genau wie beim Wave-Merge von 17-02 und 17-03, den der Kommentarblock an der Konstante bereits beschreibt.

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Kein Scope-Zuwachs. Der Nachzug ist die im Repo etablierte Pflicht jeder Aenderung an den Paketquellen und beruehrt keine Produktionslogik.

## Issues Encountered

- Die fuenfte Selbstprobe (`test_a_changed_index_format_is_still_drift`) war schon im RED-Lauf gruen, weil der alte Gold-Wert `"0.26.0"` in einem 0.27.0-Banner ebenfalls fehlt. Sie ist als Regressionswaechter gedacht und wurde im RED-Commit als solche benannt; der RED-Beweis der Lockerung haengt an der vierten Probe, die vor dem GREEN nachweislich rot war (`AssertionError: ["tantivy_version ist 'tantivy v0.26.2, index_format v7' ..."]`).

## Verification

- `uv run python -c "... _index_format_matches ..."` (die sechs Behauptungen des Plans) , `GRUEN`
- `uv run python -m pytest -q` aus `backend/` , **2514 passed, 15 skipped**, noch mit tantivy 0.26.0
- `uv run ruff check` , All checks passed
- `uv run ruff format --check` , 129 files already formatted
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` , 0 errors, 0 warnings, 0 informations
- `uv run vulture` , keine Ausgabe
- `git diff --quiet <base> HEAD -- backend/pyproject.toml backend/uv.lock backend/src/findling/index/open.py` , unberuehrt
- `grep -q 'TANTIVY_PIN = "tantivy==0.26.0"'` und `grep -qF "A red test here is not a repair"` , beide gruen
- Vorbedingung geprueft: `17-GRUNDSATZ-ENTSCHEID.md`, Abschnitt "Vollzug am 23.09.2026", Tabelle "Greifender Zweig je Entscheid": **E-17-7 = a**. Damit gilt der volle Plan.

## Known Stubs

Keine.

## User Setup Required

Keine.

## Next Phase Readiness

- Plan 17-08 kann den Pin bewegen: `backend/pyproject.toml` auf `tantivy==0.26.2`, danach `uv lock --upgrade-package tantivy` und `uv sync` aus `backend/`, nie eine Handkante an `backend/uv.lock`. Anschliessend `TANTIVY_PIN` in `backend/tests/test_upgrade_compatibility.py` auf `"tantivy==0.26.2"` nachziehen und den dortigen Kommentar zur Reihenfolge entfernen.
- Ebenfalls fuer 17-08 offen, jeweils mit dem Messbeleg vom 2026-09-23 im Kommentar: die Zusicherung 2 in `.github/workflows/deploy-harp.yml`, der Begruendungskommentar in `.github/dependabot.yml` und `THIRD-PARTY.md`.
- Beim Merge dieser Welle ist `PACKAGE_TREE_HASH_TODAY` in `backend/tests/test_measurement_scripts.py` die erwartbare Konfliktstelle; sie braucht eine einzige Messung ueber den zusammengefuehrten Baum.

---
*Phase: 17-owner-tor-und-analyseketten*
*Completed: 2026-09-23*

## Self-Check: PASSED

- Alle vier geaenderten Quelldateien und die SUMMARY liegen auf der Platte.
- Alle fuenf Commits (`11af212`, `242660c`, `2d9f5d6`, `b65f3ee`, `658a19f`) stehen in der Historie des Worktree-Branches.
