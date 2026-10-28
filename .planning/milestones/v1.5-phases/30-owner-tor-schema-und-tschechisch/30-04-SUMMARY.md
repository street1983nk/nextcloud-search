---
phase: 30-owner-tor-schema-und-tschechisch
plan: 04
subsystem: index/config (Schema, Sprachen, Marken)
tags: [schema, cz-02, cz-01, d-30-08, gold, ratchet]
requires: [30-01, 30-02, 30-03]
provides:
  - "SUPPORTED_LANGUAGES mit cs am Ende, STEMMERLESS_LANGUAGES = {cs}, TESSERACT_NAME[cs] = ces"
  - "FIELD_BODY_CS, FIELDS mit 14 Namen, BODY_FIELD[cs]"
  - "open_index registriert neun Ketten unbedingt, darunter czech_analyzer()"
  - "BODY_BOOST[cs] = 0.6"
  - "SCHEMA_VERSION = 3, GOLD_V1_5 neben GOLD_V1_3 und GOLD_V1_0_AND_V1_1"
affects: [30-05 Umbau an/aus, 30-06 Upgrade-Ausgang v1.4.2, 30-07 Store upgrade 6/7]
tech-stack:
  added: []
  patterns: ["zwei disjunkte Kettenarten (Snowball, stemmerlos) decken SUPPORTED_LANGUAGES exakt", "historische Erwartung liest die Zeugentabelle, nicht den Code"]
key-files:
  created: []
  modified:
    - backend/src/findling/config.py
    - backend/src/findling/index/schema.py
    - backend/src/findling/index/open.py
    - backend/src/findling/query/rewrite.py
    - backend/tests/test_language_allowlist.py
    - backend/tests/test_index_open.py
    - backend/tests/test_schema_generations.py
    - backend/tests/test_field_plan_ranking.py
    - backend/tests/test_upgrade_compatibility.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_upgrade_seed_steps.py
    - backend/tests/test_v13_ablauf.py
    - .github/workflows/deploy-harp.yml
decisions:
  - "STEMMERLESS_LANGUAGES ohne Final, wie alle Konstanten in config.py (Final ist dort nicht importiert)"
  - "Store upgrade 6 Zusicherung 1 schon in 30-04 auf 2 vorher, 3 nachher gedreht (Pitfall 8), weil der Stolperdraht-Test den Schemasprung sofort rot meldet"
  - "test_v13_ablauf E1 liest die Schemazahl aus GOLD_V1_3, die Fahrt ist gelaufen und 00-ablauf.md darf nach der Messung nicht angepasst werden"
metrics:
  duration: "ca. 40 min (davon 3 x ca. 10 min volle Suite)"
  completed: 2026-10-10
  tasks: 3
  files: 14
---

# Phase 30 Plan 04: Schemaschritt body_cs und Sprache cs Summary

`cs` ist die siebte Produktsprache (am Ende von `SUPPORTED_LANGUAGES`, außerhalb von Snowball über `STEMMERLESS_LANGUAGES`), `body_cs` ist das vierzehnte Feld (`stored=False`, Kette `cs`), `open_index` registriert neun Ketten unbedingt, und `SCHEMA_VERSION` steht mit `GOLD_V1_5` und Owner-Begründung (D-30-02, D-30-08) auf 3. Das ist der einzige Schemaschritt von v1.5.

## Ergebnis

- Task 1: Allowlist-Parität `set(SUPPORTED_LANGUAGES) == set(SNOWBALL_NAME) | STEMMERLESS_LANGUAGES`, disjunkt; `STEMMERLESS_LANGUAGES` disjunkt zu `LANGUAGE_ALLOWLIST`, kein `"czech"` in config.py (grep = 0). `FINDLING_LANGUAGES=cs,de` -> `("de","cs")`, `de,en` bleibt `("de","en")`. `TESSERACT_NAME["cs"] = "ces"`.
- `grep "SNOWBALL_NAME\["` in src: nur feste Schlüssel (`es`, `it`, `nl`, `pt`), keine Schleife über `SUPPORTED_LANGUAGES` indiziert `SNOWBALL_NAME[code]`. Kein Fund.
- Task 2: 14 Felder, `tuple(BODY_FIELD) == (de,en,es,it,nl,pt,cs)`; `body_cs` in `meta.json` mit `stored: false`, Tokenizer `cs`; `smlouvě` trifft `smlouve` und `rizeni`, `smlouva` nicht (CZ-03-Grenze). Neun `register_tokenizer` außerhalb von Kommentaren, keiner unter `ast.If`; Schreibtest unter `FINDLING_LANGUAGES=de` grün. `FIELDS - FIELDS_SCHEMA_2 == {body_cs}`. `BODY_BOOST["cs"] == 0.6`.
- Task 3: `SCHEMA_VERSION = 3` mit Begründungskommentar. `GOLD_V1_5` neben den unveränderten Tabellen (git diff entfernt keine Goldzeile), Absatz zitiert D-30-02, D-30-08, 30-CONTEXT "Folge für Phase 30", LEGACY_SCHEMA_STEPS ("2","3") und "Store upgrade 5". Neu: Ein-Stufen-Test `GOLD_V1_3 -> GOLD_V1_5` über alle Marken, "Upgrade von 1.3.x/1.4.x bewegt genau die Schemamarke", "dieser Code trägt die Marken von v1.5". `ALL_MARKS` bleibt bei sieben.
- Baumhash: Task 1+2 `73ad4fc4...717f`, Task 3 `89d7a5f8...a321`; `PACKAGE_FILES_TODAY` bleibt 74; je ein Journalabsatz.
- Gates: ruff, ruff format, pyright (latest) 0 Fehler, vulture grün. Volle Suite nach Task 1+2: 4751 passed / 25 skipped; nach Task 3: 4753 passed / 25 skipped. Skipzahl gegen vor dem Plan (25) unverändert.

