# DACH-Erkennungsqualität: die Zeichenfehlerrate auf gerenderten Seiten

Sechs gerenderte Seiten, 3.148 Zeichen bekannter Wahrheit, ein Lauf im
Laufzeitabbild dieses Repositories. Der Bericht beantwortet die Frage des
Owners, ob die OCR-Kette Umlaute, Datums- und Währungsformate der DACH-Region
sauber liest. Bisher stand dazu ein Suchtreffer, und ein Suchtreffer kann die
Frage nicht beantworten: ein Zeichen, das die Engine falsch liest, ist in einem
Wort, das trotzdem auf denselben Term stemmt, für eine Suche unsichtbar.

## Das Verdikt, zuerst

**Null Fehler.** Auf allen sechs Seiten, in allen drei Sprachvarianten, über
3.148 Zeichen. Die Zeichenfehlerrate ist 0,000000. Das schließt jeden Fall ein,
nach dem der Auftrag gefragt hat: die Kleinumlaute, die drei Großumlaute in
`ÄNDERUNGEN AN DER AUSSENHÜLLE BENÖTIGEN EINE ZUSTIMMUNG`, das Datum
`01.03.2026` und die ausgeschriebene Form `1. März 2026`, den Betrag
`1.234,56 Euro` mit deutschen Trennzeichen, den Betrag `CHF 1'234.56` mit dem
Schweizer Apostroph als Tausendertrennzeichen, und das Aktenzeichen
`BH/MU/2026/0042-7` mit seinen zwei Schrägstrichen.

**Wofür die Null gilt und wofür nicht,** steht weiter unten unter "Was diese
Zahl nicht sagt", und dieser Abschnitt ist der wichtigste des Berichts. Kurz:
sie gilt für gerenderte, saubere Seiten in einer Schrift, deren Prüfsumme im
Repository steht. Sie gilt nicht für einen fotografierten Beleg.

## Die Umgebung dieser Messung

| Angabe | Wert |
|---|---|
| Datum | 2026-09-06 |
| Abbild | `findling-ocr-quality:local`, lokaler Bau aus `backend/Dockerfile` |
| Abbildkennung | `sha256:ee05fa9cde888a28b63e1e7776a910ce945d26422f6be68e244f264da4ee9886` |
| Basis-Abbild | `python:3.13-slim-trixie@sha256:ffb752e1...c6e30a`, wie in `backend/Dockerfile` gepinnt |
| Maschine | x86_64, 13th Gen Intel Core i5-1335U, 12 sichtbare Kerne, Docker Desktop unter Windows 11 |
| Engine | tesseract 5.5.0, leptonica 1.84.1, libtiff 4.7.0, libpng 1.6.48, libwebp 1.5.0 |
| Sprachdaten | `deu`, `eng`, `fra`, `osd`, alle `1:4.1.0-2`, hart gepinnt im Dockerfile |
| Aufrufform | `--oem 1 --psm 3 -c tessedit_do_invert=0`, unverändert die von `findling.extract.ocr` |
| Auflösung | 300 dpi, der Standardwert von `FINDLING_OCR_DPI` |
| Netzwerk | abgeklemmt, `--network none` |

Es ist kein Registry-Digest: dieses Abbild wurde nie veröffentlicht. Es ist
derselbe Bau, aus dem auch die Gegenproben weiter unten stammen.

## Die Kommandozeile

```
docker build --build-context scripts=./scripts -f backend/Dockerfile \
    -t findling-ocr-quality:local backend

docker run --rm --network none \
    -v "$PWD/testdata:/testdata:ro" \
    --entrypoint /app/.venv/bin/python findling-ocr-quality:local \
    -m findling.extract.ocr_quality \
        --corpus /testdata/corpus --truth /testdata/corpus-truth.json
```

