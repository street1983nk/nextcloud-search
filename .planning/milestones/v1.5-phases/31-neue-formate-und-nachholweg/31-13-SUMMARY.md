---
phase: 31-neue-formate-und-nachholweg
plan: 13
subsystem: Upgrade-CI (deploy-harp.yml Store upgrade 2b bis 7), Gate test_upgrade_seed_steps.py, 30-AUDIT
tags: [fmt-06, d-31-02, sc2, sc4, pol-02, upgrade-ci, l-30-03, zip-bombe, nachholweg]
requires:
  - phase: 31-11
    provides: "Nachholweg recheck_1_5_0 (Teil A state.db, Teil B Abgleich mit give_up-Ausnahme)"
  - phase: 31-12
    provides: "Saat der neuen Formate unter v1.4.2 (2b), Aufzeichnung recheck_1_5_0 absent, Kandidaten und Altbestands-Digest (3c)"
provides:
  - "Store upgrade 5 mit zehn Zusicherungen: Altbestand (Zusicherung 10) getrennt von der Saat (Zusicherung 9), Zähler unchanged oder exakt hergeleitet"
  - "Store upgrade 4 hält RestartCount und Endzeit fest (UPGRADE_NEW_RESTARTS, UPGRADE_FINISHED_AT), alle Werte musterprüft"
  - "L-30-03 geschlossen: jede GITHUB_ENV-Schreibstelle von 2b bis 7 prüft ihren Wert vorher"
  - "seed-probe.py: Frage stock nimmt eine Liste, reconcile ohne Subjekt; Gate führt die Probe aus"
affects: [31-14 Store-Text, 31-15 Audit (Nachholdauer, Strecke)]
tech-stack:
  added: []
  patterns:
    - "moved(): Zähler nach = vorher + hergeleiteter Schritt, exakt, neben unchanged()"
    - "Gate parst jede GITHUB_ENV-Schreibstelle und verlangt davor eine Musterprüfung der geschriebenen Variable (direkt oder in einer Schleife)"
    - "Gate führt die eingebettete Probe gegen Datenbanken aus store/schema.sql aus, statt nur Text zu suchen"
key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
    - .planning/phases/30-owner-tor-schema-und-tschechisch/30-AUDIT.md
    - .planning/REQUIREMENTS.md
decisions:
  - "Checkpoint aus 31-12 nicht ausgelöst, also volle Saat: sieben Saatwörter, Zip-Bombe, STALE in fester Reihenfolge"
  - "Warten in Store upgrade 5 schließt die Vektoren der sieben Saatdateien ein, weil Store upgrade 6 vectors.db bytegleich vergleicht"
  - "indexed in findling_file_state heißt: keine Zeile (PHP schreibt indexed nie, revokeFailures löscht)"
  - "Vektorbestand ohne Saat = Bestand ohne die acht neuen Saat-IDs, gegen UPGRADE_VECTOR_STOCK aus 3c"
  - "Musterprüfungen neu mit [[ =~ ]] (ganze Zeichenkette, kein Zeilen-Match wie grep)"
metrics:
  duration: "ca. 115 min, davon ca. 50 min CI und ca. 25 min lokale Volltestläufe"
  completed: 2026-10-12
  tasks: 2
  files: 4
---

# Phase 31 Plan 13: Upgrade-Beweis hält den Altbestand und findet die neuen Formate Summary

Store upgrade 5 trennt jetzt "Altbestand unverändert" von "Saat neu indexiert". Nach dem Upgrade von v1.4.2, ohne `findling:index --restart` und ohne Admin-Eingriff, findet jedes der sieben Saatwörter genau seine Datei, der ZIP-Auszug beginnt mit `innen/notiz.txt: `, die von 1.4.2 als repeatedly_stuck aufgegebene .txt ist indexiert, die Zip-Bombe steht als skipped/archive_limit bei laufendem Container, recheck_1_5_0 ist done, und der Digest des Altbestands ist der aus 3c. L-30-03 ist geschlossen. Lauf **38256198997** grün über Store upgrade 0 bis 7.

