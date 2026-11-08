---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 20
subsystem: backend/store, scripts/ci
tags: [D-43-16, upgrade, reconcile, gateway_error, harness]
requires: [43-18]
provides: [einmalige neue Serie für Weigerungszeilen von 1.6.2, sqlite3-Wartezeit im Harness]
affects: [43-08, 43-07]
tech-stack:
  added: []
  patterns: [einmaliger Upgrade-Schritt über eine Meta-Marke in state.db]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-20-PLAN.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-20-SUMMARY.md
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/reconcile.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_measurement_scripts.py
    - scripts/ci/coverage_e2e.sh
    - scripts/ci/coverage_truth.sh
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-08-PLAN.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-FREIGABEN.md
decisions:
  - "attempts wird auf 1 gesetzt, nicht auf 0: 1 ist der Wert, mit dem _RECORD_SQL eine Serie beginnt; die gespeicherte Weigerung zählt als erste, danach folgen genau GATEWAY_ERROR_RETRIES erneute Ausgaben wie nach einer frischen Weigerung (0 hätte eine Anfrage mehr erlaubt)"
  - "Aufruf in _open_state von Poller und Reconcile, nicht in open_store: beide laufen erst nach der Freigabe der Backup-Pause (D-41-19), open_store rufen auch Leser und Hilfsaufgaben"
metrics:
  completed: 2026-11-08
---

# Phase 43 Plan 20: Einmal neue Serie für Weigerungszeilen von 1.6.2

Beim ersten Start von 1.6.3 bekommt jede lebende Zeile failed(gateway_error) einmal attempts = 1 (Marke refusal_streaks_1_6_3, eine Transaktion), damit der Reconcile Dateien, deren Budget 1.6.2 verbraucht hat, wieder an den Gateway gibt und sie das Urteil skipped(unreadable) samt Abhilfe bekommen.

## Ursache (geprüft)

- v1.6.2 store/repo.py:368-373: jede Weigerung schreibt failed(gateway_error), Serienbeginn 1, sonst +1; v1.6.2 :1468 Kandidaten nur bei attempts <= limit.
- Kopf: worker/reconcile.py `_compare` gibt eine Zeile mit unbewegtem etag nur über `gateway_retry_candidates(unmoved, GATEWAY_ERROR_RETRIES=3)` erneut aus, sonst `continue`. Der Upsert setzt die Serie von failed(gateway_error) nach skipped(unreadable) fort (+1), ein Neubeginn kommt also nicht von selbst.
- Log 42482017221 (upgrade/native): unter 1.6.2 standen die vier Queue-Zeilen der gesperrten Dateien 25 min offen (open=4, outages 1 und 2, Catch-up-Runde lief), jede Wiederholung zählte die Serie weiter; nach dem Update "3 of 4 container rows ... skipped/unreadable", eine Zeile blieb failed(gateway_error). Die Attempts-Werte selbst stehen nicht im Log; die Code-Lage erklärt das Bild vollständig, Test b belegt den Ausschluss.

## Nextcloud-Seite

Braucht nichts. `QueueMapper::requeueAs` filtert nicht nach dem Urteil (nur kind delete und dirty), `FileStateService::record` überschreibt die eine Zeile pro Datei unbedingt. Der Reconcile entscheidet die erneute Ausgabe allein an der Container-Zeile, auch wenn Nextcloud failed(repeatedly_stuck) trägt.

## Befund Reconcile aus

Bei FINDLING_RECONCILE_ENABLED=false gibt niemand die zurückgesetzten Zeilen aus: die Catch-up-Runde von 1.5 startet nur, solange recheck_1_5_0 nicht done ist (main.py `_the_catch_up_is_open`), auf einer Bestandsinstanz ab 1.5 also nicht. Die Marke wird trotzdem gesetzt, die Zeilen warten auf ein Ereignis, eine Änderung oder `occ findling:index --restart`. Das galt schon in 1.6.2 für jede gateway_error-Wiederholung, ist also keine Regression. Vorschlag (nicht gebaut): der Poller gibt im selben Schritt die zurückgesetzten Datei-IDs einmal über `queue.requeue(..., kind=content)` in Bändern von REQUEUE_BAND an die Queue, unabhängig vom Schalter; Kosten je Datei eine Anfrage, einmalig.

