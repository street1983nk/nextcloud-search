# Härtungsmatrix 1.4.0 (Erfolgskriterium 1, Plan 29-04)

Stand: 06.10.2026, Basis 4293f921. Jede Zeile nennt bestehende Tests, die durch Lesen bestätigt wurden (nicht aus dem Namen erschlossen), und was sie wirklich zusichern. Lücken bekommen einen neuen Test in `backend/tests/test_launch_hardening.py`.

Lokaler Lauf (Windows, `PYTHONUTF8=1 uv run pytest -q -rs <datei>::<name>`), 06.10.2026: 22 passed, 2 skipped. Die beiden übersprungenen Fälle sind die SIGKILL-Fälle aus `test_slots_kill.py`, die nur unter Linux laufen (Prozessgruppen, `/proc`). Ihr Beleg ist die Linux-CI: Lauf 37413342090 (python.yml, ubuntu-24.04) auf 1a115cd9, dessen `backend/`-Baum mit der Basis 4293f921 identisch ist, 4448 passed, 13 skipped. Die CI läuft mit `-q` ohne `-rs`, der Lauf belegt also die Suite insgesamt und nicht jeden Einzelfall namentlich.

## Matrix

| # | Szenario | Bestehender Test (Datei::Name) | Was er wirklich zusichert | Ergebnis 06.10. | Lücke | Neuer Test |
|---|---|---|---|---|---|---|
| 1 | OOM mitten in N Slots | `tests/test_slots_kill.py::test_a_killed_child_mid_pass_is_retried_alone_and_indexed_once` | Echter Poller mit vier echten Kindern, ein Kind per SIGKILL getötet: kein Verdikt unter vier Slots, Solo-Nachlauf, jede Datei genau einmal im Index, Guard zählt einen OOM-Kill. | skipped lokal (nur Linux), Linux-CI grün | | |
| | | `tests/test_poller.py::test_a_scan_killed_beside_others_runs_again_alone_and_is_indexed` | Unit-Ebene, vier Slots: ein einmal getötetes Kind läuft allein nach, alle vier indexiert, ein Kill gemeldet. | passed | | |
| | | `tests/test_poller.py::test_a_scan_that_dies_alone_as_well_ends_as_out_of_memory` | Stirbt das Kind auch allein, endet nur diese Datei als `out_of_memory`, kein dritter Lauf. | passed | | |
| | | `tests/test_poller.py::test_the_solo_run_holds_the_gate_at_one` | Zwei getötete Kinder im selben Pass laufen nacheinander mit Gate-Limit 1 in Claim-Reihenfolge; zwei Kills gemeldet. Sichert NICHT zu, dass jedes Dokument genau einmal im Index steht, und nicht den Fall "eines schuldig, eines nur Nachbar". | passed | | |
| | | `tests/test_guard.py::test_a_rising_oom_kill_lowers_at_once`, `tests/test_guard.py::test_a_reported_child_kill_lowers_at_once_even_without_events` | Ein steigender `oom_kill`-Zähler oder ein gemeldeter Kind-Kill senkt sofort (`CAUSE_OOM_KILL`). | passed | ja | `test_two_children_killed_in_one_pass_are_retried_alone_and_only_the_guilty_one_is_out_of_memory` |
| 2 | Kill beider Spuren | `tests/test_slots_kill.py::test_a_killed_main_process_mid_pass_loses_no_row_and_indexes_once` | Hauptprozess mitten im Pass getötet: Lease bringt die Zeilen zurück, zweiter Lauf indexiert jede Datei genau einmal, Pass-Marke wird als `unclean_end` gelesen. Die Embed-Spur ist im Harness abgeschaltet (`FINDLING_EMBED_ENABLED=false`). | skipped lokal (nur Linux), Linux-CI grün | ja | `test_an_ocr_slot_and_the_embed_track_killed_in_one_run_leave_every_verdict_and_every_vector_after_the_restart` |
| 3 | Hardware-Schrumpfung | `tests/test_profile.py::test_a_shrunk_box_lowers_only_the_effective_level` | Auf 8 GB/4 Kerne mit gewähltem Leistung ist die Wirksam-Stufe Standard, das gewählte Profil bleibt, `downgraded` ist wahr. Nur Profilzustand, keine Slotzahl im Poller, kein Datenbestand. | passed | | |
| | | `tests/test_profile.py::test_a_tiny_box_falls_back_to_economy`, `tests/test_profile.py::test_unknown_hardware_gives_one_slot` | Kleine Box fällt auf Sparsam; unbekannte Hardware gibt einen Slot. | passed | | |
| | | `tests/test_precision.py::test_an_active_fp32_stays_on_a_shrunk_box` | Aktives fp32 bleibt auf geschrumpfter Box (Standard gewählt, Sparsam wirksam), Urteil `tight_box`. | passed | ja | `test_a_restart_on_a_smaller_box_lowers_the_effective_level_and_the_slots_and_loses_no_document` |
| 4 | Profilwechsel mitten im Vektor-Reindex | `tests/test_embedding_track.py::test_the_redelivery_carries_on_in_the_next_process` | Cursor der Band-Wiederauslieferung liegt in der Meta-Tabelle und läuft in einem zweiten Prozess zu Ende. Kein Profilwechsel im Test. | passed | | |
| | | `tests/test_embedding_track.py::test_a_precision_change_on_a_stock_above_the_list_ceiling_writes_every_document_again` | Bestand über der Listengrenze des Controllers: jedes Dokument wird zurückgegeben, der Sweep endet. | passed | ja | `test_a_profile_change_during_the_redelivery_lets_the_cursor_run_to_the_end_without_losing_a_band` |
| 5 | Modellwechsel mitten im Vektor-Reindex | `tests/test_embedding_track.py::test_a_drift_empties_the_stock_before_it_writes_the_mark_and_asks_for_the_documents_back` | Drift-Kette in fester Reihenfolge: leeren, Marke, Wiederauslieferung. | passed | | |
| | | `tests/test_embedding_track.py::test_an_abort_between_the_emptying_and_the_mark_leaves_the_drift_repeatable` | Abbruch zwischen Leeren und Marke ist wiederholbar, Dokumente werden einmal angefordert. | passed | | |
| | | `tests/test_embedding_track.py::test_a_switch_from_int8_to_fp32_weights_re_embeds_the_stock`, `tests/test_embedding_track.py::test_a_switch_from_fp32_to_int8_weights_re_embeds_the_stock` | Je ein einzelner Präzisionswechsel löst die Kette aus, Marke trägt die neue Präzision. Kein zweiter Wechsel vor Ende des ersten Neuschreibens. | passed | ja | `test_a_second_precision_change_before_the_first_rewrite_ends_leaves_a_consistent_stock_under_the_right_mark` |
| 6 | Umgebungsvariable gegen Profil | `tests/test_profile.py::test_a_deliberate_override_wins_and_says_so` | `resolve()` mit gesetzter Variable: Wert gewinnt, Quelle `env` (SOURCE_ENV). | passed | | |
| | | `tests/test_profile.py::test_the_injected_default_never_overrules_a_profile`, `tests/test_profile.py::test_an_out_of_range_override_is_ignored`, `tests/test_profile.py::test_an_override_also_moves_economy`, `tests/test_profile.py::test_slots_have_no_variable` | Deklarierter Default zählt nicht als Override, Werte außerhalb des Bereichs werden ignoriert, Sparsam wird auch bewegt, Slots haben keine Variable. | passed | | |
| | | `tests/test_info_xml_defaults.py` (8 Fälle) | Deklarierte Defaults in info.xml gleich den Konstanten, ein deklarierter Default zählt nie als Override. | passed | ja | `test_a_set_variable_beats_the_chosen_profile_in_the_snapshot_and_survives_a_profile_change` |
| 7 | Upgrade 1.3.2 auf 1.4.0 | `tests/test_embedding_track.py::test_a_v1_3_mark_without_a_precision_is_read_as_int8_and_nothing_is_re_embedded` | Eine 1.3-Marke ohne Präzisionsteil wird als int8 gelesen, keine Drift-Kette, keine Neu-Einbettung. | passed | ja, aber nicht in diesem Plan | Nachprüfung der Altbestände (D-29-10) samt CI-Saat gehört zu Plan 29-11 |