## Checkpoint-Ergebnis aus 31-12

Nicht ausgelöst (31-12-SUMMARY, Abschnitt "Feste Reihenfolge": "Checkpoint Task 2 nicht ausgelöst, alle fünf Schritte gangbar"). Damit gilt die volle Saat: sieben Saatwörter, Zip-Bombe, STALE-Saat in fester Reihenfolge und STALE-Zusicherung "indexed".

## Herleitung der Zählerschritte (Kommentar über Store upgrade 5)

Unter 1.4.2 (31-12-SUMMARY): sechs neue Typen und Bombe ohne Zeile auf beiden Seiten, Word-OLE unter .docx skipped(legacy_format) auf beiden Seiten, .txt failed(repeatedly_stuck) in findling_file_state und 0 Zeilen in state.db. Nach dem Upgrade (Code dieser Phase): Teil A holt die Word-OLE (legacy_format, kein PowerPoint), Teil B die übrigen sieben (keine Containerzeile, die .txt über die Ausnahme für Abgeschriebene). `docs` zählt tantivy-Dokumente = indexierte Dateien (findling.tools.index_status), eine übersprungene Datei ist nie eines. Ein Erfolgsbericht nimmt skipped- und failed-Urteile in Nextcloud zurück (QueueService::acknowledge, FileStateService::revokeFailures). Vorab lokal geprüft: `extract()` dieses Baums gibt für eml, zip, doc, xls, Word-OLE und txt indexed, für die Bombe skipped/archive_limit; kein Saattext enthält Belehrung, Auszug, Erinnerung, alemanes, smlouv oder proc; jedes Saatwort ist mit der echten Wortliste (276 496 Bestandteile, Image findling_backend:dev) ein einziges Token.

| Zähler | Schritt | Grund |
|---|---|---|
| container.docs | +7 | mail, ZIP, doc, xls, HEIC, .txt, Word-OLE |
| container.indexed | +7 | dieselben sieben |
| container.skipped | 0 | +1 Bombe, -1 Word-OLE verlässt legacy_format |
| container.failed | 0 | die .txt hatte nie eine Containerzeile |
| nextcloud.skipped | 0 | +1 Bombe, -1 legacy_format der Word-OLE zurückgenommen |
| nextcloud.failed | -1 | repeatedly_stuck der .txt zurückgenommen |
| nextcloud.scheduled | 0 | abgewartet |
| nextcloud.running | 0 | abgewartet |
| container.rebuildState | 0 | idle |

Im Lauf bestätigt: docs und indexed 288 auf 295, nextcloud.failed 7 auf 6, der Rest unverändert (Zitate unten).

## Umsetzung (Task 1, cafa34df)

- **Store upgrade 4:** RestartCount und Endzeit festgehalten. Vor dem GITHUB_ENV-Block werden alle vier Werte geprüft: Containername `^[A-Za-z0-9][A-Za-z0-9_.-]*$`, Companion-Version `^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.]+)?$`, RestartCount und Endzeit `^[0-9]+$`.
- **Store upgrade 5**, Name "the ten assurances after the upgrade":
  - Saat-Warteschleife mit gemeinsamer Deadline (UPGRADE_DRAIN_BUDGET_SECONDS), ohne cron.php. Sie wartet auf: recheck_1_5_0 done, Bombe beurteilt, sieben Dateien indexed mit Chunks > 0, jedes Wort findet genau seine Datei.
  - Danach die bestehende Ruhe-Schleife im selben Budget.
  - 3 mit `moved()`, Tabelle oben.
  - 8 vergleicht den Vektorbestand ohne die acht neuen Saat-IDs mit UPGRADE_VECTOR_STOCK.
  - 9: Saat (Marke, Wörter, ZIP-Auszug, indexed ohne Nextcloud-Urteil, STALE einzeln, Bombe beidseitig, `docker inspect` Running und RestartCount, Kanariensuche nach der Bombe).
  - 10: Altbestand (je Kandidat einzeln, leere Listen als eigene Zeile, Digest über dieselbe Ausschlussliste wie 3c).
  - Fehlermeldungen nennen Wort und Datei-IDs, nie Titel oder Auszugstext (beim ZIP-Auszug nur die Länge).
