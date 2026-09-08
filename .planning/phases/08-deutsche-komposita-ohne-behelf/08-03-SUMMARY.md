---
phase: 08-deutsche-komposita-ohne-behelf
plan: 03
subsystem: infra
tags: [ci, docker, licence, gpl-2, wngerman, wordlist, reindex, status-endpoint, pytest]

requires:
  - phase: 08-deutsche-komposita-ohne-behelf
    provides: "Messgrundlage Rezept A, gemessene Kennzahlen der Liste (356010 Quellzeilen, Paket wngerman=20161207-15)"
provides:
  - "CI-Schritt im Abbildbau, der Paketfassung, Zeilenzahl, Byteanzahl, Lizenztext und dessen Modus im veroeffentlichten Abbild prueft"
  - "Ende-zu-Ende-Test des Variantenwechsels FINDLING_COMPOUND_DICT von der Umgebungsvariablen bis zu reindexRequired auf der Statusseite"
  - "Belegte Aussage in THIRD-PARTY.md, dass die erste Handpruefung jetzt maschinell mitfaehrt"
affects: [store-abgabe, launch-haertung, lizenz-audit, wortlisten-wechsel]

tech-stack:
  added: []
  patterns:
    - "Artefaktpruefung statt Bauplanpruefung: Lizenz- und Datenpflichten werden gegen ${IMAGE}@${DIGEST} geprueft, nicht gegen das Dockerfile"
    - "Gemessene statt geratene Pruefzeichenketten: jede Zeichenkette im CI-Schritt traegt das Datum ihrer Messung im Kommentar"

key-files:
  created: []
  modified:
    - .github/workflows/docker.yml
    - THIRD-PARTY.md
    - backend/tests/test_status_endpoint.py

key-decisions:
  - "Die Lizenz-Zeichenketten (Upstream-Name: igerman98, License: GPL-2+) wurden am 08.09.2026 in einem Container aus der apt-Zeile des Dockerfiles gemessen, nicht geraten"
  - "wordlistHash bleibt die Marke des bestehenden Index und wird nicht auf die eingestellte Variante umgestellt; die Abweichung meldet reindexRequired (Abweichung von der Planvorgabe, kein Produktionspfad geaendert)"
  - "Der Ende-zu-Ende-Test behauptet zusaetzlich, dass die neue Variante auf einer eigenen Datei landet, weil er sonst aus dem falschen Grund gruen ist"

patterns-established:
  - "Vier Pruefungen, vier Fehlermeldungen: ein CI-Schritt sagt beim Rotwerden, welches der vier verschiedenen Dinge kaputt ist"
  - "Rotbeweis per Mutation: eine Zeile entfernen und den Test laufen lassen, bevor er als Beleg gilt"

requirements-completed: [QUAL-01]

duration: 42min
completed: 2026-09-08
---

# Phase 8 Plan 03: Lizenz- und Variantenbeleg Summary

**Aus zwei "sieht richtig aus" sind zwei rotwerdende Pruefungen geworden: das veroeffentlichte Abbild wird auf Wortlistenfassung und GPL-2+-Text geprueft, und ein Wechsel von FINDLING_COMPOUND_DICT ist bis zur Statusseite belegt.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-09-08T17:20:00Z
- **Completed:** 2026-09-08T18:02:00Z
- **Tasks:** 2 von 2
- **Files modified:** 3

## Accomplishments

- Erfolgskriterium 3 ist maschinell geprueft: der neue Schritt "The word list, its version and its licence in this image" laeuft in beiden Matrixaesten gegen den gepushten Digest und faellt bei falscher Paketfassung, veraenderter Liste, fehlendem Lizenztext oder beschreibbar gewordenem Lizenztext um.
- Alle vier Pruefungen sind lokal gefahren, gruen und einzeln rot bewiesen (siehe Trockenlauf unten). Kein offener Punkt fuer den ersten CI-Lauf auf main.
- Erfolgskriterium 4 ist Ende zu Ende belegt: der neue Test schaltet die Umgebungsvariable um und liest die Statusseite, statt eine Marke von Hand zu verbiegen.
- Der Test unterscheidet die echte Drift von der Ersatzantwort UNPROVEN_WORDLIST, was der vorhandene Drifttest nicht tut.

## Task Commits

1. **Task 1: Die Wortliste und ihre Lizenz im veroeffentlichten Abbild pruefen** - `1626c30` (ci)
2. **Task 2: Der Variantenwechsel, Ende zu Ende bis zur Statusseite** - `bc280d3` (test)

## Files Created/Modified

- `.github/workflows/docker.yml` - neuer Schritt hinter "Answer A12 and A13 inside this image", im Job, der `steps.push.outputs.digest` kennt. Prueft mit `docker run --rm --network none --entrypoint sh` gegen `${IMAGE}@${DIGEST}`: Paketfassung `20161207-15`, `356010` Zeilen und `4725887` Bytes von `/usr/share/dict/ngerman`, Anwesenheit und Inhalt von `/usr/local/share/findling/COPYING.wngerman`, Modus `0444`.
- `THIRD-PARTY.md` - im Abschnitt "How to check this file against reality" steht jetzt ueber dem ersten Codeblock, dass diese Handpruefung als benannter Schritt bei jedem Abbildbau mitfaehrt; die Handfassung bleibt fuer Leser stehen.
- `backend/tests/test_status_endpoint.py` - `test_switching_the_dictionary_variant_asks_for_a_reindex` hinter dem vorhandenen Drifttest, plus die Konstantenliste `NOUNS_CONSTITUENTS` und vier Importe.

