---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 09
subsystem: php-companion
tags: [template, filterleiste, chips, sortierlinks, leerzustand, datumszeile, versteckte-felder, barrierefreiheit, filt-01, filt-02, filt-03, filt-04]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 08
    provides: "typeChips, rangeChips, sortLinks, resetUrl, sortMode, filtersActive, showModified und je Trefferzeile modified"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 04
    provides: "SearchFilters als Quelle der Wire-Namen, die das Template beschriftet"
provides:
  - "Block 2b in php/templates/search.php: sechs Typ-Chips, vier Zeitraum-Chips, drei Sortierlinks, ein Zuruecksetzen-Link, alles Links"
  - "drei role=group-Gruppen mit sichtbarer Beschriftung als zugaenglichem Namen"
  - "aktiver Chip als EIN Fokusstopp mit close-Symbol, aria-current und Remove filter %s als zugaenglichem Namen"
  - "die 23 englischen Quell-Strings des Copywriting Contract als $l->t() im Template"
  - "fuenf versteckte Filterfelder im Suchformular, ohne page, cursors oder fp"
  - "Datumszeile findling-hit__modified und die datierte Fassung des zugaenglichen Namens"
  - "vierte Variante des Leerzustands als Zweig INNERHALB von $showEmpty"
  - "PageController::formFilters(): die Filterliste einer Adresse in der Form, die das Formular braucht"
  - "closeIcon als siebtes Symbol der Seite, THIRD-PARTY.md zieht die Zaehlung nach"
affects: [13-10, 13-11, 13-12]

tech-stack:
  added: []
  patterns:
    - "Die Beschriftungen stehen als Abbildung von Wire-Wert auf $l->t() im Template, weil die Katalogextraktion literale Zeichenketten an der Aufrufstelle braucht: ein $l->t() ueber eine Variable ist ein Schluessel, den kein Extraktor je sieht"
    - "Der aktive Chip traegt den Entfernen-Sinn selbst statt einen Knopf zu verschachteln: ein Fokusstopp je Chip, kein Link im Link, kein ungueltiges HTML"
    - "Zustand nie allein ueber Farbe: Flaeche, close-Symbol und Ansage sind drei Traeger fuer eine Tatsache"
    - "Eine Bedingung fuer die sichtbare Zeile und fuer den gesprochenen Namen, weil ein aria-label den Inhalt ERSETZT und nicht ergaenzt"
    - "Die fuenf Feldnamen des Formulars stehen als Literale und nicht in einer Schleife, damit ein Leser und ein Gate sehen, welche fuenf Namen dieses Formular senden kann"

key-files:
  created: []
  modified:
    - php/templates/search.php
    - php/lib/Controller/PageController.php
    - php/tests/Unit/PageControllerTest.php
    - THIRD-PARTY.md
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die vierte Leerzustands-Variante ersetzt Ueberschrift UND Satz, nicht nur den Satz: die bestehende Ueberschrift sagt 'keine Datei enthaelt X', und das ist unter einem Filter schlicht unwahr, denn gesucht wurde eine Teilmenge"
  - "Der Kommentar zur Chip-Auszeichnung nennt die verbotene Auszeichnung nicht beim Namen, weil der Pruefblock des Plans und das Gate aus 13-10 die Datei auf genau diese Zeichenkette absuchen; ein erklaerender Kommentar haette das eigene Gate rot gemacht"
  - "Das Template liest sortMode nicht: jeder Sortierlink traegt sein eigenes active, und eine zweite, ungenutzte Variable im Dateikopf waere genau die tote Zusicherung, die diese Datei sonst vermeidet"
  - "Die Beschriftungen der Chips kommen aus drei Abbildungen im Template und nicht aus dem Controller, weil sonst die Kataloge leer blieben"

patterns-established:
  - "Eine Vorlage, die nichts rechnet, braucht auch die Formularfelder fertig: was sie sonst selbst zusammensetzt, ist die zweite Stelle, an der der Adresszustand ausgelegt wird"

requirements-completed: []  # FILT-01 bis FILT-04 tragen noch 13-10, 13-11 und 13-12

duration: 15min
completed: 2026-09-17
---

# Phase 13 Plan 09: Filterleiste, Datumszeile und der vierte Leerzustand Summary

**Die Ergebnisseite hat ihren sechsten Block: vierzehn Bedienelemente, die allesamt gewoehnliche Links auf fertig berechnete Adressen sind, dazu die Datumszeile im Treffer, die auch ein blinder Nutzer hoert, und einen Leerzustand unter Filter, der den einen Hebel nennt, den der Nutzer in der Hand haelt.**

