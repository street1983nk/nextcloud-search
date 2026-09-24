# Phase 18: Schema, Marken und Umbauweg - Pattern Map

**Kartiert:** 2026-09-24
**Dateien betrachtet:** 26 (2 neu, 24 geaendert)
**Analoga gefunden:** 24 / 26

Quelle der Dateiliste: `18-RESEARCH.md` Abschnitt "Empfohlene Dateistruktur" (Zeilen 168-185),
"Architectural Responsibility Map" (Zeilen 50-62), "Common Pitfalls" 5 bis 8 und
"Die umgedrehte Beweisstrecke". Ein CONTEXT.md gibt es nicht, discuss-phase wurde uebersprungen.

Alle Zeilenangaben sind am Baum vom 2026-09-24 gelesen. Ausnahmslos jede Codestelle unten ist
vorhandener Code dieses Repos, kein Entwurf. Entwuerfe stehen ausschliesslich in RESEARCH.md und
sind hier nie als Analog ausgegeben.

---

## File Classification

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Guete |
|---|---|---|---|---|
| `backend/src/findling/index/rebuild.py` | service (Vorgang mit Lebensdauer) | batch / transform | `backend/src/findling/index/writer.py` + `backend/src/findling/store/repo.py:index_bytes` | Teilstueck (Rolle passt, Verzeichnistausch ohne Vorbild) |
| `backend/src/findling/index/schema.py` | model / Definitionstabelle | - (einmal geschrieben, dauernd gelesen) | sich selbst, Zeilen 84-116 | exakt |
| `backend/src/findling/index/open.py` | factory / resource | request-response (Oeffnen) | sich selbst, Zeilen 84-102 und 123-141 | exakt |
| `backend/src/findling/index/writer.py` | service | write-path | sich selbst, Zeilen 255-273 | exakt |
| `backend/src/findling/config.py` | config | env-to-value | sich selbst, `_languages` 1068-1081 und `_ocr_languages` 1093-1131 | exakt |
| `backend/src/findling/store/repo.py` | store / model | CRUD auf `meta` | sich selbst, `_index_format_matches` 1327-1342 | exakt |
| `backend/src/findling/api/resources.py` | provider / Prozesscache | cache-invalidation | sich selbst, `read_side` 273-340 | exakt |
| `backend/src/findling/api/status.py` | controller | request-response | sich selbst, `StatusResponse` 113-187 und `_of` 312-357 | exakt |
| `backend/src/findling/api/diagnose.py` | controller | request-response | `api/status.py` plus sich selbst 316-352 | exakt |
| `backend/src/findling/main.py` | provider / Lifespan | event-driven (langlaufende Aufgabe) | sich selbst, `_release_when_idle` 254-325 | exakt |
| `backend/src/findling/tools/index_status.py` | CLI-Werkzeug / Bericht | batch | sich selbst, `_VERSION_KEYS` 60-66 und 145-150 | exakt |
| `backend/src/findling/worker/poller.py` | worker (Aufrufstelle) | event-driven | sich selbst, `_open_state` 305-326 | exakt |
| `backend/src/findling/tools/one_load.py` | CLI-Werkzeug (Aufrufstelle) | batch | `worker/poller.py:322` | exakt |
| `php/lib/Migration/Version001300Date2026MMDD000000.php` | migration | einmalige Datenaenderung | `php/lib/Migration/Version001200Date20260921000000.php` | exakt, Kopiervorlage |
| `php/templates/admin.php` | view / template | render | sich selbst, Bannerliste 209-250 | exakt |
| `php/js/admin.js` | view-script | poll-and-render | sich selbst, 1291-1307 | exakt |
| `php/lib/Service/AdminViewService.php` | service / transform | request-response | sich selbst, `backend()` 1795-1819 | exakt |
| `php/l10n/de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js` | config / i18n | - | sich selbst, gehalten von `test_admin_ui_contract.py:1521-1546` | exakt |
| `backend/appinfo/info.xml` | config | - | sich selbst, `FINDLING_LANGUAGES` 344-349 | exakt |
| `.github/workflows/deploy-harp.yml` | CI-config | Beweisstrecke | sich selbst, "Store upgrade 5" ab 3256, `snapshot()` ab 2773 | exakt |
| `backend/tests/test_upgrade_compatibility.py` | test / Sperrklinke | - | sich selbst, 66-110 | exakt |
| `backend/tests/test_admin_ui_contract.py` | test / Katalog-Gate | - | sich selbst, 1521-1546 | exakt |
| `backend/tests/conftest.py` | test-fixture | write-path | sich selbst, `write_index` 144-165 | exakt |
| `backend/tests/test_index_rebuild.py` (NEU) | test | batch | `backend/tests/test_index_writer.py` + `conftest.write_index` | Rollentreffer |
| AST-Waechter fuer Feldlisten (NEU, in `test_query_rewrite.py` oder eigener Datei) | test / Gate | - | `backend/tests/test_analyzer.py:440-470` | exakt |
| `docs/language-analyzers.md` und neue Zeilen in `docs/` | doc | - | sich selbst / `docs/l10n-french.md` | exakt |

---

## Pattern Assignments

### `backend/src/findling/index/schema.py` (model, 9 auf 13 Felder)

**Analog:** sich selbst. Die Datei ist eine Tabelle mit einer Begruendungszeile je Zeile, und
genau diese Form muss fuer vier neue Koerperfelder fortgeschrieben werden, nicht abgekuerzt.

**Konstanten- und Listenmuster** (Zeilen 33-57):

```python
FIELD_BODY_DE: Final = "body_de"
FIELD_BODY_EN: Final = "body_en"
FIELD_MTIME: Final = "mtime"

# In schema order. Callers that build documents read the names from here, because
# a field name that is written as a literal is a field name that is misspelled
# once: measured, Document.from_dict silently drops a name the schema does not
# know, and the value is gone without a single error anywhere.
FIELDS: Final = (
    FIELD_FILE_ID,
    ...
)
```

**Feldzeile mit Begruendung, die Vorlage fuer body_es/it/nl/pt** (Zeilen 106-111):

```python
    # The content, and the only stored copy of the text in the whole system. It
    # keeps positions because phrase queries and the snippet generator need them.
    builder.add_text_field(FIELD_BODY_DE, stored=True, tokenizer_name=TOKENIZER_DE)
    # The same text through the English pipeline. Not stored: the copy above is
    # the one snippets are cut from, and a second one would double the store.
    builder.add_text_field(FIELD_BODY_EN, stored=False, tokenizer_name=TOKENIZER_EN)
```

