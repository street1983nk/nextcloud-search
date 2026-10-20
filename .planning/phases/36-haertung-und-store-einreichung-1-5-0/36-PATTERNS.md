# Phase 36: Härtung und Store-Einreichung 1.5.0 - Pattern Map

**Mapped:** 2026-10-20
**Files analyzed:** 38 (neu/geändert, inkl. Katalog- und Doku-Gruppen)
**Analogs found:** 36 / 38

Alle Zeilenangaben gegen den Arbeitsbaum vom 20.10.2026 gelesen. Code bleibt Englisch und ASCII, Umlaute nur in deutscher Prosa.

## Zwei Befunde dieser Analyse, die RESEARCH.md nicht nennt (Planner bitte einplanen)

1. **Die CI-Saat `seed-bomb.zip` wechselt die Klasse.** `scripts/ci/make_upgrade_seed_formats.py:26-30, 94-99, 247-254` baut die Bombe mit Tiefe 3 UND einem Nullen-Mitglied von `1 + 258*4065` Bytes (>= `ARCHIVE_RATIO_MIN_BYTES`) weit über `ARCHIVE_MAX_RATIO`. In `archive._read_zip` (Zeile 386-391) läuft die Verhältnisprüfung auf der äußersten Ebene, BEVOR ein Mitglied gelesen wird, also bevor die Tiefe greift. Mit der Pattern-1-Zuordnung (`zip_ratio` -> blocked_malicious) endet die Saat als `skipped/blocked_malicious`, und `deploy-harp.yml:5700` und `:6134-6138` (Erwartung `skipped/archive_limit`) werden rot; ebenso die Zählerzeile `:5615-5644` und die Summary `:6224`. RESEARCH.md Tabelle "Neue Urteilsklasse" Zeile 14 sagt "nein", das stimmt nicht. Entweder Saat auf reine Tiefe umbauen (Nullen-Mitglied raus) oder die Erwartungen in deploy-harp.yml auf die neue Klasse ziehen. Entscheid in den Vorabplan.
2. **Bestehende Korpusfälle in `backend/tests/test_phase31_audit.py` ändern ihr Urteil.** `"name-nul-and-both-separators"` (Zeile 272-279, `..\\..\\boese/../x\x00` und `/abs/../../y.txt`) erwartet heute `(State.INDEXED, None)`; mit `zip_traversal` wird daraus blocked_malicious. `"lying-huge"` (Zeile 238-243, declared 0xFFFFFFF0) bleibt nur dann `archive_limit`, wenn `take_declared` (Summe > 256 MiB, Zeile 386) VOR der Verhältnisschleife bleibt; Reihenfolge in `_read_zip` nicht umdrehen. `"inner-zip-with-overlap"` (Zeile 292-297) erwartet INDEXED: Überlappung in einer INNEREN ZIP wird heute über `_is_overlap` nur auf der Außenebene als Urteil gefasst; festlegen, ob `zip_overlap` auch innen sperrt.

## File Classification

