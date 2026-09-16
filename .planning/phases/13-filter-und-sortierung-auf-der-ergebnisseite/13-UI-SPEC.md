---
phase: 13
slug: filter-und-sortierung-auf-der-ergebnisseite
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-16
extends: .planning/milestones/v1.1-phases/09-eigene-ergebnisseite/09-UI-SPEC.md
---

# Phase 13: UI Design Contract

> Visueller und interaktiver Vertrag fuer Filter und Sortierung auf der eigenen
> Ergebnisseite. Erzeugt von gsd-ui-researcher, zu pruefen von gsd-ui-checker.
>
> **Dieser Vertrag ist eine Fortschreibung, keine Neufassung.** Die Ergebnisseite
> hat seit Phase 9 einen abgenommenen Vertrag
> (`.planning/milestones/v1.1-phases/09-eigene-ergebnisseite/09-UI-SPEC.md`,
> approved 09.09.2026). Spacing, Typografie, Farbrollen, Bauweise, Verbote und
> Barrierefreiheits-Regeln von dort gelten unveraendert weiter und werden hier
> nicht neu entschieden. Dieses Dokument nennt nur, was Phase 13 hinzufuegt, und
> markiert jede Stelle, an der es eine Zusage von Phase 9 beruehrt.
>
> **Schreibweise.** Die Prosa dieses Dokuments folgt der ASCII-Konvention der
> `.planning`-Dateien (ae/oe/ue/ss). Die **Copy-Tabelle ist davon ausgenommen**:
> ihre Werte sind woertlich der Inhalt der Katalogdateien und tragen deshalb echte
> Umlaute und echte Akzente, genau so, wie sie in `php/l10n/*` stehen muessen. Was
> in der Tabelle steht, wird kopiert und nicht abgeschrieben.

---

## Was diese Phase an der Seite aendert

| # | Aenderung | Quelle |
|---|-----------|--------|
| 1 | Neuer Block "Filterleiste" zwischen Bannerzeile und Trefferliste: sechs Typ-Chips, vier Zeitraum-Chips, drei Sortierlinks, ein Zuruecksetzen-Link | D-02, D-03, D-05, D-06 |
| 2 | Vierte Zeile in der Trefferzeile ("Geaendert am ...") **nur** unter Datums-Sortierung | D-04 |
| 3 | Vierte Variante des Leerzustands: keine Treffer unter aktivem Filter | D-07 |
| 4 | Fuenf neue URL-Werte (`types`, `sort`, `range`, `since`, `until`) plus der Cursor-Fingerabdruck `fp` | FILT-04, 13-RESEARCH Befund 7 |
| 5 | 23 neue Katalogschluessel in sechs Dateien, Gate-Zahl 174 wird 197 | 13-RESEARCH Befund 11 |

Was diese Phase **nicht** aendert: keine neue Route, kein Vue, kein Build-Schritt,
kein JavaScript fuer Filter oder Sortierung, kein neues Symbol, keine neue
Abhaengigkeit, kein Trefferzaehler, keine Gesamtzahl.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none. Kein npm, kein Bundler, kein Build-Step (Fortschreibung 04-CONTEXT D-02, 09-UI-SPEC) |
| Preset | not applicable |
| Component library | none. Nextcloud-Server-CSS plus die bestehende `php/css/search.css` |
| Icon library | Material Design Icons (Pictogrammers), Apache-2.0, als Inline-SVG. **Phase 13 fuegt kein neues Symbol hinzu**: das einzige gebrauchte Zeichen ist `close`, seit Phase 4 gepinnt und in `THIRD-PARTY.md` gelistet |
| Font | `var(--font-face)` von Nextcloud. Keine eigene Schrift |

**shadcn-Gate:** nicht anwendbar. Der Stack ist ein serverseitig gerendertes
PHP-Template ohne Node-Werkzeugkette; es gibt kein `components.json`, keine
`package.json` und keinen Ort, an dem ein Preset wirken koennte. Geprueft am
16.09.2026 am Repositoriumswurzelverzeichnis.

### Verwendete Nextcloud-Variablen (alle in Phase 9 gegen stable33/34/35 verifiziert)

`--default-grid-baseline`, `--default-font-size`, `--font-size-small`,
`--default-line-height`, `--default-clickable-area`, `--border-radius-container`,
`--border-radius-small`, `--color-main-background`, `--color-main-text`,
`--color-background-hover`, `--color-border`, `--color-text-maxcontrast`,
`--color-primary-element`, `--color-primary-element-light`,
`--color-primary-element-light-text`.

Phase 13 fuehrt **keine neue Variable** ein. Wer beim Bau eine braucht, hat einen
Entwurfsfehler gefunden und keine fehlende Variable.

---

## Spacing Scale

Unveraendert aus 09-UI-SPEC. Basis `var(--default-grid-baseline)` = 4px, jeder
eigene Abstand als `calc(var(--default-grid-baseline) * n)`.

| Token | Value | Verwendung in Phase 13 |
|-------|-------|------------------------|
| xs | 4px | Abstand Chip-Label zu x-Symbol |
| sm | 8px | Abstand zwischen zwei Chips, Innenabstand eines Chips waagerecht, Abstand zwischen den drei Zeilen der Filterleiste |
| md | 16px | Abstand zwischen zwei Sortierlinks, Abstand Zeilenbeschriftung zu ihrer Chip-Gruppe |
| lg | 24px | Abstand Filterleiste zu Trefferliste, Abstand Bannerzeile zu Filterleiste |
| xl | 32px | keine neue Verwendung |
| 2xl | 48px | keine neue Verwendung |
| 3xl | 64px | Kantenlaenge des Symbols im neuen Leerzustand (wie die drei bestehenden) |

**Exceptions (unveraendert, beide fremdbestimmt oder bereits begruendet):**

| Wert | Woher | Umgang in Phase 13 |
|------|-------|--------------------|
| 34px | `var(--default-clickable-area)` | Mindesthoehe **jedes** Chips, **jedes** Sortierlinks und des Zuruecksetzen-Links. Ein Chip ist ein Link und damit eine Klickflaeche, kein Etikett wie die Chips der Verwaltungsseite |
| 44px | eigene Regel | Unter `@media (pointer: coarse)` steigt die Mindesthoehe von Chips und Sortierlinks auf 44px, wie bei Trefferzeile und Pager. 44 ist ein Vielfaches von 4 |
| 1px | Rahmen | Chip-Rahmen, wie die bestehende Trennlinie zwischen Trefferzeilen. Ein Rahmen ist keine Abstandsgroesse |

Keine neue Ausnahme. Die Inhaltsbreite bleibt 900px.