Die vier neuen Felder folgen `body_en` und nicht `body_de`: `stored=False`, und der Tokenizername
kommt aus einer Abbildung Code auf Kettenname. Ein `BODY_FIELD`-Dict (Code auf Feldname) ist neu
und gehoert hierher, weil RESEARCH.md es in `_document_from` und in `filled_languages` benutzt;
die Bauart dafuer steht in `config.py:139-146` (`SNOWBALL_NAME`), also geschlossene Abbildung,
nie zusammengesetzte Zeichenkette.

**Docstring-Pflicht** (Zeilen 1-25): der Kopf nennt heute "nine fields" und die beiden Messungen.
Eine 13-Felder-Fassung ohne fortgeschriebenen Kopf ist ein Diff, der die eigene Doku widerlegt;
die Zahlen aus RESEARCH.md Pattern 6 (+0,40 % leer, +150 % befuellt) gehoeren in genau diesen Kopf.

---

### `backend/src/findling/index/open.py` (factory, 4 auf 8 Ketten, sechster Merker)

**Analog:** sich selbst.

**Registriermuster** (Zeilen 96-102) - hier wachsen vier Zeilen an, und zwar unbedingt
unabhaengig von `settings().languages` (RESEARCH Pitfall 2):

```python
    path.mkdir(parents=True, exist_ok=True)
    index = Index.open(str(path)) if Index.exists(str(path)) else Index(build_schema(), path=str(path))
    index.register_tokenizer(TOKENIZER_DE, cached_german_analyzer(wordlist_hash(constituents), constituents))
    index.register_tokenizer(TOKENIZER_EN, english_analyzer())
    index.register_tokenizer(TOKENIZER_NAME, name_analyzer())
    index.register_tokenizer(TOKENIZER_STORED_ONLY, stored_only_analyzer())
    return index
```

Die Kettenfabrik fuer die vier neuen Sprachen steht bereits fertig in
`backend/src/findling/index/analyzer.py:232-303` (`snowball_analyzer(language)`), einarmig, mit
Allowlist-Pruefung und eigenem Supplement. Sie wird gerufen, nicht nachgebaut; `english_analyzer()`
(Zeile 229) ist selbst nur `return snowball_analyzer("english")` und damit die Vorlage fuer
`es`, `it`, `nl`, `pt`.

**Merker-Muster, die Stelle fuer den sechsten** (Zeilen 123-141):

```python
def expected_versions(digest: str) -> dict[str, str]:
    """Return the version marks an index built by this code must carry.

    The comparison itself lives in :meth:`findling.store.repo.Store.version_mismatch`:
    this module knows what the current code produces, the store knows what the
    existing index was built with, and only the caller that holds both may decide
    what a difference means. A mark that is missing counts as a difference there,
    which is why every value below is a string and none of them is optional.
    """
    return {
        "schema_version": str(SCHEMA_VERSION),
        _LOCAL_GENERATION: str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,
        "tantivy_version": TANTIVY_VERSION,
    }
```

Der zweite Parameter (Sprachmenge) folgt der Bauart von `digest`: hereingereicht, nicht im Modul
aus `settings()` gelesen. Vier Aufrufstellen sind zu bewegen, alle unten einzeln benannt.

**Praezedenz fuer eine benannte Ausnahme in der Saat** (Zeilen 53-55 und 248-252):

```python
# The one mark that is never written by the stamp below, spelled out here so
# that the exception is visible next to the function that has to make it.
_LOCAL_GENERATION: Final = "index_version"
```

```python
    for key, value in expected.items():
        if key == _LOCAL_GENERATION:
            continue
        store.write_meta(key, value)
    store.write_meta(REBUILD_MARK, "")
```

**Was hier nicht angefasst werden darf** (Zeilen 155-195, `start_rebuild_on_drift`): die Funktion
hebt die Generation, damit ein Crawl die Dateien wieder liest. Der Re-Analyse-Umbau liest keine
Datei. RESEARCH Anti-Patterns sagt das ausdruecklich; der Umbau braucht eine eigene, schmale
Stempelfunktion nach dem Muster von `stamp_after_rebuild` (198-254), aber mit anderem Tor.

---

### `backend/src/findling/store/repo.py` (store, dritte Ausnahme in `version_mismatch`)

**Analog:** sich selbst, zwei Stellen.

**Die Vergleichsschleife, in die die dritte `if`-Zeile kommt** (Zeilen 676-687):

```python
        stored = self.read_meta()
        diverging = []
        for key, value in expected.items():
            current = stored.get(key)
            if current == value:
                continue
            if key == "index_version" and _generation_at_least(current, value):
                continue
            if key == "tantivy_version" and _index_format_matches(current, value):
                continue
            diverging.append(key)
        return diverging
```

**Die Bauart einer Ausnahmefunktion, exakte Vorlage fuer `_languages_are_legacy`**
(Zeilen 1327-1342):

```python
def _index_format_matches(stored: str | None, expected: str) -> bool:
    """True when both banners name the same index format.

    The banner reads "tantivy v0.26.0, index_format v7", and only its second half
    decides whether the files on disk can still be opened. A banner without that
    half is a divergence, never a pass: a mark that cannot be read cannot be shown
    to match the current code, and an unknown state is a difference.
    """
    marker = "index_format "
    if not stored:
        return False
    ...
```

Merkmale, die zu uebernehmen sind: `stored: str | None` als erstes Argument, Rueckgabe `bool`,
Docstring mit dem Satz, warum ein unlesbarer Zustand kein Freifahrtschein ist, und der
Modulplatz direkt neben `_generation_at_least` (1315-1325). Fuer den Sprachmerker dreht sich
genau ein Satz um: Fehlen ist hier ausnahmsweise kein Drift, und der Absatz muss sagen, warum
(bis 1.2.0 filterte `_languages()` gegen `DEFAULT_LANGUAGES`, also kann kein Feldbestand
ausserhalb `de,en` existieren).

**Die Saat, aus der der neue Schluessel herausgehalten wird** (Zeilen 1394-1404):

```python
def _seed_meta(store: Store, meta: Mapping[str, str] | None) -> None:
    """Write the meta keys that are missing, touch none that are present."""
    stored = store.read_meta()
    seed = dict(_DEFAULT_META)
    seed.update(meta or {})
    seed.setdefault("created_at", str(int(time.time())))
    seed.setdefault("instance_id", uuid4().hex)

    for key, value in seed.items():
        if key not in stored:
            store.write_meta(key, value)
```

`_DEFAULT_META` steht in 119-127 und traegt heute sechs Schluessel plus `EMBEDDING_MARK`. Der
Sprachmerker gehoert **nicht** hinein, und der Kommentarblock 109-118 ist die Stelle, an der
diese Ausnahme begruendet wird.

