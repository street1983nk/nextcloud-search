---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 02
subsystem: l10n
tags: [ladepfad, pluralregeln, gate-parametrisierung, nextcloud-l10n, ci-pfadfilter, messung]

# Dependency graph
requires:
  - phase: 20-ui-kataloge-es-it-nl-pt
    plan: 01
    provides: "die fuenf Pluralschluessel als _<singular>_::_<plural>_ in allen sechs Bestandskatalogen und der an der Marke teilende Paritaetsscanner"
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "die vier Katalog-Gates in test_admin_ui_contract.py, darunter G4 mit FRENCH_PLURAL_FORM und GERMAN_PLURAL_FORM"
provides:
  - "docs/l10n-catalogues.md: der gemeinsame Beweis aller Sprachdateien der Phase, sieben Abschnitte, Ladepfad und Pluralregeln an zwei laufenden Nextclouds gemessen"
  - "PLURAL_FORM_OF: acht Sprachcodes auf ihre woertliche Regelzeichenkette, zeichengleich mit der Regeltabelle der Doku"
  - "FORM_COUNT_OF: acht Sprachcodes auf ihre Formenzahl, bewusst nicht aus nplurals= geparst"
  - "scan_plural_rule(name, code, plural_form): der sprachbewusste Kopierfehler-Test, mit dem niederlaendischen Sonderfall als gestellter Gegenprobe"
  - "test_every_catalogue_carries_the_plural_rule_of_its_language: laeuft ueber jede vorhandene php/l10n/<code>.json und nimmt die kommenden selbst mit"
  - "JS_PLURAL_FORM: die Regel der .js wird ausgeschnitten statt enthalten-geprueft, beide Haelften einer Sprache laufen durch denselben Scanner"
  - "php/l10n/** in beiden Pfadlisten von python.yml: ein reiner Katalogcommit startet die Katalog-Gates"
