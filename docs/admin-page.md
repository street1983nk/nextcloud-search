# Die Statusseite: welche Zahl woher kommt und was die vier Schalter tun

Diese Seite beschreibt die Verwaltungsansicht von Findling (ADM-01 bis ADM-04):
den Deckungsgrad, die Vorab-Schätzung, die Fehlerliste, die Diagnose einer
einzelnen Datei und die vier Schalter. Sie ist für zwei Leser geschrieben. Für
den Admin, der eine Zahl auf der Seite nachrechnen will, bevor er ihr glaubt, und
der wissen muss, was ein Schalter anrichtet, bevor er ihn umlegt. Und für den
Entwickler, der in einem Jahr auf eine Zahl stößt, die nicht zu einer anderen
passt, und sonst annehmen müsste, das sei ein Fehler.

Der Grund, aus dem es diese Seite überhaupt gibt, steht in
`.planning/research/PITFALLS.md`: das Vorgängerprojekt ist nicht daran
gescheitert, dass es nichts gefunden hat, sondern daran, dass niemand sagen
konnte, warum. Eine Statusanzeige, die "verbunden" meldet, während die Hälfte des
Bestands nie gelesen wurde, ist schlimmer als keine. Der Leitsatz dieser Seite
ist deshalb: sie sagt nie "nicht indexiert", wenn sie "ich weiß es gerade nicht"
meint.

## Wo die Seite liegt und wer sie sieht

Die Seite ist eine eigene Sektion in den Verwaltungseinstellungen und liegt unter
`/settings/admin/findling`. Sichtbar ist sie für angemeldete Administratoren und
für niemanden sonst.

Dieser Schutz ist eine Abwesenheit und keine Zutat: die Routen der Seite tragen
`FrontpageRoute` und ausdrücklich keines der Attribute `NoAdminRequired`,
`PublicPage` oder `NoCSRFRequired`. Erst dadurch verlangt die
`SecurityMiddleware` von Nextcloud einen angemeldeten Admin plus das
Anfrage-Token der Sitzung. Genau das hält `test_php_trust_boundary.py` fest, weil
sich eine Abwesenheit leichter versehentlich auflöst als eine Zeile Code. Der
praktische Nebeneffekt: die Seite ist von außen nicht per `curl` mit
Zugangsdaten erreichbar, weil das Token fehlt. Wer die Antwort ohne Browser
braucht, nimmt den occ-Zweitzugang weiter unten.

## Der Deckungsgrad und sein Nenner

Die Kopfzahl der Seite ist ein Bruch, und sein Nenner steht als Satz daneben,
damit die Zahl nachrechenbar ist statt geglaubt werden zu müssen.

Der Zähler ist `indexed` aus dem Container: die Zahl der Dateien, über die der
Container ein Urteil gefällt hat. Bewusst nicht seine Dokumentzahl `docs`, denn
die beiden sind zwei Quellen für denselben Sachverhalt, und dass sie
übereinstimmen, ist der Beweis dafür, dass das Schreiben in den Index
funktioniert. Beide bleiben nebeneinander sichtbar.

Der Nenner ist die indexierbare Menge, und er entsteht genau einmal, in
`AdminViewService::overview()`, als

```
indexierbar = filesSeen - overCap - excluded
```

aus der Tabelle `findling_scan_stats`, die der Crawl selbst füllt. Alle drei
Zahlen kommen also aus derselben Arbeit wie der Zähler und nie aus einer zweiten
Abfrage. Die Bedingungen in der Reihenfolge, in der sie greifen:

1. Die Datei liegt auf einem Mount, den die App überhaupt läuft. User-Homes
   immer, Team Folders und External Storage je nach ihrem Schalter.
2. Ihr Mimetype steht auf der Zulassungsliste
   (`StorageService::ALLOWED_MIMETYPES`, heute achtzehn Typen: PDF, die drei
   OOXML-Formate, die drei OpenDocument-Formate, Text, Markdown, CSV, HTML,
   XHTML, die beiden RTF-Schreibweisen und die vier Bildtypen). Dieser Filter
   steht in der Abfrage selbst und nicht dahinter.
