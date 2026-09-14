# Pitfalls Research

**Domain:** Ausbau einer ausgelieferten Nextcloud-Such-ExApp (Findling 1.1.0): Dateityp-Filter und Sortierung auf der eigenen Ergebnisseite, Modell-Entladung im Leerlauf, Messkampagne auf Zielhardware
**Researched:** 2026-09-14
**Confidence:** HIGH fuer alles, was am Baum von `C:\Users\Student\nextcloud-search` und an den Rohdaten von `docs/measurements/2026-09-vergleichsmessung-m7g/` nachgelesen oder empirisch gemessen wurde (Tantivy-Sortierprobe gegen die installierte 0.26.0); MEDIUM fuer die Allokator- und onnxruntime-Aussagen zur RSS-Rueckgabe (Fremdquellen, ein offener Upstream-Bug); LOW fuer nichts, was hier als Tatsache steht

> Leitsatz dieser Recherche: Alle drei v1.2-Vorhaben sind Ergaenzungen an einem System, dessen Zusagen bereits im App Store stehen. Kein einziger dieser Fallstricke ist "die Funktion geht nicht". Alle sind von der Sorte "die Funktion sieht aus, als ginge sie, und gibt dabei still eine Zusage von v1.0/v1.1 auf": die eine Berechtigungsgrenze, die Index-Kompatibilitaet ohne Reindex, die Antwort unter der 1,5-Sekunden-Aufrufdecke, die Vergleichbarkeit der Messzahlen, den Gleichstand der drei Kataloge.

**Phasennamen in diesem Dokument sind Vorschlaege**, weil die v1.2-Roadmap noch nicht steht. Verwendet werden: **Filterphase** (Dateityp-Filter und Sortierung), **Entladephase** (Modell-Entladung im Leerlauf), **Messphase** (die eine Box-Anfahrt), **Haertungsphase** (DI-11-02/03/05/06, Store-Einreichung v1.2.0).

---

## Critical Pitfalls

### Pitfall 1: Der Filter wirkt hinter der Fusion statt in der Anfrage, und das Fenster frisst ihn auf

**What goes wrong:**
Der Dateityp-Filter wird dort angewendet, wo er am billigsten einzubauen ist: auf der fertigen Trefferliste, also hinter `reciprocal_rank_fusion` oder sogar erst in PHP hinter dem Recheck. Die Suche nach "Vertrag" mit Filter "PDF" liefert dann drei Treffer auf einer Seite, die fuenfundzwanzig fasst, die Blaetterung meldet trotzdem "weiter", und zwei Seiten spaeter kommt wieder eine halbleere Seite. Auf einem Bestand wie dem Messkorpus (52.111 Dokumente) liefert der Filter regelmaessig gar nichts, obwohl passende Dateien im Index stehen.

**Why it happens:**
`findling.index.search.candidates` arbeitet mit einem Fusionsfenster von `SEARCH_RRF_WINDOW = 100` Dokumenten je Quelle. Wer erst dieses Fenster fuellt und danach filtert, filtert die hundert relevantesten Dokumente aller Typen und nicht die hundert relevantesten PDFs. Derselbe Fehler eine Etage hoeher: der PHP-Recheck bekommt eine Kandidatenseite, `SearchService` zaehlt `$approved` gegen `$pageSize`, und ein Filter, der erst hier zuschlaegt, macht aus jeder Seite eine Stichprobe. Der Filter sieht dabei funktionsfaehig aus, denn was er zeigt, ist immer richtig; falsch ist nur, was fehlt.

**How to avoid:**
Der Filter gehoert in die Anfrage, nicht in die Antwort. Der Weg existiert bereits und ist gebaut: `query/rewrite.py::extract_filters` schneidet `type:` aus der Zeile, `_extension_query` haengt ihn als `Occur.Must` auf das Feld `ext` an die geparste Anfrage. Ein UI-Filter muss auf genau diesen Pfad einzahlen, also als zusaetzliche `Must`-Klausel vor dem ersten `searcher.search`, damit das Fusionsfenster von Anfang an nur aus dem gefilterten Bestand gefuellt wird.
Die Vektorseite kann das nicht: `store/vectors.py` kennt keine Dateiendung, ein kNN-Lauf liefert Nachbarn aller Typen. Es gibt genau zwei ehrliche Auswege, und einer davon muss bewusst gewaehlt und im Bericht benannt werden:
1. Unter Filter bleibt die Suche lexikalisch. Das ist die heutige Regel (`api/search.py::one_round`, `lexical_only = bool(rewritten.operators) or ...`, `FILETYPE` ist eine dieser Marken) und kostet nichts ausser einer Zeile in der Doku.
2. Die Vektorliste wird nach der Aggregation gegen den Index auf den Typ zurueckgeschnitten, bevor sie in die Fusion geht. Dann schrumpft die semantische Haelfte unter Filter sichtbar, und `VECTOR_SCAN_MAX` muss entsprechend groesser gewaehlt werden, sonst bleibt nach dem Schnitt nichts uebrig.

**Warning signs:**
Eine gefilterte Seite liefert weniger als `PAGE_SIZE` Treffer, obwohl `hasMore` wahr ist. Ein Dokument, das ohne Filter auf Rang 4 steht, verschwindet mit passendem Filter ganz. Die Trefferzahl je Anfrage faellt unter Filter deutlich (derselbe Fingerabdruck, den Stufe 16 der v1.1-Lastreihe hatte: 4,16 statt 5,40 Treffer je Anfrage).

**Phase to address:**
Filterphase. Abnahme: ein Test, der dieselbe Anfrage mit und ohne Filter fuehrt und beweist, dass jedes gefilterte Dokument der ungefilterten Liste auch in der gefilterten steht, und zwar ueber die Fenstergrenze hinaus (Korpus mit mehr als 100 lexikalischen Treffern, von denen die passenden Typen weit hinten liegen).

---

### Pitfall 2: Der UI-Filter schreibt `type:` in die Suchzeile und schaltet damit still die Semantik ab

**What goes wrong:**
Die billigste Bauform eines Dropdowns ist, die Auswahl an die Suchzeile anzuhaengen: aus "Vertrag" plus Auswahl "PDF" wird der Text `Vertrag type:pdf`, und der Rest der Kette bleibt unveraendert. Das funktioniert auf Anhieb, denn genau diesen Text versteht `extract_filters` schon. Was dabei passiert, sieht niemand: `carried_operators` setzt die Marke `FILETYPE`, `one_round` setzt daraufhin `lexical_only = True`, und die semantische Haelfte wird fuer jede gefilterte Suche abgeschaltet. Aus einem Filter wird ein Schalter fuer die Produktfunktion, mit der das Projekt wirbt.

**Why it happens:**
Die Marke `FILETYPE` wurde eingefuehrt, als der Typ ausschliesslich aus einer getippten Zeile kam. Dort war die Begruendung richtig: wer `type:` tippt, bittet um Genauigkeit, und das Modell sieht Woerter, keine Operatoren. Ein Dropdown ist aber keine Bitte um Genauigkeit im selben Sinn. Die Entscheidung, die in `rewrite.py` steht, wird durch die neue Oberflaeche stillschweigend auf einen Fall ausgedehnt, fuer den sie nie getroffen wurde.

**How to avoid:**
Der Filter reist als eigener Parameter und niemals als Text in der Suchzeile. Konkret: ein Feld in `SearchRequest` (Achtung: `model_config = ConfigDict(extra="forbid")`, ein unbekanntes Feld wird als HTTP 400 abgewiesen, nicht ignoriert), das an `build_query` durchgereicht wird und dort dieselbe `Must`-Klausel erzeugt, ohne `carried_operators` zu beruehren. Danach ist die Frage "Semantik unter Filter ja oder nein" wieder eine bewusste Entscheidung und keine Nebenwirkung. Zusatzregel, die dazu gehoert: eine getippte `type:`-Zeile UND ein gesetzter Dropdown-Filter muessen eine definierte Semantik haben (Empfehlung: beide gelten, also UND-Verknuepfung, was leere Ergebnisse erzeugen kann und deshalb in der Oberflaeche sichtbar sein muss).

**Warning signs:**
Eine Paraphrasensuche, die ohne Filter das Dokument findet, findet es mit Filter "PDF" nicht mehr, obwohl das Dokument ein PDF ist. Der Diagnosepfad (`api/diagnose.py`, `ranked_sides`) meldet fuer gefilterte Anfragen eine leere semantische Liste.

**Phase to address:**
Filterphase, und zwar als erste Entscheidung der Phase, weil sie die Signatur von `build_query` und damit alle vier Aufrufstellen (`/search`, `/snippets`, Diagnose, Tests) bestimmt.

---

### Pitfall 3: Der neue Parameter erreicht `/search`, aber nicht `/snippets`

**What goes wrong:**
Filter und Sortierung werden an der Kandidatenroute angebaut und funktionieren. Die Ausschnittsroute bekommt sie nicht, weil sie ja "nur Text schneidet". Ergebnis: der Textausschnitt wird mit einer anderen Anfrage erzeugt als die, die den Treffer gerankt hat. Bei einem reinen Typfilter faellt das nicht auf (er fuegt keine Terme hinzu), bei allem, was die Standardfelder oder die Termmenge veraendert, schon: die Hervorhebungen markieren Woerter, die im Ranking keine Rolle spielten, oder der Ausschnitt bleibt leer und die Seite faellt auf den Pfad zurueck.

**Why it happens:**
Die Zweistufigkeit des Protokolls ist bewusst asymmetrisch (Kandidaten ohne Text, Text nur fuer Bestaetigte), und dabei wirkt die zweite Stufe wie ein Anhaengsel. Tatsaechlich baut `api/snippets.py` ueber `build_query` dieselbe Anfrage nochmal auf. Der Praezedenzfall steht schon da: `titleOnly` reist zu beiden Routen, weil es die Standardfelder wechselt.

**How to avoid:**
Jeder Parameter, der `build_query` beruehrt, wird in beide Request-Modelle aufgenommen und von `SearchService` an beide Aufrufe uebergeben (`ExAppService::searchCandidates` und `ExAppService::snippets`). Dazu ein Gleichstand-Test nach dem Muster von `backend/tests/test_search_limits_lockstep.py`: er liest beide Modelle als Text und wird rot, sobald eines ein Feld traegt, das dem anderen fehlt. Sortierung dagegen darf ausdruecklich NICHT an `/snippets` gehen: sie veraendert die Reihenfolge, nicht die Anfrage, und ein Sortierparameter im Schnitt waere ein Feld, das nichts tut und beim naechsten Umbau etwas tut.

