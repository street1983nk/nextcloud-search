# Phase 23: aufgeschobene Punkte

## Aus Plan 23-01 (27.09.2026)

- **tests/test_one_load.py, 7 Fälle rot** (`test_one_process_pays_for_one_engine_and_one_word_list`, `test_the_fourth_phase_releases_the_weights_and_fetches_them_back`, `test_the_cold_start_duration_is_a_line_of_its_own`, `test_the_entry_point_prints_its_numbers_and_exits_zero`, `test_it_goes_red_when_the_search_side_builds_its_own_engine`, `test_a_second_run_in_the_same_process_measures_a_load_and_not_a_cache_hit`, `test_it_goes_red_when_the_warm_up_loads_twice`).
  Ursache: `tools/one_load.py::drive_the_search_side` erwartet, dass `one_round` selbst lädt (`engine-loads-after-search=0` statt 1). Das ist die gewollte Folge von D-01.
  Zuständig: Plan 23-04, Task 1 (files_modified enthält `tools/one_load.py` und `tests/test_one_load.py`, Treiber bekommt den Handlerweg `warm_wanted()`/`warm()`). Nicht in 23-01 gefixt, damit die beiden Pläne nicht dieselben Dateien bearbeiten.

## Aus 23-04

- **Oberflaechentext der Admin-Seite (admin.php + 7 Sprachdateien) zum Zustand `cold`/`unloaded`:** Die Doku (`docs/admin-page.md`) ist praezisiert, der ausgelieferte Oberflaechentext selbst noch nicht. Owner-Frage am 23-08-Checkpoint: mitaendern (dann in 23-07/23-08 einarbeiten, 8 Dateien) oder so lassen (Doku erklaert den Unterschied)?
- **`docs/performance.md:3480` nennt noch `cold-search-ms=`:** datierter Messbericht, bewusst nicht angefasst.

## Aus 23-08 (Phasenaudit, docs/audits/2026-09-phase-23/README.md)

- **F-23-04 (LOW): Admin-Suche nach einem Pfad ohne Besitzer lehnt in einem Randfall ab.**
  `PathResolverService::rootsCarrying` sucht Einhängepunkte mit `/%/files/<Ordner>/`; das Prozentzeichen reicht über Schrägstriche und trifft auch einen tieferen Mount eines anderen Nutzers, dessen eigener Ordner `files` heißt. Dessen Wurzel zählt als zweite, und die Suche antwortet "nicht gefunden". Nie eine falsche Datei (`carriersOfMountedPath` verwirft die Zeile).
  **Verdikt:** kein Fix in 1.3.0, vom Owner am 27.09.2026 bestätigt: "Ja, v1.4-Backlog". **Begründung:** reine Admin-Route, falsch-negativ statt falsch-positiv, Umgehung vorhanden (Besitzer vor den Pfad setzen), und ein Umbau der Abfrage kurz vor der Abgabe bräuchte einen neuen PHPUnit-Fall plus HaRP-Lauf für einen Randfall ohne Meldung aus dem Feld.
  **Zieladresse:** v1.4-Backlog, Datei `php/lib/Service/PathResolverService.php` (`rootsCarrying`, `mountedAtOneOf`): Muster auf `/<uid>/files/<Ordner>/` einengen, etwa über einen zweiten Filter `NOT LIKE '/%/%/files/%'` oder über den Abgleich in PHP vor dem Zählen der Wurzeln; Fall "tieferer Mount eines Ordners namens files" in `PathResolverServiceTest.php`.

- **F-23-05 (LOW, Owner-Frage): Oberflächentext der Admin-Seite zu `cold`/`unloaded`** (Fortsetzung des Merkers aus 23-04).
  Stand: `cold` sagt "The model is read when it is first needed. That is the normal state.", `unloaded` sagt "The model was released to save memory. The next search answers with full text hits and loads it again in the background." Beide Sätze stimmen nach dem Kaltstart-Fix; nur `cold` sagt nicht dazu, dass auch die erste Suche mit Volltexttreffern antwortet. `docs/admin-page.md` Spalte 3 sagt es.
  **Entschieden am 27.09.2026, Owner-Wort "So lassen":** kein Umbau der acht Dateien, `docs/admin-page.md` genügt. Der Merker aus 23-04 ist damit erledigt. Begründung des Vorschlags: Der Satz ist nicht falsch, eine Änderung heißt acht Dateien (admin.php plus sieben Sprachkataloge) mit neuen Übersetzungen kurz vor der Abgabe, und die Doku erklärt den Unterschied.
  **Zieladresse, falls der Owner "mitändern" wählt:** Plan 23-08 als Fix vor 23-09 (admin.php Zeile 76, `php/l10n/*.js` und `*.json`, `test_admin_ui_contract.py`), danach Push und PHP-Lauf.

- **F-23-01 bis F-23-03:** behoben in diesem Plan, siehe Befundliste des Berichts. Kein Merker offen.

## Aus Issue #14 (27.09., ntfy-Meldung an den Owner)

- **budachst fragt (26.09. 20:00Z): "I can always throw the index away and start over, can't I?"** Owner-Entscheid 27.09.: KEINE Zwischenantwort; die abgenommene Post-Release-Antwort (store-listing.md Teil 6, "requeues every entry ... nothing has to be done by hand") beantwortet die Frage mit. Fuer 23-09: beim Posten der Antwort auf diesen letzten Kommentar antworten, damit der Bezug stimmt.
