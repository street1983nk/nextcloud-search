# Architecture Research (Milestone v1.2 "Messbeleg und Ausbau")

**Domain:** Nextcloud-ExApp für Datei-Suche (Python-Container + PHP-Companion), Ausbau einer ausgelieferten 1.1.0
**Researched:** 2026-09-14
**Confidence:** HIGH für alle Integrationspunkte (direkt am Quellcode dieses Repos gelesen, Dateien und Zeilen benannt), MEDIUM für zwei Punkte, die vor dem Bau am laufenden System zu verifizieren sind (tantivy `order_by_field`-Trefferform, tatsächlicher RAM-Gewinn der Entladung). Beide sind unten als VERIFIZIEREN markiert.

> Hinweis an den Orchestrator: diese Datei ersetzt die v1.0-Architekturrecherche vom 15.08.2026, die bis jetzt unter diesem Pfad lag. Der alte Inhalt ist über die Git-Historie erreichbar; wer ihn dauerhaft behalten will, archiviert ihn vor dem Commit nach `.planning/milestones/v1.0-ARCHITECTURE.md`.

---

## Executive Summary

Alle drei v1.2-Vorhaben sind **Erweiterungen entlang bestehender Nahtstellen**, keines verlangt eine neue Komponente, keine neue Route, keine zweite Berechtigungsgrenze und keinen Reindex.

1. **Dateityp-Filter und Sortierung** gehören vollständig in den Backend-Kandidatenpfad. Das Feld `ext` existiert seit v1.0 im Schema, `mtime` liegt als Fast-Field vor, und der Filter ist als `type:`-Präfix im Suchtext bereits implementiert. Der Ausbau ist: ein zusätzliches Request-Feld statt des Textpräfixes (Grund: das Präfix schaltet über `carried_operators` die semantische Hälfte ab), ein Sortierzweig in `index/search.py::candidates` und die Übertragung von Filter und Sortierung in den URL-Zustand der Ergebnisseite. Auf der PHP-Seite wird **nichts sortiert**: die Reihenfolge der Kandidaten ist der einzige Kanal, und sie wird durchgereicht.
2. **Modell-Entladung** gehört an zwei Halter, nicht an einen: `EmbeddingModel._engine` (Gewichte plus Session-Tokenizer) und `Poller._chunker` (Tokenizer plus Splitter, der mit 544,3 MB **größere** der beiden Posten). Die bestehende Sperrenarchitektur trägt die Entladung ohne Umbau, weil `_embed` die `_Engine` in eine lokale Variable holt: ein laufender Stapel hält seine eigene Referenz, eine Freigabe kann ihn also nicht unter den Füßen wegziehen. Der Auslöser gehört in eine eigene Aufgabe im Lifespan von `main.py`, nicht in den Poller, weil ein stummgeschalteter Poller `run_once` nie wieder betritt.
3. **Messphase** ist zu großen Teilen Wiederverwendung: `search_load.py` ist seit 10.09. gefixt und belegt, `aws_box.sh` kann `start/snapshot/destroy`, die Ablaufdatei-Form (`skripte/00-ablauf.md` mit vorher notierter Erwartung) ist etabliert und durch Gates geschützt. Genau **ein** Messwerkzeug muss inhaltlich geändert werden: die Fremdbestands-Vorprüfung in `98b-sprachfaelle.sh` misst einen Antwortdeckel statt des Bestands und kann die Schwelle 64 deshalb nie erreichen. Neu zu bauen ist nur die Wiederaufwärm-Messung für die Entladung.

Die Bauordnung ergibt sich zwingend: Backend-Parameter vor PHP-Oberfläche, Entladung vor der Messphase (sonst misst die eine Box-Anfahrt die Entladung nicht mit), Werkzeugfix vor der Anfahrt (ein Messskript, das während des eigenen Laufs nachgebessert wird, macht jede Zahl daneben unbelegt, so steht es im Bericht vom 10.09.).

---

## Neu gegenüber geändert, auf einen Blick

| Komponente | Status | Datei |
|---|---|---|
| Request-Feld `types` und `sort` | **geändert** | `backend/src/findling/api/search.py` (`SearchRequest`) |
| Filter aus dem Request statt nur aus dem Text | **geändert** | `backend/src/findling/query/rewrite.py` (`build_query`) |
| Sortierzweig im Kandidatenlauf | **geändert** | `backend/src/findling/index/search.py` (`candidates`, `_sides`, `_ranked`) |
| Sortier-Konstanten und Grenzen | **geändert** | `backend/src/findling/config.py` |
| Filter im Auszugspfad in Gleichschritt | **geändert** | `backend/src/findling/api/snippets.py` (`SnippetsRequest`, `excerpts`) |
| Filter und Sortierung im Seitenzustand | **geändert** | `php/lib/Controller/PageController.php` |
| Durchreichen an den Container | **geändert** | `php/lib/Service/ExAppService.php` (`searchCandidates`, `snippets`) |
| Signatur des einen Suchlaufs | **geändert** | `php/lib/Service/SearchService.php` (`run`) |
| Filterleiste und Sortierwahl | **geändert** | `php/templates/search.php`, `php/css/search.css` |
| Neue sichtbare Texte | **geändert** | `php/l10n/{de,de_DE,fr}.{json,js}` (sechs Dateien, vier Gates) |
| Unified-Search-Dialog | **unverändert** | `php/lib/Search/Provider.php` (bewusst, siehe A.6) |
| Freigabe der Gewichte | **NEU** | `EmbeddingModel.release()` in `backend/src/findling/embed/model.py` |
| Leerlauf-Uhr des Modells | **NEU** | `EmbeddingModel._last_use` / `last_use` in derselben Datei |
| Freigabe am Halter | **NEU** | `release_if_idle()` in `backend/src/findling/embed/engine.py` |
| Freigabe des Cutters | **NEU** | `Poller.release_the_cutter()` in `backend/src/findling/worker/poller.py` |
| Aufräumer-Aufgabe | **NEU** | Task im Lifespan von `backend/src/findling/main.py` |
| Zustand und Zähler für die Admin-Sicht | **geändert** | `backend/src/findling/api/status.py`, `php/lib/Service/AdminViewService.php`, `php/templates/admin.php`, `php/js/admin.js` |
| Fremdbestands-Messgröße | **geändert (neue Datei, alte bleibt byteidentisch)** | neues `docs/measurements/<lauf>/skripte/98c-sprachfaelle.sh` |
| Wiederaufwärm-Messung | **NEU** | `docs/measurements/<lauf>/skripte/*-wiederaufwaermen.sh` |
| Wiederaufbau-Runbook | **NEU** | `docs/measurements/<lauf>/skripte/00-ablauf.md` plus `docs/runbook-messbox.md` |

---

## Systemüberblick mit den v1.2-Eingriffspunkten

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Nextcloud (PHP)                                                          │
│  ┌──────────────────┐    ┌──────────────────────┐   ┌─────────────────┐  │
│  │ Search/Provider  │    │ Controller/Page      │   │ Settings/Admin  │  │
│  │ (Dialog)         │    │ (eigene Seite) [A]   │   │ (Statusseite)[B]│  │
│  └────────┬─────────┘    └──────────┬───────────┘   └────────┬────────┘  │
│           └──────────────┬──────────┘                        │           │
│                  ┌───────▼─────────┐                         │           │
│                  │ SearchService   │  einzige Rechtegrenze    │           │
│                  │ run() [A]       │  getFirstNodeById +      │           │
│                  └───────┬─────────┘  isReadable              │           │
│                  ┌───────▼─────────┐                 ┌────────▼────────┐  │
│                  │ ExAppService[A] │                 │ AdminViewSvc[B] │  │
│                  └───────┬─────────┘                 └────────┬────────┘  │
└──────────────────────────┼────────────────────────────────────┼──────────┘
                  exAppRequest (AppAPI, signiert)               │
