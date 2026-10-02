---
phase: quick-261002-cvf
plan: 01
subsystem: measurements
tags: [zaehltor, teilkorpus, 28-07, zaehlmarke, frischzaehlung, tdd]
requires: []
provides:
  - "Zaehlmarke (max updated_at der file_state-Tabelle) unmittelbar vor dem Trigger, nur bei ZELLE_KORPUS=teil"
  - "Zaehltor speist uebersprungen/fehlgeschlagen aus teilkorpus- und zellscharfer Frischzaehlung (updated_at > Marke, Pfad files/teilkorpus/%, Join oc_filecache) statt aus den globalen occ-Zaehlern"
  - "db_lesen() via sudo docker exec psql -At, Zugang aus der Container-Umgebung, kein Passwort auf einer Kommandozeile"
  - "psql-Zweig im Docker-Stub (STUB_ZAEHLMARKE, STUB_FRISCH_SKIPPED/FAILED) plus Lauf-5-Belegtest und Lauf-2-Kalibrierfallen-Test"
affects: [28-07, abnahme-anfahrt, T-28-03, D-28-06]
tech-stack:
  added: []
  patterns:
    - "Zeitscharfe Frischzaehlung: Marke vor dem Trigger, striktes > auf updated_at derselben Boxuhr"
    - "Format-Tor vor SQL-Einsetzung: case-Pattern laesst nur Ziffern, Bindestrich, Doppelpunkt, Punkt, Leerzeichen durch"
    - "group-by-Parser belegt fehlende Staaten auf 0 vor; unlesbarer DB-Stand bleibt unlesbar und scheitert am ist_zahl-Tor"
key-files:
  created: []
  modified:
    - backend/tests/test_v14_zelle.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
decisions:
  - "Zaehlquelle = DB-Frischzaehlung (Kernproblem-Weg 2 + Pfadfilter aus Weg a), reine Harness-Aenderung: occ zaehlt skipped/failed GLOBAL ueber oc_findling_file_state, die --rm-data und --restart ueberlebt; Lauf 5 zaehlte darum 5041 = 5000 Teilkorpus + 41 fremde Altzustaende"
  - "Unlesbare Zaehlmarke ist Abbruch 71 VOR dem Trigger: ohne Marke ist das Tor nicht pruefbar, die Zelle darf nicht messen"
  - "frisch=unlesbar haelt uebersprungen/fehlgeschlagen auf unlesbar statt 0: ein DB-Lesefehler am Tor kann kein Defizit maskieren (bestehender ist_zahl/abbruch-71-Pfad)"
metrics:
  duration: "~25 min"
  completed: "2026-10-02"
---

# Quick 261002-cvf: Zaehltor Teilkorpus-scharfe Zaehlquelle Summary

**One-liner:** Das Zaehltor der Teilkorpus-Zellen liest skipped/failed jetzt zeit- und pfadscharf aus der Datenbank (Zaehlmarke vor dem Trigger, updated_at > Marke, Pfad files/teilkorpus/%) statt aus den globalen occ-Zaehlern; der Lauf-5-Belegtest besteht mit 5000 statt 5041, und die Lauf-2-Kalibrierfalle (Altzaehler fuellen ein echtes Defizit) bleibt Abbruch 71.

## Tasks

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | RED: psql-Stub + Zaehltor-Tests auf Frischzaehlung umgeschrieben | 9a12ad54 (test(quick-261002-cvf)) |
| 2 | GREEN: 10-zelle.sh zaehlt teilkorpus- und zellscharf | a2b0fcf9 (feat(quick-261002-cvf)) |

## RED-Beleg (Diskriminierungsnachweis)

Nach Task 1 (Stub + Tests, 10-zelle.sh noch mit globalen occ-Zaehlern und ohne zaehlmarke) liefen genau die Zaehltor-Tests rot, alle 61 uebrigen Tests gruen:

