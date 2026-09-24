---
phase: 18-schema-marken-und-umbauweg
plan: 07
subsystem: index
tags: [rebuild, swap, reset-read-side, stamp, windows-rename, LEX-03]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-05: REBUILD_MARK und LANGUAGES_MARK mit expected_versions; Plan 18-06: transfer_documents mit RebuildRun.complete, counts_match, wait_merging_threads im finally"
  - phase: 02-indexkern-und-volltextsuche
    provides: "open_index als einzige Oeffnungsstelle, read_side mit _OPEN/_MARKS/_DEGRADED unter _LOCK, Store.read_meta/write_meta"
provides:
  - "backend/src/findling/index/rebuild.py mit swap_in, retire_directory, discard_directory, stamp_after_swap und dem nummerierten Sechs-Schritte-Absatz im Modulkopf"
  - "backend/src/findling/api/resources.py mit reset_read_side: verwirft _OPEN, _MARKS und _DEGRADED unter dem einen _LOCK, prueft absichtlich keinen Pfad"
  - "Der Tauschtest laeuft auf Windows und Linux und traegt kein skipif"
  - "Ratsche auf 56 Dateien mit neuem Baumhash"
affects: [18-08, 18-09, 18-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tausch als zwei Umbenennungen mit nichts dazwischen; der stillgelegte Name wird per with_name aus dem Livepfad abgeleitet und nie hereingereicht"
    - "Zwei Stempler mit zwei Toren: stamp_after_rebuild fuer den Crawl-Fall, stamp_after_swap fuer den Umbau; das Tor des zweiten ist ausschliesslich seine Aufrufstelle"
    - "Prozesscache-Verwerfung als eigene Funktion neben dem Cache statt als Sonderzweig im Getter, weil der Invalidierungszweig auf gleichem Pfad nie greift"

key-files:
  created: []
  modified:
    - backend/src/findling/index/rebuild.py
    - backend/src/findling/api/resources.py
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_read_side.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "stamp_after_swap ruft stamp_after_rebuild ausdruecklich nicht: dessen Tor verdicts_older_than(generation) == 0 fragt nach etwas, das der Umbau nie bewegt, und stuende je nach Zufall des Bestands offen oder zu"
  - "rebuild.py importiert findling.api.resources nicht; Schritt 3 (reset_read_side) gehoert dem Aufrufer von 18-09, damit die Lesehaelfte vom Index zieht und nie umgekehrt"
  - "index_version wird vom Umbau nicht bewegt; die Funktion, die die Generation hebt, existiert fuer einen Crawl, und der Umbau liest keine Datei"
  - "_SCHEMA_MARK einmal in rebuild.py buchstabiert und per Test an expected_versions gekettet, weil es sonst keine Konstante fuer den Schluessel gibt"
  - "Der statische Store-Import-Test weitet sich von einem Namen auf zwei ({index_bytes, Store}): der Stempel braucht den Typ des Handles; open_store bleibt per Textprobe draussen, damit das Modul keine eigene Datenbank oeffnet"

patterns-established:
  - "Ein Fehlschlag-Test stellt den Bruch mitten im dritten Band ueber _document_from und prueft danach das ganze Nichts: kein Tausch, kein Stempel, read_meta byteweise unveraendert, das halbe Zielverzeichnis steht noch"
  - "Statische Probe gegen den falschen Fertigmelder: weder start_rebuild_on_drift noch stamp_after_rebuild taucht als Aufruf im Syntaxbaum von rebuild.py auf"

requirements-completed: [LEX-03]

# Metrics
duration: ~70min (zwei Laeufe; der erste starb nach Task 2 am API-Limit, der zweite hat Task 3 aus dem unkommittierten Stand vervollstaendigt)
completed: 2026-09-24
---

# Phase 18 Plan 07: Verzeichnistausch, Leseseiten-Reset und der Stempel danach Summary

**Der Tausch ist eine Funktion mit einer Reihenfolge: `reset_read_side()` verwirft alle drei Prozesscaches unter dem einen Lock, `swap_in` benennt `index` nach `index.retired` und `index.rebuild` nach `index` um mit nichts dazwischen, und `stamp_after_swap` schreibt Schema- und Sprachmerker und leert `REBUILD_MARK` erst nach Endprobe und Tausch; der Tauschtest laeuft auf Windows wie auf Linux und ist auf keinem System uebersprungen.**

## Performance

- **Duration:** ~70 min ueber zwei Laeufe (08:44 bis 09:44 lokale Commitzeiten)
- **Completed:** 2026-09-24
- **Tasks:** 3 (Task 1 und 2 als TDD-Zyklen RED/GREEN, kein Refactor noetig; Task 3 als ein atomarer Commit)
- **Files created:** 0, **modified:** 5

## Accomplishments

- **`reset_read_side()`.** Steht neben `read_side()` in `api/resources.py` und verwirft `_OPEN`, `_MARKS` und `_DEGRADED` unter demselben `_LOCK`, mit lokaler Uebernahme vor dem Nullsetzen und `store.close()` vor `vectors.close()`. Der Docstring nennt den einen Unterschied zum Vorbild: die Funktion prueft den Pfad nicht, weil der Tausch `index_dir` nicht bewegt und der Invalidierungszweig von `read_side()` deshalb nie von selbst greift. Idempotent auf leerem Zustand, per Test aus zwei Threads gefahren.
- **Der Tausch.** `swap_in(target, live)` sind zwei `Path.rename` mit nichts dazwischen, dann `discard_directory` auf dem stillgelegten Verzeichnis. `retire_directory` leitet den stillgelegten Namen per `with_name(name + RETIRED_SUFFIX)` aus dem Livepfad ab, der geloeschte Pfad wird nie hereingereicht (T-18-07-04). Der Fehlerzweig loggt `type(error).__name__` und keinen Pfad (T-18-07-05).
- **Der Waechter laeuft auf beiden Systemen.** `grep -c "skipif" backend/tests/test_index_rebuild.py` meldet 0, `xfail` ebenso; ein eigener Test haelt sogar statisch fest, dass keine Marke einen Fall aus dem Lauf nimmt. Der Test mit absichtlich offen gehaltenem Searcher zeigt auf Windows den `PermissionError` (WinError 5) und laeuft auf Linux ueber die Zusicherung, dass der Produktivpfad vorher alles losgelassen hat.
- **Sechs Schritte als nummerierter Absatz im Modulkopf.** Commit + `wait_merging_threads()` + Loslassen, Quellindex loslassen, `reset_read_side()`, `index` nach `index.retired`, `index.rebuild` nach `index`, `index.retired` entfernen. Schritte 4 und 5 sind `swap_in`; Schritte 1 bis 3 gehoeren dem Aufrufer von 18-09, weil derselbe Aufrufer entscheidet, wann der Poller wieder scharf ist. `rebuild.py` importiert `findling.api.resources` nicht.
- **`stamp_after_swap`.** Schreibt `schema_version` (als `_SCHEMA_MARK`, per Test an `expected_versions` gekettet), den Sprachmerker als `",".join(settings().languages)` und leert `REBUILD_MARK`. Der Docstring traegt den Satz, warum es ein zweiter Stempler mit eigenem Tor ist: das Tor von `stamp_after_rebuild` (`verdicts_older_than(generation) == 0`) fragt nach Verdikten, die der Umbau nie anruehrt, und stuende je nach Bestand zufaellig offen oder zu; zwei Stempler unter einem Namen sind der klassische Weg, wie ein halber Index sich fuer fertig erklaert (T-18-07-03).
- **Reihenfolge im Test.** Ein Lauf mit gestelltem Bruch mitten im dritten Band tauscht nicht und stempelt nicht: `read_meta()` ist vorher wie nachher identisch, das alte `index` mit allen 9 Dokumenten antwortet noch, das halbe `index.rebuild` steht fuer den naechsten Durchgang. Ein vollstaendiger Umbau stempelt `schema_version = 2`, den Sprachmerker auf die aktive Menge (`de,en,es` im Test) und leert die Marke.
- **Die Generation steht still.** `index_version` ist vor und nach einem vollstaendigen Umbau 7, zur Laufzeit gemessen; statisch haelt ein Syntaxbaum-Test fest, dass weder `start_rebuild_on_drift` noch `stamp_after_rebuild` als Aufruf im Modul vorkommt. `grep -c "start_rebuild_on_drift" backend/src/findling/index/rebuild.py` meldet 0.
- **Ratsche bewegt.** `PACKAGE_FILES_TODAY` bleibt 56, `PACKAGE_TREE_HASH_TODAY = aceb306c...`, Kommentarkette um den dreiundzwanzigsten Absatz erweitert, der `index/rebuild.py` und `api/resources.py` nennt.
- Volle Suite **2669 passed / 15 skipped**, alle vier Gates gruen (ruff check, ruff format --check, pyright latest, vulture).

## Task Commits

1. **Task 1 RED: die Leseseite laesst sich ausdruecklich verwerfen** - `dd193a9` (test)
2. **Task 1 GREEN: reset_read_side verwirft alle drei Prozesscaches unter dem einen Lock** - `5ee9b8a` (feat)
3. **Task 2 RED: der Tausch, auf beiden Systemen und nirgends uebersprungen** - `c462489` (test)
4. **Task 2 GREEN: swap_in, retire_directory und discard_directory** - `0080a15` (feat)
5. **Task 3: stamp_after_swap hinter der Endprobe, die Generation steht still, Ratsche** - `63a8dfa` (feat)

## Files Created/Modified

- `backend/src/findling/index/rebuild.py` (jetzt 486 Zeilen) - `RETIRED_SUFFIX`, `_SCHEMA_MARK`, `swap_in`, `retire_directory`, `discard_directory` (kapselt `shutil.rmtree(..., ignore_errors=False)`: ein stillgelegtes Verzeichnis, das nicht weggeht, ist ein Befund), `stamp_after_swap`; im Modulkopf die Windows-Messung vom 2026-09-24 (Umbenennen mit offenen mmaps antwortet WinError 5) und der Sechs-Schritte-Absatz.
- `backend/src/findling/api/resources.py` (+45 Zeilen) - `reset_read_side()` mit Docstring zu Anlass und Grenze: gerufen ausschliesslich vom Umbau vor der ersten Umbenennung, kein allgemeiner Cache-Reset und keine Erholungsmassnahme.
- `backend/tests/test_index_rebuild.py` (jetzt 767 Zeilen) - Tauschfaelle (Reihenfolge, offener Searcher auf beiden Systemen definiert, weder `index.rebuild` noch `index.retired` nach dem Tausch, Suche antwortet aus dem neuen Verzeichnis), Stempelfaelle (Schluesselkette an `expected_versions`, ganzer Ablauf Probe/Tausch/Stempel, Fehlschlag-Lauf, Generation unbewegt), zwei statische Proben (Store-Importe, kein falscher Fertigmelder).
- `backend/tests/test_read_side.py` (+110 Zeilen) - neue Instanz bei gleichem `index_dir`, geschlossene `store`/`vectors` der alten, `_DEGRADED` kippt ohne TTL-Ablauf, Idempotenz auf leerem Zustand, zwei Threads unter dem einen Lock.
- `backend/tests/test_measurement_scripts.py` - neuer Baumhash bei 56 Dateien, dreiundzwanzigster Absatz der Kommentarkette.

## Decisions Made

- **Zwei Stempler, zwei Tore, zwei Aufrufstellen.** `stamp_after_swap` hat als Tor ausschliesslich seine Aufrufstelle: nach `counts_match` und nach `swap_in`. Frueher gerufen beschriebe der Stempel ein Verzeichnis, aus dem niemand liest, und genau diesen Zustand sollen die Marken sichtbar machen.
- **Keine Konstante fuer `schema_version` nachruesten, sondern die zwei Buchstabierungen per Test ketten.** `findling.index.open` und `findling.store.repo` schreiben den Schluessel als Literal; statt drei Stellen umzubauen haelt `test_the_schema_mark_of_the_stamp_is_the_one_the_expectation_carries` die Schreibweise von `_SCHEMA_MARK` an `expected_versions` fest.
- **Der Store-Import-Test wird zur Menge mit Textprobe.** `{index_bytes, Store}` ist erlaubt (der Stempel braucht den Typ, sonst naehme er ein ungetyptes Handle), `open_store` bleibt per `not in`-Textprobe verboten, damit das Modul nie eine eigene Datenbank neben dem Index oeffnet.
- **Der Fehlschlag-Test ist so gebaut, wie der Aufrufer von 18-09 laufen wird.** Das `if complete:`-Tor vor Tausch und Stempel steht woertlich im Test, damit 18-09 die Zeile abschreiben kann statt sie zu erfinden.

## Deviations from Plan

### Ausfuehrungsnotiz: Abbruch und Wiederaufnahme

Der erste Lauf starb nach Task 2 (vier Commits standen) am API-Limit; Task 3 lag als unkommittierter Diff im Arbeitsbaum. Der Diff wurde gegen die acceptance_criteria geprueft, fuer vollstaendig befunden und vervollstaendigt statt weggeworfen. Kein Task wurde wiederholt.

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der key_link-Pattern `reset_read_side()` stand nicht woertlich in rebuild.py**

- **Found during:** Wiederaufnahme, Abgleich der must_haves
- **Issue:** Der Plan verlangt als key_link das Muster `reset_read_side\(\)` in `rebuild.py`; der Sechs-Schritte-Absatz nannte die Funktion nur als Sphinx-Rolle ohne Klammern, ein Verifier-Grep faende nichts.
- **Fix:** Schritt 3 des Absatzes nennt jetzt `reset_read_side()` woertlich mit Klammern; die Architektur bleibt unveraendert (kein Import von `findling.api.resources`). Ratsche danach neu gefahren, Hash von `a4426e...` auf `aceb306c...`.
- **Files modified:** backend/src/findling/index/rebuild.py, backend/tests/test_measurement_scripts.py
- **Committed in:** `63a8dfa`

## Was dieser Plan ausdruecklich nicht tut

- **Kein Aufraeumpfad beim Start.** Ein Abbruch zwischen den beiden Umbenennungen hinterlaesst ein Volume ohne `index` (T-18-07-02); die Sequenz ist so kurz wie moeglich, der Aufraeumpfad ist Plan 18-08.
- **Kein Aufrufer.** Die Schritte 1 bis 3 (Writer schliessen, Quellindex loslassen, `reset_read_side()`) stehen als nummerierter Absatz im Modul; wer sie in dieser Reihenfolge faehrt, ist der Umbau-Orchestrierer von Plan 18-09.
- **Kein Anfassen von `stamp_after_rebuild`.** Der Crawl-Stempel in `index/open.py` bleibt unveraendert die Stelle fuer den Drift-Fall.

## Threat-Dispositionen

| Threat ID | Umsetzung |
|---|---|
| T-18-07-01 | `reset_read_side()` verwirft `_OPEN`, `_MARKS`, `_DEGRADED` unter `_LOCK` und steht als Schritt 3 vor der ersten Umbenennung; der Tauschtest laeuft auf Windows ohne skipif und faellt dort laut aus, wenn ein Handle offen blieb |
| T-18-07-02 | `swap_in` ist die kuerzestmoegliche Sequenz: zwei Umbenennungen, dann erst das Verwerfen; der Aufraeumpfad beim Start ist Plan 18-08 |
| T-18-07-03 | `stamp_after_swap` als eigene Funktion mit der Aufrufstelle als Tor, gerufen nach `counts_match` und `swap_in`; der Fehlschlag-Test prueft Marken byteweise unveraendert |
| T-18-07-04 | Der stillgelegte Pfad entsteht per `live.with_name(live.name + RETIRED_SUFFIX)` und wird nie hereingereicht; `discard_directory` bekommt nur, was `retire_directory` zurueckgab |
| T-18-07-05 | Der Fehlerzweig des Tauschs loggt `type(error).__name__` und nie einen Pfad |
| T-18-07-SC | Kein Paket installiert; `shutil` und `pathlib` sind stdlib |

## Verification

- `uv run pytest -q` - 2669 passed, 15 skipped
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 133 files already formatted
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` - 0 errors, 0 warnings, 0 informations
- `uv run vulture` - keine Meldung
- `grep -c "skipif" backend/tests/test_index_rebuild.py` - 0 (`xfail` ebenso 0)
- `grep -c "start_rebuild_on_drift" backend/src/findling/index/rebuild.py` - 0
- `40b-baumhash.py backend/src/findling "**/*.py"` - `dateien: 56`, `baumhash: aceb306c30c151b10e2ca598a525328374dfc0faebc2c13461dcb2072827702a`
- must_haves: `swap_in` in rebuild.py, `def reset_read_side` in resources.py, `reset_read_side()` woertlich im Sechs-Schritte-Absatz, `write_meta(` dreimal in `stamp_after_swap`

## Known Stubs

Keine. `swap_in`, `retire_directory`, `discard_directory` und `stamp_after_swap` haben ihre Aufrufer im Test und ihren benannten Produktiv-Aufrufer in Plan 18-09; `reset_read_side` ebenso.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans: kein Netzpfad, keine Authentifizierung, kein neues Schema; der einzige neue Dateizugriff (`rmtree`) arbeitet ausschliesslich auf einem Pfad, den das Modul selbst aus dem Livepfad ableitet.

## Self-Check: PASSED

- `backend/src/findling/index/rebuild.py` vorhanden (486 Zeilen), enthaelt `swap_in`, `stamp_after_swap`, `reset_read_side()`
- `backend/src/findling/api/resources.py` enthaelt `def reset_read_side` (Zeile 343)
- Commits `dd193a9`, `5ee9b8a`, `c462489`, `0080a15`, `63a8dfa` im Log gefunden
- Arbeitsbaum nach dem Task-3-Commit sauber, keine untracked Dateien
