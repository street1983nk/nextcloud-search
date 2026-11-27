---
phase: 46-findling-1-7-1
plan: 04
subsystem: ci
tags: [pruef-05, pruef-06, apt, harp-deploy]
requires: [46-02]
provides: [scripts/ci/apt_install.sh, Gate apt-Zeitlimit, Gate Warten auf die Queue in Store upgrade 2b]
affects: [setup-test-nc, integration.yml, coverage-e2e.yml, python.yml, deploy-harp.yml]
key-files:
  created:
    - scripts/ci/apt_install.sh
    - scripts/ci/apt_install_selftest.sh
    - backend/tests/test_ci_apt_timeouts.py
  modified:
    - .github/actions/setup-test-nc/action.yml
    - .github/workflows/integration.yml
    - .github/workflows/coverage-e2e.yml
    - .github/workflows/python.yml
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
duration: ca. 75 min
completed: 2026-11-27
---

# 46-04: CI-Robustheit (PRUEF-05, PRUEF-06)

Ausgeführt vor 46-03 nach `Entscheid Reihenfolge 46-04` (Owner "Ok", Commit a63bb9d2), ohne Docker. Vorab im selben Auftrag: I-46-01-01 behoben, 292197c9 `docs(46-05): the evidence of release 1.7.0 keeps clear of the blocked term` (drei Zeilen in docs/store-listing.md, "# Release 1.7.0": "Release-Workflow (release.yml)", "der beiden Pakete", Schrittname ohne das gesperrte Wort; Belege gleich; test_store_metadata 168 passed; gedeckt von `Freigabe Text store-listing 46-05`).

## Vorprüfung

- GitHub-Doku (metadata-syntax, gelesen 27.11.): `runs.steps[*]` einer Composite-Action kennt run, shell, if, name, id, env, working-directory, uses, with, continue-on-error; kein `timeout-minutes`. Das Zeitlimit liegt deshalb in der Shell.

## Task 1: apt_install.sh (I-45-10-07 aus 45-AUDIT.md)

- RED 54d7785d `test(46-04): every apt install of the test jobs has a time limit and retries`: `test_no_step_of_the_scope_calls_apt_get_itself` rot mit 13 Funden (erster `action.yml:397: calls apt-get itself: sudo apt-get update -qq`), übrige vier Tests grün.
- GREEN 4d5c4c6e `fix(46-04): the dictionary download and the tesseract installs give up after a time limit and retry`:
  - scripts/ci/apt_install.sh: ein Zeitlimit je Versuch für update und install zusammen (Standard 120 s, 1 bis 300), `Acquire::Retries=3`, http/https-Timeout 30 s, höchstens drei Versuche (1 bis 3), Pause 10 s (0 bis 60), Paketnamen nur `[a-z0-9.+-]`, Logzeile nur Versuch, Exitcode, Dauer; schlimmstenfalls 380 s.
  - scripts/ci/apt_install_selftest.sh: sechs Fälle ohne Netz und ohne sudo (Stand-in für apt-get): Hänger (drei Zeitlimits, rot), zweimal Fehler dann Erfolg (grün), ein Versuch (update vor install mit den Optionen), Paketname mit Shell-Code, keine Pakete, Zeitlimit über 300 (je abgewiesen ohne Aufruf). Lokal: "all 6 cases hold" (GNU timeout 8.32 in Git Bash).
  - Aufrufstellen: setup-test-nc (Wörterbuch, Kommentar mit Verweis), integration.yml dreimal tesseract, coverage-e2e.yml einmal tesseract, je `bash findling-src/scripts/ci/apt_install.sh ...`; die Prüfung `[ ! -f /usr/share/dict/ngerman ]` bleibt.
  - python.yml: die zwei neuen Skripte in der vorhandenen shellcheck-Zeile.
  - Beide Skripte mit Modus 100755 im Index.
