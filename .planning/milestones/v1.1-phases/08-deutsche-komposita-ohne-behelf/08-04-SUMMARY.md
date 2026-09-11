---
phase: 08-deutsche-komposita-ohne-behelf
plan: 04
subsystem: testing
tags: [tantivy, split_compound, regressionswaechter, ci-sprachfaelle, korpus, qual-02]

# Dependency graph
requires:
  - phase: 02-index-und-suche
    provides: german_analyzer, load_constituents, die Fixture constituents_de.txt, die vier deutschen Sprachfaelle
  - phase: 03-ocr
    provides: die Korpusdateien 13 bis 33 und die OCR-Strecke, ohne die zwei der drei neuen Faelle nichts zu finden haetten
  - phase: 08-deutsche-komposita-ohne-behelf
    plan: 01
    provides: die gemessenen Token je Fall, die Fallliste, die Sonde compound_probe.py, den Wegwerf-Container
  - phase: 08-deutsche-komposita-ohne-behelf
    plan: 02
    provides: den filter_chain-Strukturwaechter, neben dem die Tokentabelle jetzt die Wirkung statt der Ursache zeigt
provides:
  - Fixture constituents_de.txt mit 223 Eintraegen, gegen die echte Debian-Liste geprueft statt geglaubt
  - compound_probe.py --against LIST, der Gleichheitsbeweis fuer eine beliebige benannte Liste
  - COMPOUNDS mit 21 gemessenen Zeilen, die sieben Nicht-Faelle als Zusicherung statt als Kommentar
  - Gleichlauftest zwischen behaupteter Tabelle und gemessener Fallliste
  - backend/tests/test_corpus_terms.py, der Waechter vor jedem neuen CI-Suchbegriff, mit zwei Toren
  - drei zusaetzliche deutsche Sprachfaelle in integration.yml, Kompositafaelle jetzt fuenf statt zwei
affects: [08-05, ci-sprachfaelle, german-analyzer-doku, build_corpus]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Liste wird nicht geglaubt, sondern im Container gegen die echte Liste gehalten (--against)"
    - "Ein Waechter ueber Korpusbegriffe hat zwei Tore: Token fuer die Frage, Buchstaben fuer die Listenunabhaengigkeit"
    - "Ein CI-Suchbegriff wird lokal belegt, bevor er in den Workflow geschrieben wird"
    - "Verworfene Kandidaten stehen als Testfall da, nicht als Fussnote"

key-files:
  created:
    - backend/tests/test_corpus_terms.py
  modified:
    - backend/tests/fixtures/constituents_de.txt
    - backend/tests/test_analyzer.py
    - scripts/dev/compound_probe.py
    - scripts/dev/measure_compounds.sh
    - scripts/dev/build_corpus.py
    - testdata/CORPUS.md
    - .github/workflows/integration.yml

key-decisions:
  - "Verkehr faellt als CI-Fall aus: Parteienverkehr steht in einer zweiten Korpusdatei, das Tokentor sieht das nur deshalb nicht, weil die Fixture das Wort nicht zerlegen kann"
  - "Protokoll faellt als CI-Fall aus: die Engine liest die Ueberschrift von 19-uebermittlung.tif ohne Umlautpunkte, und diese Form bleibt ein Token"
  - "Der Korpus-Waechter bekommt ein zweites, listenunabhaengiges Tor ueber die Buchstaben, weil das Tokentor gegen die Fixture misst und CI gegen die volle Debian-Liste"
  - "Die drei gewaehlten Begriffe sind Vereinbarung, Auszug, Erinnerung; die beiden Scans haben eine gemessene Zeichenfehlerrate von 0"
  - "measure_compounds.sh wird mitgeaendert, obwohl der Plan es nicht auffuehrt: ohne Durchreichen von --against ist das Akzeptanzkriterium des Plans nicht ausfuehrbar"

patterns-established:
  - "Ein verworfener Kandidat wird als Test festgehalten, damit der naechste Plan ihn nicht wieder vorschlaegt"
  - "Rotbeweis von Hand: --against gegen eine absichtlich beschaedigte Liste, Rueckgabewert und Meldung im Summary"
  - "Die Messung laeuft in einen Wegwerf-Ordner, damit die Rohdaten der Vorwelle beweisbar unberuehrt bleiben"

requirements-completed: [QUAL-02]

# Metrics
duration: 70min
completed: 2026-09-08
---

# Phase 8 Plan 04: Regressionswaechter und drei neue CI-Sprachfaelle Summary