3. Sie ist nicht Ende-zu-Ende verschlüsselt. Serverseitig verschlüsselte Dateien
   sind drin, weil das Inhalts-Gate sie entschlüsselt übergibt.
4. Sie liegt unter dem Größen-Cap. Was darüber liegt, zählt der Crawl als
   `overCap` und zieht es ab.
5. Sie liegt unter keinem Ausschluss-Präfix. Was darunter liegt, zählt der Crawl
   als `excluded` und zieht es ab.

Die Prozentzahl wird abgerundet und bleibt bei 99 stehen, solange auch nur eine
Datei fehlt. Eine Seite, die 100 Prozent meldet und dabei Dateien übrig hat, ist
genau der Fehler, den diese Phase unmöglich machen soll. Zwei Fälle haben
ausdrücklich keine Prozentzahl, sondern einen Satz: ein Nenner von null, weil
sich durch null nicht teilen lässt, und ein stummes Backend, weil dann auch der
Zähler fehlt und "0 Prozent" gelesen würde als "nichts ist auffindbar", während
die Wahrheit "niemand hat den Index gefragt" ist.

Solange der Scan nicht jeden Mount durchlaufen hat, ist der Nenner eine untere
Schranke, und die Seite sagt das: "Vorläufige Zahl, X von Y Speicherorten sind
durchgezählt." Eine Zahl, die sich still nach oben korrigiert, sieht wie ein
Defekt aus.

## Die zweite Zahl: auffindbar nach Bedeutung

Unter dem Deckungsgrad steht eine zweite Zahl, und sie hat denselben Nenner wie
die erste. Zähler ist `embedded` aus dem Container: die Zahl der Dokumente, die
einen Vektor tragen, gezählt in `vectors.db` und nirgendwo sonst. Der Container
meldet sie neben `indexed`, und sie ist darin enthalten und wird nie daneben
addiert: ein Dokument ohne Vektor ist indexiert, es ist nur noch nicht nach
Bedeutung auffindbar.

Warum die Zahl überhaupt existiert: die Einbettung läuft als zweite Spur und
füllt sich über Stunden nach, nachdem Volltext und OCR längst nutzbar sind.
Mit nur einer Zahl sähe ein Admin 100 Prozent, während eine Umschreibung nichts
findet, und nirgends stünde, warum. Der Satz auf der Seite nennt deshalb beide
Spuren:

> Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche
> deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem
> Erstindex nach.

Gerechnet wird sie mit `AdminViewService::coverageShare()`, und das ist genau die
Methode, die auch die erste Zahl rechnet: ein zweiter Aufruf mit einem anderen
Zähler und nie ein zweiter Rechenweg. Zwei Rechenwege für dieselbe Art Zahl
wären der Anfang der Drift, die Phase 4 mit ihrer einen Subtraktion vermieden
hat, und das Ergebnis wären zwei Zahlen, die jede für sich plausibel sind und
nicht mehr vergleichbar.

Auch hier gilt: abgerundet, und bei 99 stehend, solange ein Dokument ohne Vektor
übrig ist. Keine Prozentzahl, sondern einen Satz, gibt es in drei Fällen: kein
Nenner, stummer Container, und ein Container, der die Zahl gar nicht meldet, weil
er älter ist als diese App. Der dritte Fall ist der Grund, warum `embedded` auf
der PHP-Seite als `null` geführt wird und nicht als 0: "keine Vektoren" und
"niemand hat gefragt" sind zwei verschiedene Auskünfte, und 0 Prozent wäre eine
Aussage über eine Instanz, deren semantische Hälfte vollständig sein kann.

Ein fehlender oder unlesbarer Vektorspeicher ist ebenfalls ein Zustand und nie
ein Fehler: die Statusantwort trägt dann `embedded` gleich 0 und eine Notiz, und
jede Volltextzahl derselben Antwort bleibt gültig.

