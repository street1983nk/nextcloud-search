---
quick: 261005-vit
subsystem: profile
tags: [speicherrechnung, vollindex-term, s-voll, owner-entscheid]
provides: [MAIN_PROCESS_PER_FILE_BYTES, profile.main_process_bytes, index_files in _memory_term/ocr_slots]
key-files:
  modified: [backend/src/findling/config.py, backend/src/findling/profile.py, backend/tests/test_config.py, backend/tests/test_profile.py, backend/tests/test_measurement_scripts.py, docs/profiles.md]
decisions:
  - "6 KiB je Datei nach Owner-Entscheid 05.10.2026 (\"6 KiB, ohne Messung\")"
  - "Keine Laufzeit-Verdrahtung: index_files Standard 0, Slotzahlen unverändert"
metrics: {duration: ~35 min, completed: 2026-10-05, tasks: 3, files: 6}
---
# Quick 261005-vit: Vollindex-Term Summary

Die Speicherrechnung zählt 6 KiB je indexierter Datei im Hauptprozess. S-voll ist damit getragen: 1.788,9 MiB anon gegen 1.813,0 MiB Rechnung, Faktor 0,987. Die Slotzahlen bleiben unverändert.

## Commits
| Schritt | Commit | Inhalt |
|---|---|---|
| Plan | 869106fe | PLAN.md |
| RED | 655cd037 | Pin der Konstante, S-voll-Test, Speicherterm-Tests, Slotzahlen-Gegenprobe |
| GREEN | e3d28dfd | Konstante, main_process_bytes, index_files, Baumhash-Pin |
| Doku | dadaf594 | profiles.md, Abschnitt Formel |

## Verifikation
4436 passed, 25 skipped; ruff, format, pyright latest 0 Fehler, vulture grün; kein Push.

## Deviations from Plan
Keine im Bau; die SUMMARY.md wurde vom Orchestrator nachgetragen, weil das Write-Werkzeug des Executors sie ablehnte.

## Offene Punkte
1. Laufzeit-Verdrahtung (note_index_files) braucht einen Owner-Entscheid.
2. 12-slotkosten.py rechnung kennt den Term noch nicht (Ordner war von 28-13 belegt).
3. Store-RAM-Angabe: etwa +300 MiB je 50.000 Dateien, Freigabe durch den Owner.

## TDD Gate Compliance
RED 655cd037 vor GREEN e3d28dfd.

## Self-Check: PASSED
