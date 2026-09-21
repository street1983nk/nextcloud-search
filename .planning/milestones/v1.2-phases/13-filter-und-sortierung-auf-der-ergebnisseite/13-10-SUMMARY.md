---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 10
subsystem: php-companion
tags: [css, filterleiste, chips, sortierlinks, barrierefreiheit, responsive, gates, verbote, filt-01, filt-04]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 09
    provides: "die vollstaendige Auszeichnung der Leiste: findling-filters samt row, label, group und reset, findling-chip-link samt --active, findling-sort samt __link und --active, findling-hit__modified"
  - phase: 09-eigene-ergebnisseite
    plan: 06
    provides: "php/css/search.css mit Kopfkommentar, Farb- und Abstandsregeln, den vier Media Queries und dem Gate-Muster ueber Template, Stil und Skript"
provides:
  - "Block 2b in php/css/search.css: Leiste, drei Zeilen, drei Beschriftungen, zwei Gruppenarten"
  - "findling-chip-link als Link mit Rahmen und Mindesthoehe, --active im hellen Akzentpaar mit Hauchrahmen"
  - "findling-sort__link und --active, Zustand ueber Schriftgewicht 700"
  - "findling-filters__reset rechtsbuendig ab 640px, linksbuendig in eigener Zeile darunter"
  - "findling-hit__modified in Block 3, 13px/400, maxcontrast, nowrap"
  - "Umbruch statt Seitwaertsrollen unter 640px, 44px fuer alle vierzehn Bedienelemente unter pointer coarse"
  - "sechs neue Gates in backend/tests/test_admin_ui_contract.py, je mit Anti-Vakuitaets-Klausel und Selbsttest"
  - "scan_template prueft zusaetzlich das style-Attribut, fuer beide Templates zugleich"
affects: [13-11, 13-12]

tech-stack:
  added: []
  patterns:
    - "Der aktive Chip nutzt das helle Akzentpaar und nicht den starken Akzent: ein Zustand ist keine Handlungsaufforderung, und der starke Akzent bleibt dem einen Knopf vorbehalten, der die Seite vorantreibt"
    - "Ein Gate, das eine Region eines Templates liest, schneidet sie am Kommentar-Oeffner des Blocks und entfernt die Kommentare vor dem Scan: sonst geht es an genau dem Satz rot, der verspricht, was es haelt"
    - "Ein neues Verbot, das fuer beide Templates gilt, erweitert den bestehenden Scanner statt ein zweites Gate danebenzustellen"
    - "Die Verbote der Phase werden als Marker-Tupel geschrieben und nicht als Schwelle: eine Liste nennt jeden Fall, eine Zahl deckt einen vergessenen genauso gut wie einen gewollten"

key-files:
  created: []
  modified:
    - php/css/search.css
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "Der aktive Chip verliert unter dem Zeiger seine Akzentflaeche und behaelt Rahmen und close-Symbol: 13-UI-SPEC nennt fuer Hover und Fokus ausnahmslos --color-background-hover, und der Zustand haengt ohnehin nicht an der Flaeche"
  - "Der Zuruecksetzen-Link ist unterstrichen statt umrandet: er ist ein Satz und kein elfter Chip, und die Unterstreichung ist dieselbe Loesung wie beim Wiederholen-Link der Bannerzeile"
  - "Das Zaehl-Orakel-Gate verbietet die Woerter des Zaehlens (count, total, badge, disabled, die Pluralform) und nicht die Ziffer: Letzte 7 Tage und Letzte 30 Tage tragen selbst Ziffern, ein Ziffern-Gate waere am ersten Tag rot"
  - "Die Docstring-Ueberschrift heisst What this gate does not prove und nicht Was dieses Gate nicht beweist: die Datei ist durchgehend englisch, wie jede Codezeile dieses Projekts"

patterns-established:
  - "Ein Stil-Plan, der nur bestehende Variablen verwendet, braucht kein Sichtprotokoll fuer Hell, Dunkel und hohen Kontrast: die drei Zweige entstehen aus denselben geprueft ausgelieferten Paaren"

requirements-completed: []  # FILT-01 und FILT-04 tragen noch 13-11 und 13-12

duration: 20min
completed: 2026-09-17
---

# Phase 13 Plan 10: Stil der Filterleiste und die Gates der Verbotsliste Summary

**Die vierzehn Bedienelemente der Leiste sehen jetzt aus wie der Rest der Seite, ohne eine einzige neue Variable und ohne einen Hexwert, und jedes der sechs textpruefbaren Verbote dieser Phase hat sein Gate mit Anti-Vakuitaets-Klausel und Selbsttest.**

