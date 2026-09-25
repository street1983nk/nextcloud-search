---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 06
subsystem: l10n
tags: [niederlaendisch, katalog, zwei-pluralformen, zeichengleiche-regel, gegenprobe, vorbehalt]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 01
    provides: "die fuenf Pluralschluessel als _<singular>_::_<plural>_ und die Giessform, die den Bestand byteweise reproduziert"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 02
    provides: "PLURAL_FORM_OF['nl'] und FORM_COUNT_OF['nl'], der sprachbewusste scan_plural_rule mit dem niederlaendischen Sonderfall als gestellter Gegenprobe, docs/l10n-catalogues.md als gemeinsamer Beweis"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 03
    provides: "VALUES_THAT_MAY_EQUAL_THEIR_KEY je Sprachcode, scan_percent_discipline, scan_pipe_character, sechs Scanner ueber L10N_CATALOGUES"
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 05
    provides: "der Commit-Zuschnitt (Katalogpaar in EINEM Commit), die Abschnittsfolge der Sprachdoku und die Regel, die Ausnahmeliste zu messen statt zu raten"
provides:
  - "php/l10n/nl.json: 202 Schluessel in der Reihenfolge von de.json, fuenf Pluralwerte mit ZWEI Formen, niederlaendische Regel mit nplurals=2"
  - "php/l10n/nl.js: mechanisch aus nl.json gegossen, Objektvergleich haelt den Gleichstand"
  - "L10N_NL_JSON und L10N_NL_JS in L10N_CATALOGUES: das Tupel fuehrt zwoelf Eintraege, alle sechs Scanner nehmen Niederlaendisch mit"
  - "Der Begruendungsabsatz im Gate, der beide Sonderfaelle benennt: zwei Formen statt drei, und die mit der deutschen zeichengleiche Regel aus core/l10n/nl.json"
  - "VALUES_THAT_MAY_EQUAL_THEIR_KEY['nl']: VIER begruendete Eintraege, gemessen statt geraten"
  - "docs/l10n-dutch.md: neun Abschnitte, 202 Tabellenzeilen, Pruefergebnisse und der datierte Vorbehalt vom 25.09.2026"
  - "Die gestellte Gegenprobe aus 20-02 ist eingeloest: scan_plural_rule meldet fuer nl mit der deutschen Zeichenkette nichts und fuer es mit derselben zwei Funde, gemessen ueber eine Sprache, die es jetzt wirklich gibt"
  - "Der Befund, dass das Vokabular-Gate ueber der niederlaendischen Doku NICHT faellt: 0 Stammtreffer, anders als bei es (61) und it (9)"
