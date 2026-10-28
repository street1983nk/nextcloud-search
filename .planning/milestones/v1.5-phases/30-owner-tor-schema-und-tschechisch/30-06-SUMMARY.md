---
phase: 30-owner-tor-schema-und-tschechisch
plan: 06
subsystem: ci/upgrade-proof (deploy-harp.yml, Store upgrade 2b/3c/4/5)
tags: [cz-02, d-30-07, upgrade, deploy-harp, recheck, schema-2]
requires: [30-04]
provides:
  - "UPGRADE_FROM_TAG v1.4.2 mit fortgeschriebener Chronik"
  - "Store upgrade 2b: Saat unter 1.4.2 richtig geurteilt (Sidecar skipped/system_file, Bild indexed, Saatwort trifft genau das Bild), markiertes Andockende für Phase 31 (FMT-06)"
  - "Store upgrade 3c: recheck_1_4_0 == done vor dem Upgrade, ganzer Vektorbestand inklusive Bild"
  - "Store upgrade 5: alle neun Zähler unchanged, schemaVersion == \"2\" per Wert, rebuildState == idle, recheck bleibt done, Vektorbestand gleich"
  - "deploy-harp-Lauf 38033629694 grün über Store upgrade 0 bis 6"
affects: [30-07 Store upgrade 6/7 cs, 31 FMT-06 legacy_format-Saat]
tech-stack:
  added: []
  patterns: ["Zusicherung per Wert neben unchanged(), weil unchanged allein auch einen falschen Gleichstand durchlässt (Schema 3 auf beiden Seiten, laufender Bandlauf auf beiden Seiten)"]
key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
decisions:
  - "Vektorbestand in 3c/5 über `seed_probe stock 0` (ganzer Bestand, Bild eingeschlossen) statt ohne Bild: das Bild ist unter 1.4.2 schon eingebettet, eine zweite Einbettung muss Zusicherung 8 fangen"
  - "Zusicherung 3 ohne moved_by_seed: alle neun Zähler unchanged, Herleitung als Tabelle im Kommentar über Store upgrade 5"
  - "Zusätzliche Wertprüfungen schemaVersion == \"2\" und rebuildState == idle (T-30-26), weil unchanged allein einen Start ohne 1.4.2 bzw. einen schon laufenden Bandlauf nicht fängt"
  - "Store upgrade 4 läuft im Gleichstandszweig (Baum und Tag beide 1.4.2), Kommentar und notice-Zeile darauf fortgeschrieben"
  - "CZ-02 nicht abgehakt: erst nach 30-07 (Auftrag)"
metrics:
  duration: "ca. 60 min (davon ca. 16 min deploy-harp-Lauf)"
  completed: 2026-10-10
  tasks: 2
  files: 2
---

# Phase 30 Plan 06: Upgrade-Strecke ab v1.4.2 Summary

Die Upgrade-Strecke von deploy-harp startet von v1.4.2. Eine 1.4.2-Installation mit Werkssprachen de,en upgradet auf den Code von Phase 30 ohne Umbau: schemaVersion bleibt 2, languages bleibt de,en, rebuildState bleibt idle, recheck_1_4_0 steht vorher und nachher auf done, kein Zähler, kein Urteil und kein Vektor bewegt sich. Lauf 38033629694 auf Commit 0b2b645f ist grün, Store upgrade 0 bis 6 eingeschlossen.

## Ermittlung: wie 1.4.2 die Saat urteilt (vor dem Umbau, aus dem Code des Tags)

