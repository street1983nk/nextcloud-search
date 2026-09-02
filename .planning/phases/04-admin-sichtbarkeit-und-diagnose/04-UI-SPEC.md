---
phase: 4
slug: admin-sichtbarkeit-und-diagnose
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-02
---

# Phase 4: UI Design Contract

> Visueller und interaktiver Vertrag für die Admin-Sichtbarkeit. Erzeugt von gsd-ui-researcher, geprüft von gsd-ui-checker.
>
> Deutsche Prosa ist die Arbeitssprache dieses Dokuments. Alle Bezeichner, CSS-Klassen, IDs und Quell-Strings bleiben englisch, die deutschen Nutzertexte stehen in der Copy-Tabelle als Übersetzung.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (gesperrt durch 04-CONTEXT D-02: kein npm, kein Build-Step im Companion-Repo) |
| Preset | not applicable |
| Component library | none. Nextcloud-Server-CSS (`core/css/*`, `apps/settings/css/settings.scss`) plus eine eigene `css/admin.css` |
| Icon library | Material Design Icons (Pictogrammers), Apache-2.0, als **Inline-SVG** im PHP-Template. Kein Icon-Font, kein npm-Paket. Ausnahme: der Core-Spinner `icon-loading-small` |
| Font | `var(--font-face)` von Nextcloud (System-UI-Stack). Keine eigene Schrift, kein Webfont |

**Verifizierte Grundlage (Nextcloud `stable32`, geprüft am 02.09.2026):**

| Fakt | Quelle |
|------|--------|
| Alle Design-Token als CSS-Variablen (`--color-*`, `--default-font-size`, `--border-radius-*`, `--default-grid-baseline`) | `apps/theming/lib/Themes/DefaultTheme.php` |
| `.section` = `padding: 30px`, Trennlinie `border-bottom: 1px solid var(--color-border)` | `core/css/server.scss`, `apps/settings/css/settings.scss` |
| `.section h2` = `20px`, `bold`, `max-width: 900px` | `apps/settings/css/settings.scss` |
| `.settings-hint` = `color: var(--color-text-maxcontrast)` | `apps/settings/css/settings.scss` |
| Alle Überschriften sind global auf `font-size: 100%; font-weight: inherit` zurückgesetzt | `core/css/styles.scss` |
| `<progress>` = 5px hoch, Spur `--color-background-dark`, Füllung `--color-primary-element` | `core/css/inputs.scss` |
| `input[type=checkbox].checkbox` + benachbartes `<label>` = 14px Box, funktioniert ohne Build | `core/css/inputs.scss` |
| `button` ohne `.button-vue` wird vom Core gestylt, `.primary` ist die Akzent-Variante | `core/css/inputs.scss` |
| Von den Legacy-Icon-Klassen existieren in NC 32 **nur noch** `icon-loading` / `icon-loading-small` | `core/css/icons.scss` |
| CSRF-Token liegt in `document.head.dataset.requesttoken` | `core/templates/layout.user.php` |
| Locale liegt in `document.documentElement.dataset.locale` (z. B. `de_DE`), Sprache in `.lang` | `core/templates/layout.user.php` |

**Bewusst nicht verwendet:**

| Verworfen | Grund |
|-----------|-------|
| `OC.dialogs.confirmDestructive()` | Seit NC 30.0.0 deprecated. Die App führt `max-version 35`, ein Wegfall innerhalb des Fensters ist realistisch. Ersatz: Inline-Bestätigung (siehe Interaktionen) |
| `OCP.InitialState.loadState()` | Seit NC 18.0.0 deprecated. Ersatz: serverseitig gerenderte Werte plus `fetch` auf die eigene JSON-Route |
| `OC.getCanonicalLocale()` / `OC.getLanguage()` | Deprecated. Ersatz: `document.documentElement.dataset.locale` |
| `icon-info`, `icon-error`, `icon-checkmark` | In NC 32 aus `core/css/icons.scss` entfernt. Ersatz: Inline-SVG |
| Inline-`<script>` im Template | Nextcloud-CSP blockt es. JS ausschließlich über `\OCP\Util::addScript('findling', 'admin')` |

**Attribution:** Die verwendeten MDI-Pfaddaten sind ein Drittanbieter-Asset. Ein Eintrag in `THIRD-PARTY.md` (Pictogrammers Material Design Icons, Apache-2.0) gehört zur Lieferung dieser Phase.

---

## Spacing Scale

Basis ist `var(--default-grid-baseline)` = 4px. Eigene Abstände werden als `calc(var(--default-grid-baseline) * n)` geschrieben, nie als lose px-Zahl.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Abstand Icon zu Label im Zustands-Chip, Innenabstand Chip vertikal |
| sm | 8px | Innenabstand Chip horizontal, Zellenabstand Tabelle vertikal, Höhe des Fortschrittsbalkens |
| md | 16px | Standardabstand zwischen Elementen, Innenabstand Metrik-Kachel, Zellenabstand Tabelle horizontal, Icon-Kantenlänge |
| lg | 24px | Abstand zwischen Blöcken innerhalb einer `.section`, Abstand Kopfzahl zu Balken |
| xl | 32px | Abstand über einer `h3`-Untergruppe |
| 2xl | 48px | nicht verwendet in dieser Phase |
| 3xl | 64px | nicht verwendet in dieser Phase |

**Exceptions (alle fremdbestimmt, nicht von uns gesetzt):**

