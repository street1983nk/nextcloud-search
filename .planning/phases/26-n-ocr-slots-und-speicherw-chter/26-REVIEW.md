---
phase: 26-n-ocr-slots-und-speicherw-chter
reviewed: 2026-09-29T05:33:20Z
depth: standard
files_reviewed: 57
files_reviewed_list:
  - .github/workflows/measure.yml
  - backend/src/findling/api/status.py
  - backend/src/findling/config.py
  - backend/src/findling/extract/errors.py
  - backend/src/findling/extract/image.py
  - backend/src/findling/extract/ocr.py
  - backend/src/findling/extract/pool.py
  - backend/src/findling/extract/sandbox.py
  - backend/src/findling/guard.py
  - backend/src/findling/index/writer.py
  - backend/src/findling/main.py
  - backend/src/findling/memory_guard.py
  - backend/src/findling/nc/queue.py
  - backend/src/findling/profile.py
  - backend/src/findling/worker/embedding.py
  - backend/src/findling/worker/poller.py
  - backend/src/findling/worker/watch.py
  - backend/tests/conftest.py
  - backend/tests/slots_kill_harness.py
  - backend/tests/test_admin_ui_contract.py
  - backend/tests/test_config.py
  - backend/tests/test_embedding_runner.py
  - backend/tests/test_embedding_track.py
  - backend/tests/test_extract_edge_paths.py
  - backend/tests/test_guard.py
  - backend/tests/test_index_writer.py
  - backend/tests/test_latency_probe.py
  - backend/tests/test_main_lifespan.py
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_memory_guard.py
  - backend/tests/test_ocr.py
  - backend/tests/test_poller.py
  - backend/tests/test_pool.py
  - backend/tests/test_profile.py
  - backend/tests/test_profile_wire.py
  - backend/tests/test_queue_client.py
  - backend/tests/test_sandbox.py
  - backend/tests/test_slot_ladder.py
  - backend/tests/test_slots_kill.py
  - backend/tests/test_status_endpoint.py
  - backend/tests/test_watch.py
  - docs/admin-page.md
  - docs/measurements/2026-09-nice-latenz/README.md
  - docs/measurements/2026-09-slot-leiter-ci/README.md
  - docs/ocr.md
  - docs/performance.md
  - docs/profiles.md
  - php/lib/Controller/ProfileController.php
  - php/lib/Service/AdminViewService.php
  - php/lib/Service/QueueService.php
  - php/lib/Service/SettingsService.php
  - php/templates/admin.php
  - php/tests/Unit/AdminViewServiceTest.php
  - php/tests/Unit/ProfileControllerTest.php
  - php/tests/Unit/QueueServiceTest.php
  - scripts/ops/latency_probe.py
  - scripts/ops/slot_ladder.py
findings:
  critical: 1
  warning: 2
  info: 4
  total: 7
status: issues_found
---

# Phase 26: Code Review Report

**Reviewed:** 2026-09-29T05:33:20Z
**Depth:** standard
**Files Reviewed:** 57
**Status:** issues_found

## Summary

Geprüft wurden alle 57 gelisteten Dateien der Phase 26 (N OCR-Slots und Speicherwächter), mit Schwerpunkt auf den Nebenläufigkeits-Zusagen (PAR-02/PAR-03): SlotPool/SlotGate, IndexBatchWriter-RLock, Chunker- und Schreibsperren der Einbettungsspur, Guard-Zustand, Genau-einmal-Zusage der Passfolge, Kill-/OOM-Pfade, Sperrfrist-Rechnung, PHP-Token-Validierung und Lane-Logik.

Der Gesamtstand ist solide: Die Sperrdisziplin des Writers (RLock um Zähler und `add`/`flush`), die Gate-Semantik (Shrink wirkt erst am nächsten Erwerb, Slot 1 läuft immer), die Barriere mit Solo-Wiederholung (D-26-16), die Sperrfrist-Herleitung (`OCR_JOB_SECONDS_MAX`, `ocr_rows_to_keep`, Parität gegen die PHP-Konstanten), die Token-Validierung auf beiden Seiten (32 Hex, `/D`-Modifier, `compare_digest`, geschlossene Mengen) und die Lane-Logik samt Echo-Prüfung sind konsistent gebaut und dicht getestet. Die Rohdaten unter `docs/measurements/2026-09-nice-latenz/raw/` enthalten keine Geheimnisse, keine Nutzerpfade und nur `localhost`-Adressen des Messaufbaus.

