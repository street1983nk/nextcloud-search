---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 08
subsystem: php-companion
tags: [pagecontroller, filterurl, fingerabdruck, cursorbindung, chips, sortierlinks, zuruecksetzen, datumszeile, filt-02, filt-04]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 04
    provides: "SearchFilters mit TYPES, SORTS, SORT_DEFAULT, EPOCH_MAX und hasAny()"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 05
    provides: "ApprovedHit mit mtime aus dem bestaetigten Knoten"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 07
    provides: "typeGroups(), sortMode(), quickRange(), epochParam(), quickRangeStart(), filters(), IDateTimeZone und IDateTimeFormatter im Konstruktor"
provides:
  - "PageController::filterUrl(): Adressbau der Filterleiste, der Position und Fingerabdruck gar nicht kennt"
  - "PageController::fingerprint(): acht Hexzeichen ueber den kanonisierten Anfragezustand"
  - "PageController::fingerprintParam(): Formpruefung des Adresswerts fp vor dem Vergleich"
  - "Cursor-Bindung in index(): ein Pfad wird nur angesehen, wenn der Fingerabdruck passt"
  - "address(): die sieben Werte der Suche, einmal je Anfrage gelesen"
  - "filterArguments(): die geteilte Argumentliste beider Adressbauer"
  - "typeChips(), rangeChips(), sortLinks(), resetUrl(), showsModified()"
  - "Template-Parameter typeChips, rangeChips, sortLinks, resetUrl, sortMode, filtersActive, showModified"
  - "rows() liefert je Zeile den Schluessel modified, formatiert ueber IDateTimeFormatter"
  - "14 neue Testfaelle ueber Adressen, Fingerabdruck, Datumszeile und Zuruecksetzen"
affects: [13-09, 13-10, 13-11]

tech-stack:
  added: []
  patterns:
    - "Zwei Bauteile statt eines Schalters: eine Methode, die die Position gar nicht als Argument nimmt, kann sie auch beim naechsten Umbau nicht schreiben"
    - "Die geteilte Haelfte beider Adressbauer ist die Filterliste, nicht die Position: ein Filter kann damit nicht von einem Bauer getragen und vom anderen fallengelassen werden"
    - "Die Adresse wird einmal je Anfrage gelesen und als Wertform weitergereicht, damit Filterlauf, Fingerabdruck und Links dieselbe Suche beschreiben, auch ueber Mitternacht"
    - "Ein Umschalt-Chip baut die Zielliste durch einen Lauf ueber die geschlossene Liste, nicht durch Hinzufuegen oder Entfernen: das Ergebnis ist dadurch kanonisch, ohne einen Sortierschritt"
    - "Der Test liest den Fingerabdruck aus einem Link, den die Seite selbst gebaut hat, statt ihn ein zweites Mal nachzurechnen"

key-files:
  created: []
  modified:
    - php/lib/Controller/PageController.php
    - php/tests/Unit/PageControllerTest.php
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Ein fehlendes fp gilt als Abweichung und nicht als Ausnahme: ein Cursorpfad ohne Fingerabdruck ist ein Pfad ohne bekannte Herkunft, und genau so kommt der von Hand kopierte Pfad der Sichtprobe 6 an"
  - "Der Fingerabdruck laeuft ueber die ROHEN Adresswerte range und since, nicht ueber die wirksame Untergrenze: sonst wechselte er um Mitternacht und wuerfe jeden blaetternden Nutzer auf Seite 1"
  - "Trennzeichen der Kanonisierung ist der Unit Separator, weil PlainText::bounded jedes Steuerzeichen ausser dem Tabulator in ein Leerzeichen verwandelt, bevor ein Begriff diese Klasse erreicht"
  - "filterUrl() und pageUrl() teilen sich filterArguments(): getrennt bleibt nur die Position, geteilt wird die Filterliste, damit ein Weiter-Link nicht durch eine andere Auswahl blaettert"
  - "showsModified() fragt SearchFilters::SORT_DEFAULT ab, statt die beiden Datumsnamen ein zweites Mal hinzuschreiben"
  - "address() als gelesene Wertform statt sieben positionaler Argumente an fuenf Methoden, weil ein Aufruf mit sieben Stellen genau die Unlesbarkeit ist, die SearchFilters in seinem eigenen Docstring anprangert"

