# Phase 23: Härtung und Store-Einreichung 1.3.0 - Pattern Map

**Mapped:** 2026-09-26
**Files analyzed:** 31 (neu oder geändert)
**Analogs found:** 29 / 31

Alle Zeilenangaben beziehen sich auf den Arbeitsbaum vom 26.09.2026 (nach Merge 257caac). Code-Auszüge sind wörtlich übernommen; Prosa deutsch, Bezeichner englisch.

## File Classification

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `backend/src/findling/embed/engine.py` | service | event-driven (Warmlauf) | selbst: `query_may_load` 367-406, `warm_wanted` 505-534, `warm` 537-582 | exact (Umbau am Ort) |
| `backend/src/findling/embed/model.py` | service | request-response | selbst: `_embed` 511-572 | exact |
| `backend/src/findling/api/search.py` | controller | request-response | selbst: Handler 359-409, Einwortregel 311-332 | exact |
| `backend/src/findling/api/snippets.py` | controller | request-response | `api/search.py:311-320` (Einwortregel) | exact |
| `backend/tests/test_embed_engine.py` | test | event-driven | selbst: 842-853, 1197-1211, 1263-1281 | exact |
| `backend/tests/test_embed_model.py` | test | request-response | selbst: 512-547 (`may_load=False`-Fälle) | exact |
| `backend/tests/test_search_endpoint.py` | test | request-response | selbst: 690-770 (`_count_the_warm_runs`, `_WARM_TASKS`) | exact |
| `backend/tests/test_snippets_endpoint.py` | test | request-response | selbst: 398-457 (`_LoadSwitchModel`) | exact |
| `.github/workflows/integration.yml` (Schritt "The paraphrase finds the document with the second track", ab 1719) | config/CI | request-response | selbst: `/status`-Abfrage `engineState` 1811-1820 | exact |
| `backend/tests/probe_image_search.py` | test/probe | batch | selbst: `ask` 284-300, `offline_step` 331-349 | exact |
| `backend/src/findling/tools/one_load.py` | utility (Messwerkzeug) | batch | selbst: `drive_the_search_side` 277-287, `measure` 320-395 | exact |
| `backend/tests/test_one_load.py` | test | batch | selbst: 159-173, 250-266, 285-294 | exact |
| `.github/workflows/resilience.yml` (Kommentar 1430-1442) | config/CI | batch | selbst | exact |
| `docs/admin-page.md:138`, `docs/embeddings.md:760-840`, `backend/appinfo/info.xml:469` | doc | , | selbst | exact |
| `php/lib/Migration/Version001300Date2026092X000000.php` (NEU) | migration | batch/CRUD | `Version001300Date20260924000000.php` (Form) + `Version001000Date20260901000000.php` (IDBConnection, Datenschritt) + `QueueService.php:410-448` (Transaktion) | role-match, zusammengesetzt |
| `php/tests/Unit/Version001300Date2026092X000000Test.php` (NEU) | test | batch | `Version001300Date20260924000000Test.php` + QB-Mock aus `PathResolverServiceTest.php:65-106` | exact (Form) |
| `backend/tests/test_measurement_scripts.py` (Ledger) | test | , | selbst: 630-659 (PHP), 780-797 (Python) | exact |
| `backend/pyproject.toml` | config | , | selbst: pillow-Absatz 22-28 (transitiv wird direkt) | exact |
| `backend/uv.lock` | config | , | generiert (`uv lock`, uv 0.11.7) | n/a |
| `THIRD-PARTY.md:200-230` | doc | , | selbst | exact |
| `backend/Dockerfile:482-490` (Kommentar) | config | , | selbst | exact |
| `.github/workflows/docker.yml` (Kommentar 337-345 + neuer Abwesenheitsschritt) | config/CI | , | Schritte 214-221 und 237-244 | exact |
| `php/appinfo/info.xml` (125 + description) | config | , | Präzedenz 16-07 / 16-12 | exact |
| `backend/appinfo/info.xml` (142, 236 + description) | config | , | Präzedenz 16-07 / 16-12 | exact |
| `docs/store-listing.md` | doc | , | selbst: "Nachtrag vom 21.09.2026" (90ff), "Die Abnahme" (785ff) | exact |
| `docs/language-analyzers.md:438-505` | doc | , | selbst | exact |
| `backend/tests/test_store_metadata.py` (347, ggf. neues Grenzlisten-Gate) | test | , | selbst: 347, 372 | exact |
| `README.md`, `README.en.md`, `README.fr.md` | doc | , | Präzedenz 16-12 | role-match |
| `docs/audits/2026-09-phase-23/README.md` (NEU) | doc | , | `docs/audits/2026-09-phase-16/README.md` | exact |
| Changelog-/Release-Notiz (GitHub-Release) | doc | , | keins im Repo | **kein Analog** |
| Issue-#14-Antwort | Kommunikation | , | keins im Repo | **kein Analog** |

---

## Pattern Assignments

### `backend/src/findling/embed/engine.py` (service, event-driven)

