---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 23
subsystem: php/Service, backend/tests, CHANGELOG
tags: [D-43-11, D-43-15, D-43-17, OE-2, OE-3, OE-4, OE-5, OE-6, OE-7, A-2, A-5, counting, share-identity]
requires: [43-22]
provides: [FileStateService::distinctPathsByReasons mit Identitäten, N1 je Mitglied unter seiner Wurzel, DocKeyService::sharePathOf, countingKeyGroups mit übergebenen Identitäten, docKeyFormat im Body und Pflicht in der Antwort von POST /coverage, coverage.shareIdentity, stündliche Logzeile über den lokalen Cache, Fixture-Variante roots, CHANGELOG-Entwurf]
affects: [43-24, 43-27, 43-12]
tech-stack:
  added: []
  patterns: [Dokumentschlüssel Format 2 auch für die PHP-only-Zählung, N1 je Wurzel gebündelt, Zähler nur als Ganzzahlen, Drosselung über ICacheFactory::createLocal]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-23-SUMMARY.md
  modified:
    - php/lib/Service/FileStateService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/DocKeyService.php
    - php/lib/Service/StorageService.php
    - php/tests/Unit/FileStateServiceCoverageTest.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/tests/Unit/CoverageTopologyParityTest.php
    - php/tests/Unit/StorageServiceTest.php
    - php/tests/Unit/SettingsControllerTest.php
    - backend/tests/fixtures/coverage_topology.json
    - backend/tests/test_coverage_counts.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_share_identity_cases.py
    - backend/tests/test_measurement_scripts.py
    - CHANGELOG.md
decisions:
  - "Gruppen aus Identitäten: AdminViewService::countingShares ruft shareIdentities genau einmal, liest shareIdentityStats direkt danach und reicht die Identitäten an countingKeyGroups($ids, $identities) (neuer optionaler Parameter, ohne ihn wie bisher) und an distinctPathsByReasons weiter; ohne externe Speicher im Crawl kein Aufruf, Zähler 0, keine Logzeile"
  - "Die Regel des Freigabe-Pfads steht nur in DocKeyService (sharePathOf, composed); docKeyOf nutzt sie, FileStateService ebenso, damit Schlüssel und N1 nie auseinanderlaufen"
  - "N1 je Mitglied, gebündelt je Wurzel: Mitglieder mit gleicher Wurzel teilen p_n und werden in einer Abfrage gefragt (gleiches Ergebnis wie je Mitglied, weniger Abfragen); Speicher- und Hash-Listen je in Bändern zu 1000"
  - "S gleich R_n wird wie im Plan mit p_n = '' gefragt; ein Speicher kann nicht auf eine Datei zeigen, und ein Wegfall senkt nur den Nenner bis zu judged (Quote bleibt höchstens 100 %)"
  - "Gruppenmitglied ohne Identität (kann nicht vorkommen): eigener Schlüssel je Speicher und Pfad-Hash, N1 nur im eigenen Speicher, verschmilzt nie"
  - "Logzeile: Nachricht 'Findling: share identities of the counting, parsed={parsed} ...' mit genau den fünf Ganzzahlen als Kontext; Cache createLocal('findling'), Schlüssel share-identity-logged, TTL 3600"
  - "Der Known-limitations-Satz zu gehashten IDs nennt die tatsächlich nicht nachbaubaren Fälle aus 43-21 (globale oder vom Nutzer hinterlegte Zugangsdaten, Anmeldename ungleich Nutzer-ID) statt des Planbeispiels 'credentials stored per user'"
metrics:
  started: 2026-11-09T12:35:00Z
  completed: 2026-11-10T04:15:00Z
  tasks: 2
  files: 15
---

# Phase 43 Plan 23: PHP-only und N1 über den Freigabe-Pfad

