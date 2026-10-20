# Ähnlich-Distanzen: wie weit Dokument und Dokument auseinanderliegen (Plan 35-04)

Stand: 2026-10-19. Diese Messung liefert die Obergrenze `SIMILAR_CEILING` der
Ähnlich-Ansicht (STR-01), bevor die Route in Plan 35-05 entsteht. Die Schwelle
der Suche (`VECTOR_MAX_DISTANCE` 86,5 und Band 14,0 aus
`docs/measurements/2026-09-06-vektordistanzen/`) gilt für Anfrage gegen
Abschnitt mit den E5-Präfixen `query: ` und `passage: `. Die Ähnlich-Ansicht
vergleicht Abschnitt gegen Abschnitt, beide als `passage: ` eingebettet, und
das ist eine andere Verteilung. Ohne eigene Obergrenze füllt ein kleiner
Bestand die Liste mit Unbeteiligtem (Pitfall 3 der Phasen-Recherche, Annahmen
A1 und A7).

**Nachtrag 19.10.2026:** Nach dem Owner-Entscheid für Weg 2 (Abschnitt 7)
liefert die Nachmessung mit Fassungspaaren `SIMILAR_CEILING` 54,5
(Abschnitt 10). Die Verdikte unten gelten für den ersten Lauf und bleiben als
Beleg stehen.

## Die Verdikte, zuerst

**Erstens: Regel nicht erfüllbar. `SIMILAR_CEILING` bekommt keinen Wert.**
Regel (1) ergibt den Rasterwert 84,0: dort liegen in allen drei Sprachen
mindestens 95 Prozent der verwandten Paare (Deutsch 1,0000, Englisch 1,0000,
Französisch 1,0000; Englisch erreicht 95 Prozent erst bei 84,0). Regel (2)
verlangt bei diesem Wert mindestens 90 Prozent abgeschnittene unbeteiligte
Paare und bekommt Deutsch 0,58 Prozent, Englisch 14,40 Prozent, Französisch
0,08 Prozent. Der Abstand ist nicht knapp: fast jedes unbeteiligte Paar läge
unter der Obergrenze. Rasterzeile:

```
   value   rel de   rel en   rel fr     cut de   cut en   cut fr
    84.0   1.0000   1.0000   1.0000     0.0058   0.1440   0.0008
```

Die Gegenzahl der Owner-Frage: der größte Rasterwert, der in jeder Sprache
90 Prozent der unbeteiligten Paare abschneidet, ist 61,5. Er verlöre
Deutsch 42 von 42, Englisch 42 von 42 und Französisch 119 von 120 verwandten
Paaren, also praktisch alle.

**Zweitens: Annahme A1 ist auf dem Korpus nicht prüfbar.** Der e2e-Korpus
ergibt 26 Chunks über 26 Dateien mit Text, keine Datei trägt mehr als einen
Chunk. Für ein einchunkiges Dokument ist der Mittelwert der Vektor selbst,
Mittelwert und Minimum sind dort identisch. Die Überschneidung Mittelwert
gegen Minimum ist deshalb keine Zahl dieses Laufs; nach Regel (3) wird A1
nicht ersatzweise auf Testset-Passagen geprüft.

**Drittens: die Gruppenprobe (4) verfehlt die Fremdgrenze, und zwar auf dem
ganzen Raster.** Bei 84,0 liegen 100 Prozent der 38 Gruppenpaare unter der
Obergrenze (gefordert mindestens 80 Prozent), aber auch 95,47 Prozent der 287
Fremdpaare (erlaubt höchstens 10 Prozent). Keine Obergrenze erfüllt beide
Grenzen zugleich: 80 Prozent der Gruppenpaare werden erst bei 71,0 erreicht
(0,8421), höchstens 10 Prozent der Fremdpaare gelten nur bis 65,0 (0,0836).

Damit gilt der Halt aus Regel (2) und (4): kein stiller Wert, kein Rückfall
auf die Suchschwelle 86,5 (dort lägen Deutsch 100 Prozent, Englisch 92,2
Prozent und Französisch 99,96 Prozent der unbeteiligten Paare darunter).
Plan 35-05 startet nicht ohne Owner-Wort. Die Owner-Frage steht in Abschnitt 7.

## 1. Entscheidungsregel (vor der Messung festgelegt)

