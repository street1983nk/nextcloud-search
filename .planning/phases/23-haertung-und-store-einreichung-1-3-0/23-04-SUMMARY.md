---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 04
subsystem: tools, ci, docs
tags: [kaltstart, one_load, resilience, integration, probe, D-01, D-08, REL-03]
requires:
  - "23-01 (query_may_load False, Warmlauf über BackgroundTasks)"
provides:
  - "one_load misst Suche plus Handlerweg, getrennt als search-ms und warm-ms"
  - "Kaltstart-Nachmessung in integration.yml: erste Suche lexikalisch mit Trefferpflicht, Warten auf engineState=loaded, Paraphrase danach"
  - "Offline-Beweis wärmt den geteilten Halter über den Produktweg"
  - "Doku zu Kaltstart und Ladefenster (D-08)"
affects:
  - "CI: Python, Integration, Resilience, Multi-arch (docker.yml) beim nächsten Push"
tech-stack:
  added: []
  patterns:
    - "Werkzeugtreiber geht denselben Weg wie ein echter Aufrufer (one_round + if warm_wanted(): warm())"
key-files:
  created: []
  modified:
    - backend/src/findling/tools/one_load.py
    - backend/tests/test_one_load.py
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/resilience.yml
    - .github/workflows/integration.yml
    - backend/tests/probe_image_search.py
    - docs/admin-page.md
    - docs/embeddings.md
decisions:
  - "Erster Suchbegriff nach dem Neustart in integration.yml: 'Frist Monate' (zweiwortig, also hybrid und mit Warmlauf-Anforderung; beide Wörter stehen in 10-kuendigung.docx und werden von den lexikalischen Schritten desselben Jobs schon gesucht)"
  - "admin-page.md: die Spalte 'Was auf der Seite steht' bleibt das wörtliche UI-Zitat; die Präzisierung zu cold steht in der Spalte 'Was ein Admin tun kann', weil eine geänderte Spalte 2 vom ausgelieferten l10n-Text abweichen würde"
  - "test_one_load-Fixture setzt engine._WARM_WANTED zurück, damit ein stehengebliebener Marker eines Vorfalls den neuen Mutationsfall nicht grün macht"
metrics:
  duration: "ca. 40 min"
  completed: 2026-09-27
  tasks: "2 von 3 lokal abgeschlossen, Task 3 (Push und CI-Auslesen) an den Orchestrator übergeben"
  files: 8
---

# Phase 23 Plan 04: Kaltstart in CI nachgemessen, one_load und Doku nachgezogen Summary

one_load misst jetzt, was ein echter Aufrufer auslöst (Suche plus Handlerweg `if warm_wanted(): warm()`), getrennt als `search-ms` und `warm-ms`. integration.yml misst die Kaltstartroute in drei Stufen nach, der Offline-Beweis wärmt über `request_warm()`/`warm()`, und die Doku beschreibt den Kaltstart samt Ladefenster (D-08). Die 7 roten one_load-Tests aus 23-01 sind grün.

## Umsetzung

**Task 1 (one_load, Tests, resilience.yml, Ledger):**
- `drive_the_search_side()` besteht aus `run_the_search()` (nur `one_round`) und `follow_the_handler_path()` (`if warm_wanted(): return warm()`). `measure()` stoppt beide Hälften einzeln mit `time.monotonic`. `warm_ms` ist 0,0, wenn kein Warmlauf fällig war.
- `Report.cold_search_ms` heißt jetzt `search_ms`, dazu kommt `warm_ms`. Die Ausgabezeilen heißen `search-ms=` und `warm-ms=`. Nach wie vor werden nur Zahlen ausgegeben, und `findings()` bewertet keine Dauer.
- Tests:
  - neuer Fall `test_a_search_alone_never_loads_the_engine`: `one_round` allein hebt `load_count()` nicht, fordert aber an
  - neuer Fall `test_the_driver_goes_the_handler_path_and_loads_exactly_once`: der Treiber hebt `load_count()` um genau 1
  - neuer Mutationsfall `test_it_goes_red_when_the_search_stops_asking_for_the_warm_run`: `request_warm` im Suchpfad ist stumm geschaltet. Im selben Test läuft eine Gegenprobe ohne Mutation, die grün sein muss.
  - Der Fall "search side builds its own engine" erwartet jetzt die Null-Meldung ("green for nothing") statt `loads-after-worker=2`. Grund: Seit 23-01 lädt die Suche ihre Eigenkopie nie, und der Handlerweg wärmt nur den Halter, den diese Suche nicht gefüllt hat.
- Rotfähigkeit von Hand belegt:
  - Handlerweg abgeklemmt: 8 Fälle rot
  - `may_load = True` im Suchpfad: der Fall "search alone" wird rot
