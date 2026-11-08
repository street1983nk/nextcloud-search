---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 07
subsystem: ci-e2e
tags: [e2e, coverage, upgrade, smb, proof]
requires: [43-05, 43-06, 43-17, 43-18, 43-20]
provides: [43-E2E.md, coverage-e2e gruen 5/5]
affects: [43-08, 43-11, 43-12]
tech-stack:
  added: []
  patterns: [Diagnose vor Fix (locked_diagnosis), gone-Storage als judge_locked-Argument, Positivkontrollen gegen 1.6.2]
key-files:
  created:
    - .github/workflows/coverage-e2e.yml
    - scripts/ci/coverage_e2e.sh
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-E2E.md
  modified:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-FREIGABEN.md
decisions:
  - "Der rote upgrade/native-Befund war ein Harness-Erwartungsfehler: die gesperrte Datei auf Carols entferntem Speicher steht zu Recht skipped/gone (Sofort-gone aus #25); judge_locked verlangt sie jetzt explizit und zaehlt die Verdikte ohne sie (17f81918)"
  - "Nur Diagnose statt Blindfix: locked_diagnosis druckt je gesperrter Datei storage, state, reason, attempts, etag, deleted_at, die Rueckkanal-Zeile und die Erneuerungs-Logzeile; Ids und Reason-Codes, nie Inhalte (c806b848)"
  - "leer.txt liefert unter 1.6.2 ebenfalls 200 mit 0 Bytes; die Unterscheidung alt/neu traegt allein das Urteil failed/gateway_error (gemessen 42418778026)"
metrics:
  completed: 2026-11-08
  tasks: 3
---

# 43-07: E2E-Abnahmetest, Push-Checkpoint und Beleg

Task 1 (Workflow + Runner-Gate) und Task 2 (Freigaben) waren seit 07.11. fertig;
Task 3 brauchte vier Fix-Runden (43-18 DENY-Fristen, Drossel, Harness-Suche) und
die 43-20-Erneuerung, bis Lauf 42503731869 auf Kopf 17f81918 alle fuenf Beine
gruen zeigte. Der vollstaendige Beleg mit allen Zahlen steht in 43-E2E.md.

Kernaussagen des gruenen Laufs: Sweep hinter blockiertem Gate mit sofortigem
gone/deselected, Zaehler pro Dokument mit D-43-11-Nenner, A1-Deduplikation,
Backfill beendet counting trotz unaufloesbarer Zeile, DENY-ACE ohne haengende
smbclient-Prozesse (422 in Millisekunden), einmalige Streak-Erneuerung
(rows=4 im Upgrade, rows=0 auf frischer Datenbank), Rueckweg 1.6.2 ok,
zweites Upgrade ok, Suchgegenprobe 22/22, beide Positivkontrollen gegen 1.6.2
greifen (kein Sweep in 240 s; 46/41 statt Wahrheit 23/55).
