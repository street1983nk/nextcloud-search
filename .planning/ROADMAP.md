# Roadmap: Findling (Nextcloud Zero-Config-Suche)

## Overview

Findling entsteht in sechs Phasen, die dem Prinzip "unbewiesenstes Stück zuerst, teuerstes zuletzt" folgen. Phase 1 entkräftet das einzige Integrationsrisiko ohne Vorbild im Ökosystem: eine PHP-Companion-App registriert einen `IProvider` und holt sich Treffer per `exAppRequest` aus dem Container. Erst wenn ein Treffer nachweislich in der Unified Search steht, wird der Indexkern gebaut (Phase 2), inklusive ACL-Tabelle im allerersten Storage-Schema, weil Berechtigungen eine Sicherheitseigenschaft sind und sich nicht nachrüsten lassen. Phase 3 hält den Index aktuell und erfasst gescannte Dokumente per OCR. Phase 4 macht den Betriebszustand für den Admin sichtbar, was nach dem stillen Sterben des Vorgängers das eigentliche Produktversprechen ist. Phase 5 beweist die Betriebsversprechen auf echter 4-GB-ARM-Hardware und reicht v1.0 (Volltext + OCR) vor Jahresende 2026 im App Store ein. Phase 6 zieht die semantische Suche als eigenständiges Release v1.1 nach, 4 bis 6 Wochen später, auf einem Schema, das von Tag eins embedding-fähig geschnitten ist.

Der Schnitt ist vertikal: jede Phase liefert eine end-to-end nutzbare Fähigkeit, keine technische Schicht. Scope-Kürzung schlägt Termin, das harte Ziel ist die v1.0-Store-Einreichung vor Jahresende 2026.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Integrationsbeweis** - Ein Treffer aus dem Container erscheint in der Unified Search, App-IDs eingefroren, beide CSRs eingereicht
 (completed 2026-08-15)

- [x] **Phase 2: Indexkern und Volltextsuche** - Dateien werden vollständig, wiederaufsetzbar und rechtekorrekt durchsuchbar
 (completed 2026-09-01)

- [x] **Phase 3: Aktualität und OCR** - Neue, geänderte und gescannte Dokumente sind kurz darauf auffindbar, ohne dass eine Datei angefasst wird (completed 2026-09-01)
- [ ] **Phase 4: Admin-Sichtbarkeit und Diagnose** - Admin sieht Deckungsgrad, Fehler und den Grund pro Datei, bevor Nutzer etwas vermissen (alle 10 Plaene ausgefuehrt, Verifikation steht aus)
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

- [x] 01-01-PLAN.md , Identitaets-Freeze und Repo-Grundgeruest
- [x] 01-02-PLAN.md , Qualitaetsgates, Nur-Lesen-Gate A und rote Kanarienprobe
- [x] 01-03-PLAN.md , CSR-Vorgaenge fuer beide App-IDs
- [x] 01-04-PLAN.md , ExApp-Kanarienvogel: POST /search mit Container-Beweis
- [x] 01-05-PLAN.md , PHP-Companion: IProvider, Proxy-Guard, Content-Gateway
- [x] 01-06-PLAN.md , Durchstich gruen und Sichtprobe des Owners
- [x] 01-07-PLAN.md , Multi-Arch-Image, HaRP und Store-Metadaten
- [x] 01-08-PLAN.md , Content-Gateway-Beweis und Pruefsummen-Gate B

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

**Plans**: 14 plans

Plans:
**Wave 1**

- [x] 03-01-PLAN.md , Ereignisweg und Job-Art in der Queue (Upload und Aenderung sind sofort findbar)
- [x] 03-05-PLAN.md , tesseract im Image, OCR-Messlauf und OCR-Konfiguration

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md , Umbenennen und Verschieben ohne Download (Metadaten-Job)
- [x] 03-06-PLAN.md , DACH- und Scan-Korpus, Textlayer-Schwelle nachgemessen

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-03-PLAN.md , Loeschen, Papierkorb und Wiederherstellen

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-04-PLAN.md , Share, Unshare und Teilbaum-Job fuer Ordner-Operationen
- [x] 03-08-PLAN.md , OCR-Modul: Rasterung, tesseract-Subprozess, Deckel-Kaskade

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 03-07-PLAN.md , Requeue-Route, Gate A und die OCR-Zweitspur

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 03-09-PLAN.md , Verdrahtung: gescanntes PDF ist auffindbar
- [x] 03-11-PLAN.md , Abgleich-Leseweg: mounts und files/slice

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 03-10-PLAN.md , Bilder per OCR plus Allowlist-Paritaets-Gate
- [x] 03-12-PLAN.md , Abgleichlauf mit Ruhe-Gate, Tombstones und Cursor

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 03-14-PLAN.md , Verschobene Audit-Befunde aus Phase 2

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 03-13-PLAN.md , Abnahmen als Dauergates plus Sichtprobe

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

