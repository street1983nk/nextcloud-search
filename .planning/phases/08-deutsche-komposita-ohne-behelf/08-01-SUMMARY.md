---
phase: 08-deutsche-komposita-ohne-behelf
plan: 01
subsystem: testing
tags: [tantivy, split_compound, wngerman, docker, messung, fixture]

# Dependency graph
requires:
  - phase: 02-index-und-suche
    provides: german_analyzer, load_constituents, wordlist_hash, die Fixture constituents_de.txt
  - phase: 03-ocr
    provides: die Korpusdateien 13 bis 33, aus denen die CI-Kandidaten stammen
provides:
  - Messsonde scripts/dev/compound_probe.py, die die ausgelieferte Kette gegen eine Fallliste faehrt
  - Wegwerf-Container scripts/dev/measure_compounds.sh mit hart gepinntem wngerman und tantivy
  - Fallliste backend/tests/fixtures/compound_cases_de.txt mit 46 Faellen
  - Messbericht docs/measurements/2026-09-komposita-rezept-a/ samt Rohdaten
  - Reproduzierbar erzeugte Fixture-Teilmenge mit 194 Eintraegen und maschinellem Gleichheitsbeweis
  - Owner-Entscheid zum Wortlaut von Erfolgskriterium 1
affects: [08-02, 08-03, 08-04, 08-05, german-analyzer-doku, ci-sprachfaelle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messung im Wegwerf-Container gegen die echte Debian-Liste, nie gegen eine Fixture"
    - "Die Fixture der Testsuite ist ein Erzeugnis des Messlaufs, nicht Handarbeit"
    - "Der Gleichheitsbeweis Teilmenge gegen volle Liste steckt in der Sonde und bricht den Lauf ab"

key-files:
  created:
    - scripts/dev/compound_probe.py
    - scripts/dev/measure_compounds.sh
    - backend/tests/fixtures/compound_cases_de.txt
    - docs/measurements/2026-09-komposita-rezept-a/README.md
    - docs/measurements/2026-09-komposita-rezept-a/rohdaten/tokens-rezept-a.tsv
    - docs/measurements/2026-09-komposita-rezept-a/rohdaten/fixture-subset.txt
    - docs/measurements/2026-09-komposita-rezept-a/rohdaten/kennzahlen.txt
  modified: []

key-decisions:
  - "Owner-Entscheid a: Erfolgskriterium 1 wird auf die messbar zerlegbaren Faelle umformuliert, keine Rezeptaenderung, kein Reindex"
  - "Die Sonde ruft german_analyzer und load_constituents des Pakets, sie baut keine eigene Filterkette"
  - "wngerman ist im Messskript hart auf 20161207-15 gepinnt, anders als in measure_wordlist.sh"
  - "Abfuhr als 46. Fall ergaenzt, damit jeder der sieben CI-Kandidaten eine zitierbare Zeile hat"

patterns-established:
  - "Pitfall 3 maschinell: die Spalten in_ngerman und entry_in_list stehen in jeder Zeile der Messtabelle"
  - "Pitfall 5 maschinell: die Sonde endet mit 1, sobald die Teilmenge auch nur einen Fall anders tokenisiert"
  - "Abweichungen von dokumentierten Zahlen sind Befunde im Bericht, nie ein stiller Durchlauf"

requirements-completed: [QUAL-01, QUAL-02]

# Metrics
duration: 55min
completed: 2026-09-08
---

# Phase 8 Plan 01: Messgrundlage und Owner-Entscheid Summary

**46 Verwaltungskomposita Fall fuer Fall gegen die echte 276496-Eintraege-Liste im Auslieferungsabbild gemessen, mit maschinellem Beweis, dass die Testfixture dieselben Token liefert wie die volle Liste, und mit dem Owner-Entscheid, Erfolgskriterium 1 umzuformulieren statt das Rezept anzufassen.**

## Performance

- **Duration:** rund 55 min
- **Tasks:** 3 von 3
- **Files created:** 7
- **Messlaeufe im Container:** 2 (der zweite nach Ergaenzung des Falls `Abfuhr`), beide mit Rueckgabewert 0

## Accomplishments

- **Die Messgrundlage der Phase steht.** `docs/measurements/2026-09-komposita-rezept-a/` traegt Token, Laenge, `in_ngerman` und `entry_in_list` fuer 46 Faelle. Jede spaetere Aussage der Phase 8 ueber Token kann eine Zeile in `rohdaten/tokens-rezept-a.tsv` zitieren statt sie zu raten.
- **Alle drei dokumentierten Zahlen reproduzieren exakt:** 356010 Quellzeilen, 276496 Eintraege nach Rezept A, `wordlist_hash` `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0`. Der gleiche Digest heisst: dieser Bericht redet ueber genau die Liste, mit der der bestehende Bestand indexiert wurde, und die Phase hat bis hierher keinen Reindex ausgeloest.
- **Die Fixture ist ab jetzt reproduzierbar.** 194 Eintraege, aus der echten Liste erzeugt, und die Sonde hat die Tokengleichheit gegen die volle Liste fuer alle 46 Eingaben geprueft. Pitfall 5 ist damit mechanisch erledigt statt durch Aufmerksamkeit.
- **Der Befund zu Erfolgskriterium 1 ist unabhaengig bestaetigt.** `Baugenehmigung`, 14 Zeichen, `in_ngerman` = 1, `entry_in_list` = 1, ein einziger Token `baugenehm`. Sieben der 21 Verwaltungskomposita zerfallen nicht, fuenf davon bisher nirgends dokumentiert.
- **Sieben baubare CI-Kandidaten sind belegt**, jeder mit gemessenem Token, passendem Suchbegriff-Term und Korpusdatei. Dazu drei Fallen, die der naechste Plan kennen muss.

## Task Commits

1. **Task 1: Messsonde, Wegwerf-Container und Fallliste** - `0f1eb2d` (feat)
2. **Task 2: Messlauf und Bericht** - `ad4e822` (docs)
3. **Task 3: Owner-Entscheid** - kein Commit, der Entscheid ist ein Dokumentationsergebnis und steht unten sowie im Metadaten-Commit dieses Summaries

## Files Created

- `scripts/dev/compound_probe.py` - Die Sonde. Ruft `load_constituents()` mit den Vorgabewerten und `german_analyzer` aus dem Paket, nie eine nachgebaute Kette. Schreibt Token je Fall, die Fixture-Teilmenge und die Kennzahlen und beweist im selben Lauf die Tokengleichheit von Teilmenge und voller Liste.
- `scripts/dev/measure_compounds.sh` - Der Wegwerf-Container nach dem Muster von `measure_wordlist.sh`, mit `wngerman=20161207-15` und `tantivy==0.26.0` hart gepinnt, allen Quellen als Nur-Lese-Mount und `--rm`.
- `backend/tests/fixtures/compound_cases_de.txt` - 46 Faelle: 21 Verwaltungskomposita, die zehn `UNSPLIT`-Woerter, die ASCII-Transkription, sieben CI-Kandidaten und sieben Suchbegriffe.
- `docs/measurements/2026-09-komposita-rezept-a/README.md` - Der Bericht, auf den sich 08-02 bis 08-05 berufen.
- `docs/measurements/2026-09-komposita-rezept-a/rohdaten/tokens-rezept-a.tsv` - Kopfzeile plus 46 Zeilen, keine leere Tokenspalte.
- `docs/measurements/2026-09-komposita-rezept-a/rohdaten/fixture-subset.txt` - 194 Eintraege, sortiert.
- `docs/measurements/2026-09-komposita-rezept-a/rohdaten/kennzahlen.txt` - Nur Zahlen und Digeste.

## Der Owner-Entscheid (Task 3)

Die Frage: Was geschieht mit dem Wortlaut von Erfolgskriterium 1 der Phase 8
("Ein Nutzer sucht 'Genehmigung' und findet Dokumente, in denen nur
'Baugenehmigung' steht")?

**Die Antwort des Owners, woertlich:**

> a) Umformulieren + Execute (Recommended)

**Buchstabe: a.** Also: Kriterium auf die messbar zerlegbaren Faelle
umformulieren, keine Rezeptaenderung, kein Reindex. Die Plaene 08-02 bis 08-05
laufen unveraendert weiter.

Der Entscheid fiel am 08.09.2026 im Chat per Auswahlfrage, nachdem die Messung
aus Task 2 vorlag.

**Was daraus folgt, weil die spaeteren Plaene sich darauf berufen:**

- `SCHEMA_VERSION` bleibt 1, `ANALYZER_VERSION` bleibt 1, `wordlist_hash` bleibt
  `b1f64012...dde0`. Kein Plan dieser Phase darf die Konstituentenliste, das
  Fenster oder `FUGEN` anfassen; jede solche Aenderung waere ein voller Reindex.
- Muster 2 (zweites Indexfeld `body_de_parts` mit Rezept A4) ist damit **nicht**
  Teil dieser Phase. Option c haette die Phase neu planen lassen; sie wurde nicht
  gewaehlt.
- Der Fall `Baugenehmigung` bleibt ein benannter Nicht-Fall. Die Zusage wird auf
  Faelle gestellt, die gemessen halten, zum Beispiel "Vereinbarung findet
  Pachtvereinbarung".
- Die Roadmap-Zeile fuer Erfolgskriterium 1 aendert ihren Wortlaut. Diese
  Aenderung gehoert dem Orchestrator beziehungsweise einem der Plaene 08-02 bis
  08-05; dieser Plan hat ROADMAP.md nicht angefasst (Worktree-Regel).

**Gegenprobe, ob die Messung dem Entscheid widerspricht: nein.** Der Lauf
bestaetigt die Recherche in jedem Punkt. `Baugenehmigung` ist mit Rezept A ein
Listeneintrag und liefert genau einen Token; nichts an dieser Messung legt nahe,
dass Rezept A den Fall doch loesen wuerde. Der Entscheid steht auf der Messung,
nicht gegen sie.

## Decisions Made

1. **Die Sonde ruft das Produkt, sie baut es nicht nach.** Ein Aufruf von
   `german_analyzer(`, ein Aufruf von `load_constituents(`, kein einziges
   Vorkommen des Builders. Eine nachgebaute Kette wuerde die Sonde messen statt
   den ausgelieferten Weg, und genau diese Verwechslung ist der Grund, warum die
   Fixture heute 172 handverlesene Eintraege hat.
2. **Der Gleichheitsbeweis ist Teil des Laufs, nicht des Berichts.** Die Sonde
   baut eine zweite Kette ueber die Teilmenge und endet bei einer einzigen
   Abweichung mit Rueckgabewert 1. Ein Bericht, der die Gleichheit nur behauptet,
   waere genau so viel wert wie die Aufmerksamkeit dessen, der ihn schreibt.
3. **`wngerman` haerter gepinnt als im Vorbild.** `measure_wordlist.sh`
   installiert das Paket ohne Fassung, dieses Skript mit `=20161207-15`. Die
   Zahlen dieser Messung sind an genau diese Fassung gebunden, und ein Debian
   Point Release darf den Bericht nicht stillschweigend ungueltig machen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktionalitaet] Siebter CI-Kandidat ohne Suchbegriff**

