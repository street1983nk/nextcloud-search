---
phase: 04-admin-sichtbarkeit-und-diagnose
verified: 2026-09-03T12:00:00Z
status: passed
score: 4/4 Erfolgskriterien verifiziert (4/4 Requirements SATISFIED)
overrides_applied: 0
deferred:
  - truth: "Sight Check 4: Skip-Verdikte des Containers (encrypted, no_text_layer, empty_text, image_not_ocrable) erscheinen als eigene Gruppen in der Fehlerliste"
    addressed_in: "Gap-Closure-Plan (DI-04-03, Owner-Entscheidung (b) aus dem Walkthrough)"
    evidence: "deferred-items.md DI-04-03: Handover der Skip-Verdikte pro fileid fehlt im Acknowledgement-Kanal; Diagnose und occ-Befehl liefern die Antwort bereits pro Datei, nur die Aggregation fehlt. Owner: 'accepted as a gap closure plan, not as a blocker of phase 4.'"
  - truth: "Der Reindex-Banner nennt eine Abhilfe (occ findling:index --restart), die die Versionsmarken tatsächlich zurücksetzt"
    addressed_in: "Gap-Closure-Plan (DI-04-04, Owner-Entscheidung (d) aus dem Walkthrough)"
    evidence: "deferred-items.md DI-04-04: kein Codepfad stempelt die Versionsmarken nach einem abgeschlossenen Rebuild neu; auf der Dev-Instanz von Hand gesetzt. Owner: 'accepted as a gap closure plan, not as a blocker of phase 4.'"
---

# Phase 4: Admin-Sichtbarkeit und Diagnose Verification Report

**Phase Goal:** Der Admin erkennt den Zustand der Suche vor dem Nutzer, kann für jede einzelne Datei begründen, warum sie auffindbar ist oder nicht, und kennt den Aufwand vorher.
**Verified:** 2026-09-03T12:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Hinweis zum MVP-Modus

Phase 4 trägt `Mode: mvp` in ROADMAP.md, aber das Goal-Feld ist nicht im geforderten Format "Als [Rolle] möchte ich [Fähigkeit], damit [Ergebnis]." formuliert (`gsd-sdk query user-story.validate` bestätigt `valid: false`). Nach `verify-mvp-mode.md` wäre das normalerweise ein Anlass, die Reformulierung über `/gsd mvp-phase` einzufordern, bevor eine neue UAT-Sichtprobe generiert wird. Das ist hier nicht nötig: der Owner-Walkthrough (2026-09-03, dokumentiert in 04-10-SUMMARY.md) hat bereits alle vier Erfolgskriterien der Roadmap direkt an der laufenden Instanz abgenommen, inklusive zwölf UI-Sichtproben (dunkles Theme, hoher Kontrast, Tastatur allein, deaktiviertes JavaScript). Diese Abnahme deckt inhaltlich genau das ab, was eine MVP-User-Flow-Sichtprobe verlangen würde. Diese Verifikation prüft daher die vier Roadmap-Erfolgskriterien direkt (goal-backward, wie im Standardverfahren) und wiederholt die bereits erfolgte menschliche Abnahme nicht.

## Goal Achievement