## Performance

- **Duration:** 15 min
- **Tasks:** 3
- **Commits:** 4

## Was gebaut wurde

### Task 1: Block 2b, die Filterleiste (`42080a4`)

Zwischen Bannerzeile und Trefferliste steht jetzt `<div class="findling-filters">`
mit drei beschrifteten Zeilen: Dateityp, Zeitraum, Sortieren nach. Jede
Beschriftung ist ein `span` mit eigener `id`, jede Gruppe ein `div` mit
`role="group"` und `aria-labelledby` auf genau diese `id`. Keine Ueberschrift,
keine Liste, kein `nav`, kein Formular, kein Skript.

Der Block wird nur bei vorhandenem Suchbegriff gerendert. Der Kommentar nennt den
Grund und die Ausnahme in einem Zug: ohne Begriff gibt es keine Menge, die man
eingrenzen koennte, also waeren zehn Chips ueber einer Einladung zehn Schalter
ohne Wirkung; mit Begriff steht die Leiste dagegen auch bei null Treffern und
auch unter einem Banner, weil genau dort der Weg zurueck gebraucht wird.

Ein Chip ist ein `<a>` mit `href` aus dem Baustein. Der aktive traegt zusaetzlich
die Modifikatorklasse, `aria-current="true"`, das `close`-Symbol (16 mal 16,
`currentColor`, `aria-hidden`, `focusable="false"`) und als zugaenglichen Namen
`Remove filter %s` mit seinem sichtbaren Text im Platzhalter. Der ganze Chip ist
der Entfernen-Link: kein verschachtelter Knopf, kein zweiter Fokusstopp, kein
ungueltiges HTML. Weil der Name den sichtbaren Text enthaelt, trifft ein
Spracheingabe-Nutzer, der "PDF" sagt, den Chip (WCAG 2.5.3).

Die Beschriftungen kommen aus drei Abbildungen von Wire-Wert auf `$l->t()`, die
im Template stehen. Der Kommentar sagt warum: die Katalogextraktion liest
literale Zeichenketten an der Aufrufstelle, ein `$l->t()` ueber eine Variable ist
ein Schluessel, den kein Extraktor je sieht, und der Satz ginge dann in jeder
Sprache auf Englisch raus. Damit kennt die Oberflaeche sechs Gruppennamen, vier
Zeitraumnamen und drei Ordnungsnamen, und keine einzige Dateiendung.

Der Zuruecksetzen-Link steht als letztes Element der Zeitraum-Zeile, ausserhalb
der Gruppe, und nur bei gesetztem `resetUrl`.

`$closeIcon` ist das siebte Symbol der Datei. `THIRD-PARTY.md` zieht die
Zaehlung nach, an beiden Stellen, an denen sie steht: in der Spalte "Where it
lands" ("carries seven") und im Absatz ueber die zwei Schreibweisen der Pfaddaten
("seven PHP variables"). Keine neue Tabellenzeile, kein neuer Name in der
Pruefschleife, weil `close` seit Phase 4 gepinnt und gelistet ist.

### Task 2: Versteckte Formularfelder und die Datumszeile (`570112e`)

Das Suchformular traegt die aktiven Filter jetzt als fuenf versteckte Felder
(`types`, `sort`, `range`, `since`, `until`). Ein leerer Wert wird gar nicht
gerendert, nicht als leeres Feld mitgeschickt. `page`, `cursors` und `fp` kommen
weiterhin nicht ins Formular, und der Kommentar nennt beide Wirkungen: wer den
Begriff praezisiert, verliert seine Eingrenzung nicht und landet wie bisher auf
Seite 1, weil die erste Seite des neuen Ergebnisses die einzige ist, die es
ueberhaupt schon gibt.

Die Trefferzeile hat eine vierte Textzeile `findling-hit__modified` mit
`Modified on %s` und dem fertig formatierten Datum. Sie steht unter dem Pfad und
ueber dem Auszug; ein Kommentar sagt, warum sie nicht an den Pfad angehaengt
wird: der Pfad ist einzeilig mit Ellipse, ein Anhaengsel waere das Erste, was
abgeschnitten wird. Sie existiert nur, wenn `showModified` gilt und `modified`
nicht leer ist.

