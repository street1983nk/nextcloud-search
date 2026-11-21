# Phase 44: PHP-Sicherheits-Gates - Pattern Map

**Mapped:** 21.11.2026
**Files analyzed:** 22 (neu und geändert, Workflow-Sammeländerung als ein Eintrag)
**Analogs found:** 16 / 22

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `.github/workflows/php.yml` (neue Jobs `psalm-taint` Matrix 33/34/35, `php-cs`; paths) | config/CI | batch | gleiche Datei: Jobs `composer-hygiene` (Z. 227-270), `phpunit` (Z. 272-460) | exact |
| `.github/workflows/workflow-lint.yml` (neu, zizmor + actionlint) | config/CI | batch | `.github/workflows/php.yml` Kopf (Z. 1-86) + `composer-hygiene` | role-match |
| `scripts/ci/psalm_taint_gate.sh` | utility/Gate-Skript | batch, file-I/O (SARIF) | `scripts/ci/update_in_process_proof.sh` (Positivkontrolle im Skript) + INNER-Block `scripts/dev/phpunit_docker.sh` Z. 148-168 (`set +e`, rc, Zählung) | role-match |
| `scripts/ci/php_cs_gate.sh` | utility/Gate-Skript | batch | wie oben | role-match |
| `scripts/ci/workflow_lint_gate.sh` | utility/Gate-Skript | batch | wie oben | role-match |
| `scripts/dev/php_gates_docker.sh` | utility/lokales Rezept | batch | `scripts/dev/phpunit_docker.sh` | exact |
| `backend/tests/test_php_static_gates.py` | test/Strukturgate | transform (YAML/Text lesen) | `backend/tests/test_php_supply_chain_gates.py` | exact |
| `backend/tests/test_workflow_tag_triggers.py` (`PATHS_BEFORE`) | test | transform | gleiche Datei Z. 45-84 | exact |
| `.github/dependabot.yml` (cooldown, Einträge `/php/tools/*`) | config | - | gleiche Datei Z. 133-154 (composer `/php`) | exact |
| `.github/workflows/*.yml` + `.github/actions/setup-test-nc/action.yml` (49 x `persist-credentials: false`) | config/CI | - | `php.yml` Z. 240-245 | exact |
| `.github/workflows/python.yml` (`enable-cache: false` Z. 130, 250; ggf. paths `.github/workflows/**`) | config/CI | - | gleiche Datei Z. 124-131 | exact |
| `php/tools/psalm/composer.json` + `.lock` | config | - | `php/composer.json` | role-match |
| `php/tools/php-cs-fixer/composer.json` + `.lock` | config | - | `php/composer.json` | role-match |
| `php/psalm.xml` | config | - | keins (RESEARCH Pattern 1) | none |
| `php/.php-cs-fixer.dist.php` | config | - | keins (RESEARCH Code Examples) | none |
| `php/tools/psalm/AppFrameworkTainter.php` | utility/Plugin | - | Kopie nextcloud/server `build/psalm/AppFrameworkTainter.php` | upstream |
| `php/tools/psalm/stubs/app_api.phpstub` | config/Stub | - | keins (RESEARCH Pattern 2) | none |
| `php/tools/psalm/taint-probe/ProbeController.php` | test-Fixture | request-response | keins im Repo (RESEARCH Pattern 4) | none |
| `.github/fixtures/workflow-lint-probe.yml` | test-Fixture | - | keins | none |
| `php/lib/**`, `php/templates/**`, `php/tests/**` (einmaliger cs-fix) | Quelltext | - | Werkzeugausgabe, abgesichert durch `phpunit_docker.sh` | n/a |
| `docs/testing.md` (Abschnitt Phase 44, lokales Rezept) | docs | - | gleiche Datei, Abschnitte "The gates of phase 13, and the boundary of each one" (Z. 231) und Z. 42/492 | exact |
| `backend/tests/test_php_supply_chain_gates.py` (nur falls nötig) | test | transform | gleiche Datei | exact |

## Pattern Assignments

### `.github/workflows/php.yml`: Jobs `psalm-taint` und `php-cs`

**Analog:** gleiche Datei, Job `composer-hygiene` (Z. 232-270).

