# Modellqualität: fp32 gegen int8, dreisprachig, und der Präfixnachweis

Fünfzehn Läufe von `scripts/dev/model_quality.py` gegen das Testset unter
`testdata/semantik`, alle im selben Abbild, alle ohne Netzwerk. Sie beantworten
zwei Fragen, die diese Phase bisher aus zweiter Hand beantwortet hatte: was die
selbst gebaute int8-Quantisierung des Modells kostet (D-02), und ob die
E5-Präfixe wirken (D-05). Getrennt davon gemessen: was die Quantisierung der
gespeicherten Vektoren zusätzlich kostet.

> **Hinweis auf den Nachtrag.** Am Ende dieses Berichts steht der Abschnitt
> "Nachtrag vom 05.09.2026: Französisch auf 120 Fällen". Er ersetzt keine der
> Zahlen unten, sondern stellt die französischen daneben, gemessen auf einem
> Testset, das von 42 auf 120 Fälle verbreitert wurde. Wer das französische
> Verdikt sucht, liest beide Stellen.

## Die beiden Verdikte, zuerst

**Zu D-05: die Präfixe sitzen.** Dieselbe Anfrage mit und ohne `query: `
beziehungsweise `passage: ` liefert eine messbar andere Rangfolge, in allen drei
Sprachen: 21 von 42 Fällen auf Deutsch, 29 von 42 auf Englisch, 31 von 42 auf
Französisch bekommen einen anderen Rang. Der Fall, den der Plan als Alarm
benennt, nämlich gar kein Unterschied, ist nicht eingetreten. Was zusätzlich
herauskam und nicht erwartet war: die Präfixe **helfen** nur auf Deutsch. Auf
Englisch und Französisch liegt die Fassung ohne Präfixe leicht vorne. Alle drei
Unterschiede sind kleiner als ihr eigener Standardfehler; darauf lässt sich
keine Entscheidung stützen, aber es ist eine Beobachtung, die Plan 06-05 kennen
muss.

**Zu D-02: die selbst quantisierte int8-Fassung trägt auf Deutsch und Englisch,
und auf Französisch trägt sie nach der Abbruchregel dieses Plans nicht.** Auf
Deutsch steigt MRR um 2,30 Prozent, auf Englisch um 5,70 Prozent, auf
Französisch fällt es um 9,24 Prozent. Die Grenze des Plans liegt bei 5 Prozent
relativem Rückgang in einer der drei Sprachen. **Sie ist überschritten, dieser
Plan endet deshalb mit einem Befund und nicht mit einem grünen Haken, und die
Entscheidung gehört dem Owner.** Der Abschnitt "Der Befund" unten nennt die drei
offenen Wege und alles, was gegen eine überstürzte Reaktion spricht.

## Die Umgebung dieser Messung

| Angabe | Wert |
|---|---|
| Datum | 2026-09-05 |
| Abbild | `findling-sem-probe:local`, lokaler Bau aus `backend/Dockerfile` (Plan 06-01) |
| Abbildkennung | `sha256:c9bb41d65746c584480ad05569445a2c36c6f347543f983d42416cedb02bfef9` |
| Maschine | x86_64, 13th Gen Intel Core i5-1335U, 12 sichtbare Kerne, Docker Desktop unter Windows 11 |
| Python im Abbild | 3.13.15 |
| onnxruntime im Abbild | 1.29.0, `CPUExecutionProvider`, `intra_op_num_threads = 2` |
| numpy, tokenizers | 2.5.2, 0.23.2 |
| Netzwerk | in jedem der fünfzehn Läufe abgeklemmt (`--network none`) |
| Tokenizer | `/usr/local/share/findling/model`, in allen Läufen derselbe |

Es ist kein Registry-Digest: dieses Abbild wurde nie veröffentlicht. Es ist
dieselbe Kennung, unter der die Proben A12 und A13 sowie die Welle-0-Messungen
gelaufen sind.

**Die Kerne sind hier nicht gepinnt**, anders als bei den Welle-0-Messungen.
Das ist Absicht: gemessen wird eine Rangfolge, und die hängt nicht davon ab, wie
viele Kerne sie erzeugt haben. Über Geschwindigkeit sagt dieser Bericht nichts.

### Die beiden Modellfassungen

| Datei | Byte | sha256 |
|---|---|---|
| fp32, `onnx/model.onnx` von `intfloat/multilingual-e5-small`, Revision `614241f6` | 470.268.510 | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` |
| int8, erzeugt daraus mit `scripts/dev/quantize_model.py` | 118.101.091 | `8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6` |

**Ein Nebenbefund, der die ganze Messung erst belastbar macht:** die hier
erzeugte int8-Datei ist **byteidentisch** mit der Datei, die im Abbild liegt
(`/usr/local/share/findling/model/model.onnx`, dieselbe sha256). Gemessen wird
also nicht eine Nachbildung des ausgelieferten Artefakts, sondern das
ausgelieferte Artefakt selbst, und `quantize_dynamic` ist über zwei getrennte
Läufe hinweg reproduzierbar.

Das fp32-Original wurde für diesen Vergleich einmal geholt und liegt bewusst
außerhalb des Repositoriums; im Abbild existiert es nicht, es wird dort in
derselben Bauschicht gelöscht, in der es heruntergeladen wird.

### Die Kommandozeile

Ein Lauf, wörtlich, so wie fünfzehnmal ausgeführt (nur `--model`, `--dataset`,
`--prefixes` und `--vector-dtype` wechseln):

```bash
docker run --rm --network none \
  -v "$PWD/scripts/dev/model_quality.py:/tmp/model_quality.py:ro" \
  -v "$PWD/testdata/semantik:/tmp/semantik:ro" \
  -v "$FP32_DIR/model.onnx:/model/fp32/model.onnx:ro" \
  -v "$INT8_DIR/model.onnx:/model/int8/model.onnx:ro" \
  --entrypoint /app/.venv/bin/python \
  findling-sem-probe:local /tmp/model_quality.py \
  --model /model/int8/model.onnx \
  --tokenizer /usr/local/share/findling/model \
  --dataset /tmp/semantik/de.jsonl \
  --prefixes on --vector-dtype fp32 --per-case
