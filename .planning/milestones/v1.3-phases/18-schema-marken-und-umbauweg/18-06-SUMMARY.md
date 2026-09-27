---
phase: 18-schema-marken-und-umbauweg
plan: 06
subsystem: index
tags: [rebuild, band-run, disk-precheck, stateless-resume, fallback-switch, LEX-03]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-01: dreizehn Felder und BODY_FIELD; Plan 18-02: _languages() gegen SUPPORTED_LANGUAGES und die Sprachschleife im Writer; Plan 18-05: sechster Versionsmerker als Ausloeser des Umbaus"
  - phase: 02-indexkern-und-volltextsuche
    provides: "open_index/open_reader als einzige Oeffnungsstelle, index_bytes als Groessensumme, MIN_FREE_BYTES als Bodenwert"
provides:
  - "backend/src/findling/index/rebuild.py mit RebuildVerdict, may_rebuild, RebuildRun, counts_match, _resume_cursor, _document_from, transfer_documents"
  - "Zustandslose Wiederaufnahme: der halbfertige Zielindex ist der einzige Fortschrittsmerker, state.db bekommt keine Zeile"
  - "FINDLING_REBUILD_FALLBACK mit genau zwei Positionen, aufgeloest in settings().rebuild_fallback"
  - "Ratsche auf 56 Dateien mit neuem Baumhash"
affects: [18-07, 18-09, 18-11, 20-sprachumbau]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bandlauf ueber ein Fast Field mit Query.range_query und Order.Asc statt wachsendem Offset; ein Commit je Band, das Band ist damit die Absturzkoernung"
    - "Zustandsloser Fortschritt: der halbfertige Zielindex wird nach seiner hoechsten file_id gefragt, kein zweiter Zustand neben dem Index"
    - "Verdikt-Dataclass traegt die Zahlen, auf denen sie beruht, damit das Banner nicht ein zweites Mal misst"
    - "try/finally um die Bandschleife: wait_merging_threads laeuft auf jedem Weg heraus, damit der Tausch von 18-07 kein Handle mehr vorfindet"

key-files:
  created:
    - backend/src/findling/index/rebuild.py
    - backend/tests/test_index_rebuild.py
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_config.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Bandlauf oeffnet beide Verzeichnisse ueber open_index und baut sich keinen eigenen Reader; die Endprobe counts_match ist eine eigene Funktion und wird nie aus 'die Schleife lief durch' gefolgert"
  - "transfer_documents nimmt die Bandgroesse als Parameter mit BAND_DOCUMENTS als Vorgabe, nach der Bauart von IndexBatchWriter(heap_bytes=, min_free_bytes=); der Abbruchtest braucht deshalb keinen Testschalter im Produktivpfad"
  - "Der Abbruch wird im Test ueber _document_from gestellt und nicht ueber einen kuenstlichen Schalter: das ist die Stelle, an der ein echter Lauf mitten im Band stirbt"
  - "Kein Eintrag in INVARIANT_2_EXCEPTIONS: rebuild.py legt selbst kein Verzeichnis an, das macht open_index, und dessen Ausnahme steht schon da"
  - "FINDLING_REBUILD_FALLBACK bleibt eine Umgebungsvariable und wird kein occ-Unterbefehl (A7): ein Unterbefehl braucht Route, Controller, Rechtepruefung und einen Lockstep-Release beider Haelften, und die Entscheidung laege dann in der Companion statt dort, wo die Verzeichnisse liegen"

patterns-established:
  - "Zwei statische Proben halten die Mechanik: keine offset-Keyword im Syntaxbaum des Moduls, und aus findling.store darf ausschliesslich index_bytes importiert werden"
  - "Randwerte einer Messung werden als eigener Test mit allen drei Werten gefahren (leere Zeichenkette, negatives mtime, storage_id 2 hoch 40)"

requirements-completed: [LEX-03]

# Metrics
duration: 25min
completed: 2026-09-24
---

# Phase 18 Plan 06: Bandlauf, Vorpruefung und zustandslose Wiederaufnahme Summary

