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
| Modelldatei | `model.onnx`, sha256 wird gegen `MODEL_SHA256` in `.github/workflows/integration.yml` (`8da4c9ba...b6`) geprüft, Ergebnis in `rohdaten/` |
| Python | 3.13.13 |
| onnxruntime | 1.31.0 |
| numpy | 2.5.4 |
| Plattform | Windows 11 Pro 10.0.26200, x86_64 |
| Netzwerk | abgeklemmt: das Werkzeug öffnet keine Verbindung, das Modell kommt aus einem lokalen Verzeichnis, der Korpus aus `scripts/dev/build_corpus.py` |
| Metrik | `vec_distance_l2` über eine `int8[384]`-Spalte, gegen `nearest()` eines echten `VectorStore` geprüft (`--selftest`) |
| Freier Speicher | vor dem Lauf gemessen, Wert in `rohdaten/` |

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
