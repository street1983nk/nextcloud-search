# Phase 30: Owner-Tor, Schema und Tschechisch - Research

**Researched:** 2026-10-10
**Domain:** tantivy-Schema/Versionsmarken, Analyseketten (tantivy-py 0.26.2), Tesseract-Sprachpakete, Upgrade-CI
**Confidence:** HIGH (Codebasis gelesen, Kernaussagen gegen tantivy 0.26.2 lokal gemessen, Paket- und Lucene-Quelle per API geprüft)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-30-01 Ausschlussmuster-Syntax (EXCL, Phase 33):** Einfache Platzhalter, nur `*` und `?` (fnmatch-artig, kein `**`, keine Negation, keine Regex). Beispiele `*.photoslibrary`, `*/node_modules/*`. Bestehende Praefix-Ausschluesse bleiben gueltig.
- **D-30-02 Tschechische Stoppwoerter (CZ-02):** Liste aus Lucene `CzechAnalyzer` (Apache 2.0), Lizenz- und Herkunftsbeleg im Repo ablegen (wie die anderen Wortlisten). Akzentfaltung: Stoppwortliste muss nach der Faltung passen (Supplement-Logik wie bei den anderen Sprachen in index/analyzer.py pruefen).
- **D-30-03 ZIP-Treffer (FMT-02, Phase 31):** EIN Treffer je Archiv. Das Archiv ist ein Dokument, Text aller inneren Dateien zusammen; das Snippet nennt die innere Datei. KEIN neues Schemafeld noetig.
- **D-30-04 Nachholweg (FMT-06, Phase 31):** Alle neu lesbaren Typen werden nach dem Upgrade nachgeholt: bisher als `legacy_format` uebersprungene .doc/.xls plus alle .eml/.zip/.heic, in Baendern wie die 1.4-Altbestands-Nachpruefung, ohne bestehende Treffer anzufassen.

### Folge fuer Phase 30 (aus CONTEXT.md, verbindlich)
- Da D-30-03 kein Schemafeld braucht, ist die einzige Schema-/Markenaenderung des Milestones das tschechische Koerperfeld (CZ-02). Bestandsinstallationen ohne `cs` in FINDLING_LANGUAGES bauen NICHT um.
- tantivy hat keinen tschechischen Snowball-Stemmer: Kette = Tokenizer, Kleinschreibung, Akzentfaltung, Stoppwoerter, KEIN Stemmer. Die Allowlist-Gegenprobe (test_language_allowlist.py) vergleicht gegen die laufende tantivy-Engine; Tschechisch braucht daher einen eigenen Weg ausserhalb von SNOWBALL_NAME (nicht einfach in LANGUAGE_ALLOWLIST eintragen, sonst Panic-/ValueError-Pfad).
- `ces`-OCR: Weg wie dan/est in Plan 16-10 (eigene apt-Zeile, Bau-Pruefung, OCR_LANGUAGE_ALLOWLIST).
- Upgrade-CI-Beweis: 1.4.2 -> neu ohne Umbau bei de,en; mit cs Umbau per Re-Analyse.
- Grenze dokumentieren (CZ-03): keine Stammformreduktion.

### Claude's Discretion
Kein eigener Abschnitt in CONTEXT.md. Offen und damit Planungsspielraum: Dateiform der Stoppwortliste, Kettenfabrik, Testschnitt, CI-Schnitt, ob ein eigenes Kettenmerkmal entsteht (Empfehlung unten: nein).

### Deferred Ideas (OUT OF SCOPE)
Keine in CONTEXT.md benannt. Aus dem Milestone gilt: kein Modellwechsel (granite nur Messung, Phase 35), Formate erst Phase 31, Filter erst Phase 32, Ausschlussmuster erst Phase 33.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CZ-01 | Admin kann Tschechisch als OCR-Sprache wählen (`ces` im Image und in der Allowlist, Bau-Prüfung wie dan/est) | `tesseract-ocr-ces` 1:4.1.0-2 in trixie verifiziert (main, all, Quelle tesseract-lang); Muster Plan 16-10: apt-Zeile mit Pin, `--list-langs`-Prüfung, `OCR_LANGUAGE_ALLOWLIST` auf 10, `test_ocr_languages.py`, THIRD-PARTY.md, info.xml-Beschreibung, `TESSERACT_NAME["cs"] = "ces"` |
| CZ-02 | Admin kann Tschechisch lexikalisch einschalten: eigenes Körperfeld ohne Stemmer, Stoppwörter mit Lizenzbeleg; Wechsel per Re-Analyse, Bestand ohne `cs` baut nicht um | Abschnitte "Kernfrage 1", "Architecture Patterns", "Czech chain"; gemessene Kette; Lucene-Liste mit Tag, Commit, SHA-256; Umbauweg über die Sprachmarke |
| CZ-03 | Grenze dokumentiert: keine Stammformreduktion | Messbeleg `smlouva` gegen `smlouvě` (zwei Terme); Doku-Orte: `docs/czech-analyzer.md` (neu) bzw. `docs/language-analyzers.md`, Kurzliste HART-05, beide info.xml dreisprachig, `LIMITATION_COUNT` |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.13 + uv; Code und Bezeichner Englisch und ASCII; echte Umlaute nur in deutscher Prosa, nie in Code. In `src` bleiben Akzente aus Literalen heraus (Präzedenz `stopwords.py`: "Accents appear nowhere in this file"); in Tests sind Akzente als Daten in String-Literalen erlaubt (`test_language_analyzers.py`, Zeile 44).
- Qualitätsgates lokal grün vor Commit: `ruff check`, `ruff format --check`, `pyright` (basic), `vulture src tests --min-confidence 80`, pytest; für `scripts/` eigener ruff-Lauf.
- Keine Em-/En-Dashes, keine Emojis in Texten (Store-Text-Gate `test_no_store_text_carries_a_dash_or_an_emoji`).
- Kurze Produkttexte: Store/README = Faktenliste; Store-Textentwurf vor Release dem Owner zeigen (Phase 34 legt ihn vor).
- Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Abschluss fixen.
- Lizenz AGPL-3.0; neue Fremdinhalte brauchen Lizenzbeleg (THIRD-PARTY.md + REUSE.toml).
- Commits nur als Owner (keine Claude-Trailer), Projektregel aus Memory.
- Repo-Muster "roter Gold-Test ist eine Owner-Frage, keine Reparatur" (`test_upgrade_compatibility.py`, Kopf): jede Markenbewegung braucht einen dokumentierten Owner-Entscheid. Für Phase 30 liegt er als D-30-02 plus "Folge für Phase 30" vor; der Plan muss ihn im Kommentar des neuen Gold-Werts zitieren.

## Summary

**Antwort auf Kernfrage 1: Ein Umbau für alle ist NICHT unvermeidlich.** Ein siebtes Körperfeld `body_cs` erzwingt einen `SCHEMA_VERSION`-Sprung von 2 auf 3, aber der Code hat für genau diesen Fall bereits die Ratsche: `LEGACY_SCHEMA_STEPS` in `store/repo.py` erlaubt Paare (gespeichert, erwartet), bei denen eine Schemamarke ohne Umbau stehen bleiben darf. Mit den Paaren `("2", "3")` und `("1", "3")` meldet `version_mismatch` für eine 1.4.2-Installation ohne `cs` keine Drift, `rebuild_the_index` antwortet `NOTHING_TO_REBUILD`, und `Index.open` liest das alte 13-Felder-Schema einfach weiter. Erst eine Sprachmarke mit `cs` (Drift von `de,en` auf `de,en,cs`) startet den Bandlauf, der das neue Verzeichnis aus `build_schema()` mit 14 Feldern anlegt und dahinter Schema `3` stempelt. Das ist exakt der Weg, den v1.3 für 1 auf 2 gegangen ist.

