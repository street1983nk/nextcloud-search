---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 07
subsystem: docs, ci (deploy-harp)
tags: [issue-37, backup-pause, docs, ci]
requires:
  - 41-04 (/status pause, pausedSince, WAL-Checkpoint)
  - 41-05 (occ findling:pause --wait, findling:resume)
  - 41-06 (Overview-Feld pause, Schalter, docs/admin-page.md)
provides:
  - docs/backup.md, docs/backup.en.md, docs/backup.fr.md
  - README-Links je Sprache (Abschnitt Datenschutz)
  - backend/tests/test_backup_docs.py (Doku-Gate, 46 Fälle)
  - Schritt "Backup pause, across restarts of the backend and of Nextcloud" in deploy-harp.yml
affects:
  - 41-08 (Push, grüner Kopf, Log-Zitate des neuen Schritts)
  - 41-10 (Owner-Runde sieht die Doku-Texte)
key-files:
  created:
    - docs/backup.md
    - docs/backup.en.md
    - docs/backup.fr.md
    - backend/tests/test_backup_docs.py
  modified:
    - README.md
    - README.en.md
    - README.fr.md
    - docs/admin-page.md
    - .github/workflows/deploy-harp.yml
decisions:
  - "README-Link im Abschnitt Datenschutz statt neben dem migrate-Link: test_migration_path sperrt den Umstiegsabschnitt auf genau einen Satz"
  - "Wiederherstellen: zurückgespieltes Volume folgt dem aktuellen Schalterstand (statt 'startet nie pausiert'), weil der Wunsch in appconfig liegt"
  - "Nextcloud-Neustart im CI = Neustart des PHP-Builtin-Servers (setup-test-nc), Nextcloud läuft dort nicht als Container"
  - "Neuer CI-Schritt nur auf stable34 / ubuntu-24.04, Trap ruft bei jedem Ende findling:resume"
metrics:
  duration: "ca. 45 min"
  completed: 2026-11-04
  tasks: 2
  commits: 2
---

# Phase 41 Plan 07: Backup-Doku und CI-Beweis der Pause Summary

Backup-Doku DE/EN/FR (Weg A docker stop, Weg B occ findling:pause --wait, Wiederherstellen) mit Doku-Gate, plus ein HaRP-Schritt mit neun Zusicherungen über Pause, WAL, Suche, Container- und Nextcloud-Neustart und Resume; CI-Beleg steht bis zum Push in 41-08 aus.

## Commits

| Hash | Nachricht |
|------|-----------|
| 7f1f0207 | docs(41-07): how to back up findling, in three languages (#37) |
| 47b34369 | ci(41-07): prove the backup pause across restarts on a real instance (#37) |

Autor street1983nk <k.cherif@outlook.de>, ohne Trailer, kein Push (Orchestrator-Vorgabe).

## Task 1: Doku

- Fakten: appconfig, Volume-Inhalt (state.db, vectors.db, Index), neu aufbaubar, Klartext-Warnung (unverschlüsselt / unencrypted / non chiffré), Weg A, Weg B mit "erst bei pausiert", ~30 min bei OCR, Neustart-Festigkeit, Crawl-Jobs laufen weiter, Neuaufbau mit zwei Index-Verzeichnissen, Wiederherstellen.
- EN enthält wörtlich "indexing stops and everything is flushed to disk while search keeps working" (D-41-06).
- Länge (wc -l): backup.md 52 vs. migrate 102; backup.en.md 50 vs. 100; backup.fr.md 52 vs. 107.
- docs/admin-page.md: Backtick-Verweis jetzt echter Link [backup.md](backup.md).
- Gates: test_backup_docs 46 grün, README-/Doku-Tests 1818 grün, ruff, ruff format, pyright (0 errors), vulture grün.

## Task 2: CI-Schritt

- `::error::`-Zählung in deploy-harp.yml: vorher 232, nachher 249.
- actionlint (Docker, v1.7.12 inkl. shellcheck): keine Meldung im neuen Schritt; die 9 Meldungen betreffen vorhandene Schritte (info/style).
- Workflow-Gates (17 Testdateien, 1594 Tests) grün, Datei bleibt reines ASCII.
- **CI-Beweis ausstehend:** Push, head_green.sh, Lauf-IDs, Log-Zitate ("Paused.", WAL-Größen, Zustand nach beiden Neustarts, running nach resume), A1-Bestätigung und PHPUnit-Summe aus "PHP and store metadata gates" folgen in 41-08. Lokal: PHPUnit 958 OK auf HEAD 28868890 (Orchestrator).

## Deviations from Plan

1. **[Rule 3] README-Link nicht neben dem migrate-Link.** test_migration_path::test_readme_sections_link_the_page_of_their_language verlangt im Umstiegsabschnitt genau den einen Satz. Link steht im Abschnitt Datenschutz/Privacy/Confidentialité (thematisch Backup). Commit 7f1f0207.
2. **[Rule 1] Wiederherstellen-Satz korrigiert.** Plan: "startet nie pausiert". Der Wunsch liegt in appconfig; steht er noch auf pausiert, startet das Backend pausiert. Doku sagt: folgt dem aktuellen Schalterstand, nach Weg B resume nicht vergessen.
3. **[Rule 3] Nextcloud-Neustart.** Im HaRP-Job läuft Nextcloud als `php -S` (setup-test-nc), nicht als Container; Zusicherung (7) startet diesen Prozess neu (pkill + composer run serve), Begründung im Kommentar.
4. **Kein Push** (Orchestrator-Vorgabe statt Plan-Schritt); CI-Teil von Task 2 wandert nach 41-08.
5. Probe-Dateien heißen backup-probe-before/during.txt, der Suchbegriff steht nur im Inhalt, damit kein Dateinamen-Treffer die Zusicherung (8) verfälscht.

## Known Stubs

Keine.

## Threat Flags

Keine neuen; T-41-29 (Klartext-Satz, Gate), T-41-30 (erst bei paused, WAL-Prüfung), T-41-31 (A1 im CI) umgesetzt.

## Self-Check: PASSED

- docs/backup.md, docs/backup.en.md, docs/backup.fr.md, backend/tests/test_backup_docs.py vorhanden
- Commits 7f1f0207, 47b34369 vorhanden
