---
phase: 02-indexkern-und-volltextsuche
plan: 01
subsystem: search
tags: [tantivy, german, compound-splitting, snowball, wngerman, config, tdd]

requires:
  - phase: 01-walking-skeleton
    provides: findling package layout, read-only gate, five Python quality gates, uv project
provides:
  - Nine pinned extraction and index packages (tantivy, pypdfium2, pypdf, python-docx, python-pptx, openpyxl, striprtf, charset-normalizer, lxml)
  - findling/config.py as the single home of every cap, path and version of the phase
  - findling/index/wordlist.py, recipe A over /usr/share/dict/ngerman with SHA-256 artifact
  - findling/index/analyzer.py, the de/en/name chains, ANALYZER_VERSION and the per process automaton
  - scripts/dev/measure_wordlist.sh, reproducible measurement in a throwaway Debian container
  - docs/german-analyzer.md, measured numbers, licence obligations, three known limits
affects: [02-06 schema, 02-07 image and third party licences, 02-09 query rewrite, 02-05 extraction sandbox, 02-13 memory protocol]

tech-stack:
  added: [tantivy==0.26.0, pypdfium2==5.13.0, pypdf==6.16.1, python-docx==1.2.0, python-pptx==1.0.2, openpyxl==3.1.5, striprtf==0.0.32, charset-normalizer==3.5.1, lxml==6.1.1]
  patterns:
    - "One module owns every cap; nothing else writes a literal for a limit"
    - "Unusable environment values fall back to the default and warn by name, never raise"
    - "The word list is a build artifact with a digest, not a runtime decision"
    - "Expensive automata are per process singletons with a testable build counter"
    - "Test tables assert WHAT is produced, measured against the real data in the shipping image"

key-files:
  created:
    - backend/src/findling/config.py
    - backend/src/findling/index/__init__.py
    - backend/src/findling/index/wordlist.py
    - backend/src/findling/index/analyzer.py
    - backend/tests/test_config.py
    - backend/tests/test_wordlist.py
    - backend/tests/test_analyzer.py
    - backend/tests/fixtures/constituents_de.txt
    - scripts/dev/measure_wordlist.sh
    - docs/german-analyzer.md
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/tests/test_readonly_gate.py

key-decisions:
  - "Recipe A encoded and recipe B refuted in the module docstring, so a later simplification has to argue against a measurement"
  - "Linking elements live in load_constituents, not in the analyzer call, so the artifact and its digest are self contained"
  - "The German test table runs from a 172 entry fixture proven token identical to the full 276496 entry Debian list, so it never skips itself"
  - "The read-only gate gained a reviewed per module exception for one mkdir instead of being weakened globally"
  - "Two memory numbers are reported because only the one after the list is freed matters, and it is an upper bound"

patterns-established:
  - "Pattern: caps and versions in one frozen, cached Settings object; environment reading never raises"
  - "Pattern: build artifact plus digest under APP_PERSISTENT_STORAGE, fail closed on a digest mismatch"
  - "Pattern: measurement modes print numbers only, never tokens or words (T-02-14)"
  - "Pattern: expensive per process resources expose a build counter so the singleton is testable"

requirements-completed: [SRCH-01, IDX-06]

duration: 55min
completed: 2026-08-31
---

# Phase 02 Plan 01: Analysefundament Summary

**Die deutsche Analysekette liefert die gemessenen Tokens gegen die echte Debian-Wortliste, das 63-Zeichen-Kompositum zerfaellt in sechs Teile statt zu verschwinden, und der Kompositaautomat wird je Prozess genau einmal gebaut.**

## Performance

- **Duration:** ca. 55 min
- **Started:** 2026-08-31T18:49Z
- **Completed:** 2026-08-31T19:45Z
- **Tasks:** 3 von 3
- **Files modified:** 13 (10 neu, 3 geaendert)

## Accomplishments

- Neun Pakete gepinnt und importierbar, Legitimitaets-Audit aus dem RESEARCH uebernommen (9 von 9 OK), keine Zusatzabhaengigkeit.
- `config.py` haelt siebzehn Deckel, vier Pfade, zwei Versionen und `INDEX_WORKERS = 1` an genau einer Stelle, jeder Wert mit Begruendung. Ein unbrauchbarer Umgebungswert faellt auf den Vorgabewert zurueck und loggt nur den Variablennamen, nie den Wert.
- Rezept A reproduziert die Zahlen des RESEARCH exakt: 356.010 Quellzeilen, 276.496 Eintraege (full) beziehungsweise 86.345 (nouns), gemessen im Image, auf dem die App ausgeliefert wird.
- Die deutsche Kette liefert alle sechzehn gemessenen Kompositum-Ergebnisse, die zehn Allerweltswoerter bleiben ungeteilt, die Stoppwortzeile ergibt die leere Liste, und kein blankes Fugen-`s` erreicht den Index.
- Der Automat wird je Prozess einmal gebaut, belegt durch `test_analyzer_is_built_once` ueber einen echten Bauzaehler.

