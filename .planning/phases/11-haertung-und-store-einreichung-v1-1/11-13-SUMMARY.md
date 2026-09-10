---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 13
subsystem: php-suche
tags: [di-07-03, v1-a, searchoutcome, ergebnisseite, l10n, 174-schluessel, rel-01]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-VORENTSCHEIDE.md, Entscheid v1-a vom 10.09.2026 (Plan 11-01), samt dem woertlichen Quellstring
  - phase: 07-gemeinsame-embedding-engine
    provides: DI-07-03, der Befund "Kandidaten vom Recheck verworfen, Nutzer sieht eine leere Liste"
  - phase: 09-ergebnisseite
    provides: das Gate gegen den ungeschuetzten Leerzustand und die $showEmpty-Entscheidung
provides:
  - "SearchOutcome::FAILURE_ALL_CANDIDATES_REJECTED, der fuenfte Zustand des Ergebnisobjekts"
  - "SearchService zaehlt die entschiedenen Kandidaten und vergibt den Zustand in der Reihenfolge Decke, Schweigen, neuer Zustand"
  - "die Ergebnisseite sagt im neuen Zustand einen Satz statt der Rechtschreibbitte, ohne Banner und ohne Aenderung an $showEmpty"
  - "der neue Zustand behaelt die naechste Seite; die vier alten verlieren sie weiterhin"
  - "der 174. Schluessel in de.json, de.js, de_DE.json und de_DE.js, englischer Quellstring und deutscher Wortlaut aus dem Entscheid"
  - "die harte Katalogzahl im Gate steht auf 174"
