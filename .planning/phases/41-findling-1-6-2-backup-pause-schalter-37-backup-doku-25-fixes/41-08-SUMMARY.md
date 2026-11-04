---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 08
subsystem: release, ci (deploy-harp)
tags: [release, 1.6.2, upgrade-proof, backup-pause, ci]
requires:
  - 41-07 (Backup-Doku, CI-Schritt Backup pause)
provides:
  - Version 1.6.2 an allen Lockstep-Stellen (zwei version, ein image-tag, sechs Links)
  - CHANGELOG [1.6.2] mit Linkdefinition v1.6.1...v1.6.2
  - Store-Listing-Abschnitt "# Entwurf v1.6.2, Stand Plan 41-08 (04.11.2026)"
  - Zusicherung 13 in "Store upgrade 5": nach dem Upgrade pause running
  - scripts/ci/backup_pause_proof.sh, scripts/ci/store_install_register.sh
  - backend/tests/test_workflow_size.py (500-KB-Gate)
affects:
  - 41-09 (Audit des Deltas v1.6.1..Kopf)
  - 41-10 (Owner-Runde: Store-Entwurf, Release-Notiz)
key-files:
  created:
    - scripts/ci/backup_pause_proof.sh
    - scripts/ci/store_install_register.sh
    - backend/tests/test_workflow_size.py
  modified:
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - CHANGELOG.md
    - docs/store-listing.md
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
    - backend/tests/test_cert_rotation_steps.py
decisions:
  - "Pause-Zusicherung über die Overview (pause running, pauseWished false) plus oc_appconfig ohne findling/paused; der Status-Wert ist prozesslokal, ein docker exec report() sähe nur den Default"
  - "deploy-harp.yml unter 500 KB: Run-Blöcke von Backup pause und Store install 6 wörtlich nach scripts/ci/ verschoben, Gate test_workflow_size.py"
  - "Uninstall 5 / Store uninstall 5 warten bis der Container den Pause-Wunsch gelesen hat (D-41-19 bleibt Produktverhalten, kein Produktfix)"
metrics:
  duration: "ca. 3 h 30 min (inkl. fünf CI-Läufe)"
  completed: 2026-11-04
  tasks: 2
  commits: 6
---

# Phase 41 Plan 08: Release-Vorbereitung 1.6.2 Summary

1.6.2 an allen Lockstep-Stellen, CHANGELOG und Store-Entwurf, Upgrade-Beweis ab v1.5.0 mit neuer Zusicherung "nach dem Upgrade nicht pausiert"; zwei CI-Blocker (500-KB-Grenze des Workflows, Rennen in der Halbentfernung durch D-41-19) behoben.

## Commits

| Hash | Nachricht |
|------|-----------|
| a06f692d | chore(41-08): version 1.6.2 in both apps |
| f12649a2 | ci(41-08): the upgrade proof names the tree 1.6.2 against v1.5.0 and checks the pause |
| eb4284bc | fix(41-08): keep deploy-harp.yml under the 500 KB cap of GitHub Actions |
| a9ba54a3 | ci(41-08): the half removal waits until the container has read the pause wish |
| cc4a4630 | fix(41-08): read pauseWished false as false in the upgrade pause assurance |
| 738a1373 | fix(41-08): the upgrade pause assurance reads the overview afresh |

Autor street1983nk <k.cherif@outlook.de>, ohne Trailer. Gepusht auf main, kein Tag.

## Task 1: Bump, CHANGELOG, Store-Entwurf

`git diff v1.6.1 -- backend/appinfo/info.xml php/appinfo/info.xml`: nur die sechs Links `blob/v1.6.1` -> `blob/v1.6.2`, zweimal `<version>1.6.2</version>`, `<image-tag>1.6.2</image-tag>` und die commands-Zeile der Companion (+ PauseCommand, ResumeCommand).

