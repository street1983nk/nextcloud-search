---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 04
subsystem: backend/api
tags: [coverage, issue-25, d-43-07, d-43-09, d-43-11, d-43-14, route]
requires:
  - 43-03 (coverage_counts, CoverageCounts, coverage_topology.json)
  - 43-16 (note_coverage_call, doc_keys_corrected, Store.doc_keys_missing/doc_keys_unresolved)
provides:
  - "POST /coverage, Body {mounted: [int], groups: [[int]]}, ADMIN in backend/appinfo/info.xml"
  - "Antwort {documents, embeddedDocuments, judgedDocuments, documentsByGroup, judgedByGroup, documentsByStorage, judgedByStorage, counting, docKeysMissing, docKeysUnresolved, docKeysCorrected}"
  - "api/coverage.py: COVERAGE_MAX_MOUNTED = 50_000, COVERAGE_MAX_MEMBERS = 1000, COVERAGE_MAX_ID = 10**18 - 1, COVERAGE_SYNC_CEILING = 100_000, COVERAGE_CACHE_SECONDS = 300, COVERAGE_CACHE_KEYS = 4"
  - "Store.living_rows_in_storages(storage_ids)"
affects:
  - 43-05 (PHP adminSend('/coverage'), Validierung, Fallback)
tech-stack:
  added: []
  patterns:
    - "pydantic strict + extra=forbid + model_validator: 422 vor jeder Datenbank"
    - "Single-Flight-Hintergrundzählung mit LRU-Cache, Schlüssel sha256 der kanonischen Anfrage, Stock-Identität beider DBs (Muster status.py left out)"
key-files:
  created:
    - backend/src/findling/api/coverage.py
    - backend/tests/test_coverage_endpoint.py
  modified:
    - backend/src/findling/main.py
    - backend/src/findling/store/repo.py
    - backend/appinfo/info.xml
    - backend/tests/test_store_repo.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_exapp_surface.py
    - backend/tests/test_semantic_boundary.py
    - backend/tests/test_probe_endpoint.py
decisions:
  - "docKeysMissing = alle lebenden Zeilen ohne Schlüssel im ganzen Bestand (Fortschritt des Backfills); ob die Zahl wartet, sagt allein counting (true, sobald ein Gruppenmitglied ohne Schlüssel lebt); ein Einzelspeicher ohne Schlüssel hält nichts auf"
  - "Der Cache rechnet in kanonischer Gruppenreihenfolge (sortierte Gruppen) und ordnet ByGroup danach in die Reihenfolge der Anfrage zurück; so trifft eine umsortierte Anfrage denselben Eintrag und bekommt trotzdem ihre Reihenfolge"
  - "Fehlende state.db (frisches Volume) = Nullen mit counting=false; unlesbare state.db oder Fehler der Zählung in der Anfrage = 503 detail 'unavailable', Logzeile nur mit Klassenname"
  - "note_coverage_call() läuft bei jedem Aufruf, der den Handler erreicht; ein 422 erreicht ihn nicht"
  - "Ein Treffer im Cache rückt den Schlüssel nach hinten (LRU auch beim Lesen)"
metrics:
  duration: "ca. 70 min (davon ca. 19 min Volltestsuite)"
  completed: 2026-11-07
  tasks: 2
  files: 10
---

# Phase 43 Plan 04: Route POST /coverage Summary

Der Container beantwortet jetzt `POST /coverage` mit der Zählung pro Dokument aus 43-03 für die Mountliste und die Freigabegruppen der Companion, nur Zahlen, Speicher-IDs, ein Bool und null; bis 100.000 lebende Zeilen synchron, darüber im Hintergrund mit Single-Flight und Cache.

## Umsetzung

- **Modell** `CoverageRequest`: `ConfigDict(extra="forbid", strict=True)`, `mounted: list[StorageId]` mit `max_length=50_000`, `groups: list[list[StorageId]]`, `StorageId = Annotated[int, Field(ge=1, le=10**18 - 1)]`; Validator: höchstens 1000 Mitglieder gesamt, Gruppen disjunkt, jedes Mitglied in mounted. Strict lehnt String, Bool und Float ab. Gruppen mit weniger als zwei Mitgliedern verwirft `_kept_groups`, ihr Mitglied zählt als Einzelspeicher.
- **Ablauf** `_answer` (in `asyncio.to_thread`): keine state.db -> Nullen; sonst `open_read_only`, `living_rows_in_storages(mounted)`, `doc_keys_missing()`, `doc_keys_unresolved()`; bis `COVERAGE_SYNC_CEILING` direkt `coverage_counts`, darüber `_cached`. `answer_of` baut die Antwort Feld für Feld; counting=true mit null-Feldern, solange keine Zahl da ist oder `CoverageCounts.doc_keys_missing > 0` (D-43-14).
- **Hintergrund**: `_COVERAGE_LOCK`, `_COVERAGE_REFRESH`, `_COVERAGE_CACHE` (OrderedDict, 4 Schlüssel), Eintrag = (Zählung in kanonischer Reihenfolge, Ende der Zählung, Stock-Identität). Stock = ((Pfad, st_dev, st_ino) der state.db, dasselbe der vectors.db oder None). TTL 300 s ab Zählende, veralteter Eintrag wird beantwortet und startet die nächste Zählung. RuntimeError beim Start setzt das Flag zurück; Fehler im Thread: Logzeile mit Klassenname, kein Eintrag. Testhelfer `join_coverage_refresh`, `cached_keys`, `_reset_coverage_cache_for_tests`.
- **Store**: `living_rows_in_storages` (eine Abfrage über `json_each(?)`, `INDEXED BY files_storage`, Tombstones und IDs < 1 draußen), mit Test.
- **Einbindung**: `COVERAGE_ROUTER` in main.py; info.xml-Block nach `/probe/state` mit englischem Kommentar (Zweck, nur Zahlen, warum POST, ADMIN), Kopfkommentar "Six routes" / "these six".

