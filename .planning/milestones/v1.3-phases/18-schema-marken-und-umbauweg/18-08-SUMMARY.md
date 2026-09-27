---
phase: 18-schema-marken-und-umbauweg
plan: 08
subsystem: index
tags: [rebuild, recovery, crash-window, volume-state, logging, LEX-03]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-06: transfer_documents mit _resume_cursor aus dem halb gefuellten Zielverzeichnis, counts_match als Endprobe; Plan 18-07: swap_in, retire_directory, discard_directory, RETIRED_SUFFIX"
  - phase: 02-indexkern-und-volltextsuche
    provides: "settings().index_dir als einziger Indexpfad, open_index als einzige Oeffnungsstelle"
provides:
  - "backend/src/findling/index/rebuild.py mit recover_the_index_directories: fuenf Zustaende des Volumes, fuenf benannte Entscheidungen, REBUILD_SUFFIX neben RETIRED_SUFFIX"
  - "Fuenf Antworttexte als geschlossene Liste: NOTHING_TO_PUT_IN_ORDER, HALF_FILLED_TARGET_KEPT, TARGET_RAISED_TO_THE_LIVE_NAME, RETIRED_BROUGHT_BACK, RETIRED_DISCARDED"
  - "docs/uninstall.md nennt die drei Verzeichnisnamen und sagt, was ein Admin von Hand loeschen darf und was nicht"
  - "Ratsche auf Baumhash 4fe79081 bei unveraenderten 56 Dateien"
