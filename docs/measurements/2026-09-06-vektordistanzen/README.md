# Vektordistanzen: wie weit relevante und unbeteiligte Paare auseinanderliegen

Zwei Messungen von `scripts/dev/vector_distances.py` auf der int8-L2-Skala, auf
der der Vektorbestand wirklich ordnet. Sie beantworten die Frage, die eine
Schwelle beantwortet haben muss, bevor sie existieren darf: wie weit legt dieses
Modell eine Anfrage von dem Abschnitt weg, den sie meint, und wie weit von einem
Abschnitt, mit dem sie nichts zu tun hat.

Anlass ist CI-Lauf 34031891300 auf `main`. Im Schritt "The seven German language
cases" liefert die Anfrage `Genehmigung` fuenf Eintraege statt einem: der erste
ist richtig, die vier anderen enthalten das Wort nirgends. Ursache ist, dass
`_semantic_documents` in `index/search.py` bis zu `window` kNN-Nachbarn ohne jede
Distanzgrenze in die Verschmelzung reicht, und eine kNN-Abfrage antwortet immer
mit k Nachbarn.

## Die zwei Verdikte, zuerst

**Erstens: die abgeleitete Schwelle ist eine Obergrenze von 86,5 und ein Band von
14,0.** Beide Zahlen stehen unten mit ihrer Ableitung. Sie sind die schaerfsten
Werte auf dem Raster, unter denen die Trefferquote des dreisprachigen Testsets in
keiner Sprache faellt, und sie nehmen der Verschmelzung trotzdem 17,3 Prozent
(Deutsch), 30,8 Prozent (Englisch) und 11,1 Prozent (Franzoesisch) aller
Ablenker ab, ohne ein einziges relevantes Paar zu verlieren.

**Zweitens, und das ist der Befund dieses Berichts: die zweite Nebenbedingung ist
nicht erfuellbar, und der Riegel allein repariert die sieben deutschen
Sprachfaelle nicht.** Damit die einwoertigen Probeanfragen auf dem e2e-Korpus
gar keinen Kandidaten erzeugen, muesste die Obergrenze unter 68,4544 liegen.
Damit die Paraphrase weiterhin `10-kuendigung.docx` findet, muesste sie ueber
79,5487 liegen. Beides zugleich ist unmoeglich, und zwar nicht knapp. **Die
zulaessige Menge der Nebenbedingung (B) ist leer.** Der Abschnitt "Der Befund"
unten nennt die Zahlen, an denen es scheitert, und die Wege, die dem Owner
offenstehen.

Was daraus folgt, steht ohne Beschoenigung hier: die Schwelle wird nicht
aufgeweicht, bis ein Job gruen wird. Die Zahlen dieses Berichts sind die Zahlen,
die (A) erfuellen. Der Riegel schliesst das ferne Feld, die Operatorregel aus
Task 3 desselben Plans nimmt die Faelle 5, 6 und 7 (Phrase, Minus, Dateityp) von
der Vektorseite ganz weg, und die Faelle 1 bis 4 brauchen eine Entscheidung, die
groesser ist als eine Zahl.

## Die Umgebung dieser Messung

| Angabe | Wert |
| --- | --- |
| Datum | 06.09.2026 |
| Modellverzeichnis | aus dem Abbild `findling-sem-probe:local` mit `docker create` und `docker cp` nach aussen kopiert, wie es `.github/workflows/integration.yml` Z. 1040 bis 1056 fuer den Laeufer tut |
| Modelldatei | `model.onnx`, 118.101.091 Byte, sha256 `8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6` |
| Pruefung der Modelldatei | identisch mit `MODEL_SHA256` in `.github/workflows/integration.yml` Z. 1039, also genau die Datei, gegen die der e2e-Lauf misst |
| Tokenizer | `tokenizer.json` aus demselben Verzeichnis |
| Python | 3.13.13 |
| onnxruntime | 1.29.0 |
| numpy | 2.5.2 |
| Plattform | Windows 11, x86_64 |
| Netzwerk | abgeklemmt: das Werkzeug oeffnet keine Verbindung, das Modell kommt aus einem lokalen Verzeichnis, der Korpus aus `scripts/dev/build_corpus.py` |
| Metrik | `vec_distance_l2` ueber eine `int8[384]`-Spalte, gegen `nearest()` eines echten `VectorStore` geprueft (`--selftest`) |

