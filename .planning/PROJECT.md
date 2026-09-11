# Findling (Nextcloud Zero-Config-Suche)

## What This Is

Findling ist eine Nextcloud-ExApp, die die kaputte Suche repariert: ein Container mit OCR, klassischer Volltextsuche und semantischer Suche, per Klick aus dem Nextcloud App Store installierbar, ohne Elasticsearch-Gebastel. Ergebnisse erscheinen in der normalen Unified Search (via schlanker PHP-Companion-App) und seit v1.1 zusaetzlich auf einer eigenen Ergebnisseite mit Paginierung. Dreisprachig (EN/DE/FR). Zielgruppe: Selfhoster und kleine Organisationen auf typischer Hardware (4-8 GB RAM, oft ARM), für die das offizielle fulltextsearch-Framework (jahrelang verwaist, weiterhin Elasticsearch-gekoppelt) keine Option ist.

## Core Value

Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.

## Current State (nach v1.1, 2026-09-11)

**Shipped:** Findling 1.1.0 im Nextcloud App Store (beide Apps signiert, Einreichung 11.09.2026, je HTTP 201).

- Grundlast im Leerlauf 103,2 MB (v1.0: 691,8 MB), belegt im Messbericht `docs/measurements/2026-09-vergleichsmessung-m7g/`
- 52.111 Dokumente auf 4-GB-arm64-Box ohne OOM indexiert; Laufzeit +40,9 Prozent gegen v1.0 (benannt, Analyse an v1.2 uebergeben)
- Deutsche Komposita ueber `split_compound` + wngerman-Wortliste (GPL-2+), CI-Sprachfall-Set das ohne Splitter rot wird
- Eigene Ergebnisseite hinter derselben Berechtigungsgrenze (ACL-Vorfilter + finaler PHP-Recheck, Paritaetstest deckt die Route)
- Vollstaendiger FR-Katalog (174 Schluessel, Owner-Muttersprachler-Abnahme), vier Katalog-Gates in CI
- Upgrade 1.0.3 auf 1.1.0 Ende zu Ende in CI bewiesen; Merker: jeder Minor-Sprung braucht eine Migration (Muster Version001100Date20260911000000), sonst stumme Suche
- AWS-Messbox abgebaut; Korpus als EBS-Snapshot `snap-03f1d1d9ad9262704` (51,6 GiB, ~2,9 USD/Monat, Wiedervorlage nach v1.2)
- Enterprise-Flag im Store gesetzt, Kontakt admin@infranode.dev in den Store-Texten

## Requirements

### Validated

- ✓ Volltextsuche über Dateiinhalte, Ergebnisse in der Unified Search, v1.0
- ✓ OCR für gescannte PDFs und Bilder, automatisch beim Indexieren, strikt index-only, v1.0
- ✓ Semantische Suche (lokale Embeddings, CPU-only) mit Hybrid-Ranking, v1.0
- ✓ Zero-Config: Installation aus dem Store, Indexierung startet selbst, v1.0
- ✓ Inkrementelle Indexierung, robust gegen Abbrüche (Resume, Backpressure), v1.0
- ✓ Berechtigungs-Durchgriff (SQLite-ACL-Vorfilter + finaler PHP-Recheck), v1.0
- ✓ PHP-Companion-App als Unified-Search-Provider mit exAppRequest-Proxy, v1.0
- ✓ Admin-Sichtbarkeit: Indexstatus, Fortschritt, Fehler, v1.0
- ✓ Multi-Arch-Image (amd64 + arm64) auf 4-8-GB-Boxen, v1.0 (v1.1: nativ-arm64-CI)
- ✓ App-Store-Einreichung als signiertes App-Paar, v1.0 (1.0.0), v1.1 (1.1.0)
- ✓ Gemeinsame Embedding-Engine, Modell einmal pro Prozess (EFF-01/02), v1.1
- ✓ Komposita-Zerlegung über lizenzkonforme Wortliste (QUAL-01..03), v1.1
- ✓ Eigene Ergebnisseite mit Paginierung und Rückkehr ohne Listenverlust (UI-01..03), v1.1
- ✓ Vergleichsmessung gegen v1.0-Baseline auf Zielhardware (MESS-01..03), v1.1

