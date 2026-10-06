# Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 22 (5 neu, 17 geändert)
**Analogs found:** 21 / 22

Alle Pfade relativ zu `C:\Users\Student\nextcloud-search`. Zeilennummern Stand 27.09.2026.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `backend/src/findling/hardware.py` (NEU) | utility (reine Parser + detect) | file-I/O, einmal je Start | `scripts/ops/ocr_slot_probe.py:71-118` (`CGROUP`, `cgroup_value(root=...)`) + `config.py`-Hausregeln | role-match |
| `backend/src/findling/profile.py` (NEU) | service/store (Prozess-Zustand + reiner Resolver) | transform + Prozess-Momentaufnahme | `backend/src/findling/index/rebuild.py:331-404` (`RebuildProgress`, `_PROGRESS`, `rebuild_progress()`, `_note_progress()`) | exact (Zustand) |
| `backend/src/findling/config.py` | config | Konstanten + Env-Leser | selbst: `INDEX_WORKERS` (60-81), `_bounded_int_from_environment` (959-972), `settings()` (1240-1247) | exact |
| `backend/src/findling/nc/client.py` | client-Wrapper | request-response (OCS GET) | `queue_stats()` (414-419), `mounts()` (458-474) | exact |
| `backend/src/findling/nc/queue.py` | service-Wrapper | request-response, Fehler = Rückfallwert | `DocumentQueue.top_up()` (475-501), `_mapping()` (194-201) | exact |
| `backend/src/findling/worker/poller.py` | worker | event-loop je Runde | `run_once()` (731-778), `queue.top_up()`-Aufruf (773) | exact |
| `backend/src/findling/api/status.py` | controller (Route) | request-response, nebenwirkungsfrei | `StatusResponse` (115-225), `_volume()` (269-320), `_of()` (371-435) | exact |
| `backend/src/findling/store/vectors.py` | model/Marke | transform | `embedding_mark()` (246-273), `ELEMENT_TYPE` (83-87) | exact |
| `backend/src/findling/main.py` | Lifespan | Start-Sequenz | Startaussagen 1-3 (688, 748, 760) | exact |
| `php/lib/Controller/ProfileController.php` (NEU) | controller (OCS) | request-response, nur Lesen | `php/lib/Controller/ReconcileController.php` (ganz, 271 Z.) | exact |
| `php/lib/Service/SettingsService.php` | service | CRUD (appconfig lesen) | selbst: `KEY_*` (56-81), `indexTeamFolders()` (217-219), `reject()` (313-319) | exact |
| `php/tests/Unit/ProfileControllerTest.php` (NEU, optional) | test | request-response | `php/tests/Unit/GatewayControllerTest.php` (1-80) | exact |
| `backend/tests/test_hardware.py` (NEU) | test | file-I/O mit tmp_path | Fake-Baum-Idee aus `ocr_slot_probe.py` (`root: Path = CGROUP`); keine bestehende Testdatei | role-match |
| `backend/tests/test_profile.py` (NEU) | test | transform + Zustand | `test_config.py:96-106, 298-305`; Zustand-Reset wie `test_status_endpoint.py:1151-1155` | role-match |
| `backend/tests/test_config.py` | test (Pin) | , | selbst: `test_index_workers_is_a_constant...` (298-305), `test_defaults_are_the_measured_numbers` (96ff.) | exact |
| `backend/tests/test_info_xml_defaults.py` (NEU) oder Abschnitt in `test_config.py` | test (Gleichstand) | file-I/O (XML) | `backend/tests/test_store_metadata.py:108-118, 470-503` (`ElementTree.fromstring`, `BACKEND_INFO`) | role-match |
| `backend/tests/test_status_endpoint.py` | test | request-response | `FIELDS` (74-111), `test_the_state_of_the_engine_is_reported_without_a_state_database` (804-817), `test_the_rebuild_fields_report_the_run_of_this_process` (1143-1159) | exact |
| `backend/tests/test_poller.py` | test (Fakes) | , | `_FakeQueue` (157-185), zweiter Fake (1902-1912) | exact |
| `backend/tests/test_embedding_track.py` | test (Fakes + Marke) | , | `_FakeQueue` (130-150), `ANOTHER_MARK` (1006), Drift-Kette (1119-1142) | exact |
| `backend/tests/test_acl_prefilter.py` / `test_reconcile.py` | test (Fakes) | , | `_OneBatchQueue` (190-212); `_FakeQueue` in test_reconcile (123-146) | exact |
| `backend/tests/test_upgrade_compatibility.py` | test (Gold-Ratchet) | , | Modul-Docstring (1-29), `test_an_index_built_by_this_code_carries_the_marks_of_v1_3` (310-318) | exact |
| `backend/tests/conftest.py` | test-Fixture | , | autouse `forget_the_cutter_notice` (323-336) | exact |
| `backend/appinfo/info.xml` | config (Doku-Satz) | , | `FINDLING_OCR_MAX_PAGES` `<description>` (406-411) | exact |

