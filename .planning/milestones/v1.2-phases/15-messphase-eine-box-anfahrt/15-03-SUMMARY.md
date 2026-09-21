---
phase: 15-messphase-eine-box-anfahrt
plan: 03
subsystem: measurement-tooling
tags: [messwerkzeug, wiederaufwaermen, mem-01, entladeschalter, drop-caches, nutzerroute, box-anfahrt]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-01, das Laufverzeichnis mit den elf uebernommenen Werkzeugen und TOOLS_THE_MEASUREMENT_ORDER_NAMES
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-02, Abschnitt 7.2 des Runbooks mit den vier Auspraegungen, dem Befehl fuer kalt und den Rueckgabewerten 29 bis 31
  - phase: 14-modell-entladung-im-leerlauf
    provides: FINDLING_EMBED_IDLE_RELEASE_SECONDS, engine_state() mit dem Wort unloaded und die Pflichtzeile aus 6.4
  - phase: 12-messwerkzeug-runbook-terminentscheid
    provides: 97-cron-vorpruefung.sh als Hausform, NARROW_SCOPE_DIRS und a_boxless_run
provides:
  - docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh, vier Auspraegungen, Rueckgabewerte 2, 29, 30, 31
  - neun boxlose Testfaelle des neuen Werkzeugs in backend/tests/test_measurement_scripts.py
  - V12_REWARM, PIPELINE_CUT, REWARM_ABORTS, USER_SEARCH_ROUTE und DIAGNOSIS_ROUTE als benannte Konstanten
  - zwei Runbook-Nachtraege fuer 15-15 (Entladezaehler, Statusbeobachter)
affects: [15-07-ablauf, 15-09-anfahrt, 15-15-bericht, 15-16-phasenabschluss]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Messschritt mit Rueckgabewerten im Runbook bekommt ein Werkzeug, bevor die Box steht; die Rohdatei von Hand ist die Herkunft des Musters und nie der Ersatz"
    - "Wo ein Abbruch steht, entscheidet ob er einer ist: die drei Abbrueche stehen unterhalb der tee-Pipeline und ein Test haelt die Position, nicht die Anwesenheit"
    - "Gates, die eine Datei lesen, streichen zuerst die Kommentare: sonst ist das Gate an genau dem Absatz rot, der es erklaert"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh
  modified:
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "engineState wird an der Admin-Seite selbst gelesen und nicht ueber 96d-statusbeobachter.py: dessen Projektion fuehrt das Feld nicht, und die gefahrene Fassung wird nicht geaendert"
  - "Der Entladezaehler ist ueber eine Prozessgrenze nicht lesbar; als zweiter Anhaltspunkt dient die cgroup-Groesse memory.current vor und nach der Ruhezeit"
  - "Die semantische Seite wird an der Trefferzahl der Nutzerroute gegen eine Referenzzahl aus demselben Lauf abgelesen, weil die Route kein Feld dafuer traegt"
  - "Die Bereitschaft nach dem Containerneustart wird an der Admin-Seite gefragt und nie mit einer Suche, weil eine Suche in den Auspraegungen 3 und 4 die Messgroesse selbst waere"
  - "exit 2 steht oberhalb der Pipeline, weil die Verweigerung ohne Auspraegung keine Rohdatei schreiben darf; nur 29, 30 und 31 stehen unterhalb"
  - "95b-wiederaufwaermen.sh tritt in TOOLS_THE_MEASUREMENT_ORDER_NAMES ein, im selben Commit wie die Datei"

patterns-established:
  - "Eine Ablesung, die ein Werkzeug nicht hergibt, wird benannt und selbst gebaut, statt das gefahrene Werkzeug zu aendern"
  - "Jede Abweichung vom Runbook-Wortlaut steht als eigener Kommentarabsatz im Kopf des Werkzeugs und als Nachtrag in der SUMMARY (D-10)"

requirements-completed: []

# Metrics
duration: 40 min
completed: 2026-09-19
---

# Phase 15 Plan 03: Das Wiederaufwaerm-Werkzeug fuer Messschritt 8 Summary