Job-Gerüst (Z. 232-252), so übernehmen; PHP für Psalm auf `'8.3'` (Pitfall 4), für cs auf `'8.2'`; dieselbe setup-php-SHA (Regel 5 von `test_workflow_pins.py`):
```yaml
  composer-hygiene:
    name: composer validate and audit
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - name: Check out the repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          # Nothing in this job pushes or calls the API, so the token has no
          # business in the working tree.
          persist-credentials: false

      - name: Set up PHP
        uses: shivammathur/setup-php@eb7c497e18156a6bbabfef1d3a82760b9eda3962 # 2.40.0
        with:
          php-version: '8.2'
          coverage: none
          tools: composer:v2
```
Install-Schritt nach `phpunit` Z. 360-366 (`composer install --no-interaction --no-progress --no-scripts`, `working-directory`), dann je Matrix-Bein `composer require --dev "nextcloud/ocp:${OCP_VERSION}" ... -W` in `php/tools/psalm`, dann `composer dump-autoload --no-scripts` in `php`, dann `run: bash scripts/ci/psalm_taint_gate.sh` (Muster Z. 494-495: Logik im Skript, nicht inline).

Kommentarstil: englische Kommentarblöcke über jedem Job/Schritt mit Begründung und gemessener Laufzeit für `timeout-minutes` (Z. 90-94, 235-238). Jeder Job braucht `timeout-minutes` (Psalm ca. 27 s je Bein, also 10 bis 15).

Lokal lesbare Schlüssel: Matrix-Tags/Image-Digests als eine Zeile je Schlüssel unter `env:` bzw. `strategy.matrix`, weil das lokale Rezept sie per `sed` liest (siehe `phpunit` Z. 282-286: "so both keys have to stay below in exactly this spelling, one per line").

paths-Erweiterung (Z. 26-42, push und pull_request identisch) um die neuen Skripte und `php/tools/**` liegt schon unter `php/**`; Kommentar-Präzedenz Z. 8-15.

---

### `.github/workflows/workflow-lint.yml` (neu)

**Analog:** `php.yml` Z. 16-64 (Trigger, Rechte, Concurrency).

```yaml
on:
  push:
    branches:
      - '**'
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'
    paths:
      - '.github/**'
      ...
  pull_request:
    paths: ...
  schedule:
    - cron: '50 5 * * 1'   # eigene Minute wählen, Reihenfolge Z. 43-50 beachten

permissions:
  contents: read

concurrency:
  group: php-${{ github.event_name }}-${{ github.ref }}
  cancel-in-progress: true
```
Pflichten aus bestehenden Gates: mindestens eine `uses:`-Zeile (`test_workflow_pins.py` `test_every_file_carries_at_least_one_uses_line`, Z. 261-279), `timeout-minutes` je Job (Regel 4, Regex `^ {4}timeout-minutes:` Z. 81, also Jobs mit 2 Leerzeichen, Schlüssel mit 4), Tag-Filter exakt `v[0-9]+.[0-9]+.[0-9]+` (`test_workflow_tag_triggers.py` Z. 161-165), keine Kontexte außer github/secrets/inputs/vars in Workflow-`env` (`test_workflow_contexts.py`). Nicht in `security.yml` (läuft nur auf main, Z. 11-15).

---

### `scripts/ci/psalm_taint_gate.sh`, `php_cs_gate.sh`, `workflow_lint_gate.sh`

**Analog 1:** `scripts/ci/update_in_process_proof.sh` (Kopfkommentar mit Usage/Environment, Positivkontrolle im selben Skript).

