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

## DI-06.1-06 (gefunden in Plan 06.1-10): die Zahl "indexiert" der Verwaltungsseite zaehlt Grabsteine mit

**Gefunden:** beim Bau der Bedingung "der Vektorbestand ist vollstaendig".
Betroffen ist keine Datei dieses Plans, sondern die Leseseite aus Plan 06-09.

**Was:** `Store.counts()` gruppiert nach `state` ohne `deleted_at` anzusehen, und
`Store.tombstone` laesst den Verdikt-Wert stehen. Ein geloeschtes Dokument bleibt
also unter `indexed` gezaehlt und verliert im selben Aufruf seine Vektoren. Auf
der Verwaltungsseite stehen die zwei Deckungszahlen damit nach der ersten
Loeschung dauerhaft auseinander: "auffindbar nach Bedeutung" kann "indexiert"
nicht mehr einholen, und ein Verwalter liest daraus einen Rueckstand der zweiten
Spur, den es nicht gibt.

**Was in diesem Plan trotzdem geschah:** nur die Stempelbedingung wurde geheilt.
`Store.indexed_alive()` zaehlt lebende indexierte Dokumente, und der Stempel
rechnet gegen diese Zahl. Haette er gegen `counts()` gerechnet, waere die Marke
auf jeder Instanz mit einer Loeschung fuer immer ungeschrieben geblieben; ein
Testfall haelt das fest
(`test_a_deleted_document_does_not_hold_the_mark_back_for_ever`).

**Warum nicht hier behoben:** die Zahl der Verwaltungsseite zu aendern heisst,
die Leseseite aus 06-09 samt ihrer Zusicherungen und dem Gate anzufassen, das
"ein Aufruf derselben Methode mit einem anderen Zaehler" prueft. Das liegt
ausserhalb der zwei Aufgaben dieses Plans und ist keine Korrektheitsfrage,
sondern eine Anzeigefrage.

**Wohin es gehoert:** eine Entscheidung vor dem Tag oder danach. Entweder zaehlt
`counts()` fuer die Seite kuenftig lebende Zeilen (dann aendert sich auch die
Fehlerliste), oder die Seite nennt neben "indexiert" ausdruecklich, dass
geloeschte Dokumente unter ihrem letzten Verdikt weitergezaehlt werden. Die
zweite Fassung ist die billigere und die ehrlichere.
---

## DI-06.1-07 (ERLEDIGT durch 06.1-15 + 06.1-22): sechs Stellen nennen den Korpus noch mit dreiunddreissig Dateien

**Teilerledigung 07.09. (Plan 06.1-15):** docs/testing.md ist erledigt (Zahl durch
Verweis auf testdata/CORPUS.md ersetzt). Offen: docs/dev-setup.md Z. 238,
docs/ocr.md Z. 261, docs/performance.md Z. 2223, scripts/dev/build_load_corpus.py
Z. 4/11/1167.

**Gefunden:** beim Nachziehen der Zahlen fuer Task 3. Der Korpus hat mit diesem
Plan 39 Dateien statt 33, und 24 PDFs statt 19.

**Was offen ist:** Innerhalb der `files_modified` dieses Plans wurde jede Zahl
mitgezogen (`testdata/CORPUS.md`, `.github/workflows/integration.yml`).
Ausserhalb steht die alte Zahl weiter als Prosa in:

