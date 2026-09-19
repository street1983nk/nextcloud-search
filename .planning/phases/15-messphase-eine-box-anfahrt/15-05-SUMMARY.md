---
phase: 15-messphase-eine-box-anfahrt
plan: 05
subsystem: measurement-tooling
tags: [messwerkzeug, d-01, filter, sortierung, blaettern, cursor, seitenroute, box-anfahrt]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-01, das Laufverzeichnis, der Kopie-Waechter und TOOLS_THE_MEASUREMENT_ORDER_NAMES
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-02, Schritt 6b der Messreihenfolge und die Rueckgabewerte 34 und 35 in Abschnitt 7.1
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-03, die Hausform des Werkzeugs und die Position der Abbrueche unterhalb der Pipeline
  - phase: 15-messphase-eine-box-anfahrt
    provides: 15-04, die Doppelbelegung einer Rueckgabezahl und das Muster des Pflichtzeilenblocks
  - phase: 13-filter-sortierung-blaettern
    provides: SORT_MODES, TYPE_GROUPS, der Cursor mit Fingerabdruck und findling-pager__step--next
  - phase: 09-seitenroute-und-budget
    provides: 99-seitenroute.sh, die Rangregel, Befund M-03 zum Anmeldeweg und der zweiwortige Begriff
provides:
  - docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh, zwei Bloecke, Rueckgabewerte 2, 29, 34, 35
  - sieben boxlose Testfaelle des Blocks in backend/tests/test_measurement_scripts.py
  - V12_FILTER_SORT, SEARCH_MODULE, SORT_MODES_NAME, SORT_MODES_IN_THE_TOOL, NEXT_LINK_MARK, BUILT_POSITION, LOAD_TOOL und FILTER_SORT_ABORTS als benannte Konstanten
  - sort_mode_names_of_the_package(), das die Sortiernamen aus dem Quelltext des Pakets liest
  - ein Runbook-Nachtrag fuer 15-15 (Doppelbelegung von 34 und 35)
affects: [15-07-ablauf, 15-09-anfahrt, 15-15-bericht, 15-16-phasenabschluss]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Messwerkzeug, das gegen eine Namenstabelle des Erzeugnisses misst, liest die Namen im Gate aus dem Quelltext und wiederholt sie nicht"
    - "Ein Blaetterwerkzeug baut ausser der ersten Seite keine Adresse; die Position kommt aus der Antwort, sonst misst es den stillen Rueckfall"
    - "Ein Zeilenname, der erst zur Laufzeit entsteht, steht zusaetzlich ausgeschrieben im Kopf, damit ein Bericht ihn in der Datei findet"

key-files:
  created:
    - docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh
  modified:
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Gemessen wird ausschliesslich ueber die Seitenroute; scripts/ops/search_load.py wird nicht angefasst und nicht gerufen, und ein Gate haelt das fest"
  - "Die drei Sortiernamen werden im Test aus SORT_MODES des Pakets gelesen und gegen die eine Zeile SORTIERMODI des Werkzeugs gehalten"
  - "Ausser Seite 1 baut das Werkzeug keine Adresse; der Weiter-Link wird an findling-pager__step--next aus der Antwort gezogen"
  - "Die gemeldete Seitenzahl kommt aus der Marke des Blaetterns und nicht aus einem Adressparameter, weil nur sie den stillen Rueckfall zeigt"
  - "Die Rueckgabewerte 34 und 35 tragen je zwei Faelle, den des Runbooks und den des Plans"
  - "Ein Entladeschalter ungleich 0 ist ein protokollierter Befund und kein Abbruch; abgebrochen wird nur bei unlesbarer Stellung (29)"
  - "99c-filter-sortierung.sh tritt in TOOLS_THE_MEASUREMENT_ORDER_NAMES ein, im selben Commit wie die Datei (16 auf 17)"

patterns-established:
  - "Zwei stille Fehlerwege eines Messblocks bekommen je einen Abbruch UND je ein Gate: der Abbruch faengt den Lauf, das Gate faengt das Werkzeug"
  - "Eine Namenstabelle des Erzeugnisses wird im Messwerkzeug an genau einer Stelle gefuehrt, damit ein Gate sie gegen die Quelle halten kann"

requirements-completed: []

# Metrics
duration: 40 min
completed: 2026-09-19
---

# Phase 15 Plan 05: Der Filter- und Sortierblock des Owner-Entscheids D-01 Summary

