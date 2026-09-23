# Architecture Research (Milestone v1.3 "Sprachausbau")

**Domain:** Nextcloud-ExApp für Datei-Suche (Python-Container + PHP-Companion), lexikalischer Sprachausbau es/it/nl/pt auf einer ausgelieferten 1.2.0
**Researched:** 2026-09-23
**Confidence:** HIGH für alle Integrationspunkte und für die drei kritischen Verhaltensmessungen (am echten Quellcode dieses Repos gelesen, Datei und Zeile benannt; drei tantivy-Verhalten in der installierten 0.26.0 selbst nachgemessen). MEDIUM für zwei Punkte, die am laufenden System zu prüfen sind (Nextcloud-Sprachcodes für Portugiesisch, Wiederaufbaudauer auf der Zielhardware). Beide unten als VERIFIZIEREN markiert.

> Hinweis an den Orchestrator: diese Datei ersetzt die v1.2-Architekturrecherche vom 14.09.2026, die bis jetzt unter diesem Pfad lag. Der alte Inhalt ist über die Git-Historie erreichbar (Commit 583fad2); wer ihn dauerhaft behalten will, archiviert ihn vor dem Commit nach `.planning/milestones/v1.2-ARCHITECTURE.md`.

---

## Executive Summary

**Erstens: `DEFAULT_LANGUAGES` hängt an fast nichts.** Die Backlog-Formulierung "`DEFAULT_LANGUAGES` ("de","en") sind Schema-Felder im Tantivy-Index" ist als Modell richtig, als Fundstelle aber irreführend. Die Konstante steht in `backend/src/findling/config.py:80` und wird im gesamten Produktivcode an genau **einer** Stelle gelesen, nämlich in `_languages()` (`config.py:1002-1015`); ihr einziger Verbraucher ist ein Boolean im Schreibpfad (`index/writer.py:166`, `self._index_english`). Die echte Sprachbindung des Systems liegt in **sechs fest verdrahteten Stellen**, die die Konstante nie anfassen: `index/analyzer.py:79-81` (Kettennamen), `index/schema.py:39-57` und `:99-111` (Feldnamen und Feldtabelle), `index/open.py:98-101` (Registrierung), `query/rewrite.py:55` und `:65` (Suchfelder und Gewichte), `index/search.py:875` (Snippet-Feld) sowie `index/bench.py:228`. Wer nur `DEFAULT_LANGUAGES` erweitert, ändert nichts außer einem Flag.

**Zweitens: die Schema-Erweiterung hat zwei stille Fehlerbilder, und beide sind hier nachgemessen, nicht vermutet.** Ein tantivy-Index persistiert sein Schema bei der Erzeugung; `open_index` öffnet ein vorhandenes Verzeichnis und übernimmt dessen altes Schema (`index/open.py:97`). Gemessen in tantivy 0.26.0 aus `backend/.venv`:

1. `writer.add_document()` mit einem Feld, das das persistierte Schema nicht kennt, wird **ohne Fehler angenommen und der Wert stillschweigend verworfen**. Ein Bestandsindex würde also `body_es` nie befüllen, und nichts im Log sagt es.
2. `index.parse_query_lenient(..., default_field_names=[... "body_es"])` **wirft** `ValueError: Field 'body_es' is not defined in the schema.` Der Suchpfad fängt jede Exception ab (`api/search.py:336-341`) und antwortet mit einer leeren, als "degraded" markierten Seite. Das heißt im Klartext: **auf jeder Bestandsinstallation würde ab dem Upgrade jede einzelne Suche leer antworten**, dauerhaft, mit einer einzigen WARNING-Zeile, die nur den Ausnahmetyp nennt. Das ist exakt die Klasse "stumme Suche nach Minor-Upgrade", die Phase 11 schon einmal gekostet hat, nur in schlimmer.

**Drittens: ein Vollreindex über Nextcloud ist vermeidbar, und das ist der wertvollste Befund dieser Recherche.** Alle acht rekonstruktionsrelevanten Felder des Schemas sind `stored=True` (`index/schema.py:89-114`); das einzige nicht gespeicherte Feld `body_en` trägt denselben Text wie das gespeicherte `body_de`. Ein neuer Index lässt sich daher **vollständig aus dem alten Index heraus** neu schreiben, ohne einen einzigen Download, ohne Textextraktion, ohne OCR und ohne Neuberechnung von Vektoren. `Query.all_query()` plus `searcher.doc(address)` reichen dafür aus (in der installierten Version geprüft). Der Unterschied in der Größenordnung: der gemessene Vollauf auf der m7g-Box lag bei 19 h 20 min für 52.137 Dokumente (`docs/performance.md:159`), der reine Umbau ist eine Analyse- und Schreiboperation und liegt geschätzt bei ein bis drei Stunden (VERIFIZIEREN).

**Viertens: eine Sprachentscheidung pro Dokument gibt es heute nicht, und sie wird auch nicht gebraucht.** `writer.add()` schreibt denselben Text in `body_de` und `body_en` (`index/writer.py:269-271`). Das Modell ist "jeder Text durch jede Kette", nicht "jeder Text durch seine Kette". Das skaliert auf sechs Sprachen mit einem Preis in Indexgröße (grob plus zwei Drittel, Rechnung in Teil B.7) und ohne neue Fehlerquelle. Eine Spracherkennung wäre eine neue Komponente mit einem neuen stillen Fehlerbild (falsch erkannt heißt unauffindbar) und spart nur Platz. Empfehlung: keine Spracherkennung in v1.3.

**Fünftens: die harten Gates dieses Repos sind gegen diesen Milestone gebaut.** `backend/tests/test_upgrade_compatibility.py` hält `schema_version == "1"` als Sperrklinke und sagt im Kopf wörtlich, ein rotes Ergebnis sei "keine Reparatur, sondern eine Frage an den Owner". `.github/workflows/deploy-harp.yml:3271-3305` prüft nach dem Upgrade, dass **kein** Merker sich bewegt hat und **kein** Reindex-Banner steht. Beide werden rot. Das ist kein Unfall, das ist der eingebaute Entscheidungspunkt. Der Milestone braucht deshalb als erste Phase ein Owner-Tor und danach eine **Umkehr der Beweisrichtung**: aus "der Index überlebt das Upgrade unberührt" wird "der Index wird beim Upgrade nachweisbar und vollständig umgebaut, ohne Datenverlust und ohne stumme Lücke".

---

## Neu gegenüber geändert, auf einen Blick

| Komponente | Status | Warum |
|---|---|---|
| `index/analyzer.py`, vier neue Ketten `spanish`/`italian`/`dutch`/`portuguese` | **geändert** (additiv) | Snowball-Stemmer und Stoppwortlisten für alle vier in tantivy 0.26.0 vorhanden, hier nachgemessen. Bestehende de/en/name-Ketten bleiben unberührt |
| `index/schema.py`, vier neue Textfelder | **geändert** | `FIELDS` wächst von 9 auf 13, `build_schema()` bekommt vier `add_text_field(..., stored=False)` |
| `index/open.py`, Registrierung | **geändert** | vier weitere `register_tokenizer`-Zeilen; sonst nichts |
| `config.py`, `SCHEMA_VERSION` | **geändert** | 1 auf 2, und das ist der Auslöser der ganzen Kette |
| **Index-Umbau aus dem alten Index** | **NEU** | die zentrale neue Komponente; es gibt heute keinen Code, der ein Indexverzeichnis wegen eines Schema-Sprungs neu baut |
| **Feldliste der Suche wird schema-abhängig** | **NEU** | `query/rewrite.py:55` ist heute eine Konstante; während des Umbaus muss die alte Feldliste gelten, sonst wirft der Parser |
| `query/rewrite.py`, `FIELD_BOOSTS` | **geändert** | vier Gewichte dazu |
| `index/writer.py`, `add()` | **geändert** | vier `add_text`-Zeilen, `_index_english` wird zu einer Menge aktiver Sprachen |
| `php/lib/Migration/Version001300Date...` | **NEU** (Pflichtmuster) | dieselbe Form wie `Version001200Date20260921000000`, Lockstep-Merker verwerfen |
| `php/l10n/`, zehn neue Katalogdateien | **NEU** | es, it, nl, pt_PT, pt_BR, je `.json` und `.js` |
| `backend/tests/test_admin_ui_contract.py`, Katalog-Gates | **geändert** | `L10N_CATALOGUES` von 6 auf 16 Dateien, Pluralregel- und Vollständigkeits-Gate je Sprache generalisieren |
| `backend/tests/test_upgrade_compatibility.py` | **geändert, mit Owner-Entscheid** | Sperrklinke wird von "kein Merker bewegt sich" auf "genau dieser eine Merker bewegt sich, aus diesem Grund" umgestellt |
| `.github/workflows/deploy-harp.yml`, Upgrade-Beweis | **geändert, Beweisrichtung gedreht** | von Unberührtheit auf Umbaubeweis |
| `store/vectors.py`, Vektorbestand | **unberührt** | die Einbettung ist mehrsprachig und sprachfeldfrei; der Bestand darf den Umbau überleben, und genau das spart den Großteil der Kosten |
| PHP-Suchpfad (`Provider`, `SearchService`, `Highlighter`) | **unberührt** | die Sprachfelder enden am Container; die PHP-Seite kennt weder Felder noch Ketten |
| OCR-Pfad | **unberührt** | Baustein 1 ist in 1.2.0 geliefert, `OCR_LANGUAGE_ALLOWLIST` hat neun Einträge |

