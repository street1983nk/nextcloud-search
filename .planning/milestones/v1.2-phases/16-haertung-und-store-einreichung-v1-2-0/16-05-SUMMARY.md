---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 05
subsystem: docs-gates
tags: [a2, m-02, l-10, geheimnisregel, vokabularregel, platzhalter, ausnahmeliste]

# Dependency graph
requires:
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: das Geheimnis- und Vokabular-Gate ueber docs/ samt der Ausnahmeliste aus Plan 16-02 und ihrer Ratsche
  - phase: 15-messphase-eine-box-anfahrt
    provides: die Befunde M-02 (58 Werte in 18 Dateien) und L-10 (das gesperrte Wort ohne Gate)
provides:
  - vier redigierte Dokumente unter docs/ (performance.md, install-check.md, admin-page.md, dev-setup.md), die Kennungen und Adressen nur noch als Platzhalter tragen
  - eine Platzhalter-Legende in backend/tests/test_public_artifacts.py, gehalten von einem Fall in beide Richtungen
  - eine von 50 auf 46 Eintraege geschrumpfte Ausnahmeliste, jeder Eintrag mit seinem eigenen Grund
affects: [16-12-phasenaudit, 16-13-launch-haertung, naechste-anfahrt]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Platzhalter benennt die ART des Wertes und nie den Wert; die Form steht als Legende im Gate und nicht in einer Zusammenfassung"
    - "Die Legende wird in beide Richtungen gegen den Baum gehalten: ein unbenutzter Eintrag ist Dekoration, ein nicht eingetragener Platzhalter ist ein Tippfehler, den niemand sieht"
    - "Bereinigen heisst neuer Commit obendrauf, nie rebase, nie filter-branch, nie erzwungener Push"
    - "Rohdaten und Skripte gefahrener Anfahrten werden nicht nachtraeglich redigiert: eine redigierte Rohdatei ist kein Beleg mehr"

key-files:
  created: []
  modified:
    - docs/performance.md
    - docs/install-check.md
    - docs/admin-page.md
    - docs/dev-setup.md
    - backend/tests/test_public_artifacts.py

key-decisions:
  - "Die Platzhalterform ist einmal festgelegt und ueberall gleich benutzt: <instanzkennung>, <volumekennung>, <sicherheitsgruppe>, <adresse-der-box>. Die im Plan vorgeschlagene fuenfte Form <adresse-des-arbeitsplatzes> ist NICHT eingefuehrt, weil in den redigierbaren Dokumenten keine Adresse eines Arbeitsplatzes steht; eine Legendenzeile ohne Fundstelle waere Dekoration und faellt durch den neuen Fall"
  - "<snapshotkennung> steht als fuenfte Zeile in der Legende, weil das Runbook diese Form fuer das Argument seiner Befehlszeile schon vor diesem Plan benutzt hat. Der Plan hat die Form uebernommen statt eine zweite zu erfinden"
  - "Die Korpus-Snapshotkennung bleibt stehen, in performance.md, im Runbook, im v1.2-Bericht und im Phase-15-Audit. Sie ist der Beispielfall aus Entscheid E2 der 16-CONTEXT.md, sie benennt die EINE Ressource, die der Betreiber am 11.09.2026 ausdruecklich behalten hat, und eine Wiederherstellungsanweisung, die umbenennt, wovon sie wiederherstellt, ist nicht ausfuehrbar"
  - "Die oeffentliche Abbildkennung I-01 bleibt in Runbook und Phase-15-Audit stehen (Gruppe B des Plans), weil sie ein oeffentliches Abbild des Anbieters benennt und fuer jedes Konto derselben Region gilt"
  - "runbook-messbox.md ist NICHT redigiert worden. Der Plan nennt es in Gruppe B als Traeger der Abbildkennung, und seine Dateiliste fuehrt es nicht als zu aenderndes Artefakt; seine drei Eintraege haben stattdessen ihren richtigen Grund bekommen"
  - "Die Kopfzeile eines Schluesselpaares im Runbook (Familie pem-privatschluessel) bleibt: sie ist eine Anweisung, wie eine Datei anfaengt, und kein Schluessel. Das ist eine dritte Art der Gruppe B gegenueber den zwei Arten, die der Plan aufzaehlt, und sie steht hier benannt statt still"
  - "Versionsnummern aus vier Gruppen (Kern 6.6.87.2, Server 34.0.3.2 und 33.0.8.2) bleiben stehen: sie sind keine Adressen, und die Familie muster-der-umsetzung kann die beiden Formen nicht auseinanderhalten. Die Eintraege der beiden Dokumente nennen jetzt genau das als Grund"
  - "Das gesperrte Wort ist auch in seinen Mehrzahlformen ersetzt worden, obwohl die Familie sie wegen der Endung nicht sieht. Der Plan zaehlt sie zu den 13 englischen Vorkommen der Installationsanleitung; sie sind aber deutsche Prosa, und die Regel des Betreibers gilt der Sprache und nicht dem Suchmuster"
  - "Der Skriptname store-archive.sh und die woertlich zitierte englische CI-Ausgabe bleiben unveraendert: ein Dateiname ist Code, und ein veraendertes Zitat waere eine Faelschung des Belegs (E-H2)"
  - "Der Ausschluss-Beispielordner der Verwaltungsanleitung heisst jetzt Ablage. Die Kommentare in php/lib/Service/ExclusionService.php und php/js/admin.js benutzen weiter den alten Beispielnamen; das Gate reicht ueber docs/ und nicht ueber den Quellcode, und eine Umbenennung dort waere ausserhalb dieses Plans"

