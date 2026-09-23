# Stack Research

**Domain:** Lexikalischer Sprachausbau es/it/nl/pt in einer eingebetteten Tantivy-Suche (Findling v1.3)
**Researched:** 2026-09-23
**Confidence:** HIGH fuer die Tantivy-Seite (eigene Messungen gegen die installierte Bibliothek und gegen den Quellbaum), MEDIUM fuer die Uebersetzungswerkzeuge

## Die kurze Antwort

**Der Sprachausbau braucht kein einziges neues PyPI-Paket und kein neues Systempaket.**

Tantivy bringt Snowball-Stemmer **und** Snowball-Stoppwortlisten fuer alle vier
Sprachen schon mit; das ist an der installierten `tantivy==0.26.0` im Backend-venv
nachgewiesen, nicht aus der Doku abgeschrieben. Es gibt genau drei Dinge zu
entscheiden, und alle drei sind Code in diesem Repo, keine Abhaengigkeit:

1. die Reihenfolge der Filter in der Kette je Sprache (gemessen, siehe unten),
2. eine kleine mitgelieferte Ergaenzungsliste gefalteter Stoppwoerter (77 + 10 + 30 + 0 Eintraege),
3. die Frage, welche Sprachfelder eine Installation ueberhaupt befuellt.

Sprach-Erkennung (lingua, fasttext, langdetect, py3langid) wird **nicht** empfohlen.
Begruendung unten mit Zahlen.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `tantivy` (PyPI) | **0.26.2** (Upgrade von 0.26.0) | Suchmaschine, Analysekette, Stemmer, Stoppwoerter | Bringt Snowball-Stemmer fuer spanish/italian/dutch/portuguese und die passenden Stoppwortlisten eingebaut. Aktuellste Fassung vom 17.09.2026. **Index-Format unveraendert v7**, eigenhaendig gegengeprueft: 0.26.0 meldet `index_format v7`, 0.26.2 ebenfalls. Der Sprung erzwingt also keinen zweiten Reindex neben dem Schema-Reindex. |
| Snowball-Stoppwortlisten | in tantivy einkompiliert | Stoppwortentfernung es/it/nl/pt | Quelle ist das Snowball-Projekt unter **BSD-3-Clause** (Porter/Boulton/Betts, Lizenztext steht im Kopf von `src/tokenizer/stop_word_filter/stopwords.rs`). AGPL-3.0-vertraeglich. Keine eigene Liste zu pflegen. |
| Snowball-Stemmer (rust-stemmers) | in tantivy einkompiliert | Stammformbildung es/it/nl/pt | Gleiche Herkunft, gleiche Lizenzlage. Kein Modell, kein Download, kein RAM. |
| Eigene Ergaenzungsliste gefalteter Stoppwoerter | neu, im Repo | schliesst die Luecke, die `ascii_fold` vor `stopword` reisst | 117 Woerter insgesamt fuer drei Sprachen, als Python-Konstante neben `FUGEN`. Maschinell aus `stopwords.rs` erzeugbar, mit Erzeugungsskript wie bei der Komposita-Wortliste. |

### Keine neuen Supporting Libraries

| Kandidat | Verdikt | Begruendung |
|----------|---------|-------------|
| Sprach-Erkennung (irgendeine) | **nein** | Wird durch die Schema-Entscheidung unten ueberfluessig. Details im Abschnitt "Sprach-Erkennung". |
| Stoppwortpakete (`stopwordsiso`, `stop-words`, `nltk`) | **nein** | Tantivy traegt die Listen bereits, und eine zweite Liste waere eine, die von der im Index benutzten abweicht. Genau die Drift, die `analyzer.py` mit einer einzigen `FUGEN`-Konstante vermeidet. |
| Lemmatisierung (`simplemma` 2.0.0) | **nein, nicht in v1.3** | 19 MB Wheel, und es loest ein Problem, das der Stemmer fuer diese vier Sprachen bereits ausreichend loest. Romanische Sprachen sind flektierend, aber nicht komponierend: das Deutsch-Sonderproblem (Komposita) hat hier kein Gegenstueck. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `scripts/dev/` Erzeugungsskript fuer die Faltungsliste | erzeugt die 117 Ergaenzungswoerter aus `stopwords.rs` | Gleiches Muster wie `measure_wordlist.sh`: die Liste wird erzeugt, committet und durch einen Test gegen ihren Hash gehalten. Nicht zur Laufzeit herunterladen. |
| Nextcloud `translationtool.phar` | erzeugt `.pot`/`.po` aus dem PHP/JS-Quelltext, kompiliert nach `l10n/*.json` und `l10n/*.js` | Offizieller Weg, funktioniert ohne Transifex. Siehe Abschnitt "UI-Kataloge". |
| Die vier bestehenden Katalog-Gates | Schluesselgleichstand, Vollstaendigkeit, Platzhalter-Paritaet, Pluralform | In `backend/tests/test_admin_ui_contract.py`. Sie tragen die vier neuen Sprachen ohne Umbau, nur die Dateitupel wachsen. |

