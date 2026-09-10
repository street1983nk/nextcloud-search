# Deferred items, Phase 07

Befunde, die waehrend der Ausfuehrung dieser Phase aufgefallen sind und
ausserhalb des Plans lagen, in dem sie aufgefallen sind, oder die in diesem
Sinne nicht klein genug fuer eine Behebung im selben Lauf waren. Kein Fix hier,
nur der Befund und der Ort, an den er gehoert.

Klein heisst in dieser Phase: keine Aenderung an der Berechtigungskette, keine
Aenderung am Suchweg, hoechstens eine Konstante oder ein Kommentar, und der Fix
passt in denselben Lauf, in dem er gefunden wurde.

---

## DI-07-01 (gefunden in Plan 07-02, Task 3): die amd64-Kaltstartzahl kann erst nach dem Zusammenfuehren entstehen

**GESCHLOSSEN 08.09.2026:** Erster integration.yml-Lauf auf main (34221154596) lieferte
1.299 ms (sqlite) und 1.392 ms (mysql); in docs/performance.md nachgetragen, Erfolgs-
kriterium 4 damit erfuellt. EFF-02 bleibt abgehakt, jetzt auf beiden Architekturen belegt.

**Gefunden:** beim Schreiben des Messberichts, unmittelbar nachdem der Messweg
in `.github/workflows/integration.yml` gebaut war.

**Was:** `docs/performance.md`, Abschnitt "Die amd64-Zahl: derselbe Vorgang auf
der anderen Architektur", traegt den Messweg vollstaendig, aber in der Zeile
"Gemessene Kaltstartdauer, amd64" steht "steht aus" statt einer Zahl. Erfolgs-
kriterium 4 der Phase verlangt die Zahl selbst.

**Warum nicht hier behoben:** Ein Lauf von `integration.yml` braucht einen
GitHub-Runner und laeuft erst, wenn der Zweig dieses Plans auf `main` steht. Der
Executor arbeitet in einem Worktree und pusht nicht. Eine geratene oder aus der
arm64-Zahl hochgerechnete Zahl waere schlimmer als eine leere Zeile: der ganze
Abschnitt haelt nur, weil jede Zahl darin ihre Rohdatei oder ihren Lauf nennt.

**Wohin es gehoert:** in den ersten Lauf von `integration.yml` auf `main` nach
dem Zusammenfuehren von Plan 07-02. Zu lesen ist die Protokollzeile, die mit
`cold semantic search over apache, the ocs route, the php provider and both
halves:` beginnt, im Job `index-search-e2e`, je Matrixzeile eine. Einzutragen
sind Zahl, Laufnummer, Datum und Matrixzeile in die genannte Tabellenzeile.
Solange die Zeile "steht aus" traegt, ist Erfolgskriterium 4 der Phase offen.

---

## DI-07-02 (gefunden in Plan 07-02, Task 3): die kalte Suche laeuft zuerst gegen 1,5 s und nicht gegen 2,5 s

**GEMESSEN 10.09.2026, NICHT GESCHLOSSEN, an Phase 11 uebergeben.** Die Messung,
nach der dieser Befund gefragt hat, ist gefahren: Plan 10-06 hat den Kaltstart
auf **vollem** Vektorbestand auf der Zielhardware gemessen, dazu drei
Reproduktionen und die Reihe unter Nebenlaeufigkeit. Die Marge ist negativ, also
wird der Befund ausdruecklich nicht geschlossen.

Die Zahlen, jede mit ihrer Rohdatei unter
`docs/measurements/2026-09-vergleichsmessung-m7g/`:

| Groesse | Wert | Marge zur Decke 1.500 ms | Rohdatei |
|---|---:|---:|---|
| Kaltstart, **voller** Bestand, 10.09. 14:05:17Z | **1.838,4 ms** | **minus 338,4 ms** | `rohdaten/95-spitze-nachher.txt` |
| Kaltstart, **leerer** Bestand, 09.09. | 1.550,4 ms | minus 50,4 ms | `rohdaten/95-spitze-vorher.txt` |
| Vorwert Plan 07-01 (leerer Bestand, amd64-Weg) | 1.332,1 ms | plus 167,9 ms | `docs/performance.md` |
| Reproduktion 1, `Bescheid` | 1.598 ms | minus 98 ms | `rohdaten/95b-kaltstart-reproduktion.txt` |
| Reproduktion 2, `Vertrag beenden` | 1.805 ms | minus 305 ms | dieselbe |
| Reproduktion 3, `Kuendigung` | 2.468 ms | minus 968 ms | `rohdaten/95c-kaltstart-reproduktion-teil2.txt` |

