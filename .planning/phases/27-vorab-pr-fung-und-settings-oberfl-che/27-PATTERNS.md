# Phase 27: Vorab-Prüfung und Settings-Oberfläche - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 34 (neu oder geändert)
**Analogs found:** 31 / 34

Alle Pfade relativ zu `C:\Users\Student\nextcloud-search`. Python-Pfade unter `backend/src/findling/`, Tests unter `backend/tests/`, PHP unter `php/`. Code, Bezeichner, Log-Texte und Katalogschlüssel Englisch; Umlaute nur in Prosa und in den deutschen Katalogwerten.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|---|---|---|---|---|
| `probe.py` (NEU, neutral: Codes, Zustand, Rechnung, Haltesignal) | store + utility | transform, event-driven | `guard.py` (ganz) | exact |
| `worker/probe_run.py` (NEU, Orchestrator) | service (Task) | batch, zeitgedeckelt | `worker/watch.py` (`GuardWatch`) + `worker/embedding.py` `_procure` (1246-1262) | role-match |
| `embed/model_probe.py` (NEU, Spawn-Kind Modellprobe) | service (Prozess-Isolation) | request-response über Pipe | `extract/sandbox.py` `_child_main` (303-383) | role-match |
| `extract/probe_scan.pdf` (NEU, Paketdatei, sha256 gepinnt) | config/asset | file-I/O | `store/schema.sql` (Paketdaten), `embed/weights.py` `FP32_SHA256` (52-58) | partial |
| `api/probe.py` (NEU, `POST /probe`, `GET /probe/state`) | controller | request-response | `api/snippets.py` (POST-Router, 44-62, 247-275) + `api/diagnose.py` (ADMIN-Docstring 40-45) | exact |
| `worker/poller.py` (Halt für die Probe, `shed_idle`) | service | batch | sich selbst `run` (790-824), `stand_down` (679-745) | exact |
| `worker/embedding.py` (EmbedRunner hält, `_need` neutral auslagern) | service | batch | sich selbst `run` (1487-1517), `_need` (1658-1667) | exact |
| `worker/watch.py` (während Probe nur neu basieren, D-27-15) | service (Tick) | event-driven | sich selbst `run_once` (200-213) | exact |
| `api/status.py` (`ProbeReport`, `model.chunks`) | controller | request-response | `LaneReport`/`_lane_report` (189-197, 414-417) | exact |
| `main.py` (Router, Probe-Task, Neustart-Aufräumen) | config/bootstrap | event-driven | Lifespan 889-902, 1030-1103; `_a_rebuild_may_start` 364-368 | exact |
| `guard.py` (IN-01: atomarer Snapshot) | store | event-driven | `profile.py` `_SNAPSHOT` (366-435) | exact |
| `extract/pool.py` (IN-02: Submit unter Sperre; `shed_idle()`) | service | request-response | sich selbst `call` (157-169), `close` (177-202) | exact |
| `config.py` (`PROBE_MEASURE_SECONDS`, `PROBE_DOWNLOAD_SECONDS`, `PROBE_PAUSE_SECONDS`, `MODEL_PROBE_CHILD_BYTES`) | config | - | Zeilen 889-940 (`GUARD_RESERVE_BYTES = OCR_SLOT_COST_BYTES`) | exact |
| `backend/appinfo/info.xml` (zwei Routen ADMIN) | config | - | `<route>` `^/diagnose$` (331-348) | exact |
| `php/lib/Controller/ProfileSettingsController.php` (NEU, drei FrontpageRoutes) | controller | request-response | `SettingsController.php` (`saveRules` 311-406, `overview` 138-150, `userId` 418-420) | exact |
| `php/lib/Service/ProbeService.php` (NEU, Start/Stand/Commit-Bindung) | service | request-response + CRUD (appconfig) | `ExAppService::adminGet` (595-644) + `SettingsService` (Leser/Schreiber) | role-match |
| `php/lib/Service/ExAppService.php` (`adminSend`, `adminState`) | service (Client) | request-response | `adminGet` (577-644), `proxyRequest` (670-684) | exact |
| `php/lib/Service/SettingsService.php` (`profileStored`, `saveProfile`, `saveConfirmation`, `profileCheck*`) | service | CRUD (appconfig) | `profile()` (314-328), `profileConfirmed()` (368-388), `save()` (426-449) | exact |
| `php/lib/Service/AdminViewService.php` (`guardToken` raus, `guardConfirmable` rein, Profil-/Probe-Block) | service | transform | `backend()` (1878-1943), `guardField`/`guardCause`/`hexToken` (2056-2103) | exact |
| `php/lib/Settings/Admin.php` (idempotente Übernahme beim Seitenaufbau) | provider | request-response | sich selbst `getForm` (38-54) | exact |
| `php/templates/admin.php` (Block `#findling-profile`, occ-Zeile raus) | component | request-response | Regeln-Block (929-1044), Diagnose-Karte (841-874), Wächterzeilen (261-295, 531-533) | exact |
| `php/js/admin.js` (Probe-Start, Poll 2000 ms, Knopflogik) | component | event-driven, polling | `ask`/`send` (183-230), `saveRules` (1135-1197), `poll`/`schedule` (1399-1442), `modelLine` (384-399) | exact |
| `php/css/admin.css` (Selektorlisten, `.findling-profile__*`, Chips, Info-Banner) | config (Style) | - | Zeilen 18-38, 69-77, 153-188 | exact |
| `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}` (16 Dateien) | config (i18n) | - | Bestandskataloge + Gates in `test_admin_ui_contract.py` | exact |
| `tests/test_probe.py` (NEU) | test | - | `tests/test_guard.py` | exact |
| `tests/test_probe_run.py` (NEU) | test | - | `tests/test_embedding_runner.py` (injizierte Uhr/Headroom), `tests/test_sandbox.py` (`probe("sleep")`), `tests/test_weights.py` (Fake-Fetch) | role-match |
| `tests/test_probe_endpoint.py` (NEU) | test | request-response | `tests/test_diagnose_endpoint.py` (TestClient, `sign`, info.xml-Block 582-595) | exact |
| `tests/test_poller.py` / `tests/test_embedding_runner.py` (Halt und Wiederaufnahme) | test | - | `_FakeQueue`, `_poller(...)` (siehe 26-PATTERNS) | exact |
| `tests/test_admin_ui_contract.py` (Wächter-Gate umbauen, neue IDs, Ausnahmen) | test | - | Gate 2240-2273, `VALUES_THAT_MAY_EQUAL_THEIR_KEY` 580-682 | exact |
| `tests/test_php_trust_boundary.py` (Ratsche anheben) | test | - | 280-316 | exact |
| `php/tests/Unit/{ProbeService,ProfileSettingsController,SettingsService}Test.php` (NEU) | test | - | `ProfileControllerTest.php` (doubled IAppConfig, 36-110), `ExAppServiceTest.php` (`onlyMethods(['proxyRequest'])`, 236-244) | exact |
| `.github/workflows/integration.yml` (Live-403 als Nicht-Admin) | config (CI) | request-response | Schritte 192-218 (`occ user:add`, curl als testuser) | role-match |
| `docs/admin-page.md`, `docs/profiles.md`, `docs/embeddings.md` §11, `.planning/ROADMAP.md` SC1 | docs | - | sich selbst | exact |

