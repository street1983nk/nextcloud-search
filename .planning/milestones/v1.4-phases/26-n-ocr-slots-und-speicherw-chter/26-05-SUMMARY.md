---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 05
subsystem: php-admin-page
tags: [admin-ui, l10n, memory-guard, closed-sets]
requires: []
provides:
  - "Vertrag des /status-Felds guard (chosen, effective, cap, cause, since, token, slotsTarget, slotsInForce, throttled) für Plan 26-08"
  - "AdminViewService: guardField, profileName, guardCause, hexToken, guardCounter; backend()-Felder guardChosen/guardEffective/guardCause/guardToken/slotsTarget/slotsInForce/slotsThrottled"
  - "admin.php: Zeilen findling-guard, findling-guard-way-back, findling-slots"
affects: [26-08, 26-04, 26-14, 27]
tech-stack:
  added: []
  patterns: ["geschlossene Mengen für Container-Wörter (T-25-14)", "Satz mit Marker übersetzen und am Marker schneiden, Befehl in eigenem code-Element"]
key-files:
  created: []
  modified:
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - php/templates/admin.php
    - php/l10n/*.js, php/l10n/*.json (16 Dateien)
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "Ungültige Slot-Zähler ergeben null (nicht 0), damit 'Container sagt nichts' von 'null Slots' getrennt bleibt"
  - "Token-Regex mit Modifier D, sonst akzeptiert $ ein abschließendes Newline im kopierten occ-Befehl"
  - "Wächterzeile erscheint nur, wenn Ursache, gewählt und wirksam alle aus der geschlossenen Menge kommen"
  - "Rückweg-Satz wird mit Marker U+E000 übersetzt und daran geschnitten; der occ-Befehl steht nie in einem Katalogtext"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-28
  tasks: 2
  files: 20
---

# Phase 26 Plan 05: Wächter- und Drosselanzeige der Adminseite Summary

Adminseite nennt nach einer Wächter-Absenkung gewählt, wirksam und Ursache, den Rückweg als `occ config:app:set findling profile_confirmed --value=<token>` und die OCR-Slot-Drosselung, alle Wörter aus PHP-seitigen geschlossenen Mengen, in acht Sprachen.

## Tasks

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | Wächterfelder in AdminViewService über geschlossene Mengen | 022f6117 | AdminViewService.php, AdminViewServiceTest.php |
| 2 | Wächter-, Rückweg- und Drosselzeile im Template, acht Kataloge | cc104ffd | admin.php, 16 Katalogdateien, test_admin_ui_contract.py |

## Vertrag für Plan 26-08

`/status` trägt ein Objekt `guard`: `chosen` (Profilname oder null), `effective` (Profilname), `cap` (Profilname oder null), `cause` ("", "memory_max_repeated", "oom_kill", "unclean_end"), `since` (int oder null), `token` (32 Kleinbuchstaben-Hex oder ""), `slotsTarget` (int), `slotsInForce` (int), `throttled` (bool). Ohne Objekt bleiben alle drei Zeilen verborgen. `cap` und `since` liest die Seite in dieser Phase nicht.

## Verifikation

- Python-Suite (ohne PHP-Pin-Test): 3711 passed, 16 skipped
- tests/test_admin_ui_contract.py + tests/test_public_artifacts.py: 111 passed
- ruff check/format auf der Testdatei grün; keine Em-/En-Dashes unter php/
- PHPUnit: läuft nur in CI nach Push (php.yml), Plan 26-14 sammelt das Ergebnis ein

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Katalog-Gate mit fester Schlüsselzahl und Gleichwort-Ausnahmen**
- **Gefunden in:** Task 2
- **Problem:** `test_the_german_catalogue_covers_both_german_language_codes` prüft `len == 207`; `test_every_catalogue_value_carries_a_wording_of_its_language` meldete "Standard" (de, de_DE, fr, it) und "Performance" (fr) als unübersetzt.
- **Fix:** Zahl auf 216 (neun neue Schlüssel), Ausnahmen mit Begründung in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` für de, it, fr.
- **Datei:** backend/tests/test_admin_ui_contract.py (nicht in files_modified des Plans)
- **Commit:** cc104ffd

**2. [Rule 1 - Bug] Token-Regex ohne Modifier D**
- **Gefunden in:** Task 1 (eigener Testfall "token mit Newline")
- **Problem:** `/^[0-9a-f]{32}$/` lässt ein abschließendes `\n` durch, das den kopierten occ-Befehl beenden würde.
- **Fix:** `/^[0-9a-f]{32}$/D`; Akzeptanz-Grep trifft weiterhin genau einmal.
- **Commit:** 022f6117

**3. [Rule 2 - Kritisch] Quelltext-Gate für die Wächterfelder**
- PHPUnit läuft lokal nicht; neuer Python-Test `test_the_guard_lines_are_built_out_of_closed_sets` hält Konstanten, backend()-Zeilen, Template-IDs, code-Element und Katalogschlüssel lokal fest.
- **Commit:** cc104ffd

## Hinweise

- `php/js/admin.js` (Poll-Neuschreiben) kennt die drei neuen Zeilen nicht; sie zeigen den Stand des Seitenaufrufs. Der Wächterzustand ändert sich selten, und admin.js lag nicht im Plan-Umfang. Kandidat für Phase 27 (Settings-UI).
- Übersetzungen außerhalb Deutsch/Englisch sind maschinell nach Hausmuster.
- PHP-Pins nicht angefasst; Plan 26-04 misst nach dem Merge der Welle 1 neu.

## Threat Flags

Keine neuen Flächen über das Threat-Register hinaus (T-26-15/16 mitigiert, T-26-17 akzeptiert).

## Self-Check: PASSED

- FOUND: php/lib/Service/AdminViewService.php, php/templates/admin.php, php/tests/Unit/AdminViewServiceTest.php
- FOUND: 022f6117, cc104ffd