---

## Systemüberblick mit den v1.3-Eingriffspunkten

```
┌──────────────────────────────────────────────────────────────────────┐
│ Nextcloud (PHP)                                                      │
│  Unified Search ──> Provider ──> SearchService ──> exAppRequest      │
│  Ergebnisseite  ──> PageController ──> templates/search.php          │
│                                          │                            │
│                                     php/l10n/*.json  <── NEU: es, it,│
│                                                          nl, pt_PT,  │
│                                                          pt_BR       │
│  Migration Version001300Date... <── NEU (Pflicht je Minor)           │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ signierter AppAPI-Aufruf
┌───────────────────────────────┴──────────────────────────────────────┐
│ Container (Python)                                                   │
│                                                                      │
│  api/search.py ──> query/rewrite.py ──> index/search.py             │
│                    DEFAULT_FIELDS       SnippetGenerator             │
│                    FIELD_BOOSTS         (FIELD_BODY_DE)              │
│                    ^^ GEAENDERT +       ^^ unveraendert              │
│                       schema-abhaengig                                │
│                                                                      │
│  worker/poller.py ──> index/writer.py ──> index/open.py             │
│                       add(): vier neue     register_tokenizer x4     │
│                       add_text-Zeilen      ^^ GEAENDERT              │
│                                                                      │
│                       index/analyzer.py: de, en, name                │
│                       + es, it, nl, pt   <── GEAENDERT (additiv)     │
│                       index/schema.py:   9 Felder ──> 13             │
│                                                                      │
│  ╔══════════════════════════════════════════════════════════════╗   │
│  ║ NEU: index/rebuild.py                                        ║   │
│  ║  altes Verzeichnis (Schema 1) ──lesen──> neues (Schema 2)    ║   │
│  ║  kein Download, keine Extraktion, kein OCR, keine Vektoren   ║   │
│  ╚══════════════════════════════════════════════════════════════╝   │
│                                                                      │
│  store/repo.py (SQLite-Zustand + ACL)  ── Merker schema_version      │
│  store/vectors.py (sqlite-vec)         ── UNBERUEHRT                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Teil A: Wo `DEFAULT_LANGUAGES` wirklich dranhängt

### A.1 Die vollständige Fundstellenliste im Produktivcode

Belegt mit `grep` über `backend/src`, Stand 23.09.2026:

| Ort | Zeile | Was dort steht |
|---|---|---|
| `config.py` | 80 | `DEFAULT_LANGUAGES = ("de", "en")`, mit dem Kommentar "Field order of the schema, not the order somebody types into the environment" |
| `config.py` | 1002-1015 | `_languages()`, die einzige Leserin; filtert `FINDLING_LANGUAGES` gegen die Konstante, fällt bei leerer Schnittmenge auf die Konstante zurück |
| `config.py` | 745, 1116 | Feld `languages: tuple[str, ...]` im `Settings`-Dataclass und dessen Befüllung |
| `index/writer.py` | 166 | `self._index_english = ("en" in resolved.languages)`, der einzige Verbraucher im Produktivcode |
| `index/writer.py` | 270-271 | `if self._index_english: document.add_text(FIELD_BODY_EN, body)` |

Das ist alles. Insbesondere gilt:

- **Der Schema-Bau liest sie nicht.** `build_schema()` (`index/schema.py:76-116`) baut immer alle neun Felder, unabhängig von der Einstellung. Das ist Absicht und durch einen Test festgehalten: `backend/tests/test_index_open.py:362-374`, "the schema does not change with the language setting", mit `assert len(FIELDS) == 9`.
- **Die Registrierung liest sie nicht.** `open_index` registriert immer alle vier Ketten (`index/open.py:98-101`).
- **Der Query-Pfad liest sie nicht.** `DEFAULT_FIELDS` (`query/rewrite.py:55`) ist eine Modulkonstante mit vier Feldnamen; sie befragt weder Settings noch Schema. Praktische Folge heute: mit `FINDLING_LANGUAGES=de` fragt die Suche weiterhin `body_en` ab, was harmlos ist, weil das Feld im Schema existiert und nur leer bleibt. Genau diese Harmlosigkeit endet mit Schema 2.
- **Der Snippet-Pfad liest sie nicht.** `SnippetGenerator.create(..., FIELD_BODY_DE)` (`index/search.py:875`) und `_passage_of` (`index/search.py:825`) sind hart auf `body_de` gebunden, weil das die einzige gespeicherte Textkopie im ganzen System ist.
- **Die Migrationen kennen sie nicht.** Die sieben PHP-Migrationen unter `php/lib/Migration/` haben mit dem Index nichts zu tun; die letzte (`Version001200Date20260921000000.php`) verwirft ausschließlich den aufgezeichneten Lockstep-Backendversionsstand.

### A.2 Die sechs Stellen, an denen die Sprache wirklich hängt

| # | Ort | Heute | Was v1.3 dort tut |
|---|---|---|---|
| 1 | `index/analyzer.py:79-81` | `TOKENIZER_DE`, `TOKENIZER_EN`, `TOKENIZER_NAME` | vier Namen dazu; die Namen sind das, was im Schema persistiert wird, nie die Kette (`index/schema.py:22-24`) |
| 2 | `index/analyzer.py:182-192` | `english_analyzer()` als Bauplan | vier Funktionen nach demselben Muster; **keine** Kompositazerlegung, das ist ein Deutsch-Spezifikum, und **mit** `ascii_fold()`, anders als die deutsche Kette |
| 3 | `index/schema.py:39-57, 99-111` | neun Feldnamen, `FIELDS`-Tupel, `build_schema()` | vier Felder `stored=False` dazu; `FIELDS` wächst auf 13 |
| 4 | `index/open.py:98-101` | vier `register_tokenizer` | acht; sonst nichts |
| 5 | `query/rewrite.py:55, 65` | `DEFAULT_FIELDS`, `FIELD_BOOSTS` | acht Felder, acht Gewichte; **und** schema-abhängig, siehe B.3 |
| 6 | `index/bench.py:228` | `[FIELD_BODY_DE, FIELD_NAME, FIELD_TITLE]` im Suchmikrobenchmark | Entscheidung nötig: Benchmark auf die neue Feldbreite heben oder bewusst schmal lassen, damit die Messreihe vergleichbar bleibt |

### A.3 Die Tests, die dabei rot werden

| Test | Zeile | Warum |
|---|---|---|
| `backend/tests/test_index_open.py` | 372 | `assert len(FIELDS) == 9` |
| `backend/tests/test_upgrade_compatibility.py` | 53, 111 | `"schema_version": "1"` als Sperrklinke, mit ausdrücklichem Verbot, den Test grün zu machen |
| `backend/tests/test_store_repo.py` | 796-807 | hält den Merkerwert `"1"` in einer Alt-Datenbank |
| `backend/tests/test_ocr_french.py` | 159-160 | `assert DEFAULT_LANGUAGES == ("de", "en")` und `"fr" not in DEFAULT_LANGUAGES`, gesetzt als Abgrenzung des OCR-Bausteins |
| `backend/tests/test_config.py` | 151-166 | `FINDLING_LANGUAGES`-Fälle inklusive Rückfall |
| `backend/tests/test_admin_ui_contract.py` | 118, 1544, 1547, 1636 | Kataloge: Dateiliste, harte Schlüsselzahl 199, Schlüsselgleichheit, Pluralregel |
| `.github/workflows/deploy-harp.yml` | 3271-3305 | "Store upgrade 5, die sechs Zusicherungen nach dem Upgrade" |

`test_ocr_french.py:159` ist der unterschätzte Eintrag: er wurde in 06.1-21 bewusst als Grenze gesetzt ("der Index hat keine dritte Sprache gelernt, und kein späterer Handgriff kann das unbemerkt aufweichen"). Er darf in v1.3 fallen, aber er muss mit einem Absatz fallen, der sagt warum, sonst wiederholt der nächste Leser die Abgrenzung.

### A.4 Was heute pro Dokument über Sprache entschieden wird: nichts

`IndexBatchWriter.add()` (`index/writer.py:246-284`) schreibt denselben normalisierten Text in `body_de` und, falls Englisch aktiv, in `body_en`. Es gibt **keine** Spracherkennung, keinen Sprachhinweis aus Nextcloud, keine Heuristik, kein Feld, das die Sprache eines Dokuments festhielte. `grep` über `backend/src` nach `langid`, `lingua`, `langdetect`, `detect_language`, `fasttext`: null Treffer.

Das Modell ist also "jeder Text durch jede Kette", und es trägt, weil ein Term, der in einer Kette nicht auftaucht, dort schlicht kein Posting erzeugt. Die Abfrage läuft pro Feld durch dieselbe Kette wie die Indexierung, also stimmen Schreib- und Frageseite pro Feld immer überein, egal welche Sprache der Text hatte.

---

## Teil B: Was "neue Sprachfelder" für Schema, Migration und Bestand heißt

### B.1 Das tantivy-Gesetz

`index/schema.py:2-6` sagt es selbst: "A tantivy schema is written once and read for the lifetime of the index: a field that is added later means a reindex." `index/open.py:97` ist die Zeile, an der das operativ wird:

```python
index = Index.open(str(path)) if Index.exists(str(path)) else Index(build_schema(), path=str(path))
```

Ein vorhandenes Verzeichnis bekommt **nie** das neue Schema. `build_schema()` wird auf einer Bestandsinstallation nach dem Upgrade gar nicht mehr aufgerufen.

### B.2 Die zwei gemessenen Fehlerbilder

Beide nachgemessen am 23.09.2026 mit dem installierten `tantivy 0.26.0` aus `backend/.venv`, nicht aus der Dokumentation übernommen.

**Fehlerbild 1, der stille Verlust auf der Schreibseite.** Ein `Document` mit einem Feld, das das persistierte Schema nicht kennt, wird von `writer.add_document()` **angenommen**, committet, und das unbekannte Feld ist danach spurlos weg. Keine Exception, kein Log, kein Zähler. Das deckt sich mit dem, was `index/schema.py:44-46` für `Document.from_dict` schon festhält, gilt aber genauso für den `add_text`-Weg, den `writer.py` benutzt.

**Fehlerbild 2, der Totalausfall auf der Leseseite.** `parse_query_lenient` mit einem `default_field_names`-Eintrag, den das Schema nicht kennt, wirft `ValueError: Field 'body_es' is not defined in the schema.` Das "lenient" bezieht sich auf Syntaxfehler in der Suchzeile, nicht auf unbekannte Felder. Die Kette danach:

`query/rewrite.py:540` wirft → `api/search.py:243` ist der `try` → `api/search.py:336-341` fängt jede Exception ab, loggt `"the candidate search ended in an unexpected ValueError"` und gibt `_Round([], False, offset, True)` zurück, also **leer und degraded**. Die PHP-Seite bekommt eine gültige, leere Antwort und zeigt "keine Treffer".

Das Ergebnis ist der schlimmstmögliche Ausgang: die Suche ist tot, der Container ist gesund, `/status` meldet einen vollen Index, der Admin sieht nichts als eine WARNING-Zeile ohne Feldnamen (der Feldname steht in der Exception-Message, und die wird bewusst nicht geloggt, `api/search.py:337-339`).

**Konsequenz für die Bauordnung:** Die Erweiterung von `DEFAULT_FIELDS` darf niemals vor dem fertigen Indexumbau wirksam werden. Das ist keine Feinheit, das ist die Reihenfolgebedingung des ganzen Milestones.

### B.3 Was die vorhandene Drift-Mechanik kann und was nicht

Vorhanden ist eine vollständige, gut durchdachte Drift-Erkennung:

- `expected_versions(digest)` (`index/open.py:123-141`) liefert fünf Merker: `schema_version`, `index_version`, `analyzer_version`, `wordlist_hash`, `tantivy_version`.
- `Store.version_mismatch` (`store/repo.py:631-670`) vergleicht sie gegen das, womit der Index wirklich gebaut wurde.
- `start_rebuild_on_drift` (`index/open.py:155-195`) hebt bei Abweichung die lokale Generation, mit einem Fingerabdruck-Merker gegen Endlosschleifen bei Neustarts.
- `stamp_after_rebuild` (`index/open.py:198-254`) schreibt die Merker erst, wenn kein lebendes Verdikt mehr aus einer älteren Generation stammt.
- `version_drift` (`api/resources.py:152-171`) speist `reindexRequired` auf der Statusseite, und `php/templates/admin.php` hebt daraus das Banner mit der Handlungsanweisung `occ findling:index --restart`.

**Was sie nicht kann:** Sie fasst das Indexverzeichnis nicht an. `start_rebuild_on_drift` macht Verdikte stale, damit ein Crawl die Dateien wieder liest. Die Dateien landen dann in einem Index mit **altem Schema**, und Fehlerbild 1 frisst jedes neue Sprachfeld. Selbst ein vollständiger, geduldig abgewarteter Crawl ergäbe am Ende einen Index ohne die vier Felder, während `stamp_after_rebuild` brav `schema_version=2` schreibt und damit lügt.

Es gibt genau einen benachbarten Mechanismus, `_raise_generation_for_lost_index` (`worker/poller.py:341-360`), und der behandelt den umgekehrten Fall (Verzeichnis weg, Datenbank da). Ein "Schema passt nicht, Verzeichnis neu bauen" existiert nirgends.

**Das ist die Lücke, und sie ist die neue Komponente dieses Milestones.**

### B.4 Drei Wiederaufbauwege, mit Kosten

**Weg 1, Vollcrawl über Nextcloud.** Verzeichnis löschen, `reset_for_reindex` (`store/repo.py:981-1001`), Admin fährt `occ findling:index --restart`.

- Kosten: der gemessene Volllauf, 19 h 20 min für 52.137 Dokumente auf m7g.large (`docs/performance.md:159`), zuvor 26 h 37 min (v1.1). Enthält Download, Extraktion, OCR und Einbettung.
- Die Einbettung fällt dabei ein zweites Mal an, obwohl der Vektorbestand gültig bleibt: der Einbettungspass liest den Text über `stored_body` aus dem Index (`worker/poller.py:1174`) und schreibt die Chunks mit `replace_chunks` neu. Reine Verschwendung, aber ohne Eingriff unvermeidlich.
- Nebenwirkung: bis der Crawl durch ist, fällt jede noch nicht wieder indexierte Datei aus der Suche. Bei 19 Stunden ist das ein Arbeitstag mit halber Suche.
- Bewertung: ehrlich, einfach, und für die Zielgruppe (Selfhoster auf 4-GB-Boxen) brutal. Widerspricht dem Geist von D-04.

**Weg 2, Umbau aus dem alten Index heraus. Empfohlen.** Das ist möglich, weil das Schema fast alles speichert. Aus `index/schema.py:89-114`:

| Feld | gespeichert | im Umbau |
|---|---|---|
| `file_id` | ja | direkt übernommen |
| `storage_id` | ja | direkt übernommen |
| `name` | ja | direkt übernommen |
| `title` | ja | direkt übernommen |
| `path` | ja | direkt übernommen |
| `ext` | ja | direkt übernommen |
| `body_de` | **ja**, die einzige Textkopie des Systems | Quelle für alle sechs Sprachfelder |
| `body_en` | nein | rekonstruierbar, es ist derselbe Text wie `body_de` |
| `mtime` | ja | direkt übernommen |

Ablauf: altes Verzeichnis lesend öffnen, neues Verzeichnis daneben mit `build_schema()` erzeugen, alle Dokumente durchlaufen, je Dokument die gespeicherten Werte lesen und in das neue Schema schreiben, committen, umschalten, altes Verzeichnis freigeben.

Durchlauf ist mit der vorhandenen API möglich, in der installierten Version geprüft: `Query.all_query()` existiert, `Searcher.search(query, limit, offset=...)` nimmt einen Offset, `Searcher.doc(address).to_dict()` liefert die gespeicherten Felder. Für 52.000 Dokumente reichen Fenster von 1.000 mit wachsendem Offset; wer die Offsettiefe vermeiden will, läuft in `file_id`-Bereichen (das Feld ist `indexed` und `fast`).

- Kosten: keine Netzlast, keine Extraktion, kein OCR, keine Einbettung. Übrig bleiben Analyse und Plattenschreiben. Gemessen auf dieser Entwicklungsmaschine liegt eine Sprachkette bei 20 bis 46 MB/s Text; die deutsche Kette mit dem Zerlegungsautomaten ist langsamer, ihre Zahl liefert `findling.index.analyzer.measure()`. Bei geschätzt 1,7 GB extrahiertem Text durch sechs Ketten und einem ARM-Abschlag landet man in der Größenordnung **ein bis drei Stunden** (VERIFIZIEREN, gehört in die Messphase BL-F03).
- Platzbedarf: alter und neuer Index gleichzeitig. Heute 785.308.851 Byte (`docs/performance.md:2923`), neu geschätzt rund 1,3 GB, Spitze also rund 2,1 GB. Das muss **vor** dem Start gegen `settings().min_free_bytes` und den freien Platz geprüft werden, mit sauberem Rückfall auf Weg 1, wenn es nicht passt.
- Die Suche kann währenddessen aus dem alten Verzeichnis weiterlaufen, wenn die Feldliste der Frage an das wirklich offene Schema gekoppelt wird (siehe B.5).
- Der Vektorbestand bleibt unberührt. Das ist korrekt: `multilingual-e5-small` ist sprachneutral, die Chunkgrenzen sind Zeichenoffsets in `body_de`, und `body_de` trägt nach dem Umbau denselben Text an denselben Offsets. Der Merker `embedding_mark` bewegt sich nicht (`api/resources.py:146-149` hält ihn ohnehin bewusst aus `expected_versions` heraus).

**Weg 3, "neu ab hier".** Neues Verzeichnis, alter Index wird verworfen, kein Umbau, die Sprachfelder füllen sich nur für Dateien, die ohnehin neu indexiert werden. Verworfen: das ergibt einen Index, der für alte Dokumente anders antwortet als für neue, und genau das ist die Kategorie Fehler, gegen die `ANALYZER_VERSION` und die ganze Merkerlogik gebaut wurden (`index/analyzer.py:51-53`).

### B.5 Die Empfehlung, als Bauanweisung

1. **`SCHEMA_VERSION = 2`** in `config.py:41`. `ANALYZER_VERSION` bleibt bei 1, denn die de/en/name-Ketten ändern sich nicht; das gehört als Absatz in `index/analyzer.py` neben die Konstante, sonst hebt es der nächste Leser reflexhaft mit.
2. **Neues Modul `index/rebuild.py`.** Ein Modul, nicht eine Funktion in `open.py`: `open.py` ist als "die eine Stelle, die einen Index öffnet" definiert und bleibt es; der Umbau ist ein Vorgang mit Lebensdauer, Fortschritt und Abbruchverhalten. Namensregel beachten: der Bezeichner `delete` ist in jedem Modul dieses Pakets gesperrt (Gate A, siehe `index/writer.py:291-293` und `backend/tests/test_readonly_gate.py:63-75`), also `discard_directory` oder `retire_directory`, nicht `delete_index`. `shutil.rmtree` steht nicht auf der Verbotsliste, `mkdir` schon, und `index/open.py` hat dafür bereits eine geprüfte Ausnahme (`test_readonly_gate.py:112`); für ein neues Modul ist ein neuer Eintrag in `INVARIANT_2_EXCEPTIONS` fällig, mit Begründungsabsatz.
3. **Die Feldliste der Frage wird schema-abhängig.** `query/rewrite.py:55` und `:65` werden von Konstanten zu Funktionen des Schemastands, den der offene Index wirklich hat. `tantivy.Schema` gibt in 0.26.0 nichts über sich preis (hier geprüft: `dir(schema)` ist leer), also kann die Quelle nicht der Index sein. Die richtige Quelle ist der Merker `schema_version` aus `Store.read_meta()`: er steht während des Umbaus noch auf `"1"` und wird erst von `stamp_after_rebuild` auf `"2"` gehoben. Damit fragt die Suche während des Umbaus die alten vier Felder und danach die acht, ohne dass irgendwo ein zweiter Zustand geführt wird.
4. **Der Umbau läuft als Aufgabe im Lifespan**, nicht im Startpfad. Ein bis drei Stunden im Start heißt ein Container, den AppAPI für tot hält. Vorbild ist die Entladeaufgabe aus v1.2 (dort als eigene Lifespan-Aufgabe gebaut).
5. **Sichtbarkeit.** Der Umbau bekommt einen eigenen Zustand auf `/status` und ein eigenes Banner auf der Adminseite. Das vorhandene Reindex-Banner nennt `occ findling:index --restart` als Heilmittel, und das ist hier **falsch**: der Admin soll nichts tun außer warten. Ein Banner, das zum Vollcrawl auffordert, während ein billiger Umbau läuft, kostet den Nutzer 19 Stunden aus Versehen. Das ist ein echter Produktfehler in Wartestellung und gehört in die Härtungsphase.
6. **Rückfall auf Weg 1** bei zu wenig Platz, bei einem unlesbaren alten Index und bei einem Umbau, der zweimal hintereinander abbricht. Der Rückfall ist genau die heutige Mechanik, also kein neuer Code, nur eine Verzweigung.

### B.6 Was die PHP-Migration ist, und was sie nicht ist

`Version001300Date2026...` ist **Pflicht**, aber nicht wegen des Index. Der Grund steht im Klassenkommentar von `Version001200Date20260921000000.php:14-45`: der Lockstep-Vergleich (`ExAppService::driftOnRecord`) hält eine aufgezeichnete Backendversion, und ein Update, das nur eine Hälfte bewegt, lässt `SearchService` jede Suche verweigern, bis jemand die Einstellungsseite öffnet. Der gemessene Beleg steht dort ebenfalls: beim Sprung 1.0.3 auf 1.1.0 kamen alle dreißig Canary-Suchen leer zurück.

Die neue Migration ist also eine **Kopie derselben zehn Zeilen** mit neuem Datum, plus der Begründungsabsatz. Sie darf den Container nicht befragen (Maintenance-Mode, kein angemeldeter Nutzer, AppAPI startet möglicherweise gerade neu, `Version001200...:55-61`) und muss gegen einen zweiten Lauf abgesichert sein.

Was sie **nicht** ist: der Ort des Indexumbaus. Der Umbau gehört in den Container, weil nur dort der Index liegt und weil eine Migration, die stundenlang läuft, ein `occ upgrade` in einen Ausfall verwandelt.

Zu prüfen beim Bau: `php/tests/Unit/Version001200Date20260921000000Test.php` ist die Vorlage für den Test der neuen Migration.

### B.7 Indexgröße und RAM, mit Zahlen

Aus `index/schema.py:10-20`: der Index wächst auf das 0,374-fache des extrahierten Textes **mit** Speicherung und auf das 0,076-fache **ohne** sie. Heute trägt der Index eine gespeicherte Kette (`body_de`) und eine ungespeicherte (`body_en`), also grob 0,45-fach. Vier weitere ungespeicherte Ketten bringen rund 4 mal 0,076, also **plus rund 0,30**, Summe grob 0,75-fach.

Gemessener Ist-Stand auf der Box: 785.308.851 Byte für 51.961 Dokumente, 15.113 Byte je Dokument (`docs/performance.md:2923`). Hochgerechnet auf die neue Feldbreite: **rund 1,3 GB**, also plus zwei Drittel. Das ist die eine Zahl, die dem Owner vor dem Bau auf den Tisch gehört, weil sie die Zielgruppe direkt trifft.

Der Faktor 0,076 wurde an deutschem Text durch die deutsche Kette gemessen. Spanisch und Italienisch erzeugen bei gleicher Textmenge andere Termzahlen; im Schnelltest hier lieferte die spanische Kette auf einem spanischen Satz deutlich weniger Tokens als die niederländische auf einem niederländischen. Die Hochrechnung ist also eine Größenordnung, keine Messung (VERIFIZIEREN in BL-F03, billig: ein Umbau auf dem Korpus-Snapshot liefert die echte Zahl nebenbei).

RAM: vernachlässigbar. Der teure Bauteil ist der deutsche Zerlegungsautomat mit rund 23 MB, der pro Prozess genau einmal gebaut wird (`index/analyzer.py:42-47`, `cached_german_analyzer`). Snowball-Stemmer und die eingebauten Stoppwortlisten sind Konstanten in der Rust-Bibliothek. Der Umbau selbst braucht einen zweiten `IndexWriter` mit eigenem Heap (50 MB nach `writer_heap_bytes`); auf einer 4-GB-Box ist das vertretbar, aber es darf nicht gleichzeitig mit OCR laufen. Die Regel `INDEX_WORKERS = 1` (`config.py:74`) und ihr Kommentar ("die OCR-Spitze und die Einbettungsspitze dürfen sich nie treffen") gelten sinngemäß auch hier: während des Umbaus ruht der Indexierungspass.

---

## Teil C: Wie die Sprachentscheidung pro Dokument zustande kommt

### C.1 Drei Feldmodelle

**Modell A, jeder Text in jedes Feld.** Die Fortschreibung des heutigen Verhaltens (`index/writer.py:269-271`).

- Dafür: kein neuer Code außer vier `add_text`-Zeilen, kein neues Fehlerbild, ein mehrsprachiges Dokument ist in jeder seiner Sprachen findbar, das Verhalten ist identisch zu dem, was de/en seit 1.0 tun und was zweieinhalbtausend Tests beschreiben.
- Dagegen: plus rund 0,30-fache Indexgröße, sechsfache Analysearbeit je Dokument.

**Modell B, Spracherkennung je Dokument.** Ein Erkenner (lingua-py, py3langid, fastText) bestimmt die Sprache, das Dokument geht in `body_de` plus höchstens ein Sprachfeld.

- Dafür: Indexgröße bleibt nahe heute, Analysearbeit sinkt.
- Dagegen: eine neue Abhängigkeit mit ARM-Wheel-Frage und Lizenzfrage; ein neues stilles Fehlerbild (falsch erkannt heißt in der falschen Kette heißt für die richtige Suchsprache unauffindbar, ohne dass irgendwo etwas rot wird); Kurztexte und Tabellen sind notorisch schlecht erkennbar, und in einer Nextcloud sind sie die Mehrheit; gemischtsprachige Dokumente (in genau den Behörden- und NGO-Beständen, die die Zielgruppe sind) fallen durch; eine Fehlerkennung ist erst nach einem erneuten Vollumbau korrigierbar. Dazu kommt ein Architekturbruch: der Erkenner müsste im Extraktionskind laufen oder im Poller, und `index/analyzer.py:48-49` verbietet dem Extraktionskind ausdrücklich, dieses Modul zu importieren.
- Bewertung: falsche Reihenfolge. Spracherkennung ist die Optimierung, die man baut, wenn Modell A gemessen zu teuer ist, nicht davor.

**Modell C, eine sprachneutrale Zusatzkette.** Ein einziges neues Feld `body_xx` mit `lowercase` plus `ascii_fold` plus `remove_long`, ohne Stemmer und ohne Stoppwörter, deckt alle vier Sprachen und jede spätere mit.

- Dafür: plus nur 0,076-fach statt 0,30-fach; ein Schemasprung für alle künftigen Sprachen statt einer pro Sprachwelle; kein Stemmer, der in der falschen Sprache Unsinn baut.
- Dagegen: kein Stemming heißt, "notificaciones" findet "notificacion" nicht. Genau diese Wortformentoleranz ist aber das Produktversprechen, mit dem Tantivy überhaupt gegen FTS5 gewonnen hat (`CLAUDE.md`, Abschnitt 1). Modell C liefert Sprachunterstützung dem Namen nach und nicht der Sache nach.
- Bewertung: verwerfen, aber im Roadmap-Dokument benennen, sonst schlägt es jemand in sechs Monaten als Neuerung vor.

### C.2 Empfehlung

**Modell A.** Keine Spracherkennung in v1.3. Als Ventil für kleine Boxen bleibt die schon vorhandene Stellschraube: `FINDLING_LANGUAGES` wählt aus, welche Felder überhaupt befüllt werden (`index/writer.py:166`), und die Erweiterung dieser Mechanik von einem Boolean auf eine Menge ist ein Zweizeiler. Ein Admin mit einem rein deutschen Bestand auf einer 4-GB-Box setzt `FINDLING_LANGUAGES=de` und zahlt die 0,30 nicht.

Dabei ist ein **vorhandener Mangel mitzuerledigen**: `FINDLING_LANGUAGES` ist heute **kein** Versionsmerker. `expected_versions` (`index/open.py:135-141`) kennt ihn nicht. Das heißt, ein Admin, der die Sprachen umstellt, bekommt weder Banner noch Wiederaufbau, obwohl die Beschreibung in `backend/appinfo/info.xml:346-348` das Gegenteil verspricht ("the index has to be built again afterwards"). Heute ist das folgenlos, weil beide Felder immer im Schema stehen und `body_en` höchstens leer bleibt. Mit sechs Sprachen wird daraus eine echte, stille Inkonsistenz. Die Menge der aktiven Sprachen gehört deshalb als sechster Merker in `expected_versions`, und ihre Änderung dann in den billigen Umbauweg, nicht in den Vollcrawl (der Text steht ja im Index).

### C.3 Die vier Ketten, konkret

Vorlage ist `english_analyzer()` (`index/analyzer.py:182-192`), nicht `german_analyzer()`:

```python
def spanish_analyzer() -> TextAnalyzer:
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword("spanish"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("spanish"))
        .build()
    )
