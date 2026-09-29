---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 15
subsystem: docs, measurements, php-admin
tags: [live, harness, owner-abnahme, sc3]
requires: ["27-11", "27-12", "27-13", "27-14"]
provides:
  - "docs/measurements/2026-09-probe-live/ mit README und raw/"
  - "Owner-Abnahme der Fläche Leistungsprofil"
affects: [docs/measurements/2026-09-probe-live/, php/lib/Service/AdminViewService.php, php/templates/admin.php, php/js/admin.js]
tech-stack:
  added: []
  patterns: ["Verdikte per docker update --memory erzwungen, ohne Produktschalter"]
key-files:
  created: [docs/measurements/2026-09-probe-live/README.md, docs/measurements/2026-09-probe-live/raw/]
  modified: [php/lib/Service/AdminViewService.php, php/templates/admin.php, php/js/admin.js, backend/tests/test_admin_ui_contract.py]
decisions:
  - "Auswahlfeld wird aus dem gespeicherten appconfig-Wert (profileSaved) vorbelegt, nicht aus profile.chosen des Containers"
  - "Deckungsgrad-Nenner (files_seen) ist Altfehler v1.0 und läuft als eigener Quick-Fix, nicht in 27-15"
metrics:
  duration: "ca. 1 Tag inkl. Abnahme"
  completed: 2026-09-29
requirements: [PRUEF-01, UI-01]
---

# Phase 27 Plan 15: Live-Lauf und Owner-Abnahme Summary

Probe und Block "Leistungsprofil" live auf dem HaRP-Harness belegt (fits, narrow, nofit, busy, Abwärtsweg, Nicht-Admin 403) und vom Owner per Playwright abgenommen; ein Vorbelegungsfehler des Auswahlfelds wurde dabei gefunden und behoben.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Live-Lauf auf dem HaRP-Harness und Ablage | f787ecc8 | docs/measurements/2026-09-probe-live/ |
| 2 | Owner-Abnahme | 9d6a11c3 (Befund-Fix), dieser Commit (Doku) | php/lib/Service/AdminViewService.php, php/templates/admin.php, php/js/admin.js, backend/tests/test_admin_ui_contract.py, README |

## Owner-Signal

Wörtlich, 29.09.2026: "approved"

## Abnahme (Playwright, http://localhost:8096/settings/admin/findling)

- Block Leistungsprofil vor Regeln und Grenzen, drei Profile
- fp32-Häkchen nur bei Standard und Leistung, Größenangabe 448,5 MB
- Knöpfe "Übernehmen und prüfen" und "Bei Sparsam bleiben", kein Erweitert-Bereich; "Übernehmen und prüfen" gesperrt ohne Änderung
- Standard/int8: Fortschrittszeile "Prüfung läuft: OCR mit einem Slot", Hinweis Indexierung pausiert, Verdikt Passt, gespeichert (occ profile=standard), aria-live-Ansage, Fokus auf der Verdikt-Karte, Karte bleibt nach Neuladen
- Abwärtsweg auf Sparsam: Knopf "Übernehmen", speichert ohne Probe (occ profile=economy)
- Einzige Konsolenfehler von Nextcloud user_status (404), nicht von Findling

## Befunde

1. **Vorbelegung des Auswahlfelds (behoben, 9d6a11c3):** Auswahl kam aus `profile.chosen` des Containers, das eine Runde nachhängt, statt aus dem gespeicherten Wert. Fix: `profileSaved` aus appconfig in AdminViewService, Template und admin.js, Vertragstest ergänzt. Live bestätigt: economy gespeichert, Container noch standard, Auswahl zeigt Sparsam, keine Konsolenfehler.
2. **Harness-Hinweis, kein Produktfehler:** opcache `revalidate_freq` 60 s und der `?v=`-Cache von admin.js verzögerten die Sichtbarkeit des Fixes; im Release wechselt die Version.
3. **Getrennter Altfehler v1.0 (nicht Teil von 27-15, eigener Quick-Fix folgt):** Deckungsgrad zeigte "607 von 587", weil der Nenner `files_seen` nur beim einmaligen Crawl entsteht und nach Ereignis-Indexierung nicht mitwächst.

## Deviations from Plan

- **[Rule 1 - Bug] Vorbelegung aus profileSaved:** während der gemeinsamen Abnahme gefunden und dort behoben statt als eigener Gap-Plan (Commit 9d6a11c3).

## Lücken

- fp32 nicht live gefahren (470268510 Bytes Download plus Neuberechnung aller Vektoren), im README vermerkt
- Harness läuft weiter für die nächste Live-Prüfung

## Self-Check: PASSED

- docs/measurements/2026-09-probe-live/README.md vorhanden, Abschnitt "Owner-Abnahme 29.09." ergänzt
- Commits f787ecc8 und 9d6a11c3 in der Historie von main
