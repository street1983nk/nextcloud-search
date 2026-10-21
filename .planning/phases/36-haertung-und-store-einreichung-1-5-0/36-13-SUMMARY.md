---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 13
subsystem: Versionssprung 1.5.0 und Upgrade-Strecke ab v1.4.3
tags: [rel-05, hart-06, bump, upgrade-proof, corresponding-source]
requires: [36-12]
provides:
  - "Beide info.xml auf 1.5.0, image-tag 1.5.0, CHANGELOG [1.5.0] - 2026-10-21, [Unreleased] leer"
  - "deploy-harp.yml: UPGRADE_FROM_TAG v1.4.3 mit Begründungsabsatz, gesetzt nach dem Bump im selben Commit"
  - "CI-Beweis des Sprungs 1.4.3 -> 1.5.0 auf main (HaRP-Lauf 39584388860)"
  - "Spiegel source-1.5-dev.3 vorbereitet (Quellpakete lokal geholt und geprüft), Veröffentlichung mit 36-14"
affects: [36-14, 36-15, 36-16]
tech-stack:
  added: []
  patterns:
    - "Bump vor UPGRADE_FROM_TAG im selben Commit, Wächtertest prüft die Reihenfolge (F2)"
    - "Meldungen der Upgrade-Zweige über ${UPGRADE_FROM_TAG} statt wörtlicher Version"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-13-SUMMARY.md
  modified:
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - CHANGELOG.md
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_phase36_audit.py
    - backend/tests/test_upgrade_seed_steps.py
    - docs/store-listing.md
decisions:
  - "Version001500Date20261012000000 verwirft backend_app_version bereits (plus markScanStale); sie fehlt im Tag v1.4.3 und läuft beim Update, daher keine neue Migration und keine Owner-Frage"
  - "PHP-Ratsche nicht verschoben: PHP_TREE_HASH_TODAY deckt nur *.php, kein PHP-Byte geändert, test_measurement_scripts.py grün"
  - "Historische 1.4.2-Kommentare in deploy-harp.yml bleiben: v1.4.3 ändert gegenüber v1.4.2 kein Byte unter backend/src, die Aussagen gelten wortgleich"
  - "Spiegel source-1.5-dev.3: Owner 'Anlegen (Empfohlen)', publish erst mit dem nächsten Owner-Wort in 36-14"
metrics:
  duration: "ca. 150 min (ca. 10:00 bis 12:55 Ortszeit), davon 17 min volle Suite und ca. 60 min CI"
  completed: 2026-10-21
  tasks: 3
  files: 7
requirements: [HART-06, REL-05]
---

# Phase 36 Plan 13: Versionssprung 1.5.0 und Upgrade-Strecke ab v1.4.3 Summary

Beide Hälften tragen 1.5.0, die Upgrade-Strecke startet bei der Store-Version v1.4.3, und der HaRP-Lauf 39584388860 auf main belegt den echten Sprung `installed_version went from 1.4.3 to 1.5.0` mit allen zehn Zusicherungen und Zusicherung 11 grün.

## Task 1: Bump und Umstellung (Commit 805308c4)

Vorbedingungen, geprüft am 21.10.2026:
- `gh release view v1.4.3`: kein Pre-Release, Assets findling.tar.gz, findling.tar.gz.sig, findling_backend.tar.gz, findling_backend.tar.gz.sig.
- `docker manifest inspect ghcr.io/street1983nk/findling_backend:1.4.3` anonym: linux/amd64 und linux/arm64 (zwei weitere Einträge unknown/unknown sind Attestierungen).

Migrationsbefund: **ja**. `php/lib/Migration/Version001500Date20261012000000.php` löscht in `postSchemaChange` den Schlüssel `ExAppService::KEY_BACKEND_VERSION` (backend_app_version) im Muster von Version001400 und markiert zusätzlich den Nenner zur Neuzählung (`markScanStale`). `git ls-tree v1.4.3 php/lib/Migration/` endet bei Version001400, die Migration ist für eine 1.4.3-Installation also neu und läuft beim Update. Keine neue Migration, keine Owner-Frage.

Reihenfolge im Commit: zuerst der Bump (beide `<version>1.5.0</version>`, `<image-tag>1.5.0</image-tag>`, CHANGELOG `## [1.5.0] - 2026-10-21` mit dem bisherigen Unreleased-Inhalt), danach `UPGRADE_FROM_TAG: v1.4.3` mit neuem Absatz oben im Begründungsblock; der Absatz zu v1.4.2 bleibt als "from 2026-10-10 until 2026-10-21". Schrittname 2b lautet "judged by the released version", die Meldung des Gleich-Versions-Zweigs nennt `${UPGRADE_FROM_TAG}` und `${new_companion}`; zwei Kommentare zum aktuellen Startpunkt (Kopf der Upgrade-Strecke, Zweigkommentar Store upgrade 4) nachgeführt. Zweiginhalte unverändert.

