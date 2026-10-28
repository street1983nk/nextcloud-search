---
phase: 30-owner-tor-schema-und-tschechisch
plan: 07
subsystem: ci/upgrade-proof (deploy-harp.yml, Store upgrade 2/3/5/6/7)
tags: [cz-02, d-30-07, upgrade, deploy-harp, rebuild, schema-3, czech]
requires: [30-05, 30-06]
provides:
  - "Store upgrade 6 schaltet de,en -> de,cs (REBUILD_LANGUAGES cs,de, normalisiert de,cs): Schema 2 -> 3, Lesestelle sucht und füllt de,cs, smlouve 1, proc 0, alemanes 0, Vektorbestand gleich"
  - "Store upgrade 7 (neu) schaltet de,cs -> de,en zurück: Schema 3 -> 3, Lesestelle de,en, body_cs ohne Term, smlouve 1, proc 1, vectors.db gleich dem Stand vor beiden Umbauten"
  - "rebuild-probe.sh: Neustart, Überblickleser, Vektordigest und Sprachprobe einmal geschrieben, von 6 und 7 gesourct"
  - "deploy-harp-Lauf 38036946762 grün über Store upgrade 0 bis 7"
affects: [30-08/30-09 Doku CZ-03, 31 FMT-06 (Andockblock 2b unverändert)]
tech-stack:
  added: []
  patterns: ["Trennscharfer Sprachbeweis: Stoppwortfrage als Unterscheider (proc 1/1/0/1), weil die Akzentfrage allein auch über body_en grün wäre", "Lesestelle direkt befragt (resources.searched_languages + terms_with_prefix über ALLE Körperfelder), statt nur der Marken"]
key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
    - backend/tests/test_language_proof_steps.py
decisions:
  - "term_hits zählt für smlouve und proc keine Vektortreffer: Ein-Wort-Zeilen laufen nach der One-term-Regel rein lexikalisch (api/search.py:307-308), Beleg unten"
  - "Spanisch-Zusicherung in Store upgrade 6 wird zu alemanes == 0 (Kette 0, 0, 0); Spanisch über den Bandlauf ist nicht mehr Gegenstand der Upgrade-Strecke, Spanisch selbst bleibt im Sprachbeweis jedes Beins"
  - "Füllkorpus 64 -> 256 Dokumente: der de,cs-Bandlauf war mit 64 schneller vorbei, als Nextcloud den neuen Container erreichte (Lauf 38035652649)"
  - "SNAPSHOT_RUN_MAX 20726 -> 20957, begründet: die zwei Czech-Zähler gehören in den einen snapshot(), die Erklärung steht als YAML-Kommentar außerhalb des Run-Blocks"
  - "CZ-02 abgehakt (Bandlauf an/aus auf echter Nextcloud grün)"
metrics:
  duration: "ca. 55 min (davon 2 deploy-harp-Läufe à ca. 18 min)"
  completed: 2026-10-10
  tasks: 2
  files: 3
---

# Phase 30 Plan 07: cs an und aus in der Upgrade-Strecke Summary

Die Upgrade-Strecke von deploy-harp schaltet auf einer echten Nextcloud Tschechisch ein (de,en -> de,cs, ohne en) und wieder aus (de,cs -> de,en), beides per Bandlauf, ohne Neu-Einbettung. Die Kette smlouve 1, 1, 1, 1 und proc 1, 1, 0, 1 über Release, Upgrade, cs an, cs aus zeigt, dass im cs-Zustand nur body_cs antwortet. Lauf **38036946762** auf Commit 21d83c0c ist grün, Store upgrade 0 bis 7 eingeschlossen.

## Klärung vorab: zählt term_hits Vektortreffer?

Nein, nicht für diese zwei Fragen. Beleg:

- `term_hits` fragt die OCS-Route `ocs/v2.php/search/providers/findling/search?term=$1` mit genau einem Wort.
- `backend/src/findling/api/search.py:307`: `lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only or sort != "relevance"`; Zeile 308 baut die `SemanticSide` nur `if not lexical_only`. `one_term` kommt aus `query/rewrite.py:637` (`carries_one_term(text)`, Definition Zeile 385; Tests `test_query_rewrite.py:380-414`).
- Dieselbe Begründung trägt seit Plan 19-08 die alemanes-0-Zusicherung (Kommentar in Store upgrade 2, "the one term rule of plan 06.1-20 ... the vector half is not built for this question at all").
- Folge: `smlouve` und `proc` sind je ein Wort, also rein lexikalisch. Die proc-0-Zusicherung bleibt eine Aussage über Felder, nicht über Vektordistanzen. Dateiname `upgrade-dopis-cs.txt` trägt keines der Wörter (name-Feld), txt-Dateien haben kein title.