┌──────────────────────────┼────────────────────────────────────┼──────────┐
│ Container (Python)       │                                    │          │
│  ┌───────────────────────▼──────────┐  ┌──────────────────────▼───────┐  │
│  │ api/search.py  api/snippets.py[A]│  │ api/status.py  [B]           │  │
│  └───────────┬──────────────────────┘  └──────────────┬───────────────┘  │
│  ┌───────────▼──────────┐  ┌────────────────────┐     │                  │
│  │ query/rewrite.py [A] │  │ api/resources.py   │     │                  │
│  └───────────┬──────────┘  │ read_side(), Cache │     │                  │
│  ┌───────────▼───────────────────────────────┐  │     │                  │
│  │ index/search.py::candidates [A]           │  │     │                  │
│  │  RRF-Fenster + ACL-Vorfilter + Nachlauf   │  │     │                  │
│  └───┬──────────────────────┬────────────────┘  │     │                  │
│      │                      │                   │     │                  │
│  ┌───▼──────┐  ┌────────────▼───┐  ┌────────────▼─────▼───────────────┐  │
│  │ tantivy  │  │ store/repo.py  │  │ embed/engine.py  Halter      [C] │  │
│  │ Index    │  │ ACL-Vorfilter  │  │ embed/model.py   Gewichte    [C] │  │
│  └──────────┘  └────────────────┘  └──────────────▲───────────────────┘  │
│  ┌──────────────────────────────────────────────┐ │                      │
│  │ worker/poller.py  zweite Spur, _chunker  [C] ├─┘                      │
│  └──────────────────────────────────────────────┘                        │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ main.py  Lifespan: Poller-Task, Reconcile-Task, NEU Reaper   [C] │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘

[A] Dateityp-Filter und Sortierung   [B] Sichtbarkeit der Entladung   [C] Entladung
```

---

## Teil A: Dateityp-Filter und Sortierung

### A.1 Was schon da ist, und warum das die halbe Antwort ist

| Baustein | Datei | Zustand |
|---|---|---|
| Feld `ext`, ein Term, `raw`-Tokenizer, `basic` | `backend/src/findling/index/schema.py:105` | vorhanden seit v1.0, **kein Reindex nötig** |
| Befüllung der Endung, kleingeschrieben, ohne Punkt | `backend/src/findling/extract/dispatch.py:161` (`extension_of`), `worker/poller.py:2111` | vorhanden |
| `type:pdf` aus dem Suchtext schneiden | `backend/src/findling/query/rewrite.py:185` (`extract_filters`) | vorhanden |
| Pflichtklausel auf `ext` an die Query hängen | `backend/src/findling/query/rewrite.py:292` (`_extension_query`), `:374` | vorhanden |
| Feld `mtime`, `fast=True`, `indexed=False` | `backend/src/findling/index/schema.py:114` | vorhanden, Kommentar dort sagt wörtlich "Display today, sorting and since/until later" |
| `mtime` reist bereits im Kandidaten mit | `backend/src/findling/index/search.py:92`, `api/search.py:110` | vorhanden |

**Das Schema trägt beides schon.** Der Ausbau kostet keinen Reindex und fällt damit nicht unter den Migrationsmerker, den v1.1 gelernt hat. Die Indexmarken bleiben unverändert, `SCHEMA_VERSION` in `config.py` bleibt stehen.

### A.2 Der Filter: eigenes Request-Feld statt `type:` im Text

Naheliegend wäre, die Filterleiste der Seite einfach `type:pdf` in den Suchtext zu hängen. **Das ist die falsche Lösung, und der Grund steht im Code.**

`query/rewrite.py:130` (`carried_operators`) vergibt die Marke `FILETYPE`, sobald ein Token mit `type:` beginnt. `api/search.py:230` liest das:

```python
lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only
```

Ein Filter aus dem Text schaltet also für **jede** gefilterte Suche die semantische Hälfte ab. Für den Tipp-Profi, der `type:pdf` selbst schreibt, ist das die dokumentierte und begründete Entscheidung ("eine Zeile mit einem Dateityp ist eine Bitte um Genauigkeit"). Für einen Klick auf eine Filterschaltfläche ist es etwas anderes: der Nutzer hat die Trefferart eingeschränkt und nicht um lexikalische Exaktheit gebeten. Ein Klick, der die Semantik still abschaltet, ist genau die Art unsichtbarer Verschlechterung, die dieses Projekt sonst überall vermeidet.

**Empfehlung:** ein eigenes Feld auf dem Request.

- `backend/src/findling/api/search.py`, `SearchRequest`: `types: list[str] = Field(default_factory=list, max_length=SEARCH_TYPES_MAX)`. camelCase ist hier nicht nötig, der Name ist neu und wird auf beiden Seiten gleich geschrieben; `extra="forbid"` bleibt und schützt weiter gegen untergeschobene Identitäten.
- Validierung der Werte im Modell, nicht im Aufrufer: kleingeschrieben, führender Punkt entfernt, nur `[a-z0-9]{1,16}`, Duplikate raus, Deckel auf etwa acht Einträge. Alles andere fällt weg statt den Request scheitern zu lassen (Präzedenz: `PageController` klemmt statt zu verweigern).
- `backend/src/findling/query/rewrite.py`, `build_query(index, text, *, title_only=False, extensions=())`: die übergebenen Endungen werden mit den aus dem Text geschnittenen **vereinigt** (`dict.fromkeys` wie schon in `extract_filters`), und `carried_operators` bleibt unverändert, weil es weiter nur den Rohtext liest. Damit gilt: Filter aus dem Text = Bitte um Genauigkeit = lexikalisch; Filter aus der Leiste = Einschränkung der Trefferart = Hybrid bleibt an. Diese Unterscheidung ist der eine Satz, der in den Docstring von `build_query` gehört.
- `backend/src/findling/api/snippets.py`, `SnippetsRequest` und `excerpts`: dasselbe Feld, weitergereicht an dasselbe `build_query`. Notwendig ist es nicht für die Korrektheit des Auszugs (der Dokumentensatz ist dort bereits bestätigt), aber der Gleichschritt der beiden Aufrufe ist im Repo eine harte Regel; ein Query-Bau, der auf zwei Wegen unterschiedlich parametrisiert wird, ist der klassische Ort für stille Drift.

**Was ausdrücklich nicht gebaut wird:** eine Facettenzählung ("PDF (23), DOCX (4)"). Eine Zahl vor dem Rechte-Recheck ist eine Aussage über Dokumente anderer Leute, genau das Zähl-Orakel aus T-02-93, gegen das `CandidatePage` bewusst kein Total trägt. Die Filterleiste zeigt feste Gruppen ohne Zahlen.

### A.3 Die Sortierung: sie muss unter den Vorfilter, nicht über ihn

Die Versuchung ist, auf der PHP-Seite die 25 bestätigten Treffer zu sortieren. Das ergäbe "innerhalb der Seite sortiert", also eine Liste, deren zweite Seite wieder ältere und neuere Dokumente mischt. Sortierung ist eine Eigenschaft der **Rangliste**, und die Rangliste entsteht in `index/search.py::candidates`, oberhalb des ACL-Vorfilters (`_permit`) und lange vor dem PHP-Recheck.

Die Reihenfolge ist auch der einzige Kanal, der überlebt: `ExAppService::filterCandidates` wirft alles außer `fileId` weg, `SearchService::run` hängt die genehmigten Treffer in Ankunftsreihenfolge an, `PageController::rows` iteriert sie unverändert. Ein `score`-Feld im Kandidaten ist für die Anzeige belanglos. **Wer die Reihenfolge im Container setzt, setzt die Reihenfolge auf dem Schirm.**

**Umfang für v1.2: zwei Sortierungen, nicht vier.**

| Sortierung | Machbar ohne Reindex | Empfehlung |
|---|---|---|
| Relevanz (heute) | ja | Standard, unverändert |
| Datum absteigend / aufsteigend | ja, `mtime` ist Fast-Field | **bauen** |
| Name | nein, kein Fast-Text-Feld im Schema, verlangt Schemaänderung und Reindex | **nicht in v1.2** |
| Größe | nein, Größe steht gar nicht im Index | **nicht in v1.2** |

Die Namenssortierung wäre ein Reindex auf Bestandsinstallationen, also genau die Strafe, die D-04 für Minor-Sprünge ausschließt. Sie gehört in den Backlog mit dem Vermerk "kostet ein Fast-Feld im Schema und damit `SCHEMA_VERSION`".

**Der Sortierzweig in `candidates()`.** Heute läuft die Funktion in zwei Abschnitten: das Fusionsfenster (RRF über lexikalische und semantische Liste) und der Nachlauf hinter dem Fenster (rein lexikalisch, Rang wird fortgezählt). Unter Datumssortierung gilt:

- Im Fenster: die **Vereinigung** beider Listen wird nicht per RRF geordnet, sondern nach `mtime` sortiert. Die Zeitstempel liegen für beide Seiten bereits vor: die lexikalischen aus `_ranked`, die nur semantisch gefundenen aus `_mtimes_of` (`index/search.py:323`), das für genau diesen Zweck schon existiert. **Die semantische Hälfte bleibt also auch bei Datumssortierung Teil der Treffermenge.** Das ist wichtig: hätte man sie abgeschaltet, würde ein Umschalten der Sortierung Treffer verschwinden lassen statt sie umzuordnen, und das ist für einen Nutzer nicht erklärbar.
- Im Nachlauf: `searcher.search(query, chunk_limit, offset=raw_cursor, order_by_field=FIELD_MTIME, order=Order.Desc)`. Die Ordnung ist monoton, der Nachlauf hängt also sauber hinter dem Fenster an, sofern die Fenstergrenze mitgeführt wird (der älteste im Fenster ausgelieferte Zeitstempel ist die Untergrenze des Nachlaufs). Bei aufsteigender Sortierung dreht sich das um.
- **VERIFIZIEREN vor dem Bau:** unter `order_by_field` liefert tantivy-py im Trefferpaar den **Feldwert** statt des Scores (`hits: list[tuple[Any, DocAddress]]` im Stub `backend/.venv/Lib/site-packages/tantivy/tantivy.pyi:386`). `_ranked` (`index/search.py:142`) packt dieses erste Element heute ungeprüft in `score`. Das ist funktional harmlos, weil der Score nirgends angezeigt wird, aber es gehört in einen Test statt in eine Annahme. Zweitens ist zu prüfen, ob `order_by_field` zusammen mit `offset` in 0.26.0 dieselbe stabile Ordnung liefert; falls nicht, ist der Nachlauf über einen Bereichsfilter auf `mtime` statt über `offset` zu fahren.

**Der Vorfilter bleibt, wo er ist.** `_permit` wird weiter bandweise auf die geordnete Liste angewendet, `_PREFILTER_BAND` bleibt 128, die Kommentarregel ("ein Test greppt diese Datei nach dem Namen des Vorfilters und erwartet ihn genau zweimal") gilt unverändert. Der Sortierzweig darf keinen dritten Aufrufer des Vorfilters erzeugen.

### A.4 Cursor-Semantik: was trägt und was bricht

Das Paginierungsmodell der Seite ist ein **Cursorpfad**: `cursors=0.25.57` sind die Container-Offsets, an denen jede bisher gezeigte Seite begann (`PageController::cursorPath`, `:274`). Der Offset zählt genehmigte Kandidaten, nie rohe Treffer (`index/search.py`, Modulkopf).

Das trägt für Filter und Sortierung **unverändert**, solange gilt: der Cursorpfad ist nur innerhalb einer festen Kombination aus Suchbegriff, `names`, `types` und `sort` gültig. Daraus folgen drei Regeln, die in den Controller gehören:

1. **Jede Änderung an Filter oder Sortierung springt auf Seite eins.** Das Formular trägt schon heute weder `page` noch `cursors` (`templates/search.php:142`), eine Filterleiste als Teil desselben Formulars erbt dieses Verhalten geschenkt. Eine Filterleiste als separater Link-Satz muss `page` und `cursors` aktiv weglassen.
2. **`pageUrl()` muss die neuen Werte mitführen**, genau wie heute `names` (`PageController:455`). Fehlt das, fällt die zweite Seite auf ungefiltert zurück, und zwar lautlos.
3. **Kein zusätzlicher Zustand im Cursor.** Die Versuchung, Filter und Sortierung in den Cursorstring zu kodieren, schafft einen zweiten Parser für eine URL, die schon einen hat. Sie stehen als eigene Query-Parameter daneben und werden wie `names` defensiv gelesen: was nicht zur geschlossenen Liste passt, ist nicht gesetzt, ohne Meldung (`PageController` Klassendoc, "ein Filter, der nicht das eine Wort ist, das diese Seite kennt, ist nicht gesetzt").

**Was tatsächlich teurer wird:** ein enger Filter senkt die Trefferdichte pro Kandidatenseite. Die Ausbeute-Schleife in `SearchService::run` hat drei Runden (`MAX_ROUNDS`) und ein Recheck-Budget (`pageSize * recheckPerHit`, gedeckelt auf 64). Bei `type:xlsx` auf einem Bestand voller PDFs kann eine Seite leer zurückkommen, obwohl es Treffer gibt. Das ist **kein neuer Fehler**, sondern DI-07-03 unter Last, und die Seite hat dafür bereits den ehrlichen Text (`FAILURE_ALL_CANDIDATES_REJECTED`). Der Filter wirkt jedoch **im Container**, vor dem Fenster, nicht im PHP: die Klausel auf `ext` ist Teil der Query, also enthält eine Kandidatenseite bereits nur passende Dateitypen. Damit verschiebt der Filter die Trefferdichte in die richtige Richtung, nicht in die falsche. Das gehört als Satz in den Plan, weil die intuitive Sorge genau andersherum lautet.

### A.5 Die PHP-Kette, Datei für Datei

```
GET /apps/findling/?query=...&names=1&types=pdf,docx&sort=date_desc&page=2&cursors=0.25
        │