**Die Tokentabelle der deutschen Kette traegt jetzt 21 gemessene Zeilen statt 16 und nagelt beide Richtungen fest, die Fixture ist von 172 auf 223 Eintraege gewachsen und im Container gegen die echte Debian-Liste geprueft statt geglaubt, und drei neue CI-Sprachfaelle stehen im Workflow, jeder vorher von einem neuen Waechter belegt, der dabei zwei der vom Plan vorgeschlagenen Kandidaten als unbaubar entlarvt hat.**

## Performance

- **Duration:** rund 70 min
- **Tasks:** 3 von 3
- **Files created:** 1, **modified:** 7
- **Tests:** 1744 passed, 15 skipped (Basis der Welle: 1723 passed), Laufzeit 3 min 31 s
- **Containerlaeufe:** 4 (zwei gruene Messlaeufe, ein Rotbeweis, ein Wiederholungslauf zur Reproduzierbarkeit)

## Accomplishments

- **Eine verlorene Zerlegung wird ab jetzt rot, nicht nur ein entfernter Splitter.** `COMPOUNDS` traegt 21 Zeilen mit den Token aus `rohdaten/tokens-rezept-a.tsv`, darunter die sieben Woerter, die heute ganz bleiben, als Zeilen mit ihrem einen Token. Der Unterschied zu `UNSPLIT` ist der Punkt: in allen vier gemessenen Rezeptvarianten ueberleben alle zehn `UNSPLIT`-Woerter unversehrt, ein Test, der nur sie prueft, winkt jede Verschlechterung der Trefferausbeute durch.
- **Die Fixture ist gemessen, nicht behauptet.** 223 Eintraege, die Vereinigung der 172 alten mit den 194 aus dem Messlauf, sortiert und ohne Doppelte. Der Lauf `sh scripts/dev/measure_compounds.sh --against backend/tests/fixtures/constituents_de.txt` endet mit 0 und meldet `/opt/findling/against.txt tokenises like the full list, 223 entries`. Das ist T-08-12 mechanisch erledigt: mehr Eintraege sind nicht automatisch besser, ein zusaetzlicher Eintrag kann eine gelingende Zerlegung in eine Sackgasse fuehren, und genau diese Frage beantwortet der Lauf statt eines Kommentars.
- **Der Waechter vor dem CI-Fall hat zwei Tore, und das zweite verdient seinen Platz.** `test_corpus_terms.py` prueft je Begriff, dass genau eine Korpusdatei alle seine Token traegt, und zusaetzlich, dass keine zweite Datei die Buchstaben des Begriffs ueberhaupt enthaelt. Das zweite Tor ist listenunabhaengig und es hat zwei Kandidaten des Plans aussortiert, die das erste Tor durchgewinkt haette.
- **Zwei Kandidaten des Plans sind nachweislich nicht baubar, und der Nachweis steht als Test da.** `Verkehr` und `Protokoll` haetten den Workflow auf `main` rot gemacht. Beide Befunde sind unten belegt und als Testfall festgehalten, damit sie nicht in einem spaeteren Plan wieder vorgeschlagen werden.
- **Kein Byte des Testkorpus hat sich bewegt.** `git status --short testdata/corpus` ist leer, `build_corpus.py --check` meldet 39 Dateien, 400065 Bytes, byteweise identisch mit einem frischen Bau. `UNIQUE_TERMS` ist eine Pruefliste und veraendert kein Byte einer Korpusdatei.
- **Kein Produktionscode angefasst.** Die Aenderungen liegen in Tests, in zwei Entwicklerskripten, in `testdata/CORPUS.md` und im Workflow. `SCHEMA_VERSION`, `ANALYZER_VERSION` und `wordlist_hash` bleiben, wo der Owner-Entscheid a sie stehen laesst; der Digest `b1f64012...dde0` ist im Wiederholungslauf unveraendert bestaetigt.

## Task Commits

1. **Task 1: Fixture erneuern und Regressionswaechter bauen** - `8cb05e5` (test)
2. **Task 2: Die neuen Suchbegriffe gegen den Korpus absichern** - `904bd25` (test)
3. **Task 3: Drei zusaetzliche deutsche Sprachfaelle im CI-Set** - `ec9c9f3` (test)

## Die Messlaeufe

**Gruener Lauf, Rueckgabewert 0:**