patterns-established:
  - "Eine Ausnahmeliste schrumpft nur, wenn ein Fall die veralteten Eintraege rot macht; die Ratsche aus 16-02 hat in diesem Plan zum ersten Mal gezogen"
  - "Wo der Wert zur Erklaerung gehoerte, tritt der Platzhalter an seine Stelle; wo er nur mitgeschrieben war, faellt er samt seiner Klammer weg und der Satz wird neu formuliert"

requirements-completed: []
requirements-partial:
  - "HART-01: Auflage A2 ist mit diesem Plan vollstaendig (Gate in 16-02, Bereinigung und Restliste hier). Das Requirement selbst wird erst in 16-13/16-14 abgehakt"

# Metrics
duration: 55 min
completed: 2026-09-21
---

# Phase 16 Plan 05: Bereinigung der Altfunde und Restliste Summary

Entscheid E2 vollzogen: die redigierbaren Dokumente unter `docs/` tragen Kennungen und Adressen nur noch als Platzhalter, die die Art des Wertes benennen, das gesperrte Wort ist aus den vier Anleitungen verschwunden, und die Ausnahmeliste des Gates ist von 50 auf 46 Einträge geschrumpft, die jetzt nur noch Belege, das öffentliche Abbild und den bewusst behaltenen Korpus-Snapshot nennen. Die Historie ist unberührt.

## Was gebaut wurde

**Task 1, die Kennungen und Adressen (M-02), Commit `fe3cf8c`.**

Sieben Werte in zwei Dokumenten, fünfzehn Fundstellen: dreizehn davon tragen
jetzt einen Platzhalter, zwei sind samt ihrem Nebensatz umformuliert.

| Wert | Platzhalter | wo |
|---|---|---|
| Instanzkennung | `<instanzkennung>` | performance.md 4x, install-check.md 1x |
| Volumekennung, Korpus | `<volumekennung>` | performance.md 3x |
| Volumekennung, System | `<volumekennung>` | performance.md 2x |
| Kennung der Security Group | `<sicherheitsgruppe>` | performance.md 2x |
| drei öffentliche Adressen der Boxen | `<adresse-der-box>` | performance.md 1x, dazu zwei umformulierte Sätze |

Die beiden umformulierten Stellen in `docs/performance.md` haben den Wert nicht
ersetzt, sondern verloren: dort stand die Adresse in einem Nebensatz, der
erklärt, dass genau diese Adresse nach dem Anhalten nicht mehr zur Box gehört.
Ein Platzhalter hätte den Satz zu einer Tautologie gemacht, also heißt es jetzt
"die bis dahin gültige" und "die bisherige". Das ist die Regel des Plans für den
nur mitgeschriebenen Wert, angewandt statt zitiert.

Die Legende steht als `PLATZHALTER` im Gate, mit einem Satz je Form, und ein
neuer Fall hält sie in beide Richtungen gegen `docs/`: jede Form der Legende
muss im Baum vorkommen, und jede Zeichenkette der Platzhalterform im Baum muss
in der Legende stehen. Die Form selbst ist absichtlich eng (`<...kennung>`,
`<sicherheitsgruppe>`, `<adresse-...>`), weil `docs/` voller spitzer Klammern
ist, die XML-Elemente und Routennamen sind.

