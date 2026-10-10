---
phase: 30-owner-tor-schema-und-tschechisch
verified: 2026-10-10T10:19:39Z
status: human_needed
score: 12/13 must-haves verified (1 UNCERTAIN, Owner-Entscheid)
overrides_applied: 0
deferred:
  - truth: "Wortlaut des fünften Grenz-Eintrags (Tschechisch ohne Stammformreduktion) ist vom Owner abgenommen"
    addressed_in: "Phase 36"
    evidence: "REQUIREMENTS.md REL-05: 'Teil der Textabnahme: Wortlaut des fuenften Grenz-Eintrags Tschechisch (D-30-06, Entwurf aus 30-08 in docs/store-listing.md ...)'"
human_verification:
  - test: "Owner entscheidet über die Abweichung 4 aus 30-08-SUMMARY: die READMEs (de/en/fr) nennen Tschechisch nur in der OCR-Klammerliste, nicht als Suchsprache, obwohl der must_have von 30-08 das verlangt"
    expected: "Entweder Override eintragen (Kurztext-Regel, Suchsprachen stehen in den sechs Store-Texten) oder je README eine Suchsprachen-Faktenzeile ergänzen"
    why_human: "Widerspruch zwischen Plan-must_have und Owner-Regel 'Kurze Produkttexte'; nur der Owner kann das auflösen"
  - test: "Owner nimmt L-30-02 (LOW, vom Audit akzeptiert) zur Kenntnis: ein Treffer, der nur über body_cs zustande kommt, erscheint ohne Auszug (Snippet nur aus body_de)"
    expected: "Bestätigung, dass das für 1.5.0 so bleiben darf, oder Auftrag für einen Fix vor Phase 36"
    why_human: "Produktentscheid zur Trefferdarstellung tschechischer Dokumente; Akzeptanz kam bisher nur aus dem Audit, nicht vom Owner"
---

# Phase 30: Owner-Tor, Schema und Tschechisch, Verifikationsbericht

**Phasenziel:** Alle offenen Owner-Entscheide des Milestones sind getroffen, das Schema für v1.5 steht in einem einzigen Schritt fest, und Admins können Tschechisch für OCR und lexikalische Suche einschalten.
**Verifiziert:** 2026-10-10T10:19:39Z
**Status:** human_needed
**Re-Verifikation:** Nein, erste Verifikation

## Zielerreichung