## Pattern Assignments

### `backend/src/findling/profile.py` (NEU, Prozess-Zustand + Resolver)

**Analog:** `backend/src/findling/index/rebuild.py` Zeilen 331-404. Genau das gesuchte Muster: frozen-slots-Dataclass als Momentaufnahme, Modul-Global mit Ruhezustand, Lese-Funktion für die Statusroute ohne I/O, eine Schreibfunktion mit einer Zuweisung.

```python
@dataclass(frozen=True, slots=True)
class RebuildProgress:
    running: bool
    documents_carried: int
    documents_total: int

_AT_REST: Final = RebuildProgress(running=False, documents_carried=0, documents_total=0)

# The progress of this process, held at module level and nowhere else, after the
# build of engine_state in findling.embed.engine: a function answers the current
# state and there is no second record of it on the volume.
_PROGRESS: RebuildProgress = _AT_REST

def rebuild_progress() -> RebuildProgress:
    """... Read by the status route ... and by nothing that decides anything.
    Nothing is opened and nothing is measured here ..."""
    return _PROGRESS

def _note_progress(progress: RebuildProgress) -> None:
    """Publish the reading of the moment. One assignment, called between bands."""
    global _PROGRESS
    _PROGRESS = progress
```

Übertrag:
- `_HARDWARE: Hardware | None = None` (einmal im Lifespan gesetzt), `_CHOSEN: Profile | None = None` (None = nie gelesen, D-24-02), je eine `note_*()`-Schreibfunktion und ein `snapshot()`-Leser.
- `note_chosen(value)` ignoriert `None` und Werte außerhalb der geschlossenen Menge (letzter Wert bleibt).
- `Profile` als `enum.StrEnum` mit Wire-Namen `economy`/`standard`/`performance` (A5); `PROFILE_NAMES: Final = frozenset(...)` für Queue und PHP-Gleichstand.
- `resolve(profile, hardware, environ) -> Resolution` und `fits(hardware) -> Profile` als reine Funktionen ohne I/O; `effective = min(chosen or ECONOMY, fits(hardware))` (D-24-07).
- Sparsam-Zeile aus den bestehenden Konstanten bauen (`INDEX_WORKERS`, `WRITER_HEAP_BYTES`, `EMBED_BATCH_SIZE`, `OCR_MAX_PAGES`, `OCR_DPI`, `OCR_CLAIM_BATCH`), keine neuen Literale.
- Leistung-Kernterm `C - 1` ohne `- r` (D-24-08); Standard `floor(0.5 * C - r)`.
- Modul-Kopf: Import nur aus `findling.config` (neutral, `worker` darf nicht aus `api` importieren).

---

### `backend/src/findling/hardware.py` (NEU, cgroup-Erkennung)

**Analog:** `scripts/ops/ocr_slot_probe.py` Zeilen 68-118, injizierbarer Wurzelpfad, nie werfend:

```python
CGROUP = Path("/sys/fs/cgroup")

def cgroup_value(file_name: str, key: str, root: Path = CGROUP) -> int | None:
    """One counter out of a flat keyed cgroup file, or None when it cannot be read."""
    try:
        text = (root / file_name).read_text(encoding="ascii")
    except OSError:
        return None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == key and parts[1].isdigit():
            return int(parts[1])
    return None
```

Konkrete Parser (`cpu_quota`, `memory_limit`, `meminfo_bytes`) stehen fertig in `24-RESEARCH.md` Abschnitt "Code Examples" Z. 303-332. `detect(cgroup_root=..., meminfo=..., cpu_count=os.process_cpu_count, machine=platform.machine)`; Kerne = Minimum aus `process_cpu_count()` und `cpu.max`-Quote (gemessen: `process_cpu_count` ignoriert `--cpus`). Schwellen gegen `memory.max` bzw. `MemTotal`, Slotformel gegen `min(memory.max, MemAvailable)`.