Der zugaengliche Name der Zeile hat eine zweite, datierte Fassung
`%1$s in %2$s, modified on %3$s`, die genau unter derselben Bedingung verwendet
wird. Eine Variable `$dated` traegt die Entscheidung fuer beide Stellen, damit
sichtbare Zeile und gesprochener Name nicht auseinanderlaufen koennen. Der Grund
steht als Kommentar: ein `aria-label` ERSETZT den Inhalt fuer den Screenreader,
ohne die zweite Fassung waere das Datum ausgerechnet unter der Datums-Sortierung
unhoerbar.

### Task 3: Die vierte Variante des Leerzustands (`0ff146a`)

Ein zusaetzlicher Zweig INNERHALB des bestehenden `$showEmpty`-Blocks, im
`$hasQuery`-Zweig, vor der `$allRejected`-Abfrage, mit `filtersActive` als
Bedingung. Inhalt: dasselbe `file-search-outline`-Symbol, Ueberschrift
`No results with the active filters`, Satz
`Remove a filter or widen the time range.` und darunter der Link
`Reset filters` auf `resetUrl`.

Die `$showEmpty`-Zeile ist woertlich unveraendert und liest weiterhin `$hasError`,
`$hasHint` und `$hasQuery`; die Form `} elseif ($showEmpty) {` steht ebenfalls
unveraendert. Beides wird von
`test_the_empty_state_of_the_page_does_not_speak_over_a_banner` als Text
gelesen, und beides ist gruen.

Die Rangfolge steht als Kommentar und ist so gebaut: die Filter-Variante
verdraengt die `$allRejected`-Variante, solange ein Filter wirkt. Beide Saetze
sind in diesem Zustand wahr, aber nur einer nennt einen Hebel, den der Nutzer in
der Hand haelt. Ohne aktiven Filter ist die `$allRejected`-Variante unveraendert
die aus V-1a.

### Nachzug: Baumhash (`8c605d0`)

`PHP_TREE_HASH_TODAY` auf `abe36dc6...` gesetzt, im Kommentarstil der
Vorgaengerplaene: drei Dateien haben ihre Bytes geaendert, die 64 bleibt stehen,
und dieser Plan lief allein in seiner Welle, braucht also keine zweite Korrektur
nach dem Merge.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Das Template kann `since` und `until` nicht kennen**

- **Found during:** Task 2
- **Issue:** Task 2 verlangt fuenf versteckte Felder, darunter `since` und
  `until`. Plan 13-08 uebergibt aber weder die rohen Adresswerte noch eine
  Feldliste: die achtzehn Template-Parameter enthalten `typeChips`,
  `rangeChips`, `sortLinks`, `resetUrl`, `sortMode`, `filtersActive` und
  `showModified`, und keiner davon traegt eine Zeitgrenze. `types` und `range`
  liessen sich noch aus den aktiven Chips zusammensuchen, aber genau das waere
  die zweite Stelle, an der der Adresszustand ausgelegt wird, und die Zusage
  dieser Phase lautet, dass das Template nicht rechnet.
- **Fix:** `PageController::formFilters()` hinzugefuegt. Sie nimmt
  `filterArguments()`, also genau die Liste, aus der jede Adresse dieser Seite
  gebaut wird, und entfernt `query` und `names`, weil das Formular beide bereits
  sichtbar vor dem Nutzer traegt. Damit erbt sie drei Eigenschaften, die sonst
  einzeln haetten zugesichert werden muessen: keine Position, kein Wert, den
  niemand gesetzt hat, und kein Standard-Sortiermodus. Neuer
  Template-Parameter `formFilters`, im Template in fuenf Einzelwerte gelesen,
  damit die Feldnamen als Literale dastehen.
- **Files modified:** `php/lib/Controller/PageController.php`,
  `php/templates/search.php`, `php/tests/Unit/PageControllerTest.php`
- **Commit:** `570112e`

**2. [Rule 3 - Blockierend] Baumhash der PHP-Haelfte nachgezogen**

- **Found during:** nach Task 3
- **Issue:** `test_the_recipe_reproduces_the_tree_hash_of_the_php_half` haelt den
  Hash aller `php/**/*.php` gegen eine festgeschriebene Zahl. Drei geaenderte
  Dateien machen das Gate rot, obwohl nichts kaputt ist.
- **Fix:** `PHP_TREE_HASH_TODAY` auf den neuen Wert gesetzt, mit dem ueblichen
  Absatz, welche Dateien ihre Bytes geaendert haben und warum die 64 stehen
  bleibt.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `8c605d0`

