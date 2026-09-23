# Pitfalls Research

**Domain:** Lexikalischer Sprachausbau (es/it/nl/pt) in einer bestehenden Tantivy-Suche auf Bestandsinstallationen
**Researched:** 2026-09-23
**Confidence:** HIGH für alles, was unten mit "gemessen" steht (in der ausgelieferten tantivy 0.26.0 aus `backend/.venv` nachgefahren, plus Quelltext und Messberichte dieses Repositoriums); MEDIUM für die Nextcloud-Katalogpunkte (aus `nextcloud/server` master gelesen, nicht gegen eine laufende Instanz geprüft)

Alle Ergebnisse in diesem Dokument sind entweder am Quelltext dieses Repositoriums
oder an der installierten Bibliothek nachgemessen. Wo eine Zahl aus einer fremden
Quelle stammt, steht die Quelle daneben. Die Reihenfolge ist Schwere, nicht
Bearbeitungsreihenfolge; die Bearbeitungsreihenfolge steht am Ende in der
Phasen-Zuordnung.

---

## Critical Pitfalls

### Pitfall 1: Das neue Schema erreicht den Bestandsindex nie, und danach beantwortet die Suche gar nichts mehr

**What goes wrong:**

Die vier Sprachfelder werden in `build_schema()` ergänzt, `SCHEMA_VERSION` wird
erhöht, die Tests sind grün, die Fremdinstallation in CI ist grün. Auf jeder
Installation, die schon ein Indexverzeichnis hat, passiert dann drei Dinge
hintereinander, und keines davon erzeugt eine Fehlermeldung an der Stelle, an
der es entsteht:

1. `open_index()` nimmt bei vorhandenem Verzeichnis den Zweig
   `Index.open(str(path))` (`backend/src/findling/index/open.py`). Das neue
   Schema aus `build_schema()` wird in diesem Zweig nie angefasst. Der Index
   behält seine neun alten Felder.
