# Phase 35: Stretch: Ähnliche Dokumente und Spikes - Pattern Map

**Mapped:** 2026-10-19
**Files analyzed:** 31 (neu oder geändert, Kataloge als eine Gruppe gezählt)
**Analogs found:** 29 / 31
**Stand des Repos:** `main` auf `a88de31f` (wie 35-RESEARCH.md)

Lesehinweis: Alle Zeilennummern beziehen sich auf den gelesenen Stand. Code-Auszüge sind wörtlich; deutsche Prosa
mit Umlauten, Code und Schlüssel ohne Umlaute.

## File Classification

### STR-01 Ähnliche Dokumente (Container)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `backend/src/findling/api/similar.py` (neu) | controller (FastAPI-Route) | request-response | `backend/src/findling/api/snippets.py` | exact |
| `backend/src/findling/index/search.py` (neue Funktion `similar_candidates`, ggf. `centroid`) | service | transform + CRUD-read | `index/search.py::_permit` (221 bis 237), `::snippets_for` (936 ff.) | exact |
| `backend/src/findling/store/vectors.py` (neue Methode `vectors_of`) | model/store | CRUD-read | `vectors.py::chunks_of` (580 bis 613), `::nearest` (485 bis 522) | exact |
| `backend/src/findling/index/fusion.py` (optional: `centroid` als reine Funktion) | utility | transform | `fusion.py::documents_from_chunks` (73 bis 104), `::near_enough` (107 bis 152) | exact |
| `backend/src/findling/main.py` | config (Router-Registrierung) | , | `main.py:48 bis 53`, `1350 bis 1355` | exact |
| `backend/src/findling/config.py` | config | , | `config.py:918 bis 955` (`VECTOR_SCAN_MAX`, `VECTOR_MAX_DISTANCE`, `VECTOR_DISTANCE_BAND`) | exact |
| `backend/appinfo/info.xml` (nur Kommentar) | config | , | `info.xml:283 bis 295` | exact |
| `backend/tests/test_similar_endpoint.py` (neu) | test | request-response | `backend/tests/test_snippets_endpoint.py` | exact |
| `backend/tests/test_semantic_boundary.py` (`KNOWN_ROUTES`) | test (Ratsche) | , | Zeile 73 | exact |
| `backend/tests/test_info_xml_defaults.py` (`CONTENT_ROUTES`) | test (Ratsche) | , | Zeile 127 | exact |
| `backend/tests/test_measurement_scripts.py` (`PACKAGE_*_TODAY`, ggf. `PHP_*_TODAY`, `NARROW_SCOPE_DIRS`) | test (Ratsche) | , | Zeilen 112, 983 bis 984, 2032 bis 2033 mit Journalabsätzen davor | exact |
| `backend/tests/test_search_library.py` / Fusion-Tests für `centroid` | test | transform | `test_search_library.py:309` (Zählgate), Fusion-Tests | role-match |

### STR-01 Ähnliche Dokumente (PHP-Companion und Seite)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `php/lib/Service/ExAppService.php` (neu `similarCandidates`) | service (Proxy) | request-response | `ExAppService::snippets` (527 bis 575), `::filterCandidates` (1035 bis 1074) | exact |
| `php/lib/Service/SearchService.php` (neu `similar`) | service (Rechtegrenze) | request-response + Recheck | `SearchService::run` (182 bis 531), `::readableFile` (568 bis 570) | exact |
| `php/lib/Service/SimilarOutcome.php` (neu, optional) | model (Wertobjekt) | , | `php/lib/Service/SearchOutcome.php` (99 bis 105), `ApprovedHit.php` (50 bis 55) | exact |
| `php/lib/Controller/PageController.php` | controller | request-response | `PageController::index` (218 bis 291), `::rows` (653 bis 673), `::filterUrl` (773 bis 775), `::pageUrl` (1073 bis 1081), Parameterleser `::pageNumber` (354 ff.) | exact |
| `php/templates/search.php` | component (Template) | request-response | Hit-Block 430 bis 486, Kopf 199 bis 210, Leerzustand 487 bis 548, Reset-Link 400 bis 401 | exact |
| `php/css/search.css` | config (Stylesheet) | , | `.findling-filters__reset` (313 bis 325), Hover-Gruppe (274 bis 281) | exact |
| `php/js/search.js` | , | , | **unverändert** (delegierter Handler 178 bis 186 trägt mit) | , |
| `php/l10n/*.json`, `*.js` (16 Dateien) | config (Katalog) | , | bestehende Schlüssel `Reset all filters`, `Remove filter %s` (`de.json:259 bis 260`) | exact |
| `docs/l10n-{french,spanish,italian,dutch,portuguese}.md` | config (Sprachtabellen) | , | `docs/l10n-french.md:387` (Zeilenform) | exact |
| `backend/tests/test_admin_ui_contract.py` (Schlüsselzahl 341 + n) | test (Ratsche) | , | Zeilen 3615 bis 3625 (Absatz), 3649 bis 3667 (Kommentar + Assert) | exact |
| `php/tests/Unit/{SearchServiceTest,ExAppServiceTest,PageControllerTest}.php` | test (nur CI) | , | `SearchServiceTest.php:325, 547, 588`; `ExAppServiceTest.php:154, 165`; `PageControllerTest.php:369 ff.` | exact |

