# Vorprueflauf zur Entladung, gemessen am 19.09.2026

Dieser Bericht beantwortet die eine Frage aus
[`skripte/00-ablauf.md`](skripte/00-ablauf.md): gibt der Container den Speicher
nach einem Loslassen von Tokenizer, Splitter und Inferenzsitzung an das
Betriebssystem zurück, auf aarch64, gegen das ausgelieferte Abbild.

Die Überschriften dieses Berichts stehen ohne Umlaute, weil Prüfungen und
Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute, die Rohdateien
stehen in ASCII, weil sie in einem Container entstanden sind, dessen
Gebietsschema niemand garantiert.

---

## 1. Geltung

| Was | Zielast | Vergleichsast |
|---|---|---|
| Runner | `ubuntu-24.04-arm` | `ubuntu-24.04` |
| Rolle im Lauf | `role=target` | `role=comparison` |
| Architektur laut Prozess | `aarch64` | `x86_64` |
| Prozessor | ARM Neoverse-N2, 4 Kerne | AMD EPYC 7763, 4 Kerne |
| Kernel | `6.17.0-1022-azure` | `6.17.0-1022-azure` |
| Speicher der Maschine | 15.947 MB | 15.989 MB |
| Python im Abbild | 3.13.15 | 3.13.15 |
| `onnxruntime` | 1.30.0 | 1.30.0 |
| `tokenizers` | 0.23.2 | 0.23.2 |
| Rohdatei | [`rohdaten/rss-rueckgabe-aarch64.txt`](rohdaten/rss-rueckgabe-aarch64.txt) | [`rohdaten/rss-rueckgabe-x86_64.txt`](rohdaten/rss-rueckgabe-x86_64.txt) |
| Maschine, vollstaendig | [`rohdaten/machine.txt`](rohdaten/machine.txt) | [`rohdaten/machine-x86_64.txt`](rohdaten/machine-x86_64.txt) |

