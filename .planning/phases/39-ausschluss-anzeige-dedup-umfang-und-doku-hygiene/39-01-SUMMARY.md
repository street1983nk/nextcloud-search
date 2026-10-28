---
phase: 39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene
plan: 01
subsystem: admin-page-coverage
tags: [dedup, weg-c, coverage, status-route, l10n, admin-page]
requires:
  - D-37-03 (Weg C als erster Schritt)
  - 35-DEDUP-NOTIZ (F1, F4, F6, Abschnitt 4 Weg C)
provides:
  - StorageService::countingKeyGroups / countingKey
  - ScanStatsService::totals(ids, groups) mit grouped, leftOutStorageIds, groupsApplied
  - GET /status?leaveOut= mit indexedLeftOut / embeddedLeftOut
  - coverage.deduplicated, coverage.rulesPending
  - findling-coverage-leftout-none, findling-coverage-leftout-explain, findling-coverage-rules-pending
affects:
  - 39-04 (DEDUP-02 Abschluss: Messung A6/A7, Weg A, Weg B)
  - 40 (Owner-Runde der neuen Sätze, php.yml-Lauf vor dem Audit-Gate)
tech-stack:
  added: []
  patterns:
    - "pydantic Field(exclude_if=...) für Felder, die ohne Parameter auf dem Draht fehlen"
    - "eigene mode=ro-URI-Verbindung mit ATTACH des Vektorbestands für eine Join-Zählung"
