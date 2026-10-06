# Phase 26: N OCR-Slots und Speicherwächter - Pattern Map

**Mapped:** 2026-09-28
**Files analyzed:** 27 (neu oder geändert)
**Analogs found:** 25 / 27

Alle Pfade relativ zu `C:\Users\Student\nextcloud-search`. Python-Pfade unter `backend/src/findling/`, Tests unter `backend/tests/`. Code, Bezeichner und Log-Texte Englisch; Umlaute nur in Prosa.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|---|---|---|---|---|
| `extract/sandbox.py` (geändert: nice, oom_score_adj, ChildKilled, Priority-Job) | service (Prozess-Isolation) | request-response über Pipe | sich selbst (`_child_main`, `_ask`) | exact |
| `extract/pool.py` (NEU: SlotPool, SlotGate) | service/utility | request-response, nebenläufig | `extract/sandbox.py` (`ExtractionWorker`, `extract_guarded`) + `scripts/ops/ocr_slot_probe.py` (N Worker je Thread) | role-match |
| `extract/ocr.py` + `extract/image.py` (EngineKilled) | utility | subprocess | `extract/ocr.py` `read_page`/`EngineFailed` | exact |
| `index/writer.py` (threading.Lock) | service | CRUD (Index-Schreiben) | sich selbst | exact |
| `memory_guard.py` (+ `memory_events`) | utility (Kernel-Leser) | file-I/O | `memory_guard.anon_bytes` | exact |
| `guard.py` (NEU, neutral: Stufe, Ursache, Token, Drossel) | store (Prozesszustand) | event-driven | `lane.py`, `profile.py` (Modul-State + snapshot/reset) | exact |
| `profile.py` (`effective()` mit Kappe) | utility | transform | sich selbst (`effective`, `_compute`) | exact |
| `worker/watch.py` (NEU, Wächter-Task) | service (Lifespan-Task) | event-driven, Tick | `worker/embedding.py` `EmbedRunner` (run/arm/silence/tick/headroom-Injektion) | role-match |
| `worker/poller.py` (Staffel, Zeilenbeschnitt, Barriere, Solo-Wiederholung, Drossel, Unrein-Ende) | service | batch | sich selbst (`run_once`, `_work`, `_read_the_scan`, `_abort`) | exact |
| `worker/embedding.py` (embed_slots nebenläufig) | service | batch | sich selbst (`EmbedRunner._work`, `EmbeddingTrack._embed`) | exact |
| `config.py` (OCR_CLAIM_BATCH_INDEX_LANE, OCR_ROWS_PER_SLOT, GUARD_*, SANDBOX_NICE, neue Ableitung) | config | - | sich selbst (Zeilen 462-491, 845-917) | exact |
| `nc/queue.py` (`CompanionChoice.confirmed`) | service (Client) | request-response | `companion_choice` Zeilen 545-569 | exact |
| `store/repo.py` (nur Nutzung `read_meta`/`write_meta`) | model | CRUD | Zeilen 707-716 | exact |
| `main.py` (Wächter-Task, Pool schließen, Merker beim Shutdown-Beginn) | config/bootstrap | event-driven | Lifespan Zeilen 862-886, 988-1044 | exact |
| `api/status.py` (GuardReport im Profilblock) | controller | request-response | `ProfileReport`/`LaneReport`, `_profile_report`, `_lane_report` | exact |
| `php/lib/Service/QueueService.php` (KIND_BATCH[ocr] je Lane) | service | CRUD | sich selbst (Zeilen 150-194, 237-310) | exact |
| `php/lib/Service/SettingsService.php` (`KEY_PROFILE_CONFIRMED`, `profileConfirmed()`) | service | CRUD (appconfig) | `modelPrecision()` Zeilen 110-137, 315-341 | exact |
| `php/lib/Controller/ProfileController.php` (`confirmed` in der Antwort) | controller | request-response | sich selbst Zeilen 45-82 | exact |
| `php/lib/Service/AdminViewService.php` + `php/templates/admin.php` + `php/l10n/*` (8 Kataloge) | component | request-response | `precisionActive`-Zeile (AdminViewService 1886-1891, admin.php 245-259) | exact |
| `tests/test_config.py` (Parität je Lane, Rows-per-slot-Invariante) | test | - | Zeilen 544-617 | exact |
| `tests/test_sandbox.py` (nice/oom-Vererbung, ChildKilled, Reihenfolge) | test | - | Zeilen 264-336, 388-421 | exact |
| `tests/test_pool.py` (NEU) | test | - | `tests/test_sandbox.py` Fixture `worker` | role-match |
| `tests/test_memory_guard.py` (+ memory.events) / `tests/test_guard.py` / `tests/test_watch.py` (NEU) | test | - | `tests/test_memory_guard.py` `_tree`-Fake-cgroup | exact |
| `tests/test_poller.py` (Staffel unter N) | test | - | `_FakeQueue`, `_Extractor`, `_poller`, `_WorkStock` | exact |
| `tests/test_slots_kill.py` (NEU, Kill-Harness SC2) | test (Integration) | batch | `_WorkStock` (test_poller.py 2151-2250) + `test_group_kill_reaches_a_grandchild` | partial |
| `scripts/ops/slot_ladder.py` oder `ocr_slot_probe.py --mode poller` | utility (Messwerkzeug) | batch | `scripts/ops/ocr_slot_probe.py` | exact |
| `.github/workflows/measure.yml` (Job `slots`, neuer Schritt) | config (CI) | batch | Job `slots` Schritt B und F (Zeilen 533-630) | exact |

