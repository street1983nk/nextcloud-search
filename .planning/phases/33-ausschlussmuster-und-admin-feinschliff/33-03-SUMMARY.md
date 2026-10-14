---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 03
subsystem: reconcile, status
tags: [exclusions, reconcile, weg-c, status, pol-01, tdd]
requires:
  - "33-02: Slice markiert Zeilen unter Muster und Präfix als skipped(excluded)"
provides:
  - "Weg C: _compare macht eine lebende Zeile mit Marke excluded zu stale Arbeit, vor dem etag-Vergleich (D-33-01)"
  - "StatusResponse.maxCells und StatusResponse.extractAddressSpaceBytes in beiden Antwortformen (für 33-06)"
affects: [33-04, 33-06, 33-08, 33-11]
tech-stack:
  added: []
  patterns:
    - "Mitgliedschaft in known_etags (row.file_id in known) statt Wertprüfung, damit eine lebende Zeile mit etag None zählt"
key-files:
  created: []
  modified:
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/api/status.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "33-03: Der Weg-C-Zweig steht nach dem DI-05-23-Zweig und vor dem etag-Vergleich; known_etags liefert keine Grabsteine (deleted_at IS NULL), also reicht die Mitgliedschaft, keine zweite Store-Abfrage"
  - "33-03: Der bestehende Zweig für unbekannte Dateien unter Regel bleibt unverändert stehen"
metrics:
  duration: "ca. 1 h 50 min inkl. voller Suite (13,5 min) und CI"
  completed: 2026-10-14
  tasks: 2
  files: 5
---

# Phase 33 Plan 03: Weg C im Abgleich und zwei Statusgrenzen Summary

Der Abgleich räumt jetzt jede Datei, die der Container kennt und die das Slice als `skipped(excluded)` markiert, auch unverändert (D-33-01); nach dem Grabstein lässt er sie liegen. Die Statusantwort trägt `maxCells` (200000) und `extractAddressSpaceBytes` (536870912) neben `maxFileBytes`, in beiden Antwortformen.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Weg C im Abgleich | eff4a9bf | reconcile.py, test_reconcile.py |
| 2 | Statusfelder, Paket-Baumhash, CI | eff4a9bf | status.py, test_status_endpoint.py, test_measurement_scripts.py |

Task 1 und 2 laufen laut Plan in einem Commit.

## Lesung known_etags

`Store.known_etags` (`store/repo.py:1318`) fragt `SELECT file_id, etag FROM files WHERE deleted_at IS NULL ...`. Grabsteine erscheinen also nie in `known`; die Mitgliedschaft `row.file_id in known` heißt "lebende Zeile". Eine zusätzliche Grabstein-Prüfung ist nicht nötig, der Test `test_an_excluded_file_behind_a_tombstone_is_not_requeued` bleibt grün.

## Belege Task 1

Neue Fälle in `test_reconcile.py`:

- `test_a_known_unchanged_excluded_file_becomes_content_work` (D-33-01-Kommentar im Docstring)
- `test_a_living_row_without_an_etag_under_a_rule_becomes_content_work` (W3: `known_etags([10]) == {10: None}`)
- `test_a_known_unchanged_file_without_the_mark_costs_nothing` (Positivkontrolle)
- `test_an_excluded_file_is_cleared_once_and_then_left_alone` (zwei Runden, dazwischen Grabstein: stale 1, dann 0)
- `test_150_known_excluded_files_travel_in_one_band_and_the_quiet_gate_holds_the_next_slice`: gemischte Seite (150 bekannt plus Regel, 20 unbekannt plus Regel, 10 bekannt ohne Regel, 5 unbekannt). Erwartung aus dem Code: 155 stale in einem Band (unter `REQUEUE_BAND` 200), die Queue zählt danach 155 über der Ruhemarke 100, das Ruhe-Tor vor dem zweiten Slice beendet die Runde mit `queue_busy`, Lesezeichen bei 185.

Bestehende Fälle: `test_a_known_excluded_file_with_a_new_etag_stays_content_work` bleibt grün (genau einmal content); die Fälle für unbekannte Dateien und Grabsteine bleiben grün.

**RED:** 4 rot vor der Umsetzung (bekannt gleiche etag, etag None, einmal räumen, 150er-Seite); Positivkontrolle grün.
**GREEN:** `tests/test_reconcile.py tests/test_extract_errors.py`: 150 passed.

**Gegenproben (unabhängig vom Muster der Umsetzung):**

- Alter Stand statt `git stash` (im Executor-Regelwerk verboten): `cp reconcile.py <scratch>; git show HEAD:backend/src/findling/worker/reconcile.py > reconcile.py; pytest -k "known_unchanged_excluded or living_row or cleared_once or 150_known or without_the_mark or new_etag_stays or behind_a_tombstone"` ergab 4 failed, 3 passed; Datei zurückkopiert, `cmp` gleich.
- Mutation 1 (`row.file_id in known` durch `known.get(row.file_id) is not None`): genau `test_a_living_row_without_an_etag_under_a_rule_becomes_content_work` rot.
- Mutation 2 (Bedingung `in known` durch `True`, also auch unbekannte und Grabsteine stale): 5 rot (zwei Runden unbekannt, Grabstein, einmal räumen, 150er-Seite, Runde nur aus Ausgeschlossenen). Belegt, dass die Mitgliedschaft die Schleife verhindert. Datei jeweils zurück, `cmp` gleich.

