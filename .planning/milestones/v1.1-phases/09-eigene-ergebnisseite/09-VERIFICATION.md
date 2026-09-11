---
phase: 09-eigene-ergebnisseite
verified: 2026-09-09T08:10:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 9: Eigene Ergebnisseite Verification Report

**Phase Goal:** Der Nutzer kann in allen Treffern seiner Suche blaettern und einen Treffer oeffnen, ohne die Liste zu verlieren, und sieht dabei genau die Dateien, die er auch in der Unified Search sieht.
**Verified:** 2026-09-09T08:10:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ein Nutzer wechselt aus der Unified Search mit einem Klick auf eine Findling-Ergebnisseite, die alle Treffer zeigt statt der gekuerzten Liste | VERIFIED | `php/lib/Search/Provider.php:322-345` haengt bei paginierter Antwort einen Eintrag "Show all results" ohne `fileId` an, Ziel `findling.page.index`. `php/lib/Controller/PageController.php` rendert die vollstaendige Liste serverseitig (`PAGE_SIZE=25`). Sichtprobe 1 im Protokoll von 09-08 bestanden (`attributes: []`, korrekte Ziel-URL) |
| 2 | Der Nutzer erreicht Treffer jenseits der ersten Seite ueber Paginierung, ohne die Suche neu zu tippen | VERIFIED | `PageController::cursorPath()`, `previousUrl()`, `nextUrl()` bauen die Adresse aus Suchbegriff + Cursorpfad. Sichtproben 3, 6, 7 (Vor/Zurueck, Lesezeichen auf Seite 3, verfaelschter Cursorpfad) bestanden. 19 PHPUnit-Faelle in `PageControllerTest.php` (bestaetigt: `grep -c 'function test'` = 19) |
| 3 | Der Nutzer oeffnet einen Treffer und kommt auf dieselbe Seite derselben Trefferliste zurueck, mit derselben Suche und derselben Position | VERIFIED | `php/js/search.js` (225 Zeilen): `sessionStorage['findling:lasthit']`, Klassen-Markierung + `scrollIntoView` + Fokus bei `back_forward`. Sichtprobe 4 und 5 vom Owner am 09.09.2026 abgenommen (Sichtprobe 5 bewusst umformuliert auf "Scrollposition ist das, was der Browser gibt", mit Begruendung und Recherchedatum in `09-UI-SPEC.md`) |
| 4 | Die Ergebnisseite zeigt genau die Dateien der Unified Search: derselbe ACL-Vorfilter, derselbe finale PHP-Recheck, keine zweite Sicherheitsflaeche; der bestehende Paritaetstest deckt die neue Route mit ab | VERIFIED | `php/lib/Service/SearchService.php` ist die einzige Stelle mit `getFirstNodeById`/`isReadable` als Sicherheitsgrenze (Provider und PageController rufen beide `SearchService::run`). `backend/tests/test_php_acl_boundary.py` haelt das per Zaehl-Gate. `scripts/ci/parity_diff.py --findling-html` vergleicht die Seite gegen Dialog und Container. **CI-Lauf `Integration` (run 34316508287, commit `2c1b741`) ist gruen**: alle 10 Paritaets-Szenarien plus die negative Probe (Falsifikation) sind bestanden |
| 5 | Ist das Backend gestoppt oder antwortet es nicht, zeigt die Seite eine klare Meldung statt einer leeren Liste oder eines Fehlers | VERIFIED | `SearchOutcome::FAILURE_BACKEND_SILENT`/`FAILURE_VERSION_DRIFT` werden im Template als Fehlerblock gerendert. Sichtprobe 9 (gestopptes Backend) und 10 (verlangsamtes Backend) im Protokoll bestanden, nachdem Befund M-01 (Leerzustand ueberlagerte den Fehlerblock) in `52db222` gefixt wurde, mit Regressionstest in `test_admin_ui_contract.py` |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `php/lib/Controller/PageController.php` | Route `findling.page.index`, URL-Vertrag, Delegation an SearchService | VERIFIED | Existiert, 457 Zeilen, `FrontpageRoute`/`NoAdminRequired`/`NoCSRFRequired` je genau 1x, keine eigene ACL-Entscheidung |
| `php/lib/Text/Highlighter.php` | Zerlegung in Textstuecke ohne HTML | VERIFIED | 124 Zeilen, kein `htmlspecialchars`/`<mark`, ausschliesslich `mb_substr` |
| `php/lib/Service/SearchService.php` | Geteilter Recheck-Dienst, einzige ACL-Stelle | VERIFIED | 499 Zeilen, `getFirstNodeById` und `isReadable` je 1x, vier `FAILURE_*`-Gruende, `MAX_CONTAINER_OFFSET=1200` |
| `php/lib/Service/SearchCaps.php`, `SearchOutcome.php`, `ApprovedHit.php` | Wertobjekte | VERIFIED | Alle drei vorhanden, final, unveraenderlich |
| `php/templates/search.php`, `php/css/search.css`, `php/js/search.js` | Sichtbare Haelfte der Seite | VERIFIED | 291/469/225 Zeilen, kein `print_unescaped`, kein Hexwert, kein `innerHTML` |
| `php/img/app.svg` | Symbol des Navigationseintrags | VERIFIED | Byte-identisch zu `app-dark.svg` (`cmp` bestaetigt lokal) |
| `php/appinfo/info.xml` (Navigationsblock) | Route im App-Menue | VERIFIED | `navigations`-Block hinter `settings`, `findling.page.index` referenziert |
| `backend/tests/test_php_acl_boundary.py` | Zaehl-Gate ueber ACL-Aufrufstellen | VERIFIED | Vorhanden, Tests gruen (92 Faelle gesamt mit weiteren Gates, siehe unten) |
| `backend/tests/test_search_limits_lockstep.py` | Drift-Gate Offset-Decken | VERIFIED | Vorhanden, gruen |
| `scripts/dev/probe_page_login.sh` | Login-Probe fuer Paritaetsjob | VERIFIED | Ausfuehrbar, keine Zugangsdaten im Text |
| `scripts/ci/parity_diff.py` (`--findling-html`) | Dritter Eingabemodus | VERIFIED | `findling-hit-` Muster vorhanden, reine Standardbibliothek |
| `docs/measurements/2026-09-seitenbudget/README.md` | Gemessenes Zeitbudget | VERIFIED | Enthaelt p95, PAGE_BUDGET_SECONDS, A3-Verdikt, Abschnitt 6.3 (Nachtrag M-03) |
| `docs/audits/2026-09-phase-09/README.md` | Security/Bug/Performance-Audit | VERIFIED | Drei Abschnitte, 31 Threats abgehakt, 3 MEDIUM gefixt, 6 LOW dokumentiert entschieden |
| `docs/l10n-french.md` | Vertagte FR-Wortlaute | VERIFIED | 24 Wortlaute, Bedingung fuer vollstaendigen Katalog, ROADMAP Phase 11 zeigt darauf |
| `php/l10n/de_DE.json`, `de_DE.js` | Deutsch unter beiden Sprachcodes | VERIFIED | Git-Blob-Hash identisch zu `de.json`/`de.js` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `PageController::index` | `SearchService::run` | direkter Methodenaufruf | WIRED | `$this->searchService->run($user, $query, $titleOnly, $startCursor, $this->caps())` |
| `Provider::search` | `SearchService::run` | direkter Methodenaufruf | WIRED | `$outcome = $this->searchService->run(...)` (Zeile 168) |
| `Provider` Einstiegs-Eintrag | `findling.page.index` | `linkToRoute` ohne fileId | WIRED | `resourceUrl` referenziert die Route; Kommentar "Deliberately no fileId attribute" |
| `PageController::rows()` | `Highlighter::segments()` | Methodenaufruf je Treffer | WIRED | `Highlighter::segments($excerpt['text'], $excerpt['highlights'])` |
| `php/appinfo/info.xml` (navigations) | `PageController` | Route `findling.page.index` | WIRED | Live gegen Instanz geprueft (laut Summary 09-06), `grep -c` = 1 |
| `scripts/ci/parity_diff.py --findling-html` | `php/templates/search.php` | Zeilen-Id `findling-hit-` | WIRED | Muster vorhanden, im CI-Lauf (search-parity) erfolgreich benutzt |
| `.github/workflows/integration.yml` | `parity_diff.py` (3. Vergleich) | `--findling-html` Aufruf | WIRED | CI-Lauf 34316508287 gruen, alle 10 Szenarien + negative Probe |

