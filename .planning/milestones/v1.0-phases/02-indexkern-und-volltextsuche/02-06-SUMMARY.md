---
phase: 02-indexkern-und-volltextsuche
plan: 06
subsystem: search
tags: [tantivy, schema, indexwriter, upsert, disk-guard, latency, tdd]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-01: Analyseketten de/en/name, ANALYZER_VERSION, config.py mit allen Deckeln"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-02: Store mit version_mismatch und den fuenf Metaschluesseln"
provides:
  - "index/schema.py: die neun Felder mit ihren Tokenizernamen, build_schema()"
  - "index/open.py: open_index (oeffnen = registrieren), open_reader, expected_versions"
  - "index/writer.py: IndexBatchWriter, der einzige IndexWriter, Upsert, Sammel-Commit, Platzwache"
  - "index/bench.py: gemessene Suchlatenz im Ruhezustand und unter Schreiblast"
  - "Gemessener Befund: delete_documents_by_term erreicht ein unsigned-Feld nicht"
affects: [02-07, 02-08, 02-09, 02-10, 02-13, 03-events-und-ocr]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Oeffnen ist Registrieren: genau eine Funktion, statisch durch einen Test erzwungen"
    - "Feldnamen als Konstanten, weil Document.from_dict unbekannte Namen still verschluckt"
    - "Ein Writer je Prozess, gekapselt; ein zweiter meldet sich als eigener Fehlertyp"
    - "Volle Platte ist ein Zustand (paused_low_disk), kein Abbruch"
    - "Messwerkzeuge geben nur Zahlen aus, nie ein Token und nie ein Wort"

key-files:
  created:
    - backend/src/findling/index/schema.py
    - backend/src/findling/index/open.py
    - backend/src/findling/index/writer.py
    - backend/src/findling/index/bench.py
    - backend/tests/test_index_open.py
    - backend/tests/test_index_writer.py
  modified:
    - backend/tests/test_readonly_gate.py

key-decisions:
  - "Der Upsert loescht ueber Query.term_query statt ueber den Term-Namen: gemessen loescht die Loeschung per Term auf einem U64-Schluessel nichts und hinterlaesst das Dokument doppelt"
  - "path bleibt ein Textfeld und wird ueber eine Kette ohne Token unsuchbar gemacht, weil tantivy-py kein unindexiertes Textfeld kennt"
  - "body_de traegt den Text unabhaengig von FINDLING_LANGUAGES, weil es die einzige gespeicherte Textkopie ist; die Spracheinstellung schaltet die englische Pipeline"
  - "close() committet nicht: der Stapel ist die Absturzgranularitaet, ein stiller Commit beim Herunterfahren wuerde die Quittung an die Queue zur Luege machen"
  - "Der Windows-Commit-Fehler wird im Messwerkzeug wiederholt und gezaehlt, nicht in writer.py abgefangen, wo ein geschluckter IO-Fehler eine volle Platte verstecken wuerde"

patterns-established:
  - "Statische Tests fuer Eigenschaften, die zur Laufzeit nicht scheitern, sondern still das Falsche tun"
  - "Fremdbibliotheks-Fallen als Stolperdraht-Test festhalten, damit eine spaetere Korrektur sichtbar wird"
  - "Messungen mit Pause zwischen den Proben, damit die Proben auf die Commits fallen und nicht dazwischen"

requirements-completed: [SRCH-01, IDX-02, IDX-06]

# Metrics
duration: 40min
completed: 2026-08-31
---

# Phase 02 Plan 06: Schema, Oeffnen, Schreiben und die erste Latenzmessung Summary

**Der Volltextindex hat sein Schema, genau eine Stelle, die ihn oeffnet und dabei registriert, genau einen Writer mit idempotentem Upsert und Platzwache, und die Suchlatenz unter Schreiblast ist gemessen statt angenommen: Median 0,08 ms im Ruhezustand gegen 0,14 ms bei 18 Commits je Sekunde.**

## Performance

- **Duration:** ca. 40 min
- **Started:** 2026-08-31T19:52Z
- **Completed:** 2026-08-31T20:30Z
- **Tasks:** 3 von 3
- **Files modified:** 7 (6 neu, 1 geaendert)

