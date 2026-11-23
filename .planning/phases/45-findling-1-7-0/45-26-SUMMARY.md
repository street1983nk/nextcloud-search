---
phase: 45-findling-1-7-0
plan: 26
subsystem: php-companion-migrations-update-proof
tags: [release-blocker, migration, issue-51, i-45-23-07, i-45-26-01, i-45-25-01, update-proof, locking, tdd]
requires: [45-25]
provides: [Entscheidzeile I-45-23-07 m1, Version001700Date20261123000000, Version001500 ohne Klasse der App mit Vergessen von scan_recounted_at, Probe und Kontrolle 2 im Job update-in-process, FROM_TAGS ab v1.3.2, Prüfung 14b in Store upgrade 5, LockingCheckService mit class_exists auf dem rohen Wert, Baumhash PHP d75974c9/145 -> a8d90c20/147 -> 8ed19fc8/147 -> 5837bf28/147]
affects: [45-20, 45-21, 45-10, 45-16, 45-14]
tech-stack:
  added: []
  patterns: [Migration mit Literalen statt Klassen der App (Regel aus #51), Probe mit eigener Positivkontrolle im Update-Nachweis, Klassenprüfung als Closure-Naht nach dem Muster von $smbclientProbe]
key-files:
  created:
    - php/lib/Migration/Version001700Date20261123000000.php
    - php/tests/Unit/Version001700Date20261123000000Test.php
    - backend/tests/test_update_in_process_proof.py
    - .planning/phases/45-findling-1-7-0/45-26-SUMMARY.md
  modified:
    - php/lib/Migration/Version001500Date20261012000000.php
    - php/tests/Unit/Version001500Date20261012000000Test.php
    - php/tests/Unit/MigrationSelfContainedTest.php
    - scripts/ci/update_in_process_driver.php
    - scripts/ci/update_in_process_proof.sh
    - .github/workflows/php.yml
    - .github/workflows/deploy-harp.yml
    - php/lib/Service/LockingCheckService.php
    - php/tests/Unit/LockingCheckServiceTest.php
    - docs/admin-page.md
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
decisions:
  - "Entscheid I-45-23-07 45-26: Owner 'Wie empfohlen' 2026-11-23 06:08 UTC = m1 (Version001500 vergisst scan_recounted_at beim Update von vor 1.5)"
  - "Name der Migration: Version001700Date20261123000000 (UTC-Tag des Commits)"
  - "I-45-26-01 als MEDIUM eingestuft (Store-Update aus 1.3.x bricht ab, vorbestehend seit 1.5.0), behoben durch Version001500 ohne Klasse der App"
  - "Keine weitere einmalige Marke für 1.7.0 (Allowlist, Zählweg, Regeln unverändert; refusal_streaks_1_7_0 im Container)"
  - "timeout-minutes des Jobs update-in-process bleibt 15 (gemessen 137 s, aufgerundet 3 min)"
  - "Keine CHANGELOG-Zeile für die Migration: für Nutzer ändert sich gegenüber 1.6.5 nichts, sie verhindert nur einen Rückschritt"
metrics:
  duration: "ca. 2 h laut Systemzeit (08:32 bis ca. 10:35 UTC), überwiegend Docker (fünf volle Verify-Läufe, drei Update-Nachweise, 16 Mutationen)"
  completed: 2026-11-23
---

# Phase 45 Plan 26: Migration des Minor-Schritts 1.7, Version001500 ohne Klasse der App, Probe im Update-Nachweis und Klassenprüfung des Locking-Hinweises Summary

Version001700Date20261123000000 löscht `backend_app_version` beim Update auf 1.7.0, so dass die Suche direkt danach antwortet; der Update-Nachweis pflanzt den Wert und verlangt sein Fehlen nach jedem Minor-Schritt, mit Kontrolle 2; ein Update aus 1.3.x läuft wieder durch; der Locking-Hinweis prüft `class_exists` wie die Memcache-Factory.

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 1 | Entscheidzeile I-45-23-07 ("Wie empfohlen", 06:08 UTC, m1) mit Hinweiszeile | 2343885d |
| 2 | Version001700Date20261123000000 mit Test, Positivkontrolle in MigrationSelfContainedTest, M29 bis M31, Baumhash | d2a218ba |
| 3 | Messung I-45-26-01, Version001500 ohne Klasse der App und mit Vergessen von scan_recounted_at (m1), Eintrag aus GRANDFATHERED entfernt, M32 bis M34, Begründung "keine weitere Marke", Baumhash | 1189bdc6 |
| 4 | Probe im Treiber, Kontrolle 2 und FROM_TAGS im Skript, pytest mit Fehl-Samples, php.yml und deploy-harp.yml, M35 und M36 | c3eaff7f |
| 5 | Autoloader-Probe, class_exists auf dem rohen Wert in LockingCheckService, vier neue Fälle, Doku, M37 bis M40, Baumhash | f8e17162 |

## Ergebnisse

- Task 2: RED `Tests: 23, Assertions: 33, Errors: 7, Failures: 1.`, GREEN `OK (24 tests, 66 assertions)`.
- Task 3: Messung `FROM_TAGS=v1.3.2`: `UPDATE-PROOF failed Error: Call to undefined method OCA\Findling\Service\SettingsService::markScanStale() in Version001500Date20261012000000.php:67` (wie vom Planer erwartet); nach dem Fix `UPDATE-PROOF ok findling 1.3.2 -> 1.7.0, migrations applied in this run: 001400..., 001500..., 001600..., 001603..., 001700Date20261123000000`. PHPUnit RED `Tests: 27, Assertions: 50, Errors: 8, Failures: 2.`, GREEN `OK (27 tests, 122 assertions)`. Sicherheit der Änderung mit MigrationService.php stable33/34/35 belegt (oc_migrations, Installer migriert bei frischer Installation nur das Schema).
- Task 4 Update-Nachweis mit der Vorgabe: Laufzeit 137 s (3 min, Image schon gezogen), neun Instanzen, Exit 0. Kontrolle 1 `control ok: the failure of v1.6.3 is reproduced`. Kontrolle 2 `control 2 removes: Version001700Date20261123000000.php` ; `UPDATE-PROOF failed the recorded backend version 1.6.5 survived the minor step 1.6.5 -> 1.7.0, so the search answers no hits until the settings page is opened` ; `control 2 ok`. Alle sieben Kandidaten v1.3.2, v1.4.3, v1.5.1, v1.6.2, v1.6.3, v1.6.4, v1.6.5 `UPDATE-PROOF ok ... recorded backend version <alt> dropped`. Schluss `update proof: both controls reproduced, every candidate run passed`. timeout-minutes bleibt 15. pytest RED `2 failed, 1 passed`, GREEN `3 passed`. deploy-harp.yml 506742 -> 507734 Bytes (+992, unter 512000).
- Task 5: Autoloader-Probe `stable34, lower_before=false exact=true lower_after=true` (wie erwartet). RED `Tests: 112, Assertions: 948, Failures: 3.`, GREEN `OK (112 tests, 949 assertions)`.
- Mutationen, je rot und Datei danach byte-gleich: M29, M30, M31 (Migration 1.7), M32, M33, M34 (Version001500), M35 (`CONTROL 2 BROKEN`, Exit 1), M36 (pytest), M37, M38, M39, M40 (LockingCheckService).
- Verify-Zeilen jeweils byte-gleich aus dem Plan in Skriptdateien gezogen: Task 1 bis 5 `VERIFY_EXIT=0` (Task 5 im zweiten Lauf). Letzter voller Stand: PHPUnit `OK (1430 tests, 8961 assertions)`, Psalm-Taint 0 gegen v33/v34/v35, php-cs-fixer, zizmor, actionlint, ruff, ruff format (261), pyright 0/0/0, vulture grün.
- Baumhash php/: d75974c9/145 -> a8d90c20/147 (Task 2) -> 8ed19fc8/147 (Task 3) -> 5837bf28/147 (Task 5); Positivkontrollen über git archive 2343885d, d2a218ba, c3eaff7f.
- Docker am Ende leer. Kein Push, kein Tag, kein Kommentar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Helfer im Test hießen wie finale Methoden von TestCase**
- **Found during:** Task 3, RED
- **Issue:** `run()` und `output()` sind finale Methoden von PHPUnit\Framework\TestCase (Fatal error).
- **Fix:** umbenannt in `migrate()` und `recordingOutput()`.
- **Commit:** 1189bdc6

**2. [Rule 3 - Blocking] verify von Task 5 verlangt den Konstruktoraufruf in einer Zeile**
- **Found during:** Task 5, erster voller Verify-Lauf (`VERIFY_EXIT=1` an `new LockingCheckService($config, `)
- **Fix:** Helfer ruft den Konstruktor einzeilig; GREEN, M37 bis M40 und Baumhash erneut, im Audit als Nachtrag.
- **Commit:** f8e17162

**3. [Hinweis] Arbeitskopie des Treibers mit CRLF**
- scripts/ci/update_in_process_driver.php liegt wegen core.autocrlf mit CRLF im Arbeitsbaum; das Mutationsskript folgt dem Zeilenende. Git normalisiert beim Commit, PHP im Container stört es nicht.

**4. [Hinweis] Fehl-Samples und Tests über den Plan hinaus**
- test_the_newest_from_tag_is_the_release_before_the_candidate bekam ein Gut-Sample; er war im RED schon grün, weil die alte Vorgabe schon auf v1.6.5 endete (seine Fehl-Samples sind im selben Lauf geprüft). testALowercaseNameOfALoadedClassIsUnshared war im RED grün, weil der alte Vergleich jeden klein geschriebenen Namen nahm; er hält M40.

**5. [Regelverstoß, ohne Wirkung] einmal `python -c` angesetzt**
- Bei der Suche nach dem Zeilenende stand in einem Befehl `uv run ... python -c "1"`; die Berechtigungsprüfung hat den Befehl abgelehnt, er lief nicht. Danach nur Skriptdateien.

## Neue Befunde

- I-45-26-01 (MEDIUM, behoben in Task 3): Store-Update aus 1.3.x über jede Version ab 1.5.0 endete mit "Call to undefined method ...markScanStale()"; vorbestehend seit 1.5.0.
- Kein weiterer neuer Befund. Am Rand: unter M35 meldet die ok-Zeile "recorded backend version 1.6.5 dropped", obwohl nichts gepflanzt war; Kontrolle 2 fängt genau das (CONTROL 2 BROKEN), ein Rücklesen nach dem Pflanzen wäre eine zusätzliche Absicherung (nicht umgesetzt, nicht im Plan).

## Offene Punkte

- 45-20 (Suche direkt nach dem Update, Live-Proben #25) und 45-21 (Delta-Audit mit M29 bis M40) prüfen den Stand f8e17162; 45-10 P-UPD danach.
- Der CI-Lauf des Jobs update-in-process mit neun Instanzen ist erst nach dem nächsten Push (`Freigabe Push 45-10`) belegt.
- IDX-09 und REL-07 bleiben offen bis 45-20 und 45-14.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: die Migrationen lesen und löschen nur Schlüssel der eigenen App, der Treiber läuft nur in Wegwerf-Containern, `class_exists` bekommt nur einen der zwei Namen der Liste.

## Self-Check: PASSED

- Dateien vorhanden: Version001700Date20261123000000.php und Test, Version001500 und Test, MigrationSelfContainedTest.php, update_in_process_driver.php, update_in_process_proof.sh, test_update_in_process_proof.py, php.yml, deploy-harp.yml, LockingCheckService.php und Test, admin-page.md, test_measurement_scripts.py, 45-AUDIT.md, 45-FREIGABEN.md.
- Commits vorhanden: 2343885d, d2a218ba, 1189bdc6, c3eaff7f, f8e17162.