affects: [20-03 (Scanner parametrisiert, erbt das Mapping), 20-04 bis 20-08 (jede neue Sprache wird vom Gate automatisch mitgenommen, sobald ihre Datei da ist), 20-09 (CI-Sprachbeweis)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Regel aus einer fremden Codebasis wird auf jeder Version des eigenen Versionsfensters gelesen, nicht nur auf der Entwicklungsinstanz; sind beide gleich, ist das ein Ergebnis und keine ausgelassene Frage"
    - "Ein Gate, das eine Zeichenkette prueft, leitet seine Erwartung nicht aus derselben Zeichenkette ab: die Formenzahl steht als eigene Zahl da und wird nicht aus nplurals= geparst"
    - "Ein sprachgebundener Vorwurf ('traegt die deutsche Regel') wird sprachbewusst, sobald eine zweite Sprache dieselbe Zeichenkette rechtmaessig fuehrt; die gestellte Gegenprobe im Testrumpf haelt fest, warum"
    - "Ein Pfadfilter, der den Gegenstand eines Gates nicht enthaelt, macht das Gate unfaehig rot zu fallen; er wird mit einem YAML-Parser geprueft und nicht mit einer Textsuche"

key-files:
  created:
    - docs/l10n-catalogues.md
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-02-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py
    - .github/workflows/python.yml

key-decisions:
  - "PLURAL_FORM_OF fuehrt fuer fr die AUSGELIEFERTE Regel (nplurals=2; plural=(n > 1);) und nicht die Kernregel (nplurals=3). Der Kern beider Instanzen fuehrt Franzoesisch mit drei Formen; Findling liefert seit 11-08 zwei, die Variante ist in beiden Haelften korrekt und der Owner hat die Wortlaute dreimal in dieser Form abgenommen. Ein Umbau auf drei Formen waere eine Wortlautaenderung ohne Nutzen. Genau diese Zeile ist der Grund, warum zwei Konstanten nicht reichen"
  - "Die Doku fuehrt ZWEI Regelbloecke, den der Kerndateien und den der Auslieferung, und sagt ausdruecklich, welcher massgeblich ist. Ein Block allein haette entweder die fr-Abweichung verschwiegen oder die Herkunft der sieben uebrigen Zeichenketten verloren"
  - "Die .js-Haelfte laeuft durch denselben Scanner wie die .json, dafuer wird die Regel mit JS_PLURAL_FORM ausgeschnitten. Der Bestand prueft nur 'rule in script' plus 'GERMAN_PLURAL_FORM not in script'; die zweite Zeile waere fuer nl dauerhaft rot gewesen, und sie ersatzlos zu streichen haette eine Pruefung verloren, die heute traegt"
  - "Ein Sprachcode aus PLURAL_FORM_OF OHNE Katalogdatei ist in diesem Gate kein Fehler. Das Fehlen einer Datei ist die Frage des Schluesselgleichheits-Gates ueber L10N_CATALOGUES; zwei Gates fuer dieselbe Frage sind eine Frage zu viel. Die Anti-Leerlauf-Klausel verlangt deshalb nur, dass die drei heute ausgelieferten Codes im Lauf vorkommen"
  - "KAT-01 und KAT-02 bleiben UNGEHAKT. KAT-02 verlangt den Ladepfad-Beweis VOR der Uebersetzungsarbeit, und der steht jetzt, aber die Anforderung umfasst auch die Uebersetzungen samt datiertem Vorbehalt. Beide Haken gehoeren fruehestens zu 20-08"

requirements-completed: []

# Metrics
duration: 30min
completed: 2026-09-25
---

# Phase 20 Plan 02: Ladepfad-Beweis, Pluralregeln und das sprachbewusste Gate Summary

**Der Ladepfad und die Pluralregeln der vier neuen Sprachen stehen jetzt gemessen in
`docs/l10n-catalogues.md` statt nur in der Research, das Pluralregel-Gate urteilt je Sprachcode
und kennt den niederlaendischen Sonderfall, und ein Commit, der nur eine Katalogdatei anfasst,
startet die Katalog-Gates ueberhaupt erst.**

## Was gebaut wurde

Drei Dinge, keine einzige neue Katalogdatei.

**Das Beweisdokument.** `docs/l10n-catalogues.md` (347 Zeilen, sieben Abschnitte) ist der
gemeinsame Beweis aller Sprachdateien dieser Phase. Die vier Sprachdokumente, die spaeter
entstehen, verweisen hierher, statt denselben Beweis viermal zu fuehren. Drei Messungen tragen
es, alle am 25.09.2026 an laufenden Containern gefahren und nicht aus der Research uebernommen.

**Die Datenseite des Gates.** `PLURAL_FORM_OF` bildet acht Sprachcodes auf ihre woertliche
Regelzeichenkette ab, `FORM_COUNT_OF` dieselben acht auf ihre Formenzahl.
`scan_french_plural_rule` ist `scan_plural_rule(name, code, plural_form)` geworden, das Gate
`test_the_french_catalogues_carry_the_french_plural_rule` heisst
`test_every_catalogue_carries_the_plural_rule_of_its_language` und laeuft ueber jede vorhandene
`php/l10n/<code>.json`. Die harte 2 der Formenzahl ist weg.

**Der Lueckenschluss in CI.** `php/l10n/**` steht in beiden Pfadlisten von `python.yml`. Vorher
startete ein reiner Katalogcommit `php.yml` und `integration.yml`, aber kein einziges
Katalog-Gate.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | Beweisdokument, Regeln auf zwei Nextclouds gelesen | `a283b7c` | `docs/l10n-catalogues.md` |
| 2 | Das Pluralregel-Gate urteilt je Sprachcode | `1e6881f` | `backend/tests/test_admin_ui_contract.py` |
| 3 | Ein Katalogcommit startet die Katalog-Gates | `5b78e08` | `.github/workflows/python.yml` |

## Die drei Messungen

### Messung A, Ladepfad (Erfolgskriterium 4)

Die Sonde der Research ist nachgefahren worden, nicht zitiert. Container `findling-nextcloud`
(`nextcloud:34.0.3-apache`), echte Probedatei `php/l10n/pt.json`, Fragen ueber `IFactory`:

```
findAvailableLanguages(findling): en,de,de_DE,fr,pt
pt      exists=yes  code=pt     t(Findling)=PROBE_PT
pt_PT   exists=no   code=en     t(Findling)=Findling
pt_BR   exists=no   code=en     t(Findling)=Findling
es      exists=no   code=en     t(Findling)=Findling
it      exists=no   code=en     t(Findling)=Findling
nl      exists=no   code=en     t(Findling)=Findling
fr      exists=yes  code=fr     t(Findling)=Findling
de_DE   exists=yes  code=de_DE  t(Findling)=Findling
```

Ein Nutzer auf `pt_PT` oder `pt_BR` landet auf `en`, obwohl ein `pt`-Katalog danebenliegt, und
auf `pt` kann niemand stehen, weil `core/l10n/` diesen Code nicht fuehrt. Also **zehn Dateien**.
Probedatei und Sondenskript sind auf beiden Seiten entfernt, `git status --short` war danach
leer.

### Messung B, Pluralregeln auf zwei Versionen (Erfolgskriterium 3)

Feld `pluralForm` aus `core/l10n/<code>.json`, gelesen in `findling-nextcloud` (34.0.3) **und**
in `nc35-nc` (35.0.0). **Beide Instanzen fuehren fuer alle acht Codes dieselbe Zeichenkette,
Zeichen fuer Zeichen.** Es gibt keinen Versionsbefund, der zu entscheiden waere.

Ein Befund steckt trotzdem darin: der Kern fuehrt **Franzoesisch mit `nplurals=3`**, Findling
liefert seit Plan 11-08 zwei Formen aus. Das ist kein Fehler (die Zwei-Formen-Variante ist in
beiden Haelften korrekt), aber es ist der Grund, warum zwei feste Konstanten nicht reichen: `fr`
muss bei zwei Formen bleiben, waehrend `es` auf drei geht.

### Messung C, Formenwahl

Probekataloge mit den Formen `%n FORM0`, `%n FORM1`, `%n FORM2`, gefragt ueber `IFactory`:

| Sprache | PHP n=0 | n=1 | n=2 | n=5 | n=1000000 |
| --- | --- | --- | --- | --- | --- |
| `es` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `it` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `nl` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `pt_PT` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `pt_BR` | **FORM0** | FORM0 | FORM1 | FORM1 | FORM1 |

**PHP erreicht FORM2 nie.** Die deklarierte Regel, ausgewertet wie der Browser sie auswertet,
waehlt fuer `es` und `it` bei n=2 dagegen Index **2**. Daher: drei Formen deklarieren, Form 1 und
Form 2 wortgleich.

Der Falle des Kerns ist hinterhergemessen worden, nicht nur nacherzaehlt. `core/l10n/pt_BR.json`
traegt `["%n resultado", "%n de resultados", "%n resultados"]`, und dieselbe Instanz antwortet
darauf:

```
pt_BR  n=1  1 resultado      n=2  2 de resultados      n=5  5 de resultados
```

## Dass das Gate rot faellt, ist bewiesen und nicht behauptet

Drei gestellte Schaeden, jeder einzeln eingebaut, gemessen und zurueckgenommen
(`git status --short` danach leer, die Kataloge byteweise wie vorher):

| Gestellter Schaden | Fund des Gates |
| --- | --- |
| `fr.json` bekommt die deutsche Regel | `fr.json: carries the German plural rule, which is not the rule of fr` plus die Zeile, dass sie nicht die Regel von `fr` ist |
| ein `fr`-Pluralwert bekommt eine dritte Form | `fr.json: '_%n minute_::_%n minutes_' carries 3 forms where fr wants 2` |
| `fr.js` bekommt die deutsche Regel | `fr.js: carries the German plural rule, which is not the rule of fr` |

Der dritte Fall ist der, den der alte Test nicht so gefunden haette: er prueft die `.js` nicht
mehr mit "enthaelt die Regel der `.json`", sondern schneidet die vierte Stelle von
`OC.L10N.register` heraus und schickt sie durch denselben Scanner.

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| `docs/l10n-catalogues.md` traegt alle sieben Abschnittsueberschriften | ja, Abschnitte 1 bis 7 |
| Regeltabelle mit je einer Zeile fuer es, it, nl, pt_PT, pt_BR, fr, de (und de_DE) | 8 Zeilen, Zeichenkette woertlich |
| Fuer jede Sprache vermerkt, ob NC 34 und NC 35 dieselbe Zeichenkette fuehren | ja, eigene Spalte, acht mal "ja" |
| `grep -c 'nplurals=3' docs/l10n-catalogues.md` >= 4 | 11 |
| Gezaehlte Schluesselzahl stimmt mit `de.json` ueberein | 202, am 25.09.2026 gezaehlt |
| Keine U+2014, U+2013, U+2019, U+00A0, U+202F im Dokument | keine, geprueft; auch keine Symbolzeichen (Emojis) |
| `git status --short` nennt keine Probedatei unter `php/l10n/` | leer nach jeder Sonde |
| `grep -c 'PLURAL_FORM_OF'` >= 4 | 5 |
| Alle acht Codes in `PLURAL_FORM_OF` | keiner fehlt |
| `grep -c 'FORM_COUNT_OF'` >= 3 | 3 |
| `grep -c 'scan_french_plural_rule'` | 0 (und im ganzen Codebaum 0) |
| Zeichenkette in `PLURAL_FORM_OF` zeichengleich mit der Regeltabelle der Doku | ja, maschinell verglichen, 8 von 8 |
| `grep -c "php/l10n/\*\*" .github/workflows/python.yml` | genau 2 |
| YAML-Parserpruefung beider Pfadlisten | ok, Trigger unveraendert |
| `git diff --stat .github/workflows/python.yml` | 19 Zeilen zugefuegt, 0 geloescht |
| `git diff --name-only -- php/templates php/js php/lib backend/src` | leer, kein Baumhash faellig |
| ruff check, ruff format --check, pyright, vulture | alle gruen (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |
| `cd backend && uv run pytest -q` | 2877 passed, 15 skipped |

## Abweichungen vom Plan

### 1. [Rule 2 - fehlende Pruefung] Die `.js`-Haelfte laeuft durch denselben Scanner

- **Gefunden in:** Task 2
- **Problem:** Der Bestand prueft die `.js` mit zwei Zeilen: `rule in script` und
  `GERMAN_PLURAL_FORM not in script`. Die zweite ist genau die Zeile, die fuer `nl` dauerhaft
  rot waere. Sie ersatzlos zu streichen haette eine heute tragende Pruefung verloren; sie
  sprachbewusst im Testrumpf nachzubauen haette dieselbe Logik ein zweites Mal aufgestellt.
- **Fix:** `JS_PLURAL_FORM` schneidet die vierte Stelle von `OC.L10N.register` heraus, und beide
  Haelften einer Sprache laufen durch `scan_plural_rule`. Das ist zugleich strenger als der
  Bestand: eine `.js`, die die richtige Regel irgendwo im Rumpf traegt und eine andere
  deklariert, waere durch den Enthalten-Test gekommen.
- **Dateien:** `backend/tests/test_admin_ui_contract.py`
- **Commit:** `1e6881f`

### 2. [Rule 1 - Messung berichtigt die Planvorgabe] Die n=0-Abweichung betrifft nur pt_PT

- **Gefunden in:** Task 1, Abschnitt 5 des Dokuments
- **Problem:** Der Plan schreibt vor, "die verbleibende benannte Abweichung bei n=0 fuer pt_PT
  **und pt_BR**" zu dokumentieren: JS waehle den Singular, PHP den Plural. Die Messung zeigt es
  anders: fuer `pt_BR` waehlt PHP bei n=0 ebenfalls FORM0, weil Symfonys `pt_BR`-Regel die Null
  wie den Singular behandelt. Nur `pt_PT` weicht ab.
- **Fix:** Das Dokument nennt `pt_PT` als einzige betroffene Sprache und sagt ausdruecklich, dass
  die Messung hier eine naheliegende Erwartung berichtigt. Die Sache selbst (die Grenze wird
  benannt statt beseitigt, betroffen ist hoechstens die Sekundenzeile der Sperre) ist
  unveraendert.
- **Dateien:** `docs/l10n-catalogues.md`
- **Commit:** `a283b7c`

### 3. [Rule 3 - Blocker] Eine Formenprobe ohne `%n` misst nichts

- **Gefunden in:** Task 1, Messung C
- **Problem:** Der erste Lauf der Probekataloge trug die Formen `FORM0`, `FORM1`, `FORM2` und
  lieferte fuer jede Anzahl `FORM0|FORM1|FORM2` zurueck. Grund:
  `L10NString::__toString()` fuellt die Parameterliste nur, wenn der Wert ein `%n` traegt, und
  ohne Parameter gibt der `IdentityTranslator` die verbundene Kette unveraendert zurueck. Eine
  ungeprueft uebernommene Probe dieser Bauart haette "PHP waehlt gar nicht" ergeben.
- **Fix:** Die Formen tragen `%n FORM0` und so fort. Der Nebenbefund steht als eigener Absatz im
  Dokument, damit die naechste Sonde nicht dieselbe Stunde verliert.
- **Dateien:** `docs/l10n-catalogues.md`
- **Commit:** `a283b7c`

### Kleine Abweichung in der Form, nicht in der Sache

Das Abnahmekriterium von Task 3 verlangt "unmittelbar vor jedem der beiden Eintraege mindestens
eine Kommentarzeile, die `l10n` oder `Katalog` nennt". Der Hausstil dieser Datei setzt einen
ganzen Begruendungsabsatz davor, nicht eine Zeile. Beide Absaetze nennen die Kataloge mehrfach,
und zusaetzlich nennt die jeweils **letzte** Zeile vor dem Eintrag `l10n`, damit das Kriterium
auch woertlich gelesen erfuellt ist.

Dazu eine Notiz zur Schreibweise: der Begruendungsabsatz des ersten Eintrags sagt, warum die
Katalogverzeichnis-Zeile enger ist als `php/**`, ohne die Zeichenfolge `php/l10n/**` ein drittes
Mal zu schreiben. Sonst waere `grep -c` auf 3 statt auf die geforderten 2 gestiegen.

## Was ausdruecklich NICHT geaendert wurde

`KAT-01` und `KAT-02` bleiben ungehakt. Dieser Plan liefert den Beweis, den KAT-02 **vor** der
Uebersetzungsarbeit verlangt, und die Parametrisierung, die KAT-01 fordert; beide Anforderungen
umfassen aber die zehn Katalogdateien selbst und werden fruehestens mit 20-08 erfuellt.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist angefasst
worden, also bewegt sich kein Baumhash. Die sechs Bestandskataloge liegen byteweise so da wie
vor diesem Plan; die drei Rot-Beweise sind vollstaendig zurueckgenommen.

Ein Gate, das die Zeichengleichheit zwischen `docs/l10n-catalogues.md` und `PLURAL_FORM_OF`
dauerhaft haelt, ist **nicht** gebaut worden: der Plan fuehrt die Zeichengleichheit als
Abnahmekriterium und nicht als Gate, und ein zusaetzlicher Test, der eine Doku-Datei liest, waere
ueber den Auftrag hinausgegangen. Die Gleichheit ist bei der Ausfuehrung maschinell nachgewiesen
(8 von 8). Wer sie dauerhaft halten will, baut das Gate in 20-03, wo die Scanner ohnehin
angefasst werden.

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Keine.

## Self-Check: PASSED

`docs/l10n-catalogues.md`, `backend/tests/test_admin_ui_contract.py` und
`.github/workflows/python.yml` liegen im Baum; die drei Commit-Hashes `a283b7c`, `1e6881f` und
`5b78e08` stehen in der Historie. Kein Eintrag fehlt.
