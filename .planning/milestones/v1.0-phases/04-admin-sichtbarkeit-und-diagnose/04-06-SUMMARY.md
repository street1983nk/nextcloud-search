---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 06
subsystem: ui
tags: [php, nextcloud, admin-settings, l10n, mount-cache, migration, accessibility]

# Dependency graph
requires:
  - phase: 04-05
    provides: "Bloecke 1 und 2 der Admin-Seite, overview() mit coverage und estimate, admin.js mit Poll-Schleife, admin.css, l10n/de"
  - phase: 04-04
    provides: "FileStateService::countByReason(), ScanStatsService, der 55-MB-Testkorpus-Eintrag fuer skipped(too_large)"
  - phase: 02
    provides: "findling_file_state als Rueckkanal mit Zustand und Grundcode"
provides:
  - "FileStateService::reasonsByState(): Grund-Aufschluesselung je Zustand, immer alle drei Zustaende"
  - "FileStateService::page(): geklemmte Seite je Zustand und Grund, nach Aktualitaet sortiert"
  - "FileStateService::forFile(): dieselbe Zeilenform fuer genau eine Datei (Basis der Pro-Datei-Diagnose in 04-07)"
  - "PathResolverService: fileid zu Besitzer und lesbarem Pfad ueber IUserMountCache, Stapelauflösung ueber IFileAccess, Papierkorb-Erkennung"
  - "AdminViewService::overview().errors: Gruppen mit Label, Abhilfe, bis zu 20 Beispielpfaden und Restzaehler"
  - "Block 3 der Admin-Seite (Tabelle, Zustands-Chips, Aufklapp-Buttons, Leerzustand)"
  - "Index findling_fs_upd (state, updated_at)"
  - "Deutsche Label und Abhilfe-Saetze fuer alle 20 Grundcodes plus Unbekannter-Grund-Fallback"
