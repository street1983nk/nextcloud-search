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
