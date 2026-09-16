# Phase 13: Filter und Sortierung auf der Ergebnisseite - Research

**Researched:** 2026-09-16
**Domain:** Tantivy-Abfragebau (Filterklausel, Fast-Field-Sortierung, Fast-Field-Bereichsabfrage), FastAPI/Pydantic-Wire-Erweiterung unter `extra="forbid"`, serverseitig gerenderte Nextcloud-PHP-Oberflaeche mit Katalog-Gates
**Confidence:** HIGH fuer alles am eigenen Baum Nachgelesene und alles gegen die installierte tantivy 0.26.0 Gemessene; HIGH fuer die Nextcloud-Suchfilter-Mechanik (stable33-Quellcode gelesen); MEDIUM fuer die Uebertragung der Sortier-Messungen von 20.000 auf 52.111 Dokumente

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Filter-Bedienung (Typgruppen)**
- **D-01:** Mehrfachauswahl der sechs Typgruppen (PDF, Dokumente, Tabellen, Praesentationen, Bilder, Text). Mehrere Gruppen sind kombinierbar (z.B. ?types=pdf,images); jeder Chip schaltet seine Gruppe an/aus. Das Backend-Feld ist eine Liste.
- **D-02:** Darstellung als Chip-Leiste ueber der Trefferliste, alle sechs Gruppen immer sichtbar, als serverseitige Links ohne JavaScript (kein Dropdown, kein Formular fuer die Typwahl).

**Sortier-Bedienung**
- **D-03:** Sortierwahl als drei Textlinks (Segmentschalter): Relevanz (Standard) | Zuletzt geaendert | Aelteste zuerst. Aktiver Modus hervorgehoben, ein Klick wechselt sofort, serverseitig ohne JavaScript.
- **D-04:** Unter Datums-Sortierung zeigt jeder Treffer sein Aenderungsdatum ("Geaendert am ..."). Der Relevanz-Score erscheint unter Sortierung NIE (tantivy liefert unter order_by_field den Feldwert statt des Scores; Candidate.score ist unter Sortierung 0.0). Unter Relevanz-Sortierung bleibt die Trefferdarstellung wie bisher (kein Datum als Zusatzzeile).

**Zeitraumfilter-UI**
- **D-05:** Zeitraum auf der Ergebnisseite ueber feste Schnellbereiche als Link-Chips (Heute, 7 Tage, 30 Tage, Dieses Jahr) neben den Typ-Chips. KEINE freien Datumsfelder, kein Formular in dieser Phase. Der Datumsfilter des Unified-Search-Dialogs wird zusaetzlich uebernommen und via getSupportedFilters() deklariert (FILT-03); since/until aus der URL werden defensiv gelesen und wirken unabhaengig von den Schnellbereichen.

**Aktive Filter und Leerzustand**
- **D-06:** Aktive Typ-/Zeitraum-Chips bleiben in der Leiste hervorgehoben und tragen ein x zum Einzeln-Entfernen; daneben ein Link "Alle Filter zuruecksetzen", der nur bei mindestens einem aktiven Filter erscheint. Keine separate Aktiv-Leiste (keine doppelte Information).
- **D-07:** Bei 0 Treffern unter aktivem Filter erscheint ein eigener Leerzustand: Hinweis "Keine Treffer mit den aktiven Filtern" plus Link "Filter zuruecksetzen", der dieselbe Suche ungefiltert oeffnet.

### Claude's Discretion
- Chip-Reihenfolge, exakte Wortlaute der Labels (dreisprachig EN/DE/FR nach bestehendem Katalog-Muster), Icon-Wahl (SVG, keine Emojis), Abstaende und Hervorhebungsstil des aktiven Zustands.
- URL-Parameternamen und Kanonisierung (types/sort/since/until o.ae.), solange FILT-04 gilt: Filter/Sortierung reisen in der URL, jede Aenderung setzt auf Seite 1 zurueck, fremder Cursorpfad wird abgewiesen.
- Genaue Abbildung der sechs UI-Gruppen auf Extensions (EIN Filtervokabular fuer UI-Gruppen und die bestehende type:-Textsyntax, nicht zwei).
- Schnellbereichs-Grenzen (Kalender- vs rollierende Fenster), solange since/until-Semantik im Backend eindeutig ist.

### Deferred Ideas (OUT OF SCOPE)
- Freie Datumsfelder (von/bis-Formular) auf der Ergebnisseite; erst wenn die Schnellbereiche nachweislich nicht reichen (v1.x).
- Sortierung nach Name oder Groesse; neues Fast-Field, SCHEMA_VERSION-Sprung, Vollreindex; ausdruecklich v2+.
- Facettenzaehler je Dateityp; ausgeschlossen (Zaehl-Orakel, T-02-93).
- Mimetype-Gruppen aus files.mime statt ext; v1.x, falls Genauigkeit wichtiger wird als "no join against files".
- Personenfilter, Ordner-Einschraenkung; eigene Phasen.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Beschreibung (gekuerzt) | Research Support |
|----|-------------------------|------------------|
| FILT-01 | Typgruppen-Filter, semantische Haelfte bleibt aktiv, strukturiertes Request-Feld, nie `type:`-Text | Befund 1 (Filterklausel an zwei Stellen: `build_query` fuer die lexikalische, `_mtimes_of` fuer die semantische Haelfte), Befund 4 (Gruppentabelle), Befund 5 (Request-Felder) |
| FILT-02 | Sortierung "Zuletzt geaendert"/"Aelteste zuerst", Relevanz Standard, Zweitschluessel `file_id`, eigener lexikalischer Modus, Score 0.0 | Befund 2 (empirische Probe gegen die installierte 0.26.0: Feldwert statt Score, `Order.Asc`/`Desc`, `offset` seitenstabil, Gleichstands-Reihenfolge NICHT `file_id`) |
| FILT-03 | Zeitraumfilter since/until, `getSupportedFilters()` deklariert den Datumsfilter | Befund 3 (`Query.range_query` auf dem nicht indizierten Fast-Field funktioniert, ohne Reindex), Befund 9 (Upstream-Mechanik: HTTP 400 bzw. Provider wird vom Dialog gar nicht erst gefragt), Befund 10 (Zeitzone) |
| FILT-04 | Filter/Sortierung in der URL, sichtbar, entfernbar, jede Aenderung auf Seite 1, fremder Cursorpfad abgewiesen | Befund 7 (heutiger Zustand von `cursorPath`, Fingerabdruck-Bindung, `pageUrl`) |
| FILT-05 | Rechtegrenze unveraendert, Paritaetstest deckt die neuen Parameter ab | Befund 12 (`scripts/ci/parity_diff.py`, `ask_page`, Richtungsproblem der Vergleichs-Semantik), Befund 13 (Gates `test_php_acl_boundary.py`, `test_php_trust_boundary.py`) |
</phase_requirements>

---

## Summary

Diese Phase kostet kein Paket, kein Schema, keinen Reindex und keine neue Route. Alles, was FILT-01 bis FILT-03 brauchen, liegt seit v1.0 im Index (`ext` als Raw-Term, `index/schema.py:105`; `mtime` als Fast-Field, `index/schema.py:114`) und ist in der installierten tantivy 0.26.0 vorhanden. Drei Dinge sind in dieser Recherche **neu empirisch belegt** und veraendern den Zuschnitt der Plaene gegenueber der Milestone-Recherche: (1) `Query.range_query` arbeitet auf dem **nicht indizierten** Fast-Field `mtime`, solange `use_inverted_index` beim Vorgabewert `False` bleibt; mit `True` liefert dieselbe Abfrage **stillschweigend null Treffer ohne Fehler**. (2) `offset` zusammen mit `order_by_field` ist ueber Seitengrenzen hinweg exakt konsistent, auch auf einem Index mit 20.000 Dokumenten in vier Segmenten und massiven Zeitstempel-Gleichstaenden; der als VERIFIZIEREN markierte offene Punkt der Milestone-Recherche ist damit geschlossen. (3) Die Gleichstands-Reihenfolge unter `order_by_field` ist **nicht** `file_id`, sondern Segment- und Dokumentadressreihenfolge; der in FILT-02 geforderte Zweitschluessel `file_id` muss also aktiv hergestellt werden und ist keine Eigenschaft der Bibliothek.

Der zentrale Architekturbefund fuer FILT-01 ist praeziser, als die Milestone-Recherche ihn formuliert: die Filterklausel muss an **zwei** Stellen wirken, nicht an einer. Die lexikalische Haelfte bekommt sie in `query/rewrite.py::build_query` als zusaetzliche `Occur.Must`-Klausel (derselbe Mechanismus, den `_extension_query` fuer `type:` schon baut, nur ohne die Operator-Marke `FILETYPE`). Die semantische Haelfte kennt keine Endung; ihre Treffer erreichen die Zusammenfuehrung ueber `index/search.py::_mtimes_of` (Zeile 323), und genau dieser Abgleich gegen den Index ist der Ort, an dem der Filter auch fuer sie gilt: was dort herausfaellt, fehlt in `known` und verschwindet in Zeile 434 (`merged = [... if file_id in known]`) aus der Liste. Damit bleibt die Semantik unter Filter an (Erfolgskriterium 1), ohne dass eine zweite Sicherheitsstelle entsteht. Der Preis ist ehrlich zu benennen: die semantische Haelfte schrumpft unter Filter sichtbar, weil `VECTOR_SCAN_MAX = 300` Chunks vor dem Typschnitt gezogen werden.

Fuer die PHP-Haelfte ist der groesste unterschaetzte Posten nicht die Oberflaeche, sondern die **Kataloge**. Sechs Dateien, drei Sprachcodes, vier Gates, und `test_admin_ui_contract.py` traegt die Schluesselzahl `174` als harte Zusicherung samt einer Docstring-Begruendung, warum sie zuletzt stieg. Jedes neue Label erhoeht sie, und mehrere der naheliegenden Labels ("PDF", "Documents", "Images") sind im Franzoesischen wortgleich mit der englischen Quelle, was das Vollstaendigkeits-Gate G2 rot faerbt, solange sie nicht namentlich in `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` stehen. Das ist kein Detail am Rand: es ist der wahrscheinlichste Grund, aus dem ein sonst fertiger Plan rot wird.

