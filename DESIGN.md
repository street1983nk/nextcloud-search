---
name: Findling
description: Volltext-, OCR- und semantische Suche für Nextcloud, gestaltet als Teil der Nextcloud-Oberfläche ohne eigene Marke.
colors:
  color-primary-element: "#00679e"
  color-primary-element-text: "#ffffff"
  color-main-background: "#ffffff"
  color-main-text: "#222222"
  color-text-maxcontrast: "#6b6b6b"
  color-background-hover: "#f5f5f5"
  color-border: "#ededed"
  color-error: "#ffe7e7"
  color-error-text: "#8a0000"
  color-element-error: "#c90000"
  color-warning: "#ffeec5"
  color-warning-text: "#664700"
  color-element-warning: "#bf7900"
  color-success: "#d8f3da"
  color-success-text: "#005416"
  color-element-success: "#099f05"
  color-info: "#d5f1fa"
  color-info-text: "#0066ac"
  color-element-info: "#0077c7"
typography:
  headline:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Oxygen-Sans, Cantarell, Ubuntu, 'Helvetica Neue', 'Noto Sans', 'Liberation Sans', Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.2
  figure:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Oxygen-Sans, Cantarell, Ubuntu, 'Helvetica Neue', 'Noto Sans', 'Liberation Sans', Arial, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Oxygen-Sans, Cantarell, Ubuntu, 'Helvetica Neue', 'Noto Sans', 'Liberation Sans', Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Oxygen-Sans, Cantarell, Ubuntu, 'Helvetica Neue', 'Noto Sans', 'Liberation Sans', Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.5
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Oxygen-Sans, Cantarell, Ubuntu, 'Helvetica Neue', 'Noto Sans', 'Liberation Sans', Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  small: "4px"
  element: "8px"
  container: "12px"
spacing:
  baseline: "4px"
  2x: "8px"
  4x: "16px"
  6x: "24px"
  8x: "32px"
  12x: "48px"
  clickable-area: "34px"
  coarse-pointer: "44px"
  reading-column: "900px"
components:
  button-primary:
    backgroundColor: "{colors.color-primary-element}"
    textColor: "{colors.color-primary-element-text}"
    rounded: "{rounded.element}"
    height: "{spacing.clickable-area}"
  chip-filter:
    backgroundColor: "{colors.color-main-background}"
    textColor: "{colors.color-main-text}"
    rounded: "{rounded.small}"
    padding: "0 8px"
    height: "{spacing.clickable-area}"
  chip-status:
    backgroundColor: "{colors.color-background-hover}"
    textColor: "{colors.color-main-text}"
    rounded: "{rounded.small}"
    padding: "4px 8px"
  banner-error:
    backgroundColor: "{colors.color-error}"
    textColor: "{colors.color-error-text}"
    rounded: "{rounded.container}"
    padding: "16px"
  banner-info:
    backgroundColor: "{colors.color-info}"
    textColor: "{colors.color-info-text}"
    rounded: "{rounded.container}"
    padding: "16px"
  hit-row:
    backgroundColor: "{colors.color-main-background}"
    textColor: "{colors.color-main-text}"
    rounded: "{rounded.container}"
    padding: "16px"
  hit-row-hover:
    backgroundColor: "{colors.color-background-hover}"
  tile:
    backgroundColor: "{colors.color-background-hover}"
    textColor: "{colors.color-main-text}"
    rounded: "{rounded.container}"
    padding: "16px"
---

# Design System: Findling

## Overview

**Creative North Star: "Ein Werkzeug aus dem Kern"** (Vorschlag, vom Owner zu bestätigen)

Findling hat kein eigenes Erscheinungsbild und soll keins bekommen. Die Ergebnisseite (`php/templates/search.php`) und die Verwaltungsseite (`php/templates/admin.php`) sollen aussehen, als kämen sie aus dem Nextcloud-Server selbst, und jedes Theming mitmachen: Akzentfarbe des Admins, hell, dunkel, hoher Kontrast. Jede Farbe, jeder Radius und jeder Abstand kommt aus einer CSS-Variable des Servers; die Hex-Werte im Frontmatter sind nur die Referenzwerte des Standard-Themes (hell, Primärfarbe `#00679e`, Stand `apps/theming` stable32) und gehören nie in den Code.

Der Stack ist bewusst schlicht: PHP-Templates, Vanilla-JS, zwei CSS-Dateien unter `php/css/`, keine Vue-Komponenten, kein Build-Schritt. Die Ergebnisseite ist ohne JavaScript vollständig (Suchen, Blättern, Filtern, Zurückkehren), deshalb gibt es dort keinen Ladezustand und kein Skelett. Die Dichte ist die einer Verwaltungsoberfläche: eine Lesespalte, ruhige Flächen, Zustände über die Statuspaare des Themes.