**Die Groessensummierung, die nicht zweimal geschrieben wird** (Zeilen 1269-1312). Achtung,
Namenskorrektur an RESEARCH.md: die Funktion heisst oeffentlich `index_bytes(directory: Path)`,
nicht `_index_bytes`. Sie wird schon von `api/status.py:259` und `api/rates.py:139` benutzt,
faengt `OSError` und nennt nie einen Pfad.

---

### `backend/src/findling/index/writer.py` (service, Schleife ueber die aktiven Sprachen)

**Analog:** sich selbst, die Dokumentbauzeilen in `add()` (Zeilen 258-272):

```python
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, record.file_id)
        document.add_unsigned(FIELD_STORAGE_ID, record.storage_id)
        document.add_text(FIELD_NAME, name)
        document.add_text(FIELD_TITLE, title)
        document.add_text(FIELD_PATH, record.path)
        document.add_text(FIELD_EXT, record.ext)
        # body_de is the only stored copy of the text in the whole system, so it
        # carries the content whatever the language setting says. The setting
        # decides about the second, index only pipeline: with FINDLING_LANGUAGES
        # set to de the English field stays empty and the index shrinks by it.
        document.add_text(FIELD_BODY_DE, body)
        if self._index_english:
            document.add_text(FIELD_BODY_EN, body)
        document.add_integer(FIELD_MTIME, record.mtime)
        writer.add_document(document)
```

Der `if self._index_english`-Zweig wird zur Schleife ueber die aktive Sprachmenge. Das Flag
selbst kommt heute aus dem Konstruktor (Zeile 166):

```python
        self._index_english = ("en" in resolved.languages) if index_english is None else index_english
```