Die Skala der Metrik folgt aus `embed/model.py::to_int8`, das einen normierten
Vektor mit 127 skaliert: 0 bei identisch, 127 mal Wurzel 2 gleich 179,6051 bei
orthogonal, 254 im Gegensatz. Der Selbsttest belegt genau diese drei Werte gegen
den Bestand.

## Die Kommandozeilen, woertlich

```
cd backend
uv run python ../scripts/dev/vector_distances.py --selftest
uv run python ../scripts/dev/vector_distances.py --testset \
    --model-dir <modellverzeichnis> --dataset-dir ../testdata/semantik
uv run python ../scripts/dev/vector_distances.py --corpus \
    --model-dir <modellverzeichnis>
uv run python ../scripts/dev/vector_distances.py --derive \
    --model-dir <modellverzeichnis> --dataset-dir ../testdata/semantik
```

Der Selbsttest antwortet:

```
selftest      the distance of this tool against nearest() of a real store
file 1        store 0.0000  own 0.0000
file 2        store 97.3088  own 97.3088
file 3        store 179.6051  own 179.6051
file 4        store 254.0000  own 254.0000
maximum       254.0000 of the metric maximum 254.0000
verdict       the tool and the store agree to four digits
```

## Tabelle 1: das dreisprachige Testset

204 Faelle aus `testdata/semantik`, 42 auf Deutsch, 42 auf Englisch, 120 auf
Franzoesisch. Je Anfrage die Distanz zu ihrem eigenen Abschnitt (das relevante
Paar) und die Distanzen zu allen uebrigen Abschnitten derselben Datei (die
Ablenker, 41 auf Deutsch und Englisch, 119 auf Franzoesisch).

| Grundgesamtheit | n | min | p05 | Median | p95 | max |
| --- | --- | --- | --- | --- | --- | --- |
| de relevant | 42 | 66,9403 | 69,4416 | 74,4815 | 79,5396 | 86,3597 |
| de Ablenker | 1722 | 67,6240 | 74,4312 | 81,3419 | 89,2793 | 96,2497 |
| en relevant | 42 | 68,8694 | 71,6176 | 76,7723 | 84,1058 | 84,3623 |
| en Ablenker | 1722 | 68,1322 | 75,9352 | 83,4656 | 92,0595 | 97,6217 |
| fr relevant | 120 | 67,2756 | 69,9342 | 76,4428 | 82,1249 | 84,2674 |
| fr Ablenker | 14280 | 63,7574 | 74,6991 | 81,0062 | 87,2238 | 94,6361 |

Die Ueberlappung, also wie viele Ablenker naeher liegen als das richtige Paar
ihres eigenen Falls: 124 von 1722 auf Deutsch, 181 von 1722 auf Englisch, 2289
von 14280 auf Franzoesisch.

**Die wichtigste Zahl dieser Tabelle ist nicht der Median, sondern die
Ueberlappung der beiden Verteilungen.** Das relevante Paar reicht auf Deutsch bis
86,3597, der naechste Ablenker beginnt bei 63,7574. Die zwei Verteilungen liegen
also nicht nebeneinander, sondern ineinander. Eine absolute Obergrenze kann
deshalb nur das ferne Feld abschneiden und niemals relevant von unbeteiligt
trennen. Das ist eine Eigenschaft dieses Modells auf dieser Metrik und keine
Eigenschaft der gewaehlten Zahl.

## Tabelle 2: die Texte des e2e-Korpus