**Hausregeln aus `config.py` Kopf (Z. 14-23):** "Unusable input never stops the container" und "The log names variables, never values". Jede unlesbare Datei ergibt `None`, nie eine Ausnahme.

---

### `backend/src/findling/config.py` (neue Konstanten, `settings()` UNVERÄNDERT)

**Analog Konstante mit Herleitung und Tabu:** Z. 60-81

```python
# IDX-08. One indexing worker, always. ...
# ... This is not a tuning knob and deliberately reads no
# environment variable, so that making it one is a code change somebody has to
# defend in review.
INDEX_WORKERS = 1
```

Neue Konstanten (Anteile 0.5/0.4, 1.0/0.6; OCR-Obergrenzen 4/16; `r = 0.25`; Slotkosten 235 MiB; Grundlinie; Reserve 20 %/15 %; Schwellen 6 GB/3 Kerne und 12 GB/6 Kerne als Byte-Konstanten mit benannter Einheit, Pitfall 4) je mit Herleitungskommentar und Quelle (`docs/performance.md:4737-4829`, D-24-03/06/08).

**Analog Env-Leser für "explizit gesetzt":** Z. 959-972

```python
def _bounded_int_from_environment(name: str, default: int, bounds: tuple[int, int]) -> int:
    value = _int_from_environment(name, default)
    low, high = bounds
    if low <= value <= high:
        return value
    LOGGER.warning("%s is outside the range this build was measured for, falling back to the default", name)
    return default
```

Neuer Helfer `_explicit_int(name, default, bounds) -> int | None` darauf aufbauen: `None` bei leer, ungültig oder **gleich dem deklarierten Default** (Pitfall 1, AppAPI injiziert jeden `<default>`). Nie `name in os.environ`.

**Nicht anfassen:** `@lru_cache(maxsize=1) def settings()` (Z. 1240-1247). Docstring dort begründet den Cache; `test_config.py:305` prüft `not hasattr(settings(), "index_workers")`.

---

### `backend/src/findling/nc/client.py` (+ `read_profile`)

**Analog:** Z. 414-419 (GET, Pfad als Stringliteral im Aufruf, Gate A)

```python
async def queue_stats(nc: AsyncNextcloudApp) -> object:
    """Waiting, held right now, and how many files ended as failed."""
    return await nc._session.ocs(
        "GET",
        "/ocs/v2.php/apps/findling/queues/documents/stats",
    )
```

Neu: `read_profile(nc)` mit `"GET", "/ocs/v2.php/apps/findling/profile"`. Rückgabe untypisiert `object` wie `mounts()` (Docstring Z. 466-469 begründet das). Kein Eintrag in `OCS_WRITE_ALLOWLIST` (Kommentar Z. 450-455: "a GET is none"); `test_write_allowlist_has_exactly_four_entries` (`test_readonly_gate.py:578`) bleibt grün.

---

### `backend/src/findling/nc/queue.py` (+ `DocumentQueue.profile`)

**Analog Import-Block:** Z. 41-49 (alphabetische Liste aus `findling.nc.client`, `read_profile` einreihen).

**Analog Kernmuster:** `top_up()` Z. 475-501

```python
    async def top_up(self) -> str:
        """...
        Every exception becomes TOPUP_UNAVAILABLE for the same reason claim
        catches everything: a companion of an older version answers 404 here,
        and a route that does not exist yet must cost one debug line and the
        ordinary backoff, never the poller.
        """
        try:
            answer = await topup_documents(self._nc)
        except Exception:
            # Debug and not a warning, same policy as claim: during an upgrade
            # window (new container, old companion) this fires once per idle
            # pass, ...
            LOGGER.debug("could not ask for a crawl slice")
            return TOPUP_UNAVAILABLE

        payload = _mapping(answer) or {}
        ...
```

`_mapping()` Z. 194-201 wiederverwenden. Fertiger Rumpf für `profile() -> str | None` steht in `24-RESEARCH.md` Z. 336-350.

---

### `backend/src/findling/worker/poller.py` (Profil je Runde lesen)

**Analog:** `run_once()` Z. 741-746

```python
        queue = await asyncio.to_thread(self._open)

        claim = await queue.claim(limit=self._batch_files, max_bytes=self._batch_max_bytes)
        if claim.unavailable:
            self._retreat()
            return RoundResult(ROUND_QUEUE_UNAVAILABLE)
```

