---
phase: 02-indexkern-und-volltextsuche
plan: 09
subsystem: search
tags: [tantivy, query-parser, umlaut, acl-prefilter, snippets, offsets, tdd]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-06: Schema, open_index mit den vier registrierten Analyseketten, Feldkonstanten"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-02: Store mit prefilter_visible und der Nur-Lese-Verbindung"
provides:
  - "query/rewrite.py: umlaut_variants, extract_filters, add_umlaut_variants, build_query, RewrittenQuery"
  - "index/search.py: candidates mit ACL-Vorfilter und Seitenmarken, Candidate, CandidatePage"
  - "index/search.py: char_ranges und snippets_for, SnippetText, ByteRange"
  - "Gemessener Befund: SearchResult.count existiert zur Laufzeit, fehlt aber im Typstub"
  - "Gemessener Befund: eine Leerzeichennormalisierung in der Umschreibung verdeckt einen Syntaxfehler"
affects: [02-10, 02-11, 02-12, 02-13, 06-semantik]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reihenfolge als Code, nicht als Absprache: Filter schneiden, dann Varianten, dann parsen"
    - "Eine Umschreibung aendert genau das, wofuer sie da ist, und kein Leerzeichen mehr"
    - "Das Antwortmodell hat strukturell kein Textfeld, ein statischer Test haelt es so"
    - "Vom Kandidaten zur Berechtigung fragen, nie umgekehrt"
    - "Fremdbibliotheks-Luecken benannt lesen statt mit Ersatzwert verstecken"

key-files:
  created:
    - backend/src/findling/query/__init__.py
    - backend/src/findling/query/rewrite.py
    - backend/src/findling/index/search.py
    - backend/tests/test_query_rewrite.py
    - backend/tests/test_search_library.py
    - backend/tests/test_snippet_offsets.py
  modified: []

key-decisions:
  - "Die Umlautersetzung ignoriert Gross- und Kleinschreibung, weil der Analyzer erst nach dem Parser kleinschreibt und Mueller so oft gross wie klein getippt wird"
  - "Eine Suchzeile aus nur einem Filter ruft die Engine nicht: ein Filter ohne Begriff waere die Anforderung aller PDF-Dateien der Instanz in keiner sinnvollen Reihenfolge"
  - "Die Trefferzahl der Engine wird in genau einer benannten Funktion gelesen und ohne Ersatzwert, weil ein Ersatzwert eine Seite dauerhaft zur letzten erklaeren wuerde"
  - "snippets_for prueft den Vorfilter als erste Handlung, unabhaengig davon, dass PHP ohnehin nur ueberlebende Kennungen schickt"
  - "bench.py behaelt den werfenden Parser; ein statisches Gate benennt es als einzige Ausnahme, statt das Messwerkzeug von 02-06 umzubauen"

patterns-established:
  - "Query-Tests laufen gegen einen echten Index: ein Test gegen ein Query-Objekt beantwortet die gestellte Frage nicht"
  - "Vorher-nachher-Paare im selben Test, damit die Zusage nicht gruen bleibt, wenn die Bibliothek die Luecke selbst schliesst"
  - "Sicherheitszusagen ueber Abwesendes als strukturelle Tests: Feldnamen einer Datenklasse, Quelltext-Greps"

requirements-completed: [SRCH-01, SRCH-02, SRCH-03, COMP-04]

# Metrics
duration: 25min
completed: 2026-08-31
---

# Phase 02 Plan 09: Die Suchbibliothek Summary

**Aus einer Suchzeile wird eine Query mit allen vier Operatoren aus SRCH-03 und geschlossener Umlautluecke, aus einer Trefferliste werden ACL-vorgefilterte Kandidaten ohne Namen, Pfad und Text, und aus einem Dokument wird ein Textausschnitt, dessen Hervorhebungen in Zeichen zaehlen statt in Bytes.**

## Performance

- **Duration:** ca. 25 min
- **Started:** 2026-08-31T20:25Z
- **Completed:** 2026-08-31T20:50Z
- **Tasks:** 3 von 3
- **Files modified:** 6 (alle neu)

## Accomplishments

