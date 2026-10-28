---
phase: 32-filter-in-der-unified-search
plan: 08
subsystem: PHP-Companion (Ordnerfilter, versteckter Provider, Skript), Backend-Tests (Audit-Proben), Doku
tags: [audit, security, performance, usrch-03, korpus, waisen, owner-frage]
requires:
  - phase: 32
    provides: "32-01 bis 32-07: types und folder im Provider, Ordnerbudget, sieben Menüeinträge, versteckter Provider findling-filter, Owner-Abnahme"
provides:
  - "32-AUDIT.md: Security-, Bug- und Performance-Audit der Phase 32, Befunde M-32-01, M-32-02, L-32-01 bis L-32-07"
  - "backend/tests/test_phase32_audit.py: Quelltextproben mit eigenem Scanner und Korpus manipulierter Filterwerte gegen eine echte Instanz"
  - "Fix M-32-01: Ordnerwert in NFC, Punktsegment ist kein Ordner (d09e5a5a)"
  - "Klärung der Waisen aus 32-07 mit Positivkontrolle; neue Owner-Frage M-32-02"
affects: [Phase-32-Verifikation, Phase 36 Launch-Härtung, REL-05]
tech-stack:
  added: []
  patterns:
    - "Quelltextprobe über einen von Hand geschriebenen Zustandsautomaten statt regulärer Ausdrücke, mit Positivkontrolle je Scanner"
    - "Instanzproben in pytest, per Umgebungsvariable aktiviert, sonst übersprungen"
    - "Abgleich der Dev-Instanz fällig machen: Stempel der Tabelle reconcile um 49 Stunden zurück"
    - "Body-Vergleich gegen den Basis-Commit über einen mitschneidenden TCP-Proxy vor dem Backend"
key-files:
  created:
    - backend/tests/test_phase32_audit.py
    - .planning/phases/32-filter-in-der-unified-search/32-AUDIT.md
  modified:
    - php/lib/Search/Provider.php
    - php/tests/Unit/ProviderTest.php
    - php/tests/Unit/SearchServiceTest.php
    - backend/tests/test_measurement_scripts.py
    - docs/search-filters.md
    - docs/privacy.md
decisions:
  - "M-32-01 im Provider gefixt, nicht im SearchService: folderOf() liest die Rohform und setzt sie in die Form des Filecache (NFC); ein '.'-Segment ist ein gebauter Wert und kein Ordner. Eine allgemeine Kanonprüfung über den Cache-Eintrag hätte Freigaben und Gruppenordner (anderer Storage, anderer interner Pfad) falsch verworfen."
  - "M-32-02 nicht gefixt: der Fix läge im Abgleich (backend/src) und ist in Phase 32 verboten (D-30-08, D-32-06); Owner-Frage."
  - "L-32-01, L-32-03, L-32-04, L-32-05, L-32-07 accept mit Grund; L-32-02 als Doku in privacy.md, L-32-06 als PHPUnit-Fall gefixt."
metrics:
  duration: "ca. 330 min inkl. ca. 40 min Korpusaufbau, ca. 40 min Volltestläufe und ca. 50 min CI"
  completed: 2026-10-13
  tasks: 3
  files: 8
---

# Phase 32 Plan 08: Security-, Bug- und Performance-Audit der Filter in der Unified Search Summary

Ein Korpus aus 59 manipulierten Filterwerten lief als alice und bob gegen die Dev-Instanz: nie ein Fremdtreffer, nie 5xx außer der Array-Form, die schon im Kern scheitert, keine Logzeile mit Ordner oder Begriff im Normalbetrieb. Gefunden und gefixt: ein Punktsegment oder die NFD-Schreibung im Ordner ergab eine leere Gruppe statt der Suche ohne Filter (M-32-01). Offen als Owner-Frage: Dokumente eines gelöschten Nutzers bleiben für immer im Index (M-32-02).

## Commits

| Commit | Inhalt |
|---|---|
| `6ec32be7` | test: Audit-Proben (Quelltextscanner, Instanzkorpus) |
| `d09e5a5a` | fix: M-32-01, Ordnerwert in NFC, Punktsegment ist kein Ordner; ProviderTest; Baumhash |
| `4c481f74` | test: L-32-06, Abfragen des Ordnermodus gezählt; Baumhash; Doku L-32-01, L-32-02, L-32-03 |
| docs(32-08) | 32-AUDIT.md, SUMMARY, STATE, ROADMAP, REQUIREMENTS, deferred-items (dieser Abschluss) |

## Task 1: Security und Bugs

