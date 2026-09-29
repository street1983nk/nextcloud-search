---
phase: 27
slug: vorab-pr-fung-und-settings-oberfl-che
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-29
---

# Phase 27: UI Design Contract (Vorab-Prüfung und Settings-Oberfläche)

> Visueller und Interaktionsvertrag für den neuen Block "Leistungsprofil" der bestehenden Adminseite. Erstellt von gsd-ui-researcher, geprüft von gsd-ui-checker.
> Grundlage: 27-CONTEXT.md (D-27-01..14, gelockt), Vorentscheide D-24/D-25/D-26, Bestandsvertrag 04-UI-SPEC.md, Bestand `php/templates/admin.php`, `php/css/admin.css`, `php/js/admin.js`.
> Diese Phase erweitert die Seite. Sie erfindet kein Token, keine Schriftgröße und keine Farbe neu.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Companion ohne npm und ohne Build-Step, Vertrag 04-UI-SPEC, D-02) |
| Preset | not applicable |
| Component library | none. Nextcloud-Server-CSS (`.section`, `.settings-hint`, `button`, `button.primary`, `select`, `input.checkbox`, `icon-loading-small`, `hidden-visually`) plus `php/css/admin.css` |
| Icon library | Material Design Icons (Pictogrammers), Apache-2.0, als Inline-SVG-Pfaddaten im Template, gepinnt über THIRD-PARTY.md. Kein Icon-Font. Spinner: Core `icon-loading-small` |
| Font | `var(--font-face)` von Nextcloud, kein Webfont |
| Stack-Grenze | Vanilla-JS in `php/js/admin.js`, kein Vue-Umbau, keine neue Bibliothek. Das Skript baut kein Markup: alle Zustände liegen im Template, das Skript schaltet `hidden` und schreibt Textknoten (Gate C in `backend/tests/test_admin_ui_contract.py`) |
| Registry | nicht anwendbar (kein shadcn, React-Gate entfällt: PHP-Template + Vanilla-JS) |

---

## Platzierung und Blockstruktur (Entscheidung dieses Vertrags)

- **Neuer Block `#findling-profile` als eigene `.section`**, eingefügt **direkt vor** "Rules and limits" (`#findling-rules`). Begründung: Die beiden schreibenden Blöcke der Seite stehen zusammen; die Blöcke eins bis vier bleiben reine Auskunft. Reihenfolge danach: Deckungsgrad, Schätzung, Nicht indexierte Dateien, Einzelne Datei prüfen, **Leistungsprofil**, Regeln und Grenzen.
- `#findling-profile` bekommt `max-width: 900px` und die `[hidden] { display: none !important }`-Regel wie die fünf Bestandsblöcke (Selektorlisten in `admin.css` Zeile 18 bis 38 erweitern).
- **ADM-04 bleibt gewahrt:** Der Block enthält genau ein Auswahlfeld und eine davon abhängige Option (fp32-Häkchen, D-27-01). Kein Aufklappen, kein "Erweitert", keine Einzelwerte zum Einstellen. Die überstimmten Einzelwerte (D-27-14) sind reine Anzeige, nie ein Feld.
- **Block eins (Deckungsgrad):** Die Wächterzeile `#findling-guard` und die Slotzeile `#findling-slots` bleiben dort unverändert (sie erklären, warum ein Lauf langsamer geht). **Die occ-Rückwegzeile `#findling-guard-way-back` entfällt samt Code-Element, Marker `\u{E000}` und Katalogschlüssel** "To lift the reduction after checking the memory: %1$s" in allen 16 Katalogdateien (D-27-12). Der Rückweg lebt jetzt als Knopf im Block Leistungsprofil.

### Aufbau von oben nach unten

```
h2  Leistungsprofil
p.settings-hint       Einleitung (1 Satz)
p                     Erkannt: Kerne 8, Speicher 15,6 GB          #findling-profile-hardware
p                     Vorschlag für diese Box: Standard            #findling-profile-suggested
p                     Wirksam: Sparsam                             #findling-profile-in-force
p.settings-hint       (nur Schrumpfung) Gewählt ..., wirksam ...   #findling-profile-shrunk
p.findling-banner--warning  (nur Wächter) Satz + [Erneut prüfen]   #findling-profile-guard
p.settings-hint       (nur Präzisionsverdikt) fp32-Satz            #findling-profile-precision

label  Profil
select [Sparsam | Standard (Vorschlag) | Leistung]                 #findling-profile-select
p.settings-hint       Beschreibung des gewählten Profils           #findling-profile-describe-*
div.findling-rules__toggle  [ ] Genaueres Suchmodell (fp32)        #findling-profile-fp32   (nur Standard/Leistung)
p.settings-hint       Download-Hinweis zum Häkchen                 #findling-profile-fp32-help
p.findling-banner--info  Neueinbettung von ... (Schätzung)         #findling-profile-reindex (nur bei Präzisionswechsel)
div (nur Env)         Lead + ul mit überstimmten Werten            #findling-profile-env

div.findling-profile__actions
    [Übernehmen und prüfen | Übernehmen]  (primary)                #findling-profile-apply
    [Bei Sparsam bleiben]                                          #findling-profile-stay
p.settings-hint       Kein-Änderung-Hinweis                        #findling-profile-nochange
p.findling-progress-hint  Spinner + Prüfung läuft: <Schritt>       #findling-profile-progress
p.settings-hint       Pause-Hinweis während der Probe              #findling-profile-progress-hint
p.findling-rules__error   Startfehler (belegt, unerreichbar, alte Version)  #findling-profile-error
div.findling-card     Verdikt-Karte                                #findling-profile-verdict
p.findling-rules__feedback  Rückmeldung Speichern ohne Probe       #findling-profile-feedback
p.settings-hint       Nur ohne JS                                  #findling-profile-nojs
span.hidden-visually  Live-Region (Ansage)                         #findling-profile-announce
```

