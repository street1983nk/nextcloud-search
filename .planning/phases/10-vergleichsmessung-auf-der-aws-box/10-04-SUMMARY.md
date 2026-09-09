---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 04
subsystem: testing
tags: [measurement, shell-scripts, detached-run, watchman, status-observer, oom-proof, language-cases, page-route, permission-rounds, tdd]

# Dependency graph
requires:
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "00-ablauf.md aus Welle 3 als Datei, die hier um die Schritte 96 bis 99b ergaenzt wird, das Muster Urteil-in-Datei-hinter-der-Pipeline, und die Schnittstelle 96-oom-beweis.txt, ohne die 95-spitze.sh nachher mit 12 abbricht"
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "das Gate test_measurement_scripts.py aus Welle 1 mit seinen zwei Geltungsbereichen, das jede neue Datei am Tag ihrer Entstehung prueft"
  - phase: 06.1-launch-haertung
    provides: "scripts/ops/search_load.py mit --password-env und seiner JSON-Antwort, und die zwei Vergleichswerte 1.129,0 ms und 524,0 ms"
  - phase: 09-eigene-ergebnisseite
    provides: "scripts/dev/probe_page_login.sh als Anmeldeweg mit Cookie-Behaelter, requesttoken und Origin-Kopf, der Befund M-03 und die drei p95-Zahlen aus Abschnitt 6.3 des Seitenbudget-Berichts"
  - phase: 07-gemeinsame-embedding-engine
    provides: "DI-07-03 mit MAX_ROUNDS = 3, dem Aufruf von searchCandidates in der Schleife und dem Gruppenbudget von 2.500 ms"
provides:
  - "96-volllauf.sh: der Anstoss des abgesetzten Laufs, Sampler und Statusbeobachter VOR dem Anstoss, die protokollierte Trockenprobe des Lesers, die Gegenprobe nach 360 s und der abgesetzte Start von Waechter und Meldekette"
  - "96b-waechter.sh: Uebergang der Spuren, Ende beider Spuren, OOM-Beweis in 96-oom-beweis.txt vor jedem Eingriff, Vektorbestand, 00-FERTIG vor dem Ruf der Meldekette"
  - "96c-lesen.py: der Leser, der indexed und embedded unter backend liest und die oberste Ebene nie meldet, mit fuenf Zusicherungen im Gate"
  - "96d-statusbeobachter.py: der Statusbeobachter zum ersten Mal im Repo, Cookie-Sitzung mit Origin-Kopf und requesttoken, Aufnahme als Projektion auf zehn Schluessel"
  - "96e-ntfy-watch.sh: die Meldekette in drei Betriebsarten, HTTP-Code jedes Versuchs in 99-ntfy-watch.log, Mail-Fallback an, immer Rueckgabewert 0"
  - "98-sprachfaelle.sh: die zehn Sprachfaelle gegen einen eigenen Nutzer, 39 Dateien ueber WebDAV, Verdikte erst bei leerem Vorrat, Bilanzzeile ueber Faelle"
  - "99-seitenroute.sh: vier Reihen der Ergebnisseite in beiden Anmeldewegen, Rangregel als ceil ohne Interpolation, Erstmessung mit vollem Vektorbestand"
  - "99b-runden.sh: die Rundenzaehlung fuer DI-07-03 in zwei getrennten Faellen, Alltag und provozierter Driftfall, mit Dauer gegen 2.500 ms und 1,5 s"
  - "00-ablauf.md: alle dreizehn Schritte mit Rohdateinamen, Wartefristen und Abbruchbedingungen, dreizehn Ablesestellen ohne Platzhalter, und eine Tabelle aller Rueckgabewerte des Laufs"
affects: [10-05, 10-06, 10-07, box-lauf]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Leseskript wird gegen gestellte Aufnahmen als Unterprozess gefahren, statt einmal trocken von Hand: die Lehre eines Vorfalls wird ein Gate, das ohne Box rot werden kann"
    - "Eine Aufnahme, die committet wird, entsteht als Projektion auf einen geschlossenen Schluesselsatz und nie als Filterliste; ein neues Feld der Quelle kann durch eine Projektion nicht durchsickern"
    - "Ein Passwort erreicht curl ueber eine Konfigurationsdatei mit Modus 600 und ein Formularfeld ueber name@datei, weil -u und --data-urlencode den Wert in die Prozessliste stellen"
    - "Ein Zaehler, der zwei Dinge zaehlen koennte, zaehlt genau eines und sagt welches: Faelle in der Bilanzzeile, Zusicherungen in der Liste darunter"
    - "Wo zwei Urteile sich widersprechen koennten, wird genau eines gedruckt: keine Anfragezeile im Protokoll ist eine Aussage ueber das Protokoll und keine Rundenzahl von null"

key-files:
  created:
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96-volllauf.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96b-waechter.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96c-lesen.py
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96d-statusbeobachter.py
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/96e-ntfy-watch.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/99-seitenroute.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/99b-runden.sh
  modified:
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "96c-lesen.py liest indexed und embedded AUSSCHLIESSLICH unter backend und faellt nicht auf die oberste Ebene zurueck. Genau der Rueckfall war der Fehler von 42c-lesen.py: dort steht das indexed der PHP-Haelfte, das per Bauart 0 bleibt. Fuenf Zusicherungen im Gate machen die falsche Ebene rot, ohne Box"
  - "Der Arbeitsvorrat ist unklar, wenn scheduled ODER running keine Zahl ist, und nie 0. Die Endebedingung des Waechters liest einen Vorrat von 0, also haette ein angenommener Nullwert ihn das Ende eines Laufs erklaeren lassen, dessen Vorrat er nie gesehen hat"
  - "Die Aufnahme des Statusbeobachters ist eine Projektion auf zehn Schluessel und keine Filterliste. Ein neues Feld der Verwaltungsseite kann durch eine Projektion nicht durchsickern, durch einen Filter, der nennt was er entfernt, schon (T-10-21)"
  - "Der Zeitstempel der Aufnahme ist die Uhr des Beobachters und nicht das at der Antwort: was die Zeile belegen muss, ist wann gefragt wurde"
  - "Der OOM-Beweis wird zweimal gelesen, beschriftet, in dieselbe Rohdatei: bei erkanntem Ende VOR jedem Eingriff, und noch einmal am Ende der Nachlaufschritte. Eine Suchlastprobe hebt memory.peak, also waere ein Spitzenwert nach ihr der der Messung und nicht der des Laufs"
  - "Der Waechter schreibt 00-FERTIG und ruft ERST DANACH die Meldekette; die Meldekette selbst endet immer mit 0. Der Vertrag ist die Datei, die Nachricht ist die Zugabe, und das Thema hat am 05.09. von dieser Box mit 403 geantwortet"
  - "Die Bilanzzeile der Sprachfaelle zaehlt Faelle, die Liste darunter Zusicherungen. Fall 1 traegt vier Zusicherungen, und vier rote Zusicherungen eines Falls sind ein roter Fall"
  - "Das Skelett wird vor jedem user:add abgeschaltet und danach zurueckgesetzt, weil Handbuch, Fotoordner und Readme in der Heimat die Zaehlzusicherungen zu Aussagen ueber Dokumente machen wuerden, die niemand gewaehlt hat"
  - "Passwoerter erreichen curl ueber eine Konfigurationsdatei mit Modus 600 und das Anmeldeformular ueber --data-urlencode password@datei. -u und ein Wert im Argument haetten das Gate aus Welle 1 bestanden und trotzdem in der Prozessliste der Box gestanden"
  - "Der Driftfall wird dreiwertig gelesen (Treffer nach der Ruecknahme, Runden je Suche), damit er belegt und nicht behauptet ist; MESS-02 und MESS-03 bleiben Pending, weil dieser Plan null Box-Minuten gekostet hat"

