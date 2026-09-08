---
phase: 07-gemeinsame-embedding-engine
plan: 03
subsystem: worker
tags: [embeddings, memory, measurement, ci, lazy-load]

# Dependency graph
requires:
  - phase: 07-gemeinsame-embedding-engine
    provides: "07-RESEARCH.md Teil 3.2 und 3.3: die Hypothese ueber Schritt 12 und die 543,7 MB aus 63-grundlast.txt"
  - phase: 07-gemeinsame-embedding-engine
    provides: "Plan 07-02: one_load mit cold_search_ms als siebter Zahl, unveraendert uebernommen"
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: "findling.tools.one_load und seine drei Rotbeweise, embed/engine.py::shared_model"
provides:
  - "docs/measurements/2026-09-grundlast-fein/: die 543,7 MB in fuenf einzeln benannte Posten zerlegt, in einem Container gemessen, amd64 nativ und arm64 emuliert"
  - "Der Entscheid gegen eine vor der Messung festgelegte Schwelle von 100 MB, mit der Zahl im Bericht"
  - "Der faule Bau der zweiten Spur: _wire_the_second_track oeffnet den Vektorbestand, _build_the_cutter baut Tokenizer, Splitter und Engine an der ersten Einbettungszeile"
  - "findling.embed.model.artifacts_present: die Artefaktfrage von aussen stellbar, zwei stats"
  - "measure.yml: ein Messschritt in beiden Matrixaesten, gegen das Abbild, --network none"
  - "deferred-items.md der Phase mit DI-07-04"