Lokale Gates: pytest 6208 passed, 264 skipped (17:09 min); ruff check, ruff format --check, pyright (0 Fehler), vulture, reuse lint (2912/2912) grün; PHPL entfällt.

## Task 2: Push und CI-Beweis

Owner-Freigabe (übermittelt durch den Koordinator am 21.10.2026): Auf die Frage "Darf ich `805308c4` auf origin/main pushen?" antwortete der Owner wörtlich: "ja".

`git push origin main`: `7fb6ef7b..805308c4  main -> main`. Läufe des Kopfs 805308c4, alle `success`:

| Lauf | Workflow |
|---|---|
| 39584388860 | HaRP deploy (vier Matrixjobs) |
| 39584389002 | Integration |
| 39584389041 | Python gates |
| 39584388899 | PHP and store metadata gates |
| 39584388914 | Multi-arch image |
| 39584388940 | Security scans |
| 39584388861 | Resilience |
| 39584388953 | OpenSSF Scorecard |

Zitate aus Job 119169558348 (stable34, ubuntu-24.04):
- Store upgrade 1: `the companion of the release carries version 1.4.3`
- Store upgrade 4: `the instance has findling installed at 1.4.3`, `the companion of this commit carries version 1.5.0`, `occ upgrade answered 0`, `installed_version went from 1.4.3 to 1.5.0`, `the instance performed the app update: 1.4.3 to 1.5.0` (Zweig verschiedener Versionen)
- Store upgrade 5: `the seed is caught up: recheck_1_5_0 read done 303s and every word found exactly its file 354s after the end of Store upgrade 4`, `all ten assurances hold`
- Store upgrade 5b: `--- 11a, the prefix of v1.4.3 still holds ---` bis `11d`, `all parts of assurance 11 hold`

Kein roter Lauf, keine Wiederholung nötig.

## Task 3: Spiegel source-1.5-dev.3 (Commit 2c379a47)

Owner-Entscheid (übermittelt durch den Koordinator): wörtlich "Anlegen (Empfohlen)", mit der zugesagten Einschränkung: Quellpakete nur lokal holen und prüfen, `publish --tag source-1.5-dev.3` erst mit dem nächsten Owner-Wort in 36-14.

Ausgeführt: `corresponding_source.py fetch` und `--verify-only` auf
`C:/Users/Student/AppData/Local/Temp/claude/C--Users-Student/dabf848d-eca9-4ddd-860f-5622518b597f/scratchpad/source-1.5-dev.3`, beide Exitcode 0, alle vier "ok":
- pillow_heif-1.8.1.tar.gz 521ebffb8a181d56c3904e5a61f20903edee0d9d3275967b8fb345f866215c06
- x265_4.3.tar.gz 83c53e4c8bbb8f1e33ed59e10a7d621d1d7801ca853910c3eb41f038b8ffb121
- libde265-1.1.3.tar.gz 554228bd17788c99a7e63b37ab5634722190e6e2bf60c1dcb01cef328e133905
- libheif-1.23.6.tar.gz 4484346dc5995319dbc11e3a1c35d0a2ec46511ce370900869337fd2c7033125

docs/store-listing.md trägt den offenen Punkt "Spiegel `source-1.5-dev.3` für das dev-Image: vorbereitet, Veröffentlichung mit 36-14" mit den Folgeschritten (publish, download in frisches Verzeichnis, `--verify-only`). Nicht veröffentlicht, nicht gepusht.

## Deviations from Plan

**1. [Rule 3 - Blocking] Zwei Tests an den Bump angepasst**
- Found during: Task 1
- Issue: `test_phase36_audit.py` suchte die Zeile "Similar documents" unter [Unreleased], `test_upgrade_seed_steps.py` erwartete `UPGRADE_FROM_TAG == v1.4.2`.
- Fix: Lesen unter [1.5.0]; Erwartung v1.4.3, die Kommentar-only-Prüfung gilt jetzt für 1.3.2 und 1.4.2.
- Files: backend/tests/test_phase36_audit.py, backend/tests/test_upgrade_seed_steps.py
- Commit: 805308c4

**2. PHP-Ratsche ohne Journalabsatz:** Der Plan sah "Moved on ... version 1.5.0" vor; der Baumhash deckt nur `*.php`, kein PHP-Byte geändert, Test grün. `backend/tests/test_measurement_scripts.py` daher unverändert.

**3. Zeilennummern:** die im Plan genannten Stellen 5310 bis 5343 lagen bei ca. 5471 und 5504.

**4. Task 3 eingeschränkt:** auf Owner-Zusage kein `publish`, nur lokale Prüfung; Abschluss in 36-14.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: backend/appinfo/info.xml (1.5.0), php/appinfo/info.xml (1.5.0), deploy-harp.yml (UPGRADE_FROM_TAG: v1.4.3), CHANGELOG [1.5.0] - 2026-10-21
- FOUND: Commits 805308c4 (auf origin/main), 2c379a47 (lokal)
- FOUND: geprüfte Quellpakete im Scratch-Pfad oben