Einfügestelle: zwischen `self._open` (741) und `claim` (743): `note_chosen(await queue.profile())` mit Kommentar im Hausstil (warum vor claim: ab Phase 26 hängt die Anspruchsgröße am Profil). Aufrufmuster des Queue-Wrappers wie Z. 773 (`await queue.top_up()`). Keine Profilwerte in Poller/Writer/Sandbox verdrahten.

**Marken-Aufrufer:** Z. 2101 `wanted = embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap)`; Vergleich exakt bei Z. 2108 `if stored != wanted:`. In Phase 24 entweder unverändert lassen (Default `WEIGHTS_INT8`) oder ausdrücklich `weights=WEIGHTS_INT8` übergeben. Keine Normalisierung einbauen.

---

### `backend/src/findling/api/status.py` (+ `profile`-Block)

**Analog Imports:** Z. 81-91; neuer Import `from findling.profile import snapshot` (bzw. Name nach Wahl).

**Analog Prozesswert in `_volume()`:** Z. 302-320 (z. B. `engineState=engine_state()`, `rebuildRunning=progress.running`). Neues Feld dort füllen:

```python
    resolved = settings()
    free, total = resources.disk_bytes()
    progress = rebuild_progress()
    return StatusResponse(
        appVersion=_app_version(),
        engineState=engine_state(),
        ...
        rebuildRunning=progress.running,
```

**Analog Übertrag in `_of()` (Pitfall 2):** Z. 406-409 und 425-429

```python
        # Carried over like the version above: the state of the engine is a
        # property of this process and the state database has nothing to say
        # about it, so it is asked once, in the branch that runs either way.
        engineState=volume.engineState,
        ...
        rebuildRunning=volume.rebuildRunning,
```

Neu: `profile=volume.profile,` mit gleichem Begründungskommentar. Feld als verschachteltes pydantic-Modell `ProfileReport(BaseModel)` mit Defaults (Klassen-Docstring `StatusResponse` Z. 116-122: "Every field defaults"), Feldnamen camelCase wie Bestand (`chosen`, `effective`, `suggested`, `hardware`, `values`, `sources`). Mutable Defaults per `Field(default_factory=...)` (Muster Z. 139-144). Route bleibt nebenwirkungsfrei ("reading it builds nothing and loads nothing", T-07-04).

---

### `backend/src/findling/store/vectors.py` (Marke mit Präzision)

**Analog (zu ändern):** Z. 246-273

```python
EMBEDDING_MODEL: Final = "multilingual-e5-small"

def embedding_mark(model: str, *, tokens: int) -> str:
    """The value of the ``embedding_version`` mark for one build.

    Four things decide whether a stored vector still means what this container
    thinks it means, and all four are in here: the model, the quantisation of
    its output, the number of dimensions, and the token cap the chunks were cut
    at. ...
    """
    return f"{model}/{ELEMENT_TYPE}/{EMBEDDING_DIMENSIONS}/{tokens}"
```

Zielform (fertig in `24-RESEARCH.md` Z. 208-222): Parameter `weights: str = WEIGHTS_INT8`, int8 bytegleich `base`, fp32 `f"{base}/{weights}"`, Unbekanntes `ValueError`. Docstring ergänzen: `ELEMENT_TYPE` (Z. 83-87) ist der Typ der gespeicherten Vektoren, nicht die Gewichtspräzision. Konstanten `WEIGHTS_INT8`, `WEIGHTS_FP32`, `WEIGHT_PRECISIONS` als `Final` im Stil von Z. 81/87.

---

### `backend/src/findling/main.py` (vierte Startaussage)

**Analog:** Z. 750-760

```python
    # The third startup statement, and the only one that is about the
    # environment rather than about the volume: it is therefore said on a shared
    # volume as well, ...
    # Through a worker thread like the two above it. ...
    await asyncio.to_thread(warn_on_uncovered_languages)
```

Direkt danach und vor `stop_indexing = asyncio.Event()` (Z. 765): `note_hardware(await asyncio.to_thread(detect))` als vierte Startaussage, außerhalb des `if shared_volume.other`-Zweigs (Hardware gilt unabhängig vom Volume). Fehlerbehandlung nach Z. 724-732 (`except Exception as error:` + nur `type(error).__name__` loggen), obwohl `detect()` selbst nicht werfen soll. Log-Zeile ohne Pfade.