| Wert | Woher | Umgang |
|------|-------|--------|
| 30px | `.section { padding: 30px }` im Core | Nicht überschreiben. Der Außenrahmen gehört den Verwaltungseinstellungen, nicht uns |
| 34px | `var(--default-clickable-area)` | Verbindliche Mindesthöhe jeder Klickfläche (Label eines Checkbox-Paars, Button, Aufklapp-Button einer Fehlergruppe) |
| 12px | `.settings-hint { margin-block: -12px 12px }` im Core | Nicht überschreiben |
| 3px | Core-Buttonmargin | Nicht überschreiben |
| 5px | Core-`<progress>`-Höhe | **Wird überschrieben** auf 8px (`#findling-coverage progress { height: calc(var(--default-grid-baseline) * 2) }`), damit die Kopfzahl der Seite einen sichtbaren Balken hat |

Inhaltsbreite: `max-width: 900px` in allen fünf Blöcken, deckungsgleich mit `max-width` von `.section h2` im Core.

---

## Typography

Nextcloud setzt alle Überschriften auf `font-size: 100%` zurück. Was nicht hier steht, existiert auf der Seite nicht.

| Role | Size | Weight | Line Height | Anwendung |
|------|------|--------|-------------|-----------|
| Body | 15px (`var(--default-font-size)`) | 400 | 1.5 (`var(--default-line-height)`) | Fließtext, Tabellenzellen, Labels, Buttons, Eingabefelder |
| Label | 13px (`var(--font-size-small)`) | 400 | 1.5 | Zustands-Chip, Metrik-Bezeichnung, Zeitstempel, `.settings-hint`, Tabellenkopf, Beispielpfade |
| Heading | 20px | 700 | 1.2 | `h2` der fünf Blöcke. Kommt aus dem Core, wird nicht selbst gesetzt |
| Display | 28px | 700 | 1.2 | Genau eine Stelle: die Deckungsgrad-Prozentzahl |

Zwei Schriftstärken, exakt: **400** (regular) und **700** (bold). 700 ist die Stärke, die der Core für `.section h2` verwendet, deshalb kein 600.

Vier Größen, exakt: **13, 15, 20, 28**. Es gibt keine fünfte. Braucht der Regeln-Block eine Untergruppe, ist das eine `h3` auf der **Body-Stufe in 700** (15px / 700 / 1.2), keine eigene Größe. Gewicht trägt die Hierarchie, nicht eine weitere Stufe.

Zahlen und Tausendertrennung: `new Intl.NumberFormat(locale)` mit `locale` aus `document.documentElement.dataset.locale.replace('_','-')`, Fallback `document.documentElement.lang`, Fallback `'en'`. Serverseitig dieselbe Darstellung über `IL10N`. Prozentwerte immer ganzzahlig, mit geschütztem Leerzeichen vor dem Prozentzeichen im deutschen Text.

---

## Color

Kein einziger Hexwert im eigenen CSS. Ausschließlich Nextcloud-Variablen, damit Dark Mode, Hoher Kontrast und Theming ohne Zutun funktionieren.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `var(--color-main-background)` | Seitengrund und Grund aller fünf `.section`-Blöcke |
| Secondary (30%) | `var(--color-background-hover)` | Metrik-Kacheln, Tabellenkopfzeile, Diagnose-Ergebniskarte, neutrale Zustands-Chips. Trennlinien: `var(--color-border)` |
| Accent (10%) | `var(--color-primary-element)` | siehe Reserveliste |
| Destructive | `var(--color-error)` Fläche, `var(--color-error-text)` Text, `var(--color-element-error)` Icon und Rand | Ausschließlich die Inline-Bestätigung "Indexierte Inhalte entfernen?" und ihr Bestätigungs-Button |

**Accent reserved for:** genau drei Dinge, nichts sonst.

1. Die gefüllte Strecke des Deckungsgrad-Fortschrittsbalkens (`<progress>`, Füllung kommt vom Core).
2. Der einzige `.primary`-Button der Seite: "Regeln speichern".
3. Der Fokusring von Eingabeelementen (kommt vom Core, wird nicht angefasst).

Nicht Akzent: Überschriften, Links im Block, Zustands-Icons, Zahlen, Kachelrahmen, der Diagnose-Button.

**Semantische Farben, getrennt vom Akzent-Budget.** Jede Farbe wird nur im Paar Fläche plus zugehörige Textfarbe verwendet, weil Nextcloud diese Paare auf Kontrast geprüft ausliefert.

| Bedeutung | Fläche | Text | Icon |
|-----------|--------|------|------|
| Erfolg (indexiert) | `--color-success` | `--color-success-text` | `--color-element-success` |
| Warnung (übersprungen, gekürzt, wenig Platz, Reindex nötig) | `--color-warning` | `--color-warning-text` | `--color-element-warning` |
| Fehler (fehlgeschlagen, Backend antwortet nicht) | `--color-error` | `--color-error-text` | `--color-element-error` |
| Neutral (ausgeschlossen, wartet, unbekannt) | `--color-background-hover` | `--color-main-text` | `--color-text-maxcontrast` |
| Hinweis (Schätzung, Erklärzeilen) | `--color-info` | `--color-info-text` | `--color-element-info` |

**Farbe ist nie der einzige Träger einer Information.** Jeder Zustand erscheint als Icon plus Textlabel plus Farbe. Ein Screenreader und ein Farbfehlsichtiger lesen dieselbe Aussage (WCAG 1.4.1).

---

## Copywriting Contract

