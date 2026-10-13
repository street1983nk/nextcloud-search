---
phase: 32-filter-in-der-unified-search
plan: 07
subsystem: PHP-Companion (Unified-Search-Plugin, Suchprovider, Symbole), Backend-Tests (Vertrag), Abnahmeprotokoll
tags: [usrch-01, usrch-02, d-32-04, owner-abnahme, playwright, befund-a, symbol, theming]
requires:
  - phase: 32
    provides: "32-01 bis 32-06: types und folder im Provider, Plugin mit sieben Einträgen, Kataloge, CI-Belege"
provides:
  - "Owner-Abnahme 13.10.2026 der sieben Menüeinträge, Chips, Ordnerauswahl, Treffer und des Wortlauts de/en/fr (unverändert)"
  - "Befund A gefixt: versteckter Provider Search\\FilterProvider (findling-filter), eine Findling-Gruppe in der ungefilterten Suche (4d616071)"
  - "Weiße Lupe an allen acht Findling-Einträgen: app-white.svg für die sieben Filtereinträge (f4fc7efa), findling.svg für den Eintrag des echten Providers (f60ca146)"
  - "Vertragstest: Datei unter der Provider-ID existiert, zeichnet die Lupe nur weiß, Navigation nennt weiter app.svg"
  - "Saat /Abnahme32 und /Woanders32 samt Share 3 geräumt, Containerzeilen tombstoned"
affects: [32-08 Audit, REL-05 Store-Text und Release]
tech-stack:
  added: []
  patterns:
    - "Symboldatei unter der Provider-ID, weil SearchComposer::fetchIcon <provider id>.svg vor app.svg fragt"
    - "Dev-Cache: Skript und Bilder per fetch(url, {cache: 'reload'}) erneuern, bevor im Browser gemessen wird"
    - "Löschen auf Dev: erst cron.php (SubtreeExpandJob), dann trashbin:cleanup"
key-files:
  created:
    - php/lib/Search/FilterProvider.php
    - php/img/app-white.svg
    - php/img/findling.svg
    - .planning/phases/32-filter-in-der-unified-search/32-07-ABNAHME.md
  modified:
    - php/js/unified-search.js
    - php/lib/AppInfo/Application.php
    - backend/tests/test_unified_search_plugin.py
    - REUSE.toml
    - THIRD-PARTY.md
    - docs/search-filters.md
    - .github/workflows/deploy-harp.yml
decisions:
  - "Befund A mit Option A1 (Owner 13.10.2026): Chips fragen den versteckten Provider findling-filter, der echte Provider findling bleibt die eine Gruppe ohne Chip"
  - "Wortlaut de/en/fr unverändert abgenommen, Präfix 'Dateiinhalte:' bleibt, normales Leerzeichen vor dem Doppelpunkt im Französischen"
  - "Symbol: weiße Lupe für alle acht Einträge; findling.svg statt app.svg weiß, damit die App-Navigation unverändert bleibt"
  - "Nebenwirkung angenommen (Owner: 'mach wie deine Empfehlung'): Theming-Tab- und Homescreen-Symbol der Findling-Seiten werden weiße Lupe statt leerem Quadrat"
  - "Die 1011 verwaisten Messzeilen aus 32-03 bleiben im Dev-Index, Befund zum Abgleich geht an 32-08"
metrics:
  duration: "Task 3 ca. 120 min inkl. ca. 13 min Volltestlauf und CI"
  completed: 2026-10-13
  tasks: 3
  files: 4
---

# Phase 32 Plan 07: Owner-Abnahme der Filter in der Unified Search Summary

Der Owner hat die Filter in der Unified Search am 13.10.2026 an der Dev-Instanz abgenommen: Wortlaut de/en/fr unverändert, Verhalten "Abgenommen", alle acht Findling-Einträge tragen die weiße Lupe. Vor dem Checkpoint wurde Befund A (sieben Scheingruppen, achtfache Anfrage) mit einem versteckten Provider gefixt; USRCH-01 und USRCH-02 sind Complete.

## Commits

