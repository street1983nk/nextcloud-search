---
phase: 09-eigene-ergebnisseite
plan: 05
subsystem: ui
tags: [php, template, css, javascript, l10n, barrierefreiheit, xss, rueckkehrvertrag]

requires:
  - phase: 09-eigene-ergebnisseite
    provides: "09-04: PageController::index() und der Parametervertrag aus elf Schlüsseln"
  - phase: 09-eigene-ergebnisseite
    provides: "09-04: Highlighter::segments als Textstücke mit Marke"
  - phase: 09-eigene-ergebnisseite
    provides: "09-UI-SPEC.md, approved: Copy-Tabelle, Spacing, Typografie, Farben, Verbote, SVG-Pfaddaten"
provides:
  - php/templates/search.php mit den fünf Blöcken, serverseitig fertig gerendert
  - php/css/search.css, ausschliesslich Theme-Variablen, vier Media-Blöcke
  - php/js/search.js, die Rückkehr-Markierung als Stufe 3 des Rückkehrvertrags
  - 24 neue Copy-Elemente in de.json und de.js, identische Schlüsselmengen (149 auf 173)
  - Die zwei Dialog-Strings "Show all results" und "Opens the Findling results page" für Plan 09-07
  - Die Klasse findling-hit--returned und der Anker id="findling-hit-<fileId>"
affects: [09-06, 09-07, 09-08]

tech-stack:
  added: []
  patterns:
    - "Das Markierungselement schreibt das Template als Literal, jedes Textstück läuft einzeln durch den escapenden Drucker; es gibt keine Zeichenkette, in der Text und Auszeichnung zusammen entstehen"
    - "Die Trefferzeile ist ein Grid, damit die Handybreite den Dateinamen neben das Symbol und Pfad und Auszug darunter stellen kann, ohne dass das Markup sich ändert"
    - "Stufe 3 des Rückkehrvertrags fragt nicht nach dem Back-Forward-Cache; scrollIntoView auf der Zeile scrollt #app-content und ist damit der Träger der Position"
    - "Jeder Speicherzugriff des Skripts liegt in try/catch: fällt Stufe 3 aus, behält die Seite die Stufen 1 und 2"

key-files:
  created:
    - php/templates/search.php
    - php/css/search.css
    - php/js/search.js
  modified:
    - php/l10n/de.json
    - php/l10n/de.js

key-decisions:
  - "Kein role=alert auf dem Fehlerblock: die 09-UI-SPEC führt Live-Bereiche ausdrücklich mit Keine, und die Seite lädt vollständig neu"
  - "Kein core-Klasse checkbox am Filter: die Serverklasse versteckt das Eingabefeld und zeichnet einen Ersatz aus dem Label, ein Vertrag, der offline gegen drei Serverfassungen nicht prüfbar ist"
  - "Ohne Suchbegriff ist die h1 die Überschrift des Leerzustands, damit die Seite genau eine erste Überschriftenebene behält"
  - "Der Fehlerblock ohne Home-Verzeichnis trägt Überschrift und Symbol und keinen Satz: die Copy-Tabelle ist geschlossen und hat für diesen Fall keinen"
  - "maxlength liest PageController::MAX_QUERY_LENGTH statt die 255 ein zweites Mal zu schreiben"
  - "Der Erneut-versuchen-Link nimmt die eigene Adresse nur, wenn sie ein Pfad dieser Instanz ist; eine protokollrelative Adresse fällt auf die Formularadresse zurück"

patterns-established:
  - "Stand-in-Welt für ein Template: sechs Attrappen in ihren echten Namensräumen, das echte Template per require, php im Testcontainer"

requirements-completed: [UI-01, UI-02]

duration: 55min
completed: 2026-09-09
---

# Phase 9 Plan 05: Die sichtbare Hälfte der Ergebnisseite Summary

**Die Seite rendert ihre fünf Blöcke serverseitig fertig, ihr Stil kommt ohne einen einzigen Hexwert aus, und das einzige Skript hat zwei Ereignisse und baut kein Zeichen Markup: der Auszug wird aus Textstücken mit einem Literal-`mark` zusammengesetzt, nie aus einer Zeichenkette.**

## Performance

- **Duration:** rund 55 min
- **Tasks:** 3, alle autonom, kein Checkpoint
- **Files:** 5 (3 neu, 2 geändert), 1.014 Zeilen dazu, 2 weg

## Accomplishments

