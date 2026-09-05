---
phase: 06-semantische-suche
plan: 03
subsystem: quality
tags: [multilingual-e5-small, quantisierung, int8, onnxruntime, testset, mehrsprachigkeit, e5-praefixe, mrr, recall]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-01: das int8-Modell im Abbild, scripts/dev/quantize_model.py und die Modellkonstanten FINDLING_EMBED_MODEL_DIR"
  - phase: 03-ocr
    provides: "scripts/dev/build_corpus.py mit der erfundenen deutschen Behoerdenprosa, aus der 20 der 42 deutschen Abschnitte stammen"
provides:
  - "ein dreisprachiges Testset aus 126 Umschreibung-zu-Passage-Paaren mit maschinell durchgesetzter Wortueberschneidungsregel"
  - "ein Messwerkzeug fuer Recall@1, Recall@5 und MRR je Modellfassung, Sprache, Praefixeinstellung und Vektorquantisierung"
  - "die beantwortete Frage D-05: die E5-Praefixe wirken nachweislich"
  - "die beantwortete Frage D-02, mit einem Befund auf Franzoesisch, der die Abbruchregel des Plans reisst"
  - "die getrennte Zahl fuer die Vektorquantisierung: auf diesem Testset nicht messbar"
affects: [06-05 Einbettungen und Modell-Wrapper, 06-04 Vektorspeicher und Schema, 06-10 Offline-Test, Store-Text D-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Testset mit maschinell durchgesetzter Regel statt mit gutem Vorsatz: ein Fall mit Wortueberschneidung misst die Volltextsuche und ist rot"
    - "Die Passagenmenge ist zugleich die Ablenkermenge, damit keine zweite Liste abdriften kann"
    - "Paarweise Auswertung ueber --per-case, weil eine MRR-Differenz ueber 42 Faelle als Zahl nicht lesbar ist"
    - "Aussenzahlen in eigener Spalte mit benannten Vorbehalten, nie als eigener Beleg"

key-files:
  created:
    - testdata/semantik/README.md
    - testdata/semantik/de.jsonl
    - testdata/semantik/en.jsonl
    - testdata/semantik/fr.jsonl
    - scripts/dev/model_quality.py
    - backend/tests/test_model_quality.py
    - docs/measurements/2026-09-05-modellqualitaet/README.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "D-05 ist positiv beantwortet: mit und ohne Praefix bekommen 21 bis 31 von 42 Faellen je Sprache einen anderen Rang, der Alarmfall (kein Unterschied) liegt nicht vor"
  - "Die Praefixe helfen nur auf Deutsch; auf Englisch und Franzoesisch liegt die Fassung ohne leicht vorne, alle drei Unterschiede liegen unter ihrem Standardfehler. Sie bleiben trotzdem an, weil das Modell mit ihnen trainiert ist und Deutsch die Hauptsprache ist"
  - "D-02 ist gespalten beantwortet: die selbst quantisierte int8-Fassung traegt auf Deutsch (+2,30 Prozent MRR) und Englisch (+5,70 Prozent) und traegt auf Franzoesisch nach der Abbruchregel dieses Plans nicht (-9,24 Prozent)"
  - "Die Abbruchregel ist angewandt: der Plan endet mit diesem Befund, die drei offenen Wege stehen im Messbericht, die Entscheidung gehoert dem Owner"
  - "Die Vektorquantisierung kostet auf diesem Testset nichts Messbares: keiner der sechs Vergleiche erreicht den doppelten Standardfehler"
  - "Die lokal erzeugte int8-Datei ist byteidentisch mit der im Abbild; gemessen wurde das ausgelieferte Artefakt und nicht seine Nachbildung"
  - "Die absoluten Werte dieses Testsets sind eine Untergrenze und nicht mit NDCG@10 auf MIRACL vergleichbar; der Bericht sagt das ausdruecklich"

patterns-established:
  - "Ein Gatter bekommt seinen Gegenbeweis: die Wortueberschneidungsregel wird im Testlauf rot gefahren, und die franzoesische Elision wird als Schlupfloch ausdruecklich geschlossen"
  - "Eine Abbruchregel wird angewandt statt umgangen, und der Bericht liefert zusaetzlich, was gegen eine ueberstuerzte Reaktion spricht"

requirements-completed: [SEM-01]

# Metrics
duration: 3h05m
completed: 2026-09-05
---

# Phase 6 Plan 03: Modellqualität dreisprachig Summary

**Ein dreisprachiges Testset aus 126 Umschreibungen ohne Wortüberschneidung, ein Messwerkzeug, das nichts von dem druckt, was es liest, und fünfzehn Läufe, die D-05 positiv und D-02 gespalten beantworten: die selbst quantisierte int8-Fassung trägt auf Deutsch und Englisch und reißt auf Französisch mit -9,24 Prozent MRR die 5-Prozent-Abbruchregel dieses Plans.**

## Performance

- **Duration:** rund 3 h 05 min
- **Started:** 2026-09-05T04:00:00Z
- **Completed:** 2026-09-05T07:05:00Z
- **Tasks:** 3 von 3
- **Files modified:** 9 (7 neu, 2 geändert)

## Accomplishments

- **Die Phase hat zum ersten Mal eine eigene Zahl statt einer fremden.** Elastic misst für Deutsch +0,17 Prozent, für Französisch gar nichts. Wir messen jetzt für alle drei Sprachen, mit unserem Verfahren, auf unserem Artefakt, und die französische Zahl fällt anders aus als die Analogie erwarten ließ. Genau dafür war der Plan da.
- **Das teuerste stille Versagen eines Testsets ist maschinell ausgeschlossen.** Kein inhaltstragendes Wort einer Anfrage steht wörtlich in ihrem Abschnitt; ein Test setzt das über 126 Fälle durch, nennt bei einem Verstoß die Kennung und nie den Text, und ist im Testlauf rot gefahren worden. Die französische Elision, das offensichtliche Schlupfloch, hat einen eigenen Test.
- **Die zwei Quantisierungsstufen stehen getrennt in einer Tabelle.** Sie werden regelmäßig verwechselt; hier ist gemessen, dass die Modellstufe die interessante ist und die Vektorstufe auf diesem Satz nichts kostet, in keiner der sechs Kombinationen.
- **Das gemessene Artefakt ist das ausgelieferte.** Die für den Vergleich lokal erzeugte int8-Datei hat dieselbe sha256 wie die im Abbild aus Plan 06-01. Damit ist `quantize_dynamic` über zwei Maschinen und zwei Zeitpunkte hinweg reproduzierbar, und die Zahlen gelten für das, was Nutzer bekommen.

## Task Commits

1. **Task 1: Das dreisprachige Testset und die Regel, die es ehrlich hält** - `87a071f` (test)
2. **Task 2: Das Messwerkzeug für fp32 gegen int8 und für die Präfixe** - `f25f270` (feat)
3. **Abweichung in Task 3: `--per-case` für die paarweise Auswertung** - `60053ca` (feat)
4. **Task 3: Fünfzehn Läufe, beide Verdikte, der Befund** - `792c934` (docs)

## Files Created/Modified

- `testdata/semantik/de.jsonl`, `en.jsonl`, `fr.jsonl` - je 42 Fälle mit `id`, `query`, `passage`, `note`; die Passagenmenge einer Sprache ist zugleich ihre Ablenkermenge
- `testdata/semantik/README.md` - Zweck, die Wortüberschneidungsregel mit Begründung, Format, Fallzahl je Sprache, Herkunft und Lizenz je Quelle, und die ausdrückliche Aussage, dass keine echten personenbezogenen Daten enthalten sind
- `scripts/dev/model_quality.py` - fünf Pflichtschalter plus `--per-case`; Ausgabe ausschließlich Zahlen, Pfade und Kennungen; drei benannte Verweigerungen mit Exitcode 2
- `backend/tests/test_model_quality.py` - 36 Tests: Wohlgeformtheit, Eindeutigkeit, Fallzahl, die Regel und ihre Rotfähigkeit, Umlaute und Akzente, Strichverbot, dazu Rangarithmetik, Gleichstandsbehandlung, Kennzahlen, Berichtsform, die drei Fehlerpfade und die Textfreiheit der Ausgabe
- `docs/measurements/2026-09-05-modellqualitaet/README.md` - Umgebung, Abbildkennung, beide Modellprüfsummen, die exakte Kommandozeile, drei Tabellen mit je vier Kombinationen, die Elastic-Spalte mit drei Vorbehalten, zwei paarweise Auswertungen, das Präfix-Verdikt, der Befund mit drei offenen Wegen
- `.planning/STATE.md`, `.planning/ROADMAP.md` - Position, vier Entscheidungen, ein Blocker

## Die Zahlen in Kurzform

MRR, alle mit Präfixen an, relative Änderung gegenüber fp32-Modell mit fp32-Vektoren:

| Sprache | fp32/fp32 | fp32/int8 | int8/fp32 | int8/int8 |
|---|---|---|---|---|
| Deutsch | 0,6398 | 0,6351 (-0,73) | **0,6545 (+2,30)** | 0,6419 (+0,33) |
| Englisch | 0,4647 | 0,4750 (+2,22) | **0,4912 (+5,70)** | 0,4880 (+5,01) |
| Französisch | 0,4926 | 0,4913 (-0,26) | **0,4471 (-9,24)** | 0,4815 (-2,25) |

Präfixe an gegen aus, int8-Modell, fp32-Vektoren:

| Sprache | MRR mit | MRR ohne | Fälle mit anderem Rang |
|---|---|---|---|
| Deutsch | 0,6545 | 0,6243 | 21 von 42 |
| Englisch | 0,4912 | 0,5014 | 29 von 42 |
| Französisch | 0,4471 | 0,4760 | 31 von 42 |

## Der Befund, und warum er kein Alarm ist

Die Abbruchregel des Plans liegt bei 5 Prozent relativem MRR-Rückgang der
int8-Modellfassung in einer der drei Sprachen. Französisch liegt bei
-9,24 Prozent. **Der Plan endet deshalb mit diesem Befund und nicht mit einem
grünen Haken; die Entscheidung gehört dem Owner.** Die drei Wege stehen im
Messbericht: eine andere Quantisierungsachse, die fp32-Datei im Abbild mit ihrem
Speicherpreis, oder eine kleinere Zusage im Store-Text.

Was der Bericht ebenso festhält, weil es wahr ist und weil eine überstürzte
Reaktion teurer wäre als der Befund:

- Der Rückgang ist keine einzelne Ausreißerzeile: 16 von 42 Fällen werden
  schlechter, 9 besser. Er ist aber mit t = -2,03 auch nur gerade eben von Null
  zu unterscheiden.
- Die ausgelieferte Kombination int8-Modell mit int8-Vektoren steht auf
  Französisch bei -2,25 Prozent, also unter der Grenze. Die Regel bezieht sich
  ausdrücklich auf die Modellfassung bei fp32-Vektoren, und dort ist sie
  gerissen. Beides steht da.
- Der billigste nächste Schritt ist kein Umbau, sondern mehr französische Fälle:
  120 statt 42 würden den Standardfehler etwa halbieren.

## Decisions Made

- **D-05 ist beantwortet und positiv.** Die Präfixe verändern die Rangfolge in großem Umfang. Plan 06-05 muss sie setzen, und dieser Bericht ist der Beleg dafür, dass ein Vergessen sichtbar wäre.
- **Die Präfixe bleiben an, obwohl sie nur auf Deutsch helfen.** Zwei Gründe, beide unabhängig von den Zahlen: das Modell ist mit ihnen trainiert, und Deutsch ist die Hauptsprache des Produkts. Ein Abschalten wäre eine Abweichung vom Modellvertrag, gestützt auf drei Unterschiede, die die Stichprobe nicht trägt.
- **Die Vektorquantisierung ist entlastet.** Sechs Vergleiche, keiner erreicht den doppelten Standardfehler, die Vorzeichen wechseln zwischen den Sprachen. Elastics 1,05 Prozent für diese Stufe wird nicht widersprochen. Für Plan 06-04 heißt das: int8 in vec0 ist keine offene Frage mehr.
- **Die absoluten Werte sind eine Untergrenze.** Recall@1 zwischen 0,26 und 0,55 auf einem Satz, der lexikalische Treffer ausdrücklich verbietet. Im Betrieb steht die Tantivy-Liste daneben und gewinnt genau die Fälle, die hier verboten sind. Der Bericht sagt ausdrücklich, dass ein Vergleich mit NDCG@10 auf MIRACL zwei verschiedene Dinge vergleicht.
- **20 der 42 deutschen Abschnitte stammen wörtlich aus `build_corpus.py`.** Damit steht auch für die Herkunftsfrage eine Antwort statt einer Behauptung: die dortige Prosa ist erfunden, das ist im Kopf jener Datei als Regel festgehalten, und kein Text in `testdata/semantik` stammt aus einem heruntergeladenen Bestand.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktion] `--per-case`, ohne das die Abbruchregel nicht lesbar ist**

