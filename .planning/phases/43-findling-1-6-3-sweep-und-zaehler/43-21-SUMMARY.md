---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 21
subsystem: php/Service, backend/tests, scripts/dev
tags: [D-43-15, D-43-17, OE-1, OE-2, OE-3, OE-4, OE-6, share-identity, counting]
requires: [43-20]
provides: [StorageService::shareIdentity, StorageService::shareIdentities, StorageService::shareIdentityStats, countingKeyGroups nach Freigabe, Katalog share_identity_cases.json]
affects: [43-22, 43-23, 43-27]
tech-stack:
  added: []
  patterns: [md5-Gegenprobe einer aus der Konfiguration nachgebauten Speicher-ID, gemeinsamer Fall-Katalog PHP/Python]
key-files:
  created:
    - backend/tests/fixtures/share_identity_cases.json
    - backend/tests/test_share_identity_cases.py
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-21-SUMMARY.md
  modified:
    - php/lib/Service/StorageService.php
    - php/tests/Unit/StorageServiceTest.php
    - backend/tests/test_measurement_scripts.py
    - scripts/dev/phpunit_docker.sh
decisions:
  - "Zählerdefinition shareIdentityStats: parsed = ausgeschriebene IDs mit Identität; hashedVerified = gehashte IDs mit md5-Treffer und Identität; hashedUngrouped = gehashte IDs mit mindestens einem smb/sftp-Mount von files_external ohne Treffer (bei Abfragefehler alle gehashten IDs); placeholder = Teilmenge von hashedUngrouped, bei der ein Kandidat wegen eines '$' außer '$user' verworfen wurde; excluded = smb/sftp-IDs (ausgeschrieben oder mit md5-Treffer nachgebaut), die shareIdentity verweigert"
  - "Gehashte IDs ohne smb/sftp-Mount von files_external (lange local-, WebDAV-IDs, andere Provider) zählen in keinem Zähler, wie ein Home: kein falscher warning-Anlass in 43-23"
  - "Login-Kandidaten je Mount: konfigurierter user (bei SMB nach splitUser) und oc_mounts.user_id; Nachbau exakt nach SMB.php/SFTP.php getId, SFTP mit splitHost (parse_url), Port-Option, cleanPath aus Common.php (stable34 :433-448)"
  - "Fehler einer Abfrage auf oc_mounts/oc_external_*: catch \\Exception (nicht Throwable), Warnung nur mit Anzahl und Exception-Klasse"
metrics:
  started: 2026-11-09T10:40:00Z
  completed: 2026-11-09T11:25:00Z
  tasks: 3
  files: 6
---

# Phase 43 Plan 21: Eine Freigabe-Identität je Speicher

Jeder SMB- und SFTP-Speicher bekommt eine Freigabe-Identität {share, root}: Host und Freigabename ASCII-klein, die Wurzel getrennt, ungefaltet und in NFC; lange (md5-gekürzte) IDs nur über die Konfiguration von files_external mit exakter md5-Gegenprobe. Die Zählgruppen entstehen nach Freigabe ohne Wurzel, die mbozem-Lage (47 Speicher) ist eine Gruppe.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Owner-Entscheide OE-1 bis OE-8, alle a (vor diesem Lauf erledigt) | 662e7b63 |
| 2 | RED: Katalog, Python-Test, StorageServiceTest, lokaler PHPUnit-Weg für Kataloge | 38d2e375 |
| 3 | GREEN: shareIdentity, shareIdentities, shareIdentityStats, Gruppierung nach Freigabe, PHP-Baumhash | f772dbb5 |

## Belege