- **`php/templates/search.php`, 270 Zeilen.** Kopf mit genau einer `h1` und dem Formular ohne `page` und `cursors`, Bannerzeile, `ol` mit `aria-label`, Leerzustand statt der Liste, Paginierung. Alle sechs SVG-Pfaddaten der 09-UI-SPEC stehen wörtlich drin, jedes mit `fill="currentColor"`, `aria-hidden="true"` und `focusable="false"`. Kein `print_unescaped`, kein `<script`, kein `style=`, keine der fünf zurückgezogenen APIs.
- **Die Sicherheitsgrenze der Anzeige hält.** Ein `<script>` im Suchbegriff, ein `<b>` im Auszug, ein `<script>` im Pfad und Anführungszeichen im Dateinamen kommen allesamt als Text heraus. Das `mark`-Element existiert genau so oft, wie der Zerleger Bereiche gemeldet hat (T-09-01, T-09-02).
- **Die Vorrangregel der Bannerzeile ist gebaut und belegt:** nie zwei Banner, der Fehlerblock schlägt den Hinweis, und `offset_ceiling` landet auf der Hinweiszeile statt auf dem Fehlerblock, auch wenn zusätzlich `degraded` gemeldet ist.
- **`php/css/search.css`, 469 Zeilen, 85 Verwendungen einer Theme-Variablen.** Kein Hexwert, keine Farbfunktion, kein entfernter Fokusring. Die einzigen Zahlen ausserhalb der Grundeinheit sind die 900px der Lesespalte, die 44px unter `pointer: coarse`, die 1px der Trennlinie, die 20px der beiden Überschriften und die drei Umbruchpunkte selbst. Vier `@media`-Blöcke: 1024, 1023, 639 und `pointer: coarse`.
- **`php/js/search.js`, 225 Zeilen, zwei Ereignisse.** Kein `innerHTML`, kein `outerHTML`, kein `insertAdjacentHTML`, kein `document.write`, kein `preventDefault`, kein `pushState`, kein `AbortController`, kein `visibilityState`, kein `setTimeout`, kein `setInterval` und keine Abfrage des Back-Forward-Caches. Drei Schritte in der Reihenfolge des Vertrags: Klasse und Screenreader-Satz, dann `scrollIntoView` nur bei Bedarf, dann Fokus nur bei `back_forward`.
- **24 neue Schlüssel in beiden Katalogen**, 149 auf 173, identische Schlüsselmengen und identische Werte. Echte Umlaute, typografische Anführungszeichen, kein Em-Dash und kein En-Dash in einer der fünf Dateien. `Findling` wurde nicht doppelt angelegt.

## Task Commits

1. **Task 1: Template und die 24 Copy-Elemente** - `1c4f587` (feat)
2. **Task 2: Der Stil der Seite** - `5e29d11` (feat)
3. **Task 3: Die Rueckkehr-Markierung** - `c9b2d27` (feat)

## Verification

| Prüfung | Ergebnis |
|---|---|
| `php -l` über `search.php` im Container | `No syntax errors` |
| `node --check php/js/search.js` | grün |
| Schlüsselmengen `de.json` gegen `de.js`, Zahl 173 | gleich, 173 |
| `grep -c 'print_unescaped'` / `'<script'` / `'style='` im Template | 0 / 0 / 0 |
| Die sechs SVG-Pfaddaten im Template | je 1 |
| `grep -c 'id="findling-hit-'` im Template | 1 (die Schleife) |
| Hexwert / Farbfunktion / `outline: none` in `search.css` | 0 / 0 / 0, auch gegen die Regex von Gate C |
| `grep -c 'var(--'` in `search.css` | 85 (gefordert mindestens 30) |
| `@media`-Blöcke, davon `pointer: coarse` | 4, davon 1 |
| `innerHTML|outerHTML|insertAdjacentHTML|document.write` in `search.js` | 0 |
| `preventDefault` / `scrollRestoration` / `.persisted` in `search.js` | 0 / 0 / 0 |
| `AbortController|visibilityState|setInterval|setTimeout` in `search.js` | 0 |
| `findling:lasthit` / `back_forward` / `try` in `search.js` | 3 / 1 / 3 |
| Em-Dash und En-Dash in allen fünf Dateien | 0 / 0 |
| Emoji in allen fünf Dateien | 0 |
| Live: `GET /apps/findling/` als `testuser` | HTTP 200, Leerzustandstext, `autofocus`, beide Ressourcen eingebunden |
| Live: `GET /apps/findling/?query=Genehmigung` | HTTP 200, Fehlerblock mit Symbol, Überschrift, Satz und `Try again` auf dieselbe Adresse |
| Stand-in-Probe über neun Renderings | 49 von 49 grün |
| `uv run pytest -q` (ganze Backend-Suite) | 1778 passed, 15 skipped |
| `test_admin_ui_contract.py` allein | 31 passed |