### Wahlentscheidungen innerhalb des Plans

- **Der erklaerende Kommentar nennt die verbotene Auszeichnung nicht beim
  Namen.** Der Plan verlangt einen Kommentar, der sagt, warum der Chip
  `aria-current` traegt und nicht die Gedrueckt-Auszeichnung eines Knopfes. Sein
  eigener Pruefblock verlangt im selben Atemzug, dass diese Zeichenkette in der
  Datei nirgends vorkommt, und 13-10 macht daraus ein Gate. Der Kommentar steht
  also da, mit derselben Begruendung, und umschreibt das verbotene Wort: die
  Auszeichnung gehoert zu einer Knopfrolle, ein `<a>` mit `href` ist ein Link,
  und ein gedrueckter Link ist nichts.
- **Die vierte Leerzustands-Variante ersetzt Ueberschrift und Satz.** Der Plan
  nennt beide Texte, und die bestehende Ueberschrift "keine Datei enthaelt X"
  waere unter einem Filter unwahr: gesucht wurde eine Teilmenge, und ueber den
  Rest sagt dieser Lauf nichts. Der alte Kommentarabsatz, der sagte, die
  Ueberschrift bewege sich nicht, gilt jetzt ausdruecklich nur noch fuer den
  Fall ohne Filter.
- **`sortMode` wird nicht gelesen.** Der Plan listet den Parameter bei den
  defensiven Lesungen auf, aber es gibt keine Stelle, an der das Template ihn
  braucht: jeder Sortierlink traegt sein eigenes `active`, die Datumszeile haengt
  an `showModified`, und der Wert fuer das versteckte Feld kommt aus
  `formFilters`, wo der Standardmodus bereits richtig fehlt. Eine ungenutzte
  Variable im Dateikopf waere genau die tote Zusicherung, die diese Datei sonst
  vermeidet.
- **Das Chip-Markup steht zweimal ausgeschrieben,** einmal je Zeile, statt
  einmal ueber eine gemeinsame Datenstruktur. Die Alternative waere eine
  Schleife ueber zwei Zeilen mit einer Sonderabfrage fuer den
  Zuruecksetzen-Link gewesen, also weniger Zeilen und eine Verzweigung mehr an
  der Stelle, an der ein Leser sehen will, was die Zeile rendert. Dieselbe Wahl
  trifft die Datei schon bei den beiden Bannerarten.
- **`$dated` statt zweier getrennter Bedingungen.** Sichtbare Zeile und
  gesprochener Name muessen dieselbe Antwort haben, sonst gibt es genau einen
  Zustand, in dem der Screenreader ein Datum vorliest, das nicht auf dem
  Bildschirm steht.

## Verification

| Gate | Ergebnis |
|---|---|
| Backend-Suite vollstaendig | gruen, 2120 passed, 15 skipped |
| `tests/test_admin_ui_contract.py` | gruen (39) |
| `tests/test_php_trust_boundary.py` | gruen (21) |
| `tests/test_php_acl_boundary.py` | gruen (8) |
| `test_the_empty_state_of_the_page_does_not_speak_over_a_banner` | gruen |
| Katalog-Gates (Schluesselzahl 174, franzoesische Vollstaendigkeit) | gruen, weil sie die Kataloge lesen und nicht die Vorlage; die 23 neuen Schluessel kommen mit 13-11 dazu |
| `ruff check` und `ruff format --check` der geaenderten Python-Datei | gruen |
| Pruefblock Task 1 (elf Zusicherungen inklusive der vier Verbote) | gruen |
| Pruefblock Task 2 (vier greps plus die Python-Probe auf den Formularrumpf) | gruen |
| Pruefblock Task 3 (fuenf greps inklusive der woertlichen `$showEmpty`-Zeile) | gruen |
| Alle 23 Quell-Strings als `$l->t('...')` in der Vorlage | gruen, einzeln geprueft |
| Vokabular-Gate, Gedankenstriche, Emojis | gruen |

### Ersatznachweis statt `php -l` und PHPUnit

Auf dieser Maschine gibt es kein PHP und die Docker-Engine laeuft nicht, also
konnten weder `php -l` noch PHPUnit laufen. Beide laufen in CI. Als Ersatz wurde
geprueft:

- Klammer-, Anfuehrungszeichen- und Apostrophbilanz aller drei PHP-Dateien nach
  jeder Aufgabe: geschweift, rund und eckig je 0, beide Anfuehrungszeichenarten
  gerade, alle drei Dateien reines ASCII.