**Warning signs:**
Hervorhebungen stehen auf Woertern, die nicht gesucht wurden. Ausschnitte sind unter Filter systematisch leer, obwohl die Dokumente den Suchbegriff enthalten.

**Phase to address:**
Filterphase, zusammen mit Pitfall 2 (dieselbe Signaturaenderung).

---

### Pitfall 4: Sortierung nach Datum wird in die Fusion gehaengt, und der Score wird zum Zeitstempel

**What goes wrong:**
Sortierung wird als Variante der bestehenden Suche gebaut: `searcher.search(query, window, order_by_field="mtime")` statt `searcher.search(query, window)`, alles andere bleibt. Zwei Dinge kippen dabei gleichzeitig und beide leise.
Erstens: **der zurueckgegebene Score ist dann nicht mehr der BM25-Wert, sondern der Feldwert selbst.** Empirisch gegen die installierte tantivy 0.26.0 gemessen (Probe vom 14.09.2026): ohne `order_by_field` liefern die Treffer Scores wie 0,1363 und 0,1220, mit `order_by_field="mtime"` liefern dieselben Treffer die Werte 500, 300, 200, 100, also die Inhalte des Feldes. Dieser Wert wandert durch `_ranked` in `Candidate.score` und von dort ueber die Wire in die PHP-Haelfte. Nichts faellt um, und jede spaetere Auswertung des Scores ist Unsinn.
Zweitens: nach Datum sortiert ist die Rangliste kein Relevanzrang mehr, und `reciprocal_rank_fusion` fusioniert dann eine Datumsliste mit einer Semantikliste zu etwas, das weder das eine noch das andere ist: "ueberwiegend neu, ein bisschen aehnlich". Die Fortsetzung hinter dem Fenster (Abschnitt 2 von `candidates`) rechnet weiter `lexical_weight / (k + rank)`, was unter Datumssortierung eine Zahl ohne Bedeutung ist.

**Why it happens:**
`order_by_field` ist ein Schluesselwortargument von `Searcher.search`, es steht direkt neben `offset`, es funktioniert sofort, und die Aenderung ist eine Zeile. Dass die Bedeutung des ersten Tupelelements mitwechselt, steht in keiner Signatur.

**How to avoid:**
Sortierung ist ein eigener Modus und keine Variante der Fusion. Empfehlung, opinionated: **unter "Neueste zuerst" laeuft die Suche lexikalisch, ohne RRF, ohne Vektorzweig, und die Oberflaeche sagt das** ("nach Datum sortiert"). Begruendung: eine Sortierung nach Datum wirft die Relevanzordnung ohnehin weg, und die semantische Haelfte existiert ausschliesslich, um Relevanz zu verbessern. Der Code-Weg dazu ist derselbe, den `lexical_only` heute schon geht, also kein neuer Zweig in der Sicherheitskette.
Zusaetzlich: der Score, den `Candidate` unter Sortierung traegt, wird auf 0.0 gesetzt und nicht durchgereicht, damit kein Zeitstempel als Relevanz aus dem Container faellt.

**Warning signs:**
`Candidate.score` traegt Werte in der Groessenordnung 1.7e9. Die Diagnoseroute meldet unter Sortierung Herkunftsmarken, die sich mit der Reihenfolge nicht erklaeren lassen. Zwei Suchen mit denselben Treffern liefern unter verschiedenen Sortierungen unterschiedliche Treffermengen (nicht nur Reihenfolgen).

**Phase to address:**
Filterphase. Abnahme: Testfall, der unter Sortierung die TrefferMENGE gegen die unsortierte Menge derselben Tiefe vergleicht; sie darf sich nur durch die Vektorhaelfte unterscheiden, und das muss benannt sein.

---

### Pitfall 5: Sortierung nach Name oder Groesse wird zugesagt und braucht einen Reindex

**What goes wrong:**
Das Dropdown bekommt vier Eintraege: Relevanz, Datum, Name, Groesse. Drei davon sind billig, einer davon ist unmoeglich, und welcher, merkt man erst beim Bauen. Schlimmer: der naheliegende Fix ist eine Schemaaenderung, und eine Schemaaenderung bedeutet `SCHEMA_VERSION` hochziehen, Versionsmarke bricht, `version_drift` meldet `reindexRequired`, und 52.111 Dokumente werden auf einer 4-GB-ARM-Box neu indexiert. Das verletzt die Zusage D-04 aus v1.1 ("index-kompatibel, kein Reindex") in genau dem Milestone, der Bestandsinstallationen nicht bestrafen soll.

**Why it happens:**
`index/schema.py` sagt es selbst: ein Feld, das spaeter hinzukommt, bedeutet einen Reindex. Nur `file_id`, `storage_id` und `mtime` sind `fast=True`. `name` ist ein Textfeld mit eigener Kette, `ext` ist `raw` mit `basic`, Groesse steht ueberhaupt nicht im Schema. Empirisch gemessen (dieselbe Probe): `order_by_field="mtime"` und `order_by_field="file_id"` funktionieren, `order_by_field="ext"` scheitert mit `ValueError: Field "ext" is not configured as fast field`, ein unbekanntes Feld mit `Field 'nope' is not defined in the schema`.

**How to avoid:**
Die Sortierauswahl von v1.2 besteht aus genau zwei Eintraegen: **Relevanz und Datum.** Beides ist ohne Schemaaenderung und ohne Reindex zu haben. Alles andere wird als Future notiert und zusammen mit einer ohnehin faelligen Schemaaenderung gebuendelt.
Dieselbe Regel gilt fuer eine Verlockung auf der Filterseite: **Trefferzahlen je Dateityp ("PDF (12)") brauchen ein Fast-Field auf `ext`**, also ebenfalls einen Reindex. Verzichten, oder nur die Typen der geladenen Seite zaehlen und das Label entsprechend ehrlich formulieren.

**Warning signs:**
Im Plan steht "Sortierung nach Name". Irgendwo taucht `SCHEMA_VERSION` in einem Diff auf, der eigentlich nur die Oberflaeche betrifft. Die Statusseite meldet nach einem Testupgrade `reindexRequired`.

**Phase to address:**
Filterphase, als Vorpruefung VOR dem ersten Plan (die Probe dauert zehn Minuten und entscheidet den Funktionsumfang). Gegenprobe in der Haertungsphase: der Upgrade-Beweis 1.1.0 auf 1.2.0 in CI muss zeigen, dass die Indexmarken unveraendert bleiben.

---

### Pitfall 6: Der Cursor-Pfad ueberlebt einen Filterwechsel und liefert eine falsche Seite ohne Fehler

**What goes wrong:**
Der Nutzer steht auf Seite 7, klickt "nur PDFs", und landet auf Seite 7 einer voellig anderen Ergebnismenge. Treffer werden uebersprungen, andere doppelt gezeigt, und nichts sagt etwas. Es gibt keine Fehlermeldung, weil die Adresse formal gueltig ist.

**Why it happens:**
`PageController::cursorPath` prueft die **Form** des Pfads und nicht seine **Herkunft**: genau `$page` Eintraege, lauter Ziffern, streng aufsteigend, erster Eintrag 0. Ein Pfad aus einer ungefilterten Suche erfuellt all das auch fuer eine gefilterte. Die Cursorwerte zaehlen erlaubte Kandidaten derselben Anfrage; aendert sich die Anfrage, zeigen dieselben Zahlen auf voellig andere Stellen. Das heutige Formular umgeht das Problem, indem es weder `page` noch `cursors` traegt, sodass jede neue Suche auf Seite eins beginnt. Ein Filter, der als Link gebaut wird ("nur PDFs" als `<a>` mit den aktuellen Parametern), nimmt den Cursor-Pfad aber genau mit.

**How to avoid:**
Zwei Regeln, beide durchsetzbar:
1. Jede Aenderung an Suchbegriff, `names`, Typfilter oder Sortierung setzt `page` auf 1 und `cursors` auf leer. Filter- und Sortiersteuerung werden deshalb als Formularfelder gebaut, die in demselben `<form>` liegen, das schon heute weder `page` noch `cursors` traegt; als Link gebaut, muessen sie beide Parameter ausdruecklich weglassen.
2. Der Cursor-Pfad wird an die Anfrage gebunden, damit eine von Hand editierte Adresse nicht durchrutscht: ein kurzer Fingerabdruck ueber (Begriff, `names`, Filter, Sortierung) reist mit, und ein Pfad mit fremdem Fingerabdruck faellt auf Seite eins zurueck. Das ist genau die Behandlung, die `cursorPath` heute schon fuer jede Abweichung vorsieht, und sie bleibt stumm, wie der Kommentar dort es verlangt.

**Warning signs:**
Ein Treffer erscheint auf Seite 3 und nochmal auf Seite 4. Die Seitennummer im Pager passt nicht zur Laenge des Cursor-Pfads in der Adresse. `nextUrl` ist `null`, obwohl `hasMore` wahr ist (die Pruefung `nextCursor <= end($cursors)` schlaegt zu, weil der Cursor aus einer anderen Anfrage stammt).

**Phase to address:**
Filterphase. Abnahme: PHP-Unit-Test, der einen Pfad aus einer ungefilterten Suche mit gesetztem Filter einreicht und Seite eins erwartet.

---

### Pitfall 7: Der Filter oeffnet eine zweite Tuer an der Berechtigungsgrenze

**What goes wrong:**
Die naheliegendste Bauform einer Filterleiste mit Trefferzahlen oder einer Sortierumschaltung ohne Neuladen ist eine zweite Route, die Treffer als Daten liefert. Damit existiert eine zweite Stelle, die Kandidaten aufloest, eine zweite, die `isReadable()` fragt (oder es vergisst), und die Sicherheitsaussage des Produkts ist nicht mehr "eine Stelle im ganzen Baum".

**Why it happens:**
Die Ergebnisseite rendert heute alles serverseitig in ein Dokument, ohne Datenroute, ohne Formatumschalter, ohne Teilnachladung. Das ist ein Entwurfsvertrag und keine technische Schranke, also laesst er sich versehentlich brechen. Zusaetzlich steht in `PageController` ein Kommentar, der leicht zur Falle wird: die drei Route-Attribute duerfen im Fliesstext dieser Datei nicht genannt werden, weil `backend/tests/test_php_trust_boundary.py` die Zeilen zaehlt, die ein Route-Attribut erwaehnen. Ein gut gemeinter Kommentar ueber die neue Filterroute macht ein Gate rot, ohne dass sich eine Route geaendert hat.

