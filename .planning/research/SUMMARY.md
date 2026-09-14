# Project Research Summary

**Project:** Findling (Nextcloud-Such-ExApp)
**Domain:** Ausbau einer ausgelieferten Nextcloud-ExApp (1.1.0 im Store) um Dateityp-Filter/Sortierung auf der eigenen Ergebnisseite, Modell-Entladung im Leerlauf und eine begleitende Messkampagne auf Zielhardware (ARM, 4 GB RAM)
**Researched:** 2026-09-14
**Confidence:** HIGH für Code-Integration und Versionsstände, MEDIUM für Freigabeketten-Theorie (Allokator/onnxruntime), LOW für alles, was nur eine Messung auf der Zielbox beantworten kann

## Executive Summary

Milestone v1.2 "Messbeleg und Ausbau" ist in allen vier Recherchen dasselbe Bild: drei Erweiterungen entlang bestehender Nahtstellen, keine neue Komponente, kein Reindex, keine neue Laufzeit-Abhängigkeit. Der Dateityp-Filter und die Datumssortierung sitzen auf Feldern, die seit v1.0 im Tantivy-Schema stehen (`ext` als Term, `mtime` als Fast-Field, `index/schema.py:105/114`); die Modell-Entladung ist `del`, `gc.collect()`, ein `ctypes`-`malloc_trim(0)` und eine dritte `asyncio`-Task im bestehenden Lifespan; die Messphase ist zu grossen Teilen Wiederverwendung von Werkzeug, das die letzte Anfahrt am 10.09.2026 bereits gefahren und geeicht hat. Wer hier ein Paket ergänzt, hat mit hoher Wahrscheinlichkeit das falsche Problem gelöst.

Der rote Faden durch alle vier Dokumente ist zugleich die grösste Falle: naheliegende, schnell gebaute Lösungen brechen still eine v1.0/v1.1-Zusage, ohne dass ein Fehler sichtbar würde. Ein UI-Filter, der `type:pdf` in die Suchzeile schreibt, schaltet über `carried_operators`/`FILETYPE` die semantische Suchhälfte für jede gefilterte Anfrage ab (STACK.md A.4/A.5, FEATURES.md Anti-Features, ARCHITECTURE.md A.2, PITFALLS.md Pitfall 2) – die einzig saubere Lösung ist ein eigenes, strukturiertes Request-Feld, das denselben `Occur.Must`-Mechanismus nutzt, den `_mtimes_of()` für die semantische Hälfte ohnehin schon abfragt (STACK.md nennt das "den wichtigsten Integrationsbefund dieses Teils"). Sortierung nach Datum ist ohne Reindex möglich, weil `mtime` bereits `fast=True` ist; Sortierung nach Name oder Grösse ist es nicht und wird von allen vier Dokumenten übereinstimmend aus v1.2 herausgehalten. Die Modell-Entladung hat zwei Speicherhalter statt einem, und ihr grösstes Risiko ist nicht Speicher, sondern die 1,5-Sekunden-Aufrufdecke, an der bereits einmal (10.09.2026, 14:05:17Z) eine echte Suche mit null Treffern gescheitert ist.

Das grösste ungelöste Spannungsfeld ist die Messphase selbst: der vorgeschlagene Zeit-/Kostendeckel für die eine bezahlte Box-Anfahrt ist kleiner als der zuletzt gemessene Volllauf allein, und ein unentdecktes Cron-Intervall hat in v1.1 rund 40 Prozent Laufzeit verschluckt, ohne dass eine der drei anderen Recherchen dieses Risiko im gleichen Detailgrad wie PITFALLS.md aufgreift. Der Plan muss diesen Deckel vor der Anfahrt neu rechnen, die Entladung hinter einen ab Werk ausgeschalteten Schalter legen (sonst lässt sich in einer Anfahrt kein A/B-Beleg führen) und die Bauordnung strikt einhalten: Werkzeug/Runbook, dann Backend-Filter/Sortierung, dann PHP-Oberfläche, dann Entladung hinter dem Schalter, erst dann die eine Box-Anfahrt, zuletzt die Härtung.

## Key Findings

### Recommended Stack

Keine neuen Pakete, weder Backend noch PHP (STACK.md, "Installation": "Backend: nichts... PHP: nichts"). Die Sortierung nutzt `Searcher.search(..., order_by_field="mtime", order=Order.Desc, offset=...)` aus der bereits installierten `tantivy` 0.26.0 (Signatur verifiziert gegen `tantivy/tantivy.pyi`). Die Modell-Entladung braucht nur Stdlib: `gc.collect()` gefolgt von `ctypes.CDLL("libc.so.6").malloc_trim(0)`, mit Schutzschalter gegen fremde libc (`try/except (OSError, AttributeError)`). `onnxruntime` bleibt bewusst bei 1.29.0 statt 1.30.0 (10.09.2026 erschienen), weil ein Runtime-Sprung die Modellqualitäts-Gates und die ARM-Wheel-Prüfung erneut auslösen würde und im Feature-Fenster nichts beiträgt, das nicht auch über die Freigabekette lösbar wäre.