Quell-Strings sind englisch und laufen durch `$l->t()`. Die deutsche Spalte ist der Inhalt von `l10n/de.json` und `l10n/de.js`. `de_DE` erbt über die Nextcloud-L10N-Fallbackkette, eine eigene Datei ist nicht nötig.

| Element | Copy |
|---------|------|
| Primary CTA | EN `Save rules` / DE `Regeln speichern` |
| Empty state heading | EN `No numbers yet` / DE `Noch keine Zahlen` |
| Empty state body | EN `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` / DE `Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen.` |
| Error state | EN `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` / DE `Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist.` |
| Destructive confirmation | `Ausschluss hinzufügen`: EN `Remove indexed content? Excluding %s also removes %n already indexed documents under that path from the index. The files themselves stay untouched on disk.` / DE `Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem %n bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte.` Buttons: EN `Exclude and remove` / `Keep files indexed`, DE `Ausschließen und entfernen` / `Dateien indexiert lassen` |

### Block-Überschriften und Kernzeilen

| Stelle | EN | DE |
|--------|----|----|
| Section-Name in der Verwaltungs-Navigation | `Findling` | `Findling` |
| h2 Block 1 | `Search coverage` | `Deckungsgrad der Suche` |
| Kopfzahl-Subline | `%1$s of %2$s indexable files are searchable` | `%1$s von %2$s indexierbaren Dateien sind durchsuchbar` |
| Statuszeile, Lauf aktiv | `Indexing, about %s left` | `Indexierung läuft, noch etwa %s` |
| Statuszeile, fertig | `Up to date, last checked %s` | `Aktuell, letzte Prüfung %s` |
| Statuszeile, stockt | `Indexing has not progressed for %s. Background jobs may not be running.` | `Die Indexierung kommt seit %s nicht voran. Möglicherweise laufen die Hintergrundaufträge nicht.` |
| Kachel-Bezeichnungen | `Indexed` / `Skipped` / `Failed` / `Excluded` | `Indexiert` / `Übersprungen` / `Fehlgeschlagen` / `Ausgeschlossen` |
| Hinweis unter den Kacheln | `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | `Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst.` |
| Banner wenig Platz | `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | `Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter.` |
| Banner Reindex nötig | `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | `Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer.` |
| h2 Block 2 | `Estimate for the first index` | `Schätzung für den Erstindex` |
| Schätzzeile | `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | `%1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index.` |
| Schätzung läuft noch | `Counting the files, this takes a moment.` | `Die Dateien werden gezählt, das dauert einen Moment.` |
| Schätz-Hinweis | `Findling does not wait for a confirmation. The first index has already started.` | `Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits.` |
| h2 Block 3 | `Files that were not indexed` | `Nicht indexierte Dateien` |
| Tabellenkopf | `Reason` / `Files` / `State` | `Grund` / `Dateien` / `Zustand` |
| Gruppe aufklappen | `Show example paths` | `Beispielpfade anzeigen` |
| Gruppe zuklappen | `Hide example paths` | `Beispielpfade verbergen` |
| Restzähler unter den Beispielen | `and %n more` | `und %n weitere` |
| Pfad nicht auflösbar | `File no longer exists (ID %s)` | `Datei existiert nicht mehr (ID %s)` |
| Leere Fehlerliste | `Every file was indexed. Nothing was skipped and nothing failed.` | `Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen.` |
| h2 Block 4 | `Look up one file` | `Einzelne Datei prüfen` |
| Feld-Label | `Path or file ID` | `Pfad oder Datei-ID` |
| Feld-Hilfe | `A path as Nextcloud stores it, or the numeric ID from the list above.` | `Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben.` |
| Diagnose-Button | `Look up file` | `Datei prüfen` |
| Diagnose-Fehlschlag | `No file at this path, and no file with this ID.` | `Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID.` |
| Diagnose, noch nicht gesehen | `Not seen yet. This file has not reached the queue. The next reconcile pass picks it up.` | `Noch nicht gesehen. Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab.` |
| Diagnose, Backend stumm | `The state of this file is unknown right now because the backend does not answer.` | `Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet.` |
| h2 Block 5 | `Rules and limits` | `Regeln und Grenzen` |
| Label Ausschlüsse | `Excluded folders` | `Ausgeschlossene Ordner` |
| Hilfe Ausschlüsse | `Prefix match on the path, no wildcards and no patterns. Example: alice/files/Backups` | `Präfix-Vergleich auf dem Pfad, keine Platzhalter und keine Muster. Beispiel: alice/files/Backups` |
| Hinzufügen-Button | `Add exclusion` | `Ausschluss hinzufügen` |
| Entfernen-Button je Zeile | `Remove exclusion %s` | `Ausschluss %s entfernen` |
| Leere Ausschlussliste | `No folder is excluded.` | `Kein Ordner ist ausgeschlossen.` |
| Label Größen-Cap | `Largest file to read` | `Größte zu lesende Datei` |
| Hilfe Größen-Cap | `Files above this size are recorded as skipped (too large) and never read.` | `Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen.` |
| Label Team Folders | `Index Team Folders` | `Team Folders indexieren` |
| Label External Storage | `Index external storage` | `Externen Speicher indexieren` |
| Hilfe External Storage | `External storage can be slow or charged per request. Indexing reads every file once.` | `Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal.` |
| Wirkungs-Hinweis | `The next run applies the new rules. Nothing restarts.` | `Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu.` |
| Speichern erfolgreich | `Rules saved. The next run applies them.` | `Regeln gespeichert. Der nächste Lauf übernimmt sie.` |
| Speichern fehlgeschlagen | `The rules were not saved. Nothing changed.` | `Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert.` |
| Validierung Größen-Cap | `Enter a size between 1 and 2048 MB.` | `Eine Größe zwischen 1 und 2048 MB eingeben.` |
| Validierung Ausschluss leer | `Enter a folder path.` | `Einen Ordnerpfad eingeben.` |
| Validierung Ausschluss doppelt | `This path is already excluded.` | `Dieser Pfad ist bereits ausgeschlossen.` |

