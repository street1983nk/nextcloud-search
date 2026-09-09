---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 02
subsystem: testing
tags: [measurement, arm64, github-actions, workflow-dispatch, base-load, tokenizer, digest, deferred-item]

# Dependency graph
requires:
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "der auf main gepushte Stand mit den renormalisierten Messskripten; measure.yml mountet genau dieses Verzeichnis in den Container"
  - phase: 07-gemeinsame-embedding-engine
    provides: "die Feinmessung der Grundlast mit ihren fuenf benannten Posten, der Messschritt D in measure.yml und DI-07-04 als benannte Luecke"
provides:
  - "01-grundlast-fein-arm64.txt: die Feinmessung der Grundlast auf nativer ARM-Hardware, Schritte 00 bis 16, mit Laufnummer, Commit und Digest im Kopf"
  - "01-grundlast-fein-arm64-emuliert.txt: die QEMU-Messung als benannter Vorlaeufer, bytegleich zur bisherigen Datei"
  - "01-grundlast-fein-amd64-runner.txt: der Kontrollast desselben Laufs, damit jede Zahl der Kontrolle ihre Rohdatei hat"
  - "die Erwartung, gegen die der Lauf auf der Box seine Grundlast haelt: fuenf Posten, 543,7 MB, native ARM-Zahl"
  - "der Digest sha256:eed6a5fc (arm64-Haelfte sha256:ae58d930), den der Lauf in Welle 5 aufloesen muss"
affects: [10-03, 10-04, 10-05, 10-06, 10-07, docs/performance.md, box-lauf]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine ersetzte Messreihe wird umbenannt und unter jeder nachgezogenen Tabelle als Vorlaeufer genannt, statt geloescht zu werden"
    - "Drei Feststellungen vor einem Messlauf: sauberer Baum gleich origin/main, gruener Bildbau auf genau diesem Commit, aufgeloester Digest"
    - "Der Kontrollast einer Matrix bekommt eine eigene Rohdatei, damit die Kontrolle belegt ist, ohne die Datei des Entscheids anzufassen"

key-files:
  created:
    - docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64-emuliert.txt
    - docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-amd64-runner.txt
  modified:
    - docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64.txt
    - docs/measurements/2026-09-grundlast-fein/README.md
    - docs/performance.md
    - .planning/phases/07-gemeinsame-embedding-engine/deferred-items.md

key-decisions:
  - "Der Dispatch lief erst, nachdem der docker.yml-Lauf 34324821140 auf genau HEAD gruen war. Der Diff gegen den vorherigen erfolgreichen Bildbau war NICHT leer (die Testdatei der Welle 1 liegt unter backend/**), und die Abbruchregel des Plans zielt auf den Fall, dass das Abbild einen anderen Quellstand traegt. Warten macht die Bedingung wahr statt sie zu umgehen: der Bildbau lief auf demselben Commit, gegen den gemessen wurde"
  - "Die emulierte Datei wird per git mv umbenannt und nicht neu geschrieben, damit die Umbenennung als solche im Baum steht und der Inhalt bytegleich bleibt"
  - "Der Kopf der neuen Rohdatei nennt den Manifestindex UND die arm64-Haelfte. Der Runner liest RepoDigests nach einem Pull auf den Tag und bekommt den Index; die aeltere amd64-Datei nennt einen Plattform-Digest von docker image inspect. Zwei verschiedene Dinge unter demselben Feldnamen sind eine Falle fuer Welle 5, also stehen beide da"
  - "Das Wort emuliert kommt in der neuen Rohdatei nicht vor, auch nicht als Verweis auf den Vorlaeufer. Die Zusicherung des Plans prueft die ganze Datei, und der Verweis gehoert in den Bericht, nicht in eine Datei, die ausser ihrem Kopf nur Skriptausgabe ist"
  - "Der amd64-Ast desselben Laufs wird als eigene Datei abgelegt statt nur ausgerechnet. Die Kontrolle nennt Zahlen, und die Hausregel dieser Messreihe ist, dass jede Zahl ihre Rohdatei nennt"
  - "Die Prozentangaben der Kontrolle bekommen ihre absolute Zahl daneben. Zwei der fuenf Posten weichen um mehr als 5 Prozent ab und um 0,39 beziehungsweise 0,21 MB; ein Prozentsatz auf einer Zahl unter einem Megabyte misst die Speicherverwaltung und nicht den Vorgang"
  - "Der Entscheid des Plans 07-03 wird nicht umgeschrieben, sondern datiert: der Zitatblock nennt weiter die Zahlen vom 08.09.2026, und die native Zahl steht als Bestaetigung darunter. Eine Entscheidung rueckwirkend auf Zahlen zu stellen, die es an ihrem Tag nicht gab, waere eine Faelschung der Vorgeschichte"
  - "MESS-01 bleibt Pending, obwohl das Frontmatter des Plans es fuehrt: die Kennung verlangt einen Vergleichslauf auf der Box gegen die v1.0-Baseline, und dieser Plan hat null Box-Minuten gekostet"