22 Chunks ueber 22 Dateien, geschnitten mit dem echten Chunker dieses
Repositoriums und eingebettet mit `passage: `. Die zehn naechsten Chunks je
Probeanfrage, aufsteigend. Chunknummer ist ueberall 0, weil jede Korpusdatei
unter dem Tokendeckel genau einen Chunk traegt.

| Probe | Rang 1 | Rang 2 | Rang 3 |
| --- | --- | --- | --- |
| `Genehmigung` | 09-bescheid.pdf 69,3758 | 19-uebermittlung.tif 69,8570 | 18-aushang.png 72,2219 |
| `Frist` | 01-text-layer.pdf 76,6485 | 18-aushang.png 77,4919 | 23-gedreht.jpg 77,9615 |
| `Mueller` | 12-aktenvermerk.txt 71,0070 | 01-text-layer.pdf 74,3976 | 03-document.docx 74,4983 |
| `Vertrag` | 11-uebersicht.odt 68,4544 | 03-document.docx 74,6793 | 19-uebermittlung.tif 75,0866 |
| `bescheid` | 10-kuendigung.docx 72,0000 | 09-bescheid.pdf 72,3948 | 18-aushang.png 75,4586 |
| Paraphrase | 13-ratsvorlage-scan.pdf 78,5048 | 17-beleg.jpg 78,6575 | **10-kuendigung.docx 79,5487** |

Die Paraphrase ist `PARAPHRASE_TERM` aus `.github/workflows/integration.yml`, das
Dokument, das sie finden muss, ist `10-kuendigung.docx`.

**Was diese Tabelle ueber den Fehler sagt.** Die Annahme, mit der der Plan
angetreten ist, naemlich dass eine Anfrage aus einem Wort von jedem Abschnitt
weit weg steht, ist falsch. Die einwoertigen Proben landen bei 68 bis 77, die
Paraphrase erreicht ihr eigenes Dokument erst bei 79,5487. Auf dieser Skala liegt
eine einwoertige Anfrage naeher an einem beliebigen Verwaltungstext als eine
Paraphrase an dem Absatz, den sie umschreibt. Ein absoluter Riegel kann die zwei
Faelle deshalb nicht auseinanderhalten.

## Die Ableitung

Zwei Zahlen, und der Bericht sagt, warum es zwei sein muessen.

**Die Obergrenze** beantwortet den Fall "hier ist nichts Naheliegendes": liegt
kein Chunk unter ihr, erzeugt die Vektorseite gar keinen Kandidaten, und die
Verschmelzung ist die Identitaet auf der lexikalischen Liste.

**Das Band um den besten Nachbarn** beantwortet den Fall "einer ist deutlich der
beste": wer weiter zurueckliegt als das Band, ist Beiwerk, auch wenn er unter der
Obergrenze liegt.

Keine der beiden reicht allein, und das ist an den Tabellen oben nachlesbar. Die
Obergrenze allein laesst auf eine gute Anfrage das ganze Mittelfeld herein: bei
`Vertrag` liegen unter 86,5 achtzehn Dateien, obwohl nur eine gemeint ist. Das
Band allein haelt bei einer Anfrage ohne jeden passenden Treffer den besten
Unbeteiligten fuer den Treffer: bei `Frist` ist der naechste Nachbar
`01-text-layer.pdf`, und ein Band greift immer erst hinter dem besten Eintrag.

### Die zwei Nebenbedingungen

**(A) Kein Rueckgang der Trefferquote auf dem Testset.** Recall@1, Recall@5 und
MRR mit Riegel duerfen gegen die Werte ohne Riegel in keiner der drei Sprachen
fallen. Gemessen wird ueber die drei Kennzahlen und nicht ueber den einzelnen
Fall: der Riegel nimmt auch Ablenker weg, ein Fall, der sein relevantes Paar
verliert, koennte also von einem Fall bezahlt werden, dessen Rang sich
verbessert. Ob er bezahlt wird, ist eine Messung und keine Annahme.

