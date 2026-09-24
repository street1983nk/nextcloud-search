---
phase: 18-schema-marken-und-umbauweg
verified: 2026-09-24T14:14:23Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 18: Schema, Marken und Umbauweg Verification Report

**Phase Goal:** Ein Bestandsindex wandert per Re-Analyse in das neue Sechs-Felder-Schema, ohne Download, ohne OCR, ohne Neu-Einbettung, und CI beweist den Weg in beide Richtungen.
**Verified:** 2026-09-24T14:14:23Z
**Status:** passed
**Re-verification:** Nein, erste Verifikation

## Vorgehen

Diese Verifikation ist AM CODE erfolgt, nicht an den zwoelf SUMMARY.md-Dateien. Fuer jedes der fuenf Roadmap-Erfolgskriterien wurde der Quellcode gelesen, die Testsuite ausgefuehrt und der genannte CI-Lauf ueber `gh run view` unabhaengig abgefragt.

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Bestandsinstallation mit `de,en` findet nach dem Upgrade dieselben Dokumente, kein Zwischenzustand laeuft leer, Migration im Lockstep vorhanden | VERIFIED | `backend/src/findling/store/repo.py:1431-1462` `_schema_is_legacy`/`LEGACY_SCHEMA_STEPS = frozenset({("1","2")})` als vierte benannte Ausnahme in `version_mismatch`; Wurzelursache und Fix dokumentiert in `.planning/debug/upgrade5-schema-drift-languages.md`, GRUEN bestaetigt durch CI-Lauf 36006893151 (`gh run view` unabhaengig abgefragt: alle 4 Matrix-Jobs "success"). Migration `php/lib/Migration/Version001300Date20260924000000.php` vorhanden, `postSchemaChange` loescht `KEY_BACKEND_VERSION`, doppellaufsicher (Guard bei leerem Wert). Datum 24.09. statt der im Plan-Frontmatter vorgeschlagenen 25.09. ist eine dokumentierte, im SUMMARY begruendete Abweichung (Anlegedatum statt Planvorschlag, wie bei den beiden Vorgaengermigrationen). |
| 2 | Re-Analyse-Umbau aus gespeicherten Feldern, wiederaufnahmefaehig, `vectors.db`/`state.db` unberuehrt, Fortschritt im Banner, kein `occ findling:index --restart` | VERIFIED | `backend/src/findling/index/rebuild.py` (927 Zeilen): `transfer_documents()` (Z.438), `_resume_cursor()` (Z.377, liest den hoechsten bereits kopierten `file_id` aus dem Zielindex selbst, kein separater Zustand in state.db), `rebuild_the_index()` (Z.784) fuehrt Vorpruefung/Ruhigstellen/Bandlauf/Tausch/Stempel in fester Reihenfolge. `main.py` haelt eine vierte Lifespan-Aufgabe (`_rebuild_the_index_directory`, Z.427, `asyncio.create_task` Z.693) mit `REBUILD_STOP_SECONDS`. `php/templates/admin.php` Z.316-322 traegt `id => 'findling-banner-rebuild'` mit Text "...there is nothing to start or to restart" (bewusst kein Kommando genannt, Kommentar Z.307-315 erklaert warum). CI "Store upgrade 6" (neun Zusicherungen) GRUEN in Lauf 36006893151, inkl. Assurance 9 (`vectors.db` byte-fuer-byte identisch, Z.4277-4280, mit explizitem Schutz gegen Vergleich zweier Abwesenheiten Z.3797). |
| 3 | Platzpruefung vor Start, Ruecklauf auf Vollreindex benannt und ausloesbar | VERIFIED | `may_rebuild()` (rebuild.py Z.224) liefert `RebuildVerdict` mit `NOT_ENOUGH_ROOM`/`ROOM_ENOUGH`. `config.py` Z.1180-1196 `_rebuild_fallback()` liest `FINDLING_REBUILD_FALLBACK`, `FULL_REINDEX_FALLBACK = "fullreindex"`; `rebuild.py:849` prueft `resolved.rebuild_fallback == FULL_REINDEX_FALLBACK` -- der Rueckfall ist im Code verdrahtet, nicht nur dokumentiert. Banner `findling-banner-rebuild-space` (admin.php Z.328-334) nennt die fehlende Bytezahl ueber `$size($rebuildBlockedBytes)` und die Umgebungsvariable im Text; Uebersetzungen in de/fr vorhanden. |
| 4 | Diagnose zeigt aktive/befuellte Sprachen, OCR-Startwarnung, sechster Merker in `expected_versions()` | VERIFIED | `api/status.py`: `languagesActive` (Z.196,299), `languagesFilled` (Z.202,300, hinter `FILLED_TTL_SECONDS=30` in `resources.py:96/466-505`). `main.py:498` OCR-Startwarnung ("carries N language(s) that FINDLING_OCR_LANGUAGES does not cover"). `store/repo.py` `_languages_are_legacy` (Z.768, Z.1465) als eigene Ausnahme neben `_schema_is_legacy`; die languages-Marke ist auf Bestand legitim abwesend bis zum ersten Umbau (SEMANTIK korrekt umgesetzt, kein Fehler). |
| 5 | CI beweist beide Richtungen, Sprachfaelle auf Feldebene | VERIFIED | `.github/workflows/deploy-harp.yml`: `UPGRADE_FROM_TAG: v1.2.0` (Z.113), "Store upgrade 5" (sechs Zusicherungen, Z.3527) UND "Store upgrade 6" (neun Zusicherungen, Z.3736) beide vorhanden und beide GRUEN in Lauf 36006893151 auf allen vier Matrix-Aesten. `backend/tests/test_language_cases_field_level.py`: 36 Tests via `pytest --collect-only` bestaetigt (4 Sprachen x 9 Parametrisierungen), alle 36 GRUEN bei eigenem Testlauf; it-Sonderfall (keine trennbare Formfamilie, nur Akzentpaare) explizit im Modulkopf dokumentiert und durch `test_the_fixture_of_a_folded_language_offers_no_such_pair` abgesichert. |