## Pattern Assignments

### `extract/sandbox.py` (service, Pipe-Protokoll)

**Analog:** sich selbst.

**Kind-Härtung, Reihenfolge ist die Eigenschaft** (Zeilen 219-239). Neue Zeilen direkt nach `os.setsid()`, im selben `sys.platform != "win32"`-Block (pyright prüft plattformabhängig, `os.nice` fehlt unter Windows):
```python
def _child_main(pipe: PipeEnd, address_space_bytes: int) -> None:
    if sys.platform != "win32":
        os.setsid()
    _shed_secrets()
    _limit_address_space(address_space_bytes)
    _pin_native_thread_pools()

    from findling.extract.dispatch import Route, extract
```
Neue Helfer im Stil von `_shed_secrets`/`_pin_native_thread_pools` (Zeilen 154-216): eine kleine Modulfunktion mit Docstring, der das Warum erklärt, best effort `OSError` schlucken (Vorbild `_kill_child_tree` Zeilen 99-107: `except (ProcessLookupError, PermissionError, OSError): pass`).

**Protokoll-Konstanten** (Zeilen 64-67): neuer Job-Typ als `Final`-String, z. B. `_JOB_PRIORITY: Final = "priority"`; Antwort als Tupel wie `_JOB_MODULES` (Zeile 260-261):
```python
if kind == _JOB_MODULES:
    answer: object = tuple(sorted(name for name in sys.modules if name.startswith("findling")))
```

**Kind-Tod-Erkennung** (Zeilen 406-412), hier setzt `ChildKilled` an:
```python
try:
    return pipe.recv()
except (EOFError, OSError):
    # Recycling rule 4 again, from the other side: the child died between
    # accepting the job and answering it.
    self._recycle()
    return ExtractionOutcome.failed(Reason.CORRUPT)
```
Wichtig: `process.exitcode` vor `self._recycle()` lesen (nach `process.join(_JOIN_GRACE_SECONDS)`), denn `_recycle()` (Zeilen 445-456) schließt und nullt `self._process`. Der Timeout-Pfad (Zeilen 390-404) kehrt vorher zurück, also ist `-SIGKILL` im EOF-Zweig immer ein fremder Kill. Kein neuer `Reason` (Quittung validiert gegen PHP-Liste). `run()` (Zeilen 332-344) prüft `isinstance(outcome, ExtractionOutcome)`; eine Ausnahme `ChildKilled` muss an dieser Prüfung vorbei zum Aufrufer.

**Docstrings nachziehen:** Moduldoc Zeilen 22-25 ("exactly one extraction runs at a time") und `extract_guarded` Zeilen 470-477 ("One worker per process") gelten nur noch für Sparsam.

---

### `extract/pool.py` (NEU, SlotPool + SlotGate)

**Analog:** `extract/sandbox.py` `ExtractionWorker` + Fassade `extract_guarded` (Zeilen 459-486); Mehrfach-Worker-Muster aus `scripts/ops/ocr_slot_probe.py` (Moduldoc Zeilen 4-12: "N threads, and every thread holds its own ExtractionWorker").

**Signatur, die Test-Fakes passen lässt** (sandbox.py 462-469, poller.py 186-191):
```python
def extract_guarded(
    path: str,
    mime: str,
    size: int,
    *,
    route: str | None = None,
    timeout_seconds: float | None = None,
) -> ExtractionOutcome:
```
```python
# poller.py
ExtractFile = Callable[..., ExtractionOutcome]
```
`SlotPool.run(...)` muss exakt diese Schlüsselwörter tragen, damit `_Extractor` aus `test_poller.py` (Zeilen 335-367) unverändert injizierbar bleibt.

**Import-Kopf** (sandbox.py 41-56): `from __future__ import annotations`, `Final`, `from findling import config`, `from findling.extract.errors import ExtractionOutcome, Reason`. Der Pool importiert **nicht** den Dispatcher (Import-Hygiene, Test `test_child_does_not_import_findling_index`).

**SlotGate:** Entwurf aus RESEARCH Muster 1 (`asyncio.Condition`, `wait_for(lambda: in_use < limit)`), kein Bestandsanalog. Eigener `ThreadPoolExecutor(max_workers=N_max, thread_name_prefix="findling-slot")` via `loop.run_in_executor`, **nicht** `asyncio.to_thread` (Default-Executor teilt `/search`, `/status`).

**Schließen:** jedes `ExtractionWorker.stop()` (sandbox.py 358-366) plus Executor-`shutdown(wait=False, cancel_futures=True)`; Aufruf aus dem Lifespan (siehe `main.py`).

---

### `extract/ocr.py` und `extract/image.py` (EngineKilled)