**Primary recommendation:** Backend zuerst in drei Schnitten (Gruppentabelle plus `build_query(extensions=...)`; Sortierzweig als eigener, rein lexikalischer Modus in `candidates`; `since`/`until` als `range_query` im selben Zweigbau), erst danach PHP; die Filterklausel gehoert VOR das Fusionsfenster und zusaetzlich in `_mtimes_of`, die Sortierung bekommt einen eigenen Pfad ohne RRF mit `score = 0.0`, und die Kataloge samt `174`-Zahl werden als eigener Planschritt gefuehrt, nicht als Anhaengsel.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Typgruppe zu Endungsmenge aufloesen | Backend (Python, `query/rewrite.py`) | PHP (nur Gruppennamen in der URL) | Nur der Container kennt das Indexvokabular; die PHP-Seite darf keine zweite Abbildung fuehren (sonst zwei Filtervokabulare) |
| Filterklausel auf die lexikalische Haelfte | Backend (`query/rewrite.py::build_query`) | -- | Die Klausel muss in der Anfrage stehen, bevor das Fusionsfenster gefuellt wird |
| Filterklausel auf die semantische Haelfte | Backend (`index/search.py::_mtimes_of`) | -- | Der Vektorspeicher kennt keine Endung; der Indexabgleich ist der einzige Ort, an dem seine Treffer typgeschnitten werden koennen |
| Reihenfolge (Relevanz vs Datum) | Backend (`index/search.py::candidates`) | -- | Einziger Ort, an dem Reihenfolge und Sichtbarkeit entstehen (Modul-Docstring) |
| Zeitraum-Grenzen since/until als Epoch | Backend (Abfrage) | PHP (Berechnung der Schnellbereiche) | Die Grenzen sind Zeitzonen-abhaengig und damit eine Eigenschaft des Nutzers, nicht des Index |
| Rechtegrenze | PHP (`SearchService::run`, `isReadable()`) | Backend (Vorfilter, keine Grenze) | Unveraendert; Filter und Sortierung duerfen daran nichts beruehren (FILT-05) |
| Chips, Sortierlinks, Leerzustand | PHP (`PageController` + `templates/search.php`) | -- | Serverseitig gerendert, keine neue Route, kein JSON-Kanal, kein Build-Schritt |
| Anzeige "Geaendert am ..." | PHP (`SearchService`, aus dem bestaetigten Knoten) | -- | Der Knoten ist bereits aufgeloest und aktueller als der Index; `mtime` muss dafuer NICHT ueber die Wire (siehe Befund 8) |
| Datumsfilter des Unified-Search-Dialogs | PHP (`Search/Provider.php::getSupportedFilters`) | Backend (dieselben since/until-Felder) | Die Deklaration ist eine reine PHP-Angelegenheit, ihre Wirkung teilt sie mit der Seite |

---

## Befund 1: Wo die Filterklausel ansetzt, und warum an ZWEI Stellen

### Heutiger Zustand, am Code gelesen

`query/rewrite.py::build_query` (Zeile 317) endet mit:

```python
if extensions:
    parsed = Query.boolean_query([(Occur.Must, parsed), (Occur.Must, _extension_query(index, extensions))])
```

`_extension_query` (Zeile 292) baut aus mehreren Endungen eine `Should`-Gruppe aus `Query.term_query(index.schema, FIELD_EXT, extension)`. Die Endungen stammen heute ausschliesslich aus `extract_filters` (Zeile 185), also aus dem Text `type:pdf`.

`carried_operators` (Zeile 130) setzt bei genau demselben Text die Marke `FILETYPE` (Zeile 83), und `api/search.py::one_round` (Zeile 230) liest:

```python
lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only
```

Ein UI-Filter, der `type:` in die Suchzeile schreibt, schaltet also die Vektorhaelfte ab. Das ist der Grund fuer das strukturierte Feld, und es ist verifiziert, nicht uebernommen. [VERIFIED: Quellcode `backend/src/findling/query/rewrite.py`, `backend/src/findling/api/search.py`]

### Die Luecke, die die Milestone-Recherche offen laesst

`store/vectors.py` kennt keine Endung. Ein kNN-Lauf liefert Nachbarn aller Typen, und diese Nachbarn kommen NICHT durch `build_query`. Ihr Weg in die Antwort ist:

```
_semantic_documents()  ->  reciprocal_rank_fusion()  ->  _mtimes_of()  ->  known  ->  merged
```

`index/search.py:426-434`:

```python
known = {file_id: mtime for file_id, _, mtime in lexical}
known.update(_mtimes_of(searcher, index.schema, [file_id for file_id, _ in fused if file_id not in known]))
...
merged = [(file_id, score) for file_id, score in fused if file_id in known]
```

`_mtimes_of` (Zeile 323) baut heute `Query.boolean_query([(Occur.Should, term_query(file_id)) ...])`. Wird diese Abfrage um `(Occur.Must, <Filterklausel>)` erweitert, faellt jedes semantisch gefundene Dokument des falschen Typs aus `known` und damit aus `merged`. Die Funktion tut das bereits fuer einen verwandten Fall: ihr Docstring sagt, ein Dokument, das der Index nicht kennt, ist in der Antwort abwesend.

**Konsequenz:** ein Filter, der nur in `build_query` steht, laesst typfremde Vektor-Treffer durch. Beide Stellen gehoeren in denselben Plan. [VERIFIED: Quellcode `backend/src/findling/index/search.py:323-434`]

### Ehrlich zu benennender Preis

`VECTOR_SCAN_MAX = 300` (config.py:593) begrenzt die Chunk-Treffer VOR dem Typschnitt. Unter einem engen Filter (etwa "Praesentationen") bleibt nach dem Schnitt wenig bis nichts uebrig. Das ist kein Defekt, sondern die Eigenschaft, die PITFALLS.md als Auswegvariante 2 beschreibt. Empfehlung: `VECTOR_SCAN_MAX` in v1.2 NICHT anheben (es ist ein Sicherheits- und Laufzeitdeckel mit eigener Begruendung), sondern die Verkleinerung in `docs/` benennen und sie im Erfolgskriterium 1 mit einem Fall pruefen, bei dem das Zieldokument den gefilterten Typ hat.

---

## Befund 2: Der Sortierzweig, gegen die installierte tantivy 0.26.0 gemessen

Probe vom 16.09.2026, `backend/.venv` (tantivy v0.26.0, index_format v7), Schema wie das Produktivschema (`file_id` unsigned/fast, `ext` raw/basic, `mtime` integer `indexed=False, fast=True`).

| Frage | Ergebnis | Bewertung |
|-------|----------|-----------|
| Erstes Tupelglied ohne `order_by_field` | 0.08701140433549881 (BM25) | Erwartungsgemaess |
| Erstes Tupelglied mit `order_by_field="mtime"` | 500, 400, 300, 200, 100 = die **Feldwerte** | Bestaetigt Pitfall 4 der Milestone-Recherche |
| `order=Order.Asc` | 100, 200, 300, 400, 500 | "Aelteste zuerst" ist derselbe Aufruf, ein Argument anders |
| `offset=2, limit=2, Desc` | 300, 200 | Korrekte zweite Seite |
| `order_by_field="ext"` | `ValueError: Field "ext" is not configured as fast field` | Bestaetigt Pitfall 5 (Name/Groesse brauchen Reindex) |
| Gleichstand: vier Dokumente, identische `mtime`, Einfuegereihenfolge 7, 3, 9, 1 | Ausgabe 7, 3, 9, 1 | **Kein** `file_id`-Zweitschluessel |

**Seitenstabilitaet auf grossem Bestand** (20.000 Dokumente, vier Segmente, nur 200 verschiedene Zeitstempel, also massive Gleichstaende):

```
num_docs 20000  num_segments 4
deep read length: 2048
paged (16 x limit=128, offset=0..1920): 2048
paged == deep: True
mtime non-increasing: True
stable across searchers: True
```

Das heisst: sechzehn Seitenabrufe mit `offset` liefern **exakt** dieselbe Folge wie ein tiefer Abruf, ohne Duplikate und ohne Luecken, trotz Gleichstaenden ueber Seitengrenzen hinweg und ueber vier Segmente. Der in ARCHITECTURE.md als VERIFIZIEREN markierte offene Punkt ("Stabilitaet von `offset` zusammen mit `order_by_field` bei 52.111 Dokumenten") ist damit fuer die Mechanik geklaert; die Uebertragung auf 52.111 Dokumente bleibt MEDIUM, weil die Segmentzahl dort groesser ist, aber das gemessene Verhalten ist segment- und gleichstandsunabhaengig. [VERIFIED: eigene Probe gegen `backend/.venv/Lib/site-packages/tantivy` am 16.09.2026]

### Was daraus fuer den Bau folgt

1. **Sortierung ist ein eigener Modus**, kein Argument an der Fusion. Vorbild ist `lexical_only`: `semantic = None`, keine RRF, `Candidate.score = 0.0`. Der Grund ist nicht Sauberkeit, sondern dass `_ranked` (Zeile 142) das erste Tupelglied ungeprueft als `score` liest und sonst ein Zeitstempel als Relevanz aus dem Container faellt.
2. **`_ranked` braucht unter Sortierung einen eigenen Zweig.** Die Funktion nimmt heute `hits: Sequence[tuple[float, DocAddress]]` und baut `(file_id, float(score), mtime)`. Unter Sortierung muss sie `0.0` einsetzen statt `float(score)`. Kleinster ehrlicher Eingriff: ein Schluesselwortargument `scored: bool = True`, und der Sortierpfad ruft mit `scored=False`.
3. **Der Zweitschluessel `file_id` ist Handarbeit.** tantivy kennt keine Mehrfeld-Sortierung, und `order_by_field` auf einem zweiten Feld gibt es nicht. Empfehlung: jede vom Suchlauf geholte Portion vor dem Rechte-Vorfilter mit `sorted(portion, key=lambda c: (-c.mtime, -c.file_id))` (Desc) beziehungsweise `(c.mtime, c.file_id)` (Asc) stabil nachsortieren. Ehrliche Grenze, die in den Kommentar gehoert: eine Gleichstandsgruppe, die genau an einer Portionsgrenze zerfaellt, ist portionsweise sortiert und nicht global. Das erzeugt weder Duplikate noch Luecken (die Engine-Reihenfolge darunter bleibt konsistent, siehe Messung), nur eine Reihenfolge innerhalb einer Sekunde, die an einer Seitengrenze nicht dem Zweitschluessel folgt. Die Alternative (Ueberholen bis zur Gleichstandsgrenze) kostet einen unbegrenzten Nachschlag und ist den Gewinn nicht wert.
4. **Der Fortsetzungszweig (Abschnitt 2 von `candidates`, Zeile 451-470) faellt im Sortiermodus weg** beziehungsweise wird zum einzigen Zweig: ohne Fusion gibt es kein Fenster, hinter dem fortgesetzt werden muesste. Der sauberste Zuschnitt ist eine eigene Schleife, die `searcher.search(query, chunk_limit, order_by_field=FIELD_MTIME, order=..., offset=raw_cursor)` ruft, durch `_permit` schickt und bei `needed` abbricht; `SEARCH_SCAN_MAX = 10_000` bleibt die Decke.

---

## Befund 3: since/until ohne Reindex, und die stille Falle daneben

`FIELD_MTIME` ist `indexed=False, fast=True` (`index/schema.py:114`). Die naheliegende Sorge, ein nicht indiziertes Feld koenne keine Bereichsabfrage tragen, ist **falsch**, und der naheliegende Reflex daneben ist gefaehrlich.

Signatur der installierten Bibliothek (`tantivy/tantivy.pyi`, Zeile 347):

```python
Query.range_query(schema, field_name, field_type, lower_bound=None, upper_bound=None,
                  include_lower=True, include_upper=True, use_inverted_index=False)
```

Gemessen:

| Aufruf | Ergebnis |
|--------|----------|
| `range_query(schema, "mtime", FieldType.Integer, 200, 400)` | Liefert korrekt die drei Dokumente mit 200, 300, 400 |
| Dasselbe mit `use_inverted_index=True` | **Null Treffer, keine Ausnahme, keine Warnung** |
| `range_query(..., 300, None)` (nur untere Grenze) | Liefert korrekt 300, 400, 500 |

