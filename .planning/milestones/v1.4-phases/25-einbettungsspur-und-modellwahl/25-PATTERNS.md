# Phase 25: Einbettungsspur und Modellwahl - Pattern Map

**Mapped:** 2026-09-28
**Files analyzed:** 41 (8 neu, 33 geändert; l10n als 1 Posten mit 16 Dateien gezählt)
**Analogs found:** 40 / 41

Alle Pfade relativ zu `C:\Users\Student\nextcloud-search`. Zeilennummern Stand 28.09.2026 (nach Phase 24). Wo 24-PATTERNS.md noch gilt, wird darauf verwiesen statt zu wiederholen.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `backend/src/findling/worker/embedding.py` (NEU: `EmbeddingTrack` + `EmbedRunner`) | worker (zweiter Task + Spur-Eigentümer) | event-loop je Runde, Queue claim/ack/unlock | Runner: `worker/reconcile.py` (ganz); Track: `worker/poller.py:1230-1373, 1685-1951, 2019-2198` | exact (beides) |
| `backend/src/findling/precision.py` (NEU) | store (Prozess-Zustand, neutral) | transform + Momentaufnahme | `backend/src/findling/profile.py:282-337` (`_CHOSEN`, `note_chosen`, `snapshot`, `reset`) | exact |
| `backend/src/findling/memory_guard.py` (NEU) | utility (reine Funktion + Live-Leser) | file-I/O (cgroup, meminfo) | `backend/src/findling/hardware.py` (ganz) | exact |
| `backend/src/findling/embed/weights.py` (NEU) | utility (Datei-Seite fp32) | file-I/O, Digest, atomar | `index/wordlist.py:143-254, 338-342` (Digest, Cache-Key size/mtime_ns), `worker/poller.py:310-331` (`_HashingSink`), `:2381-2398` (`_clear_scratch`) | role-match |
| `backend/src/findling/worker/poller.py` | worker | event-loop | selbst: `run_once` 732-901, `_abort` 1953-1979, `_open` 1644-1683 | exact |
| `backend/src/findling/embed/model.py` | model (ONNX-Halter) | request-response, Sperre | selbst: `release()` 634-675, `_artifacts_present` 291-299 | exact |
| `backend/src/findling/embed/engine.py` | service (Prozess-Halter) | Sperre + Identitätsprüfung | selbst: `shared_model` 144-168, `release_if_idle` 413-500 | exact |
| `backend/src/findling/nc/client.py` | client-Wrapper | request-response + Streaming | `claim_documents` 327-343, `_stream_file` 221-254, `new_gateway_client` 201-207 | exact |
| `backend/src/findling/nc/queue.py` | service-Wrapper | request-response, Fehler = Rückfallwert | `ClaimResult` 164-175, `claim` 365-405, `profile` 505-524 | exact |
| `backend/src/findling/index/writer.py` | model (Index-Leser) | file-I/O | selbst: `stored_body` 353-386, `free_bytes`/`disk_is_tight` 388-409 | exact |
| `backend/src/findling/profile.py` | service (Resolver) | transform | selbst: `ocr_slots` 153-176, `_compute` 270-279 | exact |
| `backend/src/findling/config.py` | config | Konstanten | selbst: `MAIN_PROCESS_BASELINE_BYTES` 862, `PROFILE_*_EMBED_SLOTS` 873/886, Settings 1399-1405 | exact |
| `backend/src/findling/store/vectors.py` | model (Marke) | transform | selbst: `embedding_mark` 271-314 | exact |
| `backend/src/findling/api/resources.py` | service (Leseseite) | request-response | selbst: Z. 265 (Marke), Z. 714 (`open_index` Leseseite) | exact |
| `backend/src/findling/api/status.py` | controller (Route) | request-response, nebenwirkungsfrei | `ProfileReport` 152-166, `_profile_report` 289-322, `_volume` 366-418, `_of` 469-538 | exact |
| `backend/src/findling/main.py` | Lifespan | Start/Abbau-Sequenz | `_guarded_reconcile` 340-357, `_release_when_idle` 360-431, `_stand_the_poller_down` 434-481, `_arm_the_poller` 484-496, Lifespan 781-957 | exact |
| `php/lib/Controller/QueueController.php` | controller (OCS) | request-response | selbst: `getDocuments` 104-133, Kind-Prüfung 296-303, `badKind` 535-548 | exact |
| `php/lib/Service/QueueService.php` | service | CRUD (claim) | selbst: `KIND_BATCH` 168-175, `claim` 212-298 | exact |
| `php/lib/Db/QueueMapper.php` | model | , (nur Kommentar LOCK_TIMEOUTS) | selbst: 109-143 | exact |
| `php/lib/Controller/ProfileController.php` | controller (OCS) | request-response, nur Lesen | selbst (ganz, 95 Z.) | exact |
| `php/lib/Service/SettingsService.php` | service | appconfig lesen | selbst: `KEY_PROFILE`/`PROFILES`/`PROFILE_DEFAULT` 84-108, `profile()` 261-284, `reject()` 365 | exact |
| `php/lib/Service/AdminViewService.php` | service (Admin-Ansicht) | transform (Container-Antwort) | selbst: `backend()` 1828-1869, `optionalCounter` 1901-1905, `engineState` 1929-1931, Coverage 1379-1400 | exact |
| `php/templates/admin.php` + `php/js/admin.js` | component (Statusfläche) | Render + Poll | `admin.php:424-458` (Block `findling-semantic`), `admin.js:390-420` (`semanticBlock`) | exact |
| `php/l10n/*.json` + `*.js` (16 Dateien, 8 Sprachen) | config (Katalog) | , | bestehende Katalogschlüssel; Gates `test_admin_ui_contract.py:2184-2400, 2566-2618` | exact |
| `php/tests/Unit/QueueServiceTest.php` | test | CRUD | selbst (bestehende Datei) | exact |
| `php/tests/Unit/ProfileControllerTest.php` | test | request-response | selbst (ganz, 147 Z.) | exact |
| `backend/tests/test_embedding_runner.py` (NEU) | test (Nebenläufigkeit, T1-T8) | event-loop mit Fakes | `test_embedding_track.py:131-178` (`_FakeQueue`), `test_reconcile.py` | role-match |
| `backend/tests/test_memory_guard.py` (NEU) | test | file-I/O mit tmp_path | `backend/tests/test_hardware.py:1-60` (Fake-cgroup-Baum) | exact |
| `backend/tests/test_precision.py` (NEU) | test (Zustandsautomat, T9) | transform + Zustand | `backend/tests/test_profile.py` + Reset-Fixture `conftest.py` | exact |
| `backend/tests/test_weights.py` (NEU) | test (Download/Digest) | Streaming mit MockTransport | `backend/tests/test_gateway_client.py:87-117` (`_Gateway`, `httpx.MockTransport`) | exact |
| `backend/tests/test_profile_wire.py` | test (Parität PHP/Python) | Regex über PHP-Quelle | selbst (ganz, 54 Z.) | exact |
| `backend/tests/test_queue_client.py` | test (Draht) | request-response | selbst: Z. 157-159 (exakte Parameter) | exact |
| `backend/tests/test_poller.py`, `test_embedding_track.py`, `test_acl_prefilter.py` | test (Fakes, Pitfall 12) | , | `test_poller.py:207-229, 2005-2041`, `test_embedding_track.py:144-168`, `test_acl_prefilter.py:199-216` | exact |
| `backend/tests/test_embed_engine.py` | test (Idle-Guard T10) | Sperre | selbst | exact |
| `backend/tests/test_status_endpoint.py` | test | request-response | `FIELDS` Z. 74ff., Muster aus 24-PATTERNS.md | exact |
| `backend/tests/test_readonly_gate.py` | test (Gate A) | AST | `INVARIANT_2_EXCEPTIONS` 77-121 | exact |
| `backend/tests/test_measurement_scripts.py` | test (Baum-Hash-Pins) | , | `PHP_FILES_TODAY`/`PHP_TREE_HASH_TODAY` 670-671, `PACKAGE_FILES_TODAY`/`..._TREE_HASH_TODAY` ~1285-1286 mit Kommentarzeile je Plan | exact |
| `backend/tests/test_admin_ui_contract.py` | test (Katalog-Gate) | , | Schlüsselzahl `== 205` Z. 2355 | exact |
| `backend/tests/test_config.py` | test (Pins, Parität) | , | Z. 312-320 (INDEX_WORKERS), 560-600 (KIND_BATCH/LOCK_TIMEOUTS) | exact |
| `docs/embeddings.md`, `docs/profiles.md`, `docs/admin-page.md` | docs | , | `docs/embeddings.md` Abschnitt Marke/Präzision (560-711) | exact |
| `docs/measurements/2026-09-fp32-speicher/` (NEU, Plan 25-01) | Messdaten | Batch | Verzeichnisstil `docs/measurements/2026-09-grundlast-fein/rohdaten/` | partial (kein Code) |

