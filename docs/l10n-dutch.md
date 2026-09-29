# Niederländische Wortlaute, vollständig

Diese Datei ist die Quelle der beiden niederländischen Katalogdateien `php/l10n/nl.json` und
`php/l10n/nl.js`. Sie trägt die niederländischen Wortlaute für **alle** Schlüssel der Adminseite
und der Ergebnisseite, in einer Tabelle, damit ein Leser sie in einem Durchgang prüfen kann und
nicht als Diff über zwei Dateien. Aus dieser Tabelle sind beide Dateien mechanisch entstanden,
ohne zweite Textrunde.

Was für **alle** Sprachdateien dieser Phase gilt, steht nicht hier, sondern einmal in
`docs/l10n-catalogues.md`: warum Nextcloud zehn Dateien und nicht fünf braucht (Abschnitt 1),
welche Regionalvarianten der Kern führt und welche Findling ausliefert (Abschnitt 2), die
wörtlichen Pluralregeln mit ihrer Herkunft (Abschnitt 3) und die Messung, aus der die Wahl der
Formen folgt (Abschnitt 4). Diese Datei verweist dorthin, statt den Beweis ein zweites Mal zu
führen.

**Niederländisch ist der Sonderfall dieser Phase, und zwar an zwei Stellen.** Beide gehören an
den Anfang, weil beide aussehen wie ein Fehler und keiner einer ist:

1. **Zwei Pluralformen, nicht drei.** Spanisch, Italienisch und beide portugiesischen Codes
   tragen `nplurals=3`, Niederländisch trägt `nplurals=2`. Wer die spanische Datei als Vorlage
   nimmt, schreibt drei Formen und legt damit eine Form ab, die die Regel nie adressiert.
   Vorlage dieses Katalogs ist deshalb `fr.json`, die andere Zwei-Formen-Sprache des Baums.
2. **Die Regelzeichenkette ist zeichengleich mit der deutschen.** Das ist die Regel beider
   Sprachen und kein Kopierfehler. Der Abschnitt "Pluralformen" führt es aus, und das Gate
   kennt den Fall seit Plan 20-02.

Wie der Kern für Italienisch führt der Kern auch für Niederländisch **keine Regionalvariante**:
die Dateiliste in Abschnitt 1 von `docs/l10n-catalogues.md` zeigt `nl.json` und `nl.js` und
nichts daneben. Der Abschnitt "Die benannte Grenze", den die spanische Datei braucht, hat hier
also keinen Gegenstand: es gibt nichts wegzulassen.

## Die Schlüsselmenge, aus der Datei gezählt

Nicht aus einem Dokument übernommen, sondern am 25.09.2026 mit `json.load` über
`php/l10n/de.json` und `php/l10n/nl.json` gezählt:

| Größe | Wert |
|---|---:|
| Schlüssel in `de.json` | **202** |
| Schlüssel in `nl.json` | **202** |
| davon mit printf-Direktiven (`%s`, `%1$s`, `%n`) | **40** |
| davon mit Direktiven, ohne die Pluralschlüssel | **35** |
| davon mit Pluralformen (Wert ist eine Liste) | **5** |
| Formen je Pluralschlüssel | **2** |
| Zeilen in der Tabelle unten | **202** |

Die vorletzte Zeile ist die, die diese Sprache von den beiden vorigen trennt: `docs/l10n-spanish.md`
und `docs/l10n-italian.md` tragen dort eine **3**. Sie steht hier in derselben Tabelle wie die
Schlüsselzahl, damit ein Leser sie nicht in der Prosa suchen muss.

Die Tabelle unten führt **202** Zeilen und nicht 201: wie in `docs/l10n-spanish.md` und
`docs/l10n-italian.md` und anders als in `docs/l10n-french.md` steht auch `Findling` darin, mit
sich selbst als Wortlaut. Er ist zugleich der erste Eintrag der Ausnahmeliste weiter unten.

## Wortwahl

Damit die Prüfung eine Entscheidung je Begriff ist und nicht 202 Einzelfälle. Die fünf
Entscheide, die der Plan verlangt, stehen in den ersten fünf Zeilen; die weiteren betreffen
jeweils Dutzende Zeilen und gehörten deshalb ebenso getroffen.

| Englisch | Niederländisch | Warum |
|---|---|---|
| the backend | de dienst | Derselbe Entscheid wie im Französischen (`le service`), Spanischen (`el servicio`) und Italienischen (`il servizio`). Der Nutzer sieht einen Dienst, der antwortet oder nicht antwortet. `de backend` wäre im Niederländischen sagbar, aber es benennt ein Bauteil und keine Zusage. Wo der Eigenname gemeint ist, bleibt er stehen: `de External App "Findling Backend"` |
| run (Lauf, Abgleichlauf, Hintergrundlauf) | doorloop, vergelijkingsdoorloop, achtergronddoorloop | `doorloop` ist ein Durchgang über einen Bestand und trägt dasselbe Bild wie `passage`, `pasada` und `passata`. Die zusammengesetzten Formen sind im Niederländischen regelmäßig und werden zusammengeschrieben. `ronde` verspricht eine Regelmäßigkeit, die der Abgleichlauf nicht hat, `uitvoering` ist das schwerere Wort für dieselbe Sache |
| worker | verwerkingsproces | Nach dem französischen `processus de traitement`, dem spanischen `proceso de tratamiento` und dem italienischen `processo di elaborazione`. `werker` wäre der Mensch, `worker` der Anglizismus, und beide sagen dem Verwaltungsnutzer weniger als die Umschreibung |
| index (Substantiv) | de index | Ein gewöhnliches niederländisches Wort mit Artikel `de`, im Plural `indexen`. Es braucht keine Umschreibung |
| index (Verb), indexing | indexeren, de indexering | Die Formen, die die niederländische Nextcloud-Oberfläche selbst führt. `indiceren` gibt es, meint aber das Zuordnen einer Kennzahl |
| coverage | dekking | Die Zahl, die sagt, welcher Anteil der Dateien durchsuchbar ist. `dekkingsgraad` wäre möglich und ist länger, ohne mehr zu sagen |
| background job | achtergrondtaak | Die Wortwahl der niederländischen Nextcloud-Oberfläche. Von `verwerkingsproces` unterscheidet sie sich deutlich genug, und beide Begriffe stehen nie im selben Satz |
| file | bestand, Plural bestanden | Das gewöhnliche Wort. `file` wäre im Niederländischen eine Verkehrsstockung, was dieser Katalog niemandem zumuten muss |
| storage | opslag, opslaglocatie, externe opslag | `opslag` ist der Vorgang und der Ort, `opslaglocatie` die einzelne Stelle, die durchgezählt wird. Beides ist die Wortwahl der niederländischen Oberfläche |
| folder | map, Plural mappen | Und nicht `directory`: die Oberfläche, in der diese Sätze stehen, sagt `map` |
| searchable, findable | doorzoekbaar, vindbaar op betekenis | Zwei Hälften derselben Aussage, deshalb zwei Formen desselben Baus |
| text recognition | tekstherkenning | OCR bleibt als Abkürzung stehen, wo der Quellstring sie führt |
| full text hits | treffers uit de volledige tekst | Und nicht `fulltext-treffers`: der Katalog stellt die volle Textsuche der Suche nach Bedeutung gegenüber, und beide Hälften lesen sich besser ausgeschrieben |
| Team Folders | Team Folders | Eigenname der Nextcloud-Funktion, in der niederländischen Oberfläche unübersetzt |
| remedy (die Abhilfe, oft nur `None.`) | `Geen.` | Das niederländische `geen` verneint ein Hauptwort und passt damit auf `geen oplossing`, ohne dass eine Form gewählt werden müsste |