---

## Typography

Unveraendert aus 09-UI-SPEC: **drei Groessen (13, 15, 20), zwei Gewichte (400, 700).**
Phase 13 fuegt keine vierte Groesse und kein drittes Gewicht hinzu.

| Role | Size | Weight | Line Height | Verwendung in Phase 13 |
|------|------|--------|-------------|------------------------|
| Body | 15px (`var(--default-font-size)`) | 400 | 1.5 | Text des neuen Leerzustands |
| Hit title | 15px | 700 | 1.5 | unveraendert |
| Label | 13px (`var(--font-size-small)`) | 400 | 1.5 | Chip-Beschriftung, Zeilenbeschriftungen der Filterleiste, Sortierlinks im Ruhezustand, Zuruecksetzen-Link, die neue Zeile "Geaendert am ..." |
| Label aktiv | 13px | **700** | 1.5 | **nur** der aktive Sortierlink. Das Gewicht ist hier ein Zustandstraeger und keine neue Rolle |
| Heading | 20px | 700 | 1.2 | Ueberschrift des neuen Leerzustands |

Der aktive Chip bleibt bei 400, weil sein Zustand ueber Flaeche, x-Symbol und
`aria-current` getragen wird; ein Gewichtswechsel wuerde die Leiste bei jedem
Klick umbrechen lassen. Der aktive Sortierlink bekommt 700, weil dort kein Symbol
steht und die Zeile drei gleich gebaute Woerter nebeneinander stellt.

---

## Color

Kein Hexwert, keine Farbfunktion, ausschliesslich Variablen. Das Gate von Phase 9
gilt unveraendert fuer jede neue Regel in `php/css/search.css`.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `var(--color-main-background)` | Seitengrund, Grund eines **inaktiven** Chips, Grund eines Sortierlinks im Ruhezustand |
| Secondary (30%) | `var(--color-background-hover)` | Chip und Sortierlink bei Hover und Fokus, Trefferzeile bei Hover, Pagerstreifen. Rahmen des inaktiven Chips: `var(--color-border)` |
| Accent (10%) | `var(--color-primary-element)` und das helle Paar `var(--color-primary-element-light)` / `var(--color-primary-element-light-text)` | siehe Reserveliste |
| Destructive | nicht anwendbar | **Diese Phase hat keine zerstoererische Aktion.** Ein Filter entfernen ist kein Loeschen: es schreibt nichts, es verliert nichts, und die Adresse davor steht im Verlauf des Browsers. Es gibt deshalb keine Bestaetigungsflaeche, keinen roten Knopf und keinen Dialog |

**Accent reserved for:** genau vier Dinge, nichts sonst. Die ersten drei sind
woertlich die aus 09-UI-SPEC, das vierte ist die eine Erweiterung dieser Phase.

1. Der einzige `.primary`-Knopf der Seite: "Suchen".
2. Die Hervorhebung des Suchworts im Auszug (`<mark>`, helles Paar).
3. Der Fokusring von Links, Knoepfen und Eingabefeld (kommt vom Core).
4. **Neu:** der aktive Filter-Chip. Flaeche `var(--color-primary-element-light)`,
   Text `var(--color-primary-element-light-text)`, Hauchrahmen 1px
   `var(--color-primary-element)`.

**Warum das helle Paar und nicht der starke Akzent.** Ein aktiver Chip ist ein
**Zustand**, keine Handlungsaufforderung. Der starke `--color-primary-element`
bleibt dem einen Knopf vorbehalten, der die Seite vorantreibt; sonst haette eine
Seite mit drei aktiven Chips vier gleich laute Flaechen und der Nutzer keinen
Blickanker mehr. Das helle Paar ist vom Server auf Kontrast geprueft ausgeliefert
(in Phase 9 in allen drei Zweigen verifiziert) und ist in Nextcloud die uebliche
Auswahlfarbe. Flaechenanteil: ein Chip ist rund 90 mal 34 Pixel; selbst wenn alle
zehn Chips gleichzeitig aktiv waeren, bleibt der Akzentanteil der Seite deutlich
unter zehn Prozent, und der Regelfall sind null bis zwei aktive Chips.

**Farbe ist nie der einzige Traeger.** Jeder aktive Chip traegt zusaetzlich das
`close`-Symbol und `aria-current="true"`; der aktive Sortierlink traegt
`aria-current="true"` und Schriftgewicht 700. Ein Nutzer mit Farbenblindheit,
ein Nutzer im Modus "hoher Kontrast" und ein Screenreader erfahren den Zustand
alle drei ohne die Farbe (WCAG 1.4.1).

**Nicht Akzent:** die Zeilenbeschriftungen, die inaktiven Chips, die
Sortierlinks, der Zuruecksetzen-Link, die Zeile "Geaendert am ...", das Symbol des
Leerzustands.

---

## Der neue Block: Filterleiste

### Ort und Aufbau

Die Seite hat jetzt sechs Bloecke statt fuenf. Der neue steht zwischen Bannerzeile
und Trefferliste.

| # | Block | Sichtbar | Neu in 13 |
|---|-------|----------|-----------|
| 1 | Kopf mit `h1` und Suchformular | immer | Formular traegt die aktiven Filter als versteckte Felder |
| 2 | Bannerzeile (Fehler oder Hinweis) | bei Bedarf | unveraendert |
| **2b** | **Filterleiste** | **wenn ein Suchbegriff vorliegt** | **ganz neu** |
| 3 | Trefferliste | wenn es Treffer gibt | vierte Zeile je Treffer unter Datums-Sortierung |
| 4 | Leerzustand | wenn es keine Treffer gibt | vierte Variante |
| 5 | Paginierung | wenn eine Nachbarseite existiert | unveraendert |

**Die Filterleiste erscheint nur mit Suchbegriff.** Ohne Begriff gibt es keine
Menge, die man eingrenzen koennte; zehn Chips ueber einer Einladung waeren zehn
Schalter ohne Wirkung. Sie erscheint dagegen **auch dann**, wenn die Suche null
Treffer hatte oder ein Banner steht: genau dort braucht der Nutzer den Weg zurueck
aus seinem Filter.

### Anatomie, von oben nach unten

```
Dateityp      [PDF] [Dokumente] [Tabellen] [Praesentationen] [Bilder] [Text]
Zeitraum      [Heute] [Letzte 7 Tage] [Letzte 30 Tage] [Dieses Jahr]   Alle Filter zuruecksetzen
Sortieren nach   Relevanz   Zuletzt geaendert   Aelteste zuerst
```