```

Gemessen am 23.09.2026 gegen `tantivy 0.26.0` aus `backend/.venv`, jede Kette gebaut und auf einem Satz der jeweiligen Sprache laufen lassen:

| Sprache | `Filter.stemmer` | `Filter.stopword` | Probe |
|---|---|---|---|
| spanish | ja | ja | "Las notificaciones administrativas fueron enviadas rapidamente" ergibt `notif, administr, envi, rapid` |
| italian | ja | ja | "Le notificazioni amministrative sono state inviate" ergibt `notif, amministr, stat, invi` |
| dutch | ja | ja | "De administratieve kennisgevingen werden verzonden" ergibt `administratiev, kennisgev, werd, verzond` |
| portuguese | ja | ja | "As notificacoes administrativas foram enviadas" ergibt `notificaco, administr, envi` |
| danish | ja | ja | funktioniert ebenfalls, falls Dänisch je dazukommt |
| **estonian** | **nein** | **nein** | `ValueError: Unsupported language: estonian` |

Der letzte Eintrag ist eine Nachricht an die Outreach-Spur: die Zusage an Bürokratt (EE) ist mit OCR eingelöst, eine **lexikalische** estnische Kette gibt tantivy 0.26.0 nicht her. Das gehört in die Antwort an den Kontakt und nicht erst in die Release Notes.

Drei Entwurfsentscheidungen, die beim Bau bewusst zu treffen sind:

- **`ascii_fold()` gehört in alle vier Ketten.** Die deutsche Kette hat bewusst keine (`index/analyzer.py:34-40`, der deutsche Snowball-Stemmer faltet Umlaute selbst und die Zerlegungsliste trägt echte Umlaute). Für Spanisch, Portugiesisch und Italienisch gilt das nicht: Tilde, Cedille und Akzente müssen gefaltet werden, sonst findet "notificacao" ohne Sonderzeichen nichts. Die Probe oben bestätigt, dass die Faltung greift.
- **Keine Kompositazerlegung.** Niederländisch kennt Komposita, aber die Wortliste ist eine deutsche (`wngerman`), der Automat kostet 23 MB, und eine niederländische Liste ist kein Bestandteil dieses Milestones. Ausdrücklich benennen, nicht stillschweigend weglassen.
- **`title` bleibt auf der deutschen Kette** (`index/schema.py:99`). Vier weitere Titelfelder wären acht statt vier neue Felder für einen Metadatenwert von wenigen Wörtern. Der Dateiname läuft ohnehin über die sprachneutrale gefaltete Kette (`TOKENIZER_NAME`), und der trägt in der Praxis die meiste Titelinformation. Als Entscheid festhalten, sonst kommt die Frage in jeder Planungsrunde wieder.

### C.4 Zwei Verhaltensfragen für die Messphase

- **Konjunktion über acht Felder.** `parse_query_lenient` läuft mit `conjunction_by_default=True` (`query/rewrite.py:544`). Aus einem Suchwort wird ein ODER über alle Standardfelder, aus mehreren Wörtern ein UND darüber. Mit acht statt vier Feldern verdoppelt sich die Klauselzahl. Bei p95-Werten im Millisekundenbereich (`config.py:106-110` nennt 0,196 ms im Leerlauf) ist das vermutlich unsichtbar, aber es ist eine Messung und keine Meinung.
- **Stoppwortkollisionen.** Ein Wort kann in einer Sprache Stoppwort und in einer anderen Inhaltswort sein ("die" ist deutsches Stoppwort und englisches Verb, "come" italienisches Stoppwort und englisches Verb). Pro Feld ist das korrekt, weil Schreib- und Frageseite dieselbe Kette benutzen; interessant wird nur der Fall, in dem ein Term in **allen** Feldern verschwindet und die Konjunktion dadurch eine leere Klausel bekommt. Das ist mit de/en schon möglich und wurde nie gemeldet; mit sechs Sprachen steigt die Wahrscheinlichkeit. Ein Sprachfall in `.github/workflows/integration.yml` je neuer Sprache ist der billige Nachweis, dass die Ketten wirklich greifen; das Muster dafür steht in `backend/tests/test_corpus_terms.py` und ist streng (ein Term muss in genau einer Korpusdatei stehen und ohne die Kette nichts finden).

---

## Teil D: UI-Kataloge es/it/nl/pt

### D.1 Der Ist-Stand, und eine korrigierte Zahl

Die Milestone-Beschreibung nennt "je 174 Schlüssel". Das ist **veraltet**. Gezählt am 23.09.2026 aus `php/l10n/de.json`: **199 Schlüssel**, davon 5 mit Pluralformen. Die harte Zahl im Gate steht auf 199 (`backend/tests/test_admin_ui_contract.py:1544`); der Weg 173 auf 174 auf 197 auf 198 auf 199 ist im Docstring darüber Absatz für Absatz begründet, und die Regel dort lautet: "Whoever raises it next writes the next paragraph."

Heute sechs Dateien für drei Sprachcodes (`test_admin_ui_contract.py:118`): `de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js`.

### D.2 Wie viele Dateien wirklich dazukommen

Nicht acht, sondern **zehn**, und der Grund ist derselbe, der 09.09.2026 zu `de_DE` geführt hat: Nextcloud liefert eigene Sprachcodes aus, und eine App ohne passenden Code ist für diese Nutzer englisch. Geprüft gegen `core/l10n` im Serverrepository: `es.json`, `it.json` und `nl.json` existieren, **`pt.json` existiert nicht**, stattdessen `pt_BR.json` und `pt_PT.json` (MEDIUM, VERIFIZIEREN: in der Test-Nextcloud `ls core/l10n/` fahren, bevor Dateien angelegt werden).

| Sprache | Codes | Dateien |
|---|---|---|
| Spanisch | `es` | `es.json`, `es.js` |
| Italienisch | `it` | `it.json`, `it.js` |
| Niederländisch | `nl` | `nl.json`, `nl.js` |
| Portugiesisch | `pt_PT` und `pt_BR` | vier Dateien, gleicher Wortlaut nach dem `de`/`de_DE`-Muster, oder ein begründeter Entscheid für nur einen der beiden |

`L10N_CATALOGUES` wächst damit von 6 auf 16.

### D.3 Die Gates, und was an ihnen zu verallgemeinern ist

| Gate | Zeile | Heute | Änderung |
|---|---|---|---|
| gleiche Schlüsselmenge über alle Kataloge | 1547 | sechs Dateien | Tupel erweitern, Logik trägt |
| deutsche Kataloge unter beiden Codes identisch | 1456 | `de` gegen `de_DE`, Textvergleich | Analogon für `pt_PT` gegen `pt_BR`, falls beide kommen |
| jeder Wert trägt einen echten Wortlaut | 1579 | `scan_french_completeness`, mit benannter Ausnahmeliste `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` (fünf Einträge) | pro Sprache eine eigene Ausnahmeliste; "PDF", "Findling", "Images", "Documents" fallen in mehreren Sprachen an. Die Form ist Liste mit Begründung je Eintrag, **nicht** Schwellwert, und dieser Entwurfsentscheid steht im Docstring bei Zeile 320 |
| Platzhalterparität | 1607 | `%s`, `%1$s`, `%n`, `%%` | sprachunabhängig, nur auf alle Kataloge ausdehnen |
| Pluralregel | 1636 | `FRENCH_PLURAL_FORM` gegen `GERMAN_PLURAL_FORM`, unterscheidet sich bei n = 0 | je Sprache eine Konstante. Erwartung für es/it/nl/pt_PT: `nplurals=2; plural=(n != 1);`, für pt_BR eher `plural=(n > 1);` (MEDIUM, VERIFIZIEREN gegen den `Plural-Forms`-Kopf der jeweiligen Nextcloud-Kerndatei, nicht gegen Erinnerung) |
| Bindestriche und Emojis in Katalogen | 831 | `scan_prose` über alle Kataloge | trägt unverändert; spanische und portugiesische Maschinenübersetzungen liefern gern Halbgeviertstriche, hier fällt das auf |

### D.4 Die Prozessfrage, die der Owner entscheidet

Das FR-Gate war Muttersprachlerabnahme; der Weg dorthin war eine Tabelle in `docs/l10n-french.md`, die der Owner in **einem** Lesevorgang abgenommen hat, und aus der `fr.json` und `fr.js` mechanisch entstanden. Für vier Sprachen ohne Muttersprachler ist der Vorschlag der Milestone-Beschreibung "maschinell plus Community-Review". Das lässt zwei Fragen offen, und beide gehören vor die Erstellung und nicht danach:

1. **Wird vor dem Review ausgeliefert?** Wenn ja, was steht als Qualitätsaussage im Store-Text und in `docs/`? Eine halbrichtige Übersetzung ist sichtbarer als gar keine.
2. **Wo findet der Review statt?** Nextcloud-Apps nutzen üblicherweise Transifex; dieses Projekt hat bisher bewusst keinen externen Dienst. Ein GitHub-Issue je Sprache mit der Tabelle aus `docs/l10n-*.md` ist der Weg, der zum Repo passt, und er passt zu dem Reddit-Nutzer, der Hilfe angeboten hat (BACKLOG BL-F02, Anlass).

Dazu ein Randstück mit eigenem Entscheid: die **Store-Seite** trägt heute `<name lang="fr">`, `<summary lang="fr">` und `<description lang="fr">` (`docs/store-listing.md:128, 142`). Ob die vier neuen Sprachen dort auch erscheinen, ist eine zweite Frage; sie fällt unter die Kurztext-Regel (Owner-Abnahme vor Einreichung) und ist unabhängig vom UI-Katalog entscheidbar.

---

## Bauvorschlag mit Abhängigkeiten

```
Phase 17  Owner-Tor: Reindex-Entscheid und Feldmodell
             │  (D-04 wird gebrochen; ohne Entscheid kein Code)
             ▼
