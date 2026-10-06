---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 15
subsystem: release
tags: [release, tag, signing, store, belegkette]
requires: [29-14]
provides: [tag v1.4.0, signierte Assets 1.4.0, Manifestindex 1.4.0, Release-Notiz 1.4.0, Belegkette Zeilen 1-5]
affects: [29-16]
tech-stack:
  added: []
  patterns: [Tag nur nach woertlichem Owner-Wort, nur das Tag gepusht, Signatur-Gegenprobe gegen Upstream-Zertifikate]
key-files:
  created: []
  modified: [docs/audits/2026-10-phase-29/README.md]
decisions:
  - "Tag v1.4.0 annotiert auf 99326ae2, nur das Tag gepusht; main bleibt lokal vor (28db8119, 4d7df4e8 und dieser SUMMARY-Commit)"
  - "Release-Notiz: abgenommene Faktenliste mit dem in Teil 6 vorab vereinbarten Zusatz 'and on the admin page', weil die Zeile Error class auf der Verwaltungskarte gebaut ist"
metrics:
  duration: ~35 min
  completed: 2026-10-06
requirements: [REL-04]
---

# Phase 29 Plan 15: Tag v1.4.0, Release-Lauf und Belegkette 1-5 Summary

v1.4.0 ist als signiertes Paar (beide Hälften "Verified OK", im CI und lokal gegen die Upstream-Zertifikate) mit Multi-arch-Abbild (linux/amd64 + linux/arm64) veröffentlicht; Release-Notiz ist die abgenommene englische Faktenliste mit Dank an budachst.

## Task 1: Owner-Wort (Checkpoint)

- Frage des Orchestrators, wörtlich: "Gibst du das Wort fuer Tag v1.4.0 auf 99326ae2?" (nach komplettem CI-Grün auf 99326ae2, Läufe 37467788135, 37467788091, 37467788076, 37467788060, 37467788007, 37467787904)
- Antwort des Owners, wörtlich: "go" (06.10.2026)
- Deckt: Tag v1.4.0 auf 99326ae2 und dessen Push. Deckt keinen Push von main.

## Task 2: Tag, Release-Lauf, Belegkette

- Tag: `git tag -a v1.4.0 -m "Findling 1.4.0" 99326ae2...`, Tag-Objekt `0959338252e6`, `git rev-list -n 1 v1.4.0` = `99326ae2667ddc243456f7787f1010efd500e357`; Remote `^{}` identisch
- Push: nur `refs/tags/v1.4.0`; `origin/main` steht weiter auf 99326ae2
- Sieben Tag-Läufe success, keiner wiederholt:
  - Release archives for the app store **37470623070**
  - PHP and store metadata gates **37470623202**
  - Multi-arch image **37470623060**
  - HaRP deploy **37470623144**
  - Python gates **37470623033**
  - Integration **37470623360**
  - Resilience **37470623071**
- Assets (4): findling.tar.gz 529.651 B, findling.tar.gz.sig 684 B, findling_backend.tar.gz 33.663 B, findling_backend.tar.gz.sig 684 B
- "Verified OK" zweimal im Lauflog; lokal unabhängig nachgeprüft mit frisch geholten Zertifikaten (CN=findling, CN=findling_backend); Archive tragen 1.4.0 und image-tag 1.4.0
- Manifestindex anonym: `application/vnd.oci.image.index.v1+json`, linux/amd64, linux/arm64 (+ 2x unknown/unknown Attestations)
- Release-Notiz per `gh release edit --notes-file`, Kopf = Faktenliste, darunter die generierten Notizen; budachst und #18 genannt
- Belegkette Zeilen 1-5 + Liste der sieben Läufe im Auditbericht, Commit **4d7df4e8** (lokal)

## Deviations from Plan

- Release-Notiz: Zusatz "and on the admin page" in der Fehlerklassen-Zeile. Nicht frei erfunden, sondern die in store-listing.md Teil 6 vorab abgenommene Bedingung ("kommt die Zeile auf der Verwaltungskarte dazu, ergänzt 29-15 'and on the admin page'"); die Zeile existiert in php/js/admin.js und wurde in der Owner-Playwright-Runde gesehen.
- Sonst keine.

## Nicht gepusht (wartet auf nächsten gedeckten Push, 29-16)

- 28db8119 (SIGKILL-Beleg, vorher schon lokal), 4d7df4e8 (Belegkette), SUMMARY-Commit dieses Plans

## Keine Store-Einreichung

Die Einreichung ist Plan 29-16.

## Self-Check: PASSED

- FOUND: docs/audits/2026-10-phase-29/README.md (Abschnitt "Die Belegkette der Abgabe v1.4.0")
- FOUND: Commit 4d7df4e8
- FOUND: Tag v1.4.0 lokal und remote auf 99326ae2
- FOUND: 4 Release-Assets
