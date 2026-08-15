# Phase 1: Integrationsbeweis - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning
**Source:** Grilling-Interview 15.08.2026 (Owner-Entscheide, dokumentiert in PROJECT.md Key Decisions) + Research-Synthese

<domain>
## Phase Boundary

Phase 1 beweist die einzige präzedenzlose Kombination des Projekts und friert die Store-Identität ein. Geliefert wird der dünnstmögliche end-to-end Durchstich (Walking Skeleton): Suchbegriff in der Nextcloud-Suchleiste -> PHP-Companion (`IProvider`) -> `exAppRequest`-Proxy -> ExApp-Container -> Treffer erscheint in der Unified Search. Dazu: Content-Gateway (ExApp liest Dateiinhalt rechtegeprüft über die PHP-App), Nur-Lesen-Invariante mit CI-Prüfsummen-Gate, Multi-Arch-Image, App-ID-Freeze und beide CSR-Vorgänge. KEINE Indexierung, KEINE echte Suche, KEIN OCR in dieser Phase (das ist Phase 2/3).

</domain>

<decisions>
## Implementation Decisions

### Identität und Store
- App-IDs eingefroren: ExApp = `findling`, PHP-Companion-ID beim Bau nach Store-Konvention festlegen (z.B. `findling` im Apps-Bereich analog context_chat/context_chat_backend-Muster) und dann NIE mehr ändern (Zertifikat ist ID-gebunden)
- Zwei Store-Einträge = zwei CSR-Vorgänge (nextcloud/app-certificate-requests), BEIDE sofort in dieser Phase einreichen (Lead-Time 1-5 Tage + Rückfragen); CSR-PR-Einreichung selbst ist Owner-Schritt (autonomous: false)
- Public GitHub-Repo street1983nk (Konto-Trennung: Commits NUR als street1983nk <k.cherif@outlook.de>, NIE Akara-Adresse, KEINE Co-Authored-By-Trailer); AGPL-3.0

### Architektur (aus Research verifiziert, nicht neu entscheiden)
- PHP-Companion implementiert `OCP\Search\IProvider` (NICHT `IExternalProvider`, der ist in der Such-UI default-aus) + proxied via `OCA\AppAPI\PublicFunctions::exAppRequest()` (NICHT das deprecated `exAppRequestWithUserInit()`); Rückgabewert prüfen (Fehler kommt als `['error' => ...]`), hartes Timeout ~2 s, bei gestopptem Backend leeres SearchResult mit klarer Meldung
- Content-Gateway: `#[ExAppRequired]`-Endpunkt `GET /files/{fileId}?userId=` in der PHP-App, `IRootFolder->getUserFolder($userId)->getFirstNodeById($fileId)->fopen('r')` als StreamResponse; Rechteprüfung passiert dadurch serverseitig
- ExApp: Python 3.13 + uv, nc_py_api[app] >= 0.30.3 mit AsyncNextcloudApp (Sync-API fällt in 0.31 weg), FastAPI, Basis python:3.13-slim-trixie, Multi-Arch amd64+arm64 (keine musl-Wheels fuer tantivy/onnxruntime, deshalb Debian)
- HaRP als Deploy-Ziel (kein Docker-Socket-Proxy-Spezifikum), NC-Fenster min 32 / max 35
- ExApp-Routen mit access_level in info.xml; Suchroute wird ausschliesslich von der PHP-App gerufen

### Nur-Lesen-Invariante (IDX-07, bewusst in Phase 1)
- Nutzerdateien werden NIE verändert; CI-Gate existiert BEVOR der erste Lesepfad entsteht: Testlauf über Referenzkorpus, Prüfsummen vorher/nachher identisch
- Alle Dateizugriffe der ExApp laufen über das Content-Gateway (nur Lesen strukturell möglich)

### Qualität
- Globale Python-Gates von Commit 1: ruff select E,F,I,UP,B,ASYNC,S,SIM,C4,RUF,PT,RET,A,ISC + format, pyright basic, vulture 80, CI-Steps, lokal grün vor Commit
- Conventional Commits; Code/README Englisch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, in Code/IDs ASCII

### Claude's Discretion
- Genaue Companion-App-ID-Wahl (Konvention am context_chat-Vorbild prüfen)
- Verzeichnislayout Mono-Repo (ExApp + PHP-App in einem Repo) vs. zwei Repos: Empfehlung Mono-Repo, ein CSR pro App-ID bleibt trotzdem nötig
- Wie der Fest-Treffer des Skeletons aussieht (hartverdrahteter Demo-Treffer reicht als Beweis)
- Test-Nextcloud-Setup-Details (juliusknorr/nextcloud-docker-dev lokal, nextcloud:apache in CI, AppAPI manual-install fuer Dev)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt-Entscheide und Research
- `.planning/PROJECT.md` , Key Decisions (Grilling 15.08.), Constraints, Kill-Kriterium
- `.planning/research/SUMMARY.md` , Synthese mit Bauteihenfolge und Research-Flags
- `.planning/research/STACK.md` , verifizierte Versionen, Wheel-Matrix, nc_py_api/AppAPI-Details
- `.planning/research/ARCHITECTURE.md` , Integrationsprotokoll (IProvider+exAppRequest, Content-Gateway, Pull-Queue), aus Quellcode verifiziert
- `.planning/research/PITFALLS.md` , Betriebsrobustheits-Invarianten, ExApp-Deploy-Fallen
- `CLAUDE.md` , Stack-Kurzreferenz und Projektregeln

</canonical_refs>

<specifics>
## Specific Ideas

- Erfolgsbild des Owners: "Ein Suchtreffer aus dem Container in der normalen Suchleiste" als demonstrierbarer Beweis, Video-tauglich
- Schwesterprojekt nextcloud-mcp-connector als Vorlage fuer: uv-Setup mit auditierten Pins, CI-Workflow, Conventional-Commit-Stil, CSR-Prozesswissen; NICHT dessen Code kopieren, nur Muster
- Referenzkorpus fuer das Pruefsummen-Gate: kleine Mischung aus PDF (mit+ohne Textlayer), DOCX, TXT, Bild; die Ratsvorlagen-PDFs sind spaeter der grosse Testkorpus (Phase 2/3)

</specifics>

<deferred>
## Deferred Ideas

- Indexierung, Queue, Tantivy, echte Suche: Phase 2
- Events, ETag-Reconcile, OCR: Phase 3
- Statusseite/Diagnose: Phase 4; Lasttest/Paritaetstest: Phase 5; Semantik: Phase 6
- Standalone-Modus ohne AppAPI: v2

</deferred>

---

*Phase: 01-integrationsbeweis*
*Context gathered: 2026-08-15 via Grilling-Interview (Ersatz fuer discuss-phase, Owner-bestaetigt)*