## Der Befund, der die Analysekette entscheidet

Die bestehende deutsche Kette faltet **nicht**, die englische faltet **vor** dem
Stoppwortfilter. Fuer die vier neuen Sprachen ist beides falsch, und zwar messbar.
Die Snowball-Stoppwortlisten tragen Akzente:

| Liste | Woerter gesamt | davon akzentuiert | zusaetzliche gefaltete Formen |
|---|---:|---:|---:|
| SPANISH | 308 | 84 | **77** |
| ITALIAN | 279 | 11 | **10** |
| PORTUGUESE | 203 | 36 | **30** |
| DUTCH | 101 | 0 | **0** |
| (GERMAN, zum Vergleich) | 231 | 8 | 7 |

Gezaehlt am 23.09.2026 aus `quickwit-oss/tantivy`, Tag 0.26.2,
`src/tokenizer/stop_word_filter/stopwords.rs`.

Drei Reihenfolgen wurden gegen Akzentpaare gefahren (`relación`/`relacion`,
`informação`/`informacao`, `perché`/`perche`, `financiën`/`financien`, und weitere):

| Reihenfolge | Ergebnis |
|---|---|
| A: `lowercase, ascii_fold, stopword, remove_long, stemmer` | Akzentschreibung und ASCII-Schreibung liefern **immer denselben Term**. Aber akzentuierte Stoppwoerter (`están`, `más`, `também`, `não`) ueberleben und landen im Index. |
| B: `lowercase, stopword, ascii_fold, remove_long, stemmer` | Stoppwoerter fallen, aber `perché` wird entfernt und `perche` bleibt als Term stehen: dasselbe Wort, zwei Schicksale, je nachdem ob der Autor den Akzent getippt hat. |
| C: `lowercase, stopword, remove_long, stemmer, ascii_fold` | **Falsch.** Der portugiesische Stemmer verarbeitet `ã`/`õ` intern; gemessen: `informação` wird zu `inform`, `informacao` zu `informaca`. Die beiden Schreibweisen finden sich nicht mehr. |

**Empfohlen ist A plus ein `Filter.custom_stopword` mit der gefalteten Ergaenzungsliste**,
genau das Muster, mit dem die deutsche Kette schon die Fugenelemente behandelt:

```python
(
    TextAnalyzerBuilder(Tokenizer.simple())
    .filter(Filter.lowercase())
    .filter(Filter.ascii_fold())
    .filter(Filter.stopword("spanish"))
    .filter(Filter.custom_stopword(FOLDED_STOPWORDS["es"]))  # 77 Woerter
    .filter(Filter.remove_long(MAX_TOKEN_CHARS))
    .filter(Filter.stemmer("spanish"))
    .build()
)
```

Gemessen mit dieser Kette, akzentuierte gegen ASCII-Eingabe:

| Sprache | Ergaenzungsliste | akzentuierte Eingabe | ASCII-Eingabe | gleich |
|---|---:|---|---|---|
| spanish | 77 | `['aqui','inform','alla']` | `['aqui','inform','alla']` | ja |
| portuguese | 30 | `['aqu','relatori']` | `['aqu','relatori']` | ja |
| italian | 10 | `['cos']` | `['cos']` | ja |
| dutch | 0 | `['huis']` | `['huis']` | ja |

Zwei Nebenwirkungen, beide erwuenscht:

- **Die Umlautvarianten-Erweiterung der Suchzeile braucht kein Gegenstueck.**
  `query/rewrite.py::umlaut_variants` existiert, weil die deutsche Kette bewusst nicht
  faltet. Weil diese vier Ketten falten, konvergieren `relación` und `relacion` schon
  in der Tokenisierung, auf beiden Seiten. Keine Query-Expansion, keine zusaetzlichen
  Klauseln.
- **`ANALYZER_VERSION` muss steigen**, weil vier Ketten hinzukommen. Das ist die
  bestehende Regel aus dem Kopf von `analyzer.py` und kein neuer Mechanismus.

## Die zweite Entscheidung: leere Sprachfelder kosten nichts

Das ist die Kernmessung dieser Recherche, und sie entscheidet die Reindex-Frage
aus BL-F02. Korpus: 1.417 Dokumente zu je 600 Woertern, 4,77 MB Text aus sechs
echten Gutenberg-Texten (de/en/es/it/nl/pt), `heap_size=50_000_000`, `num_threads=1`,
also die Produktionswerte. Gemessen auf einem Windows-Laptopkern mit tantivy 0.26.2:

| Aufbau | Schemafelder | befuellt | Zeit | Index |
|---|---:|---:|---:|---:|
| heute | 2 | 2 | 0,81 s | **8,48 MB** |
| **v1.3-Vorschlag** | **6** | **2** | **0,80 s** | **8,48 MB** |
| eine Sprache dazu | 6 | 3 | 1,16 s | 10,57 MB |
| alle sechs | 6 | 6 | 3,73 s | 17,99 MB |

Ein deklariertes, aber nie befuelltes Sprachfeld kostet **null Byte und null
Millisekunden**. Byte-identisch zum heutigen Zweifeldindex.

