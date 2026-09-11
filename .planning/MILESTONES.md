# Project Milestones: Findling (Nextcloud Zero-Config-Suche)

## v1.1 Qualitaet und Effizienz (Shipped: 2026-09-11)

**Delivered:** Findling 1.1.0 im Nextcloud App Store: 85 Prozent weniger Grundlast (691,8 auf 103,2 MB), deutsche Komposita-Zerlegung ueber eine lizenzgeklaerte Wortliste, eigene Ergebnisseite mit Paginierung, vollstaendiger franzoesischer Katalog, alles belegt durch eine Vergleichsmessung gegen die v1.0-Baseline auf derselben Zielhardware.

**Phases completed:** 7 bis 11 (5 Phasen, 37 Plaene, 75 Tasks)

**Key accomplishments:**

- Gemeinsame Embedding-Engine: Grundlast im Leerlauf von 691,8 auf 103,2 MB (minus 588,6 MB), Kaltstart im p95-Budget, Engine-Zustand in der Diagnose sichtbar
- Deutsche Komposita ohne Prefix-Behelf: split_compound mit wngerman-Wortliste (GPL-2+, 276.496 Eintraege), CI-Sprachfaelle die ohne Splitter rot werden, Wortlisten-Digest erzwingt Reindex
- Eigene Ergebnisseite: alle Treffer mit Paginierung, Rueckkehr ohne Listenverlust, dieselbe Berechtigungsgrenze wie die Unified Search (Paritaetstest deckt die Route mit ab)
- Vergleichsmessung auf der AWS-Box: 52.111 Dokumente ohne OOM, 19 Berichtsabschnitte Zeile fuer Zeile neben der v1.0-Baseline, inklusive der 13 Zahlen die nicht besser wurden (Laufzeit +40,9 Prozent benannt statt weggelassen)
- Store-Einreichung v1.1.0 mit Upgrade-Beweis 1.0.3 auf 1.1.0 Ende zu Ende in CI (dabei echten Produktfehler stumme-Suche-nach-Minor-Upgrade gefunden und per Migration gefixt), FR-Katalog 174 Schluessel vom Owner als Muttersprachler abgenommen
- Box abgebaut, Korpus als EBS-Snapshot snap-03f1d1d9ad9262704 gesichert (51,6 GiB, laufende Kosten von 9,39 auf ~2,9 USD/Monat)

**Stats:**

- 5 Phasen, 37 Plaene, 75 Tasks
- 4 Tage (08.09.2026 bis 11.09.2026)
- Git range: 1c737e6 -> 891bc6d (Tag v1.1.0), 265 Commits, 567 Dateien, +87.818/-1.774 Zeilen

**Known deferred items at close:** 3 Debug-Sessions (siehe STATE.md Deferred Items; alle drei gehoeren zu laengst gefixten CI-Befunden, nur der Session-Status blieb offen)

**What's next:** v1.2 (uebergeben: DI-10-02/DI-11-01 Sprachfall-Vorpruefung, DI-10-04 Volllauf-Analyse, DI-11-02/03/05/06, Untersuchung der vier regressiven Laststufen, Snapshot-Wiedervorlage, stable35-RE-CHECK 16.09.)

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