Das Werkzeug läuft aus dem Abbild, nicht aus dem Arbeitsbaum: die Engine, die
Sprachdaten, `pypdfium2` und der Code sind derselbe Stand, der ausgeliefert wird.
Nur der Korpus und die Wahrheitsdatei kommen von außen, schreibgeschützt
eingehängt, weil sie Testdaten sind und nicht ins Abbild gehören.

**Nebenprobe zur Sicherheit:** derselbe Lauf gegen ein Abbild, das gebaut wurde,
bevor `ocr_quality.py` existierte, mit `-e PYTHONPATH=/src` und dem Quellbaum
eingehängt, lieferte Zeile für Zeile dieselben Zahlen
(`sha256:22f716fe7a838a0c3532b212a7882855127e88a9eb42bd97b3de9770d7386590`). Der
Bau des Abbilds verschiebt die Messung also nicht.

## Die Rohdaten

```
ocr character error rate, dpi=300 languages=3
page 1         variant=de chars=701    errors=0     cer=0.000000
page 2         variant=de chars=561    errors=0     cer=0.000000
page 3         variant=de chars=316    errors=0     cer=0.000000
page 4         variant=ch chars=656    errors=0     cer=0.000000
page 5         variant=at chars=587    errors=0     cer=0.000000
page 6         variant=de chars=327    errors=0     cer=0.000000

variant=at     pages=1   chars=587    errors=0     cer=0.000000
variant=ch     pages=1   chars=656    errors=0     cer=0.000000
variant=de     pages=4   chars=1905   errors=0     cer=0.000000
overall        pages=6   chars=3148   errors=0     cer=0.000000
bar=0.050000 verdict=ok
```

Rückgabewert 0. Das Werkzeug gibt Zahlen aus und sonst nichts, weder den
erkannten noch den erwarteten Text und keinen Pfad; die Seiten tragen deshalb
ihre laufende Nummer und ihre Sprachvariante statt eines Dateinamens. Die
Zuordnung steht hier:

| Seite | Datei | Variante |
|---|---|---|
| 1 bis 3 | `13-ratsvorlage-scan.pdf` | de |
| 4 | `15-schweiz-baubewilligung.pdf` | ch |
| 5 | `16-oesterreich-mitteilung.pdf` | at |
| 6 | `30-nur-ein-bild.pdf` | de |

## Woher die Wahrheit kommt

Aus dem Generator, nicht aus einem fremden Korpus. `scripts/dev/build_corpus.py`
rendert diese Seiten aus eigener erfundener Prosa; der Quelltext ist damit die
Ground Truth, byteweise. Der Generator schreibt sie nach
`testdata/corpus-truth.json`, sortiert und mit einfachem Zeilenumbruch, und
`build_corpus.py --check` vergleicht beides bei jedem Lauf. Ein DACH-Scan-Korpus
von außen, mit unklarer Lizenz und ohne Bitgleichheit, wird dafür nicht
gebraucht.

Zwei Riegel stehen davor, und beide sind älter als diese Messung. `_font` prüft
die SHA-256 der Schriftdatei und rendert nicht, wenn sie sich um ein Byte
verschoben hat; `_assert_every_glyph_exists` bricht den Bau ab, wenn ein Zeichen
als Ersatzkasten herauskäme. Seit dieser Messung läuft der zweite Riegel über
**jedes** gerenderte Zeichen des Korpus statt über eine handgeschriebene Probe,
denn genau der Apostroph aus `CHF 1'234.56` ist das Zeichen, an das niemand
gedacht hätte.

| Eingabe | sha256 |
|---|---|
| `testdata/corpus/13-ratsvorlage-scan.pdf` | `320bb1aa17c9192d822ea6b6c570f7d125e113181e05ad62fe1afd728a0a81f3` |
| `testdata/corpus/15-schweiz-baubewilligung.pdf` | `0662fac0865a12184438decfe50dbb9d8ec50978ecce75925452814e85ebadc6` |
| `testdata/corpus/16-oesterreich-mitteilung.pdf` | `7153248c9b13c4516dd6e886235141d3dab582468cdc107b19185a5683dc151c` |
| `testdata/corpus/30-nur-ein-bild.pdf` | `df3cd87f72cea4a1cdf4b3c4f091833d797c2c8faa4db30ce8c84ffff9d7f288` |
| `testdata/corpus-truth.json` | `33090c1cebe8411f38e095c5662f13868c0bf7f29cebef24a399bbaa6c531ad5` |
| `testdata/fonts/DejaVuSans.ttf` | `57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e` |