## Was nicht im Nenner steht, und warum

Nicht im Nenner stehen: Ordner, Dateien eines nicht unterstützten Typs, Dateien
über dem Cap, Dateien unter einem Ausschluss, Dateien auf einem Mount, den die
beiden Ganz-oder-nichts-Schalter ausgenommen haben, Ende-zu-Ende verschlüsselte
Dateien und der Papierkorb.

Der Grund ist für alle derselbe: sonst erreicht die Zahl nie 100 Prozent und sagt
damit nichts mehr. Ein Deckungsgrad, der bei 60 Prozent stehen bleibt, weil
40 Prozent des Bestands Videos und ZIP-Archive sind, misst nicht die Suche,
sondern die Dateitypverteilung der Instanz. Was absichtlich draußen geblieben
ist, wird deshalb nicht versteckt, sondern getrennt gezählt und als "absichtlich
ausgelassen" ausgewiesen: `overCap` plus `excluded` plus die als
`skipped(mime_not_allowed)` verzeichneten Dateien.

Eine Ausnahme ist wichtig: `skipped(no_text_layer)` gehört NICHT dazu. Dieser
Grund ist die Übergabestelle an die OCR-Spur und kein Endurteil, und ihn als
ausgelassen zu zählen würde Dateien abschreiben, die gerade auf dem Weg in den
Index sind.

## Welche Zahl aus welcher Quelle kommt

Die Seite führt zwei Sichten nebeneinander und verrechnet sie nie zu einer Zahl.
Fünf Quellen, und die Aufteilung ist eine Entscheidung und kein Zufall:

- Aus `findling_file_state`, also von der Nextcloud-Seite: `skipped`, `failed`,
  die Aufschlüsselung nach Grundcode und die Fehlerliste mit ihren
  Beispielpfaden. Das ist die Hälfte, die einen ausgeschalteten Container
  überlebt, und genau dann sucht ein Admin danach. Es ist auch die einzige
  Hälfte, deren Datei-Ids diese Seite in lesbare Pfade verwandeln kann, denn nur
  Nextcloud kennt Mounts und Besitzer.
- Aus dem Container, unter dem Schlüssel `backend`: `indexed`, `truncated`, die
  Dokumentzahl, die ACL-Zeilen, die Index- und Analyzer-Versionsmarken, der Hash
  der Wortliste, Platz und Indexgröße, der wirklich durchgesetzte Größen-Cap und
  der Durchsatz. Nur der Container weiß, was im Index steht.
- Aus `findling_queue`: `scheduled` und `running`. Bewusst nicht über die
  HTTP-Routen der Warteschlange, denn die tragen das ExApp-Attribut und sind aus
  einer Admin-Sitzung nicht erreichbar; den Arbeitsvorrat dieser Seite beim
  Container zu erfragen wäre eine zweite Antwort auf eine Frage, die die
  Datenbank direkt beantwortet.
- Aus `appconfig`: `lastJobRun`, also die Antwort auf "läuft der Cron dieser
  Instanz überhaupt", und die vier Schalter in ihrer geltenden Fassung. Diese
  Werte sind lesbar und schreibbar, auch wenn der Container aus ist.
- Aus `findling_scan_stats`: der Nenner des Deckungsgrads und die absichtlich
  ausgelassenen Dateien.

## Warum eine Differenz ein Signal ist und kein Fehler

Die beiden Sichten dürfen sich widersprechen. Wenn der Container 4 000 Dateien
als indexiert führt und die Nextcloud-Seite 120 als übersprungen, dann sind das
zwei Aussagen über zwei verschiedene Mengen, und ihre Differenz zur indexierbaren
Menge ist eine Information: sie sagt, dass Container und Nextcloud sich über
Dateien uneinig sind. Genau das muss ein Admin sehen können. Deshalb stehen die
Zahlen nebeneinander und werden nicht addiert.