**Kerntechnologien:**
- `tantivy` 0.26.0 (unverändert) – liefert `order_by_field` und den Fast-Field-Mechanismus, den Sortierung und Filter brauchen, ohne Schema-Änderung
- Stdlib `gc` + `ctypes` – die gesamte Freigabekette der Modell-Entladung, keine neue Abhängigkeit
- `onnxruntime` 1.29.0 (gehalten) – `enable_cpu_mem_arena=False` ist bereits gesetzt und ist die Voraussetzung dafür, dass eine Freigabe dem Betriebssystem überhaupt etwas zurückgibt
- `python:3.13-slim-trixie` (Basis-Image, unverändert) – glibc mit `malloc_trim`, das ist Pflicht für die Freigabekette

Zwei Aufräumbefunde nebenbei, ausdrücklich nicht Teil des Milestones: `fastembed==0.8.0` ist gepinnt, wird aber nirgends importiert (Kandidat zur Entfernung); `numpy` ist eine indirekte, nicht deklarierte Abhängigkeit.

### Expected Features

**Must have (Launch v1.2):**
- Typfilter mit geschlossener Gruppenliste (PDF, Dokumente, Tabellen, Präsentationen, Bilder, Text), ohne Trefferzähler, serverseitig ohne JavaScript
- Ein Filtervokabular für UI-Gruppen und die bestehende `type:`-Textsyntax, nicht zwei
- Sortierung Relevanz (Standard) und "Zuletzt geändert", mit Zweitschlüssel `file_id` gegen Zeitstempel-Gleichstand
- Filter und Sortierung in der URL, defensiv gelesen, Cursorpfad wird bei jeder Änderung auf Seite 1 zurückgesetzt
- Modell-Entladung nach Leerlauf, TTL als Umgebungsvariable, `0` schaltet ab, ab Werk aus für die Messphase
- Erste Suche nach Entladung antwortet innerhalb der 1,5-Sekunden-Decke lexikalisch, Nachladen im Hintergrund
- Wiederaufwärm-Kosten gemessen und ausgewiesen, nicht geschätzt
- Migration für 1.2.0 (Pflicht, obwohl der Index kompatibel bleibt)

**Should have (v1.x, nach Validierung):**
- Zeitraumfilter `since`/`until` – repariert eine heute stumme Lücke (Unified-Search-Dialog verwirft Findling kommentarlos, sobald jemand dort einen Datumsfilter setzt, den `getSupportedFilters()` nicht anbietet)
- "Älteste zuerst" als dritte Sortierung
- Mimetype-Gruppen aus `files.mime` statt `ext`, falls Genauigkeit wichtiger wird als der bestehende Kommentar "no join against files"

**Defer (v2+):**
- Sortierung nach Name oder Grösse – kostet ein neues Fast-Field, `SCHEMA_VERSION`-Sprung, Vollreindex auf jeder Bestandsinstallation
- Facettenzähler je Dateityp – wäre ein Zähl-Orakel vor dem Rechtefilter (T-02-93), von allen vier Dokumenten übereinstimmend ausgeschlossen
- Personenfilter, Ordner-Einschränkung, geplantes Vorwärmen nach Zeitplan

### Architecture Approach

Alle drei Vorhaben hängen sich an bestehende Nahtstellen: der Filter/Sortier-Ausbau bleibt vollständig im Backend-Kandidatenpfad (`index/search.py::candidates`) und wird über zwei neue, optionale Felder in `SearchRequest`/`SnippetsRequest` transportiert; die PHP-Seite bleibt serverseitig gerendert, ohne Vue, ohne JSON-Route, ohne Build-Schritt. Die Modell-Entladung bekommt einen neuen, dritten Halter-Zustand in `embed/model.py`/`embed/engine.py` plus eine neue Freigabefunktion im Poller (`worker/poller.py`), ausgelöst von einer dritten Lifespan-Aufgabe in `main.py` (nicht vom Poller selbst, weil ein stummgeschalteter Poller `run_once` nie wieder betritt). Die Messphase ist überwiegend Wiederverwendung geeichter Skripte, mit genau einer inhaltlichen Werkzeugänderung (Fremdbestands-Messgrösse) und einem neuen Wiederaufwärm-Messwerkzeug.