Kopfmuster (Z. 1-41, gekürzt):
```bash
#!/usr/bin/env bash
# ...
#   control    ... This MUST fail with "Undefined constant". It is the positive
#              control of the harness: a proof that cannot see the bug of
#              1.6.3 proves nothing about the candidate.
#   candidate  ... This MUST pass ...
#
# Usage:
#
#     scripts/ci/update_in_process_proof.sh
#
# Environment:
#
#     FROM_TAGS   releases the candidate is updated from (default "v1.6.2 v1.6.3")
```
Kontrollprüfung (Z. 133-140): erwartetes Rot UND erwartete Meldung, sonst Skript rot:
```bash
control_out=$(run_update "${PREFIX}-control" "$(release_archive "${CONTROL_TO}")" 2>&1)
control_rc=$?
printf '%s\n' "${control_out}"
if [ "${control_rc}" -eq 0 ] || ! printf '%s\n' "${control_out}" | grep -q "UPDATE-PROOF failed .*${CONTROL_MESSAGE}"; then
```
**Analog 2:** Exit-Code-Fang `scripts/dev/phpunit_docker.sh` Z. 150-168:
```bash
set +e
php vendor/bin/phpunit --no-progress --log-junit /srv/server/findling-junit.xml "$@"
rc=$?
set -e
```
Zählerlogik und Absturzschutz direkt aus RESEARCH Pattern 3 (jq über SARIF, Exit 0/2 zulassen, fehlende SARIF rot, "2 aber 0 Treffer" rot). Positivkontrollen aus RESEARCH Pattern 4 (Probe nach `lib/TaintProbe/`, nicht `lib/Controller/`; cs-Probe `lib/CsProbe.php` mit `--path-mode=intersection`; zizmor-Probe Exit >= 13, actionlint Exit 1). Probedateien per `trap` wieder entfernen.

Hinweis: `test_workflow_size.py` Z. 39 (`test_the_moved_steps_call_their_script_and_the_script_exists`) prüft ausgelagerte Schritte gegen vorhandene Skripte; vor Abschluss lesen, ob neue Aufrufe dort eingetragen werden müssen.

---

### `scripts/dev/php_gates_docker.sh`

**Analog:** `scripts/dev/phpunit_docker.sh` (exakt übernehmen).

Pfade und Mount-Konvertierung (Z. 36-56):
```bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)
PHP_WORKFLOW="${REPO_ROOT}/.github/workflows/php.yml"

to_mount_path() {
	if command -v cygpath >/dev/null 2>&1; then
		cygpath -m "$1"
	else
		printf '%s\n' "$1"
	fi
}
```
Werte aus dem Workflow lesen statt kopieren (Z. 58-70):
```bash
read_workflow_key() {
	sed -n -E "/^[[:space:]]+$1:/{s/^[[:space:]]+$1:[[:space:]]+([^[:space:]#]+).*/\\1/p;q}" "${PHP_WORKFLOW}"
}
SERVER_VERSION=$(read_workflow_key SERVER_VERSION)
if [ -z "${SERVER_VERSION}" ] ...; then echo "phpunit_docker: could not read ..." >&2; exit 1; fi
```
Docker-Check (Z. 72-75), Spiegel aus Repo frisch je Lauf mit `--rm` und `:ro`-Mount (Z. 110-121); für dieses Rezept Spiegel aus `git ls-files php` mit CR-Entfernung (Pitfall 6). Aufrufe mit `MSYS_NO_PATHCONV=1 docker run --rm` (Z. 133-135), kein Port, seriell. Lock-Stempel für `composer install` (Z. 123-137) für `php/tools/*` wiederverwenden. Meldungen mit Präfix `php_gates_docker:`.

---

### `backend/tests/test_php_static_gates.py`

**Analog:** `backend/tests/test_php_supply_chain_gates.py` (exakt).

Aufbau: Modul-Docstring mit nummerierten Regeln und Abschnitt `**The limit.**` (Z. 1-30), Konstanten, reine `scan_*(text) -> list[str]`-Funktionen, je ein Test am echten Baum, dann gestellte Proben pro Regel.

Imports und Helfer (Z. 32-53):
```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PHP_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "php.yml"
DEFUSERS = ("|| true", "||true")


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _defused(holder: dict[str, Any]) -> bool:
    return holder.get("continue-on-error") is True
```
YAML-Falle `on` (Z. 62-63): `triggers = _mapping(workflow.get(True, workflow.get("on")))`.
Job/Schritt-Prüfung inkl. Timeout (Z. 75-94):
```python
    for job_name, raw_job in jobs.items():
        job = _mapping(raw_job)
        steps = job.get("steps")
        for raw_step in steps if isinstance(steps, list) else []:
            step = _mapping(raw_step)
            run = step.get("run")
            ...
                if any(defuser in run for defuser in DEFUSERS) or _defused(step):
                    findings.append(f"the step running '{command}' in job {job_name} is defused")
        ...
            timeout = job.get("timeout-minutes")
            if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
                findings.append(f"job {job_name} has no timeout-minutes")
```
Probenmuster (Z. 144-231): `_CLEAN_WORKFLOW`-String, `test_a_clean_workflow_is_clean`, dann je Regel `source = _CLEAN_WORKFLOW.replace(...)` und genaue Erwartung `== ["..."]` bzw. `len(findings) == 1`. Zusätzliche Defuser für diese Phase: `--no-exit-codes`, `--format sarif`/`--format=sarif`, `-ignore` (actionlint), `issueHandlers`/`suppress` für Tainted*, Datei `psalm-baseline.xml`. Ergänzend aus `test_php_route_gate_presence.py` (Z. 1-62): Konstanten für Dateipfade und Schrittnamen (`STEP_NAME = "..."`), Floors als `MIN_*`.

