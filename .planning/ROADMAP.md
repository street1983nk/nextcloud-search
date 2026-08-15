# Roadmap: Findling (Nextcloud Zero-Config-Suche)

## Overview

Findling entsteht in sechs Phasen, die dem Prinzip "unbewiesenstes Stück zuerst, teuerstes zuletzt" folgen. Phase 1 entkräftet das einzige Integrationsrisiko ohne Vorbild im Ökosystem: eine PHP-Companion-App registriert einen `IProvider` und holt sich Treffer per `exAppRequest` aus dem Container. Erst wenn ein Treffer nachweislich in der Unified Search steht, wird der Indexkern gebaut (Phase 2), inklusive ACL-Tabelle im allerersten Storage-Schema, weil Berechtigungen eine Sicherheitseigenschaft sind und sich nicht nachrüsten lassen. Phase 3 hält den Index aktuell und erfasst gescannte Dokumente per OCR. Phase 4 macht den Betriebszustand für den Admin sichtbar, was nach dem stillen Sterben des Vorgängers das eigentliche Produktversprechen ist. Phase 5 beweist die Betriebsversprechen auf echter 4-GB-ARM-Hardware und reicht v1.0 (Volltext + OCR) vor Jahresende 2026 im App Store ein. Phase 6 zieht die semantische Suche als eigenständiges Release v1.1 nach, 4 bis 6 Wochen später, auf einem Schema, das von Tag eins embedding-fähig geschnitten ist.

Der Schnitt ist vertikal: jede Phase liefert eine end-to-end nutzbare Fähigkeit, keine technische Schicht. Scope-Kürzung schlägt Termin, das harte Ziel ist die v1.0-Store-Einreichung vor Jahresende 2026.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Integrationsbeweis** - Ein Treffer aus dem Container erscheint in der Unified Search, App-IDs eingefroren, beide CSRs eingereicht
- [ ] **Phase 2: Indexkern und Volltextsuche** - Dateien werden vollständig, wiederaufsetzbar und rechtekorrekt durchsuchbar
- [ ] **Phase 3: Aktualität und OCR** - Neue, geänderte und gescannte Dokumente sind kurz darauf auffindbar, ohne dass eine Datei angefasst wird
- [ ] **Phase 4: Admin-Sichtbarkeit und Diagnose** - Admin sieht Deckungsgrad, Fehler und den Grund pro Datei, bevor Nutzer etwas vermissen
- [ ] **Phase 5: Härtung und Store-Einreichung v1.0** - Belegte Zahlen auf 4-GB-ARM, Rechte-Paritätstest als Dauergate, v1.0 im App Store
- [ ] **Phase 6: Semantische Suche (Release v1.1)** - Hybrid-Ranking findet Umschreibungen, im selben RAM-Budget und derselben ACL-Kette

## Phase Details

### Phase 1: Integrationsbeweis
**Goal**: Ein Suchtreffer, den der ExApp-Container liefert, erscheint nachweislich in der normalen Nextcloud-Unified-Search, und die Store-Identität steht unwiderruflich fest.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: COMP-01, COMP-02, IDX-07, PKG-01, PKG-02
**Success Criteria** (what must be TRUE):
  1. Nutzer tippt einen Suchbegriff in die Nextcloud-Suchleiste und sieht einen Findling-Treffer, den der Container erzeugt hat (Web-UI und OCS-Client, über `IProvider`, nicht `IExternalProvider`)
  2. Der Container liest den Inhalt einer konkreten Datei über den `#[ExAppRequired]`-Endpunkt der PHP-App als Stream, und ein Nutzer ohne Recht auf diese Datei bekommt dabei nichts geliefert
  3. Das Multi-Arch-Image (amd64 + arm64, Debian-slim-Basis) baut in der CI durch und startet auf beiden Architekturen bis zum erfolgreichen AppAPI-Handshake
  4. Beide App-IDs (`findling` ExApp + Companion) sind eingefroren und beide CSR-Vorgänge sind eingereicht, bevor der erste Bau-Commit der Folgephase entsteht
  5. Das CI-Gate für die Nur-Lesen-Invariante ist aktiv: ein Testlauf über ein Referenzkorpus belegt per Prüfsumme, dass keine Nutzerdatei verändert wurde
