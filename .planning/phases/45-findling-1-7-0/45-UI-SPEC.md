---
phase: 45
slug: findling-1-7-0
status: approved
shadcn_initialized: false
preset: none
created: 2026-11-21
reviewed_at: 2026-11-21
---

# Phase 45: UI Design Contract

> Visueller und Interaktionsvertrag für die Änderungen an der Verwaltungsseite (Block "Rules and limits") in Findling 1.7.0. Erstellt vom gsd-ui-researcher, geprüft vom gsd-ui-checker.
> Grundlage: `DESIGN.md` (bindend, wird hier nicht wiederholt, nur angewendet), `45-CONTEXT.md` D-45-01 bis D-45-16 (gesperrt), bestehender Code `php/templates/admin.php`, `php/js/admin.js`, `php/css/admin.css`.

---

## Geltungsbereich

| Teil | UI-Änderung | Quelle |
|------|-------------|--------|
| EXCL-04 | Neue Liste der Admin-Speicher unter dem Schalter "Index external storage", neue Zeile in der Inline-Bestätigung | D-45-01 bis D-45-06 |
| EXCL-05 | Zähler freier Plätze unter Ordner- und Musterliste | D-45-07 |
| EXCL-06 | Neue Feldmeldung für * oder ? im Ordnerfeld, Markierung alter Ordnereinträge mit * oder ?, geschärfte Meldung no_wildcard | D-45-08, D-45-09 |
| KAT-03, KAT-04 | Keine neue Oberfläche; zh_TW-Katalog (PR #56) und Locale-Rückfall in `admin.js` (PR #57) werden gemergt, die neue UI baut darauf auf | D-45-11, D-45-12 |
| STORE-03, STORE-04 | Keine UI. Einzige Vorgabe: der Entwurf der kurzen Store-Texte wird dem Owner kurz vor dem Release gezeigt, Einbau erst nach Freigabe | D-45-13, D-45-14 |
| REL-07 | Keine neue UI; Prüfmethode siehe Abschnitt "Abnahme und Prüfung" | D-45-15 |

Nicht in dieser Phase: Erhöhung der 64 Plätze, persönliche Nutzer-Speicher einzeln in der Liste (D-45-03), Sofort-Anstoß oder Fortschrittsanzeige beim Wiederzulassen (D-45-05).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Nextcloud-PHP-Template, Vanilla-JS, kein Build-Schritt; shadcn nicht anwendbar, kein React) |
| Preset | not applicable |
| Component library | none; native Nextcloud-Serverstile (`.checkbox`, `button`, `button.primary`, `.settings-hint`, `.section`) |
| Icon library | Material Design Icons als Inline-SVG-Pfaddaten aus dem gepinnten Commit (THIRD-PARTY.md); in dieser Phase nur bereits vorhandene Pfade (`$alertIcon` alert-circle-outline, `$closeIcon`) |
| Font | Serverschrift über `--font-face`, keine eigene Familie, keine Webfonts |

Regel: kein einziger Farb-, Radius- oder Pixelliteralwert neu in `php/css/admin.css`; alles über `--color-*`, `--border-radius-*`, `--default-clickable-area`, `calc(var(--default-grid-baseline) * n)`. Neue 13-px-Stellen schreiben `var(--font-size-small)`.

---

## Spacing Scale

Raster 4 px über `--default-grid-baseline`, geschrieben als `calc(var(--default-grid-baseline) * n)`:

| Token | Value | Usage in dieser Phase |
|-------|-------|-------|
| xs | 4px (×1) | Abstand Checkbox zu Label (wie `.findling-rules__toggle`), Abstand Zähler zur Liste darüber, Feldfehler `margin-block` |
| sm | 8px (×2) | Abstand Pfad zu Typ-Angabe in einer Speicherzeile, `margin-block` der Speicherliste, Abstand Markierungssatz unter einem alten Ordnereintrag |
| md | 16px (×4) | Einzug der Speicherliste unter dem Schalter (`padding-inline-start`), Abstand der Listenbeschriftung nach oben (wie `.findling-rules__label`), Innenabstand und `margin-block` der Inline-Bestätigung |
| lg | 24px (×6) | unverändert: Banner-Innenabstand der Ergebnisseite, hier nicht genutzt |
| xl | 32px (×8) | unverändert: Seitenabstand ab 1024 px |
| 2xl | 48px (×12) | nicht genutzt |
| 3xl | 64px (×16) | nicht genutzt |