PageController::index()                       [geaendert]
   term(), pageNumber(), cursorPath()           unveraendert
   NEU: types(), sortOrder()                    defensiv, geschlossene Listen
   caps()                                       unveraendert (SearchCaps bleibt Ceilings-only)
        │
SearchService::run($user,$term,$titleOnly,$startCursor,$caps)   [Signatur geaendert]
   NEU: ein Wert-Objekt SearchQueryShape($titleOnly,$types,$sort)
   Rechtekette unveraendert: getFirstNodeById + isReadable, genau ein Aufrufort
        │
ExAppService::searchCandidates(...)           [geaendert: zwei Felder mehr im Body]
ExAppService::snippets(...)                   [geaendert: types mit]
        │
POST /search  {query, limit, offset, titleOnly, types, sort}
```

**Zur Signatur von `SearchService::run`:** heute fünf Argumente, davon `bool $titleOnly`. Zwei weitere Skalare anzuhängen macht die Aufrufstelle unlesbar, und `SearchCaps` ist der falsche Ort dafür (dessen Klassendoc sagt ausdrücklich, es sei die Sammlung der **Deckel** eines Laufs, und jeder Wert darin ist eine Geduldsaussage des Aufrufers). Empfehlung: ein zweites kleines Wert-Objekt neben `SearchCaps`, etwa `SearchShape` mit `titleOnly`, `types`, `sort`, im selben Stil (`final class`, `readonly`, keine Defaults). Es wird an beiden Aufrufstellen ausgeschrieben, `Provider.php` übergibt die Standardform.

**Gates, die dabei anschlagen:**

- `backend/tests/test_php_acl_boundary.py` zählt die Aufrufstellen von `getFirstNodeById` und `isReadable` über `php/lib` mit entfernten Kommentaren und Zeichenketten. Solange nichts an der Schleife angefasst wird, bleibt es grün; eine "schnelle Vorsortierung" mit einer zweiten Knotenauflösung wäre sofort rot, und das ist gewollt.
- `backend/tests/test_php_trust_boundary.py` zählt die Routenattribute pro Controller-Datei. Es kommt **keine neue Route** hinzu, `index()` bekommt nur mehr Parameter. Das Anti-Leerlauf-Kriterium dieses Gates (Attributnamen dürfen nicht im Prosakommentar stehen) gilt für jeden neuen Kommentar in `PageController`.
- `backend/tests/test_search_limits_lockstep.py` hält `SearchService::MAX_CONTAINER_OFFSET = 1200` gegen `SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS` in `config.py`. Wer wegen dünnerer Trefferdichte die Rundenzahl anheben will, bewegt beide Seiten oder das Gate wird rot. Empfehlung: **nicht anheben**, der Deckel ist ein Sicherheitsargument.
- `backend/tests/test_admin_ui_contract.py` prüft Template und Skript auf Bindestriche, Emojis, unescapte Ausgabe, im Skript gebautes Markup. Die Filterleiste ist reines Server-Markup in `templates/search.php`; `php/js/search.js` bleibt unangetastet (es darf weiterhin nicht pollen, nichts abfangen, kein Markup bauen).
- Die Katalog-Gates: jeder neue sichtbare Text braucht Einträge in `php/l10n/de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js`. Sechs Dateien, kein Extraktor, von Hand. Für Französisch gilt die Owner-Abnahme aus `docs/l10n-french.md`.

### A.6 Der Unified-Search-Dialog bleibt außen vor

`Provider::getSupportedFilters()` meldet heute `BUILTIN_TERM` und `BUILTIN_TITLE_ONLY`. Nextcloud kennt keinen eingebauten Dateityp-Filter, ein eigener braucht `getCustomFilters()` mit einer `FilterDefinition`, und der Kommentar im Code warnt zu Recht: ein Name ohne Definition macht die ganze Providerliste zum Fehler, ein nicht deklarierter Filter lässt den Provider wortlos überspringen. Ein eigener Filter erschiene außerdem global in der Suchleiste, auch für andere Provider.

**Empfehlung: `Provider.php` in v1.2 nicht anfassen.** Die Brücke ist der ohnehin vorhandene Eintrittspunkt am Ende der Trefferliste (`Provider::entryPoint`, `:326`), der bereits `query` und `names` an die Seite weiterreicht. Filter und Sortierung sind Eigenschaften der eigenen Ergebnisseite, und genau das ist der Grund, warum es diese Seite gibt.

### A.7 Datenfluss vorher und nachher

```
vorher:   Text ──► carried_operators ──► build_query ──► Query
                                             │
                       type:-Praefix ────────┘ (schaltet Semantik ab)

