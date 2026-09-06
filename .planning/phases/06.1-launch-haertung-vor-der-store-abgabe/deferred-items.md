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

---

## DI-06.1-03 (gefunden in Plan 06.1-09): fuenf weitere Stellen nennen noch das alte Versionsfenster

**Gefunden:** beim Nachziehen von E-H1 (`min-version` 32 auf 33). Der Plan
fuehrt fuenf Fundstellen, und die sind gesetzt. Beim Gegensuchen nach `32` im
uebrigen Baum sind funf weitere aufgetaucht, alle ausserhalb der
`files_modified` dieses Plans.

**Was, einzeln:**

- `CLAUDE.md`, drei Stellen: die Zeile "Nextcloud-Fenster" der Tabelle
  "Kernentscheidungen auf einen Blick" (**min-version 32, max-version 35**), der
  Abschnitt "Nextcloud-Versionsfenster" und die Zeile "PHP-App" der Tabelle
  "Version Compatibility" (`NC 32 bis 34 (max-version 35)`).
- `.planning/REQUIREMENTS.md`, PKG-03, im Anforderungstext und in der
  Rueckverfolgungstabelle. Beide Stellen nennt E-H1 ausdruecklich als
  dokumentarisch mitzuziehen.
- `php/lib/Service/StorageService.php:19` und `php/lib/Settings/Section.php:16`:
  beide Kommentare sagen woertlich "the app declares min-version 32". Die
  Begruendung dahinter bleibt gueltig, ein hoeherer Boden macht die dort
  gezogenen Schluesse eher staerker; falsch ist nur die genannte Zahl.
- `.github/workflows/integration.yml:111`: der Kommentar nennt "the full
  stable32 / stable33 / stable34 matrix" als das, was `deploy-harp` faehrt. Seit
  diesem Plan sind es stable33, stable34 und stable35.
- `docs/uninstall.md`, Abschnitte um Z. 65, 168, 279, 283 und 338: der
  Deinstallations-Nachweis wird dort als "vier Laeufe" beschrieben, mit
  Nextcloud 32 als Beispiel und mit dem Hinweis auf den Schalter "Daten
  loeschen" in Nextcloud 32 und 33. Die Matrix faehrt jetzt drei Laeufe.

**Warum nicht hier behoben:** keine dieser Dateien steht in den
`files_modified` von Plan 06.1-09, und zwei davon sind PHP, dessen Gates dieser
Plan nicht faehrt. Die ausgelieferte Zusage, also beide `info.xml`, die Matrix
und die README, ist vollstaendig gesetzt und durch das neue Gate in
`backend/tests/test_lockstep_versions.py` gehalten; die Liste hier ist
Dokumentation, die der Zusage hinterherlaeuft.

**Wohin es gehoert:** `CLAUDE.md` und `REQUIREMENTS.md` in die Nachfuehrung der
Orchestrierung, die die Dokumente dieser Phase ohnehin anfasst. Die beiden
PHP-Kommentare und `integration.yml` in den naechsten Plan, der die jeweilige
Datei aus einem eigenen Grund oeffnet. `docs/uninstall.md` gehoert zu
Plan 06.1-19, der die ROADMAP wegen E-H1 und E-H5 ohnehin nachzieht, und die
Zahl der Laeufe steht dort ohnehin erst nach dem naechsten gruenen CI-Lauf
wieder belegt da.

---

## DI-06.1-04 (gefunden in Plan 06.1-04): der Dauerwaechter ueber die zweite Modellinstanz fehlt weiterhin

**Was offen ist:** Plan 06.1-04 sollte in `resilience.yml` eine Obergrenze ueber
die Differenz zwischen `before-first-search` und `after-first-search` setzen. Sie
wurde nicht gesetzt, weil die Praemisse des Plans bei der Messung fiel: der
Messcontainer startet auf leerem `APP_PERSISTENT_STORAGE`, `read_side()` gibt
`None` zurueck, und die erste Suche kehrt um, bevor sie Wortliste, Automat oder
Modell erreicht. Gemessen auf amd64 am 06.09.2026: 241.172 und 503.316 Bytes in
zwei Laeufen desselben Schrittkoerpers. Eine Grenze darueber koennte fuer die
Rueckkehr der zweiten Modellinstanz nicht rot werden.