Exceptions (aus DESIGN.md übernommen, keine neuen):
- Zeilenhöhe jeder Speicherzeile und Klickfläche jeder Checkbox: mindestens `var(--default-clickable-area)` (34 px Referenz, Servervariable), bei `pointer: coarse` mindestens 44 px.
- Lesespalte 900 px.

---

## Typography

Genau die Größen und Gewichte der Verwaltungsseite; diese Phase führt keine neue Größe und kein neues Gewicht ein.

| Role | Size | Weight | Line Height | Einsatz in dieser Phase |
|------|------|--------|-------------|-------|
| Body | 15px (`--default-font-size`) | 400 | 1.5 | Mountpunkt in der Speicherzeile, Sätze der Inline-Bestätigung |
| Label | 13px (`--font-size-small`) | 400 | 1.5 | Typ-Angabe (z. B. "SMB/CIFS"), Zähler freier Plätze, Hilfesätze (`.settings-hint`), Feldfehler, Markierungssatz alter Einträge |
| Title | 15px | 700 | 1.5 | Beschriftung der Speicherliste (Klasse `findling-rules__label`, wie "Excluded folders") |
| Heading | 20px | 700 | 1.2 | unverändert: h2 "Rules and limits" des Servers |

Gewichte: 400 und 700, sonst keine (keine 600). Die Figure-Größe 28 px der Abdeckungszahl bleibt außerhalb dieser Phase unverändert.

---

## Color

Nur Server-Variablen; Hex-Werte sind Referenz des Standard-Themes (hell) und gehören nie in den Code.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--color-main-background` (#ffffff) | Seitengrund, Speicherzeilen in Ruhe |
| Secondary (30%) | `--color-background-hover` (#f5f5f5), `--color-border` (#ededed), `--color-text-maxcontrast` (#6b6b6b) | Hover einer Speicherzeile, 1 px Trennlinie zwischen Zeilen (wie `.findling-rules__row`), gedämpfte Typ-Angabe, Zähler, Hilfesätze |
| Accent (10%) | `--color-primary-element` (#00679e) | siehe Liste unten |
| Destructive | `--color-error` / `--color-error-text` (#ffe7e7 / #8a0000), Knopf `--color-element-error` (#c90000) | Inline-Bestätigung beim Ausschließen, Feldfehler (nur Text in `--color-error-text`) |
| Warnung | `--color-warning-text` (#664700), Icon `--color-element-warning` (#bf7900) | Markierungssatz alter Ordnereinträge mit * oder ?, Zählersatz bei 1 und 0 freien Plätzen |

Accent reserved for (abschließend):
1. Der Knopf "Save rules" (`button.primary`, bestehend, einzige volle Akzentfläche des Blocks).
2. Der gesetzte Zustand der Checkboxen (Server-Stil von `.checkbox`, Findling setzt dort keine eigene Farbe).
Nicht für: Zähler, Typ-Angabe, Markierungen, Listenbeschriftung, Links.

Regeln aus DESIGN.md, hier anzuwenden: Pair Rule (Fläche plus `-text` immer als Paar), Never Color Alone (Warnmarkierung immer mit Icon und Satz; Zähler-Hinweis ist ein Satz, nicht nur eine Farbe).

---

## Komponenten und Interaktion

### 1. Liste der externen Speicher (EXCL-04)

Ort: direkt unter `#findling-rules-external-help` (unter dem Schalter "Index external storage"), vor `#findling-rules-effect`.

