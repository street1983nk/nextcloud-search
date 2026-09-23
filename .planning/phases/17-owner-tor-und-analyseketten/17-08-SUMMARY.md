---
phase: 17-owner-tor-und-analyseketten
plan: 08
subsystem: infra
tags: [tantivy, pin, uv-lock, dependabot, deploy-harp, lizenzen, reindex]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: "Plan 17-04: vollzogenes Owner-Tor, E-17-7 Option a (lockern), mit fertigen Ersatztexten je Datei"
  - phase: 17-owner-tor-und-analyseketten
    provides: "Plan 17-07: Store.version_mismatch vergleicht bei tantivy_version nur noch die index_format-Haelfte"
provides:
  - "tantivy steht auf 0.26.2, index_format v7 unveraendert, keine Bestandsinstallation reindiziert"
  - "Filter.stopword auf einer Sprache ohne eingebaute Liste wirft ValueError statt Rust-Panic"
  - "Zusicherung 2 in deploy-harp.yml haelt vier Marken fest und prueft die fuenfte auf ihre Formathaelfte"
  - "dependabot-Begruendung und THIRD-PARTY.md decken sich mit dem Messbericht vom 2026-09-23"
affects: [18, LEX-08, index-rebuild, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CI-Marke, die sich bewegen DARF: eigene Pruefung nach dem Muster von Zusicherung 6, drei Zweige (Formathaelfte gewandert = Fehler, gar nichts gewandert = unchanged, nur die Patchnummer = moved on purpose)"
    - "Berichtigter Kommentar nennt beide Daten, damit der spaetere Entscheid den frueheren abloest statt ihn zu loeschen"

key-files:
  created:
    - .planning/phases/17-owner-tor-und-analyseketten/deferred-items.md
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/tests/test_upgrade_compatibility.py
    - .github/workflows/deploy-harp.yml
    - .github/dependabot.yml
    - THIRD-PARTY.md

key-decisions:
  - "E-17-7 Option a vollzogen: Pin auf tantivy==0.26.2, GOLD_V1_0_AND_V1_1['tantivy_version'] bleibt GOLD_INDEX_FORMAT"
  - "Die falsche Formatbehauptung wird in .github/dependabot.yml nicht mehr woertlich zitiert, sondern in eigenen Worten wiedergegeben: der Ersatztext des Entscheiddokuments haette die Zeichenkette im Baum stehen lassen, die die Abnahmebedingung des Plans ausdruecklich verbietet"
  - "Der Provenienzabsatz in THIRD-PARTY.md behauptet nicht mehr, tantivys Lizenz sei nicht aus PyPI ablesbar: 0.26.2 traegt License-Expression MIT, gemessen am 2026-09-23"
  - "Der pyright: ignore in index/open.py bleibt stehen (niemand meldet ihn, und die Datei liegt in der Baumhash-Ratsche der Welle); Befund in deferred-items.md"

patterns-established:
  - "Lock-Sprung: pyproject von Hand, dann uv lock --upgrade-package <paket> und uv sync, dann den Diff LESEN, bevor irgendetwas weitergeht"
  - "Ein fertiger Ersatztext aus einem Entscheiddokument wird vor dem Einsetzen gegen die Abnahmebedingung und gegen die Wirklichkeit geprueft, nicht blind kopiert"

requirements-completed: [LEX-07]

# Metrics
duration: 40min
completed: 2026-09-23
---

# Phase 17 Plan 08: Der tantivy-Pin auf 0.26.2 Summary

**Der Pin steht auf `tantivy==0.26.2`, die volle Suite ist mit 2542 passed genauso gruen wie vorher, und alle vier Begruendungen im Baum (Test, CI-Zusicherung, dependabot, Lizenzliste) sagen jetzt dasselbe wie die Messung vom 23.09.2026.**

## Performance

- **Duration:** ca. 40 min
- **Started:** 2026-09-23
- **Completed:** 2026-09-23
- **Tasks:** 2
- **Files modified:** 6 (plus eine neue Datei fuer die zurueckgestellten Befunde)

## Accomplishments

- `backend/pyproject.toml` traegt `"tantivy==0.26.2"`; keine andere Zeile der Abhaengigkeitsliste bewegt.
- `backend/uv.lock` ausschliesslich ueber `uv lock --upgrade-package tantivy` erneuert, danach `uv sync`. Der Resolver hat genau ein Paket bewegt (`Updated tantivy v0.26.0 -> v0.26.2`, 74 Pakete aufgeloest), und der Diff umfasst 25 Zeilen in genau einem `[[package]]`-Block: `version`, `sdist`, fuenf cp313-Raeder mit sha256 und die `specifier`-Zeile. Keine Handkante.
- Die cp313t-Raeder (free-threaded) sind erwartungsgemaess entfallen; die fuenf verbliebenen cp313-Raeder decken `manylinux_2_17_aarch64`, `manylinux_2_17_x86_64`, zwei macOS-Varianten und `win_amd64` ab. Der ARM-Zielpfad bleibt bedient, musllinux gibt es in keiner der beiden Fassungen.
- `tantivy.__version__` meldet `"tantivy v0.26.2, index_format v7"`. Die Formathaelfte ist unveraendert, und genau deshalb bleibt `GOLD_V1_0_AND_V1_1["tantivy_version"]` auf `GOLD_INDEX_FORMAT`.
- Der Panic-Beweis ist gefuehrt, und zwar nicht nur fuer `romanian`, sondern fuer alle fuenf gemessenen Sprachen ohne eingebaute Stoppwortliste: `arabic`, `greek`, `romanian`, `tamil`, `turkish` werfen beim `build()` je einen `ValueError` (`No builtin stop word list for language: <name>`). Keine `PanicException`.
- `TANTIVY_PIN` steht auf `"tantivy==0.26.2"`, und der Kommentar daneben ist vom Ankuendigungstext ("der Pin wandert erst in Plan 17-08") auf einen Vollzugshinweis umgestellt: Datum, `E-17-7 Option a`, und die Feststellung, dass die Gold-Marke `"index_format v7"` bleibt und nicht mitwandert.
- Zusicherung 2 in `deploy-harp.yml` haelt vier Marken ueber `unchanged` fest; `tantivyVersion` bekommt eine eigene dreizweigige Pruefung. Alle drei Zweige sind in einer Shell gegengerechnet: 0.26.0 nach 0.26.2 meldet "moved on purpose", gleicher Banner meldet "unchanged", v7 nach v8 setzt `fail=1`.
- Der Zusammenfassungsblock nennt jetzt dieselben Marken wie der Schritt darueber. Zusicherungen 4, 5 und 6 und `UPGRADE_FROM_TAG: v1.1.0` sind im `git diff` nicht enthalten.
- Der `ignore`-Block in `.github/dependabot.yml` ist unberuehrt (`dependency-name: "tantivy"`, drei `update-types`); nur der Begruendungskommentar darueber ist neu und traegt beide Daten (2026-09-21 und 2026-09-23) sowie `E-17-7`.
- `THIRD-PARTY.md` fuehrt `tantivy` mit 0.26.2, der Provenienzabsatz ist auf Tag `0.26.2` mit Lesedatum gezogen, und die Snowball-Stoppwortlisten sind als BSD-3-Clause, einkompiliert und Herkunft der gefalteten Ergaenzungsliste benannt.
- "Union-Scorer" kommt in keinem der angefassten Artefakte vor (gegen alle sechs Dateien geprueft).

## Task Commits

1. **Task 1: Pin bewegen, Lock erneuern, volle Suite fahren** , `8f9e137` (chore)
2. **Task 2: CI-Zusicherung, dependabot-Kommentar und Lizenzliste nachziehen** , `a5581e2` (docs)

## Files Created/Modified

- `backend/pyproject.toml` , Zeile 13 von `"tantivy==0.26.0"` auf `"tantivy==0.26.2"`.
- `backend/uv.lock` , tantivy-Block auf 0.26.2 (Maschinenlauf, nicht von Hand).
- `backend/tests/test_upgrade_compatibility.py` , `TANTIVY_PIN` auf `"tantivy==0.26.2"`, Kommentar auf Vollzug umgeschrieben. `GOLD_INDEX_FORMAT`, `GOLD_V1_0_AND_V1_1`, `TANTIVY_MARK`, `WNGERMAN_PIN`, `ALL_MARKS`, `drift_findings` und alle Selbstproben unberuehrt.
- `.github/workflows/deploy-harp.yml` , Zusicherung 2 in vier Marken plus eigene `tantivyVersion`-Pruefung zerlegt, Zusammenfassungszeile nachgezogen.
- `.github/dependabot.yml` , Begruendungskommentar berichtigt, `ignore`-Block und der Absatz zu Pull Request #10 unveraendert.
- `THIRD-PARTY.md` , Tabellenzeile auf 0.26.2, Provenienzabsatz neu gelesen, Absatz zu den Snowball-Listen ergaenzt.
- `.planning/phases/17-owner-tor-und-analyseketten/deferred-items.md` , **neu**, zwei Befunde ausserhalb des Auftrags.

## Decisions Made

- **Die falsche Formatbehauptung wird nicht mehr woertlich zitiert.** Der fertige Ersatztext in `17-GRUNDSATZ-ENTSCHEID.md` gibt die widerlegte Aussage als Zitat wieder (`said "index format v7 from 0.26.2 on, which means a reindex"`). Die Abnahmebedingung desselben Plans verlangt aber ausdruecklich, dass die Zeichenkette `index format v7 from 0.26.2 on` in der Datei nicht mehr vorkommt, und das Verify-Kommando prueft genau das. Der neue Kommentar gibt die alte Behauptung deshalb in eigenen Worten wieder ("claimed that the on disk format changes to v7 with the 0.26.2 release and that a bump therefore rebuilds every index in the field"). Damit ist beides erfuellt: die falsche Zeichenkette steht nicht mehr im Baum, und T-17-35 haelt, weil der frueherer Entscheid mitsamt Datum weiterhin benannt und abgeloest statt geloescht wird.
- **`GOLD_V1_0_AND_V1_1["tantivy_version"]` wurde nicht angefasst.** Plan 17-07 hat den Wert auf `GOLD_INDEX_FORMAT` gestellt; dieser Plan hat ihn gelesen und bestaetigt.
- **Der `pyright: ignore` in `backend/src/findling/index/open.py` bleibt stehen.** Siehe Befunde unten.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Provenienzabsatz in `THIRD-PARTY.md` behauptete etwas, das fuer 0.26.2 nicht mehr stimmt**

- **Found during:** Task 2 c), beim Pruefen des fertigen Ersatztexts gegen das installierte Rad.
- **Issue:** Der Ersatztext aus `17-GRUNDSATZ-ENTSCHEID.md` uebernimmt den Satz, tantivy sei "the one entry whose licence is **not** readable from its PyPI metadata: the 0.26.2 release carries neither a `license` field nor a licence classifier". Gemessen am 2026-09-23 an `.venv/Lib/site-packages/tantivy-0.26.2.dist-info/METADATA` ist das fuer 0.26.2 falsch: die Metadaten tragen `License-Expression: MIT` und `License-File: LICENSE`, und der MIT-Text liegt als `licenses/LICENSE` im `dist-info`. Nur Lizenz-Classifier fehlen weiterhin (`grep -c "^Classifier:"` ergibt 0). Woertlich eingesetzt haette der Ersatztext eine widerlegte Begruendung in den Baum geschrieben, also genau das, was das Erfolgskriterium dieses Plans verbietet.
- **Fix:** Der Absatz ist in die Vergangenheitsform gesetzt (0.26.0 trug weder Feld noch Classifier) und um die Messung von 0.26.2 ergaenzt: `License-Expression: MIT`, mitgelieferter Lizenztext, Classifier weiterhin abwesend. Die Aussage ueber den Upstream-Tag bleibt, mit `0.26.2` und Lesedatum. Der Absatz begruendet jetzt zusaetzlich, warum er stehen bleibt: als Gedaechtnis fuer Leser eines aelteren Images.
- **Files modified:** `THIRD-PARTY.md`
- **Verification:** `grep -q '| \`tantivy\` | 0.26.2 |' THIRD-PARTY.md` gruen; die Messung ist im Absatz datiert.
- **Committed in:** `a5581e2`