Es gibt genau einen abgeleiteten Wert, `indexedDisplay`, und er wählt statt zu
verrechnen: antwortet der Container, gilt seine Zahl; schweigt er, gilt die
letzte Zahl dieser Seite, und das Banner sagt genau das. So springt keine Kachel
wegen einer gescheiterten Abfrage auf 0.

## Die sechs Stufen der Diagnose

Der Block "Look up one file" nimmt einen Pfad oder eine Datei-Id im selben Feld
und nennt Zustand, Grund, Label und Abhilfe. Der Zustand einer Datei steht in bis
zu drei Quellen und in keiner davon vollständig, deshalb ist die Antwort eine
Kette mit fester Reihenfolge und keine Zusammenfassung. Die erste Stufe, die
antwortet, gewinnt:

1. **Existiert die Datei überhaupt?** Kein Cache-Eintrag und keine Mount-Zeile
   mehr: dann ist sie gelöscht, oder es war nie eine. Beide Fälle bekommen
   dieselbe Antwort, weil drei unterscheidbare Antworten dieses Feld zu einem Weg
   machen würden, Benutzernamen der Instanz zu erraten.
2. **Bricht sie eine Regel von HEUTE?** Live berechnet, aus keiner
   Datenbankzeile: Papierkorb, nicht indexierter Speicher, Ordner statt Datei,
   nicht zugelassener Typ, über dem geltenden Cap, unter einem
   Ausschluss-Präfix. Diese Stufe muss live sein, denn `mime_not_allowed` wird
   nie geschrieben: der Crawl filtert den Mimetype in der Abfrage und sieht eine
   unpassende Datei niemals.
3. **Steht sie im Arbeitsvorrat?** Dann wartet sie, oder sie wird gerade
   bearbeitet. Ob wartend oder laufend, entscheidet die Restsperrzeit und nicht
   eine leere Sperrspalte.
4. **Gibt es ein Urteil auf dieser Seite?** Also `skipped` oder `failed` mit
   Grund aus `findling_file_state`. Das ist die Quelle, die einen gestoppten
   Container überlebt.
5. **Gibt es ein Urteil im Container?** Nur dort existiert "ist auffindbar".
   Schweigt der Container, lautet die Antwort "Zustand gerade unbekannt, weil das
   Backend nicht antwortet", und niemals "nicht indexiert".
6. **Nichts davon?** Dann hält die Datei jede Regel ein, nichts hat sie
   beurteilt, und nichts wartet auf sie: der Crawl ist noch nicht bei ihr
   angekommen. Das ist ein Zustand mit Namen ("Noch nicht gesehen") und keine
   Abwesenheit. "Nicht indexiert, Grund unbekannt" ist der Satz, den diese App
   unmöglich machen soll.

**Was ein Grabstein bedeutet und was nicht.** Der Container markiert eine Zeile,
deren Datei den Index verlassen hat. Diese Marke darf nur in Stufe 1 als Löschung
gelesen werden, also genau dort, wo überhaupt kein Cache-Eintrag mehr gefunden
wurde; dann ist der Satz "war indexiert und ist seither gelöscht" ehrlich. Bei
einer Datei, die es noch gibt, bedeutet der Grabstein etwas ganz anderes: die
Räumung nach einem Ausschluss oder nach einem Löschereignis, das die Datei
überlebt hat. Mechanisch ist das eine Löschung im Container, semantisch keine,
denn die Datei liegt unberührt auf der Platte. Eine solche Datei ist deshalb
"Noch nicht gesehen" mit dem Hinweis, dass sie vorher im Index war, und nie
"verschwunden".

## Die Schätzung: was sie ist und was nicht

Der Block "Estimate for the first index" nennt Dateizahl, OCR-Anteil, erwartete
Dauer und Platzbedarf.

