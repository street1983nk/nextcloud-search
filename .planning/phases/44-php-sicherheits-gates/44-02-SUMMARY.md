---
phase: 44-php-sicherheits-gates
plan: 02
subsystem: ci-sicherheits-gates
tags: [psalm, taint-analyse, sarif, positivkontrolle, php-yml]
requires:
  - "44-OWNER-DECISIONS.md E-05, E-07 (mit Owner-Zusatz vom 21.11.2026)"
provides:
  - "Tool-Projekt php/tools/psalm (Psalm 6.20.10, ocp v35.0.3, gelockt und auditiert)"
  - "php/psalm.xml mit AppFrameworkTainter und AppAPI-Stub"
  - "scripts/ci/psalm_taint_gate.sh mit SARIF-Selbstzählung, Absturzschutz und Positivkontrolle"
  - "Job psalm-taint in php.yml, Matrix v33.0.9, v34.0.6, v35.0.3"
affects: [44-03, 44-06, 44-08, 44-09, 44-10]
tech-stack:
  added: ["vimeo/psalm 6.20.10 (nur CI/Dev)", "nextcloud/ocp v33.0.9/v34.0.6/v35.0.3 (nur CI/Dev)"]
  patterns: ["Gate zählt Befunde selbst aus SARIF", "Positivkontrolle in jedem Lauf", "Regelnamen über tool.driver.rules aufgelöst"]
key-files:
  created:
    - php/tools/psalm/composer.json
    - php/tools/psalm/composer.lock
    - php/tools/psalm/AppFrameworkTainter.php
    - php/tools/psalm/stubs/app_api.phpstub
    - php/tools/psalm/taint-probe/ProbeController.php
    - php/psalm.xml
    - scripts/ci/psalm_taint_gate.sh
  modified:
    - .github/workflows/php.yml
    - backend/tests/test_workflow_tag_triggers.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/44-php-sicherheits-gates/44-OWNER-DECISIONS.md
decisions:
  - "Psalm-SARIF trägt als ruleId die numerische Kurzkennung (245), den Namen (TaintedHtml) nur in tool.driver.rules; das Gate löst die Namen darüber auf"
  - "Erster Lauf gegen OCP 33/34/35: je 0 Befunde, kein unbekannter Befund, Checkpoint Task 2 entfällt"
metrics:
  duration: "ca. 85 min"
  completed: 2026-11-21
  tasks: 3
  files: 11
---

# Phase 44 Plan 02: Psalm-Taint-Gate Summary

Psalm 6.20.10 mit AppFrameworkTainter und AppAPI-Stub (SSRF-Senke an `$route`) als Matrix-Job psalm-taint gegen OCP v33.0.9, v34.0.6 und v35.0.3; das Gate-Skript zählt die SARIF-Treffer selbst, ist rot bei Befund, Absturz, fehlendem Bericht und Exit 2 ohne Treffer und verlangt in jedem Lauf TaintedHtml und TaintedSql von der Taint-Probe.

## Tasks

| Task | Name | Ergebnis | Commit |
|------|------|----------|--------|
| 1 | Tool-Projekt, psalm.xml, Plugin, Stub, Probe, erster Lauf | gelockt, auditiert, 0 Befunde je OCP-Tag | 4f51f090 |
| 2 | Bedingter Checkpoint unbekannte Befunde | kein unbekannter Befund, Checkpoint entfällt | - |
| 3 | Gate-Skript, Job psalm-taint, Tool-Audit, PATHS_BEFORE | Workflow-Gates grün, Skriptlauf v35.0.3 Exit 0 | 4f51f090 |

Ein Commit für den ganzen Plan, wie in der Zielsetzung vorgegeben.

## Task 1: Tool-Projekt und erster Lauf

- composer.lock per composer:2 (Digest 50ea4d33) erzeugt: vimeo/psalm 6.20.10, nextcloud/ocp v35.0.3, 31 Pakete. `composer audit --locked`: keine Advisories (Exit 0); `composer validate --strict --no-check-publish`: valid (Exit 0), auch mit schreibgeschütztem Mount (Plan-Verify). `git check-ignore -q php/tools/psalm/vendor` Exit 0 (Regel `vendor/` in .gitignore Z. 21).
- AppFrameworkTainter.php: unverändert aus nextcloud/server master, Commit 3a161f74fb6710eca56c0b250aadb81db9e9c625 (Blob 448922d2), MIT-SPDX-Kopf behalten, Quellkommentar darunter.
- Stub-Signatur (Annahme A2) geprüft gegen nextcloud/app_api `lib/PublicFunctions.php`, Standardzweig main, letzter Commit der Datei aeb217aa1b7d707e711920adc1c95a13b6954478: `exAppRequest` und `getExApp` identisch zur Server-Stub. php/lib nutzt nur `exAppRequest`.
- Erster Lauf im Spiegel (git ls-files php plus neue Dateien, CR entfernt), php:8.3-cli (Digest 9e2a4e9b), `--threads=1 --taint-analysis --report`:

| OCP | installiert | Psalm-Exit | SARIF-Treffer | Probe-Exit | Probe-Treffer |
|-----|-------------|-----------|---------------|------------|---------------|
| v33.0.9 | v33.0.9 | 0 | 0 | 2 | 3 |
| v34.0.6 | v34.0.6 | 0 | 0 | 2 | 3 |
| v35.0.3 | v35.0.3 | 0 | 0 | 2 | 3 |

Probe-Treffer je Tag gleich: TaintedHtml (245) lib/TaintProbe/ProbeController.php:38, TaintedTextWithQuotes (274) :38, TaintedSql (244) :45. Laufzeit ca. 27 s je Psalm-Lauf, ca. 250 MB.

**Liste "unbekannte Befunde": leer.**

