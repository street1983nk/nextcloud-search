---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 11
subsystem: audit, exclusions, admin-routes, reconcile
tags: [audit, security, bugs, performance, excl-01, excl-02, excl-03, pol-01, pol-03, h-33-01, h-33-02, tdd]
requires:
  - "33-01 bis 33-09: Muster, Kehrjob, Weg C, Admin-Seite, Grenzblock, Kataloge, Doku, Nachweis"
  - "33-10: Owner-Abnahme vom 18.10.2026 (Voraussetzung für das Abhaken)"
provides:
  - "33-AUDIT.md geschlossen: status fixed, H-33-01 und H-33-02 gefixt, sechs LOW entschieden, drei nicht blockierende Owner-Fragen"
  - "backend/tests/test_phase33_audit.py: Orakel, Korpus, Quelltext-, Instanz-, Räumweg- und Regressionsproben ohne xfail (116 passed gegen 8090)"
  - "EXCL-01, EXCL-02, EXCL-03, POL-01, POL-03 Complete"
affects: [34, 36]
tech-stack:
  added: []
  patterns:
    - "Regelrouten nehmen Listen als mixed und lehnen eine Nicht-Liste mit einem bestehenden Code ab, statt den Kern in einen TypeError laufen zu lassen"
    - "appconfig-Lesestellen fangen AppConfigTypeConflictException und lesen den Schlüssel als unbrauchbare Liste mit Zählerwarnung"
    - "Testorakel fragt das PHP-Image nach der Normalizer-Klasse, statt sie aus dem Imagenamen zu raten"
    - "Performance auf der Instanz verschränkt messen (Sätze rotierend je Runde), Drift sonst als Effekt missverstanden"
key-files:
  created:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-11-SUMMARY.md
  modified:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-AUDIT.md
    - backend/tests/test_phase33_audit.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Controller/SettingsController.php
    - php/lib/Service/ExclusionService.php
    - php/tests/Unit/SettingsControllerTest.php
    - php/tests/Unit/ExclusionServiceTest.php
    - docs/admin-page.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "33-11: H-33-01 gefixt (ff4deaa9): previewRules/saveRules nehmen exclusions und exclusionPatterns als mixed, Nicht-Liste ergibt 400 mit dem bestehenden Code empty; Zwilling exclusions (Lücke seit 1.4.2) im selben Fix"
  - "33-11: H-33-02 gefixt (3657bb43): patterns() und prefixes() lesen einen Schlüssel anderen Typs als leere Liste, eine Warnzeile nur mit Zählern; Zwilling prefixes() war auf 8090 ebenso rot"
  - "33-11 (Orchestrator-Linie, überstimmbar): L-33-01 accept, xfails durch Image-Probe und dokumentierten Rückfall ersetzt"
  - "33-11 (Orchestrator-Linie, überstimmbar): L-33-02 accept, Zielphase 36, Owner-Frage F1 (Bidi-Zeichen als control_character)"
  - "33-11 (Orchestrator-Linie, überstimmbar): L-33-03 accept mit Doku-Präzisierung in docs/admin-page.md, Owner-Frage F2 (Fingerabdruck aus dem Jobargument)"
  - "33-11 (Orchestrator-Linie, überstimmbar): L-33-04 accept (H-33-01-Fix erledigt ihn nicht, macht ihn stimmig), L-33-05 accept (Selbstheilung über Weg C)"
  - "33-11 (Executor, überstimmbar): L-33-06 accept, Zielphase 36, Owner-Frage F3 (Halt am Ruhe-Tor zwischen zwei Mounts schließt den Abgleich-Zyklus)"
metrics:
  duration: "Task 3 und 4 ca. 4 h 30 min (00:20 bis ca. 04:50 Ortszeit, 19.10.2026) inkl. ca. 55 min Abgleich am Ruhe-Tor, drei Volltestläufen je ca. 11 min, einem Audit-Modullauf gegen 8090 (15 min) und CI; Task 1 und 2 in der Sitzung davor"
  completed: 2026-10-19
  tasks: 4
  files: 11