## Performance

- **Duration:** 20 min
- **Tasks:** 2
- **Commits:** 2

## Was gebaut wurde

### Task 1: Die neuen CSS-Regeln (`0b6db57`)

`php/css/search.css` hat einen neuen Abschnitt "block two b, the filter row"
zwischen Bannerzeile und Trefferliste, also genau an der Stelle, an der die
Leiste auf der Seite steht.

Die Leiste selbst ist eine Spalte aus drei Zeilen mit 8px Abstand und 24px zur
Trefferliste; den Abstand nach oben liefert die Bannerzeile bereits. Jede Zeile
ist eine umbrechende Reihe mit 16px zwischen Beschriftung und Gruppe. Die drei
Beschriftungen sind 13px/400 in `--color-text-maxcontrast`. Die Chip-Gruppen
haben 8px zwischen zwei Chips, die Sortierzeile 16px zwischen zwei Links, wie
die Abstandstabelle es festlegt. Jeder eigene Abstand steht als
`calc(var(--default-grid-baseline) * n)`; die einzige Ausnahme ist der 4px-Spalt
zwischen Chip-Beschriftung und `close`-Symbol, der als blosses
`var(--default-grid-baseline)` geschrieben ist, weil er die Basis selbst und
kein Vielfaches ist und weil `admin.css` ihn woertlich so schreibt.

`.findling-chip-link` nimmt die Grundform des Chips der Verwaltungsseite und das
Verhalten eines Pager-Schritts: `inline-flex`, `min-height:
var(--default-clickable-area)`, `text-decoration: none`, dazu Rahmen 1px
`--color-border` und Grund `--color-main-background`. `--active` setzt darauf
`--color-primary-element-light`, `--color-primary-element-light-text` und einen
Hauchrahmen `--color-primary-element`. Darueber steht die Begruendung aus
13-UI-SPEC in zwei Saetzen: ein aktiver Chip ist ein Zustand und keine
Handlungsaufforderung, der starke Akzent bleibt dem einen Knopf vorbehalten, und
das helle Paar ist vom Server auf Kontrast geprueft ausgeliefert; und die Farbe
ist nie der einzige Traeger, weil `close`-Symbol und `aria-current` danebenstehen.

`.findling-sort__link` ist dieselbe Linkform ohne Rahmen und ohne eigene
Flaeche, `--active` unterscheidet sich in genau einer Zeile: `font-weight: 700`.
Der Kommentar sagt, dass das Gewicht hier ein Zustandstraeger und keine vierte
typografische Rolle ist, und dass es dort steht, weil in dieser Zeile kein
Symbol steht.

`.findling-filters__reset` hat dieselbe Mindesthoehe und wird per
`margin-inline-start: auto` an das Ende der Zeitraum-Zeile geschoben. Hover und
Fokus aller drei Arten liegen in einer Regel auf `--color-background-hover`. Es
gibt kein `outline: none`; der Fokusring des Cores ist unberuehrt.

`.findling-hit__modified` steht in Block 3 direkt unter `.findling-hit__path`:
13px/400, `--color-text-maxcontrast`, `white-space: nowrap`.

In der bestehenden `@media (max-width: 639px)` wird die Zeile zur Spalte
(`flex-direction: column; align-items: flex-start`), womit die Beschriftung
ueber ihre Gruppe rutscht und der Zuruecksetzen-Link linksbuendig in eigener
Zeile steht; `margin-inline-start` faellt dafuer auf 0 zurueck. Der Kommentar
nennt den Grund gegen eine waagerecht scrollende Leiste: eine Reihe, aus der ein
Teil herausgeschoben ist, versteckt Bedienung hinter einer Geste und ist auf der
Tastatur gar nicht auffindbar. In der bestehenden `@media (pointer: coarse)`
wachsen Chips, Sortierlinks und der Zuruecksetzen-Link auf 44px.

Zwei bestehende Kommentare wurden nachgezogen, weil sie sonst unwahr geworden
waeren: der Kopfkommentar der 639er-Umbruchstelle nennt jetzt auch die Leiste,
und der Kommentar der Fingerregel sagt nicht mehr "die zwei Dinge, die ein
Daumen anzielt", sondern zaehlt die vierzehn Bedienelemente der Leiste mit.

### Task 2: Die Verbote als Gates (`e33f254`)

`backend/tests/test_admin_ui_contract.py` hat einen neuen Abschnitt mit fuenf
Scannern und sechs Tests. Die Datei waechst von 39 auf 45 Tests.