- **L-30-03:** Prüfungen vor TIFF/SIDECAR-IDs (2b, vorher nur Präfix-Glob), Einbettungsmarke und Vektorbestand (3c), Store upgrade 4 (oben), REBUILD_VECTORS_BEFORE (6, `^[0-9a-f]{64}$`). Store upgrade 5 und 7 schreiben nichts.
- **seed-probe.py:** `stock` nimmt eine kommagetrennte Ausschlussliste ("0" schließt nichts aus, 3c unverändert).

## TDD

- RED gegen den Workflow vor der Umsetzung: **18 failed, 73 passed**. Rot waren alle neuen bzw. umgeschriebenen Fälle außer den folgenden. Vorher grün und deshalb per Gegenprobe belegt:
  - `test_the_assurance_step_does_nothing_an_admin_would_do`: der alte Schritt hatte keinen Eingriff.
  - L-30-03-Fall für Store upgrade 5 und 7: keine Schreibstelle.
  - `test_the_checker_of_the_environment_sees_a_missing_check`: Negativprobe des Hilfsparsers.
- `test_every_counter_is_held_unchanged` ist **ersetzt** durch `test_every_counter_is_unchanged_or_moved_by_its_derived_step` plus `test_the_table_of_the_derived_steps_stands_above_the_step`. Grund: Die Saat bewegt drei Zähler, und der Fall verlangt jetzt je Zähler genau den hergeleiteten Schritt, nicht "alles unchanged". `test_the_assurance_step_states_that_nothing_was_embedded_again` verlangt jetzt `seed_probe stock "${new_seed_ids}"` statt `stock 0`.
- Gegenproben, je ein Eingriff in den Workflow, danach `cmp` gleich, alle rot:
  - `--restart` in Schritt 5
  - Containerprüfung, RestartCount-Prüfung, Markenprüfung (3c) oder Digestprüfung (6) entfernt
  - Schritt -1 auf -2
  - docs zurück auf unchanged
  - Wort cachequendel gestrichen
  - Digest ohne UPGRADE_CATCHUP_CHANGED
  - Kanariensuche vor der Bombe
- Stub-Lauf von Store upgrade 5 in Git-Bash mit gefälschten Proben, vier Varianten: ok grün ("all ten assurances hold"), falscher Schritt, Auszug ohne Präfix und RestartCount 1 jeweils rot mit der passenden Meldung. Dabei gefunden: der jq-Filter `.ocs.data.entries | length == 1 and ...` bindet das `and` in die Pipe und scheitert an der Liste. Korrigiert auf `(.ocs.data.entries | length == 1) and ...`. Der neue Fall `test_the_exact_hit_filter_reads_one_entry_of_the_right_file` wertet den Filter mit jq aus (richtige ID 0, falsche ID 1).

## Abweichungen vom Plan

**1. [Rule 1, Bug der Strecke aus 31-12] seed-probe.py las sys.argv[2] für jede Frage.**
- **Gefunden in:** Task 2, erster gemeinsamer Push, Lauf 38250670039 rot in Store upgrade 2b.
- **Befund:** Jede Runde "the reconcile of the released installation is 'unreadable'" mit `IndexError: list index out of range` (stdin Zeile 13). `seed_probe reconcile` hat kein Subjekt. Das Budget von 900 s lief ab.
- **Fix:** Subjekt optional. Neuer Fall `test_the_probe_answers_the_reconcile_question_without_a_subject` führt die Probe gegen eine reconcile-Tabelle nach v1.4.2 aus (store/repo.py:548-569 des Tags). Lokal rot mit genau diesem IndexError, danach grün. Zusätzlich `test_the_probe_answers_every_question_of_3c_and_5`: verdict, meta, chunks, rows, catchup, stock mit Liste und digest gegen schema.sql und die chunks-Tabelle von vectors.sql. Beide Dateien sind seit v1.4.2 unverändert (`git diff v1.4.2 HEAD` leer).
- **Commit:** a3911835. Produktcode unberührt.