patterns-established:
  - "Die Lehre eines Vorfalls wird ein Unterprozess-Test gegen gestellte Eingaben, nicht ein Handgriff mit Erinnerung"
  - "Ein committetes Messartefakt entsteht als Projektion auf einen geschlossenen Schluesselsatz"
  - "Ein Auswertungsblock wird vor dem Commit gegen vier Faelle trocken gefahren: vollstaendig, mit Ausreisser, unvollstaendig, und ohne beantwortete Anfrage"
  - "Zwei Zahlen, die verwechselbar sind, bekommen zwei Zeilen mit ihrem Namen"

requirements-completed: []
requirements-touched: [MESS-02, MESS-03]

# Metrics
duration: 34min
completed: 2026-09-09
---

# Phase 10 Plan 04: Das Skriptset des abgesetzten Laufs und die drei neuen Messbloecke Summary

**Der 19-Stunden-Lauf kann jetzt nachts allein laufen, weil sein Vertrag eine Datei ist, sein Leser gegen fuenf gestellte Aufnahmen geprueft ist statt gegen die Hoffnung, und sein Beobachter im Repo liegt statt nur auf einer Maschine.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-09-09T08:35:00Z
- **Completed:** 2026-09-09T09:09:00Z
- **Tasks:** 3 von 3
- **Files modified:** 10 (8 neu, 2 ergaenzt)
- **Box-Minuten:** 0, wie geplant
- **Runner-Minuten:** 0

## Accomplishments

- **Die teuerste Lehre der Vorlaeufer ist ein Gate, das ohne Box rot werden kann.** `42c-lesen.py` hat `indexed` und `embedded` auf der obersten Ebene gesucht, der Waechter hat die ganze Nacht Nullen protokolliert, die Suchlastprobe im Nachlauf ist nie gefahren und das Ende waere neun Stunden zu spaet erkannt worden. `96c-lesen.py` liest beide Zahlen unter `backend` und faellt **nicht** zurueck; fuenf Zusicherungen in `test_measurement_scripts.py` fahren es als Unterprozess gegen gestellte Aufnahmen, darunter eine mit `indexed: 8` auf der obersten Ebene und ohne `backend`, die genau dann rot wird, wenn jemand den Rueckfall wieder einbaut.
- **Der Statusbeobachter liegt zum ersten Mal im Repo**, mit dem Anmeldeweg aus `probe_page_login.sh` samt Origin-Kopf, und seine Aufnahme ist eine Projektion auf zehn Schluessel. Zwei weitere Zusicherungen fahren diese Projektion gegen eine Antwort, die drei Beispielpfade an den drei Stellen traegt, an denen die Verwaltungsseite sie wirklich fuehrt: kein Dateiname, kein Pfad, kein Nutzername, kein Schraegstrich ueberlebt sie.
- **Die Maschinenbindung ist raus.** Beide Suchlastproben des Waechters laufen ueber `scripts/ops/search_load.py` mit `--password-env` und den Parametern Nebenlaeufigkeit 1 und zehn Runden, damit ihre Zahlen gegen die 1.129,0 ms und die 524,0 ms des Semantiklaufs stellbar sind. Das Wort des fehlenden Helfermoduls kommt in keiner der neun Dateien vor, und `45-suchlast.py` wird als Grund genannt statt gerufen.
- **Der Vertrag des abgesetzten Laufs ist eine Datei.** Der Waechter schreibt `00-FERTIG` mit Zeitpunkt, Dauer, Urteil und Weckwort und ruft **erst danach** die Meldekette; die Meldekette protokolliert den HTTP-Code jedes Versuchs, faellt bei allem, was kein 2xx ist, auf Mail zurueck, und endet immer mit 0.
- **Die drei Messbloecke, die es in keinem Vorlaeuferbericht gibt, liegen als Skripte vor:** die zehn Sprachfaelle gegen einen eigenen Bestand (Konto-Vorgabe `sprachfall`, ausdruecklich nicht `lasttest`), die Seitenroute in vier Reihen auf beiden Anmeldewegen mit der Rangregel des Vorlaeuferberichts, und die Rundenzaehlung in zwei getrennten Faellen mit ihrer Herstellung.
- **Jeder Auswertungsblock ist trocken gefahren, bevor er committet wurde.** Die Seitenroute-Auswertung gegen vier gestellte Reihen (vollstaendig, mit Ausreisser in Wiederholung 8, vollstaendig, unvollstaendig mit 12 von 20 Werten), die Rundenauswertung gegen vier Faelle (eine Runde, 2,4 Runden, keine beantwortete Anfrage, fehlende Antwortdatei), und die Bilanzzeile der Sprachfaelle gegen vier rote Zusicherungen in einem Fall plus eine in einem zweiten.
- **Kein Regressionsschatten:** ganze Suite 1960 passed / 15 skipped gegen die Grundlinie 1913 / 15, also genau die 47 neuen Zusicherungen (7 eigene plus 8 neue Dateien mal 5 Gate-Zusicherungen) und keine gebrochene alte. `ruff check`, `ruff format --check`, `pyright` und `vulture` ohne Befund, `sh -n` ueber alle zwoelf Shellskripte des Laufverzeichnisses ohne Befund.

