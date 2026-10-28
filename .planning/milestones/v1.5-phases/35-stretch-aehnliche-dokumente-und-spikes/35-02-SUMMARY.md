---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 02
subsystem: docs/planning
tags: [dedup, issue-25, acl, smb, external-storage, decision-paper]
requires: []
provides:
  - "35-DEDUP-NOTIZ.md: Entscheidungsvorlage #25-Dedup je Mount-Config für v1.6"
affects:
  - "v1.6-Planung (#25-Dedup-Bau erst nach Owner-Entscheid D1 bis D4)"
tech-stack:
  added: []
  patterns: ["Quellenzeile je NC-Fakt mit Datei, Zeilen, Branch stable34, Abrufdatum", "Sperrliste aus Issue-Namen im Scratch, grep -F -i gegen die Notiz"]
key-files:
  created:
    - .planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-DEDUP-NOTIZ.md
  modified: []
decisions:
  - "Empfehlung an den Owner: Weg B (Hash-Wiederverwendung) als Standard, Weg A nur als Admin-Opt-in mit Warnsatz, Weg C sofort"
  - "Dedup-Schlüssel nie Mount-Config-ID allein, sondern Backend, Host, Share, Root nach Platzhalter-Ersetzung, Pfad"
metrics:
  duration: "ca. 20 min"
  completed: 2026-10-19
  tasks: 2
  files: 1
requirements: [STR-03]
---

# Phase 35 Plan 02: Dedup-Entscheidungsvorlage Issue #25 Summary

Interne Entscheidungsvorlage zur #25-Dedup je Mount-Config: frisch belegte stable34-Fakten (SMB-Storage-ID mit Anmeldenamen, `check_acl` standardmäßig aus, `isReadable()` ohne ACL-Prüfung, `$user`-Ersetzung je Nutzer), drei Wege mit ACL-Folge, Empfehlung B als Standard und Owner-Fragen D1 bis D4.

## Erledigt

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Sachstand (nur aggregierte Issue-Zahlen), NC-Fakten F1 bis F6 mit Quelle, Abschnitt "Wann Duplikate entstehen" | 78d6bf8f |
| 2 | Wege A/B/C mit Ablauf, ACL-Folge, Ersparnis, Bauteilen, Migration; Vergleichstabelle; Empfehlung; D1 bis D4; Abgrenzung | 385126d1 |

## Prüfergebnisse

- Sperrliste (16 Einträge aus Issue #25, nur im Scratch): `grep -F -i -f` gegen die Notiz: **0 Treffer**.
- `grep -nE "smb::[a-z0-9._-]+@"`: kein Treffer; `smb::[^<[:space:]]+@`: kein Treffer (Formel nur mit `<auth-user>`-Platzhaltern).
- Gedankenstriche U+2013/U+2014: keine.
- Pflichtbegriffe beider Tasks vorhanden; 4 mal "Empfehlung:" (D1 bis D4).
- `reuse lint`: konform (2781/2781).
- `git status`: nur die Notiz geändert, Sperrliste und Rohdaten liegen außerhalb des Repos.

## Neue Erkenntnisse gegenüber dem Research

- ACL-Option: nicht "um Zeile 214", sondern gelesen in `SMB.php:120`, angewendet in `SMB.php:249-256`, `getACL()` in 207-222.
- `getACL()` wertet nur den ACE des Anmeldenamens aus, keine Gruppen-ACEs: selbst mit `check_acl` bleibt Weg A lückenhaft.
- `isReadable()` (`SMB.php:678-688`) prüft nur Stat und Versteckt-Flag, stützt damit den Leck-Fall von Weg A (A6 bleibt als Messpunkt).
- Prüfpunkt A7 neu: Findling hat keine Inhalts-Entdopplung im Backend; warum der Zähler beim Melder zur eindeutigen Menge passt, ist offen.

## Deviations from Plan

- **Push nicht ausgeführt:** Der Plan nennt "Push"; im Worktree-Modus führt der Orchestrator zusammen und pusht. Kein Push vom Agent-Branch.
- **WebFetch nicht verfügbar:** Doku-Seite der Authentifizierungsmechanismen per `curl` in den Scratch geladen und als Text gelesen; Inhalt gleichwertig.
- Sonst: Plan wie geschrieben ausgeführt.

## Known Stubs

Keine (reine Doku).

## Self-Check: PASSED

- FOUND: .planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-DEDUP-NOTIZ.md
- FOUND: 78d6bf8f
- FOUND: 385126d1
