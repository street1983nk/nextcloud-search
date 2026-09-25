---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 03
subsystem: l10n
tags: [gate-parametrisierung, katalog-gates, vsprintf, pluralverkettung, testnamen, doku-gate]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 01
    provides: "scan_placeholder_parity teilt zusammengesetzte Schluessel an _::_ und ist seitdem sprachunabhaengig"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "PLURAL_FORM_OF und FORM_COUNT_OF je Sprachcode, das Pluralregel-Gate ueber jede vorhandene Datei, docs/l10n-catalogues.md als gemeinsamer Beweis"
provides:
  - "VALUES_THAT_MAY_EQUAL_THEIR_KEY: Ausnahmen je Sprachcode statt einer globalen franzoesischen Liste, Grund je Eintrag"
  - "scan_completeness(name, catalogue, exceptions): dieselbe Funktion fuer jede Sprache, Ausnahmen als Parameter"
  - "language_code_of(path): die einzige Zuordnung Datei zu Sprachcode"
  - "scan_percent_discipline: jedes Prozentzeichen in Schluessel und jeder Form muss Teil einer erkannten Direktive sein"
  - "scan_pipe_character: kein Schluessel und keine Form traegt das Pluraltrennzeichen"
  - "test_no_catalogue_value_can_break_the_page: beide neuen Scanner ueber L10N_CATALOGUES, vier gestellte Zeilen"
  - "test_every_catalogue_value_carries_a_wording_of_its_language, test_no_catalogue_value_loses_or_invents_a_placeholder, test_every_catalogue_carries_the_same_keys: drei Gates ohne Sprachnamen und ohne Zahl im Namen"
  - "test_the_rule_table_of_the_documentation_and_the_constant_are_one_string: docs/l10n-catalogues.md und PLURAL_FORM_OF zeichengleich, dauerhaft gehalten"
