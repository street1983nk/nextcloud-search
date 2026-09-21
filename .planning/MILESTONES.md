# Project Milestones: Findling (Nextcloud Zero-Config-Suche)

## v1.2 Messbeleg und Ausbau (Shipped: 2026-09-21)

**Delivered:** Findling 1.2.0 im Nextcloud App Store (beide Apps, Submission-Lauf 35618848300 mit 2x HTTP 201): Filter und Sortierung auf der Ergebnisseite, Modell-Entladung im Leerlauf hinter einem ab Werk ausgeschalteten Schalter, 6 OCR-Sprachen, alle offenen Messbelege des Milestones aus der einen bezahlten Box-Anfahrt, Upgrade-Beweis 1.1.0 auf 1.2.0 live in CI.

**Phases completed:** 12 bis 16 (5 Phasen, 63 Plaene, 123 Tasks)

**Timeline:** 14.09. bis 21.09.2026 (8 Tage, 317 Commits, 308 Dateien, ~86.700 Zeilen hinzugefuegt)

**Key accomplishments:**

- stable35-Terminentscheid am Stichtag vollzogen: NC 35 final (v35.0.0 vom 15.09.), Beweislauf 35095805558 mit allen vier Matrixaesten gruen, der stable35-Ast von deploy-harp ist seither muss-gruen
- Filter (sechs Typgruppen plus Zeitraum) und Datums-Sortierung auf der Ergebnisseite: im Backend genau eine Occur.Must-Klausel an der geparsten Abfrage, in PHP ein readonly-Wertobjekt mit geschlossenen Wertelisten, die Rechtegrenze in Zahl, Reihenfolge und Ort unveraendert
- Modell-Entladung im Leerlauf: beide Speicherhalter werden zusammen freigegeben (Median 100,0 Prozent des Modellspeichers zurueck ans Betriebssystem, an der laufenden Instanz 376 MB nach 75 s), Schalter ab Werk aus, die erste Suche danach antwortet lexikalisch statt zu laden, sechster Diagnosezustand "unloaded" in drei Sprachen sichtbar
- Messphase mit einer bezahlten Box-Anfahrt: alle offenen Messbelege des Milestones erhoben (Ergebnis in docs/performance.md), das Runbook dabei zum ersten Mal vollzogen, Kostendeckel 46 Stunden / 5,40 USD eingehalten, Owner-Abnahme am 21.09.2026
- Haertung: drei Flake-Staemme geschlossen (u.a. enge 423-Wiederholung, cold-engine-Wettlauf), Geheimnis-Gate ueber docs/, A4 ueber den gruenen arm64-CI-Ast (10/10 Sprachfaelle ohne Fremdbestand), Upgrade-Beweis 1.1.0 auf 1.2.0 Ende zu Ende in CI, 6 OCR-Sprachen; Audit 0 CRIT / 0 HIGH / 2 MED (behoben) / 5 LOW (Verdikte)
- Store-Einreichung v1.2.0: Tag auf f827145 mit 7/7 gruenen Tag-Laeufen, Release zweifach signaturverifiziert, Submission 2x HTTP 201, beide Store-Seiten zeigen 1.2.0; Belegkette in docs/audits/2026-09-phase-16/README.md Abschnitt 9 (inkl. 401-Zwischenfall der doppelt gefeuerten Token-Rotation, L-16-05)

**Vorbehalte:** A1/A3 ohne Zielhardware-Nachmessung (benannt in der Phase-16-Verifikation). Offene Artefakte beim Close: keine (Audit sauber, drei alte Debug-Sessions am 21.09. formal geschlossen, Fixes waren laengst committet).

---

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