## Pattern Assignments

### `backend/src/findling/worker/embedding.py` (NEU) : `EmbedRunner` (Task 2)

**Analog:** `backend/src/findling/worker/reconcile.py` (ganz). Genau das Muster: zweiter Task, nichts im Konstruktor öffnen, eigener Client über `client_factory`, `arm`/`silence`/`run`/`run_once`/`aclose`.

**Imports + Typ-Fabriken** (reconcile.py Z. 44-61, 134-140):
```python
from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Final

from findling.config import settings
from findling.nc import client as nc_client
from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import KIND_CONTENT, KIND_DELETE, DocumentQueue
from findling.store.repo import Store, open_store

LOGGER = logging.getLogger("findling.worker.reconcile")

ClientFactory = Callable[[], AsyncNextcloudApp]
QueueFactory = Callable[[AsyncNextcloudApp], DocumentQueue]
```
Übertrag: Logger `findling.worker.embedding`; Runden-Zustände als `Final`-Strings (Z. 63-71: "Strings rather than an enum ... closed list of readable names"), z. B. `LANE_PARKED`, `ROUND_EMPTY`, `ROUND_WORKED`, `ROUND_PAUSED`. `worker` darf nicht aus `api` importieren (Kommentar `poller.py:454-458`).

**Konstruktor ohne I/O** (reconcile.py Z. 190-241):
```python
class Reconcile:
    """...
    Nothing is opened in the constructor. The lifespan builds this object while
    the backend may still be disabled, and a container that opened a second write
    connection to the state database at that point would hold it without ever
    comparing anything.
    """

    def __init__(self, *, store: Store | None = None,
                 client_factory: ClientFactory = nc_client.create_app_client,
                 queue_factory: QueueFactory = DocumentQueue, ...) -> None:
        self._store = store
        self._owns_store = store is None
        ...
        self._client: AsyncNextcloudApp | None = None
        self._queue: DocumentQueue | None = None
        self._cooldown = 0.0
        self._armed = asyncio.Event()
```

**Lifecycle** (reconcile.py Z. 245-269):
```python
    @property
    def armed(self) -> bool:
        return self._armed.is_set()

    def arm(self) -> None:
        self._armed.set()

    def silence(self) -> None:
        self._armed.clear()

    async def aclose(self) -> None:
        """Give back the state connection, if this object opened one."""
        if not self._owns_store:
            return
        store, self._store = self._store, None
        if store is not None:
            store.close()
```
Zusätzlich vom Poller übernehmen: `stand_down(budget=...)` mit `_in_flight`-Flag (`poller.py:604-666`) und `unlock_held()` (`poller.py:668-679`), weil der Runner beim Rebuild und beim Abbau Zeilen zurückgeben muss (Research Pattern 5 Punkt 4/5).

**Schleife** (reconcile.py Z. 273-292, plus `_in_flight` aus `poller.py:713-721`):
```python
    async def run(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            if not self._armed.is_set():
                await _first_of(self._armed.wait(), stop_event.wait())
                continue
            try:
                await self.run_once()
            except Exception as error:
                kind_of_failure = type(error).__name__
                LOGGER.error("reconcile round ended in an unexpected %s", kind_of_failure)
                self._back_off()
            await _pause(self._tick + self._cooldown, stop_event)
```
**WICHTIG (Pitfall 3):** Der Runner darf im Generalfang gehaltene Zeilen nicht liegen lassen. Die Runde selbst behandelt `sqlite3.Error` und `_DiskTight` mit `_abort`-Semantik (unten). `_first_of` und `_pause` sind in reconcile.py Z. 674-697 bewusst kopiert ("Ten lines twice are cheaper"); dasselbe Kopiermuster gilt hier.

**Runden-Rumpf:** Skizze in `25-RESEARCH.md` "Runner-Runde mit Abbruchsemantik" (Z. 421-457). Abbruch nach `poller.py:1953-1979`:
```python
    async def _abort(self, queue: DocumentQueue, claimed: int, *, state: str = ROUND_GATEWAY_UNAVAILABLE) -> RoundResult:
        await queue.unlock(sorted(self._held))
        self._held.clear()
        self._back_off()
        return RoundResult(state, claimed=claimed)
```
Docstring-Kern dort übernehmen: "this method unlocks on every path out of it and never simply returns" (DI-05-23).

**Backoff** (reconcile.py Z. 660-666): `_back_off` verdoppelt bis 3600 s, `_reset_cooldown` auf 0.

**Eigene state.db-Verbindung, nie anlegen** (reconcile.py Z. 172-187):
```python
def _open_state() -> Store | None:
    """... Deliberately does not create it and deliberately seeds no version marks.
    Both of those belong to the poller ..."""
    path = settings().state_db
    if not path.exists():
        return None
    return open_store(path)
```

---

### `backend/src/findling/worker/embedding.py` (NEU) : `EmbeddingTrack` (Spur-Eigentümer)