## Accomplishments

- `schema.py` traegt die neun Felder in Schemareihenfolge, jedes mit einer Zeile Begruendung; `body_de` gespeichert (einzige Textkopie, Quelle des Snippets), `body_en` nur indexiert.
- `open.py` ist die einzige Stelle, die einen Index oeffnet, und ein Test laeuft ueber das ganze Paket und beweist es. Der Reopen-Test schliesst den Index, oeffnet ihn neu und sucht: ohne Registrierung faellt genau er um.
- `writer.py` haelt genau einen IndexWriter (50 MB Heap, `num_threads=1`), schreibt feldweise, macht jeden zweiten Lauf ueber den Upsert wirkungslos und prueft vor jedem Sammel-Commit den freien Platz.
- Ein zweiter Writer auf demselben Verzeichnis meldet sich als `IndexLockedError` statt als unverstaendlicher `ValueError`.
- `bench.py` misst beide Modi und macht dabei drei Zahlen sichtbar, die vorher niemand hatte: Median, p95 und Maximum der Suche waehrend laufender Indexierung.
- 37 neue Tests, alle fuenf Python-Gates lokal gruen (211 Tests, ruff check, ruff format, pyright, vulture).

## Task Commits

1. **Task 1: Schema und die einzige erlaubte Form, einen Index zu oeffnen**
   - RED `45136e4` (test), GREEN `4bf3252` (feat)
2. **Task 2: Der eine Writer mit idempotentem Schreiben, Sammel-Commit und Platzwache**
   - RED `3fa285e` (test), GREEN `81e6617` (feat)
3. **Task 3: Suchlatenz unter Schreiblast messen**
   - `41a13b5` (feat)

## TDD Gate Compliance

Task 1 und Task 2 sind mit `tdd="true"` geplant und liefen in der Reihenfolge RED, GREEN. Beide RED-Commits stehen gegen ein tatsaechlich rotes Ergebnis (`ModuleNotFoundError` beim Sammeln). Eine REFACTOR-Runde war nicht noetig. Task 3 ist ein Messwerkzeug ohne `tdd`-Kennzeichnung und hat entsprechend nur einen `feat`-Commit; sein Ergebnis sind die Zahlen weiter unten.

## Eigene Messzahlen

`uv run python -m findling.index.bench`, Windows 11, NVMe, Python 3.13.13, tantivy 0.26.0, 1000 Basisdokumente zu je rund 600 Woertern, Index 948 kB, 200 Suchen mit 5 ms Abstand.

| Zahl | `idle` | `under-write` |
|---|---|---|
| Median je Suche | 0,077 bis 0,100 ms | 0,134 bis 0,149 ms |
| p95 je Suche | 0,13 bis 0,23 ms | 0,25 bis 0,27 ms |
| Maximum je Suche | 0,34 bis 0,60 ms | 0,40 bis 0,87 ms |
| Dokumente im Index | 1.000 | 1.544 bis 1.576 |
| Indexgroesse | 947.869 B | 1.456.289 bis 1.472.415 B |
| Commits im Messfenster | 0 | 17 bis 18 |
| Im Fenster geschriebene Dokumente | 0 | 544 bis 576 |
| Messfenster | 1,08 s | 1,12 s |

Die Aussage aus drei Laeufen je Modus: laufende Indexierung mit rund 17 Commits je Sekunde verdoppelt Median und p95 der Suche, und beide bleiben zwei Groessenordnungen unter dem, was ein Mensch bemerkt. Das Maximum von 0,87 ms ist der teuerste Einzelfall und liegt immer noch unter einer Millisekunde. Der Vorbehalt steht ausdruecklich dabei: gemessen ist eine schnelle NVMe. Die interessante Zahl ist der Lauf mit gedrosselter Platte, und der gehoert laut Plan in den Messjob von 02-13, wo dieses Werkzeug die Messstelle ist. Faellt der Wert dort schlecht aus, ist die Stellschraube `batch_max_bytes`.

Nebenbefund: `commit_retries` steht in beiden Modi meist auf 0 und gelegentlich auf 2, siehe Deviation 5.