### Beobachtbare Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|----------|--------|-------|
| 1 | SC1/CZ-01: Admin kann `ces` als OCR-Sprache wählen, Bau-Prüfung im Image weist das Paket nach, ein tschechischer Scan liefert Treffer | VERIFIED | `backend/Dockerfile` Z. 350 `tesseract-ocr-ces=1:4.1.0-2`, Z. 362 `grep -qx ces` in der Bau-Kette; `config.py:430` `OCR_LANGUAGE_ALLOWLIST` enthält `ces`, `TESSERACT_NAME["cs"]="ces"`; info.xml env-Beschreibung nennt `ces (Czech)`. CI docker.yml Lauf 38042757235 (HEAD 9e9764bf), Schritt "Czech OCR in the image (CZ-01)" auf amd64 UND arm64: `names ces: True`, `czech page: 10 tokens, 4 of 4 expected: smlouva, ucetni, rizeni, rijen`, `white page: 0 tokens`, `ok` |
| 2 | SC2/CZ-02: `cs` lexikalisch einschaltbar, Akzentfaltung, Stoppwörter ohne Treffer, kein Stemmer | VERIFIED | `analyzer.czech_analyzer()`: simple, lowercase, ascii_fold, custom_stopword, remove_long, kein Stemmer. Eigene Gegenprobe: `SMLOUVĚ smlouve Smlouva proč PROC a že byt jez nájemní` ergibt `smlouve, smlouve, smlouva, byt, jez, najemni` (Akzente gefaltet, Stoppwörter weg, Ausnahmen byt/jez bleiben, Flexion bleibt getrennt wie CZ-03 dokumentiert). `SUPPORTED_LANGUAGES` und `BODY_FIELD["cs"]="body_cs"` gesetzt, `STEMMERLESS_LANGUAGES={"cs"}` außerhalb `SNOWBALL_NAME` |
| 3 | SC2: Stoppwortliste trägt Lizenzbeleg im Repo (D-30-02, D-30-05) | VERIFIED | `LICENSES/Apache-2.0.txt`; `THIRD-PARTY.md` Abschnitt "Czech stop word list (Apache Lucene)" mit Quelle, Tag 10.5.2, NOTICE; Original `backend/tests/fixtures/lucene_cz_stopwords_10_5_2.txt`, SHA-256 `61f06aa1...ad915`, eigene Gegenprobe gegen raw.githubusercontent.com/apache/lucene/releases/lucene/10.5.2: identischer Hash; `stopwords_cs.py` trägt Herkunft, NOTICE-Text (Fix L-30-01, 9e9764bf), Ausnahmetabelle mit `byt` und `jez` |
| 4 | SC3/CZ-02: Bestandsinstallation ohne `cs` upgradet von 1.4.2 ohne Umbau und ohne Neu-Einbettung (CI, UPGRADE_FROM_TAG=v1.4.2) | VERIFIED | `deploy-harp.yml:140` `UPGRADE_FROM_TAG: v1.4.2`. Lauf 38042757174 (9e9764bf), Job stable34/amd64, Schritt "Store upgrade 5": `the stored schema mark reads 2 after the upgrade, the 2 of v1.4.2, with no rebuild`, `rebuildState idle`, `no start_rebuild_on_drift line`, `languages mark reads de,en before and after`, `vector stock ... unchanged, nothing was embedded again`, `all eight assurances hold`. Gleiches Ergebnis in Lauf 38036946762. Code: `repo._schema_is_legacy` mit `LEGACY_SCHEMA_STEPS {("1","2"),("2","3"),("1","3")}`; eigene Gegenprobe: (2,3) und (1,3) True, (3,2), (4,3), (None,3) False |
| 5 | SC3: Umbau in beide Richtungen für `cs` in CI bewiesen (D-30-07) | VERIFIED | Lauf 38042757174, "Store upgrade 6": Schema 2 auf 3, Sprachmarke `de,cs`, `smlouve 1 -> 1, proc 1 -> 0` (body_cs allein antwortet), `all ten assurances hold`. "Store upgrade 7": zurück auf `de,en`, Schema bleibt 3, body_cs leer, `vectors.db` byte-gleich vor beiden Umbauten, `all seven assurances of the way back hold`. Beide HaRP-Läufe: alle 4 Jobs success; die Upgrade-Schritte laufen bewusst nur im Job stable34/ubuntu-24.04 (if-Bedingung Z. 5010/5707) und sind dort success |
| 6 | Bestandsinstallationen mit es/it/nl/pt verlieren bei Schema 2 und 3 keine Felder (Pflicht-Fix `_of_the_marks`) | VERIFIED | `resources.py:403` `QUERYABLE_SCHEMA_GENERATIONS = {"2","3"}`, Z. 420 prüft dagegen statt gegen `str(SCHEMA_VERSION)`. Eigene Gegenprobe: Marken `de,en,es,it,nl,pt` unter Schema 2 und 3 liefern alle sechs body-Felder, Schema 1/4/fehlend liefern None (Legacy-Kaskade). Tests `test_six_languages_on_a_schema_2_directory_keep_all_six_under_schema_3_code`, `test_a_schema_2_stock_with_spanish_keeps_spanish_without_a_rebuild` grün |
| 7 | SC4/D-30-08: Schema 3 ist der einzige Schemaschritt, trägt alle v1.5-Felder | VERIFIED | `config.SCHEMA_VERSION = 3`, einziges neues Feld `body_cs` (`schema.py:190`); Schema-2-Layout eingefroren (`test_schema_generations.py` `test_the_three_generations_are_nested`); D-30-03 bestimmt "kein neues Schemafeld" für ZIP-Treffer |
| 8 | D-30-08 Prüfzeile: Ordnerfilter Phase 32 über `path`-Spalte ohne Schemafeld | VERIFIED | `30-03-SUMMARY.md` Abschnitt "Prüfzeile A5"; Angaben gegengeprüft: `store/schema.sql:44` `path TEXT NOT NULL`, `repo.py:1361` `prefilter_visible`; Ergebnis "kein zweiter Schemaschritt nötig" mit Hinweis Abbildungsfrage für Phase 32 |
| 9 | Owner-Entscheide D-30-01..08 und Pflicht-Fix festgehalten | VERIFIED | `30-CONTEXT.md` Z. 8 bis 19; D-30-01/03/04 sind Vorgaben für Phase 31/33 und dort zu prüfen |
| 10 | SC5/CZ-03: Grenze "ohne Stammformreduktion" in Doku dreisprachig und als 5. Eintrag der Grenzliste | VERIFIED | `backend/appinfo/info.xml` Z. 98/128/158 und `php/appinfo/info.xml` Z. 52/85/118 (de/en/fr); `docs/language-analyzers.md` Abschnitt "Czech" (Z. 405 ff.) und Kurzliste Z. 629 ff.; Gate `LIMITATION_COUNT = 5` in `test_store_metadata.py:450` (grün) |
| 11 | 5. Grenz-Eintrag als Owner-Abnahme bei REL-05 vermerkt (D-30-06) | VERIFIED | `docs/store-listing.md:2008` "Entwurf v1.5.0 (Teil Phase 30)", Z. 2010 "Owner-Abnahme offen ... (REL-05, Phase 36)", Z. 2065; `REQUIREMENTS.md:58` REL-05 nennt den Wortlaut ausdrücklich |
| 12 | Audit Security/Bugs/Performance durchgeführt, Befunde vor Abschluss behandelt | VERIFIED | `30-AUDIT.md`: 0 CRITICAL, 0 HIGH, 0 MEDIUM; L-30-01 gefixt (9e9764bf, im Code belegt); L-30-02 und L-30-03 LOW akzeptiert |
| 13 | 30-08 must_have: READMEs nennen Tschechisch als verfügbare Suchsprache | UNCERTAIN | README.md Z. 28 bis 31, README.en.md Z. 28 bis 30, README.fr.md Z. 30 bis 32 nennen Tschechisch nur als OCR-Sprache. Abweichung 4 in 30-08-SUMMARY begründet mit Kurztext-Regel; das Roadmap-SC verlangt das nicht. Owner-Entscheid nötig (Override oder Nachtrag) |