**Plans**: 8 plans

Plans:
- [ ] 01-01-PLAN.md , Identitaets-Freeze und Repo-Grundgeruest
- [ ] 01-02-PLAN.md , Qualitaetsgates, Nur-Lesen-Gate A und rote Kanarienprobe
- [ ] 01-03-PLAN.md , CSR-Vorgaenge fuer beide App-IDs
- [ ] 01-04-PLAN.md , ExApp-Kanarienvogel: POST /search mit Container-Beweis
- [ ] 01-05-PLAN.md , PHP-Companion: IProvider, Proxy-Guard, Content-Gateway
- [ ] 01-06-PLAN.md , Durchstich gruen und Sichtprobe des Owners
- [ ] 01-07-PLAN.md , Multi-Arch-Image, HaRP und Store-Metadaten
- [ ] 01-08-PLAN.md , Content-Gateway-Beweis und Pruefsummen-Gate B

### Phase 2: Indexkern und Volltextsuche
**Goal**: Der Nutzer findet den Inhalt seiner Dokumente per Volltextsuche mit deutscher Sprachqualität, und der Erstindex überlebt jeden Abbruch.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: COMP-04, IDX-01, IDX-02, IDX-03, IDX-06, IDX-08, SRCH-01, SRCH-02, SRCH-03
**Success Criteria** (what must be TRUE):
  1. Nutzer sucht nach einem Wort aus einem PDF- oder Office-Dokument und bekommt das Dokument mit hervorgehobenem Snippet zurück, inklusive deutschem Stemming, Stopwörtern und Umlaut-Folding
  2. Nutzer bekommt ausschließlich Treffer aus Dateien, die er sehen darf: SQLite-ACL-Vorfilter liefert Kandidaten, der finale PHP-Recheck entscheidet, und Snippets entstehen erst nach bestandener Prüfung
  3. Ein `docker kill` mitten im Erstindex kostet keinen Fortschritt: nach dem Neustart setzt der Lauf an der Datenbank-Zustandsmarke fort statt neu zu beginnen
  4. Eine Datei, die zehn Nutzer sehen, wird genau einmal verarbeitet (Crawl pro Mount: User-Homes und Team Folders an, External Storage aus)
  5. Nicht indexierbare Dateien (zu groß, Typ nicht in der Allowlist) landen sichtbar in den Zuständen `failed` oder `skipped` statt stumm zu verschwinden, und Suchoperatoren (Phrase, +/-, Dateiname vs. Inhalt, Dateityp) funktionieren
**Plans**: TBD

### Phase 3: Aktualität und OCR
**Goal**: Was der Nutzer gerade ablegt, ändert, teilt oder löscht, ist kurz darauf korrekt im Index, und gescannte Dokumente sind durchsuchbar, ohne dass eine Originaldatei angefasst wird.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: COMP-03, IDX-04, IDX-05, OCR-01, OCR-02
**Success Criteria** (what must be TRUE):
  1. Nutzer lädt eine Datei hoch, benennt sie um oder verschiebt sie und findet sie kurz darauf unter ihrem neuen Zustand wieder (ein einziger Ereignisweg über die PHP-App in die Pull-Queue)
  2. Nutzer sucht nach Text aus einem gescannten PDF ohne Textlayer und findet ihn, ohne dass ein Admin OCR konfiguriert hat; Dokumente mit vorhandenem Textlayer werden extrahiert statt erneut OCR-t
  3. Entzogener Share und gelöschte Datei verschwinden zeitnah aus den Trefferlisten aller nicht mehr berechtigten Nutzer
  4. Bei komplett blockierten Events ist der Index nach einem einzigen ETag-Abgleichzyklus wieder korrekt (Abnahmetest genau so)
  5. Nach einem OCR-Lauf über ein Korpus mit defekten und ungewöhnlichen PDFs sind alle Originaldateien bitweise unverändert, und kein OCR-Job überschreitet Seitenlimit, Zeit- oder RAM-Deckel
**Plans**: TBD