```

Unter Git Bash gehört `MSYS_NO_PATHCONV=1` davor, sonst baut die Shell die
Einhängepfade um. Das Abbild aus Plan 06-01 kennt `model_quality.py` nicht, das
Werkzeug kommt deshalb als schreibgeschützte Einhängung aus dem Arbeitsbaum;
Modell, Tokenizer, onnxruntime, numpy und CPython stammen aus dem Abbild.

## Das Testset, und was seine Zahlen bedeuten und was nicht

126 Paare aus einer Umschreibung und dem gemeinten Abschnitt, 42 je Sprache,
beschrieben in `testdata/semantik/README.md`. Die Passagenmenge einer Sprache
ist zugleich ihre Ablenkermenge: jede Anfrage konkurriert gegen 41 andere
Abschnitte.

**Dieses Testset ist mit Absicht hart.** Kein inhaltstragendes Wort einer
Anfrage steht wörtlich in ihrem Abschnitt, ein Test setzt das durch. Die
absoluten Werte unten (Recall@1 zwischen 0,26 und 0,55) sind deshalb eine
**Untergrenze** und keine Note für das Modell: im Betrieb steht neben dem
Vektorzweig die Tantivy-Liste, und die gewinnt genau die Fälle, die hier
verboten sind. Wer diese Zahlen mit NDCG@10 auf MIRACL vergleicht, vergleicht
zwei verschiedene Dinge.

## Die drei Tabellen

Vier Kombinationen je Sprache, alle mit Präfixen an. Die Klammer nennt die
relative Änderung gegenüber der Bezugszeile fp32-Modell mit fp32-Vektoren, in
Prozent.

### Deutsch, `de.jsonl`, 42 Fälle

| Modell | Vektoren | Recall@1 | Recall@5 | MRR |
|---|---|---|---|---|
| fp32 | fp32 | 0,4762 (Bezug) | 0,8333 (Bezug) | 0,6398 (Bezug) |
| fp32 | int8 | 0,4762 (0,00) | 0,8333 (0,00) | 0,6351 (-0,73) |
| int8 | fp32 | 0,5476 (+14,99) | 0,8095 (-2,86) | 0,6545 (+2,30) |
| int8 | int8 | 0,5238 (+10,00) | 0,8095 (-2,86) | 0,6419 (+0,33) |

### Englisch, `en.jsonl`, 42 Fälle

| Modell | Vektoren | Recall@1 | Recall@5 | MRR |
|---|---|---|---|---|
| fp32 | fp32 | 0,2619 (Bezug) | 0,7143 (Bezug) | 0,4647 (Bezug) |
| fp32 | int8 | 0,2857 (+9,09) | 0,7619 (+6,66) | 0,4750 (+2,22) |
| int8 | fp32 | 0,3095 (+18,17) | 0,6905 (-3,33) | 0,4912 (+5,70) |
| int8 | int8 | 0,3095 (+18,17) | 0,6905 (-3,33) | 0,4880 (+5,01) |

### Französisch, `fr.jsonl`, 42 Fälle

| Modell | Vektoren | Recall@1 | Recall@5 | MRR |
|---|---|---|---|---|
| fp32 | fp32 | 0,3810 (Bezug) | 0,6190 (Bezug) | 0,4926 (Bezug) |
| fp32 | int8 | 0,3810 (0,00) | 0,5952 (-3,84) | 0,4913 (-0,26) |
| int8 | fp32 | 0,3095 (-18,77) | 0,5476 (-11,53) | 0,4471 (-9,24) |
| int8 | int8 | 0,3810 (0,00) | 0,5714 (-7,69) | 0,4815 (-2,25) |

## Der Außenmaßstab von Elastic, in einer eigenen Spalte

Elastic hat dasselbe Modell int8-quantisiert und gegen das Original gemessen
(Modellkarte `elastic/multilingual-e5-small-optimized`, abgerufen 04.09.2026,
NDCG@10 auf MIRACL):

| Sprache | Elastic fp32 | Elastic int8 | Änderung | unsere Änderung (MRR, int8-Modell, fp32-Vektoren) |
|---|---|---|---|---|
| Deutsch | 0,75862 | 0,75992 | +0,17 Prozent | +2,30 Prozent |
| Spanisch | 0,81672 | 0,81350 | -0,39 Prozent | nicht gemessen |
| Russisch | 0,80309 | 0,79668 | -0,80 Prozent | nicht gemessen |
| Englisch (BEIR SCIFACT) | 0,67700 | 0,65484 | -3,40 Prozent | +5,70 Prozent |
| Englisch (BEIR FIQA) | 0,33126 | 0,31734 | -4,20 Prozent | (dieselbe Zeile) |
| **Französisch** | **keine Zahl** | **keine Zahl** | **keine Zahl** | **-9,24 Prozent** |

Drei Vorbehalte gehören zu dieser Tabelle, und ohne sie wäre sie eine
Falschaussage:

1. **Elastic quantisiert anders.** Dort steht "per-layer unter denselben
   Bedingungen wie ELSERv2", hier steht ein nackter `quantize_dynamic`-Aufruf.
   Die Elastic-Spalte ist ein Indiz für die Machbarkeit und kein Beleg für
   unser Verfahren. Genau deshalb existiert dieser Bericht.
2. **Für Französisch gibt es dort keine Zahl.** Die Spalte ist leer, nicht
   klein. Unsere -9,24 Prozent lassen sich mit nichts von außen vergleichen.
3. **Die Maßeinheiten sind verschieden.** NDCG@10 auf MIRACL gegen MRR auf 42
   Paraphrasen ohne Wortüberschneidung: die Prozentzahlen der letzten beiden
   Spalten stehen nebeneinander, sie sind nicht ineinander umrechenbar.

## Die Modellquantisierung, paarweise ausgewertet (D-02)

Eine Differenz zweier MRR-Werte über 42 Fälle ist so lange eine Dezimalzahl, bis
jemand nachsieht, wie viele Fälle sich bewegt haben. `--per-case` liefert den
Rang jedes einzelnen Falles, und daraus stammt diese Tabelle. Verglichen wird
int8-Modell gegen fp32-Modell, beide mit fp32-Vektoren, Fall gegen Fall über den
Kehrwert des Ranges:

| Sprache | MRR-Änderung | mittlere Differenz je Fall | Standardfehler | t | Fälle bewegt | davon besser / schlechter |
|---|---|---|---|---|---|---|
| Deutsch | +2,30 Prozent | +0,0147 | 0,0437 | +0,34 | 22 von 42 | 12 / 10 |
| Englisch | +5,70 Prozent | +0,0265 | 0,0241 | +1,10 | 23 von 42 | 10 / 13 |
| Französisch | -9,24 Prozent | -0,0455 | 0,0224 | -2,03 | 25 von 42 | 9 / 16 |

Was daraus abzulesen ist, ohne Beschönigung in die eine wie in die andere
Richtung:

- Der französische Rückgang ist **kein einzelner Ausreißer**. 16 Fälle werden
  schlechter, 9 besser; das ist eine breite Verschiebung dicht beieinander
  liegender Ränge und nicht ein Fall, den man wegdiskutieren kann.
- Er ist zugleich **an der Grenze dessen, was 42 Fälle unterscheiden können**.
  t = -2,03 bei 41 Freiheitsgraden liegt knapp jenseits der üblichen Schwelle.
  Eine dritte Nachkommastelle trägt diese Stichprobe nicht.
- Auf Deutsch und Englisch zeigt die int8-Fassung **nach oben**, und auf
  Englisch stehen dem 13 verschlechterten Fällen nur 10 verbesserte gegenüber:
  der positive Mittelwert kommt aus der Größe der Bewegungen, nicht aus ihrer
  Zahl. Auch das ist Rauschen und wird hier nicht als Qualitätsgewinn verkauft.
- Die Zeile, die das Produkt betrifft, ist **int8-Modell mit int8-Vektoren**,
  denn das ist die ausgelieferte Kombination. Sie steht auf Französisch bei
  -2,25 Prozent, also unter der Grenze. Die Regel des Plans bezieht sich
  ausdrücklich auf die Modellfassung, gemessen bei fp32-Vektoren, und dort ist
  sie überschritten. Beides steht hier, weil beides wahr ist.

## Die Vektorquantisierung, davon getrennt

Die zweite Stufe: nicht die Gewichte, sondern die erzeugten Vektoren, skalar auf
int8, so wie eine `vec0`-Spalte sie hält. Verglichen wird int8-Vektoren gegen
fp32-Vektoren, je Modellfassung, wieder Fall gegen Fall:

| Sprache | Modellfassung | MRR-Änderung | mittlere Differenz je Fall | Standardfehler | t | Fälle bewegt |
|---|---|---|---|---|---|---|
| Deutsch | fp32 | -0,73 Prozent | -0,0046 | 0,0293 | -0,16 | 10 von 42 |
| Deutsch | int8 | -1,93 Prozent | -0,0126 | 0,0140 | -0,90 | 11 von 42 |
| Englisch | fp32 | +2,22 Prozent | +0,0103 | 0,0136 | +0,76 | 16 von 42 |
| Englisch | int8 | -0,65 Prozent | -0,0032 | 0,0032 | -0,99 | 10 von 42 |
| Französisch | fp32 | -0,26 Prozent | -0,0013 | 0,0177 | -0,07 | 18 von 42 |
| Französisch | int8 | +7,69 Prozent | +0,0345 | 0,0203 | +1,70 | 17 von 42 |

**Befund: die Vektorquantisierung kostet auf diesem Testset nichts Messbares.**
Kein einziger der sechs Vergleiche erreicht den doppelten Standardfehler, und
die Vorzeichen wechseln zwischen den Sprachen. Elastic gibt für diese Stufe
1,05 Prozent durchschnittlichen relativen Rückgang über BEIR an, mit dem
Hinweis, E5 sei dabei ein schwieriger Fall; unsere Werte streuen um diesen
Betrag herum und widersprechen ihm nicht.

Die eine auffällige Zeile, die ausdrücklich **nicht** als Gewinn gelesen werden
darf: Französisch mit dem int8-Modell wird durch die Vektorquantisierung um
7,69 Prozent besser. Eine Rundung, die die Qualität hebt, ist ein Zufall und
kein Mechanismus. Sie ist der Grund, warum der französische Wert in der Zeile
int8/int8 der Haupttabelle so viel milder aussieht als in der Zeile int8/fp32,
und sie ist ein weiterer Hinweis darauf, wie dicht die Ränge auf diesem
französischen Satz beieinander liegen.

**Die Verwechslungsgefahr, ausdrücklich benannt:** Modellquantisierung und
Vektorquantisierung werden regelmäßig in einen Topf geworfen. Die 1,05 Prozent
von Elastic gehören zu dieser Tabelle und nicht zu der davor. Der Kommentar am
Schalter `--vector-dtype` in `scripts/dev/model_quality.py` sagt dasselbe an der
Stelle, an der es jemand liest.

## Das Präfix-Verdikt (D-05)

Drei zusätzliche Läufe, int8-Modell, fp32-Vektoren, `--prefixes off`; das
Gegenstück mit `on` steht bereits in den Tabellen oben.

| Sprache | MRR mit Präfixen | MRR ohne | Änderung ohne | Recall@1 mit | ohne | Fälle mit anderem Rang | t der Differenz |
|---|---|---|---|---|---|---|---|
| Deutsch | 0,6545 | 0,6243 | -4,61 Prozent | 0,5476 | 0,4524 | 21 von 42 | +0,60 |
| Englisch | 0,4912 | 0,5014 | +2,08 Prozent | 0,3095 | 0,3333 | 29 von 42 | -0,23 |
| Französisch | 0,4471 | 0,4760 | +6,46 Prozent | 0,3095 | 0,3333 | 31 von 42 | -0,64 |

**Was daraus folgt.** Die Frage von D-05 lautete, ob dieselbe Anfrage mit und
ohne Präfix eine messbar andere Rangfolge liefert. Sie tut es, in jeder der drei
Sprachen und in großem Umfang: die Hälfte bis drei Viertel aller Fälle bekommen
einen anderen Rang. Die Präfixe kommen also dort an, wo sie ankommen sollen, und
der Alarmfall des Plans, nämlich gar kein Unterschied, liegt nicht vor. Für Plan
06-05 heißt das: der Modell-Wrapper muss sie setzen, und dieser Bericht ist der
Beleg dafür, dass ein Vergessen sichtbar wäre.

**Was daraus nicht folgt.** Dass die Präfixe die Qualität heben. Auf Deutsch tun
sie es deutlich (Recall@1 von 0,4524 auf 0,5476), auf Englisch und Französisch
liegt die Fassung ohne Präfixe leicht vorne. Kein einziger der drei Unterschiede
erreicht seinen eigenen Standardfehler, alle drei |t| liegen unter 0,7. Das ist
Rauschen, und die richtige Lesart ist: **auf diesem Testset ist nur für Deutsch
ein Nutzen sichtbar, und selbst der ist statistisch nicht gesichert.**

Die Präfixe bleiben trotzdem an. Zwei Gründe, beide unabhängig von diesen
Zahlen: das Modell ist mit ihnen trainiert worden, und Deutsch ist die
Hauptsprache des Produkts. Ein Abschalten wäre eine Abweichung vom
Modellvertrag, gestützt auf drei Unterschiede, die die Stichprobe nicht trägt.
Das Thema gehört als offene Beobachtung in Plan 06-05, nicht als Änderung.

## Der Befund, und die drei offenen Wege

**Die Abbruchregel dieses Plans ist angewandt und sie greift.** MRR der
int8-Modellfassung fällt auf Französisch um 9,24 Prozent relativ gegenüber der
fp32-Fassung, die Grenze liegt bei 5 Prozent. Der Plan endet damit an dieser
Stelle. Was hier **nicht** passiert: eine Entscheidung. D-02 ist eine
Owner-Entscheidung, und Mehrsprachigkeit ist eine Owner-Anforderung (D-03).

Die drei Wege, die der Plan für diesen Fall vorsieht, mit dem, was diese Messung
über jeden von ihnen sagt:

1. **Eine andere Quantisierungsachse.** `quantize_dynamic` mit
   `QuantType.QInt8` quantisiert heute alles, was es findet, einschließlich der
   Einbettungstabelle mit ihren 81,7 Prozent aller Parameter. Denkbar wäre, die
   Einbettungstabelle auszunehmen oder auf `QUInt8` zu wechseln. Preis: die
   Datei wird größer, im Extremfall bis in die Nähe der 384 MB, gegen die das
   Größengatter aus Plan 06-01 gerichtet ist, und jede Variante braucht wieder
   fünfzehn Läufe. Nutzen: unbekannt, denn die Ursache des französischen
   Rückgangs ist nicht lokalisiert.
2. **Die fp32-Datei ins Abbild, mit ihrem Speicherpreis.** 470 MB statt 118 MB
   im Abbild und im dauerhaften Arbeitsspeicher einer 4-GB-Box. Das Abbild wäre
   nach der Messung aus Plan 06-01 bei rund 1,09 GB statt 740 MB. Für das
   Hardware-Ziel dieses Produkts ist das die teuerste der drei Möglichkeiten,
   und sie kauft nach dieser Messung 9,24 Prozent MRR auf Französisch, während
   sie auf Deutsch und Englisch nichts einbringt oder sogar schadet.
3. **Eine kleinere Zusage im Store-Text.** Die semantische Suche wird für
   Deutsch und Englisch zugesagt und für Französisch als vorhanden, aber nicht
   gemessen gleichwertig beschrieben. Kostet nichts an Technik und ist die
   einzige der drei Möglichkeiten, die keine neue Unbekannte einführt. Sie
   widerspricht allerdings der Formulierung von D-03, nach der Französisch
   Anforderung und nicht Zugabe ist.

**Was gegen eine überstürzte Reaktion spricht, und der Vollständigkeit halber
dazugehört:**

- Der Wert ist mit t = -2,03 gerade eben von Null unterscheidbar. Ein zweites,
  größeres französisches Testset könnte ihn halbieren oder verdoppeln, und
  keines von beiden wäre überraschend.
- Die ausgelieferte Kombination, int8-Modell mit int8-Vektoren, steht auf
  Französisch bei -2,25 Prozent.
- Im Betrieb steht der Vektorzweig nicht allein: RRF verschmilzt ihn mit der
  Tantivy-Liste, und ein Rangverlust im Vektorzweig schlägt gedämpft durch. Wie
  stark gedämpft, weiß dieser Bericht nicht; das ist eine Messung für den Plan,
  der die Verschmelzung baut.
- Der billigste nächste Schritt wäre kein Umbau, sondern mehr französische
  Fälle. Ein Satz von 120 statt 42 würde den Standardfehler etwa halbieren und
  die Frage beantworten, statt sie zu verhandeln.

Diese vier Punkte sind Zusammenhang, keine Empfehlung. Die Entscheidung gehört
dem Owner.

## Zwei Nebenbefunde

**onnxruntime schreibt beim Start eine Telemetriezeile nach stderr:** `Failed to
persist telemetry device ID; using an in-memory identifier`. Sie erscheint in
jedem der fünfzehn Läufe, auch mit `--network none`. Es ist ein
fehlgeschlagener Schreibversuch auf eine Kennung im Dateisystem, kein
Netzwerkverkehr, und das Scheitern ist der Normalfall in einem Container mit
schreibgeschützten Pfaden. Für den Privacy-Block des Store-Textes (D-12) ist es
trotzdem eine Zeile, die jemand liest und falsch versteht; sie gehört in den
Offline-Test aus Plan 06-10, damit dort belegt ist, dass nichts nach draußen
geht.

**Die Quantisierung ist reproduzierbar.** Zwei Läufe von `quantize_model.py` auf
verschiedenen Maschinen und zu verschiedenen Zeitpunkten, einmal im Docker-Bau
von Plan 06-01 und einmal auf der Entwicklungsmaschine für diesen Bericht,
liefern dieselbe sha256. Das ist keine Selbstverständlichkeit und es ist die
Voraussetzung dafür, dass diese Zahlen etwas über das ausgelieferte Abbild
aussagen.

## Nachvollziehen

```bash
# das fp32-Original holen und die Prüfsumme prüfen
curl -fsSL -o fp32/model.onnx \
  "https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/model.onnx"