- **Found during:** Task 3, nach den ersten zwölf Läufen
- **Issue:** Der französische Wert riss die Abbruchregel. Ein Verdikt dieses Gewichts auf zwei zusammenfassende Dezimalzahlen zu stützen, wäre genau die Art von Aussage, gegen die dieser Plan geschrieben ist: über 42 Fälle ist eine MRR-Differenz von 0,046 nicht interpretierbar, solange niemand weiß, ob sich ein Fall bewegt hat oder fünfundzwanzig. Das Werkzeug lieferte nur die fünf schlechtesten Ränge.
- **Fix:** Ein zusätzlicher Schalter `--per-case`, der den Rang jedes Falles nennt, weiterhin ausschließlich als Kennung und ganze Zahl. Damit sind die paarweisen Auswertungen im Bericht (mittlere Differenz der Kehrwerte, Standardfehler, t, Zahl der bewegten Fälle) reproduzierbar statt behauptet. `worst_cases` leitet sich seitdem aus derselben Liste ab statt getrennt berechnet zu werden.
- **Files modified:** scripts/dev/model_quality.py, backend/tests/test_model_quality.py
- **Verification:** Der Textfreiheitstest läuft seitdem gegen die vollständige Fallliste statt gegen fünf Einträge; ruff, pyright, vulture und die 36 Tests der Suite grün.
- **Committed in:** `60053ca`

