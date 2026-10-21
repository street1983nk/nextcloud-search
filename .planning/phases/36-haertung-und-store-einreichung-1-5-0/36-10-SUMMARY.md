---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 10
subsystem: CI-Upgrade-Strecke (deploy-harp.yml)
tags: [hart-06, f5, sc2, d-33-01, d-36-13, exclusions, upgrade-line]
requires: [36-09]
provides:
  - "Store upgrade 2b sät unter v1.4.2 einen Präfix-Ausschluss Ausschluss36 (occ config:app:set findling exclusions, Typ array, Format aus v1.4.2:php/lib/Service/ExclusionService.php:173) vor jedem Upload, dazu Ausschluss36/a.txt, kontrolle36.txt und muster36.geheim36.txt, fail closed geprüft"
  - "GITHUB_ENV: UPGRADE_EXCLUSIONS_BEFORE, UPGRADE_EXCL_EXCLUDED_ID, UPGRADE_EXCL_CONTROL_ID, UPGRADE_EXCL_PATTERN_ID (je per [[ =~ ]] geprüft, L-30-03)"
  - "Neuer Schritt Store upgrade 5b (Zusicherung 11): Präfix wirkt nach dem Upgrade, Präfixliste unverändert lesbar, Muster *.geheim36.txt der 1.5 nimmt den Treffer nach einem Abgleich-Zyklus heraus (D-33-01), Kontrolle bleibt, Muster wieder entfernt und Datei per zweitem Zyklus zurück im Index"
  - "Gate-Tests in backend/tests/test_upgrade_seed_steps.py für Saat und Schritt 5b"
affects: [36-13]
tech-stack:
  added: []
  patterns:
    - "Abgleich-Zyklus im laufenden Container per docker exec und Reconcile(min_interval_hours=0).run_once(), wie im reconcile-and-dach-Job von integration.yml"
    - "Admin-Handlungen (Muster setzen) in eigenem Schritt neben den zehn admin-freien Zusicherungen (SC4 bleibt gültig)"
key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
decisions:
  - "Zusicherung 11 steht als eigener Schritt Store upgrade 5b statt in Store upgrade 5: der bestehende Gate-Test test_the_assurance_step_does_nothing_an_admin_would_do hält fest, dass Schritt 5 nichts tut, was ein Admin tut; ein Muster setzen ist genau das. Schritt 5 und sein Name (ten assurances) bleiben unverändert"
  - "Musterdatei heißt muster36.geheim36.txt, Muster *.geheim36.txt: eine unbekannte Endung wäre application/octet-stream und würde von der Allowlist der 1.4.2 nie indexiert, das Muster nähme dann einen Treffer heraus, den es nie gab"
  - "Erfundene Suchwörter (sperrquolvane, kontrollbrisetum, mustertavelor) statt der Komposita aus dem Plan: zerfallen in nichts aus der deutschen Wortliste, jedes Wort kann nur seine Datei finden"
  - "Präfix wird VOR den Uploads gesetzt, damit kein Fenster entsteht, in dem a.txt unter 1.4.2 erst indexiert wird"
  - "Muster per occ (zweiter Schreiber, den patterns() normalisiert), Wirkung über das Netz von D-33-01 (Abgleich), nicht über die Admin-Route (POST mit CSRF ohne Session)"
  - "UPGRADE_FROM_TAG bleibt v1.4.2 (D-36-13, Umstellung in 36-13)"
metrics:
  duration: "ca. 75 min (davon ca. 45 min CI)"
  completed: 2026-10-21
  tasks: 2
  files: 2
---

# Phase 36 Plan 10: Ausschlüsse in der Upgrade-Strecke Summary

Die Upgrade-Strecke trägt jetzt einen unter v1.4.2 gesetzten Präfix-Ausschluss durchs Upgrade und belegt danach, dass ein Muster der 1.5 nach einem Abgleich-Zyklus seinen Treffer entfernt, während die Kontrolle bleibt (Befund F5, Erfolgskriterium 2).

## Was gebaut wurde

**Task 1, Store upgrade 2b (Commit b333dd29):** Am Ende der Saat unter der alten Version:
- Präfixliste `["Ausschluss36"]` per `occ config:app:set findling exclusions --type=array`, Format aus `git show v1.4.2:php/lib/Service/ExclusionService.php` (Zeile 173: `getValueArray` auf `KEY_EXCLUSIONS`).
- Danach MKCOL und WebDAV-Uploads: `Ausschluss36/a.txt`, `kontrolle36.txt`, `muster36.geheim36.txt`.
- Warten mit dem Drain-Budget, bis die Kontrolle und die Musterdatei mit Vektoren indexiert sind.
- Fail closed: a.txt hat keine Zeile in state.db, findling_file_state oder Queue. Ihr Wort findet nichts, die beiden anderen Wörter finden genau ihre Datei.
- Liste und drei IDs gehen geprüft in GITHUB_ENV.