patterns-established:
  - "Eine Eigenschaft, die eine Methode nicht verletzen KANN, schlaegt eine Eigenschaft, die sie nicht verletzen SOLL: die Signatur ist die Durchsetzung"

requirements-completed: []  # FILT-02 und FILT-04 tragen noch 13-09 und 13-10, die Oberflaeche fehlt

duration: 21min
completed: 2026-09-17
---

# Phase 13 Plan 08: Adressen der Filterleiste, Fingerabdruck und Datumszeile Summary

**Die Bedienelemente der Filterleiste entstehen aus einem Adressbauer, der eine Seitenposition gar nicht als Argument nimmt, und der Cursorpfad ist über acht Hexzeichen an den kanonisierten Anfragezustand gebunden, sodass ein Chipklick auf Seite sieben nicht mehr auf Seite sieben einer anderen Ergebnismenge landen kann.**

## Performance

- **Duration:** 21 min
- **Tasks:** 3
- **Commits:** 4

## Was gebaut wurde

### Task 1: `filterUrl()`, Fingerabdruck und Cursor-Bindung (`2d9dfc2`)

Vier neue Methoden und eine umgebaute `index()`.

`address()` liest die sieben Werte, die sagen WAS gesucht wird, einmal je
Anfrage: Begriff, `names`, Typgruppen, Sortiermodus, Schnellbereich und die
beiden rohen Zeitgrenzen. Seitenzahl, Cursorpfad und Fingerabdruck stehen
bewusst nicht darin, denn sie sagen, WO im Ergebnis jemand steht. Die Trennung
der beiden Gruppen ist der ganze Mechanismus: die sieben gehen in jeden Link der
Filterleiste und in den Fingerabdruck, die drei anderen in keinen einzigen.

`filterUrl()` nimmt genau diese Wertform und sonst nichts. Sie kann die Position
nicht schreiben, weil sie sie nicht kennt. Das ist der Unterschied zwischen einer
Eigenschaft, die eine Methode nicht verletzen soll, und einer, die sie nicht
verletzen kann, und es ist der Grund für zwei Bauteile statt eines Schalters.

`fingerprint()` fügt die sieben Werte mit dem Unit Separator zusammen und liefert
`substr(hash('sha256', $state), 0, 8)`. Der Docstring sagt in zwei Sätzen, was
das ist und was nicht: eine Verwechslungssperre und kein Sicherheitsmerkmal, ohne
Geheimnis, ohne Signatur und ohne etwas zu fälschen, und eine Kollision kostet
höchstens eine Seite zu viel, weil der Cursor ausschließlich erlaubte Kandidaten
zählt. Die Kanonisierung steht vor dem Hashen, sonst fiele ein Nutzer beim
Umsortieren derselben Auswahl auf Seite eins.

Das Trennzeichen ist gewählt und nicht gefunden: `PlainText::bounded` verwandelt
jedes Steuerzeichen außer dem Tabulator in ein Leerzeichen, bevor ein Begriff
diese Klasse erreicht, also kann der Unit Separator in keinem der sieben Werte
vorkommen.

`fingerprintParam()` prüft erst die Form (acht Hexzeichen, klein geschrieben) und
liefert sonst nichts. `index()` sieht sich einen Cursorpfad nur an, wenn dieser
Wert dem selbst berechneten gleicht; jede Abweichung ist `[0]` und Seite 1, still.
Der bestehende Kommentar an dieser Stelle wurde fortgeschrieben und nicht
ersetzt: er nennt jetzt beide Wege, auf denen ein Pfad durchfallen kann, die Form
und die Herkunft.

`previousUrl()` und `nextUrl()` tragen den Fingerabdruck mit und sagen im
Docstring warum: sie sind die einzigen Links, die eine Position weitergeben
dürfen, weil Blättern die Suche behält und in ihr wandert, während ein Chip die
Suche wechselt.

### Task 2: Chips, Sortierlinks, Zurücksetzen und das Datum (`9bc0991`)