patterns-established:
  - "Vor einem Messlauf wird die Feststellung ueber den gemessenen Stand nicht nur geprueft, sondern hergestellt: ist der Bildbau fuer HEAD noch unterwegs, wird gewartet, statt gegen ein Abbild von gestern zu messen"
  - "Eine nachgezogene Tabelle traegt die Vorlaeuferzahl mit Dateinamen unter sich, und der Berichtskopf nennt die nachgezogenen Abschnitte samt Laufnummer"

requirements-completed: []
requirements-touched: [MESS-01]

# Metrics
duration: 25min
completed: 2026-09-09
---

# Phase 10 Plan 02: Die native arm64-Feinmessung ohne Box Summary

**Die letzte offene Zahl der Phase 7 steht: der erste `workflow_dispatch` von `measure.yml` auf `main` hat die Feinmessung der Grundlast auf `ubuntu-24.04-arm` gefahren, und die fuenf Posten treffen die grobe native Messung derselben Schritte auf 8 kB, wo die QEMU-Messung 1,2 Prozent daneben lag.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-09T07:37:00Z
- **Completed:** 2026-09-09T08:02:00Z
- **Tasks:** 2 von 2
- **Files modified:** 6 (4 geaendert, 2 neu, davon eine per Umbenennung)
- **Box-Minuten:** 0, wie geplant
- **Runner-Minuten:** 5 min 27 s im arm64-Ast, 6 min 48 s im amd64-Ast

## Accomplishments

