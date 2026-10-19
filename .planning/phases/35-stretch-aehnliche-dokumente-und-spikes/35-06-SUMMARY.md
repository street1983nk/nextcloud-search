---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 06
subsystem: php-companion
status: abgeschlossen
tags: [STR-01, similar-documents, permission-recheck, php]
requires:
  - 35-05 (POST /similar, Drahtformat {fileId, limit} -> {candidates:[{fileId}], degraded})
provides:
  - "ExAppService::similarCandidates(string $userId, int $fileId, int $limit, float $secondsLeft, float $ceilingSeconds): ?array{candidates:list<int>,degraded:bool}"
  - "SearchService::similar(IUser $user, int $sourceId, SearchCaps $caps): SimilarOutcome"
  - "SearchService::SIMILAR_MAX_HITS = 10, SearchService::SIMILAR_CANDIDATES = 30 (public)"
  - "SimilarOutcome {?ApprovedHit source, list<ApprovedHit> hits, bool degraded, ?string failure}"
affects:
  - 35-07 (PageController/Template verzweigen auf SimilarOutcome)
key-files:
  created:
    - php/lib/Service/SimilarOutcome.php
  modified:
    - php/lib/Service/ExAppService.php
    - php/lib/Service/SearchService.php
    - php/tests/Unit/ExAppServiceTest.php
    - php/tests/Unit/SearchServiceTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Backend-Ausfall nutzt den Bestandsnamen SearchOutcome::FAILURE_BACKEND_SILENT (SimilarOutcome verweist per Konstante), kein neuer Name"
  - "Treffer-Bau aus dem bestätigten Knoten als private hitOf() für run() und similar() gemeinsam, damit beide Ansichten nicht auseinanderlaufen"
  - "Ungültige Quell-ID (<= 0) ergibt ebenfalls FAILURE_SOURCE_UNAVAILABLE ohne Containeraufruf (ein Zustand, O4 (a))"
  - "Doppelte Nachbar-IDs werden in ExAppService still zusammengelegt (erste Fundstelle zählt), nicht geloggt"
metrics:
  completed: 2026-10-19
  tasks: 2
  files: 6
---

# Phase 35 Plan 06: PHP-Rechtegrenze für ähnliche Dokumente Summary

`SearchService::similar` prüft die Quelle über `readableFile` vor jedem Containeraufruf, fragt dann `/similar` über `ExAppService::similarCandidates` und lässt jeden Nachbarn durch denselben Recheck; höchstens zehn Treffer, alle Felder aus dem bestätigten Knoten, `SimilarOutcome` ohne Zählfeld.

## Commits

| Schritt | Commit | Inhalt |
|---|---|---|
| Task 1 + 2 (gemeinsam, laut Plan) | d43eb0e6 | similarCandidates, similar, hitOf, SimilarOutcome, 13 PHPUnit-Fälle, Baumhash |

## Umsetzung

- **similarCandidates:** Body genau `{fileId, limit}` an `/similar`, Limit auf 1..100 geklemmt, Quelle <= 0 ohne Rundreise null; `candidates` fehlt/kein Array: null plus statische Warnung `Findling: malformed similar answer`; verworfen werden Nicht-int, <= 0 und die Quelle selbst, geloggt nur `['count' => n]`; `degraded` wird durchgereicht. Kein Kanarien-Zweig.
- **similar():** Drift (wie run) -> `FAILURE_VERSION_DRIFT`; kein Home-Ordner -> `FAILURE_NO_HOME_FOLDER`; Quelle nicht bestätigt -> `FAILURE_SOURCE_UNAVAILABLE` ohne Log; dann Containeraufruf mit `SIMILAR_CANDIDATES`, Restzeit und `min(requestCeilingSeconds, PAGE_REQUEST_TIMEOUT_SECONDS)`; null -> `FAILURE_BACKEND_SILENT` mit Quelle; Quelle ein zweites Mal verworfen; `mountsOfUser` + `reduceIds` als Vorauswahl; Recheck bis 10 Treffer, `recheckAbsolute` oder Deadline.
- Zeilenfolge belegt: `readableFile($userFolder, $sourceId)` Zeile 581, `similarCandidates(` Zeile 589, Nachbar-Recheck Zeile 641.
- ACL-Gegenprobe: `grep -c "getFirstNodeById\|isReadable()" SearchService.php` vorher 3, nachher 3; `test_php_acl_boundary.py` grün, Register unverändert.
- Baumhash: 106 Dateien, `35504a90...91f39e`, unabhängig per find/sort/tr/sha256sum in der Shell nachgerechnet, gleich.

## PHPUnit-Fälle (nur CI)

- ExAppServiceTest (6): gültige Antwort in Reihenfolge; Quelle und unbrauchbare IDs verworfen und nur gezählt; stilles Backend null statt leerer Liste; fehlende Kandidatenliste null mit statischer Zeile; degraded durchgereicht; Anfrage an `/similar` mit genau fileId und limit.
- SearchServiceTest (7): unlesbare/unbekannte/ungültige Quelle mit `expects(never)` auf similarCandidates; kein Home-Ordner; Versionsdrift; stilles Backend mit bestätigter Quelle; 12 Vorschläge, 2 unlesbar, genau 10 in Containerreihenfolge mit Titel/Pfad aus dem Knoten; Quelle nie eigener Nachbar; Recheck-Deckel und Zeitbudget beenden die Liste mit dem Bestätigten.
- Rot lokal nicht sichtbar (kein PHP-Test-Harness ohne nextcloud/server); jeder Fall ruft die neue Methode bzw. Konstante auf und schlüge ohne Implementierung fehl.
- PHPUnit vorher: **818 Tests** (php.yml-Lauf 39316803593 auf main, 73a018fe). Erwartet nachher: 831. Nachher-Zahl offen bis Orchestrator-Push.

## Deviations from Plan

- **Rule 2 (Drift-Vermeidung):** Treffer-Bau aus `run()` in `hitOf()` ausgelagert und in beiden Pfaden genutzt, statt den Block zu kopieren. Verhalten von `run()` unverändert (gleiche Felder, gleiche Prüfreihenfolge nach `readableFile`).
- **Kein Push, kein CI-Lauf** (Worktree, Orchestrator merged und pusht); PHPUnit-Nachher-Zahl daher offen.
- `php -l` per Docker lief über einen `sh -c`-Aufruf statt der Schleife aus dem Plan (Worktree-Sperre für `$PWD`), Inhalt gleich.
- Volle Suite: ein Lifespan-Test (`test_a_disable_while_the_cycle_waits_silences_it_again`) fiel einmal unter Last (parallele Agenten), isoliert 3x grün, danach volle Suite grün. Nicht durch diesen Plan verursacht.

## Gates

- php -l: alle fünf geänderten PHP-Dateien ohne Syntaxfehler (php:8.3-cli).
- ruff check, ruff format, pyright (latest) 0 Fehler, vulture sauber, reuse lint konform (2800/2800).
- Volle Python-Suite: 5814 passed, 264 skipped.

## Threat Flags

Keine neuen Flächen außerhalb des Threat-Modells; T-35-19 bis T-35-23 wie geplant umgesetzt.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: php/lib/Service/SimilarOutcome.php, php/lib/Service/SearchService.php, php/lib/Service/ExAppService.php.
- Commit vorhanden: d43eb0e6.
