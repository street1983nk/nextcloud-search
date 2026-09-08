---
phase: 07-gemeinsame-embedding-engine
plan: 01
subsystem: docs
tags: [embeddings, memory, latency, requirements, beleg]

# Dependency graph
requires:
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: "shared_model(), load_count(), das CI-Tor findling.tools.one_load, die Nachmessung vom 07.09.2026"
provides:
  - "docs/performance.md, Abschnitt 'Die eine Engine: der Beleg zu EFF-01 und EFF-02': fuenf Aufrufstellen mit Datei und Zeile, der Zaehlerbeweis, das CI-Tor und die Praezisierung zum Tokenizer"
  - "Die Kaltstartzahl 1.332,1 ms neben der Aufrufdecke von 1,5 s aus ExAppService.php:89, getrennt vom Gruppenbudget aus Provider.php:57"
  - "Die Ablehnung der Modell-Entladung nach Leerlauf mit drei Zahlen, gegen ihre Wiederkehr in einer spaeteren Phase"
  - "EFF-01 in REQUIREMENTS.md abgehakt, mit Verweis auf den Beleg"
affects: [07-02, 07-03, 07-04, phase-10-messung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Beleg mit Datei und Zeile statt Verweis auf den Quellcode: jede Zusage nennt den Ort, an dem sie haelt"
    - "Gerechnete Zahlen werden im Bericht als Rechnung markiert und tragen die Rechnung daneben"
    - "Jede Zusage nennt ausdruecklich, was sie NICHT umfasst (Tokenizer-Objekte, amd64, voller Bestand)"

key-files:
  created:
    - .planning/phases/07-gemeinsame-embedding-engine/07-01-SUMMARY.md
  modified:
    - docs/performance.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Die beiden Teile des Plans wurden in EINEN Berichtsabschnitt geschrieben statt in zwei, weil EFF-01 und EFF-02 dieselbe Engine belegen; die Ueberschrift traegt deshalb beide Kennungen"
  - "Der Schlussteil 'Was hier nicht steht' steht einmal am Ende des Abschnitts und nicht zweimal, und deckt Speicher- wie Latenzzahlen ab"
  - "EFF-02 bleibt Pending: die Zahl ist auf arm64 gemessen, Erfolgskriterium 4 der Phase verlangt eine amd64-Zahl, und die liefert Plan 07-02"

# Metrics
metrics:
  duration: "rund 45 Minuten"
  tasks: 3
  files-changed: 2
  completed: 2026-09-08
---

# Phase 7 Plan 01: Der Beleg für die gemeinsame Embedding-Engine, Summary

Erfolgskriterium 1 der Phase ist von "gebaut" auf "belegt" gehoben: ein Leser
kann die eine Engine jetzt ohne Quellcode prüfen, und die Kaltstartzahl steht
neben der Aufrufdecke von 1,5 s, an der sie wirklich hängt, statt nur neben dem
2,5-s-Gruppenbudget.

## Was gebaut wurde

Ein neuer Abschnitt in `docs/performance.md`, zwischen der Nachmessung vom
07.09.2026 und "Was der Test gekostet hat", mit neun Teilen:

| Teil | Inhalt |
|---|---|
| Aufrufstellen | Tabelle der fünf Pfade des ausgelieferten Containers, jeder mit Datei und Zeile, alle über `shared_model()` |
| Gegenbeweis | keine zweite Konstruktion von `EmbeddingModel` in `backend/src/findling/`; `backend/tests/` und `scripts/` erreichen das Laufzeit-Abbild nicht; der Extraktions-Kindprozess trägt keine Gewichte |
| Beweisweg | `load_count()`, warum ein Zähler und keine Speichermessung, mit der 241.172/503.316-Byte-Beobachtung als Begründung |
| Tests und Tor | vier Unit-Fälle mit Zeile, drei Rotbeweise mit Zeile, das CI-Tor mit Workflow, Job, Schritt und Architektur, und der Grund für die Reihenfolge im Tor |
| Präzisierung | "eine Engine" ist eine onnxruntime-Sitzung und ein Satz Gewichte, KEIN Tokenizer-Objekt; Grund und gesperrte Entscheidung |
| EFF-02 | Kaltstarttabelle mit Rohdatei je Zeile, Aufschlag als Rechnung ausgewiesen, Speicherbeobachtung derselben Sekunde |
| Lesart | "nach Leerlauf" hat heute genau eine nichttriviale Lesart; die zweite (Seitencache) ist benannt und nicht gemessen |
| Grenze | Gruppenbudget gegen Aufrufdecke, `secondsLeft`, zwei Aufrufe je Suche, Nebenläufigkeitstabelle als Rechnung markiert |
| Entladung | Ablehnung mit drei Gründen und drei Zahlen, plus der Hinweis auf Bauform B aus 06.1-02 |

Dazu der Haken an EFF-01 in `.planning/REQUIREMENTS.md`, in der Zeile selbst und
in der Traceability-Tabelle.

## Aufgabenstand

| Task | Name | Stand | Commit |
|---|---|---|---|
| 1 | Der Beleg für EFF-01, mit Datei und Zeile | fertig | `b24f9e7` |
| 2 | Der Beleg für EFF-02 und die Ablehnung der Modell-Entladung | fertig | `48d50c6` |
| 3 | Der Haken an EFF-01 | fertig | `e1819ad` |

## Deviations from Plan

### Korrigierte Datei-und-Zeile-Angaben

**1. [Rule 1 - Bug] STATE.md:159 zeigt auf die falsche Zeile**

- **Gefunden bei:** Task 1
- **Befund:** Der Interfaces-Block des Plans und `07-RESEARCH.md` nennen
  `.planning/STATE.md:159` für die gesperrte Zwei-Tokenizer-Entscheidung. Dort
  steht die Entscheidung zu `embedding_unavailable`; die Tokenizer-Entscheidung
  steht in Zeile 160.
- **Fix:** Der Bericht zitiert `.planning/STATE.md:160`.
- **Dateien:** docs/performance.md
- **Commit:** `b24f9e7`

**2. [Rule 1 - Bug] one_load.py: die vier Zähler stehen in 286-326, nicht in 265-330**

- **Gefunden bei:** Task 1
- **Befund:** Plan und Recherche nennen `one_load.py:265-330` für die vier
  Zähler. In diesem Bereich liegen `measure()` (Zeile 249 bis 284), `findings()`
  (286 bis 326) und der Kopf von `main()` (ab 328). Die vier benannten Befunde
  mit Exit 1 stehen ausschließlich in `findings()`.
- **Fix:** Der Bericht zitiert `backend/src/findling/tools/one_load.py:286-326`.
- **Dateien:** docs/performance.md
- **Commit:** `b24f9e7`

**3. [Rule 1 - Bug] Der CI-Schritt steht bei Zeile 1420, nicht bei 1417**

- **Gefunden bei:** Task 1
- **Befund:** Plan und Recherche nennen `.github/workflows/resilience.yml`
  Zeile 1417 bis 1431 für den Schritt "One engine and one constituent list per
  process". Die `- name:`-Zeile steht bei 1420; 1417 bis 1419 gehören noch dem
  Kommentarblock darüber.
- **Fix:** Der Bericht zitiert Zeile 1420 und nennt Job (`measurements`) und
  Laufumgebung (`ubuntu-24.04`, also amd64) dazu.
- **Dateien:** docs/performance.md
- **Commit:** `b24f9e7`

**4. [Rule 1 - Bug] Die Aussage über den Extraktions-Kindprozess war zu weit gefasst**

- **Gefunden bei:** Task 1
- **Befund:** Die Recherche sagt, in `backend/src/findling/extract/` komme
  "weder `embed` noch `EmbeddingModel`" vor. Die Zeichenfolge `embed` kommt dort
  sehr wohl vor, in einem Kommentar in `extract/ocr_quality.py:102`, der auf
  `test_embed_bench.py` verweist. Die gemeinte Aussage hält trotzdem.
- **Fix:** Der Bericht sagt präzise, was geprüft ist: kein Import aus
  `findling.embed` und keine Konstruktion von `EmbeddingModel` in
  `backend/src/findling/extract/`.
- **Dateien:** docs/performance.md
- **Commit:** `b24f9e7`

### Aufbau des Abschnitts

**5. [Rule 3 - Blocker] Ein Abschnitt statt zwei, ein Schlussteil statt zwei**

- **Gefunden bei:** Task 2
- **Befund:** Task 1 verlangt als vierten Teil "den Stand der Zahlen, damit der
  Abschnitt nicht als Ersatz für Phase 10 gelesen wird", Task 2 verlangt einen
  Schlusssatz mit demselben Inhalt (arm64, Plan 07-02, Phase 10). Wortgleich
  zweimal im selben Abschnitt wäre ein Textfehler.
- **Fix:** Die Teile fünf bis acht wurden VOR den Schlussteil aus Task 1
  eingefügt, und dieser Schlussteil wurde um die Latenzzahlen erweitert. Der
  Abschnitt endet damit genau einmal mit "was hier nicht steht", und beide
  Anforderungen sind erfüllt.
- **Dateien:** docs/performance.md
- **Commit:** `48d50c6`

**6. [Rule 2 - Konvention] Überschrift und Schreibweise angepasst**

- **Gefunden bei:** Task 2
- **Befund:** Die Überschrift aus Task 1 nannte nur EFF-01, der Abschnitt trägt
  nach Task 2 beide Belege. Außerdem schreibt `docs/performance.md` deutsche
  Prosa durchgehend mit Eszett (125 Vorkommen), der neue Text hatte an einigen
  Stellen die ASCII-Ersatzform.
- **Fix:** Überschrift auf "Die eine Engine: der Beleg zu EFF-01 und EFF-02"
  erweitert, Einleitung um einen Satz zu EFF-02 ergänzt, und im neuen Abschnitt
  die betroffenen Wörter auf die Schreibweise des Berichts gebracht.
- **Dateien:** docs/performance.md
- **Commit:** `48d50c6`

Kein Scope wurde erweitert: es wurde kein Produktionscode, keine Testdatei und
kein Workflow angefasst.

## Gate-Ergebnisse

Vor jedem der drei Commits gefahren, alle drei Male identisch grün:

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 116 files already formatted |
| `uv run pytest -q` | 1671 passed, 15 skipped |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | leer |

Dazu die Verifikationen der drei Tasks:

| Prüfung | Ergebnis |
|---|---|
| Gegenbeweis-Grep `EmbeddingModel(` außerhalb von `embed/` | leer |
| Kein Em-Dash (U+2014), kein En-Dash (U+2013) in `docs/performance.md` | 0 und 0 |
| Zielgerichtete Tests `test_embed_engine.py` und `test_one_load.py` | 19 passed |
| Beide zitierten PHP-Konstanten stehen unverändert so im Baum | bestätigt |
| `.planning/STATE.md` und `.planning/ROADMAP.md` unangetastet | bestätigt |

## Was offen bleibt

- **EFF-02 bleibt Pending.** Die Zahl 1.332,1 ms ist auf arm64 gemessen;
  Erfolgskriterium 4 der Phase verlangt eine amd64-Entsprechung. Der Haken fällt
  in Plan 07-02.
- **Die zweite Lesart von "nach Leerlauf"** (Index und `vectors.db` aus dem
  Seitencache gefallen) ist im Bericht benannt und nicht gemessen. Das Werkzeug
  dafür liegt vor (`measure.yml`, Schritt "C, scan latency").
- **Die 543,7-MB-Frage** aus Teil 3 der Recherche (Tokenizer und Splitter) ist
  nicht Gegenstand dieses Plans und wandert in die folgenden Pläne der Phase.

## Self-Check: PASSED

Alle drei genannten Dateien liegen im Baum, alle drei Commits sind in der
Historie, und keine der drei Dateien enthält einen Em-Dash oder einen En-Dash.
