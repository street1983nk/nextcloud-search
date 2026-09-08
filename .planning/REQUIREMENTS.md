# Requirements: Findling v1.1 "Qualitaet und Effizienz"

Fortsetzung der ID-Vergabe aus v1.0 (Archiv: .planning/milestones/v1.0-REQUIREMENTS.md).
Neue Kategorien: EFF (Effizienz), QUAL (Suchqualitaet), UI (Ergebnisseite), MESS (Messung), REL (Release).

## v1.1 Requirements

### Effizienz

- [x] **EFF-01**: Suche und Indexer nutzen eine gemeinsame Embedding-Engine-Instanz; das Modell wird pro Prozess hoechstens einmal geladen (v1.0-Befund: zweite Instanz kostet ~276 MB RSS dauerhaft) (belegt in docs/performance.md, Abschnitt "Die eine Engine", mit Zaehler load_count() und CI-Tor findling.tools.one_load)
- [x] **EFF-02**: Die erste semantische Suche nach Leerlauf haelt das p95-Suchbudget von 2,5 s weiterhin ein (kein Kaltstart-Rueckschritt durch die gemeinsame Engine) (belegt in docs/performance.md, Abschnitte "Die erste Suche nach einem Containerstart" und "Die amd64-Zahl": gemessen auf arm64, der Zielhardware, mit 1.332,1 ms p95 gegen 2.500 ms ueber den OCS-Weg; die amd64-Entsprechung ueber denselben Weg misst seit Plan 07-02 jeder Lauf von integration.yml, ihre Zahl wird nach dem ersten Lauf auf main nachgetragen, offen als DI-07-01)

### Suchqualitaet

- [ ] **QUAL-01**: Deutsche Komposita werden ueber eine lizenzkonforme Wortliste zerlegt (Tantivy split_compound); die Lizenz der Liste ist AGPL-kompatibel und dokumentiert
- [ ] **QUAL-02**: Suchen nach Teilwoertern finden zusammengesetzte Woerter, belegt durch Testfaelle im CI-Sprachfall-Set (z. B. "Vereinbarung" findet "Pachtvereinbarung"); das frueher hier genannte Beispiel "Genehmigung" findet "Baugenehmigung" ist gemessen nicht baubar und steht als benannte Grenze in docs/german-analyzer.md (Owner-Entscheid a vom 08.09.2026)
- [ ] **QUAL-03**: Der offene Endungsvergleich der Verdikte gegen den Generator (v1.0-Messbericht "Was noch fehlt") ist durchgefuehrt und dokumentiert; Befunde fliessen als Testfaelle ein

### Ergebnisseite

- [ ] **UI-01**: Nutzer koennen aus der Unified Search auf eine eigene Findling-Ergebnisseite wechseln, die alle Treffer mit Paginierung zeigt
- [ ] **UI-02**: Nutzer koennen von der Ergebnisseite einen Treffer oeffnen und zurueckkehren, ohne die Trefferliste zu verlieren
- [ ] **UI-03**: Die Ergebnisseite respektiert dieselbe Berechtigungsgrenze wie die Unified Search (ACL-Vorfilter + finaler PHP-Recheck, keine neue Sicherheitsflaeche)

### Messung

- [ ] **MESS-01**: Ein Vergleichslauf auf der AWS-Box (vorhandener v1.0-Korpus, 51.961 Docs) belegt die RSS-Ersparnis der gemeinsamen Engine gegen die v1.0-Baseline (docs/measurements)
- [ ] **MESS-02**: Der Vergleichslauf zeigt keine Regression: p95-Suchlatenz und die 10 deutschen CI-Sprachfaelle bleiben im v1.0-Rahmen
- [ ] **MESS-03**: Der Messbericht liegt in docs/measurements mit identischer Struktur wie der v1.0-Bericht (vergleichbar Zeile fuer Zeile)

### Release

- [ ] **REL-01**: v1.1 ist im Nextcloud App Store eingereicht (beide Apps, signiert, Store-Texte nach der Kurztext-Regel, Entwurf vor Einreichung dem Owner gezeigt)

## Future Requirements

- Modell-Entladung nach Leerlauf (Alternative zu EFF-01, nur falls die gemeinsame Engine nicht reicht)
- Dateityp-Filter und Sortierung auf der Ergebnisseite
- Index-Verschluesselung (dokumentierte v1-Luecke)
- External Storage (bewusst aus v1.0 ausgeschlossen)

## Out of Scope

- Kein eigenes MCP-Tool gegen den Index (Threat-Model beider Produkte: Unified Search bleibt die einzige Berechtigungsgrenze)
- Keine neuen Sprachen ueber DE+EN hinaus
- Kein Pro-/Bezahl-Feature in v1.1 (ISV-Spur laeuft separat)

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| EFF-01 | Phase 7 | Done |
| EFF-02 | Phase 7 | Done |
| QUAL-01 | Phase 8 | Pending |
| QUAL-02 | Phase 8 | Pending |
| QUAL-03 | Phase 8 | Pending |
| UI-01 | Phase 9 | Pending |
| UI-02 | Phase 9 | Pending |
| UI-03 | Phase 9 | Pending |
| MESS-01 | Phase 10 | Pending |
| MESS-02 | Phase 10 | Pending |
| MESS-03 | Phase 10 | Pending |
| REL-01 | Phase 11 | Pending |

12 von 12 Requirements zugeordnet, keine Waisen, keine Doppelungen.
Phasen 7 bis 11 stehen in .planning/ROADMAP.md.
