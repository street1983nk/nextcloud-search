---
phase: 15-messphase-eine-box-anfahrt
plan: 01
subsystem: testing
tags: [measurement, runbook, sha256, pytest, parametrize, box-anfahrt, copy-watchman]

# Dependency graph
requires:
  - phase: 10-messbox
    provides: das Laufverzeichnis 2026-09-vergleichsmessung-m7g mit den elf Originalwerkzeugen
  - phase: 12-messwerkzeug-runbook-terminentscheid
    provides: das Laufverzeichnis 2026-09-v12-messung, NARROW_SCOPE_DIRS, 73-bestand-sonde.py und 97-cron-vorpruefung.sh
  - phase: 11-werkzeugfixe
    provides: DRIVEN_FASSUNG_RULE und das Muster byteweiser Waechter mit Mutationsprobe
provides:
  - elf byteweise uebernommene Messwerkzeuge in docs/measurements/2026-09-v12-messung/skripte/
  - COPIED_TOOLS als benannte Liste der uebernommenen Werkzeuge
  - TOOLS_THE_MEASUREMENT_ORDER_NAMES als Vollstaendigkeitspruefung der Messreihenfolge
  - dreizehn neue Faelle in backend/tests/test_measurement_scripts.py
affects: [15-02-runbook, 15-03-wiederaufwaermen, 15-04-grundlast-rueckkehr, 15-06-abbildwechsel, 15-07-ablauf, 15-09-anfahrt, 15-15-bericht]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Kopie-Waechter: sha256 der Kopie gegen sha256 des Originals, statt gegen eine dritte aufgeschriebene Zahl"
    - "Vollstaendigkeitsliste der Messreihenfolge als Gate, damit ein fehlendes Werkzeug vor der Box auffaellt und nicht auf ihr"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/40b-baumhash.py
    - docs/measurements/2026-09-v12-messung/skripte/40b-baumhash.sh
    - docs/measurements/2026-09-v12-messung/skripte/90-bestand.sh
    - docs/measurements/2026-09-v12-messung/skripte/91-korpus.sh
    - docs/measurements/2026-09-v12-messung/skripte/93-nullstand.sh
    - docs/measurements/2026-09-v12-messung/skripte/95-spitze.sh
    - docs/measurements/2026-09-v12-messung/skripte/96-volllauf.sh
    - docs/measurements/2026-09-v12-messung/skripte/96b-waechter.sh
    - docs/measurements/2026-09-v12-messung/skripte/96c-lesen.py
    - docs/measurements/2026-09-v12-messung/skripte/96d-statusbeobachter.py
    - docs/measurements/2026-09-v12-messung/skripte/97-nebenlaeufigkeit.sh
  modified:
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Eine Kopie traegt den Dateimodus ihres Originals mit: vier Werkzeuge liegen mit 100755 im Index, sieben mit 100644, wie im Quellverzeichnis; damit stimmen Blobkennung UND Modus ueberein"
  - "Der Kopie-Waechter vergleicht Kopie gegen Original statt gegen eine aufgeschriebene Pruefsumme, weil hier genau die Gleichheit der beiden Dateien die Zusage ist und eine dritte Zahl eine weitere driftende Stelle waere"
  - "Neben dem Pruefsummenfall haelt ein zweiter Fall die vollstaendige Werkzeugliste der Messreihenfolge; die Werkzeuge aus 15-03 bis 15-06 stehen bewusst nicht darin"
  - "NARROW_SCOPE_DIRS bleibt bei drei Laufverzeichnissen, es wird kein viertes angelegt (Annahme A6 der Recherche)"

patterns-established:
  - "Kopieren heisst kopieren: die Gleichheit von Kopie und Original ist an git ls-files -s ablesbar, nicht nur an einer Pruefsumme im Test"
  - "Ein Werkzeug, das die Messreihenfolge nennt und das Laufverzeichnis nicht traegt, faellt an einem Gate auf und nicht auf einer bezahlten Box"

requirements-completed: [MESS-05]

# Metrics
duration: 20 min
completed: 2026-09-19
---

# Phase 15 Plan 01: Elf Werkzeuge byteweise uebernehmen, Kopie-Waechter Summary

**Elf Messwerkzeuge aus dem v1.1-Laufverzeichnis liegen byteidentisch im Laufverzeichnis der Anfahrt, und ein parametrisierter sha256-Waechter samt Mutationsprobe und Vollstaendigkeitsliste haelt fest, dass keines beim Kopieren angefasst wurde.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-19T19:45:00Z
- **Completed:** 2026-09-19T20:05:00Z
- **Tasks:** 2 von 2
- **Files modified:** 12 (11 neu, 1 geaendert)

