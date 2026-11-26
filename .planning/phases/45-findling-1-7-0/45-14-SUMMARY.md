---
phase: 45-findling-1-7-0
plan: 14
subsystem: release
tags: [release, store, v1.7.0, belegkette]
requires: [45-16]
provides: [findling-1.7.0-im-store, belegkette-1.7.0]
affects: [45-15]
tech-stack:
  added: []
  patterns: [Belegkette wie 41-11/43-13, Store-Gegenprobe nach B9]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-14-SUMMARY.md
  modified:
    - docs/store-listing.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/phases/45-findling-1-7-0/45-ABNAHME.md
decisions:
  - "Store-Gegenprobe nach B9: höchstens drei Abfragen im Abstand von mindestens 10 Minuten; api/v1/apps.json leitet per 302 auf garm3.nextcloud.com um, daher ab Versuch 2 mit curl -L"
metrics:
  completed: 2026-11-26
  tasks: 3
---

# Phase 45 Plan 14: Tag und Store-Release 1.7.0 Summary

Findling 1.7.0 ist für beide Apps eingereicht (zweimal HTTP 201, Lauf 45898491529), signiert, immutable, aus den Release-Assets fremdinstalliert und mit vollständiger Belegkette in docs/store-listing.md dokumentiert.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Tag v1.7.0, Release-Lauf, Release-Notiz, deploy-harp-Dispatch | c7175b75, f66c7242, 0a41b736 |
| 2 | Store-Einreichung nach Freigabe | 9e9de52c |
| 3 | Belegkette, Store-Gegenprobe, Zustandspflege | 29ba097f, dieser Abschluss-Commit |

## Belege (Task 3)

- Tag v1.7.0 annotiert auf 22f98ef260fb12f8b55844b76d8070e64f441a4d.
- Release-Lauf 45895635994: zweimal Verified OK, 808542 und 52368 Bytes; Release immutable, neun Assets.
- SHA-256: findling.tar.gz `67f03ba492e9548cd38bdd222d4dbd4efe880f43b829cd41479688966469d409`, findling_backend.tar.gz `21e2c07bbc01cfe024fe0d3681a546847bcefceeade61d9de7a8ad73d2b976d3`; gleich im Log von deploy-harp 45896004205.
- Image findling_backend:1.7.0: Index `sha256:7c5ef16a...ad09`, amd64 `sha256:0f13e6b2...1eec`, arm64 `sha256:133d4a8d...e095` (imagetools inspect, kein Pull).
- deploy-harp 45896004205 mit release_tag=v1.7.0: vier Jobs success, Schritt "Store install 1 from the release" lädt beide Archive aus dem Release.
- Sechs blob/v1.7.0-Links aus beiden info.xml: je HTTP 200.
- Store-Einreichung 45898491529: `release findling v1.7.0: HTTP 201` (21:29:54Z), `release findling_backend v1.7.0: HTTP 201` (21:29:56Z).
- Store-API-Gegenprobe (Befund): 21:31:31Z appapi_apps.json `findling_backend` führt 1.7.0; apps.json `findling` 21:41:40Z und 21:51:45Z nur 1.6.5 (Zwischenspeicher wie bei 1.6.3/1.6.4). Drei Versuche nach B9 ausgeschöpft; offen: Owner-Blick auf die Store-Seite bzw. spätere Abfrage.

## Deviations from Plan

**1. [Rule 3 - Blocking] Abschnitt `## Store-Einreichung` in 45-ABNAHME.md nachgetragen**
- Found during: Task 3
- Issue: Der Verify von Task 2 verlangt beide HTTP-201-Zeilen in 45-ABNAHME.md; der Abschnitt fehlte nach Commit 9e9de52c.
- Fix: Abschnitt mit den drei Logzeilen wörtlich aus Lauf 45898491529 ergänzt; Task-2-Verify jetzt grün.

## Offen

- Store-API nennt 1.7.0 bisher nur für findling_backend; für findling bestätigt erst der Owner auf der Store-Seite oder eine spätere Abfrage (Erfolgskriterium 5, Teil "Store-API nennt 1.7.0 für beide Apps").
- Push der Belegdokumente nur mit `Freigabe Push 45-14: ... Entscheid: ja` (Frage stellt der Koordinator), danach `git pull --rebase origin main`, Push, head_green.sh "Security scans".
- HaRP deploy auf dem Tag (45895635939) lief beim Abschluss noch (drei von vier Jobs success).
- 45-15: Antworten in #45, #56, #57, #59, #25, Bitte in #53, Nachtrag der Release-Threats T-45-47 bis T-45-54, Phasenabschluss.

## Self-Check: PASSED

Dateien vorhanden (store-listing.md mit "# Release 1.7.0", 45-ABNAHME.md, STATE.md, ROADMAP.md, 45-14-SUMMARY.md); Commits c7175b75, f66c7242, 0a41b736, 9e9de52c, 29ba097f vorhanden; Verify von Task 2 und Task 3 grün.
