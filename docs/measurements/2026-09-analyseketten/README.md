# Die Position von ascii_fold, Fall für Fall gemessen, 23.09.2026

Dieser Bericht ist die Messgrundlage der Phase 17. Jede spätere Aussage dieser
Phase über Token soll eine Zeile in `rohdaten/familien.tsv` zitieren können
statt geraten zu werden, und jede Zahl über Treffer, Verluste und Stoppwörter
soll eine Zeile in `rohdaten/kennzahlen.txt` haben.

Gemessen wurde mit `scripts/dev/measure_chains.sh`, das
`scripts/dev/chain_probe.py` fährt. Es gibt hier keinen Wegwerf-Container,
anders als bei der deutschen Kette: alle vier Snowball-Stoppwortlisten und alle
vier Snowball-Stemmer sind in tantivy einkompiliert, also genügt `uv run` aus
`backend/`, und ein Container würde nur Laufzeit kosten.

Die Sonde baut die sieben Kandidatenketten selbst, weil sechs davon im Produkt
nicht existieren. Diese Ausnahme wird sofort wieder geschlossen: die Siegerkette
A+ läuft Token für Token gegen `snowball_analyzer()` aus dem ausgelieferten
Paket, für jede Form jeder Familie. Eine einzige abweichende Form ist
Rückgabecode 1. Der Lauf dieses Berichts endete mit 0, also misst der Bericht
das Produkt und nicht sich selbst.

Der Lauf sieht nie Nutzertext. Die Sonde liest die Fixtures dieses Repos und
eine veröffentlichte Snowball-Stoppwortliste, nie `state.db`, nie einen Index,
nie eine Nutzerdatei (T-02-14, hier als T-17-17 geführt).

Hinweis zur Schreibung: die Nachbarverzeichnisse unter `docs/measurements/`
verwenden ASCII-Ersatzschreibung. Das ist Bestand und wird nicht angefasst;
dieser neue Text folgt der Projektregel und schreibt echte Umlaute.

---

## 1. Die Umgebung, und der Beweis des gemessenen Standes

| Was | Wert |
|---|---|
| Datum des Laufs | 2026-09-23 |
| Suchbibliothek dieses Laufs | `tantivy==0.26.0`, Banner `tantivy v0.26.0, index_format v7`, die Fassung aus `backend/uv.lock` |
| Gegenprobe der Recherche | `tantivy==0.26.2`, Banner `tantivy v0.26.2, index_format v7`, identische Tokenisierung über 224 Zeilen |
| Python | 3.13.13 |
| Rechner | Entwicklerrechner, Windows 11, x86_64, kein Container |
| Stoppwortquelle | `quickwit-oss/tantivy`, Tag **0.26.2**, `src/tokenizer/stop_word_filter/stopwords.rs`, BSD-3-Clause |
| Als Fixture abgelegt | `backend/tests/fixtures/snowball_stopwords_0_26_2.txt`, maschinell erzeugt |
| Wortzahlen der eingebauten Listen | spanish **308**, italian **279**, portuguese **203**, dutch **101** |
| Gefaltete Ergänzungsliste | 117 Einträge, es 77, it 10, nl 0, pt 30 |
| Digest der Ergänzungsliste | `d056d4597f989c7e03113c529c92cef980254f72c4d4e5deace4588ea033311a` |
| Formfamilien | 65, zusammen 573 geordnete Paare |

Eingabe waren die vier Fixtures `backend/tests/fixtures/chain_cases_es.txt`,
`chain_cases_it.txt`, `chain_cases_nl.txt` und `chain_cases_pt.txt`, eine
Formfamilie je Zeile. Die Rohdaten liegen unverändert in `rohdaten/`:
`familien.tsv` mit einer Zeile je Form und Kandidat, `kennzahlen.txt` mit
ausschliesslich Zahlen und Digests, `verluste.tsv` mit den Formpaaren, die
unter der ausgelieferten Kette nicht zueinander finden.

Die sieben Kandidaten, `CSTOP` steht für `Filter.custom_stopword` mit der
gefalteten Ergänzungsliste:

| Kürzel | Kette |
|---|---|
| A | `low, fold, stop, long, stem` |
| **A+** | `low, fold, stop, CSTOP, long, stem` |
| B | `low, stop, fold, long, stem` |
| B+ | `low, stop, CSTOP, fold, long, stem` |
| C | `low, stop, long, stem, fold` |
| **C+** | `low, stop, CSTOP, long, stem, fold` |
| D+ | `low, fold, stop, CSTOP, long, stem, fold` |

---

## 2. Die Kandidatentabelle

Gemessen wird über Formfamilien: für jedes Lemma alle Schreibweisen, die ein
Mensch tippen oder ein Dokument tragen kann, und gezählt werden die geordneten
Paare (getippte Form, Form im Dokument), die mindestens einen Term teilen.
Hundert Prozent heisst: jede Schreibweise findet jede andere.