Die Reihe unter Nebenlaeufigkeit steht in `rohdaten/97-nebenlaeufigkeit.txt`:
p95 464,3 / 1.068,0 / 2.125,5 / 3.453,4 / 4.446,2 ms ueber die Stufen 1, 4, 8,
12 und 16, bei einem Gruppenbudget von 2.500 ms. Die Zusage steht auf Stufe 8,
die Reserve dort faellt von 585,0 auf 374,5 ms.

**Eine Methodik-Korrektur, ohne die keine dieser Zahlen richtig gelesen wird.**
Die gemessenen Dauern sind die Dauer der **ganzen OCS-Anfrage**; die Decke von
1.501 ms gilt nur fuer den **inneren Containeraufruf**. Diese Unterscheidung
fehlte allen bisherigen Kaltstartzahlen dieses Projekts. Daraus folgt: eine
Gesamtdauer ueber 1,5 s beweist keinen Abbruch, und eine darunter keinen
Nichtabbruch. Die drei Reproduktionen liegen ueber 1,5 s und liefern **je sechs
Treffer**, weil der Seitencache des Wirts die Modellgewichte noch hielt.

**Der Abbruch ist trotzdem belegt, und zwar genau einmal.** Um
`2026-09-10T14:05:17Z`, bei kaltem Wirtscache (letzter Start 29 Stunden zuvor),
steht im Nextcloud-Protokoll `cURL error 28: Operation timed out after 1501
milliseconds with 0 bytes received ... /exapps/findling_backend/search` und
darunter `Findling: backend unreachable`. Diese eine Anfrage brachte null
Treffer.

**Was daraus folgt, in einem Satz:** die Decke von 1,5 s haelt den Kaltstart auf
vollem Vektorbestand bei kaltem Wirtscache nicht aus, und der Nutzer sieht dann
keine Fehlermeldung, sondern eine leere Ergebnisgruppe.

**Warum der Befund trotzdem nicht hier entschieden wird:** eine hoehere Decke
gilt fuer **jeden** Containeraufruf der App, und die Unified Search wartet auf
jeden Provider. Sie laesst also jeden Nutzer bei jeder Suche laenger warten, um
einen Fall zu retten, der genau einmal je Containerstart auftritt. Die
Alternativen, die keine Konstante anfassen (Vorwaermen der Gewichte beim
Containerstart, ein eigener Weg fuer den ersten Aufruf), sind nicht gemessen.