## Files Created/Modified

- `backend/src/findling/index/schema.py` , neun Felder, Feldkonstanten, `FIELDS`, `build_schema()`, die Kosten des gespeicherten Bodys als Kommentar.
- `backend/src/findling/index/open.py` , `open_index`, `open_reader`, `stored_only_analyzer`, `expected_versions`, `TANTIVY_VERSION`.
- `backend/src/findling/index/writer.py` , `IndexRecord`, `FlushResult`, `IndexLockedError`, `IndexBatchWriter` mit `add`, `flush`, `collect_garbage`, `close`, `pending`, `should_flush`.
- `backend/src/findling/index/bench.py` , zwei Modi, Median, p95, Maximum, Commits im Fenster, Indexgroesse, Dokumentzahl.
- `backend/tests/test_index_open.py` , 19 Tests: Anlegen, Wiederoeffnen, Reopen mit Suche, neun Felder, schnelle Felder, gespeicherter und unsuchbarer Pfad, deutsche Kette, Namenskette, exakter Dateityp, Sprachschalter, Versionsmarken, statischer Nachweis des einzigen Oeffners.
- `backend/tests/test_index_writer.py` , 18 Tests: Auffindbarkeit, Idempotenz, unsignierte Rueckgabe, statische Nachweise fuer feldweises Schreiben und die Loeschform, Warnungsfreiheit, Platzwache, lesende Suche waehrend der Pause, Nachholen nach der Pause, Neustart, Lockerkennung, Sprachschalter, Leerlauf-Flush, Aufraeumen, Stapelgrenzen, geschlossener Writer.
- `backend/tests/test_readonly_gate.py` , dritte geprueft enge Ausnahme fuer genau ein `mkdir`, plus Erweiterung des vorhandenen Positivtests.

## Decisions Made

- **Der Upsert loescht ueber eine Termquery aus dem Schema.** Der Plan schreibt `delete_documents_by_term` vor. Gemessen loescht dieser Aufruf auf dem `unsigned`-Schluessel nichts (Deviation 1), und die Wiederholbarkeit aus Pattern 2 haengt genau daran. `Query.term_query(schema, ...)` baut den Term aus dem Schema und trifft den Typ per Konstruktion; sie waere auch dann noch richtig, wenn der Schluessel spaeter den Typ wechselte.
- **`path` bleibt ein Textfeld.** tantivy-py kennt kein unindexiertes Textfeld. Statt den Typ zu wechseln (und die Anzeige spaeterer Plaene auf Bytes umzustellen) bekommt das Feld eine Analysekette, die die leere Tokenliste liefert. Gemessen: der Wert kommt unveraendert aus dem Dokumentspeicher, und weder ein Wort daraus noch der ganze Pfad findet etwas.
- **`body_de` ist sprachunabhaengig gefuellt.** Es ist die einzige gespeicherte Textkopie und die Quelle jedes Snippets. `FINDLING_LANGUAGES=de` laesst also `body_en` leer, wie im Plan verlangt, aber es schaltet nicht den Speicher ab; die Einstellung entscheidet ueber die zweite, reine Indexpipeline.
- **`close()` committet nicht.** Der Stapel ist die Absturzgranularitaet. Ein Commit beim Schliessen wuerde eine halbe Charge dauerhaft machen, deren Quittung die Queue nie gesehen hat.
- **`open_reader` wird einmal gerufen, nicht je Suche.** Gemessen kostet `config_reader` 0,10 ms, eine ganze Suche 0,005 ms. Der Docstring nennt beide Zahlen, damit der Suchpfad in 02-09 nicht das Zwanzigfache der Suche in ihre Vorbereitung steckt.
- **Der Windows-Commit-Fehler wird nur im Messwerkzeug wiederholt.** In `writer.py` waere ein geschluckter IO-Fehler genau die Klasse Fehler, die die Platzwache sichtbar machen soll.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `delete_documents_by_term` loescht auf einem `unsigned`-Feld nicht**

