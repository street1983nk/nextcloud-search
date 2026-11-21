---
phase: 44-php-sicherheits-gates
plan: 03
subsystem: ci-sicherheits-gates
tags: [psalm, taint-analyse, lokales-rezept, docker, rotlauf]
requires:
  - "44-02 (scripts/ci/psalm_taint_gate.sh, Job psalm-taint)"
  - "44-OWNER-DECISIONS.md E-09 (Host-jq per Shim), E-10 (Store-Listing umformulieren)"
provides:
  - "scripts/dev/php_gates_docker.sh mit Unterbefehlen psalm und all"
  - "docs/testing.md Abschnitt zu den lokalen Sicherheits-Gates"
affects: [44-04, 44-07]
tech-stack:
  added: []
  patterns: ["LF-Spiegel aus git ls-files außerhalb des Repos", "php-Shim mit identischem Mountpfad, jq auf dem Host", "OCP-Tags aus der Workflow-Matrix gelesen"]
key-files:
  created:
    - scripts/dev/php_gates_docker.sh
  modified:
    - docs/testing.md
    - docs/store-listing.md
    - .planning/phases/44-php-sicherheits-gates/44-OWNER-DECISIONS.md
    - .planning/phases/44-php-sicherheits-gates/deferred-items.md
decisions:
  - "E-09: jq läuft im lokalen Rezept auf dem Host, php im Container per Shim; keine Paketinstallation im Container"
  - "E-10: zwei Stellen im 1.6.5-Abschnitt von docs/store-listing.md umformuliert, Test unverändert"
metrics:
  duration: "ca. 45 min"
  completed: 2026-11-21
  tasks: 2
  files: 2
---

# Phase 44 Plan 03: Lokales Rezept Psalm-Taint-Gate Summary

scripts/dev/php_gates_docker.sh psalm fährt das CI-Skript psalm_taint_gate.sh auf einem LF-Spiegel außerhalb des Repos gegen alle drei OCP-Tags aus php.yml, php im gepinnten php:8.3-cli per Shim, jq auf dem Host; lokal grün und dreifach rot belegt.

## Vorab (Owner-Antworten 21.11.2026)

- E-09 "Host-jq per Shim" und E-10 "Umformulieren" in 44-OWNER-DECISIONS.md eingetragen.
- E-10 umgesetzt: docs/store-listing.md Z. 3338 ("Release-Läufe für den App Store") und Z. 3343 ("Quellpakete"), Test unverändert; test_store_metadata.py 150 passed. Commit **1d6236f2** `docs(store-listing): ...`. deferred-items.md: Eintrag als erledigt markiert.

## Task 1: Rezept

- Muster von phpunit_docker.sh (`set -euo pipefail`, SCRIPT_DIR/REPO_ROOT, `to_mount_path`, Docker-Check, Präfix `php_gates_docker:`); Usage `psalm|all`, sonst Exit 2.
- Cache-Verzeichnis `${TMPDIR:-/tmp}/findling-php-gates` (oder FINDLING_PHP_GATES_DIR): `tree/` je Tag frisch aus `git ls-files --cached --others --exclude-standard -- php scripts/ci/psalm_taint_gate.sh`, CR in Textdateien entfernt (grep -I), `composer-cache/` bleibt erhalten, `bin/php` ist der Shim.
- OCP-Tags per sed aus dem Abschnitt des Jobs psalm-taint (Abbruch bei weniger als drei); keine Tags im Skript.
- Je Tag: composer:2 (Digest 50ea4d33) install, require `nextcloud/ocp:<tag>` -W, dump-autoload in php; dann auf dem Host `bash scripts/ci/psalm_taint_gate.sh` im Spiegel mit Shim vorn im PATH und TMPDIR im Spiegel (SARIF schreibt php im Container, jq liest auf dem Host).
- Lauf `bash scripts/dev/php_gates_docker.sh psalm`: **Exit 0**, Laufzeit 9 min 52 s (überwiegend composer-Entpacken auf dem Windows-Mount):

