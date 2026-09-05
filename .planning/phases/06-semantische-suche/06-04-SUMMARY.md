---
phase: 06-semantische-suche
plan: 04
subsystem: database
tags: [sqlite-vec, vec0, int8, vektorspeicher, schema, meta-marken, abstraktionsschnitt, char-offsets, embedding-version]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-01: die Antworten A12 und A13, vec0 im Abbild an FINDLING_VEC0_PATH, der vec_int8()-Befund"
  - phase: 06-semantische-suche
    provides: "06-02: die Chunkzahl 100.136, die Scan-Latenzen und das D-04-Verdikt, ohne die dieses Schema nicht festgezurrt werden durfte"
  - phase: 06-semantische-suche
    provides: "06-03: der D-02-Entscheid, dass int8-Vektoren der Messpunkt sind und die Vektorquantisierung nichts Messbares kostet"
  - phase: 02-store-und-index
    provides: "store/repo.py mit replace_acl, prefilter_visible, _transaction und der Marken-Mechanik, an der sich vectors.py woertlich orientiert"
provides:
  - "store/vectors.py: der Abstraktionsschnitt aus D-08, sechs Aufrufe breit (replace_chunks, drop_vectors, forget_all, nearest, chunks_of, open_vectors)"
  - "store/vectors.sql: chunk_vectors als vec0-Virtualtabelle int8[384] und die chunks-Bruecke mit char_start und char_end"
  - "eine eigene vectors.db neben state.db, mit den drei Gruenden im Schemakopf"
  - "SCHEMA_VERSION 2 unter einer eigenen Marke store_schema_version, rein additiv, ohne Volltext-Reindex"
  - "embedding_version als meta-Marke plus VECTOR_ONLY_MARKS, die Marken ohne Wirkung auf den Tantivy-Bestand"
  - "docs/embeddings.md mit der gemessenen Kennzahl 876,0 Byte je Dokument und beiden Ausweichpfaden"