### Grund-Taxonomie: Label und Abhilfe

Verbindliche Anzeigetexte für jeden Wert aus `FileStateService::REASONS`. Die Spalte "Abhilfe" ist die Umsetzung der Pitfalls-Lehre "mit der Angabe, welche Grenze das ändern würde". Wo es keine Abhilfe gibt, steht das ausdrücklich da statt gar nichts.

| Reason | Zustand | DE Label | DE Abhilfe |
|--------|---------|----------|------------|
| `truncated` | indexed | Text gekürzt | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. |
| `too_large` | skipped | Zu groß | Den Wert unter "Größte zu lesende Datei" erhöhen. |
| `mime_not_allowed` | skipped | Dateityp nicht unterstützt | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. |
| `encrypted` | skipped | Passwortgeschützt | Keine. Ohne Passwort ist der Inhalt nicht lesbar. |
| `no_text_layer` | skipped | Kein Text im Dokument | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. |
| `empty_text` | skipped | Kein Textinhalt | Keine. Die Datei ist lesbar, enthält aber keinen Text. |
| `too_many_cells` | skipped | Tabelle zu groß | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. |
| `gone` | skipped | Datei nicht mehr vorhanden | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. |
| `image_not_ocrable` | skipped | Bild ohne erkennbare Schrift | Keine. |
| `excluded` | skipped | Durch Regel ausgeschlossen | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. |
| `empty_file` | failed | Datei ist leer | Keine. Die Datei hat 0 Byte. |
| `corrupt` | failed | Datei beschädigt | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. |
| `xml_invalid` | failed | Dokumentstruktur fehlerhaft | Das Dokument im Ursprungsprogramm öffnen und neu speichern. |
| `encoding_unknown` | failed | Zeichensatz nicht erkannt | Die Datei als UTF-8 speichern und neu hochladen. |
| `timeout` | failed | Zeitüberschreitung beim Lesen | Wird beim nächsten Lauf erneut versucht. |
| `out_of_memory` | failed | Zu wenig Speicher beim Lesen | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. |
| `gateway_error` | failed | Datei war nicht abrufbar | Wird beim nächsten Lauf erneut versucht. |
| `repeatedly_stuck` | failed | Mehrfach hängen geblieben | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. |
| `ocr_failed` | failed | Texterkennung fehlgeschlagen | Wird beim nächsten Lauf erneut versucht. |
| `ocr_unavailable` | failed | Texterkennung nicht verfügbar | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. |

Englische Quell-Strings dieser beiden Spalten liegen wörtlich in `l10n`-Form neben den deutschen, gleiche Reihenfolge, gleiche Zahl.

**Verbot:** Kein Grund darf jemals als Rohcode angezeigt werden. Trifft ein unbekannter Reason ein (Drift zwischen den drei Listen), zeigt die UI `Unbekannter Grund (%s)` / `Unknown reason (%s)` mit dem Code in Klammern statt eines leeren Feldes.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | keine | not applicable, shadcn nicht initialisiert (04-CONTEXT D-02 verbietet einen Build-Step) |
| Drittanbieter-Registries | keine | keine deklariert, Gate entfällt |
| Material Design Icons (Pictogrammers), Apache-2.0 | 8 SVG-Pfade, wörtlich unten aufgeführt | Pfaddaten am 02.09.2026 aus `Templarian/MaterialDesign-SVG` (Stand master vom 02.09.2026) gezogen und im Dokument fixiert; beim Eintrag in `THIRD-PARTY.md` den konkreten Commit-Hash statt `master` festhalten. Kein Paket, keine Laufzeit, kein Code, nur `d`-Attribute. Lizenz Apache-2.0, mit AGPL-3.0 vereinbar |

---

## Seitenaufbau

Ein `ISettings` der PHP-Companion-App, registriert in einer eigenen `Section` mit der ID `findling`. Ein Template, fünf `<div class="section">`-Blöcke in dieser Reihenfolge. Die Reihenfolge ist die Erzählung: was gerade wahr ist, was zu erwarten ist, was schiefging, eine einzelne Datei nachschlagen, die Regeln ändern.

| # | Block-ID | h2 | Requirement | Inhalt |
|---|----------|----|-------------|--------|
| 1 | `findling-coverage` | Deckungsgrad der Suche | ADM-01 | Prozent-Kopfzahl, Fortschrittsbalken, Statuszeile, vier Metrik-Kacheln, Banner-Slot |
| 2 | `findling-estimate` | Schätzung für den Erstindex | ADM-03 | Eine Schätzzeile plus Hinweis. Wird **nur gerendert, solange der Erstindex nicht durch ist** |
| 3 | `findling-errors` | Nicht indexierte Dateien | ADM-01 | Tabelle, gruppiert nach Grund, absteigend nach Anzahl, je Gruppe aufklappbare Beispielpfade |
| 4 | `findling-diagnosis` | Einzelne Datei prüfen | ADM-02 | Ein Textfeld, ein Button, eine Ergebniskarte |
| 5 | `findling-rules` | Regeln und Grenzen | ADM-04 | Ausschlussliste, Größen-Cap, zwei Schalter, ein `.primary`-Button |

