---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 05
subsystem: l10n
tags: [italienisch, katalog, giessform, vollstaendigkeitsgate, pluralformen, vorbehalt]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 01
    provides: "die fuenf Pluralschluessel als _<singular>_::_<plural>_ und die Giessform, die den Bestand byteweise reproduziert"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "PLURAL_FORM_OF['it'] und FORM_COUNT_OF['it'], docs/l10n-catalogues.md als gemeinsamer Beweis"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 03
    provides: "VALUES_THAT_MAY_EQUAL_THEIR_KEY je Sprachcode, scan_percent_discipline, scan_pipe_character, sechs Scanner ueber L10N_CATALOGUES"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 04
    provides: "die Abschnittsfolge von docs/l10n-spanish.md, der Weg zur gemessenen Ausnahmeliste und der Vorbefund zum Vokabular-Gate"
provides:
  - "php/l10n/it.json: 202 Schluessel in der Reihenfolge von de.json, fuenf Pluralwerte mit drei Formen, Form 1 gleich Form 2, italienische Regel mit nplurals=3"
  - "php/l10n/it.js: mechanisch aus it.json gegossen, Objektvergleich haelt den Gleichstand"
  - "L10N_IT_JSON und L10N_IT_JS in L10N_CATALOGUES: das Tupel fuehrt zehn Eintraege, alle sechs Scanner nehmen Italienisch mit"
  - "VALUES_THAT_MAY_EQUAL_THEIR_KEY['it']: drei begruendete Eintraege, gemessen statt geraten"
  - "docs/l10n-italian.md: neun Abschnitte, 202 Tabellenzeilen, Pruefergebnisse und der datierte Vorbehalt vom 25.09.2026"
  - "Der Eintrag l10n-italian.md in AUSNAHMEN des Vokabular-Gates, mit dem gemessenen Grund"
  - "Der Befund, dass eine alleinstehende <code>.json das Pluralregel-Gate mit FileNotFoundError umwirft: das Katalogpaar gehoert in EINEN Commit"
