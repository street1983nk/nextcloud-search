---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 01
subsystem: testing
tags: [gitattributes, line-endings, tree-hash, sha256, docker, measurement-scripts, gate, pytest]

# Dependency graph
requires:
  - phase: 06.1-launch-haertung
    provides: "backend/tests/test_ops_scripts.py als Hausordnung fuer scripts/ops, samt MACHINE_SHAPES und dem Muster, ein Gate an einer gestellten Probe rot zu machen"
  - phase: 06-semantik
    provides: "das Baumhash-Rezept in 40-abbild.sh des Semantiklaufs, dessen Wortlaut hier zur Datei wird"
provides:
  - "Zeilenende-Regel docs/measurements/**/skripte/*.py text eol=lf in .gitattributes, mit Begruendung im Kommentarstil der Datei"
  - "40b-baumhash.py: das Baumhash-Rezept als aufrufbare Datei, Wurzel und Glob als Positionsargumente, Abbruch mit 2 statt Hash ueber nichts"
  - "40b-baumhash.sh: der Beweisschritt mit eigener Rohdatei 40b-baumhash.txt, Rezept per docker cp ins Abbild, Selbstpruefung auf drei Baumhashes"
  - "backend/tests/test_measurement_scripts.py: 86 Zusicherungen, weiter Bereich ueber alle Messskripte, enger Bereich ueber das Verzeichnis dieses Laufs"
affects: [10-02, 10-03, 10-04, 10-05, 10-06, 10-07, vergleichsmessung, box-lauf]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messskript-Hausordnung mit zwei Geltungsbereichen: weit, wo der Bestand sie heute erfuellt, eng, wo nur neue Dateien sie erfuellen koennen"
    - "Eine Gate-Konstante lebt an einer Stelle und wird per ast aus der anderen Testdatei gelesen, nicht kopiert"
    - "Ein Beweisschritt prueft seine eigene Rohdatei, bevor er sich beendet"

key-files:
  created:
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.sh
    - backend/tests/test_measurement_scripts.py
  modified:
    - .gitattributes

key-decisions:
  - "Der Baumhash reist als Argument in das Abbild, nicht als Heredoc auf stdin: 40-abbild.sh ist an einem fehlenden -i gescheitert, 61-wechsel.sh hat das -i ergaenzt und die Ausgabe fehlt trotzdem. Ein Argument braucht kein stdin, also entfaellt die ganze Fehlerklasse"
  - "Ein leeres Ergebnis ist ein Rueckgabewert und keine Zeile: fehlende Wurzel und leerer Glob enden mit 2, und jede Meldung traegt den Praefix 40b-baumhash:, weil CPython eine fehlende Skriptdatei ebenfalls mit 2 quittiert"
  - "Das Skript prueft seine eigene Rohdatei auf genau drei verankerte baumhash:-Zeilen und bricht sonst ab. Der Vorlaeuferfehler war nicht das fehlende -i, sondern dass niemand danach in die Datei gesehen hat"
  - "Ein Urteil baumhash-gleich nein beendet den Schritt mit 4, ueber die Plananforderung hinaus: jede Zahl nach dieser Zeile wuerde zu einem unbekannten Stand gehoeren"
  - "Die fuenf Altfaelle sind nur im Arbeitsbaum renormalisiert; git hatte sie ohnehin mit LF gespeichert, das CRLF kam aus core.autocrlf beim Auschecken. Committed hat sich daran nichts geaendert, und genau deshalb war die Regel noetig"
  - "Der weite Bereich des Gates deckt nur Wagenruecklauf und Gedankenstrich, weil nur diese beiden heute fuer den ganzen Bestand gelten. Maschinenpfad und Passwort gelten eng, weil 45-suchlast.py sys.path.insert auf /home/ubuntu/work und drillhelfer traegt und Geschichte mit Rohdaten daneben ist"
  - "MACHINE_SHAPES wird per ast aus test_ops_scripts.py gelesen statt importiert: tests/ ist kein Paket, ein Import haette unter pytest funktioniert und unter pyright nicht"
  - "Die Altbestaende unter docs/measurements bleiben ruff-unbehandelt: CI ruft ruff nur ueber backend/ und ../scripts, und ein Reformatieren von Skripten mit Rohdaten daneben wuerde deren Herkunft verwischen, ohne eine Zahl zu verbessern"

