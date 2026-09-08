# Rezept A, Fall fuer Fall gemessen, 08.09.2026

Dieser Bericht ist die Messgrundlage der Phase 8. Jede spaetere Aussage dieser
Phase ueber Token soll eine Zeile in `rohdaten/tokens-rezept-a.tsv` zitieren
koennen statt geraten zu werden, und die Fixture der Python-Suite soll ab jetzt
reproduzierbar aus der echten Liste entstehen statt einmalig von Hand.

Gemessen wurde mit `scripts/dev/measure_compounds.sh`, das
`scripts/dev/compound_probe.py` in einem Wegwerf-Container faehrt. Die Sonde
baut keine eigene Filterkette: sie ruft `load_constituents` und
`german_analyzer` aus dem ausgelieferten Paket, damit der Bericht das Produkt
misst und nicht sich selbst.

---

## 1. Die Umgebung, und der Beweis des gemessenen Standes

| Was | Wert |
|---|---|
| Datum des Laufs | 2026-09-08 |
| Abbild | `python:3.13-slim-trixie`, dasselbe Basisabbild, auf dem die ExApp ausgeliefert wird |
| Wortliste | Debian-Paket `wngerman=20161207-15`, hart gepinnt im Messskript |
| Suchbibliothek | `tantivy==0.26.0`, die Fassung aus `backend/uv.lock` |
| Quelle | `/usr/share/dict/ngerman`, **356010** Zeilen |
| Liste nach Rezept A | **276496** Eintraege |
| `wordlist_hash` der gefilterten Liste | `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` |
| Faelle in der Eingabeliste | 48 |
| Faelle mit mehr als einem Token | 21 |
| Faelle mit genau einem Token | 27 |
| Faelle mit leerer Tokenliste | 0 |
| Eintraege der Fixture-Teilmenge | 194 |

Die Faelle 47 und 48 sind der Nachtrag vom Audit der Phase 8, siehe Abschnitt
5.1. Der Lauf ist derselbe Lauf: gleiches Abbild, gleiche Pins, gleicher
`wordlist_hash`, nur zwei Zeilen mehr in der Eingabeliste. Die Teilmenge blieb
dabei unveraendert bei 194 Eintraegen, weil beide neuen Woerter nur Teilketten
enthalten, die schon vorher aus anderen Faellen in die Teilmenge kamen.

Eingabe war `backend/tests/fixtures/compound_cases_de.txt`, eine Zeile je Wort.
Die Rohdaten liegen unveraendert in `rohdaten/`, nichts davon ist von Hand
nachbearbeitet.

## 2. Gegenprobe gegen die drei Zahlen der Doku

`docs/german-analyzer.md`, Abschnitt "Measured numbers", nennt drei Zahlen fuer
die Variante `full`. Alle drei kommen in diesem Lauf unveraendert wieder.

| Zahl | Doku | Dieser Lauf | Befund |
|---|---|---|---|
| Zeilen der Quelle | 356010 | 356010 | gleich |
| Eintraege nach Rezept A | 276496 | 276496 | gleich |
| SHA-256 der gefilterten Liste | `b1f6...8dde0` | `b1f6...8dde0` | gleich |

**Keine Abweichung.** Der Digest ist der wichtigste der drei: er ist die Marke,
an der ein Index erkennt, dass sich die Tokenisierung geaendert hat. Dass er
byteweise derselbe ist, heisst, dass dieser Bericht ueber genau die Liste redet,
mit der der bestehende Bestand indexiert wurde, und dass die Phase bis hierher
keinen Reindex ausgeloest hat.

Laufzeiten und Speicherzahlen stehen hier bewusst nicht: sie sind in
`docs/german-analyzer.md` gemessen und haengen an der Maschine, waehrend Token
und Digest an der Liste haengen.

## 3. Die vollstaendige Falltabelle