key-files:
  created:
    - backend/tests/test_status_leave_out.py
    - php/tests/Unit/ScanStatsServiceTest.php
  modified:
    - php/lib/Service/StorageService.php
    - php/lib/Service/ScanStatsService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/FileStateService.php
    - php/lib/Service/SettingsService.php
    - php/lib/Controller/SettingsController.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.json, php/l10n/*.js (16 Kataloge)
    - backend/src/findling/api/status.py
    - backend/src/findling/store/repo.py
    - docs/admin-page.md, docs/l10n-{french,spanish,italian,dutch,portuguese}.md
    - backend/tests/test_status_endpoint.py, test_admin_ui_contract.py, test_measurement_scripts.py
    - php/tests/Unit/StorageServiceTest.php, AdminViewServiceTest.php, SettingsControllerTest.php
decisions:
  - "Weg C gruppiert smb:: und sftp:: (getId() in stable34 belegt), WebDAV/ownCloud nie"
  - "Repräsentant je Gruppe: kleinste Storage-ID mit finished_at, sonst kleinste mit Zeile, sonst kleinste"
  - "Entdopplung nur, wenn indexedLeftOut UND embeddedLeftOut als nicht negative int kommen, sonst Zahl wie 1.5"
  - "embeddedLeftOut über eigene mode=ro-URI-Verbindung (ATTACH braucht URI-Verbindung), nicht über die Status-Verbindung"
  - "rules_changed_at wird gelöscht, sobald der Hinweis durch ist, damit eine Routine-Nachzählung ihn nicht zurückbringt"
metrics:
  duration: "ca. 60 min (14:27 bis 15:26)"
  completed: 2026-10-28
  tasks: 3
  commits: 7
---

# Phase 39 Plan 01: Weg C, Erklärsatz bei 0 und Hinweis nach Regeländerung Summary

Die Abdeckung der Admin-Seite zählt SMB- und SFTP-Einbindungen derselben Share mit nutzerspezifischer Anmeldung je Schlüssel einmal (Repräsentant im Nenner, Container nennt die Dokumente der übrigen über `GET /status?leaveOut=`), der falsche Mehrfachzählungs-Satz ist korrigiert, und zwei neue Zeilen erklären "Bewusst ausgelassen: 0" und die Verzögerung nach einer Regeländerung.

## DEDUP-02 Pflichtteil Weg C: geliefert

ROADMAP Phase 39 Erfolgskriterium 3, erster Teil (D-37-03). 39-04 schließt DEDUP-02 mit Messung A6/A7, Weg A und Weg B ab.

- **Schlüssel:** Storage-ID ohne Anmeldenamen, `<backend>::<host>//<rest>`; Host = Text nach dem LETZTEN `@` vor dem ersten `//`; Root steht nach Platzhalter-Ersetzung schon so in der ID (F4), ein Root mit `$user` ist also je Nutzer ein anderer Schlüssel (Positivkontrolle im Test).
- **Nie gruppiert:** md5-gekürzte IDs (über 64 Zeichen), `home::`, `local::`, `object::`, WebDAV, ownCloud und jedes andere Backend. Rückfall = 1.5.
- **totals():** eine Abfrage je Band (statt zwei), oberste Ebene byte-gleich zu 1.5, dazu `grouped`, `leftOutStorageIds`, `groupsApplied`.
- **Container:** `indexedLeftOut` (lebende indexierte Zeilen der genannten Storages, gebändert zu 500) und `embeddedLeftOut` (davon mit mindestens einer Zeile in `vec.chunks`), Obergrenze 100000, ohne Parameter fehlen beide Schlüssel ganz (`FIELDS` unverändert).
- **Seite:** `coverage.deduplicated`; `duplicates` nur noch bei `deduplicated = false`; Nenner einmal in `figures()` nach der Antwort berechnet, gilt für Abdeckung und Schätzung.

### Belegte getId()-Formate (nextcloud/server, stable34, Kopf 4ce36f88, gelesen 28.10.2026 per gh api)

| Backend | Fundstelle | Format |
|---|---|---|
| SMB | `apps/files_external/lib/Lib/Storage/SMB.php:137-142`, Root-Normalisierung `:114-116` | `'smb::' . user . '@' . host . '//' . share . '/' . root` (root mit führendem und abschließendem `/`) |
| SFTP | `apps/files_external/lib/Lib/Storage/SFTP.php:157-167`, Root `:94-98` | `'sftp::' . user . '@' . host [':' . port] . '/' . root` (root mit führendem `/`, daher `//`) |
| WebDAV (nicht gruppiert) | `lib/private/Files/Storage/DAV.php:201-203` | `'webdav::' . user . '@' . host . '/' . root`; Host kann einen Pfad tragen, Host und Root nicht sicher trennbar |
| md5-Kürzung | `lib/private/Files/Cache/Storage.php:100-103` | IDs über 64 Zeichen werden als md5 gespeichert |

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 RED | 077d63ba | Tests countingKeyGroups, ScanStatsServiceTest (neu), test_status_leave_out.py (neu), Wire-Vertrag in test_status_endpoint.py; PHP-Hash 108 Dateien |
| 1 GREEN | 1fce632f | StorageService, ScanStatsService, status.py, repo.py; PHP- und Paket-Hash |
| 2 RED | f92cc03f | AdminViewServiceTest: 7 Fälle Weg C; PHP-Hash |
| 2 GREEN | 4fc2fc18 | AdminViewService (figures, leaveOutParameters, leftOutCounts), FileStateService::countByReason mit Storage-Liste, korrigierter Satz in 16 Katalogen und 5 Tabellen, docs/admin-page.md; PHP-Hash |
| 3 RED | 96b7d6d2 | Vertragstest ANZE-01/02 (Schlüsselzahl 353), AdminViewServiceTest rulesPending, SettingsControllerTest; PHP-Hash |
| 3 GREEN | 8d6306aa | SettingsService rules_changed_at, saveRules-Stempel, rulesPending mit IJobList, Template/Skript, 2 neue Schlüssel in 16 Katalogen und 5 Tabellen, docs/admin-page.md; PHP-Hash |
| Nachzug | a619a056 | Vertragstest prüft die gestrichene Satzhälfte über ihr Ende (Akzeptanz-grep auf 0) |

## Verify-Ergebnisse (lokal, 28.10.2026)

- `uv run --no-sync pytest tests/test_admin_ui_contract.py tests/test_measurement_scripts.py tests/test_status_leave_out.py tests/test_status_endpoint.py -q`: 883 passed
- `-k tree_hash`: 4 passed; beide Bäume unabhängig mit find, sort, tr und sha256sum nachgerechnet, gleich dem Rezept 40b-baumhash.py (PHP 108 Dateien `9a6c99ed...`, Paket 80 Dateien `5f4d6d18...`)
- ruff check / ruff format --check (ganzes backend): grün; pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest): 0 errors; vulture --min-confidence 80: grün
- weitere Gates grün: test_exclusion_path_space, test_allowlist_parity, test_readonly_gate, test_store_repo, test_vector_store, test_vec_extension_probe, test_acl_prefilter, test_rates_endpoint, test_diagnose_endpoint, test_phase36_audit, test_main_lifespan, test_store_vanished
- PHP-Unit-Tests sind lokal nicht lauffähig (kein php). Pflicht vor dem Audit-Gate der Phase 40: php.yml- und python.yml-Lauf auf dem 39-01-Stand, Lauf-IDs hier nachtragen: **offen**.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ATTACH mit URI geht nicht auf der Status-Verbindung**
- **Gefunden in:** Task 1
- **Problem:** Gemessen (sqlite 3.50.4): `ATTACH 'file:...?mode=ro'` scheitert auf einer Verbindung ohne URI-Flag; ein ATTACH mit einfachem Pfad legt eine fehlende vectors.db leer an (auch unter query_only).
- **Fix:** `repo.embedded_in_storages()` öffnet eine eigene Verbindung `file:<state.db>?mode=ro` (uri=True, query_only), hängt `file:<vectors.db>?mode=ro` als `vec` an und DETACHt im finally. Test belegt: fehlende vectors.db bleibt fehlend.
- **Commit:** 1fce632f

**2. [Rule 1 - Bug] EXISTS statt COUNT(DISTINCT) über den Join**
- Gleiche Semantik, kein temporärer B-Baum für das DISTINCT (Begründung wie `_ACL_DOCUMENTS_SQL`). Commit 1fce632f.

**3. [Rule 1 - Bug] IDs über 18 Ziffern wären ein 500 gewesen**
- `int` jenseits von SQLite INTEGER wirft OverflowError. Pattern `^[0-9]{1,18}(,[0-9]{1,18})*$`, Test "a number beyond the integer range" ergibt 422. Commit 1fce632f.

**4. [Rule 1 - Bug] Abgelehnte Dateien (mime_not_allowed) der ausgelassenen Storages**
- `refusedByType` zählt über alle Storages; unter Weg C hätte es den Nenner zu stark gekürzt (Anteil über 100, "recounting"). `FileStateService::countByReason()` nimmt eine optionale Storage-Liste (`fc.storage IN`), `figures()` zieht den Anteil der ausgelassenen Storages mit ab. Datei nicht in `files_modified` des Plans. Commit 4fc2fc18.

**5. [Rule 1 - Bug] Hinweis nach Regeländerung käme bei jeder Routine-Nachzählung zurück**
- Die Regel des Plans (Stempel > 0 und Crawl-/Kehrjob in der Liste) wäre nach jeder späteren Nachzählung wieder wahr gewesen, weil der Stempel nie zurückging. `rulesPendingNow()` löscht `rules_changed_at`, sobald der Hinweis durch ist (eine Schreibung beim ersten Poll danach). Commit 8d6306aa.

**6. [Rule 1 - Bug] Zeilenschleifen enden auf jeder Nicht-Zeile**
- `while (is_array($row = fetch()))` statt `!== false` in countingKeyGroups und totals, damit ein Cursor-Double, das null liefert, nicht endlos dreht. Commit 8d6306aa.

**7. [Rule 3] pyright im RED-Commit 96b7d6d2**
- `catalogue_of()` liefert `str | list[str]`; im GREEN-Commit 8d6306aa mit `str(...)` behoben. Der RED-Commit selbst ist nicht pyright-grün.

### Kleinere Abweichungen

- `rememberRulesChange(?int $now = null)` statt `int $now`: der Controller hat keine Zeitquelle, der Wert kommt sonst aus der ITimeFactory der SettingsService.
- SFTP zusätzlich zu SMB gruppiert (Format belegt, Issue #25 wurde mit zwei sftp-Einbindungen nachgestellt).
- Die Schätzung (estimate) bekommt unter Weg C ebenfalls die entdoppelten Zähler (ein Nenner für beide, Planregel). Die verbleibende Arbeit der Kopien ist real (Weg B fehlt), die Restzeit kann während der Erstindexierung daher zu klein wirken; nach `firstIndexDone` ist der Block ohnehin aus.
- Die Kachel "Ausgeschlossen" (`overview.excluded`) bleibt ungruppiert (echte Zählung je Datei-ID wie Übersprungen und Fehlgeschlagen).

## Known Stubs

Keine.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: input | backend/src/findling/api/status.py | neuer Query-Parameter leaveOut (T-39-02 abgedeckt: Pattern, max_length 8000, höchstens 1000 IDs, 18 Ziffern je ID, sonst 422) |
| threat_flag: file-access | backend/src/findling/store/repo.py | zweite Leseverbindung auf state.db und vectors.db, beide mode=ro plus query_only, nur Zählungen |

## Offene Punkte für Orchestrator und Owner

- Beim lokalen Lauf von test_phase33_audit.py rief der Test `docker version` auf und hing; drei `docker.exe`-Prozesse und ein Hintergrund-pytest konnten nicht beendet werden (taskkill vom Auto-Modus abgelehnt). Docker Desktop selbst wurde nicht angefasst. Diese Testdateien rufen docker: test_exclusion_driver, test_harp_connect_supervisor, test_ops_scripts, test_phase32/33/34_audit, test_v14_zelle.
- Tombstones: `indexed` des Containers zählt auch tombstoned Zeilen (`counts()` ohne deleted_at), `indexedLeftOut` laut Plan nur lebende. Tombstones ausgelassener Storages bleiben daher im Zähler (klein, wie in 1.5).

## Saetze fuer die Owner-Runde Phase 40

Alle Wortlaute stehen so in den Katalogen; Tabellen in `docs/l10n-french.md` (und den vier weiteren Sprachtabellen). es/it/nl/pt_PT/pt_BR maschineller Entwurf unter Vorbehalt.

**(1) Mehrfachzählungs-Satz (ersetzt, Schlüsselwechsel)**

- alt en: "External storages mounted once per user are counted once per mount, so the same file can stand in this figure several times. The search itself holds every file once."
- alt de: "Je Nutzer einmal eingebundene externe Speicher werden je Einbindung gezählt, dieselbe Datei kann daher mehrfach in dieser Zahl stehen. Die Suche selbst führt jede Datei nur einmal."
- alt fr: "Les stockages externes montés une fois par utilisateur sont comptés une fois par montage, le même fichier peut donc figurer plusieurs fois dans ce chiffre. La recherche elle-même ne contient chaque fichier qu'une fois."
- neu en: "External storages mounted once per user are counted once per mount here, so the same file can stand in this figure several times."
- neu de: "Je Nutzer einmal eingebundene externe Speicher werden hier je Einbindung gezählt, dieselbe Datei kann daher mehrfach in dieser Zahl stehen."
- neu fr: "Les stockages externes montés une fois par utilisateur sont comptés ici une fois par montage, le même fichier peut donc figurer plusieurs fois dans ce chiffre."
- Grund: der zweite Satz war falsch (F6: der Index führt jede Kopie je Datei-ID); der Satz steht seit 1.6 nur noch im Rückfall.

**(2) Satz bei 0 bewusst ausgelassen (neu, ANZE-01, L-36-05)**

- en: "Nothing is left out on purpose right now. Files that are too large, of a type Findling does not read, or excluded by a rule would be counted here, and they are not in the denominator above."
- de: "Derzeit ist nichts bewusst ausgelassen. Hier stünden Dateien, die zu groß sind, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen, und sie zählen nicht im Nenner darüber."
- fr: "Rien n'est volontairement laissé de côté pour l'instant. Seraient comptés ici les fichiers trop volumineux, d'un type que Findling ne lit pas, ou exclus par une règle, et ils ne figurent pas au dénominateur ci-dessus."

**(3) Hinweis nach Regeländerung (neu, ANZE-02, L-36-06)**

- en: "The exclusion rules were changed. The search applies them at once, the counters on this page follow once they have been worked out again."
- de: "Die Ausschlussregeln wurden geändert. Die Suche wendet sie sofort an, die Zähler auf dieser Seite folgen, sobald sie neu ermittelt sind."
- fr: "Les règles d'exclusion ont été modifiées. La recherche les applique immédiatement, les compteurs de cette page suivent dès qu'ils ont été recalculés."

## TDD Gate Compliance

Je Task ein `test(39-01)`-Commit vor dem `feat(39-01)`-Commit (077d63ba vor 1fce632f, f92cc03f vor 4fc2fc18, 96b7d6d2 vor 8d6306aa). Python-Teile waren im RED-Lauf nachweislich rot (KeyError indexedLeftOut; drei rote Vertragstests). PHP-RED ist lokal nicht ausführbar, nur in CI.

## Self-Check: PASSED

- FOUND: backend/tests/test_status_leave_out.py, php/tests/Unit/ScanStatsServiceTest.php, dieses SUMMARY
- FOUND: 077d63ba, 1fce632f, f92cc03f, 4fc2fc18, 96b7d6d2, 8d6306aa, a619a056