**Der vom Owner am 19.09.2026 bestellte Messblock hat sein Werkzeug: `99c-filter-sortierung.sh` misst die drei Sortiermodi auf dem Vollbestand und das Blaettern unter einem Typfilter, es zieht jede Adresse ausser der ersten aus der Antwort statt sie zu bauen, und seine beiden stillen Fehlerwege, der verworfene Cursor und die ungefilterte Route, sind als Abbruch UND als Gate ausgeschlossen.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-09-19T22:40:00Z
- **Completed:** 2026-09-19T23:20:00Z
- **Tasks:** 2 von 2
- **Files modified:** 2 (1 neu, 1 geaendert)

## Accomplishments

- **Der Owner-Entscheid D-01 hat ein Werkzeug, und zwar vor der Box.** Abschnitt 7.1 des Runbooks verbietet waehrend der bezahlten Anfahrt jede Aenderung an einem Werkzeug. Was dieser Block leisten muss, muss er also heute koennen, auf einer Maschine ohne Vollbestand: Aufrufvertrag, Verweigerung, Position der Abbrueche und die beiden Gates gegen das Driften.
- **Gemessen wird ueber die Seitenroute, und das ist keine Stilfrage.** Nur sie traegt `types` und `sort`; die beiden OCS-Provider kennen beide Parameter nicht (Befund 13-12). Eine Messung ueber sie beantwortete die gestellte Anfrage ungefiltert und unsortiert und saehe dabei aus wie eine Filtermessung. `scripts/ops/search_load.py` wird deshalb nicht gerufen und nicht angefasst; sein Name kommt in der Datei nur im Kopfkommentar vor, und ein Gate haelt genau das fest.
- **Die drei Sortiernamen koennen nicht gegen das Erzeugnis driften.** Der Test liest `SORT_MODES` aus `backend/src/findling/index/search.py` mit `ast` und haelt die Schluessel gegen die eine Zeile, in der das Werkzeug seine Namen fuehrt. Ein vierter Name im Werkzeug ist rot, ein fehlender ebenso. Das ist keine Formalie: ein unbekannter Name faellt im Erzeugnis still auf `relevance` zurueck, eine Zeile mit erfundenem Namen maesse also `relevance` unter falscher Ueberschrift, und ein fehlender Name waere ein Modus, den niemand auf der einzigen Box gemessen hat, die den Bestand hat.
- **Das Blaettern baut keine Adresse.** Der Weiter-Link wird an seiner Auszeichnung `findling-pager__step--next` aus der Antwort gezogen, seine HTML-Entitaeten werden entschaerft, und er wird aufgerufen. Ein selbstgebautes `page=2` ohne `fp` wuerde den Fingerabdruck verfehlen und auf Seite 1 zurueckwerfen: mit 200, schnell, und im Protokoll staende eine huebsche Zahl fuer einen Vorgang, der nie stattgefunden hat (13-08). Ein Gate verbietet die Positionsangabe im Code des Werkzeugs, und die gestellte Probe zeigt, dass es feuert.
- **Der stille Rueckfall hat zwei unabhaengige Faenger.** Der erste ist die Seitenzahl, die die Seite selbst meldet: sie wird aus der Marke des Blaetterns gelesen und nicht aus einem Adressparameter, weil die Uebersetzung das Wort davor umdreht und die Zahl eine Zahl bleibt. Der zweite ist der Vergleich der Datei-Kennungen zweier aufeinander folgender Seiten, den Abschnitt 7.1 fuer 35 ausdruecklich verlangt: ein Blaettern, das eine Kennung zweimal ausliefert, ist ein Befund ueber die Seitenroute und keine Sortierzahl.
- **Block A sagt, was er nicht messen kann.** `sortierung-ohne-vektorhaelfte=ja` steht mit dem Grund daneben: unter Sortierung gibt es keine Fusion, der Zweig ist rein lexikalisch und jeder Treffer traegt `score = 0.0` (13-02). Die drei Zahlen sind untereinander vergleichbar, gegen `relevance` nur bedingt. Das gehoert in die Rohdatei und nicht nur in den Bericht, weil eine Rohdatei fuer sich gelesen wird.
- **Die Pflichtzeilen stehen vor der Messung, samt Anmeldeweg.** `entladeschalter-ist`, `containerstart-ist`, `speichergrenze-ist`, `filter-typgruppe-ist`, `anmeldeweg-ist=sitzung` und `sortiermodi-ist`. Der Verzicht auf den zweiten Anmeldeweg ist eine eigene Zeile mit Zahl: Basic Auth kostet auf der Vergleichsinstanz 0,318 s je Anfrage, die kein angemeldeter Nutzer zahlt (Befund M-03 der Phase 9), und zwei Berichte sind nur ueber denselben Anmeldeweg vergleichbar.
- **Sieben boxlose Faelle belegen das alles, bevor die erste bezahlte Minute laeuft.** Drei parametrisierte Verweigerungsfaelle (`pdf`, `--help`, `1`) enden mit 2, mit der Benutzung auf stderr, leerem `stdout` und leerem `tmp_path`; vier weitere halten die Sortiernamen gegen das Paket, den gezogenen Weiter-Link, die Position der drei Abbrueche und die Abwesenheit des Lastwerkzeugs im Code.