**Analog:** die Datei selbst. Der Warmlauf existiert komplett; geändert werden zwei Stellen.

**Stelle 1, die eine Regelstelle** (Zeilen 367-406). Heute:
```python
def query_may_load() -> bool:
    ...
    return settings().embed_idle_release_seconds == 0
```
Nach D-01 antwortet sie immer `False`. Der Docstring 377-388 ("The general case is carried as a backlog item") wird zur Aussage, dass der allgemeine Fall jetzt geschlossen ist (V-22-01/02). Kommentar 399-405 zu `api/diagnose.py` (lädt weiter, fragt bewusst nicht) bleibt inhaltlich stehen.

**Stelle 2, die Schalter-0-Sperre** (Zeilen 521-534), dieser Block fällt:
```python
    if query_may_load():
        # The switch is off, so no search was ever refused a load and there is
        # nothing to make good. Warming here would be the behaviour change
        # outside the switch that query_may_load exists to refuse.
        return False
```
Docstring 505-519 ("Four conditions ... the release is switched on at all") auf drei Bedingungen umschreiben.

**Unverändert zu übernehmen, Doppelstart-Schutz** (569-582), nicht neu bauen:
```python
    with _LOCK:
        if _WARMING:
            return False
        _WARMING = True
        _WARM_WANTED = False

    try:
        return shared_model().embed_query(WARM_TEXT, may_load=True).available
    finally:
        with _LOCK:
            _WARMING = False
```
Docstring von `request_warm` (486-498) nennt "on the path of a search that query_may_load refused a load to"; bleibt wahr, Plan-Verweis 14-08 ergänzen um Phase 23.

---

### `backend/src/findling/embed/model.py` (service, request-response)

**Analog:** `_embed` 511-535.

**Einfügeort** (vor Zeile 525/526):
```python
        # The load under the lock, for the reason stated beside it in __init__.
        with self._lock:
            engine = self._load() if may_load else self._engine
            self._last_use = time.monotonic()
            if engine is None:
                return EmbedOutcome.unavailable()
```
Schnellpfad davor (RESEARCH Code Example 1): `if not may_load and self._engine is None: return EmbedOutcome.unavailable()`. **Wichtig:** `_last_use` wird im Schnellpfad NICHT gesetzt (heute setzt Zeile 533 ihn auch für den kalten Fall; `release_if_idle` in `engine.py:455-461` liest ihn nur bei gebundenem Halter). Kommentarstil: ein Absatz mit Grund und Befundnummer, wie 528-532 und 536-546.

**Leerer Batch zuerst** (519-523) bleibt oberhalb des Schnellpfads.

---

### `backend/src/findling/api/search.py` (controller, request-response)

**Analog:** Handler 359-409.

**Imports** (Zeilen 35-60), Ergänzung `BackgroundTasks` in Zeile 44:
```python
from fastapi import APIRouter, Depends, HTTPException, status
...
from findling.embed.engine import query_may_load, request_warm, warm, warm_wanted
```
Es gibt im Repo **kein** bestehendes `BackgroundTasks`-Muster (Grep: nur der Kommentar Zeile 392). Das Muster ist also neu; Starlette-Semantik siehe RESEARCH Pattern 3.

**Heutiger Warmstart, der ersetzt wird** (385-398):
```python
    if warm_wanted():
        # ... and ``BackgroundTasks`` runs only after the response has gone out.
        # ``create_task`` on the loop that is already here adds no coupling at
        # all. The run itself blocks, like every load, so it goes through
        # ``asyncio.to_thread`` (T-14-23).
        task = asyncio.create_task(asyncio.to_thread(warm))
        _WARM_TASKS.add(task)
        task.add_done_callback(_WARM_TASKS.discard)
```
Neuer Weg: Handlerparameter `background: BackgroundTasks`, dann `background.add_task(warm)` (sync-Funktion, Starlette fährt sie im Threadpool nach dem Senden). `_WARM_TASKS` (66-72) und `asyncio`-Import prüfen: `asyncio.to_thread` für `one_round` (370) bleibt, `_WARM_TASKS` fällt samt Kommentar. Der Kommentar 385-395 muss die Abwägung neu führen (GIL-Befund onnxruntime 1.30.0 macht "nach dem Senden" zum Vorteil).

**Anfordern des Warmlaufs am Entstehungsort** (311-332) bleibt die Vorlage; mit `query_may_load() == False` ist `if not may_load: request_warm()` künftig bei jeder hybriden Runde aktiv:
```python
        may_load = query_may_load()
        semantic = None
        lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only or sort != "relevance"
        if not lexical_only and side.vectors is not None and settings().embed_enabled:
            semantic = SemanticSide(
                vectors=side.vectors,
                model=resources.query_model(),
                text=text,
                may_load=may_load,
            )
            if not may_load:
                request_warm()
```
Kommentar 300-310 ("So with the release switched on this round answers out of the lexical list") auf "immer" umschreiben.

**Fehlerbehandlung** (344-349), unverändert und Vorbild für jede Ergänzung: nur Typname loggen, nie Suchtext.
```python
    except Exception as error:
        LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
        return _Round([], False, offset, True)
```