### Zurueckgestellt (ausserhalb des Auftrags)

Beide in `.planning/phases/17-owner-tor-und-analyseketten/deferred-items.md`:

1. **Der `pyright: ignore` an `TANTIVY_VERSION` ist sachlich ueberfluessig geworden.** `tantivy/tantivy.pyi` deklariert in 0.26.2 `__version__: str` (Zeile 714), und der Kommentar darueber in `backend/src/findling/index/open.py` begruendet die Unterdrueckung noch mit dem fehlenden Stub von 0.26.0. Der Plan knuepft die Entfernung daran, dass ein Werkzeug den Kommentar meldet. Es meldet ihn keines: `ruff check` ist ohne Befund, und `pyright` laeuft mit `typeCheckingMode = "basic"`, wo `reportUnnecessaryTypeIgnoreComment` aus ist. Dazu kommt die Auflage dieser Welle, `backend/src/findling/` nicht anzufassen, weil sonst `PACKAGE_TREE_HASH_TODAY` in `backend/tests/test_measurement_scripts.py` mitwandert. Beide Gruende zeigen in dieselbe Richtung: stehen lassen, in einer spaeteren Phase zusammen mit einer ohnehin faelligen Aenderung an den Paketquellen erledigen.
2. **Drei Versionsangaben in `THIRD-PARTY.md` sind aelter als ihr Pin** (`pypdf` 6.16.1 gegen 6.19.0, `striprtf` 0.0.32 gegen 0.0.33, `lxml` 6.1.1 gegen 6.1.3). Vorbestehend, ohne Bezug zum tantivy-Sprung, und dieser Plan fasst in der Tabelle nur die tantivy-Zeile an.

