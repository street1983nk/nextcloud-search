---
phase: 31-neue-formate-und-nachholweg
plan: 11
subsystem: Worker (catchup.py, reconcile.py, poller.py), Lifespan (main.py), Store (repo.py)
tags: [fmt-06, d-31-01, d-31-02, pol-02, nachholweg, reconcile, einmal-modus]
requires:
  - phase: 31-02
    provides: "VERDICTS_GENERATION 3, KNOWN_VERDICTS_GENERATIONS, öffentliche SKIPPED_FALLBACK_WITHOUT_SIGNAL"
  - phase: 31-03
    provides: "POL-02-Fix, ohne den die zweite Chance für repeatedly_stuck nichts brächte"
  - phase: 31-10
    provides: "die sechs neuen Typen in beiden Allowlists"
provides:
  - "worker/catchup.py: Teil A (select_catchup_candidates, catchup_step) unter CATCHUP_MARK recheck_1_5_0"
  - "Reconcile: Marke reconcile macht einen Zyklus sofort fällig, erster Durchgang spult zurück, Nachhol-Ausnahme im give_up-Zweig, gezieltes Neu-Urteil bei 1.3-Ersatzcode, done nach vollständigem Zyklus"
  - "Reconcile.run(stop_event, once=True) und default_catchup_reconcile"
  - "main.py: _CATCHUP_RECONCILE, _armable_tasks, Einmal-Modus bei FINDLING_RECONCILE_ENABLED=false"
  - "repo.py: CATCHUP_MARK/CATCHUP_RECONCILE/CATCHUP_DONE, catchup_scan, known_skip_reasons, rewind_reconcile_walk"
affects: [31-12 Saat, 31-13 Store upgrade 5 und recheck_1_5_0, 31-15 Audit und Kostenmessung]
tech-stack:
  added: []
  patterns:
    - "Marke mit vier Werten (fehlt, Ziffern, reconcile, done) als Zustand eines einmaligen Laufs"
    - "Ausnahmen im Abgleich nur unter einer Marke, einmal je Seite gelesen"
    - "Gemeinsame Arm-Liste _armable_tasks statt verstreuter Tupel"
key-files:
  created:
    - backend/src/findling/worker/catchup.py
    - backend/tests/test_catchup.py
  modified:
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/main.py
    - backend/src/findling/store/repo.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_poller.py
    - backend/tests/test_main_lifespan.py
    - backend/tests/test_measurement_scripts.py
    - docs/reconcile.md
    - .planning/REQUIREMENTS.md
decisions:
  - "Der erste Abgleich-Durchgang unter der Marke reconcile spult alle Cursor auf den Anfang zurück (Merker im Speicher); erst ein Zyklus, der unter der Marke begann und alle Mounts beendet, schreibt done"
  - "catchup_step(store, queue) ohne Reconcile-Parameter: Teil B hängt nur an der Marke"
  - "Teil A wählt über den gespeicherten Mimetyp (neue Abfrage catchup_scan), die Endung nur bei leerem Mimetyp; give_up-Zeilen haben keinen Pfad"
  - "Der Einmal-Abgleich hat eine eigene Fabrik default_catchup_reconcile, damit Tests und main.py ihn vom regulären trennen"
  - "docs/reconcile.md ist deutsch, der neue Abschnitt deshalb deutsch (Plan nahm englisch an)"
  - "FMT-01 bis FMT-05 zurück auf Pending bis zum E2E-Beweis in 31-13 (Owner-Linie); FMT-06 bleibt Pending bis 31-13"
metrics:
  duration: "ca. 70 min, davon ca. 25 min CI-Wartezeit"
  completed: 2026-10-12
  tasks: 3
  files: 12
---

# Phase 31 Plan 11: Einmaliger Nachholweg recheck_1_5_0 Summary

Nach dem Upgrade holt der Container den Bestand einmal und ohne Vollcrawl nach. Teil A läuft über state.db und reiht in Bändern zu 200 neu ein: legacy_format außer PowerPoint, jede nicht indexierte Zeile der sechs neuen Typen und einmal jede repeatedly_stuck-Zeile. Teil B ist ein sofort fälliger Abgleich-Zyklus nur über Metadaten. Er findet die neuen Typen, die nie eine Zeile hatten, und während er läuft, gelten zwei enge Ausnahmen: eine in Nextcloud abgeschriebene Datei ohne Containerzeile ist Arbeit statt give_up, und eine Datei mit 1.3-Ersatzcode auf der Nextcloud-Seite wird neu beurteilt, wenn der Container den passenden echten Code hält. Bei abgeschaltetem Abgleich läuft genau dieser eine Zyklus in einem eigenen Einmal-Task, `active_reconcile()` bleibt None.

