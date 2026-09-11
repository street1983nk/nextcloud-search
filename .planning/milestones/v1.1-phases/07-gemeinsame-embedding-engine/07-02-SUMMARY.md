---
phase: 07-gemeinsame-embedding-engine
plan: 02
subsystem: measurement
tags: [embeddings, latency, ci, amd64, requirements]

# Dependency graph
requires:
  - phase: 07-gemeinsame-embedding-engine
    provides: "Plan 07-01: der Beleg-Abschnitt in docs/performance.md, die arm64-Kaltstartzahl 1.332,1 ms, die beiden Decken mit Datei und Zeile"
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: "findling.tools.one_load, der Job index-search-e2e mit den beiden Paraphrasenschritten, der Nachtrag 06.1-20 (rewritten.one_term)"
provides:
  - "one_load meldet die Kaltstartdauer als siebte Zahl (cold-search-ms), berichtet und nie beurteilt"
  - "integration.yml misst die kalte semantische Suche ueber den echten PHP-Weg auf amd64 und druckt sie mit beiden Decken daneben"
  - "Ein Strukturtor gegen den Rueckschritt, der die Messung still entwerten wuerde: PARAPHRASE_TERM muss mehrwortig bleiben"
  - "docs/performance.md: der Abschnitt zur amd64-Zahl mit Weg, Grenzen des Vergleichs und der Aussage aus Erfolgskriterium 4"
  - "deferred-items.md der Phase mit DI-07-01 bis DI-07-03"
  - "EFF-02 in REQUIREMENTS.md abgehakt, mit der offenen amd64-Zahl in derselben Zeile benannt"