Diese Regel und die Gruppentabelle `gruppen.tsv` stehen in einem eigenen
Commit vor dem Werkzeug und vor jeder Rohdatei. Der Wert wird mechanisch aus
dem Raster abgeleitet, nicht nach Sicht der Zahlen gewählt.

**(1) Verwandte Paare.** `SIMILAR_CEILING` ist der kleinste Rasterwert
(Schritt 0,5 auf der int8-L2-Skala, 0 bis 254), unter dem (Distanz kleiner
oder gleich dem Wert, wie in `near_enough`) in jeder der drei Sprachen
mindestens 95 Prozent der verwandten Paare liegen.

**(2) Unbeteiligte Paare.** Der Wert aus (1) gilt nur, wenn er in jeder
Sprache mindestens 90 Prozent der unbeteiligten Paare abschneidet (Distanz
größer als der Wert). Schafft er das in einer Sprache nicht, wird kein Wert
gewählt. Stattdessen nennt der Bericht beide Zahlen als Owner-Frage: welcher
Rasterwert in jeder Sprache 90 Prozent abschnitte und wie viele verwandte
Paare er je Sprache verlöre. Ein stiller Rückfall auf die Suchschwelle oder
auf eine ungeprüfte Zahl (Annahme A7) ist ausgeschlossen.

**Herleitung der 90 Prozent.** Die Liste zeigt höchstens 10 Nachbarn
(D-35-03), und in einem Nutzerbestand ist fast jedes Dokumentpaar
unbeteiligt. Lässt die Obergrenze den Anteil q der unbeteiligten Paare durch,
füllt ein Bestand mit N unbeteiligten Dokumenten die Liste im Mittel mit q mal
N Unbeteiligten. Bezugsbestand sind 50 unbeteiligte Dokumente: ein kleiner
Selfhoster-Ordner, in der Größenordnung des e2e-Korpus (39 Dateien). Höchstens
die halbe Liste, also 5 Einträge, darf im Mittel Unbeteiligtes sein. Aus q mal
50 höchstens 5 folgt q höchstens 0,10, also mindestens 90 Prozent
abgeschnitten.

Anfrage und Abschnitt lagen im September-Bericht in ineinanderliegenden
Verteilungen (der nächste Ablenker ab 63,7574, das weiteste relevante Paar bis
86,3597). Es ist daher möglich, dass (1) und (2) zugleich unerfüllbar sind.
Das ist ein zulässiger Ausgang dieser Messung, kein stiller: dann steht
"Regel nicht erfüllbar" mit den Zahlen im Bericht, und Plan 35-05 startet
nicht ohne Owner-Wort.

**(3) Mittelwert gegen Minimum (Annahme A1).** Die Ähnlich-Ansicht fragt mit
dem Mittelwert der gespeicherten Abschnittsvektoren eines Dokuments
(`findling.index.fusion.centroid`), ein Scan statt einem je Abschnitt. Der
Mittelwert-Vektor wird verwendet, wenn auf den mehrchunkigen Dokumenten des
e2e-Korpus (`scripts/dev/build_corpus.py`) die Überschneidung der ersten zehn
Nachbarn (Mittelwert gegen einen Scan je Abschnitt mit Minimum je Dokument)
im Mittel mindestens 0,8 beträgt. Sonst steht ein Befund mit Owner-Frage im
Bericht. Trägt keine Korpusdatei mehr als einen Chunk, ist A1 auf dem Korpus
nicht prüfbar; der Bericht sagt das und prüft A1 nicht ersatzweise auf
mehrchunkigen Testset-Passagen.

**(4) Gruppenprobe.** "Verwandt" im Testset ist nur ein Ersatzmaß (Anfrage
gegen Abschnitt, nicht Dokument gegen Dokument). Deshalb ordnet `gruppen.tsv`
im selben Commit jede Datei des e2e-Korpus aus ihrem Inhalt in
`build_corpus.py` einer Themengruppe zu oder führt sie als "ohne Gruppe"
(Spalten Datei, Gruppe, Begründung in einem Satz), festgelegt vor jeder
Distanz. Beim abgeleiteten `SIMILAR_CEILING` müssen mindestens 80 Prozent der
Gruppenpaare (Centroid-Distanz zweier Dateien derselben Gruppe) unter der
Obergrenze liegen und höchstens 10 Prozent der Fremdpaare (verschiedene
Gruppen oder eine Datei ohne Gruppe), dieselbe Grenze q wie in (2). Dateien
ohne Text tragen keinen Vektor und fallen aus beiden Zählungen. Hat der
Korpus keine drei Gruppen mit je mindestens zwei Dateien mit Text, oder
verfehlt der Wert eine der beiden Grenzen, wird kein Wert gewählt, sondern ein
Befund mit Owner-Frage geschrieben. Der Korpus wird dafür nicht verändert.