## Pattern Assignments

### `probe.py` (NEU, neutral, ohne I/O)

**Analog:** `guard.py` (ganzes Modul, 331 Zeilen).

**Moduldoc-Schluss** (guard.py 25-28), fast wörtlich übernehmen:
```python
The module is neutral like findling/profile.py: standard library,
findling.config and findling.profile only, so that the worker and the api may
both import it. findling.profile never imports this one (cycle); the cap is
handed over through profile.note_cap. It logs nothing, least of all the token.
```

**Geschlossene Mengen als `Final`-Strings + frozenset** (guard.py 48-52):
```python
CAUSE_NONE: Final = ""
CAUSE_MEMORY_MAX_REPEATED: Final = "memory_max_repeated"
CAUSE_OOM_KILL: Final = "oom_kill"
CAUSE_UNCLEAN_END: Final = "unclean_end"
CAUSES: Final = frozenset({CAUSE_MEMORY_MAX_REPEATED, CAUSE_OOM_KILL, CAUSE_UNCLEAN_END})
```
Für die Probe: `STEPS`, `VERDICT_FITS/NARROW/NOFIT`, `CAUSES_NARROW`, `CAUSES_NOFIT` (Liste aus RESEARCH "Code Examples", 13 Codes inkl. `disk_short`, `memory_unknown`, `interrupted`, `pause_timeout`, `probe_failed`), `STATES = {"idle","running","done"}`, Startcodes separat (`busy`, `rebuilding`).

**Meta-Schlüssel ohne `Final`, mit `noqa`-Kommentar wo S105 greift** (guard.py 54-66):
```python
META_CAP = "guard_cap"
META_TOKEN = "guard_token"  # noqa: S105 - the name of a meta key, not a secret
```
Neu: `META_PROBE_STATE = "probe_state"`, `META_PROBE_ID = "probe_id"`, `META_PROBE_FP32_FETCHED = "probe_fp32_fetched"`, `META_PROBE_RESULT` (Ergebnis als kompakter String, Muster `repr(state.since)` in watch.py 88).

**Frozen Snapshot-Dataclass** (guard.py 79-94): `ProbeSnapshot(id, state, step, bytes_done, bytes_total, verdict, cause, numbers, target_profile, target_precision, started_at, finished_at)`.

**Reine Funktion wie `throttled_slots`** (guard.py 97-105), Vorlage für `judge(...)`:
```python
def throttled_slots(target: int, headroom: int | None) -> int:
    if target <= 1 or headroom is None:
        return 1
    extra = max(0, (headroom - GUARD_RESERVE_BYTES) // OCR_SLOT_COST_BYTES)
    return min(target, 1 + extra)
```
`judge(slots, headroom, slot_cost, pending)` exakt wie RESEARCH-Codebeispiel, `cost = max(slot_cost, OCR_SLOT_COST_BYTES)`, Abstand `GUARD_RESERVE_BYTES` (kein neuer Wert, D-27-08-Nachentscheid). Ausstehende Ladekosten `pending_load_bytes(...)` als reine Funktion nach `EmbedRunner._need` (embedding.py 1658-1667) hierher ziehen und dort wiederverwenden (eine Schreibweise, RESEARCH "Don't Hand-Roll").

**Setter validieren und werfen bei fremden Wörtern** (guard.py 185-194: `if cause not in CAUSES: raise ValueError("unknown guard cause")`).

**Haltesignal** als eigenes Modul-Flag, nicht `silence()/arm()` (RESEARCH Muster 3). `hold()`, `release()`, `held()`; ein `threading.Lock` nur falls aus Threads gelesen (Vorbild `_KILLS_LOCK`, guard.py 169-171, 260-273).

**`reset()` "For tests only; the container never forgets"** (guard.py 291-304) und `__all__` (307-331).

---

### `worker/probe_run.py` (NEU, Orchestrator)

**Analog:** `worker/watch.py` `GuardWatch` (94-254) für Konstruktor/Persistenz/Log, `EmbeddingTrack._procure` (embedding.py 1246-1262) für den Download.

**Hausregeln im Moduldoc** (watch.py 40-45): "nothing is opened in the constructor, every reader and clock is injectable, every exception ... is caught and logged with its type name only. State.db is reached through a connection of its own ..."

**Injizierbarer Konstruktor** (watch.py 102-126):
```python
def __init__(
    self,
    *,
    state_path: Path | None = None,
    events: Events = memory_guard.memory_events,
    headroom: Headroom = memory_guard.headroom_bytes,
    clock: Clock = time.monotonic,
    wall_clock: Clock = time.time,
    tick: float = GUARD_TICK_SECONDS,
    persist: bool = True,
) -> None:
```
Für die Probe zusätzlich: `worker_factory=ExtractionWorker`, `model_child=model_probe.measure`, `fetch=fetch_release_asset`, `poller`, `runner`, `pool`, `models_dir`, `sample_interval=0.2`. Tests injizieren alles.

**Eigene state.db-Verbindung unter Sperre** (watch.py 128-164): `_open`, `_read_meta`, `_write_meta` mit `self._store_lock`, Aufruf nur über `asyncio.to_thread`. Nie die Poller-Verbindung.

