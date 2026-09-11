# Roadmap: Findling

## Milestones

- [x] **v1.0 Volltext, OCR und semantische Suche** -- Shipped 2026-09-07 (Phasen 1-6 + 06.1, Archiv: .planning/milestones/v1.0-ROADMAP.md)
- [x] **v1.1 Qualitaet und Effizienz** -- Shipped 2026-09-11 (Phasen 7 bis 11, Archiv: .planning/milestones/v1.1-ROADMAP.md)

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

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-6 + 06.1 (Archiv v1.0) | v1.0 | 103/103 | Complete | 2026-09-07 |
| 7. Gemeinsame Embedding-Engine | v1.1 | 4/4 | Complete | 2026-09-08 |
| 8. Deutsche Komposita ohne Behelf | v1.1 | 5/5 | Complete | 2026-09-08 |
| 9. Eigene Ergebnisseite | v1.1 | 8/8 | Complete | 2026-09-09 |
| 10. Vergleichsmessung auf der AWS-Box | v1.1 | 7/7 | Complete | 2026-09-10 |
| 11. Haertung und Store-Einreichung v1.1 | v1.1 | 13/13 | Complete | 2026-09-11 |

## Naechster Milestone

Noch nicht geplant (Start ueber /gsd:new-milestone). Uebergeben aus v1.1:

- DI-10-02/DI-11-01: Sprachfall-Messung ohne 52.111er-Fremdbestand (Vorpruefung misst Routen-Treffer, Deckel 26 < Schwelle 64)
- DI-10-04: GEKLAERT UND GEFIXT am 11.09.2026 (Zulauf-Hunger, 5,85 h ohne Vorrat; Top-up-Route + Scheiben-Lock, Commit 1d47563, alle 6 Workflows gruen). OFFEN bleibt nur der Wirkungsbeleg: ein Volllauf gegen den Korpus-Snapshot auf m7g.large. Owner-Entscheid 11.09.: KEINE eigene Anfahrt dafuer, sondern gebuendelt mit der Laststufen-Untersuchung in EINER Box-Anfahrt der v1.2-Messphase (Deckel-Vorschlag 26 h / 3,50 USD; zugleich Erstvollzug des Wiederaufbau-Runbooks)
- DI-11-02/03/05/06 (u.a. flatternder pgsql-Ast HTTP 423: bei rot erst wiederholen)
- Entscheidung zu den vier regressiven Laststufen (hingenommen fuer v1.1.0, untersucht in der v1.2-Messplanung; dieselbe Box-Anfahrt wie der DI-10-04-Wirkungsbeleg, siehe oben)
- Snapshot-Wiedervorlage snap-03f1d1d9ad9262704 nach v1.2 (loeschen oder Archive-Tier, ~2,9 USD/Monat)
- stable35-RE-CHECK am 16.09.2026 (NC-Versionsfenster, Entscheid v2-a)
- Wiederaufbau-Runbook der Messumgebung

---
*Created: 2026-09-08. v1.1 archiviert: 2026-09-11.*