## Grenze

Läuft der neue Container vor dem Update der Companion (Reihenfolge Container zuerst) und fällt eine Reconcile-Runde in dieses Fenster, antwortet der Gateway von 1.6.2 mit 500, und diese eine Wiederholung zählt wieder als gateway_error. Die Serie hat drei Wiederholungen, je eine pro Zyklus, das Fenster ist meist Minuten lang.

## Tasks

| Task | Commit | Inhalt |
|------|--------|--------|
| 1 RED | 9504c536 | test(43-20): Fälle a bis d in test_store_repo.py |
| 1 GREEN | b46066a3 | fix(43-20): REFUSAL_RENEW_MARK, Store.renew_refusal_streaks, Aufrufe, Baumhash mit Journal |
| 2 | 9ae201a8 | ci(43-20): `-cmd ".timeout 10000"` für ncdb, statedb, das Löschen von verwaist.txt (coverage_e2e.sh) und die zwei `.backup` (coverage_truth.sh) |
| 3 | siehe Abschluss-Commit | docs(43-20): Plan, Summary, 43-08-Vermerk, Freigabe |

## Verifikation

- RED: Import von REFUSAL_RENEW_MARK schlug fehl (Sammelfehler), dann GREEN.
- Fokussiert: test_store_repo, test_poller, test_reconcile, test_catchup, test_phase41_audit: 543 passed, 1 skipped.
- Skript-Tests: test_workflow*.py, test_measurement_scripts.py, test_ops_scripts.py: 756 passed (vor dem Baumhash-Nachzug 1 failed, der erwartete Hash-Test).
- Baumhash: unabhängig mit find, sort, tr und sha256sum 3d704f65... beide Wege, HEAD vor dem Schritt 2908e94b... (Positivkontrolle).
- Gates: ruff check, ruff format --check (254 Dateien), pyright latest 0 errors, vulture src tests --min-confidence 80 grün.
- `.timeout`: sqlite shell.c.in ruft nur `sqlite3_busy_timeout`, keine Ausgabe; lokal ist kein sqlite3-CLI vorhanden (auch kein Docker, kein WSL-Paket), deshalb am Quelltext belegt. bash -n beider Skripte grün.
- Ganze Suite (gestartet vor dem Baumhash-Nachzug): 6925 passed, 331 skipped, 1 failed, das war genau der Baumhash-Test, der danach im Skript-Lauf grün ist (756 passed).

## Self-Check: PASSED

Commits 9504c536, b46066a3, 9ae201a8 vorhanden; Plan, Summary, geänderte Dateien vorhanden.

## Abweichungen

- [Rule 3] PACKAGE_TREE_HASH_TODAY in test_measurement_scripts.py nachgezogen (sonst rot), Journalzeile wie bei 43-18.
- [Rule 2] Neben ncdb/statedb auch das schreibende `sqlite3 ... DELETE FROM oc_filecache` (verwaist.txt) und die zwei `.backup` in coverage_truth.sh mit Wartezeit, gleiche Fehlerklasse; der `sql`-Helfer von coverage_truth.sh liest private Schnappschüsse und bleibt.
- 43-08-PLAN.md: neben der CHANGELOG-Zeile (7) auch die damit überholte Known-limitations-Zeile ("stay errors until they change") gestrichen und die STOPP-Liste der neuen Meta-Schlüssel sowie der deploy-harp-Kommentar um die neue Marke ergänzt, sonst widerspräche 43-08 dem Code. CHANGELOG.md unverändert.