echo "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665  fp32/model.onnx" | sha256sum -c -

# die int8-Fassung daneben legen
cd backend && uv run --group quantize python ../scripts/dev/quantize_model.py \
  --input ../fp32/model.onnx --output ../int8/model.onnx

# einen der fünfzehn Läufe, siehe die Kommandozeile oben
```

Vor dem Holen wurde die Ratengrenze geprüft: die HuggingFace-Auslieferung setzt
für diesen Abruf keine `x-ratelimit`-Kopfzeilen und keine `retry-after`, und es
ist ein einzelner Abruf einer festgenagelten Revision. Die AWS-Box wurde für
diesen Bericht nicht angefasst.

## Nachtrag vom 05.09.2026: Französisch auf 120 Fällen

Der Abschnitt oben endete mit einem Befund und einer Owner-Entscheidung. Der
Owner hat am 05.09.2026 den billigsten der dort genannten Wege gewählt, und
zwar den, den dieser Bericht selbst vorgeschlagen hatte: erst das Testset
verbreitern, dann entscheiden. Das französische Testset ist von 42 auf 120
Fälle gewachsen (`fr-43` bis `fr-120`, die ersten 42 unverändert), und die
französischen Läufe sind wiederholt worden.

**Nichts an den Zahlen oben ist angefasst worden.** Sie gelten weiter für 42
Fälle. Was hier dazukommt, gilt für 120.

### Was gleich geblieben ist, und was das wert ist

| Angabe | Wert |
|---|---|
| Abbild | `findling-sem-probe:local` |
| Abbildkennung | `sha256:c9bb41d65746c584480ad05569445a2c36c6f347543f983d42416cedb02bfef9`, dieselbe wie oben |
| int8-Datei im Abbild | `8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6`, dieselbe wie oben |
| fp32-Datei | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665`, erneut geholt, Prüfsumme geprüft |
| lokal erzeugte int8-Datei | wieder `8da4c9ba0a...`, also zum dritten Mal byteidentisch |
| Maschine, Netzwerk, Kommandozeile | unverändert, `--network none`, nur `--dataset` zeigt auf die gewachsene Datei |
| Läufe | fünf, alle französisch: vier für die Quantisierung, einer für den Präfixvergleich |
| Rohdaten | `nachtrag-fr-laeufe.txt` in diesem Verzeichnis, die fünf Ausgaben wörtlich, `--per-case` eingeschlossen |