**Der Messschritt mit den drei Rueckgabewerten hat ein Werkzeug: `95b-wiederaufwaermen.sh` faehrt genau eine von vier Auspraegungen je Lauf, schreibt seine Pflichtzeilen vor der Messung, liest die semantische Seite ausschliesslich an der Nutzerroute und prueft seine drei Abbrueche an der Stelle, an der sie wirken, unterhalb der tee-Pipeline.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-09-19T21:10:00Z
- **Completed:** 2026-09-19T21:50:00Z
- **Tasks:** 2 von 2
- **Files modified:** 2 (1 neu, 1 geaendert)

## Accomplishments

- **Die vierte offene Luecke der Recherche ist geschlossen.** Abschnitt 7.2 des Runbooks fuehrte drei Rueckgabewerte und verwies auf ein Skript, das es nicht gab; was es gab, war `95b-kaltstart-reproduktion.txt`, eine Rohdatei von Hand aus dem v1.1-Lauf, deren letzte Zeile ein `SyntaxError` aus einem inline getippten Einzeiler ist. Jetzt liegt ein Werkzeug daneben, 660 Zeilen, POSIX-`sh`, reines ASCII.
- **Vier Auspraegungen, vier Rohdateien, ein Aufrufvertrag.** `95b-wiederaufwaermen.sh <1|2|3|4>` faehrt genau einen Ast je Lauf und schreibt nach `$OUT/95b-wiederaufwaermen-<nr>.txt`. Eine Auspraegung je Lauf, weil jeder Schalterwechsel den Container neu baut und weil danach die harte Speichergrenze und die Pflichtzeile neu **abgelesen** und nicht erinnert werden.
- **Die Pflichtzeilen stehen vor der Messung und nicht daneben.** `entladeschalter-ist` (mit dem Wort `werksstand`, wenn die Variable fehlt), `containerstart-ist`, `abstand-zum-start-stunden`, `speichergrenze-ist`, `ruhezeit-ist` und, weil die Frist auf 120 s statt 900 s steht, die Begruendungszeile `ruhezeit-abweichung-grund` mit dem Wortlaut aus D-02. Die Abweichung ist damit im Protokoll begruendet und keine stille Praxis.
- **Die Stellung wird gegen den Ast geprueft und nicht nur notiert.** Die Auspraegungen 1 und 2 verlangen einen Wert groesser null, 3 und 4 genau `0`; eine Zahl am falschen Ast endet mit **29**, mit eigener Meldung. Das ist der Fall, der sonst erst beim Auswerten auffiele: ein Container mit eingeschaltetem Schalter antwortet auf jede Suche mit HTTP 200.
- **Kalt ist hergestellt, in dieser Reihenfolge.** Containerneustart, Bereitschaft an der Admin-Seite abgefragt, Waermsuche, `RUHEZEIT + KARENZ` gewartet, `engineState` gelesen, und **erst jetzt** der Seitencache des Wirts geleert (`sync`, Wert `3` nach `/proc/sys/vm/drop_caches`, `free -h` als Rueckleseprobe), auf dem Wirt und nicht im Container. Danach die Messsuche.
- **Die drei Fallen sind Code und nicht Kommentar.** **30** prueft vor den Kaltmessungen 1 und 3 zweimal unabhaengig: der Zustand, den die Admin-Seite meldet (`unloaded` fuer 1, `cold` fuer 3), und eine `/diagnose`-Zeile in `docker logs --since` seit dem Containerstart. **31** verlangt `unloaded` nach Ruhezeit und Karenz und stellt `rss-vor-ruhezeit` und `rss-nach-ruhezeit` als zweiten, unabhaengigen Anhaltspunkt daneben. **29** faengt die fehlende und die unpassende Pflichtzeile.
- **Neun boxlose Testfaelle belegen die Verweigerung, bevor die erste bezahlte Minute laeuft.** Sechs parametrisierte Faelle (`None`, `""`, `"   "`, `"0"`, `"5"`, `"eins"`) enden mit 2, mit der Benutzung auf stderr, leerem `stdout` und leerem `tmp_path`; drei weitere halten die Position der Abbrueche, die Ablesung an der Nutzerroute und die Pflichtzeilen.
- **Der Pipeline-Test wuerde rot, wenn ein Abbruch im Block stuende**, und das ist an einer gestellten Probe gezeigt statt behauptet. Kommentare werden vor dem Zaehlen gestrichen, sonst waere das Gate an genau dem Absatz rot, der den Exit-Katalog erklaert (dieselbe Falle wie `aria-current` in 13-09).