affects: [07-04, phase-10-messung, phase-11-audit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Erst messen, dann entscheiden: die Abbruchbedingung steht vor der Messung fest"
    - "Faul laden ist verschieben und nicht sparen, und der Bericht sagt das an beiden Enden"
    - "Eine Haelfte bleibt eifrig, weil ein anderer Pfad ihren Handle braucht (D-21)"
    - "Der neue Zustand heisst 'kann gebaut werden' und nicht 'ist gebaut', damit die Zusage von _embed_ready haelt"
    - "Eine emulierte Messung wird als emuliert bezeichnet und gegen eine native Gegenprobe gehalten"

key-files:
  created:
    - docs/measurements/2026-09-grundlast-fein/README.md
    - docs/measurements/2026-09-grundlast-fein/skripte/01-grundlast-fein.py
    - docs/measurements/2026-09-grundlast-fein/skripte/02-nachmessung-fauler-bau.py
    - docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-amd64.txt
    - docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64.txt
    - docs/measurements/2026-09-grundlast-fein/rohdaten/02-nachmessung-fauler-bau-amd64.txt
    - .planning/phases/07-gemeinsame-embedding-engine/07-03-SUMMARY.md
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/embed/model.py
    - backend/src/findling/tools/one_load.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_embed_engine.py
    - .github/workflows/measure.yml
    - docs/performance.md
    - .planning/phases/07-gemeinsame-embedding-engine/deferred-items.md

key-decisions:
  - "Gebaut, nicht abgebrochen: die realistische Ersparnis ist 544,3 MB auf amd64 gegen eine Schwelle von 100 MB, also das Fuenffache"
  - "Der Vektorbestand bleibt eifrig, weil attach_vectors und der Loeschpfad der Zustandsdatenbank denselben Handle brauchen (D-21)"
  - "Die zwei Tokenizer-Instanzen bleiben getrennt, obwohl die zweite mit 216,6 MB gemessen ist: STATE.md:159 ist eine gesetzte Entscheidung und eine Zahl hebt sie nicht auf"
  - "Die eifrige Haelfte prueft die Artefakte mit zwei stats, damit die Zusage von _embed_ready ohne den 544-MB-Bau haltbar bleibt"
  - "Die arm64-Rohdatei ist emuliert und als solche bezeichnet; der Entscheid haengt an der nativen amd64-Zahl (DI-07-04)"

metrics:
  tasks: 3
  tasks_skipped: 0
  commits: 5
  duration: "rund 2,5 Stunden"
  completed: 2026-09-08
---

# Phase 7 Plan 03: Die Grundlast, ihr Besitzer und der faule Bau, Zusammenfassung

Die 543,7 MB aus zwei groben Messschritten haben Besitzer statt einer Hypothese:
265,8 MB sind die erste Tokenizer-Instanz, 273,5 MB der Bau des Splitters, und
der Rest ist Rundung. Gegen die vor der Messung festgelegte Schwelle von 100 MB
ist der faule Bau freigegeben und gebaut worden; nachgemessen kostet der erste
Durchlauf des Pollers jetzt 0,6 MB statt 575,6 MB.

## Der Entscheid, mit den Zahlen

Die Abbruchbedingung stand vor der Messung fest: unter 100 MB realistischer
Ersparnis wird nicht gebaut, und ein Umbau, der das `one_load`-Tor gefährdet,
wird ebenfalls nicht gebaut. Beide Äste tragen nicht.

| Posten | amd64 (nativ) | arm64 (emuliert) |
|---|---:|---:|
| 11a Modulimport `tokenizers` | 4,2 MB | 6,0 MB |
| 11b erste Tokenizer-Instanz | 265,8 MB | 246,6 MB |
| 12a Bau des Splitters | 273,5 MB | 294,0 MB |
| 12b erster Chunkerlauf | 0,8 MB | 3,5 MB |
| 12c zweiter Chunkerlauf | 0,0 MB | 0,0 MB |
| **Summe, die realistische Ersparnis** | **544,3 MB** | **550,1 MB** |
| Schwelle | 100 MB | 100 MB |

**Ergebnis: gebaut.** Die Ersparnis liegt beim Fünffachen der Schwelle. Task 3
wurde ausgeführt, nichts wurde übersprungen.

Die Hypothese aus `07-RESEARCH.md` ist damit beantwortet und bestätigt: die
274,3 MB des Schritts 12 sind zu 273,5 MB der Bau des Splitters, also eine
zweite Materialisierung desselben Tokenizers auf der Rust-Seite, und nicht der
Preis der Chunkerläufe. Die beiden Chunkerläufe zusammen kosten 0,8 MB.

## Die Nachmessung nach dem Bau

Gemessen auf dem Weg, den der Arbeiter geht, zweimal im selben Abbild:

| Station | eifrig (veröffentlichtes Abbild) | faul (dieser Plan) |
|---|---:|---:|
| 20 zweite Spur verdrahtet, Zuwachs | 575,6 MB | 0,6 MB |
| 21 Schneider gebaut, Zuwachs | 0,0 MB | 575,0 MB |

Die tatsächliche Ersparnis eines Containers, der nur noch sucht, ist **575,0 MB**
gegen eine erwartete von 544,3 MB. Die Abweichung von 30,7 MB steht im Bericht
und ist nicht weggerundet: Skript 01 baut vorher die Wortliste und den deutschen
Automaten, Skript 02 nicht, und die Speicherverwaltung gibt für dieselbe
Anforderung verschieden viel neu an das Betriebssystem zurück.

Der faule Bau senkt nichts, er verschiebt. Ein Container, dessen zweite Spur
läuft, kommt auf dieselbe Zahl wie vorher, nur später. Genau das war der Hebel.

## Was gebaut wurde

`_wire_the_second_track` ist in zwei Hälften geteilt:

- **eifrig:** öffnet den Vektorbestand und prüft mit zwei `stat`-Aufrufen, ob
  die Artefakte im Modellverzeichnis liegen. Der Bestand bleibt hier, weil
  `_open` ihn eine Zeile weiter an `attach_vectors` gibt und der Löschpfad der
  Zustandsdatenbank denselben Handle braucht: ein Grabstein muss die Vektoren
  seiner Datei mitnehmen (D-21).
- **faul:** `_build_the_cutter` baut Tokenizer, Splitter und Engine an der
  ersten Einbettungszeile, in einem Thread, damit der Lesevorgang nicht auf der
  Ereignisschleife der Suche sitzt.

`_embed_ready` sagt seit diesem Plan "kann gebaut werden" statt "ist gebaut".
Die Zusage selbst ist unverändert: der Bestand ist offen oder die Antwort ist
falsch, und das Versprechen über den Schneider wird nur gegeben, nachdem die
eifrige Hälfte die Artefakte gesehen hat. Fällt ein Bau doch aus, senkt er das
Versprechen sofort; die eine Zeile, die dann schon unterwegs war, wird bestätigt
und verlässt die Warteschlange, statt in `failed(repeatedly_stuck)` zu laufen.

Die zwei Tokenizer-Instanzen sind **nicht** zusammengelegt. Der informative
Schritt 16 der Messung beziffert eine zweite Instanz mit 216,6 MB, und diese
Zahl hebt die gesetzte Entscheidung aus `STATE.md:159` nicht auf: eine geteilte
Instanz hätte den 1.024-Token-Deckel aus D-01 still auf 512 halbiert. Beide
Aufrufstellen von `open_tokenizer` stehen unverändert (`embed/model.py:242` für
die Sitzung, `worker/poller.py:1538` für den Schneider), und ein Testfall hält
das als Eigenschaft der Quelle fest.

## Das Tor

`one_load` ist mitgezogen: es fährt jetzt beide Hälften der Verdrahtung, in der
Reihenfolge, in der ein Durchlauf sie fährt. Die vier Zähler und ihre Erwartung
von eins sind unverändert, die drei Rotbeweise sind unangetastet und grün,
`cold_search_ms` aus Plan 07-02 ist unberührt.

Im Abbild gefahren, mit dem geänderten Quellcode hineingereicht:

```
wordlist-reads-after-index=1
wordlist-reads-after-search=1
engine-loads-after-search=1
engine-loads-after-worker=1
candidates=1
passage-vectors=1
verdict=ok
```

## Abweichungen vom Plan

**1. [Rule 3 - blockierend] Der informative Schritt steht am Ende statt zwischen 12c und 13**

- **Gefunden in:** Task 1, beim Aufbau des Skripts.
- **Sache:** Der Plan nennt die zweite Tokenizer-Instanz als sechsten Schritt
  der Zerlegung. Zwischen 12c und 13 gesetzt, hätte sie 216,6 MB zusätzlich
  belegt, bevor die Schritte 13 bis 15 gemessen werden, und genau diese drei
  sollen wortgleich mit der Nachmessung vergleichbar bleiben.
- **Lösung:** Der Schritt heißt `16-zweite-tokenizer-instanz-informativ` und
  steht hinter Schritt 15. Der Docstring des Skripts sagt, warum.
- **Commit:** 4c65d8c

**2. [Rule 3 - blockierend] Die arm64-Rohdatei ist emuliert, nicht nativ**

- **Gefunden in:** Task 1, beim Fahren der Messung.
- **Sache:** Ein Lauf von `measure.yml` auf `ubuntu-24.04-arm` braucht einen
  `workflow_dispatch`, und der Zweig steht noch nicht auf `main`; der Executor
  pusht nicht. Die AWS-Box ist angehalten und wurde nicht angefahren.
- **Lösung:** Der Messschritt in `measure.yml` ist gebaut und läuft in beiden
  Matrixästen aus derselben Skriptdatei. Die arm64-Rohdatei dieses Plans ist
  unter QEMU gemessen, im Kopf der Datei und in Abschnitt 1 des Berichts als
  emuliert bezeichnet und gegen die native grobe Messung aus
  `63-grundlast.txt` gehalten: Abweichung 6,4 MB auf 543,7 MB, also 1,2 Prozent.
  Der Entscheid hängt nicht daran, er fällt gegen die native amd64-Zahl.
  Abgelegt als **DI-07-04**.
- **Commit:** 4c65d8c, a35eb4c

**3. [Rule 2 - fehlende Zusage] `embed/model.py` bekommt `artifacts_present`**

- **Gefunden in:** Task 3, beim Bau der eifrigen Hälfte.
- **Sache:** Mit dem faulen Bau ist "der Schneider steht" kein Beleg mehr dafür,
  dass er gebaut werden kann. Ohne eine billige Artefaktfrage hätte
  `_embed_ready` auf einem Container ohne Modell eine Zeile herausgegeben, die
  nicht bearbeitet werden kann. Die Frage gab es nur als privates
  `_artifacts_present`, und zwei Testsuiten zählen Aufrufe darüber.
- **Lösung:** Eine öffentliche `artifacts_present`, die an die private
  delegiert, damit die beiden Suiten dieselben Aufrufe zählen wie vorher. Die
  Datei stand nicht in `files_modified` des Plans.
- **Commit:** 6dcc0d1

**4. [Rule 1 - Folgefehler] `tests/test_embed_engine.py` musste mitgezogen werden**

- **Gefunden in:** Task 3, im GREEN-Lauf.
- **Sache:** `test_the_second_track_and_the_read_side_wire_the_same_object`
  ruft `_wire_the_second_track()` und liest danach `worker._model`. Mit dem
  faulen Bau ist das None, und der Test wurde rot, ohne dass EFF-01 verletzt
  wäre.
- **Lösung:** Der Test fährt beide Hälften, wie `one_load` es tut. Die Aussage
  des Tests ist unverändert: die zwei Aufrufer enden an einem Objekt.
- **Commit:** 6dcc0d1

**5. [Rule 2 - fehlende Zusage] Ein zweites Messskript für die Nachmessung**

- **Gefunden in:** Task 3, beim Nachmessen.
- **Sache:** Das Skript aus Task 1 ruft `open_tokenizer` und `make_splitter`
  selbst auf. Es misst den Preis der Posten und nicht die Entscheidung darüber,
  wann er anfällt, kann die Ersparnis also nicht zeigen.
- **Lösung:** `02-nachmessung-fauler-bau.py` geht den Weg des Arbeiters und
  läuft zweimal im selben Abbild, gegen den veröffentlichten und gegen den
  geänderten Quellcode. Skript 01 bleibt unverändert und damit vergleichbar.
- **Commit:** 89cb0f3

## TDD-Tore

| Tor | Commit | Nachweis |
|---|---|---|
| RED | 2616d95 | 7 von 8 neuen Fällen rot, mit den erwarteten Meldungen |
| GREEN | 6dcc0d1 | 180 Fälle der vier betroffenen Suiten grün |
| REFACTOR | entfällt | keine Umbauten ohne Verhaltensänderung nötig |

Ein neuer Fall war in der RED-Phase grün:
`test_the_two_tokenizer_instances_are_not_merged`. Das ist beabsichtigt und kein
übersprungenes Tor: er hält eine gesetzte Entscheidung fest, die vor und nach
diesem Plan gilt, und er wäre rot geworden, wenn der Bau sie angetastet hätte.

## Gate-Ergebnisse

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün, 116 Dateien |
| `uv run pytest -q` | 1.681 grün, 15 übersprungen |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | grün |
| `python -m findling.tools.one_load` im Abbild | verdict=ok, vier Zähler auf eins |
| `test_workflow_pins.py`, `test_ops_scripts.py` | 60 grün |

## Was offen bleibt

- **DI-07-04:** die native arm64-Rohdatei kommt aus dem ersten
  `workflow_dispatch` von `measure.yml` nach dem Zusammenfügen. Der Schritt
  heißt "D, the base load step by step" und liegt in beiden Matrixästen.
- **Der Budgetposten in `CLAUDE.md`:** die Tabelle kennt "Tokenizer und
  Splitter" nicht, obwohl der Posten gemessen größer ist als das Modell.
  `docs/performance.md` nennt das ausdrücklich; ob die Tabelle nachgezogen wird,
  entscheidet der Owner. Der Plan hat `CLAUDE.md` nicht angefasst.
- `.planning/STATE.md` und `.planning/ROADMAP.md` sind unverändert, wie vom
  Plan gefordert. Es wurde nicht gepusht, und die AWS-Box wurde nicht angefahren.

## Self-Check: PASSED

Alle in dieser Zusammenfassung genannten Dateien liegen im Arbeitsbaum, alle
fuenf Commit-Kuerzel stehen in der Historie des Zweigs `exec/07-03`.
