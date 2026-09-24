---
status: awaiting_human_verify
trigger: "deploy-harp run 35989391950, Job stable34/ubuntu-24.04, Block 'Store upgrade 5': Upgrade v1.2.0 -> HEAD auf Bestandsinstallation (de,en) loest start_rebuild_on_drift aus (Generation 1->2, Reindex-Banner true) und marks.languages wird '' statt abwesend/de,en"
created: 2026-09-24
updated: 2026-09-24
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "expected_versions() liefert schema_version='2' (18-01 hob config.SCHEMA_VERSION auf 2), ein v1.2.0-Bestand hat '1' gespeichert, und Store.version_mismatch vergleicht schema_version exakt. Damit meldet der Bestand Drift auf genau einer Marke, start_rebuild_on_drift hebt die Generation und das Reindex-Banner geht an. Die languages-Marke ist unbeteiligt: sie fehlt und wird als legacy entschuldigt."
  confirming_evidence:
    - "Reproduktionslauf (/tmp/repro_check.py, uv run): version_mismatch == ['schema_version'], start_rebuild_on_drift == 2, Generation 1->2, Warnzeile wortgleich mit der CI"
    - "config.py:49 SCHEMA_VERSION = 2; open.py:187 'schema_version': str(SCHEMA_VERSION); repo.py:716-721 kennt nur drei Ausnahmen (index_version, tantivy_version, languages)"
    - "18-RESEARCH.md Zeile 884: 'Ein Upgrade 1.2.0 auf 1.3.0 mit Werkseinstellung de,en bewegt keine der fuenf Marken, weil schema_version erst nach einem Umbau gestempelt wird'"
    - "rebuild.py:760 stamp_after_swap schreibt schema_version erst nach dem Tausch; rebuild.py:185 MARKS_A_REBUILD_ANSWERS enthaelt schema_version, also startet heute sogar der Umbau auf einer Werksinstallation"
  falsification_test: "Wenn version_mismatch fuer einen Schema-1-Bestand etwas anderes als ['schema_version'] meldet, ist die Hypothese falsch"
  fix_rationale: "Vierte benannte Ausnahme in version_mismatch: ein Schema-1-Verzeichnis traegt jedes Feld, das dieser Code abfragt (set(DEFAULT_FIELDS) <= set(FIELDS_SCHEMA_1), test_schema_generations.py), also ist die gespeicherte 1 gegen die erwartete 2 keine Drift, sondern der designierte Zwischenzustand bis zum Stempel nach dem Umbau"
  blind_spots: "Ob eine kuenftige Schemastufe 3 die Ausnahme still mitnimmt (dagegen: Paarkonstante statt Zahlenvergleich); ob ein anderer Leser als version_mismatch auf schema_version==2 besteht (geprueft: nur rebuild.MARKS_A_REBUILD_ANSWERS und tools/index_status)"

next_action: Owner-Bestaetigung durch einen deploy-harp-Lauf auf diesem Stand (Block 'Store upgrade 5' und 'Store upgrade 6' gruen)

## Symptoms

expected: Upgrade v1.2.0 -> HEAD auf Bestandsinstallation mit Werkssprachen de,en: KEIN Reindex, KEIN Banner, Marken unbewegt bis auf die neu erlaubte Abwesenheit der languages-Marke
actual: |
  1. "WARNING:findling.index.open:the index was built by different code; raised the generation to 2 so the next crawl rebuilds it"
  2. indexVersion 1 -> 2, Reindex-Banner true
  3. marks.languages: vor dem Upgrade null, nach dem Upgrade "" (Leerstring)
  4. schemaVersion blieb 1
errors: "the index was built by different code; raised the generation to 2 so the next crawl rebuilds it"
reproduction: deploy-harp Workflow, Job stable34/ubuntu-24.04, Block "Store upgrade 5"
started: nach Phase 18 (SCHEMA_VERSION-Hebung in 18-01)

## Eliminated

- hypothesis: "H2 Produktfehler: irgendwer schreibt die languages-Marke als Leerstring in state.db (Saat, Stempel, Driftpfad)"
  evidence: "Reproduktionslauf: 'languages' in store.read_meta() ist False nach open_store(meta=expected) und nach start_rebuild_on_drift. Der Leerstring entsteht erst im Bericht: tools/index_status.py:154 report[name] = meta.get(key, _NO_VALUE) mit _NO_VALUE = ''. jq -r liest deshalb vor dem Upgrade 'null' (Schluessel gibt es in 1.2.0 nicht) und danach '' (Schluessel da, Wert leer). Kein Produktfehler."
  timestamp: 2026-09-24

## Evidence

- timestamp: 2026-09-24
  checked: backend/src/findling/config.py:40-54
  found: "SCHEMA_VERSION = 2 seit 18-01, INDEX_VERSION = 1"
  implication: expected_versions liefert schema_version='2' fuer jede Instanz, auch fuer eine mit Schema-1-Verzeichnis

- timestamp: 2026-09-24
  checked: backend/src/findling/store/repo.py:712-723 (version_mismatch)
  found: "drei benannte Ausnahmen: index_version (Boden), tantivy_version (Formathaelfte), languages (Teilmenge). schema_version wird exakt verglichen."
  implication: Ein Bestandsindex mit Schema 1 meldet zwangslaeufig Drift

- timestamp: 2026-09-24
  checked: Reproduktionslauf mit einer nachgebauten v1.2.0-meta-Tabelle
  found: "version_mismatch == ['schema_version']; start_rebuild_on_drift == 2; Generation 1->2; Warnzeile wortgleich; 'languages' nicht in read_meta()"
  implication: Wurzel belegt, genau eine Marke, und die languages-Marke ist unbeteiligt

