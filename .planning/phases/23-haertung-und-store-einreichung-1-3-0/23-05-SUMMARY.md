---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 05
subsystem: php-companion / migration
tags: [migration, issue-14, gone-repair, phpunit, REL-03]
requires:
  - "257caac (ACL-Fix Issue #14)"
  - "QueueMapper::requeueAs"
provides:
  - "Version001300Date20260927000000: einmaliger Reparaturlauf der skipped(gone)-Fehlurteile"
  - "PHPUnit-Beweis in php.yml (D-10, erster Teil)"
affects:
  - "Plan 23-06 (Upgrade-CI, D-10 zweiter Teil)"
  - "Plan 23-08 (Audit des #14-Pfads)"
tech-stack:
  added: []
  patterns:
    - "Datenmigration in postSchemaChange, Band 1000, eine Transaktion je Band mit rollBack plus Rethrow"
    - "QueryBuilder-Mock mit Aufzeichnung von Statement-Art, Spalten und Parametern"
key-files:
  created:
    - php/lib/Migration/Version001300Date20260927000000.php
    - php/tests/Unit/Version001300Date20260927000000Test.php
  modified:
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Literale 'skipped'/'gone' direkt in SELECT und DELETE statt Klassenkonstanten, damit das Akzeptanzkriterium (zwei Treffer) und der key_link greifen"
  - "CI-Beweis über einen eigenen Branch ci-23-05-gone-repair statt Push auf main, damit main nicht am Orchestrator vorbei bewegt wird"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-27
  tasks: 2
  files: 3
---

# Phase 23 Plan 05: gone-Reparaturlauf als Migration Summary

Neue Migration Version001300Date20260927000000 reiht beim Upgrade auf 1.3.0 alle skipped(gone)-Einträge aus oc_findling_file_state einmalig als content neu ein und löscht ihre Fehlurteile, je Band von 1000 in einer Transaktion; acht PHPUnit-Fälle belegen es in CI (311 auf 319 Tests).

## Was gebaut wurde