- Gate backend/tests/test_ci_apt_timeouts.py: kein `apt-get update|install` mehr in den drei Dateien außerhalb von Kommentaren, Anzahl der Aufrufe je Datei, schlimmster Fall des Skripts (aus seinen Standardwerten gelesen) unter der Hälfte des kleinsten `timeout-minutes` aller Jobs, die die Action nutzen oder das Skript rufen (Planprüfung B-3), Selbsttest per subprocess (übersprungen ohne bash mit GNU timeout). Positivkontrollen: der Schritt aus 1.7.0 (zwei Funde), ein nacktes `apt-get -qq update`, Budget 300 s x 3 gegen 25 Minuten.
- Mutationen je rot, Dateien danach byte-gleich (`cmp`): M1 Skript ohne `timeout`, M2 Standard ein Versuch, M3 coverage-e2e zurück auf `sudo apt-get install`, M4 Standard 300 s.
- Gates: ruff, ruff format, pyright (0 Fehler), vulture grün; test_ci_apt_timeouts, test_workflow_pins, test_workflow_size, test_workflow_contexts, test_workflow_tag_triggers 73 passed.

## Task 2: Store upgrade 2b (I-45-12-01)

- RED ad3002f8 `test(46-04): store upgrade 2b waits for the queue row before it judges the acceptance`: `test_the_acceptance_waits_for_the_queue_row_of_the_stale_file` rot.
- GREEN 142c4296 `fix(46-04): store upgrade 2b judges the acceptance once the queue row is gone`: nach `indexed/` eine Schleife bis zur leeren Queue-Zeile innerhalb des restlichen Budgets (dieselbe `deadline` wie Teil 5), je Runde `step 5: N queue row(s) of kind 'K' left for the stale file, Ss of the budget left` (keine Pfade), danach Zählung und Prüfung `1:1:0` und `left=0` unverändert, also rot bei bleibender Zeile. Im GREEN-Commit auch eine Korrektur des Gates (früher Abbruch, wenn die Schleife fehlt, damit die Positivkontrolle genau einen Fund liefert).
- deploy-harp.yml: 507 734 -> 508 437 Byte (Grenze unter 512 000), test_workflow_size grün; `bash -n` des Schritts grün (vorhandener Test).
- Mutationen: in der Datei M1 Abfragezeile entfernt, M3 Abbruchbedingung `-ge 0 ] || break`, je rot und zurückgesetzt; M2 (Schleife nach der Prüfung) als Positivkontrolle im Test.
- Gleiche Rennen gesucht: `COUNT(*) FROM oc_findling_queue` in deploy-harp.yml und integration.yml. Treffer Z. ~4568 und ~4587 (dieser Teil, jetzt nach der Wartezeit), Z. ~4781 (Datei unter dem Ausschluss-Präfix: wird nie in die Queue gestellt, also kein Rennen, keine Änderung). integration.yml: keine Queue-Prüfung. Die Schleifen mit `open=0` warten schon auf die leere Queue.
- Läufe: test_upgrade_seed_steps 110 passed, Workflow-Tests 177 passed.

## Offen und Abweichungen

- shellcheck ist lokal nicht installiert; die zwei Skripte prüft "Python gates" in CI nach dem Push (46-06). zizmor und actionlint (php_gates_docker.sh workflows) brauchen Docker: im Docker-Fenster vor dem Push.
- Der Beleg in echter CI (Wartezeile im Log, Wörterbuch über das Skript, alle vier HaRP-Varianten grün) folgt in 46-06; coverage-e2e.yml nur per Dispatch (eigene Freigabe dort).
- Befund I-46-04-01 (LOW, außerhalb des Umfangs von E-46-04 a): scripts/ci/coverage_e2e.sh Z. ~1492 und scripts/ci/smb_acl_measure.sh Z. ~55 rufen `apt-get update/install` (samba, smbclient, sqlite3) ebenfalls ohne Zeitlimit; Empfehlung: im Backlog wie die übrigen apt-Aufrufe, oder in 1.7.1 mit demselben Skript (Owner-Entscheid).
