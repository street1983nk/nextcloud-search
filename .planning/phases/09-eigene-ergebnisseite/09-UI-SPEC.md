---
phase: 9
slug: eigene-ergebnisseite
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-08
---

# Phase 9: UI Design Contract

> Visueller und interaktiver Vertrag für die eigene Ergebnisseite. Erzeugt von gsd-ui-researcher, zu prüfen von gsd-ui-checker.
>
> Deutsche Prosa ist die Arbeitssprache dieses Dokuments. Alle Bezeichner, CSS-Klassen, IDs, Routennamen und Quell-Strings bleiben englisch, die deutschen und französischen Nutzertexte stehen in der Copy-Tabelle als Übersetzung.
>
> Diese Seite ist keine freie Web-App. Sie ist eine Nextcloud-App-Seite und ordnet sich dem Server-Theming unter. Es wird keine eigene Marke erfunden, keine eigene Palette gesetzt und keine Schrift mitgebracht.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none. Kein npm, kein Bundler, kein Build-Step in der Companion-App (Fortschreibung von 04-CONTEXT D-02) |
| Preset | not applicable |
| Component library | none. Nextcloud-Server-CSS (`core/css/server.scss`, `core/css/apps.scss`, `core/css/inputs.scss`) plus eine eigene `php/css/search.css` |
| Icon library | Material Design Icons (Pictogrammers), Apache-2.0, als **Inline-SVG** im PHP-Template. Dateityp-Symbole kommen vom Server über `IMimeTypeDetector::mimeTypeIcon()` |
| Font | `var(--font-face)` von Nextcloud (System-UI-Stack). Keine eigene Schrift, kein Webfont |

### Stack-Entscheidung: serverseitiges Template statt @nextcloud/vue

**Festlegung: PHP-Template plus Vanilla-JavaScript, kein Vue, kein `@nextcloud/vue`, kein Build.**

| Kriterium | Serverseitiges Template (gewählt) | Vue mit `@nextcloud/vue` (verworfen) |
|-----------|-----------------------------------|--------------------------------------|
| Bestand der App heute | `php/templates/admin.php` (52 KB), `php/js/admin.js` (60 KB Vanilla), `php/css/admin.css` (105 Verwendungen von `var(--…)`, kein einziger Hexwert). Es gibt **keine** `package.json` im Repo | Erste `package.json`, erster Bundler, erste `node_modules` in einem Repo, das bis heute ohne auskommt |
| Prüfbarkeit | `backend/tests/test_admin_ui_contract.py` liest Template, CSS und Skript als Text und hält die Verbote. Auf der Maschine gibt es kein PHP und kein npm, nur `php -l` im Container | Ein Bundle ist für dieselbe Gate-Art Text ohne Aussage. Die vorhandene Prüfkette müsste ersetzt statt erweitert werden |
| Erfolgskriterium 3 (Öffnen und Zurück) | Ein normales Dokument. Der Browser stellt die Scrollposition beim Zurück selbst wieder her, auch ohne JavaScript | Eine SPA muss dieselbe Wiederherstellung von Hand bauen und verliert sie bei jedem Routerfehler |
| Erstes Rendern | Vollständige Trefferliste im ersten HTML. Kein Skeleton, kein Spinner, keine leere Sekunde | Leerer Rahmen, dann Nachladen. Genau das Bild, das Erfolgskriterium 5 verbietet |
| Versionsfenster NC 33 bis 35 | `#app-content` existiert unverändert in `core/css/apps.scss` in stable33, stable34 und stable35 (geprüft 08.09.2026) | `@nextcloud/vue` müsste gegen drei Serverfassungen gepinnt und mitgezogen werden |
| Zero-Config-Versprechen | Zwei neue Dateien, keine neue Abhängigkeit | Eine Werkzeugkette im Auslieferungspfad einer App, die verspricht, keine zu brauchen |

Die Seite braucht JavaScript für **nichts** außer der Rückkehr-Markierung (siehe Interaktionsvertrag). Suche, Paginierung, Filter und das Öffnen eines Treffers sind Links und ein `<form method="get">`.

### Verifizierte Grundlage (Nextcloud `stable33`, `stable34`, `stable35`, geprüft am 08.09.2026)

| Fakt | Quelle | Folge für diese Phase |
|------|--------|----------------------|
| `--default-grid-baseline: 4px`, `--default-font-size: 15px`, `--font-size-small: 13px`, `--default-line-height: 1.5`, `--default-clickable-area: 34px`, `--border-radius-container: 12px` in allen drei Zweigen identisch | `apps/theming/lib/Themes/DefaultTheme.php` | Spacing- und Typografie-Tabelle unten |
| `--color-primary-element-light` und `--color-primary-element-light-text` existieren in allen drei Zweigen | `apps/theming/lib/Themes/CommonThemeTrait.php` | Das Farbpaar der `<mark>`-Hervorhebung |
| `--background-invert-if-dark` ist `no` im hellen und `invert(100%)` im dunklen Theme | `DefaultTheme.php`, `DarkTheme.php` | Dateityp-Symbole bleiben im Dark Mode sichtbar |
| `#app-content` und `#app-content-wrapper` sind unverändert im Core-CSS | `core/css/apps.scss` Zeile 742 und 756 | Eine Nicht-Vue-App-Seite bekommt das normale Layout |
| `IMimeTypeDetector::mimeTypeIcon($mimeType)`, `@since 8.2.0` | `lib/public/Files/IMimeTypeDetector.php` | Dateityp-Symbole kommen vom Server, kein eigener Symbolsatz, keine zweite Lizenzfrage |
| `SearchComposer::getProviders()` setzt `'inAppSearch' => $provider instanceof IInAppSearch` | `lib/private/Search/SearchComposer.php` Zeile 202 | siehe nächste Zeile |
| Der Knopf `Search in {name}`, den `inAppSearch` einschaltet, hat in stable33, stable34, stable35 und master **keinen Klick-Handler und kein href** | `core/src/components/UnifiedSearch/UnifiedSearchModal.vue` Zeilen 161 und 191 (33/34), Zeile 227 (35/master) | **`IInAppSearch` wird nicht implementiert.** Es würde einen toten Knopf in den Dialog stellen, nicht den Einstiegspunkt aus Erfolgskriterium 1 |
| `SearchResult.vue` rendert `icon` als CSS-Klasse **oder** als URL (`backgroundImage`) und `resourceUrl` als `href` mit `target="_self"` | `core/src/components/UnifiedSearch/SearchResult.vue` | Der Einstieg kann ein gewöhnlicher Ergebniseintrag sein |
| In stable33 und stable34 erscheint `Load more results` genau dann, wenn `results.length === limit` | `UnifiedSearchModal.vue` Zeile 155 | Ein angehängter Einstiegs-Eintrag ersetzt dort den Nachlade-Knopf. Bewusst in Kauf genommen, siehe Einstiegspunkt |
| `SecurityMiddleware` prüft CSRF für jede Route ohne `NoCSRFRequired`, und `Request::passesCSRFCheck()` verlangt ein `requesttoken` in GET, POST oder Header | `lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php` Zeilen 194 bis 232, `lib/private/AppFramework/Http/Request.php` Zeile 438 | Die Seitenroute **muss** `NoCSRFRequired` tragen, sonst sind Lesezeichen, Zurück-Navigation und der Link aus dem Dialog unmöglich. Das ist keine Bequemlichkeit, es ist Erfolgskriterium 3 |