---

# Phase 33 Plan 11: Security-, Bug- und Performance-Audit der Ausschlussmuster Summary

Das Audit von Phase 33 ist geschlossen: die zwei HIGH-Befunde (500 mit Regelwerten im Log bei einer Nicht-Liste; ein Musterschlüssel anderen Typs hält den Listener an) sind samt ihren Zwillingen auf der Präfixliste gefixt und per RED/GREEN auf 8090 belegt, die Performance des Matchers, des Schreibpfads, des Kehrjobs, des Abgleichs und der Seite ist am echten Code gemessen, die sechs LOW-Befunde sind entschieden, und EXCL-01..03, POL-01 und POL-03 stehen auf Complete.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Sicherheit: Orakel-Korpus, Ablehnungen, Rechte, Logs, Quelltext | ee7a101f | 33-AUDIT.md, test_phase33_audit.py |
| 2 | Fehler: Randfälle der Räumwege und der Seite | 5b2cf2f5 | 33-AUDIT.md, test_phase33_audit.py |
| 3 | Performance-Audit (P1 bis P5) | 003cee5d | 33-AUDIT.md |
| 4a | Fix H-33-01 (Nicht-Liste in den Regelrouten) | ff4deaa9 | SettingsController.php, SettingsControllerTest.php, test_phase33_audit.py, test_measurement_scripts.py |
| 4b | Fix H-33-02 (Schlüssel anderen Typs) | 3657bb43 | ExclusionService.php, ExclusionServiceTest.php, test_phase33_audit.py, test_measurement_scripts.py |
| 4c | Bericht schließen, LOW entscheiden, abhaken | 417d9a2c | 33-AUDIT.md, admin-page.md, REQUIREMENTS.md, ROADMAP.md, STATE.md |

## Messwerte (Task 3, 19.10.2026, i5-1335U, 16 GB, Docker Desktop, 8090)

| Nr. | Messgröße | Wert | Vergleich | Urteil |
|---|---|---|---|---|
| P1 | Matcher, Median 1000 / 4000 Zeichen, gutartig / feindlich | 1,414 / 5,808 ms; 1,368 / 5,469 ms | 33-02: 1,506 / 6,025; 1,547 / 6,096 ms | in Ordnung, Quotient 4,11 / 4,00 |
| P2 | Upload je Datei, 0 / 4 / 32 Muster, verschränkt | Median 169,2 / 170,6 / 169,5 ms | 0 gegen 32: +0,2 % | in Ordnung |
| P2 | `isExcluded()` im Prozess, 68 Zeichen | 0,27 / 14,8 / 103,8 µs | Prototyp 22 / 180 µs | in Ordnung |
| P3 | Kehrjob 10 000 Dateien (2 500 Bundle) | 12 Bänder, Lauf Median 0,48 s, Max 9,59 s; 2 500 von 2 500 plus 2 Präfix-Dateien, 0 außerhalb | Wanduhr 30 s | in Ordnung |
| P4 | Weg C, 5 000 bekannte Dateien | eine Scheibe (500) je Takt (300 s), 5 000 in 3 260 s, alle Urteile weg, Runde 2 reiht nichts ein | Ruhe-Marke 100 | in Ordnung, L-33-06 |
| P5 | Admin-Seite 0 / 32 Muster | `load` Median 413,6 / 420,7 ms | +1,7 % | in Ordnung |

## Fixes

