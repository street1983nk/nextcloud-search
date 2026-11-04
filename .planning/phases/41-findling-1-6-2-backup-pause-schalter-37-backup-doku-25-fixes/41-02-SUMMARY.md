---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
plan: 02
subsystem: api/status, php ScanStatsService, docs/admin-page
tags: [issue-25, dedup, left-out, background-count, tree-hash]
requires:
  - 41-01 (Baumhash-Stand b8769239 / 599393dc)
provides:
  - embeddedLeftOut auch über 100 000 left-out-Dokumenten (Hintergrundzählung mit Cache)
  - Repräsentant einer Share-Gruppe = Mitglied mit größtem filesSeen
affects:
  - 41-08 (Release 1.6.2, PHPUnit-Beleg im CI-Lauf)
  - Issue-#25-Antwort (erst nach Store-Release)
tech-stack:
  added: []
  patterns:
    - "Single-flight-Hintergrundthread mit Lock, Daemon, join-Helfer (Muster Kandidat F) in status.py"
    - "Stale-while-revalidate mit TTL ab Messende, LRU auf 4 Schlüssel, Bestands-Kennung (Pfad, st_dev, st_ino)"
key-files:
  created: []
  modified:
    - backend/src/findling/api/status.py
    - backend/tests/conftest.py
    - backend/tests/test_status_leave_out.py
    - backend/tests/test_phase40_audit.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Service/ScanStatsService.php
    - php/tests/Unit/ScanStatsServiceTest.php
    - docs/admin-page.md
decisions:
  - "D-41-09: eigener Hintergrundthread findling-left-out-refresh in status.py statt Fill-Refresh; Konstanten LEFT_OUT_EMBEDDED_SYNC_CEILING = 100_000, LEFT_OUT_CACHE_SECONDS = 300, LEFT_OUT_CACHE_KEYS = 4"
  - "Abgelaufener Cache-Wert wird weiter geliefert, während die nächste Zählung läuft (wie Kandidat F), damit die Seite nicht alle 5 min für einen Poll auf 1.5-Rechnung springt"
  - "Kennung des vectors.db ohne st_mtime_ns: jeder Checkpoint des Embedding-Workers bewegt die mtime"
  - "D-41-10: Repräsentant per usort (filesSeen absteigend, finished vor unfinished, ID aufsteigend), Rückfall ohne Zeilen = kleinste ID"
metrics:
  duration: "ca. 60 min"
  completed: 2026-11-04
  tasks: 2
  commits: 7
---

# Phase 41 Plan 02: Issue #25 (embeddedLeftOut über 100k, größter Repräsentant) Summary

Über 100 000 left-out-Dokumenten zählt der Container die Vektoren jetzt in einem eigenen Hintergrundthread mit kleinem Cache statt das Feld wegzulassen, und eine Share-Gruppe wird durch ihr Mitglied mit den meisten gesehenen Dateien vertreten; mit den Zahlen aus #25 ergibt das den Nenner 246 053 statt 178 551.

## Commits (RED vor fix)

