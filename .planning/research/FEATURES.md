# Feature Research

**Domain:** Dateityp-Filter und Sortierung auf einer eigenen Suchergebnisseite in Nextcloud, plus Modell-Entladung im Leerlauf einer ExApp auf kleiner Hardware
**Researched:** 2026-09-14 (Milestone v1.2)
**Confidence:** HIGH für alles, was aus dem eigenen Quellcode, den eigenen Messberichten, dem Nextcloud-Serverquellcode und dem Developer Manual stammt. MEDIUM für die UX-Erwartungen aus Fremdprodukten (Files-App, Paperless-ngx, Immich, Ollama, LM Studio), weil das Nutzerverhalten daraus abgeleitet und nicht gemessen ist.

Nur die zwei neuen Funktionen sind hier untersucht. Volltext, Semantik, OCR, Zero-Config, Berechtigungs-Durchgriff, Ergebnisseite mit Paginierung, Admin-Sicht und EN/DE/FR gelten als gebaut.

---

## Vorbefunde, die die Feature-Frage neu stellen

Vier Befunde entscheiden mehr als jede Geschmacksfrage. Sie stehen vor der Landschaft, weil sie mehrere Zeilen der Tabellen erklären.

### V1. Der Unified-Search-Dialog kann weder Typfilter noch Sortierung tragen (HIGH)

Der Dialog von Nextcloud bietet exakt drei Filterkategorien an: Orte/Provider, Datum, Person. Es gibt keinen Dateityp-Filter und keine Sortiersteuerung. Nachgelesen im Serverquellcode, `core/src/components/UnifiedSearch/UnifiedSearchModal.vue` (`data-cy-unified-search-filter="places" | "date" | "people"`, `dateFilterActive`, `personFilterActive`).

**Folge:** Beide v1.2-Funktionen leben vollständig auf der eigenen Ergebnisseite (`php/lib/Controller/PageController.php`, `php/templates/search.php`) und im `/search`-Vertrag des Containers. `php/lib/Search/Provider.php` bleibt unberührt. Das ist eine gute Nachricht für den Umfang: der Dialogpfad muss nicht zweimal gedacht werden.

### V2. Findling verschwindet heute stumm, sobald jemand im Dialog einen Datums- oder Personenfilter setzt (HIGH)

`Provider::getSupportedFilters()` meldet genau `BUILTIN_TERM` und `BUILTIN_TITLE_ONLY`. Das Developer Manual sagt wörtlich: "If filters send by client are not supported, the provider will not receive the request." Der Dialog bietet den Datumsfilter jedem Nutzer an. Wer ihn setzt, bekommt keine Findling-Gruppe, ohne Fehler, ohne Hinweis. Genau diese Falle steht bereits als Kommentar in `Provider.php` ("a skipped provider looks exactly like a broken backend").

**Folge:** Ein `since`/`until`-Filter ist kein Luxus, sondern das Schließen einer stillen Lücke. Er ist technisch billig (siehe V3) und gehört in die Priorisierung, auch wenn er nicht im Milestone-Ziel steht.

### V3. Die Bausteine für Filter und Sortierung liegen bereits im Index und in der SQLite (HIGH, kein Reindex nötig)

| Baustein | Wo | Eignung |
|---|---|---|
| `ext`, kleingeschriebene Endung ohne Punkt, `raw`-Tokenizer, `basic` | `backend/src/findling/index/schema.py`, gefüllt über `extension_of()` | exakter Termfilter, bereits von der `type:`-Syntax benutzt |
| `mtime`, Integer, `fast=True`, `indexed=False` | dieselbe Datei | `order_by_field` und `range_query` laufen über Fast Fields |
| `files.mime`, `files.size`, `files.mtime` je `file_id` | `backend/src/findling/store/schema.sql` | Mimetype-Gruppen und Größen ohne Indexänderung, dieselbe Datenbank, die schon den ACL-Vorfilter beantwortet |
| `Searcher.search(..., order_by_field=..., order=Order.Desc)` und `Query.range_query(..., use_inverted_index=False)` | tantivy-Stub im Projekt-venv, `tantivy/tantivy.pyi` Zeilen 347 bis 401 | Sortierung und Zeitraumfilter ohne neue Abhängigkeit |

**Folge:** Typfilter, Datumssortierung und Zeitraumfilter kosten **keinen** `SCHEMA_VERSION`-Sprung und **keinen** Reindex. Das hält D-04 aus v1.1 ("Bestandsinstallationen nicht strafen") durch. Sortierung nach **Name** oder **Größe** fällt genau deshalb heraus: Name ist ein Textfeld ohne Fast-Spalte, Größe steht überhaupt nicht im Index. Siehe Anti-Features.

