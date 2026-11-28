---
phase: 46-findling-1-7-1
plan: 12
subsystem: release
tags: [threats, abschluss]
requires: [46-11]
provides: [Nachtrag Release-Threats, Phase 46 fertig]
completed: 2026-11-28
---

# 46-12: Kommentare, Release-Threats, Abschluss

- E-46-07 a, keine Kommentare in 46-12. Die beiden Kommentare der Phase (PR #60, #63, 27.11. 15:59Z) kamen in 46-07 mit eigener Freigabe.
- `## Nachtrag Release-Threats` in 46-SECURITY.md: T-46-23 bis T-46-29 closed, threats_open 0.
- REQUIREMENTS: EXCL-07, EXCL-08, ADM-05, PRUEF-05, PRUEF-06, REL-08 Complete. ROADMAP Phase 46 und Milestone v1.8 fertig, nächster Schritt `/gsd:complete-milestone v1.8` (Owner).

## Abweichung

- Die automatische Prüfung von Task 1 bleibt rot, aus drei Planfehlern, nicht aus einem Befund: sie sucht `Entscheid E-46-07 46-00` (die Zeile heißt `46-01`, weil die Entscheide in 46-01 kamen), verlangt `Entscheid: a` am Zeilenende (die Zeile trägt danach "(keine GitHub-Kommentare zu 1.7.1)") und verbietet im Zweig a jede Zeile `Freigabe Kommentar ` (die Zeile `Freigabe Kommentar PR60 und 63 46-07` deckt die zwei Kommentare aus 46-07). Inhaltlich gilt Zweig a: in 46-12 kein Kommentar, keine Zeile `Freigabe Kommentar <Nr> 46-12`. Die Freigabedatei bleibt unverändert.
