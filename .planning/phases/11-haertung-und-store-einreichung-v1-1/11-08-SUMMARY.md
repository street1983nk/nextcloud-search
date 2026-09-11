---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 08
subsystem: l10n
tags: [l10n, franzoesisch, fr-json, fr-js, gates, g1, g2, g3, g4, dash-gate, rel-01]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: docs/l10n-french.md, die am 11.09.2026 vom Owner abgenommene dreispaltige Tabelle ueber alle 174 Katalogschluessel (Plan 11-05)
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: der 174. Schluessel in den vier deutschen Katalogen und die harte Zahl 174 in test_the_german_catalogue_covers_both_german_language_codes (Plan 11-13, Entscheid V-1a)
  - phase: 09-eigene-ergebnisseite
    provides: die vier deutschen Katalogdateien und der Schluesselvergleich, an den sich das zweite Sprachpaar anhaengt
provides:
  - "php/l10n/fr.json, der franzoesische Katalog fuer die Serverseite, 174 Schluessel in der Reihenfolge von de.json"
  - "php/l10n/fr.js, derselbe Katalog als Aufruf von OC.L10N.register fuer den Browser"
  - "Gate G1: Schluesselgleichheit ueber alle sechs Katalogdateien, mit einer fehlenden Datei als benanntem Fehlschlag"
  - "Gate G2: kein leerer und kein englisch gebliebener FR-Wert, gegen eine benannte Ausnahmenliste statt gegen eine Schwelle"
  - "Gate G3: Platzhalter-Paritaet als Multimenge je Schluessel, ueber alle Formen eines Pluralwerts"
  - "Gate G4: die franzoesische Pluralregel in beiden Dateien, mit den fuenf Pluralschluesseln zu je zwei Formen"
  - "das auf die sechs Katalogdateien ausgedehnte Dash- und Emoji-Gate"
  - "vier wiederverwendbare Scanner (scan_key_sets, scan_french_completeness, scan_placeholder_parity, scan_french_plural_rule) und der geteilte Ausschneider catalogue_of"