Was er **nicht** ist: ein Bestätigungs-Gate. In dieser App wartet nichts auf das
Einverständnis eines Admins, der Erstindex startet von selbst, und das ist das
Kernversprechen einer Zero-Config-Suche (D-05). Die Schätzung ist eine
Information ab Minute 1 und keine Bedingung. Das Roadmap-Kriterium sagt "vor dem
Erstindex"; D-05 ist die spätere, ausdrückliche Entscheidung und gewinnt, und die
Seite beschriftet die Zahl stattdessen als vorläufig, solange der Scan noch
läuft.

Wie sie genauer wird: sie kalibriert sich am laufenden Durchgang statt aus
Konstanten vorhergesagt zu werden. Der Container meldet über `GET /rates` die
Text- und die OCR-Rate getrennt, und die Seite rechnet die Restmenge damit hoch,
eine Division je Spur, weil eine OCR-Seite und eine Textseite um
Größenordnungen auseinanderliegen. Der OCR-Anteil bleibt bewusst ein Intervall
(Bilder als Untergrenze, Bilder plus alle PDF als Obergrenze), bis die Hälfte der
indexierbaren Dateien ein Urteil hat, denn ein gemessener Wert, der noch
klettert, ist eine untere Schranke und sieht als Zahl wie ein Defekt aus. Der
Platzbedarf entsteht aus `indexBytes` geteilt durch `docs`, mal der Dateizahl, und
er warnt gegen den freien Platz minus der Reserve von 500 MB, die der Container
sich freihält: die Warnung kommt also, solange noch etwas zu tun ist, und nicht
nachdem der Index angehalten hat.

Solange nichts gemessen ist, stehen dokumentierte Startwerte darin, und die Seite
sagt "Startwert, wird gemessen." Die OCR-Rate entsteht dann aus der gemessenen
Millisekundenzahl je Seite mal dem Seitendeckel von 30 Seiten je Dokument; der
Textwert von 3 600 Dokumenten je Stunde ist eine Annahme, die nie gemessen wurde
(Annahme A2 der Recherche). Alle Messwerte dieses Projekts stammen von einem
amd64-Laptopkern, siehe `docs/ocr.md`; die Zielhardware ist eine ARM-Box, und
deren Messlauf steht in Phase 5 aus. Die Beschriftung ist deshalb kein Beiwerk:
eine Dauer ohne sie wäre eine Zahl, die wie eine Messung aussieht.

## Die vier Schalter

Der Block "Rules and limits" führt genau vier Schalter, und diese Kürze ist
Absicht (ADM-04, D-08).

| Schalter | Default | Wirkt ab wann | Wirkt wo |
|---|---|---|---|
| Ordner-Ausschlüsse | leere Liste, höchstens 64 Einträge mit je 256 Zeichen | nächster Lauf, plus sofortige aktive Räumung des Bestands | Crawl, Ereignis-Listener, Abgleich, Diagnose (Stufe 2) |
| Größen-Cap | 50 MiB (52428800 Byte), Untergrenze 1 MiB, Obergrenze der vom Container gemeldete Wert | nächster Lauf | Crawl (aus dem Cache-Eintrag), zusätzlich im Container |
| Team Folders | AN | nächster Lauf | Mountliste des Crawls und des Abgleichs |
| External Storage | AUS | nächster Lauf | Mountliste des Crawls und des Abgleichs |

Gespeichert wird PHP-seitig in `appconfig`, und der Container übernimmt die Werte
beim nächsten Lauf. Es gibt keinen Neustartzwang und kein Live-Signal an den
Container: "der nächste Lauf hält sich daran" ist die Zusage, nicht "ab sofort".

Team Folders sind AN, weil ein Team Folder der geteilte Arbeitsbereich der
Instanz selbst ist, seine Dateien wie ein Home auf lokalem Speicher liegen und
dort die Dokumente einer kleinen Organisation tatsächlich stehen. External
Storage ist AUS, weil ein entferntes Laufwerk jede Annahme über Lesedauer und
Datenmenge sprengt und niemand erwartet, dass die Installation einer App
anfängt, ein Mehr-Terabyte-Share durch HTTP zu ziehen.