Die Dokumente, die nur Nextcloud beurteilt hat (unlesbar, wiederholt hängengeblieben, gone), zählen je Gruppe über den Dokumentschlüssel Format 2 statt über fc.path_hash; N1 fragt jedes Mitglied unter dem Pfad unterhalb seiner Wurzel. Dieselbe unlesbare Datei unter /Daten (projekt/x) und /Daten/projekt (x) ist ein Dokument, und eine indexierte Datei unter /Daten hält ihr unlesbares Gegenstück unter /Daten/projekt aus dem Nenner. POST /coverage trägt docKeyFormat 2 und verlangt es in der Antwort; coverage.shareIdentity zeigt die fünf Zähler, eine Logzeile höchstens stündlich.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | RED: Fixture-Variante roots, Python-Container-Seite, PHPUnit-Fälle, Vertragstest | 0fa2a665 |
| 2 | GREEN: FileStateService, AdminViewService, DocKeyService::sharePathOf, countingKeyGroups mit Identitäten, CHANGELOG-Entwurf, PHP-Baumhash | 2ef75e83 |

## Belege

Stand 2026-11-09 (zweiter Executor), GREEN liegt uncommittet im Arbeitsbaum:

- Diff-Prüfung gegen den Plan: alle Teile von Task 2 umgesetzt (FileStateService mit Identitäten, docKeyOf und N1 je Wurzel in Bändern zu 1000; AdminViewService mit einem shareIdentities-Aufruf je Overview, shareIdentityStats direkt danach, docKeyFormat im Body und als erste Prüfung in perDocumentAnswer, coverage.shareIdentity, Logzeile über ICacheFactory; CHANGELOG-Entwurf; Baumhash).
- Grep-Teile beider verify-Zeilen: grün (Task 1 und Task 2, inkl. "roots", "spell|case", keine U+2013/U+2014).
- Python-Gates: ruff check grün, ruff format 256 Dateien unverändert, pyright 0/0/0, vulture rc 0.
- pytest der verify-Module (test_coverage_counts, test_share_identity_cases, test_admin_ui_contract, test_measurement_scripts, test_phase40_audit, test_store_metadata): 1089 passed, 7 skipped.
- PHP-Baumhash f3165a57c3aeed687c255f9c66b35f7ddff8a817df61ef421a0234234f3fe60f, 129 Dateien: Rezept 40b-baumhash.py und unabhängig find/sort/tr/sha256sum gleich; dieselbe Pipeline über git archive 25a3cd9e (vor dem Plan): af5413cd.
- STOPP-Regel: keine Änderung unter php/lib/Migration, backend/src, schema.sql; kein neuer AppConfig- oder Meta-Schlüssel (Cache-Schlüssel nur lokal, A-5).
- PHPUnit am 09.11. nicht gelaufen (freier Speicher 20 min lang 3,3 bis 3,4 GB, Schwelle 4 GB), nachgeholt am 10.11.

Stand 2026-11-10 (dritte Sitzung, nach Neustart des Rechners), vor dem Commit:

- Arbeitsbaum gegen die Sicherung geprüft: sha256 der vier Dienstdateien gleich (AdminViewService e975d990, DocKeyService 98e10326, FileStateService c0b59e17, StorageService 5ca5f2dd).
- **GREEN lokal** (`scripts/dev/phpunit_docker.sh --filter 'FileStateService|AdminViewService|StorageService|CoverageTopologyParity'`, freier RAM 6,0 GB): 246 Tests, 1750 Assertions, OK.
- **Gegenprobe PHP (Negativkontrolle)**: die vier Dienstdateien per `git show HEAD:<Datei>` auf den Stand von 0fa2a665 gesetzt, gleicher Filter: 246 Tests, 6 Errors, 25 Failures, 3 Warnings (u. a. Undefined array key "docKeyFormat" und "shareIdentity"). Sicherung zurückgespielt, cmp identisch, Hashes wie oben, erst dann committet.
- **Volle Suite ohne Filter** (RAM 5,5 GB): 1197 Tests, 7647 Assertions, OK (Boden 28).
- **Python-Gates** erneut: ruff check grün, ruff format 257 Dateien sauber, pyright 0/0/0, vulture 0.
- **pytest**: test_coverage_counts, test_share_identity_cases, test_admin_ui_contract, test_measurement_scripts, test_phase40_audit, test_store_metadata, test_changelog_translations, test_phase43_audit, test_doc_keys, test_coverage_endpoint, test_allowlist_parity, test_php_trust_boundary: 1244 passed, 7 skipped.
- CHANGELOG.de.md und CHANGELOG.fr.md tragen die drei neuen Punkte schon (Commit 36f4c6b1), der Gleichschritt-Test ist grün.

