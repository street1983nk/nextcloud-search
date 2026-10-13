---
phase: 32-filter-in-der-unified-search
plan: 04
subsystem: PHP-Companion (Listener, Application), Frontend-Plugin php/js, Backend-Tests (Vertrag)
tags: [usrch-01, usrch-02, d-32-04, d-32-05, unified-search, registerFilterAction, listener]
requires:
  - phase: 32
    provides: "32-01/32-02: Custom Filter types und folder im Provider, still gelesen"
provides:
  - "php/js/unified-search.js: sechs Typeinträge in TYPES-Reihenfolge und ein Ordnereintrag über OCA.UnifiedSearch.registerFilterAction, Event add-filter in setTimeout"
  - "LoadUnifiedSearchFiltersListener: BeforeTemplateRenderedEvent, nur angemeldet, Util::addScript plus Util::addTranslations"
  - "backend/tests/test_unified_search_plugin.py: Lesung des Quelltexts plus Lauf in einer node-Sandbox, mit Selbsttests"
affects: [32-05 l10n der vier neuen Sätze, 32-06 deploy-harp und Doku, 32-07 Owner-Abnahme per Playwright, 32-08 Audit]
tech-stack:
  added: []
  patterns: ["Vertrag eines Vanilla-Skripts aus zwei Richtungen: Quelltextregeln und Lauf in node vm mit gespieltem Kern"]
key-files:
  created:
    - php/js/unified-search.js
    - php/lib/Listener/LoadUnifiedSearchFiltersListener.php
    - php/tests/Unit/LoadUnifiedSearchFiltersListenerTest.php
    - backend/tests/test_unified_search_plugin.py
  modified:
    - php/lib/AppInfo/Application.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "PHP-Test über Util::getScripts() (öffentlich seit NC 24) UND über die rohen statischen Listen von OCP\\Util per ReflectionProperty (nur gelesen): getScripts() entfernt Dubletten und die Liste lebt den ganzen PHPUnit-Prozess, executionOrder defects ordnet um; die Mengendifferenz vorher/nachher macht jeden Fall reihenfolgeunabhängig"
  - "Keine eingeschleuste Ladefunktion: der Listener ruft nur zwei statische Util-Methoden, kein Konstruktorparameter"
  - "Wurzel als Ordnerwahl: filterParams {} und Chiptext 'File contents in /' (Schlüssel 'File contents in %s'); kein elfter Schlüssel. Owner sieht es in 32-07"
  - "Zweiter Klick auf den Ordnereintrag (apply false) sendet den gemerkten Ordner; ohne gemerkten Ordner öffnet sich der Picker erneut (Files tut in diesem Fall nichts)"
  - "Abbruch des Pickers sendet nichts, wie folderSearch.ts der Files-App: der Chip bleibt und sucht ohne Ordner"
  - "Ordnereintrag wird nur registriert, wenn OC.dialogs.filepicker existiert; fehlt OC.imagePath, ist das Icon leer"
  - "%s-Ersetzung mit einer Ersatzfunktion statt eines Ersatzstrings, damit $& oder $' in einem Ordnernamen Text bleiben"
  - "unified-search.js nicht in die Dateiliste von test_admin_ui_contract._sources() aufgenommen (die Liste beschreibt die zwei Seiten); der neue Test ruft scan_script und scan_prose selbst"
metrics:
  duration: "ca. 105 min inkl. ca. 13 min Volltestlauf und ca. 35 min CI"
  completed: 2026-10-13
  tasks: 2
  files: 6
---

# Phase 32 Plan 04: Filtereinträge in der Unified Search Summary

Ein Listener auf `BeforeTemplateRenderedEvent` lädt auf jeder Seite eines angemeldeten Nutzers `findling/js/unified-search` samt Katalog; das Vanilla-Skript hängt über `OCA.UnifiedSearch.registerFilterAction` sechs Typeinträge ("File contents: PDF" usw., Reihenfolge von `SearchFilters::TYPES`) und "File contents in a folder" in das Menü und gibt `filterParams` `{types: <gruppe>}` bzw. `{folder: <pfad>}` eine Runde der Ereignisschleife später über `nextcloud:unified-search:add-filter` an den Findling-Chip.