## Task 2: Checkpoint

kein unbekannter Befund, Checkpoint entfällt.

## Task 3: Gate, Job, Audit, Trigger

- scripts/ci/psalm_taint_gate.sh: Lauf mit `set +e`, nur Exit 0/2 zulässig, `test -s` auf die SARIF-Datei, `jq '[.runs[].results[]] | length'`, Exit 2 mit 0 Treffern rot; Positivkontrolle kopiert die Probe nach lib/TaintProbe/ (verweigert, wenn das Verzeichnis schon existiert; trap entfernt nur Selbstangelegtes), Probe-Ausgabe in eine Datei (keine Annotationen im Runner), verlangt Exit 2, mindestens 2 Treffer, alle in lib/TaintProbe/, TaintedHtml und TaintedSql. shellcheck 0.11.0 (aus dem actionlint-Image) mit `--severity=style`: 0 Befunde.
- php.yml: Job psalm-taint nach composer-hygiene, PHP 8.3, `fail-fast: false`, `timeout-minutes: 15`, checkout mit `persist-credentials: false`, Pins wie im Repo, `OCP_VERSION` über env. composer-hygiene um zwei Schritte für php/tools/psalm ergänzt. paths (push und pull_request) um scripts/ci/psalm_taint_gate.sh ergänzt, PATHS_BEFORE nachgezogen.
- actionlint 1.7.12 über php.yml: nur die zwei bekannten SC2016-Befunde der `php -r`-Blöcke (Z. 488, 522, Umbau in 44-06), keiner im neuen Job. zizmor 1.32.0 `--persona auditor --min-severity medium` über php.yml: 5 artipacked an bekannten Stellen (Z. 100, 143, 410, 417, 577, Behebung 44-05), keiner im neuen Job.
- pytest: test_workflow_pins, test_workflow_tag_triggers, test_workflow_size, test_workflow_contexts, test_php_supply_chain_gates, test_php_surface_bans, test_php_route_gate_presence, test_public_artifacts: 242 passed.
- Skriptlauf im Spiegel gegen v35.0.3 (php über php:8.3-cli, jq vom Host): Exit 0, "taint findings: 0", "psalm taint gate: 0 findings, probe found 3".
- Lokaler Rot-Beweis (zusätzlich, Spiegel, v35.0.3): (a) Probe vorab in lib/TaintProbe/: Exit 1, "taint findings: 3", Probe-Verzeichnis vom Gate nicht angetastet. (c) psalm.xml ohne Plugin-Zeile: Exit 1, "the taint gate is blind: the probe gave 1 finding(s), expected at least 2" (nur TaintedSql). Die förmlichen Rotläufe a bis c folgen in 44-03.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SARIF-ruleId ist numerisch**
- **Found during:** Task 1 (erster Lauf)
- **Issue:** Psalm 6.20.10 schreibt als `ruleId` die Kurzkennung ("245"), den Namen "TaintedHtml" nur in `runs[].tool.driver.rules[]`. Ein Vergleich `.ruleId == "TaintedHtml"` wäre immer falsch und die Positivkontrolle immer rot.
- **Fix:** jq-Filter `NAMED_RESULTS` löst jede Kennung über die Regeltabelle auf; Ausgabe und Prüfung nutzen den Namen.
- **Commit:** 4f51f090

**2. [Rule 3 - Blocking] Baumhash der PHP-Hälfte**
- **Found during:** Task 3 (breiterer Testlauf)
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` zählt `php/**/*.php`; die zwei neuen Werkzeugdateien machen 132 statt 130.
- **Fix:** PHP_FILES_TODAY 132, PHP_TREE_HASH_TODAY ab283cdd mit Kommentar im Stil der Datei; Positivkontrolle: Rezept über git archive von b5b202e3 ergibt 3577bd32 mit 130 (der alte Wert).
- **Hinweis:** Liegt php/tools/psalm/vendor im Arbeitsbaum, zählt das Rezept ihn mit (4027 Dateien) und der Test ist lokal rot. Der Vendor-Ordner aus Schritt 2 wurde nach dem Lauf gelöscht (ignoriert, nur selbst erzeugt). Das lokale Rezept aus 44-03 arbeitet im Spiegel außerhalb des Repos.
- **Commit:** 4f51f090

**3. [Rule 3] jq im php:8.3-cli-Image fehlt**
- Weder php:8.3-cli noch composer:2 enthalten jq. Der lokale Skriptlauf lief deshalb mit einem php-Shim (Scratchpad, php im Container unter identischem Mountpfad, jq vom Host), ohne Schalter im Gate-Skript. Folge für 44-03: das Rezept "php:8.3-cli `bash /w/scripts/ci/psalm_taint_gate.sh`" braucht jq im Container oder dieselbe Shim-Form; dort entscheiden.

**Weitere Abweichung:** Stub ohne SPDX-Kopf (die App-Dateien tragen keinen); ProbeController erklärt im Kopf, warum nie nach lib/Controller/.

## Deferred Issues

- test_store_metadata.py `test_the_store_listing_document_avoids_the_blocked_term_counting_every_line` ist schon vor 44-02 rot (docs/store-listing.md, zuletzt 24c04abd); in deferred-items.md eingetragen, vor 44-09 klären.

## Threat Flags

Keine neue Oberfläche außerhalb des Threat-Modells: SARIF bleibt im Runner (E-05), der Job hat nur `contents: read`.

## Known Stubs

Keine. `app_api.phpstub` ist eine gewollte Psalm-Stub-Datei (nur Signaturen), kein UI-Platzhalter.

## Self-Check: PASSED

- FOUND: alle sieben neuen Dateien unter php/tools/psalm, php/psalm.xml, scripts/ci/psalm_taint_gate.sh
- FOUND: 4f51f090