---

### `backend/tests/test_workflow_tag_triggers.py`

**Analog:** gleiche Datei Z. 63-84. Neue Pfade mit Begründungskommentar eintragen, wie:
```python
    "php.yml": [
        ...
        # Added with the job "Store update in one process (issue 51)": the two
        # files are that job, so a change to either has to run it.
        "scripts/ci/update_in_process_proof.sh",
        "scripts/ci/update_in_process_driver.php",
    ],
```
Liste muss exakt gleich den `paths` im Workflow sein (Z. 174 `assert block.get("paths") == PATHS_BEFORE[name]`). Neuer `workflow-lint.yml` nur aufnehmen, wenn er paths hat; sonst greifen die allgemeinen Regeln Z. 152-165.

---

### `.github/dependabot.yml`

**Analog:** Eintrag composer `/php` Z. 133-154 (Zeitplan Montag 05:00 Europe/Berlin, Gruppe minor/patch, `ignore` mit `version-update:semver-major`). Für `/php/tools/psalm` analog `ignore` für `vimeo/psalm`-Majors (Pitfall 3). `cooldown: default-days: 14` an alle Einträge (Open Question 2).

**Achtung Kopplung:** `test_php_supply_chain_gates.py` `scan_dependabot` (Z. 104-128) nimmt `composer[0]`, also den ERSTEN composer-Eintrag, und verlangt dort `/php` und die phpunit-Regel. Neue Tool-Einträge daher NACH dem `/php`-Eintrag anordnen (oder den Test bewusst anpassen).

---

### `persist-credentials: false` an allen Checkouts

**Analog:** `php.yml` Z. 240-245 (siehe oben). In `deploy-harp.yml` nur die zwei Zeilen ohne Kommentar (Pitfall 8, `test_workflow_size.py` `CAP_BYTES = 500 * 1024`, Z. 19). Checkouts mit vorhandenem `with:` (z. B. `php.yml` Z. 322-331) den Schlüssel in den bestehenden Block setzen.

### `.github/workflows/python.yml`

Z. 124-131 (und Z. 247-250):
```yaml
      - name: Install uv
        uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
        with:
          version: '0.11.7'
          enable-cache: true          # -> false (cache-poisoning, Owner-Checkpoint)
          cache-dependency-glob: backend/uv.lock
```
Falls `.github/workflows/**` in die paths kommt (Pitfall 11): `PATHS_BEFORE["python.yml"]` gleichzeitig nachziehen, Präzedenz-Kommentar Z. 79-82 ("Widened ... by plan 42-10").

---

### `php/tools/psalm/composer.json`, `php/tools/php-cs-fixer/composer.json`

**Analog:** `php/composer.json`. Übernehmen: Tabs, `"license": "AGPL-3.0-or-later"`, `_comment`-Array mit Begründung für exakte Pins und Owner-Freigabe der Pakete (wie Eintrag 4 dort), exakte Versionen in `require-dev`, `config` mit `sort-packages: true`; zusätzlich `config.platform.php` (8.3.16 bzw. 8.2.27). Kein `autoload` (Tool-Projekte), Lockfiles committen. `vendor/` ist bereits per `.gitignore` (Zeile `vendor/` unter `# PHP`) für alle Unterordner ausgeschlossen. Store-Archiv kopiert nur `appinfo lib templates js css img l10n` (`scripts/release/store-archive.sh` Z. 76), Tools reisen also nicht mit.

Audit: zusätzliche Schritte im Job `composer-hygiene` mit `working-directory: php/tools/psalm` bzw. `php/tools/php-cs-fixer` (Muster Z. 259-270). Der Strukturtest liest nur `working-directory: php`, neue Schritte stören ihn nicht.