### Bestand der eigenen App (gelesen am 08.09.2026)

| Datei | Was daraus übernommen wird |
|-------|----------------------------|
| `php/css/admin.css` | Die Schreibweise jedes Abstands als `calc(var(--default-grid-baseline) * n)`, kein Hexwert, kein `rgb()` |
| `php/templates/admin.php` | `$l->t()` für jede sichtbare Zeichenkette, `p()` für jeden Wert, kein Inline-Skript, kein `style`-Attribut, `hidden` als einziger Schaltmechanismus |
| `php/js/admin.js` | `OC.generateUrl`, `requesttoken`, kein Modul, kein Bundler, kein Markup aus Zeichenketten |
| `php/lib/Search/Provider.php` | Die Sicherheitsgrenze: Vorfilter, `getFirstNodeById`, `isReadable`, Titel und Pfad aus dem bestätigten Node, Snippet erst für die Überlebenden |
| `php/lib/Service/ExAppService.php` | `MAX_LIMIT = 100`, `MAX_SNIPPET_IDS = 100`, `MAX_SNIPPET_LENGTH = 1000`, `MAX_HIGHLIGHTS = 32`, Highlights als geprüfte Zeichen-Offsets |

---

## Spacing Scale

Basis ist `var(--default-grid-baseline)` = 4px. Eigene Abstände werden als `calc(var(--default-grid-baseline) * n)` geschrieben, nie als lose px-Zahl.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Abstand Symbol zu Text im Knopf, Abstand Titel zu Pfad |
| sm | 8px | Innenabstand der Bannerzeile vertikal, Abstand Pfad zu Snippet, Abstand der beiden Paginierungsknöpfe |
| md | 16px | Innenabstand einer Trefferzeile, Abstand Symbol zu Textblock, Seitenrand unter 1024px, Kantenlänge der Inline-SVG in Knöpfen |
| lg | 24px | Abstand Kopfbereich zu Trefferliste, Abstand Trefferliste zu Paginierung, Innenabstand des Bannerblocks |
| xl | 32px | Seitenrand ab 1024px, Kantenlänge des Dateityp-Symbols in der Trefferzeile |
| 2xl | 48px | Abstand über und unter einem Leerzustand |
| 3xl | 64px | Kantenlänge des Symbols im Leerzustand |

**Exceptions (alle fremdbestimmt, nicht von uns gesetzt):**

| Wert | Woher | Umgang |
|------|-------|--------|
| 34px | `var(--default-clickable-area)` | Verbindliche Mindesthöhe jeder Klickfläche: Trefferzeile, Paginierungsknopf, Suchknopf, Filter-Label |
| 44px | Kein Nextcloud-Token, eigene Regel | Unter `@media (pointer: coarse)` steigt die Mindesthöhe von Trefferzeile und Paginierungsknopf auf 44px. 44 ist ein Vielfaches von 4, also keine Verletzung der Skala |
| Layout des `#app-content` | Core | Nicht überschreiben. Die Seite setzt nur ihren eigenen Innenabstand und ihre Inhaltsbreite |

Inhaltsbreite: `max-width: 900px`, `margin-inline: auto`. Dieselbe Zahl wie auf der Verwaltungsseite, damit die beiden Seiten derselben App dieselbe Lesezeile haben.

---

## Typography

Nextcloud setzt alle Überschriften auf `font-size: 100%` zurück. Was nicht hier steht, existiert auf der Seite nicht.

| Role | Size | Weight | Line Height | Anwendung |
|------|------|--------|-------------|-----------|
| Body | 15px (`var(--default-font-size)`) | 400 | 1.5 (`var(--default-line-height)`) | Snippet, Bannertext, Leerzustandstext, Eingabefeld, Knöpfe |
| Hit title | 15px | 700 | 1.5 | Dateiname in der Trefferzeile |
| Label | 13px (`var(--font-size-small)`) | 400 | 1.5 | Pfad, Seitenmarke, Filter-Label, Hinweiszeile unter der Paginierung |
| Heading | 20px | 700 | 1.2 | Die eine `h1` der Seite und die Überschrift eines Leerzustands |

**Drei Größen, exakt: 13, 15, 20.** Es gibt keine vierte. **Zwei Schriftstärken, exakt: 400 und 700.** 700 ist die Stärke, die der Core für Überschriften verwendet, deshalb kein 600. Der Dateiname trägt seine Hierarchie über das Gewicht, nicht über eine eigene Größe.

Es gibt auf dieser Seite **keine Display-Stufe und keine große Zahl**, weil die Seite keine Gesamttrefferzahl behauptet (siehe Paginierungsvertrag).

---

## Color

Kein einziger Hexwert im eigenen CSS. Ausschließlich Nextcloud-Variablen, damit Dark Mode, Hoher Kontrast und Theming ohne Zutun funktionieren.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `var(--color-main-background)` | Seitengrund, Grund jeder Trefferzeile im Ruhezustand |
| Secondary (30%) | `var(--color-background-hover)` | Trefferzeile bei Hover und Fokus, Rückkehr-Markierung, Grund des Paginierungsstreifens. Trennlinien zwischen Trefferzeilen: `var(--color-border)` |
| Accent (10%) | `var(--color-primary-element)` | siehe Reserveliste |
| Destructive | nicht anwendbar | **Diese Phase hat keine zerstörerische Aktion.** Es gibt nichts zu löschen, nichts zu überschreiben und keinen Schreibvorgang. Eine Bestätigungsfläche existiert deshalb nicht |

**Accent reserved for:** genau drei Dinge, nichts sonst.

1. Der einzige `.primary`-Knopf der Seite: "Suchen".
2. Die Hervorhebung des Suchworts im Snippet, als geprüftes Paar `background-color: var(--color-primary-element-light)` mit `color: var(--color-primary-element-light-text)`.
3. Der Fokusring von Links, Knöpfen und Eingabefeld (kommt vom Core, wird nicht angefasst).

Nicht Akzent: die `h1`, der Dateiname, die Paginierungsknöpfe (tertiär), der Pfad, die Trennlinien, das Dateityp-Symbol.