## Trockenlauf des Abbildschritts (Task 1)

Ein vollstaendiger Abbildbau war nicht noetig und waere fuer diese Frage auch der falsche Aufwand gewesen: die Wortliste kommt aus genau einer `RUN`-Zeile des Dockerfiles. Gefahren wurde daher ein Container aus dem im Dockerfile gepinnten Basisabbild (`python:3.13-slim-trixie@sha256:ffb752e1...c6e30a`) mit derselben apt-Zeile und derselben `install -D -m 0444`-Zeile. Das Skript des neuen Schritts wurde aus `docker.yml` per YAML-Parser herausgeloest und woertlich gegen diesen Container gefahren.

**Gruen, gemessen am 08.09.2026:**

```
wngerman version 20161207-15
ngerman 356010 lines, 4725887 bytes
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: igerman98
Source: https://www.j3e.de/ispell/igerman98/dict/

Files: *
Copyright: 1999-2016 Bjoern Jacke <bjoern@j3e.de>
License: GPL-2+
licence mode 444
```

**Rot, jede Pruefung einzeln:**

| Pruefung | Eingriff | Ergebnis |
|---|---|---|
| 1 Paketfassung | erwartete Fassung auf `29991207-99` gesetzt | Exit 1, "the word list package is 20161207-15 and not the pinned 29991207-99" |
| 2 Zeilen und Bytes | `truncate -s 4725886` auf die Liste | Exit 1, "the word list is 356009 lines and 4725886 bytes" |
| 3 Lizenztext | Datei geloescht | Exit 1, "the GPL-2+ licence text is missing from ..." |
| 4 Modus | `chmod 0644` auf die Datei | Exit 1, "the licence text is mode 644 and not 0444, so something made it writable" |

Der Probe-Container und die Trockenlauf-Dateien wurden nach der Messung entfernt; nichts davon ist committet. Die beiden `grep`-Zeichenketten stehen mit dem Messdatum als Kommentar im Schritt.

## Rotbeweis des Ende-zu-Ende-Tests (Task 2)

Zwei Mutationen, beide gefahren:

1. **Ohne `monkeypatch.setenv("FINDLING_COMPOUND_DICT", "nouns")`:** `assert artifact != full_artifact` faellt. Beide Pfade sind dann `dict/de-full.txt`.
2. **Ohne `monkeypatch.setattr(resources, "_MARKS", None)`:** `assert answer["reindexRequired"] is True` faellt mit `assert False is True`. Der Prozess-Cache der Marken ist auf `dict_dir` geschluesselt, und die bewegt sich beim Variantenwechsel nicht.

Beide Zeilen sind danach wieder eingesetzt, der Test ist gruen.

## Decisions Made

- **Die Lizenzpruefung greift zwei Zeilen des Debian-Copyright-Formats:** `Upstream-Name: igerman98` (Zeile 2) und `License: GPL-2+` (Zeile 7). Beide wurden am 08.09.2026 mit `head -20` im gebauten Container gelesen. Ein blosses `test -s` haette eine beliebige nichtleere Datei durchgelassen.
- **Der Schritt laeuft mit `--network none`,** wie die drei Proben davor. Er braucht nichts von aussen und darf nichts nach aussen.
- **`stat -c %a` statt `ls -l`,** weil ein Zahlenvergleich weniger von der Ausgabeform des Werkzeugs abhaengt. Die Fehlermeldung nennt trotzdem `0444`, weil das die Schreibweise der `install`-Zeile im Dockerfile ist.

## Deviations from Plan

### 1. [Planvorgabe korrigiert] `wordlistHash` traegt den Digest des Index, nicht den der eingestellten Variante

- **Found during:** Task 2
- **Issue:** Der Plan verlangt im `<behavior>`-Block, dass `wordlistHash` nach dem Wechsel "den Digest der neu eingestellten Variante und nicht den des Index" traegt. Der Code liefert das Gegenteil: `backend/src/findling/api/status.py:334` setzt `wordlistHash=marks.get("wordlist_hash", "")` aus `store.read_meta()`, also aus den Marken, die der **bestehende Index** traegt.
- **Bewertung:** Das ist kein Fehler im Produktionscode. Das Feld steht neben `indexVersion` und `analyzerVersion`, und die Datei sagt ueber diese Gruppe ausdruecklich, sie sage "how the index was built" (`test_the_app_version_is_not_derived_from_the_index_marks`). Der Widerspruch zwischen Index und Einstellung ist genau das, wofuer `reindexRequired` da ist. Eine Umstellung waere ein zweiter Produktionspfad gewesen, den der Plan im Task ausdruecklich verbietet.
- **Fix:** Der Test behauptet stattdessen beide Seiten und macht den Unterschied zur Aussage: `answer["wordlistHash"] == indexed_volume.digest` und `answer["wordlistHash"] != nouns_digest`. Die Akzeptanzbedingung bleibt erfuellt, beide Digests sind im Test berechnet und keiner ist eine hart geschriebene Zeichenkette.
- **Files modified:** `backend/tests/test_status_endpoint.py`
- **Committed in:** `bc280d3`