Dieselbe Form (aufgeloest aus `settings()`, ueberschreibbar per Parameter fuer die Suite) gilt
fuer die Sprachmenge. Der Absatz, den RESEARCH.md fordert ("gespeichert" gegen "durch die
deutsche Kette analysiert"), gehoert genau an die `body_de`-Zeile oben.

**Die Plattenmuster, die `rebuild.py` benutzt statt nachzubauen** (Zeilen 365-386):

```python
    def free_bytes(self) -> int:
        """Free space on the volume this index is written to.

        Public because it is not only this class that writes to that volume.
        ...
        Two calls to ``shutil.disk_usage`` with two paths would be two answers
        about one volume, and the one that was measured is the one at :meth:`flush`.
        """
        return shutil.disk_usage(self._directory).free

    def disk_is_tight(self) -> bool:
        """True while the volume sits below the configured free space floor.
        ...
        """
        return self.free_bytes() < self._min_free_bytes
```

**Das Schliessmuster fuer den Tausch** (Zeilen 427-438):

```python
    def close(self) -> None:
        """Wait for the merging threads and release the lock. Idempotent.

        This does not commit. Whatever is still pending is lost on purpose: the
        batch is the crash granularity, ...
        """
        writer = self._writer
        if writer is None:
            return
        self._writer = None
        writer.wait_merging_threads()
```

Der Umbau muss vor dem ersten `rename` genau diese Reihenfolge fahren: committen, dann
`wait_merging_threads()`, dann das Objekt loslassen.

**Modulkopf als Vorbild:** Zeilen 1-49 sind die Form, die `rebuild.py` erben soll. Ein Absatz je
gemessener Falle, jede Messung mit ihrem Ergebnis, kein allgemeiner Rat. Die vier Messreihen aus
RESEARCH.md (Bandlauf 683 Dok/s, `to_dict()`-Form, WinError 5 beim offenen Handle,
nicht registrierte Kette wirft beim Schreiben) gehoeren in genau diese Bauart.

---

### `backend/src/findling/index/rebuild.py` (NEU: service, batch / transform)

**Analoga, nach Aufgaben zerlegt (kein einzelnes Vorbild deckt das Modul ab):**

| Aufgabe im neuen Modul | Von wo kopieren |
|---|---|
| Modulkopf, Messabsaetze, Bezeichnerdisziplin | `index/writer.py:1-49` |
| Ein Index oeffnen (nie `Index(...)` direkt) | `index/open.py:84-102`, `open_index(path, constituents)` |
| Reader konfigurieren, Searcher holen | `index/open.py:105-120`, `open_reader(index)` |
| Dokument feldweise bauen | `index/writer.py:258-272` |
| Freier Platz, Bodenwert | `index/writer.py:365-386` |
| Indexgroesse | `store/repo.py:index_bytes` (1269-1312) |
| Fehlerlogs ohne Pfad, nur `type(error).__name__` | `store/repo.py:1306-1308`, `api/resources.py:332-335` |
| Frozen dataclass als Verdikt | `index/writer.py`, `FlushResult` (Suchbegriff `@dataclass`, Zeile 60 ff.) |
| Zustandsloses Fortschrittslesen | RESEARCH Pattern 2, kein Analog im Baum |

**Das Verbotsmuster, das die Namensgebung diktiert** (`backend/tests/test_readonly_gate.py:63-75`):

```python
FORBIDDEN_IDENTIFIERS = frozenset(
    {
        "set_user",
        "upload",
        "upload_stream",
        "delete",
        "move",
        "copy",
        "mkdir",
        "makedirs",
        "trash",
    }
)
```

Das Gate liest jedes `ast.Attribute`, jeden `ast.Name` und jedes `FunctionDef` in jedem Modul des
Pakets (Zeilen 336-347). Konsequenz fuer `rebuild.py`: keine Funktion `delete_*`, kein
`shutil.move`, kein `Path.copy`, kein `mkdir` ohne Eintrag in `INVARIANT_2_EXCEPTIONS` (die
Ausnahmetabelle steht ab Zeile 76 und ist paarweise, Modul plus Bezeichner). `open_index` hat fuer
sein `path.mkdir` genau so einen Eintrag; wenn `rebuild.py` selbst ein Verzeichnis anlegt, braucht
es einen eigenen, und der Plan muss ihn nennen.

Bezeichnervorschlaege aus RESEARCH.md, die das Gate passieren: `swap_in`, `retire_directory`,
`discard_directory`, `drop_document` (letzteres ist im Baum bereits die Loesung desselben
Problems, `index/writer.py:283-300`).

---

### `backend/src/findling/api/resources.py` (provider, `reset_read_side()`)

**Analog:** sich selbst, der vorhandene Freigabezweig in `read_side()` (Zeilen 282-298):

```python
    global _OPEN
    resolved = settings()
    with _LOCK:
        if _OPEN is not None and _OPEN.index_dir == resolved.index_dir:
            return _OPEN

        # The cached handle belongs to a directory that is no longer the one the
        # settings name, so it is released here and not further down. It used to
        # be released after the two checks below, which meant the branch for a
        # volume that has nothing yet walked straight past it: the connection
        # then lived on with nothing referring to it, for as long as the process
        # did.
        previous, _OPEN = _OPEN, None
        if previous is not None:
            previous.store.close()
            if previous.vectors is not None:
                previous.vectors.close()
```

Das ist die Vorlage Zeile fuer Zeile: `global _OPEN`, `with _LOCK`, lokale Uebernahme vor dem
Nullsetzen, `store.close()` und `vectors.close()` in dieser Reihenfolge. `_LOCK` ist ein
`threading.RLock()` (Zeile 117), `_OPEN` steht auf Zeile 100. Der Unterschied der neuen Funktion
ist allein die Bedingung: sie prueft den Pfad **nicht**, weil der Pfad sich beim Tausch nicht
aendert (RESEARCH Pitfall 3).

Zu beachten: `_DEGRADED` ist ein zweiter Prozesscache unter demselben `_LOCK` (Zeilen 372-382) und
haengt ebenfalls an `index_dir`. Ein `reset_read_side()`, das ihn stehen laesst, meldet nach dem
Tausch bis zu `DEGRADED_TTL_SECONDS` lang den alten Zustand.

**Aufrufstelle des Merkersatzes, die den zweiten Parameter bekommt** (Zeilen 139-149):

```python
        try:
            marks = expected_versions(build_artifact().digest)
        except OSError:
            LOGGER.warning("the constituent list is unavailable, version marks cannot be compared")
            return None
        # The one mark that does not come from the index side. It is added here
        # and not in expected_versions() on purpose: that function feeds
        # start_rebuild_on_drift, ...
        marks[EMBEDDING_MARK] = embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap)
```

Das ist zugleich die im Baum vorhandene Praezedenz dafuer, dass ein Merker bewusst ausserhalb von
`expected_versions()` gefuehrt wird (RESEARCH Pattern 4, Schritt 2).

---

### `backend/src/findling/api/status.py` (controller, `languagesActive` und Umbaufortschritt)

**Analog:** sich selbst.

**Feldmuster des Antwortmodells** (Zeilen 113-122 und 165-175):

```python
class StatusResponse(BaseModel):
    """The operating state of one container.

    Every field defaults, so the answer for a container that has nothing yet is
    the same shape as the answer for one that has been running for a month. A
    status output whose fields come and go cannot be read by a page that has to
    render both.
    """
```

```python
    # Which of five states the embedding engine is in, out of embed/engine.py.
    # The other half of ``embedded`` above and never a second spelling of it:
    # ...
    # Defaulted to the empty string like every other field of this answer, and
    # deliberately not to one of the five words: a default that named a state
    # would be a claim this module makes without having asked.
    engineState: str = ""
    note: str = ""
```

Regeln, die daraus folgen: camelCase auf der Leitung, jedes Feld mit Vorgabewert, jedes neue Feld
mit einem Absatz, der sagt, was es **nicht** ist. `languagesActive` ist der gespeicherte Merker
(billig), `languagesFilled` gehoert laut RESEARCH.md ausdruecklich **nicht** hierher, sondern in
`api/diagnose.py`, weil `/status` bei jedem Tastendruck der Unified Search mitlaeuft.

**Das Durchreichmuster fuer Werte, die nicht aus der Zustandsdatenbank kommen** (Zeilen 341-356):

```python
        appVersion=volume.appVersion,
        embedded=volume.embedded,
        engineState=volume.engineState,
        note=volume.note,
        lowDisk=volume.lowDisk,
```

Der Umbaufortschritt ist ein Prozesswert wie `engineState` und reist genau so: in `_volume()`
gesetzt, in `_of()` durchgereicht, nie zweimal gelesen.

**Route** (Zeilen 425-428): `return await asyncio.to_thread(report)`, blockierende Arbeit nie auf
dem Loop.

---

### `backend/src/findling/main.py` (Lifespan-Aufgabe 4 und die OCR-Startwarnung)

**Analog:** `_release_when_idle` (Zeilen 254-325) ist die dritte langlaufende Aufgabe und damit
das Vorbild fuer die vierte, bis in die Fehlerbehandlung:

```python
    while not stop_event.is_set():
        await _pause(RELEASE_TICK_SECONDS, stop_event)
        if stop_event.is_set():
            break
        try:
            ...
            if await asyncio.to_thread(release_if_idle, ttl_seconds) and poller is not None:
                await asyncio.to_thread(poller.release_cutter)
        except asyncio.CancelledError:
            # Ahead of the general branch, exactly like _guarded_reconcile: a
            # task that was cancelled must not read as an unexpected failure.
            raise
        except Exception as error:
            kind_of_failure = type(error).__name__
            LOGGER.error(
                "a tick of the release task ended in an unexpected %s; the next tick runs, "
                "search and indexing continue",
                kind_of_failure,
            )
```

**Anlegemuster im Lifespan** (Zeilen 411-418):

```python
    stop_release = asyncio.Event()
    releasing: asyncio.Task[None] | None = None
    if settings().embed_idle_release_seconds > 0:
        releasing = asyncio.create_task(_release_when_idle(stop_release))
        LOGGER.info("findling releases the embedding engine after an idle span")
```

**Abbaumuster im `finally`** (Zeilen 501-509):

```python
        if releasing is not None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(asyncio.shield(releasing), timeout=RELEASE_STOP_SECONDS)
            if not releasing.done():
                releasing.cancel()
                await asyncio.gather(releasing, return_exceptions=True)
```

Der Umbau braucht sein eigenes `REBUILD_STOP_SECONDS` neben `POLLER_STOP_SECONDS`,
`RECONCILE_STOP_SECONDS`, `RELEASE_STOP_SECONDS`, und der Plan muss den Wert begruenden: ein
Band ist die Abbruchkoernung, also ist das Budget die Zeit eines Bandes.

**Startwarnung, Platz und Muster** (Zeilen 365-388): `report_version_drift()` wird dort per
`asyncio.to_thread` gerufen, mit dem Absatz, warum eine Warnung nichts entscheidet. Die
OCR-Mismatch-Warnung gehoert an dieselbe Stelle und in dieselbe Form.

---

### `backend/src/findling/config.py` (SCHEMA_VERSION 2, `_languages()` gegen `SNOWBALL_NAME`)

**Analog:** sich selbst.

**Die Zeile, die zu heben ist** (Zeilen 38-41):

```python
# Layout of the tantivy schema. Raised when a field is added, removed or retyped;
# every raise forces a visible reindex rather than a silently mixed index.
SCHEMA_VERSION = 1
```

**Die eine Zeile mit der ganzen Wirkung** (Zeilen 1068-1081):

```python
def _languages() -> tuple[str, ...]:
    """Return the active language fields, in schema order.

    An empty or unrecognisable list keeps both fields. Dropping to no language at
    all would produce an index that cannot answer anything, which is a worse
    outcome than ignoring the variable.
    """
    requested = {part.strip().lower() for part in os.environ.get("FINDLING_LANGUAGES", "").split(",")}
    kept = tuple(language for language in DEFAULT_LANGUAGES if language in requested)
    if kept:
        return kept
    if requested - {""}:
        LOGGER.warning("FINDLING_LANGUAGES names no supported language, falling back to the built in default")
    return DEFAULT_LANGUAGES
```

Der Filter wandert von `DEFAULT_LANGUAGES` auf die Schluessel von `SNOWBALL_NAME` beziehungsweise
`SUPPORTED_LANGUAGES`. Die Iteration laeuft weiter ueber die geordnete Konstante und nie ueber die
Eingabe, weil genau das die Normalisierung ist, die den Merker traegt. `DEFAULT_LANGUAGES` bleibt
`("de", "en")`, E-17-3 Option a.

Der Kommentar an `SUPPORTED_LANGUAGES` (Zeilen 121-135) sagt heute "No production path reads this
constant in phase 17, and that is deliberate". Dieser Absatz muss in diesem Plan mitgehen, sonst
steht in der Datei die Behauptung und drei Zeilen weiter ihre Widerlegung.

**Vorlage fuer einen Allowlist-Filter mit Warnung** (`_ocr_languages`, Zeilen 1093-1131) und
**Vorlage fuer einen neuen Schalter** `FINDLING_REBUILD_FALLBACK` (`_bool_from_environment`,
Zeilen 1037-1052, und die Aufloesung in `settings()` ab 1180). Die Hausregel steht dort mehrfach
ausgeschrieben: eine unlesbare Einstellung ist eine Warnung, nie eine Startverweigerung, und die
Warnung nennt den Variablennamen und nie den Wert.

**Bodenwert, der nicht bewegt wird** (Zeile 210, `MIN_FREE_BYTES = 524_288_000`, aufgeloest in
`settings()` Zeile 1195). Der Umbau addiert seinen Bedarf darauf.

---

### `backend/src/findling/worker/poller.py` und `tools/one_load.py` (Aufrufstellen)

**Analog:** `_open_state()` (Zeilen 305-326), die Stelle, an der Saat und Driftpruefung
zusammentreffen:

```python
    expected = expected_versions(build_artifact().digest)
    store = open_store(settings().state_db, meta=expected)
    start_rebuild_on_drift(store, expected)
    return store
```

Vier Aufrufstellen von `expected_versions(...)` sind zu bewegen, alle am 2026-09-24 nachgezaehlt:

| Datei:Zeile | Kontext |
|---|---|
| `backend/src/findling/api/resources.py:139` | `expected_marks()`, haengt `EMBEDDING_MARK` an |
| `backend/src/findling/worker/poller.py:322` | `_open_state()`, die Saat |
| `backend/src/findling/worker/poller.py:1833` | `stamp_after_rebuild(...)` |
| `backend/src/findling/tools/one_load.py:265` | `open_store(resolved.state_db, meta=expected_versions(artifact.digest))` |

Dazu die Testfixture `backend/tests/conftest.py:169`
(`open_store(root / "state.db", meta=expected_versions(corpus.digest))`).

**Ruhigstellen und Scharfschalten** (Zeilen 509-526):

```python
    def arm(self) -> None:
        """Let the task collect work again. ..."""
        self._idle_announced = False
        self._armed.set()

    def silence(self) -> None:
        """Stop collecting work without ending the task. ..."""
        self._armed.clear()
```

Der Aufrufer im Baum, der beides in einer Schleife ueber beide Aufgaben macht, steht in
`main.py:221-227`.

**Der umgekehrte Fall des Aufraeumpfads** (Zeilen 342-367, `_raise_generation_for_lost_index`):
leerer Index neben einer vollen Zustandsdatenbank. Der Startpfad-Fall dieser Phase (ein
`index.rebuild` oder `index.retired` ohne `index`) hat kein Vorbild, siehe "No Analog Found".

---

### `backend/src/findling/tools/index_status.py` (Bericht, sechster Eintrag)

**Analog:** sich selbst (Zeilen 60-66 und 94):

```python
_VERSION_KEYS: Final = {
    "schemaVersion": "schema_version",
    "indexVersion": "index_version",
    "analyzerVersion": "analyzer_version",
    "wordlistHash": "wordlist_hash",
    "tantivyVersion": "tantivy_version",
}

# A version mark this tool could not read at all. Deliberately different from
# repo.UNKNOWN_VERSION ("unknown"), which means "the database has no value for
# this": an empty string here says the database was not there to be asked.
_NO_VALUE: Final = ""
```

```python
    report.update(dict.fromkeys(_VERSION_KEYS, _NO_VALUE))
```

Ein Eintrag hier, camelCase links, Merkername rechts, und `empty_report()` fuellt den neuen
Schluessel automatisch mit. Das ist zugleich Zusicherung 2 und der Ersatz fuer die gestorbene
Zusicherung 6 der CI-Strecke: `marks.languages` gibt es in 1.2.0 nicht und in 1.3.0 schon.

---

### `php/lib/Migration/Version001300Date2026MMDD000000.php` (NEU, migration)

**Analog:** `php/lib/Migration/Version001200Date20260921000000.php`, vollstaendige Kopiervorlage.
Zu aendern sind Klassenname, Dateiname und Datum, sonst nichts.

**Der Rumpf** (Zeilen 73-98):

```php
class Version001200Date20260921000000 extends SimpleMigrationStep {
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

**Die drei Saetze des Klassenkommentars, die mitwandern muessen** (Zeilen 37-45, 55-61, 68-71):

```
 * **Every minor step needs a migration of this shape, as long as the recorded
 * version is maintained the way it is today.**
 ...
 * Nothing is asked of the container here. A migration runs inside occ upgrade,
 * with the instance in maintenance mode, without a logged in user, and at a
 * moment when AppAPI may be restarting the container: adminGet() needs a user
 * id and a proxy request needs a container that answers, so a migration that
 * waits on either can turn an app update into a failed one.
 ...
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
```

Der mittlere Absatz ist zugleich der Beleg fuer das Anti-Pattern "den Umbau in die PHP-Migration
legen". Der Gleichstand-Test dafuer ist `backend/tests/test_lockstep_versions.py`.

---

### `php/templates/admin.php`, `php/js/admin.js`, `php/lib/Service/AdminViewService.php` (sechstes Banner)

**Analog:** die Bannerliste in `admin.php` (Zeilen 205-250). Ein Eintrag hat vier Schluessel und
steht mit einem Begruendungskommentar in der Liste:

```php
	[
		'id' => 'findling-banner-reindex',
		'kind' => 'warning',
		'icon' => $alertIcon,
		'text' => $l->t('The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.'),
		'shown' => ($backend['reindexRequired'] ?? false) === true,
	],
```

Das neue Banner steht daneben und ersetzt es nicht (RESEARCH Anti-Patterns: der Reindex-Rat kostet
den Nutzer waehrend eines billigen Umbaus 19 Stunden aus Versehen). `kind` ist `warning` oder
`info`, der Text nennt: warten, Fortschritt, und dass die Suche weiter antwortet.

**Renderrahmen, der nicht angefasst wird** (Zeilen 256-272): jedes Banner wird gerendert und mit
`hidden` versteckt, der Text liegt in einem eigenen `<span>` mit abgeleiteter id, weil ein
`textContent` auf dem Absatz das Icon loeschen wuerde.

**Script-Seite** (`php/js/admin.js:1291-1307`):

```js
    shown('findling-banner-unreachable', view.backendReachable !== true)
    ...
    shown('findling-banner-lowdisk', backend.lowDisk === true)
    shown('findling-banner-reindex', backend.reindexRequired === true)
```

Ein Banner mit wechselndem Satz (Fortschrittszahl) braucht zusaetzlich das `text(...)`-Muster der
Lockstep-Zeile 1299-1303.

**Durchreichen aus der Containerantwort** (`AdminViewService.php:1795-1819`):

```php
	private function backend(?array $answer): array {
		$answer ??= [];

		return [
			...
			'reindexRequired' => ($answer['reindexRequired'] ?? false) === true,
			'lowDisk' => ($answer['lowDisk'] ?? false) === true,
			'diskFreeBytes' => $this->counter($answer, 'diskFreeBytes'),
			...
			'engineState' => self::engineState($answer['engineState'] ?? null),
			'note' => $this->text($answer, 'note'),
		];
	}
```

Jeder neue `/status`-Schluessel braucht hier eine Zeile, sonst kommt er auf der Seite nie an.
Boolesche Werte mit `=== true`, Zahlen ueber `counter()`, Texte ueber `text()`, und ein Wert, der
"der Container hat nichts gesagt" von "der Container sagt null" trennen muss, ueber
`optionalCounter()` (Begruendung im Docstring Zeilen 1783-1791).

---

### `php/l10n/*` (sechs Dateien im Gleichstand)

**Analog:** der Bestand selbst, gehalten von zwei Gates.

`de.json` hat die Form `{"translations": {...}}`, `de.js` die Form
`OC.L10N.register("findling", { ... }, "nplurals=2; plural=(n != 1);")`. `de_DE.*` ist eine
zeichengleiche Kopie von `de.*`, das prueft
`backend/tests/test_admin_ui_contract.py:1521-1526`:

```python
    for language, twin in ((L10N_JSON, L10N_DE_DE_JSON), (L10N_JS, L10N_DE_DE_JS)):
        assert twin.is_file(), f"{twin.name} is missing, so everybody on de_DE reads this app in English"
        assert twin.read_text(encoding="utf-8") == language.read_text(encoding="utf-8"), (
            f"{twin.name} and {language.name} have drifted apart"
        )
```

Die harte Zahl steht auf Zeile 1545:

```python
    assert len(set(map(frozenset, keys_of.values()))) == 1, f"the four catalogues disagree: {sorted(keys_of)}"
    assert len(keys_of["de.json"]) == 199
```

Und die Pflicht, die daran haengt, steht im Docstring (Zeilen 1519-1520):

```
    This paragraph carries the same duty as the three above it. Whoever raises
    the figure next writes the next paragraph.
```

Also: Zahl beim Planstart aus der Datei zaehlen, nicht aus RESEARCH.md uebernehmen, neue Zahl
setzen, Absatz mit Datum und Begruendung darunter. Franzoesisch nach `docs/l10n-french.md` mit
datiertem Vorbehalt; das zweite Gate ist
`test_all_six_catalogues_carry_the_same_keys` (ab Zeile 1548).

---

### `.github/workflows/deploy-harp.yml` ("Store upgrade 6" daneben, nicht statt)

**Analog:** "Store upgrade 5, the six assurances after the upgrade" (ab Zeile 3256).

**Die Schrittbedingung, die jeder Schritt einzeln traegt** (Zeile 3257):

```yaml
        if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04' && env.RELEASE_TAG == ''
```

**Der Vergleichshelfer und die Regel, dass jeder Vergleich laeuft** (Zeilen 3265-3281):

```bash
          fail=0
          # One comparison, one sentence saying what it means, and every one of
          # them runs: a step that stopped at the first difference would hide
          # which of the six the upgrade broke.
          unchanged() {
            path="$1"
            meaning="$2"
            was=$(jq -r "${path}" "${before}")
            now=$(jq -r "${path}" "${after}")
            if [ "${was}" != "${now}" ]; then
              echo "::error::${meaning}: ${path} was ${was} before the upgrade and is ${now} after it"
              fail=1
            else
              echo "unchanged  ${path} = ${was}   (${meaning})"
            fi
          }
```

**Die Vorlage fuer eine Marke, die sich bewegen DARF** (Zeilen 3292-3329): der
`tantivyVersion`-Block ist das Muster fuer `schemaVersion` in der neuen Strecke. Er prueft zuerst,
dass ueberhaupt etwas Vergleichbares dasteht, dann den erlaubten Teil der Bewegung, und er
unterscheidet in der Ausgabe "unchanged", "moved on purpose" und Fehler. Genau diese drei Aeste
braucht Zusicherung 1 ("um genau eine Stufe").

**Die Momentaufnahme, die um zwei Felder waechst** (ab Zeile 2773, `snapshot()`): jeder Wert wird
erst in eine Shellvariable gelesen, jeder Leerwert ist ein Abbruch mit Ausgabe des Rohtextes, und
erst danach baut ein einziges `jq -n` das Objekt. Neue Felder folgen dieser Reihenfolge.

**Die eine Zeile mit Fernwirkung** (Zeile 100): `UPGRADE_FROM_TAG: v1.1.0` wandert auf `v1.2.0`.
Folge laut RESEARCH.md: Zusicherung 6 der bestehenden Strecke (Datumsgrenzen des Providers) faellt
um und braucht `marks.languages` als Nachfolger; der Kommentarblock bei Zeile 2705 ist die Vorlage
dafuer, wie so eine Kandidatenpruefung dokumentiert wird. Ein Diff, der Zeilen aus "Store upgrade
5" entfernt, ist Pitfall 6.

---

### `backend/tests/test_upgrade_compatibility.py` (Sperrklinke umdrehen, nicht gruen machen)

**Analog:** sich selbst, Zeilen 66-110.

```python
GOLD_V1_0_AND_V1_1 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": GOLD_INDEX_FORMAT,
}

# The five marks an index carries. A mark that disappears counts as a difference
# in Store.version_mismatch, so a set that shrank would trigger a rebuild just as
# surely as a value that changed.
ALL_MARKS = ("schema_version", "index_version", "analyzer_version", "wordlist_hash", TANTIVY_MARK)
```

**Die Bauart der begruendeten Bewegung**, gelesen an der Stelle, an der der tantivy-Pin bewegt
wurde (Zeilen 93-104):

```python
# The pin the banner above grows out of. Named here because a moved pin and a
# moved mark are the same event seen from two sides. The patch number may move
# with a decision behind it; the format half above may not.
#
# It walked from 0.26.0 to 0.26.2 on 2026-09-23 in plan 17-08, under the owner
# decision E-17-7 option a of the same day, and it walked only after plan 17-07
# had loosened the comparison rule, so that the loosening stayed provable on its
# own. ...
TANTIVY_PIN = "tantivy==0.26.2"
```

Das ist die Form, die RESEARCH Pitfall 5 verlangt: zweite Goldtabelle `GOLD_V1_3` **neben** der
alten, Datum, Entscheidnummer (E-17-1 bis E-17-4, 23.09.2026), und ein Test, der den Sprung als
genau eine Stufe festhaelt. Der Kopf der Datei (Zeilen 15-18) sagt, warum ein Edit ohne Absatz
nicht zulaessig ist:

```
**A red test here is not a repair, it is a question for the owner.** Nothing in
this file may be adjusted to make it green again.
```

**Selbsttest gegen ein gestelltes Muster** (`test_the_drift_reader_fires_on_a_staged_sample`,
ab Zeile 135) und `drift_findings` (110-133) sind mitzufuehren, damit ein geloeschter Rumpf nicht
gruen aussieht.

---

### AST-Waechter fuer die Feldlisten (NEU) und der Mengeninklusionstest

**Analog:** `backend/tests/test_analyzer.py:440-470`, der Waechter aus dem Muster von Plan 17-03:

```python
def normalize_callers(relative_path: str, source: str) -> list[str]:
    """Modules that call the normalisation helper, read off the syntax tree.

    ...
    Reading the tree is also the comment filter this count needs: a comment that
    says "never call normalize() here" is not part of the tree, so it cannot
    raise the number.
    """
    normalized = relative_path.replace("\\", "/")
    tree = ast.parse(source, filename=relative_path)
    return [
        normalized
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "normalize"
    ]


def test_the_helper_is_called_from_exactly_two_modules() -> None:
    callers = sorted(...)
    # Not a tautology, a ratchet. One caller means one side normalises and the
    # other does not, ... Three means a third text space that nobody compares
    # against the first two.
    assert tuple(callers) == EXPECTED_NORMALIZE_CALLERS
```

Zu uebernehmen: Quelle als Text lesen und parsen (nicht importieren), Pfad posix-normalisieren,
das Ergebnis gegen eine benannte Konstante stellen, und der Satz "Not a tautology, a ratchet" als
Begruendungsform.

**Das Gegenstueck, das die Zielobjekte nennt** (`backend/src/findling/query/rewrite.py:55-65`):

```python
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE]
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]
FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8}
```

Diese drei ruehrt Phase 18 nicht an; der Waechter haelt genau das fest, solange die Feldliste eine
Konstante ist, und ist der Teil, den Phase 19 bewusst umbaut.

**Die Fixture fuer den echten Schema-1-Index** (`backend/tests/conftest.py:144-165`):

```python
def write_index(root: Path, documents: int) -> None:
    """Write the documents the endpoint suites search in, and commit them."""
    index = open_index(root / "index", CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id in range(1, documents + 1):
        document = Document()
        # Field by field, never through keyword arguments: a keyword built
        # document puts an I64 into the U64 column of file_id and the indexing
        # thread panics after the Python call has already returned.
        document.add_unsigned(FIELD_FILE_ID, file_id)
        ...
    writer.commit()
    writer.wait_merging_threads()
    index.reload()
```

Fuer Phase 18 braucht es eine zweite Fixture derselben Bauart, die gegen ein **festgehaltenes**
Schema 1 baut (nicht gegen `build_schema()`, das dann 13 Felder liefert), damit
`test_the_query_fields_exist_in_both_schema_generations` und der `build_query`-Lauf gegen einen
echten Altindex moeglich sind. `commit()` plus `wait_merging_threads()` plus `reload()` ist die
Reihenfolge, ohne die ein Test gegen den Stand vor dem Commit prueft.

**Form der Gate-Dateien insgesamt:** `backend/tests/test_search_fields_lockstep.py:19-25` schreibt
sie aus, und sie gilt fuer jedes neue Gate dieser Phase:

```
The shape is the shape of ``test_search_limits_lockstep.py`` ...: it reads the
sources as text rather than importing them, so that a model which does not even
import any more is a red gate and not an error in collection; it fails closed,
so a file that moved produces a finding for every field that should have come
out of it; and it carries self tests against staged samples, so that a gate
whose body was deleted cannot report zero findings over zero fields and look
healthy.
```

---

## Shared Patterns

### Logzeilen

**Quelle:** `backend/src/findling/store/repo.py:1306-1308`, `backend/src/findling/api/resources.py:332-335`
**Gilt fuer:** `index/rebuild.py`, `main.py`, jede neue Warnung

```python
        except Exception as error:
            # The type name and nothing else. A traceback here would carry
            # whatever a library put into its message, and a path is the usual
            # content.
            LOGGER.warning("the read side could not be opened, an unexpected %s", type(error).__name__)
```

Nie ein Pfad, nie ein Nutzertext, nie ein Dokumentname. Die Umbauzeilen zaehlen Dokumente. Die
Startwarnung nennt laut Hausregel von `config.py` den Variablennamen und die Anzahl, nie die Werte;
die Sprachnamen gehen ueber `/status` an die Adminseite.

### Logger je Modul

**Quelle:** `backend/src/findling/index/open.py:41`
**Gilt fuer:** `index/rebuild.py`

```python
LOGGER = logging.getLogger("findling.index.open")
```

### Bezeichnerverbot (Readonly-Gate A)

**Quelle:** `backend/tests/test_readonly_gate.py:63-75` (Menge) und 336-347 (Pruefung)
**Gilt fuer:** jedes Modul unter `backend/src/findling/`

```python
        identifier: str | None = None
        lineno = 0
        if isinstance(node, ast.Attribute):
            identifier, lineno = node.attr, node.lineno
        elif isinstance(node, ast.Name):
            identifier, lineno = node.id, node.lineno
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            identifier, lineno = node.name, node.lineno
        if identifier in FORBIDDEN_IDENTIFIERS and (normalized, identifier) not in INVARIANT_2_EXCEPTIONS:
            violations.append(f"{normalized}:{lineno}: invariant 2, writing identifier {identifier}")
```

`delete`, `move`, `copy`, `mkdir`, `makedirs` sind gesperrt, auch als Attributname und als
Funktionsname. Ausnahmen sind paarweise (Modul, Bezeichner) einzutragen und im Plan zu begruenden.

### Ein Index wird nur ueber `open_index` geoeffnet

**Quelle:** `backend/src/findling/index/open.py:1-16`, gehalten von `backend/tests/test_index_open.py`
**Gilt fuer:** `index/rebuild.py`, beide Seiten des Umbaus

Der Waechter laeuft ueber das ganze Paket. Ein `Index(...)` oder `Index.open(...)` in `rebuild.py`
ist ein roter Lauf, also gehen Quell- und Zielverzeichnis durch `open_index(path, constituents)`.

### Blockierendes gehoert in einen Worker-Thread

**Quelle:** `backend/src/findling/main.py:365`, `backend/src/findling/api/status.py:428`
**Gilt fuer:** die Umbau-Aufgabe, `reset_read_side()`, jede Plattenmessung im Lifespan

```python
    return await asyncio.to_thread(report)
```

### Eine Warnung entscheidet nichts

**Quelle:** `backend/src/findling/api/resources.py:384-390`
**Gilt fuer:** Startwarnung OCR, Platzwarnung, Sprachdrift

```python
def report_version_drift() -> None:
    """Log a version drift once at startup, and decide nothing about it.

    What follows from a drift is the poller's business: ... What is not
    defensible is a drift nobody ever hears about.
    """
```

### Merker lesen und schreiben

**Quelle:** `backend/src/findling/store/repo.py:620-629`
**Gilt fuer:** die neue Stempelfunktion des Umbaus

```python
    def read_meta(self) -> dict[str, str]:
        """All version marks and provenance values as one mapping."""
        return {str(key): str(value) for key, value in self._conn.execute("SELECT key, value FROM meta")}

    def write_meta(self, key: str, value: str) -> None:
        """Set one meta value, overwriting an existing one."""
        self._conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
```

### Sprache und Zeichensatz

**Quelle:** `CLAUDE.md`, durchgaengig im Baum bestaetigt
**Gilt fuer:** alles

Code, Bezeichner, Kommentare, Docstrings und Logtexte englisch und ASCII. Echte Umlaute nur in
deutscher Prosa (dieses Dokument, Planungsdateien) und in Katalogwerten der l10n-Dateien. Keine
Em-Dashes, auch nicht in Kommentaren.

---

## No Analog Found

| Datei / Mechanik | Rolle | Datenfluss | Grund |
|---|---|---|---|
| Der Verzeichnistausch in `index/rebuild.py` (`swap_in`, `retire_directory`) | service | file-I/O | Kein Verzeichnistausch existiert heute im Baum. Vorlage ist RESEARCH.md "Der Tausch" plus die Messreihe zu WinError 5; die Reihenfolge ist der ganze Inhalt der Funktion und wird von dort genommen, nicht erfunden |
| `_resume_cursor()`, Fortschritt aus dem Zielindex | service | batch | Jeder Fortschritt im Baum haengt heute an `state.db` (Generation, Reconcile-Bookmark). Ein zustandsloser Cursor aus einem Fast Field hat kein Vorbild; Grundlage ist RESEARCH Pattern 2 mit der Messung vom 2026-09-24 |
| Der Aufraeumpfad beim Start (`index.rebuild` oder `index.retired` ohne `index`) | service | file-I/O | `_raise_generation_for_lost_index` (`worker/poller.py:342-367`) behandelt nur den umgekehrten Fall, leerer Index neben voller Datenbank. RESEARCH Open Question 2 empfiehlt einen eigenen Plan mit vier Faellen und je einem Test |
| Der Bandlauf ueber `Query.range_query` | service | batch | Im Baum wird nur `Query.term_query` und `Query.all_query` benutzt (`index/writer.py:254`, `index/search.py`). Die Bandform stammt aus der Messung in RESEARCH Pattern 1 |
| `filled_languages()` ueber `terms_with_prefix` | controller (diagnose) | request-response | `Searcher.terms_with_prefix` wird heute nirgends gerufen. Kostenvorbehalt aus RESEARCH gilt: gehoert in `api/diagnose.py`, nicht in `/status` |

Fuer diese fuenf gilt: der Planer nimmt die Muster aus RESEARCH.md und nicht aus dem Baum, aber die
**Form** (Modulkopf, Logregel, Bezeichnerverbot, Verdikt als frozen dataclass) kommt weiterhin aus
den oben benannten Analoga.

---

## Metadata

**Suchraum:** `backend/src/findling/**`, `backend/tests/**`, `php/lib/**`, `php/templates/**`,
`php/js/**`, `php/l10n/**`, `.github/workflows/deploy-harp.yml`, `docs/**`
**Dateien gescannt:** 41 Python-Module (20.286 Zeilen), 74 Testdateien dem Namen nach, 7
PHP-Migrationen, 6 Katalogdateien, 1 Workflow
**Nicht gelesen und bewusst nicht als Analog gefuehrt:** `worker/reconcile.py`, `embed/*`,
`extract/*`, `nc/*`, weil keine Datei dieser Phase in ihre Rolle faellt
**Extraktionsdatum:** 2026-09-24
**Gueltigkeit:** solange keine der zitierten Dateien bewegt wird. Alle Zeilennummern sind vor dem
ersten Plan dieser Phase erneut zu pruefen, sobald ein Plan eine der Dateien geaendert hat.
