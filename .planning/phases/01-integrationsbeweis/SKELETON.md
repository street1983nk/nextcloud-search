# Walking Skeleton , Findling (Nextcloud Zero-Config-Suche)

**Phase:** 1 (Integrationsbeweis)
**Generated:** 2026-08-15

## Capability Proven End-to-End

Ein angemeldeter Nextcloud-Nutzer tippt einen Suchbegriff in die normale Suchleiste und sieht einen Treffer, der nachweislich im ExApp-Container entstanden ist, und derselbe Container liest den Inhalt einer konkreten Datei rechtegeprüft zurück, ohne sie zu verändern.

Der Beweis ist unfälschbar, weil die Trefferzeile Hostname des Containers, Zeitstempel und die aus dem signierten AppAPI-Header gelesene Nutzer-ID trägt. Ein hartkodierter Treffer auf der PHP-Seite würde die CI-Assertion nicht bestehen.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Integrationsprotokoll | PHP-Companion implementiert `OCP\Search\IProvider` und ruft `OCA\AppAPI\PublicFunctions::exAppRequest()` | `IExternalProvider` ist in der Such-UI per Schalter default-aus und würde Zero-Config sofort zerstören. `exAppRequestWithUserInit()` ist seit AppAPI 3.0.0 deprecated. Es gibt keinen anderen vom Server unterstützten Weg in den Container |
| Zwei-App-Modell und IDs | Companion `findling` (Store-Bereich Apps), ExApp `findling_backend` (External Apps) | Exakt das context_chat/context_chat_backend-Muster, das AppAPI-Nutzer kennen. IDs sind über beide Store-Bereiche eindeutig und nach dem CSR-Merge irreversibel, deshalb Freeze vor dem ersten Commit |
| Repo-Form | Mono-Repo mit `php/` und `backend/` | Ein Solo-Entwickler zahlt bei zwei Repos nur Synchronisationskosten. Beide Teile werden gekoppelt versioniert. Die Store-Verpackung baut in Phase 5 per Makefile-Ziel einen Tarball mit App-ID-Wurzelverzeichnis aus dem Unterordner |
| Proxy-Kapselung | Genau eine PHP-Klasse (`ExAppService`) ruft `exAppRequest`, mit `['timeout' => 2]` | Timeout, Fehlerform und Degradation leben an einer Stelle. AppAPI setzt `http_errors = false` und liefert Timeouts als `['error' => ...]`, also müssen drei Fälle getrennt geprüft werden, sonst zerstört ein Fatal Error die gesamte Suchanfrage des Nutzers |
| nc-Kapselung | Genau ein Python-Modul (`findling/nc/client.py`) importiert `nc_py_api` | Macht die Nur-Lesen-Invariante als statischen Test formulierbar und begrenzt ein nc_py_api-Update auf eine Datei. Alle anderen Module beziehen Middleware, Handler und Nutzer-ID über diese Grenzschicht |
| Identität des suchenden Nutzers | Ausschließlich aus dem signierten Header `AUTHORIZATION-APP-API` über `Depends(anc_app)`; ein Body-Feld `userId` wird mit 400 abgelehnt, `set_user()` ist per Gate verboten | Eine Nutzer-ID im Body wäre eine Rechteumgehung für jeden, der den Proxy erreicht, und fällt in keinem funktionalen Test auf |
| Rechte-Auflösung bei Dateizugriff | PHP-Content-Gateway, `#[ExAppRequired] GET /files/{fileId}?userId=`, `getUserFolder($userId)->getFirstNodeById($fileId)->fopen('r')` | Die einzige nicht driftende Wahrheitsquelle. Ein zweites Rechtemodell in Python würde Groupfolder, External Storage und Verschlüsselung verlieren. Zugriff nur über int-fileId, damit Pfadtraversierung strukturell ausgeschlossen ist |
| Datenformat der Treffer | `snippet` ist Klartext, Hervorhebungen reisen als Zeichenoffsets in `highlights` | Die Unified-Search-UI rendert die Subline als Vue-Interpolation `{{ subline }}` ohne `v-html`. HTML erschiene dem Nutzer wörtlich. Das Protokoll wird in Phase 1 eingefroren, damit Phase 2 nichts umbauen muss |
| Laufzeit der ExApp | Python 3.13 + uv, FastAPI, `AsyncNextcloudApp` mit async `enabled_handler`, `nc-py-api[app]` 0.30.3 | Die synchrone API fällt in nc_py_api 0.31.0 weg. Tests laufen mit `error::DeprecationWarning`, damit ein synchroner Handler sofort auffällt |
| Container und Deploy-Ziel | `python:3.13-slim-trixie`, supervisord mit zwei Programmen (App und `frpc`), kein `EXPOSE`, HaRP als Ziel | Ist `HP_SHARED_KEY` gesetzt, bindet `run_app()` an `/tmp/exapp.sock`. Ohne `frpc` im Image ist der Container stumm unerreichbar, obwohl uvicorn sauber startet. Debian statt musl, weil tantivy und onnxruntime keine musl-Wheels haben |
| Multi-Arch | Native Runner `ubuntu-24.04` und `ubuntu-24.04-arm`, `push-by-digest` plus `imagetools create` | QEMU macht aus einem Fünf-Minuten-Build einen Neunzig-Minuten-Build. Native arm64-Runner sind für öffentliche Repos kostenlos. Zielhardware ist ausdrücklich ARM |
| Persistenz | Container-Volume `APP_PERSISTENT_STORAGE`, in Phase 1 nur `_version.info` | Der Index kommt in Phase 2. Das Volume existiert ab Tag eins, damit die Topologie später nicht wechselt |
| Testinstanz und CI | `nextcloud/server`-Checkout plus `composer run serve`, SQLite, `manual_install`-Daemon, ExApp nativ | `occ` ist damit ein direkter Aufruf statt `docker exec`, und die Server-Matrix stable32/33/34 funktioniert ohne Image-Tags. Der Docker-Deploy-Pfad gehört zur Topologie-Prüfung in Phase 5 |
| Qualitäts- und Sicherheitsgates | ruff (E,F,I,UP,B,ASYNC,S,SIM,C4,RUF,PT,RET,A,ISC) plus format, pyright basic, vulture 80, pytest, Gate A (AST), Gate B (Prüfsummen), info.xml über `pre-info.xslt` und `info.xsd` | Alle Gates existieren vor dem Fachcode. Gate A verhindert künftige Schreibpfade, Gate B fängt Schreibvorgänge über Wege, die Gate A nicht kennt. Nur eines von beiden hätte die dokumentierte Datenverlustklasse nicht verhindert |
| Verzeichnislayout | `php/{appinfo,lib/{AppInfo,Search,Service,Controller}}`, `backend/src/findling/{main.py,api,nc,tools}`, `testdata/corpus/`, `.github/workflows/`, `docs/`, `scripts/dev/` | Verzeichnisname der PHP-App muss in der Testinstanz exakt die App-ID sein, sonst findet der Autoloader die Klassen nicht |