**Es gibt aber eine Falle, die v1.3 nicht hatte und die ohne Code-Änderung Bestandsinstallationen still beschädigt:** `api/resources.py::_of_the_marks` verlangt `marks[SCHEMA_MARK] == str(SCHEMA_VERSION)` wörtlich und fällt sonst auf `LEGACY_PLAN` (nur `body_de`, `body_en`) zurück. Bei 1 auf 2 war das harmlos, weil keine 1.2.x-Installation andere Sprachen haben konnte. Bei 2 auf 3 haben Installationen mit `es`, `it`, `nl` oder `pt` eine gespeicherte `2` und würden nach dem Upgrade ihre Zusatzsprachen nicht mehr durchsuchen, ohne Banner, ohne Umbau. Das Feldplan-Tor muss deshalb die Generation `2` als abfragbar akzeptieren (der vorhandene Feldprobe `_probed` sichert ab, dass nie ein Feld genannt wird, das das Verzeichnis nicht trägt).

Fachlich zeigt die Messung zwei Dinge, die die Erfolgskriterien betreffen: (1) Das Roadmap-Beispiel "smlouva / Smlouvě" ist ein Flexions- und kein Akzentpaar (`smlouvě` faltet zu `smlouve`, nicht zu `smlouva`); der Test muss Akzentpaare derselben Form verwenden. (2) Auf einer Instanz mit `en` faltet `body_en` tschechische Akzente bereits heute (`smlouvě` und `smlouve` ergeben beide `smlouv`), und tschechische Stoppwörter treffen über `body_en` und `body_de`. "Stoppwörter erzeugen keine Treffer" ist deshalb nur auf Feldebene (`body_cs`) oder auf einer Instanz ohne `de`/`en` beweisbar; ein CI-Beweis auf dem normalen Suchweg braucht eine Sprachmenge ohne `en` (Empfehlung `de,cs`), sonst ist er grün aus dem falschen Grund.

**Primary recommendation:** `SCHEMA_VERSION` 2 auf 3 mit `LEGACY_SCHEMA_STEPS += {("2","3"), ("1","3")}`, `_of_the_marks` akzeptiert gespeichert `2` oder `3`, `cs` wird am Ende von `SUPPORTED_LANGUAGES` angehängt und über eine eigene, stemmerlose Kettenfabrik außerhalb von `SNOWBALL_NAME` registriert (immer, unabhängig von der Sprachmenge), die Lucene-Liste wird als gefaltete ASCII-Tupel mit Herkunftsdigest des Originals abgelegt, kein achtes Merkmal.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OCR-Sprache `ces` | Container-Image (Dockerfile, Tesseract) | Backend-Config (`OCR_LANGUAGE_ALLOWLIST`) | Sprachdaten liegen im Image; die Allowlist ist zugleich Sicherheitsgrenze (T-03-502) für die Subprozess-Argumente |
| Tschechische Analysekette | Backend Index (`index/analyzer.py`, `index/open.py`) | n/a | Tokenisierung ist Teil der Daten; nur `open_index` registriert |
| Schemafeld `body_cs` | Backend Index (`index/schema.py`) | Store (`LEGACY_SCHEMA_STEPS`) | Schema wird nur beim Anlegen eines Verzeichnisses geschrieben; die Markenvergleichsregel lebt im Store |
| Umbau bei Sprachwechsel | Backend Index (`index/rebuild.py`, Bandlauf) | Poller (Auslöser) | Re-Analyse aus gespeichertem `body_de`, kein Neulesen der Dateien |
| Feldplan der Suche | Backend API (`api/resources.py::field_plan_for`) | Query (`query/rewrite.py::BODY_BOOST`) | Plan wird aus Marken des Verzeichnisses berechnet, nicht aus dem Wunsch des Containers |
| Sprachwahl durch Admin | AppAPI Deploy-Umgebung (`backend/appinfo/info.xml` `FINDLING_LANGUAGES`, `FINDLING_OCR_LANGUAGES`) | PHP-Adminseite (nur Anzeige `languagesActive`/`languagesFilled`) | Es gibt keine Auswahl-UI; die Adminseite zeigt Codes, keine Sprachnamen, daher keine l10n-Arbeit |
| Grenz-Doku und Store-Text | Doku (`docs/`), Store-Metadaten (beide `info.xml`) | Gates (`test_store_metadata.py`) | Kurzliste HART-05 wird zeichengenau gegen beide info.xml gehalten |

## Kernfrage 1 im Detail: Welche Stellen berührt ein siebtes Feld, und warum baut der Bestand nicht um

### Was beim Öffnen wirklich passiert (verifiziert im Code)
- `open_index` ruft `Index.open(path)` für ein vorhandenes Verzeichnis; `build_schema()` läuft nur bei einem neuen. Ein 1.4.2-Verzeichnis behält also 13 Felder, auch unter 1.5-Code. [VERIFIED: codebase `index/open.py:165`]
- Ein unbekannter Feldname in `Document.add_text` plus `writer.add_document` wird stumm verworfen. Gemessen heute mit tantivy 0.26.2: Schema nur mit `body_de`, Dokument mit `body_cs`, Commit ohne Fehler ("accepted silently"). Der Schreibpfad bricht also auf einem alten Verzeichnis bei aktivem `cs` nicht, `body_cs` bleibt bis zum Umbau leer. [VERIFIED: lokale Messung 2026-10-10]
- Ein registrierter Tokenizer ohne Feld schadet nicht; ein Feld ohne registrierten Tokenizer bricht dagegen JEDES `add_document` ("Error getting tokenizer for field"). Folge: `cs` muss in `open_index` immer registriert werden, wie es `es`/`it`/`nl`/`pt` schon sind. [VERIFIED: codebase `index/open.py:168-177`, Messung 2026-09-24 im Kommentar]
- `filled_languages` und `_probed` fangen fehlende Felder je Feld ab (`terms_with_prefix`, `doc_freq` mit Exception-Fang). [VERIFIED: codebase `api/resources.py:440-502, 1001-1028`]

### Die Markenkette (verifiziert)
| Stelle | Heute | Für Phase 30 |
|---|---|---|
| `config.SCHEMA_VERSION` | `2` | `3` |
| `store/repo.py::LEGACY_SCHEMA_STEPS` | `{("1","2")}` | `{("1","2"), ("2","3"), ("1","3")}` mit Begründung je Paar (Mengeninklusion der Abfragefelder) |
| `api/resources.py::_of_the_marks` | `marks[SCHEMA_MARK] != str(SCHEMA_VERSION)` -> `None` -> `LEGACY_PLAN` | gespeichertes `2` ODER `3` erlaubt (eigene benannte Menge, z. B. `QUERYABLE_SCHEMA_GENERATIONS`), `1` bleibt beim Rückfall |
| `index/rebuild.py::stamp_after_swap` | schreibt `str(SCHEMA_VERSION)` | unverändert, schreibt dann `3` |
| `index/open.py::stamp_a_new_directory` | schreibt erwartete Marke | unverändert, frische Installation bekommt `3` |
| `MARKS_A_REBUILD_ANSWERS` | Schema, Sprachen, Dutch | unverändert |
| `expected_versions` | 7 Marken | unverändert 7 Marken (kein achtes) |
| `ANALYZER_VERSION` | `1` | bleibt `1` (eine neue Kette für ein neues Feld ändert keine bestehende Tokenisierung; Gate `test_the_analyzer_version_did_not_move`) |