Ein Wert gilt nur, wenn (1), (2) und (4) erfüllt sind. (3) entscheidet über
den Anfragevektor, nicht über die Zahl.

### Die Gruppentabelle

`gruppen.tsv` (39 Dateien) teilt den Korpus so ein:

| Gruppe | Dateien |
|---|---|
| `korpus-selbstbeschreibung` | 01-text-layer.pdf, 03-document.docx, 04-notes.txt, 08-legacy-encoding.txt, 25-kaputte-xref.pdf, 32-startxref-ins-leere.pdf |
| `pdf-strukturprobe` | 29-doppelt-komprimiert.pdf, 35-startaktion-javascript.pdf, 36-eingebettete-datei.pdf, 37-verweis-ins-netz.pdf, 39-tief-verschachtelt.pdf |
| `bau-und-liegenschaft` | 09-bescheid.pdf, 13-ratsvorlage-scan.pdf, 14-pacht-mit-anhang.pdf, 15-schweiz-baubewilligung.pdf, 16-oesterreich-mitteilung.pdf |
| `zahlung` | 17-beleg.jpg, 30-nur-ein-bild.pdf |
| `fax-uebermittlung` | 19-uebermittlung.tif, 21-sendebericht.tif |
| `registratur` | 12-aktenvermerk.txt, 23-gedreht.jpg |
| ohne Gruppe, mit Text | 10-kuendigung.docx, 11-uebersicht.odt, 18-aushang.png, 20-rueckruf.webp |
| ohne Gruppe, ohne Text | 02, 05, 06, 07, 22, 24, 26, 27, 28, 31, 33, 34, 38 |

Die Begründung je Datei steht in der Tabelle selbst.

## 2. Umgebung

| Angabe | Wert |
| --- | --- |
| Modellverzeichnis | aus dem ausgelieferten Abbild `ghcr.io/street1983nk/findling_backend:1.4.3` mit `docker create` und `docker cp` nach außen kopiert, wie es `.github/workflows/integration.yml` für den Läufer tut |
| Datum des Laufs | 2026-10-19, 19:04:19 bis 19:04:33 UTC, strikt seriell (kein anderer Testlauf, kein Browser) |
| Modelldatei | `model.onnx`, 118.101.091 Byte, sha256 `8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6`, identisch mit `MODEL_SHA256` in `.github/workflows/integration.yml` (`rohdaten/00-umgebung.txt`) |
| Python | 3.13.13 |
| onnxruntime | 1.31.0 |
| numpy | 2.5.4 |
| Plattform | Windows 11 Pro 10.0.26200, x86_64 |
| Netzwerk | abgeklemmt: das Werkzeug öffnet keine Verbindung, das Modell kommt aus einem lokalen Verzeichnis, der Korpus aus `scripts/dev/build_corpus.py` |
| Metrik | `vec_distance_l2` über eine `int8[384]`-Spalte, gegen `nearest()` eines echten `VectorStore` geprüft (`--selftest`) |
| Freier Speicher | 3046 MB von 16071 MB vor dem Lauf (`GlobalMemoryStatusEx`, `rohdaten/00-umgebung.txt`), über der Grenze von rund 1,5 GB |

## 3. Populationen und Kommandozeile

**Verwandt.** Je Fall des Testsets `testdata/semantik`: der Anfragetext und
der Abschnitt desselben Falls, beide mit `passage: `-Präfix eingebettet, int8
per `to_int8`, eine Distanz je Fall.

**Unbeteiligt.** Je Sprache: jeder Abschnitt gegen jeden Abschnitt eines
anderen Falls derselben Sprache, jedes ungeordnete Paar einmal.

**Auswahl.** `en.jsonl` und `fr.jsonl` vollständig, von `de.jsonl` genau die
ersten 42 Zeilen. Das ist eine feste Auswahl, unabhängig davon, ob die
Erweiterung von Plan 35-03 auf rund 120 Fälle schon im Bestand steht: die
ersten 42 Zeilen lässt 35-03 byte-gleich.