**Plans**: 10 plans
**UI hint**: yes

Plans:
**Wave 1**

- [x] 04-01-PLAN.md , Gate B lernt zwei Routenklassen; CI sieht php/templates und den settings-Block
- [x] 04-02-PLAN.md , Container-Statusvertrag: sechs neue Zahlen, Docblock-Widerspruch aufgeloest

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-03-PLAN.md , Die Sektion Findling erscheint und zeigt den Betriebszustand (ADM-01)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-04-PLAN.md , Deckungsgrad als Bruch mit benanntem Nenner, Scan-Zaehler im Crawl (ADM-01)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 04-05-PLAN.md , Vorab-Schaetzung ab Minute 1 plus rates-Route (ADM-03)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 04-06-PLAN.md , Fehlerliste mit lesbaren Pfaden und Abhilfe je Grund (ADM-01)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 04-07-PLAN.md , Pro-Datei-Diagnose, diagnose-Route und Sechs-Stufen-Vorrangregel (ADM-02)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 04-08-PLAN.md , Regeln und Grenzen: vier Schalter, ein Pfadraum, Durchsetzung an der Quelle (ADM-04)

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 04-09-PLAN.md , Ausschluss raeumt Bestand, excluded in drei Listen, Inline-Bestaetigung (ADM-04)

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 04-10-PLAN.md , occ-Zweitzugang, Betriebsdokumentation, Gate-Lauf und Sichtprobe

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

**Lesart von Kriterium 4** (Owner-Entscheid D-09 vom 03.09.2026, festgehalten in 05-CONTEXT.md): Kriterium 4 gilt für Phase 5 als "einreichungsbereit", also signierte, XSD-validierte Release-Artefakte beider Apps plus fertige Store-Texte und der Tag v1.0.0 (D-26). Die tatsächliche Abgabe erfolgt gebündelt mit der Semantik nach Phase 6 (D-08), Fallback gestaffelt nach D-10. Kriterium 3 deckt zusätzlich Nextcloud 35 ab (D-23).

**Plans**: 19 plans

Plans:
**Wave 1**

- [x] 05-01-PLAN.md , HaRP: der echte Installationsweg, install und run
- [x] 05-02-PLAN.md , Ein Disable verliert nichts, ein Purge raeumt alles (PKG-04)
- [x] 05-03-PLAN.md , Endgueltige Aufgabe-Regel und zwei Durchsatzposten vor dem Volllauf
- [x] 05-04-PLAN.md , Bildzweig und Ordner-Wiederherstellung
- [x] 05-05-PLAN.md , Lastkorpus-Generator, RSS-Sampler und Box-Skript
- [x] 05-06-PLAN.md , Audit-Kleinreste in Container und PHP-Haelfte (D-20)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-07-PLAN.md , Lockstep-Version: beide Haelften nennen und pruefen ihre Version (D-11)
- [x] 05-08-PLAN.md , Uninstall auf dem echten Weg, NC 32 bis 35, Teilentfernung (PKG-03, PKG-04)
- [x] 05-09-PLAN.md , Sichtbarkeits-Paritaet ueber sechs Szenarien als Dauergate (SRCH-04)
- [ ] 05-10-PLAN.md , Die Miet-Box: Voraussetzungen, Bestellung, AIO ueber HaRP, Grundlast

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-11-PLAN.md , Phase-4-Erbe: Skip-Verdikte und Versionsmarken (D-19)
- [ ] 05-12-PLAN.md , Trockenlauf, gemessener OCR-Faktor und der Grenzwert
- [x] 05-13-PLAN.md , CI-Haertung: Digest-Smoke, Pin-Gate, Deadlines, Postgres-Dauergate

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 05-14-PLAN.md , ARM-Volllauf, Stoerfall-Drills, Messbericht, Box-Abbau
- [x] 05-15-PLAN.md , PHPUnit-Suite: Geruest und die ersten sechs Verhaltensweisen (D-24)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 05-16-PLAN.md , PHPUnit-Suite: die restlichen sechs Verhaltensweisen (D-24)
- [ ] 05-17-PLAN.md , Store-Metadaten dreisprachig, 1.0.0, Privacy, Textgate (PKG-05)

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 05-18-PLAN.md , Store-Medien, Release-Job, signierte Artefakte

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 05-19-PLAN.md , Abnahme: Gastnutzer-Probe, Gate-Landschaft, Tag v1.0.0

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
| 1. Integrationsbeweis | 8/8 | Complete    | 2026-08-15 |
| 2. Indexkern und Volltextsuche | 14/14 | Complete   | 2026-09-01 |
| 3. Aktualität und OCR | 14/14 | Complete   | 2026-09-01 |
| 4. Admin-Sichtbarkeit und Diagnose | 10/10 | Verification pending |  |
| 5. Härtung und Store-Einreichung v1.0 | 12/19 | In Progress|  |
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