patterns-established:
  - "Zwei Geltungsbereiche in einer Gate-Datei, mit der Begruendung fuer den Unterschied im Modul-Docstring statt in einer Notiz"
  - "Jede Diagnose eines Messwerkzeugs traegt seinen Namen als Praefix, damit eine Zusicherung ueber den Rueckgabewert nicht von der Abwesenheit des Werkzeugs erfuellt wird"
  - "Ein Gate wird an einer gestellten Probe rot gemacht und zusaetzlich an den erlaubten Gestalten gruen, damit weder der Rumpf noch die Ausnahme unbemerkt verschwindet"

requirements-completed: []  # MESS-01 und MESS-03 sind im Plan als beruehrt genannt, aber von diesem Plan nicht erfuellt: siehe Deviation 7
requirements-touched: [MESS-01, MESS-03]

# Metrics
duration: 42min
completed: 2026-09-09
---

# Phase 10 Plan 01: Werkzeugluecken vor der Anfahrt Summary

**Der Baumhash-Beweis, der in beiden Vorlaeuferberichten eine leere Rohdatei hinterlassen hat, ist ein eigener Schritt mit Selbstpruefung, und die Python-Messskripte kommen ab jetzt mit LF aus dem Windows-Checkout.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-09-09T07:20:00Z
- **Completed:** 2026-09-09T08:02:00Z
- **Tasks:** 3 von 3
- **Files modified:** 4 (1 geaendert, 3 neu)
- **Box-Minuten:** 0, wie geplant

## Accomplishments

- Die Ursache der leeren Rohdatei ist behoben, nicht umgangen: das Rezept liegt als Datei vor und reist per `docker cp` in einen Container des Abbilds, wo es mit zwei Argumenten gerufen wird. Ein Argument braucht kein stdin, also kann das fehlende `-i` von `40-abbild.sh` sich nicht wiederholen.
- Der Schritt kann nicht mehr stumm leer bleiben: `40b-baumhash.sh` schreibt drei Lesungen in `40b-baumhash.txt`, liest die Datei zurueck, zaehlt die verankerten `baumhash:`-Zeilen und bricht bei weniger als drei ab. Eine gescheiterte Lesung landet mitsamt ihrem stderr in der Rohdatei, statt den Schritt vor dem Schreiben zu beenden.
- Beide Baumhashes dieses Baums reproduzieren exakt die Werte der Recherche: `backend/src/findling` 54 Dateien / `6c47cd21...`, `php` 58 Dateien / `26b55908...`.
- Die Zeilenende-Luecke ist geschlossen: `.gitattributes` traegt einen achten Block, und die fuenf Altfaelle liegen im Arbeitsbaum mit LF. `git check-attr text eol` liefert fuer alle fuenf `text: set` und `eol: lf` statt zweimal `unspecified`.
- Die Hausordnung von `scripts/ops` gilt jetzt auch fuer die Messskripte: 86 Zusicherungen, vier Gates, jedes an einer gestellten Probe rot gemacht und an den erlaubten Gestalten gruen.
- Ganze Suite ohne Regression: 1878 passed / 15 skipped gegen die Grundlinie 1792 / 15, also genau die 86 neuen Zusicherungen und keine gebrochene alte.

## Task Commits

1. **Task 1: Die Zeilenende-Regel und die fuenf Altfaelle** , `33a1524` (chore)
2. **Task 2: Der Baumhash-Beweis als Skriptpaar mit eigener Rohdatei** , `37b1118` (test, RED) und `a4976ed` (feat, GREEN)
3. **Task 3: Das Gate ueber die Messskripte dieses Laufs** , `c53d07d` (test)