**Korpus.** Jede Datei von `build_corpus.py`, die Text trägt, mit dem
Chunker des Pakets zerlegt und als Passage eingebettet, wie im Produkt. Für
(3) fragt je mehrchunkigem Dokument der Mittelwert einmal gegen alle Chunks
der anderen Dokumente (Minimum je Dokument), verglichen mit einem Scan je
eigenem Chunk (Minimum über beide Seiten). Für (4) Centroid gegen Centroid je
Dateipaar.

```
cd backend
PYTHONUTF8=1 uv run python ../scripts/dev/vector_distances.py --selftest
PYTHONUTF8=1 uv run python ../scripts/dev/vector_distances.py --similar --derive \
    --model-dir <modellverzeichnis> --dataset-dir ../testdata/semantik \
    --groups ../docs/measurements/2026-10-aehnlich-distanzen/gruppen.tsv
```

Ausgabe vollständig nach `rohdaten/00-selftest.txt` und
`rohdaten/01-similar.txt`. Das Werkzeug druckt Zahlen, Kennungen und
Dateinamen, nie eine Anfrage und nie einen Abschnitt.

## 4. Die Populationen je Sprache

Aus `rohdaten/01-similar.txt`, int8-L2-Skala:

| Population | Anzahl | Minimum | 1. Quartil | Median | 3. Quartil | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Deutsch verwandt | 42 | 62,0645 | 67,7326 | 69,1266 | 73,0530 | 79,7183 |
| Deutsch unbeteiligt | 861 | 51,4101 | 65,9166 | 69,1665 | 72,9452 | 85,6388 |
| Englisch verwandt | 42 | 67,4537 | 74,2235 | 77,0259 | 80,4953 | 84,0000 |
| Englisch unbeteiligt | 861 | 63,0793 | 74,7730 | 78,2432 | 81,6946 | 93,7817 |
| Französisch verwandt | 120 | 61,0492 | 69,3505 | 72,3187 | 74,9683 | 81,1850 |
| Französisch unbeteiligt | 7140 | 45,5851 | 64,5368 | 67,8602 | 70,9013 | 87,3441 |

Das ist der Kern des Befunds: verwandt und unbeteiligt liegen in jeder
Sprache übereinander. Die Mediane trennen sich um höchstens 4,5 Punkte
(Französisch, und dort liegen die verwandten Paare sogar weiter auseinander
als die unbeteiligten), in Deutsch um 0,04. Eine Anfrage und ihr Abschnitt,
beide als Passage eingebettet, liegen nicht näher beieinander als zwei
beliebige Abschnitte desselben Testsets. Die Abschnitte des Testsets sind
kurze Verwaltungstexte ähnlicher Bauart, und e5 legt sie als Passagen dicht
zusammen.

Der Selbsttest (`rohdaten/00-selftest.txt`) bestätigt die Skala gegen
`nearest()` eines echten `VectorStore`: 0,0000 identisch, 97,3088 zwischen
zwei Achsen, 179,6051 orthogonal, 254,0000 entgegengesetzt.

## 5. Das Raster um die beiden Kandidaten

Spalten "rel" sind der Anteil verwandter Paare unter dem Wert, Spalten "cut"
der Anteil abgeschnittener unbeteiligter Paare.

```
   value   rel de   rel en   rel fr     cut de   cut en   cut fr
    61.0   0.0000   0.0000   0.0000     0.9350   1.0000   0.9167
    61.5   0.0000   0.0000   0.0083     0.9187   1.0000   0.9022
    62.0   0.0000   0.0000   0.0083     0.9071   1.0000   0.8881
    62.5   0.0476   0.0000   0.0167     0.8978   1.0000   0.8683
    ...
    83.5   1.0000   0.9286   1.0000     0.0058   0.1696   0.0015
    84.0   1.0000   1.0000   1.0000     0.0058   0.1440   0.0008
    84.5   1.0000   1.0000   1.0000     0.0058   0.1347   0.0007
    86.5   1.0000   1.0000   1.0000     0.0000   0.0778   0.0004
```