Genau fünf Blöcke und vier Schalter. Die Pitfalls-Lehre "Einstellungsseite mit 20 Optionen widerspricht dem Zero-Config-Versprechen" ist damit eingehalten: eine Statusseite, wenige Schalter, kein "Erweitert"-Bereich.

### Deckungsgrad: Anzeigevertrag

- Kopfzahl = `indexed / indexable`, ganzzahlig gerundet, nie aufgerundet auf 100 solange `indexable - indexed > 0`. Bei 99,6 % steht `99 %`.
- `indexable` schließt `excluded` **aus**. Der Nenner wird im Text benannt (`von %s indexierbaren Dateien`), damit die Zahl prüfbar ist statt geglaubt werden zu müssen.
- `excluded` ist eine eigene Kachel plus die Erklärzeile darunter. Ausgeschlossene Dateien verschwinden nie stumm.
- `<progress max="100" value="94">` mit sichtbarer Prozentzahl daneben. Der Balken ist Beigabe, die Zahl ist die Aussage.
- Ist `indexable` gleich 0, steht statt `0 %` der Empty-State-Text. Eine Division durch Null wird nicht als `0 %` verkauft.

### Fehlerliste: Grenzen

- Gruppiert nach `reason`, sortiert absteigend nach Anzahl, bei Gleichstand alphabetisch nach Label. Die Gruppenzahl ist **von Natur aus gedeckelt**, weil `REASONS` eine geschlossene Liste mit 20 Einträgen ist. Keine Pagination auf Gruppenebene nötig.
- Je Gruppe maximal **20 Beispielpfade**, danach die Zeile `und %n weitere`. Das ist die Antwort auf den `MAX_LIST_LENGTH`-Gotcha aus CR-01: die Obergrenze ist eine Anzeigeentscheidung mit sichtbarem Restzähler, keine stille Kürzung.
- Pfade werden **nie abgeschnitten**. `overflow-wrap: anywhere`, mehrzeilig erlaubt. Ein Pfad ist die Nutzlast dieser Liste, eine Ellipse macht ihn wertlos. Kein `title`-Tooltip als Ersatz.
- Jeder Beispielpfad ist ein Button, der Block 4 mit diesem Pfad füllt, dorthin scrollt und die Prüfung auslöst (04-CONTEXT D-04).
- Nicht mehr auflösbare `fileid`s erscheinen mit dem Ersatztext statt zu verschwinden.

---

## Zustands-Inventar

Acht Anzeigezustände, alle erstklassig sichtbar. `failed`, `skipped`, `truncated` und `excluded` haben denselben Rang wie `indexed`, das ist der Kern der Phase.

| Zustand | Icon (MDI) | Icon-Farbe | Chip-Fläche | Chip-Text | DE Label |
|---------|-----------|-----------|-------------|-----------|----------|
| `indexed` | `check-circle-outline` | `--color-element-success` | `--color-success` | `--color-success-text` | Indexiert |
| `indexed` + `truncated` | `content-cut` | `--color-element-warning` | `--color-warning` | `--color-warning-text` | Indexiert, Text gekürzt |
| `queued` | `clock-outline` | `--color-text-maxcontrast` | `--color-background-hover` | `--color-main-text` | Wartet in der Warteschlange |
| `processing` | Core-Klasse `icon-loading-small` | -- | `--color-background-hover` | `--color-main-text` | Wird gerade verarbeitet |
| `skipped` | `minus-circle-outline` | `--color-element-warning` | `--color-warning` | `--color-warning-text` | Übersprungen |
| `skipped` + `excluded` | `folder-off-outline` | `--color-text-maxcontrast` | `--color-background-hover` | `--color-main-text` | Ausgeschlossen |
| `failed` | `alert-circle-outline` | `--color-element-error` | `--color-error` | `--color-error-text` | Fehlgeschlagen |
| `unknown` | `information-outline` | `--color-text-maxcontrast` | `--color-background-hover` | `--color-main-text` | Noch nicht gesehen |

Chip-Bauform: `<span class="findling-chip findling-chip--{state}">` mit Inline-SVG (16 × 16, `fill: currentColor`, `aria-hidden="true"`, `focusable="false"`) plus Textlabel, Innenabstand 4px vertikal und 8px horizontal, Radius `var(--border-radius-small)`, Schrift 13px / 400, Abstand Icon zu Text 4px.

### SVG-Pfaddaten (wörtlich, `viewBox="0 0 24 24"`)

