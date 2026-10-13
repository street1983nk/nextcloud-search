---
phase: 32-filter-in-der-unified-search
verified: 2026-10-13T11:25:53Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "Jeder Befund MEDIUM oder höher ist vor Phasenabschluss gefixt und durch einen Regressionstest belegt (32-08)"
    reason: "M-32-02 (Dokumente gelöschter Nutzer bzw. abgeschalteter Mounts bleiben im Index) entsteht nicht durch Phase 32: der Abgleich läuft seit früheren Phasen nur über die Mounts aus files.mounts(), die Grenze ist in docs/admin-page.md als bewusst dokumentiert, und der Fix liegt in backend/src, das D-30-08/D-32-06 in dieser Phase sperren. Wirkung nie ein Fremdtreffer, höchstens belegte Kandidatenplätze. Offen als Owner-Frage (Zielplan und Karenz)."
    accepted_by: "Owner (Verifikationsauftrag 13.10.2026: M-32-02 als bekannte Lücke außerhalb des Phasenziels werten)"
    accepted_at: "2026-10-13T11:25:53Z"
deferred:
  - truth: "Owner-Abnahme des Store-Satzes Teil Phase 32 (docs/store-listing.md, 'Entwurf v1.5.0 (Teil Phase 32)'), danach info.xml und READMEs"
    addressed_in: "Phase 36"
    evidence: "Phase 36 SC3: 'Owner hat Store-Text und Produkt in einer gemeinsamen Playwright-Runde mit echten Testdateien abgenommen'; REL-05"
  - truth: "LOW-accept L-32-04 (Groß- und Kleinschreibung auf Speichern ohne Unterscheidung, nur gebaute Werte)"
    addressed_in: "Phase 36"
    evidence: "32-AUDIT.md LOW-Entscheidungen: 'Zielphase 36 (Launch-Korpus mit externem Speicher)'; Phase 36 SC1 Audit und Launch-Härtung"
---

# Phase 32: Filter in der Unified Search, Verifikationsbericht