## Umsetzung

- **repo.py:** `CATCHUP_MARK = "recheck_1_5_0"`, `CATCHUP_RECONCILE`, `CATCHUP_DONE` mit Kommentar zu den Markenwerten. `catchup_scan` ist eine Schwesterabfrage zu `recheck_scan` mit Mimetyp; `recheck_scan` bleibt unverändert. `known_skip_reasons(file_ids)` ist gebändert wie `known_etags`. `rewind_reconcile_walk()` setzt nur `after_file_id` auf 0.
- **worker/catchup.py:** Der Docstring nennt FMT-06, D-31-01, D-31-02, das Mischfenster mit Verweis auf 31-02 und docs/formats.md "Upgrade order", die zwei Teile, warum es keinen Vollcrawl gibt, die Markenwerte und die Nachhol-Ausnahme. Dazu kommen `NEW_MIMETYPES`, `select_catchup_candidates` und `catchup_step` nach dem Muster von recheck_step: Cursor in der Marke, `.ok` je Band, Log nur mit Zahlen. Wenn recheck_1_4_0 nicht done ist, liefert die Funktion False, bei reconcile oder done True ohne Arbeit.
- **reconcile.py:**
  - `_is_due`: Als erste Regel ist die Marke reconcile sofort fällig.
  - `run_once`: liest die Marke einmal je Runde. Der erste Durchgang unter der Marke spult zurück. Nach einem vollständigen Zyklus wird done geschrieben, mit der Logzeile "the catch-up cycle after the upgrade is complete".
  - `_compare`: liest die Marke einmal je Seite. Im Zweig `stored is None and written_off` mit Marke wird die Datei zu Arbeit, es wird nichts geschrieben. Im Zweig `stored == row.etag` wird die Datei Arbeit, wenn der Container einen der drei Codes hält und die Seite genau dessen Ersatz aus `SKIPPED_FALLBACK_WITHOUT_SIGNAL` trägt. Die Ersatztabelle ist importiert, nicht abgeschrieben. Der Docstring hat zwei fett gesetzte Absätze. Der Zweig "stranded handover" steht unverändert davor.
  - `run(stop_event, *, once=False)` und `default_catchup_reconcile`.
- **poller.py:** startet `catchup_step` nach recheck_1_4_0, aber nur bei `choice.verdicts == VERDICTS_GENERATION` (3). Ein In-Memory-Kurzschluss `_catchup_done` verhindert Wiederholungen. Bei Fehlern gilt dieselbe Regel wie beim re-check (Warnung mit Klassenname).
- **main.py:** `_CATCHUP_RECONCILE` als eigene Variable. `_armable_tasks(*, after_rebuild=False)` mit einem Protokoll `_Armable` ersetzt alle drei Schleifen; `_arm_the_poller` armiert nur Poller und Runner. Den Einmal-Task startet main.py, wenn der Abgleich abgeschaltet ist und `_the_catch_up_is_open()` zutrifft (state.db read-only, bei fehlender oder unlesbarer Datei offen). Er bekommt ein eigenes Stop-Event und dieselbe Abschaltfolge wie `repairing`. Ins Log kommt die zweite Zeile "one catch-up cycle after the upgrade runs once".
- **docs/reconcile.md:** Neuer Abschnitt "Der einmalige Nachholzyklus nach dem Upgrade auf 1.5": was nachgeholt wird, die zwei Ausnahmen, was nicht passiert, der Einmal-Modus, eine Markentabelle und wo der Admin den Stand sieht. Dazu ein Hinweis in der Tabelle der Einstellungen.
- **Baumhash** im selben Commit: `PACKAGE_TREE_HASH_TODAY` 02e9cddd..., `PACKAGE_FILES_TODAY` 78 auf 79, Journalabsatz "Plan 31-11". Das PHP-Paar bleibt unverändert.

## RED

- Teil A gegen einen Stub (leere Auswahl, `catchup_step` False): **24 failed, 5 passed**.
- Teil B nach dem Anlegen der Tests: **12 failed, 92 passed** (test_catchup + test_reconcile). Der Blocker-1-Fall war vor der Änderung rot, weil give_up gerufen wurde:
  ```
  test_under_the_catch_up_mark_a_written_off_file_without_a_row_is_work
  E       assert ([], 1) == ([10], 0)
  ```