Der von den drei Executors gemeldete offene Befund in `extract/sandbox.py` (`_start_child` gegen `halt()`) ist verifiziert und wird als Critical eingestuft (CR-01). Dazu kommen zwei Warnings zur Genau-einmal-Mechanik (nicht freigegebene gehaltene Zeilen nach einem Pass-Fehler, Merker-Reihenfolge in state.db) und vier Info-Befunde.

## Critical Issues

### CR-01: Race zwischen `_start_child` und `halt()` verliert Kills und liest eigene Kills als ChildKilled

**File:** `backend/src/findling/extract/sandbox.py:594-612` (und `halt()` in Zeilen 493-516)
**Issue:** In `_start_child` wird `self._process = process` gesetzt (Zeile 609), und erst danach folgt `self._halted = False` (Zeile 612). `halt()` läuft laut Design aus einem anderen Thread (SlotPool.close() bei Container-Shutdown). Daraus folgen zwei nachweisbare Fehlerbilder:

1. **Halt geht verloren.** Läuft `halt()` zwischen `self._recycle()` (Zeile 597, setzt `_process = None`) und der Zuweisung `self._process = process` (Zeile 609), setzt `halt()` zwar `_halted = True`, liest aber `self._process is None` und tötet nichts. `_start_child` überschreibt danach das Flag mit `False`. Das frisch gestartete Kind arbeitet den Job (bei OCR bis zur harten Deadline von bis zu 840 s) zu Ende, obwohl der Pool geschlossen ist. Da die `findling-slot`-Threads des Executors nicht-daemonisch sind und beim Interpreter-Ende gejoint werden, hält genau dieses Kind den Prozess-Exit auf; docker schickt nach dem Stop-Budget SIGKILL, und der geordnete Shutdown, den `close()` verspricht ("halt kills the group at once"), findet nicht statt.

2. **Eigener Kill wird als fremder gelesen.** Läuft `halt()` zwischen Zeile 609 und Zeile 612, setzt es das Flag und tötet das neue Kind; `_start_child` setzt das Flag anschließend auf `False` zurück. Das wartende `_ask` läuft in `_bury`, dort gilt `exitcode == KILLED_EXIT_CODE and not self._halted` → es wird `ChildKilled(engine=False)` geworfen. Das verletzt die Zusage im Docstring von `halt()` ("never ChildKilled, because the flag is set before the kill is sent"): Der moduleigene Kill wird als Kernel-Kill gelesen, in der Mehr-Slot-Staffel folgt `guard.report_child_kill()` (fälschliche OOM-Zählung, potentiell eine persistente Absenkung, die nur der Admin per Token aufhebt) und die Solo-Wiederholung einer Zeile, obwohl der Pool gerade schließt (`_take` wirft dann RuntimeError in den Catch-all des Pollers).

Umgekehrt kann ein zu spät stehen gebliebenes Flag (halt bei `_process is None`, danach echter OOM-Kill vor dem nächsten `_start_child`-Reset) einen echten Kernel-Kill als `failed(corrupt)` lesen und die Solo-Wiederholung (D-26-16) umgehen; das ist dieselbe Wurzel.

**Fix:** Richtung aus 26-06 bestätigt: Flag vor `process.start()` zurücksetzen, nach der Zuweisung von `self._process` erneut prüfen und bei gesetztem Flag sofort töten. Konkret:

