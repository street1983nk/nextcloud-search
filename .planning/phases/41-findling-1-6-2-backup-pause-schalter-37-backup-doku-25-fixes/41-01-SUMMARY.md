---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 01
subsystem: worker/poller, worker/reconcile, store/repo, nc/client, api/resources, php AdminViewService, l10n
tags: [nachaudit, issue-36, gateway, reconcile, l10n, tree-hash]
requires:
  - 40-NACHAUDIT.md F-40N-01 bis F-40N-04
  - Entwurf 40-07-PLAN.md Task 1 und 2 (Vorlage)
provides:
  - Eskalationsschwelle über storage_id (GATEWAY_OUTAGE_MIN_STORAGES = 2)
  - 408/429 als Ausfallstatus
  - Fill-Refresh-Start mit Rückfall bei RuntimeError
  - gedeckelter Reconcile-Retry für failed(gateway_error) (GATEWAY_ERROR_RETRIES = 3)
  - Container-Marke failed(gateway_error) für belastete Zeilen
  - neuer Katalogsatz zu gateway_error (16 Kataloge, 5 Tabellen)
affects:
  - 41-08 (Release 1.6.2, Lockstep, Push)
  - Owner-Runde Phase 41 (Wortlaut de/fr des neuen Satzes)
tech-stack:
  added: []
  patterns:
    - "Strähnenzählung in attempts per CASE im Upsert, kein Schema"
    - "Seitenabfrage in Bändern nach Muster known_skip_reasons"
key-files:
  created: []
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/api/resources.py
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/store/repo.py
    - php/lib/Service/AdminViewService.php
    - php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{json,js}
    - docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - docs/reconcile.md
    - backend/tests/test_poller.py
    - backend/tests/test_gateway_client.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "E-40-07-01 umgesetzt: Eskalation nur bei min(5, claimed), mindestens 2 claimed UND Ablehnungen desselben Status aus mindestens 2 storage_id; W-1 (ohne Gutschrift) bleibt"
  - "E-40-07-03 umgesetzt: GATEWAY_ERROR_RETRIES = 3, attempts zählt die gateway_error-Strähne je Version, Übergang setzt 1"
  - "E-40-07-04 umgesetzt: belastete Zeilen bekommen vor dem unlock failed(gateway_error) im Container, nie in der Quittung, nie skipped(gone)"
  - "Passzahlen in den Queue-Szenariotests zählen Claims, nicht run_once-Aufrufe (ein Pass ohne Claim bewegt die Lock-Uhr des Modells nicht)"
metrics:
  duration: "ca. 95 min"
  completed: 2026-11-04
  tasks: 2
  commits: 12
---

# Phase 41 Plan 01: Nachaudit F-40N-01 bis F-40N-04 Summary

Ein kaputter Mount wird jetzt Datei für Datei beurteilt statt die Queue zu blockieren (Schwelle über storage_id), 408/429 sind Ausfälle, ein nicht startbarer Fill-Refresh hängt nicht mehr, und Dateien eines kurz fehlenden Speichers kommen über einen auf drei Wiederholungen gedeckelten Reconcile-Retry zurück in den Index; der Admin-Hinweis sagt das in 16 Katalogen.

## Commits (Reihenfolge, RED vor fix)