**Die Live-Zeile `curl … | grep -c 'findling-hit-'` konnte nicht grösser als 0 werden.** Auf dieser Maschine läuft kein Findling-Backend-Container, nur `findling-nextcloud`; die Seite antwortet deshalb mit genau dem Fehlerblock, für den sie gebaut ist. Das ist ein Beleg für Block 2 und Erfolgskriterium 5 und kein Beleg für Block 3. Ersatz ist die Stand-in-Probe: sechs OCP- und Findling-Attrappen in ihren echten Namensräumen, das echte Template per `require`, neun Renderings und 49 Zusicherungen über Trefferliste, Auszug, Markierung, Paginierung, alle vier Fehlgründe, `degraded` und die Escaping-Fälle. Sie liegt in der Scratchpad-Ablage und ist bewusst nicht eingecheckt, wie die Proben aus Plan 09-04.

**Ebenfalls offen: die Sichtproben im Browser.** Dunkles Theme, Hoher Kontrast, Tastaturlauf, Handybreite, Screenreader und der Rückkehrvertrag in zwei Engines sind Augenarbeit und gehören in die Abnahme der Phase, nicht in diesen Plan. Insbesondere das Paar Fehlerfläche zu Fehlersymbol (`--color-error` mit `--color-element-error`) folgt der Farbtabelle der 09-UI-SPEC wörtlich, ist aber ein Paar, das der Server nicht als Paar auf Kontrast prüft; es gehört in Sichtprobe 16.

## Deviations from Plan

Vorbemerkung: der Entwurf eines abgestürzten Vorläufers lag als unverifiziertes Material vor (Template und l10n-Diff). Er wurde Zeile für Zeile gegen Plan und 09-UI-SPEC geprüft und in sechs Punkten korrigiert; CSS und Skript existierten dort nicht.

### Auto-fixed Issues

**1. [Rule 1 - Bug] `role="alert"` auf dem Fehlerblock entfernt**

- **Found during:** Task 1, Prüfung des Entwurfs gegen die 09-UI-SPEC
- **Issue:** Der Entwurf setzte `role="alert"` auf den Fehlerblock. Das ist ein impliziter Live-Bereich mit `aria-live="assertive"`. Der Abschnitt Barrierefreiheit der 09-UI-SPEC führt Live-Bereiche mit "**Keine.** Die Seite lädt vollständig neu, es gibt nichts, was sich unter dem Nutzer verändert". Ein assertiver Bereich hätte einen Satz angesagt, der in der Dokumentreihenfolge ohnehin schon dasteht, und dabei die Ansage unterbrochen, die der Nutzer gerade hört.
- **Fix:** Attribut entfernt. Der Block trägt weiterhin Symbol, Überschrift und Fliesstext, also drei Träger derselben Information.
- **Files modified:** `php/templates/search.php`
- **Commit:** `1c4f587`

**2. [Rule 2 - Missing critical functionality] Der Erneut-versuchen-Link kann keine fremde Adresse werden**

- **Found during:** Task 1
- **Issue:** Der Plan sagt zum Fehlerblock nur "dem Link `Try again` auf dieselbe Adresse". Die eigene Adresse kommt aus der Anfrage. Eine Referenz, die mit zwei Schrägstrichen beginnt, ist protokollrelativ und würde jemanden, der eine Suche wiederholen wollte, auf einen fremden Host schicken.
- **Fix:** Die Adresse wird nur genommen, wenn sie mit genau einem Schrägstrich beginnt; sonst tritt die Formularadresse an ihre Stelle, also dieselbe Suche von oben. Zusicherung `I` der Stand-in-Probe fährt genau diesen Fall.
- **Files modified:** `php/templates/search.php`
- **Commit:** `1c4f587`

**3. [Rule 3 - Blocking] Die Kernklasse `checkbox` am Filter fallen gelassen**

- **Found during:** Task 1
- **Issue:** Der Entwurf gab der Filter-Checkbox die Serverklasse `checkbox`. Diese Klasse schiebt das Eingabefeld aus dem Sichtfeld und zeichnet einen Ersatz über ein Pseudoelement des Labels. Ob dieser Vertrag in stable33, stable34 und stable35 gleich aussieht, lässt sich auf dieser Maschine nicht prüfen, und ein unsichtbares Kästchen ohne Ersatz wäre ein Bedienelement, das niemand findet.
- **Fix:** Natives Kästchen ohne Klasse, Label über `for` und `id` verbunden, Mindesthöhe `var(--default-clickable-area)` im eigenen CSS.
- **Files modified:** `php/templates/search.php`, `php/css/search.css`
- **Commit:** `1c4f587`, `5e29d11`

