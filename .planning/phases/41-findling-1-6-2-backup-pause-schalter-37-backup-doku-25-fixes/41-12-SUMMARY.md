---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 12
subsystem: release-kommunikation
tags: [issues, store-release, 1.6.2]
requires: [41-10, 41-11]
provides: [Issue-Antworten #37 #25 #44, Store-Beleg 1.6.2]
affects: [ROADMAP Phase 41 Erfolgskriterium 6, STATE]
key-files:
  created:
    - .planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-ISSUE-ANTWORTEN.md
    - .planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-12-SUMMARY.md
  modified:
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "I2 (#37) mit geändertem letztem Absatz gepostet, Owner-Freigabe 'Ja zu 37', weil das Issue vorher durch Commit f88b46e7 automatisch geschlossen wurde"
  - "Commit-Nachrichten nie mit close/fix/resolve-Schlüsselwort direkt vor einer Issue-Nummer; 'issue 37' schreiben"
metrics:
  completed: 2026-11-04
---

# Phase 41 Plan 12: Issue-Antworten nach dem Store-Release 1.6.2 Summary

Antworten auf #37, #25 und #44 nach belegtem Store-Release 1.6.2 (beide Apps HTTP 201, Store-API nennt 1.6.2), I3 und I4 zeichengleich, I2 mit owner-freigegebenem letztem Absatz; drei Issues closed, #33/#43/#45 offen.

## Ablauf

- Außenhandlungen (Posten, Schließen) hat der Koordinator ausgeführt; dieser Plan dokumentiert.
- Store-Beleg: apps.json findling 1.6.2 (04.11.2026 gegen 19:20 Ortszeit, Nachkontrolle 18:28Z), appapi_apps.json findling_backend 1.6.2 (18:28:59Z).
- Store-Einreichung 41875127182 HTTP 401 "Invalid token" ohne Store-Änderung; Owner erneuerte APPSTORE_TOKEN; 41885026379 beide Uploads HTTP 201.
- Tag v1.6.2 auf ba098b00, sieben Tag-Läufe grün; Image ghcr.io/street1983nk/findling_backend:1.6.2 Manifest HTTP 200.
- Kommentare: #37 issuecomment-6638602142, #25 issuecomment-6638501178, #44 issuecomment-6638502123; gepostete Bodies per gh api gegen die Scratch-Dateien zeichengleich.

## Deviations from Plan

**1. #37 vorzeitig automatisch geschlossen**
- Commit f88b46e7 (Plan-Commit dieser Phase) trug in der Betreffzeile das Schlüsselwort "closes" direkt vor der Nummer 37; der Push schloss das Issue am 04.11.2026 um 15:21:49Z, vor dem Store-Release.
- Folge: I2 mit geändertem letztem Absatz ("This one got closed a bit early by one of my commits, sorry about that. If the pause doesn't fit your backup setup, just reopen it."), Owner-Freigabe "Ja zu 37"; Rest zeichengleich (Python-Diff: nur letzte Zeile verschieden).
- Lehre festgehalten in 41-ISSUE-ANTWORTEN.md.

**2. findling_backend im AppAPI-Katalog**
- Die ExApp steht nicht in apps.json, sondern in appapi_apps.json; der Beleg für findling_backend kommt von dort.

**3. Kein CI-Gate-Aufruf head_green.sh**
- Reine Planungsdoku-Commits; keine Codeänderung.

## Offen für die Phasen-Verifikation

- 41-11-SUMMARY.md fehlt (Belegkette Tag und Einreichung steht in diesem Plan und in ROADMAP Kriterium 6).
- Forum-Post I1 beim Owner.
- Owner: UI-Sichtung der Pause; Rückmeldungen auf #37/#25/#44 beobachten; #45 für v1.7.

## Self-Check: PASSED

- 41-ISSUE-ANTWORTEN.md vorhanden, drei issuecomment-Links, keine Gedankenstriche.
- Issue-Zustände per gh api geprüft: #37/#25/#44 closed, #33/#43/#45 open.