---

### `backend/src/findling/api/snippets.py` (controller, request-response)

**Analog:** `api/search.py:313` (Einwortregel) plus eigener Block 223-230.

**Heutiger Block** (223-230):
```python
        semantic = None
        if side.vectors is not None and settings().embed_enabled:
            semantic = index_search.SemanticSide(
                vectors=side.vectors,
                model=resources.query_model(),
                text=text,
                may_load=query_may_load(),
            )
```
Neu: Bedingung um `not (bool(rewritten.operators) or rewritten.one_term or title_only)` erweitern (kein `sort`, bewusst, siehe 109-113). `title_only` ist Funktionsparameter (150), `rewritten` kommt aus `build_query` (187-195), dieselbe Quelle wie auf `/search`.

**Zwingend mitändern:** Kommentar 204-210 behauptet das Gegenteil ("The two rules of the search path (operators, one term) are not read here"). Neue Begründung: für diese Zeilen hat `/search` keine Vektorliste gebaut, also gibt es keinen reinen Vektortreffer, dem ein Auszug fehlen könnte (RESEARCH Pattern 4). Kommentar 212-222 ("With the release switched on") auf den Dauerzustand umstellen.

**Warmlauf auf /snippets:** Die Route ruft heute kein `request_warm`. Ob `/snippets` ebenfalls anfordert, ist Claude's Discretion; wenn ja, dasselbe `BackgroundTasks`-Muster wie `/search` (Handler 243-271).

---

### `backend/tests/test_embed_engine.py` (test)

**Analog:** die Datei selbst. Umdrehen:
- `test_query_may_load_stays_true_while_the_release_is_switched_off` (842-853): erwartet heute `True` bei `"0"`, künftig `False`.
- `test_no_warm_run_is_wanted_while_the_release_is_switched_off` (1197-1211): erwartet heute `False`, künftig `True` nach `request_warm()` bei kaltem Halter.

**Fixture-Muster zum Übernehmen** (1190-1194, 1203-1208):
```python
def _release_is_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "900")
    settings.cache_clear()

@pytest.mark.usefixtures("no_warm_request")
def test_...(model_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _pretend_a_model(model_home)
    _stand_in(monkeypatch)
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", "0")
    settings.cache_clear()
    shared_model()
    request_warm()
```
**Bleibt als Gegenprobe:** zehn parallele `warm()` (1263-1281, `ThreadPoolExecutor(max_workers=10)`, `load_count() - before == 1`), "kein Lauf bei geladenem Halter", "keiner ohne Modell". Den Zehnerfall zusätzlich bei Schalter `"0"` parametrisieren.

---

### `backend/tests/test_embed_model.py` (test)

**Analog:** `test_a_query_that_may_not_load_answers_the_verdict_instead_of_loading` (512-528):
```python
    engine = _model(model_dir)
    before = load_count()

    outcome = engine.embed_query("eine Anfrage", may_load=False)

    assert outcome.verdict == EMBEDDING_UNAVAILABLE
    assert outcome.available is False
    assert load_count() == before
    assert engine.loaded is False
    assert stand_in.tokenizer.seen == []
```
Neuer Fall nach RESEARCH Pattern 2: Thread A hält `engine._lock` (Stand-in für `_load`), Thread B ruft `embed_query(..., may_load=False)` und muss in < 50 ms `available is False` liefern; zusätzlich `engine.last_use() is None` (Schnellpfad setzt die Uhr nicht). Fixtures `model_dir`, `stand_in`, `clock` (446-450) wiederverwenden. Der Nachbarfall 531-547 (warmer Halter, `may_load=False` antwortet normal) bleibt und muss grün bleiben.

---

### `backend/tests/test_search_endpoint.py` (test)

**Analog:** 690-770.
- `test_with_the_release_off_the_handler_starts_nothing` (701-716) dreht sich um: bei `"0"` und kaltem Halter genau ein Lauf.
- `test_with_the_release_on_a_cold_engine_gets_exactly_one_run` (719ff) ruft den Handler direkt: `await api_search.search(SearchRequest(query=TWO_WORD_TERM), cast(Any, None))` und wartet auf `api_search._WARM_TASKS`. Mit `BackgroundTasks` bekommt der Handler einen dritten Parameter; der Test reicht ein `BackgroundTasks()` herein und prüft `background.tasks` statt `_WARM_TASKS`. Der Docstring (M-16-01, TestClient-Portal-Rennen) wird dadurch gegenstandslos und muss das sagen: TestClient fährt Hintergrundaufgaben nach der Antwort synchron, das Rennen existiert mit `BackgroundTasks` nicht mehr.

**Zählhelfer zum Übernehmen** (~690-699):
```python
    runs: list[int] = []
    ran = threading.Event()

    def fake_warm() -> bool:
        runs.append(1)
        ran.set()
        return True

    monkeypatch.setattr(api_search, "warm", fake_warm)
    return runs, ran
```
Neuer Fall: einwortige Suche fordert keinen Warmlauf an (`ONE_WORD`-Konstante analog `TWO_WORD_TERM`).

