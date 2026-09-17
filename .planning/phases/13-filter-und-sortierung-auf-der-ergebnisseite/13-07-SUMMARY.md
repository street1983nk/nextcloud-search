---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 07
subsystem: php-companion
tags: [pagecontroller, url-vertrag, stiller-rueckfall, zeitzone, kalenderfenster, filt-01, filt-03, filt-04]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 04
    provides: "SearchFilters mit TYPES, SORTS, SORT_DEFAULT und EPOCH_MAX"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 05
    provides: "SearchService::run(..., SearchFilters) als Signatur der Seite"
provides:
  - "PageController::QUICK_RANGES: die vier Kalenderfenster in der Reihenfolge der Oberflaeche"
  - "typeGroups(), sortMode(), quickRange(), epochParam(): fuenf Adresswerte mit stillem Rueckfall"
  - "quickRangeStart(): die vier Untergrenzen in der Zeitzone des angemeldeten Nutzers"
  - "filters(): das SearchFilters-Objekt der Seite, mit der engeren der beiden Untergrenzen"
  - "IDateTimeZone und IDateTimeFormatter als Konstruktorabhaengigkeiten (der Formatierer fuer 13-08)"
  - "14 neue Testfaelle ueber Rueckfall, Kanonisierung, Kalendergrenzen und engere Grenze"
affects: [13-08, 13-09, 13-11]

tech-stack:
  added: []
  patterns:
    - "Eine geschlossene Werteliste wird gelesen, nicht wiederholt: die Kanonisierung laeuft als Schleife ueber die Liste des Wertobjekts und erledigt Unbekanntes, Leeres, Doppeltes, Reihenfolge und Obergrenze in einem Durchgang"
    - "Ein Kalenderbegriff wird nie ohne Zeitzone gerechnet: DateTimeImmutable bekommt die Zone des Nutzers, und die Grenze entsteht aus setTime(0, 0) statt aus strtotime"
    - "Eine Gegenprobe formatiert den gelieferten Epochenwert in die Testzone zurueck, statt ihn als Zahl mit dem Muster der Umsetzung zu vergleichen"

key-files:
  created: []
  modified:
    - php/lib/Controller/PageController.php
    - php/tests/Unit/PageControllerTest.php
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Nur QUICK_RANGES steht als Konstante in dieser Datei; Typ- und Sortiernamen kommen aus SearchFilters, weil zwei Listen desselben Vokabulars in der Richtung auseinanderlaufen, die niemand bemerkt"
  - "Die Kanonisierung ist eine Schleife ueber SearchFilters::TYPES und kein Sortier- plus Dublettenschritt: damit ist die Sechs die Obergrenze, gleich was in der Adresse steht"
  - "Die Zeitrechnung nutzt sub(new DateInterval(...)) statt modify(): dieselben Kalendertage, aber ohne den Rueckgabewert false, den modify() in PHP 8.2 noch kennt"
  - "IDateTimeFormatter kommt eine Runde zu frueh in den Konstruktor, damit die Testdatei ihre Doubles nur einmal statt zweimal fuer ein Feature nachzieht"
  - "Die zwei Faelle zur engeren Grenze meiden das naheliegende Paar aus dieses Jahr und gestern: am 1. Januar ist gestern frueher als der 1. Januar, und der Fall waere an einem Tag im Jahr rot"

patterns-established:
  - "Ein Adresswert, der nur in die Suche reist und noch nicht ins Template, wird ueber das abgefangene Wertobjekt geprueft und nicht ueber die Template-Parameter"

requirements-completed: []  # FILT-01, FILT-03 und FILT-04 tragen noch 13-08, 13-09 und 13-11

duration: 35min
completed: 2026-09-17
---

# Phase 13 Plan 07: Fünf Adresswerte, Kalenderfenster und das Filterobjekt der Seite Summary

**Die Adresse der Ergebnisseite liest `types`, `sort`, `range`, `since` und `until` als geschlossene Werte mit stillem Rückfall, rechnet die vier Schnellbereiche als Kalenderfenster in der Zeitzone des angemeldeten Nutzers und übergibt der Suche daraus ein `SearchFilters`, in dem `range` und `since` den Zeitraum nur enger machen können.**

## Performance

- **Duration:** 35 min
- **Tasks:** 3
- **Commits:** 4

## Was gebaut wurde

### Task 1: die fünf Leser (`d8a32e4`)