_Task 2 lief als TDD-Zyklus: elf Zusicherungen zuerst rot, dann die beiden Skripte. Ein REFACTOR-Schritt war nicht noetig._

## Files Created/Modified

- `.gitattributes` , achter Block: `docs/measurements/**/skripte/*.py text eol=lf`. Der Kommentar nennt die Shebang-Ausfuehrung auf der Box, den Unterschied zum importierten Python von `backend/`, und dass Regel und ausdruecklicher `python3 <datei>`-Aufruf zusammen gelten.
- `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py` , das Rezept aus `40-abbild.sh` als aufrufbare Datei. Wurzel und Glob als Positionsargumente, Ausgabe genau `dateien: <n>` und `baumhash: <hex>`, nur Standardbibliothek, kein Dateiinhalt in der Ausgabe. Der Docstring verbietet die Aenderung des Rezepts mit Begruendung.
- `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.sh` , der Beweisschritt. Drei Lesungen (Abbild, Arbeitsbaum backend, Arbeitsbaum php), Urteilszeile `baumhash-gleich ja|nein` samt beider Hashes, Selbstpruefung der Rohdatei. Alle Pfade sind aus dem Ort des Skripts abgeleitet, das Abbild ist die Variable `IMAGE` mit Vorgabe `ghcr.io/street1983nk/findling_backend:dev`.
- `backend/tests/test_measurement_scripts.py` , die Hausordnung. Weiter Bereich (kein `\r\n`, kein U+2014/U+2013) ueber alle 32 `.py`- und `.sh`-Dateien unter `docs/measurements/**/skripte/`, aus den Verzeichnissen gelesen. Enger Bereich (Shebang, kein Maschinenpfad, kein Passwort im Argument) ueber das Verzeichnis dieses Laufs.

## Decisions Made

Die tragenden Entscheidungen stehen im Frontmatter unter `key-decisions`. Zwei davon verdienen den Fliesstext:

**Warum der weite Bereich schmaler ist als die Hausordnung von `scripts/ops`.** Der Maschinenpfad-Teil kann nicht ueber alle Messskripte laufen. `45-suchlast.py` des Semantiklaufs traegt `sys.path.insert(0, "/home/ubuntu/work")` und `from drillhelfer import suche`, und `drillhelfer` liegt nicht im Repo. Diese Datei ist Geschichte mit ihren Rohdaten daneben; ein Gate, das ihre Umschreibung verlangt, wuerde die Herkunft dieser Rohdaten verwischen und keine einzige Zahl verbessern. Der Grund steht im Modul-Docstring, damit die naechste Leserin die Verengung nicht fuer eine Nachlaessigkeit haelt.

**Warum die fuenf renormalisierten Dateien keinen Commit-Inhalt haben.** Git hatte sie ohnehin mit LF gespeichert; das CRLF entstand erst beim Auschecken durch `core.autocrlf=true`. Der committete Unterschied von Task 1 ist deshalb ausschliesslich `.gitattributes`, und die Renormalisierung wirkt im Arbeitsbaum und in jedem kuenftigen Checkout. Genau das war die Luecke: ohne Regel haette der naechste Checkout die Wagenruecklaeufe wieder hineingeschrieben, und auf der Box waere das Skript mit `bad interpreter` gescheitert, mitten in einem gedeckelten Lauf.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Zwei Zusicherungen waren in der RED-Phase gruen, weil eine fehlende Skriptdatei denselben Rueckgabewert liefert**