| Sprache | Familien | Paare | A | **A+** | B | B+ | C | **C+** | D+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| es | 20 | 208 | 174 | **174** | 174 | 174 | 178 | **178** | 174 |
| it | 14 | 56 | 56 | **56** | 56 | 56 | 54 | **54** | 56 |
| nl | 13 | 81 | 57 | **57** | 57 | 57 | 57 | **57** | 57 |
| pt | 18 | 228 | 180 | **180** | 180 | 180 | 174 | **174** | 180 |
| **Summe** | **65** | **573** | 467 | **467** | 467 | 467 | 463 | **463** | 467 |

Jede Zelle steht als `<code>_<rezept>_hits` in `rohdaten/kennzahlen.txt`.

Drei Nebenbefunde, die aus derselben Tabelle fallen:

- `D+` ist in jeder Sprache identisch mit `A+`. Die zweite Faltung hinter dem
  Stemmer ist ein No-op, wenn vorn schon gefaltet wurde. Nicht einbauen.
- `B+` ist in der Familienmetrik identisch mit `A+`. Der Unterschied liegt nur
  bei den niederländischen Betonungsakzenten, siehe Abschnitt 4, Zeile 9.
- Niederländisch liefert in allen sieben Ketten dieselbe Zahl. Der
  niederländische Stemmer faltet selbst.

---

## 3. Die Stoppwort-Leck-Tabelle

Gezählt werden die Wörter der eingebauten Liste, die trotzdem einen Term
erzeugen, getrennt nach akzentuierter und gefalteter Schreibweise.

| Sprache | A (akz./flach) | A+ | B | B+ | C | C+ | D+ |
|---|---|---|---|---|---|---|---|
| es | 77 / 77 | **0 / 0** | 0 / 77 | 0 / 0 | 0 / 77 | 0 / 0 | 0 / 0 |
| it | 10 / 10 | **0 / 0** | 0 / 10 | 0 / 0 | 0 / 10 | 0 / 0 | 0 / 0 |
| nl | 0 / 0 | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| pt | 30 / 30 | **0 / 0** | 0 / 30 | 0 / 0 | 0 / 30 | 0 / 0 | 0 / 0 |

Der Messlauf dieses Berichts fährt die Dichtheitsmessung für die ausgelieferte
Kette A+ und schreibt sie als `<code>_leaks_accented` und `<code>_leaks_flat`
nach `rohdaten/kennzahlen.txt`. Beide Zahlen sind für alle vier Sprachen 0.

Lesart: die kopierte englische Kette A leckt beide Schreibweisen, die Ketten B
und C lecken die flach getippte. Nur die Varianten mit der gefalteten
Ergänzungsliste sind in beiden Schreibweisen dicht. Die Ergänzungsliste ist
damit unabhängig von der Faltposition Pflicht, und das ist das einzige Ergebnis
dieser Messung, das keine Abwägung braucht.

---

## 4. Das Verdikt je Sprache

| Sprache | Messsieger | Abstand | Verdikt |
|---|---|---|---|
| es | `fold spät` (C+) | +4 von 208 Paaren, 1,9 Punkte | **`fold früh` (A+)**, der Abstand wird von der Einheitlichkeit aufgewogen |
| it | `fold früh` (A+) | +2 von 56 Paaren, und A+ ist fehlerfrei | **`fold früh` (A+)** |
| nl | Unentschieden | 0 | **`fold früh` (A+)**, weil es die Betonungsakzente ohne Zusatzliste erledigt |
| pt | `fold früh` (A+) | +6 von 228 Paaren | **`fold früh` (A+)** |

Vier Gründe für die einheitliche Kette, trotz des spanischen Gegenbefunds:

1. Der Abstand ist in beiden Richtungen unter drei Prozentpunkten und beruht in
   Spanisch auf genau einer Wortklasse, dem Akzent in der Snowball-Endung.
2. `fold früh` ist die Form der schon ausgelieferten englischen Kette, und eine
   leere Ergänzungsliste ist gemessen ein No-op. Eine Fabrik bedient damit en,
   es, it, nl und pt, ohne die englische Tokenisierung um ein Byte zu
   verschieben. Deutsch bleibt die begründete Ausnahme.
3. Das Produkt liest OCR. Ein Scan, dem der Akzent verlorengeht, ist bei
   `fold früh` weiterhin unter der korrekten Schreibweise auffindbar, bei
   `fold spät` nicht mehr.
4. `fold spät` erzeugt in it und nl zusätzlich Terme, die keine Anfrage
   erreichen kann. Gemessen an `één`: unter A+ fällt die Form ganz weg, unter
   C+ steht `een` als Term im Index, während dieselbe Anfrage auf der Frageseite
   als Stoppwort fällt.

Die Entscheidung über diese Kette liegt als **E-17-8** im Owner-Tor der Phase
und wird nicht in diesem Bericht getroffen. Der Bericht liefert die Zahlen.

---

## 5. Die zusammengeführte Testfall-Tabelle, Stand 23.09.2026

Alle in LEX-01 benannten Fälle, mit dem gemessenen Ergebnis unter A+.