Ziel ist Konformität, nicht Ausdruck. Ambition zeigt sich in Präzision: sichtbares Raster, geprüfte Kontrastpaare, Fokus nie entfernt, Pfade nie abgeschnitten, wo sie die eigentliche Information sind.

**Key Characteristics:**
- Nur Nextcloud-CSS-Variablen, kein einziger Farbliteralwert in `php/css/`.
- 4-px-Raster als sichtbare Rechnung: `calc(var(--default-grid-baseline) * n)`.
- Eine Lesespalte von 900 px für beide Seiten der App.
- Zwei Schriftgewichte (400, 700), Schrift des Servers, keine Webfonts.
- Flach: keine Schatten, Tiefe nur über die Hover-Fläche.
- MDI-Icons als Inline-SVG-Pfaddaten aus dem gepinnten Upstream-Commit (siehe THIRD-PARTY.md).

## Colors

Die Palette ist die des Servers: neutrale Flächen, eine Akzentfarbe des Admins und vier Statuspaare, jeweils als Fläche plus geprüfte Textfarbe.

### Primary
- **Theming-Akzent** (`--color-primary-element`, Text darauf `--color-primary-element-text`): ausschließlich für die eine Hauptaktion pro Bereich, auf der Ergebnisseite der Suchknopf (Server-Klasse `primary`). Auf der Ergebnisseite zusätzlich als Rahmen des aktiven Filter-Chips.
- **Heller Akzent** (`--color-primary-element-light` mit `--color-primary-element-light-text`): für Zustände, nicht für Aufforderungen. Aktiver Filter-Chip und die Hervorhebung `mark` im Trefferauszug. Kein fester Referenzwert, der Server leitet ihn aus dem Akzent ab.

### Neutral
- **Seitengrund** (`--color-main-background`): Fläche der Lesespalte und der Trefferzeilen in Ruhe.
- **Haupttext** (`--color-main-text`): aller Fließtext, Dateinamen, Links in Satzform.
- **Gedämpfter Text** (`--color-text-maxcontrast`): Pfade, Datumszeile, Filterbeschriftungen, Seitenmarke, Einheiten. Hält 4,5:1 auch auf der Hover-Fläche.
- **Hover-Fläche** (`--color-background-hover`): Hover und Fokus aller Zeilen und Links, Rückkehrmarke, Kacheln, Statuschips, Karten und Blätterleiste.
- **Trennlinie** (`--color-border`): Linie zwischen Treffern, Rahmen der Filter-Chips, Zeilen der Ausschlussliste.

### Statuspaare
- **Fehler** (`--color-error` / `--color-error-text`, Icon `--color-element-error`): Fehlerbanner, Fehlerchips, die einzige destruktive Bestätigung (neuer Ausschluss).
- **Warnung** (`--color-warning` / `--color-warning-text`, Icon `--color-element-warning`): übersprungene und gekürzte Dateien, Profilurteil "knapp".
- **Erfolg** (`--color-success` / `--color-success-text`, Icon `--color-element-success`): indexiert, Profil passt, gespeichert.
- **Hinweis** (`--color-info` / `--color-info-text`, Icon `--color-element-info`): Info-Banner, Hinweis zur Neuindexierung, Hinweiszeile am Listenende.

### Named Rules
**The Pair Rule.** Fläche und Text eines Status werden immer als das Paar gesetzt, das der Server ausliefert, nie gemischt. Das Paar trägt den geprüften Kontrast in hell, dunkel und hohem Kontrast.

**The Strong Accent Once Rule.** Der volle Akzent gehört der einen Aktion, die die Seite weiterbringt. Zustände bekommen den hellen Akzent.

**The Never Color Alone Rule.** Farbe ist nie der einzige Träger: jeder Banner hat Icon und Satz, jeder aktive Chip ein Schließsymbol und `aria-current`, die Rückkehrmarke einen Satz für Screenreader.

## Typography

**Body Font:** Schrift des Servers über `--font-face` (system-ui und Fallbacks); Findling setzt keine eigene Familie.
**Mono:** die Monospace des Servers in `code`, ohne eigene Größe.

**Character:** Systemschrift, zwei Gewichte, wenige Größen. Rang entsteht über Gewicht, nicht über zusätzliche Größen.