---

### `php/lib/Controller/ProfileController.php` (NEU)

**Analog:** `php/lib/Controller/ReconcileController.php` (eigene Klasse, nur Lesen, eigene `rejectForeignCaller`-Kopie). Besser als QueueController, weil ebenfalls eigenständiger Lese-Controller.

**Header + Konstruktor** (Z. 1-14, 68-75):
```php
<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\SettingsService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

class ProfileController extends OCSController {
	public function __construct(
		IRequest $request,
		private SettingsService $settingsService,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}
```

**Route** (Muster Z. 87-94 bzw. `QueueController.php:323-339`): Attribut-Trio voll qualifiziert (Klassendocblock Z. 43-47 begründet: Gate B zählt textuell), `rejectForeignCaller()` als erste Anweisung, `try/catch (\Throwable $e)` mit statischem Log-Satz und `['exception' => $e]` (Z. 105-114). Fertiger Rumpf in `24-RESEARCH.md` Z. 353-364.

**Guard** (Z. 241-253, kopieren, Log-Text anpassen):
```php
	private function rejectForeignCaller(): ?DataResponse {
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}

		$this->logger->warning('Findling: reconcile called by a foreign ExApp', ['app' => $callerAppId]);

		return new DataResponse(
			['error' => 'This route is reserved for the Findling backend.'],
			Http::STATUS_FORBIDDEN,
		);
	}
```

Gate B (`test_php_trust_boundary.py:74, 268`) globbt `php/lib/Controller/*.php` automatisch; Schranke `>= 13` (Z. 314) bleibt grün.

---

### `php/lib/Service/SettingsService.php` (+ `KEY_PROFILE`, `profile()`)

**Analog Schlüssel:** Z. 56-59 (`public const KEY_... = '...';` mit Docblock, warum public).

**Analog Leser mit Default:** Z. 217-219
```php
	public function indexTeamFolders(): bool {
		return $this->appConfig->getValueBool(Application::APP_ID, self::KEY_INDEX_TEAM_FOLDERS, true);
	}
```
Neu: `getValueString(Application::APP_ID, self::KEY_PROFILE, 'economy')`, Prüfung gegen geschlossene Menge (`public const PROFILES = ['economy', 'standard', 'performance'];`), Unbekanntes ergibt Default plus `$this->reject()`.

**Analog Ablehnung ohne Wert** (Z. 313-319):
```php
	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: refused a settings value that is outside its range',
			['rejected' => $this->rejected],
		);
	}
```
Begründung occ als ungeprüfter Zweitzugang steht bereits in `save()`-Docblock Z. 262-265. `saveProfile()` erst Phase 27. Uninstall braucht nichts (`deleteApp`).

---

### `php/tests/Unit/ProfileControllerTest.php` (NEU, CI-only, lokal kein PHP)

**Analog:** `php/tests/Unit/GatewayControllerTest.php` Z. 1-80: `#[CoversClass(...)]`, `final class ... extends TestCase`, Mocks in `setUp()`, `backendAppId()` per Reflection (Z. 63-69), `controller(string $callerAppId)` mit gestubbtem `getHeader` (Z. 75-79). Fälle: eigener Aufrufer liefert `['profile' => ...]`, fremder 403. `SettingsService` ist `final`: statt Mock ein echtes `SettingsService` mit gemocktem `IAppConfig` bauen.

---

### `backend/tests/test_config.py` (Sparsam-Pin, PROF-02)

**Analog:** Z. 298-305
```python
def test_index_workers_is_a_constant_and_not_an_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_INDEX_WORKERS", "8")
    settings.cache_clear()

    # Serial indexing is architecture (IDX-08): OCR and embedding peaks must not
    # meet on a 4 GB box. Turning this into a knob would be a silent regression.
    assert INDEX_WORKERS == 1
    assert not hasattr(settings(), "index_workers")
```
und `test_defaults_are_the_measured_numbers` (Z. 96ff.: Literal-Asserts gegen `settings()`). Pin: jede Sparsam-Zeile gegen Literal UND Konstante (Liste in `24-RESEARCH.md` Z. 173). Kann auch in `test_profile.py` stehen; das `hasattr`-Tabu bleibt unverändert.

---

### `backend/tests/test_info_xml_defaults.py` (NEU, Gleichstand info.xml gegen config.py)