- **RED lokal** (`scripts/dev/phpunit_docker.sh --filter StorageServiceTest`, freier RAM 4,0 GB): 26 Tests, 12 Errors (9x undefined method shareIdentities, 3x shareIdentity), 5 Failures (Gruppen und countingKey in alter Bedeutung). Ein erster RED-Lauf fand den Katalog im Container nicht (siehe Abweichung 1); der gültige RED-Beleg ist der zweite Lauf.
- **GREEN lokal** (RAM 4,0 GB): StorageServiceTest 26 Tests, 673 Assertions, OK. Volle Suite ohne Filter (RAM 4,3 GB): 1154 Tests, 7258 Assertions, OK (Boden 28).
- **Gegenprobe (Negativkontrolle)**: md5-Vergleich auf `true` und homes-Regel auf `false` mutiert, StorageServiceTest: 4 Failures (Katalogfälle, gehashte Einträge, Zähler, zweiter Aufruf). Datei danach wiederhergestellt (cmp identisch), erst dann committet.
- **pytest**: tests/test_share_identity_cases.py 52 grün; mit test_measurement_scripts.py, test_phase40_audit.py, test_allowlist_parity.py, test_exclusion_path_space.py zusammen 736 grün, 7 übersprungen.
- **Python-Gates** vor jedem Commit: ruff check grün, ruff format 256 Dateien sauber, pyright 0/0/0, vulture 0.
- **md5-Werte**: alle zehn per `printf '%s' '<actual>' | md5sum` gerechnet, im Python-Test mit hashlib unabhängig nachgerechnet.
- **PHP-Baumhash**: 20dac366 -> b3f9109f1542f248223f3ed21ef924214c1f9dc2d2dc56f0fd38e72653ad561f, 129 Dateien; Rezept 40b-baumhash.py und unabhängig find/sort/tr/sha256sum beide b3f9109f; dieselbe Pipeline über `git archive` vor dem Plan: 20dac366. PACKAGE-Paar und eingefrorenes PHP_FILES/PHP_TREE_HASH unberührt.
- **Sicherheit**: oc_external_config nur mit `key IN (host, share, root, user, port)`, Test prüft die Parameter (kein 'password', kein `*`, auch wenn eine password-Zeile in der Tabelle steht); Log-Test sucht jeden Host, jede Freigabe, Wurzel und jeden Anmeldenamen des Katalogs in allen Logzeilen, auch in den Fehlerpfaden. Allowlists: shareIdentities( nur in StorageService/DocKeyService/AdminViewService, docKeyOf(/docKeysFor( nur in DocKeyService/FileStateService/QueueService/ReconcileController, keine der fünf Zählfunktionen in SearchService, PathResolverService, Search/, GatewayController, Listener/ (mit Positivkontrolle).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Lokaler PHPUnit-Weg fand die Kataloge unter backend/tests/fixtures nicht**
- **Found during:** Task 2 (erster RED-Lauf)
- **Issue:** scripts/dev/phpunit_docker.sh spiegelte nur php/ in den Container; StorageServiceTest (und ebenso DocKeyServiceTest, CoverageTopologyParityTest) suchen den Katalog über FINDLING_REPO_ROOT oder findling-src, das gibt es lokal nicht.
- **Fix:** backend/tests/fixtures wird schreibgeschützt nach /findling-repo/backend/tests/fixtures eingehängt, FINDLING_REPO_ROOT=/findling-repo gesetzt. Nur Entwicklungswerkzeug, kein Produktcode, kein CI-Workflow.
- **Files modified:** scripts/dev/phpunit_docker.sh
- **Commit:** 38d2e375

**2. [Rule 1 - Testanpassung] Bestehende countingKey-Tests auf die neue Bedeutung umgestellt**
- testARootWithTheUserInItIsNeverAGroup nutzte die ID-Form `//team/anna/` (kein `//` zwischen Freigabe und Wurzel, nicht die Form von SMB.php) und verlangte "keine Gruppe"; ersetzt durch testRootsWithTheUserInThemAreOneShareWithTwoRoots in echter Form (`//team//anna/`): eine Gruppe, Wurzeln getrennt (D-43-15, Dokumentschlüssel trennt sie ab 43-22).
- countingKey ohne Wurzel und ohne `//`-Ende, SFTP mit Anmeldename (OE-4 a): Erwartungen in drei Tests entsprechend; Hash-Test umbenannt (ohne passende Konfiguration nie Gruppe).

Sonst plangemäß. Keine STOPP-Regel berührt: keine Migration, kein Schema, kein Meta- oder AppConfig-Schlüssel, keine Route, kein sichtbarer Satz; neue Abfragen nur rein lesend nach A-3.

## Bekannte Grenzen und offene Punkte

- **Zwischenzustand bis 43-23:** countingKeyGroups gruppiert jetzt Unterwurzeln derselben Freigabe; der Nenner (größtes Mitglied vertritt die Gruppe, ScanStatsService::leftOutMembers) und die Schlüssel von rc.1 sind darauf erst mit 43-22/43-23 abgestimmt. Unveröffentlicht, nur lokal; nicht einzeln ausliefern.
- **Versteckte Freigaben mit '$'** (z. B. `Daten$`, Windows-Admin-Freigaben): bei gehashter ID nach Planregel "jedes andere '$' heißt keine Identität" nie gruppiert (Zähler placeholder, warning in 43-23). Ausgeschriebene IDs solcher Freigaben werden normal gruppiert. Sichere Richtung; ob die Regel enger werden soll (md5-Gegenprobe schützt allein), wäre ein Owner-Entscheid für 43-12 Runde 2.
- **Docker-Daemon:** A-4 sagt "Daemon danach aus"; Docker Desktop lief bei Start schon und wurde nicht gestoppt (andere Sitzungen), bitte Owner entscheiden.
- ANNAHME icewind/smb gibt Host und Freigabename unverändert zurück: für gehashte IDs durch die md5-Probe abgesichert (falsch heißt ungruppiert).

## Threat Flags

Keine neuen Flächen außerhalb des Bedrohungsmodells (T-43-60 bis T-43-64 umgesetzt und getestet).

## Self-Check: PASSED

- FOUND: backend/tests/fixtures/share_identity_cases.json, backend/tests/test_share_identity_cases.py, php/lib/Service/StorageService.php, php/tests/Unit/StorageServiceTest.php
- FOUND: Commits 662e7b63, 38d2e375, f772dbb5