`typeChips()` liefert sechs Bausteine, immer alle sechs. Die Zieladresse entsteht
durch einen Lauf über die geschlossene Liste, in dem genau ein Name umgedreht
wird: dadurch ist die Zielliste kanonisch, weil sie so gebaut wurde, und nicht
weil danach sortiert wurde. Ein Kommentar nennt den Grund, warum kein Chip fehlt
und keiner ausgegraut wird: das wäre dieselbe Auskunft wie ein Zähler und damit
ein Zähl-Orakel vor der Rechteentscheidung.

`rangeChips()` liefert vier Bausteine, höchstens einer aktiv. Ein Klick auf einen
anderen ersetzt, ein Klick auf den aktiven entfernt, und keiner schreibt je eine
Obergrenze.

`sortLinks()` liefert drei Bausteine, immer genau einer aktiv, mit dem Satz zum
Segmentschalter im Docstring.

`resetUrl()` gibt es nur bei `hasAny()`, und der Sortiermodus überlebt ihn:
Zurücksetzen nimmt weg, was Treffer versteckt, und eine Reihenfolge versteckt
keinen.

`showsModified()` ist die eine Stelle, an der die Datumszeile entschieden wird,
und sie fragt `SearchFilters::SORT_DEFAULT` ab, statt die beiden Datumsnamen ein
zweites Mal hinzuschreiben. `rows()` trägt damit je Zeile ein `modified`: unter
Datums-Sortierung das über `IDateTimeFormatter::formatDate($mtime, 'long')`
formatierte Datum, sonst der leere String, und für den Kanarienvogel mit
`mtime` gleich 0 ebenfalls der leere String.

Alle sieben neuen Werte gehen fertig berechnet ins Template.

### Task 3: die Testfälle (`c21f1e6`)

Vierzehn neue Fälle und vier neue Helfer.

`fingerprintOf()` liest den Fingerabdruck aus dem Weiter-Link, den die Seite für
dieselbe Adresse gebaut hat, statt ihn nachzurechnen. Das ist dieselbe Regel, die
`dayOf()` aus 13-07 befolgt, und hier ist es zugleich der einzige Weg: der Wert
wird nie zurückgegeben und nie angezeigt.

`controlLinksOf()` gibt alle vierzehn Bedienlinks einer Adresse als eine flache
Liste, mit sprechenden Schlüsseln, sodass ein Fehlschlag den Link nennt.

Die Fälle im Einzelnen:

| Bereich | Fälle |
|---|---|
| Adressen | alle vierzehn Links ohne `page`, `cursors`, `fp`; Typ-Chip an und aus, zweite Gruppe bleibt stehen; Zeitraum-Chip ersetzt und entfernt, keiner setzt `until`; `sort=relevance` in keiner Adresse, in drei Adressformen geprüft |
| Fingerabdruck | fremder Pfad aus ungefilterter Suche ergibt Seite 1 ohne Logzeile; gleiche Auswahl in anderer Reihenfolge ergibt denselben Wert; jeder der sieben Werte ändert ihn; fünf falsch geformte `fp`; passender `fp` lässt Seitenzahl und Pfad stehen |
| Blättern | `previousUrl` und `nextUrl` tragen Fingerabdruck und aktive Filter |
| Datumszeile | `modified` unter beiden Sortierungen mit zwei verschiedenen Zeitpunkten; leer unter Relevanz bei jeder Zeile; leer bei `mtime` gleich 0 |
| Zurücksetzen | kein Link ohne Filter und auch nicht bei reiner Sortierung; mit Filter weg mit allen vier Werten, aber mit dem Sortiermodus; eine reine Datumsgrenze aus dem Dialog löst ihn ebenfalls aus |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Die acht bestehenden Cursorfälle brauchen einen Fingerabdruck**

- **Found during:** Task 3
- **Issue:** Die Abnahme von Task 3 verlangt "die bestehenden Fälle sind
  unverändert grün". Das ist mit der Zusage von Task 1 nicht vereinbar. Ein
  fehlendes `fp` MUSS als Abweichung gelten, denn die Sichtprobe 6 kopiert genau
  den Parameter `cursors` von Hand in eine gefilterte Adresse, und die entsteht
  aus `filterUrl()`, das nie ein `fp` schreibt. Würde ein fehlender Wert toleriert,
  wäre die Bindung genau in dem Fall wirkungslos, für den sie gebaut wurde. Damit
  fielen fünf bestehende Fälle auf Rot und drei weitere wurden inhaltsleer.