- resilience.yml: Kommentar auf "search plus handler path" umgestellt, "six cases", neue Felder genannt. Der Schritt liest keine Felder per Name, deshalb war an der Logik nichts zu ändern.
- Ledger: `PACKAGE_TREE_HASH_TODAY` = `6d2a697c...`, weiter 57 Dateien, datierter Absatz "Moved on 2026-09-27 by plan 23-04".

**Task 2 (integration.yml, Probe, Doku):**
- integration.yml, Schritt "The paraphrase finds the document with the second track". Die Wortzahl- und Operator-Tore und die Backlog-Wartezeit bleiben unverändert. Nach dem Neustart gilt diese Reihenfolge:
  - (a) Erste Suche `Frist Monate`. Pflicht: HTTP 200 per `-w '%{http_code}'` und mindestens ein Treffer per `jq -e`, sonst `::error::the first search after a restart came back empty, the cold start fix does not hold (D-01)`. Die Dauer wird gedruckt, nicht zugesichert.
  - (b) Schleife über `/status` mit Deadline 120 s bis `engineState=loaded`. Gedruckt wird `warm run took N s`, eine Zeitüberschreitung ist ein `::error::`.
  - (c) Die Paraphrase mit den unveränderten `jq -e`-Zusicherungen.
- Der Kommentarblock begründet den Wechsel (V-22-01/02, D-01) und nennt D-08 als nicht gemessen. Das EXAPP_SECRET geht wie bisher nur base64-kodiert in den Header.
- probe_image_search.py: `request_warm(); warm()` vor der Paraphrase, mit Kommentar. Der Docstring nennt jetzt den tatsächlichen Stack (onnxruntime plus tokenizers, ohne fastembed/requests seit HART-04).
- admin-page.md: Die Zeilen cold und unloaded sind präzisiert. Der alte Satz "wer die Nachladekosten nicht will, setzt ... auf 0" ist ersetzt durch die neue Bedeutung von 0.
- embeddings.md, Abschnitt 10:
  - Die Tabelle zeigt die Bedeutung von 0.
  - Neuer Absatz "Der Kaltstart".
  - Neuer Absatz "Das Ladefenster (D-08)" mit GIL, weicher Degradierung von /snippets, möglicher leerer zweiter /search, Owner-Abnahme vom 27.09.2026 und Verweis auf test_embed_model.py.

## Commits

| Task | Commit | Art |
|------|--------|-----|
| 1 RED | a69f523 | test(23-04) |
| 1 GREEN | c94dc1e | feat(23-04) |
| 2 | 7e6ad49 | ci(23-04) |
| 3 | nicht ausgeführt | Push an den Orchestrator übergeben |

Alle drei Commits stammen von street1983nk <k.cherif@outlook.de> und tragen keine Co-Authored-By-Zeile (geprüft über `git log 10dfbbe..HEAD`).

## PUSH AUSSTEHEND (Task 3)

Aus dem Worktree kann nicht gepusht werden (Branch worktree-agent-*). Der Orchestrator pusht nach dem Merge von main aus und liest danach die Läufe aus:
- Vor dem Push `git log --format='%an <%ae>' origin/main..HEAD | sort -u` prüfen: nur street1983nk. `git log origin/main..HEAD | grep -ci co-authored` muss 0 ergeben.
- Läufe: Python, Integration, Resilience, Multi-arch (docker.yml), HaRP deploy. Je Lauf Nummer und Urteil notieren. Bei Rot zuerst `gh run rerun --failed`.
- Integration (Schritt "The paraphrase finds the document with the second track"), wörtlich zu übernehmen:
  - Zeile "first search after a restart, cold engine ... N ms ... HTTP 200, K hits"
  - Zeile "warm run took N s ..."
  - Paraphrase-Zeilen "criterion 1 in the integration run: 10-kuendigung.docx found ..."
- docker.yml: Ergebnis des Schritts "The image carries no fastembed and no requests (HART-04)" (erster CI-Lauf überhaupt) und des Offline-Beweises (Zeile "warm run True", danach "the offline step is green").
- resilience.yml, Schritt "One engine and one constituent list per process": `search-ms`, `warm-ms`, `engine-loads-after-search=1`, `verdict=ok`.

## Deviations from Plan

**1. [Rule 1 - Bug] Test "search side builds its own engine" an das neue Verhalten angepasst**
- Gefunden in: Task 1
- Seit 23-01 lädt eine eigene Engine der Suchseite nie. Die alte Erwartung `engine-loads-after-worker=2` ist deshalb nicht mehr erreichbar.
- Der Fall bleibt rot, meldet jetzt aber `engine-loads-after-search=0` und "green for nothing".
- Commit: a69f523

