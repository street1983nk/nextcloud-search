# Requirements: Findling Milestone v1.2 "Messbeleg und Ausbau"

**Defined:** 2026-09-14
**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten, ohne dass der Admin irgendetwas konfigurieren muss.
**Scope-Entscheid Owner 14.09.2026:** Messphase (eine Box-Anfahrt), Ergebnisseite-Ausbau, Modell-Entladung, Härtungen + Release v1.2.0; Extras Zeitraumfilter und "Älteste zuerst" beide REIN.

## v1.2 Requirements

### Filter und Sortierung (FILT)

- [x] **FILT-01**: Nutzer kann Treffer auf der Ergebnisseite nach Dateityp-Gruppen filtern (geschlossene Liste: PDF, Dokumente, Tabellen, Präsentationen, Bilder, Text); die semantische Hälfte bleibt dabei aktiv (strukturiertes Request-Feld in SearchRequest/SnippetsRequest, nie `type:`-Text, `carried_operators` bleibt unberührt)
- [x] **FILT-02**: Nutzer kann nach "Zuletzt geändert" und "Älteste zuerst" sortieren; Relevanz bleibt Standard. Zweitschlüssel `file_id` gegen Zeitstempel-Gleichstand; Sortierung ist ein eigener, rein lexikalischer Modus (Score unter Sortierung 0.0, RRF aus; tantivy liefert unter `order_by_field` den Feldwert statt des Scores, `_ranked` braucht den eigenen Zweig)
- [x] **FILT-03**: Nutzer kann Treffer per Zeitraumfilter since/until eingrenzen; der Datumsfilter des Unified-Search-Dialogs wird in `getSupportedFilters()` deklariert und beachtet, damit Findling dort nicht mehr stumm verschwindet
- [x] **FILT-04**: Filter und Sortierung reisen in der URL, sind sichtbar und entfernbar; jede Filter- oder Sortieränderung setzt auf Seite 1 zurück (Cursorpfad wird invalidiert, ein fremder Cursorpfad wird nicht akzeptiert)
- [x] **FILT-05**: Rechtegrenze unverändert: jeder gefilterte/sortierte Treffer durchläuft denselben ACL-Vorfilter + finalen PHP-Recheck; der Paritätstest deckt die neuen Parameter ab

### Modell-Entladung (MEM)

- [x] **MEM-01**: Admin kann die Leerlauf-Entladung per Umgebungsvariable aktivieren (TTL in Sekunden, 0 = aus); ab Werk AUS (Voraussetzung für den A/B-Beleg in der einen Box-Anfahrt). Variablenname wird vor dem Bau festgelegt (STACK vs ARCHITECTURE nennen unterschiedliche Namen)
- [ ] **MEM-02**: Die Entladung gibt BEIDE Speicherhalter frei (EmbeddingModel-Engine UND Poller-Cutter/Tokenizer); die Beleg-Messgröße ist "Rückkehr zur Grundlast nach einem Indexlauf", nicht "Grundlast minus X"
- [x] **MEM-03**: Die erste Suche nach einer Entladung antwortet innerhalb der 1,5-Sekunden-Decke lexikalisch (bestehender Degradationspfad `EmbedOutcome.unavailable()`/D-19); das Modell wärmt im Hintergrund nach. Der cURL-error-28-Fall vom 10.09.2026 darf nicht zum Regelfall werden
- [x] **MEM-04**: Ein Vorprüflauf belegt die tatsächliche RSS-Rückgabe (gc.collect + malloc_trim) auf Zielhardware, BEVOR die Funktion fertig gebaut wird; ein negativer Ausgang ist legitim und wird dokumentiert ("gemessen, Ergebnis negativ") statt ausgeliefert
- [x] **MEM-05**: Die one_load-Zusage (`tools/one_load.py` + Gate) wird neu formuliert: nie zwei Engines gleichzeitig, genau ein Laden je warmem Fenster; die Admin-Seite zeigt den Zustand. Die engineState-Wortwahl (fünftes Wort `cold` wiederverwenden vs sechstes Wort `unloaded`, Kostenfolge sechs Stellen + vier Katalog-Gates) ist ein benannter Owner-Checkpoint in der Phase, keine Vorentscheidung

### Messphase (MESS, Fortsetzung der v1.1-Nummerierung)

- [x] **MESS-04**: Werkzeug und Runbook stehen VOR der bezahlten Anfahrt: die Fremdbestands-Vorprüfung misst über die Diagnose-Route (`ranked_sides`) statt der gedeckelten OCS-Route; `aws_box.sh` kann Volume-aus-Snapshot (`snap-03f1d1d9ad9262704`); `docs/runbook-messbox.md` als Erstfassung aus den drei bisherigen Berichten
- [ ] **MESS-05**: EINE Box-Anfahrt liefert: DI-10-04-Wirkungsbeleg (Volllauf gegen den Korpus-Snapshot mit Top-up-Fix), Untersuchung der vier regressiven Laststufen, Sprachfall-Messung ohne Fremdbestand (DI-10-02/DI-11-01, neue Messgröße), Wiederaufwärm-Kosten der Entladung (warm/kalt, mit/ohne Seitencache, A/B über den MEM-01-Schalter). Der Zeit-/Kostendeckel wird VOR der Anfahrt neu gerechnet und vom Owner freigegeben (der 26-h-Vorschlag reißt rechnerisch: letzter Volllauf allein 26 h 37 min plus ~3,5 h Rüstzeit; PITFALLS empfiehlt mindestens 31 h / ~3,59 USD oder bewusst Teilkorpus)
- [x] **MESS-06**: Das Cron-Intervall der Zielinstanz wird vor jedem Messlauf protokolliert (12 statt 5 Minuten haben in v1.1 rund 5,85 h Leerlauf und einen Teil der +40,6 % Laufzeit erzeugt); Vergleichbarkeitsbedingungen (Korpus, Werkzeugstand, Instanztyp) stehen im Runbook