### Phase 4: Admin-Sichtbarkeit und Diagnose
**Goal**: Der Admin erkennt den Zustand der Suche vor dem Nutzer, kann für jede einzelne Datei begründen, warum sie auffindbar ist oder nicht, und kennt den Aufwand vorher.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: ADM-01, ADM-02, ADM-03, ADM-04
**Success Criteria** (what must be TRUE):
  1. Admin öffnet die Statusseite und sieht Indexfortschritt, Deckungsgrad (indexierte gegen indexierbare Dateien) und die Fehlerliste, ohne Logs zu lesen
  2. Admin gibt eine beliebige Datei an und bekommt den Grund ihres Zustands genannt (zu groß, Typ nicht unterstützt, OCR fehlgeschlagen, wartet in der Queue, indexiert)
  3. Admin sieht vor dem Erstindex eine Schätzung: Anzahl Dateien, davon OCR-pflichtig, erwartete Dauer und Platzbedarf
  4. Admin schaltet Ordner-Ausschlüsse, Größen-Cap, Team Folders und External Storage um, und der nächste Lauf hält sich daran
**Plans**: TBD
**UI hint**: yes

### Phase 5: Härtung und Store-Einreichung v1.0
**Goal**: Die Betriebsversprechen sind auf echter Zielhardware belegt statt behauptet, und v1.0 (Volltext + OCR) liegt vor Jahresende 2026 im Nextcloud App Store.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: SRCH-04, PKG-03, PKG-04, PKG-05
**Success Criteria** (what must be TRUE):
  1. Ein voller Index- und OCR-Lauf auf einer echten 4-GB-ARM-Box läuft ohne OOM durch, und die gemessene RSS-Kurve ist als Store-Zahl dokumentiert
  2. Der automatisierte Paritätstest gegen die native Nextcloud-Suche ist über alle sechs Rechteszenarien grün und läuft als Dauergate in der CI (eigene Dateien, empfangener Share, entzogener Share, Team Folder, Gruppenwechsel, eingeschränkter Nutzer)
  3. Beide Apps installieren, laufen und deinstallieren sauber auf docker-compose und AIO über HaRP, auf Nextcloud 32 bis 34; Uninstall entfernt Queue-Tabellen, Preferences und nach Bestätigung das Index-Volume
  4. Beide signierten Releases mit XSD-validierter info.xml sind im App Store eingereicht, mit gekoppelter Versionierung und ausdrücklicher Privacy-Aussage im Store-Text
**Plans**: TBD

### Phase 6: Semantische Suche (Release v1.1)
**Goal**: Der Nutzer findet Dokumente auch über Umschreibungen statt nur über exakte Wörter, im selben RAM-Budget und durch dieselbe Rechtekette.
**Mode:** mvp
**Depends on**: Phase 5 (eigenständiges Release v1.1, 4 bis 6 Wochen nach der v1.0-Store-Einreichung)
**Requirements**: SEM-01, SEM-02, SEM-03
**Success Criteria** (what must be TRUE):
  1. Nutzer sucht mit einer Umschreibung, die im Dokument wörtlich nicht vorkommt, und findet es trotzdem (RRF-Hybrid aus Tantivy- und Vektor-Treffern)
  2. Vektor-Treffer durchlaufen exakt dieselbe ACL-Kette wie Volltext-Treffer: SQLite-Vorfilter, dann finaler PHP-Recheck, und der Paritätstest aus Phase 5 bleibt grün
  3. Fehlt das Modell oder fällt der Vektorzweig aus, liefert die Suche unverändert Volltext-Ergebnisse statt einen Fehler
  4. Das Vektorschema wird erst nach einem Lasttest auf mindestens 50.000 synthetischen Dokumenten festgezurrt, mit dokumentierter Kennzahl Bytes pro Dokument und beschriebenem Ausweichpfad (Bit-Vektoren/usearch)
  5. Ein voller Lauf mit aktivierten Embeddings bleibt auf der 4-GB-ARM-Box stabil (INDEX_WORKERS=1 verhindert OCR- und Embedding-Spitze gleichzeitig)
**Plans**: TBD

## Progress

**Execution Order:**
Phasen laufen in numerischer Reihenfolge: 1 → 2 → 3 → 4 → 5 → 6