## Stack Touched in Phase 1

- [x] Projekt-Gerüst: uv-Projekt, fünf Python-Gates, PHP-Syntaxgate, öffentliches AGPL-Repo (Plan 01, 02, 05)
- [x] Routing, echt: `IProvider` in der Unified Search, `POST /search` in der ExApp, `GET /files/{fileId}` als Content-Gateway (Plan 04, 05)
- [x] Datenzugriff, echt: Leselauf über den Content-Gateway auf echte Dateien einer echten Nextcloud (Plan 08). Ein Schreibpfad existiert bewusst nicht und ist per Gate verboten, das ersetzt in diesem Projekt den "einen echten Write"
- [x] UI-Interaktion: Suchbegriff in der Nextcloud-Suchleiste erzeugt eine Ergebnisgruppe mit einem Container-Treffer (Plan 06, inklusive Sichtprobe des Owners)
- [x] Deployment: Multi-Arch-Image in ghcr, Handshake-Rauchprobe auf amd64 und arm64, plus dokumentierter lokaler Volldurchlauf über `scripts/dev/` (Plan 06, 07)

## Out of Scope (Deferred to Later Slices)

Diese Liste verhindert, dass spätere Phasen die Minimalität von Phase 1 neu verhandeln.

- Jede Form von Indexierung: Crawl, Queue, Tantivy, Wiederaufsetzbarkeit, ACL-Tabelle (Phase 2)
- Echte Suchergebnisse: Der Treffer in Phase 1 ist fest verdrahtet, es gibt keinen Volltext, kein Ranking, keine Snippets aus Dokumenten, keine Suchoperatoren (Phase 2)
- Der finale PHP-Recheck pro Treffer und die Snippet-Erzeugung nach bestandener Prüfung (COMP-04, Phase 2)
- Event-Listener, ETag-Reconcile, Löschungen und Unshares (Phase 3)
- OCR in jeder Form, inklusive Scratch-Kopien und Seiten-, Zeit- und RAM-Deckeln (Phase 3)
- Admin-Statusseite, Deckungsgrad, Pro-Datei-Diagnose, Vorab-Schätzung, Ausschluss-Regeln (Phase 4)
- Lasttest auf 4-GB-ARM, Rechte-Paritätstest über sechs Szenarien, AIO- und compose-Topologie, Uninstall-Cleanup, signierte Store-Einreichung (Phase 5)
- Semantik: Embeddings, Vektorschema, RRF-Hybrid (Phase 6, Release v1.1)
- Standalone-Betrieb ohne AppAPI (v2)
- Statische PHP-Analyse mit Psalm oder PHPStan (ab Phase 2 sinnvoll, bei vier Klassen noch Luxus)
- Volle CI-Matrix stable32/33/34: In Phase 1 läuft nur stable34 auf Push, die Matrix wird ein Zeitplan-Lauf

## Subsequent Slice Plan

Jede spätere Phase legt eine vertikale Scheibe auf dieses Skelett, ohne seine architektonischen Entscheidungen zu ändern:

- **Phase 2:** Nutzer findet den Inhalt eines echten Dokuments. Der fest verdrahtete Treffer wird durch Tantivy-Kandidaten plus SQLite-ACL-Vorfilter plus finalen PHP-Recheck ersetzt. Das Antwortprotokoll aus Phase 1 bleibt unverändert, nur die Quelle der Werte ändert sich.
- **Phase 3:** Was der Nutzer gerade ablegt oder teilt, ist kurz darauf auffindbar, und gescannte PDFs werden lesbar. Der Ereignisweg läuft über dieselbe PHP-App, OCR arbeitet auf Scratch-Kopien, Gate B bleibt der Wächter.
- **Phase 4:** Der Admin sieht Zustand und Gründe, bevor Nutzer etwas vermissen. Neue Routen in der Companion-App, keine neue Integrationsmechanik.
- **Phase 5:** Belegte Zahlen auf echter ARM-Hardware, Paritätstest als Dauergate, signierte v1.0-Einreichung mit den Zertifikaten aus Phase 1.
- **Phase 6:** Umschreibungen finden Dokumente. Zweiter Retrieval-Zweig hinter derselben ACL-Kette, dasselbe Protokoll, dasselbe RAM-Budget.
