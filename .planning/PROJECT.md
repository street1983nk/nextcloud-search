# Findling (Nextcloud Zero-Config-Suche)

## What This Is

Findling ist eine Nextcloud-ExApp, die die kaputte Suche repariert: ein Container mit OCR, klassischer Volltextsuche und semantischer Suche, per Klick aus dem Nextcloud App Store installierbar, ohne Elasticsearch-Gebastel. Ergebnisse erscheinen in der normalen Unified Search (via schlanker PHP-Companion-App). Zielgruppe: Selfhoster und kleine Organisationen auf typischer Hardware (4-8 GB RAM, oft ARM), für die das offizielle fulltextsearch-Framework (jahrelang verwaist, weiterhin Elasticsearch-gekoppelt) keine Option ist.

## Core Value

Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.

## Requirements

### Validated

(None yet , ship to validate)

### Active

- [ ] Volltextsuche über Dateiinhalte (PDF, Office, Text, Mail-Anhänge später), Ergebnisse in der Unified Search
- [ ] OCR für gescannte PDFs und Bilder (Tesseract/OCRmyPDF-Pfad), automatisch beim Indexieren
- [ ] Semantische Suche (lokale Embeddings, CPU-only, z.B. fastembed/ONNX) mit Hybrid-Ranking Volltext+Vektor
- [ ] Zero-Config: Installation aus dem App Store, Indexierung startet selbst, sinnvolle Defaults, keine Pflicht-Einstellungen
- [ ] Inkrementelle Indexierung über Datei-Events (AppAPI Events Listener / webhook_listeners), robust gegen Abbrüche (Resume, Backpressure)
- [ ] Berechtigungs-Durchgriff: Nutzer finden nur, was sie sehen dürfen
- [ ] PHP-Companion-App registriert den Unified-Search-Provider und proxied an die ExApp (Muster context_chat)
- [ ] Admin-Sichtbarkeit: Indexstatus, Fortschritt, Fehler (einfache Statusseite)
- [ ] Multi-Arch-Image (amd64 + arm64), lauffähig auf 4-8-GB-Boxen (Quantisierung/Chunk-Limits)
- [ ] App-Store-Einreichung (Zertifikat/CSR, info.xml, signiertes Release)

### Out of Scope

- Elasticsearch/OpenSearch-Backends , genau die Setup-Qual, die das Produkt beseitigt
- RAG/Chat-Antworten über Dokumente , das ist Context Chat/Assistant-Terrain; wir liefern Suche, keine Antworten
- Externe Cloud-Embeddings/APIs , Privacy-Versprechen: alles lokal im Container
- Indexierung fremder Quellen (Mail-Server, S3 extern, Websites) , v1 ist Nextcloud-Files; Erweiterung später
- Typesense als Engine , GPLv3 und Index komplett im RAM, passt nicht zu kleinen Boxen

## Context

