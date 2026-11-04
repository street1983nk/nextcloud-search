---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 11
subsystem: release
tags: [tag, store-release, 1.6.2, owner-run]
requires: [41-10]
provides: [Tag v1.6.2, Release-Archive 1.6.2, Store-Einreichung findling und findling_backend 1.6.2]
affects: [ROADMAP Phase 41 Erfolgskriterium 6, STATE, Plan 41-12]
key-files:
  created:
    - .planning/phases/41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes/41-11-SUMMARY.md
  modified:
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "Tag-Push und Store-Einreichung führt der Owner aus (D-41-16); Claude prüft vorher und danach"
  - "Store-API höchstens alle 10 Minuten abfragen; 40 Minuten Dauerabfrage von apps.json führten zu HTTP 429 für die Owner-IP"
metrics:
  completed: 2026-11-04
---

# Phase 41 Plan 11: Tag v1.6.2 und Store-Einreichung Summary

Tag v1.6.2 (annotiert) auf ba098b00, sieben Tag-Läufe grün inklusive eigenem PHP-Lauf, Release immutable mit beiden signierten Paketen, Store-Einreichung nach erneuertem APPSTORE_TOKEN zweimal HTTP 201, Store-API nennt 1.6.2 für beide Apps.

## Ablauf

- Task 1 (Vorprüfung, Commit 8a219b8a): Abschnitt "Vorprüfung Tag" und Owner-Befehle in 41-ABNAHME.md.
- Task 2 (Owner): Tag `v1.6.2` gepusht; `git ls-remote`: `refs/tags/v1.6.2^{}` = ba098b00f61cb57dfa8bc127c264e198e4afa313, Objekttyp `tag` (annotiert).
- Tag-Läufe, alle success auf ba098b00: Release archives for the app store 41869261561, PHP and store metadata gates 41869261491, Python gates 41869261151, Integration 41869261583, Resilience 41869261405, Multi-arch image 41869261338, HaRP deploy 41869261143.
- Damit ist der head_green-Vorbehalt aus 41-ABNAHME.md (PHP-Gates ohne Lauf auf ba098b00, nur Ersatzbeleg 41792859857 auf f12649a2) geschlossen: PHP-Gates liefen auf dem Tag selbst grün.
- Release v1.6.2: isImmutable true; Assets findling.tar.gz (656 338 B) und findling_backend.tar.gz (44 225 B), beide unter 20 971 520 B, je mit .sig; Quellpakete findling-1.6.2-source.tar.gz, libde265, libheif, pillow_heif, x265.
- Image `ghcr.io/street1983nk/findling_backend:1.6.2`: Manifest HTTP 200 vor der Einreichung.
- Task 3 Store (Owner löste aus): Lauf 41875127182 failure, HTTP 401 "Invalid token", keine Store-Änderung. Owner erneuerte das Secret APPSTORE_TOKEN. Wiederholung 41885026379 success, Log: `release findling v1.6.2: HTTP 201`, `release findling_backend v1.6.2: HTTP 201`.
- Gegenprobe Store-API (04.11.2026 18:28Z): apps.json id `findling` nennt 1.6.2; appapi_apps.json id `findling_backend` nennt 1.6.2.

## Deviations from Plan

**1. Store-Einreichung zuerst 401**
- Ursache: abgelaufenes oder ungültiges APPSTORE_TOKEN; Owner erneuerte das Secret, zweiter Lauf grün. Kein Mischbetrieb, da der erste Lauf nichts änderte.

**2. HTTP 429 durch zu häufige Store-Abfragen**
- Claudes Hintergrund-Polling von apps.json über ca. 40 Minuten löste eine vorübergehende HTTP-429-Sperre für die IP des Owners auf apps.nextcloud.com aus.
- Lehre: Store-API höchstens alle 10 Minuten abfragen.

**3. Belegkette nur in der Planungsdoku**
- Der Abschnitt "# Release 1.6.2" in docs/store-listing.md wurde nicht angelegt (Abschluss auf Auftrag nur als Planungsdoku); die Belege stehen hier, in 41-ISSUE-ANTWORTEN.md und in ROADMAP Kriterium 6.
- Nicht erneut geprüft in diesem Abschluss: "Verified OK"-Logzeilen, SHA-256 der Pakete, Quellpflicht-Prüfung, Tag-Links per curl, Release-Notiz-Diff; die grünen Läufe Release archives 41869261561 und HaRP deploy 41869261143 (Fremdinstallation) decken die Signatur- und Installationsschritte ab.

## Self-Check: PASSED

- Tag v1.6.2 auf ba098b00 (git ls-remote), Typ tag.
- Sieben Tag-Läufe success, Store-Lauf 41885026379 mit zweimal HTTP 201 (gh run view --log).
- Release isImmutable true (gh release view).