## Der Pfadraum der Ausschlüsse

Ein Ausschluss ist ein Pfad-Präfix, ohne Muster und ohne Platzhalter (D-06), und
er wird relativ zur Wurzel des Mounts verglichen, auf dem eine Datei liegt.

In einem User-Home ist diese Wurzel der `files`-Ordner des Benutzers. Drei
Beispiele:

- `Archiv` schließt `Archiv/` und alles darunter aus.
- `Backups` ebenso, in jedem Home gleichzeitig.
- `.stversions` schließt die Versionsordner aus, die manche Clients anlegen.

Zwei Präzisierungen, ohne die ein Präfix falsch gesetzt wird:

Erstens: die Präfixe wirken in **allen** Homes auf einmal, nicht in einem
bestimmten. `Archiv` heißt "der Archiv-Ordner jedes Benutzers" und nicht "der
Archiv-Ordner von Alice". Einen Ausschluss für eine einzelne Person gibt es
bewusst nicht.

Zweitens: die früher notierte Lesart, Präfixe gelten **nur in User-Homes**, ist
in Plan 04-09 richtiggestellt worden und war nie das, was der Code tut. Der
Vergleich läuft in jedem Mount, den die App läuft, jeweils relativ zu dessen
Wurzel. Auf einem Team Folder oder einem externen Mount benennt derselbe Präfix
also einen Ordner an der Spitze dieses Mounts. Der Unterschied ist nicht
kosmetisch: was der Crawl auslässt, muss die Räumung entfernen und die Diagnose
erklären, sonst behält der Index Inhalte, die es laut Regeln nicht gibt.
Zusätzlich haben Team Folders und External Storage ihren eigenen
Ganz-oder-nichts-Schalter, sodass eine Instanz, die sie gar nicht indexiert haben
will, dafür keinen Präfix braucht.

Eine ausgeschlossene Datei verschwindet nicht stumm. Sie erscheint in der
Diagnose mit dem Grund `excluded`, also "Durch Regel ausgeschlossen" samt
Abhilfe, aus derselben geschlossenen Tabelle wie jeder andere Grund. Eine Zeile
je ausgeschlossener Datei wird bewusst nicht geschrieben: bei einem Archivordner
mit zweihunderttausend Dateien wären das zweihunderttausend Zeilen für eine
Antwort, die aus vier Vergleichen folgt, und jede davon wäre in dem Moment
falsch, in dem die Regel zurückgenommen wird.

## Was beim Hinzufügen und beim Entfernen eines Ausschlusses passiert

**Hinzufügen.** Ein neuer Ausschluss räumt den Bestand aktiv (D-07): die Inhalte
und die ACL-Zeilen unterhalb des Präfixes verlassen den Index, damit der Index
die Regeln immer spiegelt und keine Geisterinhalte auffindbar bleiben. Weil das
eine Folge ist, die niemand versehentlich auslösen soll, nennt die Seite sie
vorher. Beim Speichern erscheint eine Inline-Bestätigung, die die Dokumentzahl
unter den neuen Präfixen nennt, gezählt bis zu einer Obergrenze von 5 000; ist
die erreicht, sagt die Seite "mindestens 5 000", weil eine exakte Zahl, auf die
niemand wartet, keine Hilfe ist. Erst nach der Bestätigung wird geschrieben.

Die Räumung selbst beginnt innerhalb einer Cron-Runde und läuft in Bändern durch
den Teilbaum jedes betroffenen Mounts. **Die Dateien selbst bleiben dabei
unverändert.** Findling schreibt nie in eine Nutzerdatei, und die Räumung ist
kein Löschen auf der Platte, sondern das Entfernen von Indexzeilen; das
Prüfsummen-Gate über das Referenzkorpus hält diese Zusage bei jedem Commit fest.