- **Found during:** Task 2 (Writer), aufgefallen am roten Idempotenztest
- **Issue:** Der vom Plan vorgeschriebene Upsert liess nach dem zweiten Schreiben derselben Datei **zwei** Dokumente im Index zurueck. Damit waere die Zusage "dasselbe Dokument zweimal geschrieben liegt genau einmal im Index" gebrochen gewesen, und zwar lautlos: der Aufruf wirft nichts und meldet nichts.
- **Ursache, gemessen an tantivy 0.26.0:** die Loeschung per Term baut aus einer Python-Ganzzahl einen I64-Term. Die U64-Spalte von `file_id` enthaelt keinen solchen Term. Dieselbe Wurzel wie Pitfall 8, nur an der Loeschseite.

  | Schluesseltyp | Loeschweg | Dokumente nach dem zweiten Schreiben |
  |---|---|---|
  | unsigned | per Term (neuer Name) | 2 |
  | unsigned | per Term (alter, veralteter Name) | 2 |
  | integer | per Term | 1 |
  | unsigned | per Termquery | 1 |

- **Fix:** `writer.delete_documents_by_query(Query.term_query(self._schema, FIELD_FILE_ID, record.file_id))`. Das Schema bleibt unveraendert, weil der Feldtyp in jedem ausgelieferten Index steht, waehrend der Aufrufweg unsere Wahl ist.
- **Files modified:** `backend/src/findling/index/writer.py`, `backend/tests/test_index_writer.py`
- **Verification:** `test_the_same_file_id_written_twice_leaves_exactly_one_document` gruen; dazu `test_deleting_by_term_does_not_reach_the_unsigned_key` als Stolperdraht auf die Bibliothek: repariert tantivy das, wird der Test rot und der kuerzere Weg ist wieder frei.
- **Committed in:** `81e6617`

**2. [Rule 3 - Blocking] tantivy-py kennt kein gespeichertes, nicht indexiertes Textfeld**

- **Found during:** Task 1 (Schema)
- **Issue:** Der Plan verlangt `path` gespeichert und nicht indexiert. `add_text_field` nimmt `index_option` nur mit den Werten `basic`, `freq` und `position` an, `None` und der leere Wert werden abgelehnt. Jedes Textfeld ist also indexiert, und mit dem Tokenizer `raw` findet `path:"/Vertraege/Kuendigung.pdf"` das Dokument nachweislich.
- **Fix:** Eine vierte Analysekette `stored_only` (`remove_long(1)`, also die leere Tokenliste), unter der `path` laeuft. Der Wert bleibt gespeichert und abrufbar, kein Posting entsteht, keine Query trifft.
- **Folge fuer ein Abnahmekriterium:** `grep -c 'register_tokenizer' open.py` liefert **4** statt der geforderten 3. Die Absicht des Kriteriums (alle drei Analyzer sind registriert) ist erfuellt; die vierte Zeile ist genau die Zeile, ohne die `path` durchsuchbar waere. Der Alternativweg (`path` als Bytefeld) haette den Typ des Feldes fuer alle spaeteren Plaene geaendert und ausserdem das Neun-Felder-Kriterium gebrochen.
- **Files modified:** `backend/src/findling/index/schema.py`, `backend/src/findling/index/open.py`
- **Verification:** `test_path_is_stored_and_not_searchable` prueft beide Richtungen (Wert kommt zurueck, Wort und ganzer Pfad finden nichts).
- **Committed in:** `4bf3252`

**3. [Rule 3 - Blocking] Das Nur-Lesen-Gate verbot das `mkdir` des Indexverzeichnisses**

- **Found during:** Task 1
- **Issue:** tantivy lehnt ein nicht vorhandenes Verzeichnis ab ("Directory does not exist"), und die Standardbibliothek kennt keinen Weg, eines anzulegen, ohne `mkdir` oder `makedirs` zu nennen. Beide stehen in `FORBIDDEN_IDENTIFIERS`.
- **Fix:** Dritter Eintrag in `INVARIANT_2_EXCEPTIONS`, `("index/open.py", "mkdir")`, mit derselben Begruendung wie die beiden vorhandenen: Invariante 1 haelt `nc_py_api` und `httpx` aus dem Modul heraus, das Verzeichnis liegt im eigenen Volume des Containers. Der vorhandene Positivtest wurde um die Zeile erweitert; der Negativtest deckt `index/schema.py` bereits ab, die Ausnahme breitet sich also nachweislich nicht aus.
- **Files modified:** `backend/tests/test_readonly_gate.py`
- **Verification:** `uv run pytest tests/test_readonly_gate.py -q` gruen (16 Tests).
- **Committed in:** `4bf3252`