**Semantische Farben, getrennt vom Akzent-Budget.** Jede Farbe wird nur im Paar Fläche plus zugehörige Textfarbe verwendet, weil Nextcloud diese Paare auf Kontrast geprüft ausliefert.

| Bedeutung | Fläche | Text | Icon |
|-----------|--------|------|------|
| Fehler (Backend stumm, Versionsdrift) | `--color-error` | `--color-error-text` | `--color-element-error` |
| Hinweis (Index im Aufbau, Seitenobergrenze erreicht) | `--color-info` | `--color-info-text` | `--color-element-info` |

**Farbe ist nie der einzige Träger einer Information.** Jeder Zustandsblock trägt Symbol plus Überschrift plus Fließtext. Die Hervorhebung im Snippet ist zusätzlich ein `<mark>`-Element, also auch für einen Screenreader eine Hervorhebung und nicht nur eine andere Farbe (WCAG 1.4.1).

---

## Copywriting Contract

Quell-Strings sind englisch und laufen durch `$l->t()`. Die deutsche Spalte ist der Inhalt von `php/l10n/de.json` und `php/l10n/de.js`. Die französische Spalte ist heute **nicht** ausgeliefert (die App führt nur einen deutschen Katalog); sie steht hier, damit `fr.json` ein mechanischer Nachzug bleibt und keine zweite Textrunde. Deutsche Texte tragen echte Umlaute, keinen Em-Dash und kein Emoji.

| Element | EN (Quelle) | DE | FR |
|---------|-------------|----|----|
| Navigationseintrag und Seitenname | `Findling` | Findling | Findling |
| Primary CTA | `Search` | Suchen | Rechercher |
| Feld-Label | `Search term` | Suchbegriff | Terme de recherche |
| Feld-Platzhalter (nur Beispiel, nie Label) | `invoice 2026` | Rechnung 2026 | facture 2026 |
| Filter-Label | `Search file names only` | Nur Dateinamen durchsuchen | Rechercher uniquement dans les noms de fichiers |
| Überschrift mit Suchbegriff | `Results for "%s"` | Treffer für „%s“ | Résultats pour « %s » |
| Liste (Accessible Name) | `Search results` | Suchergebnisse | Résultats de recherche |
| Trefferzeile (Accessible Name) | `%1$s in %2$s` | %1$s in %2$s | %1$s dans %2$s |
| Rückkehr-Markierung (nur für Screenreader) | `last opened` | zuletzt geöffnet | ouvert en dernier |
| Einstieg im Suchdialog, Titel | `Show all results` | Alle Treffer anzeigen | Afficher tous les résultats |
| Einstieg im Suchdialog, Unterzeile | `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Ouvre la page de résultats de Findling |
| Paginierung zurück | `Previous page` | Vorherige Seite | Page précédente |
| Paginierung vor | `Next page` | Nächste Seite | Page suivante |
| Seitenmarke | `Page %s` | Seite %s | Page %s |
| Obergrenze erreicht | `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | D'autres résultats existent. Affinez la recherche pour les voir. |
| Empty state ohne Suchbegriff, Überschrift | `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Recherchez dans le contenu de vos fichiers |
| Empty state ohne Suchbegriff, Text | `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Saisissez un mot tiré d'un document. Findling recherche le texte à l'intérieur de vos fichiers, y compris les PDF numérisés. |
| Empty state ohne Treffer, Überschrift | `No file contains "%s"` | Keine Datei enthält „%s“ | Aucun fichier ne contient « %s » |
| Empty state ohne Treffer, Text | `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Essayez un autre mot, une partie d'un mot composé ou vérifiez l'orthographe. |
| Error state Backend stumm, Überschrift | `The search is not answering right now` | Die Suche antwortet gerade nicht | La recherche ne répond pas pour le moment |
| Error state Backend stumm, Text | `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | Findling n'a pas pu joindre son service. Vos fichiers sont inchangés. Réessayez dans un instant et prévenez votre administration si cela persiste. |
| Error state Backend stumm, Knopf | `Try again` | Erneut versuchen | Réessayer |
| Error state Versionsdrift, Überschrift | `Findling is not ready to search` | Findling ist nicht suchbereit | Findling n'est pas prêt à rechercher |
| Error state Versionsdrift, Text | `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | Les deux moitiés de Findling annoncent des versions différentes. L'administration doit les mettre à jour ensemble. |
| Hinweis Index im Aufbau | `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | L'index est encore en construction, des résultats peuvent donc manquer. |

**Regeln über den Wortlaut hinaus:**

- **Kein Satz nennt jemals Berechtigungen.** Weder "Treffer wurden entfernt" noch "Sie haben keinen Zugriff auf weitere Treffer" noch eine Zahl, aus der sich das ableiten ließe. Ein Treffer, den der Recheck verwirft, hat für diese Seite nie existiert. Alles andere wäre ein Kanal, über den sich die Existenz fremder Dateien abfragen lässt, und würde die Sicherheitsgrenze aus UI-03 durch die Anzeige aushebeln.
- **Keine Gesamttrefferzahl.** Der Container meldet `hasMore`, keine Summe. Eine Zahl, die niemand gemessen hat, wird nicht gerendert (Projektregel aus Phase 4).
- Der Suchbegriff erscheint in Überschriften in typografischen Anführungszeichen der Zielsprache und wird immer escaped ausgegeben.
- Kein Toast, keine Snackbar. Jede Aussage steht auf der Seite.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | keine | not applicable, shadcn nicht initialisiert (kein Build-Step in der Companion-App) |
| Drittanbieter-Registries | keine | keine deklariert, Gate entfällt |
| Material Design Icons (Pictogrammers), Apache-2.0 | drei neue `d`-Attribute: `chevron-left`, `chevron-right`, `file-search-outline`. Wiederverwendet ohne neue Zeile: `magnify`, `alert-circle-outline`, `information-outline` | Am 08.09.2026 gegen den in `THIRD-PARTY.md` gepinnten Commit `9e04201d4557e729822fb57f62a316c3dea1d4a8` (Tag `v7.4.47`) gezogen und wörtlich unten fixiert. Kein Paket, keine Laufzeit, kein Code, nur Kurvendaten. Lizenz Apache-2.0, mit AGPL-3.0 vereinbar. `THIRD-PARTY.md` bekommt die drei Namen in derselben Zeile, in der sie zum ersten Mal gerendert werden |
| Nextcloud-Server (Dateityp-Symbole) | `IMimeTypeDetector::mimeTypeIcon()` | Kein Fremdmaterial. Die Symbole gehören dem Server, werden per URL referenziert und nicht kopiert |

### SVG-Pfaddaten (wörtlich, `viewBox="0 0 24 24"`)