### Bewusste Auslegungen des Plans

**4. Ohne Suchbegriff hat der Leerzustand keine eigene Überschrift.** Der Plan verlangt für diesen Zweig "Ueberschrift und Text aus der Copy-Tabelle". Die Überschrift ist die `h1` des Kopfes: die 09-UI-SPEC schreibt "Genau eine `h1` (die Ergebnis- **oder** Leerzustandsüberschrift)" und lässt die `h1` in Block 1 ausdrücklich den Leerzustandstitel tragen. Beide Stellen zu füllen hätte denselben Satz zweimal untereinander gestellt. Der Zweig mit Suchbegriff trägt seine Überschrift als `h2`, weil dort die `h1` schon der Ergebnistitel ist.

**5. Der Block ohne Home-Verzeichnis trägt keinen Satz.** Das Zustands-Inventar nennt für diesen Fall den Fehlerblock "nicht suchbereit" und die Copy-Tabelle hält für diese Überschrift genau einen Satz, und der spricht über Versionen. Ihn hier zu zeigen hiesse, eine Administration hinter ein Problem zu schicken, das niemand hat. Einen neuen Satz zu erfinden verbietet die geschlossene Copy-Tabelle (T-09-05). Also Symbol und Überschrift, sonst nichts.

**6. `maxlength` liest die Konstante.** Der Plan schreibt `maxlength="255"`. Das Feld liest stattdessen `\OCA\Findling\Controller\PageController::MAX_QUERY_LENGTH`, aus demselben Grund, aus dem der Zerleger in Plan 09-04 den Deckel aus `ExAppService::MAX_HIGHLIGHTS` liest: zwei Kopien derselben Zahl sind zwei Zahlen. Gerendert steht dort `maxlength="255"`.

**7. Die Paginierungsknöpfe hellen beim Hover auf `--color-main-background` auf.** Die 09-UI-SPEC gibt dem Paginierungsstreifen `--color-background-hover` als Grund und den Knöpfen dieselbe Farbe für Hover und Fokus. Beides zusammen wäre kein Zustandswechsel. Die Knöpfe ruhen deshalb ohne eigene Fläche auf dem Streifen und nehmen im Hover den Seitengrund. Zwei Farben, beide aus dem Zweifarbenbudget der 09-UI-SPEC, keine dritte erfunden.

**8. Der Speicherschlüssel steht dreimal im Skript.** Einmal als Konstante und je einmal im Docblock des Schreibers und des Lesers. Das ist dieselbe Grep-Hygiene, die `admin.js` für seine vier Routen begründet: ein Schlüssel, der nur an einer Stelle ausgeschrieben ist, ist ein Schlüssel, den niemand findet, wenn er sich bewegt.

## Threat Model

| Threat ID | Umsetzung |
|---|---|
| T-09-01 (Tampering, `query` in Überschrift, Feld und Leerzustand) | Ausgabe ausschliesslich über `p()`. `grep -c 'print_unescaped'` ist 0. Zusicherungen `C` der Stand-in-Probe fahren einen Suchbegriff, der ein Skript-Element ist: er erscheint an drei Stellen escaped, und `<script` kommt im ganzen Dokument nicht vor |
| T-09-02 (Tampering, Auszug und Markierungsbereiche) | Das `mark`-Element ist ein Literal des Templates, jedes Textstück läuft einzeln durch `p()`. Ein `<b>` im Auszugstext bleibt Text, und das `mark` steht genau einmal, für den einen gemeldeten Bereich |
| T-09-05 (Information Disclosure, Sätze und Zahlen) | Keine Gesamttrefferzahl, keine Seitenanzahl, kein Wort über Rechte, keine Erklärung für eine kurze Seite. Die Copy-Tabelle ist geschlossen und der Block ohne Home-Verzeichnis bekam deshalb keinen erfundenen Satz. Drei Zusicherungen prüfen es |
| T-09-19 (Tampering, manipulierter `sessionStorage`-Eintrag) | Der gelesene Wert wird auf Gestalt geprüft (`key` Zeichenkette, `fileId` nichtnegative Ganzzahl) und steuert danach ausschliesslich, welche bereits im Markup vorhandene Zeile eine Klasse bekommt. Er wird nie in eine Adresse, nie in Markup und nie in eine Anfrage gesetzt; ein unbekannter Wert findet schlicht kein Element |
| T-09-20 (DoS, Skript im Fehlerfall) | Beide Speicherzugriffe liegen in `try`/`catch`, das Skript pollt nicht, lädt nichts nach und fängt keinen Klick ab. Fällt es ganz aus, verliert die Seite genau die Rückkehr-Markierung |
| T-09-21 (Information Disclosure, Trefferliste im Browsercache) | accept, wie geplant. Der `Cache-Control`-Kopf der Antwort wurde nicht angefasst; die Folge für Stufe 2 des Rückkehrvertrags trägt Stufe 3, die deshalb als tragend gebaut ist |
| T-09-SC (Supply Chain) | Kein Paket installiert, keine `package.json`, kein Build-Step. Die sechs SVG-Pfaddaten sind Kurvendaten aus dem in `THIRD-PARTY.md` gepinnten Commit, kein Code |

