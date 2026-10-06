# Phase 29: Härtung und Store-Einreichung 1.4.0 - Pattern Map

**Mapped:** 2026-10-06
**Files analyzed:** 34 (neu oder geändert, inkl. Tests und l10n-Gruppe)
**Analogs found:** 32 / 34

Alle Pfade relativ zu `C:\Users\Student\nextcloud-search`. Zeilennummern Stand 06.10. (vor Phase-29-Commits).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/src/findling/extract/errors.py` (3 Reasons, `detail`-Feld) | model | transform | sich selbst: `Reason`/`STATE_REASONS`/`from_exception` (89-158, 191-255) | exact |
| `backend/src/findling/store/repo.py` (STATE_REASONS, `file_errors`-Schreiben, Nachprüfungs-Auswahl, Meta-Marke) | store | CRUD | `STATE_REASONS` (261-292), `record` (812-866), `indexed_file_ids` (1084-1099), `EMBEDDING_BACKLOG_MARK` (156) | exact |
| `backend/src/findling/store/schema.sql` (neue Tabelle `file_errors`) | migration (IF NOT EXISTS) | CRUD | Tabelle `mounts`/`reconcile` (schema.sql 107-125) | exact |
| `backend/src/findling/extract/image.py` (TIFF-Shim, draft, Header-Schätzung, ehrliches Urteil) | service (Extraktor) | file-I/O / transform | sich selbst: `_implausible` (142-167), `_encode_frame` (210-244) | exact |
| `backend/src/findling/extract/cfb.py` (NEU, CFB/OLE-Leser) oder Funktion in `office.py` | utility | file-I/O | `office._too_large_to_read` (office.py 52-81) | role-match |
| `backend/src/findling/extract/dispatch.py` (`_run_ooxml_route` OLE-Sniff) | service | request-response | sich selbst 248-258 | exact |
| `backend/src/findling/worker/poller.py` (Sidecar-Skip vor `judge`, ShortRead-Zweig) | service (Worker) | event-driven | sich selbst 1426-1449 (judge + FileTooLargeError) und `_fetch_file` 1871-1893 | exact |
| `backend/src/findling/nc/client.py` (`ShortRead`, Größenprüfung in `_stream_file`) | service (Client) | streaming | `FileTooLargeError` + `_stream_file` (222-266) | exact |
| `backend/src/findling/worker/recheck.py` (NEU) oder Methode im Poller/Embedding-Track (D-29-10) | service | batch | `reconcile._hand_over` (578-601) + `embedding` Backlog-Cursor (954-972, 1150-1163) | exact |
| `backend/src/findling/nc/queue.py` (Fähigkeitssignal `verdicts` in `companion_choice`) | service (Client) | request-response | `companion_choice` (578-608) | exact |
| `backend/src/findling/profile.py` (`note_index_files`) | config/store (Modulzustand) | event-driven | `note_cap`/`note_weights` (403-428), `reset` (457-465) | exact |
| `backend/src/findling/api/diagnose.py` (`errorClass`) | controller | request-response | `DiagnoseResponse` (83-111) | exact |
| `backend/appinfo/info.xml` (`FINDLING_MAX_CELLS`, Version 1.4.0, image-tag) | config | n/a | `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` (527-541), `<version>` 163, `<image-tag>` 257 | exact |
| `php/appinfo/info.xml` (Version 1.4.0, Store-Texte) | config | n/a | `<version>` 146, `<description>` 36/64/92 | exact |
| `php/lib/Service/FileStateService.php` (REASONS, STATE_REASONS) | service | CRUD | sich selbst 102-178 | exact |
| `php/lib/Service/AdminViewService.php` (REASON_TEXT, Diagnose-Durchreichung, ggf. out_of_memory-Text) | service | request-response | `REASON_TEXT` 442-515 | exact |
| `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{js,json}` (16 Dateien) | config (i18n) | n/a | Eintrag "Excluded by a rule" (de.json:100, de.js:101) | exact |
| `php/lib/Controller/ProfileController.php` (Feld `verdicts`) | controller | request-response | `profile()` 66-88 | exact |
| `php/lib/Command/DiagnoseCommand.php` (Zeile `error class`) | controller (occ) | request-response | `$this->line(...)` 139-151 | exact |
| `php/lib/Migration/Version001400Date2026100X000000.php` (NEU) | migration | CRUD | `Version001300Date20260924000000.php` (ganz, 111 Zeilen) | exact |
| `php/tests/Unit/Version001400Date2026100X000000Test.php` (NEU) | test | n/a | `Version001300Date20260924000000Test.php` | exact |
| `backend/tests/test_extract_errors.py` | test | n/a | `test_php_pair_mapping_matches_python` (164-180), `test_php_reason_list_matches_python` (183-199) | exact |
| `backend/tests/test_ocr.py` (TIFF-Shim, draft, Header, Mehrseiten+Orientierung) | test | n/a | `_drawn`/`_declares` (608-641), `test_exif_rotated_photo_is_uprighted` (759-771) | exact |
| `backend/tests/test_poller.py` (Sidecar-Skip, ShortRead-Retry) | test | n/a | `test_a_skipped_file_travels_with_its_file_id_and_its_reason` (3136-3151) | exact |
| `backend/tests/test_gateway_client.py` (ShortRead) | test | n/a | `test_a_download_beyond_the_byte_cap_is_cut_off` (205-222) | exact |
| `backend/tests/test_profile.py` (note_index_files) | test | n/a | bestehende note_*-Tests, Pin `test_economy_is_todays_constants_value_for_value` | role-match |
| `backend/tests/test_info_xml_defaults.py` | test | n/a | `EXPECTED` (37-54), Anti-Vakuität `>= 16` (97) | exact |
| `backend/tests/test_ops_scripts.py` (Key-Pair-ID im Sweep) | test | n/a | `test_the_aws_destroy_takes_the_key_pair_with_it_and_reads_it_back` (601-629), `..._keeps_the_security_group_...` (1161-1177) | exact |
| `backend/tests/test_measurement_scripts.py` (Baumhash-Pins, Slotkosten-Ausgaben) | test | n/a | Pins 775-776, 1601-1602 | exact |
| `backend/pyproject.toml` (filterwarnings Starlette) | config | n/a | `filterwarnings` (133) inkl. Begründungskommentar 130-132 | exact |
| `scripts/ops/aws_box.sh` (`shared=` um Key-Pair-ID) | utility (ops) | batch | `cmd_destroy` 1270-1278 und Sweep 1397-1409 | exact |
| `docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py` (`--dateien`) | utility (Messskript) | transform | `calculation()` 256-280, argparse 325-336 | exact |
| `.github/workflows/deploy-harp.yml` (UPGRADE_FROM_TAG, neue Saat 2b, Zusicherungen 3/3b/5) | config (CI) | batch | `UPGRADE_FROM_TAG` 113, "Store upgrade 2b" 3337-3427 | exact |
| `docs/store-listing.md` (Textentwurf 1.4.0) | doc | n/a | 1.3.0-Abschnitt Teil 1 bis 7 (Zeilen 865-1277) | exact |

## Pattern Assignments

### `backend/src/findling/extract/errors.py` (model, transform)

**Analog:** sich selbst. Neue Reasons `SYSTEM_FILE`, `LEGACY_FORMAT`, `UNSUPPORTED_VARIANT` (Research-Empfehlung: alle drei unter `skipped`).

**Reason-Enum, Kommentarstil mit Inline-Begründung** (Zeilen 101-111):
```python
    # skipped, the deliberate decisions
    TOO_LARGE = "too_large"
    ...
    IMAGE_NOT_OCRABLE = "image_not_ocrable"  # a picture too small or too flat to carry text
    EXCLUDED = "excluded"  # an admin rule keeps this file out of the index, the file itself is untouched
    UNREADABLE = "unreadable"  # written by the PHP half: no user asked may read it, a Team Folder ACL (#14)