Zwischen 61,5 (letzter Wert mit 90 Prozent Schnitt überall) und 84,0 (erster
Wert mit 95 Prozent verwandt überall) liegen 22,5 Punkte. Die vollständigen
Zeilen stehen in den Rohdaten.

## 6. Gruppenprobe und Mittelwert gegen Minimum

**Gruppenprobe.** 26 Dateien mit Text, sechs Gruppen mit je mindestens zwei
Dateien, also prüfbar. 38 Gruppenpaare, 287 Fremdpaare, Centroid gegen
Centroid:

| Paare | Anzahl | Minimum | 1. Quartil | Median | 3. Quartil | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Gruppenpaare | 38 | 0,0000 | 52,6604 | 64,5515 | 69,3498 | 76,8375 |
| Fremdpaare | 287 | 59,1777 | 68,6586 | 72,3948 | 77,1881 | 88,5776 |

```
   value    group  foreign
    65.0   0.5263   0.0836
    65.5   0.5789   0.1045
    71.0   0.8421   0.4181
    84.0   1.0000   0.9547
```

Auf echten Dokumenten trennen sich die Gruppen besser als im Testset
(Median 64,6 gegen 72,4), aber nicht genug für 80 zu 10 Prozent: wo 80
Prozent der Gruppenpaare darunter liegen (ab 71,0), liegen auch 41,8 Prozent
der Fremdpaare darunter.

**Mittelwert gegen Minimum (A1).** Nicht prüfbar: kein mehrchunkiges Dokument
im Korpus (Zeile `A1` der Rohdaten). Für einchunkige Dokumente, und das ist
unter dem Deckel von D-01 bei kurzen Texten der Normalfall, ist der
Mittelwert-Vektor exakt der gespeicherte Vektor (bis auf eine Rundungsstufe,
Test in `backend/tests/test_rrf_fusion.py`).

## 7. Owner-Frage

Die Regel liefert keinen Wert. Zwei Zahlenpaare liegen vor:

- Regel (1) verlangt 84,0; dort fallen in Englisch 14,4 Prozent, in Deutsch
  0,6 Prozent und in Französisch 0,1 Prozent der unbeteiligten Paare weg
  statt 90 Prozent.
- Regel (2) erlaubte höchstens 61,5; dort gehen 42 von 42, 42 von 42 und 119
  von 120 verwandten Paaren verloren.
- Gruppenprobe (4): 80 Prozent Gruppenpaare ab 71,0, höchstens 10 Prozent
  Fremdpaare nur bis 65,0.

Frage an den Owner: Wie geht die Ähnlich-Ansicht (STR-01) weiter, wenn eine
absolute Distanzgrenze auf diesem Modell Verwandtes und Unbeteiligtes nicht
trennt? Denkbare Wege, ohne Wertung und ohne Wahl in diesem Plan:

1. Eine neue Regel mit anderer Grenze q (etwa ein größerer Bezugsbestand
   oder mehr als die halbe Liste Unbeteiligtes zugelassen), neu festgelegt vor
   einer neuen Messung.
2. Ein anderes Maß für "verwandt" (echte Dokumentpaare statt Anfrage gegen
   Abschnitt), wieder mit Regel vor dem Lauf.
3. Keine absolute Obergrenze, sondern nur die Rangfolge der nächsten Nachbarn
   mit sichtbarem Hinweis, dass es Ähnlichkeit und keine Treffer sind; das
   wäre eine Änderung von D-35-03.
4. STR-01 in Phase 35 zurückstellen.

Owner-Entscheid: 19.10.2026, Weg 2 (echte Dokumentpaare, Regel vor dem Lauf, neue Messung)

## 8. Was der Wert nicht ist

- Dieser Bericht gilt nur für `intfloat/multilingual-e5-small`, int8, wie
  ausgeliefert (sha256 oben). Für granite oder jedes andere Modell gilt keine
  Zahl hieraus; ein Modellwechsel verlangt eine neue Messung mit Regel vor dem
  Lauf.
- Die Suchschwelle 86,5 und das Band 14,0 (Anfrage gegen Abschnitt) sind
  keine Ähnlich-Obergrenze. Auf Abschnitt gegen Abschnitt ließen sie fast jedes
  unbeteiligte Paar durch.
- Die Bildtexte des Korpus sind die beabsichtigten Texte des Generators, nicht
  die Ausgabe von Tesseract. OCR-Rauschen ist in dieser Messung nicht
  enthalten.