- Zusaetzlich fuer die Vorlage, weil sie viele ineinanderliegende PHP-Bloecke
  hat: ein Lauf ueber die Datei, der Textbereiche, Zeichenketten und beide
  Kommentararten ueberspringt und nur in den Codebereichen die Klammertiefe
  zaehlt. Endtiefe 0, und der Lauf endet ausserhalb eines PHP-Blocks, also ist
  auch die Abfolge `<?php` gegen `?>` sauber verschachtelt (170 zu 170). Die
  Datei verwendet durchgehend die geschweifte Schreibweise, es gibt kein
  `endif` und kein `endforeach`, bei dem eines fehlen koennte.
- Jede grep-Zusicherung der drei `<verify>`-Bloecke einzeln nachgefahren,
  einschliesslich der Python-Probe auf den Rumpf des Formulars.
- Der Diff aller Dateien Zeile fuer Zeile gegengelesen, getrennt nach Code- und
  Kommentarzeilen.
- Die drei Python-Gates, die den PHP-Quelltext lesen (Route-Grenze,
  Rechtegrenze, Baumhash), laufen lokal und sind gruen.

## Known Stubs

Die Leiste hat noch keine Optik: `php/css/search.css` kennt weder
`findling-filters`, noch `findling-chip-link`, `findling-sort` oder
`findling-hit__modified`. Das ist der Zuschnitt der Phase, 13-10 liefert die
Regeln nach. Bis dahin ist die Leiste vollstaendig bedienbar und
tastaturzugaenglich, aber unformatiert.

Die 23 Quell-Strings stehen nur auf Englisch. Die Kataloge kommen mit 13-11; bis
dahin liest ein deutscher oder franzoesischer Nutzer die Leiste auf Englisch.
Die Zahlen-Gates der Kataloge bleiben deshalb gruen und nicht rot: sie zaehlen
`de.json` und nicht die Aufrufe in der Vorlage.

## Threat Flags

Keine. Es kommt keine Route hinzu, kein Schreibpfad, kein JSON-Kanal und keine
neue Vertrauensgrenze. Die Rechtefrage steht unveraendert an genau einer Stelle.

| Threat ID | Umsetzung |
|---|---|
| T-13-42 | alle zehn Chips immer gerendert, ohne Zahl, ohne Punkt, ohne Ausgrauen; der Grund steht im Blockkommentar. Der Filter-Leerzustand nennt keine Zahl und kein Wort ueber Berechtigungen |
| T-13-43 | jede Ausgabe durch `p()`, jede Beschriftung durch `$l->t()`; die Werte in den Adressen baut der URL-Generator, das Template setzt keine Adresse zusammen |
| T-13-44 | weiterhin genau ein `<form>`, kein `<select>`, kein `<option>`, kein Inline-Skript, kein `style`-Attribut, keine Zeile in `php/js/search.js` |
| T-13-45 | die neue Variante ist ein Zweig innerhalb von `$showEmpty`; die Entscheidung ist woertlich unveraendert und wird vom bestehenden Gate gelesen |
| T-13-46 | keine neue Route, keine JSON-Antwort; `test_php_trust_boundary.py` lief in jedem Pruefblock mit |
| T-13-SC | kein Paket installiert, kein neues Symbol |

## Fuer den naechsten Plan

13-10 findet die vollstaendige Auszeichnung vor und braucht Regeln fuer
`findling-filters`, `findling-filters__row`, `findling-filters__label`,
`findling-filters__group`, `findling-filters__reset`, `findling-chip-link` samt
`--active`, `findling-sort`, `findling-sort__link` samt `--active`,
`findling-hit__modified` und `findling-empty__reset`. Die Klassennamen sind
genau die des Vertrags; kein Element traegt ein zweites, unbenutztes.

13-11 findet 23 englische Quell-Strings vor, woertlich wie im Copywriting
Contract, und muss nur noch die Kataloge und ihre Zahlen nachziehen.

## Self-Check: PASSED

- `php/templates/search.php` FOUND
- `php/lib/Controller/PageController.php` FOUND
- `php/tests/Unit/PageControllerTest.php` FOUND
- `THIRD-PARTY.md` FOUND
- `backend/tests/test_measurement_scripts.py` FOUND
- Commit `42080a4` FOUND
- Commit `570112e` FOUND
- Commit `0ff146a` FOUND
- Commit `8c605d0` FOUND