Beide Äste messen dasselbe Abbild:
`ghcr.io/street1983nk/findling_backend:dev`, aufgelöst auf den Manifestindex
`sha256:31c905b212d815d9ba5deea29a44b90bd8564baa3c4a5bd48ea13876ef31e538`.
Gemessen wurde aus Commit `2bc232b4da5e6552a5dad91ffa5fde2656e7b9af`, Lauf
[35443822228](https://github.com/street1983nk/nextcloud-search/actions/runs/35443822228),
Schritt `E, RSS returned by a release` in `.github/workflows/measure.yml`, mit
`--network none` und `--cpuset-cpus 0,1`. Beide Äste sind grün durchgelaufen,
keiner wurde wiederholt.

**Die Erwartung stand vor dem Lauf fest.** `skripte/00-ablauf.md` mit E1 bis E4
und den Zahlen 60 Prozent und 10 Prozentpunkte ist Commit `6387d2d` vom
19.09.2026, 14:29:14 (+0200). Die Rohdaten dieses Berichts sind Commit
`64257e0` vom selben Tag, 14:58:16, also 29 Minuten später. `git log --follow`
auf beide Pfade zeigt die Reihenfolge; eine nachträglich bewegte Schwelle würde
dort sichtbar.

Eine Randbemerkung zum Digest, damit sie nicht als Ungenauigkeit gelesen wird:
`machine.txt` schreibt ihn in der Form `digest=<abbild>@sha256:...` und nicht
als nacktes `digest=sha256:...`. Das ist die Ausgabe des Schritts "Resolve the
image to a digest" seit Phase 10 und über alle bisherigen Messläufe hinweg
gleich; die Zeichenkette hinter dem `@` ist die, gegen die ein späterer Lauf
dasselbe Abbild adressiert.

---

## 2. Die Zahlen

Vier Marken je Zyklus, gelesen als `VmRSS` aus `/proc/self/status`. Die Werte
stehen hier in MB mit einer Nachkommastelle, die Rohdateien führen dieselben
Zahlen in KB.

### 2.1 Zielast, aarch64, `ubuntu-24.04-arm`

| Zyklus | `baseline` | `loaded` | `after_gc` | `after_trim` | `trim_rc` | `rueckgabe_prozent` |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 56,0 MB | 1053,7 MB | 872,3 MB | 71,9 MB | 1 | 98,4 |
| 2 | 71,9 MB | 1103,2 MB | 947,5 MB | 72,2 MB | 1 | 100,0 |
| 3 | 72,2 MB | 1105,7 MB | 930,9 MB | 72,4 MB | 1 | 100,0 |
| 4 | 72,4 MB | 1106,1 MB | 931,5 MB | 72,5 MB | 1 | 100,0 |
| 5 | 72,5 MB | 1105,5 MB | 930,1 MB | 73,2 MB | 1 | 99,9 |

`median_rueckgabe_prozent=100.0`, `zyklus1_minus_zyklus5_punkte=-1.5`.

### 2.2 Vergleichsast, x86_64, `ubuntu-24.04`

| Zyklus | `baseline` | `loaded` | `after_gc` | `after_trim` | `trim_rc` | `rueckgabe_prozent` |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 55,2 MB | 1052,6 MB | 878,8 MB | 70,5 MB | 1 | 98,5 |
| 2 | 70,5 MB | 1103,2 MB | 880,0 MB | 70,9 MB | 1 | 100,0 |
| 3 | 70,9 MB | 1102,6 MB | 880,1 MB | 70,9 MB | 1 | 100,0 |
| 4 | 70,9 MB | 1104,0 MB | 881,4 MB | 71,6 MB | 1 | 99,9 |
| 5 | 71,6 MB | 1105,3 MB | 881,4 MB | 71,7 MB | 1 | 100,0 |

`median_rueckgabe_prozent=100.0`, `zyklus1_minus_zyklus5_punkte=-1.5`.

Die 100,0 sind gerundet und nicht exakt: in Zyklus 2 des Zielastes stehen
1.055.760 KB Rückgabe gegen 1.056.056 KB Ladung, also 99,97 Prozent. Der
verbleibende Rest von 296 KB ist der Teil, der in Abschnitt 6 als Bodensatz
steht.

---

## 3. Urteil je Erwartung

Geurteilt wird ausschließlich über den Ast mit `role: target`, also über
aarch64. Der Vergleichsast urteilt nicht mit, er steht in Abschnitt 7.

- **E1: gehalten.** Verlangt war ein Median von mindestens 60 Prozent, gemessen
  wurden **100,0 Prozent** über fünf Zyklen. Der schlechteste Einzelzyklus ist
  der erste mit 98,4 Prozent und liegt damit 38 Prozentpunkte über der
  Schwelle.
- **E2: gehalten.** Verlangt war `trim_rc = 1` in mindestens vier von fünf
  Zyklen, gemessen wurde **1 in fünf von fünf**. `malloc_trim` hat in jedem
  Zyklus gemeldet, dass es Speicher an das Betriebssystem zurückgegeben hat.
- **E3: gehalten.** Verlangt war, dass `after_gc` in jedem Zyklus deutlich über
  `after_trim` liegt. Der kleinste Abstand der fünf Zyklen liegt bei
  **856,9 MB** (Zyklus 5: 930,1 MB gegen 73,2 MB). In Anteilen der Ladung
  gerechnet gibt `gc.collect()` allein zwischen 15,1 und 18,2 Prozent zurück,
  `malloc_trim(0)` die übrigen 80,2 bis 84,9 Prozent. Der wirksame Schritt ist
  der zweite, und der Schutzschalter um `ctypes.CDLL` ist damit kein toter
  Zweig, sondern die Stelle, an der auf einer libc ohne `malloc_trim` vier
  Fünftel der Rückgabe ausfallen würden.
- **E4: gehalten.** Verlangt war, dass Zyklus 5 höchstens 10 Prozentpunkte
  unter Zyklus 1 liegt. Gemessen wurde **-1,5 Prozentpunkte**, das heißt
  Zyklus 5 gibt mehr zurück als Zyklus 1 (99,9 gegen 98,4). Die befürchtete
  Verschlechterung über die Zyklen durch den dynamisch angehobenen
  `M_MMAP_THRESHOLD` ist über fünf Zyklen nicht eingetreten. Die Kurve steigt
  nach dem ersten Zyklus und bleibt danach flach.

---

## 4. Gesamturteil

Der Ausgang ist der erste der drei in `skripte/00-ablauf.md` Abschnitt 5
vorgesehenen, im Wortlaut:

> **Gehalten.** E1, E2, E3 und E4 alle gehalten. Der Vorprüflauf ist bestanden.
> Die folgenden Wellen dieser Phase sind frei, der Bau der Entladefunktion darf
> beginnen.

Die Freigabe der folgenden Wellen ist damit **nicht** erteilt, sondern
vorbereitet: der Entscheid darüber liegt beim Owner am Checkpoint des Plans
14-02 und nicht in diesem Bericht.

**MEM-04 ist mit diesem Bericht erfüllt.** Der Beleg der tatsächlichen
RSS-Rückgabe liegt auf der Zielarchitektur vor, gemessen gegen das
ausgelieferte Abbild und nicht gegen einen eigens gebauten Baum, nativ und
nicht emuliert.

---

## 5. Was diese Messung nicht sagt

Drei Fragen bleiben offen, und alle drei liegen in Phase 15 auf der gemieteten
Box:

1. **Die Ladezeit in Millisekunden.** `ubuntu-24.04-arm` ist ein
   Vier-Kern-Runner mit einem Neoverse-N2 und nicht `m7g.large`. Übertragbar
   ist die Rückgabequote, weil sie ein Verhältnis aus zwei Speicherzahlen
   desselben Prozesses ist; die Ladezeit hängt an Kernzahl, Takt und
   Datenträger und ist es nicht. Sie entscheidet den Vorgabewert der
   Leerlauffrist und die Frage nach der 1,5-Sekunden-Decke, und dieser Lauf hat
   sie nicht einmal gemessen.
2. **Die Wiederaufwaerm-Kosten mit kaltem Seitencache.** Alle fünf Zyklen
   dieses Laufs liefen hintereinander im selben Container, also mit warmem
   Seitencache: die Modelldatei lag nach dem ersten Zyklus im Cache des Kernels.
   Ein echtes Nachladen nach einer Leerlaufpause kann von der Platte kommen
   müssen, und was das kostet, sagt dieser Lauf nicht.
3. **Das A/B über den Schalter.** Ob eine Entladung auf einem echten Bestand
   mit echter Suchlast mehr Speicher spart, als sie an Nachladezeit kostet, ist
   eine Abwägung gegen Nutzungsverhalten und keine Messung dieses Runners. Hier
   steht nur, ob der Speicher überhaupt zurückkommt.

---

## 6. Der Bodensatz

Die Entladung führt nicht auf den Stand vor dem Laden zurück, sondern auf
diesen plus einen Rest. Die Differenz zwischen `after_trim` und `baseline` ist
dieser Rest, und er kommt nicht wieder: die Modulimporte von `onnxruntime` und
`numpy` bleiben geladen, egal wie oft entladen wird.

Auf dem Zielast:

| Zyklus | `after_trim` minus `baseline` |
|---:|---:|
| 1 | 15,9 MB |
| 2 | 0,3 MB |
| 3 | 0,2 MB |
| 4 | 0,1 MB |
| 5 | 0,6 MB |

Über die fünf Zyklen steigt der Boden von 56,0 MB auf 73,2 MB, also um
**17,1 MB**, davon 15,9 MB allein im ersten Zyklus. Nach dem ersten Zyklus
liegt der Zuwachs bei zwei bis sechs Zehnteln eines Megabytes je Zyklus und
damit in der Größenordnung des Messrauschens; eine über hundert Zyklen
hochgerechnete Kurve daraus wäre eine Behauptung und keine Messung. Der
Vergleichsast zeigt dasselbe Bild mit 16,6 MB Gesamtanstieg und 15,3 MB im
ersten Zyklus, die Vorrecherche auf nativem x86_64 hatte 12,1 MB gemessen.

**Der Store-Text darf diesen Bodensatz nicht verschweigen.** Wer "der Container
gibt den Modellspeicher vollständig zurück" schreibt, verspricht die Rückkehr
auf die Grundlast eines Containers, der nie eingebettet hat. Richtig ist: er
kehrt auf diese Grundlast plus rund 16 MB zurück, gemessen auf der
Zielarchitektur.

Eine Beobachtung dazu, die das Skript nicht ausrechnet, die aber in den
Rohdaten steht: der `baseline`-Wert eines Zyklus ist der `after_trim`-Wert des
vorigen, in Zyklus 2 auf das Kilobyte genau (73.648 KB in beiden Zeilen). Der
Bodensatz wächst also nicht zwischen den Zyklen, sondern die Messung beginnt
jeden Zyklus genau dort, wo der vorige aufgehört hat.

---

## 7. Architekturvergleich

Die beiden Äste liegen so eng beieinander, dass der Bericht die Architektur
nicht als Risiko führen muss. Der Median der Rückgabe ist auf beiden 100,0
Prozent, der schlechteste Einzelzyklus liegt bei 98,4 gegen 98,5 Prozent, die
Differenz zwischen Zyklus 1 und Zyklus 5 ist auf beiden Ästen -1,5
Prozentpunkte, und `trim_rc` ist beidseitig in allen fünf Zyklen 1. Einen
sichtbaren Unterschied gibt es nur in der Aufteilung zwischen den beiden
Schritten: `gc.collect()` gibt auf x86_64 rund 21,6 Prozent zurück und auf
aarch64 rund 17 Prozent, `malloc_trim(0)` entsprechend umgekehrt. Am Ergebnis
ändert das nichts, weil beide Schritte nacheinander laufen.

Was hier übertragen werden darf, ist die Rückgabequote. Die Zeit ist es nicht:
dieser Lauf hat auf beiden Ästen keine Zeit gemessen, und selbst wenn er es
getan hätte, wären es die Zeiten zweier Vier-Kern-Runner in derselben
Azure-Flotte und nicht die einer `m7g.large`.