| Commit | Inhalt |
|---|---|
| `7a175905` | docs: Playwright-Proben vor der Owner-Abnahme (Task 1) |
| `4d616071` | fix: Chips fragen den versteckten Provider findling-filter, keine Scheingruppen (Befund A) |
| `5d9c734b` | docs: Befund A Fix, Belege und Browser-Nachprobe |
| `f4fc7efa` | fix: sieben Einträge tragen `app-white.svg` |
| `9a57c904` | docs: Owner-Antworten 13.10.2026 und Symbolmessung |
| `f60ca146` | fix: Eintrag "Dateiinhalte" trägt die weiße Lupe über `findling.svg` |
| docs(32-07) | Protokoll, SUMMARY, STATE, ROADMAP, REQUIREMENTS (dieser Abschluss) |

## Task 1: Proben vorab

Zwölf Proben per Playwright auf 8090 gefahren und protokolliert (32-07-ABNAHME.md, Probentabelle), dazu Zusatzprobe Z1 rot: Befund A.

## Task 2: Owner-Abnahme

Antworten wörtlich im Protokoll ("So lassen", "Ja, Findling-Symbol", "Abgenommen", "So abnehmen", "ok", "mach wie deine Empfehlung").

## Task 3: Nachziehen, Vermerk, Aufräumen

- Wortlaut: keine Änderung verlangt, daher kein Katalog- und kein Doku-Commit.
- Symbol des Haupteintrags: Kern stable33 bis stable35 gelesen. `SearchComposer::fetchIcon` fragt `findling.svg` vor `app.svg`; die Navigation nimmt `<icon>app.svg</icon>` aus `info.xml`. `php/img/findling.svg` angelegt, REUSE.toml und THIRD-PARTY.md nachgezogen, Vertragstest mit vier Gegenproben (Datei fehlt, `currentColor`, `#000`, Navigation umgestellt: je rot).
- Messung 8090 (Bilder `owner-8-symbol.png`, `owner-8-symbol-dunkel.png`): alle acht Findling-Einträge wie die Kerneinträge, Abstand Symbol zu Grund hell 255, dunkel 232; ungefiltert genau eine Findling-Gruppe; Navigation weiter `app.svg`, ausgeliefert byte-gleich mit dem Stand vor dem Commit.
- Nebenwirkung: Tab- und Homescreen-Symbol (`touchicon-vor.png` leeres Quadrat, `touchicon-nach.png` weiße Lupe, frisch per `IconBuilder` erzeugt). Das Theming hält das alte Bild im Zwischenspeicher je Cachebuster; auf bestehenden Instanzen erscheint die Lupe erst nach einem neuen Cachebuster, auf 8090 liefert die Route weiter das alte Bild.
- Aufräumen: `/Abnahme32` und `/Woanders32` per WebDAV gelöscht (204), Share 3 weg, `cron.php` vor dem Papierkorb (zwei SubtreeExpandJob), danach `trashbin:cleanup testuser`. PROPFIND `/Abnahme32` 404; 11 Saatzeilen im Container tombstoned, 0 ACL, 0 Dokumente in tantivy (Positivkontrolle: 1011 Messdokumente gefunden); Suche `abnahme32` 0, Kanarie 1.

## Gates und CI