`in_ngerman` ist 1, wenn das Wort selbst als Zeile in `/usr/share/dict/ngerman`
steht. `entry_in_list` ist 1, wenn seine Kleinschreibung nach der Filterung ein
Eintrag der Konstituentenliste ist. Die zweite Spalte ist die entscheidende:
**ein Eintrag wird nie zerlegt.** Steht das Wort selbst in der Liste, ist jede
Erwartung an eine Zerlegung von vornherein unerfuellbar, und zwar unabhaengig
davon, wie plausibel der Fall klingt.

### 3.1 Zerfaellt (21 der 48 Eingaben)

Die 21 dieser Ueberschrift sind **nicht** die 21 aus Abschnitt 4. Hier stehen
die Eingaben dieses Laufs, die mehr als ein Token liefern
(`kennzahlen.txt: cases_more_than_one_token=21`); dort steht die Waechtertabelle
`COMPOUNDS` aus `backend/tests/test_analyzer.py`, die ebenfalls 21 Zeilen hat und
eine andere Menge ist. Dass beide Zahlen gleich sind, ist Zufall und war die
Falle, ueber die Befund M-04 des Audits gestolpert ist.

| Wort | Zeichen | in_ngerman | entry_in_list | Token |
|---|---|---|---|---|
| Grundstücksverkehrsgenehmigung | 30 | 0 | 0 | grundstuck, verkehr, genehm |
| Kündigungsfrist | 15 | 1 | 0 | kundig, frist |
| Sitzungsvorlage | 15 | 0 | 0 | sitzung, vorlag |
| Haushaltssatzung | 16 | 0 | 0 | haushalt, satzung |
| Jahresabschluss | 15 | 1 | 0 | jahr, abschluss |
| Betriebskostenabrechnung | 24 | 0 | 0 | betriebskost, abrechn |
| Krankenversicherung | 19 | 1 | 0 | krank, versicher |
| Rechnungsnummer | 15 | 0 | 0 | rechnung, numm |
| Datenschutzgrundverordnung | 26 | 0 | 0 | datenschutz, grund, verordn |
| Bundesausbildungsförderungsgesetz | 33 | 1 | 0 | bund, ausbild, forder, gesetz |
| Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz | 63 | 0 | 0 | rindfleisch, etikettier, uberwach, aufgab, ubertrag, gesetz |
| Dampfschifffahrt | 16 | 1 | 0 | dampfschiff, fahrt |
| Aufenthaltserlaubnis | 20 | 1 | 0 | aufenthalt, erlaubnis |
| Gewerbeanmeldung | 16 | 0 | 0 | gewerb, anmeld |
| Pachtvereinbarung | 17 | 0 | 0 | pacht, vereinbar |
| Übermittlungsprotokoll | 22 | 0 | 0 | ubermittl, protokoll |
| Zahlungserinnerung | 18 | 0 | 0 | zahlung, erinner |
| Grundbuchsauszug | 16 | 0 | 0 | grundbuch, auszug |
| Ersatzabgabe | 12 | 0 | 0 | ersatz, abgab |
| Sperrmüllabfuhr | 15 | 0 | 0 | sperrmull, abfuhr |
| Rechtsmittelbelehrung | 21 | 0 | 0 | rechtsmittel, belehr |

Auffaellig und leicht zu uebersehen: `in_ngerman` ist bei sechs dieser Woerter
1, `entry_in_list` aber 0. Das ist kein Widerspruch, sondern das obere Ende des
Fensters bei MAX_LEN = 14. `Kündigungsfrist` steht in der Rechtschreibliste,
faellt aber mit fuenfzehn Zeichen aus dem Fenster und wird deshalb nie ein
Eintrag. Genau dieses obere Ende ist der Grund, warum das Wort ueber `Frist`
auffindbar ist.

Kein einziger Fall hat eine leere Tokenliste. Das ist die Stelle, an der
`remove_long` hinter dem Splitter sitzt und nicht davor: das 63 Zeichen lange
Wort kommt mit sechs Token durch, waehrend es bei umgekehrter Reihenfolge
vollstaendig aus dem Index fiele.