### Hierarchy
- **Headline** (700, 20 px, 1.2): die eine h1 der Ergebnisseite und die Überschrift des leeren Zustands. Lange Suchbegriffe brechen um (`overflow-wrap: anywhere`).
- **Figure** (700, 28 px, 1.2): nur die Abdeckungszahl auf der Verwaltungsseite.
- **Title** (700, `--default-font-size` 15 px, `--default-line-height`): Dateiname eines Treffers, Unterüberschriften der Verwaltungsseite (der Server setzt Überschriften auf inherit, das Gewicht muss ausgeschrieben werden).
- **Body** (400, 15 px, 1.5): Fließtext, Trefferauszug (zwei Zeilen, dann Schnitt), Banner.
- **Label** (400, `--font-size-small` 13 px, 1.5): Pfad, Datumszeile, Seitenmarke, Filterbeschriftung, Chips, Tabellenkopf.

### Named Rules
**The Three Sizes Rule.** Auf der Ergebnisseite gibt es genau drei Größen (15, 13, 20) und auf der Verwaltungsseite zusätzlich die 28 der Abdeckungszahl. Keine Gewichtsstufe 600.

## Layout

Eine zentrierte Lesespalte mit `max-width: 900px`, gleich breit wie die h2 eines Einstellungsblocks im Kern, damit beide Seiten der App ein Maß teilen. Seitenabstand 32 px (8 Raster) ab 1024 px, 16 px (4 Raster) darunter. Senkrechter Rhythmus der Ergebnisseite: 24 px (6 Raster) zwischen den Blöcken Kopf, Banner, Filterzeilen, Trefferliste, Blätterleiste.

Alle eigenen Abstände sind Vielfache von `--default-grid-baseline` (4 px), als `calc()` geschrieben, damit das Vielfache sichtbar bleibt. Die drei benannten Ausnahmen: 900 px Lesespalte, 44 px Klickfläche bei grobem Zeiger, 32 px Breite der Icon-Spalte für die Einrückung des Links "Ähnliche Dokumente".

Haltepunkte:
- **unter 640 px:** Formular einspaltig, Suchknopf volle Breite, Filterbeschriftung über ihren Chips, Chips brechen um (bewusst keine seitlich scrollende Leiste), Dateiname neben dem Icon, Pfad und Auszug darunter über die volle Breite, Blätterlinks je halbe Breite.
- **640 bis 1023 px:** volle Breite, halber Seitenabstand.
- **ab 1024 px:** 900-px-Spalte, zentriert.
- **`pointer: coarse`:** alle Chips, Trefferzeilen und Blätterlinks mindestens 44 px hoch.

`#app-content` ist Scroll-Container des Servers und wird nicht gestylt.

## Elevation & Depth

Findling ist flach. Es gibt keinen einzigen `box-shadow`. Tiefe und Zustand entstehen tonal: Ruhe auf `--color-main-background`, Hover und Fokus auf `--color-background-hover`; auf der Blätterleiste, die selbst schon die Hover-Fläche trägt, kehrt es sich um (Hover auf Seitengrund).

**The Flat Rule.** Keine Schatten, keine Verläufe, kein Glas. Ein Zustandswechsel ist ein Flächenwechsel.

## Shapes

Radien nur über die Server-Variablen: `--border-radius-small` (4 px) für Chips, Satz-Links und die `mark`-Hervorhebung; `--border-radius-element` (8 px) für den Dokumentationsknopf im Banner; `--border-radius-container` (12 px) für Trefferzeilen, Banner, Karten, Kacheln und die Blätterleiste. Rahmen 1 px in `--color-border`, nur an Filter-Chips, Trennlinien und Listenzeilen. Kein Karten-in-Karten-Schachteln.

## Components

### Buttons
- **Shape:** Server-Knopf mit `--border-radius-element`, Höhe mindestens `--default-clickable-area`.
- **Primary:** nur der Suchknopf (Server-Klasse `primary`) mit MDI-Lupe, 16 px. Findling entscheidet nichts an der Akzentfarbe.
- **Destruktiv:** der bestätigende Knopf beim Anlegen eines Ausschlusses, `--color-element-error` mit `--color-primary-element-text`; die Gegenwahl bleibt ein schlichter Server-Knopf.
- **Icon-only:** nur der Entfernen-Knopf einer Ausschlusszeile, mit `aria-label` inklusive Pfad, mindestens `--default-clickable-area` breit und hoch.
- **Banner-Link als Knopf:** 2 px `currentColor`-Rahmen, fett, erbt das Textpaar des Banners (Owner-Entscheid 19.10.2026).

