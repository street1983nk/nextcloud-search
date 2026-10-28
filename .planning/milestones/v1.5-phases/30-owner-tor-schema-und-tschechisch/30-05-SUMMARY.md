---
phase: 30-owner-tor-schema-und-tschechisch
plan: 05
subsystem: index/rebuild (Bandlauf, Bestandspfad, Feldebene cs)
tags: [cz-02, cz-03, rebuild, schema-3, a2, beweis]
requires: [30-03, 30-04]
provides:
  - "backend/tests/test_czech_switch.py: Bestand ohne Umbau (Schema 2, Schema 2 + es, 1.2.x Schema 1), echter Writer auf Schema-2-Verzeichnis, cs an (de,cs) und aus (de,en) über rebuild_the_index, Vektorbestand unberührt, halbgefülltes Schema-2-Ziel verworfen, Feldebene Stoppwörter/Flexion/byt"
  - "A2 für cs gemessen: 0.358 Zuwachs über 2000 Dokumente, GROWTH_PER_LANGUAGE bleibt 0.40"
affects: [30-06 Upgrade-Ausgang v1.4.2, 30-07 Store upgrade 7 cs an/aus, 30-08/30-09 Doku CZ-03]
tech-stack:
  added: []
  patterns: ["Feldebene-Beweis doppelt: Suchzeile über die Kette und doc_freq im Termwörterbuch, weil eine Stoppwort-Frage allein trivial leer ist", "Gegenprobe je Feld mit Wortformen, die nur eine Kette zusammenführt (Mietverträgen/de, leased/en)"]
key-files:
  created:
    - backend/tests/test_czech_switch.py
  modified:
    - backend/src/findling/index/rebuild.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "GROWTH_PER_LANGUAGE bleibt 0.40: cs kostet 0.358 (Lastkorpus) bzw. 0.213 (Zipf-Korpus), es auf demselben Text 0.361 bzw. 0.210; die stemmerlose Kette ist nicht teurer als eine Snowball-Kette"
  - "Messkorpus: 2000 Ausschnitte zu je 4940 Zeichen aus .dev/probe-live/loadcorpus (9.88 MB wie 2026-09-24); der künstliche Korpus von 2026-09-24 (/tmp/probe18d.py) liegt nicht im Repo"
  - "CZ-02 und CZ-03 nicht abgehakt: CZ-02 erst nach 30-07 (CI-Strecke), CZ-03 verlangt die Doku der Grenze (30-08/30-09)"
metrics:
  duration: "ca. 75 min (davon 2 x ca. 10 min volle Suite)"
  completed: 2026-10-10
  tasks: 2
  files: 3
---

# Phase 30 Plan 05: cs an/aus über den Bandlauf, Bestand ohne Umbau, Feldebene Summary

Auf echtem tantivy und über den echten `rebuild_the_index` ist bewiesen: ein Schema-2-Bestand baut unter Schema-3-Code nicht um und schreibt über `IndexBatchWriter` weiter; `de,en -> de,cs` baut per Re-Analyse ein 14-Felder-Verzeichnis mit Marken `3`/`de,cs`, in dem `smlouve` nur über `body_cs` trifft; `de,cs -> de,en` baut erneut um und lässt `body_cs` leer; der Vektorbestand bleibt bytegleich. Stoppwörter, die Flexionsgrenze (CZ-03) und die Ausnahme `byt` stehen auf Feldebene fest. A2 ist für cs gemessen (0.358), 0.40 hält.

## Ergebnis

**Task 1 (cb2cefe4), zehn Fälle, alle ohne Änderung an `src` grün:**