Vor der Rechnung werden beide Seiten normalisiert: jede Folge von Leerraum wird
zu einem Leerzeichen, die Enden werden abgeschnitten. Das ist eine
Messentscheidung und keine Bequemlichkeit. Der Zeilenumbruch einer gerenderten
Seite und der Zeilenumbruch, den tesseract zwischen die gefundenen Zeilen setzt,
sind zwei verschiedene Dinge; ohne die Normalisierung wäre das Layout der
größte Posten der Rate und die Zahl sagte etwas über den Seitenumbruch statt
über die Erkennung.

## Die drei Gegenproben

Eine Null ist die Zahl, bei der man zuerst prüft, ob überhaupt gemessen wurde.
Drei Läufe im selben Abbild, mit demselben Werkzeug, zeigen, dass die Rate sich
bewegt, sobald man an der Kette dreht.

| Lauf | Gesamt | de | ch | at |
|---|---|---|---|---|
| Referenz, `deu+eng+fra`, 300 dpi | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| nur `eng`, 300 dpi | 0,020330 | 0,023622 | 0,019817 | 0,010221 |
| nur `fra`, 300 dpi | 0,007306 | 0,008924 | 0,009146 | 0,000000 |
| `deu+eng+fra`, 72 dpi | 0,006036 | 0,003150 | 0,006098 | 0,015332 |

Die Läufe wurden über `FINDLING_OCR_LANGUAGES` und `FINDLING_OCR_DPI` gestellt,
also über die Schalter, die auch ein Admin hat, und nicht über einen
Sonderpfad im Code.

**Zwei Befunde stecken in dieser Tabelle, und beide waren so nicht erwartet.**

Erstens: eine falsche Sprache kostet erstaunlich wenig. `eng` allein liest
dieselben deutschen, schweizerischen und österreichischen Seiten mit 0,0203,
`fra` allein mit 0,0073. Auf sauber gerenderter lateinischer Schrift stützt sich
der LSTM-Erkenner offenbar kaum auf sein Sprachmodell. Das hat eine Folge für
den Riegel, und sie steht unten.

Zweitens: die Annahme A7 der Recherche, Großbuchstaben mit Umlauten seien bei
niedriger Auflösung eine bekannte Schwäche von tesseract, ist auf diesem
Material **nicht** eingetreten. Bei 72 dpi, dem niedrigsten Wert, den
`FINDLING_OCR_DPI` überhaupt zulässt, bleiben über sechs Seiten 19 Fehler
übrig, und die deutsche Variante mit ihren vier Seiten ist mit 0,0032 die beste
der drei. Die Annahme war eine Annahme und ist als solche gekennzeichnet
gewesen; sie ist hiermit auf gerendertem Text widerlegt und auf fotografiertem
Material weiterhin ungeprüft.

## Der Riegel, und warum er grob ist

`findling.extract.ocr_quality.MAX_CHARACTER_ERROR_RATE` steht auf 0,05. Der
gemessene Wert ist 0,0; der Zuschlag ist damit der ganze Riegel und erlaubt
diesem Korpus 157 falsche Zeichen, bevor er anschlägt.

Er ist absichtlich nicht schärfer. Eine engere Grenze wäre genau die Aussage
über die Fassung der Engine, die `docs/testing.md` ausdrücklich nicht machen
will: die Engine hängt am Digest des Basis-Abbilds und nicht an einer gepinnten
Version, ein Debian-Punktrelease verschiebt einzelne Zeichen, und in
`docs/ocr.md` steht bereits eine solche Verschiebung, ein großes U, das seine
zwei Punkte verlor.