### Chips
- **Filter-Chip (Link):** Seitengrund, 1 px Rahmen, `--border-radius-small`, Label-Größe, volle Klickhöhe, ohne Unterstreichung.
- **Aktiv:** Rahmen im Akzent, Fläche und Text im hellen Akzentpaar, Schließsymbol, `aria-current`.
- **Statuschip (Verwaltung):** Hover-Fläche, Icon gedämpft; Urteile über die Statuspaare (Fehler, Warnung, Erfolg); "ausgeschlossen" und "unbekannt" bleiben neutral.

### Cards / Containers
- **Banner:** Icon auf der ersten Textzeile, Statuspaar als Fläche, `--border-radius-container`, Innenabstand 24 px auf der Ergebnisseite, 16 px auf der Verwaltungsseite.
- **Kacheln und Ergebniskarte:** Hover-Fläche, Container-Radius, 16 px Innenabstand, keine Schatten, keine Rahmen.

### Inputs / Fields
- **Style:** native Felder mit Server-Styling, Beschriftung in Label-Größe über dem Feld, Höhe mindestens `--default-clickable-area`.
- **Fehler:** ein Satz direkt am Feld in `--color-error-text` auf normaler Fläche, keine gefüllte Fehlerfläche für eine Feldmeldung.
- **Rückmeldung beim Speichern:** inline als Erfolgs- oder Fehlerfläche, nie als Toast.

### Navigation
- **Sortierung:** Satzlinks ohne Rahmen und Fläche, aktiv in 700 plus `aria-current`.
- **Zurücksetzen und Zurück:** unterstrichene Satzlinks, keine Kästen.
- **Blätterleiste:** Streifen auf der Hover-Fläche, echte Links mit Chevron-Icons (funktionieren ohne Skript, Mittelklick öffnet Tab), Seitenmarke gedämpft in der Mitte.

### Trefferzeile (Signature)
Die ganze Zeile ist ein Link (ein Tabstopp pro Treffer): Dateityp-Icon des Servers mit `filter: var(--background-invert-if-dark)`, Dateiname fett, Pfad einzeilig mit Auslassung (voller Pfad im zugänglichen Namen), optional Datumszeile, Auszug auf zwei Zeilen begrenzt mit `mark`-Hervorhebung. Der Link "Ähnliche Dokumente" ist ein Geschwister der Zeile, nie darin verschachtelt, mit eigenem sichtbaren Fokusring.

### Fehlerliste und Pfade (Verwaltung)
Tabelle mit gedämpftem Kopf auf Hover-Fläche, Gruppen durch Trennlinien. Pfade brechen um und werden nie gekürzt, weil sie dort die eigentliche Information sind.

## Do's and Don'ts

### Do:
- **Do** jede Farbe, jeden Radius und jede Klickfläche über die Nextcloud-Variable setzen (`--color-*`, `--border-radius-*`, `--default-clickable-area`).
- **Do** Abstände als `calc(var(--default-grid-baseline) * n)` schreiben.
- **Do** Statusflächen immer als Server-Paar setzen (Fläche plus `-text`, Icon in `--color-element-*`).
- **Do** neue Icons als MDI-Pfaddaten aus dem gepinnten Commit übernehmen und in THIRD-PARTY.md nachführen.
- **Do** jeden sichtbaren Text über `$l->t()` bzw. `t('findling', ...)` führen, Fremdwerte nur über `p()` ausgeben.
- **Do** neue Ansichten in hell, dunkel und hohem Kontrast bei 375, 768 und 1280 px prüfen (nextcloud-ui-Skill).
- **Do** für 13 px künftig `var(--font-size-small)` schreiben; `admin.css` nutzt an mehreren Stellen noch das Literal `13px` (gleicher Wert, kein Theme-Bezug).

### Don't:
- **Don't** Hex-, RGB- oder benannte Farben in `php/css/` schreiben, auch nicht die Referenzwerte aus diesem Dokument.
- **Don't** Vue-Komponenten, Webfonts, Verläufe, Glas, dekorative Schatten oder Karten in Karten einführen.
- **Don't** einen Fokusring entfernen oder `outline: none` setzen.
- **Don't** Inline-Skripte oder `style`-Attribute in Templates (CSP des Servers, Theme würde ignoriert).
- **Don't** `!important` gegen Server-Styles; einzige geduldete Stelle ist die Regel, die `[hidden]` innerhalb der eigenen Blöcke seine Bedeutung zurückgibt.
- **Don't** Pfade in Diagnose- oder Ausschlusslisten kürzen oder per `title` verstecken.
- **Don't** auf der Ergebnisseite Ladezustände oder Skelette einbauen; die Seite wird serverseitig vollständig gerendert.