| Neue/geänderte Datei | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/src/findling/extract/errors.py` | model (Urteilsliste) | transform | eigene Zeilen 89-167, 246-254 (`ARCHIVE_LIMIT`, `failed(..., detail=)`) | exact |
| `backend/src/findling/extract/archive.py` | service (Extraktor) | file-I/O | eigene Zeilen 122-138, 210-233, 373-394 | exact |
| `backend/src/findling/extract/odf.py` | service (Extraktor) | file-I/O | `archive.py` `count_central_directory` + `_is_overlap` | role-match |
| `backend/src/findling/extract/office.py` | service (Extraktor) | file-I/O | eigene `_too_large_to_read` Zeile 52-81 | exact |
| `backend/src/findling/extract/image.py` | service (Extraktor) | file-I/O | eigene Zeile 250-265 (`DecompressionBombError`) | exact |
| `backend/src/findling/extract/mail.py` | service (Extraktor) | file-I/O | `archive.py` Budget/Tiefe | role-match |
| `backend/src/findling/store/schema.sql` | migration | CRUD | `file_errors` Zeile 127-142 | exact |
| `backend/src/findling/store/repo.py` | model/repository | CRUD | `STATE_REASONS` 301-335, Reconcile-SQL 592-615, Methoden 1374-1418 | exact |
| `backend/src/findling/nc/client.py` (neue Funktion `gone_storages`) | client | request-response | `mounts()` Zeile 639-655 | exact |
| `backend/src/findling/nc/files.py` (`FileList.gone_storages`) | client wrapper | request-response | `FileList.mounts()` Zeile 257-284 | exact |
| `backend/src/findling/nc/queue.py` | config (Wire-Fallbacks) | transform | eigene Zeilen 170-196 | exact |
| `backend/src/findling/worker/reconcile.py` | service (Worker) | batch | eigene `run_once` 368-427, `_hand_over` 738-760 | exact |
| `backend/src/findling/main.py` | config (Logging) | , | eigene Zeile 924 | exact |
| `php/lib/Controller/ReconcileController.php` (`GET /storages/gone`) | controller | request-response | `mounts()` Zeile 100-140 + `rejectForeignCaller()` 356-368 | exact |
| `php/lib/Service/StorageService.php` oder `FileStateService.php` (Abfrage `oc_storages`) | service | CRUD (read) | `FileStateService::verdictsFor` 591-615 | role-match |
| `php/lib/Service/FileStateService.php` (Listen) | model | , | eigene Zeilen 119, 171 | exact |
| `php/lib/Service/AdminViewService.php` (`REASON_TEXT`) | config (Texte) | , | eigene Zeile 527-530 | exact |
| `php/lib/Controller/ProfileController.php` (Docblock) | controller | , | eigene Zeile 41-52 | exact |
| `php/js/admin.js` (Detail-Label) | component | , | eigene Zeile 748-810 | exact |
| `php/l10n/*.js` / `*.json` (16) | config (Katalog) | , | Schlüssel `"ZIP file over the safety limits"` (de.js:115, de.json:114) | exact |
| `docs/l10n-{dutch,french,italian,portuguese,spanish}.md` | docs | , | Zeilen `ZIP file over the safety limits` (z. B. l10n-french.md:241) | exact |
| `docs/formats.md` | docs | , | Zeile 105 `archive_limit` | exact |
| `backend/tests/hostile.py` (NEU) | test utility | transform | `test_phase31_audit.py` 151-226 (`Member`, `build_zip`) + `conftest.py` 578-719 (`build_cfb`) | exact |
| `backend/tests/test_phase36_hostile_corpus.py` (NEU) | test | file-I/O | `test_phase31_audit.py` 105-148, 228-337 | exact |
| `backend/tests/test_phase36_audit.py` (NEU) | test | , | `test_phase35_audit.py`, `test_phase31_audit.py` 1019-1100 | exact |
| `backend/tests/test_phase31_audit.py` (Generatoren raus, Gen-3-Liste) | test | , | eigene Zeilen 1075-1099 | exact |
| `backend/tests/test_reconcile.py` / neuer Reconcile-Test | test | batch | `test_phase31_audit.py` `_Queue` 1105-1130, `_Files` 1265-1304 | exact |
| `backend/tests/test_admin_ui_contract.py` (348 -> neu) | test (Gate) | , | eigene Zeile 3626-3680 | exact |
| `backend/tests/test_measurement_scripts.py` (Baumhashes) | test (Gate) | , | eigene Zeile 1008-1014, 2086-2088 | exact |
| `php/tests/Unit/ReconcileControllerTest.php` | test | request-response | eigene `setUp` 50-95 | exact |
| `scripts/release/corresponding_source.py` | utility | file-I/O | eigene `ARCHIVES` Zeile 81-114 | exact |
| `THIRD-PARTY.md` | docs | , | eigene Zeile 173, 205-227 | exact |
| `.github/workflows/release.yml` | config (CI) | batch | eigene Zeilen 477-515 | exact |
| `.github/workflows/deploy-harp.yml` (`UPGRADE_FROM_TAG`, Ausschlüsse, Bombe) | config (CI) | batch | eigene Zeilen 89-148, 5258-5348 | exact |
| `.github/workflows/integration.yml` (M-32-02) | config (CI) | batch | Job `reconcile-and-dach` Zeile 2365, 2621-2729 | exact |
| `scripts/ci/make_upgrade_seed_formats.py` | utility | file-I/O | eigene `_bomb()` 247-254 | exact |
| `backend/appinfo/info.xml`, `php/appinfo/info.xml`, `CHANGELOG.md`, `docs/embeddings.md`, `docs/store-listing.md`, `docs/admin-page.md`, READMEs | docs/config | , | Entwürfe `docs/store-listing.md` ab Zeile 2020 | role-match |
| `.planning/phases/36-.../36-WORTLAUT.md` (Vorabplan) | planning artefact | , | `.planning/phases/35-.../35-WORTLAUT.md` | exact |

## Pattern Assignments

### `backend/src/findling/extract/errors.py` (model, transform)

**Analog:** eigene Datei, Vorbild `ARCHIVE_LIMIT` (Plan 31-02, Commit `aa498caf`).

**Enum-Eintrag** (Zeile 113-116), neue Zeile direkt unter `ARCHIVE_LIMIT`, Kommentar im selben Stil:
```python
    LEGACY_FORMAT = "legacy_format"  # an old OLE container under an OOXML extension
    # a variant of a readable format the reader cannot map: an image encoding, Word 95, BIFF before 5
    UNSUPPORTED_VARIANT = "unsupported_variant"
    ARCHIVE_LIMIT = "archive_limit"  # a ZIP archive over the depth, size, count or ratio limits (D-31-03)
```

**Geschlossene Liste** (Zeile 133-152), Eintrag unter `State.SKIPPED`:
```python
            Reason.UNSUPPORTED_VARIANT,  # an honest verdict on a variant, not a broken file
            Reason.ARCHIVE_LIMIT,  # a safety limit of the container, not a broken file
        }
```

**`skipped()` bekommt `detail`** (heute Zeile 246-254), exakt wie `failed()`:
```python
    @classmethod
    def skipped(cls, reason: Reason) -> ExtractionOutcome:
        """A file we decided not to index. Carries no text, by construction."""
        return cls(state=State.SKIPPED, reason=reason)

    @classmethod
    def failed(cls, reason: Reason, *, detail: str | None = None) -> ExtractionOutcome:
        """A file we wanted to index and could not. This is what the status page counts."""
        return cls(state=State.FAILED, reason=reason, detail=detail)
```
Der Feldkommentar `detail` (Zeile 214-222) sagt heute "The class of the exception behind a failure"; erweitern um "or the signature code of a refused file", sonst lügt der Docstring.

---

### `backend/src/findling/extract/archive.py` (service, file-I/O)

**Analog:** eigene Datei.

**Ausnahme mit optionalem Code** (heute Zeile 122-123, nackt):
```python
class OverLimit(Exception):
    """A limit of D-31-07 is reached; the whole ZIP file is skipped(archive_limit)."""
```
Umbau nach RESEARCH.md "Code Examples" (`__init__(self, signature: str | None = None)`). Alle `raise OverLimit` in `_ArchiveBudget.take_*` (Zeile 170-188) bleiben ohne Signatur (archive_limit), nur Zeile 388-391 (Verhältnis) bekommt `OverLimit("zip_ratio")`.

**Meldungsvergleich ohne Log** (Zeile 115, 136-138), Muster für `zip_overlap` und für XML-Amplification:
```python
_OVERLAP = "Overlapped entries"

def _is_overlap(error: Exception) -> bool:
    """True for zipfile's refusal of overlapping entries. The message is compared, never logged."""
    return isinstance(error, BadZipFile) and str(error).startswith(_OVERLAP)
```

**Urteilsstelle** (Zeile 210-222), hier wird verzweigt:
```python
    try:
        _read_zip(Path(path), "", 1, budget, sections)
    except OverLimit:
        return ExtractionOutcome.skipped(Reason.ARCHIVE_LIMIT)
    except _UNREADABLE_DIRECTORY as error:
        if _is_overlap(error):
            return ExtractionOutcome.skipped(Reason.ARCHIVE_LIMIT)
        return ExtractionOutcome.from_exception(error)
```

**Vorzählung wiederverwenden** (Zeile 236-262, `count_central_directory` ist schon öffentlich; `_central_directory` Zeile 265-273 ist privat). Für odf/office die öffentliche Funktion nutzen, `_central_directory` nur öffentlich machen, falls die Verzeichnislänge separat gebraucht wird:
```python
def count_central_directory(handle: BinaryIO, size: int, *, limit: int) -> int:
    """The number of headers zipfile would read from this directory, at most ``limit + 1``.
    ...
    Raises CorruptDirectory where zipfile would raise BadZipFile, and
    OverLimit when the directory is longer than ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES.
    """
```

**Reihenfolge in `_read_zip`** (Zeile 373-394) nicht ändern: Verzeichnislänge, Zählung, `take_declared(sum)`, DANN Verhältnisschleife, DANN Mitglieder. Die Traversal-Prüfung (`zip_traversal`) gehört in die Schleife über `members` vor `_read_member`, auf `info.filename` (roher Name), nie auf `clean_display_name` (Zeile 402).

---

### `backend/src/findling/extract/odf.py` und `office.py` (service, file-I/O)

**Analog:** `office._too_large_to_read` (Zeile 52-81) ist bereits die "Prüfung vor dem Loader"; die Vorzählung (`package_entries`) gehört VOR das `ZipFile(path)` dort und in `odf.extract_odf` vor Zeile 64:
```python
    try:
        with ZipFile(path) as archive:
            declared = [info.file_size for info in archive.infolist()]
    except (BadZipFile, OSError):
        return None
```
`ZipFile()` baut alle ZipInfo-Objekte (1 Mio. Einträge = 454 MiB, Befund F3). Deshalb zuerst `Path(path).open("rb")` + `archive.count_central_directory(handle, size, limit=ARCHIVE_MAX_ENTRIES)`; `CorruptDirectory` dort an den Loader weiterreichen (gleiche Haltung wie `return None` oben: "A package that will not even open is left to the loader").

**XML-Bombe** in odf.py (Zeile 80-85) und an den drei `from_exception`-Stellen in office.py (Zeile 96-97, 119-120, 168-169):
```python
    try:
        root = etree.fromstring(content, parser=_PARSER)
    except etree.XMLSyntaxError as error:
        return ExtractionOutcome.from_exception(error)
```
Davor `_is_entity_bomb(error)` (Skizze RESEARCH.md Zeile 492-501) -> `ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail="xml_entities")`. Achtung office.py: python-docx/pptx werfen beim Laden, openpyxl read_only erst beim Iterieren der Zeilen (Zeile 171ff., `try` um `iter_rows`), expat-Fehler sind `xml.etree.ElementTree.ParseError`, nicht in `_BROKEN_PACKAGE`. Ein Fallback-Test baut die echten Ausnahmen (Muster `test_extract_errors.py`).

---

### `backend/src/findling/extract/image.py` (service, file-I/O)

**Analog:** eigene Zeile 250-257:
```python
    try:
        opened = Image.open(path)
    except Image.DecompressionBombError:
        # Pillow's own refusal, which arrives at twice our budget and before a
        # single row is decoded. A decision and not a failure: nobody could have
        # read this file, and skipped(too_large) is what an admin can act on.
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
```
Hier verzweigen: Pixel je Dateibyte > Schwelle (Vorabplan, A1) -> `skipped(BLOCKED_MALICIOUS, detail="image_pixels")`, sonst `TOO_LARGE`. Die Pixelzahl steht nicht strukturiert im Ausnahmeobjekt, und die Meldung wird nicht geparst (Pattern 3). Weg: `Image.open` ist lazy und liest nur den Header; ein zweites `Image.open(path)` unter lokal aufgehobenem `MAX_IMAGE_PIXELS` (try/finally zurücksetzen, nur `.size` lesen, nie `load()`) liefert Breite x Höhe ohne Dekodierung; Dateigröße per `os.path.getsize(path)`. Alternativ den Vergleich vor das erste `Image.open` legen. Positivkontrolle bleibt `test_phase31_audit.py:1060-1062` (`control.heic` 8000x7500 muss `TOO_LARGE` bleiben).

---

### `backend/src/findling/extract/mail.py` (service, file-I/O)

**Analog:** Docstring Zeile 27 und 50 (1000-fache Verschachtelung endet heute in `RecursionError` -> `failed(corrupt)`). Kein vorhandener Tiefenzähler; Muster ist `_ArchiveBudget` in archive.py (Zeile 141-194): eine Zahl, die je Ebene sinkt, bei Unterschreitung eine eigene Ausnahme, Urteil an EINER Stelle in der Eintrittsfunktion `extract_eml` (Zeile 187). Testfall existiert schon: `test_phase31_audit._nested_rfc822(levels)` Zeile 361.

---

### `backend/src/findling/store/schema.sql` (migration, CRUD)

**Analog:** `file_errors` Zeile 127-142, Kommentarblock und `IF NOT EXISTS` übernehmen:
```sql
-- IF NOT EXISTS like everything in this file, so an existing database gets the
-- table on its next open without a reindex and without a new SCHEMA_VERSION.
-- A database that lost it loses the diagnosis and nothing else.
CREATE TABLE IF NOT EXISTS file_errors (
    file_id     INTEGER PRIMARY KEY,
    error_class TEXT NOT NULL,      -- module.qualname, [A-Za-z0-9_.], at most 200
    recorded_at INTEGER NOT NULL
);
```
Neue Tabelle `vanished_storages (storage_id INTEGER PRIMARY KEY, first_missing_at INTEGER NOT NULL)` am Dateiende, Kommentar im Stil von `reconcile` (Zeile 93-108: "Losing it therefore costs ..."; hier: Verlust setzt die Karenz neu, kostet nie ein Dokument). `repo.SCHEMA_VERSION` ("2", Zeile 64) bleibt.

---

### `backend/src/findling/store/repo.py` (repository, CRUD)

**Analog:** eigene Datei.

**Zweite geschlossene Liste** (Zeile 301-335), Zeile unter `"archive_limit"`:
```python
            "unsupported_variant",  # an honest verdict on a variant, not a broken file
            "archive_limit",  # a safety limit of the container, not a broken file
        }
```

**Detailcode-Form** (Zeile 550-555) gilt schon für jeden Zustand; `zip_ratio` usw. passen auf `[A-Za-z0-9_.]{1,200}`:
```python
_ERROR_CLASS_SHAPE: Final = re.compile(r"[A-Za-z0-9_.]{1,200}")
```
Prüfen, dass `record()` (ab Zeile 903, Docstring 936) `file_errors` nicht nur bei `state == "failed"` schreibt; Docstring "module.qualname (D-29-09)" erweitern.

**SQL-Konstanten-Stil** (Zeile 592-615) für neue Abfragen `_LIVING_STORAGES_SQL`, `_MARK_VANISHED_SQL` (`INSERT ... ON CONFLICT(storage_id) DO NOTHING` + `SELECT first_missing_at`), `_CLEAR_VANISHED_SQL`, `_FORGET_STORAGE_*` (reconcile-, mounts-, vanished-Zeile):
```python
_RECONCILE_STATE_SQL: Final = """
SELECT MAX(finished_at), SUM(CASE WHEN after_file_id > 0 THEN 1 ELSE 0 END) FROM reconcile
"""
```

**Methodenmuster** (Zeile 1374-1418), Schreiben immer in `with self._transaction():`, Lesen direkt:
```python
    def rewind_reconcile_walk(self) -> None:
        """Put every reconcile bookmark back at the front (:data:`_REWIND_RECONCILE_SQL`)."""
        with self._transaction():
            self._conn.execute(_REWIND_RECONCILE_SQL)

    def reconcile_state(self) -> ReconcileState:
        """When the last mount finished, and how many stand mid-walk."""
        row = self._conn.execute(_RECONCILE_STATE_SQL).fetchone()
```
**Banding** für `living_file_ids(storage)` / IN-Listen: Muster `known_etags` Zeile 1331-1347 (`_ACL_BAND`, nur Platzhalterzahl interpoliert, `# noqa: S608` mit Begründung).

**F4 (ewig unfinished):** `forget_storage()` muss die `reconcile`-Zeile mitlöschen, sonst bleibt `_RECONCILE_STATE_SQL` > 0 und `_is_due` (reconcile.py:810-812) feuert jeden Takt.

---

### `backend/src/findling/nc/client.py` + `nc/files.py` (client, request-response)

**Analog Transport** `client.mounts` (Zeile 639-655):
```python
async def mounts(nc: AsyncNextcloudApp) -> object:
    """Every mount the crawl walks, and therefore every mount worth comparing.
    ...
    Returned untyped on purpose, exactly like the queue calls. ...
    """
    return await nc._session.ocs(
        "GET",
        "/ocs/v2.php/apps/findling/mounts",
    )
```
Neue `gone_storages(nc, ids)` mit `params={"ids[]": [...]}` wie `files_slice` (Zeile 683-687).

**Analog Validierung** `FileList.mounts` (files.py Zeile 257-284): `except Exception` -> Warnung ohne Inhalt, `_mapping`/`_sequence`/`_positive_int` (Zeile 153-183) für jede ID. Abweichung: Rückgabe `set[int] | None`, `None` bei jedem Fehler (auch 404 eines 1.4.x-Companions) = "unbekannt", Karenz statt Sofortlöschung (RESEARCH.md Pitfall 5):
```python
        try:
            answer = await read_mounts(self._nc)
        except Exception:
            LOGGER.warning("could not read the mount list, skipping this round")
            return MountResult(unavailable=True)
```
Zusätzlich: nur IDs zurückgeben, die auch gefragt wurden (Schnittmenge), damit ein fehlerhafter Companion nie fremde Storages löschen lässt.

---

### `backend/src/findling/nc/queue.py` (config, transform)

**Analog:** eigene Zeile 170-196, je eine Zeile in den Tabellen 2 und None ergänzen, Generation 3 bleibt leer, `VERDICTS_GENERATION` bleibt 3 (Zeile 146):
```python
# archive_limit is an archive over a safety limit; the nearest code an older
# companion knows is too_large, "over a limit" as well.
_SKIPPED_FALLBACK_BY_GENERATION: Final[Mapping[int | None, Mapping[str, str]]] = MappingProxyType(
    {
        3: MappingProxyType({}),
        2: MappingProxyType({"archive_limit": "too_large"}),
        None: MappingProxyType({**SKIPPED_FALLBACK_WITHOUT_SIGNAL, "archive_limit": "too_large"}),
    }
)
...
        2: MappingProxyType({"archive_limit": "corrupt"}),
        None: MappingProxyType(
            {
                "system_file": "corrupt",
                ...
                "archive_limit": "corrupt",
            }
        ),
```
`SKIPPED_FALLBACK_WITHOUT_SIGNAL` (Zeile 162-168) NICHT erweitern: es ist öffentlich und auf genau drei Paare festgelegt (Plan 31-11 matcht dagegen; reconcile.py:136 baut `_SUBSTITUTES` daraus).

---

### `backend/src/findling/worker/reconcile.py` (service, batch)

**Analog:** eigene Datei.

**Einhängepunkt** nach dem vollständigen Walk (Zeile 412-427), Nachlauf zwischen Schleife und `_report(ROUND_WALKED, ...)`, nur wenn `found.mounts` nicht leer:
```python
        tally = _Tally()
        for mount in found.mounts:
            ended = await self._walk(store, files, queue, mount, tally, catchup_round=catchup)
            if ended is not None:
                return self._report(ended, len(found.mounts), tally)

        self._reset_cooldown()
        ...
        return self._report(ROUND_WALKED, len(found.mounts), tally)
```

**Konstanten-Stil** (Zeile 152-164: langer Begründungsblock über `Final`), für `VANISHED_STORAGE_GRACE_SECONDS: Final = 30 * 86_400` (fest, kein `FINDLING_*`-Schalter, D-36-05).

**Löschaufträge** ausschließlich über `_hand_over` (Zeile 738-760), nie über den Indexschreiber:
```python
        for file_ids, kind in ((stale, KIND_CONTENT), (missing, KIND_DELETE)):
            for start in range(0, len(file_ids), REQUEUE_BAND):
                band = list(file_ids[start : start + REQUEUE_BAND])
                result = await queue.requeue(band, kind=kind)
                if not result.ok:
                    LOGGER.warning("could not hand %d files of kind %s to the queue, ending the round", len(band), kind)
                    return False
        return True
```
Aufruf `self._hand_over(queue, (), ids)`; erst bei `True` `store.forget_storage`. Store-Aufrufe immer `await asyncio.to_thread(...)` (Zeile 392-394, 447). Zeitquelle `self._clock()` (Zeile 495), damit Tests die Uhr stellen. Log nur Zähler und Storage-IDs, keine Pfade.

**D-36-14:** abgeschalteter Findling-Schalter = Storage fehlt in Mountliste, `oc_storages`-Zeile existiert. Die Owner-Entscheidung sagt "keine Karenz, bestehende Mechanik wie Ausschlüsse"; die RESEARCH-Skizze behandelt das als "verschwunden" mit 30 Tagen. Das ist ein Widerspruch: PHP muss im `gone`-Endpoint zusätzlich "existiert, aber per Schalter abgewählt" melden können (z. B. `StorageService::isIndexedStorage`, Zeile 335), damit der Container nur für echt abgehängte Speicher stempelt. Im Plan klären.

---

### `backend/src/findling/main.py` (config)

**Analog:** eigene Zeile 203-206 und 924:
```python
def log_level() -> str:
    """Return the configured log level, falling back to info on anything unknown."""
    level = os.environ.get("FINDLING_LOG_LEVEL", "info").strip().lower()
    return level if level in KNOWN_LOG_LEVELS else "info"
...
    global _POLLER
    logging.basicConfig(level=log_level().upper())
```
Direkt nach Zeile 924 die zwei `getLogger("httpx"/"httpcore").setLevel(logging.WARNING)` unter `if log_level() != "debug":` (RESEARCH.md Zeile 527-533). Test mit caplog, Positivkontrolle `FINDLING_LOG_LEVEL=debug`.

---

### `php/lib/Controller/ReconcileController.php` (controller, request-response)

**Analog:** `mounts()` Zeile 100-140, Attribut-Trias voll qualifiziert (Grep-Gate zählt so, Docblock Zeile 51-55):
```php
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/mounts')]
	public function mounts(): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		try {
			...
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not list the mounts', ['exception' => $e]);
			return new DataResponse(['error' => 'Mount list is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['mounts' => $mounts]);
	}
```
**Eingabeliste** begrenzen nach `QueueController::intList` (Zeile 438-454, `MAX_LIST_LENGTH = 256` Zeile 82), bei Verstoß 400 nach Muster `badMount()` (Zeile 377-384, Werte nie loggen). Klassen-Docblock Zeile 21 ("Two routes, both reading") anpassen. Kein Eintrag in `OCS_WRITE_ALLOWLIST` (GET).

**Abfrage `oc_storages`:** Muster `FileStateService::verdictsFor` (Zeile 591-615):
```php
		foreach (array_chunk($wanted, self::MAX_LOOKUP) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('file_id', 'state', 'reason')
				->from(self::TABLE_NAME)
				->where($qb->expr()->in('file_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)));

			$result = $qb->executeQuery();
			while (($row = $result->fetch()) !== false) {
				...
			}
			$result->closeCursor();
		}
```
Auf `storages`/`numeric_id` umstellen; Antwort = gefragte IDs minus gefundene. StorageService hat heute KEIN `IDBConnection` (nur `fileAccess`), also entweder dort injizieren oder eine kleine eigene Methode im FileStateService-Stil. Unit-Test: `php/tests/Unit/ReconcileControllerTest.php` `setUp` (Zeile 50-95, `EX-APP-ID`-Callback Zeile 77-79) erweitern.

---

### `php/lib/Service/FileStateService.php`, `AdminViewService.php`, `ProfileController.php`, `php/js/admin.js` (Urteilskette PHP)

**FileStateService** Zeile 116-119 und 168-171, je eine Zeile nach `'archive_limit',`.

**AdminViewService::REASON_TEXT** Zeile 527-530 (Label, Abhilfe; Wortlaut aus 36-WORTLAUT.md, Vokabelregel: kein "Archiv" in deutscher Prosa):
```php
		'archive_limit' => [
			'ZIP file over the safety limits',
			'None. ZIP files that are nested too deep, too large, too densely packed or hold too many files are skipped so the container keeps running.',
		],
```
Falls die Abhilfe von `archive_limit` "too densely packed" verliert, ändert sich der Schlüssel (zählt in der Katalogzahl nicht, Muster Absatz in test_admin_ui_contract.py:3671-3673).

**ProfileController** Docblock Zeile 41-51, Konstante bleibt `VERDICTS_GENERATION = 3`.

**admin.js** Zeile 750-752 (Kommentar "only there for a failed file") und Zeile 802 (Label `'Error class: %s'`). Neues Label nur, wenn der Vorabplan es so entscheidet; dann `text(...)` mit Funktions-Ersatz beibehalten (WR-04, Zeile 793-796). Sichtbarkeit Zeile 810 hängt schon nur an `errorClass !== ''`.

---

### `php/l10n/*` (16), `docs/l10n-*.md` (5), `docs/formats.md`

**Analog:** Schlüssel `"ZIP file over the safety limits"` liegt in jeder `.js` auf Zeile 115 und jeder `.json` auf Zeile 114; neue Schlüssel direkt dahinter, damit der Diff je Datei an derselben Stelle steht. `de.json`/`de_DE.json` und `de.js`/`de_DE.js` müssen bytegleich sein (Gate test_admin_ui_contract.py:3638-3642). Sprachtabellen: Zeile nach `ZIP file over the safety limits` (z. B. `docs/l10n-french.md:241`, Spalten en | de | Zielsprache). `docs/formats.md:105` Zeile `| \`archive_limit\` (new) | Label | Abhilfe |`.

**Zahlengate** `backend/tests/test_admin_ui_contract.py:3680` `== 348` anheben, Begründungsabsatz im Docstring nach Muster Zeile 3626-3636 ("It stands at N since ...") und Aufzählung Zeile 3661-3679 ergänzen.

---

### `backend/tests/hostile.py` (NEU, test utility)

**Analog:** `test_phase31_audit.py` Zeile 151-226 (verschieben, nicht kopieren) und `conftest.py` Zeile 578-719.

**Record-Generator** (Zeile 154-196):
```python
@dataclass(frozen=True)
class Member:
    name: bytes
    data: bytes
    deflate: bool = False
    declared: int | None = None  # the uncompressed size the records claim, when not the true one
    offset: int | None = None  # the local header offset the directory claims, when not the true one
...
def build_zip(members: Sequence[Member], *, comment: bytes = b"") -> bytes:
    body = b""
    directory = b""
    for member in members:
        payload = _deflated(member.data) if member.deflate else member.data
        crc = zlib.crc32(member.data)
        declared = len(member.data) if member.declared is None else member.declared
        at = len(body)
        body += _local(member, payload, crc, declared)
        directory += _central(member, payload, crc, declared, at if member.offset is None else member.offset)
    return body + directory + _end(len(members), len(directory), len(body), comment)
```
**Import-Konvention:** wie `from conftest import build_cfb` (test_cfb.py:25, test_extract_documents.py:36), also `from hostile import build_zip, Member`. Dateiname ohne `test_`-Präfix, damit pytest ihn nicht sammelt. Achtung: `test_phase31_audit.py` hat ein EIGENES `build_cfb` (Zeile 564, andere Signatur als `conftest.build_cfb` Zeile 607); beim Verschieben Namen nicht kollidieren lassen.

Neue Generatoren (RESEARCH.md Tabelle "Was fehlt"): ODT/DOCX/PPTX/XLSX mit Billion Laughs (über `build_zip` mit `content.xml`/`word/document.xml`), Paket mit 1 Mio. reinen Zentralverzeichnis-Records (nur `_central` + `_end`, keine Nutzdaten, "Bombs declare their size and do not carry it", Docstring Zeile 18-19), PNG-IHDR 20000x20000 + IDAT aus deflate-Nullen, TIFF-IFD-Zyklus, Polyglotte. Rein deterministisch, nur ASCII, Umlaute als Escapes.

---

### `backend/tests/test_phase36_hostile_corpus.py` (NEU, test)

**Analog:** `test_phase31_audit.py` Zeile 76-148 und 228-337.

**Sandbox-Fixture und Prüfhelfer** (Zeile 105-138):
```python
@pytest.fixture(scope="module")
def worker() -> Iterator[sandbox.ExtractionWorker]:
    started = sandbox.ExtractionWorker(max_files=1000, timeout_seconds=CORPUS_DEADLINE_SECONDS)
    yield started
    started.stop()
...
def _named_and_quick(ran: Ran, worker: sandbox.ExtractionWorker) -> None:
    """The three promises of every case: a verdict with a name, a living worker, a short run."""
    assert ran.outcome.reason in STATE_REASONS[ran.outcome.state]
    assert ran.outcome.reason is not Reason.TIMEOUT
    assert ran.seconds < CASE_SECONDS
    assert worker.run(__file__, "application/x-not-allowed", 10).reason is Reason.MIME_NOT_ALLOWED
```
**Falltabelle + Parametrisierung** (Zeile 228-237, 326-337); für die neue Klasse ein fünftes Tupelfeld "Detailcode" ergänzen und `ran.outcome.detail` prüfen:
```python
_ZIP_CASES: dict[str, tuple[Callable[[], bytes], tuple[State, Reason | None], str, str | None]] = {
    # name: (builder, verdict, a word the text must hold, the finding the case stands for)
...
@pytest.mark.parametrize("case", list(_ZIP_CASES))
def test_every_zip_of_the_corpus_ends_in_a_named_verdict(
    case: str, worker: sandbox.ExtractionWorker, tmp_path: Path
) -> None:
    build, (state, reason), word, _ = _ZIP_CASES[case]
    ran, left = _corpus_case(worker, tmp_path, "korpus.zip", build(), ZIP)
    _expect(ran, state, reason, contains=word)
    assert left == ["korpus.zip"]
```
`assert left == [...]` ist der Zip-Slip-Beweis (nichts unter Mitgliedsnamen geschrieben); für Traversal-Fälle Pflicht.

---

### `backend/tests/test_phase36_audit.py` (NEU, test)

**Analog:** `test_phase31_audit.py` Log-Sonde Zeile 1019-1070 (SECRETS-Tupel Zeile 90-99, eigener frischer Worker, Positivkontrolle über `capfd`) und Wire-Test Zeile 1075-1099. Für Gen 3 die Menge ergänzen:
```python
_NEW_IN_GENERATION_2 = frozenset({"system_file", "legacy_format", "unsupported_variant"})
_NEW_IN_GENERATION_3 = frozenset({"archive_limit"})
```
-> `{"archive_limit", "blocked_malicious"}` (in test_phase31_audit.py selbst, Zeile 1078) plus Assertion für `blocked_malicious` analog Zeile 1096-1099. Instanzproben per `FINDLING_AUDIT36_*` überspringbar wie in Phase 34.

---

### Reconcile-Tests für M-32-02 (test)

**Analog:** `test_phase31_audit.py` Fakes Zeile 1105-1130 (`_Queue` zeichnet `requeues` auf, `fail_at`), Zeile 1265-1304 (`_Files`, `_reconcile` mit stellbarer Uhr `now: list[float]`):
```python
def _reconcile(store: Store, files: _Files, queue: _Queue, *, now: list[float] | None = None) -> Reconcile:
    clock = now if now is not None else [1_800_000_000.0]
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        ...
        clock=lambda: clock[0],
        hour_of=lambda: 2,
    )
```
`_Files` um `gone_storages()` erweitern (Antwort `set`, `None` für 404). Fälle: gelöscht -> sofort delete; verschwunden -> Stempel, Uhr +31 Tage -> delete; Rückkehr setzt Stempel zurück (Pitfall 6); leere Mountliste -> nichts (Pitfall 5); F4-Regression `reconcile_state().unfinished == 0`; Kontroll-Storage bleibt (Positivkontrolle D-36-06).

---

### `.github/workflows/integration.yml` (CI, batch)

**Analog:** Job `reconcile-and-dach` (Zeile 2365ff.). Schritte nach dem Muster Zeile 2621-2729: Zustand per `occ` herstellen, "kein Queue-Eintrag"-Gegenprobe (Zeile 2635-2647), genau ein Zyklus (Zeile 2658-2686):
```yaml
          uv run python - <<'PY' | tee "${{ github.workspace }}/reconcile.txt"
          import asyncio
          import json

          from findling.worker.reconcile import Reconcile

          result = asyncio.run(Reconcile(min_interval_hours=0).run_once())
```
Prüfschritt mit `jq -e` (Zeile 2688-2702), Drain-Schleife (Zeile 2704-2728). Nutzeranlage `OC_PASS=... ./occ user:add --password-from-env` (Zeile 2444-2445). Rückdatierung per `sqlite3` gegen `${APP_PERSISTENT_STORAGE}/.../state.db` mit `UPDATE vanished_storages SET first_missing_at = first_missing_at - 31 * 86400 WHERE storage_id = ?` (RESEARCH.md Zeile 336), vorher den Wert ausgeben (Protokoll-Muster 35-08).

---

### `.github/workflows/deploy-harp.yml` (CI, batch)

**Analog:** eigene Datei.

**`UPGRADE_FROM_TAG`** Zeile 148, Begründungsabsatz OBEN in den Block Zeile 89-147 einfügen, ältere Absätze bleiben ("kept rather than overwritten", Zeile 138):
```yaml
  # v1.4.2 since 2026-10-10 (plan 30-06, D-30-07), because it is the newest
  # release and the version in the store ...
  UPGRADE_FROM_TAG: v1.4.2
```
Erst NACH dem Versionsbump auf v1.4.3 (D-36-13). Wörtliche "1.4.2" in Schrittnamen/Meldungen mitziehen: Zeile 3812 (`Store upgrade 2b ... judged by 1.4.2`), Zeile 5310-5312 und 5343 (Kommentar/Notice im Gleich-Versionszweig).

**Zweig-Logik "Store upgrade 4"** Zeile 5335-5348 nicht anfassen; sie verlangt nach dem Bump `installed_after == new_companion`.

**Ausschlüsse (F5):** kein Analog im Workflow (Grep auf `exclusion` in workflows: 0 Treffer). Neuer Teil in "Store upgrade 2b" (Saat unter alter Version) und "Store upgrade 5" (Prüfung nach Upgrade) im dortigen Stil: `"${RUNNER_TEMP}/nc-occ.sh"` für occ, `words_find_nothing` (Zeile 4445), `::error::`-Meldungen mit `${UPGRADE_FROM_TAG}`.

**Bombe** Zeile 5615-5644, 5700, 6134-6138, 6224: siehe Befund 1 oben.

---

### `.github/workflows/release.yml` (CI, batch)

**Analog:** eigene Zeilen 477-515. Neue Dateien in BEIDE Listen: Artefakt-Upload (Zeile 484-488) und `gh release create` (Zeile 508-515), Releases sind unveränderlich:
```yaml
          gh release create "${GITHUB_REF#refs/tags/}" \
            --repo "${GITHUB_REPOSITORY}" \
            --title "${GITHUB_REF#refs/tags/}" \
            --generate-notes \
            dist/findling.tar.gz \
            dist/findling.tar.gz.sig \
            dist/findling_backend.tar.gz \
            dist/findling_backend.tar.gz.sig
```
Neuer Schritt davor nach dem Stil "Prove what the archives contain" (Zeile 463-475, `fail=0`-Schleife): `python3 scripts/release/corresponding_source.py fetch dist/source` und `git archive --format=tar.gz --prefix=findling-<version>/ "${GITHUB_REF_NAME}" > dist/findling-<version>-source.tar.gz`. Checkout Zeile 116 hat kein `fetch-depth`; für `git archive` des Tags reicht der flache Checkout des Tag-Commits (`HEAD`), sonst `fetch-depth: 0`. Neue Actions nur SHA-gepinnt (`backend/tests/test_workflow_pins.py`). Nachprüfung `gh release download ... && corresponding_source.py --verify-only` (Checkliste docs/store-listing.md:2316-2363). Kommentar "Four files" (Zeile 477) und "four artifacts" (Zeile 520) anpassen.

---

### `scripts/release/corresponding_source.py` + `THIRD-PARTY.md` (Befund F1, Release-Blocker)

**Analog:** eigene `ARCHIVES` Zeile 81-114; die zwei Einträge x265 (Zeile 90-97) und libheif (Zeile 106-113) auf 4.3 / 1.23.6 mit neuen SHA-256 und URLs aus `pillow_heif-1.8.1/libheif/build_libs.py`:
```python
    Archive(
        project="x265",
        name="x265_4.2.tar.gz",
        version="4.2",
        url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_4.2.tar.gz",
        sha256="40b1ea04...",
        licence="GPL-2.0-or-later",
    ),
```
RESEARCH nennt als neue URL `.../x265/releases/download/4.3/x265_4.3.tar.gz` (anderer Host als bisher bitbucket); Host aus `build_libs.py` übernehmen, nicht raten. THIRD-PARTY.md Tabelle Zeile 217-219 (`libheif 1.23.4`, `x265 4.2 (4.2+1-e444744)`, `.so`-Namen) im Image gegen `LICENSES_bundled.txt` prüfen.

---

### Texte: info.xml (6 Stellen), CHANGELOG, embeddings.md, store-listing.md, admin-page.md

**Analog:** die "# Entwurf v1.5.0"-Blöcke in `docs/store-listing.md` (Phasen 30-34, ab Zeile 2020) und der Beleg-Abschnitt 1.4.2/1.4.3 (Zeile 2388-2392) für die Einreichung. D-36-08 betrifft `backend/appinfo/info.xml:113,144,175` UND `php/appinfo/info.xml:67,101,135`. Gate `test_every_file_type_list_stands_in_the_draft_of_phase_31_character_for_character` hält die Dateitypen-Liste zeichengleich.

### Wortlaut-Vorabplan `36-WORTLAUT.md`

**Analog:** `.planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-WORTLAUT.md` Zeile 1-40: Kopf mit Stand/Status/Grundlage, Abschnitt "Regeln für alle Zeilen" (fr-Typografie nach `docs/l10n-french.md`, Sie-Form, Platzhalter-Regeln), "(A) Schlüsseltabelle" mit Spalten `Schlüssel (en) | de | fr | Platzhalter | Ort`, dann Bestand-wiederverwendet-Tabelle, am Ende Empfehlungen (E) zur Owner-Abnahme.

## Shared Patterns

### Kein Inhalt in Log, DB oder Antwort (T-02-56, T-03-1102)
**Source:** `extract/errors.py:89-96, 269-277`; `archive._is_overlap` Zeile 136-138; `ReconcileController.php:128-136`
**Apply to:** alle Extraktoren, Reconcile-Nachlauf, neue PHP-Route
```python
    """True for zipfile's refusal of overlapping entries. The message is compared, never logged."""
```
```php
			$this->logger->error('Findling: could not list the mounts', ['exception' => $e]);
			return new DataResponse(['error' => 'Mount list is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
```
Log nur Zähler, Codes, IDs. Log-Sonde mit Positivkontrolle (test_phase31_audit.py:1048-1070) auf neue Generatoren erweitern.

### Zwei geschlossene Listen, ein Paritätstest
**Source:** `extract/errors.py:131-167` <-> `store/repo.py:301-335` <-> `FileStateService.php:116-119, 168-171`; Paritätstests lesen die PHP-Datei (`test_extract_errors.py:55`, `test_queue_client.py:1017`, `test_admin_ui_contract.py:313`)
**Apply to:** jede neue Urteilsklasse, immer alle drei Stellen im selben Commit.

### Unbekannt ist nicht leer
**Source:** `nc/files.py:107-119` (`MountResult.unavailable`), `reconcile.py:404-410`
**Apply to:** `gone_storages` (None statt leere Menge), Nachlauf nur nach `ROUND_WALKED` mit nicht leerer Mountliste.
```python
        found = await files.mounts()
        if found.unavailable:
            self._back_off()
            return RoundResult(ROUND_UNAVAILABLE)
```

### Fremd-Aufrufer abweisen
**Source:** `ReconcileController::rejectForeignCaller` Zeile 356-368
**Apply to:** neue Route `GET /storages/gone`
```php
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}
```

### Baumhash-Ratschen
**Source:** `test_measurement_scripts.py:1008-1014` (`PHP_FILES_TODAY`, `PHP_TREE_HASH_TODAY` mit datiertem Absatz "Moved on ... by Plan ..."), `:2086-2088` (`PACKAGE_TREE_HASH_TODAY`), Prüfungen `:2247-2278` (neuer Wert muss vom alten abweichen)
**Apply to:** jeder Plan, der `php/` oder das Paket berührt (FileStateService, AdminViewService, ProfileController, ReconcileController, admin.js, info.xml); neuen Absatz anhängen, Dateizahl prüfen (neue PHP-Datei? dann `PHP_FILES_TODAY` +1).

### Async-Store-Zugriff im Worker
**Source:** `reconcile.py:392-401, 447, 494-496`
**Apply to:** alle neuen Store-Methoden im Nachlauf: `await asyncio.to_thread(store.method, ...)`, Zeit über `int(self._clock())`.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Ausschluss-Teil der Upgrade-Strecke in `deploy-harp.yml` | config (CI) | batch | keine Ausschlüsse in irgendeinem Workflow; Stil von "Store upgrade 2b/5" übernehmen, Inhalt aus RESEARCH.md "Ergänzung Ausschlüsse" |
| Quellpaket-Schritt (`git archive`) in `release.yml` | config (CI) | batch | kein git-archive-Schritt im Repo; Prüfschleife von Zeile 463-475 als Form, Technik aus RESEARCH.md "release.yml (D-36-10)" |

## Metadata

**Analog search scope:** `backend/src/findling/{extract,store,nc,worker}`, `backend/src/findling/main.py`, `backend/tests/` (conftest, test_phase31/35_audit, test_admin_ui_contract, test_measurement_scripts), `php/lib/{Controller,Service}`, `php/js/admin.js`, `php/l10n`, `php/tests/Unit`, `.github/workflows/{release,deploy-harp,integration}.yml`, `scripts/release`, `scripts/ci`, `docs/`, `.planning/phases/35-*`
**Files scanned:** ca. 30
**Pattern extraction date:** 2026-10-20