**Phasenziel:** Nutzer können direkt in der Nextcloud Unified Search nach Dateityp und Ordner filtern, ohne die Ergebnisseite zu öffnen
**Verifiziert:** 2026-10-13T11:25:53Z
**Status:** passed
**Re-Verifikation:** Nein, Erstverifikation
**Stand:** main, HEAD 46161352. Seit 4c481f74 (Stand aller CI-Läufe unten) nur Planungsdateien geändert (`git diff --stat 4c481f74..HEAD`: `.planning/REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `32-08-SUMMARY.md`, `32-AUDIT.md`, `deferred-items.md`), kein Produktcode.

## Zielerreichung

### Beobachtbare Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 1 | SC1 / USRCH-01: Nutzer wählt einen der sechs Typfilter des Findling-Providers und sieht nur Treffer dieses Typs | VERIFIED | `Provider.php:182-191` deklariert `types` in `getSupportedFilters()`, `:238-243` die `FilterDefinition` (TYPE_STRING); `typesOf()` `:384-393` liest über den einen Parser `SearchFilters::typesFrom()` (`SearchFilters.php:174-193`, geschlossene Menge `TYPES` mit sechs Namen). Wire-Weg `ExAppService.php:452,466,544,560` (`types` im Body nur wenn nicht leer). Skript `php/js/unified-search.js` registriert sechs Typeinträge in der Reihenfolge von `TYPES`, Klick sendet `filterParams: { types: group }`. deploy-harp 38385966780 auf allen vier Beinen: "pdf: HTTP 200, seed ids [37] as expected", "text: ... [35 36 38]", "chip-pdf: ... [37]", Filterkarte `"types":"string","folder":"string"`. Browser: 32-07-ABNAHME Probe 2 und Nachprobe A2 (nur Bericht.pdf, Anfrage `findling-filter/search?...&types=pdf`) |
| 2 | SC2 / USRCH-02: Einschränkung auf einen Ordner zeigt nur Treffer darin und in Unterordnern; Treffer ohne Leserecht erscheinen nie (finaler PHP-Recheck unverändert) | VERIFIED | `folderOf()` `Provider.php:426-449`; `SearchService::scopeOf()` `:753-771` löst über `Folder::get()` im Baum des Fragenden auf und verlangt einen Ordner strikt unterhalb des Nutzerordners; der Recheck bleibt `readableFile($scope ?? $userFolder, ...)` `:425`, also dieselbe Methode mit engerer Wurzel. `getFirstNodeById(` und `->isReadable(` je genau einmal im ganzen `php/lib` (grep: nur `SearchService.php:569` und `:586`). `backend/tests/test_php_acl_boundary.py` seit a632a35c unverändert (diff 0 Zeilen) und lokal grün. CI deploy-harp: "folder: ... [35 36 37]" (Ordner mit Unterordner), "inner: ... [36]", Fremd.txt außerhalb fehlt. Integration 38385966737, team-folder-acl: Gruppenordner, ACL-gesperrte Datei "expected [], got []", gesperrter Unterordner leer, Kontrollnutzer mit Recht "[56]", empfangener Share "/ShareF-ci expected [59], got [59]", Außenstehender leer; Urteil "acl=ok plain=ok folder=ok" |
| 3 | SC3 / USRCH-03: unbekannte, leere oder manipulierte Filterwerte werden ignoriert, dieselben Treffer wie ohne Filter, nie leer oder Fehler; Regressionstest PHP und Backend | VERIFIED | PHP: `ProviderTest::testATypeValueThatNamesNoGroupIsTheSearchWithoutAFilterAndThrowsNothing` (10 Werte inkl. NUL, Überlänge, Array, Objekt), `testAFolderValueThatIsNoFolderIsTheSearchWithoutAFilterAndThrowsNothing` (12 Werte), `testADotSegmentIsNoFolderAndNotAnEmptyGroup` (M-32-01), `SearchServiceTest::testEveryFolderThatCannotBeUsedGivesTheSearchWithoutAFolder`; PHPUnit in CI 38385967900 "OK (666 tests, 2456 assertions)". Backend: `test_search_endpoint.py:470` und `test_snippets_endpoint.py:365` (`types=[]` gleich ohne Feld). E2E alle vier Beine: unknown, long, missing, dots, file, root, doubled je "HTTP 200 and the ids of the unfiltered search", mixed gleich `types=pdf`. Audit-Korpus 59 Werte x 2 Provider gegen echte Instanz, 137 passed nach Fix d09e5a5a. Leerwert `types=`/`folder=`: HTTP 400 des Kerns vor Findling (Owner-Entscheid D-32-01, in CI festgehalten "empty-types: HTTP 400 ... refused by the core before Findling is asked") |
| 4 | Die Einträge erscheinen in der Unified Search jeder angemeldeten Seite, ohne Scheingruppen | VERIFIED | `Application.php:55,59,135` registriert `Provider`, `FilterProvider` und den Listener; `LoadUnifiedSearchFiltersListener` lädt Skript und Übersetzungen nur bei `isLoggedIn()`. `FilterProvider` (ID `findling-filter`, `getOrder()` null, ohne `types`/`folder` leere Gruppe ohne Backend-Aufruf, sonst unverändert `Provider::search()`) behebt Befund A (acht Gruppen ohne Chip). CI: "provider list: findling-filter hidden", "chipless: HTTP 200 and an empty group". Skript schützt sich bei fehlender API (`start` prüft `OCA.UnifiedSearch.registerFilterAction`), `node --check` lokal ok |
| 5 | Ordnerwert verlässt PHP nie | VERIFIED | `backend/src` seit a632a35c unverändert (diff 0 Zeilen); `ExAppService.php` ohne `folder` (grep, nur `types`); Audit-Proxy-Mitschnitt P4/S3 ohne Ordnerbyte; Quelltextprobe in `test_phase32_audit.py` lokal grün |
| 6 | Ordnerbudget gemessen, Konstanten belegt (32-03) | VERIFIED | `SearchService.php:116-135`: `FOLDER_FETCH_LIMIT = 100`, `FOLDER_MAX_ROUNDS = 12`, Kommentar verweist auf `docs/measurements/2026-10-ordnerfilter/README.md`; Audit P1/P5 unabhängig nachgemessen (eng +64/+86 ms, höchstens 11+1 Containeraufrufe) |
| 7 | l10n: vier neue Schlüssel in allen 16 Katalogen | VERIFIED | grep: "File contents: %s", "File contents in a folder", "Choose the folder to search in", "File contents in %s" je in 8 `.json` und 8 `.js` unter `php/l10n/`; fünf `docs/l10n-*.md` nennen sie; Vertragstest `test_unified_search_plugin.py` lokal grün |
| 8 | CI-Beleg auf NC 33, 34, 35 und arm64 | VERIFIED | HaRP deploy 38385966780, Schritt "Unified search filters, type and folder on the ordinary search route": je Bein 19 Ergebniszeilen (as expected / ids of the unfiltered search / HTTP 400) auf stable33, stable34, stable35, stable34 arm64, alle Jobs success |
| 9 | Owner-Abnahme gemeinsam per Playwright, Wortlaut de/en/fr | VERIFIED | `32-07-ABNAHME.md` "Owner-Abnahme": Antworten 13.10.2026 wörtlich ("So lassen", "Abgenommen", "So abnehmen"), Symbole f4fc7efa/f60ca146 nach Owner-Wort; Probentabelle 1 bis 12 und A1 bis A7 mit Messung über DOM und Netzwerk |
| 10 | Audit Security/Bugs/Performance, Befunde vor Abschluss behandelt | PASSED (override) | `32-AUDIT.md`: 0 CRITICAL, 0 HIGH; M-32-01 gefixt (d09e5a5a, Regression ProviderTest und Korpus), L-32-02/L-32-06 gefixt (4c481f74), fünf LOW entschieden. M-32-02 offen als Owner-Frage, außerhalb des Phasenziels (siehe Override und "Bekannte Lücke") |
| 11 | Doku der Filter samt Grenzen | VERIFIED | `docs/search-filters.md:62-145` ("In the unified search"): Unterordner, Recheck, Ordner nie im Container, D-32-01, D-32-02, Abbruch, ignorierte Werte, umbenannter Ordner, Array-Form, Tür ohne Ordner; `CHANGELOG.md:22`; Store-Entwurf `docs/store-listing.md:2193` (Abnahme in Phase 36) |

**Score:** 11/11 Wahrheiten verifiziert (davon 1 per Override)

### Bewusste Abweichungen von Plan-Wahrheiten (dokumentiert, kein Befund)

- 32-04 nannte `searchFrom: 'findling'` und "Wurzel sendet keinen folder-Wert". Mit dem Fix von Befund A (4d616071, Owner-Entscheid A1) fragen die Chips den versteckten Provider `findling-filter`, und die Wurzel sendet `folder=/`, das `folderOf()` als keine Einschränkung liest. Beides in `32-07-ABNAHME.md` ("Befund A Fix") und `docs/search-filters.md` beschrieben, CI-Probe "chip-root: HTTP 200 and the ids of the unfiltered search".
- Abgebrochene Ordnerauswahl: der Chip bleibt stehen und zeigt keine Treffer (kein Parameter, also kein Filterwert im Sinne von SC3). Vom Owner am 13.10.2026 abgenommen ("leerer Chip nach Abbruch"), dokumentiert.

### Zurückgestellte Punkte

| # | Punkt | Adressiert in | Beleg |
|---|---|---|---|
| 1 | Owner-Abnahme des Store-Satzes Teil Phase 32, danach info.xml und READMEs | Phase 36 | SC3 von Phase 36, REL-05; Entwurf `docs/store-listing.md:2193` trägt "Owner-Abnahme offen" |
| 2 | L-32-04 (LOW-accept, externe Speicher ohne Groß/Klein-Unterscheidung) | Phase 36 | Zielphase laut `32-AUDIT.md` |

### Bekannte Lücke außerhalb des Phasenziels

**M-32-02 (MEDIUM, Owner-Frage):** Dokumente eines gelöschten Nutzers oder abgeschalteten Mounts bleiben im Index (`backend/src/findling/worker/reconcile.py` läuft nur die gelisteten Mounts). Nie ein Fremdtreffer (Vorauswahl und Recheck verwerfen sie), aber sie belegen Kandidatenplätze, im Ordnermodus bis Rang 1200. Ursache älter als Phase 32, Fix nur in `backend/src` (in dieser Phase gesperrt). Keine spätere Phase nennt das Aufräumen verwaister Storages ausdrücklich; der Owner entscheidet über Zielplan (Phase 36 oder Einschub) und Karenz. Kein Einfluss auf SC1 bis SC3.

### Erforderliche Artefakte

| Artefakt | Erwartet | Status | Details |
|---|---|---|---|
| `php/lib/Search/Provider.php` | Filter `types` und `folder`, Parser, fail-open | VERIFIED | 626 Zeilen, verdrahtet in `Application.php:55` |
| `php/lib/Search/FilterProvider.php` | versteckter Chip-Provider | VERIFIED | 119 Zeilen, `Application.php:59`, entscheidet nichts über Rechte (Audit-Quelltextprobe) |
| `php/lib/Service/SearchFilters.php` | `TYPES`, `typesFrom()`, Feld `folder` | VERIFIED | 217 Zeilen, von Provider und PageController genutzt |
| `php/lib/Service/SearchService.php` | `scopeOf()`, Koordinaten, Recheck im Unterbaum, Budget | VERIFIED | 818 Zeilen |
| `php/lib/Listener/LoadUnifiedSearchFiltersListener.php` | Skript auf angemeldeten Seiten | VERIFIED | `Application.php:135` |
| `php/js/unified-search.js` | sieben Einträge, Ordnerauswahl | VERIFIED | 299 Zeilen, kein DOM-Schreibzugriff, kein Netz (Audit S3) |
| `php/l10n/*` | 16 Kataloge | VERIFIED | je vier Schlüssel |
| `.github/workflows/deploy-harp.yml` Schritt Unified-Search-Filter | E2E 33/34/35/arm64 | VERIFIED | Lauf 38385966780 |
| `scripts/ci/team_folder_acl.sh` | Gruppenordner, ACL, Share mit `folder` | VERIFIED | 548 Zeilen, Integration 38385966737 |
| `docs/search-filters.md` | Doku samt Grenzen | VERIFIED | 152 Zeilen |
| `backend/tests/test_phase32_audit.py` | Korpus und Quelltextproben | VERIFIED | 9 Quelltextproben lokal grün, 128 Instanzproben ohne Instanz übersprungen (Lauf gegen 8090 im Audit belegt) |

### Key-Link-Verifikation

| Von | Nach | Über | Status | Details |
|---|---|---|---|---|
| Menüeintrag Typ | `findling-filter` | `searchFrom` + `filterParams.types` | WIRED | CI "chip-pdf", Browser A2 |
| Menüeintrag Ordner | `findling-filter` | Filepicker -> `filterParams.folder` | WIRED | CI "chip-folder", Browser A3 |
| `FilterProvider::search` | `Provider::search` | unveränderte Argumente | WIRED | Audit G5-Gegenprobe rot bei `clone` |
| `Provider::typesOf` | Container `/search` | `SearchFilters->types` -> `ExAppService` `types` | WIRED | CI pdf/text |
| `Provider::folderOf` | Recheck im Unterbaum | `SearchService::scopeOf` -> `readableFile($scope)` | WIRED | CI folder/inner, team-folder-acl |
| Tür "Alle Treffer anzeigen" | Ergebnisseite | `types` in `linkToRoute` | WIRED | `ProviderTest::testTheEntryPointCarriesTheActiveTypeGroupsIntoThePage`, Browser Probe 10 |

### Datenfluss (Level 4)

| Artefakt | Datenvariable | Quelle | Echte Daten | Status |
|---|---|---|---|---|
| Findling-Gruppe mit Typ-Chip | `.ocs.data.entries` | OCS gegen NC 33/34/35/arm64 mit HaRP | ja, Saat-ID 37 | FLOWING |
| Findling-Gruppe mit Ordner-Chip | `.ocs.data.entries` | dito, plus groupfolders mit ACL | ja, Saat-IDs 35 36 37 bzw. 50/51/56/59 | FLOWING |

### Verhaltens-Stichproben

| Verhalten | Befehl | Ergebnis | Status |
|---|---|---|---|
| Phasen-Tests lokal | `PYTHONUTF8=1 uv run python -m pytest -q -p no:randomly tests/test_phase32_audit.py tests/test_unified_search_plugin.py tests/test_unified_search_filter_steps.py tests/test_php_acl_boundary.py tests/test_type_vocabulary_parity.py tests/test_search_endpoint.py tests/test_snippets_endpoint.py` | 151 passed, 128 skipped (Instanzproben), 21 s | PASS |
| Skript-Syntax | `node --check php/js/unified-search.js` | ok | PASS |
| PHPUnit in CI | `gh run view 38385967900 --log` | "OK (666 tests, 2456 assertions)" | PASS |
| Volle Python-Suite in CI | `gh run view 38385966880 --log` | "5649 passed, 146 skipped" | PASS |

### CI-Belege (selbst per `gh run view` geprüft)

| Lauf | Workflow | Commit | Ergebnis |
|---|---|---|---|
| 38385966780 | HaRP deploy (stable33, stable34, stable35, stable34 arm64) | 4c481f74 | success |
| 38385966737 | Integration (inkl. team-folder-acl, search-parity) | 4c481f74 | success |
| 38385967900 | PHP and store metadata gates | 4c481f74 | success, 666 Tests |
| 38385966880 | Python gates | 4c481f74 | success, 5649 passed |
| 38385966954 | Multi-arch image | 4c481f74 | success |
| 38385967215 | Resilience | 4c481f74 | success |
| 38389429937 | Security scans | 46161352 (HEAD) | success |
| 38389429964 | OpenSSF Scorecard | 46161352 (HEAD) | success |

### Probe-Ausführung

Keine `scripts/*/tests/probe-*.sh` in den Plänen deklariert. Die E2E-Proben laufen in deploy-harp und Integration; ihre Ergebnisse sind oben aus den Logs zitiert, nicht aus einer SUMMARY.

### Anforderungsabdeckung

| Anforderung | Plan | Beschreibung | Status | Beleg |
|---|---|---|---|---|
| USRCH-01 | 32-01, 32-04, 32-05, 32-06, 32-07, 32-08 | Typfilter in der Unified Search | SATISFIED | Wahrheit 1, 4, 7, 8, 9 |
| USRCH-02 | 32-02, 32-03, 32-04, 32-05, 32-06, 32-07, 32-08 | Ordnerfilter inkl. Unterordner, Recheck bleibt Grenze | SATISFIED | Wahrheit 2, 5, 6, 8, 9 |
| USRCH-03 | 32-01, 32-02, 32-06, 32-08 | unbekannte/leere Werte ignoriert, Regressionstest | SATISFIED | Wahrheit 3 |

Verwaiste Anforderungen: keine. REQUIREMENTS.md ordnet Phase 32 genau USRCH-01 bis USRCH-03 zu, alle von Plänen beansprucht.

### Gefundene Anti-Muster

| Datei | Zeile | Muster | Schwere | Wirkung |
|---|---|---|---|---|
| (54 seit a632a35c geänderte Dateien unter `php`, `scripts`, `docs` ohne Messrohdaten, `.github`, `backend/tests`, README, CHANGELOG, THIRD-PARTY, REUSE) | | `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, `PLACEHOLDER` | | keine Treffer |
| Phasen-Diff a632a35c..HEAD | | U+2013/U+2014 in hinzugefügten Zeilen | | 0 |

### Menschliche Prüfung

Keine offen. Die gemeinsame Playwright-Abnahme ist erfolgt (32-07). Offen bleibt nur die Owner-Entscheidung zu M-32-02 (Zielplan, Karenz); sie betrifft das Phasenziel nicht.

### Zusammenfassung

Alle drei Erfolgskriterien sind im Code vorhanden, in PHPUnit und pytest als Regression abgesichert und auf echten Nextcloud-Installationen (33, 34, 35, arm64, dazu groupfolders mit ACL und empfangener Share) Ende zu Ende belegt. Die Rechtegrenze ist unverändert eine Auflösung und eine Lesefrage im ganzen PHP-Baum; der Ordner verlässt PHP nie, `backend/src` ist in der Phase nicht berührt. Der Owner hat Verhalten, Wortlaut und Symbole gemeinsam per Playwright abgenommen. Das Audit endet ohne CRITICAL und HIGH; M-32-01 ist gefixt. M-32-02 ist eine ältere Grenze des Abgleichs außerhalb des Phasenziels und bleibt als Owner-Frage offen.

---

_Verifiziert: 2026-10-13T11:25:53Z_
_Verifier: Claude (gsd-verifier)_