**2. [Rule 2] Warten auf die Vektoren der Saat.** Store upgrade 6 vergleicht vectors.db bytegleich. Würde die Saat noch eingebettet, wenn 6 den Digest liest, wäre 6 aus einem Grund rot, der nichts mit dem Umbau zu tun hat. Im Lauf trug Datei 335 bei der letzten Wartezeile noch 0 Chunks. Die Wartebedingung war also nötig.

**3. Zusätzliche GITHUB_ENV-Werte** `UPGRADE_NEW_RESTARTS` (vom Plan verlangt, Name frei) und `UPGRADE_FINISHED_AT` (für die Nachholdauer). Beide sind musterprüft.

**4. "indexed in findling_file_state" ist "keine Zeile".** PHP schreibt indexed nie. Ein Erfolgsbericht löscht das Urteil (FileStateService.php:294-350). Die Zusicherung lautet daher: state.db indexed/ und 0 Zeilen in findling_file_state.

**5. Kandidatenurteil in findling_file_state.** 3c hat nur das state.db-Urteil aufgezeichnet. Store upgrade 5 hält findling_file_state gegen dasselbe Urteil, bei indexed gegen keine Zeile. Die Listen sind leer, der Zweig ist durch den Stub-Lauf abgedeckt.

**6. Push-Regel eingehalten.** Der erste gemeinsame Push b021f16c..cafa34df (zusammen mit 564231c8, d3952131) war rot. Der Fix folgte sofort als eigener Commit, nie Force-Push, origin/main hat sich nicht bewegt.

## Gates und CI

- Lokal vor cafa34df: ruff check, ruff format --check (215 Dateien), pyright latest 0 Fehler, vulture grün, volle Suite **5470 passed, 30 skipped** (853 s), darin tests/test_measurement_scripts.py. `backend/src/findling` und `php/` sind nicht berührt, die Baumhashes bleiben.
- Lokal vor a3911835: dieselben Gates, volle Suite **5472 passed, 30 skipped** (712 s).
- 5379853a (nur 30-AUDIT.md): kein Code, Gates aus a3911835 gelten unverändert.
- Push 1 (`8cf62567..cafa34df`):
  - HaRP deploy **38250670039** rot: stable34/ubuntu-24.04 in Store upgrade 2b, Befund 1 oben. Die übrigen drei Jobs waren grün.
  - Python gates 38250670037, Integration 38250670111, Resilience 38250669991, Multi-arch image 38250670030 und Security scans 38250670001: success.
  - OpenSSF Scorecard 38250670095 rot wegen GitHub-API 504 (ListCommits, extern), nach `gh run rerun --failed` success.
- Push 2 (`cafa34df..a3911835`), alle grün:
  - HaRP deploy **38256198997**: vier Jobs success. stable34/ubuntu-24.04 mit Store upgrade 0, 1, 2, 2b, 3, 3b, 3c, 4, 5, 6, 7 success (`gh run view --json jobs`).
  - Python gates 38256199035, Integration 38256198957, Resilience 38256198946, Multi-arch image 38256202248, Security scans 38256199000, OpenSSF Scorecard 38256199133 und 38256382511.

## Logzitate (Lauf 38256198997, Job stable34/ubuntu-24.04)

Saat unter v1.4.2 (Store upgrade 2b), die acht Zustände:

```
the eml seed has no row in state.db and none in findling_file_state
the zip seed has no row in state.db and none in findling_file_state
the bomb seed has no row in state.db and none in findling_file_state
the doc seed has no row in state.db and none in findling_file_state
the xls seed has no row in state.db and none in findling_file_state
the heic seed has no row in state.db and none in findling_file_state
the Word file under the .docx name is skipped/legacy_format in state.db and in findling_file_state
the released installation finished its reconcile cycle, so the next one is a day away
step 1: nc_app_findling_backend is stopped
step 2: the listener queued the stale file 342 as one content row with no delivery, the container stopped
step 3: the stale file holds 57 bytes and its size reads 4153 in oc_filecache and in the queue row
step 4: nc_app_findling_backend runs again and indexes without a switch
step 5: short read 1, the claim is dated back past the lock timeout (retries and lock now 1 2026-10-12 12:52:27)
step 5: short read 2, ... (retries and lock now 2 2026-10-12 12:52:42)
step 5: short read 3, ... (retries and lock now 3 2026-10-12 12:52:58)
step 5: three deliveries read short, the fourth claim wrote failed/repeatedly_stuck and took the row out
the stale file is failed/repeatedly_stuck in findling_file_state, has no row in state.db and none in the queue
none of the seven words finds a file on the v1.4.2 installation after the seed, and the positive control finds the picture
sown under v1.4.2: six new types and the bomb without a row, the Word file under .docx skipped(legacy_format), the stale file failed(repeatedly_stuck) without a container row
```

Der Abgleich von 1.4.2 lief ab 13:51:03 sieben Runden "open" und war um 13:52:24 beendet (rund 80 s).

Store upgrade 3c:

```
recheck mark 'done', embedding mark 'multilingual-e5-small/int8/384/1024', vector stock bf915800...c6399a:288:800, seed chunks 1 and 0
the old stock holds the catch-up candidates '', as determined
recheck_1_5_0 is absent; the old stock of 300 file(s) has the digest 8241bc7219d34e8a8fc7411ed6052309925b4d5d7e08746283cd780c504a497b
```

Store upgrade 4 und 5:

```
the container after the upgrade has restarted 0 time(s)
the seed is caught up: recheck_1_5_0 read done 303s and every word found exactly its file 360s after the end of Store upgrade 4
moved      .container.docs 288 to 295, the derived step +7
moved      .container.indexed 288 to 295, the derived step +7
unchanged  .container.skipped = 9
unchanged  .container.failed = 6
unchanged  .nextcloud.skipped = 9
moved      .nextcloud.failed 7 to 6, the derived step -1
unchanged  .nextcloud.scheduled = 0
unchanged  .nextcloud.running = 0
unchanged  .container.rebuildState = idle
the stored schema mark reads 2 after the upgrade, the 2 of v1.4.2, with no rebuild
the recheck mark read done before the upgrade and reads done after it, nothing was handed back
unchanged  embedding mark = multilingual-e5-small/int8/384/1024
unchanged  vector stock without the new seed, the picture included = bf915800...c6399a:288:800, nothing was embedded again
mailquendel finds exactly the file id 335
archivquendel finds exactly the file id 336
the excerpt of the ZIP hit starts with the inner file innen/notiz.txt
wortquendel finds exactly the file id 338
zellquendel finds exactly the file id 339
fotoquendel finds exactly the file id 340
hullequendel finds exactly the file id 341
cachequendel finds exactly the file id 342
the seed file 335 ... 342 is indexed with 1 chunk(s) and carries no verdict in findling_file_state   (sieben Zeilen)
the file v1.4.2 wrote off as failed(repeatedly_stuck) without a container row is indexed, and findling_file_state holds no verdict of it any more
the ZIP bomb is skipped/archive_limit in state.db and in findling_file_state
the container runs, restart count 0 as at the end of Store upgrade 4
the container answers the canary search after the bomb
no catch-up candidate of the old stock keeps its verdict (empty list of Store upgrade 3c)
no catch-up candidate of the old stock changes its verdict (empty list of Store upgrade 3c)
unchanged  the digest of the old stock over 300 file(s) = 8241bc7219d34e8a8fc7411ed6052309925b4d5d7e08746283cd780c504a497b
all ten assurances hold
```

