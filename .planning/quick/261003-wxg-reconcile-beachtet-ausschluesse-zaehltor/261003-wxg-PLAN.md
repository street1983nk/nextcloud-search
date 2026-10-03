---
phase: quick-261003-wxg
plan: 01
type: tdd
wave: 1
depends_on: []
files_modified:
  - backend/src/findling/worker/reconcile.py
  - backend/tests/test_reconcile.py
  - php/lib/Service/StorageService.php
  - php/lib/Controller/ReconcileController.php
  - php/tests/Unit/ReconcileControllerTest.php
  - backend/tests/test_exclusion_path_space.py
  - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
  - backend/tests/test_v14_zelle.py
autonomous: true
requirements: [IDX-04, D-06, T-28-03]
must_haves:
  truths:
    - "Eine Datei, die eine Ausschlussregel von HEUTE trifft und die der Container nicht kennt (unbekannt oder Grabstein), wird vom Reconcile nicht mehr als content-Arbeit eingeplant, in keiner Runde (Lauf-7-Befund: 549 Dateien alle ~300 s)"
    - "Die Ausschluss-Entscheidung fällt ausschließlich in der PHP-Hälfte über ExclusionService::isExcluded auf dem einen Pfadraum (mountRelativePath); der Container trägt keine Präfixliste und keinen Präfixvergleich (D-06)"
    - "Eine AUFGEHOBENE Ausschlussregel macht die Dateien in der nächsten Reconcile-Runde wieder zu content-Arbeit: der Container persistiert für excluded kein Urteil, die Seite trägt nach der Aufhebung kein skipped(excluded) mehr"
    - "Eine geänderte Datei (neue etag), die der Container bereits mit anderer etag kennt, bleibt content-Arbeit, auch wenn sie ausgeschlossen ist; describe() antwortet dafür weiter mit dem Löschauftrag (CR-01 bleibt erhalten)"
    - "Eine Runde, deren Seiten nur ausgeschlossene unbekannte Dateien tragen, läuft durch (ROUND_WALKED, stale 0) und schließt den Mount ab, statt am eigenen Schub an der Ruhemarke zu scheitern"
    - "Das Zaehltor in 10-zelle.sh zählt den Vorrat (oc_findling_queue) nur für Dateien unter files/teilkorpus; die Lauf-7-Zahlen (global 549, Teilkorpus 0, eingebettet 5000) ergeben summe 5000 statt 5549"
    - "Ein echtes Defizit im Teilkorpus führt weiter zu Abbruch 71; ein unlesbarer Vorrat ebenso"
  artifacts:
    - path: "backend/src/findling/worker/reconcile.py"
      provides: "excluded-Zweig in _compare, Konstanten EXCLUDED_STATE/EXCLUDED_REASON"
      contains: "EXCLUDED_REASON"
    - path: "php/lib/Controller/ReconcileController.php"
      provides: "filesSlice markiert ausgeschlossene Zeilen als skipped(excluded), live aus den Regeln von heute"
      contains: "isExcluded"
    - path: "php/lib/Service/StorageService.php"
      provides: "getFileSlice mit optionalem Ausschluss-Prädikat auf dem internen Pfad"
      contains: "getFileSlice"
    - path: "php/tests/Unit/ReconcileControllerTest.php"
      provides: "PHPUnit für die Markierung (CI-Vorbehalt)"
    - path: "docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh"
      provides: "teilkorpus-scharfer Vorrat am Zaehltor via psql"
      contains: "findling_queue"
  key_links:
    - from: "php/lib/Controller/ReconcileController.php"
      to: "ExclusionService::isExcluded + mountRelativePath"
      via: "Prädikat pro Zeile der Seite, mountRootPath einmal pro Seite"
      pattern: "mountRelativePath"
    - from: "backend/src/findling/worker/reconcile.py"
      to: "FileRow.state/reason der Seite"
      via: "stored is None and skipped(excluded) -> keine Arbeit, kein store-Schreiben"
      pattern: "EXCLUDED_STATE"
    - from: "docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh"
      to: "nextcloud-aio-database (psql)"
      via: "db_lesen, oc_findling_queue JOIN oc_filecache, path like 'files/teilkorpus/%'"
      pattern: "findling_queue"