**Download mit Ergebnis statt Ausnahme** (embedding.py 1253-1262):
```python
outcome = UNAVAILABLE
try:
    outcome = await procure_fp32(models_dir, fetch_release_asset, min_free_bytes=self._min_free_bytes)
except Exception as error:
    LOGGER.warning("the fetch of the fp32 weights ended in an unexpected %s", type(error).__name__)
finally:
    ...
```
Die Probe umschließt das mit `asyncio.timeout(PROBE_DOWNLOAD_SECONDS)` und zählt Bytes über einen Wrapper um `fetch`, der den `write`-Callback umhüllt (Schnittstelle `fetch(FP32_ASSET_URL, write, cap=FP32_BYTES)`, weights.py 239-247). `procure_fp32` räumt `.part` im `finally` (weights.py 310-313), also auch bei Deckel-Cancellation. Mapping der vier Ergebnisse `PROCURE_OUTCOMES` (weights.py 64-70) auf Ursachencodes laut RESEARCH Muster 1. Die Probe ruft `begin_procurement` NICHT (RESEARCH Muster 4).

**Warten auf Staffel-Ende** nach `stand_down` (poller.py 726-735), aber ohne Writer-Close und ohne `unlock_held`:
```python
deadline = time.monotonic() + budget
while self._in_flight:
    if time.monotonic() >= deadline:
        LOGGER.warning(...)
        return False
    await asyncio.sleep(STAND_DOWN_TICK_SECONDS)
```
Budget `PROBE_PAUSE_SECONDS` (1800 s), Überschreitung -> `pause_timeout`. Wartet auf `poller.pass_in_flight` (675-677) und `runner.parked` (embedding.py 1430-1433).

**Kinder-Deadline:** jedes `ExtractionWorker.run(..., timeout_seconds=verbleibend)` (sandbox.py 417-453), damit `_ask` selbst tötet (543-557). Fremd-Kill kommt als `ChildKilled` (sandbox.py 567-583) -> Ursache `slot_killed`. Frische Worker statt Pool-Kinder (Pitfall 5); am Ende `worker.stop()` (483-491).

**Headroom-Stichproben:** eigener Daemon-Thread, nie Default-Executor (pool.py Moduldoc 14-20). `memory_guard.headroom_bytes()` (memory_guard.py 71-89), `None` -> `memory_unknown` (Regel `admits`, 92-94).

**Log-Regel** (watch.py 224-225, 250-254): nur statische Sätze mit `%s` für Codes und Typnamen, nie Pfad, URL, Token, Zahlen aus Nutzerdaten.

---

### `embed/model_probe.py` (NEU, Spawn-Kind)

**Analog:** `extract/sandbox.py` `_child_main` (303-383) und die Härtungshelfer.

**Spawn-Kontext** (sandbox.py 71-72): `SPAWN_CONTEXT: Final = mp.get_context("spawn")` wiederverwenden (importieren, nicht neu definieren).

**Härtungsreihenfolge im Kind** (sandbox.py 310-328), übernehmen ohne `_limit_address_space` (RESEARCH Muster 4, A2):
```python
if sys.platform != "win32":
    os.setsid()
    os.nice(SANDBOX_NICE)
    _lower_own_standing()
_shed_secrets()
_limit_address_space(address_space_bytes)   # NICHT für das Modell-Kind
_pin_native_thread_pools()

from findling.extract.dispatch import Route, extract   # Import erst nach der Härtung
```
Helfer `_lower_own_standing` (187-213), `_shed_secrets` (238-250) importieren statt kopieren. onnxruntime-Import erst nach der Härtung im Kind (Import-Hygiene, Moduldoc 44-49).

**Antwort als Tupel statt Objekt** (sandbox.py 74-86, 351-354): Pipe-Protokoll klein halten, z. B. `(rss_before, rss_after, passages_per_second)` als Ints/Floats. Ausnahmen im Kind als Sentinel (Muster `_ANSWER_KILLED`), `MemoryError` gesondert (358-362).

**Kill und Deadline im Elternteil:** Muster `_ask` (518-565) mit `pipe.poll(deadline)` und `_kill_child_tree` (120-130); Messmethode (RssAnon vor Laden und nach erstem Batch, 8 Passagen, Sequenzlänge 512) laut `docs/measurements/2026-09-fp32-speicher/README.md` §3.

---

### `extract/probe_scan.pdf` (NEU, Paketdatei)

**Analog:** `store/schema.sql` (Nicht-.py-Datei im Modul, von `uv_build` mitgenommen, `backend/pyproject.toml` 91-96 `module-root = "src"`), Quelle `testdata/corpus/13-ratsvorlage-scan.pdf` (existiert).

**Digest-Pin wie die fp32-Konstanten** (weights.py 52-53):
```python
FP32_SHA256: Final = "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"
FP32_BYTES: Final = 470_268_510
```
`PROBE_SCAN_SHA256`/`PROBE_SCAN_BYTES` in `probe.py` oder `probe_run.py`; Test prüft Datei im Paket und Digest.

---

### `api/probe.py` (NEU, Router)

**Analog:** `api/snippets.py` (POST mit pydantic-Body) und `api/diagnose.py` (Docstring zu ADMIN).

**Imports und Router** (snippets.py 40-62):
```python
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
...
LOGGER = logging.getLogger("findling.api.snippets")

ROUTER = APIRouter()
```

**POST-Handler** (snippets.py 247-255):
```python
@ROUTER.post("/snippets")
async def snippets(
    body: SnippetsRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> SnippetsResponse:
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")
```
Body `ProbeRequest(profile: Literal["economy","standard","performance"], precision: Literal["int8","fp32"])` (zweite geschlossene Menge nach PHP). Antworten 202 `{id}`, 409 `{state:"busy", id}` / `{state:"rebuilding"}`, 503 ohne Lifespan. Für 202/409 `JSONResponse` wie in `main.py` 1159-1174.

**Antwortmodell mit Defaults überall** (diagnose.py 83-109, "Every field defaults"): `ProbeStateResponse` mit `state="idle"`, leeren Strings und `None` für Zahlen, nie Text, nie Pfad.

**Docstring-Absatz zu ADMIN** (diagnose.py 40-45) sinngemäß übernehmen: `exAppRequest` passiert die Access-Level-Prüfung nie; wirksame Grenze ist die PHP-Route.

**Registrierung** in `main.py` neben den anderen (1135-1139): `APP.include_router(PROBE_ROUTER)`.