nachher:  Text ──► carried_operators ──► build_query(extensions=types) ──► Query
            │                                 ▲
            │      type:-Praefix ─────────────┤ (schaltet Semantik weiter ab, Profipfad)
            └──── Leiste ──► types ───────────┘ (Semantik bleibt an)

candidates(..., sort=relevance)  ──►  RRF-Fenster ──► Vorfilter ──► lexikalischer Nachlauf
candidates(..., sort=date_desc)  ──►  Vereinigung nach mtime ──► Vorfilter ──► order_by_field-Nachlauf
```

---

## Teil B: Modell-Entladung im Leerlauf

### B.1 Wer hält heute was

| Halter | Inhalt | Gemessenes Gewicht | Datei |
|---|---|---|---|
| `embed/engine.py::_ENGINE` | die eine `EmbeddingModel`-Hülle (Pfad plus Objekt) | winzig, hält aber alles darunter | `engine.py:70` |
| `EmbeddingModel._engine` (`_Engine`) | onnxruntime-Session **plus** truncating/padding-Tokenizer | Gewichte 118 MB, Aktivierungsspitze 250 bis 400 MB | `model.py:319`, `:276` |
| `Poller._chunker` (Closure) | zweiter Tokenizer plus `semantic-text-splitter` | **544,3 MB Spitze**, faul gebaut seit Plan 07-03 | `poller.py:1615`, RAM-Tabelle in `CLAUDE.md` |
| `Poller._model` | Referenz auf dieselbe `EmbeddingModel` | keine eigene Last | `poller.py:1657` |

**Das ist der wichtigste Befund dieses Teils.** Der große Posten ist nicht das Modell, sondern die Tokenizer-Materialisierung, und sie existiert zweimal: einmal als Session-Encoder in `_Engine`, einmal als Cutter-Tokenizer im Poller. Eine Entladung, die nur `EmbeddingModel._engine` freigibt, lässt den größeren Teil stehen. Die Belege stehen in `docs/measurements/2026-09-grundlast-fein/` und in `docs/measurements/2026-09-vergleichsmessung-m7g/`, Abschnitt 5.2.

**VERIFIZIEREN:** wie viel von den 103,2 MB Grundlast nach v1.1 überhaupt auf Modell und Cutter entfällt. Nach der faulen Bauweise seit 07-03 ist die Grundlast **eines frisch gestarteten Containers** bereits ohne beides gemessen worden. Der Gewinn der Entladung ist also nicht "Grundlast minus X", sondern "Rückkehr zur Grundlast nach einem Indexlauf". Das ist eine andere Messgröße und die Messphase muss sie so benennen, sonst verspricht der Store-Text eine Zahl, die nicht die gemessene ist.

### B.2 Wohin die Freigabe gehört

Drei Ebenen, drei Verantwortungen, und die bestehende Abhängigkeitsrichtung bleibt unangetastet (`worker/` importiert aus `embed/`, `api/` importiert aus `embed/`, `embed/` kennt keinen von beiden, `main.py` kennt alle):

1. **`embed/model.py`, `EmbeddingModel.release() -> bool`.** Setzt `self._engine = None` unter `self._lock` und meldet, ob wirklich etwas freigegeben wurde. **Was dabei stehen bleiben muss:** `_absent` (Eigenschaft der Installation), `_load_failed_at` (Eigenschaft des Moments, deren Cooldown weiterläuft), `_run_failure_warned` (Log-Dämpfung). Eine Freigabe ist kein Neustart des Objekts, und `reset()` in `engine.py` bleibt das, was es ist: ein Werkzeug für Tests und `one_load.py`.
2. **`embed/engine.py`, `release_if_idle(seconds) -> bool`.** Liest den Halter ohne ihn zu füllen (`_held`, `:236`, existiert schon genau dafür), fragt die Leerlauf-Uhr des Modells und ruft `release()`. Zählt die Freigaben in einem Modulzähler neben `_LOAD_COUNT`-Vorbild, damit die Admin-Sicht eine Zahl hat.
3. **`worker/poller.py`, `Poller.release_the_cutter() -> bool`.** Setzt `self._chunker = None` und `self._model = None`. `_build_the_cutter` baut beim nächsten Dokument neu, weil seine erste Zeile genau dieses Paar prüft (`:1606`). `_cutter_absent` und `_cutter_failed_at` bleiben stehen, aus demselben Grund wie oben. Wichtig ist die Bedingung "die drei reisen zusammen oder keiner von ihnen" aus dem Kommentar bei `:1653`: die Freigabe muss beide Felder setzen, nie nur eines.

### B.3 Der Auslöser: eine eigene Aufgabe im Lifespan

Der naheliegende Ort wäre der Leerlaufzweig des Pollers (`run_once`, `ROUND_EMPTY`, `poller.py:614`). **Das ist falsch, und zwar aus einem konkreten Grund:** ein stummgeschalteter Poller (`silence()`) wartet in `run()` auf `self._armed` und betritt `run_once` nie wieder (`poller.py:543`). Genau dieser Container, der nicht indexiert und nur gelegentlich durchsucht wird, ist der Fall, für den die Entladung gebaut wird.

**Empfehlung:** eine dritte Aufgabe im Lifespan von `main.py`, neben `indexing` und `repairing` (`main.py:308`, `:319`), mit demselben Muster: `asyncio.create_task`, eigenes `stop_event`, im Shutdown-Block mit `wait_for(shield(...))` eingesammelt. Ein grober Takt von etwa 60 Sekunden reicht, die Aufgabe darf nichts öffnen und nichts laden; sie liest zwei Uhren und ruft im Zweifel zwei Freigaben.

`main.py` ist die einzige Datei, die beide Hälften kennen darf, sie verdrahtet sie ohnehin (`_POLLER`, `resources`). Damit muss weder `embed/` vom Poller wissen noch `worker/` von einem Aufräumer.

**Die Uhr.** Ein Zeitstempel, ein Schreiber: `EmbeddingModel._last_use = time.monotonic()` am Ende jedes erfolgreichen `_embed`, egal ob Passage oder Query. Damit deckt eine einzige Uhr beide Nutzer ab, und es entsteht keine zweite Meinung darüber, was "benutzt" heißt. Präzedenz im Repo ist `note_cutter_failure`: ein Wert, ein Schreiber, ein Leser.

**Die zweite Bedingung.** Freigegeben wird nur, wenn der Poller gerade nichts in Arbeit hat. Sonst entlädt der Aufräumer mitten in einer Charge und der nächste Stapel baut alles neu auf, wieder und wieder. Der Poller hat den Zustand bereits: `self._held` ist zwischen Anspruch und Verdikt gefüllt. Eine schmale Nur-Lese-Eigenschaft (`Poller.busy`) genügt, und sie ist billiger und ehrlicher als ein Mitzählen im Modell.

**Die Schwelle** gehört nach `config.py` in der dortigen Form: Konstante mit Begründung, Bereich, Umgebungsvariable, zum Beispiel `EMBED_IDLE_RELEASE_SECONDS = 900` mit `FINDLING_EMBED_IDLE_RELEASE_SECONDS` und `0` als "aus". Ein Abschaltwert ist Pflicht: er ist die Rückfallebene, wenn die Messphase zeigt, dass das Wiederaufwärmen teurer ist als der Gewinn.

### B.4 Threadsicherheit: das Bestehende trägt, und das ist kein Zufall

`EmbeddingModel._embed` (`model.py:406`) holt die Engine unter der Sperre in eine **lokale Variable** und läuft danach außerhalb der Sperre durch die Stapel:

```python
with self._lock:
    engine = self._load()