Was der Riegel deshalb **nicht** fängt, ist oben gemessen: eine falsch gewählte
Sprache. Der Plan für dieses Modul hatte angenommen, dass er das könne; die
Gegenprobe sagt etwas anderes, und der Kommentar an der Konstanten sagt es jetzt
auch. Eine Grenze, die `eng` allein noch fängt, müsste bei etwa 0,005 stehen,
also bei fünfzehn Zeichen Spielraum über 3.148, und das ist die scharfe Grenze
unter anderem Namen. Die falsche Sprache wird dort abgefangen, wo sie hingehört:
die Positivliste in `findling.config` weist eine Sprache ab, die das Abbild
nicht trägt, und der Bau des Abbilds scheitert, wenn `--list-langs` nicht `deu`,
`eng` und `fra` zeigt.

Was er fängt, ist der Totalausfall, für den er benannt ist. Eine Seite, die leer
oder als Rauschen zurückkommt, liegt bei oder nahe 1,0 und reißt ihn um den
Faktor zwanzig. Genau dafür gibt es einen Testfall.

## Was diese Zahl nicht sagt

Ehrlichkeitshalber, damit die nächste Phase nicht das Falsche annimmt:

- **Nichts über fotografierte Belege.** Die Vorlage ist gerenderter Text, also
  der freundlichste denkbare Fall: kein Schräglauf, kein Rauschen, kein
  Schattenwurf, kein Papierknick, eine einzige Schriftart in einer einzigen
  Größe. Ein schief abfotografiertes Protokoll liest diese Kette schlechter, um
  wie viel schlechter sagt dieser Bericht nicht, und `STACK.md` führt RapidOCR
  seit dem 15.08.2026 genau für diesen Fall als möglichen Zusatzpfad.
- **Nichts über die Abnahme.** Das Gate zu D-09 bleibt ein Suchtreffer und wird
  von dieser Messung nicht ersetzt und nicht verschärft. Die Messung steht
  daneben und beantwortet eine andere Frage.
- **Nichts über Fraktur.** Die Fraktur-Option ist dokumentiert und
  ausdrücklich kein Standard; es wurde keine Fraktur-Seite gerendert und keine
  gemessen. Die Paketlage steht in `docs/ocr.md` und im Kommentar von
  `backend/Dockerfile`.
- **Nichts über ARM.** Der Lauf ist amd64. Die Sprachdaten sind
  `Architecture: all` und damit bitgleich, und die Rate hängt an den Pixeln und
  nicht an der Rechenleistung, aber gemessen ist sie hier nicht.
- **Nichts über Zeit oder Speicher.** Dieser Bericht misst Zeichen. Die
  Zeitwerte und die Adressraumwerte der OCR-Kette stehen in `docs/ocr.md` unter
  "Messprotokoll".

## Reproduzieren

```
uv run --directory backend python ../scripts/dev/build_corpus.py --check
docker build --build-context scripts=./scripts -f backend/Dockerfile \
    -t findling-ocr-quality:local backend
docker run --rm --network none \
    -v "$PWD/testdata:/testdata:ro" \
    --entrypoint /app/.venv/bin/python findling-ocr-quality:local \
    -m findling.extract.ocr_quality \
        --corpus /testdata/corpus --truth /testdata/corpus-truth.json
```

Die Gegenproben stellt man über die Umgebung des dritten Befehls:
`-e FINDLING_OCR_LANGUAGES=eng`, `-e FINDLING_OCR_LANGUAGES=fra`,
`-e FINDLING_OCR_DPI=72`.

Der erste Befehl ist kein Beiwerk: er stellt fest, dass die Seiten auf der Platte
byteweise die sind, die der Generator baut, und dass die Wahrheitsdatei zu ihnen
passt. Ohne ihn misst der dritte Befehl gegen eine Wahrheit, von der niemand
weiß, ob sie noch zu den Pixeln gehört.