- Poller: **3 failed, 3 passed** (Start bei Generation 3, Reihenfolge 1.4 vor 1.5, Fehlerregel).
- Lifespan gegen einen Stub (`_CATCHUP_RECONCILE = None`, `_armable_tasks` leer): **8 failed, 5 passed**.
- Den Einmal-Modus von `Reconcile.run` habe ich vor seinen Tests geschrieben. Belegt ist er per Gegenprobe (`once` ignoriert): **5 von 5 rot**.

## Gegenproben

Jeder Test, der vor der Umsetzung schon grün war, ist mit genau einem Eingriff rot gesehen. Danach kam die Datei aus der Sicherung zurück und `filecmp` war gleich (Skript im Scratchpad, seriell):

| Probe | Eingriff | Ergebnis |
|---|---|---|
| GA1 | system_file/unsupported_variant in Teil A gewählt | rot |
| GA2 | neue Typen in jedem Zustand gewählt | rot |
| GA3 | Teil A wartet nicht auf recheck_1_4_0 | rot |
| GA4 | Teil A schreibt eine Vektormarke | rot (Store-Digest) |
| GA5 | REQUEUE_BAND als eigene Zuweisung | zuerst NICHT rot (CPython cacht 200, `is` ist wahr); Test um AST-Prüfung ergänzt, dann rot |
| GB1 | jede Marke fordert den Zyklus an | 3 rot |
| GB2 | Ruhe-Tor nur beim Rundenstart übersprungen | zuerst NICHT rot (das Tor vor jeder Scheibe greift); Gegenprobe GB2b mit abgeschaltetem `_quiet`: rot |
| GB3 | Nachhol-Regeln unter jeder Marke | 5 rot |
| GB4 | stranded handover nur außerhalb der Marke | 1 rot (Marke reconcile) |
| GB5 | jede unveränderte Datei ist Arbeit unter der Marke | rot |
| GB6 | jeder gespeicherte skipped-Code wird geheilt | 8 rot |
| GB7 | Ersatzcode bei geändertem ETag verworfen | rot |
| GB9 | jeder vollständige Zyklus schreibt done | rot |
| GB10 | Nachholzyklus vergisst den Bestand | rot (Store-Digest) |
| GC1 | Poller ohne Generationsbedingung | rot (None) |
| GC2 | weder Poller noch Teil A warten auf 1.4 | rot |
| GD1 | Start liest die Marke nicht | rot |
| GD2 | Einmal-Task auch neben regulärem Abgleich | rot |
| GD3 | Neuaufbau armiert alle Tasks | rot |
| GD4 | eine Route nennt active_reconcile | rot |
| GD5 | Disable lässt den Einmal-Task armiert | rot |

## Gates und CI

- Lokal vor 1a18e4b2: ruff check (backend und ../scripts), ruff format --check (234 Dateien), pyright latest 0 Fehler, vulture grün. Volle Suite: **5408 passed, 29 skipped**. Der erste Volllauf stoppte am Grep-Gate `test_the_reconcile_log_carries_no_path_and_no_name` (siehe Abweichung 4).
- Push `a91c6b50..1a18e4b2` (mit a646061d), alle sieben Läufe success:
  - Python gates **38238806249** (5420 passed, 17 skipped)
  - HaRP deploy **38238806189**: Store upgrade 0 bis 7 success im Job stable34/ubuntu-24.04. Die Zähler in Store upgrade 5 bis 7 sind unverändert (docs 288, skipped 8, nextcloud.failed 6, scheduled 0).
  - Resilience **38238806242**, Integration 38238806197, Multi-arch image 38238806256, Security scans 38238806228, OpenSSF Scorecard 38238806286
  - PHP gates liefen nicht, weil php/ unverändert ist (Pfadfilter).

## Commits

| Commit | Inhalt |
|---|---|
| a646061d | docs(31-11): FMT-01 to FMT-05 back to pending until the E2E proof in 31-13 |
| 1a18e4b2 | feat(31-11): one catch-up after the upgrade, without a full crawl |

## Deviations from Plan

**1. [Rule 2] Zurückspulen des Abgleichs beim ersten Durchgang unter der Marke.** Der Plan setzt done "nach einem vollständig beendeten Zyklus". Ein Durchgang, der vor der Marke begann (Cursor mitten im Mount), wäre sonst unter der Marke zu Ende gelaufen. Seine ersten Seiten hätten weder die give_up-Ausnahme noch das Neu-Urteil gesehen, und done wäre nach einem halben Zyklus gekommen. Lösung: `rewind_reconcile_walk` beim ersten Durchgang des Objekts unter der Marke, done nur, wenn die Runde unter der Marke begann. Der Merker liegt im Speicher, ein Neustart mitten im Nachholzyklus wiederholt also nur Metadaten. Test: `test_a_walk_begun_before_the_mark_is_walked_again_from_the_front`.

