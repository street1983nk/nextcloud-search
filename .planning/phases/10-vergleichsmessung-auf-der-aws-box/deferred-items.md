# Deferred items, Phase 10

Befunde, die waehrend der Ausfuehrung dieser Phase aufgefallen sind und
ausserhalb des Plans lagen, in dem sie aufgefallen sind, oder die in diesem
Sinne nicht klein genug fuer eine Behebung im selben Lauf waren. Kein Fix hier,
nur der Befund und der Ort, an den er gehoert.

Klein heisst in dieser Phase: keine Aenderung an der Berechtigungskette, keine
Aenderung am Suchweg, keine Aenderung an einer Konstante, die jeden Nutzer
betrifft, und der Fix passt in denselben Lauf, in dem er gefunden wurde. Diese
Phase hat ausserdem eine harte Nebenbedingung: **jede Nacharbeit an einer
Messung kostet eine neue Anfahrt der Box, eine neue Freigabe und Geld.** Ein
Befund, der eine zweite Messung braucht, ist deshalb nie klein.

---

## DI-10-01 (gefunden in Plan 10-06, Task 3): das Lastwerkzeug zaehlt abgebrochene Containeraufrufe als Erfolge

**Gefunden:** bei der Reproduktion des Kaltstarts, im Nextcloud-Protokoll, also
neben der Messung und nicht in ihr.

**Was:** Zwischen `2026-09-10T13:51:11Z` und `13:51:42Z` stehen im
Nextcloud-Protokoll **17 abgebrochene Containeraufrufe** mit `cURL error 28`.
Dieses Fenster ist **Stufe 16 der Nebenlaeufigkeitsreihe** (13:50:59Z bis
13:51:42Z), und
`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/97-stufe-16.json`
meldet `"failures": 0` fuer 160 Anfragen.

Der Grund ist der Weg, nicht das Werkzeug allein: die OCS-Route antwortet bei
einem abgebrochenen Containeraufruf mit **HTTP 200** und einer Ergebnisgruppe
ohne Containerteil. `search_load.py` zaehlt einen Fehlschlag am Statuscode und
sieht deshalb keinen. Der Fingerabdruck steht in den Trefferzahlen:

| Stufe | Anfragen | `failures` | Treffer | Treffer je Anfrage | Abbrueche im Fenster |
|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 0 | 54 | 5,40 | 0 |
| 4 | 40 | 0 | 216 | 5,40 | 0 |
| 8 | 80 | 0 | 420 | 5,25 | 0 |
| 12 | 120 | 0 | 577 | 4,81 | 0 |
| 16 | 160 | 0 | 666 | **4,16** | **17** |

Fuer 10,6 Prozent der Anfragen der Stufe 16 hat die gemessene Antwortzeit damit
nicht die Zeit einer vollstaendigen Antwort gemessen. Die 4.446,2 ms der Stufe
16 sind eher zu guenstig als zu schlecht.

**Warum nicht hier behoben:** Ein Werkzeug, das mitten in einer laufenden
Messreihe geaendert wird, macht die Reihe unvergleichbar. Der Befund ist
ausserdem erst bei der Auswertung des Protokolls aufgefallen, also nachdem alle
fuenf Stufen gefahren waren, und eine Wiederholung der Reihe haette eine neue
Anfahrt gekostet. Die Zusage der Phase steht auf **Stufe 8**, und die Stufen 1
bis 12 tragen keinen einzigen Abbruch; der Befund beruehrt damit keine Zahl,
auf der eine Zusage ruht.