### Behavioral Spot-Checks / Live-Verifikation

| Behavior | Command/Quelle | Result | Status |
|----------|------|--------|--------|
| Backend-Testsuite laeuft vollstaendig | `cd backend && uv run pytest -q` (lokal ausgefuehrt) | 1792 passed, 15 skipped, 141s | PASS |
| ACL-/Lockstep-/Trust-Boundary-/Admin-UI-/Parity-Diff-Gates isoliert | `uv run pytest -q tests/test_php_acl_boundary.py tests/test_search_limits_lockstep.py tests/test_php_trust_boundary.py tests/test_admin_ui_contract.py tests/test_parity_diff.py` | 92 passed | PASS |
| `de.json`/`de_DE.json` und `de.js`/`de_DE.js` byte-identisch | `git ls-files -s` (Blob-Hashes verglichen) | identische Hashes | PASS |
| `app.svg` byte-identisch zu `app-dark.svg` | `cmp` | identisch | PASS |
| Provider ruft SearchService, keine eigene ACL-Logik mehr | `grep` ueber `Provider.php` | `getFirstNodeById`/`isReadable`/`IRootFolder` = 0 Treffer | PASS |

### Probe Execution / CI-Laeufe (extern verifiziert)

| Workflow | Commit | Ergebnis | Status |
|----------|--------|----------|--------|
| `PHP and store metadata gates` (php.yml) | `2c1b741` | success | PASS |
| `Python gates` | `2c1b741` | success | PASS |
| `Integration` (`search-parity`, 10 Szenarien + negative Probe, 3-Wege-Vergleich inkl. Ergebnisseite) | `2c1b741` | success (run 34316508287) | PASS |