```
check-circle-outline   M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M12 20C7.59 20 4 16.41 4 12S7.59 4 12 4 20 7.59 20 12 16.41 20 12 20M16.59 7.58L10 14.17L7.41 11.59L6 13L10 17L18 9L16.59 7.58Z
alert-circle-outline   M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z
minus-circle-outline   M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M7,13H17V11H7
clock-outline          M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z
folder-off-outline     M2.39 1.73L1.11 3L2.64 4.53C2.25 4.9 2 5.42 2 6V18C2 19.11 2.9 20 4 20H18.11L20.84 22.73L22.11 21.46L2.39 1.73M4 18V8H6.11L16.11 18H4M11.2 8L7.2 4H10L12 6H20C21.1 6 22 6.89 22 8V18C22 18.24 21.96 18.47 21.88 18.68L20 16.8V8H11.2Z
content-cut            M19,3L13,9L15,11L22,4V3M12,12.5A0.5,0.5 0 0,1 11.5,12A0.5,0.5 0 0,1 12,11.5A0.5,0.5 0 0,1 12.5,12A0.5,0.5 0 0,1 12,12.5M6,20A2,2 0 0,1 4,18C4,16.89 4.9,16 6,16A2,2 0 0,1 8,18C8,19.11 7.1,20 6,20M6,8A2,2 0 0,1 4,6C4,4.89 4.9,4 6,4A2,2 0 0,1 8,6C8,7.11 7.1,8 6,8M9.64,7.64C9.87,7.14 10,6.59 10,6A4,4 0 0,0 6,2A4,4 0 0,0 2,6A4,4 0 0,0 6,10C6.59,10 7.14,9.87 7.64,9.64L10,12L7.64,14.36C7.14,14.13 6.59,14 6,14A4,4 0 0,0 2,18A4,4 0 0,0 6,22A4,4 0 0,0 10,18C10,17.41 9.87,16.86 9.64,16.36L12,14L19,21H22V20L9.64,7.64Z
magnify                M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z
information-outline    M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z
```

`magnify` steht im Diagnose-Button, `information-outline` in den Hinweis-Bannern.

### Leer- und Randzustände

| Fall | Auslöser | Darstellung |
|------|----------|-------------|
| Noch kein Zustand | `note == NO_STATE_YET` oder `indexable == 0` | Block 1: Empty-State-Überschrift und -Text statt Kopfzahl, kein Balken, Kacheln mit echten Nullen. Block 3: derselbe Text statt Tabelle. Block 4 und 5 voll bedienbar |
| Zustands-DB unlesbar | `note == STATE_UNREADABLE` | Fehler-Banner mit dem Backend-Fehlertext, darunter die Nullen. Kein "0 % Deckung" als Aussage |
| Backend antwortet nicht | ExApp-Aufruf liefert `error` oder Timeout | Fehler-Banner oben in Block 1. Blöcke 1 und 3 zeigen die letzten PHP-seitigen Zahlen aus `findling_file_state` mit Zeitstempel. Block 2 verborgen. Block 4 antwortet mit dem Backend-stumm-Text. Block 5 bleibt bedienbar, denn `appconfig` liegt in PHP |
| Schätzung läuft noch | Metadaten-Scan nicht fertig | Block 2: `icon-loading-small` plus "Die Dateien werden gezählt, das dauert einen Moment." Keine Platzhalterzahlen, keine Skeleton-Balken |
| Erstindex durch | Erstlauf abgeschlossen | Block 2 wird nicht gerendert. ADM-03 ist eine Vorab-Schätzung, danach hat sie keine Aussage |
| Fehlerliste leer | alle Gruppen 0 | Block 3: eine Zeile, keine leere Tabelle, kein Tabellenkopf |
| Diagnose ohne Treffer | weder Pfad noch ID auflösbar | Ergebniskarte mit `information-outline`, neutrale Fläche, Fehlschlag-Text. Kein rotes Fehler-Styling, das ist eine Auskunft, kein Defekt |
| Diagnose ohne Verdikt | Datei existiert, keine Zustandszeile, keine Queue-Zeile | Chip `unknown` plus Text "Noch nicht gesehen" plus nächster Schritt |
| Ausschlussliste leer | keine Präfixe | "Kein Ordner ist ausgeschlossen." statt leerer Liste |
| Wenig Platz | `lowDisk == true` | Warn-Banner, Kopfzahl bleibt sichtbar. Ausdrücklich: "Die Suche funktioniert weiter" |
| Reindex nötig | `reindexRequired == true` | Warn-Banner mit dem `occ`-Befehl im Klartext |
| Lauf stockt | Fortschritt bewegt sich über mehrere Abfragen nicht, obwohl offene Arbeit besteht | Statuszeile wechselt auf den Stockt-Text. Nie grün, wenn nichts vorangeht (Pitfalls-Lehre "Statusseite ist grün, aber 0 Treffer") |

---

## Interaktionsvertrag

### Erstes Rendern ohne JavaScript

Blöcke 1 bis 3 werden **serverseitig mit echten Werten** gerendert. Ohne JavaScript sind Deckungsgrad, Schätzung und Fehlerliste vollständig lesbar. Kein Skeleton, kein Ladezustand beim ersten Aufschlag. Diagnose-Nachschlag und Regeln-Speichern brauchen JavaScript, das ist eine bewusste, dokumentierte Grenze für eine Verwaltungsseite.

### Aktualisierung

| Aspekt | Festlegung |
|--------|------------|
| Verfahren | `fetch` auf die PHP-Settings-Route, JSON-Antwort, Textknoten ersetzen. Kein Neuaufbau des DOM, kein Flackern |
| Kadenz aktiv | 5 s, solange offene Arbeit besteht |
| Kadenz im Ruhezustand | 30 s, sobald der Erstindex durch ist und keine Queue-Arbeit ansteht |
| Tab im Hintergrund | Abfrage pausiert bei `document.visibilityState !== 'visible'`, nimmt beim Zurückkehren mit einer sofortigen Abfrage wieder auf |
| Selbstabschaltung | Nach 20 aufeinanderfolgenden Abfragen ohne Zahlenänderung wird auf 30 s gedrosselt. Nie unendlich im 5-s-Takt gegen eine ruhende Instanz |
| Überlappung | Eine Abfrage gleichzeitig, vorherige über `AbortController` abbrechen |
| Fehlschlag | Zahlen bleiben stehen, Fehler-Banner erscheint, Abfrage läuft weiter. Zahlen werden nie auf 0 zurückgesetzt, weil eine Abfrage scheiterte |
| CSRF | `requesttoken`-Header aus `document.head.dataset.requesttoken` |