Hinweis zu D-05: "neben den Typ-Chips" ist hier bewusst als "zusaetzlich zu den
Typ-Chips" gelesen, nicht als "in derselben Zeile". Die Zeitraum-Chips stehen als
eigene beschriftete Zeile unter der Dateityp-Zeile, weil beide Gruppen eine
sichtbare Zeilenbeschriftung als zugaenglichen Gruppennamen brauchen und eine
gemeinsame Zeile auf schmalen Breiten umbricht, ohne dass die Gruppengrenze
erkennbar bliebe.

| Teil | Auszeichnung | Regel |
|------|--------------|-------|
| Zeilenbeschriftung | `<span class="findling-filters__label" id="findling-filter-types">` usw., 13px/400, `--color-text-maxcontrast` | Sichtbar und zugleich der zugaengliche Name der Gruppe (`aria-labelledby`). Drei Beschriftungen, drei Gruppen |
| Gruppe | `<div role="group" aria-labelledby="...">` | Kein `<ul>`, weil die Chips keine Aufzaehlung sind, sondern ein Satz Schalter; kein `<nav>`, weil drei Navigationsbereiche auf einer Seite die Landmarkenliste unbrauchbar machen |
| Chip inaktiv | `<a class="findling-chip-link" href="...">Label</a>` | Ziel: dieselbe Suche **mit** dieser Gruppe zusaetzlich. Zugaenglicher Name ist der sichtbare Text |
| Chip aktiv | `<a class="findling-chip-link findling-chip-link--active" aria-current="true" aria-label="Filter PDF entfernen" href="...">Label + close-SVG</a>` | Ziel: dieselbe Suche **ohne** diese Gruppe. Der ganze Chip ist der Entfernen-Link, das x ist ein Symbol darin (`aria-hidden="true"`, `focusable="false"`), **kein zweiter Link** |
| Zuruecksetzen | `<a class="findling-filters__reset">Alle Filter zuruecksetzen</a>` | Steht als letztes Element der Zeitraum-Zeile, ab 640px per `margin-inline-start: auto` rechts. Erscheint **nur**, wenn mindestens ein Typ-, Zeitraum- oder Datumswert gesetzt ist (D-06) |
| Sortierlink | `<a class="findling-sort__link">`, aktiver zusaetzlich `--active` und `aria-current="true"` | Drei Links, immer alle drei, immer genau einer aktiv. Der aktive Link zeigt auf dieselbe Ansicht; das ist kein toter Link, sondern der Normalfall eines Segmentschalters |

**Kein Link im Link, kein zweiter Fokusstopp je Chip.** Ein aktiver Chip ist ein
Fokusstopp, nicht zwei. Deshalb traegt er den Entfernen-Sinn selbst, statt einen
eigenen x-Knopf zu verschachteln (das waere ungueltiges HTML und ein zweiter Tabstopp
je aktivem Filter).

**Warum `aria-current` und nicht `aria-pressed`.** `aria-pressed` gehoert zu
`role="button"`; ein `<a>` mit `href` ist ein Link, und ein gedrueckter Link ist
nichts. `aria-current="true"` ist die Auszeichnung fuer "dieses Element der Gruppe
ist gerade das geltende" und wird von Screenreadern als "aktuell" angesagt.

### Zehn Chips und ihr Wortschatz

Die sechs Typgruppen sind eine geschlossene Liste in dieser Reihenfolge; sie ist
die Reihenfolge aus ROADMAP-Erfolgskriterium 1 und aus FILT-01, damit Roadmap,
Requirement und Oberflaeche dieselbe Folge nennen.

| Pos | Wire-Name (URL) | Label EN | Endungen (Quelle: 13-RESEARCH Befund 4) |
|-----|-----------------|----------|------------------------------------------|
| 1 | `pdf` | PDF | pdf |
| 2 | `documents` | Documents | docx, odt, rtf |
| 3 | `spreadsheets` | Spreadsheets | xlsx, ods, csv |
| 4 | `presentations` | Presentations | pptx, odp |
| 5 | `images` | Images | jpg, jpeg, jps, mpo, png, tif, tiff, webp |
| 6 | `text` | Text | txt, text, md, markdown, mdown, mdwn, mkd, htm, html, json, xml, yaml, yml, conf, cnf, eml, adoc, asciidoc, org, fb2, js |

Die Endungsspalte steht hier nur zur Nachvollziehbarkeit. **Sie lebt im Backend**
(`query/rewrite.py::TYPE_GROUPS`) und nirgends sonst; eine zweite Abbildung in
PHP waere das zweite Filtervokabular, das 13-RESEARCH ausdruecklich verbietet. Die
Oberflaeche kennt sechs Woerter und keine einzige Dateiendung.

Die vier Zeitraum-Chips sind **Kalenderfenster** und keine rollierenden Fenster
(Entscheid zu A5 aus 13-RESEARCH Befund 10; "Heute" und "Dieses Jahr" sind ohnehin
Kalenderbegriffe, und zwei Modelle nebeneinander auf einer Leiste kann niemand
erklaeren). Alle vier setzen nur `since`, nie `until`.

| Wire-Name | Label EN | Untergrenze, in der Zeitzone des Nutzers (`OCP\IDateTimeZone`) |
|-----------|----------|----------------------------------------------------------------|
| `today` | Today | heute 00:00 |
| `week` | Last 7 days | vor 6 Tagen 00:00 (sieben Kalendertage einschliesslich heute) |
| `month` | Last 30 days | vor 29 Tagen 00:00 (dreissig Kalendertage einschliesslich heute) |
| `year` | This year | 1. Januar dieses Jahres 00:00 |

**Genau ein Zeitraum-Chip kann aktiv sein.** Zwei Zeitraeume gleichzeitig ergeben
entweder den groesseren (dann ist der kleinere wirkungslos) oder eine leere Menge
(dann ist die Seite unerklaerlich). Ein Klick auf einen anderen Zeitraum-Chip
ersetzt den bisherigen; ein Klick auf den aktiven entfernt ihn. Die Typ-Chips sind
davon unberuehrt mehrfach waehlbar (D-01).

**Keine Trefferzaehler je Chip, in keiner Form.** Nicht als Zahl, nicht als Punkt,
nicht als Ausgrauen eines Chips ohne Treffer. Jede dieser drei Formen waere
dieselbe Auskunft, und sie waere ein Zaehl-Orakel vor dem Rechtefilter (T-02-93).
Ein Chip, hinter dem null Treffer stecken, sieht deshalb aus wie jeder andere und
fuehrt auf den Leerzustand.

---

## URL-Vertrag (FILT-04)

Fortschreibung der Tabelle aus 09-UI-SPEC. `query`, `names`, `page` und `cursors`
bleiben unveraendert.

