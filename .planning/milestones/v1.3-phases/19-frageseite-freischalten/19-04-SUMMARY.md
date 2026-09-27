---
phase: 19-frageseite-freischalten
plan: 04
subsystem: api
tags: [ranking, feld-boosts, bm25, tantivy, gegenprobe, messung]

# Dependency graph
requires:
  - phase: 19-frageseite-freischalten
    provides: "FieldPlan, BODY_BOOST, build_query(plan=...) aus 19-01; field_plan_for(marks, index) aus 19-03"
  - phase: 18-schema-und-umbau
    provides: "Dreizehn-Felder-Schema mit sechs Koerperfeldern, open_index registriert alle sechs Ketten"
provides:
  - "backend/tests/test_field_plan_ranking.py: die Rangprobe zu Erfolgskriterium 3, acht Faelle"
  - "TIPPING_BOOST = 0.81: die gemessene Grenze, ab der der Rang kippt, datiert im Modulkopf"
  - "Der Nachweis, dass die ausgelieferte 0.6 mit Abstand 0.21 unterhalb dieser Grenze liegt"
affects: [19-09 Doku der Frageseite, 22 Messphase (MESS-09, disjunction_max-Entscheid)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Rangzusicherung ohne Gegenprobe ist auch fuer einen Index gruen, in dem der Vergleichsfall nicht eintritt"
    - "Die Probe wird auf die Uneinigkeit der Ketten gebaut, weil nur dort die Verzerrung lebt"
    - "Eine Messzahl bleibt als Lauf in der Suite statt als Notiz im Kommentar"

key-files:
  created:
    - backend/tests/test_field_plan_ranking.py
  modified: []

key-decisions:
  - "BODY_BOOST bleibt bei 0.6: die Probe haelt, die gemessene Kippgrenze liegt bei 0.81"
  - "Das Wortpaar document/documents/documento teilt die sechs Ketten drei gegen drei und ist damit der einzige Ort, an dem die Mehrfeld-Summierung im Vergleich zweier Dokumente ueberhaupt sichtbar wird"
  - "Alle drei Dokumente tragen denselben Text in allen sechs Koerperfeldern, weil eine Probe mit einem Feld je Dokument eine Form messen wuerde, die niemand ausliefert"
  - "Die Kippgrenze wird als Sweep in der Suite gefahren statt einmal gemessen und hingeschrieben"

requirements-completed: []
# LEX-05 bleibt offen. 19-03 hat die erste Haelfte eingeloest (die Anfrage durchsucht genau die
# aktiven Felder), dieser Plan die zweite Haelfte des Boost-Satzes (die vier Gewichte liegen
# unterhalb body_en, und zwar belegt statt behauptet). Der Haken in REQUIREMENTS.md gehoert dem
# Plan 19-05, der das Anti-Feature "keine Spracherkennung" festhaelt; erst dann ist der ganze
# Satz von LEX-05 bewiesen.

# Metrics
duration: 35min
completed: 2026-09-24
---

# Phase 19 Plan 04: Rangprobe der Feld-Boosts Summary

**Erfolgskriterium 3 ist ab hier gemessen statt begruendet: der bessere englische Treffer steht auf einem echten Index mit sechs befuellten Koerperfeldern vor dem Dokument, das dieselbe Frage ueber drei Zusatzketten trifft, die Gegenprobe bei Boost 1,0 kippt ihn, und die Grenze dazwischen liegt bei 0,81**

## Performance

- **Duration:** rund 35 min
- **Started:** 2026-09-24T21:05:00Z
- **Completed:** 2026-09-24T21:40:00Z
- **Tasks:** 2
- **Files modified:** 1 (neu)

## Accomplishments

- `backend/tests/test_field_plan_ranking.py` existiert mit 411 Zeilen und acht bestandenen
  Faellen. Der Modulkopf traegt in dieser Reihenfolge: was schiefgeht (tantivy summiert die
  Feldbeitraege), die Messreihe M-3 als Zahlentabelle mit den vier Zeilen
  `0.1823 / 2.1500 / 1.3264 / 0.5394`, den realen Fall (derselbe Text geht in alle
  eingeschalteten Felder, die Multiplikation kuerzt sich im Vergleich zweier Dokumente
  weitgehend heraus), was die Datei beweist, die Zahl fuer Phase 22 und was die Datei
  ausdruecklich nicht beweist.
- Der Probenindex ist ein echtes Verzeichnis ueber `open_index`, drei Dokumente, und jedes
  Dokument traegt seinen Text in allen sechs Koerperfeldern, genau wie `index/writer.py` auf
  einer Sechs-Sprachen-Instanz schreibt.
- Die Verzerrung wird an der einzigen Stelle gebaut, an der sie im Vergleich zweier Dokumente
  ueberhaupt lebt: die Frage `document` legen die Ketten de, en und nl auf Dokument A
  (Schreibweise `documents`), die Ketten es, it und pt auf Dokument B (Schreibweise
  `documento`). Das ist je Feld zugesichert und nicht angenommen.
- Die strukturelle Zusage von Erfolgskriterium 3 steht doppelt: einmal auf den ausgelieferten
  Zahlen (`BODY_BOOST[es|it|nl|pt] < BODY_BOOST[en] < BODY_BOOST[de]`) und einmal ueber jeden
  erzeugbaren Plan, also alle 63 nicht leeren Sprachmengen durch `field_plan_for` gegen den
  echten Index, mit 64 einzelnen Vergleichen und einem Zaehler, der eine stumm abgebrochene
  Schleife auffliegen laesst.
- Die Rangprobe selbst laeuft ueber `build_query` mit dem Plan, den `field_plan_for` fuer eine
  Instanz mit allen sechs Sprachen liefert, und liest die Reihenfolge nach dem Muster von
  `_unfiltered_order` vom Searcher ab: `[1, 2]`, also A vor B.
- Die Gegenprobe kippt: mit den vier Zusatzgewichten auf 1,0 liefert dieselbe Suche `[2, 1]`.
  Der Lauf wurde einmal von Hand invertiert, siehe Verification.
- Die Zahl fuer Phase 22 ist ermittelt und als benannte Konstante mit Messdatum im Modulkopf
  festgehalten: **`TIPPING_BOOST = 0.81`**, gemessen am 24.09.2026 gegen tantivy 0.26.2 durch
  einen Sweep ueber 101 Werte (0,00 bis 1,00 in Hundertsteln, alles ausser den vier Gewichten
  stillgehalten). Der Sweep bleibt als Fall in der Suite stehen.
- `BODY_BOOST` ist NICHT gesenkt worden: die ausgelieferten 0,6 liegen 0,21 unterhalb der
  Kippgrenze, die Probe haelt also mit Abstand und nicht knapp. Damit beruehrt dieser Plan keine
  Datei unter `backend/src/findling`, und `PACKAGE_TREE_HASH_TODAY` bleibt unberuehrt.

## Die Zahl, die Phase 22 braucht

| Groesse | Wert | Herkunft |
|---|---|---|
| Ausgelieferter Boost der vier Zusatzfelder | 0,6 | `BODY_BOOST` in `query/rewrite.py`, unveraendert |
| Gemessene Kippgrenze auf dieser Probe | **0,81** | Sweep in `test_the_boost_at_which_the_ranking_turns_over_is_this_one`, 24.09.2026, tantivy 0.26.2 |
| Abstand des ausgelieferten Werts zur Grenze | 0,21 | Zusicherung im selben Fall |
| Rechnerischer Schnittpunkt | 0,8094 | 1,8953 = t * (3,3223 - 0,9808), aus den Einzelfeld-Scores der Probe |

Die Einzelfeld-Scores derselben Probe, gemessen am 24.09.2026, weil sie die Grenze erklaeren:

| Feld | Dokument | BM25 |
|---|---|---|
| `body_de` | A | 0,9684 |
| `body_en` | A | 1,1586 |
| `body_nl` | A | 0,9808 |
| `body_es` | B | 1,1988 |
| `body_it` | B | 1,0682 |
| `body_pt` | B | 1,0553 |

A sammelt also 1,0 * 0,9684 + 0,8 * 1,1586 fest plus t * 0,9808, B sammelt t * 3,3223. Die
Grenze ist keine Eigenschaft des Produkts, sondern dieser drei Dokumente; was sie traegt, ist
die Richtung und die Groessenordnung.

## Task Commits

1. **Task 1: Der Probenindex und die strukturelle Zusicherung** - `459fc20` (test)
2. **Task 2: Die Rangprobe, ihre Gegenprobe und die gemessene Grenze** - `c4d7cbc` (test)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `backend/tests/test_field_plan_ranking.py` - NEU, 411 Zeilen, acht Faelle:
  `test_the_four_build_out_weights_lie_below_english_and_english_below_german`,
  `test_every_producible_plan_keeps_its_build_out_fields_below_english`,
  `test_the_two_hits_answer_the_question_through_chains_that_disagree`,
  `test_the_question_reaches_no_file_name_and_no_title`,
  `test_the_distractor_is_in_the_index_and_still_does_not_answer_the_question`,
  `test_the_better_english_hit_stands_before_the_three_chain_hit`,
  `test_the_same_ranking_turns_over_once_the_four_weights_reach_one`,
  `test_the_boost_at_which_the_ranking_turns_over_is_this_one`

## Decisions Made

- **Das Wortpaar ist gesucht und nicht erfunden.** Eine Sonde ueber 186 Woerter (die vier
  Fixture-Wortlisten `chain_cases_*.txt` plus eine englische Liste) hat alle Tripel aus Frage,
  A-Form und B-Form bestimmt, deren Trefferfeldmengen ein Fenster oeffnen, in dem der Rang
  ueberhaupt kippen kann. Gewaehlt wurde das breiteste: Frage `document`, A traegt `documents`
  (de, en, nl), B traegt `documento` (es, it, pt). Ein Paar, das die Ketten nicht spaltet, haette
  eine Probe ergeben, in der sich die Mehrfeld-Multiplikation vollstaendig herauskuerzt und in
  der die Gegenprobe nie kippt.
- **Derselbe Text in alle sechs Koerperfelder.** Die Sonde `probe19b` aus RESEARCH befuellte
  Dokument 2 nur im englischen Feld; das ergibt das 11,8-fache aus der Tabelle und ist eine Form,
  die kein Schreibpfad dieses Projekts erzeugt. Die Probe hier bildet
  `index/writer.py:286-293` nach, weil sonst die gemessene Grenze eine Grenze eines Aufbaus
  waere, den niemand ausliefert.
- **Die Kippgrenze bleibt ein Lauf, kein Kommentar.** Der Sweep kostet auf drei Dokumenten
  nichts messbares und haelt die Zahl im Modulkopf an den Code gebunden. Eine einmal gemessene und
  hingeschriebene Zahl waere ab dem naechsten Kettenumbau eine Erinnerung.
- **Keine Aenderung an `BODY_BOOST`.** Der Plan hat den Fall vorgesehen, dass die 0,6 nicht
  traegt; sie traegt. Ein Senken ohne Not waere eine Verhaltensaenderung an der Rangfolge jeder
  Instanz und haette die Ratsche und einen zweiten Begruendungsstrang nach sich gezogen.
- **`name` und `title` bleiben aus der Frage heraus.** Sie wiegen 3,0 und 2,0; ein `document` in
  einem der beiden haette den Rang entschieden, bevor ein Koerperfeld ueberhaupt gehoert worden
  waere. Ein eigener Fall sichert das zu, statt dass ein Kommentar es behauptet.

## Deviations from Plan

### Auto-fixed Issues

Keine. Der Plan wurde in zwei Commits ausgefuehrt, genau in der Reihenfolge und mit dem
Fussabdruck, den er nennt.

### Befunde, die der Plan nicht vorhergesehen hat

**Ein Paar, das die Ketten spaltet, ist selten, und ohne Suche haette die Probe nichts gemessen.**
Die erste, naheliegende Form der Probe (Dokument B traegt die Frage woertlich, Dokument A eine
englische Beugung davon) ist gemessen worden und taugt nicht: B trifft dann in allen sechs
Feldern und A in einem oder zweien, und die Gegenprobe braucht dafuer ein BM25-Verhaeltnis von
rund 6, das auf drei kurzen Dokumenten nicht herstellbar ist. Erst die Aufteilung drei gegen
drei oeffnet ein Fenster, in dem die ausgelieferten 0,6 halten UND die 1,0 kippen. Der Plan
rechnete mit dem Fall "0,6 traegt nicht"; der tatsaechliche Fall war "die Probe traegt nur mit
dem richtigen Wortpaar", und das ist im Modulkopf und in den Kommentaren am Wortpaar
festgehalten, damit ein spaeterer Leser nicht dieselbe Sackgasse laeuft.

**Die Probe selbst macht Erfolgskriterium 3 nicht wahrer als es ist.** Sie belegt: bei den
ausgelieferten Gewichten steht der bessere englische Treffer vorn, und die Gewichte sind der
Grund dafuer, weil der Rang kippt, sobald man sie hebt. Sie belegt nicht, dass die Summierung
beseitigt waere; die vier Zeilen der Messreihe M-3 stehen deshalb im Modulkopf und nicht in
einer Fussnote.

---

**Total deviations:** 0
**Impact on plan:** Kein Scope-Zuwachs, kein Fussabdruck ueber die eine neue Datei hinaus.

## Threat Flags

Keine. Der Plan legt keine Route an, oeffnet keinen Netzpfad, fasst keine Datei unter
`backend/src/findling` an und aendert weder `backend/pyproject.toml` noch `backend/uv.lock`
(T-19-04-SC damit mangels Gegenstand erfuellt). Die drei uebrigen Eintraege des Registers:

- **T-19-04-01 (Rangzusicherung ohne Gegenprobe):** umgesetzt.
  `test_the_same_ranking_turns_over_once_the_four_weights_reach_one` kippt den Rang, und
  `test_the_two_hits_answer_the_question_through_chains_that_disagree` sichert vorher je Feld
  zu, dass beide Dokumente ueberhaupt erreichbar sind. Zusaetzlich sichert
  `_multi_chain_hit_leads` in jedem Sweep-Schritt zu, dass beide Ids in der Antwort stehen.
- **T-19-04-02 (`BODY_BOOST` gesenkt, Ratsche nicht nachgezogen):** gegenstandslos, weil nicht
  gesenkt. Der Diff dieses Plans enthaelt genau eine Datei, und die liegt unter `backend/tests`.
- **T-19-04-03 (Laufzeit der Probe):** der Probenindex wird einmal je Modul gebaut
  (`scope="module"`), drei Dokumente, `tmp_path_factory`. Das ganze Modul laeuft in 4,9 s,
  darunter der Sweep mit 101 Suchen.

## Known Stubs

Keine.

## Issues Encountered

- Die zwei Prosastellen in `backend/src/findling/store/repo.py` (Zeilen 128 und 1448), die noch
  den in 19-01 gefallenen Namen `DEFAULT_FIELDS` nennen, sind erneut NICHT mitgenommen worden.
  Dieser Plan fasst `backend/src/findling` per Fussabdruck nicht an. Der Eintrag bleibt in
  STATE.md stehen.
- `backend/tests/test_language_cases_field_level.py` nennt denselben Namen in seinem Modulkopf
  nicht mehr falsch; 19-02 hat die Datei angefasst. Offen ist nur noch `store/repo.py`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **19-05 (Anti-Feature-Waechter)** ist unberuehrt und kann sofort laufen; dieser Plan hat weder
  eine Signatur noch einen Aufrufpfad bewegt.
- **19-06 (Sprachfaelle auf dem Suchweg)** bekommt aus diesem Modul ein brauchbares Muster
  mitgeliefert: der Probenindex zeigt, wie ein Index mit sechs befuellten Koerperfeldern gebaut
  wird und wie die Uneinigkeit der Ketten je Feld abgelesen wird. Der Haken aus RESEARCH Pattern
  4 bleibt bestehen und wird von diesem Modul bestaetigt: auf dem normalen Suchweg stehen alle
  aktiven Felder in der Liste, und ein Formenpaar, das die englische Kette selbst zusammenfuehrt,
  beweist dort nichts.
- **19-09 (Doku)** traegt `TIPPING_BOOST = 0.81` samt Messdatum und Methode nach
  `docs/language-analyzers.md`. Die Zahl und ihre Herleitung stehen im Modulkopf von
  `backend/tests/test_field_plan_ranking.py` und in der Tabelle oben.
- **Phase 22 (MESS-09)** hat ihren Startpunkt: der `disjunction_max`-Entscheid beginnt bei der
  Frage, wie weit die 0,21 Abstand auf echten Daten traegt. In diesem Plan ist
  `disjunction_max_query` bewusst nicht verwendet und nicht vorbereitet; der Name kommt genau
  einmal vor, in dem Kommentar, der die Vertagung nennt.

## Verification

- `uv run pytest -q` aus `backend/`: **2784 bestanden, 15 uebersprungen, 0 Fehlschlaege**
  (vorher 2776/15; acht Faelle dazu).
- `uv run pytest -q tests/test_field_plan_ranking.py --no-header`: 8 bestanden in 4,94 s.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 135 files already
  formatted. `uv run vulture src tests --min-confidence 80`: keine Befunde.
  `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- **Die Gegenprobe ist rot, wenn man sie invertiert, und das ist von Hand geprueft.** Eine Kopie
  des Moduls mit umgedrehter Zusicherung
  (`assert order == [ENGLISH_HIT, MULTI_CHAIN_HIT]` im Gegenprobenfall) lief einmal ausserhalb
  des Repos-Fussabdrucks und endete mit `assert [2, 1] == [1, 2]`, also rot. Die Kopie ist
  danach geloescht worden; `git status` ist sauber.
- Akzeptanzkriterien einzeln geprueft:
  - `backend/tests/test_field_plan_ranking.py` existiert, 411 Zeilen (Mindestmass 90), und die
    vier Zahlen der Messreihe M-3 stehen woertlich im Modulkopf.
  - `grep -c "BODY_BOOST"` und `grep -c "open_index"` zusammen 7 Zeilen, beide also mindestens 1.
  - `grep -c "tantivy.Index("` ist 0.
  - `grep -c "disjunction_max"` ist 1, und die Zeile ist ein Kommentar, der Phase 22 und
    REQUIREMENTS MESS-09 namentlich nennt.
  - Das Modul enthaelt einen Fall, der eine Reihenfolge zweier Dokument-Ids vergleicht
    (`order.index(ENGLISH_HIT) < order.index(MULTI_CHAIN_HIT)`), und einen, der dieselbe
    Reihenfolge unter Boost 1,0 als umgekehrt zusichert.
  - Der Modulkopf nennt eine datierte, benannte Zahl: `TIPPING_BOOST: Final = 0.81`, Messdatum
    und Methode im Kommentar darueber.
  - `BODY_BOOST` wurde nicht gesenkt, also enthaelt der Diff dieses Plans nur
    `backend/tests/test_field_plan_ranking.py`; `git show --stat` beider Commits bestaetigt das,
    und `backend/tests/test_measurement_scripts.py` ist unberuehrt.
- Kein Em-Dash und kein einziges Nicht-ASCII-Zeichen in der neuen Datei, maschinell geprueft.
  Zeilenenden durchgaengig CRLF wie im Rest von `backend/tests`.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-24*

## Self-Check: PASSED

`backend/tests/test_field_plan_ranking.py` liegt auf der Platte, beide Commits (`459fc20`,
`c4d7cbc`) stehen in der Historie, das Arbeitsverzeichnis trug vor diesem docs-Commit nichts
Offenes.