### Ablauf je Installationstyp nach dem Upgrade 1.4.2 -> 1.5
| Ausgangslage | Gespeichert | Erwartet | Ergebnis |
|---|---|---|---|
| Werkseinstellung `de,en` | schema `2`, languages `de,en` | `3`, `de,en` | kein Mismatch (Paar `2,3`), kein Banner, kein Umbau, Feldplan `de,en` (mit Fix) |
| `de,en,es` | `2`, `de,en,es` | `3`, `de,en,es` | kein Umbau; OHNE `_of_the_marks`-Fix Rückfall auf `LEGACY_PLAN`, `body_es` still aus der Suche |
| 1.2.x direkt auf 1.5 | `1`, keine Sprachmarke | `3`, `de,en` | kein Umbau (Paar `1,3`, Sprachmarke legacy), Feldplan Rückfall `LEGACY_PLAN` = korrekt |
| Admin schaltet `cs` zu | `2`, `de,en` | `3`, `de,en,cs` | Sprachdrift -> Bandlauf in neues 14-Felder-Verzeichnis -> Stempel `3`, `de,en,cs` |
| Admin schaltet `cs` wieder ab | `3`, `de,en,cs` | `3`, `de,en` | Sprachdrift -> Bandlauf, `body_cs` bleibt leer, Feld bleibt im Schema |
| Frische 1.5-Installation | (neu) | `3` | `stamp_a_new_directory` schreibt `3` |

### Verworfene Alternative B: kein Schemasprung
`body_cs` hinzufügen und `SCHEMA_VERSION` bei 2 lassen. Technisch tragfähig (Feldplan + Sonde fangen es ab), aber: widerspricht der Regel im Docstring von `build_schema` ("changing a line here means raising SCHEMA_VERSION"), macht die Marke `2` mehrdeutig (13 oder 14 Felder), und ROADMAP SC4 verlangt ausdrücklich, dass die Markenänderung in Phase 30 stattfindet. Nicht empfohlen. [ASSUMED: Bewertung]

### Owner-Hinweis
Ein Umbau für alle ist vermeidbar, daher kein Owner-Hinweis "Umbau für alle" nötig. Formuliert werden muss nur die Notiz für den Gold-Test (Kopf `test_upgrade_compatibility.py`): "Schema-Marke 2 -> 3 unter D-30-02 / 30-CONTEXT 'Folge für Phase 30', Bestand ohne cs baut nicht um, bewiesen durch LEGACY_SCHEMA_STEPS ("2","3") und CI-Leg Store upgrade 5".

## Standard Stack

### Core (alles vorhanden, keine neue Python-Abhängigkeit)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tantivy (tantivy-py) | 0.26.2 (gepinnt) | Kette `Tokenizer.simple` -> `Filter.lowercase` -> `Filter.ascii_fold` -> `Filter.custom_stopword` -> `Filter.remove_long` | Alle Filter bereits im Repo genutzt; Faltung der tschechischen Diakritika gemessen [VERIFIED: lokale Messung, Banner "tantivy v0.26.2, index_format v7"] |
| Debian `tesseract-ocr-ces` | 1:4.1.0-2, main, Architecture all, Quelle `tesseract-lang` | OCR-Modell Tschechisch | Gleiche Quelle und Signaturkette wie die neun vorhandenen Packs; Download 1411716 Byte [VERIFIED: api.ftp-master.debian.org madison, packages.debian.org/trixie] |
| Lucene `cz/stopwords.txt` | Tag `releases/lucene/10.5.2` (04.10.2026), Datei unverändert seit Commit `e8e4245d9b36123446546ff15967ac95429ea2b0` (17.04.2012) | Tschechische Stoppwortquelle (D-30-02) | 172 Zeilen, 171 eindeutig (Duplikat `ji`), UTF-8, ohne Kopfzeile; SHA-256 der Datei `61f06aa1e7567ee8c72e895ea33229033669ac1cc52c6d40369a9ee2b76ad915` (identisch auf `main` und Tag 10.5.2) [VERIFIED: GitHub raw + API] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Lucene-Liste | stopwords-iso `cs` | Gesperrt durch D-30-02 |
| Eigene stemmerlose Fabrik | Tschechisch in `LANGUAGE_ALLOWLIST` | Gesperrt: `Filter.stopword("czech")`/`stemmer` existiert in tantivy nicht, ValueError-Pfad |
| Lucene `CzechStemFilter` nachbauen | eigener Light-Stemmer | Deferred: wäre ein eigener Stemmer mit eigener Pflege; CZ-03 dokumentiert stattdessen die Grenze |

**Installation:** keine pip/uv-Änderung. Dockerfile: eine apt-Zeile `tesseract-ocr-ces=1:4.1.0-2 \` im bestehenden Block zwischen `est` und `osd`, plus `&& tesseract --list-langs 2>&1 | grep -qx ces \`.

## Package Legitimacy Audit

Diese Phase installiert kein PyPI/npm-Paket. slopcheck ist daher nicht anwendbar und wurde nicht ausgeführt.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| tesseract-ocr-ces | Debian trixie (main) | in Debian seit oldoldstable, 1:4.1.0-2 in stable/testing/unstable | n/a | salsa/tesseract-lang, upstream tesseract-ocr/tessdata_fast | n/a (Distributionspaket) | Approved, Pin `1:4.1.0-2` |
| Lucene cz/stopwords.txt | Datei aus apache/lucene, vendored als abgeleitete Daten | Datei seit 2012 unverändert | n/a | github.com/apache/lucene | n/a | Approved (Owner D-30-02) |

**Packages removed:** keine. **Flagged:** keine.

## Architecture Patterns

### System Architecture Diagram

```
Admin setzt FINDLING_LANGUAGES (z. B. de,en,cs) und/oder FINDLING_OCR_LANGUAGES (z. B. deu+ces)
        |  (AppAPI-Deploy-Env, wirksam nach Container-Neustart)
        v
config._languages()  --filtert gegen-->  SUPPORTED_LANGUAGES (+ "cs" am Ende)
config._ocr_languages() --filtert gegen--> OCR_LANGUAGE_ALLOWLIST (+ "ces")
        |
        v
Start: expected_versions(... languages="de,en,cs") ----> Store.version_mismatch
        |                                                   |
        |   schema 2 vs 3 -> LEGACY_SCHEMA_STEPS: keine Drift
        |   languages de,en vs de,en,cs -> Drift (nur wenn cs neu)
        v                                                   v
  keine Drift: Poller läuft weiter              Drift in MARKS_A_REBUILD_ANSWERS
  auf altem 13-Felder-Verzeichnis               -> rebuild_the_index (Bandlauf)
  (body_cs wird stumm verworfen,                   open_index(source), open_index(target=build_schema, 14 Felder)
   wenn cs aktiv ohne Umbau)                       _document_from: body_de -> body_cs durch Kette "cs"
                                                   swap_in -> stamp_after_swap(schema 3, de,en,cs)
        |                                                   |
        v                                                   v