[VERIFIED: eigene Probe, 16.09.2026]

**Das ist der wichtigste neue Fallstrick dieser Phase.** Wer beim Lesen von `indexed=False` reflexhaft `use_inverted_index=True` setzt, bekommt einen Zeitraumfilter, der immer null Treffer liefert, ohne dass irgendetwas rot wird: auf der Seite sieht das aus wie "in diesem Zeitraum gibt es nichts". Der Vorgabewert `False` ist der richtige, und er gehoert mit genau dieser Begruendung in einen Kommentar, weil er sonst beim naechsten Umbau "korrigiert" wird.

Semantik-Empfehlung: `since` inklusiv, `until` inklusiv (`include_lower=True, include_upper=True`, beides Vorgabe), beide optional und unabhaengig. `mtime` ist Unix-Epoche in Sekunden: `QueueService.php:781` und `StorageService.php:415` schreiben `$node->getMTime()`, `nc/files.py:231` und `nc/queue.py:331` lesen es als ganze Zahl, `index/writer.py:272` schreibt es per `add_integer`. Damit ist der Vergleich zeitzonenfrei. [VERIFIED: Quellcode beider Haelften]

---

## Befund 4: EIN Filtervokabular; heute existiert noch gar keines

Die Erwartung "die bestehende `type:`-Textsyntax definiert irgendwo Extension-Listen" trifft **nicht** zu. `extract_filters` (rewrite.py:203-204) nimmt den Text hinter `type:` woertlich, kleingeschrieben, fuehrenden Punkt entfernt, und macht daraus einen Rohterm auf `ext`. Es gibt heute keine Gruppe, keine Tabelle und keine Menge. Die sechs UI-Gruppen bringen das Vokabular also erst mit, und "EIN Vokabular" heisst folglich: **die neue Gruppentabelle ist die einzige Quelle, und die Textsyntax wird an sie angeschlossen**, nicht umgekehrt.

