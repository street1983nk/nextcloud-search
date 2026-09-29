---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 10
subsystem: php-companion
tags: [php, template, css, admin-ui, profile, probe, security]
requires: [27-01, 27-08]
provides:
  - Block #findling-profile im Admin-Template mit allen IDs der UI-SPEC plus Unter-IDs für das Skript
  - CSS .findling-profile__facts/__actions/__env, .findling-banner--info, Chips --fits/--narrow/--nofit
  - Template-Gates für SC1, ADM-04, D-27-11, D-27-12, D-27-14
affects: [27-12, 27-13]
tech-stack:
  added: []
  patterns: [alle Zustände im Markup mit hidden, PHP-Maps auf Katalogsätze, Marker-Schnitt für code-Element]
key-files:
  created: []
  modified:
    - php/templates/admin.php
    - php/css/admin.css
    - backend/tests/test_admin_ui_contract.py
    - THIRD-PARTY.md
decisions:
  - "Drei option-Elemente und drei Beschreibungszeilen literal ausgeschrieben statt per Schleife, damit das SC1-Gate sie direkt liest"
  - "Primärknopf trägt beide Beschriftungen als data-label-check / data-label-apply, das Skript tauscht nur den Textknoten"
  - "Schritte download und ocr_n brauchen Zahlen, die nur die Probe-Route kennt; serverseitig steht dann 'Check running.' bis zum ersten Probe-Poll"
  - "Probe-Knöpfe serverseitig disabled bei unerreichbarem Backend (Z14), fehlender Probe-Route (Z15), laufendem Umbau (Z16a) oder laufender Probe; die Fehlerzeile nennt den Grund schon beim Rendern"
  - "Variablenname der Env-Zeilen kommt aus einer Template-Map nach Feldschlüssel, das variable-Feld der Overview wird nicht ausgegeben"
metrics:
  duration: ca. 45 min
  completed: 2026-09-29
  tasks: 2
  files: 4
---

# Phase 27 Plan 10: Block Leistungsprofil im Admin-Template Summary

Der Block "Performance profile" steht direkt vor den Regeln: ein Auswahlfeld mit genau drei Profilen, das fp32-Häkchen nur bei Standard und Leistung, Hinweisflächen für Hardware, Vorschlag, Wirksam, Schrumpfung, Wächter mit "Check again", Präzision, Env-Überstimmung und Reindex; die letzte Verdikt-Karte wird serverseitig aus profileCheck gerendert. Die occ-Rückwegzeile samt Token ist weg.

## Erledigt

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Way-back-Variablen und #findling-guard-way-back entfernt; Block #findling-profile mit Maps $stepNames, $verdictNames, $probeCauseNames (13 Ursachen, Zahlen über $count/$size/$span, Zeile verborgen bei fehlendem Zahlwert), $precisionSentences, $envLines (Marker-Schnitt), $profileDescriptions; Verdikt-Karte mit drei Icons, Geprüft-Zeile, Folge, D-27-17-Satz, Angebotsknöpfen; Stylesheet ergänzt; THIRD-PARTY.md um close-circle-outline | 2d61c0a8 |
| 2 | Wächter-Gate: Abwesenheit von Element, Variablen und Satz; Token-Gate um Template erweitert; sieben neue Tests (drei Profile, kein Erweitert-Bereich, alle IDs, Stay on Economy, Verdikt-Karte ohne Live-Region, feste Env-Namen, Slot-Deckel gleich config.py); Template-Optionen literal | 66d94b63 |

## Verifikation