**`index/rebuild.py` steht mit seinen drei unstrittigen Haelften: die Vorpruefung verweigert den Start mit beiden Zahlen im Verdikt, der Bandlauf ueberfuehrt jedes Dokument feldgleich in 500er-Baendern ueber `file_id`, und nach einem Abbruch setzt der naechste Lauf an der hoechsten bereits kopierten `file_id` fort, ohne dass in `state.db` eine einzige Zeile dazukommt.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-24T06:11:00Z
- **Completed:** 2026-09-24T06:36:00Z
- **Tasks:** 3 (Task 2 als TDD-Zyklus RED/GREEN, kein Refactor noetig)
- **Files created:** 2, **modified:** 3

## Accomplishments

- **Vorpruefung.** `may_rebuild(index_dir, new_language_count)` baut den Bedarf als `index_bytes(index_dir) * (1 + 0.40 * new_language_count)` und vergleicht gegen den freien Platz minus `settings().min_free_bytes`. `MIN_FREE_BYTES` ist unangetastet geblieben, der Bedarf wird daraufgesetzt. Genau ein `shutil.disk_usage` im Modul, `rglob` kommt nicht vor, `index_bytes` wird importiert statt nachgebaut.
- **Verdikt mit Zahlen.** `RebuildVerdict(may_start, reason, needed_bytes, free_bytes)` als frozen dataclass mit `slots=True`, nach der Bauart von `FlushResult`. Die Refusal-Logzeile nennt drei Zahlen und keinen Pfad (T-18-06-02), belegt durch einen Test.
- **Bandlauf.** `transfer_documents` laeuft ueber `Query.range_query(schema, FIELD_FILE_ID, FieldType.Unsigned, cursor + 1, 2**64 - 1, True, True)` mit `order_by_field=FIELD_FILE_ID` und `Order.Asc`, Bandgroesse 500, ein Commit je Band. Kein `offset=` im ganzen Modul, und ein statischer Test ueber den Syntaxbaum haelt das fest.
- **Dokumentaufbau.** `_document_from(stored, languages)` baut alle acht gespeicherten Felder feldweise wieder auf, schreibt `body_de` unbedingt (einzige gespeicherte Textkopie, der Snippetgenerator schneidet daraus) und speist jede aktive Kette aus demselben String; `body_en` wird so rekonstruiert, obwohl es in `to_dict()` fehlt.
- **Zustandslose Wiederaufnahme.** `_resume_cursor(target)` liefert 0 auf einem leeren Zielindex und sonst die hoechste `file_id` ueber `search(all_query, limit=1, order_by_field="file_id", order=Order.Desc)`. Der Abbruchtest bricht mitten im dritten Band ab, der zweite Lauf schreibt genau die fehlenden 5 von 9 Dokumenten, und die Schluessel von `Store.read_meta()` sind vorher und nachher identisch.
- **Endprobe.** `counts_match(source, target)` ist eine eigene Funktion, laedt beide Indizes neu und vergleicht `num_docs`; `RebuildRun.complete` traegt ihr Ergebnis, damit der Aufrufer von 18-07 nicht tauscht, solange ein Dokument fehlt.
- **Rueckfallschalter.** `FINDLING_REBUILD_FALLBACK` mit den zwei Positionen leer und `fullreindex`, aufgeloest in `settings().rebuild_fallback`, unlesbarer Wert ist eine Warnung mit dem Variablennamen und nie eine Startverweigerung. Vier Faelle in `test_config.py` (Vorgabe, `  FullReindex ` mit Blanks und Grossbuchstaben, Unsinn plus Warnung ohne den Wert, Positionsliste).
- **Namensgate.** `tests/test_readonly_gate.py` laeuft ueber das neue Modul und ist gruen, ohne dass ein Eintrag aus `FORBIDDEN_IDENTIFIERS` entfernt oder eine Ausnahme eingetragen wurde (`git diff` gegen die Datei ist leer).
- **Ratsche bewegt, mitsamt der Anzahl.** `PACKAGE_FILES_TODAY` 55 auf 56, `PACKAGE_TREE_HASH_TODAY = 68474cd9...`, Kommentarkette um einen Absatz erweitert, der beide bewegten Dateien nennt.
- Volle Suite **2652 passed / 15 skipped**, alle vier Gates gruen (ruff check, ruff format --check, pyright, vulture).