**(B) Auf den Korpustexten ergeben die einwoertigen Probeanfragen null Nachbarn
unter der Obergrenze, und die Paraphrase behaelt `10-kuendigung.docx`.**

### Die vier Zahlen, an denen sich beides entscheidet

| Zahl | Wert | Bedeutung |
| --- | --- | --- |
| (B) obere Schranke der Obergrenze | 68,4544 | der naechste Chunk der einwoertigen Proben (`Vertrag` gegen 11-uebersicht.odt) |
| (B) untere Schranke der Obergrenze | 79,5487 | das gewollte Dokument der Paraphrase (10-kuendigung.docx) |
| (A) weitestes relevantes Paar | 86,3597 | ueber die drei Sprachen, deutsch |
| (A) naechster Ablenker | 63,7574 | ueber die drei Sprachen, franzoesisch |

### Der Befund: (B) ist leer

Die obere Schranke von (B) liegt **elf Einheiten unter** ihrer eigenen unteren
Schranke. Es gibt keine Obergrenze, die beide Haelften von (B) erfuellt, und es
gibt auch keine, die auch nur eine der beiden erfuellt, ohne (A) zu verletzen:
eine Obergrenze unter 68,4544 schneidet jedes relevante Paar des Testsets ab, das
tiefste liegt bei 66,9403 und das fuenfte Perzentil bei 69,4416.

Damit steht (A), und (B) ist ein Befund. Es wird nicht gedreht, bis der Job gruen
ist; eine Schwelle, die so entsteht, ist kein Messwert.

### Die gewaehlten Zahlen

Das Raster laeuft in Schritten von 0,5 von der kleinsten bis zur groessten
gemessenen Distanz, und es wird vom schaerfsten Riegel aufwaerts durchsucht. Weil
(B) leer ist, ist die zulaessige Menge nach oben offen: jedes groessere Paar ist
ein schwaecherer Riegel. Genommen wird deshalb das schaerfste zulaessige Paar,
und der genannte Abstand ist der zur einzigen Grenze, die es gibt, naemlich der
nach unten.

| Zahl | Wert | Abstand zur Grenze |
| --- | --- | --- |
| `VECTOR_MAX_DISTANCE` | **86,5** | 0,5 nach unten, danach faellt MRR |
| `VECTOR_DISTANCE_BAND` | **14,0** | 0,5 nach unten, danach faellt Recall@5 |

### Was das Paar auf dem Testset wirklich tut

| Sprache | Faelle | R@1 ohne | R@1 mit | R@5 ohne | R@5 mit | MRR ohne | MRR mit | Ablenker entfernt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| de | 42 | 0,5000 | 0,5000 | 0,8333 | 0,8333 | 0,6268 | 0,6268 | 17,31 % |
| en | 42 | 0,3333 | 0,3333 | 0,7143 | 0,7143 | 0,5101 | 0,5101 | 30,78 % |
| fr | 120 | 0,1583 | 0,1583 | 0,3750 | 0,3750 | 0,2655 | 0,2655 | 11,09 % |

Keine der neun Kennzahlen bewegt sich, und trotzdem verlaesst zwischen einem
Neuntel und knapp einem Drittel der Ablenker die Kandidatenliste. Das ist der
Nutzen, den dieses Paar hat, und es ist genau der Nutzen, den man auf einer
kleinen Instanz nicht sieht.

### Was das Paar auf dem e2e-Korpus tut

| Probe | Kandidaten unter dem Riegel |
| --- | --- |
| `Genehmigung` | 22 von 22 |
| `Frist` | 20 von 22 |
| `Mueller` | 15 von 22 |
| `Vertrag` | 18 von 22 |
| `bescheid` | 19 von 22 |
| Paraphrase | 18 von 22, `10-kuendigung.docx` darunter |

Auf 22 Chunks in einem Abstandsband von 68 bis 84 greift ein Riegel, der bei 86,5
schliesst, kaum. Das ist keine Fehlkonstruktion des Riegels, sondern die Aussage
der Messung: der e2e-Korpus ist zu klein und zu gleichfoermig, als dass eine
absolute Distanz auf ihm etwas trennen koennte.