## Accomplishments

- Die Messreihenfolge des Runbooks (Abschnitt 7, neun Bloecke) hat fuer jeden ihrer Bloecke ein Werkzeug im Laufverzeichnis `docs/measurements/2026-09-v12-messung/skripte/`. Vorher lagen dort drei Dateien, jetzt vierzehn.
- Die elf Kopien tragen im Git-Index dieselbe Blobkennung wie ihre Originale. Das ist die staerkste verfuegbare Form des Belegs: gleiche Blobkennung heisst gleiche Bytes, und sie ist ohne Testlauf mit `git ls-files -s` nachlesbar.
- `COPIED_TOOLS` und ein parametrisierter Fall halten die Byteidentitaet als Gate, mit `DRIVEN_FASSUNG_RULE` als Diagnose. Elf Faelle, einer je Werkzeug, benannt nach dem Dateinamen.
- Die Mutationsprobe zeigt die Schaerfe des Waechters an einer gestellten Probe: ein einziges zusaetzliches Leerzeichen und ein `set -eu` zu `set -e` machen ihn rot.
- `TOOLS_THE_MEASUREMENT_ORDER_NAMES` prueft die Vollstaendigkeit ueber alle vierzehn Werkzeuge der Messreihenfolge. Ein spaeter vergessenes Werkzeug faellt damit vor der Anfahrt auf und nicht auf der bezahlten Box.
- Die fuenf Gate-Familien des engen Bereichs (`shebang`, `carriage_return`, `dash`, `path_of_one_machine`, `password_on_a_command_line`) sammeln die elf neuen Pfade automatisch ein, weil `NARROW_SCOPE_DIRS` das v12-Verzeichnis bereits fuehrt. Das sind 55 zusaetzliche Faelle ohne eine einzige neue Zeile Konfiguration.

## Task Commits

Each task was committed atomically:

1. **Task 1: Elf Werkzeuge byteweise uebernehmen** - `75460b4` (feat)
2. **Task 2: Der Kopie-Waechter** - `5e1ace3` (test)