- Recherche vom 15.08.2026 (Memory `project_nextcloud_exapp_ideen.md` + Session-Reports mit Quell-URLs): Das offizielle fulltextsearch-Framework ist faktisch verwaist (kein NC-34-Release, AIO-Ausfall 01/2026, unbeantwortete Issues seit 2025); Context Chat braucht 12 GB RAM, kann kein OCR und keine Keyword-Suche; der Thread "OCR in Nextcloud, giving up after a month" (02/2026) belegt den Schmerz. Niemand kombiniert OCR + Volltext + semantisch zero-config.
- Technischer Kernbefund: AppAPI kann KEINE Search-Provider registrieren; etabliertes Muster ist eine kleine PHP-App, die den `IProvider` registriert und an die ExApp proxied (so macht es context_chat).
- Kandidaten-Bausteine: Tantivy oder SQLite FTS5 (+ sqlite-vec) im ExApp-Prozess statt Suchserver-Sidecar; OCRmyPDF/Tesseract; fastembed (ONNX, CPU-only). Meilisearch als Fallback, wenn eine Engine-Alternative nötig wird.
- Wiederverwendung aus dem Schwesterprojekt nextcloud-mcp-connector (läuft parallel, Phase 1): ExApp-Skeleton (nc_py_api + FastAPI + AppAPI-Handshake), Store-/CSR-Pipeline, Docker-Multi-Arch, Test-Nextcloud-Setups (nextcloud-docker-dev, CI-Rezept), alle Lehren (App-ID früh einfrieren, CSR-Lead-Time, HaRP statt DSP).
- Owner-Entscheide 15.08.2026: Alles in v1 (Volltext + OCR + Semantik); AGPL-3.0; public auf GitHub street1983nk; Setup heute, Bau startet erst nach der MCP-Connector-Store-Einreichung (September).
- WICHTIG, Lageänderung 12.08.2026 (Features-Research): Nextcloud GmbH hat fulltextsearch/files_fulltextsearch/fulltextsearch_elasticsearch mit 35.0.0beta1 wiederbelebt (aktive Commits, WIP-PRs "new sync service" und "files content provider"). Die Positionierung "einzige lebende Suche" trägt nicht mehr; es tragen: kein Elasticsearch, OCR eingebaut, Semantik, kleines RAM-Budget, sichtbarer Indexstatus, Pro-Datei-Diagnose.
- Stack-Research 15.08.: Tantivy 0.26 als Engine gesetzt (deutsches Stemming + Stopwörter + Komposita-Zerlegung nativ in den Python-Bindings, SnippetGenerator); FTS5 raus (kein deutsches Stemming), Meilisearch raus (zweiter Serverprozess). Embeddings: multilingual-e5-small (MIT), selbst int8-quantisiert, ins Image gebacken (HF_HUB_OFFLINE=1). OCR: pypdfium2-Rendering + tesseract-Subprozess direkt (OCRmyPDF nicht im Indexpfad). Debian-slim-Basis (keine musl-Wheels für tantivy/onnxruntime/sqlite-vec). Versionsfenster NC 32-34 (max 35). nc_py_api nur async (Sync-API fällt in 0.31 weg). Zwei Store-Apps = zwei CSR-Vorgänge.
- Pitfalls-Research 15.08.: fulltextsearch starb an Betriebsrobustheit, nicht an Features. Nicht verhandelbar: Fortschritt in der DB statt Prozessspeicher (Resume nach docker kill), Deckungsgrad als Statusmaß, failed/skipped sichtbar, Nur-Lesen-Invariante auf Nutzerdateien (die alte Tesseract-App hat PDFs GELÖSCHT), Events nur als Beschleuniger + periodischer ETag-Abgleich als Garantie, Rechteprüfung VOR Snippet-Erzeugung, INDEX_WORKERS=1 (OCR- und Embedding-Spitzen nie gleichzeitig auf 4-GB-Boxen).

## Constraints