```

**Closed list** (128-143): neuen Code in `State.SKIPPED`-frozenset ergänzen, gleiche Zeile mit Kommentar.

**Dataclass, an die `detail` angehängt wird** (191-204): frozen, slots, Felder mit Default am Ende. `detail: str | None = None` NACH `text_chars` (Pickle-Weg Kind zu Eltern).
```python
@dataclass(frozen=True, slots=True)
class ExtractionOutcome:
    state: State
    reason: Reason | None = None
    text: str = field(default="", repr=False)
    text_chars: int = 0
```

**from_exception, wo die Klasse schon vorliegt** (239-255): Detail = gleiche Formatierung wie der Schlüssel der Tabelle, nie die Message (T-02-56):
```python
        for klass in type(error).__mro__:
            reason = _EXCEPTION_REASONS.get(f"{klass.__module__}.{klass.__qualname__}")
            if reason is not None:
                return cls.failed(reason)
        return cls.failed(Reason.CORRUPT)
```
`failed()` (233-236) braucht einen optionalen `detail`-Parameter; Detail ist `f"{type(error).__module__}.{type(error).__qualname__}"` (geworfene Klasse, nicht die MRO-Treffer-Klasse).

**Modul-Regel** (17-23): nur stdlib-Imports in errors.py; der neue Code bleibt so.

---

### `backend/src/findling/store/repo.py` (store, CRUD)

**Analog:** sich selbst.

**STATE_REASONS-Duplikat** (261-292) wortgleich nachziehen, Kommentar 255-260 sagt: "Adding a reason is a deliberate act: it shows up in the admin UI and needs a German label there."

**record(): Validierung vor Transaktion, dann ein Transaktionsblock** (843-866):
```python
        allowed = STATE_REASONS.get(state)
        if allowed is None:
            raise ValueError(f"unknown state {state!r}, expected one of {sorted(STATE_REASONS)}")
        if reason not in allowed:
            raise ValueError(f"reason {reason!r} does not belong to state {state!r}")

        with self._transaction():
            self._conn.execute(_RECORD_SQL, (...))