D-06 bleibt: kein Pfad, kein Muster im Container, keine neue Logzeile.

## Belege Task 2

- Drei neue Fälle in `test_status_endpoint.py` (Standardwerte ohne State-DB, Umgebung ohne State-DB, Umgebung auf indexiertem Volume = Übertragsweg) und die zwei Felder im Feldvertrag `FIELDS`. RED: 47 failed (Feldvertrag und neue Fälle), GREEN: 91 passed.
- Gegenprobe Übertragsweg: die zwei Zeilen `maxCells=volume.maxCells` und `extractAddressSpaceBytes=volume.extractAddressSpaceBytes` per `sed` gelöscht, genau `test_the_two_limits_are_carried_over_on_an_indexed_volume` rot, Datei zurück.
- `grep -c "maxCells=" status.py` = 2.

**Paket-Baumhash:** `PACKAGE_TREE_HASH_TODAY` von `c5498922...` auf `567467b795e8ceab743eb55d8d7cf3bdc750526c0e97ce3adfe09f7cf219849a`, Dateizahl 79, Journalabsatz "Moved on 2026-10-14 by Plan 33-03". `PHP_TREE_HASH_TODAY` unverändert (Diff zeigt nur die PACKAGE-Zeile und den Absatz).

**Gates lokal (backend/, PYTHONUTF8=1):** pytest 5660 passed, 159 skipped (13:33 min); ruff check grün; ruff format --check 222 Dateien; pyright 0 errors (latest); vulture leer; reuse lint 2718/2718. Kein PHP berührt, `php -l` entfällt.

## CI (eff4a9bf)

Alle mit `gh run watch <id> --exit-status` bis zum Ende beobachtet, alle grün:

- Python gates 38500185559
- Security scans 38500185508
- OpenSSF Scorecard 38500185689
- Resilience 38500185702
- Multi-arch image 38500185598
- HaRP deploy 38500185766 (zweiter Watch-Aufruf, der erste lief in die lokale Zeitgrenze)
- Integration 38500187026

PHP gates liefen nicht (Pfadfilter, php/ unverändert). Erste Liste leer, zweiter Aufruf mit 7 Läufen, dritter Aufruf gleich.

## Dev-Instanz

Der Host-Prozess (pid 695175) lief noch mit den alten Quellen; da Version und Routen gleich sind, hätte `register-exapp.sh` ihn weiterverwendet. Deshalb vorher per `kill -TERM` gestoppt, dann `FINDLING_PORT=8090 scripts/dev/register-exapp.sh` ("ExApp findling_backend successfully registered"). Abfrage über den AppAPI-Proxy:

```
curl -u admin:... http://localhost:8090/index.php/apps/app_api/proxy/findling_backend/status
{'appVersion': '1.4.2', 'maxFileBytes': 52428800, 'maxCells': 200000, 'extractAddressSpaceBytes': 536870912, 'indexed': 2595, 'note': ''}
```

Antwortform mit State-DB (Übertragsweg), beide Felder sichtbar.

## Deviations from Plan

1. **Gegenprobe ohne `git stash`:** Der Plan nennt `git stash` des Quellcodes; das ist im Executor-Regelwerk verboten (gemeinsamer Stash-Stapel). Ersatz: alter Stand per `git show HEAD:` eingesetzt, eigene Kopie danach zurück, `cmp` gleich. Zusätzlich zwei Mutationen statt Auskommentieren.
2. **Kein Altfall zum Umdrehen:** Der Plan verlangt, einen vorhandenen Fall "bekannt, unverändert, ausgeschlossen bleibt liegen" umzudrehen. Einen solchen Fall gab es nicht (die vorhandenen Fälle betreffen unbekannte Dateien, Grabsteine und geänderte etag). Der D-33-01-Kommentar steht im neuen Fall `test_a_known_unchanged_excluded_file_becomes_content_work`.
3. **Dev-Backend vor dem Registrieren gestoppt** (siehe oben), sonst hätte der alte Prozess ohne die neuen Felder geantwortet.

## Hinweis für 33-04

Weg C löscht im Container nur das Dokument. Die Urteilszeilen auf der PHP-Seite (auch `no_text_layer` und Dateien ohne lebende Containerzeile) räumt 33-04 Task 3 (PE-9, Befund B3 des Plan-Checks).

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-33-09 (150er-Test über Band und Ruhe-Tor), T-33-10 (nur lebende Einträge, Grabstein-Test, Mutation 2), T-33-11 (zwei Codes, kein Muster im Container) umgesetzt; T-33-12 nur ganze Zahlen aus der eigenen Umgebung.

## Self-Check: PASSED

- FOUND: reconcile.py, status.py, test_reconcile.py, test_status_endpoint.py, test_measurement_scripts.py (in eff4a9bf)
- FOUND: eff4a9bf
