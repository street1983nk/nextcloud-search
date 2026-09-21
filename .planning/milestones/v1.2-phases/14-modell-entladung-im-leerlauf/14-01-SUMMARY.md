---
phase: 14-modell-entladung-im-leerlauf
plan: 01
subsystem: testing
tags: [measurement, rss, malloc_trim, glibc, onnxruntime, tokenizers, github-actions, aarch64]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: embed/model.py mit open_tokenizer, _open_session, THREADS und MODEL_FILE
  - phase: 07-indexlauf
    provides: fauler Bau von Tokenizer und Splitter im Poller, auf den sich die Messgroesse bezieht
  - phase: 10-messbox
    provides: measure.yml als dispatch-only Messwerkstatt mit arm64-Ast und Digest-Aufloesung
provides:
  - Messverzeichnis docs/measurements/2026-09-entladung-vorpruefung/
  - Erwartung E1 bis E4 mit Zahlen, geschrieben vor jeder Messung
  - Messskript 01-rss-rueckgabe.py, vier Marken je Zyklus, fuenf Zyklen, trim_rc
  - Schritt E in measure.yml auf beiden Matrixaesten
affects: [14-02-vorprueflauf, 14-entladefunktion, 15-boxmessung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messerwartung vor dem Lauf: Schwelle im Ablaufdokument, nicht im Bericht"
    - "Eingehaengtes Messskript gegen das ausgelieferte Abbild statt eines neuen Bench-Modus"

key-files:
  created:
    - docs/measurements/2026-09-entladung-vorpruefung/skripte/00-ablauf.md
    - docs/measurements/2026-09-entladung-vorpruefung/skripte/01-rss-rueckgabe.py
  modified:
    - .github/workflows/measure.yml

key-decisions:
  - "Die Schwelle E1 steht bei 60 Prozent Median-Rueckgabe, hergeleitet aus 97,2 Prozent nativ x86_64 und 71,4 Prozent unter qemu"
  - "Der Vorprueflauf ist ein eingehaengtes Messskript und kein vierter Bench-Modus, weil er gegen das ausgelieferte Abbild laufen muss, bevor Produktcode entsteht"
  - "Der neue Workflow-Schritt heisst E und nicht D, weil D die Grundlast ist und unter diesem Buchstaben bereits zitiert wird"
  - "zyklus() gibt eine benannte Tupelstruktur zurueck statt list[str], damit Median und E4-Differenz ohne Rueckparsen der eigenen Ausgabe entstehen"

patterns-established:
  - "Messgroesse rueckgabe_prozent = (loaded - after_trim) / (loaded - baseline) * 100, nie Grundlast minus X"
  - "malloc_trim-Rueckgabewert gehoert als trim_rc in jede Messzeile, eine Prozentzahl ohne ihn ist kein Beleg"

requirements-completed: []
# MEM-04 steht in der Frontmatter dieses Plans, ist aber mit ihm NICHT erfuellt:
# der Plan baut das Werkzeug und schreibt die Erwartung, er erhebt keine Zahl.
# MEM-04 verlangt den Beleg auf Zielhardware und wird in 14-02 abgehakt.
requirements-advanced: [MEM-04]

# Metrics
duration: 38min
completed: 2026-09-19
---

# Phase 14 Plan 01: Werkzeug und Erwartung des Entladungs-Vorprueflaufs Summary

**Messverzeichnis, Schwelle E1 bis E4 und ein eingehaengtes Messskript, das vier RSS-Marken je Zyklus plus den Rueckgabewert von malloc_trim erhebt, gefahren aus dem neuen Schritt E von measure.yml gegen das ausgelieferte Abbild.**

## Performance

- **Duration:** 38 min
- **Started:** 2026-09-19T12:06:00Z
- **Completed:** 2026-09-19T12:45:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 neu, 1 geaendert)

## Accomplishments