```
`file_errors` schreiben/löschen gehört in denselben `with self._transaction():`-Block (keyword-only Parameter `error_class: str | None = None` wie `content_hash`/`ocr_used`).

**Cursor-Auswahl für die Nachprüfung** (1084-1099), Docstring-Begründung "Ascending and above a cursor rather than an offset" übernehmen:
```python
    def indexed_file_ids(self, *, after: int = 0, limit: int) -> list[int]:
        rows = self._conn.execute(_INDEXED_FILE_IDS_SQL, (after, limit))
        return [int(row[0]) for row in rows]
```
Neue Methode z. B. `recheck_candidates(*, after, limit)`: SQL-Konstante auf Modulebene (`_..._SQL: Final = """..."""`), `deleted_at IS NULL AND state = 'failed' AND reason IN ('corrupt','out_of_memory')`; Sidecar-Basisnamen in Python filtern (Pitfall 6, kein `LIKE '%/._%'`).

**Meta-Marke als Modulkonstante mit Begründung** (147-156):
```python
# Where the redelivery of the vector stock has got to, or an empty value when no
# redelivery is running.
# ... a container restarts in the middle of the work, and a cursor that lived only
# in a process would leave the rest of the stock unwritten with nothing anywhere saying so.
EMBEDDING_BACKLOG_MARK: Final = "embedding_backlog_at"
```
Neu analog: `RECHECK_MARK: Final = "recheck_1_4_0"` (Wert = Cursor oder "done"); Lesen/Schreiben über `read_meta()` (707) / `write_meta(key, value)` (711).

**Schema-Mark-Regel** (49-63): `SCHEMA_VERSION` NICHT anheben, wenn nur eine IF-NOT-EXISTS-Tabelle dazukommt ("an existing database absorbs the change on the next open, and no reindex ... is needed").

---

### `backend/src/findling/store/schema.sql` (migration, CRUD)

**Analog:** `mounts` (119-125), mit Kommentarblock davor, der sagt, was verloren geht, wenn die Tabelle fehlt:
```sql
-- A mirror for the display, nothing else. ...
CREATE TABLE IF NOT EXISTS mounts (
    storage_id     INTEGER PRIMARY KEY,
    root_id        INTEGER NOT NULL,
    ...
    updated_at     INTEGER NOT NULL
);
```
Neu: `CREATE TABLE IF NOT EXISTS file_errors (file_id INTEGER PRIMARY KEY, error_class TEXT NOT NULL, recorded_at INTEGER NOT NULL);` mit Kommentar "Diagnosedatum, kein Verdikt; nur module.qualname, nie Message (T-02-56)".

---

### `backend/src/findling/extract/image.py` (service, file-I/O)

**Analog:** sich selbst.

**Imports** (37-49): `from PIL import Image, ImageOps` erweitern um `TiffImagePlugin`; `resource` nur POSIX (Windows-Tests!) wie in `extract/sandbox.py:104-117` (dort nachsehen, wie der Import geschützt ist).

**Modulkonstanten mit Begründungskommentar** (51-91), z. B.:
```python
# What the engine is given at most on the long edge. ...
_MAX_EDGE_PIXELS: Final = 3500
```
Shim-Registrierung als Modul-Seiteneffekt direkt neben `Image.MAX_IMAGE_PIXELS = _MAX_PIXELS` (63), mit `setdefault` (Research Code Example "TIFF-Shim", Ziel `("LA","LA")`, Pitfall 2/3).

**Header-Prüfung vor Dekodierung** (142-167): neue Header-Schätzung als weitere Frage in `_implausible` bzw. direkt danach, gleiche Rückgabeform `ExtractionOutcome | None`:
```python
    if width * height > _MAX_PIXELS:
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    if longest < _MIN_LONG_EDGE_PIXELS:
        return ExtractionOutcome.skipped(Reason.IMAGE_NOT_OCRABLE)
    ...
    return None
```
Urteil bei Überschreitung: `ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)` (Research Pattern 2).

**Open-Fehlerpfad, an dem "unknown pixel mode" unterschieden wird** (106-116):
```python
    try:
        opened = Image.open(path)
    except Image.DecompressionBombError:
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    except OSError:
        # UnidentifiedImageError is a subclass of this ...
        return ExtractionOutcome.failed(Reason.CORRUPT)
```
Im `OSError`-Zweig: TIFF-Magic prüfen und `_is_unsupported_tiff_variant` (Research Code Example) aufrufen, dann `skipped(UNSUPPORTED_VARIANT)`; sonst CORRUPT mit `detail`. Gleiches für die zweite CORRUPT-Stelle (136-139). Komprimierte SF0-Dateien: Prüfung vor `_read_frames` (`tag_v2.get(339)`, `info["compression"] != "raw"`).

**Drehung/Skalierung, die ersetzt wird** (223-244): heute `ImageOps.exif_transpose(picture)` + `thumbnail`. Neu: `picture.draft("L", seitenverhältnistreues_Ziel)` nur bei `n_frames == 1` vor dem ersten Laden, dann `exif_transpose(..., in_place=True)` (Research Code Example "JPEG verkleinert dekodieren", Pitfall 10). `finally`-Struktur zum Schließen der Arbeitskopie (240-243) beibehalten.

---

### `backend/src/findling/extract/cfb.py` (NEU, utility, file-I/O) bzw. OLE-Sniff

**Analog:** `office._too_large_to_read` (office.py 52-81): Vorab-Prüfung vor jedem Loader, gibt `ExtractionOutcome | None`, fängt Lesefehler und fällt zurück statt zu werfen:
```python
def _too_large_to_read(path: str, *, every_part_is_read: bool) -> ExtractionOutcome | None:
    try:
        with ZipFile(path) as archive:
            declared = [info.file_size for info in archive.infolist()]
    except (BadZipFile, OSError):
        return None

    if any(size > EXTRACT_ARCHIVE_MEMBER_MAX_BYTES for size in declared):
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    ...
    return None