- **Fix:** Ein Helfer `bound()` hängt an eine Adresse den Fingerabdruck, den die
  Seite selbst für sie berechnet. Die acht Fälle wurden damit umgestellt; ihre
  Aussagen sind unverändert, sie prüfen wieder das, was ihr Name sagt. Der
  Docstring von `bound()` nennt den Grund.
- **Files modified:** `php/tests/Unit/PageControllerTest.php`
- **Commit:** `c21f1e6`

**2. [Rule 3 - Blockierend] Baumhash der PHP-Hälfte nachgezogen**

- **Found during:** nach Task 3
- **Issue:** `test_the_recipe_reproduces_the_tree_hash_of_the_php_half` hält den
  Hash aller `php/**/*.php` gegen eine festgeschriebene Zahl. Zwei geänderte
  Dateien machen das Gate rot, obwohl nichts kaputt ist.
- **Fix:** `PHP_TREE_HASH_TODAY` auf den neuen Wert gesetzt, im Kommentarstil der
  Vorgängerplane: welche Dateien ihre Bytes geändert haben und warum die 64
  stehen bleibt. Dazu der Satz, dass dieser Plan allein in seiner Welle lief und
  die Zahl deshalb keine zweite Korrektur nach dem Merge braucht, anders als bei
  13-06 und 13-07.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Commit:** `6123d2b`

### Wahlentscheidungen innerhalb des Plans

- **Der Fingerabdruck läuft über die rohen Adresswerte,** also über `range` UND
  das rohe `since`, nicht über die wirksame Untergrenze. Mit der wirksamen Grenze
  wechselte der Wert um Mitternacht und würfe jeden Blätternden ohne sichtbaren
  Grund auf Seite 1. Der Plan nennt in seiner Aufzählung ohnehin beide Werte
  getrennt.
- **`filterUrl()` und `pageUrl()` teilen sich `filterArguments()`.** Getrennt
  bleibt die Position, geteilt wird die Filterliste. Zwei getrennte Listen wären
  die nächste stille Abweichung gewesen: ein Weiter-Link, der die aktiven Chips
  verliert, blättert durch ein anderes Ergebnis als das auf dem Bildschirm.
  `filterUrl()` bleibt dabei wörtlich frei von `page`, `cursors` und `fp`, was
  der Prüfblock des Plans einzeln nachweist.
- **`address()` als gelesene Wertform statt sieben positionaler Argumente.**
  `SearchFilters` prangert in seinem eigenen Docstring genau den Aufruf an, bei
  dem niemand mehr sagen kann, welcher Wert was bedeutet; sieben Stellen an fünf
  Methoden wären dieser Aufruf gewesen. Nebeneffekt und eigentlicher Gewinn: die
  Adresse wird einmal je Anfrage gelesen, also beschreiben Filterlauf,
  Fingerabdruck und alle Links dieselbe Suche, auch wenn die Anfrage über
  Mitternacht läuft. `filters()` und `outcome()` nehmen die Wertform bzw. das
  fertige Filterobjekt entgegen statt selbst zu lesen.
- **`showsModified()` fragt nach dem Standardmodus** statt die beiden
  Datumsnamen aufzuschreiben, nach derselben Regel, mit der diese Datei schon die
  Typgruppen behandelt. Der Kommentar nennt die Zeile, an der ein vierter Modus
  vorbeimüsste.
- **Die Großschreibprobe des `fp` nutzt eine feste Zeichenkette** statt
  `strtoupper()` des richtigen Werts. Ein Fingerabdruck aus lauter Ziffern ist
  selten, aber möglich, und dann wäre der Fall an genau einem Tag still
  wirkungslos statt rot.

## Verification

