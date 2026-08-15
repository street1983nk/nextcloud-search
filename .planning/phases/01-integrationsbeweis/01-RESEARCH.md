# Phase 1: Integrationsbeweis - Research

**Researched:** 2026-08-15
**Domain:** Nextcloud ExApp (AppAPI/nc_py_api) plus PHP-Companion mit `OCP\Search\IProvider`, Store-Identitaet und Multi-Arch-Verpackung
**Confidence:** HIGH fuer das Integrationsprotokoll, die CI-Rezeptur und den CSR-Prozess (alles direkt aus Quellcode und offizieller Doku am 15.08.2026 verifiziert); MEDIUM fuer die Store-Laufzeiten und den HaRP-Betrieb auf Windows/Docker-Desktop

---

## Summary

Die praezedenzlose Kombination dieses Projekts, ein `IProvider` in PHP, der seine Treffer per `exAppRequest` aus einem Container holt, ist mechanisch vollstaendig geklaert. Beide Haelften liegen als lesbarer Quellcode vor: `OCA\AppAPI\PublicFunctions::exAppRequest()` samt der darunterliegenden `AppAPIService::prepareRequestToExApp()` (Guzzle-Optionen, Default-Timeout 3 Sekunden, `http_errors = false`, Rueckgabe `array|IResponse`), und `OCP\Search\IProvider` mit `SearchResult::complete()` bzw. `paginated()`. Das Fehlerverhalten ist eindeutig: unbekannte ExApp und jede Guzzle-Exception (also auch der Timeout) kommen als `['error' => ...]` zurueck, 4xx und 5xx dagegen als normales `IResponse`. Beide Faelle muessen getrennt geprueft werden, sonst zeigt die Suchleiste stumm nichts an.

Drei Befunde korrigieren bzw. praezisieren die bisherige Projektrecherche und muessen in die Planung einfliessen. Erstens: die Unified-Search-UI rendert die Subline als Vue-Interpolation `{{ subline }}` in `core/src/components/UnifiedSearch/SearchResult.vue`, also **ohne** `v-html`. HTML im Snippet wird als Text angezeigt, nicht als Markup. Das Proxy-Protokoll muss deshalb Klartext-Snippets liefern, Hervorhebungspositionen gehoeren allenfalls in `attributes`. Zweitens: `<dependencies>` im info.xml-Schema kennt **keine** App-zu-App-Abhaengigkeit. Die Bindung an `app_api` ist ausschliesslich ein Laufzeit-Check (`IAppManager::isEnabledForUser('app_api')` plus `\OCP\Server::get()` im try/catch), genau so wie context_chat es macht. Drittens: `nc.ocs()` in nc_py_api parst die Antwort immer als JSON, das Inhalts-Gateway liefert aber einen Bytestrom. Der Abruf muss ueber `download2stream` bzw. den rohen httpx-Adapter laufen.

Die Verpackung ist ebenfalls entschieden. Beide App-IDs, `findling` und `findling_backend`, sind in beiden Store-Feeds (`apps.json` mit 741 Apps und `appapi_apps.json` mit 25 ExApps) am 15.08.2026 frei. Der CSR-Prozess ist fuer beide identisch (`openssl req -nodes -newkey rsa:4096 -keyout X.key -out X.csr -subj "/CN=X"`, ein Verzeichnis `X/X.csr` je App im Repo `nextcloud/app-certificate-requests`), und auch die ExApp braucht ein Zertifikat, weil der Store-Tarball mit `occ integrity:sign-app` signiert wird. Fuer Multi-Arch loesen die seit August 2025 allgemein verfuegbaren, fuer oeffentliche Repos kostenlosen `ubuntu-24.04-arm`-Runner die QEMU-Falle aus PITFALLS Nr. 11 vollstaendig auf.

**Primary recommendation:** Mono-Repo mit `php/` und `backend/`, PHP-Companion-ID `findling` (Apps-Bereich), ExApp-ID `findling_backend` (External Apps), Proxy-Aufruf gekapselt in genau einer Klasse mit `['timeout' => 2]`, Klartext-Snippets im Protokoll, CI nach dem verifizierten context_chat_backend-Muster (Server auschecken, `occ maintenance:install`, `composer run serve`, `app_api:daemon:register ... manual_install`, `app_api:app:register --json-info`), Multi-Arch-Build auf nativen amd64- und arm64-Runnern statt QEMU, beide CSRs am Tag des ersten Bau-Commits einreichen.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Identitaet und Store**
- App-IDs eingefroren: ExApp = `findling`, PHP-Companion-ID beim Bau nach Store-Konvention festlegen (z.B. `findling` im Apps-Bereich analog context_chat/context_chat_backend-Muster) und dann NIE mehr aendern (Zertifikat ist ID-gebunden)
- Zwei Store-Eintraege = zwei CSR-Vorgaenge (nextcloud/app-certificate-requests), BEIDE sofort in dieser Phase einreichen (Lead-Time 1-5 Tage + Rueckfragen); CSR-PR-Einreichung selbst ist Owner-Schritt (autonomous: false)
- Public GitHub-Repo street1983nk (Konto-Trennung: Commits NUR als street1983nk <k.cherif@outlook.de>, NIE Akara-Adresse, KEINE Co-Authored-By-Trailer); AGPL-3.0

**Architektur (aus Research verifiziert, nicht neu entscheiden)**
- PHP-Companion implementiert `OCP\Search\IProvider` (NICHT `IExternalProvider`, der ist in der Such-UI default-aus) + proxied via `OCA\AppAPI\PublicFunctions::exAppRequest()` (NICHT das deprecated `exAppRequestWithUserInit()`); Rueckgabewert pruefen (Fehler kommt als `['error' => ...]`), hartes Timeout ~2 s, bei gestopptem Backend leeres SearchResult mit klarer Meldung
- Content-Gateway: `#[ExAppRequired]`-Endpunkt `GET /files/{fileId}?userId=` in der PHP-App, `IRootFolder->getUserFolder($userId)->getFirstNodeById($fileId)->fopen('r')` als StreamResponse; Rechtepruefung passiert dadurch serverseitig
- ExApp: Python 3.13 + uv, nc_py_api[app] >= 0.30.3 mit AsyncNextcloudApp (Sync-API faellt in 0.31 weg), FastAPI, Basis python:3.13-slim-trixie, Multi-Arch amd64+arm64 (keine musl-Wheels fuer tantivy/onnxruntime, deshalb Debian)
- HaRP als Deploy-Ziel (kein Docker-Socket-Proxy-Spezifikum), NC-Fenster min 32 / max 35
- ExApp-Routen mit access_level in info.xml; Suchroute wird ausschliesslich von der PHP-App gerufen

**Nur-Lesen-Invariante (IDX-07, bewusst in Phase 1)**
- Nutzerdateien werden NIE veraendert; CI-Gate existiert BEVOR der erste Lesepfad entsteht: Testlauf ueber Referenzkorpus, Pruefsummen vorher/nachher identisch
- Alle Dateizugriffe der ExApp laufen ueber das Content-Gateway (nur Lesen strukturell moeglich)

**Qualitaet**
- Globale Python-Gates von Commit 1: ruff select E,F,I,UP,B,ASYNC,S,SIM,C4,RUF,PT,RET,A,ISC + format, pyright basic, vulture 80, CI-Steps, lokal gruen vor Commit
- Conventional Commits; Code/README Englisch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, in Code/IDs ASCII

### Claude's Discretion

- Genaue Companion-App-ID-Wahl (Konvention am context_chat-Vorbild pruefen)
- Verzeichnislayout Mono-Repo (ExApp + PHP-App in einem Repo) vs. zwei Repos: Empfehlung Mono-Repo, ein CSR pro App-ID bleibt trotzdem noetig
- Wie der Fest-Treffer des Skeletons aussieht (hartverdrahteter Demo-Treffer reicht als Beweis)
- Test-Nextcloud-Setup-Details (juliusknorr/nextcloud-docker-dev lokal, nextcloud:apache in CI, AppAPI manual-install fuer Dev)

### Deferred Ideas (OUT OF SCOPE)

- Indexierung, Queue, Tantivy, echte Suche: Phase 2
- Events, ETag-Reconcile, OCR: Phase 3
- Statusseite/Diagnose: Phase 4; Lasttest/Paritaetstest: Phase 5; Semantik: Phase 6
- Standalone-Modus ohne AppAPI: v2
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMP-01 | Nutzer sieht Findling-Treffer in der Unified Search ueber einen `IProvider` | Abschnitt "Frage 1" (minimale PHP-App), "Frage 2" (Subline ist Klartext), "Frage 3" (Timeout und Fehlerform), Code-Beispiele 1 bis 4. Verifiziert: `registerSearchProvider` seit NC 20, `getOrder()` darf nicht `null` liefern, sonst wird der Provider in der UI versteckt und die API gar nicht erst gerufen |
| COMP-02 | ExApp holt Dateiinhalte ueber `#[ExAppRequired]`-Endpunkt (Rechtepruefung inklusive) | Code-Beispiel 5 (wortgleich aus `context_chat/lib/Controller/QueueController.php` verifiziert) plus Pitfall 4: `nc.ocs()` kann keine Binaerdaten liefern, der Abruf braucht `download2stream` |
| IDX-07 | Nur-Lesen-Invariante mit CI-Pruefsummen-Gate | Abschnitt "Nur-Lesen-Invariante: der konkrete Gate-Bauplan", zwei Gates (statisch plus Pruefsummenlauf), beide ohne Indexierungscode lauffaehig |
| PKG-01 | Multi-Arch-Image (amd64 + arm64), Debian-slim-Basis | Abschnitt "Frage 7", verifiziertes Workflow-Muster aus `nextcloud/context_chat_backend`, plus native arm64-Runner statt QEMU; HaRP zwingt zusaetzlich `frpc` plus Supervisor ins Image |
| PKG-02 | Beide App-IDs eingefroren, beide CSRs sofort eingereicht | Abschnitt "Frage 6", beide IDs am 15.08.2026 live gegen beide Store-Feeds als frei geprueft, openssl-Kommandos woertlich aus der offiziellen Doku, gemessene Merge-Zeiten aus dem Repo |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

Aus `CLAUDE.md` im Projektwurzelverzeichnis abgeleitete, fuer den Planer bindende Direktiven:

| Direktive | Wirkung auf Phase 1 |
|---|---|
| Python 3.13 + uv, lokales System-Python gilt als defekt | Jede Python-Aktion im Plan laeuft ueber `uv run` / `uv sync`, nie ueber blankes `python -m pip` |
| AGPL-3.0 | `<licence>agpl</licence>` in beiden info.xml, LICENSE-Datei, REUSE-konforme SPDX-Header |
| Repo public auf GitHub street1983nk, nicht Akara-GitLab | Remote-Setup und Commit-Identitaet sind eigene Plan-Tasks; Owner-Schritt fuer die CSR-PRs |
| Code/README Englisch, Projektkommunikation Deutsch | Alle Bezeichner, Kommentare, Commit-Messages und Store-Texte in Englisch; Planungsartefakte Deutsch |
| Keine Em-Dashes, echte Umlaute nur in deutscher Prosa, nie in Code | Gilt auch fuer info.xml-`<description>`, README und Store-Beschreibung |
| Globale Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal gruen vor Commit | Die Gates entstehen in Wave 1, vor dem ersten Fachcode |
| Security/Privacy: Berechtigungs-Durchgriff strikt, keine Inhalte verlassen den Server, keine Telemetrie | Der `/search`-Endpunkt darf die Nutzer-ID nur aus `AUTHORIZATION-APP-API` lesen; `set_user()` ist verboten |
| Hardware-Ziel 4-8 GB RAM, ARM-tauglich, CPU-only | Multi-Arch ab dem ersten Image, kein QEMU-only-Build |
| GSD-Workflow-Zwang: keine direkten Repo-Edits ausserhalb eines GSD-Kommandos | Betrifft die Ausfuehrung, nicht die Recherche |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Registrierung in der Unified Search | Nextcloud-PHP-App (Companion) | - | `registerSearchProvider` ist eine reine Server-API; AppAPI kann nachweislich keinen Suchanbieter registrieren |
| Uebersetzung `ISearchQuery` -> Backend-Aufruf | Nextcloud-PHP-App | - | `ISearchQuery` existiert nur im PHP-Prozess |
| Transport PHP -> Container | AppAPI-Proxy (`/apps/app_api/proxy/*`, HaRP/FRP) | - | Einziger vom Server unterstuetzter Weg, setzt die Auth-Header |
| Erzeugung der Treffer und Snippets | ExApp-Container (Python) | - | Nur dort liegt (spaeter) der Chunktext; in Phase 1 ist es ein fest verdrahteter Demo-Treffer |
| Rendering der Trefferliste | Browser (Vue) | - | `SearchResult.vue` interpoliert Titel und Subline als Text, kein HTML |
| Rechte-Aufloesung beim Dateizugriff | Nextcloud-PHP-App (Content-Gateway) | Nextcloud-Storage-Layer | `getUserFolder($userId)->getFirstNodeById()` ist die einzige nicht driftende Wahrheitsquelle |
| Identitaet des suchenden Nutzers | AppAPI-Header, gelesen im Container | - | `AUTHORIZATION-APP-API` traegt `base64("<uid>:<secret>")`; eine Nutzer-ID im Body waere eine Rechteumgehung |
| Persistenter Zustand der ExApp | Container-Volume (`APP_PERSISTENT_STORAGE`) | - | In Phase 1 nur `_version.info`, kein Index |
| Image-Bau und Registry | CI (GitHub Actions) plus ghcr.io | - | AppAPI zieht `registry/image:tag` aus `<docker-install>` zur Installationszeit |
| Store-Identitaet und Signatur | apps.nextcloud.com plus app-certificate-requests | Owner (PR-Einreichung) | Zertifikat ist an die App-ID gebunden, deshalb ID-Freeze vor dem ersten Bau-Commit |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `nc-py-api[app]` | 0.30.3 (aktuellste auf PyPI, geprueft 15.08.2026) | ExApp-Geruest, AppAPI-Handshake, Auth-Middleware, OCS-Client | Die einzige gepflegte Python-Bibliothek fuer AppAPI; `set_handlers()` liefert `/enabled`, `/heartbeat` und `/init` fertig [VERIFIED: PyPI JSON-API + Quellcode `nc_py_api/ex_app/integration_fastapi.py`] |
| `fastapi` | 0.141.1 | HTTP-Ebene der ExApp | Von nc_py_api vorausgesetzt (`>= 0.133`) [VERIFIED: PyPI] |
| `starlette` | 1.6.0 | ASGI-Unterbau | Boden `>= 1.0.1` wegen CVE-2026-48710 nicht unterlaufen [CITED: nc_py_api CHANGELOG, uebernommen aus STACK.md] |
| `uvicorn` | via `nc_py_api.ex_app.run_app` | ASGI-Server | `run_app` waehlt automatisch Unix-Socket (HaRP) oder TCP (`APP_PORT`) [VERIFIED: `nc_py_api/ex_app/uvicorn_fastapi.py`] |
| `httpx` | 0.28.1 | Transitiv via nc_py_api, direkt fuer den Binaer-Abruf am Content-Gateway | `nc.ocs()` parst immer JSON, Bytes brauchen den rohen Adapter [VERIFIED: `nc_py_api/_session.py`] |
| PHP | >= 8.2 | Companion-App | NC 32 bis 34 Matrix [ASSUMED, aus STACK.md uebernommen] |
| `OCP\Search\IProvider` | seit NC 20 | Suchanbieter | `getOrder()` seit NC 28 nullable, `null` versteckt den Provider [VERIFIED: `nextcloud/server` `lib/public/Search/IProvider.php`] |
| `OCA\AppAPI\PublicFunctions` | AppAPI 32.x bis 34.x | Proxy in den Container | `exAppRequest()`; `exAppRequestWithUserInit()` ist seit AppAPI 3.0.0 deprecated und ruft intern dasselbe [VERIFIED: `nextcloud/app_api` `lib/PublicFunctions.php`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `uv` | 0.12.5 (lokal installiert: 0.11.7) | Abhaengigkeits- und Umgebungsverwaltung | Jede Python-Ausfuehrung, auch im Dockerfile |
| `ruff` | 0.16.3 | Lint plus Format | Gate ab Commit 1, Regelsatz aus CONTEXT.md |
| `pyright` | 1.1.411 | Typpruefung, Modus `basic` | Gate ab Commit 1 |
| `vulture` | 2.16 | Toter Code, min-confidence 80 | Gate ab Commit 1 |
| `pytest` | 9.1.1 | Tests, inkl. Pruefsummen-Gate | Gate ab Commit 1 |
| `pytest-asyncio` | aktuell | Async-Tests gegen die FastAPI-App | Fuer alle `AsyncNextcloudApp`-Pfade |
| `frpc` | 0.61.1 | FRP-Client fuer HaRP im Container | Pflicht, sobald HaRP das Deploy-Ziel ist |
| `supervisord` | Debian-Paket | Startet `frpc` und `uvicorn` nebeneinander | Der Container hat unter HaRP zwei Prozesse |
| `krankerl` | 0.14.0 | Tarball-Bau fuer den Store | Optional, ein Makefile-Ziel `appstore` tut es auch |
| `xmllint` (libxml2) | aktuell | Lokale XSD-Validierung der info.xml | CI-Gate, siehe Fallstrick 2 |
| `xsltproc` | aktuell | Normalisierung der info.xml vor der XSD-Pruefung | Ohne diesen Schritt validiert man das falsche Dokument |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Mono-Repo mit `php/` und `backend/` | Zwei getrennte Repos (wie nextcloud/context_chat und nextcloud/context_chat_backend) | Nextcloud trennt, weil dort zwei Teams arbeiten. Bei einem Solo-Entwickler kostet die Trennung nur Synchronisation, und beide Versionen muessen ohnehin im Gleichschritt laufen. Mono-Repo empfohlen; die Store-Verpackung muss dann aus einem Unterverzeichnis tarren, was `krankerl` nicht ohne Weiteres kann, ein Makefile-Ziel schon |
| Native arm64-Runner (`ubuntu-24.04-arm`) | QEMU-Emulation ueber `docker/setup-qemu-action` | QEMU macht aus einem 5-Minuten-Build einen 90-Minuten-Build. Nextcloud selbst schreibt im eigenen Workflow den Kommentar "arm takes too long with qemu". Native Runner sind fuer oeffentliche Repos kostenlos und seit 07.08.2025 allgemein verfuegbar |
| CI mit `nextcloud/server`-Checkout plus `composer run serve` | Service-Container `nextcloud:apache` | Das offizielle Docker-Image bringt einen eigenen Entrypoint mit Installationsassistent mit und macht `occ` nur ueber `docker exec` erreichbar. Das verifizierte Muster von context_chat_backend nutzt einen Quell-Checkout plus PHP-Builtin-Server. Es ist einfacher, schneller und erlaubt die Server-Matrix stable32/33/34/master direkt |
| ExApp-Prozess in CI nativ starten | ExApp im Docker-Container starten | Nativ ist schneller und braucht keinen Deploy-Daemon; der Docker-Pfad gehoert in Phase 5 (AIO- und compose-Topologie) |
| `SearchResult::complete()` fuer den Skeleton | `SearchResult::paginated()` | Fuer einen fest verdrahteten Demo-Treffer ist `complete()` ehrlicher; die Cursor-Semantik kommt mit der echten Suche in Phase 2 |

**Installation:**

```bash
uv init --package backend
uv add "nc-py-api[app]>=0.30.3" fastapi uvicorn httpx
uv add --dev ruff pyright vulture pytest pytest-asyncio
```

**Version verification:** Alle Versionen am 15.08.2026 gegen die PyPI-JSON-API geprueft (`https://pypi.org/pypi/<name>/json`, Feld `info.version`).

---

## Package Legitimacy Audit

Ausgefuehrt mit `slopcheck install ...` am 15.08.2026 (slopcheck war lokal via uv-Tool verfuegbar), Ergebnis fuer alle neun Pakete `[OK]`.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `nc-py-api` | PyPI | seit 2023 | etabliert | github.com/cloud-py-api/nc_py_api | [OK] (Hinweis: Name endet auf `-api`, klassisches LLM-Muster, Paket aber etabliert) | Approved |
| `fastapi` | PyPI | seit 2018 | sehr hoch | github.com/fastapi/fastapi | [OK] | Approved |
| `uvicorn` | PyPI | seit 2017 | sehr hoch | github.com/encode/uvicorn | [OK] | Approved |
| `httpx` | PyPI | seit 2019 | sehr hoch | github.com/encode/httpx | [OK] | Approved |
| `pytest` | PyPI | seit 2009 | sehr hoch | github.com/pytest-dev/pytest | [OK] | Approved |
| `pytest-asyncio` | PyPI | seit 2014 | sehr hoch | github.com/pytest-dev/pytest-asyncio | [OK] | Approved |
| `ruff` | PyPI | seit 2022 | sehr hoch | github.com/astral-sh/ruff | [OK] | Approved |
| `pyright` | PyPI | seit 2020 | hoch | github.com/RobertCraigie/pyright-python | [OK] | Approved |
| `vulture` | PyPI | seit 2012 | hoch | github.com/jendrikseipp/vulture | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

Zusaetzlich ohne Registry: `frpc` 0.61.1 wird nicht von PyPI, sondern als Binaerdatei aus `nextcloud/HaRP` (gepinnter Commit `dadcb7cf...`) geladen, genau so wie `context_chat_backend` es tut. Das ist eine bewusste Abweichung vom Paketmanager und gehoert als solche in den Plan: URL und Pruefsumme pinnen, nicht `latest` ziehen.

---

## Architecture Patterns

### System Architecture Diagram

```
Nutzer tippt in der Nextcloud-Suchleiste
        |
        v
Browser: ein eigener HTTP-Request PRO PROVIDER
   GET /ocs/v2.php/search/providers/findling/search?term=...
        |
        v
+--------------------------------------------------------------+
| NEXTCLOUD PHP-PROZESS                                          |
|                                                                |
|  UnifiedSearchController -> SearchComposer                     |
|        |                                                       |
|        v                                                       |
|  OCA\Findling\Search\Provider  (implements IProvider)          |
|        |  getId() / getName() / getOrder() / search()          |
|        v                                                       |
|  OCA\Findling\Service\ExAppService   <-- EINZIGE Stelle mit    |
|        |                                  exAppRequest         |
|        |  1. isEnabledForUser('app_api')?  -> nein: leer       |
|        |  2. Server::get(PublicFunctions::class) im try/catch  |
|        |  3. exAppRequest('findling_backend','/search',$uid,   |
|        |       'POST', $params, ['timeout' => 2])              |
|        |  4. is_array($r) -> Fehler ODER Timeout               |
|        |     $r instanceof IResponse -> Status pruefen         |
|        v                                                       |
+--------|-------------------------------------------------------+
         |                                     ^
         | AppAPI-Proxy setzt Header:          | StreamResponse (Bytes)
         |  AA-VERSION                         | GET /ocs/v2.php/apps/
         |  EX-APP-ID, EX-APP-VERSION          |   findling/files/{id}
         |  AUTHORIZATION-APP-API =            |   ?userId=<uid>
         |    base64("<uid>:<app_secret>")     |   #[ExAppRequired]
         v                                     |
+--------------------------------------------------------------+
| HaRP  (FRP-Tunnel, remotePort=APP_PORT -> unix:/tmp/exapp.sock)|
+--------------------------------------------------------------+
         |                                     ^
         v                                     |
+--------------------------------------------------------------+
| ExApp-CONTAINER (python:3.13-slim-trixie, supervisord)         |
|                                                                |
|  [frpc]        [uvicorn --uds /tmp/exapp.sock]                 |
|                        |                                       |
|                AppAPIAuthMiddleware                            |
|                  prueft Signatur, setzt scope["username"]      |
|                  (heartbeat immer ausgenommen)                 |
|                        |                                       |
|     +------------------+------------------+                    |
|     v                  v                  v                    |
|  PUT /enabled     GET /heartbeat     POST /init                |
|  (set_handlers)   (set_handlers)     (set_handlers)            |
|     |                                                          |
|     v                                                          |
|  POST /search   -> Nutzer-ID AUSSCHLIESSLICH aus               |
|                    Depends(anc_app) -> await nc.user           |
|                 -> Phase 1: ein fest verdrahteter Treffer      |
|                 -> Antwort: Klartext-Snippet, kein HTML        |
|                                                                |
|  Content-Abruf (Phase 1 nur als Beweis, nicht als Pipeline):   |
|    nc._session.download2stream(...)  NICHT nc.ocs()            |
|                                                                |
|  Volume $APP_PERSISTENT_STORAGE: nur _version.info             |
+--------------------------------------------------------------+
```

Wichtig am oberen Rand des Diagramms: die Unified Search ruft **nicht** alle Provider in einem PHP-Request auf. Der Browser stellt pro Provider einen eigenen Request an `GET /ocs/v2.php/search/providers/{providerId}/search` [VERIFIED: `core/Controller/UnifiedSearchController.php`, Attribut `#[ApiRoute(verb: 'GET', url: '/providers/{providerId}/search', root: '/search')]`]. Ein langsamer Provider blockiert also keinen anderen Provider im PHP-Prozess, belegt aber einen PHP-Worker und laesst die UI fuer diese eine Ergebnisgruppe haengen. Das harte Timeout bleibt trotzdem Pflicht, weil sonst der Worker haengt und der Nutzer eine ewig drehende Gruppe sieht.

### Recommended Project Structure

```
nextcloud-search/
├── php/                              # Companion-App, Store-ID: findling
│   ├── appinfo/
│   │   ├── info.xml                  # id, licence agpl, nextcloud min 32 max 35
│   │   └── routes.php                # leer bzw. nur Nicht-OCS-Routen
│   ├── lib/
│   │   ├── AppInfo/Application.php   # registerSearchProvider(Provider::class)
│   │   ├── Search/Provider.php       # IProvider, duenn, keine Fehlerlogik
│   │   ├── Service/ExAppService.php  # EINZIGE Stelle mit exAppRequest
│   │   └── Controller/
│   │       └── GatewayController.php # #[ExAppRequired] GET /files/{fileId}
│   ├── tests/
│   └── composer.json                 # nur autoload-Mapping, keine Runtime-Deps
│
├── backend/                          # ExApp, Store-ID: findling_backend
│   ├── appinfo/info.xml              # external-app: docker-install + routes
│   ├── src/findling/
│   │   ├── main.py                   # FastAPI, lifespan, set_handlers
│   │   ├── api/search.py             # POST /search
│   │   ├── api/lifecycle.py          # enabled_handler (async!)
│   │   └── nc/client.py              # EINZIGES Modul, das nc_py_api importiert
│   ├── tests/
│   │   ├── test_readonly_gate.py     # IDX-07: statisches Gate
│   │   └── test_checksum_corpus.py   # IDX-07: Pruefsummenlauf
│   ├── docker/
│   │   ├── install_frpc.sh
│   │   ├── harp_connect.sh
│   │   ├── entrypoint.sh
│   │   └── supervisord.conf
│   ├── Dockerfile                    # multi-stage, python:3.13-slim-trixie
│   └── pyproject.toml                # uv, exakte Pins
│
├── testdata/corpus/                  # Referenzkorpus fuer das Pruefsummen-Gate
├── .github/workflows/
│   ├── python.yml                    # ruff, pyright, vulture, pytest
│   ├── php.yml                       # php -l, info.xml-XSD
│   ├── integration.yml               # Walking-Skeleton-Test gegen echtes NC
│   └── docker.yml                    # Multi-Arch-Build, nur auf Tags
├── Makefile                          # register / unregister / appstore
└── .planning/
```

Begruendung der beiden harten Kapselungen: `php/lib/Service/ExAppService.php` ist die einzige Datei, die `exAppRequest` aufruft, damit Timeout, Fehlerform und Degradation an genau einer Stelle leben. `backend/src/findling/nc/client.py` ist das einzige Modul, das `nc_py_api` importiert, damit das Nur-Lesen-Gate aus IDX-07 als statischer Test formulierbar ist ("kein anderes Modul importiert nc_py_api" ist pruefbar, "niemand schreibt irgendwo" nicht).

### Pattern 1: Der geschuetzte Proxy-Aufruf

**Was:** Vor jedem `exAppRequest` steht ein zweistufiger Schutz (App aktiviert, Klasse aufloesbar), danach eine dreistufige Auswertung (Array mit `error`, IResponse mit Fehlerstatus, IResponse mit JSON).

**Wann:** Bei jedem Aufruf in den Container, ohne Ausnahme.

**Warum so:** `<dependencies>` im info.xml kennt keine App-zu-App-Abhaengigkeit [VERIFIED: `nextcloud/appstore` `info.xsd`, complexType `dependencies` enthaelt nur php, database, command, lib, owncloud, nextcloud, architecture, backend]. Ist `app_api` deaktiviert, existiert die Klasse `OCA\AppAPI\PublicFunctions` gar nicht im Autoloader. Ohne den Guard faellt die gesamte Unified Search des Nutzers mit einem Container-Fehler aus, nicht nur unsere Ergebnisgruppe.

**Beispiel:** siehe Code-Beispiel 3.

### Pattern 2: Identitaet ausschliesslich aus dem Header

**Was:** Der `/search`-Endpunkt liest die Nutzer-ID ueber `Depends(anc_app)` bzw. `scope["username"]`, niemals aus dem Request-Body. Kommt eine `userId` im Body an, antwortet der Endpunkt mit 400.

**Wann:** Fuer jede Route, die nutzerbezogene Daten liefert.

**Warum so:** `AppAPIAuthMiddleware` prueft die Signatur des Headers `AUTHORIZATION-APP-API` und setzt `scope["username"]` [VERIFIED: `nc_py_api/ex_app/integration_fastapi.py`, Klasse `AppAPIAuthMiddleware`]. Ein Body-Feld waere nicht signiert. Zusaetzlich existiert `AsyncNextcloudApp.set_user()`; dieser Aufruf ist in unserem Code verboten und gehoert in das statische Gate.

**Beispiel:** siehe Code-Beispiel 6.

### Pattern 3: Klartext im Protokoll, Markup nirgends

**Was:** Die `/search`-Antwort liefert `snippet` als reinen Text. Optionale Hervorhebungen reisen als Zeichenoffsets in einem separaten Feld, nicht als eingebettetes HTML.

**Wann:** Ab jetzt, weil das Antwortformat in Phase 1 eingefroren wird und Phase 2 darauf aufbaut.

**Warum so:** siehe Frage 2. Die UI interpoliert die Subline als Text.

### Pattern 4: Ein Prozessbaum statt eines Prozesses (HaRP)

**Was:** Der Container startet unter `supervisord` zwei Programme, `frpc` (aus `harp_connect.sh`) und die eigentliche Anwendung. Die Anwendung lauscht auf `/tmp/exapp.sock`, nicht auf einem TCP-Port, sobald `HP_SHARED_KEY` gesetzt ist.

**Wann:** Sobald HaRP das Deploy-Ziel ist, also ab Phase 1.

**Warum so:** `run_app()` waehlt den Socket automatisch, wenn `HP_SHARED_KEY` gesetzt ist [VERIFIED: `nc_py_api/ex_app/uvicorn_fastapi.py`]. Ohne `frpc` im Image erreicht HaRP diesen Socket nie. Das ist der Grund, warum `context_chat_backend` `supervisord.conf`, `harp_connect.sh` und `install_frpc.sh` mitbringt.

### Anti-Patterns to Avoid

- **`IExternalProvider` implementieren:** Das Interface bedeutet "fragt Dritte", nicht "laeuft in einem anderen Prozess". Solche Provider sind im Unified-Search-Dialog per Schalter standardmaessig aus. Das killt Zero-Config direkt. Stattdessen `IProvider`.
- **`getOrder()` gibt `null` zurueck:** Dann wird der Provider in der UI versteckt und die API gar nicht erst gerufen [VERIFIED: Doc-Kommentar in `IProvider.php`, "If null, the search provider will be hidden in the UI and the API not called"]. Fuer Phase 1 immer einen `int` liefern.
- **Rueckgabewert von `exAppRequest` als Objekt annehmen:** Bei unbekannter ExApp und bei jeder Guzzle-Exception (auch Timeout) kommt ein Array. Ohne `is_array()`-Pruefung ist der naechste Methodenaufruf ein Fatal Error.
- **Auf `http_errors` vertrauen:** AppAPI setzt `$options['http_errors'] = false`. 4xx und 5xx erreichen den Aufrufer als normales `IResponse`. Der Statuscode muss explizit geprueft werden.
- **`nc.ocs()` fuer den Content-Gateway-Abruf:** `ocs()` macht immer `loads(response.text)`. Ein Bytestrom sprengt das mit einer JSON-Exception.
- **`exAppRequestWithUserInit()` verwenden:** Deprecated seit AppAPI 3.0.0, ruft intern dasselbe.
- **App-ID nach dem ersten Bau-Commit aendern:** Das Zertifikat ist per `CN` an die ID gebunden. Eine Umbenennung entwertet es und kostet eine neue CSR-Runde.
- **QEMU als Standardweg fuer arm64:** Kostet das Zehnfache an CI-Zeit und produziert schwer diagnostizierbare Fehlschlaege. Native Runner nutzen.

---

## Antworten auf die offenen Research-Fragen

### Frage 1: Wie sieht die minimale PHP-App aus?

Vier Dateien reichen fuer den Beweis. Alle vier Bausteine sind einzeln in produktivem Code verifiziert.

**`appinfo/info.xml`.** Pflichtfelder laut XSD: `id`, `name`, `summary`, `description`, `version`, `licence`, `author`, `category`, `bugs`, `dependencies/nextcloud`. `namespace` ist optional, sollte aber gesetzt werden (`Findling`), weil sonst aus der ID abgeleitet wird. Es gibt **keinen** Weg, `app_api` als Abhaengigkeit zu deklarieren; das ist ein Laufzeit-Check. `id` muss dem Muster `[a-z]+[a-z0-9_]*[a-z0-9]+` genuegen und darf hoechstens 32 Zeichen lang sein [VERIFIED: `info.xsd`, simpleType `id`]. Der Store verbietet ausserdem das Wort "Nextcloud" im App-Namen und verlangt AGPL-3.0-or-later oder kompatibel [VERIFIED: `developer_manual/app_publishing_maintenance/publishing.rst`, Zeilen 34 und 35].

**`lib/AppInfo/Application.php`.** Eine Klasse, die `App` erweitert und `IBootstrap` implementiert; in `register()` genau eine Zeile: `$context->registerSearchProvider(Provider::class);`. `registerSearchProvider(string $class): void` existiert seit NC 20 in `OCP\AppFramework\Bootstrap\IRegistrationContext` [VERIFIED: Quellcode]. context_chat selbst registriert nachweislich **keinen** Suchanbieter (dort stehen nur `registerEventListener`-Aufrufe), deshalb liefert es fuer diesen Teil kein Vorbild; die rund zwanzig Standard-Apps mit `registerSearchProvider` tun es.

**`lib/Search/Provider.php`.** Implementiert `IProvider` mit vier Methoden. Als konkrete, lesbare Vorlage dient `apps/files/lib/Search/FilesSearchProvider.php` aus `nextcloud/server`: Konstruktorinjektion von `IL10N` und `IURLGenerator`, `#[\Override]`-Attribute, `getOrder()` mit Routen-Fallunterscheidung, `SearchResult::paginated(...)` bzw. fuer uns `complete(...)`.

**`lib/Service/ExAppService.php`.** Kapselt den Proxy. Der Guard und die Auswertung stammen wortgleich aus `context_chat/lib/Service/LangRopeService.php`.

Damit ist Frage 1 vollstaendig beantwortet; die einzige neue Arbeit ist das Zusammenfuegen, nicht die Mechanik.

**Wahl der App-IDs (Claude's Discretion, mit Korrekturvorschlag).** CONTEXT.md haelt fest "ExApp = `findling`" und gleichzeitig "PHP-Companion-ID analog context_chat/context_chat_backend-Muster". Beides zusammen geht nicht: App-IDs sind ueber beide Store-Bereiche hinweg eindeutig, und das genannte Vorbild vergibt die kurze ID an die PHP-App. Empfehlung, die dem Vorbild und der Nutzererwartung folgt:

| Teil | Store-Bereich | ID | Begruendung |
|---|---|---|---|
| PHP-Companion | Apps | `findling` | Das ist der Eintrag, den der Admin sucht und installiert, und der Name, der in der Suchleiste als Ergebnisgruppe erscheint |
| Python-ExApp | External Apps | `findling_backend` | Exakt das context_chat/context_chat_backend-Muster, das AppAPI-Nutzer bereits kennen |

Beide IDs sind am 15.08.2026 in beiden Store-Feeds frei [VERIFIED: `https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json`, 741 Eintraege, und `https://apps.nextcloud.com/api/v1/appapi_apps.json`, 25 Eintraege; weder `findling` noch `findling_backend` enthalten]. **Diese Abweichung von der woertlichen CONTEXT-Formulierung braucht eine Owner-Bestaetigung, bevor die CSRs rausgehen, weil sie danach irreversibel ist.**

### Frage 2: Laesst die Unified-Search-UI HTML in der Subline durch?

**Nein. Antwort verifiziert im Quellcode, HIGH confidence.**

`core/src/components/UnifiedSearch/SearchResult.vue` rendert die Subline so:

```vue
<template #subname>
    {{ subline }}
</template>
```

Das ist Vue-Mustache-Interpolation, kein `v-html`. Vue escaped dabei. Ein geliefertes `<b>Kuendigungsfrist</b>` erscheint dem Nutzer woertlich als `<b>Kuendigungsfrist</b>`. Auch der Titel geht als gebundenes Prop `:name="title"` in `NcListItem` und wird dort als Text behandelt. `SearchResultEntry` selbst ist ein reines Datenobjekt mit `jsonSerialize()` und fuehrt keine Sanitisierung durch, das heisst: die Verantwortung liegt vollstaendig beim Renderer, und der rendert Text.

**Konsequenz fuer das Proxy-Protokoll, jetzt festzulegen:**

```json
{
  "results": [
    {
      "fileId": 12345,
      "path": "Documents/contract.pdf",
      "title": "contract.pdf",
      "snippet": "... eine Kuendigungsfrist von drei Monaten ...",
      "highlights": [[8, 24]],
      "score": 0.0312,
      "mtime": 1755200000
    }
  ]
}
```

`snippet` ist Klartext. `highlights` sind Zeichenoffsets (Start, Ende) in `snippet`, in Phase 1 leer. Damit bleibt die Hervorhebung fuer eine spaetere eigene UI oder fuer OCS-Clients moeglich, ohne dass die Standard-UI unbrauchbaren Text anzeigt. `SearchResultEntry::addAttribute(string $key, string $value)` nimmt nur Strings; die Offsets muessten dort JSON-kodiert reisen. Das ist der einzige Weg, sie ueberhaupt zum Client zu bekommen [VERIFIED: `SearchResultEntry.php`, `@psalm-var array<string, string>`].

Nebenbefund, der zur selben Frage gehoert: der Snippet-Text ist nach PITFALLS Nr. 6 ein Datum, kein Darstellungsdetail. Er darf erst nach bestandener Rechtepruefung entstehen. In Phase 1 ist er hartkodiert, das Protokollfeld existiert aber bereits, damit Phase 2 nichts umbauen muss.

### Frage 3: Wie setzt man ein Timeout auf `exAppRequest`, und was passiert dann?

**Vollstaendig verifiziert in `nextcloud/app_api/lib/Service/AppAPIService.php`.**

Setzen: sechster Parameter `$options`, Schluessel `timeout`, Wert in Sekunden. Das Array wird unveraendert an den Nextcloud-HTTP-Client (Guzzle) durchgereicht.

```php
$response = $appApiFunctions->exAppRequest(
    'findling_backend', '/search', $userId, 'POST',
    ['query' => $term, 'limit' => 20],
    ['timeout' => 2],
);
```

Was AppAPI vorher selbst am `$options`-Array macht:

| Schluessel | Wert | Bedeutung fuer uns |
|---|---|---|
| `headers` | AppAPI-Auth-Header werden zu vorhandenen Headern hinzugemischt | Eigene Header (z.B. `Content-Type`) bleiben erhalten |
| `headers['Accept-Language']` | Sprache aus `IL10NFactory`, falls nicht gesetzt | Nicht ueberschreiben |
| `nextcloud.allow_local_address` | `true` | Noetig, weil die App-ID als Hostname dient |
| `http_errors` | `false`, hart gesetzt | **4xx und 5xx werfen nicht, sie kommen als IResponse zurueck** |
| `timeout` | `3`, nur wenn nicht gesetzt | Der Default ist 3 Sekunden, unser Wert 2 unterbietet ihn bewusst |
| `json` bzw. Query | Bei `GET` werden `$params` per `http_build_query` an die URL gehaengt, sonst nach `$options['json']` | Bei `GET` also keine JSON-Body-Erwartung im Container |

Was beim Timeout passiert, Zeile fuer Zeile:

```php
private function requestToExAppInternal(...): array|IResponse {
    try {
        return match ($method) { 'GET' => $this->client->get($uri, $options), ... };
    } catch (\Exception $e) {
        $this->logger->warning(...);
        return ['error' => $e->getMessage()];
    }
}
```

Ein Guzzle-`ConnectException` bzw. cURL-Fehler 28 wird gefangen und als `['error' => 'cURL error 28: Operation timed out ...']` zurueckgegeben. **Es fliegt keine Exception nach oben.** Damit gibt es genau drei Auswertungsfaelle, und alle drei muessen im Code stehen:

1. `is_array($r) && isset($r['error'])` -> ExApp unbekannt, nicht erreichbar oder Timeout. Reaktion: leeres `SearchResult`, Log auf `info`, kein Rethrow.
2. `$r instanceof IResponse && $r->getStatusCode() >= 400` -> Container antwortet, aber mit Fehler. Reaktion: leeres `SearchResult`, Log auf `warning` mit Statuscode.
3. `$r instanceof IResponse` mit 2xx -> Body per `json_decode` auswerten, `null` als vierten Fehlerfall behandeln.

Zwei ergaenzende Beobachtungen: AppAPI selbst benutzt beim Aktivieren und Deaktivieren einer ExApp `options: ['timeout' => 60]`, was zeigt, dass der Parameter der vorgesehene Weg ist. Und es gibt `requestToExAppAsync()` mit `IPromise`; das ist fuer Phase 1 unnoetig, waere aber der Ausweg, falls sich in Phase 2 herausstellt, dass zwei Sekunden im Suchpfad zu knapp sind.

### Frage 4: AppAPI-Handshake-Minimum fuer eine ExApp mit nc_py_api

**Der Handshake ist fertig eingebaut.** Ein einziger Aufruf im FastAPI-Lifespan registriert alle drei Pflichtrouten [VERIFIED: `nc_py_api/ex_app/integration_fastapi.py`, Funktion `set_handlers`]:

| Route | Verb | Woher | Verhalten |
|---|---|---|---|
| `/enabled` | PUT | `set_handlers(..., enabled_handler=...)` | Ruft unseren Handler, antwortet `{"error": "<text or empty>"}` |
| `/heartbeat` | GET | `default_heartbeat=True` | Antwortet `{"status": "ok"}`, ist von der Auth-Middleware **immer** ausgenommen |
| `/init` | POST | `default_init=True` | Startet optional Modell-Downloads als BackgroundTask, antwortet sofort `{}` |

Zwei harte Anforderungen aus dem Quellcode:

- Der `enabled_handler` **muss** eine Coroutine sein. `set_handlers` prueft mit `asyncio.iscoroutinefunction`; ein synchroner Handler erzeugt eine `DeprecationWarning` mit dem Hinweis "will be removed in v0.31.0" und bindet ausserdem den deprecateten `nc_app`-Dependency-Provider statt `anc_app`. Ein Projekt, das mit `-W error` testet, faellt darauf herein.
- `AppAPIAuthMiddleware` muss als Middleware registriert werden, sonst prueft jeder Endpunkt die Signatur einzeln ueber `__request_sign_check_if_needed`. Mit Middleware liegt die gepruefte Nutzer-ID zusaetzlich in `scope["username"]`.

**Pflicht-Umgebungsvariablen im Container**, aus dem Quellcode abgeleitet: `APP_ID`, `APP_VERSION`, `APP_SECRET`, `APP_PORT`, optional `APP_HOST` (Default `127.0.0.1`), `NEXTCLOUD_URL`, `APP_PERSISTENT_STORAGE`. Unter HaRP zusaetzlich `HP_SHARED_KEY`, `HP_FRP_ADDRESS`, `HP_FRP_PORT` und optional `HP_EXAPP_SOCK`. Ist `HP_SHARED_KEY` gesetzt, bindet `run_app` an den Unix-Socket statt an `APP_PORT`; das ist der Punkt, an dem ein Image ohne `frpc` stumm unerreichbar bleibt.

**Registrierung fuer Dev und CI.** Zwei Schritte, beide verifiziert aus dem Integrationstest von `context_chat_backend`:

```bash
# 1. Deploy-Daemon einmalig anlegen (manual-install, ExApp laeuft als lokaler Prozess)
occ app_api:daemon:register --net host \
    manual_install "Manual Install" manual-install http localhost http://localhost:8080

# 2. ExApp registrieren (Prozess muss vorher laufen und /heartbeat beantworten)
occ app_api:app:register findling_backend manual_install --json-info \
  '{"id":"findling_backend","name":"Findling Backend","daemon_config_name":"manual_install","version":"0.1.0","secret":"12345","port":10035,"scopes":[],"system":0,"routes":[{"url":".*","verb":"GET,POST,PUT,DELETE","access_level":1,"headers_to_exclude":[]}]}' \
  --force-scopes --wait-finish
```

Feinheiten zum JSON: `getAppInfo()` akzeptiert sowohl `id` als auch das aeltere `appid`, und es hebt die Schluessel `docker-install`, `translations_folder`, `routes`, `k8s-service-roles` und `environment-variables` automatisch von der Wurzel nach `external-app` [VERIFIED: `ExAppService::getAppInfo`]. `access_level` ist im JSON-Weg numerisch (`1` = USER), im XML-Weg symbolisch (`USER`). `--wait-finish` blockiert, bis der Handshake durch ist, und ist in CI Pflicht.

**info.xml-Felder fuer den `docker-install`-Fall:**

```xml
<external-app>
    <docker-install>
        <registry>ghcr.io</registry>
        <image>street1983nk/findling_backend</image>
        <image-tag>0.1.0</image-tag>
    </docker-install>
    <routes>
        <route>
            <url>search</url>
            <verb>POST</verb>
            <access_level>USER</access_level>
            <headers_to_exclude>[]</headers_to_exclude>
            <bruteforce_protection>[401]</bruteforce_protection>
        </route>
    </routes>
    <environment-variables>
        <variable>
            <name>FINDLING_LOG_LEVEL</name>
            <display-name>Log level</display-name>
            <description>One of debug, info, warning, error. Default: info.</description>
            <default>info</default>
        </variable>
    </environment-variables>
</external-app>
```

`<routes>` wird bei der Installation automatisch registriert und bei Update bzw. Deinstallation neu gesetzt bzw. entfernt [CITED: `developer_manual/exapp_development/tech_details/api/routes.rst`]. `access_level`-Werte sind `PUBLIC`, `USER`, `ADMIN`. Fuer uns: `/search` als `USER`, nichts als `PUBLIC`. `/enabled`, `/heartbeat` und `/init` brauchen keinen Routeneintrag, die spricht AppAPI direkt an, nicht ueber den Proxy.

### Frage 5: CI-Setup

**Das verifizierte Muster kommt aus `nextcloud/context_chat_backend/.github/workflows/integration-test.yml` und ist deutlich einfacher als ein `nextcloud:apache`-Service-Container.** Statt das Docker-Image zu betreiben, wird der Server als Quellcode ausgecheckt und mit dem PHP-Builtin-Server betrieben. Dadurch ist `occ` ein direkter Aufruf im Arbeitsverzeichnis statt `docker exec`, und die Server-Matrix stable32/33/34/master funktioniert ohne Image-Tags.

Ablauf, auf unser Projekt uebertragen:

```yaml
strategy:
  matrix:
    server-versions: ['stable32', 'stable33', 'stable34']
    php-versions: ['8.2']

services:
  postgres: { image: postgres:17, ... }   # oder sqlite, siehe unten

steps:
  - uses: actions/checkout@v4               # nextcloud/server @ matrix
    with: { repository: nextcloud/server, ref: ${{ matrix.server-versions }}, submodules: recursive }
  - uses: shivammathur/setup-php@v2
    with: { php-version: ${{ matrix.php-versions }},
            extensions: 'mbstring, iconv, fileinfo, intl, sqlite, pdo_sqlite, pgsql, pdo_pgsql, gd, zip' }

  # PHP-Companion an ihren Platz
  - uses: actions/checkout@v4
    with: { path: apps/findling }           # unser Repo-Unterordner php/ wird hierhin gemappt
  - uses: actions/checkout@v4
    with: { repository: nextcloud/app_api,
            ref: ${{ matrix.server-versions == 'master' && 'main' || matrix.server-versions }},
            path: apps/app_api }

  - run: mkdir data && ./occ maintenance:install --database=sqlite --admin-user admin --admin-pass password
  - run: composer run serve &               # PHP-Builtin-Server auf :8080
  - run: ./occ app:enable -vvv -f findling app_api testing

  # ExApp nativ starten (kein Docker in Phase 1)
  - run: uv sync && uv run python -m findling.main &
    env: { APP_ID: findling_backend, APP_SECRET: '12345', APP_PORT: '10035',
           APP_VERSION: '0.1.0', APP_HOST: '127.0.0.1',
           NEXTCLOUD_URL: 'http://localhost:8080',
           APP_PERSISTENT_STORAGE: '${{ runner.temp }}/findling' }

  - run: timeout 10 ./occ app_api:daemon:register --net host manual_install "Manual Install" manual-install http localhost http://localhost:8080
  - run: timeout 120 ./occ app_api:app:register findling_backend manual_install --json-info '...' --force-scopes --wait-finish

  # Der eigentliche Beweis
  - run: ./occ user:add --password-from-env testuser
  - run: curl -u testuser:... -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
           'http://localhost:8080/ocs/v2.php/search/providers/findling/search?term=findling-canary' | tee out.json
  - run: jq -e '.ocs.data.entries | length > 0' out.json
```

**Wie die PHP-Companion an ihren Platz kommt:** nicht ueber `custom_apps`, sondern durch einen Checkout direkt nach `apps/<app_id>` im Server-Baum, gefolgt von `occ app:enable -f <app_id>`. Der Verzeichnisname **muss** exakt die App-ID sein, sonst findet der Autoloader die Klassen nicht. Bei einem Mono-Repo mit `php/`-Unterordner braucht es dafuer entweder `actions/checkout` mit anschliessendem `mv php apps/findling` oder einen Symlink; ein Symlink funktioniert, `occ app:enable` folgt ihm.

**Datenbankwahl:** context_chat_backend nutzt Postgres, weil es pgvector braucht. Wir brauchen in Phase 1 gar keine eigene Tabelle, deshalb reicht SQLite und spart den Service-Container samt Wartezeit. Ab Phase 2 (Queue-Tabellen) sollte mindestens ein Matrix-Eintrag auf MariaDB oder Postgres laufen, weil `IQueryBuilder`-Fehler dialektabhaengig sind.

**Zeitbudget:** der Server-Checkout mit Submodulen plus `maintenance:install` kostet erfahrungsgemaess mehrere Minuten je Matrix-Eintrag. Fuer Phase 1 genuegt ein einziger Integrationslauf (stable34) auf `push` und `pull_request`; die volle Matrix gehoert in einen `schedule`-Lauf, sonst wird die PR-Rueckmeldung zaeh.

### Frage 6: CSR-Prozess fuer zwei Apps

**Der Prozess ist identisch fuer beide Apps und laeuft ueber dasselbe Repo, mit je einem eigenen Verzeichnis.** Verifiziert am Beispiel des Vorbilds: `nextcloud/app-certificate-requests` enthaelt `context_chat/context_chat.csr` plus `context_chat.crt` und daneben `context_chat_backend/context_chat_backend.csr` plus `.crt`. Auch die ExApp braucht also ein Zertifikat, denn ihr Store-Tarball wird ebenfalls mit `occ integrity:sign-app` signiert.

**Schlüsselerzeugung, woertlich aus der offiziellen Doku:**

```bash
openssl req -nodes -newkey rsa:4096 -keyout findling.key -out findling.csr -subj "/CN=findling"
openssl req -nodes -newkey rsa:4096 -keyout findling_backend.key -out findling_backend.csr -subj "/CN=findling_backend"
```

Der `CN` **muss** die App-ID sein; der Server prueft das beim Signaturcheck und meldet sonst "Certificate is not valid for required scope" [CITED: `developer_manual/app_publishing_maintenance/code_signing.rst`].

**Ablauf des PRs**, aus dem README des Zertifikats-Repos:

1. Im GitHub-Webinterface "Create new file"
2. Dateiname `APP_ID/APP_ID.csr`
3. Inhalt der `.csr` einfuegen
4. Committen, Pull Request oeffnen
5. Nice to have: Link auf das oeffentliche Repo mit dem Quellcode
6. Niemanden erwaehnen, die Zustaendigen sind auf das Repo abonniert

**Zwei getrennte PRs sind der sichere Weg.** Ein PR mit zwei Verzeichnissen ist technisch moeglich, aber alle beobachteten Vorgaenge in Juli und August 2026 betreffen genau eine App. Zwei PRs entkoppeln ausserdem die Bearbeitungszeit: wenn bei einer App eine Rueckfrage kommt, wartet die andere nicht mit.

**Gemessene Laufzeiten aus dem Repo (geschlossene PRs, Stand 15.08.2026):**

| PR | erstellt | gemergt | Dauer |
|---|---|---|---|
| Add certificate signing request file for Curio | 2026-07-30 05:23 | 2026-07-30 10:45 | 5 Stunden |
| Add certificate request for schwarzes_brett | 2026-07-29 11:46 | 2026-07-30 10:30 | 1 Tag |
| Add certificate request for Proofing Gallery | 2026-08-03 08:40 | 2026-08-03 11:20 | 3 Stunden |
| Request certificate for SmartCook | 2026-07-30 13:18 | 2026-08-03 06:51 | 4 Tage |
| Add certificate signing request for Jalali calendar | 2026-07-30 18:51 | 2026-08-03 07:32 | 4 Tage |
| Add certificate request for text2image_flux | 2026-08-06 19:26 | 2026-08-10 14:27 | 4 Tage |
| Add certificate request for shortcuts | 2026-08-03 12:32 | 2026-08-14 16:50 | **11 Tage** |

Median rund 3 bis 4 Tage, Ausreisser bis 11 Tage. Die Schaetzung "1 bis 5 Tage" aus dem Schwesterprojekt ist damit zu optimistisch am oberen Rand. Fuer den Terminplan gilt: mindestens zwei Wochen Puffer einplanen, und die PRs am selben Tag einreichen, an dem die IDs eingefroren werden.

**Nach dem Merge:** Nextcloud committet die signierte `.crt` in dasselbe Verzeichnis. Sie ist damit oeffentlich abrufbar, und der Release-Workflow zieht sie zur Buildzeit:

```bash
wget --quiet "https://github.com/nextcloud/app-certificate-requests/raw/master/findling/findling.crt"
php nextcloud/occ integrity:sign-app --privateKey=findling.key --certificate=findling.crt --path=<app-dir>
```

Der private Schluessel gehoert in ein GitHub-Secret (`APP_PRIVATE_KEY` bzw. zwei Secrets fuer zwei Apps) und nirgends sonst hin. Das Repo enthaelt reale PRs mit dem Titel "Revoke and replace certificate for X (private key exposed)"; eine Widerrufsrunde mitten im Terminplan kostet erneut Tage.

**Was zusaetzlich vorbereitet werden muss, aber kein Owner-Schritt ist:** Ein Entwicklerkonto auf apps.nextcloud.com plus ein `APPSTORE_TOKEN` (abrufbar unter `https://apps.nextcloud.com/account/token`). Ohne das laesst sich spaeter kein Release hochladen. Das kann parallel zur CSR laufen.

### Frage 7: GitHub-Repo-Setup, Multi-Arch, Gates im Mono-Repo

**Multi-Arch-Build.** Das verifizierte Nextcloud-Muster nutzt `docker/setup-qemu-action` plus `docker/setup-buildx-action` plus `docker/build-push-action` mit `platforms: linux/amd64,linux/arm64` und Registry-Cache (`cache-from`/`cache-to` mit `type=registry,ref=...:buildcache`). Im selben Workflow steht aber der Kommentar, dass arm mit QEMU zu lange dauert. Fuer ein oeffentliches Repo gibt es seit dem 07.08.2025 den besseren Weg: `ubuntu-24.04-arm` als GitHub-gehosteter Runner, allgemein verfuegbar und in oeffentlichen Repos kostenlos mit 4 vCPUs.

Empfohlener Aufbau, zwei Jobs plus ein Merge-Job:

```yaml
jobs:
  build:
    strategy:
      matrix:
        include:
          - platform: linux/amd64
            runner: ubuntu-24.04
          - platform: linux/arm64
            runner: ubuntu-24.04-arm
    runs-on: ${{ matrix.runner }}
    steps:
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v6
        with:
          context: ./backend
          platforms: ${{ matrix.platform }}
          outputs: type=image,name=ghcr.io/street1983nk/findling_backend,push-by-digest=true,name-canonical=true,push=true
  merge:
    needs: build
    runs-on: ubuntu-24.04
    steps:
      - run: docker buildx imagetools create -t ghcr.io/street1983nk/findling_backend:${{ env.VERSION }} <digests>
```

Kein QEMU, keine 90-Minuten-Builds. Wichtig: das Image muss **vor** dem Store-Release unter genau dem Tag verfuegbar sein, der in `<image-tag>` steht, weil der Deploy-Daemon zur Installationszeit `registry/image:tag` zieht. In Phase 1 reicht `:dev` bzw. der Commit-SHA; der Versions-Tag kommt in Phase 5.

**Dockerfile-Anforderungen fuer Phase 1** (PKG-01 ist erst "bis zum AppAPI-Handshake" faellig, nicht bis zur fertigen Pipeline):

- Basis `python:3.13-slim-trixie` (glibc, nicht musl)
- `uv` per COPY aus `ghcr.io/astral-sh/uv` oder Installationsskript, dann `uv sync --frozen --no-dev`
- `install_frpc.sh` mit Architekturweiche (`uname -m` -> `aarch64` bzw. sonst), FRP 0.61.1, URL auf einen gepinnten Commit in `nextcloud/HaRP`
- `supervisord.conf` mit zwei Programmen: `app` (unser Entrypoint) und `frpc` (`harp_connect.sh`)
- `ENTRYPOINT ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]`
- Kein `EXPOSE`, kein fester Port: unter HaRP lauscht die App auf einem Unix-Socket

**Python-Gates.** Ein Workflow, ein Job, alles ueber `uv`:

```yaml
- run: uv sync --frozen
- run: uv run ruff check .
- run: uv run ruff format --check .
- run: uv run pyright
- run: uv run vulture src tests --min-confidence 80
- run: uv run pytest -q
```

Der ruff-Regelsatz aus CONTEXT.md gehoert in `backend/pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["E","F","I","UP","B","ASYNC","S","SIM","C4","RUF","PT","RET","A","ISC"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]   # assert ist in Tests erlaubt
```

Hinweis zu `S` (bandit): `S101` (assert) schlaegt in Tests immer an, deshalb der per-file-ignore. `ASYNC` ist fuer dieses Projekt besonders wertvoll, weil `AsyncNextcloudApp` durchgehend async ist und blockierende Aufrufe im Event-Loop der haeufigste Anfaengerfehler in FastAPI-ExApps sind.

**PHP-Gates.** Ohne PHP-Toolchain auf dem Entwicklungsrechner (siehe Environment Availability) laufen sie nur in CI. Minimal und ausreichend fuer eine App dieser Groesse:

```yaml
- uses: shivammathur/setup-php@v2
  with: { php-version: '8.2' }
- run: find php/lib php/appinfo -name '*.php' -print0 | xargs -0 -n1 php -l
- run: composer --working-dir=php install
- run: composer --working-dir=php run psalm    # oder phpstan level 5
```

Psalm ist der Nextcloud-Hausstandard (`nextcloud/ocp` als Stub-Paket liefert die `OCP`-Typen), Phpstan die Alternative mit geringerer Einstiegshuerde. Fuer eine App mit vier Klassen ist beides Luxus; `php -l` plus die XSD-Pruefung sind das Minimum, das wirklich Fehler faengt.

**Pfadgefilterte Workflows.** Im Mono-Repo sollte `python.yml` auf `backend/**` und `php.yml` auf `php/**` reagieren (`on.push.paths`), sonst laeuft bei jedem Doku-Commit alles. Der Integrationstest laeuft bei Aenderungen an beiden.

**Repo-Grundeinrichtung.** Public, AGPL-3.0, `.github/workflows/`, `REUSE.toml` bzw. SPDX-Header (Nextcloud-Konvention, erleichtert spaeter den Store-Review), Branch-Protection auf `main`, und die Commit-Identitaet lokal per `git config user.name street1983nk` / `git config user.email k.cherif@outlook.de` **im Repo, nicht global**, damit die Kontotrennung nicht von der globalen Konfiguration abhaengt.

---

## Nur-Lesen-Invariante: der konkrete Gate-Bauplan (IDX-07)

CONTEXT.md verlangt, dass das Gate existiert, **bevor** der erste Lesepfad entsteht. Das ist umsetzbar, weil sich beide Haelften des Gates ohne Indexierungscode formulieren lassen.

**Gate A, statisch (laeuft in `pytest`, keine Nextcloud-Instanz noetig).** Ein Test parst den AST aller Module unter `backend/src/findling/` und behauptet drei Invarianten:

1. Nur `findling/nc/client.py` importiert `nc_py_api`. Jeder andere Import ist ein Fehler.
2. In `findling/nc/client.py` erscheint keiner der verbotenen Bezeichner: `set_user`, `upload`, `upload_stream`, `delete`, `move`, `copy`, `mkdir`, `makedirs`, `trash`. Diese decken die schreibenden Methoden von `nc_py_api.files` ab.
3. Kein Aufruf von `nc.ocs` bzw. des rohen Adapters mit einer der Methoden `PUT`, `POST`, `PATCH`, `DELETE` auf einen Pfad, der nicht in einer expliziten Allowlist steht. In Phase 1 ist die Allowlist leer, denn der Container schreibt noch nichts nach Nextcloud.

Ergaenzend, aber nicht ersetzend: `[tool.ruff.lint.flake8-tidy-imports.banned-api]` kann `nc_py_api.files` projektweit verbieten. Das faengt nur Importe, nicht Attributzugriffe, deshalb bleibt der AST-Test die eigentliche Absicherung.

**Gate B, Pruefsummenlauf (laeuft im Integrationsworkflow).** Der Referenzkorpus liegt unter `testdata/corpus/` und enthaelt laut CONTEXT.md eine PDF mit Textlayer, eine PDF ohne Textlayer, eine DOCX, eine TXT und ein Bild. Empfehlung aus PITFALLS Nr. 3: mindestens zwei bewusst kaputte Dateien dazu (nullbyte-PDF, passwortgeschuetzte PDF), denn der Fehlerpfad ist der Pfad, auf dem files_fulltextsearch_tesseract Nutzerdaten geloescht hat.

Ablauf im Workflow:

```bash
cp -r testdata/corpus data/admin/files/corpus
./occ files:scan --all
sha256sum $(find data/admin/files/corpus -type f) | sort -k2 > before.txt
# ExApp einmal jede Datei ueber das Content-Gateway lesen lassen
uv run python -m findling.tools.read_corpus     # ruft GET /files/{id} je fileId
sha256sum $(find data/admin/files/corpus -type f) | sort -k2 > after.txt
diff before.txt after.txt                        # Exit != 0 -> Gate rot
```

Zusaetzlich pruefen, dass die Dateizahl gleich geblieben ist (`diff` faengt geloeschte Dateien nur, wenn die Liste vorher fix ist, deshalb die Liste einmal erzeugen und beide Male dieselbe Liste hashen). Und `mtime` mitpruefen: ein `touch` veraendert die Pruefsumme nicht, waere aber trotzdem eine Verletzung der Invariante.

**Warum beide Gates noetig sind:** Gate A verhindert, dass jemand kuenftig einen Schreibpfad einbaut. Gate B verhindert, dass ein Schreibvorgang ueber einen Weg passiert, den Gate A nicht kennt (etwa ueber eine Bibliothek, die im Hintergrund schreibt). Ein einzelnes Gate haette die dokumentierte Datenverlustklasse nicht verhindert.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| AppAPI-Lebenszyklus (`/enabled`, `/heartbeat`, `/init`) | Eigene FastAPI-Routen mit eigener Antwortform | `nc_py_api.ex_app.set_handlers()` | Die Antwortformen sind nicht dokumentiert, sondern nur im Quellcode festgelegt (`{"error": ...}` bzw. `{"status": "ok"}`); eine Abweichung laesst die Registrierung stumm scheitern |
| Verifikation des AppAPI-Auth-Headers | Eigenes Parsen von `AUTHORIZATION-APP-API` | `AppAPIAuthMiddleware` | Es gibt eine Signaturpruefung ueber mehrere Header, nicht nur ein base64-Decode; eigenes Parsen ist eine Authentifizierungsluecke |
| HTTP-Aufruf in den Container | Eigener Guzzle- oder cURL-Client gegen die Container-URL | `PublicFunctions::exAppRequest()` | Nur AppAPI kennt Port, Hostnamen, HaRP-Tunnel und die zu setzenden Header; die URL ist je nach Deploy-Daemon eine andere |
| Rechtepruefung beim Dateizugriff | Eigene Share- und Gruppenaufloesung in Python | `getUserFolder($userId)->getFirstNodeById($fileId)` in PHP | Ein zweites Rechtemodell driftet garantiert; ausserdem faellt Groupfolder-, External-Storage- und Verschluesselungsbehandlung dann weg |
| Signatur des Store-Tarballs | Eigenes `openssl dgst`-Skript ueber die Dateiliste | `occ integrity:sign-app` | Erzeugt `appinfo/signature.json` mit exakt der erwarteten Hash- und Zertifikatsstruktur; jede Abweichung faellt beim Upload durch |
| info.xml-Validierung | Eigene XML-Pruefung | `xsltproc pre-info.xslt` gefolgt von `xmllint --schema info.xsd` | Der Store normalisiert vor der Validierung; wer nur gegen das XSD prueft, testet das falsche Dokument (siehe Fallstrick 2) |
| Multi-Arch-Manifest | Zwei Tags und ein manuelles `docker manifest create` | `docker buildx imagetools create` mit `push-by-digest` | Attestierungen und Provenance gehen beim Handbau verloren |
| FRP-Client bauen | frpc aus Quellen kompilieren | Binaerdatei aus `nextcloud/HaRP` (gepinnter Commit) | Genau das tut das Referenzprojekt; Versionsdrift zwischen frpc und HaRP-Server ist eine reale Fehlerquelle |

**Key insight:** Die gesamte Phase besteht aus dem korrekten Verdrahten fremder Bausteine. Jede Zeile Eigenbau in diesem Bereich ist entweder eine Sicherheitsluecke (Auth), eine Fehlerquelle bei fremden Topologien (URL-Aufloesung) oder ein spaeterer Store-Rueckweiser (Signatur, Schema).

---

## Common Pitfalls

### Pitfall 1: Der Rueckgabewert von `exAppRequest` wird als Objekt behandelt

**Was schiefgeht:** `$response->getBody()` wird auf einem `array` aufgerufen und erzeugt einen Fatal Error, der die gesamte Suchanfrage des Nutzers zerstoert, nicht nur unsere Ergebnisgruppe.
**Warum es passiert:** Die Signatur ist `array|IResponse`, und der Erfolgsfall ist das Objekt. Wer nur den Erfolgsfall testet, sieht das Array nie.
**Vermeidung:** Immer `is_array($r)` zuerst. Zusaetzlich einen expliziten Testfall bauen, der die ExApp deregistriert und danach die Suche ausfuehrt.
**Warnzeichen:** Der Provider hat keinen Testfall fuer "Backend gestoppt".

### Pitfall 2: Die info.xml wird gegen das falsche Dokument validiert

**Was schiefgeht:** Man validiert `appinfo/info.xml` direkt gegen `info.xsd` aus `nextcloud/appstore` und bekommt einen Fehler bei `<routes>` und `<k8s-service-roles>`, obwohl der Store diese Dateien akzeptiert. Oder umgekehrt: man laesst die Pruefung ganz weg und faellt beim Upload durch.
**Warum es passiert:** Der Store schiebt die Datei zuerst durch `pre-info.xslt`. Dieses Stylesheet baut das Dokument neu auf und laesst unbekannte Elemente weg; im Template `external-app` kopiert es ausdruecklich nur `docker-install`, `scopes`, `system` und `environment-variables`. `<routes>` wird also **stillschweigend verworfen**, nicht abgelehnt. Erst das Ergebnis wird gegen `info.xsd` geprueft [VERIFIED: `nextcloud/appstore` `pre-info.xslt` Zeilen 172 bis 179, Kommentar "excluded unknown elements"].
**Vermeidung:** Das CI-Gate laedt beide Dateien und macht `xsltproc pre-info.xslt info.xml | xmllint --noout --schema info.xsd -`. Beide Dateien in der CI mit fixem Commit-SHA ziehen, nicht von `master`, sonst bricht der Build durch fremde Aenderungen.
**Warnzeichen:** Ein CI-Gate, das nur `xmllint --schema` aufruft.
**Zweiter, wichtigerer Teil des Befunds:** Weil die Store-Datenbank die Routen nicht speichert, holt AppAPI sie sich bei der Installation aus dem **Release-Archiv**, nicht aus dem Store-JSON (`ExAppService::getLatestExAppInfoFromAppstore` ruft `ExAppArchiveFetcher::downloadInfoXml`). Der Tarball muss die vollstaendige, unveraenderte `appinfo/info.xml` enthalten. Wer beim Tarball-Bau die info.xml filtert oder umschreibt, kappt die Routen der installierten App.

### Pitfall 3: Der Provider erscheint gar nicht in der Suchleiste

**Was schiefgeht:** Die App ist aktiviert, es gibt keine Fehlermeldung, aber es taucht keine Ergebnisgruppe auf.
**Warum es passiert:** Vier Ursachen, alle stumm. Erstens `getOrder()` liefert `null` (dann wird der Provider versteckt und die API nicht gerufen). Zweitens `registerSearchProvider` steht in `boot()` statt in `register()`. Drittens der Verzeichnisname der App entspricht nicht der ID, der Autoloader findet die Klasse nicht. Viertens der Suchdialog blendet Provider ohne Ergebnisse aus, sodass ein leeres `SearchResult` wie "nicht registriert" aussieht.
**Vermeidung:** Als erste Diagnose immer `GET /ocs/v2.php/search/providers` aufrufen. Steht `findling` dort nicht, ist es Ursache eins bis drei; steht es dort, ist es Ursache vier und der Fehler liegt im Container.
**Warnzeichen:** Debugging beginnt beim Container statt bei der Providerliste.

### Pitfall 4: `nc.ocs()` fuer den Content-Gateway-Abruf

**Was schiefgeht:** Der Abruf einer PDF wirft `json.decoder.JSONDecodeError` oder liefert Datenmuell.
**Warum es passiert:** `AsyncNcSessionBasic.ocs()` macht bedingungslos `response_data = loads(response.text)` [VERIFIED: `nc_py_api/_session.py`]. Es gibt keinen Schalter fuer Rohdaten. `response_type="json"` ueberspringt nur das OCS-Envelope-Parsing, nicht das JSON-Parsen.
**Vermeidung:** `nc._session.download2stream(url_path, fp, dav=False)` benutzen, das intern `adapter.get(..., stream=True)` verwendet und in Bloecken schreibt. Alternativ einen eigenen httpx-Client mit selbst gesetztem `AUTHORIZATION-APP-API`-Header. Die erste Variante ist kuerzer, greift aber auf ein privates Attribut zu; das gehoert dokumentiert und in `nc/client.py` gekapselt, damit ein nc_py_api-Update nur eine Datei trifft.
**Warnzeichen:** Der Content-Gateway-Test benutzt eine TXT-Datei, weil die zufaellig als JSON durchgeht.

### Pitfall 5: Der Container ist unter HaRP nicht erreichbar, obwohl er laeuft

**Was schiefgeht:** `occ app_api:app:register` laeuft in einen Timeout, die Containerlogs zeigen aber ein sauber gestartetes uvicorn.
**Warum es passiert:** Ist `HP_SHARED_KEY` gesetzt, bindet `run_app()` an `/tmp/exapp.sock` statt an `APP_PORT`. Ohne `frpc` im Image spricht niemand mit diesem Socket. Der Prozess laeuft, ist aber unerreichbar.
**Vermeidung:** `frpc` plus `harp_connect.sh` plus `supervisord` gehoeren von der ersten Dockerfile-Version an ins Image. In den Startlogs sichtbar machen, welcher Bindungsmodus gewaehlt wurde.
**Warnzeichen:** Das Dockerfile hat `EXPOSE` und einen `ENTRYPOINT`, der direkt Python startet.

### Pitfall 6: Nutzer-ID aus dem Request-Body

**Was schiefgeht:** Wer den Proxy erreicht, sucht als beliebiger Nutzer. Faellt in keinem funktionalen Test auf.
**Warum es passiert:** Es ist der bequemste Weg, und `AsyncNextcloudApp.set_user()` existiert und laedt dazu ein.
**Vermeidung:** Die Nutzer-ID kommt aus `Depends(anc_app)`; beachten, dass `AsyncNextcloudApp.user` eine **async property** ist, also `uid = await nc.user`. Kommt eine `userId` im Body an, mit 400 antworten statt sie zu ignorieren. `set_user` in Gate A verbieten.
**Warnzeichen:** Das Request-Modell des `/search`-Endpunkts hat ein Feld `user_id`.

### Pitfall 7: Ein synchroner `enabled_handler`

**Was schiefgeht:** Alles funktioniert, aber es gibt eine `DeprecationWarning`, und in nc_py_api 0.31.0 bricht es hart.
**Warum es passiert:** Alle aelteren Beispiele (auch das offizielle `to_gif`) sind synchron.
**Vermeidung:** `async def enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str`. In `pytest` mit `-W error::DeprecationWarning` laufen, dann faellt es sofort auf.
**Warnzeichen:** Das Beispiel, von dem kopiert wurde, importiert `NextcloudApp` statt `AsyncNextcloudApp`.

### Pitfall 8: Spaete Umbenennung entwertet das Zertifikat

**Was schiefgeht:** Nach zwei Wochen faellt ein besserer Name ein. Das Zertifikat ist per `CN` an die alte ID gebunden, die neue braucht eine neue CSR-Runde von bis zu elf Tagen.
**Vermeidung:** Der ID-Freeze ist ein eigener, expliziter Plan-Task mit Owner-Bestaetigung, und er steht **vor** dem ersten Commit, der die ID in Code oder Verzeichnisnamen schreibt.
**Warnzeichen:** Im Plan steht "App-ID spaeter festlegen".

### Pitfall 9: Docker-API-Version und AppAPI

**Was schiefgeht:** Deployment scheitert vollstaendig, weder ueber Docker Socket Proxy noch ueber HaRP (app_api Issue Nr. 712, November 2025: Docker 29 verlangt API 1.44, AppAPI sprach 1.41).
**Aktueller Stand:** Behoben. `DockerActions::DOCKER_API_VERSION` steht auf `'v1.44'` [VERIFIED: `nextcloud/app_api` `lib/DeployActions/DockerActions.php`, Zeile 34]. Die lokal installierte Docker-Version ist 29.5.2 und damit kompatibel.
**Vermeidung:** Eine Kompatibilitaetsmatrix (Nextcloud-Version, AppAPI-Version, getestete Docker-Version) ab dem ersten Release im README pflegen, damit der naechste Docker-Sprung nicht ueberrascht.

---

## Code Examples

### 1. `Application.php` (PHP-Companion)

```php
<?php
declare(strict_types=1);
namespace OCA\Findling\AppInfo;

use OCA\Findling\Search\Provider;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'findling';
    public const BACKEND_APP_ID = 'findling_backend';

    public function __construct(array $urlParams = []) {
        parent::__construct(self::APP_ID, $urlParams);
    }

    // registerSearchProvider gehoert in register(), nicht in boot().
    // Signatur verifiziert: IRegistrationContext::registerSearchProvider(string $class): void, @since 20.0.0
    public function register(IRegistrationContext $context): void {
        $context->registerSearchProvider(Provider::class);
    }

    public function boot(IBootContext $context): void {
    }
}
```

### 2. `Provider.php` (Muster aus `apps/files/lib/Search/FilesSearchProvider.php`)

```php
<?php
declare(strict_types=1);
namespace OCA\Findling\Search;

use OCA\Findling\Service\ExAppService;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUser;
use OCP\Search\IProvider;
use OCP\Search\ISearchQuery;
use OCP\Search\SearchResult;
use OCP\Search\SearchResultEntry;

final class Provider implements IProvider {
    public function __construct(
        private IL10N $l10n,
        private IURLGenerator $urlGenerator,
        private ExAppService $exApp,
    ) {
    }

    #[\Override]
    public function getId(): string {
        return 'findling';
    }

    #[\Override]
    public function getName(): string {
        return $this->l10n->t('File contents');
    }

    // NIEMALS null zurueckgeben: das versteckt den Provider und die API wird nicht gerufen.
    #[\Override]
    public function getOrder(string $route, array $routeParameters): ?int {
        return str_starts_with($route, 'files.') ? -5 : 25;
    }

    #[\Override]
    public function search(IUser $user, ISearchQuery $query): SearchResult {
        $hits = $this->exApp->search($user->getUID(), $query->getTerm(), $query->getLimit());

        $entries = array_map(
            fn (array $hit): SearchResultEntry => new SearchResultEntry(
                thumbnailUrl: '',
                title: $hit['title'],
                // Klartext. Markup wird von der UI als Text angezeigt, nicht gerendert.
                subline: $hit['snippet'],
                resourceUrl: $this->urlGenerator->linkToRoute('files.View.showFile', ['fileid' => $hit['fileId']]),
                icon: 'icon-search',
            ),
            $hits,
        );

        return SearchResult::complete($this->getName(), $entries);
    }
}
```

### 3. `ExAppService.php` (Guard und Auswertung, Muster aus `context_chat/lib/Service/LangRopeService.php`)

```php
<?php
declare(strict_types=1);
namespace OCA\Findling\Service;

use OCA\Findling\AppInfo\Application;
use OCP\App\IAppManager;
use OCP\Http\Client\IResponse;
use OCP\IUserManager;
use Psr\Container\ContainerExceptionInterface;
use Psr\Container\NotFoundExceptionInterface;
use Psr\Log\LoggerInterface;

final class ExAppService {
    private const TIMEOUT_SECONDS = 2;

    public function __construct(
        private IAppManager $appManager,
        private IUserManager $userManager,
        private LoggerInterface $logger,
    ) {
    }

    /** @return list<array{fileId:int,title:string,snippet:string}> */
    public function search(string $userId, string $term, int $limit): array {
        $user = $this->userManager->get($userId);

        // info.xml kann app_api NICHT als Abhaengigkeit fuehren, deshalb Laufzeit-Check.
        if (!$this->appManager->isEnabledForUser('app_api', $user)) {
            $this->logger->info('Findling: app_api is not enabled, returning no results');
            return [];
        }

        try {
            $appApi = \OCP\Server::get(\OCA\AppAPI\PublicFunctions::class);
        } catch (ContainerExceptionInterface|NotFoundExceptionInterface) {
            $this->logger->info('Findling: AppAPI public functions unavailable');
            return [];
        }

        $response = $appApi->exAppRequest(
            Application::BACKEND_APP_ID,
            '/search',
            $userId,
            'POST',
            ['query' => $term, 'limit' => $limit],
            ['timeout' => self::TIMEOUT_SECONDS],
        );

        // Fall 1: ExApp unbekannt, nicht erreichbar ODER Timeout. Alles landet hier.
        if (is_array($response)) {
            $this->logger->info('Findling: backend unreachable', ['error' => $response['error'] ?? 'unknown']);
            return [];
        }

        // Fall 2: AppAPI setzt http_errors=false, also kommen 4xx/5xx als IResponse an.
        /** @var IResponse $response */
        if ($response->getStatusCode() >= 400) {
            $this->logger->warning('Findling: backend returned an error', ['status' => $response->getStatusCode()]);
            return [];
        }

        // Fall 3: Erfolg. Body kann trotzdem kein JSON sein.
        $body = $response->getBody();
        $decoded = is_string($body) ? json_decode($body, true) : null;
        if (!is_array($decoded) || !isset($decoded['results']) || !is_array($decoded['results'])) {
            $this->logger->warning('Findling: malformed backend response');
            return [];
        }

        return $decoded['results'];
    }
}
```

### 4. `info.xml` der PHP-Companion (Minimum, XSD-konform)

```xml
<?xml version="1.0"?>
<info>
    <id>findling</id>
    <name>Findling</name>
    <summary>Zero-config full text search for your files</summary>
    <description><![CDATA[Findet den Inhalt Ihrer Dokumente in der normalen Nextcloud-Suche.
Diese App veraendert Ihre Dateien niemals. Es verlaesst kein Inhalt Ihren Server.
Benoetigt die App "AppAPI" und die External App "Findling Backend".]]></description>
    <version>0.1.0</version>
    <licence>agpl</licence>
    <author>street1983nk</author>
    <namespace>Findling</namespace>
    <category>files</category>
    <website>https://github.com/street1983nk/findling</website>
    <bugs>https://github.com/street1983nk/findling/issues</bugs>
    <repository type="git">https://github.com/street1983nk/findling.git</repository>
    <dependencies>
        <!-- Es gibt KEIN Element fuer App-zu-App-Abhaengigkeiten. app_api wird zur Laufzeit geprueft. -->
        <php min-version="8.2"/>
        <nextcloud min-version="32" max-version="35"/>
    </dependencies>
</info>
```

### 5. Content-Gateway (wortgleich aus `context_chat/lib/Controller/QueueController.php` verifiziert)

```php
#[ExAppRequired]
#[ApiRoute(verb: 'GET', url: '/files/{fileId}')]
public function getFileContents(IRootFolder $rootFolder, int $fileId, string $userId): DataResponse|Http\StreamResponse {
    try {
        $file = $rootFolder->getUserFolder($userId)->getFirstNodeById($fileId);
        if (!$file || !$file instanceof \OCP\Files\File) {
            return new DataResponse(['error' => 'Node is not a file or could not be found.'], Http::STATUS_NOT_FOUND);
        }
        $stream = $file->fopen('r');   // 'r' ist die gesamte Nur-Lesen-Garantie an dieser Stelle
        if (!$stream) {
            return new DataResponse(['error' => 'File could not be opened for reading.'], Http::STATUS_UNPROCESSABLE_ENTITY);
        }
        return new Http\StreamResponse($stream);
    } catch (\Throwable $e) {
        $this->logger->error('Findling: unknown error reading a file: ' . $e->getMessage(), ['exception' => $e]);
        return new DataResponse(['error' => 'Unknown error occurred.'], Http::STATUS_INTERNAL_SERVER_ERROR);
    }
}
```

Voller Pfad von aussen: `GET /ocs/v2.php/apps/findling/files/{fileId}?userId=<uid>`. `#[ExAppRequired]` existiert seit NC 30 in `OCP\AppFramework\Http\Attribute`.

### 6. ExApp-Skelett mit AsyncNextcloudApp

```python
"""Findling ExApp: walking skeleton."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from nc_py_api import AsyncNextcloudApp
from nc_py_api.ex_app import AppAPIAuthMiddleware, anc_app, run_app, set_handlers
from pydantic import BaseModel


async def enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str:
    """Must be async: sync handlers are deprecated and removed in nc_py_api 0.31.0."""
    del nc
    return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Registers PUT /enabled, GET /heartbeat and POST /init.
    set_handlers(app, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)  # heartbeat is always excluded


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class Hit(BaseModel):
    fileId: int  # noqa: N815 -- wire format is defined by the PHP side
    title: str
    snippet: str  # plain text only, the unified search UI does not render markup
    highlights: list[tuple[int, int]] = []


@APP.post("/search")
async def search(
    body: SearchRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> dict[str, list[Hit]]:
    # AsyncNextcloudApp.user is an async property.
    user_id = await nc.user
    if not user_id:
        raise HTTPException(status_code=401, detail="no user in AppAPI header")

    # Phase 1: one hard-wired hit. This is the whole point of the walking skeleton.
    return {
        "results": [
            Hit(
                fileId=0,
                title="Findling canary",
                snippet=f"This result was produced inside the container for {user_id}.",
            )
        ]
    }


if __name__ == "__main__":
    run_app("findling.main:APP", log_level="info")
```

### 7. CI-Gate fuer die info.xml

```bash
XSLT_SHA=<pinned-sha>
curl -sL "https://raw.githubusercontent.com/nextcloud/appstore/${XSLT_SHA}/nextcloudappstore/api/v1/release/pre-info.xslt" -o /tmp/pre-info.xslt
curl -sL "https://raw.githubusercontent.com/nextcloud/appstore/${XSLT_SHA}/nextcloudappstore/api/v1/release/info.xsd"     -o /tmp/info.xsd

for f in php/appinfo/info.xml backend/appinfo/info.xml; do
  xsltproc /tmp/pre-info.xslt "$f" | xmllint --noout --schema /tmp/info.xsd - || exit 1
done
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `exAppRequestWithUserInit()` | `exAppRequest()` | AppAPI 3.0.0 | Alte Beispiele im Netz nicht uebernehmen; die deprecatete Methode ruft intern dasselbe |
| Docker Socket Proxy als Deploy-Ziel | HaRP mit FRP-Tunnel | NC 32 aufwaerts, DSP soll mit NC 35 entfallen | Der Container braucht `frpc` und lauscht auf einem Unix-Socket statt auf einem TCP-Port |
| Synchrone nc_py_api-Handler (`NextcloudApp`, `nc_app`) | `AsyncNextcloudApp`, `anc_app`, async `enabled_handler` | nc_py_api 0.30.x deprecatet, Entfernung in 0.31.0 | Alle offiziellen Beispiele (`to_gif` und Verwandte) sind noch synchron und duerfen nicht 1:1 kopiert werden |
| Multi-Arch per QEMU-Emulation | Native `ubuntu-24.04-arm`-Runner | Allgemein verfuegbar seit 07.08.2025, in oeffentlichen Repos kostenlos | Loest die dokumentierte 90-Minuten-Build-Falle vollstaendig auf; das Nextcloud-Referenzworkflow nutzt sie noch nicht |
| AppAPI spricht Docker-API 1.41 | `DOCKER_API_VERSION = 'v1.44'` | nach app_api Nr. 712 (November 2025) | Docker 29 funktioniert wieder; die lokal installierte 29.5.2 ist kompatibel |
| `IProvider` allein | `IProvider` plus optional `IFilteringProvider`, `IInAppSearch` | NC 28 | Filter sind moeglich, aber nicht Phase 1; `IExternalProvider` (NC 32) bleibt tabu |

**Deprecated/outdated:**
- `exAppRequestWithUserInit()`: durch `exAppRequest()` ersetzt
- Synchrone Entry-Points von nc_py_api: fallen in 0.31.0 weg
- Docker Socket Proxy: soll mit NC 35 entfallen
- Die Formulierung "PHP-App muss `app_api` als Abhaengigkeit fuehren" aus STACK.md: technisch nicht umsetzbar, ersetzt durch den Laufzeit-Guard

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | PHP >= 8.2 ist die richtige Untergrenze fuer NC 32 bis 34 | Standard Stack | CI-Matrix laeuft auf einer nicht unterstuetzten PHP-Version; billig zu korrigieren, indem `icewind1991/nextcloud-version-matrix` die Version aus der info.xml ableitet (so macht es der offizielle Workflow) |
| A2 | SQLite reicht als CI-Datenbank fuer Phase 1 | Frage 5 | Nur relevant, wenn Phase 1 doch eigene Tabellen anlegt; dann Postgres oder MariaDB in die Matrix |
| A3 | Ein einziger Integrationslauf (stable34) genuegt fuer die PR-Rueckmeldung, volle Matrix nur nach Zeitplan | Frage 5 | Ein Bruch auf stable32 faellt spaeter auf; Gegenmittel ist der geplante `schedule`-Lauf |
| A4 | `nc._session.download2stream()` ist der pragmatische Weg zum Content-Gateway | Pitfall 4 | Es ist eine private API. Bei einem nc_py_api-Update kann sie sich aendern. Gekapselt in `nc/client.py` ist der Schaden auf eine Datei begrenzt; die Alternative ist ein eigener httpx-Client mit selbst gebautem Auth-Header |
| A5 | Psalm oder PHPStan sind fuer vier PHP-Klassen optional, `php -l` plus XSD reichen | Frage 7 | Typfehler in der PHP-App fallen erst zur Laufzeit auf. Bei so wenig Code vertretbar; ab Phase 2 (Queue, Mapper) sollte statische Analyse dazukommen |
| A6 | Der Store akzeptiert eine ExApp-Einreichung aus einem Mono-Repo-Unterverzeichnis | Standard Stack, Alternatives | `krankerl` erwartet ein Repo-Root; ein Makefile-Ziel `appstore` mit `tar` loest das. Falls der Store weitere Annahmen macht (Verzeichnisname im Tarball muss die App-ID sein), faellt das erst beim Upload auf. Konkret gilt: der Tarball muss ein Wurzelverzeichnis mit exakt dem App-ID-Namen enthalten |
| A7 | HaRP laesst sich lokal unter Docker Desktop auf Windows sinnvoll betreiben | Environment Availability | Falls nicht, bleibt fuer die lokale Entwicklung der `manual_install`-Daemon (funktioniert nachweislich, siehe CI), und der HaRP-Test wandert in CI oder auf eine Linux-VM |
| A8 | Es gibt serverseitig kein zusaetzliches Timeout auf einen Suchanbieter | Frage 3, Diagramm | Falls doch, waere unser 2-Sekunden-Wert davon nur unterschritten; das Risiko ist gering und die Richtung ungefaehrlich |

---

## Open Questions

1. **App-ID-Konflikt zwischen CONTEXT.md und der Store-Konvention**
   - Was wir wissen: App-IDs sind ueber beide Store-Bereiche eindeutig; `findling` und `findling_backend` sind beide frei; das genannte Vorbild vergibt die kurze ID an die PHP-App.
   - Was unklar ist: CONTEXT.md sagt woertlich "ExApp = `findling`". Beide Varianten sind zulaessig, aber nur eine kann gewaehlt werden, und die Wahl ist nach der CSR irreversibel.
   - Empfehlung: PHP-Companion = `findling`, ExApp = `findling_backend`. Der Planer soll dafuer einen `checkpoint:human-verify`-Task **vor** dem CSR-Task vorsehen.

2. **Wie sieht der Fest-Treffer aus, damit er als Beweis taugt?**
   - Was wir wissen: Der Owner will "ein Suchtreffer aus dem Container in der normalen Suchleiste", video-tauglich.
   - Was unklar ist: Ob der Treffer auf eine echte Datei zeigen soll (dann braucht es eine `fileId` und der `resourceUrl` funktioniert) oder ob ein Treffer ohne Ziel reicht.
   - Empfehlung: Der Treffer traegt einen im Container erzeugten Beweis-String (Hostname des Containers plus Zeitstempel plus die Nutzer-ID aus dem Auth-Header). Das ist unfaelschbar, ohne dass eine Datei existieren muss, und im Video sofort verstaendlich. Zusaetzlich ein zweiter Treffer, der auf eine echte Datei aus dem Referenzkorpus zeigt, damit der `resourceUrl`-Pfad ebenfalls bewiesen ist.

3. **Signiert man den Mono-Repo-Tarball aus einem Unterverzeichnis?**
   - Was wir wissen: `occ integrity:sign-app --path=<dir>` erwartet ein App-Verzeichnis; der offizielle Workflow entpackt den Tarball und signiert das entpackte Verzeichnis.
   - Was unklar ist: Ob `krankerl` in einem Mono-Repo brauchbar ist.
   - Empfehlung: Fuer Phase 1 nicht loesen. Ein `make appstore`-Ziel, das per `tar` ein Verzeichnis mit dem App-ID-Namen baut, reicht und ist in Phase 5 sowieso Thema. In Phase 1 nur sicherstellen, dass die Verzeichnisstruktur diese Loesung nicht verbaut.

4. **Verhalten des AppAPI-Proxys bei parallelen Suchanfragen**
   - Was wir wissen: Jeder Provider bekommt einen eigenen Browser-Request, also einen eigenen PHP-Prozess. Der Container sieht mehrere gleichzeitige `/search`-Aufrufe.
   - Was unklar ist: Ob HaRP bzw. FRP eine Verbindungsobergrenze hat, die bei vielen Nutzern greift.
   - Empfehlung: In Phase 1 nicht relevant (ein Nutzer). Als Messpunkt in den Lasttest der Phase 5 aufnehmen.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Docker | Lokale Test-Nextcloud, Image-Bau, HaRP | ja | 29.5.2 (Desktop, WSL2-Backend) | - |
| Git | Repo | ja | 2.54.0.windows.1 | - |
| GitHub CLI | Repo-Anlage, PR-Verwaltung | ja | 2.92.0 | Webinterface |
| Python | ExApp | ja | 3.13.1 | - |
| uv | Abhaengigkeiten | ja | 0.11.7 (aktuell waere 0.12.5) | `uv self update` |
| OpenSSL | CSR-Erzeugung | ja | 3.5.6 | - |
| Node / npm | nicht benoetigt in Phase 1 | ja | 22.21.0 / 11.14.1 | - |
| curl | Diagnose | ja | 8.19.0 | - |
| **PHP CLI** | `php -l`, lokales `occ` | **nein** | - | Alles PHP laeuft im Container der Test-Nextcloud (`docker exec ... php occ ...`) oder in CI |
| **Composer** | PHP-Autoload, Psalm | **nein** | - | Im Container bzw. in CI; die Companion-App braucht keine Runtime-Abhaengigkeiten |
| **xmllint / xsltproc** | info.xml-Validierung | **nein** | - | Nur CI-Gate (ubuntu-Runner haben libxml2-utils und xsltproc). Lokal notfalls per Container |
| **make** | Makefile-Ziele | **nein** | - | Git-Bash-Skripte oder `docker run` statt Makefile; alternativ make ueber Chocolatey/Scoop nachziehen |

**Missing dependencies with no fallback:** keine.

**Missing dependencies with fallback:**
- PHP, Composer, xmllint, xsltproc und make fehlen lokal. Alle vier sind entweder im Nextcloud-Testcontainer oder auf den GitHub-Runnern vorhanden. Konsequenz fuer den Plan: **kein Task darf voraussetzen, dass PHP lokal ausfuehrbar ist.** PHP-Syntaxpruefung und XSD-Validierung sind CI-Tasks, nicht lokale Vorbedingungen. Die lokale Verifikation laeuft ueber die Test-Nextcloud im Container.

Zusaetzliche Beobachtung: das Docker-Desktop-Backend laeuft ueber WSL2. Fuer `juliusknorr/nextcloud-docker-dev` bzw. eine eigene compose-Datei ist das der uebliche Weg; Pfad-Mounts von Windows nach Linux sind langsam, deshalb sollte das Nextcloud-Arbeitsverzeichnis moeglichst im WSL2-Dateisystem liegen und nicht unter `C:\Users\...`.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | ja | Keine eigene Authentifizierung. ExApp-Zugang ausschliesslich ueber `AppAPIAuthMiddleware` (signaturgeprueft), PHP-Zugang ueber die Nextcloud-Session. `#[ExAppRequired]` sperrt den Content-Gateway gegen Browser und normale Nutzer |
| V3 Session Management | nein | Es gibt keine eigene Session. Der Container ist zustandslos je Request |
| V4 Access Control | ja | Die einzige Autorisierungsentscheidung faellt in `getUserFolder($userId)->getFirstNodeById($fileId)`. Die Nutzer-ID kommt nur aus dem signierten Header, nie aus dem Body. `set_user()` ist per Gate verboten |
| V5 Input Validation | ja | Pydantic-Modelle fuer jeden Request-Body; `limit` mit Ober- und Untergrenze; `fileId` als `int` typisiert (Nextcloud casted es aus der Route) |
| V6 Cryptography | ja (indirekt) | Nichts selbst bauen. Signaturen: `openssl` fuer die CSR, `occ integrity:sign-app` fuer den Tarball. Die AppAPI-Header-Signatur macht nc_py_api |
| V7 Error Handling / Logging | ja | Fehler nie stumm schlucken: Backend nicht erreichbar wird auf `info` geloggt, Backend-Fehlerstatus auf `warning`. Keine Nutzerinhalte im Log |
| V12 Files | ja | Kernpunkt. Nur `fopen('r')`, kein Schreibpfad, Zugriff nur ueber `fileId` (umbenennungsfest, keine Pfadtraversierung moeglich) |
| V14 Configuration | ja | `frpc`-Binaerdatei mit gepinntem Commit, alle Python-Pins exakt, Actions mit SHA-Pin (so macht es der Nextcloud-Workflow durchgehend) |

### Known Threat Patterns for Nextcloud ExApp plus PHP-Companion

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Nutzer-ID aus dem Request-Body (Rechteumgehung fuer jeden, der den Proxy erreicht) | Elevation of Privilege | ID ausschliesslich aus `AUTHORIZATION-APP-API`; Body-Feld `userId` mit 400 ablehnen |
| Impersonation ueber `set_user()` bzw. AppAPI-Systemrechte | Elevation of Privilege | Genau eine Client-Fabrik in `nc/client.py`, kein Systempfad, `set_user` im statischen Gate verboten |
| Inhaltsabfluss ueber Snippets vor der Rechtepruefung | Information Disclosure | Snippet entsteht erst nach bestandener Pruefung (in Phase 1 trivial, weil es keinen Inhalt gibt; das Protokollfeld ist aber schon so gebaut) |
| Zerstoerung von Nutzerdateien im OCR- oder Fehlerpfad | Tampering | Nur-Lesen-Invariante mit zwei CI-Gates (IDX-07), kein Rueckschreibpfad im Code |
| Pfadtraversierung beim Dateizugriff | Tampering / Information Disclosure | Zugriff ausschliesslich ueber `fileId`, nie ueber Pfadstrings |
| Kompromittierter Signierschluessel | Spoofing | Privater Schluessel nur als GitHub-Secret, niemals im Repo; Widerrufsprozess ist dokumentiert und kostet Tage |
| Supply-Chain ueber ungepinnte Actions oder Binaerdateien | Tampering | Alle Actions mit Commit-SHA pinnen, `frpc` von gepinntem Commit, Python-Pins exakt |
| Brute-Force-Zaehler durch fehlschlagende Proxy-Requests | Denial of Service | `bruteforce_protection` in der Routendefinition bewusst nur auf `[401]` setzen, nicht auf `[500]`, damit ein Backend-Fehler nicht die Instanz-IP sperrt |
| Denial of Service durch haengenden Provider | Denial of Service | Hartes Timeout von 2 Sekunden, leeres Ergebnis statt Warten |

---

## Sources

### Primary (HIGH confidence, Quellcode direkt gelesen am 15.08.2026)

- `nextcloud/app_api` `lib/PublicFunctions.php` , Signatur `exAppRequest(string, string, ?string, string, array, array, ?IRequest): array|IResponse`, Deprecation von `exAppRequestWithUserInit`
- `nextcloud/app_api` `lib/Service/AppAPIService.php` , `prepareRequestToExApp` (Default-Timeout 3, `http_errors=false`, GET per `http_build_query`), `requestToExAppInternal` (Exception wird zu `['error' => ...]`)
- `nextcloud/app_api` `lib/Service/ExAppService.php` , `getAppInfo` (JSON- und XML-Weg, Anhebung von `routes` nach `external-app`), `getLatestExAppInfoFromAppstore` (info.xml kommt aus dem Release-Archiv)
- `nextcloud/app_api` `lib/Command/ExApp/Register.php` , Optionen `--info-xml`, `--json-info`, `--wait-finish`, `--env`, `--mount`
- `nextcloud/app_api` `lib/DeployActions/DockerActions.php` , `DOCKER_API_VERSION = 'v1.44'`
- `nextcloud/server` `lib/public/Search/IProvider.php` , `getOrder()` nullable seit 28, `null` versteckt den Provider
- `nextcloud/server` `lib/public/Search/SearchResultEntry.php` , Felder, `attributes` nur `array<string,string>`
- `nextcloud/server` `lib/public/Search/ISearchQuery.php`, `SearchResult.php` , `complete()` und `paginated()`
- `nextcloud/server` `lib/public/AppFramework/Bootstrap/IRegistrationContext.php` , `registerSearchProvider`, @since 20.0.0
- `nextcloud/server` `lib/public/AppFramework/Http/Attribute/ExAppRequired.php` , @since 30.0.0
- `nextcloud/server` `core/src/components/UnifiedSearch/SearchResult.vue` , `{{ subline }}` ohne `v-html`
- `nextcloud/server` `core/Controller/UnifiedSearchController.php` , ein Request je Provider
- `nextcloud/server` `apps/files/lib/Search/FilesSearchProvider.php` , konkrete IProvider-Vorlage
- `nextcloud/appstore` `nextcloudappstore/api/v1/release/info.xsd` , `dependencies` ohne App-Element, `id`-Pattern, `external-app` ohne `routes`
- `nextcloud/appstore` `nextcloudappstore/api/v1/release/pre-info.xslt` , Normalisierung vor der Validierung, Template `external-app`
- `nextcloud/context_chat` `lib/AppInfo/Application.php`, `lib/Service/LangRopeService.php`, `lib/Controller/QueueController.php`, `appinfo/info.xml` , Guard-Muster, Content-Gateway, Zwei-App-Muster
- `nextcloud/context_chat_backend` `appinfo/info.xml`, `Makefile`, `supervisord.conf`, `harp_connect.sh`, `dockerfile_scripts/install_frpc.sh`, `.github/workflows/integration-test.yml`, `.github/workflows/appstore-build-publish.yml`, `.github/workflows/docker-build-publish.yml` , CI-Rezept, HaRP-Aufbau, Signatur- und Multi-Arch-Workflow
- `cloud-py-api/nc_py_api` `nc_py_api/ex_app/integration_fastapi.py`, `uvicorn_fastapi.py`, `misc.py`, `_session.py`, `nextcloud.py` , `set_handlers`, `AppAPIAuthMiddleware`, Unix-Socket unter HaRP, `ocs()` parst immer JSON, `user` als async property
- `cloud-py-api/nc_py_api` `examples/as_app/to_gif/` , Referenz-Makefile mit `--json-info`, info.xml mit `<routes>`
- `nextcloud/app-certificate-requests` README plus Verzeichnisse `context_chat/` und `context_chat_backend/` , CSR-Ablauf, zwei Zertifikate

### Primary (HIGH confidence, offizielle Dokumentation)

- https://raw.githubusercontent.com/nextcloud/documentation/master/developer_manual/app_publishing_maintenance/code_signing.rst , openssl-Kommandos woertlich, `occ integrity:sign-app`, Fehlerklassen
- https://raw.githubusercontent.com/nextcloud/documentation/master/developer_manual/app_publishing_maintenance/publishing.rst , Store-Regeln (AGPL, kein "Nextcloud" im Namen, Uninstall-Sauberkeit)
- https://raw.githubusercontent.com/nextcloud/documentation/master/developer_manual/app_publishing_maintenance/release_automation.rst , `APPSTORE_TOKEN`, Push-Action
- https://raw.githubusercontent.com/nextcloud/documentation/master/developer_manual/exapp_development/tech_details/api/routes.rst , `<routes>`-Format, `access_level`-Werte, automatische Registrierung
- https://raw.githubusercontent.com/nextcloud/documentation/master/admin_manual/exapps_management/ManagingDeployDaemons.rst , `app_api:daemon:register` mit allen HaRP-Optionen

### Primary (HIGH confidence, Live-APIs)

- https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json , 741 Apps, `findling` frei
- https://apps.nextcloud.com/api/v1/appapi_apps.json , 25 ExApps, `findling_backend` frei
- https://pypi.org/pypi/{ruff,pyright,vulture,pytest,uv,fastapi,nc-py-api,starlette,httpx}/json , aktuelle Versionen
- GitHub API `repos/nextcloud/app-certificate-requests/pulls?state=closed` , gemessene Merge-Zeiten Juli/August 2026
- `slopcheck install ...` , Paket-Legitimitaet, 9 von 9 OK

### Secondary (MEDIUM confidence)

- https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/ , native arm64-Runner allgemein verfuegbar
- https://github.blog/changelog/2025-01-16-linux-arm64-hosted-runners-now-available-for-free-in-public-repositories-public-preview/ , kostenlos fuer oeffentliche Repos, 4 vCPUs
- https://learn.arm.com/learning-paths/cross-platform/github-arm-runners/public-repos/ , Multi-Arch-Aufbau mit nativen Runnern
- `.planning/research/ARCHITECTURE.md`, `STACK.md`, `PITFALLS.md` , Projekt-Vorrecherche, hier punktuell korrigiert
- `C:\Users\Student\nextcloud-mcp-connector\.planning\research\PITFALLS.md` , Store- und Zertifikatswissen aus dem Schwesterprojekt

---

## Metadata

**Confidence breakdown:**
- Integrationsprotokoll (IProvider plus exAppRequest, Fehlerform, Timeout): **HIGH** , beide Seiten im Quellcode gelesen, keine Ableitung noetig
- Subline-Rendering (Frage 2): **HIGH** , Vue-Template direkt gelesen, eindeutig
- AppAPI-Handshake und nc_py_api: **HIGH** , `set_handlers` und Middleware im Quellcode gelesen
- CI-Rezeptur: **HIGH** , aus einem laufenden, gepflegten Workflow uebernommen, nur auf unser Projekt uebertragen
- CSR-Prozess und Store-Identitaet: **HIGH** , offizielle Doku woertlich plus live gepruefte Namensverfuegbarkeit plus gemessene Merge-Zeiten
- info.xml-Validierungsweg: **HIGH** , XSLT und XSD gelesen, Widerspruch zum publizierten context_chat_backend aufgeloest
- Multi-Arch mit nativen Runnern: **MEDIUM-HIGH** , Verfuegbarkeit belegt, aber im Nextcloud-Oekosystem noch nicht als Muster etabliert
- HaRP unter Docker Desktop auf Windows: **MEDIUM** , Mechanik verstanden, Betrieb auf dieser Topologie nicht selbst geprueft
- Standard Stack (PHP-Versionen, Store-Verpackung aus dem Mono-Repo): **MEDIUM** , siehe Assumptions Log A1, A5, A6

**Research date:** 2026-08-15
**Valid until:** 2026-09-14 (30 Tage). Frueher neu pruefen, wenn nc_py_api 0.31.0 erscheint (Entfernung der Sync-API) oder AppAPI ein Major-Release veroeffentlicht.

---
*Phase research for: 01-integrationsbeweis*
*Researched: 2026-08-15*
