---
phase: 37-owner-tor-und-store-sichtbarkeit
plan: 01
subsystem: planning
tags: [owner-tor, dedup, store, zert]
requires: [35-DEDUP-NOTIZ.md, 38-RESEARCH.md]
provides: [37-OWNER-VORLAGE.md, 37-OWNER-ENTSCHEIDE.md, D-37-01..D-37-09]
affects: [37-02, phase-38, phase-39]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/37-owner-tor-und-store-sichtbarkeit/37-OWNER-VORLAGE.md
    - .planning/phases/37-owner-tor-und-store-sichtbarkeit/37-OWNER-ENTSCHEIDE.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
decisions:
  - "Owner-Tor Phase 37 am 28.10.2026 mit 'Wie empfohlen (Recommended)' geschlossen: D1 a, D2 c, D3 a, D4 a, S1 a, S2 a, S3 a, S4 a, Z1 a"
  - "Phase 39: Weg C zuerst, Weg B im Rahmen 1.6.0 sonst vertagt, Weg A nicht in v1.6, Messung A6/A7 in CI oder Testbox"
  - "ZERT-01/02 neu gefasst (D-37-09): erkennen, melden, neue Dateien ohne Re-Register und Neustart uebernehmen, gedeckelt"
  - "Store-Namen, discussion-Link 249775 und Cross-Promo-Satz bleiben bzw. kommen wie empfohlen (D-37-05..08)"
metrics:
  duration: "ca. 25 min (inkl. Wartezeit auf Owner)"
  completed: 2026-10-28
---

# Phase 37 Plan 01: Owner-Tor Summary

In einer einzigen Remote-Runde hat der Owner alle neun Punkte mit "Wie empfohlen (Recommended)" entschieden. Die Entscheide stehen als D-37-01 bis D-37-09 in 37-OWNER-ENTSCHEIDE.md. Phase 39 SC3 trägt jetzt den Dedup-Umfang samt A6/A7-Messung. Phase 38 und ZERT-01/02 haben einen erfüllbaren Wortlaut (Erkennen, Melden, Dateiübernahme ohne Re-Register).

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Gebündelte Owner-Vorlage 37-OWNER-VORLAGE.md | aee10169 |
| 2 | Owner-Tor (Checkpoint, Antwort über Remote Control) | kein Commit |
| 3 | Entscheide festgehalten, Phase 38/39 und ZERT angepasst | 656bd585 |

## Verifikation

- Task-1-Verify: vorlage-ok. Gegenproben: D1-D4 zeichengleich zur Notiz, S4-Sätze zeichengleich zu den info.xml, Forum-URL HTTP 200 (28.10.2026 12:51).
- Task-3-Verify: alle Marken vorhanden, D-37-04 und D-37-09 in ROADMAP.md, alter ZERT-01-Wortlaut entfernt, keine Gedankenstriche, keine getrackte Änderung unter php/, backend/, docs/.

## Deviations from Plan

**1. [Rule 2 - Konsistenz] Phase 37 SC2 und STORE-01 präzisiert**
- Gefunden in: Task 3
- Problem: SC2 und STORE-01 verlangten "Findling Search" in allen Sprachvarianten beider info.xml. Das widerspricht D-37-05 und D-37-06 (de "Findling Suche", fr "Findling Recherche", Backend "Findling Backend").
- Lösung: Beide Stellen nennen jetzt die freigegebenen Sprachvarianten und verweisen auf D-37-05 und D-37-06, damit Plan 37-02 und der Verifier nicht gegen den alten Wortlaut prüfen.
- Dateien: .planning/ROADMAP.md, .planning/REQUIREMENTS.md
- Commit: 656bd585

**2. [Verify-Hinweis] Untracked backend/.coverage**
- Die Datei lag schon vor Planstart untracked vor und stammt nicht aus diesem Plan. Der Verify-Teil "keine Änderung unter backend/" schlägt deshalb wörtlich an; ohne untracked Dateien liefert er 0 Änderungen. Die Datei wurde nicht angefasst.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: 37-OWNER-VORLAGE.md, 37-OWNER-ENTSCHEIDE.md
- FOUND: aee10169, 656bd585
