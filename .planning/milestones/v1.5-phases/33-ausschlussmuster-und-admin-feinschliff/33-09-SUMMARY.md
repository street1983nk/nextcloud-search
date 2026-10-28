---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 09
subsystem: exclusions, reconcile, admin-ui, proof
tags: [excl-02, excl-01, excl-03, weg-a, weg-c, d-33-01, dev-instance, gegenprobe, l-33-09-01]
requires:
  - "33-03: Weg C im Abgleich (Commit eff4a9bf)"
  - "33-04: Kehrjob Weg A und forgetVerdicts im Abgleichs-Slice"
  - "33-05: Musterliste, Fehlersätze, zahlenlose Bestätigung"
provides:
  - "33-09-NACHWEIS.md: Weg A und Weg C auf 8090 mit Positivkontrolle, Kontrolle, Gegenfall und Gegenprobe auf dem Codestand vor 33-03"
  - "Fix L-33-09-01: Regelvorschau als POST mit Body, kein Regelwert mehr in nextcloud.log oder Access-Log; Logsatz je Liste"
  - "Gate scan_rules_routes mit Selbsttest gegen eine Rückkehr der Vorschau zu GET"
affects: [33-10, 33-11, 36]
tech-stack:
  added: []
  patterns:
    - "Regelwerte reisen nur im Body: das Kernfeld url jeder Logzeile und das Access-Log tragen die Adresse"
    - "Gegenprobe eines alten Containerstands per Worktree und PYTHONPATH auf denselben Speicher"
key-files:
  created:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-09-NACHWEIS.md
  modified:
    - php/lib/Controller/SettingsController.php
    - php/lib/Service/ExclusionService.php
    - php/js/admin.js
    - php/tests/Unit/SettingsControllerTest.php
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "33-09: L-33-09-01 nach Owner-Entscheid 14.10.2026 Option 1 gefixt: POST /admin/rules/preview mit JSON-Body, Request-Token wie jede Admin-Route"
  - "33-09: Abgelehnte Muster loggen 'refused an exclusion pattern that is not a usable pattern'; der Ordnersatz bleibt byte-gleich zu 1.4.2 (Differenztest)"
  - "33-09: Weg-C-Läufe mit FINDLING_OCR_ENABLED=false, damit no_text_layer auf dem Host ohne Tesseract stehen bleibt"
metrics:
  duration: "ca. 4 h 40 min (10:21 bis 15:00) inkl. Anhalten am Befund, Fix mit Volltestlauf (16:48 min), drei Abgleichsläufen nach Fälligkeit und CI"
  completed: 2026-10-14
  tasks: 2
  files: 7
---

# Phase 33 Plan 09: EXCL-02 auf der Dev-Instanz 8090 Summary

Weg A und Weg C sind an der laufenden Instanz belegt: Bereits indexierte Dateien unter `*.key`, `*/node_modules/*` und einem Präfix verschwinden aus der Suche, Kontrolle und Gegenfall `.keynote` bleiben, die Urteilszeilen unter Regel verschwinden, die Kontrollzeilen bleiben. Auf dem Containerstand vor 33-03 bleiben G und H nach einem fälligen Abgleich auffindbar (`stale=0`), auf dem neuen Stand verschwinden sie (`stale=7`), ein zweiter Abgleich reiht nichts erneut ein. Unterwegs fand der Nachweis L-33-09-01 (Regelwerte im nextcloud.log über die GET-Vorschau), nach Owner-Entscheid als POST gefixt.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Weg A über die Seite (Positivkontrolle, Kontrolle, Gegenfall, B2, Zähler, Diagnose, Bestand, Ablehnungen, Logprobe) | 8e00d401 (Zwischenstand beim Anhalten), Abschluss im docs-Commit | 33-09-NACHWEIS.md |
| Fix | L-33-09-01: Regelvorschau als POST, Logsatz je Liste | fe813988 | SettingsController.php, ExclusionService.php, admin.js, SettingsControllerTest.php, test_admin_ui_contract.py, test_measurement_scripts.py |
| 2 | Weg C mit Gegenprobe vor 33-03, Rückweg, Aufräumen | docs-Commit | 33-09-NACHWEIS.md |

## Ergebnisse

- **Weg A:** A (`Vortrag.key/Data/notiz.txt`) und D (`/node_modules/x.txt`) von 1 auf 0 Treffer, B (Kontrolle) und C (`Vortrag.keynote`) bleiben 1, E unter `Archiv` 0. Bestätigung ohne Zahl, genau ein ExclusionSweepJob, nach einem cron.php weg, rund eine Minute bis zum Verschwinden.
- **Weg C:** Regeln per occ (`*.key`, Präfix `Abnahme33c/Altordner`), kein Kehrjob und kein SubtreeExpandJob. Gegenprobe auf `bd4e13af`: G 1, H 1 (`stale=0`). Neuer Stand: G 0, H 0, K 1 (`stale=7`), Diagnose `excluded`; zweiter Abgleich `stale=0`, Queue 0. Fälligkeit je Lauf aus `_is_due` gerechnet, Stunde bei jedem Neustart neu gesetzt, Zeitpunkte im NACHWEIS.
- **Urteilszeilen:** Weg A: 2995 weg, Kontrolle 2996 bleibt, Fehlerliste `image_not_ocrable` 10 auf 9. Weg C: zwei `no_text_layer`-Zeilen unter `Praesentation.key` weg (schon im Slice des Gegenprobe-Laufs, weil die Bereinigung laut 33-04 auf der PHP-Seite sitzt), Kontrolle 3008 bleibt.
- **Zähler und Diagnose:** Kachel "Excluded by a rule" nach dem Recount 2 auf 6; neue Datei F unter dem Bundle ohne Queue-Zeile; Diagnose "Excluded by a rule" mit der Abhilfe für beide Listen.
- **Präfix Archiv:** `exclusions` hex `5B22417263686976225D` am Anfang, nach den Ablehnungen und am Ende gleich; E 0, Diagnose `excluded`.
- **Ablehnungen:** `[0-9]*`, `**/x`, `!foo`, `*`, `node_modules` je mit dem Satz aus 33-WORTLAUT.md und ohne Bestätigung; 61 Zeichen und 33 Muster lokal abgelehnt, am Formular vorbei HTTP 400 `too_long` bzw. `too_many`; nichts gespeichert.

