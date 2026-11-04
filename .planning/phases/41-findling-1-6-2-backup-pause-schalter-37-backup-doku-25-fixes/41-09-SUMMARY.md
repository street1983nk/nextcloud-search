---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 09
subsystem: audit (pause, reconcile, status, php admin)
tags: [audit, 1.6.2, backup-pause, security, performance]
requires:
  - 41-08 (Code-Kopf 738a1373, CI grün)
provides:
  - 41-AUDIT.md mit audited_head 738a13731f6448aa97f0a752d5553c6c54db3e85
  - backend/tests/test_phase41_audit.py (24 Proben P bis V)
  - deferred-items.md: vier LOW für v1.7 bzw. Owner-Runde
affects:
  - 41-10 (Owner-Runde: drei Owner-LOW)
  - 41-11 (Tag nur, wenn audited_head..Tag-Kopf über die Code-Pfade leer)
key-files:
  created:
    - backend/tests/test_phase41_audit.py
    - .planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-AUDIT.md
  modified:
    - .planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/deferred-items.md
decisions:
  - "0 CRIT / 0 HIGH / 0 MEDIUM / 4 LOW / 4 INFO über v1.6.1..738a1373; kein Fix, audited_head = Code-Kopf"
  - "Offene Frage aus 41-08 (Container ohne Companion still auf unknown, keine D-17-Zeile) = F-41A-03 LOW, Owner-Punkt 41-10"
  - "LOW-Proben pinnen das heutige Verhalten und werden mit dem Fix rot"
metrics:
  duration: "ca. 2 h 30 min"
  completed: 2026-11-04
  tasks: 2
  commits: 4
---

# Phase 41 Plan 09: Audit 1.6.2 Summary

Audit des ganzen Code-Deltas v1.6.1..738a1373 (46 Dateien, +2523/-253) mit 24 gefahrenen Proben und PHPUnit am Kopf: 0 CRIT, 0 HIGH, 0 MEDIUM, 4 LOW, 4 INFO; in "paused" ändert sich kein Byte des Volumes, solange der Container läuft.

## Commits

| Hash | Nachricht |
|------|-----------|
| 4e369f55 | test(41-09): probes of the 1.6.2 delta |
| bfa8da8e | docs(41-09): audit of the 1.6.2 delta v1.6.1..738a1373 |
| bc4d5c01 | docs(41-09): audit of the 1.6.2 delta closed |
| (dieser) | docs(41-09): complete the audit plan |

Autor street1983nk <k.cherif@outlook.de>, ohne Trailer. Nicht gepusht (Owner-Regel: Push nur für einen MEDIUM-Fix).

## Ergebnis

- audited_head 738a13731f6448aa97f0a752d5553c6c54db3e85; `git diff --stat 738a1373..HEAD` über die Code-Pfade leer (neu nur backend/tests und .planning).
- LOW: F-41A-01 (Stopp in der Pause schreibt zwei leere Meta-Zeilen, watch.py note_shutdown_begins), F-41A-02 (Catch-up-Fenster vor in_flight), F-41A-03 (ohne Companion still auf unknown, 240 Lesungen je Stunde ohne Leiter; offene Frage aus 41-08), F-41A-04 (fp32-Sweep und fp32-Abruf schreiben in der Pause).
- INFO: Leser legen -shm und leeres -wal an; Arm-Marke bei Enable; Repräsentantenwechsel im Crawl; 240 Lesungen je Stunde (A3).
- Performance: Hintergrundzählung 93 ms bei 250 000 Dokumenten (x86), Retry-Abfrage 0,34 ms je Seite von 1000.
- PHPUnit am Kopf (Docker, nextcloud:32.0.15-apache): OK (958 tests, 5851 assertions).
- Gates: ruff check, ruff format --check (244 Dateien), pyright latest 0 errors, vulture 80 Exit 0.
- Volltestsuite lokal in zwei Hälften mit den sechs --ignore: tests/test_[a-m]*.py 3185 passed, 41 skipped; tests/test_[n-z]*.py 3404 passed, 262 skipped; 0 failed.

## Owner-LOW für 41-10

1. F-41A-03: annehmen für 1.6.2 (Vorschlag) oder Doku-Satz; v1.7 WARNING-Zeile plus Leiter.
2. F-41A-01: v1.7 (Vorschlag) oder Fix in 1.6.2 mit neuem Kopf und Nachaudit, oder Doku-Satz.
3. F-41A-04: v1.7 (Vorschlag).

F-41A-02 direkt v1.7 (deferred-items.md).

## Deviations from Plan

1. **Kein Push und kein head_green.sh.** Plan verlangt Push und CI-Gate "Security scans"; Owner-Regel des Koordinators erlaubt Push nur für einen MEDIUM-Fix. Es gab keinen. Die drei Commits liegen lokal auf main; die Prüfzeile `git log origin/main..HEAD` ist deshalb nicht leer. Der Koordinator bzw. Owner pusht.
2. **Probe Q ohne echtes quiesce.** Der Testpoller trägt einen eingespritzten Writer und Index; nach quiesce baut der Resume beide über die System-Wortliste neu (`/usr/share/dict/ngerman`, lokal nicht vorhanden). quiesce/reopen sind in Probe P (echte Lifespan) und test_backup_pause.py belegt; Probe Q prüft die Holds.
3. **Probe U "zwei Slots"** nicht als Lauf: `_count_refusal` ist synchron und zählt je Pass über Mengen, die Slotzahl geht nicht ein (im Bericht begründet).

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche (nur Tests und Planungsdateien).

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_phase41_audit.py, 41-AUDIT.md
- Commits 4e369f55, bfa8da8e, bc4d5c01 vorhanden
- Code-Diff 738a1373..HEAD über die Code-Pfade leer