**How to avoid:**
- Keine neue Route. Filter und Sortierung sind zwei zusaetzliche Werte in der bestehenden Adresse von `findling.page.index`, genau wie `query`, `names`, `page`, `cursors`. Die Seite bleibt eine Route, ein Dokument, kein Nachladen.
- Der Filter wird niemals hinter dem Recheck angewendet (siehe Pitfall 1). Damit bleibt `SearchService::run` die einzige Stelle, die `getFirstNodeById` und `isReadable` fragt, und `backend/tests/test_php_acl_boundary.py` zaehlt weiter genau zwei Aufrufstellen.
- Neue Parameter werden wie die vier bestehenden behandelt: still auf einen sicheren Wert zurueckfallen, niemals eine Meldung ueber die eigene Adresszeile erzeugen. Ein unbekannter Typwert bedeutet "kein Filter", eine unbekannte Sortierung bedeutet "Relevanz".
- Auf der Containerseite: `SearchRequest` hat `extra="forbid"`. Der neue Parameter muss dort deklariert werden, sonst scheitert die Validierung und die Suche bricht komplett; und er darf nichts sein, was eine Identitaet transportieren koennte. Die Nutzerkennung kommt weiterhin ausschliesslich aus dem signierten AppAPI-Header.
- Der Unified-Search-Dialog bleibt unangetastet: `getSupportedFilters` meldet `BUILTIN_TERM` und `BUILTIN_TITLE_ONLY`, `getCustomFilters` meldet nichts. Ein eigener Filter dort braucht eine `FilterDefinition`, und ein Name ohne Definition macht laut dem Kommentar in `Provider.php` die ganze Providerliste kaputt. Dateityp und Sortierung gehoeren in v1.2 ausschliesslich auf die eigene Seite.

**Warning signs:**
Ein Diff fuegt `php/appinfo/routes.php` eine Zeile hinzu. `test_php_acl_boundary.py` oder `test_php_trust_boundary.py` wird rot. In `SearchService` taucht ein zweites `foreach` ueber Kandidaten auf.

**Phase to address:**
Filterphase fuer den Bau, Haertungsphase fuer den Audit (die Launch-Haertung hat in v1.0 und v1.1 je echte Produktfehler an genau solchen Stellen gefunden).

---

### Pitfall 8: MIME und Dateiendung sind zwei Wahrheiten, und der Filter waehlt die falsche

**What goes wrong:**
Die Filterkategorie heisst "Bilder" und wird in der Oberflaeche ueber den MIME-Typ gedacht, weil der Treffer sein Symbol schon ueber `IMimeTypeDetector::mimeTypeIcon($hit->mimeType)` bekommt. Im Index gibt es aber keinen MIME-Typ, nur `ext`. Ergebnis: Eine Datei mit Symbol "Bild" faellt aus dem Filter "Bilder" heraus, weil ihre Endung `.jpeg` und nicht `.jpg` ist, oder eine Datei ganz ohne Endung ist unter keinem Filter zu erreichen und auch nicht unter "Sonstige".

**Why it happens:**
Es gibt im Produkt zwei unabhaengige Klassifikationsquellen, und beide sind korrekt fuer ihren Zweck:
- `ext` kommt aus `extract/dispatch.py::extension_of`, also aus dem **Dateinamen**: kleingeschriebenes Suffix ohne Punkt, leer wenn keines da ist. Es steht als `raw`-Token mit `basic`-Indexoption im Index und wird beim Indexieren geschrieben.
- `mimeType` kommt in `SearchService` aus dem **bestaetigten Knoten** (`$node->getMimetype()`), also aus dem Nextcloud-Dateicache, und ist aktueller als alles, was der Index wissen kann.
Sie stimmen fast immer ueberein und gelegentlich nicht: `.jpg` gegen `.jpeg`, `.tif` gegen `.tiff`, Office-Formate, die als ZIP erkannt werden, umbenannte Dateien zwischen zwei Indexlaeufen, Dateien ohne Endung. Ein leeres `ext` erzeugt ueberdies gar kein Token, also kann keine `term_query` es je treffen.

**How to avoid:**
- Die Filterkategorien werden **ueber Endungen definiert und ueber Endungen gefiltert**, weil nur die im Index steht. Die Kategorie "Bilder" ist eine Menge von Endungen und wird als `Should`-Gruppe uebersetzt, so wie `_extension_query` es fuer mehrere `type:`-Angaben schon tut.
- Die Menge der anbietbaren Endungen kommt aus dem, was der Indexer ueberhaupt einreiht, nicht aus einer frei erfundenen Liste. Der Endungsvergleich aus v1.1 (13 Endungen, Generator gleich Bestand, eine benannte Abweichung) ist die Quelle dafuer.
- Dateien ohne Endung bekommen eine bewusste Entscheidung: entweder sie sind unter keinem Filter erreichbar und das steht in der Doku, oder es gibt eine Kategorie fuer sie, die dann ein Index-Feld braucht, das es nicht gibt (also: Variante eins).
- Wenn Symbol und Filterkategorie nebeneinander stehen, muss die Oberflaeche damit leben koennen, dass beide aus verschiedenen Quellen kommen. Kein Test darf die Gleichheit von `ext` und `mimeType` behaupten.

**Warning signs:**
Ein Testkorpus enthaelt nur `.pdf`, `.docx`, `.txt`. Eine Kategorie in der Oberflaeche heisst wie ein MIME-Oberbegriff. Im PHP-Code taucht eine Abbildung von MIME auf Endung auf.

**Phase to address:**
Filterphase. Abnahme: Korpusfall mit `.jpeg`, `.JPG` (Grossschreibung), einer Datei ohne Endung und einer umbenannten Datei.

---

### Pitfall 9: Sortierung nach Datum auf grossem Fremdbestand liefert systematisch leere Seiten

**What goes wrong:**
Ein Nutzer mit dreissig eigenen Dateien auf einer Instanz mit 52.000 fremden Dokumenten waehlt "Neueste zuerst" und bekommt gar nichts, ohne Fehlermeldung. Unter Relevanz hatte er wenigstens manchmal Treffer.

**Why it happens:**
Das ist DI-07-03 in verschaerfter Form, und der Messbericht hat den Mechanismus bereits belegt: der Vorfilter rankt ueber den ganzen Index, der Recheck filtert erst danach, und fuer drei von vier geprueften Begriffen kam die eigene Datei unter den ersten **2.000** Kandidaten nicht vor. Unter Relevanz hat ein seltener Begriff wenigstens eine Chance ("Mueller" hatte genau einen Treffer im ganzen Index, und das war die eigene Datei). Unter Datumssortierung gibt es diese Chance nicht mehr: die neuesten hundert Dokumente, die "Vertrag" enthalten, gehoeren auf einer solchen Instanz mit an Sicherheit grenzender Wahrscheinlichkeit jemand anderem. Die Schleife holt dabei genau eine Runde (gemessen: 1,0 Runde je Suche), also wird nicht nachgefasst.

**How to avoid:**
- Den Fall messen statt hoffen: die Sprachfall-Messung der Messphase muss beide Sortierungen fahren, sonst wird die Verschaerfung erst von Nutzern gefunden.
- Die Seite muss den Unterschied zwischen "nichts gefunden" und "alle Kandidaten dieser Runde gehoerten anderen" weiterhin aussprechen. Der Mechanismus existiert: `SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED` und die Ausnahme in `nextUrl`, die genau in diesem Zustand die naechste Seite NICHT wegnimmt (Entscheid V-1a vom 10.09.2026). Unter Sortierung darf diese Ausnahme nicht verloren gehen, denn hier ist sie der Normalfall und nicht die Ausnahme.
- Nicht kaufen, was verboten ist: eine zusaetzliche Runde, ein groesseres Fenster oder gar ein Vorfilter, der die Berechtigung schon beim Ranken beruecksichtigt, sind die naheliegenden Fixe. Die ersten beiden kosten Laufzeit unter einer 1,5-Sekunden-Decke, der dritte macht eine zweite Sicherheitsgrenze auf. Die Roadmap hat diesen Handel ausdruecklich ausgeschlossen.

**Warning signs:**
`FAILURE_ALL_CANDIDATES_REJECTED` haeuft sich in einem Testlauf unter Datumssortierung. Die gemessene Rundenzahl bleibt bei 1,0, waehrend die Trefferzahl auf null faellt.

**Phase to address:**
Filterphase (Verhalten), Messphase (Zahl auf Zielhardware), Haertungsphase (Formulierung auf der Seite in EN/DE/FR).

---

### Pitfall 10: Die Entladung gibt RSS nicht zurueck, und die Messung sagt trotzdem "erfolgreich"

**What goes wrong:**
Die Sitzung wird freigegeben, der Halter geleert, im Log steht "entladen", und `anon` im Container faellt um zwanzig Megabyte statt um vierhundert. Oder schlimmer: die Zahl faellt im Testfall und nicht auf der Box, weil die Testumgebung andere Allokatorbedingungen hat.

**Why it happens:**
Drei Schichten geben Speicher unterschiedlich zurueck.
- **glibc-malloc** gibt freigegebene Bloecke ueblicherweise nicht ans Betriebssystem zurueck, sondern behaelt sie in der Arena. Das Basisimage ist `python:3.13-slim-trixie`, also glibc, und `malloc_trim(0)` ist verfuegbar, muss aber ausdruecklich gerufen werden (per `ctypes`).
- **onnxruntime** hat einen offenen Bericht genau zu diesem Verhalten beim Zerstoeren von Sitzungen (Issue 26831: Speicher wird von `ReleaseSession`/`ReleaseEnv` nicht zurueckgegeben). Der Arena-Allokator ist in diesem Projekt bereits abgeschaltet (`enable_cpu_mem_arena=False`, Hebel 6), was die Lage verbessert, aber keine Rueckgabe garantiert.
- **Der groessere Block liegt gar nicht bei onnxruntime.** Die RAM-Tabelle in `CLAUDE.md` nennt Tokenizer und Splitter mit **544 MB** Spitze (amd64 544,3 / arm64 543,7 / auf der Box 542,8), gegen 250 bis 400 MB fuer onnxruntime plus Modell. Wer nur die ONNX-Sitzung entlaedt, laesst den groesseren Posten stehen. Der Tokenizer lebt ausserdem auf der Rust-Seite, also ausserhalb dessen, was Pythons Speicherverwaltung ueberhaupt beruehrt.