| Parameter | Form | Bedeutung | Pruefung |
|-----------|------|-----------|----------|
| `types` | Kommaliste aus der geschlossenen Sechser-Menge, hoechstens sechs Eintraege, z.B. `pdf,images` | Die aktiven Typgruppen | Kleinschreiben, gegen die geschlossene Liste pruefen, Unbekanntes **still** weglassen, Dubletten entfernen, in der Reihenfolge der Tabelle oben kanonisieren. Leere Liste = kein Typfilter |
| `sort` | `relevance`, `newest` oder `oldest` | Die Reihenfolge. `relevance` ist Standard und wird **nicht** in die Adresse geschrieben | Alles andere gilt still als `relevance` |
| `range` | `today`, `week`, `month` oder `year` | Der Schnellbereich. Der Server rechnet daraus bei jedem Aufruf neu ein `since` | Alles andere gilt still als nicht gesetzt |
| `since`, `until` | Ganzzahl, Unix-Epoche in Sekunden, `>= 0`, mit Obergrenze | Frei gesetzte Grenzen, auch aus dem Unified-Search-Dialog (FILT-03) | Nichtzahl oder ausserhalb der Grenzen gilt still als nicht gesetzt |
| `fp` | acht Hexzeichen | Der Fingerabdruck des Anfragezustands, an den der Cursorpfad gebunden ist | Abweichung heisst Seite 1, still (13-RESEARCH Befund 7) |

**Zusammenspiel von `range` und `since`/`until`.** Beide wirken unabhaengig (D-05)
und beide grenzen **ein**, nie aus. Sind beide gesetzt, gilt die engere Grenze:
`since` wirksam = Maximum aus der Schnellbereichsgrenze und dem rohen `since`,
`until` wirksam = das rohe `until`. Damit ist die Semantik im Backend eindeutig,
und ein von Hand zusammengesetzter Link kann den Zeitraum nie versehentlich
aufweiten. Der Zeitraum-Chip gilt als aktiv, wenn `range` seinen Namen traegt; ein
reines `since` aus dem Dialog aktiviert keinen Chip, loest aber den
Zuruecksetzen-Link aus (es ist ein sichtbarer, entfernbarer Filter im Sinne von
FILT-04, siehe naechster Abschnitt).

**Jeder Chip-, Sortier- und Zuruecksetzen-Link traegt niemals `page`, `cursors`
oder `fp`.** Sie entstehen aus einem eigenen Bauteil neben `pageUrl()` (in
13-RESEARCH als `filterUrl()` vorgeschlagen), das gar keinen Cursor schreiben
kann. Zwei Bauteile statt eines Schalters, weil ein Schalter beim naechsten Umbau
falsch gesetzt wird.

**Das Suchformular traegt die aktiven Filter als versteckte Felder** (`types`,
`sort`, `range`, `since`, `until`) und weiterhin **kein** `page`, `cursors`, `fp`.
Wer den Suchbegriff praezisiert, verliert damit seine Eingrenzung nicht, landet
aber wie bisher auf Seite 1. Ein leerer Wert wird nicht als leeres Feld
mitgeschickt, sondern gar nicht gerendert, damit die Adresse nach dem Absenden so
kurz bleibt wie die Auswahl.

**Sichtbar und entfernbar (FILT-04) heisst hier konkret:** jeder wirksame Filter
ist entweder als hervorgehobener Chip sichtbar (Typ, Schnellbereich) oder er loest
mindestens den Zuruecksetzen-Link aus (frei gesetztes `since`/`until` aus dem
Dialog). Es gibt keinen Zustand, in dem die Seite weniger zeigt, als sie sucht.

---

## Trefferzeile unter Sortierung (D-04)

```
[Dateityp-Symbol 32px]  Rechtsmittelbelehrung.pdf                      <- 15px / 700
                        Freigaben/Recht/2026                           <- 13px / 400, maxcontrast
                        Geaendert am 14. September 2026                <- 13px / 400, maxcontrast  (NUR unter sort=newest|oldest)
                        ... die Rechtsmittelbelehrung ist beigefuegt ...<- 15px / 400, mark
```

| Gegenstand | Festlegung |
|------------|------------|
| Wann sichtbar | **Nur** bei `sort=newest` oder `sort=oldest`. Unter `relevance` existiert die Zeile nicht, weder leer noch versteckt (D-04) |
| Woher der Wert | `$node->getMTime()` am bereits **bestaetigten** Knoten, ueber ein fuenftes Feld in `ApprovedHit`. Nie aus der Container-Antwort (13-RESEARCH Befund 8) |
| Formatierung | `OCP\IDateTimeFormatter::formatDate($ts, 'long', $timeZone, $l)`. Kein eigenes Datumsformat, kein Formatstring im Katalog |
| Einbettung | Katalogschluessel `Modified on %s`. Der Platzhalter nimmt das fertig formatierte Datum |
| Stelle | Eigene Zeile unter dem Pfad, ueber dem Auszug. Nicht an den Pfad angehaengt: der Pfad ist einzeilig mit Ellipse, ein Anhaengsel waere das Erste, was abgeschnitten wird |
| Klasse | `.findling-hit__modified`, 13px/400, `--color-text-maxcontrast`, `white-space: nowrap` |
| Kein Relevanzwert | Unter Sortierung ist `Candidate.score` 0.0, und die Seite zeigt ohnehin nie einen Score. Es gibt keinen Zustand, in dem ein Zeitstempel als Relevanz erscheinen koennte |

**Der zugaengliche Name der Zeile aendert sich mit.** Die Trefferzeile traegt ein
`aria-label`, und ein `aria-label` **ersetzt** den Inhalt fuer den Screenreader:
ohne Anpassung waere das Datum fuer einen blinden Nutzer genau unter der
Datums-Sortierung unhoerbar. Deshalb gibt es eine zweite, datierte Fassung des
Namens (`%1$s in %2$s, modified on %3$s`), die genau dann verwendet wird, wenn die
Zeile sichtbar ist. Das ist der einzige Grund fuer den 20. neuen Katalogschluessel,
und er ist ein guter.

---

## Zustands-Inventar (Ergaenzungen)

Die neun Faelle aus 09-UI-SPEC gelten unveraendert. Diese kommen hinzu.