Empfohlene Ausgestaltung (Claude's Discretion, aber mit einer konkreten Empfehlung):

- Eine Tabelle `TYPE_GROUPS: Final[Mapping[str, tuple[str, ...]]]` in `query/rewrite.py` (dort, wo `_extension_query` steht), Gruppennamen englisch und kleingeschrieben, weil sie in der URL stehen und Wire-Vokabular sind.
- `build_query(index, text, *, title_only=False, groups=())` loest die Gruppen ueber die Tabelle auf, vereinigt sie mit den `type:`-Endungen aus dem Text und baut EINE `Should`-Gruppe daraus. Und-Verknuepfung von Text und UI-Filter waere die Alternative; die Vereinigung ist die bessere, weil `type:pdf` plus Chip "Bilder" sonst garantiert leer ist und der Nutzer nicht sieht, warum.
- `extract_filters` erhaelt zusaetzlich: ein `type:`-Wort, das ein Gruppenname ist, wird ueber dieselbe Tabelle expandiert. Damit ist `type:images` gleichbedeutend mit dem Chip, und es gibt wirklich nur ein Vokabular. Falls das den Plan zu breit macht, ist der Verzicht darauf vertretbar, muss dann aber ausdruecklich entschieden werden.

### Das Endungsuniversum, gegen die Nextcloud-Zuordnung geprueft

Der Indexer laesst 18 Mimetypes zu (`extract/dispatch.py:100`, Spiegel in `php/lib/Service/StorageService.php:112-129`). Welche Endungen daraus real in `ext` landen koennen, ergibt die Mimetype-Zuordnung des Servers (`resources/config/mimetypemapping.dist.json`, stable33):

| Mimetype | moegliche Endungen |
|---|---|
| application/pdf | `pdf` |
| ...wordprocessingml.document | `docx` |
| ...spreadsheetml.sheet | `xlsx` |
| ...presentationml.presentation | `pptx` |
| opendocument.text / .spreadsheet / .presentation | `odt` / `ods` / `odp` |
| text/rtf, application/rtf | `rtf` |
| text/csv | `csv` |
| text/html | `htm`, `html` |
| text/markdown | `markdown`, `md`, `mdown`, `mdwn`, `mkd` |
| text/plain | `adoc`, `asciidoc`, `cnf`, `conf`, `eml`, `fb2`, `htaccess`, `js`, `json`, `org`, `ovpn`, `schema`, `text`, `txt`, `xml`, `yaml`, `yml` |
| image/jpeg | `jpeg`, `jpg`, `jps`, `mpo` |
| image/png | `png` |
| image/tiff | `tif`, `tiff` |
| image/webp | `webp` |

[VERIFIED: `nextcloud/server` stable33, `resources/config/mimetypemapping.dist.json`, abgeglichen gegen die eigene Allowlist]

Zwei Beobachtungen, die den Zuschnitt bestimmen:

1. **`jpg` und `jpeg` sind beide real**, ebenso `tif` und `tiff`. Eine Bildgruppe, die nur `jpg` kennt, verliert Dateien mit sichtbar gleichem Symbol. Das ist Pitfall 8 in konkreter Form.
2. **`application/xhtml+xml` hat in der Zuordnung gar keine Endung**, und `svg` faellt auf `image/svg+xml` (nicht in der Allowlist) und wird deshalb nie indiziert. Zwei Sorgen weniger.
3. Die Textgruppe ist die einzige, die als vollstaendige Aufzaehlung unsinnig waere. Empfehlung: `txt`, `text`, `md` und die vier Markdown-Varianten, `csv` gehoert zu Tabellen, `htm`/`html`, plus die Konfigurations- und Datenendungen als bewusste Auswahl. Was nicht in der Tabelle steht, ist unter keinem Chip erreichbar, und genau dieser Satz gehoert in `docs/`.
4. **Dateien ohne Endung sind unter keinem Filter erreichbar.** `extension_of` (dispatch.py:161) liefert dafuer den leeren String, und ein leeres Raw-Feld erzeugt keinen Term, den eine `term_query` je treffen koennte. Das ist Variante eins aus PITFALLS Pitfall 8 und die richtige: die Alternative braucht ein Feld, das es nicht gibt. In die Doku, nicht in den Code.

**Grossschreibung:** `extension_of` schreibt klein, `extract_filters` liest klein, und der Raw-Tokenizer normalisiert nichts. Der neue strukturierte Parameter muss also selbst kleinschreiben, sonst trifft "PDF" nichts. Der Gruppenname aus der URL wird ebenfalls kleingeschrieben und gegen die geschlossene Tabelle geprueft; was nicht darin steht, bedeutet "kein Filter" (still, nach der Hausregel von `PageController`).

---

## Befund 5: Die Request-Modelle, `extra="forbid"` und wer welches Feld bekommt

| Modell | Datei | Heutige Felder |
|---|---|---|
| `SearchRequest` | `api/search.py:75` | `query`, `limit`, `offset`, `titleOnly` |
| `SnippetsRequest` | `api/snippets.py:71` | `query`, `fileIds`, `titleOnly` |

Beide tragen `model_config = ConfigDict(extra="forbid")`. Ein unbekanntes Feld ergibt HTTP 422 (nicht 400; `test_search_endpoint.py:142ff` haelt das fest). Auf der PHP-Seite landet ein 422 in `ExAppService::call()` Fall 2, wird zu `null`, und `SearchService` setzt `$silent = true`; die Seite zeigt dann den Fehlerblock "Die Suche antwortet gerade nicht". Der Versions-Lockstep (D-11) verhindert diesen Mischstand im Normalbetrieb, die Bauordnung Backend-vor-PHP bleibt trotzdem verbindlich. [VERIFIED: Quellcode + Test]

**Welches Feld wohin:**

| Feld | `SearchRequest` | `SnippetsRequest` | Begruendung |
|---|---|---|---|
| Typgruppen (z.B. `types: list[str]`) | ja | **ja** | Beruehrt `build_query`; `api/snippets.py:135` baut dieselbe Anfrage erneut auf. Pitfall 3. |
| `since` / `until` | ja | **ja** | Dito; sie sind Teil der Anfrage, nicht der Reihenfolge. |
| `sort` | ja | **nein** | Veraendert die Reihenfolge, nicht die Anfrage. Ein Sortierfeld im Schnitt waere ein Feld, das nichts tut und beim naechsten Umbau etwas tut (PITFALLS Pitfall 3, ausdruecklich). |

Damit ist der Gleichstands-Test **nicht** "beide Modelle tragen dieselben Felder", sondern "jedes Feld, das `build_query` beruehrt, steht in beiden". Ein Text-Gate nach dem Muster von `test_search_limits_lockstep.py` kann das: es liest beide Modelldefinitionen als Text, bildet die Feldmengen und prueft die Differenz gegen eine benannte Ausnahmeliste, in der `sort` mit seiner Begruendung steht. Eine Ausnahmeliste und keine Schwelle, genau wie `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` es vormacht.

**Validierungsmuster** (dem bestehenden Stil folgend): geschlossene Werte als `Literal[...]` beziehungsweise `list[Literal[...]]` mit `Field(default_factory=list, max_length=6)`, Zeitstempel als `int` mit `ge=0` und einer Obergrenze. Kein `str`-Freitext: das Feld reist ueber eine Route mit `access_level USER`, und ein freier String waere ein zweiter Weg in den Abfragebau.

**Drei Produktivaufrufe von `build_query`**, alle mit derselben Signaturaenderung: `api/search.py:194`, `api/snippets.py:135`, `api/diagnose.py:172`. Die Diagnoseroute braucht die Filter nicht zwingend, sollte sie aber bekommen, weil sie genau das Warnsignal misst, das FILT-01 absichert (leere semantische Liste unter Filter). [VERIFIED: grep ueber `backend/src`]

---

## Befund 6: Der Weg durch die PHP-Haelfte, und warum ein Wertobjekt

Heute:

```php
SearchService::run(IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $caps): SearchOutcome
ExAppService::searchCandidates(string $userId, string $term, int $limit, int $offset, bool $titleOnly, float $secondsLeft, float $ceilingSeconds): ?array
ExAppService::snippets(string $userId, string $term, array $fileIds, bool $titleOnly, float $secondsLeft, float $ceilingSeconds): array
```

Zwei Aufrufer von `run`: `PageController::outcome()` (Zeile 322) und `Search/Provider.php::search()` (Zeile 168).

Vier weitere positionale Parameter (`types`, `sort`, `since`, `until`) an drei Methoden ist die Bauform, die niemand mehr lesen kann. Das Repository hat dafuer bereits ein Muster: `SearchCaps` (`php/lib/Service/SearchCaps.php`), ein `readonly`-Wertobjekt mit sieben Feldern, das der Aufrufer ausschreibt. Empfehlung: ein zweites solches Objekt, etwa `SearchFilters` mit `types: list<string>`, `sort: string`, `since: ?int`, `until: ?int`, mit einer Konstanten-Liste der erlaubten Werte und einer statischen `none()`-Fabrik fuer den Dialogfall. Der Dialog uebergibt `types = []`, `sort = 'relevance'` und seine beiden Datumswerte; die Seite uebergibt alles.

`ExAppService` muss die Werte in den POST-Rumpf legen (Zeile 415 und 488) und dabei dieselbe Disziplin walten lassen wie bei `limit`: klemmen statt ablehnen, unbekannte Werte weglassen. Die Konstanten `MIN_LIMIT`/`MAX_LIMIT` zeigen das Muster.

**Wichtig fuer den Sortiermodus:** `sort` gehoert NICHT in den `/snippets`-Rumpf (Befund 5).

---

## Befund 7: Cursorpfad, Pfadbindung und FILT-04

`PageController::cursorPath()` (Zeile 274) prueft die **Form** und nicht die **Herkunft**: genau `$page` Eintraege, lauter Ziffern, streng aufsteigend, erster Eintrag 0. Jede Abweichung ergibt `[0]`, und Zeile 183-189 setzt dann `page = 1`. Es gibt heute keinerlei Bindung an den Suchbegriff oder an `names`.

Warum das heute reicht: das Formular (`templates/search.php:142`) traegt weder `page` noch `cursors`, also beginnt jede neue Suche ohnehin auf Seite eins. Ein Chip, der als `<a>` mit den aktuellen Parametern gebaut wird (D-02, D-03, D-05), nimmt den Pfad dagegen mit. [VERIFIED: Quellcode]

**Zwei Regeln, beide durchsetzbar:**

1. Jeder Chip-, Sortier- und Zuruecksetzen-Link wird aus `pageUrl()`-Bausteinen gebaut, die `page` und `cursors` **ausdruecklich weglassen**. Praktisch: eine zweite private Methode neben `pageUrl()` (etwa `filterUrl()`), die dieselben Wertargumente nimmt, aber nie einen Cursor schreibt. Zwei Methoden statt eines Flags, weil ein Flag beim naechsten Umbau falsch gesetzt wird.
2. Der Cursorpfad bekommt eine Fingerabdruck-Bindung: ein kurzer, nicht umkehrbarer Wert ueber (Begriff, `names`, Typgruppen, Sortierung, since, until) reist als eigener Parameter mit, und ein Pfad mit fremdem Fingerabdruck faellt still auf Seite eins zurueck. Das ist genau die Behandlung, die `cursorPath` heute schon fuer jede Abweichung vorsieht, und sie bleibt stumm, wie der Kommentar dort es verlangt. Empfehlung zur Ausgestaltung: `substr(hash('xxh128', $kanonisierterZustand), 0, 8)` oder `sha256` gekuerzt; es ist kein Sicherheitsmerkmal, sondern eine Verwechslungssperre, deshalb reicht kurz und braucht kein Geheimnis. Kanonisierung (sortierte Typliste, normalisierte Zahlen) vor dem Hashen, sonst faellt ein Nutzer beim Umsortieren derselben Auswahl auf Seite eins.

Abnahme: ein Fall in `php/tests/Unit/PageControllerTest.php` nach dem Muster von `testACursorPathThatDoesNotCheckOutIsPageOne` (Zeile 243), der einen Pfad aus einer ungefilterten Suche mit gesetztem Filter einreicht und Seite eins erwartet.

---

## Befund 8: "Geaendert am ..." braucht KEINE Protokollaenderung

D-04 verlangt das Aenderungsdatum je Treffer unter Datums-Sortierung. Der naheliegende Weg (mtime ueber die Wire durchreichen) ist der schlechtere und waere ein Bruch:

`ExAppService::filterCandidates()` (Zeile 761) laesst von einem Kandidaten **ausschliesslich** `fileId` durch; Titel und Ausschnitt nur fuer den Kanarienvogel mit `fileId = 0`. Der Docstring sagt warum: alles, was vor dem Recheck ankommt, ist ein Vorschlag, und ein Vorschlag, der die Anzeige erreicht, ist genau die Offenlegung, gegen die das Zweistufenprotokoll gebaut ist. (Das Backend-Modell `Candidate` traegt `mtime: int = 0`, aber PHP verwirft es heute.)

Der bessere Weg liegt bereits offen: `SearchService::run()` loest jeden bestaetigten Kandidaten ohnehin zu einem `File`-Knoten auf (Zeile 324) und liest daraus Name, Pfad und Mimetype (Zeile 341-358). `$node->getMTime()` steht an derselben Stelle zur Verfuegung und ist **aktueller als der Index**. Also: `ApprovedHit` (heute vier Felder) bekommt ein fuenftes, `mtime`, aus dem bestaetigten Knoten; fuer den Kanarienvogel (`fileId = 0`, kein Knoten) bleibt es `0`.

Formatierung: `OCP\IDateTimeFormatter::formatDate($timestamp, 'long', $timeZone, $l)` ist seit NC 8.0.0 oeffentlich und im Fenster 33 bis 35 vorhanden. Das spart eine eigene Datumsformat-Zeichenkette im Katalog; im Katalog steht nur das Etikett ("Geaendert am %s"). Neue Konstruktorabhaengigkeit in `PageController` bedeutet: `PageControllerTest::setUp()` bekommt einen weiteren Mock. [VERIFIED: `nextcloud/server` stable33 `lib/public/IDateTimeFormatter.php`; eigener Quellcode]

---

## Befund 9: Der Datumsfilter des Unified-Search-Dialogs, Mechanik nachgelesen

Heute meldet `Search/Provider.php::getSupportedFilters()` (Zeile 132) genau `[IFilter::BUILTIN_TERM, IFilter::BUILTIN_TITLE_ONLY]`.

Upstream-Mechanik (stable33 gelesen):

- `IFilter` definiert `BUILTIN_TERM='term'`, `BUILTIN_SINCE='since'`, `BUILTIN_UNTIL='until'`, `BUILTIN_PERSON`, `BUILTIN_TITLE_ONLY='title-only'`, `BUILTIN_PLACES`, `BUILTIN_PROVIDER`, alle `@since 28.0.0`. [CITED: nextcloud/server stable33 `lib/public/Search/IFilter.php`]
- `SearchComposer::buildFilter()` wirft `UnsupportedFilter`, wenn ein exklusiver Filter gesetzt ist, den der Provider nicht deklariert. `UnifiedSearchController::search()` faengt das und antwortet **HTTP 400** fuer diesen Provider. [CITED: nextcloud/server stable33 `lib/private/Search/SearchComposer.php`, `core/Controller/UnifiedSearchController.php`]
- `SearchComposer::getProviders()` liefert je Provider ein Feld `filters` (aus `getSupportedFilters()` plus `getCustomFilters()`), an dem die Oberflaeche ablesen kann, welche Provider sie unter den aktiven Filtern ueberhaupt fragen darf.

Netto: mit gesetztem Datumsfilter verschwindet Findling aus dem Dialog, entweder weil die Oberflaeche ihn nicht mehr fragt oder weil seine Gruppe mit 400 endet. Beides ist fuer den Nutzer dasselbe Bild, und FILT-03 beschreibt es richtig. Die Reparatur ist eine Zeile plus Wirkung: `BUILTIN_SINCE` und `BUILTIN_UNTIL` in `getSupportedFilters()`, und `Provider::search()` liest sie ueber `$query->getFilter(IFilter::BUILTIN_SINCE)?->get()`.

**Wichtig:** der Wert ist ein `\DateTimeImmutable` (`lib/private/Search/Filter/DateTimeFilter.php`; der Konstruktor akzeptiert eine ganze Zahl als Epoche oder eine Datumszeichenkette). `->getTimestamp()` liefert die Epoche direkt, also zeitzonenfrei und direkt gegen `mtime` vergleichbar. Defensiv behandeln wie `titleOnly()` (Zeile 253): alles, was nicht die erwartete Klasse ist, gilt als nicht gesetzt.

**`getCustomFilters()` bleibt leer.** Ein Typfilter im Dialog braucht eine `FilterDefinition`, und ein Name ohne Definition macht laut dem Kommentar in `Provider.php` die ganze Providerliste kaputt. Dateityp und Sortierung gehoeren in v1.2 ausschliesslich auf die eigene Seite.

---

## Befund 10: Die Zeitzonen-Falle der Schnellbereiche

`mtime` ist Epoche in Sekunden, also zeitzonenfrei. Der Dialogpfad ist deshalb unkritisch: `DateTimeImmutable::getTimestamp()` liefert die Grenze, die der Nutzer gemeint hat.

Die Falle sitzt bei D-05, den serverseitig berechneten Schnellbereichen. "Heute" ist keine Epochenzahl, sondern eine Aussage ueber einen Kalendertag, und der beginnt in der Zeitzone des Nutzers. Wer `strtotime('today')` oder `new DateTimeImmutable('today')` ohne Zeitzone rechnet, nimmt die PHP-Standardzeitzone des Servers (haeufig UTC) und liegt fuer einen Nutzer in Europa/Berlin um ein bis zwei Stunden daneben; in der Nacht bedeutet das, dass "Heute" die Dateien der letzten Stunden **nicht** enthaelt.

Richtiger Weg: `OCP\IDateTimeZone::getTimeZone()` (`@since 8.0.0`, im Fenster 33 bis 35 vorhanden) liefert die Zeitzone des angemeldeten Nutzers, Sommerzeit beruecksichtigt. Damit:

```php
$zone = $this->dateTimeZone->getTimeZone();
$now = new \DateTimeImmutable('now', $zone);
$since = $now->setTime(0, 0, 0)->getTimestamp();           // Heute
$since = $now->modify('-7 days')->setTime(0, 0, 0)->getTimestamp();   // 7 Tage
$since = $now->setDate((int)$now->format('Y'), 1, 1)->setTime(0, 0, 0)->getTimestamp(); // Dieses Jahr
```

[VERIFIED: `nextcloud/server` stable33 `lib/public/IDateTimeZone.php`]

Entscheidung, die der Plan treffen muss (Claude's Discretion laut D-05): Kalenderfenster ("Heute" = seit Mitternacht) oder rollierendes Fenster ("7 Tage" = seit jetzt minus 168 Stunden). Empfehlung: **Kalenderfenster mit Tagesgrenze**, weil "Heute" und "Dieses Jahr" ohnehin Kalenderbegriffe sind und ein gemischtes Modell auf einer Leiste nebeneinander niemand erklaeren kann. Der Chip setzt `since` und laesst `until` leer.

---

## Befund 11: Die Kataloge sind der groesste unterschaetzte Posten

Sechs Dateien: `php/l10n/{de,de_DE,fr}.{js,json}`. Stand heute **174 Schluessel je Datei** (nachgezaehlt).

Vier Gates in `backend/tests/test_admin_ui_contract.py`, und sie gelten fuer die ganze App, nicht nur fuer die Adminseite:

| Gate | Zeile | Was rot wird |
|---|---|---|
| G1 Schluesselmengen | `test_all_six_catalogues_carry_the_same_keys` | Ein Schluessel fehlt in einer der sechs Dateien |
| Deutsche Zwillinge | `test_the_german_catalogue_covers_both_german_language_codes` (Zeile 1051) | `de_DE.json` ist nicht **textgleich** mit `de.json` (und `de_DE.js` nicht mit `de.js`), **und** `assert len(keys_of["de.json"]) == 174` |
| G2 Franzoesische Vollstaendigkeit | `scan_french_completeness` (Zeile 353) | Ein franzoesischer Wert ist leer **oder gleich seinem englischen Schluessel**, ausser er steht namentlich in `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` (heute zwei Eintraege: "Findling", "Page %s") |
| G3 Platzhalter-Paritaet | `scan_placeholder_parity` (Zeile 373) | Ein Wert traegt andere `%s`/`%1$s`/`%n`/`%%`-Direktiven als sein Schluessel |
| Prosa-Gate | `test_no_file_of_the_page_carries_a_dash_or_an_emoji` | Ein Gedankenstrich oder ein Emoji in einem Katalog |

[VERIFIED: Quellcode der Gates, eigene Zaehlung der Kataloge]

**Drei konkrete Konsequenzen fuer den Plan:**

1. Die harte Zahl `174` steigt und muss **im Gate** geaendert werden, samt der Docstring-Begruendung. Der bestehende Docstring erklaert ausdruecklich, warum sie zuletzt von 173 auf 174 stieg, und schreibt vor, dass die naechste Erhoehung ebenso begruendet wird ("Ohne diesen Absatz nimmt der naechste Leser eine erhoehte Zahl fuer Schlamperei und senkt sie wieder"). Das ist eine Planaufgabe, kein Nebenprodukt.
2. `docs/l10n-french.md` zaehlt seine Abdeckung gegen genau diesen Schluesselsatz und muss mitziehen.
3. **Die franzoesische Gleichwort-Falle trifft diese Phase mehrfach.** Wahrscheinliche Labels und ihre franzoesischen Entsprechungen:

| Englischer Schluessel | Franzoesisch | G2-Konflikt? |
|---|---|---|
| `PDF` | PDF | **ja**, Ausnahme noetig |
| `Documents` | Documents | **ja**, Ausnahme noetig |
| `Images` | Images | **ja**, Ausnahme noetig |
| `Spreadsheets` | Feuilles de calcul | nein |
| `Presentations` | Presentations (mit Akzent) | nein, wenn der Akzent gesetzt wird |
| `Text` | Texte | nein |
| `Relevance` | Pertinence | nein |

Jede Ausnahme braucht einen Eintrag in `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` **mit Begruendung** und einen Absatz in `docs/l10n-french.md`. Die Liste ist bewusst eine Liste und keine Schwelle; sie waechst also sichtbar.

Nebenbei: `Presentations` mit Akzent im franzoesischen Wert, aber der englische Schluessel ohne, ist zugleich die Loesung fuer den Gleichwort-Konflikt und die korrekte Uebersetzung. Umlaute und Akzente in den Katalogen sind echte Zeichen (Projektregel), im Code dagegen nie.

**Stilvorgaben aus denselben Gates:** keine Farbliterale in `php/css/search.css` (nur `var(--color-...)`), kein entfernter Fokusring, kein Inline-Skript, kein `style`-Attribut, jede Ausgabe durch `p()`. Die Chips sind Links, also brauchen sie einen sichtbaren aktiven Zustand, der nicht allein ueber Farbe funktioniert (`aria-pressed` ist fuer `<a>` falsch; besser `aria-current="true"` am aktiven Chip).

---

## Befund 12: FILT-05, und warum der Paritaetstest eine Richtungsentscheidung braucht

Der Paritaetsjob (`.github/workflows/integration.yml`, Job `search-parity`, ab Zeile 2611) stellt je Szenario dieselbe Frage dreimal: OCS-Provider `files`, OCS-Provider `findling`, und seit Phase 9 die Ergebnisseite ueber `ask_page` (Zeile 2961), die die Treffer-IDs aus den Zeilen-IDs `findling-hit-<n>` liest. `scripts/ci/parity_diff.py` vergleicht sie als Mengen in **beiden** Richtungen:

- `missing`: die native Suche zeigt es, Findling nicht. Funktionsdefekt.
- `extra`: Findling zeigt es, die native Suche demselben Nutzer nicht. **Das ist die Richtung, die die Rechtegrenze beruehrt.**
- `--expect-min` ist Pflicht und gilt fuer alle drei Mengen (Schutz gegen gruen ueber leeren Mengen).

[VERIFIED: Quellcode von Workflow und Werkzeug]

**Das Problem, das der Plan loesen muss:** ein gefilterter oder auf einen Zeitraum eingegrenzter Lauf hat naturgemaess **weniger** Treffer als die native Suche. Ein naiver zweiter Aufruf von `compare()` mit `types=...` wuerde also `missing` melden, obwohl nichts kaputt ist. Drei gangbare Wege, der dritte ist der empfohlene:

1. Filter waehlen, der nichts wegnimmt: die Markerdateien des Fixtures sind alle `.txt`, also liefert `types=text` dieselbe Menge wie ungefiltert. Billig, aber es prueft die Grenze nur schwach, weil nichts gefiltert wird.
2. `parity_diff.py` um einen Modus erweitern, der nur die `extra`-Richtung prueft. Aendert ein Werkzeug, dessen Rot-Faehigkeit eigens abgesichert ist (`test_parity_diff.py`), also mit eigenem Selbsttest.
3. **Beides, in zwei Szenarien:** ein gefilterter Lauf mit `types=text` (Menge identisch, beide Richtungen scharf, `--expect-min` unveraendert) und ein sortierter Lauf (`sort=newest`, Menge identisch, nur die Reihenfolge anders, deshalb auch beide Richtungen scharf). Beide kosten je einen `ask_page`-Aufruf und keine Werkzeugaenderung. Zusaetzlich ein Lauf mit einem Filter, der **wegnimmt** (`types=images` auf einem `.txt`-Fixture) und mit `--expect-min 0` nur die `extra`-Richtung belegt, indem die erwartete Findling-Menge leer ist.

Der Punkt, den FILT-05 wirklich verlangt, ist am Ende einfach: **kein neuer Pfad an der Rechtegrenze.** Die beiden Gates, die das halten, sind `test_php_acl_boundary.py` (zaehlt die Aufrufstellen von `getFirstNodeById` und `isReadable` und fuehrt ein benanntes Register) und `test_php_trust_boundary.py` (zaehlt Route-Attribute; deshalb darf die Prosa in `PageController.php` weiterhin **kein** Route-Attribut beim Namen nennen). Beide bleiben gruen, solange der Filter vor dem Vorfilter wirkt und keine Route dazukommt.

---

## Befund 13: Testbestand und wo die neuen Faelle hingehoeren

| Datei | Deckt heute | Was Phase 13 dort braucht |
|---|---|---|
| `backend/tests/test_query_rewrite.py` | `build_query`, `extract_filters`, `carried_operators`, `type:`-Faelle (Zeile 145-260) | Gruppen zu Endungen, Vereinigung Text plus Gruppen, **Negativfall: der Gruppenparameter setzt `FILETYPE` NICHT** |
| `backend/tests/test_search_library.py` | `candidates()`: Vorfilter, keine Namen, kein Gesamtwert, Nutzer ohne Rechtezeile | Sortierzweig (Score 0.0, Reihenfolge, Zweitschluessel), Filter vor dem Fenster, `_mtimes_of` unter Filter |
| `backend/tests/test_semantic_search.py` | Hybridpfad | Erfolgskriterium 1: Paraphrase findet unter Filter dasselbe Dokument |
| `backend/tests/test_search_endpoint.py` | 422 bei unbekanntem Feld, Kanarienvogel | Neue Felder akzeptiert, unbekannte Werte weiterhin 422 |
| `backend/tests/test_snippets_endpoint.py` | Ausschnittsroute | Neue Felder im Gleichstand, `sort` **abgelehnt** |
| neu: `test_search_fields_lockstep.py` | -- | Gleichstands-Gate der beiden Modelle mit benannter `sort`-Ausnahme (Muster: `test_search_limits_lockstep.py`) |
| `backend/tests/test_admin_ui_contract.py` | Katalog- und Oberflaechen-Gates, Zahl `174` | Neue Zahl, neue G2-Ausnahmen, Leerzustands-Gate (`$showEmpty` muss weiterhin `$hasError`, `$hasHint`, `$hasQuery` lesen) |
| `php/tests/Unit/PageControllerTest.php` | Adressleisten-Vertrag, Cursorpfad, Pager | Unbekannte Typ-/Sortierwerte fallen still zurueck; Cursorpfad mit fremdem Fingerabdruck ist Seite eins; Chip-Links tragen kein `page`/`cursors` |
| `php/tests/Unit/ProviderTest.php` | Dialog-Provider | `getSupportedFilters()` meldet since/until; ein `DateTimeImmutable` wird zur Epoche; kaputter Filterwert gilt als nicht gesetzt |
| `php/tests/Unit/SearchServiceTest.php` | Recheck, Rundenlogik | Filter reisen unveraendert an beide Containeraufrufe; `mtime` kommt aus dem Knoten |
| `php/tests/Unit/ExAppServiceTest.php` | Rumpfbau, vier Fehlerpfade | Neue Rumpffelder, Klemmen statt Ablehnen |
| `scripts/ci/parity_diff.py` + `test_parity_diff.py` | Paritaet in beiden Richtungen | Siehe Befund 12 |
| `docs/testing.md` | Registertabelle aller Gates | Neue Gates eintragen (Hausregel: jedes Gate hat dort eine Zeile mit "was es NICHT beweist") |

Alle Pfade laufen mit: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run vulture src tests --min-confidence 80`, `uv run pytest -q` (aus `backend/`); PHP ueber `vendor/bin/phpunit`. `ruff` laeuft zusaetzlich ueber `../scripts`. [VERIFIED: `.github/workflows/python.yml`, `php.yml`]

---

## Architecture Patterns

### Datenfluss einer gefilterten, sortierten Suche

```
Browser (GET /apps/findling/?query=..&types=pdf,images&sort=newest&since=..&page=..&cursors=..&fp=..)
  |
  v
PageController::index()
  |-- term(), pageNumber(), cursorPath()            [alle still zurueckfallend]
  |-- filters(): geschlossene Werte -> SearchFilters
  |-- Fingerabdruck gegen ?fp  -> Abweichung = Seite 1
  v
SearchService::run(user, term, titleOnly, startCursor, caps, filters)
  |
  |  Schleife ueber max. 3 Runden:
  |   |-- ExAppService::searchCandidates(... + types/sort/since/until)  --POST /search-->
  |   |-- je Kandidat: getFirstNodeById() + isReadable()   [DIE Rechtegrenze, unveraendert]
  |   '-- ApprovedHit(fileId, title, path, mimeType, mtime aus dem Knoten)
  |
  '-- ExAppService::snippets(... + types/since/until, OHNE sort)        --POST /snippets-->
  v
templates/search.php: Chips, Sortierlinks, Trefferliste, Leerzustand, Pager
```

Im Container:

```
POST /search  ->  SearchRequest (extra=forbid)
  |
  v
one_round()
  |-- build_query(index, text, title_only, groups=..., since=..., until=...)
  |     |-- extract_filters()  (type:-Text)          -> Endungen A
  |     |-- TYPE_GROUPS[...]   (UI-Gruppen)          -> Endungen B
  |     |-- Should(A u B) als Occur.Must an die geparste Anfrage
  |     '-- range_query(mtime, since, until, use_inverted_index=False) als Occur.Must
  |
  |-- sort == relevance ?
  |     ja  -> semantic = SemanticSide(...) sofern erlaubt
  |     |      candidates(): Fenster -> RRF -> _mtimes_of(MIT Filterklausel) -> Baender -> Fortsetzung
  |     nein -> semantic = None
  |            candidates(): EIN Zweig, searcher.search(order_by_field=mtime, order=..., offset=..),
  |                          Portion nach (-mtime, -file_id) stabilisiert, score = 0.0, keine RRF
  v
CandidatePage(candidates, has_more, next_offset)
```

### Empfohlener Dateizuschnitt

```
backend/src/findling/
  query/rewrite.py        # TYPE_GROUPS, build_query(..., groups=, since=, until=), _extension_query,
                          # neue _mtime_range_query
  index/search.py         # SortOrder-Konstanten, candidates(): Sortierzweig, _ranked(scored=),
                          # _mtimes_of(..., filter_query=)
  api/search.py           # SearchRequest: types, sort, since, until
  api/snippets.py         # SnippetsRequest: types, since, until  (KEIN sort)
  api/diagnose.py         # dieselbe build_query-Signatur
php/lib/
  Service/SearchFilters.php   # neues readonly-Wertobjekt nach dem Muster von SearchCaps
  Service/SearchService.php   # run(..., SearchFilters), ApprovedHit um mtime
  Service/ApprovedHit.php     # fuenftes Feld
  Service/ExAppService.php    # Rumpffelder, Klemmen
  Search/Provider.php         # getSupportedFilters() + since/until lesen
  Controller/PageController.php  # filters(), filterUrl(), Fingerabdruck, Template-Parameter
php/templates/search.php    # Chip-Leiste, Sortierlinks, Datumszeile, Leerzustand
php/css/search.css          # Chips, aktiver Zustand (nur CSS-Variablen)
php/l10n/*.{js,json}        # sechs Dateien im Gleichstand
```

### Anti-Patterns to Avoid

- **Den Filter in PHP hinter dem Recheck anwenden.** Macht aus jeder Seite eine Stichprobe und eroeffnet eine zweite Stelle an der Rechtegrenze. `test_php_acl_boundary.py` wird rot, und zwar zu Recht.
- **Eine JSON-Route fuer die Chips.** Bricht den Entwurfsvertrag der Seite und `test_php_trust_boundary.py`.
- **Trefferzaehler je Typ.** Braucht ein Fast-Field auf `ext` (also Reindex) und waere ein Zaehl-Orakel vor dem Rechtefilter (T-02-93). Ausdruecklich ausgeschlossen.
- **`use_inverted_index=True` beim Zeitraumfilter.** Liefert stillschweigend nichts (Befund 3).
- **Ein zweites Typvokabular in PHP.** Die Seite kennt Gruppennamen, der Container kennt Endungen; eine Abbildung von Mimetype auf Endung im PHP-Code ist das Warnsignal aus Pitfall 8.
- **Sortierung an `/snippets`.** Ein Feld, das nichts tut und beim naechsten Umbau etwas tut.

---

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---|---|---|---|
| Zeitraum-Eingrenzung auf `mtime` | Nachtraegliches Filtern der Kandidaten in Python oder PHP | `Query.range_query(..., use_inverted_index=False)` als `Occur.Must` | Nachtraegliches Filtern erzeugt halbleere Seiten hinter dem Fusionsfenster; der Fast-Field-Bereich kostet nichts und ist verifiziert |
| Datumssortierung | Eigenes Sortieren der 100er-Kandidatenliste | `searcher.search(..., order_by_field=FIELD_MTIME, order=Order.Asc/Desc, offset=..)` | Eine Liste nachzusortieren sortiert die relevantesten hundert Dokumente aller Zeiten, nicht die hundert neuesten |
| Zeitzone des Nutzers | `date_default_timezone_get()` oder eine Instanzeinstellung selbst lesen | `OCP\IDateTimeZone::getTimeZone()` | Sommerzeit, Nutzerpraeferenz, seit NC 8 stabil |
| Datum anzeigen | Eigenes `date()`-Format je Sprache | `OCP\IDateTimeFormatter::formatDate()` | Sonst ein zusaetzlicher Katalogschluessel je Sprache, der die Gates beruehrt, und ein falsches Format in `fr` |
| Aenderungsdatum beschaffen | `mtime` durch `filterCandidates()` durchlassen | `$node->getMTime()` am bereits bestaetigten Knoten | Aktueller, keine Protokollaenderung, kein Vorschlagswert vor dem Recheck |
| Endungen je Gruppe | Frei erfundene Liste | Ableitung aus der eigenen Mimetype-Allowlist ueber `mimetypemapping.dist.json` | `jpg`/`jpeg`, `tif`/`tiff`, fuenf Markdown-Schreibweisen; eine erfundene Liste verliert Dateien mit sichtbar gleichem Symbol |
| Cursorbindung | Ein Zufallswert in der Sitzung | Kurzer Hash ueber den kanonisierten Anfragezustand in der URL | Die Adresse muss teilbar und lesezeichenfaehig bleiben; die Sitzung waere ein Zustand, den ein Lesezeichen nicht mitbringt |

**Kernaussage:** in dieser Phase ist fast jede "billige" Variante genau die, die eine bestehende Zusage still aufgibt. Der teure Weg ist hier der kurze.

---

## Common Pitfalls

### Pitfall A: `use_inverted_index=True` beim Zeitraumfilter
**Was schiefgeht:** since/until liefert immer null Treffer.
**Warum:** `FIELD_MTIME` ist `indexed=False`. Wer das liest, setzt reflexhaft `use_inverted_index=True`; tantivy 0.26.0 antwortet dann mit einer leeren Trefferliste **ohne Ausnahme**.
**Vermeidung:** Vorgabewert `False` lassen und mit dieser Begruendung kommentieren.
**Warnzeichen:** jeder Zeitraum-Chip zeigt den Leerzustand, auch "Dieses Jahr".

### Pitfall B: Der Filter wirkt nur auf die lexikalische Haelfte
**Was schiefgeht:** Unter Chip "PDF" erscheinen `.docx`-Treffer, die die semantische Haelfte beigesteuert hat.
**Warum:** `build_query` beruehrt nur die Engine-Anfrage; Vektor-Treffer kommen ueber `_mtimes_of` in `known` und von dort in `merged`.
**Vermeidung:** dieselbe Filterklausel als `Occur.Must` in die `_mtimes_of`-Abfrage.
**Warnzeichen:** ein Treffer der falschen Gruppe steht in der gefilterten Liste, aber die Diagnoseroute (`ranked_sides`) fuehrt ihn nur auf der semantischen Seite.

### Pitfall C: Zeitstempel als Relevanz
**Was schiefgeht:** `Candidate.score` traegt Werte in der Groessenordnung 1.7e9.
**Warum:** unter `order_by_field` ist das erste Tupelglied der Feldwert (gemessen: 500/400/300/200/100 statt 0.087).
**Vermeidung:** eigener Sortiermodus, `_ranked` mit `scored=False`, `score = 0.0`, keine RRF.
**Warnzeichen:** zwei Suchen mit denselben Treffern liefern unter verschiedenen Sortierungen unterschiedliche Treffer**mengen** und nicht nur Reihenfolgen.

### Pitfall D: Der Cursorpfad ueberlebt den Chipklick
**Was schiefgeht:** Ein Klick auf einen Chip auf Seite 7 landet auf Seite 7 einer anderen Ergebnismenge; Treffer werden uebersprungen oder doppelt gezeigt, ohne Fehlermeldung.
**Warum:** `cursorPath()` prueft die Form und nicht die Herkunft.
**Vermeidung:** Chip-Links ohne `page`/`cursors` bauen **und** den Fingerabdruck binden. Beides, nicht eines von beiden: die Adresse ist von Hand editierbar.
**Warnzeichen:** `nextUrl` ist `null`, obwohl `hasMore` wahr ist.

### Pitfall E: Die Katalogzahl 174
**Was schiefgeht:** Der Plan ist fertig, die Seite sieht gut aus, und `test_admin_ui_contract.py` ist rot mit "the four catalogues disagree" oder mit einem Zahlenvergleich.
**Warum:** harte Zahl im Gate, textgleiche deutsche Zwillinge, franzoesisches Vollstaendigkeits-Gate.
**Vermeidung:** Kataloge als eigener Planschritt am Ende, mit allen sechs Dateien, der neuen Zahl, der Gate-Docstring-Begruendung, den G2-Ausnahmen und `docs/l10n-french.md`.
**Warnzeichen:** ein Label, das in allen drei Sprachen gleich heisst ("PDF", "Documents", "Images").

### Pitfall F: Der Leerzustand widerspricht dem Banner
**Was schiefgeht:** Ueber "Keine Treffer mit den aktiven Filtern" steht "Die Suche antwortet gerade nicht".
**Warum:** D-07 fuegt einen dritten Leerzustand hinzu, und das Gate `test_the_empty_state_of_the_page_does_not_speak_over_a_banner` prueft, dass die `$showEmpty`-Entscheidung `$hasError`, `$hasHint` und `$hasQuery` liest.
**Vermeidung:** die neue Filtervariante **innerhalb** des bestehenden `$showEmpty`-Blocks als zusaetzlicher Zweig, nicht als eigener Block daneben.
**Warnzeichen:** das Gate meldet "the $showEmpty decision does not read ...".

### Pitfall G: Sortierung auf grossem Fremdbestand liefert systematisch leer
**Was schiefgeht:** Ein Nutzer mit dreissig eigenen Dateien auf einer Instanz mit 52.000 fremden waehlt "Zuletzt geaendert" und bekommt gar nichts.
**Warum:** Unter Relevanz hat ein seltener Begriff eine Chance; unter Datumssortierung gehoeren die neuesten Treffer mit hoher Wahrscheinlichkeit jemand anderem (DI-07-03 in verschaerfter Form).
**Vermeidung:** `FAILURE_ALL_CANDIDATES_REJECTED` und die Ausnahme in `nextUrl` (Entscheid V-1a) muessen unter Sortierung erhalten bleiben; hier sind sie der Normalfall. Keine zusaetzliche Runde, kein groesseres Fenster, kein rechtebewusster Vorfilter.
**Warnzeichen:** der `all_candidates_rejected`-Satz haeuft sich in einem Sortierlauf.

### Pitfall H: Gleichstands-Reihenfolge wird als gegeben angenommen
**Was schiefgeht:** FILT-02 verlangt `file_id` als Zweitschluessel; der Code verlaesst sich auf tantivy.
**Warum:** gemessen liefert tantivy die Einfuege-/Segmentreihenfolge (7, 3, 9, 1 bei Einfuegereihenfolge 7, 3, 9, 1), nicht `file_id`.
**Vermeidung:** portionsweise stabil nachsortieren, Grenze im Kommentar benennen.
**Warnzeichen:** zwei Testlaeufe nach einem Merge liefern innerhalb derselben Sekunde eine andere Reihenfolge.

---

## Code Examples

### Filterklausel in `build_query` (lexikalische Haelfte)

```python
# Quelle: eigenes Muster, abgeleitet aus query/rewrite.py:374-375
TYPE_GROUPS: Final[Mapping[str, tuple[str, ...]]] = {
    "pdf": ("pdf",),
    "documents": ("docx", "odt", "rtf"),
    "spreadsheets": ("xlsx", "ods", "csv"),
    "presentations": ("pptx", "odp"),
    "images": ("jpg", "jpeg", "jps", "mpo", "png", "tif", "tiff", "webp"),
    "text": ("txt", "text", "md", "markdown", "mdown", "mdwn", "mkd", "htm", "html",
             "json", "xml", "yaml", "yml", "conf", "cnf", "eml", "adoc", "asciidoc",
             "org", "fb2", "js"),
}

def extensions_of(groups: Sequence[str]) -> tuple[str, ...]:
    """Die Endungen der genannten Gruppen, ohne Doppelte, in stabiler Ordnung."""
    wanted: list[str] = []
    for group in groups:
        wanted.extend(TYPE_GROUPS.get(group.lower(), ()))
    return tuple(dict.fromkeys(wanted))
```

### Zeitraum als Bereichsabfrage auf dem Fast-Field

```python
# Quelle: eigene Probe gegen tantivy 0.26.0 am 16.09.2026
from tantivy import FieldType, Occur, Query

def _mtime_range_query(index: Index, since: int | None, until: int | None) -> Query | None:
    """Der Zeitraum als Bereich ueber die Fast-Spalte von mtime.

    use_inverted_index bleibt beim Vorgabewert False, und das ist die ganze
    Zeile: mtime ist indexed=False, und mit True antwortet tantivy 0.26.0 mit
    einer leeren Trefferliste statt mit einem Fehler (gemessen).
    """
    if since is None and until is None:
        return None
    return Query.range_query(index.schema, FIELD_MTIME, FieldType.Integer, since, until)
```

### Sortierzweig als eigener Modus

```python
# Quelle: eigenes Muster, abgeleitet aus index/search.py:454-470 und der Probe
from tantivy import Order

def _sorted_round(searcher, query, *, order: Order, scan_cap: int, needed: int,
                  store, uid) -> tuple[list[Candidate], int]:
    """Rein lexikalisch, ohne RRF, ohne Vektorzweig, Score 0.0.

    Portionsweise nach (-mtime, -file_id) stabilisiert: tantivy ordnet
    Gleichstaende nach Segment und Dokumentadresse, nicht nach file_id
    (gemessen 16.09.2026). Eine Gleichstandsgruppe, die genau an einer
    Portionsgrenze zerfaellt, ist portionsweise sortiert und nicht global;
    Duplikate oder Luecken entstehen dabei nicht, weil offset zusammen mit
    order_by_field seitenstabil ist (gemessen ueber 20.000 Dokumente in vier
    Segmenten, 16 Seiten, Folge identisch mit einem tiefen Abruf).
    """
    permitted: list[Candidate] = []
    raw_cursor = 0
    reverse = order is Order.Desc
    while len(permitted) < needed and raw_cursor < scan_cap:
        chunk_limit = min(max(needed, _SCAN_CHUNK_MIN), scan_cap - raw_cursor)
        hits = searcher.search(
            query, chunk_limit, order_by_field=FIELD_MTIME, order=order, offset=raw_cursor
        ).hits
        if not hits:
            break
        portion = [
            Candidate(file_id=file_id, score=0.0, mtime=mtime)
            for file_id, _, mtime in _ranked(searcher, hits, scored=False)
        ]
        portion.sort(key=lambda c: (c.mtime, c.file_id), reverse=reverse)
        permitted.extend(_permit(store, uid, portion))
        raw_cursor += len(hits)
        if len(hits) < chunk_limit:
            break
    return permitted, raw_cursor
```

### Datumsfilter des Dialogs lesen

```php
// Quelle: Muster von Provider::titleOnly() (php/lib/Search/Provider.php:253)
// plus lib/private/Search/Filter/DateTimeFilter.php von nextcloud/server
private function epochOf(ISearchQuery $query, string $name): ?int {
    $filter = $query->getFilter($name);
    if ($filter === null) {
        return null;
    }
    $value = $filter->get();

    return $value instanceof \DateTimeImmutable ? $value->getTimestamp() : null;
}

#[\Override]
public function getSupportedFilters(): array {
    return [
        IFilter::BUILTIN_TERM,
        IFilter::BUILTIN_TITLE_ONLY,
        IFilter::BUILTIN_SINCE,
        IFilter::BUILTIN_UNTIL,
    ];
}
```

### Schnellbereich in der Zeitzone des Nutzers

```php
// Quelle: OCP\IDateTimeZone (nextcloud/server stable33, @since 8.0.0)
private function quickRangeStart(string $range): ?int {
    $now = new \DateTimeImmutable('now', $this->dateTimeZone->getTimeZone());

    return match ($range) {
        'today' => $now->setTime(0, 0)->getTimestamp(),
        'week'  => $now->modify('-6 days')->setTime(0, 0)->getTimestamp(),
        'month' => $now->modify('-29 days')->setTime(0, 0)->getTimestamp(),
        'year'  => $now->setDate((int)$now->format('Y'), 1, 1)->setTime(0, 0)->getTimestamp(),
        default => null,
    };
}
```

---

## State of the Art

| Alter Stand | Jetziger Stand | Seit | Bedeutung fuer die Phase |
|---|---|---|---|
| "Bereichsabfragen brauchen ein indiziertes Feld" | tantivy-py `range_query` mit `use_inverted_index=False` arbeitet auf der Fast-Spalte | tantivy 0.22 aufwaerts, in 0.26.0 verifiziert | since/until ohne Reindex und ohne Schemaaenderung |
| `IProvider` mit `getSupportedFilters` optional | `IFilteringProvider` seit NC 28; ein nicht deklarierter Filter fuehrt zu `UnsupportedFilter` und HTTP 400 | NC 28.0.0 | FILT-03 ist eine Deklaration plus ihre Wirkung, kein neuer Mechanismus |
| `IDateTimeZone::getTimeZone()` ohne Nutzerangabe | Zusaetzlicher `?string $userId`-Parameter | NC 32.0.0 | Nicht noetig; der Aufruf ohne Argumente beantwortet den angemeldeten Nutzer |

**Nichts davon ist veraltet oder abgekuendigt.** Es gibt in dieser Phase keine Abkuendigung, die eine Wiedervorlage braucht.

---

## Package Legitimacy Audit

**Diese Phase installiert kein Paket, weder im Backend noch in PHP.** Alles Benoetigte ist bereits gepinnt und im Image.

| Paket | Registry | Rolle in dieser Phase | Disposition |
|---|---|---|---|
| `tantivy` 0.26.0 | PyPI, bereits gepinnt | `order_by_field`, `Order`, `range_query`, `Occur` | Unveraendert, keine Installation |

Der Package-Legitimacy-Gate (slopcheck, Registry-Verifikation, postinstall-Pruefung) entfaellt mangels neuer Pakete. Sollte ein Plan doch ein Paket vorschlagen, ist das ein Warnsignal: die Milestone-Recherche und diese Phasenrecherche kommen unabhaengig zu demselben Schluss ("Backend: nichts. PHP: nichts").

---

## Environment Availability

| Abhaengigkeit | Gebraucht fuer | Vorhanden | Version | Ausweichweg |
|---|---|---|---|---|
| `tantivy` in `backend/.venv` | Sortier-/Filter-/Bereichsabfragen | ja | 0.26.0, index_format v7 | -- |
| Python-Umgebung (uv) | Alle Backend-Gates | ja | `backend/.venv`, Python 3.13 | Globales Python ist defekt, immer `uv run` |
| PHP-Laufzeit lokal | PHPUnit | **nein** | -- | Muster des Repositories: Text-Gates in Python lesen die PHP-Quellen (`docs/testing.md` begruendet das); PHPUnit laeuft in CI |
| Laufende Nextcloud-Testinstanz | Paritaetsjob, Ende-zu-Ende | nur in CI | -- | `.github/workflows/integration.yml`, Job `search-parity` |
| `nextcloud/server`-Quellen | Upstream-Verifikation | ueber das Netz gelesen | stable33 | -- |

**Fehlende Abhaengigkeiten ohne Ausweichweg:** keine.
**Fehlende Abhaengigkeiten mit Ausweichweg:** PHP lokal; deshalb muessen die PHP-seitigen Zusicherungen dieser Phase, soweit moeglich, als Text-Gates in `backend/tests/` formuliert werden, und die funktionalen Faelle als PHPUnit-Faelle, die erst in CI laufen.

---

## Project Constraints (from CLAUDE.md)

Aus `./CLAUDE.md` (verbindlich fuer jeden Plan dieser Phase):

- **Code englisch**, Projektkommunikation deutsch. Echte Umlaute nur in deutscher Prosa, **nie im Code**. Keine Gedankenstriche.
- **Qualitaetsgates:** ruff-Vollregelsatz, pyright basic, vulture, lokal gruen vor dem Commit.
- **Sicherheit/Privatsphaere:** Berechtigungs-Durchgriff strikt; keine Inhalte verlassen den Server.
- **Nextcloud-Fenster:** min 33, max 35. Jede genutzte API muss in allen dreien vorhanden sein (`IFilter::BUILTIN_SINCE` seit 28, `IDateTimeZone` seit 8, `IDateTimeFormatter` seit 8: alle drei sicher).
- **PHP-Companion minimal**, `registerSearchProvider` plus `IFilteringProvider`; Proxy nur ueber `PublicFunctions::exAppRequest`.
- **Owner-Regel (06.09.2026):** nach Fertigstellung aller Merkmale wird vor der Abgabe ausgiebig geprueft, nicht nur der Happy Path. Fuer diese Phase heisst das konkret: Fehler-, Rand- und Negativpfade je neuem Parameter.
- **Owner-Regel (15.08.2026):** nach jeder Phase Security-, Bug- und Performance-Audit, Befunde vor Phasenabschluss fixen.
- **Aus den globalen Regeln des Nutzers:** keine Emojis (Icons als SVG, wie die Seite es bereits macht); Umlaute in deutscher Prosa nie durch `ae/oe/ue/ss` ersetzt (Ausnahme: die `.planning`-Dateien folgen der hier gewaehlten ASCII-Konvention, die Kataloge und die Oberflaeche nicht).
- **Vokabular-Gate:** das gesperrte Wort darf in oeffentlichen Erzeugnissen nicht vorkommen; keine neue Zeichenkette dieser Phase braucht es.

---

## Security Domain

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Trifft zu | Standardkontrolle in diesem Baum |
|---|---|---|
| V2 Authentication | nein | Unveraendert: Nutzerkennung ausschliesslich aus dem signierten AppAPI-Header |
| V3 Session Management | nein | Route ist `NoCSRFRequired`, aber sitzungspflichtig; keine Aenderung |
| V4 Access Control | **ja** | `SearchService::run()` mit `getFirstNodeById()` + `isReadable()` bleibt die einzige Stelle; `test_php_acl_boundary.py` zaehlt die Aufrufstellen |
| V5 Input Validation | **ja** | Pydantic `extra="forbid"` plus `Literal`-Wertemengen im Container; in PHP geschlossene Werte mit stillem Rueckfall |
| V6 Cryptography | nein (Grenzfall) | Der Cursor-Fingerabdruck ist kein Sicherheitsmerkmal, sondern eine Verwechslungssperre; kein Geheimnis, keine Signatur, und genau so muss er kommentiert sein |
| V7 Error Handling / Logging | **ja** | Kein Log dieser Phase darf einen Suchbegriff, einen Pfad oder eine Trefferzahl tragen; bestehende Regel, gilt fuer die neuen Zweige mit |

### Bekannte Bedrohungsmuster fuer diesen Stapel

| Muster | STRIDE | Standard-Gegenmassnahme |
|---|---|---|
| Zaehl-Orakel ueber Facetten oder Gesamtwerte (T-02-93) | Information Disclosure | Keine Trefferzaehler je Typ, kein Gesamtwert, Cursor zaehlt erlaubte Kandidaten |
| Zweite Tuer an der Rechtegrenze durch eine Datenroute | Elevation of Privilege | Keine neue Route; Chips und Sortierung sind Werte in der bestehenden Adresse |
| Identitaet im Request-Rumpf geschmuggelt | Spoofing | `extra="forbid"` bleibt; neue Felder tragen nie eine Kennung |
| Dienstverweigerung ueber unbegrenzte Parameter | Denial of Service | `types` mit `max_length`, `since`/`until` als `int` mit Grenzen, `SEARCH_SCAN_MAX` als Decke auch im Sortierzweig |
| Regulaerer Ausdruck aus der Suchleiste | Denial of Service | Unveraendert `allow_regexes=False`; der neue Parameter ist kein Freitext und geht nie in den Parser |
| Stiller Filterausfall, der wie "nichts gefunden" aussieht | (kein STRIDE, aber ein Produktrisiko) | Pitfall A; ausserdem ein Testfall, der belegt, dass ein gesetzter Zeitraum ueberhaupt Treffer liefern kann |

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die Seitenstabilitaet von `offset` plus `order_by_field`, gemessen ueber 20.000 Dokumente in vier Segmenten, gilt auch bei 52.111 Dokumenten und mehr Segmenten | Befund 2 | Tiefes Blaettern unter Sortierung koennte Treffer doppeln oder ueberspringen; billig gegenzupruefen, sobald ein grosser Index verfuegbar ist (Phase 15) |
| A2 | Die vorgeschlagene Gruppen-zu-Endungs-Tabelle deckt den realen Bestand einer typischen Instanz ausreichend ab | Befund 4 | Einzelne Dateien sind unter keinem Chip erreichbar; heilbar durch Ergaenzung der Tabelle, kein Reindex |
| A3 | Die franzoesischen Entsprechungen der Gruppenlabels ("Documents", "Images" wortgleich) loesen G2 aus | Befund 11 | Wenn nicht, entfaellt lediglich der Ausnahme-Eintrag; kein Schaden |
| A4 | Der Unified-Search-Dialog (Vue) fragt Provider nur mit den Filtern, die sie melden; das HTTP 400 ist der Ausweichpfad | Befund 9 | Das Ergebnisbild bleibt dasselbe (Findling verschwindet), nur die Ursache liegt anders; ohne Folge fuer die Reparatur |
| A5 | Kalenderfenster sind fuer die Schnellbereiche die bessere Wahl als rollierende Fenster | Befund 10 | Reine Produktentscheidung; Owner kann sie drehen, ohne den Backend-Vertrag zu beruehren |
| A6 | Ein `xxh128`/`sha256`-Kurzhash reicht als Cursor-Fingerabdruck | Befund 7 | Kollisionen sind harmlos (eine Seite zu viel statt Seite eins); kein Sicherheitsrisiko, weil der Cursor nur erlaubte Kandidaten zaehlt |

---

## Open Questions (RESOLVED)

RESOLVED am 2026-09-16 bei der Planung: alle fuenf Fragen sind entschieden, jede
Empfehlung ist in einem Plan umgesetzt. (1) Zweitschluessel portionsweise mit
benannter Grenze in 13-02, (2) type:<gruppenname> wird expandiert, ein Vokabular,
in 13-01, (3) Vereinigung statt Schnittmenge von Text- und Chip-Filter in 13-01,
(4) Paritaets-Weg 3 ohne Werkzeugaenderung in 13-12, (5) Diagnoseroute zieht mit
in 13-03.

1. **Zweitschluessel `file_id` an Portionsgrenzen**
   - Was feststeht: tantivy ordnet Gleichstaende nach Segment und Dokumentadresse; `offset` ist seitenstabil; eine portionsweise Nachsortierung erzeugt weder Duplikate noch Luecken.
   - Was offen ist: ob die Phase die portionsweise Grenze akzeptiert oder ob FILT-02 woertlich eine globale Ordnung verlangt.
   - Empfehlung: portionsweise Nachsortierung plus ein Satz im Plan und im Kommentar. Eine globale Ordnung waere ein unbegrenzter Nachschlag ueber eine Gleichstandsgruppe und ist den Gewinn nicht wert.

2. **Soll `type:<gruppenname>` in der Textsyntax funktionieren?**
   - Was feststeht: heute gibt es keine Gruppen in der Textsyntax; sie nimmt rohe Endungen.
   - Was offen ist: ob "EIN Filtervokabular" bedeutet, dass die Textsyntax die Gruppennamen ebenfalls versteht.
   - Empfehlung: ja, weil es eine Zeile kostet (dieselbe Tabelle) und die Zusage woertlich einloest. Falls der Plan zu breit wird, ausdruecklich vertagen statt stillschweigend weglassen.

3. **Verknuepfung von `type:`-Text und Chip**
   - Was feststeht: beide erzeugen dieselbe Klausel.
   - Was offen ist: Vereinigung oder Schnittmenge.
   - Empfehlung: Vereinigung. Die Schnittmenge ist in fast jedem gemischten Fall leer, und die Seite haette keine Moeglichkeit, das zu erklaeren, ohne die Textsyntax zu erlaeutern.

4. **Paritaets-Szenarien fuer FILT-05**
   - Was feststeht: `parity_diff.py` prueft beide Richtungen und verlangt `--expect-min` fuer alle drei Mengen.
   - Was offen ist: welche Szenarien hinzukommen, ob das Werkzeug einen Modus braucht.
   - Empfehlung: zwei mengenneutrale Szenarien (`types=text`, `sort=newest`) ohne Werkzeugaenderung, plus ein wegnehmendes Szenario mit erwarteter Leermenge. Werkzeugaenderung nur, wenn das nicht reicht; sie zieht `test_parity_diff.py` nach sich.

5. **Diagnoseroute mitziehen?**
   - Was feststeht: `api/diagnose.py:172` ruft `build_query` und muss die Signatur mittragen.
   - Was offen ist: ob die Route die Filter auch anbietet.
   - Empfehlung: ja. `ranked_sides` ist genau das Werkzeug, mit dem "Semantik unter Filter noch da" ueberhaupt beobachtbar wird, und Erfolgskriterium 1 braucht diesen Blick.

---

## Sources

### Primary (HIGH confidence)
- Eigener Quellcode, Stand 16.09.2026: `backend/src/findling/index/search.py` (Zeilen 142, 267, 290, 323, 349, 409-481), `index/schema.py:105/114`, `query/rewrite.py` (Zeilen 130, 185, 292, 317, 374), `api/search.py` (Zeilen 75, 176, 230), `api/snippets.py:71`, `api/diagnose.py:172`, `extract/dispatch.py` (Zeilen 88-161), `config.py` (Zeilen 41, 166-182, 547, 593)
- Eigener PHP-Quellcode: `php/lib/Controller/PageController.php` (Zeilen 83, 95, 176-301, 433-466), `lib/Service/SearchService.php` (Zeilen 131, 229-358, 409), `lib/Service/ExAppService.php` (Zeilen 95-207, 402-455, 761), `lib/Service/ApprovedHit.php`, `lib/Service/SearchOutcome.php`, `lib/Search/Provider.php` (Zeilen 132-152, 253), `templates/search.php`, `php/l10n/*` (174 Schluessel, nachgezaehlt)
- Eigene Gates: `backend/tests/test_admin_ui_contract.py` (Zeilen 290-380, 698, 1051-1130), `test_php_acl_boundary.py`, `test_php_trust_boundary.py`, `test_search_limits_lockstep.py`, `test_search_endpoint.py:142`, `test_parity_diff.py`, `scripts/ci/parity_diff.py`, `.github/workflows/integration.yml` (Job `search-parity`, ab Zeile 2611), `.github/workflows/python.yml`, `php.yml`
- **Eigene Probe gegen die installierte tantivy 0.26.0, 16.09.2026** (`backend/.venv`): Feldwert statt Score unter `order_by_field`; `Order.Asc`/`Desc`; `offset` seitenstabil ueber 20.000 Dokumente in vier Segmenten (16 Seiten identisch mit einem tiefen Abruf); `range_query` auf dem nicht indizierten Fast-Field funktioniert mit `use_inverted_index=False` und liefert mit `True` still nichts; `order_by_field="ext"` scheitert mit `ValueError`; Gleichstands-Reihenfolge ist nicht `file_id`
- `backend/.venv/Lib/site-packages/tantivy/tantivy.pyi` (Signaturen `Query.range_query` Zeile 347, `Searcher.search` Zeile 393, `Order` Zeile 368)
- `nextcloud/server`, Branch `stable33`: `lib/public/Search/IFilter.php`, `lib/private/Search/SearchComposer.php`, `core/Controller/UnifiedSearchController.php`, `lib/private/Search/Filter/DateTimeFilter.php`, `lib/public/IDateTimeZone.php`, `lib/public/IDateTimeFormatter.php`, `resources/config/mimetypemapping.dist.json`

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md`, `PITFALLS.md` (Pitfalls 1 bis 9) der Milestone-Recherche v1.2; jede uebernommene Aussage dieser Phase wurde am Code oder an der Bibliothek gegengeprueft und ist oben entsprechend markiert
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `13-CONTEXT.md`

### Tertiary (LOW confidence)
- Keine. Alle Aussagen dieses Dokuments sind entweder am eigenen Baum gelesen, an der installierten Bibliothek gemessen oder an einer Upstream-Quelle belegt; die verbleibenden Unsicherheiten stehen im Assumptions Log.

---

## Metadata

**Confidence breakdown:**
- Integrationsstellen im Backend: HIGH; jede mit Datei und Zeile belegt
- Tantivy-Verhalten (Sortierung, Bereich, Seitenstabilitaet, Gleichstand): HIGH; gegen die installierte Version gemessen, nicht aus der Dokumentation uebernommen
- Nextcloud-Filter-Mechanik und Datumswerte: HIGH; stable33-Quellcode gelesen
- PHP-Integrationsstellen und Gates: HIGH; am eigenen Baum gelesen, Katalogzahl nachgezaehlt
- Endungsuniversum je Gruppe: MEDIUM-HIGH; aus der eigenen Allowlist und der Server-Zuordnung abgeleitet, nicht an einem realen Bestand gemessen
- Uebertragung der Sortiermessung auf 52.111 Dokumente: MEDIUM; Mechanik segment- und gleichstandsunabhaengig, Groessenordnung aber nicht selbst gefahren

**Research date:** 2026-09-16
**Valid until:** 2026-10-16 (Backend-Befunde sind an gepinnte Versionen gebunden; die Nextcloud-Befunde gelten fuer das Fenster 33 bis 35 und muessen bei einer Fensteraenderung erneut gelesen werden)