### 3.2 Zerfaellt nicht (27 der 48 Eingaben)

| Wort | Zeichen | in_ngerman | entry_in_list | Token |
|---|---|---|---|---|
| Mietvertrag | 11 | 1 | 1 | mietvertrag |
| Bebauungsplan | 13 | 1 | 1 | bebauungsplan |
| Baugenehmigung | 14 | 1 | 1 | baugenehm |
| Bauantrag | 9 | 1 | 1 | bauantrag |
| Baukosten | 9 | 0 | 0 | baukost |
| Arbeitsvertrag | 14 | 1 | 1 | arbeitsvertrag |
| Steuerbescheid | 14 | 1 | 1 | steuerbescheid |
| Grundstuecksverkehrsgenehmigung | 31 | 0 | 0 | grundstuecksverkehrsgenehm |
| Information | 11 | 1 | 1 | information |
| Vertrag | 7 | 1 | 1 | vertrag |
| Rechnung | 8 | 1 | 1 | rechnung |
| Sitzung | 7 | 1 | 1 | sitzung |
| Kunde | 5 | 1 | 1 | kund |
| Formular | 8 | 1 | 1 | formular |
| Termin | 6 | 1 | 1 | termin |
| Ordnung | 7 | 1 | 1 | ordnung |
| Beamter | 7 | 1 | 1 | beamt |
| Genehmigung | 11 | 1 | 1 | genehm |
| Vereinbarung | 12 | 1 | 1 | vereinbar |
| Protokoll | 9 | 1 | 1 | protokoll |
| Erinnerung | 10 | 1 | 1 | erinner |
| Auszug | 6 | 1 | 1 | auszug |
| Abgabe | 6 | 1 | 1 | abgab |
| Belehrung | 9 | 1 | 1 | belehr |
| Abfuhr | 6 | 1 | 1 | abfuhr |
| Verkehr | 7 | 1 | 1 | verkehr |
| Ubermittlungsprotokoll | 22 | 0 | 0 | ubermittlungsprotokoll |

Diese Tabelle enthaelt vier Gruppen, die man nicht verwechseln darf.

**Die zehn Alltagswoerter** von `Information` bis `Genehmigung` und die sieben
Suchbegriffe von `Vereinbarung` bis `Abfuhr` **sollen** hier stehen. Ein Rezept,
das eines von ihnen zerlegt, erzeugt Unsinnsterme statt besserer Ausbeute. Die
Praezision von Rezept A ist in diesem Lauf einwandfrei.

**Die sieben Verwaltungskomposita** von `Mietvertrag` bis `Steuerbescheid` sind
der Verlust. Zwei davon sind in `docs/german-analyzer.md` bereits als Grenze
dokumentiert, fuenf nicht.

**Die zwei Nachtragsfaelle** `Verkehr` und `Ubermittlungsprotokoll` stehen hier,
weil `backend/tests/test_corpus_terms.py` Behauptungen ueber genau diese beiden
Woerter aufstellt und der Audit der Phase 8 diese Behauptungen ohne Messzeile
vorgefunden hat. Siehe Abschnitt 5.1.

**Drei Sonderfaelle** stehen in dieser Tabelle, obwohl sie keinen Listeneintrag
bilden:

`Baukosten` hat neun Zeichen, steht **nicht** in `ngerman` und ist **kein**
Listeneintrag, bleibt aber trotzdem ein einziger Token. Der Grund ist die
Untergrenze: `bau` hat drei Zeichen und liegt unter MIN_LEN = 4, also fehlt dem
Splitter der erste Teil und die Zerlegung findet keinen vollstaendigen Weg durch
das Wort. Das ist der Beleg dafuer, dass `entry_in_list` allein den Fall nicht
erklaert und die Untergrenze eine zweite, unabhaengige Sperre ist.