## Commit

- `68893ef0` feat(32-04): seven filter entries of findling in the unified search menu (Task 1 und 2 in einem Commit, wie im Plan vorgegeben), gepusht auf origin/main.

## Kernquellen erneut geprüft (Research gültig bis 12.11.)

Am 13.10. aus nextcloud/server stable33, stable34 und stable35 gelesen:
- `core/src/unified-search.ts`: `registerFilterAction({id, appId, searchFrom, label, callback, icon})` in allen drei Zweigen gleich; Store `unified-search-external-filters.js` legt den Eintrag mit `isPluginFilter: true` ab, die Modal-Liste der Provider enthält die Einträge (`[...providers, ...this.externalFilters]`), deshalb findet `handlePluginFilter` den Eintrag über seine eigene ID.
- `addProviderFilter` (stable34:674-704, stable35:1212-1240, stable33 identisch zu 34): `callback(!isProviderFilterApplied)` vor dem push; bereits gesetzter Chip wird entfernt und ohne `extraParams` neu angelegt (Pitfall 2 bestätigt).
- `handlePluginFilter` (stable34:828-845, stable35:1365-1380): setzt `extraParams` nur an einem vorhandenen Chip.
- `OC.dialogs.filepicker` in allen drei Zweigen wortgleich: Rückgabe ist der nutzerrelative Pfad (`'/'` für die Wurzel und für "Wählen" ohne Auswahl), Abbruch ruft den Callback nicht.
- `folderSearch.ts` (stable34, stable35 gleich): Abbruch sendet nichts, `showFilePicker === false` tut nichts.
- `Util::getScripts()` ist öffentlich (seit 24); `Util::addScript` ruft für Apps außer core selbst `addTranslations` (stable34). Der explizite Aufruf im Listener bleibt als ausgeschriebene Abhängigkeit.

## Task 1: Listener, Registrierung, PHP-Test

- `LoadUnifiedSearchFiltersListener`: `instanceof BeforeTemplateRenderedEvent` und `isLoggedIn()`, dann `Util::addScript(Application::APP_ID, 'unified-search')` und `Util::addTranslations(Application::APP_ID)`. Kein Konstruktor, keine Datenbank, kein Container, kein Dateisystem. Docblock: warum jede Seite (nicht `LoadSearchPlugins`, Pitfall 5), warum nur angemeldet, warum die Übersetzungen.
- `Application::register()`: eigene Zeile mit Kommentar, `registerEventListener(BeforeTemplateRenderedEvent::class, LoadUnifiedSearchFiltersListener::class)`.
- `LoadUnifiedSearchFiltersListenerTest` (drei Fälle): angemeldet fügt genau einmal `findling/js/unified-search` und mindestens einen Eintrag `findling/l10n/...` hinzu, sonst nichts Fremdes, und `getScripts()` enthält das Skript; nicht angemeldet und fremdes `Event` ändern die statischen Listen nicht.
- PHPUnit-Rot: lokal kein PHPUnit; die Fälle rufen eine Klasse, die vor dem Commit nicht existierte. PHPUnit-Zahl 645 (32-03) auf 648 (Lauf 38330232409), genau die drei neuen Fälle. `php -l` über die drei PHP-Dateien per php:8.3-cli sauber.

## Task 2: Plugin und Vertragstest

