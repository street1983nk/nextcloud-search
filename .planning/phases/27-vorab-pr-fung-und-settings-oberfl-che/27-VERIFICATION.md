---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
verified: 2026-09-29T18:30:00Z
status: human_needed
score: 4/4
overrides_applied: 0
deferred:
  - truth: "OCR-indexierte Dateien mit skipped(no_text_layer) zählen weiter unter der Kachel Übersprungen (Rest von WR-04)"
    addressed_in: "Phase 29"
    evidence: "Owner-Entscheid 29.09.: in Phase 29 (Launch-Härtung) klären; 27-REVIEW-FIX.md WR-04 'Not done, owner decision needed'"
human_verification:
  - test: "Die 12 Review-Fixes (918f340d..d25c85e8) pushen und den Lauf 'PHP and store metadata gates' abwarten"
    expected: "PHPUnit grün inklusive der neuen Fälle in ProbeServiceTest (WR-06 inForce, WR-07 adopt), ScanRecountJobTest und CrawlAdvanceServiceTest (WR-01)"
    why_human: "Die neuen PHPUnit-Fälle liefen nirgends; lokal gibt es keinen Server-Checkout und kein vendor, nur php -l ist lokal geprüft. Push nur mit Owner-Wort."
  - test: "fp32-Zweig der Probe einmal live fahren (standard + fp32 auf dem HaRP-Harness)"
    expected: "Download mit Fortschritt, Digest geprüft, beide Modellkinder gemessen, Verdikt mit Ursache; bei nofit wird nur die selbst geladene Datei gelöscht"
    why_human: "Nur automatisiert belegt (Tests, Python gates 36578517859); live bewusst nicht gefahren (470268510 Bytes Download plus Neueinbettung), Owner-Entscheid in 27-15"
  - test: "Maschinenübersetzungen der neuen Sätze aus WR-02 (Nenner-Neuzählung) und WR-10 (digest_mismatch bei abgelegter Datei) in fr/es/it/nl/pt_BR/pt_PT lesen"
    expected: "Sinngleich mit DE/EN, zusammen mit dem Release-Text abgenommen"
    why_human: "Sprachqualität ist nicht maschinell prüfbar; die Gates prüfen nur Vollständigkeit und Gleichstand"
---

# Phase 27: Vorab-Prüfung und Settings-Oberfläche Verification Report

**Phase Goal:** Der Admin sieht auf einer ersten echten Settings-Fläche erkannte Hardware, Vorschlag und Verdikt, und ein Profil wird erst gespeichert, nachdem eine echte Probe auf DIESER Box "passt" gesagt hat.
**Verified:** 2026-09-29
**Status:** human_needed
**Re-verification:** Nein, Erstverifikation