- **Migration** (`php/lib/Migration/Version001300Date20260927000000.php`): Konstruktor mit genau `IDBConnection` und `QueueMapper`, kein Containerkollaborateur. `postSchemaChange` liest `file_id` mit `state='skipped' AND reason='gone'`, bandet zu 1000 (`private const BAND`, begründet über Parametergrenzen und das private `QueueMapper::DELETE_BAND`), je Band `beginTransaction`, `requeueAs($band, KIND_CONTENT)`, DELETE mit `state='skipped' AND reason='gone' AND file_id IN (band)`, `commit`; bei `Throwable` `rollBack` und Rethrow. Ausgabe nur als Zahl: `no gone verdicts to repair` bzw. `requeued %d files once judged gone`. Schema unberührt (changeSchema nicht überschrieben). Klassenkommentar mit Grund (#14), Löschzwang (revokeFailures nimmt nur failed zurück, PHP schreibt nie indexed), Idempotenz, kein Containeraufruf, Dateinamen-Satz wörtlich.
- **Test** (`php/tests/Unit/Version001300Date20260927000000Test.php`), acht Fälle: leere Tabelle (kein requeueAs, keine Transaktion, eine Infozeile), Einreihen und Löschen mit Reihenfolge `begin, requeue, delete, commit`, nur skipped(gone) im SELECT und DELETE, Rollback ohne commit und ohne DELETE mit weitergeworfener Ausnahme, 2500 Zeilen als Bänder 1000/1000/500 in drei Transaktionen, zweiter Lauf als No-op, Konstruktor per Reflection (`assertCount(2, ...)`, IDBConnection und QueueMapper), Schema unberührt (`schemaClosure` mit `self::fail`).
- **Ledger**: `PHP_FILES_TODAY` 70 auf 72, `PHP_TREE_HASH_TODAY` = `d28262d9643285aa62dff1225692aac9adb95106d1182bf5b6b562d8a152ac3b`, datierter Absatz "Moved on 2026-09-27 by plan 23-05".

## Belege

| Prüfung | Ergebnis |
|---------|----------|
| `php -l` Migration, lokal im `nextcloud:35`-Image | No syntax errors detected |
| `php -l` Test, lokal im `nextcloud:35`-Image | No syntax errors detected |
| Akzeptanz-Greps Migration | `requeueAs(` 1, `'gone'` 2, `rollBack` 1, ExAppService/exAppRequest/IClientService 0 |
| `git diff --quiet 8b060e5 -- .../Version001300Date20260924000000.php` | Exit 0 (bestehende Migration unverändert) |
| OCP-Signaturen im Image gegen die Mocks geprüft | beginTransaction/commit/rollBack `void`, eq/in `string`, fetchAll/closeCursor passen |
| `uv run pytest -q tests/test_measurement_scripts.py` | 435 passed |
| `uv run pytest -q` (volle Suite) | 3339 passed, 15 skipped |
| ruff check, ruff format --check, pyright (latest), vulture | grün, 0 Fehler |

PHPUnit ist laut php.yml und `php/tests/bootstrap.php` CI-only (braucht einen nextcloud/server-Checkout mit `tests/bootstrap.php`, den das Release-Image nicht enthält). Lokal daher nur `php -l` im nextcloud:35-Image, der Testlauf in CI.

### CI auf Kopf 5e0c57c (Branch `ci-23-05-gone-repair`)

| Workflow | Run-ID | Urteil |
|----------|--------|--------|
| PHP and store metadata gates (php -l, info.xml, PHPUnit) | 36286662554 | success |
| Python gates | 36286662584 | success |
| Integration | 36286662572 | success |
| Resilience | 36286662597 | success |
| HaRP deploy | 36286662639 | success |

PHPUnit-Zahl: **vorher 311** (Run 36262662006 auf main, Kopf 257caac, "OK (311 tests, 1138 assertions)"), **nachher 319** (Run 36286662554, "OK (319 tests, 1186 assertions)"), also genau +8 neue Fälle. Kein roter Ast, keine Wiederholung nötig.

## Commits

| Task | Commit | Nachricht |
|------|--------|-----------|
| 1 (RED) | 8634346 | test(23-05): add failing cases for the gone repair migration |
| 1 (GREEN) | fc5e933 | feat(23-05): requeue the gone verdicts of issue #14 once on upgrade |
| 2 | 5e0c57c | test(23-05): move the php tree ledger to 72 files |

## Deviations from Plan

1. **Push-Ziel:** Der Plan sagt "git push" und liest php.yml auf main. Ich habe den Worktree-Kopf nach `origin/ci-23-05-gone-repair` gepusht, nicht nach main, weil der Orchestrator main besitzt (Merge und Push nach der Welle). php.yml läuft bei jedem Push mit php/**-Änderung, der Beweis ist gleichwertig. Remote-main stand zum Zeitpunkt auf a5f6d50 (meine Basis), der spätere Merge ist ein Fast-Forward. Der Hilfsbranch kann nach dem Merge gelöscht werden.
2. **Literale statt Konstanten** für 'skipped'/'gone' in SELECT und DELETE, damit `grep -c "'gone'"` wie gefordert 2 liefert.

## TDD Gate Compliance

RED-Commit 8634346 (`test(...)`) vor GREEN-Commit fc5e933 (`feat(...)`). Der RED-Stand ließ sich lokal nicht ausführen (PHPUnit CI-only) und wurde bewusst nicht gepusht, um keinen roten CI-Lauf zu erzeugen; die Fälle referenzieren eine zu dem Zeitpunkt nicht existierende Klasse und wären rot gewesen.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche über das Threat Register hinaus. T-23-16 (DELETE-Bedingung mit drei Parametern, Testfall), T-23-17 (Transaktion je Band, Rollback-Testfall) und T-23-19 (Ausgabe nur Zahl, Wortlaut geprüft) sind umgesetzt.

## Self-Check: PASSED

- FOUND: php/lib/Migration/Version001300Date20260927000000.php
- FOUND: php/tests/Unit/Version001300Date20260927000000Test.php
- FOUND: Commits 8634346, fc5e933, 5e0c57c