---

## Spacing Scale

Unverändert aus 04-UI-SPEC; jede eigene Distanz als `calc(var(--default-grid-baseline) * n)`, Baseline 4px.

| Token | Value | Usage in diesem Block |
|-------|-------|-------|
| xs | 4px | Icon zu Label im Verdikt-Chip, Checkbox zu Label, Label zu Feld (`margin-block-end` des Labels) |
| sm | 8px | Abstand zwischen den Knöpfen der Aktionszeile, Spinner zu Fortschrittssatz, Absätze in der Verdikt-Karte, Listenabstand der Env-Zeilen |
| md | 16px | Abstand Aktionszeile zu Formular darüber, Innenabstand Verdikt-Karte, Banner und Rückmeldung, Abstand Label "Profil" nach oben, Icon-Kantenlänge |
| lg | 24px | Abstand zwischen Auskunftsteil (Hardware/Vorschlag/Wirksam) und Formularteil (Label "Profil") |
| xl | 32px | nicht verwendet |
| 2xl | 48px | nicht verwendet |
| 3xl | 64px | nicht verwendet |

Exceptions (alle aus dem Core, nicht überschreiben):
- 30px `.section`-Padding des Core.
- `var(--default-clickable-area)` (34px) als Mindesthöhe für Select, Checkbox-Label und alle vier Knopfarten.
- `.settings-hint { margin-block: -12px 12px }` des Core.
- Select-Breite: `min-width: calc(var(--default-grid-baseline) * 60)` (240px), damit "Standard (Vorschlag)" in allen acht Sprachen ohne Abschneiden steht.

Neue CSS-Klassen (einzige Ergänzungen in `admin.css`):
- `.findling-profile__actions`: `display: flex; flex-wrap: wrap; align-items: center; gap: calc(var(--default-grid-baseline) * 2); margin-block: calc(var(--default-grid-baseline) * 4);` Knöpfe darin `min-height: var(--default-clickable-area)`.
- `#findling-profile-select`: `min-height: var(--default-clickable-area); min-width: calc(var(--default-grid-baseline) * 60);`
- `.findling-profile__facts` (Wrapper der drei Auskunftszeilen): `margin-block-end: calc(var(--default-grid-baseline) * 6);`
- `.findling-banner--info`: `background-color: var(--color-info); color: var(--color-info-text);` Icon `color: var(--color-element-info)` (Hinweis-Paar aus 04-UI-SPEC, bisher nicht als Banner-Modifier vorhanden).
- `.findling-chip--narrow` = Warnpaar, `.findling-chip--nofit` = Fehlerpaar, `.findling-chip--fits` = Erfolgspaar (dieselben Deklarationen wie `--skipped`, `--failed`, `--indexed`; als Selektor dort anhängen statt kopieren).
- Der Knopf im Wächter-Banner: `margin-inline-start: auto; min-height: var(--default-clickable-area);` damit er rechts am Satz steht und bei Umbruch unter ihn fällt (`flex-wrap: wrap` am Banner dieses Blocks).
- Verdikt-Karte, Fortschritt, Fehlerzeile und Rückmeldung nutzen die Bestandsklassen `.findling-card`, `.findling-progress-hint`, `.findling-rules__error`, `.findling-rules__feedback--success|--error` unverändert.

---

## Typography

Keine neue Größe, kein neues Gewicht. Die 28px-Display-Größe kommt in diesem Block nicht vor.

| Role | Size | Weight | Line Height | Anwendung im Block |
|------|------|--------|-------------|-----------|
| Body | 15px (`var(--default-font-size)`) | 400 | 1.5 (`var(--default-line-height)`) | Auskunftszeilen, Select, Knöpfe, Checkbox-Label, Banner, Verdikt-Ursache |
| Label | 13px | 400 | 1.5 | `.settings-hint`-Zeilen, Verdikt-Chip, Env-Zeilen, Fehlerzeile |
| Heading | 20px | 700 | 1.2 | `h2` "Leistungsprofil" (Core) |
| Feldlabel | 15px | 700 | 1.5 | Label "Profil" über dem Select, Klasse `.findling-rules__label` wiederverwenden |

Gewichte gesamt: 400 und 700. Variablennamen in Env-Zeilen stehen in `<code>` (Core-Monospace), ohne eigene Größe.