---

### `backend/tests/test_snippets_endpoint.py` (test)

**Analog:** 398-457.
```python
class _LoadSwitchModel:
    def __init__(self) -> None:
        self.seen: list[bool] = []

    def embed_query(self, text: str, *, may_load: bool = True) -> EmbedOutcome:
        self.seen.append(may_load)
        return EmbedOutcome.unavailable()

def _watch_the_load_switch(monkeypatch: pytest.MonkeyPatch, seconds: str) -> _LoadSwitchModel:
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", seconds)
    settings.cache_clear()
    model = _LoadSwitchModel()
    monkeypatch.setattr(resources, "query_model", lambda: model)
    return model
```
- Parametrisierung 424-443 `[("0", True), ("900", False)]` wird `[("0", False), ("900", False)]`.
- Neuer D-02-Fall: einwortige Zeile (`TERM`, sofern einwortig) liefert `model.seen == []` und trotzdem den Auszug (`[text.file_id for text in cut] == [ALICE_FILE]`, Muster 455-457). Gleich für Operator-Zeile und `title_only=True`.

---

### `.github/workflows/integration.yml` (CI, Paraphrase-Kaltsuche 1719-1855)

**Analog:** derselbe Schritt. Wiederzuverwendende Bausteine:

**Status-Abfrage ohne Laden** (1811-1820):
```bash
          auth=$(printf 'cold:%s' "${EXAPP_SECRET}" | base64 -w0)
          status_answer=$(curl -sf -m 10 "http://127.0.0.1:${EXAPP_PORT}/status" \
            -H 'EX-APP-ID: findling_backend' \
            -H "EX-APP-VERSION: ${APP_VERSION}" \
            -H "AUTHORIZATION-APP-API: ${auth}" || true)
          engine_state=$(printf '%s' "${status_answer}" | jq -r '.engineState // empty' || true)
```
**Warteschleifen-Muster mit Deadline** (1759-1772, `backlog_deadline=$(( $(date +%s) + 60 ))` ... `sleep 5`): Vorlage für "bis `engineState=loaded` warten".

**Umbau:** erste kalte Suche: HTTP 200, Dauer drucken (weiter nicht behaupten, Stil 1834-1836 "printed for the reader and asserted nowhere"); dann auf `loaded` warten und Warmlaufdauer als Zahl loggen; dann die zweite Suche mit den bestehenden `jq -e`-Zusicherungen 1840-1846 ("the paraphrase found nothing at all"). Die Wortzahl- und Operator-Tore 1724-1748 bleiben.

---

### `backend/tests/probe_image_search.py` (probe, batch)

**Analog:** `offline_step` 331-349. Einfügeort zwischen `write_vector_stock` und `ask(PARAPHRASE, ...)`:
```python
    root = volume_for(CORPUS, embedding=True)
    chunks = write_vector_stock(root, CORPUS)
    print(f"vector stock                {chunks} chunks for {len(CORPUS)} documents")
    lexical = ask(LEXICAL_TERM, label="full text query")
    semantic = ask(PARAPHRASE, label="paraphrase, with vectors")
```
Vor `semantic = ask(...)` den geteilten Halter über den Produktweg wärmen (`request_warm(); warm()`), mit Kommentar warum. `write_vector_stock` baut ein eigenes `EmbeddingModel` (220-224), der geteilte Halter bleibt kalt; das ist die Ursache. Druckregel (289-291): nur Label, Ids, Flag.

---

### `backend/src/findling/tools/one_load.py` + `backend/tests/test_one_load.py` (utility/test, batch)

**Analog:** `drive_the_search_side` (277-287):
```python
def drive_the_search_side() -> int:
    page = one_round(MEASURE_USER, QUERY, SEARCH_LIMIT, 0, False)
    return len(page.candidates)
```
Nach dem Fix lädt `one_round` nie selbst. Ergänzung um den Handlerweg: `if warm_wanted(): warm()`, damit "a caller that stops going through the holder has to be caught here" (Kommentar 381-386) wahr bleibt. `cold_search_ms` (359-362, Kommentar "This round is the one that brings the engine loads from zero to one") umbenennen oder getrennt messen (Suche vs. Warmlauf). Die Tests 159-173 (`engine_loads_after_search == 1`), 250-266 und 285-294 (`test_it_goes_red_when_the_search_never_reaches_the_model`) müssen gegen das neue Verhalten ihre Rotfähigkeit behalten. Kommentar in `resilience.yml:1430-1442` ("the search side has to bring the engine loads to one on its own") nachziehen.

---

### Doku zum Schalter 0