## Task Commits

Each task was committed atomically:

1. **Task 1: 95b-wiederaufwaermen.sh, vier Auspraegungen** - `c92199d` (feat)
2. **Task 2: Boxlose Verweigerungstests des neuen Werkzeugs** - `2ffff31` (test)

**Plan metadata:** siehe den docs-Commit dieses Plans

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh` - das Werkzeug des Messschritts 8, vier Auspraegungen, Rueckgabewerte 2, 29, 30, 31
- `backend/tests/test_measurement_scripts.py` - `V12_REWARM`, `USER_SEARCH_ROUTE`, `DIAGNOSIS_ROUTE`, `PIPELINE_CUT`, `REWARM_ABORTS`, `the_two_halves_of()` und vier Testfunktionen (neun Faelle); `95b-wiederaufwaermen.sh` in `TOOLS_THE_MEASUREMENT_ORDER_NAMES`

## Decisions Made

- **`engineState` wird selbst gelesen, und der Statusbeobachter bleibt unberuehrt.** Die `<interfaces>` des Plans nennen `96d-statusbeobachter.py --deckel 1` als Weg zu `engineState`. Das Werkzeug liest zwar dieselbe Admin-Seite, seine Aufzeichnung ist aber auf sechs Zaehler, `runState`, `backendReachable` und das genestete Paar **projiziert**; `engineState` ist dort nicht darunter, weil das Werkzeug aus dem v1.1-Lauf stammt und der Zustand erst mit Phase 14 entstand. Es ist eine gefahrene Fassung, und eine gefahrene Fassung wird nicht geaendert (`DRIVEN_FASSUNG_RULE`, 15-01). Das neue Skript geht deshalb dieselbe Anmeldung mit demselben `data-requesttoken` und liest genau ein Feld. `BEOBACHTER` bleibt als Vorgabe stehen, damit die Abweichung an einer Zeile haengt und nicht nur an einem Absatz.
- **Der Entladezaehler wird nicht gelesen, sondern ersetzt.** Er hat keine Route und lebt im Prozess des Containers; ein `docker exec python -c` startet einen zweiten Prozess mit einem eigenen Zaehler auf null und misst nichts. Der Beleg der Entladung ist deshalb `engineState unloaded` plus die cgroup-Differenz `memory.current` vor und nach der Ruhezeit.
- **Die semantische Seite wird an der Trefferzahl abgelesen.** Die Nutzerroute traegt kein Feld, das "die semantische Haelfte stand" sagt; `degraded` meint den unvollstaendigen Index und nicht die fehlenden Gewichte. Gelesen wird deshalb die Trefferzahl desselben zweiwortigen Begriffs gegen eine Referenzzahl **aus demselben Lauf**: in 1 und 2 die Waermsuche vor der Ruhezeit, in 3 und 4 die zweite Suche nach der Messsuche, beide mit geladenen Gewichten. Ist eine der beiden Zahlen keine Zahl, lautet die Antwort `unbestimmt` und nicht `nein`.
- **Der Begriff hat zwei Woerter, und das ist eine Bedingung und keine Vorliebe.** Eine einwortige Zeile wird seit Plan 06.1-20 allein aus dem Wortindex beantwortet: sie haette nie eine semantische Haelfte, die fehlen koennte, und die Ablesung waere blind.
- **Die Bereitschaft wird an der Admin-Seite gefragt und nie mit einer Suche.** Eine Suche als Bereitschaftsprobe waere in den Auspraegungen 3 und 4 die erste Suche ueberhaupt, also genau die Zahl, die gemessen werden soll. Das Lesen der Admin-Seite laedt kein Modell.
- **`exit 2` steht oberhalb der Pipeline, die drei anderen darunter.** Ein Aufruf ohne Auspraegung darf keine Rohdatei schreiben, also faellt die Entscheidung vor `mkdir -p "$OUT"`. Nur 29, 30 und 31 werden aus Arbeitsdateien unterhalb der Pipeline gelesen, und nur sie haelt der Test dort fest.
- **Der Dateimodus folgt dem juengsten Nachbarn.** Die drei in diesem Laufverzeichnis neu geschriebenen Werkzeuge (`73-bestand-sonde.py`, `97-cron-vorpruefung.sh`, `98c-sprachfaelle.sh`) liegen mit `100644` im Index; die elf Kopien tragen den Modus ihrer Originale. Die neue Datei liegt mit `100644` im Index und mit gesetztem Ausfuehrungsbit auf der Platte.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Der im Plan genannte Weg zu `engineState` fuehrt nicht zu `engineState`**

- **Found during:** Task 1
- **Issue:** Die `<interfaces>` des Plans nennen `96d-statusbeobachter.py --deckel 1` als Ablesung von `engineState`. Die Aufzeichnung dieses Werkzeugs traegt das Feld nicht: `recording_of()` projiziert auf `COUNTER_KEYS`, `runState`, `backendReachable` und `backend`, und `RECORDING_KEYS` im Gate haelt genau diese zehn Schluessel fest. Ueber diesen Weg waeren die Abbrueche 30 und 31 nicht entscheidbar gewesen, und das Skript haette sie mit einem Wort geprueft, das nie ankommt.
- **Fix:** Das Skript liest die Admin-Seite `/apps/findling/admin/overview` selbst, ueber dieselbe Anmeldung und dasselbe `data-requesttoken`, das der Beobachter geht, und zieht ein Feld heraus. Der Beobachter wird nicht geaendert (er ist eine gefahrene Fassung) und nicht gerufen. Die Abweichung steht als eigener Kommentarabsatz ("Abweichung 2") im Kopf des Skripts.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh`
- **Commit:** `c92199d`