### Härtung und Release (HART/REL, Fortsetzung ab REL-02)

- [ ] **HART-01**: DI-11-02/03/05/06 abgearbeitet oder dokumentiert entschieden (u.a. flatternder pgsql-Ast HTTP 423: bei rot erst wiederholen)
- [ ] **HART-02**: BL-F01-Schlusssatz zur Connector-Synergie in den Store-Texten beider Hälften (EN/DE/FR, Wortlaut-Basis in BACKLOG.md, Gate-konform: keine Em-Dashes, keine Backticks/Tabellen)
- [x] **HART-03**: stable35-Fenster-Entscheid (RE-CHECK 16.09.2026, Entscheid v2-a) vollzogen und dokumentiert
- [ ] **REL-02**: v1.2.0 eingereicht: Migration `Version001200Date...` (Pflicht bei jedem Minor-Sprung, auch ohne Schemaänderung), Ende-zu-Ende-Upgrade-Beweis 1.1.0 auf 1.2.0 in CI, Messzahl an drei Stellen im Gleichschritt (README.en.md + beide info.xml), Store-Submission mit 2x HTTP 201

## Future Requirements (deferred)

- Sortierung nach Name oder Größe (braucht neues Fast-Field, SCHEMA_VERSION-Sprung, Vollreindex auf Bestandsinstallationen)
- Mimetype-Gruppen aus `files.mime` statt Endung (nur bei nachgewiesenem Genauigkeitsbedarf; bricht den Kommentar "no join against files")
- Geplantes Vorwärmen nach Zeitplan
- Index-Verschlüsselung mit Key-Rotation (Pro-Schiene)
- External Storage (SMB, S3) mit ACL-Mapping (Pro-Schiene)

## Out of Scope

- Facettenzähler je Dateityp: wäre ein Zähl-Orakel vor dem Rechtefilter (T-02-93), von allen vier Recherche-Dokumenten übereinstimmend ausgeschlossen
- Personenfilter, Ordner-Einschränkung auf der Ergebnisseite
- onnxruntime-Sprung auf 1.30.0 im Feature-Fenster (löst Modellqualitäts-Gates und ARM-Wheel-Prüfung neu aus, trägt nichts bei)
- Vue/JSON-Route/Build-Schritt für die Ergebnisseite (bleibt serverseitig gerendert)
- jemalloc/mimalloc per LD_PRELOAD, psutil, APScheduler (Entladung geht mit Stdlib)
- Alles aus dem PROJECT.md-Out-of-Scope (Elasticsearch, RAG/Chat, Cloud-Embeddings, fremde Quellen, eigenes MCP-Tool, Typesense)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FILT-01 | Phase 13 | Complete |
| FILT-02 | Phase 13 | Complete |
| FILT-03 | Phase 13 | Complete |
| FILT-04 | Phase 13 | Complete |
| FILT-05 | Phase 13 | Complete |
| MEM-01 | Phase 14 | Complete |
| MEM-02 | Phase 14 | Pending (gebaut in 14-04 bis 14-07, Messgroesse in 14-11 festgeschrieben; der Beleg an der Messgroesse entsteht auf der Box der Phase 15) |
| MEM-03 | Phase 14 | Complete (14-08) |
| MEM-04 | Phase 14 | Complete (14-02) |
| MEM-05 | Phase 14 | Complete (14-09 die Admin-Seite, 14-10 die Zusage und ihr Gate; Wortwahl vom Owner am 19.09.2026 entschieden) |
| MESS-04 | Phase 12 | Complete |
| MESS-05 | Phase 15 | Pending |
| MESS-06 | Phase 12 | Complete |
| HART-01 | Phase 16 | Pending |
| HART-02 | Phase 16 | Pending |
| HART-03 | Phase 12 | Complete |
| REL-02 | Phase 16 | Pending |

**Abdeckung:** 17 von 17 Requirements zugeordnet, keine Waise, keine Doppelzuordnung.

**Zuordnungs-Anmerkungen:**

- HART-03 (stable35-Fenster) liegt thematisch bei der Härtung, ist aber Phase 12 zugeordnet, weil die Frist der 16.09.2026 ist, also zwei Tage nach Milestone-Start. Das Ergebnis fließt in Phase 16 in die Release-Entscheidung ein, ohne dort noch einmal als eigene Anforderung zu zählen.
- MESS-06 (Cron-Protokoll, Vergleichbarkeitsbedingungen) ist Phase 12 zugeordnet, weil es Runbook- und Werkzeugarbeit ist; die Anwendung erfolgt im Messlauf der Phase 15 und ist dort Bestandteil von Erfolgskriterium 2.
- FILT-01 bis FILT-05 sind end-to-end formuliert (Backend-Feld plus Oberfläche plus Parität) und liegen deshalb geschlossen in Phase 13, mit verbindlicher Planreihenfolge Backend vor PHP.