- **Found during:** Task 2 (Messlauf und Bericht)
- **Issue:** Der Plan zaehlt sieben CI-Kandidaten auf, aber nur sechs
  Suchbegriffe (`Vereinbarung`, `Protokoll`, `Erinnerung`, `Auszug`, `Abgabe`,
  `Belehrung`). Fuer `Sperrmüllabfuhr` fehlte der zugehoerige Konstituent. Damit
  haette der siebte Kandidat als einziger keine zitierbare Zeile in
  `tokens-rezept-a.tsv` gehabt, was dem erklaerten Zweck dieser Messung und dem
  ersten Erfolgskriterium des Plans widerspricht.
- **Fix:** `Abfuhr` als 46. Fall in `compound_cases_de.txt` ergaenzt und den
  Messlauf wiederholt. Gemessen: `Abfuhr` ist Listeneintrag, ein Token `abfuhr`,
  byteweise derselbe Token wie der zweite Token von `Sperrmüllabfuhr`. Der Fall
  ist damit baubar.
- **Files modified:** `backend/tests/fixtures/compound_cases_de.txt`
- **Verification:** Zweiter Containerlauf mit Rueckgabewert 0, `cases=46`,
  Kopfzeile plus 46 Zeilen in der TSV, Digest unveraendert.
- **Committed in:** `0f1eb2d` (Teil des Task-1-Commits, weil die Fallliste dort
  entsteht), Wirkung in `ad4e822`