**Analog:** `backend/tests/test_store_metadata.py` Z. 108-118 und 470-475
```python
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_INFO = REPO_ROOT / "backend" / "appinfo" / "info.xml"
...
        info = ElementTree.fromstring(source)  # noqa: S314
```
Variablen liegen unter `<environment-variables><variable><name>/<default>` (`backend/appinfo/info.xml` Z. 358-496, 16 Einträge). Test: explizite Abbildung Name -> Konstante (z. B. `FINDLING_OCR_MAX_PAGES` -> `OCR_MAX_PAGES`, `FINDLING_OCR_DPI` -> `OCR_DPI`, `FINDLING_MAX_FILE_BYTES` -> `MAX_FILE_BYTES`), plus Vollständigkeitsprüfung, dass jede deklarierte Variable in der Abbildung steht (Anti-Vakuität wie `>= 13` in Gate B). Strings (`de,en`, `deu+eng+fra`, `true`) gegen die jeweiligen Konstanten in ihrer Wire-Form.

---

### `backend/tests/test_status_endpoint.py`

**Analog `FIELDS`:** Z. 74-111, Satz wird an zehn Stellen exakt geprüft; `"profile"` mit Kommentar im Stil Z. 94-98 ergänzen.

**Analog ohne state.db:** Z. 804-817 (`volume`-Fixture, `assert set(answer) == FIELDS`).

**Analog Prozesswert setzen und zurücksetzen:** Z. 1151-1155
```python
    rebuild._note_progress(RebuildProgress(running=True, documents_carried=40, documents_total=120))
    try:
        answer = _status(client, sign("admin"))
    finally:
        rebuild._note_progress(RebuildProgress(running=False, documents_carried=0, documents_total=0))
```
Je ein Test mit `indexed_volume` (Zweig `_of()`) und mit `volume` (Zweig `_volume()`); Schrumpfungsfall: Hardware-Fake klein, gewählt `performance`, erwartet `effective` kleiner und beide Werte gemeldet (D-24-07).

---

### `backend/tests/test_poller.py`, `test_embedding_track.py`, `test_acl_prefilter.py`, `test_reconcile.py` (Fakes, Pitfall 7)

**Analog:** `test_poller.py` Z. 172-185
```python
        # What the top-up of an empty pass answers, and how often it was asked.
        # Idle by default, because that is the state every existing test means:
        # a queue whose script ran out has nothing left to crawl.
        self.topups = 0
        self.topup_answer = TOPUP_IDLE
    ...
    async def top_up(self) -> str:
        self.topups += 1
        return self.topup_answer
```
Neu in jedem Fake: `self.profile_answer: str | None = None` plus `async def profile(self) -> str | None`. Betroffene Fakes (alle, die `run_once` durchlaufen):
- `test_poller.py:157` `_FakeQueue` und `:1902ff.` (zweiter Stock-Fake mit `top_up` Z. 1909)
- `test_embedding_track.py:130` `_FakeQueue`
- `test_acl_prefilter.py:190` `_OneBatchQueue` (hat kein `top_up`, braucht `profile()` trotzdem, weil der Aufruf VOR `claim` liegt)
- `test_reconcile.py:123` `_FakeQueue` nur, falls der Reconcile-Pfad `run_once` erreicht (prüfen; er ruft laut Docstring nur `stats`/`requeue`)

Neue Poller-Tests: Fake wirft, Erststart -> Sparsam; Fake liefert `standard`, danach wirft -> `standard` bleibt (D-24-02).

**Analog Marken-Verhaltenstest:** `test_embedding_track.py` Z. 999-1006 (`_wanted_mark()`, `ANOTHER_MARK`) und Z. 1119-1142 (Drift-Kette `forget_all -> write mark -> requeue`). Neu: gespeicherte 1.3-Marke `"multilingual-e5-small/int8/384/1024"`, Leerlaufrunde, `chain == []` und `queue.requeues == []`; Gegenprobe mit fp32-Marke löst die Kette aus.

---

### `backend/tests/test_upgrade_compatibility.py` (Gold-Ratchet der Marke)

**Analog:** Modul-Docstring Z. 15-18 ("A red test here is not a repair, it is a question for the owner") und Z. 310-318:
```python
def test_an_index_built_by_this_code_carries_the_marks_of_v1_3() -> None:
    findings = drift_findings(expected_versions("digest-egal", GOLD_LANGUAGES), GOLD_V1_3)

    assert findings == [], findings
```
Neu: `assert embedding_mark(EMBEDDING_MODEL, tokens=1024) == "multilingual-e5-small/int8/384/1024"` als Gold-Wert mit Owner-Frage-Begründung (5-h-Reindex).