Lesehälfte: field_plan_for(marks, index)
   _of_the_marks: schema in {2,3}? -> Körperfelder aus Sprachmarke (+ body_cs bei cs)
   _probed: wirft jedes Feld raus, das das Verzeichnis nicht hat
        v
build_query (BODY_BOOST["cs"]) -> tantivy -> RRF mit Vektoren -> PHP-Recheck -> Unified Search

OCR-Pfad: Scan -> Tesseract -l <FINDLING_OCR_LANGUAGES inkl. ces> -> Text -> wie oben
```

### Recommended Project Structure (neue/berührte Dateien)
```
backend/src/findling/
├── config.py                # SUPPORTED_LANGUAGES +cs, neue Menge STEMMERLESS_LANGUAGES ({"cs"}), TESSERACT_NAME cs->ces,
│                            # OCR_LANGUAGE_ALLOWLIST +ces, SCHEMA_VERSION 3
├── index/schema.py          # FIELD_BODY_CS, FIELDS, BODY_FIELD["cs"], add_text_field(stored=False, tokenizer "cs")
├── index/analyzer.py        # TOKENIZER_CS, czech_analyzer() (eigene Fabrik, kein Snowball)
├── index/stopwords_cs.py    # NEU: gefaltete ASCII-Tupel + Herkunft (Tag, Commit, SHA-256 Original) + Hash-Funktion
├── index/open.py            # register_tokenizer(TOKENIZER_CS, czech_analyzer()) unbedingt
├── store/repo.py            # LEGACY_SCHEMA_STEPS
├── api/resources.py         # _of_the_marks akzeptiert 2 und 3
└── query/rewrite.py         # BODY_BOOST["cs"] = 0.6
scripts/dev/czech_stopwords.py   # NEU: Generator (liest Original, prüft SHA-256, faltet mit tantivy, gibt Tupel aus)
docs/czech-analyzer.md           # NEU (Muster docs/dutch-analyzer.md), oder Abschnitt in language-analyzers.md
```

### Pattern 1: Stemmerlose Kettenfabrik außerhalb von SNOWBALL_NAME
**What:** `czech_analyzer()` baut `simple -> lowercase -> ascii_fold -> custom_stopword(CZECH_STOPWORDS_FOLDED) -> remove_long(48)`. Kein `Filter.stopword(...)`, kein `Filter.stemmer(...)`, also kein Kontakt zu `LANGUAGE_ALLOWLIST`.
**When to use:** jede Sprache ohne tantivy-Snowball.
**Allowlist-Gegenprobe grün halten:** `test_every_product_language_stands_in_the_allowlist` rechnet heute `SUPPORTED_LANGUAGES - SNOWBALL_NAME` und verlangt leer; `test_the_thirteen_hold_and_the_six_are_a_true_subset` verlangt `len(SUPPORTED_LANGUAGES) == 6`. Beide müssen umgebaut werden auf: `set(SUPPORTED_LANGUAGES) == set(SNOWBALL_NAME) | STEMMERLESS_LANGUAGES`, die beiden Teilmengen disjunkt, `STEMMERLESS_LANGUAGES` und `LANGUAGE_ALLOWLIST` disjunkt (sonst würde jemand später "czech" in die Allowlist schreiben), Länge 7. Die Gegenprobe gegen die laufende Engine (`test_every_offered_language_is_carried_by_the_running_tantivy`) bleibt unverändert. Zusätzlich ein Fall: `snowball_analyzer("czech")` wirft weiterhin ValueError. [VERIFIED: codebase `tests/test_language_allowlist.py:73-123`]
**Example (Form, gemessen):**
```python
# Source: lokale Messung 2026-10-10 gegen tantivy 0.26.2, Filter wie in analyzer.py
def czech_analyzer() -> TextAnalyzer:
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.custom_stopword(list(CZECH_STOPWORDS_FOLDED)))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .build()
    )
