---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 02
subsystem: Logging / Lizenzpflicht / Release-Workflow
tags: [hart-06, rel-05, logging, corresponding-source, release-yml, gpl]
requires: [36-01]
provides:
  - "httpx/httpcore auf WARNING außer bei FINDLING_LOG_LEVEL=debug (nc/client.py quiet_client_loggers, Aufruf im Lifespan)"
  - "Korrespondierende Quelle für pillow-heif 1.8.1: x265 4.3, libheif 1.23.6, libde265 1.1.3, SHA-256 aus eigenem Download"
  - "Stempel RECIPE_READ_FOR_PILLOW_HEIF gegen backend/uv.lock, Versionsabgleich THIRD-PARTY.md gegen ARCHIVES"
  - "release.yml: Quellpakete plus git archive im selben gh release create, neun Dateien, per Dispatch geprobt"
affects: [36-12, 36-13, 36-15]
tech-stack:
  added: []
  patterns:
    - "Client-Loggernamen nur in nc/client.py (Gate A, test_gateway_client)"
    - "COMPANION_VERSION einmal gelesen, per GITHUB_ENV an Tag-Check und Quellarchiv"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-02-SUMMARY.md
  modified:
    - backend/src/findling/main.py
    - backend/src/findling/nc/client.py
    - backend/tests/test_main_lifespan.py
    - backend/tests/test_measurement_scripts.py
    - scripts/release/corresponding_source.py
    - THIRD-PARTY.md
    - backend/tests/test_corresponding_source.py
    - backend/tests/test_third_party_versions.py
    - docs/store-listing.md
    - .github/workflows/release.yml
    - docs/certificates.md
decisions:
  - "Logger-Hebung als quiet_client_loggers in nc/client.py statt inline in main.py, weil Gate A das Wort httpx nur dort erlaubt"
  - "x265-Quelle von GitHub Multicorewareinc/x265 (Host aus build_libs.py 1.8.1), nicht mehr bitbucket"
  - "Companion-Version in eigenem Schritt gelesen (COMPANION_VERSION), der Tag-Check nutzt dieselbe Variable: eine Leselogik"
  - "Rückfall bei Upstream-Ausfall nur von Hand über den Spiegel, kein automatischer Workflow-Zweig"
metrics:
  duration: "ca. 75 min Arbeitszeit (ohne Unterbrechung durch das Usage-Limit)"
  completed: 2026-10-20
  tasks: 3
  files: 11
requirements: [HART-06, REL-05]
---

# Phase 36 Plan 02: Client-Logs, korrespondierende Quelle 1.8.1 und Quellpakete im Release Summary

Im Standardbetrieb loggen httpx und httpcore nur noch ab WARNING, mit Debug kommen die Anfragezeilen zurück. Die korrespondierende Quelle passt jetzt zum ausgelieferten pillow-heif 1.8.1 (x265 4.3, libheif 1.23.6), und ein Stempeltest wird rot, wenn sich der Pin ohne Nachzug bewegt. release.yml legt die vier GPL/LGPL-Quellpakete und ein `git archive` des Baums im selben unveränderlichen `gh release create` ab. Die Probe per Dispatch ist grün und liefert neun Dateien.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | httpx/httpcore auf WARNING außer bei debug | c9c55300, Nachbesserung 03a45248 | main.py, nc/client.py, test_main_lifespan.py, test_measurement_scripts.py |
| 2 | Quellliste auf pillow-heif 1.8.1, Stempel | d67a7863 | corresponding_source.py, THIRD-PARTY.md, test_corresponding_source.py, test_third_party_versions.py, store-listing.md |
| 3 | Quellpakete in release.yml, Probe | f180d650 | release.yml, certificates.md |

## Belege

**Task 1 (RED vor GREEN):** Ohne Code ist `test_the_client_loggers_stand_on_warning_by_default` rot (`assert 10 == 30`, httpx effektiv DEBUG). Positivkontrolle (debug) und eigener Logger waren schon grün. Mit dem Code laufen alle drei grün. Baumhash-Ratsche: 5a348317 auf 2f73265b (c9c55300) und nach der Gate-A-Nachbesserung auf 92013822 (03a45248). Gerechnet jeweils mit 40b-baumhash.py und unabhängig mit find/sort/tr/sha256sum, beide Wege gleich.