## Task Commits

1. **Task 1, RED: das Gate vor den Dateien** , `fe22a02` (test) , sieben Zusicherungen, alle rot, weil die zwei Dateien noch fehlten
2. **Task 1, GREEN: der abgesetzte Volllauf, sein Waechter, sein Leser und sein Beobachter** , `7b5cc39` (feat)
3. **Task 2: die zehn Sprachfaelle auf der Box, als eigener Nutzer** , `b4399c1` (feat)
4. **Task 3: die Seitenroute auf der Zielhardware und die Rundenzaehlung** , `149c89c` (feat)

## Files Created

| Datei | Was sie tut, und was sich gegen den Vorlaeufer geaendert hat |
|---|---|
| `96-volllauf.sh` | Nach `42-semantiklauf.sh`. Zustand vor dem Einschalten (Ablesestelle 8), Sampler mit 5 s und Statusbeobachter mit 120 s **vor** dem Anstoss, dann die protokollierte Trockenprobe des Lesers, dann der Anstoss, dann 360 s gegen die langsamste Uhr und die Gegenprobe mit gezaehlten Poller-Durchgaengen. Neu: die drei Woerter der Trockenprobe sind gleichzeitig der **Startpunkt** des Laufs, und wenn `indexed` dort schon ueber null steht, sagt das Skript ausdruecklich, dass die Laufzeit eine Untergrenze ist. Waechter und Meldekette werden erst nach dem gruenen Urteil abgesetzt gestartet. |
| `96b-waechter.sh` | Nach `42b-wachter.sh`, mit denselben drei Aufgaben, demselben Rundendeckel 340 und denselben Bedingungen. Neu: beide Suchlastproben ueber `search_load.py --password-env` mit Nebenlaeufigkeit 1 und zehn Runden, der OOM-Beweis in `96-oom-beweis.txt` **bei erkanntem Ende** plus ein beschrifteter Nachtrag am Schluss, `00-FERTIG` vor dem Ruf der Meldekette, und ein Rueckgabewert 13 fuer den Rundendeckel und 14 fuer eine leere Aufnahmenreihe. |
| `96c-lesen.py` | Nach der korrigierten Fassung `42c-lesen.py`, mit dem einen Unterschied, der Pitfall 8 schliesst: kein Rueckfall auf die oberste Ebene. Vorrat ist `unklar`, wenn eine der beiden Zahlen fehlt. Immer drei Woerter, immer Rueckgabewert 0, damit der Waechter unter `set -eu` nicht an einer halb geschriebenen Zeile stirbt. |
| `96d-statusbeobachter.py` | Zum ersten Mal im Repo. Cookie-Anmeldung mit Origin-Kopf, danach ein frischer `data-requesttoken` fuer die Sitzung, dann `GET /apps/findling/admin/overview` im festen Intervall. Aufnahme als Projektion auf zehn Schluessel, Zustandswort nur als kurzer Bezeichner, Fehlschlag als Aufnahme mit `fehler` statt als Luecke, verlorene Sitzung wird einmal neu angemeldet. Nur Standardbibliothek. |
| `96e-ntfy-watch.sh` | Nach `43-ntfy-watch.sh`, in drei Betriebsarten (`start`, `senden`, `warten`). HTTP-Code jedes Versuchs in `99-ntfy-watch.log`, Mail-Fallback ueber `mail` oder `sendmail`, Deckel 20 h mit Warnung und 34 h zum Aufgeben. Rueckgabewert immer 0, auch bei falschem Aufruf. |
| `98-sprachfaelle.sh` | Neu. Fuenf Abschnitte: eigener Nutzer (Skelett aus, `user:add --password-from-env`), 39 Dateien ueber WebDAV mit Zahlvergleich, Warten auf leeren Arbeitsvorrat gegen die langsamste Uhr, die zehn Faelle aus `integration.yml` im Wortlaut ihrer Fehlermeldungen, und die Einordnung als Erstmessung neben dem CI-Beleg. Alle zehn laufen, auch nach einem roten. |
| `99-seitenroute.sh` | Neu. Vier Reihen à 20 Wiederholungen plus 5 Aufwaermanfragen, Anmeldeweg in jeder Kopfzeile, Rangregel als `ceil` ohne Interpolation, Vergleich gegen 0,122 s, 0,445 s und 0,538 s und gegen die Decken 1,5 s und 3,0 s. Ausreisser bekommt eine Zeile mit seiner Wiederholungsnummer und bleibt in der Reihe. |
| `99b-runden.sh` | Neu. Fall 1 der Alltag, Fall 2 der provozierte Driftfall (Freigaben an ein zweites Konto, Rechte aufgenommen mit gezaehltem Poller-Durchgang belegt, dann Ruecknahme ohne Wartezeit). Gezaehlt werden Containeraufrufe je Suche, getrennt nach `POST /search` und `POST /snippets`, dazu die Dauer gegen 2.500 ms und 1,5 s. Keine Zeile in `php/`. |
| `00-ablauf.md` | Ergaenzt. Die Schritte 7 und 10 bis 13 tragen jetzt ihre Rohdateinamen, Wartefristen und Abbruchbedingungen; die Platzhalter "Plan 10-04" sind weg. Die Liste der Ablesestellen ist ohne Luecke, mit zwei erklaerten Zusaetzen. Neu: sechs weitere Wartefristen mit ihren Uhren und eine Tabelle aller sechzehn Rueckgabewerte des Laufs. |

## Decisions Made

Die tragenden Entscheidungen stehen im Frontmatter. Vier verdienen den Fliesstext:

**Warum der Leser nicht zurueckfaellt.** `42c-lesen.py` schreibt `indexed = b.get("indexed", d.get("indexed", 0))`. Das ist genau die Zeile, an der der Semantiklauf blind wurde: der Rueckfall liefert das `indexed` der PHP-Haelfte, das per Bauart 0 bleibt, und tut das ohne jedes Anzeichen. Ein Rueckfall auf eine Zahl, die es gibt und die falsch ist, ist teurer als ein Loch: eine Null wird beobachtet und weggeklickt, ein `unklar` faellt auf. `96c-lesen.py` liest deshalb nur unter `backend`, und der Test dazu stellt eine Aufnahme mit `indexed: 8` auf der obersten Ebene: er wird rot, wenn jemand die alte Zeile zurueckschreibt, und er sagt in seinem Docstring warum.