```
Gemessene Ausgaben dieser Form (mit voller gefalteter Lucene-Liste):
- `"Smlouvě smlouve SMLOUVĚ smlouva"` -> `smlouve, smlouve, smlouve, smlouva` (Akzentpaar eint, Flexionspaar nicht)
- `"ŘÍJEN Říjen rijen"` -> `rijen` x3
- `"Žluťoučký kůň úpěl ďábelské ódy"` -> `zlutoucky, kun, upel, dabelske, ody` (alle Diakritika gefaltet: č ř š ž ý á í é ů ú ě ň ď ť ó)
- `"Proč proc už uz"` -> leer
- `"Nájemní smlouva na byt, být či nebýt"` -> `najemni, smlouva, nebyt` (**`byt` = "Wohnung" verschwindet**, siehe Pitfall 3)
- `"smluvní strana"` -> `smluvni` (**`strana` steht in der Lucene-Liste**)

### Pattern 2: Supplement-Logik für Tschechisch (D-30-02 "nach der Faltung")
Bei den Snowball-Sprachen gibt es zwei Listen, weil die eingebaute Liste Akzente trägt und nach der Faltung nicht mehr greift; das Supplement ergänzt die gefalteten Formen. Für Tschechisch gibt es keine eingebaute Liste. Die Supplement-Logik reduziert sich daher auf EINE Liste: die gefaltete, deduplizierte Lucene-Liste hinter `ascii_fold`. Gemessen: 172 Zeilen, 171 eindeutig, 69 mit Diakritika, nach Faltung 169 eindeutig, alle ASCII (Kollisionen innerhalb der Liste nur `ji`/`jí` -> `ji`, `již`/`jíž` -> `jiz`). 66 gefaltete Formen sind selbst kein Listeneintrag (z. B. `byt`, `uz`, `proc`, `ktery`, `tema`, `vice`, `zpravy`, `prvni`, `nove`, `novy`, `clanku`, `clanky`). [VERIFIED: lokale Messung]
Ablage: `index/stopwords_cs.py` mit ASCII-Tupel (Akzentregel in `src` bleibt gewahrt), Digest des gefalteten Tupels als Test-Konstante (Muster `FOLDED_SUPPLEMENT_SHA256`), SHA-256 des Originals im Docstring und im Generator. Der Digest ist KEIN Versionsmerkmal (siehe Muster-Docstring `stopwords.py`).

### Pattern 3: Kein achtes Merkmal für die tschechische Liste
`wordlist_hash_nl` existiert, weil die niederländische Liste aus einem Debian-Paket kommt, das mit dem Image driften kann. Die tschechische Liste liegt im Quelltext und ändert sich nur per Commit; ein Digest-Gate macht jede Änderung rot. Ein achtes Merkmal würde `expected_versions`, `_MARKS_OF_A_DIRECTORY`, `stamp_a_new_directory`, `stamp_after_swap`, `MARKS_A_REBUILD_ANSWERS`, den Seed-Skip, eine Legacy-Regel in `repo.py`, `ALL_MARKS` und die CI-Snapshots berühren. Empfehlung: kein achtes Merkmal; Docstring hält fest, dass eine spätere Listenänderung eine Markenentscheidung braucht. [ASSUMED: Empfehlung, Owner kann anders entscheiden]

### Pattern 4: OCR-Sprache wie Plan 16-10
Exakt die Bauform von 16-10: Pin-Zeile, `--list-langs`-Prüfung, `OCR_LANGUAGE_ALLOWLIST` 9 -> 10, `OCR_DEFAULT_LANGUAGES` bleibt `deu, eng, fra` (Gate `test_the_default_stays_at_three...`), THIRD-PARTY.md-Tabelle der später zugekommenen Packs um `ces` mit Datum, Größe und Prüfquelle, `docs/ocr.md`, die `FINDLING_OCR_LANGUAGES`-Beschreibung in `backend/appinfo/info.xml` ("today are deu ... est" + ces), READMEs (de/en/fr) mit "neun" -> "zehn Sprachen". `TESSERACT_NAME["cs"] = "ces"` ist Pflicht, weil `test_every_body_language_has_a_tesseract_name_and_every_name_is_installed` jeden Code von `SUPPORTED_LANGUAGES` gegen `TESSERACT_NAME` und die Allowlist hält: CZ-01 muss vor oder mit dem `SUPPORTED_LANGUAGES`-Eintrag landen. [VERIFIED: codebase `tests/test_ocr_languages.py:114-184`, `config.py:400-429`]

### Anti-Patterns to Avoid
- **`"czech"` in `LANGUAGE_ALLOWLIST` oder `SNOWBALL_NAME`:** tantivy 0.26.2 kennt die Sprache nicht, ValueError beim Start.
- **`cs` nur bei aktiver Sprache registrieren:** jedes `add_document` auf einem 14-Felder-Verzeichnis bricht.
- **`cs` irgendwo außer am Ende von `SUPPORTED_LANGUAGES`:** die Normalisierung der Sprachmarke iteriert über diese Reihenfolge. Für Installationen ohne `cs` wäre jede Position neutral, aber `BODY_FIELD`-Reihenfolge = Schemafeldreihenfolge = Anzeige-Reihenfolge; Anhängen hält alle vorhandenen Listen byte-gleich. Folge: normalisierte Marke `de,en,cs`, nicht `cs,de,en`.
- **`body_cs` gespeichert:** nein, wie alle Körperfelder außer `body_de` (`stored=False`), sonst doppelter Store.
- **Akzentliterale in `src`:** Projektregel; Akzente nur in Tests als Daten.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Akzentfaltung | eigene `unicodedata`-Zerlegung im Index | `Filter.ascii_fold()` | Gemessen vollständig für Tschechisch; eine zweite Faltung wäre ein zweiter Textraum |
| Gefaltete Stoppliste | Handabschrift | Generator-Skript, das das Original per SHA-256 prüft und mit derselben tantivy-Kette faltet | Muster `scripts/dev/stopword_supplement.py`; Handkopie driftet |
| Schema-Kompatibilität | Zahlenvergleich `int(stored) < int(expected)` | Paare in `LEGACY_SCHEMA_STEPS` | Ratsche des Repos, ausdrücklich so dokumentiert |
| Umbau | neuer Reindex-Pfad | vorhandener Bandlauf `rebuild_the_index` | Re-Analyse aus `body_de`, wiederaufnehmbar, getestet |
| Tschechisch-Stemming | eigener Stemmer | keiner (CZ-03 dokumentiert die Grenze) | Owner-Entscheid; Stemmer wäre eigene Pflege und eigener Merkmalsweg |

**Key insight:** Alles, was diese Phase braucht, existiert als Muster im Repo (16-10, 17-03, 18-01, 18-05, 21-05). Neu ist nur die stemmerlose Kettenart und der erste Schemaschritt mit Nicht-Legacy-Sprachmarken im Feld.

## Runtime State Inventory

(Schema-/Migrationsphase, daher ausgefüllt.)

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `state.db` meta `schema_version` = `2` auf jeder 1.3/1.4-Installation, `1` auf nie umgebauten 1.2.x; tantivy-Verzeichnisse mit persistiertem 13- bzw. 9-Felder-Schema; halb gefüllte `index.rebuild`-Ziele mit `.rebuild-for`-Fingerabdruck | Code-Änderung (`LEGACY_SCHEMA_STEPS`, `_of_the_marks`), KEINE Datenmigration. Halb gefüllte Ziele mit altem Fingerabdruck werden durch `_make_the_target_fit_this_code` verworfen (erwartete Marke enthält jetzt `3`), Lauf beginnt neu: akzeptabel, im Plan benennen |
| Live service config | AppAPI-Registrierung trägt `FINDLING_LANGUAGES`/`FINDLING_OCR_LANGUAGES` als Env der Registrierung; Admins müssen `cs`/`ces` selbst setzen | Keine Aktion; Doku nennt den Neustart |
| OS-registered state | Keine (Container, keine Systemdienste) | None, verifiziert durch Architektur (ExApp-Container) |
| Secrets/env vars | Keine neuen Variablen; Werte `cs`/`ces` sind neue gültige Inhalte bestehender Variablen | None |
| Build artifacts | Docker-Image bekommt ein Paket (+1,4 MB Download); `PACKAGE_TREE_HASH_TODAY`/`PACKAGE_FILES_TODAY` (73 -> 74 mit `stopwords_cs.py`) und `PHP_TREE_HASH_TODAY` (falls `php/appinfo/info.xml` berührt wird) in `test_measurement_scripts.py` | Je Commit, der `backend/src/findling` oder `php/` berührt, Pin + Journalzeile im selben Commit |

**Downgrade-Hinweis:** Eine frische 1.5-Installation (14 Felder) auf 1.4.2 zurückgesetzt registriert keinen Tokenizer `cs`; jedes `add_document` des 1.4.2-Pollers bricht, bis dessen Bandlauf (Schema 3 vs 2 ist dort eine Drift) ein 13-Felder-Verzeichnis gebaut hat. Als bekannte Grenze dokumentieren, nicht bauen. [VERIFIED: Code-Lesung; ASSUMED: Verhalten von 1.4.2 im Detail nicht ausgeführt]

## Common Pitfalls

### Pitfall 1: Stiller Verlust von es/it/nl/pt nach dem Schemasprung
**What goes wrong:** `_of_the_marks` vergleicht die Schemamarke wörtlich mit `SCHEMA_VERSION`; gespeichert `2` gegen `3` ergibt `None`, `field_plan_for` fällt auf `LEGACY_PLAN` (de,en).
**Why it happens:** Bei 1 auf 2 war der Rückfall korrekt, weil 1.2.x nur de,en kannte. Bei 2 auf 3 tragen Bestandsinstallationen andere Sprachen.
**How to avoid:** Abfragbare Generationen als benannte Menge (`{"2","3"}`); Test: Verzeichnis mit 13-Felder-Schema, Marken `2` + `de,en,es`, Code mit Schema 3 -> Feldplan enthält `body_es`, nicht `body_cs`; `plan_falls_short` ist False.
**Warning signs:** Adminseite zeigt `languagesActive` mit `es`, aber `searched_languages` nur `de,en`.

### Pitfall 2: Roadmap-Beispiel "smlouva / Smlouvě" ist kein Akzentpaar
**What goes wrong:** Ein Test mit Dokument `Smlouvě` und Frage `smlouva` wird rot, weil ohne Stemmer `smlouve` != `smlouva`.
**How to avoid:** Akzentpaare derselben Form: `smlouvě`/`smlouve`/`SMLOUVĚ`, `řízení`/`rizeni`, `účetní`/`ucetni`. Das Flexionspaar `smlouva`/`smlouvě` gehört als Negativfall in die CZ-03-Grenze (zwei Terme, gemessen).

### Pitfall 3: Faltung macht Stoppwörter zu Inhaltswörtern (`být` -> `byt` = Wohnung)
**What goes wrong:** Die gefaltete Liste entfernt `byt` (Wohnung), ein häufiges Wort in Mietverträgen ("nájemní smlouva na byt"). Unabhängig von der Faltung enthält die Lucene-Liste Inhaltswörter aus einem Nachrichtenkorpus: `strana` (u. a. "smluvní strana" = Vertragspartei), `zprávy`, `článku`, `články`, `první`, `nový`, `nové`, `téma`, `tipy`, `napište`, `dnes`, `zpět`, `pravé`, sowie `cz`, `re`, `neg`, `pta`.
**Why it happens:** Lucenes CzechAnalyzer filtert ungefaltet (StopFilter vor dem Stemmer, kein Folding), dort ist `byt` kein Stoppwort; erst unsere Faltung erzeugt die Kollision. Die Inhaltswörter stehen so im Original.
**How to avoid:** Owner-Frage (Open Question 1). Gemildert wird es dadurch, dass auf Instanzen mit `de` oder `en` dieselben Wörter über `body_de`/`body_en` weiter gefunden werden; nur Instanzen ohne beide verlieren sie ganz.
**Warning signs:** Frage `byt` liefert auf einer `cs`-only-Instanz nichts.

### Pitfall 4: "Stoppwörter erzeugen keine Treffer" ist auf dem normalen Suchweg mit `de`/`en` nicht wahr
**What goes wrong:** Der Feldplan fragt alle aktiven Körperfelder; `proč` wird von `body_de` roh (`proč`) und von `body_en` als `proc` indexiert. Gemessen. Ein Suchweg-Test für Stoppwörter auf `de,en,cs` ist rot oder beweist das Falsche.
**How to avoid:** Stoppwort-Kriterium auf Feldebene (Kette `cs` liefert leere Tokenliste für beide Schreibweisen jedes Listeneintrags, Muster `test_no_built_in_stop_word_reaches_the_index_in_either_spelling`) und ggf. mit einer Instanz nur `cs`. SC2 im Verifier so lesen.

### Pitfall 5: CI-Beweis grün aus dem falschen Grund
**What goes wrong:** `body_en` faltet Tschechisch bereits (`smlouvě` und `smlouve` -> `smlouv`, gemessen). Ein Sprachbeweis auf `de,en,cs` trifft auch ohne `cs`-Kette.
**How to avoid:** Den `cs`-Beweis auf eine Menge ohne `en` legen, z. B. "Store upgrade 6" mit `REBUILD_LANGUAGES='cs,de'` -> normalisiert `de,cs`. `de` faltet nicht (`smlouvě` bleibt `smlouvě` nach dem deutschen Stemmer, gemessen ohne Komposita-Liste), also kann nach dem Umbau nur `body_cs` die Frage `smlouve` gegen ein Dokument `smlouvě` beantworten. Zusätzlich Vorbedingung `languagesActive == de,cs` und `searched_languages` ohne `en` prüfen.

### Pitfall 6: Upgrade-CI auf v1.4.2 erbt 1.3.2-spezifische Saat
**What goes wrong:** `UPGRADE_FROM_TAG` steht auf `v1.3.2`. "Store upgrade 2b" sät zwei Dateien, die 1.3.2 falsch beurteilt, "3c" verlangt, dass die Recheck-Marke `recheck_1_4_0` vor dem Upgrade FEHLT, "5" wartet auf ihren Abbau. Eine 1.4.2-Installation hat den Recheck schon erledigt ("done"); 3c bricht mit "already carries the recheck mark".
**How to avoid:** Beim Umzug auf `v1.4.2` 2b/3c/5 auf den neuen Ausgangspunkt umschreiben (Recheck-Zusicherungen als "bleibt done, bewegt nichts" statt "wird abgebaut"), Kommentar-Chronik am `UPGRADE_FROM_TAG` fortschreiben. Phase 31 (FMT-06) braucht in derselben Strecke eine neue Saat (`legacy_format`-Dateien), daher 2b so schneiden, dass Phase 31 andocken kann. Gleiche Version im Baum (1.4.2) ist zulässig, der Gleichstands-Zweig von "Store upgrade 4" existiert und das Image kommt aus dem Commit.

### Pitfall 7: Drei exakte Sprachzeichenketten in deploy-harp.yml
**What goes wrong:** Zeile 700 (`sed` auf `de,en,es,it,nl,pt`), 910 (Vorbedingung `languagesActive`), 4288/4293 (Rückbau auf `de,en`) prüfen genau diese Zeichenkette. Wird der Sprachbeweis um `cs` erweitert, müssen alle drei Stellen gemeinsam auf `de,en,es,it,nl,pt,cs` wandern.
**How to avoid:** Entweder alle drei in einem Commit, oder die Sprache-Proof-Strecke bewusst bei sechs Sprachen lassen und `cs` nur in Store upgrade 6/7 beweisen (empfohlen, wegen Pitfall 5 ist `cs` im Sechs-plus-eins-Beweis ohnehin nicht trennscharf).

### Pitfall 8: Store upgrade 6 erwartet Schemamarke 2 vor und nach dem Umbau
**What goes wrong:** Assurance 1 (Zeile 5263 bis 5278) verlangt `2` auf beiden Seiten. Nach dem Sprung baut der Bandlauf ein Schema-3-Verzeichnis und stempelt `3`.
**How to avoid:** Assurance 1 auf "2 vor dem Umbau, 3 danach" drehen (so lautete sie bis Plan 29-13 für 1 -> 2), Summary-Zeile 5438 ebenso. "Store upgrade 5" Assurance 2 (`schemaVersion` unverändert nach dem reinen Upgrade) bleibt richtig: ohne Umbau bleibt `2` stehen.

### Pitfall 9: Feste Feldzahlen in Tests
`test_index_open.py` (`len(FIELDS) == 13`, Zeilen 187-207, 443; `len(BODY_FIELD) + 2 == EXPECTED_REGISTRATIONS`, 682), `conftest.py` (Fixture des 13-Felder-Schemas, Zeilen 247/487), `test_schema_generations.py` (nur `FIELDS_SCHEMA_1`), `test_upgrade_compatibility.py` (`GOLD_V1_3`, "exactly one step"). Neu: eingefrorene `FIELDS_SCHEMA_2` (13 Namen) + Fixture `schema_2_index`, Inklusionstests gegen Schema 3, `GOLD_V1_5` mit `schema_version: "3"`, Schrittprüfung `GOLD_V1_5` gegen `GOLD_V1_3` = 1. Das alte "1 -> 2"-Gold bleibt als Zeuge stehen.

### Pitfall 10: Grenzliste D-06 fixiert vier Einträge
`LIMITATION_COUNT = 4` in `test_store_metadata.py`, und `docs/language-analyzers.md` sagt "D-06 fixes the short list at four entries". ROADMAP SC5 verlangt den Eintrag "in der Grenzliste", also fünf. Das ist eine neue Owner-Festlegung (Roadmap), im Kommentar so zitieren; Änderung an beiden info.xml in drei Sprachen plus `docs/store-listing.md`-Entwurf. `php/appinfo/info.xml` liegt unter `php/` und bewegt `PHP_TREE_HASH_TODAY`.

## Code Examples

### Legacy-Schritt und abfragbare Generationen
```python
# store/repo.py (Form; Begründung je Paar im Kommentar, wie bei ("1","2"))
LEGACY_SCHEMA_STEPS: Final = frozenset({("1", "2"), ("2", "3"), ("1", "3")})