### STR-01 Wortlaut und Abnahme

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `.planning/phases/35-*/35-WORTLAUT.md` (neu) | doc (Owner-Abnahme) | , | `.planning/phases/34-umstiegsweg/34-WORTLAUT.md` | exact |
| `.planning/phases/35-*/35-0x-ABNAHME.md` (neu) | doc (Playwright-Protokoll) | , | `.planning/phases/34-umstiegsweg/34-05-ABNAHME.md` | exact |
| `.planning/phases/35-*/35-AUDIT.md` (neu) | doc (Audit) | , | `.planning/phases/34-umstiegsweg/34-AUDIT.md` | exact |

### STR-01 Wave-0-Distanzlauf und STR-02 granite-Messung

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `docs/measurements/2026-10-aehnlich-distanzen/README.md` (neu, Name frei) | doc (Messbericht) | batch | `docs/measurements/2026-09-06-vektordistanzen/README.md` + Regel-Kopf aus `2026-10-ordnerfilter/README.md:1 bis 20` | exact |
| Distanz-Messskript (neu oder Modus von `scripts/dev/vector_distances.py`) | utility (Messskript) | batch | `scripts/dev/vector_distances.py` (`--derive`, `--corpus`, `near_enough_rows` 543 ff.) | exact |
| `docs/measurements/2026-10-granite-vergleich/README.md` (neu) | doc (Messbericht) | batch | `docs/measurements/2026-09-05-modellqualitaet/README.md` + `2026-09-vergleichsmessung-m7g/README.md` + `2026-10-abnahme-anfahrt/README.md` | exact |
| `docs/measurements/2026-10-granite-vergleich/skripte/*.sh|*.py` (neu) | utility (Messskript) | batch | `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/94-grundlast.sh` (Kopfkommentar-Stil), `00-ablauf.md` | exact |
| `docs/measurements/2026-10-granite-vergleich/rohdaten/*` (neu) | data | file-I/O | `2026-10-abnahme-anfahrt/rohdaten/` (Nummernschema `00-`, `01-`, `90-kosten.txt`, `08-abbau-*`) | exact |
| `scripts/dev/model_quality.py` (Schalter `--pooling {mean,cls}`) | utility (Messwerkzeug) | transform | eigene Datei, `parse_args` 102 bis 126, `embed` 194 bis 221, `mean_pool` 224 bis 229 | exact |
| `backend/tests/test_model_quality.py` (Fälle für `--pooling`) | test | , | eigene Datei (pure Teile ohne onnxruntime, Zeile 25 ff.) | exact |
| `scripts/dev/quantize_model.py` | utility | file-I/O | **unverändert**, Aufruf mit `--min-bytes/--max-bytes` (78 bis 99) | , |

### STR-03 Dedup-Notiz

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Qualität |
|---|---|---|---|---|
| `.planning/phases/35-*/35-DEDUP-NOTIZ.md` (neu) | doc (Entscheidungsvorlage) | , | Abschnitt "(E) Fragen an den Owner" in `34-WORTLAUT.md:433 bis 480` (Optionen (a)/(b) + Empfehlung) | partial |

## Pattern Assignments

### `backend/src/findling/api/similar.py` (controller, request-response)

**Analog:** `backend/src/findling/api/snippets.py` (275 Zeilen, ganz gelesen)

**Modul-Docstring:** wie snippets.py:1 bis 35 ausführlich begründen, warum die Route Inhaltsroute ist, warum der
Vorfilter als erste Aktion läuft (Confused Deputy) und warum ein fehlender Treffer eine vollständige Antwort ist.

**Imports** (snippets.py:37 bis 62):
```python
import asyncio
import logging
from functools import partial
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from findling.api import resources
from findling.config import SEARCH_LIMIT_MAX
from findling.index import search as index_search
from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id

LOGGER = logging.getLogger("findling.api.snippets")   # -> "findling.api.similar"

ROUTER = APIRouter()
```

**Request-Modell mit `extra="forbid"`** (snippets.py:80 bis 92):
```python
class SnippetsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=SEARCH_QUERY_MAX_CHARS)
    fileIds: list[int] = Field(max_length=SEARCH_LIMIT_MAX)
```
Für `SimilarRequest`: `fileId: int = Field(ge=1)`, `limit: int = Field(ge=1, le=SEARCH_LIMIT_MAX)`; camelCase, weil
das Drahtformat der PHP-Seite gehört (Kommentar snippets.py:93 bis 94). Antwortmodell nach `SearchResponse`
(api/search.py:154 bis 170) mit `degraded: bool = False`, aber Kandidaten nur `{fileId}`, ohne Score (D-14).

**Synchrone Arbeitsfunktion, alle Fehler leer** (snippets.py:183 bis 186 und 239 bis 244):
```python
    try:
        side = resources.read_side()
        if side is None:
            return []
        ...
        return index_search.snippets_for(side.index, side.store, uid, rewritten.query, file_ids, semantic=semantic)
    # Deliberately every exception, for the reason in the docstring above.
    except Exception as error:
        # The type name and nothing else: a traceback carries whatever a library
        # put into its message, and here that would be document text.
        LOGGER.warning("cutting the excerpts ended in an unexpected %s", type(error).__name__)
        return []
```
Für `/similar`: `side.vectors is None` ebenfalls leer (kein Vektorbestand), aber KEIN `resources.query_model()`,
denn der Anfragevektor kommt aus dem Bestand (Research Muster 1). `degraded` über `resources.degraded(side)` wie
api/search.py:239.