## Task Commits

1. **Task 1: Abhaengigkeiten pinnen und alle Deckel in ein Konfigurationsmodul ziehen**
   - RED `abbec2c` (test), GREEN `85cfeb1` (feat)
2. **Task 2: Wortliste nach Rezept A, mit Hash und nachgemessenen Zahlen**
   - RED `2f0dd86` (test), GREEN `4048e75` (feat)
3. **Task 3: Die drei Analyseketten, ihre Testtabelle und der einmalige Automatenbau**
   - RED `a5b58e1` (test), GREEN `06ffbf2` (feat)

## TDD Gate Compliance

Alle drei Aufgaben sind mit `tdd="true"` geplant und wurden in der Reihenfolge RED, GREEN ausgefuehrt. Jeder RED-Commit wurde gegen ein tatsaechlich rotes Testergebnis erzeugt (`ModuleNotFoundError` beziehungsweise `ImportError` beim Sammeln). Ein REFACTOR-Schritt war in keiner Aufgabe noetig; die Ketten und die Konfiguration entstanden bereits in ihrer Endform, und ein leerer Refactor-Commit haette keine Aussage getragen.

## Files Created/Modified

- `backend/src/findling/config.py` - Alle Deckel, Pfade und Versionen der Phase an einer Stelle, plus die tolerante Zahlenlesung.
- `backend/src/findling/index/__init__.py` - Haelt fest, warum der Extraktions-Kindprozess dieses Paket nicht importieren darf.
- `backend/src/findling/index/wordlist.py` - Rezept A, Fugenelemente, SHA-256, Build-Artefakt unter `dict/de.txt`, Messmodus fuer die Liste.
- `backend/src/findling/index/analyzer.py` - Die drei Ketten, `ANALYZER_VERSION`, der Prozess-Singleton mit Bauzaehler, Messmodus fuer den Automaten.
- `backend/tests/test_config.py` - 25 Tests: Vorgabewerte, Pfadableitung, Sprachliste, Wortlistenvariante, Konstantencharakter von `INDEX_WORKERS`, Rueckfall bei Unsinn.
- `backend/tests/test_wordlist.py` - 16 Tests: Fenster, Fugen, Umlauterhalt, Sortierung, Hashstabilitaet, Artefakt-Wiederverwendung, manipuliertes Artefakt.
- `backend/tests/test_analyzer.py` - 41 Testfaelle: sechzehn Komposita, zehn ungeteilte Woerter, Rindfleisch-Fall, Stoppwoerter, Nominalflexion, D2, D3, englische und Namenskette, Einmalbau.
- `backend/tests/fixtures/constituents_de.txt` - 172 Eintraege aus der echten Debian-Liste, nachweislich tokenidentisch fuer alle Testeingaben.
- `scripts/dev/measure_wordlist.sh` - Messung im Wegwerf-Container, `full` und `nouns`.
- `docs/german-analyzer.md` - 191 Zeilen: Rezepttabelle, eigene Messzahlen, Filterreihenfolge, 16-Komposita-Tabelle, Lizenzblock, Memory, Known limits.
- `backend/pyproject.toml`, `backend/uv.lock` - Die neun Pakete, exakt gepinnt.
- `backend/tests/test_readonly_gate.py` - Eine geprueft eng geschnittene Ausnahme fuer genau ein `mkdir`.

## Eigene Messzahlen

`scripts/dev/measure_wordlist.sh` in `python:3.13-slim-trixie`:

| Zahl | `full` | `nouns` |
|---|---|---|
| Quellzeilen `/usr/share/dict/ngerman` | 356010 | 356010 |
| Eintraege nach der Filterung | 276496 | 86345 |
| SHA-256 | `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` | `03c2b9b548d3be7374dccd2d704ca9b42d7db1a666de8fc9937d10f142a858c3` |
| Filterzeit | 0,251 s | 0,118 s |
| Bauzeit des Automaten | 0,327 s | 0,136 s |
| Dauerhaftes RSS des Prozesses | 43.454.464 B | 7.651.328 B |
| Durchsatz | 1.781.918 Token/s | 1.952.990 Token/s |
| Automatenbauten je Prozess | 1 | 1 |