- **Found during:** Task 2 (RED-Phase)
- **Issue:** `test_the_recipe_refuses_a_root_that_does_not_exist` und `test_the_recipe_refuses_an_empty_result_instead_of_hashing_nothing` bestanden, obwohl `40b-baumhash.py` noch nicht existierte. CPython quittiert eine fehlende Skriptdatei ebenfalls mit Rueckgabewert 2 und einer Meldung auf stderr, also waren beide Zusicherungen von der Abwesenheit genau des Skripts erfuellt, ueber das sie eine Aussage machen. Das ist der Fall, den die TDD-Regel als "test passes unexpectedly during RED" beschreibt.
- **Fix:** Jede Diagnose des Rezepts traegt den Praefix `40b-baumhash:`, und beide Zusicherungen verlangen ihn mit `stderr.startswith(DIAGNOSIS_PREFIX)`. Danach waren alle elf Zusicherungen rot. Der Grund steht als Kommentar an der Konstante, damit der Praefix nicht als Zierde entfernt wird.
- **Files modified:** `backend/tests/test_measurement_scripts.py`, `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py`
- **Verification:** RED danach 11 failed / 0 passed, GREEN 11 passed
- **Committed in:** `37b1118` (RED) und `a4976ed` (GREEN)

**2. [Rule 1 - Bug] Das Passwort-Gate wurde rot an `mkdir -p "$OUT"`**

- **Found during:** Task 3
- **Issue:** Der erste Entwurf nahm die vom Plan genannten Zeichenketten als reine Teilstrings, erweitert um `-p "$`. Damit wurde `40b-baumhash.sh` an seinem eigenen `mkdir -p "$OUT"` rot. Auch die Plangestalt `-p $` haette denselben Fehlbefund an jedem `mkdir -p $DIR` erzeugt: welche Anfuehrungszeichen jemand setzt, haette entschieden, ob das Gate feuert.
- **Fix:** Die Langformen `--password ` und `--password=` bleiben Teilstrings und sind eindeutig, `--password-env` wird von beiden nicht getroffen. Die Kurzform ist ein Ausdruck, der `-p` nur hinter einem Programm zaehlt, das wirklich ein Passwort so nimmt (`mysql`, `mariadb`, `mysqldump`, `redis-cli`, `smbclient`). Die gestellte Probe fuehrt beide Richtungen: die drei verbotenen Gestalten rot, `--password-env` und `mkdir -p "$OUT"` gruen.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Verification:** 86 passed, und die Probe haelt den Fehlbefund selbst fest
- **Committed in:** `c53d07d`

**3. [Rule 2 - Missing critical functionality] Ein Urteil `baumhash-gleich nein` beendet den Schritt mit einem Fehler**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt den Abbruch nur fuer eine leere Rohdatei und fuer weniger als drei `baumhash:`-Zeilen. Ein Ungleichstand haette also eine vollstaendige Rohdatei mit dem Wort `nein` darin erzeugt und den Rueckgabewert 0 , wieder eine Zeile, die jemand ueberliest. `:dev` ist ein wandernder Zeiger, der Fall ist nicht hypothetisch.
- **Fix:** Rueckgabewert 4 mit zwei Zeilen auf stderr, die sagen, dass jede danach gemessene Zahl zu einem unbekannten Stand gehoerte. Getrennter Code von der 3 der Rohdatenpruefung, damit die zwei Faelle unterscheidbar bleiben.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.sh`
- **Verification:** `sh -n` ohne Befund; der Zweig ist im Skript benannt und begruendet
- **Committed in:** `a4976ed`

**4. [Rule 2 - Missing critical functionality] Eine gescheiterte Lesung beendet den Schritt nicht mehr vor dem Schreiben**

- **Found during:** Task 2
- **Issue:** Mit `set -eu` haette ein fehlgeschlagener Aufruf (kein Docker, Abbild nicht vorhanden) das Skript beendet, bevor `40b-baumhash.txt` ueberhaupt entsteht. Ergebnis: keine Rohdatei statt einer unvollstaendigen, also derselbe Zustand, der die Vorlaeufer unbemerkt bleiben liess.
- **Fix:** Der Helfer `reading` faengt den Fehlschlag einer einzelnen Lesung, schreibt "the reading failed" samt eingerueckter stderr-Ausgabe in die Teildatei und laesst die Zaehlung am Ende urteilen. Die Rohdatei existiert danach immer, und die fehlende `baumhash:`-Zeile macht den Schritt rot.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.sh`
- **Verification:** `sh -n` ohne Befund; die Zaehlpruefung ist die Zusicherung, die den Fall faengt
- **Committed in:** `a4976ed`