**Analog:** `extract/ocr.py` Zeilen 99-104 und 204-213.
```python
class EngineFailed(Exception):
    """The engine ended with a non zero code or was killed by a signal."""
...
    if finished.returncode != 0:
        raise EngineFailed
```
Neue Unterklasse oder Schwester `EngineKilled` bei `finished.returncode == -signal.SIGKILL`, geprüft **vor** dem `!= 0`-Zweig. Beide Aufrufer mappen: `ocr.py` Zeile 131 (`except EngineFailed: return ExtractionOutcome.failed(Reason.OCR_FAILED)`) und `image.py` Zeile 129 (`except ocr.EngineFailed:`). Da ein Reason nicht in Frage kommt, muss das Kind "killed" als Pipe-Sentinel melden (Antwort-Tupel wie `_JOB_MODULES`), das `ExtractionWorker` in `ChildKilled` übersetzt.

---

### `index/writer.py` (threading.Lock)

**Analog:** sich selbst. Zustandsfelder im Konstruktor (Zeilen 172-176):
```python
self._pending = 0
self._pending_bytes = 0
heap = resolved.writer_heap_bytes if heap_bytes is None else heap_bytes
try:
    self._writer: IndexWriter | None = index.writer(heap_size=heap, num_threads=1)
```
Hier `self._lock = threading.Lock()` ergänzen. Zu sperren: `add` (243-322, Löschen+Einfügen+Zähler als Einheit), `drop_document` (324-366), `flush` (393-422), `collect_garbage` (424-430), `close` (432-443), Properties `pending`/`pending_bytes` (199-241). `stored_body`/`free_bytes`/`disk_is_tight` sind lesend und brauchen keine Sperre. `"num_threads=1"` muss wörtlich stehen bleiben (Pin in `test_profile.py` Zeile 211).

---

### `memory_guard.py` (+ `memory_events`)

**Analog:** `anon_bytes` Zeilen 28-43, gleiche Hausregeln (Moduldoc 5-7: stdlib + `findling.hardware`, Pfad injizierbar, wirft nie, loggt nie):
```python
_STAT_FIELDS = 2  # "<name> <bytes>"

def anon_bytes(root: Path = CGROUP_ROOT) -> int | None:
    """The ``anon`` bytes of memory.stat, or None when the file or the line is unusable."""
    try:
        raw = (root / "memory.stat").read_text(encoding="ascii")
    except (OSError, ValueError):
        return None
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) != _STAT_FIELDS or fields[0] != "anon":
            continue
```
`memory_events(root) -> dict[str, int] | None` wie RESEARCH Code-Beispiel; `_STAT_FIELDS` wiederverwenden. Moduldoc "phase 26 builds the memory guard on top of it" (Zeile 3-4) ist schon vorbereitet.

---

### `guard.py` (NEU, neutral)

**Analog:** `lane.py` (ganzes Modul, 121 Zeilen) und Modul-State-Teil von `profile.py` (Zeilen 344-415).

**Moduldoc-Schluss** (lane.py 22-23): "The module is neutral like findling/profile.py: standard library only, so that the worker and the api may both import it. It logs nothing."

**Geschlossene Mengen + Snapshot-Dataclass** (lane.py 29-47):
```python
MODE_INLINE: Final = "inline"
MODE_PARALLEL: Final = "parallel"
MODES: Final = frozenset({MODE_INLINE, MODE_PARALLEL})
...
@dataclass(frozen=True, slots=True)
class LaneSnapshot:
    mode: str
    reason: str
    supported: bool
```
Für den Wächter: `CAUSE_NONE = ""`, `CAUSE_MEMORY_MAX_REPEATED = "memory_max_repeated"`, `CAUSE_OOM_KILL = "oom_kill"`, `CAUSE_UNCLEAN_END = "unclean_end"`, `CAUSES: Final = frozenset(...)`.

**Setter mit Validierung, die bei fremden Wörtern wirft** (lane.py 77-88):
```python
def note_mode(mode: str, reason: str) -> None:
    global _MODE, _REASON
    if mode not in MODES or reason not in REASONS:
        raise ValueError("unknown lane mode or reason")
```
**`snapshot()` und `reset()` ("For tests only; the container never forgets")**, lane.py 91-102, plus `__all__` (105-121).

`throttled_slots(target, headroom)` als reine Funktion hier (RESEARCH Muster 6), Konstanten aus `config.py`. Token über `secrets.token_hex(16)`.

---

### `profile.py` (`effective()` berücksichtigt Kappe)

**Analog:** sich selbst, Zeilen 160-163 und 329-341:
```python
def effective(chosen: Profile | None, fitting: Profile) -> Profile:
    """min(chosen, fitting); never read counts as economy, never switches up (D-24-07)."""
    wanted = Profile.ECONOMY if chosen is None else chosen
    return min(wanted, fitting, key=PROFILE_ORDER.index)
```
Kappe als drittes, optionales Argument in `min(...)`; neuer Modul-State `_CAP` mit Setter `note_cap(...)` nach Vorbild `note_weights`/`note_chosen` (Zeilen 369-397: nur bei Änderung neu rechnen, nichts loggen), `reset()` (409-415) nachziehen. `ProfileSnapshot.downgraded` (310-313) bleibt die Anzeige "gewählt vs. wirksam". Moduldoc-Absatz "Phase 24 computes and reports only" (29-33) anpassen. `profile.py` darf `guard.py` nicht importieren, wenn `guard.py` `profile` importiert (Zyklus-Regel wie bei `precision`, Zeilen 112-117): Kappe als `Profile | None` hineinreichen.