- `docs/admin-page.md:138`, Zeile `unloaded`: "wer die Nachladekosten nicht will, setzt `FINDLING_EMBED_IDLE_RELEASE_SECONDS` auf 0" ist nach D-01 falsch (auch bei 0 lädt die erste Suche nicht mehr im Request). Zeile `cold` (137) "Das Modell wird beim ersten Bedarf geladen" um "im Hintergrund, die erste Suche antwortet mit Volltexttreffern" präzisieren.
- `backend/appinfo/info.xml:469` (Beschreibung der Umgebungsvariable) prüfen: der Satz "The first search afterwards answers from the full text side while the model is warmed up again in the background" gilt künftig auch für den Kaltstart ohne Freigabe. Diese Beschreibung reist mit dem Release (Store-Text-Regel).
- `docs/embeddings.md:760-840`: gleiche Aussage.

---

### `php/lib/Migration/Version001300Date2026092X000000.php` (NEU, migration, batch)

**Analoge:** drei Dateien, jede für einen Teil.

**Form, Klassenkommentar-Schluss, Datei = Klassenname** aus `Version001300Date20260924000000.php` (1-13, 80-111):
```php
<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * ...
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001300Date20260924000000 extends SimpleMigrationStep {
	public function __construct(
		private IAppConfig $appConfig,
	) {
	}

	/**
	 * After the schema, because this touches data and no table.
	 *
	 * Guarded so a second run is a no-op, ...
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		...
		if ($recorded === '') {
			$output->info('no recorded backend version to drop');

			return;
		}
		...
		$output->info(sprintf('dropped the recorded backend version %s, it predates this update', $recorded));
	}
}
```
Einrückung mit Tabs, `declare(strict_types=1)`, Konstruktor-Promotion. Datum im Namen: Entstehungstag, lexikalisch NACH `20260924000000` (z. B. `Version001300Date20260926000000`).

**IDBConnection im Konstruktor und Datenschritt in postSchemaChange** aus `Version001000Date20260901000000.php` (44-48, 103-109):
```php
	public function __construct(
		private IDBConnection $db,
	) {
	}
	...
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$qb = $this->db->getQueryBuilder();
		$qb->update('findling_queue')
			->set('locked_at', $qb->createNamedParameter(new \DateTime('@0'), IQueryBuilder::PARAM_DATE))
			->where($qb->expr()->isNull('locked_at'));
		$qb->executeStatement();
	}
```

**Löschen im Band mit `PARAM_INT_ARRAY`** aus `FileStateService::revokeFailures` (`php/lib/Service/FileStateService.php:318-334`), die Vorlage für das Löschen der gone-Zeilen:
```php
		foreach (array_chunk($wanted, self::MAX_LOOKUP) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->delete(self::TABLE_NAME)
				->where($qb->expr()->eq('state', $qb->createNamedParameter('failed', IQueryBuilder::PARAM_STR)))
				->andWhere($qb->expr()->in('file_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));
			$revoked += $qb->executeStatement();
		}
```
Für die Migration: `state='skipped'` UND `reason='gone'` UND `file_id IN (band)`. Tabellenname über `FileStateService::TABLE_NAME` (`'findling_file_state'`, Zeile 53), Band 1000 wie `MAX_LOOKUP` (203) bzw. `QueueMapper::DELETE_BAND` (185, privat, also nicht referenzierbar: eigene Konstante mit Begründungssatz).

**Neu einreihen, nicht selbst bauen:** `QueueMapper::requeueAs(array $fileIds, string $kind): int` (`php/lib/Db/QueueMapper.php:609-685`) mit `QueueMapper::KIND_CONTENT` (Zeile 59). Die Methode bandet selbst (615), respektiert `delete`-Vorrang (617-620, 634), `dirty`-Zeilen (644-652) und legt fehlende Zeilen mit `storage_id=0, root_id=0` an (662-681).

**Transaktion** aus `php/lib/Service/QueueService.php:410-448`:
```php
		$this->db->beginTransaction();
		try {
			...
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}
```
Reihenfolge je Band: `requeueAs`, dann Löschen, dann `commit`. Ausgabe nur als Zahl (Muster 102-109; Leerfall `'no gone verdicts to repair'`). Keine Kennungen, keine Pfade (V7).

**Konstruktor-Vertrag:** Nur `IDBConnection` und `QueueMapper`, kein `ExAppService` oder sonstiger Container-Kollaborateur (Klassenkommentar-Absatz 55-61 der 1.3.0-Migration als Begründungstext übernehmen).

---

### `php/tests/Unit/Version001300Date2026092X000000Test.php` (NEU, test)

**Analog:** `php/tests/Unit/Version001300Date20260924000000Test.php` (ganze Datei, 158 Zeilen).

**Kopf und Attribute** (1-13, 40-41):
```php
<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use Closure;
use OCA\Findling\Migration\Version001300Date20260924000000;
use OCP\Migration\IOutput;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

#[CoversClass(Version001300Date20260924000000::class)]
final class Version001300Date20260924000000Test extends TestCase {
```
**Schema-Closure, die laut scheitert** (50-57):
```php
	private function schemaClosure(): Closure {
		return static function (): never {
			self::fail('this migration must not touch the schema');
		};
	}
```
**Konstruktorprüfung per Reflection** (139-157), angepasst auf zwei Parameter (`IDBConnection`, `QueueMapper`):
```php
		$constructor = (new \ReflectionClass(Version001300Date20260924000000::class))->getConstructor();
		self::assertNotNull($constructor);
		$parameters = $constructor->getParameters();
		self::assertCount(1, $parameters, 'the migration was handed a second collaborator');
		$type = $parameters[0]->getType();
		self::assertInstanceOf(\ReflectionNamedType::class, $type);
		self::assertSame(IAppConfig::class, $type->getName());
```
**Zweiter Lauf** (120-137, `willReturnOnConsecutiveCalls`, `expects(self::exactly(2))->method('info')`).