---

**Total deviations:** 1 auto-fixed (1 Bug), 2 zurueckgestellt
**Impact on plan:** Kein Scope-Zuwachs. Die eine Abweichung ersetzt eine widerlegte Begruendung durch die gemessene, was das Erfolgskriterium des Plans verlangt, statt ihm zu widersprechen.

## Issues Encountered

- Der Lauf der vollen Suite nach Schritt 3 war erwartungsgemaess **einmal rot**, und zwar an genau einer Stelle: `test_the_engine_is_held_through_its_exact_pin` (`AssertionError: tantivy==0.26.0`), weil der Plan den Lock vor dem Testpin bewegt. Alles andere war bereits mit 0.26.2 gruen, 2541 passed. Das ist der eigentliche Beleg fuer die Lockerung aus Plan 17-07: die Ratsche `test_upgrade_compatibility.py` und `test_index_open.py` haben den bewegten Pin ohne Anpassung ueberstanden. Nach Schritt 5 stand die Suite wieder bei 2542 passed, also exakt auf dem Stand der Basis.
- Der Worktree hatte keine `.venv`; `uv sync` hat sie neu gebaut. Das erklaert die lange Ausgabe des Sync-Laufs und hat nichts mit dem Pin zu tun.

## Verification

- `uv lock --upgrade-package tantivy` , `Resolved 74 packages`, `Updated tantivy v0.26.0 -> v0.26.2`
- `git diff --name-only -- backend/uv.lock | wc -l` , **1**
- `git diff -U0 -- backend/uv.lock | grep -c '^[+-][^+-]'` , **25** (Grenze des Plans: 80)
- `uv run python -c "... tantivy.__version__ ... Filter.stopword ..."` , `'tantivy v0.26.2, index_format v7'`, fuenfmal `ValueError`, `GRUEN`
- `uv run python -m pytest -q` aus `backend/` , **2542 passed, 15 skipped** (Basis: 2542/15)
- `uv run python -m pytest tests/test_lockstep_versions.py tests/test_upgrade_compatibility.py tests/test_index_open.py tests/test_search_fields_lockstep.py -q` , **80 passed**
- `uv run ruff check` , All checks passed
- `uv run ruff format --check` , 129 files already formatted
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` , 0 errors, 0 warnings, 0 informations
- `uv run vulture` , keine Ausgabe, rc=0
- `yaml.safe_load` auf `deploy-harp.yml` und `dependabot.yml` , `YAML ok`
- Alle neun Greps der Abnahme von Task 2 , gruen, inklusive `! grep -q "index format v7 from 0.26.2 on" .github/dependabot.yml`
- `grep -rn "Union-Scorer"` ueber alle sechs Dateien , keine Treffer
- `grep -n "UPGRADE_FROM_TAG:" .github/workflows/deploy-harp.yml` , `v1.1.0`, unveraendert
- `git diff` des Workflows , Zusicherungen 4, 5 und 6 nicht enthalten
- Die drei Zweige der neuen `tantivyVersion`-Pruefung in einer Shell gegengerechnet , "moved on purpose", "unchanged", Fehlerzweig

## Known Stubs

Keine.

## Threat Flags

Keine. Der Sprung beruehrt keinen Datenpfad, keine Route und keine Ausgabe; `T-17-36` ist im Threat Register bereits als `accept` gefuehrt. `T-17-SC` haelt: kein neuer Paketname, `uv lock --upgrade-package` statt eines frei getippten Namens, und die fuenf neuen Rad-Hashes stehen im gelesenen Diff.

## User Setup Required

Keine.

## Next Phase Readiness

- Der Lauf von `deploy-harp.yml` nach dem Merge ist die letzte offene Zusicherung dieses Plans. Der Job "Store upgrade 5" muss kein Reindex-Banner und keine Zeile "built by different code" melden, und Zusicherung 2 sollte `moved on purpose .marks.tantivyVersion tantivy v0.26.0, index_format v7 to tantivy v0.26.2, index_format v7` ausgeben. **Die Laufnummer gehoert nach dem Merge in den Vollzugsabschnitt von `17-GRUNDSATZ-ENTSCHEID.md`**; sie kann aus einem Worktree heraus nicht beschafft werden.
- `UPGRADE_FROM_TAG` steht weiterhin auf `v1.1.0`. Die Hebung auf `v1.2.0` ist LEX-08 und Zusage von Phase 18.
- Phase 18 kann `Index.is_compatible()` aus 0.26.2 benutzen; es prueft das Schema nicht mit, das bleibt Aufgabe der Marken.
- Erwartbare Konfliktstelle beim Merge dieser Welle: `PACKAGE_TREE_HASH_TODAY` in `backend/tests/test_measurement_scripts.py`. Dieser Plan hat sie **nicht** bewegt, weil er keine Datei unter `backend/src/findling/` angefasst hat.

---
*Phase: 17-owner-tor-und-analyseketten*
*Completed: 2026-09-23*

## Self-Check: PASSED

- Alle sechs geaenderten Dateien, die neue `deferred-items.md` und diese SUMMARY liegen auf der Platte.
- Beide Task-Commits (`8f9e137`, `a5581e2`) stehen in der Historie des Worktree-Branches, aufgesetzt auf `bb6dfbc`.
- `STATE.md` und `ROADMAP.md` sind nicht angefasst; der Orchestrator schreibt sie nach dem Merge der Welle.