---

<objective>
Owner-Entscheid 03.10.2026, Teil a + b (LOCKED).

Teil a, Produkt-Fix: Der Container-Reconcile plant ausgeschlossene Dateien nicht mehr endlos neu ein.
Mechanik (aus Code gelesen, Lauf 7 dreifach belegt): Der Reconcile bekommt über
`/files/slice` jede Datei des Mounts, auch ausgeschlossene (getFileSlice filtert bewusst nicht,
sonst würde eine kurze Seite als final gelten und Löschungen auslösen). `_compare` hält jede Datei
ohne gespeicherte etag für Arbeit (`known_etags` blendet Grabsteine aus). QueueService::describe
erkennt den Ausschluss erst beim Claim und antwortet mit KIND_DELETE, der Poller vergisst die Datei
(Grabstein), und die nächste ruhige Runde findet sie wieder ohne etag. Da der eigene Schub die
Ruhemarke reißt, bleibt die Runde unfinished und `_is_due` ist sofort wieder wahr: Schub alle ~300 s,
dauerhaft, bei jedem Admin mit Ausschlussregeln.

Gewählter Schnitt (Planner-Entscheid, Kandidat 2 des Owner-Entscheids, gleiche Wirkung wie Kandidat 1
ohne dessen heiklen Punkt): Die PHP-Hälfte markiert im Rückkanal, den es seit Plan 05-03 gibt
(FileRow.state/reason, `withVerdicts`), jede Zeile, die eine Regel von HEUTE trifft, live als
`skipped(excluded)`. Der Container plant eine solche Zeile nicht ein, solange er die Datei nicht
kennt, und schreibt dafür NICHTS in seine files-Tabelle. Begründung gegen Kandidat 1 (persistiertes
Urteil samt etag): ein in `files` gespeichertes skipped(excluded) mit passender etag würde nach einer
Regelaufhebung über den Zweig `stored == row.etag` weiter als erledigt gelten, die Datei bliebe für
immer aus dem Index. Das Live-Urteil hängt an der Version, die die Seite gerade trägt, und
verschwindet mit der Regel; das ist dieselbe Linie wie ExclusionService ("no row per excluded file
... works the reason out live") und die Diagnose (AdminViewService arbeitet excluded live heraus).
Kein Doppel-Regelwerk im Container: die Präfixe bleiben in der PHP-Hälfte (D-06), der Container liest
nur zwei Codes vom Draht.

Teil b, Werkzeug: Das Zaehltor in 10-zelle.sh zählt auch den Vorrat teilkorpus-scharf (nur
`files/teilkorpus/%`), gleiche Linie wie Quick 261002-cvf.

Output: drei atomare, lokal committete Commits (kein Push, den macht der Orchestrator).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@backend/src/findling/worker/reconcile.py
@docs/measurements/2026-10-abnahme-anfahrt/rohdaten/05-typwechsel-arm.txt
@.planning/quick/261002-cvf-zaehltor-teilkorpus-scharfe-zaehlquelle/261002-cvf-PLAN.md

<interfaces>
Aus backend/src/findling/worker/reconcile.py (Ist-Stand):
- `GIVEN_UP_STATE = "failed"`, `GIVEN_UP_REASON = "repeatedly_stuck"`, `HANDOVER_STATE = "skipped"`, `HANDOVER_REASON = "no_text_layer"`: Draht-Codes bewusst ausgeschrieben, nicht aus findling.extract.errors importiert (Kommentar Zeilen 73-104).
- `Reconcile._compare(store, mount, rows) -> tuple[list[int], int]`, Zweigfolge: stranded handover -> `stored == row.etag: continue` -> `stored is None and written_off: store.give_up(...)` -> `stale.append`.
- `__all__` listet die Draht-Konstanten.

Aus backend/src/findling/nc/files.py:
- `FileRow(file_id, etag, size, mtime, mime, state="", reason="")`, `state`/`reason` kommen aus `fields.get("state")`/`"reason"` als Strings.

Aus backend/src/findling/store/repo.py:
- `Store.known_etags(file_ids) -> dict[int, str | None]` (nur `deleted_at IS NULL`, Grabsteine fehlen im Ergebnis)
- `Store.tombstone(file_id, at=None) -> int`, `Store.file_row(file_id)`, `STATE_REASONS` enthält `"excluded"` unter skipped (Zeile ~273).
- `findling.extract.errors.Reason.EXCLUDED = "excluded"`.

Aus backend/tests/test_reconcile.py:
- Helfer `a_file(file_id, *, etag) -> FileMeta`, `a_row(file_id, *, etag, state="", reason="")`, `a_given_up_row`, `_FakeQueue` (`kinds_of(kind)`, `requeues`), `_FakeFiles(*pages)`, `_reconcile(store, files, queue, *, now=NOW, slice_size=2)`, Konstanten `NOW`, `HOUR`, Fixture `store`.
- Muster für Zwei-Zyklen-Tests: `test_a_file_nextcloud_gave_up_on_is_not_requeued_by_two_cycles` (Zeile 225).
- Quelltexttest `test_the_slice_route_hands_the_verdict_over_with_the_page` liest `PHP_RECONCILE_CONTROLLER` über `_php_source`.

Aus php/lib/Controller/ReconcileController.php:
- `__construct(IRequest $request, private StorageService $storageService, private FileStateService $fileStateService, private LoggerInterface $logger)`
- `filesSlice(int $storage = 0, int $root = 0, int $after = 0, int $limit = self::DEFAULT_SLICE)`: `getFileSlice` -> `withVerdicts` -> `final = count < size`.
- `private function withVerdicts(array $files): array`: `$row + $verdict` (Linksvorrang des Array-Union).

Aus php/lib/Service/StorageService.php:
- `getFileSlice(int $storageId, int $overriddenRoot, int $lastFileId, int $batchSize): array` (Zeile 405), projiziert `getFilesInMount` auf fileId/etag/size/mtime/mime.
- `mountRootPath(int $storageId, int $overriddenRoot): string`.
- StorageService darf ExclusionService NICHT injizieren (ExclusionService hängt an StorageService, Zyklus).

Aus php/lib/Service/ExclusionService.php (final class):
- `prefixes(): array`, `isExcluded(string $mountRelativePath): bool`, `mountRelativePath(string $internalPath, string $rootInternalPath): string`.
- Konstruktor `(IAppConfig, StorageService, IJobList, LoggerInterface)`; prefixes liest `IAppConfig::getValueArray(APP_ID, SettingsService::KEY_EXCLUSIONS, [])`.
- Muster der Crawl-Aufrufstelle: `isExcluded(mountRelativePath($entry->getPath(), $mountRoot))` mit `$mountRoot = mountRootPath($storageId, $overriddenRoot)` (StorageCrawlJob Zeilen 254, 477-481).

Aus php/tests/Unit/QueueServiceTest.php (Zeile ~225): ExclusionService ist final und wird in Tests echt über gemockte IAppConfig/StorageService/IJobList/LoggerInterface gebaut.
Aus php/tests/Unit/QueueControllerTest.php (Zeile ~58): IRequest-Mock beantwortet `getHeader('EX-APP-ID')`.

Aus backend/tests/test_exclusion_path_space.py:
- Konstanten `CRAWL`, `LISTENER`, `STORAGE_SERVICE`, `QUEUE_SERVICE`, `EXCLUSION_SERVICE`, `HELPER_CALL`, `PATH_SPACE_CALL`, `PREFIX_COMPARISONS`, Helfer `statements(source)`; Muster `test_the_reconcile_requeue_path_consults_the_helper` (Zeile 332); Anti-Vakuum-Test `test_the_four_files_of_the_exclusion_exist`.

Aus docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh:
- `db_lesen "<sql>"` (psql -At im DB-Container, Fehler -> `unlesbar`), `${DB_PREFIX}`, `ist_zahl`, `vorrat_von <datei>` (summiert scheduled + handed aus `occ findling:index`).
- Zaehltor-Block Zeilen ~584-652: Doppellesung von embedded um `bestand_lesen` + frisch-Query, danach `vorrat=$(vorrat_von "$WORK/bestand.txt")`, Zeile `zaehlung vorrat ... summe $summe`, `abbruch 71`.
- Der Ende-Schritt (Zeilen ~654-685) nutzt den globalen Vorrat und bleibt UNVERÄNDERT (nicht erbeten).

Aus backend/tests/test_v14_zelle.py:
- `STUB_DOCKER` (Zeile 405): DB-Zweig `*nextcloud-aio-database*` beantwortet `*"max(updated_at)"*` und `*"group by s.state"*`; occ-Zweig liefert `Work stock` aus `STUB_SCHEDULED`/`STUB_HANDED` nur bei der ersten Lesung nach dem Trigger.
- Belegtests `test_cell_teilkorpus_passes_with_the_counters_of_run_5`, `..._old_states_mask_no_real_shortfall`, `ABORT_71_COUNTERS`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Reconcile lässt live ausgeschlossene, unbekannte Dateien liegen (Python, TDD)</name>
  <files>backend/tests/test_reconcile.py, backend/src/findling/worker/reconcile.py</files>
  <behavior>
    - Test A (Lauf-7-Form, zwei Zyklen nach dem Muster Zeile 225): eine Seite mit unbekannter Zeile 10 als skipped(excluded) und unbekannter Zeile 11 ohne Urteil. Runde 1: nur [11] als content, Zustand ROUND_WALKED, stale 1, given_up 0; `store.file_row(10)` ist None (kein persistiertes Urteil). Runde 2 bei NOW + 25 * HOUR mit derselben excluded-Zeile 10: keine Übergabe von 10.
    - Test B (Grabstein): `a_file(10, etag="aaa")` schreiben, `store.tombstone(10)`, Seite trägt 10 als skipped(excluded) mit etag "aaa": keine Übergabe, stale 0.
    - Test C (Regelaufhebung, der heikle Punkt): Runde 1 mit 10 als skipped(excluded) -> nichts; Runde 2 (NOW + 25 * HOUR) trägt 10 mit derselben etag ohne Urteil -> [10] als content.
    - Test D (CR-01 bleibt): `a_file(10, etag="aaa")` bekannt, Seite trägt 10 als skipped(excluded) mit etag "bbb" -> [10] als content (describe macht daraus den Löschauftrag).
    - Test E (Runde läuft durch): Seite nur mit excluded-Zeilen, final -> ROUND_WALKED, `queue.requeues == []`, eine zweite Runde innerhalb der Mindestpause liefert ROUND_NOT_DUE (der Mount ist abgeschlossen, kein Dauer-Takt mehr).
    - Test F (Vokabular): `(EXCLUDED_STATE, EXCLUDED_REASON) == ("skipped", "excluded")` und der Grund steht unter skipped in `findling.store.repo.STATE_REASONS` und in `findling.extract.errors.STATE_REASONS` (gleiche Haltung wie der Kommentar zu GIVEN_UP_*).
  </behavior>
  <action>
RED zuerst: Tests A bis F in backend/tests/test_reconcile.py anlegen (Helfer `a_excluded_row(file_id, *, etag)` analog `a_given_up_row`, Docstrings im Stil der Datei, englisch, Bezug Lauf 7 / Owner-Entscheid 03.10. a). Aus backend/ laufen lassen und den RED-Beleg (A, B, E, F rot wegen fehlender Konstanten bzw. Übergabe der excluded-Zeile; C und D dürfen schon grün sein, sie sind die Schutzgeländer) für das SUMMARY festhalten.

GREEN in backend/src/findling/worker/reconcile.py (per Owner-Entscheid a, Schnitt Kandidat 2):
- Neue Draht-Konstanten `EXCLUDED_STATE: Final = "skipped"` und `EXCLUDED_REASON: Final = "excluded"` neben GIVEN_UP_*/HANDOVER_*, mit Kommentarblock im Stil der Nachbarn: dieser Modul erkennt das Urteil nur, die Regel gehört der PHP-Hälfte (D-06), das Urteil ist live für die Version, die die Seite trägt, und wird darum nie in `files` geschrieben, weil ein gespeichertes Urteil eine Regelaufhebung über den Zweig `stored == row.etag` überleben würde. In `__all__` aufnehmen.
- In `_compare` nach `if stored == row.etag: continue` und VOR dem given-up-Zweig: wenn `stored is None` und die Zeile `EXCLUDED_STATE`/`EXCLUDED_REASON` trägt, `continue` (keine Arbeit, kein `store.give_up`, kein Zähler). Bekannte Dateien mit abweichender etag laufen unverändert in `stale` (CR-01-Hälfte: describe antwortet mit KIND_DELETE).
- Docstring von `_compare` um einen Absatz zur Ausschlussregel ergänzen (Lauf-7-Mechanik in zwei Sätzen: Grabstein durch describe/Löschauftrag, Wiederkehr in jeder ruhigen Runde, Runde blieb unfinished). Keinen Präfixvergleich, keine Pfade, keine Präfixliste im Container; der Log bleibt Zähler-only (T-03-1205). Keine neuen Felder in RoundResult (nicht erbeten).

Gates aus backend/: `uv run ruff check .`, `uv run ruff format --check .`, `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`, `uv run vulture src tests --min-confidence 80`, alle grün. Commit (lokal, kein Push), Autor street1983nk, keine Claude-Trailer: `fix(reconcile): leave files excluded by today's rules alone instead of requeueing them every round`.
  </action>
  <verify>
    <automated>cd backend && PYTHONUTF8=1 uv run pytest tests/test_reconcile.py tests/test_extract_errors.py -q</automated>
  </verify>
  <done>RED-Lauf belegt, danach grün; reconcile.py enthält EXCLUDED_STATE/EXCLUDED_REASON und keinen Präfixvergleich (`grep -v '^\s*#' backend/src/findling/worker/reconcile.py | grep -c "startswith"` bleibt beim Ist-Wert); ruff, format, pyright (latest), vulture grün; Commit lokal.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: PHP-Hälfte markiert ausgeschlossene Zeilen der Seite live als skipped(excluded)</name>
  <files>php/lib/Service/StorageService.php, php/lib/Controller/ReconcileController.php, php/tests/Unit/ReconcileControllerTest.php, backend/tests/test_exclusion_path_space.py, backend/tests/test_reconcile.py</files>
  <behavior>
    - Gate (Python, lokal lauffähig, RED zuerst): ReconcileController.php ist eine vierte Aufrufstelle der Ausschlussregel: ruft `isExcluded` UND `mountRelativePath`, keinen Eintrag aus PREFIX_COMPARISONS; die Datei steht im Anti-Vakuum-Test.
    - Quelltexttest in test_reconcile.py: ReconcileController.php trägt das Codepaar 'skipped'/'excluded' in der Markierung und `withVerdicts` bleibt bestehen.
    - PHPUnit (CI-Vorbehalt, lokal nicht lauffähig): ohne Präfixe trägt keine Zeile ein excluded-Urteil; mit Präfix `loadtest` trägt eine Zeile unter `files/loadtest/x.pdf` state skipped / reason excluded, eine Zeile unter `files/teilkorpus/y.pdf` nicht; die excluded-Zeile bleibt auf der Seite (nicht gefiltert, `final` unverändert); excluded hat Vorrang vor einem findling_file_state-Urteil derselben Datei; die Antwortzeilen tragen nur die sieben Drahtfelder.
  </behavior>
  <action>
RED zuerst: in backend/tests/test_exclusion_path_space.py eine Konstante `RECONCILE_CONTROLLER = PHP_ROOT / "Controller" / "ReconcileController.php"` mit Kommentar (vierte Aufrufstelle, Owner-Entscheid 03.10. a, Lauf 7) und einen Test `test_the_reconcile_slice_marks_excluded_rows_through_the_helper` nach dem Muster von `test_the_reconcile_requeue_path_consults_the_helper` anlegen; die Datei in `test_the_four_files_of_the_exclusion_exist` aufnehmen (Name des Tests unverändert lassen oder sachlich anpassen, Inhalt zählt). Dazu den Quelltexttest in test_reconcile.py neben `test_the_slice_route_hands_the_verdict_over_with_the_page`. RED-Beleg festhalten.

GREEN (per Owner-Entscheid a, Schnitt Kandidat 2, D-06):
- StorageService::getFileSlice bekommt einen optionalen fünften Parameter `?\Closure $isExcludedPath = null` (Signatur: interner Pfad -> bool). Ist er gesetzt, trägt jede Zeile zusätzlich `'excluded' => (bool)$isExcludedPath($entry->getPath())`. Kein Filter, kein Präfixvergleich in StorageService; Docblock um einen Absatz ergänzen (warum markieren statt filtern: final-Marke und Löschregel, siehe bestehender Absatz; warum ein Prädikat: ExclusionService hängt an StorageService, Injektion wäre ein Zyklus). Rückgabetyp im Docblock um `excluded?: bool` ergänzen.
- ReconcileController: ExclusionService per Konstruktor injizieren. In filesSlice nur wenn `$this->exclusionService->prefixes() !== []` (keine Kosten ohne Regeln, wie Listener und describe): `$mountRoot = $this->storageService->mountRootPath($storage, $root)` einmal pro Seite und ein Closure, das `$this->exclusionService->isExcluded($this->exclusionService->mountRelativePath($path, $mountRoot))` beantwortet, an getFileSlice reichen. In withVerdicts: Zeile mit `excluded === true` bekommt state `skipped` / reason `excluded` (zwei private Konstanten mit Kommentar: Codes der geschlossenen Liste FileStateService::REASONS, live und nie in findling_file_state geschrieben, damit eine Regelaufhebung sofort wirkt), sonst wie bisher das findling_file_state-Urteil; den Schlüssel `excluded` vor der Antwort entfernen, damit der Draht bei sieben Feldern bleibt. Klassen-Docblock und filesSlice-Docblock um den Satz zum excluded-Urteil ergänzen; keine Pfade, Präfixe oder Namen in den Log (T-03-1102).
- Neue Datei php/tests/Unit/ReconcileControllerTest.php nach dem Muster von QueueControllerTest (IRequest-Mock mit `EX-APP-ID` = findling_backend bzw. der dort verwendeten App-Id) und QueueServiceTest (ExclusionService echt über gemockte IAppConfig, deren `getValueArray` die Präfixliste liefert); StorageService mocken: `getFileSlice` ruft das übergebene Closure mit erfundenen internen Pfaden auf und gibt die Zeilen samt `excluded` zurück, `mountRootPath` liefert `files`. Fälle wie im behavior-Block.
- `php -l` ist lokal nicht verfügbar: CI-Vorbehalt im SUMMARY vermerken (PHPUnit + php -l laufen nach dem Push in CI).

Gates aus backend/: ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest), vulture grün. Commit (lokal): `fix(reconcile): mark files excluded by today's rules in the file slice`.
  </action>
  <verify>
    <automated>cd backend && PYTHONUTF8=1 uv run pytest tests/test_exclusion_path_space.py tests/test_reconcile.py tests/test_php_trust_boundary.py tests/test_readonly_gate.py -q</automated>
  </verify>
  <done>Gate- und Quelltexttests erst rot, dann grün; ReconcileController.php ruft isExcluded und mountRelativePath, StorageService.php enthält keinen neuen Präfixvergleich; ReconcileControllerTest.php existiert mit den vier Fällen; volle Python-Suite aus backend/ grün; Gates grün; Commit lokal; CI-Vorbehalt (PHPUnit, php -l) notiert.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Zaehltor zählt den Vorrat teilkorpus-scharf (Werkzeug, Teil b)</name>
  <files>backend/tests/test_v14_zelle.py, docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh</files>
  <behavior>
    - Lauf-7-Belegtest: STUB_SCHEDULED 549 (globaler Vorrat, ausgeschlossene Dateien), Teilkorpus-Vorrat 0, STUB_EMBEDDED/STUB_INDEXED 5000 -> Rückgabe 0, `zaehltor bestanden 5000`, die zaehlung-Zeile trägt summe 5000 und nicht 5549 und nennt beide Vorräte.
    - Positivkontrolle: Teilkorpus-Vorrat 0, global 549, eingebettet 4951 -> Abbruch 71 `zaehltor verfehlt 4951 statt 5000` (der globale Schub füllt kein echtes Defizit).
    - Unlesbarer Teilkorpus-Vorrat (DB-Stub liefert Fehler) -> Abbruch 71.
    - Bestehende Zaehltor-Tests (Lauf 5, Kalibrierfalle, ABORT_71_COUNTERS, embedded-statt-indexed, Leserace) bleiben grün; Vollkorpus-Zellen rufen weiter kein psql.
  </behavior>
  <action>