**Wohin es gehoert:** in `backend/tests/tools/search_load.py`, Phase 11. Der
Fix ist klein und benennbar: eine Antwort ohne Containerteil ist bei einer
Anfrage, die Treffer erwartet, kein Erfolg. Zwei Wege stehen offen, und der
Bericht entscheidet nicht zwischen ihnen: entweder das Werkzeug zaehlt eine
Ergebnisgruppe ohne Containerteil als Fehlschlag, oder es meldet die Trefferzahl
je Stufe als eigene Kennzahl, damit der Fingerabdruck ohne Protokoll sichtbar
ist. Belegstelle:
`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 9.3.

---

## DI-10-02 (gefunden in Plan 10-06, Task 4): der Messaufbau der Sprachfaelle trennt die Berechtigung und nicht den Index

**Gefunden:** bei der vom Owner am 10.09. entschiedenen Diagnose der vier roten
Sprachfaelle.

**Was:** `98-sprachfaelle.sh` fuehrt einen eigenen Nutzer ein, weil der
Lastkorpus dieselben Woerter traegt (Fallstrick 3 der Recherche). **Ein eigener
Nutzer trennt aber die Berechtigung und nicht den Index.** Der Vorfilter rankt
ueber den ganzen Index, der Recheck filtert erst danach auf das Erlaubte, und
bei einem Fremdbestand von 52.111 Dokumenten mit denselben Tokens bleibt nichts
uebrig: fuer `Genehmigung`, `Frist` und `Vertrag` kommt unter den ersten 2.000
Kandidaten keine Datei des fragenden Kontos vor, fuer `Bescheid` steht sie auf
Rang 1.925 von 2.000
(`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/98b-sprachfaelle-diagnose.txt`).

Die Bilanz `sprachfaelle bestanden 6 von 10` ist damit gemessen und richtig,
aber sie ist **keine Aussage ueber die Sprachverarbeitung von v1.1**. Der
Bericht fuehrt sie in Abschnitt 12 ausdruecklich als Erstmessung mit
Mess-Setup-Vorbehalt.

**Warum nicht hier behoben:** Ein tragfaehiger Aufbau braucht entweder eine
Instanz ohne Lastkorpus oder Begriffe, die im Fremdbestand nachweislich selten
sind. Beides ist eine neue Messung, also eine neue Anfahrt und eine neue
Freigabe. Die Box war zu diesem Zeitpunkt 30 Stunden gelaufen und am
Kostendeckel.

**Wohin es gehoert:** in die Haertung der Phase 11, entweder als Anpassung von
`98-sprachfaelle.sh` (Begriffe, die im Lastkorpus nicht vorkommen, gegengeprueft
vor dem Lauf) oder als eigener Lauf auf einer Instanz ohne Fremdbestand. Der
Befund **ueber das Erzeugnis**, der aus derselben Diagnose faellt, ist nicht
dieser hier, sondern DI-07-03: die Schleife holt keine zweite Runde nach.

---

## DI-10-03 (gefunden in Plan 10-07, Task 2): die Zahlen der Kernaussage fehlen in README.md und docs/store-listing.md

**Gefunden:** beim Nachziehen der Projektdokumente nach dem Messbericht.

**Was:** `README.md` und `docs/store-listing.md` sind nach aussen sichtbarer
Text und tragen die Zahlen des v1.0-Standes. Die Vergleichsmessung liefert die
Zahlen des v1.1-Standes: Grundlast 103,2 MB statt 691,8 MB, anon-Spitze
1.764,2 MB unter einer harten Grenze von 2 GiB, alle drei Schadenszaehler auf
null, acht gleichzeitige Suchende innerhalb des Budgets von 2,5 Sekunden.

**Warum nicht hier behoben:** die Kurztext-Regel des Owners vom 07.09.2026
verlangt, dass der Entwurf jedes nach aussen sichtbaren Textes **vor einem
Release** dem Owner gezeigt wird, und der Store-Text reist unveraenderlich mit
dem Release. Zwei Textrunden statt einer sind teurer fuer den Owner und
erzeugen zwei Staende desselben Textes. Ein Messbericht darf lang sein, ein
Store-Text nicht; die Uebersetzung von einem in den anderen ist eine eigene
Arbeit.

**Wohin es gehoert:** **Phase 11, REL-01**, zusammen mit der
Store-Text-Abnahme, als **eine** Textrunde. Der Checkpoint des Plans 10-07 hat
dem Owner genau diese Frage vorgelegt.

---

## DI-10-04 (gefunden in Plan 10-06, Task 1): die Ursache der Mehrlaufzeit ist eingegrenzt und nicht bewiesen

**Gefunden:** beim Auswerten von Laufzeit und Durchsatz nach dem Volllauf.

**Was:** Der Lauf brauchte **26 h 37 min** gegen 18 h 56 min in 06-11, also
plus 40,6 Prozent bei einem Mehrbestand von 0,29 Prozent, und liegt damit ueber
der Owner-Erwartung von 22 bis 26 Stunden Gesamtlaufzeit. Zwei Kandidaten stehen
nebeneinander, und die Daten entscheiden nicht zwischen ihnen
(`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/00-ende.txt`):

- **Kandidat 1, die Kopplung der Spuren.** Beide Spuren wurden gleichzeitig und
  um denselben Faktor langsamer (Indexierung minus 30,9 Prozent, Einbettung
  minus 24,4 Prozent), der Durchsatz war ueber 22 Stunden auf einer Geraden bei
  34 je Minute, und der Nachlauf mit rund 170 Dokumenten je Minute, der in 06-11
  die letzten 52 Minuten trug, kommt nicht vor. Dieser Kandidat wird von den
  Daten gestuetzt.
- **Kandidat 2, die Zulauf-Luecken** aus Plan 10-05 (`vorrat=0` in 62 von 325
  Lesungen). Er erklaert eine Wartezeit, aber nicht, warum beide Spuren im
  Gleichschritt langsamer wurden.

Speicherdruck ist als Erklaerung **ausgeschlossen**: er wuerde mit der Zeit
wachsen, und der Durchsatz faellt erst im Auslauf.

**Warum nicht hier behoben:** Welcher der beiden traegt, entscheidet eine
Messung, die kein Plan dieser Phase vorsieht: ein Lauf, der die Einbettung erst
nach der Indexierung anstoesst, oder eine Instrumentierung, die die Wartezeit
des Zulaufs mitschreibt. Beides ist eine neue Anfahrt.

**Wohin es gehoert:** Phase 11 oder spaeter, als Frage an den Durchsatz und
nicht an die Speicheraussage. Sie beruehrt kein Erfolgskriterium der Phase 10;
die Laufzeit ist als Verschlechterung benannt
(`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 19.2).

