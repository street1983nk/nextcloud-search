---
phase: 01-integrationsbeweis
plan: 02
subsystem: infra
tags: [uv, ruff, pyright, vulture, pytest, github-actions, ast, nextcloud, ci, supply-chain]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Eingefrorene App-IDs findling und findling_backend, Mono-Repo-Geruest mit backend/ und .github/workflows/"
provides:
  - "uv-Paketprojekt backend/ mit exakten Pins und committetem uv.lock"
  - "Fuenf Python-Qualitaetsgates lokal gruen und als SHA-gepinnter Workflow python.yml"
  - "Gate A: statischer AST-Test der drei Nur-Lesen-Invarianten mit eigenem Negativbeweis"
  - "integration.yml: Walking-Skeleton-Job mit echter Nextcloud stable34 und Kanarienprobe auf /ocs/v2.php/search/providers"
  - "Rote Messlatte fuer Phase 1, aufgehaengt bevor der erste Fachcode existiert"
affects: [01-03, 01-04, 01-05, 01-06, 01-07, 01-08, phase-02-indexierung, docker, csr]

# Tech tracking
tech-stack:
  added:
    - "nc-py-api[app]==0.30.3"
    - "fastapi==0.141.1"
    - "httpx==0.28.1"
    - "ruff==0.16.3"
    - "pyright==1.1.411"
    - "vulture==2.16"
    - "pytest==9.1.1"
    - "pytest-asyncio==1.4.0"
  patterns:
    - "Alle GitHub-Actions ausschliesslich per Commit-SHA referenziert, nie per Tag"
    - "Sicherheitsuntergrenzen ueber uv constraint-dependencies statt ueber direkte Pins"
    - "Nur-Lesen-Invariante als AST-Test mit Selbsttestgruppe, damit das Gate auf leerem Paket nicht vakuum-gruen ist"
    - "Pfadgefilterte Workflows im Mono-Repo (backend/** gegen php/**)"

key-files:
  created:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/README.md
    - backend/src/findling/__init__.py
    - backend/tests/test_readonly_gate.py
    - .github/workflows/python.yml
    - .github/workflows/integration.yml
  modified: []

key-decisions:
  - "starlette nicht direkt gepinnt, sondern als uv constraint-dependency starlette>=1.0.1, damit der CVE-2026-48710-Boden gilt, ohne die Abhaengigkeitskante von nc-py-api zu uebernehmen"
  - "setup-uv in CI auf uv 0.11.7 festgelegt, also genau die Version, die backend/uv.lock erzeugt hat, damit --frozen lokal und in CI dieselbe Aufloesung bedeutet"
  - "Invariante 2 (verbotene Bezeichner) gilt wie im Bauplan nur fuer nc/client.py; Invariante 3 gilt paketweit, aber nur fuer Nextcloud-Empfaenger (nc, _session, adapter, ocs, session), damit spaetere lokale Aufrufe wie index_writer.delete keine Falschmeldung erzeugen"
  - "pytest laeuft mit filterwarnings error::DeprecationWarning und asyncio_default_fixture_loop_scope function, damit ein synchroner enabled_handler (Pitfall 7) sofort auffaellt"
  - "TDD-Zyklus in einer Datei: RED mit scan_source-Stub, GREEN mit Implementierung; REFACTOR entfiel, weil die Implementierung ohne Nacharbeit alle Gates bestand"

patterns-established:
  - "Gate A: jede kuenftige Erweiterung der Verbotsliste erfolgt in FORBIDDEN_IDENTIFIERS, die Allowlist OCS_WRITE_ALLOWLIST bleibt leer bis ein Schreibpfad begruendet ist"
  - "Kanarienprobe vor Fachcode: die Erfolgsmessung der Phase haengt als roter CI-Lauf, statt hinterher behauptet zu werden"
  - "Jede Action-Referenz traegt den 40-stelligen Commit-SHA plus Versionskommentar"

requirements-completed: [IDX-07, COMP-01]

# Metrics
duration: 11 min
completed: 2026-08-15
---

# Phase 1 Plan 02: Qualitaetsgates und rote Messlatte Summary

**uv-Backend mit fuenf gruenen Gates, ein AST-basiertes Nur-Lesen-Gate, das seinen eigenen Bruch nachweislich meldet, und ein Integrations-Workflow, der eine echte Nextcloud stable34 hochzieht und den fehlenden Suchanbieter anprangert.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-08-15T10:43:00Z
- **Completed:** 2026-08-15T10:54:00Z
- **Tasks:** 3 (Task 2 als TDD-Zyklus mit zwei Commits)
- **Files created:** 7

## Accomplishments