RED zuerst in backend/tests/test_v14_zelle.py: im DB-Zweig von STUB_DOCKER einen Fall für die neue Vorrats-Query (Muster `*"findling_queue"*`) ergänzen, der `${STUB_VORRAT_TEIL}` ausgibt und ohne diese Variable `STUB_SCHEDULED + STUB_HANDED` der aktuellen Lesung liefert, damit die bestehenden Zaehltor-Tests ihre Zahlen behalten (die erste Lesung nach dem Trigger ist die Zaehltor-Lesung; die Lesezähler-Logik des occ-Zweigs nicht verändern); einen Schalter für eine Fehlerantwort (z. B. `STUB_VORRAT_TEIL=fehler` -> exit 1, db_lesen macht daraus unlesbar). Die drei Tests aus dem behavior-Block anlegen (Docstrings mit Bezug auf 05-typwechsel-arm.txt Lauf 7, L-T Abbruch 71, 5549). RED-Beleg festhalten.

GREEN in docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh (per Owner-Entscheid b):
- Im Zaehltor-Block die Vorratsquelle von `vorrat_von "$WORK/bestand.txt"` auf `db_lesen` umstellen: `select count(*) from ${DB_PREFIX}findling_queue q join ${DB_PREFIX}filecache f on f.fileid = q.file_id where f.path like 'files/teilkorpus/%'`. Die Lesung gehört IN die Doppellesungs-Schleife zwischen `vorher` und `nachher` (neben die frisch-Query), damit Vorrat und embedded aus demselben Fenster stammen. Begründung im Kommentar: scheduled + handed aus occ ist die Summe aller Zeilen über QueueMapper::KINDS, die Query zählt dieselben Zeilen, nur pfadscharf; Lauf 7 (global 549 Dateien unter Ordner-Ausschlüssen, Teilkorpus 0) belegt den Bedarf.
- `bestand_lesen` bleibt in der Schleife (Rohdatum, und der Ende-Schritt bleibt unverändert global, nicht erbeten). Den globalen Wert zusätzlich als `vorrat_global=$(vorrat_von "$WORK/bestand.txt")` lesen und nur protokollieren.
- zaehlung-Zeile: `zaehlung vorrat-teilkorpus $vorrat vorrat-global $vorrat_global uebersprungen-frisch ... summe $summe`. Vorher `grep -n "zaehlung vorrat" backend/tests` prüfen und Asserts auf das alte Format nachziehen. Ein unlesbarer Teilkorpus-Vorrat macht über `ist_zahl` die summe unlesbar -> Abbruch 71 (bestehender Pfad).
- Kopfkommentar (Schritt trigger, Zeilen ~49-55) um "Vorrat teilkorpus-scharf" ergänzen. Sonst nichts am Skript ändern.