### Abweichungen, die keine Autoreparatur sind

**2. Die Fallzahl liegt bei 42 statt bei den geforderten 40 je Sprache**

Der Plan verlangt mindestens 40. Es sind 42 geworden, in allen drei Sprachen
gleich, weil die Gattungen sich so gleichmäßig aufteilen ließen. Der Test prüft
weiterhin gegen die Untergrenze 40, das README nennt die tatsächliche Zahl, und
ein weiterer Test hält beide aneinander.

**3. Der Bericht enthält zwei Auswertungen, die der Plan nicht verlangt**

Die beiden paarweisen Tabellen (Standardfehler, t, Zahl der bewegten Fälle) sind
im Plan nicht vorgesehen. Sie stehen dort, weil die Abbruchregel gerissen ist
und ein Befund, der eine Owner-Entscheidung auslöst, seine eigene Belastbarkeit
mitliefern muss. Ohne sie sähe -9,24 Prozent nach einer festen Zahl aus, und
das ist sie bei 42 Fällen nicht.

---

**Total deviations:** 1 autorepariert (fehlende kritische Funktion), 2 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Die Erweiterung des Werkzeugs war die Voraussetzung dafür, dass das Verdikt dieses Plans überhaupt eine Grundlage hat.

## Issues Encountered

- **Die absoluten Zahlen sind niedriger, als eine Analogie zu MIRACL erwarten ließe**, und das ist kein Fehler, sondern der Zuschnitt des Testsets: 42 Ablenker und ein ausdrückliches Verbot lexikalischer Brücken. Der Bericht hat dafür einen eigenen Absatz bekommen, weil diese Zahlen sonst irgendwann neben einer NDCG-Zahl stehen und niemand mehr weiß, dass sie nicht vergleichbar sind (T-06-12).
- **onnxruntime schreibt in jedem Lauf eine Telemetriezeile nach stderr**, auch mit abgeklemmtem Netzwerk. Es ist ein fehlgeschlagener lokaler Schreibversuch und kein Netzwerkverkehr; im Bericht festgehalten und an Plan 06-10 (Offline-Test) weitergereicht, weil eine solche Zeile im Store-Kontext falsch gelesen werden kann.
- **Der Bind-Mount unter Git Bash braucht weiterhin `MSYS_NO_PATHCONV=1`**, dieselbe Beobachtung wie in Plan 06-01. Steht in der Kommandozeile des Berichts.