Sechs Gründe der Ausnahmeliste sind auf den verbliebenen Bestand nachgezogen
worden; sie sagten vorher "ein Dokument, das Plan 16-05 noch ändern kann", und
das ist seit diesem Plan keine Begründung mehr, sondern eine Verfallsanzeige.

**Task 2, das gesperrte Wort (L-10), Commit `f1c15a1`.**

52 Vorkommen in vier Dokumenten sind ersetzt: 41 in `install-check.md`, 7 in
`admin-page.md`, 3 in `dev-setup.md`, 1 in `performance.md`. Die Ersatzformen
kommen aus dem Vokabular, das `docs/store-listing.md` bereits führt:

| gemeint war | Ersatz |
|---|---|
| die gepackte Release-Datei je Hälfte | Paketdatei, Companion-Paketdatei, Backend-Paketdatei |
| der Beispielordner eines Ausschlusses | Ablage, Ablageordner |
| gepackte Dateien eines Bestands | ZIP-Dateien |
| die kalte Speicherstufe des Anbieters | kalte Ablagestufe |

Drei Vorkommen bleiben, und jedes mit seinem Grund: zweimal der Skriptname
`store-archive.sh`, der Code ist, und einmal die wörtlich zitierte englische
Ausgabe eines CI-Schrittes, die englische technische Prosa ist (E-H2).

Die vier Dateien stehen damit nicht mehr auf der Vokabular-Ausnahmeliste. Unter
dieser Familie bleiben zwei Einträge, beide Rohdateien gefahrener Anfahrten.

## Die Ausnahmeliste, vorher und nachher

| Familie | vor 16-05 | nach 16-05 |
|---|---:|---:|
| pem-privatschluessel | 2 | 2 |
| aws-ressourcenkennung | 10 | 10 |
| schluesselwort-mit-wert | 11 | 11 |
| base64-block-ab-40 | 2 | 2 |
| muster-der-umsetzung | 19 | 19 |
| vokabular | 6 | 2 |
| **gesamt** | **50** | **46** |

Die Zahl der Einträge fällt nur um vier, und das ist die ehrliche Bilanz: die
meisten Einträge der Liste waren von Anfang an Belege oder Fehlalarme, die eine
Familie nicht von einem Geheimnis unterscheiden kann. Was sich wirklich geändert
hat, steht nicht in der Zahl der Zeilen, sondern in den Dokumenten: dreizehn
Werte weniger und 52 gesperrte Wörter weniger unter `docs/`. Sechs Einträge
tragen außerdem einen anderen Grund als vorher, weil ihr alter Grund ein
Versprechen auf diesen Plan war.

## Der Konflikt, der benannt gehoert

Der Plan zählt für Gruppe B "zwei Arten, und nur diese zwei". Gefunden habe ich
drei, und die dritte steht hier benannt statt still auf der Liste:

1. **Rohdaten und Skripte gefahrener Anfahrten.** Unverändert, wie vorgesehen.
2. **Die öffentliche Abbildkennung I-01.** Unverändert, wie vorgesehen.
3. **Die Korpus-Snapshotkennung und die Kopfzeile eines Schlüsselpaares.** Die
   Snapshotkennung ist der Beispielfall aus Entscheid E2 der 16-CONTEXT.md
   ("z.B. bewusst oeffentliche Hostnamen wie loadtest.infranode.dev,
   snap-Kennung"), und sie taucht in der Aufzählung des Befundes M-02 gar nicht
   auf: dort stehen eine Instanzkennung, zwei Volumekennungen, eine
   Security-Group-Kennung und die öffentlichen Adressen, und genau die sind
   ersetzt. Die Kopfzeile im Runbook ist eine Anweisung, wie eine Datei anfängt,
   und trägt kein Schlüsselmaterial.

Ebenfalls benannt: `runbook-messbox.md`, `docs/audits/2026-09-phase-15/README.md`
und die READMEs der Messreihen sind nicht redigiert worden, obwohl der Plan
unter Gruppe A auch "Auditberichte" und "README-Dateien unter docs/" nennt. Der
Grund ist die Dateiliste des Plans, die genau fünf Dateien führt, und der Befund
selbst: in diesen Dateien steht von den bereinigbaren Arten nichts mehr, sondern
nur noch die Abbildkennung und der Snapshot der Gruppe B. Die
Messreihen-READMEs bleiben zusätzlich unberührt, weil der Plan jede Änderung
unter `docs/measurements/` ausschließt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - fehlende kritische Vollstaendigkeit] Die Mehrzahlformen des gesperrten Wortes**

