---
phase: quick-261001-vl0
plan: 01
subsystem: measurements
tags: [zaehltor, teilkorpus, 28-07, leserace, tdd]
requires: []
provides:
  - "Zaehltor in 10-zelle.sh rechnet summe = vorrat + uebersprungen + fehlgeschlagen + eingebettet"
  - "Stabilisierte embedded-Lesung (vor/nach bestand_lesen, max. 6 Versuche, sonst zaehlung-instabil)"
  - "Drei diskriminierende Zaehltor-Tests mit den echten Abbruch-71-Zaehlerstaenden"
affects: [28-07, abnahme-anfahrt]
tech-stack:
  added: []
  patterns:
    - "Doppellesung vor/nach einer zweiten Quelle, nur bei Gleichheit gewertet (Leserace-Schutz)"
    - "Stub simuliert Arbeitsablauf ueber Trigger-Marke und Lesungszaehler in STUB_STATE"
key-files:
  created: []
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
    - backend/tests/test_v14_zelle.py
decisions:
  - "Zaehlformel auf eingebettet (embedded) statt indexiert: der Vorrat sinkt im Takt von embedded, eine Index-Fertigstellung ist vorratsneutral, indexiert steckt also doppelt in der alten Summe"
  - "Instabile Lesung faellt sicher: eingebettet=unlesbar haelt summe=unlesbar, 01-teilkorpus.py liefert bei Nicht-Zahl Status != 0, abbruch 71 wie gehabt"
metrics:
  duration: "~35 min"
  completed: "2026-10-01"
---

# Quick 261001-vl0: Findling 28-07 Zaehltor-Fix (Formel auf eingebettet) Summary

**One-liner:** Zaehltor in 10-zelle.sh summiert jetzt eingebettet statt indexiert (eliminiert die 1937 Doppeltzaehlungen des Abbruchs 71) und wertet embedded nur bei stabiler Doppellesung; drei neue Tests mit den echten Abbruch-Zaehlerstaenden belegen Fix, Fehlmengen-Erkennung und Race-Abbruch.

## Tasks

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | Harness erweitern + drei diskriminierende Tests (RED) | e23cd72b (test(28-07)) |
| 2 | Zaehlformel auf eingebettet, Lesung stabilisiert (GREEN) | 6d114659 (fix(28-07)) |
| 3 | Qualitaetsgate + Commits (test dann fix, kein Push) | in 1+2 enthalten |

## RED-Beleg (Diskriminierungsnachweis)

Der Beleg-Test `test_cell_teilkorpus_counts_embedded_not_indexed` lief VOR dem Formel-Fix nachweislich rot. Terminal-Ausgabe des RED-Laufs (alte Formel, echte Abbruch-71-Zaehler scheduled 3518, handed 10, skipped 35, failed 6, indexed 3368, embedded 1431):

```
>       assert answer.returncode == 0, answer
E       AssertionError: CompletedProcess(... Zaehltor 5000 ist verfehlt (6937) ...)
E        +  where 71 = CompletedProcess(..., stderr='10-zelle: das Zaehltor 5000 ist verfehlt (6937)\n').returncode
FAILED tests/test_v14_zelle.py::test_cell_teilkorpus_counts_embedded_not_indexed
3 failed, 2 passed, 59 deselected
```

Die alte Formel reproduzierte exakt die 6937 des echten Abbruchs 71 (rc 71 statt 0); die beiden Alt-Teilkorpus-Tests blieben dabei gruen. Nach dem Fix: Beleg-Test gruen mit "zaehltor bestanden 5000".

## Verifikation

- `python -m pytest backend/tests/test_v14_zelle.py` (via uv, venv-Python, PYTHONUTF8=1): **64 passed** (inkl. der 3 neuen Tests, beide Alt-Teilkorpus-Tests unveraendert gruen)
- `ruff check backend/tests/test_v14_zelle.py`: All checks passed
- `ruff format --check`: 1 file already formatted
- 10-zelle.sh: 0 CR-Bytes (Python-Byte-Zaehlung mit Positivkontrolle), `.gitattributes` erzwingt `*.sh eol=lf`; Testdatei im Index LF (`i/lf`, CRLF nur Working-Tree via autocrlf)
- Keine Em-/En-Dashes in beiden Dateien
- `set -eu` in 10-zelle.sh unveraendert; Schritt ende (ab "schritt ende") unveraendert
- 2 lokale Commits, Autor street1983nk <k.cherif@outlook.de>, keine Trailer, NICHT gepusht

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug im Testdesign] Beleg-Test erreichte rc 0 nicht: Zelle hing nach bestandenem Tor im Schritt ende**
- **Found during:** Task 2 (GREEN-Lauf: 63 passed, Beleg-Test failed nach Haengen in der ende-Schleife)
- **Issue:** Der Plan sah statische Stub-Zaehler vor. Mit vorrat 3528 und indexed 3368 != embedded 1431 erfuellt der Schritt ende (vorrat 0 UND indexed == embedded, zweimal) sein Kriterium nie; der Beleg-Test konnte den vom Plan geforderten returncode 0 nicht erreichen.
- **Fix:** Stub simuliert den echten Arbeitsablauf zustandsbehaftet: `findling:index --restart -n` setzt eine Trigger-Marke in `$STUB_STATE/getriggert`; `findling:index` liefert den Vorrat (STUB_SCHEDULED/STUB_HANDED) nur fuer die erste Lesung nach dem Trigger, danach 0; die uebersicht liefert ab der zweiten Lesung embedded = STUB_INDEXED (Arbeit abgelaufen). Die 93b-Nullstand-Lesung vor dem Trigger bleibt unberuehrt (keine Marke, Vorrat 0 wie bisher). Wackel-Mechanik hat Vorrang vor der Ablauf-Simulation.
- **Files modified:** backend/tests/test_v14_zelle.py (nur Stub-Logik, im test-Commit enthalten)
- **Commit:** e23cd72b

## Known Stubs

Keine neuen Stubs im Produktionspfad. Die Test-Stubs (Docker/occ/uebersicht) sind absichtliche Harness-Stand-ins im bestehenden Muster der Datei.

## Self-Check: PASSED

- backend/tests/test_v14_zelle.py: FOUND
- docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh: FOUND
- Commit e23cd72b: FOUND
- Commit 6d114659: FOUND
