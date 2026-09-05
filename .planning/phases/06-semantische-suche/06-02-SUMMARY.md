---
phase: 06-semantische-suche
plan: 02
subsystem: infra
tags: [messung, benchmark, aarch64, onnxruntime, sqlite-vec, vec0, tokenizer, github-actions, workflow-dispatch, scan-latency]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-01: das Abbild mit int8-Modell an FINDLING_EMBED_MODEL_DIR und vec0.so an FINDLING_VEC0_PATH, plus die Antworten A12 und A13"
  - phase: 05-betriebsbeweis
    provides: "docs/performance.md mit den gemessenen 1.355.205.169 Zeichen ueber 50.068 Dokumente, also 27.067 Zeichen je Dokument"
  - phase: 02-store-und-index
    provides: "backend/src/findling/index/bench.py als Vorbild fuer Aufbau, argparse-Form und den T-02-14-Datenschutzabsatz eines Messwerkzeugs"
provides:
  - "backend/src/findling/embed/bench.py mit drei Messmodi, p50 und p95, und einer Ausgabe aus ausschliesslich Zahlen"
  - ".github/workflows/measure.yml, dispatch-only, ein Job je Architektur gegen das veroeffentlichte Abbild"
  - "die ersetzten Annahmen A1, A2 und A3 und den Boden unter A4, auf x86 und auf nativem aarch64"
  - "das D-04-Verdikt: der gemessene x86/ARM-Faktor ist 1,20 gegen Schwellen von 5,5 und 9,6, der potion-Notausgang bleibt zu"
  - "die Chunkzahl 100.136 und den Vektoranteil je Nutzersuche, beide gerechnet statt geschaetzt"
affects: [06-04 Vektorspeicher und Schema, 06-05 Chunker und Modell-Wrapper, 06-06 Durchstich und Degradieren, 06-07 Embedding-Zweitspur, Store-Text D-17a]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messwerkzeug im ausgelieferten Abbild statt neben ihm: measure.yml zieht das veroeffentlichte Mehrarchitektur-Abbild per Digest und weigert sich, gegen eines ohne das Werkzeug zu laufen"
    - "Dispatch-only-Arbeitsablauf fuer Messungen: keine Gates, kein Lauf je Commit, das Ergebnis gehoert in einen Bericht und nicht in ein Haekchen"
    - "Kalt heisst kalt je Abfrage, nicht einmal am Anfang; wenn der Seitencache nicht verworfen werden kann, sagt die Ausgabe cold_not_enforced statt eine warme Zahl als kalte zu liefern"
    - "Zwei Architekturen aus einer Matrixdefinition, damit ein Unterschied aus der Hardware kommt und nicht aus einem einseitig bearbeiteten Schritt"
    - "Datierter Nachtrag statt Umschreibung: der Stand vor dem arm64-Lauf bleibt stehen, weil er die Grundlage der D-04-Schwellen ist"