**Analog:** die heutigen Poller-Methoden, die umziehen (verhaltensgleicher Refactor, Plan 25-04). Keine neue Logik erfinden, Docstrings mitnehmen.

| Heute in `poller.py` | Zeilen | Wird im Track |
|---|---|---|
| `_needs_vectors` | 1230-1261 | `needs_vectors` (öffentlich, Poller fragt) |
| `_embed_the_body` | 1263-1373 | `embed_row(job, done)` |
| `_wire_the_second_track` | 1685-1754 | Track-Öffnung (eigene vectors.db-Verbindung) |
| `_build_the_cutter` | 1756-1852 | unverändert |
| `release_cutter` | 1860-1904 | unverändert, `busy` = Zeile in Arbeit egal welcher Treiber |
| `_cutter_cooling_down`, `_embed_ready` | 1906-1951 | unverändert |
| `_keep_the_vector_stock_in_step` bis `_next_backlog_band` | 2019-2198 | Markenschritt; `wanted` aus aktiver Präzision |

**Die drei Stellen, die sich ändern MÜSSEN** (Anti-Pattern aus Research):
```python
# poller.py:1293 heute über den Writer:
if self._writer_or_die().disk_is_tight():
    raise _DiskTight
# -> Helfer über Verzeichnis + min_free_bytes (index/writer.py:388-409 als Vorlage)

# poller.py:1328 heute über die Poller-state.db-Verbindung:
await asyncio.to_thread(self._store_or_die().replace_acl, job.file_id, _acl_users(job))
# -> eigene Track-Verbindung (reconcile._open_state-Muster)

# poller.py:1330 heute über das Writer-Objekt:
body = await asyncio.to_thread(self._writer_or_die().stored_body, job.file_id)
# -> freie Funktion stored_body(index, schema, file_id) über eigenen Lese-Handle
```

**Marke aus der aktiven Präzision** (poller.py:2111, IN-02):
```python
wanted = embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap)
```
-> `embedding_mark(EMBEDDING_MODEL, tokens=..., weights=<precision.active>)`; in Plan 25-02 vorerst ausdrücklich `weights=WEIGHTS_INT8`.

**Driftkette bleibt in dieser Reihenfolge** (poller.py:2161-2173): `forget_all()` -> `write_meta(EMBEDDING_BACKLOG_MARK, BACKLOG_START)` -> `write_meta(EMBEDDING_MARK, wanted)` -> `_next_backlog_band`. Der Engine-Tausch (Pattern 8d) hängt sich zwischen Marke und Band ein, unter der Track-Sperre, ohne Zeile in Arbeit.

**Konstruktor-Injektion erhalten:** `Poller(vectors=, chunker=, model=)` (poller.py:439-441) reicht an den Track durch, damit `test_embedding_track.py` im Refactor-Plan grün bleibt.

---

### `backend/src/findling/precision.py` (NEU, neutraler Zustand)

**Analog:** `backend/src/findling/profile.py`, Zustand Z. 282-337 und Enum Z. 89-98. Modul-Kopf-Regel Z. 35-37 wörtlich übernehmen ("neutral: stdlib, findling.config ... logs nothing, neither ... names nor environment values").

```python
class Profile(enum.StrEnum):
    """The wire names. Display texts come from the catalogues (phase 27)."""

    ECONOMY = "economy"
    STANDARD = "standard"
    PERFORMANCE = "performance"


PROFILE_ORDER: Final = (Profile.ECONOMY, Profile.STANDARD, Profile.PERFORMANCE)
PROFILE_NAMES: Final = frozenset(p.value for p in Profile)
```
Übertrag: `Precision(enum.StrEnum)` mit `INT8 = "int8"`, `FP32 = "fp32"`; `PRECISION_NAMES: Final = frozenset(...)`. Werte müssen mit `WEIGHTS_INT8`/`WEIGHTS_FP32` aus `store/vectors.py` übereinstimmen (Import von dort oder Gleichstandstest).

```python
_HARDWARE: Hardware | None = None
_CHOSEN: Profile | None = None
_SNAPSHOT: ProfileSnapshot = _compute(None, None)

def note_chosen(value: str | None) -> None:
    """... None and anything outside PROFILE_NAMES change nothing (D-24-02) ..."""
    global _CHOSEN, _SNAPSHOT
    if value is None or value not in PROFILE_NAMES:
        return
    chosen = Profile(value)
    if chosen is _CHOSEN:
        return
    _CHOSEN = chosen
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN)

def snapshot() -> ProfileSnapshot:
    return _SNAPSHOT

def reset() -> None:
    """Back to the resting state. For tests only; the container never forgets."""
```
Übertrag: `note_chosen_precision(value)` mit derselben Semantik; zusätzlich Übergangserkennung int8 -> fp32 in diesem Prozess (D-25-14: Download-Auslöser) als eigenes Feld, `active` und `verdict` (geschlossene Menge `""`, `downloading`, `fp32_unavailable`, `fp32_not_in_economy`, `fp32_on_a_tight_box`) als Momentaufnahme-Dataclass `frozen=True, slots=True` (Muster `ProfileSnapshot` Z. 254-267 inkl. abgeleiteter Property wie `downgraded`). Startzustand NICHT aus Default (Pitfall 6): `active` bleibt `None`/unentschieden, bis Marke + verifizierte Datei gelesen sind. Reset-Fixture in `conftest.py` nach dem Profil-Muster.

---

### `backend/src/findling/memory_guard.py` (NEU, RAM-Bedingung)

**Analog:** `backend/src/findling/hardware.py` (ganz). Modul-Docstring-Stil Z. 1-21 ("neutral on purpose: stdlib only ... every path injectable ... never raises. It logs nothing").

**Leser-Bausteine wiederverwenden, nicht kopieren** (hardware.py Z. 44-100):
```python
def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="ascii").strip()
    except (OSError, ValueError):
        return None

def memory_limit(root: Path) -> int | None:
    """The memory.max limit in bytes, or None for "max" or garbage."""
    return _positive_int(_read(root / "memory.max"))

def meminfo_bytes(path: Path, key: str) -> int | None:
    """One field of /proc/meminfo in bytes (the file speaks kB), or None."""
```
Neu: `anon`-Zähler aus `memory.stat` (flache Schlüsseldatei; Parser-Vorlage `scripts/ops/ocr_slot_probe.py` `cgroup_value(file_name, key, root)`, zitiert in 24-PATTERNS.md Z. 83-97). Öffentliche Signatur mit Default-Pfaden wie `detect(cgroup_root=CGROUP_ROOT, meminfo=MEMINFO)` (hardware.py Z. 182-187). `CGROUP_ROOT`/`MEMINFO` aus `hardware.py` importieren (eine Schreibweise). Reine Funktion `admits(headroom, reserve, activation, load_cost) -> bool` getrennt vom Leser, damit Phase 26 darauf baut. NIE `memory.current` (Pitfall 7).

---

### `backend/src/findling/embed/weights.py` (NEU, fp32-Datei-Seite, kein httpx)

