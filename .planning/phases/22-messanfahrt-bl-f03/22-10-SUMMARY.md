---
phase: 22-messanfahrt-bl-f03
plan: 10
subsystem: query-ranking, messung
tags: [MESS-09, disjunction_max, E10, kaltstart]
requires:
  - "22-08/22-09: Rohdaten 98d-dismax-probe.txt, 95c, m01 aus der Anfahrt vom 26.09.2026"
provides:
  - "MESS-09 entschieden: Summe bleibt, disjunction_max dokumentiert verworfen"
  - "Ursache des leeren Kaltstarts geklärt (README 6.11)"
affects:
  - "22-11 (Bericht: E10 gehalten, MESS-09-Verweis in performance.md; Kaltstart-Lücke mit geklärter Ursache und drei Wegen)"
  - "Owner-Nachfreigabe D-02: vor der 0,24-USD-Nachmessung Wahl des Weges (a/b/c)"
tech-stack:
  added: []
  patterns:
    - "Sprachfall-Eigenrang über die Kennungen der v1.2-Rohdatei 05-sprachfaelle.txt zugeordnet (Snapshot trägt dieselben 39 Dateien)"
key-files:
  created:
    - .planning/phases/22-messanfahrt-bl-f03/22-10-SUMMARY.md
  modified:
    - docs/measurements/2026-09-v13-messung/README.md
    - docs/language-analyzers.md
    - backend/tests/test_field_plan_ranking.py
    - .planning/phases/22-messanfahrt-bl-f03/deferred-items.md
decisions:
  - "MESS-09: Entscheid Summe nach E10; tie 0.0 RBO-Median 0,8399, tie 0.1 0,9633 gegen Summe 0,9531, Schwelle +0,05 von keinem erreicht; Urteil E10 gehalten, Folge verworfen"
  - "rewrite.py byteweise unverändert, keine Baumhash-Ratsche"
  - "Leerer Kaltstart = PHP-Deckel 1,5 s gerissen, weil die erste hybride Suche bei Schalter 0 das Modell lädt (bekannter Vorfall 10.09.); kein Fix in 22-10, Owner-Wahl nötig"
metrics:
  duration: "ca. 30 min"
  completed: 2026-09-26
---

# Phase 22 Plan 10: MESS-09-Entscheid Summary

disjunction_max ist nach der eingefrorenen Regel E10 auf den Box-Rohdaten von 98d verworfen. Die Score-Summe bleibt ausgeliefert, und die Verwerfung steht mit Zahlen in docs/language-analyzers.md. Nebenbei ist die Ursache des leeren Kaltstarts aus den Rohdaten geklärt.

## Entscheid

| Bedingung (00-ablauf.md Abschnitt 6) | Schwelle | tie 0.0 | tie 0.1 |
|---|---|---|---|
| 1. RBO@10-Median gegen Altplan ≥ Summe + 0,05 | ≥ 1,0031 | 0,8399, nein | 0,9633, nein |
| 2. kein Sprachfall-Eigenrang schlechter | | ja | ja |
| 3. Latenz-Median ≤ 1,20 × Summe (4,7667 ms) | ≤ 5,72 ms | 4,2832, ja | 4,7697, ja |

- **Urteil E10: gehalten.** 98d endete mit 0, alle Kennzahlen liegen vor, die Treffermengen sind in allen 55 Nicht-Rückfall-Anfragen gleich (nachgezählt).
- **Entscheid: Summe. Folge: verworfen.**
- Bedingung 2: Die Kennungen stammen aus `2026-09-v12-messung/rohdaten/05-sprachfaelle.txt`, der Snapshot trägt dieselben 39 Dateien (03-aufbau.txt). Alle acht Nicht-Rückfall-Fälle sind zugeordnet, also kein "nicht entschieden".
- Vermerkt: Die Schwelle 1,0031 lag über dem Höchstwert 1 eines RBO. Die Regel war auf diesen Daten nicht erreichbar. Am Urteil ändert das nichts, eine neue Regel wäre ein neuer Owner-Entscheid.

## Kaltstart: Ursache geklärt (README 6.11)

- m01-Kaltstartzeilen beider 95c-Läufe: `/search innerMs 1505` bis `1596` gegen `ceilingMs 1500.0`, je einer pro Kaltzyklus.
- Der Begriff hat zwei Wörter, also läuft die Suche hybrid. Bei `FINDLING_EMBED_IDLE_RELEASE_SECONDS=0` lädt die erste Suche das Modell selbst (`query_may_load`). Der PHP-Deckel reißt, und die Antwort ist HTTP 200 mit leerer Gruppe. Es ist derselbe Vorfall wie am 10.09.2026, der allgemeine Fall steht im Backlog.
- Folge: Eine unveränderte Nachmessung liefert deterministisch wieder 0 Treffer. Der Owner wählt vorher: (a) Schalter an, (b) einwortiger Begriff, (c) erst Produktfix.
- Einordnung: Das ist ein bekanntes Produktverhalten und keine neue Fehlerklasse. In 22-10 ist nichts gefixt, weil das eine Änderung am ausgelieferten Verhalten bei jedem Start wäre.

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 | f0eec86 | README 6.10 (Kennzahlen, Regel, Urteil), language-analyzers.md Messtabelle |
| 2 | 6d9952a | Verwerfungsabsatz in language-analyzers.md, Kopf von test_field_plan_ranking.py |
| Zusatz | 1ef5977 | README 6.11 Kaltstart-Ursache, deferred-items 22-10 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Abgleich] Zuordnung Urteil zu Zweig**
- **Found during:** Task 1
- **Issue:** Laut Plan führen nur "verfehlt" oder "nicht entschieden" zur Verwerfung. E10 selbst nimmt aber keinen Ausgang vorweg ("Die Erwartung selbst nimmt keinen der beiden Ausgänge vorweg").
- **Fix:** Urteil E10 lautet wörtlich "gehalten" (die Probe hat regelgerecht geliefert), der Entscheid lautet Summe. Gefahren wurde der Zweig Verwerfung, weil der Regelausgang Summe eindeutig ist. Eine Owner-Entscheidung war dafür nicht nötig.

**2. [Rule 2 - Zusatz] Kaltstart-Ursache dokumentiert**
- **Found during:** Analyse auf Auftrag des Orchestrators
- **Fix:** README 6.11 und deferred-items ergänzt, eigener Commit 1ef5977. Am Code ist nichts geändert.

## Verification

- Gezielte Tests (query_rewrite, field_plan_ranking, search_endpoint, measurement_scripts, dismax_probe, public_artifacts): 614 passed.
- ruff check, ruff format --check, pyright latest (0 errors), vulture: grün.
- Volle Suite: 3272 passed, 15 skipped.
- `git diff f0eec86 -- backend/src/findling/query/rewrite.py` ist leer, und `that decision belongs to phase 22` kommt nicht mehr vor (0 Treffer).

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: docs/measurements/2026-09-v13-messung/README.md (6.10, 6.11)
- FOUND: docs/language-analyzers.md ("disjunction_max was measured and rejected on 2026-09-26")
- FOUND: f0eec86, 6d9952a, 1ef5977
