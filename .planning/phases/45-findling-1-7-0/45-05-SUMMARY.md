---
phase: 45-findling-1-7-0
plan: 05
subsystem: php-companion (Admin-Seite Regelblock, Kataloge, Sprachtabellen)
tags: [excl-04, admin-page, l10n, zh_TW]
requires: [45-02, 45-03, 45-04]
provides:
  - "fieldset#findling-rules-mounts unter dem Schalter 'Index external storage' mit vier serverseitigen Zuständen (Liste, Hauptschalter aus, leer, files_external aus)"
  - "Dritte Zeile der Inline-Bestätigung #findling-rules-confirm-mounts ohne Zahl, Einzahl/Mehrzahl, am %s geschnitten"
  - "POST /admin/rules sendet excludedExternalMounts als letzten Schlüssel (nicht gesetzte IDs; ohne gerenderte Liste die in Kraft stehende Liste)"
  - "Neun Sätze in 18 Katalogen und 6 Sprachtabellen"
affects: [45-06, 45-10]
tech-stack:
  added: []
  patterns: ["Mount-ID nur aus data-mount-id, Einhängepunkt nur per textContent", "inForceMounts als Stand in Kraft neben inForcePrefixes/inForcePatterns"]
key-files:
  created: []
  modified:
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/l10n/*.js, php/l10n/*.json (18 Dateien)
    - docs/l10n-french.md, -spanish.md, -italian.md, -dutch.md, -portuguese.md, -chinese.md
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Typnamen unübersetzt (Fachbegriffe): die Anzeigenamen aus ExternalMountService::BACKEND_NAMES (SMB/CIFS, SFTP, Local, ...) laufen nicht durch unsere Kataloge"
  - "Hilfesatz-Schlüssel 'Clear the tick of a storage to keep it out of the index.' statt 'Clear a box ...': POL-03 verbietet das Wort box in jedem Schlüssel von de.json (test_no_sentence_of_the_page_says_box_any_more); Übersetzungen unverändert aus der UI-SPEC"
  - "Bestätigungssätze als t() im Script (wie die Mustersätze und Zähler aus 45-04), nicht als data-Attribute"
  - "Bei ausgeschaltetem Hauptschalter keine Bestätigung (nichts Externes ist indexiert, D-45-04); 'Keep files indexed' und Escape setzen genau die neu geleerten Haken zurück"
  - "'ID %s' gleich dem Schlüssel in allen neun Sprachen, auch zh_TW (keine Klammern, also kein Vollbreiten-Unterschied); Ausnahmeliste zh_TW in docs/l10n-chinese.md auf neun Schlüssel nachgezogen"
  - "Schlüsselzahl de.json 371 -> 380; Baumhash PHP 136/ee8088b3"
metrics:
  duration: "ca. 35 min laut Systemzeit (02:55 bis 03:30 UTC), davon ca. 15 min Docker (zweimal PHPUnit, zweimal php_gates_docker.sh all) und ca. 4 min PHP-lesende pytest-Läufe"
  completed: 2026-11-22
---

# Phase 45 Plan 05: Speicherliste unter dem Hauptschalter (EXCL-04) Summary

Admins sehen unter "Index external storage" jeden von einem Admin angelegten externen Speicher mit Einhängepunkt und Typ als eigenen Haken; die Seite sperrt die Liste mit dem Hauptschalter, bestätigt einen neuen Ausschluss inline mit dem Einhängepunkt und sendet die nicht gesetzten IDs, alles in 9 Sprachen in einem Commit.

## Commit

| Task | Name | Commit |
|------|------|--------|
| 1 bis 3 | Template, Script, Stil, Gates, alle Kataloge und Tabellen (Commit-Schnitt des Plans: ein Commit) | ae57d083 |

Task 1 und 2 haben ihre Teil-Gates lokal geprüft und nicht committet.

## Seite (Task 1)

- Template: Variablen `$externalMountsEnabled`, `$externalMounts`, `$excludedExternalMounts` defensiv aus `$_['externalMounts']` und `$rules` (is_array/is_int/is_string/bool). Zwischen `#findling-rules-external-help` und `#findling-rules-effect`: ohne files_external nur `#findling-rules-mounts-disabled`; sonst `fieldset#findling-rules-mounts` (`disabled`, wenn Hauptschalter aus) mit `legend.findling-rules__label`, `#findling-rules-mounts-help` / `#findling-rules-mounts-off` (je per hidden getauscht), `#findling-rules-mounts-empty` nur bei leerer Liste, `ul#findling-rules-mounts-list` (hidden bei leerer Liste) mit `li.findling-rules__row.findling-rules__mount`, Checkbox `data-mount-id` (ID als `(string)(int)`, checked = nicht ausgeschlossen), Label mit `span.findling-path` und `span.findling-rules__mount-type` (+ `ID %s` bei duplicate), `#findling-rules-mounts-again` nur bei vorhandenen Speichern. Bestätigung: `#findling-rules-confirm-mounts` mit `-before`, `code#...-value`, `-after` nach der Musterzeile. Alles über `p()`, kein `style=`, kein Inline-Skript.
- Script: `mountBoxes()`, `mountIdOf()` (nur `getAttribute('data-mount-id')`, nur ganze Zahlen), `excludedMountsOf()` (aufsteigend), `setMountBoxes()`, `mountPointOf()` (textContent des Labels), `newMountsOf()` (leer bei Hauptschalter aus), `refreshMountLock()` am Change des Hauptschalters (fieldset.disabled, Hilfesatz/Aus-Satz). `inForceMounts` aus den gerenderten Haken bzw. aus `bootstrap.rules.excludedExternalMounts`, nach dem Speichern aus `rules.excludedExternalMounts` (Haken folgen). `saveRules()`: `const mounts = mountsListed() ? excludedMountsOf() : inForceMounts.slice()` (T-45-21), Auslöser um neu ausgeschlossene IDs erweitert, `excludedExternalMounts` letzter Schlüssel. `pendingMounts` hält die IDs der offenen Bestätigung; `dismissConfirmation()` setzt genau diese Haken zurück (ohne Change-Event). Kein innerHTML.
- CSS: `.findling-rules__mounts` (border 0, Einzug `calc(var(--default-grid-baseline) * 4)`, keine Fläche), Hover `--color-background-hover`, Label flex/wrap/gap 2 Einheiten/`min-height: var(--default-clickable-area)`, Einhängepunkt `overflow-wrap: anywhere`, Typ `--font-size-small` in `--color-text-maxcontrast`, unter 640 px Typ auf eigener Zeile, `@media (pointer: coarse)` 44 px. Diff-Grep auf Farbliterale leer, kein `outline: none`.

## Gates

- `test_the_script_sends_the_pattern_list_and_cuts_the_confirmation_around_it`: Schlüsselreihenfolge mit `excludedExternalMounts` am Ende.
- Neu `test_the_script_reads_a_mount_only_out_of_its_row_and_writes_it_as_text` mit `scan_mount_script()` und drei handgebauten Fehl-Samples (B8): Label per innerHTML, ID aus dataset, leere Liste statt in Kraft stehender.
- Neu `test_the_template_renders_every_state_of_the_mount_list` mit `scan_mount_template()` und drei Fehl-Samples: fieldset ohne Sperre, Einhängepunkt ohne eigene Spanne, Liste unter der Effektzeile.
- Anti-Vakuum-Liste des Regelblock-Gates um die neun Sätze ergänzt; `VALUES_THAT_MAY_EQUAL_THEIR_KEY` um `ID %s` für de (de_DE gebunden), es, it, nl, pt_PT, pt_BR, fr und zh_TW; Schlüsselzahl 380 mit Absatz im Docstring.
- Baumhash PHP 136/ee8088b3: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) gleich; Positivkontrolle über git archive 6cea90e4 = 47251647 mit beiden Wegen.

Lokal grün vor dem Commit: PHPUnit voll 1277 Tests (zweimal, zuletzt nach dem cs-fixer-Nachtrag); `php_gates_docker.sh all` Exit 0 (Psalm-Taint 33/34/35 je 0, php-cs 0 Verstöße, zizmor, actionlint); `test_admin_ui_contract.py` (221), `test_measurement_scripts.py`, `test_admin_locale.py`, `test_public_artifacts.py` zusammen 854 passed; die übrigen PHP/l10n-lesenden Dateien (migration_path, phase33/34/40/41_audit, probe_run, store_metadata, unified_search_plugin, workflow_tag_triggers, changelog_translations) 466 passed, 113 skipped; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture; `node --check php/js/admin.js`.

## Übersetzungen

DE und FR wortgleich aus der UI-SPEC. Übrige Sprachen nach den Glossaren der docs/l10n-*.md: es "almacenamiento externo", usted ("Desmarque"), "pasada de comparación"; it "archiviazione esterna", Infinitiv, "passata di confronto"; nl "externe opslag" (Mehrzahl "opslaglocaties"), Infinitiv, "vergelijkingsdoorloop"; pt_BR "usuários", "arquivos", "salvas", "execução de comparação"; pt_PT "utilizadores", "ficheiros", "guardadas", "passagem de comparação", "Retirar"; zh_TW 外部儲存空間, 儲存空間, 管理員, 使用者, 取消勾選, 下一輪例行比對作業, 「」 um den Schalternamen, Vollbreiten-Zeichensetzung, Halbbreiten-Leerzeichen um `%s` und `ID`. Platzhalter-Parität per Gate, keine U+2013/U+2014 in neuen Werten. Bezug "es"/"son" auf den Schalter in es/fr/it/pt jeweils am Satzende ("en cuanto se active", "dès son activation", "appena viene riattivato", "assim que (ele) for ativado").

Umlaut-Audit der neuen de/de_DE-Werte (Vorfilter `(ae|oe|ue)[a-z]|ss[^a-z]`): zwei Treffer, beide "Ausschluss" (kurzer Vokal, ss korrekt, kein ß). Echte Umlaute in "nächsten", "regulären", "außerdem", "unverändert", "darüber". "Neue", "Nutzer" ohne Ersatzschreibung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Wort "box" im Hilfesatz-Schlüssel**
- **Found during:** Task 3 (volle Gates, `test_no_sentence_of_the_page_says_box_any_more`)
- **Issue:** POL-03 (G5 c der Phase 33) verbietet `\bbox\b` in jedem Schlüssel von de.json; der UI-SPEC-Satz "Clear a box to keep that storage out of the index." verstößt.
- **Fix:** Schlüssel auf "Clear the tick of a storage to keep it out of the index." (Wortlaut im Bestand: "clear the tick"), in Template, Gate, 18 Katalogen und 6 Tabellen. Die Übersetzungen sagten schon "Haken entfernen"/"Décocher" usw. und bleiben.
- **Commit:** ae57d083

**2. [Rule 3 - Blocking] php-cs-fixer: Einrückung eines `?>`**
- Schließendes `?>` nach dem neuen Kommentarblock stand eingerückt; auf Spalte 0 gesetzt wie im Bestand, Gates erneut gelaufen.

**3. [Rule 2] Bestätigung nur bei eingeschaltetem Hauptschalter, Escape wie "Keep files indexed"**
- UI-SPEC verlangt die Bestätigung nur bei eingeschaltetem Hauptschalter; `newMountsOf()` liefert dann leer. Escape ruft dieselbe `dismissConfirmation()` und setzt die Haken ebenso zurück.

**4. [Rule 2] Ausnahmeliste zh_TW in docs/l10n-chinese.md**
- Der Gate-Eintrag `ID %s` für zh_TW ist in der Doku-Liste der G2-Ausnahmen nachgetragen ("nine keys"), damit Doku und Testkonstante übereinstimmen.

## Hinweise

- `docs/l10n-chinese.md` Zeile 128 (U+2014 aus PR #56 als Beschreibung der verbotenen Typografie) lässt die Plan-Verifikation `! grep ... docs/l10n-*.md` anschlagen; bekannte Ausnahme, nicht geändert (Doku-Runde 45-07). Alle übrigen geprüften Dateien frei.
- Zählungen in `docs/l10n-chinese.md` (366 Schlüssel, Satzzeichen) bleiben datierter Stand vom 15.11.; Nachzählen in der Doku-Runde.
- Bei zwei Speichern mit gleichem Einhängepunkt nennt die Bestätigung den Einhängepunkt zweimal (ohne ID); die Liste selbst unterscheidet per "ID %s". Kandidat für die Abnahme in 45-10.
- Playwright (drei Breiten hell/dunkel, vier Zustände, Bestätigung, zh_TW) und impeccable folgen in 45-10; Probe mit Markup im Einhängepunkt (T-45-19) ebenfalls 45-10.
- Kein Push, keine Außenwirkung in diesem Plan.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: keine neue Route, Template-Parameter aus 45-03. T-45-19 (p() im Template, textContent im Script, Gate mit Fehl-Sample), T-45-20 (Inline-Bestätigung mit Einhängepunkt, Fokus auf "Keep files indexed", Haken zurück), T-45-21 (inForceMounts ohne gerenderte Liste) umgesetzt; T-45-22 accept wie geplant.

## Self-Check: PASSED

- ae57d083 vorhanden, Autor street1983nk <k.cherif@outlook.de>, keine Session-Zeile, kein Co-Authored-By; kein offener Diff in php/, docs/, backend/tests/.
- Alle 18 Kataloge enthalten "External storage to index" und "Excluding the external storages %s".