```
chevron-left           M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z
chevron-right          M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z
file-search-outline    M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H13C12.59,21.75 12.2,21.44 11.86,21.1C11.53,20.77 11.25,20.4 11,20H6V4H13V9H18V10.18C18.71,10.34 19.39,10.61 20,11V8L14,2M20.31,18.9C21.64,16.79 21,14 18.91,12.68C16.8,11.35 14,12 12.69,14.08C11.35,16.19 12,18.97 14.09,20.3C15.55,21.23 17.41,21.23 18.88,20.32L22,23.39L23.39,22L20.31,18.9M16.5,19A2.5,2.5 0 0,1 14,16.5A2.5,2.5 0 0,1 16.5,14A2.5,2.5 0 0,1 19,16.5A2.5,2.5 0 0,1 16.5,19Z
magnify                M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z
alert-circle-outline   M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z
information-outline    M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z
```

`magnify` steht im Suchknopf und im Leerzustand ohne Suchbegriff, `file-search-outline` im Leerzustand ohne Treffer, `alert-circle-outline` im Fehlerblock, `information-outline` im Hinweisbanner, die beiden Chevrons in der Paginierung.

Jedes Inline-SVG: 16 × 16 in Knöpfen, 64 × 64 im Leerzustand, `fill: currentColor`, `aria-hidden="true"`, `focusable="false"`.

---

## Seitenaufbau

### Ort, Route und Adresse

| Gegenstand | Festlegung |
|------------|------------|
| Controller | `php/lib/Controller/PageController.php`, Methode `index()` |
| Route | `#[FrontpageRoute(verb: 'GET', url: '/')]` plus `#[NoAdminRequired]` plus `#[NoCSRFRequired]`, Routenname `findling.page.index` |
| Adresse | `/apps/findling/?query=…&names=1&page=…&cursors=…` |
| Template | `php/templates/search.php`, gerendert als normale Nutzerseite (`RENDER_AS_USER`), Inhalt in `#app-content` |
| Stil und Skript | `php/css/search.css` und `php/js/search.js`, beide über `\OCP\Util::addStyle`/`addScript` im Template, wie auf der Verwaltungsseite |
| Navigationseintrag | `<navigations>` in `php/appinfo/info.xml` mit `<route>findling.page.index</route>`, `<icon>app.svg</icon>`, `<order>10</order>`. Dazu neu: `php/img/app.svg` (einfarbig schwarzes `magnify`, vom Server gethemt). `app-dark.svg` bleibt unangetastet |

`NoCSRFRequired` ist Pflicht und keine Bequemlichkeit: ohne dieses Attribut scheitert jede Navigation ohne `requesttoken`, also der Link aus dem Suchdialog, jedes Lesezeichen und jede Zurück-Navigation. Verifiziert in `SecurityMiddleware` und `Request::passesCSRFCheck()` von stable33.

### URL-Vertrag

| Parameter | Form | Bedeutung | Prüfung |
|-----------|------|-----------|---------|
| `query` | Zeichenkette, auf 255 Zeichen begrenzt | Der Suchbegriff. Reist als URL-Parameter, damit Lesezeichen, Zurück-Navigation und ein geteilter Link dieselbe Seite ergeben | `PlainText::bounded(…, 255)`, Ausgabe immer escaped, `maxlength="255"` am Feld |
| `names` | `1` oder fehlt | Der eingebaute Filter "nur Dateinamen", derselbe, den der Dialog kennt (`IFilter::BUILTIN_TITLE_ONLY`) | Alles außer `1` gilt als nicht gesetzt |
| `page` | Ganzzahl ab 1, höchstens `MAX_PAGE` = 20 | Die Anzeigeseite, 1-basiert | Alles andere gilt als 1 |
| `cursors` | Punktgetrennte Liste von Ganzzahlen, genau `page` Einträge, erster Eintrag `0`, streng aufsteigend, höchstens 20 Einträge | Der Container-Offset, an dem **jede** bisherige Anzeigeseite begann. Das letzte Element ist der Startcursor der angezeigten Seite, die vorderen Elemente sind der Rückweg | Bei jeder Abweichung fällt die Seite auf `page=1`, `cursors=0` zurück, ohne Fehlermeldung |

**Warum ein Cursorpfad und keine Rechnung aus `page`.** Eine Anzeigeseite ist eine Seite **genehmigter** Treffer. Zwischen zwei genehmigten Treffern können beliebig viele Kandidaten liegen, die der Recheck verworfen hat, und wie viele das sind, weiß niemand vorher. `offset = (page - 1) * pageSize` würde deshalb je nach Nutzer Treffer doppelt zeigen oder überspringen. Der Cursorpfad ist zustandslos, überlebt ein Lesezeichen, funktioniert ohne JavaScript und ohne Serversitzung, und der Rückweg steht darin, statt aus einer Sitzung geraten zu werden.

**Was ein alter Cursorpfad nicht kann.** Wenn sich der Index zwischen zwei Aufrufen ändert, zeigt derselbe Cursor eine andere Stelle. Ein Suchergebnis ist kein Dokument; das ist kein Defekt und wird nicht beklagt. Ein ungültiger Pfad landet still auf Seite 1, weil die Seite über die eigene Adresszeile keine Aussage macht.

### Einstiegspunkt aus der Unified Search

**Festlegung: ein zusätzlicher Ergebniseintrag am Ende der Findling-Gruppe, kein `IInAppSearch`.**

| Eigenschaft | Festlegung |
|-------------|------------|
| Wann | Genau dann, wenn die Antwort des Providers paginiert ist (`$exhausted === false`), also genau dann, wenn es mehr Treffer gibt, als der Dialog zeigt. Bei einer vollständigen Gruppe erscheint der Eintrag nicht, weil die Seite dann nichts hinzufügt |
| Wo | Immer als letzter Eintrag der Gruppe, angehängt nach `toEntries()`, nie gegen `$limit` gezählt |
| Aussehen | `title` = "Alle Treffer anzeigen", `subline` = "Öffnet die Findling-Ergebnisseite", `icon` = `icon-search` (Core-Klasse, gethemt, kein neues Asset), `thumbnailUrl` leer |
| Ziel | `IURLGenerator::linkToRoute('findling.page.index', ['query' => $term] + ($titleOnly ? ['names' => '1'] : []))`. Kein `page`, kein `cursors`: der Einstieg ist immer Seite 1 |
| Attribute | Kein `fileId`-Attribut. Der Eintrag ist kein Treffer und darf in keiner Zählung als einer auftauchen |

**Bewusst in Kauf genommen:** In NC 33 und 34 erscheint `Load more results` nur, wenn `results.length === limit`. Der angehängte Eintrag macht die Gruppe um eins länger und ersetzt dort den Nachlade-Knopf durch den Einstieg. Das ist die Richtung, die diese Phase will: eine Art zu blättern, nämlich die Seite. `SearchResult::paginated()` bleibt trotzdem die Antwortform, damit die Cursorsemantik des Dialogs unangetastet bleibt.