**Analog Digest-Cache an Dateiidentität:** `index/wordlist.py` Z. 214-254
```python
# The key is the identity of the artifact, not its path alone: the recorded
# digest plus the size and the modification time of the file that carries it.
_CacheKey = tuple[str, str, int, int]
_CACHED_ENTRIES: dict[_CacheKey, list[str]] = {}
_CACHE_LOCK = threading.Lock()
...
    return (str(target), recorded, status.st_size, status.st_mtime_ns)
```
Übertrag: verifizierter Digest je Prozess an `(size, mtime_ns)` merken, unter `threading.Lock`; Absenz ist nie ein Schlüssel.

**Analog Hash beim Streamen:** `worker/poller.py` Z. 310-331 (`_HashingSink`: `self._digest = hashlib.sha256()`, `write` aktualisiert und schreibt durch). Für die Sink-Seite des Downloads direkt nutzbar als Vorlage.

**Analog Aufräumen von Resten:** `worker/poller.py` Z. 2381-2398
```python
def _discard(scratch: Path) -> None:
    with contextlib.suppress(OSError):
        scratch.unlink(missing_ok=True)

def _clear_scratch(directory: Path) -> None:
    """Only the files this module names. A cleanup that swept the directory would
    one day sweep something else that lives in the volume."""
    removed = 0
    for entry in directory.glob(f"*{SCRATCH_SUFFIX}"):
        _discard(entry)
        removed += 1
    if removed:
        LOGGER.info("removed %d scratch files from an earlier run", removed)
```
Übertrag: nur `model.onnx.part` im fp32-Verzeichnis löschen; Rückweg D-25-09 löscht `model.onnx` per `unlink(missing_ok=True)`.

**Ablagepfad:** neben `dict_dir` (`config.py:1399-1405`: `dict_dir=root / "dict"`), also `root / "models" / "multilingual-e5-small-fp32" / "model.onnx"` als neues Settings-Feld oder abgeleitet aus `_storage_root()` (`config.py:1249-1260`).

**Gate A (Pitfall 9):** `mkdir`/`makedirs` sind in `FORBIDDEN_IDENTIFIERS` (`test_readonly_gate.py:63-75`). Entweder neues Paar `("embed/weights.py", "mkdir")` in `INVARIANT_2_EXCEPTIONS` (Z. 113-121) mit Begründungsabsatz im Stil Z. 85-112 ("invariant 1 keeps nc_py_api and httpx out of that module ..."), oder Verzeichnis anderswo anlegen. `os.replace`, `Path.unlink`, `os.fsync` sind erlaubt.

**Konstanten** (`config.py`-Stil mit Herleitungskommentar, siehe 24-PATTERNS.md "config.py"): `FP32_SHA256`, `FP32_BYTES = 470_268_510`, `FP32_ASSET_URL`, `FP32_EXTRA_BYTES` (Wert aus Plan 25-01).

---

### `backend/src/findling/nc/client.py` (+ `lane`, + `fetch_release_asset`)

**Analog claim** (Z. 327-343): Pfad bleibt Stringliteral im Aufruf (Kommentar Z. 314-319, Gate liest `ast.Constant`).
```python
async def claim_documents(nc: AsyncNextcloudApp, *, limit: int, max_bytes: int) -> object:
    return await nc._session.ocs(
        "GET",
        "/ocs/v2.php/apps/findling/queues/documents",
        params={"n": limit, "max_bytes": max_bytes},
    )
```
Neu: `lane: str | None = None`; nur setzen, wenn nicht None (Research "Claim mit Spur und Echo", Z. 405-413). `test_queue_client.py:159` prüft `kwargs["params"] == {"n": 32, "max_bytes": 64}` exakt: Sparsam-Draht bleibt bytegleich.

**Analog Streaming mit Deckel** (Z. 221-254):
```python
    async with client.stream("GET", gateway_url(file_id), params=..., headers=app_api_headers(header_user)) as response:
        if response.status_code >= _FIRST_ERROR_STATUS:
            raise NextcloudException(response.status_code, reason=...)
        async for chunk in response.aiter_bytes(CHUNK_SIZE):
            written += len(chunk)
            if written > cap:
                raise FileTooLargeError(...)
            await asyncio.to_thread(fp.write, chunk)
```
**Abweichung für `fetch_release_asset` (Pitfall 8):** eigener Client OHNE `app_api_headers` (keine Zugangsdaten), `follow_redirects=True, max_redirects=3` statt `new_gateway_client` (Z. 201-207, dort bewusst `follow_redirects=False` wegen AppAPI-Credential). Host-Allowlist `github.com`, `release-assets.githubusercontent.com`, nur `https`. `verify` darf `_certificate_setting()` (Z. 181-188) NICHT übernehmen (NPA_NC_CERT gilt der Nextcloud, nicht GitHub); `trust_env` bleibt Default. Timeout über `_timeout()` (Z. 191-198) ist vertretbar. Skizze fertig in 25-RESEARCH.md Z. 477-496. Modul-Docstring (Z. 13-16, 22-30) um einen Absatz "one GET to a fixed URL, no credential, only on an admin action" ergänzen; `__all__` (Z. 45-69) erweitern. Kein Eintrag in `OCS_WRITE_ALLOWLIST` (GET).

---

### `backend/src/findling/nc/queue.py` (+ `lane_honored`, + Präzision)

**Analog Ergebnis-Dataclass** (Z. 164-175):
```python
@dataclass(frozen=True, slots=True)
class ClaimResult:
    jobs: tuple[QueueJob, ...] = ()
    discarded: int = 0
    unavailable: bool = False
```
Neu: `lane_honored: bool = False` mit Default, damit alle Fakes, die `ClaimResult(...)` bauen, weiter kompilieren.

**Analog Echo-Prüfung:** in `claim()` (Z. 387-390) VOR dem frühen `return ClaimResult()` für leere Antworten auswerten, sonst meldet ein leerer, aber echo-tragender Anspruch `lane_honored=False`:
```python
        payload = _mapping(answer)
        entries = _mapping(payload.get("files")) if payload is not None else None
        if not entries:
            return ClaimResult()
```

**Analog Präzision lesen** (Z. 505-524):
```python
    async def profile(self) -> str | None:
        try:
            answer = await read_profile(self._nc)
        except Exception:
            LOGGER.debug("could not read the profile")
            return None

        value = (_mapping(answer) or {}).get("profile")
        if isinstance(value, str) and value in PROFILE_NAMES:
            return value
        return None
```
Neu: eine Antwort, zwei Werte, jeder fällt einzeln auf `None` (Research 8a). Entweder `profile()` liefert ein kleines Dataclass-Paar, oder `profile()` bleibt und die Antwort wird einmal gelesen und intern zwischengespeichert. Signaturänderung zieht alle Fakes mit (Pitfall 12). Geschlossene Mengen `LANES` (`all`, `index`, `embed`) als `Final` frozenset neben `KINDS` (Z. 72-78).