| OCP | Ausgabe |
|-----|---------|
| v33.0.9 | taint findings: 0; psalm taint gate: 0 findings, probe found 3 |
| v34.0.6 | taint findings: 0; psalm taint gate: 0 findings, probe found 3 |
| v35.0.3 | taint findings: 0; psalm taint gate: 0 findings, probe found 3 |

Schlusszeile: "php_gates_docker: psalm taint gate green against 3 nextcloud/ocp tags".

- Kriterien: `grep -c "read_workflow_key\|php.yml"` 3; `grep -c -E "v3[345]\.0\.[0-9]+"` 0; `--rm` vorhanden; `--name`/` -p ` 0. shellcheck 0.11.0 (actionlint-Image) `--severity=style`: 0 Befunde.

## Task 2: Rotläufe, Gegenläufe, Commit

Rotläufe auf Kopien des v35.0.3-Spiegels im Scratchpad (eigener Shim mit Mount der Kopie), danach gelöscht:

| Fall | Änderung in der Kopie | Exit | Meldung |
|------|----------------------|------|---------|
| a | ProbeController.php zusätzlich nach php/lib/TaintProbe/ | 1 | "taint findings: 3" (TaintedHtml :38, TaintedTextWithQuotes :38, TaintedSql :45), "psalm taint gate: 3 taint finding(s); fix each one, or bring it to the owner, never suppress it silently" |
| b | Plugin-Pfad in psalm.xml auf tools/psalm/NoSuchTainter.php | 1 | Psalm: "Cannot find plugin file ...", "psalm taint gate: psalm crashed or refused its config (exit 1)" |
| c | Plugin-Zeile aus psalm.xml entfernt | 1 | "taint findings: 0", Probe nur TaintedSql, "psalm taint gate: the taint gate is blind: the probe gave 1 finding(s), expected at least 2" |

- `bash scripts/dev/phpunit_docker.sh`: rc 0, "OK (1222 tests, 7765 assertions)".
- pytest test_public_artifacts.py + test_measurement_scripts.py: grün (626 + 1, siehe Abweichung 2). Zusätzlich test_store_metadata, test_admin_ui_contract, test_backup_docs, test_lockstep_versions, test_exapp_call_instrumentation nach der Doku-Änderung: 1054 passed.
- `git ls-files php/lib | grep -c TaintProbe`: 0. Gedankenstriche: keine.
- Commit **8f5aca31** `ci(44-03): lokales Rezept für das Psalm-Taint-Gate`, Autor street1983nk <k.cherif@outlook.de>, kein Push.

## Deviations from Plan

**1. [E-09] Gate läuft auf dem Host, nicht als `php:8.3-cli bash ...`**
Der Plan nennt "php:8.3-cli `bash /w/scripts/ci/psalm_taint_gate.sh`". Das Image hat kein jq; nach Owner-Entscheid E-09 läuft das Gate-Skript auf dem Host und nur php im Container (Shim). Kein Schalter im Gate-Skript. Dokumentiert in docs/testing.md (mitcommittet in 8f5aca31, der Plan nannte nur das Skript).

**2. [Hinweis] Baumhash-Test lokal rot durch ungetrackte 44-04-Vorbereitung**
test_the_recipe_reproduces_the_tree_hash_of_the_php_half zählt den Arbeitsbaum; die schon angelegte php/.php-cs-fixer.dist.php (44-04) ergab 133 statt 132. Gegenprobe ohne diese Datei: 1 passed. Anpassung des Werts folgt in 44-04 mit dem Commit, der die Datei einführt.

**3. read_workflow_key nicht übernommen**
Das Rezept braucht keinen `KEY: value`-Wert, nur die Matrix-Liste; eine ungenutzte Funktion wäre toter Code. Der Tag-Leser `read_ocp_tags` folgt derselben Form (ein sed-Aufruf, keine Pipe) und verweist im Kommentar darauf. Das grep-Kriterium ist über "php.yml" erfüllt.

## Threat Flags

Keine. Nur `docker run --rm`, keine Namen, keine Ports, seriell (T-44-35); Probe nur in Kopien (T-44-36); Tags und Skript aus dem Repo (T-44-34).

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: scripts/dev/php_gates_docker.sh
- FOUND: 1d6236f2, 8f5aca31
