---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 01
subsystem: testing
tags: [ci, flake, webdav, http-423, pytest, timeouts, dependabot, tantivy]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: den zurueckgestellten Punkt DI-11-05 samt Merker "erst wiederholen, dann suchen"
  - phase: 15-messphase-eine-box-anfahrt
    provides: den Audit-Befund L-11 und den Einzelfall des Laufs 35470079862
provides:
  - write_revision als einzige WebDAV-Schreibstelle der Integrationsstrecke, mit enger Wiederholung nur auf HTTP 423
  - ARRIVAL_SECONDS als eigene Frist der Warte-auf-Ankunft-Faelle, getrennt von der Obergrenze BLOCKED_WARM_SECONDS
  - docs/audits/2026-09-phase-16/flake-register.md mit den drei bekannten Flake-Staemmen
  - ignore-Eintrag fuer tantivy in .github/dependabot.yml, mit dem Reindex-Grund daneben
affects: [16-07-versionsbump, 16-09-upgrade-beweis, 16-13-launch-haertung, 16-14-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Enge Wiederholung: genau ein Fehlercode wird gewartet, jeder andere scheitert sofort und laut, und die Zahl der Treffer steht im Protokoll"
    - "Eine Zeitkonstante pro Frage: die Ankunftsfrage bekommt eine lange Frist, die Obergrenzenfrage behaelt die kurze"
    - "Eine Regel, die im Zustand eines fremden Dienstes lebt, wird in eine Datei des Repositoriums geholt"

key-files:
  created:
    - docs/audits/2026-09-phase-16/flake-register.md
  modified:
    - .github/workflows/integration.yml
    - backend/tests/test_search_endpoint.py
    - .github/dependabot.yml

key-decisions:
  - "write_revision steht in mutation.sh und nicht im Mutationsschritt allein, weil damit ALLE drei Schreibvorgaenge der Strecke (die Erstfassung, die acht Runden, der neunte) durch dieselbe Wiederholung gehen und die Schreibadresse genau einmal im Quelltext steht"
  - "Der Ausstieg bei erschoepfter Obergrenze und bei jedem fremden Code ist exit 1 aus der Funktion heraus und nicht return 1, damit der Schritt auch dann rot endet, wenn ein spaeterer Umbau die Fehlerbehandlung des Aufrufers verliert"
  - "Nur drei der sechs Wartestellen wandern auf ARRIVAL_SECONDS; die beiden 0,25-Sekunden-Stellen (nichts ist passiert) und die Blockade des Stand-in-Laufs (Obergrenze) bleiben kurz, weil eine lange Frist dort entweder jede gruene Fahrt teuer machen oder die Aussage aufloesen wuerde"
  - "parity-login wird nicht gefixt, sondern beobachtet: zwei Fehlschlaege desselben Schritts an zwei verschiedenen Aesten derselben Funktion (404 der Ergebnisseite am 11.09., verweigerte Anmeldung am 19.09.) lassen die Deutung offen, und ein Fix ohne Deutung waere eine Vermutung im Erzeugnis"

patterns-established:
  - "Flake-Register: je Stamm eine Kennung, der Auftrag mit Schritt, die letzte rote Laufnummer mit Datum, die gefahrene Gegenprobe, ein Verdikt und der Fix beziehungsweise der Merker"
  - "Flake-Behandlung gehoert in den ersten Block einer Abgabephase und nicht in die Abgabewoche"

requirements-completed: []
requirements-partial:
  - "HART-01: DI-11-05 ist erledigt, DI-11-02/03/06 bleiben bei Plan 16-04; das Requirement wird erst dort abgehakt"

# Metrics
duration: 35 min
completed: 2026-09-21
---

# Phase 16 Plan 01: Flake-Haertung, Register und tantivy-Ignoranweisung Summary

Die drei bekannten Flake-Stämme dieses Repositoriums sind behandelt oder benannt,
bevor die Abgabewoche beginnt: eine enge 423-Wiederholung im Mutationsschritt, eine
zweite Zeitkonstante für die Warte-auf-Ankunft-Fälle, ein Register mit Laufnummern
und Gegenproben, und der tantivy-Pin hat seine Regel jetzt in einer Datei statt nur
im Zustand eines fremden Dienstes.

## Was gebaut wurde

**Task 1, die enge 423-Wiederholung (DI-11-05), Commit `a856563`.**
`write_revision` liegt in `mutation.sh`, also in der Werkzeugdatei, die alle drei
Schritte des Mutationsfalls einlesen. Damit steht die Schreibadresse genau einmal
im Quelltext (vorher dreimal), und alle drei Schreibvorgänge gehen durch dieselbe
Behandlung: die Erstfassung, die acht Runden der Schleife und der neunte, der
`final`-Vorgang. `curl` läuft mit `-w` auf den HTTP-Code und ohne `-f`, damit der
Code lesbar ist statt in einem Rückgabewert 22 zu verschwinden. Nur `423` wartet
und wiederholt, höchstens dreimal mit zwei Sekunden Pause; jeder andere Code außer
`2xx` beendet den Schritt sofort mit `::error::` und dem Code in der Meldung. Am
Ende des Schritts steht `the lock was hit N time(s)`, und null ist die erwartete
Zahl.

**Task 2, die zweite Zeitkonstante (L-11), Commit `a27ec2c`.**
`ARRIVAL_SECONDS = 30.0` trägt ab jetzt die Frage "hat der Lauf stattgefunden",
`BLOCKED_WARM_SECONDS = 5.0` nur noch die Frage "hat der Handler gewartet". Drei
Aufrufstellen sind umgestellt, darunter der lastempfindliche Single-Flight-Fall;
die Stand-in-Blockade, an der die Obergrenze hängt, bleibt bei 5,0, und die beiden
0,25-Sekunden-Stellen bleiben kurz, weil sie eine Abwesenheit behaupten.

**Task 3, Register und Ignoranweisung, Commit `9b24613`.**
`docs/audits/2026-09-phase-16/flake-register.md` führt `mutation-423`,
`single-flight-zeit` und `parity-login` in einer Tabelle, je mit Laufnummer,
Datum, Gegenprobe, Verdikt und Fix beziehungsweise Merker; über der Tabelle steht
der Satz, dass die erste Handlung bei einem roten Ast die Wiederholung ist.
`.github/dependabot.yml` trägt im `uv`-Eintrag einen `ignore`-Block für `tantivy`
über major, minor und patch, mit dem Grund daneben: Index-Format v7 ab 0.26.2
bedeutet einen Reindex auf jeder bestehenden Installation, also bewegt sich der
Pin nur mit Reindex-Plan.

## Verifikation

| Prüfung | Ergebnis |
|---|---|
| `integration.yml` parst als YAML | ja |
| Schreibadresse im Quelltext | 1 Stelle, vorher 3 |
| `bash -n` über die beiden Mutationsschritte | grün |
| Verhalten von `write_revision` gegen einen Stand-in für `curl` | 423/423/201 gibt zwei Sperrtreffer und Rückgabe 0; dauerhaft 423 endet nach drei Wiederholungen mit Code 1; 500 endet sofort mit Code 1; 204 geht ohne Wiederholung durch |
| `pytest tests/test_search_endpoint.py` | 50 bestanden |
| Single-Flight-Fall zehnmal hintereinander | zehnmal grün |
| ruff, ruff format --check, pyright, vulture | alle grün |
| volle Suite | 2.394 bestanden / 15 übersprungen, Skipzahl unverändert |
| `dependabot.yml`, uv-Eintrag trägt `ignore` für tantivy | ja |
| Register nennt drei Stämme | ja |
| Dependabot-PR #11 | nur gelesen, nicht angefasst |

Die Gegenprobe zum Verhalten von `write_revision` ist gefahren und nicht vermutet:
die Funktion wurde aus der Workflow-Datei extrahiert und mit einem Stand-in für
`curl` gegen vier Antwortfolgen laufen gelassen. Beim ersten Anlauf meldete der
Stand-in immer 423, weil die Zuweisung des Codes in einer Subshell läuft und der
Zähler des Stand-ins dort nicht zurückkam. Das war ein Fehler der Prüfvorrichtung
und nicht der Funktion, und er ist mit einem Zähler auf Platte behoben worden.

## Abweichungen vom Plan

**1. Die Schreibfunktion liegt in `mutation.sh` statt allein im Mutationsschritt.**
Der Auftragstext sagt "Baue im Schritt ... eine Schreibfunktion", das
Abnahmekriterium daneben verlangt genau eine Schreibstelle im Quelltext. Beides
zugleich ist nur zu haben, wenn die Funktion in der gemeinsamen Werkzeugdatei
steht, denn der erste Schreibvorgang des Falls liegt in einem anderen Schritt. Der
Nebeneffekt ist erwünscht: auch dieser erste Schreibvorgang ist jetzt gegen die
Sperre abgesichert.

**2. Das Register benutzt echte Umlaute im Fließtext.**
Der Auftragstext verlangt "ASCII-Umschrift wie im übrigen Verzeichnis". Das übrige
Verzeichnis `docs/audits/` schreibt seinen Fließtext mit echten Umlauten und nur
die Überschriften ohne, und die Projektregel sagt dasselbe. Regel und Verzeichnis
haben Vorrang vor der Beschreibung.

**3. HART-01 wird hier nicht abgehakt.**
Das Requirement deckt DI-11-02, 03, 05 und 06; erledigt ist in diesem Plan nur
DI-11-05. Die drei anderen liegen bei Plan 16-04, und dort wird das Requirement
abgehakt. `.planning/REQUIREMENTS.md` bleibt deshalb unveraendert.

Keine weiteren Abweichungen, kein Rule-4-Fall, keine neue Abhängigkeit. Unter
`backend/src/findling` und unter `php/` ist keine Zeile geändert, also war kein
Baumhash nachzuziehen.

## Was der nächste Plan wissen muss

- Das Register ist die Stelle, an der die Abgabepläne 16-13 und 16-14 nachsehen,
  bevor sie einen roten Ast untersuchen. Es ist kein Abschlussdokument: kommt in
  dieser Phase ein vierter Stamm dazu, gehört er dort hinein.
- `parity-login` bleibt offen und unbehandelt. Wer ihn aufnimmt, liest den älteren
  Befund `parity-login-probe-404` daneben.
- Die 423-Wiederholung ist noch nie in einer echten CI-Fahrt gelaufen, weil die
  Sperre selten ist. Belegt sind bisher das Verhalten der Funktion gegen einen
  Stand-in und die Syntax des Schritts; der erste echte Lauf der
  Integrationsstrecke ist die Feldprobe.
- Dependabot-PR #11 liegt weiterhin beim Owner.

## Known Stubs

Keine.

## Self-Check: PASSED

Vier geänderte beziehungsweise angelegte Dateien auf Platte nachgesehen, drei
Commits in `git log` nachgesehen, alle vorhanden.
