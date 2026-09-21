# Die zehn Sprachfaelle auf arm64, ohne Fremdbestand (A4)

Dieser Bericht haelt genau eine Messung fest: die zehn deutschen Sprachfaelle,
gefahren auf `ubuntu-24.04-arm` gegen eine frische Nextcloud, deren einziger
Bestand der Testkorpus ist. Er entsteht aus der Ausgabe eines einzigen Laufs,
Nummer **35586213137**, Auftrag **`index-search-e2e (sqlite, ubuntu-24.04-arm)`**
der Werkbank `integration.yml`. Keine Zahl dieses Berichts stammt aus einer
Erwartung.

**Das Ergebnis in zwei Saetzen.** Alle zehn Faelle tragen auf dieser Instanz
eine Aussage, und alle zehn sind gruen. Die fuenf Faelle, die in Phase 15
"nicht messbar" hiessen, sind es hier nicht, und der Grund ist genau der, den
der Befund L-09 benannt hat: auf dieser Instanz liegt kein Fremdbestand, in dem
die eigene Datei versinken koennte.

---

## 1. Was gemessen wurde und warum

Owner-Auflage **A4** der Phase-15-Abnahme und **Erfolgskriterium 4** derselben
Phase (Befund **L-09** des Phasenaudits) verlangen die Sprachfall-Messung ohne
Fremdbestand. In Phase 15 lief sie auf einer Box, deren Nextcloud den
Korpus-Snapshot hielt: rund 52.000 Fremddokumente mit denselben Woertern. Fuenf
der zehn Faelle bekamen dort kein Urteil, sondern die Auskunft "nicht messbar",
weil die eigene Datei in beiden Ranglisten ausserhalb der 64 Rechecks stand.
Das war keine Aussage ueber die Sprache, sondern eine ueber die Verduennung.

Entscheid **E3** der Phase 16 gibt den Weg vor: CI zuerst, Box nur bei belegtem
CI-Fehlschlag. Dieser Bericht ist der CI-Teil.

## 2. Die Bedingungen

| Posten | Wert | Herkunft in der Laufausgabe |
|---|---|---|
| Laufnummer | 35586213137 | Werkbank `integration.yml`, Anlass: Push von `845c019` auf `main` |
| Auftrag | `index-search-e2e (sqlite, ubuntu-24.04-arm)`, Auftragsnummer 106290048837 | Auftragsliste des Laufs |
| Ausgang | success, alle acht Auftraege des Laufs gruen | Auftragsliste des Laufs |
| Datum und Dauer | 2026-09-21, 09:58:38Z bis 10:02:21Z, also 3 min 43 s | Auftragsliste des Laufs |
| Maschine | `ubuntu-24.04-arm`, Abbild 20260907.118.1, Ubuntu 24.04.5, Laeufer 2.337.0 | Block "Set up job" |
| Architektur | aarch64 (arm64), Vier-Kern-Maschine der Werkbankflotte | Maschinenart des Abbilds, siehe Abschnitt 5 |
| Serverfassung | `nextcloud/server`, Zweig `stable34`, "Nextcloud was successfully installed" | Schritt "Set up the test Nextcloud ..." |
| PHP | 8.2.33, ausgeliefert ueber den eingebauten Entwicklungsserver | derselbe Schritt |
| Datenbank | sqlite | Matrixeintrag, im Schritt gedruckt statt angenommen |
| Fassung der Anwendung | 1.2.0, gelesen aus `backend/appinfo/info.xml` | "app version 1.2.0, taken from ..." |
| Baustand des Containers | Das Modellverzeichnis stammt aus dem veroeffentlichten Abbild `findling_backend:dev`; der sha256-Abgleich der `model.onnx` endete mit `OK`, also traegt die arm64-Seite des Abbilds dieselbe Datei wie die gemessene | Schritt "Take the embedding model out of the published image" |
| OCR | `tesseract 5.3.4` aus den Paketen der Maschine (nicht die 5.5.0 des ausgelieferten Abbilds, siehe Abschnitt 5) | Schritt "Install the OCR engine ..." |
| **Fremdbestand** | **`files on the instance before the corpus: 0`** | Schritt "Empty the instance of everything that is not the corpus" |
| Korpus | `testdata/corpus`, `corpus entries: 39`, rund 500 KB; der Scan meldet 39 Dateien in 5 Ordnern | Schritt "Put the reference corpus into the account of the owner" |
| Verdikte | `draining: open=0 indexed=26 skipped=7 failed=6`, danach "the queue is empty and 39 files have a verdict" | Schritt "Wait until the queue is empty ..." |
| Bilanz am Ende | "the corpus ended as 26 indexed, 7 skipped, 6 failed, 26 documents in the index" | Schritt "The verdicts of the whole corpus, counted" |
| Zweite Spur | `second track: 26 of 26 documents carry a vector` | Schritt "Wait until the second track has written its vectors" |
| Antwortzeit einer gewoehnlichen Suche | 298 ms (eine Beobachtung, keine Zusicherung; siehe Abschnitt 5) | Schritt "The ten German language cases, as the owner" |