- `query/rewrite.py` schneidet zuerst den Dateityp-Filter heraus, ergaenzt dann die Umlautvarianten und parst zuletzt leniently. Die Reihenfolge steht als Kommentar im Modul, weil ihre Umkehrung den Filterausdruck in den Volltext kippt.
- Die Umlautluecke ist auf der Anfrageseite geschlossen und in beiden Richtungen belegt: `kuendigung` findet ohne Umschreibung **nichts**, mit Umschreibung das Dokument.
- `index/search.py` liefert Kandidaten, die vier Werte tragen und nichts sonst. Zwei statische Tests halten es so: die Feldnamen der Datenklasse und ein Quelltext-Grep gegen `"title"`, `"path"`, `"snippet"` und `"body`.
- Die Antwort nennt `hasMore` und `nextOffset` und **keine** Gesamttrefferzahl. Die Zahl der Engine wird gelesen, benutzt und bleibt in der Funktion.
- `char_ranges` rechnet Byte- in Zeichenpositionen um, dedupliziert und verschmilzt. Der Umlauttest schneidet das Fragment mit den zurueckgegebenen Positionen und vergleicht die Zeichenkette; er hat zwei Mehrbytezeichen vor der Fundstelle.
- 34 neue Tests, alle fuenf Python-Gates lokal gruen (312 Tests, ruff check, ruff format, pyright, vulture).

## Task Commits

1. **Task 1: Query-Umschreibung, Filter und der leniente Parser**
   - RED `84b3992` (test), GREEN `36a2a54` (feat)
2. **Task 2: Kandidatensuche mit Vorfilter und Seitenmarken**
   - RED `bbab4b3` (test), GREEN `3a9581c` (feat)
3. **Task 3: Snippets mit Zeichenpositionen statt Bytepositionen**
   - RED `e8159e1` (test), GREEN `a0ecbde` (feat)

Dazu `ffac37f` (test): das statische Gate gegen den werfenden Parser im Anfragepfad, siehe Deviation 3.

## TDD Gate Compliance

Alle drei Aufgaben sind mit `tdd="true"` geplant und liefen in der Reihenfolge RED, GREEN. Jeder RED-Commit steht gegen ein tatsaechlich rotes Ergebnis beim Sammeln (`ModuleNotFoundError` bei Task 1 und 2, `ImportError` bei Task 3, weil `search.py` da bereits existierte und die beiden neuen Namen fehlten). Eine REFACTOR-Runde war in keiner Aufgabe noetig; in Task 1 wurde innerhalb der GREEN-Runde ein Fehler der eigenen Implementierung gefunden und behoben, bevor der Commit fiel (Deviation 1).

## Eigene Messbefunde

Gemessen an tantivy 0.26.0, Python 3.13.13, Windows 11, mit der deutschen Analysekette aus 02-01.

| Beobachtung | Wert |
|---|---|
| `Snippet.highlighted()` fuer "... die Kündigungsfrist für ..." | `(35, 51)` in Bytes, `(35, 50)` in Zeichen |
| Bereiche fuer ein zerlegtes Kompositum im Fragment | `[(4, 20), (4, 20), (57, 73), (57, 73)]`, also je Teiltoken einmal |
| Suche nach `Genehmigung` auf "Grundstücksverkehrsgenehmigung" | `(21, 52)` in Bytes fuer ein 30 Zeichen langes Wort, markiert das ganze Kompositum |
| Dokument ohne Treffer im Textfeld | leeres Fragment, leere Bereichsliste, keine Ausnahme |
| `kuendigung` ohne Umschreibung | 0 Treffer; mit Umschreibung 1 Treffer |
| `/.*genehmigung.*/` bei `allow_regexes=False` | 0 Treffer, Fehlereintrag "Regex queries are not allowed" |
| unpaariges Anfuehrungszeichen | 0 Treffer, Fehlereintrag "missing delimiter", keine Ausnahme |

## Files Created/Modified

- `backend/src/findling/query/rewrite.py` , `UMLAUTS`, `umlaut_variants`, `extract_filters`, `add_umlaut_variants`, `build_query`, `RewrittenQuery`, die Feldlisten und die Gewichte.
- `backend/src/findling/query/__init__.py` , Paket-Docstring, nennt die Reihenfolge der drei Schritte.
- `backend/src/findling/index/search.py` , `Candidate`, `CandidatePage`, `candidates`, `ByteRange`, `SnippetText`, `char_ranges`, `snippets_for`.
- `backend/tests/test_query_rewrite.py` , 12 Tests an einem echten Drei-Dokumente-Index: Umlautform vorher/nachher, Filterschnitt, `title_only`, Phrase, Pflicht- und Ausschlussterm, kaputte Eingabe, Regex, leerer Begriff mit Zaehler an der Engine, plus das Parser-Gate ueber das Paket.
- `backend/tests/test_search_library.py` , 11 Tests: Vorfilter, schmale Kandidatenform, Seitenmarken, zweite Seite ohne Ueberschneidung, Nutzer ohne ACL-Zeile, keine Gesamtzahl, Score-Reihenfolge, leere Trefferliste, Endung und Zeitstempel.
- `backend/tests/test_snippet_offsets.py` , 11 Tests: Umlaut vor der Fundstelle, doppelt gemeldeter Bereich, ueberlappende Bereiche, getrennte Bereiche, Kompositum, Klartext, statisches Gate gegen die HTML-Form, Dokument ohne Treffer, fremde Kennungen, leere Liste, Reihenfolge.