---

### `worker/watch.py` (NEU, Wächter-Task)

**Analog:** `worker/embedding.py` `EmbedRunner` Zeilen 1323-1476 und 1565-1596.

**Konstruktor mit injizierbaren Lesern und Uhr** (1359-1376):
```python
def __init__(
    self,
    *,
    track: EmbeddingTrack,
    client_factory: ClientFactory = nc_client.create_app_client,
    queue_factory: QueueFactory = DocumentQueue,
    tick: float = EMBED_RUNNER_TICK_SECONDS,
    headroom: Headroom = memory_guard.headroom_bytes,
    engine: EngineState = engine_state,
    clock: Clock = time.monotonic,
) -> None:
```
Für den Wächter: `events=memory_guard.memory_events`, `headroom=memory_guard.headroom_bytes`, `clock=time.monotonic`, `tick=15.0` (gleicher Takt `EMBED_RUNNER_TICK_SECONDS`, Zeile 174), plus Persistenz-Callback.

**Schleife, jede Ausnahme gefangen, nur Typname geloggt** (1446-1476):
```python
while not stop_event.is_set():
    if not self._armed.is_set():
        await _first_of(self._armed.wait(), stop_event.wait())
        continue
    ...
    except Exception as error:
        LOGGER.error("embed round ended in an unexpected %s", type(error).__name__)
        self._back_off()
    await _pause(wait + self._cooldown, stop_event)
```
**Kernel-Lesen in einem Thread** (1577, 1583-1585):
```python
if not await asyncio.to_thread(self._admits, snapshot.weights):
```
**Anti-Flattern über Zeitstempel** (1574-1576) ist das Vorbild für "zwei qualifizierte Ticks, mindestens 60 s Abstand, Fenster 600 s".

---

### `worker/poller.py` (Staffel unter N Slots)

**Analog:** sich selbst.

**Injektion im Konstruktor** (397-416): neuer Parameter z. B. `ocr_slots: int | None = None` (Kill-Harness, Pitfall 10: kein Umgebungsschalter) und `extract: ExtractFile = extract_guarded` wird auf den Pool umgestellt. Default bleibt Produktionsverdrahtung.

**Profil vor dem Anspruch, Lane-Wahl** (746-766):
```python
choice = await queue.companion_choice()
note_chosen(choice.profile)
note_chosen_precision(choice.precision)
economy = profile_snapshot().effective is Profile.ECONOMY
...
wanted = LANE_INDEX if not economy and lane.snapshot().mode == lane.MODE_PARALLEL else None
claim = await queue.claim(limit=self._batch_files, max_bytes=self._batch_max_bytes, lane=wanted)
```
Hier: Token-Abgleich (`choice.confirmed`) und Drossel-Lesung vor der Staffel; Kommentar Zeilen 739-745 ("from phase 26 on the size of the claim depends on it", "Nothing below reads the value yet") aktualisieren.

**Gehaltene Zeilen und Zeilenbeschnitt** (821-835): nach `self._held = {...}` den Überschuss per `queue.unlock(...)` zurückgeben und aus `_held` nehmen, Muster aus `_work` Schritt 3b (926-932):
```python
if moved.ok:
    self._held.difference_update(queue_ids[file_id] for file_id in file_ids if file_id in queue_ids)
```
**Staffel-Reihenfolge bleibt** (856-941): Schritt 1 Schleife `for job in jobs`, Abbruch-Ausnahmen `_GatewayDown`/`_DiskTight` -> `self._abort(...)`; Schritt 2 `flush` in `asyncio.to_thread`; 3 `_record_verdicts`; 3b `hand_over`; 4 `acknowledge` dann `self._held.clear()`. Die OCR-Tasks laufen nur in Schritt 1, danach Barriere (`asyncio.gather(..., return_exceptions=True)`), Ausnahmen nach der Barriere wie heute in `_abort`.

**OCR-Zeile, die zur Task wird** (`_read_the_scan`, 1187-1233):
```python
outcome = await asyncio.to_thread(
    self._extract,
    str(read.path),
    job.mime,
    read.size,
    route=Route.OCR,
    timeout_seconds=self._ocr_hard_deadline,
)
...
if outcome.state is State.INDEXED:
    await asyncio.to_thread(self._writer_or_die().add, _record_of(job, outcome))
```
In der Task: `_fetch_file`, Extraktion über Pool-Executor statt `to_thread`, `writer.add` (Sperre in der Klasse); `_collect` (1466-1511) erst nach der Barriere im Loop-Thread, keine `state.db`-Zugriffe in der Task (Pitfall 4). `_discard(read.path)` im `finally` beibehalten.