affects: [20-06 bis 20-08 (dieselbe Giessform, dieselbe Abschnittsfolge, derselbe Commit-Zuschnitt), 20-09 (CI-Sprachbeweis laeuft auch fuer it)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Katalogpaar .json und .js geht in EINEN Commit: das Pluralregel-Gate liest zu jeder vorhandenen <code>.json die zugehoerige <code>.js unbedingt, also ist eine alleinstehende .json ein roter Zwischenstand und kein halber Fortschritt"
    - "Eine Ausnahmeliste wird gefunden und nicht geraten: drei Laeufe (kein Eintrag, leeres Mapping, begruendete Liste), und jeder gemeldete Schluessel wird einzeln beurteilt"
    - "Ein Wortstamm-Gate stolpert je Sprache ueber andere Woerter: bei Spanisch war es das Wort fuer Datei, bei Italienisch das fuer den Speicherort. Die Vorhersage aus 20-04 stimmte in der Wirkung und nicht im Wort"
    - "Ein echter Treffer der gesperrten Form wird umformuliert und nicht mitentschuldigt: die Ausnahme gilt je Datei, also deckt sie sonst auch den Fehler, den die Familie fangen soll"
    - "Die Anrede einer Uebersetzung folgt Zeile fuer Zeile der Quelle: wechselt der deutsche Bestand zwischen Infinitiv und Sie-Form, wechselt die Uebersetzung mit, und der Wechsel bleibt eine Eigenschaft der Quelle statt eine Nachlaessigkeit der Uebersetzung"

key-files:
  created:
    - php/l10n/it.json
    - php/l10n/it.js
    - docs/l10n-italian.md
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-05-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_public_artifacts.py

key-decisions:
  - "Das Katalogpaar it.json und it.js steht in EINEM Commit statt in zweien. Das ist eine begruendete Rule-3-Abweichung und gemessen: mit it.json allein faellt test_every_catalogue_carries_the_plural_rule_of_its_language mit FileNotFoundError auf it.js, weil das Gate ueber PLURAL_FORM_OF laeuft und zu jeder vorhandenen .json die .js unbedingt liest. Plan 20-04 hat diesen Zwischenstand committet; hier ist er vermieden, und der Gate-Eintrag bleibt trotzdem ein eigener Commit"
  - "Die italienische Ausnahmeliste fuehrt DREI Eintraege und nicht zwei wie die spanische: zusaetzlich zu Findling und PDF steht %1$s in %2$s darin, weil das Italienische dieselbe Praeposition schreibt wie das Englische. Das Spanische hat dort en und damit einen eigenen Wortlaut. Gemessen mit leerem Mapping: sechs Funde, drei Schluessel ueber zwei Dateien"
  - "Das Gate hat KEINE Logikaenderung gebraucht. git diff ueber test_admin_ui_contract.py zeigt 39 Zufuegungen und 0 Loeschungen, verteilt auf das Konstantenpaar, den Tupel-Eintrag und die Ausnahmeliste. Die Parametrisierung aus Plan 20-03 haelt damit ihre zweite neue Sprache aus, und 20-06 bis 20-08 duerfen dasselbe erwarten"
  - "Die eine deutsche Stelle des Vokabular-Befundes ist umformuliert und nicht entschuldigt worden. Der Entwurf der Wortwahl-Tabelle erklaerte das italienische Wort mit der deutschen Form des gesperrten Begriffs; das ist genau der Fehler, den die Familie fangen soll. Erst danach ist der Ausnahmeeintrag gesetzt worden, und er deckt nur noch die neun italienischen Treffer"
  - "Kein literales Prozentzeichen im Katalog, auch kein verdoppeltes: der 100-Prozent-Satz heisst il cento per cento. Dieselbe Wahl wie im Spanischen, und die Schreibregel %% steht trotzdem im Typografie-Abschnitt der Doku"
  - "KAT-01 und KAT-02 bleiben UNGEHAKT. Beide umfassen zehn Katalogdateien; vier davon stehen. Der Haken gehoert fruehestens zu 20-08"

requirements-completed: []

# Metrics
duration: 45min
completed: 2026-09-25
---

# Phase 20 Plan 05: Der italienische Katalog Summary

**Findling spricht Italienisch: `php/l10n/it.json` und `php/l10n/it.js` fuehren dieselben 202
Schluessel wie der deutsche Katalog, laufen durch dieselben sechs Scanner wie die acht
Bestandsdateien, und das Gate hat dafuer keine einzige Zeile Logik gebraucht: 39 Zufuegungen,
0 Loeschungen.**

## Was gebaut wurde

**Zwei Katalogdateien.** `it.json` traegt 202 Schluessel in der Reihenfolge von `de.json`,
`Findling` als ersten mit sich selbst als Wert, fuenf Pluralwerte mit je drei Formen (Form 1
und Form 2 wortgleich) und die italienische Regel mit `nplurals=3`, zeichengleich aus
`docs/l10n-catalogues.md` uebernommen. `it.js` ist daraus gegossen und nicht getippt; der
Objektvergleich zwischen dem `register`-Rumpf und der `.json` ist Teil der Abnahme.

**Zwei Konstanten und eine Ausnahmeliste im Gate.** `L10N_IT_JSON` und `L10N_IT_JS` stehen mit
Begruendungsabsatz in `L10N_CATALOGUES`, das damit zehn Eintraege fuehrt. Prosa-Scan,
Schluesselmenge, Vollstaendigkeit, Platzhalterparitaet, Prozentdisziplin und Pipe-Pruefung
nehmen Italienisch seitdem automatisch mit. `VALUES_THAT_MAY_EQUAL_THEIR_KEY["it"]` fuehrt drei
begruendete Eintraege.

**Eine Sprachdokumentation.** `docs/l10n-italian.md`, 477 Zeilen, neun Abschnitte in der
Reihenfolge von `docs/l10n-spanish.md`, mit der vollstaendigen Tabelle `| Schluessel | DE | IT |`
und dem datierten Vorbehalt.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | it.json in der Reihenfolge des deutschen Katalogs, samt gegossener it.js | `ecf8bd2` | `php/l10n/it.json`, `php/l10n/it.js` |
| 2 | Das Gate um Italienisch erweitern | `fff9aba` | `backend/tests/test_admin_ui_contract.py` |
| 3 | docs/l10n-italian.md mit Tabelle, Pruefergebnissen und datiertem Vorbehalt | `e6185c9` | `docs/l10n-italian.md` |
| 3a | Rule-3-Fix: Vokabular-Gate ueber der neuen Doku | `42f6add` | `backend/tests/test_public_artifacts.py` |

## Die Begriffsentscheide

Der Plan verlangt fuenf vor dem Schreiben getroffen und danach begruendet. Sie stehen als
Tabelle im Abschnitt "Wortwahl" der Sprachdoku und folgen der romanischen Linie, weil
Franzoesisch, Spanisch und Italienisch dieselben Saetze uebersetzen:

| Englisch | Italienisch | Grund in einem Satz |
| --- | --- | --- |
| the backend | `il servizio` | wie `le service` und `el servicio`: der Nutzer sieht einen Dienst, der antwortet oder nicht |
| run | `passata` | dasselbe Bild wie `pasada` und `passage`, ein Durchgang ueber den Bestand; `esecuzione` ist schwerer, `ciclo` verspricht eine Regelmaessigkeit, die der Abgleichlauf nicht hat |
| worker | `processo di elaborazione` | nach `processus de traitement`; `lavoratore` waere der Mensch |
| index | `l'indice` (Substantiv), `indicizzare` (Verb) | anders als im Spanischen ohne Akzent eindeutig; `indexare` ist kein italienisches Wort |
| coverage | `copertura` | die Zahl, die den durchsuchbaren Anteil nennt |

Drei weitere Entscheide standen nicht im Plan und gehoerten trotzdem getroffen, weil sie
jeweils Dutzende Zeilen betreffen: `file` bleibt `file` (das Italienische hat das englische
Wort uebernommen und bildet keinen Plural), `background job` wird `processo in background`
(die Wortwahl der italienischen Nextcloud-Oberflaeche, von `processo di elaborazione` durch
die Ergaenzung unterschieden und nie im selben Satz), und die Anrede folgt Zeile fuer Zeile
dem deutschen Bestand: wo Deutsch den Infinitiv fuehrt, steht der italienische Infinitiv, wo
Deutsch siezt, die hoefliche Form auf `-i`.

## Die Giessform, erneut gegen den Bestand geprueft

Vor der ersten neuen Zeile lief die Form aus Plan 20-01 noch einmal gegen die acht
Bestandsdateien: `cast_json(alt) == alt` und `cast_js(alt) == alt`, byteweise, fuer `de`,
`de_DE`, `fr` und `es`, **acht von acht `True`**. Erst danach ist `it.json` geschrieben worden.

Das Giessskript liegt **nicht** im Repo. Es lag fuer die Dauer der Ausfuehrung ausserhalb des
Arbeitsbaums und ist dort geblieben; `git status --short` ist nach jedem Task leer gewesen.

## Die Ausnahmeliste ist gefunden und nicht geraten

Drei Laeufe, in dieser Reihenfolge:

| Lauf | Ergebnis |
| --- | --- |
| kein Eintrag fuer `it` in der Tabelle | `AssertionError: languages without a list of exceptions: ['it']` |
| leeres Mapping `"it": {}` | sechs Funde, drei Schluessel ueber zwei Dateien, erster davon `it.json: 'Findling' is still the English source string` |
| drei begruendete Eintraege | gruen, 52 passed |

Beurteilt wurde je Schluessel: `Findling` ist der Eigenname der App, `PDF` der eines
Dateiformats, und `%1$s in %2$s` sind zwei Platzhalter mit der Praeposition dazwischen, die das
Italienische genauso schreibt wie das Englische und das Deutsche. **Die italienische Liste ist
damit um einen Eintrag laenger als die spanische**, und das ist ein Befund: das Spanische
schreibt `%1$s en %2$s` und hat dort einen eigenen Wortlaut. Der verwandte Schluessel
`%1$s in %2$s, modified on %3$s` steht nicht in der Liste, weil sein zweiter Teil italienisch
ist.

## Das Gate hat keine Logikaenderung gebraucht

Das ist der eigentliche Gegenstand dieses Plans. `git diff backend/tests/test_admin_ui_contract.py`
zeigt **39 Zufuegungen und 0 Loeschungen**, verteilt auf genau drei Stellen: das Konstantenpaar
mit seinem Begruendungsabsatz, der Eintrag im Tupel, der Eintrag in
`VALUES_THAT_MAY_EQUAL_THEIR_KEY`. Kein Scanner, kein Testrumpf und keine Zahl im Testnamen ist
angefasst worden. Die Parametrisierung aus Plan 20-03 traegt damit ihre zweite neue Sprache,
und 20-06 bis 20-08 duerfen dasselbe erwarten.

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| Schluesselmenge und Reihenfolge `it.json` gegen `de.json` | gleich, 202 von 202 |
| Genau fuenf Listenwerte, je drei Eintraege, Eintrag 1 gleich Eintrag 2 | 5 von 5 |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, `nplurals=3` | ja, in beiden Dateien |
| U+2014, U+2013, U+2019, U+00A0, U+202F in `it.json`, `it.js`, `l10n-italian.md` | je 0 |
| Zeichenfolge `e'` als Ersatz fuer `è` | 0 |
| Pipe-Zeichen in Schluesseln und Formen | 0 |
| Prozentzeichen ohne erkannte Direktive | 0, und ueberhaupt kein literales Prozentzeichen |
| Platzhalterparitaet Schluessel gegen Wert, Pluralschluessel an `_::_` geteilt | 0 Abweichungen ueber 40 Schluessel mit Direktiven |
| Wert zu `Findling` | `Findling` |
| LF, UTF-8 ohne BOM, abschliessender Zeilenumbruch | beide Kataloge und die Doku, byteweise geprueft; der Git-Blob ist reines LF (0 CR) |
| `it.js` beginnt mit `OC.L10N.register(` und endet mit der Regel als viertem Parameter | ja, byteweise geprueft |
| Objektvergleich `it.js` gegen `it.json` | identisch, 202 Schluessel |
| `grep -c 'L10N_IT_JSON\|L10N_IT_JS'` | 4, gefordert waren mindestens 4 |
| Eintraege in `L10N_CATALOGUES` | 10 |
| Kommentarabsatz vor `L10N_IT_JSON`, nennt die fehlende Regionalvariante | ja, 20 Zeilen |
| `VALUES_THAT_MAY_EQUAL_THEIR_KEY["it"]`, jeder Schluessel mit Grund | 3 Eintraege, alle drei mit Grund |
| `git diff` am Gate: nur Zufuegungen in den drei genannten Bereichen | 39 zu, 0 weg |
| Neun Abschnitte der Doku in der Reihenfolge von `docs/l10n-spanish.md` | ja, maschinell ausgelesen |
| Datenzeilen der Tabelle gleich der Schluesselzahl | 202 |
| Jeder Schluessel aus `it.json` kommt in der Doku vor | fehlend 0 |
| Ausnahmeliste der Doku gegen `VALUES_THAT_MAY_EQUAL_THEIR_KEY["it"]` | dieselben drei Schluessel, maschinell verglichen |
| Abschnitt "Abnahme" mit Datum TT.MM.JJJJ, `20-05` und `von keinem Muttersprachler gelesen` | alle drei vorhanden |
| Zeilen in `docs/l10n-italian.md` | 477, gefordert waren mindestens 260 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped (dreimal gefahren, vor jedem Commit) |
| ruff check, ruff format --check, pyright, vulture | alle gruen (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |
| `git diff --name-only -- php/templates php/js php/lib backend/src` | leer, kein Baumhash faellig |
| Loeschungen in den vier Commits | 0 |

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker] Das Katalogpaar geht in EINEN Commit

- **Gefunden in:** Task 1, vor dem Commit, durch die geplante Messung des Zwischenstands
- **Problem:** `test_every_catalogue_carries_the_plural_rule_of_its_language` laeuft ueber die
  Codes von `PLURAL_FORM_OF`, die heute eine `.json` haben, und liest zu jedem davon die `.js`
  **unbedingt**. Eine alleinstehende `it.json` bringt das Gate deshalb nicht rot zum Fallen,
  sondern zum Absturz: `FileNotFoundError: ... php\l10n\it.js`, gemessen mit
  `1 failed, 51 passed`.
- **Warum nicht anders zu loesen:** Der Plan schneidet Task 1 auf `it.json` und Task 2 auf
  `it.js` plus Gate. Dieser Schnitt erzeugt genau einen Commit, an dem die Suite nicht laeuft.
  Plan 20-04 hat ihn committet (`7dd61fd` traegt `es.json` allein), und die Projektregel
  "Gates lokal gruen VOR jedem Commit" laesst das nicht zu. Die Alternative, die `.js`
  wegzulassen und das Gate anzupassen, waere eine Logikaenderung am Gate gewesen und damit
  genau das, was dieser Plan ausdruecklich verbietet.
- **Fix:** `it.json` und `it.js` stehen zusammen in `ecf8bd2`. Beide sind ohnehin ein
  mechanisches Erzeugnis desselben Laufs; die `.js` ist keine eigene Arbeit, sondern eine
  Funktion der `.json`. Der Gate-Eintrag bleibt ein eigener Commit (`fff9aba`), also bleiben es
  vier Commits wie im Plan.
- **Dateien:** `php/l10n/it.json`, `php/l10n/it.js`
- **Commit:** `ecf8bd2`
- **Mitzunehmen in 20-06 bis 20-08:** derselbe Schnitt. Der Zwischenstand "nur die .json" ist
  in diesem Repo kein halber Fortschritt, sondern eine kaputte Suite.

### 2. [Rule 3 - Blocker] Das Vokabular-Gate faellt ueber dem italienischen Wort fuer den Speicherort

- **Gefunden in:** Task 3, beim Suitelauf nach dem Bau der Doku
- **Problem:** `tests/test_public_artifacts.py` haelt eine Wortstamm-Sperre ueber alles unter
  `docs/` und meldete `l10n-italian.md`. Plan 20-04 hat das vorhergesagt, aber mit dem falschen
  Wort: erwartet war das italienische Wort fuer **Datei**, und das gibt es nicht, weil das
  Italienische dafuer das englische Wort uebernommen hat (`un file`, `i file`). Getroffen hat
  stattdessen das Wort fuer den **Speicherort**, das in der Nextcloud-Oberflaeche an neun
  Stellen dieses Katalogs steht.
- **Ein echter Treffer war dabei, und er ist nicht entschuldigt worden.** Der Entwurf der
  Wortwahl-Tabelle erklaerte das italienische Wort mit der **deutschen** Form des gesperrten
  Begriffs. Das ist genau der Fehler, den die Familie fangen soll, und eine Ausnahme je Datei
  haette ihn mitgedeckt. Die Zeile ist umformuliert worden, die Zaehlung ging dadurch von zehn
  auf neun Treffer zurueck, und erst danach ist der Ausnahmeeintrag gesetzt worden.
- **Fix:** Ein Eintrag `("l10n-italian.md", "vokabular")` in `AUSNAHMEN`, mit eigenem Grund in
  eigenen Saetzen, der die Zahl neun und die umformulierte Stelle ausdruecklich nennt.
- **Dateien:** `backend/tests/test_public_artifacts.py`
- **Commit:** `42f6add`
- **Restrisiko, benannt:** wie in 20-04 gilt die Ausnahme fuer die ganze Datei, also wuerde eine
  spaeter eingefuegte deutsche Form in `docs/l10n-italian.md` nicht mehr auffallen. Feiner kann
  die Liste heute nicht, sie ist auf Datei und Familie geschluesselt.
- **Mitzunehmen in 20-06 bis 20-08:** die Vorhersage aus 20-04 stimmte in der Wirkung und nicht
  im Wort. Das Gate einmal laufen zu lassen und die Treffer zu **lesen** ist billiger, als sich
  auf die Prognose der Vorgaengersprache zu verlassen. Fuer Portugiesisch und Niederlaendisch
  bleibt die Prognose "kein Treffer", aber sie ist jetzt zweimal knapp danebengegangen.

### Kleine Abweichungen in der Form, nicht in der Sache

**Drei Begriffsentscheide mehr als die fuenf verlangten.** `file`, `background job` und die
Anrede betreffen jeweils Dutzende Zeilen; sie stehen begruendet in der Wortwahl-Tabelle.

**Die Ausnahmeliste hat drei statt der zwei spanischen Eintraege.** Kein Fehler, sondern eine
Eigenschaft der Sprache, oben ausgefuehrt.

**Kein `%%` im Katalog.** Wie im Spanischen ist der einzige betroffene Satz umformuliert
(`il cento per cento`). Die Schreibregel steht trotzdem im Typografie-Abschnitt der Doku.

## Was ausdruecklich NICHT geaendert wurde

`PLURAL_FORM_OF["it"]` und `FORM_COUNT_OF["it"]` stehen unveraendert so da wie nach 20-02; sie
sind hier benutzt und nicht angefasst worden. Die acht Bestandskataloge, `docs/l10n-french.md`,
`docs/l10n-spanish.md` und `docs/l10n-catalogues.md` liegen byteweise wie vor diesem Plan.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist
angefasst worden, also bewegt sich kein Baumhash.

`KAT-01` und `KAT-02` bleiben **ungehakt**. Beide umfassen zehn Katalogdateien, und vier davon
stehen. Der Haken gehoert fruehestens zu 20-08.

Nicht gepusht.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-19 (italienisches Prozentzeichen, Denial of Service) | `scan_percent_discipline` laeuft ueber `it.json` und `it.js`, seit das Paar im Tupel steht; im Katalog steht ueberdies kein literales Prozentzeichen |
| T-20-20 (U+2019 als Apostroph in `l'indice`) | eigenes Abnahmekriterium ueber U+2014, U+2013, U+2019, U+00A0, U+202F in beiden Dateien und in der Doku, je 0 Treffer; dazu die Suche nach `e'` als Akzentersatz, 0 Treffer, und ein eigener Absatz im Typografie-Abschnitt |
| T-20-21 (verlorener oder umnummerierter Platzhalter) | `scan_placeholder_parity` ueber beide neuen Dateien, mit Teilung der zusammengesetzten Pluralschluessel; 0 Abweichungen ueber 40 Schluessel mit Direktiven |
| T-20-22 (`it.js` laeuft von `it.json` weg) | die `.js` ist gegossen, und der Gleichstand ist per Objektvergleich geprueft |
| T-20-23 (Katalog ohne Vorbehalt) | `docs/l10n-italian.md`, Abschnitt "Abnahme", datiert auf den 25.09.2026, mit Plannummer und dem Satz "von keinem Muttersprachler gelesen" |
| T-20-SC (Paketinstallation) | keine Installation in dieser Phase |

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Keine.

## Self-Check: PASSED

`php/l10n/it.json`, `php/l10n/it.js`, `docs/l10n-italian.md`,
`backend/tests/test_admin_ui_contract.py` und `backend/tests/test_public_artifacts.py` liegen im
Baum; die vier Commit-Hashes `ecf8bd2`, `fff9aba`, `e6185c9` und `42f6add` stehen in der
Historie. Kein Eintrag fehlt.