...
    with self._lock:
        encoded = _encode_batch(engine, window)
    vectors.extend(_run_encoded(engine, encoded))
```

Setzt der Aufräumer gleichzeitig `self._engine = None`, verliert der laufende Aufruf nichts: seine lokale Referenz hält Session und Tokenizer am Leben, bis die Funktion zurückkehrt. **Eine Freigabe kann also keinen laufenden Stapel zerstören, und es braucht keinen Umbau der Sperrenarchitektur.** Sie kann nur eines: nichts bewirken, solange noch jemand arbeitet. Genau deshalb ist die Leerlauf-Uhr die richtige Steuergröße und nicht ein Nutzungszähler mit Wartebedingung.

Zwei Feinheiten gehören trotzdem in den Plan:

- Die Suche läuft über `asyncio.to_thread` (`api/search.py:260`), der Poller ebenfalls; der Aufräumer läuft auf dem Event-Loop. `release()` selbst nimmt nur die Sperre und setzt ein Feld, das ist mikroskopisch und darf auf dem Loop passieren. Die eigentliche Freigabe des Speichers geschieht beim Fallenlassen der letzten Referenz, also im Zweifel im Destruktor von onnxruntime, und das kann messbar dauern. Wenn die Messung das zeigt: `release()` in `asyncio.to_thread` verlagern, nicht die Sperre verbreitern.
- `enable_cpu_mem_arena=False` ist bereits gesetzt (`model.py:272`). Das ist die Voraussetzung dafür, dass eine Freigabe dem Betriebssystem überhaupt etwas zurückgibt, und der Kommentar dort begründet es schon für die Aktivierungsspitze. Der Satz gilt für die Entladung doppelt und sollte dort ergänzt werden.

### B.5 Wechselwirkung mit dem Ein-Ladung-pro-Prozess-Gate

`embed/model.py::_LOAD_COUNT` und `tools/one_load.py` belegen die Zusage von Plan 06.1-02: **eine Ladung pro Prozess**. Mit der Entladung wird diese Zusage wörtlich falsch, und das muss bewusst und sichtbar geschehen, nicht als Nebenwirkung:

- `backend/src/findling/tools/one_load.py` und `backend/tests/test_one_load.py`: die Aussage wird zu "eine Ladung pro Prozess **ohne zwischenzeitliche Freigabe**". Der Zähler bleibt monoton (der Kommentar in `engine.py::reset` verteidigt das zu Recht), aber der Beweis braucht die zusätzliche Bedingung.
- `backend/tests/test_embed_engine.py` und `test_embed_model.py`: neue Fälle für Freigabe im Leerlauf, Freigabe bei laufender Arbeit (darf nichts kaputtmachen), Nachladen nach Freigabe, Erhalt von `_absent` und `_load_failed_at` über eine Freigabe hinweg.
- `backend/tests/test_lifecycle.py`: die dritte Aufgabe muss im Shutdown eingesammelt werden wie die anderen beiden.

### B.6 Sichtbarkeit für den Admin

Heute: `engineState` aus `embed/engine.py` mit fünf Wörtern (`loaded`, `cold`, `disabled`, `missing`, `waiting_for_retry`), gespiegelt in `php/lib/Service/AdminViewService.php:177`, sechs Sätze in `php/templates/admin.php:66` und dieselben sechs in `php/js/admin.js`, zusammengehalten von `backend/tests/test_admin_ui_contract.py` (`test_both_halves_of_the_page_map_the_same_state_to_the_same_sentence`, `test_the_six_sentences_of_the_engine_line_are_in_the_german_catalogue`).

Zwei Wege, und die Empfehlung ist der erste:

**Empfohlen: ein sechstes Wort `unloaded`.** Der Milestone verlangt ausdrücklich, die Wiederaufwärm-Kosten zu "messen und auszuweisen". Ausweisen heißt: der Admin sieht den Unterschied zwischen "noch nie gelesen" (`cold`) und "zum Sparen freigegeben, die nächste Suche kostet das Nachladen". Beide Sätze sind wahr, aber sie sagen einem Admin Verschiedenes. Kosten: `ENGINE_STATES` in `engine.py`, `ENGINE_STATES` in `AdminViewService.php`, ein Satz in `admin.php`, derselbe Satz in `js/admin.js`, sechs Katalogdateien, dazu die Gate-Erwartung "sechs Sätze" wird "sieben".

**Fallback: bei fünf Wörtern bleiben**, nach der Freigabe wieder `cold` melden und stattdessen zwei Zahlen in `api/status.py` ergänzen (`modelReleases`, `lastRewarmMs`). Billiger, aber die Statuszeile verschweigt genau die Eigenschaft, die v1.2 neu einführt.

In beiden Fällen gilt die harte Regel aus dem Kopf von `api/status.py`: **die Statusabfrage baut und lädt nichts.** `engine_state()` liest den Halter ohne ihn zu füllen, und eine neue Zahl darf daran nichts ändern; die Admin-Seite pollt alle fünf Sekunden.

### B.7 Was bei der Entladung ausdrücklich nicht angefasst wird

- Der Vektorbestand (`store/vectors.py`) und dessen Lese-Handle in `api/resources.py::ReadSide.vectors`. Er ist SQLite auf Platte, er ist nicht die Last, und ein Schließen würde nur die nächste Suche verteuern.
- Der tantivy-Reader (`open_reader`, einmal pro Index konfiguriert, 0,10 ms gegen 0,005 ms pro Suche). Der Index liegt im Page-Cache, nicht im Heap.
- Die Wortliste und das 23-MB-Automat aus `index/wordlist.py`. Sie gehört zur lexikalischen Suche, also zu dem Teil, der immer antworten muss.
- `EmbeddingModel` als Objekt. Freigegeben wird `_engine`, nie die Hülle; sonst verliert man die drei Merker und die Suche fängt an, eine Installation ohne Modell wieder und wieder zu befragen.

---

## Teil C: Was die Messphase wiederverwendet

### C.1 Bestand und Änderungsbedarf

| Artefakt | Zustand nach v1.1 | Verwendung in v1.2 | Änderung |
|---|---|---|---|
| `scripts/ops/search_load.py` | gefixt und am 10.09. belegt (`min_hits`, `hits_per_request`, `EmptyResultGroup`) | Laststufen 1/4/8/12/16, Untersuchung der vier regressiven Stufen | **keine.** Wird byteidentisch auf die Box gebracht, wie am 10.09. |
| `scripts/ops/aws_box.sh` | acht Unterbefehle, `start` zieht die SSH-Regel nach, `snapshot` mit eigenem Tag `findling-corpus-keep` | Wiederanfahrt aus `snap-03f1d1d9ad9262704`, Kosten, Abbau | **klein:** ein Unterbefehl oder Abschnitt, der ein Volume **aus** einem Snapshot erzeugt. `volume` legt heute ein leeres an. Das ist die eine Lücke im Wiederaufbau. |
| `scripts/ops/rss_sampler.sh`, `rss_digest.py` | cgroup-Abtastung, beide Treiberlayouts | Grundlast, Volllauf, Entladungs-Nachweis | **keine** |
| `docs/measurements/.../skripte/96-volllauf.sh`, `96b-waechter.sh`, `96c-lesen.py`, `96d-statusbeobachter.py`, `96e-ntfy-watch.sh` | gefahren am 10.09. | Wirkungsbeleg-Volllauf DI-10-04 | **kopieren in neues Laufverzeichnis**, nicht editieren (siehe C.3) |
| `docs/measurements/.../skripte/97-nebenlaeufigkeit.sh` | gefahren | vier regressive Laststufen | kopieren, Stufenliste anpassen |
| `.../2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh` | gefahren, **Fix greift nicht** | Sprachfall-Messung DI-10-02/DI-11-01 | **inhaltliche Änderung nötig**, siehe C.2 |
| `.../skripte/00-ablauf.md` (beide Läufe) | Muster: Ablauf plus vorher notierte Erwartung E1..En | Runbook-Erstvollzug | **Vorlage**, neue Datei je Anfahrt |
| `.../skripte/40b-baumhash.py/.sh` | Baumhash der beiden Hälften, per Test reproduziert | Beweis, dass die Box den Repo-Stand trägt | **keine** |
| `docs/performance.md` | trägt die Nachmessungs-Zusage (acht gleichzeitige Suchen) | wird von den neuen Zahlen fortgeschrieben | Text |
| `README.en.md` plus beide `info.xml` | eine Messzahl an drei Stellen | falls die Entladung die ausgewiesene Zahl bewegt | drei Stellen im Gleichschritt, Store-Regel |

### C.2 Die eine echte Werkzeugänderung: die Fremdbestands-Messgröße

Der Bericht vom 10.09. (`docs/measurements/2026-09-werkzeugfixe/README.md`, Abschnitt 4) hat es sauber gemessen und benannt: die Vorprüfung fragt dieselbe OCS-Route, und die antwortet dem Lasttest-Konto für **jeden** Begriff exakt 26 Treffer bei Tiefe 64, 200 und 2000. Die Größe hängt weder am Begriff noch an der Tiefe, sie ist ein Deckel der Antwort. Damit kann sie die Schwelle 64 nie erreichen, das dreiwertige Urteil bleibt praktisch zweiwertig, und vier Fälle sind rot, ohne dass das eine Aussage über die deutsche Sprachkette wäre.

Der Bericht nennt die Lösung bereits: **die Zahl der Dokumente im Index, die den Begriff tragen, statt der Zahl der Treffer, die die Route herausgibt.** Dafür gibt es im Container zwei gangbare Quellen:

- `Searcher.doc_freq(field_name, field_value)` aus den tantivy-Bindings (im Stub vorhanden), also die Dokumentfrequenz eines Terms. Nächstliegend, aber sie zählt Terme nach Analyse, nicht Dokumente nach Suchzeile.
- Die Diagnose-Route `backend/src/findling/api/diagnose.py` mit `ranked_sides` (`index/search.py:296`), die ausdrücklich **ohne** Vorfilter arbeitet und für genau solche Admin-Fragen gebaut ist.

Die zweite ist die richtige: sie geht durch denselben Query-Bau wie die Suche, sie ist bereits als Admin-Frage begründet, und sie liefert die Rangliste, in der das eigene Dokument stehen müsste. **Empfehlung:** die Nachfolgefassung heißt `98c-sprachfaelle.sh`, liegt im neuen Laufverzeichnis, und ihre Vorprüfung fragt die Diagnose-Route statt der OCS-Route. Das ist ein eigener Planschritt **vor** der Anfahrt, denn: "ein Messskript, das während seines eigenen Laufs nachgebessert wird, macht jede Zahl daneben unbelegt" (ebenda).

### C.3 Die Byte-Identitäts-Regel

`backend/tests/test_measurement_scripts.py::test_the_driven_language_case_script_stays_byte_identical` pinnt Größe und SHA-256 der am 10.09. gefahrenen Fassung `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh`, und ein zweiter Test beweist, dass der Wächter schon auf ein einzelnes zusätzliches Zeichen anschlägt. Daraus folgt die Arbeitsweise für die ganze Messphase: **gefahrene Skripte werden nie editiert, Nachfolgefassungen bekommen ein neues Laufverzeichnis.** Das gilt auch für `98b`, sobald es gefahren ist. Für jedes neue Skript greifen zusätzlich die Breitengates (`test_the_measurement_script_carries_no_dash`, `no_carriage_return`, `starts_with_a_shebang`, `carries_no_path_of_one_machine`).

### C.4 Neu zu bauen: die Wiederaufwärm-Messung

Für die Entladung fehlt ein Werkzeug, und es ist klein. Gebraucht werden drei Zahlen:

1. Grundlast nach dem Indexlauf, vor der Freigabe (`rss_sampler.sh`, vorhanden).
2. Grundlast nach der Freigabe, wenn der Aufräumer zugeschlagen hat (dasselbe Werkzeug plus die Log-Zeile der Freigabe als Zeitmarke).
3. Die Dauer der **ersten** Suche danach, gegen die Dauer einer Suche im warmen Zustand.

Für Punkt 3 gibt es bereits das Muster: `docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95-nachher-erste-suche.json` ist genau eine solche Einzelmessung, erzeugt aus `search_load.py` mit `--concurrency 1 --rounds 1`. Damit braucht die Wiederaufwärm-Messung kein neues Lastwerkzeug, sondern ein Ablaufskript, das Freigabe erzwingt (Leerlaufschwelle per Umgebungsvariable herabgesetzt) und danach `search_load.py` einmal fährt. Das ist der zweite Grund, warum die Schwelle konfigurierbar sein muss.

### C.5 Das Wiederaufbau-Runbook

Es existiert heute **nicht** als Dokument; es existiert verstreut als Erfahrung in drei Berichten und in den Kommentaren von `aws_box.sh`. Der Erstvollzug ist Teil dieses Milestones. Was hineingehört, ist bereits belegt:

- die drei Fallen der Anfahrtsliste vom 10.09.: der `/etc/hosts`-Pin auf die falsche Apache-Adresse, der von AppAPI nicht gestartete Container (DI-05-36-Heilung), die wechselnde Box-Adresse (`aws_box.sh start` zieht die SSH-Regel selbst nach).
- die Speicherbegrenzung `mem=4G` im Kern und das Zurückmessen vor jedem Lauf (`free -h` sagt 3.9Gi, `nproc` sagt 2, `uname -m` sagt aarch64), aus dem Kopf von `aws_box.sh`.
- das Volume aus dem Snapshot statt leer, die eine fehlende Fähigkeit aus C.1.
- die Abbruchbedingung als prüfbare Zahl. Der Bericht vom 10.09. hält fest, dass `occ findling:index --status` für diese Prüfung untauglich ist (meldet `indexed` bauartbedingt als 0), die Zahl kommt aus der Container-Zählung. Das gehört wörtlich ins Runbook, es hat schon einmal 1,7 Stunden Laufzeit gekostet.
- der Deckel (Owner-Vorschlag 26 h / 3,50 USD) und die Kostenrechnung inklusive der öffentlichen IPv4-Adresse, die in `cmd_prices` bereits als eigene Position geführt wird.

Ablage: `docs/measurements/<neues-laufverzeichnis>/skripte/00-ablauf.md` für die konkrete Anfahrt (Pflicht, Muster vorhanden) und zusätzlich ein beständiges `docs/runbook-messbox.md`, auf das die Ablaufdatei verweist, damit der nächste Milestone nicht wieder in drei Berichten sucht.

---

## Bauvorschlag mit Abhängigkeiten

```
Phase M1  Werkzeug und Runbook (ohne Box)
  ├─ 98c-sprachfaelle.sh: Vorpruefung auf Diagnose-Route umstellen   [DI-10-02]
  ├─ aws_box.sh: Volume aus Snapshot                                  [Wiederaufbau]
  └─ docs/runbook-messbox.md, Erstfassung aus den drei Berichten
        │  (muss vor der Anfahrt fertig sein: Skript nicht waehrend des Laufs fixen)
        ▼