**Warum die Aufnahme eine Projektion ist und keine Filterliste.** T-10-21 handelt davon, dass die Verwaltungsseite Beispielpfade fuehrt und diese Rohdatei committet wird. Eine Liste zu entfernender Schluessel deckt die Felder, die heute existieren; die Seite hat in Phase 4 zweimal ein Feld dazubekommen, und ein neues Feld haette sich still durch den Filter bewegt. Die Projektion nimmt neun Schluessel oberster Ebene plus `backend` mit genau zwei Zahlen, und ein Zustandswort muss dem Muster eines kurzen Bezeichners entsprechen, sonst faellt es weg. Der Test fuettert die Projektion mit einer Antwort, die drei Beispielpfade traegt, und prueft, dass in der Aufnahme nicht einmal ein Schraegstrich steht.

**Warum der OOM-Beweis zweimal gelesen wird.** Der Plan gibt die Reihenfolge des Vorlaeufers vor: `occ findling:index`, Suchlast mit vollem Bestand, Beobachter beenden, OOM-Beweis, Vektorbestand. Das Akzeptanzkriterium verlangt aber den Beweis "vor jedem Eingriff". Beides zusammen geht nicht, denn eine Suchlastprobe **ist** ein Eingriff: sie hebt `memory.peak`, und der Spitzenwert danach beschreibt die Messung statt den Lauf. Die Loesung ist keine Wahl zwischen den beiden, sondern zwei beschriftete Lesungen in derselben Datei: die erste unmittelbar bei erkanntem Ende, bevor irgendetwas passiert, die zweite am Schluss. `95-spitze.sh nachher` braucht nur, dass die Datei existiert und nicht leer ist, also ist die Schnittstelle aus Welle 3 mit der ersten Lesung schon erfuellt.

**Warum die Bilanzzeile Faelle zaehlt.** Der erste Entwurf zaehlte Zeilen in der Fehlerdatei, und der Rauchtest hat gezeigt, was das bedeutet: Fall 1 traegt vier Zusicherungen, also haette ein einziger roter Fall 1 die Zeile `sprachfaelle bestanden 6 von 10` erzeugt, obwohl neun Faelle gruen waren. Eine Bilanzzeile, die vier Zusicherungen eines Falls als vier Faelle meldet, ist im Bericht eine falsche Zahl mit dem Anschein der Genauigkeit. Jetzt zaehlt die Zeile Faelle, die Liste darunter Zusicherungen, und beide sagen im Text, was sie zaehlen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Der Beobachter braucht einen frischen `requesttoken`, sonst ist jede Aufnahme ein Fehler**

- **Found during:** Task 1, beim Nachlesen, wie die Verwaltungsseite ihre eigene Route ruft
- **Issue:** Der Plan beschreibt den Anmeldeweg mit Cookie-Behaelter und Origin-Kopf und sagt, dass ein GET der Seite keinen eigenen requesttoken braucht (das gilt fuer `PageController::index()`, weil es `NoCSRFRequired` traegt). `SettingsController::overview()` traegt das Attribut **nicht**: `php/js/admin.js` schickt bei jedem Poll `requesttoken: document.head.dataset.requesttoken`, und `scripts/dev/aio_install_check.sh` faellt genau darauf zurueck, wenn Basic-Auth abgelehnt wird. Ohne den Kopf haette der Beobachter 19 Stunden lang Fehleraufnahmen geschrieben, der Waechter haette dreimal `unklar` gelesen, nichts erkannt und am Rundendeckel geendet: derselbe Schaden wie Pitfall 8, nur mit einer anderen Ursache.
- **Fix:** Nach der Anmeldung wird eine Seite geholt und `data-requesttoken` daraus gelesen; jeder Abruf der Verwaltungsroute traegt den Kopf. Wird die Sitzung als verloren gemeldet (`SessionGone`, 401, 403, 412), meldet der Beobachter sich einmal neu an und holt einen neuen Token.
- **Files modified:** `96d-statusbeobachter.py`
- **Verification:** Trockenlauf gegen eine nicht erreichbare Adresse: Rueckgabewert 4 ohne Passwort, 3 bei abgelehnter Anmeldung, beides mit benannter Ursache auf stderr
- **Committed in:** `7b5cc39`

**2. [Rule 2 - Missing critical functionality] Der OOM-Beweis steht vor der Suchlastprobe des Nachlaufs, nicht danach**

- **Found during:** Task 1, beim Abgleich der Reihenfolge des Plans mit seinem eigenen Akzeptanzkriterium
- **Issue:** Siehe Fliesstext. Die Reihenfolge des Vorlaeufers legt den Beweis hinter zwei Eingriffe, die `memory.peak` heben.
- **Fix:** Zwei beschriftete Lesungen in `96-oom-beweis.txt`, die erste bei erkanntem Ende vor jedem Eingriff.
- **Files modified:** `96b-waechter.sh`, `00-ablauf.md` (Abschnitt 3 erklaert die Teilung)
- **Verification:** `sh -n` ohne Befund; die erste Lesung liegt vor dem ersten `occ`-Aufruf des Nachlaufs
- **Committed in:** `7b5cc39`

**3. [Rule 2 - Missing critical functionality] Der Waechter stirbt nicht, wenn der Leser nichts sagt**

- **Found during:** Task 1
- **Issue:** `42b-wachter.sh` schreibt `set -- $(tail -1 ... | python3 42c-lesen.py)` und liest danach `$1`, `$2`, `$3`. Unter `set -u` ist das der Tod des Waechters, sobald der Leser einmal nichts ausgibt, etwa weil die Datei noch nicht existiert oder der Interpreter fehlt. Ein Waechter, der in Runde 3 von 340 endet, ist ein Lauf ohne Beobachtung.
- **Fix:** Die Lesung wandert erst in eine Variable und wird auf `unklar unklar unklar` vorbelegt; die drei Felder tragen zusaetzlich Vorgabewerte. Der Waechter zaehlt ausserdem die brauchbaren Lesungen und endet mit 14, wenn es keine einzige gab: dann ist sein Urteil eine Aussage ueber den Beobachter und nicht ueber den Lauf.
- **Files modified:** `96b-waechter.sh`
- **Verification:** `sh -n` ohne Befund; der Zweig ist in der Schleife vor jeder Auswertung
- **Committed in:** `7b5cc39`

**4. [Rule 2 - Missing critical functionality] Das Skelett wird vor jedem `user:add` abgeschaltet**

