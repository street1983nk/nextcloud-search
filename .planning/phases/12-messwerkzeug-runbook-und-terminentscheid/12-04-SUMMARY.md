---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 04
subsystem: measurement-tooling
tags: [tantivy, ranked-sides, messskript, pytest, github-actions, di-10-02]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "98b-sprachfaelle.sh, DRIVEN_FASSUNG_RULE und der enge Geltungsbereich der Messskript-Gates"
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "das Laufverzeichnis docs/measurements/2026-09-v12-messung/ aus Plan 12-03"
provides:
  - "73-bestand-sonde.py: ungedeckelter Indexbestand je Begriff, im Prozess des Containers gemessen"
  - "Fensterbelegung beider Ranglisten und Rang der eigenen Datei ueber ranked_sides, ohne zweiten Weg"
  - "V12_RUN_DIR und STOCK_PROBE im engen Geltungsbereich der Messskript-Gates"
  - "Waechter mit sha256 und Bytezahl ueber die zweite gefahrene Fassung 98b-sprachfaelle.sh"
  - "docs/measurements/** in beiden Pfadlisten von python.yml"
affects: [12-05-sprachfaelle-98c, 12-06-cron-vorpruefung, 15-messphase-eine-box-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messgroesse im Prozess erheben statt ueber eine Route, damit die Zahl keine Prozessgrenze ueberquert (T-02-93)"
    - "SearchResult.count als ungedeckelte Bestandszahl, unter docs/measurements/**/skripte/ ohne Typstub-Kosten"
    - "Eigene Kennungen ausschliesslich ueber die Umgebung (DATEI_IDS), nie ueber ein Argument"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py
  modified:
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/python.yml

key-decisions:
  - "Die Sonde laeuft im Container und fragt keine Route: die Zaehlung ueberquert keine Prozessgrenze, das Zaehl-Orakel aus T-02-93 entsteht gar nicht erst"
  - "Ein einziger Weg zu den beiden Ranglisten: ranked_sides, kein Nachbau; ein Nachbau beantwortet eine Suche, die dieser Container nie gefahren hat"
  - "Nichtmessbarkeit wird am Rang entschieden, nicht am Bestand: NICHT MESSBAR, wenn die eigene Datei in BEIDEN Listen fehlt oder in beiden schlechter als 64 steht"
  - "Ein Fall ohne uebergebene Kennung meldet keine-kennung statt ausserhalb: fehlende Eingabe und fehlender Rang sind zwei verschiedene Aussagen"
  - "98b bekommt einen eigenen sha256-Waechter, weil es gefahren wurde und Rohdaten traegt; die Korrektur heisst 98c in einem neuen Laufverzeichnis"

patterns-established:
  - "Ein neues Laufverzeichnis wandert mit seinen drei Gate-Stellen in EINER Welle: Skript, NARROW_SCOPE_DIRS und CI-Pfadfilter"
  - "Jede gefahrene Messfassung bekommt ihren Waechter, nicht nur die erste"

requirements-completed: []  # MESS-04 bleibt offen: es traegt auch 12-05 bis 12-08
requirements-advanced: [MESS-04]

# Metrics
duration: 10min
completed: 2026-09-14
---

# Phase 12 Plan 04: In-Container-Bestandssonde und die drei Gate-Stellen Summary

**Die Fremdbestandszahl entsteht ab jetzt als `SearchResult.count` im Prozess des Containers statt als gedeckelte 26 ueber die OCS-Route, und das neue Laufverzeichnis wird von den Messskript-Gates und von der CI tatsaechlich gesehen.**

## Performance

- **Duration:** rund 10 min
- **Started:** 2026-09-14T16:44Z
- **Completed:** 2026-09-14T16:54Z
- **Tasks:** 2 von 2
- **Files modified:** 3 (1 neu, 2 geaendert)

## Accomplishments

- `73-bestand-sonde.py` misst je Begriff fuenf Groessen: `index` (ungedeckelter Bestand aus `searcher.search(query, 1, count=True).count`), `fenster_lex` und `fenster_sem` (Belegung beider Ranglisten, saettigt bei 100) sowie `rang_lex` und `rang_sem` (1-basierte Position der eigenen Datei, sonst `ausserhalb` beziehungsweise `keine-kennung`).
- Die Schwelle 64 (`MAX_RECHECKS_ABSOLUTE`) ist damit erstmals erreichbar: die alte Messgroesse blieb fuer jeden Begriff und jede Tiefe bei 26 und konnte kein einziges Urteil der dritten Art ausloesen (DI-10-02, DI-11-01).
- Kein Produktionscode angefasst. Weder `backend/src/` noch `php/lib/` wurden veraendert, keine Route bekommt ein Zahlenfeld, die Zaehlung bleibt im Container (T-12-14).
- Der Schlussabschnitt der Sonde schreibt seine Lesart selbst hin, mit der RRF-Begruendung: ein Dokument, das in BEIDEN Listen vor der eigenen Datei liegt, liegt mit beiden Summanden vor ihr und damit auch in der fusionierten Liste. Ein Rang schlechter als 64 in beiden Listen kommt durch keine Fusion in die Reichweite der 64 Rechecks.
- `NARROW_SCOPE_DIRS` steht auf drei Verzeichnissen, der Pin-Test heisst `..._three_run_directories_...` und prueft die Sonde namentlich statt nur das Verzeichnis, das auch leer sein koennte.
- Zweiter Waechter: `98b-sprachfaelle.sh` ist mit 35.344 Byte und `ef74a070...c85669` festgeschrieben und meldet bei Bruch `DRIVEN_FASSUNG_RULE`.
- `docs/measurements/**` steht in `push.paths` und in `pull_request.paths` von `python.yml`, je mit Begruendung nach dem Muster von `scripts/dev/build_corpus.py`. Ein reiner Messskript-Commit startet die Python-Gates jetzt selbst und faerbt nicht mehr den naechsten, falschen Commit rot (T-12-18).

## Task Commits

1. **Task 1: In-Container-Sonde 73-bestand-sonde.py im neuen Laufverzeichnis** - `b1a5f0b` (feat)
2. **Task 2: Enger Geltungsbereich, Waechter ueber 98b und CI-Pfadfilter** - `f630e92` (test)

**Plan metadata:** siehe Schlusscommit dieses Plans (docs)

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py` (neu, 170 Zeilen) - Kopf-Docstring mit Befund, Messgegenstand und den zwei Regeln; Konstanten `BEGRIFFE` (zehn Begriffe in der Reihenfolge der Faelle 1 bis 10 von `98b`), `SCHWELLE = 64`, `FENSTER_DECKEL = 100`; Kennungen aus `DATEI_IDS`; eine ausgerichtete `bestand ...`-Zeile je Begriff; Schlussabschnitt "was daraus folgt"
- `backend/tests/test_measurement_scripts.py` - `V12_RUN_DIR`, `STOCK_PROBE`, `SUCCESSOR_LANGUAGE_CASES_SHA256`, `SUCCESSOR_LANGUAGE_CASES_BYTES`, `NARROW_SCOPE_DIRS` auf drei Verzeichnisse, umbenannter Pin-Test, neuer Test `test_the_successor_language_case_script_stays_byte_identical`
- `.github/workflows/python.yml` - `docs/measurements/**` in beiden Pfadlisten, mit Begruendungskommentar in der `push`-Liste und Rueckverweis in der `pull_request`-Liste

## Decisions Made

- **`count` statt `len(hits)`.** `SearchResult.count` ist im Typstub der installierten tantivy 0.26.0 nicht deklariert, zur Laufzeit aber vorhanden (am 14.09.2026 gegen `backend/.venv` gemessen: 300 Dokumente, `limit=10`, `count` liefert 300). Die Datei liegt unter `docs/measurements/**/skripte/`, wo weder ruff noch pyright laufen; der fehlende Stub ist dort folgenlos. Ausserhalb dieses Baums braeuchte derselbe Zugriff ein `type: ignore` oder `getattr`.
- **`read_side()` wird in der Messfunktion geholt, nicht einmal vorweg.** Der Zugriff ist im Prozess ohnehin gecacht, und der Abbruchpfad steht damit an der Stelle, an der er auffaellt: liefert er `None`, schreibt die Sonde `keine-lesbare-seite` und endet mit Rueckgabewert 2, statt so zu tun, als sei nichts zu messen gewesen.
- **Der Begriff steht in einfachen Anfuehrungszeichen im Feld `begriff`.** Zwei der zehn Begriffe tragen ein Leerzeichen (`"drei Monate"`, `type:pdf bescheid`); ohne Klammerung waere die `name=wert`-Zeile fuer einen Fahrer nicht eindeutig zerlegbar.
- **Kein zweiter Waechter ueber `98`, sondern ein erster ueber `98b`.** Der bestehende Waechter bleibt unveraendert; `98b` hat bis heute keinen Pin getragen, obwohl es am 10.09. gefahren wurde und Rohdaten unter `2026-09-werkzeugfixe/rohdaten/` traegt (T-12-17).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Shebang-Teil des Verifikationsbefehls von Task 1 kann nie gruen werden**
- **Found during:** Task 1 (Verifikation)
- **Issue:** Der Plan prueft mit `head -c 19 "$f" | grep -q '#!/usr/bin/env python3'`. Die Zeichenkette ist 22 Byte lang, 19 Byte koennen sie nicht enthalten; der Befehl ist unabhaengig vom Inhalt der Datei rot.
- **Fix:** Mit `head -c 23` gefahren, also Shebang plus LF. Die Pruefabsicht bleibt unveraendert, die Datei selbst wurde nicht angepasst.
- **Files modified:** keine
- **Verification:** `od -c` ueber die ersten 23 Byte zeigt `#!/usr/bin/env python3\n`; der uebrige Verifikationsbefehl (ast, `ranked_sides`, `count=True`, `DATEI_IDS`, kein CR, kein Geviertstrich, keine Maschinenpfade) meldet GRUEN
- **Committed in:** b1a5f0b

**2. [Rule 1 - Bug] Der Begruendungskommentar in `python.yml` verletzte sein eigenes Abnahmekriterium**
- **Found during:** Task 2 (Pfadfilter)
- **Issue:** Der erste Entwurf des Kommentars nannte das Leseziel des Gates woertlich als `docs/measurements/**/skripte/`. Damit stand die Zeichenkette `docs/measurements/**` dreimal in der Datei, das Abnahmekriterium verlangt genau zwei Vorkommen, je eines in `push.paths` und `pull_request.paths`.
- **Fix:** Kommentar auf "jedes Skript jeder Messung" umformuliert. Die Begruendungskette bleibt vollstaendig, der Glob steht nur noch dort, wo er wirkt.
- **Files modified:** .github/workflows/python.yml
- **Verification:** `grep -c "docs/measurements/\*\*"` liefert 2; die geparsten YAML-Listen tragen den Eintrag beide
- **Committed in:** f630e92

**3. [Rule 1 - Bug] Der Docstring von `scripts_of_this_run` sagte weiter "Two directories"**
- **Found during:** Task 2 (enger Geltungsbereich)
- **Issue:** Die Funktion liest `NARROW_SCOPE_DIRS`, das jetzt drei Verzeichnisse traegt. Ein Docstring, der die alte Zahl nennt, ist die naechste Stelle, an der jemand nachliest, warum ein Verzeichnis nicht geprueft wird.
- **Fix:** Auf drei Verzeichnisse fortgeschrieben, mit dem Grund des dritten (die Sonde, die den Fremdbestand im Container zaehlt).
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `pytest tests/test_measurement_scripts.py` gruen, 209 bestanden
- **Committed in:** f630e92

---

**Total deviations:** 3 auto-fixed (3 bugs)
**Impact on plan:** Kein Scope-Zuwachs. Zwei der drei betreffen Pruefbefehle und Kommentartext des Plans selbst, die dritte haelt eine Dokumentationszeile an der Konstante, die sie beschreibt.

## Issues Encountered

- **`ruff check .` vom Repositoriumswurzelverzeichnis aus ist nicht das Gate.** Am Wurzelverzeichnis liegt kein `pyproject.toml`, ruff faellt dort auf seinen kleinen Standardregelsatz zurueck und meldet Befunde in Dateien, die kein Gate dieses Projekts prueft (unter anderem `45-suchlast.py` des Semantiklaufs vom 05.09.). Gefahren wurde deshalb genau die Aufrufkette der CI: `ruff check .` und `ruff format --check .` im Backend, dazu `ruff check --config pyproject.toml ../scripts` und `ruff format --config pyproject.toml --check ../scripts`. Alle vier gruen, dazu `pyright` (0 errors) und `vulture src tests --min-confidence 80`. Die Standardregelsatz-Befunde sind Vorbefunde fremder Dateien und werden hier nicht angefasst.
- **Die Sonde ist noch nicht gegen einen echten Index gefahren.** Es gibt in dieser Phase keine Box. Abgesichert ist sie ueber `ast.parse`, ueber einen Importlauf gegen `backend/.venv` (alle vier Zugaenge aufloesbar) und ueber den Abgleich der Signaturen: `build_query(index, text, *, title_only=False)` und `ranked_sides(index, query, *, semantic=None)` passen zur Verwendung in der Datei. Der Erstvollzug im Container gehoert zu Plan 12-05 beziehungsweise Phase 15.

## User Setup Required

Keine.

## Next Phase Readiness

- Plan 12-05 kann `98c-sprachfaelle.sh` auf dieser Messgroesse aufsetzen: Abschnitt 0 faehrt die Sonde ohne `DATEI_IDS` und schreibt `index` je Begriff, Abschnitt 3b faehrt sie nach Upload und Indexierung erneut mit `DATEI_IDS` und liest die beiden Raenge. Das Transportmuster steht in `94-grundlast.sh:102-113`, der Abbruchcode 19 ist vergeben.
- Der enge Geltungsbereich gilt ab jetzt fuer jede weitere Datei des v1.2-Laufverzeichnisses: Shebang exakt, kein Maschinenpfad im Code, kein Passwort auf einer Kommandozeile.
- Offen bleibt bewusst: `98b` bleibt unberuehrt, die Korrektur heisst `98c`; und die Sonde saettigt bei 100 je Fenster, was die Lesart der beiden Fensterzahlen oberhalb davon begrenzt.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/73-bestand-sonde.py` existiert (170 Zeilen, Shebang und LF geprueft)
- `backend/tests/test_measurement_scripts.py` und `.github/workflows/python.yml` tragen die geforderten Zeichenketten (`V12_RUN_DIR`, `STOCK_PROBE`, `NARROW_SCOPE_DIRS = (RUN_DIR, FIX_RUN_DIR, V12_RUN_DIR)`, zweimal `docs/measurements/**`)
- Beide Commits sind in `git log` auffindbar: `b1a5f0b`, `f630e92`
- Keine der drei Dateien traegt einen Wagenruecklauf, ein U+2014 oder ein U+2013; die beiden geaenderten Dateien liegen mit LF im Index

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