**Route, Nutzer nur aus signiertem Header, Worker-Thread** (snippets.py:247 bis 275):
```python
@ROUTER.post("/snippets")
async def snippets(
    body: SnippetsRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> SnippetsResponse:
    """Answer with one excerpt per confirmed file id, and with nothing else."""
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")
    ...
    cut = await asyncio.to_thread(
        partial(
            excerpts,
            user_id,
            ...
        )
    )
```
Die künstliche Verzögerung (`FINDLING_ARTIFICIAL_DELAY_MS`, snippets.py:64 bis 75, 133 bis 143) NICHT übernehmen;
sie gilt laut Kommentar "in this endpoint and in no other".

**Logging-Regel:** keine fileid, kein Pfad, kein Titel im Log, nur Typname (api/search.py:342).

---

### `backend/src/findling/index/search.py` (service, transform)

**Analog:** dieselbe Datei.

**Imports bereits vorhanden** (Zeilen 48 bis 53): `to_int8`, `ChunkHit`, `documents_from_chunks`, `near_enough`,
`VectorStore`, `Store`. Neue Konstanten aus `findling.config` dazunehmen.

**Einziger Vorfilter-Weg** (Zeilen 221 bis 237):
```python
def _permit(store: Store, uid: str, ranked: Sequence[Candidate]) -> list[Candidate]:
    """Keep the candidates the prefilter confirms, in the order they arrived.
    ...
    One function rather than two call sites, and that is an assertion and not a
    style: a test greps this file for the name of the prefilter and expects to
    find it exactly twice, here and in the snippet cut. ...
    """
    if not ranked:
        return []
    visible = store.prefilter_visible(uid, [candidate.file_id for candidate in ranked])
    return [candidate for candidate in ranked if candidate.file_id in visible]
```
**Pflicht:** `similar_candidates` ruft nur `_permit` (zweimal: Quelle zuerst, dann Top-Fenster). Der Name des
Vorfilters darf in keinem neuen Kommentar oder Docstring dieser Datei stehen (`test_search_library.py:309`:
`assert source.count("prefilter_visible") == 2`). Aufrufer-Gate in `test_semantic_boundary.py:252` erwartet
`["_permit", "snippets_for"]`.

**Skizze** aus 35-RESEARCH.md "Ablauf im Container" (Zeilen 437 bis 451) direkt übernehmen; `k_max` explizit am
Aufruf (`vectors.nearest(query, SIMILAR_SCAN_CHUNKS, k_max=SIMILAR_SCAN_CHUNKS)`), Quell-Chunks vor der Aggregation
raus, `near_enough(hits, ceiling=SIMILAR_CEILING, band=SIMILAR_CEILING)`.

---

### `backend/src/findling/store/vectors.py` (store, CRUD-read)

**Analog:** `chunks_of` (580 bis 613) für Form und Docstring, `_NEAREST_SQL` (236 bis 246) für SQL-Konstanten.

**SQL-Konstante mit Kommentar** (240 bis 246):
```python
_NEAREST_SQL: Final = """
SELECT v.rowid, c.file_id, c.ordinal, c.char_start, c.char_end, v.distance
FROM chunk_vectors AS v
JOIN chunks AS c ON c.chunk_id = v.rowid
WHERE v.embedding MATCH vec_int8(?) AND k = ?
ORDER BY v.distance
"""
```
Neue Konstante `_VECTORS_OF_SQL` (Research Zeilen 401 bis 407) im selben Block wie 229 bis 234 ablegen.

**Methodenform** (chunks_of 592 bis 613): leere Eingabe früh beenden, Zeilen typisiert umwandeln, Docstring sagt, was
"leer" bedeutet ("Documents without vectors are absent ... so a caller can tell 'no chunks' from 'not asked about'").

**Gate:** kein Wort über Rechte/Nutzer in dieser Datei außerhalb der bestehenden Docstrings
(`test_semantic_boundary.py:287` bis 293). `Neighbour` (196 bis 210) bleibt unverändert; der Feldsatz ist per Test
geprüft.

---

### `backend/src/findling/index/fusion.py` (utility, transform), optional für `centroid`

**Analog:** `documents_from_chunks` (73 bis 104) und `near_enough` (107 bis 152): reine Funktion, ausführlicher
Docstring mit Begründung und Randfällen, keine Datenbank. `test_search_library.py:486` verlangt
`"prefilter_visible" not in fusion`. `to_int8` aus `embed/model.py:245` wiederverwenden (Klemmung 254 bis 258);
wenn `centroid` hier liegt, `to_int8` importieren statt selbst runden.

---

### `backend/src/findling/main.py` und `config.py` (config)

**main.py Imports** (48 bis 53) und Registrierung (1350 bis 1355):
```python
from findling.api.snippets import ROUTER as SNIPPETS_ROUTER
...
APP.include_router(SEARCH_ROUTER)
APP.include_router(SNIPPETS_ROUTER)
```
`from findling.api.similar import ROUTER as SIMILAR_ROUTER` alphabetisch zwischen `search` und `snippets`
einsortieren, `APP.include_router(SIMILAR_ROUTER)` nach Zeile 1351.

**config.py** (952 bis 955) als Vorlage:
```python
VECTOR_MAX_DISTANCE = 86.5
VECTOR_MAX_DISTANCE_RANGE = (0.0, 254.0)
VECTOR_DISTANCE_BAND = 14.0
VECTOR_DISTANCE_BAND_RANGE = (0.0, 254.0)
```
`SIMILAR_CEILING` mit Kommentar, der auf den Wave-0-Messbericht verweist (wie `near_enough`-Docstring auf
`2026-09-06-vektordistanzen` verweist). Ob die Konstanten per Umgebungsvariable einstellbar werden (Muster
1684 bis 1690), ist Planner-Entscheidung; dann würde `info.xml` eine Umgebungsvariable bekommen und
`test_info_xml_defaults.py` greift, also eher feste Konstanten.

