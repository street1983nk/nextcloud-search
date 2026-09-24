---
phase: 18-schema-marken-und-umbauweg
plan: 04
subsystem: testing
tags: [tantivy, snowball, analyzer, parse_query_lenient, language-cases, fixtures]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: gemessene Formfamilien-Fixtures (chain_cases_*.txt), chain_probe.py als einziger Fixture-Leser, snowball_analyzer
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-01: SCHEMA_VERSION 2, dreizehn Felder mit BODY_FIELD, acht bedingungslos registrierte Ketten"
provides:
  - Vier Sprachfaelle auf Feldebene (es, it, nl, pt) gegen body_es, body_it, body_nl, body_pt
  - Ein in der Suite bewiesenes Auswahlkriterium fuer Wortpaare (die englische Kette darf das Paar nicht selbst zusammenfuehren)
  - Gegenprobe gegen das leere body_en und eine Fremdbestands-Assertion je Fall
  - Term-Woerterbuch-Gate: das Feld traegt die Terme seiner eigenen Kette, nicht die der englischen
affects: [19-frageseite-und-ranking, 20-sprachumbau, release-haertung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Searcher.terms_with_prefix(field, '') als Beweis, welche Kette ein Feld wirklich geschrieben hat"
    - "Testfall waehlt sein Wortpaar aus der Messfixture statt es als Literal zu tragen; ein Test haelt die Literalfreiheit"

key-files:
  created:
    - backend/tests/test_language_cases_field_level.py
  modified: []

key-decisions:
  - "Die Aussagekraft eines Sprachfalls ist eine Assertion, keine Kommentarzeile: je Paar wird geprueft, dass die englische Kette es nicht selbst zusammenfuehrt"
  - "Italienisch bekommt das schwaechere Kriterium, weil die vierzehn gemessenen it-Familien reine Akzentpaare sind; die Ausnahme ist gegen die Fixture abgesichert und faellt rot, sobald eine Flexionsfamilie dazukommt"
  - "Das Paar wird nicht benannt, sondern nach Regel aus der Fixture gezogen (erstes Paar, das das Kriterium erfuellt)"
  - "Zusaetzlich zum Trefferbeweis wird das Term-Woerterbuch des Feldes gegen die eigene und gegen die englische Kette gehalten"

patterns-established:
  - "Fremdbestand: ein Fall laeuft auf einem eigenen Index mit drei Dokumenten EINER Sprache; die fuenf anderen body-Felder sind per Assertion leer"
  - "Feldebene: parse_query_lenient(..., default_field_names=[BODY_FIELD[code]]), nie ueber build_query, solange die Frageseite zu ist"
  - "Index im Test ausschliesslich ueber open_index; grep -c 'Index(' meldet 0"

requirements-completed: [LEX-08]

# Metrics
duration: 27min
completed: 2026-09-24
---

# Phase 18 Plan 04: Sprachfaelle auf Feldebene Summary

**Vier parametrisierte Sprachfaelle (es, it, nl, pt) fragen mit `parse_query_lenient` direkt gegen `body_<code>` und finden das Dokument, das nur die andere Wortform traegt, auf einem Index ohne Fremdbestand, mit Gegenprobe gegen das leere `body_en` und mit einem Term-Woerterbuch-Gate, das die Kette des Feldes benennt.**

## Performance

- **Duration:** 27 min
- **Started:** 2026-09-24T05:18:00Z
- **Completed:** 2026-09-24T05:45:00Z
- **Tasks:** 2
- **Files modified:** 1 (neu)

## Accomplishments

- `backend/tests/test_language_cases_field_level.py` mit 36 Faellen, alle gruen; volle Suite 2592 passed / 15 skipped.
- Das Wortpaar je Sprache kommt aus `backend/tests/fixtures/chain_cases_<code>.txt` und steht nirgends als Literal in der Testdatei; ein eigener Test haelt diese Linie (T-18-04-02).
- Die Aussagekraft jedes Paares ist Teil der Suite: fuer es, nl und pt ist per Assertion gezeigt, dass die englische Kette die beiden Formen auf zwei verschiedene Terme legt (T-18-04-01); fuer alle vier Sprachen ist gezeigt, dass die englische Kette andere Terme schreiben wuerde.
- Jeder Fall laeuft auf einem eigenen Index mit drei Dokumenten genau einer Sprache; dass die fuenf anderen body-Felder leer sind, ist eine Assertion und keine Absicht (Lehre A4 aus v1.1).
- Rot-Beweis erbracht: mit `field = FIELD_BODY_EN` statt `BODY_FIELD[code]` fallen alle vier Faelle (`assert [] == [1, 2]`).
- `backend/src/` unberuehrt; `git diff --stat backend/src/` ist leer, die Ratsche bleibt bei 18-02.

## Task Commits

1. **Task 1: Wortpaare auswaehlen, die nur die Zielkette zusammenfuehrt** - `1b6c772` (test)
2. **Task 2: Vier Sprachfaelle gegen das Feld, ohne Fremdbestand** - `9d0597a` (test)

## Files Created/Modified

- `backend/tests/test_language_cases_field_level.py` (neu, 458 Zeilen) - Auswahl der vier Wortpaare aus den Messfixturen, ihre Aussagekraft als Assertion, und die vier Feldfaelle samt Gegenprobe, Fremdbestands-Gate und Term-Woerterbuch-Gate.

## Die vier gewaehlten Paare

Die Paare werden zur Laufzeit aus der Fixture gezogen (erstes Paar in Fixture-Reihenfolge, das das Kriterium erfuellt), stehen also nicht im Code. Was die Regel heute liefert:

| Sprache | Paar (Klasse) | Zielkette | Englische Kette | Kriterium |
|---|---|---|---|---|
| es | -es-Plural gegen feminines Singular des Adjektivs fuer "deutsch" | ein Stamm | zwei Terme | stark (getrennt) |
| nl | Infinitiv gegen Partizip des Verbs fuer "beeinflussen" | ein Stamm | zwei Terme | stark (getrennt) |
| pt | Substantiv fuer "Land", Singular gegen Plural | ein Stamm | zwei Terme | stark (getrennt) |
| it | Substantiv fuer "Qualitaet", akzentuiert gegen flach | ein Stamm | ein anderer Term als der der Zielkette | schwach (gefaltet) |

Der dritte Dokumenttext je Index ist ein Ablenker aus derselben Fixture, den die Kette auf einen anderen Term legt, damit eine Abfrage, die alles findet, nicht wie eine Abfrage aussieht, die den Fall trifft.

## Decisions Made

- **Auswahl per Regel statt per Hand.** Der Fall nimmt das erste Paar der Fixture, das das Kriterium erfuellt. Waechst eine Fixture, waechst der Fall mit, ohne dass jemand eine Wortliste pflegt.
- **Zwei Kriterien statt eines.** Das starke Kriterium ("die englische Kette haelt die beiden Formen auseinander") ist das, das die fehlgeschlagene Sonde vom 24.09. gebraucht haette. Das schwaechere ("die englische Kette wuerde andere Terme schreiben") faengt die Sprache auf, deren Fixture keine Flexionspaare kennt, und wird zusaetzlich am echten Term-Woerterbuch des Feldes gemessen.
- **`Searcher.terms_with_prefix(field, "")` als Beweismittel.** Es beantwortet zwei Fragen in einem Aufruf: welche Terme das Feld wirklich traegt (also welche Kette es geschrieben hat) und ob ein anderes body-Feld Bestand hat.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Das Abnahmekriterium "englische Kette legt das Paar auf zwei Terme" ist fuer Italienisch mit der gemessenen Fixture unerfuellbar**

- **Found during:** Task 1 (Wortpaare auswaehlen)
- **Issue:** Der Plan verlangt fuer JEDES der vier Paare die Assertion, dass die englische Kette die beiden Formen auf zwei verschiedene Terme legt. Eine Auswertung aller Paare aller vier Fixturen gegen die ausgelieferten Ketten zeigt: es hat 2, nl 7, pt 4 solche Paare, **it hat 0**. Grund: die vierzehn italienischen Familien der Messung vom 23.09. sind ausnahmslos Akzentpaare (akzentuiert gegen flach), und beide Ketten falten vor dem Stemmer, also sind die beiden Formen nach der Faltung dieselbe Zeichenkette. Ein Paar hinzuerfinden war ausgeschlossen (Paare muessen aus der Messfixture kommen), eine Familie zur Fixture hinzufuegen ebenso: `test_language_analyzers.py` haelt `EXPECTED_FAMILY_SCORES` fuer it auf gemessene 56 von 56 Paaren, und eine neue Familie waere eine ungemessene Zahl.
- **Fix:** Zwei ausgewiesene Staerkeklassen. `SEPARATED = ("es", "nl", "pt")` traegt die vom Plan geforderte Assertion unveraendert. `FOLDED = ("it",)` traegt statt dessen die Assertion, dass die englische Kette fuer dieses Paar ANDERE Terme schreiben wuerde, und zusaetzlich das Term-Woerterbuch-Gate am Index: die Terme von `body_it` sind genau die der italienischen Kette und nicht die der englischen. Die Ausnahme ist nicht behauptet, sondern gemessen: `test_the_fixture_of_a_folded_language_offers_no_such_pair` faellt rot, sobald die italienische Fixture ein Flexionspaar bekommt, und fordert dann die Hochstufung.
- **Files modified:** backend/tests/test_language_cases_field_level.py
- **Verification:** 36 Faelle gruen; der Klassifikationstest haelt die Einteilung gegen die Fixturen, nicht gegen den Autor.
- **Committed in:** `1b6c772` (Task 1) und `9d0597a` (Task 2, Term-Woerterbuch-Gate)

**2. [Rule 2 - Missing Critical] Term-Woerterbuch-Gate am Index ergaenzt**

- **Found during:** Task 2 (Feldfaelle)
- **Issue:** Der Trefferbeweis allein haelt T-18-04-01 nur fuer die drei getrennten Sprachen. Waere `body_it` versehentlich mit der englischen Kette registriert, liefen Schreiben und Fragen durch dieselbe falsche Kette, das Paar wuerde trotzdem zusammenfinden und der Fall waere gruen aus dem falschen Grund.
- **Fix:** `test_the_field_carries_the_terms_of_its_own_chain` liest die Terme des Feldes mit `Searcher.terms_with_prefix(field, "")` und haelt sie gegen die Terme, die die Kette der Sprache fuer dieselben drei Texte erzeugt, sowie dagegen, dass die englische Kette dieselben Terme schreiben wuerde.
- **Files modified:** backend/tests/test_language_cases_field_level.py
- **Verification:** vier Faelle gruen; beim Rot-Beweis auf `body_en` faellt der Trefferfall zusaetzlich.
- **Committed in:** `9d0597a`

---

**Total deviations:** 2 auto-fixed (1 blockierendes Abnahmekriterium, 1 fehlende kritische Absicherung)
**Impact on plan:** Kein Scope-Zuwachs ausserhalb der Plandatei. Das Ziel von LEX-08 (ein belastbarer Sprachfall je Sprache auf Feldebene) ist erfuellt; fuer Italienisch traegt der Beweis nachweislich ueber das Term-Woerterbuch statt ueber die Trennung, und diese Schwaeche ist ausgewiesen statt versteckt.

## Issues Encountered

- `ruff format` hat zwei Zeilen der neuen Datei umgebrochen; nachformatiert, danach alle vier Gates gruen.
- Eine zunaechst eingefuehrte Konstante `DISTRACTOR_DOCUMENT` blieb ungenutzt (vulture meldet das bei min_confidence 80 nicht) und wurde vor dem Commit entfernt.

## Verification

- `uv run python -m pytest -q tests/test_language_cases_field_level.py` : 36 passed
- `uv run python -m pytest -q` : 2592 passed, 15 skipped
- `uv run ruff check` / `ruff format --check` / `pyright` / `vulture` : alle gruen
- `grep -c "Index(" backend/tests/test_language_cases_field_level.py` : 0
- Rot-Beweis: `field = FIELD_BODY_EN` statt `BODY_FIELD[code]` laesst alle vier Faelle fallen (`assert [] == [1, 2]`), danach zurueckgestellt
- `git diff --stat backend/src/` : leer

## TDD Gate Compliance

Task 2 traegt `tdd="true"`. Der Plan ist ein reiner Testplan, es gibt also keine Produktaenderung, die eine `feat`-Stufe traegt; beide Commits sind `test`. Die RED-Stufe wurde als der vom Plan geforderte Gegenbeweis gefahren: der Fall auf `body_en` umgestellt, alle vier Sprachen rot, dann zurueck auf `BODY_FIELD[code]` und gruen. Es fehlt bewusst ein `feat`-Commit; ein solcher haette `backend/src/` beruehrt, was dieser Plan ausdruecklich nicht darf.

## Known Stubs

Keine.

## Threat Flags

Keine. Der Plan legt keine Netzstrecke, keinen Rechtepfad und keine Schemaaenderung an; es entsteht nur eine Testdatei.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 19 kann die Frageseite oeffnen: das Term-Woerterbuch-Gate und die Fremdbestands-Assertion sind das Muster, an dem sich ein spaeterer Rangbeweis messen lassen muss (Rang bewusst nicht Teil dieses Plans).
- Sollte eine spaetere Messung die italienische Fixture um eine Flexionsfamilie erweitern, meldet sich `test_the_fixture_of_a_folded_language_offers_no_such_pair` von selbst und fordert die Hochstufung des it-Falls.

## Self-Check: PASSED

- `backend/tests/test_language_cases_field_level.py` vorhanden (458 Zeilen)
- `.planning/phases/18-schema-marken-und-umbauweg/18-04-SUMMARY.md` vorhanden
- Commits `1b6c772` und `9d0597a` in der Historie gefunden

---
*Phase: 18-schema-marken-und-umbauweg*
*Completed: 2026-09-24*