| Fall | Ausloeser | Darstellung |
|------|-----------|-------------|
| Kein Filter, keine Sortierung | Standardaufruf mit Begriff | Zehn Chips inaktiv, "Relevanz" aktiv, kein Zuruecksetzen-Link, keine Datumszeile |
| Filter aktiv, Treffer vorhanden | mindestens ein Chip aktiv | Chips hervorgehoben mit x, Zuruecksetzen-Link sichtbar, Liste wie gewohnt |
| Sortierung aktiv | `sort=newest|oldest` | Sortierlink hervorgehoben (700 + `aria-current`), jede Trefferzeile mit Datumszeile |
| **Filter aktiv, null Treffer** | Liste leer, Backend hat geantwortet, mindestens ein Filter wirkt | Vierte Variante des Leerzustands: `file-search-outline`, Ueberschrift "Keine Treffer mit den aktiven Filtern", Satz "Entfernen Sie einen Filter oder erweitern Sie den Zeitraum.", darunter der Link "Filter zuruecksetzen" auf dieselbe Suche ohne jeden Filter (D-07) |
| Filter aktiv, null Treffer, Banner steht | zusaetzlich `$hasError` oder `$hasHint` | Der Leerzustand schweigt, wie alle Varianten mit Begriff. Die neue Variante ist ein **Zweig innerhalb** des bestehenden `$showEmpty`-Blocks und kein Block daneben (Pitfall F, Gate `test_the_empty_state_of_the_page_does_not_speak_over_a_banner`). Die Filterleiste bleibt trotzdem stehen, damit der Weg zurueck sichtbar ist |
| Filter aktiv, null Treffer, alle Kandidaten verworfen | `$allRejected` **und** ein Filter wirkt | **Die Filter-Variante gewinnt.** Begruendung: beide Saetze sind wahr, aber nur einer nennt einen Hebel, den der Nutzer in der Hand haelt. "Andere Dateien enthalten dieses Wort, aber keine, die Sie oeffnen duerfen" hat keinen naechsten Schritt; "Entfernen Sie einen Filter" hat einen, und er ist ein Klick weit und umkehrbar. Ohne aktiven Filter bleibt die `$allRejected`-Variante unveraendert die aus V-1a |
| Unbekannter Typ-, Sortier- oder Zeitraumwert in der Adresse | von Hand verfaelscht | Stiller Rueckfall auf "nicht gesetzt" beziehungsweise `relevance`, keine Fehlermeldung, keine Aussage ueber die Adresszeile (Hausregel `PageController`) |
| Fremder Cursorpfad unter Filter | `fp` passt nicht zum Zustand | Stille Rueckkehr auf Seite 1 derselben gefilterten Suche |
| Sortierung liefert systematisch nichts | grosser Fremdbestand, eigener Bestand alt | Der bestehende Leerzustand greift unveraendert; die Seite sagt kein Wort ueber Rechte und keine Zahl (Pitfall G) |

---

## Copywriting Contract

23 neue Schluessel. Quell-Strings englisch, durch `$l->t()`. Die deutsche Spalte ist
woertlich der Inhalt von `de.json`, `de.js`, `de_DE.json` und `de_DE.js` (textgleiche
Zwillinge, Gate `test_the_german_catalogue_covers_both_german_language_codes`), die
franzoesische der von `fr.json` und `fr.js`. **Diese Tabelle traegt echte Umlaute und
Akzente**, weil sie Kataloginhalt ist und kopiert wird. Kein Gedankenstrich, kein
Emoji, kein Backtick.

| # | Element | EN (Quelle) | DE | FR |
|---|---------|-------------|----|----|
| 1 | Zeilenbeschriftung Typ | `File type` | Dateityp | Type de fichier |
| 2 | Typ-Chip 1 | `PDF` | PDF | PDF |
| 3 | Typ-Chip 2 | `Documents` | Dokumente | Documents |
| 4 | Typ-Chip 3 | `Spreadsheets` | Tabellen | Feuilles de calcul |
| 5 | Typ-Chip 4 | `Presentations` | Präsentationen | Présentations |
| 6 | Typ-Chip 5 | `Images` | Bilder | Images |
| 7 | Typ-Chip 6 | `Text` | Text | Texte |
| 8 | Zeilenbeschriftung Zeitraum | `Time range` | Zeitraum | Période |
| 9 | Zeitraum-Chip 1 | `Today` | Heute | Aujourd'hui |
| 10 | Zeitraum-Chip 2 | `Last 7 days` | Letzte 7 Tage | 7 derniers jours |
| 11 | Zeitraum-Chip 3 | `Last 30 days` | Letzte 30 Tage | 30 derniers jours |
| 12 | Zeitraum-Chip 4 | `This year` | Dieses Jahr | Cette année |
| 13 | x am aktiven Chip (Accessible Name) | `Remove filter %s` | Filter %s entfernen | Retirer le filtre %s |
| 14 | Zuruecksetzen in der Leiste | `Reset all filters` | Alle Filter zurücksetzen | Réinitialiser tous les filtres |
| 15 | Zeilenbeschriftung Sortierung | `Sort by` | Sortieren nach | Trier par |
| 16 | Sortierlink 1 (Standard) | `Relevance` | Relevanz | Pertinence |
| 17 | Sortierlink 2 | `Last modified` | Zuletzt geändert | Dernière modification |
| 18 | Sortierlink 3 | `Oldest first` | Älteste zuerst | Les plus anciens d'abord |
| 19 | Datumszeile im Treffer | `Modified on %s` | Geändert am %s | Modifié le %s |
| 20 | Trefferzeile mit Datum (Accessible Name) | `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %1$s dans %2$s, modifié le %3$s |
| 21 | Leerzustand unter Filter, Ueberschrift | `No results with the active filters` | Keine Treffer mit den aktiven Filtern | Aucun résultat avec les filtres actifs |
| 22 | Leerzustand unter Filter, Text | `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | Retirez un filtre ou élargissez la période. |
| 23 | Leerzustand unter Filter, Link | `Reset filters` | Filter zurücksetzen | Réinitialiser les filtres |

### Vertragspflichten, die aus dieser Tabelle folgen

| Pflicht | Wert |
|---------|------|
| Primary CTA dieser Phase | Unveraendert `Search` / "Suchen". **Phase 13 fuehrt keinen neuen Primaerknopf ein**; jede neue Bedienung ist ein Link |
| Empty state heading (neu) | "Keine Treffer mit den aktiven Filtern" |
| Empty state body (neu) | "Entfernen Sie einen Filter oder erweitern Sie den Zeitraum." plus der Link "Filter zuruecksetzen" als konkreter naechster Schritt |
| Error state | Unveraendert die drei Bloecke aus Phase 9. Phase 13 fuegt **keinen** neuen Fehlerzustand hinzu: ein unbekannter Wert in der Adresse ist kein Fehler, sondern ein stiller Rueckfall |
| Destructive confirmation | Nicht anwendbar. Keine zerstoererische Aktion in dieser Phase |