**Nicht gewählt:** `IInAppSearch`. Der Dialog rendert dafür in allen vier geprüften Zweigen einen Knopf "Search in Findling" ohne Klick-Handler und ohne `href`. Ein toter Knopf ist schlechter als kein Knopf.

### Anatomie der Seite, von oben nach unten

| # | Block | Immer sichtbar | Inhalt |
|---|-------|----------------|--------|
| 1 | Kopf | ja | `h1` mit dem Suchbegriff (oder dem Leerzustandstitel), darunter das Formular: Label, Suchfeld, Filter-Checkbox, Primärknopf. `<form method="get" action="/apps/findling/">` ohne `page` und ohne `cursors`, damit jede neue Suche auf Seite 1 beginnt |
| 2 | Bannerzeile | nur bei Bedarf | Hinweis "Index im Aufbau" oder der Fehlerblock. Nie beides |
| 3 | Trefferliste | wenn es Treffer gibt | `<ol>` mit einer Trefferzeile je Eintrag |
| 4 | Leerzustand | wenn es keine Treffer gibt | Symbol, Überschrift, Text. Ersetzt Block 3, steht nie daneben |
| 5 | Paginierung | wenn eine Nachbarseite existiert | Zurück, Seitenmarke, Weiter. Darunter gegebenenfalls die Zeile zur Obergrenze |

Fünf Blöcke, ein Formularfeld, ein Filter, ein Primärknopf. Das ist die ganze Seite.

---

## Trefferzeile: Anatomie

```
[Dateityp-Symbol 32px]  Rechtsmittelbelehrung.pdf                      <- 15px / 700
                        Freigaben/Recht/2026                           <- 13px / 400, maxcontrast
                        … die Rechtsmittelbelehrung ist beigefügt …    <- 15px / 400, mark auf dem Treffer
```

| Teil | Quelle | Regel |
|------|--------|-------|
| Dateityp-Symbol | `IMimeTypeDetector::mimeTypeIcon($node->getMimetype())` als `<img alt="" aria-hidden="true">`, 32 × 32 | `filter: var(--background-invert-if-dark)`, damit es im dunklen Theme sichtbar bleibt. **Keine Vorschaubilder**: eine Miniatur kostet Serverarbeit pro Treffer und würde Dateiinhalt in einen zweiten Auslieferungsweg legen, den diese Phase nicht braucht |
| Dateiname | `$node->getName()` des **bestätigten** Node, über `PlainText::bounded(…, 255)` | Nie aus der Container-Antwort. Wie im Provider: ein verwirrtes Backend darf keinen fremden Namen vor den Nutzer stellen |
| Pfad | `$userFolder->getRelativePath(...)`, `PlainText::bounded(…, 255)` | Einzeilig mit `text-overflow: ellipsis`. Der vollständige Pfad steckt im Accessible Name der Zeile (`%1$s in %2$s`), damit die Kürzung nichts unterschlägt. Kein `title`-Tooltip als einziger Träger |
| Snippet | `ExAppService::snippets()`, also erst **nach** dem Recheck geholt | Zwei Zeilen, `-webkit-line-clamp: 2` mit `overflow: hidden`. Fehlt das Snippet (Zeitbudget, stummes Backend), steht der Pfad an seiner Stelle, genau wie im Dialog. Ein Treffer ohne Auszug ist besser als kein Treffer |
| Hervorhebung | `highlights` als geprüfte Zeichen-Offsets aus `ExAppService::filterHighlights()` | Serverseitig in `<mark>` übersetzt: Text an den Offsets mit `mb_substr` zerlegt, **jedes** Stück einzeln escaped, dann zusammengesetzt. Der Renderer sortiert die Bereiche selbst nach Startwert und verwirft überlappende oder rückwärts laufende, weil `filterHighlights` Grenzen und Anzahl prüft, die Reihenfolge aber nur zusichert. Nie HTML aus der Container-Antwort übernehmen. Höchstens `MAX_HIGHLIGHTS` = 32 Bereiche |
| Verlinkung | Die ganze Zeile ist **ein** Link auf `files.View.showFile` mit der `fileid`, `target="_self"` | Ein Link je Zeile, nicht drei. Der Dateiname ist der sichtbare Linktext, Pfad und Snippet liegen im selben Link |
| Zeilen-Id | `id="findling-hit-<fileId>"` | Anker für die Rückkehr-Markierung |

Trennung zwischen zwei Zeilen: `border-block-end: 1px solid var(--color-border)`, letzte Zeile ohne. Hover und Fokus: Fläche wechselt auf `var(--color-background-hover)`, Radius `var(--border-radius-container)`.

---

## Paginierungsvertrag (Erfolgskriterium 2)

| Größe | Wert | Begründung |
|-------|------|------------|
| Seitengröße | **25 Treffer** | 25 × Overfetch 4 = 100, exakt `ExAppService::MAX_LIMIT`. Es braucht keine neue Deckelung, und `MAX_SNIPPET_IDS` = 100 wird ebenfalls nicht überschritten |
| Höchste Seite | **20** (`MAX_PAGE`) | 500 Treffer sind die Obergrenze dessen, was diese Seite ausliefert. Wer darüber hinaus sucht, sucht falsch, und die Seite sagt das statt endlos weiterzublättern |
| Bedienelemente | "Vorherige Seite" und "Nächste Seite" als tertiäre Knöpfe mit Chevron, dazwischen die Seitenmarke "Seite 3" | Beide sind gewöhnliche Links (`<a>` mit Knopf-Aussehen), damit sie ohne JavaScript funktionieren und ein Mittelklick eine neue Registerkarte öffnet |
| "Weiter" erscheint | wenn der Container `hasMore` meldet **und** `page < MAX_PAGE` | Nie "Weiter" ins Leere |
| "Zurück" erscheint | wenn `page > 1` | Ziel ist `page - 1` mit dem um ein Element gekürzten Cursorpfad |
| Obergrenze erreicht | `page == MAX_PAGE` und `hasMore` | Statt "Weiter" steht die Hinweiszeile "Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen." mit `information-outline` |
| Kurze Seite | Wenn ein Budget die Seite früh beendet, zeigt sie weniger als 25 Treffer und trotzdem "Weiter" | Die Seite erklärt das **nicht**. Jede Erklärung wäre eine Aussage über verworfene Kandidaten |

Es gibt keine Seitenzahl-Gesamtangabe ("Seite 3 von 12"), keine Trefferzahl und keinen Sprung zur letzten Seite. Alle drei bräuchten eine Summe, die niemand gemessen hat.

---

## Positions- und Rückkehrvertrag (Erfolgskriterium 3)

Drei Stufen, in dieser Reihenfolge, jede für sich ausreichend für "gleiche Suche, gleiche Seite".