## Task Commits

Each task was committed atomically:

1. **Task 1: 99c-filter-sortierung.sh** - `1d3a3ec` (feat)
2. **Task 2: Boxlose Tests und die zwei Driftgates** - `aa40a3d` (test)

**Plan metadata:** siehe den docs-Commit dieses Plans

## Files Created/Modified

- `docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh` - das Werkzeug des Messschritts 6b, zwei Bloecke, Rueckgabewerte 2, 29, 34, 35
- `backend/tests/test_measurement_scripts.py` - `V12_FILTER_SORT`, `SEARCH_MODULE`, `SORT_MODES_NAME`, `SORT_MODES_IN_THE_TOOL`, `NEXT_LINK_MARK`, `BUILT_POSITION`, `LOAD_TOOL`, `FILTER_SORT_ABORTS`, `sort_mode_names_of_the_package()` und fuenf Testfunktionen (sieben Faelle); `99c-filter-sortierung.sh` in `TOOLS_THE_MEASUREMENT_ORDER_NAMES`, die Zahl im Waechter von 16 auf 17

## Decisions Made

- **Die Seitenroute ist die einzige Quelle, und das Lastwerkzeug bleibt unberuehrt.** `scripts/ops/search_load.py` ist geeicht, es ist der Vergleichsschluessel der Stufen aus Schritt 6 gegen v1.1, und es fragt eine Route, die `types` und `sort` nicht kennt. Es wird weder geaendert noch auf eine neue Frage gerichtet. Sein Name darf im Kopf stehen, weil ein Leser, der sich wundert, warum das naheliegende Werkzeug fehlt, die Antwort in der Datei verdient; er darf nirgends stehen, wo eine Shell ihn liest.
- **Die Sortiernamen werden gelesen und nicht wiederholt.** Eine im Test aufgeschriebene Liste dreier Woerter waere sich selbst einig an dem Tag, an dem das Erzeugnis einen vierten Namen bekommt. Gelesen wird der Quelltext des Pakets mit `ast`, und das Werkzeug fuehrt seine Namen an genau einer Stelle (`SORTIERMODI`), damit es eine Stelle gibt, gegen die gehalten werden kann.
- **Die gemeldete Seitenzahl kommt aus der Marke und nicht aus der Adresse.** Die Marke druckt `Page %s` durch die Uebersetzung; das Wort davor wechselt mit der Sprache der Instanz, die Zahl nicht. Gelesen werden deshalb die Ziffern des Markentextes. Ein Adressparameter waere die falsche Quelle: er sagt, was angefordert wurde, und dieser Block will wissen, was geantwortet hat.
- **Die Rueckgabewerte 34 und 35 tragen je zwei Faelle.** Abschnitt 7.1 gibt 34 dem wachsenden Bestand und 35 der Stufe ohne Antwortzahlen samt doppelter Datei-Kennung; der Plan 15-05 gibt 34 dem Sortierlauf ohne Trefferzahl und 35 dem fehlenden Weiter-Link samt verworfenem Cursor. Beide Lesarten sind umgesetzt, wie schon bei 32 und 33 in 15-04: eine einmal vergebene Zahl wird nicht umgehaengt, damit Rohdaten frueherer Laeufe lesbar bleiben.
- **Ein Entladeschalter ungleich 0 bricht nicht ab.** Der Plan sagt, dieser Block laufe auf `0`, und verlangt 29 nur fuer die FEHLENDE Stellung. Eine andere Stellung ist deshalb eine protokollierte Zeile (`entladeschalter-passt-zum-block=nein, ...`) und kein Abbruch: die beiden Sortierzweige sind ohnehin rein lexikalisch, und ein Abbruch an dieser Stelle koste Box-Zeit fuer einen Umstand, der die Zahlen erklaert statt sie zu entwerten.
- **Der Bestand wird vor der ersten Stufe geprueft.** Abschnitt 7.1 gibt 34 dem Bestand, der noch wuchs. Geprueft wird der Arbeitsvorrat aus `occ findling:index` nach dem Muster von `93-nullstand.sh`; ist er nicht leer, endet der Lauf, bevor eine einzige Zeile gefahren ist.
- **Aufwaermanfragen gibt es nicht.** `99-seitenroute.sh` faehrt fuenf davon je Zeile, weil es auf einer kalten Instanz misst. Schritt 6b steht hinter den Laststufen, der Container ist dort aufgewaermt, und zusaetzliche Anfragen je Zeile waeren gekaufte Box-Zeit ohne Aussage. Die Rangregel bleibt dieselbe wie im Seitenbudget-Bericht, ohne Interpolation.
- **`exit 2` steht oberhalb der Pipeline.** Dieselbe Aufteilung wie in 15-03 und 15-04: ein Aufruf mit Argument bestreitet den Zuschnitt des ganzen Werkzeugs, und ein Streit darf keine Rohdatei schreiben; die Pipeline schriebe eine. 29, 34 und 35 stehen darunter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Die Runbook-Bedeutungen von 34 und 35 fehlten im Plan**