Daraus folgt die Empfehlung:

- Das Schema bekommt **alle sechs** `body_*`-Felder auf einen Schlag (`SCHEMA_VERSION`
  von 1 auf 2, ein sichtbarer Reindex, genau einmal).
- Welche davon befuellt werden, entscheidet `FINDLING_LANGUAGES` zur Laufzeit.
  Werkseinstellung bleibt `("de","en")`, damit Bestandsinstallationen nach dem
  Umstieg **exakt denselben Index** haben wie vorher.
- Eine Installation, die spaeter Spanisch dazunimmt, braucht dann **keine
  Schemaaenderung mehr**, nur noch ein Nachziehen der Inhalte. Das ist der eigentliche
  Gewinn: die Sprachfrage wird nach v1.3 eine Betriebsfrage und keine Releasefrage.

Wer alle sechs befuellt, zahlt **2,12-fache Indexgroesse und 4,6-fache Schreibzeit**
gegenueber heute. Das ist genau der Grund, warum die Werkseinstellung bei zwei bleibt:
dieselbe Logik, mit der `OCR_DEFAULT_LANGUAGES` bei `deu+eng+fra` geblieben ist,
obwohl die Positivliste neun Eintraege hat.

Kosten je zusaetzlich befuellter Sprache, aus derselben Messung abgeleitet:
etwa **+2,1 MB Index je 4,77 MB Text**, also rund **+25 Prozent des heutigen Index**
pro Sprache, und **+0,4 s Schreibzeit je 4,77 MB Text** auf dem Messkern.

> **Vorbehalt, ehrlich benannt:** meine absolute Verhaeltniszahl (Index zu Text)
> liegt bei 1,78 und damit weit ueber den 0,374, die `schema.py` aus der Phase-02-
> Messung nennt. Ursache ist mit hoher Wahrscheinlichkeit der Korpus: Belletristik
> hat einen viel groesseren Wortschatz als Verwaltungsdokumente, und der Wortschatz
> treibt Termwoerterbuch und Positionslisten. **Die relativen Faktoren (2,12x, leeres
> Feld = 0) sind belastbar, die absoluten Megabyte nicht.** Die absolute Zahl gehoert
> auf den Korpus-Snapshot `snap-03f1d1d9ad9262704`, also in die Messphase BL-F03.

### Suchlatenz

Dieselbe Messung, zehn Suchbegriffe, fuenf Runden:

| Felder | Median | p95 |
|---|---:|---:|
| 2 | 0,01 ms | 0,03 ms |
| 6 | 0,04 ms | 0,12 ms |

Relativ vervierfacht, absolut irrelevant: die p95 der laufenden Installation liegt
laut `config.py` bei 0,196 ms im Leerlauf, und die 1,5-Sekunden-Decke wird vom
ACL-Vorfilter und dem PHP-Recheck bestimmt, nicht von der Feldzahl. **Die Feldzahl
ist ein Platz- und Schreibproblem, kein Latenzproblem.**

## Die Reindex-Frage: die Wanderung braucht die Dateien nicht

BL-F02 nennt die Reindex-Frage offen. Sie hat eine gute Antwort, und sie steht
bereits im Schema: **jedes Feld ist `stored=True`, bis auf `body_en`, und `body_en`
traegt denselben Text wie das gespeicherte `body_de`.** Ein Dokument des alten Index
ist also vollstaendig rekonstruierbar, ohne eine einzige Datei aus Nextcloud zu
holen und ohne eine einzige Seite erneut durch Tesseract zu schicken.

Nachgebaut und gemessen (100 Dokumente, 0,33 MB Text, altes Zweifeldschema nach
neuem Dreifeldschema, `Query.all_query()` mit Offset-Paging, `searcher.doc(addr).to_dict()`):

```
gewandert: 100 Dokumente in 0,17 s (0,33 MB Text) -> 1,93 MB Text/s
```

Das ist reine Tokenisierung auf einem Laptopkern. Ein voller Reindex dagegen kostet
Download, Extraktion und vor allem OCR, und OCR liegt bei rund 2 s pro Seite
(`OCR_PAGE_SECONDS`-Kommentar: Median 1.984 ms auf amd64). Bei 52.137 Dokumenten
ist das der Unterschied zwischen Stunden und Tagen auf der Zielbox.

Was die Wanderung braucht und was sie nicht anfasst:

| Punkt | Lage |
|---|---|
| `vectors.db` | unangetastet, keine Neueinbettung. Der Schluessel ist `file_id`, und der wandert mit. |
| `state.db` | unangetastet, Indexmarken bleiben gueltig. |
| Plattenplatz | **zwei Indexverzeichnisse gleichzeitig.** Bei sechs befuellten Feldern ist der neue rund doppelt so gross wie der alte, Spitzenbedarf also etwa das Dreifache des heutigen Index. `MIN_FREE_BYTES` (500 MB) ist dafuer zu niedrig angesetzt; die Wanderung braucht eine eigene, aus der Indexgroesse abgeleitete Platzpruefung vor dem Start. |
| Abbruchfestigkeit | Die Wanderung muss wiederaufnehmbar sein (Paging ueber `file_id`, Fortschritt in `state.db`), sonst faengt eine unterbrochene Migration auf einer langsamen Box von vorne an. |
| `SnippetGenerator` | liest weiter `body_de`, das Feld bleibt das einzige gespeicherte. Hier aendert sich nichts. |