### 2. [Rule 2 - fehlende kritische Absicherung] Der Test war zunaechst aus dem falschen Grund gruen

- **Found during:** Task 2, beim vom Plan geforderten Rotbeweis
- **Issue:** In der ersten Fassung genau nach Planablauf blieb der Test auch ohne den Variantenwechsel gruen. Grund: ohne gesetzte Umgebungsvariable zeigt `artifact_path()` auf dieselbe Datei, die die Fixture geschrieben hat, das Schreiben der neuen Konstituenten ueberschrieb also die Liste, mit der der Index gebaut wurde. Gemessen wurde damit die Drift einer **bearbeiteten Datei**, nicht die eines **umgeschalteten Schalters**. Genau der Fehler, gegen den der Test antritt.
- **Fix:** Zwei Behauptungen ergaenzt: `assert artifact != artifact_path("full")` vor dem Schreiben, und nach dem Schreiben, dass die Digestdatei der Variante `full` noch den Fixture-Digest traegt. Damit faellt der Test ohne den Wechsel sofort.
- **Verification:** Rotbeweis 1 oben, danach gruen.
- **Files modified:** `backend/tests/test_status_endpoint.py`
- **Committed in:** `bc280d3`

---

**Total deviations:** 2 (1 Planvorgabe korrigiert ohne Produktionsaenderung, 1 Rule 2)
**Impact on plan:** Kein Scope-Zuwachs. Beide Abweichungen betreffen nur die Testdatei und machen den Beleg schaerfer, statt ihn zu erweitern.

## Issues Encountered

- **Kein voller Abbildbau moeglich beziehungsweise sinnvoll:** Das echte Abbild zieht ein 470-MB-Modell und quantisiert es. Fuer die Frage dieses Plans genuegt und traegt der Nachbau der einen `RUN`-Zeile auf demselben gepinnten Basisabbild. Das ist oben dokumentiert; es bleibt **kein** offener Punkt fuer den ersten CI-Lauf, weil alle vier Pruefungen gruen und rot gefahren wurden.

## TDD Gate Compliance

Task 2 traegt `tdd="true"`, aber die geprueften Verhalten sind bereits gebaut (Recherche A4). Es gibt daher einen `test(...)`-Commit und keinen `feat(...)`-Commit: es wurde kein Produktionsverhalten hinzugefuegt, und der Plan verbietet fuer diesen Zweck ausdruecklich einen zweiten Produktionspfad. Der RED-Zustand ist stattdessen per Mutation belegt (zwei Faelle, siehe oben), was fuer einen nachtraeglichen Beleg die schaerfere Form ist: er zeigt, dass der Test die Ursache und nicht nur die Wirkung misst.

## Verification

| Gate | Ergebnis |
|---|---|
| `cd backend && uv run pytest -q` | 1714 passed, 15 skipped |
| `uv run pytest -q tests/test_status_endpoint.py` | 35 passed |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 116 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | keine Befunde |
| `docker.yml` parst als YAML | ja, `yaml.safe_load` gruen |
| Literale im Schritt | `COPYING.wngerman` 1x, `20161207-15`, `356010`, `4725887`, `0444` vorhanden |

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche. Die vier Dispositionen `mitigate` des Bedrohungsregisters (T-08-08, T-08-09, T-08-10) sind umgesetzt, T-08-11 bleibt `accept`: der Schritt gibt Zahlen und sieben Zeilen Lizenzkopf aus, keinen Nutzerinhalt, und laeuft mit `--network none`. T-08-SC ist eingehalten, kein neues Paket, der vorhandene Pin wird zusaetzlich geprueft statt neu gesetzt.

## User Setup Required

Keine.

## Next Phase Readiness

- Der neue CI-Schritt laeuft beim naechsten Push auf `main` das erste Mal echt. Faellt er dort, ist die Aussage eine echte: die vier Werte sind gegen ein Abbild aus derselben apt-Zeile gemessen.
- Fuer die Launch-Haertung vor der Store-Abgabe ist der Lizenzpunkt damit vom "haben wir nachgesehen" zum "faellt auf, wenn es fehlt" geworden.
- Offen bleibt nur, was dieser Plan nie versprochen hat: Erfolgskriterium 1 und 2 der Phase liegen bei den anderen Wellen.

## Self-Check: PASSED

- `.github/workflows/docker.yml` geaendert und committet: gefunden
- `THIRD-PARTY.md` geaendert und committet: gefunden
- `backend/tests/test_status_endpoint.py` geaendert und committet: gefunden
- Commit `1626c30`: gefunden
- Commit `bc280d3`: gefunden

---
*Phase: 08-deutsche-komposita-ohne-behelf*
*Completed: 2026-09-08*
