---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 06
subsystem: admin-ui, status
tags: [pol-01, limits, deploy-options, admin-page, b3, docs, phpunit, tdd]
requires:
  - "33-03: StatusResponse.maxCells und StatusResponse.extractAddressSpaceBytes in beiden Antwortformen"
  - "33-01: Wortlaut Abschnitt E (abgenommen)"
provides:
  - "AdminViewService::backend() mit maxCells und extractAddressSpaceBytes als optionalCounter (null bei Container 1.4.x)"
  - "AdminViewService::limits(): Ansicht limits mit file, address_space, cells, pages (Wert, Option, sichtbar, Quelle, Profil)"
  - "Admin-Seite: Block Limits per file im Regelblock, nur lesend, Änderungshinweis mit Tag-Link"
  - "docs/admin-page.md: Abschnitt Grenzen je Datei ändern mit festem Anker limits-per-file"
affects: [33-07, 33-08, 33-10, 33-11, 36]
tech-stack:
  added: []
  patterns:
    - "Optionsname im code-Element aus einer Template-Map (D-27-14), Satz am Marker U+E000 geschnitten, Map per Vertragstest gleich LIMIT_VARIABLES"
    - "Versionierte Doku-URL an genau einer Stelle des Templates ($limitsDocsUrl), Anker lokal per Vertragstest geprüft"
key-files:
  created: []
  modified:
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/SettingsService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/tests/Unit/AdminViewServiceTest.php
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - docs/admin-page.md
decisions:
  - "33-06: Größengrenze im Block ist die Decke des Containers (SettingsService::containerCap()), nicht der Wert des Feldes; die Zeile bleibt auch bei stillem Container sichtbar"
  - "33-06: OCR-Deckel aus profile.values.ocrMaxPages mit Quelle; Quelle env zeigt FINDLING_OCR_MAX_PAGES, Quelle profile den Satz mit dem Profilnamen in Kraft (Wortlaut E), ohne bekannte Quelle oder Profil bleibt die Zeile verborgen"
  - "33-06: Optionsnamen kommen auf der Seite aus der Template-Map $limitVariables (Gate D-27-14), die Ansicht trägt sie zusätzlich laut Plan; ein Vertragstest hält beide gleich"
  - "33-06: Die Grenzzeilen folgen jedem Poll (kein Formular), view.rules weiterhin nicht"
  - "33-06: Tag v1.5.0 steht nur in $limitsDocsUrl in php/templates/admin.php; REL-05 hebt ihn dort beim nächsten Release"
requirements-completed: []
metrics:
  duration: "ca. 2 h 30 min inkl. zweier Volltestläufe (je ca. 17 min), Sichtprobe und ca. 35 min CI"
  completed: 2026-10-14
  tasks: 2
  files: 9
---

# Phase 33 Plan 06: Grenzen je Datei auf der Admin-Seite Summary

Der Regelblock zeigt unter "Largest file to read" den Block "Limits per file": größte Datei (Decke des Containers), Speicher je Dokument, Zellen je Tabellendatei und Seiten je gescanntem Dokument, jeweils mit der Deploy-Option als code-Element, nur lesend. Der falsche AppAPI-Satz (Befund B3) ist ersetzt; der Änderungshinweis nennt `occ app_api:app:unregister findling_backend` (ohne `--rm-data`) und verlinkt die versionierte Tag-URL auf den neuen Doku-Abschnitt.

POL-01 bleibt laut Plan offen bis 33-11 (Übersetzung in 33-07, Abnahme in 33-10).

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Grenzwerte aus dem Status lesen und als Ansicht liefern | 72d1c032 | AdminViewService.php, AdminViewServiceTest.php, test_admin_ui_contract.py |
| 2 | Grenzblock, Änderungshinweis, B3 ersetzt, Doku, Hash, CI | 72d1c032 | admin.php, admin.js, admin.css, SettingsService.php, admin-page.md, test_admin_ui_contract.py, test_measurement_scripts.py |

Task 1 und 2 laufen laut Plan in einem Commit.

## Umsetzung