**Hauptkomponenten:**
1. `query/rewrite.py::build_query(extensions=...)` – vereinigt Text-Operator und UI-Filter zu einer Query, ohne `carried_operators` zu berühren
2. `index/search.py::candidates` – trägt sowohl den Sortierzweig (Fusionsfenster nach `mtime` statt RRF) als auch die Filterklausel; bleibt die einzige Stelle, an der Reihenfolge und Sichtbarkeit entstehen
3. `embed/engine.py::release_if_idle()` + `worker/poller.py::release_the_cutter()` – zwei getrennte Freigabefunktionen für zwei getrennte Speicherhalter, orchestriert von einer neuen Lifespan-Aufgabe in `main.py`
4. `php/lib/Controller/PageController.php` – erweitert um zwei defensiv gelesene, geschlossene Werte (`types`, `sort`), keine neue Route, kein neuer JSON-Kanal

### Critical Pitfalls

1. **Filter wirkt hinter der Fusion statt in der Anfrage** – auf grossem Bestand (52.111 Dokumente) liefert das systematisch halbleere Seiten, weil das 100er-Fusionsfenster nur die relevantesten Dokumente aller Typen füllt. Vermeidung: Filter als `Occur.Must`-Klausel vor dem ersten `searcher.search`, exakt der Pfad, den `_mtimes_of()` schon für die semantische Hälfte anbietet.
2. **UI-Filter als `type:`-Text geschickt** – schaltet über `carried_operators`/`FILETYPE` die Semantik für jede gefilterte Suche ab, unsichtbar. Vermeidung: eigenes Request-Feld, das die Operator-Marke nicht setzt.
3. **Sortierung wird der Fusion als Argument untergeschoben** – tantivy liefert unter `order_by_field` den Feldwert statt des BM25-Scores im ersten Tupelglied; empirisch gemessen gegen die installierte 0.26.0 (500/300/200/100 statt 0,1363/0,1220). `Candidate.score` würde sonst einen Zeitstempel als Relevanz ausliefern. Vermeidung: Sortierung ist ein eigener, rein lexikalischer Modus wie `lexical_only` heute schon, Score wird unter Sortierung auf 0.0 gesetzt.
4. **Nur ein Speicherhalter wird entladen** – der grössere Posten ist nicht die ONNX-Sitzung (250 bis 400 MB), sondern der Cutter-Tokenizer im Poller (542,8 bis 544,3 MB Spitze). Vermeidung: beide Halter, eine gemeinsame Leerlauf-Uhr.
5. **Nachladen im Anfragepfad reisst die 1,5-Sekunden-Decke** – bereits einmal produktiv passiert (10.09.2026, `cURL error 28`, null Treffer). Vermeidung: kaltes Modell beantwortet die Suche sofort lexikalisch, Laden läuft im Hintergrund.

## Implications for Roadmap

Alle vier Dokumente konvergieren, mit unterschiedlicher Betonung, auf dieselbe Bauordnung. ARCHITECTURE.md liefert dafür bereits einen benannten Phasenvorschlag (M1 bis M6), PITFALLS.md liefert unabhängig davon dieselbe Reihenfolge über die Pitfall-Tabelle ("Filterphase und Entladephase vor der Messphase, Härtungsphase zuletzt"). Diese Übereinstimmung ist selbst ein Befund: keines der vier Dokumente schlägt eine andere Grobreihenfolge vor.

### Phase 1: Werkzeug und Runbook (ohne Box)

**Rationale:** Der Messbericht vom 10.09.2026 hält explizit fest: "ein Messskript, das während seines eigenen Laufs nachgebessert wird, macht jede Zahl daneben unbelegt" (PITFALLS.md Pitfall 15/18, ARCHITECTURE.md C.2/C.3). Das Werkzeug muss vor der bezahlten Anfahrt fertig sein.
**Delivers:** Vorprüfung der Fremdbestands-Messgrösse auf die Diagnose-Route umgestellt (statt der gedeckelten OCS-Route, die nie über 26 Treffer hinauskommt), `aws_box.sh` um "Volume aus Snapshot" ergänzt, `docs/runbook-messbox.md` als Erstfassung aus drei bisherigen Berichten.
**Addresses:** keine Feature-Zeile direkt, aber Voraussetzung für den Wirkungsbeleg (FEATURES.md, Differentiator "Wiederaufwärm-Zahl wird ausgewiesen statt versprochen").
**Avoids:** Pitfall 15 (Messdeckel kleiner als der Lauf), Pitfall 16 (Vergleichbarkeit bricht an fünf Stellen), Pitfall 18 (Werkzeug zählt Ausfälle als Erfolge).

### Phase 2: Backend – Filter und Sortierung