| Gate | Ergebnis |
|---|---|
| `tests/test_php_trust_boundary.py` | grün (21) |
| `tests/test_php_acl_boundary.py` | grün (8) |
| `tests/test_measurement_scripts.py` | grün (228) |
| Backend-Suite vollständig | grün, 2120 passed, 15 skipped |
| `ruff check` und `ruff format --check` der geänderten Python-Datei | grün |
| Prüfblock Task 1 (`filterUrl` ohne `page`, `cursors`, `fp`) | grün |
| Prüfblock Task 2 (drei Bauer, `resetUrl`, `showModified`, `formatDate`, keine Dateiendung) | grün |
| Prüfblock Task 3 (`fp`, `resetUrl`, `modified` in der Testdatei) | grün |
| Vokabular-Gate und Gedankenstrich-Probe der drei Dateien | grün |

### Ersatznachweis statt `php -l` und PHPUnit

Auf dieser Maschine gibt es kein PHP und die Docker-Engine läuft nicht, also
konnten weder `php -l` noch PHPUnit laufen. Beide laufen in CI. Als Ersatz wurde
geprüft:

- Klammer-, Anführungszeichen- und Apostrophbilanz beider PHP-Dateien nach jeder
  Aufgabe: geschweift, rund und eckig je 0, beide Anführungszeichenarten gerade,
  beide Dateien reines ASCII.
- Jede grep-Zusicherung der drei `<verify>`-Blöcke einzeln nachgefahren,
  einschließlich der Python-Probe auf den Rumpf von `filterUrl()`.
- Der Diff beider Dateien Zeile für Zeile gegengelesen, getrennt nach Code- und
  Kommentarzeilen.
- Die drei Python-Gates, die den PHP-Quelltext lesen (Route-Grenze, Rechtegrenze,
  Baumhash), laufen lokal und sind grün.

## Known Stubs

Die sieben neuen Template-Parameter werden von `php/templates/search.php` noch
nicht gelesen. Das ist Absicht und der Zuschnitt der Phase: 13-09 baut das
Markup der Filterleiste, 13-10 die Optik und den Leerzustand. Bis dahin sind die
Werte berechnet und unbenutzt, und kein Nutzer sieht eine halbe Leiste.

`filterUrl()` hat nach Task 1 für einen Commit lang keinen Aufrufer; ab Task 2
ist sie die Quelle aller vierzehn Bedienlinks.

## Threat Flags

Keine. Es kommt keine Route hinzu, kein Schreibpfad und keine neue
Vertrauensgrenze. Die Rechtefrage steht unverändert an genau einer Stelle.

| Threat ID | Umsetzung |
|---|---|
| T-13-37 | beide Maßnahmen zusammen: `filterUrl()` kennt die Position nicht, und der Pfad wird nur bei passendem Fingerabdruck angesehen; ein Fall über alle vierzehn Links und einer über den kopierten Pfad |
| T-13-38 | als Verwechslungssperre kommentiert, ohne Geheimnis und ohne Signatur; die Folgenabschätzung der Kollision steht im Docstring |
| T-13-39 | alle zehn Chips immer in der Liste, ohne Zahl, ohne Punkt, ohne Ausgrauen; der Grund steht als Kommentar an der Schleife |
| T-13-40 | `modified` existiert nur unter Datums-Sortierung, ein Fall prüft jede Zeile unter Relevanz auf den leeren String |
| T-13-41 | keine neue Route, keine JSON-Antwort; `test_php_trust_boundary.py` lief in jedem Prüfblock mit |
| T-13-SC | kein Paket installiert |

## Für den nächsten Plan

13-09 findet vor: `typeChips`, `rangeChips` und `sortLinks` als Listen aus
`key`, `active` und `url`, `resetUrl` als Adresse oder `null`, `sortMode` als
Wire-Wert, `filtersActive` und `showModified` als Boolesche Werte und je
Trefferzeile ein `modified`, das außerhalb der Datums-Sortierung leer ist. Das
Template muss nichts rechnen und nichts fragen, es setzt die Beschriftungen dazu
und entscheidet keine einzige dieser Fragen neu.

## Self-Check: PASSED

- `php/lib/Controller/PageController.php` FOUND
- `php/tests/Unit/PageControllerTest.php` FOUND
- `backend/tests/test_measurement_scripts.py` FOUND
- Commit `2d9dfc2` FOUND
- Commit `9bc0991` FOUND
- Commit `c21f1e6` FOUND
- Commit `6123d2b` FOUND
</content>
</invoke>