| Stufe | Träger | Was sie leistet | Ohne JavaScript |
|-------|--------|-----------------|-----------------|
| 1 | Die URL | Suchbegriff, Filter, Seite und Cursorpfad stehen in der Adresse. Zurück im Browser lädt exakt dieselbe Liste | funktioniert |
| 2 | Der Browser | Die Seite ist ein gewöhnliches Dokument, also stellt der Browser die Scrollposition beim Zurück selbst wieder her. `history.scrollRestoration` wird **nicht** auf `manual` gesetzt | funktioniert |
| 3 | Die Rückkehr-Markierung | Beim Klick auf eine Trefferzeile schreibt `search.js` `sessionStorage['findling:lasthit']` mit `{key, fileId}`, wobei `key` aus Suchbegriff, Filter und Seite gebildet wird. Der Klick wird nicht abgefangen, der Link folgt normal | entfällt, ohne Verlust der Stufen 1 und 2 |

Beim `pageshow` (auch aus dem Back-Forward-Cache) liest das Skript die Markierung und handelt nur, wenn `key` zur aktuellen Seite passt:

1. Die Zeile bekommt die Klasse `findling-hit--returned`: Fläche `var(--color-background-hover)`, plus ein für Screenreader sichtbarer Text "zuletzt geöffnet" in der Zeile. Farbe allein markiert nichts.
2. `scrollIntoView({block: 'center'})` **nur**, wenn die Zeile nicht ohnehin im Sichtfeld ist. Eine vom Browser wiederhergestellte Position wird nie überschrieben.
3. Der Fokus wandert **nur dann** auf den Link der Zeile, wenn `performance.getEntriesByType('navigation')[0].type === 'back_forward'` ist. Bei einem frischen Aufruf wird kein Fokus gestohlen.

**Treffer öffnen sich in derselben Registerkarte.** Kein `target="_blank"`, keine Vorschau in einem Modal. Der Rückweg ist der Zurück-Knopf, den jeder Nutzer kennt, und der Vertrag oben macht ihn verlässlich.

---

## Zustands-Inventar

| Fall | Auslöser | Darstellung |
|------|----------|-------------|
| Kein Suchbegriff | `query` fehlt oder ist leer | Kopf mit fokussiertem Suchfeld, Leerzustand mit `magnify` (64px, `--color-text-maxcontrast`), Überschrift und Text. Keine Liste, keine Paginierung |
| Suche läuft | keiner | **Existiert nicht.** Die Seite wird serverseitig fertig gerendert. Kein Skeleton, kein Spinner, kein Ladezustand |
| Treffer vorhanden | mindestens ein genehmigter Treffer | Liste plus Paginierung |
| Keine Treffer | Liste leer, Backend hat geantwortet | Leerzustand mit `file-search-outline`, Überschrift mit dem Suchbegriff, Text mit drei konkreten nächsten Schritten. **Kein Wort über Rechte** |
| Index im Aufbau | Container meldet `degraded` | Hinweisbanner über der Liste. Die gefundenen Treffer bleiben stehen |
| Backend stumm | `searchCandidates()` liefert `null` (Timeout, Fehler, gestoppter Container) | Fehlerblock mit `alert-circle-outline`, Überschrift, Text, Knopf "Erneut versuchen" (ein Link auf dieselbe URL). **Keine leere Liste**, kein `500`, keine Nextcloud-Fehlerseite. Erfolgskriterium 5 |
| Versionsdrift | `ExAppService::driftOnRecord()` liefert einen Wert | Derselbe Fehlerblock mit eigenem Wortlaut. Keine Versionsnummern für den Nutzer, die stehen auf der Verwaltungsseite |
| Kein Home-Verzeichnis | `getUserFolder()` wirft | Fehlerblock "nicht suchbereit". Nie ungeprüfte Treffer, nie eine Exception in der Oberfläche |
| Seite jenseits der Obergrenze | `page > 20` | Stille Rückkehr auf Seite 1 mit demselben Suchbegriff |
| Ungültiger Cursorpfad | Länge, Reihenfolge oder Startwert passen nicht | Stille Rückkehr auf Seite 1 mit demselben Suchbegriff |
| Snippet fehlt | Zeitbudget erschöpft oder Backend antwortet nur teilweise | Der Pfad steht an der Stelle des Snippets. Kein Platzhalter, kein "kein Auszug verfügbar" |

---

## Interaktionsvertrag

### Erstes Rendern ohne JavaScript

Die vollständige Seite, alle Treffer, die Paginierung, das Formular und jeder Zustandsblock werden serverseitig mit echten Werten gerendert. Mit abgeschaltetem JavaScript verliert die Seite genau eine Sache: die Rückkehr-Markierung aus Stufe 3. Suchen, Blättern, Filtern, Öffnen und Zurückkehren funktionieren vollständig.

### Was `search.js` tun darf

| Erlaubt | Verboten |
|---------|----------|
| Die Rückkehr-Markierung schreiben und lesen | Markup bauen. Jedes Element der Seite existiert bereits im Template |
| Eine Klasse setzen, `scrollIntoView` rufen, Fokus setzen | Treffer nachladen, Endlos-Scrollen, eine zweite Suchroute rufen |
| Auf `pageshow` und `click` hören | Ein Klick auf eine Trefferzeile abfangen oder `preventDefault` rufen |
| Auf `sessionStorage` zugreifen | `history.scrollRestoration = 'manual'` setzen, `history.pushState` für die Paginierung verwenden |

Es gibt **kein Polling** auf dieser Seite. Die Verwaltungsseite pollt, weil sie einen laufenden Vorgang beobachtet; ein Suchergebnis ist eine Antwort auf eine Frage, keine Beobachtung.

### Responsive

| Breite | Verhalten |
|--------|-----------|
| ab 1024px | Inhalt 900px breit, mittig, Seitenrand 32px |
| unter 1024px | Seitenrand 16px, Inhalt volle Breite |
| unter 640px | Formular einspaltig (Feld, Filter, Knopf untereinander, Knopf volle Breite). Trefferzeile: Symbol und Dateiname in einer Zeile, Pfad und Snippet darunter über die volle Breite. Paginierungsknöpfe je 50 Prozent breit |
| `pointer: coarse` | Mindesthöhe von Trefferzeile und Paginierungsknöpfen 44px |

---

## Barrierefreiheit

