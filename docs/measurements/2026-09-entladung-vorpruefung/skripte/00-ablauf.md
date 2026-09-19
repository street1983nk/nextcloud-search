# Der Ablauf des Vorprueflaufs zur Entladung, in seiner Reihenfolge

**Geschrieben am 19.09.2026, vor dem Lauf.** Diese Datei ist der Ablaufplan des
Laufs im Verzeichnis `docs/measurements/2026-09-entladung-vorpruefung/`. Sie
beschreibt den Lauf, **bevor** er stattfindet, und das ist ihr einziger Zweck:
die Erwartung steht weiter unten mit Zahlen da, damit sie nach der Messung nicht
zur Erklärung des Ergebnisses werden kann. Eine Schwelle, die nach der Zahl
festgelegt wird, ist keine Schwelle.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt durchgehend echte
Umlaute. Das Messskript dieses Verzeichnisses schreibt seine Kommentare und
Ausgabezeilen in ASCII, weil es in einem Container läuft, dessen Gebietsschema
niemand garantiert.

---

## 1. Geltung und Frage

Dieser Lauf beantwortet **eine** Frage: gibt der Container den Speicher nach
einem Loslassen von Tokenizer, Splitter und Inferenzsitzung an das
Betriebssystem zurück, auf aarch64, gegen das ausgelieferte Abbild.

Er gehört zu **MEM-04** und zu **Erfolgskriterium 1 der Phase 14**: der Beleg
der tatsächlichen RSS-Rückgabe auf Zielhardware steht vor dem Bau der
Entladefunktion und nicht danach. Alles, was diese Phase an Produktcode vorhat,
hängt am Ergebnis dieses Laufs.

Er beantwortet ausdrücklich **nicht**, ob eine Entladung sich im Alltag lohnt,
wie lange ein Nachladen dauert und wie oft entladen werden sollte. Das sind drei
weitere Fragen mit drei eigenen Messungen.

**Ein negatives Ergebnis ist ein legitimer Ausgang.** Fällt die Rückgabe unter
die Schwelle in Abschnitt 4, wird die Phase als
"gemessen, Ergebnis negativ" dokumentiert und die Funktion wird nicht gebaut.
Eine gemessene Absage
ist ein Ergebnis dieser Phase und kein Fehlschlag, und sie ist billiger als ein
Feature, das eine Zusage trägt, die die Hardware nicht einlöst.

---

## 2. Was gemessen wird

Vier Marken je Zyklus, gelesen als `VmRSS` aus `/proc/self/status`, nach dem
Muster von `index/wordlist.py::rss_bytes`:

| Marke | Wann sie gelesen wird | Was sie enthaelt |
|---|---|---|
| `baseline` | nach den Modulimporten, vor dem ersten Laden | der Bodensatz der Importe, der nie zurückkommt |
| `loaded` | nach Tokenizer, Splitter, Encoder, Sitzung und **einem** `run` | alles Geladene samt Aktivierungsspeicher |
| `after_gc` | nach dem Loslassen aller Referenzen plus `gc.collect()`, **ohne** `malloc_trim` | was die Sprachlaufzeit allein zurückgibt |
| `after_trim` | nach `malloc_trim(0)`, mit dessen Rückgabewert | was das Betriebssystem wirklich zurückbekommt |

Der eine `run` gehört dazu und ist kein Beiwerk: der Aktivierungsspeicher des
ersten `run` ist der größte Einzelposten der ganzen Ladung, er bleibt liegen,
obwohl `enable_cpu_mem_arena = False` gesetzt ist, und er verschwindet erst mit
der Entladung. Ein Zyklus ohne `run` würde den großen Posten der Frage aus dem
Bild nehmen.

**Fuenf Zyklen, nicht einer.** glibc hebt `M_MMAP_THRESHOLD` während der
Freigabe großer Blöcke dynamisch an, und die Konsequenz ist, dass Zyklus 5 nicht
aussehen muss wie Zyklus 1: spätere Ladungen können aus der Arena bedient werden
statt per `mmap`, und dann gibt `malloc_trim` weniger zurück. Ein einziger
Zyklus ist deshalb kein Beleg für einen Container, der Wochen läuft.

---

## 3. Die Messgroesse

```
rueckgabe_prozent = (loaded - after_trim) / (loaded - baseline) * 100
```

Also: welcher Anteil dessen, was das Laden gekostet hat, kommt wieder.

Diese Größe und ausdrücklich **nicht** "Grundlast minus X". Die Grundlast dieses
Containers wird seit dem faulen Bau von Plan 07-03 bereits **ohne** Modell und
ohne Cutter gemessen; eine Ersparnis gegen sie zu rechnen würde eine Zahl
erzeugen, die es nie gab. Die Messgröße heißt hier schon so, wie sie später im
Bericht und im Store-Text heißen muss.

Der Nenner ist `loaded - baseline` und nicht `loaded`, weil der Import-Bodensatz
von onnxruntime und numpy nicht zurückkommen kann: die Module bleiben geladen.
Eine Rückgabequote, die diesen Bodensatz im Nenner trägt, wäre systematisch zu
niedrig und würde die Funktion schlechter aussehen lassen, als sie ist.

---

## 4. Erwartung, vor dem Lauf notiert

Dieser Abschnitt ist der Grund, warum diese Datei vor dem Lauf entsteht. Was
hier steht, wird nach der Messung **nicht** angepasst.