Phase M2  Backend: Filter und Sortierung
  ├─ config.py: SEARCH_TYPES_MAX, Sortierwerte, Grenzen
  ├─ rewrite.py: build_query(..., extensions=)
  ├─ index/search.py: Sortierzweig, _sides/_ranked, order_by_field    [VERIFIZIEREN]
  ├─ api/search.py + api/snippets.py: types, sort
  └─ Tests: test_search_endpoint, test_search_library, test_rrf_fusion,
            test_query_rewrite, test_acl_prefilter
        │  (PHP kann erst danach etwas durchreichen)
        ▼
Phase M3  PHP: Ergebnisseite
  ├─ SearchShape, SearchService::run, ExAppService
  ├─ PageController: types(), sortOrder(), pageUrl()
  ├─ templates/search.php + css, sechs l10n-Dateien
  └─ Gates: acl_boundary, trust_boundary, admin_ui_contract, Kataloge
        ▼
Phase M4  Entladung  (unabhaengig von M2/M3, aber VOR M5)
  ├─ model.py: _last_use, release()
  ├─ engine.py: release_if_idle(), Freigabezaehler, ggf. sechstes Wort
  ├─ poller.py: release_the_cutter(), busy
  ├─ main.py: dritte Lifespan-Aufgabe + Shutdown
  ├─ status.py + AdminViewService + admin.php + js/admin.js + Kataloge
  └─ one_load.py und sein Gate nachziehen
        │  (die Messphase soll die Entladung mitmessen, eine Anfahrt)
        ▼
