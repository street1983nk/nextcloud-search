# Deferred items, Phase 06.1

Befunde, die waehrend der Ausfuehrung dieser Phase aufgefallen sind und
ausserhalb des Plans lagen, in dem sie aufgefallen sind. Kein Fix hier, nur der
Befund und der Ort, an den er gehoert.

---

## DI-06.1-01 (gefunden in den Plaenen 06.1-01, 06.1-02 und 06.1-05, unabhaengig voneinander): der Store-Satz steht nicht mehr in der README

**Gefunden:** beim vollstaendigen Backend-Lauf vor dem Abschluss von Plan
06.1-01, also nicht durch dessen Aenderungen. Betroffen ist keine der vier
Dateien dieses Plans.

**Was:** `tests/test_store_metadata.py::test_the_measured_sentence_reads_the_same_in_all_three_places`
ist rot, mit der Meldung `README.md: does not carry the measured sentence of
05-14`. Das Gate verlangt, dass der gemessene Satz aus Plan 05-14 wortgleich in
`README.md`, `php/appinfo/info.xml` und `backend/appinfo/info.xml` steht:

> A full index and OCR run over 50,000 files and 20 GB on a 4-GB ARM64 box
> peaked at 422 MB of resident anonymous memory, under a hard 2 GB limit
> enforced by the kernel, with no OOM kill.

Die README traegt ihn nicht mehr. Der letzte Eingriff an dieser Stelle ist
`80e93c1 docs(06-11): die Zahlen des Semantiklaufs eingesetzt, RSS-Store-Zahl
ersetzt`, also die Uebernahme der Zahlen aus dem Semantiklauf; die beiden
info.xml sind dabei nicht mitgezogen worden.

**Warum nicht hier behoben:** Plan 06.1-01 schliesst DI-05-36 und fasst
`main.py`, `config.py`, `test_lifecycle.py` und `resilience.yml` an. Der
Store-Satz gehoert zu Pflichtpunkt 7 dieser Phase, und die Zahl darin steht
ausserdem unter Vorbehalt: Pflichtpunkt 1 (die zweite Modellinstanz) senkt die
Grundlast und wird auf der Box nachgemessen, danach ist der Satz ohnehin neu zu
setzen. Ihn jetzt aus der README zurueckzuschreiben hiesse, eine Zahl zu
zementieren, die diese Phase gerade veraendert.

**Wohin es gehoert:** in den Plan dieser Phase, der die Store-Texte und die
Zahlen nach der Nachmessung anfasst (Pflichtpunkt 7), zusammen mit der
Dreisprachigkeit und dem Vokabular-Gate. Das Gate bleibt bis dahin rot und ist
damit die Erinnerung an genau diesen Schritt.

**Nachtrag der Orchestrierung (Welle 1, 06.09.2026):** Alle drei Executoren der
Welle haben denselben roten Test gemeldet, jeder auf dem Basiscommit `e40dc51`
und ohne Bezug zu seinem Plan (Suitenstaende 1372 bzw. 1403 gruen, 13
uebersprungen, 1 rot). Der Test bleibt als Erinnerung rot, bis Pflichtpunkt 7
die Zahl nach der Nachmessung aus Plan 06.1-18 in allen drei Dateien neu setzt
(Plan 06.1-13 fuer die Formalien, Plan 06.1-18 Task 4 fuer die Zahl).

**ZWISCHENSTAND GESCHLOSSEN (Orchestrator, Welle 1, 06.09.2026):** Beide info.xml
tragen jetzt den 06-11-Satz in EN/DE/FR in der D-H2-Form, das Gate vergleicht
gegen den 06-11-Satz, die Suite ist gruen. Grund fuer den Eingriff ausserhalb
eines Plans: ohne ihn waere die CI der Hauptlinie bis Welle 7 rot gewesen und
haette jede echte Regression der Wellen 2 bis 6 verdeckt. Plan 06.1-18 Task 4
ersetzt die Zahl nach der Nachmessung an denselben drei Stellen plus Konstante.

---

## DI-06.1-02 (gefunden in Plan 06.1-08): ein gewoehnlicher Share auf eine Gruppe faellt weiterhin nur dem Crawl zu

**Gefunden:** beim Bau von `GroupEventListener`, also beim Schliessen von
DI-05-11.

**Was:** Der neue Listener frischt die Rechte der **Team-Folder-Mounts** einer
Gruppe auf. Ein gewoehnlicher Share, der auf eine Gruppe geht, erreicht seine
Mitglieder aber ueber den Mount-Provider von `files_sharing` und nicht ueber den
von Team Folders. Wer einer Gruppe beitritt, die einen solchen Share haelt,
findet dessen Inhalte weiterhin erst nach dem naechsten Crawl-Durchgang. Genau
dieser Fall steht woertlich im Absatz von `ShareEventListener`, den dieser Plan
fortgeschrieben hat, und deshalb steht er hier und nicht nur im Docstring.

**Warum es kein Sicherheitsbefund ist:** unveraendert die Begruendung aus
E-H3 und DI-05-11. Die Sicherheitsgrenze ist der PHP-Recheck ueber
`getUserFolder()->getFirstNodeById()`; ein veralteter Vorfilter kostet
Trefferqualitaet und Rechenzeit, nicht Vertraulichkeit.

**Warum nicht hier behoben:** die Wurzel eines `files_sharing`-Mounts kann eine
einzelne Datei sein, und `SubtreeExpandJob` hat fuer den Dateifall keinen Zweig:
`getFilesInMount` mit einer Datei als Vorfahr liefert nichts, also waere die
Einplanung ein stiller Leerlauf. Der Fall braucht entweder einen zweiten Zweig im
Listener, der eine einzelne `acl`-Zeile einreiht, oder eine Auskunft darueber, ob
die Mount-Wurzel ein Ordner ist. Beides liegt ausserhalb der `files_modified`
dieses Plans, und die `<behavior>`-Liste von 06.1-08 nennt ausdruecklich den
Team Folder.

**Wohin es gehoert:** in einen Folgeplan an der Ereigniskette, oder als benannte
Nichtabdeckung nach `docs/testing.md`, in der Form, die E-H6 fuer den Federated
Share gewaehlt hat. Ein Paritaets-Szenario dafuer waere die Spiegelung von
Szenario 10 mit einem Gruppen-Share statt einem Team Folder.