`QUICK_RANGES` steht als einzige neue Konstante am Klassenkopf. Die sechs
Typnamen und die drei Sortiernamen stehen bewusst nicht daneben: sie werden aus
`SearchFilters::TYPES` und `SearchFilters::SORTS` gelesen, und der Docstring der
Konstante nennt den Grund beim Wort.

Vier private Leser, alle nach dem Muster von `pageNumber()`:

| Methode | Rückfall |
|---|---|
| `typeGroups()` | leere Liste |
| `sortMode()` | `SearchFilters::SORT_DEFAULT` |
| `quickRange()` | kein Wert |
| `epochParam()` | kein Wert |

`typeGroups()` ist die einzige mit etwas mehr Arbeit: sie trennt an Kommata,
schreibt klein, trimmt und läuft dann über die geschlossene Liste. Diese eine
Schleife erledigt vier Dinge zugleich, und deshalb gibt es keinen Sortierschritt,
keinen Dublettenschritt und keinen Zählschritt: Unbekanntes fällt weg, Leeres
fällt weg, ein doppelt geschriebener Name bleibt einmal übrig, und mehr Einträge
als die Liste hat kann sie gar nicht liefern. Die Sechs ist damit eine
Eigenschaft der Bauweise und keine zusätzliche Prüfung.

Die Docstrings von Klasse und `index()` nennen jetzt neun Adresswerte statt
vier, in derselben Aufzählung wie zuvor und mit derselben Hausregel: kein neuer
Fehlerzustand, keine Meldung, keine Aussage über die Adresszeile.

### Task 2: Kalendergrenzen und `filters()` (`4c13d04`)

Der Konstruktor nimmt `IDateTimeZone` und `IDateTimeFormatter`. Nur die erste
der beiden wird in diesem Plan benutzt; die zweite kommt eine Runde zu früh,
damit die Testdatei ihre Doubles nicht zweimal für dasselbe Feature nachzieht.

`quickRangeStart()` baut die Zeit ausschließlich über
`$this->dateTimeZone->getTimeZone()`. Die Datei enthält kein `strtotime` und
keine zonenlose Zeit. Die vier Untergrenzen sind heute 00:00, vor 6 Tagen 00:00,
vor 29 Tagen 00:00 und der 1. Januar 00:00; keine davon setzt eine Obergrenze.

`filters()` schreibt das Wertobjekt vollständig aus, wie `caps()` es vormacht.
Wirksames `since` ist das Maximum aus Schnellbereichsgrenze und rohem Wert,
wirksames `until` der rohe Wert. `outcome()` übergibt dieses Objekt an
`SearchService::run` statt `SearchFilters::none()`.

### Task 3: die Testfälle (`7c47451`)

`setUp()` stellt beide neuen Doubles, und die Testzone ist `Europe/Berlin`. Ein
Kommentar sagt, warum sie nicht UTC ist: auf einem Runner in UTC würde ein
Controller, der die Zeitzone des Nutzers komplett vergessen hat, jeden
Mitternachtsfall bestehen.

Vierzehn neue Fälle, gegen das abgefangene `SearchFilters` und nicht gegen die
Template-Parameter, weil die Anzeige dieser Werte erst 13-08 baut:

- die drei glücklichen Pfade (Typen, beide Sortiermodi, beide Zeitwerte)
- die vier Kalenderfenster in einer Schleife, jedes mit seiner Mitternacht und
  ohne Obergrenze
- Großschreibung und Leerzeichen, Unbekanntes und Doppeltes,
  Kanonisierungsreihenfolge, doppelt so lange Liste wie die geschlossene
- unbekannter `sort` in fünf Schreibweisen, unbekannter `range` in vier,
  fünf ungültige Zeitwerte gegen beide Grenzen
- zweimal die engere Grenze
- ein Fall, der alle falschen Werte in eine Adresse packt und belegt, dass
  daraus weder ein Fehlerzustand noch eine Logzeile entsteht

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Baumhash der PHP-Hälfte nachgezogen**

- **Found during:** nach Task 3
- **Issue:** `test_the_recipe_reproduces_the_tree_hash_of_the_php_half` vergleicht
  den Hash aller `php/**/*.php` gegen eine festgeschriebene Zahl. Zwei geänderte
  Dateien machen das Gate rot, obwohl nichts kaputt ist.