**4. [Rule 2 - Korrektheit] Der Versionsstempel von tantivy ist im Typstub nicht deklariert**

- **Found during:** Task 1
- **Issue:** `tantivy.__version__` liefert zur Laufzeit `tantivy v0.26.0, index_format v7`, das mitgelieferte `.pyi` kennt das Attribut nicht, und pyright schlaegt an.
- **Fix:** Eine benannte Konstante `TANTIVY_VERSION` mit `# pyright: ignore[reportAttributeAccessIssue]` und der Begruendung. Bewusst kein Zugriff mit Ersatzwert: der wuerde aus einem umbenannten Attribut eine Versionsmarke machen, die still das Falsche behauptet und damit genau den Reindex verhindert, den sie ausloesen soll.
- **Files modified:** `backend/src/findling/index/open.py`
- **Verification:** `test_the_tantivy_mark_carries_the_on_disk_format` prueft, dass die Marke das Plattenformat nennt und nicht nur die Release-Nummer.
- **Committed in:** `4bf3252`

**5. [Rule 1 - Bug] Der Messlauf brach unter Windows in etwa jedem dritten Lauf ab**

- **Found during:** Task 3 (Messwerkzeug)
- **Issue:** `writer.commit()` scheiterte mitten im Fuellen mit `An IO error occurred: 'Zugriff verweigert (os error 5)'`, in vier von sechs Laeufen an wechselnder Stelle. Damit war das Abnahmekriterium "endet mit Exit 0" nicht verlaesslich erfuellbar.
- **Ursache, gemessen:** derselbe Commit gelingt 0,25 s spaeter in allen beobachteten Faellen. Es ist der bekannte Unterschied der Betriebssysteme: POSIX loescht eine gemappte Datei anstandslos, Windows verweigert das, solange ein Handle offen ist, und tantivy loescht beim Verschmelzen von Segmenten.
- **Fix:** `bench.py` wiederholt einen Commit nach einem IO-Fehler genau einmal und **zaehlt** die Wiederholungen als `commit_retries` in der Ausgabe. `writer.py` bleibt unveraendert: ein dort geschluckter IO-Fehler wuerde eine volle Platte verstecken, und die App laeuft ausgeliefert in einem Linux-Container.
- **Files modified:** `backend/src/findling/index/bench.py`
- **Verification:** je drei Laeufe beider Modi ohne Abbruch, `commit_retries` 0 bis 2.
- **Committed in:** `41a13b5`

**6. [Rule 2 - Korrektheit] Ohne Pause zwischen den Suchen misst der Lastmodus nichts**

- **Found during:** Task 3
- **Issue:** 200 Suchen am Stueck brauchen 6 ms. Sie fallen damit zwischen zwei Commits, und der erste Lauf meldete folgerichtig genau einen Commit im Messfenster: eine Zahl ohne Aussage ueber die Frage, die der Plan stellt.
- **Fix:** `--pace-ms` mit dem Vorgabewert 5 ms. Die Pause wird nicht mitgemessen, verteilt die 200 Proben aber ueber rund eine Sekunde, in der 17 bis 18 Commits liegen. Erst damit ist der p95 die Antwort auf "was kostet die Suche waehrend eines fsync".
- **Files modified:** `backend/src/findling/index/bench.py`
- **Verification:** `commits_in_window` stieg von 1 auf 17 bis 18, der Median von 0,03 auf 0,14 ms.
- **Committed in:** `41a13b5`

### Abweichungen in der Aufgabenzuordnung

- Die Verhaltenszeile "Bei `FINDLING_LANGUAGES=de` bleibt body_en leer" steht in Task 1, betrifft aber das Schreiben. Task 1 prueft, was ihm zusteht (das Schema aendert sich mit der Einstellung nicht), Task 2 prueft das Fuellen. Im Endzustand des Plans ist die Zeile vollstaendig belegt.
- `backend/tests/test_readonly_gate.py` steht nicht in `files_modified` des Plans; die Aenderung ist Folge von Deviation 3.