**QueryBuilder-Mock** aus `php/tests/Unit/PathResolverServiceTest.php:65-106` (`getQueryBuilder` per `willReturnCallback`, `select/from/where/andWhere` mit `willReturnSelf`, `executeQuery` liefert `IResult`-Mock mit `fetchAll`). Für `delete` und `executeStatement` ergänzen. `QueueMapper` als Mock wie `QueueServiceReaderTest.php:56` (`$this->createMock(QueueMapper::class)`), dort `expects(self::once())->method('requeueAs')->with([...], QueueMapper::KIND_CONTENT)`.

**Fälle (RESEARCH Open Question 3):** leere Tabelle (No-op + Infozeile, kein `requeueAs`, kein `beginTransaction`); gone-Zeilen werden eingereiht UND gelöscht; andere Gründe/Zustände werden nicht angefasst (Löschbedingung prüft `reason='gone'`); Rollback bei Wurf aus `requeueAs`; zweiter Lauf wirft nicht; Konstruktor ohne Container-Kollaborateur.

---

### `backend/tests/test_measurement_scripts.py` (Ledger)

**Analog:** datierte Absätze 630-657 (PHP) und 780-795 (Python):
```python
# Moved on 2026-09-26 by the review of issue #14, fourth fix: two of the 70
# files changed their bytes and none came or went. PathResolverService.php
# asks ...
PHP_FILES_TODAY = 70
PHP_TREE_HASH_TODAY = "2e59ceb5..."
...
# Moved on 2026-09-26 by the fix of issue #14: two of the 57 files changed their
# bytes. ... No file came and none went, so
# PACKAGE_FILES_TODAY stays at 57.
PACKAGE_FILES_TODAY = 57
PACKAGE_TREE_HASH_TODAY = "b5608980..."
```
Neue Migration + Test: `PHP_FILES_TODAY` 70 auf 72, Hash neu. `embed/engine.py`, `embed/model.py`, `api/search.py`, `api/snippets.py`, `tools/one_load.py` bewegen `PACKAGE_TREE_HASH_TODAY` (Dateizahl bleibt 57). Je Commit ein eigener Absatz mit Datum, Plan und Dateiliste.

---

### `backend/pyproject.toml` + `backend/uv.lock` (config)

**Analog:** pillow-Absatz 22-28, genau der Fall "transitiv wird direkt":
```toml
    # Pillow was already in uv.lock, pulled in transitively by python-pptx. The
    # OCR path uses it directly (...), and a direct import of an indirect
    # dependency is the version that silently disappears when the package that
    # dragged it in stops needing it. So it becomes a direct edge here. Net new
    # PyPI packages of phase 3: zero.
    "pillow==12.3.0",
```
Zu entfernen: Absatz 32-38 samt `"fastembed==0.8.0"`. Neu: `"tokenizers==0.23.2"` und `"numpy==2.5.2"` im pillow-Stil ("Net new PyPI packages of phase 23: zero"). onnxruntime-Kommentar 39-43 ("The inference runtime under fastembed", "1.29.0 ... is the newest release", "fastembed excludes 1.24.0 and 1.24.1") auf den Pin 1.30.0 und ohne fastembed-Bezug umschreiben. Danach `uv lock` (uv 0.11.7), `uv lock --check`, `uv sync --frozen`.

---

### `THIRD-PARTY.md` (doc)

**Analog:** Tabelle 207-212 und Absatz 224-230:
```markdown
| `fastembed` | 0.8.0 | Apache-2.0 | github.com/qdrant/fastembed | `/app/.venv/lib/python3.13/site-packages/fastembed` |
| `onnxruntime` | 1.29.0 | MIT | github.com/microsoft/onnxruntime | ... |
```
fastembed-Zeile ersetzen durch `tokenizers` 0.23.2 (Apache-2.0, github.com/huggingface/tokenizers) und `numpy` 2.5.2 (BSD-3-Clause, github.com/numpy/numpy); onnxruntime auf 1.30.0 (Altbefund). Einleitung 202-205 "Four packages" anpassen. Absatz 224-230 "Two network libraries enter the image through `fastembed`": `requests` fällt weg, `huggingface-hub` bleibt, jetzt "through `tokenizers`"; `HF_HUB_OFFLINE=1` bleibt nötig.

---

### `backend/Dockerfile:482-490` und `.github/workflows/docker.yml` (config/CI)