```
Neu `_ole_verdict(path) -> ExtractionOutcome | None`: Kopf `d0cf11e0a1b11ae1`, Verzeichnis per `struct` mit Sektor-Deckel und Besucht-Menge; `EncryptionInfo`/`EncryptedPackage` -> `skipped(ENCRYPTED)` (Präzedenz pdf.py 132-135), `Workbook`/`Book`/`WordDocument`/`PowerPoint Document` -> `skipped(LEGACY_FORMAT)`; jeder Lesefehler -> `None` (Rückfall auf ZIP-Loader, dessen `BadZipFile` dann `from_exception` sieht). Kein neues Paket (kein olefile). Modul-Docstring nach office.py-Muster (1-28), inkl. "Known gap"-Absatz für DIFAT > 109.

### `backend/src/findling/extract/dispatch.py` (service, request-response)

**Einhängepunkt** (248-258): Sniff am Anfang von `_run_ooxml_route`, vor `from findling.extract import office`-Aufruf der Extraktoren:
```python
def _run_ooxml_route(route: Route, path: str) -> ExtractionOutcome:
    """The three ZIP packages of the Office world."""
    from findling.extract import office

    match route:
        case Route.DOCX:
            return office.extract_docx(path)
```
Lazy-Import-Regel (199-213) gilt auch für `cfb`. `judge()` (122-137) bleibt unverändert; Sidecar-Skip gehört NICHT hierher, sondern in den Poller (Pfad ist hier unbekannt).

---

### `backend/src/findling/worker/poller.py` (service, event-driven)

**Analog:** sich selbst.

**Verdikt vor dem ersten Byte** (1426-1432), direkt davor den Sidecar-Skip mit `PurePosixPath(job.path).name` (Fallback `job.title`) einfügen:
```python
        route = judge(job.mime, job.size)
        if isinstance(route, ExtractionOutcome):
            # Decided before the first byte. Reading fifty megabytes to learn what
            # the mimetype already said is the most expensive possible way of
            # finding out that a film has no text in it.
            self._collect(job, route, done, failed, verdicts)
            return 0
```

**Ausnahme je Datei, die den Pass nicht stoppt** (1434-1442), Vorlage für `ShortRead`:
```python
        try:
            read = await self._fetch_file(job)
        except FileTooLargeError:
            # ... A verdict, not an error: the row leaves the queue ...
            self._collect(job, ExtractionOutcome.skipped(Reason.TOO_LARGE), done, failed, verdicts)
            return 0
```
Unterschied: `ShortRead` -> sofortiger zweiter Versuch; bleibt kurz -> Zeile OHNE Verdikt freigeben (kein `_collect`), Muster "row handed back unjudged" (Test `test_a_row_handed_back_unjudged_does_not_count_as_a_delivery`, test_poller.py 2323).

**`_fetch_file` Durchreichen statt `_GatewayDown`** (1879-1888):
```python
        try:
            written, sink = await self._stream_into(scratch, job)
        except FileTooLargeError:
            _discard(scratch)
            raise
        except Exception as error:
            _discard(scratch)
            LOGGER.warning("content gateway did not deliver, %s", type(error).__name__)
            raise _GatewayDown from error
```
`except ShortRead:` als zweiter Durchreich-Zweig vor `except Exception`.

**Fähigkeitsabhängiges Reason-Mapping (Pitfall 1):** Rückfall `system_file`/`unsupported_variant` -> `corrupt`, `legacy_format` -> `mime_not_allowed`, solange `companion_choice()` kein `verdicts`-Signal liefert. Sitz: dort, wo Skip/Failure-Listen für `acknowledge` gebaut werden (`_collect`/Quittungsaufbau im Poller).

---

### `backend/src/findling/nc/client.py` (service, streaming)

**Analog:** `FileTooLargeError` (222-230) und Zählschleife (257-265):
```python
class FileTooLargeError(Exception):
    """The gateway delivered more bytes than any file this app would queue.
    ... The message carries the file id and nothing else: no name, no path.
    """
...
        async for chunk in response.aiter_bytes(CHUNK_SIZE):
            written += len(chunk)
            if written > cap:
                raise FileTooLargeError(f"file id {file_id} exceeded the byte cap while downloading")
            await asyncio.to_thread(fp.write, chunk)
    return written