- **Dokumentiert:** Bericht, Abschnitt 5, "Befund 3"

**2. [Rule 3 - Blockierendes Problem] Die Pins standen nur als Variablenwert im Skript**

- **Found during:** Task 1
- **Issue:** Erste Fassung von `measure_compounds.sh` hielt die Fassungen als
  `TANTIVY_VERSION="0.26.0"` und `WNGERMAN_VERSION="20161207-15"`. Die
  Zeichenketten `tantivy==0.26.0` und `wngerman=20161207-15` standen damit
  nirgends im Skript, ein grep nach dem Pin fand nichts, und das
  Akzeptanzkriterium des Plans war verletzt.
- **Fix:** Die Pins stehen jetzt als vollstaendige apt- und pip-Argumente in je
  einer Variablen (`WNGERMAN="wngerman=20161207-15"`,
  `TANTIVY="tantivy==0.26.0"`), einmal geschrieben und dreifach benutzt.
- **Files modified:** `scripts/dev/measure_compounds.sh`
- **Verification:** `grep -c` fuer beide Zeichenketten ergibt 1, `sh -n` sauber,
  Containerlauf erfolgreich.
- **Committed in:** `0f1eb2d`

---

**Total deviations:** 2 auto-fixed (1x Rule 2, 1x Rule 3)
**Impact on plan:** Beide sind Korrektheitsfragen im Rahmen des Plans, kein
Scope Creep. Weder das Rezept noch die Filterkette noch der Digest wurden
angefasst.