**Kommentar-Analog** `Dockerfile:482-485`:
```dockerfile
# HF_HUB_OFFLINE is a net, not a proof, and the difference is worth one line.
# What it does: huggingface-hub and requests arrive in this image through
# fastembed, and with this variable set the library refuses to resolve a name
```
und `docker.yml:340-343` ("fastembed brought two network libraries, huggingface-hub and requests"): beide auf "huggingface-hub arrives through tokenizers" umstellen.

**Neuer Abwesenheitsschritt**, Analog `docker.yml:214-221` (Einzeiler im Abbild) und 237-244 (`sh -c` mit `set -eu` und je Befund eigener `::error::`):
```yaml
      - name: Answer A12 and A13 inside this image
        env:
          DIGEST: ${{ steps.push.outputs.digest }}
        run: |
          docker run --rm --network none \
            -v "${GITHUB_WORKSPACE}/backend/tests:/probe:ro" \
            --entrypoint python \
            "${IMAGE}@${DIGEST}" /probe/test_vec_extension_probe.py
```
Inhalt: `find_spec('fastembed')` und `find_spec('requests')` müssen `None` sein, `find_spec('tokenizers')`/`numpy` nicht; zwei Meldungen für zwei Befunde. Kommentarblock davor im Hausstil (was geprüft wird, was nicht).

---

### Versionsstellen `php/appinfo/info.xml:125`, `backend/appinfo/info.xml:142`, `backend/appinfo/info.xml:236` (config)

**Analog:** Präzedenzplan `.planning/milestones/v1.2-phases/16-haertung-und-store-einreichung-v1-2-0/16-07-PLAN.md` (files_modified: beide info.xml, Migration, Migrationstest, test_measurement_scripts.py). Drei Stellen in einem Commit:
```xml
	<version>1.2.0</version>          <!-- php/appinfo/info.xml:125 -->
	<version>1.2.0</version>          <!-- backend/appinfo/info.xml:142 -->
			<image-tag>1.2.0</image-tag>  <!-- backend/appinfo/info.xml:236 -->
```
Gates: `backend/tests/test_lockstep_versions.py:159` (keine Zahl gepinnt, nur Gleichlauf), `release.yml:177-188`, `docker.yml:96`. `backend/pyproject.toml:3` (0.1.0) ist keine Release-Stelle.

---

### Store-Texte: `docs/store-listing.md`, beide `info.xml`-Beschreibungen, READMEs, `backend/tests/test_store_metadata.py`

**Analog:** Präzedenzpläne 16-11 (Entwurf in `docs/store-listing.md`, Owner-Checkpoint, `autonomous: false`) und 16-12 (wörtliche Übertragung in beide `info.xml` + drei READMEs + `test_store_metadata.py`).

**Aufbau der Beschreibung** (`php/appinfo/info.xml:36-56`), Faktenliste mit Überschriftzeilen und Spiegelstrichen:
```text
What Findling does:
- Full text search in the normal Nextcloud search bar
...
Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 731.9 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64
```
Die "Known limitations"-Liste (D-06) als eigener Block im gleichen Stil, dreisprachig (EN ohne `lang`, `de`, `fr`), ohne MB-Angabe.

**Gates** in `test_store_metadata.py`: `RESIDENT_FIGURE = "731.9"` (347), `MEASURED_FIGURE = re.compile(r"\d+(?:[.,]\d+)?\s(?:MB|Mo)\b")` (372, genau eine Messzahl je Beschreibung), Vokabular-Sperre (195). Regeln `docs/store-listing.md:15-32` (keine Backticks, keine Tabellen, keine Gedankenstriche, echte Akzente).

**Änderungsprotokoll-Muster** in `docs/store-listing.md`: "Nachtrag vom 21.09.2026: die Messzahl der Fassung 1.2.0 (Entscheid E1)" (Zeile 90) und "Die Abnahme" (785). Neuer Nachtrag für 1.3.0 (Grenzliste, Messzahlentscheid 731,9 gegen 730,2 MB, ggf. Sprachzeile als Vorschlag).

**Wortlaut-Quelle der Grenzen** `docs/language-analyzers.md`: `año`/`ano` (438-443), Portugiesisch (468-475), Komposita (477-483), Französisch nur beiläufig (74-75). Die Fußnote 500-505 kündigt die Kurzfassung ausdrücklich an und wird durch den "Known limitations"-Abschnitt eingelöst (identischer Wortlaut wie im Store-Text, D-06).

---

### `docs/audits/2026-09-phase-23/README.md` (NEU, doc)

**Analog:** `docs/audits/2026-09-phase-16/README.md`. Gliederung übernehmen:
```
## 1. Die Haertungsmatrix
## 2. Gate-Protokoll
## 3. Security, ASVS V2, V4, V6, V7, V12, V14
## 4. Die Geheimnis-Gegenprobe, mit einem anderen Verfahren
## 5. Performance-Durchgang
## 6. Der Stand der ... Auflagen
```
Plan-Vorlage: 16-13 (Härtung + Audit + Owner-Abnahme, `autonomous: false`), 16-14 (Abgabe, eigener Plan, aktualisiert REQUIREMENTS/ROADMAP/STATE und den Audit-README). Umfang laut D-07 plus #14-Pfade (RESEARCH Open Question 4).