- **Timeline**: HARTES ZIEL: EINE gemeinsame Store-Einreichung als Erstrelease 1.0.0 mit Volltext, OCR und Semantik, vor Jahresende 2026 (Owner-Entscheide D-08, D-10, D-11 vom 03.09.2026; ersetzt die frühere Staffelung v1.0 jetzt, v1.1 vier bis sechs Wochen später). Scope-Kürzung schlägt Termin; Fallback laut D-10 ist die Staffelung, falls Phase 6 den Dezember gefährdet
- **Kapazität**: Solo-Entwickler; Aufwandsschätzung 10-14 Personenwochen für v1 mit allem
- **Hardware-Ziel**: 4-8 GB RAM, ARM-tauglich , alles CPU-only, kein GPU-Zwang, RAM-Budget hart einplanen
- **Tech stack**: Python 3.13 + uv (lokales System-Python defekt), ExApp via AppAPI/nc_py_api, plus kleine PHP-Companion-App; Docker/WSL2 für Test-Nextcloud
- **Lizenz**: AGPL-3.0 (Ghostscript/OCRmyPDF-AGPL im Container damit kompatibel)
- **Repo**: public auf GitHub street1983nk (privates Konto, NICHT Akara-GitLab)
- **Sprache**: Code/README Englisch, Projektkommunikation Deutsch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code
- **Qualitätsgates**: globale Python-Regel (ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal grün vor Commit)
- **Security/Privacy**: Berechtigungs-Durchgriff strikt; keine Inhalte verlassen den Server; kein Telemetrie-Phoning

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Alles in v1, aber gestaffelt released: v1.0 Volltext+OCR in den Store, v1.1 Semantik 4-6 Wochen später | Grilling 15.08.: früher sichtbar + Feedback vor Nextcloud-Reaktion; Architektur ab Tag 1 embedding-ready, kein Umbau | ÜBERHOLT durch D-08 vom 03.09.2026: eine gemeinsame Einreichung als Erstrelease 1.0.0. Die Staffelung bleibt Fallback (D-10). Der Eintrag steht als Protokoll dessen, was am 15.08. entschieden war |
| Name: **Findling**; App-IDs: Companion = `findling`, ExApp = `findling_backend` | Verfügbarkeits-Check 15.08. (Store beide frei, keine Markenkollision); context_chat-Muster: sichtbare Store-App trägt den kurzen Namen; nach CSR irreversibel | , Pending |
| Kill-Kriterium: Nextcloud kündigt ES-freie Volltextsuche mit OCR an -> Stopp/Pivot-Neubewertung | fulltextsearch am 12.08.26 von NC GmbH wiederbelebt; Nextcloud Conference Sept. beobachten | , Pending |
| Ziel: Reputation/Portfolio; Pro-Schiene bewusst offen ab v2 | Store hat kein Bezahlmodell; Monetarisierung jetzt wuerde v1 verlangsamen | , Pending |
| v1 nur ExApp; Architektur standalone-faehig geschnitten (Provider-Interface wie MCP Connector) | Deploy-Daemon fehlt auf Managed Hosting; Option offenhalten kostet wenig | , Pending |
| Validierung: Test-Korpus (eigene Dokumente + Ratsvorlagen-PDFs, deutsch/gescannt) + Docker-NC mit Testnutzern | Ranking/OCR-Qualitaet vor Fremdinstallationen real pruefen | , Pending |
| Findling verdraengt Crawlwerk (rutscht auf 2027) | belegter Schmerz + Zeitfenster + ExApp-Stack-Synergie | , Pending |
| OCR strikt index-only, Nutzerdateien nie anfassen | "nie destruktiv"-Linie; Alt-Tesseract-App hat PDFs geloescht | , Pending |
| Keine Index-Verschluesselung at rest in v1, transparent dokumentiert | Schutzniveau identisch zum Host der NC-Daten; Disk-Encryption ist Host-Sache | , Pending |
| Sprachen v1: Deutsch + Englisch voll (Stemming, Komposita, OCR-Packs) | DACH-Zielgruppe; deutsche Komposita-Suche als Differenzierer | , Pending |
| Hartes Ziel: v1.0-Store-Einreichung vor Jahresende 2026, Scope-Kuerzung schlaegt Termin | Termindruck-Muster vom MCP Connector; NC-Eigenbau-Risiko bestraft Troedeln | , Pending |
| Pro-Datei-Diagnose + Vorab-Schaetzung in v1.0 | billig (Zustandsmaschine fuehrt die Daten ohnehin), IST das Anti-Silent-Failure-Versprechen | , Pending |
| Engine: Tantivy + SQLite-ACL-Vorfilter auf Kandidaten + finaler PHP-Recheck | Sprachqualitaet ist das Produktversprechen; Sicherheitsgrenze ist der PHP-Recheck, nicht der SQL-Join | , Pending |
| Team Folders default AN, External Storage default AUS | Mount-Crawl macht Team Folders billig; External Storage unkalkulierbar | , Pending |
| Embedded Engine (Tantivy/FTS5) statt Suchserver-Sidecar | Zero-Config + RAM-Budget kleiner Boxen; kein zweiter Serverprozess | , Pending (Research Phase validiert) |
| PHP-Companion-App für Unified Search | AppAPI kann keine Search-Provider registrieren; context_chat-Muster ist etabliert | , Pending |
| AGPL-3.0 + public street1983nk | Ökosystem-Kultur, CSR braucht public Repo, OCR-Stack ist AGPL | , Pending |
| Baustart SOFORT (Owner-Entscheid 15.08. abends, ersetzt "nach MCP-Abgabe") | Arbeit liegt bei Claude, Sessions laufen unabhängig; Phasen werden am Stück durchgezogen, Releases ggf. zusammen eingereicht; fertig zur Nextcloud Conference = bester Launch | , Pending |
| Release-Staffelung v1.0/v1.1 wird zur Einreichungs-Option | Wenn beim Einreichen alles fertig ist, gemeinsame oder direkt aufeinanderfolgende Abgabe; Entscheid bei Store-Einreichung | ENTSCHIEDEN durch D-08 vom 03.09.2026: gemeinsame Abgabe als EIN Erstrelease 1.0.0 |
| App-ID und Name VOR dem ersten Bau-Commit einfrieren | Zertifikat ist ID-gebunden (Lehre aus MCP-Connector-Research) | , Pending (Naming-Task in Phase 1) |

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
2. Core Value check , still the right priority?
3. Audit Out of Scope , reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-15 after initialization*