### V4. Die Wiederaufwärm-Kosten der Entladung sind bereits gemessen, und sie waren einmal ein echter Nulltreffer (HIGH)

Aus `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`:

| Größe | Wert |
|---|---|
| Grundlast im Leerlauf, Modell kalt | 103,2 MB |
| Erste Suche mit semantischem Anteil, `anon` danach | 518,2 MB, also **plus 415,0 MB dauerhaft** |
| Einzelposten "Gewichte geladen" | plus 398,7 MB |
| Kaltstart über OCS, leerer Bestand | 1.550,4 ms |
| Kaltstart über OCS, voller Bestand | 1.838,4 ms |
| Drei Reproduktionen | 1.598 / 1.805 / 2.468 ms, warm danach 553 bis 674 ms |
| Decke eines einzelnen Containeraufrufs | 1.501 ms (`ExAppService::REQUEST_TIMEOUT_SECONDS` und `PAGE_REQUEST_TIMEOUT_SECONDS`, je 1,5 s) |
| Belegter Abbruch am 10.09.2026, 14:05:17Z | `cURL error 28 ... after 1501 milliseconds`, `backend unreachable`, **null Treffer** für den Nutzer, bei kaltem Seitencache des Wirts |

**Folge, und sie ist die wichtigste Zeile dieses Dokuments:** Die 415 MB sind der Gewinn, den die Entladung holt. Der Preis ist genau der Kaltstart, der bereits einmal eine Suche gekostet hat. Eine Entladung, die den Nutzer das Nachladen **synchron** bezahlen lässt, baut diesen Nulltreffer als wiederkehrendes Verhalten ein. Die Architektur kann das bereits sauber: `_semantic_documents()` in `backend/src/findling/index/search.py` fängt jeden Fehler der Vektorhälfte ab und liefert eine leere Liste, worauf die Suche rein lexikalisch antwortet (D-19). Entladung muss auf genau diesen Pfad aufsetzen.