**How to avoid:**
- Das Erfolgskriterium ist eine **gemessene Zahl auf der Zielbox**, nach demselben Ablesungsprotokoll wie in v1.1 (`anon` aus den cgroup-Werten, nicht RSS aus `ps`), und nicht "die Referenz ist weg".
- Entladen wird, was zusammengehoert: die ONNX-Sitzung UND der Tokenizer/Splitter des zweiten Gleises (`poller._chunker`, `poller._model`). Sonst ist die Ersparnis der kleinere Teil der Rechnung.
- `malloc_trim(0)` nach der Entladung ausprobieren und die Wirkung ausweisen. Wenn es nichts bringt, gehoert auch das in den Bericht.
- Vorab eine Messung, die entscheidet, ob die Funktion sich lohnt: erst entladen, dann messen, dann bauen. v1.1 hat die Entladung nicht gebaut, weil die gemeinsame Engine 588,6 MB gebracht hat und die Entladung damit ein "Bedarfsfall" wurde. Wenn die Rueckgabe jetzt nur 40 MB betraegt, ist der Bedarfsfall nicht eingetreten und die Funktion faellt zugunsten der Messphase weg. Das ist ein legitimer Ausgang und muss vor dem Bau ausgesprochen sein.

**Warning signs:**
Die Entladung ist in Unit-Tests gruen, aber es gibt keine Zahl von der Box. Die Ersparnis wird aus der Differenz "geladen minus frisch gestartet" gerechnet statt aus "vor der Entladung minus nach der Entladung". Der Wert schwankt zwischen zwei Laeufen um mehr als die behauptete Ersparnis.

**Phase to address:**
Entladephase, aber mit einem Vorprueflauf ganz am Anfang, dessen Ergebnis ueber den Rest der Phase entscheidet.

---

### Pitfall 11: Zwei Besitzer der Engine, und die Entladung tut deshalb nichts

**What goes wrong:**
`engine.reset()` wird gerufen, der Halter ist leer, die Diagnose sagt "cold", und der Speicher bleibt trotzdem belegt. Oder das Gegenteil: nach der Entladung baut der Suchpfad eine neue Engine, waehrend das zweite Gleis noch die alte haelt, und der Container traegt wieder zwei Tokenizer und zwei onnxruntime-Sitzungen. Das sind genau die 276 MB, die Plan 06.1-02 entfernt hat.

**Why it happens:**
Der Halter in `embed/engine.py` ist nicht der einzige Besitzer. Der Poller haelt in `_build_the_cutter` eine eigene Referenz (`self._model`, dazu `self._chunker`). `engine.reset()` leert ausdruecklich nur das Modulglobal, und die Docstring sagt selbst, dass die Funktion "von niemandem im Container" benutzt wird und fuer Testsuite und ein Werkzeug da ist. Wer sie als Entladefunktion wiederverwendet, bekommt genau diesen Zwei-Besitzer-Zustand.
Die zweite Haelfte ist angenehmer, als sie klingt: Pythons Referenzzaehlung schuetzt einen laufenden Aufruf. `EmbeddingModel._embed` holt die Engine einmal unter dem Lock in eine lokale Variable und laesst `Run()` bewusst ausserhalb des Locks laufen (der onnxruntime-Maintainer sagt das zu). Wird `self._engine` in diesem Moment auf None gesetzt, lebt das `_Engine`-Objekt weiter, solange die lokale Referenz existiert. **Unsicher wird es erst, wenn die Entladung mehr tut als loslassen**: ein explizites `del session` plus `gc.collect()`, ein Aufruf einer Freigabefunktion der Bibliothek, oder ein Umbau, der die Engine nicht mehr in eine lokale Variable holt.

**How to avoid:**
- Genau ein Ort entscheidet ueber Laden und Entladen, und das ist der Halter in `embed/engine.py`. Der Poller fragt ihn bei jedem Bedarf neu, statt eine Referenz ueber Stunden zu halten. Das ist die gleiche Bewegung, die 06.1-02 fuer das Laden gemacht hat, jetzt fuer das Entladen.
- Entladen heisst loslassen. Keine expliziten Destruktoren, kein erzwungener `gc.collect()` auf einem Objekt, das gerade in einem nativen Aufruf sein koennte. Wenn `malloc_trim` gerufen wird, dann nach einem Zaehlerstand, der belegt, dass kein Aufruf mehr laeuft.
- Ein Zaehler fuer laufende Einbettungen (hoch beim Betreten von `_embed`, runter beim Verlassen), und die Entladung passiert nur bei Stand null. Der bestehende RLock reicht dafuer nicht, weil er den Graphlauf absichtlich nicht abdeckt.
- Ein Test nach dem Muster des bestehenden: `load_count()` vor und nach einem Entlade- und Nachladezyklus mit gleichzeitiger Suche, und die Zusicherung, dass nie zwei Sitzungen gleichzeitig existieren.

**Warning signs:**
`engine.reset()` taucht ausserhalb von Tests und `tools/one_load.py` im Produktionspfad auf. Der Poller haelt nach der Entladung noch `self._chunker`. Die Grundlast nach der Entladung liegt ueber der Grundlast vor dem ersten Laden.

**Phase to address:**
Entladephase.

---

### Pitfall 12: Die Kaltstart-Klippe wird vom Ausnahmefall zum Regelfall und reisst die 1,5-Sekunden-Decke

**What goes wrong:**
Nach der Entladung zahlt die naechste Suche das Nachladen. Die PHP-Haelfte ruft den Container mit einer harten Decke von `REQUEST_TIMEOUT_SECONDS = 1.5` Sekunden auf. Reisst der Aufruf, antwortet die Route mit **HTTP 200 und einer Ergebnisgruppe ohne Containerteil**: der Nutzer sieht null Treffer, keine Fehlermeldung, und im Nextcloud-Protokoll steht `cURL error 28`. Genau das ist am 10.09.2026 um 14:05:17Z passiert und in `rohdaten/95c-...` belegt. Eine Entladung im Leerlauf macht aus diesem einmaligen Vorfall ein taegliches Ereignis: jede erste Suche nach einer Ruhephase faellt hinein, und die Unified Search fragt bei jedem Tastendruck.

**Why it happens:**
Die gemessenen Zahlen lassen dafuer keinen Spielraum. Kaltstart ueber OCS auf vollem Bestand: **1.838,4 ms**, Marge zur Decke **minus 338,4 ms**. Drei Reproduktionen lagen bei 1.598, 1.805 und 2.468 ms, und dass sie trotzdem Treffer lieferten, lag am Seitencache des Wirts, der die Modellgewichte noch hielt. Die erste Suche kostet ausserdem gemessene **plus 415,0 MB** `anon`. Wer entlaedt, kauft Grundlast mit genau dieser Klippe.

**How to avoid:**
Die Entladung darf niemals dazu fuehren, dass ein Nutzer synchron auf das Nachladen wartet. Der Weg dafuer ist schon gebaut und kostet nichts: ein nicht geladenes Modell ist kein Fehler, sondern der Zustand `embedding_unavailable`, die Vektorliste ist leer, die RRF-Fusion wird zur Identitaet auf der lexikalischen Liste, und der Nutzer bekommt Volltexttreffer (D-19). Also:
- Beim Nachladen antwortet die Suche **sofort lexikalisch** und stoesst das Laden im Hintergrund an. Die naechste Suche ist dann wieder vollstaendig.
- Alternative, die ausdruecklich zu verwerfen ist: die Decke auf 3 Sekunden anheben. Sie gilt fuer den Dialog, der alle Provider parallel fragt, und ein Provider, der drei Sekunden blockiert, macht die ganze Suche traege.
- Die Ruhefrist wird gross genug gewaehlt, dass sie in einem Arbeitstag nicht mehrfach greift, und der Wiederaufwaerm-Preis wird **gemessen und ausgewiesen**, wie der Milestone es verlangt: als Zahl mit Angabe des Seitencache-Zustands (siehe Pitfall 16).
- Eine Alternative, die ernsthaft zu pruefen ist und die den ganzen Fallstrick umgeht: **nur das zweite Gleis entlaedt** (Tokenizer und Splitter, 544 MB, kein Nutzer wartet darauf), der Suchpfad behaelt seine Sitzung. Das ist der groessere Posten und der ungefaehrliche.

**Warning signs:**
Im Nextcloud-Protokoll haeufen sich `cURL error 28` auf `/exapps/findling_backend/search`. Die Trefferzahl je Anfrage faellt, waehrend das Messwerkzeug null Fehlschlaege meldet (siehe Pitfall 18). Nutzer berichten "die erste Suche findet nie etwas".

**Phase to address:**
Entladephase fuer das Verhalten, Messphase fuer die Zahl, Haertungsphase fuer den Store-Text (die Zusage darf nicht besser klingen als die Messung).

---

### Pitfall 13: Der sechste Engine-Zustand bricht ein geschlossenes Vokabular an sechs Stellen

**What goes wrong:**
Die Entladung braucht ein Wort fuer "war geladen, ist jetzt entladen, laedt bei Bedarf nach". Es wird im Container eingefuehrt, die Admin-Seite zeigt daraufhin "Dieser Container meldet den Zustand des Modells noch nicht", was wie ein kaputtes Backend aussieht, und in der franzoesischen Fassung fehlt der Satz ganz.

**Why it happens:**
Der Zustand ist ein geschlossenes Vokabular, das an sechs Stellen im Gleichstand gehalten wird:
1. `backend/src/findling/embed/engine.py`: die fuenf Konstanten und `ENGINE_STATES` als `frozenset`, ausdruecklich so gebaut, "dass eine sechste Antwort nicht ankommen kann, ohne dass diese Zeile sie sieht".
2. `php/lib/Service/AdminViewService.php`: `private const ENGINE_STATES = ['loaded', 'cold', 'disabled', 'missing', 'waiting_for_retry']`. Ein unbekanntes Wort wird zu `null`.
3. `php/templates/admin.php`: die Satzabbildung `$engineSentences` fuer die erste Darstellung.
4. `php/js/admin.js`: der `switch` fuer jede weitere Abfrage.
5. bis 6. die Kataloge `de.js/de.json`, `de_DE.js/de_DE.json`, `fr.js/fr.json` mit den vier Gates aus `backend/tests/test_admin_ui_contract.py`: gleiche Schluesselmengen, franzoesische Vollstaendigkeit, Platzhalter-Paritaet, franzoesische Pluralregel.