**Score:** 5/5 Erfolgskriterien verifiziert

### Zusaetzliche Pruefpunkte aus dem Verifikationsauftrag

| Pruefpunkt | Ergebnis |
|---|---|
| Zwischenzustands-Beweis (18-03) | `backend/tests/test_schema_generations.py`: `FIELDS_SCHEMA_1` (9 Felder, Z.77-100), Mengeninklusion (`test_the_new_schema_is_a_superset_of_the_old_one`), echter AST-Waechter (`ast.parse`/`ast.walk` Z.219-292, kein Import-basierter Test), `test_the_query_field_lists_name_no_field_the_old_schema_lacks` |
| `DEFAULT_FIELDS` unveraendert vier Felder | `backend/src/findling/query/rewrite.py:55`: `DEFAULT_FIELDS = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE]`, unveraendert |
| Python-Ratsche | `PACKAGE_FILES_TODAY = 56` (`test_measurement_scripts.py:809`), Hash `6063f7ca...` deckungsgleich mit dem in der Debug-Session dokumentierten Fix |
| PHP-Ratsche | `PHP_FILES_TODAY = 68` (`test_measurement_scripts.py:554`) |
| Volle Suite | `uv run pytest -q` aus `backend/`: **2719 passed, 15 skipped in 253.52s** -- deckungsgleich mit dem in beiden Debug-Sessions dokumentierten Endstand (2719 passed, 15 skipped) |
| CI-Lauf 36006893151 | Unabhaengig per `gh run view 36006893151` abgefragt: alle vier Matrix-Jobs (stable33/34/34-arm/35) "success" |
| Sechs Kataloge im Gleichstand (18-10) | `php/l10n/{de,de_DE,fr}.{json,js}`: alle sechs Dateien tragen exakt 202 Schluessel; beide neuen Bannertexte in de und fr uebersetzt vorhanden |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `backend/src/findling/index/schema.py` | 13 Felder, 6 Koerperfelder, `BODY_FIELD`-Mapping | VERIFIED | `FIELDS` traegt 13 Konstanten, `BODY_FIELD` mapt alle 6 Sprachen auf Feldnamen |
| `backend/src/findling/index/open.py` | 8 Kettenregistrierungen unbedingt | VERIFIED | `register_tokenizer` fuer de/en/es/it/nl/pt/name/stored_only, alle unbedingt zur Modulzeit |
| `backend/src/findling/config.py` | `SCHEMA_VERSION=2`, `SUPPORTED_LANGUAGES` sechs Codes | VERIFIED | Z.49, Z.148 |
| `backend/src/findling/store/repo.py` | `_schema_is_legacy`, `_languages_are_legacy`, `LEGACY_SCHEMA_STEPS` | VERIFIED | Alle drei vorhanden und in `version_mismatch` verdrahtet |
| `backend/src/findling/index/rebuild.py` | `RebuildVerdict`, `may_rebuild`, `_resume_cursor`, `transfer_documents`, `swap_in`, `retire_directory`, `discard_directory`, `stamp_after_swap`, `recover_the_index_directories`, `rebuild_the_index` | VERIFIED | 927 Zeilen, alle genannten Funktionen vorhanden, ueber `open_index` und `Store.write_meta` verdrahtet |
| `backend/src/findling/main.py` | vierte Lifespan-Aufgabe, OCR-Startwarnung, `REBUILD_STOP_SECONDS` | VERIFIED | `_rebuild_the_index_directory`, `asyncio.create_task` Z.693, Warnzeile Z.498 |
| `backend/src/findling/api/status.py` | `languagesActive`, `languagesFilled`, `rebuildRunning/Done/Total` | VERIFIED | Alle Felder vorhanden und aus `rebuild_progress()`/`resources.filled_languages()` befuellt |
| `php/templates/admin.php` | Umbau-Banner + Platzbanner, kein Restart-Aufruf | VERIFIED | `findling-banner-rebuild` und `findling-banner-rebuild-space`, Text vermeidet bewusst jedes Kommando |
| `php/lib/Migration/Version001300Date20260924000000.php` | Lockstep-Migration 1.2.0 auf 1.3.0 | VERIFIED | `postSchemaChange` loescht `KEY_BACKEND_VERSION`, doppellaufsicher |
| `.github/workflows/deploy-harp.yml` | `UPGRADE_FROM_TAG=v1.2.0`, "Store upgrade 5" + "Store upgrade 6" | VERIFIED | Beide Bloecke vorhanden, beide gruen im referenzierten Lauf |
| `backend/tests/test_language_cases_field_level.py` | 4 Sprachfaelle auf Feldebene | VERIFIED | 36 parametrisierte Tests, alle gruen |
| `backend/tests/test_schema_generations.py` | Mengeninklusion + AST-Waechter | VERIFIED | Echter `ast`-basierter Waechter, kein Import-Mock |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `schema.py` | `analyzer.py` | Tokenizernamen `TOKENIZER_(ES\|IT\|NL\|PT)` | WIRED |
| `open.py` | `analyzer.snowball_analyzer` | `register_tokenizer` je Sprache | WIRED |
| `rebuild.py` | `index/open.open_index` | beide Verzeichnisse ausschliesslich ueber `open_index` | WIRED |
| `rebuild.py` | `store/repo.Store.write_meta` | eigene `stamp_after_swap`, nicht die alte Stempelfunktion | WIRED |
| `main.py` | `Poller.silence`/`Poller.arm` | Ruhigstellen vor Band 1, Scharfschalten nach Tausch, Journal `["silence","document","drop_read_side","stamp","arm"]` (18-09-SUMMARY) | WIRED |
| `main.py` | `index/rebuild` | `asyncio.to_thread`, blockierende Arbeit nie auf dem Loop | WIRED |
| `php/lib/Service/AdminViewService.php` | `GET /status` | `languagesActive`, `rebuildRunning` etc. gelesen und ins Template gereicht | WIRED |
| `config.py` (`FINDLING_REBUILD_FALLBACK`) | `rebuild.py` Vollreindex-Zweig | `resolved.rebuild_fallback == FULL_REINDEX_FALLBACK` | WIRED |
| `deploy-harp.yml` | `findling.tools.index_status` | `marks.languages` als Unterschied 1.2.0/1.3.0 | WIRED |

