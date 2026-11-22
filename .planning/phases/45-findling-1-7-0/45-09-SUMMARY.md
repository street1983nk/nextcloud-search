---
phase: 45-findling-1-7-0
plan: 09
subsystem: php-companion, ci
tags: [launch-hardening, audit, external-storage, rule-routes, digest-gate]
requires: [45-08]
provides: [45-AUDIT.md mit audited_head af0e5e13, Digest-Gleichheits-Gate, drei LOW-Fixes, grüner Kopf cb2038b9 auf main]
affects: [45-10, 45-12, 45-14]
tech-stack:
  added: []
  patterns: [Guard per IDBConnection::tableExists vor Abfragen auf Tabellen einer optionalen App, Obergrenze auch beim Lesen, strikter Schreibweg mit duldsamem Leseweg]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
  modified:
    - backend/tests/test_php_supply_chain_gates.py
    - php/lib/Service/StorageService.php
    - php/lib/Service/SettingsService.php
    - php/lib/Controller/SettingsController.php
    - php/tests/Unit/StorageServiceTest.php
    - php/tests/Unit/SettingsServiceTest.php
    - php/tests/Unit/SettingsControllerTest.php
    - backend/tests/test_phase33_audit.py
    - backend/tests/test_measurement_scripts.py
    - docs/admin-page.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
decisions:
  - "L-45-09-02: Die Regelrouten lehnen ein JSON-Objekt und eine Liste mit Lücke in allen drei Listen ab (empty, out_of_range für die Mount-Liste); das Lesen gespeicherter Objekt-Formen bleibt duldsam. Ersetzt die Regel H-33-01 'An object stays what it was'"
  - "L-45-09-03: Guard nur auf die fehlende Tabelle oc_external_mounts, nicht auf 'files_external deaktiviert', weil sonst alte oc_mounts-Zeilen ausgeschlossene Speicher wieder in den Index bringen könnten"
  - "L-45-09-01: die ersten 1000 brauchbaren IDs in gespeicherter Reihenfolge gelten, Überschuss als unusable gezählt"
metrics:
  duration: "ca. 150 min ab Task 2 laut Systemzeit, inkl. Instanz-Nachstellung, dreimal PHPUnit und PHP-Gates, ca. 35 min CI"
  completed: 2026-11-22
---

# Phase 45 Plan 09: Launch-Härtung und Audit von 1.7.0 Summary

Delta-Audit v1.6.5..HEAD mit 16 Prüfpunkten und Digest-Gate; die drei LOW-Befunde nach Owner-Entscheid per TDD behoben (Tabellen-Guard für files_external, Leseobergrenze 1000, Objekt-Ablehnung in allen drei Regellisten), L-45-09-03 auf einer frischen Nextcloud 34.0.3 vorher und nachher belegt; Kopf cb2038b9 auf main mit allen neun Workflows grün, audited_head af0e5e13.

## Tasks

| Task | Inhalt | Commits |
|---|---|---|
| 1 | Digest-Gate, Regressionsfälle, Audit-Bericht | 92fd028a, 493680a2, 2cf52981 (Checkpoint-Stand 802434fd) |
| 2 | Owner "Ok" 2026-11-22 05:36 UTC: Push ja, drei LOW beheben; Fixes per TDD | fcfa50b2 (L-03), 2b623a3f (L-01), af0e5e13 (L-02), cb2038b9 (Freigaben und Audit-Belege) |
| 3 | Push 612b7c9e..cb2038b9, ein CI-Warter grün, Belege, audited_head | Abschluss-Commit dieses Plans |

## Ergebnisse

- L-45-09-03 nachgestellt (frischer Container `nextcloud:34.0.3-apache`, SQLite, files_external aus, Tabelle fehlt, `occ` schreibt `[5]` bei Schalter an): vorher `DbalException ... no such table: oc_external_mounts` in `getMounts()`, Upload nicht eingereiht (queue rows 0), SchedulerJob bricht ab; nachher `getMounts: ok`, Upload eingereiht, Planer und Crawl laufen (54 Dateien), keine Logzeile. Befehle und Ausgaben wörtlich in 45-AUDIT.md.
- RED vor den Fixes: 11 Fälle rot (1 Error, 10 Failures), genau die neuen; GREEN danach, volle Suite 1299 Tests grün.
- CI am Kopf cb2038b9: Multi-arch image, Security scans, HaRP deploy, Workflow security lint, Python gates, Resilience, OpenSSF Scorecard, Integration, PHP and store metadata gates alle success, kein Rerun. Update-Probe v1.6.4 und v1.6.5 -> 1.7.0 ok (Lauf 44993702837), HaRP "installed_version went from 1.5.0 to 1.7.0" und frische Installation mit Treffer ohne Konfiguration (Lauf 44993702767).

## Deviations from Plan

1. **[Rule 3 - Werkzeug] Erster PHP-Gate-Lauf zum Commit 2b623a3f rot, Commit trotzdem schon erstellt.** Ursache: vimeo/psalm im Gate-Container unvollständig entpackt ("psalm wrote no SARIF report"), kein Codebefund. Der Commit lief in einer Befehlskette mit `;` direkt danach. Der zweite Lauf am unveränderten Baum desselben Commits war grün (drei Mal 0 Taint-Befunde, php-cs 0, zizmor und actionlint ohne Befund). Dokumentiert in 45-AUDIT.md; B3 damit nachträglich erfüllt, aber die Reihenfolge war falsch.
2. **[Eingrenzung L-45-09-03] Guard nur auf die fehlende Tabelle.** Der freigegebene Vorschlag nannte "files_external nicht aktiviert ODER Tabelle fehlt". Die App-Bedingung wurde bewusst nicht umgesetzt: mit deaktivierter App, aber vorhandener Tabelle läuft die Abfrage fehlerfrei, und eine leere Menge würde dann ausgeschlossene Speicher über alte oc_mounts-Zeilen wieder zulassen (Ausschluss fiele offen aus). Enger als freigegeben, keine zusätzliche Verhaltensänderung. Der Owner sollte das zur Kenntnis nehmen.
3. **CHANGELOG 1.7.0 nicht ergänzt.** L-45-09-02 ändert das Verhalten der Regelroute für gebaute Anfragen (Objekt seit 1.7.0 abgelehnt). Die CHANGELOG-Freigabe von 45-08 ist verbraucht; die Zeile steht in docs/admin-page.md. Ob CHANGELOG eine Zeile bekommt, entscheidet der Owner (nur nicht nutzersichtbar über die Seite).
4. Regel H-33-01 wurde in Code-Docblocks, docs/admin-page.md und test_phase33_audit.py neu gefasst; ältere Planungsnotizen (33-AUDIT, STATE-Einträge von 33-11) bleiben als Historie unverändert.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: keine neue Route, kein neuer Schlüssel, keine neue Logzeile mit Wert. Der Guard liest nur das Schema.

## Self-Check

- 45-AUDIT.md: audited_head af0e5e13e17aeb8d915dd5caacffcb056eb49e69, status_45_09 passed, Verify-Kette des Plans ohne CI-Aufruf grün (VERIFY-OK), af0e5e13 ist Vorfahre von origin/main.
- Commits vorhanden: 92fd028a, 493680a2, 2cf52981, 802434fd, fcfa50b2, 2b623a3f, af0e5e13, cb2038b9.

## Self-Check: PASSED