```
measure_compounds: image=python:3.13-slim-trixie wngerman=20161207-15 tantivy==0.26.0
measure_compounds: against=/c/.../backend/tests/fixtures/constituents_de.txt
compound_probe: /opt/findling/against.txt tokenises like the full list, 223 entries
compound_probe: 46 cases, 276496 entries, 194 in the subset
```

**Rotbeweis, von Hand gefahren, Rueckgabewert 1.** Ein Waechter ist nur so viel
wert wie der Nachweis, dass er faellt. Aus der Fixture wurde der Eintrag `frist`
entfernt und der Lauf wiederholt:

```
compound_probe: /opt/findling/against.txt does not tokenise like the full list
compound_probe: differing case: Kündigungsfrist
EXIT_CODE=1
```

Der Waechter nennt die betroffene Eingabe, nicht nur die Tatsache einer
Abweichung. Die beschaedigte Liste lag ausserhalb des Repositoriums und wurde
danach geloescht.

**Reproduzierbarkeit der Rohdaten aus 08-01:** derselbe Lauf, in einen
Wegwerf-Ordner ausserhalb des Repositoriums geschrieben, liefert
`tokens-rezept-a.tsv`, `fixture-subset.txt` und `kennzahlen.txt` zeichengleich
mit den in 08-01 eingecheckten Dateien, inklusive
`wordlist_hash=b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0`
und `cases_without_token=0`. Deshalb steht in `docs/measurements/` kein
geaendertes Byte: der Lauf dieser Welle hat die Rohdaten der Vorwelle bestaetigt,
nicht ueberschrieben.

## Die zwei Befunde, die zwei geplante CI-Faelle gekippt haben

Beide sind als Test festgehalten, nicht als Prosa, damit der naechste Plan sie
nicht ueberliest.

### Befund 1: `Verkehr` trifft zwei Dateien, und das Tokentor sieht es nicht

Der Plan nennt `Verkehr` als ersten Kandidaten (Konstituent von
`Grundstücksverkehrsgenehmigung` in `09-bescheid.pdf`, Textlage). Gemessen:

| Begriff | Traeger nach Token (Fixture) | Traeger nach Buchstaben |
|---|---|---|
| `Verkehr` | `09-bescheid.pdf` | `09-bescheid.pdf`, `16-oesterreich-mitteilung.pdf` |
| `Abgabe` | `15-schweiz-baubewilligung.pdf` | `15-schweiz-baubewilligung.pdf`, `16-oesterreich-mitteilung.pdf` |

`16-oesterreich-mitteilung.pdf` traegt `Parteienverkehr` und
`Verwaltungsabgabe`. Unter der **Fixture** bleiben beide Woerter ein Token, weil
`parteien` und `verwaltung` nie Teil eines gemessenen Falls waren und deshalb
nicht in der Teilmenge stehen; das Tokentor meldet beide Begriffe als eindeutig.
Unter der **vollen Debian-Liste**, mit der CI indexiert, sind `parteien` und
`verwaltung` Eintraege. Fuer `Verwaltungsabgabe` ist der Zerfall zum Term
`abgab` in 08-01 bereits gemessen (Befund 1 des Messberichts).

Das ist die eigentliche Lehre dieses Plans: **das Tokentor kann einen Begriff nur
eindeutiger machen, als er ist, nie weniger eindeutig.** Deshalb steht daneben
ein zweites, listenunabhaengiges Tor ueber die Buchstaben des Begriffs. Wenn
keine zweite Datei die Buchstaben ueberhaupt enthaelt, kann keine Wortliste der
Welt dort einen zweiten Treffer erzeugen. Die Regel ist bewusst konservativ, und
sie ist der Grund, warum dieser Plan einen roten CI-Lauf auf `main` nicht
produziert hat.

`test_a_rejected_candidate_passes_the_token_gate_and_fails_the_letter_gate`
haelt beides fest: dass beide Begriffe das Tokentor bestehen und am
Buchstabentor scheitern.

### Befund 2: `Protokoll` ist nicht baubar, weil die Engine keine Umlautpunkte liest

Der Plan nennt `Protokoll` als dritten Kandidaten (`Übermittlungsprotokoll` in
`19-uebermittlung.tif`). Der Begriff besteht **beide** Tore. Trotzdem faellt der
Fall, und zwar an einer dritten Stelle:

`docs/ocr.md` und `backend/tests/test_ocr.py` halten seit dem 01.09.2026 fest,
dass tesseract 5.5.0 im Auslieferungsabbild die fette Ueberschrift dieser Datei
als `Ubermittlungsprotokoll` liest, ohne die zwei Punkte. Die vier
kleingeschriebenen Umlaute der anderen Korpusbilder kommen unversehrt zurueck;
es ist der grosse Umlaut in der Ueberschrift, der sie verliert. Gemessen mit der
Fixture:

```
Übermittlungsprotokoll -> ['ubermittl', 'protokoll']
Ubermittlungsprotokoll -> ['ubermittlungsprotokoll']
```

Indexiert wird die zweite Form. Sie ist ein Token, also findet eine Suche nach
`Protokoll` diese Datei nicht. Der bestehende Test
`test_a_photographed_document_becomes_the_terms_the_corpus_promises` bleibt
davon unberuehrt, weil er den Rohtext faltet und nach einer Teilzeichenkette
sucht, nicht nach einem Term.

`test_the_headline_the_engine_really_reads_does_not_come_apart` haelt beide
Formen nebeneinander fest.

## Die drei gewaehlten Begriffe

| Fall | Suchbegriff | Kompositum | Datei | Lage | Zeichenfehlerrate |
|---|---|---|---|---|---|
| 8 | `Vereinbarung` | Pachtvereinbarung | `14-pacht-mit-anhang.pdf` | Textlage | entfaellt |
| 9 | `Auszug` | Grundbuchsauszug | `16-oesterreich-mitteilung.pdf` | nur Pixel | 0,000000 |
| 10 | `Erinnerung` | Zahlungserinnerung | `30-nur-ein-bild.pdf` | nur Pixel | 0,000000 |

Alle drei haben eine gemessene Zeile in `tokens-rezept-a.tsv`, alle drei
bestehen beide Tore, und die beiden Scans stehen auf Seiten, die die
OCR-Messung vom 06.09.2026 mit einer Zeichenfehlerrate von exakt 0 gelesen hat.
Fall 8 traegt zusaetzlich die Zusicherung auf den Textausschnitt (`subline`
enthaelt `vereinbarung`, keine spitze Klammer), also die Zusicherung, die einen
Treffer von einem Treffer mit Inhalt trennt.

**Eine Einschraenkung, die der Kommentar im Workflow ausdruecklich nennt:**
`14-pacht-mit-anhang.pdf` schreibt das Wort `Vereinbarung` auch einmal fuer sich
allein in die Textlage. Fall 8 waere also auch ohne `split_compound` gruen. Die
Faelle 9 und 10 sind die beiden, die **nur** die Zerlegung beantworten kann:
`Auszug` und `Erinnerung` stehen in ihren Dateien ausschliesslich als zweiter
Teil eines Kompositums.

## Was der Beweis dieser drei Faelle wirklich ist

**Der Beweis der drei neuen CI-Faelle ist erst der erste `integration.yml`-Lauf
auf `main`.** Dieser Workflow laeuft auf `push` und `pull_request` und nur mit
den Pfadfiltern seines Kopfes; er laeuft nicht in diesem Worktree, und er kann
hier auch nicht laufen: er baut zwei vollstaendige Nextcloud-Instanzen, indexiert
39 Korpusdateien und faehrt eine OCR-Strecke ueber ein Dutzend gerenderte
Seiten.

**Die lokale Vorpruefung ist `backend/tests/test_corpus_terms.py`.** Sie laeuft
in jeder Suite, sie misst dieselbe Frage mit den Mitteln, die eine
Entwicklermaschine hat, und sie ist der Grund, warum die drei Faelle nicht auf
gut Glueck geschrieben wurden. Was sie nicht ersetzen kann: den echten Index,
die echte Wortliste des Abbilds und die echte OCR-Strecke. Genau an dieser Naht
sitzt das Buchstabentor.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierendes Problem] `measure_compounds.sh` konnte `--against` nicht durchreichen**

- **Found during:** Task 1
- **Issue:** Das Akzeptanzkriterium des Plans verlangt den Lauf
  `sh scripts/dev/measure_compounds.sh --against backend/tests/fixtures/constituents_de.txt`.
  Das Skript kannte nur `[output-directory]` und haette `--against` als
  Ausgabeverzeichnis gelesen. Ohne Aenderung ist das Kriterium nicht
  ausfuehrbar, und die Datei steht nicht in `files_modified` des Plans.