---

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Typgruppen im Nextcloud-Vokabular statt Endungsliste: Dokumente, Tabellen, Präsentationen, PDF, Bilder, Text | Die Files-App filtert seit NC 30 genau so (`apps/files/src/components/FileListFilter/FileListFilterType.vue`: Documents, Spreadsheets, Presentations, PDFs, Folders, Audio, Images, Videos, über Mime-Aliase `x-office/document` usw.). Wer diese Wörter in der Dateiliste gelernt hat, sucht sie auf der Ergebnisseite wieder | MEDIUM | Gruppen auf die indexierbaren Typen kürzen (`ALLOWED_MIMETYPES` in `backend/src/findling/extract/dispatch.py`): PDF, docx/odt/rtf, xlsx/ods, pptx/odp, txt/md/csv/html, jpeg/png/tiff/webp. Audio, Video, Ordner gibt es hier nie, also dürfen sie auch nicht angeboten werden |
| Genau ein Filter-Vokabular, nicht zwei | Es gibt bereits `type:pdf` in der Suchzeile (`backend/src/findling/query/rewrite.py`). Ein UI-Filter, der etwas anderes bedeutet als die Syntax, produziert zwei Wahrheiten | MEDIUM | Entweder der UI-Filter übersetzt in dieselbe `ext`-Menge, oder die Syntax wird auf Gruppen erweitert. Eine Entscheidung, nicht zwei Implementierungen |
| Aktive Filter sichtbar und mit einem Klick entfernbar, plus "Filter zurücksetzen" | Standardmuster in Files-App (Chips), Paperless-ngx und jeder Facettensuche; NN/g nennt die einklickbare Entfernung als Pflicht | LOW | Serverseitig als Formular, kein JS nötig. `php/js/search.js` sagt im Kopf bereits zu, dass "filtering" ohne Script funktioniert |
| Filter- oder Sortierwechsel setzt auf Seite 1 zurück | Sonst zeigt Seite 5 Treffer aus einer anderen Ergebnismenge | LOW, aber korrektheitskritisch | Der Cursorpfad (`PageController::cursorPath`) gilt nur für ein Tupel aus Begriff, `names`, Filter und Sortierung. Ändert sich eines davon, muss `cursors` verworfen werden. Bereits vorhandene Regel: jeder Pfaddefekt landet auf Seite 1 |
| Filter und Sortierung stehen in der URL und überleben Teilen, Lesezeichen und Zurücknavigation | Die Seite ist bewusst ein Dokument; Zurückkehren ohne Listenverlust ist ein geliefertes v1.1-Versprechen (UI-03) | LOW | `PageController::pageUrl()` erweitern, dieselbe defensive Leseart wie `names` und `page`: unbekannter Wert bedeutet "nicht gesetzt", nie eine Fehlermeldung |
| Sortierung: Relevanz als Vorgabe, "Zuletzt geändert" als zweite Option | Paperless-ngx sortiert Volltexttreffer per Vorgabe nach Score; Drive, Dropbox und SharePoint bieten Relevanz plus Datum. Relevanz muss die Vorgabe bleiben, sonst verliert die Hybridsuche ihren Sinn | MEDIUM | `order_by_field=mtime`, `Order.Desc`. Zweitschlüssel `file_id` gegen gleiche Zeitstempel, sonst wackelt die Paginierung |
| Leerer Ergebniszustand nennt den aktiven Filter | "Keine Treffer" nach einem unbemerkt gesetzten Filter ist die klassische Sackgasse | LOW | Ein Satz plus der Entfernen-Link, in allen drei Katalogen |
| Entladung kostet den Nutzer nie eine gescheiterte Suche | Belegt in V4: ein Kaltstart hat bereits einmal 0 Treffer erzeugt | HIGH | Erste Suche nach Entladung antwortet sofort lexikalisch, das Modell wärmt im Hintergrund nach, ab der zweiten Suche ist die Semantik zurück. Nutzt den bestehenden Degradationspfad |
| Der Zustand ist auf der Admin-Seite ablesbar | Die Seite nennt heute fünf Modellzustände mit je einem Satz (`php/templates/admin.php`, `docs/admin-page.md`) | LOW bis MEDIUM | Sechstes Wort nötig, etwa `unloaded`. `AdminViewService::ENGINE_STATES` ist eine geschlossene Liste; ein unbekanntes Wort fällt heute auf "meldet den Zustand noch nicht" zurück, und ein Test sichert genau das ab (`AdminViewServiceTest`: 'a word from a later release' => ['unloading']). Neuer Container plus alte Hälfte bleibt also unfallfrei, zeigt aber den Ersatzsatz |
| Abschaltbar | Immich (`MACHINE_LEARNING_MODEL_TTL=0`), Ollama (`OLLAMA_KEEP_ALIVE=-1`) und LM Studio (TTL je Modell) machen die Entladung alle abschaltbar. Wer RAM hat, will Tempo | LOW | Eine Umgebungsvariable im Muster von `backend/src/findling/config.py`, `0` bedeutet nie entladen. Kein Admin-UI-Schalter, siehe Anti-Features |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Filter und Sortierung ohne Reindex | Das offizielle fulltextsearch-Umfeld erkauft Filter mit einem Suchserver. Findling holt sie aus Feldern, die seit v1.0 im Index stehen. Bestandsinstallationen aktualisieren und haben die Funktion sofort | LOW (Entscheidung, nicht Code) | Hält D-04 durch. Gehört in den Store-Text: "neue Filter, kein Reindex" |
| Typfilter, der nur anbietet, was es geben kann | Die Files-App zeigt "Videos" auch dort, wo nie ein Video liegt. Ein Filter, der nie leer läuft, wirkt gebaut statt generiert | LOW | Ergibt sich aus der Kürzung auf `ALLOWED_MIMETYPES` |
| Mimetype-Gruppen aus der SQLite statt Endungsraten | `files.mime` ist der von Nextcloud bestimmte Typ, also derselbe Wert, nach dem die Files-App filtert. Eine `.docx`, die jemand `.doc` genannt hat, landet in derselben Gruppe wie im Dateimanager | MEDIUM | Alternative zum `ext`-Term im Index. Preis: der Vorfilter bekäme einen Join gegen `files`, und `prefilter_visible()` trägt heute den ausdrücklichen Kommentar "no ORDER BY and no join against files on this path". Bewusste Entscheidung nötig, siehe Abhängigkeiten |
| Zeitraumfilter `since`/`until`, im Dialog **und** auf der Seite | Schließt V2: Findling verschwindet heute stumm, sobald jemand im Dialog nach Datum filtert. Mit `range_query` über das Fast Field ist es fast geschenkt | MEDIUM | Zwei Zeilen in `getSupportedFilters()`, ein Range-Query im Rewriter, eine Übersetzung in `Provider::search()`. Der größere Teil ist der Beweis, dass die Paginierung damit stabil bleibt |
| "Älteste zuerst" als dritte Sortierung | Kostet nach der Datumssortierung nur `Order.Asc`. Für Aktenrecherche ("der erste Schriftwechsel") der eigentlich gesuchte Fall | LOW | Erst bauen, wenn Desc steht |
| Die Wiederaufwärm-Zahl wird ausgewiesen statt versprochen | Die Beleg-Kultur des Projekts ist sein Verkaufsargument. "Nach X Minuten Leerlauf gibt der Container 415 MB zurück, die nächste Suche antwortet in Y ms lexikalisch und ab der übernächsten wieder semantisch" ist eine Aussage, die ein Admin prüfen kann | MEDIUM | Gehört in die Messphase der Box-Anfahrt, nicht in eine Schätzung. Eine Messzahl steht an drei Stellen (README.en.md, beide info.xml) |
| Vorwärmen im Hintergrund statt synchronem Nachladen | Ollama, Immich und LM Studio lassen alle die nächste Anfrage warten. Wer stattdessen sofort lexikalisch antwortet und im Hintergrund nachlädt, ist in dieser Klasse ungewöhnlich und passt exakt zur 1,5-Sekunden-Decke | MEDIUM | Ein Thread, der genau eine Ladung anstößt, mit dem bestehenden `LOAD_RETRY_SECONDS`-Muster gegen Dauerversuche |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Facettenzähler am Filter, "PDF (42)" | Jede Shop-Suche hat sie, sie wirken professionell | Der Zähler müsste vor dem Berechtigungsfilter gezogen werden und zählt damit Dokumente anderer Leute. Genau dieses Leck ist im Projekt bereits benannt und geschlossen (T-02-93, "counting oracle"), `CandidatePage` trägt deshalb bis heute **kein** Total | Filter ohne Zahlen. Wenn eine Gruppe leer ist, sagt das der leere Zustand nach dem Klick, nicht vorher |
| Filter ohne Suchbegriff, "zeig mir alle PDFs" | Die Files-App kann genau das | `build_query()` liefert bei einer Zeile aus nur einem Filter bewusst `None`: "No term, no engine". Ohne Begriff gibt es keine Rangfolge, und der ACL-Vorfilter müsste über den ganzen Bestand laufen statt über eine Trefferliste. Das ist die Umkehrung der Frage, die der Vorfilter beantwortet, und sein dokumentiertes Anti-Pattern | Der leere Zustand nennt den Grund in einem Satz und verweist auf den Typfilter der Dateiliste. Suche bleibt Suche, kein Dateibrowser |
| Sortierung nach Name oder Größe | Die Dateiliste sortiert so, die Erwartung wird mitgebracht | Name ist ein Textfeld ohne Fast-Spalte, Größe steht gar nicht im Index. Beides heißt: neues Schemafeld, `SCHEMA_VERSION`-Sprung, Vollreindex auf jeder Installation. Dazu die Sortierreihenfolge für Umlaute (DIN 5007) als eigenes Fass | Relevanz und Datum. Wenn später ohnehin ein Reindex ansteht, können `name_sort` und `size` mitgenommen werden. Bis dahin: nicht anbieten statt schlecht anbieten |
| Sortierung nur innerhalb der angezeigten 25 Zeilen, per JS | Schnell gebaut, sieht aus wie Sortierung | Sortiert die Seite, nicht das Ergebnis. Auf Seite 3 steht dann ein älterer Treffer als auf Seite 1. Das ist eine Lüge im UI und zerstört das Versprechen der Ergebnisseite | Serverseitige Sortierung über die ganze Trefferstrecke oder gar keine |
| Den UI-Filter einfach als `type:pdf` in die Suchzeile schreiben | Ein Dreizeiler, die Syntax existiert schon | `carried_operators()` markiert `type:` als `FILETYPE`, und `one_round()` schaltet daraufhin die Vektorhälfte ab. Jede gefilterte Suche wäre damit stumm rein lexikalisch, also schlechter als die ungefilterte. Der Nutzer sieht nur "mit Filter finde ich weniger" | Strukturiertes Feld in `SearchRequest` (etwa `types: list[str]`), das die Operator-Regel **nicht** auslöst, plus bewusste Entscheidung, wie die Vektorhälfte gefiltert wird (siehe Abhängigkeit D3) |
| Freitextfeld für beliebige Endungen im UI | "Ich will nach .eml filtern" | Endungen, die nie indexiert werden, erzeugen garantiert leere Ergebnisse und wirken wie ein Defekt. Außerdem zweites Vokabular neben den Gruppen | Geschlossene Gruppenliste im UI, `type:`-Syntax bleibt für Fortgeschrittene erhalten und ist dokumentiert |
| Entladung auch während der Indexierung | "TTL ist TTL" | `worker/poller.py` holt sich dasselbe Modell über `shared_model()` aus `embed/engine.py`. Eine TTL, die zwischen zwei Einbettungsbändern feuert, lädt 398,7 MB immer wieder neu und verlängert genau den Lauf, dessen Laufzeit in v1.1 schon um 40,9 Prozent gestiegen ist | TTL zählt ab der letzten Nutzung durch **irgendeinen** Aufrufer, und die zweite Spur hält das Modell, solange sie arbeitet. Gemessen, nicht angenommen |
| Aggressive TTL, etwa 60 Sekunden | Maximaler RAM-Gewinn | Auf einer Instanz mit ein paar Suchen pro Stunde zahlt praktisch jede Suche den Kaltstart. Der Gewinn ist Speicher, den niemand braucht, der Preis ist Latenz, die jeder merkt | Vorgabe im Bereich der Präzedenzfälle (Immich 300 s, Ollama 300 s, LM Studio 60 min) und am eigenen Messwert kalibriert. Konservativ starten, Zahl begründen |
| Admin-Schalter im Nextcloud-UI für die TTL | Wirkt bedienbarer als eine Umgebungsvariable | Der Container liest Umgebungsvariablen; der Weg von PHP in den Container ist die Schreib-Allowlist mit drei Einträgen und einem Test, der sie zählt. Ein Schalter für eine Speicheroptimierung ist kein Grund, ein Sicherheitstor zu erweitern | Umgebungsvariable plus Zeile in `docs/admin-page.md` und `docs/embeddings.md`. Die Admin-Seite **zeigt** den Zustand, sie **stellt** ihn nicht |
| Entladung als "Sparmodus" verkaufen | Klingt nach Feature | Wer gar keine Semantik will, hat `FINDLING_EMBED_ENABLED` bereits. Zwei Schalter für dieselbe Wirkung verwirren | Klar trennen: Entladung ist eine Leerlaufoptimierung, kein Abschalter |