## CHANGELOG-Entwurf für 43-12 Runde 2 (Owner)

Entwurf für 43-12 Runde 2 (Owner), englisch, lokal, nicht gepusht, nicht im Store:

- Fixed: "The coverage figure counts a document once also when one share is configured with different roots, or with the server or share name spelled in a different case (#25). A Samba [homes] share is never grouped across users, and SFTP storages are grouped per login only." (OE-3 a, OE-4 a)
- Known limitations: "A Samba share whose folder depends on the user on the server side (a path with %U or %S) still counts as one tree for all users." (OE-7 a)
- Known limitations: "Storages with an id longer than 64 characters that cannot be rebuilt from their configuration (global or user provided credentials, a login name other than the user id) are counted per storage." (OE-2 a lässt ungruppierte gehashte Speicher zu)

## Deviations from Plan

**1. Wortlaut der Known limitation zu gehashten IDs**
- Der Satz nennt die tatsächlich nicht nachbaubaren Fälle aus 43-21 (globale oder vom Nutzer hinterlegte Zugangsdaten, Anmeldename ungleich Nutzer-Id) statt des Planbeispiels "credentials stored per user".

**2. N1 je Wurzel gebündelt**
- Mitglieder mit gleicher Wurzel werden in einer Abfrage gefragt statt je Mitglied einzeln; gleiches Ergebnis, weniger Abfragen.

**3. countingKeyGroups mit optionalem Parameter**
- StorageService::countingKeyGroups nimmt die Identitäten als optionalen zweiten Parameter (ohne ihn wie bisher), damit AdminViewService shareIdentities genau einmal ruft; dazu ein Fall in StorageServiceTest (testHandedInIdentitiesAreGroupedWithoutAQuery). SettingsControllerTest bekommt den ICacheFactory-Mock für den neuen Konstruktorparameter von AdminViewService.

**4. Ablauf**
- GREEN in drei Sitzungen: Umsetzung am 09.11. (Executor während der vollen Suite gestoppt), Gates am 09.11., PHPUnit, Gegenprobe und Commit am 10.11. Der Arbeitsbaum blieb dazwischen unverändert (Hashes gegen die Sicherung geprüft).

Sonst plangemäß. Keine STOPP-Regel berührt.

## Bekannte Grenzen und offene Punkte

- **Zwischenzustand bis 43-24:** PHP schickt docKeyFormat 2 in POST /coverage und verlangt es in der Antwort; der Container sendet docKeyFormat erst ab 43-24. Bis dahin greift der Weg von 1.6.2 (Zählung ohne Antwort des Containers pro Dokument). Unveröffentlicht, nur lokal; nicht einzeln ausliefern.
- **Volle Python-Suite lokal nicht belegt:** ein Lauf ohne Modulauswahl blieb unter Windows nach rund zwei Minuten an einem multiprocessing-Kindprozess stehen (keine CPU-Last, abgebrochen, Ursache nicht untersucht). Belegt sind die zwölf oben genannten Module; die volle Suite läuft erst mit dem Push in der CI (43-26).
- **Docker Desktop:** für den Lauf gestartet, läuft weiter.

## Threat Flags

Keine neuen Flächen außerhalb des Bedrohungsmodells (T-43-68 bis T-43-71 umgesetzt und getestet).

## Self-Check: PASSED

- FOUND: php/lib/Service/FileStateService.php (docKeyOf(), kein shareIdentities()), php/lib/Service/AdminViewService.php (shareIdentities(), 'docKeyFormat' =>, shareIdentity), php/lib/Service/DocKeyService.php (sharePathOf)
- FOUND: Commits 0fa2a665, 2ef75e83