- **Found during:** Task 2, beim Lesen des Nutzeranlage-Schritts von `integration.yml`
- **Issue:** Der Plan verlangt einen Nutzer, dessen Heimat "ausschliesslich `testdata/corpus` enthaelt". `occ user:add` legt aber das Skelett mit Handbuch, Fotoordner und Readme in jede neue Heimat. `integration.yml` setzt `skeletondirectory` genau deshalb vor dem Anlegen auf leer und schreibt den Grund dazu. Ohne diesen Schritt waeren die Zaehlzusicherungen Aussagen ueber Dokumente, die niemand gewaehlt hat, und ein `length == 1` haette aus dem falschen Grund gehalten oder gebrochen.
- **Fix:** Der vorige Wert wird gelesen, `skeletondirectory` auf leer gesetzt, das Konto angelegt, und am Ende wird der vorige Wert zurueckgeschrieben (oder der Schluessel geloescht, wenn er vorher nicht gesetzt war). Dasselbe in `99b-runden.sh` fuer das Driftkonto, dort mit dem zweiten Grund: eigene Dateien des Kontos wuerden den Recheck ueberleben und den Driftfall stumpf machen.
- **Files modified:** `98-sprachfaelle.sh`, `99b-runden.sh`
- **Verification:** `sh -n` ohne Befund; der Zweig steht vor `user:add` und der Rueckbau im letzten Abschnitt
- **Committed in:** `b4399c1`, `149c89c`

**5. [Rule 2 - Missing critical functionality] Kein Passwort in einer Kommandozeile, auch nicht in den Gestalten, die das Gate nicht kennt**

- **Found during:** Task 2 und Task 3
- **Issue:** T-10-27 verbietet Passwoerter in Kommandozeilen, und das Gate aus Welle 1 prueft `--password `, `--password=` und die Kurzform hinter bestimmten Programmen. Die drei Gestalten, die dieser Plan gebraucht haette, sind davon **keine**: `curl -u konto:passwort` (so macht es `71-ocrphase.sh`), `--data-urlencode "password=$PW"` fuer das Anmeldeformular, und `env VAR=wert sudo -E python3 ...` fuer die Umgebungsvariable von `search_load.py`. Alle drei stellen den Wert in die Prozessliste der Box und in jedes Protokoll, das den Befehl aufzeichnet, und alle drei haetten das Gate bestanden.
- **Fix:** `curl -K datei` mit einer Konfigurationsdatei (Modus 600, unter `mktemp -d` mit Modus 700), wie es `aio_install_check.sh` vorzeichnet; `--data-urlencode "password@datei"` fuer das Formularfeld, mit der Datei ohne Zeilenumbruch, weil ein Umbruch als `%0A` mitreisen wuerde; und eine Zuweisung mit `export` in der Shell statt `env`, weil eine Zuweisung in keiner Argumentliste steht. Jede der drei Stellen traegt den Grund als Kommentar.
- **Files modified:** `98-sprachfaelle.sh`, `99-seitenroute.sh`, `99b-runden.sh`
- **Verification:** Gate gruen; zusaetzlich von Hand geprueft, dass keine der neun Dateien `-u "` mit einem Passwort, `password=$` oder `env FINDLING` traegt
- **Committed in:** `b4399c1`, `149c89c`

**6. [Rule 1 - Bug] Die Bilanzzeile der Sprachfaelle haette Zusicherungen als Faelle gemeldet**

- **Found during:** Task 2, im Rauchtest der Zaehllogik
- **Issue:** Der erste Entwurf zaehlte Zeilen in der Fehlerdatei. Fall 1 traegt vier Zusicherungen, also haette ein einziger roter Fall 1 die Zeile `sprachfaelle bestanden 6 von 10` erzeugt, und der Bericht haette vier gebrochene Faelle behauptet, die es nicht gab. Bei fuenf roten Zusicherungen in zwei Faellen waere die Zahl auf 5 gefallen.
- **Fix:** Jeder Fall setzt eine Variable `FALL`, `fail()` schreibt die Fallnummer in eine Datei und den Wortlaut in eine zweite; die Bilanzzeile zaehlt eindeutige Fallnummern, die Liste darunter Zusicherungen, und beide Zeilen sagen, was sie zaehlen.
- **Files modified:** `98-sprachfaelle.sh`
- **Verification:** Rauchtest mit vier roten Zusicherungen in Fall 1 und einer in Fall 8: `sprachfaelle bestanden 8 von 10`, `rote faelle 2, rote zusicherungen 5`; der gruene Fall liefert `10 von 10` und zwei Nullen
- **Committed in:** `b4399c1`

**7. [Rule 1 - Bug] Die Rundenzaehlung haette sich bei leerem Protokoll selbst widersprochen**

- **Found during:** Task 3, im Trockenlauf des Auswertungsblocks
- **Issue:** Bei null Anfragezeilen im Zugriffsprotokoll druckte der Block zwei Urteile untereinander: `befund eine Runde je Suche` (weil 0 durch 10 unter der Schwelle liegt) und `befund das Zugriffsprotokoll traegt keine Anfragezeile`. Zwei widersprechende Urteile in einer Rohdatei sind schlimmer als eines, das fehlt: der Bericht haette das erste zitiert.
- **Fix:** Genau ein Urteil wird gedruckt. Keine Anfragezeile ist eine Aussage ueber das Protokoll und keine Rundenzahl von null.
- **Files modified:** `99b-runden.sh`
- **Verification:** Trockenlauf in drei Faellen (10/10 Aufrufe, 24/0 Aufrufe, 0/0 Aufrufe): je genau eine `befund`-Zeile
- **Committed in:** `149c89c`

**8. [Rule 2 - Missing critical functionality] Der Auswertungsblock der Rundenzaehlung prueft `max_ms`, bevor er es liest**

- **Found during:** Task 3, aus Deviation 4 der 10-03-SUMMARY
- **Issue:** `search_load.py` schreibt `p50_ms`, `p95_ms` und `max_ms` nur, wenn mindestens eine Anfrage beantwortet wurde. Der Driftfall ist genau der Fall, in dem Anfragen fehlschlagen koennen, und ein `KeyError` haette die Rohdatei mit einem Abschnittstitel und einem Traceback beendet.
- **Fix:** Derselbe Schluesselzweig wie in `95-spitze.sh`, mit `failure_kinds` in der Ausgabe; zusaetzlich ein Zweig fuer eine fehlende Antwortdatei.
- **Files modified:** `99b-runden.sh`
- **Verification:** Trockenlauf mit einem Bericht ohne `max_ms` und mit einem fehlenden Pfad: je eine benannte Zeile, Rueckgabewert 0
- **Committed in:** `149c89c`