- **Fix:** `PHP_TREE_HASH_TODAY` auf den neuen Wert gesetzt, mit dem Kommentar in
  derselben Form wie bei 13-04 und 13-05: welche Dateien ihre Bytes geändert
  haben und warum die Zahl 64 stehen bleibt. `PHP_FILES_TODAY` und die beiden
  Messwerte des Laufs bleiben unangetastet.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `5bdee0c`

Sonst keine. Die drei Aufgaben liefen genau so, wie der Plan sie beschreibt.

### Zwei kleine Wahlentscheidungen innerhalb des Plans

- Die Tagesarithmetik nutzt `sub(new \DateInterval('P6D'))` statt `modify()`.
  Dieselben Kalendertage, dieselbe Sommerzeitbehandlung, aber ohne den
  `false`-Rückgabewert, den `modify()` in PHP 8.2 noch kennt und den niemand
  prüfen würde.
- Die zwei Fälle zur engeren Grenze nehmen nicht das im Plan genannte Paar aus
  "dieses Jahr" und "gestern". Am 1. Januar ist gestern früher als der 1. Januar,
  der Fall wäre an einem Tag im Jahr rot. Genommen wurden stattdessen "dieses
  Jahr" mit einem Zeitpunkt aus dem laufenden Jahr und "heute" mit einem
  Zeitpunkt von vor einem Jahr; beide Aussagen gelten an jedem Tag.

## Verification

| Gate | Ergebnis |
|---|---|
| `tests/test_php_trust_boundary.py` | grün (21) |
| `tests/test_php_acl_boundary.py` | grün (8) |
| `tests/test_measurement_scripts.py` | grün (228) |
| `tests/test_admin_ui_contract.py` | grün |
| Backend-Suite vollständig | grün, 2120 passed, 15 skipped |
| `ruff check` und `ruff format --check` der geänderten Python-Datei | grün |
| grep-Prüfungen aller drei Aufgaben | grün, kein `strtotime`, keine Dateiendung als Zeichenkette |

### Ersatznachweis statt `php -l` und PHPUnit

Auf dieser Maschine gibt es kein PHP, und die Docker-Engine läuft nicht, also
konnten weder `php -l` noch PHPUnit laufen. Beide laufen in CI. Als Ersatz
wurde geprüft:

- Klammer-, Anführungszeichen- und Apostrophbilanz beider geänderter PHP-Dateien
  gegen ihren Stand vor der Änderung: unverändert ausgeglichen.
- Jede grep-Zusicherung der drei `<verify>`-Blöcke des Plans einzeln nachgefahren.
- Die drei Python-Gates, die den PHP-Quelltext lesen (Route-Grenze, Rechtegrenze,
  Baumhash), laufen lokal und sind grün.

## Known Stubs

`IDateTimeFormatter` ist als Konstruktorabhängigkeit vorhanden und wird in
diesem Plan nicht benutzt. Das ist Absicht und im Docstring des Konstruktors
begründet: Plan 13-08 formatiert damit die Zeile "Geändert am ...". Ebenso
bewusst reicht dieser Plan den berechneten Zustand (aktive Gruppen, Sortiermodus,
aktiver Schnellbereich, wirksame Grenzen) noch nicht ins Template; auch das ist
13-08 und steht als Satz im Docstring von `filters()`.

## Threat Flags

Keine. Es kommt keine Route, kein Schreibpfad und keine neue Vertrauensgrenze
hinzu. Die fünf neuen Werte reisen ausschließlich in das `SearchFilters`-Objekt
und von dort in den Vorfilter des Containers, also vor die Rechtegrenze, die
unverändert an genau einer Stelle steht.

| Threat ID | Umsetzung |
|---|---|
| T-13-32 | geschlossene Wertelisten mit stillem Rückfall, je Wert ein Negativfall |
| T-13-33 | Ausgabe höchstens sechs Gruppen, Zeitwerte gegen `0` bis `EPOCH_MAX` |
| T-13-34 | kein neuer Fehlerzustand, ein Fall belegt die stumme Antwort |
| T-13-35 | Filter nur im Wertobjekt, keine Filterung hinter dem Recheck |
| T-13-36 | keine neue Route, Klassen-Docstring nennt kein Route-Attribut |

## Für den nächsten Plan

13-08 findet vor: `filters()` mit dem fertigen Zustand, `quickRange()` als
aktiven Chip-Namen, `QUICK_RANGES` als Reihenfolge der Zeitraumzeile und den
`IDateTimeFormatter` bereits im Konstruktor. Was fehlt, ist der Weg dieser Werte
ins Template samt `filterUrl()`, Fingerabdruck und Chips.