---

## DI-10-05 (gefunden in Plan 10-03, Task 1, bestaetigt in Plan 10-06): der aufgeschriebene Digest von `:dev` haelt nicht

**Gefunden:** beim Abbildwechsel auf der Box, vor dem Indexaufbau.

**Was:** `92-wechsel.sh` schreibt `digest-gleich nein`. Plan 10-02 hatte
`sha256:eed6a5fc...` (Manifestindex) und `sha256:ae58d930...` (arm64-Haelfte)
aufgeschrieben, gemessen wurde `sha256:78ab61d8...`. Der Grund steht in der
Rohdatei selbst: `:dev` ist ein wandernder Zeiger, und der Pfadfilter von
`docker.yml` greift nach `backend/**`, also verschiebt ein Commit, der nur eine
Testdatei hinzufuegt, diese Zeichenkette, ohne das Abbild inhaltlich zu aendern.

**Warum nicht hier behoben:** Der Befund hat den Lauf nicht aufgehalten, weil
die Feststellung, die entscheidet, der **Baumhash** ist, und der stimmt
(`baumhash-gleich ja`, 54 Dateien, identisch in Abbild und Arbeitsbaum). Ein
Wechsel auf unbewegliche Tags oder auf ein Pinnen per Digest ist eine Aenderung
an der Auslieferungskette und gehoert nicht in einen Messplan.

**Wohin es gehoert:** Phase 11, in die Haertung der Auslieferung. Die Frage
lautet: soll ein Messlauf gegen `:dev` pruefen duerfen, oder muss er gegen einen
unbeweglichen Tag laufen? Solange die Antwort offen ist, bleibt der Baumhash der
Beweis und der Digest die Notiz. Belegstelle:
`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitte 1 und
19.11.

---

## Geprueft und ausdruecklich kein Befund

Diese Kandidaten sind geprueft worden, weil sie sich aus Plan 10-07 anboten, und
sie sind **kein** Eintrag:

- **Die Entscheidung ueber `REQUEST_TIMEOUT_SECONDS`.** Sie gehoert nicht hier
  hin, weil sie ein Eintrag der Phase 7 ist: **DI-07-02** traegt die gemessenen
  Zahlen, ist nicht geschlossen und ist mit Zahl und Folgesatz an Phase 11
  uebergeben. Ein zweiter Eintrag an zweiter Stelle waere genau der Widerspruch,
  den die Audits dieses Projekts sonst aufschreiben.
- **Die Rundenzaehlung des Rechteabgleichs.** Ebenfalls Phase 7,
  **DI-07-03**: der Messteil ist mit beiden Zahlen geschlossen, die Frage an den
  Rechteabgleich ist an Phase 11 uebergeben.
- **Die fehlende Aktivierungsspitze der Einbettung als eigene Zahl** (A5 der
  Phase 6) und die **amd64-Entsprechung dieses Laufs**. Beide sind im Bericht in
  Abschnitt 16 als nicht abgedeckt benannt und waren nie Gegenstand eines Plans
  dieser Phase. Sie sind Fehlstellen mit Namen und keine Befunde ausserhalb
  eines Plans.
- **Der Abbau der Box.** Kein Befund, sondern eine Entscheidung des Owners vom
  10.09.2026 ("NUR ANHALTEN, kein Abbau. Abbau ist ein eigener Entscheid in
  Phase 11."). Sie steht in `docs/performance.md` unter "Der vierte Verbleib"
  und braucht keinen Eintrag hier.