### Regeln ueber den Wortlaut hinaus (Fortschreibung)

- **Kein Satz nennt Berechtigungen, keine Zahl erlaubt einen Rueckschluss.** Gilt
  fuer die neuen Saetze genauso. Insbesondere sagt der Filter-Leerzustand nie, wie
  viele Treffer ein anderer Filter haette.
- **Keine Zahl neben einem Chip.** Siehe Zaehl-Orakel.
- **"Zuruecksetzen" ist nie "Loeschen".** Die Copy nennt das Entfernen eines
  Filters nie mit einem Wort aus dem Feld des Loeschens, weil nichts geloescht wird.
- **Die Kalenderbedeutung steht in der Beschriftung, nicht in einem Tooltip.**
  "Letzte 7 Tage" ist die ganze Erklaerung; ein `title`-Attribut als einziger
  Traeger einer Bedeutung ist verboten (Fortschreibung aus Phase 9).

### Katalog-Gates: was dieser Vertrag ausloest

| Gate | Heute | Nach Phase 13 |
|------|-------|---------------|
| Schluesselzahl in `test_admin_ui_contract.py` | 174 | **197**, mit einem neuen Absatz im Docstring, der die Erhoehung begruendet (23 Schluessel: 10 Chips, 3 Zeilenbeschriftungen, 3 Sortierlinks, 2 Zuruecksetzen-Varianten, 2 Datumsformen, 3 Leerzustand). Die bestehende Begruendung fuer 173 auf 174 bleibt stehen |
| `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` | 2 Eintraege | **5**: neu `PDF` (Eigenname der Dateiart, in allen drei Sprachen dasselbe Kuerzel), `Documents` und `Images` (im Franzoesischen wortgleich mit dem englischen Quellwort; eine kuenstliche Abweichung waere eine falsche Uebersetzung) |
| `docs/l10n-french.md` | zaehlt gegen 174 | zieht auf 197 nach und nennt die drei neuen Ausnahmen mit ihrer Begruendung |
| Platzhalter-Paritaet | gruen | Schluessel 13 und 19 tragen je genau ein `%s` in allen drei Sprachen, Schluessel 20 genau `%1$s`, `%2$s`, `%3$s` |
| Prosa-Gate (Gedankenstrich, Emoji) | gruen | Keiner der 23 Werte traegt einen Gedankenstrich oder ein Emoji |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | keine | not applicable. shadcn ist nicht initialisiert und kann es in diesem Stack nicht werden: kein `components.json`, keine `package.json`, kein Build-Schritt (geprueft 16.09.2026 am Repositoriumswurzelverzeichnis) |
| Drittanbieter-Registries | keine | **Keine deklariert.** Der Vetting-Gate (`shadcn view` plus Durchsicht) entfaellt mangels Gegenstand |
| Material Design Icons (Pictogrammers), Apache-2.0 | **kein neues Symbol.** Phase 13 verwendet ausschliesslich `close`, seit Phase 4 gepinnt, in `THIRD-PARTY.md` gelistet und in `php/templates/admin.php` bereits gerendert | Keine neue Zeile in `THIRD-PARTY.md`, kein neuer Eintrag in der Pruefschleife: die Namensliste des Pruefbefehls bleibt bei zwoelf. **Eine Textstelle zieht nach**: die Spalte "Where it lands" sagt heute, `search.php` trage sechs Symbole; es werden sieben. Die Aenderung gehoert in den Plan, der den Chip zuerst rendert |
| Nextcloud-Server | Dateityp-Symbole, Datumsformatierung (`IDateTimeFormatter`), Zeitzone (`IDateTimeZone`) | Kein Fremdmaterial. Alle drei sind oeffentliche APIs im Fenster 33 bis 35 (13-RESEARCH Befund 8 und 10) |

### SVG-Pfaddaten (woertlich, `viewBox="0 0 24 24"`, gepinnter Commit `9e04201d4557e729822fb57f62a316c3dea1d4a8`)

```
close   M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z
```

Das Zeichen steht im aktiven Chip, 16 mal 16, `fill: currentColor`,
`aria-hidden="true"`, `focusable="false"`. Wie in `admin.php` wird der Pfad oben im
Template einer Variablen zugewiesen und nicht dreimal abgeschrieben.

---

## Barrierefreiheit (Ergaenzungen)

Die Tabelle aus 09-UI-SPEC gilt unveraendert. Diese Punkte kommen hinzu.

| Anforderung | Umsetzung |
|-------------|-----------|
| Zustand nie allein ueber Farbe | Aktiver Chip: Flaeche **plus** `close`-Symbol **plus** `aria-current="true"`. Aktiver Sortierlink: Gewicht 700 **plus** `aria-current="true"` |
| Gruppenbenennung | Drei `role="group"` mit `aria-labelledby` auf die sichtbare Zeilenbeschriftung. Eine unsichtbare Beschriftung waere eine zweite Wahrheit; hier ist die sichtbare auch die vorgelesene |
| Label in Name (WCAG 2.5.3) | Der zugaengliche Name eines aktiven Chips ("Filter PDF entfernen") **enthaelt** seinen sichtbaren Text ("PDF"). Ein Spracheingabe-Nutzer, der "PDF" sagt, trifft den Chip |
| Ein Fokusstopp je Chip | Der aktive Chip ist ein Link, nicht Link plus Knopf. Kein Link im Link |
| Klickflaechen | Jeder Chip, jeder Sortierlink und der Zuruecksetzen-Link mindestens 34px hoch, unter `pointer: coarse` 44px |
| Tastatur | Alles sind native Links in Dokumentreihenfolge: Formular, Typ-Chips, Zeitraum-Chips, Zuruecksetzen, Sortierlinks, Trefferliste, Pager. Kein `tabindex`, kein Tastaturfang, kein eigener Shortcut |
| Fokusring | Unangetastet. Kein `outline: none` in den neuen Regeln (bestehendes Gate) |
| Live-Bereiche | Weiterhin **keine**. Jeder Chipklick ist eine vollstaendige Navigation; es aendert sich nichts unter dem Nutzer |
| Ueberschriftenhierarchie | Unveraendert genau eine `h1`. Die Zeilenbeschriftungen der Filterleiste sind `span`, keine Ueberschriften |
| Datum fuer Screenreader | Unter Sortierung traegt der zugaengliche Name der Trefferzeile das Datum mit (Schluessel 20), weil `aria-label` den Inhalt ersetzt |
| Dark Mode und hoher Kontrast | Automatisch, weil nur Variablen und nur geprueft ausgelieferte Farbpaare verwendet werden. Sichtprobe in Hell, Dunkel und hohem Kontrast gehoert zur Abnahme |