- `backend()`: `'maxCells' => $this->optionalCounter($answer, 'maxCells'),` und `'extractAddressSpaceBytes' => $this->optionalCounter($answer, 'extractAddressSpaceBytes'),` (`grep -c` = 2). Container ohne die Felder ergibt null, nie 0.
- `limits()` (statisch, öffentlich): `file` aus `containerCap()` (immer sichtbar), `address_space` und `cells` aus den optionalen Zählern, `pages` aus `profile.values.ocrMaxPages` samt `sources.ocrMaxPages` (nur `env` oder `profile`) und dem Profil in Kraft. Kein neuer Endpunkt, kein Schreibweg. Docblock von `rules()` und `SettingsService::KEY_CONTAINER_CAP` sagen nicht mehr "AppAPI app settings".
- Template: Zeilen im Stil der env-Zeilen, Satz mit Marker U+E000 geschnitten, Optionsname aus `$limitVariables`, Größen über `$size`, Zahlen über `$count`, verborgen ohne Wert; zweite Form der Seitenzeile für Quelle Profil. Änderungshinweis mit code-Element für den Befehl und `<a href=... target="_blank" rel="noreferrer noopener">` "Steps in the documentation". Der B3-Satz ist auf den neuen Schlüssel aus E gewechselt (Schlüsselzahl gleich).
- Skript: `limitsView(view.limits)` in `render()` nach `profileView`, schreibt die zwei Textspannen je Zeile über `text()` (textContent) und schaltet `hidden`; die Funktionen stehen hinter `render()`, außerhalb des Profilblock-Schnitts.
- CSS: `.findling-limits`, `.findling-limits__list` (Form der env-Zeilen in normaler Schriftgröße), Link unterstrichen.
- Doku: `<a id="limits-per-file"></a>` direkt vor "## Grenzen je Datei ändern": Tabelle der vier Grenzen mit Option, Standard aus config.py und Wirkung, Änderungsweg (unregister ohne `--rm-data`, erneut bereitstellen mit `--env` bzw. Deploy-Optionen der Oberfläche, Daten und Index bleiben), Verweis auf docs/performance.md, Hinweis "nur lesend, Editieren außerhalb". Der alte Zwei-Schritte-Weg im Abschnitt "Der Größen-Cap" verweist jetzt auf diesen Abschnitt. Der Weg ist gegen AppAPI der Dev-Instanz belegt: `Register.php:62` Option `--env` (ENV_NAME=ENV_VALUE), `Unregister.php:54-55` Daten bleiben standardmäßig, `--rm-data` entfernt sie.

## Belege

**PHPUnit (nur CI):** Vorher 777 Tests (Lauf 38512158095), nachher **789 Tests, 2947 Assertions** (Lauf 38520405650). +12: zwei neue Felder durchgereicht, Container ohne Felder ergibt null (auch ohne Antwort), sechs Fremdwerte (`"200000"`, `-1`, `1.5`, `true`, Markup, Liste) ergeben null, vier Grenzen aus den bestehenden Lesestellen, Container 1.4 verbirgt die zwei neuen Zeilen und behält die Decke, Seitendeckel aus der Umgebung ohne Profil, fremde Quelle, unbekanntes Profil oder Zeichenkette verbergen die Seitenzeile. `backend()` wird per Reflection auf einer Instanz ohne Konstruktor gefragt (liest nur die Antwort). Rot vor der Umsetzung nur als Textprüfung belegbar: `backend()` kannte die Schlüssel nicht, `limits()` gab es nicht.

**Vertragsfälle, neu in test_admin_ui_contract.py:**

- Task 1: `test_every_new_status_key_has_exactly_one_line_in_the_service` um `maxCells` und `extractAddressSpaceBytes` erweitert, mit Formprüfung `optionalCounter`.
- (a) `test_the_rules_block_shows_the_four_limits_read_only` (vier Zeilen mit code-Element, Profilform, Wortlaut E zeichengleich, kein `input`/`select`/`textarea`/`button` im Block, unter dem Feld, Template-Map gleich `LIMIT_VARIABLES`)
- (b) `test_the_wrong_appapi_sentence_is_gone_from_both_halves`
- (c) `test_the_change_hint_links_the_anchor_of_the_documentation` mit `scan_limits_link()` (genau ein Link, Tag-URL, ASCII, Anker genau einmal in der Doku) und Selbsttest `test_a_link_with_another_anchor_or_without_a_tag_is_one_finding` (anderer Anker ein Befund, `blob/main` ein Befund, Doku ohne Anker ein Befund)
- (d) `test_the_script_writes_the_limits_as_text_only`

RED ohne `git stash`: Template, Skript, AdminViewService und Doku per `git show HEAD:` eingesetzt: Statusschlüssel, (a), (b), (d) **4 rot**, Selbsttest grün; (c) mit neuem Template und alter Doku rot mit "the anchor <a id="limits-per-file"></a> is not in the documentation exactly once". Eigene Kopien zurück, `cmp` gleich.