---

### `backend/appinfo/info.xml` (nur Kommentar)

**Analog** (283 bis 295):
```
				/search and /snippets are deliberately not declared. Their only
				caller is the companion, over PublicFunctions::exAppRequest, and
				that path never consults this table: ...
```
Satzanfang auf "/search, /snippets and /similar" erweitern; keine `<route>` hinzufügen.

---

### Gate-Ratschen (test, je Commit mitziehen)

**`test_semantic_boundary.py:68 bis 73`:**
```python
# ... Every plan that adds a route
# adds it here too, otherwise the clause stops being a ratchet.
KNOWN_ROUTES = ("/diagnose", "/probe", "/probe/state", "/rates", "/search", "/snippets", "/status")
```
`"/similar"` alphabetisch einfügen, Kommentar um den Planverweis ergänzen. Pfadname frei von "semantic"/"vector"
(Zeile 62).

**`test_info_xml_defaults.py:127`:** `CONTENT_ROUTES = ("/search", "/snippets")` um `"/similar"` erweitern; der
parametrisierte Test 135 ff. deckt die neue Route dann automatisch.

**`test_measurement_scripts.py`:** Journalabsatz direkt über der Konstante, Muster 960 bis 969:
```python
# Moved on 2026-10-19 by Plan 34-03 (UMST-02, PE-34-1, PE-34-2): the detection
# of the full text search framework next to Findling. One file came in lib,
# Service/ParallelSearchService.php (...). One test came,
# php/tests/Unit/ParallelSearchServiceTest.php (...). No file went, so PHP_FILES_TODAY moves
# to 105.
PHP_FILES_TODAY = 105
PHP_TREE_HASH_TODAY = "04a2c174..."
```
und Paketseite 2025 bis 2033 (`PACKAGE_FILES_TODAY = 79` auf 80 mit `api/similar.py`, Satz "The PHP pair does not
move" wenn php/ unverändert). Kataloge und CSS liegen nicht im PHP-Baum (Satz aus 974 bis 975 / 980 bis 982
wiederverwenden). Neuer `skripte/`-Ordner der granite-Messung als `*_RUN_DIR` (Muster Zeile 80
`V14_RUN_DIR = MEASUREMENTS_DIR / "2026-10-abnahme-anfahrt" / "skripte"`) und in `NARROW_SCOPE_DIRS` (Zeile 112).

**`test_admin_ui_contract.py`:** neuer Absatz nach 3615 bis 3624 im Stil:
```
    It stands at 341 since 19.10.2026, and the rise of one is plan 34-03: the
    banner of UMST-02, ... All sixteen files moved in one
    commit, the five language documents carry the row, the German and French
    wording is the one the owner accepted in 34-WORTLAUT.md, the five other
    languages are machine drafts under the same dated reservation as the rest.
    Whoever moves it next writes the next paragraph.
```
plus Aufzählung im Kommentar 3649 bis 3666 ("..., n of plan 35-0x (similar documents)") und
`assert len(keys_of["de.json"]) == 341` auf den neuen Wert. Zusätzlich prüfen die Scanner
`scan_page_template_for_an_unguarded_empty_state` und `scan_filter_row_for_a_counting_oracle` (um 1660 und 1790)
`search.php`.

---

### `backend/tests/test_similar_endpoint.py` (test, request-response)

**Analog:** `backend/tests/test_snippets_endpoint.py`

**Kopf und Fixtures** (17 bis 57):
```python
import pytest
from fastapi.testclient import TestClient

from conftest import Corpus, body_of
from findling.api import resources
from findling.embed.model import DIMENSIONS, EmbedOutcome
from findling.store.vectors import Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]
...
# An odd file id, so alice may see it and bob may see it. Even ids belong to bob
# alone, which is what the prefilter claim below rests on.
ALICE_FILE = 1
BOB_FILE = 2
```

**Vektorbestand ohne Modellartefakt** (72 bis 88):
```python
def _stock_one_chunk(root: Path) -> None:
    stock = open_vectors(root / "vectors.db")
    try:
        stock.replace_chunks(
            ALICE_FILE,
            [Chunk(ordinal=0, char_start=0, char_end=PASSAGE_CHARS,
                   embedding=bytes(127 if index == 1 else 0 for index in range(DIMENSIONS)))],
        )
    finally:
        stock.close()
```
Für `/similar` mehrere Dateien mit nahen/fernen Vektoren bestücken; da kein Modell geladen wird, ist kein `_Model`-
Stand-in nötig, ein Test sollte das sogar belegen (Modell-Seam wirft, Route antwortet trotzdem).

**Pflichtfälle nach dem Muster** 139 bis 195: fremde Quelle (bob-Datei von alice gefragt) liefert `[]`; Nutzer
ohne Rechtezeile liefert `[]`; unbekannte fileId liefert `[]`; `userId` im Body ergibt 400 mit
`"user identity is taken from the AppAPI header only"` (172 bis 180); Grenzen von `limit`; Quelle nie in der
eigenen Antwort; keine Distanz/Score im JSON.

---

### `php/lib/Service/ExAppService.php` (service, request-response)

**Analog:** `snippets()` (507 bis 575) und `searchCandidates()` (432 bis 505).