affects: [20-04 bis 20-08 (jede neue Sprache braucht einen Eintrag in VALUES_THAT_MAY_EQUAL_THEIR_KEY, sonst faellt das Vollstaendigkeitsgate mit Namen), 20-09 (CI-Sprachbeweis laeuft gegen dieselben Gates)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Ausnahmeliste haengt am Sprachcode, nicht am Modul; eine Sprache ohne Liste ist ein Fehlschlag mit Namen und kein stilles leeres Mapping"
    - "Ein Gate, das eine kaputte Seite verhindert, zaehlt statt ein zweites Mal zu erkennen: die Zahl der %-Zeichen gegen die Zahl der von PRINTF_DIRECTIVE verbrauchten, damit es nur eine Definition einer Direktive gibt"
    - "Ein Gate ueber einen heute leeren Befund (null Pipes im Baum) braucht mehr gestellte Zeilen als eines ueber einen bewohnten, weil grueneres Gruen und geloeschter Rumpf gleich aussehen"
    - "Ein Testname traegt keine Zahl und keinen Sprachnamen, der bei der naechsten Datei nachgezogen werden muss; die Zahl steht in der Liste, die falsch sein und gesehen werden kann"
    - "Ein Beweisdokument und die Konstante, die aus ihm stammt, muessen einander falsch nennen koennen: sonst giesst ein verrutschtes Dokument zehn Dateien falsch und das Gate meldet zehn kaputte Kataloge"

key-files:
  created:
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-03-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "de und de_DE bekommen VIER begruendete Ausnahmen und nicht das leere Mapping, das der Plan erwartet hat. Der Baum ist am 25.09.2026 gelesen worden statt angenommen: Findling, %1$s in %2$s, PDF und Text sind in de.json und de_DE.json mit ihrem englischen Schluessel identisch. Ein leeres Mapping haette das Gate beim ersten Lauf rot gemacht"
  - "de_DE bindet auf den de-Eintrag statt ihn abzuschreiben. Zwei Kopien einer Liste sind zwei Dinge, die gleich bleiben muessen, und die Wortgleichheit der beiden deutschen Kataloge haelt bereits test_the_german_catalogue_covers_both_german_language_codes"
  - "Der Prozent-Scanner laeuft ausdruecklich auch ueber den Schluessel. Ein englischer Quellstring mit nacktem Prozentzeichen ist dieselbe kaputte Seite eine Ebene frueher und erreicht sie ueber de.json, bevor irgendeine Uebersetzung davon existiert"
  - "Der Zaehlvergleich statt eines zweiten Regex ist eine Entwurfsentscheidung und steht als solche im Docstring: ein zweites Muster fuer 'Prozentzeichen ohne Direktive' waere eine zweite Definition einer Direktive, und die beiden liefen an dem Tag auseinander, an dem jemand %1$d ergaenzt"
  - "test_the_six_files_of_the_two_pages_exist ist mit umbenannt worden, obwohl seine Sechs keine Kataloge zaehlt. Das Abnahmekriterium des Plans verlangt eine leere Liste ueber _six_, und der Grund traegt auch hier: eine dritte Seite braechte acht Pfade"
  - "Das Doku-Gate (Zeichengleichheit docs/l10n-catalogues.md gegen PLURAL_FORM_OF) ist gebaut worden, obwohl der Plan es nicht auffuehrt. Es steht als Auftrag in STATE.md, faellt in dieselbe Datei und schliesst eine echte Luecke: 20-04 bis 20-08 giessen zehn Dateien aus der Tabelle des Dokuments, und das Pluralregel-Gate urteilt gegen die Konstante"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-09-25
---

# Phase 20 Plan 03: Sprachunabhaengige Scanner und die zwei stillen Seitenzerstoerer Summary

**Die vier Katalog-Gates tragen kein Franzoesisch mehr im Namen und keine Ausnahmeliste mehr
im Modul, zwei neue Scanner halten die beiden Wortlaute fest, die nicht den Satz, sondern die
Seite kaputtmachen, und alles davon ist bewiesen, solange erst de, de_DE und fr existieren.**

## Was gebaut wurde

Eine einzige Datei ist angefasst worden, `backend/tests/test_admin_ui_contract.py`. Kein
Katalog, kein Template, kein Skript, kein Workflow.

**Die Ausnahmen haengen jetzt an der Sprache.**
`FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` ist `VALUES_THAT_MAY_EQUAL_THEIR_KEY` geworden, eine
Tabelle Sprachcode auf Mapping "Schluessel zu Grund". Der Absatz, der erklaert, warum das eine
benannte Liste und keine Toleranzschwelle ist, ist unverkuerzt mitgewandert und gilt jetzt
ausdruecklich fuer jede Sprache. `scan_french_completeness` ist
`scan_completeness(name, catalogue, exceptions)`, `language_code_of(path)` ist die einzige
Zuordnung Datei zu Code (`fr.json` zu `fr`, `pt_BR.js` zu `pt_BR`), und das Gate heisst
`test_every_catalogue_value_carries_a_wording_of_its_language` und laeuft ueber alle sechs
Dateien. Eine Sprache ohne Eintrag in der Tabelle ist ein Fehlschlag, der ihren Code nennt.

**Zwei neue Scanner.** `scan_percent_discipline` verlangt, dass jedes Prozentzeichen eines
Schluessels und jeder Form Teil einer von `PRINTF_DIRECTIVE` erkannten Direktive ist, geprueft
als Zaehlvergleich. `scan_pipe_character` verbietet das Zeichen, mit dem Nextcloud die
Pluralformen verbindet. Beide laufen in `test_no_catalogue_value_can_break_the_page` ueber
`L10N_CATALOGUES`, mit vier gestellten Zeilen.

**Die Paritaet laeuft ueber alles, die Namen halten.**
`test_no_french_value_loses_or_invents_a_placeholder` ist
`test_no_catalogue_value_loses_or_invents_a_placeholder` und scannt alle Kataloge statt der
zwei franzoesischen Pfade. `test_all_six_catalogues_carry_the_same_keys` heisst
`test_every_catalogue_carries_the_same_keys`, und sein Docstring sagt jetzt auch, warum
`pt_PT` und `pt_BR` die deutsche Textgleichheit ausdruecklich **nicht** bekommen.

**Ein Gate ueber das Beweisdokument** (Abweichung, siehe unten): der Regelblock aus
`docs/l10n-catalogues.md` und `PLURAL_FORM_OF` sind zeichengleich, und das wird jetzt gehalten
statt einmal gemessen.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | Ausnahmen am Sprachcode, Vollstaendigkeitsgate ohne Adjektiv | `32f6e47` | `backend/tests/test_admin_ui_contract.py` |
| 2 | Prozent- und Pipe-Scanner, gemeinsames Gate mit vier gestellten Zeilen | `d2ddcb4` | `backend/tests/test_admin_ui_contract.py` |
| 3 | Paritaet ueber alle Kataloge, Testnamen ohne Zahl und Sprachnamen, Doku-Gate | `106ce1e` | `backend/tests/test_admin_ui_contract.py` |

## Sechs Scanner ueber L10N_CATALOGUES

| Scanner | Gate | Neu in diesem Plan |
| --- | --- | --- |
| `scan_prose` | `test_no_file_of_the_page_carries_a_dash_or_an_emoji` | nein |
| `scan_key_sets` | `test_every_catalogue_carries_the_same_keys` | nur der Name |
| `scan_completeness` | `test_every_catalogue_value_carries_a_wording_of_its_language` | Signatur, Name, Lauf ueber alles |
| `scan_placeholder_parity` | `test_no_catalogue_value_loses_or_invents_a_placeholder` | Lauf ueber alles, Name |
| `scan_percent_discipline` | `test_no_catalogue_value_can_break_the_page` | ja |
| `scan_pipe_character` | `test_no_catalogue_value_can_break_the_page` | ja |

## Dass die Gates rot fallen, ist gemessen und nicht behauptet

| Gestellter Schaden | Ergebnis |
| --- | --- |
| Rumpf von `scan_percent_discipline` auf `return []` gesetzt | genau `test_no_catalogue_value_can_break_the_page` faellt (`AssertionError: assert 0 == 1`), die uebrigen 50 bleiben gruen; danach zurueckgesetzt, 51 passed |
| `fr`-Zeile im Regelblock von `docs/l10n-catalogues.md` von `(n > 1)` auf `(n >= 1)` geaendert | `test_the_rule_table_of_the_documentation_and_the_constant_are_one_string` faellt und nennt beide Zeichenketten; `git checkout --` zurueckgenommen, `git status --short` danach nur der Testdatei-Eintrag |

Dazu die gestellten Zeilen in den Gate-Rumpfen selbst: `50 % de los archivos` (ein Fund),
`50 %% de los archivos` (kein Fund), `a | b` (ein Fund), eine Pluralliste mit nacktem
Prozentzeichen in der zweiten Form (ein Fund, und die Fundmeldung wird woertlich gegen den
erwarteten Satz mit der Formnummer geprueft), sowie im Vollstaendigkeitsgate die dritte
Zeile, die belegt, dass die Ausnahmeliste wirklich gelesen wird (derselbe Schmutzkatalog
liefert mit begruendetem `Reason` genau einen Fund weniger).

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| `grep -c 'scan_french_completeness'` | 0 |
| `grep -c 'VALUES_THAT_MAY_EQUAL_THEIR_KEY'` >= 3 | 6 |
| `grep -c 'def scan_completeness'` | 1 |
| `grep -c 'def language_code_of'` | 1 |
| Eintraege fuer `de`, `de_DE`, `fr`; `fr` weiterhin fuenf Schluessel mit Grund | ja, `de`/`de_DE` teilen vier Eintraege, `fr` fuenf |
| `grep -c 'def scan_percent_discipline'` / `'def scan_pipe_character'` | 1 / 1 |
| `grep -c 'def test_no_catalogue_value_can_break_the_page'` | 1 |
| Beide Scanner nur in diesem Gate, ueber `L10N_CATALOGUES` | ja, keine eigene Dateiliste |
| `grep -c 'test_all_six_catalogues_carry_the_same_keys'` | 0 |
| `grep -c 'def test_every_catalogue_carries_the_same_keys'` | 1 |
| `grep -c 'def test_no_catalogue_value_loses_or_invents_a_placeholder'` | 1 |
| `grep -c 'test_no_french_value_loses_or_invents_a_placeholder'` | 0 |
| `grep -c 'def test_the_two_translation_files_carry_the_same_keys'` | 1 (unveraendert) |
| Testnamen mit `french|spanish|italian|dutch|portuguese|_six_|_four_` | leere Liste |
| Kein Testname und kein Scannername traegt noch `french` | 0 Treffer |
| Sechs Scanner ueber `L10N_CATALOGUES` | ja, Tabelle oben |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped |
| ruff check, ruff format --check, pyright, vulture | alle gruen (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |
| `git diff --name-only` nennt ausschliesslich `backend/tests/test_admin_ui_contract.py` | ja |
| `git diff --name-only -- php/templates php/js php/lib backend/src/findling` | leer, kein Baumhash faellig |

## Die Selbstpruefung der Testnamen

Neun der 52 Testnamen dieser Datei tragen eine Zahl oder einen Sprachnamen. Zwei sind
umbenannt worden, sieben bleiben stehen, jeder mit seinem Grund:

| Testname | Urteil |
| --- | --- |
| `test_all_six_catalogues_carry_the_same_keys` | **umbenannt** zu `test_every_catalogue_carries_the_same_keys`: die Sechs zaehlte Kataloge |
| `test_the_six_files_of_the_two_pages_exist` | **umbenannt** zu `test_every_file_of_the_two_pages_exists`: die Sechs zaehlt keine Kataloge, wohl aber Dateien, die bei einer dritten Seite acht werden |
| `test_no_french_value_loses_or_invents_a_placeholder` | **umbenannt** zu `test_no_catalogue_value_loses_or_invents_a_placeholder` |
| `test_every_french_value_carries_a_french_wording` | **umbenannt** zu `test_every_catalogue_value_carries_a_wording_of_its_language` |
| `test_the_seven_sentences_of_the_engine_line_are_in_the_german_catalogue` | bleibt: die Sieben zaehlt die Zustaende der Maschine, und Deutsch ist der Bezugskatalog, gegen den das Schluesselgleichheits-Gate alle anderen haelt. Begruendung im Docstring ergaenzt |
| `test_all_three_files_carry_the_same_sentence_about_a_stall` | bleibt: die Drei zaehlt Template, Skript und den deutschen Katalog, nicht die Kataloge der App. Begruendung im Docstring ergaenzt |
| `test_the_two_translation_files_carry_the_same_keys` | bleibt unveraendert: die deutschen Zwillinge sind dauerhaft zwei, und der Test ist die IN-02-Klammer fuer Deutsch |
| `test_the_german_catalogue_covers_both_german_language_codes` | bleibt: dauerhaft eine Aussage ueber `de` und `de_DE` |
| `test_both_halves_of_the_page_carry_the_two_rebuild_banners` | bleibt: zwei Banner, keine Kataloge |

## Abweichungen vom Plan

### 1. [Rule 1 - Messung berichtigt die Planvorgabe] Deutsch bekommt vier Ausnahmen, nicht das leere Mapping

- **Gefunden in:** Task 1
- **Problem:** Der Plan schreibt vor, `de` und `de_DE` mit einem **leeren** Mapping und dem
  Satz einzutragen, "heute gibt es keinen" deutschen Wert, der seinem englischen Schluessel
  gleicht. Der Baum sagt etwas anderes: `Findling`, `%1$s in %2$s`, `PDF` und `Text` sind in
  `de.json` und `de_DE.json` mit ihrem Schluessel identisch. Ein leeres Mapping haette das
  Gate beim ersten Lauf ueber die deutschen Kataloge achtfach rot gemacht.
- **Fix:** Vier Eintraege mit je einem Grund, und ein Absatz ueber der Tabelle, der
  festhaelt, dass hier gelesen und nicht angenommen wurde. `de_DE` bindet auf den `de`-Eintrag.
- **Dateien:** `backend/tests/test_admin_ui_contract.py`
- **Commit:** `32f6e47`

### 2. [Rule 2 - fehlende Pruefung, Auftrag aus STATE.md] Das Doku-Gate ist gebaut worden

- **Gefunden in:** Task 3
- **Problem:** 20-02 hat die Zeichengleichheit zwischen dem Regelblock in
  `docs/l10n-catalogues.md` und `PLURAL_FORM_OF` einmal maschinell nachgewiesen (8 von 8) und
  als Zahl in einer Zusammenfassung stehen lassen. STATE.md fuehrt das fehlende Gate
  ausdruecklich als "Mitzunehmen in 20-03". Die Luecke ist keine Formsache: 20-04 bis 20-08
  giessen zehn Katalogdateien aus der Tabelle dieses Dokuments, und das Pluralregel-Gate
  urteilt gegen die Konstante. Ein verrutschtes Dokument haette zehn Dateien falsch gegossen,
  und das Gate haette zehn kaputte Kataloge gemeldet statt der einen falschen Zeile.
- **Fix:** `L10N_DOCUMENTATION`, `DECLARED_RULE`, `rules_declared_in(text)` und
  `test_the_rule_table_of_the_documentation_and_the_constant_are_one_string`. Das Muster
  trennt den Auslieferungsblock von der Tabelle darueber ueber den Abstand hinter dem
  Sprachcode; die Tabelle fuehrt zwischen Code und Regel noch zwei Spalten.
- **Dateien:** `backend/tests/test_admin_ui_contract.py`
- **Commit:** `106ce1e`

### 3. [Rule 3 - Abnahmekriterium gegen Planwortlaut] Ein Testname mehr umbenannt als angekuendigt

- **Gefunden in:** Task 3
- **Problem:** Der Plantext stellt frei, einen verbleibenden Namen zu behalten und zu
  begruenden. Das Abnahmekriterium und der Verifikationsbefehl desselben Tasks verlangen aber
  eine **leere** Liste ueber dem Muster `_six_`, und `test_the_six_files_of_the_two_pages_exist`
  faellt darunter, obwohl seine Sechs die Dateien zweier Seiten zaehlt und keine Kataloge.
- **Fix:** Umbenannt zu `test_every_file_of_the_two_pages_exists`, mit dem Grund im
  Kommentarblock: eine dritte Seite braechte acht Pfade, und die Zahl steht ohnehin in der
  Liste darunter, wo sie falsch sein und gesehen werden kann.
- **Dateien:** `backend/tests/test_admin_ui_contract.py`
- **Commit:** `106ce1e`

### Kleine Abweichungen in der Form, nicht in der Sache

Die Anti-Leerlauf-Klausel des Paritaets-Gates hat bisher gefragt, ob **die franzoesische**
`fr.json` ueberhaupt Schluessel mit Direktiven traegt. Da das Gate jetzt jede Datei scannt,
fragt sie das jetzt fuer jede Datei und nennt die, der nichts zu vergleichen bliebe.

Die beiden Fundhinweise stehen als Konstanten `PERCENT_HINT` und `PIPE_HINT` ueber den
Scannern, weil beide Fundformen (die ueber einen Schluessel und die ueber eine Form) denselben
Satz sagen muessen und die Zeilen sonst ueber die 120-Zeichen-Grenze von ruff gehen.

## Was ausdruecklich NICHT geaendert wurde

`test_the_two_translation_files_carry_the_same_keys` ist unveraendert: es ist die
IN-02-Klammer fuer Deutsch und beantwortet eine andere Frage als das Gate ueber alle
Kataloge. Die bestehenden Gates aus Task 2 sind unangetastet geblieben, der Task hat nur
hinzugefuegt. `PLURAL_FORM_OF`, `FORM_COUNT_OF`, `JS_PLURAL_FORM`, `scan_plural_rule` und
`PRINTF_DIRECTIVE` stehen so da wie nach 20-02, die harte Zahl 202 ebenfalls.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist
angefasst worden, also bewegt sich kein Baumhash. Die sechs Kataloge und
`docs/l10n-catalogues.md` liegen byteweise so da wie vor diesem Plan; der Rot-Beweis am
Dokument ist vollstaendig zurueckgenommen.

`KAT-01` bleibt **ungehakt**. Dieser Plan liefert die Parametrisierung, die die Anforderung
fordert, aber KAT-01 umfasst die zehn Katalogdateien selbst und wird fruehestens mit 20-08
erfuellt.

Nicht gepusht.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-09 (nacktes Prozentzeichen, Denial of Service) | `scan_percent_discipline` ueber Schluessel und jede Form, Zaehlvergleich, rote und gruene gestellte Zeile |
| T-20-10 (Pipe-Zeichen, Tampering) | `scan_pipe_character` ueber alle Kataloge, gestellte rote Zeile |
| T-20-11 (verlorenes `%2$s`) | `scan_placeholder_parity` laeuft ueber `L10N_CATALOGUES` |
| T-20-12 (Sprache ohne begruendete Ausnahmeliste) | fehlender Eintrag in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` ist ein Fehlschlag, der den Code nennt |
| T-20-13 (Markup im Katalogwert) | akzeptiert wie im Plan; diese Phase fasst keine Ausgabestelle an |

Keine neue Angriffsflaeche: die Aenderung liegt vollstaendig in einer Testdatei, es gibt
keinen neuen Endpunkt, keinen neuen Dateizugriff ausser dem lesenden auf
`docs/l10n-catalogues.md` und keine Schemaaenderung.

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Keine.

## Self-Check: PASSED

`backend/tests/test_admin_ui_contract.py` liegt im Baum und traegt alle sechs Scanner; die
drei Commit-Hashes `32f6e47`, `d2ddcb4` und `106ce1e` stehen in der Historie. Kein Eintrag
fehlt.
