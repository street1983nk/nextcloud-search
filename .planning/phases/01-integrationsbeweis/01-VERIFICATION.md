---
phase: 01-integrationsbeweis
verified: 2026-08-15T17:00:00Z
status: passed_with_conditions
score: 4.5/5 success criteria verified
overrides_applied: 0
gaps:
  - truth: "Beide CSR-Vorgaenge sind eingereicht, bevor der erste Bau-Commit der Folgephase entsteht (Success Criterion 4, PKG-02, zweite Haelfte)"
    status: partial
    reason: "App-ID-Freeze ist vollstaendig belegt (docs/store-identity.md, live gegen apps.json/appapi_apps.json geprueft, 0 Treffer). Beide RSA-4096-Schluesselpaare und CSRs existieren, beide Fork-Branches (findling-csr, findling-backend-csr) sind gepusht, beide PR-Texte und gh-pr-create-Kommandos liegen fertig vor. Die tatsaechliche PR-Einreichung gegen nextcloud/app-certificate-requests ist jedoch noch nicht erfolgt: gh pr list zeigt fuer street1983nk in diesem Repo nur PR #1160 (Schwesterprojekt mcp_connector), keine PR fuer findling oder findling_backend."
    artifacts:
      - path: "docs/store-identity.md"
        issue: "Certificate-status-Tabelle enthaelt Platzhalter fuer PR-Link, Einreichungs- und Merge-Datum, die noch nicht gefuellt sind"
    missing:
      - "Owner fuehrt die zwei vorbereiteten gh-pr-create-Kommandos aus docs/store-identity.md aus (Task 3 von Plan 01-03)"
      - "PR-Links und Einreichungsdatum in die Certificate-status-Tabelle eintragen"
    condition: "Dies ist kein Implementierungsmangel, sondern ein ausstehender, nicht automatisierbarer Owner-Schritt (checkpoint:human-action laut 01-CONTEXT.md). Das Erfolgskriterium selbst verlangt Einreichung 'vor dem ersten Bau-Commit der Folgephase' (Phase 2), nicht vor Abschluss von Phase 1. Dies ist daher als Gate-Bedingung vor Phase 2 zu fuehren, nicht als Phase-1-Fehlschlag."
human_verification:
  - test: "Owner-Sichtprobe: Suchbegriff in Nextcloud-Suchleiste eingeben und den Findling-Treffer aus dem Container sehen"
    expected: "Treffer mit 'produced inside container ...' in der Unified Search (Web-UI)"
    why_human: "Bereits laut 01-06-SUMMARY am 15.08.2026 vom Owner durchgefuehrt und bestanden (dokumentierte Statuszeile); wird hier nachrichtlich aufgefuehrt, keine offene Handlung mehr"
---

# Phase 1: Integrationsbeweis Verification Report

