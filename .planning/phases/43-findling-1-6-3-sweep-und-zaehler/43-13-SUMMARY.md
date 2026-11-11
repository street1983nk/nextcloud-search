---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 13
subsystem: Release 1.6.3 (Tag, Release-Lauf, Store-Einreichung, Belegkette)
tags: [D-43-10, D-43-15, release, store, tag]
requires: [43-12]
provides: [Tag v1.6.3 auf 8b00d610, Release v1.6.3 mit neun Assets, Findling und findling_backend 1.6.3 im App Store, Belegkette in docs/store-listing.md]
affects: [43-14]
key-files:
  modified:
    - docs/store-listing.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-ABNAHME.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-FREIGABEN.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
decisions:
  - "Der Owner hat die Ausführung von Tag, Tag-Push und Store-Einreichung an Claude übertragen ('Kannst das machen ich bin nicht am Rechner') und Release-Notiz, Fremdinstallation und Beleg-Push freigegeben"
  - "Der Tag wurde nach Mitternacht gesetzt, damit er zum CHANGELOG-Datum 2026-11-12 passt"
metrics:
  completed: 2026-11-12T00:58:00+01:00
  tasks: 3
---

# Phase 43 Plan 13: Tag v1.6.3 und Store-Einreichung

Findling 1.6.3 ist getaggt, veröffentlicht und für beide Apps im App Store eingereicht; die Store-API nennt 1.6.3 für findling und findling_backend.

## Belege (Einzelheiten in docs/store-listing.md, "# Release 1.6.3 (12.11.2026)")

- Tag v1.6.3, annotiert, auf 8b00d6100be0133fd436fd2f277736f5d9e86a9b, gesetzt 2026-11-12T00:00:23+01:00.
- Sieben Läufe auf dem Tag grün, darunter Release 43116399950 (zweimal "Verified OK", 707721 und 49637 Bytes) und PHP and store metadata gates 43116400115.
- Release immutable, neun Assets; Image 1.6.3 für amd64 und arm64; Tag-Links HTTP 200.
- Store submission 43120250685: zweimal HTTP 201. Store-API um 23:52Z: 1.6.3 für beide IDs.
- Release-Notiz ersetzt und verglichen; Fremdinstallation deploy-harp 43120397524 grün in vier Beinen.

## Abweichungen vom Plan

- Der Plan sieht vor, dass der Owner Tag und Einreichung selbst ausführt. Er hat die Ausführung übertragen; das Wort steht mit der Lesart von Claude in 43-FREIGABEN.md.
- Die Liste api/v1/apps.json führte für findling rund 20 Minuten lang noch 1.6.2 (Zwischenspeicher).