- **Fix:** Das Skript nimmt `--against LIST` vor dem optionalen
  Ausgabeverzeichnis an, prueft die Datei, haengt sie als Nur-Lese-Mount an und
  reicht das Argument als `PROBE_ARGS` in den Container. Die Mounts stehen jetzt
  in Positionsparametern, weil eine POSIX-Shell ohne Felder kein Argument
  anhaengen kann, ohne die Quotierung der vorherigen zu verlieren.
- **Files modified:** `scripts/dev/measure_compounds.sh`
- **Verification:** `sh -n` sauber, gruener Lauf mit 0, Rotbeweis mit 1, beide
  Pins weiterhin je einmal als vollstaendiges Argument im Skript.
- **Committed in:** `8cb05e5`

**2. [Rule 1 - Fehler] `Verkehr` als CI-Fall haette den Workflow auf main rot gemacht**

- **Found during:** Task 2
- **Issue:** Der Plan nennt `Verkehr` als bevorzugten ersten Kandidaten. Der
  Begriff steht als `Parteienverkehr` in einer zweiten Korpusdatei; unter der
  vollen Debian-Liste, mit der CI indexiert, zerfaellt dieses Wort und der
  Sprachfall haette statt einem Treffer zwei bekommen.
- **Fix:** `Verkehr` faellt aus der Auswahl, `Auszug` rueckt nach. Der Grund
  steht als Testfall in `test_corpus_terms.py` und nicht als Fussnote. Dazu das
  zweite, listenunabhaengige Tor, das diese Klasse von Fehlern kuenftig
  automatisch abfaengt.
- **Files modified:** `backend/tests/test_corpus_terms.py`
- **Verification:** gemessene Traegerlisten oben, beide Tore als Test.
- **Committed in:** `904bd25`

**3. [Rule 1 - Fehler] `Protokoll` als CI-Fall haette den Workflow auf main rot gemacht**

- **Found during:** Task 2
- **Issue:** Der Plan nennt `Protokoll` als dritten Kandidaten. Die Engine liest
  die Ueberschrift von `19-uebermittlung.tif` ohne Umlautpunkte, und diese Form
  bleibt ein einziges Token, also findet `Protokoll` die Datei nicht.
- **Fix:** `Protokoll` faellt aus der Auswahl, `Erinnerung` rueckt nach. Die
  beiden Wortformen stehen als Zusicherung nebeneinander im neuen Waechter.
- **Files modified:** `backend/tests/test_corpus_terms.py`
- **Verification:** gemessene Tokenlisten oben.
- **Committed in:** `904bd25`

**4. [Rule 2 - Fehlende kritische Funktionalitaet] Ein Tokentor allein ist ein falsches Gruen**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt die Pruefung ueber Tokenmengen. Das ist richtig
  und reicht nicht: die Pruefung laeuft gegen die Fixture, der Workflow gegen
  die volle Debian-Liste. Ein Begriff, den die Fixture als eindeutig meldet,
  kann unter der vollen Liste in einer zweiten Datei zerfallen; genau das ist
  bei zwei der vorgeschlagenen Kandidaten der Fall.
- **Fix:** Ein zweites Tor ueber die Buchstaben des Begriffs, ausdruecklich
  **zusaetzlich** und nicht als Ersatz fuer die Tokenpruefung. Die drei
  gewaehlten Begriffe bestehen beide Tore, die beiden verworfenen scheitern am
  zweiten. Das Akzeptanzkriterium des Plans (keine Teilzeichenketten-Pruefung
  als Ersatz) ist damit eingehalten: die Entscheidung ueber Eindeutigkeit faellt
  weiterhin ueber Tokenmengen, das Buchstabentor kann nur zusaetzlich ablehnen.
- **Files modified:** `backend/tests/test_corpus_terms.py`
- **Committed in:** `904bd25`

---

**Total deviations:** 4 auto-fixed (1x Rule 3, 2x Rule 1, 1x Rule 2)
**Impact on plan:** Alle vier sind Korrektheitsfragen im Rahmen des Plans. Der
Plan gibt eine Vorzugsreihenfolge mit zwei Toren vor; zwei Kandidaten halten die
Tore nicht, also ruecken die naechsten nach. Kein Scope Creep, keine
Rezeptaenderung, kein Reindex.

## Issues Encountered

**Der Messlauf schreibt standardmaessig in die Rohdaten von 08-01.** Um einen
stillen Ueberschreibvorgang auszuschliessen, lief die Messung in einen
Wegwerf-Ordner ausserhalb des Repositoriums und wurde danach gegen die
eingecheckten Dateien verglichen. Ergebnis: zeichengleich. Das ist zugleich der
Nachweis, dass die Messung von 08-01 reproduzierbar ist.