- `docs/testing.md` Z. 94, 100 und 101 ("thirty three files including twelve
  broken PDFs", und zweimal in der Begruendung des Verdikt-Zaehlers)
- `docs/dev-setup.md` Z. 238 ("33 files, the four image types")
- `docs/ocr.md` Z. 261 ("dem Referenzkorpus dieses Repositories, 33 Dateien,
  davon 19 PDFs"), wo auch die PDF-Zahl nicht mehr stimmt
- `docs/performance.md` Z. 2223 ("Korpus von 33 Dateien")
- `scripts/dev/build_load_corpus.py` Z. 4, 11 und 1167, im Docstring des
  Lastkorpus

Keine dieser Stellen wird maschinell gelesen, keine faerbt einen Lauf rot. Es
sind Saetze fuer Leser, und sie sind ab jetzt falsch.

**Warum nicht hier behoben:** Alle sechs liegen ausserhalb der `files_modified`
dieses Plans. `docs/testing.md` gehoert nach dem Wellenplan den Plaenen 06.1-15
und 06.1-19, und zwei Plaene derselben Welle teilen sich keine Datei.

**Wohin es gehoert:** in den Plan, der `docs/testing.md` ohnehin anfasst, also
06.1-15 oder 06.1-19. Die uebrigen vier Dateien sind je eine Zeile und koennen
dort mitlaufen. Empfehlung fuer die Gelegenheit: die Zahl aus
`testdata/CORPUS.md` zitieren statt sie ein siebtes Mal zu schreiben, damit die
naechste Korpuserweiterung nicht wieder sechs Stellen suchen muss.

---

## DI-06.1-08 (gefunden in Plan 06.1-06): der Deckel gegen Archivbomben zaehlt je Mitglied und nie die Summe

**Gefunden:** beim Bau der Korpusdatei `34-zip-bombe.docx`.

**Was offen ist:** `_oversized_part` in `backend/src/findling/extract/office.py`
und die gleichnamige Pruefung in `extract/odf.py` fragen
`any(info.file_size > EXTRACT_ARCHIVE_MEMBER_MAX_BYTES ...)`, also je Mitglied.
Ein Paket mit hundert Teilen von je 63 MiB kommt an dieser Pruefung vorbei. Ob
es danach wirklich schadet, haengt am Loader: python-docx liest
`word/document.xml`, python-pptx die Folien, openpyxl im Read-only-Modus zeilen-
weise. Ein Paket, dessen einzelnes gelesenes Teil unter dem Deckel bleibt, ist
also nicht automatisch gefaehrlich, aber die Aussage des Deckels ist enger als
sie klingt.

**Warum nicht hier behoben:** Das ist keine Korrektur an dieser Stelle, sondern
eine Aenderung der Semantik des Deckels (Summe statt Maximum, oder ein zweiter
Deckel daneben), mit Folgen fuer jedes gueltige grosse Dokument. Nach den
Abweichungsregeln ist das Regel 4 und braucht eine Entscheidung, keinen
Schnellschuss im Randpfad-Plan.

**Wohin es gehoert:** in das Sicherheitsaudit dieser Phase. Dort mit einer
Messung entscheiden: wie viel liest jeder der drei Loader tatsaechlich, und
reicht ein Summendeckel oder braucht es einen Deckel auf der Gesamtgroesse des
entpackten Pakets.
---

## DI-06.1-09 (Plan 06.1-21, ERLEDIGT im Merge-Commit vom 06.09.): die Integrationslaeufer installieren `tesseract-ocr-fra` nicht

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

## DI-06.1-10 (Plan 06.1-21): zwei weitere Stellen nennen noch zwei OCR-Sprachen

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

---

## DI-06.1-11 (Plan 06.1-14): die OCR-Qualitaetsmessung faehrt in keinem Job

**Gefunden:** beim Bau von `findling.extract.ocr_quality` in Plan 06.1-14.

**Was:** das Werkzeug rechnet die Zeichenfehlerrate und traegt einen groben
Riegel von 0,05, der als Rueckgabewert 1 sichtbar wird. Gefahren wird es heute
nur von Hand, im Container, so wie es
`docs/measurements/2026-09-06-ocr-dach/README.md` beschreibt. Ein Riegel, den
niemand faehrt, faengt nichts: der Totalausfall, fuer den er da ist, wuerde erst
bei der naechsten Messung von Hand auffallen. Der natuerliche Ort ist der Job
`reconcile-and-dach` in `.github/workflows/integration.yml`, wo Korpus und
Engine ohnehin beieinander liegen; ein Schritt mit `--corpus testdata/corpus
--truth testdata/corpus-truth.json` genuegt, und der Rueckgabewert reicht als
Zusicherung.

**Warum nicht hier gefixt:** `integration.yml` gehoert in dieser Welle Plan
06.1-11, der dieselbe Datei anfasst. Zwei Executoren an einer Workflow-Datei
sind ein Konflikt und kein Fortschritt.

**Wohin es gehoert:** in den Plan, der `integration.yml` nach 06.1-11 als
naechster anfasst, spaetestens in den Abschlussplan der Phase (06.1-19). Wichtig
dabei: der Schritt gehoert **neben** die drei DACH-Suchen und nicht an ihre
Stelle. Das Gate bleibt ein Suchtreffer, die Messung steht daneben, und diese
Trennung ist die ganze Begruendung des Plans 06.1-14.

---

## DI-06.1-12 (Plan 06.1-14): Annahme A7 ist auf gerendertem Text widerlegt, auf Fotos ungeprueft

**Gefunden:** in der Gegenprobe bei 72 dpi, Plan 06.1-14.

**Was:** die Recherche fuehrt unter A7 als Annahme, Grossbuchstaben mit Umlauten
seien bei niedriger Aufloesung eine bekannte Schwaeche von tesseract. Auf
gerendertem Text ist das nicht eingetreten: bei 300 dpi null Fehler ueber alle
sechs Seiten, bei 72 dpi, dem niedrigsten von `FINDLING_OCR_DPI` zugelassenen
Wert, 19 Fehler ueber 3.148 Zeichen, und die deutsche Variante ist mit 0,0032
die beste der drei. Damit ist die Annahme auf sauberem Material widerlegt und
auf fotografiertem Material weiterhin ungeprueft, denn dafuer liegt kein
Testmaterial im Repository.

**Warum nicht hier gefixt:** ein fotografiertes Korpus ist keine Erweiterung des
Generators, sondern ein fremdes Korpus mit unklarer Lizenz und ohne
Bitgleichheit, und genau das schliesst die Regel "Don't Hand-Roll" der
Phasenrecherche aus. Es ist eine eigene Entscheidung und keine Nebenaufgabe.

**Wohin es gehoert:** in die Bewertung des RapidOCR-Zusatzpfads, den `STACK.md`
seit dem 15.08.2026 genau fuer fotografierte Belege fuehrt. Bis dahin gilt, was
`docs/measurements/2026-09-06-ocr-dach/README.md` unter "Was diese Zahl nicht
sagt" schreibt: die Null gilt fuer gerenderte Seiten und fuer nichts anderes.

---

## DI-06.1-13 (Debug-Session store-install-5, 06.09.): die widerlegte Routes-Behauptung steht noch an drei Stellen, und die Routen-URLs sind bare paths

**Gefunden:** beim Debuggen der Falsifikationsprobe Store install 5. HaRP (0.4.5,
haproxy_agent.py Z. 529-531) ueberspringt die Routenpruefung fuer AppAPI-signierte
Anfragen; der <routes>-Block regiert nur den unsignierten Direktzugriff. Die alte
Behauptung, ohne den Block verstumme die Suche, ist damit widerlegt (Beleg:
.planning/debug/store-install-5-routes-probe.md).

**Was noch falsch dasteht:** backend/appinfo/info.xml Z. 8-15 (Kommentar),
docs/certificates.md Z. 294-297, scripts/release/store-archive.sh Z. 82-91
(woertlich "proves with a stripped copy that the search goes silent without the
block").

**Zweiter Befund:** Findlings fuenf Routen-URLs sind bare paths (search, status).
HaRP matcht mit re.match(route.url, target_path) gegen /search, das ist None.
Kanonisch waere ^/search$ usw. Heute folgenlos (der signierte Weg fragt die
Tabelle nicht), aber der Block ist bei HaRP-Installationen wirkungslos und
schuetzt den unsignierten Weg nicht so, wie die info.xml es nahelegt.

**Wohin es gehoert:** die drei Textstellen in den Doku-Plan 06.1-15/17; die
kanonische Routen-Form in einen kleinen Folgeplan oder zusammen mit der
info.xml-Aenderung von DI-06.1-05 (Lizenz-Schreibweise), weil beide dieselbe
Datei anfassen und das Lockstep-Gate beide Haelften zusammen sehen will.

---

## DI-06.1-14 (ERLEDIGT durch 06.1-22, Plan 06.1-16): docs/dev-setup.md fuehrt beim lokalen Store-Weg in eine haengende Registrierung

**Was:** Der Abschnitt "Der Store-Installationsweg lokal" beschreibt die
compose-Einrichtung ohne Frontproxy und mit http://harp:8780 als nextcloud_url.
Ohne Frontproxy vor Nextcloud und HaRP kann der Container
PUT /ocs/v1.php/apps/app_api/ex-app/status nicht absetzen (404), weil AppAPI
nextcloud_url in zwei Richtungen braucht. Wer der Anleitung folgt, sucht den
Fehler bei der App. deploy-harp.yml loest die Topologie seit 03.09.2026 anders.

**Wohin:** Doku-Plaene 06.1-15/17.

---

## DI-06.1-15 (ERLEDIGT durch 06.1-22, Plan 06.1-16): ein auf Windows gebautes Release-Paket traegt CRLF

**Was:** Ein auf einem Windows-Arbeitsbaum gebautes Paket ist byteweise ein
anderes als das aus release.yml. Heute harmlos, weil release.yml der einzige
Erzeuger ist. Ein warnender Satz in scripts/release/store-archive.sh oder eine
Weigerung bei CRLF haelt es harmlos.

---

## DI-06.1-16 (Plan 06.1-16): die ExApps-Verwaltungsoberflaeche ist auf keinem Weg gemessen

**Was:** Weder CI noch Handlauf pruefen den Klickpfad der Verwaltungsseite,
den die meisten Admins gehen. Steht als Nichtabdeckung in docs/install-check.md.

---

## ERLEDIGT-Vermerk zu DI-06.1-11-Meldung aus Plan 06.1-16

Plan 06.1-16 meldete den root.crt-Zeilenumbruch (END/BEGIN verschmolzen,
splitCerts verliert die CI-CA) als eigenen Befund samt lokaler Reproduktion.
Zum Merge-Zeitpunkt war die Ursache bereits auf main behoben (8a20a1f:
printf-Newline-Wache plus verankerte Zaehlung). Die unabhaengige
Zweitreproduktion bestaetigt Diagnose und Fix; kein offener Rest.

---

## DI-06.1-17 (Plan 06.1-15): die Gastnutzer-Probe prueft ihre eigene Voraussetzung nicht

**Was:** Eine Instanz mit stillgelegtem Container hat ebenfalls eine leere
Warteschlange; der Vergleich meldet dann missing statt "die Probe konnte nicht
stattfinden". Abhilfe: Eigentuemer-Vergleich ueber den freigegebenen Marker vor
dem ersten Gastvergleich.

**Wohin:** Plan 06.1-19 (Owner-Sichtprobe), wo die Probe ohnehin gefahren wird.

---

## DI-06.1-18 (ERLEDIGT durch 06.1-22, Plan 06.1-17, Security-Audit): Passwoerter stehen in der Argumentliste zweier Dev-Skripte

**Was:** scripts/dev/guest_parity.sh und scripts/dev/aio_install_check.sh nehmen
Passwoerter als Kommandozeilenargument; auf einem Mehrbenutzersystem sind sie
damit in der Prozessliste lesbar. Schliessform laut Audit: Umgebungsvariable
oder stdin-Abfrage. Nur Dev-Werkzeuge, keine Auslieferung, deshalb LOW.

**Wohin:** kleiner Folge-Fix oder zusammen mit Plan 06.1-19.

---

## DI-06.1-19 (Plan 06.1-22): die compose-Fassung des Frontproxys in docs/dev-setup.md ist ungefahren

**Was:** Das Rezept ist aus deploy-harp.yml abgeleitet, auf dem compose-Stack
selbst aber nicht gefahren. Drei offene Details: Host: app, Namensaufloesung,
curl im Nextcloud-Image. Ehrlich als Messstand-Absatz gekennzeichnet.

## DI-06.1-20 (Plan 06.1-22): die CRLF-Wache greift erst beim Packen, nicht beim Stagen

**Was:** assert_no_crlf laeuft im pack-Schritt. Heute nicht erreichbar, weil
release.yml auf Linux laeuft; ein Stage-seitiger Check waere frueher.

## DI-06.1-21 (Plan 06.1-22): aio_install_check.sh hat kein eigenes Gate

**Was:** Die Hausordnung des Skripts liegt in test_guest_parity.py mit; ein
eigenes Testmodul waere die saubere Adresse.

---

## DI-06.1-22 (BEARBEITET durch 06.1-23 + Upstream, Plan 06.1-18, Befund arm64-4): zwei Instanzen am selben Docker-Dienst teilen den ExApp-Volumennamen

**Was:** Der Volumenname folgt allein aus der App-Kennung
(nc_app_findling_backend_data). Laufen zwei Nextcloud-Instanzen am selben
Docker-Dienst, loescht `app_api:app:unregister --rm-data` in der einen den
Bestand der anderen: state.db, vectors.db und den Tantivy-Index.

**Belegt durch Schaden:** genau das ist am 07.09. um 06:46Z passiert und hat das
Messvolumen dieses Laufs zerstoert (keine Messzahl verloren, alle waren
committet; der Korpus mit 50.000 Dateien blieb erhalten, der Index ist weg und
faehrt beim naechsten Boxstart einen Neuaufbau von rund 19 Stunden an).

**Wohin:** als Warnung in docs/uninstall.md und in jede Anleitung fuer einen
Testlauf neben einer echten Instanz. Vor der Store-Abgabe entscheiden, ob der
Loeschweg zusaetzlich die Instanz-Kennung in den Volumennamen aufnehmen soll,
das ist eine Produktentscheidung und keine Doku-Frage.

## DI-06.1-23 (Plan 06.1-18, Befund arm64-1): HaRP scheitert im Container an update-ca-certificates

**Was:** Permission denied, Exit 2, weil das Abbild nicht als root laeuft. Folge:
eine eigene CA der Instanz landet nicht im Vertrauensspeicher des Containers.
Fuer eine Instanz mit selbst ausgestelltem Zertifikat kann das der Unterschied
zwischen erreichbar und nicht erreichbar sein, und das ist ungemessen.
Auf beiden Instanzen der Box beobachtet.

## DI-06.1-24 (Plan 06.1-18, Befund arm64-2, MIT RICHTIGSTELLUNG des Orchestrators)

**Gemeldet wurde:** docs/dev-setup.md beschreibe den Store-Installationsweg
weiterhin ohne Frontproxy mit `location /exapps/`, Befund 4 aus 06.1-16 sei
weiterhin offen.

**Richtigstellung (07.09., am Repo geprueft):** Plan 06.1-22 Task 4 hat genau das
eingebaut, docs/dev-setup.md Z. 350-440 enthaelt die Zwei-Richtungen-Bedingung,
den 404-Fallstrick, den nginx-Block mit `location /exapps/` und die
Aufraeumzeile. DI-06.1-14 ist also zu Recht als erledigt gefuehrt. Der Executor
hat den Fallstrick auf der Box offenbar unabhaengig wiederentdeckt statt die
Anleitung zu lesen.

**Was daraus BLEIBT:** DI-06.1-19 fuehrt das Rezept als ungefahren. Dieser Lauf
hat den Fallstrick auf einer echten Instanz bestaetigt; ob die dort gefahrene
Loesung mit dem Rezept in der Anleitung uebereinstimmt, ist EIN Abgleich in Plan
06.1-19 wert (Messbericht 2026-09-nachmessung-m7g gegen docs/dev-setup.md
Z. 350-440).

## DI-06.1-25 (Plan 06.1-18, Befund arm64-3): der frpc-Aufbau gelingt erst im zweiten Anlauf

**Was:** Der erste Anlauf findet /certs/frp vorhanden, aber client.crt,
client.key oder ca.crt nicht lesbar fuer uid 1000, faellt auf einen Tunnel ohne
Client-Zertifikat zurueck und bekommt EOF. Eine Zeitabhaengigkeit zwischen HaRP
und dem Container, die auf einer langsameren Maschine laenger dauern koennte.

## DI-06.1-26 (Plan 06.1-18, Bericht Abschnitt 7): no_text_layer ist ein voruebergehendes Verdikt

**Was:** Es steht in state.db, bis der OCR-Durchgang die Datei wieder vorlegt.
Wer die Verdikttabelle liest, waehrend Arbeitsvorrat da ist, liest
Zwischenstaende. Ein Hinweis gehoert an die Stelle, die diese Tabelle beschreibt.

## DI-06.1-27 (Plan 06.1-18, docs/install-check.md Abschnitt 5): Deckungsgrad meldet "unbekannt" bei Nenner 0

**Was:** Solange der Nenner (indexierbare Dateien) 0 ist und der Zaehler schon
springt, meldet die Anzeige "unbekannt". Auf einer frischen Instanz mit einer
Datei sieht das wie ein Fehler aus und ist keiner.

**Bearbeitungsstand 07.09. (Plan 06.1-23 + Orchestrator):** Doku-Warnung an drei
Stellen (uninstall.md eigener Abschnitt, install-check.md und dev-setup.md je
ein Zeiger) und Instanz-Marke im Volumen (instance.py: fremde Kennung = kein
Indexstart, VOLUME_SHARED in /status, Server bleibt oben; kaputte Marke heilt
sich). Upstream gemeldet als nextcloud/app_api#1021 plus Kommentar an #523.
Restrisiko bleibt bis zum Upstream-Fix bestehen und ist dokumentiert.

---

## DI-06.1-28 (Plan 06.1-23): die note aus /status erreicht das Auge des Verwalters nicht

**Was:** AdminViewService traegt die note (z.B. VOLUME_SHARED) in die Nutzlast,
aber admin.php und admin.js rendern sie nirgends. Der Grund erreicht Protokoll
und JSON, nicht die Verwaltungsseite. Gilt genauso fuer die vier schon
vorhandenen Notizen, ist also ein Bestandsbefund. UI-Umbau mit l10n-String,
gehoert in einen eigenen kleinen Plan oder v1.0.1.

---

## DI-06.1-29 (ERLEDIGT 07.09.): der echte Fix der Volumenkollision liegt Upstream

**Was:** Als nextcloud/app_api#1021 eingereicht (Uebernahme- und Loeschpfad
pruefen keine Eigentuemerschaft; Label-Vorschlag als backportfaehiger Fix),
dazu Kommentar an #523 (Sechs-Stellen-Korrektur des Maintainer-Plans, HaRP
seit v0.2.0 fertig). Auf Reaktionen achten.

---

## DI-06.1-30 (ERLEDIGT, Plan 06.1-19): der Office-Fix ist im veroeffentlichten Abbild

Runde 2 der Sichtprobe hat den Fix am neu gebauten :dev-Abbild belegt (5/5
Suchproben, 0 fehlgeschlagen im Container).

## DI-06.1-31 (ERLEDIGT durch 06.1-24): kein CI-Job erreichte die Vielkern-Falle des Office-Pfads

Die Luecke, durch die Befund 8 fuenf Phasen fiel: Referenzkorpus ueberwiegend
PDF, Runner zu klein fuer die Adressraumgrenze. Owner-Entscheid 07.09.: wird
VOR der Abgabe geschlossen (Plan 06.1-24, Task 2, RLIMIT_AS-Ansatz).

## DI-06.1-32 (Plan 06.1-19): docs/dev-setup.md fuehrt beim lokalen Store-Weg weiter ohne Frontproxy

Als DI-06.1-14 erledigt vermerkt, aber der Abschnitt beschreibt weiterhin
http://harp:8780 als nextcloud_url; die Sichtprobe brauchte die Frontproxy-
Topologie. Kleiner Doku-Nachzug. (Hinweis Orchestrator: Widerspruch zur
Richtigstellung in DI-06.1-24 pruefen; moeglicherweise zwei verschiedene
Abschnitte derselben Datei.)

## DI-06.1-33 (Plan 06.1-19): Deckung meldet "indexable 0" waehrend des Erstlaufs

Im Zero-Config-Nachweis stand "indexed 41 of 0 indexable"; Endzustand korrekt,
waehrenddessen unbrauchbar. Verwaltungsseiten-Nachzug, klein.

## DI-06.1-34 (ERLEDIGT durch 06.1-24): ein failed-Urteil der PHP-Haelfte wird jetzt von spaeterem Erfolg widerrufen (nur content/ocr, skipped bleibt; siehe DI-06.1-36)

Befund 9 der Sichtprobe, vom Owner live gesehen (Kacheln "4 Fehlgeschlagen"
und "Datei beschaedigt, 4" samt Neu-hochladen-Rat bei findbaren Dateien).
Owner-Entscheid 07.09.: Fix VOR der Abgabe (Plan 06.1-24, Task 1).

## DI-06.1-35 (ERLEDIGT 07.09.): der gruene deploy-harp-Lauf ueber die neue Routenpruefung liegt vor (success auf 2f6f95b)

Befund 10 behoben (Erwartung auf die verankerte Routenform gezogen), die
Bestaetigung liefert der naechste deploy-harp-Lauf auf main nach dem Merge
der Runde 2.

---

## DI-06.1-36 (Plan 06.1-24): skipped wird nicht widerrufen

Der Widerruf gilt nur failed(content/ocr). Eine skipped-Zeile, deren Grund
spaeter entfaellt (z.B. OCR-Erfolg nach Konfigurationsaenderung), bleibt stehen.
Bewusste Grenze, klein.

## DI-06.1-37 (Plan 06.1-24): erschoepfter Adressraum meldet sich als corrupt statt out_of_memory

OpenBLAS raist bei pthread_create-Fehlschlag SIGINT -> KeyboardInterrupt
(BaseException) -> Kind stirbt -> Recyclingregel 4 urteilt corrupt. Ehrlicher
waere out_of_memory. Kandidat v1.0.1.

## DI-06.1-38 (Plan 06.1-24): Sprachmischung docs/testing.md (EN) vs docs/admin-page.md (DE)

Doku-Konsistenzfrage fuer einen spaeteren Nachzug.

## KORREKTUR-VERMERK (Plan 06.1-24) zu zwei Aussagen der 06.1-19-SUMMARY

Die "24-h-Aufraeumung" der failed-Zeilen existierte nicht (cleanupLatencyHours
ist etwas anderes); der Widerspruch der Verwaltungsseite war DAUERHAFT, der
Fix von DI-06.1-34 also noetiger als gedacht. Und failed(corrupt) beim
Office-Befund kam nicht von dispatch, sondern via OpenBLAS-SIGINT und
Recyclingregel 4 (siehe DI-06.1-37).