Stand geprüft: lokales main, HEAD 9e370e66. origin/main = 2b9de323. Lokal und ungepusht sind nur die Review-Dokumente, die 12 Fix-Commits 918f340d..d25c85e8 und 9e370e66. Richtigstellung zum Auftrag: der Quick-Task 260929-kii (f5953fbd, e3af082c, 65e860c8, bbb4f406, a8e3d7ea) ist bereits in origin/main enthalten und lief in den CI-Läufen auf a8e3d7ea mit (`git log origin/main..HEAD` zeigt ihn nicht).

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Adminseite: ein Auswahlfeld mit genau drei Profilen, Hinweisfläche mit Kernen/Speicher und Vorschlag, Knöpfe "Übernehmen und prüfen" und "Bei Sparsam bleiben"; ohne Klick bleibt Sparsam; kein Erweitert-Bereich | VERIFIED | `php/templates/admin.php` Z. 1131 bis 1233: Block `findling-profile`, `<select id="findling-profile-select">` mit genau `economy`/`standard`/`performance` (Z. 1150 bis 1154), Hinweise `Detected: cores %1$s, memory %2$s` und `Suggested for this box: %s` (Z. 1136, 1138), Knöpfe `Apply and check` (Z. 1191) und `Stay on Economy` (Z. 1194), Katalog DE "Übernehmen und prüfen" / "Bei Sparsam bleiben". Default: `SettingsService::PROFILE_DEFAULT = 'economy'`, `profile()` fällt ohne Schlüssel und bei ungültigem Wert auf economy; `profileStored()` per `hasKey`; das Formular wird mit dem Vorschlag vorbelegt, gespeichert wird aber nichts ohne Klick. Kein `<details>`/advanced im Block. Live-Beleg 27-15 `raw/01-erstaufruf.txt` (profileStored false, wirksam economy), Owner-Abnahme der Fläche per Playwright. Hinweis: das fp32-Häkchen unter dem Auswahlfeld ist ein zweites Bedienelement, per D-27-01 und UI-SPEC vom Owner so entschieden, kein Erweitert-Bereich |
| 2 | "Übernehmen und prüfen" fährt eine echte Probe (N-Slot am OCR-Pfad mit mitgelieferter Scanseite, RAM-Rechnung mit gemessenen Slot-Kosten, bei fp32 Modellprobe) und zeigt passt/passt knapp/passt nicht mit Ursache; gespeichert nur bei "passt" | VERIFIED (int8 live, fp32 nur automatisiert) | `worker/probe_run.py` `_steps` -> `_pause` -> `_weights` (nur bei fp32-Wechsel) -> `_measure`; `_measured` misst erst einen Slot auf `probe_scan.pdf` (Digest vor Gebrauch geprüft, Z. 630), rechnet `slot_cost = headroom - minimum`, `probe.judge` mit `max(slot_cost, OCR_SLOT_COST_BYTES)`, fährt N Kinder nur wenn "fits" und N > 1, `judge_run` auf dem niedrigsten Headroom. Scanseite unabhängig nachgemessen: sha256 `320bb1aa...a81f3`, 79506 Bytes, gleich `PROBE_SCAN_SHA256`/`PROBE_SCAN_BYTES`. `_model_step` misst int8- und fp32-Kind. Verdikte `fits`/`narrow`/`nofit`, jede Ursache mit Satz in `admin.php` (Z. 1055 bis 1075). Speichern: einziger Commit-Pfad `ProbeService::takeOver` Z. 318, nur bei `VERDICT_FITS`, passender Id (hash_equals) und Ziel, und seit WR-06 nur bei unverändertem Stand; `ProfileSettingsController::saveProfile` speichert nur `isDownward` (sonst 400 `probe_required`). Live 27-15: fits gespeichert, nofit memory_short und narrow reserve_thin nicht gespeichert, Aufwärts ohne Probe 400 |
| 3 | Probe vorab gegen die Speichergrenze gerechnet, kein OOM durch die Probe; höchstens eine Probe gleichzeitig; Zeitdeckel; Nicht-Admin erreicht Probe- und Profilroute nicht | VERIFIED | Vorab-Tore: `first_slot_admitted` (Slot-Kosten plus `GUARD_RESERVE_BYTES`) vor dem ersten Kind, `model_child_admitted` vor jedem Modellkind, N Kinder erst nach `judge` "fits". Einzelflug: `ProbeRun.start` unter `_start_lock`, laufende Probe -> `busy` (live `raw/05-busy.txt`). Deckel: `asyncio.timeout(self._measure_seconds)` (Messteil), `asyncio.timeout(self._download_seconds)` (Download), Pause-Deckel -> `pause_timeout`. Rechte: `backend/appinfo/info.xml` `^/probe$` und `^/probe/state$` mit `<access_level>ADMIN</access_level>`; die drei PHP-Routen in `ProfileSettingsController` tragen nur `FrontpageRoute`, keinen der Admin-Aufheber (`NoAdminRequired`, `NoCSRFRequired`, `PublicPage`, `ExAppRequired`), also Admin plus CSRF-Token durch die SecurityMiddleware. CI: Integration 36578517923, Schritt "A user who is not an admin reaches neither the probe nor the profile route" (integration.yml Z. 273 bis 295) grün; HaRP deploy 36581106370 prüft die Routen samt Level; lokal 403 in `raw/07-nicht-admin.txt` |
| 4 | Alle neuen Texte in allen acht Sprachkatalogen (16 Dateien) im Gleichstand, Katalog-Gates grün | VERIFIED | Unabhängige Gegenprobe (eigenes Skript, nicht die Gates der Umsetzung): alle 8 `.json` haben 289 Schlüssel, identische Schlüsselmengen, keine leeren Werte; jede `.js` ist inhaltlich gleich ihrer `.json`; alle 179 Singular- und 4 Pluralschlüssel, die `admin.php` und `admin.js` als Literal an `$l->t`/`t('findling', ...)`/`n(...)` übergeben, stehen in allen 8 Katalogen. Gates grün lokal (pytest 4130 passed) und in Python gates 36578517859 (Stand a8e3d7ea, 287/288 Schlüssel; die 289. aus WR-10 nur lokal) |