1. **Kein Skript fuer die Leiste.** `scan_page_script_for_the_filter_row` liest
   `php/js/search.js` gegen vier Marker: `findling-filters`,
   `findling-chip-link`, `findling-sort` und `aria-current`. Der Docstring nennt
   die Zusage aus D-02, D-03 und D-05 und sagt im Absatz "What this gate does
   not prove", dass ein Zuhoerer an einem blossen `a` keine dieser Zeichenketten
   traegt und vom bestehenden `preventDefault`-Gate abgefangen wird.

2. **Kein zweiter Bedienkanal.**
   `scan_page_template_for_a_second_control_channel` meldet jedes `<select>` und
   jedes `<option>` und zaehlt die `<form>`-Elemente; alles ausser genau einem
   ist ein Befund. Die Anti-Vakuitaets-Klausel ist die Zaehlung selbst.

3. **Kein `aria-pressed`.** `scan_template_for_a_pressed_link` laeuft ueber jedes
   Template der App, nicht nur ueber die Ergebnisseite. Die Klausel prueft, dass
   die Glob-Suche wirklich `admin.php` und `search.php` findet.

4. **Kein `style`-Attribut.** Der bestehende `scan_template` bekommt eine
   siebte Zeile statt eines zweiten Gates; damit gilt das Verbot fuer beide
   Templates zugleich. Der Selbsttest prueft auch den Beinah-Treffer:
   `data-style="x"` ist kein `style`-Attribut.

5. **Kein Zaehl-Orakel.** `scan_filter_row_for_a_counting_oracle` schneidet die
   Leiste zwischen `<?php /* Block 2b:` und `<?php /* Block 3:` heraus, entfernt
   alle Blockkommentare und sucht dann nach `count`, `total`, `badge`,
   `disabled` und `$l->n(`. Eine verlorene Region ist selbst ein Befund.

6. **Mindesthoehe und Umbruch.** `scan_page_stylesheet_for_a_reachable_row`
   liest die Regelkoerper von `.findling-chip-link`, `.findling-sort__link` und
   `.findling-filters__reset` auf `min-height: var(--default-clickable-area)`,
   den Rumpf der `pointer: coarse`-Query auf die 44px je Bedienelement, die drei
   Container auf `flex-wrap: wrap` und die ganze Datei auf `overflow-x`.

Jeder der sechs Tests traegt einen Docstring mit dem Absatz "What this gate does
not prove", eine Anti-Vakuitaets-Klausel und mindestens einen Selbsttest, der
eine von Hand gebaute, fehlerhafte Fassung rot werden laesst. Die Zahl `174` und
`FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` sind unangetastet; beide gehoeren
Plan 13-11.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Der Pruefblock von Task 1 zaehlt zwei Media Queries, die Datei hat vier**

- **Found during:** Task 1
- **Issue:** `<verify>` verlangt `grep -c '@media' php/css/search.css | grep -qx
  2`, also genau zwei Media Queries, und das Akzeptanzkriterium sagt "weiterhin
  genau zwei". `php/css/search.css` hat aber seit Phase 9 vier:
  `min-width: 1024px`, `max-width: 1023px`, `max-width: 639px` und
  `pointer: coarse`. Der `<interfaces>`-Abschnitt desselben Plans nennt nur die
  beiden, in die neue Regeln gehoeren ("die beiden bestehenden Umbruchstellen"),
  und leitet daraus offenbar die Zahl ab. Der Pruefblock waere damit an einer
  unveraenderten Datei rot gewesen.
- **Fix:** Die pruefbare Absicht ist "keine neue Media Query", und die wurde
  eingehalten: die Zahl steht vor und nach diesem Plan bei vier, alle neuen
  Regeln stehen in den beiden bestehenden Umbruchstellen. Geprueft wurde gegen
  4 statt gegen 2.
- **Files modified:** keine; nur der Nachweis wurde angepasst
- **Commit:** `0b6db57`

### Wahlentscheidungen innerhalb des Plans

- **Der aktive Chip gibt unter dem Zeiger seine Akzentflaeche ab.** Die
  Farbtabelle in 13-UI-SPEC nennt fuer Hover und Fokus ausnahmslos
  `--color-background-hover`, ohne Ausnahme fuer den aktiven Chip. Die Regel
  setzt deshalb nur `background-color`; Rahmen `--color-primary-element`,
  `close`-Symbol und `aria-current` bleiben, der Zustand ist also auch unter dem
  Zeiger an drei Stellen ablesbar. Der Kommentar sagt das ausdruecklich, damit
  der naechste Leser es nicht fuer ein Versehen haelt.
