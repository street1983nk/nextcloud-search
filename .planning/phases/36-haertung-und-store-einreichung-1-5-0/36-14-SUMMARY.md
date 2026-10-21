---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 14
subsystem: Tag und Release v1.5.0
tags: [rel-05, hart-06, tag, release, corresponding-source, foreign-install]
requires: [36-13]
provides:
  - "Annotierter Tag v1.5.0 auf 6c953a76, alle sieben Tag-Läufe grün"
  - "Release v1.5.0 mit neun Assets, unveränderlich, Verified OK zweimal, Quellpflicht aus dem Release geprüft"
  - "Manifestindex findling_backend:1.5.0 mit linux/amd64 und linux/arm64, anonym geprüft"
  - "Release-Notiz beginnt mit der abgenommenen Liste B4"
  - "Tag-Links 200, Fremdinstallation aus den Release-Assets grün (deploy-harp 39590105344, vier Matrixzeilen inkl. arm64)"
  - "Spiegel source-1.5-dev.3 veröffentlicht und aus dem Download geprüft; THIRD-PARTY.md verweist darauf"
affects: [36-15, 36-16]
tech-stack:
  added: []
  patterns:
    - "Doku-Commits vor dem Tag pushen, damit der Tag auf den Kopf nach dem Push zeigt"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-14-SUMMARY.md
  modified:
    - docs/store-listing.md
    - THIRD-PARTY.md
decisions:
  - "Release-Notiz: B4 wortgleich als Kopf, danach der generierte Block What's Changed; die generierte Full-Changelog-Zeile (ab v1.4.2) entfällt, weil B4 die abgenommene Zeile ab v1.4.3 trägt"
  - "Spiegel-Tag source-1.5-dev.3 explizit auf b6bd308d (Kopf nach Push A) statt auf den Zweignamen main"
metrics:
  duration: "ca. 75 min (12:50 bis 14:05 Ortszeit), davon ca. 50 min CI"
  completed: 2026-10-21
  tasks: 3
  files: 2
requirements: [REL-05, HART-06]
---

# Phase 36 Plan 14: Tag und Release v1.5.0 Summary

v1.5.0 ist annotiert auf 6c953a76 getaggt und als unveränderliches Release mit neun Assets veröffentlicht. Beide Pakete sind signiert ("Verified OK" zweimal), die vier Quellpakete sind aus dem Release geprüft, das Image ist ein Index für amd64 und arm64, und die Fremdinstallation aus den echten Assets ist auf allen vier Matrixzeilen grün.

## Task 1: Owner-Worte, Push, Spiegel

Owner-Worte, übermittelt durch den Koordinator am 21.10.2026:
- Frage A: "Darf ich die beiden Doku-Commits 2c379a47 und b6bd308d auf origin/main pushen?" Antwort wörtlich: "ok".
- Frage Spiegel: "Darf ich source-1.5-dev.3 jetzt als öffentliches GitHub-Pre-Release veröffentlichen?" Antwort wörtlich: "ok".
- Frage B: (a) Push des Spiegel-Doku-Commits 42eaa997 mit CI, (b) danach v1.5.0 annotiert auf den neuen Kopf setzen und pushen, dazu die Empfehlung, THIRD-PARTY.md:273 vorher auf source-1.5-dev.3 umzustellen und mitzupushen. Antwort wörtlich: "ok wie du empfehlst". Tag-SHA = Kopf nach dem Push = 6c953a76b7043bf1c549cc1e0303aa80cb4c9746.

Ablauf:
1. `git push origin main`: `805308c4..b6bd308d`. Läufe auf b6bd308d (nur docs/ und .planning/, Pfadfilter): Security scans 39588494058, OpenSSF Scorecard 39588493958, beide success.
2. Spiegel: `corresponding_source.py publish --tag source-1.5-dev.3 --source-dir <Scratch>/source-1.5-dev.3 --target b6bd308d` (vorher `--verify-only` und `--dry-run`). Pre-Release https://github.com/street1983nk/nextcloud-search/releases/tag/source-1.5-dev.3, nicht latest, `isImmutable: true`, 2026-10-21T11:01:17Z, vier Assets. Frischer Download nach `.../scratchpad/verify-source-1.5-dev.3-130123/mirror`, `--verify-only` alle vier "ok", Exit 0. Kein Workflow durch diesen Tag gestartet. Doku-Commit 42eaa997.
3. THIRD-PARTY.md:273 auf source-1.5-dev.3 (nur der Link), Doku- und Store-Tests 191 passed; Commit 6c953a76.
4. `git push origin main`: `b6bd308d..6c953a76`. Läufe: OpenSSF Scorecard 39589356094, Security scans 39589356178, beide success.
5. `git tag -a v1.5.0 -m "Findling 1.5.0" 6c953a76...`, `git push origin v1.5.0` um 11:07:55Z.