- `php/js/unified-search.js`: `'use strict'`, IIFE, Start bei `DOMContentLoaded` oder sofort; `TYPE_ENTRIES` als `[gruppe, Schlüssel]`; Label `t('findling', 'File contents: %s')` mit `t('findling', <Gruppenname>)`; Icon `OC.imagePath('findling', 'app')`; jeder Callback und der Start in `guarded()` (keine Ausnahme nach außen, T-32-16); Event nur über `window._nc_event_bus.emit` nach `typeof`-Prüfung, immer in `setTimeout(..., 0)`. Ordner: Picker mit Titel "Choose the folder to search in", `['httpd/unix-directory']`, `FILEPICKER_TYPE_CHOOSE`, Start `/`, `{allowDirectoryChooser: true}`; Pfad normalisiert auf einen führenden und keinen abschließenden Slash; `folder` nur bei Wert ungleich `''` und `'/'`.
- Vertragstest (25 Fälle):
  - Lesung (Kommentare entfernt, Strings bleiben): Gruppen gleich PHP `TYPES` (über `php_type_groups` aus dem Paritätstest), Gruppennamen aus den Katalogen, ID-Literale, keine ID `'findling'` (auch nicht über eine Konstante), `appId`/`searchFrom` `'findling'`, zwei Aufrufstellen von `registerFilterAction`, vier `typeof`-Prüfungen, `_nc_event_bus` nur über `window`, jedes `.emit(` innerhalb der Argumente eines `setTimeout(` (Klammerabgleich), kein Ordner-Literal, kein `|| ''`, Wächter für `''` und `'/'`, nur die zehn Schlüssel von D-32-04 und alle vier neuen benutzt, Verbotsliste; dazu `scan_script` und `scan_prose`; `node --check`.
  - Lauf in node (`vm`-Sandbox als Kern): sieben Registrierungen in TYPES-Reihenfolge mit `appId`/`searchFrom` `findling` und übersetzten Labels; jeder Typklick sendet synchron nichts und nach den Timern genau `{types: gruppe}`, auch beim zweiten Klick (`apply` false); Ordner: Picker-Argumente, `/Projekte/2026/` ergibt `{folder: '/Projekte/2026'}` und Chip "... in 2026", zweiter Klick sendet ohne neuen Picker erneut; `/` und `''` ergeben `{}`, Nicht-String nichts; Ordnername mit `$&` bleibt Text; `readyState` loading registriert erst nach `DOMContentLoaded`; ohne `OCA`, ohne `registerFilterAction`, mit werfendem `registerFilterAction`, ohne `OC.dialogs` (nur sechs), ohne `OC.imagePath` (Icon leer), ohne Bus (keine Sendung): nie ein Fehler.
  - Selbsttests auf einem eigenen Beispielskript (Positivkontrolle sauber und lauffähig): `innerHTML`, synchrones Emit (Lesung und Lauf sehen es), drei Formen eines leeren Ordnerwerts, ID `'findling'` als Literal und über Konstante, vertauschte Reihenfolge, fehlende Feature-Prüfung, fremder Schlüssel, Kommentar verdeckt nichts und erzeugt nichts.
- Gegenproben am echten Skript (Kopie im Scratchpad, danach `cmp` gleich): Emit ohne `setTimeout` 5 rot, Wurzelwächter `if (folder)` 2 rot, Gruppen pdf/documents vertauscht 3 rot, kein erneutes Senden bei `apply` false 1 rot, `.replace('%s', value)` 1 rot.
- Baumhash: `PHP_FILES_TODAY` 93 auf 95, `PHP_TREE_HASH_TODAY` e5b9c78625d8f419327bb0da94a5362ccfff0e513a299121ff9c057505710a3c, Journal "Plan 32-04" (JS zählt nicht, Rezept globt `**/*.php`).
- Store-Archiv: `scripts/release/store-archive.sh` Zeile 76 kopiert `appinfo lib templates js css img l10n`, `php/js/unified-search.js` reist also mit.

## Gates und CI