- **H-33-01 (ff4deaa9):** `php/lib/Controller/SettingsController.php`. Beide Routen nehmen die Listen als `mixed`, `listOf()` gibt eine Nicht-Liste als Code `empty` zurück (bestehender Code und Satz, kein neuer Katalogtext). RED 19.10.: Vorschau 400 ohne Code, Speichern 500 für String, Zahl, leeren String auf beiden Listen. GREEN: 79 passed auf 8090; PHPUnit +16 Fälle.
- **H-33-02 (3657bb43):** `php/lib/Service/ExclusionService.php`. `patterns()` und `prefixes()` fangen `AppConfigTypeConflictException`, Warnzeile mit `unusable: 1, inForce: 0`. RED: für beide Schlüssel Seite 500, Übersicht 500, PUT ohne Queue-Zeile, `diagnose` Exit 1. GREEN: alle fünf Müllformen und der Zwilling grün; PHPUnit +3 Fälle.
- Je Fix volle Suite (5705 passed, 252 skipped), ruff, ruff format, pyright (latest) 0, vulture, `php -l`, Baumhash-Journal im selben Commit (`2f07e7fb...`, dann `79bbd1f1...`). Kein Fix berührt Schema, Marken oder Migration (D-30-08), keiner einen sichtbaren Satz.

## Entscheidungslinien des Orchestrators (Owner schlief, überstimmbar)

| Befund | Linie | Umgesetzt |
|---|---|---|
| H-33-01 | fixen, bestehender Code, Zwilling `exclusions` mit | ja, `empty`, Zwilling mit Regressionstest |
| H-33-02 | fixen, fail-open wie bestehende Müll-Behandlung, Zwilling `prefixes()` prüfen | ja, Zwilling auf 8090 rot belegt und mitgefixt |
| L-33-01 | accept, kein xfail darf bleiben | xfails durch Image-Probe plus dokumentierten Rückfall im Orakel ersetzt, grün auf beiden Images |
| L-33-02 | accept, Zielphase 36, Owner-Frage | F1 |
| L-33-03 | accept mit Doku-Korrektur, Owner-Frage zum Jobargument | `docs/admin-page.md` präzisiert, F2 |
| L-33-04 | prüfen, ob H-33-01 ihn erledigt, sonst accept | erledigt ihn nicht, accept |
| L-33-05 | accept | accept |
| L-33-06 | (neu in Task 3, keine Linie) | Executor: accept, Zielphase 36, F3 |

## Offene Owner-Fragen (alle LOW, keine blockiert)

- **F1 (L-33-02):** Bidi- und Formatzeichen (U+200E, U+200F, U+202A bis U+202E, U+2066 bis U+2069, U+061C) in Mustern und Präfixen als `control_character` ablehnen?
- **F2 (L-33-03):** Den Fingerabdruck aus dem Argument des Kehrjobs nehmen, damit auch die Fehlerzeile des Kerns ihn nicht nennt?
- **F3 (L-33-06):** Die Zyklusregel des Abgleichs in Phase 36 so ändern, dass ein Halt am Ruhe-Tor zwischen zwei Mounts den Zyklus offen lässt?

## CI

- Stand 3657bb43 (Push von ee7a101f bis 3657bb43): PHP and store metadata gates 39189895915 (PHPUnit OK, 810 Tests), Python gates 39189895896, Security scans 39189895934, Resilience 39189895905, Integration 39189895884, HaRP deploy 39189895882, Multi-arch image 39189895922, OpenSSF Scorecard 39189895921: alle grün.
- Stand 417d9a2c (Abschluss): Verify-Kommando von Task 4 vollständig grün (EXIT 0): php -l, volle Suite 5705 passed / 252 skipped, ruff, ruff format, pyright 0, vulture, still_open ohne CRITICAL/HIGH/MEDIUM, kein xfail, Owner-Abnahme gefunden, fünf Haken, REUSE 2736/2736, CI des HEAD: Security scans 39192390285 und OpenSSF Scorecard 39192390276 grün (die übrigen Workflows filtern auf Pfade, die ein Doku- und Planungs-Commit nicht berührt); `gh run list --commit` lieferte dazu zwei Dependabot-Läufe des Branches (39193353830, 39193332535, grün), die nicht zu diesem Commit gehören.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Zwillinge der zwei HIGH-Befunde mitgefixt**
- **Found during:** Task 4 (RED-Lauf)
- **Issue:** `exclusions` als String/Zahl ergab ebenso 500; `exclusions` mit `--type=integer` brach Seite, Übersicht und Listener wie H-33-02.
- **Fix:** im selben Fix je Befund, mit eigenem Regressionstest (`prefix list: ... instead of a list`, `test_a_prefix_key_of_another_type_breaks_neither_page_nor_listener`).
- **Commits:** ff4deaa9, 3657bb43

