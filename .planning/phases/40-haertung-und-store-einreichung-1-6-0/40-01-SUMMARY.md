---
phase: 40-haertung-und-store-einreichung-1-6-0
plan: 01
subsystem: audit
tags: [audit, security, leaveOut, harp, watcher, ci-gate]
requires:
  - 39-01 (Weg C, leaveOut, rulesPending)
  - 39-03 (IN-Fixes)
  - 38-01, 38-02 (Tunnel-Wächter, Kopierbefehl)
provides:
  - 40-AUDIT.md (status fixed, 0 CRIT / 0 HIGH / 0 MEDIUM, 6 LOW)
  - backend/tests/test_phase40_audit.py (Proben S1 bis S7, B1 bis B6, P1 bis P3)
  - scripts/ci/head_green.sh (CI-Gate je Commit für 40-02 bis 40-05)
affects:
  - 40-02 (Versionssprung startet auf auditiertem, grünem Kopf efcf26c5)
  - 40-04 (Owner-Runde: F-40-06 und der geänderte Kopierbefehl zur Kenntnis)
tech-stack:
  added: []
  patterns:
    - "Probe der SQL-Texte über eine aufzeichnende sqlite3.Connection (factory), weil der trace callback die Werte einsetzt"
    - "Wächter-Leerlauf gezählt über ein sha256sum vorn im PATH, CPU aus /proc/<pid>/stat"
    - "CI-Gate je Commit: head_green.sh <sha> <Workflowname>..."
key-files:
  created:
    - backend/tests/test_phase40_audit.py
    - scripts/ci/head_green.sh
    - .planning/phases/40-haertung-und-store-einreichung-1-6-0/40-AUDIT.md
    - .planning/phases/40-haertung-und-store-einreichung-1-6-0/deferred-items.md
  modified:
    - backend/src/findling/api/status.py
    - backend/docker/harp_connect.sh
    - docs/harp-tunnel.md
    - .github/workflows/deploy-harp.yml
    - .github/workflows/python.yml
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/tests/Unit/StorageServiceTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "F-40-01 bis F-40-04 (LOW) gefixt: leaveOut nur kanonisch, Wächter trägt unfertige Zeilen über, test -s im Kopierbefehl, Längendecke 8000 auch auf der PHP-Seite"
  - "F-40-05 (LOW, Rennen rules_changed_at) und F-40-06 (LOW, Tombstones ausgelassener Storages im Zähler) akzeptiert; F-40-06 zur Kenntnis in die Owner-Runde 40-04"
metrics:
  duration: ca. 190 min inkl. ca. 11 min Volltestlauf und ca. 55 min CI
  completed: 2026-10-28
  tasks: 3
  files: 13
---

# Phase 40 Plan 01: Launch-Audit 1.6.0 Summary

Audit-Gate über v1.5.1..336ccae7 (48 Dateien, 2258 Zeilen dazu, 199 weg) mit
gefahrenen Proben in test_phase40_audit.py: 0 CRIT / 0 HIGH / 0 MEDIUM, sechs
LOW, davon vier gefixt (leaveOut nur kanonisch, Wächter verliert keine
langsame Zeile mehr, ein leerer Lesevorgang leert kein Zertifikat, Längendecke
von leaveOut auch auf der Admin-Seite) und zwei begründet akzeptiert; alle
acht Workflows auf dem Code-Kopf efcf26c5 grün, belegt mit dem neuen
scripts/ci/head_green.sh.

## Was gebaut wurde

- **Task 1 (Security):** Proben S1 (15 Missbrauchswerte je 422 vor jeder
  Abfrage, Doppel-IDs, nur Platzhalter in den Anweisungen, /status einzige
  ADMIN-Route), S1b (kein Codepfad ruft die discussion-URL ab), S2 (fehlende
  vectors.db bleibt fehlend, Sonderzeichenpfad, Schreibversuch scheitert,
  WAL-Schreiber blockiert nicht), S3 (Injektion, 10 000 x509-Zeilen, Symlinks
  in Verzeichnis mit Leerzeichen, Kopierbefehl der Doku), S4 (keine
  Markup-Senke in admin.js, Sätze über `p()`), S5, S6, S7 (starlette 1.6.0 im
  Lock). Befunde F-40-01 bis F-40-04 als strict xfail.
- **Task 2 (Bugs, Performance):** B1 (PHPUnit-Fall `//` im Login-Namen und in
  der Wurzel), B2, B3, B4 (Lektüre, F-40-05), B5 (fastapi-Release-Notes 0.144
  bis 0.161.1 gegen die Suite), B6 (F-40-06 beziffert), P1 (Median über
  100 000 Dokumente: 55,0 ms ohne, 95,2 ms mit leaveOut; echte Decke 100 000
  belegt), P2 (1 Container-Aufruf je Poll nach der Erstindexierung, 2
  währenddessen, v1.5.1 und HEAD gleich), P3 (Leerlauf und Flut, Linux).
- **Task 3:** vier Fix-Commits, head_green.sh mit Selbsttest, Audit
  geschlossen, CI-Gate auf Code- und Doku-Kopf.

## Commits