**Entfernen.** Einen Präfix zurückzunehmen heilt sich selbst, und zwar langsam.
Die Dateien werden wieder aufgezählt, aber eingesammelt werden sie vom
nächtlichen Abgleich, und der hält sich zurück, solange
`FINDLING_RECONCILE_MIN_INTERVAL_HOURS` es sagt (Default 24 Stunden). Die Seite
nennt diese Latenz, denn ohne sie würde ein Admin einen Präfix entfernen, neu
laden, nichts passieren sehen und Warten nicht von Kaputt unterscheiden können.
Wer nicht warten will, nimmt den ausgeschriebenen Ausweg:

```bash
occ findling:index --restart
```

Das reiht jeden Mount neu ein und liest damit jedes Dokument der Instanz noch
einmal. Es ist der Notausgang und nicht der Normalweg.

## Der Größen-Cap und die doppelte Durchsetzung

Der Cap wird an zwei Stellen durchgesetzt, und das ist der Grund, warum das
Eingabefeld nach oben geklemmt ist.

Die PHP-Seite kennt den Cap aus `appconfig` und wendet ihn im Crawl an, aus dem
Cache-Eintrag, noch vor dem Download. Der Container wendet ihn ein zweites Mal
an: `nc/client.py` bricht den Download bei `settings().max_file_bytes` ab, und
`extract/dispatch.py` prüft die Größe noch einmal. `settings()` liest dabei
ausschließlich Umgebungsvariablen und ist `lru_cached`, also beim Prozessstart
festgelegt.

Ein PHP-Wert oberhalb von `FINDLING_MAX_FILE_BYTES` hätte deshalb keine Wirkung,
sondern eine schlimmere Folge: die Datei würde eingereiht, der Container würde
den Download abbrechen und `skipped(too_large)` schreiben, und die Seite würde
daneben einen Cap anzeigen, unter dem die Datei angeblich liegt. Das ist genau
der Widerspruch zwischen Seite und Verhalten, den diese Phase beseitigt. Deshalb
meldet der Container seinen eigenen Deckel in der Statusantwort, die Seite merkt
sich diesen Wert (er überlebt damit einen gestoppten Container) und klemmt die
Eingabe daran.

Um darüber hinaus zu gehen, reicht die Seite nicht. Nötig sind zwei Schritte:

1. `FINDLING_MAX_FILE_BYTES` in den AppAPI-App-Einstellungen der ExApp
   "Findling Backend" hochsetzen.
2. Den Container neu starten, weil die Variable beim Start gelesen wird.

Danach meldet der Container den neuen Deckel, die Obergrenze des Feldes wandert
mit, und der Wert lässt sich auf der Seite setzen.

## Der occ-Zweitzugang

Für einen Support-Fall ist der wichtigste Zugang der ohne Browser, und die Seite
kann ihn nicht liefern: ihre Routen verlangen das Anfrage-Token einer echten
Browsersitzung. Dafür gibt es `occ findling:diagnose`. Das Kommando ruft dieselbe
Funktion wie die Route, `AdminViewService::diagnose()`, und hat keine eigene
Zustandslogik, es gibt also keine zweite Vorrangregel, die driften könnte.

Eine Eingabeart je Beispiel:

```bash
# als Datei-Id, so wie sie in der Fehlerliste steht
occ findling:diagnose 190

# als Pfad in der Schreibweise, die Nextcloud führt
occ findling:diagnose testuser/files/corpus/09-bescheid.pdf

# als Kurzform aus Besitzer und Pfad relativ zum files-Ordner
occ findling:diagnose testuser:corpus/09-bescheid.pdf
```

Ausgegeben werden Zustand, Grundcode, Label, Abhilfe, Pfad, Besitzer, Datei-Id,
Papierkorb- und Freigabestand, der letzte Prüfzeitpunkt und ausdrücklich, ob das
Backend geantwortet hat. Eine Eingabe, die keine Datei benennt, ist eine Auskunft
und kein Fehler: das Kommando sagt es und endet mit Exit-Code 0. Nur eine leere
oder zu lange Eingabe wird mit einem statischen Satz abgewiesen, und der Wert
selbst erscheint in keiner Logzeile, denn was in diesem Feld ankommt, ist ein
Dateiname.