Lokal vorab gemessen über die ausgelieferten Ketten (2026-10-10):

| Kette | Dokument "Proč je Smlouvě o nájmu bytu třeba podpis." | smlouve | proc |
|---|---|---|---|
| de | proč, je, smlouvě, ... | smlouv | proc |
| en | proc, je, smlouv, ... | smlouv | proc |
| cs | smlouve, najmu, bytu, treba, podpis | smlouve | (leer) |

Also de,en: beide über body_en; de,cs: smlouve nur über body_cs, proc gar nicht. Die Sprachprobe im Container (`rebuild-languages.py`) wurde vorher lokal gegen einen cs-an/aus-Bestand aus `test_czech_switch.py` geprüft: `{"searched": "de,cs", "filled": "de,cs"}` bzw. `{"searched": "de,en", "filled": "de,en"}`.

## Task 1 (6b86643e): Korpus, Snapshot, Umbau an, Rückweg

- Job-env: `REBUILD_LANGUAGES: 'cs,de'`, `REBUILD_LANGUAGES_NORMALISED: 'de,cs'`, neu `REBUILD_LANGUAGES_BACK: 'de,en'`; Begründung (unsortiert bleibt Absicht, cs statt es wegen D-30-07 und Pitfall 5).
- Store upgrade 2: tschechisches Dokument per printf mit oktalem UTF-8 (Workflow bleibt ASCII), Kommentar wozu.
- Store upgrade 3: Snapshot um `czech` (smlouve) und `czechStop` (proc), eigene Schlüssel neben `.terms`; vorher verlangt 1 und 1. Die Kettentabelle steht als YAML-Kommentar über dem Schritt.
- Store upgrade 5: beide nach dem reinen Upgrade 1 und 1.
- Store upgrade 6: Neustart, Leser und Probe in `rebuild-probe.sh` ausgelagert (wie `upgrade-probe.sh`, einmal geschrieben, zweimal gesourct); Vorbedingung czech 1/1; Assurance 1 bleibt "2 vor, 3 nach"; Assurance 10 neu: Lesestelle sucht und füllt de,cs, smlouve 1, proc 0, alemanes 0; `REBUILD_VECTORS_BEFORE` per GITHUB_ENV an Schritt 7.
- Store upgrade 7 (neu, direkt nach 6, gleiche `if`, Matrixwerte als env, ausdrucksfrei): Vorbedingungen (Marke de,cs, Schema 3, idle, Terme je 1, czech 1/0), Neustart mit de,en, Warten auf Bandlauf, sieben Zusicherungen (Schema 3/3, Marke de,en, Lesestelle de,en ohne cs, Terme/Dokumente/Arbeitsbestand unverändert, smlouve 1 proc 1, keine Drift-Zeile, vectors.db gleich vor 6, vor 7 und nach 7), Zusammenfassungszeilen. Beweisdateien rebuild-back-* im Artefakt.
- Gates: `test_upgrade_seed_steps.py` um 14 Fälle (env-Werte, Sechs-Sprachen-Strecke unberührt = 7 Vorkommen, Dokument und Dekodierung des printf, Snapshot-Schlüssel, Kette 1/1/0/1, Lesestellenprobe, Spanisch 0, Schritt 7 genau einmal direkt nach 6 mit gleicher `if`, ein gemeinsamer Neustart, Vektordigest, Marke/Drift, ausdrucksfrei, Bash-Parse für 2/3/3c/4/5/6/7); Schema-Fall fortgeschrieben ("v1.4.2 stamps 2, this code stamps 3 after a rebuild", Schritt 7 verlangt 3/3). `test_language_proof_steps.py`: Vorbedingung 3-mal (Schritt 7), Spanisch 0 dreimal, 1 nie, Muster und Selbsttests nachgezogen.
- RED belegt: neue Gates gegen den Workflow von HEAD: 16 failed / 63 passed. GREEN: 86 passed (Verify-Satz), alle 20 Testdateien, die Workflows lesen: 1308 passed, 1 skipped; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün.