```
Neu: `class ShortRead(Exception)` gleicher Docstring-Stil; `_stream_file` bekommt `expected: int` (keyword-only), nach der Schleife `if expected > 0 and written < expected: raise ShortRead(f"file id {file_id} ...")`. `fetch_file_stream` (269ff) reicht den Parameter durch. `expected <= 0` = keine Prüfung (requeueAs legt `size = 0` an, Annahme A2; `nc/queue.py:353-382` zeigt `size=0 if size is None`).

---

### Nachprüfungslauf D-29-10 (`worker/recheck.py` NEU oder Methode am bestehenden Track; service, batch)

**Analog 1, Bänder unter 256:** `reconcile._hand_over` (reconcile.py 578-601) und Konstante `REQUEUE_BAND: Final = 200` (148) wiederverwenden (importieren, nicht kopieren):
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

**Analog 2, Cursor erst nach erfolgreicher Übergabe schreiben** (embedding.py 954-972, Bug-Audit M1):
```python
        band = await asyncio.to_thread(self._vector_mark_step, target)
        if not band:
            return
        # **The cursor moves here and not one step earlier ...** Judged on ``ok``
        # and never on ``count`` ...
        if (await hand_over(queue, band, kind=KIND_EMBED)).ok:
            await asyncio.to_thread(self._store_or_die().write_meta, EMBEDDING_BACKLOG_MARK, str(band[-1]))
```

**Analog 3, Cursor-Lesen robust gegen Handedits** (embedding.py 1150-1163):
```python
        if not cursor:
            return []
        after = int(cursor) if cursor.isdigit() else 0
        band = store.indexed_file_ids(after=after, limit=VECTOR_BACKLOG_BAND)
        if not band:
            store.write_meta(EMBEDDING_BACKLOG_MARK, "")
        return band
```
Kein `index_version`-Anheben (Anti-Pattern). Start erst bei Companion-Signal `verdicts`.

**Analog 4, PHP-seitige Einmal-Requeue-Semantik als Begründungsvorlage:** Klassenkommentar `php/lib/Migration/Version001301Date20260929000000.php` (15-66: "A second run is harmless", "Only unreadable", "Nothing is asked of the container here"). Nur Begründungsstil, Mechanik bleibt containerseitig.

---

### `backend/src/findling/nc/queue.py` (service, request-response)

**Analog:** `companion_choice` (578-608), geschlossene Wertemenge, fehlendes Feld = None:
```python
        payload = _mapping(answer) or {}
        profile = payload.get("profile")
        precision = payload.get("precision")
        confirmed = payload.get("confirmed")
        return CompanionChoice(
            profile=profile if isinstance(profile, str) and profile in PROFILE_NAMES else None,
            ...
        )
```
Neu: Feld `verdicts` (int, nur exakt erwarteter Wert gilt), `CompanionChoice` um `verdicts: int | None` erweitern; Exception-Zweig (591-597) setzt es auf None. **D-29-13:** requeue-Warnung (610-649) ist bereits vorhanden ("could not hand %d files to another track, %s status=%s after %.1f s"), nur verifizieren.

---

### `backend/src/findling/profile.py` (Modulzustand, event-driven)

**Analog:** `note_cap`/`note_weights` (403-428), `reset` (457-465), Modulzustand (390-394):
```python
def note_weights(value: str | None) -> None:
    """Publish the precision in force ... The snapshot is only recomputed on a change."""
    global _WEIGHTS, _SNAPSHOT
    if value not in _WEIGHT_NAMES or value == _WEIGHTS:
        return
    _WEIGHTS = value
    _SNAPSHOT = _compute(_HARDWARE, _CHOSEN, _WEIGHTS, _CAP)
```
Neu: `_INDEX_FILES: int = 0`, `note_index_files(count)` rundet auf ganze Tausend ab, nur bei Änderung neu rechnen; `_compute(...)` (360) und `_profile_values` (Aufruf `ocr_slots(profile, hardware, weights=weights)` bei 260) bekommen `index_files` durchgereicht; `ocr_slots(..., index_files=...)` (220-241) und `main_process_bytes` (183-190) existieren schon. `reset()` setzt `_INDEX_FILES = 0`. Docstring-Satz "No caller hands a file count in yet" (43-48) anpassen. Aufrufer im Poller mit `store.indexed_alive()` (repo.py 1066).

### `docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py` (utility, transform)

**Analog:** `calculation()` (256-280) und argparse-Unterbefehl `rechnung` (333-336):
```python
    return config.MAIN_PROCESS_BASELINE_BYTES + slots * config.OCR_SLOT_COST_BYTES + loads + fp32
...
    rechnung.add_argument("--profil")
    rechnung.add_argument("--slots")
    rechnung.add_argument("--praezision")
```
Neu `rechnung.add_argument("--dateien", default="0")`, additiver Term `dateien * config.MAIN_PROCESS_PER_FILE_BYTES` (config.py 910). Default 0 hält bestehende gepinnte Ausgaben in `test_measurement_scripts.py` bytegleich.

---

### `backend/src/findling/api/diagnose.py` (controller, request-response)

**Analog:** `DiagnoseResponse` (83-111), jedes Feld mit Default:
```python
    embedded: bool = False
    chunks: int = 0
    origin: str | None = None
    note: str = ""