- CHANGELOG `## [1.6.2] - 2026-11-04`: Added 2, Fixed 6, `[Unreleased]` leer, Linkdefinition `compare/v1.6.1...v1.6.2`.
- docs/store-listing.md: Entwurfsabschnitt vor "# Release 1.6.1", Namen und Beschreibungen zeichengleich zu 1.6.1, sieben neue Sätze en/de/fr (gateway_error-Hinweis, sechs Pause-Sätze), Entwurf der englischen Release-Notiz. Owner-Abnahme in 41-10.
- Konsistenz-grep `blob/v1.6.2` außerhalb der erlaubten Dateien: leer. Keine Gates hielten 1.6.1 als aktuellen Stand fest (test_lockstep_versions + test_store_metadata 140 grün).

## Task 2: Upgrade-Strecke, STOPP-Prüfung, CI

- `UPGRADE_FROM_TAG: v1.5.0` bleibt; Begründungssatz zu 1.6.2 unter dem v1.5.0-Absatz; Kommentare "the tree carries 1.6.2 (1.6.1 until 2026-11-04, ...)", "installed_version 1.6.2", Image-Tag-Kommentar.
- Neue Zusicherung 13 in "Store upgrade 5" ("twelve assurances"): frisch gelesene Overview `pause == running` binnen 60 s (unknown unterwegs erlaubt, paused/pausing nie), `pauseWished == false`, `oc_appconfig` ohne `findling/paused`; sonst `::error::an upgrade must not leave indexing paused ...`.
- `grep -c '::error::'` in deploy-harp.yml: vorher 249, nach f12649a2 250 (genau +1). Die Verschiebung in eb4284bc nimmt die 17 `::error::` des Backup-pause-Blocks nach scripts/ci/backup_pause_proof.sh mit (Datei danach 233, 233 + 17 = 250); a9ba54a3 fügt keines hinzu.
- test_upgrade_seed_steps.py und test_cert_rotation_steps.py auf "twelve" und Abschnitt 13 nachgezogen.
- STOPP-Prüfung: `git diff --stat v1.6.1..HEAD -- php/lib/Migration backend/src/findling/store/schema.sql backend/src/findling/store/vectors.sql backend/src/findling/index/schema.py` leer; kein `+`-Treffer auf STORE_SCHEMA_MARK/SCHEMA_VERSION/write_meta/set_meta.
- Lokal: Volltestsuite in zwei Hälften 3673 passed / 49 skipped und 2890 passed / 254 skipped; ruff, ruff format, pyright (0 errors), vulture grün; PHPUnit Docker OK (958 tests, 5851 assertions); actionlint nur die 9 bekannten info/style-Meldungen; shellcheck der zwei neuen Skripte sauber.

## CI-Beleg (Kopf 738a1373)

head_green.sh Exit 0 auf 738a1373: HaRP deploy 41803255633 success (alle vier Beine), Security scans 41803255432 success, OpenSSF Scorecard 41803255431 success. Die übrigen Workflows laufen wegen Pfadfiltern nicht auf diesem Kopf (Kopf ändert seit eb4284bc nur deploy-harp.yml): Python gates 41793610965, Integration 41793611053, Resilience 41793610962, Multi-arch image 41793610951 success auf eb4284bc; PHP and store metadata gates 41792859857 success auf f12649a2 mit "OK (958 tests, 5851 assertions)".

Wörtlich aus HaRP deploy 41803255633, Bein stable34 / ubuntu-24.04:

- Store upgrade 4: "the companion of this commit carries version 1.6.2", "installed_version went from 1.5.0 to 1.6.2"
- Store upgrade 5: "pause reads running after the upgrade (states seen: running), pauseWished is false and oc_appconfig carries no findling/paused", "all twelve assurances of this step hold"
- Backup pause (41-07, jetzt scripts/ci/backup_pause_proof.sh): "A1 holds: container nc_app_findling_backend, volume nc_app_findling_backend_data"; "Paused. Indexing has stopped and everything is flushed to disk; search keeps working."; "wal: state.db-wal and vectors.db-wal are empty or absent"; "after the restart of the backend container: pause=paused 7s after the first answer, states seen: unknown paused"; "after the restart of Nextcloud: pause=paused 0s after the first answer, states seen: paused"; "pause after resume: running"
- Uninstall 5/6 und Store uninstall 5/6: "the container read the pause wish: running", "retreat announced after 3 lines, 0 lines in the 60 s that followed"