---

## Color

Nur Theme-Variablen, keine Literalwerte (hell, dunkel, hoher Kontrast ohne Zweitregel).

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `var(--color-main-background)` | Grund des Blocks |
| Secondary (30%) | `var(--color-background-hover)` | Verdikt-Karte, neutraler Chip; Trennlinie `var(--color-border)` |
| Accent (10%) | `var(--color-primary-element)` | siehe Reserveliste |
| Destructive | `var(--color-error)` / `--color-error-text` / `--color-element-error` | nur Verdikt-Chip "Passt nicht", Fehlerzeile und Rückmeldung "nicht gespeichert"; **kein destruktiver Knopf** in diesem Block |

Accent reserved for (abschließend):
1. Der eine Primärknopf `#findling-profile-apply` (`class="primary"`), in beiden Beschriftungen.
2. Die Core-Darstellung des gesetzten fp32-Häkchens.
3. Der Core-Fokusring des Select (nicht anfassen).

Nicht Akzent: "Bei Sparsam bleiben", "Erneut prüfen", "%s prüfen" sind Core-Standardknöpfe. Pro Zustand ist höchstens EIN Primärknopf sichtbar.

Bedeutungspaare (aus 04-UI-SPEC, hier angewandt):

| Bedeutung | Fläche / Text / Icon | Stelle |
|-----------|------|--------|
| Erfolg | `--color-success` / `--color-success-text` / `--color-element-success` | Chip "Passt", Rückmeldung "gespeichert" |
| Warnung | `--color-warning` / `--color-warning-text` / `--color-element-warning` | Chip "Passt knapp", Wächter-Banner |
| Fehler | `--color-error` / `--color-error-text` / `--color-element-error` | Chip "Passt nicht", Startfehler, Speicherfehler |
| Hinweis | `--color-info` / `--color-info-text` / `--color-element-info` | Reindex-Hinweis |
| Neutral | `--color-background-hover` / `--color-main-text` / `--color-text-maxcontrast` | Verdikt-Karte, "Noch keine Prüfung" |

Farbe ist nie alleiniger Träger: jeder Chip hat Icon und Wort, jeder Banner Icon und Satz.

Icons (Inline-SVG, 16px, `aria-hidden="true" focusable="false"`):
- Passt: check-circle-outline (Pfad wie `$diagnosisIcons['indexed']`).
- Passt knapp: alert-circle-outline (`$alertIcon`).
- Passt nicht: close-circle-outline (neuer Pfad, aus dem in THIRD-PARTY.md gepinnten MDI-Commit übernehmen).
- Wächter-Banner: `$alertIcon`. Reindex-Hinweis: `$infoIcon`. Fortschritt: Core-Spinner.
Alle drei Verdikt-Icons liegen gleichzeitig im Markup, zwei davon `hidden` (Muster Diagnose-Karte).

---

## Zustandsinventar (verbindlich)

Datengrundlage: Statusblock `profile` (gewählt, vorgeschlagen, wirksam, Hardware, Werte samt Quelle `profile`/`env`), Block `guard`, `precisionActive`/`precisionVerdict`, gespeichertes letztes Probe-Ergebnis, Probe-Stand-Route. Alle Wörter kommen als Codes aus geschlossenen Mengen und werden PHP- bzw. JS-seitig auf Katalogsätze abgebildet; unbekannter Code = Zeile verborgen (T-26-16-Muster).