**Task 2:**
- `libheif/build_libs.py` des sdist 1.8.1 (SHA-256 521ebffb..., gleich dem ARCHIVES-Eintrag) nennt `LIBX265_URL .../Multicorewareinc/x265/releases/download/4.3/x265_4.3.tar.gz`, libde265 v1.1.3 und libheif v1.23.6.
- In beiden Linux-Wheels (cp313, x86_64 und aarch64) ist `LICENSES_bundled.txt` byte-gleich. `pillow_heif.libs` enthält `libheif-*.so.1.23.6`, `libde265-*.so.0.2.3` und `libx265-*.so.217`, kompiliert ist der String `4.3+1-e9b8812`. Größe von libx265: 11,4 MB auf arm64, 22,9 MB auf amd64.
- SHA-256 aus eigenem Download: x265_4.3 `83c53e4c...b121`, libheif-1.23.6 `4484346d...3125`. Beide gegengeprüft am `digest` der GitHub-Release-Assets (gleich).
- Upstream wheels.yml am Tag v1.8.1 (Commit 0ed53791) ruft `libheif/build_libs.py` als `CIBW_BEFORE_ALL_LINUX`. THIRD-PARTY.md ist darauf nachgezogen.
- RED: Nach dem Testumbau sind 3 Tests rot (Versionen, Stempel fehlt). Nach der Skriptänderung sind der Tabellenabgleich und der neue Versionsabgleich gegen THIRD-PARTY.md rot. Nach dem THIRD-PARTY-Nachzug laufen 20/20 grün.
- Gegenprobe Stempel: `test_the_stamp_gate_fires_on_a_stale_stamp` setzt `RECIPE_READ_FOR_PILLOW_HEIF` auf "1.8.0" und erwartet den AssertionError. Der Test ist grün, das Gate feuert also.
- `fetch` in Scratch: vier Zeilen `ok (fetched)`, rc=0. `--verify-only`: vier Zeilen `ok`, rc=0. Auch unter Python 3.12 läuft es (Runner ubuntu-24.04).

**Task 3:**
- test_workflow_pins.py und test_workflow_tag_triggers.py sind unverändert grün (41 passed).
- Probe: Lauf 39439309752 (workflow_dispatch, create_release=false, Kopf 03a45248) ist success. Das Artefakt `store-release` enthält genau neun Dateien:
  - findling-1.4.2-source.tar.gz
  - findling.tar.gz, findling.tar.gz.sig
  - findling_backend.tar.gz, findling_backend.tar.gz.sig
  - source/libde265-1.1.3.tar.gz, source/libheif-1.23.6.tar.gz, source/pillow_heif-1.8.1.tar.gz, source/x265_4.3.tar.gz
- `--verify-only` lokal auf `source/`: vier Zeilen ok, rc=0. Das Quellarchiv hat 3168 Einträge, alle unter `findling-1.4.2/`, darunter `php/appinfo/info.xml` und `backend/src/findling/main.py`.
- Volle Suite lokal vor dem Push: 5927 passed, 264 skipped.
- CI-Block für den Push 03a45248, alle acht Läufe success: Python gates 39439252339, Integration 39439252430, Security scans 39439252517, OpenSSF Scorecard 39439252565, Multi-arch image 39439252464, PHP and store metadata gates 39439252828, Resilience 39439252687, HaRP deploy 39439252750.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Gate A durch Loggernamen in main.py verletzt**
- **Found during:** volle Suite vor dem Push (nach Task 3)
- **Issue:** `test_gateway_client.py::test_nc_py_api_is_named_in_the_client_module_only` erlaubt `httpx` nur in `nc/client.py`. Mein Task-1-Code nannte es in main.py.
- **Fix:** `CLIENT_LOGGERS` und `quiet_client_loggers(log_level)` liegen jetzt in nc/client.py, der Lifespan ruft die Funktion direkt hinter `basicConfig` auf. Der Kommentar in main.py nennt nur noch httpcore. Die Ratsche ist mit neuem Journalabsatz nachgezogen. Der Test bleibt unverändert.
- **Files modified:** backend/src/findling/main.py, backend/src/findling/nc/client.py, backend/tests/test_measurement_scripts.py
- **Commit:** 03a45248
- **Folge für das Akzeptanzkriterium:** `grep '"httpcore"' main.py` findet keinen String-Literal mehr. Die Hebung steht als Aufruf `quiet_client_loggers(log_level())` direkt hinter `basicConfig`, das Wort httpcore steht im Kommentar.

**2. [Rule 1 - Doku] docs/certificates.md nannte "four artifacts" für die Probe**
- Auf neun Dateien gezogen, mit Commit f180d650 (Datei nicht in files_modified).

**3. [Rule 3] Companion-Version für das Quellarchiv**
- Der Versionsschritt 184ff. läuft nur auf Tags, also gab es keine Variable, die ein Dispatch-Lauf übernehmen konnte. Ein neuer Schritt "Read the companion version" schreibt deshalb `COMPANION_VERSION` nach GITHUB_ENV. Der Tag-Check nutzt dieselbe Variable statt eines zweiten sed-Aufrufs, es bleibt also bei einer Leselogik.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flächen. T-36-05 bis T-36-07 sind wie geplant gemindert.

## Offen

- Spiegel `source-1.5-dev.3` bewusst nicht angelegt (Owner-Wort in 36-13).
- Requirements HART-06 und REL-05 reichen über weitere Pläne (36-12, 36-13, 36-15) und werden hier nicht abgehakt.

## Self-Check: PASSED
