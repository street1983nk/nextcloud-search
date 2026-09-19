---
phase: 14-modell-entladung-im-leerlauf
plan: 02
subsystem: testing
tags: [measurement, rss, malloc_trim, glibc, onnxruntime, aarch64, github-actions, gate]

# Dependency graph
requires:
  - phase: 14-modell-entladung-im-leerlauf
    provides: Messskript 01-rss-rueckgabe.py, Schritt E in measure.yml, Erwartung E1 bis E4 aus 14-01
  - phase: 10-messbox
    provides: measure.yml als dispatch-only Messwerkstatt mit arm64-Ast und Digest-Aufloesung
provides:
  - Rohdaten der RSS-Rueckgabe auf aarch64 und x86_64, Lauf 35443822228
  - Messbericht mit Urteil je Erwartung und Gesamturteil im Wortlaut des Ablaufdokuments
  - Der Bodensatz als benannte Groesse fuer den Store-Text
affects: [14-entladefunktion, 15-boxmessung, 16-store-texte]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messbericht urteilt gegen die vorher committete Erwartung, Commitzeiten beider Dateien im Bericht zitiert"
    - "Nur die Rohdateien der gestellten Frage wandern aus dem Artefakt ins Repository"

key-files:
  created:
    - docs/measurements/2026-09-entladung-vorpruefung/README.md
    - docs/measurements/2026-09-entladung-vorpruefung/rohdaten/machine.txt
    - docs/measurements/2026-09-entladung-vorpruefung/rohdaten/machine-x86_64.txt
    - docs/measurements/2026-09-entladung-vorpruefung/rohdaten/rss-rueckgabe-aarch64.txt
    - docs/measurements/2026-09-entladung-vorpruefung/rohdaten/rss-rueckgabe-x86_64.txt
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "E1 bis E4 sind alle gehalten: Median der Rueckgabe 100,0 Prozent auf aarch64, trim_rc in fuenf von fuenf Zyklen 1"
  - "Der Gesamtausgang ist Gehalten, der Satz gemessen, Ergebnis negativ trifft auf diesen Lauf nicht zu"
  - "MEM-04 ist erfuellt: die Zahl liegt auf Zielarchitektur, nativ, gegen das ausgelieferte Abbild"
  - "Der Bodensatz von rund 16 MB gehoert in den Store-Text und wird nicht verschwiegen"
  - "Die Freigabe der Plaene 14-03 bis 14-12 liegt beim Owner und nicht in diesem Bericht"

requirements-completed: [MEM-04]

# Metrics
duration: 26min
completed: 2026-09-19
---

# Phase 14 Plan 02: Der Vorprueflauf auf Zielhardware Summary

**Der Lauf ist auf `ubuntu-24.04-arm` gegen das ausgelieferte Abbild gefahren und gibt mit einem Median von 100,0 Prozent praktisch den gesamten Modellspeicher an das Betriebssystem zurueck; E1 bis E4 sind alle gehalten, der Ausgang heisst "Gehalten", und das Tor der Phase liegt jetzt beim Owner.**

## Status: CHECKPOINT OFFEN

Task 3 dieses Plans ist ein `checkpoint:human-verify` und ist **nicht
entschieden**. Die Tasks 1 und 2 sind ausgefuehrt und committet, der Bericht
steht, aber der Ausgang des Tors gehoert dem Owner. Solange die Antwort fehlt,
gilt:

- Es ist **kein Produktcode** entstanden und es darf keiner entstehen.
- Die Plaene **14-03 bis 14-12 sind nicht freigegeben**.
- Der Abschnitt "Owner-Entscheid" dieser Zusammenfassung traegt die Antwort im
  Wortlaut nach, sobald sie vorliegt.

## Performance

- **Duration:** 26 min
- **Started:** 2026-09-19T12:45:00Z
- **Completed (Tasks 1 und 2):** 2026-09-19T13:11:00Z
- **Tasks:** 2 von 3 (Task 3 ist der offene Owner-Checkpoint)
- **Files created/modified:** 5 neu, 3 Zustandsdateien

## Accomplishments