### Diagnose-Nachschlag

1. Eingabe akzeptiert Pfad **oder** Zahl im selben Feld (D-04). Erkennung: rein numerisch bis 19 Ziffern wird als `fileid` behandelt, alles andere als Pfad.
2. Absenden per Button oder `Enter` im Feld. Das Feld liegt in einem `<form>`, damit `Enter` ohne Tastatur-Handler funktioniert.
3. Während der Anfrage: Button deaktiviert, `icon-loading-small` im Button, Feld bleibt bedienbar.
4. Ergebnis erscheint in einer Karte unter dem Feld, `role="status" aria-live="polite"`, damit ein Screenreader die Antwort ohne Fokussprung hört.
5. Karteninhalt in dieser Reihenfolge: Zustands-Chip, aufgelöster Pfad (umbruchfähig), Grund-Label, Abhilfe-Satz, `Datei-ID: %s`, `Zuletzt geprüft: %s`.
6. Eine neue Prüfung ersetzt die Karte. Keine Historie, kein Stapel.

### Regeln speichern

1. Änderungen sind lokal, bis "Regeln speichern" gedrückt wird. Kein Auto-Speichern. Bei ungespeicherten Änderungen erscheint über dem Button die Zeile "Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu."
2. `Ausschluss hinzufügen` fügt der Liste eine Zeile hinzu, **noch nicht** gespeichert.
3. Enthält der Speichervorgang mindestens einen **neuen** Ausschluss, erscheint statt des sofortigen Speicherns eine **Inline-Bestätigung** direkt über dem Button: Fläche `--color-error`, Text `--color-error-text`, `alert-circle-outline` in `--color-element-error`, Radius `var(--border-radius-container)`, Innenabstand 16px. Darin der Destructive-Text mit Pfad und Dokumentzahl, dann zwei Buttons: `Ausschließen und entfernen` (Fläche `--color-element-error`, Textfarbe `--color-primary-element-text`) und `Dateien indexiert lassen` (Standard-Button). Erst der Bestätigungsklick schreibt.
4. Grund der Inline-Lösung statt eines Modals: `OC.dialogs.confirmDestructive` ist seit NC 30 deprecated und die App führt `max-version 35`. Inline ist zudem der Ort, an dem die Folge steht.
5. Reine Toggle- oder Cap-Änderungen ohne neuen Ausschluss speichern ohne Bestätigung. Es gibt nichts zu verlieren.
6. Rückmeldung inline unter dem Button, `role="status" aria-live="polite"`, kein Toast. Erfolg: `--color-success`-Fläche. Fehlschlag: `--color-error`-Fläche und der Satz "Es hat sich nichts geändert", damit klar ist, dass kein Halbzustand entstand.
7. Validierung vor dem Absenden, Fehlermeldung direkt am betroffenen Feld über `aria-describedby`, Fokus springt in das erste fehlerhafte Feld.

### Fehlergruppen aufklappen

`<button aria-expanded="false" aria-controls="findling-errors-{reason}">` mit den Texten "Beispielpfade anzeigen" / "Beispielpfade verbergen". Reines Anzeigen und Verbergen, keine Höhenanimation, keine Nachladeanfrage: die Beispiele stehen bereits im Markup. Ohne JavaScript sind alle Gruppen offen.

---

## Barrierefreiheit

| Anforderung | Umsetzung |
|-------------|-----------|
| Farbe nie allein | Jeder Zustand trägt Icon plus Textlabel plus Farbe (WCAG 1.4.1) |
| Kontrast | Nur Nextcloud-Farbpaare Fläche/Text, kein eigener Hexwert. Damit gelten die vom Core geprüften Verhältnisse in allen Themes |
| Beschriftung | Jedes Eingabeelement hat ein `<label for>`. Kein Placeholder als Label. Placeholder nur als Beispiel |
| Fortschritt | `<progress max="100" value="…" id="…">` mit `aria-labelledby` auf die Kopfzeile, Prozentwert zusätzlich als Text |
| Live-Bereiche | Genau drei: Statuszeile in Block 1, Diagnose-Ergebniskarte, Speicher-Rückmeldung. Alle `aria-live="polite"`. Die Kopfzahl selbst ist **kein** Live-Bereich, sonst plappert der Screenreader alle 5 s |
| Klickflächen | Mindesthöhe `var(--default-clickable-area)` (34px) für Buttons, Aufklapp-Buttons und Checkbox-Labels. Die 14px-Box des Core-Checkbox-Musters ist die Grafik, das Label ist die Klickfläche |
| Fokus | Core-Fokusring unangetastet. Kein `outline: none` im eigenen CSS |
| Icons | `aria-hidden="true"` und `focusable="false"` auf jedem SVG. Icon-only-Buttons (Ausschluss entfernen) tragen ein `aria-label` mit dem Pfad im Text |
| Tabelle | Echte `<table>` mit `<caption class="hidden-visually">`, `<th scope="col">`. Kein Div-Raster |
| Sprache | Alle Texte durch `$l->t()`. Keine hartcodierte Sprache im Template |
| Dark Mode | Automatisch, weil ausschließlich Variablen verwendet werden. Sichtprobe in Hell, Dunkel und Hoher Kontrast gehört zur Abnahme |