---

## Feature Dependencies

```
[Typfilter UI auf der Ergebnisseite]
    └──requires──> [strukturiertes Filterfeld im /search-Vertrag]
                       └──requires──> [Entscheidung: ext-Term im Index ODER mime aus files-Tabelle]
                                          └──requires──> [Regel, wie die Vektorhaelfte gefiltert wird]

[Sortierung nach Datum]
    └──requires──> [order_by_field ueber mtime + Zweitschluessel file_id]
                       └──conflicts──> [RRF-Fusion aus index/fusion.py]

[Typfilter UI] ──requires──> [Cursorpfad-Invalidierung bei Filter- oder Sortwechsel]
[Sortierung]   ──requires──> [Cursorpfad-Invalidierung bei Filter- oder Sortwechsel]

[Zeitraumfilter since/until] ──enhances──> [Sortierung nach Datum]   (dieselbe mtime-Spalte)
[Zeitraumfilter since/until] ──repariert──> [stilles Verschwinden im Dialog, V2]

[Modell-Entladung im Leerlauf]
    └──requires──> [Halter in embed/engine.py kann freigeben]
    └──requires──> [nicht blockierender Erstzugriff: lexikalisch antworten, im Hintergrund waermen]
    └──requires──> [sechstes engineState-Wort + AdminViewService::ENGINE_STATES + drei Kataloge]
    └──conflicts──> [Einbettungsspur in worker/poller.py, shared_model()]

[Jede neue sichtbare Zeichenkette] ──requires──> [EN/DE/FR im Gleichstand, vier CI-Gates]
[Minor-Sprung auf 1.2.0]           ──requires──> [Migration im Muster Version001200Date...]
```