**Zwei Bestandsgates schlugen im ersten Volltestlauf an** (2 failed, 5675 passed): `test_the_env_lines_name_only_fixed_variables` (D-27-14: kein `['variable']` im Template) und `test_every_sentence_of_the_profile_block_is_in_every_catalogue` (die Grenzfunktionen standen im Skript vor `render()`, also im Schnitt des Profilblocks). Behoben durch die Template-Map `$limitVariables` und das Verschieben der zwei Funktionen hinter `render()`; die Kataloge bleiben Sache von 33-07.

**Baumhash:** `PHP_TREE_HASH_TODAY` von `48aa61a8...` auf `2dbfe17d033d41dc4b7cabd818cde4e25691c8c9f444fc1c8e8073e535518f39`, `PHP_FILES_TODAY` bleibt 103, Journalabsatz "Moved on 2026-10-14 by Plan 33-06". Gegenprobe unabhängig vom Rezeptskript: sha256 über die Index-Blobs (`git cat-file blob :<pfad>`, Shell-`sha256sum`, Sortierung `LC_ALL=C`) liefert denselben Wert.

**Gates lokal (backend/, PYTHONUTF8=1):** pytest **5677 passed, 159 skipped** (17:09 min, zweiter Volltestlauf nach den Korrekturen); ruff check grün; ruff format --check 222 Dateien; pyright 0 errors (latest); vulture leer; reuse lint 2725/2725; `node --check php/js/admin.js` grün; PHPL-Block vor und nach dem Commit grün. Keine Halbgeviert- oder Geviertstriche im Diff, keine Umlaute in Code.

## Sichtprobe 8090 (Playwright, admin)

Statusantwort des Host-Backends: `maxFileBytes` 52428800, `maxCells` 200000, `extractAddressSpaceBytes` 536870912, `ocrMaxPages` 30 mit Quelle `profile`, Profil in Kraft `economy`.

Bildschirmfotos (`C:/Users/Student/AppData/Local/Temp/claude/C--Users-Student/f6488641-8ddf-4bad-8748-b99f3aecda70/scratchpad/sicht3306/`):

- `1-regelblock.png`: Regelblock, der Grenzblock unter dem Feld "Größte zu lesende Datei" (Feld unverändert, `max` 50), Hinweissatz "This ceiling is a deploy option, see "Limits per file"."
- `2-grenzblock.png`: "Largest file the backend reads: 50,0 MB (FINDLING_MAX_FILE_BYTES)", "Memory one document may use while it is read: 512,0 MB (FINDLING_EXTRACT_ADDRESS_SPACE_BYTES)", "Cells read per spreadsheet file: 200.000 (FINDLING_MAX_CELLS)", "Pages read per scanned document: 30, from the profile Sparsam"; Änderungshinweis mit `occ app_api:app:unregister findling_backend` als code; Link `href` genau `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/admin-page.md#limits-per-file`, `target="_blank"`, `rel="noreferrer noopener"`. Kein Eingabeelement im Block (0). Nach dem ersten Poll sind die Zeilen textgleich mit der Erstdarstellung; keine Konsolenfehler.
- `3-doku-anker-main.png`: `blob/main/docs/admin-page.md#limits-per-file` nach dem Push, HTTP 200, Anker `user-content-limits-per-file` genau einmal, Überschrift "Grenzen je Datei ändern". **Tag-Link geht erst mit v1.5.0 auf** (heute HTTP 404, geprüft wird nur die URL-Form).

Die Größen stehen nach der Konvention der Seite (`$size`, Einheit MB mit einer Nachkommastelle, Basis 1024), also "512,0 MB" statt "512 MiB". Die neuen Sätze erscheinen auf der deutschen Seite noch englisch; die Übersetzung ist Sache von 33-07.

## CI (72d1c032)

Alle mit `gh run watch <id> --exit-status` bis zum Ende beobachtet, alle grün:

- PHP and store metadata gates 38520405650 (PHPUnit 789)
- Python gates 38520405690
- Security scans 38520405602
- OpenSSF Scorecard 38520405605
- Resilience 38520405571
- Multi-arch image 38520405681
- Integration 38520405678
- HaRP deploy 38520405885 (zweiter Watch-Aufruf, der erste lief in die lokale Zeitgrenze)