```
Neu `errorClass: str = ""` (nicht None, da nur `origin` absent sein darf, Kommentar 105-108).

### `php/lib/Command/DiagnoseCommand.php`

**Analog** (139-143):
```php
		$output->writeln('Verdict');
		$this->line($output, 'state', $answer['state']);
		$this->line($output, 'reason code', $answer['reason']);
		$this->line($output, 'label', $answer['label']);
		$this->line($output, 'remedy', $answer['remedy']);
```
Neu `$this->line($output, 'error class', $answer['errorClass']);` (leer -> `-` über `line()` 182-183). Feld in AdminViewService-Diagnoseantwort durchreichen.

---

### `php/lib/Service/FileStateService.php` (service, CRUD)

**Analog:** `REASONS` (102-127) und `STATE_REASONS` (151-178), Kommentar `// skipped` / `// failed` gruppiert:
```php
	public const REASONS = [
		// indexed
		'truncated',
		// skipped
		'too_large',
		...
		'unreadable',
		// failed
		...
	];
	private const STATE_REASONS = [
		'indexed' => [null, 'truncated'],
		'skipped' => [ ..., 'excluded', 'unreadable', ],
```
Beide Listen ergänzen; der Paritätstest (`test_extract_errors.py` 140-199) liest sie per Regex `const STATE_REASONS = \[(.*?)\];` aus, also Formatierung beibehalten (einfache Anführungszeichen, `[a-z_]+`).

**K6-Falle:** `QueueController::failureList`/`skipList` (QueueController.php 470-535) lehnen bei unbekanntem Code die GANZE Liste ab (`return null` -> 400). Nicht ändern, sondern containerseitig über das Fähigkeitssignal absichern.

### `php/lib/Controller/ProfileController.php`

**Analog** (73-77):
```php
			return new DataResponse([
				'profile' => $this->settingsService->profile(),
				'precision' => $this->settingsService->modelPrecision(),
				'confirmed' => $this->settingsService->profileConfirmed(),
			]);
```
Neu `'verdicts' => 2` (Konstante mit Docblock, warum: K6, Companion kennt die drei Reasons). Test: `php/tests/Unit/ProfileControllerTest.php`; Wire-Gegenstück `backend/tests/test_profile_wire.py`.

### `php/lib/Service/AdminViewService.php` (service)

**Analog:** `REASON_TEXT` (442-515), Paar Label/Abhilfe, Abhilfe "None. ..." für nicht behebbare Fälle:
```php
		'encrypted' => [
			'Password protected',
			'None. Without the password the content cannot be read.',
		],
		'image_not_ocrable' => [
			'Image without recognisable writing',
			'None.',
		],
```
Neu z. B. `'system_file' => ['System or helper file', 'None. macOS metadata files (._) and Office lock files (~$) carry no document content.']`, analog `legacy_format`, `unsupported_variant`. Texte sind Teil des Owner-Textentwurfs (Pitfall 7: `out_of_memory`-Abhilfe 507-510 mit überarbeiten). Fallback `reasonText()` (1613-1622) zeigt sonst "Unknown reason (code)".

### `php/l10n/*.js|*.json` (16 Dateien)

**Analog:** de.json:100 / de.js:101:
```
        "Excluded by a rule": "Durch Regel ausgeschlossen",
```
Jeder neue Label- und Abhilfe-String als Schlüssel in allen 8 Sprachen x 2 Formate; Kontrakttest `backend/tests/test_admin_ui_contract.py`.

---

### `php/lib/Migration/Version001400Date2026100X000000.php` (migration)

**Analog:** `Version001300Date20260924000000.php` vollständig (Zeilen 1-111). Kern (85-110):
```php
class Version001300Date20260924000000 extends SimpleMigrationStep {
	public function __construct(
		private IAppConfig $appConfig,
	) {
	}

	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$recorded = $this->appConfig->getValueString(Application::APP_ID, ExAppService::KEY_BACKEND_VERSION, '');
		if ($recorded === '') {
			$output->info('no recorded backend version to drop');

			return;
		}

		$this->appConfig->deleteKey(Application::APP_ID, ExAppService::KEY_BACKEND_VERSION);
		$output->info(sprintf('dropped the recorded backend version %s, it predates this update', $recorded));
	}
}
```
Klassenkommentar-Pflichtsätze übernehmen: "Every minor step needs a migration of this shape" (37-45), "Nothing is asked of the container here" (55-61), "The class name and the file name have to be identical to the character" (80-83). Keine Nachprüfungslogik hier (gehört in den Container).

### `php/tests/Unit/Version001400Date2026100X000000Test.php`

**Analog:** `Version001300Date20260924000000Test.php` (Zeilen 1-80+): Schlüssel per Reflection aus `ExAppService::KEY_BACKEND_VERSION`, `schemaClosure()` mit `self::fail`, Fälle "recorded dropped", "never recorded left alone", `setValueString` nie, zweiter Lauf no-op. PHPUnit lokal nicht verfügbar: Beleg über CI `php.yml`.

---

### `backend/appinfo/info.xml` (config)