key-files:
  created:
    - backend/src/findling/embed/__init__.py
    - backend/src/findling/embed/bench.py
    - backend/tests/test_embed_bench.py
    - .github/workflows/measure.yml
    - docs/measurements/2026-09-05-welle0-arm64/README.md
    - docs/measurements/2026-09-05-welle0-arm64/raw/ (30 Rohdateien, 10 je Vergleichsbasis)
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "A1 ist ersetzt: 3,2947 bis 3,2972 Zeichen je Token fuer laufende deutsche Prosa und 4,0452 fuer reines Vokabular, geschaetzt waren 3,5 mit Bandbreite 3,0 bis 4,0; die zwei Faelle liegen 23 Prozent auseinander und die Schaetzung traf keinen von beiden"
  - "A2 und A3 sind ersetzt: 3.519 bis 4.809 Token je Sekunde auf zwei gepinnten aarch64-Kernen, geschaetzt waren 800 bis 2.000; die Schaetzung war um den Faktor 2 bis 6 zu pessimistisch"
  - "Unter dem Deckel aus D-01 entscheidet A1 die Laufzeit nicht mehr: jedes durchschnittliche Dokument laeuft gegen die 1.024 Token, die eingebettete Menge ist 51.269.632 Token unabhaengig davon, welcher A1-Wert stimmt"
  - "D-04 greift nicht: hoechster gemessener x86/ARM-Faktor 1,20 gegen die Schwellen 5,5 und 9,6; der gedeckelte Erstindex dauert auf nativem aarch64 2 h 58 min bis 4 h 09 min statt der geschaetzten 7 bis 24 Stunden. Owner-Abnahme 05.09.2026: weiter wie geplant"
  - "Der Tokenizer ist architekturunabhaengig, und das ist jetzt belegt statt behauptet: die Tokenzahlen auf aarch64 und x86_64 sind in allen drei Textsorten auf das letzte Token gleich"
  - "int8 mit brute force haelt das Zeitbudget bei der Chunkzahl dieser Phase auf beiden Architekturen: 37,8 ms p95 warm und 153,5 ms kalt je Runde gegen ein Abbruchkriterium von 300 ms, also 4,5 bis 18,4 Prozent des 2,5-Sekunden-Budgets bei drei Runden"
  - "D-10 (Bit-Vektoren nicht bauen, nur dokumentieren) bleibt richtig; D-08 (Abstraktionsschnitt) auch, weil bei einer Million Chunks int8 auch auf ARM warm reisst und bit dieselbe Million kalt haelt"
  - "Der Scan ist speicherbandbreitengebunden und nicht rechengebunden: 1,11 GB/s auf aarch64 gegen 1,13 GB/s auf dem x86-Notebook, bei voellig verschiedener Hardware"
  - "Eine emulierte arm64-Zahl wurde ausdruecklich nicht erzeugt: QEMU haette fuer Messung B einen katastrophalen Ausfall vorgetaeuscht und D-04 ohne Anlass ausgeloest (T-06-09)"
  - "Der Abbildunterschied ist benannt statt weggelassen: die x86-Zahlen stammen aus findling-sem-probe:local, die Laeuferzahlen aus dem veroeffentlichten ghcr-Abbild; der Bericht fuehrt drei Vergleichsbasen und sagt zu jeder Zahl, welche gilt"

patterns-established:
  - "Eine Schwelle wird vor der Messung ausgerechnet und nach der Messung dagegen gestellt, statt das Verdikt aus der Zahl herzuleiten"
  - "Ein Verdikt nennt seine Reserve: nicht nur, dass die Schwelle haelt, sondern um welchen Faktor die noch ungemessene Zielhardware schlechter sein duerfte"

requirements-completed: []
requirements-advanced: [SEM-03]

# Metrics
duration: 2h05m
completed: 2026-09-05
---

# Phase 6 Plan 02: Welle 0 auf aarch64 Summary

**Drei Messungen, die vier tragende Schätzungen dieser Phase durch Zahlen ersetzen, gelaufen auf nativer aarch64-Hardware und auf zwei Vergleichsmaschinen daneben: der gemessene x86/ARM-Faktor ist 1,20 gegen Abbruchschwellen von 5,5 und 9,6, der gedeckelte Erstindex dauert 2 h 58 min bis 4 h 09 min statt der geschätzten 7 bis 24 Stunden, und D-04 greift damit nicht.**

## Performance

- **Duration:** rund 2 h 05 min zwischen erstem und letztem Commit, davon rund 1 h 20 min Wartezeit auf den Owner-Checkpoint und den arm64-Lauf
- **Started:** 2026-09-05T03:43:28Z (erster Commit)
- **Completed:** 2026-09-05T05:48:15Z (letzter Commit)
- **Tasks:** 3 von 3
- **Files modified:** 37 (35 neu, davon 30 Rohdatendateien; 2 geändert)

## Accomplishments