Eintragszahlen, Quellumfang und alle Zerlegungsergebnisse decken sich exakt mit dem RESEARCH. Die Bauzeit liegt unter den dort gemessenen 0,44 s, der Durchsatz leicht unter den 2,3 Mio. Token/s: Maschinenrauschen, kein Befund, der eine Entscheidung aendert. Vierzehn von sechzehn Komposita sind ueber ein Teilwort findbar, null Fehlzerlegungen.

Die RSS-Zahl ist bewusst eine Obergrenze und nicht die im RESEARCH genannten rund 23 MB: glibc gibt freigegebene Arenen nicht an das Betriebssystem zurueck, die transiente Python-Liste zaehlt also mit. Die Aussage fuer das RAM-Budget ist dieselbe, und Plan 02-13 protokolliert die Zahl noch einmal am laufenden Image.

## Decisions Made

- **Fugenelemente gehoeren in `load_constituents`, nicht in den Analyzer-Aufruf.** Der RESEARCH-Codeausschnitt haengt sie erst beim Bau an. Im Plan steht dagegen, dass sie Eintraege der Liste sind, und nur so deckt der SHA-256 auch sie ab und `dict/de.txt` ist vollstaendig das, was der Splitter sieht. Doppeltes Anhaengen ist damit strukturell ausgeschlossen.
- **Zwei Messmodi statt einem.** `wordlist.measure()` ruehrt den Analyzer nicht an, `analyzer.measure()` misst den Automaten. Damit bleibt die Zusage aus `index/__init__.py` wahr, dass `wordlist` niemanden den Automaten kosten kann, und das Skript ruft schlicht beide Module.
- **Der Cache haelt hoechstens einen Automaten.** Geschluesselt auf den Wortlisten-Hash; eine geaenderte Liste ersetzt den alten Automaten, statt einen zweiten daneben zu legen.
- **Zwei Speicherzahlen werden berichtet.** Nur die nach dem Freigeben der Liste ist die interessante, und sie wird ausdruecklich als Obergrenze ausgewiesen, statt eine saubere Zahl vorzutaeuschen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Nur-Lesen-Wache verbot das einzige noetige `mkdir`**

- **Found during:** Task 2 (Wortliste)
- **Issue:** `test_readonly_gate.py` verbietet die Bezeichner `mkdir` und `makedirs` in jedem Modul des Pakets, weil `nc_py_api.files` sie als Schreiboperationen fuehrt. `build_artifact` muss aber `$APP_PERSISTENT_STORAGE/dict/` anlegen. Ohne Aenderung war die Aufgabe nicht abschliessbar, und die Wache selbst benennt diesen Fall in ihrem Docstring ausdruecklich als geplante Erweiterung.
- **Fix:** `INVARIANT_2_EXCEPTIONS` als Menge von (Modul, Bezeichner)-Paaren, aktuell genau ein Eintrag: `("index/wordlist.py", "mkdir")`. Global waere `mkdir` weiterhin ein Verstoss. Dazu drei neue Selbsttests: die Ausnahme greift im genannten Modul, sie greift nicht ein Modul weiter, und sie deckt nur den genannten Bezeichner ab (`target.delete()` bleibt im selben Modul ein Verstoss).
- **Files modified:** `backend/tests/test_readonly_gate.py`
- **Verification:** `uv run pytest tests/test_readonly_gate.py -q` gruen, 16 statt 13 Tests.
- **Committed in:** `4048e75`

**2. [Rule 3 - Blocking] Die Analyzer-Tests brauchten eine Wortliste, die es auf keiner Entwicklermaschine gibt**

- **Found during:** Task 3 (Analyseketten)
- **Issue:** Die Testtabelle soll pruefen, WAS zerlegt wird. Die gemessenen Tokens entstehen aus der 276.496 Eintraege grossen Debian-Liste, und `/usr/share/dict/ngerman` existiert weder unter Windows noch in einem gewoehnlichen CI-Runner. Ein Test, der sich bei fehlender Liste selbst ueberspringt, ist genau die Beruhigung, vor der Pitfall 1 warnt.
- **Fix:** `backend/tests/fixtures/constituents_de.txt`, 172 Eintraege. Erzeugt im Container als Teilmenge der echten Liste: alle Eintraege, die als Teilzeichenkette in einer Testeingabe vorkommen. Da der Splitter leftmost-longest nur Teilzeichenketten der Eingabe treffen kann, ist die Teilmenge fuer genau diese Eingaben aequivalent. Der Generator hat das gegengeprueft: null Abweichungen zwischen voller Liste und Fixture ueber alle 41 Eingaben.
- **Files modified:** `backend/tests/fixtures/constituents_de.txt`, `backend/tests/test_analyzer.py`
- **Verification:** Container-Lauf mit `mismatches: []`; `uv run pytest tests/test_analyzer.py -q` gruen mit 41 Faellen.
- **Committed in:** `a5b58e1`