**Task 2, Store upgrade 5b (Commit 24c27454):** Neuer Schritt direkt nach den zehn Zusicherungen:
- 11a: Das Präfix wirkt (Wort findet nichts, Kontrolle genau ihre Datei, a.txt ohne Zeile in state.db).
- 11b: `config:app:get findling exclusions` gleich `UPGRADE_EXCLUSIONS_BEFORE`.
- 11c: Muster `*.geheim36.txt` per occ in `exclusion_patterns` (Typ array). Ein Abgleich-Zyklus im Container markiert die bekannte Datei als Arbeit, describe() macht daraus den Löschauftrag, und die Datei wird mit einem Tombstone markiert. Danach findet ihr Wort nichts mehr, die Kontrolle bleibt.
- 11d: Muster gelöscht, zweiter Zyklus, Datei wieder indexiert mit Vektoren und gefunden. Die Schritte 6/7 starten damit vom unveränderten Stand.
- Zeile im Step Summary: "exclusions: prefix kept, pattern applied ...".

## Beleg CI (Commit 24c27454)

- HaRP deploy **39557497418** grün, alle vier Beine. stable34/ubuntu-24.04, alle Store-upgrade-Schritte `success`: 0, 1, 2, 2b, 3, 3b, 3c, 4, 5, **5b**, 6, 7.
- Log 2b: `the prefix list of v1.4.2 reads ["Ausschluss36"]`; `on v1.4.2 the word under the prefix finds nothing, the control and the pattern word find exactly their file`.
- Log 5b: `unchanged the prefix list = ["Ausschluss36"]`; Zyklus 1 `{"state": "walked", "seen": 313, "stale": 1, "missing": 0}` (genau die Musterdatei); `the pattern file is tombstoned and its word finds nothing`; Zyklus 2 ebenfalls `stale: 1`; `the pattern file is indexed again with 1 chunk(s) and found`.
- Ebenfalls grün: Python gates 39557497338, Integration 39557497494, Resilience 39557497380, Multi-arch image 39557497425, Security scans 39557497334, OpenSSF Scorecard 39557497544.
- Lokal: test_upgrade_seed_steps, test_language_proof_steps, test_phase31_audit, test_lockstep_versions und weitere Workflow-Tests: 914 passed. `-k "workflow or deploy_harp or harp"`: 50 passed. ruff check/format und pyright für die Testdatei grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Zusicherung 11 als eigener Schritt 5b statt in Schritt 5**
- **Found during:** Task 2
- **Issue:** `test_the_assurance_step_does_nothing_an_admin_would_do` verbietet in Store upgrade 5 jeden occ-Aufruf außer `findling:index |` und jede Containerhandlung (SC4: Upgrade ohne Admin). Muster setzen und ein Zyklus per docker exec verletzen das.
- **Fix:** Neuer Schritt `Store upgrade 5b, the exclusions carried through the upgrade` mit gleicher Bedingung zwischen 5 und 6. Die Summary-Zeile steht in 5b, weil der Summary-Block von 5 vor 5b geschrieben wird. Zählerprüfungen von 5 brauchten keine Korrektur, weil die drei Dateien vor dem Snapshot von Schritt 3 gesät werden und so auf beiden Seiten stehen.
- **Files modified:** .github/workflows/deploy-harp.yml, backend/tests/test_upgrade_seed_steps.py
- **Commit:** 24c27454

**2. [Rule 1 - Bug] Dateiname und Muster `muster36.geheim36.txt` / `*.geheim36.txt` statt `muster36.geheim36` / `*.geheim36`**
- **Found during:** Task 1
- **Issue:** Die Endung `.geheim36` wäre application/octet-stream. Die Allowlist der 1.4.2 hätte die Datei nie indexiert, und die Prüfung "Musterwort findet genau seine Datei" wäre nie grün geworden.
- **Fix:** Endung `.txt`, Muster entsprechend.
- **Commit:** b333dd29

**3. [Rule 1 - Bug] Erfundene Suchwörter statt Komposita**
- **Found during:** Task 1
- **Issue:** `ausschlusswortsechsunddreissig` und die beiden anderen Wörter zerfallen über die deutsche Kompositum-Wortliste in gängige Wörter (wort, sechs, dreissig). Damit hängt "genau eine Datei" an der Abfragesemantik.
- **Fix:** `sperrquolvane`, `kontrollbrisetum`, `mustertavelor`. Vorher wird geprüft, dass jedes Wort nichts findet.
- **Commit:** b333dd29

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: .github/workflows/deploy-harp.yml (Ausschluss36, UPGRADE_EXCLUSIONS_BEFORE, kontrollbrisetum, exclusion_patterns)
- FOUND: b333dd29, 24c27454
- UPGRADE_FROM_TAG: v1.4.2 unverändert