---

### `worker/poller.py` (Halt für die Probe)

**Analog:** sich selbst, `run` (790-808):
```python
while not stop_event.is_set():
    if not self._armed.is_set():
        await _first_of(self._armed.wait(), stop_event.wait())
        continue
    try:
        self._in_flight = True
        try:
            await self.run_once()
        finally:
            self._in_flight = False
```
Neuer Zweig direkt nach dem Armed-Check: gehalten -> `await _first_of(<release-Event>.wait(), stop_event.wait()); continue`. `_first_of` (2262-2270) wiederverwenden. Halt-Event im Konstruktor neben `self._armed = asyncio.Event()` (581); Kommentar-Stil wie 582-589 (warum `_in_flight` und nicht `busy`). `arm()/silence()` (649-672) bleiben unberührt (Anti-Pattern RESEARCH). Die Probe setzt `multi_slot_pass` NICHT (RESEARCH Muster 3).

---

### `worker/embedding.py` (EmbedRunner hält)

**Analog:** sich selbst, `run` (1494-1504) mit gleichem Armed-Muster; `parked` (1430-1433, 1521-1525) ist das Signal "keine Runde läuft". Halt-Zweig wie beim Poller. `_need` (1658-1667) ruft künftig die neutrale Funktion aus `probe.py`:
```python
need = EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES
if not self._track.cutter_built:
    need += CUTTER_LOAD_BYTES
if self._engine() != ENGINE_LOADED:
    need += EMBED_WEIGHTS_LOAD_BYTES
    if weights == WEIGHTS_FP32:
        need += FP32_EXTRA_BYTES
```

---

### `worker/watch.py` (Rebase während der Probe, D-27-15)

**Analog:** sich selbst, `run_once` (200-213):
```python
events = await asyncio.to_thread(self._events)
headroom = await asyncio.to_thread(self._headroom)
cause = self._escalation.observe(self._clock(), events, headroom, guard.take_child_kills())
```
Während `probe.held()` (und einen Tick danach): nur Basis setzen, nicht zählen. `Escalation.observe` setzt die Basis als erste Tat (guard.py 131-132); eine Methode `Escalation.rebase(events)` plus `guard.take_child_kills()` verwerfen ist die schmale Änderung. Slot-Drossel bleibt aktiv.

---

### `api/status.py` (`ProbeReport`, `model.chunks`)

**Analog:** `LaneReport` + `_lane_report` (189-197, 414-417):
```python
class LaneReport(BaseModel):
    """Where the embedding runs, out of ``findling.lane``: inline or parallel, and why."""

    mode: str = "inline"
    reason: str = ""
...
def _lane_report() -> LaneReport:
    state = lane.snapshot()
    return LaneReport(mode=state.mode, reason=state.reason)
```
`ProbeReport(supported: bool = True, running: bool = False, step: str = "")`, liest nur `probe.snapshot()`, misst nichts (T-07-04). Feld in `StatusResponse` mit Kommentar wie 353-356. `GuardReport.token` (200-225) bleibt im Container-Status (PHP liest ihn serverseitig), aber der Docstring "the admin confirms it through occ" (211-212) wird auf den Knopf umgeschrieben. `ModelReport` (170-186) bekommt `chunks: int = 0` für die Reindex-Schätzung.

---

### `main.py` (Lifespan)

**Analog:** Aufbau des Wächters (889-902) und Shutdown (1095-1103):
```python
_GUARD_WATCH = GuardWatch(persist=not shared_volume.other)
try:
    await _GUARD_WATCH.restore()
except Exception as error:
    LOGGER.warning("the memory guard could not restore its state, %s", type(error).__name__)
stop_watch = asyncio.Event()
watching = asyncio.create_task(_guarded_watch(_GUARD_WATCH, stop_watch))
```
```python
stop_watch.set()
with contextlib.suppress(TimeoutError):
    await asyncio.wait_for(asyncio.shield(watching), timeout=GUARD_STOP_SECONDS)
if not watching.done():
    watching.cancel()
await asyncio.gather(watching, return_exceptions=True)
```
Probe-Task als Modulvariable wie `_REBUILDING` (106-107), angehängt an den Lifespan, damit der Shutdown ihn cancelt und das `finally` die Pause aufhebt. Startsperre bei laufendem Rebuild über `_a_rebuild_may_start()` (364-368) -> Startcode `rebuilding`. Start-Aufräumen `probe_state == running` -> `interrupted`; fp32-Datei erst nach erstem erfolgreichem `companion_choice` löschen (Pitfall 7; `companion_choice` in `nc/queue.py` 556-582).

---

### `guard.py` (IN-01)

**Analog:** `profile.py` 366-435, eine Referenz-Zuweisung als atomarer Austausch:
```python
_SNAPSHOT: ProfileSnapshot = _compute(None, None, _INT8)
...
def note_cap(cap: Profile | None) -> None:
    global _CAP, _SNAPSHOT
    if cap is _CAP:
        return
    _CAP = cap
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP)
...
def snapshot() -> ProfileSnapshot:
    return _SNAPSHOT
```
`_set_cap` (guard.py 174-182) schreibt heute sechs Globals nacheinander; künftig ein unveränderliches Zustandsobjekt bauen und in einem Schritt zuweisen, `snapshot()` (276-288) liest nur diese eine Referenz. Regressionstest in `test_guard.py` (Stil 198-216).

---

### `extract/pool.py` (IN-02, `shed_idle`)

**Analog:** sich selbst `call` (157-169):
```python
with self._lock:
    if self._closed:
        raise RuntimeError("this SlotPool is closed")
    if self._executor is None:
        self._executor = ThreadPoolExecutor(max_workers=self._size, thread_name_prefix="findling-slot")
    executor = self._executor
return asyncio.get_running_loop().run_in_executor(executor, functools.partial(fn, *args, **kwargs))
```
Fix: `run_in_executor` unter die Sperre ziehen oder das `RuntimeError` des Executors in die eigene Meldung übersetzen (26-REVIEW IN-02). `shed_idle()` nach `close()` (177-202), aber nur die Freiliste: unter `self._lock` `free = list(self._free); self._free.clear(); self._built -= len(free)`, danach außerhalb `worker.stop()`.

---

### `config.py`