Hinweis: Der Auftrag wies darauf hin, dass diese Laeufe zum Spawn-Zeitpunkt des Verifiers noch ausstehen koennten. Sie wurden waehrend dieser Verifikation live abgewartet und liefen vollstaendig durch (Status `completed`/`success`), inklusive des CI-only-Fixes `d604880`, der die Seiten-Probes ueber `/index.php` routet (notwendig, weil der CI-Runner `php -S` benutzt).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UI-01 | 09-01, 09-03, 09-04, 09-06 | Wechsel aus Unified Search auf eigene Ergebnisseite mit Paginierung | SATISFIED | Navigationseintrag, Einstiegs-Eintrag im Dialog, PageController mit Paginierung, Sichtproben 1-3, 6-8 |
| UI-02 | 09-04, 09-05 | Treffer oeffnen und zurueckkehren ohne Listenverlust | SATISFIED | Cursorpfad, Rueckkehr-Markierung (search.js), Sichtproben 4-5 |
| UI-03 | 09-02, 09-03, 09-04, 09-06, 09-07 | Gleiche Berechtigungsgrenze wie Unified Search | SATISFIED | SearchService als einzige ACL-Stelle, ACL-Gate, Paritaetsjob (CI gruen) |

Keine verwaisten Requirements: REQUIREMENTS.md fuehrt UI-01/UI-02/UI-03 als "Complete" mit Phase 9, alle drei sind in den `requirements:`-Feldern der acht Plaene deklariert.

### Anti-Patterns Found

