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