- Die Messerwartung steht schriftlich und datiert fest, bevor eine einzige Zahl erhoben ist: E1 (Median mindestens 60 Prozent auf dem `role: target`-Ast), E2 (`trim_rc` in vier von fuenf Zyklen 1), E3 (`after_gc` deutlich ueber `after_trim`), E4 (Zyklus 5 hoechstens 10 Prozentpunkte unter Zyklus 1). Dazu drei benannte Ausgaenge samt dem Wortlaut "gemessen, Ergebnis negativ" fuer den legitimen negativen Ausgang.
- Das Messskript erhebt je Zyklus `baseline`, `loaded`, `after_gc` und `after_trim` aus `/proc/self/status` und druckt `trim_rc` daneben. Es laeuft gegen das ausgelieferte Abbild, ohne dass dafuer ein neues Abbild gebaut werden muss, und es druckt `median_rueckgabe_prozent` und `zyklus1_minus_zyklus5_punkte`, damit E1 und E4 ohne Nachrechnen ablesbar sind.
- `measure.yml` faehrt den Lauf als Schritt E auf `ubuntu-24.04-arm` (role target) und `ubuntu-24.04` (role comparison), schreibgeschuetzt eingehaengt, mit `--network none` und `--cpuset-cpus 0,1`, ohne `--privileged` und ohne `--user 0`.
- Kein Produktcode veraendert, keine neue Abhaengigkeit, keine neue Action: `git diff --name-only HEAD~3 HEAD` nennt genau die drei Dateien der Frontmatter.

## Task Commits

Each task was committed atomically:

1. **Task 1: Messverzeichnis und die Erwartung vor dem Lauf** - `6387d2d` (docs)
2. **Task 2: Das Messskript, vier Marken je Zyklus** - `1723447` (feat)
3. **Task 3: Schritt E in measure.yml** - `f38917b` (ci)

## Files Created/Modified

- `docs/measurements/2026-09-entladung-vorpruefung/skripte/00-ablauf.md` - Ablaufplan des Vorprueflaufs: Frage und Geltung, die vier Marken, die Messgroesse, die Erwartung E1 bis E4 mit Zahlen, drei Ausgaenge, Vergleichbarkeitsbedingungen und der ausdrueckliche Ausschluss der Ladezeit.
- `docs/measurements/2026-09-entladung-vorpruefung/skripte/01-rss-rueckgabe.py` - Das Messskript: Kopfzeilen aus den drei `FINDLING_MEASURE_*`-Variablen, ein Zyklus aus Tokenizer, Splitter, Encoder, Sitzung und einem `session.run`, dann Loslassen, `gc.collect()`, `malloc_trim(0)`; `--cycles` mit Vorgabe 5.
- `.github/workflows/measure.yml` - Neuer Schritt `E, RSS returned by a release` zwischen Schritt D und der Artefaktabgabe, mit Kommentarblock in Laenge und Tonlage der vier anderen Messschritte.

## Decisions Made

- **Schwelle E1 bei 60 Prozent.** Hergeleitet und im Dokument begruendet: nativ x86_64 wurden in der Vorrecherche 97,2 Prozent gemessen, die qemu-Gegenprobe kommt trotz Emulationsaufschlag auf 71,4 Prozent. 60 ist der Boden, unter dem die Funktion ihren Preis nicht wert ist. Die Zahl steht vor dem Lauf fest, weil eine nachtraeglich gesetzte Schwelle keine ist (14-RESEARCH.md, offene Frage 5).
- **Nenner `loaded - baseline` statt `loaded`.** Der Import-Bodensatz von onnxruntime und numpy kann nicht zurueckkommen, weil die Module geladen bleiben. Ein Nenner, der ihn mittraegt, waere systematisch zu niedrig.
- **Die Sitzungsoptionen werden im Skript wiederholt und nicht importiert.** `_open_session` ist privat. Ein Messskript, das in private Namen greift, bricht beim naechsten Umbau still; ein Messskript, das einen Namen oeffentlich machen laesst, aendert das Erzeugnis wegen einer Messung. Drei wiederholte Zeilen unter der Aufsicht eines Kommentars sind der kleinere Preis.
- **Zwei Tokenizer-Instanzen im Zyklus.** Der schlichte fuer den Splitter, der truncierte und gepaddete fuer die Sitzung. Das ist die verriegelte Entscheidung des Projekts und hier zusaetzlich die Messwahrheit, weil der Container im Betrieb beide haelt.

## Deviations from Plan

Keine Abweichung nach den Regeln 1 bis 4. Zwei Abweichungen im Bauwerk des Skripts, beide klein und beide unten begruendet.