**Abbruch gibt immer zurück** (`_abort`, 1607-1633): `await queue.unlock(sorted(self._held))`, `self._held.clear()`, `self._back_off()`. Solo-Wiederholung nach `ChildKilled` mit Limit 1, zweiter Kill -> `ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)`.

**Log-Regel** (Moduldoc 48-50, Beispiel 945-956): nur Zähler und Reason-Codes (`"pass finished, claimed=%d indexed=%d ..."`), ein neuer Zähler wie `slots=%d throttled=%d` fügt sich dort ein.

---

### `worker/embedding.py` (embed_slots = 2)

**Analog:** `EmbedRunner._work` (1526-1561) und `EmbeddingTrack._embed` (519-615).

Heutige Serienschleife, die nebenläufig wird:
```python
for job in jobs:
    if not _level_allows_parallel():
        stopped = True
        break
    if job.kind != KIND_EMBED:
        continue
    await self._track.embed_row(job, done)
```
Innerhalb der Track-Sperre (`async with self._track.lock:`, Zeile 1493; `self.lock = asyncio.Lock()`, Zeile 369) Tasks mit `asyncio.Semaphore(profile.snapshot().resolution.values.embed_slots)`. Neu zu sperren in `_embed`: `asyncio.to_thread(chunker, body)` (Zeile 579, `threading.Lock`), `replace_acl` (569) und `vectors.replace_chunks` (601-613) per `asyncio.Lock` (eine Verbindung mit `BEGIN IMMEDIATE`). `_rows_in_work`-Zähler (513-517) ist schon mehrfachfest. Klassendoc "One runner, one row at a time (D-25-12)" (1340-1342) und `config.py` Kommentar 892-894 aktualisieren.

---

### `config.py`

**Analog:** sich selbst, Spiegel-Block Zeilen 462-491:
```python
OCR_LOCK_TIMEOUT_SECONDS = 1800
OCR_CLAIM_BATCH = 2
...
OCR_JOB_SECONDS_MAX = OCR_LOCK_TIMEOUT_SECONDS // OCR_CLAIM_BATCH - 2 * OCR_HARD_DEADLINE_MARGIN_SECONDS
...
OCR_JOB_SECONDS_RANGE = (1, OCR_JOB_SECONDS_MAX)
```
Neu: `OCR_CLAIM_BATCH_INDEX_LANE = 32`, `OCR_ROWS_PER_SLOT = 2`, Ableitung auf `OCR_ROWS_PER_SLOT` umstellen (Wert bleibt 780), `OCR_CLAIM_BATCH = 2` bleibt (Pin `test_profile.py` 209). Kommentarstil: jede Konstante mit Herleitung und Verweis auf PHP-Gegenstück. Wächter-Konstanten nach Vorbild `EMBED_LANE_RESERVE_BYTES = OCR_SLOT_COST_BYTES` (Zeile 885): `GUARD_RESERVE_BYTES = OCR_SLOT_COST_BYTES`, `GUARD_WINDOW_SECONDS = 600`, `GUARD_MIN_GAP_SECONDS = 60`, `SANDBOX_NICE = 10`. Keine Umgebungsvariable für Slots (Moduldoc profile.py 24-27, INDEX_WORKERS-Tabu).

---

### `nc/queue.py` (`confirmed`)

**Analog:** `CompanionChoice` (197-206) und `companion_choice` (545-569):
```python
payload = _mapping(answer) or {}
profile = payload.get("profile")
precision = payload.get("precision")
return CompanionChoice(
    profile=profile if isinstance(profile, str) and profile in PROFILE_NAMES else None,
    precision=precision if isinstance(precision, str) and precision in PRECISION_NAMES else None,
)
```
Drittes Feld `confirmed: str | None`, validiert als 32 Hex (sonst None). Fehlerpfad (554-561) liefert alle drei None. `_FakeQueue.companion_choice` in `test_poller.py` (220-225) und `_WorkStock` (2185-2188) um das Feld ergänzen.

---

### `store/repo.py` (Merker, nur Nutzung)

**Analog:** Zeilen 707-716:
```python
def read_meta(self) -> dict[str, str]:
    return {str(key): str(value) for key, value in self._conn.execute("SELECT key, value FROM meta")}

def write_meta(self, key: str, value: str) -> None:
    self._conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
```
Schlüssel `guard_cap`, `guard_cause`, `guard_since`, `guard_token`, `guard_chosen`, `multi_slot_pass`. Eigene Verbindung für den Wächter (`open_store`), nicht die Poller-Verbindung.

---

### `main.py` (Lifespan)