`quantize_dynamic` hat damit über drei Läufe auf zwei Maschinen dieselbe Datei
erzeugt. Gemessen wurde erneut das ausgelieferte Artefakt.

### Die Zahlen, Französisch, 120 Fälle

Alle mit Präfixen an. Die Klammer nennt die relative Änderung gegenüber der
Bezugszeile fp32-Modell mit fp32-Vektoren, in Prozent.

| Modell | Vektoren | Recall@1 | Recall@5 | MRR |
|---|---|---|---|---|
| fp32 | fp32 | 0,1667 (Bezug) | 0,3833 (Bezug) | 0,2870 (Bezug) |
| fp32 | int8 | 0,1833 (+9,96) | 0,3917 (+2,19) | 0,2908 (+1,32) |
| int8 | fp32 | 0,1583 (-5,04) | 0,3667 (-4,33) | **0,2673 (-6,87)** |
| int8 | int8 | 0,1833 (+9,96) | 0,3750 (-2,17) | 0,2767 (-3,59) |

**Die absoluten Werte sind mit denen der 42er-Tabelle nicht vergleichbar, und
zwar nicht ein bisschen, sondern grundsätzlich.** Die Passagenmenge ist die
Ablenkermenge: jede Anfrage kämpfte vorher gegen 41 Mitbewerber und kämpft
jetzt gegen 119. Dass MRR von 0,4926 auf 0,2870 fällt, ist deshalb kein
Qualitätsverlust, sondern eine schwerere Aufgabe. Vergleichbar sind
ausschließlich zwei Läufe über dieselbe Datei, und genau das sind die vier
Zeilen dieser Tabelle untereinander.