Weil occ keine Sitzung hat, nimmt das Kommando für den Aufruf beim Container das
erste aktivierte Mitglied der Gruppe `admin` als Identität; AppAPI signiert
seinen Header damit. Lässt sich keines ermitteln, etwa weil die Verwaltung dieser
Instanz an eine Gruppe anderen Namens delegiert ist, sagt die Ausgabe "backend
answered no" statt einen Zustand zu behaupten. Die Hälfte, die aus Nextcloud
kommt, steht trotzdem da.

Der Zweitzugang zu den Zahlen liegt auf der Container-Seite:
`backend/src/findling/tools/index_status.py`, derselbe Gedanke für die Zähler
statt für die einzelne Datei.

## Was die Seite bewusst nicht kann

Drei Dinge fehlen absichtlich, und jedes davon ist eine Entscheidung und kein
offener Punkt.

**Keinen Textauszug in der Diagnose.** Ein Snippet ist Dateiinhalt und bleibt an
SRCH-02 gebunden, wo es nur für einen Treffer gebaut wird, der den
Berechtigungs-Recheck schon überlebt hat. Diese Linie hier zu verwischen ist der
Weg, auf dem ein Verwaltungswerkzeug zu einem Inhaltsleck wird. Der Container
meldet eine Zeichenzahl, und selbst die wird nicht weitergegeben: eine Zahl
könnte man anzeigen, einen Text nicht, und der kürzeste Weg, beides
auseinanderzuhalten, ist keines von beiden zu tragen.

**Kein Alter der ältesten wartenden Zeile.** Die Tabelle `findling_queue` hat
keine Spalte `created_at`, und eine dafür nachzurüsten wäre eine Migration für
eine Zahl, die die eigentliche Frage nicht beantwortet. Wer wissen will, ob etwas
hängt, will wissen, ob die Hintergrundjobs dieser Instanz laufen, und das
beantwortet `lastJobRun` mitsamt dem Stockt-Zustand: mehr als 30 Minuten ohne
Lauf bei wartender Arbeit, also sechs verpasste Runden des
Fünf-Minuten-Systemcrons.

**Keinen Erweitert-Bereich mit zwanzig Optionen.** Die Zielgruppe sind
Selbsthoster und kleine Organisationen, und die Optionsflut ist einer der Gründe,
an denen das Vorgängerprojekt gescheitert ist. Es bleibt bei vier Schaltern.
Alles andere ist eine Umgebungsvariable des Containers, dokumentiert dort, wo sie
gemessen wurde, und keine Zeile auf dieser Seite.

## Wo die Seite lokal zu sehen ist

Die Sichtprobe läuft gegen die Instanz aus `docs/dev-setup.md`, als `admin`
angemeldet, unter `/settings/admin/findling`.

Zum Port, weil er in den Artefakten zweimal unterschiedlich steht: die
Compose-Datei liest `FINDLING_PORT` und hat 8080 als Default, und der
Phase-1-Abschnitt von `docs/dev-setup.md` benutzt genau diesen Default. Ab dem
Phase-2-Abschnitt schreibt dasselbe Dokument ausdrücklich `FINDLING_PORT=8090`
vor, weil auf der Entwicklungsmaschine eine zweite lokale Nextcloud die 8080
hält und zwei Instanzen auf einem Port nicht laut scheitern, sondern die Anfragen
der jeweils anderen beantworten. Die laufende Entwicklungsinstanz antwortet daher
auf 8090, und die Angabe 8090 im UI-Vertrag ist richtig. Wer die
Umgebungsvariable nicht exportiert, landet auf 8080 und sucht dann eine Seite,
die auf einem anderen Port steht.