| Gegenstand | Urteil unter v1.4.2 | Quelle (v1.4.2) | im Lauf gemessen |
|---|---|---|---|
| AppleDouble-Sidecar `._seed-notes.docx` (26 Byte, `00 05 16 07`) | skipped(system_file) vor dem ersten Byte, in state.db und in findling_file_state | `backend/src/findling/worker/poller.py:1480-1482` (`is_sidecar_name` -> `ExtractionOutcome.skipped(Reason.SYSTEM_FILE)`), Regel `extract/errors.py:282` | `round 4: open=0 picture=indexed/ sidecar=skipped/system_file`; `the sidecar is skipped/system_file in state.db and in findling_file_state` |
| Grau+Extra-TIFF `upgrade-seed-grey-extra.tif` | indexed über den TIFF-Shim von Plan 29-07, kein Eintrag in findling_file_state | `backend/src/findling/extract/image.py:127` (`_SHIM_KEYS = _register_tiff_variants()`); `php/lib/Command/IndexCommand.php:140` (findling_file_state hält nur skipped und failed) | `the picture is indexed in state.db and carries no verdict in findling_file_state`; `the seed word finds exactly the file id 141` |
| Vektoren des Bildes | eingebettet (Economy) | Einbettungsspur 1.4.x | 3c: `seed chunks 1 and 0` |
| `recheck_1_4_0` nach dem Durchlauf | `done` | `backend/src/findling/worker/recheck.py:129` (schreibt `RECHECK_DONE` am Ende), angestoßen in `worker/poller.py:930-932`, sobald die Companion `VERDICTS_GENERATION` 2 meldet (`php/lib/Controller/ProfileController.php:49`, `nc/queue.py:131`); `recheck.py:99-102` kehrt bei done sofort zurück | 3c: `recheck mark 'done'` |
| schemaVersion | 2 | `backend/src/findling/config.py:49` | Assurance 2: `unchanged .marks.schemaVersion = 2` |

Folge für die Zusicherungen: Nach dem Upgrade auf den Phase-30-Code reicht der Recheck nichts zurück (Mark done, `recheck_step` kehrt sofort zurück), also bewegt sich keiner der neun Zähler. Bis 30-06 bewegten sich sechs davon um den hergeleiteten Schritt (+1, +1, +1, -2, +1, -2); das gilt nur für einen Start, der die Saat falsch urteilt (1.3.2).

Release-Assets geprüft am 2026-10-10: `gh release view v1.4.2` listet findling.tar.gz, findling.tar.gz.sig, findling_backend.tar.gz, findling_backend.tar.gz.sig (publiziert 2026-10-09T17:05:07Z); `ghcr.io/street1983nk/findling_backend:1.4.2` anonym mit linux/amd64 und linux/arm64.

## Task 1 (0b2b645f): Ausgangspunkt v1.4.2, Schritte 2b/3c/5

- `UPGRADE_FROM_TAG: v1.4.2`, Chronik um den Absatz 2026-10-10 (Plan 30-06, D-30-07) ergänzt, v1.3.2 bleibt als "2026-10-06 bis 2026-10-10" im Kommentar.
- **Store upgrade 2b** heißt "the seed of the released installation, judged by 1.4.2". Sät dieselben zwei Dateien, wartet auf das Urteil, sichert fail-closed: Sidecar `skipped/system_file` in state.db und findling_file_state, Bild `indexed/` mit 0 Einträgen in findling_file_state, Saatwort vorher 0 Treffer und danach genau 1 Treffer mit `attributes.fileId == tiff_id` (Wiederholung innerhalb desselben Budgets). Am Ende steht der markierte Block "Phase 31 (FMT-06) appends its legacy_format seed here", nach dem Export der beiden IDs.
- **Store upgrade 3c** verlangt `recheck == done`, wartet auf Einbettungsmarke UND Chunks des Bildes, hält den ganzen Vektorbestand (`seed_probe stock 0`) fest, Bild >= 1 Chunk, Sidecar 0 Chunks.
- **Store upgrade 4**: Gleichstandszweig ist jetzt der erwartete (Baum und Tag 1.4.2); Kommentar und notice-Zeile fortgeschrieben (Rule 1, die alte Zeile nannte "1.4.0 against 1.3.2").
- **Store upgrade 5** ("the eight assurances", Zahl bleibt acht): 3 = alle neun Zähler `unchanged`, `moved_by_seed` entfernt; neu per Wert `schemaVersion == "2"` (Assurance 2) und `rebuildState == "idle"` (Assurance 3); 3b = beide Saatdateien behalten ihr 1.4.2-Urteil; 6 = recheck vorher done, nachher done, languages de,en beidseitig; 7 (alemanes) unverändert; 8 = Einbettungsmarke und ganzer Vektorbestand gleich, Profil economy. Zusammenfassungszeilen auf die neue Ausgangslage (darunter die veraltete Zeile "languages mark is empty").
- Kein `1.3.2` mehr außerhalb von Kommentaren (neuer Gate-Fall `test_the_old_start_stands_in_comments_only`; eine Fehlermeldung in Assurance 6 nannte "the fresh directory of 1.3.2", jetzt `${UPGRADE_FROM_TAG}`).
- Gate `test_upgrade_seed_steps.py`: `test_the_proof_starts_from_v1_4_2`, `..._asserts_the_verdict_of_1_4_2_fail_closed`, `..._leaves_room_for_phase_31`, `test_every_counter_is_held_unchanged`, `test_the_assurance_step_demands_no_rebuild_and_schema_2`; Record-Fall verlangt `!= "done"`-Bruch statt `"absent"`; kein Fall verlangt mehr recheck absent (zusätzlich textweit verboten). Bash-Parsefälle, Einmaligkeit, ausdrucksfreier Run-Text und "kein at-least" bleiben.