2. Der Schreibpfad legt `body_es` an. Gemessen in tantivy 0.26.0:
   `Document.from_dict({"body_de": ..., "body_es": ...}, schema)` gibt
   `{'body_de': ['hola mundo']}` zurück, ohne Fehler und ohne Warnung, und
   `add_document(body_es=...)` läuft ebenfalls fehlerfrei durch. Spanisch wird
   also niemals indexiert. Genau dieser Befund steht schon als Kommentar in
   `backend/src/findling/index/schema.py` ("Document.from_dict silently drops a
   name the schema does not know").
3. Der Lesepfad ist schlimmer. Gemessen:

   ```
   idx.parse_query_lenient("hola", default_field_names=["body_de", "body_es"])
   -> ValueError: Field `body_es` is not defined in the schema.
   ```

   Das ist keine Zeile in der Fehlerliste des lenient-Parsers, sondern eine
   geworfene Ausnahme. `findling/query/rewrite.py` fängt um
   `index.parse_query_lenient(...)` nichts ab. Jede Suche, in jeder Sprache,
   läuft damit in einen Fehler, die PHP-Hälfte bekommt keine Antwort und
   liefert ein leeres `SearchResult`.

Ergebnis auf einer Bestandsinstallation: nach dem Update findet die Suche
**nichts mehr**, nicht nur kein Spanisch. Und zwar still, weil die
Companion-App einen nicht antwortenden Container per Entwurf als leeres
Ergebnis behandelt.

Zur Vollständigkeit, ebenfalls gemessen: der andere Zweig ist kein Ausweg.
`Index(neues_schema, path=vorhandenes_verzeichnis)` wirft
`ValueError: Schema error: 'An index exists but the schema does not match.'`.
Ein Tantivy-Index hat keine additive Schema-Migration. Das Verzeichnis muss neu
gebaut werden.

**Why it happens:**

Die Entwicklungsumgebung und jede CI-Strecke, die frisch installiert, nehmen
immer den `Index(build_schema(), ...)`-Zweig. Der Fall "Verzeichnis existiert
schon, Schema im Code ist neuer" kommt lokal nie vor. Die Projektlehre "jeder
Minor-Sprung braucht eine Migration, sonst stumme Suche" zielt heute auf die
PHP-Lockstep-Migration (`Version001200Date20260921000000`) und nicht auf das
Indexverzeichnis; wer die Lehre befolgt, schreibt die PHP-Migration und hält
damit den Punkt für erledigt.

**How to avoid:**

- `open_index()` bekommt einen dritten Zweig: Verzeichnis existiert **und** das
  gelesene Schema trägt nicht alle Felder, die `build_schema()` erzeugt. Dieser
  Zweig öffnet nicht, sondern löst den Neubau aus. Der Vergleich läuft über
  die Feldnamen des gelesenen Schemas gegen `FIELDS`, nicht über
  `SCHEMA_VERSION`: die Marke sagt, was das Verzeichnis sein sollte, das
  gelesene Schema sagt, was es ist, und nur das zweite ist die Wahrheit.
- Der Neubau ist ein **neues Verzeichnis** (`index.new` daneben, danach
  Umbenennen), nicht ein Überschreiben. Ein Abbruch mitten im Neubau darf den
  alten Index nicht kaputt hinterlassen.
- Ein Test, der das Bestandsverzeichnis wirklich herstellt: Index mit dem
  v1.2-Schema anlegen, Dokumente schreiben, schließen, dann den v1.3-Code
  darauf loslassen. Ein Test, der ein frisches Verzeichnis benutzt, ist zu
  diesem Fehler blind, und genau das ist der Grund, warum er heute nicht
  auffällt.

**Warning signs:**

- Im Containerlog nach einem Update steht keine einzige Zeile von
  `start_rebuild_on_drift`, obwohl `SCHEMA_VERSION` erhöht wurde.
- `GET /status` meldet unveränderte Dokumentzahlen und `reindexRequired=false`.
- Die Suche wirft `Field ... is not defined in the schema` oder antwortet
  überall leer, während die semantische Hälfte weiter Treffer liefert.

**Phase to address:**

Erste Bauphase (Schema und Migration), vor jeder Arbeit an den Analyseketten.
Alles andere in diesem Milestone hängt daran.

---

### Pitfall 2: Der Reindex wird als volle Neuextraktion gebaut, obwohl der Text schon im Index liegt

**What goes wrong:**

Der übliche Weg für "Schema geändert, also Reindex" ist: Generation erhöhen,
alle Verdikte veralten lassen, Crawl über alle Mounts, jede Datei neu holen,
neu extrahieren, neu OCRn, neu einbetten. Auf der Zielhardware ist das gemessen
teuer: der v1.2-Volllauf über 52.137 Dateien auf m7g.large (2 Kerne, 4 GB,
`INDEX_WORKERS=1`) lief **19 h 20 min**
(`docs/measurements/2026-09-v12-messung/README.md`, Abschnitt zum Volllauf).
Ein Minor-Update, das auf einer 4-GB-Box knapp einen Tag Volllast erzeugt, die
CPU des Hosts für alles andere wegnimmt und die Suche währenddessen leer
laufen lässt, ist auf einer Selfhoster-Box kein Update, sondern ein Ausfall.

**Why it happens:**

Der einzige Rebuild-Weg, den das Projekt heute hat, ist genau dieser:
`start_rebuild_on_drift` hebt die Generation, und der Crawl liest die Dokumente
wieder von Nextcloud. Der Weg ist für Analyzer- und Wortlisten-Drift gebaut
worden, wo er auch richtig ist, weil dort niemand einen billigeren Weg hatte.

**How to avoid:**

Für diesen Milestone gibt es einen billigeren Weg, und er ist im Repositorium
schon halb gebaut. **Jedes Feld, das ein Dokument braucht, ist stored:**
`file_id`, `storage_id`, `name`, `title`, `path`, `ext`, `body_de` und `mtime`
(`backend/src/findling/index/schema.py`). `body_en` ist nicht stored, trägt
aber denselben Text wie `body_de`. Der Volltext liegt also vollständig im
alten Index. `IndexWriter.stored_body()` nutzt genau das heute schon für
Umbenennungen ("a rename costs no download").

Also: **Re-Analyse statt Re-Extraktion.** Der Neubau liest die Dokumente
Segment für Segment aus dem alten Index und schreibt sie in das neue
Verzeichnis mit dem neuen Schema. Kein Gateway-Aufruf, kein Download, kein
OCR-Lauf, keine Einbettung, keine Berührung der Nutzerdateien, keine
Änderung an der Zustands-DB und keine an den Vektoren. Das verwandelt einen
Tag in einen Lauf, dessen Kosten allein die Analysekette bestimmt, und die
Analysekette ist der billige Teil.

Dazu gehören drei Auflagen:

- **Wiederaufnehmbar.** Der Lauf muss nach einem Containerneustart dort
  weitermachen, wo er war (Fortschritt in der DB, wie es die
  Betriebsregeln des Projekts ohnehin verlangen), sonst fängt eine Box, die
  nachts neu startet, jeden Morgen von vorn an. Das ist derselbe Fehler, gegen
  den `REBUILD_MARK` in `open.py` schon einmal gebaut wurde.
- **Platz.** Während des Umbaus liegen zwei Indexverzeichnisse nebeneinander.
  Der Index ist gemessen 0,374 mal den extrahierten Text groß; das neue kommt
  in voller Größe daneben. `MIN_FREE_BYTES` (500 MB) ist dafür zu knapp
  bemessen: die Prüfung vor dem Start muss die erwartete Größe des neuen
  Verzeichnisses addieren und sonst mit einer klaren Meldung abbrechen, statt
  mitten im Umbau in `paused_low_disk` zu laufen.
- **Rückfallweg.** Wenn die Re-Analyse an einem Dokument scheitert, darf sie
  nicht das ganze Verzeichnis verwerfen. Fehlerhafte Dokumente kommen auf die
  normale Neu-Extraktion, gezählt und sichtbar.

**Warning signs:**

- Im Planungstext steht "Reindex" ohne das Wort "aus dem gespeicherten Text".
- Der Rebuild-Pfad ruft irgendetwas unter `findling/nc/` oder `findling/extract/`
  auf.
- Der Fortschritt hängt am Cron-Intervall der Instanz. Dann ist es wieder der
  Crawl, und der Leerlaufanteil von v1.1 (22,0 Prozent) kommt zurück.

**Phase to address:**

Phase Schema und Migration, als eigener Plan neben dem Schema selbst.

---

### Pitfall 3: Die bestehende Upgrade-Beweisstrecke beweist das Gegenteil, und jemand repariert sie durch Löschen

**What goes wrong:**

`.github/workflows/deploy-harp.yml`, Schritt "Store upgrade 5, the six
assurances after the upgrade", behauptet heute wortwörtlich:

- die fünf Marken `schemaVersion`, `indexVersion`, `analyzerVersion`,
  `wordlistHash`, `tantivyVersion` sind **unverändert** ("a moved mark is a full
  reindex on every installation in the field (D-04)"),
- das Adminbanner für den Reindex erscheint **nicht**,
- im Containerlog steht **keine** Zeile `built by different code`,
- die Trefferzahlen für `Belehrung`, `Auszug`, `Erinnerung` und alle
  Dokumentzähler sind identisch.

v1.3 verletzt jede einzelne dieser Zusagen mit Absicht. Die Strecke wird also
rot, und der bequeme Weg ist, die Behauptungen zu entschärfen oder den Schritt
zu überspringen. Danach hat das Projekt für den einen Milestone, in dem der
Upgrade-Pfad zum ersten Mal wirklich gefährlich ist, gar keinen Upgrade-Beweis
mehr.

Zweitens deckt die Strecke den Fall auch inhaltlich nicht ab: sie prüft nur,
dass sich nichts ändert. Sie hat keine einzige Behauptung der Form "nach dem
Umbau findet eine Suche ein Dokument, das vor dem Update indexiert wurde, über
das neue spanische Feld". Genau das ist aber der Beweis, den v1.3 braucht.

Drittens steht `UPGRADE_FROM_TAG` auf `v1.1.0` und muss auf `v1.2.0`.

**Why it happens:**

Die Strecke ist als D-04-Wächter gebaut worden ("v1.1 index-kompatibel, kein
Reindex"). D-04 gilt in v1.3 nicht mehr. Eine Zusage, deren Voraussetzung
weggefallen ist, sieht im Diff wie ein defekter Test aus.

**How to avoid:**

Die Strecke wird nicht entschärft, sondern **umgedreht**, als eigener Schritt
neben dem alten (der für künftige index-kompatible Minors erhalten bleibt).
Die v1.3-Fassung behauptet:

1. `schemaVersion` hat sich bewegt, und zwar genau um eine Stufe.
2. Das Containerlog trägt **genau eine** Zeile `built by different code`, nicht
   null und nicht zwei (zwei hieße: der Neustart hat den Umbau neu angestoßen,
   also greift `REBUILD_MARK` nicht).
3. Das Adminbanner steht während des Umbaus und ist danach weg.
4. Nach Abschluss des Umbaus sind die Trefferzahlen für `Belehrung`, `Auszug`,
   `Erinnerung` **wieder identisch mit den Werten vor dem Update**. Das ist die
   scharfe Behauptung: der Umbau hat nichts verloren.
5. Ein Dokument, das vor dem Update indexiert wurde und spanischen Text
   enthält, wird nach dem Umbau über einen spanischen Suchbegriff gefunden,
   dessen Stamm sich vom Wortlaut unterscheidet (also nicht ein Treffer, den
   auch die alte Kette geliefert hätte).
6. Während des Umbaus antwortet die Suche mit einem Fehler **nicht**: sie
   antwortet mit weniger Treffern und mit dem Banner. Eine Kanarienabfrage
   mitten im Umbau gehört in die Strecke.
7. Kein Nextcloud-Aufruf und kein OCR-Prozess während des Umbaus (Pitfall 2).
   Nachweisbar über die Zähler in `GET /status` und das Containerlog.

**Warning signs:**

Ein Diff an `deploy-harp.yml`, der Zeilen aus "Store upgrade 5" entfernt, statt
einen zweiten Schritt danebenzustellen.

**Phase to address:**

Phase Schema und Migration (die Strecke wird zusammen mit dem Umbauweg
geschrieben, nicht erst in der Härtung). In der Härtungsphase wird sie nur
noch einmal gefahren.

---

### Pitfall 4: `ascii_fold()` an der falschen Stelle der Kette zerstört Stemmer und Stoppwortliste

**What goes wrong:**

Die englische Kette dieses Projekts lautet
`lowercase -> ascii_fold -> stopword -> remove_long -> stemmer`. Wer die vier
neuen Ketten nach diesem Muster baut (und das ist das naheliegende Muster, es
steht direkt daneben in `analyzer.py`), bekommt in drei von vier Sprachen
kaputte Analyse. Gemessen in tantivy 0.26.0, dieselbe Kette einmal mit
`ascii_fold` vor dem Stemmer und einmal danach:

| Sprache | Eingabe | ohne fold | fold **vor** stemmer | fold **nach** stemmer |
|---|---|---|---|---|
| es | `información informaciones` | `inform`, `inform` | **`informacion`, `inform`** | `inform`, `inform` |
| es | `año ano` | `año`, `ano` | `ano`, `ano` | `ano`, `ano` |
| it | `perché più` | (beide als Stoppwort entfernt) | **`perc`, `piu` bleiben stehen** | (beide entfernt) |
| pt | `informação informações` | `inform`, `inform` | **`informaca`, `informaco`** | `inform`, `inform` |
| nl | `één` | `een` | **verschwindet ganz** | `een` |

Was dabei passiert: der Snowball-Stemmer für Spanisch, Italienisch und
Portugiesisch erwartet die akzentuierte Form. Nimmt man die Akzente vorher weg,
greifen die Suffixregeln nicht mehr, und `información` bleibt als
`informacion` stehen, während `informaciones` zu `inform` wird. Die beiden
teilen dann keinen Term. Genauso die Stoppwortlisten: die italienische Liste
enthält `perché` mit Akzent und vergleicht exakt, also überlebt `perc` die
Filterung und landet als Müllterm im Index. Im Niederländischen ist es noch
hässlicher: `één` (die Zahl eins) faltet zu `een` und wird dann von der
Stoppwortliste als unbestimmter Artikel gelöscht, das Wort ist weg.

Das ist exakt derselbe Fehlertyp, den das Projekt für Deutsch schon einmal
gefunden und im Modulkopf von `analyzer.py` aufgeschrieben hat ("The German
branch has no folding filter"). Der Unterschied: für Deutsch war die Lösung
"gar nicht falten", weil der deutsche Stemmer selbst faltet. Für die vier
neuen Sprachen ist "gar nicht falten" nur die halbe Lösung, denn dann findet
`ano` das Dokument mit `año` nicht, und Nutzer tippen Akzente oft nicht.

**Why it happens:**

Die gängige Empfehlung im Netz (und die Formulierung mancher Solr-Beispiele)
lautet "Normalisierung vor Stemming". Für die germanischen Sprachen stimmt das
meistens, für die romanischen Snowball-Algorithmen stimmt es nicht. Wer die
Regel übernimmt, statt sie zu messen, baut den Fehler ein, und keine der
vorhandenen Prüfungen wird rot: die Kette produziert ja Tokens.

**How to avoid:**

- Kettenreihenfolge für es/it/pt/nl:
  `lowercase -> stopword(lang) -> remove_long(48) -> stemmer(lang) -> ascii_fold`.
  Das Falten **hinter** dem Stemmer liefert gemessen beides: intakte Stammformen
  und akzentunempfindliche Terme.
- Die Abfrageseite läuft durch dieselbe Kette (das tut sie über das
  registrierte Tokenizer-Objekt automatisch), also ist die Symmetrie gegeben,
  solange niemand für die Abfrage eine zweite Kette baut.
- `ANALYZER_VERSION` erhöhen. Die Marke steht bewusst in `analyzer.py` neben
  den Ketten; jede neue Kette ist eine Änderung an der Tokenisierung.
- Pro Sprache eine Handvoll Wortpaare als Tabellentest, im Muster der
  Messtabelle oben: Eingabe, erwartete Tokens, und zwar Paare, die sich genau
  dann treffen, wenn die Reihenfolge stimmt (`información`/`informaciones`,
  `informação`/`informações`, `perché` als Stoppwort, `año`/`ano`,
  `één`/`een`). Ein Test, der nur prüft "die Kette liefert nicht-leere
  Tokens", ist wertlos.

**Warning signs:**

Ein Stammformtest, der nur mit akzentfreien Wörtern arbeitet. Der ist grün,
egal wo `ascii_fold` steht.

**Phase to address:**

Phase Analyseketten, mit der Messtabelle als Abnahmekriterium.

---

### Pitfall 5: Ein unvalidierter Sprachname bringt den Container mit einem Rust-Panic zu Fall

**What goes wrong:**

`FINDLING_LANGUAGES` soll ab v1.3 mehr als eine Teilmenge von `("de","en")`
zulassen. Wenn der Wert des Admins ohne geschlossene Positivliste in
`Filter.stemmer()` und `Filter.stopword()` wandert, gibt es drei verschiedene
Ausgänge, und zwei davon sind schlecht. Gemessen in tantivy 0.26.0:

| Sprachname | `Filter.stemmer(...)` | `Filter.stopword(...)` |
|---|---|---|
| german, english, french, spanish, italian, dutch, portuguese, danish, russian, norwegian, swedish, finnish, hungarian | ok | ok |
| greek, arabic, turkish, tamil, romanian | ok | **PanicException, `Option::unwrap()` on a `None` value** (`src/tokenizer.rs:388`) |
| estonian, catalan, hindi, indonesian, irish, armenian, basque, bengali, latvian, nepali | ValueError | ValueError |

Zwei Punkte daran sind nicht offensichtlich:

1. Fünf Sprachen haben einen Stemmer, aber keine Stoppwortliste, und das Fehlen
   erzeugt **keinen Python-Fehler, sondern einen Rust-Panic**, der als
   `pyo3_runtime.PanicException` hochkommt. Ein Panic in einer
   Erweiterungsbibliothek ist keine Ausnahme, die man sauber behandelt; er
   schreibt eine Panikmeldung auf stderr und kann den Interpreterzustand
   hinterlassen, wie er will.
2. Die Prüfung passiert **nicht** bei `Filter.stemmer("unsinn")`, das läuft
   fehlerfrei durch, sondern erst beim Anhängen an den
   `TextAnalyzerBuilder`. Ein Konstruktionstest, der nur `Filter.stemmer(x)`
   aufruft, ist also grün und beweist nichts.

Gutnachricht für diesen Milestone: es, it, nl, pt haben beide Filter, und dan
(für die OCR-Zusage an OS2ai) ebenfalls. Est und cat haben **keinen** Stemmer;
wer also später Estnisch oder Katalanisch lexikalisch nachrüsten will, kann
das mit tantivy 0.26 nicht.

**Why it happens:**

`OCR_LANGUAGE_ALLOWLIST` existiert bereits und ist genau gegen diese Klasse von
Fehler gebaut (T-03-502). Der Indexpfad hat heute kein Gegenstück, weil
`_languages()` nur filtern und nie hinzufügen kann und das Problem daher nicht
haben konnte.

**How to avoid:**

- Eine geschlossene Tabelle im Code: Sprachcode (`es`) auf Feldname
  (`body_es`), Tokenizername (`es`), Snowball-Name (`spanish`). Genau eine
  Tabelle, aus der Schema, Analyzer-Registrierung, Abfragefelder und Boosts
  gelesen werden. Vier getrennte Listen sind vier Gelegenheiten zu driften.
- Ein Test, der jede Sprache der Tabelle wirklich **durch den Builder
  anhängt** und analysiert, nicht nur den Filter konstruiert.
- Ein unbekannter Wert in `FINDLING_LANGUAGES` wird verworfen und geloggt
  (Muster von `_ocr_languages()`), nie durchgereicht.

**Warning signs:**

`getattr(Filter, ...)` oder ein f-String, der aus einem Konfigurationswert einen
Snowball-Namen bildet.

**Phase to address:**

Phase Analyseketten, zusammen mit der Sprachtabelle.

---

### Pitfall 6: Die Sprachauswahl steht nicht in den Versionsmarken, also merkt niemand, wenn sie sich ändert

**What goes wrong:**

`expected_versions()` in `open.py` führt `schema_version`, `index_version`,
`analyzer_version`, `wordlist_hash`, `tantivy_version`. Die **Menge der
aktiven Sprachen steht nicht darin**. Heute ist das harmlos, weil
`FINDLING_LANGUAGES` nur zwischen `de`, `en` und beiden wählen kann und kaum
jemand daran dreht. Ab v1.3 wird das Umschalten zur normalen Amtshandlung: der
niederländische Verein installiert Findling, merkt nach zwei Wochen, dass
`nl` nicht an ist, setzt die Variable und startet den Container neu.

Was dann passiert: das Feld `body_nl` existiert im Schema, der Analyzer wird
registriert, aber **keine der 52.000 bestehenden Zeilen wird neu geschrieben**,
weil sich keine Marke bewegt hat. `is_unchanged()` vergleicht Inhaltshash und
Generation, beide unverändert. Nur neu angefasste Dateien bekommen
niederländische Terme. Die Suche liefert dauerhaft zu wenig, und der Admin hat
keinen Hinweis, dass etwas fehlt, weil er ja Treffer bekommt.

**Why it happens:**

Das Feld existiert, also "ist die Sprache da". Der Unterschied zwischen
"Schema kennt das Feld" und "Feld ist für den Bestand gefüllt" ist genau die
Art Unterschied, die man in einem Statusbildschirm nicht sieht.

**How to avoid:**

- `expected_versions()` bekommt eine Marke `languages`, deren Wert die sortierte
  aktive Sprachmenge ist. Damit greift `start_rebuild_on_drift` beim Umschalten
  automatisch und die bestehende Banner- und Generationsmechanik erledigt den
  Rest. Das ist eine Zeile Code und die billigste Prävention in diesem ganzen
  Dokument.
- Achtung auf den Gegenlauf: die Marke muss auch beim **Abschalten** einer
  Sprache greifen. Sonst bleiben Terme einer nicht mehr gewünschten Sprache im
  Index stehen und blähen ihn auf, ohne dass sie je aufgeräumt werden.
- Der Neubau beim reinen Sprachwechsel ist wieder Pitfall 2: Re-Analyse aus dem
  gespeicherten Text, keine Neuextraktion. Ein Sprachwechsel darf keine 19
  Stunden OCR auslösen.
- `GET /status` und die Adminseite nennen die aktiven Sprachen **und** die Zahl
  der Dokumente, die unter der aktuellen Sprachmenge geschrieben wurden.

**Warning signs:**

Die Adminseite zeigt "Sprachen: de, en, nl" und zugleich "0 Dokumente
ausstehend". Beides zusammen ist auf einer Bestandsinstallation eine Lüge.

**Phase to address:**

Phase Schema und Migration.

---

### Pitfall 7: Während des Umbaus ist die lexikalische Suche leer, und niemand hat es angekündigt

**What goes wrong:**

`body_de` ist die einzige gespeicherte Kopie des extrahierten Texts im ganzen
System, und der Snippet-Generator schneidet daraus. Während das neue
Indexverzeichnis gefüllt wird, gibt es für noch nicht umgeschriebene
Dokumente in diesem Verzeichnis weder Terme noch Text. Je nachdem, wie die
Umschaltung gebaut ist, sehen Nutzer stundenlang eine Suche, die viel weniger
findet als gestern, mit Treffern ohne Textausschnitt. Die naheliegende
Reaktion des Admins ist ein Downgrade oder eine Deinstallation, und beides ist
teurer als die Wartezeit.

**Why it happens:**

Ein Umbau ist im Kopf des Entwicklers ein Hintergrundvorgang. Für den Nutzer
ist es ein kaputtes Produkt, solange ihm niemand etwas anderes sagt.

**How to avoid:**

- **Alter Index beantwortet weiter, bis der neue fertig ist.** Das ist der
  Grund, warum Pitfall 2 ein zweites Verzeichnis und einen Schwenk am Ende
  verlangt und kein Überschreiben. Der alte Index ist lexikalisch vollständig
  und in den alten Sprachen korrekt; er ist nur nicht spanisch. Das ist
  unendlich viel besser als leer.
- Wenn der Platz für zwei Verzeichnisse nicht reicht: **nicht** heimlich auf
  Überschreiben umschalten, sondern den Umbau verweigern, das Banner setzen und
  dem Admin sagen, wie viel Platz fehlt.
- Die semantische Hälfte läuft weiter. Die Vektoren sind sprachneutral
  (multilingual-e5-small) und werden vom Umbau nicht angefasst. Das gehört in
  die Banner-Formulierung: "Die Suche nach Bedeutung antwortet unverändert."
- Das Banner trägt Fortschritt (x von y Dokumenten) und eine Schätzung, nicht
  nur "Reindex läuft". Die Betriebsregel "Fortschritt in der DB,
  failed/skipped sichtbar" gilt hier genauso.

**Warning signs:**

Der Umbauplan enthält das Wort "wipe", "clear" oder `rmtree` auf dem aktiven
Indexverzeichnis.

**Phase to address:**

Phase Schema und Migration (Mechanik), Phase Kataloge (Wortlaut in allen
Sprachen), Phase Härtung (Abnahme).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|---|---|---|---|
| Alle sechs Sprachfelder immer füllen, statt eine Auswahl zu fahren | Keine Sprachauswahl, keine Erkennung, keine Marke, kein Umschalt-Rebuild | Index wächst für jede Installation, auch die rein deutsche. Gemessen synthetisch: 2 auf 6 Body-Felder sind 22,25 auf 42,26 MB, also plus 90 Prozent; aus den echten Projektfaktoren (0,374 mit Store, 0,076 ohne) gerechnet eher plus 40 Prozent. Beide Zahlen sind Schätzungen für den echten Korpus | Nie als Dauerlösung. Als Zwischenstand in der Bauphase in Ordnung, wenn die Auswahl vor dem Release kommt |
| Sprache automatisch erkennen und nur ein Feld füllen | Kleinster Index, kein Adminentscheid | Modell oder Bibliothek im Container (RAM, Lizenz, Abbildgröße), plus die gesamte Fehlerklasse aus dem nächsten Abschnitt. Ein falsch erkanntes Dokument ist dauerhaft unauffindbar und meldet sich bei niemandem | Nur wenn der Index sonst nachweislich nicht auf die Box passt. Für v1.3 ablehnen |
| Die vier Kataloge maschinell erzeugen und ungeprüft ausliefern | Vier Sprachen in einem Tag | Platzhalter- und Pluralfehler, die erst beim Nutzer auffallen, plus Store-Bewertungen in Sprachen, die niemand im Team liest | Vertretbar, wenn maschinell **plus** die maschinellen Gates aus dem Katalogabschnitt greifen und der Community-Review als benannter Vorbehalt in der Abnahme steht |
| Die gescheiterte Upgrade-Strecke entschärfen statt umdrehen | CI wieder grün | Der Milestone mit dem gefährlichsten Upgrade-Pfad ist der einzige ohne Upgrade-Beweis | Nie |
| `SCHEMA_VERSION` erhöhen und den Rebuild "später" bauen | Schema ist fertig | Pitfall 1 in voller Härte auf jeder Bestandsinstallation | Nie. Schema und Umbauweg sind ein Plan, nicht zwei |
| Katalog nur als `pt.json` statt `pt_BR` und `pt_PT` | Eine Datei statt zwei | `pt` gibt es in Nextcloud nicht (siehe unten). Die Datei wird nie geladen, die Arbeit ist unsichtbar | Nie |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|---|---|---|
| Nextcloud-Sprachcodes | `pt.json` schreiben. Gelesen aus `nextcloud/server` master, `core/l10n/`: es, it, nl existieren, **`pt` existiert nicht**, nur `pt_BR` und `pt_PT` | Für Portugiesisch zwei Kataloge in beiden Formaten, also vier Dateien. Wortlaute unterscheiden sich real (ficheiro/arquivo, utilizador/usuário, ecrã/tela), das ist kein Kopieren |
| Nextcloud-Sprachvarianten | Annehmen, `es_MX` falle auf `es` zurück. Der eigene Projektbefund für `de`/`de_DE` ("Abweichung B der Phase-9-Abnahme: de alleine lässt de_DE auf Englisch") sagt, dass es diesen Rückfall nicht gibt | Entweder `es_EC` und `es_MX` mitliefern (beide existieren in `core/l10n/`) oder ausdrücklich entscheiden, dass diese Nutzer Englisch lesen, und den Entscheid aufschreiben |
| Pluralregeln | Die französische Regel `nplurals=2; plural=(n > 1);` als Vorlage nehmen. Gelesen aus `nextcloud/server` master: **es, it, pt_BR und pt_PT führen alle `nplurals=3`**, nur `nl` führt `nplurals=2; plural=(n != 1);`. Nebenbefund zum Nachsehen: das heutige `core/l10n/fr.json` führt ebenfalls `nplurals=3`, während Findlings `php/l10n/fr.json` und der harte Test `FRENCH_PLURAL_FORM` auf zwei Formen stehen | Die Regel je Sprache aus `core/l10n/<lang>.json` der Ziel-Nextcloud lesen und wörtlich übernehmen, in `pluralForm` der JSON **und** als vierten Parameter von `OC.L10N.register` in der JS. Drei Formen heißen drei Einträge im Wertearray der fünf Pluralschlüssel, nicht zwei |
| AppAPI/Lockstep | Die PHP-Migration für 1.3.0 vergessen. `Version001300Date2026....php` mit **zeichengleichem** Klassen- und Dateinamen, sonst wird sie stumm nie ausgeführt | Die Migration wird wie `Version001200Date20260921000000` gebaut: den aufgezeichneten Backend-Stand löschen, nicht raten, gegen doppelten Lauf gesichert, ohne einen einzigen Aufruf an den Container |
| OCR-Sprachcodes gegen Index-Sprachcodes | Zwei Vokabulare für dieselbe Sache: `FINDLING_OCR_LANGUAGES=spa` (ISO-639-2) und `FINDLING_LANGUAGES=es` (ISO-639-1). Ein Admin setzt `FINDLING_LANGUAGES=spa`, `_languages()` erkennt nichts, loggt eine Warnung und fällt still auf die Vorgabe zurück. Der Index bleibt deutsch-englisch, die OCR spanisch, und die Suche findet die Scans nicht | Beide Werte gegen ihre Positivliste prüfen, den jeweils anderen Code in der Warnung nennen ("spa ist ein OCR-Code, für den Index heißt diese Sprache es"), und auf der Adminseite beide Listen nebeneinander zeigen, mit einer sichtbaren Meldung, wenn eine OCR-Sprache ohne zugehöriges Indexfeld läuft |
| tantivy-Version | `tantivy_version` ist eine der Marken. Ein Dependabot-Sprung auf 0.27 löst auf jeder Installation denselben Umbau aus wie v1.3 | Im selben Release nicht beides. Die tantivy-Version hält still, solange v1.3 unterwegs ist (gleiche Disziplin wie bei der Messanfahrt: Werkzeugstand ist Vergleichbarkeitsbedingung) |
| Store | Die eine Messzahl steht an drei Stellen, beide Hälften tragen dieselbe Minor-Version, `min-version`/`max-version` unverändert | Bestehende Release-Checkliste; zusätzlich die vier neuen Sprachen in der Store-Beschreibung, als Faktenliste, Owner-Abnahme vor der Einreichung |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|---|---|---|---|
| Man optimiert die Abfragezeit, obwohl sie das Problem nicht ist | Diskussionen über Feldzahl und Latenz | Gemessen (synthetisch, 1500 Dokumente, gleicher Text in jedes Feld): 2 Body-Felder 0,07 ms je Abfrage, 6 Body-Felder 0,15 ms. Ein Faktor 2 auf einem Wert, der drei Größenordnungen unter der 1,5-s-Decke liegt. Die Abfrage ist nicht der Engpass | Erst bei Feldzahlen weit jenseits von sechs, oder bei Wildcard- und Präfix-Abfragen über viele Felder |
| Indexgröße wächst unbemerkt | Volume läuft voll, `paused_low_disk`, dann Beschwerden | Gemessen synthetisch 22,25 auf 42,26 MB (plus 90 Prozent) beim Gang von 2 auf 6 Body-Felder; aus den echten Projektfaktoren eher plus 40 Prozent. Beides sind Schätzungen. **Die echte Zahl gehört in die Messanfahrt BL-F03**, gemessen am Korpus-Snapshot, weil dort 52.137 echte Dokumente liegen | Auf einer Box mit knappem Volume sofort. `MIN_FREE_BYTES` deckt es nicht ab |
| Schreibzeit je Dokument steigt linear mit der Feldzahl | Der Umbaulauf dauert länger als geschätzt | Gemessen synthetisch: 2,9 s auf 10,5 s für denselben Textbestand beim Gang von 2 auf 6 Feldern, also rund Faktor 3,6 für die reine Analyse ohne Extraktion und ohne OCR. Im Volllauf fällt das kaum auf, weil OCR dominiert; im Re-Analyse-Umbau aus Pitfall 2 ist es der **einzige** Posten und bestimmt die ganze Laufzeit | Bei jedem Umbau. Deshalb muss die Schätzung im Banner aus dieser Zahl kommen, nicht aus der Volllaufzeit |
| Writer-Heap und Merge-Spitze | Der Container stirbt im Umbau an der cgroup-Grenze (gemessen: `memory.max` 2147483648, `memory.swap.max` 0 auf der Messbox) | `WRITER_HEAP_BYTES` bleibt bei 50 MB, `num_threads=1` bleibt. Mehr Felder heißen mehr Postings je Commit und größere Merges. Der Umbau läuft mit denselben Deckeln wie der Indexlauf, nicht mit größeren, "weil er ja nur umschreibt" | Sobald jemand den Heap für den Umbau hochdreht |
| Zwei Indexverzeichnisse nebeneinander | Umbau bleibt bei `paused_low_disk` stehen und der Nutzer sieht ein halbfertiges Ergebnis | Platzprüfung **vor** dem Start, gegen die erwartete Größe des neuen Verzeichnisses plus `MIN_FREE_BYTES`, mit klarer Absage statt Abbruch mittendrin | Auf jeder Box, deren Volume knapp bemessen ist, also der Zielgruppe |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---|---|---|
| Sprachnamen aus der Umgebung direkt an `Filter.stopword()` geben | Rust-Panic (gemessen für greek, arabic, turkish, tamil, romanian), also ein von außen auslösbarer Absturzpfad in einer Erweiterungsbibliothek | Geschlossene Positivliste, wie `OCR_LANGUAGE_ALLOWLIST` sie für tesseract bereits ist |
| Der Umbau liest Dokumente und loggt dabei | Der gespeicherte Text ist Nutzerinhalt. Eine Fortschrittszeile mit Dateiname oder Textprobe ist ein Leck, das ein Admin in einem Supportfall weitergibt | Dieselbe Regel wie im Messmodus von `analyzer.py`: Zahlen, nie ein Token und nie ein Wort. Fehler mit `file_id`, nicht mit Pfad oder Inhalt |
| Die Rechtegrenze beim Umbau anfassen | Der Umbau schreibt `storage_id` neu; ein Fehler darin verschiebt die Vorfilterung | Der finale PHP-Recheck bleibt die einzige Sicherheitsgrenze und wird nicht angefasst. Der Paritätstest aus v1.2 läuft gegen den umgebauten Index unverändert, mit den vier neuen Feldern in der Abfrage |
| Übersetzte Zeichenketten unmaskiert in Templates | Vier neue Kataloge aus maschineller Quelle, in `php/templates/search.php` | Die Kataloge durchlaufen dieselbe Ausgabe-Maskierung wie heute. Zusätzlich ein Gate, das in keinem Katalogwert `<`, `>` oder `&#` zulässt, außer dort, wo der englische Quellstring sie auch führt |
| Nur-Lesen-Invariante | Ein Umbauweg, der "der Einfachheit halber" über Nextcloud-Dateien geht | Der Re-Analyse-Weg fasst keine Nutzerdatei an, und das ist zusätzlich ein Sicherheitsargument, nicht nur ein Geschwindigkeitsargument |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---|---|---|
| Der Umbau läuft ohne Ankündigung | Die Suche ist stundenlang schlechter, der Nutzer hält das Update für kaputt | Banner mit Fortschritt und Schätzung, in allen ausgelieferten Sprachen, plus der Satz, dass die Bedeutungssuche unverändert antwortet |
| Neue Sprachen ab Werk an | Jede bestehende deutsche Installation bezahlt Index und Umbauzeit für Sprachen, die dort niemand spricht | Dem OCR-Entscheid vom 21.09. folgen: angeboten, nicht Vorgabe. `DEFAULT_LANGUAGES` bleibt `("de","en")`, die vier neuen sind wählbar. Das ist zugleich der billigste Weg an Pitfall 7 vorbei |
| Der Admin kann die Sprachen nur über eine Umgebungsvariable setzen, die ein Neustart des Containers erfordert | Die meistgewünschte neue Funktion des Milestones ist die am schlechtesten erreichbare | `<environment-variables>` in der `info.xml` ist der etablierte Weg und bleibt es. Aber die Adminseite muss den aktuellen Stand **zeigen** und sagen, was ein Wechsel kostet (Umbau, geschätzte Dauer), bevor jemand ihn auslöst |
| Halb übersetzte Oberfläche | Schlimmer als Englisch: der Nutzer hält die Anwendung für unfertig. Genau dieser Befund steht im Projekt schon fest ("24 of 174 strings produce a half French surface") | Ein Katalog geht vollständig oder gar nicht. Das Gate zählt Schlüssel, nicht Zeilen |
| Der Leerzustand erklärt nicht, dass eine Sprache nicht aktiv ist | Ein spanischer Nutzer sucht auf Spanisch, bekommt nichts und glaubt, das Produkt kann kein Spanisch | Wenn die Suchzeile Zeichen einer nicht aktiven Sprache trägt, ist das nicht erkennbar, also nicht versprechen. Aber die Adminseite nennt die aktiven Sprachen im Klartext, und die Store-Beschreibung nennt, dass Sprachen eingeschaltet werden müssen |

---

## Falsche Spracherkennung: warum sie in v1.3 gar nicht erst eingebaut werden sollte

Die Frage "welche Sprache hat dieses Dokument" ist in diesem Produkt schlechter
gestellt als anderswo, und zwar aus vier Gründen, die alle im Bestand
nachweisbar sind:

- **Kurze Texte.** Ein großer Teil der Treffer kommt über `name` und `title`.
  Ein Dateiname hat drei bis fünf Wörter. Jede Erkennung ist dort Münzwurf.
- **OCR-Rauschen.** Der Korpus enthält gescannte Dokumente. Der OCR-Standard
  ist `deu+eng+fra`; ein spanischer Scan, der mit diesen drei Modellen gelesen
  wurde, ergibt Text, der für eine Erkennung weder spanisch noch deutsch
  aussieht. Die Erkennung würde also ausgerechnet dort versagen, wo sie
  gebraucht wird.
- **Gemischte Dokumente.** Zweisprachige Verträge, Rechnungen mit englischen
  Positionsbezeichnungen, Protokolle mit Zitaten. Eine Entscheidung je Dokument
  wirft die zweite Sprache weg.
- **Stille Folgen.** Ein falsch erkanntes Dokument wird unter der falschen
  Kette indexiert und ist unter der richtigen Sprache nie auffindbar. Es gibt
  kein Ereignis, keine Zahl und keinen Log, an dem das sichtbar würde. Das ist
  dieselbe Klasse von Fehler wie die NFC/NFD-Sache aus `analyzer.py`: "der
  Nutzer sieht eine leere Liste ohne Grund, und das ist die eine Art Defekt,
  die niemand meldet".

Dazu käme eine Bibliothek oder ein Modell in einen Container, dessen ganzes
Versprechen ein kleines RAM-Budget ist.

**Empfehlung, opinioniert:** in v1.3 keine Spracherkennung. Der Text geht in
jedes aktive Sprachfeld, wie er heute in `body_de` und `body_en` geht. Der
Admin wählt die Sprachen seiner Instanz. Das kostet Indexgröße, die
messbar und deckelbar ist, statt Trefferqualität, die es nicht ist. Wenn die
Indexgröße auf dem echten Korpus als untragbar herauskommt, ist die richtige
Antwort immer noch nicht Erkennung, sondern eine engere Vorgabe: `body_de`
bleibt immer gefüllt (es ist die einzige gespeicherte Kopie), und die
übrigen Felder folgen der Auswahl.

---

## Sprachspezifische Stemmer-Fallen im Einzelnen

Alle Beispiele in tantivy 0.26.0 nachgefahren, Kette
`lowercase -> stopword -> remove_long(48) -> stemmer` (Faltung wie in Pitfall 4
besprochen).

**Niederländisch: die Kompositaannahme im Backlog ist falsch.** BL-F02 sagt
"Komposita-Zerlegung entfällt, ist Deutsch-Spezifikum". Niederländisch ist
eine Kompositasprache wie Deutsch. Gemessen:
`ziektekostenverzekering -> ['ziektekostenverzeker']`,
`arbeidsongeschiktheidsverzekering -> ['arbeidsongeschiktheidsverzeker']`,
`gemeentehuis -> ['gemeentehuis']`. Wer `verzekering` sucht, findet keines der
drei Dokumente. Das ist kein Fehler der Kette, sondern eine Lücke im Versprechen.
Entscheidung nötig, und sie gehört in den Milestone, nicht dahinter: entweder
(a) ausdrücklich dokumentieren, dass Niederländisch ohne Kompositazerlegung
ausgeliefert wird, oder (b) `Filter.split_compound` mit einer
niederländischen Wortliste versorgen. Für (b) gilt alles, was für die
deutsche Liste gilt: Lizenzkonformität, rund 23 MB Automat je Liste, und der
Automat ist ein Prozess-Singleton je Wortliste. Zwei Listen heißen zwei
Automaten und damit rund 46 MB dauerhaft. Auf einer 4-GB-Box ist das eine
Entscheidung mit Preis, keine Selbstverständlichkeit. Empfehlung: (a) für
v1.3, (b) als Backlog-Eintrag mit der Speicherzahl daneben.
Nebenbefund, unkritisch: `IJsselmeer` und `ijsselmeer` landen beide auf
`ijsselmer`, der IJ-Digraph macht keine Probleme. `'s-Hertogenbosch` zerfällt
in `s`, `hertogenbosch`; das einbuchstabige `s` ist derselbe Müllterm, gegen den
die deutsche Kette `custom_stopword(FUGEN)` fährt.

**Portugiesisch: zwei Orthographien, ein Stemmer.** Gemessen bleiben
`facto`/`fato` auf `fact`/`fat`, `acção`/`ação` auf `acçã`/`açã` und
`óptimo`/`ótimo` auf `óptim`/`ótim` getrennt. Das ist der Unterschied zwischen
europäischem und brasilianischem Portugiesisch vor und nach dem Acordo
Ortográfico, und kein Snowball-Algorithmus vereinigt ihn. Konsequenz für die
Erwartungshaltung: ein pt-PT-Dokument wird von einer pt-BR-Suchanfrage in diesen
Fällen nicht gefunden. Das ist hinnehmbar und gehört dokumentiert; es als Bug
gemeldet zu bekommen und dann erst nachzudenken, ist teurer. Die Faltung nach
dem Stemmer hilft hier nur teilweise (`acca` gegen `aca` bleiben verschieden).

**Spanisch: `año` gegen `ano`.** Ohne Faltung sind es zwei Terme, mit Faltung
nach dem Stemmer einer. Das ist der Preis der Akzentunempfindlichkeit, und er
ist richtig bezahlt: Nutzer tippen `ano`, wenn sie `año` meinen, viel öfter
als umgekehrt. Aufschreiben, nicht wegdiskutieren.

**Italienisch: Elision funktioniert, aber aus Versehen.** `l'anno`,
`dell'uomo`, `nell'azienda`, `un'idea` werden gemessen korrekt zu
`anno`, `uom`, `azi`, `ide`. Das liegt daran, dass `Tokenizer.simple()` am
Apostroph trennt und die italienische Stoppwortliste `l`, `dell`, `nell` und
`un` schluckt. Es gibt keinen Elisionsfilter in tantivy. Die Kette funktioniert
also, aber sie funktioniert über zwei unabhängige Bausteine; ein Test gehört
darauf, sonst fällt eine spätere Änderung an der Stoppwortliste
unbemerkt auf die Füße.

**Alle vier: `remove_long` und die Position.** Die deutsche Kette hat
`remove_long` hinter dem Kompositasplitter, aus einem gemessenen Grund. In den
vier neuen Ketten gibt es keinen Splitter, also steht `remove_long` vor dem
Stemmer, wie in der englischen Kette. Das ist richtig; es ist nur eine der
Stellen, an denen ein Copy-Paste aus der deutschen Kette schaden würde.

---

## Katalog-Übersetzungsfallen

**Die Schlüsselzahl im Milestone-Text ist veraltet.** BL-F02 und die
Milestone-Beschreibung sagen "je 174 Schlüssel". Aus `php/l10n/de.json`
gezählt sind es heute **199**. Die Zahl ist zwischen 10.09. und 19.09. viermal
gestiegen (174, 197, 198, 199), jedes Mal mit einem Absatz Begründung im
Test. Die Aufwandsschätzung für vier Sprachen liegt also um 25 Schlüssel je
Sprache daneben, plus alle Schlüssel, die v1.3 selbst hinzufügt (Banner,
Fortschritt, Sprachliste auf der Adminseite). Realistisch sind es 205 bis 215
je Sprache.

**Die Gates sind auf Französisch verdrahtet.** `FRENCH_PLURAL_FORM` ist eine
Konstante, `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` ist eine feste Menge, die
Dateipfade stehen einzeln in `L10N_CATALOGUES`. Wer die vier neuen Sprachen
dagegen prüft, indem er den französischen Testblock viermal kopiert,
bekommt vier grüne Gates mit der französischen Pluralregel. Richtig ist eine
Tabelle: Sprachcode auf Pluralregel auf Ausnahmemenge, und ein
parametrisierter Test darüber. Und die Pluralregel kommt aus
`nextcloud/server`, nicht aus dem Gedächtnis: gelesen aus master führen
**es, it, pt_BR und pt_PT je `nplurals=3`**, `nl` führt `nplurals=2`.
Drei Formen heißen drei Werte im Array jedes der fünf Pluralschlüssel. Ein
Katalog mit zwei Werten, wo drei erwartet werden, greift bei der dritten Form
ins Leere.

**Platzhalter.** 37 Schlüssel tragen printf-Direktiven, 5 davon `%n` in
Pluralformen. Maschinelle Übersetzung dreht `%1$s in %2$s` gern in
`%2$s ... %1$s` (in romanischen Sprachen oft sogar korrekterweise, dann muss
die Nummerierung mitwandern und darf nicht zu `%s ... %s` werden), übersetzt
`%s` gelegentlich mit, und macht aus `%n` ein `% n`. Gate: je Schlüssel die
Multimenge der Direktiven im Quellstring gegen die im Zielstring vergleichen,
Nummerierung eingeschlossen. Das Gate gibt es für Französisch schon; es muss
nur allgemein werden.

**Typografie je Sprache.** Die französischen Regeln (Guillemets, ASCII-
Apostroph, einfaches Leerzeichen vor `:`) sind französisch und gelten für die
vier neuen nicht. Was für alle gilt und was maschinelle Übersetzung
zuverlässig verletzt: **keine Em-Dashes** (U+2014, U+2013) und **kein
typographischer Apostroph** U+2019. Spanisch braucht zusätzlich `¿` und `¡` am
Satzanfang, Italienisch und Portugiesisch echte Akzente. Alle vier Punkte sind
maschinell prüfbar und gehören als Gate in denselben Test.

**Werte, die gleich ihrem Schlüssel sein dürfen.** Die französische Fassung
hat dafür eine benannte Ausnahmemenge (`Findling` und vier weitere). Für jede
neue Sprache ist diese Menge anders und muss einzeln entschieden werden, sonst
fällt entweder ein echter Übersetzungsausfall durch oder ein korrekt gleicher
Wert löst einen Fehlalarm aus.

**Community-Review statt Muttersprachler-Gate.** Der Entscheid ist getroffen und
vernünftig. Damit er nicht zur Ausrede wird: die maschinelle Fassung geht mit
einem datierten Vorbehalt ins Release ("die Wortlaute dieser vier Sprachen sind
maschinell erzeugt und noch nicht von Muttersprachlern geprüft"), genau in der
Form, in der der französische Vorbehalt heute schon im Repositorium steht. Die
Reddit-Nutzer, die die Sprachen gewünscht haben, und die Kontakte aus dem
EU-Outreach sind die naheliegende Reviewrunde, und der Backlog-Eintrag nennt
schon einen Freiwilligen.

---

## "Looks Done But Isn't" Checklist

- [ ] **Neue Sprachfelder:** oft fehlt der Eintrag in `FIELD_BOOSTS`. Heute
      stehen dort `name` 3.0, `title` 2.0, `body_de` 1.0, `body_en` 0.8. Ein
      Feld ohne Eintrag bekommt 1.0, also würde Spanisch höher gewichtet als
      Englisch, ohne dass es jemand entschieden hat. Prüfen: jedes Feld aus
      `DEFAULT_FIELDS` hat einen Boost, und ein Test hält das fest
- [ ] **Neue Sprachfelder:** oft fehlt die Aufnahme in `DEFAULT_FIELDS`. Dann
      ist das Feld gefüllt und wird nie durchsucht. Prüfen: eine Suche nach
      einem Wort, das nur in der spanischen Stammform existiert
- [ ] **Schema-Änderung:** oft fehlt der Test gegen ein **vorhandenes**
      Indexverzeichnis mit altem Schema. Prüfen: Testaufbau legt den alten
      Index wirklich an, statt ein leeres Verzeichnis zu benutzen
- [ ] **Migration:** oft fehlt der Test, dass Klassenname und Dateiname
      zeichengleich sind, und der Test auf den zweiten Lauf. Beide gibt es für
      1.1.0 und 1.2.0 schon als Muster (`php/tests/Unit/Version001200...Test.php`)
- [ ] **Versionsmarken:** oft fehlt `languages`. Prüfen: Sprache umschalten,
      Container neu starten, Banner muss kommen
- [ ] **Umbau:** oft fehlt die Wiederaufnahme nach Neustart. Prüfen: Container
      mitten im Umbau töten, neu starten, genau eine `built by different code`-Zeile
      insgesamt, Fortschritt geht weiter statt von vorn
- [ ] **Umbau:** oft fehlt die Platzprüfung für zwei Verzeichnisse
- [ ] **Kataloge:** oft fehlen `pt_BR` und `pt_PT` als zwei Dateien; oft fehlt
      die `.js`-Fassung neben der `.json`; oft fehlt die Pluralregel im vierten
      Parameter von `OC.L10N.register`
- [ ] **Kataloge:** oft sind die neuen v1.3-Schlüssel (Banner, Fortschritt) nur
      auf Deutsch und Englisch da. Prüfen: die harte Schlüsselzahl steht in
      allen Katalogen gleich, mit dem Begründungsabsatz im Test
- [ ] **Store:** oft fehlt die Nennung der neuen Sprachen in beiden `info.xml`
      und in den drei Stellen der einen Messzahl
- [ ] **Messung:** oft fehlt die Indexgröße **mit** vier zusätzlichen Feldern
      am echten Korpus. Die synthetischen Zahlen oben sind keine Abnahme

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---|---|---|
| 1, Schema erreicht den Bestand nicht und die Suche wirft | HIGH, wenn es im Store steht | Patchrelease, das den fehlenden Zweig in `open_index` nachliefert. Betroffene Installationen brauchen danach den vollen Umbau. Kein Downgrade möglich, weil die PHP-Migration schon gelaufen ist. **Deshalb ist dieser Punkt die erste Phase und nicht die letzte** |
| 2, Umbau als Neuextraktion ausgeliefert | MEDIUM | Nicht rücknehmbar bei denen, die schon umgebaut haben. Für die anderen ein Patchrelease mit dem Re-Analyse-Weg. Kosten sind Ruf, nicht Daten |
| 4, Faltung an falscher Stelle | MEDIUM | `ANALYZER_VERSION` erhöhen, die bestehende Drift-Mechanik löst den Umbau aus. Mit dem Re-Analyse-Weg aus Pitfall 2 ist das billig: genau dafür ist der Weg da. Ohne ihn ist es ein zweiter 19-Stunden-Lauf |
| 5, Panic durch Sprachnamen | LOW | Positivliste nachliefern. Der Container startet nach dem Zurücksetzen der Variablen wieder |
| 6, Sprachmenge nicht in den Marken | LOW, wenn früh gefunden | Marke nachliefern; beim ersten Start nach dem Patch greift die Drift und der Umbau läuft. Spät gefunden heißt: Installationen mit stillem Teilbestand, die niemand zählen kann |
| Katalog mit falscher Pluralzahl | LOW | Katalogkorrektur, kein Index betroffen, kein Umbau. Geht in jedes Patchrelease |
| pt statt pt_BR/pt_PT | LOW | Dateien umbenennen und aufteilen. Ärger ist nur, dass die Arbeit bis dahin unsichtbar war |

---

## Pitfall-to-Phase Mapping

Die Reihenfolge ist keine Empfehlung, sondern eine Abhängigkeit: Phase B kann
ohne A nicht abgenommen werden (die Marken hängen an den Ketten), und A darf
ohne B nicht ausgeliefert werden (ein erhöhtes `ANALYZER_VERSION` ohne
Umbauweg ist Pitfall 1 in klein).

| Pitfall | Prevention Phase | Verification |
|---|---|---|
| 4, Faltung und Kettenreihenfolge; 5, Panic durch Sprachnamen; nl-Komposita-Entscheid; it-Elision | **A, Analyseketten und Sprachtabelle** | Die Messtabelle aus Pitfall 4 als Tabellentest, je Sprache mindestens fünf Wortpaare. Ein Test, der jede Sprache der Tabelle durch den `TextAnalyzerBuilder` anhängt. Owner-Entscheid zu Niederländisch schriftlich |
| 1, Schema erreicht den Bestand nicht; 2, Umbau als Neuextraktion; 6, Sprachmenge nicht in den Marken; 7, Ausfallfenster | **B, Schema, Marken und Umbauweg** | Test gegen ein wirklich vorhandenes v1.2-Indexverzeichnis. Umbau ohne einen einzigen Nextcloud-Aufruf, nachgewiesen über Zähler und Log. Sprachwechsel löst Drift aus. Container-Tötung mitten im Umbau führt zu genau einer Driftzeile |
| 3, Upgrade-Beweisstrecke | **B, im selben Plan wie der Umbauweg** | Neuer Schritt in `deploy-harp.yml` mit den sieben Behauptungen aus Pitfall 3. `UPGRADE_FROM_TAG` auf `v1.2.0`. Der alte Schritt bleibt stehen und wird nicht entschärft |
| Alle Katalogfallen; UX-Wortlaute des Banners | **C, UI-Kataloge es/it/nl/pt_BR/pt_PT** | Parametrisierte Gates statt vier Kopien des französischen Blocks. Pluralregeln aus `core/l10n/<lang>.json` der Ziel-Nextcloud. Schlüsselzahl gleich in allen Katalogen, mit Begründungsabsatz. Vorbehalt zur maschinellen Herkunft datiert im Repositorium |
| Indexgröße, Schreibzeit, Umbaudauer am echten Bestand | **D, Messanfahrt BL-F03** | Zwei zusätzliche Messaufträge im Rechenblatt **vor** der Owner-Freigabe: Indexgröße mit sechs Sprachfeldern am Korpus-Snapshot, und Wandzeit des Re-Analyse-Umbaus über 52.137 Dokumente. Beide Zahlen gehen in `docs/performance.md` und in die Schätzung des Banners |
| Store- und Lockstep-Fallen | **E, Härtung und Store-Einreichung 1.3.0** | `Version001300Date...` mit Namensgleichheitstest und Zweitlauf-Test. Fremdinstallation und Upgrade-Strecke grün. Store-Text als Faktenliste mit Owner-Abnahme |

**Zwei Phasen, die dieses Dokument nicht braucht, und warum das gesagt gehört:**
eine eigene Phase für Spracherkennung (bewusst nicht gebaut, Begründung oben)
und eine eigene Phase für Abfrageoptimierung (gemessen kein Problem, 0,07 auf
0,15 ms). Beide würden sich in der Planung natürlich anfühlen und wären
Aufwand am falschen Ort.

---

## Sources

- **Gemessen in `backend/.venv`, tantivy 0.26.0 (`tantivy v0.26.0, index_format v7`), 23.09.2026:**
  Schema-Mismatch beim Öffnen, stilles Verwerfen unbekannter Felder in
  `Document.from_dict`, `ValueError` bei `parse_query_lenient` auf ein
  unbekanntes Feld, Sprachmatrix für `Filter.stemmer`/`Filter.stopword`
  einschließlich der fünf Panic-Fälle, Kettenreihenfolge und Faltung für
  es/it/nl/pt, Index- und Zeitvergleich 2 gegen 6 Body-Felder (synthetischer
  Korpus, 1500 Dokumente, als obere Schranke gekennzeichnet). HIGH
- `backend/src/findling/index/schema.py`, `analyzer.py`, `open.py`, `writer.py`,
  `query/rewrite.py`, `config.py`: Feldliste und Speicherflags, Ketten und
  `ANALYZER_VERSION`, `expected_versions`/`start_rebuild_on_drift`/`REBUILD_MARK`,
  `stored_body`, `DEFAULT_FIELDS`/`FIELD_BOOSTS`, `_languages`/`_ocr_languages`/
  `OCR_LANGUAGE_ALLOWLIST`, `MIN_FREE_BYTES`, `WRITER_HEAP_BYTES`. HIGH
- `.github/workflows/deploy-harp.yml`, Schritte "Store upgrade 0 bis 5" und
  `UPGRADE_FROM_TAG`: der Wortlaut der sechs Zusagen. HIGH
- `php/lib/Migration/Version001200Date20260921000000.php`: Lockstep-Begründung,
  die Regel "jeder Minor-Sprung braucht eine Migration", der offene Punkt
  DI-11-06. HIGH
- `backend/tests/test_admin_ui_contract.py`: Schlüsselzahlhistorie 173/174/197/198/199,
  `FRENCH_PLURAL_FORM`, `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY`, der de/de_DE-Befund. HIGH
- `docs/l10n-french.md`: Platzhalterzählung (37 mit Direktiven, 5 Pluralschlüssel),
  Typografieregeln, Abnahmeform. HIGH
- `docs/measurements/2026-09-v12-messung/README.md` und `docs/performance.md`:
  Volllauf 19 h 20 min über 52.137 Dokumente auf m7g.large, Indexfaktoren
  0,374 mit Store und 0,076 ohne, cgroup-Grenze 2147483648 bei `swap.max` 0. HIGH
- `nextcloud/server` master, `core/l10n/` (API-Verzeichnisliste und die
  `pluralForm`-Zeilen von es, it, nl, pt_BR, pt_PT, fr, de), gelesen 23.09.2026:
  kein `pt`, `es_EC` und `es_MX` vorhanden, drei Pluralformen für es/it/pt_BR/pt_PT. MEDIUM
  (aus dem Quellbaum gelesen, nicht gegen eine laufende Instanz der Zielversion geprüft)
- `.planning/BACKLOG.md` BL-F02 und BL-F03, `.planning/PROJECT.md`: Milestone-Zuschnitt,
  der Merksatz zur Migration, der OCR-Entscheid "angeboten, nicht Vorgabe". HIGH
- Solr Reference Guide, "Language Analysis", und die Lucene-`SnowballFilter`-Dokumentation:
  als **Gegenbeispiel** angeführt. Die dort übliche Lesart "Normalisierung vor
  Stemming" widerspricht der Messung für die romanischen Snowball-Algorithmen
  und ist der Grund, warum Pitfall 4 gemessen statt übernommen wurde. LOW als
  Empfehlung, HIGH als Beleg dafür, dass die falsche Reihenfolge naheliegt

---
*Pitfalls research for: lexikalischer Sprachausbau es/it/nl/pt auf Bestandsindexen (Findling v1.3)*
*Researched: 2026-09-23*