**1. [Bauform] `zyklus()` gibt `Messung` statt `list[str]` zurueck**
- **Found during:** Task 2
- **Issue:** Der Plan gibt die Signatur `def zyklus(nummer, model_dir, s) -> list[str]` vor. `main()` braucht aber `median_rueckgabe_prozent` und die Differenz zwischen Zyklus 1 und Zyklus 5, also die Zahlen selbst; mit `list[str]` haette `main()` die eigene Ausgabe zurueckparsen muessen.
- **Fix:** Ein `NamedTuple` mit den vier Marken, `trim_rc`, der Eigenschaft `rueckgabe_prozent` und der Methode `zeile()`. Die gedruckte Zeile ist unveraendert die des Plans, mit allen sieben Feldern in der vorgegebenen Reihenfolge.
- **Files modified:** docs/measurements/2026-09-entladung-vorpruefung/skripte/01-rss-rueckgabe.py
- **Verification:** Probelauf `--cycles 1` druckt `zyklus=1 baseline_kb=... rueckgabe_prozent=98.4`, danach `median_rueckgabe_prozent` und `zyklus1_minus_zyklus5_punkte`.
- **Committed in:** `1723447`

**2. [Bauform] `del` statt Zuweisung von `None` beim Loslassen**
- **Found during:** Task 2
- **Issue:** Der Plan verlangt, alle Halter auf `None` zu setzen. Eine Zuweisung an einen Namen, der danach nie mehr gelesen wird, ist eine tote Zuweisung und wird von ruff zu Recht als F841 gemeldet.
- **Fix:** Ein `del` ueber alle sechs Halter (beide Tokenizer, Splitter, Stuecke, Sitzung, Ergebnis des Laufs). Die Wirkung auf den Referenzzaehler ist dieselbe; ein Kommentar an der Stelle sagt, warum.
- **Files modified:** docs/measurements/2026-09-entladung-vorpruefung/skripte/01-rss-rueckgabe.py
- **Verification:** `ruff check` und `ruff format --check` mit der Projektkonfiguration gruen; der Probelauf zeigt `after_trim_kb` weit unter `after_gc_kb`, das Loslassen wirkt also.
- **Committed in:** `1723447`

---

**3. [Rule 1 - Bug] MEM-04 wurde NICHT als erfuellt eingetragen**
- **Found during:** Zustandspflege nach Task 3
- **Issue:** Die Frontmatter des Plans traegt `requirements: [MEM-04]`, und der Zustandsbefehl hat MEM-04 daraufhin in `.planning/REQUIREMENTS.md` abgehakt. MEM-04 verlangt aber den Beleg der RSS-Rueckgabe auf Zielhardware; dieser Plan erhebt keine einzige Zahl. Ein abgehaktes MEM-04 haette eine Messung behauptet, die es nicht gibt, und genau das ist der Fehler, gegen den die Anforderung geschrieben ist.
- **Fix:** Der Haken und die Zeile der Rueckverfolgungstabelle sind zurueckgenommen; MEM-04 steht wieder auf Pending. Die Frontmatter dieser Zusammenfassung fuehrt MEM-04 unter `requirements-advanced` statt unter `requirements-completed`, mit der Begruendung im Kommentar.
- **Files modified:** .planning/REQUIREMENTS.md (netto unveraendert), .planning/phases/14-modell-entladung-im-leerlauf/14-01-SUMMARY.md
- **Verification:** `git diff .planning/REQUIREMENTS.md` ist leer; MEM-04 steht in beiden Stellen der Datei auf Pending.
- **Committed in:** der Metadaten-Commit dieses Plans

---

**Total deviations:** 2 Bauform-Abweichungen und 1 Korrektur nach Regel 1, 0 architektonische.
**Impact on plan:** Kein Zuwachs am Umfang. Die Ausgabe, die Schnittstelle zur Werkstatt und die vier Marken sind genau die des Plans.

## Issues Encountered

