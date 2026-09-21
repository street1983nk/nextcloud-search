---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 13
subsystem: audit-und-haertung
tags: [hart-01, launch-haertung, phasenaudit, asvs, geheimnis-gegenprobe, flake, owner-abnahme]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: die zwoelf Plaene 16-01 bis 16-12, deren Ergebnisse dieser Bericht gegen die acht Pfade der Owner-Regel haelt
  - phase: 15-messphase-eine-box-anfahrt
    provides: die Befundliste mit M-01, M-02 und der L-Reihe, die Hausform des Phasenaudits und die vier Auflagen A1 bis A4
provides:
  - docs/audits/2026-09-phase-16/README.md mit Haertungsmatrix, Gate-Protokoll, ASVS-Durchgang, Geheimnis-Gegenprobe, Auflagenstand, Erfolgskriterien und Befundliste
  - die zehnte Familie des Geheimnis-Gates (Namensform des zweiten Anbieters) samt drei Ausnahmeeintraegen
  - ein deterministischer Ersatz fuer den Flake-Stamm single-flight-zeit, dessen erster Fix nicht getragen hat
  - deferred-items.md mit der zu Ende gefuehrten Phase-15-Liste und drei neuen LOW-Verdikten
  - die Owner-Abnahme der Launch-Haertung im Wortlaut
