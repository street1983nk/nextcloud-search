---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 04
subsystem: testing
tags: [hardening, slots, oom, embedding, profile, precision, REL-04]
requires: []
provides:
  - "Härtungsmatrix Erfolgskriterium 1 (sieben Zeilen, je Datei::Test und gefahrenes Ergebnis)"
  - "Sechs Lückentests in backend/tests/test_launch_hardening.py"
affects: [29-13, 29-14]
tech-stack:
  added: []
  patterns: ["Lückentests importieren die Stand-ins aus test_poller.py und test_embedding_track.py statt neuer Harnesses", "Neustart = zweiter Poller auf demselben Volume plus Reset des Modulzustands"]
key-files:
  created:
    - backend/tests/test_launch_hardening.py
    - docs/audits/2026-10-phase-29/haertungsmatrix.md
  modified: []
decisions:
  - "Befunde aus 29-04 gehen an 29-13 (Audit) und 29-14 (Fix), weil 29-14-PLAN die xfail-Entfernung trägt"
  - "Die Embed-Spur wird im Prozess als BaseException-Tod simuliert; ein SIGKILL der Spur allein gibt es nicht, sie läuft im Hauptprozess"
  - "FINDLING_MAX_CELLS in EXPECTED bleibt beim Fix-Plan von D-29-03 (Produktänderung an info.xml)"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-06
  tasks: 2
  files: 2
---

# Phase 29 Plan 04: Härtungsmatrix 1.4.0 Summary

Matrix aller Szenarien von Erfolgskriterium 1 mit gelesenen und gefahrenen Bestandstests plus sechs neue Lückentests (zwei Kills in einem Pass, Kill beider Spuren, Hardware-Schrumpfung, Profil- und Präzisionswechsel mitten im Vektor-Reindex, Umgebungsvariable gegen Profil), alle grün, kein Produktbefund.

## Erledigt

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Matrix aus bestehenden Tests bestätigen | 26dc283c | docs/audits/2026-10-phase-29/haertungsmatrix.md |
| 2 | Lückentests der Härtungsmatrix | 22204166 | backend/tests/test_launch_hardening.py, docs/audits/2026-10-phase-29/haertungsmatrix.md |

## Ergebnisse

- Bestandstests: 22 passed, 2 skipped lokal (Windows). Die beiden übersprungenen Fälle sind die SIGKILL-Fälle aus `test_slots_kill.py` (nur Linux); Beleg ist die Linux-CI, Lauf 37413342090 auf 1a115cd9 (backend-Baum identisch mit der Basis), 4448 passed, 13 skipped. Die CI läuft ohne `-rs`, der Einzelfallnachweis ist daher als offener Punkt für 29-13 in der Matrix vermerkt.
- Lückentests: 6 passed. Positivkontrollen im Test selbst: Teilbestand an Vektoren beim Tod der Embed-Spur, Slotziel fällt von 15 auf 3.
- Vollsuite: 4442 passed, 25 skipped (lokal, 11 min). ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.
- `git diff --stat HEAD~2 -- backend/src php` leer: kein Produktcode berührt, Baumhash-Pins unangetastet.

## Abweichungen vom Plan

- Befund-Übergabe: Der Plan nennt 29-13; laut 29-14-PLAN liegen die Fixes und die xfail-Entfernung dort. Die Matrix nennt beides ("Audit in 29-13, Fix in 29-14"). Da kein Befund entstand, hat das keine Folgen.
- Zeile 7 (Upgrade 1.3.2 auf 1.4.0) bekommt hier bewusst keinen neuen Test; die Nachprüfung D-29-10 mit CI-Saat gehört zu 29-11, wie im Plan vorgesehen.
- Testfehler im ersten Entwurf von Zeile 5 (Filter `_drift_chain` zählt auch die Sweep-Bänder), im Test korrigiert, kein Produktbefund.

## Befunde für 29-13 / 29-14

Keine. Kein xfail, keine H-29-NN-ID.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: backend/tests/test_launch_hardening.py (484 Zeilen)
- FOUND: docs/audits/2026-10-phase-29/haertungsmatrix.md (enthält "Hardware-Schrumpfung", 28 Treffer "test_")
- FOUND: 26dc283c, 22204166