affects: [18-09, 18-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Aufraeumpfad ohne Parameter: alle drei Verzeichnisnamen per with_name aus settings().index_dir, kein Pfad wird hereingereicht, damit das rmtree nur das Volume dieses Containers erreichen kann"
    - "Abwesenheit als Beweis, einmal und ausgeschrieben: ein fehlendes index belegt, dass der Tausch schon begonnen hatte, weil nur swap_in diesen Namen entfernt und swap_in nur hinter counts_match steht"
    - "Der gewoehnliche Startzweig schweigt; nur die vier Zweige, die im Betrieb nie erscheinen sollen, loggen auf warning"

key-files:
  created: []
  modified:
    - backend/src/findling/index/rebuild.py
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_measurement_scripts.py
    - docs/uninstall.md

key-decisions:
  - "Fall 2 (halb gefuelltes index.rebuild neben lebendem index) bleibt ausdruecklich stehen: das halbe Verzeichnis IST der Fortschrittsmerker, den _resume_cursor liest; Verwerfen wuerde jedes committete Band des abgebrochenen Laufs wegwerfen"
  - "Fall 2 tauscht auch nicht ein: dieser Start weiss nicht, ob der Lauf durch war, das weiss nur counts_match, und die Frage stellt der Lauf und nicht der Start"
  - "Fall 3 raeumt ein daneben stehendes index.retired mit weg, weil das Anheben des Ziels die zweite Umbenennung des Tauschs ist und das Verwerfen der Schritt dahinter"
  - "Ein leeres Volume (gar kein Indexverzeichnis) bekommt dieselbe Antwort wie Fall 1 und keine Warnzeile: eine Warnung, die bei jedem Erststart erscheint, ist keine Warnung"
  - "Die Antwort ist Text aus einer geschlossenen Liste und kein Enum, wie schon bei den zwei Antworten der Vorpruefung: sie reist in einen Betriebsbericht"

patterns-established:
  - "Zustandsbeweis per Dreifachlesung: relativer Pfad, mtime in Nanosekunden und Inhaltsdigest je Datei, damit 'unveraendert' gegen Kommen/Gehen, Umschreiben und Gleichschreiben haelt"
  - "Der caplog-Test faehrt alle vier sprechenden Zweige in einem Fall und liest jede Zeile: kein Volumename, kein absoluter Pfad, kein Schraegstrich in beide Richtungen"
  - "Koederverzeichnis eine Ebene ueber dem Volume (volume.name + '.retired'), das nach dem Lauf unangetastet dasteht: so faellt eine per Zeichenkettenverkettung statt with_name gebaute Ableitung auf"

requirements-completed: [LEX-03]

# Metrics
duration: ~35min
completed: 2026-09-24
---

# Phase 18 Plan 08: Der Aufraeumpfad beim Start Summary

**Ein Container liest beim Start, was im Volume steht, und entscheidet fuenf Zustaende einzeln: der gewoehnliche Start bleibt unberuehrt, ein halb gefuelltes `index.rebuild` bleibt als Fortschrittsmerker stehen, ein `index.rebuild` ohne `index` wird an die Livestelle gehoben, ein `index.retired` ohne `index` wird zurueckgeholt, und ein `index.retired` neben einem `index` ist Abfall und geht.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-24
- **Tasks:** 2 (Task 1 als TDD-Zyklus RED/GREEN, kein Refactor noetig; Task 2 als ein atomarer Commit)
- **Files created:** 0, **modified:** 4

## Accomplishments

- **`recover_the_index_directories()`.** Nimmt keinen Parameter, liest `settings().index_dir` und leitet die zwei Nachbarnamen zweimal per `with_name` ab (`REBUILD_SUFFIX = ".rebuild"` neben dem vorhandenen `RETIRED_SUFFIX`). Damit kann das `rmtree` dieses Moduls ausschliesslich ein Verzeichnis erreichen, das die Funktion selbst benannt hat, auf dem Volume, auf das `findling.config` zeigt (T-18-08-03).
- **Fuenf Zustaende, fuenf benannte Zweige, fuenf Antworttexte.** Fall 1 nur `index`: nichts angefasst. Fall 2 `index` + `index.rebuild`: das halbe Ziel bleibt stehen. Fall 3 nur `index.rebuild`: angehoben, ein danebenstehendes `index.retired` verworfen. Fall 4 nur `index.retired`: zurueckgeholt. Fall 5 `index.retired` neben `index`: verworfen. Jeder Zweig traegt im Code den Satz, warum diese Entscheidung und nicht die naheliegende andere.
- **Fall 2 mit seiner Begruendung im Code.** Die naheliegende Handlung waere, das halbe Zielverzeichnis zu verwerfen, und sie waere falsch: `_resume_cursor` liest die hoechste uebertragene `file_id` genau aus diesem Verzeichnis, also wuerde ein Verwerfen jedes committete Band des abgebrochenen Laufs wegwerfen. Getauscht wird aus dem Start heraus ebenfalls nicht, weil dieser Start nicht wissen kann, ob der Lauf durch war; das weiss nur `counts_match`, und gefragt wird sie vom Lauf.
- **Fall 3 mit dem einen Beweis aus einer Abwesenheit.** `index.rebuild` ist nicht allgemein vollstaendig (Fall 2 ist dasselbe Verzeichnis mitten im Fuellen). Vollstaendig ist es hier, weil `index` fehlt: diesen Namen entfernt nur `swap_in`, und `swap_in` steht ausschliesslich hinter einem `counts_match`, das True gesagt hat. Der Schluss steht ausgeschrieben im Docstring, weil er die einzige Stelle der Phase ist, an der eine Abwesenheit als Beleg dient.
- **Zehn neue Faelle im Test.** Je einer fuer die fuenf Zustaende mit dem Fall im Funktionsnamen, dazu der Halbtausch mit beiden Zusatzverzeichnissen gleichzeitig, der Folgetest auf die Wiederaufnahme, das leere Volume, der Logzeilentest und der statische Signatur- plus Koedertest.
- **Fall 1 ist byteweise belegt.** `_volume_fingerprint` liest je Datei den relativen Pfad, `st_mtime_ns` und den sha256 des Inhalts; die Liste ist vor und nach dem Lauf identisch. Eine Inhaltssumme allein haette ein Umschreiben mit gleichen Bytes durchgelassen, eine mtime allein ein Kommen und Gehen.
- **Die Wiederaufnahme ist gemessen, nicht behauptet.** Nach Fall 2 steht der Cursor vor und nach dem Aufraeumen auf `file_id = 2`, und der anschliessende Bandlauf schreibt genau die vier fehlenden Dokumente (`documents_written == 4`, `complete is True`), traegt also die zwei bereits uebertragenen kein zweites Mal.
- **Keine Zeile nennt einen Pfad.** Der caplog-Test faehrt alle vier sprechenden Zweige hintereinander in einem Volume, prueft die vier Antworten in der Reihenfolge und liest jede der vier Zeilen auf Volumename, absoluten Pfad und beide Schraegstriche (T-18-08-04).
- **Doku.** `docs/uninstall.md` bekommt in Abschnitt 2 den Unterabschnitt "Drei Verzeichnisnamen im Volume, und keiner davon muss von Hand weg": eine Tabelle mit `index`, `index.rebuild` und `index.retired`, der Satz, dass der Container beim Start selbst aufraeumt, und die Handreichung fuer den Admin, der doch von Hand loeschen will (ein `index.rebuild` darf weg, ein `index.retired` nur, wenn ein `index` daneben liegt).
- **Ratsche bewegt.** `PACKAGE_FILES_TODAY` bleibt 56 (`docs/` liegt ausserhalb des Musters), `PACKAGE_TREE_HASH_TODAY = 4fe79081...`, Kommentarkette um den vierundzwanzigsten Absatz erweitert, der `index/rebuild.py` und den Aufraeumpfad nennt.
- Volle Suite **2679 passed / 15 skipped**, alle vier Gates gruen.

## Task Commits

1. **Task 1 RED: fuenf Zustaende des Volumes beim Start, ein Fall je Zustand** - `f902c7e` (test)
2. **Task 1 GREEN: recover_the_index_directories, fuenf Zustaende und fuenf Entscheidungen** - `a709634` (feat)
3. **Task 2: die drei Verzeichnisnamen in der Doku und die Ratsche dahinter** - `baa4365` (docs)

## Files Created/Modified

- `backend/src/findling/index/rebuild.py` (486 auf 624 Zeilen) - `REBUILD_SUFFIX`, die fuenf Antwortkonstanten, `recover_the_index_directories()`; im Modulkopf ein neuer Absatz ("A volume is read before it is used"), und der Satz in `swap_in`, der auf den Aufraeumpfad statt auf "Plan 18-08" verweist.
- `backend/tests/test_index_rebuild.py` (767 auf 1045 Zeilen) - Abschnitt "the clean up path at the start, five states of one volume" mit zehn Faellen und den zwei Helfern `_volume_fingerprint` und `_only_the_live_directory_is_left`.
- `backend/tests/test_measurement_scripts.py` - vierundzwanzigster Absatz der Kommentarkette, neuer Baumhash bei unveraenderten 56 Dateien.
- `docs/uninstall.md` (+33 Zeilen) - neuer Unterabschnitt in Abschnitt 2, vor "Zwei Instanzen an einem Docker-Dienst teilen das Volume".

## Decisions Made

- **Der gewoehnliche Start schweigt.** Der Plan verlangt "je Zweig eine Logzeile auf `warning`". Umgesetzt fuer die vier Zweige, die nach einem harten Abbruch erscheinen; Fall 1 und das leere Volume loggen auf `debug`. Begruendung im Code: eine Warnung, die bei jedem Containerstart erscheint, ist keine Warnung mehr, und der Wert dieser Zeilen liegt gerade darin, dass sie im Betrieb nie auftauchen. Die Akzeptanzkriterien des Plans fordern fuer Fall 1 keine Zeile.
- **Fall 3 schliesst den Tausch ab statt nur die Umbenennung nachzuholen.** Das Anheben des Ziels ist die zweite Umbenennung, das Verwerfen eines danebenstehenden `index.retired` der Schritt dahinter. Ohne das haette der Halbtausch-Fall ein Abfallverzeichnis hinterlassen, und das Akzeptanzkriterium "nach den Faellen 3, 4 und 5 existiert genau ein Verzeichnis `index`" waere fuer den Halbtausch nicht erfuellt.
- **Reihenfolge der Zweige: erst `index` da oder nicht, dann die Nachbarn.** Stehen bei fehlendem `index` beide Zusatzverzeichnisse, gewinnt `index.rebuild`, weil das genau der Zustand zwischen erster und zweiter Umbenennung ist und das Ziel dort das vollstaendige neuere Verzeichnis ist.
- **Ein sechster Zustand ist benannt und bekommt keine sechste Antwort.** Ein Volume ohne jedes Indexverzeichnis ist der Erststart; `open_index` legt das Verzeichnis Sekundenbruchteile spaeter an. Er teilt sich die Antwort mit Fall 1, und ein eigener Name haette eine Entscheidung vorgetaeuscht, die es nicht gibt.

## Deviations from Plan

### Auto-fixed Issues

Keine. Der Plan lief wie geschrieben; die einzige bewusste Abweichung ist die Logstufe von Fall 1 (siehe "Decisions Made", erster Punkt) und der zusaetzliche sechste Testfall fuer das leere Volume, der ohne den Plan zu verletzen die Luecke schliesst, die diese Entscheidung aufmacht.

## Was dieser Plan ausdruecklich nicht tut

- **Kein Aufrufer.** `recover_the_index_directories()` hat seine Aufrufer im Test; die Stelle im Startpfad des Containers (`main.py`, vor dem ersten `open_index`) setzt der Umbau-Orchestrierer von Plan 18-09.
- **Kein Anfassen von `_raise_generation_for_lost_index`.** Der umgekehrte Fall (leerer Index neben voller Zustandsdatenbank) bleibt unveraendert in `worker/poller.py`; er beantwortet eine andere Frage und wird von hier nicht gerufen.
- **Keine Pruefung, ob ein vollstaendiges Verzeichnis inhaltlich stimmt.** Der Aufraeumpfad entscheidet ueber Namen und Vorhandensein, nicht ueber Dokumentzahlen; die inhaltliche Endprobe ist und bleibt `counts_match` im Lauf.

## Threat-Dispositionen

| Threat ID | Umsetzung |
|---|---|
| T-18-08-01 | Fall 3 hebt das vollstaendige Ziel an die Livestelle, Fall 4 holt den stillgelegten Bestand zurueck; je ein Test zaehlt danach die Dokumente im Liveverzeichnis (8 bzw. 3) |
| T-18-08-02 | Fall 2 laesst `index.rebuild` stehen; der Folgetest zeigt Cursor 2 vor und nach dem Aufraeumen und `documents_written == 4` im anschliessenden Bandlauf |
| T-18-08-03 | Kein Parameter (per `inspect.signature` belegt), alle drei Namen per `with_name` aus `settings().index_dir`; ein Koederverzeichnis eine Ebene ueber dem Volume steht nach dem Lauf unberuehrt da |
| T-18-08-04 | Vier Zweige, vier Zeilen, alle vier im caplog-Test gelesen: kein Volumename, kein absoluter Pfad, kein Schraegstrich |
| T-18-08-SC | Kein Paket installiert; `shutil` und `pathlib` sind stdlib |

## Verification

- `uv run pytest -q` - 2679 passed, 15 skipped
- `uv run pytest -q tests/test_index_rebuild.py` - 40 passed
- `uv run pytest -q tests/test_measurement_scripts.py` - 376 passed
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 133 files already formatted
- `uv run pyright` - 0 errors, 0 warnings, 0 informations
- `uv run vulture` - keine Meldung
- `grep -c "index.rebuild" docs/uninstall.md` - 3
- `40b-baumhash.py backend/src/findling "**/*.py"` - `dateien: 56`, `baumhash: 4fe79081564ce5d69f2e45a4dcca5fd53e1d693004a5f4b477caf84df51b2b9d`
- must_haves: `recover` dreimal in `rebuild.py`, `with_name(` dreimal in `rebuild.py`, RED-Lauf vor dem GREEN-Commit belegt (ImportError auf die fuenf neuen Namen)
- Keine Em-Dashes in `docs/uninstall.md` (per Zeichenpruefung auf U+2014 und U+2013)

## Known Stubs

Keine. Die Funktion ist vollstaendig und getestet; ihr Produktiv-Aufrufer ist in Plan 18-09 benannt, wie schon bei `swap_in` und `stamp_after_swap` aus 18-07.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans: kein Netzpfad, keine Route, kein Schema, keine neue Vertrauensgrenze. Der einzige neue Dateizugriff ist ein `rename` und ein `rmtree` auf Pfaden, die die Funktion selbst aus `settings().index_dir` ableitet.

## Self-Check: PASSED

- `backend/src/findling/index/rebuild.py` vorhanden (624 Zeilen), enthaelt `def recover_the_index_directories`
- `backend/tests/test_index_rebuild.py` vorhanden (1045 Zeilen), enthaelt die zehn neuen Faelle
- `docs/uninstall.md` vorhanden, nennt `index`, `index.rebuild` und `index.retired`
- Commits `f902c7e`, `a709634`, `baa4365` im Log gefunden
- Arbeitsbaum nach dem letzten Task-Commit sauber, keine untracked Dateien