**Empfehlung:** Die Migration `Version001300Date...` bekommt genau diese Wanderung,
und der volle Reindex bleibt der Notnagel fuer den Fall, dass der alte Index
unlesbar ist.

## Sprach-Erkennung: bewusst nicht

Sprach-Erkennung waere nur noetig, wenn pro Dokument entschieden werden soll, in
welches Feld es wandert. Mit der Schema-Entscheidung oben entscheidet das die
Installation einmal und nicht jedes Dokument, und das ist die billigere und die
zero-config-treuere Loesung: ein falsch erkanntes Dokument waere in **keinem** Feld
richtig indexiert und nur durch einen Reindex zu heilen.

Die Kandidaten wurden trotzdem geprueft, damit die Absage belegt ist (PyPI-Abfrage
23.09.2026):

| Kandidat | Version | Lizenz | Warum nicht |
|---|---|---|---|
| `lingua-language-detector` | 2.2.0 (09.03.2026) | Apache-2.0 (Code) | **Wheel 172,5 MB.** Die Sprachmodelle sind einkompiliert. Das allein ist mehr als die Haelfte dessen, was das Embedding-Modell im Image wiegt, fuer eine Funktion, die keine Suche verbessert. Auf einer 4-GB-Box nicht zu rechtfertigen. |
| `fasttext-langdetect` / lid.176 | 1.1.1 (26.05.2026) | Code MIT, **Modell CC BY-SA 3.0** | Share-alike auf einem Modell, das in einem AGPL-Container ausgeliefert wird, ist eine Lizenzfrage, die sich niemand einhandeln muss. Dazu Modelldownload beim ersten Start, was das Zero-Config-Versprechen bricht (die Regel steht schon in CLAUDE.md unter "Modelldownload beim ersten Start"). |
| `py3langid` | 0.4.0 (02.09.2026) | BSD-3-Clause | Technisch der beste Kandidat: rein Python, 4,6 MB, ARM-neutral, gepflegt. Zieht aber **numpy** als harte Abhaengigkeit, und numpy ist im Repo gerade als Aufraeumbefund offen ("numpy undeklariert"). Eine ungeklaerte Abhaengigkeit zur Pflichtabhaengigkeit zu befoerdern ist die falsche Reihenfolge. Fuer eine spaetere Fassung der erste Griff, falls Erkennung doch gebraucht wird. |
| `langdetect` | 1.0.9 (07.05.2021) | MIT | Fuenf Jahre ohne Release, kein `requires_python`. |
| `pycld3` / `gcld3` | 0.22 (2021) / 3.0.13 (2020) | Apache-2.0 | **Keine aarch64-Wheels**, keine cp313-Wheels. Fuer das Multi-Arch-Abbild tot. |

## Installation

Es gibt nichts zu installieren. Der einzige Paketschritt ist eine Pin-Anhebung in
`backend/pyproject.toml`:

```toml
# vorher
"tantivy==0.26.0",
# nachher
"tantivy==0.26.2",
```

```bash
cd backend && uv lock --upgrade-package tantivy && uv sync
```

Kein Eintrag in `backend/Dockerfile` (keine neuen apt-Pakete, die OCR-Sprachen
fahren seit 1.2.0 schon mit), keine Modelldateien, kein zweiter Prozess.

Warum die Anhebung ueberhaupt, wo 0.26.0 alles kann, was gebraucht wird:

- **`Filter.stopword` mit einer Sprache ohne eingebaute Liste ist in 0.26.0 ein
  Rust-Panic, in 0.26.2 ein sauberer `ValueError`.** Beides selbst ausgeloest:
  0.26.0 antwortet auf `Filter.stopword("romanian")` mit
  `PanicException: called Option::unwrap() on a None value` aus
  `src/tokenizer.rs:388`, 0.26.2 mit
  `ValueError: No builtin stop word list for language: romanian`. Ein Panic
  quer durch die FFI-Grenze ist in einem Container, der beim Start Analysatoren
  registriert, die unangenehmste Fehlerart, die es gibt. Fuer die vier Sprachen
  dieses Milestones tritt er nicht auf; er tritt an dem Tag auf, an dem jemand
  Rumaenisch oder Tuerkisch nachtraegt, und dann ist der Absturz die erste
  Fehlermeldung.
- Tantivy-Kern 0.26.2 enthaelt ausserdem Bugfix #3086, "Disable the buffered union
  `seek_danger` override to avoid consuming unaligned scorers". Die Suche dieses
  Projekts baut `Should`-Gruppen, also Unions, und mit sechs Feldern breitere als
  heute. Ein Korrektheitsfix im Union-Scorer gehoert vor eine Verbreiterung.