- **Die Phase rechnet ab jetzt nicht mehr gegen sich selbst.** Vier Annahmen aus dem Assumptions Log trugen jede Entscheidung dieser Phase, und alle vier standen als Schätzung da. A1 ist ersetzt (3,29 für Prosa, 4,05 für Vokabular, geschätzt waren 3,5), A2 und A3 sind ersetzt (3.519 bis 4.809 Token je Sekunde auf zwei ARM-Kernen, geschätzt waren 800 bis 2.000), und A4 hat mit der Scan-Latenz-Reihe seinen Boden bekommen.
- **Die eine Zahl, an der die Phase hängen konnte, hängt nicht.** D-04 hält den potion-Notausgang für den Fall bereit, dass selbst der 1.024-Token-Deckel über einem Tag liegt. Gemessen sind auf nativer aarch64-Hardware 2 h 58 min bis 4 h 09 min. Die Zielhardware dürfte gegenüber dem Läufer um den Faktor 5,9 bis 8,0 langsamer sein, bevor die 24 Stunden fallen.
- **Die Behauptung "ein Tokenizer liefert auf jeder Maschine dieselben Token" ist keine Behauptung mehr.** Die Tokenzahlen der drei Textsorten stimmen zwischen aarch64 und x86_64 auf das letzte Token überein: 142.396, 163, 247.204. Das ist der billigste denkbare Beweis, und er kostete einen Job, der ohnehin lief.
- **Die teuerste falsche Zahl dieser Welle wurde nicht erzeugt.** Ein emulierter arm64-Lauf war auf derselben Maschine in Minuten zu haben und hätte für Messung B einen Faktor im zweistelligen Bereich ausgewiesen, weil QEMU den Befehlssatz emuliert. Er hätte wie ein katastrophaler Ausfall ausgesehen und D-04 ohne Anlass ausgelöst. Der Bericht sagt an der Stelle ausdrücklich, warum dort nichts steht (T-06-09).
- **Der Vektoranteil je Nutzersuche ist zum ersten Mal am eigenen Zeitbudget gemessen.** `Provider.php` führt `BUDGET_NANOSECONDS = 2_500_000_000` und `MAX_ROUNDS = 3`, und diese beiden Konstanten waren nie mit der Vektorseite verrechnet worden. Bei der Chunkzahl dieser Phase kostet int8 mit brute force 4,5 Prozent des Budgets warm und 18,4 Prozent kalt.

## Task Commits

1. **Task 1 (RED): Das Gatter über dem Welle-0-Messwerkzeug** - `4518585` (test)
2. **Task 1 (GREEN): Drei Modi, die nur Zahlen ausgeben** - `db32d27` (feat)
3. **Task 2: Der Arbeitsablauf und der Bericht, der drei Schätzungen ersetzt** - `f41ebbd` (feat)
4. **Checkpoint-Zwischenstand in STATE.md** - `55e8a0e` (docs)
5. **Task 3: Die aarch64-Spalte, das D-04-Verdikt und die Owner-Abnahme** - `d84fbbc` (docs)

## Files Created/Modified

- `backend/src/findling/embed/bench.py` - drei Modi (`chars-per-token`, `tokens-per-second`, `scan-latency`), p50 und p95, `--vector-type` für int8 und bit, `--cache` für warm und kalt, `--batch` und `--sequence` für die zwei RAM-Hebel; Vorgabe von `--sizes` enthält die 100000 aus Erfolgskriterium 4 samt Kommentar; `FINDLING_EMBED_MODEL_DIR` und `FINDLING_VEC0_PATH` sind Pflicht und werden nie geraten
- `backend/tests/test_embed_bench.py` - 593 Zeilen über die sieben Verhaltensweisen, darunter der Leckprüfer gegen jedes Wort des gelesenen Textes, das Rotfahren des Kalt-Etiketts und drei Antivakuitätsklauseln
- `backend/src/findling/embed/__init__.py` - Paket-Init nach dem Muster von `index/__init__.py`
- `.github/workflows/measure.yml` - `workflow_dispatch` als einziger Auslöser, zwei Läufer aus einer Matrixdefinition, Digest-Auflösung mit Musterprüfung der Eingabe, ein eigener Schritt, der ein Abbild ohne das Messwerkzeug mit benannter Meldung abweist, `--privileged --user 0` nur an Messung C und mit Begründung im Kommentar
- `docs/measurements/2026-09-05-welle0-arm64/README.md` - der Bericht: Umgebung, Kommandozeilen, drei Messungen, drei Ableitungen, und seit dem 05.09.2026 der Nachtrag mit der aarch64-Spalte, dem D-04-Verdikt und der Owner-Abnahme
- `docs/measurements/2026-09-05-welle0-arm64/raw/` - 30 Rohdateien: `amd64-*` vom lokalen x86-Notebook, `arm64-*` vom Zielläufer, `runner-amd64-*` vom Vergleichsläufer