### Data-Flow Trace (Level 4)

Nicht separat noetig: die zentralen Datenfluesse (Umbaufortschritt, Sprachmarken, Vektorbestand) sind bereits ueber echte CI-Laeufe mit echten Containern belegt (Lauf 36006893151, neun Zusicherungen inklusive Byte-Vergleich von `vectors.db`), nicht nur ueber Unit-Mocks.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Feldebene-Sprachfaelle laufen wirklich | `uv run pytest tests/test_language_cases_field_level.py -q` | 36 passed | PASS |
| Volle Suite laeuft real | `uv run pytest -q` aus `backend/` | 2719 passed, 15 skipped in 253.52s | PASS |
| Testsammlung entspricht der behaupteten Fallzahl | `pytest --collect-only -q` | "36 tests collected" | PASS |
| CI-Lauf tatsaechlich gruen | `gh run view 36006893151` | alle 4 Matrix-Jobs "success" | PASS |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh`-Dateien in diesem Projekt gefunden; die Beweisstrecke laeuft ausschliesslich ueber die CI-Workflow-Schritte "Store upgrade 5"/"Store upgrade 6", die oben unabhaengig per `gh run view` abgefragt wurden. SKIPPED (kein konventionelles Probe-Verzeichnis).

### Requirements Coverage

| Requirement | Source Plan | Beschreibung | Status | Evidence |
|---|---|---|---|---|
| LEX-02 | 18-01, 18-02 | Schema fuehrt immer sechs Koerperfelder, Befuellung nach `FINDLING_LANGUAGES` | SATISFIED | `schema.py` FIELDS, `writer.py` BODY_FIELD-Schleife |
| LEX-03 | 18-06, 18-07, 18-08, 18-09 | Re-Analyse-Umbau, wiederaufnahmefaehig, `vectors.db`/`state.db` unberuehrt | SATISFIED | `rebuild.py` komplett, CI Assurance 9 |
| LEX-04 | 18-03, 18-05, 18-11 | Getrennte Phasen, kein Zwischenzustand-Totalausfall, Migration im Lockstep | SATISFIED | `test_schema_generations.py`, `_schema_is_legacy`, Migrationsdatei |
| LEX-06 | 18-05, 18-09, 18-10 | Diagnose aktive/befuellte Sprachen, OCR-Startwarnung | SATISFIED | `status.py`, `main.py:498` |
| LEX-08 | 18-04, 18-12 | CI beweist beide Richtungen, Sprachfaelle auf Feldebene | SATISFIED | `deploy-harp.yml`, `test_language_cases_field_level.py`, Lauf 36006893151 |

Keine verwaisten Requirements: `.planning/REQUIREMENTS.md` listet fuer Phase 18 exakt LEX-02, LEX-03, LEX-04, LEX-06, LEX-08, und alle fuenf erscheinen als `requirements:`-Feld in mindestens einem der zwoelf Plaene. `REQUIREMENTS.md` selbst traegt die Checkboxen noch als `[ ]` (Pflege obliegt dem Abschluss der Phase, kein inhaltlicher Befund).

### Anti-Patterns Found

Keine. `grep` auf TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER/"not yet implemented" in allen zentralen neuen/geaenderten Dateien (`rebuild.py`, `repo.py`, `open.py`, `schema.py`, `config.py`, `main.py`, `status.py`, `resources.py`, der Migrationsklasse, `admin.php`, `AdminViewService.php`, `admin.js`) liefert keinen Treffer.

### Debug-Sessions dieser Phase

Zwei im Lauf gefundene und behobene Befunde, beide als `VERIFIED 24.09.2026` markiert und durch denselben unabhaengig geprueften CI-Lauf 36006893151 bestaetigt:

1. `upgrade5-schema-drift-languages.md`: `expected_versions()` behauptete `schema_version=2` fuer jede Instanz; ein Bestand mit Schema 1 meldete faelschlich Drift und loeste einen ungewollten Reindex aus. Behoben durch `_schema_is_legacy`/`LEGACY_SCHEMA_STEPS` als Paartabelle (kein Zahlenvergleich, damit eine kuenftige Schemastufe 3 die Ausnahme nicht automatisch erbt).
2. `upgrade6-rebuild-timeout.md`: zwei Ursachen, keine im Produktcode. (a) Der Containerneubau via `docker inspect` verlor die von HaRP nachtraeglich abgelegten Tunnelzertifikate, dadurch 300 s `backendReachable:false`. (b) Nach dem Tunnelfix war das Umbaufenster (reine Tragezeit) mit dem 497-kB-Referenzkorpus kuerzer als eine Leserunde; behoben durch einen 32-MB-Fuellkorpus in "Store upgrade 2", ohne eine Zusicherung zu entschaerfen.

Beide Befunde sind reine CI-Infrastruktur- bzw. Messkorrekturen, keine Luecken im Produktverhalten.

### Human Verification Required

Keine. Alle fuenf Erfolgskriterien sind ueber Code-Lese-Pruefung, eigenen Testlauf und eine unabhaengig abgefragte, tatsaechlich gruene CI-Ausfuehrung (Container-Ebene, kein Mock) belegt.

### Gaps Summary

Keine Luecken gefunden. Alle fuenf Roadmap-Erfolgskriterien der Phase 18 sind im Code umgesetzt, ueber echte Tests (36/36 Feldebene-Sprachfaelle, 2719/2719 Suite gruen) und einen unabhaengig verifizierten CI-Lauf (36006893151, alle vier Matrix-Aeste gruen) belegt. Die beiden im Lauf aufgetretenen Debug-Befunde sind vollstaendig behoben und durch denselben gruenen Lauf bestaetigt. Dokumentierte Abweichungen (Migrationsdatum 24.09. statt 25.09., diverse "Praezisierungen" in den Plaenen) sind begruendet, aendern nichts an der Zielerreichung und sind keine Luecken.

---

*Verified: 2026-09-24T14:14:23Z*
*Verifier: Claude (gsd-verifier)*