**Analog:** Zeilen 920-940, Kommentar mit Herleitung vor jeder Konstante:
```python
# The reserve a further slot has to leave free, ...
GUARD_RESERVE_BYTES = OCR_SLOT_COST_BYTES
```
Neu: `PROBE_MEASURE_SECONDS = 120`, `PROBE_DOWNLOAD_SECONDS = 600`, `PROBE_PAUSE_SECONDS = OCR_LOCK_TIMEOUT_SECONDS` (467), `MODEL_PROBE_CHILD_BYTES` aus der Messung. Keine Umgebungsvariable (INDEX_WORKERS-Tabu).

---

### `backend/appinfo/info.xml`

**Analog:** `^/diagnose$` (331-348):
```xml
<route>
    <url>^/diagnose$</url>
    <verb>GET</verb>
    <access_level>ADMIN</access_level>
    <headers_to_exclude>[]</headers_to_exclude>
    <bruteforce_protection>[401]</bruteforce_protection>
</route>
```
Zwei neue Blöcke `^/probe$` (POST) und `^/probe/state$` (GET), je ein Kommentarblock davor. Kommentar "Five routes" (261) und "do not shorten these five" (275-276) auf sieben ziehen.

---

### `php/lib/Controller/ProfileSettingsController.php` (NEU)

**Analog:** `SettingsController.php`.

**Klassenkopf und Konstruktor** (1-17, 93, 108-117):
```php
declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\IRequest;
use OCP\IUserSession;
use Psr\Log\LoggerInterface;

final class SettingsController extends Controller {
	public function __construct(
		IRequest $request,
		...
		private IUserSession $userSession,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}
```
Plain `Controller`, nie `OCSController` (Docblock 48-53). Die vier verbotenen Attributnamen nicht im Datei-Text erwähnen und den Attributnamen nur über den Methoden schreiben (Docblock 42-46, Gate zählt Zeilen).

**Route mit voll qualifiziertem Attribut** (311-317):
```php
#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'POST', url: '/admin/rules')]
public function saveRules(
	array $exclusions = [],
	int $maxFileBytes = 0,
	...
): DataResponse {
```
Drei Routen: `POST /admin/profile/check` (Start), `GET /admin/profile/check` (Stand, idempotente Übernahme), `POST /admin/profile` (Abwärtsweg ohne Probe). Wertemengen mit `in_array(..., SettingsService::PROFILES, true)` (RESEARCH PHP-Beispiel).

**Ablehnung zählen, nie zitieren** (329-342) und **Fehlerpfad** (386-398):
```php
} catch (\Throwable $e) {
	$this->logger->error('Findling: could not save the rules', ['exception' => $e]);

	return new DataResponse(
		['saved' => false, 'error' => 'The rules could not be saved.'],
		Http::STATUS_INTERNAL_SERVER_ERROR,
	);
}
```
**Session-UID** (418-420): `$this->userSession->getUser()?->getUID() ?? ''`.

---

### `php/lib/Service/ProbeService.php` (NEU)

**Analog:** `ExAppService::adminGet` (Transport) + `SettingsService` (appconfig) + `AdminViewService` (Feldprüfung).

**Container-Felder gegen geschlossene Mengen prüfen**, nie casten (AdminViewService 2056-2092):
```php
public static function guardField(array $answer, string $key): mixed {
	$guard = $answer['guard'] ?? null;

	return is_array($guard) ? ($guard[$key] ?? null) : null;
}

public static function guardCause(mixed $value): ?string {
	return is_string($value) && in_array($value, self::GUARD_CAUSES, true) ? $value : null;
}

public static function hexToken(mixed $value): ?string {
	return is_string($value) && preg_match('/^[0-9a-f]{32}$/D', $value) === 1 ? $value : null;
}
```
Neue Mengen als `private const` in derselben Einzeilen-Schreibweise wie `GUARD_CAUSES` (Gate-Regex `private const GUARD_CAUSES = \[([^\]]*)\];`, test_admin_ui_contract 2280): `PROBE_STATES`, `PROBE_STEPS`, `PROBE_VERDICTS`, `PROBE_CAUSES`. Zahlen über `guardCounter`-Muster (2101-2103). Probe-Id als `/^[0-9a-f]{16}$/D`.

**Commit-Bindung:** `pending` per `IAppConfig::setValueArray`, Vergleich `hash_equals`, einmalige Übernahme bei `state=done && id == pending.id && target == pending`. Bestätigungs-Token nur hier aus frischem `adminGet('/status', ...)` gelesen (AdminViewService 526) und per `SettingsService::saveConfirmation` geschrieben (D-27-12).

---

### `php/lib/Service/ExAppService.php` (`adminSend`, `adminState`)

**Analog:** `adminGet` (595-644) mit den vier Fällen, aber unterscheidbarer Rückgabe statt `null`:
```php
$response = $this->proxyRequest($path, $userId, 'GET', $params, self::ADMIN_REQUEST_TIMEOUT_SECONDS);
if ($response === null) {
	return null;                       // -> kind 'unreachable'
}
if (is_array($response)) {             // Case 1: Transportfehler
	$this->logger->warning('Findling: backend unreachable for the admin page', [...]);
	return null;                       // -> kind 'unreachable'
}
if ($response->getStatusCode() >= 400) {   // Case 2: 404 -> 'missing', 409 -> 'busy', sonst 'refused'
	...
}
// Case 3: Körpergröße gegen MAX_BODY_BYTES, Case 4: json_decode
```
Form `{kind: ok|unreachable|missing|busy|refused, body}`; `proxyRequest` (670-684) bleibt die einzige Ausgangsstelle (POST: Body-Params). Timeout `ADMIN_REQUEST_TIMEOUT_SECONDS` (140).

---

### `php/lib/Service/SettingsService.php`