- Risiko der Anhebung: gering und geprueft. Rust-Kern 0.26.0 auf 0.26.2 ist ein
  Patchsprung, `index_format` bleibt v7, die Wheel-Matrix ist vollstaendig
  (`cp313 manylinux_2_17_aarch64` vorhanden, 4,66 MB), Lizenz MIT.

## Was die vier Sprachen NICHT brauchen

| Vermeiden | Konkretes Problem | Stattdessen |
|---|---|---|
| Komposita-Zerlegung fuer nl | Niederlaendisch schreibt zwar zusammen (`huurovereenkomst`), aber die deutsche Loesung haengt an einer 276.496 Eintraege grossen `wngerman`-Liste mit 23 MB Automat im RSS. Eine gleichwertige niederlaendische Liste in lizenzkonformer Form ist nicht Teil dieses Milestones, und ein halb gefuellter Automat zerlegt falsch. | Ohne Zerlegung ausliefern und es in der Doku sagen. Gemessen: `huurovereenkomsten` wird zu `huurovereenkomst`, das ist die Stammform, nur eben nicht zerlegt. Ein eigener Backlog-Eintrag, falls es jemand meldet. |
| Zweite Stoppwortquelle (`stopwordsiso`, `nltk`) | Eine Liste, die von der im Index verwendeten abweicht, fuehrt zu Anfragen, die ein Wort entfernen, das der Index behalten hat. | Die Ergaenzungsliste aus `stopwords.rs` erzeugen, also aus genau der Quelle, die der Index benutzt. |
| Reihenfolge `stemmer` vor `ascii_fold` | Gemessen: bricht Portugiesisch (`informação` zu `inform`, `informacao` zu `informaca`). | `ascii_fold` als zweiter Filter, vor `stopword`. |
| `ascii_fold` in der deutschen Kette nachruesten | Der deutsche Stemmer faltet selbst und die Komposita-Liste traegt echte Umlaute. Der Kopf von `analyzer.py` begruendet das ausfuehrlich. | Deutsche Kette unveraendert lassen. Der Sprachausbau ist additiv. |
| Meilisearch/charabia als Segmentierer | Zweiter Prozess, Bruch mit Zero-Config, und fuer diese vier Sprachen loest er kein Problem, das tantivy nicht loest. | Nichts tun. |
| Alle sechs Sprachen ab Werk befuellen | 2,12-fache Indexgroesse und 4,6-fache Schreibzeit auf jeder Bestandsinstallation, ohne dass jemand danach gefragt hat. | Werkseinstellung `("de","en")`, `FINDLING_LANGUAGES` waehlt aus. |

## UI-Kataloge es/it/nl/pt

### Erster Befund: die Zahl 174 stimmt nicht mehr

`php/l10n/de.json` traegt am 23.09.2026 **199 Schluessel**, nicht 174, und `fr.json`
und `de_DE.json` ebenso. Die 174 stammt aus Phase 11, `docs/l10n-french.md`
dokumentiert den Zwischenstand 197 aus Phase 13 samt Aufschluesselung. Die
Milestone-Beschreibung und jede Aufwandsschaetzung sollten auf 199 laufen, und der
Plan sollte die Zahl beim Start noch einmal aus der Datei zaehlen statt sie zu
uebernehmen: sie ist zweimal gewachsen, ohne dass jemand es gemerkt haette.

### Werkzeugempfehlung

Die Uebersetzung ist ein **einmaliger Entwicklungsschritt, kein Laufzeitpfad**.
Kein RAM-Budget des Containers ist betroffen, die Werkzeugwahl ist damit eine Frage
der Qualitaet und des Pruefwegs, nicht der Hardware.

| Weg | Empfehlung | Begruendung |
|---|---|---|
| **Maschineller Erstentwurf, dann Owner-Abnahme in einer Tabelle** | **empfohlen** | Genau das Verfahren, das die franzoesische Runde getragen hat: `docs/l10n-french.md` ist eine Tabelle mit allen Schluesseln, damit der Owner sie in einem Lesevorgang pruefen kann, und aus der Tabelle entstehen die JSON- und JS-Dateien mechanisch. Vier weitere Tabellen (`docs/l10n-spanish.md` und so fort) sind die billigste und die bereits bewaehrte Form. |
| **Nextcloud-Transifex fuer Community-Apps** | **als spaetere Option, nicht fuer v1.3** | Die offizielle Doku sagt ausdruecklich: "If your community app should be translated by the Nextcloud community on Transifex just follow the setup section below", Bedingung ist ein Repo auf github.com (gegeben). Preis: `@nextcloud-bot` braucht Schreibrecht auf das Repo und schiebt Kataloge direkt hinein, an den vier Gates und an der Owner-Abnahme vorbei. Das ist ein Kontrollverlust, den man nach dem Release bewusst waehlen kann, aber nicht mitten in einem Milestone mit Gleichstands-Gates. |
| **`translationtool.phar`** | **nuetzlich, unabhaengig vom Rest** | `create-pot-files` und `convert-po-files` erzeugen `translationfiles/<lang>/findling.po` und daraus `l10n/<lang>.json` und `.js`. Damit wird die Katalogerzeugung mechanisch und der Quellstring-Satz maschinell aus dem Code gezogen, statt von Hand gepflegt. Kein Cloud-Zwang. |
| `argostranslate` 1.11.0 lokal | **nein** | Zieht `spacy` **und** `stanza==1.10.1`, und stanza bringt torch mit. Mehrere Gigabyte Entwicklungsinstallation fuer 199 kurze Oberflaechenstrings. |
| `weblate` selbst hosten | **nein** | 2026.9.1, GPL-3.0, Django-Stack mit celery und redis. Das ist eine eigene Betriebsaufgabe fuer einen Solo-Entwickler. |
| Cloud-Uebersetzer (DeepL, Google) | **nein, nicht noetig** | Die Oberflaechenstrings enthalten keine Nutzerinhalte, ein Cloud-Dienst waere also datenschutzrechtlich vertretbar, aber er ist auch nicht besser als ein guter lokaler Erstentwurf plus Muttersprachler-Gegenlesen. Kein Grund, eine Abhaengigkeit von einem Dienst in den Releaseweg zu legen. |