### Dependency Notes

- **D1, Typfilter braucht ein strukturiertes Feld, keinen Text.** `SearchRequest` in `backend/src/findling/api/search.py` hat `extra="forbid"`; ein neues Feld ist eine bewusste Vertragsänderung auf beiden Seiten. Der Umweg über die `type:`-Syntax ist ausdrücklich verboten (Anti-Feature), weil er die Semantik abschaltet.
- **D2, der Filterort entscheidet über Kosten und Genauigkeit.** Im Tantivy-Query (`FIELD_EXT`, `_extension_query()` existiert bereits) ist der Filter billig, weil die Engine gar nichts anderes liefert; er trifft aber nur die lexikalische Hälfte und arbeitet auf Endungen. In der SQLite (`files.mime`) ist er genauer und trifft beide Hälften, kostet aber einen Join im heißen Pfad, der heute ausdrücklich keinen hat.
- **D3, die Vektorhälfte kennt keinen Dateityp.** `store/vectors.py` liefert Nachbarn als `file_id`. Wird nur der Tantivy-Teil gefiltert, kommen über die semantische Hälfte Treffer der falschen Gruppe durch, und der Filter wirkt kaputt. Drei Auswege: Filter in der SQLite für beide Hälften (sauber), Nachfiltern der fusionierten Liste über eine Typabfrage (mittel), oder die gefilterte Suche bleibt lexikalisch (billig, aber dann muss die Seite das sagen).
- **D4, Sortierung schließt Fusion aus.** Rang entsteht relativ zu einer Liste; eine nach Datum sortierte Liste hat keine Ränge, die RRF verrechnen könnte, und die Vektorhälfte kann nichts nach Datum ordnen. Die saubere Regel ist die, die das Projekt schon kennt: wie `lexical_only` bei Operatoren fällt bei Datumssortierung die semantische Hälfte weg. Das ist kein Defekt, es ist die Definition. Es gehört aber in einen sichtbaren Satz auf der Seite oder in die Dokumentation.
- **D5, Paginierung hängt an der Ordnungsstabilität.** Der Cursorpfad zählt erlaubte Kandidaten, nicht Rohtreffer (`candidates()` in `index/search.py`). Das funktioniert für jede deterministische Ordnung. Gleiche `mtime`-Werte ohne Zweitschlüssel machen die Ordnung aber zwischen zwei Aufrufen instabil, und dann verdoppeln oder verschlucken sich Treffer beim Blättern.
- **D6, `_ranked()` liest heute Score-Tupel.** Mit `order_by_field` liefert tantivy den Fast-Field-Wert an der Stelle des Scores. Der Umbau ist klein, aber er trifft eine Funktion, die auf beiden Suchpfaden liegt.
- **D7, Entladung und Indexierung teilen einen Halter.** `worker/poller.py` importiert `shared_model` und `note_cutter_failure` aus `embed/engine.py`. Die TTL darf nicht nur den Suchpfad kennen.
- **D8, jeder neue Modellzustand ist ein Protokollwort.** `engine_state()` (Python) speist `status.py::engineState`, das `AdminViewService::ENGINE_STATES` gegen eine geschlossene Liste prüft, das `admin.php` in einen Satz übersetzt, der in EN/DE/FR stehen muss und in `docs/admin-page.md` als Tabellenzeile. Fünf Stellen für ein Wort.
- **D9, der Minor-Sprung braucht eine Migration.** Merker aus v1.1: jeder Minor-Sprung ohne Migration im Muster `Version001100Date20260911000000` endet in stummer Suche. Für 1.2.0 gilt das unverändert und unabhängig davon, dass der Index kompatibel bleibt.