---

### `backend/tests/conftest.py` (Zustand-Reset)

**Analog:** Z. 323-336
```python
@pytest.fixture(autouse=True)
def forget_the_cutter_notice() -> Iterator[None]:
    """No case inherits the failed cutter build of the case before it.
    ... Cleared on both sides, so the order the
    suite happens to run in cannot be read off any answer.
    """
    note_cutter_failure(None)
    yield
    ...
```
Neu: `forget_the_profile_state()` setzt Hardware und gewähltes Profil beidseitig zurück (eigene `reset()`-Funktion in `profile.py`).

---

### `backend/appinfo/info.xml` (nur Beschreibungssatz)

**Analog:** Z. 406-411, `<description>` von `FINDLING_OCR_MAX_PAGES`. Einen kurzen Satz zur Überstimmungsregel ergänzen (ein vom Default abweichender Wert überstimmt das Profil). Store-Text-Regel: kurz. Keine neuen Variablen, keine Default-Änderung (Gleichstandstest!).

## Shared Patterns

### Fehlertoleranz "Route fehlt im alten Companion"
**Source:** `backend/src/findling/nc/queue.py:475-501`
**Apply to:** `DocumentQueue.profile()`, Poller-Aufruf
Jede Exception -> Rückfallwert, `LOGGER.debug` ohne Werte, nie den Poller stoppen.

### Prozess-Zustand für die Statusroute
**Source:** `backend/src/findling/index/rebuild.py:346-404`, Testmuster `test_status_endpoint.py:1151-1155`, Reset `conftest.py:323-336`
**Apply to:** `profile.py`, `status.py`, Tests
Modul-Global + Ruhezustand + Leser ohne I/O + Schreiber mit einer Zuweisung; Tests setzen und resetten im `finally` bzw. per autouse-Fixture.

### Logs ohne Werte / Nie werfen
**Source:** `config.py:14-23`; `main.py:726-732` (`type(error).__name__`); PHP `SettingsService::reject()` (313-319), `ReconcileController.php:105-114`
**Apply to:** `hardware.py`, `profile.py`, `config.py`-Helfer, `main.py`, PHP-Controller und -Service

### ExApp-Routenschutz (Gate B)
**Source:** `ReconcileController.php:87-94, 241-253`
**Apply to:** `ProfileController.php`
Attribut-Trio voll qualifiziert, `rejectForeignCaller()` als erste Anweisung, eigene private Kopie.

### Geschlossene Profilmenge beidseitig
**Source:** Container `PROFILE_NAMES` (neu), PHP `SettingsService::PROFILES` (neu); Stil `config.py:87-90` (geschlossene Sprachmenge)
**Apply to:** `profile.py`, `queue.py`, `SettingsService.php`. Empfehlung: ein Gleichstandstest, der die PHP-Konstante textuell gegen `PROFILE_NAMES` prüft (Muster Gate B liest PHP-Quellen per Regex).

### Qualitätsgates
`[tool.vulture] min_confidence = 80` (`backend/pyproject.toml:122-124`): ungenutzte Dataclass-Felder (60 %) werden nicht gemeldet, Pitfall 8 betrifft höchstens ungenutzte Funktionen. ruff 0.16.8 inkl. `format --check`, pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `backend/tests/test_hardware.py` | test | file-I/O (Fake-cgroup per `tmp_path`) | Kein bestehender Test mit Fake-cgroup-Baum; `ocr_slot_probe.py` ist ein Ops-Skript ohne Tests. Muster aus `24-RESEARCH.md` Pattern 5 (Z. 187-204) nutzen: Dateien `cpu.max`, `memory.max`, `meminfo` schreiben, `cpu_count=lambda: 16` injizieren; die drei gemessenen `docker run`-Varianten als parametrisierte Fälle. |

## Metadata

**Analog search scope:** `backend/src/findling/**`, `backend/tests/**`, `php/lib/Controller/`, `php/lib/Service/`, `php/tests/Unit/`, `scripts/ops/`, `backend/appinfo/info.xml`, `backend/pyproject.toml`
**Files scanned:** 24
**Pattern extraction date:** 2026-09-27
