---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 14
subsystem: docs, ci
tags: [docs, integration, trust-boundary, sc3]
requires: ["27-07", "27-10", "27-11"]
provides:
  - "docs/admin-page.md Abschnitt Das Leistungsprofil"
  - "integration.yml Schritt: Nicht-Admin erreicht weder Probe noch Profilroute"
affects: [docs/admin-page.md, docs/profiles.md, docs/embeddings.md, .github/workflows/integration.yml]
tech-stack:
  added: []
  patterns: ["Live-Absage per curl mit OCS-APIRequest-Header, damit eine Absage nur der Admin-Check sein kann"]
key-files:
  created: []
  modified: [docs/admin-page.md, docs/profiles.md, docs/embeddings.md, .github/workflows/integration.yml]
decisions:
  - "Nicht-Admin-Schritt nutzt Basic-Auth plus OCS-APIRequest wie der Bestand; CSRF fällt damit als Absagegrund weg"
  - "Erlaubte Absagecodes 401, 403, 302, 303; Gegenprobe GET als admin muss 200 sein"
metrics:
  duration: "ca. 20 min"
  completed: 2026-09-29
requirements: [PRUEF-01, UI-01]
---

# Phase 27 Plan 14: Doku und Live-Nicht-Admin-Schritt Summary

Doku der Phase als Faktenlisten (Block Leistungsprofil, occ als Weg ohne Probe, ehrliche Grenzen) plus ein Integrationsschritt, der SC3 live als Nicht-Admin belegt.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Doku admin-page, profiles, embeddings | c5e62d90 | docs/admin-page.md, docs/profiles.md, docs/embeddings.md |
| 2 | Live-Nicht-Admin-Schritt | 3c150e5f | .github/workflows/integration.yml |

## Inhalt

- admin-page.md: neuer Abschnitt "Das Leistungsprofil" (Auskunft, Formular, Probe mit Schritten und Deckeln 1800/600/120 s, eine Probe gleichzeitig, Verdikte, Abwärtswege, Grenzen, Zugriff). Wächterzeilen: occ-Rückweg durch "Erneut prüfen" ersetzt, Token nicht mehr auf der Seite. "Keinen Erweitert-Bereich" um ADM-04-Satz ergänzt. Zwei "ab Phase 27"-Vorgriffe auf Gegenwart gestellt.
- profiles.md: Adminseite empfohlen, occ als zweiter Weg, überspringt die Probe, dann sichert nur der Wächter (D-27-13); Env nur Einzelwerte (D-27-14); Rückweg per "Erneut prüfen".
- embeddings.md §11: fp32-Download in der Probe, D-27-17, D-27-18, Preis des Modell-Kinds (rund 820 MiB transient gegen 367 MiB im Betrieb), occ ohne Probe.
- integration.yml: drei Aufrufe als testuser (nie 200), Profilschlüssel vorher gleich nachher, Gegenprobe GET als admin 200. LF, Pins unverändert.

## Verifikation

- Greps: Leistungsprofil 6, "überspringt" in profiles.md 1, "profile_confirmed --value" in admin-page.md 0, keine U+2013/U+2014.
- `pytest -k "doc or docs or public_artifacts"`: 238 passed.
- integration.yml: YAML gültig, `admin/profile/check` 6, `test_workflow_pins.py` 14 passed.
- Der CI-Schritt läuft erst nach einem Push wirklich; lokal nur Struktur- und Pin-Tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Doku-Geheimnis-Gate schlug an**
- **Found during:** Task 1
- **Issue:** Die Zeile "**Token:** erscheint ..." traf die Familie `schluesselwort-mit-wert` in `test_public_artifacts.py`.
- **Fix:** Umformuliert zu "**Bestätigung:** Der Token erscheint ...".
- **Commit:** c5e62d90

## Beobachtung außerhalb des Scopes

- `test_probe_run.py::test_a_deep_dip_in_the_n_run_is_narrow` fiel einmal im breiten Lauf (`-k ci`) unter Last, einzeln 54 passed. Vermutlich zeitabhängig; nicht angefasst.

## Self-Check: PASSED

- docs/admin-page.md, docs/profiles.md, docs/embeddings.md, .github/workflows/integration.yml vorhanden
- Commits c5e62d90 und 3c150e5f vorhanden