**Analog:** Zeilen 875-886 (Runner-Aufbau) und 988-1044 (Shutdown-Reihenfolge):
```python
global _EMBEDDING
stop_embedding = asyncio.Event()
_EMBEDDING = EmbedRunner(track=_POLLER.track)
_POLLER.attach_runner(_EMBEDDING)
embedding = asyncio.create_task(_guarded_embedding(_EMBEDDING, stop_embedding))
```
```python
finally:
    stop_indexing.set()
    stop_embedding.set()
    ...
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(asyncio.shield(indexing), timeout=POLLER_STOP_SECONDS)
    if not indexing.done():
        indexing.cancel()
        await asyncio.gather(indexing, return_exceptions=True)
    with contextlib.suppress(Exception):
        await _POLLER.unlock_held()
    await _POLLER.aclose()
```
Merker `multi_slot_pass = 0` als **erste** Zeile im `finally` (vor allen Wartezeiten, Pitfall 9). Pool schließen nach dem Poller-Stop. Wächter-Task wie `releasing`/`repairing` (907-911, 1046-1057). Merker-Lesen beim Start neben `note_hardware` (857-860), in `asyncio.to_thread`, Ausnahme nur mit Typname loggen.

---

### `api/status.py` (GuardReport)

**Analog:** `ProfileReport`/`LaneReport` (153-197) und `_lane_report` (382-385):
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
Neue Felder als camelCase mit Defaults (jedes Feld defaultet, Klassendoc 200-204), liest nur `guard.snapshot()`, misst nichts (T-07-04). Feld in `StatusResponse` mit Kommentar wie Zeilen 322-324; Übernahme im Volume-Pfad (592-603) nicht vergessen. Test-Analog: `tests/test_status_endpoint.py` Zeile 1243 ff.

---

### `php/lib/Service/QueueService.php` (KIND_BATCH[ocr] je Lane)

**Analog:** sich selbst, Konstante 187-194 und Verwendung 279:
```php
private const KIND_BATCH = [
	QueueMapper::KIND_ACL => 128,
	QueueMapper::KIND_DELETE => 128,
	QueueMapper::KIND_METADATA => 64,
	QueueMapper::KIND_CONTENT => 32,
	QueueMapper::KIND_OCR => 2,
	QueueMapper::KIND_EMBED => 8,
];
...
$batch = min(self::KIND_BATCH[$kind] ?? $limit, $rows);
```
Vorschlag: zweite Konstante `KIND_BATCH_INDEX_LANE = [QueueMapper::KIND_OCR => 32,]` (Zeilenform `KEY => N,` mit Komma, sonst greift der Paritäts-Regex nicht) und Auswahl vor Zeile 279 bei `$lane === self::LANE_INDEX`. Die Lane-Zweige 271-277 sind das Muster. Docblock 150-186 ("ocr is two, and that number is arithmetic") und `claim()`-Docblock 229-233 ("the per kind batch of KIND_BATCH ... are the same in every lane") müssen umgeschrieben werden. PHP-Test: `php/tests/Unit/QueueServiceTest.php` `kindsAskedFor` (199-235) erweitern, sodass auch `$limit` je Kind aufgezeichnet wird.

---

### `php/lib/Service/SettingsService.php` + `ProfileController.php` (`confirmed`)

**Analog:** Schlüssel-Konstante 110-121 und Leser 315-341:
```php
public const KEY_MODEL_PRECISION = 'model_precision';
...
public function modelPrecision(): ?string {
	$stored = $this->appConfig->getValueString(
		Application::APP_ID,
		self::KEY_MODEL_PRECISION,
		self::PRECISION_DEFAULT,
	);
	if (!in_array($stored, self::PRECISIONS, true)) {
		$this->reject();
		return null;
	}
	return $stored;
}
```
`KEY_PROFILE_CONFIRMED = 'profile_confirmed'`, Validierung `preg_match('/^[0-9a-f]{32}$/', ...)`, sonst null. Docblock nennt den occ-Rückweg wie Zeile 118-119. Controller-Antwort (ProfileController 68-71) um `'confirmed' => $this->settingsService->profileConfirmed()` ergänzen, Docblock 45-57 anpassen. Test: `php/tests/Unit/ProfileControllerTest.php` `stored(...)` (67 ff.) und die `assertSame([...], $response->getData())`-Fälle (99, 108, 124).

---

### Adminseite + acht Kataloge

**Analog:** `AdminViewService::backend()` (1847-1893), Feld aus Unterobjekt über geschlossene Menge:
```php
'precisionActive' => self::precision(self::modelField($answer, 'precisionActive')),
'reembedRunning' => self::strictFlag(self::modelField($answer, 'reembedRunning')),
```
Template `admin.php` 245-259: Anzeigename wird **auf PHP-Seite** aus einem Wort der geschlossenen Menge gebaut, nie Container-Text übernommen (T-25-14):
```php
$modelNames = ['int8' => 'e5-small int8', 'fp32' => 'e5-small fp32'];
$precisionActive = is_string($backend['precisionActive'] ?? null) ? $backend['precisionActive'] : '';
$modelLine = ... $l->t('Model: %1$s', [$modelName]);
```
Ursachen `memory_max_repeated`/`oom_kill`/`unclean_end` genauso als Map auf `$l->t(...)`. Neue Strings in allen acht Katalogen `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}` im Gleichstand. Test: `php/tests/Unit/AdminViewServiceTest.php`.

---

### `tests/test_config.py` (Parität je Lane, Invariante)