**Was geliefert wurde:** die Differenz steht ab jetzt als Zahl im Protokoll des
Schritts, damit die Reihe entsteht, aus der eine Grenze kommen kann.

**Wohin es gehoert:** eine Entscheidung zwischen drei Wegen, ausgefuehrt in
`06.1-04-SUMMARY.md`. Empfehlung dort: ein Messeinstieg, der
`embed.model.load_count()` prueft, statt einer Speichermessung.

**GESCHLOSSEN (Checkpoint-Entscheidung des Orchestrators, 06.09.2026):** Weg 2
wurde gewaehlt und in Plan 06.1-04 gebaut. `findling.tools.one_load` treibt
Indexseite, Suchseite und zweites Gleis in einem Prozess an und prueft
`load_count()` und `read_count()`; `resilience.yml` faehrt ihn im Abbild und
faerbt den Job rot, wenn ein Zaehler nicht eins ist. Die RSS-Differenz bleibt als
unbeurteilte Beobachtung im Protokoll. Rot-Faehigkeit dreifach belegt
(`backend/tests/test_one_load.py`) plus einem roten Containerlauf. Commits
0366a3b und d22c8ec. Fuer 06.1-18 bleibt nur noch die einmalige Nachmessung der
Grundlast auf der arm64-Box; der Dauerwaechter haengt nicht mehr an ihr.

---

## DI-06.1-05 (Plan 06.1-13): Der Lizenzwert `agpl` ist in der Store-XSD als veraltet gefuehrt

**Gefunden:** Plan 06.1-13, Task 2, beim Lesen der Aufzaehlung `licence` in
`info.xsd` am gehobenen Pin `eda850ba`.

**Was:** Beide `info.xml` tragen `<licence>agpl</licence>`. Die XSD nimmt den
Wert an, fuehrt ihn aber unter der Ueberschrift `Deprecated`, zusammen mit
`mit`, `mpl` und `apache`. Die nicht veralteten Schreibweisen darueber tragen
den Kommentar `Requires Nextcloud minVersion >= 31`; fuer dieses Projekt waere
das `AGPL-3.0-or-later`.

**Warum es kein Fehler von heute ist:** Der Wert ist gueltig, die Validierung
ist gruen, und das neue Gate laesst ihn ausdruecklich durch. Es ist eine
Schreibweise, die der Store selbst als ueberholt markiert, mehr nicht.

**Warum nicht hier behoben:** Die Umstellung beruehrt beide Haelften
gleichzeitig, und `php/appinfo/info.xml` steht nicht in den `files_modified`
dieses Plans. Eine Aenderung an nur einer Haelfte waere genau die Art halber
Bewegung, gegen die das Lockstep-Gate existiert. Dazu kommt die Voraussetzung
`minVersion >= 31`: sie ist mit E-H1 (min-version 33) erfuellt, aber diese
Hebung faehrt in Plan 06.1-09, nicht hier.

**Wohin es gehoert:** in den Plan, der beide `info.xml` ohnehin zusammen
anfasst (06.1-09 oder der Abschlussplan 06.1-19), oder ausdruecklich nach v1.0.
Der Aufwand ist eine Zeile je Haelfte plus ein Lauf ueber
`scripts/dev/validate_info_xml.sh`.

---

## DI-05-32 ist mit E-H2 geschlossen (Vermerk aus Plan 06.1-13)

Kein neuer Befund, sondern der Abschluss eines alten. `DI-05-32` in
`.planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md`
fragte, ob die Vokabularregel des Owners den englischen Fachausdruck in einem
Kommentar von `backend/appinfo/info.xml` trifft. Entscheidung E-H2 vom
06.09.2026 sagt nein: die Regel gilt fuer deutsche Prosa in den oeffentlichen
Texten, der englische Fachausdruck im technischen Kommentar ist ausgenommen.
Plan 06.1-13 hat die Entscheidung umgesetzt, die Ausnahme steht im Kopf des
Gates in `backend/tests/test_store_metadata.py` und wird von einem eigenen Fall
belegt. Der Kommentar in `backend/appinfo/info.xml` bleibt unveraendert. Die
Eintragung in die Deferred Items der Phase 5 steht aus, weil jene Datei nicht in
den `files_modified` dieses Plans steht.