**Score:** 12/13 verifiziert, 1 UNCERTAIN

### Zurückgestellte Punkte

| # | Punkt | Erledigt in | Beleg |
|---|-------|-------------|-------|
| 1 | Owner-Abnahme des Wortlauts des 5. Grenz-Eintrags | Phase 36 | REL-05 in REQUIREMENTS.md nennt die Abnahme ausdrücklich |

### Artefakte

| Artefakt | Status | Details |
|----------|--------|---------|
| `backend/src/findling/index/analyzer.py` (`czech_analyzer`, `TOKENIZER_CS`) | VERIFIED | substanziell, registriert, im CI-Probe und in den Tests genutzt |
| `backend/src/findling/index/stopwords_cs.py` | VERIFIED | 167 gefaltete Einträge, Ausnahmen byt/jez, Digest-Gate |
| `backend/src/findling/index/schema.py` (`body_cs`) | VERIFIED | `BODY_FIELD["cs"]`, Writer schreibt über `BODY_FIELD[language]` |
| `backend/src/findling/config.py` (`SCHEMA_VERSION=3`, Allowlists) | VERIFIED | |
| `backend/src/findling/store/repo.py` (`LEGACY_SCHEMA_STEPS`) | VERIFIED | in `diverging_marks` über `_schema_is_legacy` verdrahtet |
| `backend/src/findling/api/resources.py` (`QUERYABLE_SCHEMA_GENERATIONS`) | VERIFIED | in `_of_the_marks`, `field_plan_for`, `plan_falls_short` |
| `backend/Dockerfile` (ces) | VERIFIED | apt-Zeile plus Bau-Prüfung |
| `.github/workflows/deploy-harp.yml` (v1.4.2, Schritte 6/7) | VERIFIED | grün in 38042757174 und 38036946762 |
| `.github/workflows/docker.yml` (Czech OCR probe) | VERIFIED | grün auf amd64 und arm64 |
| `THIRD-PARTY.md`, `LICENSES/Apache-2.0.txt`, Lucene-Fixture | VERIFIED | Hash upstream gegengeprüft |
| `docs/language-analyzers.md`, beide `info.xml`, `docs/store-listing.md` | VERIFIED | |

### Key Links

| Von | Nach | Über | Status |
|-----|------|------|--------|
| `config.FINDLING_LANGUAGES=cs` | `writer.py:317` | `BODY_FIELD[language]` | WIRED |
| `schema.py body_cs` | `czech_analyzer` | `tokenizer_name=TOKENIZER_CS` | WIRED |
| Sprachmarke im state.db | Feldplan der Suche | `_of_the_marks` / `field_plan_for` | WIRED |
| Schemamarke 2 bei Code 3 | kein Drift | `diverging_marks` -> `_schema_is_legacy` | WIRED |
| Sprachwechsel cs an/aus | Re-Analyse-Umbau | Band-Run, CI Schritte 6/7 | WIRED |
| Kurzliste in Doku | sechs Store-Texte | zeichengleich, `test_store_metadata.py` | WIRED |

### Verhaltens-Stichproben