---

## Responsive

| Breite | Verhalten der neuen Teile |
|--------|---------------------------|
| ab 1024px | Filterleiste in der 900px-Lesespalte, drei Zeilen, Beschriftung links, Chips daneben, Zuruecksetzen-Link am rechten Rand der Zeitraum-Zeile |
| unter 1024px | unveraendert, nur die Seitenraender halbieren sich wie bisher |
| unter 640px | Die Zeilenbeschriftung rutscht ueber ihre Chip-Gruppe, die Chips umbrechen (`flex-wrap: wrap`), der Zuruecksetzen-Link steht in eigener Zeile linksbuendig, die drei Sortierlinks umbrechen bei Bedarf. **Kein waagerechtes Scrollen, keine abgeschnittene Chip-Reihe, kein Karussell** |
| `pointer: coarse` | Chips und Sortierlinks mindestens 44px hoch |

Die Chips bekommen bewusst **keine** waagerecht scrollende Leiste: eine Reihe, aus
der ein Teil der Auswahl herausgeschoben ist, versteckt Bedienung hinter einer
Geste, und auf der Tastatur ist sie gar nicht auffindbar. Zehn kurze Woerter
umbrechen stattdessen.

---

## Verbote (Fortschreibung)

Die Verbotsliste aus 09-UI-SPEC gilt vollstaendig weiter. Mit **[G]** markierte
Punkte sind als Text pruefbar und gehoeren in ein Gate nach dem Muster von
`backend/tests/test_admin_ui_contract.py`.

- **[G]** Kein JavaScript fuer Filter oder Sortierung. `php/js/search.js` bekommt
  keinen Zuhoerer, keinen Selektor und keine Zeile fuer Chips oder Sortierung; sein
  einziger Zweck bleibt die Rueckkehr-Markierung (D-02, D-03, D-05).
- **[G]** Kein `<select>`, kein `<option>` und kein zweites `<form>` in der
  Filterleiste. Die Typwahl ist eine Chip-Leiste aus Links und kein Formular (D-02).
- **[G]** Keine neue Route und kein JSON-Kanal fuer Chips
  (`test_php_trust_boundary.py` zaehlt Route-Attribute).
- **[G]** Kein Hexwert, keine Farbfunktion in den neuen CSS-Regeln, kein
  `outline: none`, kein Inline-Skript, kein `style`-Attribut.
- **[G]** Kein Gedankenstrich und kein Emoji in den 23 neuen Katalogwerten.
- **[G]** Kein `aria-pressed` an einem `<a>`.
- Keine Trefferzahl, kein Punkt, kein Ausgrauen und keine sonstige Auskunft
  darueber, was hinter einem Chip liegt, bevor er geklickt wurde.
- Kein Chip-Zustand ohne zweiten, farbunabhaengigen Traeger.
- Kein `page`, kein `cursors`, kein `fp` in einem Chip-, Sortier- oder
  Zuruecksetzen-Link.
- Keine Datumszeile unter Relevanz-Sortierung, in keiner Form, auch nicht
  versteckt.
- Kein zweites Typvokabular in PHP. Die Seite kennt sechs Gruppennamen und keine
  Dateiendung.
- Kein freies Datumsfeld, kein Datumswaehler, kein Kalender-Popup in dieser Phase
  (vertagt, siehe 13-CONTEXT Deferred).
- Kein Ausblenden eines Chips, weil er gerade nicht passt. Alle sechs Typgruppen
  und alle vier Zeitraeume sind immer sichtbar (D-02).
- Kein Toast, keine Snackbar, kein Ladezustand beim Filterwechsel. Ein Chipklick
  ist eine gewoehnliche Navigation.

---

## Grenzen zu anderen Vertraegen

Diese Punkte liegen ausserhalb der Gestaltung, haengen aber an ihr und gehoeren in
die Planung.

| Punkt | Befund | Was daraus folgt |
|-------|--------|------------------|
| Bauordnung | `extra="forbid"` macht ein unbekanntes Feld zu HTTP 422 und damit zur stummen Suche | Backend-Felder **vor** jeder Zeile Oberflaeche. Dieser Vertrag beschreibt das Ziel, nicht die Reihenfolge |
| Ein Filtervokabular | `TYPE_GROUPS` lebt im Backend | Die Oberflaeche schickt Gruppennamen, nie Endungen. Ein Plan, der eine Endung in PHP schreibt, verletzt diesen Vertrag |
| Rechtegrenze | `SearchService::run()` mit `getFirstNodeById()` und `isReadable()` bleibt die einzige Stelle | Die Filterleiste ist reine Anzeige. Kein Filter wird in PHP hinter dem Recheck angewendet (sonst halbe Seiten und eine zweite Sicherheitsflaeche) |
| Datum im Treffer | `ApprovedHit` bekommt ein fuenftes Feld aus dem bestaetigten Knoten | Keine Protokollaenderung, kein `mtime` durch `filterCandidates()` |
| Cursorbindung | `cursorPath()` prueft Form, nicht Herkunft | Der Fingerabdruck `fp` ist Teil des Adressvertrags und damit Teil dieses Dokuments; er ist **kein** Sicherheitsmerkmal und wird genau so kommentiert |
| Dialog-Filter | `getSupportedFilters()` meldet kuenftig `since`/`until` | Im Dialog aendert sich **nichts an der Gestaltung**: keine eigenen Chips, kein `getCustomFilters()`. Typ und Sortierung gibt es in v1.2 nur auf der eigenen Seite |
| Attribution | `THIRD-PARTY.md` sagt "search.php carries six" | Zeile auf sieben aendern, im Plan, der den Chip rendert |

---

## Abnahme-Sichtproben

Gegen `docs/dev-setup.md` (Port 8090, `testuser`/`kollegin`, Testkorpus).

1. Suche mit Treffern verschiedener Typen: zehn Chips und drei Sortierlinks stehen
   ueber der Liste, alle Chips inaktiv, "Relevanz" hervorgehoben, kein
   Zuruecksetzen-Link.
2. Klick auf "PDF": nur PDF-Treffer, der Chip hervorgehoben mit x, der
   Zuruecksetzen-Link erscheint, die Seite steht auf 1, die Adresse traegt
   `types=pdf` und weder `page` noch `cursors`.
3. Zusaetzlich "Bilder" klicken: beide Chips aktiv, Adresse `types=pdf,images`,
   Treffer beider Gruppen. Erneuter Klick auf "PDF" entfernt nur PDF.
4. Paraphrasensuche unter aktivem Typfilter: dasselbe Dokument wie ohne Filter
   wird gefunden (Erfolgskriterium 1), und die Seite ist voll besetzt statt
   halbleer.
