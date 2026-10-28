---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 07
subsystem: php-companion
status: abgeschlossen
tags: [STR-01, similar-documents, result-page, php]
requires:
  - 35-01 (Wortlaut abgenommen 19.10.2026, O1-O6 je a)
  - 35-06 (SearchService::similar, SimilarOutcome)
provides:
  - "PageController::similarId(): ?int, Ansichtszweig similarView(), similarUrl je Treffer, backUrl"
  - "Template-Schlüssel similarSource {fileId,title}|null, similarState ok|empty|unavailable|failed|null, backUrl"
  - "search.php: findling-hit__similar, h1-Zweig, Rückweg findling-similar__back, zwei Zustände"
affects:
  - 35-13 (Kataloge, Sprachtabellen, Rendering-Probe auf 8090)
key-files:
  modified:
    - php/lib/Controller/PageController.php
    - php/templates/search.php
    - php/css/search.css
    - php/tests/Unit/PageControllerTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Formfalscher similar-Wert (abc, 0, -3, 1e3, 20 Ziffern) wird still verworfen, normale Ergebnisseite; formgültige, aber nicht lesbare ID ergibt 'unavailable' (so auch 35-13 Probe 3/4)"
  - "Vierter Zustand 'failed' für Backend-Ausfall/Drift/kein Home: nur Bestandsbanner plus Rückweg, kein Leerzustand"
  - "Kanarienzeile (fileId 0) bekommt keinen Ähnlich-Link (kein Datei-Ziel)"
  - "Ansicht setzt degraded=false und das Template schließt den Hinweisbanner aus (O4 a)"
metrics:
  completed: 2026-10-19
  tasks: 2
  files: 5
---

# Phase 35 Plan 07: Ähnlich-Ansicht auf der Ergebnisseite Summary

Jeder Treffer trägt einen zweiten Link "Similar documents" (aria-Label "Similar documents to %s"); `?similar=<id>` rendert dieselbe Seite serverseitig als Ähnlich-Ansicht mit genau einem h1, Rückweg auf die exakte Ausgangsliste, bis zu zehn Nachbarn ohne Auszug, Filterzeile, Pager oder weiteren Link.

## Commits

| Schritt | Commit | Inhalt |
|---|---|---|
| Task 1 + 2 (gemeinsam, laut Plan) | e6c6b975 | Controller, Template, CSS, 6 PHPUnit-Fälle, Baumhash |

## Pre-flight

`grep -E "^Owner-Abnahme: ..." 35-WORTLAUT.md` vor der ersten Codeänderung:
`187:Owner-Abnahme: 19.10.2026, "Abgenommen (alle Empfehlungen)", alle Sätze wie vorgelegt, O1-O6 je Option a`

## Umsetzung

- **Controller:** `similarId()` nach `pageNumber()` (`^[1-9][0-9]{0,18}$`, sonst null); Zweig in `index()` vor `outcome()`, ruft `SearchService::similar($user, $id, $this->caps())`, nie `run()`. Ansicht: Chips/Sortierung leer, Reset/Pager null, `hits` aus `similarRows()` (segments leer, modified leer, kein similarUrl), `backUrl = pageUrl(...)` der aktuellen Adresse. `rows()` setzt je Zeile `similarUrl` über `linkToRoute('findling.page.index', filterArguments + page, cursors, fp, similar)`. Keine neue Route.
- **Template:** Kopf-Variablen im Bestandsmuster; dritter Zweig im einen h1 ("Similar to: %s" bzw. "Similar documents" ohne Quelle); Rückweg "Back to the results" direkt unter dem h1 in jedem Zustand; Filterblock und Pager mit `$similarState === null` ausgeschlossen; Listen-aria-Label "Similar documents"; zweites `<a class="findling-hit__similar">` nach dem `</a>` des Zeilen-Links; beide Zustände als Zweig im Block `findling-empty`, `$showEmpty` liest weiterhin `$hasError`, `$hasHint`, `$hasQuery`.
- **Zeilenfolge (grep -n):** `<li class="findling-hit"` 500, Zeilen-Link 505 bis `</a>` 532, `findling-hit__similar` 541, `</li>` 544. `grep -c "<h1"` = 1.
- **CSS:** `.findling-hit__similar` (Satz-Link unter dem Grid, eingerückt auf die Pfadspalte, mobil linksbündig), `:focus-visible`-Ring in Textfarbe, Hover in der Gruppe, `.findling-similar__back` wie der Reset-Link, beide 44px unter `pointer: coarse`.
- **Schlüssel:** die sieben englischen Schlüssel aus 35-WORTLAUT.md Tabelle A zeichengleich; Kataloge unangetastet (35-13).
- **Render-Probe (lokal, Stub-Harness, php:8.3-cli, danach gelöscht):** normal: 1 h1, 1 Ähnlich-Link, aria-Label escaped; ok: h1 "Similar to: Miet&lt;vertrag&gt;.pdf", Rückweg, keine Filter, Liste "Similar documents"; empty: h2 "No similar documents found"; unavailable: h1 "Similar documents", h2 "This file is not available"; failed: Fehlerbanner, kein Leerzustand.