---

## MVP Definition

### Launch With (v1.2)

- [ ] **Typfilter mit geschlossener Gruppenliste auf der Ergebnisseite**, Gruppen nur aus indexierbaren Typen, ohne Zähler, serverseitig, ohne JS bedienbar
- [ ] **Ein Filtervokabular**, das UI-Gruppen und `type:`-Syntax zur Deckung bringt
- [ ] **Sortierung Relevanz (Vorgabe) und Zuletzt geändert**, mit Zweitschlüssel gegen Zeitstempel-Gleichstand
- [ ] **Filter und Sortierung in der URL**, defensive Leseart, unbekannte Werte still auf die Vorgabe
- [ ] **Cursorpfad wird bei jedem Filter- oder Sortwechsel verworfen**, Rückfall auf Seite 1
- [ ] **Leerer Zustand nennt den aktiven Filter und bietet das Entfernen an**
- [ ] **Eine ehrliche Zeile zur Semantik**, wenn nach Datum sortiert wird und die Hybridhälfte deshalb entfällt
- [ ] **Modell-Entladung nach Leerlauf**, TTL als Umgebungsvariable, `0` schaltet ab
- [ ] **Erste Suche nach Entladung antwortet lexikalisch innerhalb der 1,5-Sekunden-Decke**, Nachladen im Hintergrund
- [ ] **TTL feuert nie gegen die laufende Einbettungsspur**
- [ ] **Sechstes `engineState`-Wort**, Satz auf der Admin-Seite in EN/DE/FR, Zeile in `docs/admin-page.md`
- [ ] **Wiederaufwärm-Kosten gemessen und ausgewiesen**, in derselben Box-Anfahrt wie der Wirkungsbeleg
- [ ] **Migration für 1.2.0**, sonst stumme Suche nach dem Upgrade

### Add After Validation (v1.x)

- [ ] **Zeitraumfilter `since`/`until`**, samt Erweiterung von `getSupportedFilters()`. Auslöser: sobald die Datumssortierung steht, ist die Range-Abfrage fast fertig, und sie repariert das stille Verschwinden im Dialog
- [ ] **"Älteste zuerst"**. Auslöser: erste Rückmeldung, die nach dem ältesten Schriftstück fragt
- [ ] **Mehrfachauswahl von Gruppen**. Auslöser: `_extension_query()` kann ODER bereits; das UI wird nur dann mehrfachfähig, wenn jemand danach fragt
- [ ] **Ordner-Einschränkung ("nur in diesem Ordner")**. Auslöser: Nachfrage; Vorarbeit liegt mit `storage_id` im Schema, aber `path` ist bewusst nicht indexiert

### Future Consideration (v2+)