Die Lückenspalte stützt sich auf die Research-Tabelle "Launch-Härtung: Abdeckung Erfolgskriterium 1" (29-RESEARCH.md) und wurde beim Lesen der Tests bestätigt. Zeile 6 hatte in der Research zusätzlich `FINDLING_MAX_CELLS` in `EXPECTED` als Kandidat; das ist eine Produktänderung an info.xml (D-29-03) und gehört zum zugehörigen Fix-Plan, nicht hierher.

## Lückentests (Task 2)

Alle sechs in `backend/tests/test_launch_hardening.py`, aufgebaut auf den Stand-ins von `test_poller.py` (`_KillingExtractor`, `_slot_poller`, `_FakeQueue`) und `test_embedding_track.py` (`_FakeModel`, `_cut`, `_watched`, `_FakeQueue`). Ein Neustart ist wie in diesen Dateien ein zweiter Poller auf demselben Volume, mit dem Modulzustand (Profil, Präzision, Spur, Guard) im Ruhezustand. Lauf 06.10.2026 lokal (Windows): 6 passed.

| Zeile | Testname | Was er zusichert | Ergebnis 06.10. |
|---|---|---|---|
| 1 | `test_two_children_killed_in_one_pass_are_retried_alone_and_only_the_guilty_one_is_out_of_memory` | Vier Slots, Scan 300 stirbt auch allein, Scan 302 nur einmal: beide laufen allein nach, nur 300 endet als `out_of_memory`, kein dritter Lauf, zwei Kill-Meldungen, 7001 bis 7003 genau einmal im Index und `indexed`. | passed |
| 2 | `test_an_ocr_slot_and_the_embed_track_killed_in_one_run_leave_every_verdict_and_every_vector_after_the_restart` | Ein OCR-Kind getötet, danach stirbt die Embed-Spur beim dritten Dokument (BaseException, kein Handler kann sie zum Verdikt machen): Teilbestand an Vektoren, nichts zurückgegeben. Nach Neustart und Wiederauslieferung per Lease: alle vier Verdikte `indexed`, jedes Dokument einmal im Index, jedes trägt Vektoren, keine doppelten Chunks. | passed |
| 3 | `test_a_restart_on_a_smaller_box_lowers_the_effective_level_and_the_slots_and_loses_no_document` | Große Box (16 Kerne, 64 GiB) mit Leistung: Slotziel 15. Neustart auf 8 Kernen und 8 GB: Statusbericht nennt gewählt `performance`, wirksam `standard`, `downgraded`, Slotziel 3; alle acht Dokumente beider Boxen genau einmal im Index. | passed |
| 4 | `test_a_profile_change_during_the_redelivery_lets_the_cursor_run_to_the_end_without_losing_a_band` | Band-Wiederauslieferung mit Bandbreite 1 über drei Dokumente, Profil Sparsam, Standard, Sparsam zwischen den Bändern: jedes Band genau einmal, Cursor endet leer, Marke aktuell. | passed |
| 5 | `test_a_second_precision_change_before_the_first_rewrite_ends_leaves_a_consistent_stock_under_the_right_mark` | int8 zu fp32, nach dem ersten Band zurück zu int8: die Drift-Kette läuft ein zweites Mal vollständig, die zwischenzeitlichen fp32-Vektoren gehen mit, Marke endet auf int8 (1.3-Schreibweise), danach jedes Dokument einmal angefordert, Sweep endet. | passed |
| 6 | `test_a_set_variable_beats_the_chosen_profile_in_the_snapshot_and_survives_a_profile_change` | `FINDLING_OCR_MAX_PAGES` und `FINDLING_OCR_DPI` gesetzt, Profil Leistung, Sparsam, Standard nacheinander gewählt: im Statusbericht gewinnen beide Variablen jedes Mal mit Quelle `env`, alle anderen Werte bleiben `profile`, Slotzahl folgt dem Profil. | passed |

Positivkontrolle: Zeile 2 belegt im Test selbst, dass der Tod mitten in der Spur lag (0 < Dokumente mit Vektoren < 4, keine Rückgabe per unlock); Zeile 3 belegt, dass das Slotziel wirklich fällt (15 auf 3). Ein erster Entwurf von Zeile 5 war rot, weil die Filterfunktion `_drift_chain` auch die Sweep-Bänder nach der zweiten Kette zählt; das war ein Testfehler, kein Produktbefund, und ist im Test korrigiert.

## Befunde für 29-13

Audit in 29-13, Fix in 29-14 (29-14-PLAN: "Alle Befunde H-29-NN aus der Härtungsmatrix sind behoben, ihre xfail-Marken entfernt").

Keine. Alle sechs Lückentests laufen grün, kein Test trägt eine xfail-Marke, es gibt keinen Befund H-29-NN aus diesem Plan.

Offen bleibt nur der Nachweis der beiden Linux-Fälle aus `test_slots_kill.py` je Einzelfall: die CI läuft mit `-q` ohne `-rs`. 29-13 kann ihn mit einem CI-Lauf belegen, der `-rs` oder `-v` für diese Datei setzt.