Gates aus backend/: ruff check, ruff format --check, pyright (latest), vulture grün; `bash -n ../docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh`. Falls Tests Baum-Hashes der Skripte pinnen (test_measurement_scripts.py / Baumhash), neu pinnen wie in d799ef53. Commit (lokal): `docs(measurements): count the work stock of the partial corpus path sharp at the count gate (28-07)`.
  </action>
  <verify>
    <automated>cd backend && PYTHONUTF8=1 uv run pytest tests/test_v14_zelle.py tests/test_v14_teilkorpus.py tests/test_measurement_scripts.py -q && bash -n ../docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh</automated>
  </verify>
  <done>Lauf-7-Belegtest erst rot (summe 5549, Abbruch 71), dann grün (5000); Positivkontrolle und Unlesbar-Fall Abbruch 71; alle bestehenden Zellen-Tests grün; bash -n sauber; Gates grün; Commit lokal.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Container -> PHP `/files/slice` | ExApp-signierter GET; Antwort verlässt die PHP-Hälfte Richtung Container |
| Admin-Regeln -> Index | Ausschlussregeln bestimmen, was nie in den Index darf |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-wxg-01 | Information Disclosure | ReconcileController::filesSlice | mitigate | Das Prädikat sieht den internen Pfad nur in PHP; die Antwort bleibt bei den sieben Feldern (`excluded` wird vor der Antwort entfernt), Log nur Zähler (T-03-1102); PHPUnit prüft die Feldmenge |
| T-wxg-02 | Tampering/Elevation | Ausschlussregel umgangen | mitigate | Eine bekannte, geänderte ausgeschlossene Datei bleibt content-Arbeit und describe antwortet weiter mit KIND_DELETE (Test D, Gate `test_an_excluded_row_is_handed_out_as_a_delete_order` unverändert grün) |
| T-wxg-03 | Denial of Service | Reconcile-Takt | mitigate | Ausgeschlossene unbekannte Dateien erzeugen keinen Schub mehr, die Runde schließt den Mount ab (Test E) |
| T-wxg-04 | Tampering | Regelaufhebung wirkungslos | mitigate | Kein persistiertes excluded-Urteil im Container (Test A `file_row(10) is None`, Test C) |
| T-wxg-05 | Spoofing | fremde ExApp liest Slice | accept | Unverändert durch rejectForeignCaller abgesichert, nicht Teil dieses Plans |
</threat_model>