**Analog:** Leser mit Validierung (314-328), Token-Prüfung (368-388), Schreiber (426-449), `reject()` (469-475).
```php
public function profile(): string {
	$stored = $this->appConfig->getValueString(
		Application::APP_ID,
		self::KEY_PROFILE,
		self::PROFILE_DEFAULT,
	);

	if (!in_array($stored, self::PROFILES, true)) {
		$this->reject();

		return self::PROFILE_DEFAULT;
	}

	return $stored;
}
```
Neu: `profileStored(): bool` über `IAppConfig::hasKey(Application::APP_ID, self::KEY_PROFILE)`; `saveProfile(string $profile, string $precision): bool` validiert erneut (Docblock-Argument 418-422: occ ist ein zweiter Weg); `saveConfirmation(string $token)` mit `/^[0-9a-f]{32}$/D`; `KEY_PROFILE_CHECK = 'profile_check'`, `KEY_PROFILE_CHECK_PENDING = 'profile_check_pending'` mit Docblock im Stil 110-121. Docblocks "Until the admin page of phase 27 the only way ... occ" (118-119, 145-147) umschreiben (D-27-13).

---

### `php/lib/Service/AdminViewService.php`

**Analog:** `backend()` (1878-1943), Feld für Feld über einen Richter:
```php
'guardCause' => self::guardCause(self::guardField($answer, 'cause')),
// The confirmation token of the way back, shown inside an occ
// command and nowhere else; only 32 lower case hex digits pass
// (D-26-04, no button in this phase).
'guardToken' => self::hexToken(self::guardField($answer, 'token')),
```
Ersetzen durch `'guardConfirmable' => self::hexToken(self::guardField($answer, 'token')) !== null,` (Token verlässt den Server nicht, Pitfall 2). Neue Einträge für den Block `profile` (Hardware, chosen/suggested/effective, `sources` mit Wert `env`) über eine `profileField`-Hilfe nach `modelField` (2017-2021), Block `probe` (`supported`, `running`, `step`) und `model.chunks`. `profileStored` und letztes `profile_check` aus `SettingsService` in `overview()` (484-549) aufnehmen, damit Template und Initial State denselben Stand lesen.

---

### `php/lib/Settings/Admin.php`

**Analog:** sich selbst (38-54):
```php
$overview = $this->view->overview();

$this->initialState->provideInitialState('bootstrap', $overview);

return new TemplateResponse(Application::APP_ID, 'admin', $overview, TemplateResponse::RENDER_AS_BLANK);
```
Vor `overview()` einmal `ProbeService::settle()` (idempotente Übernahme eines fertigen "passt", RESEARCH Muster 5), damit ein geschlossener Tab das Verdikt nicht verliert. Bootstrap enthält keinen Token mehr.

---

### `php/templates/admin.php` (Block `#findling-profile`)

**Analog 1: Wörter nur aus PHP-Maps** (261-282):
```php
$profileNames = ['economy' => $l->t('Economy'), 'standard' => $l->t('Standard'), 'performance' => $l->t('Performance')];
$causeNames = [
	'memory_max_repeated' => $l->t('memory tight, memory.events max twice'),
	...
];
$guardCause = is_string($backend['guardCause'] ?? null) ? $backend['guardCause'] : '';
$guardCauseName = $causeNames[$guardCause] ?? '';
```
Gleiches Muster für `$stepNames`, `$verdictNames`, `$probeCauseNames`, `$envNames` (vier feste Variablennamen). Unbekannter Code = leer = Zeile `hidden`.

**Analog 2: Marker-Schnitt für `<code>`** (285-291), jetzt für Env-Zeilen statt occ:
```php
$wayBackMarker = "\u{E000}";
$wayBackParts = explode($wayBackMarker, $l->t('To lift the reduction after checking the memory: %1$s', [$wayBackMarker]), 2) + ['', ''];
```
Zeilen 283-291 und `#findling-guard-way-back` (532) entfallen samt Katalogschlüssel (D-27-12).

**Analog 3: Blockaufbau und Formular** (929-1035): `<div id="findling-rules" class="section">`, `<h2>`, `label.findling-rules__label`, `div.findling-rules__toggle` mit `input.checkbox` + `label`, `p.findling-rules__error`, `button.primary`, `p.findling-rules__feedback`. Neuer Block direkt vor 929.

**Analog 4: Verdikt-Karte mit allen Icons im Markup** (858-873):
```php
<div class="findling-card" id="findling-diagnosis-result" role="status" aria-live="polite" hidden>
	<p class="findling-chip" id="findling-diagnosis-chip">
		<?php foreach ($diagnosisIcons as $state => $icon) { ?>
			<svg id="findling-diagnosis-icon-<?php p($state); ?>" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false" hidden><path fill="currentColor" d="<?php p($icon); ?>"/></svg>
		<?php } ?>
```
Für die Verdikt-Karte: kein `aria-live` auf der Karte (UI-SPEC: eine Live-Region `#findling-profile-announce`), `tabindex="-1"`. Icons: `$diagnosisIcons['indexed']` (830), `$alertIcon` (309), `$infoIcon` (622), neuer close-circle-Pfad aus dem gepinnten MDI-Commit.

**Analog 5: Nojs-Zeile und Spinner** (850, 856): `p.settings-hint#…-nojs`, `span.icon-loading-small`; Fortschritt als `p.settings-hint.findling-progress-hint` (631).

**Server-Render aller Zustände** (Kommentar 225-227): alle Elemente liegen im Markup, JS schaltet nur `hidden` und Textknoten.

---

### `php/js/admin.js`

**Analog: Routen-Konstanten voll ausgeschrieben** (48-55):
```js
const ROUTE_RULES = 'admin/rules'
const ROUTE_RULES_PREVIEW = 'admin/rules/preview'
```
Neu `ROUTE_PROFILE = 'admin/profile'`, `ROUTE_PROFILE_CHECK = 'admin/profile/check'`, `POLL_PROBE_MS = 2000`.

**Lesen und Schreiben** (183-230): `ask(path, params, signal)` mit `requesttoken: document.head.dataset.requesttoken` bei jedem Aufruf; `send(path, payload)` gibt `{ ok, body }` zurück statt zu werfen.

**Knopf-Ablauf** (saveRules 1167-1196):
```js
if (button !== null) {
  button.disabled = true
}
try {
  const answer = await send(ROUTE_RULES, {...})
  if (answer.ok && answer.body.saved === true) {
    ...
    feedback(true, t('findling', 'Rules saved. The next run applies them.'))
    return
  }
  feedback(false, t('findling', 'The rules were not saved. Nothing changed.'))
} catch (error) {
  feedback(false, ...)
} finally {
  if (button !== null) {
    button.disabled = false
  }
}
```