Phase M5  Messphase, EINE Box-Anfahrt
  ├─ Wiederaufbau aus dem Snapshot, Runbook-Erstvollzug
  ├─ DI-10-04 Wirkungsbeleg-Volllauf
  ├─ vier regressive Laststufen
  ├─ Sprachfaelle mit der neuen Messgroesse
  ├─ Wiederaufwaerm-Kosten der Entladung
  └─ Kosten und Abbau, Snapshot-Entscheid
        ▼
Phase M6  Haertung und Store-Einreichung v1.2.0
  ├─ DI-11-02/03/05/06, BL-F01-Schlusssatz, stable35-Entscheid
  ├─ Messzahl an drei Stellen im Gleichschritt
  └─ Migration Version001200Date... (Merker: jeder Minor-Sprung braucht eine)
```

**Die drei harten Abhängigkeiten:**

1. M2 vor M3. Die Seite kann keinen Parameter senden, den der Container nicht kennt; ein `extra="forbid"`-Modell antwortet mit 422, und das kommt auf der PHP-Seite als "leer" an, also als stumme Suche.
2. M1 vor M5. Belegt durch den Bericht vom 10.09.
3. M4 vor M5. Sonst braucht die Entladung eine zweite Box-Anfahrt, und der Owner-Entscheid vom 11.09. lautet: eine Anfahrt.

M2/M3 und M4 sind gegeneinander unabhängig und könnten getauscht werden. Für die hier vorgeschlagene Reihenfolge spricht, dass der Filter der sichtbare Teil des Milestones ist und die Entladung im schlimmsten Fall per Umgebungsvariable auf Null gestellt ausgeliefert wird, ohne den Milestone zu gefährden.

---

## Anti-Patterns für diesen Milestone

**1. Sortieren auf der PHP-Seite.**
Was naheliegt: `usort` über `$outcome->hits` in `PageController::rows`.
Warum falsch: sortiert nur die 25 Treffer dieser Seite. Seite zwei beginnt wieder mit einem anderen Datumsbereich, und der Nutzer sieht eine Liste, die nirgends sortiert ist. Außerdem wäre die Sortierung im Dialog und auf der Seite verschieden.
Stattdessen: die Reihenfolge entsteht in `index/search.py::candidates`, PHP reicht durch.

**2. Den UI-Filter als `type:`-Text schicken.**
Warum falsch: `carried_operators` vergibt `FILETYPE`, `api/search.py` schaltet daraufhin die semantische Hälfte ab. Ein Klick auf eine Schaltfläche würde die Suchqualität still verändern.
Stattdessen: eigenes Request-Feld, das die Operatorenmarke nicht setzt.

**3. Ein Total oder Facettenzahlen ausliefern.**
Warum falsch: Zahlen vor dem Rechte-Recheck sind Aussagen über fremde Dokumente (T-02-93). `CandidatePage` trägt aus genau diesem Grund kein Total.
Stattdessen: feste Filtergruppen ohne Zahlen, `hasMore` bleibt die einzige Mengenaussage.

**4. Filter und Sortierung in den Cursorstring kodieren.**
Warum falsch: zweiter Parser für dieselbe URL, und ein Cursorpfad, der bei jeder Filteränderung ungültig wird, sieht dann wie ein Fehler aus statt wie ein Neuanfang.
Stattdessen: eigene Query-Parameter, Filteränderung springt auf Seite eins.

**5. Die Entladung im Leerlaufzweig des Pollers aufhängen.**
Warum falsch: ein stummgeschalteter Poller betritt `run_once` nie wieder, und genau der ruhende Container ist der Zielfall.
Stattdessen: eigene Lifespan-Aufgabe in `main.py`, die beide Halter kennt.

**6. Nur `EmbeddingModel._engine` freigeben.**
Warum falsch: der größere Posten (544,3 MB Spitze) ist der Cutter-Tokenizer im Poller. Eine halbe Entladung liefert eine halbe Zahl, und die steht dann im Store-Text.
Stattdessen: beide Halter, eine Uhr.

**7. Beim Entladen `_absent` oder `_load_failed_at` mit zurücksetzen.**
Warum falsch: dann sucht ein Container ohne Modell nach jeder Freigabe wieder nach den Artefakten, und ein Cooldown nach einer MemoryError-Ladung wäre ausgehebelt. Genau diese Unterscheidung hat das Audit von 06.1-17 eingeführt.
Stattdessen: `release()` setzt ausschließlich `_engine`.

**8. Ein gefahrenes Messskript nachbessern.**
Warum falsch: Byte-Identitäts-Wächter wird rot, und jede Zahl daneben verliert ihren Beleg.
Stattdessen: neues Laufverzeichnis, Nachfolgefassung mit neuem Namen.

**9. `SEARCH_ROUNDS` oder `MAX_CONTAINER_OFFSET` anheben, weil gefilterte Seiten dünner werden.**
Warum falsch: der Deckel ist ein Sicherheitsargument (unbegrenzter Offset gleich unbegrenzte Arbeit pro Anfrage), und `test_search_limits_lockstep.py` hält beide Seiten zusammen.
Stattdessen: der Filter wirkt im Container vor dem Fenster, die Trefferdichte steigt dadurch; wenn eine Seite trotzdem leer bleibt, ist das DI-07-03 und hat bereits seinen ehrlichen Text.

---

## Integrationspunkte in Kurzform

### Container, Leseseite

| Datei | Eingriff |
|---|---|
| `backend/src/findling/api/search.py` | `SearchRequest.types`, `SearchRequest.sort`, Durchreichen in `one_round`, unveränderte Kanarienvogel- und Degradiert-Logik |
| `backend/src/findling/api/snippets.py` | dasselbe Feldpaar, Gleichschritt beim Query-Bau |
| `backend/src/findling/query/rewrite.py` | `build_query(..., extensions=())`, Vereinigung mit den aus dem Text geschnittenen Endungen, `carried_operators` unverändert |
| `backend/src/findling/index/search.py` | Sortierzweig in `candidates`, `_sides` mit Ordnung, `_ranked` gegen die veränderte Trefferform, `_mtimes_of` wiederverwenden, `_permit` unverändert und weiterhin genau zweimal genannt |
| `backend/src/findling/config.py` | Sortierwerte, Endungsdeckel, `EMBED_IDLE_RELEASE_SECONDS` plus Bereich und Umgebungsvariable |
| `backend/src/findling/api/status.py` | Zähler der Freigaben, ggf. sechstes Zustandswort |
| `backend/src/findling/api/resources.py` | **unverändert.** `query_model()` bleibt der reine Durchgriff |

### Container, Schreibseite und Lebenszyklus

| Datei | Eingriff |
|---|---|
| `backend/src/findling/embed/model.py` | `_last_use`, `release()`, `unload_count`, Erhalt der drei Merker |
| `backend/src/findling/embed/engine.py` | `release_if_idle()`, Zähler, ggf. `ENGINE_UNLOADED` und `ENGINE_STATES` |
| `backend/src/findling/worker/poller.py` | `release_the_cutter()`, `busy`, Freigabe auch in `silence()` |
| `backend/src/findling/main.py` | dritte Aufgabe im Lifespan plus Shutdown nach dem Muster von `indexing`/`repairing` |
| `backend/src/findling/tools/one_load.py` | Zusage präzisieren |

### PHP-Companion

| Datei | Eingriff |
|---|---|
| `php/lib/Controller/PageController.php` | vier auf sechs untrusted Werte, `pageUrl` trägt Filter und Sortierung, keine neue Route |
| `php/lib/Service/SearchService.php` | Signatur nimmt `SearchShape`, Rechtekette unangetastet |
| `php/lib/Service/SearchCaps.php` | unverändert (bleibt reine Deckel-Sammlung) |
| `php/lib/Service/ExAppService.php` | zwei Felder im Body von `/search` und `/snippets` |
| `php/templates/search.php` | Filterleiste und Sortierwahl im bestehenden GET-Formular, serverseitig gerendert, ohne Skriptbedarf |
| `php/css/search.css` | Layout der Leiste, keine Literalfarben (Gate) |
| `php/js/search.js` | **unverändert** |
| `php/lib/Search/Provider.php` | **unverändert** |
| `php/lib/Service/AdminViewService.php`, `php/templates/admin.php`, `php/js/admin.js` | Zustandsliste und Satztabelle für die Entladung |
| `php/l10n/{de,de_DE,fr}.{json,js}` | alle neuen sichtbaren Texte, Handpflege, vier Gates |
| `php/lib/Migration/Version001200Date...` | Merker aus v1.1: jeder Minor-Sprung braucht eine Migration, sonst stumme Suche |

### Gates, die den Bau begleiten

`test_php_acl_boundary.py` (Aufrufzählung der Rechtefragen), `test_php_trust_boundary.py` (Routenattribute), `test_search_limits_lockstep.py` (Deckel beiderseits), `test_admin_ui_contract.py` (Seiten, Skripte, Kataloge, Zustandssätze), `test_measurement_scripts.py` (Byte-Identität, Breitengates), `test_ops_scripts.py` (`aws_box.sh`-Unterbefehle in der Usage, Anmeldedaten nie im Klartext), `test_one_load.py`, `test_lifecycle.py`.

---

## Offene Punkte, vor dem Bau zu klären

| Punkt | Warum offen | Wer klärt |
|---|---|---|
| Trefferform unter `order_by_field` in tantivy 0.26.0 | Stub sagt `tuple[Any, DocAddress]`, der Wert ist unter Sortierung der Feldwert statt des Scores; `_ranked` liest ihn heute als Score | Planschritt M2, ein Test gegen den realen Index |
| Stabilität von `offset` zusammen mit `order_by_field` | falls instabil, Nachlauf über Bereichsfilter statt Offset | Planschritt M2 |
| Tatsächlicher Gewinn der Entladung | die Grundlast von 103,2 MB ist bereits ohne Modell und Cutter gemessen; die richtige Größe ist "Rückkehr zur Grundlast nach einem Indexlauf" | Planschritt M4, Messphase M5 |
| Fünf oder sechs Zustandswörter | Kosten gegen Aussagekraft, siehe B.6 | Owner-Entscheid vor M4 |
| Standardwert der Leerlaufschwelle | 900 s ist ein Vorschlag, keine Messung | Messphase M5, Abschaltwert 0 bleibt Rückfallebene |
| Ersatz-Messgröße für den Fremdbestand | Diagnose-Route empfohlen, Alternative `doc_freq` | Planschritt M1 |
| Snapshot-Entscheid `snap-03f1d1d9ad9262704` | fällt laut PROJECT.md nach v1.2 | nach M5 |

---

## Sources

Alle Aussagen über dieses System sind am Quellcode und an den Berichten dieses Repos gelesen, Stand 2026-09-14, Arbeitsbaum `C:\Users\Student\nextcloud-search`.

- `backend/src/findling/api/search.py`, `api/snippets.py`, `api/resources.py`, `api/status.py`
- `backend/src/findling/index/search.py`, `index/schema.py`, `query/rewrite.py`, `store/repo.py`
- `backend/src/findling/embed/model.py`, `embed/engine.py`, `worker/poller.py`, `main.py`, `config.py`
- `backend/.venv/Lib/site-packages/tantivy/tantivy.pyi` (Signatur von `Searcher.search`, `fast_field_values`, `doc_freq`)
- `php/lib/Controller/PageController.php`, `lib/Service/SearchService.php`, `lib/Service/ExAppService.php`, `lib/Service/SearchCaps.php`, `lib/Service/AdminViewService.php`, `lib/Search/Provider.php`, `templates/search.php`, `templates/admin.php`, `js/search.js`
- `backend/tests/test_php_acl_boundary.py`, `test_php_trust_boundary.py`, `test_admin_ui_contract.py`, `test_search_limits_lockstep.py`, `test_measurement_scripts.py`, `test_ops_scripts.py`
- `scripts/ops/search_load.py`, `scripts/ops/aws_box.sh`
- `docs/measurements/2026-09-werkzeugfixe/README.md` und `skripte/98b-sprachfaelle.sh`
- `docs/measurements/2026-09-vergleichsmessung-m7g/` (Skripte, Rohdaten, Abschnitt 5.2)
- `.planning/PROJECT.md`, `.planning/STATE.md`, `CLAUDE.md` (RAM-Tabelle, Owner-Regeln)

---
*Architecture research for: Findling v1.2, Integration von Dateityp-Filter/Sortierung, Modell-Entladung und Messphase*
*Researched: 2026-09-14*
