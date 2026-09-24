# Phase 19: Frageseite freischalten - Research

**Researched:** 2026-09-24
**Domain:** tantivy-Query-Aufbau, Feldlisten am Versionsmerker, Rangordnung über sechs Körperfelder, CI-Beweisführung
**Confidence:** HIGH (alles Tragende ist am installierten `tantivy 0.26.2` und am Repo gemessen, nicht erinnert)

## Summary

Die Frageseite ist heute genau eine Zeile: `query/rewrite.py:542` ruft `index.parse_query_lenient(...)`
mit den drei Modulkonstanten `DEFAULT_FIELDS`, `TITLE_ONLY_FIELDS` und `FIELD_BOOSTS`. Phase 19 ersetzt
diese drei Konstanten durch einen **Feldplan**, der aus zwei gespeicherten Marken der Instanz entsteht
(`schema_version` und `languages` aus `state.db`) und nirgendwo aus dem Anfragetext. Das ist der
gesamte fachliche Kern der Phase; alles andere ist Beweisführung.

Drei Dinge sind am 24.09.2026 gemessen worden und ändern die Planung gegenüber jeder Vorannahme.
**Erstens** wirft `parse_query_lenient` die `ValueError` nicht nur für `default_field_names`, sondern
genauso für `field_boosts`: ein Boost auf `body_es` gegen ein Schema-1-Verzeichnis reisst den Suchpfad
identisch auf. Die Boost-Abbildung muss also aus derselben Quelle kommen wie die Feldliste, nicht
danebenstehen. **Zweitens** summiert tantivy die Feldbeiträge (`most_fields`-Verhalten): ein Dokument,
das in fünf Feldern trifft, bekam in der Sonde 2,15 gegen 0,1823 eines Dokuments, das nur in einem
trifft, und Boosts von 0,2 drückten das nur auf 0,5394 gegen 0,1459. Erfolgskriterium 3 ist damit als
"Boosts lösen das Problem" nicht erfüllbar; es ist als "die Boosts der vier neuen Felder liegen
unterhalb `body_en`, und eine Rangprobe belegt, wie weit das trägt" erfüllbar. **Drittens** kommt ein
Treffer, der ausschliesslich über ein neues Sprachfeld gefunden wurde, ohne Textauszug zurück: der
`SnippetGenerator` hängt fest an `FIELD_BODY_DE` (`index/search.py:875`), und die Sonde lieferte für
die Frage `alemanes` gegen das Dokument `alemana` einen Treffer mit leerem Fragment.

Dazu kommt ein Befund zur Beweisbarkeit, der die CI-Planung bestimmt: **für Italienisch gibt es in der
vorhandenen Fixture kein einziges Formenpaar, das nur die italienische Kette zusammenführt**, solange
Englisch aktiv ist (gemessen: 0 von 56 geordneten Paaren; die vierzehn Familien sind reine Akzentpaare,
und die englische Kette faltet ebenfalls). Ein it-Beweis auf dem normalen Suchweg braucht also entweder
eine neue Flexionsfamilie in der Fixture (zwölf von zwölf geprüften it-Flexionspaaren sind "nur it")
oder eine Instanz ohne Englisch.

**Primary recommendation:** Den Feldplan einmal beim Öffnen der Lesehälfte berechnen und auf `ReadSide`
tragen (`api/resources.py`), nicht pro Anfrage und nicht in einem neuen Cache. Dort liegen Index, Store
und Marken bereits zusammen, die Invalidierung durch `reset_read_side()` nach dem Verzeichnistausch
existiert schon, und die Kosten sind ein Meta-Lesevorgang plus vier `doc_freq`-Sonden zu je 0,26 us pro
Öffnung statt pro Tastendruck.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Feldliste und Boosts bestimmen | Python-Backend (`api/resources.py`) | - | Nur dort liegen Index, `state.db` und die Marken in einer Hand; Berechnung einmal je Öffnung |
| Anfrage bauen | Python-Backend (`query/rewrite.py`) | - | Eine Stelle, `parse_query_lenient` wird genau einmal gerufen |
| Sicherheitstor gegen den ValueError-Pfad | Persistenz (`state.db` Marke `schema_version`) | Index (`doc_freq`-Sonde) | Die Marke ist die Zusage, die Sonde ist die Gegenprobe am Verzeichnis selbst |
| Rangordnung über Felder | tantivy BM25 plus `field_boosts` | Fusion (RRF, `index/fusion.py`) | Die Feldsummierung passiert unterhalb von RRF und ist von dort nicht korrigierbar |
| Unified Search ausliefern | PHP-Companion (`php/lib/Search/Provider.php`) | - | Reicht nur den Begriff durch, kennt keine Sprache; keine Änderung nötig |
| Ergebnisseite ausliefern | PHP-Companion (`php/lib/Controller/PageController.php`) | - | Nutzt dieselbe Backend-Route über `SearchService`; keine Änderung nötig |
| Textauszug schneiden | Python-Backend (`index/search.py::snippets_for`) | - | Hängt an `body_de`; bekannte Lücke, siehe Pitfall 4 |
| Anti-Feature absichern | Testebene (Quelltext-Wächter) | Abhängigkeitsliste | Abwesenheit eines Pfades ist nur strukturell beweisbar, nicht funktional |

## Project Constraints (from CLAUDE.md)

Verbindliche Vorgaben aus `./CLAUDE.md`, die der Planer einhalten muss:

| Vorgabe | Auswirkung auf Phase 19 |
|---------|------------------------|
| Python 3.13 + uv, lokales System-Python defekt | Alle Befehle über `uv run` aus `backend/` |
| Qualitätsgates: ruff-Vollregelsatz, pyright basic (`PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture, lokal grün VOR Commit | Jeder Plan braucht diese vier Gates in der Verifikation |
| Code Englisch, Projektkommunikation Deutsch, keine Em-Dashes, echte Umlaute nur in deutscher Prosa und nie in Code | Testnamen, Feldnamen, Kommentare Englisch und ASCII; die Fixture-Dateien sind der einzige Ort mit Akzenten, und das ist dort ausdrücklich erlaubt |
| Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Phasenabschluss fixen | Audit-Plan am Phasenende einplanen |
| Berechtigungs-Durchgriff strikt, keine Inhalte verlassen den Server | Der Feldplan darf die eine Suchroute nicht verdoppeln (siehe `test_semantic_boundary.py`) |
| Launch-Härtung vor Store-Abgabe | Gehört zu Phase 23, nicht hierher |
| Kurze Produkttexte, Owner-Abnahme vor Release | Gehört zu Phase 23 |

Zusätzliche Arbeitsregeln aus dem Phasenauftrag, die in jeden Plan gehören:

- Python-Schreibvorgänge in `.planning`- und Testdateien mit `newline="\n"` (CRLF-Falle).
- Jede Änderung unter `backend/src/findling` oder `php/` zieht `PACKAGE_TREE_HASH_TODAY`
  (`backend/tests/test_measurement_scripts.py:916`) bzw. `PHP_TREE_HASH_TODAY` (Zeile 565) im
  **selben** Commit nach.
- `-k`-Selektoren der Pläne gegen echte Testnamen prüfen, nicht gegen vermutete.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LEX-05 | Die Anfrage durchsucht genau die aktiven Sprachfelder mit Feld-Boosts unterhalb `body_en`; KEINE Spracherkennung, weder dokument- noch anfrageseitig (Anti-Feature, einstimmig) | Pattern 1 (Feldplan aus zwei Marken), Pattern 2 (Boost-Tabelle und was sie leistet), Pattern 5 (struktureller Anti-Feature-Wächter nach dem Muster `test_semantic_boundary.py`), Messung M-3 und M-4 |

## Bindende Vorentscheide (statt CONTEXT.md)

Es gibt **keine** `19-CONTEXT.md`. Die folgenden Entscheide sind trotzdem gesetzt und dürfen nicht neu
aufgemacht werden; sie stammen aus `17-GRUNDSATZ-ENTSCHEID.md` (datiert 23.09.2026) und aus der Roadmap.

### Gesetzte Entscheidungen

- **Keine Spracherkennung**, weder dokument- noch anfrageseitig. Einstimmig, in STATE.md als
  Milestone-tragende Entscheidung geführt. `[CITED: .planning/STATE.md, .planning/research/FEATURES.md Teil 3]`
- **E-17-2 Option a:** Das Schema trägt immer alle sechs Körperfelder; `FINDLING_LANGUAGES` entscheidet
  ausschliesslich die Befüllung. `[CITED: 17-GRUNDSATZ-ENTSCHEID.md]`
- **E-17-3 Option a:** `FINDLING_LANGUAGES` darf Deutsch und Englisch abschalten. Der Feldplan muss
  deshalb auch `body_de` und `body_en` fallen lassen können, nicht nur die vier neuen.
  `[VERIFIED: backend/src/findling/index/writer.py:268-285 sagt das wörtlich voraus]`
- **E-17-4 Option a:** Die Sprachmenge ist sechster Versionsmerker, normalisiert in Schemafeldreihenfolge.
- **Suchfeldmenge ist nicht die Nutzersprache.** Immer alle befüllten Felder, Rangordnung über
  Feld-Boosts. `[CITED: .planning/research/FEATURES.md Frage 3]`
- **`disjunction_max_query` ist NICHT Teil dieser Phase.** Der Entscheid fällt in Phase 22 auf Messbasis
  (MESS-09). Phase 19 darf ihn vorbereiten (Messhaken), aber nicht vorwegnehmen.
  `[CITED: .planning/REQUIREMENTS.md MESS-09, ROADMAP Phase 22 Kriterium 4]`
- **Phase 18 ist die harte Vorbedingung.** Die Feldliste darf sich nur öffnen, wenn die gespeicherte
  `schema_version` sagt, dass der Umbau durch ist.

### Claude's Discretion (Empfehlung in dieser Recherche)

- Wo der Feldplan berechnet und wie er transportiert wird (Empfehlung: `ReadSide`, Pattern 1).
- Konkrete Boost-Werte der vier neuen Felder (Empfehlung: 0,6; Begründung und Messung in Pattern 2).
- Form der Rangprobe (Empfehlung: Pattern 3).
- Ob der it-Fall über eine neue Fixture-Familie oder über eine Instanz ohne Englisch bewiesen wird
  (Empfehlung: Fixture-Familie, Open Question 1).

### Ausserhalb des Scopes

- Niederländische Komposita (Phase 21, eigenes Tor).
- UI-Kataloge (Phase 20, Parallelpfad).
- Messanfahrt und `disjunction_max`-Entscheid (Phase 22).
- Französisches Körperfeld (nach v1.3).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tantivy` | 0.26.2 (`tantivy v0.26.2, index_format v7`) | Query-Parser, BM25, Feld-Boosts, SnippetGenerator | Bereits gepinnt und in Phase 17 als Zusicherung verdrahtet; kein Wechsel in dieser Phase `[VERIFIED: backend/pyproject.toml, `import tantivy; tantivy.__version__` am 24.09.2026]` |

### Supporting

Keine. **Phase 19 installiert kein einziges neues Paket.** Die Phase ist eine Umverdrahtung vorhandener
Module plus Tests plus zwei CI-Schritte.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Feldplan auf `ReadSide` | Modulglobaler Cache mit TTL in `query/rewrite.py` | Zweiter Cache neben `_DEGRADED`/`_FILLED`, zweite Generationsfalle (Audit M-18-02 hat genau diese Klasse Fehler schon einmal gekostet). Abgelehnt. |
| Feldplan aus `schema_version` + `languages` | Feldplan aus `resources.filled_languages()` | `filled_languages()` läuft über das gesamte Term-Wörterbuch je Feld und hängt an einer 30-s-TTL; das ist eine Diagnosefunktion, keine Funktion des Anfragepfads. Siehe Open Question 2. |
| Gespeicherte Marke als Tor | `Searcher.doc_freq(field, value)` als direkte Feldexistenz-Sonde | Die Sonde fragt das Verzeichnis selbst und kostet 0,26 us, kann die Roadmap-Zusage aber nicht ersetzen (Kriterium 2 nennt den Merker). Empfehlung: Marke als Vertrag, Sonde als Gegenprobe beim Öffnen. |
| Boosts senken | `Query.disjunction_max_query` | Löst die Summierung wirklich, kostet aber den Umbau des gesamten Parserpfads (Filterpräfixe, Umlautvarianten, Tiefenwächter) und ist per REQUIREMENTS MESS-09 an eine Messung in Phase 22 gebunden. Nicht hier. |

**Installation:** entfällt, keine neuen Pakete.

## Package Legitimacy Audit

**Diese Phase installiert keine externen Pakete.** Der Abhängigkeitsbaum von `backend/pyproject.toml`
bleibt unverändert; es kommt kein npm-, PyPI- oder crates-Eintrag hinzu. Die Legitimitätsprüfung nach
dem Package-Legitimacy-Gate entfällt damit mangels Gegenstand.

| Package | Registry | Disposition |
|---------|----------|-------------|
| (keine) | - | Keine Installation in dieser Phase |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine

Zur Klarstellung für den Planer: `tantivy==0.26.2` ist in Phase 17 bereits geprüft, gepinnt und in
`THIRD-PARTY.md` geführt; Phase 19 fasst den Pin nicht an.

## Architecture Patterns

### System Architecture Diagram

```
Nutzer tippt in der Unified Search            Nutzer öffnet die Ergebnisseite
        |                                              |
        v                                              v
 php/lib/Search/Provider.php            php/lib/Controller/PageController.php
 (IFilteringProvider, kennt keine Sprache)  (FrontpageRoute, NoCSRFRequired)
        |                                              |
        +--------------------+-------------------------+
                             v
                  php/lib/Service/SearchService.php
                  php/lib/Service/ExAppService.php
                             |
                             |  POST /search   { query, limit, offset, titleOnly, types, sort, ... }
                             |  (SearchRequest: extra="forbid", KEIN Sprachfeld)
                             v
                  backend api/search.py::one_round
                             |
                             |  side = resources.read_side()
                             |         +-- index (tantivy, Verzeichnis auf Platte)
                             |         +-- store (state.db, read only)
                             |         +-- NEU: field_plan  <--- Phase 19
                             v
                  query/rewrite.py::build_query(index, text, plan=...)
                             |
                             |  1. Tiefenwächter (SEARCH_QUERY_MAX_DEPTH)
                             |  2. carried_operators / carries_one_term (Rohzeile)
                             |  3. extract_filters (type:)  -> Erweiterungen
                             |  4. add_umlaut_variants
                             |  5. parse_query_lenient(default_field_names=plan.fields,
                             |                         field_boosts=plan.boosts, ...)
                             v
                  index/search.py::candidates
                             |
                             +--- lexikalische Liste (BM25, SUMME über die Felder)
                             +--- semantische Liste (nur wenn nicht lexical_only)
                             |
                             v  index/fusion.py (RRF, k=60)
                             |
                             v  store.prefilter_visible(uid, ids)   <-- die eine Rechtegrenze
                             v
                  Kandidaten ohne Name, ohne Pfad, ohne Text
                             |
                             v  POST /snippets  -> snippets_for(... FIELD_BODY_DE ...)
                             |                     (leer bei reinem Sprachfeld-Treffer, Pitfall 4)
                             v
                  PHP-Recheck über getUserFolder()->getFirstNodeById()
                             v
                  Treffer beim Nutzer

Woher der Feldplan kommt (einmal je Öffnung der Lesehälfte):

  state.db meta
    +-- schema_version : "1" (Bestand) | "2" (Umbau durch, stamp_after_swap)
    +-- languages      : fehlt (Legacy = de,en) | "de,en" | "de,en,es" | ...
                |
                v
    api/resources.py::_field_plan(store, index)
                |
                +-- schema_version != "2"  ->  eingefrorener Bestandsplan (4 Felder)
                +-- schema_version == "2"  ->  name, title + body_<code> je Sprache der Marke
                |
                v  Gegenprobe: doc_freq(field, "") je Körperfeld, ValueError = Feld fehlt
                v
            ReadSide.field_plan (frozen, unveränderlich bis reset_read_side())
```

### Recommended Project Structure

Keine neuen Module. Die Phase berührt genau diese Dateien:

```
backend/src/findling/
  query/rewrite.py       # DEFAULT_FIELDS/FIELD_BOOSTS raus, plan-Parameter rein
  api/resources.py       # FieldPlan berechnen, auf ReadSide tragen
  api/search.py          # plan durchreichen
  api/snippets.py        # plan durchreichen
  api/diagnose.py        # plan durchreichen
  index/schema.py        # ggf. BODY_FIELD-Reihenfolge als einzige Quelle bestätigen (keine Änderung erwartet)
backend/tests/
  test_schema_generations.py       # AST-Wächter ERSETZEN (Phasengrenze, siehe unten)
  test_query_fields_plan.py        # NEU: der Feldplan als eigene Einheit
  test_language_cases_query_path.py# NEU: die vier Sprachfälle auf dem normalen Suchweg
  test_no_language_detection.py    # NEU: der Anti-Feature-Wächter
  test_query_rewrite.py            # Aufrufstellen nachziehen
  test_measurement_scripts.py      # PACKAGE_TREE_HASH_TODAY nachziehen
.github/workflows/deploy-harp.yml  # spanischer Beweis in der Upgrade-Strecke + arm64-tauglicher Fall
docs/language-analyzers.md         # Abschnitt "Was die Frageseite durchsucht" + Grenze Textauszug
```

### Pattern 1: Der Feldplan entsteht einmal, beim Öffnen der Lesehälfte

**Was:** Ein eingefrorener Wert mit zwei Feldern (`fields`, `boosts`), berechnet in
`api/resources.py::read_side()` und auf der bestehenden `ReadSide` getragen.

**Warum genau dort:** `read_side()` (Zeile 335 bis 425) hält Index, Store und die Einstellungen
gleichzeitig, wird einmal je Verzeichnis geöffnet und durch `reset_read_side()` nach dem
Verzeichnistausch des Umbaus verworfen. Die Invalidierung, die ein eigener Cache neu bräuchte,
existiert dort bereits und ist durch die Generationszählung (`ReadSide.generation`, Audit M-18-02)
gegen genau die Wettlaufsituation gehärtet, die ein neuer Cache wieder aufmachen würde.

**Kosten, gemessen:** ein `store.read_meta()` plus vier `doc_freq`-Aufrufe zu je 0,26 us, einmal je
Öffnung. Gegenüber `filled_languages()`, das je Feld das gesamte Term-Wörterbuch abläuft und deshalb
eine eigene 30-s-TTL braucht, ist das keine Optimierung, sondern eine andere Grössenordnung.

**Die Rangfolge der Tore:**

1. `stored["schema_version"] != "2"` -> der eingefrorene Bestandsplan, wörtlich die heutigen vier
   Namen. Das ist das Sicherheitstor der Roadmap und es fällt geschlossen: eine fehlende Marke,
   `UNKNOWN_VERSION` und jede unbekannte Stufe landen hier.
2. Sonst: die Sprachmenge aus `stored["languages"]`, gelesen mit **derselben** Legacy-Regel, die
   `store/repo.py::_languages_are_legacy` anwendet (fehlende Marke = `de,en`). Keine zweite Lesart.
3. Aus der Sprachmenge entsteht die Feldliste in `BODY_FIELD`-Reihenfolge, plus `name` und `title`.
4. Gegenprobe: `searcher.doc_freq(field, "")` je Körperfeld. Wirft das eine `ValueError`, fällt der
   Plan auf den Bestandsplan zurück und schreibt eine Warnzeile. Das fängt den einen Fall, den die
   Marke nicht sehen kann: eine `state.db` aus einer Sicherung neben einem älteren Indexverzeichnis.

**Anti-Pattern, das der Planer ausschliessen muss:** `settings().languages` als Quelle. Das ist der
Wunsch des laufenden Containers, nicht die Wahrheit des Verzeichnisses. Genau diese Verwechslung ist in
Phase 18 als Bedrohung T-18-05-01 benannt und hat dort die Saat-Ausnahme erzwungen
(`store/repo.py:1555` lässt `languages` bewusst aus `_DEFAULT_META` weg).

### Pattern 2: Boosts kommen aus derselben Quelle wie die Feldliste

**Gemessen am 24.09.2026 gegen tantivy 0.26.2** (Sonde, Volltext unter "Code Examples"):

| Aufruf | Ergebnis |
|---|---|
| `parse_query_lenient(..., default_field_names=["body_de","body_es"])` gegen Schema ohne `body_es` | ``ValueError: Field `body_es` is not defined in the schema.`` |
| `parse_query_lenient(..., default_field_names=["body_de"], field_boosts={"body_es": 0.6})` gegen dasselbe Schema | **dieselbe `ValueError`** |
| `field_boosts` auf ein Feld, das im Schema steht, aber nicht in `default_field_names` | kein Fehler |
| `parse_query_lenient("body_es:vertrag", default_field_names=["body_de"])` gegen dasselbe Schema | **kein Wurf**, `errors=[Field does not exist: 'body_es']` |

Die zweite Zeile ist neu gegenüber allem, was in 17-RESEARCH und 18-RESEARCH steht, und sie ist
bindend: **wer nur `DEFAULT_FIELDS` dynamisch macht und `FIELD_BOOSTS` als Konstante stehen lässt, hat
den Totalausfall nicht behoben, sondern nur verschoben.** Beide Listen gehören in einen Wert.

Die vierte Zeile ist die gute Nachricht und gehört in die Sicherheitsbetrachtung: Nutzereingabe kann
den Pfad nicht auslösen. Wer `body_es:vertrag` in die Suchleiste tippt, bekommt einen Eintrag in der
Fehlerliste und keine Ausnahme. Gefährlich ist ausschliesslich die vom Code gestellte Feldliste.

**Die Boost-Tabelle, Empfehlung:**

| Feld | Boost heute | Boost nach Phase 19 | Begründung |
|---|---|---|---|
| `name` | 3,0 | 3,0 | unverändert, ein Name ist eine Absicht |
| `title` | 2,0 | 2,0 | unverändert |
| `body_de` | 1,0 | 1,0 | unverändert, Leitsprache und einzige gespeicherte Textkopie |
| `body_en` | 0,8 | 0,8 | unverändert, Leitsprache |
| `body_es` | - | 0,6 | Zusatzsprache, ausdrücklich unterhalb `body_en` |
| `body_it` | - | 0,6 | dito |
| `body_nl` | - | 0,6 | dito |
| `body_pt` | - | 0,6 | dito |

0,6 ist die Zahl aus `.planning/research/FEATURES.md` Frage 3 und sie ist eine Empfehlung, keine
Messung. Was die Messung sagt, steht im nächsten Muster; der Planer sollte den Wert als benannte
Konstante mit Begründungskommentar anlegen, damit Phase 22 ihn ohne Suche findet.

### Pattern 3: Die Rangprobe, und was sie ehrlich belegen kann

**Gemessen** (Sonde `probe19b`, fünf Körperfelder, Dokument 1 in allen fünf Feldern befüllt, Dokument 2
nur im englischen Feld, identische Frage):

| Aufbau | Score Dok 1 (fünf Felder) | Score Dok 2 (ein Feld) | Verhältnis |
|---|---|---|---|
| nur `body_en` durchsucht | 0,1823 | 0,1823 | 1,0 |
| fünf Felder, alle Boosts 1,0 | 2,1500 | 0,1823 | **11,8** |
| fünf Felder, en 0,8 / Rest 0,6 | 1,3264 | 0,1459 | **9,1** |
| fünf Felder, en 0,8 / Rest 0,2 | 0,5394 | 0,1459 | **3,7** |

tantivy summiert die Feldbeiträge. Boosts dämpfen die Summe, sie beseitigen sie nicht. Erfolgskriterium
3 der Roadmap sagt "Ein Treffer in mehreren Sprachfeldern drängt sich nicht vor einen besseren
englischen Treffer" und begründet das mit den Boosts. Der Planer muss wissen, dass die Begründung die
Behauptung nicht trägt, und die Probe entsprechend formulieren.

**Was die Probe belegen kann, und es ist der reale Fall:** derselbe Text geht in **alle** eingeschalteten
Felder (`index/writer.py:286-293`). Die Mehrfeld-Multiplikation trifft deshalb jedes Dokument, nicht nur
manche, und kürzt sich im Vergleich zweier Dokumente weitgehend heraus. Gemessen (Sonde `probe19c`, drei
Dokumente in en/nl/es, sechs Felder, vier Fragen): **jede Frage brachte unter zwei Feldern und unter
sechs Feldern dasselbe Dokument zurück**, die Reihenfolge verschob sich nicht. Die Verzerrung entsteht
nur dort, wo die Ketten sich über ein Dokument uneins sind: ein Wort, das alle sechs Ketten unverändert
durchlassen (`informatie`), bekommt sechs Beiträge, ein Wort, das nur drei Ketten auf den Fragestamm
legen (`contratos` gegen `contrato`), bekommt drei.

**Empfohlene Form der Rangprobe** (ein Testmodul, kein Integrationslauf):

1. Ein Index mit sechs befüllten Körperfeldern, drei Dokumenten: A ist ein starker englischer Treffer,
   B trifft dieselbe Frage über mehrere Sprachketten schwächer, C ist der Ablenker.
2. Zusicherung 1, struktur: `plan.boosts[body_es|it|nl|pt] < plan.boosts[body_en]` für jede aktive
   Menge. Das ist die wörtliche Roadmap-Zusage und sie ist billig.
3. Zusicherung 2, Rang: A steht vor B. Wenn A unter den empfohlenen 0,6 **nicht** vor B steht, ist das
   ein Messergebnis und keine Testschwäche: dann senkt der Plan die vier Werte, bis es hält, und
   schreibt die gemessene Grenze in den Kommentar. Genau diese Zahl ist die Eingabe für den
   `disjunction_max`-Entscheid in Phase 22.
4. Zusicherung 3, Gegenprobe: mit allen vier Boosts auf 1,0 kippt der Rang. Ohne sie wäre Zusicherung 2
   auch für einen Index grün, in dem B die Frage gar nicht trifft.

Das Muster für Punkt 4 steht im Repo: `test_rrf_fusion.py` baut seine Behauptungen durchweg als Paar aus
Aussage und Gegenprobe (`test_a_semantic_weight_of_zero_removes_the_semantic_list`).

### Pattern 4: Die Sprachfälle auf den normalen Suchweg heben

`test_language_cases_field_level.py` ist die Vorlage und sie ist ausdrücklich als Vorstufe geschrieben:
der Modulkopf sagt, die Fälle laufen auf der Feldebene, "weil Phase 19 die Frageseite öffnet". Die
Hebung ist mechanisch: statt
`index.parse_query_lenient(text, default_field_names=[BODY_FIELD[code]])`
läuft die Frage durch `build_query(index, text, plan=...)` mit dem echten Feldplan einer Instanz, deren
Sprachmenge den Code enthält.

**Der Haken, und er entscheidet, ob der Beweis etwas wert ist.** Auf dem normalen Suchweg sind **alle**
aktiven Felder in der Liste. Ein Formenpaar, das die deutsche oder die englische Kette selbst
zusammenführt, beweist danach nichts mehr. Genau dieser Fehler ist am 24.09.2026 schon einmal passiert
und steht im Modulkopf der Feldebenen-Datei ("A probe written on 2026-09-24 found a Spanish document
through the ENGLISH chain").

**Gemessen am 24.09.2026**, über die vorhandenen Fixtures, Kriterium "die eigene Kette führt zusammen,
die englische UND die deutsche Kette nicht":

| Sprache | Paare, die nur die eigene Kette verbindet | Beispiel aus der Fixture | gemeinsamer Term |
|---|---|---|---|
| es | **2** | `alemanes` gegen `alemana` | `aleman` |
| it | **0** | - | - |
| nl | **2** | `beïnvloeden` gegen `beinvloed` | `beinvloed` |
| pt | **2** | `país` gegen `paises` | `pais` |

Für es, nl und pt ist der Beweis damit sofort schreibbar, mit Wörtern, die bereits in
`backend/tests/fixtures/chain_cases_<code>.txt` stehen und deshalb nicht als Literale in den Test müssen
(die Regel `test_no_form_of_the_case_stands_in_this_file` gilt weiter).

Für **it** gibt es kein solches Paar, solange Englisch aktiv ist. Die vierzehn Familien der it-Fixture
sind reine Akzentpaare, und die englische Kette faltet ebenfalls. Gegen die **deutsche** Kette allein
wären es 14 von 14. Siehe Open Question 1.

### Pattern 5: Der Anti-Feature-Wächter

Die Abwesenheit eines Pfades ist funktional nicht beweisbar. Das Repo hat dafür ein eingeführtes Muster,
und `test_semantic_boundary.py` schreibt es selbst hin: die Behauptungen lesen die Quellen, mit
Kommentaren und Zeichenketten entfernt (`tokenize`), damit erklärender Text den Zähler nicht auslöst.

**Vier Aussagen, die zusammen das Anti-Feature festhalten:**

1. **Strukturell, die stärkste:** die Funktion, die den Feldplan baut, nimmt den Anfragetext nicht
   entgegen. Als AST-Prüfung über die Signatur: kein Parameter, der Text heisst oder Text sein kann.
   Eine Spracherkennung der Anfrage ist damit nicht "verboten", sondern nicht anschliessbar.
2. **Strukturell, die zweite:** `build_query` liest den Feldplan nur aus seinem Parameter und nie aus
   `settings()` oder einer Modulkonstante. Gezählt über den entkommentierten Quelltext.
3. **Am Abhängigkeitsbaum:** weder `backend/pyproject.toml` noch `backend/uv.lock` führen ein Paket
   aus der Spracherkennungsfamilie. Geprüft am 24.09.2026: `langdetect`, `lingua`, `langid`,
   `py3langid`, `fasttext`, `cld2`, `cld3`, `pycld` kommen in keiner der beiden Dateien vor.
4. **Am Wireformat:** `SearchRequest` und `SnippetsRequest` tragen `extra="forbid"` und kein Sprachfeld.
   Das hält bereits `test_search_fields_lockstep.py` fest; der neue Test muss es nur benennen, nicht
   wiederholen.

Der Wächter braucht wie jeder andere in diesem Repo gestellte Gegenproben: ein Muster mit einem
Textparameter in der Signatur muss rot werden, ein leeres Modul muss einen Befund je erwarteter Aussage
liefern und nicht null.

### Pattern 6: Die Phasengrenze auflösen, und zwar sichtbar

`backend/tests/test_schema_generations.py` ist mit einer Selbstzerstörungsklausel geschrieben. Der
Modulkopf sagt wörtlich: "Phase 19 turns `DEFAULT_FIELDS` and `FIELD_BOOSTS` into functions of the
stored `schema_version` mark, and from that moment a check over constants has nothing left to check
[...] whoever deletes it in phase 19 will have to say in the same commit what took its place." Die
gestellte Probe `test_the_gate_fails_closed_when_a_field_list_stops_being_a_list` hält den Übergang
bereits fest.

**Was der Planer damit machen muss, in genau einem Commit:**

- Der AST-Wächter über die drei Konstanten fällt weg (er meldet sonst je umgebauter Liste einen Befund,
  und das ist gewollt, nicht kaputt).
- **Was bleibt:** `FIELDS_SCHEMA_1` (die eingefrorenen neun Namen), die Mengeninklusionen gegen das
  neue Schema, die Schema-1-Fixture (`schema_1_index` aus `conftest.py`) und die Fälle, die gegen
  diesen Index wirklich suchen.
- **Was an die Stelle tritt:** ein Test, der den Feldplan gegen einen **echten Schema-1-Index mit einer
  Bestandsmarke** rechnet und zusichert, dass genau die vier heutigen Namen herauskommen, plus ein
  Test, der den gerechneten Plan durch `parse_query_lenient` gegen denselben Index schickt und
  zusichert, dass er weder wirft noch eine leere degradierte Antwort erzeugt. Das ist stärker als der
  Wächter, den er ersetzt: der prüfte Namen, dieser prüft die Maschine.
- Im Commit steht, was an die Stelle trat. Das ist die ausdrückliche Übergabebedingung aus
  `18-03-SUMMARY.md`.

### Pattern 7: Die CI-Strecke

**Zwei Fragen, zwei Orte, und sie sind nicht derselbe.**

**(a) Der spanische Beweis auf einer echten Instanz.** Er gehört in `deploy-harp.yml`, Schritt
"Store upgrade 6", weil dort bereits eine Instanz mit `FINDLING_LANGUAGES=es,de,en` entsteht und der
Umbau nachweislich läuft (`REBUILD_LANGUAGES: 'es,de,en'`, Zeile 362). Die stärkste Form ist ein
Vorher-Nachher:

- In "Store upgrade 2" (Korpus der Bestandsinstallation, noch unter v1.2.0) wandert eine spanische
  Datei mit ins Verzeichnis. Sie wird unter 1.2.0 indexiert, also in ein Schema ohne `body_es`.
- **Vor** dem Umbau: die Suche nach dem spanischen Stamm bringt **0** Treffer. Das ist der
  Gegenbeweis und er ist ohne ihn wertlos.
- **Nach** dem Umbau: **1** Treffer. Der Umbau hat den gespeicherten Text durch die spanische Kette
  geschickt und Phase 19 hat das Feld in die Frage aufgenommen.

**Zwei Fallen dabei, beide konkret.** Erstens: die Vorbedingung `[.terms[]] | all(. == 1)` steht
zweimal im Workflow (Zeile 3133 und 3790) und würde an einem Term brechen, der vorher 0 sein **soll**.
Der spanische Term braucht deshalb einen eigenen Schlüssel im Sondenbericht, nicht einen weiteren
Eintrag in `.terms`. Zweitens: der Wortlaut muss ein Paar sein, das weder die deutsche noch die
englische Kette zusammenführt, sonst ist der Beweis schon vor Phase 19 grün. `alemanes` als Frage gegen
`alemana` im Dokument erfüllt das (gemessen, siehe Pattern 4).

**(b) Der arm64-Ast.** Hier liegt ein Befund, den der Planer kennen muss: **"Store upgrade 5" und
"Store upgrade 6" laufen ausdrücklich nicht auf arm64.** Beide tragen
`if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04' && env.RELEASE_TAG == ''`
(Zeilen 3528 und 3737). Der arm64-Eintrag der Matrix ist `server-version: stable34, runner:
ubuntu-24.04-arm` (Zeile 222 bis 225), also durch die zweite Hälfte der Bedingung ausgeschlossen.

Ein Beweis, der auf allen vier Ästen einschliesslich arm64 läuft, muss deshalb in einem Schritt **ohne**
`if` stehen. Das Vorbild ist "Store install 7, a search finds content without anybody configuring
anything" (Zeile 2129): kein `if`, lädt eine Datei über WebDAV hoch, pollt die OCS-Suchroute
`ocs/v2.php/search/providers/findling/search?term=...` bis zum Treffer, prüft mit `jq`. Ein Schritt
dieser Form mit `FINDLING_LANGUAGES` auf der Zielsprache und vier Sprachfällen ist die einzige Form,
die Erfolgskriterium 1 wörtlich erfüllt ("derselbe Beweis läuft je Sprache für it, nl und pt über den
grünen arm64-CI-Ast"). Siehe Open Question 3 für die Kostenabwägung.

**(c) Die Ergebnisseite.** Heute berührt kein einziger CI-Schritt die Route der Ergebnisseite; gesucht
wird ausschliesslich über die OCS-Unified-Search-Route und die Adminübersicht. Die Route ist aber ohne
Weiteres prüfbar: `PageController::index` trägt `NoAdminRequired` **und** `NoCSRFRequired`
(`php/lib/Controller/PageController.php:215-217`), ein
`curl -u testuser:pass 'http://localhost:8080/index.php/apps/findling/?term=alemanes'` liefert also
HTML, in dem der Dateiname des Treffers stehen muss. Das ist die billigste ehrliche Form der zweiten
Hälfte von Kriterium 1.

### Anti-Patterns to Avoid

- **Nur `DEFAULT_FIELDS` dynamisch machen.** `FIELD_BOOSTS` wirft dieselbe `ValueError` (gemessen).
- **`settings().languages` als Quelle des Feldplans.** Das ist der Wunsch, nicht der Zustand; genau die
  Verwechslung, gegen die Phase 18 die Saat-Ausnahme gebaut hat.
- **Einen zweiten Cache mit eigener TTL anlegen.** `_DEGRADED` und `_FILLED` haben bereits eine
  Generationsfalle gekostet (Audit M-18-02); ein dritter wäre die dritte.
- **Eine zweite Suchroute für Sprachtreffer.** `test_semantic_boundary.py` zählt die Aufrufstellen des
  Rechte-Vorfilters; ein zweiter Weg wäre für den Paritätsjob unsichtbar.
- **Sprachfälle mit selbst gewählten Wörtern.** Die Stärke eines Falls muss aus der Fixture kommen und
  im Test behauptet werden, nicht im Kommentar stehen.
- **Den `disjunction_max`-Umbau vorwegnehmen.** REQUIREMENTS MESS-09 bindet ihn an eine Messung in
  Phase 22.
- **Die `[.terms[]] | all(. == 1)`-Vorbedingung im Workflow aufweichen**, damit der neue Term
  hineinpasst. Die Vorbedingung ist der Grund, warum die Zusicherungen etwas bedeuten.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Welche Felder hat dieses Indexverzeichnis? | Eigener Schema-Leser, eigene Feldliste-Datei neben dem Verzeichnis | `Searcher.doc_freq(field, "")` in `try/except ValueError` | Gemessen: die `Schema`-Klasse von tantivy 0.26.2 hat **keine** öffentliche Introspektion (`dir()` ist leer). `doc_freq` wirft für ein unbekanntes Feld und kostet 0,26 us. |
| Ist dieses Feld befüllt? | Zähler in `state.db` mitführen | `Searcher.terms_with_prefix(field, "", limit=1)` über `resources.filled_languages()` | Existiert bereits, ist gecacht und für die Adminseite gebaut. Nicht neu bauen, aber auch nicht in den Anfragepfad ziehen. |
| Ist die gespeicherte Sprachmarke Legacy? | Zweite Lesart im Feldplan | `store/repo.py::_languages_are_legacy` bzw. die dortige Konstante `LEGACY_LANGUAGES` | Zwei Lesarten derselben Marke driften auseinander, und die Drift wäre unsichtbar. |
| Anfrage in Terme zerlegen | Eigene Tokenisierung, um "die richtige Sprache zu raten" | `parse_query_lenient` mit der vollen Feldliste | Die Kette des Feldes analysiert die Frage bereits feldweise. Das ist genau der Grund, warum keine Spracherkennung gebraucht wird. |
| Formenpaare für die Sprachfälle | Von Hand gewählte Wörter im Test | Die Auswahllogik aus `test_language_cases_field_level.py` (`_separated_pairs`, `_case_pair`, `_distractor`) | Sie ist bereits geschrieben, sie liest aus den Messfixtures und sie macht die Stärke des Falls zu einer Behauptung. |
| Quelltext-Wächter | Regex über die Datei | `ast` plus `tokenize` nach dem Muster `test_semantic_boundary.py` / `test_schema_generations.py` | Kommentare und Zeichenketten müssen raus, sonst löst der erklärende Text den Zähler aus. |

**Key insight:** In dieser Phase ist fast alles schon einmal gebaut worden. Der Wert der Planung liegt
darin, die vorhandenen Bausteine zu verdrahten statt neue danebenzustellen; jedes neue Modul in diesem
Suchpfad muss durch die Rechte-, Offset- und Paritätszusagen erneut geführt werden.

## Runtime State Inventory

Phase 19 ist keine Umbenennung, aber sie liest Laufzeitzustand, der über das Verhalten entscheidet.
Was der Feldplan lesen kann und was er nicht lesen darf:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Gespeicherte Marken | `state.db` Tabelle `meta`: `schema_version` ("1" auf jeder Bestandsinstallation, "2" erst nach `rebuild.stamp_after_swap`), `languages` (auf Bestand **abwesend**, Legacy-Lesart `de,en`) | Beide lesen, beide mit den vorhandenen Legacy-Regeln, keine zweite Lesart |
| Indexverzeichnis | Trägt neun Felder auf Bestand, dreizehn nach dem Umbau. `Index.open` liest das persistierte Schema zurück, `build_schema()` läuft dort nie | Als Gegenprobe per `doc_freq` befragen, nie als alleinige Quelle |
| Laufende Containerkonfiguration | `FINDLING_LANGUAGES` über `settings().languages` | **Nicht** als Quelle des Feldplans verwenden (Wunsch, kein Zustand) |
| Prozessinterne Caches | `resources._OPEN`, `_MARKS`, `_DEGRADED`, `_FILLED`, `_GENERATION`, `_SWAPPING` | Keinen neuen anlegen; den Plan an `_OPEN` hängen und von `reset_read_side()` mit verwerfen lassen |
| Ratschen und Bauartefakte | `PACKAGE_TREE_HASH_TODAY` (`test_measurement_scripts.py:916`), `PHP_TREE_HASH_TODAY` (Zeile 565) | Im selben Commit nachziehen wie jede Änderung unter `backend/src/findling` bzw. `php/` |
| Messfixtures | `backend/tests/fixtures/chain_cases_{es,it,nl,pt}.txt`, Zählgates `EXPECTED_FAMILY_SCORES = {"es": (174, 208), "it": (56, 56), "nl": (57, 81), "pt": (180, 228)}` (`test_language_analyzers.py:436`) | Wird die it-Fixture erweitert, müssen diese Zahlen und `docs/measurements/2026-09-analyseketten/` mitwandern |

**Nichts gefunden in:** OS-registrierter Zustand, Geheimnisse und Umgebungsnamen, externe
Dienstkonfiguration. Geprüft: diese Phase legt keine Aufgabe an, ändert keinen Schlüsselnamen und
berührt keinen Dienst ausserhalb des Containers.

## Common Pitfalls

### Pitfall 1: Die Boost-Abbildung bleibt eine Konstante

**Was schiefgeht:** `DEFAULT_FIELDS` wird sauber dynamisch, `FIELD_BOOSTS` bleibt stehen und bekommt
"der Vollständigkeit halber" die vier neuen Einträge. Auf jeder Bestandsinstallation wirft
`parse_query_lenient` dann weiter, der Suchpfad fängt die Ausnahme und antwortet dauerhaft leer.
**Warum es passiert:** Die Fehlermeldung nennt ein Feld, und der Reflex sucht sie in der Feldliste.
**Wie vermeiden:** Ein Wert mit beiden Hälften. Ein Test, der `set(plan.boosts) <= set(plan.fields)`
für jede erzeugbare Sprachmenge behauptet.
**Warnzeichen:** Ein Test, der nur `plan.fields` gegen `FIELDS_SCHEMA_1` hält.

### Pitfall 2: Der Sprachfall beweist die englische Kette

**Was schiefgeht:** Ein spanischer Fall mit `informacion` gegen `informaciones` sieht überzeugend aus
und ist auf dem normalen Suchweg wertlos: die englische Kette stemmt den Plural genauso.
**Warum es passiert:** Auf der Feldebene von Phase 18 war nur ein Feld in der Frage, jetzt sind es alle.
**Wie vermeiden:** Das Auswahlkriterium aus `test_language_cases_field_level.py` um die deutsche Kette
erweitern und die Auswahl im Test behaupten, nicht im Kommentar.
**Warnzeichen:** Der Fall ist auch dann grün, wenn man `body_es` aus dem Plan nimmt. Genau diese
Gegenprobe gehört in den Test.
**Zusatz, gemessen:** `informacion`/`informaciones` teilen in der spanischen Kette nicht einmal einen
Stamm (`informacion` gegen `inform`); `docs/language-analyzers.md` führt die ganze `-ción`-Klasse unter
"Known limits". Wer sie als Fall nimmt, baut einen Test, der aus zwei Gründen falsch ist.

### Pitfall 3: Der arm64-Beweis läuft nicht

**Was schiefgeht:** Der Sprachbeweis wandert in "Store upgrade 6" und ist damit auf drei von vier
Matrix-Ästen gar nicht vorhanden. Der Lauf ist grün, das Kriterium ist nicht erfüllt.
**Warum es passiert:** Die Upgrade-Strecke ist die naheliegende Stelle, weil dort der Umbau läuft.
**Wie vermeiden:** Vor dem Schreiben die `if`-Zeile des Zielschritts lesen. `if:` mit
`matrix.runner == 'ubuntu-24.04'` schliesst arm64 aus.
**Warnzeichen:** Der neue Schritt erscheint in der Zusammenfassung nur einmal statt viermal.

### Pitfall 4: Der Sprachtreffer kommt ohne Textauszug

**Was schiefgeht, gemessen am 24.09.2026:** Ein Index mit `body_de`/`body_en`/`body_es`, Dokument
`"Esta es una carta de la empresa alemana sobre el contrato de arrendamiento."` in allen drei Feldern.
Frage `alemanes` über den vollen Feldplan: **1 Treffer**, `SnippetGenerator.create(..., FIELD_BODY_DE)`
liefert `fragment() == ''` und `highlighted() == []`. Kontrollfrage `contrato` (die auch die deutsche
Kette als Rohtoken trifft): volles Fragment.
**Warum es passiert:** Der Auszug wird ausschliesslich aus `body_de` geschnitten
(`index/search.py:875`), weil das die einzige gespeicherte Textkopie ist. Eine Frage, die nur über die
spanische Kette auf den Dokumentterm trifft, hat in der deutschen Kette keinen Termtreffer, also nichts
zu markieren. Der vorhandene Ausweichpfad `_passage_of` braucht einen Rangabschnitt aus der
Vektorhälfte, und die wird bei einer Einwortfrage gar nicht erst gebaut (`one_term` schaltet auf
`lexical_only`).
**Wie vermeiden:** Nicht vermeiden, sondern benennen und messen. Der Treffer ist ein Treffer
("a hit without a snippet is still a hit", so steht es im Docstring), die PHP-Seite hat einen eigenen
Rückfall für die Unterzeile. Die CI-Probe muss deshalb den **Treffer** behaupten und nicht den Auszug.
Die Grenze gehört in `docs/language-analyzers.md` unter "Known limits" und in die Grenzenliste, die
Phase 23 (REL-03 Kriterium 2) in Doku und Store-Text schreibt.
**Warnzeichen:** Eine Probe, die `.ocs.data.entries[0].subline` prüft, statt `entries | length`.

### Pitfall 5: Die Fixture-Zählgates brechen

**Was schiefgeht:** Eine neue it-Formfamilie wandert in `chain_cases_it.txt`, und
`EXPECTED_FAMILY_SCORES["it"] = (56, 56)` sowie der Messbericht in
`docs/measurements/2026-09-analyseketten/` stehen noch auf den alten Zahlen.
**Warum es passiert:** Die Fixture ist gleichzeitig Messeingabe (Plan 17-05/17-06) und Testdaten
(Plan 18-04). Die Doppelrolle ist nirgends an der Datei selbst vermerkt.
**Wie vermeiden:** Wenn die Fixture wächst, wächst der Plan um einen Schritt "Messung wiederholen"
(`scripts/dev/measure_chains.sh`) und um die Aktualisierung von Zählgate und Bericht. Alternativ eine
eigene Fixture für die Phase-19-Fälle, siehe Open Question 1.
**Warnzeichen:** `test_language_analyzers.py` wird rot an einer Stelle, die mit Phase 19 nichts zu tun
hat.

### Pitfall 6: Ein neuer Parameter ohne sicheren Vorgabewert

**Was schiefgeht:** `build_query` bekommt einen Pflichtparameter `plan`, und einer der drei Aufrufer
(`api/search.py`, `api/snippets.py`, `api/diagnose.py`) oder eine der rund zwei Dutzend Teststellen
wird übersehen.
**Warum es passiert:** `build_query(index, text)` wird in den Tests durchgehend mit zwei Positionen
gerufen.
**Wie vermeiden:** Der Parameter ist keyword-only mit dem **sicheren** Vorgabewert, also dem
eingefrorenen Bestandsplan. Wer ihn vergisst, sucht weiter genau die vier Felder von heute und bricht
nichts. Das ist dieselbe Fail-Closed-Linie, die `_schema_is_legacy` und `_languages_are_legacy` fahren.
**Warnzeichen:** Ein Vorgabewert, der aus `settings()` gelesen wird.

### Pitfall 7: `body_de` bleibt unbedingt in der Feldliste

**Was schiefgeht:** Der Feldplan behandelt nur die vier neuen Sprachen dynamisch und lässt `body_de`
und `body_en` als feste Einträge stehen. Auf einer Instanz mit `FINDLING_LANGUAGES=es` (nach E-17-3
Option a erlaubt) durchsucht die Frage dann ein Feld, das zwar Text trägt, aber durch die deutsche Kette
gelaufen ist und für das niemand eine Frage gemeint hat.
**Warum es passiert:** `body_de` ist gespeichert und wird unbedingt geschrieben, also wirkt es wie ein
Sonderfall.
**Wie vermeiden:** `index/writer.py:268-285` hat den richtigen Satz bereits: "stored" und "analysed by
the German chain" folgen nicht auseinander. Der Schreibvorgang ist unbedingt, **die Frage nicht**. Der
Feldplan behandelt alle sechs Körperfelder gleich.
**Warnzeichen:** `FIELD_BODY_DE` steht als Literal in der Plan-Funktion statt über `BODY_FIELD`.

## Code Examples

### Messung M-1: `field_boosts` wirft genauso wie `default_field_names`

```python
# Gemessen 2026-09-24 gegen tantivy v0.26.2, index_format v7
# Schema ohne body_es, Index mit einem Dokument.
try:
    idx.parse_query_lenient("vertrag", default_field_names=["body_de"], field_boosts={"body_es": 0.6})
except ValueError as ex:
    print(ex)      # Field `body_es` is not defined in the schema.

# Dasselbe Feld in der Feldliste: identische Ausnahme.
# Ein Boost auf ein Feld, das im Schema steht, aber nicht in default_field_names: kein Fehler.
# Nutzereingabe "body_es:vertrag": KEIN Wurf, errors == [Field does not exist: 'body_es']
```

### Messung M-2: Es gibt keine Schema-Introspektion, aber eine billige Feldsonde

```python
# Gemessen 2026-09-24 gegen tantivy v0.26.2
print([d for d in dir(schema) if not d.startswith("_")])   # []  -> keine Introspektion

searcher.doc_freq("body_de", "vertrag")   # 1   (Feld vorhanden, Term vorhanden)
searcher.doc_freq("body_en", "vertrag")   # 0   (Feld vorhanden, leer)
searcher.doc_freq("body_es", "vertrag")   # ValueError: Field `body_es` is not defined in the schema.

# Kosten je Aufruf: 0.26 us  (20000 Läufe)
# Zum Vergleich: parse_query_lenient 2.26 us, terms_with_prefix(limit=1) 1.27 us auf einem winzigen Index
```

### Messung M-3: tantivy summiert die Feldbeiträge

```python
# Fünf Körperfelder, Dokument 1 in allen fünf befüllt, Dokument 2 nur im englischen Feld,
# dieselbe Frage. Gemessen 2026-09-24.
# nur body_en durchsucht      -> [(0.1823, 1), (0.1823, 2)]
# fünf Felder, Boosts 1.0     -> [(2.1500, 1), (0.1823, 2)]
# fünf Felder, en .8 / neu .6 -> [(1.3264, 1), (0.1459, 2)]
# fünf Felder, en .8 / neu .2 -> [(0.5394, 1), (0.1459, 2)]
```

### Messung M-4: Ein reiner Sprachfeld-Treffer hat keinen Textauszug

```python
# Gemessen 2026-09-24. Dokument in body_de/body_en/body_es:
#   "Esta es una carta de la empresa alemana sobre el contrato de arrendamiento."
q, _ = idx.parse_query_lenient(
    "alemanes",
    default_field_names=["body_de", "body_en", "body_es"],
    field_boosts={"body_de": 1.0, "body_en": 0.8, "body_es": 0.6},
    conjunction_by_default=True,
)
# hits: 1
generator = SnippetGenerator.create(searcher, q, idx.schema, "body_de")
# fragment: ''        highlighted: []
# Kontrollfrage "contrato":
# fragment: 'Esta es una carta de la empresa alemana sobre el contrato de arrendamiento'
```

### Messung M-5: Welche Formenpaare nur die eigene Kette verbindet

```python
# Gemessen 2026-09-24 über die vorhandenen Fixtures, mit den ausgelieferten Ketten
# (english_analyzer(), cached_german_analyzer(...), snowball_analyzer(SNOWBALL_NAME[code])).
# Kriterium: eigene Kette führt zusammen, en UND de nicht.
# es: 2 Paare   ('alemanes','alemana'), ('alemanes','alemanas')   -> 'aleman'
# it: 0 Paare   (gegen de allein wären es 14; gegen en null, weil beide Ketten falten)
# nl: 2 Paare   ('beïnvloeden','beinvloed'), ('beinvloeden','beïnvloed') -> 'beinvloed'
# pt: 2 Paare   ('país','paises'), ('pais','países')              -> 'pais'
```

### Messung M-6: Italienisch lässt sich mit Flexion beweisen

```python
# Gemessen 2026-09-24. Zwölf gewöhnliche italienische Flexionspaare, alle zwölf
# "nur it": die italienische Kette führt zusammen, die englische und die deutsche nicht.
# informazione/informazioni  it ['inform']     en ['informazion']/['informazioni']
# contratto/contratti        it ['contratt']   en ['contratto']/['contratti']
# documento/documenti        it ['document']   en ['documento']/['documenti']
# pagamento/pagamenti        it ['pag']        en ['pagamento']/['pagamenti']
# ... fattura/fatture, riunione/riunioni, dipendente/dipendenti, scadenza/scadenze,
#     richiesta/richieste, comunicazione/comunicazioni, allegato/allegati, bolletta/bollette
```

### Skizze: der Feldplan (Form, nicht fertiger Code)

```python
# api/resources.py
@dataclass(frozen=True, slots=True)
class FieldPlan:
    """What a bare word searches on THIS directory, and how the fields are weighted."""

    fields: tuple[str, ...]
    boosts: Mapping[str, float]
    title_only: tuple[str, ...]


# The frozen list of every release up to and including the intermediate state of
# phase 18. It is what an index of schema 1 answers, and it is the value every
# caller that forgets to pass a plan gets.
LEGACY_PLAN: Final = FieldPlan(
    fields=(FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE),
    boosts={FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8},
    title_only=(FIELD_NAME,),
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Feldliste als Modulkonstante, gültig für alle Instanzen | Feldliste aus den Marken des einzelnen Indexverzeichnisses | Phase 19 | Zwei Schemageneration leben gleichzeitig im Feld; eine Konstante kann beide nicht bedienen |
| AST-Wächter über die drei Konstanten | Feldplan-Test gegen echten Schema-1-Index plus `parse_query_lenient`-Lauf | Phase 19 | Der Wächter hat keinen Gegenstand mehr, sobald die Listen keine Konstanten sind. Sein Ersatz ist stärker |
| Sprachfälle auf der Feldebene, ein Feld je Frage | Sprachfälle über `build_query` mit dem echten Feldplan | Phase 19 | Das Auswahlkriterium für Formenpaare muss die deutsche Kette mit ausschliessen |
| `tantivy_version` als volle Gleichheit | nur die `index_format`-Hälfte entscheidet | Phase 17, E-17-7 Option a | Für Phase 19 nur als Kontext relevant |

**Deprecated/überholt:**

- Die Notiz aus der Milestone-Research, die `ValueError` nenne das Feld in Apostrophen: in 0.26.2 sind es
  Backticks (`` Field `body_es` is not defined in the schema. ``). Wer die Meldung im Test matcht, matcht
  auf den Feldnamen, nicht auf die Klammerung. `test_schema_generations.py` macht das bereits richtig
  (`pytest.raises(ValueError, match=field)`).
- Die Annahme, Feld-Boosts könnten die Mehrfeld-Summierung beheben. Gemessen: sie dämpfen sie.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Boost 0,6 für die vier neuen Felder ist der richtige Wert | Pattern 2 | Die Rangprobe fällt anders aus; der Plan senkt den Wert und schreibt die gemessene Grenze hin. Kein struktureller Schaden. |
| A2 | Kriterium 2 meint mit "befüllt" die Sprachen der gespeicherten `languages`-Marke, nicht das Ergebnis von `filled_languages()` | Pattern 1, Open Question 2 | Wird es als Term-Wörterbuch-Probe gelesen, kommt ein voller Wörterbuchlauf in den Anfragepfad. Owner- oder Planerentscheid nötig. |
| A3 | "Der grüne arm64-CI-Ast" meint den Matrixeintrag `ubuntu-24.04-arm` in `deploy-harp.yml` | Pattern 7b, Open Question 3 | Andere Lesart: der pytest-Lauf. Der läuft aber laut `python.yml` nur auf amd64 (`extract-bench-arm` ist ein reiner Messjob). |
| A4 | Die Ergebnisseite braucht keine PHP-Änderung, weil sie dieselbe Backend-Route benutzt | Architekturdiagramm | Wäre falsch, wenn `SearchService` eine eigene Feldlogik trüge. Im Rahmen dieser Recherche nicht Zeile für Zeile gelesen; der Planer sollte `php/lib/Service/SearchService.php` einmal bestätigen. |
| A5 | Der leere Textauszug beim reinen Sprachfeld-Treffer ist akzeptabel und wird dokumentiert statt behoben | Pitfall 4 | Wenn der Owner ihn als Mangel wertet, wächst die Phase um einen Auszugspfad je Körperfeld. Der Befund ist gemessen, die Bewertung ist es nicht. |
| A6 | `EXPECTED_FAMILY_SCORES` und der Messbericht sind die einzigen Stellen, die an den Fixture-Zahlen hängen | Pitfall 5 | Eine übersehene dritte Stelle kostet einen roten Lauf, keinen Fehler im Produkt. |

## Open Questions (RESOLVED)

> Alle vier Fragen sind bei der Planung am 24.09.2026 entlang der Empfehlungen entschieden worden:
> OQ1 -> neue it-Flexionsfamilie (19-02), OQ2 -> "befuellt" = languages-Marke (19-03),
> OQ3 -> EIN ungegateter CI-Schritt (19-07), OQ4 -> AST-Waechter-Ersatz im selben Commit (19-01).

1. **Wie wird der italienische Fall auf dem normalen Suchweg bewiesen?**
   - Was wir wissen: In der vorhandenen it-Fixture gibt es null Paare, die nur die italienische Kette
     verbindet, solange Englisch aktiv ist (gemessen). Gegen die deutsche Kette allein wären es 14.
     Zwölf von zwölf geprüften italienischen Flexionspaaren sind dagegen "nur it" (gemessen).
   - Was unklar ist: ob die Messfixture erweitert werden darf, ohne die Messung vom 23.09.2026 neu zu
     fahren.
   - Empfehlung: **Eine Flexionsfamilie in `chain_cases_it.txt` aufnehmen** (zum Beispiel
     `informazione informazioni`) und dabei `EXPECTED_FAMILY_SCORES["it"]`, den Bericht in
     `docs/measurements/2026-09-analyseketten/` und die Klassifizierung `FOLDED`/`SEPARATED` in
     `test_language_cases_field_level.py` mitziehen. Der Modulkopf dort sieht diese Beförderung
     ausdrücklich vor ("an Italian inflection family added later turns it red, and then the case gets
     promoted"). Die Alternative, den it-Beweis auf einer Instanz ohne Englisch zu fahren, erzeugt eine
     Konfiguration, die kein Nutzer fährt, und beweist damit weniger.

2. **Heisst "befüllt" in Erfolgskriterium 2 die Marke oder das Term-Wörterbuch?**
   - Was wir wissen: `resources.filled_languages()` beantwortet die Wörterbuchfrage, läuft je Feld über
     das gesamte Term-Wörterbuch und hängt deshalb an einer 30-s-TTL; sein eigener Docstring nennt die
     Kosten als Grund für die Sparsamkeit (Audit M-18-08).
   - Was unklar ist: ob die Roadmap diese Funktion meinte.
   - Empfehlung: **Die Marke.** Ein Feld, das aktiv und gebaut, aber noch leer ist, kostet in der Frage
     einen leeren Postinglisten-Zugriff und liefert keinen falschen Treffer. Ein voller
     Wörterbuchdurchlauf im Anfragepfad kostet dagegen mit dem Index. `filled_languages()` bleibt, was
     es ist: die Diagnose der Adminseite. Wenn der Planer es anders liest, gehört das in eine
     Owner-Frage und nicht in eine Implementierung.

3. **Wie viel CI-Zeit ist der Beweis "je Sprache, auch auf arm64" wert?**
   - Was wir wissen: Ein ungegateter Schritt nach dem Muster von "Store install 7" läuft auf allen vier
     Matrixästen. Vier Sprachen mal vier Äste sind sechzehn Durchläufe eines Upload-plus-Poll-Zyklus.
     `deploy-harp` hat `timeout-minutes: 45`.
   - Was unklar ist: die tatsächliche Laufzeit eines solchen Schritts (der Zero-Config-Schritt pollt
     `ZERO_CONFIG_BUDGET_SECONDS` lang mit `cron.php`-Runden).
   - Empfehlung: **Ein Schritt, vier Dateien, eine Instanz** mit
     `FINDLING_LANGUAGES=de,en,es,it,nl,pt`, vier Uploads und vier Suchen in einer Schleife, statt vier
     Schritten. Vorher die Laufzeit einmal messen und die Zahl in den Kommentar schreiben, wie es die
     anderen Budgets dieses Workflows tun. Wenn die Zeit nicht reicht, ist die ehrliche Kürzung "nur
     der arm64-Ast bekommt alle vier, die anderen drei bekommen Spanisch" und nicht "der Beweis wandert
     in einen gegateten Schritt".

4. **Bekommt Phase 19 einen Messhaken für den `disjunction_max`-Entscheid?**
   - Was wir wissen: MESS-09 bindet den Entscheid an eine Messung auf echten Daten in Phase 22. Die
     Rangprobe aus Pattern 3 erzeugt die Zahl, die dort gebraucht wird (ab welchem Boost kippt der
     Rang), kostenlos.
   - Empfehlung: Das Ergebnis der Rangprobe als benannte Zahl in `docs/language-analyzers.md`
     hinterlegen und in der Phase-22-Vorbereitung darauf verweisen. Kein Code, kein Schalter.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 + uv, `backend/.venv` | Suite, Sonden | ja | `.venv/Scripts/python.exe` vorhanden und lauffähig | - |
| `tantivy` | Feldliste, Boosts, Rangprobe, Snippets | ja | `tantivy v0.26.2, index_format v7` (am 24.09.2026 aus der venv gelesen) | - |
| `backend/tests/fixtures/chain_cases_{es,it,nl,pt}.txt` | Sprachfälle | ja | es 20 Familien / 208 Paare, it 14 / 56, nl 13 / 81, pt 18 / 228 | - |
| `conftest.py::schema_1_index`, `build_schema_1`, `open_schema_1_index` | Bestandsbeweis des Feldplans | ja | in `backend/tests/conftest.py` | - |
| GitHub-Runner `ubuntu-24.04-arm` | arm64-Ast | ja | bereits in `deploy-harp.yml`, `docker.yml`, `python.yml`, `measure.yml` genutzt | - |
| `gh` CLI für die unabhängige Laufabfrage | Verifikation | ja (in Phase 18 verwendet) | - | Weblauf ansehen |
| Neue externe Pakete | - | entfällt | - | - |

**Fehlende Abhängigkeiten ohne Ausweichweg:** keine.
**Fehlende Abhängigkeiten mit Ausweichweg:** keine.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein (unverändert) | Identität ausschliesslich aus dem signierten AppAPI-Header, `Depends(anc_app)` |
| V3 Session Management | nein (unverändert) | Nextcloud-Sitzung, `NoCSRFRequired` nur auf der lesenden Seitenroute |
| V4 Access Control | **ja, indirekt** | `store.prefilter_visible` bleibt die eine Aufrufstelle; der Feldplan darf keine zweite Suchroute erzeugen. `test_semantic_boundary.py` zählt die Aufrufstellen und muss grün bleiben |
| V5 Input Validation | **ja** | `SearchRequest` mit `extra="forbid"`; die Feldliste entsteht **nie** aus Anfrageinhalt; `_max_bracket_depth` vor dem Parser (Audit C2); `allow_regexes=False` |
| V6 Cryptography | nein | Keine Krypto in dieser Phase |
| V7 Error Handling and Logging | **ja** | Die Fehlerliste des Parsers zitiert die Eingabe und bleibt auf `debug`. Eine neue Warnzeile zum Feldplan darf den Anfragetext nicht führen, nur Feldnamen und die Marke |

### Known Threat Patterns for diesen Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Feldliste aus Nutzereingabe ableiten (Sprachschalter, Sprachparameter) | Elevation of Privilege / Tampering | Nicht anschliessbar machen: die Planfunktion nimmt keinen Text entgegen (Pattern 5, Aussage 1) |
| Dauerhafter Denial of Service über den ValueError-Pfad | Denial of Service | Fail-closed-Tor am gespeicherten `schema_version`; Gegenprobe per `doc_freq`; Test gegen echten Schema-1-Index |
| Suchbegriff im Log | Information Disclosure | Nur Feldnamen und Marken loggen, niemals `text` oder die Parserfehlerliste oberhalb `debug` |
| Zweite Suchroute umgeht den Rechte-Vorfilter | Elevation of Privilege | Der Feldplan reist als Parameter durch die vorhandene Route; keine neue Funktion, die selbst sucht |
| Voller Term-Wörterbuchlauf je Anfrage | Denial of Service | `filled_languages()` bleibt aus dem Anfragepfad (Open Question 2) |
| Regex aus der Suchleiste | Denial of Service | `allow_regexes=False` bleibt gesetzt und wird von `test_index_open.py` bewacht |

## Sources

### Primary (HIGH confidence)

- Eigene Messungen gegen das installierte `tantivy v0.26.2, index_format v7` am 24.09.2026
  (`backend/.venv`): Boost-Ausnahme, fehlende Schema-Introspektion, `doc_freq`-Sonde und ihre Kosten,
  Score-Summierung über Felder, leerer Textauszug beim reinen Sprachfeld-Treffer, Formenpaar-Auswahl
  über die ausgelieferten Ketten, italienische Flexionspaare.
- `backend/src/findling/query/rewrite.py` (565 Zeilen), `index/schema.py`, `index/open.py`,
  `index/search.py`, `index/writer.py`, `store/repo.py`, `api/resources.py`, `api/search.py`.
- `backend/tests/test_schema_generations.py`, `test_language_cases_field_level.py`,
  `test_language_analyzers.py`, `test_semantic_boundary.py`, `test_rrf_fusion.py`,
  `test_search_fields_lockstep.py`, `conftest.py`.
- `.github/workflows/deploy-harp.yml` (4369 Zeilen), `python.yml`, `integration.yml`.
- `php/lib/Controller/PageController.php`, `php/lib/Search/Provider.php`, `php/appinfo/routes.php`.
- `backend/tests/fixtures/chain_cases_{es,it,nl,pt}.txt`.

### Secondary (MEDIUM confidence)

- `.planning/research/FEATURES.md` (Frage 2, Frage 3, Anti-Features, Messtabelle "wie viele der sechs
  Ketten treffen zugleich"): stimmt in Richtung und Grössenordnung mit den eigenen Messungen überein.
- `.planning/phases/18-schema-marken-und-umbauweg/18-RESEARCH.md` Pattern 5 (sichere Reihenfolge):
  eigene Messung bestätigt die dortigen vier Zeilen und ergänzt die Boost-Zeile.
- `docs/language-analyzers.md` (Known limits, Schema-Marke bleibt auf 1).
- `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md` (E-17-2 bis E-17-4).
- `.planning/phases/18-schema-marken-und-umbauweg/18-VERIFICATION.md` (Zustand nach Phase 18).

### Tertiary (LOW confidence)

- Keine. Diese Recherche hat keine Websuche gebraucht: der Gegenstand ist die eigene Kodebasis und eine
  gepinnte Bibliothek, die lokal installiert und direkt messbar ist.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH. Keine neuen Pakete; die einzige Bibliothek ist gepinnt und wurde direkt
  befragt.
- Architektur (Feldplan auf `ReadSide`): HIGH für die Zwänge (Marken, Invalidierung, Kosten), MEDIUM
  für die konkrete Form, weil sie eine Empfehlung und kein Owner-Entscheid ist.
- Boost-Werte: MEDIUM. 0,6 stammt aus der Milestone-Research, nicht aus einer Rangmessung auf echten
  Daten. Die Rangprobe dieser Phase liefert die Zahl nach.
- Pitfalls: HIGH. Vier der sieben sind gemessen, drei sind am Kodetext belegt.
- CI-Strecke: HIGH für den Befund "Store upgrade 5/6 laufen nicht auf arm64" (an der `if`-Zeile
  gelesen), MEDIUM für die Laufzeitabschätzung des neuen Schritts.
- Sprachfälle: HIGH. Die Paarauswahl ist mit den ausgelieferten Ketten nachgerechnet.

**Research date:** 2026-09-24
**Valid until:** 2026-10-24 für alles, was am Kodetext hängt; die tantivy-Messungen gelten, solange der
Pin auf 0.26.2 steht. Wandert der Pin, sind M-1 bis M-4 neu zu fahren.