**Poll-Schleife mit eigenem AbortController** (1399-1442, `lookupRequest` 67-71 als Vorbild für einen eigenen `probeRequest`, damit Status-Poll und Probe-Poll sich nicht abbrechen). Nach Verdikt `schedule(0)` für den Status-Poll.

**Codes auf Katalogsätze** (modelLine 384-399): Map im Skript, unbekannt = leer = `shown(id, false)`:
```js
const names = { int8: 'e5-small int8', fp32: 'e5-small fp32' }
const name = (precision === 'int8' || precision === 'fp32') ? names[precision] : ''
text('findling-semantic-model', t('findling', 'Model: %1$s').replace('%1$s', name))
shown('findling-semantic-model', name !== '')
```
Formatierer `span()` (124-132), `size()` (143-157), `numbers.format`; Hilfen `text()` (232-240), `shown()` (242-247). Nojs verbergen wie `shown('findling-diagnosis-nojs', false)` (831). `setupProfile()` neben `setupRules()` (1454-1456). Kein Markup bauen (Gate C, Moduldoc 11-19).

---

### `php/css/admin.css`

**Analog:** Selektorlisten (18-38) um `#findling-profile` erweitern:
```css
#findling-diagnosis,
#findling-rules {
	max-width: 900px;
}
...
#findling-rules [hidden] {
	display: none !important;
}
```
Chips anhängen statt kopieren (153-180): `.findling-chip--narrow` an `--skipped`, `.findling-chip--nofit` an `--failed`, `.findling-chip--fits` an `--indexed`, jeweils auch die `svg`-Regel. `.findling-banner--info` nach `.findling-banner--warning` (74-77). Abstände nur `calc(var(--default-grid-baseline) * n)` (Kopfkommentar 6-8).

---

### `php/l10n/*` (16 Dateien)

**Analog:** Bestandskataloge; Gates in `test_admin_ui_contract.py`:
- `test_every_catalogue_carries_the_same_keys` (2525), `test_every_catalogue_value_carries_a_wording_of_its_language` (2658), `test_no_catalogue_value_loses_or_invents_a_placeholder` (2733), `test_no_catalogue_value_can_break_the_page` (2785).
- Ausnahmen je Sprache mit Begründung in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` (580-682), Stil:
```python
"Standard": "the name of a profile, the same word in German as in English",
```
`de_DE` spiegelt `de` (682). Schlüssel `To lift the reduction after checking the memory: %1$s` in allen 16 Dateien löschen.

---

### `tests/test_probe.py` (NEU)

**Analog:** `tests/test_guard.py`: kleine Fabriken (`_events` 44, `_big_box` 48), ein Test je Regel mit sprechendem Namen (`test_the_throttle_grants_a_slot_per_cost_above_the_reserve`, 97). Grenzfälle `judge`: reserve -1, 0, 234 MiB, 235 MiB; Pin `GUARD_RESERVE_BYTES` als Abstand; geschlossene Mengen (`test_the_causes_are_a_closed_set_without_the_empty_word`, 69); Meta-Schreibweise (`test_the_meta_keys_are_the_agreed_spelling`, 77).

### `tests/test_probe_run.py` (NEU)

**Analog:** injizierte Leser und Uhr wie `tests/test_embedding_runner.py`; Kind-Deadline über `ExtractionWorker.probe("sleep", ...)` (sandbox.py 148-149, 455-462); Fremd-Kill über `os.kill(worker.pid, signal.SIGKILL)` wie `tests/test_sandbox.py` (26-PATTERNS); Fake-Fetch nach `tests/test_weights.py` (`_Sink.write`, 69-79) mit hängender Variante für den Download-Deckel. Vorab-Tor: kein Kind gestartet (Zähler auf `worker_factory`).

### `tests/test_probe_endpoint.py` (NEU)

**Analog:** `tests/test_diagnose_endpoint.py`: `pytestmark = pytest.mark.usefixtures("appapi_environment")` (47), Fixtures `client`/`sign` aus `conftest.py` (393-421), `BACKEND_INFO` (57) und der info.xml-Block-Test (582-595):
```python
manifest = BACKEND_INFO.read_text(encoding="utf-8")
block = manifest[manifest.index("<url>^/diagnose$</url>") :]

assert "<access_level>ADMIN</access_level>" in block[: block.index("</route>")]
```
Je einmal für `^/probe$` und `^/probe/state$`; zweiter Start 409 `busy`; Feldmenge der Antwort als Ganzes (FIELDS-Muster 59-72).

### `tests/test_admin_ui_contract.py` (Wächter-Gate umbauen)

**Analog:** 2246-2273:
```python
for key, judge, field in (
    ("guardChosen", "profileName", "chosen"),
    ...
    ("guardToken", "hexToken", "token"),
    ...
):
    assert view.count(f"'{key}' => ") == 1, key
for element in ("findling-guard", "findling-guard-way-back", "findling-slots"):
    assert f'id="{element}"<?php if (' in template, element
assert "<code><?php p($wayBackCommand); ?></code>" in template
```
`guardToken`/`findling-guard-way-back`/`$wayBackCommand`/entfallender Schlüssel werden zu Abwesenheits-Asserts (Schlüssel fehlt in allen 16 Katalogen, Token nicht in Overview/Bootstrap). Neues Gate für `#findling-profile`: genau ein `select` mit drei `option`, alle IDs der UI-SPEC, kein Aufklapp-Element (SC1), PHP/JS-Map-Gleichheit der Codes (Muster `scan_guard_fields` 2288-2294).

### `tests/test_php_trust_boundary.py`

**Analog:** Ratsche 297-316. Neue FrontpageRoutes erhöhen die Zählung; Untergrenze mit Kommentar anheben ("Every plan that adds a route raises this bound with it"). `FORBIDDEN_ON_ADMIN_ROUTE` (102) bleibt unverändert.

### PHPUnit: `ProbeServiceTest.php`, `ProfileSettingsControllerTest.php`, `SettingsServiceTest.php` (NEU)