- Der Lauf ist gefahren: `gh workflow run measure.yml -f image_ref=dev`, Lauf
  [35443822228](https://github.com/street1983nk/nextcloud-search/actions/runs/35443822228),
  beide Matrixaeste gruen, keine Wiederholung noetig. Vorher wurden die vier
  Commits aus 14-01 nach `main` gedrueckt, weil ein Dispatch gegen einen Baum
  ohne Schritt E nichts gemessen haette.
- **Die Zahl der Zielarchitektur liegt vor.** Fuenf Zyklen auf `aarch64`
  (Neoverse-N2, vier Kerne, `ubuntu-24.04-arm`), gegen das ausgelieferte Abbild
  `sha256:31c905b2...ef31e538`, nativ und nicht emuliert:

  | Zyklus | `baseline` | `loaded` | `after_gc` | `after_trim` | `trim_rc` | `rueckgabe_prozent` |
  |---:|---:|---:|---:|---:|---:|---:|
  | 1 | 56,0 MB | 1053,7 MB | 872,3 MB | 71,9 MB | 1 | 98,4 |
  | 2 | 71,9 MB | 1103,2 MB | 947,5 MB | 72,2 MB | 1 | 100,0 |
  | 3 | 72,2 MB | 1105,7 MB | 930,9 MB | 72,4 MB | 1 | 100,0 |
  | 4 | 72,4 MB | 1106,1 MB | 931,5 MB | 72,5 MB | 1 | 100,0 |
  | 5 | 72,5 MB | 1105,5 MB | 930,1 MB | 73,2 MB | 1 | 99,9 |

  `median_rueckgabe_prozent=100.0`, `zyklus1_minus_zyklus5_punkte=-1.5`.

- **Das Urteil steht gegen die vorher notierte Erwartung**, nicht gegen eine
  nachtraeglich gewaehlte Zahl:

  | Erwartung | Verlangt | Gemessen | Urteil |
  |---|---|---|---|
  | E1 | Median mindestens 60 Prozent | 100,0 Prozent (schlechtester Zyklus 98,4) | **gehalten** |
  | E2 | `trim_rc = 1` in vier von fuenf Zyklen | 1 in fuenf von fuenf | **gehalten** |
  | E3 | `after_gc` deutlich ueber `after_trim` | kleinster Abstand 856,9 MB; `gc.collect()` gibt 15,1 bis 18,2 Prozent, `malloc_trim(0)` die uebrigen 80,2 bis 84,9 Prozent | **gehalten** |
  | E4 | Zyklus 5 hoechstens 10 Punkte unter Zyklus 1 | minus 1,5 Punkte, Zyklus 5 ist besser | **gehalten** |

- Die Commitreihenfolge ist nachpruefbar: `skripte/00-ablauf.md` ist `6387d2d`
  vom 19.09.2026 14:29:14, die Rohdaten sind `64257e0` vom selben Tag 14:58:16.
  Die Schwelle stand 29 Minuten vor der ersten Zahl fest (T-14-06).
- Der Bodensatz ist benannt statt verschwiegen: ueber fuenf Zyklen steigt der
  Boden von 56,0 MB auf 73,2 MB, also um 17,1 MB, davon 15,9 MB allein im
  ersten Zyklus. Der Bericht sagt ausdruecklich, dass der Store-Text ihn nicht
  verschweigen darf.

## Task Commits

1. **Task 1: Den Lauf fahren und die Rohdaten holen** - `64257e0` (docs)
2. **Task 2: Der Bericht und das Urteil gegen die Erwartung** - `0cb44ca` (docs)
3. **Task 3: Owner-Tor** - offen, siehe Abschnitt "Owner-Entscheid"

## Files Created/Modified

- `docs/measurements/2026-09-entladung-vorpruefung/README.md` - Der Bericht:
  Geltung mit beiden Maschinen und dem Digest, die Zahlen je Architekturast,
  Urteil je Erwartung, Gesamturteil im Wortlaut, was die Messung nicht sagt,
  der Bodensatz und der Architekturvergleich.
- `docs/measurements/2026-09-entladung-vorpruefung/rohdaten/rss-rueckgabe-aarch64.txt` -
  Die fuenf Zyklen des Zielastes, roh, mit vierzeiliger Herkunftsangabe nach
  dem Muster von `2026-09-grundlast-fein/rohdaten/`.
- `docs/measurements/2026-09-entladung-vorpruefung/rohdaten/rss-rueckgabe-x86_64.txt` -
  Derselbe Lauf auf dem Vergleichsast.
- `docs/measurements/2026-09-entladung-vorpruefung/rohdaten/machine.txt` -
  Runner, Rolle, Architektur, Kernel, Kerne, Abbild, Digest, Lauf und Commit
  des Zielastes, unveraendert aus dem Artefakt.
- `docs/measurements/2026-09-entladung-vorpruefung/rohdaten/machine-x86_64.txt` -
  Dasselbe fuer den Vergleichsast.
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` -
  Zustand, Fortschrittszeile und MEM-04 von Hand nachgezogen.

## Decisions Made

- **Der Ausgang ist "Gehalten", und er wird nicht aufgerundet.** Alle vier
  Erwartungen sind erfuellt, also greift der erste der drei Ausgaenge aus
  `skripte/00-ablauf.md` Abschnitt 5. Der Bericht zitiert ihn woertlich und
  stellt zugleich fest, dass die Freigabe damit **vorbereitet und nicht
  erteilt** ist: die Entscheidung ueber 14-03 bis 14-12 liegt am Checkpoint.
- **MEM-04 ist abgehakt.** In 14-01 wurde der Haken zurueckgenommen, weil dort
  keine Zahl erhoben wurde. Jetzt liegt sie vor, auf Zielarchitektur, nativ,
  gegen das ausgelieferte Abbild, mit der Maschine daneben. Das Ablaufdokument
  sagt ausserdem, dass MEM-04 selbst bei einem negativen Ausgang erfuellt
  waere; die Anforderung verlangt den Beleg, nicht ein bestimmtes Ergebnis.
- **Nur vier Dateien aus dem Artefakt.** `welle0-arm64` und `welle0-amd64`
  tragen je zwoelf Dateien; die acht Dateien der Messungen A bis D sind nicht
  die Frage dieses Laufs, und ihre Zahlen stuenden neben den bestehenden
  Berichten, ohne deren Vergleichbarkeitsbedingungen zu erfuellen.
- **Die Rohdateien bekommen eine Herkunftsangabe, keine Bearbeitung.** Vier
  ASCII-Zeilen mit Lauf, Adresse, Commit, Runner und Rolle vor der
  Skriptausgabe, wie es `2026-09-grundlast-fein/rohdaten/` seit Phase 7 macht.
  Die Zahlen selbst sind unangetastet; `machine.txt` und `machine-x86_64.txt`
  sind byteweise Kopien.

## Deviations from Plan

**1. [Rule 3 - Blocker] Die Commits aus 14-01 standen nicht auf `main`**
- **Found during:** Task 1, Schritt 1
- **Issue:** `git rev-list --count origin/main..HEAD` meldete 4. Schritt E lag
  nur lokal; ein `workflow_dispatch` haette den Stand ohne den Schritt gefahren
  und nichts gemessen.
- **Fix:** `git push origin main` vor dem Dispatch. Der Plan sieht genau diesen
  Schritt vor ("Ist der Commit aus 14-01 noch nicht auf main, wird er zuerst
  gemergt").
- **Verification:** Der Lauf traegt `commit=2bc232b4da5e6552a5dad91ffa5fde2656e7b9af`,
  und Schritt E ist in beiden Aesten gelaufen.
- **Commit:** kein eigener, es wurde nur gedrueckt.

**2. [Planfehler, nicht Umsetzungsfehler] Das Digest-Format in `machine.txt`**
- **Found during:** Task 1, Abnahmepruefung
- **Issue:** Das Abnahmekriterium verlangt `digest=sha256:...`. `measure.yml`
  schreibt seit Phase 10 `digest=<abbild>@sha256:...`, weil der Schritt
  "Resolve the image to a digest" `RepoDigests` nach einem `docker pull` liest.
  Das gilt fuer alle bisherigen Messlaeufe dieses Projekts gleichermassen.
- **Fix:** Keiner an der Rohdatei. Eine Messrohdatei wird nicht nachbearbeitet,
  damit sie zu einem Kriterium passt. Der Bericht benennt die Schreibweise in
  Abschnitt 1 ausdruecklich, damit sie nicht als Ungenauigkeit gelesen wird.
- **Verification:** `grep -o 'digest=.*' rohdaten/machine.txt` zeigt den Digest
  vollstaendig; die Zeichenkette hinter dem `@` ist dieselbe, gegen die ein
  spaeterer Lauf dasselbe Abbild adressiert.
- **Commit:** `64257e0` (Rohdaten), `0cb44ca` (Bericht).

**3. [Bauform] Die Rohdatei heisst `aarch64`, das Artefakt `arm64`**
- **Found during:** Task 1, Schritt 5
- **Issue:** `measure.yml` benennt seine Ausgabe nach `matrix.arch`, also
  `rss-rueckgabe-arm64.txt`. Der Plan verlangt `rss-rueckgabe-aarch64.txt`.
- **Fix:** Beim Ablegen umbenannt, wie es `2026-09-grundlast-fein` mit seinen
  Dateien auch tut. Der Inhalt traegt `arch=aarch64` aus dem Prozess selbst,
  der Name folgt also der Datei und nicht der Matrix.
- **Verification:** `grep -c '^zyklus='` gibt 5, `grep 'aarch64' machine.txt`
  trifft.
- **Commit:** `64257e0`.

---

**Total deviations:** 1 nach Regel 3, 2 Bauform- und Kriteriumsabweichungen, 0
architektonische. Kein Fix am Erzeugnis, kein Produktcode.
**Impact on plan:** Kein Zuwachs am Umfang. Beide ausgefuehrten Tasks liefern
genau die Artefakte der Frontmatter.

## Owner-Entscheid

**OFFEN.** Der Checkpoint (Task 3) ist nicht entschieden. Hier wird die Antwort
des Owners im Wortlaut eingetragen, sobald sie vorliegt, dazu bei "teilweise"
jede Auflage einzeln und bei "freigegeben" die Nennung der freigegebenen
Plaene 14-03 bis 14-12.

## Issues Encountered

- Keine. Beide Matrixaeste liefen beim ersten Versuch gruen, der `role:
  target`-Ast war nicht rot, es gab keine Wiederholung und keinen
  Authentifizierungs-Halt.

## Verification

- `test -s rohdaten/rss-rueckgabe-aarch64.txt`, `grep -c '^zyklus='` gleich 5,
  `grep -q 'aarch64' rohdaten/machine.txt`: OK.
- Je eine Zeile `median_rueckgabe_prozent=` und `zyklus1_minus_zyklus5_punkte=`
  in der Zielrohdatei; der Vergleichsast liegt mit fuenf Zyklen daneben.
- `rohdaten/` traegt genau vier Dateien, keine der Messungen A bis D.
- Kein Carriage Return, kein U+2014, kein U+2013, kein Emoji und kein gesperrtes
  Wort in den fuenf neuen Dateien; die Ueberschriften des Berichts stehen ohne
  Umlaute.
- `git status --short backend/src php` ist leer: kein Produktcode veraendert.
- `cd backend && uv run pytest tests/test_measurement_scripts.py -q`: 230 passed.
- `cd backend && uv run pytest -q`: 2132 passed, 15 skipped.
- `git log --format=%ct -1` auf `skripte/00-ablauf.md` ist 1789820954, auf
  `rohdaten/rss-rueckgabe-aarch64.txt` 1789822696: das Ablaufdokument ist
  aelter.

## Known Stubs

Keine. Dieser Plan liefert Rohdaten und einen Bericht; beide sind vollstaendig.
Offen ist allein der Owner-Entscheid, und der ist kein Stub, sondern das Tor.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers des Plans. T-14-05:
die vier Rohdateien tragen Zahlen, Kopfzeilen, Runnernamen und die Ausgabe von
`lscpu` und `free`, keinen Pfad einer Privatmaschine und kein Geheimnis;
gegen das gesperrte Vokabular geprueft. T-14-06: die Commitzeiten beider
Dateien stehen im Bericht. T-14-07: Digest und Commit stehen in `machine.txt`
und werden im Bericht zitiert. T-14-SC: kein Paket installiert.

## Next Phase Readiness

- **Das Tor ist der Owner-Checkpoint.** Erst nach der Antwort steht fest, ob
  Wave 3 (14-03 und folgende) laeuft. Bis dahin entsteht kein Produktcode.
- Bei Freigabe: die Zahlen dieses Laufs sind die Grundlage des Bauens, und der
  Bodensatz von rund 16 MB gehoert von Anfang an in jede Zusage, auch in die
  Store-Texte der Phase 16.
- Phase 15 bleibt zustaendig fuer die drei Fragen, die dieser Lauf nicht
  beantwortet: Ladezeit in Millisekunden auf `m7g.large`, Wiederaufwaerm-Kosten
  mit kaltem Seitencache und das A/B ueber den Schalter auf echtem Bestand.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19 (Tasks 1 und 2; Task 3 offen)*

## Self-Check: PASSED

Alle fuenf neuen Dateien liegen unter den genannten Pfaden, beide Task-Commits
(`64257e0`, `0cb44ca`) sind im Verlauf auffindbar, und diese Zusammenfassung
traegt kein U+2014 und kein U+2013.