Keine neue Angriffsfläche ausserhalb des Registers: dieser Plan legt keine Route an, keinen Endpunkt, keinen Schreibvorgang und keinen Schemawechsel. Die einzige neue Zustandsablage ist `sessionStorage['findling:lasthit']` im Browser, und sie steht im Modell.

## Notes for Future Phases

- **Plan 09-06 (Gates) erbt drei Dateien und eine Falle.** Der Scanner darf die Admin-Sondertests nicht auf diese Seite ziehen (09-RESEARCH, Pitfall 4). Was die neue Seite hält und woran sie sich messen lassen kann, steht in der Verifikationstabelle oben; alle dortigen Zahlen sind heute wahr.
- **Zwei der 24 Schlüssel gehören noch niemandem.** `Show all results` und `Opens the Findling results page` sind der Einstiegs-Eintrag im Suchdialog und werden erst von Plan 09-07 gerendert. Sie liegen bereits in beiden Katalogen, damit dieser Plan keinen zweiten l10n-Schritt braucht.
- **Die Klasse `findling-hit--returned` und der Anker `id="findling-hit-<fileId>"` sind die Nahtstelle** zwischen Template, Stil und Skript. Wer eine davon umbenennt, bewegt drei Dateien in einem Commit.
- **`THIRD-PARTY.md` ist noch nicht angefasst.** Die 09-UI-SPEC verlangt die drei neuen MDI-Namen (`chevron-left`, `chevron-right`, `file-search-outline`) "in dem Plan, der sie zuerst rendert", und das ist dieser. Der Plan nennt die Datei in keiner Aufgabe und in keiner Dateiliste, und eine Datei anzufassen, die der Plan nicht führt, wäre eine stille Erweiterung des Auftrags. Aufgenommen als aufgeschobener Punkt, siehe unten.
- **Der Fokus wandert mit `preventScroll: true`.** Ohne das Flag würde `focus()` die Entscheidung von Schritt zwei sofort wieder überschreiben, und zwar genau in dem Fall, in dem Schritt zwei bewusst nicht gescrollt hat.
- **`php/img/app.svg` und der Navigationseintrag fehlen weiterhin.** Ohne sie erreicht ein Nutzer die Seite nur über eine getippte Adresse oder über den Einstiegs-Eintrag aus Plan 09-07. Das ist die geplante Reihenfolge und kein Defekt dieses Plans.

## Deferred Issues

| Id | Punkt | Warum offen |
|---|---|---|
| DI-09-01 | `THIRD-PARTY.md` bekommt `chevron-left`, `chevron-right` und `file-search-outline` in die Namensliste und in die Prüfschleife | Ausserhalb der Dateiliste dieses Plans. Gehört in Plan 09-06 oder in die Phasen-Verifikation, spätestens vor der Store-Abgabe |
| DI-09-02 | Die zwanzig Abnahme-Sichtproben der 09-UI-SPEC, insbesondere 4, 5, 16, 17, 18 und 19 | Augenarbeit in zwei Browser-Engines, und für die Trefferliste braucht es einen laufenden Backend-Container, den diese Maschine gerade nicht hat |
| DI-09-03 | Sichtprobe 5 ist in der vorliegenden Fassung nicht haltbar und gehört umformuliert | Befund 2 der 09-RESEARCH: `no-store` schliesst die Seite in Firefox vom Back-Forward-Cache aus, die Scrollposition ohne JavaScript ist damit browserabhängig |

## Self-Check: PASSED

- `php/templates/search.php`, `php/css/search.css`, `php/js/search.js` liegen auf der Platte, 270, 469 und 225 Zeilen.
- `php/l10n/de.json` und `php/l10n/de.js` tragen beide 173 Schlüssel, Mengen und Werte identisch.
- Die drei Commits `1c4f587`, `5e29d11` und `c9b2d27` stehen in `git log`.
- Der Arbeitsbaum war vor dem Schreiben dieser Datei sauber.
