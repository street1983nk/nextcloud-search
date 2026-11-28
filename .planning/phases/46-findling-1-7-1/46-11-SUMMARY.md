---
phase: 46-findling-1-7-1
plan: 11
subsystem: release
tags: [rel-08, tag, store]
requires: [46-10]
provides: [Tag v1.7.1, Findling 1.7.1 im Store]
completed: 2026-11-28
---

# 46-11: Tag und Store

- Vorprüfung Tag grün, Tag v1.7.1 annotiert auf a3c94c16, gepusht 00:10:58 UTC; alle 8 Tag-Läufe grün, Release immutable, Notiz gesetzt.
- store-submit 46089033695: zweimal HTTP 201; deploy-harp 46089036633 aus den Release-Assets auf vier Beinen grün.
- Store-API 01:22 UTC: findling 1.7.1 (apps.json), findling_backend 1.7.1 (appapi_apps.json). Owner sieht 1.7.1 im App Store.
- Belegkette docs/store-listing.md `# Release 1.7.1 (28.11.2026)`, Push nach `Freigabe Push 46-11` (9e3d1203), Security scans und Scorecard grün.

## Lehren

- `api/v1/apps.json` antwortet mit 302 auf garmN.nextcloud.com: immer `curl -sL`, Antwort in eine Datei, dann auswerten. ExApps stehen in `api/v1/appapi_apps.json`.
- Das Vokabular-Gate zählt in docs/store-listing.md jede Zeile; Workflow-Namen mit dem gesperrten Wort über den Dateinamen nennen.