**Rationale:** "Die Seite kann keinen Parameter senden, den der Container nicht kennt" (ARCHITECTURE.md, harte Abhängigkeit 1). `extra="forbid"` in `SearchRequest` liefert sonst HTTP 400, was auf der PHP-Seite als stumme, leere Suche ankommt.
**Delivers:** `SearchRequest.types`/`sort`, `SnippetsRequest` im Gleichschritt, `build_query(extensions=...)`, Sortierzweig in `candidates` (Fusionsfenster nach `mtime` bei aktiver Sortierung, `Occur.Must`-Filterklausel bereits im Fenster), Konstanten in `config.py`.
**Uses:** `tantivy` `order_by_field`/`Order`, bestehendes `FIELD_EXT`/`FIELD_MTIME`.
**Implements:** `index/search.py::candidates`, `query/rewrite.py::build_query`.

### Phase 3: PHP – Ergebnisseite

**Rationale:** Kann erst beginnen, wenn Backend 1.2 die Felder kennt (harte Abhängigkeit M2 vor M3). Der Versions-Lockstep (`ExAppService`) verhindert ohnehin, dass ein PHP 1.2 gegen ein Backend 1.1 läuft.
**Delivers:** Filterleiste und Sortierwahl im bestehenden GET-Formular, `PageController::pageUrl()` mit `types`/`sort`, Cursorpfad-Invalidierung bei jeder Änderung, sechs l10n-Dateien in EN/DE/FR im Gleichstand.
**Addresses:** FEATURES.md Table Stakes (Typgruppen im Nextcloud-Vokabular, aktive Filter sichtbar/entfernbar, Filterwechsel setzt auf Seite 1 zurück).
**Avoids:** Pitfall 6 (Cursorpfad überlebt Filterwechsel), Pitfall 7 (zweite Tür an der Berechtigungsgrenze), Pitfall 8 (MIME gegen Endung).

### Phase 4: Modell-Entladung (hinter Schalter, ab Werk aus)

**Rationale:** Unabhängig von M2/M3, muss aber vor der Messphase stehen, sonst misst die eine bezahlte Anfahrt die Entladung gar nicht mit (harte Abhängigkeit M4 vor M5, Owner-Entscheid "eine Anfahrt"). Der Schalter ist zwingend, weil eine einzige Anfahrt sonst keine A/B-Zurechenbarkeit zwischen DI-10-04-Fix und Entladung herstellen kann (PITFALLS.md Pitfall 19).
**Delivers:** `EmbeddingModel.release()`, `EmbeddingModel._last_use`, `embed/engine.py::release_if_idle()`, `worker/poller.py::release_the_cutter()`, dritte Lifespan-Aufgabe in `main.py`, Idle-Umgebungsvariable mit `0` als Abschaltwert (Namensfrage zwischen den Dokumenten, siehe Gaps), `tools/one_load.py` und dessen Gate neu formuliert.
**Uses:** Stdlib `gc`/`ctypes`, bestehendes `RLock` in `EmbeddingModel`.
**Implements:** die beiden Freigabeketten aus ARCHITECTURE.md Teil B.

### Phase 5: Messphase – eine Box-Anfahrt

**Rationale:** Wiederverwendung von Werkzeug aus M1, Auswertung von M2 bis M4 unter Realbedingungen (ARM, 4 GB). Muss nach M4 liegen, sonst bleibt die Entladung im Store unbelegt.
**Delivers:** DI-10-04-Wirkungsbeleg-Volllauf, vier regressive Laststufen, Sprachfall-Messung mit der neuen Messgrösse, Wiederaufwärm-Kosten der Entladung (warm und kalt, mit und ohne Seitencache), Kosten- und Abbauentscheid.
**Addresses:** FEATURES.md Differentiator "Die Wiederaufwärm-Zahl wird ausgewiesen statt versprochen".
**Avoids:** Pitfall 9 (Datumssortierung auf grossem Fremdbestand liefert leere Seiten), Pitfall 10 (RSS kommt nicht zurück), Pitfall 12 (Kaltstart-Klippe), Pitfall 17 (Aufwärmphase statt Erzeugnis gemessen).

### Phase 6: Härtung und Store-Einreichung v1.2.0

**Rationale:** Muss zuletzt liegen, weil sie die Ergebnisse aus M2 bis M5 in Store-Texte, Kataloge und die Upgrade-Beweiskette überführt.
**Delivers:** Migration `Version001200Date...` (Pflicht, auch ohne Schemaänderung – Merker aus v1.1, dort erst in der Härtungsphase gefunden), Ende-zu-Ende-Upgrade-Beweis 1.1.0 auf 1.2.0, Messzahl an drei Stellen im Gleichschritt (README.en.md, beide info.xml), ggf. sechstes `engineState`-Wort mit vier Katalog-Gates.
**Addresses:** alle offenen Store-Zusagen.
**Avoids:** Pitfall 13 (sechster Engine-Zustand bricht Vokabular), Pitfall 20 (Minor-Sprung ohne Migration).