**2. Signatur `catchup_step(store, queue)` statt `(store, queue, reconcile)`.** Teil B hängt allein an der Marke, das Reconcile-Objekt wird nicht gebraucht. "REQUEUE_BAND aus reconcile" ist importiert, der Test prüft das.

**3. Doku-Sprache.** docs/reconcile.md ist deutsch. Der Abschnitt ist deshalb deutsch ("Der einmalige Nachholzyklus nach dem Upgrade auf 1.5") und nicht englisch, wie der Plan annahm.

**4. [Rule 1] Logzeile gegen das Grep-Gate.** `LOGGER.error(..., type(error).__name__)` in `_catchup_mark` traf die Regex des Gates `test_the_reconcile_log_carries_no_path_and_no_name` (das Wort name). Ich habe das Muster der Datei übernommen (`kind_of_failure`), danach den Baumhash neu gemessen und vor dem Commit nachgezogen.

**5. Einmal-Modus-Tests zusätzlich in test_reconcile.py.** Die Rundenlogik (ein Zyklus, done, Ende, kein gewöhnlicher Zyklus, still ohne Arm) ist auf Ebene von `Reconcile` getestet. Die Verdrahtung (Fabrik, Arm/Silence, Herunterfahren, Status) liegt in test_main_lifespan.py, dort mit einem echten `Reconcile` auf Attrappen für den Ablauf deaktiviert, Enable, ein Zyklus.

**6. INFO 5, Befund des grep.** `active_reconcile` liest keine Route und kein Statusweg; nur main.py und test_lifecycle.py nutzen es. Der Test vergleicht `status.report()` mit und ohne Einmal-Task (ohne `diskFreeBytes`). Außerdem prüft er, dass kein Modul unter api/ `active_reconcile` oder `_CATCHUP_RECONCILE` nennt.

**7. Owner-Auftrag außerhalb des Plans.** FMT-01 bis FMT-05 stehen in REQUIREMENTS.md wieder auf Pending mit dem Vermerk "E2E-Beweis in 31-13" (eigener Docs-Commit a646061d).

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche außerhalb des Plans. Umgesetzt:
- T-31-34: Store-Digest-Tests für Teil A und den Nachholzyklus, GA4, GB10
- T-31-35: REQUEUE_BAND importiert (AST-Prüfung), Bändertest 200/200/50
- T-31-36: handgeschriebener Cursor startet bei 0
- T-31-37: Ausnahme nur unter der Marke reconcile, Tests beider Seiten, GB3
- T-31-37b: Einmal-Task endet nach dem Zyklus, gezählte run_once-Aufrufe bei vorgestellter Uhr
- T-31-37c: Neu-Urteil nur bei exaktem Ersatzcode, Tests in beide Richtungen, GB6; die Kosten misst 31-15
- T-31-37d: eigene Variable, `active_reconcile()` None, Statusvergleich

## Requirements

FMT-06 bleibt **Pending**. Der Containerteil ist umgesetzt und durch Unit- und Lifespan-Tests belegt. Der Upgrade-CI-Beweis mit Saat (Store upgrade 3c ohne Marke, Store upgrade 5 mit done) folgt in 31-12/31-13. Lauf 38238806189 zeigt nur, dass der Nachholweg den Bestand der Strecke nicht bewegt. Dass die Marke dort done erreicht, liest deploy-harp noch nicht. POL-02 war schon Complete (31-03); die einmalige zweite Chance für aufgegebene Dateien reist hier mit. FMT-01 bis FMT-05 stehen auf Pending bis 31-13 (Owner-Linie).

## Offene Punkte

- 31-12/31-13: Saat unter v1.4.2, `recheck_1_5_0` in Store upgrade 3c abwesend und in Store upgrade 5 done, Containerprotokoll mit beiden Nachhol-Logzeilen.
- 31-15: Kosten des Neu-Urteils (`known_skip_reasons` je Seite) mit realistischem Anteil messen. Außerdem bewerten, ob der Neustart mitten im Nachholzyklus (erneutes Zurückspulen) auf großen Instanzen stört.
- `occ findling:diagnose` zeigt die Marke nicht. Ob ein Admin sie sehen soll, ist eine Frage für 31-14 (docs/formats.md) oder für später.

## Self-Check: PASSED

catchup.py, test_catchup.py und die SUMMARY sind vorhanden. a646061d und 1a18e4b2 liegen auf origin/main. Alle sieben CI-Läufe auf 1a18e4b2 sind success.