## TDD-Belege

- Task 1 RED (da83fa8f): Lauf scheitert am Import `STEMMERLESS_LANGUAGES`. Gegenprobe mit nur der Konstante als Stub (ohne `cs` in `SUPPORTED_LANGUAGES`): Parität, `cs,de`, `de,cs`, `cs` und Sieben-Sprachen-Fall einzeln rot (5 failed); `de,en` grün (Regression, soll grün bleiben). Der Disjunktheitswächter wurde per Mutation (`"cs": "czech"` in `SNOWBALL_NAME`) rot gesehen.
- Task 2 RED (4fc6d8ad): Lauf scheitert am Import. Gegenprobe mit Stubs `STEMMERLESS_LANGUAGES` und `FIELD_BODY_CS` (ohne Feld, Registrierung, Gewicht): alle acht neuen bzw. geänderten Fälle einzeln rot.
- Task 3 RED (1af56eb0): drei Fälle rot gegen `SCHEMA_VERSION = 2`. Der reine Goldtabellen-Fall (Ein-Stufen-Test) wurde per Mutation rot gesehen: Schema "4" (Schritt 2) und Sprachmarke `de,en,cs` je einzeln.
- Alle Stubs und Mutationen wurden zurückgedreht, nichts davon ist committet.

## Commits

| Commit | Inhalt |
|---|---|
| da83fa8f | test(30-04): RED cs als stemmerlose Produktsprache |
| 4fc6d8ad | test(30-04): RED body_cs, neun Registrierungen, Gewicht cs |
| ffa9ba34 | feat(30-04): GREEN Task 1+2, Baumhash |
| 1af56eb0 | test(30-04): RED Goldfälle Schemamarke 3 |
| 068d0c55 | feat(30-04): SCHEMA_VERSION 3, Store upgrade 6, Baumhash |

Nicht gepusht (Plan verlangt kein CI).

## Deviations from Plan

**1. [Rule 3 - Testpflege] test_field_plan_ranking.py fortgeschrieben (nicht in der Dateiliste)**
- `BUILD_OUT` leitet sich aus `SUPPORTED_LANGUAGES` ab und enthält jetzt `cs`. `checked == 64` -> `160` (5 x 2^(7-2)); der Erreichbarkeitsfall trägt `"cs": []` (ohne Stemmer erreicht die Kette weder `documents` noch `documento`, die Drei-gegen-drei-Aufteilung bleibt). Der neue Fall zum Gewicht `cs` steht ebenfalls dort. `TIPPING_BOOST` 0.81 hält unverändert.

**2. [Rule 3 - Stolperdraht] Store upgrade 6 Zusicherung 1 auf "2 vorher, 3 nachher" (deploy-harp.yml)**
- `test_the_rebuild_step_demands_the_schema_of_the_running_code` ist ausdrücklich so gebaut, dass ein Schemasprung ihn rot macht. Die Zusicherung und die Zusammenfassungszeile von Store upgrade 6 wurden auf 2 vor und 3 nach dem Umbau gedreht, der Test auf `SCHEMA_VERSION == 3` und die neue Bedingung. Das ist der Pitfall-8-Punkt aus 30-07; **für 30-07 erledigt**, dort bleibt nur der cs-spezifische Teil (REBUILD_LANGUAGES `cs,de`, `smlouve`, Store upgrade 7).

**3. [Rule 1 - Test] test_v13_ablauf E1 band historische Erwartung an den laufenden Code**
- `00-ablauf.md` Abschnitt 3 verbietet, die Erwartung nach der Messung anzupassen, und die v1.3-Fahrt ist gelaufen. Der Test liest die Schemazahl jetzt aus `GOLD_V1_3["schema_version"]` (Zeuge von Schema 2) statt aus `SCHEMA_VERSION`; Skript und Ablaufplan bleiben unverändert.

**4. [Testpflege] test_index_rebuild.py** `== "2"` -> `"3"` (beschreibt das aktuelle Schema, Pitfall 9).

**5. [Testpflege] test_schema_generations.py** Der Fall "die Körperfelder des Ausbaus fehlen im alten Schema" beschreibt den Schritt 1 -> 2 und liest jetzt `FIELDS_SCHEMA_2` statt `FIELDS`.

**6. Konvention** `STEMMERLESS_LANGUAGES` ohne `Final`-Annotation, weil config.py `Final` nirgends nutzt und nicht importiert.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-30-15 (Filter gegen geschlossenes `SUPPORTED_LANGUAGES`, Normalisierungsfälle), T-30-16 (AST-Wächter neun Aufrufe, Selbstprobe grün), T-30-17 (Disjunktheitstest), T-30-18 (`GOLD_V1_5` mit Zitat, alte Tabellen bleiben, Ein-Stufen-Test) durch die Tests oben abgedeckt.

## Self-Check: PASSED

- Commits da83fa8f, 4fc6d8ad, ffa9ba34, 1af56eb0, 068d0c55 im Log
- `SCHEMA_VERSION = 3`, `STEMMERLESS_LANGUAGES`, `"cs": "ces"` in config.py; `FIELD_BODY_CS` in schema.py; `register_tokenizer(TOKENIZER_CS, czech_analyzer())` in open.py; `"cs": 0.6` in rewrite.py; `GOLD_V1_5` in test_upgrade_compatibility.py