**Signatur und Docblock-Stil** (527):
```php
public function snippets(string $userId, string $term, array $fileIds, bool $titleOnly, SearchFilters $filters, float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS, float $ceilingSeconds = self::REQUEST_TIMEOUT_SECONDS): array {
```
**Aufruf über das bestehende `call()`** (556 bis 573):
```php
		$decoded = $this->call('/snippets', $userId, [
			'query' => $term,
			'fileIds' => array_values($wanted),
			...
		], $secondsLeft, $ceilingSeconds);
		if ($decoded === null) {
			return [];
		}

		$snippets = $decoded['snippets'] ?? null;
		if (!is_array($snippets)) {
			$this->logger->warning('Findling: malformed snippet answer');
			return [];
		}
```
**Antwort-Filterung** (filterCandidates 1035 bis 1074): nur `is_int($candidate['fileId']) && > 0` behalten, alles
andere zählen und mit `['count' => $dropped]` loggen. Für `/similar` ist der Kanarien-Zweig (1051 bis 1066) NICHT
nötig; Kandidaten mit fileId gleich der Quelle zusätzlich verwerfen. Null bei "keine brauchbare Antwort" (wie
searchCandidates 410 bis 413), damit `SearchService` "Backend schweigt" von "keine Nachbarn" trennen kann.
Timeout-Konstante `PAGE_REQUEST_TIMEOUT_SECONDS = 1.5` (Zeile 122) als Decke.

---

### `php/lib/Service/SearchService.php` (service, Rechtegrenze)

**Analog:** `run()` (182 bis 531).

**Heimatordner-Fehler** (216 bis 229):
```php
		try {
			$userFolder = $this->rootFolder->getUserFolder($uid);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: no home folder for this user, dropping every hit', ['exception' => $e]);

			return $this->nothing($startCursor, SearchOutcome::FAILURE_NO_HOME_FOLDER);
		}
```
**Versionsdrift zuerst** (201 bis 214) übernehmen: bei Drift keine Anfrage.

**Mounts einmal lesen** (233 bis 234): `$mounts = $this->mountsOfUser($user); $storageIds = self::storageIdsOf($mounts ?? []);`
dann `reduceIds` (638 ff.) vor dem Recheck.

**Recheck und ApprovedHit nur aus dem Knoten** (425 bis 458):
```php
				$node = self::readableFile($scope ?? $userFolder, $candidate['fileId']);
				if ($node === null) {
					continue;
				}

				$title = PlainText::bounded($node->getName(), self::MAX_TITLE_LENGTH);
				$path = PlainText::bounded(
					ltrim((string)$userFolder->getRelativePath($node->getPath()), '/'),
					self::MAX_PATH_LENGTH,
				);
				if ($title === null || $path === null) {
					continue;
				}
				...
				$approved[] = new ApprovedHit(
					$candidate['fileId'],
					$title,
					$path,
					PlainText::bounded($node->getMimetype(), self::MAX_MIME_LENGTH) ?? '',
					(int)$node->getMTime(),
				);
```
Für `similar()` dieselbe Folge zweimal: **erst die Quelle** über `self::readableFile($userFolder, $sourceId)`, bei
`null` sofort ein einziger Zustand "nicht verfügbar" OHNE Containeraufruf (Pitfall 1); dann `similarCandidates`,
dann Recheck je Kandidat bis 10 oder Budget (`$recheckBudget`-Muster 244 bis 245, Deadline-Muster 183 und
`secondsLeft` 815). **Nie** `getFirstNodeById`/`isReadable` direkt aufrufen: `test_php_acl_boundary.py:85`
`RESOLUTION_REGISTER` zählt sie in dieser Datei genau einmal.

**Fehlerzustände ohne Zahl** (476 bis 494): wie dort einen benannten Failure setzen, nie eine Anzahl verworfener
Nachbarn.

---

### `php/lib/Service/SimilarOutcome.php` (model, optional)

**Analog:** `SearchOutcome.php` (Konstanten 42 bis 81, Konstruktor 99 bis 105):
```php
	public function __construct(
		public readonly array $hits,
		public readonly array $excerpts,
		public readonly int $nextCursor,
		public readonly bool $hasMore,
		public readonly bool $degraded,
		public readonly ?string $failure,
	)
```
Neues Wertobjekt mit `?ApprovedHit $source`, `list<ApprovedHit> $hits`, `bool $degraded`, `?string $failure` und
Konstanten im Stil `FAILURE_SOURCE_UNAVAILABLE = 'source_unavailable'`. Eine neue Datei hebt `PHP_FILES_TODAY`
(Journalabsatz). Alternative: `SearchOutcome` plus Quelle wiederverwenden (dann keine neue Datei).

---

### `php/lib/Controller/PageController.php` (controller, request-response)

**Analog:** dieselbe Datei; **keine neue Route** (`test_php_trust_boundary.py:87 bis 89` zählt `ApiRoute`/`FrontpageRoute`).

**Parameterleser, still verwerfen** (pageNumber 354 bis 357):
```php
	private function pageNumber(): int {
		$raw = $this->request->getParam('page', '');
		if (!is_string($raw) || !ctype_digit($raw)) {
			return 1;
```
`similarId()` nach Research-Beispiel (Zeilen 456 bis 463) im gleichen Stil.

**Zweig in `index()`** (218 bis 291): der Similar-Zweig steht vor `$this->outcome(...)` (244); er gibt dieselbe
`TemplateResponse(Application::APP_ID, 'search', [...], TemplateResponse::RENDER_AS_USER)` zurück, mit zusätzlichen
Schlüsseln (`similarSource`, `backUrl`) und leeren `typeChips`/`rangeChips`/`sortLinks`, `previousUrl`/`nextUrl`
`null`. Log-Zeile ohne Inhalt wie 252.