**9. [Rule 1 - Bug] MESS-02 und MESS-03 wurden nicht abgehakt, obwohl das Frontmatter sie fuehrt**

- **Found during:** Zustands-Update nach Task 3
- **Issue:** Das Frontmatter nennt `requirements: [MESS-02, MESS-03]`. MESS-02 verlangt, dass der **Vergleichslauf** keine Regression zeigt, MESS-03 den Bericht in `docs/measurements`. Dieser Plan hat zehn Dateien geschrieben, die Box nicht angefasst, keine Rohdatei erzeugt und keinen Bericht. Derselbe Fehlgriff ist in Welle 1 passiert und zurueckgenommen worden.
- **Fix:** `requirements.mark-complete` nicht aufgerufen; `REQUIREMENTS.md` unveraendert, alle drei Kennungen weiter `Pending`.
- **Files modified:** keine (`.planning/REQUIREMENTS.md` ausdruecklich nicht angefasst)
- **Verification:** `grep MESS-0 .planning/REQUIREMENTS.md` zeigt drei offene Kaestchen und drei `Pending`-Zeilen; die Datei steht in keinem Commit dieses Plans
- **Committed in:** dieser Metadaten-Commit

**10. [Rule 1 - Bug] Drei Zustandsbefehle des SDK haben wieder falsche oder leere Werte geschrieben**

- **Found during:** Zustands-Update
- **Issue:** Wie in den Wellen 2 und 3: `state.add-decision` schrieb `[Phase ?]` vor jede Entscheidung, `state.update-progress` meldete "Progress field not found in STATE.md" und liess `completed_plans` auf 20, `state.record-metric` und `state.add-decision` lehnten Positionsargumente ab und brauchten Flags, `state.record-session` liess `stopped_at` auf `10-03`, und `roadmap.update-plan-progress` setzte das Kaestchen von Plan 04 nicht, weil die Phase-10-Plaene als Kaestchenliste stehen.
- **Fix:** Die fuenf Vermerke auf `[Phase 10]` gesetzt, `completed_plans` auf 21, `stopped_at` und `Stopped at` auf `Completed 10-04-PLAN.md`, die Zeile "Naechster Schritt" auf Welle 5 samt der drei Voraussetzungen der Anfahrt, und das Kaestchen von Plan 04 von Hand gesetzt.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** `grep "Phase ?"` ohne Treffer, `completed_plans: 21`, `stopped_at: Completed 10-04-PLAN.md`, `| Phase 10 P04 | 34min | 3 tasks | 10 files |`, `- [x] 10-04-PLAN.md`
- **Committed in:** dieser Metadaten-Commit

### Kleinere Abweichungen, ohne eigene Regel

- **`96e-ntfy-watch.sh` hat drei Betriebsarten statt einer.** Der Plan verlangt eine Meldekette, die der Waechter ruft (`senden`), und beschreibt sie nach `43-ntfy-watch.sh`, das ein Wartemodus war. Beides ist gebaut, plus `start`, und der Kopf sagt ausdruecklich, dass eine doppelte Abschlussmeldung Absicht ist: zwei Sender, die einander nicht kennen, sind die billigste Versicherung gegen den, der nicht laeuft.
- **`96-volllauf.sh` startet Waechter und Meldekette selbst**, abgesetzt mit `setsid nohup` und eigenen Protokolldateien, damit der Lauf mit einem Befehl abgesetzt ist. Bei rotem Urteil startet es den Waechter **nicht**, weil 340 Runden gegen einen Lauf, der nie begonnen hat, ein Tag und eine halbe Nacht Nichts sind.
- **Sampler und Beobachter werden im `tee`-Block gestartet, aber vollstaendig umgeleitet.** Ein Hintergrundprozess, der die Standardausgabe des Blocks offen haelt, haette verhindert, dass `tee` je endet.
- **Die Trockenprobe des Lesers ist gleichzeitig der Startpunkt des Laufs.** Nicht verlangt, aber die drei Woerter stehen ohnehin da, und eine Laufzeit, die von einem Start gezaehlt wird, der kein Nullstart war, ist eine Untergrenze und muss als eine berichtet werden.
- **`99-seitenroute.sh` nennt `page=3` und die drei Vergleichszahlen im Kopf** in ihrer deutschen Schreibweise, weil die Adresse im Rumpf aus Variablen entsteht und eine Zahl, die nur gerechnet wird, im Bericht nicht wiederfindbar ist.
- **Reihe C wird gegen die 0,122 s der Sitzung gestellt**, mit dem Hinweis, dass sich die Seitentiefe unterscheidet. Der Plan verlangt einen Vergleich "gegen die Entsprechung aus Abschnitt 6.3", und die Entsprechung eines Sitzungsweges ist der Sitzungswert; die tiefe Seite hat gar keine.
- **`99b-runden.sh` liest den Driftfall dreiwertig.** Treffer nach der Ruecknahme grosser null heisst, dass die Freigabe noch wirksam war und dies nicht der Driftfall ist; null Treffer mit mehr als einer Runde heisst, der Fall ist erzeugt; null Treffer mit einer Runde heisst, der Vorfilter wusste schon Bescheid. Ohne diese drei Zeilen waere die Zahl behauptet statt belegt.
- **Beide Skripte mit `jq` verweigern mit 18, wenn `jq` fehlt**, statt zwanzig Zusicherungen einzeln scheitern zu lassen. Kein Paket wird installiert.
- **Das Driftkonto bleibt stehen.** Ein `user:delete` loest eine Raeumung im Index aus, und die waere eine Bewegung mitten in einer Messreihe. Der Grund steht in der Rohdatei.

---

**Total deviations:** 10 auto-fixed (4x Rule 1 Bug, 6x Rule 2 fehlende kritische Funktionalitaet) plus neun kleinere Abweichungen ohne eigene Regel
**Impact on plan:** Kein Scope Creep, keine Fremdabhaengigkeit, kein Paket installiert, `backend/uv.lock` unveraendert, keine Zeile unter `php/`. Sechs der zehn drehen sich um denselben Punkt: eine Zahl, die falsch sein kann und trotzdem wie eine Messung aussieht. Genau die Fehlerart, deren Reparatur der Gegenstand dieser Phase ist.

## Issues Encountered