## Die Zahlen in Kurzform

**Messung A, Zeichen je Token** (ersetzt A1: 3,5, Bandbreite 3,0 bis 4,0)

| Textsorte | aarch64 | x86-Notebook |
|---|---|---|
| Deutsche Prosa | 3,2972 | 3,2947 |
| Referenzkorpus | 4,0429 | 4,0429 |
| Wortliste | 4,0452 | 4,0452 |

**Messung B, Token je Sekunde bei p50** (ersetzt A2 und A3: 800 bis 2.000)

| Charge / Sequenz | x86-Notebook | **arm64-Läufer** | amd64-Läufer | Faktor Notebook/ARM |
|---|---|---|---|---|
| 2 / 256 | 5.700 | **4.745** | 2.516 | **1,20** |
| 2 / 512 | 3.451 | **3.640** | 2.112 | **0,95** |
| 8 / 256 | 4.573 | **4.809** | 2.493 | **0,95** |
| 8 / 512 | 3.275 | **3.519** | 2.082 | **0,93** |

**Messung C, int8 bei 100.000 Chunks** (der Boden unter A4)

| Basis | warm p50 | warm p95 | kalt p50 | kalt p95 |
|---|---|---|---|---|
| arm64-Läufer | 37,5 ms | 37,8 ms | 92,0 ms | 153,5 ms |
| x86-Notebook | 34,3 ms | 42,6 ms | 81,4 ms | 107,8 ms |

**Die drei Ableitungen**

| Größe | Ergebnis |
|---|---|
| Chunkzahl bei dem 1.024-Token-Deckel | 100.136, also die 100.000 aus Erfolgskriterium 4 auf 136 genau |
| Dauer der Embedding-Zweitspur, gedeckelt, auf aarch64 | 2 h 58 min bis 4 h 09 min (geschätzt: 7 bis 24 h) |
| Vektoranteil je Nutzersuche, int8, drei Runden | 113,3 ms warm und 460,6 ms kalt, also 4,5 bis 18,4 Prozent von 2,5 s |

## Die Checkpoint-Historie

Der Plan hat einen Checkpoint, und er ist zweimal angelaufen worden.

**Erster Anlauf, 05.09.2026 gegen 03:58 UTC.** Tasks 1 und 2 waren committet, der
Bericht stand, und er stand mit einer benannten Lücke: die native aarch64-Zahl
fehlte, weil `workflow_dispatch` voraussetzt, dass die Arbeitsablaufdatei im
Standardzweig liegt, und der Ausführende nicht pushen darf. Der Executor hat den
Checkpoint mit genau diesem Stand zurückgegeben statt eine emulierte Zahl
einzusetzen, und `55e8a0e` hält ihn in STATE.md fest.