- [ ] **Sortierung nach Name und Größe**. Verschoben, weil sie ein Schemafeld und damit einen Vollreindex kostet. Nur zusammen mit einem ohnehin fälligen Reindex, und dann mit sauberer Umlautsortierung
- [ ] **Facetten mit Zählern**. Verschoben, bis es eine Zählung gibt, die den Berechtigungsfilter nicht umgeht. Heute wäre sie ein Zählorakel
- [ ] **Personenfilter**. Verschoben: Findling indexiert Inhalte, nicht Urheberschaft; die Zuordnung käme aus Nextcloud und wäre eine zweite Berechtigungsgrenze
- [ ] **Modell-Vorwärmen nach Zeitplan**, etwa morgens vor Arbeitsbeginn. Verschoben: erst messen, ob die TTL überhaupt stört

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Typfilter mit Nextcloud-Gruppen | HIGH | MEDIUM | P1 |
| Cursor-Invalidierung bei Filter- oder Sortwechsel | HIGH (Korrektheit) | LOW | P1 |
| Sortierung Relevanz und Zuletzt geändert | HIGH | MEDIUM | P1 |
| Filter und Sortierung in der URL, ohne JS bedienbar | MEDIUM | LOW | P1 |
| Leerer Zustand nennt den Filter | MEDIUM | LOW | P1 |
| Entladung mit nicht blockierendem Erstzugriff | HIGH (415 MB auf 4-GB-Boxen) | HIGH | P1 |
| TTL abschaltbar per Umgebungsvariable | MEDIUM | LOW | P1 |
| Sechstes `engineState`-Wort plus Kataloge | MEDIUM | LOW | P1 |
| Wiederaufwärm-Messung im Bericht | HIGH (Beleg-Kultur) | MEDIUM | P1 |
| Zeitraumfilter `since`/`until` | MEDIUM bis HIGH (repariert stille Lücke) | MEDIUM | P2 |
| Mimetype-Gruppen aus `files.mime` statt `ext` | MEDIUM (Genauigkeit) | MEDIUM | P2 |
| "Älteste zuerst" | LOW bis MEDIUM | LOW | P2 |
| Mehrfachauswahl von Gruppen | LOW | LOW | P3 |
| Ordner-Einschränkung | MEDIUM | HIGH | P3 |
| Sortierung Name und Größe | MEDIUM | HIGH (Reindex) | P3 |
| Facetten mit Zählern | LOW | HIGH (Sicherheitsproblem) | P3, eher nie |

---

## Competitor Feature Analysis

### Filter und Sortierung

| Feature | Nextcloud Files-App (NC 30+) | Nextcloud Unified Search | Paperless-ngx | Unser Ansatz |
|---------|------------------------------|--------------------------|---------------|--------------|
| Typfilter | Chips: Documents, Spreadsheets, Presentations, PDFs, Folders, Audio, Images, Videos, über Mime-Aliase | gibt es nicht | Dokumenttyp, Korrespondent, Tags | Dieselben Wörter, gekürzt auf indexierbare Typen, ohne Ordner, Audio und Video |
| Zähler an den Filtern | nein | entfällt | teils | nein, und begründet (Zählorakel) |
| Sortierung | Name, Größe, Geändert über Spaltenköpfe, clientseitig über die geladene Liste | keine | Score als Vorgabe bei Volltext, dazu Sortierfelder | Relevanz als Vorgabe, Zuletzt geändert serverseitig; Name und Größe bewusst nicht |
| Filter ohne Suchbegriff | ja, filtert die Ordneransicht | entfällt | ja, filtert die Dokumentliste | nein, mit Verweis auf die Dateiliste |
| Filterwirkung auf die Paginierung | keine Paginierung, die Liste ist geladen | Gruppe mit "mehr" | serverseitige Seiten | Cursorpfad wird verworfen, Rückfall auf Seite 1 |
| Verfügbare Filter im Dialog | entfällt | Orte/Provider, Datum, Person; ein Provider ohne passende Deklaration wird stumm übersprungen | entfällt | Dialog bleibt bei `term` und `title-only`; der Typfilter lebt auf der eigenen Seite |

### Modell-Entladung im Leerlauf

| Aspekt | Immich (Machine Learning) | Ollama | LM Studio | Unser Ansatz |
|---|---|---|---|---|
| Vorgabe-TTL | 300 s | 300 s (5 min) | 60 min für per API geladene Modelle | am eigenen Messwert kalibrieren, konservativ, Zahl begründen |
| Abschalten | `MACHINE_LEARNING_MODEL_TTL=0` | `OLLAMA_KEEP_ALIVE=-1` oder `24h` | TTL je Anfrage oder App-Vorgabe | Umgebungsvariable, `0` bedeutet nie entladen |
| Kosten der nächsten Anfrage | Nutzer wartet auf das Nachladen | Nutzer wartet, je nach Modell Sekunden bis zehner Sekunden | Nutzer wartet | **Nutzer wartet nicht**: sofort lexikalische Treffer, Semantik ab der nächsten Suche |
| Sichtbarkeit | Logzeile | `ollama ps` | UI | Admin-Seite nennt den Zustand als eigenes Wort mit eigenem Satz |
| Konflikt mit Hintergrundarbeit | kaum thematisiert | kaum thematisiert | Auto-Evict beim Modellwechsel | ausdrückliche Regel: die TTL feuert nie gegen die laufende Einbettungsspur |