**How to avoid:**
- Zuerst pruefen, ob ueberhaupt ein sechstes Wort noetig ist. `cold` bedeutet heute "die Artefakte sind da, nichts hat geworfen, nichts wurde gelesen". Das beschreibt einen entladenen Container korrekt. Der Satz dahinter ("Das Modell wird gelesen, wenn es zuerst gebraucht wird. Das ist der normale Zustand.") passt ebenfalls. **Empfehlung: kein sechstes Wort, sondern `cold` wiederverwenden**, und die Information "es war schon einmal geladen" gehoert, wenn ueberhaupt, in eine getrennte Zahl auf der Admin-Seite.
- Wenn es doch ein sechstes Wort wird: alle sechs Stellen in einem Plan, plus die Owner-Abnahme fuer den franzoesischen Wortlaut (Muttersprachler-Gate als blockierender Checkpoint, wie in v1.1).

**Warning signs:**
Die Admin-Seite zeigt den Ausweichsatz. Ein Katalog-Gate wird rot mit "differs from ... in [...]". `AdminViewService::engineState` liefert `null` fuer einen Zustand, den der Container gerade gemeldet hat.

**Phase to address:**
Entladephase (Entscheid und Bau), Haertungsphase (Kataloge und Abnahme).

---

### Pitfall 14: Der one-load-Beweis wird durch die Entladung entwertet, ohne rot zu werden

**What goes wrong:**
`findling.tools.one_load` und der zugehoerige Schritt in `resilience.yml` beweisen seit 06.1-02, dass ein Prozess genau einmal laedt. Mit einer Entladung im Leerlauf ist diese Zusicherung nicht mehr wahr, und das Gate hat zwei moegliche Ausgaenge, die beide schlecht sind: es wird rot, obwohl das Produkt richtig arbeitet, oder es bleibt gruen, weil sein Messfenster kuerzer ist als die Ruhefrist, und beweist damit eine Eigenschaft, die das Produkt nicht mehr hat.

**Why it happens:**
`_LOAD_COUNT` ist absichtlich monoton und nicht zuruecksetzbar ("ein Zaehler, der genullt werden kann, ist einer, mit dem ein Gate sich selbst gruen nullen koennte"). Die Aussage "genau ein Laden je Prozess" war die richtige Formulierung fuer eine Welt ohne Entladung.

**How to avoid:**
Die Invariante wird umformuliert, bevor die Funktion gebaut wird, nicht danach:
- alt: "ein Prozess laedt genau einmal"
- neu: "zu keinem Zeitpunkt existieren zwei Engines, und innerhalb eines warmen Fensters wird genau einmal geladen"
Dazu ein zweiter Zaehler fuer Entladungen, damit die Differenz `loads - unloads` die Aussage traegt, und die Rot-Faehigkeit des umgebauten Gates wird per Mutation am echten Baum bewiesen. Das ist der etablierte Standard dieses Projekts ("Beweis-Tests, deren Rot-Faehigkeit per Mutation belegt ist, sind die einzigen, deren Gruen etwas bedeutet").

**Warning signs:**
Das Gate wird flatterig statt deterministisch. Im Plan steht "Gate anpassen" ohne Angabe, welche Aussage es danach traegt.

**Phase to address:**
Entladephase, als erster Plan der Phase (die Invariante steht vor dem Bau fest).

---

### Pitfall 15: Der Messdeckel ist kleiner als der Lauf, den er decken soll

**What goes wrong:**
Der Deckelvorschlag lautet 26 Stunden und 3,50 USD fuer EINE Anfahrt, die den DI-10-04-Wirkungsbeleg-Volllauf, die Untersuchung der vier regressiven Laststufen, die Sprachfall-Messung ohne Fremdbestand und den Erstvollzug des Wiederaufbau-Runbooks traegt. Der letzte Volllauf allein hat **26 Stunden 37 Minuten** gedauert. Der Deckel reisst am ersten Tag, genau wie der 30-Stunden-Deckel in v1.1 gerissen ist (gerissen am 10.09. um 15:20Z, vom Owner auf 34 Stunden angehoben).

**Why it happens:**
Der Deckel wird aus der Erinnerung an die erwartete Laufzeit gebildet, nicht aus der gemessenen. Dazu kommen in v1.1 gemessene 38 Minuten Anfahrt und Vormessungen plus rund 2 Stunden 50 Minuten Nachmessungen, also gut 3,5 Stunden neben dem Lauf.

**How to avoid:**
Vor der Anfahrt eine Zeitrechnung aufstellen, die von der gemessenen Laufzeit ausgeht, nicht von der erhofften. Drei Stellschrauben, von denen mindestens eine gezogen werden muss:
- Deckel auf mindestens 31 Stunden setzen (26h37 plus 3,5 h plus Reserve) und die Kosten entsprechend (bei 0,1158 USD/h sind 31 Stunden rund 3,59 USD).
- Oder den Wirkungsbeleg auf einem Teilkorpus fahren und die Aussage entsprechend enger fassen. Das kostet Vergleichbarkeit gegen die 26h37 und muss der Owner entscheiden.
- Oder den Volllauf detached ueber Nacht fahren (in v1.1 bewaehrt) und alle Messungen davor und danach so buendeln, dass keine Box-Stunde auf einen Menschen wartet.
Der Deckel ist ein Owner-Checkpoint. Ein Vorschlag, der arithmetisch nicht aufgehen kann, gehoert nicht in einen Plan.

**Warning signs:**
Im Plan steht ein Deckel ohne eine Zeile, die die gemessene Vorlaufzeit nennt. Die Anfahrt beginnt ohne fertigen Ablaufplan als Datei.

**Phase to address:**
Messphase, im Checkpoint-Plan vor der Anfahrt.

---

### Pitfall 16: Die Vergleichbarkeit gegen die v1.1-Grundlinie bricht an fuenf Stellen gleichzeitig

**What goes wrong:**
Der neue Volllauf dauert 20 Stunden, die Freude ist gross, und die Zahl bedeutet nichts, weil sich neben dem gemessenen Fix noch vier andere Dinge geaendert haben.

**Why it happens:**
Der Bericht von v1.1 nennt die Stoerfaktoren selbst, und sie sind alle unauffaellig:
1. **Startzustand.** Beim Anstoss des v1.1-Laufs lagen bereits **1.653 Dateien im Index**; ein Lauf von null haette laenger gebraucht. Der Snapshot `snap-03f1d1d9ad9262704` enthaelt Korpus **und** die fertigen Indizes. Wer ihn einspielt und "Volllauf" startet, misst unter Umstaenden einen Resume ueber 52.000 fertige Zeilen.
2. **Cron-Intervall.** Der ganze Laufzeitzuwachs von 40,6 Prozent war Zulauf: das Arbeitsvorrat lief 5,85 Stunden lang trocken (194 von 812 Statuslesungen), weil `StorageCrawlJob` nur beim System-Cron vorrueckte und der auf jener Instanz **alle 12 Minuten** lief statt alle 5. Auf einer neu aufgebauten Box mit 5-Minuten-Cron waere ein Teil der Verbesserung die Box und nicht der Fix.
3. **Der Fix selbst.** Die Top-up-Route fuehrt jetzt Crawl-Scheiben **inline** aus, mit 20 Sekunden Budget unter einem OCS-Aufruf. Die dabei verbrauchte PHP-Zeit steht im Leerlauf des Containers und gehoert in die Durchsatzrechnung.
4. **Das Lastwerkzeug.** Wenn es fuer v1.2 korrigiert wird (und das muss es, siehe Pitfall 18), sind die v1.1-Stufenzahlen zu guenstig und die v1.2-Zahlen ehrlich. Ein direkter Vergleich stellt eine Verschlechterung dar, die eine Korrektur ist.
5. **Der Seitencache des Wirts.** Er hat die Kaltstart-Reproduktion vom 10.09. vollstaendig erklaert: derselbe Vorgang lag einmal bei 1.838 ms und einmal bei 1.598 ms, weil der letzte Start einmal 29 Stunden und einmal Minuten zurueck lag.

**How to avoid:**
- Der Wiederaufbau-Runbook-Erstvollzug ist die Gelegenheit, jede dieser fuenf Groessen **abzulesen und zu protokollieren**, bevor der Lauf startet: Zeilenstaende von `state.db` (indexiert/uebersprungen/fehlgeschlagen), Cron-Intervall der Instanz, Instanztyp, harte Containergrenze, Zeit seit dem letzten Containerstart.
- Der Wirkungsbeleg wird **mit derselben Schalterstellung wie v1.1** gefahren, also mit abgeschalteter Modell-Entladung. Sonst misst er zwei Aenderungen auf einmal (siehe Pitfall 19).
- Wo Vergleichbarkeit nicht herstellbar ist, wird die Zahl als **Erstmessung** gefuehrt und nicht als Vergleichszeile. v1.1 hat das fuer die Sprachfaelle und die Seitenroute genau so gemacht, und es war der Grund, warum der Bericht ohne Beanstandung abgenommen wurde.

**Warning signs:**
Der Durchsatz liegt in den ersten Minuten unplausibel hoch (Resume statt Neubau). Im Bericht steht eine Prozentzahl ohne die Nennung des Startzustands. Das Wort "Grundlinie" steht neben einer Zahl, die mit einem anderen Werkzeug erhoben wurde.

**Phase to address:**
Messphase, und zwar im Runbook selbst, damit die Ablesungen erzwungen und nicht erinnert werden.

---

### Pitfall 17: Gemessen wird die Aufwaermphase, nicht das Erzeugnis

**What goes wrong:**
Die Wiederaufwaerm-Kosten der Entladung werden gemessen, sie betragen 300 ms, alle sind zufrieden. Auf einer Instanz, die das Modell nicht im Seitencache hat, sind es 1.800 ms und die Aufrufdecke reisst.

**Why it happens:**
Derselbe Mechanismus wie in Pitfall 16 Punkt 5, hier aber als eigenstaendige Falle, weil die Entladefunktion genau diese Groesse zur Kennzahl macht. Dazu kommt der Klassiker: die ersten Anfragen einer Lastreihe treffen einen Container, dessen Reader-Konfiguration, Analysekette (23-MB-Automat aus der Konstituentenliste) und Degradiert-Verdikt noch nicht gebaut sind. Die Verdikt-Zwischenspeicherung hat fuenf Sekunden TTL, was bei kurzen Stufen genau in die Messung faellt.

**How to avoid:**
- Jede Kaltstartzahl traegt den Zustand des Seitencaches mit sich: entweder wurde er geleert (dokumentierter Befehl im Runbook) oder es steht dabei, wie lange der letzte Start zurueckliegt. Der Bericht von v1.1 formuliert die Lehre bereits als Satz, der uebernommen werden kann: eine Gesamtdauer ueber 1,5 s ist kein Beweis fuer einen Abbruch, und eine darunter keiner fuer das Gegenteil.
- Lastreihen bekommen Aufwaermrunden, die verworfen werden, und die Zahl der verworfenen Runden steht im Bericht.
- Fuer die Entladung wird **beides** gemessen: warm (Seitencache haelt die Gewichte) und kalt (Seitencache geleert). Die Store-Aussage darf sich nur auf die schlechtere stuetzen.