**Die Anrede folgt Zeile für Zeile dem deutschen Bestand.** Das Deutsche wechselt innerhalb
dieses Katalogs zwischen der unpersönlichen Infinitivanweisung ("Den Wert unter ... erhöhen.")
und der Sie-Form ("Grenzen Sie die Suche ein."). Das Niederländische kann beides ebenso, also
steht dort, wo Deutsch den Infinitiv führt, der niederländische Infinitiv (`De waarde onder
"Grootste bestand om te lezen" verhogen.`) und dort, wo Deutsch siezt, die höfliche Form mit
`u` (`Verfijn de zoekopdracht om ze te zien.`, `Doorzoek de inhoud van uw bestanden`). Das ist
derselbe Entscheid wie im Italienischen: der Wechsel bleibt eine Eigenschaft der Quelle statt
eine Nachlässigkeit der Übersetzung, und wer ihn vereinheitlichen will, findet die Stellen im
deutschen Katalog und nicht hier.

Die Schaltflächen und kurzen Beschriftungen tragen die niederländische Oberflächenkonvention,
also den Infinitiv statt der Befehlsform: `Regels opslaan`, `Uitsluiting toevoegen`,
`Voorbeeldpaden tonen`, `Opnieuw proberen`. Das ist dieselbe Trennung, die das Deutsche
zwischen "Regeln speichern" und "Versuchen Sie es noch einmal" macht.

## Typografie

Jede Regel unten ist maschinell geprüft, das Ergebnis steht im Abschnitt "Maschinelle
Prüfungen".

- **Der Apostroph ist ausnahmslos der gerade ASCII-Apostroph** (U+0027), nie der
  typographische (U+2019). Das ist im Niederländischen keine Formalie, sondern die Regel, die
  am leichtesten reißt: die Sprache setzt den Apostroph im Alltag (`foto's`, `'s ochtends`,
  `auto's`, `Anna's map`), und genau dort schleppt eine maschinelle Übersetzung am
  zuverlässigsten U+2019 ein. Dieser Katalog kommt ohne eine einzige Apostrophstelle aus, und
  die Regel steht trotzdem hier, denn der nächste Plural auf `-o` kommt bestimmt. Gezählt über
  beide Dateien und über dieses Dokument: 0 Vorkommen von U+2019.
- **`één` und `een` sind zwei verschiedene Wörter, und der Unterschied ist bedeutungstragend.**
  `een` ist der unbestimmte Artikel, `één` das betonte Zahlwort. `Één bestand controleren` heißt
  "ein einziges Prüfen", `een bestand controleren` hieße "irgendeine Datei prüfen", und das ist
  in einer Diagnoseschaltfläche nicht dasselbe. Eine maschinelle Übersetzung glättet die beiden
  Akutakzente gern weg. Dieser Katalog führt sie an vier Stellen, alle vier absichtlich:
  `Één bestand controleren`, `De controle van één bestand ...`, `... is één keer mislukt ...`
  und `... leest elk bestand één keer.`
- **Kein geschütztes Leerzeichen**, weder U+00A0 noch das schmale U+202F. Sie sind unsichtbar,
  und ein Katalog voll unsichtbarer Zeichen ist ein Katalog, dessen Diff niemand liest.
- **Kein Gedankenstrich**, weder U+2014 noch U+2013. Das ist die Regel des Repositoriums und
  wird vom Prosa-Scanner über jede Katalogdatei gehalten.
- **Der Suchbegriff steht in geraden ASCII-Anführungszeichen**, also `"%s"`, genau wie die
  Bezeichner der Oberfläche und die Befehle: `"occ findling:index --restart"`,
  `"Uitgesloten mappen"`. Das ist ein Entscheid und eine Abweichung vom deutschen Bestand, der
  zwischen typographischen Anführungszeichen für den Suchbegriff und geraden für Bezeichner
  trennt. Grund: die niederländische Buchtypografie setzt einfache Anführungszeichen, und deren
  schließende Hälfte ist zeichengleich mit U+2019, das die Apostrophregel oben verbietet. Zwei
  Regeln, die einander widersprechen, sind schlechter als eine schlichte Schreibweise.
- **Die Platzhalter sind die des Schlüssels**, in Art und Zahl. `%1$s in %2$s` bleibt
  `%1$s in %2$s` und wird niemals `%s in %s`.
- **Ein literales Prozentzeichen wird `%%` geschrieben.** Der Grund ist gemessen und nicht
  befürchtet: Nextcloud reicht jeden Katalogwert durch `vsprintf`, ein nacktes `%` wirft dort
  einen `ValueError`, und die Seite bleibt weiß. **In diesem Katalog steht kein einziges
  Prozentzeichen dieser Art**, auch kein verdoppeltes: wo der deutsche Satz "100 Prozent" sagt,
  sagt der niederländische `honderd procent`. Umformulieren war hier billiger als retten, und
  der Satz liest sich besser als mit `%%`. Die Schreibregel steht trotzdem hier, denn die
  nächste Zeile, die eine Zahl mit Prozentzeichen braucht, kommt bestimmt.
- **Kein Pipe-Zeichen.** Nextcloud verbindet die Pluralformen damit; ein Wert, der es trägt,
  zerlegt sich selbst. `scan_pipe_character` aus Plan 20-03 hält das über jede Katalogdatei.

## Pluralformen

Die niederländische Regel lautet

```
nplurals=2; plural=(n != 1);
```

und steht wörtlich so als `"pluralForm"` in `php/l10n/nl.json` und als vierter Parameter von
`OC.L10N.register` in `php/l10n/nl.js`. Sie ist aus `docs/l10n-catalogues.md`, Abschnitt 3,
übernommen und nicht nachgetippt; dort steht auch, dass NC 34.0.3 und NC 35.0.0 für
Niederländisch dieselbe Zeichenkette führen.

**Die fünf Pluralwerte tragen zwei Formen und nicht drei.** Das ist der erste Unterschied zu
`docs/l10n-spanish.md` und `docs/l10n-italian.md`, die beide `nplurals=3` führen und deshalb
Form 1 und Form 2 wortgleich schreiben müssen. Diese Frage stellt sich hier nicht: die Regel
liefert die Indizes 0 und 1, mehr gibt es nicht zu füllen. Eine dritte Form wäre ein Eintrag,
den die Regel nie adressiert; die Browserseite von Nextcloud wertet die deklarierte Regel aus
und griffe damit auf einen Index, den sie nie bekommt. Das Formenzahl-Gate aus Plan 20-02 hält
das fest: `FORM_COUNT_OF["nl"]` ist 2, und die Zahl steht dort als eigene Zahl und wird nicht
aus `nplurals=` geparst.

**Die Zeichenkette ist zeichengleich mit der deutschen, und das ist richtig so.** Deutsch und
Niederländisch bilden den Plural nach derselben Regel: Singular bei genau eins, sonst Plural.
`core/l10n/de.json` und `core/l10n/nl.json` tragen deshalb dieselbe Zeile, gemessen auf beiden
Instanzen des Versionsfensters. Die Regel dieses Katalogs stammt **aus der niederländischen
Kerndatei** und nicht aus unserem deutschen Katalog; dass das Ergebnis gleich aussieht, ist
eine Eigenschaft der beiden Sprachen. Eine Maschine kann zwei gleiche Zeichenketten nicht nach
ihrer Herkunft auseinanderhalten, also ist dieser Absatz die Kontrolle und nicht ein Gate.

Genau dieser Fall ist der Grund, warum `scan_plural_rule` seit Plan 20-02 je Sprachcode urteilt.
Ein pauschaler Vorwurf "diese Datei trägt die deutsche Regel" wäre für `nl` dauerhaft rot, und
ein rotes Gate, das man zu Recht ignoriert, ist schlimmer als kein Gate. Gemessen am
25.09.2026, jetzt über eine Sprache, die es wirklich gibt:

| Aufruf | Ergebnis |
|---|---|
| `scan_plural_rule("nl.json", "nl", GERMAN_PLURAL_FORM)` | `[]`, kein Fund |
| `scan_plural_rule("es.json", "es", GERMAN_PLURAL_FORM)` | zwei Funde, darunter `es.json: carries the German plural rule, which is not the rule of es` |
| `scan_plural_rule("nl.json", "nl", "nplurals=3; plural=(n > 2);")` | ein Fund, die fremde Zeichenkette wird genannt |

Die dritte Zeile ist dabei die wichtige: dass das Gate für `nl` nicht pauschal schweigt, sondern
weiterhin eine falsche Regel findet. Der Kommentarabsatz über `L10N_NL_JSON` in
`backend/tests/test_admin_ui_contract.py` sagt dasselbe, damit niemand anfängt, den Scanner zu
reparieren.

