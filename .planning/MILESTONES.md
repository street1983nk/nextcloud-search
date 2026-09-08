# Project Milestones: Findling (Nextcloud Zero-Config-Suche)

## v1.0 Volltext, OCR und semantische Suche (Shipped: 2026-09-07)

**Delivered:** Findling 1.0.0 im Nextcloud App Store: Zero-Config-Suche (Volltext + OCR + Semantik) als ExApp-Paar, Treffer in der Unified Search, komplett on-prem.

**Phases completed:** 1 bis 6 + 06.1 (103 Plaene, 102 Summaries; 05-19 ersetzt durch 06.1-15)

**Key accomplishments:**
- Praezedenzlose Kombination IProvider + exAppRequest-Proxy bewiesen und im Store (zwei signierte Apps)
- Tantivy-Index mit deutschem Stemming, SQLite-ACL-Vorfilter, finaler PHP-Recheck als Sicherheitsgrenze
- OCR strikt index-only, Semantik mit Distanzriegel + Einwortregel, 7 deutsche Sprachfaelle in CI
- Betriebsversprechen auf Zielhardware belegt: 51.961 Docs auf 4 GB/arm64, anon-Spitze 1.838 MB, 0 failed
- Launch-Haertung 06.1 (24 Plaene): Resilience-Ratsche, HaRP-Drift-Probe, drei Audits, Fremdinstallation

**Stats:**
- 7 Phasen, 103 Plaene
- 24 Tage von Projektstart (15.08.2026) bis Store (07.09.2026)
- Git range: fc4e7e5 -> 1c737e6 (Tags v1.0.0 bis v1.0.3)

**Known deferred items at close:** 2 Debug-Sessions (siehe STATE.md Deferred Items)

**What's next:** v1.1 Qualitaet + Effizienz (gemeinsame Embedding-Engine, Komposita-Wortliste, Ergebnisseite, Vergleichsmessung auf der AWS-Box)

---