- Diff a632a35c..7006129d, 52 gelesene Dateien ohne Rohdaten.
- Korpus (46 Ordnerwerte, 13 Typwerte, 2 Array-Formen) gegen `findling` und `findling-filter`: vor dem Fix 12 Fälle rot (M-32-01), danach 137 passed; beide Provider antworten in allen 59 Fällen mit denselben IDs.
- Logs mit zwei Positivkontrollen sauber; Loglevel debug und Backendausfall zusätzlich gefahren (L-32-02).
- Orakel: fremder und erfundener Ordner gleich (Status, IDs), Laufzeit Rauschen.
- Quelltextproben: eine Auflösung und eine Lesefrage, kein Ordnerwert zum Container (dazu Proxy-Mitschnitt), kein Begriff oder Pfad in Logaufrufen, `findling-filter` entscheidet nichts über Rechte, Skript ohne DOM-Schreibzugriff und ohne Netz; acht Gegenproben je rot.
- CSP-Nonce, Legacy-Suche, öffentliche Links, REUSE, Store-Archiv, Workflow-Gates, Gedankenstriche gefahren.
- Waisen aus 32-07: Der Abgleich am 13.10. 01:08 lief vor dem Löschen der Messdateien (Zeitstempel aus state.db, Tabelle reconcile, Backend-Log). Positivkontrolle: Abgleich fällig gemacht, `missing=1011`, alle entfernt.

## Task 2: Performance

P1 Browser-Timing (n = 60): ohne Ordner 80 / 72 ms, enger Ordner 145 / 158 ms (Limit 5 / 10), Mehrkosten wie 32-03. P2 Query-Log: eine `getByFileIds` je Runde, eine `getByFileId` je Lauf, `oc_mounts` einmal vom Kern. P3 Skript: 4,7 KB kalt, warm 0, CPU unter 1 ms. P4 ungefilterter Body byte-gleich zur Basis. P5 eng 11 + 1 Containeraufrufe, ohne Chip 0.

## Task 3: Befunde

- M-32-01 gefixt (d09e5a5a), Regression in ProviderTest und Korpus, Gegenproben F1/F2 live je rot.
- M-32-02 Owner-Frage (siehe unten).
- LOW: L-32-02 und L-32-06 gefixt (4c481f74), L-32-01, L-32-03, L-32-04, L-32-05, L-32-07 entschieden.

## Gates und CI

- Lokal vor jedem Commit (aus `backend/`, `PYTHONUTF8=1`): ruff check, ruff format --check, pyright latest 0 Fehler, vulture ohne Befund, `node --check php/js/unified-search.js`, `php -l` per `php:8.3-cli`, volle Suite je 5637 passed, 158 skipped. `test_php_acl_boundary.py` unverändert und grün.
- CI auf 4c481f74, alle acht per `gh run watch --exit-status`: PHP and store metadata gates 38385967900 (PHPUnit 666 Tests), Python gates 38385966880, HaRP deploy 38385966780, Integration 38385966737, Resilience 38385967215, Security scans 38385967351, OpenSSF Scorecard 38385966865, Multi-arch image 38385966954.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - fehlender Beleg] PHPUnit zählte die Abfragen des Ordnermodus nicht (L-32-06)**
- **Found during:** Task 2 (P2 verlangt Doppel-Zählung und Query-Log)
- **Fix:** ein SearchServiceTest-Fall über den längsten Ordnerlauf mit `expects()`
- **Files modified:** php/tests/Unit/SearchServiceTest.php, backend/tests/test_measurement_scripts.py
- **Commit:** 4c481f74

**2. [Auftrag des Owners] Waisen über den Plan hinaus untersucht**
- Ursache der 32-07-Beobachtung geklärt, Positivkontrolle am laufenden Abgleich; dabei M-32-02 gefunden und live mit Kontrolle im selben Abgleich belegt.

**3. [Umgebung] Messkorpus unter alice statt testuser, Upload mit Login-Passwort**
- Der Korpus aus 32-03 wurde mit dem unveränderten Skript neu gebaut (rund 35 min statt 7 wegen paralleler Indexierung); das Messverfahren selbst ist ohnehin ein anderes (Browser-Sitzung).

### Hinweis zur Reihenfolge der Commits

Der Fix lag lokal schon vor dem ersten Commit vor. Für jeden Commit wurde der Baum auf genau dessen Stand gebracht (Sicherung im Scratch, betroffene Dateien auf HEAD) und die volle Suite auf diesem Stand gefahren.

## Owner-Frage

**M-32-02:** Dokumente von Storages, die die Mountliste verlassen (gelöschter Nutzer, abgeschalteter Mount), bleiben für immer im Index. Sie zeigen sich nie als Treffer, belegen aber Kandidatenplätze (im Ordnermodus einen der 1200 Ränge). Fix nur in `backend/src` oder der Queue-Semantik. Eigener Plan (Phase 36 oder Einschub), und mit welcher Karenz für Mounts, die zurückkommen können?

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: der Fix verengt nur, was als Ordner gilt; die Testdatei spricht eine Instanz nur, wenn die Umgebungsvariablen gesetzt sind.

## Self-Check: PASSED

- backend/tests/test_phase32_audit.py, 32-AUDIT.md, 32-08-SUMMARY.md vorhanden.
- Commits 6ec32be7, d09e5a5a, 4c481f74 im Log.