**Warning signs:**
Zwei Laeufe derselben Messung unterscheiden sich um mehr als das Rauschband von fuenf Prozent. Eine Kaltstartzahl steht ohne Zeitangabe im Bericht.

**Phase to address:**
Messphase (Protokoll im Runbook), Entladephase (die zu messende Groesse ist definiert, bevor die Box angefahren wird).

---

### Pitfall 18: Das Messwerkzeug zaehlt Ausfaelle als Erfolge

**What goes wrong:**
Stufe 16 der Nebenlaeufigkeitsreihe meldet `"failures": 0` bei 160 Anfragen, waehrend das Nextcloud-Protokoll im selben Fenster **17 abgebrochene Containeraufrufe** mit `cURL error 28` verzeichnet. Die Route antwortet bei einem abgebrochenen Containeraufruf mit HTTP 200 und einer Ergebnisgruppe ohne Containerteil, also zaehlt das Werkzeug sie als beantwortet. Fuer 10,6 Prozent der Anfragen hat die gemessene Antwortzeit nicht die Zeit einer vollstaendigen Antwort gemessen.

**Why it happens:**
Das Werkzeug misst HTTP-Status, und der Status ist ehrlich: die Unified Search soll nicht die ganze Suche verlieren, wenn ein Provider schweigt. Die Messfrage ist eine andere als die Produktfrage, und das Werkzeug kennt nur die eine.

**How to avoid:**
- Jede Stufe wird gegen eine **unabhaengige Quelle** aufgerechnet: das Nextcloud-Protokoll im selben Zeitfenster. Das ist bereits als Lehre 3 in der Retrospektive festgehalten.
- Der Fingerabdruck wird mitgefuehrt und ausgewertet: **Treffer je Anfrage.** 5,40 auf den Stufen 1 und 4, 4,16 auf Stufe 16. Eine Stufe, deren Trefferdichte faellt, ist verdaechtig, auch bei `failures: 0`.
- Wird das Werkzeug korrigiert, gilt Pitfall 16 Punkt 4: die alten Stufenzahlen sind nicht mehr vergleichbar, und der Bericht sagt das, statt eine Korrektur als Regression darzustellen.
- Und der zweite Teil derselben Lehre: **Skripte, die auf der Box laufen, muessen vorher auf der Box gelaufen sein.** In v1.1 mussten zwei Messskripte waehrend des Laufs korrigiert werden, weil `sudo` die Umgebung raeumt und `docker exec` keine weitergibt, sodass `OC_PASS` nirgends ankam. Das gehoert in die Wellen ohne Box-Zeit, vor die Anfahrt.

**Warning signs:**
`failures: 0` bei steigender Nebenlaeufigkeit und fallender Trefferdichte. Ein Messskript wird waehrend eines laufenden Deckels editiert.

**Phase to address:**
Messphase, in der Vorbereitungswelle ohne Box-Zeit.

---

### Pitfall 19: Eine Anfahrt, zwei Aenderungen, keine zurechenbare Zahl

**What goes wrong:**
Der Owner-Entscheid lautet: EINE Box-Anfahrt fuer alles. Wenn in diesem einen Lauf sowohl der DI-10-04-Fix als auch die Modell-Entladung und womoeglich noch der Filter aktiv sind, ist keine der drei Aenderungen zurechenbar. Der Lauf produziert eine Gesamtzahl und keinen Beleg.

**Why it happens:**
Der Kostendruck ist real und der Entscheid ist richtig. Falsch waere nur, aus "eine Anfahrt" auf "ein Lauf" zu schliessen. Eine Anfahrt kann mehrere Zustaende messen, wenn die Zustaende umschaltbar sind.

**How to avoid:**
- Die Modell-Entladung bekommt einen **Schalter, der ab Werk aus ist** (Umgebungsvariable, Muster `FINDLING_*`, wie alle anderen Stellschrauben). Damit kann dieselbe Box denselben Korpus in zwei Zustaenden messen, und der Wirkungsbeleg fuer DI-10-04 laeuft mit dem Schalter aus, also vergleichbar zu v1.1.
- Der Filter aendert an Durchsatz und Grundlast nichts und darf mitlaufen, aber seine eigenen Messungen (gefilterte Suche, Sortierung, DI-07-03 unter Sortierung) sind eigene Messbloecke mit eigenen Rohdateien.
- Daraus folgt eine Reihenfolge fuer die Roadmap: **Filter und Entladung werden VOR der Messphase gebaut**, die Entladung hinter dem Schalter, und die Messphase misst beide Zustaende in einer Anfahrt. Umgekehrt waere die Entladung ungemessen im Store.

**Warning signs:**
Im Messplan steht ein Lauf und drei Fragen. Es gibt keine Umgebungsvariable, mit der sich die Entladung abschalten laesst.

**Phase to address:**
Roadmap-Reihenfolge (Filterphase und Entladephase vor der Messphase), Entladephase fuer den Schalter, Messphase fuer den Ablaufplan.

---

### Pitfall 20: Der Minor-Sprung ohne Migration, zum zweiten Mal

**What goes wrong:**
v1.2 aendert die Datenbank nicht, also braucht es keine Migration. Bestandsinstallationen suchen nach dem Upgrade stumm ins Leere, und niemand merkt es, weil frische Installationen funktionieren.

**Why it happens:**
Genau dieser Fehler wurde in v1.1 gefunden, und zwar erst in der Haertungsphase durch den Ende-zu-Ende-Upgrade-Beweis 1.0.3 auf 1.1.0 in CI. Die Lehre steht als Muster in der Retrospektive: **jeder Minor-Versionssprung braucht eine PHP-Migration** (Muster `Version001100Date20260911000000`). Die Versuchung, sie wegzulassen, ist bei einem Milestone, der ausdruecklich index-kompatibel bleiben will, besonders gross, weil "keine Schemaaenderung" sich wie "keine Migration" anhoert.

**How to avoid:**
`Version001200Date2026....php` wird angelegt, auch wenn sie fachlich nichts tut, und der Upgrade-Beweis 1.1.0 auf 1.2.0 laeuft in `deploy-harp` Ende zu Ende, wie in v1.1. Dazu die uebrigen Release-Regeln des Projekts, die alle schon einmal Geld oder Zeit gekostet haben: beide Haelften fuehren dieselbe Major und Minor; eine Messzahl steht an genau drei Stellen (README.en.md und beide info.xml) und ein Gate haelt die Wortlaute zusammen; der Store-Tag wird nie verschoben; das Vokabular-Gate laeuft vor dem Push.

**Warning signs:**
Im Release-Plan fehlt eine Migrationsdatei. Der Upgrade-Workflow wird uebersprungen, weil "sich nichts an der Datenbank geaendert hat".