Phase 18  Ketten und Schema (im Container, ohne Wirkung nach aussen)
             │  analyzer.py +4, schema.py 9->13, open.py +4,
             │  SCHEMA_VERSION=2, writer.py schreibt die Felder
             │  ABER: DEFAULT_FIELDS bleibt bei vier
             ▼
Phase 19  Der Umbau (index/rebuild.py, die neue Komponente)
             │  Durchlauf, Platzpruefung, Umschaltung, Rueckfall,
             │  Lifespan-Aufgabe, Statusfeld, eigenes Banner
             ▼
Phase 20  Die Frageseite aufdrehen (schema-abhaengige Feldliste)
             │  erst hier darf body_es je in einer Query auftauchen
             ▼
Phase 21  Beweisstrecke drehen (CI + Sperrklinke) ─┐
Phase 21' Kataloge es/it/nl/pt (unabhaengig)  ─────┤
Phase 22  Messanfahrt BL-F03 + Umbaudauer + Indexgroesse
             ▼
Phase 23  Haertung und Store-Einreichung 1.3.0
             (inkl. PHP-Migration Version001300Date...)
```

**Warum diese Reihenfolge, und nicht die naheliegende.** Der Reflex wäre, Schema und Query-Felder in einem Zug zu ändern, weil sie inhaltlich zusammengehören. Genau das ist der Totalausfall aus B.2: zwischen "Schema erweitert" und "Umbau fertig" liegt auf jeder Bestandsinstallation ein Zeitfenster, und wenn `DEFAULT_FIELDS` in diesem Fenster die neuen Felder nennt, antwortet jede Suche leer. Die Trennung von Phase 18 und Phase 20 ist keine Zerlegung nach Aufwand, sie ist die Sicherheitsbedingung.

**Warum das Owner-Tor eine eigene Phase ist.** `backend/tests/test_upgrade_compatibility.py` sagt im Kopf: "A red test here is not a repair, it is a question for the owner. Nothing in this file may be adjusted to make it green again. The green way out is to leave the mark where it is; the other way out is a decision that an upgrade rebuilds every installed index, and that decision is not a test edit." Der Milestone beginnt mit genau dieser Frage. Das Vorbild für die Form ist der stable35-Entscheid aus v1.2, der ebenfalls als eigener Plan in der ersten Phase lag.

**Was dem Owner im Tor vorliegen muss:**

1. Die zwei gemessenen Fehlerbilder aus B.2, damit klar ist, dass "kein Umbau" keine Option ist.
2. Die drei Wege aus B.4 mit ihren Zahlen: 19 h 20 min gemessen gegen ein bis drei Stunden geschätzt.
3. Die Indexgröße: 785 MB heute gegen rund 1,3 GB, plus zwei Drittel.
4. Das Feldmodell A gegen B gegen C aus Teil C.1.
5. Die Frage nach `FINDLING_LANGUAGES` als sechstem Versionsmerker.
6. Den Katalogprozess aus D.4.

**Was parallel laufen kann.** Phase 21' (Kataloge) hängt an nichts aus dem Indexstrang und kann jederzeit vorgezogen werden, wenn der Indexstrang am Owner-Tor wartet. Das ist der einzige echte Parallelpfad des Milestones.

**Was zuletzt kommt.** Die PHP-Migration ist Pflicht, aber sie ist zehn Zeilen und darf nicht am Anfang stehen: ihr Datum wandert mit dem Releasedatum, und eine Migration mit einem Datum aus dem Planungsmonat ist eine Ungenauigkeit, die niemand später korrigiert.

---

## Anti-Patterns für diesen Milestone

### `DEFAULT_LANGUAGES` erweitern und glauben, damit sei etwas geschehen

Die Konstante hat genau einen Verbraucher (`index/writer.py:166`). Ein Tupel mit sechs Einträgen ohne Schema-, Ketten- und Registrierungsänderung ergibt einen `_index_english`-Ausdruck, der weiterhin nur nach `"en"` fragt, und sonst nichts. Der Test `test_ocr_french.py:159` fällt dabei, was leicht als "die Änderung wirkt" fehlgelesen wird.

### Das Schema erweitern, ohne das Indexverzeichnis anzufassen

Hier gemessen: der Schreibweg verliert die Werte lautlos, der Leseweg wirft und wird zu einer leeren Antwort verschluckt. Die vorhandene Drift-Mechanik hilft **nicht**: sie hebt die Generation, und der Crawl schreibt die Dokumente in ein Verzeichnis mit altem Schema zurück. Am Ende schriebe `stamp_after_rebuild` sogar `schema_version=2` in einen Index, der Schema 1 hat.

### Den Umbau in die PHP-Migration legen

Eine Migration läuft in `occ upgrade`, im Maintenance-Mode, ohne angemeldeten Nutzer, und möglicherweise während AppAPI den Container neu startet (`Version001200Date20260921000000.php:55-61`). Ein Umbau von ein bis drei Stunden an dieser Stelle verwandelt ein App-Update in einen Ausfall, und ein Abbruch mittendrin in eine kaputte Installation.

### Das vorhandene Reindex-Banner für den Umbau wiederverwenden

Es nennt `occ findling:index --restart` als Heilmittel. Während eines laufenden billigen Umbaus ist das die Aufforderung, stattdessen 19 Stunden Vollcrawl zu starten. Der Umbau braucht eine eigene Zustandsmeldung, deren Handlungsanweisung "warten" lautet.

### Den Vektorbestand mit wegwerfen

Reflex bei "Reindex ist fällig". Falsch: `multilingual-e5-small` ist mehrsprachig, die Chunkgrenzen sind Zeichenoffsets in `body_de`, und `body_de` trägt nach dem Umbau denselben Text an denselben Offsets. Der Einbettungsmerker wird aus `expected_versions` bewusst herausgehalten (`api/resources.py:146-149`, D-21), genau damit ein Indexereignis den Vektorbestand nicht mitreißt. Wer ihn trotzdem verwirft, kauft sich die teuerste Hälfte des Volllaufs ohne Gegenwert.

### Spracherkennung einbauen, weil es ordentlicher klingt

Siehe C.1, Modell B. Sie spart Platz und kauft dafür ein stilles Fehlerbild in einem System, dessen gesamte Architektur darauf ausgelegt ist, stille Fehlerbilder zu vermeiden. Wenn Modell A gemessen zu teuer ist, ist sie die richtige nächste Stufe, aber die Messung kommt zuerst.

### `pt.json` anlegen

Nextclouds Kern kennt `pt_BR` und `pt_PT`, kein blankes `pt`. Eine `pt.json` würde nie geladen, jedes Gate wäre grün, und die Sprache wäre trotzdem nicht da. Dieselbe Falle hat 09.09.2026 schon einmal zugeschnappt, damals mit `de_DE` (`test_admin_ui_contract.py:88-94`).

### Die Schlüsselzahl 174 übernehmen

Sie steht so im Milestone-Auftrag und ist seit dem 19.09.2026 falsch. Die Zahl ist 199, sie steht hart im Gate (`test_admin_ui_contract.py:1544`), und wer sie senkt, macht das Gate blind.

---

## Integrationspunkte in Kurzform

### Container, Schreibseite

| Datei | Zeile | Eingriff |
|---|---|---|
| `config.py` | 41 | `SCHEMA_VERSION = 1` auf `2` |
| `config.py` | 80 | `DEFAULT_LANGUAGES` auf sechs Einträge, Reihenfolge = Schemareihenfolge |
| `config.py` | 1002-1015 | `_languages()` trägt bereits jede Menge, kein Eingriff nötig |
| `index/analyzer.py` | 79-81 | vier Tokenizernamen |
| `index/analyzer.py` | nach 192 | vier Kettenfunktionen nach dem Muster von `english_analyzer` |
| `index/schema.py` | 39-57 | vier Feldkonstanten, `FIELDS` auf 13 |
| `index/schema.py` | 111 | vier `add_text_field(..., stored=False, tokenizer_name=...)` |
| `index/open.py` | 98-101 | vier `register_tokenizer` |
| `index/writer.py` | 166 | `_index_english: bool` wird zu einer Menge aktiver Sprachen |
| `index/writer.py` | 269-271 | Schleife über die aktiven Sprachfelder statt einer `if`-Zeile |
| **`index/rebuild.py`** | neu | Durchlauf, Neuschrift, Umschaltung, Platzprüfung, Rückfall |
| `worker/poller.py` | 305-338 | `_open_state` und `_open_writer` müssen den Umbauzustand kennen; der Indexierungspass ruht währenddessen |

### Container, Leseseite

| Datei | Zeile | Eingriff |
|---|---|---|
| `query/rewrite.py` | 55 | `DEFAULT_FIELDS` von Konstante zu Funktion des Merkers `schema_version` |
| `query/rewrite.py` | 65 | `FIELD_BOOSTS` ebenso; Startwert für die vier neuen Felder 0.8 wie `body_en` |
| `query/rewrite.py` | 540-546 | Aufrufstelle, unverändert, bekommt nur die andere Liste |
| `index/search.py` | 875 | Snippet bleibt auf `FIELD_BODY_DE`, weil das die einzige gespeicherte Kopie ist; kein Eingriff, aber im Plan festhalten |
| `api/search.py` | 336-341 | der Sammelfang, der Fehlerbild 2 verschluckt; prüfen, ob ein `ValueError` aus dem Parser künftig eine eigene, lautere Behandlung verdient |
| `api/resources.py` | 135-149 | `expected_marks`, falls die Sprachmenge sechster Merker wird |
| `api/status.py`, `tools/index_status.py` | 61 | Umbauzustand nach außen sichtbar machen |

### PHP-Companion

| Datei | Eingriff |
|---|---|
| `php/lib/Migration/Version001300Date...` | neu, Vorlage `Version001200Date20260921000000.php`, Test-Vorlage `php/tests/Unit/Version001200Date20260921000000Test.php` |
| `php/l10n/` | zehn neue Dateien |
| `php/templates/admin.php` | Banner für den Umbauzustand, getrennt vom Reindex-Banner |
| `php/appinfo/info.xml` | Versionssprung, ggf. Sprachzeile im Store-Text |
| Provider, SearchService, Highlighter | **kein** Eingriff |

### Gates, die den Bau begleiten

| Gate | Was zu tun ist |
|---|---|
| `test_upgrade_compatibility.py` | Sperrklinke umstellen, mit Owner-Beleg im Docstring; die Form "Versprechen als Test" bleibt |
| `deploy-harp.yml`, "Store upgrade 5" | Beweisrichtung drehen: statt "kein Merker bewegt sich" nun "genau `schemaVersion` bewegt sich, der Umbau läuft an, endet, und danach findet die Suche dieselben drei Korpusterme wie vorher" |
| `deploy-harp.yml`, `UPGRADE_FROM_TAG` | von `v1.1.0` auf `v1.2.0` |
| `integration.yml` | je neuer Sprache ein Sprachfall nach dem Muster von `test_corpus_terms.py` |
| `test_readonly_gate.py` | Eintrag in `INVARIANT_2_EXCEPTIONS` für `index/rebuild.py`, plus Begründungsabsatz |
| `test_index_open.py:372` | `len(FIELDS)` auf 13 |
| `test_admin_ui_contract.py` | `L10N_CATALOGUES` auf 16, Pluralregeln und Ausnahmelisten je Sprache |
| `test_ocr_french.py:159-160` | Abgrenzung fällt, mit Absatz |

---

## Offene Punkte, vor dem Bau zu klären

| # | Punkt | Wer entscheidet | VERIFIZIEREN |
|---|---|---|---|
| 1 | Reindex ja und in welcher Form: Weg 1, 2 oder 3 | Owner | nein, Entscheid |
| 2 | Feldmodell A, B oder C | Owner, Empfehlung A | nein, Entscheid |
| 3 | Wird die Sprachmenge sechster Versionsmerker? | Owner | nein, Entscheid |
| 4 | Wie lange dauert der Umbau auf m7g.large wirklich? | Messung | **ja**, gehört in BL-F03, Snapshot `snap-03f1d1d9ad9262704` steht bereit |
| 5 | Wie groß wird der Index wirklich? Der Faktor 0,076 stammt aus deutscher Messung | Messung | **ja**, fällt beim Umbau in Punkt 4 kostenlos mit an |
| 6 | Reichen 2,1 GB Spitzenplatz auf typischen Installationen? Was tut der Rückfall genau? | Owner plus Messung | **ja** |
| 7 | Nextcloud-Sprachcodes: `pt_PT` plus `pt_BR`, oder nur einer? | Owner | **ja**, `ls core/l10n/` in der Test-Nextcloud |
| 8 | Pluralregeln je Sprache | Bau | **ja**, `Plural-Forms` aus den Kerndateien lesen, nicht aus dem Gedächtnis |
| 9 | Katalogprozess: maschinell, dann Review wo und durch wen, und wird vor dem Review ausgeliefert? | Owner | nein, Entscheid |
| 10 | Kommen die vier Sprachen auch in die Store-Seite (`<summary lang=...>`)? | Owner, Kurztext-Regel | nein, Entscheid |
| 11 | `index/bench.py:228`: Benchmark auf acht Felder heben oder schmal lassen? | Bau, Auswirkung auf Vergleichbarkeit der Messreihe | nein |
| 12 | Estnisch lexikalisch geht nicht. Wie wird das an Bürokratt kommuniziert? | Owner | nein, Fakt steht |

---

## Sources

**Quellcode dieses Repos, gelesen am 23.09.2026 (HIGH).** Jede Aussage oben nennt Datei und Zeile. Zentral: `backend/src/findling/config.py`, `index/{analyzer,schema,open,writer,search,bench}.py`, `query/rewrite.py`, `api/{search,resources}.py`, `store/repo.py`, `worker/poller.py`, `php/lib/Migration/Version001200Date20260921000000.php`, `backend/tests/{test_upgrade_compatibility,test_index_open,test_admin_ui_contract,test_readonly_gate,test_corpus_terms,test_ocr_french}.py`, `.github/workflows/deploy-harp.yml`, `backend/appinfo/info.xml`.

**Eigene Messungen gegen `tantivy 0.26.0` aus `backend/.venv`, 23.09.2026 (HIGH).** Vier Proben:

1. `Filter.stemmer`/`Filter.stopword` für spanish, italian, dutch, portuguese, danish gebaut und auf Sätzen laufen lassen; estonian wirft `ValueError: Unsupported language`.
2. `writer.add_document()` mit einem schemafremden Feld: angenommen, Wert stillschweigend verworfen, `to_dict()` danach ohne das Feld.
3. `parse_query_lenient(default_field_names=[...schemafremdes Feld])`: `ValueError: Field 'body_es' is not defined in the schema.` Dasselbe für `parse_query`.
4. `Query.all_query()` plus `Searcher.search(..., offset=...)` plus `Searcher.doc(address).to_dict()`: liefert die gespeicherten Felder, also ist der Umbau aus dem alten Index technisch möglich. `tantivy.Schema` gibt in 0.26.0 keine Feldliste preis (`dir(schema)` ist leer), deshalb muss die Feldliste der Frage an den Merker gekoppelt werden.
5. Durchsatz der vier neuen Ketten auf dieser x86-Entwicklungsmaschine: 20 bis 46 MB/s Text je Kette. Nur Größenordnung, ARM-Abschlag nicht eingerechnet.

**Messberichte dieses Projekts (HIGH).** `docs/performance.md:159` (Volllauf 19 h 20 min, 52.137 Dokumente), `:2923` (Tantivy-Index 785.308.851 Byte, 15.113 Byte je Dokument), `:2924` (Vektorbestand 68.642.504 Byte), `:1575` (Korpus 50.000 Dateien, 20,2 GB). `backend/src/findling/index/schema.py:10-20` (Faktoren 0,374 und 0,076).

**Planungsunterlagen (HIGH).** `.planning/PROJECT.md`, `.planning/BACKLOG.md:144-200` (BL-F02 mit dem Stand von Baustein 1), `docs/l10n-french.md` (Katalogprozess als Vorlage).

**Nextcloud-Serverrepository, `core/l10n` (MEDIUM).** `es.json`, `it.json`, `nl.json`, `pt_BR.json` und `pt_PT.json` vorhanden, kein `pt.json`. Vor dem Anlegen der Dateien in der Test-Nextcloud gegenprüfen, weil die Liste sich mit Serverversionen ändern kann.

---
*Architecture research for: Nextcloud-ExApp Findling, Milestone v1.3 Sprachausbau*
*Researched: 2026-09-23*