Zwei niederländische Zusätze zu den Formen selbst:

- `%n uur` steht **zweimal gleich**, und das ist korrektes Niederländisch und keine vergessene
  Zeile. Maßangaben bleiben nach einem Zahlwort im Singular: `twee uur`, `drie kilometer`. Bei
  `minuut` und `dag` gilt das nicht, dort stehen `%n minuten` und `%n dagen`.
- `en nog %n` steht ebenfalls zweimal gleich, weil der Satz kein Hauptwort trägt, das sich
  beugen könnte. Der deutsche Bestand macht an derselben Stelle dasselbe ("und %n weitere").

In der Tabelle unten stehen die Formen eines Pluralschlüssels durch ` / ` getrennt in einer
Zelle, zuerst der Singular, wie es der französische, spanische und italienische Bestand machen.
Hier tragen **beide** Spalten zwei Formen, anders als in den beiden vorigen Sprachdateien, wo
die deutsche Spalte zwei und die andere drei führt.

## Die Tabelle

Alle drei Spalten sind aus `php/l10n/de.json` und `php/l10n/nl.json` erzeugt und nicht
abgetippt; die Reihenfolge ist die der Dateien. Die Spaltennamen sind ASCII, weil sie
Vertragsbezeichner sind und die Projektregel echte Umlaute der deutschen Prosa vorbehält. Der
Schlüssel ist der englische Quellstring: er steht wörtlich so im Template, läuft dort durch
`$l->t()` und ist in jeder Katalogdatei der Schlüssel der Übersetzung.

Kein Wert und kein Schlüssel kann ein Pipe-Zeichen enthalten, dafür sorgt `scan_pipe_character`
aus Plan 20-03. Diese Tabelle kann also nicht an einem Wortlaut zerbrechen.