---

### `backend/src/findling/embed/model.py` (Idle-Guard + Gewichtspfad)

**Analog (zu ändern):** `release()` Z. 634-675
```python
    def release(self) -> bool:
        global _UNLOAD_COUNT

        with self._lock:
            if self._engine is None:
                return False
            if self._in_flight:
                return False
            self._engine = None
            _UNLOAD_COUNT += 1

        _return_free_pages_to_the_system()
        return True
```
Zielform: `release(self, *, idle_seconds: float | None = None)`, zusätzliche Prüfung von `self._last_use` (Feld Z. 405, gesetzt Z. 533) unter `self._lock` (Skizze 25-RESEARCH.md Z. 459-475). Docstring-Absatz "Three remembered facts stay" bleibt.

**Gewichtspfad:** `_artifacts_present` (Z. 291-299) prüft heute `model_dir / MODEL_FILE` und `model_dir / TOKENIZER_FILE` im selben Verzeichnis; `_load` öffnet `self._model_dir / MODEL_FILE` (Z. 603). Neu: Konstruktor (Z. 382) nimmt `weights_path` (Default `model_dir / MODEL_FILE`, damit int8 unverändert) und `precision`. Kommentar Z. 326-332 ("IDX-08 keeps the two apart in time and not in space") mit PAR-04-Hinweis nachtragen.

---

### `backend/src/findling/embed/engine.py` (Halter-Schlüssel + Tausch)

**Analog Halter** (Z. 144-168):
```python
def shared_model() -> EmbeddingModel:
    global _ENGINE
    resolved = settings()
    with _LOCK:
        if _ENGINE is not None and _ENGINE[0] == resolved.embed_model_dir:
            return _ENGINE[1]
        model = EmbeddingModel(resolved.embed_model_dir, batch_size=..., sequence_len=...)
        _ENGINE = (resolved.embed_model_dir, model)
        return model
```
Neu: Schlüssel `(tokenizer_dir, weights_path)`; `swap_engine(weights_path, precision)` unter `_LOCK` nach demselben "nothing is loaded by this call"-Prinzip.

**Analog Freigabe** (Z. 463-490): `release_if_idle` liest `last_use` zweimal (vor und unter `_LOCK`, WR-02-Kommentar Z. 437-447). Neu: `held.release(idle_seconds=ttl_seconds)` übergeben; Docstring-Satz "is a v1.4 backlog note" (Z. 445-447) auf "closed in phase 25" umschreiben. `_held(model_dir)` bekommt den neuen Schlüssel.

---

### `backend/src/findling/index/writer.py` (`stored_body` als Funktion, Plattenboden)

**Analog:** Z. 353-386 (Methode nutzt nur `self._index` und `self._schema`, nie den `IndexWriter`):
```python
        self._index.reload()
        searcher = self._index.searcher()
        hits = searcher.search(Query.term_query(self._schema, FIELD_FILE_ID, file_id), limit=1).hits
        if not hits:
            return None
        _score, address = hits[0]
        values = searcher.doc(address).to_dict().get(FIELD_BODY_DE, [])
        return str(values[0]) if values else None
```
Als freie Funktion `stored_body(index, schema, file_id)` herausziehen, Methode delegiert (Docstring zum U64-Term bleibt an der Funktion). Plattenboden (Z. 388-409) analog als freie Funktion über `(directory, min_free_bytes)`; Docstring "Two calls to shutil.disk_usage with two paths would be two answers about one volume" begründet: gleiches Verzeichnis `resolved.index_dir` verwenden. Der Track-Index-Handle kommt aus `open_index` wie die Leseseite (`api/resources.py:714`); `open_index` legt das Verzeichnis an (`index/open.py:164`), der Track darf es erst öffnen, wenn der Poller es angelegt hat.

---

### `backend/src/findling/profile.py` (fp32-Mehrbedarf im Speicherterm)

**Analog (zu ändern):** Z. 173-176
```python
    budget = share * memory
    reserve = reserve_share * budget
    memory_term = math.floor((budget - reserve - MAIN_PROCESS_BASELINE_BYTES) / OCR_SLOT_COST_BYTES)
    return max(1, min(core_term, memory_term, cap))
```
Neu: `- FP32_EXTRA_BYTES`, wenn fp32 gewünscht und honoriert; `ocr_slots`, `_profile_values`, `_compute` (Z. 270-279) bekommen den Präzisionsparameter. Neutralität (nur `findling.config`, `findling.hardware`) wahren: Präzision als Wert übergeben, nicht `precision.py` von hier aus importieren, wenn das einen Zyklus erzeugt. `PROFILE_*_EMBED_SLOTS` (config.py 873/886) bleibt (D-25-12).

---

### `backend/src/findling/store/vectors.py` + `api/resources.py` (IN-02)

**Analog:** `vectors.py:271` `def embedding_mark(model: str, *, tokens: int, weights: str = WEIGHTS_INT8)`. Default entfernen; beide Aufrufer übergeben ausdrücklich:
- `worker/poller.py:2111` (bzw. nach 25-04 im Track)
- `api/resources.py:265` `marks[EMBEDDING_MARK] = embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap)`

Docstring Z. 291-294 fordert es bereits ("weights has to be the precision of the model that was ACTUALLY loaded"). Gold-Wert-Test `test_upgrade_compatibility.py` (int8-Marke bytegleich) bleibt grün.

---

### `backend/src/findling/api/status.py` (+ `ModelReport`, `LaneReport`)

**Analog verschachteltes Modell** (Z. 152-166):
```python
class ProfileReport(BaseModel):
    """... ``chosen`` and ``effective`` are two fields on purpose (D-24-07) ..."""

    chosen: str | None = None
    effective: str = "economy"
    suggested: str = "economy"
    downgraded: bool = False
    hardware: HardwareReport = Field(default_factory=HardwareReport)
```
**Analog Feld in `StatusResponse`** (Z. 279-285, Kommentar-Stil "A process value like engineState, so the state database knows nothing of it"), **Leser ohne I/O** (Z. 289-322 `_profile_report`: "Nothing is measured, loaded or written here", T-07-04), **setzen in `_volume()`** (Z. 412 `profile=_profile_report(),`), **übertragen in `_of()`** (Z. 527-531):
```python
        # Carried over like the engine state: the profile is a value of this
        # process and the state database has nothing to say about it. Left out
        # here, it would vanish on every installation that has indexed anything
        # (24-RESEARCH.md, Pitfall 2).
        profile=volume.profile,
```
Neu: `model=volume.model,` und `lane=volume.lane,` mit gleichem Kommentar. `reembedRunning` braucht den Cursor `embedding_backlog`: der gehört zur state.db und darf daher in `_of()` aus `marks = store.read_meta()` (Z. 480) gelesen werden, nicht in `_volume()`. Fortschritt über bestehendes `embedded` (`_embedded()` Z. 421-466) gegen `indexed`.

---