RED belegt: vor der Workflow-Änderung 9 failed / 24 passed. GREEN: `test_upgrade_seed_steps.py test_upgrade_seed_fixture.py test_language_proof_steps.py` 69 passed; alle 11 Testdateien, die deploy-harp.yml lesen: 1071 passed, 1 skipped. ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün. actionlint lokal nicht installiert.

## Task 2: deploy-harp-Lauf

Push `1cdac186..0b2b645f` auf origin main (15 Commits, 30-03 bis 30-06). Lauf **38033629694** (HaRP deploy, headSha 0b2b645f21d3e9d8f6c0acc82503d584aad4238a, 07:12:35Z bis 07:28:39Z): **success**.

| Job | Ergebnis | Store upgrade 0-6 |
|---|---|---|
| 114159462681 deploy-harp (stable34, 8.2, ubuntu-24.04) | success | 0, 1, 2, 2b, 3, 3b, 3c, 4, 5, 6 alle success |
| 114159462713 deploy-harp (stable35, 8.3, ubuntu-24.04) | success | skipped (Strecke läuft nur auf stable34/x86) |
| 114159462717 deploy-harp (stable33, 8.2, ubuntu-24.04) | success | skipped |
| 114159462736 deploy-harp (stable34, 8.2, ubuntu-24.04-arm) | success | skipped |

**Store upgrade 6 ist ebenfalls grün**: die in 30-04 gedrehte Zusicherung 1 hält (`the schema mark reads 2 before the rebuild and 3 after it, the schema of the start and of the running code`, `all ten assurances hold`). Der Plan hätte ein rotes Store upgrade 6 in diesem Lauf erlaubt (Gegenstand von 30-07); das ist nicht eingetreten. Für 30-07 bleibt der cs-spezifische Teil (REBUILD_LANGUAGES cs,de, smlouve, Store upgrade 7).

Übrige Workflows desselben Pushes, alle success: Python gates 38033629707, Resilience 38033629704, Multi-arch image 38033629697, Integration 38033629687, Security scans 38033629670, OpenSSF Scorecard 38033629691.

Logzitate (Job 114159462681):