affects: [11-09, 11-10, 11-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Katalog wird aus der abgenommenen Tabelle mit einem Einwegskript gegossen; das Skript wird nicht eingecheckt, das Erzeugnis wird geprueft"
    - "Der Formatierer des Einwegskripts beweist sich, bevor er etwas Neues schreibt: er reproduziert de.json und de.js zeichengleich, sonst bricht er ab"
    - "Wo Textgleichheit als Invariante nicht taugt, tritt eine Invariante an ihre Stelle, die die Zielsprache tatsaechlich halten kann: Platzhalter-Paritaet statt gleicher Woerter"
    - "Jedes Gate bekommt einen Selbsttest an mutierter Eingabe, damit ein geloeschter Rumpf nicht als sauberer Baum durchgeht"
    - "Ein Gate ueber eine Dateimenge traegt seine Anti-Leerlauf-Klausel mit: eine fehlende Datei ist ein Fehlschlag mit Namen und kein stilles Weniger-Pruefen"

key-files:
  created:
    - php/l10n/fr.json
    - php/l10n/fr.js
  modified:
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "Der Guss ist mechanisch: ein Einwegskript liest docs/l10n-french.md, zieht die 173 Tabellenzeilen, nimmt Findling aus der Ausnahmenliste dazu und schreibt beide Dateien. Von Hand abgeschrieben waere genau die Fehlerquelle gewesen, gegen die die Tabelle gebaut wurde"
  - "Das Skript prueft sich selbst, bevor es schreibt: sein Formatierer muss de.json und de.js aus deren eigenen Daten zeichengleich reproduzieren. Erst danach giesst er fr. Damit ist die Formgleichheit der sechs Dateien bewiesen und nicht behauptet, insbesondere die einzeilige Schreibweise der Pluralliste, die json.dumps mit indent nicht liefert"
  - "G2 vergleicht die Gleichheit mit dem Quellstring auf dem Wert und nicht auf der einzelnen Pluralform. Der Singular von %n minute ist im Franzoesischen %n minute, richtig so; eine Pruefung je Form haette eine dritte Ausnahme verlangt fuer einen Wert, der uebersetzt ist. Das ist zugleich die Lesart der maschinellen Pruefungen von docs/l10n-french.md, wo die Zahl 2 lautet und beide benannt sind. Die Leere wird weiterhin ueber jede Form geprueft, weil eine leere zweite Pluralform eine leere Zeile auf der Seite ist"
  - "Die vier Gates liegen in backend/tests/test_admin_ui_contract.py und nicht in einer neuen Datei, weil der de/de_DE-Vergleich dort lebt. Zwei Orte fuer eine Frage sind der Widerspruch, den die Audits dieses Projekts sonst aufschreiben"
  - "Der Ausschneider fuer das Objekt der .js-Datei steht jetzt als catalogue_of einmal da und wird von den neuen Gates benutzt. Die bestehenden Tests sind unberuehrt geblieben: ihre Zusicherungen aendern sich nicht, und eine Umschreibung waere Aenderung ohne Anlass"
  - "Die harte Zahl 174 ist nicht angefasst worden. Sie stand schon richtig, weil Plan 11-13 sie in Welle 2 mitsamt Docstring gehoben hat; der FR-Katalog uebersetzt die vorhandenen Schluessel und erfindet keinen"
  - "Das Dash-Gate liest alle sechs Katalogdateien und nicht nur die zwei franzoesischen. Eine Regel, die fuer eine Sprache gilt und fuer die anderen nicht, ist die Asymmetrie, an die sich in einem Jahr niemand erinnert"
  - "Die beiden neuen Dateien liegen mit LF im Arbeitsbaum, wie es der Plan verlangt; der Index fuehrt sie wie die vier deutschen mit LF, und ein Auschecken auf dieser Maschine macht daraus CRLF. Deshalb steht in keinem Gate eine Byte-Pruefung auf den Wagenruecklauf: sie waere in CI gruen und in jeder Windows-Arbeitskopie rot. Die Pruefung ist einmal beim Guss gefahren worden"

patterns-established:
  - "Ein Generator, der eine bestehende Datei nachbauen kann, darf eine neue schreiben; kann er es nicht, ist sein Formatbegriff falsch und nicht die Quelle"
  - "Der Beweis der Rot-Faehigkeit laeuft zweimal: als Selbsttest an einer Probe im Test und einmalig als Mutation am echten Baum, mit anschliessender Wiederherstellung"

requirements-completed: []

# Metrics
duration: 55min
completed: 2026-09-11
---

# Phase 11 Plan 08: Der Guss des franzoesischen Katalogs und seine vier Gates Summary

**`php/l10n/fr.json` und `php/l10n/fr.js` sind mechanisch aus der am 11.09.2026 abgenommenen Tabelle gegossen, 174 Schluessel in der Reihenfolge von `de.json` mit der franzoesischen Pluralregel, und vier Gates plus das ausgedehnte Dash-Gate halten ab jetzt sechs Katalogdateien zusammen, deren Rot-Faehigkeit an zehn Mutationen des echten Baums belegt ist.**

## Was entstanden ist

Die Vorbedingung aus Phase 9 ist eingeloest: die App liefert eine dritte Sprache,
vollstaendig und in beiden Dateiformaten, und der Schluesselvergleich, der bisher
vier deutsche Dateien zusammengehalten hat, umfasst jetzt sechs.

### Der Guss (Task 1 und 2)

Ein Einwegskript liest `docs/l10n-french.md`, zieht die 173 Zeilen der
dreispaltigen Tabelle, nimmt `Findling` mit dem Wert `Findling` aus der
Ausnahmenliste dazu und schreibt beide Dateien in der Schluesselreihenfolge von
`de.json`. Die fuenf Pluralzeilen werden am Trenner ` / ` in zwei Formen
zerlegt, Singular zuerst.

Bevor das Skript etwas Neues schreibt, beweist es seinen Formatbegriff: es baut
`de.json` und `de.js` aus deren eigenen Daten nach und bricht ab, wenn auch nur
eine Zeile abweicht. Das war noetig und nicht Zierde. Die Pluralwerte stehen in
den Bestandsdateien einzeilig als `["%n Minute", "%n Minuten"]`, und `json.dumps`
mit `indent=4` bricht eine Liste ueber vier Zeilen um; ein Guss ohne diesen
Selbsttest haette zwei Dateien geliefert, die inhaltlich stimmen und formal aus
einer anderen Welt kommen.

Gemessen am Erzeugnis:

| Groesse | Wert |
|---|---:|
| Schluessel, Menge und Reihenfolge wie `de.json` | 174 |
| Pluralschluessel mit genau zwei Formen | 5 |
| Schluessel mit printf-Direktiven | 34 |
| Abweichungen der Platzhalter-Paritaet | 0 |
| FR-Werte gleich ihrem Quellstring | 2, beide benannt |
| U+2019, U+2014, U+2013, U+00A0, U+202F | je 0 |
| leere Werte | 0 |

`fr.js` traegt `OC.L10N.register` mit der Kennung `findling`, dasselbe Objekt und
die Pluralregel `nplurals=2; plural=(n > 1);` als vierten Parameter,
zeichengleich mit `pluralForm` in `fr.json`.

### Die vier Gates und das Dash-Gate (Task 3)

Alle in `backend/tests/test_admin_ui_contract.py`, wo der de/de_DE-Vergleich
schon liegt.

| Gate | Test | Was er prueft |
|---|---|---|
| G1 | `test_all_six_catalogues_carry_the_same_keys` | `de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js` tragen dieselbe Schluesselmenge. Zuerst prueft er die Existenz aller sechs und meldet eine fehlende Datei mit Namen, dann vergleicht er die Schluesselmengen gegen die erste und nennt bei einer Abweichung die symmetrische Differenz |
| G2 | `test_every_french_value_carries_a_french_wording` | Kein FR-Wert ist leer, und keiner ist mit seinem englischen Schluessel identisch, ausser `Findling` und `Page %s`. Die Ausnahmen stehen als Modulkonstante `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` mit ihrem Grund, und der Test prueft zusaetzlich, dass beide Schluessel im Katalog wirklich existieren, damit keine Ausnahme ins Leere zeigt |
| G3 | `test_no_french_value_loses_or_invents_a_placeholder` | Fuer jeden Schluessel ist die sortierte Liste der Prozent-Direktiven im FR-Wert dieselbe wie im Schluessel, ueber alle Formen eines Pluralwerts. Multimenge und nicht Menge: zwei gleiche Direktiven sind zwei. Der Regulaerausdruck `%%\|%\d+\$[sd]\|%[sdn]` erfasst das verdoppelte Prozentzeichen, die nummerierte Form mit Dollarzeichen, die einfache und das `%n` der Pluralformen. Mit Anti-Leerlauf-Klausel, damit ein Katalog ohne Direktiven nicht als perfekt gilt |
| G4 | `test_the_french_catalogues_carry_the_french_plural_rule` | `fr.json` traegt `nplurals=2; plural=(n > 1);`, `fr.js` denselben String, die deutsche Regel steht in keiner der beiden, und die fuenf Pluralschluessel sind dieselben wie im Deutschen und tragen je zwei Formen |
| Dash | `test_no_file_of_the_page_carries_a_dash_or_an_emoji` | Liest zusaetzlich zu den sechs Dateien der beiden Seiten jetzt die sechs Katalogdateien auf Gedankenstrich und Emoji. Begruendung im Docstring: franzoesische Typographie bringt Guillemets und Apostrophe mit, die harmlos sind, aber der Gedankenstrich ist gebraeuchlich und waere in einer Datei eingezogen, die bisher kein Gate dieses Repositoriums gelesen hat |

Jedes der vier Gates hat seinen Selbsttest an einer mutierten Probe im Test
selbst, nach dem Muster der Datei. Zusaetzlich sind alle fuenf einmal am echten
Baum mutiert und wieder hergestellt worden:

| Mutation | Gate wird rot |
|---|---|
| ein Schluessel aus `fr.json` entfernt | G1 |
| `fr.json` geloescht | G1, mit Dateinamen |
| ein Wert geleert | G2 |
| ein Wert auf den englischen Quellstring gesetzt | G2 |
| `%1$s dans %2$s` zu `%1$s dans` verkuerzt | G3 |
| zweite Pluralform verliert ihr `%n` | G3 |
| deutsche Pluralregel in `fr.json` | G4 |
| abweichende Regel in `fr.js` | G4 |
| ein Pluralwert zur Zeichenkette gemacht | G4 |
| Gedankenstrich in einem Katalogwert | Dash-Gate |

Die harte Zahl 174 in `test_the_german_catalogue_covers_both_german_language_codes`
steht unveraendert, und der Docstring dort nennt den Entscheid V-1a wie von Plan
11-13 hinterlassen. Dieser Plan hat sie geprueft und nicht angefasst.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] G2 vergleicht auf dem Wert und nicht auf der Pluralform**