## Der OCR-Vorbehalt

**Die Texte der Bilddateien in Tabelle 2 sind die beabsichtigten Texte des
Generators `scripts/dev/build_corpus.py`, nicht die Ausgabe von tesseract.**
Diesem Weg fehlt also das OCR-Rauschen, das im e2e-Lauf zwischen dem Pixel und
dem Vektor liegt. Betroffen sind `13-ratsvorlage-scan.pdf`,
`14-pacht-mit-anhang.pdf`, `15-schweiz-baubewilligung.pdf`,
`16-oesterreich-mitteilung.pdf`, `17-beleg.jpg`, `18-aushang.png`,
`19-uebermittlung.tif`, `20-rueckruf.webp`, `21-sendebericht.tif`,
`23-gedreht.jpg` und `30-nur-ein-bild.pdf`, also elf der 22 Dateien der Tabelle.

Rauschen entfernt sich vom sauberen Text, die gemessenen Distanzen dieser elf
Dateien sind im e2e-Lauf also eher groesser als hier. Fuer den Befund oben
aendert das nichts: die zwei Schranken, an denen (B) scheitert, haengen an
`11-uebersicht.odt` (68,4544, keine Bilddatei, kein OCR) und an
`10-kuendigung.docx` (79,5487, ebenfalls kein OCR). **Dieser Bericht entscheidet
die Schwelle, der e2e-Lauf beweist sie.**

## Die Wege, die offen sind, und die Entscheidung des Owners

Der Befund wird nicht durch eine Zahl geloest. Was zur Wahl steht:

1. **Die Operatorregel weiterdrehen und einwoertige Anfragen rein lexikalisch
   beantworten.** Sie loest die Faelle 1 bis 4 und den `bescheid`-Kontrollfall
   vollstaendig, kostet aber die Semantik fuer jede kurze Anfrage. Der Plan
   entscheidet ausdruecklich gegen diese Ausweitung ("Eine mehrwortige Anfrage
   ohne Operator bleibt hybrid"), und eine Ausweitung auf ein Wort waere eine
   neue Entscheidung und keine Ableitung.
2. **Ein relativer Riegel statt eines absoluten**, also nicht "wie weit ist der
   Nachbar", sondern "wie viel besser ist der beste als das Mittelfeld dieser
   Anfrage". Das Band ist die halbe Antwort darauf; die andere Haelfte waere eine
   Normierung auf die Verteilung der Antwort selbst. Das ist ein Entwurf und
   keine Stellschraube.
3. **Die sieben Faelle auf einem Korpus messen, der gross genug ist, dass eine
   Distanz etwas trennt.** Auf 22 Dokumenten ist jede Datei die Nachbarin jeder
   Anfrage; das ist die eigentliche Aussage von Tabelle 2.
4. **Die Erwartung der sieben Faelle als "genau eine Datei" aufgeben.** Davon
   raet dieser Bericht ab: die Faelle sind die Produktzusage und nicht der
   Messwert, und sie abzuschwaechen waere Fallstrick 3 dieser Phase an einer
   Zusicherung statt an einer Zahl.

Die Entscheidung gehoert dem Owner. Bis dahin steht im Behaelter der Riegel, der
(A) erfuellt, und die Operatorregel, die die Faelle 5, 6 und 7 rein lexikalisch
beantwortet.

## Was dieser Bericht nicht enthaelt

Keine Anfrage und keinen Abschnitt des Testsets, in keiner der drei Sprachen; nur
Kennungen, Dateinamen und Zahlen. Dasselbe gilt fuer das Werkzeug: ein Fall in
`backend/tests/test_vector_distances.py` prueft, dass weder das Skript noch seine
Ausgabe ein `query`- oder ein `passage`-Feld traegt (T-06.1-86, Muster T-06-11).