**2. [Rule 2 - Missing critical functionality] Das neue Werkzeug fehlte in der Vollstaendigkeitsliste der Messreihenfolge**

- **Found during:** Task 1
- **Issue:** 15-01 hat `TOOLS_THE_MEASUREMENT_ORDER_NAMES` mit der ausdruecklichen Zusage angelegt, dass die Werkzeuge der Plaene 15-03 bis 15-06 die Liste "mit ihren eigenen Plaenen" betreten. Der Plan 15-03 nennt diesen Schritt in Task 2 nicht. Ohne ihn waere die Liste eine Vollstaendigkeitspruefung, die ein Werkzeug der Messreihenfolge nicht kennt, und der naechste vergessene Name fiele erst auf der bezahlten Box auf.
- **Fix:** `95b-wiederaufwaermen.sh` steht in der Liste, und die Zahl im Waechter ist von 14 auf 15 gezogen, im selben Commit wie die Datei (Projektregel: `test_measurement_scripts.py` reist mit dem neuen Skript).
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `c92199d`

**3. [Rule 1 - Bug] Der Bereitschaftstest haette die Messgroesse der Auspraegungen 3 und 4 verbraucht**

- **Found during:** Task 1
- **Issue:** Der Plan sagt fuer Auspraegung 1: "warten, bis die Nutzerroute wieder antwortet". Fuer 3 und 4 verlangt derselbe Plan, die Messsuche sei "die erste Suche ueberhaupt". Beides zusammen geht nicht: eine Suche als Bereitschaftsprobe waere dort die erste Suche und laedt die Gewichte, also genau das, was 3 als Bezugswert ohne Entladung messen soll.
- **Fix:** Ein `bereit_warten()`, das die Admin-Seite fragt, nicht die Suchroute. Das Lesen dieser Seite laedt laut `<interfaces>` kein Modell, der Ablauf ist damit fuer alle vier Auspraegungen derselbe, und die erste Suche bleibt in 3 und 4 die Messsuche.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh`
- **Commit:** `c92199d`

### Abweichungen vom Wortlaut der Akzeptanzkriterien

- **`exit 2` steht nicht unterhalb der Pipeline.** Das erste Akzeptanzkriterium von Task 1 verlangt alle vier Zeichenketten hinter der `tee`-Pipeline. Fuer `exit 2` ist das nicht erfuellbar und auch nicht gewollt: derselbe Plan verlangt zwei Absaetze hoeher, dass ein Aufruf ohne Auspraegung **keine Datei schreibt**, und die Pipeline schreibt die Rohdatei. Task 2 des Plans loest den Widerspruch selbst auf und prueft nur 29, 30 und 31 unterhalb des Schnitts. Umgesetzt ist die Fassung aus Task 2.
- **`--password-env` steht als Aufrufvertrag im Kopf und nicht als eigene Option.** Das Skript nimmt das Passwort ueber den **Namen** der Umgebungsvariablen (`PASSWORT_ENV`) und schreibt den Wert in eine Datei mit `chmod 600`, aus der `curl` ihn liest; auf einer Kommandozeile steht er nie. Die Option `--password-env` gehoert dem Statusbeobachter, und sein vollstaendiger Aufrufvertrag steht im Kommentar ueber `BEOBACHTER`, samt dem Grund, warum beide Werkzeuge dieselbe Variable nennen.

## Runbook-Nachtraege fuer 15-15 (D-10)

Zwei Stellen des Runbooks sind nach diesem Plan nachzutragen. Beide bleiben als eigene Zeile stehen und werden nicht stillschweigend geglaettet:

1. **Abschnitt 7.2, Entladezaehler.** Der Wortlaut nennt als Beleg der Entladung `unloaded` **und den Entladezaehler des Containers**. Der Zaehler ist ueber eine Prozessgrenze nicht lesbar. Der Nachtrag setzt an seine Stelle die cgroup-Groesse `memory.current` vor und nach der Ruhezeit als zweiten, unabhaengigen Anhaltspunkt.
2. **Abschnitt 7.2, Ablesung des Zustands.** Dass `engineState` nicht ueber `96d-statusbeobachter.py` zu bekommen ist, sondern nur ueber eine eigene Lesung der Admin-Seite, gehoert in den Schritt, in dem es gebraucht wird, und nicht nur in den Kopf des Skripts.

## Known Stubs

Keine. Das Skript hat keinen Pfad, der eine Zahl erfindet: wo eine Quelle nicht antwortet, steht `unlesbar`, `unklar` oder `unbestimmt`, und keins dieser Worte geht als Zahl durch. `94b-grundlast-rueckkehr.sh`, `99c-filter-sortierung.sh` und `92b-wechsel.sh` fehlen weiterhin im Laufverzeichnis; das ist die Reihenfolge dieser Phase (15-04 bis 15-06) und kein Stub dieses Plans.

## Issues Encountered

Ein Werkzeug, das die Box nicht hat, kann boxlos nur an seinen Verweigerungspfaden geprueft werden. Die Messpfade selbst (Neustart, Ruhezeit, Leeren des Caches, beide Suchen) sind auf dieser Maschine nicht fahrbar; belegt sind Syntax, Aufrufvertrag, die Position der Abbrueche und die Namen der Pflichtzeilen. Der erste echte Lauf ist Schritt 8 der Anfahrt, und Abschnitt 7.1 verbietet dann jede Aenderung am Werkzeug: was dort auffaellt, wird notiert und nach dem Abbau korrigiert.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | `sh -n` auf dem neuen Skript | GRUEN |
| 2 | `exit 29`, `exit 30`, `exit 31` unterhalb der `tee`-Pipeline, `exit 2` oberhalb | GRUEN, Testfall mit gestellter Probe |
| 3 | Boxlose Verweigerung: 2, leeres `stdout`, leeres Zielverzeichnis | GRUEN, sechs parametrisierte Faelle plus Handprobe |
| 4 | Protokollnamen vollstaendig (elf Namen aus dem Akzeptanzkriterium) | GRUEN, alle elf in der Datei |
| 5 | `drop_caches` und `sync` auf dem Wirt, nicht im Container | GRUEN, kein `docker exec` in diesem Block |
| 6 | OCS-Nutzerroute vorhanden, `/diagnose` nur in der Zeile mit `docker logs` | GRUEN, genau eine Fundstelle |
| 7 | `--password `, `--password=` kommen nicht vor | GRUEN, einzige Fundstelle ist `--password-env` im Kommentar |
| 8 | Gates ueber `NARROW_SCOPE_DIRS` fuer den neuen Pfad (Shebang, CR, Dash, Maschinenpfad, Passwort) | GRUEN, fuenf zusaetzliche Faelle |
| 9 | `-k "rewarm_tool"` waehlt mindestens neun Faelle | GRUEN, 9 bestanden, 303 abgewaehlt |
| 10 | `ruff check`, `ruff format --check`, `pyright`, `vulture` | GRUEN, alle vier ohne Befund |
| 11 | Volle Suite aus `backend/`, Skipzahl unveraendert | GRUEN, 2.344 bestanden, **15 uebersprungen** (unveraendert gegen 15-01 und 15-02) |
| 12 | Kein Em-Dash, kein Umlaut, kein Emoji im Skript | GRUEN, die Datei ist durchgehend ASCII |
| 13 | Zeilenenden wie bei den Geschwistern | GRUEN, LF, kein einziges CR |

Zur Testzahl: 2.330 im Stand 15-02, plus fuenf Faelle der engen Gate-Familien ueber den einen neuen Pfad, plus neun neue Faelle ergibt 2.344. Die Rechnung geht ohne Rest auf, es ist also kein Fall stillschweigend verschwunden.

## Threat Flags

Keine neue Angriffsflaeche. Die drei Dispositionen des Bedrohungsregisters sind umgesetzt: T-15-06 (kein Passwort in einem Argument, nur der Name der Variablen; Wert in einer Datei mit `chmod 600`), T-15-07 (Rueckgabewert 30 mit `engineState` **und** der `docker logs`-Suche als zweitem, unabhaengigem Kriterium), T-15-08 (Rueckgabewert 31 mit `unloaded` und der cgroup-Differenz). T-15-SC ist erfuellt: keine Abhaengigkeit wird installiert, das Skript ist POSIX-`sh` und nutzt `docker`, `curl`, `sed`, `awk` und, wenn vorhanden, `jq`.

## User Setup Required

None. Der Owner-Checkpoint 15-08 (Deckelfreigabe) ist von diesem Plan nicht beruehrt und steht weiter vor Welle C.

## Next Phase Readiness

- **15-04** (`94b-grundlast-rueckkehr.sh`, MEM-02) kann anschliessen und findet hier das Muster: Pflichtzeilen vor der Messung, Abbrueche unterhalb der Pipeline, Arbeitsdateien unter `$WORK`, und die Ablesung des Zustands an der Admin-Seite statt am Statusbeobachter. Sein Rueckgabewert 31 ist derselbe Befund wie hier und bekommt keine zweite Zahl.
- **15-07** (`00-ablauf.md` auf zehn Schritte) kann den Aufrufvertrag `95b-wiederaufwaermen.sh <1|2|3|4>` und die vier Rohdateinamen uebernehmen.
- **15-15** (Bericht) nimmt die zwei Runbook-Nachtraege oben auf.
- **MESS-05 bleibt ungetickt.** Die Anforderung gehoert an das Phasenende (15-16), obwohl die Frontmatter des Plans sie fuehrt.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh` auf der Platte gefunden, `sh -n` fehlerfrei.
- `backend/tests/test_measurement_scripts.py` traegt `V12_REWARM` und die vier neuen Testfunktionen.
- Beide Task-Commits liegen in der Historie: `c92199d`, `2ffff31`.
- Keine Loeschung in beiden Commits (`git diff --diff-filter=D` leer).
- Volle Suite aus `backend/` gruen (2.344 bestanden, 15 uebersprungen).

---
*Phase: 15-messphase-eine-box-anfahrt*
*Completed: 2026-09-19*