```
FAILED tests/test_v14_zelle.py::test_cell_teilkorpus_demands_the_count_gate
FAILED tests/test_v14_zelle.py::test_cell_teilkorpus_passes_with_the_counters_of_run_5
FAILED tests/test_v14_zelle.py::test_cell_teilkorpus_old_states_mask_no_real_shortfall
FAILED tests/test_v14_zelle.py::test_cell_teilkorpus_counts_embedded_not_indexed
FAILED tests/test_v14_zelle.py::test_cell_teilkorpus_still_fails_on_a_real_shortfall
5 failed, 2 passed, 61 deselected
```

Die zwei Kernbelege im Wortlaut des RED-Laufs:

- **Lauf-5-Belegtest** (vorrat 3535 = scheduled 3525 + handed 10, eingebettet 1465, globale Altzaehler skipped 35 + failed 6): alte Formel summiert exakt die 5041 des echten Abbruchs auf m7g.large:
  ```
  E       AssertionError: CompletedProcess(... Zaehltor 5000 ist verfehlt (5041) ...)
  E       assert 71 == 0
  ```
- **Lauf-2-Kalibrierfalle** (wie oben, aber eingebettet 1424, echtes Defizit 41): alte Formel laesst die 41 Altzustaende die Luecke exakt fuellen, die Zelle laeuft faelschlich bis `10-ZELLE-FERTIG` durch:
  ```
  E       assert 0 == 71
  ```

Nach Task 2 (GREEN): Belegtest besteht mit `zaehltor bestanden 5000` und `summe 5000` in der zaehlung-Zeile plus einer `zaehlmarke `-Zeile im Protokoll; die Kalibrierfalle endet mit `zaehltor verfehlt 4959 statt 5000`, Abbruch 71, Schritt ende nicht erreicht.

## Verifikation

- `uv run pytest tests/test_v14_zelle.py tests/test_measurement_scripts.py` (im backend/, PYTHONUTF8=1): **545 passed** (inkl. der 2 neuen Belegtests und aller umgebauten Zaehltor-Tests)
- `uv run ruff check tests/test_v14_zelle.py`: All checks passed; `ruff format --check`: 1 file already formatted
- `sh -n docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh`: sauber
- 10-zelle.sh: 0 CR-Bytes (grep-Zaehlung exit 1 bei 0 Treffern); Testdatei im Index LF (`i/lf`, CRLF nur Working-Tree via autocrlf); keine Em-/En-Dashes in beiden Dateien (Python-Codepoint-Pruefung U+2013/U+2014)
- `grep -n zaehlmarke 10-zelle.sh`: Treffer im Kopfkommentar (Zeilen 48, 98) und im trigger-Block (563, 565)
- Format-Tor der Marke vorab in der Test-Shell (Git Bash sh) positiv- und negativ-geprueft: `2026-10-01 00:00:00` und `...00.123` ok; leer, `unlesbar`, `; drop table x`, `T`-Trennzeichen abgelehnt
- php/ und docs/measurements/2026-10-abnahme-anfahrt/skripte/01-teilkorpus.py woertlich unveraendert (git diff leer); Vollkorpus-Pfad ruft db_lesen nie (Assert `kein psql in bench.calls()` im Voll-Test)
- 2 lokale Commits, Autor street1983nk <k.cherif@outlook.de>, keine Trailer, NICHT gepusht
- "DIESE FASSUNG IST NICHT GEFAHREN" steht weiter im Kopf von 10-zelle.sh

## Deviations from Plan

None - plan executed exactly as written. (Einzige Auslegung: bei `frisch=unlesbar` werden uebersprungen/fehlgeschlagen auf unlesbar statt 0 gesetzt, damit ein DB-Lesefehler kein Defizit maskiert; das folgt dem Plan-Satz "ist_zahl-Pruefung wie gehabt: nicht-numerisch ergibt summe unlesbar, abbruch 71" und verschaerft nur die 0-Vorbelegung auf den Erfolgsfall der Query.)

## Known Stubs

Keine neuen Stubs im Produktionspfad. Der psql-Zweig im Docker-Stub ist ein absichtlicher Harness-Stand-in im bestehenden Muster der Datei (STUB_DOCKER).

## Self-Check: PASSED

- backend/tests/test_v14_zelle.py: FOUND
- docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh: FOUND
- Commit 9a12ad54: FOUND
- Commit a2b0fcf9: FOUND