**3. [Rule 3 - Blocking] `.gitignore` verschluckte das Testfixture**

- **Found during:** Task 3
- **Issue:** Das Fixture lag zunaechst unter `backend/tests/data/`. `.gitignore` ignoriert `data/` fuer die Nextcloud-Laufzeitdaten, das Fixture waere also nie im Repository gelandet und die Tests waeren beim naechsten Checkout rot geworden.
- **Fix:** Verzeichnis nach `backend/tests/fixtures/` umbenannt, statt die Ignore-Regel aufzuweichen.
- **Files modified:** `backend/tests/test_analyzer.py`
- **Verification:** `git add` ohne `-f` erfolgreich, Datei im Commit enthalten.
- **Committed in:** `a5b58e1`

### Abweichungen in der Aufgabenzuordnung

- Das Abnahmekriterium von Task 2 verlangt Bauzeit und RSS-Zuwachs bereits in `docs/german-analyzer.md`. Beide Zahlen setzen den Analyzer voraus, der erst in Task 3 entsteht. Die Datei traegt nach Task 2 die gemessenen Listenzahlen und nach Task 3 die Automatenzahlen; im Endzustand des Plans ist das Kriterium vollstaendig erfuellt. Der Messlauf fuer die Listenzahlen lief in Task 2 als Einzelaufruf im Container, der committete Skriptlauf in Task 3 fuer beide Varianten.
- `backend/tests/fixtures/constituents_de.txt` und die drei zusaetzlichen Tests in `test_readonly_gate.py` stehen nicht in `files_modified` des Plans. Beide sind Folge der Deviations 1 bis 3.

---

**Total deviations:** 3 auto-fixed (3x Rule 3 - Blocking)
**Impact on plan:** Alle drei waren zum Abschluss der jeweiligen Aufgabe zwingend. Kein Scope Creep: die Wache wurde eng erweitert statt aufgeweicht, das Fixture ist nachweislich aequivalent zur echten Liste, und die Umbenennung beruehrt nur einen Pfad.

## Issues Encountered

- **Ruff sortierte den Import des noch nicht existierenden Moduls falsch ein.** Solange `src/findling/config.py` fehlte, hielt ruffs isort `findling.config` fuer Drittanbietercode und verlangte einen anderen Importblock. Mit der Datei loeste sich das von selbst. Kein Eingriff noetig, nur eine kurze Verwirrung im RED-Schritt.
- **`# noqa` fuer nicht aktivierte Regeln ist selbst ein Lint-Fehler.** `ANN`, `PLW0603` und `T201` stehen nicht im Regelsatz des Projekts, also schlug `RUF100` (unbenutztes noqa) zu. Geloest, indem die Anmerkungen entfernt und stattdessen echte Typannotationen ergaenzt wurden.
- **Kein CI-Lauf moeglich.** Die Gates wurden lokal ausgefuehrt (`pytest`, `ruff check`, `ruff format --check`, `pyright`, `vulture`), alle fuenf gruen bei 134 Tests. Der GitHub-Actions-Lauf ist lokal nicht pruefbar und steht aus.

## User Setup Required

None - keine externe Konfiguration noetig. `scripts/dev/measure_wordlist.sh` braucht ein laufendes Docker; ohne Docker bricht es mit einer klaren Meldung ab, statt falsche Zahlen zu liefern.

## Next Phase Readiness

Bereit fuer die naechsten Plaene der Phase:

- **02-06 (Schema)** kann `TOKENIZER_DE`, `TOKENIZER_EN`, `TOKENIZER_NAME`, `SCHEMA_VERSION`, `INDEX_VERSION` und `ANALYZER_VERSION` direkt lesen; die Registrierung beim Oeffnen passt damit zu den im Schema gespeicherten Namen.
- **02-07 (Image)** muss `wngerman` im Laufzeitimage installieren und `THIRD-PARTY.md` mit dem GPL-2+-Block anlegen; `docs/german-analyzer.md` nennt die Pflichten bereits vollstaendig.
- **02-09 (Query)** hat mit D3 eine konkrete, getestete Aufgabe: Umlautvariante bilden und mit `Occur.Should` veroden.
- **02-05 (Extraktion)** hat die Auflage schwarz auf weiss: `findling.index` im Kindprozess nicht importieren.
- **02-13 (Memory)** protokolliert die RSS-Zahl am laufenden Image; die hier gemessene Obergrenze ist der Vergleichswert.

Kein Blocker.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