Die Instanz wird vor dem Korpus geleert, das Skelett abgeschaltet und erst
danach der Korpus in das Konto des Eigentuemers gelegt. Die Zeile
`files on the instance before the corpus: 0` ist deshalb keine Nebenbemerkung,
sondern der Beleg fuer den Kern dieser Messung: **sie laeuft ohne
Fremdbestand.**

## 3. Die zehn Faelle

**Wie diese Zahlen entstehen, damit niemand mehr hineinliest, als da steht.**
Der Schritt stellt jede Frage ueber die gewoehnliche Nextcloud-Suchroute und
haelt die Antwort gegen zwei Zusicherungen: die Trefferzahl und den Titel des
Treffers. Eine abweichende Zahl beendet den Schritt rot, mit einer eigenen
Meldung je Fall. Der Schritt ist gruen zu Ende gelaufen, also hat jede
Zusicherung unten gehalten. Von sich aus druckt er nur eine Zeile, die
Antwortzeit des ersten Falls; die Trefferzahlen sind die zugesicherten, und was
sie belegt, ist der gruene Ausgang und keine gedruckte Zahl.

| Fall | Begriff | Erwarteter Titel | Trefferzahl | Urteil |
|---|---|---|---|---|
| 1 | `Genehmigung` | `09-bescheid.pdf` | 1 | gruen, zusaetzlich mit Textausschnitt, der das Wort traegt und keine Auszeichnung enthaelt |
| 2 | `Frist` | `10-kuendigung.docx` | 1 | gruen |
| 3 | `Mueller` | `12-aktenvermerk.txt` | 1 | gruen |
| 4 | `Vertrag` | `11-uebersicht.odt` | 1 | gruen |
| 5 | `"drei Monate"` | `10-kuendigung.docx` | 1 | gruen |
| 6 | `bescheid`, danach `bescheid -frist` | `09-bescheid.pdf` | 2, danach 1 | gruen, beide Haelften: die Kontrolle bringt zwei Dateien, der Ausschluss entfernt die richtige |
| 7 | `type:pdf bescheid` | `09-bescheid.pdf` | 1 | gruen |
| 8 | `Belehrung` | `15-schweiz-baubewilligung.pdf` | 1 | gruen, zusaetzlich mit Textausschnitt aus dem erkannten Text |
| 9 | `Auszug` | `16-oesterreich-mitteilung.pdf` | 1 | gruen |
| 10 | `Erinnerung` | `30-nur-ein-bild.pdf` | 1 | gruen |

Bilanz: **zehn von zehn gruen, null rot, null ohne Aussage.**

Die Faelle 8, 9 und 10 fragen nach Text, den es nur als Bildpunkte gibt: die
drei Dateien sind gescannte Seiten, ihr Inhalt entsteht erst im OCR-Durchlauf
dieses Laufs. Sie sind damit auch der Beleg, dass die Scan-Spur auf arm64
gelaufen ist und nicht nur die Textspur.

## 4. Die Gegenueberstellung zur Phase 15

Die Messung der Phase 15 steht in
`docs/measurements/2026-09-v12-messung/rohdaten/05-sprachfaelle.txt`. Sie
urteilte dreiwertig und las den Rang der eigenen Datei in beiden Ranglisten
gegen die Schwelle 64; ausserhalb hiess "nicht messbar" und ausdruecklich nicht
"rot". Die Messung hier urteilt zweiwertig ueber die Antwort der gewoehnlichen
Suche. Die Frage ist dieselbe, das Messwerkzeug ist es nicht, und genau deshalb
steht beides nebeneinander.