## Decisions Made

- **Die Umlautersetzung ignoriert die Gross- und Kleinschreibung.** Code-Beispiel 4 des Research ersetzt woertlich, also nur `ue`. Getippt wird aber genauso oft `Mueller`, und der Analyzer schreibt erst nach dem Parser klein. `re.sub(..., flags=re.IGNORECASE)` deckt beide Formen ab und aendert an der Tabelle nichts.
- **Eine Suchzeile aus nur einem Filter ruft die Engine nicht.** `type:pdf` allein hinterlaesst keinen Begriff. Die erkannte Endung wird trotzdem zurueckgegeben, damit der Aufrufer die Zeile nicht ein zweites Mal zerlegt.
- **`title_only` setzt nur die Standardfelder um.** Die Gewichte bleiben eine Konstante fuer alle Faelle: zwei Gewichtstabellen waeren zwei Orte, an denen dieselbe Zahl steht. Der Kommentar nennt Pitfall 15, damit die PHP-Seite in 02-12 den Filter vollstaendig deklariert.
- **Kandidaten sind eine `frozen`-Datenklasse mit vier Feldern.** Ein Test prueft die Feldnamen als Menge, ein zweiter den Quelltext auf die verbotenen Bezeichner. Beides sind Aussagen ueber Abwesendes, und die faellt in keinem funktionalen Test auf.
- **`snippets_for` prueft den Vorfilter als erste Handlung.** Dass PHP ohnehin nur ueberlebende Kennungen schickt, ist keine Eigenschaft dieser Funktion, sondern eine Annahme ueber einen anderen Prozess.
- **`char_ranges` nimmt ein Protokoll statt des Bibliothekstyps.** Damit ist die reine Funktion mit einem Fragment und zwei Zahlen pruefbar, ohne dass ein Test einen Index bauen muss.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Umschreibung normalisierte Leerzeichen und verdeckte damit einen Syntaxfehler**

- **Found during:** Task 1, aufgefallen am roten Test fuer das unpaarige Anfuehrungszeichen
- **Issue:** Die erste Fassung zerlegte jeden unquotierten Abschnitt mit `split()` und setzte ihn mit einzelnen Leerzeichen wieder zusammen. Aus `kaputt "` wurde damit `kaputt"`, und **der Parser meldete keinen Fehler mehr**: er las die Eingabe als wohlgeformten Term. Die Zusage aus Pitfall 13 (kaputte Eingabe liefert Query *und* Fehlerliste) war damit stillschweigend gebrochen, und zwar genau fuer die Eingabe, fuer die sie gemacht wurde.
- **Ursache:** Eine Umschreibung, die mehr aendert als ihren Gegenstand. Die Normalisierung sah in jedem gewoehnlichen Fall identisch aus.
- **Fix:** `re.split(r"(\s+)")` statt `split()`, die Trennzeichen bleiben Elemente der Liste und werden unveraendert wieder eingesetzt. Dieselbe Korrektur in `extract_filters`, wo das Entfernen des Filtertokens sonst dieselbe Wirkung gehabt haette.
- **Files modified:** `backend/src/findling/query/rewrite.py`
- **Verification:** `test_an_unbalanced_quotation_mark_yields_errors_instead_of_raising` gruen; der Kommentar an `_WHITESPACE` nennt die Messung, damit die Vereinfachung nicht zurueckkehrt.
- **Committed in:** `36a2a54`

**2. [Rule 2 - Korrektheit] `SearchResult.count` ist im Typstub nicht deklariert**

- **Found during:** Task 2 (Kandidatensuche)
- **Issue:** `searcher.search(..., count=True)` liefert die Zahl zur Laufzeit, das mitgelieferte `.pyi` von tantivy 0.26.0 kennt am Ergebnis nur `hits`, und pyright schlaegt an. Dieselbe Klasse wie Deviation 4 aus 02-06.
- **Fix:** Eine benannte Funktion `_hits_in_total` mit `# pyright: ignore[reportAttributeAccessIssue]` und der Begruendung daneben. Bewusst **kein** Ersatzwert: ein `getattr` mit Vorgabe wuerde aus einem umbenannten Attribut eine Seite machen, die sich immer fuer die letzte haelt, und die verlorenen Treffer wuerde niemand je bemerken. Verschwindet das Attribut, fliegt ein `AttributeError` und die Seitentests werden rot.
- **Files modified:** `backend/src/findling/index/search.py`
- **Verification:** `pyright` ohne Befund, `test_the_page_says_whether_more_results_exist` und `test_the_last_page_says_that_it_is_the_last` gruen.
- **Committed in:** `3a9581c`