**Plan metadata:** siehe den docs-Commit dieses Plans

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/40b-baumhash.py` - Rezept des Baumhashes, wird beim Abbildwechsel gebraucht
- `docs/measurements/2026-09-v12-messung/skripte/40b-baumhash.sh` - der Beweisteil des Baumhashes
- `docs/measurements/2026-09-v12-messung/skripte/90-bestand.sh` - Endmessung des Bestands (Schritt 9)
- `docs/measurements/2026-09-v12-messung/skripte/91-korpus.sh` - Korpusseite der Endmessung
- `docs/measurements/2026-09-v12-messung/skripte/93-nullstand.sh` - Nullstandsbeleg (Schritt 1)
- `docs/measurements/2026-09-v12-messung/skripte/95-spitze.sh` - die Spitze, Muster fuer Schritt 6
- `docs/measurements/2026-09-v12-messung/skripte/96-volllauf.sh` - Anstoss des Volllaufs (Schritt 4)
- `docs/measurements/2026-09-v12-messung/skripte/96b-waechter.sh` - der Beobachter neben dem Volllauf
- `docs/measurements/2026-09-v12-messung/skripte/96c-lesen.py` - der Leser, den der Beobachter entscheidet
- `docs/measurements/2026-09-v12-messung/skripte/96d-statusbeobachter.py` - die Aufzeichnung alle 120 s
- `docs/measurements/2026-09-v12-messung/skripte/97-nebenlaeufigkeit.sh` - die fuenf Laststufen (Schritt 6)
- `backend/tests/test_measurement_scripts.py` - `COPIED_TOOLS`, `TOOLS_THE_MEASUREMENT_ORDER_NAMES` und drei Faelle (13 Testfaelle)

## Decisions Made

- **Der Dateimodus reist mit.** Im Quellverzeichnis liegen vier der elf Werkzeuge mit `100755` im Index (`96-volllauf.sh`, `96b-waechter.sh`, `96c-lesen.py`, `96d-statusbeobachter.py`), die uebrigen sieben mit `100644`. Die Kopien tragen denselben Modus. `core.fileMode` steht in diesem Repo auf `false`, also haette `git add` sonst alle elf auf `100644` gesetzt und die Kopie waere in einer Eigenschaft vom Original abgewichen, die auf der Box sichtbar wird. Auf der Platte tragen alle elf das Ausfuehrungsbit, wie der Plan es verlangt.
- **Der Waechter vergleicht zwei Dateien, nicht eine Datei gegen eine Zahl.** Die bestehenden Waechter (`DRIVEN_LANGUAGE_CASES_SHA256`, `SUCCESSOR_LANGUAGE_CASES_SHA256`) schreiben die Pruefsumme auf, weil sie eine gefahrene Fassung gegen ihre eigene Vergangenheit halten. Hier ist die Zusage eine andere: Kopie und Original sollen ein und dieselbe Datei sein. Eine dritte aufgeschriebene Zahl waere eine weitere Stelle, die driften kann, ohne dass die Zusage dadurch schaerfer wuerde. Beide Seiten werden vorher auf Existenz geprueft, damit ein geloeschtes Original nicht als gruen durchgeht.
- **Die Vollstaendigkeitsliste nennt vierzehn Namen und keine kuenftigen.** `95b-wiederaufwaermen`, `94b-grundlast-rueckkehr.sh`, `99c-filter-sortierung.sh` und `92b-wechsel.sh` entstehen in 15-03 bis 15-06 und kommen mit ihren eigenen Plaenen in die Liste. Eine Liste, die sie heute nennt, waere rot aus einem Grund, der kein Befund ist.
- **`NARROW_SCOPE_DIRS` bleibt unveraendert.** Gemessen wird in `2026-09-v12-messung`, ein viertes Laufverzeichnis entsteht nicht (Annahme A6 der Recherche). `test_the_narrow_scope_covers_the_three_run_directories_written_under_these_rules` ist unberuehrt und weiter gruen.

## Deviations from Plan

None - plan executed exactly as written.

Der Dateimodus-Entscheid oben ist keine Abweichung, sondern die Umsetzung des Plansatzes "Kopieren heisst kopieren" und "Das Ausfuehrungsbit der neun Skripte bleibt gesetzt" unter einem Repo mit `core.fileMode=false`.

## Issues Encountered

None.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | Elf Kopien vorhanden, je sha256-gleich mit dem Original | GRUEN, elf von elf; zusaetzlich gleiche Blobkennung im Index |
| 2 | Quellverzeichnis `2026-09-vergleichsmessung-m7g/` unveraendert | GRUEN, `git status --porcelain` darauf ist leer |
| 3 | Volle Suite aus `backend/` gruen, Skipzahl unveraendert | GRUEN, 2330 bestanden, **15 uebersprungen** (unveraendert gegen 14-12) |
| 4 | Kein Em-Dash und kein Emoji in den geaenderten Dateien | GRUEN, Pruefung ueber alle zwoelf Dateien ohne Befund |
| 5 | `-k "byte_identical_to_their_original"` waehlt elf Faelle | GRUEN, 11 bestanden, 287 abgewaehlt |
| 6 | Kein `__pycache__`, keine `.claude-active` im Zielverzeichnis | GRUEN |
| 7 | `ruff check`, `ruff format --check`, `pyright`, `vulture` | GRUEN, alle vier ohne Befund |

Zur Skipzahl: 2262 bestanden im Stand 14-12, plus 55 Faelle der fuenf engen Gate-Familien ueber die elf neuen Pfade, plus 13 neue Faelle dieses Plans ergibt 2330. Die Rechnung geht ohne Rest auf, es ist also kein Fall stillschweigend verschwunden.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 15-02 kann anschliessen: das Runbook bekommt den neu gerechneten Deckel, den Abbildwechsel-Block 13b, `drop_caches` und die Schritte 6b und 8b. Die Werkzeuge, auf die es dabei zeigt, liegen jetzt alle im Laufverzeichnis.
- 15-03 bis 15-06 bauen ihre Nachfolgefassungen neben den hier kopierten Mustern (`94-grundlast.sh`, `92-wechsel.sh`, `99-seitenroute.sh`, `99b-runden.sh` bleiben bewusst im Quellverzeichnis). Wenn dabei ein Werkzeug in `TOOLS_THE_MEASUREMENT_ORDER_NAMES` aufgenommen wird, gehoert das in denselben Commit wie die Datei.
- Der Owner-Checkpoint 15-08 (Deckelfreigabe) ist von diesem Plan nicht beruehrt und steht weiter vor Welle C.

## Self-Check: PASSED

- Alle elf Kopien auf der Platte gefunden, je sha256-gleich mit dem Original.
- `backend/tests/test_measurement_scripts.py` traegt `COPIED_TOOLS` mit elf Eintraegen.
- Beide Task-Commits liegen in der Historie: `75460b4`, `5e1ace3`.
- Keine Loeschung in beiden Commits (`git diff --diff-filter=D` leer).

---
*Phase: 15-messphase-eine-box-anfahrt*
*Completed: 2026-09-19*