- `backend/` ist ein uv-Paketprojekt mit exakten Runtime-Pins (`nc-py-api[app]==0.30.3`, `fastapi==0.141.1`, `httpx==0.28.1`), committetem `uv.lock` und einer Constraint, die `starlette` nicht unter den CVE-2026-48710-Boden fallen laesst.
- Alle fuenf Gates laufen lokal gruen: `ruff check`, `ruff format --check`, `pyright` (basic), `vulture` (min-confidence 80), `pytest`. Derselbe Fuenfschritt steht in `.github/workflows/python.yml`, pfadgefiltert auf `backend/**`.
- Gate A (`backend/tests/test_readonly_gate.py`, 209 Zeilen) prueft die drei Invarianten aus IDX-07 per `ast.parse` und beweist sich selbst an vier synthetischen Verstossklassen, bevor es das echte Paket scannt.
- Die Manipulationsprobe ist real durchgefuehrt: eine Datei `src/findling/_tmp_probe.py` mit `import nc_py_api` dreht die Suite auf Exit 1, nach dem Loeschen wieder auf Exit 0.
- `.github/workflows/integration.yml` installiert Nextcloud stable34 aus dem Quellcheckout auf SQLite, aktiviert `app_api` und `findling` und fragt anschliessend `/ocs/v2.php/search/providers` per `jq` ab. Der Job ist heute rot, weil `php/` noch leer ist, und genau das ist die Messlatte der Phase.

## Task Commits

1. **Task 1: uv-Projekt mit exakten Pins und allen fuenf Qualitaetsgates** - `b86515b` (chore)
2. **Task 2 RED: fehlschlagender Selbsttest des Nur-Lesen-Gates** - `64b48ce` (test)
3. **Task 2 GREEN: Implementierung von `scan_source`** - `cb5fe23` (feat)
4. **Task 3: rote Kanarienprobe gegen eine echte Nextcloud** - `fabcfa2` (ci)

## Files Created/Modified

- `backend/pyproject.toml` - uv-Projekt, exakte Pins, ruff-Vollregelsatz, pyright/vulture/pytest-Konfiguration
- `backend/uv.lock` - 43 aufgeloeste Pakete, Grundlage fuer `uv sync --frozen` in CI
- `backend/README.md` - Entwicklungsbefehle und Hinweis auf die Nur-Lesen-Invariante (wird von `pyproject.toml` als readme referenziert)
- `backend/src/findling/__init__.py` - Paketdocstring und `__version__ = "0.1.0"`, gekoppelt an die PHP-App
- `backend/tests/test_readonly_gate.py` - Gate A: `scan_source` plus sechs Tests (vier Negativfaelle, ein Positivfall, ein Paketscan)
- `.github/workflows/python.yml` - fuenf Gates, `ubuntu-24.04`, Actions per SHA gepinnt
- `.github/workflows/integration.yml` - Walking-Skeleton-Job mit Nextcloud stable34, PHP 8.2, Kanarienprobe und `if: failure()`-Logausgabe

## Decisions Made

- **starlette als Constraint statt als Pin.** Der Sicherheitsboden `>=1.0.1` gehoert zu nc-py-api; ein direkter Pin haette bei jedem nc-py-api-Update nachgezogen werden muessen. `[tool.uv] constraint-dependencies` haelt den Boden, ohne die Kante zu besitzen. Aufgeloest wurde `starlette==1.6.0`.
- **CI-uv auf 0.11.7 statt 0.12.5.** Die Lockdatei stammt von der lokal installierten 0.11.7. Gleichstand zwischen Locker und CI ist mehr wert als die neuere Nebenversion; ein Sprung auf 0.12.x ist ein eigener, bewusster Commit.
- **Reichweite der Invarianten.** Invariante 1 und 2 bleiben exakt am Bauplan (Import nur in `nc/client.py`, verbotene Bezeichner nur dort). Invariante 3 gilt paketweit, ist aber auf Nextcloud-Empfaenger eingegrenzt, damit spaetere Indexoperationen wie `index_writer.delete(...)` nicht faelschlich als Schreibzugriff auf Nutzerdaten gelten.
- **`pytest-asyncio` exakt gepinnt (1.4.0)**, obwohl der Plan hier keine Version nannte. Ein ungepinnter Dev-Baustein widerspricht der Supply-Chain-Linie der uebrigen acht Pakete.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `backend/README.md` und `backend/tests/` ergaenzt**
- **Found during:** Task 1
- **Issue:** `pyproject.toml` deklariert `readme = "README.md"`, die Datei existierte nicht; `uv run vulture src tests` bricht ab, wenn `tests/` fehlt. Beides haette den Build und ein Abnahmekriterium blockiert.
- **Fix:** Kurzes `backend/README.md` (Entwicklungsbefehle, Nur-Lesen-Hinweis, Lizenz) und `backend/tests/.gitkeep` angelegt.
- **Files modified:** backend/README.md, backend/tests/.gitkeep
- **Verification:** `uv sync --frozen` und `uv run vulture src tests --min-confidence 80` laufen sauber durch.
- **Committed in:** `b86515b`