**Analog:** Variable `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` (527-541), XML-Kommentar mit Messbeleg + Deklarationsgrund davor:
```xml
			<!--
				The address space of the extraction child, ...
				Declared so that an admin can raise it: AppAPI hands the
				container only the variables listed here, an undeclared value is
				dropped without a word.
			-->
			<variable>
				<name>FINDLING_EXTRACT_ADDRESS_SPACE_BYTES</name>
				<display-name>Memory a single document may take while it is read</display-name>
				<description>A whole number of bytes. ...</description>
				<default>536870912</default>
			</variable>
```
Neu `FINDLING_MAX_CELLS` mit `<default>200000</default>` exakt = `config.MAX_CELLS` (config.py 245; gelesen bei 1562 über `_int_from_environment`). Satz "Only one document is read at a time ..." ist ab 1.4.0 falsch (Pitfall 7), im Textentwurf neu fassen. Versionen: `<version>` 163, `<image-tag>` 257 auf 1.4.0; `php/appinfo/info.xml` `<version>` 146. Gate `backend/tests/test_lockstep_versions.py` (159).

### `backend/tests/test_info_xml_defaults.py`

**Analog** (37-54, 92-98):
```python
EXPECTED: dict[str, str] = {
    ...
    "FINDLING_EXTRACT_ADDRESS_SPACE_BYTES": str(config.EXTRACT_ADDRESS_SPACE_BYTES),
}
...
    assert len(declared) >= 16
```
Ergänzen `"FINDLING_MAX_CELLS": str(config.MAX_CELLS),`; Anti-Vakuitätsschwelle und Kommentar ("sixteen variables") auf 17 heben.

---

### `backend/pyproject.toml` (config)

**Analog** (130-133), Eintrag immer mit Begründungskommentar:
```toml
# A synchronous enabled_handler still works with nc-py-api 0.30.x but only emits a
# DeprecationWarning, and it breaks hard in 0.31.0. Turning that warning into an
# error is the only way the mistake surfaces before the release that removes it.
filterwarnings = ["error::DeprecationWarning"]
```
Neu als zweites Listenelement: `"ignore:Using .httpx. with .starlette.testclient. is deprecated:starlette.exceptions.StarletteDeprecationWarning"` plus Kommentar (testseitig, `src` nutzt keinen TestClient, httpx2 = [SUS], keine neue Abhängigkeit). Owner-Bestätigung laut Research Open Question 2.

---

### `scripts/ops/aws_box.sh` + `backend/tests/test_ops_scripts.py`

**Analog Sweep** (1397-1409): Vergleich gegen `tag['ResourceId']`, `shared` aus Shell interpoliert:
```bash
    remaining=$(ec2 describe-tags --filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE" | json "
...
left = [
    tag for tag in tags
    if tag['ResourceId'] != '$instance_id'
    and tag['ResourceId'] not in keepers
    and tag['ResourceId'] not in shared
]
```
**Einhängepunkt** (1277): `shared="$others $other_volumes $group_id"` um Key-Pair-ID ergänzen, ermittelt über `ec2 describe-key-pairs --key-names "$SSH_KEY_NAME"` + `json`-Helfer (Muster 1272-1276: Python-Einzeiler über `json.load(sys.stdin)['KeyPairs'][0]['KeyPairId']`).

**Test-Analog** (1161-1177): `an_aws_box_run(tmp_path, ["destroy"], state="terminated", sharing=[AWS_OTHER_INSTANCE], umgebung=_a_backup(tmp_path))`, Asserts auf `answer.stdout`/`calls`; statische Textprüfung wie 601-629 (`body = text.split("cmd_destroy() {", 1)[1]`). Fake-describe-key-pairs-Antwort im Test-Harness ergänzen (Annahme A4).

---

### `.github/workflows/deploy-harp.yml` (CI, batch)

**Analog 1, Tag-Zeile mit Historienkommentar** (105-113): Kommentar fortschreiben ("the release of phase 23 published v1.3.2 ..."), Wert `UPGRADE_FROM_TAG: v1.3.2`.

**Analog 2, Saat-Schritt "Store upgrade 2b"** (3337-3427), Bausteine zum Kopieren:
- Gate-Zeile: `if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04' && env.RELEASE_TAG == ''`
- `q()`-Helfer: `sqlite3 -cmd '.timeout 30000' "${FINDLING_DB}" "$1"`
- `seed_hits()` fail-closed (HTTP-Code + jq-Länge, `case "${code}:${count}"`)
- Vorher-Nullprobe des Saatworts, `docker pause` + `trap ... EXIT`, `files:scan --path=...`, file_id-Ermittlung aus `oc_filecache`, Fail-closed-Zusicherungen mit `::error::`, Export nach `$GITHUB_ENV` (`UPGRADE_SEED_FILE_ID=...`).

Neue Saat: `._seed.docx` und Grau+Extra-TIFF im 1.3.2-Stand, die 1.3.2 nachweislich als `failed(corrupt)` verbucht (hier NICHT per SQL säen, sondern vom alten Container urteilen lassen und Verdikt prüfen); Zusicherung in "Store upgrade 5" (4293ff): Sidecar `skipped(system_file)`, TIFF `indexed` + Suchworttreffer, `index_version` unverändert, Vektor-Marke/`embedded` unverändert, Profil `economy`. Gone-Zusicherungen 3/3b (4265-4292, 4424) ersetzen. Texte "1.3.0 against the 1.2.0" (2902, 4032, 4059, 4092, 4240, 4271, 4567) umstellen. Run-Block "Store upgrade 3" (~20,7k Zeichen) nicht vergrößern.