| Commit | Inhalt |
|---|---|
| 4b48e79a | test(40-01): security probes of the v1.6 changes |
| 4965dcc2 | test(40-01): bug and performance probes of the v1.6 changes (PHP-Baumhash 2b5effd0) |
| 7193cb5a | fix(40-01): leaveOut takes canonical numbers only (F-40-01), Paket-Baumhash 3c7df60a |
| 12f7dfe0 | fix(40-01): the tunnel watcher keeps a line that arrives slower than its poll (F-40-02) |
| 7a2a68a2 | fix(40-01): an empty read never replaces a certificate in the copy command (F-40-03) |
| 0c875261 | fix(40-01): the admin page holds the length ceiling of leaveOut too (F-40-04), PHP-Baumhash 3e366f7a |
| efcf26c5 | ci(40-01): head_green.sh as the CI gate on one commit, audit probes by name |
| 20fcca75 | docs(40-01): security part of the 1.6.0 audit |
| 69c52b65 | docs(40-01): bug and performance part of the 1.6.0 audit |
| d5807b67 | docs(40-01): close the 1.6.0 audit |

## Verifikation

- Lokale Suite auf efcf26c5 mit der Ignore-Liste der Phase: **6095 passed, 69
  skipped** in 11:00; `test_phase40_audit.py` lokal 58 passed, 7 skipped
  (Linux-Proben); `-m timing` mit `FINDLING_TIMING=1` grün.
- Gates vor jedem Code-Commit: ruff, ruff format, pyright latest 0 Fehler,
  vulture sauber, `-k tree_hash` grün.
- `head_green.sh efcf26c5 "Python gates" "PHP and store metadata gates" "HaRP
  deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`:
  Exit 0. Läufe: Python gates 40743288537, PHP and store metadata gates
  40743288689, HaRP deploy 40743288892, Integration 40743288570, Resilience
  40743288490, Multi-arch image 40743288507, Security scans 40743288478,
  OpenSSF Scorecard 40743288696, alle success.
- Doku-Kopf d5807b67: `head_green.sh d5807b67 "Security scans"` Exit 0,
  Security scans 40748691618, OpenSSF Scorecard 40748692674.
- S3-Beleg: Python gates 40743288537, Schritt "The audit probes of 1.6.0 by
  name", 64 passed, 1 skipped; die sechs Linux-Proben mit PASSED wörtlich in
  40-AUDIT.md.
- **Offener Punkt aus 39-01-SUMMARY erledigt:** php.yml-Lauf (PHP gates
  40743288689) und python.yml-Lauf (Python gates 40743288537) vor dem
  Audit-Gate auf einem Kopf, der den 39-01-Stand enthält.
- **Selbsttest head_green.sh:** auf 297b69ba mit "Python gates" "HaRP deploy"
  Exit 0 (sieben Läufe success); mit erfundenem Namen "No such workflow" Exit 1
  ("no run of 'No such workflow'"); auf einem ungepushten Commit Exit 1 ("no
  workflow run").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PASSED-Zeilen der Wächterproben waren im CI-Log nicht sichtbar**
- **Found during:** Task 3
- **Issue:** der Testschritt von python.yml läuft mit `-q`, S3 verlangt die
  PASSED-Zeile aus `gh run view --log`.
- **Fix:** eigener Schritt "The audit probes of 1.6.0 by name" mit `-v -rs`
  (Muster des SIGKILL-Schritts).
- **Commit:** efcf26c5

**2. [Rule 1 - Bug] trace callback ungeeignet für die Platzhalterprobe**
- **Found during:** Task 1
- **Issue:** `set_trace_callback` liefert die Anweisung mit eingesetzten
  Werten, die erste Fassung der Probe war dadurch falsch rot.
- **Fix:** aufzeichnende `sqlite3.Connection` per `factory`.
- **Commit:** 4b48e79a

### Abweichungen im Vorgehen

- **Code-Kopf getrennt gepusht:** Erst efcf26c5 (letzter Code-Commit) auf
  main, dann die Doku-Commits. Sonst hätte der Code-Commit keine eigenen Läufe
  und der Verify-Befehl des Plans (`git log -1 -- . ':!.planning' ':!docs'`)
  fände keine Laufliste.
- **S3-Nachtrag ohne eigenen Commit:** Lauf-ID und PASSED-Zeilen standen vor
  dem Abschluss-Commit fest und sind in d5807b67 enthalten.
- **Kein SPDX-Kopf in head_green.sh:** die übrigen Skripte unter scripts/ci
  tragen keinen; die Lizenz kommt per REUSE.toml (`path = "**"`).
- **Prosa mit echten Umlauten:** der Plan prüft "lokale Ausführung nicht
  möglich" wörtlich und schreibt echte Umlaute vor; die Vorgabe "ASCII prose"
  des Koordinators tritt dahinter zurück.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. Die Fixes verengen nur (Muster, Längendecke,
`test -s`, Übertrag einer Zeile im Wächter).

## Offene Punkte

- **Owner-Runde 40-04:** F-40-06 (Tombstones ausgelassener Storages heben die
  Abdeckung während der Erstindexierung um bis zu Gruppengröße mal
  Tombstone-Anteil) zur Kenntnis, Entscheidung accept; Kopierbefehl in
  docs/harp-tunnel.md um `test -s` ergänzt (Entwürfe #33 und HaRP-Upstream
  verlinken nur die Doku). Kein Store-Text und kein Katalogsatz geändert.
- deferred-items.md: Tombstones im Feld `indexed` (Stand 1.5) für v1.7 prüfen.

## Self-Check: PASSED

- Dateien vorhanden: test_phase40_audit.py, head_green.sh, 40-AUDIT.md,
  deferred-items.md, 40-01-SUMMARY.md.
- Commits vorhanden: 4b48e79a, 4965dcc2, 7193cb5a, 12f7dfe0, 7a2a68a2,
  0c875261, efcf26c5, 20fcca75, 69c52b65, d5807b67.