## 9. Nachvollziehen

```
cd backend
PYTHONUTF8=1 uv run python ../scripts/dev/vector_distances.py --selftest
PYTHONUTF8=1 uv run python ../scripts/dev/vector_distances.py --similar --derive \
    --model-dir <modellverzeichnis> --dataset-dir ../testdata/semantik \
    --groups ../docs/measurements/2026-10-aehnlich-distanzen/gruppen.tsv
```

`<modellverzeichnis>` ist `/usr/local/share/findling/model` aus dem
ausgelieferten Abbild, per `docker create` und `docker cp` nach außen kopiert.
Der Lauf dauert auf der Entwicklungsmaschine rund 15 Sekunden.

## 10. Nachmessung Weg 2: Fassungspaare

Auf den Owner-Entscheid vom 19.10.2026 (Abschnitt 7, Weg 2) misst diese
Nachmessung "verwandt" neu: nicht mehr eine Anfrage gegen ihren Abschnitt,
sondern echte Dokumentpaare, Centroid gegen Centroid, so wie die
Ähnlich-Ansicht fragt. Abschnitte 1 bis 9 bleiben als Beleg des ersten Laufs
unverändert stehen.

### 10.1 Regel (vor der Messung festgelegt)

Diese Regel steht in einem eigenen Commit vor der Erweiterung des Werkzeugs und
vor jeder Rohdatei der Nachmessung (Präfix `02-`). Der Wert wird mechanisch aus
dem Raster abgeleitet, nicht nach Sicht der Zahlen gewählt.

**Warum ein abgeleiteter Bestand und nicht `gruppen.tsv`.** Der e2e-Korpus hat
26 Dateien mit Text, und seine Gruppen sind Themengruppen verschiedener Texte,
keine Fassungen eines Inhalts. Ihre Zahlen sind seit Abschnitt 6 bekannt; eine
neue Grenze auf denselben Paaren wäre nach Sicht der Zahlen gewählt. Der
Korpus wird deshalb nicht verändert, und die Paar-Wahrheit kommt aus einem
neuen, deterministisch erzeugten Bestand.

**(F0) Der Bestand.** Quelle sind alle Abschnitte (Feld `passage`) der drei
Dateien unter `testdata/semantik`, je Sprache für sich: Deutsch 120, Englisch
42, Französisch 120, in der Reihenfolge der Datei. Je Sprache gilt:

1. Ein Zufallsgenerator `random.Random(3504)` wird für jede Sprache neu
   angelegt (Seed 3504, fest, hier festgelegt).
2. Die Positionen 0 bis n minus 1 werden mit `shuffle` gemischt und der Reihe
   nach in Blöcke zu je vier Abschnitten geteilt; ein Rest unter vier fällt
   weg (Englisch: 2 Abschnitte). Das ergibt Deutsch 30, Englisch 10,
   Französisch 30 Blöcke.
3. **Basisdokument** eines Blocks: die vier Abschnitte in Blockreihenfolge,
   getrennt durch eine Leerzeile.
4. **Fassung** desselben Blocks: Block für Block zieht der Generator
   `randrange(4)`, dieser Abschnitt wird gestrichen, die übrigen drei stehen in
   umgekehrter Reihenfolge, getrennt durch eine Leerzeile. Das ist eine
   überarbeitete Fassung: ein Absatz gestrichen, die anderen umgestellt, kein
   Wort neu.
5. Jedes Dokument wird wie im Produkt behandelt: Zerlegung mit dem Chunker des
   Pakets, Einbettung als Passage, int8 per `to_int8`, Dokumentvektor per
   `findling.index.fusion.centroid`.

**Fassungspaare (verwandt):** je Block Basisdokument gegen seine Fassung,
eine Distanz je Block. **Unbeteiligte Paare:** jedes ungeordnete Paar zweier
Dokumente (Basis oder Fassung) aus verschiedenen Blöcken derselben Sprache.
Sie teilen keinen Abschnitt. Erwartete Anzahlen: Deutsch 30 und 1740,
Englisch 10 und 180, Französisch 30 und 1740.

**(F1) Fassungen.** Kandidat ist der kleinste Rasterwert (Schritt 0,5 auf der
int8-L2-Skala, 0 bis 254), unter dem (Distanz kleiner oder gleich dem Wert) in
jeder Sprache mindestens 95 Prozent der Fassungspaare liegen. Bei 10
englischen Paaren heißt das: alle 10.