### `.github/workflows/store-submit.yml`

Keine Codeänderung erwartet; Aufruf `gh workflow run store-submit.yml -f tag=v1.4.0` (`workflow_dispatch` Input `tag`, Zeile 28-30), erwartet zweimal "HTTP 201".

### `docs/store-listing.md`

**Analog:** Abschnitt 1.3.0 Teil 1 bis 7 (Zeilen 865-1277). Gates `backend/tests/test_store_metadata.py`: `RESIDENT_FIGURE = "730.2"` (356) bleibt, `scan_one_measured_figure` (866) = genau eine Zahl je Beschreibung, keine Dashes/Emojis. D-24-04-Satz wörtlich.

---

## Shared Patterns

### Geschlossene Reason-Liste, fünf Kopien
**Quellen:** `extract/errors.py` 89-158, `store/repo.py` 261-292, `php/lib/Service/FileStateService.php` 102-178, `AdminViewService.php` REASON_TEXT 442ff, 16 l10n-Dateien.
**Apply to:** jeder Plan, der `system_file`/`legacy_format`/`unsupported_variant` einführt. In EINEM Commit alle Kopien; Paritätstests `test_extract_errors.py` (164-199) und `test_admin_ui_contract.py` laufen grün nur so. Plus Rückfall-Mapping bei fehlendem Companion-Signal (Pitfall 1).

### Keine Pfade/Messages in Logs und Details (T-02-56, T-24-19)
**Quelle:** `nc/queue.py` 620-640, `worker/poller.py` 1887:
```python
            LOGGER.warning("content gateway did not deliver, %s", type(error).__name__)
```
**Apply to:** `detail`/`error_class`, ShortRead-Meldung (nur file id), Nachprüfungs-Logzeilen (nur Zahlen), Migration-Output (nur Zahlen).

### Vorab-Urteil statt Ausnahme (`ExtractionOutcome | None`)
**Quellen:** `image._implausible` (142-167), `office._too_large_to_read` (52-81), `dispatch.judge` (122-137).
**Apply to:** OLE-Sniff, Header-Schätzung, SF0-komprimiert-Urteil, Sidecar-Skip.

### Bänder + Cursor nach Erfolg
**Quellen:** `reconcile.REQUEUE_BAND` (148) + `_hand_over` (578-601); `embedding` 954-972 und 1150-1163.
**Apply to:** Nachprüfungslauf D-29-10.

### note_*-Setter mit Neuberechnung nur bei Änderung
**Quelle:** `profile.py` 403-447, `reset` 457-465.
**Apply to:** `note_index_files` (D-29-12).

### Deklarierter Default = config-Konstante
**Quelle:** `backend/appinfo/info.xml` 527-541 + `test_info_xml_defaults.py` EXPECTED 37-54.
**Apply to:** `FINDLING_MAX_CELLS`.

### Baumhash-Pins nachziehen
**Quelle:** `backend/tests/test_measurement_scripts.py` `PHP_FILES_TODAY = 88`/`PHP_TREE_HASH_TODAY` (775-776), `PACKAGE_FILES_TODAY = 71`/`PACKAGE_TREE_HASH_TODAY` (1601-1602).
**Apply to:** jeder Plan mit Änderungen unter `backend/src/findling` oder `php/` (neue Dateien cfb.py, recheck.py, Migration erhöhen die Zahl). Bei parallelen Wellen Pin-Abschluss-Task pro Welle.

### Kommentarstil
Englische Kommentare/Docstrings, die das "Warum" mit Befund-ID (z. B. "security audit M5", "D-26-16", "#18") begründen; kein Em-/En-Dash; Umlaute nur in deutscher Prosa (Docs), nie im Code.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| CFB-Verzeichnisleser (Kern von `extract/cfb.py`) | utility | file-I/O | Kein Binärformat-Parser mit `struct` im Extraktionspfad; Rahmen (Vorab-Urteil, Rückfall) von `office._too_large_to_read`, Offsets aus Research Pattern 3 gegen [MS-CFB] 2.2 prüfen (A1) |
| TIFF-`OPEN_INFO`-Shim | utility | transform | Erste Laufzeitänderung eines Pillow-Moduldicts; Vorlage nur `Image.MAX_IMAGE_PIXELS = _MAX_PIXELS` (image.py 57-63) als Modul-Seiteneffekt, Code aus Research Code Example |

## Metadata

**Analog search scope:** `backend/src/findling/{extract,worker,nc,store,api}`, `backend/src/findling/{profile,config}.py`, `backend/tests`, `backend/appinfo`, `backend/pyproject.toml`, `php/lib/{Controller,Service,Migration,Command}`, `php/tests/Unit`, `php/l10n`, `.github/workflows/{deploy-harp,store-submit}.yml`, `scripts/ops/aws_box.sh`, `docs/measurements/2026-10-abnahme-anfahrt/skripte/12-slotkosten.py`
**Files scanned:** ca. 40
**Pattern extraction date:** 2026-10-06