| # | Zustand | Auslöser | Sichtbar | Controls |
|---|---------|----------|----------|----------|
| Z1 | Erstaufruf ohne Probe, Vorschlag = Sparsam | kein Profilschlüssel gespeichert, keine Probe, Vorschlag economy | Hardware, "Vorschlag: Sparsam", "Wirksam: Sparsam", Verdikt-Karte mit "Noch keine Prüfung." | Select auf Sparsam, Apply deaktiviert, "Bei Sparsam bleiben" verborgen, Kein-Änderung-Hinweis sichtbar |
| Z2 | Erstaufruf mit Vorschlag Standard/Leistung | kein Profilschlüssel gespeichert, Vorschlag über Sparsam | wie Z1, Vorschlag nennt Stufe, Option trägt "(Vorschlag)" | **Select vorbelegt mit dem Vorschlag**, fp32 aus, Apply = "Übernehmen und prüfen" aktiv, "Bei Sparsam bleiben" sichtbar. Ohne Klick wird nichts gespeichert, wirksam bleibt Sparsam (SC1) |
| Z3 | Gespeicherter Zustand, keine Änderung im Formular | Profilschlüssel vorhanden, Formular = gespeichert | Auskunft, letzte Verdikt-Karte (falls vorhanden) | Select auf gespeichertem Profil, Apply deaktiviert (Beschriftung "Übernehmen und prüfen"), Kein-Änderung-Hinweis sichtbar; "Bei Sparsam bleiben" nur, wenn gespeichert = Sparsam und Vorschlag darüber |
| Z4 | Änderung, die eine Probe braucht | Ziel über gespeichertem Profil, **Leistung zu Standard** (D-27-09), oder fp32 neu gesetzt | wie Z3 plus ggf. Reindex-Hinweis | Apply = "Übernehmen und prüfen", aktiv |
| Z5 | Änderung ohne Probe (Abwärtsweg D-27-09) | Ziel = Sparsam, oder nur fp32 zu int8 bei gleichem Profil | Reindex-Hinweis bei fp32 zu int8 | Apply = **"Übernehmen"**, aktiv; Klick speichert sofort, Rückmeldung inline, keine Probe, kein Dialog |
| Z6 | Probe läuft | Klick in Z2/Z4, "Erneut prüfen", "%s prüfen", oder Seite geöffnet während einer Probe (auch aus anderem Tab) | Fortschrittszeile mit Spinner und Schritt, Pause-Hinweis; letzte Verdikt-Karte verborgen | Select, Checkbox und alle Knöpfe `disabled`; kein Abbrechen-Knopf (Zeitdeckel D-27-06 begrenzt) |
| Z6a | Probe lädt fp32 | Schritt `download` | Fortschritt "Modell herunterladen, 120,4 MB von 448,5 MB" | wie Z6 |
| Z7 | Verdikt Passt | Probe fertig, `fits` | Karte: Chip "Passt", Geprüft-Zeile, "Gespeichert. %s gilt ab der nächsten Indexrunde."; bei fp32 zusätzlich Reindex-Hinweis | Formular = neuer gespeicherter Stand (Z3), "Wirksam" aktualisiert mit dem nächsten Status-Poll |
| Z8 | Verdikt Passt knapp | `narrow` + Ursache | Karte: Chip "Passt knapp", Geprüft-Zeile, Ursache, "Nichts gespeichert. %s bleibt wirksam.", bei fp32 "Die geladene Modelldatei wurde wieder gelöscht." | Angebot der nächstniedrigeren Stufe in der Karte: Leistung → Knopf "Standard prüfen"; Standard → Knopf "Bei Sparsam bleiben". Kein "Trotzdem übernehmen" (D-27-08). Formular springt auf den gespeicherten Stand zurück |
| Z9 | Verdikt Passt nicht | `nofit` + Ursache | wie Z8 mit Chip "Passt nicht" | wie Z8 |
| Z10 | Wächter-Absenkung | `guardCause` in geschlossener Menge und gewählt ≠ wirksam | Warn-Banner mit beiden Stufen, Ursache und Knopf "Erneut prüfen" oben im Block; Wächterzeile in Block eins bleibt | "Erneut prüfen" startet die Probe für das GEWÄHLTE Profil samt gespeicherter Präzision; bei "Passt" gilt das als Bestätigung (Token serverseitig, D-26-04/D-27-12), Banner verschwindet mit dem nächsten Status-Poll. Der Token erscheint nirgends auf der Seite |
| Z11 | Hardware-Schrumpfung | gewählt ≠ wirksam ohne Wächter-Ursache (D-24-07) | Hinweiszeile "Gewählt ..., wirksam ...: Diese Box hat weniger Hardware ..." | normal bedienbar |
| Z12 | Env-Überstimmung | mindestens ein Wert mit Quelle `env` | Lead-Satz plus Liste, je Wert eine Zeile mit Wert und Variablenname in `<code>` | Select bleibt frei (D-27-14) |
| Z13 | Präzisionsverdikt | `precisionVerdict` in {fp32_unavailable, fp32_on_a_tight_box, fp32_not_in_economy, fp32_active_in_economy, downloading} | genau eine Zeile `#findling-profile-precision` | normal |
| Z14 | Backend nicht erreichbar | `backendReachable` falsch oder Probe-Start/Stand liefert Transportfehler | Auskunftszeilen mit letzten bekannten Werten; Fehlerzeile "Die Prüfung braucht das Backend ..." (bei Klick) | Apply "Übernehmen und prüfen" und "Erneut prüfen" `disabled` solange unerreichbar; "Übernehmen" ohne Probe (Z5) bleibt möglich, weil es nur appconfig schreibt (D-24-01) |
| Z15 | Container ohne Probe-Route (alt) | Probe-Start liefert 404/unbekannte Route, oder Statusantwort ohne Block `profile` | Fehlerzeile "Diese Backend-Version kann die Prüfung nicht fahren ..."; ohne Block `profile`: "Dieses Backend meldet seine Hardware noch nicht." statt Hardware/Vorschlag | Probe-Knöpfe `disabled`; Z5-Wege bleiben |
| Z16 | Probe schon belegt | Start liefert "busy" | Fehlerzeile "Eine Prüfung läuft bereits ..."; Seite wechselt sofort in Z6 und pollt die laufende Probe | wie Z6 |
| Z17 | Speichern fehlgeschlagen | Schreibroute liefert Fehler (Z5 oder nach Passt) | Rückmeldung Fehlerpaar "Das Profil wurde nicht gespeichert. Es hat sich nichts geändert." | Formular bleibt auf der Auswahl, Apply wieder aktiv |
| Z18 | Ohne JavaScript | kein Skript | Auskunftszeilen, Banner, letzte Verdikt-Karte serverseitig vollständig; Select/Checkbox gerendert; Zeile `#findling-profile-nojs` sichtbar (Skript setzt `hidden`) | Knöpfe tun nichts; Satz nennt das |