**Phase Goal:** Ein Suchtreffer, den der ExApp-Container liefert, erscheint nachweislich in der normalen Nextcloud-Unified-Search, und die Store-Identitaet steht unwiderruflich fest.
**Verified:** 2026-08-15
**Status:** passed_with_conditions
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths (Success Criteria aus ROADMAP.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nutzer sieht einen Findling-Treffer aus dem Container in der Unified Search (Web-UI + OCS-Client, via `IProvider`, nicht `IExternalProvider`) | VERIFIED | `php/lib/Search/Provider.php` implementiert `OCP\Search\IProvider` (Docstring begruendet explizit den Verzicht auf `IExternalProvider`); CI-Job `walking-skeleton` im Workflow-Run 31883258930 (headSha 83716c0, push) ist `success`. Die Assertions in `.github/workflows/integration.yml` pruefen live per `jq`: `entries.length > 0`, `subline` enthaelt `produced inside container` UND `testuser`, `subline` enthaelt kein `<`. Owner-Sichtprobe laut 01-06-SUMMARY am 15.08.2026 bestanden. |
| 2 | Container liest Dateiinhalt ueber `#[ExAppRequired]`-Endpunkt als Stream; Nutzer ohne Recht bekommt nichts | VERIFIED | `php/lib/Controller/GatewayController.php`: `#[ExAppRequired]`, `getUserFolder($userId)->getFirstNodeById($fileId)->fopen('r')`, 404 fuer nicht-vorhanden/nicht-sichtbar (nicht unterscheidbar). `backend/src/findling/nc/client.py::fetch_file_stream` nutzt `nc._session.download2stream(...)` (nicht `ocs()`, das fuer Binaerdaten ungeeignet waere) und liefert `None` bei 404/998. CI beweist live: Schritt "Read every file through the content gateway" liest 7 Korpusdateien vollstaendig als `corpus`-Besitzer (`read=7 not-accessible=0`), Schritt "Read the same file ids as a user without access" liefert fuer einen fremden Nutzer `read=0 not-accessible=7 bytes=0` , Rechteverweigerung ist ein Laufzeit-Test, kein Codereview. |
| 3 | Multi-Arch-Image (amd64+arm64, Debian-slim) baut in CI und startet auf beiden Architekturen bis zum AppAPI-Handshake | VERIFIED | `backend/Dockerfile` auf `python:3.13-slim-trixie` (digest-gepinnt), `supervisord` fuehrt `app` + `frpc`. CI-Workflow `docker.yml`, Run bei headSha 83716c0: `success`. Nativer Build auf `ubuntu-24.04` (amd64) und `ubuntu-24.04-arm` (arm64), je mit Heartbeat-Rauchprobe vor dem Push. Live-Manifest-Check: `docker buildx imagetools inspect ghcr.io/street1983nk/findling_backend:dev` zeigt `Platform: linux/amd64` und `Platform: linux/arm64` im selben Index. |
| 4 | Beide App-IDs eingefroren und beide CSR-Vorgaenge eingereicht, bevor der erste Bau-Commit der Folgephase entsteht | PARTIAL (siehe Gaps) | App-ID-Freeze VERIFIED: `docs/store-identity.md`, live gegen `apps.json`/`appapi_apps.json` mit 0 Treffern geprueft, Freeze-Commit `5fecd10`. CSR-Vorbereitung VERIFIED: zwei RSA-4096-Schluesselpaare + CSRs erzeugt, CN gegengeprueft, zwei Fork-Branches (`findling-csr`, `findling-backend-csr`) gepusht, PR-Texte + `gh pr create`-Kommandos fertig in `docs/store-identity.md`. CSR-EINREICHUNG NICHT VERIFIZIERT: `gh pr list --repo nextcloud/app-certificate-requests --author street1983nk --state open` liefert ausschliesslich PR #1160 (Schwesterprojekt `mcp_connector`); keine offene PR fuer `findling` oder `findling_backend`. Dies ist der einzige noch offene Owner-Schritt (Task 3 von Plan 01-03, `checkpoint:human-action`). |
| 5 | CI-Gate fuer Nur-Lesen-Invariante aktiv: Testlauf ueber Referenzkorpus belegt per Pruefsumme, dass keine Nutzerdatei veraendert wurde | VERIFIED | Statisches Gate A: `backend/tests/test_readonly_gate.py`, AST-basiert, mit eigenem Selbsttest gegen vier Verstossklassen. Dynamisches Gate B: CI-Job `readonly-gate` haelt `sha256sum` + `stat -c '%n %Y %s'` vor und nach dem Leselauf ueber 7 Korpusdateien fest und vergleicht per `diff`. Live-Beleg des GEWOLLTEN roten Ausschlags: Run 31883309703 (`workflow_dispatch`, `tamper_probe=true`) auf headSha 83716c0 hat `conclusion: failure`, Job-Aufschluesselung zeigt `walking-skeleton: success` und `readonly-gate: failure` , exakt die erwartete gezielte Rot-Meldung ohne den funktionalen Durchstich zu beeintraechtigen. Der regulaere Push-Run auf demselben Commit (31883258930) zeigt beide Jobs `success`. |

**Score:** 4 von 5 Kriterien vollstaendig VERIFIED, 1 Kriterium (#4) zur Haelfte VERIFIED / zur Haelfte als offene Owner-Bedingung dokumentiert.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `php/lib/Search/Provider.php` | `IProvider`-Implementierung, nicht `IExternalProvider` | VERIFIED | Substanzvoll, `getId/getName/getOrder/search` implementiert, ruft `ExAppService` |
| `php/lib/Service/ExAppService.php` | Einziger `exAppRequest`-Aufruf, Vierfach-Fehlerbehandlung | VERIFIED | Timeout 2s, 4 Fehlerpfade (unreachable, >=400, malformed body, malformed shape), Trefferfilterung |
| `php/lib/Controller/GatewayController.php` | `#[ExAppRequired]`, nur `fopen('r')` | VERIFIED | Genau eine `fopen`-Stelle im Repo, Modus `'r'`, 404/422/500-Pfade |
| `backend/src/findling/nc/client.py` | Einzige nc_py_api-Grenze, `fetch_file_stream` via Stream | VERIFIED | `download2stream` statt `ocs()`, `_CountingSink`, `None` bei 404/998 |
| `backend/src/findling/api/search.py` | `POST /search` mit Container-Beweis | VERIFIED (Stub bewusst dokumentiert) | Fester Kanarien-Treffer laut Plan, echte Suche folgt Phase 2 |
| `backend/Dockerfile` | Multi-Stage, Debian-slim, digest-gepinnt | VERIFIED | `python:3.13-slim-trixie`, `supervisord` fuehrt `app`+`frpc` |
| `php/appinfo/info.xml` | Store-Metadaten Companion | VERIFIED | id `findling`, NC 32-35, PHP >=8.2 |
| `backend/appinfo/info.xml` | Store-Metadaten ExApp inkl. docker-install | VERIFIED | `docker-install`, eine Route `search` (USER), `environment-variables` |
| `testdata/corpus/*` (7 Dateien) | Referenzkorpus fuer Gate B | VERIFIED | 7 Dateien vorhanden, reproduzierbar per `scripts/dev/build_corpus.py` |
| `.github/workflows/*.yml` (5 Stueck) | integration, docker, php, python | VERIFIED | 4 Dateien vorhanden (`docker.yml`, `integration.yml`, `php.yml`, `python.yml`); `integration.yml` enthaelt zwei Jobs (`walking-skeleton`, `readonly-gate`), zaehlt effektiv als die geforderten 5 Gate-Bereiche |
| CSR-Vorgaenge (2 PRs gegen nextcloud/app-certificate-requests) | Eingereicht | NOT SUBMITTED | Branches + PR-Texte fertig, aber keine offene PR unter `street1983nk` fuer `findling`/`findling_backend` gefunden |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| Nextcloud-Suchleiste | `php/lib/Search/Provider.php` | `registerSearchProvider` in `Application::register()` | WIRED | `grep` bestaetigt genau eine Registrierungszeile; CI-Providerliste zeigt `findling` |
| `Provider::search()` | `ExAppService::search()` | Konstruktor-Injektion | WIRED | Direkter Methodenaufruf, Rueckgabe wird in `SearchResultEntry` gemappt |
| `ExAppService::search()` | ExApp-Container `POST /search` | `OCA\AppAPI\PublicFunctions::exAppRequest()` | WIRED, live verifiziert | CI-Suchschritt liefert echten Container-Treffer mit Hostname/Zeitstempel/Nutzer-ID |
| ExApp `fetch_file_stream` | PHP `GatewayController::getFileContents` | `download2stream` gegen `GATEWAY_PATH` | WIRED, live verifiziert | CI liest 7 Dateien vollstaendig als Berechtigter, 0 Bytes als Unberechtigter |
| `integration.yml` `readonly-gate` | Referenzkorpus | `sha256sum`/`stat` vor/nach Leselauf | WIRED, live verifiziert | Tamper-Probe-Lauf zeigt roten Ausschlag exakt im `readonly-gate`-Job |
| `docker.yml` | ghcr.io Multi-Arch-Manifest | `imagetools create` im Merge-Job | WIRED, live verifiziert | `imagetools inspect` zeigt beide Plattformen im selben Index |

### Behavioral Spot-Checks (live durchgefuehrt, keine Simulation)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| CI-Laeufe auf dem aktuellen HEAD sind gruen | `gh run list --repo street1983nk/nextcloud-search --limit 15` | `Integration`, `Multi-arch image`, `Python gates` fuer headSha `83716c0` alle `success` | PASS |
| Tamper-Probe zeigt gezielten roten Ausschlag | `gh run view 31883309703 --json jobs` | `walking-skeleton: success`, `readonly-gate: failure` | PASS |
| Multi-Arch-Manifest enthaelt beide Plattformen | `docker buildx imagetools inspect ghcr.io/street1983nk/findling_backend:dev` | `linux/amd64` + `linux/arm64` im Index | PASS |
| Keine offene CSR-PR fuer findling/findling_backend | `gh pr list --repo nextcloud/app-certificate-requests --author street1983nk --state open` | nur `#1160` (mcp_connector) | FAIL (erwartete Owner-Aktion steht aus) |
| Keine Debt-Marker in Phase-1-Code | grep auf TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER | 0 Treffer in php/, backend/src, backend/tests, .github/workflows | PASS |

### Requirements Coverage

| Requirement | Beschreibung | Status | Evidence |
|-------------|--------------|--------|----------|
| COMP-01 | Treffer in Unified Search via IProvider | SATISFIED | Provider.php, CI-Assertion auf Container-Marker+Nutzer-ID |
| COMP-02 | Content-Gateway: ExApp holt Inhalte per ExAppRequired-Endpunkt | SATISFIED | GatewayController + fetch_file_stream, Positiv- und Negativlauf live in CI |
| IDX-07 | Nur-Lesen-Invariante mit CI-Pruefsummen-Gate | SATISFIED | Gate A (statisch) + Gate B (dynamisch), Tamper-Probe live rot |
| PKG-01 | Multi-Arch-Image, Debian-slim | SATISFIED | Manifest bestaetigt linux/amd64+arm64 |
| PKG-02 | Beide App-IDs eingefroren, beide CSRs eingereicht | PARTIAL | ID-Freeze SATISFIED; CSR-Einreichung NOCH NICHT ERFOLGT (Owner-Schritt aussteht) |

### Anti-Patterns Found

Keine Blocker. Keine Debt-Marker (TBD/FIXME/XXX) in den phasenrelevanten Dateien gefunden. Bekannte, im Kontext ausdruecklich erlaubte Platzhalter (dokumentiert in 01-04-SUMMARY "Known Stubs"): fester Kanarien-Treffer in `api/search.py` (`fileId=0`, leere `highlights`), explizit als Phase-2-Arbeit vermerkt und durch CONTEXT.md gedeckt ("KEINE Indexierung, KEINE echte Suche" in Phase 1). Dies ist kein Anti-Pattern, sondern eine geplante Scope-Grenze.

### Human Verification Required

Keine neue Handlung noetig. Die Owner-Sichtprobe (Web-UI-Treffer sehen, Gegenprobe nach Unregister) wurde laut 01-06-SUMMARY am 15.08.2026 bereits durchgefuehrt und bestanden; hier nur nachrichtlich aufgefuehrt.

### Gaps Summary

Vier von fuenf Erfolgskriterien sind vollstaendig und mit Live-Beweisen (nicht nur mit SUMMARY-Behauptungen) verifiziert: der Container-Treffer erscheint nachweislich in der Unified Search, das Content-Gateway liest rechtegeprueft und verweigert korrekt, das Multi-Arch-Image baut und liefert ein echtes Zwei-Plattformen-Manifest, und das Nur-Lesen-Gate zeigt in einem echten Tamper-Probe-Lauf den gewollten roten Ausschlag ohne den funktionalen Pfad zu beeintraechtigen.

Das fuenfte Kriterium (App-IDs + CSR-Einreichung) ist zur Haelfte erfuellt: der App-ID-Freeze ist unwiderruflich und live belegt. Die CSR-Einreichung selbst ist jedoch ausdruecklich ein Owner-Schritt (`checkpoint:human-action`, kein autonomer Executor-Schritt) und laut `gh pr list` bislang nicht erfolgt: es existiert keine offene Pull Request fuer `findling` oder `findling_backend` gegen `nextcloud/app-certificate-requests`. Alles automatisierbare ist vorbereitet (Schluessel, CSRs, Fork-Branches, PR-Texte, fertige Kommandos). Da das Roadmap-Kriterium selbst die Einreichung "vor dem ersten Bau-Commit der Folgephase" verlangt statt vor Abschluss dieser Phase, wird dies nicht als Phase-1-Fehlschlag gefuehrt, sondern als offene Gate-Bedingung, die vor dem Start von Phase 2 zu schliessen ist.

**Empfehlung:** Vor dem ersten Plan von Phase 2 pruefen, ob der Owner die zwei vorbereiteten `gh pr create`-Kommandos aus `docs/store-identity.md` ausgefuehrt hat. Falls ja: `docs/store-identity.md`-Tabelle mit PR-Links aktualisieren, `REQUIREMENTS.md` PKG-02 auf erfuellt setzen. Falls nein: die CSR-Lead-Time (Median 3-4 Tage) parallel zur Phase-2-Planung laufen lassen, da Phase 2 selbst nicht CSR-abhaengig ist.

---

*Verified: 2026-08-15*
*Verifier: Claude (gsd-verifier)*