## Offene Verifikation

Keine. Alle Läufe sind ausgeführt, alle Zahlen stehen im Bericht, und das
gemessene Artefakt ist über seine sha256 als das ausgelieferte ausgewiesen. Was
offen ist, ist keine Verifikation, sondern eine Entscheidung: der französische
Befund liegt beim Owner.

## User Setup Required

**Eine Owner-Entscheidung, keine Konfiguration.** Der Messbericht unter
`docs/measurements/2026-09-05-modellqualitaet/README.md` legt den französischen
Befund und drei mögliche Wege vor. Bis dahin bleibt alles, wie es ist: das
int8-Modell im Abbild, die Präfixe an, int8-Vektoren in vec0.

## Next Phase Readiness

- **Plan 06-05 kann den Modell-Wrapper bauen.** Die Präfixe sind nachweislich wirksam und gehören gesetzt; dass sie auf Englisch und Französisch auf diesem Satz nicht helfen, ist als Beobachtung notiert und nicht als Auftrag.
- **Plan 06-04 hat eine Sorge weniger.** int8-Vektoren in vec0 kosten auf diesem Testset nichts Messbares, in keiner der sechs Kombinationen.
- **Der Store-Text (D-17) hat jetzt eine Grundlage und eine offene Stelle.** Die Qualitätsaussage für Deutsch und Englisch ist belegt; die für Französisch hängt an der Owner-Entscheidung.
- **Ein Blocker, benannt und in STATE.md eingetragen:** die D-02/D-03-Entscheidung zum französischen Rückgang.

## Self-Check: PASSED

Alle sieben angelegten Dateien liegen auf der Platte, alle vier Commits stehen
in `git log`. Zusätzlich geprüft: `ruff check`, `ruff format --check`, `pyright`
und `vulture` grün über `backend` und über `scripts/dev/model_quality.py`, die
volle Suite mit 1057 bestandenen und 11 übersprungenen Tests grün, und die
Verifikationszeile des Plans über den Messbericht (alle sechs Schlüsselbegriffe
vorhanden, 357 Tabellenstriche, kein Geviert- und kein Halbgeviertstrich).

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
