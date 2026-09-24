---
phase: 18-schema-marken-und-umbauweg
plan: 05
subsystem: store
tags: [version-marks, drift, seed, languages, upgrade-compatibility, E-17-4]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: "E-17-4 Option a (Sprachmenge wird Merker, normalisiert nach Schemafeldreihenfolge), _index_format_matches als zweite benannte Ausnahme"
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-01: SCHEMA_VERSION 2 und sechs Koerperfelder; Plan 18-02: _languages() filtert gegen SUPPORTED_LANGUAGES; Plan 18-03: sicherer Zwischenstand"
provides:
  - "Sechster Versionsmerker languages in expected_versions(digest, languages)"
  - "_languages_are_legacy als dritte benannte Ausnahme in Store.version_mismatch"
  - "Saat schreibt den Sprachmerker nie, auch nicht wenn ein Aufrufer ihn hereinreicht"
  - "Sechster Eintrag im index_status-Bericht als sichtbarer Unterschied 1.2.0 gegen 1.3.0"
affects: [18-11, 20-sprachumbau, release-haertung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dritte benannte Ausnahme in der Vergleichsschleife, Bauart _generation_at_least / _index_format_matches (stored: str | None zuerst, Rueckgabe bool, Docstring begruendet statt behauptet)"
    - "Merker aus der Saat heraushalten: _seed_meta wirft den Schluessel raus, auch wenn der Aufrufer ihn liefert (dritter Fall neben EMBEDDING_MARK und index_version)"
    - "Umgebungsabhaengige Werte werden an expected_versions hereingereicht, nie im Modul aus settings() gelesen"

key-files:
  created: []
  modified:
    - backend/src/findling/index/open.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/tools/one_load.py
    - backend/src/findling/tools/index_status.py
    - backend/tests/conftest.py
    - backend/tests/probe_image_search.py
    - backend/tests/test_index_open.py
    - backend/tests/test_poller.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_index_status.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_measurement_scripts.py
    - docs/language-analyzers.md

key-decisions:
  - "LANGUAGES_MARK steht in index/open.py, repo.py nennt den Schluessel als Literal, genau wie heute schon fuer index_version und tantivy_version; die Saatprobe faellt rot, sobald die beiden Schreibweisen auseinanderlaufen"
  - "LEGACY_LANGUAGES ist eine eigene Konstante und kein Import von DEFAULT_LANGUAGES: sie beschreibt, was im Feld existieren KANN, und darf sich nicht mit der Werkseinstellung bewegen"
  - "_seed_meta entfernt den Schluessel aktiv (seed.pop), weil das Weglassen aus _DEFAULT_META allein nicht reicht: die Saat uebernimmt den Aufrufer-Merkersatz per seed.update"
  - "Die vier Faelle liegen in tests/test_store_repo.py und nicht in tests/test_store_metadata.py; letzteres ist das Gate fuer die App-Store-Texte"
  - "ALL_MARKS und GOLD_V1_3 sind bereits im Task-1-Commit auf sechs gehoben worden, weil das Abnahmekriterium von Task 1 (pyright gruen) die Aufrufstellen dieser Datei mitzieht"

patterns-established:
  - "Vier durchgerechnete Faelle als vier Tests mit dem Fall im Funktionsnamen, plus ein Fall-schliesst-zu-Test der Ausnahmefunktion selbst"
  - "Eine bewusst offen gelassene Luecke bekommt drei Orte: Docstring, Test mit dem Wort auf purpose im Namen, und einen Absatz in docs/"

requirements-completed: [LEX-02, LEX-04]

# Metrics
duration: 42min
completed: 2026-09-24
---

# Phase 18 Plan 05: Sechster Merker ohne Bestands-Reindex Summary

**Die Sprachmenge ist sechster Versionsmerker, sie wird niemals gesaet, und ihr Fehlen wird als Teilmenge von `("de", "en")` gelesen, sodass eine Bestandsinstallation auf Werkseinstellung oder auf reinem `de` ohne Umbau upgradet, waehrend das Einschalten von `es`, `it`, `nl` oder `pt` und auch das Abschalten einer Sprache Drift melden.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-09-24T05:32:00Z
- **Completed:** 2026-09-24T06:14:00Z
- **Tasks:** 3 (Task 2 als TDD-Zyklus)
- **Files modified:** 16 (6 Produktivmodule, 9 Testdateien, 1 Dokument)

## Accomplishments

- `expected_versions(digest, languages)` traegt sechs Marken. Der zweite Parameter wird an allen vier Produktiv-Aufrufstellen (`api/resources.py:139`, `worker/poller.py:322`, `worker/poller.py:1833`, `tools/one_load.py:265`) und in der Testfixture als `",".join(settings().languages)` gebildet; keine Stelle baut die Zeichenkette anders zusammen, und `grep -n "settings()" backend/src/findling/index/open.py` trifft weiterhin keine Zeile.
- `_languages_are_legacy(stored, expected)` steht in der Bauart von `_index_format_matches` direkt daneben, mit einem Docstring, der die Ausnahme beweist (bis 1.2.0 filterte `_languages()` gegen `DEFAULT_LANGUAGES`, also kann kein Feldbestand ein Koerperfeld ausserhalb `de,en` tragen) und die eine offen gelassene Luecke benennt.
- Der Merker wird nie gesaet, und das ist per Test belegt und nicht behauptet: nach `open_store(..., meta=expected_versions("ein-digest", "de,en,es"))` fehlt `languages` in `read_meta()`, und derselbe Aufruf meldet danach Drift genau auf diesem Merker.
- Die vier Faelle der Recherche sind vier gruene Tests mit dem Fall im Namen, dazu die Saatprobe, der Lueckentest und ein Fall-schliesst-zu-Test der Ausnahmefunktion selbst.
- `index_status` meldet `languages` als sechsten Eintrag, in `empty_report()` als leerer Wert und in `collect()` aus der `meta`-Tabelle.
- Ratsche nachgezogen: `PACKAGE_TREE_HASH_TODAY = 7b14950d...`, `PACKAGE_FILES_TODAY` bleibt 55, die Kommentarkette nennt alle sechs bewegten Module einzeln.
- Volle Suite 2630 passed / 15 skipped, alle vier Gates gruen.

## Task Commits

1. **Task 1: expected_versions bekommt die Sprachmenge als zweiten Parameter** - `df4adfb` (feat)
2. **Task 2 RED: vier Faelle, Saatprobe, Luecke** - `c56c5d3` (test)
3. **Task 2 GREEN: Teilmengenregel und Saat-Ausnahme** - `c38a7cd` (feat)
4. **Task 3: sechster Berichtseintrag, Doku, Ratsche** - `5b81fde` (feat)

## Files Created/Modified

- `backend/src/findling/index/open.py` - `LANGUAGES_MARK` neben `REBUILD_MARK` und `_LOCAL_GENERATION`, mit dem Absatz, dass der Merker die Sprachmenge des gebauten Verzeichnisses nennt und nie die gewuenschte; `expected_versions` mit zweitem Parameter und sechstem Eintrag.
- `backend/src/findling/store/repo.py` - `_LANGUAGES_MARK`, `LEGACY_LANGUAGES`, `_languages_are_legacy`, die dritte `if`-Zeile in `version_mismatch`, der Absatz ueber `_DEFAULT_META` und das `seed.pop` in `_seed_meta`.
- `backend/src/findling/tools/index_status.py` - sechster Eintrag in `_VERSION_KEYS` samt dem Satz, warum er der Nachfolger der gestorbenen Zusicherung 6 der CI-Strecke ist.
- `backend/src/findling/api/resources.py`, `worker/poller.py`, `tools/one_load.py` - die vier Aufrufstellen.
- `backend/tests/test_store_repo.py` - sieben neue Faelle (vier Faelle, Saatprobe, Luecke, Fall-schliesst-zu).
- `backend/tests/test_upgrade_compatibility.py` - `ALL_MARKS` auf sechs, `GOLD_LANGUAGES`, `GOLD_V1_3` mit `de,en`, Absatz nach `TANTIVY_PIN`-Bauart mit Datum und E-17-4; `GOLD_V1_0_AND_V1_1` unberuehrt.
- `backend/tests/test_index_status.py`, `conftest.py`, `probe_image_search.py`, `test_index_open.py`, `test_poller.py`, `test_embedding_track.py` - Aufrufstellen und der neue Berichtstest.
- `backend/tests/test_measurement_scripts.py` - Baumhash und Kommentarabsatz.
- `docs/language-analyzers.md` - die benannte Luecke ausserhalb des Docstrings, im Abschnitt ueber das Einschalten einer Sprache.

## Die vier Faelle, wie sie jetzt in der Suite stehen

| Bestand | Erwartung | Gespeichert | Verdikt | Test |
|---|---|---|---|---|
| 1.2.0, Werkseinstellung | `de,en` | fehlt | kein Drift | `test_case_one_a_1_2_0_installation_on_the_factory_setting_reports_no_drift` |
| 1.2.0, `FINDLING_LANGUAGES=de` | `de` | fehlt | kein Drift | `test_case_two_a_1_2_0_installation_pinned_to_german_reports_no_drift` |
| 1.2.0, Spanisch wird eingeschaltet | `de,en,es` | fehlt | Drift auf `languages` | `test_case_three_a_1_2_0_installation_that_switches_spanish_on_reports_drift` |
| 1.3.0, gespeichert `de,en,es` | `de,en` | `de,en,es` | Drift (Gegenlauf) | `test_case_four_switching_a_language_off_on_1_3_0_reports_drift_as_well` |

## Decisions Made

- **Der Merker wird aktiv aus der Saat geworfen, nicht nur aus `_DEFAULT_META` weggelassen.** `_seed_meta` baut `seed = dict(_DEFAULT_META)` und danach `seed.update(meta or {})`; der Aufrufer-Merkersatz enthaelt `languages`, also haette das blosse Weglassen aus `_DEFAULT_META` exakt nichts bewirkt und Pitfall 1 waere unbemerkt eingetreten. Ein `seed.pop(_LANGUAGES_MARK, None)` nach dem `update` ist der Eingriff, und die Saatprobe ist der Beweis.
- **`LANGUAGES_MARK` in `open.py`, Literal in `repo.py`.** `repo.py` kann `index/open.py` nicht importieren (die Abhaengigkeit laeuft andersherum, `open.py` importiert `Store`), und die Datei nennt `index_version` und `tantivy_version` in derselben Schleife bereits als Literal. Die Saatprobe importiert beide Seiten und faellt rot, sobald die Schreibweisen auseinanderlaufen.
- **`LEGACY_LANGUAGES` steht fuer sich.** Ein Import von `DEFAULT_LANGUAGES` wuerde die Ausnahme an dem Tag stillschweigend erweitern, an dem die Werkseinstellung sich bewegt. Ein Test haelt `set(LEGACY_LANGUAGES) == {"de", "en"}`.
- **Der bekannte Preis auf frischen Installationen mit exotischer Sprachmenge.** Eine ganz neue Installation mit `FINDLING_LANGUAGES=de,en,es` meldet beim ersten Start Drift auf `languages`, weil die Saat den Merker nicht setzt: `start_rebuild_on_drift` hebt die Generation einmal von 0 auf 1, und der erste leere Durchlauf stempelt. Das ist bewusst so: die Alternative waere genau die Saat, die den Merker fuer die Bestandsinstallation wertlos macht. Der Zustand heilt sich beim ersten `stamp_after_rebuild`, und auf einer frischen Installation gibt es nichts, was er kosten koennte.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die vier Faelle liegen in `tests/test_store_repo.py`, nicht in `tests/test_store_metadata.py`**

- **Found during:** Task 2 (vor dem Schreiben der RED-Tests)
- **Issue:** Der Plan nennt `backend/tests/test_store_metadata.py` als Ort der Tests. Diese Datei ist das Gate fuer die Texte des App-Store-Eintrags (Beschreibungen, Screenshots, Kategorien, Vokabularregel E-H2) und hat mit der `meta`-Tabelle der Zustandsdatenbank nichts zu tun. `Store.version_mismatch`, `_index_format_matches` und `_DEFAULT_META` werden in `tests/test_store_repo.py` gehalten.
- **Fix:** Die sieben Faelle stehen in `tests/test_store_repo.py`, direkt hinter den Tantivy-Ausnahmefaellen, nach deren Bauart sie gebaut sind. Die Verifikation des Plans lief ohnehin ueber beide Dateien.
- **Files modified:** backend/tests/test_store_repo.py
- **Verification:** `uv run python -m pytest -q tests/test_store_metadata.py tests/test_store_repo.py` gruen (83 + die Store-Text-Faelle).
- **Committed in:** `c56c5d3`

**2. [Rule 3 - Blocking] `ALL_MARKS` und `GOLD_V1_3` sind schon im Task-1-Commit gewandert**

- **Found during:** Task 1 (Abnahmekriterium "pyright gruen")
- **Issue:** Der Plan legt `ALL_MARKS` und `GOLD_V1_3` in Task 3, aber `test_upgrade_compatibility.py` ruft `expected_versions` an fuenf Stellen. Nach der Signaturaenderung meldet pyright dort fuenf `reportCallIssue`, und das Abnahmekriterium von Task 1 verlangt ausdruecklich gruenes pyright. Nur die Aufrufstellen nachzuziehen haette `test_no_mark_appeared_and_none_went_missing` rot hinterlassen (`tuple(marks) == ALL_MARKS` mit fuenf Eintraegen).
- **Fix:** Die Datei ist in einem Zug mitgezogen worden: Aufrufstellen, `GOLD_LANGUAGES`, `GOLD_V1_3`, `ALL_MARKS` auf sechs, der geforderte Absatz mit Datum und E-17-4 und die beiden Docstrings, die noch von fuenf Marken sprachen. `GOLD_V1_0_AND_V1_1` ist unveraendert.
- **Files modified:** backend/tests/test_upgrade_compatibility.py
- **Verification:** `uv run python -m pytest -q tests/test_upgrade_compatibility.py` 11 passed; pyright 0 errors.
- **Committed in:** `df4adfb`

**3. [Rule 1 - Bug] Der neue Berichtstest haette sich selbst widerlegt**

- **Found during:** Task 3
- **Issue:** Der erste Entwurf des `index_status`-Tests setzte den Sprachmerker ueber `_state_database(db, meta={"languages": ...})`, also ueber die Saat. Genau diese Saat ueberspringt den Schluessel seit Task 2, der Test haette den leeren Wert gelesen und waere aus dem falschen Grund rot geworden.
- **Fix:** Der Test schreibt den Merker mit `store.write_meta`, so wie `stamp_after_rebuild` es tut, mit einem Kommentar, der auf T-18-05-01 verweist.
- **Files modified:** backend/tests/test_index_status.py
- **Verification:** `uv run python -m pytest -q tests/test_index_status.py` 10 passed.
- **Committed in:** `5b81fde`

---

**Total deviations:** 3 auto-fixed (2 blockierend, 1 Fehler im eigenen Testentwurf)
**Impact on plan:** Kein Scope-Zuwachs. Die Dateiliste des Plans ist um `backend/tests/test_store_repo.py` und `backend/tests/probe_image_search.py` gewachsen und um `backend/tests/test_store_metadata.py` geschrumpft; `backend/tests/test_upgrade_compatibility.py` ist eine Aufgabe frueher bewegt worden als geplant.

## Issues Encountered

- `ruff format` hat eine Zeile der neuen Faelle umgebrochen; nachformatiert, danach alle vier Gates gruen.
- Der Ratschentest `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` war zwischen Task 1 und Task 3 erwartungsgemaess rot, weil der Baumhash erst am Ende nachgezogen wird, wenn `backend/src/` sich nicht mehr bewegt. Kein anderer Test war in dieser Zeit rot.

## Verification

- `uv run python -m pytest -q` : 2630 passed, 15 skipped
- `uv run ruff check` / `ruff format --check` / `pyright` (PYRIGHT_PYTHON_FORCE_VERSION=latest) / `vulture` : alle gruen
- `grep -rn "expected_versions(" backend/src backend/tests --include=*.py` : jede Fundstelle mit zwei Argumenten
- `grep -n "settings()" backend/src/findling/index/open.py` : keine Zeile in `expected_versions`
- Saatprobe: nach `open_store(..., meta=expected_versions("ein-digest", "de,en,es"))` fehlt `languages` in `read_meta()`, und `version_mismatch(expected) == ["languages"]`
- Baumhash-Rezept ueber `backend/src/findling`: `dateien: 55`, `baumhash: 7b14950daf877e9ba0ae03d02fae24c68c6afd5cda5dce67f47240d8dfca9d70`

## TDD Gate Compliance

Task 2 traegt `tdd="true"`. RED (`c56c5d3`) faellt mit `ImportError: cannot import name 'LEGACY_LANGUAGES'` und damit fuer die gesamte Datei, GREEN (`c38a7cd`) bringt 83 Faelle der Datei gruen. Eine REFACTOR-Stufe gab es nicht, nur einen `ruff format`-Lauf, der in den GREEN-Commit eingegangen ist. Die Gate-Reihenfolge `test(...)` vor `feat(...)` steht in der Historie.

## Known Stubs

Keine. Der Merker ist an beiden Enden verdrahtet: er wird von `expected_versions` erzeugt, von `version_mismatch` verglichen, von `stamp_after_rebuild` geschrieben und von `index_status` berichtet.

## Threat Flags

Keine neue Angriffsflaeche. Es entsteht keine Netzstrecke, kein Rechtepfad und keine Schemaaenderung an einer Vertrauensgrenze; die Driftmeldung nennt weiterhin nur Merkernamen, keine Werte und keinen Pfad (T-18-05-04 unveraendert erfuellt).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-11 kann den sichtbaren Unterschied zwischen 1.2.0 und 1.3.0 am Berichtsschluessel `languages` festmachen: in 1.2.0 gibt es ihn nicht, in 1.3.0 steht er nach dem ersten Stempel.
- Der Umbauweg (Plan 18-06 ff.) hat jetzt das Tor, das ihn ausloest: `version_mismatch` meldet `languages`, und nur die Installationen, die eine Sprache bewegt haben, laufen hinein.
- Offen und bewusst offen: die Luecke `de` nach `de,en`. Sie steht im Docstring, in einem Test und in `docs/language-analyzers.md`; wer sie schliessen will, braucht einen Owner-Entscheid, weil das Schliessen genau die Instanzen trifft, die heute nichts zahlen.

## Self-Check: PASSED

- `backend/src/findling/index/open.py` enthaelt `LANGUAGES_MARK` (gefunden)
- `backend/src/findling/store/repo.py` enthaelt `_languages_are_legacy(current, value)` in `version_mismatch` (gefunden)
- `backend/src/findling/tools/index_status.py` enthaelt den Eintrag `languages` (gefunden)
- `.planning/phases/18-schema-marken-und-umbauweg/18-05-SUMMARY.md` vorhanden
- Commits `df4adfb`, `c56c5d3`, `c38a7cd`, `5b81fde` in der Historie gefunden

---
*Phase: 18-schema-marken-und-umbauweg*
*Completed: 2026-09-24*