**Phase to address:**
Haertungsphase, als blockierender Schritt vor der Einreichung.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Dropdown schreibt `type:pdf` in die Suchzeile | eine Zeile Code, kein Protokollumbau | Semantik ist unter jedem Filter aus, unsichtbar; spaeterer Rueckbau beruehrt vier Aufrufstellen | nie |
| Filter in PHP hinter dem Recheck | keine Containeraenderung, kein neuer Parameter | halbleere Seiten, luegender Pager, auf grossem Bestand systematisch leere Ergebnisse | nie |
| Sortierung als zusaetzliches Argument in `_sides` durchgereicht | zwei Zeilen | `Candidate.score` traegt Zeitstempel, RRF fusioniert Datum mit Semantik | nie |
| Trefferzahlen je Dateityp anzeigen | bessere Oberflaeche | Fast-Field auf `ext`, Schemaaenderung, Reindex von 52.000 Dokumenten, D-04 gebrochen | nur zusammen mit einer ohnehin faelligen Schemaaenderung, also fruehestens v2 |
| `engine.reset()` als Entladefunktion wiederverwenden | die Funktion existiert schon | zweiter Besitzer im Poller, doppelte Engine, 276-MB-Regression von 06.1-02 zurueck | nie |
| Entladung ohne Schalter ausliefern | eine Konfiguration weniger | die eine Box-Anfahrt kann A/B nicht messen, der Wirkungsbeleg wird unzurechenbar | nie in v1.2 |
| Nur die ONNX-Sitzung entladen, Tokenizer behalten | einfacher, kein Poller-Umbau | der groessere Posten (544 MB) bleibt stehen, die Kennzahl enttaeuscht | als bewusst benannte erste Stufe, wenn die Zahl trotzdem ausgewiesen wird |
| Aufrufdecke von 1,5 s anheben, statt lexikalisch zu antworten | Kaltstart reisst nicht mehr | der Dialog wartet auf einen Provider, die ganze Unified Search wird traege | nie fuer den Dialog; fuer die eigene Seite ist `PAGE_REQUEST_TIMEOUT_SECONDS` bereits getrennt und darf mit Messung bewegt werden |
| Messzahl ohne Angabe des Startzustands in den Bericht | kuerzerer Bericht | die Zahl ist im naechsten Milestone unbrauchbar, der Vergleich muss neu erhoben werden | nie |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Unified-Search-Dialog (`Provider.php`) | Dateityp als Filter deklarieren, weil er auf der eigenen Seite existiert | `getSupportedFilters` bleibt bei `BUILTIN_TERM` und `BUILTIN_TITLE_ONLY`; ein Name ohne `FilterDefinition` macht die ganze Providerliste kaputt, ein nicht deklarierter Filter laesst den Provider kommentarlos ueberspringen |
| `SearchRequest` im Container | neues Feld nur auf der PHP-Seite senden | `extra="forbid"` weist unbekannte Felder als HTTP 400 ab, die Suche bricht komplett; das Feld muss im Modell deklariert sein, und die Nutzerkennung kommt weiter nur aus dem signierten Header |
| `/snippets` | neuen Anfrageparameter vergessen | jeder Parameter, der `build_query` beruehrt, reist zu beiden Routen, mit Gleichstand-Test nach Muster `test_search_limits_lockstep.py` |
| Tantivy `Searcher.search` | `order_by_field` setzen und Score weiterverwenden | gemessen: der Score wird zum Feldwert; unter Sortierung Score auf 0.0 setzen und RRF nicht anwenden |
| Tantivy-Schema | Sortierfeld nachtraeglich auf `fast` setzen | gemessen: nur `mtime`, `file_id`, `storage_id` sind `fast`; `ext` scheitert mit "is not configured as fast field"; alles andere kostet `SCHEMA_VERSION` und einen Reindex |
| `IMimeTypeDetector` gegen Index-`ext` | Filterkategorien ueber MIME denken | Kategorien als Endungsmengen definieren, weil nur `ext` im Index steht; `mimeType` bleibt fuer das Symbol zustaendig |
| Nextcloud-Cron auf der Messbox | Intervall nicht ablesen | Intervall protokollieren; der v1.1-Laufzeitzuwachs war zu grossen Teilen ein 12-Minuten-Cron |
| EBS-Snapshot `snap-03f1d1d9ad9262704` | einspielen und "Volllauf" starten | der Snapshot traegt Korpus UND fertige Indizes; Zeilenstaende aus `state.db` vor dem Start protokollieren, Index und `vectors.db` fuer einen echten Neubau entfernen |
| huggingface-hub / onnxruntime beim Nachladen | `HF_HUB_OFFLINE=1` als Beweis nehmen | die Variable ist ein Netz, kein Beweis; der Offline-Nachweis ist der `--network none`-Lauf in `docker.yml`, und er muss um einen Entlade- und Nachladezyklus erweitert werden |
| onnxruntime-Telemetriezeile | als Netzwerkverkehr lesen | "Failed to persist telemetry device ID" ist ein fehlgeschlagener lokaler Schreibvorgang, erscheint bei JEDER Sitzungserzeugung und taucht mit der Entladung nun wiederholt im Log auf; das gehoert dokumentiert, bevor ein Admin es meldet |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Filter hinter der Fusion | halbleere Seiten, `hasMore` trotzdem wahr | Filter als `Must`-Klausel vor dem ersten `searcher.search` | sobald die Treffermenge groesser ist als `SEARCH_RRF_WINDOW` = 100, also auf jeder echten Instanz |
| Seltener Dateityp treibt die Fortsetzungsschleife | Seitenaufbau naehert sich dem 3-s-Budget, Containeraufruf naehert sich 1,5 s | Filter in der Anfrage (dann filtert die Engine selbst), nicht in der Antwort | ab einigen zehntausend Dokumenten, wenn der gefilterte Typ selten ist |
| Datumssortierung auf grossem Fremdbestand | leere Seiten, 1,0 Runde je Suche, `FAILURE_ALL_CANDIDATES_REJECTED` | Verhalten messen und benennen; keine zweite Runde, kein groesseres Fenster kaufen | ab etwa dem Verhaeltnis des Messkorpus: wenige eigene Dateien gegen zehntausende fremde |
| Nachladen im Anfragepfad | `cURL error 28`, HTTP 200 ohne Containerteil, null Treffer ohne Fehlermeldung | waehrend des Nachladens lexikalisch antworten (D-19-Pfad), Laden im Hintergrund | bei jeder ersten Suche nach der Ruhefrist; gemessener Kaltstart 1.838,4 ms gegen Decke 1.500 ms |
| Entladung ohne Rueckgabe an das Betriebssystem | Grundlast faellt kaum, obwohl "entladen" | cgroup-`anon` vor und nach der Entladung messen, `malloc_trim(0)` pruefen, Tokenizer mit entladen | sofort, und es faellt nur auf der Box auf |
| Wiederholtes Laden statt Zwischenspeichern | `memory.events max` steigt (v1.1: von 2.796 auf 21.939), `memory.peak` erreicht die harte Grenze | Ruhefrist gross genug, Entladung nur im echten Leerlauf, Zaehler fuer Laden und Entladen ausweisen | auf der 2-GiB-Containergrenze der Zielbox, wo die Spitze schon heute exakt anliegt |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Filter oder Sortierung erst hinter dem PHP-Recheck anwenden | eine zweite Stelle entscheidet ueber Sichtbarkeit; `test_php_acl_boundary.py` zaehlt Aufrufstellen und faellt, oder faellt nicht und die Grenze ist trotzdem doppelt | Filter in der Container-Anfrage, oberhalb des einen Vorfilters; die Zahl der Aufrufstellen bleibt zwei |
| Zweite Route fuer Filterdaten oder Sortierung | `NoAdminRequired` und `NoCSRFRequired` muessten erneut begruendet werden; Trust-Boundary-Gate | eine Route, ein Dokument, Parameter in der bestehenden Adresse |
| Trefferzahl je Typ oder Gesamtzahl anzeigen | ein Zaehler vor dem Recheck ist eine Aussage ueber Dokumente anderer Leute (Zaehl-Orakel T-02-93) | kein Total, wie bisher; `hasMore` genuegt; falls gezaehlt wird, dann nur ueber bestaetigte Treffer der geladenen Seite |
| Neuer Parameter wird in `Candidate` mitgeschickt (etwa die Endung) | Aussage ueber ein Dokument vor dem Recheck; der Feldmengen-Test geht rot | `Candidate` bleibt bei drei Feldern; Endung und Name kommen aus dem bestaetigten Knoten |
| Sortier- oder Filterwert landet in einer Logzeile | Filterwert ist zwar kein Suchbegriff, aber eine Fehlerzeile des Parsers zitiert die Eingabe | weiterhin nur Typnamen loggen, nie Eingaben; Parserfehler bleiben auf `debug` |
| Nachladen des Modells oeffnet einen Socket | das Privacy-Versprechen des Store-Textes | Offline-Probe in `docker.yml` um einen Entlade- und Nachladezyklus erweitern, weiter mit `--network none` |
| Entladung schreibt in den Nutzerdatenbereich (Zwischenspeicher, Cache-Datei) | Nur-Lesen-Invariante auf Nutzerdateien | die Entladung braucht keinen Speicherort; nichts wird ausgelagert |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Filter ohne Suchbegriff | `build_query` gibt `query=None` zurueck, die Seite zeigt nichts, und das sieht kaputt aus | die Seite sagt in einem Satz, dass ein Suchbegriff noetig ist; ein Filter allein fragt nach allen PDFs der Instanz in keiner sinnvollen Reihenfolge und wird bewusst nicht beantwortet |
| `<select onchange="this.form.submit()">` | ohne JavaScript ist die Seite unbedienbar; der Entwurfsvertrag sagt, dass Suchen, Blaettern, Filtern, Oeffnen und Zurueckkehren ohne Skript funktionieren | Auswahlfelder im bestehenden Formular plus sichtbare Absendeschaltflaeche, oder Links, die alle vier Adresswerte selbst setzen |
| Filterwechsel behaelt die Seitennummer | Sprung mitten in eine fremde Ergebnismenge, ohne Hinweis | jeder Wechsel setzt `page=1` und leert `cursors` |
| Sortierung wird angeboten, aber die Relevanz verschwindet ohne Hinweis | Nutzer glauben, die Suche sei schlechter geworden | die Seite benennt die aktive Sortierung; wenn unter Sortierung die Semantik entfaellt, steht das dort, wo es gelesen wird |
| Leere gefilterte Seite ohne Unterscheidung | "kaputt" statt "in dieser Runde war nichts fuer Sie dabei" | die drei bestehenden Failure-Zustaende bleiben erhalten und bekommen unter Filter und Sortierung eigene Formulierungen in EN/DE/FR |
| Neue Bedienelemente ohne Beschriftung fuer Screenreader | die Seite hat heute genau eine h1 und benannte Bereiche; eine unbeschriftete Auswahl faellt aus der Struktur | Beschriftungen wie bei `findling-search-names`, und die Kataloge im Gleichstand |

---

## "Looks Done But Isn't" Checklist