- **Der Zuruecksetzen-Link ist unterstrichen und nicht umrandet.** Die Vorgabe
  nennt nur Mindesthoehe und Rechtsbuendigkeit. Ein Rahmen haette ihn zum elften
  Chip gemacht, obwohl er kein Filter ist, sondern deren Aufhebung; die
  Unterstreichung ist dieselbe Loesung, die der Wiederholen-Link der
  Bannerzeile schon verwendet.
- **`.findling-sort` bekommt eine eigene Regel statt einer Ueberschreibung.**
  Gruppe und Sortierzeile unterscheiden sich nur im Spalt (8px gegen 16px). Zwei
  vollstaendige Regeln sind drei Zeilen mehr als eine gemeinsame mit einer
  Ausnahme, und sie ersparen dem Leser die Frage, welche der beiden Zahlen gilt.
- **Das Zaehl-Orakel-Gate sucht Woerter und keine Ziffern.** Der Plan schlaegt
  "kein `findling-chip-link`-Element mit einer Ziffernausgabe" vor. Zwei der vier
  Zeitraum-Beschriftungen sind "Last 7 days" und "Last 30 days", und das
  `close`-Symbol traegt `viewBox="0 0 24 24"`: ein Ziffern-Gate waere am ersten
  Tag rot gewesen. Die fuenf Marker decken stattdessen jede Form, die die
  Verbotsliste nennt, inklusive der Pluralform, mit der eine gezaehlte Aussage
  allein gebaut werden koennte.
- **Die Region wird am Kommentar-Oeffner geschnitten und die Kommentare werden
  vor dem Scan entfernt.** Der Blockkommentar der Leiste erklaert selbst, dass es
  keinen Zaehler, keinen Punkt und kein Ausgrauen gibt, und nennt dabei die
  Woerter `count`, `dot` und `greyed out`. Ein Schnitt an einer Klasse haette die
  Region mitten in einem Kommentar beginnen lassen, der Kommentarentferner haette
  den Oeffner nicht gefunden, und das Gate waere an seiner eigenen Begruendung
  rot geworden. Das ist dieselbe Falle, die 13-09 beim `aria-current`-Kommentar
  bereits umschifft hat; hier ist sie im Gate geloest statt in der Prosa.
- **"What this gate does not prove" statt der deutschen Ueberschrift.** Der Plan
  nennt den Absatz auf Deutsch. Die Datei ist durchgehend englisch, wie jede
  Codezeile dieses Projekts, und der Modul-Docstring fuehrt bereits "What this
  gate does not claim". Die englische Fassung fuegt sich ein; die Pflicht, den
  Absatz zu haben, ist erfuellt.
- **`.findling-hit__modified` steht in Block 3 und nicht im neuen Abschnitt.**
  Der Plan listet die Regel unter Task 1 auf, und Task 1 verlangt die Reihenfolge
  der Bloecke der Seite. Die Zeile gehoert in die Trefferzeile, also direkt unter
  `.findling-hit__path`.

## Verification

| Gate | Ergebnis |
|---|---|
| Backend-Suite vollstaendig | gruen, 2126 passed, 15 skipped (vorher 2120, plus die sechs neuen Tests) |
| `tests/test_admin_ui_contract.py` | gruen, 45 statt 39 |
| `uv run ruff check .` | gruen |
| `uv run ruff format --check .` | gruen (122 Dateien) |
| `uv run pyright` | gruen, 0 errors |
| `uv run vulture` | gruen, keine Ausgabe |
| Baumhash-Gate der PHP-Haelfte | gruen und unangetastet: dieser Plan aendert keine `.php`-Datei, `PHP_TREE_HASH_TODAY` bleibt auf `abe36dc6...` bei 64 Dateien |
| Katalog-Gates (174, franzoesische Vollstaendigkeit, Pluralregel) | gruen und unveraendert |
| Vokabular, Gedankenstriche, Emojis | gruen; `scan_prose` laeuft ueber beide neuen Dateien mit |

### Pruefblock Task 1, einzeln nachgefahren