- **Found during:** Task 3, erster Lauf der Gates
- **Issue:** Die erste Fassung von `scan_french_completeness` hat jede Form
  einzeln gegen den Schluessel gehalten und drei Treffer gemeldet, darunter
  `%n minute`, dessen franzoesischer Singular zeichengleich `%n minute` lautet.
  Das ist korrektes Franzoesisch und kein fehlender Wortlaut. Die Alternative
  waere eine dritte Ausnahme gewesen, die `docs/l10n-french.md` nicht nennt, und
  der Plan verlangt eine Liste, die aus dieser Datei gefuellt ist.
- **Fix:** Die Gleichheit mit dem Quellstring wird auf dem Wert geprueft, womit
  ein Pluralwert als Liste nie gleich seinem Schluessel sein kann. Das ist die
  Lesart, die die maschinellen Pruefungen der abgenommenen Datei selbst
  verwenden, wo die Zahl 2 lautet. Die Leere wird unveraendert ueber jede Form
  geprueft, damit eine leere zweite Pluralform weiter ein Befund bleibt. Die
  Begruendung steht im Docstring des Scanners.
- **Files modified:** backend/tests/test_admin_ui_contract.py
- **Commit:** 1c5fea8

### Bewusste Auslegungen

**Keine Byte-Pruefung auf den Wagenruecklauf in einem Gate.** Das
Abnahmekriterium von Task 2 verlangt eine Datei ohne Wagenruecklauf, und der
Guss hat das geprueft: beide Dateien liegen mit LF im Arbeitsbaum, ohne BOM, mit
abschliessendem Zeilenumbruch. Als dauerhaftes Gate gehoert diese Pruefung aber
nicht in den Baum. Das Repositorium fuehrt die vier deutschen Katalogdateien im
Index mit LF, und die Entwicklungsmaschine checkt mit `core.autocrlf=true` aus,
weshalb `de.json` im Arbeitsbaum CRLF traegt. Ein Gate auf Byte-Ebene waere in
CI gruen und in jeder Windows-Arbeitskopie rot, also ein Gate, das die falsche
Sache misst. Die Gates lesen die Dateien im Textmodus, wie es
`test_the_german_catalogue_covers_both_german_language_codes` seit Phase 9 tut
und in seinem Docstring auch begruendet.