**2. [Rule 1 - Bug] pyright-Fehler im Gate A behoben**
- **Found during:** Task 2 (GREEN)
- **Issue:** `node.lineno` wurde auf dem generischen `ast.AST` aus `ast.walk` gelesen; pyright meldete `reportAttributeAccessIssue`.
- **Fix:** Die Zeilennummer wird jetzt im jeweiligen `isinstance`-Zweig zusammen mit dem Bezeichner gebunden.
- **Files modified:** backend/tests/test_readonly_gate.py
- **Verification:** `uv run pyright` meldet 0 errors, alle sechs Tests bleiben gruen.
- **Committed in:** `cb5fe23`

**3. [Rule 3 - Blocking] Zwei Abnahmekriterien von Task 3 sind erst nach dem Orchestrator-Push pruefbar**
- **Found during:** Task 3
- **Issue:** Die Kriterien `gh workflow list fuehrt integration.yml`, `gh run list ... liefert failure` und `gh run view --log-failed zeigt keinen Fehler in maintenance:install` setzen einen Push voraus. Dieser Executor laeuft in einem Worktree und darf laut Auftrag nicht pushen (der Orchestrator pusht nach dem Wave-Merge).
- **Fix:** Alles lokal Pruefbare wurde geprueft: YAML parst sauber (`yaml.safe_load`, ein Job `walking-skeleton`, 12 Schritte), `grep -c 'search/providers'` = 1, alle vier `uses:`-Zeilen tragen einen 40-stelligen SHA, `maintenance:install` ist enthalten. Die Referenzen `nextcloud/server@stable34`, `nextcloud/app_api@stable34` und die drei Action-SHAs wurden live gegen die GitHub-API aufgeloest.
- **Files modified:** keine
- **Verification:** **Offen bis zum Orchestrator-Push.** Danach mit `gh run list --workflow=integration.yml --limit 1 --json conclusion -q '.[0].conclusion'` den Wert `failure` bestaetigen und im Log pruefen, dass der Abbruch bei `Enable findling` oder bei der Kanarienprobe liegt, nicht bei `maintenance:install` oder `composer run serve`.
- **Committed in:** `fabcfa2`

---

**Total deviations:** 3 auto-fixed (2 blockierend, 1 Bug)
**Impact on plan:** Kein Scope-Zuwachs. Abweichung 3 ist keine inhaltliche Aenderung, sondern eine Verifikation, die durch die Parallel-Ausfuehrung im Worktree zeitlich nach hinten rutscht.

## Issues Encountered

- Der RED-Commit brauchte einen Zwischenschritt: mit `scan_source` als Stub war `import ast` unbenutzt und `ruff` (F401) war rot. Der Import kam mit der Implementierung zurueck. Das ist die Normalform, wenn RED und GREEN in derselben Datei liegen.
- Ohne PHP-Toolchain auf diesem Rechner ist `integration.yml` nur statisch pruefbar; das war bereits in der RESEARCH.md unter "Environment Availability" so festgehalten.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers des Plans. Die drei mitigierten Eintraege sind umgesetzt:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-01-04 (Tampering, Nutzerdateien) | Gate A aktiv, Manipulationsprobe nachgewiesen |
| T-01-05 (Elevation of Privilege) | `set_user` steht in `FORBIDDEN_IDENTIFIERS` |
| T-01-SC (Supply Chain) | Exakte Pins plus `uv.lock`; alle vier Action-Referenzen per Commit-SHA |

## User Setup Required

None - keine externe Dienstkonfiguration noetig.

## Next Phase Readiness

- Bereit fuer 01-03 und die folgenden Plaene: jeder neue Python-Commit laeuft ab sofort durch fuenf Gates, und jeder kuenftige Schreibpfad bricht Gate A.
- Offener Punkt fuer den Orchestrator: nach dem Push den ersten `integration.yml`-Lauf ansehen und bestaetigen, dass er aus dem erwarteten Grund rot ist (fehlende PHP-App), nicht wegen eines Setup-Fehlers.
- Gate B (Pruefsummenlauf ueber `testdata/corpus/`) ist bewusst nicht Teil dieses Plans; IDX-07 ist damit statisch abgedeckt, der dynamische Teil folgt mit dem Content-Gateway.

## Self-Check: PASSED

- Alle sieben angelegten Dateien auf der Platte vorhanden (`ls -l` bestaetigt).
- Alle vier Commits im Log: `b86515b`, `64b48ce`, `cb5fe23`, `fabcfa2`.
- Alle Abnahmekriterien von Task 1 und Task 2 lokal ausgefuehrt und bestanden, inklusive Manipulationsprobe (Exit 0 / Exit 1 / Exit 0).
- Abnahmekriterien von Task 3: die drei dateibezogenen bestanden, die drei laufbezogenen als Deviation 3 dokumentiert und dem Orchestrator uebergeben.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md.

---
*Phase: 01-integrationsbeweis*
*Completed: 2026-08-15*