| Anforderung | Umsetzung |
|-------------|-----------|
| Farbe nie allein | Jeder Zustandsblock trägt Symbol plus Überschrift plus Text. Die Rückkehr-Markierung trägt zusätzlich den Text "zuletzt geöffnet" für Screenreader. Die Snippet-Hervorhebung ist ein `<mark>`, also auch semantisch eine Hervorhebung |
| Kontrast | Nur Nextcloud-Farbpaare Fläche zu Text, kein eigener Hexwert. Damit gelten in allen Themes die vom Core geprüften Verhältnisse |
| Überschriftenhierarchie | Genau eine `h1` (die Ergebnis- oder Leerzustandsüberschrift). Trefferzeilen sind Listeneinträge, keine Überschriften |
| Liste | Eine `<ol>` mit `aria-label="Suchergebnisse"`. Die Reihenfolge ist eine Rangfolge, deshalb geordnet und nicht `<ul>` |
| Ein Link je Treffer | Die ganze Zeile ist ein Link mit dem Accessible Name `%1$s in %2$s`. Kein zweiter Fokusstopp je Zeile, kein Link im Link |
| Beschriftung | `<label for>` am Suchfeld und an der Filter-Checkbox. Der Platzhalter ist ein Beispiel, nie das Label |
| Klickflächen | Mindestens `var(--default-clickable-area)` (34px), unter `pointer: coarse` 44px |
| Fokus | Core-Fokusring unangetastet. Kein `outline: none` im eigenen CSS. Beim Zurück wandert der Fokus auf den zuletzt geöffneten Treffer, damit ein Tastaturnutzer nicht am Seitenanfang neu beginnt |
| Symbole | `aria-hidden="true"` und `focusable="false"` an jedem Inline-SVG, `alt=""` am Dateityp-Bild |
| Live-Bereiche | **Keine.** Die Seite lädt vollständig neu, es gibt nichts, was sich unter dem Nutzer verändert |
| Sprache | Alle Texte durch `$l->t()`. Keine hartcodierte Sprache im Template |
| Dark Mode und Hoher Kontrast | Automatisch, weil ausschließlich Variablen verwendet werden. Das Dateityp-Symbol trägt zusätzlich `filter: var(--background-invert-if-dark)`. Sichtprobe in Hell, Dunkel und Hoher Kontrast gehört zur Abnahme |
| Tastatur | Formular, Filter, Trefferliste und Paginierung sind in Dokumentreihenfolge erreichbar. Kein Tastaturfang, kein eigener Shortcut, kein `tabindex` größer als 0 |

---

## Verbote

Die mit **[G]** markierten Punkte sind als Text prüfbar und gehören in ein Gate nach dem Muster von `backend/tests/test_admin_ui_contract.py`.

- **[G]** Kein npm, kein Build-Step, kein Vue, kein Bundle in der Companion-App.
- **[G]** Kein Hexwert, kein `rgb()`, kein `hsl()` in `php/css/search.css`. Nur `var(--…)`.
- **[G]** Kein Emoji, nirgends. Symbole nur als SVG.
- **[G]** Kein Em-Dash und kein En-Dash in Nutzertexten.
- **[G]** Kein Inline-`<script>`, kein `style`-Attribut.
- **[G]** Kein unescaped Ausdrucken im Template. Jeder Wert läuft durch `p()`, jede Zeichenkette durch `$l->t()`.
- **[G]** Kein Markup aus Zeichenketten in `php/js/search.js` (`innerHTML`, `insertAdjacentHTML`, `outerHTML`, `document.write`).
- **[G]** Kein `outline: none` im eigenen CSS.
- **[G]** `IInAppSearch` kommt in keiner PHP-Datei der App vor.
- Kein Dateiname und kein Pfad aus einer Container-Antwort. Beide entstehen ausschließlich aus dem bestätigten Node.
- Kein HTML aus einer Container-Antwort. Highlights sind Offsets und werden serverseitig in `<mark>` übersetzt, nie übernommen.
- Kein Satz, keine Zahl und kein Symbol, aus dem sich ableiten lässt, dass Treffer wegen fehlender Rechte verschwunden sind.
- Keine Gesamttrefferzahl, keine Seitenanzahl, kein Sprung zur letzten Seite.
- Kein Skeleton, kein Spinner, kein Ladezustand.
- Kein Endlos-Scrollen, kein Nachladen von Treffern per JavaScript.
- Keine Vorschaubilder und keine Miniaturen von Dateiinhalten.
- Kein `target="_blank"` und kein Modal für einen Treffer.
- Kein zweiter Suchweg. Die Seite ruft denselben Dienst wie der Provider (siehe nächster Abschnitt).

---

## Grenzen zu anderen Verträgen

Diese vier Punkte liegen außerhalb der Gestaltung, hängen aber an ihr und gehören in die Planung, sonst kann die Seite nicht gebaut werden.

| Punkt | Befund | Was daraus folgt |
|-------|--------|------------------|
| Dritte Routenklasse | `backend/tests/test_php_trust_boundary.py` kennt zwei Klassen: `ApiRoute` (ExApp) und `FrontpageRoute` (Admin). `FORBIDDEN_ON_ADMIN_ROUTE` enthält `NoAdminRequired`, `PublicPage` und `NoCSRFRequired`. Die Seitenroute braucht die ersten beiden davon zwingend | Gate B lernt eine dritte Klasse "Nutzerseite": `FrontpageRoute` plus `NoAdminRequired` plus `NoCSRFRequired`, verboten bleiben `PublicPage` und `ExAppRequired`. Die Klasse wird an der Methode erkannt, nicht am Dateinamen, und die Selbsttests des Gates bekommen ein sauberes und ein schmutziges Muster wie die beiden bestehenden Klassen |
| Eine Sicherheitsgrenze, nicht zwei | UI-03 und Erfolgskriterium 4 verlangen denselben Vorfilter und denselben finalen PHP-Recheck | Die Recheck-Schleife aus `Provider::search()` (Vorfilter über `IUserMountCache` und `IFileAccess`, `getFirstNodeById`, `isReadable`, Titel und Pfad aus dem Node, Snippet erst danach) zieht in **einen** Dienst, den Provider und Seite beide rufen. Die Seite reicht eigene Werte für Seitengröße und Zeitbudget hinein und bringt keine eigene Entscheidung mit. Ein Gate nach dem Muster von `test_semantic_boundary.py` zählt die Aufrufstellen |
| Paritätstest | Der CI-Job `search-parity` in `.github/workflows/integration.yml` (Zeile 2611) vergleicht über `scripts/ci/parity_diff.py` | Erfolgskriterium 4 verlangt, dass derselbe Job die neue Route mitprüft: gleiche Frage, gleicher Nutzer, gleiche Menge Dateien über den Dialogweg und über die Seitenroute |
| Attribution | `THIRD-PARTY.md` führt neun MDI-Namen und die Prüfzeile am Dateiende | Die drei neuen Namen kommen in dieselbe Zeile und in dieselbe Prüfschleife, in dem Plan, der sie zuerst rendert |

---

## Abnahme-Sichtproben

Gegen `docs/dev-setup.md` (Port 8090, `testuser`/`kollegin`, Testkorpus), zusätzlich `scripts/ci/slow_backend.py` für die stumme Hälfte.