Regeln zu den Zuständen:
- **Probe nötig?** Genau dann nicht, wenn Zielprofil = Sparsam, oder Zielprofil = gespeichertes Profil und die einzige Änderung fp32 zu int8 ist. Alles andere läuft durch die Probe. Das Skript schaltet die Beschriftung des Primärknopfs bei jedem `change` von Select und Checkbox.
- **fp32-Häkchen:** sichtbar (`hidden` entfernt) nur bei Select = Standard oder Leistung (D-27-01). Beim Wechsel auf Sparsam wird es verborgen; die Präzision ändert sich dadurch nicht (D-25-10). Ist fp32 aktiv und das Ziel Sparsam, speichert "Übernehmen" nur das Profil, und Z13 zeigt danach `fp32_active_in_economy` mit dem Rückweg.
- **Reindex-Hinweis** (D-27-03) erscheint sofort beim Setzen oder Entfernen des Häkchens, sobald die Zielpräzision von der aktiven abweicht, ohne Dialog. Zwei Formen: mit Dauer, wenn eine Schätzung vorliegt; sonst Kurzform nur mit Dokumentzahl. Die Dauer ist als "geschätzt" beschriftet und nutzt denselben Einkorn-Formatierer wie `$span` (eine Einheit: Minuten, Stunden oder Tage).
- **Verdikt verfällt nicht** (D-27-10): die letzte Karte bleibt nach Neuladen sichtbar (serverseitig gerendert aus dem gespeicherten Ergebnis) mit Datum und Ergebnis, bis eine neue Probe startet.
- **Poll:** Während Z6 fragt das Skript den Probe-Stand alle 2000 ms ab (Endwert legt die Research fest, höchstens 5000 ms wie `POLL_ACTIVE_MS`), stoppt bei Verdikt oder Fehler und löst dann einen Status-Poll aus. Beim Seitenaufruf mit laufender Probe setzt das Skript sofort in Z6 ein.

---

## Interaktion, Fokus und Barrierefreiheit

- **Semantik:** `<label for="findling-profile-select">` über dem Select; Select trägt `aria-describedby` auf die Profilbeschreibung und die Kein-Änderung-Zeile. Checkbox im Core-Paar `input.checkbox` + `label`, `aria-describedby="findling-profile-fp32-help findling-profile-reindex"`.
- **Eine Live-Region:** `<span id="findling-profile-announce" class="hidden-visually" role="status" aria-live="polite">`, nie verborgen, nie entfernt. Das Skript schreibt genau einen Satz hinein: beim Probe-Start, bei jedem **Wechsel** des Schritts (nicht bei jedem Poll; der Downloadfortschritt wird nur sichtbar aktualisiert, angesagt höchstens in 25-Prozent-Schritten), beim Verdikt (Verdiktwort + Ursache + Folge in einem Satz), bei Startfehler und bei Rückmeldung. Die sichtbaren Elemente (Fortschritt, Karte, Rückmeldung) tragen selbst kein `aria-live`, damit nichts doppelt angesagt wird.
- **Fokus:**
  - Probe-Start: Da alle Controls `disabled` werden, geht der Fokus auf die Fortschrittszeile `#findling-profile-progress` (`tabindex="-1"`).
  - Verdikt Passt: Fokus auf die Verdikt-Karte (`tabindex="-1"`).
  - Verdikt Passt knapp/nicht: Fokus auf den Angebotsknopf in der Karte ("Standard prüfen" bzw. "Bei Sparsam bleiben").
  - Startfehler: Fokus zurück auf den auslösenden Knopf, sobald er wieder aktiv ist; Fehlerzeile ist per `aria-describedby` an ihn gebunden.
  - Speichern ohne Probe: Fokus bleibt auf "Übernehmen"; Rückmeldung per Live-Region.
- **Tastatur:** Alles mit Tab erreichbar in Dokumentreihenfolge; Enter/Leertaste auf Knöpfen; kein eigener Tastenhandler außer dem Core-Verhalten. `disabled` statt `aria-disabled`, weil während der Probe wirklich nichts wirken darf.
- **Klickflächen:** Jede Klickfläche mindestens `var(--default-clickable-area)` hoch.
- **Fokusring:** unverändert vom Core, nichts entfernt eine Outline.
- **Kein Toast, kein Modal, kein Bestätigungsdialog** in diesem Block (D-27-03; Seitenlinie seit 04-UI-SPEC).

---

## Copywriting Contract