```python
def _start_child(self) -> None:
    if self._process is not None and self._process.is_alive():
        return
    self._recycle()
    # The flag falls BEFORE the start, so a halt that arrives from here on
    # is never erased; it is re-read after the handle is visible.
    self._halted = False
    parent_end, child_end = SPAWN_CONTEXT.Pipe(duplex=True)
    process = SPAWN_CONTEXT.Process(
        target=_child_main, args=(child_end, self.address_space_bytes), daemon=True
    )
    process.start()
    child_end.close()
    self._process = process
    self._pipe = parent_end
    self._files_handled = 0
    # A halt that ran between the reset above and this line saw either no
    # process or the new one; either way the flag is set now and the kill
    # is finished here, as the module's own (never ChildKilled).
    if self._halted and process.is_alive():
        _kill_child_tree(process)
```

Dazu gehört ein Regressionstest, der `halt()` deterministisch in beide Fenster legt (z. B. über ein Monkeypatch auf `SPAWN_CONTEXT.Process.start`, das den `halt()` synchron auslöst) und beide Zusagen prüft: kein überlebendes Kind nach `halt()`, und `failed(corrupt)` statt `ChildKilled` für den eigenen Kill.

## Warnings

### WR-01: Ein Pass, der mit einer unerwarteten Exception endet, gibt seine gehaltenen Zeilen nicht zurück; der nächste Claim überschreibt `_held`

**File:** `backend/src/findling/worker/poller.py:811-816` (Catch-all in `run()`) und `backend/src/findling/worker/poller.py:918` (`self._held = {...}`)
**Issue:** `run()` fängt jede Exception eines Passes, loggt den Typnamen und macht Backoff, ruft aber nie `unlock_held()`. Die Zeilen bleiben in `self._held` stehen, und der nächste `run_once` ersetzt das Set in Zeile 918 (`self._held = {job.queue_id for job in claim.jobs}`) ohne die alten Ids freizugeben. Ab diesem Moment kann auch `stand_down()`/`unlock_held()` sie nicht mehr zurückgeben. Jede solche Zeile zahlt die volle Sperrfrist UND behält ihre gezählte Auslieferung (QueueMapper::unlock erstattet die Auslieferung nur bei einem Unlock, nicht beim Sperrfrist-Ablauf, siehe QueueService::MAX_DELIVERIES-Docblock). Drei Pässe, die z. B. an einem Writer-Fehler (`ValueError` aus tantivy im `flush`) scheitern, schreiben damit gesunde Dateien als `failed(repeatedly_stuck)` ab, exakt der Fehlermodus, den der `sqlite3.Error`-Zweig (ROUND_PAUSED_STORE_ERROR) und DI-05-23 für den Store-Fall gerade beseitigt haben. Für alle anderen Exception-Typen besteht die Lücke weiter.
**Fix:** Im Catch-all von `run()` die gehaltenen Zeilen zurückgeben, bevor der Backoff greift:

```python
except Exception as error:
    LOGGER.error("indexing pass ended in an unexpected %s", type(error).__name__)
    with contextlib.suppress(Exception):
        await self.unlock_held()
    self._back_off()
```

Alternativ (oder zusätzlich, als Gurt): in `run_once` vor Zeile 918 vorhandene Reste freigeben statt zu überschreiben.

### WR-02: Merker-Reihenfolge in state.db: `multi_slot_pass` wird vor `multi_slot_chosen` geschrieben, und `multi_slot_chosen` wird nie geleert

**File:** `backend/src/findling/worker/poller.py:1240-1263` (`_mark_the_multi_slot_pass` / `_clear_the_multi_slot_pass`)
**Issue:** Die Pass-Marke wird in zwei getrennten Autocommit-Statements geschrieben, PASS zuerst, CHOSEN danach; `_clear_the_multi_slot_pass` leert nur PASS. Ein harter Tod zwischen den beiden Schreibvorgängen hinterlässt eine gesetzte PASS-Marke neben einem CHOSEN-Wert aus einer frueheren Staffel. `GuardWatch.restore` (watch.py:185-191) senkt dann mit `chosen=<stale>` ab. Folge über `guard.note_confirmation`: Der Rückweg "anderes Profil gewählt" vergleicht gegen genau dieses gespeicherte `_CHOSEN`. Beispiel: frühere Staffel unter `standard` (CHOSEN=standard bleibt stehen), Admin wechselt auf `performance`, neue Staffel schreibt PASS=performance, Crash vor dem CHOSEN-Write. Nach dem Neustart steht die Absenkung mit `chosen=standard`; die erste Runde liest vom Companion `profile=performance`, `Profile("performance") is _CHOSEN` ist falsch, und die Kappe wird OHNE Token und OHNE Admin-Handlung aufgehoben. Das unterläuft D-26-04 ("Rückweg nur durch den Admin") in genau dem Neustart-nach-Absturz-Fall, für den der Merker existiert.
**Fix:** Reihenfolge drehen und gemeinsam leeren, damit die PASS-Marke der Commit-Punkt ist:

```python
async def _mark_the_multi_slot_pass(self) -> None:
    levels = profile_snapshot()
    chosen = "" if levels.chosen is None else levels.chosen.value
    store = self._store_or_die()
    # CHOSEN first, PASS last: the pass mark is the commit point, so a death
    # between the two writes never pairs a fresh mark with a stale choice.
    await asyncio.to_thread(store.write_meta, guard.META_MULTI_SLOT_CHOSEN, chosen)
    await asyncio.to_thread(store.write_meta, guard.META_MULTI_SLOT_PASS, levels.effective.value)
```

und in `_clear_the_multi_slot_pass` (sowie `GuardWatch.note_shutdown_begins`/`restore`) beide Schlüssel auf `""` setzen, PASS zuerst.

## Info

### IN-01: `guard.snapshot()` kann aus dem Worker-Thread einen zerrissenen Mehr-Feld-Zustand lesen

**File:** `backend/src/findling/guard.py:174-182` (`_set_cap`) und `backend/src/findling/api/status.py:739` (`asyncio.to_thread(report)`)
**Issue:** `_set_cap` mutiert sechs Modul-Globals nacheinander ohne Sperre. Alle Schreiber laufen auf dem Event-Loop, aber `snapshot()` wird über `asyncio.to_thread(report)` aus einem Worker-Thread gelesen; ein Poll der Adminseite kann so z. B. eine neue Kappe mit altem Token/alter Ursache paaren (nur transient, ein Poll später korrekt; `note_confirmation` selbst läuft auf dem Loop und ist nicht betroffen).
**Fix:** Zustand wie in `profile.py` als ein unveränderliches Snapshot-Objekt halten, das `_set_cap` atomar austauscht (eine Referenz-Zuweisung), oder die Felder unter `_KILLS_LOCK` mitschützen.

### IN-02: `SlotPool.call` prüft `_closed` unter der Sperre, submittet aber außerhalb

**File:** `backend/src/findling/extract/pool.py:157-169`
**Issue:** Zwischen dem `_closed`-Check (unter `self._lock`) und `run_in_executor` kann `close()` den Executor herunterfahren; dann wirft `run_in_executor` das generische `RuntimeError("cannot schedule new futures after interpreter shutdown"/"after shutdown")` statt der eigenen Meldung, und die Zeile landet im Catch-all des Pollers. Kein Datenverlust (Zeilen gehen über die Sperrfrist zurück), aber ein irreführender Fehlertyp im Shutdown-Fenster.
**Fix:** Die Submission mit unter die Sperre ziehen oder das `RuntimeError` des Executors in die eigene "this SlotPool is closed"-Meldung übersetzen.

### IN-03: `DocumentQueue.acknowledge` deckelt nur die Skip-Liste, nicht `done` und `failed`

**File:** `backend/src/findling/nc/queue.py:304-321` und `458-497`
**Issue:** `_capped_skips` schützt nur eine der drei Listen gegen `QueueController::MAX_LIST_LENGTH` (256); `done` und `failures` reisen ungedeckelt. Heute unerreichbar (Claim-Deckel 256 auf der PHP-Seite), aber der im Docblock benannte Wächter "gegen den Tag, an dem eine der beiden Zahlen sich bewegt" ist nur für eine Liste gebaut: bewegt sich der Claim-Deckel, macht eine überlange done-Liste die GESAMTE Quittung zum Bad Request und die Zeilen kreisen bis zur Sperrfrist.
**Fix:** Dieselbe Kappung (oder mindestens ein Paritätstest gegen MAX_ACK_LIST) auch für `done` und `failures`, oder ein Kommentar/Assert, der die Annahme "Claim <= MAX_ACK_LIST" explizit an den bestehenden PHP-Paritätstest bindet.