## PHPUnit-Fälle (nur CI)

Sechs neue Fälle in PageControllerTest: formfalsche Werte (fehlt, leer, 0, -3, abc, 1e3, 00, " 7", 20 Ziffern) ohne similar-Aufruf; gültige ID ruft similar(42), nie run, Steuerelemente leer; jede Zeile trägt similarUrl mit allen Positionswerten; Rückweg = similarUrl ohne similar (Rundreise über die echte Adresse); Nachbarzeilen ohne Auszug/Datum/Link plus Zustand empty; unavailable ohne Quelle und ohne failure, failed reicht FAILURE_BACKEND_SILENT durch. Erwartete PHPUnit-Zahl nach 35-06 (831) plus 6 = 837; Nachher-Zahl offen bis Orchestrator-Push.

## Gates

- php -l: PageController.php, search.php, PageControllerTest.php ohne Fehler.
- pytest gezielt: test_admin_ui_contract, test_measurement_scripts, test_php_acl_boundary, test_php_trust_boundary: 703 grün (vor Ratsche 1 rot, nur der Baumhash).
- Baumhash: 106 Dateien, `9aa79bb73926212910b0e58d3def6eb0fef82ef650a28c3f1bf8f66df5fe853a`, unabhängig per find/sort/sed/sha256sum nachgerechnet, gleich.
- ruff check, ruff format, pyright (latest) 0 Fehler, vulture sauber, reuse lint konform (2801/2801).

## Deviations from Plan

- **Volle Python-Suite nicht gelaufen:** der Hintergrundlauf wurde vom System wegen Speichermangel gestoppt (parallele Agenten); laut Vorgabe nicht neu gestartet. Geändert wurde nur eine Python-Datei (Konstante plus Kommentar); die vier PHP-nahen Gate-Dateien liefen vollständig grün.
- **Kein Push, kein CI-Lauf** (Worktree, Orchestrator merged und pusht); Laufnummern und PHPUnit-Nachher-Zahl offen.
- **Rule 2:** Kanarienzeile (fileId <= 0) ohne Ähnlich-Link, weil `similar=0` keine Datei benennt.
- **Auslegung O4 (a) "ungültiger Wert":** formfalsche Werte gelten wie im Plan als nicht vorhanden (normale Seite, auch 35-13 Probe 4 `similar=abc`); formgültige, aber nicht bestätigte IDs ergeben den einen Zustand "This file is not available".
- `php/js/search.js` unverändert, wie vorgegeben.

## Threat Flags

Keine neuen Flächen; T-35-24 bis T-35-27 wie geplant umgesetzt (Regex-Prüfung, ein Zustand, keine Zahl, Ausgabe nur über p() und $l->t()).

## Known Stubs

Keine. Deutsche und französische Sätze fehlen bis 35-13 bewusst (Fallback auf Englisch, kein Release dazwischen).

## Self-Check: PASSED

- Dateien vorhanden: php/lib/Controller/PageController.php, php/templates/search.php, php/css/search.css.
- Commit vorhanden: e6c6b975.