**Zeilenbau** (rows 653 bis 673):
```php
			$rows[] = [
				'fileId' => $hit->fileId,
				'title' => $hit->title,
				'path' => $hit->path,
				'iconUrl' => $this->mimeTypes->mimeTypeIcon($hit->mimeType),
				'url' => $this->fileUrl($hit->fileId),
				'modified' => ...,
				'segments' => $excerpt === null ? [] : Highlighter::segments($excerpt['text'], $excerpt['highlights']),
			];
```
Neuer Schlüssel `'similarUrl'` je Zeile (in der Similar-Ansicht weglassen, eine Ebene). Für Nachbarn
`'segments' => []` (D-35-03, keine Markierung).

**URL-Bau mit vollem Zustand** (pageUrl 1073 bis 1081):
```php
	private function pageUrl(array $address, int $page, array $cursors, string $fingerprint): string {
		$arguments = $this->filterArguments($address) + [
			'page' => (string)$page,
			'cursors' => implode('.', $cursors),
			'fp' => $fingerprint,
		];

		return $this->urlGenerator->linkToRoute('findling.page.index', $arguments);
	}
```
`similarUrl` = dieselben Argumente plus `'similar' => (string)$fileId`; `backUrl` = `pageUrl(...)` ohne `similar`.
Docblock im Stil 756 bis 772 begründen, warum der Link die Position mitnimmt (Rückweg landet auf demselben Schirm).

---

### `php/templates/search.php` (component)

**Analog:** dieselbe Datei.

**Kopf-Variablen** (63 bis 84): neue Werte im selben Muster lesen:
```php
$resetUrl = is_string($_['resetUrl'] ?? null) ? $_['resetUrl'] : null;
```
**h1-Zweig** (204 bis 210): dritte Variante "Ähnlich zu: %s" mit Titel aus dem Knoten, weiterhin genau ein h1.

**Zweiter Link im `<li>`** nach Zeile 483 `</a>` (Block 451 bis 484), Kommentarstil `<?php /* ... */ ?>` wie 452 bis
455; aria-Label nach Muster 457:
```php
					<a class="findling-hit__link" href="<?php p($url); ?>" target="_self"
						aria-label="<?php p($dated ? $l->t('%1$s in %2$s, modified on %3$s', [$title, $path, $modified]) : $l->t('%1$s in %2$s', [$title, $path])); ?>">
```
Textlink-Snippet aus 35-RESEARCH.md (468 bis 470), Schlüssel aus dem Wortlaut-Plan.

**Rückweg-Link** wie Reset-Link (400 bis 401):
```php
					<a class="findling-filters__reset" href="<?php p($resetUrl); ?>"><?php p($l->t('Reset all filters')); ?></a>
```
**Leerzustand** als Zweig im Block `findling-empty` (523 bis 548), hinter `$showEmpty` (Kommentar 488 bis 522: nie
neben einem Banner, keine Zahl, kein Wort über Rechte). Filterzeile (Block ab 326) und Pager (557 ff.) in der
Similar-Ansicht nicht rendern.

---

### `php/css/search.css`

**Analog** `.findling-filters__reset` (313 bis 325) für einen unterstrichenen Satz-Link, Hover-Gruppe 274 bis 281
erweitern; Kommentar im Stil 309 bis 312. Achtung: `.findling-hit__link` ist `display: grid` (348 bis 359), der neue
Link steht als Geschwister darunter, nicht im Grid. Gate "no dash" gilt für Seitendateien.

---

### `php/l10n/*` (16 Dateien) und `docs/l10n-*.md` (5 Tabellen)

**Analog** `de.json:259 bis 260`, `de.js:260 bis 261`:
```json
        "Remove filter %s": "Filter %s entfernen",
        "Reset all filters": "Alle Filter zurücksetzen",
```
`de_DE.*` byte-identisch zu `de.*` (Gate test_admin_ui_contract.py:3626 bis 3630). Sprachtabelle nach
`docs/l10n-french.md:387`:
```
| `Reset all filters` | Alle Filter zurücksetzen | Réinitialiser tous les filtres |
```
de/fr zeichengleich aus 35-WORTLAUT.md, übrige Sprachen als Maschinenentwurf unter Vorbehalt (Satz aus 3622 bis 3623).

---

### `php/tests/Unit/*Test.php` (nur CI, lokal kein PHP)

**Analoge Fälle:** `SearchServiceTest.php:325` (`testANodeThatResolvesButIsNotReadableIsStillNotAHit`), `:547`
(`testExcerptsAreOnlyRequestedAfterTheRecheck`), `:588`; Helfer `service()` 104, `caps()` 119, `user()` 139,
`readableFile()` 207, `folderResolvingNothing()` 230. Für `similar`: "Container wird nie gefragt, wenn die Quelle
nicht lesbar ist" (Warnzeichen aus Pitfall 1). `ExAppServiceTest.php:154, 165` für Antwortfilterung,
`PageControllerTest.php:369 ff.` für Parameterverwerfung.

---

### `.planning/phases/35-*/35-WORTLAUT.md` (doc, Owner-Abnahme)

**Analog:** `34-WORTLAUT.md`.

**Kopf** (1 bis 23): Titel "Phase 35: Wortlaut-Entwurf (de, en, fr)", Stand/Status-Zeile, Grundlage, Regelliste
(Französisch nach `docs/l10n-french.md`, Infinitiv, keine Zahl über fremde Dateien).