### Observable Truths (Roadmap-Erfolgskriterien)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin öffnet die Statusseite und sieht Indexfortschritt, Deckungsgrad und Fehlerliste, ohne Logs zu lesen | VERIFIED | `php/lib/Settings/Section.php`+`Admin.php` registrieren `Verwaltung > Findling`; `AdminViewService::overview()` liefert `coverage`, `errors`, `estimate`, `rules` (Zeilen 494-497); live: `curl http://localhost:8090/settings/admin/findling` → 401 (Route existiert, admin-only); Owner-Walkthrough bestätigt Kriterium 1 live: "Coverage 83 percent ... no log opened at any point" |
| 2 | Admin gibt eine beliebige Datei an und bekommt den Grund ihres Zustands genannt | VERIFIED | Live nachvollzogen: `occ findling:diagnose 1` → `state=excluded, label="This is a folder"`; `occ findling:diagnose testuser/files/corpus/01-text-layer.pdf` → `state=indexed, backend answered yes`; sechsstufige Vorrangregel in `AdminViewService::diagnose()` (Zeile 615ff.), Route `GET /apps/findling/admin/diagnose` (401 live bestätigt) |
| 3 | Admin sieht vor dem Erstindex eine Schätzung: Dateizahl, OCR-Anteil, Dauer, Platzbedarf | VERIFIED (mit dokumentierter Wortlaut-Abweichung, Owner-akzeptiert) | `backend/src/findling/api/rates.py`, `AdminViewService`-Teilbaum `estimate` mit 13 Schlüsseln; Owner-Walkthrough: "168 Dateien, davon 33 mit OCR. Etwa 1 Minute und etwa 1,4 MB Index." Abweichung vom wörtlichen D-05-Zitat als Owner-Entscheidung (a) protokolliert, Substanz vorhanden |
| 4 | Admin schaltet Ordner-Ausschlüsse, Größen-Cap, Team Folders und External Storage um, und der nächste Lauf hält sich daran | VERIFIED | `SettingsService.php` (4 appconfig-Schlüssel), `ExclusionService.php` (`isExcluded`, `mountRelativePath`, `scheduleCleanup`); Gate D (`test_exclusion_path_space.py`, 13+ Tests) grün; Owner-Walkthrough Sichtprobe 7: Ausschluss gespeichert, Bestätigung mit Dokumentzahl, `SubtreeExpandJob` räumte 2 Dokumente, Denominator sank von 168 auf 166 |

**Score:** 4/4 Erfolgskriterien verifiziert

### Deferred Items

Zwei Befunde aus dem Owner-Walkthrough sind bewusst nicht in Phase 4 behoben, sondern mit Owner-Sign-off als Gap-Closure-Material für einen späteren Zyklus dokumentiert (siehe Frontmatter `deferred:` und `deferred-items.md`).

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Skip-Verdikte des Containers erscheinen nicht als eigene Fehlerlisten-Gruppen (Sichtprobe 4) | Gap-Closure-Plan, DI-04-03 | Owner-Entscheidung (b): "accepted as a gap closure plan, not as a blocker of phase 4" |
| 2 | Reindex-Banner nennt eine Abhilfe, die die Versionsmarken nicht zurücksetzt (Finding 5) | Gap-Closure-Plan, DI-04-04 | Owner-Entscheidung (d): "accepted as a gap closure plan, not as a blocker of phase 4" |