---

## Offene Fragen für die Planung

1. **Filterort:** `ext` im Tantivy-Query oder `mime` in der SQLite? Entscheidet über Genauigkeit, über die Wirkung auf die Vektorhälfte und darüber, ob `prefilter_visible()` seinen Kommentar "no join against files" verliert (Abhängigkeiten D2, D3).
2. **Semantik bei Datumssortierung:** Der Wegfall ist technisch zwingend (D4). Offen ist nur, ob die Seite das sagt oder ob es in der Dokumentation steht.
3. **TTL-Vorgabewert:** erst nach der Wiederaufwärm-Messung festlegen. Die Präzedenzfälle spannen 300 s bis 60 min auf, und der eigene Kaltstart liegt gefährlich nah an der 1.501-ms-Decke.
4. **Wortwahl des sechsten Zustands** (`unloaded`, `idle`, `released`) samt Satz in drei Katalogen. Die alte Companion-Hälfte zeigt in jedem Fall den Ersatzsatz, das ist geprüft und harmlos.
5. **Zeitraumfilter mitnehmen oder vertagen?** Er repariert eine stille Lücke, teilt sich die ganze mtime-Mechanik mit der Sortierung und wäre nach v1.2 deutlich teurer, weil die Mechanik dann wieder aufgemacht werden müsste.

---

## Sources

**Eigener Quellcode und eigene Messberichte (HIGH):**
- `backend/src/findling/index/schema.py`, `index/search.py`, `index/fusion.py`, `query/rewrite.py`, `api/search.py`, `api/status.py`, `embed/engine.py`, `extract/dispatch.py`, `store/schema.sql`, `store/repo.py`, `worker/poller.py`
- `php/lib/Search/Provider.php`, `php/lib/Controller/PageController.php`, `php/lib/Service/ExAppService.php`, `php/lib/Service/AdminViewService.php`, `php/lib/Service/SettingsService.php`, `php/templates/search.php`, `php/templates/admin.php`, `php/js/search.js`, `php/tests/Unit/AdminViewServiceTest.php`
- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` (Abschnitte 5.3, 6, 9), `docs/measurements/2026-09-05-semantiklauf-m7g/README.md`, `docs/admin-page.md`
- tantivy-Python-Stub im Projekt-venv, `tantivy/tantivy.pyi` (`order_by_field`, `Order`, `range_query(use_inverted_index=False)`)

**Nextcloud, offiziell (HIGH):**
- Developer Manual, Search: https://docs.nextcloud.com/server/stable/developer_manual/digging_deeper/search.html (Filternamen `term`, `since`, `until`, `person`, `min-size`, `max-size`, `mime`, `type`; "If filters send by client are not supported, the provider will not receive the request.")
- `nextcloud/server`, `core/src/components/UnifiedSearch/UnifiedSearchModal.vue` (nur Orte, Datum, Person)
- `nextcloud/server`, `apps/files/src/filters/TypeFilter.ts` und `apps/files/src/components/FileListFilter/FileListFilterType.vue` (die acht Typ-Presets)
- `nextcloud/server`, `resources/config/mimetypealiases.dist.json` (Mime-Aliase auf `x-office/document`, `x-office/spreadsheet`, `x-office/presentation`)
- PR nextcloud/server#45708, Dateilisten-Filter

**Fremdprodukte als Erwartungsmaßstab (MEDIUM):**
- Immich, `MACHINE_LEARNING_MODEL_TTL`, Vorgabe 300 s, `0` schaltet ab
- Ollama FAQ, `OLLAMA_KEEP_ALIVE`, Vorgabe 5 Minuten, https://docs.ollama.com/faq
- LM Studio, Idle TTL und Auto-Evict, Vorgabe 60 Minuten für per JIT geladene Modelle, https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
- Paperless-ngx, Volltexttreffer nach Score sortiert, Filter nach Dokumenttyp, https://docs.paperless-ngx.com/
- Nielsen Norman Group, Filter- und Sortier-Leitlinien (einklickbares Entfernen, Sortiervorgaben am Nutzermodell), https://www.nngroup.com/

---
*Feature research for: Dateityp-Filter, Sortierung und Modell-Entladung im Leerlauf (Findling v1.2)*
*Researched: 2026-09-14*
