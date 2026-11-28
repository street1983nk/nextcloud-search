---
phase: 46-findling-1-7-1
plan: 10
subsystem: security
tags: [secure-phase, threats]
requires: [46-09]
provides: [46-SECURITY.md verified, threats_open 0]
completed: 2026-11-28
---

# 46-10: secure-phase vor dem Tag

- Erster Lauf: 20 von 22 closed, offen T-46-17 (ausgelieferter Stand nicht belegt) und T-46-18 (Zeitfolge der Push-Freigabe).
- T-46-18: Korrekturzeile des Owners (4b6cda07), "Go" lag vor dem Push 22:24:16 UTC.
- T-46-17: Docker-Fenster mit Freigabe; ausgelieferte admin.js, admin.css und 18 Kataloge gleich a3c94c16 (0a0f8dfa).
- Unabhängiger gsd-security-auditor: beide closed, threats_open 0, status verified (d22d47bb). `Abschluss Security 46-10` vom Owner, ROADMAP/STATE nachgezogen (790ceb25).

## Lehren

- Nextcloud liefert `l10n/*.json` per HTTP nicht aus (404-Seite); Kataloge im Container hashen, `.js` zusätzlich per HTTP.