**Schlüsseltabelle** (360 bis 363):
```
| Schlüssel (en) | de | fr | Platzhalter |
|---|---|---|---|
| ... | ... | ... | keine |
| Steps in the documentation (Bestand, wiederverwendet) | Schritte in der Dokumentation | Étapes dans la documentation | keine |
```
**Fragen an den Owner** (433 bis 477) als O-Nummern mit (a)/(b) und "Empfehlung:" (z. B. Leerzustand, aria-Label,
Messfrage `de.jsonl` 42 oder 120 aus Open Question 1). **Vorab-Prüfung** (482 bis 494, Sperrwort, Geheimnisse,
Gedankenstriche). **Owner-Abnahme** (496 bis 519) mit wörtlichem Owner-Wort und "Folgen für 35-0x".

---

### `docs/measurements/2026-10-aehnlich-distanzen/` (Wave-0) und Messskript

**Analog Bericht:** `2026-09-06-vektordistanzen/README.md` (Anlass, "Die zwei Verdikte, zuerst", Ableitung der
Schwelle auf der int8-L2-Skala). **Regel-Kopf** aus `2026-10-ordnerfilter/README.md:9 bis 20`:
```
## 1. Entscheidungsregel (vor der Messung festgelegt)

Gewählt wird die kleinste Variante, bei der
1. ...
Erfüllt keine Variante die Regel, wird keine still gewählt.
```
**Analog Skript:** `scripts/dev/vector_distances.py` (866 Zeilen): Modi `--selftest`, `--testset`, `--corpus`,
`--derive` (204 bis 213), `distances_to` (243), `corpus_stock` (477), `near_enough_rows` (543). Ein neuer Modus
"Dokument-Mittel gegen Dokument" oder ein eigenes Skript im `skripte/`-Ordner; gefahrene Skripte nachträglich
nicht ändern. Tests: `backend/tests/test_vector_distances.py`.

---

### `docs/measurements/2026-10-granite-vergleich/` (doc + Skripte + Rohdaten)

**Analog Bericht Qualität:** `2026-09-05-modellqualitaet/README.md` (Gliederung: Verdikte zuerst, Umgebung,
Modellfassungen, Kommandozeile, Testset, Tabellen je Sprache, paarweise Auswertung, "Nachvollziehen").
**Analog Box-Bericht:** `2026-10-abnahme-anfahrt/README.md` (Umfang und Abweichungen, Abbild, Speicher je Zelle,
Durchsatz je Zelle, Kosten gegen den Deckel, Runbook-Belege, Owner-Entscheide, Abbau und Schlusskosten) und
`2026-09-vergleichsmessung-m7g/README.md` Abschnitt 7 (Laufzeit, 26 h 37 min Bezug) und 17 (Kosten und Verbleib).

**Skript-Kopf** (`2026-09-vergleichsmessung-m7g/skripte/94-grundlast.sh:1 bis 13`):
```sh
#!/bin/sh
# The hard limit, then the idle base load, in the form of 63-grundlast.sh.
#
# The limit first, and read back out of the cgroup: a register throws it away
# (pitfall 4), and a run that measures against 4 GB when it means to measure
# against 2 measures nothing at all. Nothing is measured before that line is
# proven.
```
Shebang Pflicht, kein Maschinenpfad, kein Passwort auf der Kommandozeile, kein CR, kein Dash (NARROW_SCOPE).
Ablaufdatei nach `skripte/00-ablauf.md`. Rohdaten-Nummern wie `2026-10-abnahme-anfahrt/rohdaten/`
(`01-vorbedingungen.txt`, `02-rechenblatt-freigabe.txt`, `03-aufbau-arm.txt`, `08-abbau-boxen.txt`,
`90-kosten.txt`). Box-Werkzeug `scripts/ops/aws_box.sh` (`prices|create|...|status|stop|destroy`, Zeile 78),
Deckel nach `docs/runbook-messbox.md` Abschnitt 2 (Zeile 101 ff.).

---

### `scripts/dev/model_quality.py` (utility, transform)

**Analog:** dieselbe Datei.

**Argument-Muster** (109 bis 120):
```python
    parser.add_argument(
        "--prefixes",
        required=True,
        choices=PREFIX_CHOICES,
        help="whether the E5 prefixes query: and passage: are set",
    )
```
`--pooling` mit `choices=("mean", "cls")` und **`default="mean"`** (nicht `required`), damit alte Aufrufe und Tests
gleich bleiben. Pooling-Stelle (220):
```python
        rows.append(mean_pool(np.asarray(hidden, dtype=np.float32), attention_mask))
```
plus neue reine Funktion `cls_pool(hidden)` (`hidden[:, 0, :]`) neben `mean_pool` (224 bis 229), Wahl durchreichen
über `measure()` (327 bis 354) und `format_report()` (291) als Kopfzeile. Pad-Token liest `_pad_token` (177 bis 186)
schon aus `special_tokens_map.json`; für granite prüfen, ob die Datei vorhanden ist, sonst um
`tokenizer_config.json` erweitern (Pitfall 12). Fehler über `MeasurementError` und `REFUSED:` (361 bis 363).

**Tests** `backend/tests/test_model_quality.py`: Modul per Pfad laden (Zeile 25 ff.), pure Teile ohne onnxruntime
testen; Positivkontrolle "cls != mean" auf einem kleinen Array.

---

### `scripts/dev/quantize_model.py` (unverändert)

