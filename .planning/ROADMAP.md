# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Messbeleg und Ausbau** -- Shipped 2026-09-21 (Phasen 12 bis 16, Archiv: .planning/milestones/v1.2-ROADMAP.md)
- [x] **v1.3 Sprachausbau** -- Shipped 2026-09-27 (Phasen 17 bis 23, Archiv: .planning/milestones/v1.3-ROADMAP.md)

## Phases

<details>
<summary>v1.0 Volltext, OCR und semantische Suche (Phasen 1-6 + 06.1) -- SHIPPED 2026-09-07</summary>

Details im Archiv: .planning/milestones/v1.0-ROADMAP.md (103 Plaene, Store-Einreichung 1.0.0, Tags v1.0.0 bis v1.0.3)

</details>

<details>
<summary>v1.1 Qualitaet und Effizienz (Phasen 7-11) -- SHIPPED 2026-09-11</summary>

- [x] Phase 7: Gemeinsame Embedding-Engine (4/4 Plaene) -- completed 2026-09-08
- [x] Phase 8: Deutsche Komposita ohne Behelf (5/5 Plaene) -- completed 2026-09-08
- [x] Phase 9: Eigene Ergebnisseite (8/8 Plaene) -- completed 2026-09-09
- [x] Phase 10: Vergleichsmessung auf der AWS-Box (7/7 Plaene) -- completed 2026-09-10
- [x] Phase 11: Haertung und Store-Einreichung v1.1 (13/13 Plaene) -- completed 2026-09-11

Details im Archiv: .planning/milestones/v1.1-ROADMAP.md

</details>

<details>
<summary>v1.2 Messbeleg und Ausbau (Phasen 12-16) -- SHIPPED 2026-09-21</summary>

- [x] Phase 12: Messwerkzeug, Runbook und Terminentscheid (8/8 Plaene) -- completed 2026-09-16
- [x] Phase 13: Filter und Sortierung auf der Ergebnisseite (13/13 Plaene) -- completed 2026-09-19
- [x] Phase 14: Modell-Entladung im Leerlauf (12/12 Plaene) -- completed 2026-09-19
- [x] Phase 15: Messphase, eine Box-Anfahrt (16/16 Plaene) -- abgenommen 2026-09-21, Auflagen A1 bis A4 an Phase 16
- [x] Phase 16: Haertung und Store-Einreichung v1.2.0 (14/14 Plaene) -- completed 2026-09-21, v1.2.0 im Store (2x HTTP 201)

Details im Archiv: .planning/milestones/v1.2-ROADMAP.md

</details>

<details>
<summary>v1.3 Sprachausbau (Phasen 17-23) -- SHIPPED 2026-09-27</summary>

- [x] Phase 17: Owner-Tor und Analyseketten (8/8 Plaene) -- completed 2026-09-23
- [x] Phase 18: Schema, Marken und Umbauweg (12/12 Plaene) -- completed 2026-09-24
- [x] Phase 19: Frageseite freischalten (9/9 Plaene) -- completed 2026-09-25
- [x] Phase 20: UI-Kataloge es/it/nl/pt (9/9 Plaene) -- completed 2026-09-25
- [x] Phase 21: Niederlaendische Komposita (9/9 Plaene) -- completed 2026-09-25
- [x] Phase 22: Messanfahrt BL-F03 (13/13 Plaene) -- completed 2026-09-26
- [x] Phase 23: Haertung und Store-Einreichung 1.3.0 (9/9 Plaene) -- completed 2026-09-27, v1.3.0 im Store (2x HTTP 201)

Details im Archiv: .planning/milestones/v1.3-ROADMAP.md

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7-11 (Archiv) | v1.1 | 37/37 | Complete | 2026-09-11 |
| 12-16 (Archiv) | v1.2 | 63/63 | Complete | 2026-09-21 |
| 17-23 (Archiv) | v1.3 | 69/69 | Complete | 2026-09-27 |

## Nach v1.3 (Wiedervorlage)

Offene Punkte, die bewusst NICHT in v1.3 lagen (Kandidaten fuer v1.4 und spaeter; v1.4-Fokus laut Owner-Linie: BL-F04 SPEED, Vorarbeit-Research und Basiszahlen liegen vor):

- Franzoesisches Koerperfeld (FR hat OCR und Katalog, aber keine lexikalische Kette; v1.4-Kandidat)
- Getrennte pt_BR/pt_PT-Wortlaute fuer die Suche selbst
- Niederlaendische Betonungsakzente als eigene `custom_stopword`-Liste
- Sortierung nach Name oder Groesse (Fast-Field, SCHEMA_VERSION-Sprung; koennte kuenftig mit einem ohnehin faelligen Umbau reisen)
- Mimetype-Gruppen aus `files.mime`, geplantes Vorwaermen
- Pro-Schiene (Index-Verschluesselung, External Storage; ISV-Entscheid 03.11.)
- Estnisch/Daenisch lexikalisch nicht moeglich (tantivy kennt keinen estonian-Stemmer): muss aktiv an die Buerokratt/OS2ai-Outreach-Spur kommuniziert werden, bevor dort falsche Erwartungen entstehen
- Snapshot `snap-03f1d1d9ad9262704`: Wiedervorlage beim Milestone-Close (Stand 27.09.: bleibt im Standard-Tier, dritter Behalten-Entscheid, ~2,85 USD/Monat; naechste Wiedervorlage beim v1.4-Close)
- Deferred aus Phase 23: F-23-04 (v1.4-Backlog), idle-Guard EmbeddingModel.release() (v1.4), IN-01..03 dokumentiert

Aktiver Blocker unabhaengig vom Milestone: Kill-Kriterium Nextcloud Conference (kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet; geprueft 21.09.2026, nicht ausgeloest).

---
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11. v1.2 archiviert: 2026-09-21. v1.3 archiviert: 2026-09-27.*