- **E1: Der Median von `rueckgabe_prozent` über die fünf Zyklen liegt bei
  mindestens 60 Prozent** auf dem Ast mit `role: target`, also auf `aarch64`.
  Herleitung: auf nativem x86_64 wurden in der Vorrecherche 97,2 Prozent
  gemessen, die qemu-Gegenprobe kommt trotz Emulationsaufschlag auf 71,4
  Prozent. 60 ist der Boden, unter dem die Funktion ihren Preis nicht wert ist:
  unterhalb davon bleibt nach einer Entladung so viel liegen, dass sich das
  Nachladen, die zweite Ladezeit und der ganze Zustandsapparat nicht
  rechtfertigen lassen.

- **E2: `trim_rc` ist in mindestens vier der fünf Zyklen 1.** `malloc_trim`
  meldet mit 1, dass es Speicher zurückgegeben hat, und mit 0, dass es nichts
  zurückgeben konnte. Ein `trim_rc` von durchgehend 0 heißt, dass `malloc_trim`
  nichts zurückgegeben hat, und macht E1 unglaubwürdig, selbst wenn die
  Prozentzahl passt.

- **E3: `after_gc` liegt in jedem Zyklus deutlich über `after_trim`.** Das ist
  der Beleg, dass `malloc_trim` und nicht `gc.collect()` der wirksame Schritt
  ist, und damit zugleich der Beleg, dass der Schutzschalter um `ctypes.CDLL`
  kein toter Zweig ist: auf einer libc ohne `malloc_trim` fällt genau der
  Löwenanteil der Rückgabe aus. Ein Container, in dem `gc.collect()` allein
  schon fast alles zurückgibt, braucht diese Phase nicht.

- **E4: `rueckgabe_prozent` von Zyklus 5 liegt höchstens 10 Prozentpunkte unter
  dem von Zyklus 1.** Fällt die Kurve stärker, ist die Entladung über die Zyklen
  hinweg schlechter statt besser, und das ist der dynamische
  `M_MMAP_THRESHOLD` aus Abschnitt 2. Dieser Befund gehört in den Bericht, auch
  wenn E1 gehalten wird, weil ein Container in der Praxis nicht fünfmal
  entlädt, sondern hundertmal.

**Eine verfehlte Erwartung ist ein Ergebnis und kein Grund für einen zweiten
Lauf mit anderen Zahlen.** Wird eine der vier gerissen, steht sie so im Bericht.

---

## 5. Ausgaenge

| Ausgang | Bedingung | Folge |
|---|---|---|
| **Gehalten** | E1, E2, E3 und E4 alle gehalten | Der Vorprüflauf ist bestanden. Die folgenden Wellen dieser Phase sind frei, der Bau der Entladefunktion darf beginnen |
| **E1 gerissen** | Der Median liegt unter 60 Prozent | Die Phase endet mit "gemessen, Ergebnis negativ". Es entsteht kein Produktcode, der Bericht nennt die gemessene Quote, die Maschine und das Datum, und MEM-04 gilt damit als erfüllt, nicht als offen |
| **E2 bis E4 gerissen, E1 gehalten** | Die Quote stimmt, aber der Weg dahin ist unklar oder die Kurve fällt über die Zyklen | Kein eigenmächtiges Weiterbauen. Der Owner entscheidet am Checkpoint des folgenden Plans, mit den Zahlen auf dem Tisch |

---

## 6. Vergleichbarkeitsbedingungen

Eine Messung ohne ihre Maschine ist eine Behauptung, die an der falschen
Hardware zitiert wird. Sechs Angaben gehören zu jeder Zahl dieses Laufs:

1. der Digest des gemessenen Abbilds,
2. der Runner, also `ubuntu-24.04-arm` oder `ubuntu-24.04`,
3. `uname -m`,
4. der Kernel,
5. `nproc`,
6. der Commit, gegen den gemessen wurde.

Alle sechs schreibt der Schritt "Write down the machine" in
`.github/workflows/measure.yml` bereits nach `machine.txt`. Dieses Dokument
verlangt nur, dass der Bericht sie **zitiert** und nicht bloß auf die Rohdatei
verweist. Das Messskript selbst druckt Datum, Architektur, Python-Version,
Abbild-Digest, Abbild-Referenz und die Rolle des Astes noch einmal in seinen
eigenen Kopfzeilen, damit eine Rohdatei auch dann ihre Maschine trägt, wenn sie
allein aus dem Artefakt gezogen wird.

---

## 7. Was NICHT gemessen wird

**Die Ladezeit in Millisekunden.** `ubuntu-24.04-arm` ist ein Vier-Kern-Runner
und nicht `m7g.large`. Übertragbar ist die Rückgabequote, weil sie ein
Verhältnis aus zwei Speicherzahlen desselben Prozesses ist; die Ladezeit ist es
nicht, weil sie an Kernzahl, Takt und Datenträger hängt. Die Zeit entscheidet
den Vorgabewert der Leerlauffrist und die Frage nach der 1,5-Sekunden-Decke, und
sie kommt in Phase 15 von der gemieteten Box.

**Die Wirkung auf einen echten Bestand.** Dieser Lauf lädt und entlädt einen
Container ohne Index und ohne Suchlast. Das A/B über den Schalter, mit warmem
und kaltem Seitencache, ist eine Messung der Box und nicht dieses Runners.

**Der Nutzen.** Ob eine Entladung im Alltag mehr Speicher spart, als sie an
Nachladezeit kostet, ist eine Abwägung und keine Messung dieses Laufs. Hier
steht nur, ob der Speicher überhaupt zurückkommt.