**Die Verwaltungsroute ist keine `NoCSRFRequired`-Route.** Das war der eine Punkt, an dem der Plan eine Voraussetzung uebernommen hat, die fuer eine **andere** Route gilt. `PageController::index()` traegt das Attribut, `SettingsController::overview()` nicht, und der Unterschied ist zwischen den beiden Dateien nur zu sehen, wenn man beide aufschlaegt. Gefunden wurde er nicht am PHP, sondern an zwei Aufrufern: `php/js/admin.js` schickt den Kopf bei jedem Poll, und `scripts/dev/aio_install_check.sh` faellt ausdruecklich auf ihn zurueck. Zwei Aufrufer, die dasselbe tun, sind ein Vertrag.

**Ein Passwort hat drei Gestalten, die kein Gate kennt.** Das Gate aus Welle 1 prueft `--password `, `--password=` und eine Kurzform hinter fuenf Programmen. Dieser Plan brauchte Basic-Auth in `curl`, ein Formularfeld und eine Umgebungsvariable fuer einen Unterprozess unter `sudo`, und die naheliegende Schreibweise war in allen drei Faellen ein Wert in der Argumentliste. Das Gate waere gruen geblieben. Der Ausweg stand jedes Mal schon im Repo: `-K` mit Konfigurationsdatei in `aio_install_check.sh`, `name@datei` in der curl-Dokumentation, und eine Shell-Zuweisung statt `env`.

**Der Rueckgabewert einer Pipeline gehoert `tee`, und das gilt auch fuer diese fuenf Skripte.** Das Muster aus Welle 3 ist unveraendert uebernommen: jedes Urteil wird im Block in eine Datei unter `$WORK` geschrieben und nach der Pipeline gelesen, dort steht der `exit`. Neu ist nur, wie viele Urteile es geworden sind: neun Rueckgabewerte in vier Dateien, alle in `00-ablauf.md` tabelliert.

**`jq` ist eine Annahme ueber die Box.** Beide neuen Bloecke mit JSON-Zusicherungen brauchen es, `71-ocrphase.sh` und `integration.yml` benutzen es, aber ob es auf dieser Box liegt, ist nirgends belegt. Statt es zu installieren (was in dieser Phase ohnehin kein Skript darf) verweigern beide Skripte mit 18 und sagen, was fehlt. Das ist eine Zeile fuer die Anfahrt von Welle 5.

## User Setup Required

None. Der Plan hat keine Cloud-Ressource angefasst, die Box nicht gestartet und keine Runner-Minute verbraucht.

Fuer Welle 5 sind drei Dinge vorzubereiten, die dieser Plan nur benennen kann: der A-Record `loadtest.infranode.dev` oder einer seiner zwei Rueckfaelle, `jq` auf der Box, und die zwei Passwortdateien (`admin` und `lasttest`) an den Stellen, die die Vorgaben `PWFILE` erwarten.

## Next Phase Readiness

**Bereit fuer Welle 5.** Was diese Welle hinterlaesst:

- **Die Schnittstelle aus Welle 3 ist erfuellt:** `96b-waechter.sh` schreibt `96-oom-beweis.txt` bei erkanntem Ende, vor jedem Eingriff. `95-spitze.sh nachher` findet die Datei und bricht nicht mit 12 ab.
- **Der Lauf ist mit einem Befehl abgesetzt:** `96-volllauf.sh` startet Sampler, Beobachter, Waechter und Meldekette und endet mit `96-VOLLLAUF-GESTARTET`; danach ist die naechste Aktion das Lesen von `00-FERTIG`.
- **Neun neue Rueckgabewerte, die im Bericht auftauchen koennen:** 13 Rundendeckel, 14 kein Vorrat beziehungsweise keine Aufnahme, 15 Upload unvollstaendig, 16 Vorrat nicht leer, 17 Sprachfall rot, 18 kein `jq`, 19 Reihe unvollstaendig, 20 Zugriffsprotokoll ohne Anfragezeile, 21 Driftfall nicht erzeugbar. Alle in `00-ablauf.md` Abschnitt 5.
- **Drei Annahmen, die der Lauf beantwortet und die kein Skript vorwegnehmen kann:** ob das Zugriffsprotokoll des Containers Anfragezeilen traegt (sonst ist die Rundenzaehlung eine Aussage ueber das Protokoll), ob die zehn Sprachfaelle gegen einen eigenen Bestand halten (Annahme A7, deshalb abbrechbar), und ob der Driftfall in dem Zeitfenster erzeugbar ist, das eine Ruecknahme laesst.

**Was dieser Plan ausdruecklich nicht getan hat:** keine Zeile in `php/`, keine Zeile der Vorlaeuferskripte geaendert, kein Hilfsskript angefasst. `42d-bestand.py`, `search_load.py`, `rss_sampler.sh` und `44-korpus-pruefsumme.py` werden gerufen, wie sie sind. Der latente Schluesselfehler in `67-nebenlaeufigkeit.sh` bleibt stehen, weil seine Rohdaten daneben liegen.

## Known Stubs

Keine im Sinne von unverdrahteten Daten. Was ohne Box pruefbar war, ist geprueft: `96c-lesen.py` und die Projektion von `96d-statusbeobachter.py` laufen unter sieben Zusicherungen im Gate, die drei Auswertungsbloecke sind gegen gestellte Eingaben trocken gefahren (Seitenroute vier Reihen, Rundenzaehlung vier Faelle, Bilanzzeile zwei Faelle), und `sh -n` deckt alle zwoelf Shellskripte des Verzeichnisses.