| Fall | Begriff | Phase 15 (mit Fremdbestand) | Dieser Lauf (ohne Fremdbestand) |
|---|---|---|---|
| 1 | `Genehmigung` | nicht messbar (Rang ausserhalb, 51.965 Dokumente tragen den Begriff) | **gruen** |
| 2 | `Frist` | nicht messbar (Rang ausserhalb, 51.956 Dokumente) | **gruen** |
| 3 | `Mueller` | gruen (Rang 1) | gruen |
| 4 | `Vertrag` | nicht messbar (Rang ausserhalb, 51.111 Dokumente) | **gruen** |
| 5 | `"drei Monate"` | gruen (Rang 1) | gruen |
| 6 | `bescheid` | nicht messbar (Rang ausserhalb, 51.167 Dokumente) | **gruen** |
| 7 | `type:pdf bescheid` | nicht messbar (Rang ausserhalb, 33.226 Dokumente) | **gruen** |
| 8 | `Belehrung` | gruen (Rang 1) | gruen |
| 9 | `Auszug` | gruen (Rang 1) | gruen |
| 10 | `Erinnerung` | gruen (Rang 1) | gruen |

Bilanz der Phase 15: 5 von 10 gruen, 0 rot, 5 ohne Aussage. Bilanz hier: 10 von
10 gruen, 0 rot, 0 ohne Aussage. **Alle fuenf zuvor nicht messbaren Faelle
tragen jetzt eine Aussage, und keiner von ihnen ist rot.** Damit bestaetigt
dieser Lauf auch die Begruendung der Phase 15: die fuenf Faelle scheiterten an
der Verduennung durch den Fremdbestand und an keinem Sprachbefund.

## 5. Was dieser Lauf nicht beweist

Dieser Abschnitt ist Pflicht, weil ein Ergebnis von einem fremden Maschinentyp
sonst fuer eines von der Zielhardware gehalten wird.

- **Keine echte Nextcloud mit AppAPI und HaRP.** Das Backend laeuft hier als
  gewoehnlicher Prozess auf der Maschine und nicht als Container hinter dem
  HaRP-Weg, und der Server ist der eingebaute PHP-Entwicklungsserver.
- **Keine m7g.large.** Der Laeufer ist eine Vier-Kern-Maschine derselben
  Werkbankflotte. Das ist der Vorbehalt aus 14-02, und er gilt unveraendert.
- **Keine harte Speichergrenze, keine Speicheraussage.** Auf dieser Maschine
  gibt es keine 4-GB-Grenze im Kern und keine Begrenzung eines Containers.
- **Keine Zeitaussage.** Die 298 ms des ersten Falls sind eine Beobachtung
  dieser einen Maschine an diesem einen Tag, kein Messwert einer Messreihe und
  keine Zusicherung.
- **Keine Aussage ueber das Verhalten unter Fremdbestand.** Der Verzicht auf
  Fremdbestand ist der Zweck dieser Messung, und er faellt in beide Richtungen:
  wie sich dieselben Begriffe unter 52.000 Fremddokumenten ordnen, sagt weiter
  nur die Messung der Phase 15.
- **Keine Aussage ueber Datenbankdialekte.** Der arm64-Ast faehrt sqlite; die
  drei Dialekte stehen unveraendert auf amd64 daneben.
- **Eine andere OCR-Fassung als im Auslieferungsabbild.** Hier laeuft
  `tesseract 5.3.4` aus den Paketen der Maschine, das ausgelieferte Abbild
  traegt 5.5.0. Fuer die drei gescannten Faelle heisst das: der Text wurde
  erkannt, aber nicht von der Fassung, die ein Nutzer installiert.

Was er beweist, ist die **Suchqualitaet auf arm64 gegen einen eigenen Index**,
und genau das sind die zehn Sprachfaelle.

## 6. Das Urteil zum Weg

**traegt**

Der CI-Weg nach Entscheid E3 traegt die Messung. Er liefert die Aussage, die
Auflage A4 und Erfolgskriterium 4 verlangen, zu null Kosten, wiederholbar, und
er bleibt als Gate stehen: der naechste Rueckschritt in einem der zehn Faelle
faellt kuenftig auf arm64 genauso auf wie auf amd64. Ein Fehlschlag, der die
Box-Anfahrt nach Entscheid E3 begruenden wuerde, liegt nicht vor.