### `backend/src/findling/main.py` (zweiter Task, Abbau, Freigabe)

**Analog Wächter um den Task** (Z. 340-357 `_guarded_reconcile`): `_guarded_embedding(runner, stop_event)` identisch, `CancelledError` zuerst neu werfen, sonst nur Typname loggen.

**Analog Start** (Z. 794-805):
```python
    global _RECONCILE
    stop_reconcile = asyncio.Event()
    repairing: asyncio.Task[None] | None = None
    if settings().reconcile_enabled:
        _RECONCILE = default_reconcile()
        repairing = asyncio.create_task(_guarded_reconcile(_RECONCILE, stop_reconcile))
```
plus `active_reconcile()`-Zugriff (Z. 184-186) als `active_embedding()`. Arming überall, wo heute `(active_poller(), active_reconcile())` iteriert wird: `enabled_handler` Z. 275-281 und Lifespan Z. 860-863.

**Analog Abbau** (Z. 921-947): `wait_for(shield(task), timeout=...)`, sonst `cancel()` + `gather(return_exceptions=True)`, dann `with contextlib.suppress(Exception): await runner.unlock_held()`, dann `aclose()`, Modul-Global auf `None`.

**Rebuild** (Z. 434-496): `_stand_the_poller_down` und `_arm_the_poller` müssen den Runner mit herunterfahren bzw. bewaffnen (gleiches `run_coroutine_threadsafe(..stand_down(budget=STAND_DOWN_SECONDS), loop)`-Muster Z. 472-481).

**Freigabe-Task** (Z. 408-417, Pitfall 4):
```python
            poller = active_poller()
            if poller is not None and poller.busy:
                continue
            if await asyncio.to_thread(release_if_idle, ttl_seconds) and poller is not None:
                await asyncio.to_thread(poller.release_cutter)
```
-> `track.busy` fragen und `track.release_cutter()` rufen; Docstring Z. 381-388 entsprechend anpassen.

**Hardware vor den Tasks** (Z. 764-779) bleibt unverändert die vierte Startaussage; Präzisions-Startzustand gehört NICHT in den Lifespan-Start mit Netz (D-24-05: Start lädt nie etwas), sondern in den ersten Markenschritt des Tracks.

---

### `php/lib/Controller/QueueController.php` (`lane` + Echo + 400)

**Analog Route** (Z. 104-133):
```php
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/queues/documents')]
	public function getDocuments(int $n = self::DEFAULT_BATCH_FILES, int $max_bytes = self::DEFAULT_BATCH_BYTES): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		$limit = max(1, min(self::MAX_BATCH_FILES, $n));
		$budget = max(self::MIN_BATCH_BYTES, min(self::MAX_BATCH_BYTES, $max_bytes));

		try {
			$files = $this->queueService->claim($limit, $budget);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not hand out a batch', ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['files' => $files]);
	}
```
**Analog geschlossene Liste** (Z. 296-303): `if (!is_string($kind) || !in_array($kind, QueueMapper::KINDS, true)) { return $this->badKind(); }`
**Analog 400 ohne Wert** (Z. 541-548):
```php
	private function badKind(): DataResponse {
		$this->logger->warning('Findling: rejected a requeue with an unknown job kind');

		return new DataResponse(
			['error' => 'Unknown job kind.'],
			Http::STATUS_BAD_REQUEST,
		);
	}
```
Neu: dritter Parameter `string $lane = QueueService::LANE_ALL`, `badLane()` nach `badKind`, Antwort `['files' => $files, 'lane' => $lane]`. Docblock Z. 93-103 um den Echo-Grund ergänzen (Dispatcher verwirft unbekannte Parameter still, K6). Attribut-Trio bleibt voll qualifiziert (Gate B zählt textuell); `rejectForeignCaller` bleibt erste Anweisung.

---

### `php/lib/Service/QueueService.php` (`LANES`, `claim(..., $lane)`)

**Analog:** `claim()` Z. 212-298, Artenschleife Z. 241-247:
```php
		foreach (QueueMapper::KINDS as $kind) {
			if ($rows <= 0) {
				break;
			}

			$batch = min(self::KIND_BATCH[$kind] ?? $limit, $rows);
			foreach ($this->queueMapper->claimBatch($batch, $budget, $kind) as $row) {
```
Neu: `public const LANE_ALL = 'all'; LANE_INDEX = 'index'; LANE_EMBED = 'embed'; public const LANES = ['all', 'index', 'embed'];` (eine Zeile, wie `PROFILES`, für den textuellen Paritätstest). In der Schleife nur filtern (`index` überspringt `KIND_EMBED`, `embed` überspringt alle anderen); Reihenfolge D-04 und `KIND_BATCH` (Z. 168-175) unverändert, Paritätstest `test_config.py:560-567` bleibt grün. Docblock Z. 189-211 ergänzen.

**`QueueMapper.php:109-143`:** nur Kommentar zu `LOCK_TIMEOUTS[embed]` ("embed row travels in the same claim as OCR" gilt nur noch für Spur `all`), Wert bleibt.

---

### `php/lib/Service/SettingsService.php` + `php/lib/Controller/ProfileController.php` (Präzision)

**Analog Schlüssel + Menge + Default** (SettingsService Z. 84-108):
```php
	public const KEY_PROFILE = 'profile';

	/**
	 * Has to stay identical to PROFILE_NAMES in backend/src/findling/profile.py.
	 * A parity test on the Python side compares the two textually, which is why
	 * this list keeps exactly this one line spelling.
	 */
	public const PROFILES = ['economy', 'standard', 'performance'];

	public const PROFILE_DEFAULT = 'economy';
```
**Analog Leser** (Z. 270-284):
```php
	public function profile(): string {
		$stored = $this->appConfig->getValueString(Application::APP_ID, self::KEY_PROFILE, self::PROFILE_DEFAULT);

		if (!in_array($stored, self::PROFILES, true)) {
			$this->reject();

			return self::PROFILE_DEFAULT;
		}

		return $stored;
	}
```
Neu: `KEY_MODEL_PRECISION = 'model_precision'`, `PRECISIONS = ['int8', 'fp32']`, `PRECISION_DEFAULT = 'int8'`, `modelPrecision(): string` identisch gebaut. occ-Hinweis im Docblock wie Z. 88-90 (`occ config:app:set findling model_precision --value=fp32`).

**ProfileController** (Z. 54-72): Antwort `['profile' => ..., 'precision' => $this->settingsService->modelPrecision()]` im selben `try`; die 500-Antwort (Z. 68-70) trägt weiterhin keinen Wert (D-24-02). Klassendocblock Z. 15-32 und Methodendocblock Z. 42-50 um das zweite Feld ergänzen. Keine neue Route (Gate B, Read-only-Gate unverändert).

---

### `php/lib/Service/AdminViewService.php` + `php/templates/admin.php` + `php/js/admin.js` + `php/l10n/*` (D-25-13)