1. Suche im Dialog nach einem Begriff mit mehr Treffern als der Dialog zeigt: der Eintrag "Alle Treffer anzeigen" steht als letzter in der Findling-Gruppe und führt auf die Seite mit demselben Suchbegriff.
2. Suche mit wenigen Treffern: der Einstiegs-Eintrag erscheint **nicht**.
3. Auf der Seite zweimal "Nächste Seite", dann zweimal "Vorherige Seite": dieselben Treffer in derselben Reihenfolge, keine Dublette, keine Lücke, der Suchbegriff steht unverändert im Feld.
4. Auf Seite 3 einen Treffer öffnen, in der Dateiliste umsehen, Zurück: dieselbe Seite 3, dieselbe Suche, dieselbe Scrollposition, der geöffnete Treffer markiert, der Fokus auf ihm.
5. Dasselbe mit abgeschaltetem JavaScript: dieselbe Seite 3, dieselbe Suche, Scrollposition vom Browser, keine Markierung, keine Fehlermeldung.
6. Die Adresse von Seite 3 als Lesezeichen speichern, Browser schließen, Lesezeichen öffnen: Seite 3 erscheint, ohne CSRF-Fehler.
7. `cursors` in der Adresse von Hand verfälschen: Seite 1 derselben Suche, keine Fehlerseite, keine Ausnahme im Log.
8. Zwei Nutzer, eine geteilte und eine nicht geteilte Datei mit demselben Suchwort: die Seite zeigt beiden genau das, was der Dialog ihnen zeigt, und sagt nirgends etwas über die fehlende Datei.
9. Backend gestoppt: Fehlerblock mit Überschrift, Text und "Erneut versuchen". Keine leere Liste, keine Nextcloud-Fehlerseite, keine Ausnahme im Log.
10. Backend künstlich verlangsamt: die Seite antwortet mit dem, was sie hat, und der Fehlerblock erscheint nur, wenn nichts kam.
11. Versionsdrift zwischen den Hälften erzeugen: der eigene Fehlerblock erscheint, ohne Versionsnummern zu nennen.
12. Suche ohne Treffer: Leerzustand mit Suchbegriff und drei nächsten Schritten, kein Wort über Rechte.
13. Seite ohne Suchbegriff aufrufen (über den Navigationseintrag): Leerzustand, Fokus im Suchfeld.
14. Suchbegriff mit `<script>`, mit Umlauten und mit 300 Zeichen: escaped ausgegeben, auf 255 gekürzt, kein Layoutbruch.
15. Datei mit Umlauten im Treffertext: die `<mark>`-Hervorhebung sitzt auf dem richtigen Wort (Zeichen-Offsets, nicht Byte-Offsets).
16. Dunkles Theme und Hoher Kontrast: kein unsichtbares Dateityp-Symbol, kein Text unter 4.5:1, die Hervorhebung bleibt lesbar.
17. Tastatur allein: Formular, Filter, alle 25 Treffer, beide Paginierungsknöpfe erreichbar, Fokusring überall sichtbar.
18. Screenreader über eine Trefferzeile: Dateiname, "in", vollständiger Pfad, danach das Snippet.
19. Handybreite (unter 640px): Formular einspaltig, Paginierungsknöpfe je halbe Breite, kein waagerechtes Scrollen.
20. Seite auf Englisch und auf Deutsch: keine unübersetzte Zeichenkette, keine abgeschnittene Beschriftung.

---

## Offene Punkte für die Planung

Keiner davon ist eine Gestaltungsfrage, alle sind Folgen dieses Vertrags.

1. **Der geteilte Recheck-Dienst** ist der erste Schritt der Phase und muss vor der Seite stehen. Wird die Seite zuerst gebaut, entsteht die zweite Sicherheitsfläche, die UI-03 verbietet.
2. **Gate B braucht die dritte Routenklasse**, bevor der erste `PageController` existiert, sonst steht der Baum zwischendurch rot. Das ist genau die Reihenfolge, die Phase 4 für die zweite Klasse gewählt hat.
3. **`fr.json`**: die App liefert heute nur einen deutschen Katalog. Ob Phase 9 den französischen anlegt oder ob das ein eigener Schritt vor der Store-Abgabe wird, ist eine Owner-Entscheidung. Die Wortlaute stehen in der Copy-Tabelle bereit.
4. **Zeitbudget der Seitenroute**: der Provider fährt 2,5 Sekunden, weil der Dialog alle Anbieter parallel abwartet. Die Seite wartet auf niemanden. Ein eigener, größerer Deckel ist zulässig, gehört aber gemessen und benannt, nicht geraten.
5. **`php/img/app.svg`** existiert noch nicht und wird für den Navigationseintrag gebraucht.

---

## Herkunft der Festlegungen

| Quelle | Übernommene Entscheidungen |
|--------|---------------------------|
| ROADMAP.md Phase 9 | Alle fünf Erfolgskriterien wörtlich abgebildet: Einstieg (1) auf den Ergebniseintrag, Paginierung (2) auf den Cursorpfad, Öffnen und Zurück (3) auf den dreistufigen Rückkehrvertrag, ACL-Parität (4) auf den geteilten Dienst, stummes Backend (5) auf den Fehlerblock. Die dort benannte offene Frage "Paginierung gegen ACL-Recheck" ist mit dem Cursorpfad beantwortet |
| REQUIREMENTS.md | UI-01 Kopf, Liste und Paginierung. UI-02 Rückkehrvertrag. UI-03 Verbote und Abschnitt "Grenzen zu anderen Verträgen" |
| 04-UI-SPEC.md (Phase 4) | Fortgeschrieben statt neu erfunden: keine eigene Palette, `calc(var(--default-grid-baseline) * n)`, zwei Schriftstärken, MDI als Inline-SVG mit gepinntem Commit, Verbotsliste als prüfbares Gate, kein Build-Step |
| `php/lib/Search/Provider.php` | Sicherheitsreihenfolge, Herkunft von Titel und Pfad, Verhalten bei Versionsdrift und fehlendem Home-Verzeichnis, `paginated` gegen `complete` |
| `php/lib/Service/ExAppService.php` | Seitengröße 25 aus `MAX_LIMIT` 100, Snippet-Deckel, Highlights als geprüfte Zeichen-Offsets und die Lücke in ihrer Reihenfolgezusicherung |
| `php/css/admin.css`, `php/templates/admin.php`, `php/js/admin.js` | Der gesamte Bauweise-Vertrag der Companion-App |
| Nextcloud stable33, stable34, stable35 | Jede Variable, jede Klasse und jede API in der Verifikationstabelle unter "Design System", gelesen am 08.09.2026 |
| CLAUDE.md und globale Regeln | Keine Emojis, keine Em-Dashes, echte Umlaute in deutscher Prosa, ASCII in Bezeichnern, kurze Nutzertexte |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