### Paarweise, und der Grund, warum hier zwei Prüfungen stehen

Fall gegen Fall über den Kehrwert des Ranges, wie oben. Neu ist die letzte
Spalte, und sie ist der eigentliche Ertrag dieses Nachtrags.

| Vergleich | MRR-Änderung | mittlere Differenz je Fall | Standardfehler | t | bewegt | schlechter / besser | Vorzeichentest p |
|---|---|---|---|---|---|---|---|
| Modell int8 gegen fp32, fp32-Vektoren | -6,87 Prozent | -0,0197 | 0,0165 | -1,19 | 97 von 120 | 64 / 33 | **0,0022** |
| Modell int8 gegen fp32, int8-Vektoren | -4,86 Prozent | -0,0141 | 0,0174 | -0,81 | 94 von 120 | 59 / 35 | 0,0172 |
| Vektoren int8 gegen fp32, fp32-Modell | +1,32 Prozent | +0,0038 | 0,0069 | +0,55 | 72 von 120 | 37 / 35 | 0,9063 |
| Vektoren int8 gegen fp32, int8-Modell | +3,52 Prozent | +0,0094 | 0,0096 | +0,98 | 79 von 120 | 42 / 37 | 0,6530 |
| Präfixe aus gegen an, int8-Modell | -3,72 Prozent | -0,0100 | 0,0233 | -0,43 | 104 von 120 | 43 / 61 | 0,0950 |