**5. [Rule 2 - Missing critical functionality] Kein `/home/` in der Datei, auch nicht als kommentierte Vorgabe**

- **Found during:** Task 2
- **Issue:** Der Plan haette einen Maschinenpfad als kommentierte Variablenvorgabe erlaubt. Damit haette die Datei den Pfad einer Maschine getragen, und das Gate haette eine Ausnahme gebraucht, die es aufweicht.
- **Fix:** Alle Vorgaben sind aus dem Ort des Skripts abgeleitet (`SKRIPTE`, `REPO`, `OUT`), was auf der Box und in einem Checkout gleich gilt. Die Datei enthaelt keine Form aus `MACHINE_SHAPES`. Die Ausnahme ist im Gate trotzdem gebaut und an einer Probe belegt, weil ein spaeteres Skript sie brauchen kann.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.sh`
- **Verification:** `grep -n "/home/"` ohne Treffer; `machine_shapes_in_code` liefert `[]`
- **Committed in:** `a4976ed`

**6. [Rule 2 - Missing critical functionality] Ein Verzeichnis, dessen Name auf die Endung passt, beendet das Rezept nicht mehr mit einem Stacktrace**

- **Found during:** Task 2
- **Issue:** Das Rezept der Vorlaeufer ruft `read_bytes()` auf jeden Glob-Treffer. Ein Verzeichnis mit dem Namen `x.py` haette `IsADirectoryError` geworfen.
- **Fix:** `if not path.is_file(): continue`, mit Kommentar, dass der Schutz den Hash eines Python-Pakets oder eines PHP-Baums nicht aendern kann, weil nur eine regulaere Datei Bytes traegt. Beide Erwartungswerte reproduzieren unveraendert, also ist das Rezept nachweislich dasselbe.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py`
- **Verification:** 54 / `6c47cd21...` und 58 / `26b55908...` unveraendert
- **Committed in:** `a4976ed`

**7. [Rule 1 - Bug] MESS-01 und MESS-03 wurden beim Zustands-Update als erfuellt eingetragen und sind zurueckgenommen**

- **Found during:** Zustands-Update nach Task 3
- **Issue:** Das Frontmatter des Plans nennt `requirements: [MESS-01, MESS-03]`, und `requirements.mark-complete` hat beide in `REQUIREMENTS.md` abgehakt und in der Zuordnungstabelle auf `Complete` gesetzt. Erfuellt ist keines von beiden. MESS-01 verlangt einen Vergleichslauf auf der Box, der die RSS-Ersparnis belegt; MESS-03 verlangt den Bericht in `docs/measurements` mit der Struktur des v1.0-Berichts. Dieser Plan hat zwei Skripte und ein Gate gebaut, die Box ist nicht angefahren, es gibt keine Rohdatei und keinen Bericht, und sechs Plaene der Phase stehen noch aus.
- **Fix:** Beide Haken und beide Tabellenzeilen auf `Pending` zurueckgesetzt, `REQUIREMENTS.md` steht damit unveraendert. Im Frontmatter dieser Zusammenfassung ist `requirements-completed` leer, und die zwei Kennungen stehen unter `requirements-touched`. Der Plan traegt sie als beruehrt, nicht als abgeschlossen; abhaken darf sie der Plan, der die Zahlen und den Bericht erzeugt.
- **Files modified:** `.planning/REQUIREMENTS.md` (zurueckgesetzt, netto unveraendert), `.planning/phases/10-vergleichsmessung-auf-der-aws-box/10-01-SUMMARY.md`
- **Verification:** `git diff --stat` nennt `REQUIREMENTS.md` nicht mehr; `grep MESS-0` zeigt drei offene Kaestchen und drei `Pending`-Zeilen
- **Committed in:** dieser Metadaten-Commit