Struktur (Template rendert vollständig serverseitig, Script baut kein Markup):
- `<fieldset id="findling-rules-mounts" class="findling-rules__mounts">` mit `<legend class="findling-rules__label">` (Title-Stil). Einzug `padding-inline-start: calc(var(--default-grid-baseline) * 4)`, kein Rahmen, keine Fläche, keine Karte (`border: 0` auf dem fieldset, kein Karten-in-Karten).
- Hilfesatz `<p class="settings-hint" id="findling-rules-mounts-help">`.
- `<ul class="findling-rules__list" aria-describedby="findling-rules-mounts-help">`, je Admin-Speicher ein `<li class="findling-rules__row findling-rules__mount">`:
  - `<input type="checkbox" class="checkbox" id="findling-rules-mount-{mountId}" data-mount-id="{mountId}">`, gesetzt = wird indexiert (D-45-01). Gespeichert wird die Liste der nicht gesetzten IDs (D-45-02).
  - `<label for=...>` mit zwei Teilen: Mountpunkt in `<span class="findling-path">` (Body, bricht um, wird nie gekürzt, kein `title`) und Typ in `<span class="findling-rules__mount-type">` (Label-Größe, `--color-text-maxcontrast`). Typ = Anzeigename des files_external-Backends, wie Nextcloud ihn liefert (z. B. "SMB/CIFS", "SFTP", "Local"); fehlt er, die Backend-Kennung.
  - Teilen sich zwei Zeilen Mountpunkt und Typ, bekommt jede Zeile zusätzlich "ID %s" in derselben gedämpften Spanne, damit sie unterscheidbar bleiben.
- Reihenfolge: nach Mountpunkt, alphabetisch mit `localeCompare` bzw. PHP-Collator der Nutzersprache; bei Gleichstand nach ID.
- Ganze Zeile ist Klickfläche über das Label, Mindesthöhe `--default-clickable-area`; Hover der Zeile auf `--color-background-hover`; Fokusring der Checkbox bleibt der des Servers (nie `outline: none`).

Zustände:
| Zustand | Darstellung |
|---------|-------------|
| Hauptschalter an, Speicher vorhanden | Liste aktiv, Haken nach gespeichertem Stand |
| Hauptschalter aus (D-45-04) | `fieldset` bekommt `disabled` (Server graut alle Checkboxen aus), Haken behalten ihren gespeicherten Stand; statt des Hilfesatzes steht der Satz "Hauptschalter aus" (siehe Copy). Umschalten des Hauptschalters setzt/entfernt `disabled` sofort ohne Neuladen. Gespeicherte Ausschlüsse bleiben erhalten. |
| Keine Admin-Speicher | Liste entfällt (`hidden`), Leersatz steht an ihrer Stelle |
| files_external nicht aktiviert | Liste und Leersatz entfallen, stattdessen Satz "nicht aktiviert" |
| Gelöschter Speicher in der gespeicherten Liste (D-45-06) | erscheint nicht; kein Fehler, keine Meldung |
| Ohne JavaScript | Liste sichtbar mit gespeichertem Stand; Speichern braucht wie heute JS, kein eigener Satz nötig (bestehender Block hat Speichern ohnehin nur per JS) |

Persönliche Speicher der Nutzer erscheinen nicht (D-45-03); der Hilfesatz sagt das.

### 2. Inline-Bestätigung beim Ausschließen eines Speichers