Die Bezugszeile der zweiten Zeile ist fp32-Modell mit int8-Vektoren, nicht die
Bezugszeile der Haupttabelle; deshalb steht dort -4,86 und in der Haupttabelle
-3,59. Beide Zahlen beschreiben dieselben zwei Läufe, gemessen gegen zwei
verschiedene Bezugspunkte.

**Warum ein zweiter Test dazugekommen ist.** Der t-Wert der ersten Zeile ist von
-2,03 auf -1,19 gefallen, und das sieht auf den ersten Blick nach Entwarnung
aus. Es ist keine. Die Differenz zweier Kehrwerte wird von wenigen Fällen
beherrscht, die zwischen Rang 1 und Rang 2 wechseln: ein einziger solcher Fall
trägt 0,5 bei, während ein Sprung von Rang 60 auf Rang 90 nur 0,006 beiträgt.
Bei 119 Ablenkern liegen fast alle Ränge im hinteren Bereich, die Differenzen
werden klein, ihre Streuung bleibt von den wenigen Vorderplätzen bestimmt, und
der t-Wert verliert Trennschärfe. Der Vorzeichentest über die bewegten Fälle
benutzt nur die Richtung und ist gegen diese Schieflage unempfindlich.

Er sagt das Gegenteil einer Entwarnung: **von 97 bewegten Fällen rutschen 64
nach hinten und nur 33 nach vorn, zweiseitig p = 0,0022.** Auf 42 Fällen war
dasselbe Verhältnis 16 zu 9 und damit p = 0,23, also nichts. Die Verbreiterung
hat die Richtung des Befundes nicht entkräftet, sondern zum ersten Mal
belastbar gemacht.

### Der Vergleich beider Messungen in einer Zeile