### Was bei den vier Sprachen technisch zu beachten ist

- **Pluralform.** `fr.js` endet auf `"nplurals=2; plural=(n > 1);"`. Fuer die vier
  neuen gilt nach Standard-gettext: **es, it, nl und pt jeweils `nplurals=2; plural=(n != 1);`**
  (also die englisch-deutsche Form, nicht die franzoesische). Das ist der eine Wert,
  den ein aus `fr.js` kopierter Katalog falsch traegt, und `docs/l10n-french.md`
  benennt genau diese Falle schon fuer Franzoesisch. Ein Gate dafuer existiert;
  es muss nur die vier neuen Werte kennen. **Anmerkung fuer pt:** falls jemand
  spaeter `pt_BR` nachtraegt, kippt der Wert dort auf `(n > 1)`.
- **Fuenf Pluralschluessel und 32 Schluessel mit printf-Direktiven** (Stand
  `docs/l10n-french.md`, gegen die heutige Datei nachzuzaehlen) laufen durch das
  Platzhalter-Paritaetsgate. Argumentreihenfolge (`%1$s`, `%2$s`) darf sich beim
  Uebersetzen aendern, die Menge der Direktiven nicht.
- **Nextcloud-Stilregeln** aus dem Developer Manual gelten auch fuer die
  Uebersetzungen: ASCII-Apostroph statt Typografie-Apostroph, `…` als Unicode-Zeichen
  mit geschuetztem Leerzeichen davor, Doppelpunkte in die Uebersetzung aufnehmen
  (manche Sprachen setzen ein Leerzeichen davor). Fuer Spanisch und Italienisch
  kommt die Projektregel dazu: keine Em-Dashes, keine Emojis, und die
  invertierten Satzzeichen im Spanischen (`¿`, `¡`) sind echte Zeichen und kein
  ASCII-Ersatz.
- **Dateizahl.** Je Sprache zwei Dateien (`xx.json`, `xx.js`), also acht neue
  Dateien, und das Katalogtupel im Gate waechst von sechs auf vierzehn.

## Integrationspunkte im Repo

| Datei | Aenderung |
|---|---|
| `backend/src/findling/config.py` | `DEFAULT_LANGUAGES` von `("de","en")` auf die Sechserliste als **Schemareihenfolge**, plus eine neue Konstante fuer die **Werkseinstellung der befuellten Sprachen**, die bei `("de","en")` bleibt. Die beiden Begriffe sind ab v1.3 nicht mehr dasselbe, und der Unterschied gehoert in einen Kommentar, sonst faellt er beim naechsten Lesen zusammen. |
| `backend/src/findling/config.py::_languages()` | Heute filtert der Leser `FINDLING_LANGUAGES` gegen `DEFAULT_LANGUAGES` und faellt bei leerer Schnittmenge auf beide zurueck. Mit sechs Kandidaten entsteht eine neue Frage: darf ein Admin `FINDLING_LANGUAGES=es` setzen und damit Deutsch und Englisch **abschalten**? Empfehlung: ja, ausdruecklich erlauben (eine spanische Instanz spart damit die Haelfte ihres Index), aber die leere Menge weiter auf die Werkseinstellung zurueckfallen lassen. Das ist eine Entscheidung fuer den Plan, kein Nebeneffekt. |
| `backend/src/findling/index/analyzer.py` | Vier neue Ketten, eine Fabrik statt vier Funktionen (die vier unterscheiden sich nur im Sprachnamen und in der Ergaenzungsliste), `ANALYZER_VERSION` auf 2, vier neue `TOKENIZER_*`-Namen. Bauzeit und RSS gemessen: **0,1 ms fuer alle vier zusammen, kein messbarer RSS-Zuwachs.** Kein Singleton noetig, anders als beim deutschen Automaten. |
| `backend/src/findling/index/schema.py` | Vier `add_text_field(..., stored=False, tokenizer_name=...)`. `body_de` bleibt das einzige gespeicherte Feld. |
| `backend/src/findling/index/open.py` | Vier weitere `register_tokenizer`-Aufrufe. **Das ist die Stelle, an der ein vergessener Name als "the tokenizer 'es' for the field 'body_es' is unknown" erst beim ersten `parse_query` auffaellt**, also nach dem Start und nicht beim Start. Der Kopf von `open.py` beschreibt diese Falle bereits fuer de/en. |
| `backend/src/findling/index/writer.py` | Schreibt den Text in die befuellten Felder statt in zwei feste. |
| `backend/src/findling/index/search.py`, `query/rewrite.py` | Feldliste und Boosts aus den befuellten Sprachen ableiten statt aus zwei Konstanten. Keine Akzentvariantenerweiterung noetig (siehe oben). |
| Migration `Version001300Date...` | Pflicht je Minor-Sprung. Traegt die Index-zu-Index-Wanderung. |
| `php/l10n/` | Acht neue Dateien. |
| `backend/tests/test_admin_ui_contract.py` | Katalogtupel von sechs auf vierzehn, harte Schluesselzahl auf den dann gezaehlten Wert. |

