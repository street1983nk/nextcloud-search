---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 01
subsystem: planung/ui-vertrag
tags: [ui-spec, roadmap, owner-checkpoint, ursachencodes]
requires: []
provides:
  - "UI-SPEC-Delta D-27-20: Ursachen disk_short, memory_unknown, interrupted, pause_timeout, probe_failed und Startcode rebuilding, je ein Satz EN/DE"
  - "Endwerte Poll 2000 ms, Messdeckel 120 s, Download inkl. Digest 600 s, Pause 1800 s, GUARD_RESERVE_BYTES 235 MiB"
  - "ROADMAP Phase 27 SC1 mit Knopf 'Bei Sparsam bleiben' (D-27-11)"
affects: [27-02, 27-07, 27-13]
tech-stack:
  added: []
  patterns: ["geschlossene Codemenge als gemeinsame Quelle für Container, PHP und JS"]
key-files:
  created: []
  modified:
    - .planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-UI-SPEC.md
    - .planning/ROADMAP.md
decisions:
  - "Owner bestätigt SC1-Wortlaut 'Bei Sparsam bleiben' und die sechs neuen Sätze unverändert (29.09.2026)"
metrics:
  duration: "ca. 15 min (ohne Wartezeit am Owner-Checkpoint)"
  completed: 2026-09-29
  tasks: 2
  files: 2
---

# Phase 27 Plan 01: UI-SPEC-Delta D-27-20 und SC1-Wortlaut Summary

UI-Vertrag auf Entscheidungsstand D-27-11 und D-27-15 bis D-27-20 gebracht: fünf neue Ursachencodes plus Startcode rebuilding mit je einem Satz EN/DE, Delta-Abschnitt mit Endwerten und Zahlenschlüsseln, ROADMAP-SC1 auf "Bei Sparsam bleiben"; vom Owner bestätigt.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | UI-SPEC-Delta D-27-20, Endwerte, ROADMAP SC1 | 256c8fb1 | 27-UI-SPEC.md, .planning/ROADMAP.md |
| 2 | Owner-Checkpoint SC1-Wortlaut und Delta | (kein Code, Signal unten) | keine |

## Ergebnis

- Ursachentabelle: disk_short, memory_unknown, interrupted, pause_timeout, probe_failed mit Wortlaut aus der Research
- Tabelle Startfehler: rebuilding (Z16a, Probe-Knöpfe gesperrt, Z5-Wege bleiben)
- Abschnitt "Delta 29.09.2026 (D-27-15 bis D-27-20)": 2000 ms, 120 s, 600 s, 1800 s mit Schritt pause und Ursache pause_timeout, GUARD_RESERVE_BYTES 235 MiB, D-27-17, D-27-18, D-27-12 (guardConfirmable), Zahlenschlüssel und Platzhalterbelegung je Ursache
- ROADMAP SC1: nur der Knopfname geändert, "Beim sicheren Standard bleiben" kommt nicht mehr vor
- Gates erneut geprüft: jeder der sechs Codes mindestens zweimal in der UI-SPEC, "Bei Sparsam bleiben" zweimal in der ROADMAP, keine U+2013/U+2014 in der UI-SPEC

## Owner-Signal (Task 2, wörtlich)

"approved" (Owner, 29.09.2026) für SC1-Wortlaut "Bei Sparsam bleiben" und die sechs neuen Sätze disk_short, memory_unknown, interrupted, pause_timeout, probe_failed, rebuilding unverändert.

Keine Wortlautänderungen gewünscht, daher keine Nacharbeit.

## Deviations from Plan

None - plan executed exactly as written.

Hinweis: STATE.md wird laut Auftrag in diesem Plan nicht fortgeschrieben (Orchestrator-Aufgabe).

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: 27-UI-SPEC.md, .planning/ROADMAP.md
- FOUND: Commit 256c8fb1 auf worktree-agent-a0dc13deee9d6b016