- **Der Dispatch ist gefahren und gruen:** Lauf [34325000302](https://github.com/street1983nk/nextcloud-search/actions/runs/34325000302) auf `main`, Commit `b6426ed`, beide Matrixaeste erfolgreich. Der arm64-Ast lief auf `ubuntu-24.04-arm`, `uname -m` meldet `aarch64`, Kernel 6.17.0-1022-azure, 4 CPUs.
- **Die Grundlinie ist an ihrem Platz:** Schritt 00 kostet nativ **13,0 MB** gegen 43,2 MB unter Emulation und liegt damit neben der amd64-Zahl von 13,3 MB. Die rund 30 MB QEMU-Aufschlag sind weg, wie die Recherche es vorhergesagt hat.
- **Die Zuwaechse bestaetigen die Emulation und schlagen sie in der Genauigkeit:** die fuenf Posten summieren sich nativ auf **543,7 MB** (556.752 kB) gegen 543,7 MB (556.760 kB) aus der groben nativen Messung `2026-09-nachmessung-m7g/rohdaten/63-grundlast.txt`. Das ist ein Unterschied von **8 kB** oder 0,001 Prozent, auf zwei verschiedenen ARM-Maschinen gemessen (AWS Graviton3 und der Azure-Runner). Schritt 11 gesamt trifft mit 275.912 kB gegen 275.912 kB auf das Kilobyte.
- **Die Geschichte bleibt lesbar:** die emulierte Reihe steht als `01-grundlast-fein-arm64-emuliert.txt` bytegleich daneben (`git diff` gegen den alten Blob ist leer), und jede der vier nachgezogenen Tabellen nennt die Vorlaeuferzahl mit diesem Dateinamen.
- **Die Kontrolle ist gerechnet und belegt:** der amd64-Ast desselben Laufs liegt als `01-grundlast-fein-amd64-runner.txt` im Repo. Gegen die Datei des Entscheids weichen die fuenf Posten in der Summe um **0,76 MB, also 0,14 Prozent** ab; die grosse absolute Abweichung des ganzen Laufs ist -4,38 MB am informativen Schritt 16.
- **DI-07-04 ist geschlossen**, in der Form von DI-07-01: Datum, Laufnummer, Artefaktname `welle0-arm64`, Digest, und die Liste der nachgezogenen Abschnitte. Der bisherige Text steht darunter.
- **Kein Regressionsschatten:** ganze Suite 1878 passed / 15 skipped, genau die Grundlinie der Welle 1. `ruff check`, `ruff format --check`, `pyright` und `vulture` ohne Befund. `CLAUDE.md` unveraendert.

## Task Commits

1. **Task 1: Der Dispatch von measure.yml auf nativem arm64** , `d8d902a` (feat)
2. **Task 2: Die vier Spalten, die Zeile in performance.md und DI-07-04** , `235474e` (docs)

## Die drei Feststellungen vor dem Dispatch

Jede als Ausgabe im Protokoll, keine als Annahme, wie der Plan es verlangt:

| Feststellung | Ergebnis |
|---|---|
| Arbeitsbaum sauber, `main` gleich `origin/main` | beide auf `b6426ed8818459d7b2bef60ce51305f5775e8433`, `git status --porcelain` leer. Die Commits der Welle 1 standen bereits auf `origin/main`, ein Push war nicht noetig |
| Letzter erfolgreicher `docker.yml`-Lauf und der Beweis, dass `:dev` den Backend-Stand von HEAD traegt | zunaechst 34316508242 auf `2c1b741`, und der Diff dagegen war **nicht leer**: `backend/tests/test_measurement_scripts.py` aus der Welle 1 liegt unter `backend/**`. Genau deshalb lief `docker.yml` in diesem Moment fuer `b6426ed`. Nach dessen Erfolg (Lauf 34324821140) ist der letzte erfolgreiche Bildbau derselbe Commit wie HEAD, und `git diff b6426ed HEAD -- backend/ php/` ist leer |
| Der Digest, den `:dev` heute aufloest | `docker buildx imagetools inspect`: Manifestindex `sha256:eed6a5fcb152373e7bf6d7725da774844d4012cfe0cbe02b261f31a865e4cce3`, arm64-Haelfte `sha256:ae58d93005dc18849c3bd128cef51bea0530c143f5719a284fd694b6f9e09d44`, amd64-Haelfte `sha256:a2b9aef78e321d5829838b8120d7feaf2f9ab36e62058fd4ba5388fc33944c11`. Der Lauf hat denselben Index aufgeloest, in beiden Aesten |

## Files Created/Modified

- `docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64.txt` , die native Messung. Fuenf Kopfzeilen (Titel mit Datum, Laufnummer samt URL und Commit, Runner samt `uname -m` und der Feststellung "kein QEMU", Digest mit Index und arm64-Haelfte, Gegenprobe), darunter die unveraenderte Ausgabe des Skripts mit den Schritten 00 bis 16.
- `docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64-emuliert.txt` , die QEMU-Messung vom 08.09.2026, per `git mv` umbenannt, Inhalt bytegleich.
- `docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-amd64-runner.txt` , der Kontrollast. Derselbe Kopfaufbau, dazu eine Rollenzeile, die ausdruecklich sagt, dass diese Datei NICHT die Datei des Entscheids aus Plan 07-03 ist.
- `docs/measurements/2026-09-grundlast-fein/README.md` , Abschnitt 1 (Umgebungstabelle mit `arm64 (nativ)`, zwei Bemerkungen zum Digest, die neu gerechnete Abweichungstabelle, die Kontrolltabelle samt Befund), Abschnitt 2 (alle 20 Schrittzeilen, Vorlaeuferzeile, die Gegenprobe jetzt in Kilobyte, ein Absatz zu den zwei Zeilen der Einbettung), Abschnitt 3 (der Modulimport nativ), Abschnitt 4 (die Postentabelle und die Datierung des Entscheids). Dazu ein Nachzugsvermerk unter dem Titel.
- `docs/performance.md` , die Tabelle des Abschnitts "Der groesste Posten der Grundlast heisst Tokenizer und Splitter" auf `arm64 (nativ)`, ein Absatz zum Vorlaeufer mit Dateiname und Prozentzahlen, und eine neue Zeile in "Stand dieses Berichts" mit Datum 2026-09-09.
- `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md` , DI-07-04 geschlossen.

## Die Zahlen, die aus diesem Plan weiterreisen

| Posten | amd64 (Entscheidsdatei) | arm64 nativ, Lauf 34325000302 | arm64 emuliert (Vorlaeufer) |
|---|---:|---:|---:|
| 00-leerer-prozess (Grundlinie) | 13,3 MB | **13,0 MB** | 43,2 MB |
| 11a-tokenizers-modul-importiert | 4,2 MB | **4,2 MB** | 6,0 MB |
| 11b-erste-tokenizer-instanz | 265,8 MB | **265,2 MB** | 246,6 MB |
| 12a-splitter-gebaut | 273,5 MB | **273,4 MB** | 294,0 MB |
| 12b-erster-chunkerlauf | 0,8 MB | **0,9 MB** | 3,5 MB |
| 12c-zweiter-chunkerlauf | 0,0 MB | **0,0 MB** | 0,0 MB |
| **Summe der fuenf** | **544,3 MB** | **543,7 MB** | **550,1 MB** |
| Abweichung gegen 63-grundlast.txt (543,7 MB) | , | **-8 kB, -0,001 %** | +6,4 MB, +1,2 % |

Fuer Welle 5 gehoert an den Ablaufplan: der Lauf auf der Box muss
`sha256:eed6a5fcb152373e7bf6d7725da774844d4012cfe0cbe02b261f31a865e4cce3`
aufloesen, und wenn er einen Plattform-Digest liest, ist die Zielzeichenkette
die arm64-Haelfte `sha256:ae58d930...`. Steht dort etwas anderes, gehoeren die
zwei Messungen zu zwei Abbildern.

## Decisions Made

Die tragenden Entscheidungen stehen im Frontmatter unter `key-decisions`. Zwei verdienen den Fliesstext:

**Warum der Plan nicht abgebrochen wurde, obwohl der Diff nicht leer war.** Feststellung 2 verlangt einen leeren `git diff <letzter-docker.yml-Commit> HEAD -- backend/ php/` und schreibt fuer den anderen Fall den Abbruch vor. Der Diff war nicht leer: die Testdatei der Welle 1 liegt unter `backend/tests/`, also innerhalb des Pfadfilters von `docker.yml`. Die Regel schuetzt aber vor einer Sache, die hier nicht vorlag, naemlich einer Feinmessung gegen ein Abbild, das einen anderen Quellstand traegt. `docker.yml` lief in genau diesem Moment fuer `b6426ed`, also fuer HEAD selbst. Zu warten macht die Bedingung wahr, statt sie zu umgehen: nach dem gruenen Lauf 34324821140 ist der letzte erfolgreiche Bildbau derselbe Commit wie HEAD, und der Diff ist leer. Der Umweg hat ausserdem eine Wettlaufgefahr beseitigt, die der Plan nicht kannte: ein Dispatch waehrend eines laufenden Bildbaus haette `:dev` mitten in der Messung verschoben.

**Warum die Kontrolle eine eigene Rohdatei bekommt.** Der Plan verlangt die Kontrolle als Rechnung und verbietet ausdruecklich, `01-grundlast-fein-amd64.txt` zu ersetzen. Beides ist eingehalten, aber die Rechnung nennt Zahlen, und die Hausregel dieser Messreihe steht im Bericht selbst: der Abschnitt haelt nur, weil jede Zahl ihre Rohdatei oder ihren Lauf nennt. Eine Kontrolle, deren Zahlen nur in einer Berichtstabelle stehen, ist genau die Art Aussage, die dieser Bericht sonst nicht macht. Also liegt der Ast als `01-grundlast-fein-amd64-runner.txt` daneben, mit einer Rollenzeile im Kopf, die die Verwechslung mit der Entscheidsdatei ausschliesst.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Der Dispatch haette gegen ein wanderndes `:dev` gemessen**

- **Found during:** Task 1, Feststellung 2
- **Issue:** `gh run list --workflow=docker.yml --limit 5` zeigte einen **laufenden** Bildbau fuer `b6426ed`, also fuer HEAD. Der letzte erfolgreiche stand auf `2c1b741`, und der Diff dagegen war nicht leer. Ein Dispatch in diesem Zustand haette entweder gegen das Abbild von `2c1b741` gemessen oder, schlimmer, mitten in der Messung ein neues `:dev` bekommen: die Aufloesung geschieht im ersten Schritt des Laufs, der Messschritt D im letzten.
- **Fix:** Auf den Abschluss von `docker.yml` gewartet (`gh run watch 34324821140`, Ergebnis `success`), danach die Feststellung erneut gefahren. Der letzte erfolgreiche Bildbau ist damit HEAD, und `git diff b6426ed HEAD -- backend/ php/` ist leer. Kein Abbruch, weil die Bedingung des Plans hergestellt und nicht umgangen wurde.
- **Files modified:** keine
- **Verification:** `gh run view 34324821140` meldet `success` auf `b6426ed`; der Diff ist leer; der Messlauf 34325000302 loest `sha256:eed6a5fc` auf, den Index des Baus aus `b6426ed`
- **Committed in:** , (Feststellung, keine Dateiaenderung)

**2. [Rule 2 - Missing critical functionality] Die Kontrolle bekommt eine eigene Rohdatei**

- **Found during:** Task 1, Schritt c
- **Issue:** Der Plan laesst die Kontrolle als Rechnung im Bericht enden. Damit haetten sechs Zahlen im Bericht gestanden, deren Rohdatei nicht im Repo liegt, in einem Verzeichnis, dessen ganze Beweiskraft daran haengt, dass jede Zahl ihre Rohdatei nennt (T-10-06 und T-10-08 zielen genau darauf).
- **Fix:** Das Artefakt des amd64-Astes liegt als `01-grundlast-fein-amd64-runner.txt` im Repo, mit demselben Kopfaufbau und einer Rollenzeile, die sagt, dass die Datei des Entscheids `01-grundlast-fein-amd64.txt` heisst und unveraendert ist. Die Kontrolltabelle des Berichts nennt beide Dateien.
- **Files modified:** `docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-amd64-runner.txt`, `docs/measurements/2026-09-grundlast-fein/README.md`
- **Verification:** `git diff --name-only` nennt `01-grundlast-fein-amd64.txt` nicht; die neue Datei traegt Digest, Laufnummer und `x86_64`
- **Committed in:** `d8d902a` und `235474e`

**3. [Rule 1 - Bug] DI-07-04 nennt Abschnitt 7 eines Berichts, der sechs hat**

- **Found during:** Task 2, `read_first`
- **Issue:** DI-07-04 und das Frontmatter dieses Plans nennen "Abschnitt 1, 2, 4 und 7" als die vier Stellen mit arm64-Spalten. `docs/measurements/2026-09-grundlast-fein/README.md` hat sechs Abschnitte. Die vier Stellen mit arm64-Zahlen sind 1, 2, **3** und 4: Abschnitt 3 nennt den Modulimport mit "4,2 MB auf amd64 und 6,0 MB emuliert" im Fliesstext. Wer die Zahl nur in den drei genannten Tabellen ersetzt, laesst eine emulierte Zahl in der Prosa stehen, und zwar die, die den Kernsatz "der Modulimport ist nicht das Problem" traegt.
- **Fix:** Alle vier Stellen nachgezogen, Abschnitt 3 mit dem Vorlaeufer in Klammern. Der Abschlussvermerk von DI-07-04 nennt die vier Abschnitte 1, 2, 3 und 4 und haelt in einem eigenen Absatz fest, dass die "7" des alten Textes ins Leere zeigte, damit der naechste Leser die Abweichung nicht fuer eine Auslassung haelt.
- **Files modified:** `docs/measurements/2026-09-grundlast-fein/README.md`, `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`
- **Verification:** `grep -n "emuliert\|Emulation\|QEMU"` ueber beide Dokumente zeigt nur noch bewusste Vorlaeuferverweise
- **Committed in:** `235474e`

**4. [Rule 1 - Bug] MESS-01 wurde nicht abgehakt, obwohl das Frontmatter es fuehrt**

- **Found during:** Zustands-Update nach Task 2
- **Issue:** Das Frontmatter des Plans nennt `requirements: [MESS-01]`. MESS-01 verlangt einen Vergleichslauf auf der AWS-Box mit dem vorhandenen v1.0-Korpus, der die RSS-Ersparnis gegen die v1.0-Baseline belegt. Dieser Plan hat null Box-Minuten gekostet, keinen Korpus angefasst und keine Baseline verglichen; er hat eine Erwartung geschaerft, gegen die spaeter gemessen wird. Genau derselbe Fehlgriff ist in der Welle 1 passiert (Deviation 7 der 10-01-SUMMARY) und dort zurueckgenommen worden.
- **Fix:** `requirements.mark-complete` nicht aufgerufen. `REQUIREMENTS.md` bleibt unveraendert, MESS-01 steht weiter auf `Pending`. Im Frontmatter dieser Zusammenfassung ist `requirements-completed` leer und MESS-01 unter `requirements-touched` gefuehrt.
- **Files modified:** keine (`.planning/REQUIREMENTS.md` ausdruecklich nicht angefasst)
- **Verification:** `grep MESS-01 .planning/REQUIREMENTS.md` zeigt ein offenes Kaestchen und `Pending`; `git diff --name-only b6426ed HEAD` nennt `REQUIREMENTS.md` nicht
- **Committed in:** dieser Metadaten-Commit

**5. [Rule 2 - Missing critical functionality] Der Kopf nennt zwei Digest-Arten, nicht eine**

- **Found during:** Task 1, Schritt b
- **Issue:** Der Plan verlangt "den Digest des gemessenen Abbilds". `measure.yml` liest `RepoDigests` nach einem `docker pull` auf den Tag und bekommt damit den Digest des **Manifestindex**; die vorhandene amd64-Datei nennt unter demselben Feldnamen `image_digest` einen **Plattform-Digest** aus `docker image inspect` auf einer lokalen Maschine. Ein Lauf auf der Box, der nach "demselben Digest" sucht, haette je nach Werkzeug die eine oder die andere Zeichenkette gelesen und einen Ungleichstand gemeldet, den es nicht gibt. Das ist T-10-08 mit umgekehrtem Vorzeichen.
- **Fix:** Der Kopf der neuen Rohdatei nennt beide, Index und arm64-Haelfte. Abschnitt 1 des Berichts erklaert den Unterschied in zwei Saetzen, und der Abschlussvermerk von DI-07-04 fuehrt beide Zeichenketten.
- **Files modified:** `docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64.txt`, `docs/measurements/2026-09-grundlast-fein/README.md`, `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`
- **Verification:** beide Zeichenketten stehen in der Rohdatei und im Bericht; `docker buildx imagetools inspect` belegt die Zuordnung
- **Committed in:** `d8d902a` und `235474e`

**6. [Rule 2 - Missing critical functionality] Der Entscheid von Plan 07-03 wird datiert statt umgeschrieben**

- **Found during:** Task 2
- **Issue:** Der Plan sagt "die Zahl wird ersetzt". Im Zitatblock des Abschnitts 4 steht aber keine Messgroesse, sondern eine Entscheidung: "Entschieden wird gegen 544,3 MB auf amd64 und 550,1 MB auf emuliertem arm64". Die 550,1 MB dort durch 543,7 MB zu ersetzen haette behauptet, am 08.09.2026 sei gegen eine Zahl entschieden worden, die es an diesem Tag nicht gab.
- **Fix:** Der Zitatblock nennt weiter beide Zahlen vom 08.09.2026 und traegt jetzt das Datum. Darunter steht die native Zahl als Bestaetigung, mit dem ausdruecklichen Satz, dass sich am Entscheid nichts aendert, weil die Schwelle bei 100 MB liegt. Dasselbe Muster in `docs/performance.md`.
- **Files modified:** `docs/measurements/2026-09-grundlast-fein/README.md`, `docs/performance.md`
- **Verification:** die Schwelle 100 MB und der Faktor fuenf stehen unveraendert; der Entscheid ist als Entscheid vom 08.09.2026 lesbar
- **Committed in:** `235474e`

**7. [Rule 2 - Missing critical functionality] Zwei Zeilen der Einbettung sind benannt, nicht weggelassen**

- **Found during:** Task 2, beim Nachziehen der Tabelle in Abschnitt 2
- **Issue:** Mit der nativen Spalte liegen die zwei Architekturen so nah, dass zwei Zeilen herausstehen: Schritt 14 kostet auf ARM 400,8 MB gegen 395,4 MB, Schritt 15 nur 26,4 MB gegen 39,9 MB. Eine Tabelle, die die kleinen Abweichungen erklaert und die grossen unkommentiert laesst, laedt zur falschen Lesart ein.
- **Fix:** Ein Absatz benennt beide. Schritt 14 loest sich gegen den amd64-Ast desselben Laufs auf (399,4 MB, also 1,4 MB Abstand statt 5,4), Schritt 15 nicht (37,6 MB, also gut 11 MB Abstand bleiben). Der Absatz sagt ausdruecklich, dass ein Lauf je Architektur daraus keine Aussage macht und dass die fuenf Posten nicht betroffen sind.
- **Files modified:** `docs/measurements/2026-09-grundlast-fein/README.md`
- **Verification:** die drei Zahlen stehen in den drei Rohdateien und sind im Bericht mit ihrer Herkunft genannt
- **Committed in:** `235474e`

**8. [Rule 1 - Bug] Zwei Zustandsbefehle des SDK haben leere oder falsche Werte geschrieben**

- **Found during:** Zustands-Update
- **Issue:** `state.add-decision` schrieb die drei Entscheidungen mit dem Vermerk `[Phase ?]` statt `[Phase 10]`, `state.update-progress` meldete "Progress field not found in STATE.md" und liess `completed_plans` auf 18 stehen, und `state.record-session` mit leerem ersten Argument liess `stopped_at` auf "Completed 10-01-PLAN.md" stehen.
- **Fix:** Die Entscheidungen auf `[Phase 10]: 10-02: ...` gesetzt, wie die uebrigen Eintraege der Liste; `completed_plans` auf 19; `record-session` mit `--summary`, `--stopped-at` und `--resume-file` erneut gefahren.
- **Files modified:** `.planning/STATE.md`
- **Verification:** `grep "Phase ?"` ohne Treffer, `stopped_at: Completed 10-02-PLAN.md` in Frontmatter und Sitzungsblock, `completed_plans: 19`
- **Committed in:** dieser Metadaten-Commit

### Kleinere Abweichungen, ohne eigene Regel

- Der Herkunftsvermerk der neuen Rohdatei hat **fuenf** Zeilen und nicht drei. Der Plan nennt vier Angaben (Laufnummer und URL, Datum, Runner mit `uname -m`, Digest) in "drei Zeilen"; dazu kommt die Gegenprobenzeile, die die Vorlaeuferdatei ebenfalls trug. Getrennte Zeilen statt gedraengter, weil der Kopf mit `key=value` gelesen wird wie der Rest der Datei.
- Der Verweis auf die Vorlaeuferdatei steht **nicht** im Kopf der neuen Rohdatei. Die Zusicherung des Plans verbietet die Zeichenfolge `emul` in der ganzen Datei (die Datei traegt kein `===`, also greift die Trennung der Zusicherung nicht), und ein Dateiname mit dem Wort darin haette sie rot gemacht. Der Verweis steht an allen vier nachgezogenen Stellen des Berichts.
- Die neue Prosa traegt echte Umlaute, auch in `deferred-items.md`, wo die Nachbareintraege `ae/oe/ue` schreiben. Der Plan verlangt echte Umlaute ausdruecklich, und andere `.planning`-Dateien dieses Projekts fuehren sie ebenfalls. Es gibt kein Gate, das dagegen steht.

---

**Total deviations:** 8 auto-fixed (3x Rule 1 Bug, 4x Rule 2 fehlende kritische Funktionalitaet, 1x Rule 3 blockierend) plus drei kleinere Abweichungen ohne eigene Regel
**Impact on plan:** Kein Scope Creep, keine Fremdabhaengigkeit, kein Paket installiert, `backend/uv.lock` unveraendert. Sieben der acht drehen sich um denselben Punkt: eine Zahl braucht ihre Herkunft, und eine ersetzte Zahl braucht ihren Vorlaeufer. Die einzige Abweichung mit Aussenwirkung ist Nummer 1, und sie hat den Plan nicht gedehnt, sondern eine seiner Abbruchbedingungen erst wahr gemacht.

## Issues Encountered

**Der Pfadfilter von `docker.yml` und eine Testdatei.** Die Welle 1 hat `backend/tests/test_measurement_scripts.py` angelegt, also eine Datei unter `backend/**`, also innerhalb des Pfadfilters von `docker.yml`. Ein neues `:dev` wurde damit von einer Aenderung ausgeloest, die im Abbild gar nicht landet (`tests/` wird nicht mitgebaut). Folge fuer diese Phase: der Digest von `:dev` bewegt sich, wenn ein Plan eine Testdatei anfasst, obwohl der Inhalt gleich bleibt. Fuer den Lauf auf der Box heisst das, den Digest kurz vor der Anfahrt neu zu lesen und nicht aus einem Bericht zu uebernehmen. Der Vergleich, der wirklich traegt, ist der Baumhash aus `40b-baumhash.sh` der Welle 1, nicht die Digest-Zeichenkette.

**`gsd-sdk query state.*` nimmt Flags, nicht Positionsargumente.** `state.record-metric "10" "02" "25min" "2" "6"` scheitert mit "phase, plan, and duration required"; mit `--phase 10 --plan 02 --duration 25min --tasks 2 --files 6` laeuft derselbe Befehl. Ebenso `state.add-decision --summary "..."` und `state.record-session --summary ... --stopped-at ... --resume-file ...`. Notiert, damit die naechste Welle nicht dieselbe Runde dreht.

**`roadmap.update-plan-progress` findet in dieser ROADMAP keine Fortschrittstabelle.** Der Befehl laeuft durch und meldet `plan_count: 7`, `summary_count`, `status: In Progress`, aber die Phase-10-Plaene stehen als Kaestchenliste. Das Haken von `10-02-PLAN.md` ist deshalb von Hand gesetzt.

## User Setup Required

None. Der Plan hat keine Cloud-Ressource beschafft und die AWS-Box nicht angefasst. Verbraucht wurden GitHub-Runner-Minuten: 5 min 27 s auf `ubuntu-24.04-arm` und 6 min 48 s auf `ubuntu-24.04`.

## Next Phase Readiness

**Bereit fuer Welle 3.** Was diese Welle fuer den Lauf auf der Box hinterlaesst:

- Die Erwartung fuer die Grundlast steht als native ARM-Zahl: fuenf Posten, 543,7 MB, Grundlinie 13,0 MB. Weicht der Lauf auf der Box davon ab, ist die Abweichung eine Aussage ueber die Box und nicht ueber QEMU.
- Der Digest, gegen den geprueft wird, steht in der Rohdatei, im Bericht und im Abschlussvermerk von DI-07-04. Dazu die Warnung aus "Issues Encountered": ein Bildbau, den eine Testdatei ausloest, verschiebt ihn, ohne den Inhalt zu aendern.
- `measure.yml` ist als Messweg belegt und nicht nur gebaut: `workflow_dispatch` auf `main`, beide Matrixaeste gruen, Artefakte vollstaendig, `if-no-files-found: error` hat nicht gefeuert. Der Weg steht fuer jede weitere Messung offen, die kein Volumen und keinen Korpus braucht.
- Offen bleiben MESS-01, MESS-02 und MESS-03. Alle drei brauchen den Lauf auf der Box, und keiner der sieben Plaene vor Welle 5 kann sie schliessen.

**Ein Nebenbefund fuer den Bericht der Welle 7:** die Kaltmessung `chars-per-token-prose.txt` ist in beiden Aesten **0 Byte** gross. Der Schritt mountet `.planning/phases/06-semantische-suche`, und dieses Verzeichnis existiert nicht mehr, seit die v1.0-Phasen nach `.planning/milestones/v1.0-phases/` verschoben wurden. Der Schritt bleibt gruen, weil `docker run` einen leeren Mount anlegt, und das Werkzeug schreibt eine leere Datei statt eines Fehlers. Kein Befund fuer diesen Plan, denn `chars-per-token` gehoert der Phase 6 und nicht MESS-01; der Eintrag liegt in `deferred-items.md` der Phase 10.

## Known Stubs

Keine. Beide Rohdateien tragen vollstaendige Messreihen mit allen 20 Schritten, alle vier nachgezogenen Stellen nennen Zahlen mit ihrer Rohdatei, und der Abschlussvermerk von DI-07-04 nennt Laufnummer, Datum, Artefakt und Digest.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die sechs Eintraege mit Disposition `mitigate`:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-10-06 | Umbenennen statt Loeschen, Inhalt bytegleich (`git diff` gegen den alten Blob leer); Vorlaeuferzahl mit Dateinamen unter allen vier nachgezogenen Stellen; der Berichtskopf nennt den Nachzug samt Laufnummer |
| T-10-07 | Der Kopf jeder Rohdatei nennt Runner und `uname -m`; die neue arm64-Datei fuehrt `runner=ubuntu-24.04-arm` und `arch=aarch64`, die Kontrolldatei `ubuntu-24.04` und `x86_64`; die Zusicherung des Plans prueft es |
| T-10-08 | Der Digest steht im Kopf, im Bericht und im DI-Vermerk, und zwar als Index UND arm64-Haelfte (Deviation 5). `docker.yml` loest nur auf `backend/**`, und diese Phase aendert `backend/src` nicht; der Diff gegen den gemessenen Commit ist leer |
| T-10-09 | Drei Feststellungen vor dem Dispatch, jede mit Ausgabe im Protokoll; die zweite wurde hergestellt statt umgangen (Deviation 1); der Lauf traegt `commit=b6426ed`, gleich `origin/main` |
| T-10-10 | Uebernommen wurde ausschliesslich das Artefakt des Messschritts, nie eine Zeile Laufprotokoll. Musterpruefung ueber die drei Dateien auf `ghp_`, `gho_`, `github_pat_`, `AKIA...`, `-----BEGIN`, `password`, `passwort`, `secret`, `token=`, `Bearer`: kein Treffer |
| T-10-SC | Kein Paket installiert. Der Runner zieht ein veroeffentlichtes Abbild und baut nichts; `backend/uv.lock` unveraendert |

## Self-Check: PASSED

| Geprueft | Ergebnis |
|----------|----------|
| Die drei Rohdateien liegen auf der Platte | alle drei `FOUND` |
| Beide Task-Commits in `git log` | `d8d902a` und `235474e` `FOUND` |
| `git diff --name-only b6426ed HEAD` | genau die sechs Dateien des Plans, keine siebte |
| `CLAUDE.md` unveraendert | nicht im Diff |
| `.planning/REQUIREMENTS.md` unveraendert | nicht im Diff |
| Loeschungen in den zwei Commits | keine (`--diff-filter=D` leer) |
| Umbenennung inhaltsgleich | `git diff HEAD~1:...arm64.txt HEAD:...arm64-emuliert.txt` leer |
| `01-grundlast-fein-amd64.txt` unveraendert | nicht im Diff |
| Schrittnamen der neuen Datei zeichengleich mit der amd64-Datei | `True`, alle 20 |
| Schritt 00 der neuen Datei unter 20 MB | 13.268 kB, also 13,0 MB |
| Zusicherung Task 1 | `ok` |
| Zusicherung Task 2 | `ok` |
| Geheimnisse in den drei Dateien | keine |
| Wagenruecklauf in den neuen Dateien | keiner (LF geschrieben, `core.autocrlf` liefert CRLF im Arbeitsbaum und LF im Blob, wie bei den Nachbardateien) |
| Em-Dash oder En-Dash in den sechs Dateien | keiner, und keiner in dieser Zusammenfassung |
| `pytest -q` ganze Suite | 1878 passed / 15 skipped (Grundlinie 1878 / 15) |
| `ruff check .`, `ruff format --check .` in `backend/` | All checks passed, 120 files already formatted |
| `pyright` | 0 errors, 0 warnings, 0 informations |
| `vulture src tests --min-confidence 80` | ohne Befund |
| `gh run list --workflow=measure.yml --limit 1` | 34325000302, `completed / success`, `headSha b6426ed` gleich `origin/main` |

## TDD Gate Compliance

Nicht anwendbar. Der Plan traegt `type: execute`, keine Aufgabe ist mit `tdd="true"` ausgezeichnet, und keine Zeile Produktionscode ist entstanden: die Aenderungen sind zwei Rohdateien, ein Messbericht, ein Leistungsbericht und ein vertagter Befund. Das Gate ueber die Messskripte aus der Welle 1 laeuft trotzdem mit und ist gruen (132 passed zusammen mit der Hausordnung von `scripts/ops`).

---
*Phase: 10-vergleichsmessung-auf-der-aws-box*
*Completed: 2026-09-09*