| Fallzahl | MRR fp32 | MRR int8 | relativ | mittlere Differenz | Standardfehler | t | bewegt | schlechter / besser | Vorzeichentest p |
|---|---|---|---|---|---|---|---|---|---|
| 42 | 0,4926 | 0,4471 | -9,24 Prozent | -0,0455 | 0,0224 | -2,03 | 25 von 42 | 16 / 9 | 0,2295 |
| 120 | 0,2870 | 0,2673 | -6,87 Prozent | -0,0197 | 0,0165 | -1,19 | 97 von 120 | 64 / 33 | 0,0022 |

Zwei Dinge stehen hier, die auseinandergehalten gehören. Der Punktschätzer ist
milder geworden, von -9,24 auf -6,87 Prozent. Die Richtung ist sicherer
geworden. Beides zugleich ist der Normalfall, wenn eine kleine Stichprobe einen
echten, aber kleineren Effekt zufällig überzeichnet hat.

**Eine Vorhersage dieses Berichts hat sich nicht bewahrheitet, und das gehört
hierher.** Oben steht, 120 statt 42 Fälle würden den Standardfehler etwa
halbieren. Er ist von 0,0224 auf 0,0165 gefallen, also um gut ein Viertel statt
um die Hälfte. Die Rechnung unterstellte gleiche Streuung je Fall; tatsächlich
hat die Verbreiterung zugleich die Aufgabe verändert, weil sie die Ablenkermenge
verdreifacht hat. Eine Prognose über eine Stichprobengröße, die nebenbei die
Messgröße mitverändert, war zu einfach gerechnet.

### Das Verdikt zu D-02 für Französisch bei n = 120