- `php -l templates/admin.php` in php:8.3-cli (Docker): keine Syntaxfehler
- Wegwerf-Render-Smoke in Docker mit Stubs für p(), $l und OCP (danach gelöscht): drei Szenarien (Erstaufruf mit Vorschlag Standard und Nofit-Verdikt, leere Overview, laufende Probe) ohne Warnung gerendert, Zustände wie erwartet (Z2 vorbelegt, Z10-Banner, Z12, Z14/Z15-Fehlerzeile, Z6 alles disabled und Karte verborgen)
- Acceptance-Greps: `id="findling-profile"` 1 und vor `id="findling-rules"`; way-back/wayBackCommand/guardToken/"To lift the reduction" 0; jede Contract-ID genau einmal; `#findling-profile` in admin.css 5-mal; Farbliterale 0 wie vorher
- `uv run pytest -q tests/test_admin_ui_contract.py`: 71 passed; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber
- PHPUnit: lokal nicht ausführbar, läuft in CI (php.yml); dieser Plan ändert keine PHP-Klasse
- Baumhash-Pin in test_measurement_scripts.py bewusst nicht angefasst (PHP-Baum geändert, Orchestrator misst nach dem Merge)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Lizenz] THIRD-PARTY.md um das dreizehnte Icon ergänzt**
- **Found during:** Task 1
- **Issue:** close-circle-outline (Chip "Does not fit") ist neu im Template, die Attribution nannte zwölf Icons und das Prüfrezept hätte nicht mehr gestimmt
- **Fix:** Name in Liste und Rezept, Anzahl zwölf zu dreizehn, admin.php trägt neun; Pfad byte-gleich aus dem gepinnten Commit 9e04201d geholt
- **Commit:** 2d61c0a8

**2. [Rule 3] Optionen und Beschreibungen literal statt Schleife**
- **Found during:** Task 2
- **Issue:** Das Gate "genau drei option mit den Werten ..." und "jede ID genau einmal" konnte eine foreach-Schleife nicht zählen
- **Fix:** drei option- und drei describe-Zeilen ausgeschrieben, Beschriftung über $profileOption
- **Commit:** 66d94b63

**3. Zusätzliche Unter-IDs** für das Skript aus 27-12 (hardware-unknown, guard-text, recheck, fp32-row, reindex-long/-short, env-<feld>, progress-text, verdict-empty/-chip/-icon-*/-word/-checked/-cause/-saved/-kept/-deleted, offer-check, offer-stay). Die Contract-IDs bleiben je einmal.

**4. Zusätzlicher Test** test_the_slot_caps_of_the_descriptions_are_the_caps_of_the_profiles hält die Zahlen 4 und 16 der Beschreibungen gleich PROFILE_*_OCR_SLOTS_MAX.

## Hinweise für Folgepläne

- **27-13 (Kataloge):** neuer Schlüssel `Check running.` (UI-SPEC nennt die Kurzform "nur Check running" ohne eigenen Satz); dazu alle Sätze der UI-SPEC-Tabellen. Der Katalogschlüssel "To lift the reduction after checking the memory: %1$s" wird nicht mehr gelesen und ist in allen 16 Dateien zu löschen; das Wächter-Gate verlangt ihn nicht mehr.
- **precisionVerdict:** Das Template liest `$backend['precisionVerdict']` gegen die fünf Codes, AdminViewService::backend() liefert das Feld aber noch nicht (liest nur precisionActive und reembedRunning). Bis ein Plan es ergänzt, bleibt #findling-profile-precision verborgen (Z13). Nicht im files_modified dieses Plans, daher nicht geändert.
- **27-12 (Skript):** Schritt download und ocr_n, Z16-Satz "A check is already running..." und die Rückmeldungen schreibt das Skript aus seinen eigenen Maps in die vorhandenen Elemente.

## Known Stubs

- #findling-profile-precision bleibt verborgen, solange die Overview precisionVerdict nicht liefert (siehe oben).
- #findling-profile-reindex, -feedback sind serverseitig immer verborgen bzw. leer; sie werden erst durch Formularänderungen im Skript (27-12) relevant, so vorgesehen.

## Threat Flags

Keine neue Oberfläche außerhalb des Threat-Modells. T-27-31 (nur Katalogsätze über Maps, nur p()), T-27-32 (Token und occ-Zeile weg, Gate) und T-27-33 (ein select, drei option, eine Checkbox, kein details/summary, Gate) umgesetzt.

## Self-Check: PASSED

- php/templates/admin.php, php/css/admin.css, backend/tests/test_admin_ui_contract.py, THIRD-PARTY.md geändert
- Commits 2d61c0a8 und 66d94b63 im Log