Erste Liste mit 7 Läufen, zweiter Aufruf mit 8 (PHP gates spät gestartet).

## Hinweis für Phase 36 (REL-05)

Die Tag-Version des Doku-Links steht an genau einer Stelle: `$limitsDocsUrl` in `php/templates/admin.php`. Beim Release nach 1.5.0 dort heben; der Vertragstest `LIMITS_DOCS_URL` in `test_admin_ui_contract.py` zieht mit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 1 - Bug] Falsche Handlungsanweisung auch in Kommentaren und Doku**
- **Gefunden in:** Task 2
- **Problem:** Neben `admin.php:1291` stand der B3-Weg ("AppAPI app settings, restarts the container") auch im Docblock von `AdminViewService::rules()`, in `SettingsService::KEY_CONTAINER_CAP` und in docs/admin-page.md (Abschnitt "Der Größen-Cap", zwei Schritte).
- **Fix:** Alle drei auf den Weg über unregister ohne `--rm-data` und Deploy mit neuem Wert umgestellt, die Doku verweist auf den neuen Abschnitt.
- **Dateien:** php/lib/Service/AdminViewService.php, php/lib/Service/SettingsService.php, docs/admin-page.md
- **Commit:** 72d1c032

**2. [Regel 3 - Blockierend] Zwei Bestandsgates**
- **Gefunden in:** Task 2, erster Volltestlauf
- **Problem:** Gate D-27-14 verbietet `['variable']` im Template; der Profilblock-Schnitt des Skripts reicht bis `function render`.
- **Fix:** Optionsnamen aus der Template-Map `$limitVariables` (per Test gleich `LIMIT_VARIABLES`), Grenzfunktionen hinter `render()` verschoben.
- **Commit:** 72d1c032

### Weitere Abweichungen

1. **SettingsService.php und admin.css geändert** (nicht in files_modified): Kommentar zu B3 und Stil des Blocks.
2. **Seitenzeile mit Quelle Profil ohne Optionsnamen:** Der Wortlaut E (abgenommen) sieht für die Quelle Profil "..., from the profile %2$s" vor; die must_haves-Formulierung "each with its deploy option name" gilt deshalb für die Umgebungsform. Die Option `FINDLING_OCR_MAX_PAGES` steht im Doku-Abschnitt.
3. **Ansicht trägt den Optionsnamen, die Seite nutzt ihn nicht:** Der Plan verlangt den Namen in der Ansicht; Gate D-27-14 verlangt, dass die Seite ihn aus der eigenen Map nimmt. Beides gilt, ein Vertragstest hält Map und Konstante gleich.
4. **Grenzzeilen folgen jedem Poll:** Der Plan sagt "wo der Poll die Regelansicht nachzieht"; der Poll zieht `view.rules` bewusst nicht nach (Formular). Da der Grenzblock kein Formular ist, zieht `render()` ihn aus `view.limits` nach.
5. **TDD-Reihenfolge:** Vertragsfälle nach der Umsetzung geschrieben; Rot per `git show HEAD:`-Gegenprobe belegt (nicht per `git stash`), PHPUnit-Rot nur als Textprüfung (CI-only).
6. **Größenangabe "512,0 MB" statt "512 MiB":** Konvention der Seite (`$size`, Wortlaut E "Größen über $size").

## Known Stubs

Keine. Die neuen Sätze sind noch nicht in den Katalogen; laut Plan Sache von 33-07, auf der Seite als englischer Text sichtbar.

## Threat Flags

Keine neue Fläche über das Threat Register hinaus. T-33-21: Statusfelder nur über `optionalCounter` bzw. `nonNegativeInt` (PHPUnit mit sechs Fremdwerten), Ausgabe nur über `p()` und `textContent`, Quelle und Profil gegen geschlossene Mengen. T-33-22: B3 ersetzt, Vertragsfall gegen den alten Wortlaut, Ankerprüfung des Links. Der neue externe Link öffnet mit `rel="noreferrer noopener"`.

## Self-Check: PASSED

- FOUND: php/templates/admin.php (findling-limits, blob/v1.5.0/docs/admin-page.md#limits-per-file genau 1x)
- FOUND: php/lib/Service/AdminViewService.php (optionalCounter für maxCells und extractAddressSpaceBytes, 2 Treffer)
- FOUND: docs/admin-page.md (FINDLING_MAX_CELLS, Anker genau 1x)
- FOUND: 72d1c032