---

**Total deviations:** 7 auto-fixed (3x Rule 1 Bug, 4x Rule 2 fehlende kritische Funktionalitaet)
**Impact on plan:** Kein Scope Creep. Drei der sieben sind Reparaturen an Aussagen, die sonst gruen geblieben waeren, ohne etwas zu belegen (zwei Zusicherungen und zwei Anforderungshaken) , also genau die Fehlerart, die dieser Plan an den Vorlaeufern behebt. Die vier Rule-2-Ergaenzungen betreffen alle denselben Punkt: der Beweisschritt darf nicht auf einem Weg enden, der wieder eine leere oder ueberlesene Rohdatei erzeugt. Keine Fremdabhaengigkeit, `backend/uv.lock` unveraendert.

## Issues Encountered

**Der Glob als Argument statt `rglob` im Rezept.** Die Vorlaeufer rufen `root.rglob("*.py")`. Mit dem Glob als Argument waere `root.rglob("**/*.py")` zu `**/**/*.py` geworden, und ob pathlib dabei dedupliziert, ist nicht zugesichert. Geloest mit `root.glob(pattern)`, was fuer `**/*.py` genau die Menge von `rglob("*.py")` liefert. Belegt dadurch, dass beide Erwartungswerte auf das letzte Zeichen stimmen.

**MACHINE_SHAPES beziehen, ohne pyright zu brechen.** `tests/` ist kein Paket und traegt kein `__init__.py`, `from test_ops_scripts import ...` haette unter pytest funktioniert und unter pyright als nicht aufloesbarer Import gegolten. Geloest mit `ast.literal_eval` ueber den Syntaxbaum der anderen Testdatei. Nebenwirkung, die gewollt ist: verschwindet die Konstante dort, scheitert dieses Modul beim Einsammeln laut statt still.

## User Setup Required

None , keine externe Konfiguration. Der Plan hat null Box-Minuten gekostet und keine Cloud-Ressource angefasst.

## Next Phase Readiness

**Bereit.** Das Messwerkzeug fuer den Lauf ab Welle 5 ist geschlossen, bevor die Box angefahren wird:

- Ein Messskript aus diesem Checkout startet auf der Box ueber seine eigene Shebang, und die naechste Datei unter `docs/measurements/**/skripte/` bekommt die Regel geschenkt.
- `40b-baumhash.sh` gehoert in den Ablaufplan des Laufs an die Stelle, an die `61-wechsel.sh` seinen leeren Abschnitt geschrieben hat, also direkt hinter das Ziehen von `:dev` und vor die Registrierung. Erwartung: `dateien: 54` und `baumhash: 6c47cd21...` auf beiden Seiten, `baumhash-gleich ja`.
- Die Rohdatei `40b-baumhash.txt` entsteht erst auf der Box; das Verzeichnis `rohdaten/` legt das Skript selbst an.

**Was dieser Plan ausdruecklich nicht getan hat:** Die Altbestaende unter `docs/measurements` sind nicht ruff-clean (16 Befunde, 8 Dateien nicht format-clean) und bleiben es. CI ruft ruff ueber `backend/` und `../scripts`, nie ueber `docs/measurements`, und ein Reformatieren von Skripten mit ihren Rohdaten daneben wuerde deren Herkunft verwischen. Das ist kein offener Punkt, sondern eine Entscheidung.

**Ein Hinweis fuer den Lauf:** Der Pfad `IMAGE_ROOT` traegt `python3.13`, also die Interpreterfassung des Abbilds. Hebt das Abbild seinen Python, muss diese Zeile mitziehen. Sie steht als benannte Variable mit Kommentar oben im Skript, damit das eine Zeile ist und keine Suche.

## Known Stubs