### Phase Ordering Rationale

- M2 vor M3: `extra="forbid"` macht einen Mischstand zum HTTP-400-Fehler, der auf der PHP-Seite als stumme Suche ankommt.
- M1 vor M5: belegt am Bericht vom 10.09.2026, ein während der Anfahrt korrigiertes Skript entwertet seine eigene Messung.
- M4 vor M5: Owner-Entscheid "eine Anfahrt" verlangt, dass die Entladung in derselben Anfahrt mitgemessen wird, was einen Schalter voraussetzt.
- M2/M3 und M4 sind gegeneinander vertauschbar; die vorgeschlagene Reihenfolge (Filter zuerst) liefert früher den sichtbaren Teil des Milestones und lässt die Entladung notfalls per Schalter ausgeliefert, ohne den Milestone zu gefährden.

### Research Flags

Phasen, die während der Planung vertiefte Recherche brauchen:
- **Phase 2 (Backend Filter/Sortierung):** die Trefferform von `tantivy.Searcher.search` unter `order_by_field` ist zwar bereits empirisch geprüft (PITFALLS.md, eigene Probe gegen die installierte 0.26.0), die Stabilität von `offset` zusammen mit `order_by_field` bei 52.111 Dokumenten ist es nicht (ARCHITECTURE.md, "Offene Punkte"). Ein Test gegen den realen Index vor dem Bau ist Pflicht.
- **Phase 4 (Entladung):** wie viel RSS die Freigabekette (`gc.collect()` + `malloc_trim(0)`) auf der Zielhardware tatsächlich zurückgibt, ist in keinem der vier Dokumente mehr als eine begründete Vermutung; STACK.md nennt es ausdrücklich "nicht recherchierbar, ... messbar". Der Vorprüflauf muss vor dem Rest der Phase feststehen.
- **Phase 5 (Messphase):** der Zeit-/Kostendeckel braucht eine eigene Rechnung mit dem Owner, weil der vorgeschlagene Deckel (26 h) kleiner ist als der zuletzt gemessene Volllauf allein (26 h 37 min, PITFALLS.md Pitfall 15).

Phasen mit etablierten Mustern (keine gesonderte Phasenrecherche nötig):
- **Phase 3 (PHP-Oberfläche):** folgt exakt dem Formular-/Katalog-Muster, das v1.0/v1.1 bereits etabliert und mit Gates abgesichert haben.
- **Phase 6 (Härtung):** Migrationsmuster, Upgrade-Beweis und Katalog-Gates sind aus v1.1 unverändert übertragbar.

## Wo die vier Dokumente uneinig sind, statt gemittelt

**(1) Der Dateityp-Filter muss ein Request-Feld sein, nicht `type:` im Text.** Kein Dissens, aber der zentralste Einzelbefund über alle vier Dokumente: STACK.md nennt es "den wichtigsten Integrationsbefund dieses Teils" (A.4), FEATURES.md führt es als V1/Anti-Feature, ARCHITECTURE.md als harte Abhängigkeit D1/D3, PITFALLS.md als Pitfall 2 mit der Warnung, dass eine Paraphrasensuche unter Filter ein vorhandenes Dokument nicht mehr findet. Grund: `carried_operators()` markiert jedes `type:`-Token als `FILETYPE`, `one_round()` setzt daraufhin `lexical_only = True` und schaltet die Vektorhälfte für die ganze Anfrage ab. Die Lösung ist ebenso einhellig: ein eigenes, optionales Feld in `SearchRequest`/`SnippetsRequest`, das dieselbe `Occur.Must`-Klausel erzeugt wie `_extension_query()`, aber `carried_operators` nicht berührt.