- timestamp: 2026-09-24
  checked: backend/src/findling/index/rebuild.py:185, 760, 844
  found: "MARKS_A_REBUILD_ANSWERS = {schema_version, languages}; stamp_after_swap schreibt schema_version erst nach dem Tausch"
  implication: Dieselbe Wurzel wuerde auch den Umbau auf einer Werksinstallation ausloesen, nicht nur die Generationshebung

- timestamp: 2026-09-24
  checked: backend/tests/test_schema_generations.py, backend/tests/conftest.py:195-262
  found: "set(DEFAULT_FIELDS) <= set(FIELDS_SCHEMA_1) ist bewiesen; die Fixtur build_schema_1/open_schema_1_index existiert"
  implication: Ein Schema-1-Verzeichnis ist unter diesem Code voll abfragbar, die gespeicherte 1 ist kein Mangel, sondern die Wahrheit ueber die Platte

- timestamp: 2026-09-24
  checked: .github/workflows/deploy-harp.yml Zusicherung 6 (Zeile 3541-3564)
  found: "verlangt was=='null' und now=='de,en'"
  implication: Die Erwartung 'de,en' widerspricht dem Entwurf 'der Merker wird nie gesaet und erst nach einem Umbau gestempelt'. Der sichtbare Unterschied 1.2.0 gegen 1.3.0 ist null gegen Leerstring.

## Resolution

root_cause: "expected_versions() behauptet schema_version=2 fuer jede Instanz, waehrend das Verzeichnis einer Bestandsinstallation weiter Schema 1 traegt (Index.open liest das persistierte Schema, build_schema() laeuft dort nie). Store.version_mismatch vergleicht diese Marke exakt und kennt keine Legacy-Ausnahme, also meldet jeder v1.2.0-Bestand Drift auf schema_version, start_rebuild_on_drift hebt die Generation und das Reindex-Banner geht an. Der Entwurf sah vor, dass schema_version erst nach dem Umbau gestempelt wird und der Umbau ohne Sprachwechsel gar nicht startet."
fix: |
  1. backend/src/findling/store/repo.py: vierte benannte Ausnahme _schema_is_legacy neben
     _generation_at_least, _index_format_matches und _languages_are_legacy, dazu _SCHEMA_MARK
     und LEGACY_SCHEMA_STEPS (Paartabelle {("1","2")}, keine Zahlenvergleichsregel, damit eine
     kuenftige Stufe 3 die Ausnahme nicht erbt). Ein fehlender oder unbekannter Merker bleibt Drift.
  2. Zwei Testfixturen, die die Schema-Marke als Driftausloeser missbrauchten, staffeln jetzt die
     Drift, um die es in Phase 18 wirklich geht (gespeicherte Sprachmenge ungleich aktiver Menge):
     _a_volume_that_asks_for_a_rebuild in test_index_rebuild.py und der Drifthelfer in
     test_main_lifespan.py. Disk-Vorpruefung unveraendert (_new_language_count bleibt 0).
  3. .github/workflows/deploy-harp.yml, Zusicherung 6: verlangt nicht mehr "de,en" nach dem
     Upgrade, sondern den sichtbaren Unterschied, den es wirklich gibt: Schluessel fehlt in
     1.2.0 (jq -r -> "null"), Schluessel vorhanden und leer in 1.3.0 (jq -r -> ""). Ein WERT
     ist jetzt der Fehlerfall. Keine Zusicherung entfernt oder entschaerft.
  4. docs/language-analyzers.md: Absatz "The schema mark of an unchanged installation stays at 1".
  5. Ratsche: PACKAGE_TREE_HASH_TODAY auf 6063f7ca..., PACKAGE_FILES_TODAY bleibt 56.
verification: |
  - RED zuerst: test_a_stock_volume_of_1_2_0_arrives_without_a_rebuild war auf dem Stand vor dem Fix
    rot mit exakt der CI-Beobachtung (version_mismatch == ['schema_version'], Generation 1->2,
    Warnzeile wortgleich). Commit 8ab77c5.
  - GREEN danach, und die vier Faelle aus 18-05 bleiben gruen: Fall 3 (Spanisch an) und Fall 4
    (Sprache aus) melden weiter Drift, belegt durch
    test_the_same_volume_still_rebuilds_when_a_language_is_switched_on und die restaged Fixturen.
  - Volle Suite: 2719 passed, 15 skipped (235 s).
  - Gates: ruff check All checks passed, ruff format 133 files already formatted,
    pyright 0 errors 0 warnings, vulture ohne Befund.
  - Unabhaengige Gegenprobe ausserhalb der Suite: nachgebaute v1.2.0-meta-Tabelle meldet jetzt
    mismatch [] und start_rebuild_on_drift None, Generation bleibt 1.
files_changed:
  - backend/src/findling/store/repo.py
  - backend/tests/test_index_open.py
  - backend/tests/test_store_repo.py
  - backend/tests/test_index_rebuild.py
  - backend/tests/test_main_lifespan.py
  - backend/tests/test_measurement_scripts.py
  - .github/workflows/deploy-harp.yml
  - docs/language-analyzers.md

---
**VERIFIED 24.09.2026:** deploy-harp-Lauf 36006893151 GRUEN auf allen vier
Matrix-Aesten. "Store upgrade 5" haelt alle sechs Zusicherungen (Bestand
unberuehrt, languages-Marke legitim abwesend), "Store upgrade 6" alle neun
(Umbau beobachtet, Schema genau eine Stufe, Sprachmarke de,en,es,
Vektorbestand byteidentisch). Beide Wurzelursachen bestaetigt behoben.