**Analog:** `ProfileControllerTest.php` (36-92): echter `SettingsService` auf gedoubeltem `IAppConfig` (Service ist `final`), `stored(...)`-Helfer mit Map über alle Schlüssel:
```php
$this->appConfig->method('getValueString')->willReturnCallback(
	static fn (string $app, string $key, string $default = ''): string => $values[$key] ?? $default,
);
```
Transport-Double nach `ExAppServiceTest.php` (236-244):
```php
return $this->getMockBuilder(ExAppService::class)
	->setConstructorArgs([...])
	->onlyMethods(['proxyRequest'])
	->getMock();
```
Fälle: nur `fits` mit passender Id schreibt; fremde Id/fremdes Ziel schreibt nicht; zweite Übernahme idempotent; Abwärtsweg-Regel (economy, fp32 -> int8) sonst `probe_required`; `profileStored()` false bei fehlendem Schlüssel. Nur in CI (`php.yml` Job `phpunit`).

### `.github/workflows/integration.yml` (Live-403)

**Analog:** 192-218: Nutzer über `OC_PASS=... ./occ user:add --password-from-env testuser` (196), Aufruf mit `curl -u "testuser:${TESTUSER_PASS}"`. Neuer Schritt: `POST /index.php/apps/findling/admin/profile/check` und `POST /index.php/apps/findling/admin/profile` als Nicht-Admin, Status 403 (bzw. Redirect/401 je nach Middleware) per `curl -s -o /dev/null -w '%{http_code}'` prüfen. Kommentarstil "The assertions in order of what they rule out" (198-207).

### Doku

`docs/admin-page.md`, `docs/profiles.md`, `docs/embeddings.md` §11, `ROADMAP.md` SC1: sich selbst als Analog; Inhalte laut UI-SPEC "Doku-Folgen" und D-27-11/13. Kurze Sätze, keine Erzählabsätze (Owner-Regel).

## Shared Patterns

### Geschlossene Mengen statt Text über die Vertrauensgrenze
**Source:** `guard.py` 48-52, `AdminViewService.php` 2056-2103, `admin.php` 271-282, `admin.js` 384-399
**Apply to:** `probe.py`, `api/probe.py`, `ProbeService`, `AdminViewService`, Template, Skript, Kataloge
Container liefert nur Codes; PHP prüft mit `in_array(..., true)` bzw. `/D`-verankertem Regex; Anzeige nur über PHP-/JS-Map auf `$l->t`/`t('findling', ...)`; unbekannt = Zeile verborgen (T-26-16).

### Admin-Schutz durch Abwesenheit der Attribute
**Source:** `SettingsController.php` Docblock 55-80, `test_php_trust_boundary.py` 102
**Apply to:** `ProfileSettingsController`
Plain `Controller`, `FrontpageRoute` voll qualifiziert, kein NoAdminRequired/PublicPage/NoCSRFRequired/ExAppRequired; info.xml ADMIN nur Tiefenverteidigung.

### Neutrale Zustandsmodule
**Source:** `guard.py`, `profile.py` 366-445
**Apply to:** `probe.py`, IN-01-Fix
Stdlib + config, `note_*`-Setter validieren, `snapshot()` ohne Seiteneffekt als eine Referenz, `reset()` nur für Tests, kein Logging.

### Task-Lebenszyklus und Ausnahme-Hygiene
**Source:** `watch.py` 215-227, `poller.py` 790-824, `main.py` 1095-1103
**Apply to:** `probe_run.py`, Halt in Poller/Runner
Jede Ausnahme gefangen, geloggt nur mit `type(error).__name__`; `CancelledError` durchlassen; Pause immer im `finally` aufheben; Shutdown `wait_for(shield(task))`, dann `cancel` + `gather(return_exceptions=True)`.

### Gehärtete Spawn-Kinder
**Source:** `sandbox.py` 303-383, `pool.py` 14-20
**Apply to:** Probe-OCR-Läufe, `model_probe.py`
`setsid`, `nice(SANDBOX_NICE)`, `_lower_own_standing`, `_shed_secrets` vor jedem Import; Wartezeiten nie im Default-Executor.

### Speicherrechnung aus einer Schreibweise
**Source:** `memory_guard.py` 71-94, `guard.py` 97-105, `embedding.py` 1658-1667
**Apply to:** `probe.judge`, `EmbedRunner._need`
Headroom über `headroom_bytes()`, unlesbar nie zugelassen, Slot-Kosten mindestens `OCR_SLOT_COST_BYTES`, Abstand `GUARD_RESERVE_BYTES`.

### Log-Hygiene
**Source:** `poller.py` 812-815, `SettingsController.php` 326-332
**Apply to:** alle neuen Module und PHP-Klassen
Statische Sätze, Zähler, Codes, Typnamen; nie Pfad, URL, Token, Nutzereingabe.

### Katalog-Gleichstand
**Source:** `test_admin_ui_contract.py` 275-299, 580-682, 2525-2839
**Apply to:** alle 16 Katalogdateien
Jeder neue Schlüssel in allen acht Sprachen, JS und JSON wertgleich, Ausnahmen begründet, kein nacktes `%`, kein `|`.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| Headroom-Stichproben-Thread in `worker/probe_run.py` | utility | streaming (Messreihe) | Kein Bestandscode tastet den Headroom periodisch während eines Laufs ab; RESEARCH Muster 2 (200 ms, Daemon-Thread, Minimum) nutzen |
| Modellmessung im Kind (`embed/model_probe.py`, RssAnon-Delta, Passagenrate) | service | request-response | Nur als Messskript unter `docs/measurements/2026-09-fp32-speicher` beschrieben, kein Laufzeitcode; Methode dort §3 übernehmen, Härtung aus `sandbox.py` |
| Commit-Bindung per Probe-Id (`ProbeService`) | service | request-response | Keine Schreibroute bindet heute an ein Container-Ergebnis; RESEARCH Muster 5 als Vorlage, Prüfhelfer aus `AdminViewService` |

## Metadata

**Analog search scope:** `backend/src/findling/{guard,profile,memory_guard,config,main}.py`, `backend/src/findling/{worker,extract,embed,api,nc}/`, `backend/appinfo/info.xml`, `backend/tests/{test_guard,test_diagnose_endpoint,test_php_trust_boundary,test_admin_ui_contract,conftest}.py`, `php/lib/{Controller,Service,Settings}`, `php/templates/admin.php`, `php/js/admin.js`, `php/css/admin.css`, `php/tests/Unit/{ProfileControllerTest,ExAppServiceTest}.php`, `.github/workflows/integration.yml`, `.planning/phases/26-*/26-REVIEW.md`
**Files scanned:** 30
**Pattern extraction date:** 2026-09-29