**Score:** 4/4 Success Criteria verifiziert

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | skipped(no_text_layer) OCR-indexierter Dateien zählt weiter unter "Übersprungen" (WR-04-Rest) | Phase 29 | Owner-Entscheid, Launch-Härtung; 27-REVIEW-FIX.md WR-04 |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/findling/probe.py` | Codes, Snapshot, judge/judge_run, Vorab-Tore, Scan-Pin, Haltesignal, measure() | VERIFIED | 595 Zeilen, substanziell, von `probe_run.py`, `api/probe.py`, `worker/watch.py` genutzt |
| `backend/src/findling/worker/probe_run.py` | Orchestrator: Einzelflug, Pause, Download/Digest, Messteil, Aufräumen, Recover | VERIFIED | 854 Zeilen, `ProbeRun` in `api/probe.py` und Lifespan verdrahtet |
| `backend/src/findling/api/probe.py` | POST /probe, GET /probe/state | VERIFIED | Router Z. 123 und 149, Routen in info.xml als ADMIN |
| `backend/src/findling/extract/probe_scan.pdf` | synthetische Scanseite mit Digest-Pin | VERIFIED | Digest und Größe unabhängig nachgemessen |
| `php/lib/Controller/ProfileSettingsController.php` | drei Admin-Routen, kein Verdikt aus dem Browser | VERIFIED | Start nur bei `needsProbe`, Speichern nur `isDownward` |
| `php/lib/Service/ProbeService.php` | Start, State, Take-over mit Commit-Bindung | VERIFIED | Commit nur bei fits, Id, Ziel, unverändertem Stand (WR-06), Adopt (WR-07) |
| `php/lib/Service/SettingsService.php` | profileStored, needsProbe, isDownward, saveProfile | VERIFIED | Default economy, beide Schlüssel zusammen |
| `php/lib/Service/AdminViewService.php` | Profil-, Probe-, Env-, Reindex-Felder, Token nicht an die Seite | VERIFIED | per Template-Nutzung geprüft |
| `php/templates/admin.php`, `php/js/admin.js` | Block Leistungsprofil, Poll 2000 ms, Verdikt | VERIFIED | `ROUTE_PROFILE_CHECK = 'admin/profile/check'`, `POLL_PROBE_MS = 2000`, Verdikt-Rendering Z. 1847 |
| `php/l10n/*` (16 Dateien) | Gleichstand | VERIFIED | siehe SC4 |
| `.github/workflows/integration.yml` | Live-Nicht-Admin-Schritt | VERIFIED | Z. 273 bis 295, `expect_refused` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| admin.js | ProfileSettingsController | POST/GET `admin/profile/check`, POST `admin/profile` | WIRED | Konstante und Poll im Skript, Routen per FrontpageRoute |
| ProfileSettingsController | ProbeService | `start()`, `state()` | WIRED | direkt injiziert |
| ProbeService | Container `/probe`, `/probe/state` | ExAppService adminSend/adminState | WIRED | live in 27-15 und in Integration belegt |
| api/probe.py | ProbeRun | `start()` / Snapshot | WIRED | Router ruft Orchestrator |
| ProbeService.takeOver | SettingsService.saveProfile | nur bei fits | WIRED | Z. 318 bis 319, einziger Aufwärts-Schreibpfad |
| ProbeRun | Poller/EmbedRunner | hold_for_probe/release_probe_hold | WIRED | `_pause` und `finally` in `_run` |

### Behavioral Spot-Checks und lokale Gates (unabhängig gefahren, HEAD 9e370e66)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Python-Suite | `cd backend && uv run pytest -q` | 4130 passed, 25 skipped, 1 warning, 285 s | PASS |
| Lint | `uv run ruff check` | All checks passed! | PASS |
| Format | `uv run ruff format --check` | 183 files already formatted | PASS |
| Typen | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | 0 errors, 0 warnings, 0 informations | PASS |
| Totcode | `uv run vulture src tests --min-confidence 80` | keine Befunde | PASS |
| PHP-Syntax | `docker exec findling-harp-nextcloud php -l` auf allen 25 PHP-Dateien, die seit aeef83be (erster 27-Commit) geändert sind; Baum `php/` ist nach `/var/www/html/custom_apps/findling` gemountet (md5 gleich) | alle "No syntax errors" | PASS |
| Katalog-Gleichstand | eigenes Skript (Schlüsselmengen, js=json, Literal-Abdeckung) | 8 x 289, 0 Abweichung, 0 fehlend | PASS |
| Scanseite | `sha256sum`, `wc -c` | gleich dem Pin | PASS |
| PHPUnit | nicht lokal lauffähig (kein vendor, kein Server-Checkout) | letzter Lauf CI 36578517939 auf a8e3d7ea, ohne die Review-Fix-Fälle | SKIP, siehe Human Verification 1 |

Die 25 Skips sind plattformabhängig (POSIX-Grenzen, SIGKILL, fehlende Werkzeuge unter Windows); der Linux-Lauf in Python gates 36578517859 trägt sie, allerdings auf a8e3d7ea, also ohne die Testfälle der Review-Fixes (CR-01, WR-07, WR-08, WR-09 laufen lokal grün, soweit nicht POSIX-gebunden).

### CI-Stand (Owner-Angabe, gegen 27-16-SUMMARY abgeglichen)

| Workflow | Lauf | Commit | Ergebnis |
|----------|------|--------|----------|
| PHP and store metadata gates | 36578517939 | a8e3d7ea | success |
| Integration (inkl. Nicht-Admin-Schritt) | 36578517923 | a8e3d7ea | success |
| Resilience | 36578517899 | a8e3d7ea | success |
| Python gates | 36578517859 | a8e3d7ea | success |
| Multi-arch image | 36578517843 | a8e3d7ea | success |
| HaRP deploy | 36581106370 | 2b9de323 | success (nach Routen-Ratschen-Fix) |

Nicht in CI gelaufen: alle Commits nach 2b9de323, also die 12 Review-Fixes (Python, PHP, Template, Kataloge). Sie sind lokal durch pytest, Python-Gates und php -l gedeckt, ihre PHPUnit-Fälle nicht.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PRUEF-01 | 27-02 bis 27-07, 27-09, 27-11, 27-12, 27-14 bis 27-16 | Echte Probe vor dem Speichern, Verdikt mit Ursache, Speichern nur bei passt, Vorab-Rechnung, Einzelflug, Deckel, ADMIN | SATISFIED | SC2, SC3; fp32-Zweig nur automatisiert |
| UI-01 | 27-01, 27-04, 27-07, 27-08, 27-10, 27-12, 27-13, 27-15, 27-16 | Erste Settings-Fläche, geschlossene Profilmenge, Hinweisfläche, ADM-04, acht Kataloge | SATISFIED | SC1, SC4 |

Keine verwaisten Requirements: REQUIREMENTS.md ordnet Phase 27 nur PRUEF-01 und UI-01 zu. Die Checkboxen dort stehen noch auf Pending (Nachführung beim Phasenabschluss).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (alle seit aeef83be geänderten Dateien unter php/ und backend/src, ohne l10n) | | TBD/FIXME/XXX | keine | 0 Treffer |
| (dieselben) | | TODO/HACK/not yet implemented | keine | 0 Treffer |

### Human Verification Required

1. **PHPUnit der Review-Fixes in CI**
   **Test:** Die Commits 918f340d..9e370e66 mit Owner-Wort pushen, Lauf "PHP and store metadata gates" abwarten.
   **Expected:** grün inklusive der neuen Fälle (WR-01 ScanRecountJob/CrawlAdvance, WR-06 inForce, WR-07 adopt), dazu Python gates auf Linux mit den neuen Kindtests.
   **Why human:** lokal kein PHPUnit möglich; Push nur mit Owner-Freigabe.
   **Erledigt (2026-09-29):** Owner-Wort "ja", Push bis c87a0239; alle sechs Workflows grün: PHP and store metadata gates 36596834116, Python gates 36596834155, Integration 36596834631, Resilience 36596834180, Multi-arch image 36596834250, HaRP deploy 36596834148.

2. **fp32-Zweig live**
   **Test:** standard + fp32 auf dem HaRP-Harness prüfen lassen.
   **Expected:** Download, Digest, zwei Modellkinder, Verdikt mit Ursache; nofit löscht nur die selbst geladene Datei.
   **Why human:** großer Download und Neueinbettung, per Owner-Entscheid in 27-15 nicht gefahren.

3. **Maschinenübersetzungen WR-02/WR-10**
   **Test:** die zwei neuen Sätze in fr/es/it/nl/pt_BR/pt_PT lesen.
   **Expected:** sinngleich, mit dem Release-Text abgenommen.
   **Why human:** Sprachqualität.

### Gaps Summary

Keine Blocker. Alle vier Success Criteria sind im Code belegt und mit unabhängigen Mustern gegengeprüft: ein Auswahlfeld mit drei Profilen und Hinweisfläche, Default economy ohne Schreibzugriff, eine echte zweistufige Probe mit Vorab-Toren, Einzelflug und Deckeln, ein einziger Aufwärts-Schreibpfad nur bei "fits", ADMIN auf Container- und PHP-Routen samt grünem Live-Nicht-Admin-Schritt in CI, und 16 Kataloge im Gleichstand. Der Owner hat Fläche (27-15) und Phase (27-16) abgenommen. Offen bleiben drei menschliche Punkte: die PHPUnit-Fälle der 12 lokalen Review-Fixes sind noch nie gelaufen, der fp32-Zweig ist nur automatisiert belegt, und zwei neue Sätze liegen in fünf Sprachen nur maschinell übersetzt vor. Der WR-04-Rest ist per Owner nach Phase 29 verschoben.

---

_Verified: 2026-09-29_
_Verifier: Claude (gsd-verifier)_