Store upgrade 6 und 7:

```
the schema mark reads 2 before the rebuild and 3 after it, the schema of the start and of the running code
unchanged  .container.docs = 295
all ten assurances hold
vectors.db is unchanged at 36dcf137...622d2f, before the rebuild of Store upgrade 6, before the way back and after it
```

**Nachholdauer der Saat (für 31-15):** Vom Ende von Store upgrade 4 bis "recheck_1_5_0 done" vergingen 303 s. Bis jedes Wort seine Datei fand, die sieben Vektoren standen und die Bombe beurteilt war, vergingen 360 s. Die Werte sind auf eine Schleifenrunde genau (5 s plus Abfragen). Die erste Wartezeile um 13:53:58 zeigt Marke 'reconcile', Bombe 'none' und die Word-OLE (341) schon indexed (Teil A vor Teil B).

## Requirements

FMT-01 bis FMT-06 auf Complete (Owner-Linie: E2E-Beweis in 31-13). Der Lauf belegt je Format ein Wort Ende zu Ende auf einer echten Installation. Die übrigen Teilaussagen sind über die Unit-Tests der Pläne 31-04 bis 31-09 belegt: Betreff und Absender der Mail, benannte Skip-Urteile, Zellgrenze und ZIP-Grenzen einzeln. POL-02 war schon Complete und ist hier Ende zu Ende über die STALE-Saat belegt.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. Umgesetzt:

- T-31-41: Musterprüfung vor jedem GITHUB_ENV-Wert von 2b bis 7, Gate über sechs Schritte, Gegenproben.
- T-31-42: moved() und unchanged() exakt, Tabelle, kein at-least.
- T-31-43: Altbestands-Digest und Vektorbestand ohne Saat gleich.
- T-31-43b: archive_limit plus Running, RestartCount und Kanariensuche.

## Offene Punkte

- 31-15: Die Nachholdauer (303 s bis done, 360 s bis alles gefunden) gilt für einen Altbestand von 300 Dateien. Teil B ist ein Abgleich über alle Metadaten, also für große Instanzen gesondert messen.
- 31-15: Die Musterprüfungen aus 31-12 nutzen weiter `printf | grep -Eq` (Zeilen-Match). Die IDs kommen aus `sqlite3` einzeilig, deshalb kein Befund. Die neuen Prüfungen nutzen `[[ =~ ]]`.
- Das lokale Image findling_backend:1.4.3 ist unberührt. Für die Token-Prüfung wurde nur findling_backend:dev lesend gestartet (`docker run --rm`, Quellbaum read-only gemountet).

## Commits

| Commit | Inhalt | gepusht |
|---|---|---|
| b021f16c | ci(31-12): sow the new formats on 1.4.2 and record them before the upgrade | ja (gemeinsam mit cafa34df) |
| 564231c8, d3952131 | docs(31-12) | ja (gemeinsam mit cafa34df) |
| cafa34df | ci(31-13): the upgrade proof holds the old stock and finds the new formats | ja |
| a3911835 | fix(31-13): the seed probe answers the reconcile question without a subject | ja |
| 5379853a | docs(31-13): L-30-03 closed in the phase 30 audit | ja |

Läufe auf 5379853a (nur 30-AUDIT.md): Security scans 38259982638 und OpenSSF Scorecard 38259982518 success (die übrigen Workflows starten bei reinen .planning-Änderungen nicht).

## Self-Check: PASSED

31-13-SUMMARY.md, 30-AUDIT.md (`still_open: [L-30-02]`), deploy-harp.yml und test_upgrade_seed_steps.py vorhanden. b021f16c, 564231c8, d3952131, cafa34df, a3911835 und 5379853a liegen auf origin/main (`git branch -r --contains`). `grep -n "index --restart"` im Workflow trifft nur Zeilen vor Store upgrade 5.