affects: [06-05 Chunker und Modell-Wrapper, 06-06 Durchstich und Degradieren, 06-07 Embedding-Zweitspur und Loeschweg, 06-08 Statusseite, Store-Text D-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Schema als Artefakt neben dem Modul: vectors.sql wird per executescript angewandt, jede Anweisung IF NOT EXISTS, auf jedem Start"
    - "Loeschen vor dem Einfuegen in einer Transaktion, mit der Breitenpruefung davor: eine Wiederzustellung kann den Bestand nicht verdoppeln"
    - "Zwei Zaehler auf zwei Speicher-Engines, getrennt gezaehlt, weil ihre Divergenz die Form eines kaputten Loeschwegs ist"
    - "Der Deckel einer Abfrage ist ein Argument, und was er NICHT deckelt, steht im Docstring"
    - "Ein Groessenbeleg im Schemakommentar wird gegen das ausgelieferte Schema gemessen statt aus der Recherche uebernommen"

key-files:
  created:
    - backend/src/findling/store/vectors.py
    - backend/src/findling/store/vectors.sql
    - backend/tests/test_vector_store.py
    - docs/embeddings.md
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/api/resources.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_read_side.py

key-decisions:
  - "Die Vektoren liegen in einer eigenen vectors.db: verwerfbar ohne Volltextverlust, haelt die Ladefaehigkeit fuer Erweiterungen von state.db fern, und der Pfad bleibt ein Argument"
  - "repo.py::_connect bleibt UNVERAENDERT ohne enable_load_extension. Die Recherche erwartete das Gegenteil; weil die Vektoren in einer eigenen Datei liegen, braucht state.db keine Erweiterung, und weniger Ladefaehigkeit ist die bessere Antwort (A13 belegt, dass es eine Wahl und keine Grenze ist)"
  - "SCHEMA_VERSION 2 bekommt eine eigene meta-Marke store_schema_version. Der Schluessel schema_version traegt die Tantivy-Schemafassung aus config.py; ein Sprung unter diesem Schluessel haette den Volltext-Reindex erzwungen, den D-21 ausschliesst"
  - "version_mismatch meldet den embedding_version-Drift weiterhin und entscheidet nichts; die Trennung liegt in VECTOR_ONLY_MARKS und wird von version_drift angewandt, also dort, wo aus einer Differenz eine Folge wird"
  - "Die Chunk-Kennung kommt von SQLite (lastrowid) und wird nicht aus file_id und Ordinal abgeleitet: eine Ableitung haette den Deckel aus D-01, den ein Betreiber anheben darf, in eine stille Kollision zwischen zwei Dokumenten verwandelt"
  - "open_vectors legt kein Verzeichnis an (Gate A verbietet mkdir ausserhalb einer kurzen Liste, und open_store legt den Datentraeger ohnehin an); ein fehlendes Verzeichnis ist ein Verdrahtungsfehler und keine Reparaturaufgabe"
  - "Die Kennzahl aus Erfolgskriterium 4 ist gemessen statt gerechnet: 43.859.968 Byte fuer 100.136 Chunks, also 438,0 je Chunk und 876,0 je Dokument, 5,8 Prozent des Tantivy-Index"
  - "nearest deckelt k und sagt ausdruecklich, dass es die Zahl der besuchten Zeilen NICHT deckelt: genau das kaufen die beiden Ausweichpfade, und keiner von beiden ist gebaut"

patterns-established:
  - "Eine Zahl im Quelltextkommentar wird gegen das ausgelieferte Artefakt gemessen und nennt daneben, was die Schaetzung war"
  - "Wenn zwei Konstanten denselben meta-Schluessel teilen und ihre Bedeutungen auseinandergehen, bekommt die juengere ihren eigenen Schluessel, bevor die erste Erhoehung sie in Konflikt bringt"

requirements-completed: [SEM-03]

# Metrics
duration: 30min
completed: 2026-09-05
---

# Phase 6 Plan 04: Vektorspeicher und Schema Summary

**Das Vektorschema steht, nach den Messungen und nicht davor: zwei Tabellen in einer eigenen vectors.db hinter sechs Aufrufen, eine Löschordnung, die eine Wiederzustellung überlebt, eine Schemafassung 2, die keinen Volltext-Reindex erzwingt, und die Kennzahl aus Erfolgskriterium 4 als gemessene Zahl (876,0 Byte je Dokument) statt als Schätzung.**

## Performance

- **Duration:** rund 30 min
- **Started:** 2026-09-05T05:58:00Z
- **Completed:** 2026-09-05T06:28:00Z
- **Tasks:** 3 von 3
- **Files modified:** 8 (4 neu, 4 geändert)

## Accomplishments

- **Erfolgskriterium 4 ist eingelöst, und zwar mit einer Messung.** Die Recherche hatte 432 Byte je Chunk und 864 je Dokument geschätzt. Gemessen sind gegen genau das ausgelieferte Schema 438,0 und 876,0, bei 100.136 Chunks also 43.859.968 Byte, das sind 5,8 Prozent des gemessenen Tantivy-Index. Die Schätzung lag um 1,4 Prozent daneben, und die Zahl im Schemakommentar ist trotzdem die gemessene, weil sie nachrechenbar ist.
- **Der Abstraktionsschnitt ist eine Datei und keine Absichtserklärung.** sqlite-vec hat seit dem 18.05.2026 keinen Commit gesehen. Alles, was der Rest des Containers vom Vektorspeicher verlangen darf, steht jetzt in einem Modul, und die zwei Auswege sind mit Kosten, Nutzen und Wechselort beziffert, ohne dass einer davon gebaut wurde.
- **Ein stiller Reindex ist abgewendet worden, bevor er entstehen konnte.** `repo.SCHEMA_VERSION` und `config.SCHEMA_VERSION` schrieben bisher denselben meta-Schlüssel und waren zufällig beide 1. Die vom Plan verlangte Erhöhung auf 2 hätte unter diesem Schlüssel eine neue Tantivy-Schemafassung behauptet und damit genau den stundenlangen Neuaufbau erzwungen, den D-21 ausschliesst. Die Fassung von `schema.sql` hat deshalb eine eigene Marke bekommen.
- **Zwei Befunde aus Plan 06-01 haben sich ausgezahlt.** `vec_int8()` an der Aufrufstelle und `load_extension` vor `query_only` sind beim ersten Versuch richtig gewesen, weil sie im Messbericht standen. Die halbe Stunde, die Plan 06-01 dafür ausgegeben hat, ist hier nicht ein zweites Mal ausgegeben worden.

## Task Commits

1. **Task 1 (RED): Das Gatter über dem Vektorspeicher, vor seinem Modul** - `b5e2604` (test)
2. **Task 1 (GREEN): Der Vektorspeicher hinter drei Operationen, in einer eigenen Datei** - `3757cef` (feat)
3. **Task 2: Schemafassung 2, die embedding_version-Marke und ihre Trennung** - `6cfe306` (feat)
4. **Task 3: embeddings.md mit der gemessenen Kennzahl und beiden Ausweichpfaden** - `e0378d1` (docs)

## Files Created/Modified

- `backend/src/findling/store/vectors.py` - der Abstraktionsschnitt: `replace_chunks`, `drop_vectors`, `forget_all`, `nearest`, `chunks_of`, `open_vectors`, dazu `embedding_mark` und zwei benannte Ausnahmen (`ExtensionUnavailable`, `DimensionMismatch`); kein `findling.config`-Import, Pfad als Argument, kein `mkdir`, kein Bezeichner `delete`
- `backend/src/findling/store/vectors.sql` - `chunk_vectors` als vec0-Virtualtabelle `int8[384]`, `chunks` mit `char_start` und `char_end` als ZEICHEN, `chunks_file`-Index; jeder Block mit Grössenbeleg, Fremdschlüssel-Begründung und dem Zugriffspfad, der den Index braucht
- `backend/tests/test_vector_store.py` - 32 Tests über die elf Verhaltensweisen, darunter die Wiederzustellung, die Bandung über 1.200 Chunks, die Feldmenge von `Neighbour` und A12 als Eigenschaft des Moduls
- `backend/src/findling/store/repo.py` - `SCHEMA_VERSION` auf `"2"`, neue Konstanten `STORE_SCHEMA_MARK`, `EMBEDDING_MARK` und `VECTOR_ONLY_MARKS`, `_DEFAULT_META` entsprechend umgestellt, der `_connect`-Kommentar mit der Fundstelle von Probe A13
- `backend/src/findling/api/resources.py` - `expected_marks` trägt `embedding_version`, zusammengesetzt aus Modellname, Quantisierung, Dimensionszahl und Tokendeckel; `version_drift` lässt die Vektormarken aus
- `backend/tests/test_store_repo.py` - drei Fälle auf die getrennten Marken umgestellt, vier neue: die Saatwerte, die Zugehörigkeit zu `VECTOR_ONLY_MARKS`, der gemeldete Embedding-Drift und eine Datenbank der Fassung 1, die öffnet und ihren Bestand behält
- `backend/tests/test_read_side.py` - zwei neue Fälle: die Marke steht in `expected_marks`, und ihr Drift erscheint in `version_mismatch`, ohne dass `version_drift` etwas meldet
- `docs/embeddings.md` - sechs Abschnitte: Abdeckung, Modell, Schema, die Kennzahl mit Rechenweg und Kommandozeile, die zwei Ausweichpfade, das Wartungsrisiko

## Die Kennzahl in Kurzform

| Grösse | Wert | Herkunft |
|---|---|---|
| Byte je Vektor | 384 | gerechnet (384 Dimensionen mal 1 Byte) |
| Chunks je Dokument | 2 | gerechnet aus dem 1.024-Token-Deckel (D-01) |
| Chunks insgesamt | 100.136 | Welle-0-Bericht, Ableitung 1 |
| Dateigrösse `vectors.db` | **43.859.968 Byte** | **gemessen 05.09.2026** |
| Byte je Chunk | **438,0** | gerechnet aus der Messung (geschätzt: 432) |
| Byte je Dokument | **876,0** | gerechnet aus der Messung (geschätzt: 864) |
| Verwaltung je Chunk | 54,0 Byte | gerechnet (geschätzt: 48) |
| Zuwachs gegenüber dem Tantivy-Index | **5,8 Prozent** | gerechnet (geschätzt: 5,7) |

## Decisions Made

- **`repo.py::_connect` bleibt unverändert.** Der Plan liess beide Wege offen und verlangte, den gewählten hier zu nennen. Gewählt ist der ohne `enable_load_extension`: weil die Vektoren in einer eigenen Datei liegen, braucht `state.db` keine Erweiterung, und die Fähigkeit, Maschinencode in diesen Prozess zu laden, existiert damit in genau einem Modul, das sie für eine bekannte Bibliothek einschaltet und unmittelbar danach wieder abschaltet (T-06-14). Probe A13 belegt, dass die Übersetzung im Abbild es könnte, was diesen Verzicht zu einer Wahl macht und nicht zu einer Grenze. Die Fundstelle steht als Kommentar an der Funktion.
- **Eine eigene `vectors.db`.** Die offene Stelle aus Claude's Discretion ist so entschieden, wie die Recherche es empfohlen hatte, und die drei Gründe stehen im Kopf von `vectors.sql`. Der wichtigste ist nicht der Platz, sondern die Verwerfbarkeit: "bau die semantische Hälfte neu" ist damit ein `rm`.
- **Die Chunk-Kennung kommt von SQLite.** Eine abgeleitete Kennung (`file_id` mal Deckel plus Ordinal) wäre schneller und würde den Deckel aus D-01, den ein Betreiber anheben darf, in eine stille Kollision zwischen zwei Dokumenten verwandeln. Ein `INSERT` je Chunk statt `executemany` ist der Preis, und bei zwei Chunks je Dokument ist er nicht messbar.
- **`nearest` sagt, was sein Deckel nicht deckelt.** `k_max` begrenzt die Antwort. Die Zahl der besuchten Zeilen begrenzt es nicht, weil kein Parameter dieser Abfrage das kann: sqlite-vec scannt den ganzen Bestand. Genau das kaufen die beiden Ausweichpfade, und dass es heute bezahlbar ist, ist gemessen (37,8 ms p95 warm gegen 300 ms).
- **Die Vorgabe von `k_max` ist 100**, die Fenstertiefe je Quelle aus D-12. Wer mehr verlangt, als die Verschmelzung verwenden kann, verlangt Scanarbeit, die niemand liest.
- **Der Wert von `embedding_version` ist `multilingual-e5-small/int8/384/1024`.** Vier Grössen, weil eine Änderung an jeder von ihnen einen gespeicherten Vektor mit einem frisch gerechneten Anfragevektor unvergleichbar macht. Zwei davon kommen aus `vectors.py`, die anderen zwei stehen bis Plan 06-06 als Konstanten neben der Stelle, an der die Marke gebildet wird.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die verlangte Erhöhung von SCHEMA_VERSION hätte einen Volltext-Reindex erzwungen**

- **Found during:** Task 2
- **Issue:** `repo.SCHEMA_VERSION` (die Fassung von `schema.sql`) und `config.SCHEMA_VERSION` (die Fassung des Tantivy-Schemas) schreiben beide den meta-Schlüssel `schema_version`: die eine über `_DEFAULT_META`, die andere über `index/open.py::expected_versions`. Bis heute standen beide auf 1, der Konflikt war deshalb unsichtbar. Eine Erhöhung der ersten auf "2" unter diesem Schlüssel hätte behauptet, das Tantivy-Schema habe eine neue Fassung, und `start_rebuild_on_drift` hätte die Generation angehoben: ein stundenlanger Neuaufbau des Volltextbestands, also genau das, was D-21 und das Abnahmekriterium dieses Plans ausschliessen.
- **Fix:** Die Fassung von `schema.sql` bekommt eine eigene Marke `store_schema_version`. Der Schlüssel `schema_version` bleibt bei seiner Bedeutung (Tantivy-Schema) und wird von `_DEFAULT_META` mit dem Platzhalter `unknown` gesät, wie `analyzer_version` und `tantivy_version` es schon werden: eine Zustandsdatenbank, die dieses Modul ohne Angabe angelegt hat, kann über die Tantivy-Fassung nichts aussagen. Der Grund steht als Kommentar an beiden Konstanten.
- **Files modified:** backend/src/findling/store/repo.py, backend/tests/test_store_repo.py
- **Verification:** Drei bestehende Fälle in `test_store_repo.py` mussten auf die getrennten Marken umgestellt werden und waren damit der Beleg, dass der Konflikt real war; ein neuer Fall hält `_DEFAULT_META` fest. Die volle Suite ist grün, und `version_drift` meldet auf einem frischen Datenträger unverändert nichts.
- **Committed in:** `6cfe306`

**2. [Rule 2 - Fehlende kritische Funktion] Ohne eine Trennung der Marken hätte die neue Marke den Reindex-Banner dauerhaft gesetzt**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt, dass `expected_marks` die Marke `embedding_version` trägt und dass ihr Drift den Tantivy-Index nicht invalidiert. Beides zusammen geht nicht von allein: `version_drift` reicht das Ergebnis von `version_mismatch` unverändert an `api/status.py` weiter, wo es als `reindexRequired` erscheint. Ein Container ohne Vektorbestand, also jeder frisch installierte, hätte ab dem ersten Start einen Reindex-Banner gezeigt, dessen Abhilfe nichts an der Ursache ändert.
- **Fix:** `VECTOR_ONLY_MARKS` in `repo.py` als die eine Stelle, die sagt, welche Marken nichts über den Tantivy-Index aussagen, und `version_drift` filtert danach. `version_mismatch` bleibt unverändert und meldet weiterhin alles; sein Docstring ("It decides nothing.") bleibt damit wahr, und die Entscheidung liegt beim Aufrufer, der sie ohnehin trifft.
- **Files modified:** backend/src/findling/store/repo.py, backend/src/findling/api/resources.py, backend/tests/test_read_side.py
- **Verification:** Ein Test schreibt eine ältere Marke und belegt beides zugleich: `version_mismatch` nennt sie, `version_drift` gibt eine leere Liste zurück.
- **Committed in:** `6cfe306`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**3. Die neuen Marken-Tests stehen nicht in `test_store_metadata.py`**

Der Plan führt `backend/tests/test_store_metadata.py` als Ablage für die neuen
Fälle und beschreibt sie als "welche Marken heute geprüft werden". Diese Datei
prüft aber nicht die Marken der Zustandsdatenbank, sondern die **Store-Texte**
der beiden App-Store-Einträge (Sprachen, Längen, Bindestriche, Screenshots).
Der Name kollidiert, der Inhalt hat mit dem Vorhaben nichts zu tun. Die neuen
Fälle liegen deshalb dort, wo ihre Gegenstände schon geprüft werden:
`test_store_repo.py` für die meta-Marken (dort steht die `store`-Fixture und die
bestehenden `version_mismatch`-Fälle) und `test_read_side.py` für
`expected_marks` und `version_drift`. Beide Dateien stehen ohnehin in der
Verifikationszeile des Plans.

**4. Der Abstraktionsschnitt ist sechs Aufrufe breit und nicht drei**

D-08 nennt drei Operationen (speichere, lösche, finde_ähnliche), und die
Handlungsanweisung des Plans nennt sechs Bezeichner. Gebaut sind sechs plus zwei
Zähler: `replace_chunks`, `drop_vectors`, `forget_all`, `nearest`, `chunks_of`,
`open_vectors`, `chunk_count`, `vector_count`. Die drei aus D-08 sind darin
enthalten; `forget_all` ist der Reindexweg, `chunks_of` die Rückrichtung für
Löschweg und Diagnose, und die zwei Zähler existieren, weil die beiden Tabellen
in verschiedenen Speicher-Engines liegen und ihre Divergenz die Form eines
kaputten Löschwegs ist. Die Eigenschaft, um die es D-08 geht, ist erfüllt: ein
Wechsel auf Bit-Vektoren oder usearch betrifft diese eine Datei.

**5. `chunk_count` und `vector_count` sind im Plan nicht vorgesehen**

Sie sind dazugekommen, weil ohne sie kein Test belegen kann, dass zweimaliges
`replace_chunks` denselben Bestand hinterlässt wie einmaliges, ohne selbst SQL
zu schreiben. Ein Test, der am Modul vorbei in die Datenbank greift, prüft nicht
mehr das Modul. Beide werden ausserdem von der zweiten Deckungsgrad-Zahl aus
D-16 gebraucht.

---

**Total deviations:** 2 autorepariert (1 Fehler, 1 fehlende kritische Funktion), 3 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Beide Autoreparaturen betreffen genau die Eigenschaft, die dieser Plan zusichern soll: dass die Schemaänderung additiv ist und keinen Volltext-Reindex auslöst.

## Issues Encountered

- **Die Kennzahl liess sich nicht aus dem Welle-0-Bericht übernehmen.** Der Bericht misst, was ein Scan liest (38,4 MB Nutzlast), nicht, was auf der Platte liegt; der Verwaltungsanteil je Chunk war nur geschätzt. Gelöst mit einem Messlauf gegen das gerade entstandene Schema, dessen Kommandozeile in `docs/embeddings.md` steht. Die Verbindung wird vor dem `stat` geschlossen, sonst läge ein Teil des Bestands noch im WAL und die gemessene Datei wäre zu klein.
- **Die Vorgabemetrik der `int8[384]`-Spalte ist L2 und nicht Kosinus.** Die Recherche spricht von Kosinus. Gemessene Distanzen liegen im L2-Bereich, und die Metrik ist eine Deklaration in `vectors.sql`. Bei normierten Vektoren ist die Rangfolge unter beiden dieselbe; ob die int8-Quantisierung die Normierung ausreichend erhält, ist nicht gemessen. Der Punkt steht in `docs/embeddings.md` benannt und gehört in Plan 06-06, wo der Anfragevektor entsteht.
- **Kein Messlauf auf der AWS-Box.** Die Box ist nicht angefasst worden; dort läuft der Phase-5-Volllauf. Die Grössenmessung ist plattformunabhängig, weil das SQLite-Dateiformat es ist, und über Geschwindigkeit sagt sie nichts.

## Offene Verifikation

Keine. Alle Gates sind lokal grün gelaufen: `pytest` mit 1.096 bestandenen und 11
übersprungenen Tests, `ruff check .`, `ruff format --check .`, `pyright` mit 0
Fehlern und `vulture` ohne Befund, jeweils im CI-Umfang `backend`. Die neun
vorbestehenden Markdown-Formatbefunde oberhalb von `backend` (DI-06-01) sind
unverändert und nicht Gegenstand dieses Plans.

## User Setup Required

None - keine externe Konfiguration nötig. Das Schema entsteht beim ersten Öffnen,
die Erweiterung liegt seit Plan 06-01 im Abbild.

## Next Phase Readiness

- **Plan 06-05 kann den Chunker und den Modell-Wrapper bauen.** Die Form, in der ein Chunk abgelegt wird, steht fest (`Chunk` mit Ordinal, zwei Zeichenoffsets und einem 384 Byte breiten int8-Vektor), und die Breitenprüfung ist die Stelle, an der ein falsch konfiguriertes Modell auffällt statt still zu wirken.
- **Plan 06-06 findet den Lesepfad fertig.** `open_vectors(..., read_only=True)` liefert eine Verbindung unter `PRAGMA query_only = 1`, `nearest` gibt ausschliesslich Zahlen zurück, und der Deckel ist ein Argument. Was 06-06 noch zu entscheiden hat: der Vorgabewert des Deckels als Einstellung in `config.py`, die Distanzmetrik der Spalte und die Präfixe am Anfragevektor.
- **Plan 06-07 hat seine Werkzeuge.** `drop_vectors`, `forget_all` und `chunks_of` existieren; ihre Verdrahtung in `drop_document`, `tombstone` und `reset_for_reindex` ist dort zu leisten. `replace_chunks` löscht bereits vor dem Einfügen, der Wiederzustellungsfall ist damit strukturell erledigt.
- **Plan 06-08 kann die zweite Deckungsgrad-Zahl rechnen.** `chunk_count` und `vector_count` stehen bereit.
- **Ein Punkt für 06-06 und 06-07, damit er nicht doppelt gefunden wird:** `embedding_version` wird heute von niemandem geschrieben. Die Marke steht auf `unknown`, ihr Drift wird gemeldet und bleibt folgenlos, bis die Zweitspur sie nach einem abgeschlossenen Lauf stempelt.
- **Kein Blocker.**

## Self-Check: PASSED

Alle vier angelegten Dateien liegen auf der Platte
(`backend/src/findling/store/vectors.py`, `backend/src/findling/store/vectors.sql`,
`backend/tests/test_vector_store.py`, `docs/embeddings.md`), alle vier Commits
(`b5e2604`, `3757cef`, `6cfe306`, `e0378d1`) stehen in `git log`. Zusätzlich
geprüft: `grep -c 'def delete'` in `vectors.py` ist 0, der `findling.config`-Import
ist 0, alle drei DDL-Anweisungen tragen `IF NOT EXISTS`,
`SCHEMA_VERSION: Final = "2"` kommt genau einmal vor, weder Geviert- noch
Halbgeviertstrich stehen in einer der acht Dateien, und die Verifikationszeile
des Plans über `docs/embeddings.md` antwortet mit `ok`.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