**3. [Rule 2 - Korrektheit] Der werfende Parser stand noch im Paket, ohne Gate**

- **Found during:** Abschliessende Verifikation ("kein `parse_query` ohne lenient im Projekt")
- **Issue:** `index/bench.py` aus Plan 02-06 ruft den strikten Parser. Der Suchpfad tut es nicht, aber nichts hielt einen spaeteren Endpunkt davon ab, es ihm gleichzutun, und genau das ist Pitfall 13.
- **Fix:** Ein statischer Test ueber das ganze Paket, der die Menge der Module mit diesem Aufruf gegen genau eine benannte Ausnahme haelt: `index/bench.py` ist ein Messwerkzeug, wird von keiner Anfrage erreicht und traegt seinen Suchtext als Konstante im Modul. Das Messwerkzeug selbst blieb unangetastet, damit die in 02-06 protokollierten Zahlen und der Vergleichslauf in 02-13 vergleichbar bleiben.
- **Files modified:** `backend/tests/test_query_rewrite.py`
- **Verification:** `test_no_module_of_the_request_path_uses_the_throwing_parser` gruen; ein Endpunkt mit dem strikten Parser macht ihn rot.
- **Committed in:** `ffac37f`

---

**Total deviations:** 3 auto-fixed (1x Rule 1, 2x Rule 2)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 ist ein Fehler der eigenen ersten Fassung, den der geplante Testfall gefunden hat, die beiden anderen sind Absicherungen an genau den Stellen, die der Plan als Fallen benennt.

## Abnahmekriterien im Einzelnen

| Kriterium | Ergebnis |
|---|---|
| `pytest tests/test_query_rewrite.py -q` | Exit 0, 12 Tests |
| `grep -c 'parse_query_lenient' rewrite.py` = 1 | 1 |
| `grep -Ec 'parse_query\(' rewrite.py` = 0 | 0 |
| `grep -c 'allow_regexes=False' rewrite.py` = 1 | 1 |
| `grep -c 'conjunction_by_default=True' rewrite.py` = 1 | 1 |
| `grep -c 'def test_' test_query_rewrite.py` >= 7 | 12 |
| `pytest tests/test_search_library.py -q` | Exit 0, 11 Tests |
| `grep -c 'prefilter_visible' search.py` >= 1 | 1 |
| `grep -Ec '"title"\|"path"\|"snippet"\|"body' search.py` = 0 | 0 |
| `grep -c 'count=True' search.py` = 1 | 1 |
| `grep -c 'def test_user_without_acl' test_search_library.py` = 1 | 1 |
| `grep -c 'def test_' test_search_library.py` >= 7 | 11 |
| `pytest tests/test_snippet_offsets.py tests/test_search_library.py -q` | Exit 0, 22 Tests |
| `grep -c 'to_html' search.py` = 0 | 0, zusaetzlich als Test im Modul |
| `grep -c 'encode("utf-8")' search.py` >= 1 | 1 |
| `grep -c 'set_max_num_chars' search.py` = 1 | 1 |
| `grep -c 'def test_umlaut_before_the_match' test_snippet_offsets.py` >= 1 | 1 |
| `grep -c 'def test_' test_snippet_offsets.py` >= 5 | 11 |
| ruff check, ruff format --check, pyright, vulture | alle vier ohne Befund |
| `pytest -q` gesamt | 312 passed, 1 skipped |

## Issues Encountered

- **Der Vorfilter braucht eine echte Zustandsdatenbank, kein Attrappenobjekt.** Beide neuen Testdateien oeffnen einen `Store` in `tmp_path` und schreiben ACL-Zeilen ueber `replace_acl`. Ein nachgebauter Vorfilter haette genau die Frage nicht beantwortet, um die es geht.
- **Die Sortierung der Importe kippt mit der Existenz des Moduls.** Wie in 02-02 protokolliert: solange `findling.query` fehlte, sortierte ruff den Import in der Testdatei als Fremdpaket. Der RED-Commit von Task 1 traegt deshalb die Sortierung, die nach dem GREEN-Schritt richtig ist.
- **Kein CI-Lauf moeglich.** Alle Gates liefen lokal ueber `uv run` unter Windows. Der GitHub-Actions-Lauf ist von hier nicht pruefbar und steht aus; die Messzahlen oben sind Windows-Zahlen.
- **Nicht gemessen:** die Kostenangaben des Plans (Tantivy-Suche 0,1 ms, Vorfilter 0,18 ms fuer 400 Kandidaten, 20 Snippets 4,2 ms) wurden aus dem Research uebernommen und stehen als Kommentar im Modul. Der Lauf in dieser Groessenordnung gehoert laut CONTEXT.md in Phase 5.