| Hash | Nachricht |
|------|-----------|
| be10d8be | test(41-02): the vector figure of left out storages must not stop at a hundred thousand (#25) |
| e244425e | fix(41-02): count the vectors of left out storages in the background above the ceiling (#25) |
| 5dc54383 | test(41-02): the package tree hash follows the left out count |
| d401ca2f | test(41-02): a share group must be represented by its largest member (#25) |
| 9eb6c453 | fix(41-02): the largest member represents a share group (#25) |
| 497fbdd5 | docs(41-02): the admin page names the new representative |
| fbbfa1f7 | test(41-02): the php tree hash follows the representative |

Alle als street1983nk <k.cherif@outlook.de>, 0 Trailer-Zeilen. Kein Push.

## Task 1: embeddedLeftOut hybrid

- status.py: `LEFT_OUT_EMBEDDED_SYNC_CEILING = 100_000` (bis hier synchron, ~40 ms für 60 000 Dokumente, 40-AUDIT.md P1). Darüber `_cached_left_out`: Cache-Treffer mit gleicher Bestands-Kennung -> Wert (abgelaufen: Wert plus Start der nächsten Zählung), sonst None und Start. `_start_left_out_refresh` (single flight, `thread.start()` in try, RuntimeError -> Flag None, WARNING "the left out vector count could not start, RuntimeError"), `_refresh_left_out` (Pfade nur aus settings(), zählt außerhalb des Locks, schreibt nur bei gleicher Kennung und gleichem Pfad, Moment = Messende, LRU auf 4), `join_left_out_refresh`, `forget_left_out_counts` (Testhilfen).
- conftest.py: neue autouse-Fixture `quiesce_the_left_out_refresh` (join + Cache leeren, vor und nach jedem Fall).
- RED-Beleg (be10d8be gegen e2df8da6): 10 Fehlschläge (7 in test_status_leave_out.py, 3 Parameter in test_phase40_audit.py); die conftest-Änderung ging bewusst erst mit dem fix-Commit, weil sie sonst jede Testdatei rot gemacht hätte.
- Tests: up_to_the_ceiling_is_counted_at_once, above_the_ceiling_comes_from_the_background, a_left_out_refresh_that_cannot_start_is_tried_again, the_left_out_cache_ages_from_the_end_of_the_count, the_left_out_cache_holds_at_most_four_lists, a_refilled_vector_stock_drops_the_cached_figure, the_ceiling_of_the_synchronous_count_is_a_hundred_thousand_documents. test_phase40_audit.py: `test_p1_the_vector_figure_above_a_hundred_thousand_documents_comes_from_the_background` mit echter Grenze, parametrisiert 100 000 (sofort), 100 001 und 113 851 (D-41-11, nach join vorhanden).
- `LEFT_OUT_EMBEDDED_CEILING`-Reste: nur `test_status_leave_out.py:384` (`assert not hasattr(...)`, pinnt die Umbenennung). Keine in src.

## Task 2: Repräsentant = größtes filesSeen

- ScanStatsService.php: `$finished` entfällt; `$counted` per usort mit Spaceship über `[-filesSeen, finished ? 0 : 1, id]`; `$representative = $counted[0] ?? $members[0];` Kommentar mit Begründung (#25, 178k gegen 246k, deterministischer Tie-Break wegen Cache-Schlüssel in status.py), Docblock von totals() nachgezogen.
- ScanStatsServiceTest.php: testTheRepresentativeIsTheMemberWithTheMostFilesSeen, testAnUnfinishedMemberWithMoreFilesSeenStillRepresents, testEqualFilesSeenPrefersFinishedThenTheSmallestId, testWithoutCountedMembersTheSmallestMemberRepresents, testTheIssue25SharesGiveTheLargerDenominator (4 Shares, Archiv 28 303 bis 112 053; alte Wahl 178 551, neue 246 053). Die beiden alten Tests sind ersetzt.
- RED-Begründung (kein PHP lokal): gegen die alte Zeile `$finished[0] ?? $counted[0] ?? $members[0]` fallen Fall 1 (wählt 5), Fall 2 (wählt fertiges 5) und Fall #25 (wählt 11 mit 44 551) rot; Gleichstand und Rückfall waren auch alt grün und pinnen das Verhalten. Lokal belegt: `php -l` beider Dateien (Docker php:8.3-cli) und die Sortierausdrücke in einem Probeskript (31,40,17 / 9,5 / 40,17). PHPUnit-Lauf folgt im CI-Job von 41-08.
- docs/admin-page.md: neue Regel an beiden Stellen, plus ein Satz zur Hintergrundzählung über 100 000 (fünf Minuten vorgehalten, bis zur ersten Zählung Rechnung wie in 1.5).

## Baumhash-Paare

| Paar | alt | neu |
|---|---|---|
| PACKAGE (80 Dateien) | b8769239... | 906e72a0... |
| PHP (110 Dateien) | 599393dc... | eb7fd98f... |

Beide zweimal gerechnet (40b-baumhash.py und find/sort/tr/sha256sum), `-k tree_hash` grün.

## Verifikation

- test_status_leave_out.py, test_phase40_audit.py, test_status_endpoint.py: 193 passed, 7 skipped; test_status_leave_out.py dreimal hintereinander grün (27 passed).
- test_admin_ui_contract.py, test_phase33_audit.py, test_phase34_audit.py (lesen docs/admin-page.md): 248 passed.
- tests/test_s*.py und tests/test_p*.py (neue autouse-Fixture über viele Dateien): 1733 passed, 253 skipped.
- ruff check, ruff format --check, pyright (latest) 0 errors, vulture 80 grün.
- Keine U+2013/U+2014 im Delta, keine Umlaute in Code.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Abgelaufener Wert nicht verwerfen**
- **Found during:** Task 1
- **Issue:** Der Plan sah bei abgelaufenem Cache "None und Start" vor. Das hätte das Feld alle 5 Minuten für einen Poll entfernt und die Seite auf die Rechnung von 1.5 springen lassen.
- **Fix:** Stale-while-revalidate wie Kandidat F, nur bei gleicher Bestands-Kennung; Test prüft es ausdrücklich.
- **Commit:** e244425e

**2. [Rule 1 - Bug] Bestands-Kennung ohne mtime**
- **Issue:** `st_mtime_ns` ändert sich bei jedem WAL-Checkpoint des Embedding-Workers, der Wert wäre auf aktiven Instanzen fast nie gültig.
- **Fix:** Kennung = (Pfad, st_dev, st_ino); ein Neubefüllen per Ersetzen der Datei wird erkannt (Test), Änderungen am Ort deckt die TTL.

**3. [Rule 3 - Blocking] S2-Audittest pinnt die Aufrufe von embedded_in_storages**
- **Issue:** `test_s2_the_route_takes_both_paths_from_the_settings_only` erlaubte genau einen Aufruf.
- **Fix:** Der Thread bekommt nur die Storage-IDs und löst die Pfade selbst über settings() auf; der Test erlaubt nun genau die zwei Aufrufe, beide mit `resolved.state_db, resolved.vectors_db`.

**4. Testfall #25 in PHP:** indexedLeftOut 113 851 ist keine Eingabe von ScanStatsService::totals(); die Zahl ist im Python-Test mit echten 113 851 Zeilen belegt, der PHP-Fall verweist darauf.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche: keine Route, kein Feld; Logzeilen nur mit Klassennamen; Cache auf 4 Schlüssel begrenzt (T-41-08 bis T-41-11 je mit Test).

## Self-Check: PASSED

- Alle sieben Commits (be10d8be bis fbbfa1f7) vorhanden, alle acht geänderten Dateien vorhanden.