**Analog:** Zeilen 544-617.
```python
def _php_constant_entry(source_path: Path, block_name: str, key: str) -> int:
    source = source_path.read_text(encoding="utf-8")
    block = re.search(rf"const {block_name} = \[(.*?)\];", source, re.DOTALL)
    ...
    entry = re.search(rf"{key} => (\d+),", block.group(1))
```
```python
def test_the_mirrored_php_numbers_behind_the_job_ceiling_are_the_real_ones() -> None:
    assert _php_constant_entry(PHP_QUEUE_MAPPER, "LOCK_TIMEOUTS", "KIND_OCR") == OCR_LOCK_TIMEOUT_SECONDS
    assert _php_constant_entry(PHP_QUEUE_SERVICE, "KIND_BATCH", "KIND_OCR") == OCR_CLAIM_BATCH
```
Achtung: der Regex `const {block_name} = \[` trifft `private const KIND_BATCH = [` genau; ein Name wie `KIND_BATCH_INDEX_LANE` braucht einen eigenen Blocknamen (kein Präfix-Konflikt, da `KIND_BATCH = \[` den Suffix ausschließt). Neue Assertion für den Index-Lane-Wert. Rot-Probe nach `test_a_moved_php_number_makes_the_parity_gate_red` (578-594). `test_a_full_ocr_claim_at_the_ceiling_stays_under_the_lock_timeout` (611-617) auf `OCR_ROWS_PER_SLOT` umschreiben.

---

### `tests/test_sandbox.py` (Härtung, Vererbung, ChildKilled)

**Analog:** Reihenfolge-Test per Quelltext (388-394, 413-421):
```python
def test_the_child_hardens_itself_before_the_parsers_load() -> None:
    body = SANDBOX_SOURCE.read_text(encoding="utf-8").split("def _child_main", 1)[1]

    assert body.index("_shed_secrets()") < body.index("from findling.extract.dispatch import ")
    assert body.index("os.setsid()") < body.index("_shed_secrets()")
```
Enkel-Nachweis über `probe("grandchild", ...)` + `/proc` (248-288, `@ONLY_POSIX`, `ONLY_POSIX` Zeile 47-50); für nice im Elternteil `os.getpriority(os.PRIO_PROCESS, pid)`. Fremd-Kill-Test nach `test_an_unexpected_child_death_is_a_verdict_and_not_a_hang` (326-336), der **grün bleiben muss** (Exitcode 70 bleibt `CORRUPT`); neu: `os.kill(worker.pid, signal.SIGKILL)` während `probe("sleep", ...)` -> `ChildKilled`. Fixture `worker` (79-83).

---

### `tests/test_memory_guard.py` / `tests/test_guard.py` / `tests/test_watch.py`

**Analog:** `tests/test_memory_guard.py` Fake-Baum (23-49):
```python
def _tree(root: Path, *, memory_max: str | None, anon: int | None = None, file_cache: int = 10 * GIB) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if memory_max is not None:
        (root / "memory.max").write_text(memory_max + "\n", encoding="ascii")
```
Um `memory.events` (`low 0\nhigh 0\nmax N\noom 0\noom_kill K\n`) erweitern; Fälle aus RESEARCH Testschnitt (kein Limit, v1, Δmax ohne Druck, zwei qualifizierte Ticks, zu dicht, oom_kill, Neustart, Token, Profilwechsel). Für `watch.py` die Runner-Tests `tests/test_embedding_runner.py` als Vorlage (injizierte `clock`/`headroom`, `run_once` ohne Zeit).

---

### `tests/test_poller.py` (Staffel unter N)

**Analog:** `_FakeQueue` (182-254), `_Extractor` (335-367), `_poller(...)` (370-400), Fixtures `writer`/`store` (307-332). `_poller` um `ocr_slots` erweitern; `_Extractor` kann eine Verzögerung/`ChildKilled` als `error` liefern. Sparsam-Pin: Lane `all` erzeugt dieselben `queue.lanes`/`unlocked`-Aufzeichnungen wie heute.

---

### `tests/test_slots_kill.py` (NEU, SC2)

**Analog (teilweise):** `_WorkStock` (test_poller.py 2151-2250) als PHP-treue Zustandsmaschine (retries beim Anspruch, Erstattung bei `unlock`, Quittung löscht); die Regeln werden aus dem PHP-Quelltext gelesen (`_unlock_body`, `_hands_the_delivery_back`, Zeilen 2104-2150). Für den Harness muss der Zustand in eine SQLite-Datei (überlebt SIGKILL des Harness-Prozesses) und ein Lease-Ablauf dazu. Echte Kinder über `probe("sleep", ...)`-artige Dauer; `/proc`-Wartemuster aus `test_group_kill_reaches_a_grandchild`. Nur Linux (`skipif`), unter 60 s (python.yml `timeout-minutes: 15`, Zeile 102).

---

### `scripts/ops/slot_ladder.py` bzw. `ocr_slot_probe.py --mode poller`

**Analog:** `scripts/ops/ocr_slot_probe.py` (Moduldoc 1-52, `Round`-Dataclass 84-97, `cgroup_value` 108-118). Regeln: findling-Import erst in Funktionen (Zeile 49-51), keine Pfade/Texte in der Ausgabe (35-39), Ausgabezeilen `round ... failed_slots N` und `pages_per_second_median X`, die Schritt F von measure.yml parst.