## Threat Flags

Keine neue Angriffsflaeche. Die sechs `mitigate`-Dispositionen des Plans sind umgesetzt:

| Threat ID | Umsetzung |
|---|---|
| T-02-91 (Confused Deputy bei Snippets) | `prefilter_visible` ist die erste Handlung von `snippets_for`; `test_snippets_are_produced_only_for_confirmed_file_ids` fragt mit einem Nutzer ohne ACL-Zeile nach drei fremden Kennungen und bekommt eine leere Liste |
| T-02-92 (Kandidaten verraten Namen) | Vier Felder, `frozen`; ein Test ueber die Feldnamen und ein Quelltext-Grep gegen die vier verbotenen Bezeichner |
| T-02-93 (Trefferzahl verraet fremde Dokumente) | Die Zahl wird in `_hits_in_total` gelesen und verlaesst die Funktion nicht; `CandidatePage` traegt genau `candidates`, `has_more` und `next_offset`, als Test ueber die Feldnamen |
| T-02-94 (Regex als Lastangriff) | `allow_regexes=False` ausdruecklich gesetzt, ein Test mit Regex-Syntax belegt Fehlereintrag und leeres Ergebnis; ein Aufruf ist ein Durchgang, die Runden zaehlt PHP |
| T-02-95 (kaputte Eingabe wirft) | Der leniente Parser, plus der Test mit dem unpaarigen Anfuehrungszeichen, plus das Paket-Gate gegen den strikten Parser (Deviation 3) |
| T-02-96 (Nutzereingabe im Log) | Die Fehlerliste geht nur in die Rueckgabe an den Aufrufer; das Debug-Log nennt ihre **Anzahl**, nicht ihren Inhalt, und es gibt keine Info-Zeile |

## Known Stubs

Keine. `ByteRange` ist ein Protokoll und kein Platzhalter, und `_UNKNOWN_EXTENSION` ist der leere Wert fuer ein Dokument ohne Endung, kein unfertiger Pfad.

## User Setup Required

Keine.

## Next Phase Readiness

- **02-11 (Endpunkte)** findet `build_query`, `candidates`, `snippets_for` und `char_ranges` vor. Alle vier sind synchron; das Umschalten auf `asyncio.to_thread` gehoert wie geplant in die Endpunkte. `open_reader` wird dort einmal gerufen, nicht je Suche (0,10 ms gegen 0,005 ms, gemessen in 02-06).
- **Das eingefrorene Protokoll aus Phase 1 passt ohne Aenderung:** `Hit.highlights` ist `list[tuple[int, int]]` in Zeichen, und `char_ranges` liefert genau das. `Hit.snippet` bleibt Klartext.
- **02-12 (PHP-Seite)** muss `title-only` in `getSupportedFilters()` nennen (sonst wird der Provider ganz uebergangen) und den Dateityp als `type:<endung>` in die Suchzeile stellen. Das begrenzte Nachfassen laeuft ueber `has_more` und `next_offset`, hoechstens drei Runden.
- **Offene Anschlussstelle, hier bewusst nicht entschieden:** wer `search_overfetch` und `search_rounds` aus `config.py` anwendet. Diese Bibliothek nimmt `limit` und `offset` so, wie sie kommen; der Ueberfetch ist eine Entscheidung des Endpunkts.
- **Bekannte Grenze:** die Verbformluecke D2 aus dem Research bleibt offen und wird nicht umgeschrieben, und die Umlautvariante erzeugt bei gewoehnlichen Woertern nachweislich Unsinnszweige ("neue" wird zu "neü"), die leer bleiben (Annahme A10). Beides ist im Modul benannt.

## Self-Check: PASSED

Alle sechs neuen Dateien liegen im Worktree, alle sieben Commit-Hashes stehen im Log von `gsd/agent-02-09`, keiner der Commits enthaelt eine Loeschung. Abschliessender Lauf: `uv run pytest -q` 312 passed, 1 skipped; `ruff check`, `ruff format --check`, `pyright` und `vulture --min-confidence 80` ohne Befund.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
