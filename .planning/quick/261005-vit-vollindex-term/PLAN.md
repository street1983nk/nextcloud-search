---
quick: 261005-vit
title: Vollindex-Term (6 KiB je indexierter Datei im Hauptprozess)
created: 2026-10-05
type: tdd
files_modified:
  - backend/src/findling/config.py
  - backend/src/findling/profile.py
  - backend/tests/test_config.py
  - backend/tests/test_profile.py
  - backend/tests/test_measurement_scripts.py
  - docs/profiles.md
---

# Quick 261005-vit: Vollindex-Term

## Owner-Signal

Owner-Entscheid vom 05.10.2026 per Auswahlfrage, wörtlich: "6 KiB, ohne Messung".
Die Speicherrechnung bekommt einen Posten von 6 KiB je indexierter Datei im
Hauptprozess, ohne weitere Box-Messung (keine Zerlegungsmessung als Vorstufe).

## Begründung

Vorlage: `.planning/phases/28-abnahme-anfahrt/28-12-SUMMARY.md`, Abschnitt
"Vorlage Vollindex-Term".

- S-voll (m7g.large, Sparsam, 1 Slot, 52.137 Dateien): anon-Spitze 1.788,9 MiB
  gegen Rechnung 1.507,5 MiB (Slotwert 250 MiB), Grenze 1.658,3 MiB, es fehlen
  118,8 MiB. Die Zelle ist heute "nicht getragen".
- Zwischen 5.000 (S-T) und 52.137 Dateien (S-voll) wächst der Hauptprozess um
  279,5 MiB, rund 6 KiB je Datei (zwei Datenpunkte, gleiche Box, gleiche Stufe).
- 6 KiB statt 2,4 KiB: der Index wächst nach der Messung weiter, 2,4 KiB
  schöpft die Toleranz schon bei 52.137 Dateien voll aus.

## Soll

1. `config.py`: `MAIN_PROCESS_PER_FILE_BYTES = 6 * 1024` (6.144 Byte), Kommentar
   mit Messordner, den zwei Datenpunkten und dem Owner-Datum.
2. `profile.py`:
   - `main_process_bytes(index_files, *, weights)`: Grundlinie plus
     `index_files x MAIN_PROCESS_PER_FILE_BYTES` (plus fp32-Mehrbedarf), der
     Hauptprozess-Anteil der dokumentierten Rechnung.
   - `_memory_term` und `ocr_slots` nehmen `index_files` (Standard 0) und ziehen
     den Posten vom Speicherterm ab.
   - Laufzeit-Verdrahtung der Dateizahl in den Snapshot ist NICHT Teil dieses
     Auftrags: alle laufenden Slotzahlen bleiben unverändert (Sparsam hat ohnehin
     keinen Speicherterm; Probe und Wächter lesen den freien Speicher live).
3. Tests (TDD, erst rot):
   - Pin der Konstante in `test_config.py`.
   - `test_profile.py`: S-voll-Rechnung mit Term bei 52.137 Dateien trägt die
     anon-Spitze 1.788,9 MiB (anon <= 1,10 x Rechnung), ohne Term nicht;
     Speicherterm mit 0, 5.000 und 52.137 Dateien; Slotzahlen ohne Dateizahl
     unverändert; Sparsam unberührt.
4. Baumhash-Pin in `test_measurement_scripts.py` fortschreiben
   (`PACKAGE_FILES_TODAY` bleibt 71).
5. `docs/profiles.md`: ein kurzer Punkt im Abschnitt Formel (eine Datei, kein
   Umschreiben des 28-11-Kapitels).

## Grenzen

- Nicht angefasst: `docs/measurements/2026-10-abnahme-anfahrt/` (paralleler
  28-13-Executor, auch `skripte/12-slotkosten.py`), STATE.md, ROADMAP.md.
- Kein Push.

## Gates

ruff check + format --check, pyright basic (PYRIGHT_PYTHON_FORCE_VERSION=latest),
vulture, volle pytest-Suite via uv, alles lokal grün vor jedem Commit.