| # | Fall | Quelle | Ergebnis unter A+ | grün? |
|---|---|---|---|---|
| 1 | `información` / `informacion` | STACK, LEX-01 | beide `informacion` | ja |
| 2 | `información` / `informaciones` | PITFALLS, LEX-01 | `informacion` gegen `inform` | **nein, dokumentierter Verlust** |
| 3 | `informação` / `informacao` | STACK, LEX-01 | beide `informaca` | ja |
| 4 | `informação` / `informações` | PITFALLS, LEX-01 | `informaca` gegen `informaco` | **nein, in jeder Kette** |
| 5 | `informações` / `informacoes` | STACK | beide `informaco` | ja |
| 6 | `año` / `ano` | PITFALLS, LEX-01 | beide `ano`, bewusster Recall-Kauf | ja |
| 7 | `perché` als Stoppwort, beide Schreibweisen | FEATURES, PITFALLS, LEX-01 | beide leer | ja |
| 8 | `più` als Stoppwort, beide Schreibweisen | PITFALLS | beide leer | ja |
| 9 | `één` / `een` | FEATURES, LEX-01 | beide leer, kein Mülltoken | ja |
| 10 | akzentuierte Stoppwörter es | FEATURES, LEX-01 | 0 Lecks, akzentuiert wie flach | ja |
| 11 | akzentuierte Stoppwörter pt | FEATURES, LEX-01 | 0 Lecks | ja |
| 12 | akzentuierte Stoppwörter it | FEATURES | 0 Lecks | ja |
| 13 | `qualità` / `qualita` | neu aus dieser Messung | beide `qual` | ja |
| 14 | `città` / `citta`, `società`, `università` | STACK | je gleicher Term | ja |
| 15 | `coördinatie` / `coordinatie`, `financiën` / `financien` | FEATURES | je gleicher Term | ja |

Die beiden roten Zeilen sind nicht reparierbar, ohne einen anderen Fall rot zu
machen. Sie stehen zusammen mit den übrigen 51 Verlusten des Laufs in
`rohdaten/verluste.tsv` und sind von dort in die vier Fixtures
`backend/tests/fixtures/chain_known_losses_<code>.txt` übernommen: es 17, it 0,
nl 12, pt 24 Formpaare.

---

## 6. Nebenrechnung: die gerichtete Variante der Metrik

Die Abnahmemetrik ist ungerichtet: sie nimmt an, dass beide Schreibweisen
sowohl getippt werden als auch in Dokumenten stehen. Die gerichtete Variante
nimmt an, dass die Dokumente korrekt akzentuiert sind und nur die Anfragen
gemischt eintreffen. Sie wurde für zwei Familien nachgerechnet:

| Familie | Sprache | A+ | C+ | Lesart |
|---|---|---|---|---|
| `alemán aleman alemanes alemana alemanas` | es | 11 von 20 | 16 von 20 | Vorteil `fold spät` |
| `informação informacao informações informacoes` | pt | 4 von 8 | 4 von 8 | Unentschieden |

Das ist dieselbe Richtung, die Abschnitt 4 als spanischen Gegenbefund führt, nur
deutlicher. Sie steht hier als Nebenrechnung, damit ein späterer Leser die
Abwägung nachvollziehen kann. Abnahme ist die ungerichtete Metrik, weil das
Produkt OCR liest und ein Scan ohne Akzent genauso im Index landet wie eine
Anfrage ohne Akzent.

---

## 7. Wie der Lauf wiederholt wird

    sh scripts/dev/measure_chains.sh

Der Treiber löst die Repo-Wurzel selbst auf, prüft die Vorbedingungen mit
eigener Meldung und reicht den Rückgabecode der Sonde durch. Er schreibt nach
`docs/measurements/2026-09-analyseketten/rohdaten`, wenn kein anderes Ziel
genannt wird. Die Erwartungswerte stehen im Kopfkommentar des Treibers, samt dem
Satz, dass eine Abweichung ein Befund für diesen Bericht ist und kein Grund,
eine Datei von Hand zu bearbeiten.

---

## 8. Abweichungen dieses Laufs von den Erwartungswerten

Es gab keine. Alle vier Familienzahlen, alle vier Paarzahlen, die sieben
Kandidatenspalten je Sprache, die vier Ergänzungslisten und der Digest der
Ergänzungsliste stimmen mit den Erwartungswerten aus dem Kopfkommentar von
`scripts/dev/measure_chains.sh` überein. Die Gegenprobe der Siegerkette gegen
`snowball_analyzer()` meldete null abweichende Formen, die Dichtheitsmessung
null Lecks in beiden Schreibweisen für alle vier Sprachen.

Ein Unterschied zur Recherche ist zu benennen, er ist aber keine Abweichung der
Zahlen: die Recherche hat gegen `tantivy==0.26.2` gemessen, dieser Lauf gegen
`tantivy==0.26.0` aus `backend/uv.lock`. Die Zahlen sind identisch, was die
Aussage der Recherche stützt, dass der Patch-Sprung die Tokenisierung nicht
bewegt. Der Pin selbst wird in dieser Phase nicht angefasst; er hängt am
Owner-Tor.