`Grundstuecksverkehrsgenehmigung`, die ASCII-Transkription mit ausgeschriebenen
Umlauten, bleibt ebenfalls ein einziger Token, waehrend die Fassung mit echten
Umlauten in drei zerfaellt. Die Konstituentenliste traegt ihre Umlaute, die
Index-Seite bildet keine Umlautvarianten, und ein Wort mit ausgeschriebenen
Umlauten trifft deshalb keinen einzigen Eintrag. Fuer deutsche Altbestaende und
fuer OCR-Laeufe mit verlorenen Umlautpunkten ist das eine reale Luecke. Sie
gehoert entweder als Testfall oder als benannter Grenzfall in die Doku; dieser
Bericht stellt nur fest, dass sie gemessen ist.

`Ubermittlungsprotokoll`, die Fassung ohne die zwei Punkte ueber dem grossen
Buchstaben, ist derselbe Fall an einer zweiten Stelle und traegt deshalb ein
eigenes Gewicht: es ist nicht eine Transkription, die jemand tippt, sondern das,
was die OCR-Engine des Abbilds von der fetten Ueberschrift in
`19-uebermittlung.tif` wirklich liest (gemessen am 01.09.2026, festgehalten in
`docs/ocr.md`). Die Fassung mit Umlaut zerfaellt in `ubermittl, protokoll`, die
gelesene bleibt ein Token von 22 Zeichen. Genau deshalb ist `Protokoll` kein
CI-Sprachfall: der Index bekommt die gelesene Fassung, und eine Suche nach dem
zweiten Teil faende nichts.

## 4. Warum Erfolgskriterium 1 im Wortlaut nicht baubar ist

Erfolgskriterium 1 der Phase 8 lautet: "Ein Nutzer sucht 'Genehmigung' und
findet Dokumente, in denen nur 'Baugenehmigung' steht." Die Begruendungskette
dagegen hat drei Glieder, und alle drei sind gemessen.

**Erstens: `Baugenehmigung` hat 14 Zeichen und liegt damit im Fenster.** Die
Zeile dieses Laufs:

```
Baugenehmigung	14	1	1	baugenehm
```

`in_ngerman` = 1, `entry_in_list` = 1. Das Wort steht selbst in der
Rechtschreibliste, liegt zwischen MIN_LEN = 4 und MAX_LEN = 14 und wird deshalb
selbst ein Eintrag der Konstituentenliste. Ein Eintrag wird nie zerlegt, weil
der Splitter den laengsten Treffer von links nimmt. Das Ergebnis ist ein
einziger Token, der gestemmte Ganzwortstamm `baugenehm`.

**Zweitens: Der Suchbegriff erzeugt einen anderen Term.** `Genehmigung` steht
mit elf Zeichen ebenfalls in der Liste und ergibt `genehm`. Die beiden Terme
`baugenehm` und `genehm` teilen sich nichts; die Suche kann den Treffer nicht
finden, und zwar auf beiden Seiten mit derselben, korrekt arbeitenden Kette.

**Drittens: Den Eintrag zu entfernen hilft nicht.** Die Recherche hat die drei
moeglichen Listenzustaende in derselben Umgebung durchgemessen
(`.planning/phases/08-deutsche-komposita-ohne-behelf/08-RESEARCH.md`, Abschnitt
"Die zentrale Messung"; dieser Lauf misst ausschliesslich das ausgelieferte
Rezept A und bestaetigt dessen Zeile, die dritte der drei):

```
Liste ohne "bau", ohne "baugenehmigung":  Baugenehmigung -> ['baugenehmigung']
Liste mit  "bau", ohne "baugenehmigung":  Baugenehmigung -> ['bau', 'genehmigung']
Liste mit  "bau", mit  "baugenehmigung":  Baugenehmigung -> ['baugenehmigung']
```