## Issues Encountered

**Der Owner-Entscheid lag beim Start bereits vor.** Task 3 ist im Plan ein
`checkpoint:decision`. Die Antwort des Owners (Buchstabe a) war im Auftrag an
diesen Executor enthalten, zusammen mit der Auflage, bei einem substanziellen
Widerspruch zwischen Messung und Entscheid anzuhalten. Die Messung
widerspricht nicht, deshalb wurde der Checkpoint als beantwortet behandelt und
der Wortlaut oben protokolliert, statt anzuhalten.

**Docker-Mounts auf Windows.** Der Lauf braucht `MSYS_NO_PATHCONV=1`, sonst
verbiegt MSYS die Container-Pfade der Nur-Lese-Mounts. Der Hinweis steht im
Kopfkommentar des Skripts und in Abschnitt 7 des Berichts.

## Befunde fuer die naechsten Plaene

Drei Dinge, die 08-02 bis 08-05 kennen muessen und die vor diesem Lauf niemand
wusste:

1. **`Abgabe` trifft zwei Korpusdateien.** `15-schweiz-baubewilligung.pdf`
   traegt `Ersatzabgabe`, `16-oesterreich-mitteilung.pdf` traegt
   `Verwaltungsabgabe`; beide zerfallen zum Term `abgab`. Ein CI-Sprachfall, der
   auf genau einen Treffer prueft, ist mit diesem Suchbegriff nicht baubar. Der
   Waechter in `build_corpus.py` schuetzt den Term nicht, weil `Abgabe` nicht in
   der Einmaligkeits-Tabelle von `testdata/CORPUS.md` steht.
2. **`Rechtsmittelbelehrung` fehlt in der Einmaligkeits-Tabelle** von
   `CORPUS.md`, steht aber gegen `corpus-truth.json` geprueft nur in Datei 15.
   Wer daraus einen CI-Fall macht, sollte den Term nachtragen, damit der
   Waechter ihn ab dann mitschuetzt.
3. **`Baukosten` erklaert sich nicht ueber `entry_in_list`.** Neun Zeichen,
   nicht in `ngerman`, kein Listeneintrag, und trotzdem ein einziger Token,
   weil `bau` mit drei Zeichen unter MIN_LEN = 4 liegt. Die Untergrenze ist eine
   zweite, unabhaengige Sperre neben der Listenmitgliedschaft. Wer nur die
   Spalte `entry_in_list` liest, uebersieht die Haelfte der Faelle.

Dazu der bereits in der Recherche benannte, jetzt gemessene achte Fall:
`Grundstuecksverkehrsgenehmigung` mit ausgeschriebenen Umlauten bleibt ein
einziger Token, waehrend die Fassung mit echten Umlauten in drei zerfaellt. Die
Index-Seite bildet keine Umlautvarianten. Das gehoert als Testfall oder als
benannter Grenzfall in `docs/german-analyzer.md`.

## Known Stubs

Keine. Alle erzeugten Dateien tragen gemessene Daten, keine Platzhalter.

## User Setup Required

Keine. Der Lauf braucht nur Docker, das auf der Maschine vorhanden ist (29.5.2).

## Next Phase Readiness

08-02 bis 08-05 koennen unveraendert laufen. Sie haben ab jetzt:

- eine zitierbare Zeile je Fall in `rohdaten/tokens-rezept-a.tsv`,
- eine reproduzierbar erzeugte Fixture-Teilmenge samt Gleichheitsbeweis,
- sieben belegte CI-Kandidaten mit Korpuszuordnung und drei benannten Fallen,
- den Owner-Entscheid a als Grundlage fuer die Umformulierung von
  Erfolgskriterium 1.

**Nicht erledigt und bewusst nicht angefasst:** `STATE.md` und `ROADMAP.md`
schreibt der Orchestrator nach der Welle, nicht dieser Worktree-Agent. Die
Umformulierung der Roadmap-Zeile fuer Erfolgskriterium 1 ist damit noch offen.

## Self-Check: PASSED

- Alle sieben erzeugten Dateien plus dieses Summary liegen auf der Platte.
- Beide Task-Commits sind in `git log`: `0f1eb2d`, `ad4e822`. Summary-Commit
  `b648372`.
- Arbeitsbaum sauber, keine Aenderung an `STATE.md` oder `ROADMAP.md`.
- Alle drei Commits als `street1983nk <k.cherif@outlook.de>`, keine
  Claude-Trailer.

---
*Phase: 08-deutsche-komposita-ohne-behelf*
*Completed: 2026-09-08*