**Windows und der Ausgabepfad.** Ein Ausgabeverzeichnis unterhalb von
`AppData/Local/Temp` bildet MSYS auf `/tmp` ab; mit `MSYS_NO_PATHCONV=1` landet
dieser Pfad im Container statt auf der Platte des Hosts, und die Dateien sind
danach nicht auffindbar. Ein Pfad unter `/c/Users/...` funktioniert. Der Hinweis
auf `MSYS_NO_PATHCONV=1` im Kopf des Skripts bleibt richtig, er reicht nur nicht
fuer jedes Ziel.

## Verification

- `cd backend && uv run pytest -q`: **1744 passed, 15 skipped** (Basis der Welle: 1723 passed)
- `uv run ruff check .`, `uv run ruff format --check .`: gruen, 117 Dateien
- `uv run pyright`: 0 errors, 0 warnings, 0 informations
- `uv run vulture`: keine Meldung
- `uv run ruff check ../scripts/dev/compound_probe.py` und `ruff format --check`: gruen (die Datei liegt ausserhalb des pyright- und vulture-Include-Pfads, deshalb ausdruecklich geprueft)
- `uv run ruff check ../scripts/dev/build_corpus.py` und `ruff format --check`: gruen
- `sh scripts/dev/measure_compounds.sh --against backend/tests/fixtures/constituents_de.txt`: Rueckgabewert 0
- `python -c "yaml.safe_load(...)"` ueber `integration.yml`: parst, fuenf Jobs
- `grep -c "seven German language cases" .github/workflows/integration.yml`: 0
- Zehn nummerierte Faelle im Schritt, elf `search`-Aufrufe (Fall 6 hat die Gegenprobe)
- `git status --short testdata/corpus`: leer
- `python scripts/dev/build_corpus.py --check`: 39 Dateien, 400065 Bytes, byteweise identisch
- `wc -l backend/tests/fixtures/constituents_de.txt`: 223, `sort -u` liefert dieselbe Datei

## Known Stubs

Keine. Jede Zusicherung dieses Plans steht auf einer gemessenen Zahl.

## Threat Flags

Keine neue sicherheitsrelevante Flaeche. Die Dispositionen des Plans sind
erfuellt: T-08-12 ueber `--against` im Container, T-08-13 ueber die Zeile fuer
das 63 Zeichen lange Kompositum (sechs Token, nie leer), T-08-14 ueber je eine
eigene Fehlermeldung und eine eigene JSON-Datei je Fall, T-08-SC ueber den
Verzicht auf neue Pakete und darauf, `build_corpus.py` als Modul zu laden statt
auszufuehren.

## User Setup Required

Keine. Der Messlauf braucht Docker, das auf der Maschine vorhanden ist.

## Next Phase Readiness

- Der Regressionswaechter steht: eine Listen- oder Rezeptaenderung wird an der Stelle rot, an der sie Trefferausbeute kostet, und der Waechter aus 08-02 nennt daneben die Ursache.
- Das CI-Sprachfall-Set traegt fuenf Kompositafaelle. Der Beweis der drei neuen faellt beim ersten `integration.yml`-Lauf auf `main`.
- Fuer 08-05 offen und ausdruecklich nicht erledigt: `docs/german-analyzer.md` spricht weiterhin von "den sechzehn Testkomposita" und von "14 von 16". Diese Doku steht nicht in `files_modified` dieses Plans und wurde deshalb nicht angefasst.
- `STATE.md` und `ROADMAP.md` schreibt der Orchestrator nach der Welle, nicht dieser Worktree-Agent.

## Self-Check: PASSED

- `backend/tests/test_corpus_terms.py` liegt auf der Platte, die sieben geaenderten Dateien ebenso.
- Alle drei Task-Commits sind in `git log`: `8cb05e5`, `904bd25`, `ec9c9f3`.
- Arbeitsbaum ausser diesem Summary sauber, keine Aenderung an `STATE.md` oder `ROADMAP.md`, kein Byte in `testdata/corpus`.
- Alle Commits als `street1983nk <k.cherif@outlook.de>`, keine Claude-Trailer.
- Das Hilfsskript der Messung und die beschaedigte Liste lagen ausserhalb des Repositoriums beziehungsweise wurden vor dem Commit geloescht.

---
*Phase: 08-deutsche-komposita-ohne-behelf*
*Completed: 2026-09-08*