**Der Lauf dazwischen.** Der Orchestrator hat nach dem Push von `8d108a3`
`measure.yml` von Hand ausgelöst. Lauf
[33946845859](https://github.com/street1983nk/nextcloud-search/actions/runs/33946845859),
beide Jobs erfolgreich, 05:18 UTC, Abbild
`ghcr.io/street1983nk/findling_backend:dev` unter
`sha256:86cf2fcddb96bd608a761d6b46e5eaa87e15d46e731af9b911f83407f1f54b45`.

**Zweiter Anlauf und Abnahme, 05.09.2026.** Der Owner hat den Messbericht mit
"weiter wie geplant" abgenommen, also Variante 3a des Checkpoints. Die Phase
läuft mit e5-small und dem 1.024-Token-Deckel weiter, Plan 06-04 zurrt das Schema
fest. Die zweite Frage des Checkpoints (bleibt der Vektoranteil unter 300 ms p95
je Runde?) ist mit 37,8 ms warm und 153,5 ms kalt beantwortet und stellt sich
damit nicht als Owner-Entscheidung. **D-04 wurde nicht angetastet**: die Regel
steht unverändert in 06-CONTEXT.md, und dieser Plan ist der Beleg, dass ihre
Bedingung nicht eingetreten ist.

## Decisions Made

- **D-04 greift nicht, und das Verdikt nennt seine Reserve.** Der höchste gemessene x86/ARM-Faktor ist 1,20, gemessen bei genau der Kombination, deren Schwelle mit 9,6 die höchste ist. In drei von vier Kombinationen ist ARM nicht langsamer, sondern schneller. Die Zielbox dürfte gegenüber dem Läufer um den Faktor 5,9 bis 8,0 schlechter sein, bevor der gedeckelte Erstindex 24 Stunden reißt.
- **Der Bericht führt drei Vergleichsbasen und sagt zu jeder Zahl, welche gilt.** Das x86-Notebook ist die Basis der Schwellen 5,5 und 9,6 und deshalb die Basis des Verdikts. Der arm64-Läufer ist die Zielarchitektur. Der amd64-Läufer ist der einzige saubere Architekturvergleich, weil sich zwischen ihm und dem arm64-Lauf außer dem Befehlssatz nichts unterscheidet; dort ist der Neoverse-N2 um den Faktor 1,69 bis 1,93 schneller als der EPYC 9V74.
- **Keine der drei Basen ist die Zielbox, und das steht im Bericht statt daneben.** Der Läufer hat vier dedizierte Kerne, von denen zwei gepinnt wurden; die Zielbox hat zwei geteilte vCPU. Was die Zahlen trägt, ist nicht ihre Nähe zur Zielbox, sondern der Abstand zur Schwelle.
- **Der Store-Text nach D-17a darf die gemessene Dauer nicht als Zusage tragen.** Das Verdikt sagt, dass die Phase nicht kippt, nicht wie lange der Erstindex auf der Box eines Betreibers dauert.
- **Unter dem Deckel aus D-01 entscheidet A1 die Laufzeit nicht mehr, sondern die Abdeckungszusage.** Jedes durchschnittliche Dokument trägt 6.691 bis 8.209 Token und läuft gegen die 1.024. Was A1 stattdessen entscheidet, ist der Anteil aus D-17b: gemessen 12,5 Prozent eines durchschnittlichen Dokuments, geschätzt waren 13,2. Der Store-Text sollte den Anteil nennen und nicht die Tokenzahl.
- **Befund 2 des x86-Laufs hält auf ARM nicht.** Auf dem Notebook war Charge 2 bei Sequenz 256 um ein Viertel schneller als Charge 8; auf aarch64 sind beide gleich, mit 1,3 Prozent für Charge 8. Für Plan 06-05 bleibt Charge 2 die richtige Wahl, aber mit der Begründung "kostet auf der Zielarchitektur keine messbare Zeit" statt "ist zugleich die schnellste".
- **Die 250.000er-Schwelle fällt auf den beiden Maschinen verschieden aus.** Auf dem Notebook riss der kalte Punkt mit 372,7 ms, auf dem Läufer hält er mit 251,1 ms. Der Unterschied liegt in der Platte (NVMe gegen WSL2-Datei), nicht im Prozessor. Die vorsichtige Lesart bleibt stehen: 250.000 ist der Grenzpunkt, und eine von zwei gemessenen Maschinen reißt ihn kalt.
- **Der Nachtrag schreibt nichts um.** Der Abschnitt "Der Stand dieses Berichts" beschreibt die Lage vor dem arm64-Lauf und bleibt unverändert, weil er die Grundlage der Schwellen ist. Er bekommt einen datierten Verweis auf den Nachtrag vorangestellt, damit ihn niemand als aktuellen Stand liest.

## Deviations from Plan

### Auslegungen des Plans, keine Autoreparaturen

**1. Der Checkpoint ist über zwei Ausführungen gelaufen, weil der Executor nicht pushen darf**

Task 2 verlangt "Workflow auslösen, Artefakte holen". `workflow_dispatch` setzt
voraus, dass die Datei im Standardzweig steht, und dorthin kommt sie nur über
einen Push. Der Erstlauf hat den Bericht deshalb mit einer ausdrücklich benannten
Lücke abgeliefert und den Checkpoint zurückgegeben. Die Alternative, eine
emulierte arm64-Zahl aus dem lokal vorhandenen `findling-sem-probe:arm64` zu
nehmen, wurde verworfen und im Bericht mit Begründung als verworfen
dokumentiert: QEMU emuliert den Befehlssatz und ist um ein Vielfaches langsamer,
die Zahl hätte D-04 ohne Anlass ausgelöst (T-06-09).

**2. Der amd64-Vergleichslauf liegt unter dem Präfix `runner-amd64-` und nicht unter `amd64-`**

Der Bericht kündigt in seiner Rohdatentabelle nur ein Präfix `arm64-` an. Die
bestehenden `amd64-`-Dateien stammen aber vom lokalen x86-Notebook und haben ein
anderes Abbild gemessen; der amd64-Job des Arbeitsablaufs hätte sie unter
demselben Namen überschrieben und damit die Grundlage der Schwellen 5,5 und 9,6
still ersetzt. Drittes Präfix statt Kollision, und der Nachtrag sagt in einem
Satz, warum es das gibt.

**3. SEM-03 wird nicht abgehakt, obwohl die Planvorspann-Zeile es vorsieht**

Der Plan führt `requirements: [SEM-03]`, und die Abschlussroutine hat die
Anforderung entsprechend als erfüllt markiert. Das ist zurückgenommen worden.
SEM-03 lautet "Vektor-Schema erst nach Lasttest festgezurrt", und Plan 06-04
führt dieselbe Anforderung: dieser Plan liefert den Lasttest, das Festzurren
selbst steht noch aus. Ein Haken an dieser Stelle hätte eine halb erfüllte
Anforderung als erfüllt ausgewiesen, und zwar in genau dem Dokument, das später
die Vollständigkeit des Release belegen soll. `REQUIREMENTS.md` bleibt deshalb
unverändert, und der Vorspann dieser Summary trennt `requirements-completed`
(leer) von `requirements-advanced` (SEM-03).

**4. Der Nachtrag rechnet Ableitung 1 und 3 ein zweites Mal, statt sie zu übernehmen**

Der Plan verlangt drei Ableitungen, und sie standen bereits im Hauptteil. Der
Nachtrag rechnet Ableitung 1 mit dem leicht abweichenden Prosa-Wert (3,2972 statt
3,2947) gegen und Ableitung 3 mit den aarch64-Latenzen neu, weil eine Ableitung,
die auf einer anderen Architektur zitiert wird als der, auf der sie entstand,
genau die Sorte Zahl ist, gegen die T-06-07 steht.

---

**Total deviations:** 0 autorepariert, 4 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Die Zweiteilung der Ausführung
ist die vorgesehene Wirkung des Checkpoints und keine Abweichung von seinem Sinn.

## Issues Encountered

- **`workflow_dispatch` braucht die Datei im Standardzweig.** Das ist keine Eigenheit dieses Repositoriums, sondern GitHub-Verhalten, und es macht jeden Arbeitsablauf, der sich selbst zum ersten Mal auslösen soll, zu einem Zwei-Schritte-Vorgang. Für künftige Messpläne heißt das: der Push gehört vor den Checkpoint und nicht dahinter.
- **Die kalte Reihe streut auf dem Läufer stärker als auf dem Notebook.** Bei 100.000 Chunks int8 liegt der kalte p95 bei 153,5 ms und der schlechteste Einzelfall bei 566,0 ms. Ein Ausreißer unter hundert Abfragen ist kein p95, aber er ist im Bericht genannt, weil er zeigt, wo die kalte Spalte ihre Unruhe hat.
- **Das lokal gemessene Abbild und das gemessene Läuferabbild sind nicht dasselbe Artefakt.** Beide stammen aus demselben `backend/Dockerfile`, aber `findling-sem-probe:local` wurde nie veröffentlicht und trägt das Messmodul nur als Bind-Mount. Der Nachtrag nennt beide Kennungen nebeneinander, damit die zwei Spalten nicht als zwei Läufe desselben Artefakts gelesen werden.

## Offene Verifikation

Keine. Der Arbeitsablauf ist auf beiden Architekturen grün gelaufen, alle
Rohdaten liegen im Repositorium, und der Owner hat abgenommen.

Was offen bleibt, ist keine Verifikation, sondern eine ungemessene Größe: **die
Zahl auf der Zielbox selbst.** Sie ist im Bericht als offen benannt und durch die
Reserve von Faktor 5,9 bis 8,0 gedeckt. Ebenfalls unverändert offen und
ausdrücklich nicht Gegenstand dieses Plans: A5 (die RAM-Spitze beim Einbetten,
gehört an den Lasttest der Zweitspur), A8 (ob `vec0` mit Metadaten- und
Partitionsspalten schneller oder langsamer wird), der Qualitätsverlust von
Bit-Vektoren auf Deutsch, und wie viele Dokumente unter 1.024 Token liegen.

## User Setup Required

None. Der Arbeitsablauf ist dispatch-only und braucht keinen Schlüssel über den
lesend gescopten `GITHUB_TOKEN` hinaus. Die AWS-Box wurde nicht angefasst.

## Next Phase Readiness

- **Plan 06-04 kann das Schema festzurren.** Erfolgskriterium 4 verlangt einen Lasttest über mindestens 50.000 synthetische Dokumente vor der Festlegung; die Scan-Latenz-Reihe deckt 100.000 Chunks ab und das Zehnfache darüber, auf beiden Architekturen, in int8 und in bit, warm und kalt. Die Zahl, gegen die der Vektordeckel in 06-06 bemessen wird, steht damit im Repositorium.
- **Plan 06-05 bekommt die zwei RAM-Hebel als Messung statt als Vermutung.** Sequenzlänge schlägt Chargengröße (37 bis 40 Prozent Durchsatzgewinn von 512 auf 256 Token), und Charge 2 kostet auf der Zielarchitektur keine messbare Zeit gegenüber Charge 8. Die sparsame Wahl ist damit auch die zeitlich unbedenkliche.
- **Plan 06-07 hat eine Laufzeit für die Zweitspur.** 2 h 58 min bis 4 h 09 min für den gedeckelten Erstindex auf zwei ARM-Kernen, mit dem ausdrücklichen Vorbehalt, dass die Zielbox geteilte vCPU hat.
- **Der Store-Text (D-17) bekommt zwei Zahlen und eine Warnung.** Die Abdeckung ist mit 12,5 Prozent eines durchschnittlichen Dokuments gemessen und gehört als Anteil in den Text, nicht als Tokenzahl. Die Erstindexdauer gehört nicht hinein, solange sie nur auf einem Läufer gemessen ist.
- **Kein Blocker aus diesem Plan.** D-04 ist geprüft und hält.

## Self-Check: PASSED

Alle fünf Kerndateien und alle 30 Rohdateien liegen auf der Platte, alle fünf
Commits stehen in `git log`. Zusätzlich geprüft: der Lauf 33946845859 ist über
`gh run view` als `success` in beiden Jobs bestätigt, keine der vier
`scan-latency`-Rohdateien trägt eine `cold_not_enforced`-Zeile, die
Tokenzahlgleichheit zwischen aarch64 und x86_64 ist über die Rohdateien
nachgezählt, und weder Geviert- noch Halbgeviertstrich stehen im Bericht.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