## RAM-Budget: die Ergaenzung zur Tabelle in CLAUDE.md

| Komponente | Ruhezustand | Spitze | Beleg |
|---|---|---|---|
| Vier zusaetzliche Analysatoren (es/it/nl/pt) | **0** | **0** | Gemessen 23.09.2026: Bau aller vier in 0,1 ms, RSS-Zuwachs unter der Messaufloesung. Stemmer sind Code, Stoppwortlisten sind statische Daten im Binary. |
| Ergaenzungsliste gefalteter Stoppwoerter | < 10 kB | < 10 kB | 117 kurze Strings. |
| Tantivy-Writer bei sechs befuellten Feldern | unveraendert | unveraendert, aber **haeufigere Commits** | `heap_size` ist die Grenze, nicht die Feldzahl; dreifacher Postingstrom fuellt denselben Heap dreimal so schnell. Das erhoeht die Segmentzahl und die Merge-Last, nicht die Spitze. Auf der Box zu beobachten. |
| Page-Cache fuer den Index | doppelt so gross bei sechs befuellten Feldern | | Der Index ist mmap; ein doppelt so grosser Index heisst doppelt so viel Cache-Druck auf einer 4-GB-Box. **Das ist der eigentliche RAM-Effekt des Sprachausbaus**, und er trifft nur Installationen, die auch wirklich mehrere Sprachen befuellen. |
| Wanderungsspitze bei der Migration | | zwei Indexverzeichnisse auf Platte | Kein RAM, aber Plattenplatz. Siehe oben. |

## Alternatives Considered

| Empfohlen | Alternative | Wann die Alternative besser ist |
|---|---|---|
| Sechs Schemafelder, konfigurationsgesteuert befuellt | Schema nur ueber die konfigurierten Sprachen bauen | Nie. Es spart nachweislich nichts (leere Felder kosten null) und handelt sich dafuer pro Installation ein anderes Schema ein, das beim Oeffnen gegen eine persistierte Sprachmenge geprueft werden muesste. |
| Sechs Schemafelder | Ein Feld pro Dokument, Sprache erkannt | Wenn Installationen mit stark gemischten Bestaenden ueber viele Sprachen auftauchen und die Indexgroesse zum Beschwerdegrund wird. Preis: ein Erkennungsfehler ist nur durch Reindex heilbar, plus eine Abhaengigkeit von 4,6 bis 172 MB. |
| Index-zu-Index-Wanderung | Voller Reindex mit erneutem OCR | Wenn der alte Index beschaedigt ist oder das Schema Felder gewinnt, die nicht aus dem gespeicherten Text ableitbar sind. Beides ist hier nicht der Fall. |
| tantivy 0.26.2 | bei 0.26.0 bleiben | Wenn der Milestone die Pin-Anhebung aus Termingruenden nicht mehr traegt. Dann aber die Sprachnamen hart auf die vier begrenzen und den Panic in einem Kommentar festhalten. |
| Ergaenzungsliste aus `stopwords.rs` erzeugen | `custom_stopword` von Hand pflegen | Nie. Eine handgepflegte Liste driftet gegen die einkompilierte, sobald tantivy seine Listen aktualisiert. Das Erzeugungsskript plus Hash-Test macht die Drift sichtbar. |

## Version Compatibility