## Task 2: deploy-harp-Läufe

**Lauf 38035652649** (6b86643e): rot in Store upgrade 6, nur Assurance 3 und 5. Log:

```
the container was created again at 2026-10-10T08:05:44Z with FINDLING_LANGUAGES=cs,de ...
the rebuild is through after 2 rounds, languagesActive is de,cs
the banner was up in 0 of those rounds, which is the window this reader saw
##[error]the rebuild was never seen running, so the banner of plan 18-10 was never observed up
##[error]no canary was taken inside the run, ...
the reading side searches de,cs and the fields that carry terms are de,cs: no en field is asked or filled
smlouve went from 1 to 1 and proc from 1 to 0 across the rebuild, which is body_cs alone answering
```

Ursache belegt: Der cs-Teil war schon grün; der Bandlauf war vorbei, bevor Nextcloud den neuen Container erreichte. Vergleich Lauf 38033629694 (es,de,en): "caught in the act in round 2", "banner was up in 2 of those rounds". Kettenkosten über den Füllblock gemessen (0.5 MB): de 0.036 s, en 0.018 s, es 0.019 s, cs 0.006 s. de,cs trägt dieselben 32 MB also in gut der Hälfte der Zeit. Fix (21d83c0c): Füllkorpus 64 -> 256 Dokumente (der Workflow nennt ihn selbst "the knob"), Budgetkommentare nachgezogen, Gate pinnt `seq 1 256`. Keine Zusicherung aufgeweicht.

**Lauf 38036946762** (21d83c0c, 08:10:11Z bis 08:28:12Z): **success**.

| Job | Ergebnis | Store upgrade 0-7 |
|---|---|---|
| 114169242139 deploy-harp (stable34, 8.2, ubuntu-24.04) | success | 0, 1, 2, 2b, 3, 3b, 3c, 4, 5, 6, 7 alle success |
| 114169241952 deploy-harp (stable33, 8.2, ubuntu-24.04) | success | skipped (Strecke nur stable34/x86) |
| 114169242120 deploy-harp (stable35, 8.3, ubuntu-24.04) | success | skipped |
| 114169242149 deploy-harp (stable34, 8.2, ubuntu-24.04-arm) | success | skipped |

Store upgrade 2 dauerte 2 min 38 s (08:23:38Z bis 08:26:16Z), 6 dauerte 21 s, 7 dauerte 24 s. Übrige Workflows desselben Commits, alle success: Python gates 38036946775, Integration 38036946693, Resilience 38036946725, Multi-arch image 38036946767, Security scans 38036946776, OpenSSF Scorecard 38036946792.

Logzitate (Job 114169242139):

```
Store upgrade 2:  the fill corpus: 256 files of 500019 characters each
Store upgrade 3:  three terms, one file each; the Spanish question with no hit at all; smlouve and proc one file each; the languages mark de,en
Store upgrade 5:  unchanged  .marks.schemaVersion = 2
                  smlouve and proc answer one document each after the upgrade, as before it
                  all eight assurances hold
Store upgrade 6:  the rebuild was caught in the act in round 2:
                  the rebuild is through after 7 rounds, languagesActive is de,cs
                  the banner was up in 5 of those rounds, which is the window this reader saw
                  the schema mark reads 2 before the rebuild and 3 after it, the schema of the start and of the running code
                  the mark reads de,cs for a set given as cs,de, so the order is the schema's and not the admin's
                  the search for Belehrung answered 1 hit(s) at 0 of 288 documents carried
                  no start_rebuild_on_drift line in 35 lines of container log
                  vectors.db is unchanged at 36dcf137f892daee9d73754eb852c884d34dbe82c2d455497fa9b96e2d622d2f
                  the reading side searches de,cs and the fields that carry terms are de,cs: no en field is asked or filled
                  smlouve went from 1 to 1 and proc from 1 to 0 across the rebuild, which is body_cs alone answering
                  the question alemanes still answers nought, the rebuild filled no chain outside its set
                  all ten assurances hold
Store upgrade 7:  languages mark de,cs at schema 3, no rebuild directory, three terms with one file each, smlouve one and proc nought, a vector stock to compare
                  the rebuild back is through after 14 rounds, languagesActive is de,en
                  the schema mark reads 3 before the way back and 3 after it
                  the languages mark went from de,cs to de,en
                  the reading side searches de,en and the fields that carry terms are de,en: cs is no longer filled
                  smlouve went from 1 to 1 and proc from 0 to 1 across the way back
                  no start_rebuild_on_drift line in 38 lines of container log
                  vectors.db is unchanged at 36dcf137f892daee9d73754eb852c884d34dbe82c2d455497fa9b96e2d622d2f, before the rebuild of Store upgrade 6, before the way back and after it
                  all seven assurances of the way back hold
```