**2. [Rule 1 - Bug] Test-Isolation des Warm-Markers**
- `engine._WARM_WANTED` ist ein Modulglobal und wird von `engine.reset()` nicht gelöscht. Ein Vorfall könnte den Marker stehen lassen und den neuen Mutationsfall grün machen.
- Die Fixture setzt ihn per `monkeypatch` zurück. Ausgelieferter Code ist nicht betroffen.
- Commit: a69f523

**3. admin-page.md: Präzisierung in Spalte 3 statt Spalte 2**
- Spalte 2 zitiert den ausgelieferten UI-Text (`php/templates/admin.php` plus 7 l10n-Dateien). Eine Änderung nur in der Doku hätte Doku und Seite auseinanderlaufen lassen.
- Die geforderte Formulierung steht wörtlich in Spalte 3. Ob der UI-Text selbst geändert wird, ist eine Owner-Frage für den Store-Text-Plan (23-07).

## Deferred Issues

- `docs/performance.md:3480` nennt historisch `cold-search-ms=` als Reportzeile. Das ist ein datierter Messbericht, kein aktueller Vertrag, und wurde bewusst nicht umgeschrieben. Das Akzeptanzkriterium prüft nur src, tests und workflows, und dort gibt es keinen Treffer mehr.
- Der Offline-Modus von probe_image_search.py braucht das 118-MB-Modell und lief deshalb lokal nicht. Lokal lief nur der Modus model-gone (grün). Der Offline-Lauf kommt mit docker.yml im CI.

## Verifikation (lokal)

- ruff check, ruff format --check, pyright latest (0 errors), vulture 80: grün
- pytest: **3339 passed, 15 skipped, 0 failed**. Die 7 vormals roten one_load-Fälle sind grün, die Skipzahl liegt unverändert bei 15.
- `grep -rn cold_search_ms backend/src backend/tests .github/workflows`: kein Treffer
- resilience.yml enthält "bring the engine loads to one on its own" nicht mehr
- integration.yml: engineState 5, D-01 5; embeddings.md: D-08 2; probe: request_warm 3; der alte admin-page-Satz fehlt
- Syntax des geänderten integration.yml-Schritts mit `bash -n` geprüft, YAML parst
- CI-Läufe: ausstehend (siehe PUSH AUSSTEHEND)

## Self-Check: PASSED

- Commits a69f523, c94dc1e und 7e6ad49 sind vorhanden
- Alle 8 Dateien aus key-files sind vorhanden und geändert
- STATE.md und ROADMAP.md sind unverändert

## CI-Belege nach dem Push (Task 3, nachgetragen vom Orchestrator am 27.09.2026)

Push fd2f93c..a5f6d50 auf main. Autorenprobe vor dem Push: nur street1983nk <k.cherif@outlook.de>, 0 Co-authored-Zeilen.

| Workflow | Lauf | Ergebnis |
|---|---|---|
| Python gates | 36285187639 | success |
| Integration | 36285187617 | success |
| Resilience (Push; measurements skippt bei Push per Design) | 36285187618 | success |
| Resilience (workflow_dispatch fuer den one_load-Beweis) | 36286121016 | success |
| Multi-arch image (docker.yml) | 36285187622 | success |
| HaRP deploy | 36285187628 | success |

Beweiszeilen woertlich aus den Logs:

- Integration, Kaltstart-Nachmessung: `first search after a restart, cold engine, over apache, the ocs route, the php provider and both halves: 973 ms on amd64, runner ubuntu-24.04, database mysql, HTTP 200, 1 hits out of the lexical list.`
- Integration: `warm run took 0 s from the end of the first search to engineState=loaded` (beide Matrixzeilen)
- Integration: `criterion 1 in the integration run: 10-kuendigung.docx found through a paraphrase, resource /index.php/f/31`
- docker.yml, HART-04-Schritt "The image carries no fastembed and no requests (HART-04)": success (beide Plattform-Jobs, erster CI-Lauf des Schritts aus 23-02)
- docker.yml, Offline-Beweis: `warm run                    True` und `the offline step is green` (beide Jobs)
- resilience.yml, Schritt "One engine and one constituent list per process" (Dispatch-Lauf 36286121016, Job measurements): `engine-loads-after-search=1`, `search-ms=10.3`, `warm-ms=669.6`, `verdict=ok`

Anmerkung: Der measurements-Job laeuft per Design nicht bei Push (`if: github.event_name != 'push'`); der Beweis kam aus einem manuellen Dispatch auf demselben Commit a5f6d50.