affects: [07-03, 07-04, phase-10-messung, phase-11-audit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zeit berichten, Zaehler und Struktur torieren: keine Millisekundenschranke auf einem geteilten Runner"
    - "Die Wanduhr gehoert in den Aufrufer, nicht in den gemessenen Treiber"
    - "Zwei Zahlen ueber zwei Wege, und keine gibt vor, die andere zu sein: one_load im Prozess, integration.yml ueber den PHP-Weg"
    - "Eine fehlende Zahl bleibt als 'steht aus' stehen und wird nicht hochgerechnet"

key-files:
  created:
    - .planning/phases/07-gemeinsame-embedding-engine/deferred-items.md
    - .planning/phases/07-gemeinsame-embedding-engine/07-02-SUMMARY.md
  modified:
    - backend/src/findling/tools/one_load.py
    - backend/tests/test_one_load.py
    - .github/workflows/integration.yml
    - docs/performance.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Die amd64-Zahl steht im Bericht als 'steht aus' statt als geschaetzte Zahl: ein Lauf von integration.yml ist erst nach dem Zusammenfuehren moeglich, und der Abschnitt haelt nur, weil jede Zahl darin ihren Lauf nennt (DI-07-01)"
  - "EFF-02 ist abgehakt, weil die Zusage auf der schwaecheren Zielhardware belegt ist (arm64, 1.332,1 ms gegen 2.500 ms); die offene amd64-Zahl steht in derselben Zeile und als DI-07-01 in der Ablage"
  - "Beide Befunde der Zeitkette sind abgelegt und nicht behoben: keiner ist klein im Sinne des Plans, beide brauchen eine Messung oder ein Audit"
  - "Der Wortzaehler prueft nur die Wortzahl und nicht Anfuehrungszeichen, Minus, Feld, Dateityp oder titleOnly: nur die Wortzahl kann eine spaetere Bearbeitung dieser env-Zeile versehentlich herbeifuehren"

# Metrics
metrics:
  duration: "rund 70 Minuten"
  tasks: 3
  files-changed: 6
  completed: 2026-09-08
---

# Phase 7 Plan 02: Die amd64-Zahl und das Rückschritt-Tor, Summary

Der Weg zur amd64-Kaltstartzahl ist gebaut und läuft ab dem nächsten
Integrationslauf bei jedem Push mit, ohne dass eine Box angefahren wurde und
ohne dass ein Millisekundendeckel entstanden ist; die Zahl selbst steht als
offen markiert im Bericht, weil sie erst auf dem Runner entsteht.

## Was gebaut wurde

**Weg A, die billige Reihe.** `findling.tools.one_load` hat ein siebtes Feld:
`cold_search_ms`, gemessen mit `time.perf_counter` um den Aufruf von
`drive_the_search_side()` in `measure()`. Die Uhr sitzt im Aufrufer und nicht im
Treiber, weil der Treiber das Gemessene ist. `lines()` druckt
`cold-search-ms=`, `findings()` liest die Zahl nicht. Modulkopf und
Report-Docstring tragen den Grund: ein Millisekundendeckel auf einem geteilten
Runner wird für Runnerlast rot, und `resilience.yml` hat dieselbe Falle für den
Speicher schon einmal ausgeschlagen. Der Modulkopf nennt außerdem, warum es
diese Reihe neben dem Integrationslauf gibt: zwei Zahlen über zwei Wege.

**Weg B, die belastbare Zahl.** Der Schritt "The paraphrase finds the document
with the second track" in `index-search-e2e` war bereits eine kalte semantische
Suche über den echten PHP-Weg. Er hat jetzt drei Dinge mehr:

| Zusatz | Was er tut |
|---|---|
| Wanduhr | `date +%s%N` vor dem `curl`, `elapsed_ms` danach, eine benannte Zeile mit Runner, Architektur, Matrixzeile, Bestandsgröße und beiden Decken als Text |
| Strukturtor | zählt die Wörter von `PARAPHRASE_TERM` und bricht unter zwei mit einer benannten Meldung ab, die den Nachtrag 06.1-20 und `rewritten.one_term` nennt |
| Kommentar | benennt den Schritt "Wait until the second track has written its vectors" als Vorbedingung, damit die beiden nicht auseinandergezogen oder umgedreht werden |

Die vier vorhandenen Zusicherungen des Schritts sind unverändert: Ergebnis nicht
leer, `PARAPHRASE_FILE` enthalten, Rangfolge im Protokoll, `resourceUrl` im
Protokoll. Gegen die gemessene Dauer wird nichts geprüft.

**Der Bericht.** `docs/performance.md` hat drei neue Abschnitte vor "Der Stand
der Zahlen": den Messweg zur amd64-Zahl mit den drei Gründen, warum arm64 und
amd64 hier nicht vergleichbar sind, die Aussage aus Erfolgskriterium 4
(Suchphase minus 712,6 MB, Grundlast unverändert, Gesamtspitze minus 25,1 MB)
und die zwei Befunde über die Zeitkette mit Datei und Zeile.

## Aufgabenstand

| Task | Name | Stand | Commit |
|---|---|---|---|
| 1 | one_load meldet die Kaltstartdauer als siebte Zahl | fertig | `7b9a359` |
| 2 | Die kalte Suche über den echten PHP-Weg, mit Uhr und Struktur-Tor | fertig | `038065b` |
| 3 | Die Zahl in den Bericht, die zwei Befunde in die Ablage, der Haken an EFF-02 | fertig mit Einschränkung | `bed27cf` |

## Deviations from Plan

### 1. [nur in CI prüfbar] Die amd64-Zahl selbst fehlt noch

- **Gefunden bei:** Task 3, unmittelbar nachdem Task 2 den Messweg gebaut hatte.
- **Befund:** Der Plan verlangt die Zahl "mit Laufnummer, Datum, Runner und
  Matrixzeile" im Bericht. Ein Lauf von `integration.yml` braucht einen
  GitHub-Runner und ist erst nach dem Zusammenführen möglich; der Executor
  arbeitet in einem Worktree und pusht nicht.
- **Entscheidung:** Die Tabellenzeile trägt "steht aus" mit dem genauen Weg zur
  Zahl (Workflow, Job, Schritt, Protokollzeile, je Matrixzeile eine). Nicht
  geschätzt und nicht aus der arm64-Zahl hochgerechnet, weil der ganze Abschnitt
  davon lebt, dass jede Zahl ihre Rohdatei oder ihren Lauf nennt.
- **Nachverfolgung:** `DI-07-01` in
  `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`, mit der
  Ansage, dass Erfolgskriterium 4 der Phase offen bleibt, solange die Zeile
  "steht aus" trägt.
- **Dateien:** docs/performance.md, deferred-items.md
- **Commit:** `bed27cf`

### 2. [Rule 4 - Entscheidung, hiermit dem Owner vorgelegt] EFF-02 ist abgehakt, obwohl die amd64-Zahl aussteht

- **Gefunden bei:** Task 3.
- **Befund:** Plan 07-01 hat EFF-02 ausdrücklich offen gelassen mit der
  Begründung, die Zahl sei auf arm64 gemessen und Erfolgskriterium 4 verlange
  eine amd64-Zahl. Diese Zahl liegt nach Abweichung 1 noch nicht vor. Der Plan
  07-02 verlangt trotzdem den Haken.
- **Entscheidung:** Haken gesetzt, mit der Einschränkung in derselben Zeile. Die
  Begründung: der Wortlaut von EFF-02 nennt keine Architektur, und die Zusage
  ist auf arm64 belegt, also auf der schwächeren Zielhardware dieses Produkts
  (1.332,1 ms p95 gegen 2.500 ms, über den OCS-Weg). Ein amd64-Runner ist
  schneller, die arm64-Zahl ist damit die konservative Schranke. Die
  amd64-Entsprechung ist eine Bestätigung und Erfolgskriterium der Phase, nicht
  der Inhalt der Zusage.
- **Wenn der Owner das anders sieht:** Zeile 11 und Zeile 53 von
  `.planning/REQUIREMENTS.md` auf Pending zurücksetzen, bis `DI-07-01` erledigt
  ist. Der Rest dieses Plans hängt nicht daran.
- **Dateien:** .planning/REQUIREMENTS.md
- **Commit:** `bed27cf`

### 3. [Rule 3 - Vorgehen] TDD-Zyklus ohne roten Commit

- **Gefunden bei:** Task 1.
- **Befund:** Task 1 ist `tdd="true"`, die Executor-Regeln dieses Plans
  verlangen aber "vor jedem Commit lokal grün", einschließlich `pytest -q`. Ein
  Commit der RED-Phase wäre ein Commit mit roter Suite.
- **Vorgehen:** Der Zyklus ist vollständig gefahren, nur nicht in zwei Commits.
  RED: die fünf neuen Zusicherungen wurden zuerst geschrieben und liefen rot
  (5 failed, 4 passed, `TypeError` an der `Report`-Konstruktion). GREEN: das
  siebte Feld, die Uhr und die Zeile, danach 9 passed. Die Rotfähigkeit der
  Nicht-Beurteilung ist zusätzlich per Mutation belegt, siehe Torergebnisse.
- **Dateien:** backend/tests/test_one_load.py, backend/src/findling/tools/one_load.py
- **Commit:** `7b9a359`

### 4. [Rule 1 - Präzisierung] "Keine Schranke auf einer gemessenen Dauer in diesem Job" gilt für die Kaltstartdauer, nicht für den Job

- **Gefunden bei:** Task 2, beim Gegenlesen des Akzeptanzkriteriums.
- **Befund:** Der Job `index-search-e2e` enthält einen zweiten Schritt, der eine
  eigene Wanduhr misst und sie sehr wohl gegen eine Schranke prüft: "A slow
  backend costs the excerpt, not the hit and not the budget", das
  Verzögerungsbudget aus dem `FINDLING_ARTIFICIAL_DELAY_MS`-Aufbau. Er hat mit
  der Kaltstartmessung nichts zu tun und misst eine künstlich verzögerte,
  warme Suche.
- **Entscheidung:** Nicht angefasst. Das Akzeptanzkriterium ist als "keine
  Schranke auf der gemessenen Kaltstartdauer" gelesen, und das hält: `elapsed_ms`
  des neuen Blocks wird ausschließlich gedruckt.
- **Dateien:** keine
- **Commit:** keiner

## Gate-Ergebnisse

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 116 files already formatted |
| `uv run pytest -q` | 1673 passed, 15 skipped |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | ohne Befund |
| `pytest tests/test_workflow_pins.py -q` | 14 passed |
| `yaml.safe_load(integration.yml)` | geladen, `cold semantic search` und `REQUEST_TIMEOUT_SECONDS` im Job vorhanden |
| Em-Dash und En-Dash in allen geänderten Dateien | keiner |

Die Gates sind vor jedem der drei Commits vollständig gelaufen.

### Zwei Probeläufe, die den Toren beim Rotwerden zusehen

**Das Wort-Tor.** Der Block des Schritts wurde mit drei Belegungen von
`PARAPHRASE_TERM` gegen `sh` gefahren:

| Belegung | Ausgabe | Exit |
|---|---|---|
| `Kuendigung` | `::error::PARAPHRASE_TERM holds 1 word, and this step needs at least two.` | 1 |
| `Wann darf ich meinen Job aufgeben und wie lange muss ich vorher warten` | `gate passed with 13 words` | 0 |
| leer | `::error::PARAPHRASE_TERM holds 0 word, ...` | 1 |

**Die Nicht-Beurteilung der Dauer.** In `findings()` wurde versuchsweise eine
Schranke von 5.000 ms eingezogen und die Suite gefahren:
`test_the_duration_is_reported_and_never_judged` wurde rot, 8 andere blieben
grün. Die Mutation wurde danach zurückgenommen; sie steht in keinem Commit.

## Was nur in CI prüfbar ist

| Kriterium | Warum hier nicht prüfbar |
|---|---|
| Ein Lauf von `integration.yml` ist grün und trägt die Kaltstartzeile | braucht einen GitHub-Runner mit Nextcloud, AppAPI und dem gebauten Modell; lokal gegengelesen ist nur die YAML-Struktur und die Shell-Logik des neuen Blocks |
| Die amd64-Kaltstartdauer selbst | dieselbe Ursache, siehe `DI-07-01` |
| `resilience.yml` bleibt grün und druckt die siebte Zahl mit | der Schritt druckt den Report vollständig (`sed "s/^/${MEASURE_PREFIX} one-load /" one-load.txt`), die neue Zeile erscheint also von selbst; der Workflow wurde in diesem Plan nicht angefasst |

## Was dieser Plan nicht getan hat

- Kein Millisekundendeckel, in keiner Form, an keiner Stelle.
- `resilience.yml` nicht angefasst.
- `.planning/STATE.md` und `.planning/ROADMAP.md` nicht angefasst.
- Kein `git push`, kein Zusammenführen.
- Die AWS-Box nicht angefahren.

## Self-Check

Dateien:

- `backend/src/findling/tools/one_load.py` vorhanden, `cold_search` fünfmal enthalten
- `backend/tests/test_one_load.py` vorhanden, zwei neue Fälle
- `.github/workflows/integration.yml` vorhanden, lädt als YAML
- `docs/performance.md` vorhanden, alle sieben Suchmuster der Planverifikation treffen
- `.planning/REQUIREMENTS.md` vorhanden, EFF-02 abgehakt und in der Tabelle auf Done
- `.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md` vorhanden, DI-07-01 bis DI-07-03

Commits: `7b9a359`, `038065b`, `bed27cf` auf `exec/07-02`, alle als
street1983nk, kein Werkzeughinweis in irgendeinem Artefakt.

## Self-Check: PASSED