**(F2) Unbeteiligte.** Obergrenze ist der größte Rasterwert, der in jeder
Sprache mindestens 90 Prozent der unbeteiligten Paare abschneidet (Distanz
größer als der Wert). Die 90 Prozent sind dieselbe Grenze q wie in Abschnitt 1,
mit derselben Herleitung (Liste von höchstens 10, Bezugsbestand 50
unbeteiligte Dokumente, höchstens 5 Unbeteiligte im Mittel).

**(F3) Der Wert.** Ist der Kandidat aus (F1) kleiner oder gleich der Obergrenze
aus (F2), ist `SIMILAR_CEILING` die Mitte beider Werte, auf das 0,5-Raster
abgerundet. Beide Enden sind Rasterwerte, die abgerundete Mitte liegt also
immer zwischen ihnen und hält zu beiden Seiten Abstand, wie die Ableitung der
Suchschwelle im September. Ist der Kandidat größer als die Obergrenze, oder
gibt es keine Obergrenze, lautet das Ergebnis **"Regel nicht erfüllbar"**:
kein Wert, beide Zahlen und der Verlust je Sprache in den Bericht, Plan 35-05
startet nicht ohne Owner-Wort. Ein stiller Rückfall auf die Suchschwelle oder
auf einen Wert aus Abschnitt 1 bis 9 ist ausgeschlossen.

**(F4) Mindestumfang.** Hat eine Sprache weniger als 10 Fassungspaare, ist die
Regel nicht prüfbar und das Ergebnis lautet ebenfalls "Regel nicht
erfüllbar".

**Was nicht entscheidet.** Die Gruppenprobe aus Abschnitt 1 (4) misst
Themenverwandtschaft verschiedener Texte, nicht Fassungen eines Inhalts. Beim
abgeleiteten Wert weist der Bericht ihre beiden Anteile (Gruppenpaare und
Fremdpaare darunter) als Information aus, damit sichtbar ist, was der Wert für
themenverwandte, aber verschiedene Dokumente bedeutet. Sie entscheidet nicht
über den Wert. Annahme A1 (Mittelwert gegen Minimum) bleibt außerhalb dieser
Nachmessung.

### 10.2 Ergebnis: `SIMILAR_CEILING` 54,5

**Die Regel ist erfüllt. `SIMILAR_CEILING` = 54,5** (int8-L2-Skala, nur
`intfloat/multilingual-e5-small` int8 wie ausgeliefert). Grundlage für Plan
35-05; die Konstante in `config.py` setzt erst 35-05.

- (F1) Kandidat 46,0: dort liegen in jeder Sprache alle Fassungspaare
  darunter (Englisch erreicht 95 Prozent erst bei 46,0, bei 45,5 sind es 9 von
  10); abgeschnitten werden dort 100 Prozent der unbeteiligten Paare in allen
  drei Sprachen.
- (F2) Obergrenze 63,5: der größte Rasterwert, der überall mindestens 90
  Prozent der unbeteiligten Paare abschneidet (Deutsch 0,9552, Englisch
  0,9722, Französisch 0,9098; bei 64,0 fällt Französisch auf 0,8782). Unter
  63,5 geht kein Fassungspaar verloren (0 von 30, 0 von 10, 0 von 30).
- (F3) Mitte von 46,0 und 63,5 ist 54,75, abgerundet 54,5. Abstand 8,5 nach
  unten und 9,0 nach oben.
- (F4) erfüllt: 30, 10 und 30 Fassungspaare.

Bei 54,5 liegen alle 70 Fassungspaare darunter und alle 3660 unbeteiligten
Paare darüber.

| Population | Anzahl | Minimum | 1. Quartil | Median | 3. Quartil | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Deutsch Fassungen | 30 | 23,3452 | 28,2489 | 34,5975 | 36,2491 | 41,8091 |
| Deutsch unbeteiligt | 1740 | 55,4076 | 67,6739 | 70,4095 | 73,0633 | 84,3682 |
| Englisch Fassungen | 10 | 23,1301 | 29,4710 | 32,9031 | 40,3191 | 45,6289 |
| Englisch unbeteiligt | 180 | 61,0492 | 68,3081 | 71,4143 | 74,5318 | 82,3286 |
| Französisch Fassungen | 30 | 22,8254 | 28,2356 | 31,5357 | 35,0141 | 41,6293 |
| Französisch unbeteiligt | 1740 | 57,6888 | 65,6201 | 67,7975 | 70,4432 | 82,1158 |

