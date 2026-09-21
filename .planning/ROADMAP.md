# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Messbeleg und Ausbau** -- Shipped 2026-09-21 (Phasen 12 bis 16, Archiv: .planning/milestones/v1.2-ROADMAP.md)

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

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv v1.0) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7. Gemeinsame Embedding-Engine | v1.1 | 4/4 | Complete | 2026-09-08 |
| 8. Deutsche Komposita ohne Behelf | v1.1 | 5/5 | Complete | 2026-09-08 |
| 9. Eigene Ergebnisseite | v1.1 | 8/8 | Complete | 2026-09-09 |
| 10. Vergleichsmessung auf der AWS-Box | v1.1 | 7/7 | Complete | 2026-09-10 |
| 11. Haertung und Store-Einreichung v1.1 | v1.1 | 13/13 | Complete | 2026-09-11 |
| 12. Messwerkzeug, Runbook und Terminentscheid | v1.2 | 8/8 | Complete    | 2026-09-16 |
| 13. Filter und Sortierung auf der Ergebnisseite | v1.2 | 13/13 | Complete | 2026-09-19 |
| 14. Modell-Entladung im Leerlauf | v1.2 | 12/12 | Complete | 2026-09-19 |
| 15. Messphase, eine Box-Anfahrt | v1.2 | 16/16 | Complete | 2026-09-21 |
| 16. Haertung und Store-Einreichung v1.2.0 | v1.2 | 14/14 | Complete | 2026-09-21 |

## Nach v1.2 (Wiedervorlage)

Offene Punkte, die bewusst NICHT in v1.2 liegen:

- Snapshot-Wiedervorlage `snap-03f1d1d9ad9262704` nach v1.2 (loeschen oder Archive-Tier, rund 2,9 USD/Monat)
- Sortierung nach Name oder Groesse (neues Fast-Field, SCHEMA_VERSION-Sprung, Vollreindex auf Bestandsinstallationen)
- Mimetype-Gruppen aus `files.mime` statt Endung, nur bei nachgewiesenem Genauigkeitsbedarf
- Geplantes Vorwaermen nach Zeitplan
- Index-Verschluesselung mit Key-Rotation und External Storage (SMB, S3) mit ACL-Mapping, beide Pro-Schiene
- Aufraeumbefunde aus der Recherche: `fastembed==0.8.0` gepinnt aber nirgends importiert, `numpy` als indirekte, nicht deklarierte Abhaengigkeit
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht

Aktiver Blocker unabhaengig vom Milestone: Kill-Kriterium Nextcloud Conference September (kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet).

---
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11. v1.2 archiviert: 2026-09-21.*