- Lokal vor `f60ca146` (aus `backend/`, `PYTHONUTF8=1`): pytest 5628 passed, 30 skipped (darunter `test_php_acl_boundary.py` unverändert grün); ruff check, ruff format --check, pyright latest 0 Fehler, vulture ohne Befund; `node --check php/js/unified-search.js`; `reuse lint` konform.
- CI `f60ca146`, alle acht grün (je `gh run watch --exit-status`): Python gates 38361677147, PHP and store metadata gates 38361677194, Security scans 38361677104, OpenSSF Scorecard 38361677013, Multi-arch image 38361677007, Resilience 38361677356, Integration 38361677059, HaRP deploy 38361677008.
- CI `f4fc7efa`: alle acht grün (Python 38352605822, PHP 38352605882, HaRP 38352605823, Integration 38352605877).
- CI `4d616071`: PHP 38347181812 (661 Tests), Python 38347181819, Integration 38347181828, HaRP 38347181759 grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Befund A: sieben Scheingruppen und achtfache Anfrage ohne Chip**
- **Found during:** Task 1 (Zusatzprobe Z1)
- **Issue:** Der Kern führt jeden `registerFilterAction`-Eintrag als Provider und fragt ihn ohne Chip unter `searchFrom` ab; mit `searchFrom: 'findling'` sieben Doppelgruppen und acht gleiche Anfragen je Suchbegriff.
- **Fix:** Owner-Entscheid Option A1: versteckter Provider `findling-filter` (`getOrder` null, leer ohne `types`/`folder`), Callback setzt `this.filters`, Wurzel sendet `folder=/`.
- **Files modified:** php/lib/Search/FilterProvider.php, php/lib/AppInfo/Application.php, php/js/unified-search.js, Tests, docs/search-filters.md, deploy-harp.yml
- **Commit:** 4d616071

**2. [Abweichung Symbol] currentColor im img unsichtbar**
- **Found during:** Owner-Runde (Frage Symbol)
- **Issue:** Die Einträge trugen schon `app.svg`, das in `currentColor` zeichnet; als `img` ist das schwarz, der Kern invertiert hell zu Weiß auf Weiß, dunkel bleibt es Schwarz auf Dunkel. Kein Symbol zu sehen.
- **Fix:** weiße Dateien `app-white.svg` (sieben Einträge) und `findling.svg` (Haupteintrag), `app.svg` und Navigation unverändert.
- **Commits:** f4fc7efa, f60ca146

**3. [Nebenwirkung, Owner-Entscheid] Theming-Tab- und Homescreen-Symbol**
- `findling.svg` wird auch vom Theming zuerst gelesen; dem Owner vor dem Commit gemeldet, auf "mach wie deine Empfehlung" angenommen und im Protokoll mit Vorher- und Nachher-Bild belegt.

**4. Browser ohne Playwright-MCP**
- Die Nachproben nach dem Fix und die Symbolmessung liefen mit lokalem Playwright 1.63 (Chromium headless) per Skript, gemessen über DOM, Canvas und Netzwerk.

### Lehre auf Dev (Cache)

Die Dev-Instanz liefert Skript und Bilder mit langer Cache-Dauer aus. Vor jeder Browser-Messung nach einer Änderung unter `php/` die geänderten Adressen per `fetch(url, {cache: 'reload'})` holen und den Stand prüfen (Skript enthält die Änderung, SVG weiß), sonst misst man den alten Stand. Das Theming-Symbol hängt zusätzlich am Cachebuster des Theming.

## Deferred Issues

- Die 1011 Messdateien aus 32-03 (IDs 730 bis 1740) stehen weiter im Dev-Container-Index (ohne `deleted_at`, mit ACL, 1011 Dokumente). Auf dem Weg der Saat nicht zu bereinigen, weil die Dateien samt Papierkorb seit 32-03 weg sind. Für 32-08: Der Abgleich vom 13.10. 01:08 (Nachholzyklus) meldete `seen=1488 stale=0 missing=0`, obwohl `oc_filecache` keine dieser IDs mehr kennt; nach `_GONE_IN_RANGE_SQL` müssten sie als fehlend gelten. Nicht untersucht, Dev unverändert gelassen.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: eine statische SVG-Datei ohne Skript und ohne externe Verweise; `findling-filter` ist in 4d616071 mit derselben Rechteprüfung wie der echte Provider belegt.

## Self-Check: PASSED

- php/img/findling.svg, php/img/app-white.svg, php/lib/Search/FilterProvider.php, 32-07-ABNAHME.md vorhanden.
- Commits 7a175905, 4d616071, 5d9c734b, f4fc7efa, 9a57c904, f60ca146 im Log.
- Bilder im Scratch `abnahme32\`: owner-8-symbol.png, owner-8-symbol-dunkel.png, touchicon-vor.png, touchicon-nach.png.