- Lokal aus backend/ mit PYTHONUTF8=1: `pytest` 5611 passed, 30 skipped (5586 + 25); `ruff check`, `ruff format --check` grün; `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` 0 Fehler; `vulture src tests --min-confidence 80` ohne Befund. `test_php_acl_boundary.py` unverändert (`git diff --quiet HEAD`) und grün.
- CI auf 68893ef0, jeweils `gh run watch <id> --exit-status` mit Exitcode 0:
  - php.yml 38330232409: grün (OK, 648 Tests, 2370 Assertions).
  - python.yml 38330232425: grün (5623 passed, 18 skipped im Runner; node vorhanden).
  - integration.yml 38330232257: grün.
  - deploy-harp.yml 38330232192: grün.
  - Außerdem grün: Resilience 38330232168, Security scans 38330232221, OpenSSF Scorecard 38330232211, Multi-arch image 38330232170.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ersatzstring von String.prototype.replace**
- **Found during:** Task 2
- **Issue:** `.replace('%s', name)` wie in admin.js liest `$&`, `$'` und `` $` `` im Ersatzstring als Muster; ein Ordnername ist Nutzereingabe (T-32-15) und wäre verfälscht im Chip gelandet.
- **Fix:** Ersetzung über eine Ersatzfunktion (`filled()`), eigener Lauffall und Gegenprobe.
- **Commit:** 68893ef0

**2. [Rule 2 - Correctness] Keine Ausnahme nach außen**
- **Found during:** Task 2
- **Issue:** Der Kern ruft den Callback vor dem push des Chips; eine Ausnahme im Callback hätte den Chip verhindert, eine beim Start fremde Seiten gestört (T-32-16).
- **Fix:** Start, Callbacks, Picker-Rückruf und Timer laufen in `guarded()`; Lauffall mit werfendem `registerFilterAction`.
- **Commit:** 68893ef0

### Präzisierungen

- Der Vertragstest prüft zusätzlich zur Lesung das Verhalten in node. Kein Skip ohne node: der Test verlangt node (GitHub-Runner haben es, Lauf 38330232425 belegt).
- `apply === false` ohne gemerkten Ordner öffnet den Picker (Plan nannte nur das erneute Senden des gemerkten Ordners).

## Known Stubs

Keine. Die vier neuen Schlüssel stehen noch in keinem Katalog; bis 32-05 zeigt das Menü auf jeder Sprache die englischen Sätze, die Gruppennamen sind schon übersetzt. So im Plan vorgesehen.

## Threat Flags

Keine neue Fläche außerhalb des Threat Models. T-32-14 (statische Datei über `Util::addScript`, Verbotsliste), T-32-15 (Ordnername nur als `filterUpdateText`, keine DOM-Erzeugung, Ersatzfunktion), T-32-16 (Feature-Erkennung, `guarded()`, Lauffälle ohne APIs), T-32-17 (IDs `findling-type-*`/`findling-folder`, Test verbietet `'findling'`) sind umgesetzt. XSS-Probe mit Ordnernamen folgt in 32-07/32-08.

## Hinweise für Folgepläne

- 32-05: Schlüssel "File contents: %s", "File contents in a folder", "File contents in %s", "Choose the folder to search in" in 16 Kataloge; `ALLOWED_KEYS`/`NEW_KEYS` in test_unified_search_plugin.py sind die Liste.
- 32-07: Playwright prüft Doppelklick auf Typ- und Ordnereintrag, Abbruch des Pickers (Chip bleibt ungefiltert), Wurzelwahl ("File contents in /"), Annahme A3 (`window._nc_event_bus` zum Klickzeitpunkt).

## Self-Check: PASSED

- Dateien vorhanden: php/js/unified-search.js, php/lib/Listener/LoadUnifiedSearchFiltersListener.php, php/tests/Unit/LoadUnifiedSearchFiltersListenerTest.php, backend/tests/test_unified_search_plugin.py.
- Commit 68893ef0 in `git log` und auf origin/main.
- Akzeptanz: `registerEventListener(.*BeforeTemplateRenderedEvent` trifft Application.php:130; Listener ohne ExAppService/IDBConnection/IRootFolder; `innerHTML|eval(|console.` im Skript leer; `registerFilterAction` 5 Treffer, Lauf zählt sieben Registrierungen; `node --check` 0; PHP_FILES_TODAY 95.