### Weitere Abweichungen

1. **P3-Korpus halbiert:** 10 000 statt 20 000 Dateien, 2 500 statt 5 000 im Bundle, weil vor der Messung nur 2,71 bzw. 2,27 GB RAM frei waren (Plan erlaubt das unter etwa 4 GB). P4 lief mit den vollen 5 000.
2. **P2 zweimal gefahren:** die erste Blockreihe (0, 4, 32, 0) maß Drift (zweiter 0-Block 28 Prozent langsamer), verworfen und verschränkt neu gefahren. Die Serverzeit kommt aus dem Access-Log und aus einer Messung im Prozess, weil Loglevel 2 keine Zeile je Anfrage schreibt und Loglevel 0 Muster in Kernzeilen trägt (L-33-03).
3. **P4-Vorbereitung:** der Zähl-Crawl reiht nicht ein, und das Einreihen über den Abgleich lief mit 500 je Takt; die 5 000 Dateien wurden deshalb über `QueueService::enqueueFile` im Container bekannt gemacht (dieselbe Zeile wie Crawl oder Listener; nur Vorbereitung, nicht gemessen). Zwei Skriptläufe abgebrochen (falsche Warte-Bedingung; Kommandozeile mit 500 IDs zu lang).
4. **Aufräumfehler bei P3:** cron ohne Pause, Papierkorb vor dem Ende des SubtreeExpandJob geleert; das reproduzierte den bekannten Nebenbefund aus `deferred-items.md` (Fehlerzeile mit Zahlen-Argument, kein Indexrest). Danach mit Pause aufgeräumt.
5. **Neuer Befund L-33-06** aus P4, ohne Linie des Orchestrators: als Executor-Entscheid accept, Zielphase 36, Owner-Frage F3.
6. **Zwischen-xfail:** für saubere Einzel-Commits standen die H-33-02-Fälle im Commit ff4deaa9 noch als strict xfail und fielen in 3657bb43; die Umstellung von L-33-01 (ohne Produktcode) reiste in ff4deaa9 mit.
7. **Probe-Korrektur:** die neue Zwillingsprobe erwartete Ganzzahlen im Log-Kontext; der Kern schreibt `app` dazu und die Zahlen als Text. Erwartung auf genau `{"unusable": "1", "inForce": "0"}` gesetzt.
8. **Doku L-33-03:** neben Debug-Level und Jobargument nennt der Absatz auch das Feld `url` des Kerns (bei einem Upload der Pfad), gesehen an der Warnzeile von H-33-02 während eines PUT; Doku, kein Katalogtext.
9. **STATE.md und ROADMAP.md von Hand** (Vorgabe des Orchestrators), keine SDK-Handler.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-33-33 (Laufzeitreihe, Schreibpfad), T-33-34 (Orakel), T-33-35 (Rechte), T-33-36 (Logs) und T-33-37 (Abhaken erst nach Owner-Abnahme und geschlossenem Bericht) sind im Bericht belegt.

## Self-Check: PASSED

- FOUND: 33-AUDIT.md (status fixed, still_open nur LOW), 33-11-SUMMARY.md, test_phase33_audit.py ohne xfail
- FOUND: ee7a101f, 5b2cf2f5, 003cee5d, ff4deaa9, 3657bb43, 417d9a2c
- REQUIREMENTS.md: fünf Zeilen `- [x]`, Traceability fünfmal Complete
- Endzustand 8090: `exclusions` `["Archiv"]`, `exclusion_patterns` fehlt, Jobliste nur ScanRecountJob, Korpora `Perf3311k`, `Perf3311r`, `Perf3311w`, `Perf3311i` ohne filecache-Zeile, Papierkorb geleert
