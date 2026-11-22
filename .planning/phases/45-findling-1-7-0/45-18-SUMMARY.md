---
phase: 45-findling-1-7-0
plan: 18
subsystem: backend-and-php-companion
tags: [issue-59, policy-blocked, verdict-generation, l10n, refusal-streak, tdd]
requires: [45-17]
provides: [Reason policy_blocked in drei Vokabularlisten und der Reason-Tabelle, Texte in 18 Katalogen, Generation 4 beidseitig mit Rückfall gateway_error, GatewayPolicyRefused, Urteil ohne Ausfallzählung, Serie bis 3 Nächte, einmalige Erneuerung refusal_streaks_1_7_0, Zahl-Gates, 1.6.3-Gate nach c1]
affects: [45-19, 45-22, 45-20, 45-21, 45-10]
tech-stack:
  added: []
  patterns: [Fallback-Tabelle je Generation mit leerem Eintrag für die eigene Generation (W3), Kopf statt Body als Unterscheidung einer Ablehnung, Erneuerung je Marke in eigener Transaktion, Zahl im Satz per Gate an die Konstante gebunden]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-18-SUMMARY.md
  modified:
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/reconcile.py
    - php/lib/Controller/ProfileController.php
    - php/lib/Service/FileStateService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/ReaderCandidates.php
    - php/l10n/*.js und *.json (18 Dateien)
    - docs/l10n-chinese.md, l10n-dutch.md, l10n-french.md, l10n-italian.md, l10n-portuguese.md, l10n-spanish.md
    - backend/tests/test_extract_errors.py, test_queue_client.py, test_admin_ui_contract.py, test_store_metadata.py, test_measurement_scripts.py, test_phase31_audit.py, test_poller.py, test_gateway_client.py, test_store_repo.py, test_reconcile.py
    - php/tests/Unit/ProfileControllerTest.php, AdminViewServiceTest.php, FileStateServiceCoverageTest.php
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
decisions:
  - "c1 umgesetzt: alter unreadable-Schlüssel aus allen 18 Katalogen und sechs Sprachtabellen entfernt; SUPERSEDED_IN_1_7_0 hält den alten Satz mit seinem abgenommenen deutschen Wortlaut nur gegen docs/store-listing.md"
  - "Der Nachlauf von 1.5 startet ab Generation 3 (CATCHUP_MIN_GENERATION), nicht nur bei der Generation dieses Codes; sonst hätte die Generation 4 ihn vor einer 1.6-Begleit-App abgeschaltet"
  - "Die skipped-Tabellen bekommen keinen Eintrag für policy_blocked (nur 4 leer, wie im Plan); der Draht-Test aus 31-15 überspringt policy_blocked in der skip-Liste und hält zugleich fest, dass ExtractionOutcome.skipped(policy_blocked) nicht gebaut werden kann"
  - "Logzeile der Erneuerung: 'refusal streaks renewed once after the update, rows=%d mark=%s' (Zähler vor der Marke, damit die Diagnose in scripts/ci/coverage_e2e.sh weiter trifft)"
metrics:
  duration: "ca. 80 min laut Systemzeit (ca. 15:35 bis 16:55 UTC), davon ca. 35 min Docker (zweimal volles PHPUnit und PHP-Gates, ein gefilterter RED) und ca. 28 min zwei volle pytest-Läufe, teils parallel zum Schreiben"
  completed: 2026-11-22
---

# Phase 45 Plan 18: policy_blocked als eigenes Urteil, Generation 4, Erneuerung der Serien aus 1.6 Summary

Eine Datei, die eine Regel für alle Gefragten sperrt (Wasserzeichen von Nextcloud Office auch für den Besitzer), heißt jetzt failed(policy_blocked) mit eigenem Label und ehrlicher Abhilfe in 18 Katalogen; der Container erkennt die 403 mit `X-Findling-Refusal: policy`, zählt sie nie zur Ausfallschwelle und behandelt sie in derselben Serie wie gateway_error (bis 3 Nächte); die verbrauchten Serien aus 1.6 kommen nach dem Update einmal zurück.

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 1 | Vokabular policy_blocked (errors.py, repo.py, FileStateService), Reason-Zeile und neue unreadable-Abhilfe, Generation 4 beidseitig (W3), 18 Kataloge, sechs Sprachtabellen, Zahl-Gates, 1.6.3-Gate nach c1, Docblock ReaderCandidates (I-45-17-04), Schlüsselzahl 382, Baumhashes | 7198db12 |
| 2 | GatewayPolicyRefused im Client, Urteil ohne Ausfallzählung im Poller, Serie in `_RECORD_SQL` und `gateway_retry_candidates`, Erneuerung `refusal_streaks_1_7_0`, Kommentare im Reconcile, Mutationsgegenprobe | 5b1de936 |

## Ergebnisse

- RED Task 1: Python `24 failed, 576 passed`, PHP `Tests: 239, Assertions: 1097, Failures: 5`; RED Task 2: `18 failed, 526 passed, 1 skipped`; jeweils nur neue Fälle (Liste wörtlich in 45-AUDIT.md `### RED und GREEN 45-18`).
- GREEN Task 1: verify Exit 0 (`1262 passed, 12 skipped`, ruff, format, pyright latest 0/0/0, vulture, PHPUnit `OK (1347 tests, 8616 assertions)`, PHP-Gates grün gegen ocp v33.0.9, v34.0.6, v35.0.3, php-cs-fixer, zizmor, actionlint).
- GREEN Task 2: verify Exit 0 (`784 passed, 1 skipped`, dieselben Gates, PHPUnit `OK (1347 tests, 8616 assertions)`); volle pytest-Suite `7333 passed, 305 skipped`.
- Mutationsgegenprobe: Rückkehr vor der Zählung entfernt -> `test_five_refusals_by_a_rule_over_three_storages_are_five_verdicts[True-False]` und `test_policy_refusals_from_two_storages_never_escalate_to_an_outage` rot, Datei danach byte-gleich (`restored_identical=yes`).
- Fehl-Samples der Gates: 21 statt 20 im unreadable-Satz (es.json) rot; "vier keer" statt "drie keer" (nl.js) und 4 Wiederholungen rot; Kopf-Gate mit anderem Wert rot (beide Richtungen); 1.6.3-Gate: Satz ohne Schlüssel und ohne Listeneintrag rot, Satz in der Liste und noch im Katalog rot, deutscher Wortlaut nicht im Abschnitt rot.
- Baumhashes: php/ `34d00c1f...` (141, Positivkontrolle 006c2983 -> `ef4f5a19...`); backend/src/findling `7249fe45...` nach Task 1, `9fa6c443...` nach Task 2 (83, Positivkontrollen 006c2983 -> `76a4f649...`, 7198db12 -> `7249fe45...`).
- Docker am Ende leer (`docker ps -q`), kein Push, kein Tag, kein Kommentar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Nachlauf von 1.5 hätte mit Generation 4 vor einer 1.6-Begleit-App nie gestartet**
- **Found during:** Task 1 (Lesen der Aufrufer von VERDICTS_GENERATION)
- **Issue:** `poller.py` startete den Nachlauf nur bei `choice.verdicts == VERDICTS_GENERATION`; mit 4 und einer Begleit-App 1.6 (3) im gemischten Fenster nie.
- **Fix:** `CATCHUP_MIN_GENERATION: Final = 3`, Bedingung `>=`; Test parametrisiert auf 3 und 4 (RED `1 failed, 6 passed` nach dem Hochsetzen, vor dem Fix).
- **Files modified:** backend/src/findling/worker/poller.py, backend/tests/test_poller.py
- **Commit:** 7198db12

**2. [Rule 3 - Blocking] Zwei Testdateien außerhalb von files_modified wanderten mit der Generation**
- **Found during:** Task 1, volle Läufe vor dem Commit
- **Issue:** Sieben Erwartungs-Arrays in `ProfileControllerTest.php` tragen `'verdicts' => 3` wörtlich (voller PHPUnit-Lauf `Failures: 13`); `test_phase31_audit.py::test_no_code_reaches_a_companion_that_does_not_know_it` kannte Generation 4 nicht (volle Suite `7 failed`).
- **Fix:** Arrays auf 4; der Draht-Test kennt `_NEW_IN_GENERATION_4`, prüft 4 und 5, policy_blocked nur zu 4 unverändert, sonst gateway_error; in der skip-Liste wird policy_blocked übersprungen und `ExtractionOutcome.skipped(policy_blocked)` als unbaubar festgehalten (die skipped-Tabellen bleiben wie im Plan).
- **Files modified:** php/tests/Unit/ProfileControllerTest.php, backend/tests/test_phase31_audit.py
- **Commit:** 7198db12

**3. [Rule 3 - Blocking] Paket-Baumhash in Task 2 nachgezogen**
- **Found during:** Task 2
- **Issue:** `test_measurement_scripts.py` steht nur in Task 1, Task 2 ändert aber backend/src/findling, also `PACKAGE_TREE_HASH_TODAY`.
- **Fix:** Konstante und Absatz nachgezogen (Rezept, Pipeline, Positivkontrolle 7198db12).
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commit:** 5b1de936

**4. [Rule 1 - Bug] Logzeile der Erneuerung mit Zähler vor der Marke**
- **Found during:** Task 2
- **Issue:** `scripts/ci/coverage_e2e.sh` (Diagnose `locked_diagnosis`) greift `refusal streaks renewed once after the update, rows=[0-9]*`; eine Zeile `mark=... rows=...` hätte die Diagnose leer gemacht.
- **Fix:** `rows=%d mark=%s`; Plan-Vorgabe "nur Zähler und Marke" erfüllt.
- **Files modified:** backend/src/findling/store/repo.py, backend/tests/test_store_repo.py
- **Commit:** 5b1de936

**5. [Hinweis] RED-Technik**
- Die Python-Tests lesen `GatewayPolicyRefused` und `REFUSAL_RENEW_MARK_1_7_0` über das Modul (`nc_client_module.GatewayPolicyRefused`, `repo_module...`), damit RED rote Fälle statt eines Importfehlers der ganzen Datei zeigt (Muster aus 43-18).
- Die Task-2-Tests waren vor dem Commit von Task 1 geschrieben; sie wurden für den Commit von Task 1 beiseitegelegt (Kopie im Scratchpad, Block aus test_poller.py herausgenommen) und danach unverändert zurückgespielt.

### Regelverstoß des Ausführers (ohne Wirkung)

- Ein versehentlicher Aufruf `uv run ... python -` mit leerem stdin (`< /dev/null`) in einer Hilfszeile; er blieb hängen, wurde nach ca. zwei Minuten beendet, hat nichts ausgeführt und nichts geschrieben. Gegen die Regel "nie `python -`"; danach nur noch Skriptdateien.

## Befunde

Keine neuen Befunde in Produktcode. Hinweise für die Folgepläne:

- 45-20: Die Logzeile `content gateway refused one file, http status 403 for file id N` ist byte-gleich und kommt je Ablehnung einmal (Unit-Test prüft sechs Zeilen); dazu je Datenbank eine Zeile `refusal streaks renewed once after the update, rows=N mark=refusal_streaks_1_7_0`.
- Die Erneuerung von 1.7.0 setzt alle lebenden failed(gateway_error) mit attempts > 1 auf 1, also auch echte Speicherausfälle aus 1.6 (T-45-69, accept): höchstens drei Anfragen mehr je Datei und Datenbank.
- Die Übersetzungen es, it, nl, pt_BR, pt_PT, zh_TW sind maschinelle Entwürfe unter dem datierten Vorbehalt der Sprachdokumente (Nachtrag 22.11.2026 je Dokument).

## Threat Flags

Keine neue Fläche außerhalb des Threat-Registers: T-45-62 (Ausfallzählung) mit Test, Gegenkontrolle und Mutation; T-45-63 (Draht-Vokabular) mit Generation 4 und Rückfall gateway_error; T-45-69 (Last der Erneuerung) wie geplant; T-45-70 (gefälschter Kopf) unverändert accept, der Kopf ändert nur das Urteil.

## Known Stubs

Keine.

## Offene Punkte

- COMP-05 bleibt Pending (Teil 2 von 6); REL-07 bleibt Pending.
- 45-19 als Nächstes (V-45-10-02/03), dann 45-22, 45-20, 45-21, 45-10 neu.

## Self-Check: PASSED

Commits vorhanden: 7198db12, 5b1de936. Dateien vorhanden: 45-18-SUMMARY.md, backend/src/findling/nc/client.py (GatewayPolicyRefused), backend/src/findling/store/repo.py (refusal_streaks_1_7_0), php/lib/Service/AdminViewService.php ('policy_blocked' =>). Docker leer.