# api/resources.py
# Generations whose directory answers a plan built from its own marks; the probe
# (_probed) drops any name the directory does not carry.
QUERYABLE_SCHEMA_GENERATIONS: Final = frozenset({"2", str(SCHEMA_VERSION)})

def _of_the_marks(marks: Mapping[str, str]) -> FieldPlan | None:
    if marks.get(SCHEMA_MARK) not in QUERYABLE_SCHEMA_GENERATIONS:
        return None
    ...
```

### Generator für die gefaltete Liste (Form)
```python
# scripts/dev/czech_stopwords.py (Form)
SOURCE_URL = ("https://raw.githubusercontent.com/apache/lucene/releases/lucene/10.5.2/"
              "lucene/analysis/common/src/resources/org/apache/lucene/analysis/cz/stopwords.txt")
SOURCE_SHA256 = "61f06aa1e7567ee8c72e895ea33229033669ac1cc52c6d40369a9ee2b76ad915"
# read (local copy or URL), verify SHA-256, fold every entry with the same
# lowercase+ascii_fold chain the index uses, keep first appearance order, drop
# duplicates, print the tuple for index/stopwords_cs.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Schema mit sechs Körperfeldern, Marke 2 | sieben Körperfelder, Marke 3, Legacy-Paare | Phase 30 | Kein Umbau ohne `cs` |
| Alle Sprachen über `snowball_analyzer` | zusätzliche stemmerlose Kettenart | Phase 30 | Allowlist-Tests prüfen jetzt zwei disjunkte Mengen |
| `UPGRADE_FROM_TAG: v1.3.2` | `v1.4.2` | Phase 30 | 2b/3c/5 neu ableiten |