---

## Verbote

- Kein npm, kein Build-Step, kein Vue, kein Bundle im Companion-Repo (D-02).
- Kein Hexwert, kein `rgb()`, kein `hsl()` im eigenen CSS. Nur `var(--…)`.
- Kein Emoji, nirgends. Icons nur als SVG.
- Kein Em-Dash in Nutzertexten.
- Kein Inline-`<script>`, kein `style`-Attribut mit Farbe oder Abstand (CSP und Theming).
- Kein Dateiname und kein Pfad in einer Antwort des Containers. Pfade entstehen ausschließlich PHP-seitig zur Anzeigezeit (D-03).
- Kein Skeleton-Platzhalter und keine Schätzzahl, die als Messwert aussieht.
- Keine Prozentzahl ohne benannten Nenner.
- Kein stiller Zustand: `failed`, `skipped`, `truncated` und `excluded` sind immer sichtbar.
- Kein Toast als einzige Rückmeldung einer Schreibaktion.
- Keine abgeschnittenen Pfade.
- Keine deprecated Nextcloud-API (Liste oben in "Bewusst nicht verwendet").

---

## Abnahme-Sichtproben

Gegen `docs/dev-setup.md` (Port 8090, `testuser`/`kollegin`, Testkorpus):

1. Frische Installation, Seite innerhalb der ersten Minute öffnen: Empty-State-Text, echte Nullen, keine Fehlermeldung, Block 2 zeigt den Zähl-Hinweis.
2. Erstindex läuft: Kopfzahl steigt ohne Neuladen, Statuszeile nennt Restzeit, Block 2 aktualisiert sich mit.
3. Backend gestoppt: Fehler-Banner erscheint, Zahlen bleiben stehen und springen nicht auf 0, Block 5 bleibt bedienbar.
4. Korpus mit defektem PDF, passwortgeschütztem PDF, 0-Byte-Datei und 500-MB-Datei: vier Gruppen mit korrektem Label und korrekter Abhilfe, Beispielpfade auflösbar.
5. Beispielpfad anklicken: Block 4 gefüllt, Ergebniskarte mit demselben Grund.
6. Diagnose mit einer Zahl, mit einem Pfad, mit Unsinn: drei unterschiedliche, jeweils erklärte Antworten.
7. Ausschluss auf einen Ordner mit indexierten Dokumenten hinzufügen und speichern: Inline-Bestätigung nennt die Dokumentzahl, nach der Bestätigung erscheinen die Dateien mit Grund `Durch Regel ausgeschlossen`.
8. Größen-Cap auf 0 und auf 99999: Validierungsmeldung am Feld, Fokus im Feld, kein Speichern.
9. Dunkles Theme und Hoher Kontrast: kein Text unter 4.5:1, kein unsichtbarer Chip.
10. Tastatur allein: alle fünf Blöcke durchlaufbar, Aufklappen, Diagnose, Speichern und Bestätigen ohne Maus.
11. JavaScript deaktiviert: Blöcke 1 bis 3 vollständig lesbar, alle Fehlergruppen offen.
12. Seite auf Englisch und auf Deutsch: keine unübersetzte Zeichenkette, keine abgeschnittene Beschriftung.

---

## Herkunft der Festlegungen

| Quelle | Übernommene Entscheidungen |
|--------|---------------------------|
| 04-CONTEXT.md | D-01 Ort als `ISettings`-Sektion, D-02 Vanilla ohne Build, D-03 Pfadauflösung in PHP, D-04 ein Feld für Pfad oder ID plus Verlinkung aus der Fehlerliste, D-05 keine Bestätigung vor dem Erstindex, D-06 Präfixe ohne Muster und Grund `excluded`, D-07 aktive Räumung als bestätigungspflichtige Folge, D-08 vier Schalter mit Wirkung im nächsten Lauf. Discretion genutzt für: Abfragekadenz, Fehlerlisten-Grenzen und Sortierung |
| ROADMAP.md Phase 4 | Vier Erfolgskriterien wörtlich auf die fünf Blöcke abgebildet |
| REQUIREMENTS.md | ADM-01 Blöcke 1 und 3, ADM-02 Block 4, ADM-03 Block 2, ADM-04 Block 5. IDX-06 `failed`/`skipped` erstklassig sichtbar |
| research/PITFALLS.md | Deckung statt Konnektivität, benannter Nenner, gruppierte Fehler mit Grund und Abhilfe, Stockt-Zustand statt Grün, wenige Schalter statt Optionsflut, Pfade als Beispiele |
| `backend/src/findling/api/status.py` | Feldnamen des Anzeigevertrags, `NO_STATE_YET` und `STATE_UNREADABLE` als eigene Zustände, `lowDisk` und `reindexRequired` als Banner, Privacy-Grenze |
| `php/lib/Service/FileStateService.php` | Vollständige Grund-Taxonomie, drei Zustände, Behandlung eines unbekannten Reason |
| `php/lib/Command/IndexCommand.php` | `occ findling:index --restart` als genannter Rückweg im Reindex-Banner |
| Nextcloud `stable32`-Quellen | Alle Token, Klassen und APIs, siehe Verifikationstabelle unter "Design System" |
| CLAUDE.md / globale Regeln | Keine Emojis, keine Em-Dashes, echte Umlaute in deutscher Prosa, ASCII in Bezeichnern |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