A1 bestätigt, docs/backup*.md brauchen keine Korrektur. D-41-05 und D-41-06 sind damit im CI belegt (offene Punkte aus 41-07 erledigt).

## Deviations from Plan

1. **[Rule 3] deploy-harp.yml über der 500-KB-Grenze.** Der erste Push (f12649a2) bekam HaRP-Lauf 41792857387 ohne Job: "exceeds the maximum allowed size of 500 KB". Ursache: der Schritt aus 41-07 hob die Datei von 508782 auf 524483 Bytes (526401 mit 41-08). Fix eb4284bc: Run-Blöcke von "Backup pause" und "Store install 6" (beide ohne Testvertrag auf den Text) wörtlich nach scripts/ci/ (Matrixwerte als env, `set -eo pipefail`), Datei 501251 Bytes; Gate test_workflow_size.py (jede Workflow-Datei < 500*1024 Bytes, die zwei Schritte rufen ihr Skript).
2. **[Rule 1] Halbentfernung rot auf drei von vier Beinen (Lauf 41793610987).** "Uninstall 6"/"Store uninstall 6": "the container never announced the retreat". Der in Schritt 5 neu registrierte Container hatte den Pause-Wunsch noch nicht gelesen, als die Companion entfernt wurde; nach D-41-19 hält er dann alle Schreiber und pollt nie, also kommt die Rückzugszeile von D-17 nicht. stable35 war grün (Rennen). Fix a9ba54a3: Schritt 5 beider Hälften wartet bis 90 s auf "backup pause: running" im Log seit der Registrierung. Produktverhalten bleibt (Owner-Entscheid D-41-19); offene Frage für 41-09: Ein Container, der ohne Companion startet, bleibt still auf unknown statt sich zurückzuziehen, was ruhig ist, aber die D-17-Zeile nie schreibt.
3. **[Rule 1] Eigener Fehler in Zusicherung 13.** Lauf 41796285191: `jq '.pauseWished // "absent"'` macht aus false "absent" (jq-Alternativoperator); die Instanz lief korrekt (pause 'running', 0 Zeilen findling/paused). Fix cc4a4630: `.pauseWished | tostring`. Danach Lauf 41799683340: pause 'unknown' im Overview-Schnappschuss aus "Store upgrade 4" (Container nach dem Upgrade hatte den Wunsch noch nicht gelesen, D-41-19). Fix 738a1373: Zusicherung 13 fragt die Overview bis 60 s neu ab, unknown unterwegs erlaubt, paused/pausing nie, Ziel running.
4. **PHP and store metadata gates laufen nicht auf dem Kopf** (Pfadfilter, nur deploy-harp.yml/scripts/tests geändert). Beleg auf f12649a2 (gleicher php/-Baum): Lauf 41792859857 success, "OK (958 tests, 5851 assertions)". Python gates, Integration, Resilience, Multi-arch image grün auf eb4284bc (vom Kopf nur in deploy-harp.yml verschieden).

## Known Stubs

Keine.

## Threat Flags

Keine neuen. T-41-32 (STOPP-Prüfung leer, Strecke ab v1.5.0), T-41-33 (Zusicherung 13), T-41-34 (Lockstep-Test grün) umgesetzt.

## Self-Check: PASSED

- scripts/ci/backup_pause_proof.sh, scripts/ci/store_install_register.sh, backend/tests/test_workflow_size.py vorhanden
- Commits a06f692d, f12649a2, eb4284bc, a9ba54a3, cc4a4630, 738a1373 vorhanden, Autor street1983nk, ohne Trailer