### Abnahmekriterien im Einzelnen

| Kriterium | Ergebnis |
|---|---|
| `pytest tests/test_index_open.py -q` | Exit 0, 19 Tests |
| `grep -c 'register_tokenizer' open.py` = 3 | **4**, siehe Deviation 2 |
| kein `Index.open`/`tantivy.Index(` ausserhalb `open.py` | keine Treffer, zusaetzlich als Test |
| `grep -Ec 'add_text_field\|add_unsigned_field\|add_integer_field' schema.py` = 9 | 9 |
| `grep -c 'def test_reopen' test_index_open.py` >= 1 | 1 |
| `pytest tests/test_index_writer.py -q` | Exit 0, 18 Tests |
| `grep -c 'delete_documents_by_term' writer.py` = 1 | 1, **aber nur im Docstring**: der Aufruf ist `delete_documents_by_query`, siehe Deviation 1. Das Kriterium ist woertlich erfuellt und in seiner Absicht ueberholt |
| `grep -Ec 'delete_documents\(' writer.py` = 0 | 0 |
| `grep -Ec 'Document\([a-z_]+=' writer.py` = 0 | 0 |
| `grep -c 'add_unsigned' writer.py` >= 2 | 2 |
| `grep -c 'disk_usage' writer.py` >= 1 | 1 |
| `grep -c 'num_threads=1' writer.py` = 1 | 1 |
| `grep -c 'def test_' test_index_writer.py` >= 7 | 18 |
| `pytest -q` ohne DeprecationWarning | 211 Tests gruen; die eine verbleibende Warnung ist eine `StarletteDeprecationWarning` aus `fastapi.testclient` und war vor diesem Plan da |
| `tests/test_readonly_gate.py` gruen | 16 Tests |
| `bench --mode idle --queries 200` | Exit 0, Median und p95 in der Ausgabe |
| `bench --mode under-write --queries 200` | Exit 0, nennt `commits_in_window` |
| `grep -c 'p95' bench.py` >= 2 | 4 |
| `grep -c 'under-write' bench.py` >= 1 | 3 |
| ruff check, ruff format --check, pyright, vulture | alle vier ohne Befund |

---

**Total deviations:** 6 auto-fixed (2x Rule 1, 2x Rule 2, 2x Rule 3)
**Impact on plan:** Kein Scope-Zuwachs. Zwei der sechs (1 und 2) sind Messbefunde, die eine Planannahme widerlegen; beide sind so aufgeloest, dass das Schema unangetastet bleibt und spaetere Plaene nichts umbauen muessen.

## Issues Encountered

- **`delete_documents` ist in 0.26.0 nicht laut.** Der Plan nennt den alten Namen als Quelle einer `DeprecationWarning`, die in dieser Suite ein Testfehler waere. Unter `-W error::DeprecationWarning` und mit `warnings.simplefilter("error")` gemessen: der Aufruf gelingt und warnt nicht. Der alte Name bleibt trotzdem draussen, und ein statischer Test haelt beide Namen aus dem Modul fern; die Begruendung dafuer ist jetzt aber die Wirkungslosigkeit (Deviation 1) und nicht eine Warnung.
- **Ein falsch typisiertes Feld wirft nicht, es toetet den Indexierungsthread.** Gemessen: ein aus Schluesselwortargumenten gebautes Dokument und `add_integer` auf einem `unsigned`-Feld erzeugen beide `panicked ... Input type forbidden. This column has been forced to type U64, received I64(42)` in einem Hintergrundthread, waehrend der Python-Aufruf Erfolg meldet. Deshalb ist die Absicherung dagegen ein statischer Test und kein Laufzeittest: ein Test, der auf eine Ausnahme wartet, wartet ewig.
- **`Document.from_dict` verschluckt unbekannte Feldnamen.** Ein Tippfehler im Feldnamen kostet den Wert ohne jede Meldung. Deshalb kommen alle Feldnamen aus `schema.py`.
- **Kein CI-Lauf moeglich.** Alle Gates liefen lokal ueber `uv run` unter Windows. Der GitHub-Actions-Lauf ist von hier nicht pruefbar und steht aus. Die Zahlen der Messung sind Windows-Zahlen; der Lauf im Container mit gedrosselter Platte ist 02-13.