## Task Commits

1. **Task 1: Modulgeruest, Vorpruefung, Rueckfallschalter** - `a5614e4` (feat)
2. **Task 2 RED: Feldparitaet, Abbruch im dritten Band, Randwerte** - `d4a925f` (test)
3. **Task 2 GREEN: Bandlauf, Dokumentaufbau, Wiederaufnahme** - `0cb7d8a` (feat)
4. **Task 3: Ratsche auf 56 Dateien mit neuem Baumhash** - `595a092` (test)

## Files Created/Modified

- `backend/src/findling/index/rebuild.py` (neu, 329 Zeilen) - Modulkopf mit den vier Messabsaetzen vom 2026-09-24 (683 Dok/s, die Form von `to_dict()`, WinError 5 beim Umbenennen mit offenen mmaps, der Schemafehler einer nicht registrierten Kette), `LOGGER`, `GROWTH_PER_LANGUAGE`, `ROOM_ENOUGH`/`NOT_ENOUGH_ROOM`, `BAND_DOCUMENTS`, `_HIGHEST_FILE_ID`, `RebuildVerdict`, `may_rebuild`, `RebuildRun`, `counts_match`, `_resume_cursor`, `_document_from`, `transfer_documents`.
- `backend/tests/test_index_rebuild.py` (neu, 18 Faelle) - Platzverweigerung mit beiden Zahlen und ohne Pfad in der Logzeile, Feldparitaet aller acht gespeicherten Felder ueber 30 Dokumente, `body_en` als Frage statt als Feldvergleich, die drei Randwerte, Cursor auf leerem und auf halbem Zielindex, Abbruch und Wiederaufnahme mit unveraenderten `read_meta()`-Schluesseln, Endprobe in beiden Richtungen, plus die zwei statischen Proben.
- `backend/src/findling/config.py` - `REBUILD_FALLBACK_POSITIONS`, `DEFAULT_REBUILD_FALLBACK`, `_rebuild_fallback()`, das Feld `rebuild_fallback` in `Settings` und seine Aufloesung in `settings()`; daneben der Absatz, warum das eine Umgebungsvariable und kein `occ`-Unterbefehl ist.
- `backend/tests/test_config.py` - `FINDLING_REBUILD_FALLBACK` in der `ENVIRONMENT`-Liste und vier neue Faelle.
- `backend/tests/test_measurement_scripts.py` - `PACKAGE_FILES_TODAY = 56`, neuer Baumhash, zweiundzwanzigster Absatz der Kommentarkette.

## Die Zahlen hinter dem Faktor 0,40

| Aufbau | Faktor gegen den Text | Herleitung |
|---|---|---|
| Grundindex, neun Felder | 0,231 | Messung 2026-09-24, 2.000 Dokumente, 9,88 MB Text |
| je zusaetzlich befuellte Kette | 0,086 mal Text | `(5.692.365 - 2.277.376) / 4` |
| je Kette gegen den Grundindex | **0,372** | `0,086 / 0,231` |
| im Code | **0,40** | bewusst darueber: Abbruch vor dem Start kostet eine Logzeile, Abbruch mitten im Lauf den ganzen Durchgang |

## Decisions Made