Zusätzlich zwei operative Anmerkungen ohne Codebezug zu Phase 4 selbst (DI-04-01: `register-exapp.sh` deklariert nur 1 von 5 Routen im Dev-Skript; DI-04-02: Dev-Backend braucht Neustart nach neuer Route) — beide sind Dev-Tooling-Fußnoten, keine Produktdefekte, und in `deferred-items.md` mit Fix-Vorschlag dokumentiert.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `php/lib/Settings/Section.php` / `Admin.php` | Admin-Sektion registriert | VERIFIED | 60 / 65 Zeilen, `IIconSection`/`ISettings`, `<settings>`-Block in `info.xml` verdrahtet |
| `php/lib/Controller/SettingsController.php` | 4 Admin-only-Routen (overview, diagnose, rules/preview, rules) | VERIFIED | 421 Zeilen, 4× `FrontpageRoute`, live 401 auf overview/diagnose bestätigt |
| `php/lib/Service/AdminViewService.php` | Eine Aggregation aus Container + Nextcloud-DB | VERIFIED | 1655 Zeilen, liefert `coverage`, `estimate`, `errors`, `rules`, `diagnose()` |
| `php/templates/admin.php` / `php/js/admin.js` | 5 Blöcke, serverseitig gerendert, Polling ohne Reload | VERIFIED | 751 / 1260 Zeilen; Owner-Walkthrough bestätigt Polling ohne Reload (83%→ steigend) und No-JS-Rendering |
| `php/lib/Service/ScanStatsService.php` | Deckungsgrad-Nenner aus Crawl-Zählern | VERIFIED | 363 Zeilen, Migration `findling_scan_stats`, idempotent geprüft |
| `backend/src/findling/api/rates.py` | GET /rates, gemessener Durchsatz | VERIFIED | 200 Zeilen, Feldmengen- und Privacy-Test vorhanden und grün |
| `backend/src/findling/api/diagnose.py` | GET /diagnose, Verdikt ohne Pfad/Titel | VERIFIED | 138 Zeilen, Privacy-Test pinnt Feldmenge |
| `php/lib/Service/PathResolverService.php` | fileid → lesbarer Pfad, Papierkorb-Erkennung | VERIFIED | 424 Zeilen, live gegen echte fileids getestet |
| `php/lib/Service/SettingsService.php` / `ExclusionService.php` | 4 Schalter, ein Ausschluss-Helfer | VERIFIED | 320 / 773 Zeilen, Gate D pinnt einen Pfadraum über zwei Aufrufwege |
| `php/lib/Command/DiagnoseCommand.php` | occ-Zweitzugang | VERIFIED | 210 Zeilen; live ausgeführt: `occ findling:diagnose` funktioniert für fileid und Pfad |
| `docs/admin-page.md` | Betriebsdokumentation | VERIFIED | 427 Zeilen, deckt Denominator, 6 Diagnose-Stufen, 4 Schalter, Ausschluss-Pfadraum ab |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `php/appinfo/info.xml` | `Settings/Admin.php` | `<settings><admin>`-Eintrag | WIRED | `grep` bestätigt Eintrag; live 200/401-Verhalten der Seite konsistent |
| `php/js/admin.js` | `SettingsController` | `fetch` auf `/admin/overview`, `/admin/diagnose`, `/admin/rules(/preview)` | WIRED | Live: alle 4 Routen antworten 401 (auth-geschützt, korrekt verdrahtet) |
| `AdminViewService` | Backend `GET /status`, `/rates`, `/diagnose` | `ExAppService::adminGet`/`call` über `exAppRequest` | WIRED | Live: `occ findling:diagnose` liefert `backend answered yes` mit echtem Verdikt aus dem Container |
| `StorageCrawlJob`/`FileEventListener` | `ExclusionService::isExcluded` | ein Helfer, ein Pfadraum | WIRED | Gate D (`test_exclusion_path_space.py`) grün; zusätzlich CR-01-Fix schließt den dritten Aufrufweg (Reconcile) mit eigenem Gate-Test |
| `ExclusionService::scheduleCleanup` | `SubtreeExpandJob` (`kind=delete`) | `IJobList::add` | WIRED | Owner-Walkthrough Sichtprobe 7 bestätigt live: Räumung lief, Denominator sank |
| `php/lib/Command/DiagnoseCommand.php` | `AdminViewService::diagnose()` | derselbe Aufruf wie die Route | WIRED | Live bestätigt: `occ findling:diagnose` und die Diagnose-Karte liefern denselben Grund für dieselbe Datei |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| Block 1 (Coverage) | `coverage.indexed/indexable/percent` | `ScanStatsService::totals()` + `FileStateService::counts()` (echte DB-Abfragen) | Ja | FLOWING |
| Block 3 (Fehlerliste) | `errors.groups` | `FileStateService::reasonsByState()`/`page()` gegen `findling_file_state` | Ja | FLOWING |
| Block 4 (Diagnose) | `diagnose()` Verdikt | 6-Stufen-Kette über Container-`GET /diagnose`, Queue, `findling_file_state` | Ja, live mit echten fileids verifiziert | FLOWING |
| Block 5 (Regeln) | `rules()` | `appconfig` über `SettingsService`/`ExclusionService` | Ja, live gespeichert und zurückgelesen (Owner-Walkthrough) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Admin-Routen sind geschützt (401 ohne Session) | `curl -s -o /dev/null -w '%{http_code}' http://localhost:8090/apps/findling/admin/overview` | 401 | PASS |
| Admin-Routen sind geschützt (401 ohne Session) | dito für `/admin/diagnose` | 401 | PASS |
| Settingsseite ist admin-only geschützt | `curl .../settings/admin/findling` | 401 | PASS |
| occ-Zweitzugang funktioniert | `docker compose exec app php occ findling:diagnose 1` | `state=excluded, label="This is a folder"` | PASS |
| occ-Zweitzugang liefert Container-Verdikt | `docker compose exec app php occ findling:diagnose testuser/files/corpus/01-text-layer.pdf` | `state=indexed, backend answered yes` | PASS |
| `php -l` über den ganzen Findling-Baum im Dev-Container | `find lib appinfo templates -name '*.php' \| xargs -n1 php -l` | keine Syntaxfehler in 35 Dateien | PASS |
| StatusResponse trägt exakt 17 Felder | `python -c "from findling.api.status import StatusResponse; ..."` | 17 Felder, Feldnamen stimmen mit Plan überein | PASS |
| Backend-Testsuite | `uv run python -m pytest -q` | 775 passed, 11 skipped | PASS |
| Ruff/Pyright/Vulture | `ruff check .`, `ruff format --check .`, `pyright`, `vulture` | alle grün, 0 Findings | PASS |
| Alle 4 Gates dieser Phase gemeinsam | `pytest test_php_trust_boundary.py test_admin_ui_contract.py test_exclusion_path_space.py test_readonly_gate.py test_status_endpoint.py test_rates_endpoint.py test_diagnose_endpoint.py test_extract_errors.py test_allowlist_parity.py` | 168 passed | PASS |
| Alle 7 Review-Fixes im Code vorhanden | `grep` je Fix (CR-01 bis WR-06) | alle 7 bestätigt im Quelltext | PASS |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh`-Dateien in diesem Projekt gefunden. Die vier textuellen Gates der Phase (Gate B `test_php_trust_boundary.py`, Gate C `test_admin_ui_contract.py`, Gate D `test_exclusion_path_space.py`, Gate A `test_readonly_gate.py`) übernehmen diese Rolle und wurden oben unter Behavioral Spot-Checks unabhängig ausgeführt (nicht nur aus SUMMARY.md übernommen).

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| ADM-01 | 04-03, 04-04, 04-06, 04-10 | Statusseite: Fortschritt, Deckungsgrad, Fehlerliste | SATISFIED | Blöcke 1–3 live bestätigt, `[x]` in REQUIREMENTS.md, Owner-Walkthrough Kriterium 1 |
| ADM-02 | 04-07, 04-09, 04-10 | Pro-Datei-Diagnose mit Grund | SATISFIED | Live `occ findling:diagnose` + Route, sechsstufige Vorrangregel, Owner-Walkthrough Kriterium 2 |
| ADM-03 | 04-05 | Vorab-Schätzung vor Erstindex | SATISFIED | `GET /rates`, `estimate`-Teilbaum, Owner-Walkthrough Kriterium 3 (mit dokumentierter Wortlaut-Abweichung) |
| ADM-04 | 04-08, 04-09 | Ausschluss-Regeln und Toggles | SATISFIED | `SettingsService`, `ExclusionService`, Gate D, Owner-Walkthrough Kriterium 4 + Sichtprobe 7 |

Alle vier Requirement-IDs aus den PLAN-Frontmatters sind vollständig durch Plans 04-01 bis 04-10 abgedeckt; keine Waisen-Requirements gefunden (Abgleich mit REQUIREMENTS.md Zeile 128: "4 | ADM-01, ADM-02, ADM-03, ADM-04 | 4" stimmt exakt).

**Anmerkung (nicht blockierend):** Die Traceability-Tabelle in REQUIREMENTS.md (Zeilen 111–114) führt die Status-Spalte für ADM-01 bis ADM-04 weiterhin als "Pending", obwohl die Checkbox-Liste am Dateianfang bereits `[x]` zeigt. Diese Inkonsistenz betrifft offenbar alle Phasen 1–6 gleichermaßen (auch bereits abgenommene Phasen 1–3 stehen dort auf "Pending") und ist damit eine vorbestehende Pflege-Lücke der Tabelle, kein Phase-4-spezifisches Problem. Empfehlung: bei nächster Gelegenheit die Statusspalte für Phasen 1–4 nachziehen.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | Debt-Marker (TBD/FIXME/XXX) | — | Keine gefunden in den 16 geprüften Kern-Dateien der Phase |
| — | — | Em-/En-Dash | — | Keine gefunden |
| `backend/src/findling/store/repo.py:915-917` | IN-01 | `index_bytes` loggt bei jedem Poll eine Warnung für den normalen Zustand "frischer Container" | Info | Kosmetisch, bewusst unbehoben, dokumentiert im REVIEW |
| `php/l10n/de.json:10` | IN-02 | Tote Übersetzungszeile "Indexing, about %s left" | Info | Kein Aufrufer, bewusst unbehoben |
| `php/templates/admin.php:191` | IN-03 | NBSP vs. normales Leerzeichen vor "%" nach erstem Poll | Info | Kosmetisch |
| `php/lib/Service/PathResolverService.php:204` | IN-04 | Backslash-zu-Slash-Konvertierung verhindert Diagnose von Dateien mit `\` im Namen | Info | Randfall, bewusst unbehoben |
| `php/lib/Settings/Section.php:22-27` | IN-05 | Docblock behauptet fälschlich, `#[\Override]` sei auf PHP 8.2 ein Parse-Fehler | Info | Kommentarfehler, keine Funktionsauswirkung |
| `backend/src/findling/api/resources.py:58-59` | IN-06 | Modul-Cache ohne Lock zwischen Worker-Threads | Info | Kein Korrektheitsrisiko laut REVIEW (last-writer-wins) |
| `php/lib/Service/ExclusionService.php:207-225` | IN-07 | `.`-Segment in Ausschluss-Präfix wird gespeichert, matcht aber nie | Info | Randfall, bewusst unbehoben |