Gesamtkette: Schema 2 -> 3 -> 3, languages de,en -> de,cs -> de,en, smlouve 1/1/1, proc 1/0/1 (mit Release und Upgrade davor 1/1), Vektordigest über beide Umbauten gleich.

## Commits

| Commit | Inhalt |
|---|---|
| 6b86643e | ci(30-07): the upgrade proof switches cs on without en and back |
| 21d83c0c | ci(30-07): four times the fill text keeps the de,cs band run watchable |

## Deviations from Plan

**1. [Rule 1 - Bug] Füllkorpus zu klein für den de,cs-Bandlauf**
- **Found during:** Task 2 (Lauf 38035652649)
- **Issue:** Assurance 3 (Banner beobachtet) und 5 (Kanarienfrage im Lauf) rot, weil der Bandlauf auf de,cs vor dem ersten erreichbaren Überblick endete.
- **Fix:** Füllkorpus 64 -> 256 Dokumente, Begründung mit gemessenen Kettenkosten im Kommentar, Gate-Fall.
- **Files modified:** .github/workflows/deploy-harp.yml, backend/tests/test_upgrade_seed_steps.py
- **Commit:** 21d83c0c

**2. [Rule 2 - Beweisschärfe] "searched languages" direkt an der Lesestelle**
- Der PHP-Überblick reicht `languagesSearched` nicht durch, und `languagesFilled` fragt nur die aktiven Sprachen plus de (würde ein liegengebliebenes body_cs nach dem Rückweg nicht sehen). Deshalb eine Probe im Container (`rebuild-languages.py`): `resources.searched_languages()` und `terms_with_prefix` über alle Körperfelder, ohne except (ein nicht fragbares Feld macht den Schritt rot).

**3. [Rule 3 - Blocker] Gemeinsames Probe-Skript statt zweitem Neustart**
- Schritt 7 braucht denselben Neustart; statt ~130 Zeilen zu duplizieren, stehen Neustart, App-Passwort, Überblickleser, Vektordigest und Sprachprobe in `rebuild-probe.sh` (Muster `upgrade-probe.sh`). Gate verlangt genau ein `docker create`.

**4. Dritte Gate-Datei test_language_proof_steps.py**
- Nicht in `files_modified`, aber zwingend: der Wegfall der Spanisch-1 und die dritte Vorbedingung (Schritt 7) ändern deren Zählungen. Selbsttests und Muster nachgezogen.

**5. Kein separater RED-Commit**
- Wie 30-06: grüne Gates vor jedem Commit verlangt; RED lokal belegt (16 failed).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-30-27: Sprachmenge ohne en, Lesestelle de,cs gesucht und gefüllt, Unterscheider proc 1/0/1. T-30-28: Run-Texte von 6 und 7 ohne `${{` (Gate-Fall). T-30-29: Schema 2 -> 3 erst nach dem Umbau, Sprachmarke je Richtung geprüft. T-30-30: vectors.db-Digest vor 6, vor 7 und nach 7 gleich. Die Container-Probe läuft lesend im CI-Wegwerfcontainer.

## Self-Check: PASSED

- .github/workflows/deploy-harp.yml: `REBUILD_LANGUAGES: 'cs,de'` 1-mal, `      - name: Store upgrade 7` 1-mal, `de,en,es,it,nl,pt` 7-mal wie vor dem Plan
- backend/tests/test_upgrade_seed_steps.py enthält "Store upgrade 7"
- Commits 6b86643e und 21d83c0c auf origin/main
- Lauf 38036946762 success, Store upgrade 0 bis 7 success im Job 114169242139