- [ ] **Dateityp-Filter:** oft fehlt die Wirkung VOR dem Fusionsfenster; pruefen mit einem Korpus, in dem der gefilterte Typ jenseits von Rang 100 liegt
- [ ] **Dateityp-Filter:** oft fehlt der Fall "Datei ohne Endung" und "Endung in Grossschreibung"; pruefen mit `.JPG` und einer Datei ohne Punkt im Namen
- [ ] **Dateityp-Filter:** oft fehlt die Weitergabe an `/snippets`; pruefen, ob der Ausschnitt mit derselben Anfrage geschnitten wurde, die gerankt hat
- [ ] **Sortierung:** oft fehlt, dass der Score zum Feldwert wird; pruefen, welchen Wert `Candidate.score` unter Sortierung traegt
- [ ] **Sortierung:** oft fehlt der Fall "grosser Fremdbestand"; pruefen mit dem Messkorpus, nicht mit zwanzig Dateien
- [ ] **Blaetterung:** oft fehlt die Entwertung des Cursor-Pfads bei Filterwechsel; pruefen mit einer von Hand zusammengesetzten Adresse
- [ ] **Modell-Entladung:** oft fehlt die Zahl von der Box; pruefen mit cgroup-`anon` vor und nach der Entladung auf arm64
- [ ] **Modell-Entladung:** oft fehlt der Tokenizer (544 MB); pruefen, ob `poller._chunker` nach der Entladung noch steht
- [ ] **Modell-Entladung:** oft fehlt das Verhalten der ersten Suche danach; pruefen, ob sie lexikalisch antwortet oder auf das Laden wartet
- [ ] **Modell-Entladung:** oft fehlt der Schalter; pruefen, ob die Funktion ab Werk aus ist und in einer Anfahrt A/B messbar bleibt
- [ ] **Admin-Seite:** oft fehlt eine der sechs Gleichstand-Stellen des Engine-Zustands; pruefen, ob die Seite den Ausweichsatz zeigt
- [ ] **Messung:** oft fehlt der Startzustand im Bericht; pruefen, ob Zeilenstaende, Cron-Intervall und Zeit seit letztem Start protokolliert sind
- [ ] **Messung:** oft fehlt die Gegenrechnung gegen das Nextcloud-Protokoll; pruefen, ob jede Laststufe ihre Abbruchzahl traegt
- [ ] **Release:** oft fehlt die Migration fuer den Minor-Sprung; pruefen mit dem Ende-zu-Ende-Upgrade 1.1.0 auf 1.2.0 in CI
- [ ] **Release:** oft fehlt eine der drei Stellen fuer eine Messzahl; pruefen mit dem Wortlaut-Gate ueber README.en.md und beide info.xml

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Filter wirkt hinter der Fusion (ausgeliefert) | MEDIUM | Filter in die Anfrage ziehen, Patch-Release; keine Datenaenderung, kein Reindex, aber eine neue Store-Einreichung mit Migration |
| Sortierung schreibt Zeitstempel in `score` | LOW | Score unter Sortierung auf 0.0 setzen; nichts Persistentes betroffen |
| Sortierung nach Name zugesagt, Fast-Field fehlt | HIGH | entweder Zusage zuruecknehmen (Store-Text reist mit dem Release und ist nicht editierbar, also nur per neuer Version) oder Schemaaenderung mit Reindex ueber den ganzen Bestand |
| Cursor-Pfad ueberlebt Filterwechsel | LOW | Fingerabdruck einfuehren, Rueckfall auf Seite eins; rein serverseitig |
| Entladung gibt nichts zurueck | LOW bis MEDIUM | Funktion hinter dem Schalter lassen, ab Werk aus, Zahl im Bericht ehrlich ausweisen; das ist ein legitimer Ausgang und kein Fehlschlag |
| Entladung erzeugt zwei Engines | MEDIUM | Halter zur einzigen Quelle machen, Poller-Referenz entfernen, `load_count`-Differenz als Gate; Symptom ist Speicher, nicht Datenverlust |
| Kaltstart-Klippe im Feld | MEDIUM | Schalter ab Werk aus schaltet die Funktion fuer alle Bestandsinstallationen ab, ohne Release; danach lexikalische Antwort waehrend des Ladens nachliefern |
| Messdeckel gerissen | LOW | Owner entscheidet (in v1.1 auf 34 h angehoben); Voraussetzung ist, dass der Stand jederzeit ablesbar ist, also Kostenablesung im Runbook |
| Volllauf misst einen Resume statt eines Neubaus | HIGH | zweite Anfahrt noetig, ausser die Zeilenstaende wurden protokolliert und erlauben eine Korrekturrechnung |
| Minor-Sprung ohne Migration ausgeliefert | MEDIUM | in-place-Reparatur der Store-Version ueber den Update-Endpunkt plus zusaetzliche neue Version, damit Bestandsinstallationen das Update sehen; Tag nie verschieben |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 Filter hinter der Fusion | Filterphase | Test mit Treffern jenseits von Rang 100; jedes gefilterte Dokument der ungefilterten Liste taucht auf |
| 2 `type:` in der Suchzeile schaltet Semantik ab | Filterphase (erster Plan) | Diagnoseroute meldet unter Filter eine nicht leere semantische Liste, wenn so entschieden wurde |
| 3 Parameter erreicht `/snippets` nicht | Filterphase | Gleichstand-Test ueber beide Request-Modelle, Rot-Faehigkeit per Mutation |
| 4 Sortierung in der Fusion, Score wird Zeitstempel | Filterphase | Test auf `Candidate.score` unter Sortierung; Treffermengenvergleich sortiert gegen unsortiert |
| 5 Sortierfeld braucht Reindex | Filterphase (Vorpruefung vor Plan 1) | Probe gegen tantivy 0.26.0; Upgrade-Beweis zeigt unveraenderte Indexmarken |
| 6 Cursor-Pfad ueberlebt Filterwechsel | Filterphase | PHP-Unit-Test mit fremdem Cursor-Pfad erwartet Seite eins |
| 7 Zweite Tuer an der Berechtigungsgrenze | Filterphase, Audit in der Haertungsphase | `test_php_acl_boundary.py` zaehlt weiter zwei Aufrufstellen; keine neue Zeile in `routes.php` |
| 8 MIME gegen Endung | Filterphase | Korpusfall mit `.jpeg`, `.JPG`, ohne Endung, umbenannt |
| 9 Sortierung auf Fremdbestand liefert leer | Filterphase (Verhalten), Messphase (Zahl) | Rundenzaehlung und Failure-Zustand unter beiden Sortierungen gemessen |
| 10 RSS kommt nicht zurueck | Entladephase (Vorpruefung) | cgroup-`anon` vor und nach der Entladung auf arm64, mit Rohdatei |
| 11 Zwei Besitzer der Engine | Entladephase | `load_count`-Differenz ueber einen Entlade- und Nachladezyklus mit gleichzeitiger Suche |
| 12 Kaltstart-Klippe | Entladephase (Verhalten), Messphase (Zahl) | erste Suche nach der Ruhefrist antwortet lexikalisch und unter der Decke |
| 13 Sechster Engine-Zustand | Entladephase (Entscheid), Haertungsphase (Kataloge) | vier Katalog-Gates gruen, Admin-Seite zeigt nie den Ausweichsatz |
| 14 one-load-Beweis entwertet | Entladephase (erster Plan) | umformulierte Invariante, Rot-Faehigkeit per Mutation belegt |
| 15 Messdeckel kleiner als der Lauf | Messphase (Checkpoint-Plan) | Zeitrechnung mit gemessener Vorlaufzeit im Plan, Owner-Freigabe |
| 16 Vergleichbarkeit bricht | Messphase (Runbook) | fuenf Ablesungen protokolliert, bevor der Lauf startet |
| 17 Messen in der Aufwaermphase | Messphase (Protokoll), Entladephase (Messgroesse) | jede Kaltstartzahl traegt den Seitencache-Zustand |
| 18 Werkzeug zaehlt Ausfaelle als Erfolge | Messphase (Welle ohne Box-Zeit) | jede Laststufe mit Abbruchzahl aus dem Nextcloud-Protokoll und Trefferdichte |
| 19 Eine Anfahrt, zwei Aenderungen | Roadmap-Reihenfolge, Entladephase (Schalter) | Entladung abschaltbar, Wirkungsbeleg mit Schalter aus gefahren |
| 20 Minor-Sprung ohne Migration | Haertungsphase | Upgrade 1.1.0 auf 1.2.0 Ende zu Ende in `deploy-harp` |

**Reihenfolge-Empfehlung, die sich aus der Tabelle ergibt:** Filterphase und Entladephase (Entladung hinter einem Schalter, ab Werk aus) VOR der Messphase, Haertungsphase zuletzt. Begruendung: die eine bezahlte Box-Anfahrt ist die einzige Gelegenheit, den Wiederaufwaerm-Preis und die vier regressiven Laststufen auf Zielhardware zu messen, und sie kann beide Schalterstellungen messen, wenn es den Schalter gibt. Umgekehrt ginge die Entladung ungemessen in den Store, und der DI-10-04-Wirkungsbeleg waere durch eine zweite gleichzeitige Aenderung entwertet.

---

## Sources

**Projektinterne Quellen (HIGH, am Baum gelesen am 14.09.2026):**
- `backend/src/findling/index/search.py` (Fusionsfenster, Vorfilter-Baender, Fortsetzung hinter dem Fenster, Offset-Semantik, `snippets_for`)
- `backend/src/findling/index/fusion.py` (RRF, Gewichte, Distanzriegel), `backend/src/findling/index/schema.py` (neun Felder, welche `fast` sind)
- `backend/src/findling/query/rewrite.py` (`extract_filters`, `carried_operators`, `carries_one_term`, `_extension_query`)
- `backend/src/findling/api/search.py` (`extra="forbid"`, `lexical_only`, `Candidate` mit drei Feldern), `backend/src/findling/api/snippets.py`, `backend/src/findling/api/resources.py`
- `backend/src/findling/embed/model.py` (Lock-Grenzen, `LOAD_RETRY_SECONDS`, `_LOAD_COUNT`, `enable_cpu_mem_arena=False`), `backend/src/findling/embed/engine.py` (Halter, `reset()`, fuenf Zustaende), `backend/src/findling/worker/poller.py` (`_build_the_cutter`, zweite Referenz)
- `php/lib/Service/SearchService.php` (die eine Berechtigungsentscheidung, Runden, Budgets), `php/lib/Controller/PageController.php` (`cursorPath`, `nextUrl`, `PAGE_SIZE`, `MAX_PAGE`), `php/lib/Search/Provider.php` (`getSupportedFilters`, `getCustomFilters`), `php/lib/Service/ExAppService.php` (`REQUEST_TIMEOUT_SECONDS = 1.5`), `php/lib/Service/CrawlAdvanceService.php` (DI-10-04-Analyse im Klassenkopf), `php/lib/Service/AdminViewService.php`, `php/templates/search.php`, `php/js/search.js`
- `backend/tests/test_admin_ui_contract.py` (die vier Katalog-Gates), `.github/workflows/docker.yml` (Offline-Probe mit `--network none`, Telemetriezeile), `.github/workflows/resilience.yml` (one-load-Schritt)
- `docs/measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md` (alle Messzahlen dieses Dokuments: Grundlast 103,2 MB, Spitze 1.764,2 MB, `memory.events max` 21.939, p95-Reihe ueber fuenf Stufen, Kaltstart 1.838,4 ms, 17 Abbrueche gegen `failures: 0`, Sprachfall-Diagnose, Laufzeit 26 h 37 min, Kostendeckel)
- `.planning/RETROSPECTIVE.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/PROJECT.md`, `CLAUDE.md` (RAM-Budget-Tabelle mit den 544 MB fuer Tokenizer und Splitter)

**Eigene Messung (HIGH):**
- Probe gegen die installierte `tantivy 0.26.0` in `backend/.venv`, gefahren am 14.09.2026: `order_by_field="mtime"` funktioniert auf dem i64-Fast-Field, auch mit `offset` und `Order.Asc`; der zurueckgegebene Score ist der Feldwert (500/300/200/100) statt des BM25-Werts (0,1363/0,1220); `order_by_field="ext"` scheitert mit `Field "ext" is not configured as fast field`; ein unbekanntes Feld mit `Field 'nope' is not defined in the schema`

**Externe Quellen (MEDIUM):**
- [Elasticsearch, Reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) (feste `rank_window_size` als Grundlage konsistenter Blaetterung)
- [Paginating hybrid search on Postgres, and why the obvious fix is worse](https://dev.to/pavangupta352/paginating-hybrid-search-on-postgres-and-why-the-obvious-fix-is-worse-2kmd) (Limit je Quelle vor der Fusion; verschwundene und doppelte Zeilen ueber Seiten hinweg)
- [OpenSearch, Introducing reciprocal rank fusion for hybrid search](https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/)
- [onnxruntime Issue 26831: memory not released by ReleaseSession or ReleaseEnv](https://github.com/microsoft/onnxruntime/issues/26831)
- [malloc internals: why free() doesn't return memory to the system](https://dev.to/piotrek1372/malloc-internals-why-free-doesnt-return-memory-to-the-system-33pc) (glibc-Arena, `malloc_trim`)
- [tantivy-py Tutorials](https://tantivy-py.readthedocs.io/en/latest/tutorials.html) und [tantivy::collector](https://docs.rs/tantivy/latest/tantivy/collector/index.html) (Sortierung ueber Fast-Fields)

---
*Pitfalls research for: Findling v1.2 (Messbeleg und Ausbau)*
*Researched: 2026-09-14*