| Fall | Zusicherung |
|---|---|
| Bestand Schema 2, `de,en` | `NOTHING_TO_REBUILD`, 13 Felder (meta.json), Marken unverändert, Plan body_de/body_en/name/title |
| Bestand schreibt weiter | `IndexBatchWriter.add(IndexRecord)` + `flush` auf der Schema-2-Fixture, 13 Felder, Marken gleich; `mietvertrag` über den Plan und über body_de, nicht über body_en; `lease` über den Plan und über body_en, nicht über body_de |
| Bestand Schema 2, `de,en,es` | kein Umbau, `body_es` im Plan, `body_cs` nicht |
| 1.2.x Schema 1, keine Sprachmarke | kein Umbau, Marke bleibt `1`, Plan == `LEGACY_PLAN` |
| cs an (`cs,de` -> `("de","cs")`) | `REBUILD_THROUGH`, 14 Felder, Marken `3`/`de,cs`, body_en nicht im Plan, `smlouve` und `SMLOUVĚ` finden das Dokument |
| Gegenprobe cs an (eigener Fall) | `smlouve` nur gegen body_de: leer; gegen body_cs: Treffer |
| cs aus (`de,en`) | `REBUILD_THROUGH`, Schema bleibt `3`, Marke `de,en`, `terms_with_prefix(body_cs, "")` leer, `smlouve` über Plan und body_en |
| Vektorbestand | SHA-256 über vectors.db (plus Beiwerk) vor, nach cs an und nach cs aus gleich, ein Chunk bleibt |
| Halbgefülltes Ziel, direkt | Ziel mit 13 Feldern, 2 Dokumenten und Fingerabdruck der Schema-2-Erwartung: `_make_the_target_fit_this_code` verwirft (Log "other version marks"), danach 14 Felder, 0 Dokumente, neuer Fingerabdruck |
| Halbgefülltes Ziel, ganzer Lauf | Bandlauf über so ein Ziel: 14 Felder, 2 Dokumente, Schema `3`, `smlouve` über body_cs |

Der cs-an-Beweis nutzt nirgends `en` (Pitfall 5).

**Task 2 (26fab028):**
- Stoppwörter: ein Dokument aus "proč už jsem a nebo" plus allen Einträgen des Lucene-Originals (ohne die zwei Ausnahmen `být`/`jež` -> `byt`/`jez`), ein Kontrolldokument "Pronájem kanceláře". Für jeden Eintrag in Original- und gefalteter Schreibweise: Suchzeile auf body_cs leer UND `doc_freq(body_cs, ...) == 0`. Positivkontrolle: `pronajem` findet das Kontrolldokument, `doc_freq("kancelare") == 1`.
- CZ-03-Negativfall: `smlouvě` findet nur das smlouvě-Dokument, nie das smlouva-Dokument; `Smlouve` findet das smlouvě-Dokument. Docstring: dokumentierte Grenze, kein Fehler.
- Ausnahme: "Nájemní smlouva na byt", `byt` trifft auf body_cs.
- A2 gemessen, Kommentar über `GROWTH_PER_LANGUAGE` um drei Zeilen ergänzt (Wert bleibt 0.40), Baumhash `21275bc1...ebff9` mit Journalabsatz Plan 30-05, `PACKAGE_FILES_TODAY` bleibt 74.

## Messung A2 (2026-10-10)

Skript im Scratch (nicht im Repo; das Skript von 2026-09-24 lag nur unter `/tmp/probe18d.py`). Je Aufbau ein frisches Verzeichnis über `open_index`, Writer 50 MB/1 Thread, ein Commit, Größe aller Dateien.

| Korpus | Dokumente | Text | de,en | de,en,cs | Zuwachs cs | Zuwachs es |
|---|---|---|---|---|---|---|
| Lastkorpus (`.dev/probe-live/loadcorpus`, Ausschnitte à 4940 Zeichen) | 2000 | 9.88 Mio. Zeichen, 10.33 MB | 27 116 711 B | 36 809 820 B | **0.358** | 0.361 |
| Zipf über die Fixture-Wortliste | 2000 | 9.88 Mio. Zeichen | 7 119 184 B | 8 636 102 B | 0.213 | 0.210 |

Ergebnis: höchstens 0.358 <= 0.40, `GROWTH_PER_LANGUAGE` **nicht bewegt**. cs liegt in beiden Korpora innerhalb von 1 Prozent der Snowball-Kette es, die Annahme "eine befüllte Kette kostet gleich viel" gilt also auch ohne Stemmer.

## TDD-Belege und Positivkontrollen

Der Plan erwartet, dass alle Fälle ohne `src`-Änderung grün sind (30-03/30-04 liefern die Bausteine), deshalb gibt es keinen RED-Commit. Die Trennschärfe ist per Mutation an `src` belegt; jede Mutation wurde per `git checkout -- <datei>` zurückgedreht, nichts davon ist committet.