affects: [04-07, 04-08, 04-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pfadauflösung ausschliesslich PHP-seitig zur Anzeigezeit (D-03), Container liefert nur Zahlen"
    - "Geschlossene Label- und Abhilfe-Abbildung mit genau einem Fallback-Zweig, nie ein Rohcode allein"
    - "Nicht auflösbare fileid bleibt mit Ersatztext in der Liste, Kuerzung immer mit sichtbarem Restzaehler"
    - "Aufklapp-Buttons liegen hidden im Markup und werden vom Skript sichtbar gemacht, damit ohne JavaScript keine tote Bedienelemente entstehen"

key-files:
  created:
    - php/lib/Service/PathResolverService.php
    - php/lib/Migration/Version001000Date20260904000000.php
  modified:
    - php/lib/Service/FileStateService.php
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/l10n/de.json
    - php/l10n/de.js

key-decisions:
  - "Die Label- und Abhilfe-Abbildung deckt 20 Codes ab, obwohl FileStateService::REASONS heute 19 hat: excluded steht schon im UI-Vertrag und kommt mit Plan 04-08; REASONS bleibt unangetastet, weil die drei Grundlisten nur gemeinsam wachsen duerfen (Pitfall 13)"
  - "page() liest einen null-Grund als kein Filter und nicht als Zeilen ohne Grund; eine Gruppe mit leerem Grundcode bekommt daher keine Beispiele, aber ihre Zahl und den vollen Restzaehler"
  - "MAX_PAGE = 50 in FileStateService, 20 Beispiele je Gruppe in AdminViewService: die Grenze ist die Auflösungskosten und ausdruecklich nicht der MAX_LIST_LENGTH-Gotcha aus CR-01"
  - "findling_fs_upd traegt nur (state, updated_at); der zweite Sortierschluessel file_id bricht nur Gleichstaende und wuerde jeden Indexeintrag verbreitern"
  - "Die Beispielpfade werden im Poll nie neu gebaut, nur die Gruppenzahlen; sonst zerstoert jede Aktualisierung den geoeffneten Zustand und den Tastaturfokus"
  - "Drei Grundcodes teilen denselben Abhilfe-Satz (Wortlaut des UI-Vertrags), deshalb 20 Label-Schluessel und 18 Abhilfe-Schluessel in l10n"

patterns-established:
  - "Kostenvertrag im Docblock: describeMany nennt Abfragen je Zeile und leitet daraus die Aufrufregel ab (eine Seite, nie die Tabelle)"
  - "Zustands-Chip aus Icon plus Wort plus Farbpaar, vier Gestalten (skipped, failed, truncated, excluded)"

requirements-completed: [ADM-01]

# Metrics
duration: 22 min
completed: 2026-09-02
---

# Phase 04 Plan 06: Fehlerliste mit Grund, Abhilfe und Beispielpfaden Summary

**Die Admin-Seite zeigt nicht indexierte Dateien nach Grund gruppiert, mit deutschem Label, Abhilfe-Satz und bis zu 20 vollstaendigen Beispielpfaden, die aus fileids ueber den Mount-Cache in der Besitzersicht entstehen.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-02T17:52:00Z
- **Completed:** 2026-09-02T18:14:46Z
- **Tasks:** 3
- **Files modified:** 9 (2 neu, 7 geaendert)

## Accomplishments

- `FileStateService` hat drei neue Leser: `reasonsByState()` (Grund-Aufschluesselung, immer alle drei Zustaende), `page()` (geklemmte Seite je Zustand und Grund, `updated_at` absteigend mit `file_id` als Gleichstandsbrecher) und `forFile()` (dieselbe Zeilenform fuer eine Datei, Basis von 04-07). `record()`, `counts()`, `STATES` und `REASONS` sind Zeichen fuer Zeichen unangetastet.
- Migration `Version001000Date20260904000000` legt `findling_fs_upd (state, updated_at)` an, `hasTable`- und `hasIndex`-geschuetzt. Live geprueft: Index existiert, zweiter `occ upgrade`-Lauf ist ein No-op.
- `PathResolverService` loest eine fileid ueber `IUserMountCache::getMountsForFileId` zu Besitzer und lesbarem Pfad auf, waehlt die Besitzersicht ueber den Mount mit leerem `getRootInternalPath()`, erkennt eine Datei im Papierkorb und degradiert bei jedem Fehler auf "nicht auflösbar" mit einer `debug`-Zeile ohne Pfad. `describeMany()` macht genau eine Stapelabfrage `IFileAccess::getByFileIds` je Seite.
- `AdminViewService::overview()` liefert `errors.groups`: je Grund `state`, `reason`, `count`, `label`, `remedy`, `examples`, `remaining`, sortiert absteigend nach Anzahl und bei Gleichstand alphabetisch nach Label. Quelle der Zahlen ist die Nextcloud-Sicht; `backend.reasons` steht unverrechnet daneben.
- Block 3 des Templates ist eine echte `<table>` mit `<caption class="hidden-visually">` und `<th scope="col">`, Zustands-Chips mit MDI-Inline-SVG, Abhilfe-Satz, Aufklapp-Button mit `aria-expanded`/`aria-controls`, bis zu 20 Beispielpfad-Buttons und der Zeile `und %n weitere`. Ohne JavaScript ist alles offen und es gibt keinen toten Button.
- Deutsche Fassungen aller 20 Label und aller Abhilfe-Saetze plus Tabellenkopf, Aufklapp-Texte, Restzaehler, Ersatztext, Papierkorb-Zusatz, Leere-Liste-Satz und `Unbekannter Grund (%s)` in `de.json` und `de.js`, Schluessel fuer Schluessel deckungsgleich.

## Task Commits

1. **Task 1: Die PHP-Seite kann Gruende aufschluesseln und Seiten liefern** , `3c40c7e` (feat)
2. **Task 2: Aus einer fileid wird ein lesbarer Pfad** , `862d14c` (feat)
3. **Task 3: Block 3 zeigt die Fehlerliste** , `65754a5` (feat)

## Files Created/Modified

- `php/lib/Service/PathResolverService.php` , fileid zu Besitzer und Pfad, Stapelauflösung, Papierkorb-Erkennung, kein Dateihandle und kein Pfad im Log
- `php/lib/Migration/Version001000Date20260904000000.php` , Index `findling_fs_upd (state, updated_at)`
- `php/lib/Service/FileStateService.php` , `MAX_PAGE`, `reasonsByState()`, `page()`, `forFile()`, Zeilenform und Zeitstempel-Umwandlung
- `php/lib/Service/AdminViewService.php` , `errors`-Teilbaum, geschlossene Label- und Abhilfe-Abbildung mit 20 Codes plus Fallback, `IL10N` und `PathResolverService` injiziert
- `php/templates/admin.php` , Block 3 samt Zustands-Chips, Aufklapp-Buttons, Beispielpfaden und Leerzustand
- `php/js/admin.js` , `errorsBlock()` (nur Zahlen), `setupErrorGroups()` (Zuklappen und Buttons sichtbar machen), Fehlergruppen im Fingerprint
- `php/css/admin.css` , Tabellen- und Beispiel-Regeln, `overflow-wrap: anywhere`, Mindesthoehe `var(--default-clickable-area)`, Chip-Varianten fuer skipped, failed, truncated und excluded
- `php/l10n/de.json`, `php/l10n/de.js` , 55 neue Schluessel, echte Umlaute, keine Em-Dashes

## Decisions Made

- **20 Label gegen 19 Grundcodes.** Der UI-Vertrag fuehrt `excluded` als 20. Grund, `FileStateService::REASONS` hat ihn noch nicht. Die Abbildung deckt beide Faelle ab: `excluded` ist von Anfang an dabei (Plan 04-08 traegt ihn dann in alle drei Grundlisten ein), und `REASONS` wurde nicht angefasst, weil `test_extract_errors.py` und `test_allowlist_parity.py` die drei Listen in beiden Richtungen vergleichen und nur ein gemeinsamer Diff sie gruen laesst (Pitfall 13).
- **`page()` mit null-Grund heisst "kein Filter".** Damit ist `page('failed', null, ...)` fuer 04-07 brauchbar. Preis: eine Gruppe mit leerem Grundcode kann keine Beispiele holen, weil sie sonst die Zeilen aller anderen Gruppen desselben Zustands unter ihr Label bekaeme. Sie zeigt ihre Zahl und den vollen Restzaehler, verschwindet also nicht. Kein Schreiber dieser App erzeugt so eine Zeile.
- **Aufklapp-Button liegt `hidden` im Markup.** Der UI-Vertrag verlangt `aria-expanded="false"` im Markup und gleichzeitig offene Gruppen ohne JavaScript. Beides zusammen waere eine Falschaussage an den Screenreader und ein Button, der ohne Skript nichts tut. Also: Gruppen offen, Button verborgen, und das Skript klappt zu und macht den Button sichtbar.
- **Chip-Bauform vier statt drei.** `truncated` und `excluded` sind im Zustands-Inventar eigene Zustaende; unter dem Label "Uebersprungen" bzw. "Indexiert" wuerden beide als Defekt gelesen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `ownerMountOf()` griff auf Index 0 eines gefilterten Arrays zu**
- **Found during:** Task 2 (PathResolverService)
- **Issue:** Der verifizierte Zielcode aus `04-RESEARCH.md` Beispiel 3 endet mit `return $mounts[0];`. `getMountsForFileId()` filtert die Mount-Liste im Server, und ein gefiltertes PHP-Array behaelt die Schluessel des Ausgangsarrays. Auf einer Instanz, bei der der erste Mount einer Datei herausgefiltert wird, waere das ein undefinierter Index gewesen.
- **Fix:** `return reset($mounts);` mit der Begruendung im Docblock.
- **Files modified:** `php/lib/Service/PathResolverService.php`
- **Verification:** `php -l` gruen, Live-Probe `describe()` gegen fuenf echte fileids und drei Papierkorb-Eintraege.
- **Committed in:** `862d14c`

**2. [Rule 2 - Missing Critical] `describe()` faengt jetzt jeden Fehler ab**
- **Found during:** Task 2
- **Issue:** Der Zielcode aus dem Research hat kein try/catch. `getUser()` laedt den Besitzer nachtraeglich und wirft bei einer Mount-Zeile auf einen geloeschten Nutzer; ohne Abfangen haette eine einzige verwaiste Zeile die ganze Admin-Seite mit einer Ausnahme beendet, also genau die Seite, die man in diesem Zustand aufruft.
- **Fix:** try/catch um den ganzen Rumpf, degradieren auf `null` plus eine `debug`-Zeile ohne fileid und ohne Pfad, wie im Muster von `Search/Provider.php`.
- **Files modified:** `php/lib/Service/PathResolverService.php`
- **Verification:** Live-Probe mit fileid 0, mit einer nicht existierenden fileid und mit 25 unauflösbaren fileids: Zeilen bleiben mit Ersatztext, keine Ausnahme.
- **Committed in:** `862d14c`

**3. [Rule 3 - Blocking] Bezeichner `fopen` und `getFirstNodeById` aus der Prosa entfernt**
- **Found during:** Task 2
- **Issue:** Die Aufgabe verlangt einen Docblock, der beide Namen nennt, und das Abnahmekriterium verlangt, dass die Datei keinen der beiden enthaelt. Beides zeichengleich ist unmoeglich.
- **Fix:** Der Docblock nennt die Sache ohne die Bezeichner ("kein Dateihandle, kein Stream, kein Inhalt, kein Snippet", "und ausdruecklich nicht die Node-Suche per id, die getUserFolder() anbietet") und sagt in einem Satz, warum die vier Namen nirgends ausgeschrieben stehen. Damit ist der Grep auf die vier Aufrufe null und die Begruendung erhalten.
- **Files modified:** `php/lib/Service/PathResolverService.php`
- **Verification:** `grep` auf `fopen`, `getContent`, `fread`, `getFirstNodeById` ist null.
- **Committed in:** `862d14c`

**4. [Rule 2 - Missing Critical] Fehlergruppen im Fingerprint des Polls**
- **Found during:** Task 3 (admin.js)
- **Issue:** Der Fingerprint entscheidet, ob sich etwas geaendert hat, und drosselt nach 20 unveraenderten Abfragen auf 30 Sekunden. Ohne die Gruppenzahlen darin haette eine Instanz, auf der nur die Fehlerzahlen steigen, als "nichts passiert" gegolten und die Zahlen waeren im Ruhetakt nachgelaufen.
- **Fix:** `errorSignature(view)` haengt `state:reason:count` aller Gruppen an den Fingerprint.
- **Files modified:** `php/js/admin.js`
- **Verification:** UI-Gate gruen, `innerHTML` weiterhin null, Kadenz-Test der Gate-Datei unveraendert.
- **Committed in:** `65754a5`

### Abweichung ohne Fix

**5. [Abnahmekriterium] 18 statt 20 Abhilfe-Schluessel in `l10n/de.json`**
- Das Kriterium erwartet 20 uebersetzte Abhilfe-Schluessel. Die Tabelle des UI-Vertrags gibt drei Codes (`timeout`, `gateway_error`, `ocr_failed`) woertlich denselben Satz "Wird beim naechsten Lauf erneut versucht.", und identische Quellstrings sind in l10n ein Schluessel. Kuenstlich unterschiedliche englische Saetze nur zum Erreichen der Zahl waeren eine Verschlechterung des Wortlauts. Erfuellt ist die Sache dahinter: jeder der 20 Codes hat genau ein Label und genau einen Abhilfe-Satz, keiner ist leer, und die Label sind alle 20 verschieden. Geprueft mit einem Skript, das die Abbildung aus `AdminViewService` liest und jeden Quellstring in beiden l10n-Dateien sucht: 0 fehlende Uebersetzungen, 0 Schluessel nur in einer der beiden Dateien.

---

**Total deviations:** 4 auto-fixed (1 Bug, 2 Missing Critical, 1 Blocking) plus 1 dokumentierte Abweichung von einer Zahl in einem Abnahmekriterium
**Impact on plan:** Kein Scope-Zuwachs. Zwei der Fixes haerten den uebernommenen Research-Code gegen genau die Instanz, auf der man diese Seite aufruft.

## Verification Results

| Pruefung | Ergebnis |
|----------|----------|
| `cd backend && uv run python -m pytest -q` | 740 passed, 11 skipped |
| `pytest tests/test_extract_errors.py tests/test_allowlist_parity.py -q` | 55 passed (REASONS unveraendert) |
| `pytest tests/test_admin_ui_contract.py -q` | 13 passed |
| `php -l` ueber `lib`, `appinfo`, `templates` im Container | ausschliesslich "No syntax errors detected" |
| `occ upgrade` zweimal | erster Lauf setzt 0.3.0, zweiter Lauf "No upgrade required" |
| Index `findling_fs_upd` | `CREATE INDEX findling_fs_upd ON oc_findling_file_state (state, updated_at)` |
| `grep -c "const REASONS = \["` | 1 |
| `grep`: `findling-errors` 13, `aria-expanded` 1, `scope="col"` 3, `hidden-visually` 1 | alle grosser 0 |
| `grep`: `print_unescaped` 0, `innerHTML` 0, `text-overflow: ellipsis` 0, `overflow-wrap` 4 | wie gefordert |
| `grep` in `PathResolverService`: `fopen`, `getContent`, `fread`, `getFirstNodeById` | 0 |
| Label- und Abhilfe-Abbildung | 20 Zeilen, 20 verschiedene Label, 18 verschiedene Abhilfe-Saetze, 1 Fallback-Zweig |
| l10n-Parität `de.json` gegen `de.js` | keine Differenz in beiden Richtungen, `de.json` ist gueltiges JSON |
| Em-Dash und En-Dash in allen neun Dateien | keiner |

**Live-Sichtproben** (lokale Instanz auf Port 8090, `default_language=de`, Rendern ueber `OC_Template('findling','admin')`):

- Fuenf Gruppen mit korrektem Label, korrekter Abhilfe und korrektem Chip: `corrupt` (Datei beschaedigt, Fehlgeschlagen), `empty_file` (Datei ist leer), `encrypted` (Passwortgeschuetzt, Uebersprungen), `truncated` (Text gekuerzt, Indexiert Text gekuerzt), `too_large` (Zu gross, Uebersprungen). Sortierung: 25 vor den vier Einsern, diese alphabetisch nach Label.
- Grenze der Beispiele: 24 `<li>` auf der ganzen Seite bei 25+1+1+1+1 Zeilen, also 20 in der grossen Gruppe, dazu die Zeile "und 5 weitere".
- Nicht auflösbare fileid: "Datei existiert nicht mehr (ID 900025)" statt eines Pfads, Zeile bleibt.
- Papierkorb: `testuser/files_trashbin/files/13-ratsvorlage-scan.pdf.d1788275762 (im Papierkorb)`.
- Aufgeloeste Pfade in der Besitzersicht: `corpus/01-text-layer.pdf`, `99-riesenprotokoll.txt` (das 55-MB-Beispiel aus 04-04), Besitzer `testuser`.
- Ohne JavaScript: die Aufklapp-Buttons tragen `hidden`, die Bereiche kein `hidden`, alle Beispielpfade sind lesbar.
- Leere Fehlerliste: genau eine Zeile "Alle Dateien sind indexiert. Nichts uebersprungen, nichts fehlgeschlagen.", keine Tabelle und kein Tabellenkopf.
- Unbekannter Grundcode: "Unbekannter Grund (brand_new_code)" als Label, nie der Rohcode allein.

Die Sichtproben liefen auf gesaeten Zustandszeilen (25 `corrupt`, je eine `encrypted`, `truncated`, `gone`) und einer eigens angelegten und dann geloeschten Datei `trash-probe.txt`. Alles davon wurde nach der Pruefung wieder entfernt: `findling_file_state` traegt wieder genau die beiden echten Zeilen (`skipped/too_large` 1, `failed/empty_file` 1), der Papierkorb-Eintrag der Probedatei ist geloescht, `default_language` ist wieder unbesetzt.

## Issues Encountered

- Die erste Papierkorb-Probe meldete `trashed: false`, obwohl die Datei im selben Aufruf geloescht worden war. Ursache ist kein Fehler dieser Klasse: `UserMountCache` haelt einen Prozess-Cache je fileid, und die Auflösung vor dem Loeschen hatte ihn gefuellt. Eine Probe in einem frischen Aufruf gegen drei echte Papierkorb-Eintraege liefert `trashed: true`. Fuer die Seite ist das ohne Folge, weil jede Anfrage ein eigener Prozess ist.

## User Setup Required

None , keine externe Dienstkonfiguration.

## Next Phase Readiness

- Plan 04-07 (Block 4, Pro-Datei-Diagnose) hat alles, was er braucht: `FileStateService::forFile()` als Stufe 4 der Vorrangregel, `PathResolverService::describe()` fuer Pfad und Besitzer, die Label- und Abhilfe-Abbildung fuer die Ergebniskarte und die Beispielpfad-Buttons samt `data-findling-path` und `data-findling-file-id` im Markup. Zu tun bleibt dort: Block 4 bauen, die Buttons aktivieren (`disabled` entfernen, `aria-describedby` auf den Platzhalter-Satz entfernen), das Scrollen und das Ausloesen der Pruefung verdrahten. Der Satz "Die Einzelpruefung ist noch nicht auf dieser Seite" verschwindet mit demselben Plan.
- Plan 04-08 (Regeln) muss `excluded` in allen drei Grundlisten gleichzeitig eintragen (`FileStateService::REASONS`, `backend/src/findling/extract/errors.py`, `backend/src/findling/store/repo.py`); Label, Abhilfe und Chip fuer den Code stehen hier bereits.
- Offen und unveraendert: `STARTUP_TEXT_DOCS_PER_HOUR` ist die einzige ungemessene Zahl der Seite und betrifft nur die erste Minute.

## Self-Check: PASSED

- `php/lib/Service/PathResolverService.php` FOUND
- `php/lib/Migration/Version001000Date20260904000000.php` FOUND
- Commit `3c40c7e` FOUND
- Commit `862d14c` FOUND
- Commit `65754a5` FOUND

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*