## Threat Flags

Keine neue Angriffsflaeche. Die sechs `mitigate`-Dispositionen des Plans sind umgesetzt:

| Threat ID | Umsetzung |
|---|---|
| T-02-61 (volle Platte) | `flush` prueft `shutil.disk_usage` zuerst und meldet `paused_low_disk`, ohne zu schreiben; zwei Tests, davon einer fuer die weiterhin antwortende Suche und einer fuer das Nachholen |
| T-02-62 (zweiter Writer) | Genau ein Writer, gekapselt in `writer.py`; `IndexLockedError` statt `ValueError`; dazu der Test, der das ganze Paket nach einem zweiten Oeffner absucht |
| T-02-63 (stiller Analyzerwechsel) | `expected_versions` liefert die fuenf Sollwerte in genau den Schluesseln, die `store/repo.py` vergleicht, inklusive Plattenformat im Tantivy-Stempel |
| T-02-64 (Speicherspitze) | `heap_size` und `num_threads=1` aus `config.py`, oberhalb der harten Untergrenze von 15 MB |
| T-02-65 (falsch typisiertes Feld) | Feldweises Belegen ueber `add_unsigned` und `add_integer`, dazu der statische Test gegen Dokumente aus Schluesselwortargumenten |
| T-02-66 (Suche haengt beim Commit) | `bench.py` misst beide Modi; die Zahlen stehen oben, der Lauf mit gedrosselter Platte ist 02-13 |

T-02-67 (voller Dokumenttext im Volume) bleibt wie geplant `accept`; die Kosten und der Grund stehen im Modul-Docstring von `schema.py` und gehoeren in die Datenschutzaussage von 02-07.

## Known Stubs

Keine. `storage_id` ist als Reserve fuer den Mount-Vorfilter aus Phase 5 im Schema und im Kommentar als solche benannt: eine Spalte jetzt kostet weniger als ein Reindex spaeter.

## User Setup Required

Keine. `bench.py` laeuft ohne Docker und ohne die Debian-Wortliste; fehlt sie, nennt die Ausgabe `wordlist=builtin-sample`, statt sich zu ueberspringen oder falsche Zahlen zu liefern.

## Next Phase Readiness

- **02-08 (Poller/Indexschleife)** findet `IndexBatchWriter` mit `add`, `should_flush`, `flush`, `collect_garbage` und `close` vor. Die Reihenfolge aus Pattern 2 ist einhaltbar: `flush()` liefert den Zustand, der ueber das Quittieren entscheidet, und `paused_low_disk` ist ein Zustand und kein Fehler.
- **02-09 (Suchpfad)** liest die Feldnamen aus `schema.py`, oeffnet ueber `open_index` und ruft `open_reader` einmal, nicht je Suche (0,10 ms gegen 0,005 ms).
- **02-07 (Image, Lizenzen, Datenschutz)** braucht die Aussage zum gespeicherten Dokumenttext; die gemessenen Faktoren stehen im Modul-Docstring von `schema.py`.
- **02-13 (Messprotokoll)** ruft `python -m findling.index.bench --mode under-write` im Container mit gedrosselter Platte. Die Windows-Zahlen oben sind der Vergleichswert, `commit_retries` sollte dort 0 sein.
- **Offene Anschlussstelle, hier bewusst nicht entschieden:** wer `expected_versions` beim Start gegen `Store.version_mismatch` haelt und was eine Abweichung ausloest.

## Self-Check: PASSED

Alle sechs neuen und die eine geaenderte Datei liegen im Worktree; alle fuenf Commit-Hashes stehen im Log von `gsd/agent-02-06`. Keine Loeschungen in einem der Commits. Abschliessender Lauf: `uv run pytest -q` 211 passed, `ruff check`, `ruff format --check`, `pyright` und `vulture --min-confidence 80` ohne Befund.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