Die Docker-, `occ`-, WebDAV- und cgroup-Haelften koennen ohne Box nicht gefahren werden. Das ist keine Auslassung, sondern der Gegenstand der Welle 5.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die zehn Eintraege mit Disposition `mitigate`:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-10-19 | `96c-lesen.py` liest ausschliesslich unter `backend`, ohne Rueckfall; fuenf Zusicherungen fahren es als Unterprozess gegen gestellte Aufnahmen, eine davon mit `indexed` auf der obersten Ebene und ohne `backend` |
| T-10-20 | `00-FERTIG` wird vor dem Ruf der Meldekette geschrieben und traegt Zeitpunkt, Dauer, Urteil und Weckwort; `96e-ntfy-watch.sh` protokolliert den HTTP-Code jedes Versuchs in `99-ntfy-watch.log`, faellt bei allem ausser 2xx auf Mail zurueck und endet immer mit 0 |
| T-10-21 | Die Aufnahme entsteht als Projektion auf neun Schluessel oberster Ebene plus `backend` mit zwei Zahlen; das Zustandswort muss einem kurzen Bezeichnermuster entsprechen; ein Test fuettert die Projektion mit drei Beispielpfaden und prueft, dass nicht einmal ein Schraegstrich uebrig bleibt |
| T-10-22 | `search_load.py` statt `45-suchlast.py`, `96d-statusbeobachter.py` zum ersten Mal im Repo, und keine der neun Dateien nennt das fehlende Helfermodul; `machine_shapes_in_code` liefert `[]` fuer alle |
| T-10-23 | Eigener Nutzer mit Vorgabe `sprachfall`, ausdruecklich nicht `lasttest`; der Kopf nennt die sechs kollidierenden Woerter des Lastkorpus mit ihren Zeilennummern; das Skelett wird abgeschaltet, damit die Heimat wirklich nur den Korpus traegt |
| T-10-24 | Jede der vier Reihen nennt ihren Anmeldeweg in einer eigenen Zeile, beide Wege werden gemessen, und die Differenz der Reihen A und B wird als Preis des Anmeldeweges ausgewiesen (Befund M-03) |
| T-10-25 | Zwei getrennte Faelle mit getrennten Rohdateien, eine dreiwertige Lesung des Driftfalls, und ein eigener Abschnitt, der verlangt, dass der Bericht beide Faelle mit ihrer Herstellung nennt |
| T-10-26 | Alle drei Bloecke laufen ueber die OCS-Route beziehungsweise die Seitenroute, also ueber den finalen PHP-Recheck; `git diff --name-only cf01bda HEAD` nennt keine Datei unter `php/` |
| T-10-27 | `occ user:add --password-from-env` mit `OC_PASS`, `--password-env` bei `search_load.py`, `curl -K` mit Konfigurationsdatei (Modus 600) statt `-u`, `--data-urlencode password@datei` statt eines Wertes im Argument, und eine Shell-Zuweisung mit `export` statt `env VAR=wert` |
| T-10-SC | Kein Paket installiert. Die beiden neuen Python-Dateien importieren ausschliesslich Standardbibliothek (`argparse`, `http.cookiejar`, `json`, `os`, `re`, `sys`, `time`, `urllib`, `datetime`, `pathlib`, `typing`); `backend/uv.lock` unveraendert. Fehlt `jq`, wird nichts installiert, sondern mit 18 verweigert |

Zusaetzlich, weil es die Grenze "Messskript zur cgroup" betrifft: keine der neun Dateien enthaelt `docker stats`. Jede Speicherzahl kommt aus `/sys/fs/cgroup/system.slice/docker-<CID>.scope/`, und `96b-waechter.sh` loest die Container-Kennung selbst auf.

## Self-Check: PASSED

| Geprueft | Ergebnis |
|----------|----------|
| Alle zehn Dateien aus `files_modified` liegen auf der Platte | zehnmal `FOUND` |
| Alle vier Commits in `git log` | `fe22a02`, `7b5cc39`, `b4399c1`, `149c89c` |
| `git diff --name-only cf01bda HEAD` | genau die zehn Dateien des Plans, keine elfte |
| Loeschungen in den vier Commits | keine (`--diff-filter=D` leer) |
| Datei unter `php/` im Diff | keine |
| `sh -n` ueber alle zwoelf Shellskripte des Laufverzeichnisses | ohne Befund |
| Zusicherung Task 1 (der Prueflauf des Plans) | `ok` |
| Zusicherung Task 2 (zehn Begriffe, sieben Dateinamen, beide `length`-Formen) | `ok` |
| Zusicherung Task 3 (Anmeldewege, Adressen, drei Vorwerte, Rangregel, MAX_ROUNDS, Ablaufplan) | `ok` |
| Trockenlauf der Seitenroute-Auswertung | vier Reihen: vollstaendig, mit Ausreisser in Wiederholung 8 benannt, vollstaendig, unvollstaendig mit 12 von 20; Urteil `nein` |
| Trockenlauf der Rundenauswertung | vier Faelle: 1,0 Runden, 2,4 Runden, keine beantwortete Anfrage, fehlende Antwortdatei; je genau eine `befund`-Zeile |
| Rauchtest der Bilanzzeile | 4 rote Zusicherungen in Fall 1 plus 1 in Fall 8 ergibt `bestanden 8 von 10`, `rote faelle 2, rote zusicherungen 5`; gruen ergibt `10 von 10` |
| Trockenlauf des Beobachters | Rueckgabewert 4 ohne Passwort, 3 bei nicht erreichbarer Instanz, beides mit benannter Ursache |
| `pytest tests/test_measurement_scripts.py -q` | 168 passed (121 vor diesem Plan, 47 neue) |
| `pytest -q` (ganze Suite) | 1960 passed / 15 skipped (Grundlinie 1913 / 15) |
| `ruff check .`, `ruff format --check .` in `backend/` | All checks passed, 120 files already formatted |
| `ruff check` und `ruff format --check` ueber das Laufverzeichnis | All checks passed, 4 files already formatted |
| `pyright` | 0 errors, 0 warnings, 0 informations |
| `vulture src tests --min-confidence 80` | ohne Befund |
| Wagenruecklauf, Em-Dash oder En-Dash in den neun Dateien | keiner |
| `docker stats` in einer der neun Dateien | kein Treffer |
| Maschinenpfad in Code-Zeilen der neun Dateien | `machine_shapes_in_code` liefert `[]` fuer alle |
| `.planning/REQUIREMENTS.md` unveraendert | nicht im Diff |
| `CLAUDE.md` unveraendert | nicht im Diff |

## TDD Gate Compliance

Task 1 traegt `tdd="true"`, und die Reihenfolge ist eingehalten:

| Gate | Commit | Beleg |
|------|--------|-------|
| RED | `fe22a02` (`test(10-04)`) | 7 failed, 121 passed. Alle sieben scheitern an den zwei Dateien, die es noch nicht gab |
| GREEN | `7b5cc39` (`feat(10-04)`) | 138 passed, danach 153 mit den drei Shellskripten desselben Commits |
| REFACTOR | keiner | Nicht noetig: die zwei Python-Dateien standen nach dem ersten gruenen Lauf formatiert und lintfrei da |

Die Tasks 2 und 3 tragen kein `tdd`-Kennzeichen und haben keine Produktionslogik erzeugt; das Gate aus Welle 1 laeuft trotzdem gegen jede ihrer Dateien und war bei jedem Commit gruen (121, 153, 158, 168).

---
*Phase: 10-vergleichsmessung-auf-der-aws-box*
*Completed: 2026-09-09*