---

### Release-Workflows (nur Nutzung, keine oder minimale Änderung)

- `.github/workflows/store-submit.yml`: `workflow_dispatch` mit Eingang `tag` (28-30); Erfolg je App `200|201` (132, 158), Beleg ist der Wortlaut `release ${app} ${TAG}: HTTP ${code}` (155).
- `.github/workflows/deploy-harp.yml`: `UPGRADE_FROM_TAG: v1.2.0` (113) bleibt in dieser Phase stehen. Zusicherung Block 3 (4192-4200) verlangt `unchanged '.nextcloud.skipped'` und `unchanged '.nextcloud.scheduled'`; eine Migration, die im CI-Korpus gone-Zeilen fände, würde hier rot (RESEARCH A3). Falls der E2E-Beweis für D-04 gewollt ist, im Stil dieser `unchanged`-Zeilen mit eigenem Begründungskommentar.
- `.github/workflows/probe-92d.yml`: Eingang `from_tag`, Vorgabe `'v1.1.0'` (51-55); nach dem Bump mit `from_tag=v1.2.0` dispatchen (Präzedenz 16-09 für die Umstellung von Upgrade-Beweisen).

---

## Shared Patterns

### Logging ohne Inhalt (T-06-27, T-14-22)
**Quelle:** `backend/src/findling/api/search.py:344-349`, `api/snippets.py:236-240`, PHP `QueueService.php:450-454`
**Gilt für:** alle geänderten Python-Routen, Warmlauf, Migration
```python
        LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
```
```php
			$this->logger->info('Findling: recorded verdicts the container reported', ['count' => $recorded]);
```
Nur Typnamen und Zähler; Warmlauf nutzt ausschließlich `WARM_TEXT` (`engine.py:108-113`).

### Idempotente Migration
**Quelle:** `Version001300Date20260924000000.php:91-110`, `Version001000Date20260901000000.php:50-54`
**Gilt für:** die neue Migration
Zweiter Lauf ist No-op oder harmlos, wirft nie; Leerfall mit Infozeile; kein Containeraufruf; Klassen- und Dateiname zeichengleich.

### DB-Transaktion mit Rollback und Rethrow
**Quelle:** `php/lib/Service/QueueService.php:410-448` (auch `StorageCrawlJob.php:246-351`, `SubtreeExpandJob.php:147-207`)
**Gilt für:** Reparaturband der Migration

### Bänder gegen Parametergrenzen
**Quelle:** `FileStateService.php:195-203` (`MAX_LOOKUP = 1000`), `QueueMapper.php:185`
**Gilt für:** Select/Delete der gone-Zeilen

### Eine Regelstelle statt drei
**Quelle:** `engine.py:390-393` (Docstring `query_may_load`)
**Gilt für:** `/search`, `/snippets`; die Einwortregel auf `/snippets` liest dieselben Felder `rewritten.operators`, `rewritten.one_term` wie `api/search.py:313`, keine zweite Definition von "einwortig" (Quelle bleibt `query/rewrite.py:383 carries_one_term`).

### Umgebungsschalter in Tests
**Quelle:** `test_embed_engine.py:1190-1194`, `test_snippets_endpoint.py:415-421`
```python
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", seconds)
    settings.cache_clear()
```

### Ledger-Pflicht
**Quelle:** `backend/tests/test_measurement_scripts.py:630-659`, `780-797`
**Gilt für:** jeden Commit unter `backend/src` oder `php/**/*.php`.

### Qualitätsgates vor Commit
ruff (Vollregelsatz), `ruff format --check`, pyright basic mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture 80, pytest (Referenz 3324/15). PHP lokal nur über `nextcloud:35`-Image oder CI `php.yml`.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| Changelog-/Release-Notiz 1.3.0 (Dank an budachst, Verweis #14, D-05) | doc | , | keine CHANGELOG-Datei im Repo; Notiz entsteht mit dem GitHub-Release, Text als Teil des Owner-Entwurfs vorlegen |
| Antwort in Issue #14 | Kommunikation | , | kein Repo-Artefakt; nach dem Release, Owner-Freigabe (Regel: fremde Issues nicht eigenmächtig schließen) |
| FastAPI-`BackgroundTasks` im Handler | controller | event-driven | Muster ist im Repo neu (nur Kommentar `api/search.py:392`); Vorlage ist RESEARCH Code Example 2 und die Starlette-Doku |

## Metadata

**Analog search scope:** `backend/src/findling/{embed,api,tools}`, `backend/tests`, `php/lib/{Migration,Db,Service}`, `php/tests/Unit`, `.github/workflows/{integration,docker,resilience,deploy-harp,probe-92d,store-submit}.yml`, `docs/{store-listing,language-analyzers,admin-page}.md`, `docs/audits/`, `THIRD-PARTY.md`, `.planning/milestones/v1.2-phases/16-*`
**Files scanned:** ca. 35
**Pattern extraction date:** 2026-09-26