Quell-Strings Englisch (Code Englisch), Übersetzung Deutsch hier festgelegt; die anderen sechs Sprachen (es, fr, it, nl, pt_BR, pt_PT) plus `de_DE` bekommen dieselben Schlüssel im Gleichstand (16 Dateien). Katalog-Gates, die grün bleiben müssen: `test_every_catalogue_carries_the_same_keys`, `test_every_catalogue_value_carries_a_wording_of_its_language` (Ausnahmen wie "Standard" und "fp32"-haltige Gleichheiten in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` begründen), `test_no_catalogue_value_loses_or_invents_a_placeholder`, `test_no_catalogue_value_can_break_the_page` (kein nacktes `%`, kein `|`), JS/JSON-Wertgleichheit. Variablennamen, Hostnamen, Modellnamen und Zahlen stehen als Platzhalter oder fest im Code, nie im übersetzbaren Text, soweit unten nicht ausdrücklich im String.

| Element | Copy |
|---------|------|
| Primary CTA | EN `Apply and check` / DE `Übernehmen und prüfen` |
| Empty state heading | EN `No check yet.` / DE `Noch keine Prüfung.` (Verdikt-Karte in Z1/Z2) |
| Empty state body | EN `Choose a profile and check it on this box. Until then Economy stays in force.` / DE `Ein Profil wählen und auf dieser Box prüfen. Bis dahin bleibt Sparsam wirksam.` |
| Error state | EN `The check needs the backend, and it does not answer right now. Nothing was saved.` / DE `Die Prüfung braucht das Backend, und es antwortet gerade nicht. Nichts gespeichert.` |
| Destructive confirmation | keine in dieser Phase. Begründung: kein Schritt vernichtet Nutzerdaten; der Rückweg fp32 zu int8 löscht nur die nachladbare Modelldatei und ist laut D-27-03 bewusst ohne Dialog, die Reindex-Zeile benennt die Folge vor dem Klick |

### Block, Auskunft, Formular

| Schlüssel (EN) | DE | Stelle |
|---|---|---|
| `Performance profile` | `Leistungsprofil` | h2 |
| `How much of this box Findling may use. Without a change Findling stays on Economy.` | `Wie viel dieser Box Findling nutzen darf. Ohne Änderung bleibt Findling bei Sparsam.` | Einleitung |
| `Detected: cores %1$s, memory %2$s` | `Erkannt: Kerne %1$s, Speicher %2$s` | Hardware (Zahl via `$count`, Größe via `$size`) |
| `This backend does not report its hardware yet.` | `Dieses Backend meldet seine Hardware noch nicht.` | Z15 |
| `Suggested for this box: %s` | `Vorschlag für diese Box: %s` | Vorschlag |
| `In force: %s` | `Wirksam: %s` | Wirksam |
| `Chosen %1$s, in force %2$s: this box has less hardware than the chosen profile needs.` | `Gewählt %1$s, wirksam %2$s: Diese Box hat weniger Hardware, als das gewählte Profil braucht.` | Z11 |
| `Profile` | `Profil` | Label Select |
| `Economy` / `Standard` / `Performance` | `Sparsam` / `Standard` / `Leistung` | Optionen (Bestandsschlüssel, wiederverwenden) |
| `%s (suggested)` | `%s (Vorschlag)` | Option des Vorschlags |
| `One OCR slot, as before.` | `Ein OCR-Slot, wie bisher.` | Beschreibung Sparsam |
| `At most half of this box, up to %s OCR slots.` | `Höchstens die Hälfte dieser Box, bis zu %s OCR-Slots.` | Beschreibung Standard (%s = 4 aus Konstante) |
| `Everything but one core, up to %s OCR slots.` | `Alles bis auf einen Kern, bis zu %s OCR-Slots.` | Beschreibung Leistung (%s = 16 aus Konstante) |
| `More accurate search model (fp32)` | `Genaueres Suchmodell (fp32)` | Checkbox |
| `Downloaded once during the check, about %s from the Findling release on GitHub. Needs more memory than int8.` | `Wird bei der Prüfung einmal geladen, etwa %s aus dem Findling-Release auf GitHub. Braucht mehr Speicher als int8.` | Hilfe Checkbox (%s via `$size` aus der Bytegröße der Release-Datei) |
| `Re-embedding of %1$s documents, estimated about %2$s. Full text search stays fully available.` | `Neueinbettung von %1$s Dokumenten, geschätzt etwa %2$s. Die Volltextsuche bleibt voll verfügbar.` | Reindex lang |
| `Re-embedding of %s documents. Full text search stays fully available.` | `Neueinbettung von %s Dokumenten. Die Volltextsuche bleibt voll verfügbar.` | Reindex kurz |
| `Choose a different profile or model to check it.` | `Ein anderes Profil oder Modell wählen, um es zu prüfen.` | Kein-Änderung-Hinweis |
| `Changing the profile needs JavaScript. Everything above stays complete without it.` | `Das Profil zu ändern braucht JavaScript. Alles darüber bleibt ohne es vollständig.` | Z18 |

### Überstimmte Werte (D-27-14)

| Schlüssel (EN) | DE |
|---|---|
| `The check calculates with these values from environment variables:` | `Die Prüfung rechnet mit diesen Werten aus Umgebungsvariablen:` |
| `OCR resolution %1$s dpi, set by %2$s` | `OCR-Auflösung %1$s dpi, gesetzt durch %2$s` |
| `OCR limit %1$s pages per file, set by %2$s` | `OCR-Deckel %1$s Seiten je Datei, gesetzt durch %2$s` |
| `Embedding batch size %1$s, set by %2$s` | `Einbettungs-Stapelgröße %1$s, gesetzt durch %2$s` |
| `Index writer memory %1$s, set by %2$s` | `Speicher des Indexschreibers %1$s, gesetzt durch %2$s` |

`%2$s` ist immer einer der vier festen Namen aus `_OVERRIDES` (`FINDLING_OCR_DPI`, `FINDLING_OCR_MAX_PAGES`, `FINDLING_EMBED_BATCH_SIZE`, `FINDLING_WRITER_HEAP_BYTES`), gerendert in `<code>` per Marker-Schnitt wie bisher beim occ-Befehl; der Wert ist Ganzzahl bzw. `$size`.

### Knöpfe

| Schlüssel (EN) | DE | Wann |
|---|---|---|
| `Apply and check` | `Übernehmen und prüfen` | Primär, Änderung mit Probe |
| `Apply` | `Übernehmen` | Primär, Abwärtsweg ohne Probe (Z5) |
| `Stay on Economy` | `Bei Sparsam bleiben` | Z2, Z3 (gespeichert Sparsam, Vorschlag darüber), Karte in Z8/Z9 ab Standard. Klick: Select auf Sparsam, fp32 aus; speichert Sparsam sofort ohne Probe, auch wenn schon Sparsam gilt (damit der Vorschlag nicht erneut vorbelegt wird) |
| `Check again` | `Erneut prüfen` | Wächter-Banner Z10 |
| `Check %s` | `%s prüfen` | Karte in Z8/Z9 ab Leistung (%s = `Standard`) |

### Probe-Fortschritt

| Schlüssel (EN) | DE |
|---|---|
| `Check running: %s` | `Prüfung läuft: %s` |
| `waiting for the indexing batch` | `Indexstaffel abwarten` |
| `downloading the model, %1$s of %2$s` | `Modell herunterladen, %1$s von %2$s` |
| `verifying the model file` | `Modelldatei prüfen` |
| `loading the model` | `Modell laden` |
| `OCR with one slot` | `OCR mit einem Slot` |
| `calculating memory` | `Speicher rechnen` |
| `OCR with %s slots` | `OCR mit %s Slots` |
| `cleaning up` | `aufräumen` |
| `Indexing pauses during the check and continues afterwards.` | `Die Indexierung pausiert während der Prüfung und läuft danach weiter.` |

Schrittcodes als geschlossene Menge (Endliste legt die Research fest; jeder neue Code braucht hier einen Satz, sonst zeigt die Zeile nur `Check running` ohne Schritt): `pause`, `download`, `digest`, `model`, `ocr_one`, `calc`, `ocr_n`, `cleanup`.

### Verdikt

| Schlüssel (EN) | DE | Stelle |
|---|---|---|
| `Fits` | `Passt` | Chip |
| `Fits narrowly` | `Passt knapp` | Chip |
| `Does not fit` | `Passt nicht` | Chip |
| `Checked: %1$s with %2$s, %3$s` | `Geprüft: %1$s mit %2$s, %3$s` | Profil, Modellname (`e5-small int8`/`e5-small fp32` wie Modellzeile), Datum via `IDateTimeFormatter::formatDateTime` |
| `Saved. %s applies from the next indexing round.` | `Gespeichert. %s gilt ab der nächsten Indexrunde.` | Passt |
| `Nothing was saved. %s stays in force.` | `Nichts gespeichert. %s bleibt wirksam.` | Passt knapp / nicht |
| `The downloaded model file was deleted again.` | `Die geladene Modelldatei wurde wieder gelöscht.` | knapp/nicht mit fp32 (D-27-02) |

### Ursachen (geschlossene Menge, Claude's Discretion; Research darf Codes zusammenlegen, jeder verbleibende Code braucht genau einen dieser Sätze)

| Code | Verdikt | EN | DE |
|---|---|---|---|
| `reserve_thin` | knapp | `Memory reserve too thin: %1$s left, %2$s needed.` | `Speicherreserve zu knapp: %1$s übrig, %2$s nötig.` |
| `memory_short` | nicht | `Not enough memory: %1$s OCR slots need about %2$s, %3$s are available.` | `Zu wenig Speicher: %1$s OCR-Slots brauchen etwa %2$s, verfügbar sind %3$s.` |
| `model_memory` | nicht | `Not enough memory for the fp32 model: it needs about %1$s, %2$s are available.` | `Zu wenig Speicher für das fp32-Modell: Es braucht etwa %1$s, verfügbar sind %2$s.` |
| `slot_killed` | nicht | `A test slot was ended for lack of memory.` | `Ein Prüf-Slot wurde wegen Speichermangel beendet.` |
| `timeout` | nicht | `The measurement took longer than %s.` | `Die Messung dauerte länger als %s.` |
| `download_failed` | nicht | `The model could not be downloaded. Check that github.com and release-assets.githubusercontent.com are reachable.` | `Das Modell ließ sich nicht herunterladen. Prüfen, ob github.com und release-assets.githubusercontent.com erreichbar sind.` |
| `download_slow` | nicht | `The download took longer than %s.` | `Der Download dauerte länger als %s.` |
| `digest_mismatch` | nicht | `The model file does not match its checksum and was deleted.` | `Die Modelldatei passt nicht zu ihrer Prüfsumme und wurde gelöscht.` |

Zahlen: Slotzahl via `$count`, Bytes via `$size`, Deckel via `$span`. Fehlt dem Container ein Zahlwert, zeigt die Seite keinen Satz mit Loch: dann gilt die Kurzform des Chips plus `Nothing was saved. %s stays in force.`.

### Startfehler, Rückmeldung, Wächter, Präzision

| Schlüssel (EN) | DE | Zustand |
|---|---|---|
| `The check needs the backend, and it does not answer right now. Nothing was saved.` | `Die Prüfung braucht das Backend, und es antwortet gerade nicht. Nichts gespeichert.` | Z14 |
| `This backend version cannot run the check. Bring both halves of Findling to the same version.` | `Diese Backend-Version kann die Prüfung nicht fahren. Beide Hälften von Findling auf dieselbe Version bringen.` | Z15 |
| `A check is already running. Its result appears here.` | `Eine Prüfung läuft bereits. Ihr Ergebnis erscheint hier.` | Z16 |
| `Saved. %s applies from the next indexing round.` | (wie oben) | Z5 Erfolg |
| `The profile was not saved. Nothing changed.` | `Das Profil wurde nicht gespeichert. Es hat sich nichts geändert.` | Z17 |
| `The memory guard lowered the profile: chosen %1$s, in force %2$s (%3$s).` | `Der Speicherwächter hat das Profil abgesenkt: gewählt %1$s, wirksam %2$s (%3$s).` | Z10, %3$s = Bestands-Ursachensätze `memory_max_repeated`/`oom_kill`/`unclean_end` |
| `The fp32 model is not available. The search uses int8.` | `Das fp32-Modell ist nicht verfügbar. Die Suche nutzt int8.` | `fp32_unavailable` |
| `fp32 is set, but this box has too little memory for it. The search uses int8.` | `fp32 ist gesetzt, aber diese Box hat zu wenig Speicher dafür. Die Suche nutzt int8.` | `fp32_on_a_tight_box` |
| `fp32 is only available in Standard and Performance. The search uses int8.` | `fp32 gibt es nur in Standard und Leistung. Die Suche nutzt int8.` | `fp32_not_in_economy` |
| `fp32 stays active under Economy. To go back to int8, choose Standard or Performance and clear the tick.` | `fp32 bleibt unter Sparsam aktiv. Zurück zu int8: Standard oder Leistung wählen und das Häkchen entfernen.` | `fp32_active_in_economy` |
| `The fp32 model is being downloaded.` | `Das fp32-Modell wird heruntergeladen.` | `downloading` außerhalb einer Probe (occ-Weg) |

Entfallende Schlüssel (in allen 16 Dateien löschen, Ausnahmelisten der Gates mitziehen): `To lift the reduction after checking the memory: %1$s`.

Tonregel: kurze Sätze, keine Erzählabsätze (Owner-Regel Kurze Produkttexte), keine Em-/En-Dashes, echte Umlaute, keine Emojis. Profilnamen immer aus den drei Bestandsschlüsseln, nie frei geschrieben.

---

## Sicherheits- und Datenregeln der Oberfläche

- Kein Wort des Containers wird Teil eines Satzes: Profil, Präzision, Schritt, Verdikt, Ursache, Env-Name sind Codes aus geschlossenen Mengen, PHP (Serverrender) und JS (Poll) bilden sie auf dieselben Katalogsätze ab; unbekannter Code blendet die Zeile aus. Wortgleichheit PHP/JS per Gate wie bei den Engine-Sätzen.
- Werte werden nur mit `p()` bzw. `textContent` ausgegeben.
- Der Bestätigungs-Token (D-26-04) wird nie gerendert, weder im Markup noch im Initial State; "Erneut prüfen" schickt nur das Profil, der Token wird serverseitig angehängt.
- Schreib- und Probe-Aufrufe nur mit `requesttoken`-Header (CSRF), Admin-Sitzung; die UI schickt ausschließlich `profile` ∈ {economy, standard, performance} und `precision` ∈ {int8, fp32}.

---

## Doku-Folgen (für den Plan)

- `docs/admin-page.md`: neuer Abschnitt "Das Leistungsprofil" mit Zuständen und Abwärtswegen; Abschnitt "Die Wächterzeilen" ohne occ-Rückweg, mit Verweis auf "Erneut prüfen"; "Keinen Erweitert-Bereich" um den Satz ergänzen, dass Auswahlfeld plus Häkchen ADM-04 wahren.
- `docs/profiles.md` / `docs/embeddings.md` §11: occ als Weg ohne Probe (D-27-13), "Bis zur Einstellungsseite (Phase 27) per occ" umformulieren.
- ROADMAP SC1: "Beim sicheren Standard bleiben" zu "Bei Sparsam bleiben" (D-27-11).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| keine (kein shadcn, kein npm im Companion) | keine | nicht anwendbar |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