---

### `docs/testing.md`

**Analog:** gleiche Datei, Abschnitte "The gates of phase 13, and the boundary of each one" (Z. 231) und Rezept-Block Z. 492-493 (`scripts/dev/phpunit_docker.sh`). Neuer Abschnitt im selben Stil: je Gate was es prüft, Positivkontrolle, Grenze (Templates für Taint blind, Pitfall 5; zizmor `--offline`, Pitfall 13), lokaler Aufruf. Bestehende Doku ist englisch; Sprachwahl laut D-12 mit dem Planner abstimmen (deutsche Prosa verlangt).

## Shared Patterns

### Action-Pins (alle Workflow-Änderungen)
**Quelle:** `php.yml` Z. 99, 102; Regeln in `backend/tests/test_workflow_pins.py` Docstring Z. 13-31.
```yaml
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
uses: shivammathur/setup-php@eb7c497e18156a6bbabfef1d3a82760b9eda3962 # 2.40.0
```
Eine SHA je Action im ganzen Repo, exakte Versionskommentare, `timeout-minutes` an jedem Job. Container-Images per Digest (`image:tag@sha256:...`), Werte aus RESEARCH Standard Stack.

### Keine Entschärfung
**Quelle:** `php.yml` Z. 227-231 ("nothing here is softened by continue-on-error or an '|| true'") und `DEFUSERS` im Strukturtest. Gilt für alle neuen Gate-Schritte und -Skripte.

### Positivkontrolle im selben Lauf
**Quelle:** `php.yml` Z. 368-386 (Schritt "Prove the bootstrap refuses a path with no server behind it"):
```bash
if NEXTCLOUD_SERVER_ROOT=/nonexistent-on-purpose \
   vendor/bin/phpunit --no-progress > probe.log 2>&1; then
  echo "the bootstrap accepted a path with no nextcloud/server in it"
  cat probe.log
  exit 1
fi
grep -q 'no nextcloud/server checkout at this path' probe.log
```
Erwartetes Rot UND erwartete Meldung prüfen, sonst ist das Gate blind.

### Gleiche Werte lokal und CI
**Quelle:** `phpunit_docker.sh` Z. 19-21 und `read_workflow_key` (Z. 61-63). Versionen, Tags und Digests stehen nur im Workflow; Skripte lesen sie.

### Selbsttests jedes Textgates
**Quelle:** `test_workflow_contexts.py` Z. 20-21 ("Like every textual gate of this repository the rule carries self tests on staged samples"), Ausführung wie `test_php_supply_chain_gates.py` Z. 142-272.

## No Analog Found

| Datei | Rolle | Grund |
|---|---|---|
| `php/psalm.xml` | config | erstes Psalm im Repo; RESEARCH Pattern 1 (heute getestet) |
| `php/.php-cs-fixer.dist.php` | config | erstes cs-Werkzeug; RESEARCH Code Examples |
| `php/tools/psalm/stubs/app_api.phpstub` | Stub | RESEARCH Pattern 2; Signatur gegen nextcloud/app_api prüfen (A2) |
| `php/tools/psalm/AppFrameworkTainter.php` | Plugin | Kopie aus nextcloud/server, MIT-SPDX-Kopf und Quell-SHA im Kopf |
| `php/tools/psalm/taint-probe/ProbeController.php` | Fixture | RESEARCH Pattern 4; liegt außerhalb `lib/` und `tests/` (Autoload und RouteSecurity) |
| `.github/fixtures/workflow-lint-probe.yml` | Fixture | RESEARCH Pattern 4; liegt außerhalb `.github/workflows` und `.github/actions`, wird daher weder von GitHub noch von `test_workflow_pins.py` (scannt nur WORKFLOWS/ACTIONS, Z. 62-63) erfasst |

## Metadata

**Analog search scope:** `.github/workflows/`, `.github/dependabot.yml`, `scripts/ci/`, `scripts/dev/`, `backend/tests/test_php_*`, `backend/tests/test_workflow_*`, `php/composer.json`, `.gitignore`, `docs/testing.md`, `scripts/release/store-archive.sh`
**Files scanned:** 14
**Pattern extraction date:** 21.11.2026