- **Die Bandgroesse ist ein Parameter mit Vorgabe, kein Testschalter.** `transfer_documents(..., band_documents=BAND_DOCUMENTS)` folgt der Bauart von `IndexBatchWriter(heap_bytes=..., min_free_bytes=...)`, wo der Produktivwert aus den Einstellungen kommt und der Aufrufer ihn ueberschreiben darf. Der Abbruchtest kann damit mit Baendern von 2 arbeiten und der Produktivpfad traegt keine Zeile, die nur fuer Tests da ist.
- **`_HIGHEST_FILE_ID` ist `2**64 - 1` und nicht `2**63 - 1`.** `file_id` ist ein unsigned Feld, also ist das die obere Kante der Spalte; gemessen nimmt `Query.range_query` den Wert an. Ein zu kleiner Deckel waere ein Dokument, das nie kopiert wird, und nichts wuerde es melden.
- **`counts_match` nimmt zwei `Index` und keine Pfade.** Der Aufrufer von 18-07 haelt beide Objekte ohnehin, und zwei Pfade wuerden das Oeffnen ein drittes Mal bezahlen. `transfer_documents` ruft die Funktion selbst und liefert das Ergebnis als `RebuildRun.complete` mit, damit ein Aufrufer die Frage nicht vergessen kann.
- **`wait_merging_threads()` steht im `finally`.** Jeder Weg aus der Bandschleife heraus, auch der ueber eine Ausnahme, gibt den Writer und damit die Sperre zurueck. Das ist die Vorbedingung des Tausches von 18-07 (auf Windows gemessen: Umbenennen mit offenen mmaps antwortet WinError 5) und zugleich der Grund, warum der Abbruchtest ueberhaupt ein zweites Mal laufen kann.
- **Kein Eintrag in `INVARIANT_2_EXCEPTIONS`.** Das Modul legt kein Verzeichnis an: `open_index` tut das, und die Ausnahme dafuer steht seit Phase 2 dort. Der Plan sagt ausdruecklich "Braucht es keinen, wird auch keiner eingetragen", und `git diff` gegen `test_readonly_gate.py` ist leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Messsatz zum Offset steht ohne das Zeichen `=` im Kommentar**

- **Found during:** Task 2 (nach dem GREEN-Lauf, beim Abhaken der Abnahmekriterien)
- **Issue:** Das Abnahmekriterium verlangt `grep -c "offset=" backend/src/findling/index/rebuild.py` gleich 0, die Aktion verlangt zugleich den Messsatz `search(all_query, limit=1000, offset=51000)` als Kommentar an der Bandzeile. Beides woertlich erfuellt geht nicht: der Satz enthaelt die gesuchte Zeichenkette zweimal.
- **Fix:** Der Kommentar nennt die Messung ausgeschrieben ("mit einem Limit von 1000 und einem Offset von 51000") und sagt in einem Halbsatz, warum er ausgeschrieben ist. Der Inhalt der Warnung bleibt vollstaendig, der Greptest ist 0, und der Test im Suite-Teil prueft schaerfer als der grep: er sucht `ast.keyword` mit `arg == "offset"` im Syntaxbaum und findet damit auch eine Schreibweise mit Leerzeichen.
- **Files modified:** backend/src/findling/index/rebuild.py
- **Verification:** `grep -c "offset=" backend/src/findling/index/rebuild.py` meldet 0, `test_the_band_walks_the_documents_and_never_pages_with_an_offset` gruen.
- **Committed in:** `0cb7d8a`

**2. [Rule 3 - Blocking] `tests/test_index_rebuild.py` entsteht schon in Task 1**

- **Found during:** Task 1
- **Issue:** Die Dateiliste von Task 1 nennt die neue Testdatei nicht, das Verifikationskommando von Task 1 ruft sie aber auf (`pytest -q tests/test_config.py tests/test_index_rebuild.py`), und das Abnahmekriterium zur Platzverweigerung gehoert inhaltlich zu Task 1.
- **Fix:** Die Datei entsteht in Task 1 mit den sechs Faellen der Vorpruefung; die Faelle des Bandlaufs kommen im RED-Schritt von Task 2 dazu.
- **Files modified:** backend/tests/test_index_rebuild.py
- **Verification:** Task-1-Kommando gruen (190 passed).
- **Committed in:** `a5614e4`

### Nicht umgesetzt, bewusst

- **`backend/tests/test_readonly_gate.py` ist unveraendert.** Die Datei steht in der Kopfzeile des Plans unter `files_modified`, die Aktion von Task 3 macht die Aenderung aber ausdruecklich davon abhaengig, ob das Modul selbst ein Verzeichnis anlegt. Es legt keines an, also bleibt die Datei, wie sie ist. Das Gate ist ueber das neue Modul gelaufen und gruen.