| Schluessel | DE | NL |
|---|---|---|
| `Findling` | Findling | Findling |
| `File contents` | Dateiinhalte | Inhoud van bestanden |
| `Search coverage` | Deckungsgrad der Suche | Dekking van de zoekfunctie |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %1$s van %2$s indexeerbare bestanden zijn doorzoekbaar |
| `%s files are searchable. The count of indexable files is being updated, and the share is shown again afterwards.` | %s Dateien sind durchsuchbar. Die Zahl der indexierbaren Dateien wird gerade neu ermittelt, danach erscheint der Anteil wieder. | %s bestanden zijn doorzoekbaar. Het aantal indexeerbare bestanden wordt bijgewerkt; daarna verschijnt het aandeel weer. |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | Het aandeel is op dit moment niet te berekenen, omdat de dienst niet antwoordt. %s bestanden van deze instantie zijn indexeerbaar. |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | Bewust weggelaten: %s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | Deze bestanden zijn te groot, van een type dat Findling niet leest, of door een regel uitgesloten. Ze staan niet in de noemer hierboven, zodat de dekking honderd procent kan bereiken. |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | Voorlopig getal, %1$s van %2$s opslaglocaties zijn doorgeteld. |
| `Findable by meaning` | Auffindbar nach Bedeutung | Vindbaar op betekenis |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %1$s van %2$s indexeerbare bestanden zijn ook op betekenis te vinden |
| `Model: %1$s` | Modell: %1$s | Model: %1$s |
| `Model: %1$s, re-embedding %2$s (%3$s of %4$s)` | Modell: %1$s, Neueinbettung %2$s (%3$s von %4$s) | Model: %1$s, vectoren opnieuw berekenen %2$s (%3$s van %4$s) |
| `Economy` | Sparsam | Zuinig |
| `Standard` | Standard | Standaard |
| `Performance` | Leistung | Prestatie |
| `memory tight, memory.events max twice` | Speicher knapp, zweimal memory.events max | geheugen krap, twee keer memory.events max |
| `a slot was killed for lack of memory` | ein Slot wurde wegen Speichermangels beendet | een slot is wegens geheugentekort beëindigd |
| `the container ended during a multi slot pass` | der Container endete während einer Mehr-Slot-Staffel | de container stopte tijdens een ronde met meerdere slots |
| `Profile: chosen %1$s, in force %2$s (%3$s)` | Profil: gewählt %1$s, wirksam %2$s (%3$s) | Profiel: gekozen %1$s, actief %2$s (%3$s) |
| `OCR slots: %1$s of %2$s, memory tight` | OCR-Slots: %1$s von %2$s, Speicher knapp | OCR-slots: %1$s van %2$s, geheugen krap |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | Het semantische aandeel is op dit moment niet te berekenen. De dienst antwoordt niet, of meldt dit getal nog niet. |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | Het model staat in het geheugen, de semantische zoekfunctie antwoordt. |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | Het model wordt geladen zodra het voor het eerst nodig is. Dat is de normale toestand. |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | De semantische helft is uitgeschakeld in de instellingen van de container. |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | In dit image zit geen model. De zoekfunctie blijft treffers uit de volledige tekst leveren, de semantische helft blijft leeg. |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | Het laden van het model is één keer mislukt en wordt binnenkort opnieuw geprobeerd. Tot die tijd levert de zoekfunctie treffers uit de volledige tekst. |
| `The model was released to save memory. The next search answers with full text hits and loads it again in the background.` | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. | Het model is vrijgegeven om geheugen te sparen. De volgende zoekopdracht antwoordt met treffers uit de volledige tekst en laadt het op de achtergrond opnieuw. |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | Deze container meldt de toestand van het model nog niet. |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | Het zoeken in de volledige tekst dekt elk geïndexeerd document. Het zoeken op betekenis dekt het begin van elk document, en dit tweede getal loopt vol nadat de eerste indexering klaar is. |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | Actueel, laatst gecontroleerd %s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | De indexering komt al %s niet vooruit. In die tijd heeft noch een achtergrondtaak noch de dienst iets afgerond. |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | Er is nog geen achtergrondtaak van deze app gelopen. Mogelijk lopen de achtergrondtaken niet. |
| `Indexing is running.` | Die Indexierung läuft. | De indexering loopt. |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | De getallen konden niet worden ververst. De waarden hieronder zijn de laatste die deze pagina heeft ontvangen. |
| `_%n minute_::_%n minutes_` | %n Minute / %n Minuten | %n minuut / %n minuten |
| `_%n hour_::_%n hours_` | %n Stunde / %n Stunden | %n uur / %n uur |
| `_%n day_::_%n days_` | %n Tag / %n Tage | %n dag / %n dagen |
| `Waiting in the queue` | Wartet in der Warteschlange | Wacht in de wachtrij |
| `Being processed` | Wird gerade verarbeitet | Wordt verwerkt |
| `Indexed` | Indexiert | Geïndexeerd |
| `Skipped` | Übersprungen | Overgeslagen |
| `Failed` | Fehlgeschlagen | Mislukt |
| `Excluded` | Ausgeschlossen | Uitgesloten |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | Uitgesloten bestanden tellen niet mee in de dekking. Het zijn de bestanden die Findling op uw aanwijzing met rust laat. |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | Weinig schijfruimte vrij. De indexering pauzeert, zodat de index heel blijft. Zoeken werkt gewoon door. |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | De index is met een oudere tekstanalyse gebouwd. Met "occ findling:index --restart" opnieuw opbouwen, anders blijven er treffers ontbreken. |
| `Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.` | Findling baut seinen Index neu auf, damit die neu eingeschalteten Sprachen durchsucht werden können. %1$s von %2$s Dokumenten sind übertragen. Die Suche antwortet währenddessen weiter, und es gibt nichts zu starten oder neu zu starten. | Findling bouwt zijn index opnieuw op, zodat de nieuw ingeschakelde talen doorzocht kunnen worden. %1$s van %2$s documenten zijn overgezet. Zoeken blijft ondertussen antwoorden, en er is niets te starten of opnieuw te starten. |
| `Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.` | Findling möchte seinen Index für die neu eingeschalteten Sprachen neu aufbauen, und es ist nicht genug Platz: %s fehlen zusätzlich zu dem, was der Index bereits belegt. Geben Sie so viel frei, oder setzen Sie die Umgebungsvariable FINDLING_REBUILD_FALLBACK=fullreindex, damit das Backend die Dateien stattdessen neu liest. In beiden Fällen versucht es das Backend erst nach einem Neustart des Containers erneut. | Findling wil zijn index opnieuw opbouwen voor de nieuw ingeschakelde talen, en er is niet genoeg ruimte: %s ontbreken naast wat de index al gebruikt. Maak zoveel ruimte vrij, of zet de omgevingsvariabele FINDLING_REBUILD_FALLBACK=fullreindex, zodat de dienst de bestanden in plaats daarvan opnieuw leest. In beide gevallen probeert de dienst het pas na een herstart van de container opnieuw. |
| `Languages of the index: %1$s switched on, %2$s with text in the index.` | Sprachen des Index: %1$s eingeschaltet, %2$s mit Text im Index. | Talen van de index: %1$s ingeschakeld, %2$s met tekst in de index. |
| `No numbers yet` | Noch keine Zahlen | Nog geen getallen |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | De eerste indexeringsdoorloop is nog niet klaar. Findling is vanzelf gestart, er is niets in te stellen. |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | De twee helften van Findling melden verschillende versies: deze app is %1$s, de dienst is %2$s. Zolang ze niet bij elkaar passen, antwoordt de zoekfunctie zonder resultaten, omdat een verkeerd antwoord zonder melding erger zou zijn. Breng beide helften op dezelfde versie. |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | De Findling-dienst antwoordt niet. De getallen hieronder zijn de laatste die deze app heeft vastgelegd. Controleer onder Apps of de External App "Findling Backend" geïnstalleerd is en draait. |
| `Estimate for the first index` | Schätzung für den Erstindex | Schatting voor de eerste index |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s bestanden, waarvan %2$s met OCR. Ongeveer %3$s en ongeveer %4$s aan index. |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s bestanden, waarvan %2$s met OCR. |
| `%1$s to %2$s` | %1$s bis %2$s | %1$s tot %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | De bestanden worden geteld, dat duurt even. |
| `Startup value, being measured.` | Startwert, wird gemessen. | Startwaarde, wordt gemeten. |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | De benodigde ruimte wordt gemeten zodra de eerste documenten in de index staan. |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | De index heeft naar verwachting meer ruimte nodig dan er op dit volume vrij is. De indexering pauzeert voordat het volume vol loopt, en zoeken werkt gewoon door. |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | Findling wacht niet op een bevestiging. De eerste indexering loopt al. |
| `Files that were not indexed` | Nicht indexierte Dateien | Niet geïndexeerde bestanden |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | Niet geïndexeerde bestanden, gegroepeerd op reden |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | Alle bestanden zijn geïndexeerd. Niets overgeslagen, niets mislukt. |
| `Reason` | Grund | Reden |
| `Files` | Dateien | Bestanden |
| `State` | Zustand | Toestand |
| `Show example paths` | Beispielpfade anzeigen | Voorbeeldpaden tonen |
| `Hide example paths` | Beispielpfade verbergen | Voorbeeldpaden verbergen |
| `_and %n more_::_and %n more_` | und %n weitere / und %n weitere | en nog %n / en nog %n |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | Bestand bestaat niet meer (ID %s) |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s (in de prullenbak) |
| `%1$s (ID %2$s)` | %1$s (ID %2$s) | %1$s (ID %2$s) |
| `%1$s (in the trash bin, ID %2$s)` | %1$s (im Papierkorb, ID %2$s) | %1$s (in de prullenbak, ID %2$s) |
| `Indexed, text truncated` | Indexiert, Text gekürzt | Geïndexeerd, tekst ingekort |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | Onbekende reden (%s) |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | Deze app kent deze code niet. Hij kan van een nieuwere versie van de dienst komen. |
| `Text truncated` | Text gekürzt | Tekst ingekort |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | Het begin van het document is doorzoekbaar, de rest niet. Zeer lange documenten worden bewust afgekapt. |
| `Too large` | Zu groß | Te groot |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | De waarde onder "Grootste bestand om te lezen" verhogen. |
| `File type not supported` | Dateityp nicht unterstützt | Bestandstype niet ondersteund |
| `None. Findling reads PDF, Office, OpenDocument, text and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. | Geen. Findling leest PDF, Office, OpenDocument, tekst en afbeeldingen. |
| `Password protected` | Passwortgeschützt | Met wachtwoord beveiligd |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | Geen. Zonder het wachtwoord is de inhoud niet te lezen. |
| `No text in the document` | Kein Text im Dokument | Geen tekst in het document |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | Geen. Het document bevat noch een tekstlaag noch herkenbaar schrift. |
| `No text content` | Kein Textinhalt | Geen tekstinhoud |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | Geen. Het bestand is leesbaar, maar bevat geen tekst. |
| `Spreadsheet too large` | Tabelle zu groß | Spreadsheet te groot |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | Geen. Zeer grote spreadsheets worden overgeslagen, zodat de container niet omvalt. |
| `File no longer present` | Datei nicht mehr vorhanden | Bestand niet meer aanwezig |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | Geen. Het bestand was bij het lezen al verwijderd of verplaatst. |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | Afbeelding zonder herkenbaar schrift |
| `None.` | Keine. | Geen. |
| `Excluded by a rule` | Durch Regel ausgeschlossen | Door een regel uitgesloten |
| `Remove the matching entry under "Excluded folders".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | De passende vermelding onder "Uitgesloten mappen" verwijderen. |
| `Not readable for the users asked` | Für die gefragten Nutzer nicht lesbar | Niet leesbaar voor de gevraagde gebruikers |
| `The file is still there. Check the advanced permissions of the Team Folder: Findling reads a file only as a user who may open it and asks the first 20 of its users in alphabetical order.` | Die Datei ist noch vorhanden. Die erweiterten Berechtigungen des Team Folders prüfen: Findling liest eine Datei nur als Nutzer, der sie öffnen darf, und fragt die ersten 20 ihrer Nutzer in alphabetischer Reihenfolge. | Het bestand bestaat nog. De geavanceerde rechten van de Team Folder controleren: Findling leest een bestand alleen namens een gebruiker die het mag openen en vraagt de eerste 20 van zijn gebruikers in alfabetische volgorde. |
| `The user named in front of the path may not open this file. The diagnosis is about the file itself.` | Der vor dem Pfad genannte Nutzer darf diese Datei nicht öffnen. Die Diagnose gilt der Datei selbst. | De gebruiker die voor het pad staat, mag dit bestand niet openen. De diagnose gaat over het bestand zelf. |
| `File is empty` | Datei ist leer | Bestand is leeg |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | Geen. Het bestand heeft 0 bytes. |
| `File damaged` | Datei beschädigt | Bestand beschadigd |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | Het bestand buiten Nextcloud controleren en opnieuw uploaden. |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | Documentstructuur onjuist |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | Het document openen in het programma waaruit het komt en opnieuw opslaan. |
| `Character set not recognised` | Zeichensatz nicht erkannt | Tekenset niet herkend |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | Het bestand als UTF-8 opslaan en opnieuw uploaden. |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | Tijdslimiet overschreden bij het lezen |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | De volgende doorloop probeert het opnieuw. |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | Te weinig geheugen bij het lezen |
| `The next run tries again. If it happens again, lower the size cap.` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. | De volgende doorloop probeert het opnieuw. Gebeurt het nog eens, verlaag dan de bovengrens voor de grootte. |
| `File was not retrievable` | Datei war nicht abrufbar | Bestand was niet op te halen |
| `Stuck repeatedly` | Mehrfach hängen geblieben | Meermaals blijven hangen |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | Findling probeert dit bestand niet opnieuw. Via de controle nagaan of het buiten Nextcloud opengaat. |
| `Text recognition failed` | Texterkennung fehlgeschlagen | Tekstherkenning mislukt |
| `Text recognition not available` | Texterkennung nicht verfügbar | Tekstherkenning niet beschikbaar |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | De dienst kon Tesseract niet starten. Het logboek van de External App controleren. |
| `Look up one file` | Einzelne Datei prüfen | Één bestand controleren |
| `Path or file ID` | Pfad oder Datei-ID | Pad of bestands-ID |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Een pad zoals Nextcloud het bijhoudt, of het getal uit de lijst hierboven. |
| `Look up file` | Datei prüfen | Bestand controleren |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | De controle van één bestand heeft JavaScript nodig. Alles daarboven blijft ook zonder volledig leesbaar. |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | Op dit pad staat geen bestand, en geen bestand heeft dit ID. |
| `Not seen yet` | Noch nicht gesehen | Nog niet gezien |
| `State unknown right now` | Zustand im Moment unbekannt | Toestand op dit moment onbekend |
| `File ID: %s` | Datei-ID: %s | Bestands-ID: %s |
| `Last checked %s` | Zuletzt geprüft: %s | Laatst gecontroleerd: %s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | De controle heeft niet gewerkt. Aan dit bestand is niets veranderd. |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | De toestand van dit bestand is op dit moment onbekend, omdat de dienst niet antwoordt. |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | Dit bestand is nog niet in de wachtrij aangekomen. De volgende vergelijkingsdoorloop haalt het op. |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | Het was eerder geïndexeerd en wordt bij de volgende vergelijkingsdoorloop opnieuw vastgelegd. |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | Dit bestand was geïndexeerd en is inmiddels verwijderd. Daarmee is het ook uit de index. |
| `In the trash bin` | Im Papierkorb | In de prullenbak |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | Het bestand terugzetten. De volgende vergelijkingsdoorloop haalt het op. |
| `Storage is not indexed` | Speicherort wird nicht indexiert | Opslaglocatie wordt niet geïndexeerd |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | Findling leest de persoonlijke mappen van uw gebruikers. Team Folders en externe opslag zijn aparte instellingen. |
| `This is a folder` | Das ist ein Ordner | Dit is een map |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | Het pad van een bestand invoeren. Een map heeft geen eigen toestand. |
| `Attempts so far: %s` | Bisherige Versuche: %s | Pogingen tot nu toe: %s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | De volgende achtergronddoorloop haalt dit bestand op (%s). |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | De inhoud van dit bestand is doorzoekbaar. |
| `_A worker holds this file. The claim runs out in %n second if nothing acknowledges it._::_A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it._` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | Een verwerkingsproces houdt dit bestand vast. De claim verloopt over %n seconde als niemand hem bevestigt. / Een verwerkingsproces houdt dit bestand vast. De claim verloopt over %n seconden als niemand hem bevestigt. |
| `Rules and limits` | Regeln und Grenzen | Regels en grenzen |
| `Excluded folders` | Ausgeschlossene Ordner | Uitgesloten mappen |
| `Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Prefixvergelijking op het pad zoals de lijsten op deze pagina het tonen, geen jokertekens en geen patronen. Voorbeeld: Backups |
| `Add exclusion` | Ausschluss hinzufügen | Uitsluiting toevoegen |
| `Remove exclusion %s` | Ausschluss %s entfernen | Uitsluiting %s verwijderen |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | Geen enkele map is uitgesloten. |
| `Largest file to read` | Größte zu lesende Datei | Grootste bestand om te lezen |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | Grotere bestanden worden als overgeslagen (te groot) vastgelegd en nooit gelezen. |
| `The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.` | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | De dienst van deze instantie leest hoogstens %s MB. Voor meer FINDLING_MAX_FILE_BYTES verhogen in de app-instellingen van AppAPI, waardoor de container opnieuw start. |
| `Index Team Folders` | Team Folders indexieren | Team Folders indexeren |
| `Index external storage` | Externen Speicher indexieren | Externe opslag indexeren |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | Externe opslag kan traag zijn of per aanvraag geld kosten. De indexering leest elk bestand één keer. |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | De volgende doorloop neemt de nieuwe regels over. Er start niets opnieuw. |
| `Save rules` | Regeln speichern | Regels opslaan |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | Regels opgeslagen. De volgende doorloop neemt ze over. |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | De regels zijn niet opgeslagen. Er is niets veranderd. |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | Een grootte tussen %1$s en %2$s MB invoeren. |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | Een mappad invoeren. |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | Dit pad is al uitgesloten. |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | Een vermelding verwijderen werkt binnen %1$s uur, wanneer de volgende vergelijkingsdoorloop die bestanden weer opneemt. Met "%2$s" meteen overnemen. |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Geïndexeerde inhoud verwijderen? Het uitsluiten van %1$s haalt ook %2$s al geïndexeerde documenten onder dat pad uit de index. De bestanden zelf blijven onveranderd op de schijf staan. |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Geïndexeerde inhoud verwijderen? Het uitsluiten van %s haalt ook de al geïndexeerde documenten onder dat pad uit de index. De bestanden zelf blijven onveranderd op de schijf staan. |
| `at least %s` | mindestens %s | minstens %s |
| `Exclude and remove` | Ausschließen und entfernen | Uitsluiten en verwijderen |
| `Keep files indexed` | Dateien indexiert lassen | Bestanden geïndexeerd laten |
| `Search` | Suchen | Zoeken |
| `Search term` | Suchbegriff | Zoekterm |
| `invoice 2026` | Rechnung 2026 | factuur 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | Alleen bestandsnamen doorzoeken |
| `Results for "%s"` | Treffer für „%s“ | Resultaten voor "%s" |
| `Search results` | Suchergebnisse | Zoekresultaten |
| `%1$s in %2$s` | %1$s in %2$s | %1$s in %2$s |
| `last opened` | zuletzt geöffnet | laatst geopend |
| `Show all results` | Alle Treffer anzeigen | Alle resultaten tonen |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Opent de resultatenpagina van Findling |
| `Previous page` | Vorherige Seite | Vorige pagina |
| `Next page` | Nächste Seite | Volgende pagina |
| `Page %s` | Seite %s | Pagina %s |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | Er zijn meer resultaten. Verfijn de zoekopdracht om ze te zien. |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Doorzoek de inhoud van uw bestanden |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Typ een woord uit een document. Findling doorzoekt de tekst in uw bestanden, ook in gescande PDF-bestanden. |
| `No file contains "%s"` | Keine Datei enthält „%s“ | Geen bestand bevat "%s" |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Probeer een ander woord, een deel van een samenstelling, of controleer de spelling. |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | Andere bestanden bevatten dit woord, maar geen enkele die u mag openen. |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | De zoekfunctie antwoordt op dit moment niet |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | Findling kon zijn dienst niet bereiken. Uw bestanden zijn onveranderd. Probeer het zo meteen nog een keer, en laat het uw beheerder weten als het zo blijft. |
| `Try again` | Erneut versuchen | Opnieuw proberen |
| `Findling is not ready to search` | Findling ist nicht suchbereit | Findling is niet klaar om te zoeken |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | De twee helften van Findling melden verschillende versies. Uw beheerder moet beide samen bijwerken. |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | De index wordt nog opgebouwd, daarom kunnen er resultaten ontbreken. |
| `File type` | Dateityp | Bestandstype |
| `PDF` | PDF | PDF |
| `Documents` | Dokumente | Documenten |
| `Spreadsheets` | Tabellen | Spreadsheets |
| `Presentations` | Präsentationen | Presentaties |
| `Images` | Bilder | Afbeeldingen |
| `Text` | Text | Tekst |
| `Time range` | Zeitraum | Periode |
| `Today` | Heute | Vandaag |
| `Last 7 days` | Letzte 7 Tage | Laatste 7 dagen |
| `Last 30 days` | Letzte 30 Tage | Laatste 30 dagen |
| `This year` | Dieses Jahr | Dit jaar |
| `Remove filter %s` | Filter %s entfernen | Filter %s verwijderen |
| `Reset all filters` | Alle Filter zurücksetzen | Alle filters wissen |
| `Sort by` | Sortieren nach | Sorteren op |
| `Relevance` | Relevanz | Relevantie |
| `Last modified` | Zuletzt geändert | Laatst gewijzigd |
| `Oldest first` | Älteste zuerst | Oudste eerst |
| `Modified on %s` | Geändert am %s | Gewijzigd op %s |
| `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %1$s in %2$s, gewijzigd op %3$s |
| `No results with the active filters` | Keine Treffer mit den aktiven Filtern | Geen resultaten met de actieve filters |
| `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | Verwijder een filter of verruim de periode. |
| `Reset filters` | Filter zurücksetzen | Filters wissen |
| `Performance profile` | Leistungsprofil | Prestatieprofiel |
| `How much of this box Findling may use. Without a change Findling stays on Economy.` | Wie viel dieser Box Findling nutzen darf. Ohne Änderung bleibt Findling bei Sparsam. | Hoeveel van deze machine Findling mag gebruiken. Zonder wijziging blijft Findling op Zuinig. |
| `Detected: cores %1$s, memory %2$s` | Erkannt: Kerne %1$s, Speicher %2$s | Gedetecteerd: kernen %1$s, geheugen %2$s |
| `This backend does not report its hardware yet.` | Dieses Backend meldet seine Hardware noch nicht. | Deze dienst meldt zijn hardware nog niet. |
| `Suggested for this box: %s` | Vorschlag für diese Box: %s | Voorgesteld voor deze machine: %s |
| `In force: %s` | Wirksam: %s | Actief: %s |
| `Chosen %1$s, in force %2$s: this box has less hardware than the chosen profile needs.` | Gewählt %1$s, wirksam %2$s: Diese Box hat weniger Hardware, als das gewählte Profil braucht. | Gekozen %1$s, actief %2$s: deze machine heeft minder hardware dan het gekozen profiel nodig heeft. |
| `Profile` | Profil | Profiel |
| `%s (suggested)` | %s (Vorschlag) | %s (voorgesteld) |
| `One OCR slot, as before.` | Ein OCR-Slot, wie bisher. | Eén OCR-slot, zoals voorheen. |
| `At most half of this box, up to %s OCR slots.` | Höchstens die Hälfte dieser Box, bis zu %s OCR-Slots. | Hoogstens de helft van deze machine, tot %s OCR-slots. |
| `Everything but one core, up to %s OCR slots.` | Alles bis auf einen Kern, bis zu %s OCR-Slots. | Alles op één kern na, tot %s OCR-slots. |
| `More accurate search model (fp32)` | Genaueres Suchmodell (fp32) | Nauwkeuriger zoekmodel (fp32) |
| `Downloaded once during the check, about %s from the Findling release on GitHub. Needs more memory than int8.` | Wird bei der Prüfung einmal geladen, etwa %s aus dem Findling-Release auf GitHub. Braucht mehr Speicher als int8. | Wordt tijdens de controle eenmaal gedownload, ongeveer %s uit de Findling-release op GitHub. Heeft meer geheugen nodig dan int8. |
| `Re-embedding of %1$s documents, estimated about %2$s. Full text search stays fully available.` | Neueinbettung von %1$s Dokumenten, geschätzt etwa %2$s. Die Volltextsuche bleibt voll verfügbar. | Vectoren van %1$s documenten opnieuw berekenen, geschat ongeveer %2$s. Zoeken in de volledige tekst blijft volledig beschikbaar. |
| `Re-embedding of %s documents. Full text search stays fully available.` | Neueinbettung von %s Dokumenten. Die Volltextsuche bleibt voll verfügbar. | Vectoren van %s documenten opnieuw berekenen. Zoeken in de volledige tekst blijft volledig beschikbaar. |
| `Choose a different profile or model to check it.` | Ein anderes Profil oder Modell wählen, um es zu prüfen. | Een ander profiel of model kiezen om het te controleren. |
| `Changing the profile needs JavaScript. Everything above stays complete without it.` | Das Profil zu ändern braucht JavaScript. Alles darüber bleibt ohne es vollständig. | Het profiel wijzigen vereist JavaScript. Alles hierboven blijft zonder JavaScript volledig. |
| `The check calculates with these values from environment variables:` | Die Prüfung rechnet mit diesen Werten aus Umgebungsvariablen: | De controle rekent met deze waarden uit omgevingsvariabelen: |
| `OCR resolution %1$s dpi, set by %2$s` | OCR-Auflösung %1$s dpi, gesetzt durch %2$s | OCR-resolutie %1$s dpi, ingesteld door %2$s |
| `OCR limit %1$s pages per file, set by %2$s` | OCR-Deckel %1$s Seiten je Datei, gesetzt durch %2$s | OCR-limiet %1$s pagina's per bestand, ingesteld door %2$s |
| `Embedding batch size %1$s, set by %2$s` | Einbettungs-Stapelgröße %1$s, gesetzt durch %2$s | Batchgrootte voor vectoren %1$s, ingesteld door %2$s |
| `Index writer memory %1$s, set by %2$s` | Speicher des Indexschreibers %1$s, gesetzt durch %2$s | Geheugen van de indexschrijver %1$s, ingesteld door %2$s |
| `Apply and check` | Übernehmen und prüfen | Toepassen en controleren |
| `Apply` | Übernehmen | Toepassen |
| `Stay on Economy` | Bei Sparsam bleiben | Bij Zuinig blijven |
| `Check again` | Erneut prüfen | Opnieuw controleren |
| `Check %s` | %s prüfen | %s controleren |
| `Check running: %s` | Prüfung läuft: %s | Controle loopt: %s |
| `Check running.` | Prüfung läuft. | Controle loopt. |
| `waiting for the indexing batch` | Indexstaffel abwarten | wachten op de indexeringsronde |
| `downloading the model, %1$s of %2$s` | Modell herunterladen, %1$s von %2$s | model downloaden, %1$s van %2$s |
| `verifying the model file` | Modelldatei prüfen | modelbestand controleren |
| `loading the model` | Modell laden | model laden |
| `OCR with one slot` | OCR mit einem Slot | OCR met één slot |
| `calculating memory` | Speicher rechnen | geheugen berekenen |
| `OCR with %s slots` | OCR mit %s Slots | OCR met %s slots |
| `cleaning up` | aufräumen | opruimen |
| `Indexing pauses during the check and continues afterwards.` | Die Indexierung pausiert während der Prüfung und läuft danach weiter. | Het indexeren pauzeert tijdens de controle en gaat daarna verder. |
| `Fits` | Passt | Past |
| `Fits narrowly` | Passt knapp | Past krap |
| `Does not fit` | Passt nicht | Past niet |
| `Checked: %1$s with %2$s, %3$s` | Geprüft: %1$s mit %2$s, %3$s | Gecontroleerd: %1$s met %2$s, %3$s |
| `Saved. %s applies from the next indexing round.` | Gespeichert. %s gilt ab der nächsten Indexrunde. | Opgeslagen. %s geldt vanaf de volgende indexeringsronde. |
| `Nothing was saved. %s stays in force.` | Nichts gespeichert. %s bleibt wirksam. | Er is niets opgeslagen. %s blijft actief. |
| `The downloaded model file was deleted again.` | Die geladene Modelldatei wurde wieder gelöscht. | Het gedownloade modelbestand is weer verwijderd. |
| `Memory reserve too thin: %1$s left, %2$s needed.` | Speicherreserve zu knapp: %1$s übrig, %2$s nötig. | Geheugenreserve te krap: %1$s over, %2$s nodig. |
| `Not enough memory: %1$s OCR slots need about %2$s, %3$s are available.` | Zu wenig Speicher: %1$s OCR-Slots brauchen etwa %2$s, verfügbar sind %3$s. | Te weinig geheugen: %1$s OCR-slots hebben ongeveer %2$s nodig, %3$s is beschikbaar. |
| `Not enough memory for the fp32 model: it needs about %1$s, %2$s are available.` | Zu wenig Speicher für das fp32-Modell: Es braucht etwa %1$s, verfügbar sind %2$s. | Te weinig geheugen voor het fp32-model: het heeft ongeveer %1$s nodig, %2$s is beschikbaar. |
| `A test slot was ended for lack of memory.` | Ein Prüf-Slot wurde wegen Speichermangel beendet. | Een testslot is wegens geheugentekort beëindigd. |
| `The measurement took longer than %s.` | Die Messung dauerte länger als %s. | De meting duurde langer dan %s. |
| `The model could not be downloaded. Check that github.com and release-assets.githubusercontent.com are reachable.` | Das Modell ließ sich nicht herunterladen. Prüfen, ob github.com und release-assets.githubusercontent.com erreichbar sind. | Het model kon niet worden gedownload. Controleren of github.com en release-assets.githubusercontent.com bereikbaar zijn. |
| `The download took longer than %s.` | Der Download dauerte länger als %s. | Het downloaden duurde langer dan %s. |
| `The model file does not match its checksum and was deleted.` | Die Modelldatei passt nicht zu ihrer Prüfsumme und wurde gelöscht. | Het modelbestand komt niet overeen met zijn controlesom en is verwijderd. |
| `The model file placed on the volume does not match its checksum. Replace or remove it.` | Die auf dem Volume abgelegte Modelldatei passt nicht zu ihrer Prüfsumme. Die Datei ersetzen oder entfernen. | Het op het volume geplaatste modelbestand komt niet overeen met zijn controlesom. Het bestand vervangen of verwijderen. |
| `Not enough disk space for the fp32 model.` | Zu wenig Platz auf dem Datenträger für das fp32-Modell. | Te weinig schijfruimte voor het fp32-model. |
| `The available memory could not be read.` | Der verfügbare Speicher ließ sich nicht lesen. | Het beschikbare geheugen kon niet worden gelezen. |
| `The check was interrupted by a restart of the backend.` | Die Prüfung wurde durch einen Neustart des Backends unterbrochen. | De controle is onderbroken door een herstart van de dienst. |
| `The running indexing batch did not end within %s.` | Die laufende Indexstaffel endete nicht innerhalb von %s. | De lopende indexeringsronde eindigde niet binnen %s. |
| `The check stopped with an error.` | Die Prüfung brach mit einem Fehler ab. | De controle is met een fout gestopt. |
| `The check needs the backend, and it does not answer right now. Nothing was saved.` | Die Prüfung braucht das Backend, und es antwortet gerade nicht. Nichts gespeichert. | De controle heeft de dienst nodig, en die antwoordt nu niet. Er is niets opgeslagen. |
| `This backend version cannot run the check. Bring both halves of Findling to the same version.` | Diese Backend-Version kann die Prüfung nicht fahren. Beide Hälften von Findling auf dieselbe Version bringen. | Deze versie van de dienst kan de controle niet uitvoeren. Beide helften van Findling op dezelfde versie brengen. |
| `A check is already running. Its result appears here.` | Eine Prüfung läuft bereits. Ihr Ergebnis erscheint hier. | Er loopt al een controle. Het resultaat verschijnt hier. |
| `The index is being rebuilt right now. The check is possible afterwards.` | Der Index wird gerade neu aufgebaut. Die Prüfung ist danach möglich. | De index wordt nu opnieuw opgebouwd. De controle is daarna mogelijk. |
| `The profile was not saved. Nothing changed.` | Das Profil wurde nicht gespeichert. Es hat sich nichts geändert. | Het profiel is niet opgeslagen. Er is niets veranderd. |
| `The memory guard lowered the profile: chosen %1$s, in force %2$s (%3$s).` | Der Speicherwächter hat das Profil abgesenkt: gewählt %1$s, wirksam %2$s (%3$s). | De geheugenbewaker heeft het profiel verlaagd: gekozen %1$s, actief %2$s (%3$s). |
| `The fp32 model is not available. The search uses int8.` | Das fp32-Modell ist nicht verfügbar. Die Suche nutzt int8. | Het fp32-model is niet beschikbaar. Zoeken gebruikt int8. |
| `fp32 is set, but this box has too little memory for it. The search uses int8.` | fp32 ist gesetzt, aber diese Box hat zu wenig Speicher dafür. Die Suche nutzt int8. | fp32 is ingesteld, maar deze machine heeft er te weinig geheugen voor. Zoeken gebruikt int8. |
| `fp32 is only available in Standard and Performance. The search uses int8.` | fp32 gibt es nur in Standard und Leistung. Die Suche nutzt int8. | fp32 is alleen beschikbaar in Standaard en Prestatie. Zoeken gebruikt int8. |
| `fp32 stays active under Economy. To go back to int8, choose Standard or Performance and clear the tick.` | fp32 bleibt unter Sparsam aktiv. Zurück zu int8: Standard oder Leistung wählen und das Häkchen entfernen. | fp32 blijft actief onder Zuinig. Terug naar int8: Standaard of Prestatie kiezen en het vinkje weghalen. |
| `The fp32 model is being downloaded.` | Das fp32-Modell wird heruntergeladen. | Het fp32-model wordt gedownload. |
| `No check yet.` | Noch keine Prüfung. | Nog geen controle. |
| `Choose a profile and check it on this box. Until then Economy stays in force.` | Ein Profil wählen und auf dieser Box prüfen. Bis dahin bleibt Sparsam wirksam. | Een profiel kiezen en het op deze machine controleren. Tot dan blijft Zuinig actief. |

**Nachtrag 29.09.2026 (Review der Phase 27, WR-05).** 82 Zeilen sind ergänzt: die 72 Schlüssel der Phase 27 (Plan 27-13, Oberfläche des Leistungsprofils) und 10 ältere aus den Plänen 25-04 und 26-05, die beim Abschluss der Phase 26 schon fehlten. Die ergänzten Zeilen sind nicht abgetippt, sondern mechanisch aus `php/l10n/de.json` und den Katalogen der Spalten dieser Tabelle übernommen, stehen hinter dem Schlüssel, der ihnen in `de.json` vorausgeht, und tragen genau den Wortlaut, den die App ausliefert. Seitdem hält `test_every_language_table_carries_every_key_with_the_catalogue_wording` in `backend/tests/test_admin_ui_contract.py` diese Tabelle gegen die Kataloge, in beide Richtungen und Zelle für Zelle. Die Zählungen weiter oben und unten sind der Stand ihres Datums; die maßgebliche Zählung steht in `docs/l10n-catalogues.md`.

## Ausnahmen für das Vollständigkeitsgate G2

Gate G2, heute `test_every_catalogue_value_carries_a_wording_of_its_language`, fordert, dass
kein Wert leer und keiner mit dem englischen Quellstring identisch ist. Genau vier Schlüssel
sind es im Niederländischen absichtlich. Das ist eine benannte Liste und ausdrücklich **keine**
Toleranzschwelle: eine Schwelle würde einen vergessenen Wortlaut genauso mitdecken wie einen
gewollten, eine Liste deckt nur, was in ihr steht. Die Liste darf wachsen, die Zahl vier ist
keine Grenze, sondern das Ergebnis des Zählens, und jeder Eintrag trägt seinen Grund bei sich.

- `Findling`: Eigenname der App, in jeder Sprache dasselbe Wort. Er steht als Schlüssel in
  `de.json` und muss deshalb in `nl.json` stehen, hat aber keinen eigenen Wortlaut.
- `%1$s in %2$s`: zwei Platzhalter und die Präposition dazwischen, die das Niederländische
  genau so schreibt wie das Englische und das Deutsche. Es ist derselbe Schlüssel, den die
  deutsche und die italienische Liste führen, und aus demselben Grund. Der verwandte Schlüssel
  `%1$s in %2$s, modified on %3$s` steht **nicht** hier, weil sein zweiter Teil niederländisch
  ist (`gewijzigd op %3$s`).
- `PDF`: Eigenname eines Dateiformats, in jeder Sprache dieselbe Abkürzung.
- `Spreadsheets`: das Wort, das die niederländische Nextcloud-Oberfläche für diesen
  Dateityp-Filter selbst führt. `Rekenbladen` gibt es und wäre eine Erfindung an dieser Stelle:
  der Filter soll heißen, wie die Anwendung daneben heißt. Dieser Eintrag ist der Grund, warum
  die niederländische Liste eine Stelle länger ist als die italienische.
- `%1$s (ID %2$s)` (seit Quick-Task 260929-s7p, Issue #14): zwei Platzhalter und die
  Abkürzung ID, die in jeder Sprache dieses Baums gleich geschrieben wird.

Die Liste ist nicht geraten worden. Drei Läufe, in dieser Reihenfolge:

| Lauf | Ergebnis |
|---|---|
| kein Eintrag für `nl` in der Tabelle | `AssertionError: languages without a list of exceptions: ['nl']` |
| leeres Mapping `"nl": {}` | acht Funde, vier Schlüssel über zwei Dateien, erster davon `nl.json: 'Findling' is still the English source string` |
| vier begründete Einträge | grün, 52 passed |

Beurteilt wurde je Schlüssel und nicht gezählt. Die Liste ist kürzer als die französische (fünf
Einträge), weil `Page %s`, `Documents` und `Images` im Niederländischen eigene Wortlaute haben:
`Pagina %s`, `Documenten`, `Afbeeldingen`. Sie ist um einen Eintrag länger als die italienische
und um zwei länger als die spanische, und der Grund ist eine Eigenschaft der Sprache: das
Niederländische hat mehr englische Fachwörter unverändert übernommen als die romanischen
Sprachen. Der Plan hat genau das erwartet; gemessen ist es trotzdem worden, weil eine Erwartung
über eine Zahl keine Beurteilung eines Schlüssels ersetzt.

Dieselben vier Schlüssel mit denselben Gründen stehen in
`VALUES_THAT_MAY_EQUAL_THEIR_KEY["nl"]` in `backend/tests/test_admin_ui_contract.py`. Doku und
Gate dürfen hier nicht auseinanderlaufen: die Doku sagt, was erlaubt ist, das Gate hält es.

## Maschinelle Prüfungen

Gefahren am 25.09.2026 über die beiden erzeugten Dateien, nicht per Augenmaß:

| Prüfung | Ergebnis |
|---|---|
| Schlüsselmenge `nl.json` gleich `de.json`, in derselben Reihenfolge | ja, 202 von 202, fehlend 0 |
| Schlüsselmenge `nl.js` gleich `nl.json` (Objektvergleich über den `register`-Rumpf) | ja, identisch |
| Jeder Schlüssel aus `nl.json` kommt in dieser Datei vor | fehlend: 0 |
| Platzhalter-Parität Schlüssel gegen Wert, über alle 40 Schlüssel mit Direktiven, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen |
| Pluralschlüssel mit genau **zwei** Formen | 5 von 5 |
| Pluralschlüsselmenge gleich der deutschen | ja |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, mit `nplurals=2` | ja, in beiden Dateien |
| `scan_plural_rule` meldet für `nl` mit der deutschen Zeichenkette keinen Fund | ja, `[]`, während dieselbe Zeichenkette für `es` zwei Funde erzeugt |
| U+2019 (typographischer Apostroph) | 0 |
| U+2014 und U+2013 (Gedankenstriche) | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 |
| Nackte Prozentzeichen, also `%` ohne erkannte Direktive | 0 in Schlüsseln und in allen Formen |
| Pipe-Zeichen (der senkrechte Strich, mit dem Nextcloud Pluralformen verbindet) | 0 in Schlüsseln und in allen Formen |
| Wert identisch mit dem englischen Quellstring | 4, alle vier oben benannt |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Dateien, byteweise geprüft; der Git-Blob ist reines LF (0 CR) |
| Giessform gegen den unveränderten Bestand, vor der ersten neuen Zeile | 10 von 10 byteweise gleich (`de`, `de_DE`, `fr`, `es`, `it`, je `.json` und `.js`) |
| Einträge in `L10N_CATALOGUES` | 12 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped |
| ruff check, ruff format --check, pyright, vulture | alle grün |

**Ein Befund gehört zu dieser Tabelle, weil er den beiden vorigen Sprachen widerspricht.** Das
Vokabular-Gate in `backend/tests/test_public_artifacts.py` hält eine Wortstamm-Sperre über
alles unter `docs/` und ist bei Spanisch (61 Treffer) und bei Italienisch (9 Treffer) rot
gefallen. Über dieser Datei fällt es **nicht**: das Niederländische schreibt Datei als
`bestand` und Speicherort als `opslag`, und keines der beiden Wörter trägt den gesperrten
Stamm. Die Prognose aus Plan 20-04 hat für `nl` also gestimmt. Gemessen ist sie trotzdem
worden, weil sie für `it` in der Wirkung stimmte und im Wort danebenlag; ein Lauf kostet
Sekunden, eine falsche Prognose einen Fehlschlag im Commit.

Was keine Maschine prüfen kann, ist die Sprache. Das ist der Gegenstand des Abschnitts
darunter.

## Abnahme

**Erzeugt am 25.09.2026, Plan 20-06.** Die niederländischen Wortlaute dieser Tabelle sind
maschinell entstanden und anschließend gegen die Gates gefahren, die der Abschnitt "Maschinelle
Prüfungen" aufzählt: Schlüsselmenge, Gleichstand der beiden Dateien, Platzhalterparität,
Formenzahl, Pluralregel, Prozentdisziplin, Pipe-Zeichen, Prosa-Scan auf Gedankenstriche und
Symbolzeichen, Apostroph- und Akzentprüfung, Vollständigkeit mit benannter Ausnahmeliste.

**Dieser Katalog ist von keinem Muttersprachler gelesen worden.** Das ist keine offene
Aufgabe, die jemand vergessen hat, sondern der gesperrte Entscheid E-17-5, Option a: die vier
neuen Sprachen entstehen maschinell und werden über das offene Community-Review korrigiert, das
jede App im Nextcloud App Store hat. Wer einen Fehler findet, meldet ihn als Issue im
Repositorium `street1983nk/nextcloud-search` oder schickt eine Änderung an dieser Tabelle; die
nächste Ausgabe nimmt ihn mit. Ein Muttersprachler-Gate ist ausdrücklich **nicht** gewählt
worden und wird hier auch nicht nachträglich eingeführt.

**Die Auslieferung wartet darauf nicht.** Das ist die Abwägung hinter dem Entscheid: ein
niederländischer Katalog mit einzelnen unrunden Sätzen ist für einen niederländischen Nutzer
besser als eine englische Oberfläche, und die Fehler, die eine Maschine macht, sind sichtbar und
korrigierbar. Der Unterschied zum französischen Katalog ist an dieser Stelle ausdrücklich
festgehalten: `docs/l10n-french.md` trägt eine Abnahme durch den Owner, einen französischen
Muttersprachler, datiert auf den 11.09., 19.09. und 24.09.2026. Diese Datei trägt eine Stufe
weniger, und sie sagt es, damit niemand die beiden für gleich abgenommen hält.

**Drei Stellen, an denen ein Muttersprachler zuerst hinsehen sollte.** Sie sind hier benannt,
damit das Review nicht bei null anfängt. Erstens die Wahl von `doorloop` für den Lauf und die
daraus gebauten Zusammensetzungen `vergelijkingsdoorloop` und `achtergronddoorloop`: sie sind
regelmäßig gebildet, aber lang, und ein Muttersprachler könnte `ronde` oder eine Umschreibung
vorziehen. Zweitens `verwerkingsproces` für den Worker, aus der romanischen Linie übernommen.
Drittens der Wechsel zwischen Infinitiv und `u`-Form, der dem deutschen Bestand folgt und
deshalb innerhalb einer Seite wechselt; wer ihn vereinheitlichen will, muss zuerst den
deutschen Katalog vereinheitlichen.

**Was ausdrücklich nicht zur Nachbesserung ansteht:** die zwei Pluralformen und die mit der
deutschen zeichengleiche Regel. Beides sieht nach einem Fehler aus und ist keiner; der
Abschnitt "Pluralformen" führt es aus, und wer es ändern will, widerlegt zuerst die Messung in
`docs/l10n-catalogues.md`, Abschnitt 3.

**Stand dieser Datei:** alle 202 Zeilen sind am 25.09.2026 entstanden, keine ist später
hinzugekommen, und keine ist abgenommen. Kommt später ein Schlüssel dazu, gehört er in diese
Tabelle und in einen datierten Nachtrag darunter, aus demselben Grund, aus dem
`docs/l10n-french.md` seine Nachträge führt: eine Datei darf keine ungelesene Zeile
stillschweigend mittragen.