affects: [20-07 und 20-08 (dieselbe Giessform, dieselbe Abschnittsfolge, derselbe Commit-Zuschnitt), 20-09 (CI-Sprachbeweis laeuft auch fuer nl)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine gestellte Gegenprobe wird eingeloest, sobald die Sprache existiert, fuer die sie gestellt wurde: nicht nur der gruene Testlauf, sondern der ausdrueckliche Dreifachaufruf (richtige Regel, fremde Regel, dieselbe Zeichenkette bei einer anderen Sprache) belegt, dass das Gate fuer nl nicht pauschal schweigt"
    - "Ein Sonderfall, der wie ein Fehler aussieht, steht an beiden Orten, an denen ihn jemand fuer einen halten koennte: im Kommentarabsatz des Gates und in der Sprachdoku, jeweils mit der ausdruecklichen Bitte, den Scanner nicht zu reparieren"
    - "Eine Ausnahmeliste wird gefunden und nicht geraten: drei Laeufe (kein Eintrag, leeres Mapping, begruendete Liste), und jeder gemeldete Schluessel wird einzeln beurteilt; nl hat vier, it drei, es zwei, fr fuenf"
    - "Eine Prognose wird auch dann gemessen, wenn sie stimmt: das Vokabular-Gate ist ueber nl gruen, aber der Lauf kostet Sekunden und die Prognose der Vorgaengersprache ist zweimal danebengegangen"
    - "Zwei gleiche Formen in einem Pluralwert koennen die richtige Uebersetzung sein: %n uur steht zweimal, weil niederlaendische Massangaben nach einem Zahlwort im Singular bleiben"

key-files:
  created:
    - php/l10n/nl.json
    - php/l10n/nl.js
    - docs/l10n-dutch.md
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-06-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "Das Katalogpaar nl.json und nl.js steht in EINEM Commit (3f76cdc). Das ist die begruendete Rule-3-Abweichung aus 20-05, hier vorausschauend uebernommen statt neu gemessen: test_every_catalogue_carries_the_plural_rule_of_its_language laeuft ueber die Codes von PLURAL_FORM_OF, die heute eine .json haben, und liest zu jedem die .js unbedingt. Der Gate-Eintrag bleibt ein eigener Commit"
  - "Die niederlaendische Ausnahmeliste fuehrt VIER Eintraege und ist damit die laengste der drei neuen Sprachen: Findling, %1$s in %2$s, PDF und Spreadsheets. Gemessen mit leerem Mapping: acht Funde, vier Schluessel ueber zwei Dateien. Spreadsheets ist der Eintrag, den es weder im Spanischen noch im Italienischen gibt, und er ist eine Eigenschaft der Sprache: die niederlaendische Nextcloud-Oberflaeche fuehrt das englische Wort, und Rekenbladen waere an dieser Stelle eine Erfindung"
  - "Die fuenf Pluralwerte tragen zwei Formen, und zwei davon fuehren zweimal denselben Wortlaut. Das ist kein Kopierfehler: %n uur bleibt im Niederlaendischen nach einem Zahlwort im Singular (twee uur, drie kilometer), und en nog %n traegt ueberhaupt kein beugbares Hauptwort. Bei minuut und dag gilt das nicht, dort stehen %n minuten und %n dagen"
  - "Der Suchbegriff steht in geraden ASCII-Anfuehrungszeichen und nicht in typographischen wie im deutschen Bestand. Grund: die niederlaendische Buchtypografie setzt einfache Anfuehrungszeichen, deren schliessende Haelfte zeichengleich mit U+2019 ist, und genau dieses Zeichen verbietet die Apostrophregel dieses Katalogs. Zwei Regeln, die einander widersprechen, sind schlechter als eine schlichte Schreibweise"
  - "Der Katalog fuehrt VIER Stellen mit een als betontem Zahlwort, alle vier absichtlich. Der Unterschied zum unbestimmten Artikel ist bedeutungstragend (Een bestand controleren heisst ein einziges pruefen), und eine maschinelle Uebersetzung glaettet ihn gern weg"
  - "Das Gate hat KEINE Logikaenderung gebraucht. git diff ueber test_admin_ui_contract.py zeigt 55 Zufuegungen und 0 Loeschungen, verteilt auf das Konstantenpaar mit seinem Begruendungsabsatz, den Tupel-Eintrag und die Ausnahmeliste. Die Parametrisierung aus 20-03 traegt damit ihre dritte neue Sprache und zum ersten Mal eine mit abweichender Formenzahl"
  - "Kein Eintrag im Vokabular-Gate von tests/test_public_artifacts.py. Anders als bei Spanisch (61 Treffer) und Italienisch (9) faellt es ueber docs/l10n-dutch.md nicht: das Niederlaendische schreibt Datei als bestand und Speicherort als opslag. Gemessen, nicht prognostiziert; 0 Stammtreffer"
  - "KAT-01 und KAT-02 bleiben UNGEHAKT. Beide umfassen zehn Katalogdateien; sechs davon stehen. Der Haken gehoert fruehestens zu 20-08"

requirements-completed: []

# Metrics
duration: 50min
completed: 2026-09-25
---

# Phase 20 Plan 06: Der niederländische Katalog Summary

**Findling spricht Niederländisch: `php/l10n/nl.json` und `php/l10n/nl.js` führen dieselben 202
Schlüssel wie der deutsche Katalog, tragen aber ZWEI Pluralformen statt drei, und der
Sonderfall der mit der deutschen zeichengleichen Regel ist an beiden Orten benannt, an denen
ihn jemand für einen Fehler halten könnte. Das Gate hat dafür wieder keine Zeile Logik
gebraucht: 55 Zufügungen, 0 Löschungen.**

## Was gebaut wurde

**Zwei Katalogdateien.** `nl.json` trägt 202 Schlüssel in der Reihenfolge von `de.json`,
`Findling` als ersten mit sich selbst als Wert, fünf Pluralwerte mit je **zwei** Formen und die
niederländische Regel `nplurals=2; plural=(n != 1);`, zeichengleich aus
`docs/l10n-catalogues.md` übernommen. Vorlage der Form war `fr.json`, ausdrücklich nicht
`es.json`. `nl.js` ist daraus gegossen und nicht getippt; der Objektvergleich zwischen dem
`register`-Rumpf und der `.json` ist Teil der Abnahme.

**Zwei Konstanten, ein Begründungsabsatz und eine Ausnahmeliste im Gate.** `L10N_NL_JSON` und
`L10N_NL_JS` stehen in `L10N_CATALOGUES`, das damit zwölf Einträge führt. Der Absatz darüber
(33 Zeilen) nennt beide Sonderfälle ausdrücklich und schließt mit der Bitte an den späteren
Leser, `scan_plural_rule` nicht zu reparieren. `VALUES_THAT_MAY_EQUAL_THEIR_KEY["nl"]` führt
vier begründete Einträge.

**Eine Sprachdokumentation.** `docs/l10n-dutch.md`, 534 Zeilen, neun Abschnitte in der
Reihenfolge von `docs/l10n-spanish.md` und `docs/l10n-italian.md`, mit der vollständigen
Tabelle `| Schluessel | DE | NL |` und dem datierten Vorbehalt.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | nl.json mit zwei Pluralformen, samt gegossener nl.js | `3f76cdc` | `php/l10n/nl.json`, `php/l10n/nl.js` |
| 2 | Das Gate um Niederländisch erweitern, Sonderfall benannt | `e7ed056` | `backend/tests/test_admin_ui_contract.py` |
| 3 | docs/l10n-dutch.md mit Tabelle, Prüfergebnissen und datiertem Vorbehalt | `d40e335` | `docs/l10n-dutch.md` |

Drei Commits statt der vier der beiden Vorgängerpläne: der vierte war dort jeweils der
Rule-3-Fix am Vokabular-Gate, und der ist hier nicht nötig gewesen (siehe unten).

## Die Begriffsentscheide

Der Plan verlangt fünf vor dem Schreiben getroffen und danach begründet. Sie stehen als Tabelle
im Abschnitt "Wortwahl" der Sprachdoku:

| Englisch | Niederländisch | Grund in einem Satz |
| --- | --- | --- |
| the backend | `de dienst` | wie `le service`, `el servicio` und `il servizio`: der Nutzer sieht einen Dienst, der antwortet oder nicht; `de backend` benennt ein Bauteil und keine Zusage |
| run | `doorloop`, `vergelijkingsdoorloop`, `achtergronddoorloop` | ein Durchgang über den Bestand, dasselbe Bild wie `passage`, `pasada`, `passata`; `ronde` verspricht eine Regelmäßigkeit, die der Abgleichlauf nicht hat |
| worker | `verwerkingsproces` | nach `processus de traitement`; `werker` wäre der Mensch |
| index | `de index` (Substantiv), `indexeren` (Verb) | gewöhnliche niederländische Wörter, die die Oberfläche selbst führt; `indiceren` meint das Zuordnen einer Kennzahl |
| coverage | `dekking` | die Zahl, die den durchsuchbaren Anteil nennt |

Acht weitere Entscheide standen nicht im Plan und gehörten trotzdem getroffen, weil sie jeweils
Dutzende Zeilen betreffen: `bestand` für file (und ausdrücklich **nicht** `file`, das im
Niederländischen eine Verkehrsstockung ist), `achtergrondtaak` für background job, `opslag` und
`opslaglocatie` für storage, `map` für folder, `treffers uit de volledige tekst` für full text
hits, `Geen.` für die Abhilfezeile, `Team Folders` unübersetzt, und die Anrede, die Zeile für
Zeile dem deutschen Bestand folgt: wo Deutsch den Infinitiv führt, steht der niederländische
Infinitiv, wo Deutsch siezt, die Form mit `u`.

## Die Giessform, erneut gegen den Bestand geprüft

Vor der ersten neuen Zeile lief die Form aus Plan 20-01 noch einmal gegen die zehn
Bestandsdateien: `cast_json(alt) == alt` und `cast_js(alt) == alt`, byteweise, für `de`,
`de_DE`, `fr`, `es` und `it`, **zehn von zehn `True`**. Der erste Anlauf lief mit fünf von
zehn: die `.js`-Hälfte fehlte der abschließende Zeilenumbruch. Das ist genau der Zweck dieser
Vorprüfung, und sie hat sich zum zweiten Mal bezahlt gemacht.

Das Giessskript liegt **nicht** im Repo. Es lag für die Dauer der Ausführung ausserhalb des
Arbeitsbaums und ist dort geblieben; `git status --short` ist nach jedem Task leer gewesen.

## Der niederländische Sonderfall, gemessen statt behauptet

Das ist der eigentliche Gegenstand dieses Plans. Plan 20-02 hat `scan_plural_rule`
sprachbewusst gemacht und die Gegenprobe damals mit einer Sprache gestellt, die es noch nicht
gab. Jetzt gibt es sie, und der Dreifachaufruf am 25.09.2026 sagt:

| Aufruf | Ergebnis |
| --- | --- |
| `scan_plural_rule("nl.json", "nl", GERMAN_PLURAL_FORM)` | `[]`, kein Fund |
| `scan_plural_rule("es.json", "es", GERMAN_PLURAL_FORM)` | zwei Funde, darunter `es.json: carries the German plural rule, which is not the rule of es` |
| `scan_plural_rule("nl.json", "nl", "nplurals=3; plural=(n > 2);")` | ein Fund, die fremde Zeichenkette wird wörtlich genannt |

Die dritte Zeile ist die wichtige: das Gate schweigt für `nl` nicht pauschal, sondern findet
weiterhin eine falsche Regel. Ein Gate, das für eine Sprache blind geworden wäre, hätte dieselbe
erste Zeile geliefert.

## Die Ausnahmeliste ist gefunden und nicht geraten

Drei Läufe, in dieser Reihenfolge:

| Lauf | Ergebnis |
| --- | --- |
| kein Eintrag für `nl` in der Tabelle | `AssertionError: languages without a list of exceptions: ['nl']` |
| leeres Mapping `"nl": {}` | acht Funde, vier Schlüssel über zwei Dateien, erster davon `nl.json: 'Findling' is still the English source string` |
| vier begründete Einträge | grün, 52 passed |

Beurteilt wurde je Schlüssel: `Findling` ist der Eigenname der App, `PDF` der eines
Dateiformats, `%1$s in %2$s` sind zwei Platzhalter mit der Präposition dazwischen, die das
Niederländische genauso schreibt wie das Englische und das Deutsche, und `Spreadsheets` ist das
Wort, das die niederländische Nextcloud-Oberfläche für diesen Filter selbst führt.
**Die niederländische Liste ist damit die längste der drei neuen Sprachen** (nl 4, it 3, es 2),
und das ist die Eigenschaft, die der Plan vorhergesagt hat: das Niederländische hat mehr
englische Fachwörter unverändert übernommen als die romanischen Sprachen. Vorhergesagt war es
trotzdem nur der Größe nach; welcher Schlüssel es ist, hat erst der Lauf gesagt.

## Das Gate hat keine Logikänderung gebraucht

`git diff backend/tests/test_admin_ui_contract.py` zeigt **55 Zufügungen und 0 Löschungen**,
verteilt auf genau drei Stellen: das Konstantenpaar mit seinem Begründungsabsatz, der Eintrag
im Tupel, der Eintrag in `VALUES_THAT_MAY_EQUAL_THEIR_KEY`. Kein Scanner, kein Testrumpf und
keine Zahl im Testnamen ist angefasst worden.

Das ist mehr als die 39 Zeilen des italienischen Plans, und der Unterschied ist vollständig der
Begründungsabsatz: Italienisch brauchte einen Absatz über die fehlende Regionalvariante,
Niederländisch braucht zusätzlich die zwei Sonderfälle und die Warnung an den späteren Leser.
Die **Parametrisierung** selbst trägt damit ihre dritte neue Sprache, und zum ersten Mal eine
mit einer abweichenden Formenzahl.

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| Schlüsselmenge und Reihenfolge `nl.json` gegen `de.json` | gleich, 202 von 202 |
| Genau fünf Listenwerte, je **zwei** Einträge | 5 von 5 |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, `nplurals=2` | ja, in beiden Dateien |
| U+2014, U+2013, U+2019, U+00A0, U+202F in `nl.json`, `nl.js`, `l10n-dutch.md` | je 0 |
| Pipe-Zeichen in Schlüsseln und Formen | 0 |
| Prozentzeichen ohne erkannte Direktive | 0, und überhaupt kein literales Prozentzeichen |
| Platzhalterparität Schlüssel gegen Wert, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen über 40 Schlüssel mit Direktiven |
| Wert zu `Findling` | `Findling` |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Kataloge und die Doku, byteweise geprüft; der Git-Blob ist reines LF (0 CR) |
| `nl.js` beginnt mit `OC.L10N.register(` und endet mit der Regel als viertem Parameter | ja, byteweise geprüft |
| Objektvergleich `nl.js` gegen `nl.json` | identisch, 202 Schlüssel |
| `grep -c 'L10N_NL_JSON\|L10N_NL_JS'` | 4, gefordert waren mindestens 4 |
| Einträge in `L10N_CATALOGUES` | 12 |
| Kommentarabsatz vor `L10N_NL_JSON`, nennt die Zeichengleichheit mit der deutschen Regel | ja, 33 Zeilen, mit beiden Sonderfällen und der Warnung an den späteren Leser |
| `VALUES_THAT_MAY_EQUAL_THEIR_KEY["nl"]`, jeder Schlüssel mit Grund | 4 Einträge, alle vier mit Grund |
| `git diff` am Gate: nur Zufügungen in den drei genannten Bereichen | 55 zu, 0 weg |
| Neun Abschnitte der Doku in der Reihenfolge der beiden vorhandenen Sprachdateien | ja, maschinell ausgelesen |
| Datenzeilen der Tabelle gleich der Schlüsselzahl | 202 |
| Jeder Schlüssel aus `nl.json` kommt in der Doku vor | fehlend 0 |
| Ausnahmeliste der Doku gegen `VALUES_THAT_MAY_EQUAL_THEIR_KEY["nl"]` | dieselben vier Schlüssel, maschinell verglichen |
| Abschnitt "Abnahme" mit Datum TT.MM.JJJJ, `20-06` und `von keinem Muttersprachler gelesen` | alle drei vorhanden |
| Abschnitt "Pluralformen" nennt zwei Formen und die Zeichengleichheit | ja, beide Zeichenketten maschinell geprüft |
| Zeilen in `docs/l10n-dutch.md` | 534, gefordert waren mindestens 260 |
| Stammtreffer des Vokabular-Gates in der neuen Doku | 0 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q tests/test_public_artifacts.py` | 55 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped (dreimal gefahren, vor jedem Commit) |
| ruff check, ruff format --check, pyright, vulture | alle grün (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |
| `git diff --name-only 62ddacc..HEAD -- php/templates php/js php/lib backend/src` | leer, kein Baumhash fällig |
| Löschungen in den drei Commits | 0 |

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker, vorausschauend übernommen] Das Katalogpaar geht in EINEN Commit

- **Gefunden in:** nicht neu gefunden, sondern aus 20-05 mitgenommen
- **Problem:** Der Plan schneidet Task 1 auf `nl.json` und Task 2 auf `nl.js` plus Gate.
  `test_every_catalogue_carries_the_plural_rule_of_its_language` läuft über die Codes von
  `PLURAL_FORM_OF`, die heute eine `.json` haben, und liest zu jedem davon die `.js`
  **unbedingt**. Eine alleinstehende `nl.json` bringt das Gate deshalb nicht rot zum Fallen,
  sondern zum Absturz mit `FileNotFoundError`. Plan 20-05 hat das gemessen und als
  Mitzunehmendes in STATE.md hinterlegt.
- **Warum nicht anders zu lösen:** Die Projektregel "Gates lokal grün VOR jedem Commit" lässt
  den Zwischenstand nicht zu. Die Alternative, das Gate an ihn anzupassen, wäre die
  Logikänderung gewesen, die dieser Plan gerade nicht brauchen sollte.
- **Fix:** `nl.json` und `nl.js` stehen zusammen in `3f76cdc`. Beide sind ohnehin ein
  mechanisches Erzeugnis desselben Laufs. Der Gate-Eintrag bleibt ein eigener Commit
  (`e7ed056`).
- **Dateien:** `php/l10n/nl.json`, `php/l10n/nl.js`
- **Commit:** `3f76cdc`
- **Mitzunehmen in 20-07 und 20-08:** derselbe Schnitt. Für 20-07 mit dem Zusatz, dass dort
  **vier** Dateien entstehen (`pt_PT` und `pt_BR`, je `.json` und `.js`); jedes Paar ist ein
  Commit, oder alle vier sind einer.

### 2. [Rule 1 - Messung berichtigt die Erwartung] Der vierte Ausnahmeeintrag heißt Spreadsheets

- **Gefunden in:** Task 2, beim Lauf mit leerem Mapping
- **Problem:** Der Plan sagt voraus, die niederländische Liste werde "erfahrungsgemäß länger
  als bei den romanischen Sprachen" sein, weil das Niederländische mehr englische Fachwörter
  übernimmt. Das stimmt, aber nicht bei den Wörtern, bei denen man es erwarten würde: `file`
  heißt `bestand`, `folder` heißt `map`, `index` heißt `index` (und damit nicht wie der
  englische Schlüssel, der `Index Team Folders` heißt). Der eine zusätzliche Treffer gegenüber
  dem Italienischen ist `Spreadsheets`.
- **Fix:** Der Eintrag steht mit eigenem Grund in der Liste und in der Doku: die
  niederländische Nextcloud-Oberfläche führt dieses Wort selbst, und `Rekenbladen` wäre an
  dieser Stelle eine Erfindung. Der Filter soll heißen wie die Anwendung daneben.
- **Dateien:** `backend/tests/test_admin_ui_contract.py`, `docs/l10n-dutch.md`
- **Commits:** `e7ed056`, `d40e335`

### 3. [Rule 1 - Abweichung vom deutschen Bestand, begründet] Gerade Anführungszeichen für den Suchbegriff

- **Gefunden in:** Task 1, beim Festlegen der Typografie
- **Problem:** Der deutsche Bestand trennt zwischen typographischen Anführungszeichen für den
  Suchbegriff und geraden für Bezeichner und Befehle. Das Niederländische setzt in der
  Buchtypografie einfache Anführungszeichen, und deren schließende Hälfte ist zeichengleich mit
  U+2019, das die Apostrophregel dieses Katalogs ausdrücklich verbietet.
- **Fix:** Der Suchbegriff steht in geraden ASCII-Anführungszeichen, genau wie die Bezeichner.
  Der Entscheid und sein Grund stehen im Typografie-Abschnitt der Doku. Zwei Regeln, die
  einander widersprechen, sind schlechter als eine schlichte Schreibweise.
- **Dateien:** `php/l10n/nl.json`, `php/l10n/nl.js`, `docs/l10n-dutch.md`
- **Commits:** `3f76cdc`, `d40e335`

### Was diesmal NICHT nötig war: der Rule-3-Fix am Vokabular-Gate

20-04 und 20-05 brauchten je einen vierten Commit, weil das Wortstamm-Gate in
`tests/test_public_artifacts.py` über der neuen Sprachdoku fiel (Spanisch 61 Treffer,
Italienisch 9). Über `docs/l10n-dutch.md` fällt es **nicht**: das Niederländische schreibt
Datei als `bestand` und Speicherort als `opslag`, und keines der beiden trägt den gesperrten
Stamm. **0 Stammtreffer**, `tests/test_public_artifacts.py` 55 passed.

Die Prognose aus 20-04 hat für `nl` also gestimmt. Gemessen ist sie trotzdem worden, und das
bleibt die Regel: ein Lauf kostet Sekunden, eine falsche Prognose einen roten Commit. Für
Portugiesisch in 20-07 lautet die Prognose weiterhin "kein Treffer", und sie ist damit einmal
bestätigt und zweimal knapp danebengegangen.

### Kleine Abweichungen in der Form, nicht in der Sache

**Acht Begriffsentscheide mehr als die fünf verlangten.** Sie stehen begründet in der
Wortwahl-Tabelle.

**Zwei Pluralwerte tragen zweimal denselben Wortlaut.** `%n uur` und `en nog %n`. Das ist
korrektes Niederländisch (Maßangaben bleiben nach einem Zahlwort im Singular; der zweite Satz
trägt kein beugbares Hauptwort) und steht als eigener Absatz im Abschnitt "Pluralformen".

**Kein `%%` im Katalog.** Wie im Spanischen und Italienischen ist der einzige betroffene Satz
umformuliert (`honderd procent`). Die Schreibregel steht trotzdem im Typografie-Abschnitt.

## Was ausdrücklich NICHT geändert wurde

`PLURAL_FORM_OF["nl"]` und `FORM_COUNT_OF["nl"]` stehen unverändert so da wie nach 20-02; sie
sind hier benutzt und nicht angefasst worden. Die zehn Bestandskataloge, `docs/l10n-french.md`,
`docs/l10n-spanish.md`, `docs/l10n-italian.md` und `docs/l10n-catalogues.md` liegen byteweise
wie vor diesem Plan. `backend/tests/test_public_artifacts.py` ist **nicht** angefasst worden.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist
angefasst worden, also bewegt sich kein Baumhash.

`KAT-01` und `KAT-02` bleiben **ungehakt**. Beide umfassen zehn Katalogdateien, und sechs davon
stehen. Der Haken gehört frühestens zu 20-08.

Nicht gepusht.

## Bedrohungen dieses Plans

| ID | Erledigt durch |
| --- | --- |
| T-20-24 (drei Formen bei `nplurals=2`, Denial of Service) | `FORM_COUNT_OF["nl"]` ist 2, das Formenzahl-Gate aus 20-02 prüft je Pluralschlüssel, und die Vorlage war `fr.json` statt `es.json`; gemessen 5 von 5 mit genau zwei Formen |
| T-20-25 (niederländisches Prozentzeichen, Denial of Service) | `scan_percent_discipline` läuft über `nl.json` und `nl.js`, seit das Paar im Tupel steht; im Katalog steht überdies kein literales Prozentzeichen (`honderd procent`) |
| T-20-26 (U+2019 als Apostroph) | eigenes Abnahmekriterium über U+2014, U+2013, U+2019, U+00A0, U+202F in beiden Dateien und in der Doku, je 0 Treffer; dazu ein eigener Absatz im Typografie-Abschnitt und der Entscheid gegen typographische Anführungszeichen |
| T-20-27 (Regel aus `de.json` kopiert statt aus der Kerndatei gelesen) | akzeptiert wie im Plan, weil zwei gleiche Zeichenketten maschinell nicht nach Herkunft trennbar sind. Die Kontrolle ist der Begründungsabsatz im Gate und der Doppelabsatz in der Sprachdoku; beide stehen |
| T-20-28 (Katalog ohne Vorbehalt) | `docs/l10n-dutch.md`, Abschnitt "Abnahme", datiert auf den 25.09.2026, mit Plannummer und dem Satz "von keinem Muttersprachler gelesen" |
| T-20-SC (Paketinstallation) | keine Installation in dieser Phase |

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Keine.

## Self-Check: PASSED

`php/l10n/nl.json`, `php/l10n/nl.js`, `docs/l10n-dutch.md` und
`backend/tests/test_admin_ui_contract.py` liegen im Baum; die drei Commit-Hashes `3f76cdc`,
`e7ed056` und `d40e335` stehen in der Historie. Kein Eintrag fehlt.