> **Nachtrag 05.09.2026, Owner-Entscheid.** Der Abschnitt unter dieser Zeile
> bleibt unverändert stehen. Der Owner hat den Messpunkt der Abbruchregel
> inzwischen auf die ausgelieferte Kombination gelegt (Weg 4 unten); **D-02 gilt
> damit als bestanden.** Die Begründung steht am Ende dieser Datei unter
> [Der Owner-Entscheid vom 05.09.2026](#der-owner-entscheid-vom-05092026-der-messpunkt-der-abbruchregel).

**Die selbst quantisierte int8-Fassung trägt auf Französisch nicht.** MRR fällt
gegenüber fp32 um 6,87 Prozent relativ, die Abbruchregel dieses Plans liegt bei
5 Prozent. Die Grenze ist zum zweiten Mal gerissen, jetzt auf dem dreifachen
Testset, und die Richtung des Rückgangs ist mit p = 0,0022 nicht mehr mit Zufall
zu erklären. Für Deutsch und Englisch bleibt es bei den Verdikten oben; sie sind
nicht neu gemessen worden, weil sie die Grenze nicht gerissen hatten.

Die Entscheidung gehört weiterhin dem Owner. Was diese Messung den drei Wegen
aus dem Abschnitt "Der Befund" hinzufügt:

1. **Eine andere Quantisierungsachse.** Der Befund ist jetzt belastbar genug,
   dass sich der Aufwand lohnen könnte. Was er weiterhin nicht sagt: wo im
   Modell der Verlust entsteht. Die Einbettungstabelle mit ihren 81,7 Prozent
   aller Parameter bleibt der erste Verdächtige, und sie auszunehmen bleibt der
   erste Versuch. Preis unverändert: eine größere Datei gegen das Größengatter
   aus Plan 06-01, und je Variante wieder ein voller Satz Läufe.
2. **Die fp32-Datei ins Abbild.** Preis unverändert: 470 MB statt 118 MB, das
   Abbild bei rund 1,09 GB statt 740 MB, auf einer 4-GB-Box. Was diese Messung
   dazu beiträgt: der Gegenwert ist kleiner als bisher angenommen, nämlich 6,87
   statt 9,24 Prozent MRR auf einer Sprache, und für Deutsch und Englisch kauft
   die Datei nach der Messung oben nichts.
3. **Eine kleinere Zusage im Store-Text.** Unverändert die einzige der drei
   Möglichkeiten ohne neue Unbekannte, und unverändert im Widerspruch zu D-03.

Und ein vierter Punkt, den es vorher nicht gab, weil er ohne belastbare Richtung
keinen Sinn ergab:

4. **Die ausgelieferte Kombination getrennt betrachten.** Was Nutzer bekommen,
   ist int8-Modell mit int8-Vektoren, und diese Zeile steht bei -3,59 Prozent
   gegenüber fp32/fp32, also unter der Grenze. Ihre Richtung ist mit p = 0,0172
   ebenfalls belastbar, ihr Betrag aber nicht mehr. Die Abbruchregel des Plans
   ist ausdrücklich auf die Modellfassung bei fp32-Vektoren geschrieben und
   dort gerissen. Ob die Regel den richtigen Punkt misst, ist selbst eine
   Owner-Frage und wird hier nicht beantwortet.

### Zwei Nebenergebnisse der Nachmessung

**D-05 ist auf breiterer Grundlage bestätigt.** Mit und ohne Präfixe bekommen
104 von 120 französischen Fällen einen anderen Rang. Der Alarmfall des Plans,
gar kein Unterschied, liegt weiterhin nicht vor, und zwar deutlicher als vorher.

**Die Beobachtung "die Präfixe helfen außerhalb des Deutschen nicht" hält
nicht.** Auf 42 Fällen lag die Fassung ohne Präfixe auf Französisch mit +6,46
Prozent MRR vorn. Auf 120 Fällen liegt sie mit -3,72 Prozent hinten. Das
Vorzeichen hat sich umgedreht, |t| liegt in beiden Messungen unter 0,7, und der
Vorzeichentest kommt auf p = 0,095. Damit ist belegt, was der Bericht oben
vermutet hat: diese Beobachtung war Rauschen. Für Plan 06-05 heißt das, dass sie
als Beobachtung ersatzlos entfällt, während die Anweisung, die Präfixe zu
setzen, unverändert gilt.

**Die Entlastung der Vektorquantisierung hält.** Beide französischen Vergleiche
liegen bei p = 0,91 und p = 0,65, die Vorzeichen bleiben uneinheitlich, kein
t-Wert erreicht 1. Für Plan 06-04 ändert sich nichts: int8 in vec0 kostet auch
auf 120 Fällen nichts Messbares.

### Nachvollziehen

```bash
# fp32-Original holen wie oben, int8-Fassung daneben legen wie oben, dann
# fuenfmal derselbe Aufruf, nur --model, --prefixes und --vector-dtype wechseln:
docker run --rm --network none \
  -v "$PWD/scripts/dev/model_quality.py:/tmp/model_quality.py:ro" \
  -v "$PWD/testdata/semantik:/tmp/semantik:ro" \
  -v "$FP32_DIR/model.onnx:/model/fp32/model.onnx:ro" \
  -v "$INT8_DIR/model.onnx:/model/int8/model.onnx:ro" \
  --entrypoint /app/.venv/bin/python \
  findling-sem-probe:local /tmp/model_quality.py \
  --model /model/int8/model.onnx \
  --tokenizer /usr/local/share/findling/model \
  --dataset /tmp/semantik/fr.jsonl \
  --prefixes on --vector-dtype fp32 --per-case
```

Unter Git Bash weiterhin `MSYS_NO_PATHCONV=1` davor. Die fünf Ausgaben liegen
wörtlich in `nachtrag-fr-laeufe.txt`; die Tabellen dieses Nachtrags sind daraus
gerechnet und nicht abgeschrieben. Der Vorzeichentest ist die zweiseitige
Binomialwahrscheinlichkeit über die bewegten Fälle, Gleichstände ausgeschlossen.

Vor dem erneuten Holen der fp32-Datei wurde die Ratengrenze wieder geprüft: die
HuggingFace-Auslieferung setzt für diesen Abruf weiterhin keine
`x-ratelimit`-Kopfzeilen und kein `retry-after`, `content-length` stimmt mit der
ersten Messung überein, und es ist ein einzelner Abruf einer festgenagelten
Revision. Die AWS-Box wurde auch für diesen Nachtrag nicht angefasst.

## Der Owner-Entscheid vom 05.09.2026: der Messpunkt der Abbruchregel

**Entscheid (Owner, 05.09.2026): Die Abbruchregel von Plan 06-03 wird auf die
ausgelieferte Kombination bezogen, also int8-Modell mit int8-Vektoren. Diese
Kombination steht auf Französisch bei -3,59 Prozent MRR und damit unter der
5-Prozent-Grenze. D-02 gilt damit als BESTANDEN.** Begründung in einem Satz: die
Regel soll die Qualität dessen absichern, was Nutzer bekommen, und das ist die
Kombination beider Quantisierungsstufen und nicht die Modellfassung bei
fp32-Vektoren, die in keinem Abbild ausgeliefert wird.

**Das ist eine dokumentationspflichtige Umdeutung des Messpunktes und keine
stille Regeländerung.** Verschoben hat sich der Messpunkt, von der isolierten
Modellfassung auf die ausgelieferte Kombination; die Grenze von 5 Prozent
relativem MRR-Rückgang steht unverändert. Weg 4 des Abschnitts oben hatte genau
diese Möglichkeit benannt und ausdrücklich offen gelassen, ob die Regel den
richtigen Punkt misst. Diese Frage ist hiermit beantwortet, und zwar vom Owner
und nicht vom Bericht.

**Was der Entscheid nicht wegräumt, und was deshalb hier stehen bleibt.** Die
Richtung des Rückgangs ist auch für die ausgelieferte Kombination belastbar
(p = 0,0172); nicht belastbar ist ihr Betrag. Die Zahl -6,87 Prozent für die
Modellfassung bei fp32-Vektoren bleibt gemessen und bleibt in den Tabellen oben
stehen. Der Entscheid sagt, welche der beiden Zahlen die Regel prüft, nicht dass
die andere falsch wäre.

**Die Folgen, aufgezählt statt angedeutet:**

- **Kein Umbau.** Die Wege 1 bis 3 aus dem Abschnitt "Der Befund" werden nicht
  gegangen: keine andere Quantisierungsachse, keine fp32-Datei im Abbild, keine
  kleinere Zusage im Store-Text. Das Abbild bleibt bei 118 MB Modelldatei und
  rund 740 MB gesamt.
- **Die Store-Text-Zusage bleibt, wie D-03 und D-17 sie festhalten.** Deutsch,
  Englisch und Französisch werden weiter gleichrangig zugesagt.
- **Für Plan 06-04 und 06-05 ändert sich nichts.** int8 in vec0 bleibt gesetzt,
  die E5-Präfixe bleiben an.
- **Der Blocker ist damit aufgeloest.** Die offene Owner-Entscheidung, die seit
  dem Erstlauf in .planning/STATE.md stand, ist getroffen und dort ausgetragen.