| Mutation | rot gewordene Fälle |
|---|---|
| M1 `("2","3")` aus `LEGACY_SCHEMA_STEPS` | Bestand Schema 2, Bestand mit es |
| M6 `("1","3")` aus `LEGACY_SCHEMA_STEPS` | 1.2.x Schema 1 |
| M2 `ascii_fold` aus `czech_analyzer` | cs an, Gegenprobe cs an, Lauf über halbgefülltes Ziel, Stoppwörter, Flexion |
| M3 `_document_from` schreibt body_cs immer | cs aus |
| M4 `_make_the_target_fit_this_code` verwirft nie | beide Fälle halbgefülltes Ziel |
| M5 Writer lässt body_en aus | Bestand schreibt weiter |
| M7 Umbau überschreibt vectors.db | Vektorbestand |
| M8 Stoppwortfilter aus `czech_analyzer` | Stoppwörter |
| M9 Präfix-Trigramm statt `simple` (führt smlouva/smlouvě zusammen) | Flexion (`{1, 2} == {2}`), Stoppwörter, byt |
| M10 `byt` zurück auf die Stoppliste | byt |

## Commits

| Commit | Inhalt |
|---|---|
| cb2cefe4 | test(30-05): Bestand, cs an und aus über den Bandlauf |
| 26fab028 | test(30-05): Feldebene cs, A2 gemessen, Baumhash |

Gates vor jedem Commit: ruff (Vollsatz), ruff format, pyright latest 0 Fehler, vulture grün; volle Suite nach Task 1: 4763 passed / 25 skipped, nach Task 2: 4766 passed / 25 skipped (Skipzahl unverändert). Nicht gepusht (Plan verlangt kein CI).

## Deviations from Plan

**1. [Rule 1 - Testschärfe] Gegenprobe-Wörter des Falls "Bestand schreibt weiter"**
- Der Plan nennt "Mietvertrag" und "lease". Gemessen trifft `mietvertrag` aber auch über body_en (die englische Kette faltet und lässt die Grundform stehen), und `lease` über body_de (der deutsche Stemmer kürzt `lease` und `leases` auf `leas`). Mit diesen Formen wäre die Gegenprobe "das andere Feld allein findet nichts" rot gewesen, ohne dass etwas falsch ist.
- Fix: der Dokumenttext trägt `Mietverträgen` (nur die deutsche Kette führt es auf `mietvertrag`) und `leased` (nur die englische Kette führt es auf `leas`); die Suchwörter bleiben `mietvertrag` und `lease`. Vorher per Analyse beider Ketten geprüft.

**2. [Rule 2 - Beweisschärfe] Stoppwortfall fragt zusätzlich das Termwörterbuch**
- Eine Suchzeile aus einem Stoppwort läuft durch dieselbe Kette und wird leer, egal was im Index steht; der Fall wäre allein damit trivial grün. Deshalb zusätzlich `doc_freq(body_cs, Schreibweise) == 0`, und das Stoppwortdokument enthält die ganze Originalliste statt nur der fünf Beispielwörter (die fünf sind als Teilmenge zugesichert).

**3. Messkorpus A2**
- Das Skript der Messung von 2026-09-24 liegt nicht im Repo, sein künstlicher Korpus ist nicht reproduzierbar. Gemessen wurde mit gleicher Dokumentzahl und Textmenge auf zwei Korpora und mit es als Vergleich auf demselben Text; maßgeblich ist der höhere Wert (0.358).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-30-20 (Marken genau nach dem Lauf: Schema 3 + Sprachen in cs an/aus), T-30-21 (A2 für cs gemessen, 0.40 hält), T-30-22 (halbgefülltes Schema-2-Ziel verworfen, direkt und im ganzen Lauf) sind durch die Fälle oben abgedeckt.

## Self-Check: PASSED

- backend/tests/test_czech_switch.py vorhanden (13 Fälle, `IndexBatchWriter`, `rebuild_the_index`, `field_plan_for`)
- Commits cb2cefe4 und 26fab028 im Log
- rebuild.py Zeile 146: Messzeile cs mit Datum 2026-10-10