---

### `.github/workflows/measure.yml` (Job `slots`)

**Analog:** Schritt B (533-551) und F (594-630):
```yaml
for combination in "1 0" "2 0,1" "4 0-3"; do
  set -- ${combination}
  docker run --rm --network none --cpuset-cpus "$2" \
    -v "${GITHUB_WORKSPACE}/scripts/ops:/ops:ro" \
    -v "${RUNNER_TEMP}/scan:/scan:ro" \
    --entrypoint /app/.venv/bin/python "${TARGET}" \
    /ops/ocr_slot_probe.py --slots "$1" --rounds 3 --scan /scan/scan-8.pdf \
    | tee "${OUT}/w3-slots-$1.txt"
done
```
Neuer Schritt nach demselben Muster; Faktor-Schritt wie F mit Schwelle 1,05 je Stufe (1->2, 2->4), "unbestimmt" plus `exit 1` bei kaputten Läufen. Korpus-Schritt A (515-531) mit festem Seed erweitern. Action-Pins nicht ändern (`test_workflow_pins.py`).

## Shared Patterns

### Neutrale Zustandsmodule
**Source:** `lane.py` (ganz), `profile.py` 344-415
**Apply to:** `guard.py`, Kappe in `profile.py`
Modul-globaler Zustand, `note_*`-Setter (validieren, nur bei Änderung neu rechnen), `snapshot()` ohne Seiteneffekt, `reset()` nur für Tests, stdlib + config only, loggt nichts.

### Kernel-Leser
**Source:** `memory_guard.py` 21-64
**Apply to:** `memory_events`, Wächter
Pfad als Parameter mit `CGROUP_ROOT`-Default, `except (OSError, ValueError): return None`, nie werfen, nie loggen; Aufruf aus async immer über `asyncio.to_thread`.

### Rückgabe statt Verlust
**Source:** `Poller._abort` (poller.py 1607-1633), `DocumentQueue.unlock` (nc/queue.py 488-515)
**Apply to:** Zeilenbeschnitt, Barriere-Abbruch, Shutdown
Jeder Weg ohne Quittung ruft `unlock` (Erstattung der Auslieferung), `_held` wird danach geleert; gehaltene IDs, die an einen anderen Track gehen, verlassen `_held` sofort.

### Task-Lebenszyklus
**Source:** `EmbedRunner` (embedding.py 1394-1476), Lifespan (main.py 875-886, 988-1044)
**Apply to:** `worker/watch.py`, Pool-Schließen
`arm`/`silence`/`run(stop_event)`/`stand_down`, `_in_flight`-Flag, jede Ausnahme gefangen mit `type(error).__name__`, Shutdown `wait_for(shield(task), timeout=...)`, dann `cancel` + `gather(return_exceptions=True)`.

### Log-Hygiene
**Source:** poller.py Moduldoc 48-50, 719-723
**Apply to:** alle neuen Module
Nur Zähler, Stufen, Ursachencodes und Typnamen; nie Pfad, Titel, Text, Token-Wert. Der bestehende Grep-Test (`_poller_lines`, test_poller.py 2350) gilt auch für neue Zeilen.

### PHP/Python-Paritätsgates
**Source:** test_config.py 544-594, `test_profile_wire.py`
**Apply to:** `KIND_BATCH` je Lane, `LOCK_TIMEOUTS[ocr]` unverändert, `confirmed`-Feld
Wert aus PHP-Quelltext per Regex lesen, Python-Spiegel vergleichen, Rot-Probe über kopierte, geänderte Quelle.

### Sparsam bleibt byte-gleich
**Source:** `test_profile.py` 179-212
**Apply to:** Poller-Schleife bei `S == 1`/Lane `all`, `OCR_CLAIM_BATCH`, `num_threads=1`
Wert-für-Wert-Pins bleiben grün; nice/oom_score_adj sind bewusst keine Sparsam-Abweichung (gelten überall), müssen aber den Pin nicht berühren.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `SlotGate` in `extract/pool.py` | utility | event-driven | Keine größenveränderliche asyncio-Schranke im Code; RESEARCH Muster 1 nutzen |
| Dateibasierte Lease-Warteschlange im Kill-Harness (`tests/test_slots_kill.py`) | test fixture | CRUD, prozessübergreifend | `_WorkStock` ist nur im Speicher und ohne Lease-Ablauf; Persistenz und Ablauf neu nach RESEARCH Testschnitt |

## Metadata

**Analog search scope:** `backend/src/findling/{extract,worker,index,store,nc,api}`, `memory_guard.py`, `profile.py`, `lane.py`, `config.py`, `main.py`; `backend/tests/{test_config,test_sandbox,test_memory_guard,test_poller,test_profile}.py`; `php/lib/{Service,Controller,Db}`, `php/templates/admin.php`, `php/tests/Unit`; `scripts/ops/ocr_slot_probe.py`; `.github/workflows/{measure,python}.yml`
**Files scanned:** 28
**Pattern extraction date:** 2026-09-28