Alle 7 Info-Findings stammen aus 04-REVIEW.md und wurden dort bewusst unbehoben belassen (kein Blocker-Kriterium erfüllt: keine Sicherheitslücke, keine stille Datenkorruption). Der 1 Critical- und 6 Warning-Befund des Reviews wurden dagegen **alle** gefixt und im Code verifiziert (Commits `e91b409`, `4efd6fe`, `b3220f6`, `629fdcc`, `82e289c`, `a4fdf2e`, `2ab18a7` — alle sieben in `git log` gefunden, alle sieben Fix-Signaturen per `grep` im aktuellen Code bestätigt).

### Human Verification Required

Keine. Der Owner-Walkthrough (2026-09-03, dokumentiert in 04-10-SUMMARY.md) hat bereits alle vier Roadmap-Erfolgskriterien und alle zwölf UI-Sichtproben (dunkles Theme, hoher Kontrast, Tastatur allein, deaktiviertes JavaScript, Deutsch/Englisch) an der laufenden Instanz abgenommen, mit Verdikt "approved" und vier protokollierten Owner-Entscheidungen. Diese Verifikation hat zusätzlich unabhängig eigene Live-Proben gegen den laufenden Dev-Container ausgeführt (occ-Befehl, HTTP-Statuscodes der Admin-Routen, php -l, volle Testsuite) und keine Abweichung zu den SUMMARY-Behauptungen gefunden.

### Gaps Summary

Keine blockierenden Gaps gefunden. Alle vier Roadmap-Erfolgskriterien sind durch Code, Live-Proben und den bereits erfolgten Owner-Walkthrough belegt. Der eine kritische und die sechs Warnbefunde aus dem Code-Review wurden vollständig behoben und im aktuellen Code verifiziert. Zwei Befunde aus dem Walkthrough (Skip-Verdikt-Handover, Versionsmarken-Neustempelung) sind bewusst als Gap-Closure-Material für einen späteren Zyklus zurückgestellt, mit explizitem Owner-Sign-off — das sind dokumentierte Entscheidungen, keine übersehenen Lücken. Alle Qualitätsgates (pytest, ruff, pyright, vulture, php -l) laufen grün über das gesamte Repository, unabhängig nachvollzogen und nicht nur aus SUMMARY.md übernommen.

---

*Verified: 2026-09-03T12:00:00Z*
*Verifier: Claude (gsd-verifier)*