Begründung: D-45-05 entfernt Dokumente sofort ohne Gnadenfrist, das ist dieselbe Verlustklasse wie ein neuer Ordnerausschluss (D-07 der Phase 33). Darum dritte Zeile in der bestehenden `#findling-rules-confirm`, nach dem Muster der Musterzeile:
- Neue `<span class="findling-rules__confirm-line" id="findling-rules-confirm-mounts" hidden>` mit `-before`, `<code class="findling-path" id="findling-rules-confirm-mounts-value">`, `-after`; das Script schneidet den übersetzten Satz am Platzhalter, der Mountpunkt ist nie Teil eines übersetzten Strings.
- Gezeigt nur, wenn der Speichervorgang mindestens eine ID neu ausschließt, die vorher indexiert wurde, und der Hauptschalter an ist. Keine Zahl (wie bei Mustern; Vorschau-Zählung ist Claude's Discretion, wenn die Vorschau-Route sie billig liefert, dann Variante mit Zahl analog zur Ordnerzeile).
- Knöpfe unverändert: "Exclude and remove" (destruktiv) und "Keep files indexed"; Fokus geht wie heute auf den harmlosen Knopf. "Keep files indexed" setzt die betroffenen Haken zurück auf gesetzt.
- Wiederzulassen (Haken setzen) löst keine Bestätigung aus.

### 3. Zähler freier Plätze (EXCL-05)

- Je ein `<p class="settings-hint findling-rules__slots" id="findling-rules-slots">` direkt unter `.findling-rules__add` der Ordnerliste und `id="findling-rules-patterns-slots"` unter der Musterliste, vor dem jeweiligen Feldfehler-Element.
- Grenzen aus `data-max-entries` des Feldes (Server: `ExclusionService::MAX_PREFIXES` 64, `MAX_PATTERNS` 32), nie im Template oder JS hart verdrahtet. Zahlen über `numbers.format` (Locale-Formatierung, bestehend).
- Gezählt werden die Zeilen, die gerade in der Liste stehen (auch noch ungespeicherte). Aktualisierung bei jedem Hinzufügen und Entfernen ohne Neuladen.
- Ansage für Screenreader: Zähler selbst ohne `aria-live` (sonst Dauergeplapper); beim Wechsel auf 1 und auf 0 wird der Satz über das bestehende Ansage-Muster (`role="status"`, `aria-live="polite"`, z. B. vorhandene hidden-visually-Spanne des Blocks oder eine neue `findling-rules-announce`) einmal angesagt.
- Bei 1 und 0 frei: Satzwechsel (siehe Copy) plus Textfarbe `--color-warning-text`; der Satz trägt die Bedeutung, nicht die Farbe. Der Knopf "Add exclusion" bzw. "Add pattern" bleibt aktiv; bei 0 meldet ein Versuch den bestehenden Fehler `too_many` am Feld.
- Server rendert den Startwert (ohne JS korrekt).

### 4. * oder ? im Ordnerfeld (EXCL-06, D-45-08)

- Neuer Fehlercode `wildcard` in `ExclusionService::validate` und in `folderErrorSentences()`; das JS prüft beim Hinzufügen vor, der Server entscheidet beim Speichern.
- Darstellung wie alle Feldfehler: ein Satz in `#findling-rules-new-error`, `--color-error-text`, keine gefüllte Fläche, Feld bekommt `aria-invalid="true"`, Fokus bleibt im Feld, Eingabe bleibt stehen (nicht leeren), damit der Admin sie ins Musterfeld übernehmen kann.
- Der Satz nennt "Excluded patterns" mit Beispiel.

### 5. Markierung alter Ordnereinträge mit * oder ? (D-45-08)

- Bereits gespeicherte Ordnerzeilen, deren Pfad * oder ? enthält, bekommen unter dem Pfad innerhalb derselben `li` einen Satz `<p class="findling-rules__row-warning">`: Icon `$alertIcon` 16 px in `--color-element-warning`, Text Label-Größe in `--color-warning-text`, auf normaler Fläche (keine Warnfläche). Zeile wird dazu `flex-wrap: wrap`, Satz auf volle Breite.
- Der Entfernen-Knopf bleibt; nichts wird still gelöscht oder umgedeutet.
- Markierung entscheidet der Server (Template) für gespeicherte Einträge; das JS setzt sie nicht für neu hinzugefügte (die werden vorher abgewiesen).
- Offene Frage an den Planer, nicht blockierend: ob `validate` alte Einträge mit * oder ? beim Speichern ebenfalls abweist (dann muss der Admin sie erst entfernen) oder sie duldet. Der Markierungssatz unten ist für beide Wege richtig. Empfehlung: dulden (keine Aussperrung durch ein Upgrade), aber neue ablehnen.

### 6. Geschärfte Meldung no_wildcard (D-45-09)

Nur der Wortlaut ändert sich (Schlüssel neu, alter Schlüssel entfällt aus allen Katalogen), Darstellung wie bisher am Musterfeld.

---

## Copywriting Contract

Englische Quelltexte stehen im Code (`$l->t()` bzw. `t('findling', ...)`); jede Zeile in allen Katalogen. Anführungszeichen wie im Bestand gerade `"`. Kein Gedankenstrich, kein Emoji. Deutsche Texte mit echten Umlauten.

| Element | EN (Quelle) | DE | FR |
|---------|-------------|----|----|
| Primary CTA (unverändert) | Save rules | Regeln speichern | (Bestand) |
| Beschriftung Speicherliste | External storage to index | Zu indexierende externe Speicher | Stockages externes à indexer |
| Hilfesatz Speicherliste | Storage set up by an admin. Clear a box to keep that storage out of the index. New external storage is included automatically. Storage that users add themselves follows the switch above. | Von Admins angelegte Speicher. Haken entfernen, um diesen Speicher aus dem Index zu nehmen. Neue externe Speicher sind automatisch dabei. Speicher, die Nutzer selbst anlegen, folgen dem Schalter darüber. | Stockages créés par un administrateur. Décocher une case pour retirer ce stockage de l'index. Un nouveau stockage externe est inclus automatiquement. Les stockages que les utilisateurs ajoutent eux-mêmes suivent l'interrupteur ci-dessus. |
| Hauptschalter aus | "Index external storage" is off, so no external storage is indexed. The choices below stay saved and apply again once it is on. | "Externen Speicher indexieren" ist aus, daher wird kein externer Speicher indexiert. Die Auswahl darunter bleibt gespeichert und gilt wieder, sobald der Schalter an ist. | "Indexer le stockage externe" est désactivé, aucun stockage externe n'est donc indexé. Les choix ci-dessous restent enregistrés et s'appliquent de nouveau dès son activation. |
| Hinweis Wiederzulassen (unter der Liste, nur bei vorhandenen Speichern) | A storage you include again is indexed on the next regular comparison run. | Ein wieder zugelassener Speicher wird beim nächsten regulären Abgleich nachindexiert. | Un stockage inclus de nouveau est indexé lors de la prochaine comparaison régulière. |
| Empty state heading | (keine eigene Überschrift; Verwaltungsliste, Muster wie "No folder is excluded.") | | |
| Empty state body | No external storage has been set up by an admin. | Es gibt keinen von Admins angelegten externen Speicher. | Aucun stockage externe n'a été créé par un administrateur. |
| files_external aus | External storage is not enabled on this server. | Externer Speicher ist auf diesem Server nicht aktiviert. | Le stockage externe n'est pas activé sur ce serveur. |
| Unterscheidung gleicher Zeilen | ID %s | ID %s | ID %s |
| Bestätigung, ein Speicher | Remove indexed content? Excluding the external storage %s also removes its already indexed documents from the index. The files themselves stay untouched on the storage. | Indexierte Inhalte entfernen? Der Ausschluss des externen Speichers %s entfernt außerdem seine bereits indexierten Dokumente aus dem Index. Die Dateien selbst bleiben unverändert auf dem Speicher. | Supprimer les contenus indexés ? L'exclusion du stockage externe %s retire également de l'index ses documents déjà indexés. Les fichiers eux-mêmes restent intacts sur le stockage. |
| Bestätigung, mehrere Speicher | Remove indexed content? Excluding the external storages %s also removes their already indexed documents from the index. The files themselves stay untouched on the storage. | Indexierte Inhalte entfernen? Der Ausschluss der externen Speicher %s entfernt außerdem ihre bereits indexierten Dokumente aus dem Index. Die Dateien selbst bleiben unverändert auf dem Speicher. | Supprimer les contenus indexés ? L'exclusion des stockages externes %s retire également de l'index leurs documents déjà indexés. Les fichiers eux-mêmes restent intacts sur le stockage. |
| Destructive confirmation (Knöpfe, unverändert) | Exclude and remove / Keep files indexed | Ausschließen und entfernen / Dateien indexiert lassen | (Bestand) |
| Zähler, ab 2 frei | %1$s of %2$s slots free | Noch %1$s von %2$s frei | Encore %1$s emplacements libres sur %2$s |
| Zähler, 1 frei | 1 of %s slots free. This is the last one. | Noch 1 von %s frei. Das ist der letzte Platz. | Encore 1 emplacement libre sur %s. C'est le dernier. |
| Zähler, 0 frei | 0 of %s slots free. Remove an entry to add another one. | Noch 0 von %s frei. Einen Eintrag entfernen, um einen neuen hinzuzufügen. | Plus aucun emplacement libre sur %s. Supprimer une entrée pour en ajouter une autre. |
| Error: `wildcard` im Ordnerfeld (neu) | Folders take no * or ?. For a pattern like Archiv* use "Excluded patterns". | Ordner ohne * oder ?. Für Muster wie Archiv* das Feld "Ausgeschlossene Muster" nutzen. | Les dossiers n'acceptent ni * ni ?. Pour un motif comme Archiv*, utiliser "Motifs exclus". |
| Error: `no_wildcard` im Musterfeld (ersetzt den Bestand) | This entry has no * or ?. Add whole folders under "Excluded folders", or use a pattern like Name*. | Dieser Eintrag hat kein * oder ?. Ganze Ordner unter "Ausgeschlossene Ordner" eintragen, oder ein Muster wie Name* verwenden. | Cette entrée ne contient ni * ni ?. Ajouter les dossiers entiers sous "Dossiers exclus", ou utiliser un motif comme Name*. |
| Markierung alter Ordnereintrag | This entry contains * or ?, which folders do not support, so it only matches that exact text. Remove it and add it under "Excluded patterns". | Dieser Eintrag enthält * oder ?, was Ordner nicht kennen; er passt daher nur auf genau diesen Text. Ihn entfernen und unter "Ausgeschlossene Muster" eintragen. | Cette entrée contient * ou ?, que les dossiers ne prennent pas en charge : elle ne correspond donc qu'à ce texte exact. La supprimer et l'ajouter sous "Motifs exclus". |
| Error state Speichern (unverändert) | The rules were not saved. Nothing changed. | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | (Bestand) |

Hinweise zum Wortlaut:
- Die Zähler-Sätze sind drei getrennte Schlüssel statt `n()`-Plural, weil 1 und 0 eigene Aussagen tragen; für Sprachen mit mehreren Pluralformen bleibt "%1$s of %2$s slots free" grammatisch neutral formulierbar (Übersetzer dürfen "frei: %1$s von %2$s" bauen). Wenn der Planer `n()` vorzieht, ist das zulässig, solange 1 und 0 ihre eigenen Sätze behalten.
- Der Bestands-Hilfesatz der Ordnerliste ("Prefix match ... without wildcards. For wildcards use "Excluded patterns". Example: Backups") bleibt unverändert.
- Genaue Wortlaute innerhalb von D-45-08/09 sind Claude's Discretion; obige Fassung ist der Vorschlag für die Ausführung. Die französischen und weiteren Übersetzungen gehen durch den Volltest DE/EN/FR (Sprachfehler No-Go).

Kataloge: jeder Schlüssel in jedem Katalog unter `php/l10n/` (je `.js` und `.json`). Bestand heute: de, de_DE, es, fr, it, nl, pt_BR, pt_PT (8 Sprachen, 16 Dateien) plus zh_TW aus PR #56. zh_TW-Übersetzung der neuen Schlüssel machen wir selbst (D-45-12). Umlaut-Audit aller neuen sichtbaren Texte.

Destruktive Aktionen dieser Phase:
- Speicher ausschließen: Inline-Bestätigung (Abschnitt 2), Knopf "Exclude and remove".
- Ordner/Muster hinzufügen: unverändert bestehende Inline-Bestätigung.
- Hauptschalter "Index external storage" aus: unverändert ohne Bestätigung (Bestandsverhalten, nicht Teil dieser Phase).

---

## Responsive und Barrierefreiheit

- Unter 640 px: Speicherzeile umbrechen, Typ-Angabe unter den Mountpunkt (flex-wrap), Mountpunkt bricht um (`overflow-wrap: anywhere`), nie abgeschnitten.
- 640 bis 1023 px und ab 1024 px: Mountpunkt und Typ in einer Zeile, Typ folgt mit 8 px Abstand.
- `pointer: coarse`: jede Speicherzeile mindestens 44 px hoch.
- Tastatur: ein Tabstopp je Checkbox, Leertaste schaltet; bei gesperrtem fieldset keine Tabstopps in der Liste.
- Die Liste ist über `legend` benannt; die Zahl der Zeilen liest der Screenreader aus der `ul`.
- Keine Inline-Skripte, keine `style`-Attribute (CSP); `[hidden]`-Ausnahme nur wie im Bestand.
- Locale: Seite muss unter `zh_Hant_TW` (dreiteilige Locale) und mit Rückfall auf `root.lang` funktionieren (PR #57); Zahlen im Zähler über die vorhandene Locale-Formatierung.

---

## Abnahme und Prüfung

- Playwright in drei Breiten 375, 768 und 1280 px, jeweils hell und dunkel, dazu hoher Kontrast als Stichprobe (DESIGN.md "Do"). Zustände, die abgebildet werden müssen: Liste mit 3 Speichern (einer ausgeschlossen), Hauptschalter aus (gesperrt), leer, files_external aus, Bestätigung mit Speicherzeile, Zähler bei 2, 1 und 0, Feldfehler `wildcard`, Markierung eines alten Eintrags mit *, Meldung `no_wildcard`, Seite unter zh_TW.
- Sprachen der Screenshots: DE, EN, FR (Volltest), dazu zh_TW für KAT-03/04.
- impeccable-Audit der geänderten Ansicht nach der Umsetzung.
- Owner-Abnahme der UI gemeinsam per Playwright (D-45-15).
- Store-Texte (STORE-03/04): kein UI-Bestandteil; der Entwurf DE/EN/FR beider Apps plus Liste der Verlagerungen wird dem Owner kurz vor dem Release gezeigt und erst nach Freigabe eingebaut (D-45-13).

---

## Offene Fragen (nicht blockierend)

1. Werden gespeicherte Ordnereinträge mit * oder ? beim Speichern abgewiesen oder geduldet? Empfehlung: dulden und markieren (Abschnitt 5).
2. Katalogzählung: CONTEXT nennt "16 Kataloge plus zh_TW (17)"; im Repo sind es 8 Sprachen in 16 Dateien. Maßgeblich für die Ausführung: jeder vorhandene Katalog nach dem Merge von PR #56.
3. Liefert die Vorschau-Route die Dokumentzahl je Speicher billig, darf die Bestätigung die Zahl nennen (Variante analog zur Ordnerzeile); sonst ohne Zahl wie oben.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| keine (kein shadcn, kein Fremdregister) | keine | not applicable |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: FLAG (nicht blockierend: Speicherfehler-Text ohne nächsten Schritt, Zähler ohne Einheit)
- [x] Dimension 2 Visuals: FLAG (nicht blockierend: Blickfang nicht ausdrücklich benannt; "Save rules" einzige Akzentfläche, Speicherliste erstes Leseziel unter dem Schalter)
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-11-21 (gsd-ui-checker, 0 Blocker, 3 Hinweise)