5. Auf Seite 3 blaettern, dann einen Chip klicken: Seite 1 der neuen Auswahl, keine
   Dublette, keine Luecke.
6. `cursors` von Hand aus einer ungefilterten Suche in eine gefilterte Adresse
   kopieren: Seite 1, keine Fehlermeldung, keine Ausnahme im Log.
7. "Zuletzt geaendert" waehlen: jede Trefferzeile traegt "Geaendert am ...", die
   Reihenfolge faellt, kein Zahlenwert erscheint sonst irgendwo. Zurueck auf
   "Relevanz": die Datumszeile ist weg.
8. "Aelteste zuerst": dieselbe Menge, umgekehrte Folge.
9. "Dieses Jahr" waehlen, dann "Heute": nur ein Zeitraum-Chip ist aktiv. Um
   Mitternacht Ortszeit geprueft, dass "Heute" die Datei der letzten Stunde
   enthaelt (Zeitzonenfalle, Befund 10).
10. Filter setzen, der nichts trifft: Leerzustand "Keine Treffer mit den aktiven
    Filtern" mit Satz und Link; der Link fuehrt auf dieselbe Suche ohne Filter und
    liefert wieder Treffer.
11. Backend stoppen, dann filtern: der Fehlerblock steht, der Filter-Leerzustand
    schweigt, die Filterleiste bleibt bedienbar.
12. Mit abgeschaltetem JavaScript: alle zehn Chips, alle drei Sortierlinks und der
    Zuruecksetzen-Link funktionieren vollstaendig.
13. Tastatur allein: Chips und Sortierlinks in Dokumentreihenfolge erreichbar,
    Fokusring ueberall sichtbar, ein Stopp je Chip.
14. Screenreader ueber die Leiste: "Dateityp, Gruppe", je Chip der Name, beim
    aktiven zusaetzlich "aktuell" und "Filter PDF entfernen"; unter Sortierung
    nennt die Trefferzeile das Datum.
15. Dunkles Theme und hoher Kontrast: aktiver Chip ohne Farbe erkennbar (x und
    Rahmen), kein Text unter 4.5:1.
16. Handybreite unter 640px: Chips umbrechen, kein waagerechtes Scrollen, Chips
    mindestens 44px hoch.
17. Seite auf Englisch, Deutsch und Franzoesisch: keine unuebersetzte Zeichenkette,
    keine abgeschnittene Chip-Beschriftung, "Feuilles de calcul" bricht die Leiste
    nicht.

---

## Herkunft der Festlegungen

| Quelle | Uebernommene Entscheidungen |
|--------|-----------------------------|
| 13-CONTEXT.md | D-01 bis D-07 vollstaendig und woertlich: Mehrfachauswahl (D-01), Chip-Leiste ohne JavaScript (D-02), drei Sortierlinks (D-03), Datum nur unter Datums-Sortierung (D-04), vier Schnellbereiche als Link-Chips (D-05), aktive Chips mit x plus Zuruecksetzen-Link (D-06), eigener Leerzustand unter Filter (D-07) |
| 13-CONTEXT "Claude's Discretion" | Hier entschieden: Chip-Reihenfolge (Roadmap-Folge), Wortlaute in drei Sprachen, Icon-Wahl (nur `close`, kein neues), Abstaende und Hervorhebungsstil (helles Akzentpaar plus x plus `aria-current`), URL-Namen (`types`, `sort`, `range`, `since`, `until`, `fp`), Kalenderfenster statt rollierender Fenster |
| 13-RESEARCH.md | Befund 4 (Gruppen zu Endungen, ein Vokabular), Befund 7 (`filterUrl()` ohne Cursor, Fingerabdruck), Befund 8 (`mtime` aus dem Knoten, `IDateTimeFormatter`), Befund 10 (Zeitzone der Schnellbereiche), Befund 11 (Katalog-Gates, `174`, franzoesische Gleichwortfalle, `aria-current` statt `aria-pressed`), Pitfall F (Leerzustand als Zweig, nicht als Block) |
| 09-UI-SPEC.md | Fortgeschrieben statt neu erfunden: Spacing-Skala samt 34/44-Ausnahmen, drei Groessen, zwei Gewichte, Farbrollen und Akzent-Reserveliste, Verbotsliste, Barrierefreiheits-Tabelle, Bauweise ohne Build-Schritt |
| ROADMAP.md Phase 13 | Erfolgskriterium 1 (sechs Gruppen, Reihenfolge), 2 (drei Sortiermodi, kein Zeitstempel als Relevanz), 3 (Dialog-Datumsfilter), 4 (sichtbar und entfernbar, Seite 1, fremder Cursorpfad) |
| REQUIREMENTS.md | FILT-01 bis FILT-05, Ausschluss der Facettenzaehler |
| `php/css/search.css`, `php/templates/search.php`, `php/css/admin.css` | Klassennamen-Muster, Chip-Optik der Verwaltungsseite, Symbolvariablen am Dateikopf, `p()` und `$l->t()` fuer jede Ausgabe |
| CLAUDE.md und globale Regeln | Keine Emojis, keine Gedankenstriche, echte Umlaute in Katalogen, ASCII in Bezeichnern und in dieser Prosa, Code englisch |

---

## Offene Punkte fuer die Planung

Keiner davon ist eine Gestaltungsfrage.

1. **Die 23 Katalogschluessel sind ein eigener Planschritt am Ende**, mit allen
   sechs Dateien, der Zahl 197, der Docstring-Begruendung, den drei neuen
   G2-Ausnahmen und `docs/l10n-french.md`. Als Anhaengsel an einen anderen Schritt
   wird es rot (Pitfall E).
2. **`THIRD-PARTY.md`**: eine Textstelle ("carries six") zieht auf sieben nach, in
   dem Plan, der den Chip zuerst rendert. Keine neue Zeile, keine neue Pruefzeile.
3. **Der Fingerabdruck `fp`** ist Teil des Adressvertrags und braucht seinen
   Kommentar ("Verwechslungssperre, kein Sicherheitsmerkmal") und seinen Testfall
   in `PageControllerTest`.
4. **`PageController` bekommt zwei neue Konstruktorabhaengigkeiten**
   (`IDateTimeZone`, `IDateTimeFormatter`) und damit `setUp()` zwei weitere Mocks.
5. **Rangfolge im Leerzustand**: dieser Vertrag entscheidet, dass die
   Filter-Variante die `$allRejected`-Variante verdraengt, solange ein Filter
   wirkt. Der Plan muss das als Zweig innerhalb von `$showEmpty` bauen und mit
   einem Testfall belegen.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