Nimmt man `baugenehmigung` aus der Liste, scheitert die Zerlegung weiter, weil
`bau` drei Zeichen hat und durch MIN_LEN = 4 ausgeschlossen ist. Erst beide
Aenderungen zusammen, Untergrenze auf 3 **und** Entfernen der selbst zerlegbaren
Eintraege, loesen den Fall. Genau diese Kombination ist Rezept A4, und sie ist
netto schlechter: `Sitzungsvorlage` zerfaellt dann nicht mehr,
`Bundesausbildungsförderungsgesetz` wird zu `bund, sau, bildung, ...`, und das
63 Zeichen lange Wort ergibt die leere Tokenliste, faellt also vollstaendig aus
dem Index.

Die Reichweite: von den **21 Verwaltungskomposita der Waechtertabelle**
`COMPOUNDS` in `backend/tests/test_analyzer.py` zerfallen sieben nicht. Diese 21
sind 16 aus der Recherche der Phase 2 (die 14 zerfallenden plus `Mietvertrag`
und `Bebauungsplan`, beide seit damals dokumentiert) und 5 aus der Recherche
dieser Phase (`Baugenehmigung`, `Bauantrag`, `Baukosten`, `Arbeitsvertrag`,
`Steuerbescheid`). Sie sind nicht dieselbe Menge wie die 21 aus Abschnitt 3.1,
die nur zufaellig ebenso gross ist.

Die Doku spricht von "14 von 16", aber ihre sechzehn sind ueberwiegend die
langen, seltenen Woerter. Die kurzen, haeufigen sind die, die Nutzer tippen, und
genau die stehen mit hoher Wahrscheinlichkeit selbst in `ngerman`; genau sie
sind auch die fuenf, die diese Phase neu dazugestellt hat.

Bemerkenswert und in `docs/german-analyzer.md` festzuhalten: **in keiner der
gemessenen Varianten zerfaellt eines der zehn Alltagswoerter.** Ein Test, der
nur diese zehn prueft, winkt jede der Verschlechterungen durch.

## 5. Kandidaten fuer neue CI-Sprachfaelle

Sieben Komposita, die heute zerfallen und in einer Datei des Referenzkorpus
stehen. Der Suchbegriff ist jeweils der zweite Konstituent, also die Form, die
ein Nutzer wirklich tippt. Die Spalte "Term des Suchbegriffs" nennt den Token,
den die Query-Seite erzeugt; er muss mit einem Token der Index-Seite
uebereinstimmen, sonst ist der Fall nicht baubar.

| Kompositum | Gemessene Token | Suchbegriff | Term des Suchbegriffs | Korpusdatei |
|---|---|---|---|---|
| Pachtvereinbarung | pacht, vereinbar | Vereinbarung | vereinbar | `testdata/corpus/14-pacht-mit-anhang.pdf` |
| Übermittlungsprotokoll | ubermittl, protokoll | Protokoll | protokoll | `testdata/corpus/19-uebermittlung.tif` |
| Zahlungserinnerung | zahlung, erinner | Erinnerung | erinner | `testdata/corpus/30-nur-ein-bild.pdf` |
| Grundbuchsauszug | grundbuch, auszug | Auszug | auszug | `testdata/corpus/16-oesterreich-mitteilung.pdf` |
| Ersatzabgabe | ersatz, abgab | Abgabe | abgab | `testdata/corpus/15-schweiz-baubewilligung.pdf` |
| Sperrmüllabfuhr | sperrmull, abfuhr | Abfuhr | abfuhr | `testdata/corpus/18-aushang.png` |
| Rechtsmittelbelehrung | rechtsmittel, belehr | Belehrung | belehr | `testdata/corpus/15-schweiz-baubewilligung.pdf` |

Alle sieben Paare passen: der zweite Token des Kompositums ist byteweise der
Token des Suchbegriffs. Die Zuordnung zur Korpusdatei stammt aus
`testdata/CORPUS.md`, Spalte "The one term that stands only here", und ist fuer
die vier mehrseitigen OCR-Dateien zusaetzlich gegen `testdata/corpus-truth.json`
geprueft.

Drei Befunde, die der Plan fuer die CI-Faelle beachten muss:

**Befund 1: `Abgabe` trifft zwei Dateien.** `15-schweiz-baubewilligung.pdf`
traegt `Ersatzabgabe`, `16-oesterreich-mitteilung.pdf` traegt
`Verwaltungsabgabe`. Beide zerfallen und liefern den Term `abgab`. Ein
CI-Sprachfall, der auf genau einen Treffer prueft, ist mit diesem Suchbegriff
nicht baubar, ohne entweder die Trefferzahl auf zwei zu stellen oder den Fall
ueber `Ersatz` statt `Abgabe` zu fuehren. Der Korpus-Waechter in
`scripts/dev/build_corpus.py` prueft die Einmaligkeit der Terme aus der zweiten
Tabelle von `CORPUS.md`, und `Abgabe` steht dort nicht als eigener Term, deshalb
ist das kein Bruch einer bestehenden Zusage, sondern eine Falle fuer den naechsten
Plan.

**Befund 2: `Rechtsmittelbelehrung` steht nicht in der Einmaligkeits-Tabelle.**
Das Wort steht im Text von `15-schweiz-baubewilligung.pdf`, aber nicht in der
Spalte "The one term that stands only here" von `CORPUS.md`. Gegen
`corpus-truth.json` geprueft steht es tatsaechlich nur in dieser einen Datei,
und `Belehrung` ebenfalls. Wer daraus einen CI-Fall macht, sollte den Term in
`CORPUS.md` nachtragen, damit der Waechter ihn ab dann mitschuetzt.

**Befund 3: Die Fallliste traegt `Abfuhr`, obwohl der Plan sechs Suchbegriffe
nennt.** Der Plan zaehlt sieben Kandidaten und sechs Suchbegriffe auf; fuer
`Sperrmüllabfuhr` fehlte der Suchbegriff. Ohne ihn haette der siebte Kandidat
keine zitierbare Zeile in `tokens-rezept-a.tsv`, was dem erklaerten Zweck dieser
Messung widerspricht. `Abfuhr` steht deshalb als 46. Fall in der Eingabeliste,
gemessen wie alle anderen.

Fuer alle sieben gilt: keiner von ihnen ist ein Listeneintrag, keiner liegt
unter MIN_LEN, und keiner hat die Falle aus Abschnitt 4. Sie sind die Faelle,
die gemessen halten.

### 5.1 Nachtrag vom 08.09.2026: die Faelle 47 und 48

Der Audit der Phase 8 (Befund M-07) hat zwei Behauptungen in
`backend/tests/test_corpus_terms.py` gefunden, die ueber Woerter sprechen, die
in dieser Messung nicht vorkamen. Eine Behauptung ueber ein nie gemessenes Wort
ist eine Behauptung ueber die Fixture und nicht ueber das Produkt, also wurden
die zwei Woerter nachgemessen statt umformuliert.

| Fall | Wort | Warum das Modul darueber redet |
|---|---|---|
| 47 | `Verkehr` | Abgelehnter CI-Kandidat: `Grundstuecksverkehrsgenehmigung` steht in `09-bescheid.pdf`, `Parteienverkehr` in der oesterreichischen Mitteilung. Das Modul behauptet, dass er das Token-Gatter passiert und am Buchstabengatter scheitert. |
| 48 | `Ubermittlungsprotokoll` | Was tesseract von der Ueberschrift in `19-uebermittlung.tif` wirklich liest. Das Modul behauptet, dass diese Fassung ein einziger Token bleibt, und darauf beruht die Entscheidung, `Protokoll` **nicht** als CI-Sprachfall zu bauen. |

Gemessen mit demselben Skript, demselben Abbild und denselben Pins:

```
compound_probe: /opt/findling/against.txt tokenises like the full list, 223 entries
compound_probe: 48 cases, 276496 entries, 194 in the subset
```

```
Verkehr	7	1	1	verkehr
Ubermittlungsprotokoll	22	0	0	ubermittlungsprotokoll
```