- **Found during:** Task 1
- **Issue:** Der Plan belegt 34 mit "ein Sortierlauf ohne Trefferzahl" und 35 mit "kein Weiter-Link oder Rueckfall auf Seite 1". Abschnitt 7.1 des Runbooks hat denselben beiden Zahlen seit 15-02 zwei andere Faelle gegeben: den Bestand, der noch wuchs (34), und die Stufe ohne Antwortzahlen oder mit einer doppelt ausgelieferten Datei-Kennung (35). Ein Werkzeug, das nur die Plan-Faelle kennte, hiesse in der Tabelle des Runbooks etwas anderes als in seiner eigenen Datei.
- **Fix:** Beide Lesarten sind umgesetzt. 34 faellt zusaetzlich, wenn der Arbeitsvorrat vor der ersten Stufe nicht leer ist; 35 faellt zusaetzlich, wenn zwei aufeinander folgende Seiten eine Datei-Kennung teilen. Der Kopfkommentar nennt beide Herkuenfte, und die Doppelbelegung gehoert als Nachtrag ins Runbook (15-15). Das ist dasselbe Vorgehen, das 15-04 fuer 32 und 33 gewaehlt hat.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh`
- **Commit:** `1d3a3ec`

**2. [Rule 2 - Missing critical functionality] Das neue Werkzeug fehlte in der Vollstaendigkeitsliste der Messreihenfolge**

- **Found during:** Task 1
- **Issue:** 15-01 hat `TOOLS_THE_MEASUREMENT_ORDER_NAMES` mit der Zusage angelegt, dass die Werkzeuge der Plaene 15-05 und 15-06 die Liste mit ihren eigenen Plaenen betreten. Task 2 des Plans nennt diesen Schritt nicht. Ohne ihn waere die Liste eine Vollstaendigkeitspruefung, die ein Werkzeug der Messreihenfolge nicht kennt, und Schritt 6b staende in der Tabelle des Runbooks ohne Datei in der Liste.
- **Fix:** `99c-filter-sortierung.sh` steht in der Liste, die Zahl im Waechter ist von 16 auf 17 gezogen, und beide Kommentare nennen nur noch 15-06 als ausstehend. Im selben Commit wie die Datei (Projektregel).
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `1d3a3ec`

**3. [Rule 3 - Blocking issue] Zwei geforderte Zeilennamen entstehen erst zur Laufzeit**

- **Found during:** Task 1, Akzeptanzpruefung
- **Issue:** Das sechste Akzeptanzkriterium verlangt, dass die Datei die Zeilen `sortierung-relevance-ms-median` und `blaettern-seite-1-ms` traegt. Beide entstehen in einer Schleife aus `sortierung-$modus-ms-median` und `blaettern-seite-$seite-ms` und stehen deshalb nirgends in der Datei. Ein Bericht, der nach einem Zeilennamen greift, faende sie ebenso wenig.
- **Fix:** Der Kopf traegt einen eigenen Block "Die Zeilen, die dieses Werkzeug schreibt" mit allen Namen ausgeschrieben, einschliesslich der drei Sortiermodi und der ersten geblaetterten Seite. Das erfuellt das Kriterium woertlich und ist zugleich das, was ein Leser der Rohdatei braucht.
- **Files modified:** `docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh`
- **Commit:** `1d3a3ec`

### Abweichungen vom Wortlaut der Akzeptanzkriterien

- **`exit 2` steht nicht unterhalb der Pipeline.** Das vierte Akzeptanzkriterium von Task 1 verlangt alle vier Zeichenketten hinter der `tee`-Pipeline. Fuer `exit 2` ist das nicht erfuellbar und nicht gewollt: derselbe Plan verlangt in Task 2 ein leeres `tmp_path` nach dem verweigerten Aufruf, und die Pipeline schreibt die Rohdatei. Umgesetzt ist die Fassung aus Task 2, dieselbe Aufteilung wie in 15-03 und 15-04, und ein Testfall haelt beide Seiten.
- **Der Schalterbefund ist milder als in 15-04.** Dort endet eine Stellung von 0 mit 29, weil jener Block eine Freigabe braucht. Hier ist 0 die erwartete Stellung, und eine andere ist ein Befund neben den Zahlen. Abgebrochen wird nur bei unlesbarer Stellung, genau wie der Plan es sagt.

## Runbook-Nachtraege fuer 15-15 (D-10)

Zu den Nachtraegen aus 15-03 und 15-04 kommt einer dazu:

1. **Abschnitt 7.1, Rueckgabewerte 34 und 35.** Beide tragen jetzt je zwei Faelle. Die Tabelle nennt bisher nur einen davon; der zweite gehoert daneben, mit dem Satz, dass keine Bedeutung weggefallen ist. Das ist dieselbe Ergaenzung, die 15-04 fuer 32 und 33 angemeldet hat.

## Known Stubs

Keine. Das Werkzeug hat keinen Pfad, der eine Zahl erfindet: wo eine Quelle nicht antwortet, steht `unlesbar`, `unbestimmt` oder `keine`, und keines dieser Worte geht als Zahl durch. `92b-wechsel.sh` fehlt weiterhin im Laufverzeichnis; das ist die Reihenfolge dieser Phase (15-06) und kein Stub dieses Plans.

## Issues Encountered

Ein Werkzeug, das die Box nicht hat, kann boxlos nur an seinen Verweigerungspfaden und an seinem Wortlaut geprueft werden. Die Messpfade selbst (Anmeldung, Sortierlaeufe, Blaettern, Cursor) sind auf dieser Maschine nicht fahrbar; belegt sind Syntax, Aufrufvertrag, die Position der Abbrueche, die Uebereinstimmung der Sortiernamen mit dem Erzeugnis, der gezogene Weiter-Link und die Abwesenheit des Lastwerkzeugs im Code. Der erste echte Lauf ist Schritt 6b der Anfahrt, und Abschnitt 7.1 verbietet dann jede Aenderung am Werkzeug: was dort auffaellt, wird notiert und nach dem Abbau korrigiert.

Eine zweite Grenze ist ehrlicher zu nennen als zu verschweigen: die Trefferzahl einer Seite ist die Zahl ihrer Trefferzeilen und nicht die Gesamtzahl der Treffer. Die Ergebnisseite fuehrt bewusst keine Summe (Block 5 ihrer Vorlage), weil eine Summe niemand gemessen hat. Die drei Sortierzeilen sind deshalb an ihrer Seitenfuellung vergleichbar, nicht an einer Gesamtmenge.

## Verification

| Nr | Pruefung | Ergebnis |
|----|----------|----------|
| 1 | `sh -n` auf dem neuen Skript | GRUEN |
| 2 | Die Datei nennt `relevance`, `newest` und `oldest` und keinen vierten Sortiernamen | GRUEN, `SORTIERMODI` liefert genau die drei Schluessel von `SORT_MODES` |
| 3 | Die Datei nennt `findling-pager__step--next` und baut ausser Seite 1 keine Adresse | GRUEN, null Fundstellen der Positionsangabe im Code |
| 4 | `exit 29`, `exit 34`, `exit 35` unterhalb der `tee`-Pipeline, `exit 2` oberhalb | GRUEN, Testfall mit gestellter Probe |
| 5 | Die Datei nennt `search_load.py` nur im Kopfkommentar und ruft es nirgends auf | GRUEN, genau eine Fundstelle, und die ist ein Kommentar |
| 6 | Die geforderten Zeilennamen stehen in der Datei | GRUEN, alle vier, drei davon ueber den Zeilenblock im Kopf |
| 7 | Boxlose Verweigerung: 2, Benutzung auf stderr, leeres `stdout`, leeres Zielverzeichnis | GRUEN, drei parametrisierte Faelle plus Handprobe |
| 8 | `git status --porcelain scripts/ops/` ist leer | GRUEN |
| 9 | Gates ueber `NARROW_SCOPE_DIRS` fuer den neuen Pfad (Shebang, CR, Dash, Maschinenpfad, Passwort) | GRUEN, fuenf zusaetzliche Faelle |
| 10 | `-k "filter_sort_tool"` waehlt mindestens sieben Faelle | GRUEN, 7 bestanden, 329 abgewaehlt |
| 11 | `ruff check`, `ruff format --check`, `pyright`, `vulture` | GRUEN, alle vier ohne Befund |
| 12 | Volle Suite aus `backend/`, Skipzahl unveraendert | GRUEN, 2.368 bestanden, **15 uebersprungen** (unveraendert gegen 15-01 bis 15-04) |
| 13 | Kein Em-Dash, kein Umlaut, kein Emoji im Skript | GRUEN, die Datei ist durchgehend ASCII |
| 14 | Zeilenenden wie bei den Geschwistern | GRUEN, LF, kein einziges CR |

Zur Testzahl: 2.356 im Stand 15-04, plus fuenf Faelle der engen Gate-Familien ueber den einen neuen Pfad, plus sieben neue Faelle ergibt 2.368. Die Rechnung geht ohne Rest auf, es ist also kein Fall stillschweigend verschwunden.

## Threat Flags

Keine neue Angriffsflaeche. Die vier Dispositionen des Bedrohungsregisters sind umgesetzt: T-15-12 (Rueckgabewert 35 an der gemeldeten Seitenzahl UND an der doppelten Datei-Kennung, Weiter-Link gezogen statt gebaut, dazu ein Gate gegen die selbstgebaute Position), T-15-13 (Messung ueber die Seitenroute, `search_load.py` wird nicht gerufen, und ein Gate haelt fest, dass sein Name nur in Kommentarzeilen steht), T-15-14 (das Passwort reist ueber den NAMEN einer Umgebungsvariablen in eine Datei mit `chmod 600` und steht in keinem Argument; das bestehende Gate greift auf die neue Datei), T-15-SC (keine Abhaengigkeit wird installiert; das Skript ist POSIX-`sh` und nutzt `docker`, `curl`, `sed`, `awk`, `grep`, `sort` und `comm`).

## User Setup Required

None. Der Owner-Checkpoint 15-08 (Deckelfreigabe) ist von diesem Plan nicht beruehrt und steht weiter vor Welle C.

## Next Phase Readiness

- **15-06** (`92b-wechsel.sh`, der Abbildwechsel-Block 13b) kann anschliessen und findet hier dasselbe Muster wie 15-03 und 15-04 es hinterlassen haben, ergaenzt um ein Gate, das eine Namenstabelle des Erzeugnisses gegen das Messwerkzeug haelt.
- **15-07** (`00-ablauf.md` auf zehn Schritte) kann den Aufrufvertrag `99c-filter-sortierung.sh` ohne Argument und den Rohdateinamen `99c-filter-sortierung.txt` uebernehmen, dazu die Stellschrauben `BEGRIFF`, `FILTER_GRUPPE`, `SORTIERMODI`, `SEITEN` und `RUNDEN`.
- **15-15** (Bericht) nimmt den Runbook-Nachtrag oben auf, zusaetzlich zu den vieren aus 15-03 und 15-04.
- **MESS-05 bleibt ungetickt.** Dieser Plan baut das Werkzeug; das Requirement gehoert an das Phasenende (15-16), obwohl die Frontmatter des Plans es fuehrt.

## Self-Check: PASSED

- `docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh` liegt auf der Platte.
- `backend/tests/test_measurement_scripts.py` liegt auf der Platte.
- `1d3a3ec` und `aa40a3d` stehen in `git log`.
- Keine Loeschung in den beiden Task-Commits.
