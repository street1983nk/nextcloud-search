---
phase: 40-haertung-und-store-einreichung-1-6-0
plan: 05
subsystem: release
tags: [tag, release, store-submission, evidence]
requires:
  - 40-04 (GO: ja, Tag-Kopf 91a0603f)
provides:
  - Tag v1.6.0 (annotiert, 91a0603f), Release v1.6.0 mit 9 Assets
  - Einreichung beider Apps 1.6.0 (Store submission 40868132102, zweimal HTTP 201)
  - docs/store-listing.md "# Release 1.6.0 (29.10.2026)" mit Belegen (1) bis (12)
  - REL-06 abgehakt
affects:
  - Phasenverifikation 40, Milestone-Abschluss v1.6
key-files:
  created:
    - .planning/phases/40-haertung-und-store-einreichung-1-6-0/40-05-SUMMARY.md
  modified:
    - docs/store-listing.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "Release-Notiz v1.6.0 nach Muster 1.5.0: abgenommene acht Zeilen wortgleich vorn, danach der generierte Block What's Changed, generierte Full-Changelog-Zeile entfällt"
  - "appapi_apps.json führte nach sechs Aufrufen bis 11:53:11Z noch 1.5.1 (Cache-Verzug wie 1.4.3 und 1.5.0); Nachführung offen, kein Befund"
metrics:
  completed: 2026-10-29
  tasks: 2
  files: 4
---

# Phase 40 Plan 05: Tag, Release und Store-Einreichung 1.6.0 Summary

Findling 1.6.0 ist getaggt (v1.6.0 auf 91a0603f), als unveränderliches Release mit neun Assets veröffentlicht, aus den Release-Assets auf vier Matrixzeilen fremdinstalliert und für beide Apps mit zweimal HTTP 201 im Store eingereicht; beide App-Seiten nennen 1.6.0 für Nextcloud 33, 34 und 35.

## Ablauf

Fortsetzung nach versehentlichem Stopp des Vorgängers. Der Vorgänger hatte den Tag gesetzt und gepusht (Tag-Objekt 82ffcaa0, 2026-10-29T11:20:11Z), aber noch nichts in docs/store-listing.md oder .planning geschrieben; es gab keinen begonnenen Abschnitt "# Release 1.6.0" und keine Arbeitsnotiz. Die Vorprüfungen vor dem Tag (GO, Tag-Kopf auf origin/main, head_green) belegt 40-ABNAHME.md; nachgeprüft: `GO: ja`, `git rev-list -n 1 v1.6.0` gleich Tag-Kopf, `git cat-file -t v1.6.0` = tag.

## Task 1: Belegkette (1) bis (8)

- (1) Tag annotiert auf 91a0603f2b69213037c0d8ac2101121f9ba767b2.
- (2) Release-Lauf 40864595574 success, 9 Assets, veröffentlicht 11:21:11Z, kein Draft.
- (3) findling.tar.gz 642813 B, findling_backend.tar.gz 43647 B, zweimal "Verified OK" im Log, isImmutable true; SHA-256 890d861d... und 12f3fe9b...
- (4) corresponding_source.py --verify-only Exitcode 0 (vier Zeilen ok), Quellarchiv 3262 Einträge, get-tar-commit-id = 91a0603f.
- (5) Image-Index sha256:2107130e... mit linux/amd64 und linux/arm64, anonym über die Registry-API.
- (6) Release-Notiz gesetzt, diff der ersten acht Zeilen gegen den abgenommenen Codeblock leer, danach 9 Assets und isImmutable true.
- (7) drei Tag-Links (je info.xml) antworten 200, Compare-Link 200.
- (8) Fremdinstallation `deploy-harp.yml --ref main -f release_tag=v1.6.0`, Lauf 40865691730 success auf stable33, stable34, stable34 arm64, stable35; je Zeile `RELEASE_TAG: v1.6.0` und dieselben SHA-256.

Tag-Läufe alle success, keine Wiederholung: Release 40864595574, PHP and store metadata gates 40864595622, Multi-arch image 40864595511, HaRP deploy 40864595641 (vier Zeilen), Python gates 40864595569, Integration 40864595676, Resilience 40864595571. Beleg-Commit cb65aa61: Security scans 40868095970, Scorecard 40868095728 success.

## Task 2: Einreichung und Gegenprobe

- Vorher: kein Store-submission-Lauf seit 39865809204 (1.5.1).
- Store submission 40868132102 (erstellt 11:47:44Z, Kopf cb65aa61) success:
  - `release findling v1.6.0: HTTP 201` (11:47:55Z)
  - `release findling_backend v1.6.0: HTTP 201` (11:47:57Z)
- 11:48:25Z/11:48:26Z: beide App-Seiten 200, Stable channel 1.6.0 für NC 35, 34, 33, Download auf releases/download/v1.6.0.
- 11:48:27Z: platform/34.0.3/apps.json findling 1.6.0, created 11:47:55.560497Z.
- appapi_apps.json: sechs Aufrufe 11:48:43Z bis 11:53:11Z, findling_backend noch 1.5.1 (Cache-Verzug, Nachführung offen).

## Commits

| Commit | Inhalt |
|---|---|
| cb65aa61 | docs(40-05): release 1.6.0 evidence |
| (folgt) | docs(40-05): store submission 1.6.0 evidence (docs/store-listing.md) |
| (folgt) | docs(40-05): store submission 1.6.0 state (.planning) |

## Deviations from Plan

- **Tag durch den Vorgänger:** Tag und Tag-Push lagen schon vor; die Vorprüfungen (a) bis (e) vor dem Tag stammen aus 40-ABNAHME.md und dem Vorgänger, hier nur nachgeprüft (Tag-SHA, Tag-Typ, Tag-Links 200).
- **Zwei Commits statt einem in Task 2:** docs/store-listing.md (mit Session-Zeile) und .planning (ohne) getrennt, nach der Commit-Regel des Koordinators.
- **ROADMAP Planzahl:** Phase 40 hat sechs Pläne (40-06 kam dazu), Progress 6/6 statt 5/5.
- **Release-Notiz:** die abgenommene Notiz hat keine Leerzeile vor "**Full Changelog**"; wortgleich übernommen (diff leer), auf GitHub rendert die Zeile deshalb als Fortsetzung des letzten Punkts.
- **Image-Beleg:** anonyme Registry-API statt `docker manifest inspect` (kein lokales docker, laut Plan).

## Known Stubs

Keine.

## Self-Check: PASSED

- docs/store-listing.md enthält "# Release 1.6.0", zweimal "Verified OK", "release_tag=v1.6.0", beide HTTP-201-Zeilen.
- REQUIREMENTS.md `[x] **REL-06`, Traceability Complete.
- cb65aa61 auf origin/main; Läufe 40864595574, 40865691730, 40868132102 success.