Beide Behauptungen halten. `Verkehr` ist Listeneintrag und bleibt ein Token,
`Ubermittlungsprotokoll` ist kein Listeneintrag, steht auch nicht in `ngerman`
und bleibt trotzdem ein Token von 22 Zeichen, weil die Liste ihre Umlaute
behaelt. Der `wordlist_hash` ist unveraendert, die Fixture-Teilmenge blieb bei
194 Eintraegen, und `cases_more_than_one_token` blieb bei 21: die zwei neuen
Faelle zerfallen nicht und verschieben deshalb keine der Aussagen der
Abschnitte 3 und 4.

Ein Waechter haelt das ab jetzt fest:
`test_every_word_this_module_claims_about_was_measured` in
`backend/tests/test_corpus_terms.py` prueft jedes Wort, ueber das das Modul eine
Aussage macht, gegen `fixtures/compound_cases_de.txt`. Der Zwilling dazu in
`test_analyzer.py` gab es schon; im Modul, dessen Aussagen direkt in einen
CI-Schritt wandern, fehlte er.

## 6. Die Fixture-Teilmenge

`rohdaten/fixture-subset.txt` traegt **194 Eintraege**. Es sind genau die
Eintraege der 276496 Zeilen langen Liste, die als Teilzeichenkette in mindestens
einem der 46 kleingeschriebenen Eingabewoerter vorkommen. Ein Eintrag, der in
keiner Eingabe als Teilzeichenkette steht, kann vom Splitter nie getroffen
werden, also kann sein Wegfall kein einziges Token aendern.

Das ist die Begruendung. Der **Beweis** ist Teil des Laufs und keine Handarbeit:
die Sonde baut eine zweite Kette ueber die Teilmenge und vergleicht fuer **jede
der 46 Eingaben** die Token beider Ketten. Bei einer einzigen Abweichung
schreibt sie die betroffenen Woerter nach stderr und endet mit Rueckgabewert 1.
Dieser Lauf endete mit 0, also liefert die Teilmenge fuer jede Eingabe dieselben
Token wie die echte Liste.

Damit ist Pitfall 5 mechanisch erledigt statt durch Aufmerksamkeit: Die
bestehende Fixture `backend/tests/fixtures/constituents_de.txt` mit 172
Eintraegen ist einmalig von Hand entstanden und enthaelt zum Beispiel weder
`bau` noch `baugenehmigung`. Ab jetzt ist die Teilmenge ein Erzeugnis des
Messlaufs, und wer einen Fall hinzufuegt, laesst den Lauf neu fahren statt eine
Zeile in eine Fixture zu schreiben.

Die kuerzesten Eintraege der Teilmenge sind `n`, `s`, `en`, `er`, `es` und `ns`,
also genau die sechs Fugenelemente aus `FUGEN`. Sie sind kuerzer als MIN_LEN und
koennen nur ueber diese Konstante in die Liste kommen. Ohne sie bricht die Kette
der Treffer zwischen den Teilen, und das Kompositum bliebe ganz.

## 7. Wie der Lauf wiederholt wird

```sh
sh scripts/dev/measure_compounds.sh
```

Auf einer Windows-Maschine aus Git Bash mit `MSYS_NO_PATHCONV=1` aufrufen, sonst
verbiegt MSYS die Container-Pfade der Nur-Lese-Mounts. Ohne Docker bricht das
Skript mit derselben Meldung ab wie `scripts/dev/measure_wordlist.sh`: auf einer
Entwicklungsmaschine gibt es keine Debian-Wortliste, und eine Messung, die
stillschweigend auf eine Fixture ausweicht, misst die Fixture.

Der Lauf schreibt ausschliesslich nach
`docs/measurements/2026-09-komposita-rezept-a/rohdaten` und liest ausschliesslich
die Fallliste des Repositoriums und die Wortliste des Abbilds. Er sieht weder
`state.db` noch einen Index noch eine Nutzerdatei, kann also nichts drucken, was
Nutzerinhalt waere (T-08-01, Fortschreibung von T-02-14).