affects: [16-14-abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Fix, der nicht getragen hat, bekommt im Register einen Nachtrag und keine stille Korrektur; ein Register, das nur die erfolgreichen Fixe fuehrt, beantwortet die Frage, die niemand stellt"
    - "Eine Gegenprobe wechselt nicht nur das Muster, sondern auch die Reichweite und die Art der Erkennung: sechs fremde Familien plus eine Entropiemessung, ueber die Aenderungsmenge statt ueber ein Verzeichnis"
    - "Ein Gate, das Ressourcen an ihrem Namen erkennt, ist so breit wie die Zahl der Anbieter, die es kennt; jede neue Herkunft braucht eine eigene Familie"
    - "Ein Testfall, der auf eine lose Aufgabe wartet, wird auf der eigenen Schleife gefahren statt durch einen Client, der sein Tor nach jeder Anfrage schliesst"
    - "Die Haertungsmatrix ist eine Tabelle mit Beleg je Zeile und ersetzt damit den Vorsatz, ausgiebig geprueft zu haben"

key-files:
  created:
    - docs/audits/2026-09-phase-16/README.md
  modified:
    - backend/tests/test_search_endpoint.py
    - backend/tests/test_public_artifacts.py
    - docs/performance.md
    - docs/audits/2026-09-phase-16/flake-register.md
    - .planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md

key-decisions:
  - "M-16-01 ist als MEDIUM gefuehrt und nicht als LOW, obwohl kein Nutzer davon etwas merkt: vier rote von acht abgeschlossenen Laeufen einer Werkbank sind kein Flattern mehr, und die Werkbank ist eine der sieben, die am Tag gleichzeitig gruen sein muessen"
  - "M-16-02 ist als MEDIUM gefuehrt, in derselben Abwaegung, die Phase 15 fuer M-02 getroffen hat: der praktische Schaden ist gering, die Luecke im Verfahren nicht. Eine andere Einstufung waere bequemer und unehrlicher gewesen"
  - "Der Fall des Stammes single-flight-zeit wandert auf die Schleife des Falls und bekommt KEINE laengere Frist. Die Frist aus 16-01 bleibt trotzdem stehen, weil die Trennung der zwei Fragen unabhaengig richtig ist und zwei weitere Stellen sie benutzen"
  - "L-16-01 wird nicht gefixt, obwohl er dieselbe Wurzel hat. Der Nachbarfall macht seine Aussage genau ueber zehn Anfragen DURCH DIE ROUTE, und ein Umbau auf die Schleife wuerde die Aussage ersetzen statt sie zu haerten"
  - "Die Redaktion in performance.md benutzt die Platzhalterform, die das Dokument an einer vierten Stelle schon vorher selbst benutzt hat, statt eine zweite Form einzufuehren; eine Form, die den Wert und seine Art zugleich nennt, waere doppelt gemoppelt"
  - "Der Bericht nennt keine Kennung und keine Adresse, auch nicht die aus seinem eigenen Befund M-16-02: ein Bericht, der sie zitierte, waere die Datei, die sie traegt"
  - "Die Commits stehen in der Reihenfolge Fixe zuerst, Bericht danach, und nicht in der Reihenfolge der Aufgaben; ein Bericht, der seine Befunde als behoben nennt, bevor der Fix existiert, waere in dem Moment falsch, in dem er committet wird"

patterns-established:
  - "Nach einem Push wird die Laufliste des Pushes gelesen und nicht nur der Lauf, den der Plan erwartet; jeder nicht-gruene Lauf wird in der SUMMARY benannt, bevor sie geschrieben ist (L-16-02)"
  - "Die acht Pfade der Owner-Haertungsregel bekommen je eine Zeile mit Beleg und Urteil, und Zeile 8 (alle Audits erneut) ist die, aus der die Befunde kommen"

requirements-completed: [HART-01]
requirements-partial: []

# Metrics
duration: 150 min
completed: 2026-09-21
---

# Phase 16 Plan 13: Launch-Haertung, Phasenaudit und Owner-Abnahme Summary

Die Haertung vor der Abgabe ist eine Tabelle mit acht belegten Zeilen statt eines Vorsatzes, das Phasenaudit liegt vor dem Tag und kennt kein CRITICAL und kein HIGH, und es hat zwei MEDIUM gefunden, die beide in derselben Ausfuehrung behoben sind: ein Fix dieser Phase hatte nicht getragen, und ein Gate kannte die Namensform nur eines von zwei Anbietern.

## Die Owner-Abnahme, im Wortlaut

Vorgelegt wurden am 21.09.2026 per strukturierter Rueckfrage: die Haertungsmatrix mit dem Ergebnis je Zeile, die Befundliste mit Schweregrad und Stand, der Stand der aus Phase 15 weitergereichten Befunde, die fuenf Erfolgskriterien je mit Urteil, der Stand der vier Auflagen einschliesslich dessen, was NICHT belegt ist, und die Vorbedingungen des Plans 16-14.

**Antwort des Owners, im Wortlaut:**

> "Abgenommen"

**Ohne Auflagen.** Damit ist die Bedingung der Owner-Regel vom 06.09.2026 erfuellt: die Abgabe startet erst nach der Abnahme der Haertung, und sie ist erteilt. Plan 16-14 darf beginnen.

Keine Kostenzeile: in dieser Phase ist keine Box gelaufen und kein Deckel abgerufen worden.

## Was gebaut wurde

### Der Bericht (`cfa5eae`)

`docs/audits/2026-09-phase-16/README.md`, 533 Zeilen, nach dem Muster der Phasen 14 und 15, mit acht Abschnitten:

1. **Die Haertungsmatrix**, acht Zeilen, je mit dem Womit, dem Beleg und dem Urteil. Die Zeile, die am meisten Arbeit gekostet hat, ist die zweite: dass die Berechtigungskette unberuehrt ist, steht dort als **leere Ausgabe eines Diffs** ueber acht Orte seit dem letzten Commit der Phase 15 und nicht als Satz. Die eine beruehrte Datei der Kette zeigt 42 hinzugefuegte und **eine** geaenderte Zeile, und die eine ist eine Protokollzeile, die ein Feld dazubekommt.
2. **Das Gate-Protokoll**, sechs Stufen in einem Zug, dazu die Skipzahl gegen den Stand vor der Phase und der CI-Stand des heutigen Baums.
3. **Der ASVS-Durchgang** ueber V2, V4, V6, V7, V12 und V14, mit V3 und V5 als je einer Zeile, weil eine weggelassene Kategorie von einer geprueften nicht zu unterscheiden ist. Schwerpunkt ist V7, und dort liegt auch ein Befund.
4. **Die Geheimnis-Gegenprobe** mit einem anderen Verfahren, siehe unten.
5. **Der Performance-Durchgang** ueber die drei Stellen, an denen diese Phase etwas gebaut hat, das Laufzeit oder Platz kosten kann.
6. **Der Stand der vier Auflagen**, je mit dem, was NICHT belegt ist.
7. **Die Befundliste** mit Schwere und Stand, dazu zwei Punkte, die keine Befunde sind, und der Stand der elf aus Phase 15 weitergereichten.
8. **Was dieser Bericht nicht sagt**, als eigener Pflichtabschnitt.

### Die Gegenprobe, die anders ist als das Gate

Die Regel vom 02.08.2026 hat in dieser Phase einen neuen Anlass: **das Gate aus Plan 16-02 ist jetzt selbst das Muster der Umsetzung.** Es ist ueber `docs/` gelaufen und ueber jeden Commit dieser Phase, und eine Form, die seine zehn Regeln nicht kennen, haette es jedes Mal uebersehen.

Die Gegenprobe unterscheidet sich deshalb in beidem:

- **Reichweite:** alle **72 Dateien, die diese Phase committet hat**, in jedem Verzeichnis, also auch ausserhalb von `docs/`. Danach ein zweiter Lauf ueber alle **405 Dateien unter `docs/`**, nach der Lehre von M-02.
- **Verfahren:** sechs Musterfamilien, die das Gate nicht fuehrt (Token in drei punktgetrennten Teilen und Anmeldekopfzeile, Zugangsdaten in einer Adresse, die Markenpraefixe sechs fremder Dienste, das Anwendungspasswort in fuenf Gruppen, ein Hexgeheimnis hinter einem Bezeichner, der kein Pruefsummenwort ist, und jede Postadresse), plus **eine Messung, die ueberhaupt kein Muster ist**: die Shannon-Entropie zugewiesener Werte.

**Null Treffer in den vier gefaehrlichen Familien**, in beiden Laeufen. Die uebrigen Treffer sind je einzeln erklaert: vierzehn Pruefsummen, eine einzige zur Veroeffentlichung bestimmte Kontaktadresse an sieben Stellen, und vierzehn Pfade, die die Entropiemessung findet, weil ein Pfad viele verschiedene Zeichen hat.

**Die Ausnahmeliste ist eigens geprueft**, und zwar nicht von dem Gate, das sie fuehrt: 49 Eintraege, kuerzester Grund 95 Zeichen (Mindestlaenge ist 20), kein doppelt benutzter Grund, kein Grund unter acht Woertern, **kein Grund, der ein Versprechen auf einen spaeteren Plan statt einer Begruendung ist**. Der letzte Punkt ist der wichtige: genau diese Sorte Satz stand vor Plan 16-05 sechsmal auf der Liste.

### Die zwei Fixe (`8f0d7f8`)

**M-16-01, der unangenehme.** Der Fix des Flake-Stammes `single-flight-zeit` aus Plan 16-01 hat nicht getragen. Der Fall `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` ist am 21.09.2026 **viermal** in CI rot gegangen, in den Laeufen 35586354661, 35594647359, 35596116820 und 35597353833, jedes Mal **mit** der neuen Frist von dreissig Sekunden, also vier rote von acht abgeschlossenen Laeufen der Werkbank seit dem Fix.

Die Deutung "lastempfindlich" war falsch, und die roten Laeufe beweisen es: ein Lauf, der mit dreissig Sekunden Geduld scheitert, scheitert nicht an der Geduld. Die Ursache ist ein Wettlauf: der Testclient oeffnet je Anfrage ein eigenes Tor und schliesst es wieder, und die Aufgabe, die der Handler mit `create_task` bestellt, ist eine lose Aufgabe auf dieser Schleife. Bekommt sie ihren ersten Zeitschlitz nicht, bevor das Tor zugeht, laeuft sie nie.

Der Fall wird deshalb auf der Schleife des Falls gefahren und wartet die Aufgabe ab, genau wie sein Nachbar, der denselben Grund seit Phase 14 im Docstring traegt. **Nichts ist dabei weicher geworden**: der Fall wartet jetzt auf die Aufgabe statt auf ein Ereignis, und er liest die Zahl der Laeufe, nachdem der Lauf fertig ist, statt mittendrin. Zwoelf von zwoelf Wiederholungen gruen.

**M-16-02.** Die vier Familien des Gates, die eine Ressource an ihrem Namen erkennen, kennen die Namensform **eines** Anbieters. Dieses Projekt hat bei zweien gemietet, und der Name, den der zweite fuer den Einhaengepunkt eines Datentraegers bildet, traegt dessen Kennung. Er stand nach der Bereinigung aus Plan 16-05 weiter an drei Stellen in einem redigierbaren Dokument unter `docs/`. **Gefunden hat ihn nicht das Gate, sondern die Gegenprobe dieses Berichts**, und genau dafuer gibt es sie.

Behoben in vier Teilen: das Dokument traegt an allen drei Stellen die Platzhalterform, die es an einer vierten schon vorher benutzt hat; das Gate hat eine zehnte Familie mit Kommentar, sauberer und mutierter Probe; die drei Rohdateien der gefahrenen Anfahrt vom 04.09.2026, in denen der Name bleibt, stehen mit je einem eigenen Grund auf der Ausnahmeliste; und die Mutationsprobe ist gefahren. Mit dem Wert zurueck im Dokument meldet das Gate `['performance.md']` statt der leeren Liste, ohne ihn ist es gruen. Der Baum ist danach zurueckgesetzt worden; die Probe liegt in keinem Commit.

**Das Flake-Register** hat einen Nachtrag bekommen, der sagt, dass der erste Fix nicht getragen hat, und warum. Ein Register, das nur die erfolgreichen Fixe fuehrt, beantwortet die Frage, die niemand stellt.

### Die Verdikte der drei LOW-Befunde (`cfa5eae`)

`deferred-items.md` traegt drei neue Abschnitte, je mit Befund, Verdikt, Begruendung und Zieladresse, und dazu die **zu Ende gefuehrte Phase-15-Liste**: je Befund eine Zeile mit seinem heutigen Stand, damit niemand ihn aus sieben SUMMARY-Dateien zusammensuchen muss. M-01 steht dort ausdruecklich als **teilerfuellt**, mit dem Satz, was noch aussteht.

## Die Befundliste

| ID | Schwere | Befund | Stand |
|---|---|---|---|
| M-16-01 | MEDIUM | Der Fix des Flake-Stammes `single-flight-zeit` aus 16-01 hat nicht getragen; vier rote CI-Laeufe am 21.09.2026 mit der neuen Frist. Die Ursache ist ein Wettlauf mit dem Tor des Testclients und nicht die Frist | **behoben**, 12 von 12 Wiederholungen gruen, Nachtrag im Flake-Register |
| M-16-02 | MEDIUM | Das Geheimnis-Gate kannte die Namensform nur eines von zwei Anbietern; der Datentraegername des zweiten stand weiter dreimal in einem redigierbaren Dokument | **behoben**: Redaktion, zehnte Familie, drei Ausnahmeeintraege, Mutationsprobe gefahren |
| L-16-01 | LOW | Derselbe Wettlauf steckt im Nachbarfall der zehn Suchen; nie rot, weil zehn Anfragen zehn Chancen sind | **weitergereicht** mit Adresse: der naechste Plan, der die Warmlauf-Faelle anfasst |
| L-16-02 | LOW | Ein Plan liest den Lauf, den er erwartet, und nicht die Laufliste des Pushes; genau so blieben vier rote Laeufe unbemerkt | **weitergereicht** als Verfahrensregel im Wortlaut, Adresse: 16-14 und der Planer der naechsten Phase |
| L-16-03 | LOW | Der Stamm `parity-login` bleibt offen und ist in dieser Phase nicht aufgetreten | **weitergereicht**, beobachtet, Merker gilt |

**Kein CRITICAL, kein HIGH.** Zwei Punkte sind als "kein Befund" gefuehrt: die zur Veroeffentlichung bestimmte Kontaktadresse der Enterprise-Zeile und eine Installationskennung einer am 04.09.2026 abgebauten Testinstanz in einer Rohdatei.

## Die fuenf Erfolgskriterien der Phase, wie vorgelegt

| Nr. | Kriterium (Kurzform) | Urteil | Artefakt |
|---|---|---|---|
| 1 | DI-11-02/03/05/06 abgearbeitet oder dokumentiert entschieden | **erfuellt** | 16-01 (423-Wiederholung und Flake-Register), 16-04 (Vorlaufsonde und sieben Verdikte in deferred-items) |
| 2 | Connector-Satz dreisprachig in beiden Haelften, Katalog-Gates gruen, keine Gedankenstriche, keine Backticks oder Tabellen | **erfuellt** | 16-12, 67 Faelle mit Anzahlpruefung; Lauf 35603906800 |
| 3 | Upgrade 1.1.0 auf 1.2.0 Ende zu Ende in CI bewiesen, Suche nicht stumm | **erfuellt** | Lauf 35594647362, bestaetigt in 35603906848 |
| 4 | Messzahl im Gleichschritt an drei Stellen | **erfuellt** | 16-12, je Stelle ein Mutationsfall |
| 5 | v1.2.0 eingereicht, zweimal HTTP 201 | **offen, planmaessig** | Plan 16-14, beginnt nach dieser Abnahme |

Keines ist umgedeutet worden.

## Der Stand der vier Auflagen, einschliesslich des nicht Belegten

- **A1:** beide Nachfolgefassungen statisch abgenommen. **NICHT belegt: die Wirkung.** Keine ist gefahren, neben keiner liegt eine Rohdatei.
- **A2:** vollstaendig, und in diesem Plan um die fehlende Familie ergaenzt. **NICHT belegt: die Reichweite ueber `docs/` hinaus.** Die Gegenprobe ist einmal ueber die anderen Verzeichnisse gelaufen, und ein Lauf ist kein Gate.
- **A3:** Instrumentierung gebaut und von beiden Seiten geprueft. **NICHT belegt: eine Zahl auf Zielhardware.** Es gibt keine, weil diese Phase keine Box gefahren hat.
- **A4:** erfuellt und abgenommen ("Zweig a, zustimmen"), mit dem Vorbehalt seines Weges: keine echte Nextcloud mit AppAPI und HaRP, keine Maschine des Zieltyps, keine harte Speichergrenze, andere OCR-Fassung als im Auslieferungsabbild.

## Gate-Protokoll

Gefahren am 21.09.2026 auf der Entwicklungsmaschine, in der Reihenfolge von `.github/workflows/python.yml`, `pyright` mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`.

| Stufe | Befehl | Ausgang |
|---|---|---|
| 1 | `uv run ruff check .` | gruen, All checks passed |
| 2 | `uv run ruff format --check .` | gruen, 126 Dateien bereits formatiert |
| 3 | `uv run pyright` | gruen, 0 errors, 0 warnings, 0 informations |
| 4 | `uv run vulture src tests --min-confidence 80` | gruen, keine Ausgabe |
| 5 | `uv run pytest -q` (VOLLE Suite), vor den Fixen | gruen, **2487 bestanden / 15 uebersprungen**, 210,78 s |
| 5b | `uv run pytest -q` (VOLLE Suite), nach den Fixen | gruen, **2491 bestanden / 15 uebersprungen**, 214,07 s |
| 6a | `uv run ruff check --config pyproject.toml ../scripts` | gruen |
| 6b | `uv run ruff format --config pyproject.toml --check ../scripts` | gruen, 10 Dateien bereits formatiert |

**Die Skipzahl ist unveraendert 15** gegen den Stand vor der Phase (2394 / 15), bei 97 Faellen mehr. Eine gewachsene Skipzahl waere ein Befund gewesen.

Auf Commit 67661e5 sind **sechs Werkbaenke gleichzeitig gruen**: Python gates 35603907050, Resilience 35603906880, HaRP deploy 35603906848, PHP and store metadata gates 35603906800, Multi-arch image 35603906783, Integration 35603906685.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Flake-Fix aus 16-01 hat nicht getragen**

- **Found during:** Aufgabe 1, beim Nachsehen der Laufliste fuer das Gate-Protokoll
- **Issue:** Vier rote CI-Laeufe derselben Werkbank am 21.09.2026, alle mit der Frist aus 16-01, keiner in einer SUMMARY genannt.
- **Fix:** Der Fall laeuft auf der Schleife des Falls und wartet die bestellte Aufgabe ab; das Flake-Register traegt den Nachtrag.
- **Files modified:** `backend/tests/test_search_endpoint.py`, `docs/audits/2026-09-phase-16/flake-register.md`
- **Commit:** `8f0d7f8`

**2. [Rule 2 - fehlende kritische Funktionalitaet] Das Gate kannte nur einen Anbieter**

- **Found during:** Aufgabe 1, in der eigenen Gegenprobe
- **Issue:** Der Datentraegername des zweiten Anbieters stand nach der Bereinigung weiter dreimal in `docs/performance.md`, und keine Familie des Gates konnte ihn sehen.
- **Fix:** Redaktion des Dokuments, zehnte Familie im Gate mit sauberer und mutierter Probe, drei Ausnahmeeintraege fuer die Rohdateien, Mutationsprobe gefahren.
- **Files modified:** `docs/performance.md`, `backend/tests/test_public_artifacts.py`
- **Commit:** `8f0d7f8`

**3. [Rule 3 - blockierende Regel] Eine async-Funktion darf das Dateisystem nicht fragen**

- **Found during:** Aufgabe 2, beim ersten `ruff check` nach dem Umbau
- **Issue:** Der umgebaute Fall behielt die Zusicherung `warm_ground.is_dir()`, und die Regel ASYNC240 verbietet sie in einer async-Funktion. Der Nachbarfall liest denselben Pfad aus demselben Grund als Namen.
- **Fix:** dieselbe Form wie der Nachbar, mit dem Grund im Kommentar.
- **Files modified:** `backend/tests/test_search_endpoint.py`
- **Commit:** `8f0d7f8`

### Bewusste Abweichung vom Plan

**Die Reihenfolge der Commits ist Fixe zuerst, Bericht danach**, und nicht die Reihenfolge der Aufgaben. Der Plan sieht einen Commit je Aufgabe vor, Aufgabe 1 den Bericht und Aufgabe 2 die Fixe. Ein Bericht, der seine Befunde als behoben nennt, bevor der Fix existiert, waere aber in dem Moment falsch, in dem er committet wird, und ein Bericht, der sie als offen nennt, waere es eine Stunde spaeter. Die Fixe stehen deshalb in `8f0d7f8`, der Bericht mit ihrem Ergebnis in `cfa5eae`.

**Die Dateiliste des Plans ist um drei Dateien groesser als angekuendigt.** Angekuendigt waren `README.md` und `deferred-items.md`; dazu gekommen sind die drei Dateien der zwei Fixe. Das ist keine Ausweitung, sondern die Anweisung der Aufgabe 2 ("jeder Befund ab MEDIUM wird VOR dem Phasenabschluss gefixt") an einem Ort, an dem der Plan die Befunde noch nicht kennen konnte.

## Auth Gates

Keine.

## Known Stubs

Keine. Der Bericht traegt keinen Platzhalterabschnitt, und beide Fixe sind vollstaendig verdrahtet und je mit einer Probe belegt, die rot werden kann.

## Threat Flags

Keine neue Angriffsflaeche. Die fuenf Bedrohungen des Plans sind je belegt: T-16-48 (ein Audit, das sein eigenes Verfahren als Gegenprobe benutzt) durch sechs fremde Familien plus eine Entropiemessung und durch die eigens geprueften Gruende der Ausnahmeliste; T-16-49 (die Berechtigungskette wird unbemerkt beruehrt) durch den leeren Diff in Zeile 2 der Matrix; T-16-50 (eine gewachsene Skipzahl versteckt abgeschaltete Faelle) durch die Skipzahl im Vergleich, unveraendert 15; T-16-51 (der Bericht zitiert selbst Kennungen) durch den Lauf des Gates und der Gegenprobe ueber den Bericht; T-16-SC gegenstandslos, keine Abhaengigkeit und kein Installationsbefehl.

## Was offen bleibt

- **Ob der zweite Fix von M-16-01 in CI traegt, ist nicht bewiesen.** Er ist auf dieser Maschine zwoelfmal gruen, und genau das war der erste Fix auch. Der Beweis ist der naechste Push, und dort gilt die neue Regel aus L-16-02.
- **Die sieben gleichzeitig gruenen Tag-Laeufe** stehen aus. Sechs Werkbaenke sind auf dem heutigen Baum gleichzeitig gruen; die siebte laeuft erst auf einem Tag.
- **M-01 bleibt teilerfuellt.** Die Zahl auf Zielhardware entsteht auf einer Box und nirgends sonst.
- **Die drei Commits dieses Plans sind nicht gepusht**, und kein Tag ist gesetzt.

## Self-Check: PASSED

- `docs/audits/2026-09-phase-16/README.md`: vorhanden, 533 Zeilen, enthaelt "Befundliste" und dreimal "Flake-Register".
- `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/deferred-items.md`: vorhanden und ergaenzt, reines ASCII, kein Gedankenstrich, kein gesperrtes Wort.
- `backend/tests/test_search_endpoint.py`, `backend/tests/test_public_artifacts.py`, `docs/performance.md`, `docs/audits/2026-09-phase-16/flake-register.md`: vorhanden und geaendert.
- Commits `8f0d7f8`, `cfa5eae` und `baff223`: in `git log` vorhanden.
- `git diff --diff-filter=D` ueber die Commits dieses Plans: keine geloeschte Datei.
- Alle verify-Befehle beider Aufgaben gruen, volle Suite 2491 bestanden / 15 uebersprungen.