Anders als im ersten Lauf trennen sich die Verteilungen: zwischen der weitesten
Fassung (45,6289, Englisch) und dem nächsten unbeteiligten Paar (55,4076,
Deutsch) liegt eine Lücke von knapp 10 Punkten.

```
   value   ver de   ver en   ver fr     cut de   cut en   cut fr
    46.0   1.0000   1.0000   1.0000     1.0000   1.0000   1.0000
    54.5   1.0000   1.0000   1.0000     1.0000   1.0000   1.0000
    55.5   1.0000   1.0000   1.0000     0.9994   1.0000   1.0000
    63.5   1.0000   1.0000   1.0000     0.9552   0.9722   0.9098
    64.0   1.0000   1.0000   1.0000     0.9414   0.9611   0.8782
```

Selbsttest dieses Laufs (`rohdaten/02-selftest.txt`): 0,0000 / 97,3088 /
179,6051 / 254,0000 gegen `nearest()`, wie im ersten Lauf.

### 10.3 Was 54,5 bedeutet und was nicht

- **Information, nicht entscheidend (Gruppenprobe):** bei 54,5 liegen 26,32
  Prozent der 38 Gruppenpaare des e2e-Korpus darunter (10 von 38) und 0 der
  287 Fremdpaare. Die Ähnlich-Ansicht zeigt mit diesem Wert also Fassungen und
  sehr nahe Texte, aber die meisten themenverwandten, verschieden formulierten
  Dokumente nicht. Das ist die Folge des Maßes, das der Owner gewählt hat, und
  gehört in die Erwartung an STR-01.
- **Grenzen des Bestands:** Die Basisdokumente mischen vier zufällige
  Abschnitte verschiedener Fälle; echte Dokumente sind thematisch
  geschlossener. Eine Fassung streicht und stellt um, sie formuliert nicht
  neu. Umformulierte Fassungen können weiter auseinanderliegen. Die Abschnitte
  sind kurze Verwaltungstexte; die Zahl der Chunks je Dokument weist das
  Werkzeug nicht aus.
- **Kein OCR-Rauschen**, wie in Abschnitt 8. Nur e5-small int8; ein
  Modellwechsel verlangt eine neue Messung mit Regel vor dem Lauf.
- **Mass der Route gegen Mass dieser Messung (A1, Audit 35-12):** Gemessen
  wurde hier Centroid gegen Centroid (Dokument gegen Dokument); die Route aus
  Plan 35-05 vergleicht den Centroid der Quelle gegen einzelne Abschnitte der
  Nachbarn und wertet je Dokument das Minimum. Die beiden Masse koennen in
  beide Richtungen voneinander abweichen (die Renormierung des Centroids kann
  Aehnlichkeiten anheben); der Abstand von knapp 10 Punkten zwischen dem
  entferntesten Fassungspaar (45,63) und dem naechsten unbeteiligten Paar
  (55,41) ist der Spielraum, den die Decke 54,5 dafuer hat. Live
  gegengeprueft im Audit 35-12: die byte-gleiche Kopie erscheint als
  Nachbar, thematisch nur verwandte Dokumente fallen wie in der Gruppenprobe
  ueberwiegend heraus, fremde nie.

### 10.4 Nachvollziehen

```
cd backend
PYTHONUTF8=1 uv run python ../scripts/dev/vector_distances.py --selftest
PYTHONUTF8=1 uv run python ../scripts/dev/vector_distances.py --versions --derive \
    --model-dir <modellverzeichnis> --dataset-dir ../testdata/semantik \
    --groups ../docs/measurements/2026-10-aehnlich-distanzen/gruppen.tsv
```

Ausgabe vollständig in `rohdaten/02-selftest.txt` und `rohdaten/02-versions.txt`,
Umgebung, Speicher (3086 MB frei vor dem Lauf) und Modell-Hash in
`rohdaten/02-umgebung.txt`. Der Lauf dauerte rund 33 Sekunden (19:29:02 bis
19:29:35 UTC), strikt seriell.