**Analog Durchreichen** (`backend()` Z. 1828-1869): neue Felder wie `engineState` behandeln, also geschlossene Liste statt `text()` (Z. 1929-1931):
```php
	public static function engineState(mixed $value): ?string {
		return is_string($value) && in_array($value, self::ENGINE_STATES, true) ? $value : null;
	}
```
Übertrag: `precisionActive`/`precisionVerdict` gegen geschlossene Mengen, `null` wenn der Container nicht meldet (älterer Container, T-07-03-Argument Z. 1806-1813). Docblock-Zahl "twenty-five keys" (Z. 1800) nachziehen.

**Analog Statuszeile** (`admin.php:424-458`, Block `findling-semantic`): eine neue `<p class="settings-hint" id="findling-semantic-model">` neben `findling-semantic-engine` (Z. 458); Text über `$l->t('...', [...])` mit Platzhaltern `%1$s` wie Z. 438. Script-Gegenstück in `semanticBlock` (`admin.js:390-420`): `text('findling-semantic-model', t('findling', '...').replace('%1$s', ...))` wie Z. 406-408, `shown(...)` wie Z. 417-420.

**Kataloge:** neuer Schlüssel in allen 16 Dateien (8 Sprachen, je `.json` + `.js`). Gates: `test_every_catalogue_carries_the_same_keys` (`test_admin_ui_contract.py:2358`), Platzhalter-Parität (Z. 2566), Seitenbruch (Z. 2618), und die harte Zahl `assert len(keys_of["de.json"]) == 205` (Z. 2355) muss mitgezogen werden.

---

### `backend/tests/test_embedding_runner.py` (NEU)

**Analog Fake:** `test_embedding_track.py:131-178`
```python
class _FakeQueue:
    """The four queue calls, answered from a script and recorded."""

    def __init__(self, *batches: ClaimResult) -> None:
        self._batches = list(batches)
        self.claims = 0
        self.acknowledged: list[tuple[list[int], dict[int, str]]] = []
        self.unlocked: list[list[int]] = []
        self.requeues: list[tuple[list[int], str]] = []
        self.profile_answer: str | None = None

    async def claim(self, *, limit: int, max_bytes: int) -> ClaimResult:
        del limit, max_bytes
        self.claims += 1
        return self._batches.pop(0) if self._batches else ClaimResult()

    async def unlock(self, ids: Any) -> CallResult:
        self.unlocked.append(list(ids))
        return CallResult(ok=True, count=len(ids))
```
Neu: `claim(..., lane: str | None = None)` zeichnet `lane` auf; Fake-Embedder nach `test_embedding_track.py:115-128` (`embed_passages` mit `calls`-Liste) um Start/Ende-Zeitstempel erweitern (T1/T2-Recorder). Hardware injizieren per `profile.note_hardware(Hardware(... cores=4, 16 GB ...))` (Pitfall 11). T3 mit `pytest.mark.skipif(sys.platform != "linux" or (os.process_cpu_count() or 1) < 2, ...)`.

**Pitfall 12:** dieselbe `lane`-Signatur in `test_poller.py:214, 2015`, `test_embedding_track.py:150`, `test_acl_prefilter.py:205`; Profil-Fakes (`test_poller.py:207, 2005`, `test_embedding_track.py:144`, `test_acl_prefilter.py:199`) liefern zusätzlich die Präzision, im selben Plan wie die Signaturänderung.

---

### `backend/tests/test_memory_guard.py` (NEU)

**Analog:** `test_hardware.py:15-60`
```python
def _meminfo(path: Path, total_kb: int = MEM_TOTAL_KB, available_kb: int = MEM_AVAILABLE_KB) -> Path:
    path.write_text(f"MemTotal:       {total_kb} kB\n...MemAvailable:   {available_kb} kB\n", encoding="ascii")
    return path

def _v2_tree(root: Path, cpu_max: str, memory_max: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cpu.max").write_text(cpu_max + "\n", encoding="ascii")
    (root / "memory.max").write_text(memory_max + "\n", encoding="ascii")
    return root
```
Neu: `memory.stat` mit `anon <bytes>`-Zeile und einer großen `file`-Zeile (Seitencache), um Pitfall 7 zu beweisen; parametrisiert wie Z. 48-60. Modul-Docstring-Stil Z. 1-13 ("no real /sys is touched, which is why this runs on Windows too").

---

### `backend/tests/test_weights.py` (NEU)

**Analog:** `test_gateway_client.py:87-117`
```python
class _Gateway:
    def __init__(self, *, status: int = 200, chunks: list[bytes] | None = None) -> None:
        ...
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._status >= 400:
            return httpx.Response(self._status, text="refused")
        ...

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handle))
```
Übertrag: Handler antwortet 302 von `github.com` auf `release-assets.githubusercontent.com`, dann Bytes; Fälle: richtiger Digest, falscher Digest (Datei verworfen, kein `.part`-Rest), fremder Umleitungshost (abgelehnt), Überlänge (Deckel), keine AppAPI-Header in `request.headers`, Sideload mit richtigem Digest (kein Request). `fetch_release_asset` muss dafür einen injizierbaren Client oder Transport annehmen (Muster `fetch_file_stream(..., client=...)`, `nc/client.py:257-296`).

---

### `backend/tests/test_profile_wire.py` (Paritäten `PRECISIONS`, `LANES`)

**Analog:** ganze Datei (54 Z.):
```python
SETTINGS_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "SettingsService.php"

_PROFILES = re.compile(r"public const PROFILES = \[(.*?)\];", re.DOTALL)
_DEFAULT = re.compile(r"public const PROFILE_DEFAULT = '(\w+)';")
_QUOTED = re.compile(r"'(\w+)'")

def test_each_constant_is_found_exactly_once() -> None:
    source = _source()
    assert len(_PROFILES.findall(source)) == 1
    assert len(_DEFAULT.findall(source)) == 1
```
Neu: `_PRECISIONS`, `_PRECISION_DEFAULT` gegen `PRECISION_NAMES` und `"int8"`; `LANES` aus `QueueService.php` gegen `nc.queue.LANES`, jeweils mit Anti-Vakuität "found exactly once".

---

### `backend/tests/test_status_endpoint.py`, `test_config.py`, `test_embed_engine.py`, `test_measurement_scripts.py`, `test_readonly_gate.py`