## Fix L-33-09-01

- Befund: Die Vorschau war GET mit allen Präfixen und Mustern in der Query; Nextcloud schreibt die Adresse in das Feld `url` jeder Logzeile, also standen bei abgelehnter Vorschau alle Regelwerte im nextcloud.log und im Access-Log (seit v1.4.2 für Präfixe). Nebenbefund: falscher Logsatz für Muster.
- Fix `fe813988`: `POST /admin/rules/preview`, Seite schickt JSON-Body; Logsatz je Liste. PHPUnit 789 auf 791, neues Gate `scan_rules_routes` mit Selbsttest, Gegenprobe mit dem alten Stand 2 rot. PHP-Baumhash `6b4a5994...`, 103 Dateien.
- Live: neue Logzeilen und Access-Log ohne `Archiv`, `*.key`, `node_modules` (Positivkontrolle `befund-log-url.txt` vom alten Stand); alte GET-Adresse 405.

## Gates

pytest 5682 passed, 159 skipped (16:48 min); ruff check und format (222); pyright 0 Fehler (latest); vulture leer; reuse 2730/2730; `node --check php/js/admin.js`; `php -l` (php:8.3-cli) für alle geänderten PHP-Dateien.

## CI

- `8e00d401` (Zwischenstand): Security scans 38535831635, OpenSSF Scorecard 38535831622, beide grün.
- `fe813988` (Fix), alle grün mit `gh run watch --exit-status`: PHP and store metadata gates 38542497810 (791 Tests, 2976 Assertions), Python gates 38542497613 (5693 passed), Security scans 38542497846, OpenSSF Scorecard 38542497926, Resilience 38542497538, Multi-arch image 38542497556, Integration 38542497748, HaRP deploy 38542497788.
- docs-Commit dieses Abschlusses: siehe Abschlussmeldung.

## Deviations from Plan

### Auto-fixed Issues

Keine stillen Fixes. L-33-09-01 wurde gemeldet, der Lauf hielt an, der Fix folgte dem Owner-Entscheid (Option 1) als eigener Commit `fe813988`.

### Weitere Abweichungen

1. **Anhalten und Fortsetzung:** Task 1 hielt um 10:31 am Befund an; Fortsetzung nach dem Owner-Entscheid in derselben Ausführung.
2. **Registrierskript ersetzte den Gegenprobe-Prozess** (Routenprobe `^/status$` 404, Neustart des Hauptbaums ohne Variablen um 11:46:23). Der Abgleich der Gegenprobe war um 11:46:10 schon fertig; für die folgenden Läufe wurde der Prozess vorher beendet.
3. **Routen-Cache (APCu):** Nach dem Wechsel auf POST antwortete die Instanz 405, bis der Container `findling-nextcloud` neu gestartet war.
4. **OCR aus für Weg C** (`FINDLING_OCR_ENABLED=false`), dadurch auch die Bilder mit `no_text_layer` statt `image_not_ocrable`.
5. **Gegenprobe-Start von Hand** mit dem Python des Hauptbaums und `PYTHONPATH` auf den Worktree (gleicher Speicher und gleiches Geheimnis), weil das Skript im Worktree einen eigenen leeren Speicher `.dev/storage` des Worktrees genommen hätte.
6. **Testuser-Zugang** über ein App-Passwort (`occ user:auth-tokens:add`), am Ende gelöscht.
7. **`exclusion_patterns` am Ende gelöscht** statt `[]` gespeichert, damit der Zustand dem vor dem Plan gleicht; liest sich als leere Liste.
8. **Wartezeiten** ereignisgetrieben über `tail -f | grep -m1` auf Backend- und Access-Log; zweimal ein kurzes `timeout 2 tail -f` beim Stoppen eines Prozesses bzw. Container-Neustart.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-33-27 (Positivkontrolle, Kontrolle, Gegenfall, Gegenprobe vor 33-03), T-33-28 (Logprobe mit Marker; Befund L-33-09-01 gefixt, Nachweis ohne Regelwerte in nextcloud.log und Access-Log), T-33-29 (Endzustand per occ, SQL und PROPFIND, Worktree entfernt) umgesetzt. Die Vorschau bleibt eine Route, die nichts schreibt; der Verbwechsel ändert nur, wo die Werte reisen.

## Self-Check: PASSED

- FOUND: 33-09-NACHWEIS.md, 33-09-SUMMARY.md, SettingsController.php (POST-Vorschau)
- FOUND: 8e00d401, fe813988
- `git worktree list` ohne abnahme33