```
Store upgrade 2b: round 4: open=0 picture=indexed/ sidecar=skipped/system_file, 883s of the budget left
Store upgrade 2b: sown: a picture indexed and a sidecar skipped(system_file) under v1.4.2, and the seed word finds exactly the picture
Store upgrade 3c: recheck mark 'done', embedding mark 'multilingual-e5-small/int8/384/1024', vector stock 7809e2d4...9dab82:95:223, seed chunks 1 and 0
Store upgrade 4:  installed_version went from 1.4.2 to 1.4.2
Store upgrade 5:
unchanged  .marks.schemaVersion = 2
the stored schema mark reads 2 after the upgrade, the 2 of v1.4.2, with no rebuild
unchanged  .container.docs = 95 / .container.indexed = 95 / .container.skipped = 8 / .container.failed = 6
unchanged  .nextcloud.skipped = 8 / .nextcloud.failed = 6 / .nextcloud.scheduled = 0 / .nextcloud.running = 0
unchanged  .container.rebuildState = idle
the rebuild state is idle after the upgrade, no band run
the seed word finds exactly the file id 141, as it did on v1.4.2
no reindex banner: backend.reindexRequired is false, ...
no start_rebuild_on_drift line in 42 lines of container log
the recheck mark read done before the upgrade and reads done after it, nothing was handed back
the languages mark reads de,en before and after the upgrade, nothing was restamped
the Spanish question answers 0 hits after the upgrade, unchanged against the v1.4.2 installation, ...
unchanged  embedding mark = multilingual-e5-small/int8/384/1024
unchanged  vector stock, the picture included = 7809e2d4...9dab82:95:223, nothing was embedded again
the picture carries 1 chunk(s), the ones it was embedded with before the upgrade
the profile in force after the upgrade is economy
all eight assurances hold
```

(Die Zählerzeilen sind hier zusammengezogen, im Log steht jede einzeln.)

## Commits

| Commit | Inhalt |
|---|---|
| 0b2b645f | ci(30-06): the upgrade proof starts from v1.4.2 |

## Deviations from Plan

**1. [Rule 2 - Beweisschärfe] Wertprüfungen neben unchanged()**
- `unchanged` allein ließe Schema 3 auf beiden Seiten und einen schon vor dem Upgrade laufenden Bandlauf durch. Deshalb in Store upgrade 5 zusätzlich `.marks.schemaVersion == "2"` und `.container.rebuildState == "idle"` (T-30-26).

**2. [Rule 2 - Beweisschärfe] Vektorbestand mit Bild**
- Bis 30-06 lag das Bild außerhalb des Digest, weil es auf dem Upgradeweg neu eingebettet wurde. Unter 1.4.2 ist es schon eingebettet; der Digest umfasst jetzt den ganzen Bestand (`seed_probe stock 0`, keine Zeile hat file_id 0), und 3c wartet auf die Chunks des Bildes.

**3. [Rule 1 - veralteter Text] Store upgrade 4 und Assurance-6-Meldung**
- Kommentar und notice-Zeile von Store upgrade 4 nannten "1.4.0 against the 1.3.2", eine Fehlermeldung in Assurance 6 nannte "the fresh directory of 1.3.2". Beides auf die neue Ausgangslage bzw. `${UPGRADE_FROM_TAG}`. Nicht in der Schrittliste des Plans, aber nötig für das Akzeptanzkriterium "v1.3.2 nur in Chronik-Kommentaren".

**4. Kein separater RED-Commit**
- Der Auftrag verlangt grüne lokale Gates vor jedem Commit; RED wurde lokal belegt (9 failed), committet wurde Gate und Workflow zusammen.

## Known Stubs

Keine. Der Andockblock für Phase 31 in Store upgrade 2b ist ein Kommentar, kein Platzhaltercode.

## Threat Flags

Keine neue Angriffsfläche. T-30-24: jede Zusicherung neu abgeleitet und per Gate wörtlich geprüft, Beleg aus dem v1.4.2-Code in der Tabelle oben; keine Zusicherung entfällt ersatzlos (moved_by_seed -> unchanged mit Herleitung, recheck absent -> done mit Quelle). T-30-25: Run-Texte von 2b/3c/5 ohne `${{`, Gate-Fall bleibt. T-30-26: schemaVersion 2 und rebuildState idle per Wert.

## Self-Check: PASSED

- .github/workflows/deploy-harp.yml: `UPGRADE_FROM_TAG: v1.4.2` genau einmal, `1.3.2` nur in Kommentarzeilen (Gate-Fall grün)
- backend/tests/test_upgrade_seed_steps.py: `test_the_proof_starts_from_v1_4_2` vorhanden
- Commit 0b2b645f im Log und auf origin/main
- Lauf 38033629694 success, Store upgrade 0 bis 6 success im Job 114159462681
