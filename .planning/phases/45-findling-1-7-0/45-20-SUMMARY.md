---
phase: 45-findling-1-7-0
plan: 20
subsystem: gateway, reconcile, audit trail, ci, docs
tags: [issue-59, issue-25, watermark, secure-view, files-accesscontrol, admin-audit, live-probe, update-path, tdd]
requires: [45-17, 45-18, 45-19, 45-22, 45-23, 45-24, 45-25, 45-26]
provides: [Gegenprobe nach dem Fix über den echten Update-Weg in M1 bis M5, Live-Proben #25 F1 und F2, Erneuerung 1.7.0 erst ab Generation 4, Prüfspur mit lesender Person, origin in der warning-Zeile, CI-Job watermark-59, CHANGELOG und Doku 1.7.0]
affects: [45-21, 45-10, 45-16]
tech-stack:
  added: []
  patterns: [OCP-Audit-Ereignis CriticalActionPerformedEvent nur nach einem Lesen in actAs, Herkunft einer Ausnahme nur als Klasse::Funktion aus dem ersten Frame, einmalige Erneuerung an die Generation der Gegenseite gebunden]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-20-SUMMARY.md
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/reconcile.py
    - php/lib/Service/GatewayReader.php
    - php/lib/Controller/GatewayController.php
    - php/tests/Unit/GatewayReaderTest.php
    - php/tests/Unit/GatewayControllerTest.php
    - php/tests/Unit/SecureViewRefusal.php
    - backend/tests/test_store_repo.py
    - backend/tests/test_poller.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_php_static_gates.py
    - .github/workflows/integration.yml
    - CHANGELOG.md
    - CHANGELOG.de.md
    - CHANGELOG.fr.md
    - docs/reconcile.md
    - docs/formats.md
    - docs/admin-page.md
    - docs/privacy.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
    - .planning/phases/45-findling-1-7-0/45-20-PLAN.md
decisions:
  - "U-45-20-01 (MEDIUM, Owner f1): die Erneuerung refusal_streaks_1_7_0 läuft erst im ersten Pass, der Generation 4 von der Begleit-App liest; die Reihenfolge der Updates ist gleichgültig"
  - "U-45-20-02 (MEDIUM, Owner a4): admin_audit nennt für ein Lesen in actAs die Sitzungsperson (--); das Gateway dispatcht deshalb CriticalActionPerformedEvent mit id, Pfad und uid, nur nach einem Lesen in actAs; info-Zeile mit reader"
  - "U-45-20-03 (LOW, Entscheid c2): warning-Zeile einer anderen ForbiddenException mit origin = Klasse::Funktion, nie Meldung, Pfad oder Argument"
  - "I-45-20-04 (INFO): Team Folder unter shareAll indexiert über das Mitglied, das ihn selbst herunterladen darf (groupfolders getOwner)"
  - "I-45-20-05 (INFO): verify von Task 1 an Logformate angepasst (Schritt C (c) drei Belege statt Literalzeile nach c2; asked als Zeichenkette)"
  - "F2 mit echtem Container-Backend am Kopf und echtem OCR-Rückstand (Owner t1)"
metrics:
  duration: "ca. 11 h 40 min laut Systemzeit (10:39 bis 22:20 UTC), davon über 6 h echtes Warten auf Abgleich-Intervalle (d1, F1, F2)"
  completed: 2026-11-23
---

# Phase 45 Plan 20: Gegenprobe #59 über den echten Update-Weg, Live-Proben #25, CI, CHANGELOG und Doku Summary

#59 ist nach dem Fix auf echter Instanz über den Update-Weg 1.6.5 -> 1.7.0 in allen fünf Wasserzeichen-Modi belegt, mit files_accesscontrol, E1-Prüfspur und E3-Ausschnitten; #25 F1 und F2 sind auf einer frischen Instanz mit Container-Backend und echtem OCR-Rückstand belegt. Drei Befunde der Gegenprobe sind per TDD behoben, zwei als INFO festgehalten.

## Tasks

| Task | Inhalt | Commits |
|---|---|---|
| 1 | Serie auf v1.6.5 (d1, echt), Schritt A und B (zweimal, nach dem Fix U-45-20-01), Suche direkt nach dem Update, M1 bis M5, Pfad, asked, files_accesscontrol, E1, E3, Altbestand, Fixes U-45-20-01 bis -03 | aec5edcf, 151dca7b, f3290689, 1d191e7e, 3550b2b3, c9dc3270, aca91fac |
| 2 | Live-Proben #25 auf findling-25 (Container-Backend am Kopf), F1 (a), Gegenkontrolle, (b), (c), F2 mit 9000 gescannten Seiten | 960dec8c |
| 3 | CI-Job watermark-59 mit Strukturgate, CHANGELOG (Text 4, E3, Text 7, I-45-26-01), Doku, status_45_20; Gate-Korrektur des origin-Musters | 0f6afac7, 457a0786, 25980ccd, Summary-Commit |

## Deviations from Plan

1. [Checkpoint, Owner f1] U-45-20-01 MEDIUM: die Erneuerung von 1.7.0 lief vor einer Begleit-App der Generation 3 und wurde verbraucht. Fix per TDD, Schritt A und B neu; vor dem Neulauf nur die Marke aus state.db entfernt (restore20.py, im Audit).
2. [Checkpoint, Owner a4] U-45-20-02 MEDIUM: admin_audit nannte die lesende Person nicht. Fix per TDD mit CriticalActionPerformedEvent, live belegt.
3. [Checkpoint, Entscheid c2] U-45-20-03 LOW: origin in der warning-Zeile; Plan-Erwartung der Literalzeile "Access denied by access control" war falsch, verify von Task 1 prüft drei Belege (Entscheidzeile in 45-FREIGABEN.md).
4. [Rule 3] verify von Task 1 erwartete `"asked": 20`, nextcloud.log schreibt `"asked":"20"`; Regex nimmt optionale Anführungszeichen, Zahl weiter exakt (I-45-20-05).
5. Team Folder unter shareAll indexiert statt policy_blocked (Entscheid INFO), Erwartungstabelle und docs/privacy.md begründen es.
6. Schritt C (a) und (b) mit eigenen Tags statt `fac59`, damit die Regeln nebeneinander stehen.
7. F1 (b): eine Nachzählung von 50 000 Einträgen braucht unter einer Sekunde je Scheibe; der belastbare Lauf nutzt den empfohlenen Cron-Takt von 5 Minuten, damit ein Tick in die Runde fällt. F2: meta.py läuft im Backend-Container (state.db im Volume).
8. Erste gw20-Probe mit Person im AppAPI-Kopf verworfen und korrigiert; Altbestand-Erstabfrage 1 bis 2 s nach einer CLI-Einstellung (APCu des Webservers) verworfen und gemessen.
9. [Rule 1] c9dc3270 wurde mit gefiltertem PHPUnit und den betroffenen pytest-Dateien committet, nicht mit der vollen Suite; der volle Lauf vor Task 3 fand den Gate L-36-01 rot (verankerte Namensprüfung von `GatewayReader::origin` ohne Modifier D, ein Name mit Zeilenumbruch hätte gepasst). Behoben im fix-Commit der Gate-Korrektur, Baumhash PHP 7e296129, volle Gates danach grün.

## TDD Gate Compliance

Je Fix ein test(45-20)-Commit (RED) vor dem fix(45-20)-Commit (GREEN): aec5edcf/151dca7b, f3290689/1d191e7e, 3550b2b3/c9dc3270; Mutationen jeweils rot (4, 4 und 3 Mutationen).

## Known Stubs

Keine.

## Threat Flags

| Flag | File | Description |
|---|---|---|
| threat_flag: audit-trail | php/lib/Service/GatewayReader.php | neue Prüfspur-Zeile mit uid und Pfad (nur admin_audit, kein Inhalt); in 45-16 gegen T-45-Register prüfen |

## Self-Check: PASSED