- **Der lokale Probelauf laedt mehr als die Vorrecherche.** `loaded_kb=1080728` gegen die 475,9 MB aus 14-RESEARCH.md 3.2. Ursache ist kein Fehler, sondern der Batch: die Recherche hat mit einem kleinen Einzeltext gemessen, dieses Skript schickt acht Stuecke zu 510 Token durch den Graphen, also den Aktivierungsspeicher eines echten Batches. Das ist gewollt, weil der Aktivierungsspeicher der groesste Einzelposten der Entladung ist. Die Folge fuer den Bericht: die `loaded`-Zahlen dieses Laufs sind nicht die der Recherche und duerfen nicht nebeneinander gestellt werden; vergleichbar ist `rueckgabe_prozent`.
- **onnxruntime schreibt beim Start eine Warnzeile auf die Standardfehlerausgabe** ("Failed to persist telemetry device ID"). Sie ist eine Eigenschaft des Abbilds, geht nicht durch die `tee`-Pipeline in die Rohdatei und verlaesst den Container nicht: der Schritt faehrt mit `--network none`.
- **Ein Heredoc mit dem vollstaendigen Ablauftext war in dieser Shell nicht schreibbar** (Parse-Abbruch). Die Datei ist stattdessen direkt geschrieben worden; kein Einfluss auf den Inhalt.

## Verification

- `cd backend && uv run pytest tests/test_measurement_scripts.py -q`: 230 passed. Die neue Datei ist in der weiten Menge (kein Carriage Return, kein U+2014, kein U+2013).
- `cd backend && uv run pytest -q`: 2132 passed, 15 skipped, einmal nach Task 2 und einmal nach Task 3.
- `cd backend && uv run pytest tests/test_workflow_pins.py -q`: 14 passed, keine neue Action.
- `ruff check` und `ruff format --check` mit `backend/pyproject.toml` ueber das neue Skript: gruen.
- Probelauf im ausgelieferten Abbild, `--cycles 1`, Exit 0: `baseline_kb=56356 loaded_kb=1080728 after_gc_kb=878916 after_trim_kb=73136 trim_rc=1 rueckgabe_prozent=98.4`. Das ist ein amd64-Rauchtest der Mechanik und **nicht** der Vorprueflauf; die Zahl, an der die Phase haengt, kommt vom `role: target`-Ast.
- `measure.yml` parst als YAML, traegt `E, RSS returned by a release` genau einmal, hinter Schritt D und vor der Artefaktabgabe, mit `--network none` und `--cpuset-cpus 0,1` und ohne `--privileged` und `--user 0`.
- `git diff --name-only HEAD~3 HEAD` nennt ausschliesslich die drei Dateien der Frontmatter.

## Known Stubs

Keine. Dieser Plan liefert ein Messwerkzeug und ein Dokument; beide sind vollstaendig.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers des Plans. Die drei
mitigierten Punkte sind umgesetzt: fester Bibliotheksname `libc.so.6` im Code
(T-14-01), Ausgabe nur aus Zahlen und Kopfzeilen (T-14-02), keine neue Action
und keine neuen Rechte im Workflow-Schritt (T-14-03).

## User Setup Required

Keine. Der Lauf ist ein `workflow_dispatch` von `measure.yml` und braucht weder
eine gemietete Box noch ein Geheimnis ueber den bereits vorhandenen,
lesebeschraenkten `GITHUB_TOKEN` hinaus.

## Next Phase Readiness

- Wave 2 (Plan 14-02) kann den Lauf ausloesen: `measure.yml` per `workflow_dispatch` mit `image_ref: dev`, danach das Artefakt `welle0-arm64` holen, `rss-rueckgabe-arm64.txt` und `machine.txt` nach `docs/measurements/2026-09-entladung-vorpruefung/rohdaten/` legen und den Bericht gegen E1 bis E4 schreiben.
- Offen und bewusst offen: es ist noch keine Zahl auf Zielarchitektur erhoben. Erfolgskriterium 1 der Phase ist erst mit dem Bericht aus 14-02 erfuellt, nicht mit diesem Plan.
- Der negative Ausgang bleibt moeglich. Faellt E1, endet die Phase mit "gemessen, Ergebnis negativ" und ohne Produktcode; die folgenden Plaene duerfen davor nicht gebaut werden.

---
*Phase: 14-modell-entladung-im-leerlauf*
*Completed: 2026-09-19*

## Self-Check: PASSED

Alle drei Dateien der Frontmatter liegen unter den genannten Pfaden, alle drei
Task-Commits sind im Verlauf auffindbar, und die Zusammenfassung selbst traegt
kein U+2014 und kein U+2013.