### Active

(Nächster Milestone noch nicht geplant; Kandidaten siehe ROADMAP.md "Naechster Milestone" und Future Requirements des v1.1-Archivs: Dateityp-Filter/Sortierung auf der Ergebnisseite, Modell-Entladung nach Leerlauf, Index-Verschlüsselung, External Storage.)

### Out of Scope

- Elasticsearch/OpenSearch-Backends, genau die Setup-Qual, die das Produkt beseitigt
- RAG/Chat-Antworten über Dokumente, Context-Chat/Assistant-Terrain; wir liefern Suche, keine Antworten
- Externe Cloud-Embeddings/APIs, Privacy-Versprechen: alles lokal im Container
- Indexierung fremder Quellen (Mail-Server, S3 extern, Websites), Nextcloud-Files zuerst
- Kein eigenes MCP-Tool gegen den Index, Unified Search bleibt die einzige Berechtigungsgrenze
- Typesense als Engine, GPLv3 und Index komplett im RAM, passt nicht zu kleinen Boxen

## Context

- Stand 11.09.2026: zwei Milestones geliefert (v1.0 am 07.09., v1.1 am 11.09.), Backend Python 3.13/Tantivy/fastembed, Companion PHP, ~2.000 Python-Tests + 185 PHP-Tests, 6 CI-Workflows inkl. Fremdinstallations- und Upgrade-Strecke (deploy-harp), Messberichte unter docs/measurements/.
- ZenDiS hat den Schwester-Connector installiert und praesentiert ihn auf der Smart Country Convention; ISV-Call mit Nextcloud (Fabrice Mous) am 14.09.2026, Findling + Backend + Connector tragen das Enterprise-Flag im Store.
- Kill-Kriterium weiter aktiv: Nextcloud GmbH hat fulltextsearch am 12.08.2026 reaktiviert; kündigt sie eine Elasticsearch-freie Volltextsuche mit OCR an (Nextcloud Conference September), wird neu bewertet. Die Differenzierer bleiben: kein Elasticsearch, OCR eingebaut, Semantik, kleines RAM-Budget, deutsche Komposita, Ergebnisseite.
- Historischer Rechercheteil (Marktlücke 15.08.2026, Stack-Entscheide, Pitfalls des alten fulltextsearch) steht im v1.0-Archiv und in docs/; die nicht verhandelbaren Betriebsregeln gelten weiter: Fortschritt in der DB, failed/skipped sichtbar, Nur-Lesen-Invariante auf Nutzerdateien, Rechteprüfung vor Snippet-Erzeugung, INDEX_WORKERS=1.

## Constraints