**(2) Sortierung: Datum ja ohne Reindex, Name/Grösse nein – und der Score-wird-Sortierschlüssel-Fallstrick ist konkret gemessen.** `mtime` ist seit v1.0 `fast=True` (`index/schema.py:114`, Kommentar dort: "Display today, sorting and since/until later"), also kostet Datumssortierung keinen `SCHEMA_VERSION`-Sprung. Name (`FIELD_NAME`, Textfeld ohne Fast-Spalte) und Grösse (gar kein Feld im Schema) würden dagegen einen Vollreindex über 52.111 Dokumente erzwingen und sind von allen vier Dokumenten übereinstimmend aus v1.2 ausgeschlossen. Der Fallstrick, den nur PITFALLS.md und ARCHITECTURE.md mit einer eigenen Messung belegen: unter `order_by_field` liefert tantivy 0.26.0 im ersten Tupelglied nicht mehr den BM25-Score, sondern den Feldwert selbst – empirisch gegen die installierte Version geprüft, mit konkreten Zahlen (500/300/200/100 statt 0,1363/0,1220). `index/search.py::_ranked` liest dieses Element heute ungeprüft als `score`. STACK.md beschreibt denselben Mechanismus theoretisch ("das erste Tupelglied ist ... nicht mehr der Score"), ohne die Messung; die Empfehlung aller vier ist trotzdem gleich: Sortierung ist ein eigener, rein lexikalischer Modus, Score wird unter Sortierung auf 0.0 gesetzt, RRF wird nicht angewendet.

**(3) Die Entladung hat zwei Speicherhalter, und das grösste Risiko ist die 1,5-Sekunden-Decke, nicht der Speicher selbst.** `EmbeddingModel._engine` (STACK.md, ARCHITECTURE.md B.1: Gewichte 118 MB, Aktivierungsspitze 250 bis 400 MB) ist der kleinere Posten. Der grössere ist `Poller._chunker` (ARCHITECTURE.md nennt 544,3 MB Spitze, STACK.md nennt aus demselben Messbericht 542,8 MB für "fünf Posten zusammen" – die beiden Zahlen stammen aus unterschiedlichen Messläufen/Plattformen desselben Berichts und sind keine echte Widersprüchlichkeit, aber die Dokumente runden sie leicht unterschiedlich). PITFALLS.md Pitfall 11 warnt zusätzlich vor einem doppelten Besitzer-Zustand: wird nur `embed/engine.py::reset()` (ursprünglich ein Test-/Werkzeug-Helfer) als Entladefunktion zweckentfremdet, bleibt der Poller mit einer eigenen Referenz zurück, und der Container trägt nach einem Nachladen zwei Sitzungen gleichzeitig – exakt die 276 MB Regression, die Plan 06.1-02 einmal beseitigt hat. Das grössere Risiko ist aber unabhängig vom Speicher: `ExAppService::REQUEST_TIMEOUT_SECONDS = 1,5 s` gilt für jeden Aufruf, ein Kaltstart hat bereits einmal produktiv (10.09.2026, 14:05:17Z, `cURL error 28`) eine Suche mit null Treffern erzeugt, ohne Fehlermeldung für den Nutzer. Alle vier Dokumente empfehlen unabhängig voneinander dieselbe Lösung: die erste Suche nach Entladung wird nicht auf das Nachladen warten gelassen, sondern sofort über den bestehenden Degradationspfad (`EmbedOutcome.unavailable()`, D-19) rein lexikalisch beantwortet, das Modell wärmt im Hintergrund. Zusätzliche, nur in ARCHITECTURE.md ausgesprochene Nuance: die gemessene Grundlast von 103,2 MB ist nach der seit Plan 07-03 faulen Bauweise vermutlich bereits *ohne* Modell und Cutter gemessen worden; die eigentlich interessante Grösse ist deshalb nicht "Grundlast minus 415 MB", sondern "Rückkehr zur Grundlast nach einem Indexlauf" – eine Unterscheidung, die STACK.md und FEATURES.md in ihrer Zahlentabelle nicht explizit machen und die vor der Store-Formulierung geklärt werden muss.

**(4) Der Box-Budget-Konflikt ist nur in PITFALLS.md explizit durchgerechnet.** ARCHITECTURE.md nennt den Owner-Vorschlag "26 h / 3,50 USD" beiläufig als Runbook-Bestandteil, ohne ihn gegen die zuletzt gemessene Laufzeit zu prüfen. PITFALLS.md (Pitfall 15) rechnet explizit gegen: der letzte Volllauf allein hat bereits 26 Stunden 37 Minuten gedauert, dazu kommen aus v1.1 gemessene 38 Minuten Anfahrt plus rund 2 Stunden 50 Minuten Nachmessungen (zusammen gut 3,5 Stunden neben dem Lauf). Der vorgeschlagene 26-Stunden-Deckel reisst also rechnerisch am ersten Tag, genau wie der 30-Stunden-Deckel aus v1.1 bereits einmal gerissen ist (auf 34 Stunden angehoben). Empfehlung aus PITFALLS.md: Deckel auf mindestens 31 Stunden setzen (rund 3,59 USD bei 0,1158 USD/h) oder den Wirkungsbeleg bewusst auf einen Teilkorpus verkleinern, aber als Owner-Entscheidung vor der Anfahrt, nicht als stillschweigende Annahme im Plan. Eng verwandt und ebenfalls nur in PITFALLS.md (Pitfall 16) benannt: ein unentdecktes Cron-Intervall (12 statt 5 Minuten `StorageCrawlJob`) hat in v1.1 rund 5,85 Stunden Leerlauf erzeugt und einen Teil des gemessenen 40,6-Prozent-Laufzeitzuwachses verursacht, der eigentlich dem DI-10-04-Fix zugeschrieben wurde. Für v1.2 folgt daraus: das Cron-Intervall der Zielinstanz gehört vor jedem Lauf ins Runbook-Protokoll, sonst ist eine gemessene Verbesserung möglicherweise die Box und nicht der Fix.