Aufruf mit Fenster (78 bis 99), Standardwerte NICHT ändern:
```
cd backend && uv run --group quantize python ../scripts/dev/quantize_model.py --input <fp32> --output <int8> --min-bytes 85000000 --max-bytes 110000000
```
Die Ablehnungsmeldung (106 bis 110) nennt "81.7 percent of this model" e5-spezifisch; im README erklären, dass bei
granite rund 71 Prozent gelten.

---

### `.planning/phases/35-*/35-DEDUP-NOTIZ.md` (doc, Entscheidungsvorlage)

**Kein direktes Analog** für eine Designnotiz. Formvorlage: Abschnitt "(E) Fragen an den Owner" in
`34-WORTLAUT.md:433 bis 477` (Optionen (a)/(b)/(c), danach "Empfehlung:" mit Begründung), Inhalt aus 35-RESEARCH.md
"Architektur STR-03" (Sachstand-Tabelle, NC-Fakten, Wege A bis C). Keine Nutzer-, Host- oder Share-Namen aus Issue
#25. Sachstand der bestehenden Mehrfachzählungs-Anzeige: `docs/admin-page.md:130 bis 145`.

## Shared Patterns

### Rechtegrenze: ein Recheck-Weg
**Source:** `php/lib/Service/SearchService.php:568 bis 587` (`readableFile`, `readableNode`)
**Apply to:** `SearchService::similar` (Quelle und jeder Nachbar)
```php
	public static function readableFile(Folder $userFolder, int $fileId): ?File {
		return self::readableNode($userFolder->getFirstNodeById($fileId));
	}
```
Gate `backend/tests/test_php_acl_boundary.py:85` (`RESOLUTION_REGISTER`). Titel, Pfad, Mime, Datum nur aus dem
bestätigten Knoten (SearchService.php:439 bis 458).

### Container-Vorfilter nur über `_permit`
**Source:** `backend/src/findling/index/search.py:221 bis 237`
**Apply to:** `similar_candidates`, sonst nichts. Zählgates `test_search_library.py:309`, `test_semantic_boundary.py:252`.

### Undeklarierte Inhaltsroute
**Source:** `backend/appinfo/info.xml:283 bis 295`, `test_info_xml_defaults.py:120 bis 140`, `test_semantic_boundary.py:68 bis 73`
**Apply to:** `/similar`; beide Ratschen im selben Commit wie die Route.

### Fehler werden leer, Logs ohne Inhalt
**Source:** `backend/src/findling/api/snippets.py:239 bis 244`, `api/search.py:342`; PHP `ExAppService.php:564 bis 572`
**Apply to:** `api/similar.py`, `ExAppService::similarCandidates`. Nur Typname bzw. statischer Satz, Zählwerte als Kontext.

### Serverseitige GET-Zustände
**Source:** `php/lib/Controller/PageController.php:773 bis 775` (`filterUrl`), `1073 bis 1081` (`pageUrl`)
**Apply to:** `similarUrl` je Treffer und `backUrl`; immer über `$this->urlGenerator->linkToRoute('findling.page.index', ...)`.

### Leerzustände ohne Zählorakel
**Source:** `php/templates/search.php:488 bis 522` (Kommentar), Gates `test_admin_ui_contract.py` um 1660 und 1790
**Apply to:** Leerzustand und "nicht verfügbar" der Similar-Ansicht.

### Baumhash- und Schlüsselzahl-Journal
**Source:** `backend/tests/test_measurement_scripts.py:960 bis 984` und `2025 bis 2033`; `test_admin_ui_contract.py:3615 bis 3667`
**Apply to:** jeder Plan, der `php/**/*.php`, `backend/src/findling/**/*.py` oder die Kataloge anfasst.

### Regel vor der Messung
**Source:** `docs/measurements/2026-10-ordnerfilter/README.md:9 bis 20`
**Apply to:** Wave-0-Distanzlauf und granite-Bericht; README mit Regel committen vor dem ersten Lauf.

### Wortlaut vor Code
**Source:** `.planning/phases/34-umstiegsweg/34-WORTLAUT.md` (Kopf, Tabelle, Fragen, Owner-Abnahme)
**Apply to:** alle neuen UI-Sätze von STR-01 (D-35-08), de/fr zeichengleich in die Kataloge.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `.planning/phases/35-*/35-DEDUP-NOTIZ.md` | doc | , | Keine frühere Designnotiz; nur die Optionenform aus 34-WORTLAUT.md (E) als Formvorlage, Inhalt aus 35-RESEARCH.md STR-03 |
| `cls_pool` in `scripts/dev/model_quality.py` | utility | transform | Kein CLS-Pooling im Repo (Produkt und Messwerkzeug sind e5-fest); granite-Konfiguration `1_Pooling/config.json` laut Research ist die Quelle |

## Metadata

**Analog search scope:** `backend/src/findling/{api,index,store,embed}`, `backend/src/findling/{main,config}.py`,
`backend/appinfo/info.xml`, `backend/tests/`, `php/lib/{Service,Controller}`, `php/templates/search.php`,
`php/css/search.css`, `php/js/search.js`, `php/l10n/`, `php/tests/Unit/`, `scripts/dev/`, `scripts/ops/`,
`docs/measurements/`, `docs/runbook-messbox.md`, `.planning/phases/34-umstiegsweg/`
**Files scanned:** rund 35 (davon 14 gezielt gelesen)
**Pattern extraction date:** 2026-10-19
**Hinweis:** Keine Tests und keine Browser gestartet (RAM-Vorgabe unter 4 GB); reine Lese-Analyse.