<verification>
- Aus backend/: `PYTHONUTF8=1 uv run pytest -q` komplett grün.
- `uv run ruff check .`, `uv run ruff format --check .`, `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`, `uv run vulture src tests --min-confidence 80` grün.
- `bash -n docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh` sauber.
- `git log --oneline -3` zeigt drei lokale Commits, kein Push.
</verification>

<success_criteria>
- Teil a: Container plant ausgeschlossene, ihm unbekannte Dateien nicht mehr ein; Regel liegt allein in PHP (isExcluded/mountRelativePath); Regelaufhebung macht Dateien in der nächsten Runde wieder indexierbar; CR-01-Löschpfad intakt.
- Teil b: Zaehltor-Vorrat teilkorpus-scharf, Lauf-7-Zahlen ergeben 5000.
- SUMMARY vermerkt: (1) RED-Belege aller drei Tasks; (2) CI-Vorbehalt PHPUnit + php -l; (3) Lauf 8 braucht ein NEUES Container-Abbild (CI baut nach dem Push) UND die Companion-App aus php/ erneut in custom_apps/findling der Box (wie Lauf 7), sonst fehlt die excluded-Markierung; (4) der Ende-Schritt von 10-zelle.sh liest den Vorrat weiter global (nicht erbeten, nach dem Produkt-Fix ohne Schub unkritisch).
</success_criteria>

<output>
Create `.planning/quick/261003-wxg-reconcile-beachtet-ausschluesse-zaehltor/261003-wxg-SUMMARY.md` when done
</output>