Keine Blocker gefunden. Gescannt wurden alle in der Phase erzeugten/geaenderten Kern-Dateien (PHP, Template, CSS, JS, Python-Gates, CI-Skripte) auf `TBD`/`FIXME`/`XXX`, Em-/En-Dash und typische Stub-Muster (`return null`, leere Handler, `console.log`-only). Keine Treffer.

Die im Auftrag genannten Abweichungsentscheidungen sind alle dokumentiert und nachvollziehbar:
- **M-01** (Leerzustand ueberlagerte Fehlerblock): gefixt in `52db222`, Regressionstest vorhanden.
- **de_DE-Katalog** (M-02): gefixt in `0175b56`, Byte-Gleichheit mit `de.json`/`de.js` verifiziert.
- **Zwei-h1** (L-01): als LOW dokumentiert, vom Owner am 09.09.2026 akzeptiert, Wiedervorlage Phase 11.
- **CI-only-Fix `d604880`**: technisch begruendet (php -S Routing-Eigenheit), betrifft nur den CI-Workflow, keine Produktionslogik.

### Human Verification

Keine offenen Punkte. Die 22 Abnahme-Sichtproben (20 aus der 09-UI-SPEC plus 2 phasenspezifische) wurden im blockierenden Checkpoint von Plan 09-08 gefahren und vollstaendig protokolliert; sechs davon (Sichtprobe 4, 5, 13, 15, 16, 17, 18, 19 — Augenarbeit: Rueckkehr-Gefuehl, zwei Browser-Engines, Fokus, Bild, Kontrast/Theme, Tastatur, Screenreader, Handybreite) tragen ein Owner-Abnahmedatum vom 09.09.2026 im Protokoll. Es gibt keine neuen, von diesem Verifier identifizierten Pruefpunkte, die zusaetzliche menschliche Abnahme erfordern wuerden.

### Deferred Items

Items, die bewusst nicht in dieser Phase geschlossen wurden und einen klaren Wiedervorlage-Ort haben (aus dem Auditbericht, LOW-Kategorie, kein Einfluss auf die 5 Erfolgskriterien):

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Vollstaendiger franzoesischer l10n-Katalog | Phase 11 | `.planning/ROADMAP.md` Zeile 177: "Vorbedingung aus Phase 9 ... ist Vorbedingung der Abgabe", zeigt auf `docs/l10n-french.md` |
| 2 | `docs/testing.md` beschreibt Paritaetsjob noch als 2-Wege-Vergleich (DI-09-06) | Phase 11 | Auditbericht/Summary 09-08 benennt Wiedervorlage in Phase 11 (Doku-Durchsicht vor Abgabe) |
| 3 | `docs/certificates.md` nennt veraltete Archiv-Zahl (L-02) | Phase 11 | Auditbericht: "Wiedervorlage: Phase 11, beim ersten Paketbau" |
| 4 | Seltene Backend-Fehlermeldung waehrend laufendem Indexlauf (L-05) | Phase 11 | Auditbericht: "Wiedervorlage: Phase 11, Launch-Haertung, Abschnitt Ressourcengrenzen" |

## Gaps Summary

Keine Gaps. Alle fuenf Roadmap-Erfolgskriterien sind durch Code, Tests und (fuer Erfolgskriterium 4) durch einen live abgewarteten gruenen CI-Lauf des Paritaetsjobs belegt. Alle acht Plaene (09-01 bis 09-08) haben ihre deklarierten must_haves (Truths, Artefakte, Key Links) im Repository wiedergefunden, keine Stubs, keine Platzhalter, keine unbelegten Behauptungen. Die drei vom Auftrag genannten Entscheidungen (M-01-Fix, de_DE-Katalog, Zwei-h1 als LOW) sind nachvollziehbar dokumentiert und im Code/den Tests wiedergefunden. Die drei CI-Workflows (php.yml, Python gates, integration.yml) sind fuer den HEAD-Commit `2c1b741` gruen.

---

*Verified: 2026-09-09T08:10:00Z*
*Verifier: Claude (gsd-verifier)*