## Task 2: Release-Lauf und Belege

Tag-Läufe, alle success, keine Wiederholung:

| Lauf | Workflow |
|---|---|
| 39589670677 | Release (release.yml), Job 119187177861 |
| 39589670945 | PHP and store metadata gates |
| 39589670827 | Multi-arch image |
| 39589670578 | HaRP deploy (vier Matrixzeilen) |
| 39589670676 | Python gates |
| 39589670579 | Integration |
| 39589670752 | Resilience |

- Neun Assets, Bytezahlen: findling.tar.gz 627001, findling_backend.tar.gz 42597, je .sig 684, findling-1.5.0-source.tar.gz 25881295, pillow_heif 17395786, x265 2052112, libde265 324452, libheif 2373898.
- Log: `dist/findling.tar.gz is 627001 bytes, the store limit is 20971520` + `Verified OK`; `dist/findling_backend.tar.gz is 42597 bytes, ...` + `Verified OK`.
- `isImmutable`: gh kennt das Feld (Probe v1.4.3 true), v1.5.0 true; Gegenprobe `gh api .../releases/tags/v1.5.0 --jq .immutable` true.
- Quellpflicht aus dem Release: `--verify-only` alle vier "ok", Exit 0; Quellbaum 3193 Einträge mit Präfix `findling-1.5.0/`, `git get-tar-commit-id` = 6c953a76.
- Manifest anonym (docker manifest inspect und anonymes Registry-Token): Index sha256:cf805dfa...49d8, linux/amd64 sha256:5b5bc09b..., linux/arm64 sha256:ec87abe1..., plus zwei Attestierungen.
- Release-Notiz per `gh release edit v1.5.0 --notes-file`, Exit 0; die ersten zehn Zeilen sind B4 wortgleich (diff gegen 36-WORTLAUT.md und store-listing Teil 8).

## Task 3: Tag-Links und Fremdinstallation

- Tag-Links: drei eindeutige URLs (docs/migrate-from-fulltextsearch{,.en,.fr}.md unter blob/v1.5.0), alle 200. READMEs tragen keine Tag-Links.
- `gh workflow run deploy-harp.yml --ref main -f release_tag=v1.5.0`: Lauf 39590105344 success; stable33 amd64 119188649239, stable34 amd64 119188649843, stable34 arm64 119188649600, stable35 amd64 119188649692. Jede Zeile lädt beide Pakete von releases/download/v1.5.0, die SHA-256 (14e9b218..., d9c7b28f...) gleichen dem lokalen Download.
- Beleg-Commit a4035afc (lokal, nicht gepusht).

## Deviations from Plan

**1. [Rule 1 - Bug] Gesperrtes Wort im Beleg**
- Found during: Task 3, Doku-Tests
- Issue: Der Workflow-Name "Release archives for the app store" enthält das gesperrte Wort (E-H2), test_store_metadata rot.
- Fix: im Beleg `release.yml` statt des Workflow-Namens.
- Commit: a4035afc

**2. Release-Notiz ohne die generierte Full-Changelog-Zeile:** GitHub erzeugte den Vergleich ab v1.4.2 (v1.4.3 liegt auf release/1.4.x). B4 trägt bereits die abgenommene Zeile ab v1.4.3 (Link 200); eine zweite, abweichende Zeile wäre irreführend. Der generierte Block What's Changed steht unverändert dahinter.

**3. Ein Beleg-Commit statt zwei:** die Belege von Task 2 und Task 3 stehen in einem Abschnitt und gingen in einen Commit (a4035afc).

**4. Zusätzlicher Commit 6c953a76 (THIRD-PARTY.md):** auf Owner-Wort zu Frage B vor dem Tag, daher steht der Tag auf diesem Commit.

## Known Stubs

Keine.

## Offen

- 36-15 Owner-Abnahme, 36-16 Einreichung; lokaler Commit a4035afc und diese SUMMARY gehen mit dem Owner-Wort in 36-16 hinaus.

## Self-Check: PASSED

- FOUND: Tag v1.5.0 (annotiert) auf 6c953a76, Release mit 9 Assets
- FOUND: Commits 42eaa997, 6c953a76 (auf origin/main), a4035afc (lokal)
- FOUND: Abschnitt "# Release 1.5.0" mit "Verified OK" zweimal und release_tag=v1.5.0 in docs/store-listing.md