### IN-04: Shutdown-Reihenfolge: Pass-Marke wird geleert, bevor die Stop-Events gesetzt sind

**File:** `backend/src/findling/main.py:1038-1044`
**Issue:** `await _GUARD_WATCH.note_shutdown_begins()` (mit `to_thread`-Await) läuft vor `stop_indexing.set()`. Während dieses Awaits kann der Poller-Loop eine NEUE Mehr-Slot-Staffel beginnen und die Marke erneut schreiben. Endet der geordnete Stop danach im docker-SIGKILL (Stop-Budget), liest der nächste Start ein unclean_end und senkt nach einem gewöhnlichen Update ab, genau das Bild, das Pitfall 9 verhindern soll. Das Fenster ist schmal (Millisekunden gegen die Pass-Kadenz), aber vermeidbar.
**Fix:** Zuerst die Stop-Events setzen (mindestens `stop_indexing.set()`), dann die Marke leeren; oder die Marke nach dem Warten auf `indexing` ein zweites Mal leeren.

---

## Verifikation der Schwerpunkte (ohne Befund)

- **SlotGate/SlotPool:** Shrink nimmt nie einen laufenden Slot (Recheck unter der Condition), Waiter in Ankunftsreihenfolge, lazy Bau unter der Pool-Sperre, `_give` nach `close()` stoppt den Worker. Belegt durch test_pool.py inkl. echter POSIX-Kinder.
- **IndexBatchWriter:** RLock um `add`/`drop_document`/`flush`/`pending*`; Upsert über `Query.term_query` (U64-Typ-Falle dokumentiert und getestet); `flush` prüft den Platz vor dem Commit.
- **Genau-einmal:** Reihenfolge commit -> record -> requeue -> acknowledge per Test gepinnt; Zeilenbeschnitt (`ocr_rows_to_keep`) vor der ersten Extraktion mit unlock (Auslieferung wird erstattet); Solo-Wiederholung vor den Embed-Zeilen, Gate auf 1; SC2-Harness beweist "genau einmal im Index" über echten SIGKILL beider Sorten.
- **Kill-/OOM-Pfade:** `KILLED_EXIT_CODE`-Unterscheidung in `_bury` und `read_page` (SIGKILL vs. SIGABRT), `oom_score_adj` 1000 und nice 10 vor dem Parser-Import (Quelltext-Reihenfolge getestet), `EngineKilled` als Schwester (nicht Subklasse) von `EngineFailed` korrekt durchgereicht. Einzige Ausnahme ist CR-01.
- **Sperrfrist-Rechnung:** `OCR_JOB_SECONDS_MAX = 1800//2 - 120 = 780`, harte Deadline = weiche + 60, Datei-Deckel 900 s, floor(1800/900) = 2 Zeilen je Slot; Paritätstests lesen die PHP-Konstanten aus dem Quelltext.
- **PHP-Token:** `profileConfirmed()` mit `preg_match('/^[0-9a-f]{32}$/D')` (Trailing-Newline abgedeckt), `hexToken()` auf der Anzeige-Seite identisch, Container-Seite `_TOKEN_PATTERN.fullmatch` plus `secrets.compare_digest`; Ausgabe im Template ausschließlich über `p()`.
- **Lane-Logik:** Echo-Prüfung gegen die geschlossene Menge, `lane_honored` default False (sichere Richtung), Index-Lane nur mit parallelem Läufer, Economy wartet auf `parked`; PHP-Seite prüft Lane strikt vor der Datenbank.

---

_Reviewed: 2026-09-29T05:33:20Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