Keine. Beide Skripte laufen vollstaendig, `40b-baumhash.py` reproduziert die zwei Erwartungswerte, und `40b-baumhash.sh` ist bis auf die drei Aufrufe ins Docker der Box lokal mit `sh -n` geprueft. Die Docker-Haelfte kann ohne Box nicht gefahren werden, das ist keine Auslassung, sondern der Gegenstand von Welle 5.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Alle sechs Eintraege mit Disposition `mitigate` sind umgesetzt:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-10-01 | Eigener Schritt, eigene Rohdatei, Aufruf als Argument, Selbstpruefung auf drei verankerte `baumhash:`-Zeilen, Abbruch mit 3 |
| T-10-02 | `.gitattributes`-Regel, fuenf Altfaelle renormalisiert, Gate ueber den ganzen Bestand |
| T-10-03 | Passwort-Gate ueber das Verzeichnis dieses Laufs, `--password-env` als erlaubter Weg, an einer Probe belegt |
| T-10-04 | Docstring verbietet die Aenderung des Rezepts, drei Zusicherungen halten Normalisierung, Pfadabhaengigkeit und Bytetreue, zwei Erwartungswerte stehen als Konstanten im Gate |
| T-10-05 | `40b-baumhash.py` gibt nur Anzahl und einen Hash aus, der Digest je Datei verlaesst den Prozess nicht, der Docstring sagt es ausdruecklich |
| T-10-SC | Kein Paket installiert, `backend/uv.lock` unveraendert, Importe des Rezepts sind `hashlib`, `sys` und `pathlib` |

## Self-Check: PASSED

Alle vier Dateien aus `files_modified` liegen auf der Platte, alle vier Commits sind in `git log`, und `git diff --name-only af18542 HEAD` nennt keine fuenfte Datei. Kein Em-Dash und kein En-Dash in den geaenderten Dateien und in dieser Zusammenfassung.

| Geprueft | Ergebnis |
|----------|----------|
| `.gitattributes` traegt die Regel, `git check-attr text eol` fuer die fuenf | `text: set`, `eol: lf` (vorher zweimal `unspecified`) |
| Kein `\r\n` unter `docs/measurements/**/skripte/` | 32 Dateien, alle sauber |
| `40b-baumhash.py` gegen `backend/src/findling` | `dateien: 54`, `baumhash: 6c47cd21...` |
| `40b-baumhash.py` gegen `php` | `dateien: 58`, `baumhash: 26b55908...` |
| Aufruf gegen fehlende Wurzel | Rueckgabewert 2, `40b-baumhash: no such directory`, keine `baumhash:`-Zeile |
| `sh -n 40b-baumhash.sh` | ohne Befund |
| `pytest tests/test_measurement_scripts.py -q` | 86 passed |
| `pytest -q` (ganze Suite) | 1878 passed / 15 skipped (Grundlinie 1792 / 15) |
| `ruff check .`, `ruff format --check .` in `backend/` | All checks passed, 120 files already formatted |
| `ruff check` und `ruff format --check` ueber das neue Verzeichnis | All checks passed, 1 file already formatted |
| `pyright` | 0 errors, 0 warnings, 0 informations |
| `vulture src tests --min-confidence 80` | ohne Befund |
| Loeschungen in den vier Commits | keine |

## TDD Gate Compliance

Task 2 traegt beide Tore in der richtigen Reihenfolge: `37b1118` (`test(10-01)`, 11 failed) vor `a4976ed` (`feat(10-01)`, 11 passed). Ein REFACTOR-Tor war nicht noetig, weil beide Skripte in ihrer ersten Fassung durch ruff, ruff format und pyright gingen. Task 3 ist eine reine Testdatei ohne Quelldatei und damit kein verhaltensaenderndes Vorhaben; sein einziger Commit ist folgerichtig ein `test(...)`.

Die RED-Phase von Task 2 ist einmal fail-fast gelaufen: zwei Zusicherungen waren gruen, bevor es etwas zu pruefen gab. Das ist unter Deviation 1 dokumentiert und war der Grund fuer den Diagnose-Praefix.

---
*Phase: 10-vergleichsmessung-auf-der-aws-box*
*Completed: 2026-09-09*
