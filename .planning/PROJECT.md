# Findling (Nextcloud Zero-Config-Suche)

## What This Is

Findling ist eine Nextcloud-ExApp, die die kaputte Suche repariert: ein Container mit OCR, klassischer Volltextsuche und semantischer Suche, per Klick aus dem Nextcloud App Store installierbar, ohne Elasticsearch-Gebastel. Ergebnisse erscheinen in der normalen Unified Search (via schlanker PHP-Companion-App) und seit v1.1 zusaetzlich auf einer eigenen Ergebnisseite mit Paginierung, seit v1.2 dort mit Dateityp-Filter, Zeitraumfilter und Datums-Sortierung. Optional gibt der Container sein Modell im Leerlauf frei (Schalter ab Werk aus). Dreisprachig (EN/DE/FR). Zielgruppe: Selfhoster und kleine Organisationen auf typischer Hardware (4-8 GB RAM, oft ARM), für die das offizielle fulltextsearch-Framework (jahrelang verwaist, weiterhin Elasticsearch-gekoppelt) keine Option ist.

## Core Value

Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.

## Current State (nach v1.2, 2026-09-21)

**Shipped:** Findling 1.2.0 im Nextcloud App Store (beide Apps signiert, Submission 21.09.2026, Lauf 35618848300, je HTTP 201).

- Filter (sechs Typgruppen, Zeitraum) und Datums-Sortierung auf der Ergebnisseite; Filter reisen in der URL, Rechtegrenze unveraendert (Paritaetstest deckt die neuen Parameter)
- Modell-Entladung im Leerlauf hinter TTL-Schalter (ab Werk aus): beide Speicherhalter zusammen, Rueckkehr zur Grundlast 377,5 MB an der Messgroesse belegt (docs/measurements/2026-09-v12-messung/), erste Suche danach antwortet lexikalisch unter der 1,5-s-Decke
- Alle offenen Messbelege des Milestones aus EINER Box-Anfahrt (Deckel 46 h / 5,40 USD, verbraucht 25,75 h / 2,98 USD); Ergebnisse in docs/performance.md; bekannter Bodensatz 628,0 MB nach Indexlauf mit entladenem Modell
- 6 OCR-Sprachen (deu, eng, fra + ita, nld, spa als Positivliste von neun), stable35-Fenster vollzogen (NC 33-35, stable35-Ast muss-gruen)
- Upgrade-Beweis 1.1.0 auf 1.2.0 Ende zu Ende in CI, Migration Version001200Date20260921000000 (Pflicht je Minor-Sprung)
- Volle Suite 2.491 Python-Tests bestanden / 15 uebersprungen; Tag v1.2.0 auf f827145 mit 7/7 gruenen Tag-Laeufen
- Korpus-Snapshot snap-03f1d1d9ad9262704 bewusst behalten (Owner 21.09., ~2,9 USD/Monat, einzige laufende Box-Kostenstelle)
- Downloads Stand 21.09.: Findling 623 Release-Downloads

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
- ✓ Dateityp-Filter, Zeitraumfilter und Datums-Sortierung auf der Ergebnisseite, Rechtegrenze unveraendert (FILT-01..05), v1.2
- ✓ Modell-Entladung im Leerlauf, beide Speicherhalter, ab Werk aus, one_load-Zusage neu gefasst (MEM-01..05), v1.2
- ✓ Messwerkzeug + Runbook vor der Anfahrt, eine bezahlte Box-Anfahrt mit allen Messbelegen, Cron-Intervall als erzwungene Messbedingung (MESS-04..06), v1.2
- ✓ Haertungen DI-11-02/03/05/06, BL-F01-Schlusssatz dreisprachig, stable35-Entscheid, Store-Einreichung 1.2.0 mit Upgrade-Beweis (HART-01..03, REL-02), v1.2

### Active

(v1.3 Sprachausbau, Owner-Entscheid 23.09.2026; REQ-IDs entstehen in REQUIREMENTS.md.)

- Lexikalische Suche fuer es/it/nl/pt: Tantivy-Sprachfelder, Migration, Reindex-Frage
- UI-Kataloge es/it/nl/pt
- Messanfahrt-Buendel BL-F03 (fuenf offene Boxzahlen)
- Aufraeumbefunde fastembed/numpy
- Store-Einreichung 1.3.0