- **Found during:** Task 2
- **Issue:** Der Plan zählt 13 englische Vorkommen in `install-check.md` und
  nimmt sie von der Bereinigung aus. Zehn davon sind deutsche Mehrzahlformen,
  die das Suchmuster der Familie wegen der Endung nicht sieht; die Regel des
  Betreibers gilt aber der deutschen Prosa und nicht dem Suchmuster.
- **Fix:** Alle deutschen Formen ersetzt, Mehrzahl eingeschlossen; dazu ein
  Vorkommen in `admin-page.md`, das außerhalb der Zählung des Plans lag
  (ZIP-Dateien statt der gesperrten Mehrzahl). Wirklich englisch sind nur drei
  Vorkommen, und die bleiben.
- **Files modified:** docs/install-check.md, docs/admin-page.md
- **Commit:** f1c15a1

**2. [Rule 3 - blockierende Unschaerfe] Die fuenfte Platzhalterform**

- **Found during:** Task 1
- **Issue:** Der Plan schlägt `<adresse-des-arbeitsplatzes>` vor. In den
  redigierbaren Dokumenten steht keine solche Adresse; sie liegt in Rohdaten der
  Gruppe B. Eine Legendenzeile ohne Fundstelle wäre Dekoration.
- **Fix:** Form nicht eingeführt, dafür die im Runbook bereits benutzte Form
  `<snapshotkennung>` in die Legende aufgenommen. Der neue Fall hält die Legende
  in beide Richtungen gegen den Baum, so dass beide Entscheidungen geprüft sind
  und nicht behauptet.
- **Files modified:** backend/tests/test_public_artifacts.py
- **Commit:** fe3cf8c

## Gate-Protokoll

| Stufe | Befehl | Ausgang |
|---|---|---|
| 1 | `uv run pytest tests/test_public_artifacts.py -q` | grün, **51 Fälle** (vorher 50; der neue ist die Legende) |
| 2 | `uv run pytest tests/test_public_artifacts.py -q -k "vokabular or blocked"` | grün, 5 ausgewählt, 46 abgewählt |
| 3 | `uv run ruff check tests` | grün |
| 4 | `uv run ruff format --check tests` | grün, 69 Dateien bereits formatiert |
| 5 | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | grün, 0 errors, 0 warnings, 0 informations |
| 6 | `uv run vulture src tests --min-confidence 80` | grün, keine Ausgabe |
| 7 | `uv run pytest -q` (VOLLE Suite) | grün, **2464 bestanden, 15 übersprungen**, 205,01 s |

Die Skipzahl ist unverändert 15 gegen den Stand nach 16-04 (2463 bestanden und
15 übersprungen); der eine zusätzliche bestandene Fall ist der Legendenfall aus
Task 1.

## Die Historie

`git log --oneline` zeigt zwei neue Commits obendrauf und nichts sonst. Kein
`rebase`, kein `amend` auf fremden Commits, kein `filter-branch`, kein Push.
Jede früher zitierte Commit-Kennung gilt weiter (Regel des Betreibers vom
25.08.2026, T-16-17).

`git diff --name-only HEAD~2 HEAD` nennt fünf Dateien und keine einzige unter
`docs/measurements/`.

## Verification

1. Das Gate ist grün mit einer Ausnahmeliste, die nur noch Belege, das
   öffentliche Abbild und den behaltenen Snapshot nennt: **ja**, 51 Fälle.
2. Keine Datei unter `docs/measurements/**` ist geändert: **ja**, gegen
   `git diff --name-only HEAD~2 HEAD` geprüft.
3. Die Historie ist unberührt: **ja**.
4. Volle Suite grün, Skipzahl unverändert: **ja**, 2464 und 15.

## Self-Check: PASSED

- `docs/performance.md`, `docs/install-check.md`, `docs/admin-page.md`,
  `docs/dev-setup.md`, `backend/tests/test_public_artifacts.py`: vorhanden und
  geändert.
- Commits `fe3cf8c` und `f1c15a1`: in `git log` vorhanden.
- Kein Kennungs- oder Adresswert mehr in den vier redigierten Dokumenten, gegen
  das Gate selbst nachgelesen.