| Paket | Vertraegt sich mit | Anmerkung |
|---|---|---|
| tantivy 0.26.2 | Python 3.10 bis 3.14 | `requires_python >=3.10`, cp313-Wheels fuer `manylinux_2_17_aarch64` und `_x86_64` vorhanden, Lizenz MIT. |
| tantivy 0.26.2 | bestehendes Indexverzeichnis | `index_format v7` in 0.26.0 und 0.26.2 identisch, selbst nachgemessen. `INDEX_VERSION` bleibt 1. |
| tantivy 0.26.2 | Rust-Kern tantivy 0.26.2 | Patchsprung von 0.26.0, drei Bugfixes (zwei Aggregationen, einer im Union-Scorer). Keine Breaking Changes; die stehen erst in 0.27.0 an (`.set_fast(..)` nimmt dort ein `&str`). |
| Snowball-Listen und -Stemmer | AGPL-3.0 | BSD-3-Clause, Copyright Porter/Boulton/Shibukawa/Betts. Der Lizenztext muss bei Weitergabe erhalten bleiben, was tantivy im Quellkopf tut; unsere erzeugte Ergaenzungsliste sollte denselben Hinweis tragen. |
| `SCHEMA_VERSION` 2 | Bestandsindex Version 1 | Erzwingt die Migration. Genau dafuer ist die Konstante da. |

## Sources

- `quickwit-oss/tantivy-py`, Tag 0.26.2, `src/tokenizer.rs` (roh von raw.githubusercontent.com abgerufen 23.09.2026): `parse_language` mit 18 Sprachen, `Filter.stopword`-Dokumentation mit der Liste der 13 Sprachen mit eingebauter Stoppwortliste, `ok_or_else`-Fehlerbehandlung. **HIGH**
- Eigene Ausfuehrung gegen `tantivy==0.26.0` im Backend-venv und gegen `tantivy==0.26.2` in einer Wegwerf-uv-Umgebung, 23.09.2026: Sprachmatrix Stemmer/Stoppwoerter, Panic gegen ValueError, `index_format v7` in beiden. **HIGH**
- `quickwit-oss/tantivy`, Tag 0.26.2, `src/tokenizer/stop_word_filter/stopwords.rs` und `gen_stopwords.py`: Wortzahlen je Liste, Snowball-Herkunft, BSD-3-Clause-Lizenztext. **HIGH**
- `quickwit-oss/tantivy`, `CHANGELOG.md` (main, abgerufen 23.09.2026): Inhalt von 0.26.1 und 0.26.2, Breaking Change in 0.27.0. **HIGH**
- Eigene Messreihe 23.09.2026 mit sechs Gutenberg-Texten (de/en/es/it/nl/pt), 1.417 Dokumente zu 600 Woertern, `heap_size=50_000_000`, `num_threads=1`: Indexgroesse und Schreibzeit bei 2/3/6 befuellten Feldern, Nullkosten leerer Felder, Suchlatenz, Wanderungsdurchsatz, Filterreihenfolge gegen Akzentpaare. **HIGH fuer die Verhaeltniszahlen, MEDIUM fuer die absoluten Megabyte** (Korpus ist Belletristik, nicht Verwaltungstext).
- PyPI JSON-API fuer `tantivy`, `lingua-language-detector`, `py3langid`, `langdetect`, `fasttext-langdetect`, `fasttext-predict`, `pycld3`, `gcld3`, `simplemma`, `stopwordsiso`, `argostranslate`, `weblate`, `translate-toolkit`, abgerufen 23.09.2026: Versionen, Releasedaten, Lizenzfelder, `requires_python`, Wheel-Plattformen, Wheelgroessen. **HIGH**
- Nextcloud Developer Manual, `developer_manual/basics/translations.html` und `developer_manual/app_development/translation.html`, abgerufen 23.09.2026: Transifex-Aufnahme fuer Community-Apps, GitHub-Bedingung, `translationtool.phar`, Ordnerlayout `l10n/` und `translationfiles/`, Stilregeln und Pluralregeln. **HIGH**
- Repo selbst: `backend/src/findling/index/analyzer.py`, `schema.py`, `open.py`, `config.py`, `php/l10n/*.json`, `php/l10n/fr.js`, `docs/l10n-french.md`, `backend/tests/test_admin_ui_contract.py`. **HIGH**

## Offene Punkte fuer die Planung

1. **Die absolute Indexgroesse bei sechs befuellten Feldern** gehoert auf den
   Korpus-Snapshot, nicht auf Belletristik. Das ist ein Kandidat fuer das
   BL-F03-Rechenblatt und kostet dort fast nichts extra.
2. **Darf `FINDLING_LANGUAGES` Deutsch und Englisch abschalten?** Produktentscheid,
   nicht Technik. Empfehlung: ja.
3. **Wiederaufnahmefaehigkeit der Wanderung** auf einer Box, die waehrenddessen
   neu startet. Das ist der Punkt, an dem eine Migration zum stillen Datenverlust
   wird, und er braucht einen eigenen Test.
4. **Schluesselzahl der Kataloge** beim Planstart aus der Datei zaehlen (heute 199),
   nicht aus einem Dokument uebernehmen.
5. **Niederlaendische Komposita** als Backlog-Eintrag festhalten, damit die
   bewusste Nicht-Entscheidung nicht als Versehen gelesen wird.

---
*Stack research for: lexikalischer Sprachausbau es/it/nl/pt, Findling v1.3*
*Researched: 2026-09-23*
</content>
</invoke>