affects: [11-05, 11-08, 11-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Ergebniszustand, der eine Aussage ueber das Ergebnis ist und keine ueber den Lauf, wird von der Nein-naechste-Seite-Regel ausgenommen statt in sie eingereiht"
    - "Vorrangkette im Dienst: Feststellungen ueber den Lauf (Decke, Schweigen) schlagen die Feststellung ueber sein Ergebnis"
    - "Eine Zaehlvariable, die ausschliesslich liest, wird als solche kommentiert, damit ein Leser sie nicht fuer eine zweite Grenze haelt"
    - "Ein neuer Zustand geht ausdruecklich weder in $hasError noch in $hasHint ein, damit die drei Entscheidungszeilen der Phase 9 byteweise stehen bleiben"
    - "Eine gemessene Zahl wird nicht ueberschrieben, wenn der Code weiterlaeuft: sie bekommt eine zweite Zahl neben sich und beide werden zugesichert"

key-files:
  created: []
  modified:
    - php/lib/Service/SearchOutcome.php
    - php/lib/Service/SearchService.php
    - php/lib/Controller/PageController.php
    - php/lib/Search/Provider.php
    - php/templates/search.php
    - php/l10n/de.json
    - php/l10n/de.js
    - php/l10n/de_DE.json
    - php/l10n/de_DE.js
    - php/tests/Unit/SearchServiceTest.php
    - php/tests/Unit/PageControllerTest.php
    - php/tests/Unit/ProviderTest.php
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Owner hat unter V-1 keinen eigenen Wortlaut genannt, also gilt der Vorschlag des Dossiers woertlich. Es ist kein Gegenvorschlag gemacht worden: der Plan sieht dafuer keinen Spielraum vor, und ein Satz, den der Owner abgenommen hat, wird nicht vom Ausfuehrenden verbessert"
  - "Die Vorrangkette lautet Decke, Schweigen, neuer Zustand. Eine Decke und ein Schweigen sind Feststellungen ueber den Lauf, der neue Zustand ist eine Feststellung ueber sein Ergebnis; ein Lauf, der frueh gestoppt hat, hat ueber den Rest nicht entschieden, und ihm den neuen Zustand zu geben hiesse mehr zu behaupten, als der Lauf weiss"
  - "$allRejected steht als eigene Zeile zwischen $ceiling und $hasError, nicht in einer der beiden Summen. Damit bleiben $hasError, $hasHint und $showEmpty byteweise unveraendert, und das Gate der Phase 9 sieht dieselbe Entscheidung wie vorher"
  - "Die Ueberschrift des Leerzustands bleibt 'No file contains \"%s\"'. Sie ist auch im neuen Zustand wahr, denn keine Datei DIESES Nutzers enthaelt das Wort; nur der Satz darunter wechselt"
  - "PageController nimmt genau den einen Grund von der Nein-naechste-Seite-Regel aus, statt die Regel umzuschreiben. Die anderen vier verlieren die naechste Seite weiterhin"
  - "Der Provider bekommt nur einen Kommentar. Dass der Suchdialog keinen eigenen Satz traegt, ist die bestehende Linie des Produkts (Docstring von testEveryFailureOfTheServiceBecomesTheSameEmptyGroup) und keine Entscheidung dieses Plans"
  - "Die harte Katalogzahl steigt hier und nicht erst in 11-08, weil der Baum zwischen den beiden Plaenen sonst rot stuende"
  - "PHP_TREE_HASH wird nicht ueberschrieben, sondern bekommt PHP_TREE_HASH_TODAY neben sich. 4a4c6f62 ist ein Rohmesswert vom 09.09.2026, zitiert in rohdaten/40b-baumhash.txt und im Messbericht; ihn zu ueberschreiben hiesse eine berichtete Vergleichszahl zu retirieren"

patterns-established:
  - "Ein bedingter Plan liest seinen Entscheid, bevor er eine Datei oeffnet, und nennt die Belegzeile in der SUMMARY"
  - "Der geltende Wortlaut wird mit einem Python-Einzeiler gegen die Entscheid-Datei geprueft, nicht per Augenmass"
  - "Bytegleichheit einer Zeile wird gegen `git show HEAD:<datei>` bewiesen, nicht am Diff abgelesen"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-09-10
---

# Phase 11 Plan 13: Der Satz fuer den Lauf, der Kandidaten bekam und keinen behielt Summary

**Der Nutzer, dessen Begriffe im Fremdbestand haeufig sind, liest seit dem 10.09.2026 statt einer wortlosen leeren Liste den Satz "Andere Dateien enthalten dieses Wort, aber keine, die Sie oeffnen duerfen.", behaelt seine naechste Seite, und die Berechtigungskette ist am Diff beweisbar unveraendert.**

## Die Vorbedingung

Erster Handgriff, vor jedem Lesen von Code, wie der Plan es verlangt:
`11-VORENTSCHEIDE.md`, Abschnitt `## V-1`, Zeile 116 traegt woertlich

> **Entscheid 2026-09-10: v1-a.** DI-07-03 wird in v1.1.0 gefixt, als MEDIUM mit
> der von der Berechtigungskette getrennten Abhilfe. Plan 11-13 ist damit scharf
> und faehrt in Welle 2. Der Katalog steigt von 173 auf 174 Schluessel.

Der Plan ist also den BAU-Pfad gefahren. Zeile 120 haelt zusaetzlich fest, dass
der Owner keinen eigenen Wortlaut genannt hat, also der Vorschlag des Dossiers
woertlich gilt. Beide Zeichenketten sind byteweise uebernommen, ohne
Gegenvorschlag.

## Der Satz, wie er auf der Ergebnisseite steht

Der Leerzustand mit Suchbegriff, Block 4 von `php/templates/search.php`:

| Zeile | Englisch (Quelle) | Deutsch (de und de_DE) |
|---|---|---|
| Ueberschrift, unveraendert | `No file contains "%s"` | `Keine Datei enthält „%s“` |
| Text im neuen Zustand | `Other files contain this word, but none that you may open.` | `Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen.` |
| Text sonst, unveraendert | `Try another word, a part of a compound word, or check the spelling.` | `Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise.` |

Der Satz traegt echte Umlaute, keine Prozent-Direktive, keinen Gedankenstrich
und kein Emoji. Er nennt keine Zahl, keinen Dateinamen und keinen Pfad
(T-11-50). Kein Banner steht darueber, weder das Fehlerbanner noch der Hinweis.

Geprueft, nicht geschaetzt:

```
Owner en : 'Other files contain this word, but none that you may open.'
im Template gefunden: True
de.json:    Schluessel=174 vorhanden=True wert_gleich=True
de_DE.json: Schluessel=174 vorhanden=True wert_gleich=True
de.js:      Schluessel=174 vorhanden=True wert_gleich=True
de_DE.js:   Schluessel=174 vorhanden=True wert_gleich=True
```

## Die drei Zeilen der Phase 9, byteweise

Das schaerfste Kriterium des Plans, und es ist gegen `git show HEAD:` geprueft
und nicht am Diff abgelesen:

```
IDENTISCH $hasError = $silent || $drift || $noHome;
IDENTISCH $hasHint = !$hasError && ($ceiling || $degraded);
IDENTISCH $showEmpty = $hits === [] && (!$hasQuery || (!$hasError && !$hasHint));
```

`$allRejected` steht als eigene Zeile zwischen `$ceiling` und `$hasError` und
geht in keine der beiden Summen ein. `git diff php/templates/search.php`
enthaelt keine geaenderte Zeile, in der eine der drei Variablen definiert wird.
`grep -c print_unescaped php/templates/search.php` ist 0; jede neue
Ausgabezeile laeuft durch `p($l->t(`.

## Die Berechtigungskette

- `grep -c "MAX_ROUNDS = 3" php/lib/Search/Provider.php` ist unveraendert 1.
- `git diff php/lib/Service/SearchService.php` enthaelt genau eine Zeile mit
  `isReadable`, und die ist ein Kommentar, der festhaelt, dass die Frage die
  einzige Berechtigungsentscheidung bleibt. Keine Zeile aendert `isReadable`,
  `reduceIds` oder das Recheck-Budget.
- Die Zaehlvariable `$decided` liest ausschliesslich; sie summiert das bereits
  vorhandene `$consumed` je Seite und entscheidet nichts (T-11-51).

## Was gebaut wurde, Task fuer Task

**Task 1, der fuenfte Zustand im Dienst.** `SearchOutcome` traegt
`FAILURE_ALL_CANDIDATES_REJECTED = 'all_candidates_rejected'` mit einem
Docblock, der sagt, was die Konstante von den vier anderen unterscheidet: die
vier sagen, dass der Lauf nicht oder nicht zu Ende stattgefunden hat, diese
eine sagt, dass er stattgefunden hat und dass seine Antwort fuer diesen Nutzer
leer ist. Herkunft und Entscheiddatum stehen darin. Der Klassen-Docblock und
die Parameterzeile sagen fuenf statt vier. In `SearchService` zaehlt `$decided`
die entschiedenen Kandidaten ueber alle Runden, und der Zweig
`if ($approved === [])` bekommt den dritten Ast in der Reihenfolge Decke,
Schweigen, neuer Zustand, mit dem Satz als Kommentar. An der Rundenschleife
steht, was ausdruecklich NICHT passiert.

**Task 2, die Ergebnisseite.** Fuenfte Zustandszeile im Template, Bedingung im
Textabsatz von Block 4, Ueberschrift unveraendert. Der Blockkommentar hat den
Satz "Not one word about permissions" verloren, denn der neue Satz spricht ueber
Berechtigung; an seine Stelle ist die Begruendung getreten, warum er das darf
und was er trotzdem nicht nennt. `PageController::nextUrl` liest nicht mehr
`$outcome->failure !== null`, sondern `$runFellShort`, das den neuen Grund
ausnimmt. Der Provider hat nur den Kommentar bekommen, vier Gruende sind fuenf.

**Task 3, die Kataloge.** Der 174. Schluessel steht in allen vier deutschen
Dateien an derselben Stelle, direkt neben `Try another word, ...`. Die harte
Zahl im Gate steht auf 174, der Docstring nennt den Entscheid V-1a mit Datum
und die Begruendung, warum sie hier steigt und nicht in 11-08. Der Kommentar
in Zeile 101 spricht nicht mehr von 173.

## Tests

**PHP, nur in CI (kein PHP auf der Entwicklungsmaschine).** Lauf
[34530207832](https://github.com/street1983nk/nextcloud-search/actions/runs/34530207832),
Job "PHPUnit over the companion app": `OK (185 tests, 473 assertions)`, Boden
28. Vorher 177 (Lauf 34316508231), also genau die acht neuen Faelle:

| Datei | Neue Faelle |
|---|---|
| SearchServiceTest | 6, je einer je Punkt der Verhaltensliste, jeder mit der Frage im Kommentar |
| PageControllerTest | 1, die naechste Seite bleibt im neuen Zustand erhalten |
| ProviderTest | 1, der Dialog liefert eine leere Gruppe und traegt den Grund in die Spur |

Dazu die fuenfte Konstante in den beiden Aufzaehlungen, deren Docstrings jetzt
fuenf statt vier sagen.

Die sechs Faelle des Dienstes decken: kein Kandidat bleibt `failure === null`,
entschiedene Kandidaten ohne Treffer ergeben den neuen Zustand, die Decke
gewinnt, das Schweigen gewinnt, ein Lauf mit Treffer traegt ihn nie, und
`hasMore` und `nextCursor` sind dieselben Werte wie heute im gleichen Fall.

**Lokal, PHP-Syntax.** `php -l` ueber `lib`, `appinfo`, `templates` und `tests`
in einem `php:8.2-cli`-Container: 58 Dateien ohne Syntaxfehler. In CI derselbe
Lauf gruen ("php -l": success).

**Python.** `uv run python -m pytest -q`: **2002 passed, 15 skipped**, also
genau die Grundlinie. `ruff check .`, `ruff format --check .` und `pyright`
ohne Befund, `vulture src tests --min-confidence 80` ohne Befund.

## CI

| Workflow | Lauf | Ergebnis |
|---|---|---|
| PHP and store metadata gates (php -l, info.xml, PHPUnit) | 34530207832 | success |
| Python gates (ruff, format, pyright, vulture, pytest) | 34530207763 | success |
| Integration | 34530208024 | success |
| Multi-arch image | 34530207919 | success |
| Resilience | 34530207817 | success |
| HaRP deploy | 34530207632 | success |

Alle sechs Workflows des Push-Commits `cf83e4e` sind gruen, im ersten Anlauf,
ohne Wiederholung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Der Baumhash-Beweis der PHP-Haelfte hielt den Baum fest**

- **Found during:** Verifikation nach Task 3, volle Python-Suite
- **Issue:** `backend/tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half`
  rechnet den Baumhash ueber `php/**/*.php` des Arbeitsbaums aus und vergleicht
  ihn mit `PHP_TREE_HASH = 4a4c6f62...`. Diese Zahl ist ein Rohmesswert vom
  09.09.2026 aus der Vergleichsmessung. Plan 11-13 ist der erste Plan seit
  jener Messung, der die PHP-Haelfte anfasst, also war die Zusicherung mit dem
  ersten Task rot: `assert 'cf56a358...' == '4a4c6f62...'`. Der Plan verlangt
  eine gruene Suite, also war der Befund blockierend und nicht aufschiebbar.
- **Fix:** Additiv, ohne eine berichtete Zahl zu retirieren. `PHP_TREE_HASH`
  bleibt unangetastet und wird jetzt gegen die Datei geprueft, aus der sie
  gelesen wurde (`rohdaten/40b-baumhash.txt`), damit Konstante und Bericht
  nicht unbemerkt auseinanderlaufen. Daneben steht `PHP_TREE_HASH_TODAY =
  cf56a358...` fuer den heutigen Baum, und das Rezept wird gegen den geprueft,
  denn ein Rezept, das gegen einen nicht mehr existierenden Baum geprueft wird,
  wird gegen nichts geprueft. Eine dritte Zusicherung faellt um, wenn die
  beiden Zahlen je wieder gleich werden, damit die zweite nicht als Leiche
  stehen bleibt. Die Dateizahl 58 ist unveraendert; acht von 58 Dateien haben
  ihre Bytes geaendert, keine ist gekommen oder gegangen.
- **Warum nicht ueberschreiben:** `4a4c6f62...` steht in
  `docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/40b-baumhash.txt`,
  in der Tabelle des Messberichts und in `10-05-SUMMARY.md`. Die Regel dieses
  Projekts, dort woertlich festgehalten, lautet: keine berichtete
  Vergleichszahl wird retiriert. Der Bericht wird durch den neuen Wert auch
  nicht unwahr, denn er nennt den Hash des Arbeitsbaums, aus dem er geschrieben
  wurde.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Commit:** cf83e4e

Keine weitere Abweichung. Kein Paket installiert (T-11-SC), keine
Architekturaenderung, kein Checkpoint noetig.

## Threat Flags

Keine. Der Plan fuehrt keine Netzwerkschnittstelle, keinen Auth-Pfad, keinen
Dateizugriff und keine Schemaaenderung ein. Die vier Dispositionen des
Registers sind bedient: T-11-50 (der Satz nennt keine Zahl, keinen Namen,
keinen Pfad), T-11-51 (die Zaehlvariable liest nur, am Diff belegt), T-11-52
(jede Ausgabe durch `p($l->t(...))`, Escaping-Gate und Leerzustands-Gate
gruen), T-11-53 (dieser Plan ist gefahren, nicht uebersprungen; der Entscheid
steht oben mit Datum).

## Uebergaben

- **11-05** zaehlt die franzoesische Abdeckung aus `php/l10n/de.json`. Die
  Datei traegt jetzt 174 Schluessel, und der 174. ist
  `Other files contain this word, but none that you may open.` Er muss in
  `fr.json` und `fr.js` mit. `docs/l10n-french.md` nennt an drei Stellen noch
  173 (Zeilen 54, 58, 70); das gehoert zu 11-05 und ist hier bewusst nicht
  angefasst worden, weil die Datei nicht in `files_modified` dieses Plans
  steht und kein Gate sie liest.
- **11-08** prueft den Katalog gegen 174. Die Zahl steht bereits so im Gate.
  Das Platzhalter-Gate G3 bekommt nichts Neues zu pruefen: der Satz traegt
  keine Prozent-Direktive.
- **11-10** kann DI-07-03 als MEDIUM-gefixt ins Audit tragen und die
  Unveraendertheit der Berechtigungskette unter ASVS V4 am Diff nachpruefen.
  Zusaetzlich zu bedenken: die Tabelle in
  `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` nennt die
  PHP-Haelfte des Arbeitsbaums mit `4a4c6f62...`; das war am Berichtstag
  richtig und ist seit diesem Plan nicht mehr der heutige Baum. Der Grund
  steht in `test_measurement_scripts.py` an der Konstante.

## Self-Check: PASSED
