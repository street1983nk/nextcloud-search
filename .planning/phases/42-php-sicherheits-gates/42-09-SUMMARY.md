---
phase: 42-php-sicherheits-gates
plan: 09
subsystem: Python-Gates (Textsperren PHP-Hälfte, ExApp-Fläche)
tags: [python-gates, text-bans, info-xml, exapp-routes, appapi, gap-closure, G42-1]
requires:
  - 42-04 (RouteProfiles::SERVER_ANNOTATION_NAMES)
provides:
  - backend/tests/test_php_surface_bans.py (18 Annotationen in php/lib, Router-/Container-Texte, routes.php, info.xml der Companion-App; Gleichschritt mit RouteProfiles)
  - backend/tests/test_exapp_surface.py (ExApp-Routentabelle exakt, PUBLIC/headers_to_exclude als Regel, keine AppAPI-Registrierung zur Laufzeit, OCS-Präfix)
affects:
  - Phasenverifikation 42
tech-stack:
  added: []
  patterns:
    - "Textseite der PHPUnit-Sperren in python.yml, auch bei reinen Backend-Commits und montags"
    - "backend/src per ast, Docstrings ausgenommen"
key-files:
  created:
    - backend/tests/test_php_surface_bans.py
    - backend/tests/test_exapp_surface.py
  modified: []
decisions:
  - "LIB_BANS ohne Einschränkung von '->action(': grep über php/lib ergab 0 Treffer, keine Eingrenzung nötig"
  - "info.xml per ElementTree aus Bytes geparst (die Datei trägt eine XML-Deklaration)"
  - "Die Annotation-Sperre meldet je Treffer Datei und Zeile, auch in Klassen-Docblocks und Methoden ohne Route"
metrics:
  completed: 2026-11-05
  tasks: 2
  files: 2
---

# Phase 42 Plan 09: Python-Textsperren und exakte ExApp-Routentabelle Summary

Zwei neue Python-Gates halten die Textseite der PHP-Sperren (Annotationen, Router- und Container-Zugriffe, routes.php, remote/public/sabre und Co. in info.xml, exakte settings-Kinder) und die ExApp-Fläche (fünf Routen exakt, PUBLIC und headers_to_exclude als eigene Regel, keine AppAPI-Registrierung zur Laufzeit, nur eigene OCS-Pfade) auch bei reinen Backend-Commits und im Wochenlauf.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | 0aed7906 | test(42-09): text bans for the php half and an exact ExApp route table |

## Belege

- Vorprüfung: `grep -rn -- "->action(" php/lib` 0 Treffer; kein `@<Servername>` in php/lib; 65 PHP-Dateien unter php/lib; info.xml der Companion-App ohne remote/public/sabre/collaboration/activity/two-factor-providers/fulltextsearch/dashboard, settings mit admin und admin-section.
- test_php_surface_bans.py: 67 passed (echter Baum, Gleichschritt mit den 18 Namen aus RouteProfiles.php, parametrisierte Proben über alle 18 Namen, jede LIB_BANS-Zeile, jede ROUTES_BANS-Form, jedes verbotene Element, drittes settings-Kind, geänderte Admin-Klasse, Negativproben wie `#[PublicPage]`, `@PublicPageExtra`, `@param`, `admin@example.org`, `IURLGenerator`, `$this->container`).
- test_exapp_surface.py: 19 passed (Tabelle exakt, sechste Route, PUBLIC zweifach gemeldet, USER, headers_to_exclude zweifach, fehlende bruteforce_protection, vertauschte Reihenfolge, Leser erkennt geänderten access_level; backend/src: app_api-Pfad, fremder OCS-Pfad auch als f-String, jede der fünf Registrierungsflächen; Docstrings und Kommentare bleiben grün; 11 OCS-Pfade gefunden, Untergrenze 9).
- Rot-Beweise (Python-Ersetzung, danach `git checkout -- php/lib php/appinfo backend/appinfo backend/src`, `git status --porcelain` leer, je `ROLLBACK-CLEAN`); Befunde über die Scan-Funktionen am geänderten Baum, je der echte-Baum-Test rot (`1 failed`):
  - "\t * @PublicPage" im setPause-Docblock: `php/lib/Controller/SettingsController.php:506: docblock annotation @publicpage`.
  - `<remote><findling>appinfo/routes.php</findling></remote>` in php/appinfo/info.xml: `info.xml has the forbidden element <remote>`.
  - `// see OCP\Route\IRouter` in php/lib/Service/SettingsService.php: `php/lib/Service/SettingsService.php:7: IRouter`.
  - `$this;` vor dem return in php/appinfo/routes.php: `routes.php:11: $this`.
  - access_level von ^/rates$ auf USER: `the route table is (...('^/rates$', 'GET', 'USER', '[]', '[401]')...), expected (...)`.
  - `_RED_PROOF = "/ocs/v2.php/apps/app_api/api/v1/ui/files-actions-menu"` in nc/client.py: `path under app_api/ ...` und `OCS path outside /ocs/v2.php/apps/findling/ ...` (zwei Befunde, wie geplant).
  - `def _red_proof(nc): return nc.ui.resources` in nc/client.py: `backend/src/findling/nc/client.py:51: attribute .ui`.
- Python-Gates grün (ruff check/format backend und scripts, pyright 0 Fehler, vulture); pytest seriell: test_php_surface_bans 67, test_exapp_surface 19, test_info_xml_defaults 9, test_phase40_audit 65 passed und 7 skipped.
- Keine PHP-Datei geändert, Baumhash unverändert; python.yml unverändert.

## CI-Beleg

`scripts/ci/head_green.sh "$(git rev-parse HEAD)" "Python gates"` auf 0aed7906d0d8...: rc 0, sieben Läufe success (php.yml startet bei diesem Commit nicht, wie geplant):
Python gates 41956536303 (volle Suite `6807 passed, 254 skipped`, die beiden neuen Dateien darin), Integration 41956536318, HaRP deploy 41956536288, Resilience 41956536302, Multi-arch image 41956536338, Security scans 41956537240, OpenSSF Scorecard 41956536322.

## Deviations from Plan

1. [Hinweis] Plan nennt in Task 1 "zwei Rot-Beweise" im done-Text, beschreibt aber vier; in Task 2 drei; ausgeführt wurden alle sieben.
2. [Rule 2, verschärft] Zusätzlich zu den verlangten Proben: f-String mit fremdem OCS-Pfad, Pfad `/index.php/apps/app_api/x`, alle fünf Registrierungsflächen einzeln, klein geschriebener Namespace `\oc\route\`.

## Known Stubs

Keine.

## Self-Check: PASSED

- backend/tests/test_php_surface_bans.py und backend/tests/test_exapp_surface.py vorhanden, Commit 0aed7906 vorhanden, CI-Kopf grün.