## TDD

- RED 0306b4a7: Sammelfehler (Modul `findling.api.coverage` fehlt).
- GREEN a5a95585: tests/test_coverage_endpoint.py 39 passed. Topologie über die Route gleich expected; 14 ungültige Bodies je 422 ohne Aufruf von `coverage_counts`/`open_read_only` (50.001 mounted, 1001 Mitglieder, 0, -5, 10**18, "5", true, 5.0, überlappend, Mitglied nicht eingebunden, Zusatzfeld, fehlende groups, falsche Form, Liste statt Objekt); größter erlaubter Body (50.000 mounted, 1000 Mitglieder) und größte ID 200; Hintergrund mit Schwelle 5; Single-Flight über drei Anfragen; Schlüssel unabhängig von der Reihenfolge; ersetzte state.db verwirft den Cache; fünfter Schlüssel verdrängt den ältesten; veralteter Eintrag beantwortet und neu gezählt; Fehler im Thread ohne Pfad im Log und neuer Versuch; NULL-Schlüssel eines Mitglieds -> counting; NULL eines Einzelspeichers -> keine Sperre; note_coverage_call je Aufruf; docKeysCorrected durchgereicht; frisches Volume Nullen; kaputte state.db 503 ohne Pfad; Deklaration POST/ADMIN; Route gemountet; /status?leaveOut= unverändert.
- Antwortgröße (W-d): 50.000 Einzelspeicher mit je zwei Paaren, 1.400.238 Bytes, Aufbau und Serialisierung 0,067 s.

## Gates und Tests

- ruff check: All checks passed; ruff format --check: 253 files already formatted; pyright (latest): 0 errors; vulture: leer.
- Verify-Satz plus Nachbarn (coverage_endpoint, coverage_counts, status_leave_out, status_endpoint, diagnose_endpoint, measurement_scripts, store_repo, exapp_surface, semantic_boundary, probe_endpoint, info_xml_defaults, doc_keys, main_lifespan): 1146 passed nach dem Nachziehen von test_probe_endpoint.
- Volltestsuite mit den --ignore aus 40-01 (2,9 GB frei): `test_[a-m]*` 3334 passed, 43 skipped; `test_[n-r]*` 1982 passed, 278 skipped; `test_[s-z]*` 1567 passed, 10 skipped.
- Baumhash PACKAGE: 82 -> 83 Dateien, cdd2a8e2... -> d7627c127f60da58a3e1eec42043f979f30245f991b79d98ef2198a84cde4994. Zweimal gerechnet: Rezept 40b-baumhash.py und unabhängig `find | LC_ALL=C sort | tr -d '\r' | sha256sum`, beide d7627c12; Positivkontrolle über `git archive HEAD` vor dem Schritt: cdd2a8e2. PHP-Paare unberührt. info.xml ist nicht im Rezept; geprüft über test_exapp_surface, test_probe_endpoint, test_info_xml_defaults und die Volltestsuite.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Routentabellen der Nachbartests (nicht in files_modified)**
- `tests/test_exapp_surface.py` EXPECTED_ROUTES um `("^/coverage$", "POST", "ADMIN", "[]", "[401]")` ergänzt (Docstring "six routes").
- `tests/test_semantic_boundary.py` KNOWN_ROUTES um `/coverage` ergänzt (Ratsche laut Kommentar).
- `tests/test_probe_endpoint.py::test_each_probe_route_is_declared_once`: `<route>`-Zahl 5 -> 6, Kopfkommentar der info.xml "Five routes"/"these five" -> "Six routes"/"these six", die alten Zahlen als Negativprüfung.

**2. Erweiterung der Antwort**
- Statt der acht Schlüssel der must_haves trägt die Antwort elf (`docKeysMissing`, `docKeysUnresolved`, `docKeysCorrected` aus dem Action-Text); der Test prüft genau diese elf.

**3. Form**
- `ByStorage` als Paare `[storageId, Zahl]`, aufsteigend nach ID, nur Werte > 0; `ByGroup` immer eine Zahl je behaltener Gruppe.
- Neue Store-Funktion `living_rows_in_storages`, weil keine bestehende alle Urteile über beliebig viele Speicher in einer Abfrage zählt (`indexed_in_storages` zählt nur indexed und in Bändern zu 500).

## Hinweis für 43-05 (Befund, nicht hier behoben)

- `ExAppService::MAX_BODY_BYTES = 1048576` (1 MiB). Die Antwort für 50.000 Einzelspeicher mit Dokumenten ist 1,40 MB und würde dort als `refused` abgelehnt. Ab grob 37.000 Einzelspeichern mit Dokumenten fällt die Seite damit auf den heutigen Weg zurück. 43-05 muss das entscheiden (eigene Obergrenze für /coverage oder Fallback sichtbar machen).
- `docKeysMissing` ist global; PHP soll für "wird gezählt" nur `counting` lesen.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: endpoint | backend/src/findling/api/coverage.py | neue ADMIN-Route POST /coverage, im Plan als T-43-10 bis T-43-13 erfasst; Body begrenzt, Antwort nur Zahlen |

## Known Stubs

Keine.

## Self-Check: PASSED

- backend/src/findling/api/coverage.py und backend/tests/test_coverage_endpoint.py vorhanden; `@ROUTER.post("/coverage")`, `<url>^/coverage$</url>`, `COVERAGE_ROUTER` gefunden.
- Commits 0306b4a7 (test) und a5a95585 (feat) im Log, Autor street1983nk <k.cherif@outlook.de>, kein Trailer, 0 Treffer für closes/fixes/resolves #N, keine Löschungen.