| Hash | Nachricht |
|------|-----------|
| b535151f | test(41-01): a large broken storage must not hold up the queue (#36) |
| 59119398 | fix(41-01): count gateway refusals over storages before calling an outage (#36) |
| a30eb009 | fix(41-01): 408 and 429 from a proxy are an outage, not a verdict |
| a4b5f4d8 | fix(41-01): a fill refresh that could not start is started again |
| 8ac65ece | test(41-01): count the passes of the queue scenarios as claims |
| 74da1610 | test(41-01): the package tree hash follows the storage threshold |
| 6b63ebfb | test(41-01): a storage that was away must come back into the index (#36) |
| 2a9c3511 | fix(41-01): the reconcile tries a gateway_error again, capped (#36) |
| 8397d93f | fix(41-01): a charged row carries gateway_error in the store (#36) |
| 2ee2056f | fix(41-01): the admin page says when a gateway_error is tried again |
| 822aef8a | docs(41-01): reconcile notes on the gateway_error retry |
| 60cf6766 | test(41-01): both tree hashes follow the gateway retry |

Alle als street1983nk <k.cherif@outlook.de>, kein Trailer (`git log --format=%b` über alle zwölf: 0 Zeilen "Claude-Session"). Kein Push (41-08 pusht gesammelt).

## Task 1: Schwelle über storage_id, 408/429, Fill-Refresh

- poller.py: `GATEWAY_OUTAGE_MIN_STORAGES: Final = 2`, Feld `_refusal_storages: dict[int, set[int]]` (in `_work` zurückgesetzt), `_count_refusal` eskaliert nur unter (a) claimed >= 2, (b) count >= min(5, claimed), (c) >= 2 storage_id. Logzeile: "content gateway refused %d files of this pass with http status %d from %d storages, taken as an outage" (keine storage_id-Liste). Begründungskommentar mit 72 s je Datei / 20 h für 1 000 Dateien, 401/403 nicht sofort, E-40-07-02, W-1.
- client.py: `_OUTAGE_STATUS = frozenset({408, 429, 502, 503, 504})` mit Begründung; Docstrings in client.py und poller.py nachgezogen.
- resources.py: `thread.start()` in try, `except RuntimeError` setzt `_FILL_REFRESH = None`, WARNING "the fill level refresh could not start, %s" mit Klassennamen.
- RED-Beleg (b535151f gegen 0565c7a2): 16 Fehlschläge, darunter alle Szenario- und Schwestertests, 408/429 in beiden Dateien und der Fill-Refresh-Test.

### Passzahlen der Szenarien

| Szenario | 1.6.0 (Nachaudit) | 1.6.2 (gemessen im Test) |
|----------|------------------|--------------------------|
| 200 kaputte Dateien auf storage 7, 32 gesunde dahinter, Batch 32, lock_rounds 8 | 121 Pässe bis zur ersten gesunden Datei | erste gesunde Datei im 7. Pass, Queue nach 8 Pässen leer, 0 Eskalationen, 200 x failed(gateway_error) |
| 100 auf storage 7, 100 auf storage 8, 32 gesunde auf 9 | 128 Pässe bis zur ersten gesunden Datei | erste gesunde Datei im 8. Pass, Queue nach 28 Claims leer, 3 Eskalationen (Grenzpass 4 und zweimal dieselben 5 Grenzzeilen nach Lock-Timeout), 5 belastete queue_ids, 195 x failed(gateway_error), 5 x repeatedly_stuck |
| 70 Dateien, eine Storage, alle 500 (E-40-07-02) | n/a | 3 Pässe ROUND_WORKED, 70 Verdikte, 0 unlock, je Datei 1 Anfrage |

Test `test_two_broken_storages_in_a_row_only_charge_the_rows_at_the_border` pinnt (28 Claims, 3 Eskalationen).

### W-1-Tests neu abgeleitet, je mit Einzel-Storage-Schwester

| W-1-Test (zwei storage_id, Aussage unverändert) | Schwester (eine storage_id) |
|---|---|
| test_the_same_refusal_for_every_file_of_a_pass_is_an_outage | test_the_same_refusal_for_every_file_of_one_storage_is_six_verdicts |
| test_a_small_pass_of_only_refusals_escalates_without_a_refund[2,3,4] | test_a_small_pass_of_only_refusals_on_one_storage_is_judged_file_by_file[2,3,4] |
| test_refused_scans_under_several_slots_escalate_without_a_refund | test_refused_scans_of_one_storage_under_several_slots_are_verdicts |
| test_files_that_always_refuse_reach_the_give_up_rule_and_the_queue_drains | test_files_of_one_storage_that_always_refuse_end_as_verdicts_and_the_queue_drains |

### Testfunktionszahlen (`grep -cE "^(async )?def test"`)

| Datei | vorher | nach Task 1 | nach Task 2 |
|---|---|---|---|
| tests/test_poller.py | 205 | 214 | 217 |
| tests/test_gateway_client.py | 26 | 26 | 26 |
| tests/test_status_endpoint.py | 78 | 79 | 79 |
| tests/test_reconcile.py | 66 | 66 | 71 |
| tests/test_store_repo.py | 113 | 113 | 116 |
| tests/test_admin_ui_contract.py | 114 | 114 | 115 |

Keine Zahl sank. In test_gateway_client.py wurde `test_the_outage_statuses_are_exactly_the_three_proxy_answers` umbenannt in `..._five_proxy_answers` und prüft zusätzlich, dass 500, 401, 403, 422, 423 nicht im Raster stehen.

## Task 2: gedeckelter Reconcile-Retry, Container-Marke, Hinweis

### STOPP-Prüfung `git grep -n "attempts" -- backend/src` (vor dem Umbau)

| Treffer | Urteil |
|---|---|
| api/diagnose.py:5, :103, :325 | nur Anzeige in der Diagnose, keine Regel |
| store/repo.py:341, :345, :361, :503, :504, :530, :539, :566, :976, :1151 | Upsert, Kommentare, Docstrings; der einzige Ort, der attempts schreibt |
| store/schema.sql:54 | Spaltendeklaration, unverändert (kein Schema-Delta) |
| worker/poller.py:196 | Wort "attempts" in einem Kommentar zum Retreat, unabhängig |
| worker/poller.py:1999, :2060 | Docstrings, die Store.record beschreiben |

Keine weitere Stelle liest attempts für eine Regel: kein STOPP. `git diff v1.6.1` über schema.sql, vectors.sql, index/schema.py, php/lib/Migration ist leer; kein SCHEMA_VERSION/STORE_SCHEMA_MARK, kein neuer Meta-Schlüssel.

- repo.py: `_RECORD_SQL` setzt attempts per CASE auf 1 beim Übergang in failed(gateway_error) (nicht gleiche Version mit failed(gateway_error) davor), sonst +1; Kommentar und `record()`-Docstring ergänzt. Neue Methode `gateway_retry_candidates(file_ids, limit) -> set[int]` in Bändern (`_ACL_BAND - 1`, weil das Limit selbst ein Parameter ist).
- reconcile.py: `GATEWAY_ERROR_RETRIES: Final = 3` mit Begründungsblock; `_compare` fragt einmal je Seite nur für Zeilen mit unverändertem Etag (leere Liste ohne Abfrage) und prüft im Zweig `stored == row.etag` zuerst `row.file_id in retry` -> stale. Stranded-Handover- und Excluded-Zweig bleiben davor.
- poller.py: `_refused_jobs: dict[int, QueueJob]`; `_abort` ruft bei nicht leerem `charged` vor dem unlock `_mark_the_charged`, das je Zeile `store.record(..., "failed", "gateway_error")` über asyncio.to_thread in try/except schreibt (WARNING nur Klassenname); unlock läuft in jedem Fall.
- AdminViewService.php: Hinweis zu gateway_error = "Nextcloud could not open the file, often because its storage was not available. The nightly comparison tries it again up to three times, and a change to the file tries it at once."; "The next run tries again." bleibt bei timeout und ocr_failed (2 Vorkommen).
- l10n: 16 Kataloge (de/fr nach E-40-07-05 von Hand, es/it/nl/pt_PT/pt_BR maschineller Entwurf unter Vorbehalt), fünf Tabellen docs/l10n-{french,spanish,italian,dutch,portuguese}.md, nicht docs/l10n-catalogues.md (0 Treffer). de-Schlüsselzahl 354 -> 355 mit Absatz "Plan 41-01".
- docs/reconcile.md: Satz zum gedeckelten Retry neben der IN-03-Ausnahme in Schritt 5, neuer Abschnitt "Ein Speicher, der kurz weg war (F-40N-02)" mit Zustandstabelle und bekannter Grenze.
- RED-Beleg (6b63ebfb gegen 74da1610): 14 Fehlschläge in store/reconcile/poller plus 2 im Vertragstest (neuer Satz, de-Zahl 355); pyright meldete im RED-Stand nur die noch fehlende Methode `gateway_retry_candidates`.

## Baumhash-Paare

| Paar | alt | nach Task 1 | nach Task 2 |
|---|---|---|---|
| PACKAGE_FILES_TODAY / PACKAGE_TREE_HASH_TODAY (80 Dateien) | c5da3ea5... | a4a0cf66... | b8769239... |
| PHP_FILES_TODAY / PHP_TREE_HASH_TODAY (110 Dateien) | 71443d7d... | unverändert | 599393dc... |

Jeder Wert zweimal gerechnet: Rezept 40b-baumhash.py und unabhängig find | LC_ALL=C sort | tr -d '\r' | sha256sum (Positivkontrolle des Shell-Rezepts auf dem alten PHP-Stand: 71443d7d, gleich). Das eingefrorene Paar PHP_FILES/PHP_TREE_HASH unverändert (`git diff -U0 ... | grep -E "^[-+]PHP_(FILES|TREE_HASH) ="` leer), `grep -c "PACKAGE_FILES_TODAY = 80"` = 1, `-k tree_hash` grün.

## Verifikation

- Gezielte Testdateien: test_poller.py, test_gateway_client.py, test_status_endpoint.py: 371 passed, 1 skipped; test_store_repo.py, test_reconcile.py, test_poller.py: 449 passed, 1 skipped; test_admin_ui_contract.py, test_php_acl_boundary.py, test_extract_errors.py: 279 passed.
- Volltestsuite lokal am Kopf 60cf6766 in zwei Hälften mit den sechs --ignore (5,4 bzw. 5,6 GB frei, seriell): tests/test_[a-m]*.py 3088 passed, 41 skipped; tests/test_[n-z]*.py 3353 passed, 262 skipped; zusammen 6441 passed, 303 skipped, 0 failed. PHPUnit läuft lokal nicht (kein php), Beleg im CI-Job "PHP and store metadata gates" nach dem gesammelten Push in 41-08.
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture 80 vor jedem Commit grün (außer pyright im RED-Stand von Task 2, s. o.).
- Keine U+2013/U+2014 im Delta, keine Umlaute in backend/src.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Passzahl der Queue-Szenarien zählte run_once-Aufrufe**
- **Found during:** Task 1, nach dem Fix
- **Issue:** Ein Lauf der drei Testdateien zeigte einmal 2 Fehlschläge (darunter test_two_broken_storages_in_a_row_only_charge_the_rows_at_the_border), sieben Wiederholungen waren grün. Die Tests zählten Pässe als run_once-Aufrufe; ein Pass, der vor seinem Claim endet, bewegt die Lock-Uhr des Queue-Modells nicht und verfälscht so die Zahl. Die genaue Ursache des einen Ausreißers ließ sich nicht reproduzieren.
- **Fix:** Passzahlen als Claims des Modells (`len(queue.handed)`), Schleifen mit Spielraum, Zustände in der Fehlermeldung; die Einzel-Storage-Prüfung filtert ROUND_WAITING_FOR_RUNNER.
- **Files modified:** backend/tests/test_poller.py
- **Commit:** 8ac65ece

**2. [Rule 3 - Blocking] Fill-Refresh-Test patcht nur den Modulnamen**
- **Found during:** Task 1 RED
- **Issue:** `threading.Thread.start` prozessweit zu patchen hätte Threads des Testclients und von asyncio.to_thread mit getroffen.
- **Fix:** `resources.threading` per monkeypatch durch einen Namespace mit einer nicht startbaren Thread-Unterklasse ersetzt; `_FILL_REFRESH` per monkeypatch zurückgesetzt, damit ein roter Lauf keinen nie gestarteten Thread für den nächsten Fall hinterlässt.
- **Commit:** b535151f

**3. Anmerkung zu einer Testaussage:** In `test_the_same_refusal_for_every_file_of_a_pass_is_an_outage` prüfte die alte Fassung, dass keine der sechs Dateien eine Zeile im Store hat. Mit E-40-07-04 tragen die fünf belasteten Zeilen jetzt failed(gateway_error); die Aussage wurde auf die nie geholte sechste Datei eingeengt, und `test_a_charged_row_carries_gateway_error_in_the_store` prüft die fünf Marken mit Etag und attempts ausdrücklich.

## Bekannte Grenzen (für die Owner-Runde und v1.7)

- Zeilen, die 1.6.0 oder 1.6.1 als gateway_error geschrieben haben, tragen die alte, kumulierte attempts-Zählung; über 3 wird die Datei nicht automatisch wiederholt. Abhilfe `occ findling:index --restart` (steht in docs/reconcile.md).
- 1.6.0/1.6.1-Belastungen, die schon als repeatedly_stuck abgeschrieben sind und im Container keine Zeile haben, bleiben Endzustand (give_up), wie im Entwurf 40-07 beschrieben.
- Die Nextcloud-Seite zeigt für eine belastete und später abgeschriebene Zeile bis zur Wiederholung "repeatedly_stuck" mit "Findling does not try this file again" (bekannte Unschärfe, v1.7).
- Zwei gleichzeitig kaputte Mounts mit verzahnten Datei-IDs eskalieren in jedem Pass dieses Bereichs; in Crawl-Reihenfolge nur an der Grenze (Test oben: 5 Grenzzeilen, 3 Eskalationen).
- Einzel-Storage-Instanz mit globalem 500: jede Datei endet als failed(gateway_error), höchstens vier Anfragen je Datei und Version; gatewayUnavailableSince erscheint dabei bewusst nicht (E-40-07-02).
- Wortlaut de/fr des neuen Satzes geht in die Owner-Runde der Phase 41; es/it/nl/pt_PT/pt_BR sind maschinelle Entwürfe unter Vorbehalt.

## Threat Flags

Keine neue Angriffsfläche über das Threat-Register hinaus: keine neue Route, kein neuer Meta-Schlüssel, neue Logzeilen nur mit Zahlen, Status und Klassennamen (T-41-05), neuer Katalogsatz über t() und das bestehende Rendering (T-41-07).

## Self-Check: PASSED

- 41-01-SUMMARY.md vorhanden; alle zwölf Commits (b535151f bis 60cf6766) im Repo gefunden.