**(5) Das `one_load`-Gate und die `engineState`-Wortwahl sind ein echter, ungelöster Dissens zwischen den Dokumenten.** Alle vier sind sich einig, dass `tools/one_load.py`/`_LOAD_COUNT` inhaltlich umformuliert werden muss: die alte Zusage "ein Prozess lädt genau einmal" wird mit der Entladung wörtlich falsch, PITFALLS.md (Pitfall 14) verlangt eine neue Invariante ("zu keinem Zeitpunkt existieren zwei Engines, und innerhalb eines warmen Fensters wird genau einmal geladen") vor dem Bau. Uneinig sind sich die Dokumente aber bei der Frage, ob ein sechstes `engineState`-Wort ("unloaded"/"idle") eingeführt wird. STACK.md ist dagegen ("Kein sechster Engine-Zustand ... Nicht tun") und will stattdessen, dass `engine_state()` nach der Entladung wieder `cold` liefert. PITFALLS.md (Pitfall 13) empfiehlt ebenfalls ausdrücklich, `cold` wiederzuverwenden und die Information "war schon geladen" höchstens als separate Zahl auf der Admin-Seite zu führen. FEATURES.md dagegen listet ein "Sechstes `engineState`-Wort" als Teil des MVP-Umfangs (Launch-With-Checkliste), und ARCHITECTURE.md nennt "ein sechstes Wort `unloaded`" seine eigene Empfehlung ("Empfohlen"), mit dem expliziten Gegenargument, dass der Milestone verlangt, die Wiederaufwärm-Kosten "auszuweisen", und `cold` allein den Unterschied zwischen "nie gelesen" und "zum Sparen freigegeben" verwischt. Das ist keine Nuance, sondern eine Empfehlung, die zwischen den vier Dokumenten in zwei Richtungen zeigt, mit Kostenfolgen: ein sechstes Wort berührt sechs Stellen im Gleichstand (`engine.py`, `AdminViewService.php`, `admin.php`, `admin.js`, drei Katalogpaare) und vier Katalog-Gates. Dieser Punkt gehört als benannter Owner-Checkpoint in Phase 4, nicht als vorentschiedene Annahme in den Plan.

## Confidence Assessment

| Bereich | Konfidenz | Anmerkung |
|------|------------|-------|
| Stack | HIGH | Alle Versionsstände (`tantivy` 0.26.0, `onnxruntime` 1.29.0, Basis-Image) gegen PyPI/Tag geprüft; die Freigabekette selbst ist MEDIUM (glibc-Mechanik dokumentiert, aber die tatsächliche Rückgabe auf der Zielbox ist LOW, siehe Gaps) |
| Features | HIGH für alles aus eigenem Code/eigenen Messberichten, MEDIUM für die UX-Erwartungen, die aus Fremdprodukten (Files-App, Paperless-ngx, Immich, Ollama, LM Studio) abgeleitet und nicht am eigenen Nutzerverhalten gemessen sind | Quellenqualität ist im Dokument selbst so benannt |
| Architektur | HIGH für alle Integrationspunkte (direkt am Quellcode mit Datei:Zeile belegt), MEDIUM für zwei Punkte, die vor dem Bau am laufenden System verifiziert werden müssen (tantivy-Trefferform unter `order_by_field`, tatsächlicher RAM-Gewinn) | beide MEDIUM-Punkte sind im Dokument selbst als VERIFIZIEREN markiert |
| Pitfalls | HIGH für alles am eigenen Baum/den eigenen Rohdaten nachgelesene oder empirisch gemessene (inkl. eigener Tantivy-Sortierprobe gegen die installierte 0.26.0), MEDIUM für Allokator-/onnxruntime-Aussagen zur RSS-Rückgabe (Fremdquellen, ein offener Upstream-Bug), explizit LOW für nichts | Dokument benennt seine eigene Konfidenz differenziert je Aussage |

**Overall confidence:** HIGH für die Code-Integration und den Funktionsumfang, MEDIUM bis LOW für alles, was nur eine Messung auf der Zielhardware beantworten kann (RSS-Rückgabe, Kaltstartdauer, Vergleichbarkeit über mehrere Lade-/Entladezyklen).