**Release-Schnitt:** Phasen 1 bis 5 bilden v1.0 (Volltext + OCR, Store-Einreichung vor Jahresende 2026). Phase 6 ist Release v1.1 (Semantik), 4 bis 6 Wochen später.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Integrationsbeweis | 0/8 | Not started | - |
| 2. Indexkern und Volltextsuche | 0/TBD | Not started | - |
| 3. Aktualität und OCR | 0/TBD | Not started | - |
| 4. Admin-Sichtbarkeit und Diagnose | 0/TBD | Not started | - |
| 5. Härtung und Store-Einreichung v1.0 | 0/TBD | Not started | - |
| 6. Semantische Suche (Release v1.1) | 0/TBD | Not started | - |

## Requirement Coverage

30 von 30 v1-Requirements sind genau einer Phase zugeordnet, keine Waisen, keine Doppelungen.

| Phase | Requirements | Anzahl |
|-------|--------------|--------|
| 1 | COMP-01, COMP-02, IDX-07, PKG-01, PKG-02 | 5 |
| 2 | COMP-04, IDX-01, IDX-02, IDX-03, IDX-06, IDX-08, SRCH-01, SRCH-02, SRCH-03 | 9 |
| 3 | COMP-03, IDX-04, IDX-05, OCR-01, OCR-02 | 5 |
| 4 | ADM-01, ADM-02, ADM-03, ADM-04 | 4 |
| 5 | SRCH-04, PKG-03, PKG-04, PKG-05 | 4 |
| 6 | SEM-01, SEM-02, SEM-03 | 3 |

## Research-Flags für die Phasenplanung

Aus research/SUMMARY.md übernommen, relevant für `/gsd:plan-phase --research-phase`:

- **Phase 1**: Die Kombination `IProvider` (PHP) ruft `exAppRequest` (ExApp) hat kein Vorbild. Offen: Entfernt die Unified-Search-UI HTML aus `SearchResultEntry`, und wo liegt die reale Timeout-Obergrenze im AppAPI-Proxy.
- **Phase 2**: Zusammenführung Tantivy-Kandidaten, SQLite-ACL-Vorfilter und finaler PHP-Recheck ist ohne Präzedenzfall und braucht ein durchdachtes Interface-Design. Zusätzlich: Snippet-Offsets mit `ascii_fold()` bei Umlauten an echten deutschen Dokumenten prüfen, bevor der Analyzer festgezurrt wird.
- **Phase 5**: Reale RAM-Spitzen auf ARM sind Schätzungen (MEDIUM confidence). Messlauf gehört hierhin, bevor Worker-Defaults final sind. Ebenfalls offen: ob AIO-Borg-Sicherungen das ExApp-Volume erfassen.
- **Phase 6**: sqlite-vec ist Alpha, die 250.000-Chunk-Schwelle ist gerechnet, nicht gemessen. Benchmark vor Schema-Fixierung, plus deutsches Testset fp32 gegen int8.

Etablierte Muster, Research kann entfallen: Event-Listener und Reconcile (Phase 3, aus context_chat verifiziert), OCR-Subprozessaufruf (Phase 3), Statusseiten-Muster (Phase 4), Store-/Zertifikatsprozess (Phase 5, aus nextcloud-mcp-connector dokumentiert).

## Sequenz-Zwänge (nicht verhandelbar)

1. Der Integrationsbeweis steht zuerst. Ein spätes Scheitern an der `IProvider`-ExApp-Kombination wäre der teuerste denkbare Fehlschlag.
2. Die ACL-Tabelle gehört in das erste Storage-Schema (Phase 2). Berechtigungen nachträglich in ein Schema zu ziehen ist ein Neuschreiben, kein Feature.
3. Der Reconcile-Lauf gehört in dieselbe Phase wie die Event-Listener (Phase 3), sonst wird er in der Praxis nie gebaut.
4. Semantik (SEM-*) ist ein eigener Block nach der v1.0-Store-Einreichung. Sie bringt eine neue Tabelle, einen neuen Retrieval-Zweig und die größte Hardwareabhängigkeit mit, das gehört auf einen erprobten Unterbau.
5. Die v1.0-Store-Einreichung vor Jahresende 2026 ist das harte Ziel. Scope-Kürzung schlägt Termin.
6. Kill-Kriterium bleibt aktiv: Kündigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet (Nextcloud Conference September beobachten).

---
*Created: 2026-08-15*