**Deprecated/outdated:** Die Aussage in `schema.py` "the schema carries all six body fields at all times" und die Zahl "thirteen" in Modul- und Testtexten werden zu sieben/vierzehn; `info.xml` "Comma separated, out of de, en, es, it, nl and pt" bekommt `cs`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Kein achtes Merkmal für die tschechische Liste nötig | Pattern 3 | Spätere Listenänderung ohne Umbau unsichtbar; Gegenmittel Digest-Gate |
| A2 | `GROWTH_PER_LANGUAGE = 0.40` deckt auch die stemmerlose Kette (mehr eindeutige Terme als Snowball) | Rebuild-Vorprüfung | Vorprüfung zu knapp, Lauf läuft voll; im Plan einmal messen (Muster Messung 2026-09-24, 2000 Dokumente) |
| A3 | `BODY_BOOST["cs"] = 0.6` wie die anderen Ausbausprachen | rewrite.py | Rangfolge; Gate `test_field_plan_ranking.py` verlangt nur `< en` |
| A4 | Bewertung Alternative B (kein Schemasprung) als schlechter | Kernfrage 1 | gering |
| A5 | Phase 32 (Ordnerfilter USRCH-02) braucht kein Schemafeld, weil `state.db` eine `path`-Spalte hat (schema.sql:44) und `path` im Index nur gespeichert, nicht indexiert ist; Filterung als Store-Vorfilter wie `prefilter_visible` | SC4 | Wenn Phase 32 doch einen tantivy-Pfadfilter will, wäre das ein zweiter Schemaschritt nach Phase 30. Im Plan als ausdrückliche Prüfzeile aufnehmen |
| A6 | Downgrade-Verhalten 1.5 -> 1.4.2 wie beschrieben | Runtime State | nur Doku |

## Open Questions

1. **Lucene-Liste wörtlich oder mit benannter Ausschlussliste?**
   - What we know: Faltung macht `být` zu `byt` (Wohnung); Original enthält `strana`, `zprávy`, `první`, `nový` u. a.
   - What's unclear: ob der Owner D-30-02 wörtlich meint.
   - Recommendation: Owner-Checkpoint im ersten Plan. Vorschlag: Liste wörtlich übernehmen, aber `byt` (Faltungskollision, entsteht erst durch uns) per benannter, getesteter Ausnahme nicht filtern; die Nachrichtenwörter (`strana` usw.) als dokumentierte Grenze stehen lassen, weil sie dem Original entsprechen.
2. **Grenzliste auf fünf Einträge** (D-06 vs. ROADMAP SC5): Empfehlung, SC5 als neue Owner-Festlegung lesen und den Wortlaut des fünften Eintrags (en/de/fr) im Plan vorlegen, z. B. "Czech: no stemming, inflected forms are separate words".
3. **Umbau "in beide Richtungen" in CI:** Empfehlung: Store upgrade 6 `de,en` -> `de,cs` (cs an, en ab, Schema 2 -> 3, Frage `smlouve` trifft Dokument `smlouvě`), neuer Schritt Store upgrade 7 `de,cs` -> `de,en` (cs ab, Schema bleibt 3, `smlouve` trifft wieder über `body_en`, Sprachmarke `de,en`). Kosten: ein weiterer Container-Neustart. Alternativ "Aus"-Richtung nur in pytest; Owner-Kriterium SC3 spricht von CI, beides zählt, Empfehlung deploy-harp.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv + Python 3.13 venv (backend/.venv) | Tests, Generator | ✓ | tantivy 0.26.2 importierbar | n/a |
| tesseract lokal (Windows) | `ces`-Smoke | ✗ (nicht geprüft, Windows-Host) | n/a | Bau-Prüfung im Image (`--list-langs`) + CI `docker.yml`; lokaler Scan-Test nur im Container |
| Docker/WSL2 | Image-Bau lokal | nicht geprüft | n/a | CI-Bau |
| GitHub-Zugriff (raw/api) | Lucene-Quelle | ✓ | n/a | n/a |

**Missing dependencies with no fallback:** keine.

## Validation Architecture