**Das Einwegskript ist nicht eingecheckt**, wie der Plan es verlangt. Es lag
unter dem Scratchpad-Verzeichnis dieser Sitzung. Was von ihm bleibt, ist das
Erzeugnis und die Gates, die es halten.

## Authentication Gates

Keine.

## Verification

Aus `backend/`:

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | 2016 passed, 15 skipped (Grundlinie 2012, plus die vier neuen Gates) |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 121 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | ohne Befund |

Die PHP-Seite ist nicht beruehrt: die beiden neuen Dateien sind Katalogdaten,
kein PHP-Quelltext, und kein PHPUnit-Test liest die Katalogdateien.

## Known Stubs

Keine.

## Threat Flags

Keine. Der Katalog fuehrt keine Berechtigungsentscheidung, und die neuen Werte
laufen durch dieselbe Uebersetzungs- und Escaping-Kette wie die deutschen; T-11-30
ist durch das bestehende Escaping-Gate und das jetzt mitlesende Dash-Gate
abgedeckt, T-11-31 durch G3, T-11-32 durch G1 und T-11-33 durch G4.

## Commits

| Commit | Art | Inhalt |
|---|---|---|
| 7209146 | feat | `php/l10n/fr.json`, der Katalog fuer die Serverseite |
| 888d6f8 | feat | `php/l10n/fr.js`, derselbe Katalog fuer den Browser |
| 1c5fea8 | test | die vier Gates und das ausgedehnte Dash-Gate |

## Self-Check: PASSED

Alle drei Commits liegen in `git log`, alle vier genannten Dateien existieren.