---

## DI-06.1-06 (Plan 06.1-21, BLOCKIEREND fuer die CI nach dem Merge): die Integrationslaeufer installieren `tesseract-ocr-fra` nicht

**Gefunden:** beim Durchsehen der Sprachnennungen im Repo, waehrend Plan 06.1-21
den OCR-Standard auf `deu+eng+fra` gehoben hat.

**Was:** `.github/workflows/integration.yml` startet die ExApp nicht im gebauten
Image, sondern nativ auf dem Runner (`uv run python -m findling.main`), und
installiert die Sprachpakete dort selbst. Drei Stellen tun das, Z. 432, Z. 1076
und Z. 1843, und alle drei lauten heute:

```
sudo apt-get install -y -qq tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng tesseract-ocr-osd
```

`FINDLING_OCR_LANGUAGES` wird in dieser Datei nirgends gesetzt, der Lauf nimmt
also den eingebauten Standard. Der lautet seit Plan 06.1-21 `deu+eng+fra`, und
`tesseract -l deu+eng+fra` bricht auf einem Runner ohne `fra.traineddata` bei
jeder einzelnen Seite ab. Der OCR-Zweig der Integration wird nach dem Merge also
rot, und zwar ohne dass irgendetwas am Produkt kaputt waere: das gelieferte Image
bringt `fra` mit, nur der Runner nicht.

**Warum nicht hier gefixt:** `integration.yml` gehoert zu den `files_modified`
von Plan 06.1-06, der zeitgleich in einem eigenen Worktree laeuft. Eine Aenderung
von zwei Seiten an derselben Datei ist genau der Konflikt, den die Wellen-
Aufteilung vermeiden soll.

**Wohin es gehoert:** in denselben Merge wie Plan 06.1-21, spaetestens vor dem
naechsten gruenen CI-Lauf. Der Fix ist ein Wort in drei Zeilen: hinter
`tesseract-ocr-eng` ein `tesseract-ocr-fra`. Wer es macht, prueft danach, dass
`tesseract --list-langs` in dem Schritt darunter `fra` ausgibt.

---

## DI-06.1-07 (Plan 06.1-21): zwei weitere Stellen nennen noch zwei OCR-Sprachen

**Gefunden:** beim abschliessenden `grep` ueber `deu+eng` in Plan 06.1-21.

**Was:** zwei Stellen ausserhalb der `files_modified` behaupten weiterhin den
alten Zweiersatz:

1. `docs/performance.md:1169` zeigt die Aufrufform mit `-l deu+eng`. Das ist
   ein Messkommando aus dem Lauf von 06-11 und insofern historisch richtig, aber
   es steht dort ohne Datumsvermerk und liest sich wie die aktuelle Aufrufform.
   `docs/ocr.md` hat diesen Vermerk in Plan 06.1-21 bekommen, `docs/performance.md`
   nicht.
2. `CLAUDE.md:37` fuehrt in der Stack-Tabelle `Tesseract 5.5.0 (deu+eng+osd)`.
   Die Datei ist generiert, die Quelle ist die Stack-Recherche, also gehoert die
   Korrektur dorthin und nicht in die erzeugte Datei.

**Warum nicht hier gefixt:** beide liegen ausserhalb der `files_modified` von
Plan 06.1-21, und `docs/performance.md` ist eine Messschrift, in der eine
nebenbei geaenderte Kommandozeile den Beleg von seiner Messung trennen wuerde.

**Wohin es gehoert:** in den Abschlussplan der Phase (06.1-19) oder in den Plan,
der `docs/performance.md` nach der Box-Nachmessung 06.1-18 ohnehin anfasst. Ein
Satz mit Datum reicht in beiden Faellen.