| Verhalten | Befehl | Ergebnis | Status |
|-----------|--------|----------|--------|
| Phasen-Tests Teil 1 | `uv run pytest` über 10 Kerndateien (czech_analyzer, czech_switch, schema_generations, query_fields_plan, phase30_audit, ocr_languages, language_allowlist, upgrade_compatibility, field_plan_ranking, store_metadata) | 274 passed | PASS |
| Phasen-Tests Teil 2 | `uv run pytest` über index_open, index_rebuild, language_proof_steps, measurement_scripts, store_repo, upgrade_seed_steps, v13_ablauf | 866 passed | PASS |
| cs-Kette | `czech_analyzer().analyze(...)` | Faltung, Stoppwörter, Ausnahmen wie spezifiziert | PASS |
| Feldplan-Tor | `_of_the_marks` für Schema 1/2/3/4/fehlend | 2 und 3 behalten sechs Sprachen, sonst None | PASS |
| Ratsche | `_schema_is_legacy` Paare | nur (1,2),(2,3),(1,3) | PASS |
| Lucene-Original | `curl ... | sha256sum` | identisch mit Fixture | PASS |
| CI python.yml HEAD | `gh run list` | 38042757203 success | PASS |

### Probe-Ausführung

Keine `scripts/*/tests/probe-*.sh` deklariert. `backend/tests/probe_image_ocr_czech.py` braucht das Image und läuft in docker.yml; Ergebnis dort per `gh run view --log` belegt (siehe Wahrheit 1).

### Requirements

| Requirement | Plan | Status | Beleg |
|-------------|------|--------|-------|
| CZ-01 | 30-02, 30-08 | SATISFIED | Wahrheit 1 |
| CZ-02 | 30-01, 30-03..30-07 | SATISFIED | Wahrheiten 2 bis 6 |
| CZ-03 | 30-08 | SATISFIED | Wahrheit 10 |

Keine verwaisten Requirements für Phase 30.

### Anti-Pattern

| Datei | Befund | Schwere |
|-------|--------|---------|
| Diff der Phase (44 Dateien außerhalb .planning) | keine neuen TBD/FIXME/XXX | keine |
| `index/search.py:875` | L-30-02: Treffer nur über body_cs ohne Auszug | Hinweis, Owner-Kenntnisnahme |
| `deploy-harp.yml:5301` | L-30-03: Vektordigest ungeprüft in GITHUB_ENV (nur CI) | Info |

### Menschliche Prüfung nötig

1. **README-Abweichung (30-08 must_have)**
   Test: entscheiden, ob die READMEs Tschechisch zusätzlich als Suchsprache nennen sollen.
   Erwartet: Override oder Nachtrag einer Faktenzeile.
   Warum Mensch: Plan-must_have widerspricht der Owner-Regel "Kurze Produkttexte".

   Vorschlag für Override in dieser Datei:
   ```yaml
   overrides:
     - must_have: "Store-Texte und READMEs nennen zehn OCR-Sprachen inklusive Tschechisch und Tschechisch als verfügbare Suchsprache"
       reason: "READMEs haben keine Suchsprachen-Zeile; Kurztext-Regel; Suchsprachen stehen in allen sechs Store-Texten"
       accepted_by: "street1983nk"
       accepted_at: "<ISO-Zeitpunkt>"
   ```

2. **L-30-02 Treffer ohne Auszug**
   Test: Index `de,cs`, nach tschechischem Wort suchen, das nur body_cs trifft.
   Erwartet: Owner bestätigt, dass Treffer ohne Snippet für 1.5.0 tragbar ist, oder beauftragt Fix.
   Warum Mensch: Produktentscheid zur Trefferdarstellung.

### Hinweise

- Das Roadmap-Beispiel "smlouva / Smlouvě" ist als Akzentpaar derselben Form gelesen (smlouvě/smlouve treffen ein Term). smlouva gegen smlouvě bleibt bewusst getrennt, das ist genau die dokumentierte Grenze CZ-03 (`test_an_inflection_pair_stays_two_terms_on_body_cs`).
- Der OCR-Beweis prüft Erkennung plus cs-Kette im Image, nicht eine Suchanfrage über einen gescannten Tschechisch-Bestand in einer laufenden Instanz; die Suche über body_cs ist separat in deploy-harp Schritt 6 bewiesen.

### Zusammenfassung

Das Phasenziel ist im Code erreicht: `ces` im Image mit Bau-Prüfung und CI-Bildbeweis auf beiden Architekturen, stemmerlose cs-Kette mit gefalteter Lucene-Liste und vollständigem Lizenzbeleg, einziger Schemaschritt 2 auf 3 mit Ratsche und Pflicht-Fix für es/it/nl/pt, Upgrade von v1.4.2 ohne Umbau und ohne Neu-Einbettung sowie Umbau cs an und aus in CI grün, Grenze dreisprachig in sechs Store-Texten und als fünfter Eintrag mit REL-05-Vermerk. Offen bleiben zwei Owner-Entscheide ohne Blocker-Charakter (README-Abweichung, L-30-02).

---

_Verifiziert: 2026-10-10T10:19:39Z_
_Verifier: Claude (gsd-verifier)_