(`workflow.nyquist_validation` ist in `.planning/config.json` `false`; der Abschnitt steht auf ausdrücklichen Wunsch des Orchestrators.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (backend), plus Gates ruff/pyright/vulture |
| Config file | `backend/pyproject.toml` |
| Quick run command | `cd backend && uv run pytest -q tests/test_language_allowlist.py tests/test_language_analyzers.py tests/test_ocr_languages.py tests/test_schema_generations.py tests/test_upgrade_compatibility.py -x` |
| Full suite command | `cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run vulture src tests --min-confidence 80 && uv run pytest -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CZ-01 | `ces` hat Pin-Zeile und `--list-langs`-Prüfung, Allowlist 10, Standard bleibt 3, `TESSERACT_NAME["cs"]` | unit (Textleser) | `uv run pytest -q tests/test_ocr_languages.py` | ✅ (erweitern) |
| CZ-01 | Scan in Tschechisch liefert Treffer | integration (Image) | CI `docker.yml`/`deploy-harp` mit `FINDLING_OCR_LANGUAGES=deu+ces` und einer tschechischen Testseite | ❌ Wave 0: Fixture-Scan (selbst erzeugt, Lizenz eigen) |
| CZ-02 | Kette: Akzentpaare einen, Stoppwörter in beiden Schreibweisen leer, kein Stemmer, Reihenfolge der Filter | unit | `uv run pytest -q tests/test_czech_analyzer.py` | ❌ Wave 0 |
| CZ-02 | Gefaltete Liste = Generator-Ausgabe, Digest fest, Original-SHA im Docstring | unit | `uv run pytest -q tests/test_czech_analyzer.py -k digest` | ❌ Wave 0 |
| CZ-02 | Allowlist-Parität mit stemmerloser Menge, `snowball_analyzer("czech")` wirft | unit | `uv run pytest -q tests/test_language_allowlist.py` | ✅ (umbauen) |
| CZ-02 | Upgrade ohne cs: keine Drift, Feldplan behält es/it/nl/pt auf Schema-2-Verzeichnis | unit/integration | `uv run pytest -q tests/test_schema_generations.py tests/test_upgrade_compatibility.py tests/test_store_repo.py` | ✅ (erweitern, Fixture `schema_2_index` neu) |
| CZ-02 | Umbau an/aus über Bandlauf, Stempel 3, `body_cs` gefüllt/leer | integration (echtes tantivy) | `uv run pytest -q tests/test_index_rebuild.py -k czech` | ✅ (erweitern) |
| CZ-02 | Bestand 1.4.2 baut nicht um; cs-Umbau beide Richtungen | e2e CI | `deploy-harp` Store upgrade 5/6/7 | ✅ (umbauen) |
| CZ-03 | Grenze in docs + Kurzliste = beide info.xml, drei Sprachen | unit (Textleser) | `uv run pytest -q tests/test_store_metadata.py` | ✅ (`LIMITATION_COUNT` 5) |
| alle | Baumhash-Pins | unit | `uv run pytest -q tests/test_measurement_scripts.py` | ✅ (je Commit nachziehen) |

### Sampling Rate
- **Per task commit:** Quick run command plus `tests/test_measurement_scripts.py`
- **Per wave merge:** Full suite command
- **Phase gate:** Full suite grün plus ein deploy-harp-Lauf mit Laufnummer vor `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_czech_analyzer.py` (Kette, Liste, Digest, Akzentpaare, Flexionspaar als CZ-03-Negativfall, `byt`-Entscheid)
- [ ] Fixture `schema_2_index` in `backend/tests/conftest.py` und `FIELDS_SCHEMA_2` in `test_schema_generations.py`
- [ ] Tschechische OCR-Testseite (selbst gerendert) für den Image-Beweis
- [ ] `scripts/dev/czech_stopwords.py` (Generator) samt ruff-Gate für `scripts/`

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a |
| V3 Session Management | no | n/a |
| V4 Access Control | yes (unverändert) | PHP-Recheck jeder Trefferliste; Feldplan ändert keine Rechte |
| V5 Input Validation | yes | `_languages()` filtert gegen geschlossene Menge; `_ocr_languages()` gegen `OCR_LANGUAGE_ALLOWLIST` (Subprozess-Argumentgrenze T-03-502) |
| V6 Cryptography | no | SHA-256 nur als Herkunftsdigest |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Argument-Injektion in tesseract über `FINDLING_OCR_LANGUAGES` | Tampering | Allowlist, Liste statt Shell (unverändert, nur `ces` ergänzt) |
| Gefälschte/manipulierte Stoppliste (Supply Chain) | Tampering | SHA-256 des Originals im Generator, Digest-Gate der gefalteten Liste |
| Markenlüge nach Umbau (Index behauptet aktuell zu sein) | Repudiation/Integrity | Stempel nur hinter dem Tausch (`stamp_after_swap`), Seed überspringt Sprachmarke |
| Stiller Feldverlust (Pitfall 1) | Denial of Service (funktional) | `_of_the_marks`-Fix + Test + `plan_falls_short` |
| Log-Leck von Inhalten | Information Disclosure | Kette loggt keine Tokens (bestehende Regel T-02-14) |

## Sources

### Primary (HIGH confidence)
- Codebasis: `backend/src/findling/{config.py, index/schema.py, index/analyzer.py, index/stopwords.py, index/open.py, index/rebuild.py, index/writer.py, store/repo.py, api/resources.py, query/rewrite.py}`, Tests `test_language_allowlist.py`, `test_ocr_languages.py`, `test_upgrade_compatibility.py`, `test_schema_generations.py`, `test_store_metadata.py`, `test_measurement_scripts.py`, `.github/workflows/deploy-harp.yml`, `backend/Dockerfile`, `backend/appinfo/info.xml`, `THIRD-PARTY.md`, `REUSE.toml`, `docs/language-analyzers.md`, Plan-Archiv `16-10-SUMMARY.md`, v1.3-Phasen 17 bis 21
- Lokale Messung 2026-10-10, tantivy 0.26.2 (`backend/.venv`): Faltung, Kettenausgaben, stummes Verwerfen unbekannter Felder, Verhalten von en/de-Ketten auf Tschechisch
- https://api.ftp-master.debian.org/madison?package=tesseract-ocr-ces und https://packages.debian.org/trixie/tesseract-ocr-ces
- https://github.com/apache/lucene, Datei `lucene/analysis/common/src/resources/org/apache/lucene/analysis/cz/stopwords.txt` auf `main` und Tag `releases/lucene/10.5.2`, Commit-Historie per GitHub-API, `CzechAnalyzer.java` und `NOTICE.txt` am Tag 10.5.2

### Lizenzbefund Lucene (HIGH)
- `NOTICE.txt` (Tag 10.5.2) nennt die tschechische Liste nicht gesondert (nur Snowball-, Savoy-, Carrot2-Listen); sie fällt unter die allgemeine ASF-Zeile "Apache Lucene, Copyright 2001-2025 The Apache Software Foundation. This product includes software developed at The Apache Software Foundation". Apache-2.0 §4 verlangt: Lizenztext beilegen (liegt als `LICENSES/Apache-2.0.txt` vor), Hinweise erhalten, geänderte Dateien kennzeichnen (Faltung + Deduplizierung = Änderung, im Docstring und in THIRD-PARTY.md benennen), NOTICE-Attributionszeilen wiedergeben (in THIRD-PARTY.md). REUSE: neue `[[annotations]]` für `backend/src/findling/index/stopwords_cs.py` mit `SPDX-License-Identifier = "AGPL-3.0-or-later AND Apache-2.0"` und `SPDX-FileCopyrightText` inkl. "The Apache Software Foundation" (Muster der App-Icons in `REUSE.toml`).

### Secondary / Tertiary
- keine

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (Paket und Liste per Primärquelle geprüft, keine neuen PyPI-Pakete)
- Architecture: HIGH (Markenkette vollständig im Code verfolgt; Pitfall 1 aus Code-Lesung, nicht ausgeführt, daher im Plan als roter Test zuerst schreiben)
- Pitfalls: HIGH für 2 bis 5 (gemessen), MEDIUM für 6 bis 8 (CI-Text gelesen, nicht ausgeführt)

**Research date:** 2026-10-10
**Valid until:** 2026-11-09 (stabil; Lucene-Datei seit 2012 unverändert, Debian trixie stabil)