- `test_status_endpoint.py`: `FIELDS` um `"model"`, `"lane"` erweitern; je ein Test über `volume` (Zweig `_volume`) und `indexed_volume` (Zweig `_of`); Zustand setzen/zurücksetzen im `finally` (Muster 24-PATTERNS.md Z. 397-404). IN-03-Parität `PROFILE_VALUE_KEYS` gleich mitnehmen.
- `test_config.py`: INDEX_WORKERS-Tabu (Z. 312-320) und KIND_BATCH/LOCK_TIMEOUTS (Z. 560-600) unverändert grün; neue Konstanten (`FP32_BYTES`, `FP32_SHA256`, `FP32_EXTRA_BYTES`, `EMBED_CLAIM_BATCH`) als Literal-Pins.
- `test_embed_engine.py`: T10, Einbettung zwischen zweiter Lesung und `release()` per Monkeypatch einschieben, Freigabe liefert `False`.
- `test_measurement_scripts.py`: jeder Plan aktualisiert die Pins mit einer Kommentarzeile im Stil "Moved on 2026-09-2x by plan 25-0y ... One file came and none went, so PACKAGE_FILES_TODAY moves to NN." Vier neue Python-Module (`worker/embedding.py`, `precision.py`, `memory_guard.py`, `embed/weights.py`) erhöhen `PACKAGE_FILES_TODAY`; PHP-Änderungen verschieben `PHP_TREE_HASH_TODAY` (Z. 671), `PHP_FILES_TODAY` (Z. 670) bleibt ohne neue PHP-Datei. Nach jedem Wellen-Merge neu messen (Pitfall 10).
- `test_readonly_gate.py`: nur falls `embed/weights.py` ein Verzeichnis anlegt, neues Paar in `INVARIANT_2_EXCEPTIONS` (Z. 113-121) mit eigenem Begründungsabsatz; `test_write_allowlist_has_exactly_four_entries` bleibt grün (alles neue ist GET).

---

### `php/tests/Unit/ProfileControllerTest.php` + `QueueServiceTest.php`

**Analog:** `ProfileControllerTest.php` ganz. Staging-Muster Z. 55-62 für den zweiten Schlüssel erweitern:
```php
	private function storedProfile(?string $value): void {
		$this->appConfig->method('getValueString')->willReturnCallback(
			static fn (string $app, string $key, string $default = ''): string => ($value !== null && $key === SettingsService::KEY_PROFILE) ? $value : $default,
		);
	}
```
-> Callback mit Map `[KEY_PROFILE => ..., KEY_MODEL_PRECISION => ...]`. Erwartete Antworten `['profile' => 'standard', 'precision' => 'int8']`; Fall "Wert außerhalb der Menge wird int8 und nicht geloggt" nach Z. 93-107; 500 ohne Wert nach Z. 109-130 (auch `PRECISIONS` im Negativ-Assert). `QueueServiceTest.php`: Spur `embed` liefert nur embed, `index` nie embed, `all` wie 1.3; Controller-Test: unbekannte `lane` -> 400, Echo in jeder Antwort. PHPUnit läuft nur in CI.

## Shared Patterns

### Zweiter Nebenläufer im Prozess
**Source:** `worker/reconcile.py:190-292`, `main.py:340-357, 794-805, 921-947`
**Apply to:** `worker/embedding.py`, `main.py`
Nichts im Konstruktor öffnen; `arm`/`silence`/`run`; Generalfang loggt nur `type(error).__name__`; Lifespan: eigenes `asyncio.Event`, `_guarded_*`-Hülle, Abbau mit `wait_for(shield(...))`, `cancel`, `unlock_held`, `aclose`.

### Zeilen zurückgeben statt Verdikt (DI-05-23)
**Source:** `worker/poller.py:1953-1979` (`_abort`), `nc/queue.py:448-475` (`unlock` mit Rückerstattung)
**Apply to:** Runner-Runde, Hauptschleife bei `sqlite3.Error`, fehlendes Echo, Gate schließt mitten im Anspruch
Jeder Ausstieg ohne Quittung ruft `unlock(sorted(held))`, leert `_held`, `_back_off()`.

### Fehlertoleranz "Route/Feld fehlt im alten Companion"
**Source:** `nc/queue.py:477-524` (`top_up`, `profile`)
**Apply to:** `lane_honored`, Präzisionsfeld, `fetch_release_asset`-Verdikt
Jede Exception -> Rückfallwert, `LOGGER.debug` ohne Werte; geschlossene Menge prüfen, Unbekanntes wie Fehler behandeln.

### Prozess-Zustand für die Statusroute
**Source:** `profile.py:282-337`, `api/status.py:279-322, 412, 527-531`
**Apply to:** `precision.py`, Lane-Zustand des Runners, `status.py`
Modul-Global + Ruhezustand + Leser ohne I/O + Schreiber mit einer Zuweisung + `reset()` für Tests; in `_volume()` setzen UND in `_of()` übertragen.

### Geschlossene Mengen beidseitig mit textuellem Paritätstest
**Source:** `SettingsService.php:94-101` (eine Zeile), `test_profile_wire.py`
**Apply to:** `PRECISIONS`, `LANES`
PHP-Konstante in genau einer Zeile, Python-`frozenset`, Regex-Test mit "found exactly once".

### ExApp-Routenschutz (Gate B) und 400 ohne Wert
**Source:** `ProfileController.php:51-58, 81-93`, `QueueController.php:104-111, 541-548`
**Apply to:** `getDocuments` mit `lane`, Profilantwort mit `precision`
Attribut-Trio voll qualifiziert, `rejectForeignCaller()` erste Anweisung, Ablehnungstext statisch, Eingabe nie im Log.

### Logs ohne Werte, blockierendes nie auf dem Loop
**Source:** `config.py:14-23`, `worker/poller.py:41-46, 1296-1313` (`asyncio.to_thread`), `nc/client.py:249-253`
**Apply to:** alle neuen Python-Module
Typnamen und Zähler, nie Pfade, Digests oder Werte; Datei-IO, Digest über 470 MB, SQLite und Modellload in `asyncio.to_thread`.

### Qualitätsgates
ruff 0.16.8 inkl. `format --check`, pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture `--min-confidence 80` (`backend/pyproject.toml:122-124`). Baum-Hash-Pins je Plan nachziehen (Pitfall 10).

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `docs/measurements/2026-09-fp32-speicher/` (Plan 25-01) | Messdaten | Batch | Kein Code; nur Verzeichnis- und Rohdatenstil der bestehenden Messordner (`docs/measurements/2026-09-grundlast-fein/rohdaten/`). Messmethode (RssAnon-Sprung int8 gegen fp32, je drei Läufe, im lokalen Abbild `:dev`) steht in 25-RESEARCH.md Plan-Schnitt Welle 0. |

Teil-Lücke ohne direktes Vorbild: die gegenseitige Ausschluss-Mechanik (Track-Sperre `asyncio.Lock` plus Park-`asyncio.Event` zwischen Hauptschleife und Runner). Nächstes Vorbild ist `Poller.stand_down` (`poller.py:604-666`, Flag-Warten mit Budget) und `_first_of` (`reconcile.py:680-688`); die Semantik selbst steht in 25-RESEARCH.md Pattern 3.

## Metadata

**Analog search scope:** `backend/src/findling/{worker,nc,embed,index,store,api}/`, `backend/src/findling/{profile,hardware,config,main}.py`, `backend/tests/`, `php/lib/{Controller,Service,Db}/`, `php/templates/`, `php/js/`, `php/l10n/`, `php/tests/Unit/`
**Files scanned:** 31
**Pattern extraction date:** 2026-09-28