- **Kapazität**: Solo-Entwickler
- **Hardware-Ziel**: 4-8 GB RAM, ARM-tauglich, alles CPU-only, RAM-Budget hart einplanen (RAM-Tabelle in CLAUDE.md)
- **Tech stack**: Python 3.13 + uv, ExApp via AppAPI/nc_py_api, PHP-Companion-App; Docker/WSL2 für Test-Nextcloud
- **Lizenz**: AGPL-3.0
- **Repo**: public auf GitHub street1983nk (privates Konto, NICHT Akara-GitLab); Git-Identität nie übersteuern (pre-commit-Hook sperrt)
- **Sprache**: Code/README Englisch, Projektkommunikation Deutsch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code; Kataloge EN/DE/FR im Gleichstand (vier Gates)
- **Qualitätsgates**: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal grün vor Commit; Audit-Gate nach jeder Phase (MEDIUM+ fixen, LOW dokumentiert entscheiden)
- **Security/Privacy**: Berechtigungs-Durchgriff strikt; keine Inhalte verlassen den Server; keine Telemetrie
- **Store-Regeln**: Kurztext-Regel (Faktenlisten, Owner-Abnahme vor Einreichung); eine Messzahl steht an drei Stellen (README.en.md + beide info.xml); Tag im Store nie verschieben

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Name: **Findling**; App-IDs `findling` + `findling_backend` | Store frei, context_chat-Muster, nach CSR irreversibel | ✓ Good, zwei Releases im Store, keine Kollision |
| Eine gemeinsame Einreichung 1.0.0 (D-08, ersetzt Staffelung) | Früher sichtbar, Architektur embedding-ready | ✓ Good, 1.0.0 am 07.09. mit allem |
| Engine: Tantivy + SQLite-ACL-Vorfilter + finaler PHP-Recheck | Sprachqualität ist das Produktversprechen; Sicherheitsgrenze ist der PHP-Recheck | ✓ Good, trug durch beide Milestones, keine zweite Grenze aufgemacht |
| Embedded Engine statt Suchserver-Sidecar | Zero-Config + RAM-Budget | ✓ Good, 103,2 MB Grundlast nach v1.1 |
| PHP-Companion für Unified Search (AppAPI kann keine Provider) | context_chat-Muster etabliert | ✓ Good, präzedenzlose Kombination bewiesen |
| OCR strikt index-only, Nutzerdateien nie anfassen | Alt-Tesseract-App hat PDFs gelöscht | ✓ Good |
| Launch-Härtungsphase vor jeder Store-Abgabe | Owner: "perfektes Findling, nicht nur Happy Path" | ✓ Good, fand in 06.1 und 11 echte Produktfehler (u.a. stumme Suche nach Minor-Upgrade) |
| Sprachen v1: DE+EN voll; FR-Katalog ab v1.1 | DACH-Zielgruppe; Owner-Muttersprache FR, Zielmarkt DACH+Frankreich | ✓ Good, 174 Schlüssel, Abnahme ohne Korrektur |
| Gemeinsame Embedding-Engine statt Modell-Entladung (v1.1) | Entladung wäre Bedarfsfall gewesen | ✓ Good, minus 588,6 MB Grundlast, Entladung nicht mehr nötig |
| v1.1 index-kompatibel, kein Reindex (D-04) | Bestandsinstallationen nicht strafen | ✓ Good, Upgrade-Beweis in CI, Indexmarken unverändert |
| Messbox einmal anfahren, danach Snapshot + Abbau (D-01/D-03) | Kosten, Vergleichbarkeit zur Baseline | ✓ Good, 2 Läufe unter Deckel, laufende Kosten auf ~2,9 USD/Monat |
| Kill-Kriterium: NC kündigt ES-freie Volltextsuche mit OCR an -> Neubewertung | fulltextsearch am 12.08. reaktiviert |, Pending (NC Conference September beobachten) |
| Keine Index-Verschlüsselung at rest, transparent dokumentiert | Schutzniveau identisch zum Host |, Pending (Future Requirement) |
| Team Folders default AN, External Storage default AUS | Mount-Crawl billig, External Storage unkalkulierbar | ✓ Good, keine Beschwerden, External Storage bleibt Future |
| Ziel Reputation/Portfolio; Pro-Schiene offen ab v2 | Store hat kein Bezahlmodell |, Pending (Enterprise-Flag + Fake-Door seit 11.09. live, ISV-Spur läuft separat) |

## Next Milestone Goals

Noch nicht geplant (/gsd:new-milestone). Übergabeliste aus v1.1 steht in ROADMAP.md "Naechster Milestone"; nächster fester Termin: stable35-RE-CHECK 16.09.2026, Nextcloud Conference im September (Kill-Kriterium).

<details>
<summary>Archiv: Milestone-Beschreibung v1.1 (abgeschlossen 2026-09-11)</summary>

**Goal:** Die Suche wird spuerbar besser und schlanker, belegt durch einen Vergleichslauf gegen die v1.0-Baseline auf derselben Zielhardware.

**Target features:** Gemeinsame Embedding-Engine; lizenzkonforme Komposita-Wortliste; eigene Ergebnisseite mit Paginierung; Endungsvergleich der Verdikte; Vergleichsmessung auf der AWS-Box.

**Ergebnis:** Alles geliefert, v1.1.0 am 11.09.2026 eingereicht (Details: .planning/milestones/v1.1-ROADMAP.md und MILESTONES.md).

</details>

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check, still the right priority?
3. Audit Out of Scope, reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-11 after v1.1 milestone (archiviert, Full Evolution Review)*