Weiter in der Wiedervorlage (NICHT in v1.3): Sortierung nach Name/Groesse (Schema-Sprung), Mimetype-Gruppen aus files.mime, geplantes Vorwaermen, Pro-Schiene (Index-Verschluesselung, External Storage, ISV-Entscheid 03.11.).

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
| Kill-Kriterium: NC kündigt ES-freie Volltextsuche mit OCR an -> Neubewertung | fulltextsearch am 12.08. reaktiviert | ✓ Geprüft 21.09.: NICHT ausgelöst (nur ES-Stack-Modernisierung); weiter quartalsweise beobachten |
| Keine Index-Verschlüsselung at rest, transparent dokumentiert | Schutzniveau identisch zum Host |, Pending (Future Requirement) |
| Team Folders default AN, External Storage default AUS | Mount-Crawl billig, External Storage unkalkulierbar | ✓ Good, keine Beschwerden, External Storage bleibt Future |
| Ziel Reputation/Portfolio; Pro-Schiene offen ab v2 | Store hat kein Bezahlmodell |, Pending (Enterprise-Flag + Fake-Door seit 11.09. live, ISV-Spur läuft separat) |
| Eine bezahlte Box-Anfahrt für alle v1.2-Messbelege, Deckel vor dem Start vom Owner freigegeben | Kosten, Runbook-Erstvollzug als Nebenertrag | ✓ Good, 25,75 h / 2,98 USD unter Deckel 46 h / 5,40 USD, alle vier Messaufträge mit Zahl |
| Modell-Entladung hinter TTL-Schalter, ab Werk AUS | Zero-Config-Versprechen, A/B-Beleg brauchte beide Zustände | ✓ Good, 377,5 MB Rückkehr belegt, erste Suche danach lexikalisch statt langsam |
| Sortierung als rein lexikalischer Modus (Score 0.0, RRF aus) | tantivy liefert unter order_by_field den Feldwert statt des Scores | ✓ Good, kein Pseudo-Ranking ausgeliefert |
| 6 OCR-Sprachen (Owner-Entscheid "Mitfahren") | Sprachpakete sind arch-neutral und billig, Positivliste deckelt | ✓ Good, sechs eigene Bau-Prüfungen, Standard bleibt deu+eng+fra |
| stable35-Entscheid als eigener fristgebundener Plan in der ERSTEN Phase | Frist 16.09. lag zwei Tage nach Milestone-Start | ✓ Good, am Stichtag vollzogen, Beweislauf 4/4 grün |

## Current Milestone: v1.3 Sprachausbau

**Goal:** Die lexikalische Suche beherrscht Spanisch, Italienisch, Niederlaendisch und Portugiesisch (Tantivy-Sprachfelder mit sauberer Migration), und die fuenf offenen Boxzahlen aus v1.2 werden nachgemessen.

**Target features:**
- BL-F02 Baustein 2: Tantivy-Sprachfelder es/it/nl/pt, Schema-Migration (Pflicht je Minor-Sprung), Reindex-Frage geklaert
- BL-F02 Baustein 3: UI-Kataloge es/it/nl/pt (je 174 Schluessel, maschinell plus Community-Review statt Muttersprachler-Gate)
- BL-F03: Messanfahrt-Buendel als eigene Messphase (M-01-Zahl, 92c/99d-Wirkung, Bodensatz-Zyklus 2, die 44+6 Dateien, Kaltstartlatenz); Rechenblatt + Deckel VOR Boxstart zur Owner-Freigabe
- Aufraeumbefunde: fastembed-Pin unbenutzt, numpy undeklariert
- Store-Release 1.3.0 (Haertung + Einreichung wie gehabt)

**Key context:** Reddit-Nachfrage + EU-Outreach-Zusagen (OS2ai, GovChat-NL, Buerokratt); OCR-Baustein 1 faehrt schon in v1.2.0 mit. Kill-Kriterium 21.09. geprueft: nicht ausgeloest. Snapshot snap-03f1d1d9ad9262704 steht fuer die Messphase bereit. Owner-Entscheid 23.09.2026.

<details>
<summary>Archiv: Milestone-Beschreibung v1.2 (abgeschlossen 2026-09-21)</summary>

**Goal:** Die v1.1-Verbesserungen werden auf der Zielhardware belegt (Wirkungsbeleg, Laststufen, Sprachfaelle) und die Suche baut sichtbar aus: Dateityp-Filter und Sortierung auf der Ergebnisseite plus Modell-Entladung im Leerlauf, abgeschlossen mit gehaerteter Store-Einreichung v1.2.0.

**Ergebnis:** Alles geliefert, v1.2.0 am 21.09.2026 eingereicht (2x HTTP 201, Lauf 35618848300). Benannte Vorbehalte: die Sprachfall-Messung ohne Fremdbestand lief nicht auf der Box (der Korpus-Snapshot IST der Fremdbestand), sondern wurde als Auflage A4 in Phase 16 ueber den gruenen arm64-CI-Ast nacherfuellt (10/10 Sprachfaelle, Owner-Zweig a); A1/A3 ohne Zielhardware-Nachmessung. Details: .planning/milestones/v1.2-ROADMAP.md und MILESTONES.md.

</details>

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
*Last updated: 2026-09-23, Start Milestone v1.3 Sprachausbau*