**Wohin es gehoert: Phase 11**, in das Audit der Haertung, mit diesen Zahlen und
mit dem Bericht
`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 9.

**Gefunden:** beim Einordnen der Kaltstartdauer gegen die Decken des PHP-Wegs.

**Was:** `REQUEST_TIMEOUT_SECONDS = 1.5` in
`php/lib/Service/ExAppService.php:89` deckelt einen einzelnen Containeraufruf,
und der Kaltstartaufschlag faellt vollstaendig in genau diesen einen Aufruf: das
Laden steht unter dem Lock (`backend/src/findling/embed/model.py:369`), also
warten gleichzeitige Suchen hinter demselben Laden. Das 2.500-ms-Gruppenbudget
aus `php/lib/Search/Provider.php:57` kann einen Aufruf nur verkuerzen, nie
verlaengern. Die gemessenen 1.332,1 ms der arm64-Box lassen 167,9 ms Marge zur
kleineren Decke, nicht 1.167,9 ms zur groesseren.

**Warum nicht hier behoben:** Die Decke zu heben ist keine kleine Aenderung. Sie
gilt fuer jeden Containeraufruf der App, und die Unified Search wartet auf jeden
Provider; eine hoehere Decke laesst also alle Nutzer laenger warten, fuer einen
Fall, der bisher nur gerechnet und nicht gemessen ist. Die Entscheidung braucht
eine Messung des Kaltstarts unter Nebenlaeufigkeit auf der Zielhardware.

**Wohin es gehoert:** Phase 10. Die Rechnung, die den Bedarf begruendet, steht
in `docs/performance.md` in der Nebenlaeufigkeitstabelle des Abschnitts "Die
Grenze, an der eine kalte Suche zuerst reisst" und ist dort ausdruecklich als
Rechnung und nicht als Messreihe markiert.

---

## DI-07-03 (gefunden in Plan 07-02, Task 3): eine Suche kostet zwei Containeraufrufe, und der erste steht in einer Schleife

**MESSTEIL GESCHLOSSEN 10.09.2026.** Die Frage, wie oft die Schleife ueber
`MAX_ROUNDS = 3` mehr als eine Runde dreht und was die Runden kosten, ist auf
der Zielhardware gemessen (Plan 10-06, Schritt 12). Eine Aenderung am
Rechteabgleich ist ausdruecklich **nicht** beschlossen: er ist die
Berechtigungskette, und diese Entscheidung weist der Befund selbst Phase 11 zu.

| Fall | Runden je Suche | Containeraufrufe je Suche | Treffer | p50 | p95 | Marge zu 2.500 ms | Rohdatei |
|---|---:|---:|---:|---:|---:|---:|---|
| 1, der Alltag | **1,0** | **1,9** (10 Kandidaten-, 9 Snippetaufrufe) | 54 | 589,4 ms | **683,6 ms** | 1.816,4 ms | `rohdaten/99b-runden-alltag.txt` |
| 2, provozierter Driftfall | 1,0 | 1,0 (10 Kandidaten-, 0 Snippetaufrufe) | 0 | 444,2 ms | 681,6 ms | 1.818,4 ms | `rohdaten/99b-runden-drift.txt` |

Beide Rohdateien liegen unter
`docs/measurements/2026-09-vergleichsmessung-m7g/`.

**Wie die beiden Faelle hergestellt wurden**, weil eine Zahl aus einem
provozierten Zustand ohne diesen Satz als Alltagszahl gelesen wird:

- **Fall 1** ist das Konto, das alle Dateien besitzt, zehn Suchen, 40 geteilte
  Dateien. Der Recheck entfernt nichts, die Schleife dreht genau eine Runde.
  Gezaehlt wurden die Containeraufrufe im Protokoll (`POST /search`,
  `POST /snippets`), nicht ein abgelesener Zustand.
- **Fall 2** wurde absichtlich erzeugt: eigenes Konto `driftfall`, 20 Freigaben,
  zwei gezaehlte Poller-Durchgaenge, Kontrolle vor der Ruecknahme lieferte vier
  Treffer, dann Ruecknahme um 14:14:14Z ohne Wartezeit und sofort gefragt.
  **Der Driftfall liess sich damit nicht herstellen.** Das Skript liest
  dreiwertig, und gemessen wurde die dritte Lesart: null Treffer **und** eine
  Runde je Suche heisst, der Vorfilter wusste schon Bescheid und die Drift war
  zu kurz. **Die Alltagszahl traegt, die Driftzahl nicht.**

**Gegen die Decken:** die Aufrufdecke `REQUEST_TIMEOUT_SECONDS` = 1,5 s gilt je
Aufruf, das Gruppenbudget `BUDGET_SECONDS` = 2,5 s je Ergebnisgruppe. Bei 1,0
Runde und 1,9 Aufrufen je Suche teilen sich im Alltag nie mehr als zwei Aufrufe
dasselbe Budget, und der gemessene p95 von 683,6 ms laesst 1.816,4 ms Marge.
**Der gerechnete Worst Case von vier Aufrufen gegen ein Budget ist im Alltag
nicht eingetreten.**

**Was offen bleibt und Phase 11 gehoert**, mit einem zweiten Befund aus
demselben Lauf: die Schleife holt **keine zweite Runde nach**, auch dann nicht,
wenn der Recheck alle Kandidaten der ersten Runde verworfen hat. Auf einer
Instanz mit grossem Fremdbestand findet ein Nutzer mit wenigen Dateien seine
eigenen deshalb nicht, sobald seine Begriffe im Fremdbestand haeufig sind, und
er bekommt keine Fehlermeldung, sondern eine leere Liste. Fuer drei von vier
geprueften Begriffen kam die Datei des fragenden Kontos unter den ersten 2.000
Kandidaten nicht vor (`rohdaten/98b-sprachfaelle-diagnose.txt`). Das ist der
Befund hinter den vier roten Sprachfaellen der Vergleichsmessung, und er ist
eine Frage an den Rechteabgleich, also **Phase 11**.

**Gefunden:** beim Nachlesen der Kandidatenschleife, waehrend Befund 1
geschrieben wurde.

**Was:** `searchCandidates` wird in `php/lib/Search/Provider.php:258` innerhalb
der Schleife ueber `MAX_ROUNDS = 3` (`Provider.php:247`) gerufen, `snippets`
danach einmal (`Provider.php:411`). Die Schleife dreht mehr als eine Runde, wenn
der Rechteabgleich Treffer einer Seite entfernt und noch Recheck-Budget uebrig
ist (`Provider.php:248-258`). Eine einzige Suche kann damit vier
Containeraufrufe gegen ein Gruppenbudget von 2.500 ms setzen; jeder Aufruf
bekommt nur, was `secondsLeft($deadline)` uebrig laesst (`Provider.php:504`).

**Warum nicht hier behoben:** Die Schleife zu verkuerzen hiesse, den
Rechteabgleich anzufassen, und der ist die Berechtigungskette. Das ist per
Definition nicht klein. Ausserdem fehlt die Zahl, um die Sache ueberhaupt zu
beurteilen: wie oft die Schleife in echten Bestaenden mehr als eine Runde dreht,
ist nirgends gemessen.

**Wohin es gehoert:** Phase 10 fuer die Messung, wie oft die Schleife mehr als
eine Runde dreht und was die Runden kosten. Ergibt die Messung, dass der
Rechteabgleich selbst geaendert werden muesste, gehoert diese Entscheidung
Phase 11, denn sie ist eine Frage fuer das Audit und nicht fuer einen Messplan.

---

## DI-07-04 (gefunden in Plan 07-03, Task 1): die native arm64-Rohdatei der Feinmessung kann erst nach dem Zusammenfuehren entstehen

**GESCHLOSSEN 09.09.2026:** Erster `workflow_dispatch` von `measure.yml` auf main
(34325000302, Ast arm64 auf `ubuntu-24.04-arm`, Artefakt `welle0-arm64`) lieferte die
native Rohdatei; gemessenes Abbild
`sha256:eed6a5fcb152373e7bf6d7725da774844d4012cfe0cbe02b261f31a865e4cce3`
(Manifestindex von :dev, arm64-Hälfte
`sha256:ae58d93005dc18849c3bd128cef51bea0530c143f5719a284fd694b6f9e09d44`).
Schritt 00 fällt von 43,2 MB auf 13,0 MB, die Summe der fünf Posten liegt mit 543,7 MB
8 kB neben der groben nativen Messung aus 63-grundlast.txt statt 1,2 Prozent daneben.
Nachgezogen sind die Abschnitte 1, 2, 3 und 4 von
`docs/measurements/2026-09-grundlast-fein/README.md` und die Tabelle des Abschnitts
"Der größte Posten der Grundlast" samt einer Zeile in "Stand dieses Berichts" in
`docs/performance.md`. Die emulierte Datei ist nicht gelöscht, sondern umbenannt in
`01-grundlast-fein-arm64-emuliert.txt` und unter jeder nachgezogenen Tabelle als
Vorläufer genannt. Der Entscheid des Plans 07-03 bleibt unberührt.

**Ein Zusatz gegen die Sprachfalle:** Dieser Eintrag nennt "Abschnitt 1, 2, 4 und 7" des
Berichts. Der Bericht hat sechs Abschnitte; die vier Stellen mit arm64-Zahlen sind 1, 2,
3 und 4. Nachgezogen sind diese vier.

**Gefunden:** beim Fahren der feineren Grundlastmessung, unmittelbar nachdem der
Messschritt in `.github/workflows/measure.yml` gebaut war.

**Was:** `docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64.txt`
traegt eine Messung unter QEMU-Emulation und nicht auf nativer ARM-Hardware. Der
Kopf der Datei und Abschnitt 1 des Berichts sagen das ausdruecklich. Die
Grundlinie ist dadurch um rund 30 MB nach oben verschoben (Schritt 00: 43,2 MB
statt 13,3 MB); die Zuwaechse der fuenf gemessenen Posten liegen in der Summe
1,2 Prozent neben der nativen groben Messung derselben Schritte aus
`2026-09-nachmessung-m7g/rohdaten/63-grundlast.txt`.

**Warum nicht hier behoben:** Ein Lauf von `measure.yml` auf `ubuntu-24.04-arm`
braucht einen GitHub-Runner und einen `workflow_dispatch`, und der Zweig dieses
Plans steht noch nicht auf `main`. Der Executor arbeitet in einem Worktree und
pusht nicht. Die AWS-Box ist angehalten, ihr Datentraeger ist teilweise zerstoert
und sie gehoert Phase 10; sie wird dafuer nicht angefahren. Der Entscheid des
Plans haengt nicht daran: er faellt gegen 544,3 MB nativ gemessen auf amd64, und
die Schwelle liegt bei 100 MB.

**Wohin es gehoert:** in den ersten `workflow_dispatch` von `measure.yml` nach
dem Zusammenfuehren von Plan 07-03. Der Schritt heisst "D, the base load step by
step", er laeuft in beiden Matrixaesten aus derselben Skriptdatei, und sein
Artefakt `01-grundlast-fein-arm64.txt` ersetzt die emulierte Datei ohne weitere
Aenderung. Danach sind die arm64-Spalten in Abschnitt 1, 2, 4 und 7 des Berichts
und die arm64-Spalte in `docs/performance.md` gegen die native Datei
nachzuziehen.