### Gaps to Address

- **Wie viel RSS die Entladung auf der Zielbox tatsächlich zurückgibt** – keines der vier Dokumente kann das recherchieren, nur messen. Ein Vorprüflauf muss am Anfang der Entladephase stehen und darüber entscheiden, ob die Funktion überhaupt gebaut wird oder als "gemessen, Ergebnis negativ" dokumentiert im Bericht landet (STACK.md B.7, PITFALLS.md Pitfall 10 nennen das ausdrücklich einen legitimen Ausgang).
- **Wie teuer ein kaltes Laden auf der konkreten Zielhardware (m7g.large-Nachfolger) ist**, in Millisekunden gegen die 1,5-Sekunden-Decke, mit und ohne Seitencache – entscheidet den Standardwert der Leerlaufschwelle, der aktuell nur ein Vorschlag (900 s) ist.
- **Namensinkonsistenz der Umgebungsvariable** zwischen STACK.md (`FINDLING_EMBED_IDLE_SECONDS`) und ARCHITECTURE.md (`EMBED_IDLE_RELEASE_SECONDS`/`FINDLING_EMBED_IDLE_RELEASE_SECONDS`) – vor dem Bau auf einen Namen festlegen.
- **Sechstes `engineState`-Wort ja oder nein** (siehe Disagreement 5 oben) – als Owner-Checkpoint vor Phase 4 klären, nicht während des Baus entscheiden.
- **Filterort ext-im-Index vs. mime-in-SQLite** (FEATURES.md D2/D3 führt das noch als offene Frage, obwohl STACK.md/ARCHITECTURE.md bereits eine konkrete, kostengünstigere Umsetzung ohne Join spezifizieren) – die Planung sollte die STACK/ARCHITECTURE-Lösung als Standard übernehmen und die SQLite-Variante nur bei nachgewiesenem Genauigkeitsbedarf (Pitfall 8: `.jpg` vs `.jpeg`, Dateien ohne Endung) nachziehen.
- **Zeit-/Kostendeckel der Box-Anfahrt** – muss vor der Anfahrt neu gerechnet und vom Owner freigegeben werden (siehe Disagreement 4).

## Sources

### Primary (HIGH confidence)
- Eigener Quellcode, Stand 2026-09-14: `backend/src/findling/index/schema.py`, `index/search.py`, `index/fusion.py`, `query/rewrite.py`, `api/search.py`, `api/snippets.py`, `api/status.py`, `embed/model.py`, `embed/engine.py`, `worker/poller.py`, `main.py`, `config.py`, `extract/dispatch.py`
- `php/lib/Controller/PageController.php`, `lib/Service/{SearchService,ExAppService,AdminViewService,SearchCaps}.php`, `lib/Search/Provider.php`, `templates/{search,admin}.php`, `js/{search,admin}.js`
- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` (Abschnitte 5, 5.2, 5.3, 6, 9) und Rohdaten, `docs/measurements/2026-09-werkzeugfixe/README.md`
- `quickwit-oss/tantivy-py`, Tag `0.26.0`, `tantivy/tantivy.pyi`; eigene Probe gegen die installierte Version am 14.09.2026 (Score-wird-Feldwert, Fast-Field-Fehlermeldungen)
- PyPI JSON-API für tantivy, onnxruntime, tokenizers, sqlite-vec, semantic-text-splitter, fastembed, Stand 14.09.2026

### Secondary (MEDIUM confidence)
- microsoft/onnxruntime Issue #14590 (Maintainer-Aussage zu `del`/`gc.collect()`) und #26831 (offen, RSS wächst trotz `ReleaseSession`/`ReleaseEnv`)
- man7.org `malloc_trim(3)`, `mallopt(3)` (glibc-Mechanik, HIGH für die Dokumentation selbst, MEDIUM für die Übertragung auf dieses Produkt)
- Nextcloud Developer Manual (Search-Filter), `nextcloud/server` Quellcode (`UnifiedSearchModal.vue`, `FileListFilterType.vue`, `mimetypealiases.dist.json`)
- Immich (`MACHINE_LEARNING_MODEL_TTL`), Ollama (`OLLAMA_KEEP_ALIVE`), LM Studio (Idle TTL), Paperless-ngx als UX-Erwartungsmassstab

### Tertiary (LOW confidence)
- Keine tatsächliche RSS-Rückgabe-Zahl auf Zielhardware, keine Kaltstart-Zahl auf der konkreten v1.2-Zielinstanz – beides ausdrücklich als "nur messbar, nicht recherchierbar" markiert

---
*Research completed: 2026-09-14*
*Ready for roadmap: yes*