## Was dieser Plan ausdruecklich nicht tut

- **Kein Verzeichnistausch.** `swap_in` und `retire_directory` sind Plan 18-07. Die Vorbedingung dafuer, dass am Ende eines Laufs kein Handle mehr offen ist, wird hier trotzdem schon eingehalten.
- **Kein Ruhigstellen des Pollers.** Die Bedingung, ohne die der Bandlauf falsch wird (der Poller darf waehrend des Laufs nicht in den Quellindex schreiben, sonst landet ein Dokument unterhalb des Cursors und wird nie kopiert), steht als Warnabsatz im Docstring von `transfer_documents`. Das Ruhigstellen selbst gehoert dem Aufrufer von Plan 18-09, weil derselbe Aufrufer auch entscheiden muss, wann wieder scharf gestellt wird.
- **Kein Stempel.** Das Modul schreibt keine Versionsmarke und keine Generation. `stamp_after_rebuild` bleibt die einzige Stelle, die einen Umbau fuer beendet erklaert (T-18-06-05).

## Threat-Dispositionen

| Threat ID | Umsetzung |
|---|---|
| T-18-06-01 | Alle Pfade kommen als Argument herein und werden von den Aufrufern aus `settings().index_dir` abgeleitet; das Modul liest keinen Pfad aus einer Warteschlangenzeile |
| T-18-06-02 | Die drei Logzeilen zaehlen Bytes und Dokumente; ein Test prueft, dass die Refusal-Warnung den Verzeichnisnamen nicht enthaelt |
| T-18-06-03 | 500 Dokumente je Band mit Begruendungsabsatz gegen das 4-GB-Budget, Commit je Band |
| T-18-06-04 | Faktor 0,40 oberhalb des gemessenen 0,372, `MIN_FREE_BYTES` unveraendert als Boden darunter |
| T-18-06-05 | `counts_match` als eigene Funktion, `RebuildRun.complete` als ihr Ergebnis; das Modul stempelt nichts |
| T-18-06-06 | Readonly-Gate A gruen ohne neue Ausnahme und ohne aufgeweichte Verbotsliste |
| T-18-06-SC | Kein Paket installiert; `shutil`, `logging`, `dataclasses`, `pathlib` sind stdlib, `tantivy` ist gepinnt und stand schon im Baum |

## Verification

- `uv run python -m pytest -q` - 2652 passed, 15 skipped
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 133 files already formatted
- `uv run pyright` - 0 errors, 0 warnings, 0 informations
- `uv run vulture` - keine Meldung
- `grep -c "offset=" backend/src/findling/index/rebuild.py` - 0
- `grep -c "rglob" backend/src/findling/index/rebuild.py` - 0
- `grep -v '^ *#' backend/src/findling/index/rebuild.py | grep -c "shutil.disk_usage"` - 1
- `40b-baumhash.py src/findling "**/*.py"` - `dateien: 56`, `baumhash: 68474cd9715062ed734b88b9a72b8bfc95a1773a83f4e6b96f7a1e3406c1fee4`

## Known Stubs

Keine. Jede Funktion des Moduls hat einen Aufrufer im Test und einen benannten Aufrufer in einem der Folgeplaene (18-07 fuer `counts_match` und das Ende des Laufs, 18-09 fuer `may_rebuild` und `transfer_documents`, 18-11 fuer `settings().rebuild_fallback`).

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans: kein Netzpfad, keine Authentifizierung, kein neues Schema, kein Dateizugriff ausserhalb des eigenen Volumes.

## Self-Check: PASSED

- `backend/src/findling/index/rebuild.py` vorhanden, 329 Zeilen (Mindestmass 150), enthaelt `range_query`, `open_index(`, `index_bytes(`
- `backend/tests/test_index_rebuild.py` vorhanden, enthaelt `_resume_cursor`
- Commits `a5614e4`, `d4a925f`, `0cb7d8a`, `595a092` im Log gefunden
- `git diff 2ba1502..HEAD -- backend/tests/test_readonly_gate.py` leer, also kein Eintrag aus `FORBIDDEN_IDENTIFIERS` entfernt