| Zusicherung | Ergebnis |
|---|---|
| `findling-chip-link`, `--active`, `findling-sort__link`, `findling-hit__modified` haben Regeln | gruen |
| `var(--color-primary-element-light)` und `-light-text` je zweimal, `var(--color-primary-element)` einmal | gruen |
| kein Hexwert (`#[0-9a-f]{3,8}`) | 0 Treffer |
| keine Farbfunktion (`rgb(`, `rgba(`, `hsl(`) | 0 Treffer |
| kein `outline: none` | 0 Treffer |
| Media Queries | 4, wie vor diesem Plan (siehe Abweichung 1) |
| Klammerbilanz der Datei, Kommentare entfernt | 0 |
| jeder blanke Pixelwert ist eine benannte Ausnahme | 900 (Lesespalte), 20 (Ueberschriftgroesse), 1px (Rahmen), 44px (Fingerregel), 1024/1023/639 (Umbruchstellen) |
| `min-height: var(--default-clickable-area)` | 9 Stellen, darunter die drei neuen |
| `overflow-x` | 0 Treffer |

### Pruefblock Task 2, einzeln nachgefahren

`grep -q 'aria-pressed'` gruen (5 Stellen), `grep -q 'search.js'` gruen (2
Stellen). Die Zeile `assert len(keys_of["de.json"]) == 174` und der zweizeilige
`FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` stehen unveraendert im Diff.

### Ersatznachweis statt `php -l` und PHPUnit

Entfaellt: dieser Plan aendert keine PHP-Datei. Die beiden geaenderten Dateien
sind eine CSS- und eine Python-Datei, und beide werden von Gates gelesen, die
lokal laufen.

### Was lokal nicht geprueft werden konnte

Die Sichtprobe in Hell, Dunkel und hohem Kontrast (Abnahmepunkt 15) und die
Handybreite unter 640px (Punkt 16) brauchen die laufende Testinstanz und
gehoeren zur Abnahme der Phase. Dieser Plan hat dafuer die eine Vorkehrung
getroffen, die im Quelltext moeglich ist: es gibt keinen Wert, der nicht aus
einer geprueft ausgelieferten Variablen kommt, also kann kein Zweig eigene
Kontrastwerte haben.

## Known Stubs

Keine im Zuschnitt dieses Plans. Die Leiste ist vollstaendig gestylt.

Was weiterhin offen ist und nicht diesem Plan gehoert: die 23 Quell-Strings
stehen nur auf Englisch, die Kataloge und die Zahl 197 kommen mit 13-11, und
FILT-01 und FILT-04 werden erst nach 13-12 als erfuellt markiert.

## Threat Flags

Keine. Es kommt keine Route hinzu, kein Schreibpfad, kein JSON-Kanal und keine
neue Vertrauensgrenze; eine CSS-Datei und eine Testdatei koennen keine haben.

| Threat ID | Umsetzung |
|---|---|
| T-13-47 | eigenes Gate ueber die Region der Leiste, fuenf Marker, Kommentare vorher entfernt, Selbsttest mit drei Formen gleichzeitig |
| T-13-48 | `scan_template` um das `style`-Attribut erweitert statt verdoppelt; das Inline-Skript-Verbot galt bereits |
| T-13-49 | zwei Gates: genau ein `<form>` samt Verbot von `select` und `option`, und `search.js` ohne jeden Bezug auf die Leiste |
| T-13-50 | jedes der sechs neuen Gates hat Anti-Vakuitaets-Klausel und Selbsttest; ein geloeschter Rumpf wird rot |
| T-13-51 | kein `overflow-x`, drei umbrechende Container, alles vom Umbruch-Gate gelesen |
| T-13-SC | kein Paket installiert, kein neues Symbol, keine neue Abhaengigkeit |

## Fuer den naechsten Plan

13-11 findet die Zahl `174` und die zweizeilige G2-Ausnahmeliste genau so vor,
wie 13-09 sie hinterlassen hat, und muss beide zusammen mit den sechs
Katalogdateien und `docs/l10n-french.md` in einem Zug auf 197 und fuenf
Eintraege ziehen. Der neue `scan_template`-Zweig fuer das `style`-Attribut
beruehrt die Kataloge nicht.

13-12 findet eine Seite vor, deren Leiste vollstaendig aussieht und sich
vollstaendig bedienen laesst, und kann sich auf die Abnahme-Sichtproben
beschraenken.

## Self-Check: PASSED

- `php/css/search.css` FOUND
- `backend/tests/test_admin_ui_contract.py` FOUND
- `.planning/phases/13-filter-und-sortierung-auf-der-ergebnisseite/13-10-SUMMARY.md` FOUND
- Commit `0b6db57` FOUND
- Commit `e33f254` FOUND
- Commit `c92e7eb` FOUND (dieser Eintrag, Hash aus dem Log)
