"""Chinese switched on and off over the band run, and the stock that never asks for it.

The update promise of issue #53, in the maintainer's words: an update must not
force a reindex. This file proves it on a real tantivy directory and through the
real band run of :func:`findling.index.rebuild.rebuild_the_index`, the way
``tests/test_czech_switch.py`` proves it for the step to schema 3:

* **The stock does not rebuild.** A directory of the fourteen field schema of
  1.5.0 or later, whose marks say schema 3, is left as it is under the schema 4
  code: no band run, fourteen fields, the same marks, the same field plan. It
  goes on taking new documents through the real writer. The same holds with an
  extra language that the stock already carried (cs). The steps from schema 2
  and schema 1 are held by ``tests/test_czech_switch.py``, whose stock cases
  run under this code as well.
* **Switching zh on is a re-analysis.** The band run carries the stored body_de
  text into a directory of the running schema and lets the chain of every
  active language analyse it again, so zh arrives without a crawl, without OCR
  and without a new embedding, and leaves again the same way.
* **Before the switch the word is not found, after it it is.** The counter
  probe that makes the switch the cause and not the fixture.
"""

from __future__ import annotations

import gc
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

import pytest
from tantivy import Document, Index

from conftest import CONSTITUENTS, open_schema_3_index, write_wordlist
from findling.api.resources import field_plan_for
from findling.config import settings
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, expected_versions, open_index
from findling.index.rebuild import NOTHING_TO_REBUILD, REBUILD_THROUGH, rebuild_the_index
from findling.index.schema import (
    FIELD_BODY_CS,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ZH,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.query.rewrite import FieldPlan, build_query
from findling.store.repo import Store, open_store
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

# The field counts of the two layouts, written out rather than read from the
# schema module, for the reason tests/test_czech_switch.py gives.
FIELDS_OF_SCHEMA_3 = 14
FIELDS_OF_SCHEMA_4 = 15

COMMA = chr(0xFF0C)
FULL_STOP = chr(0x3002)

# The Chinese document of the switch and a German one beside it. 天氣 stands
# inside a longer run, so the German chain keeps it as part of one token and
# only body_zh reaches the word.
CHINESE_BODY = f"今天台北的天氣很好{COMMA}我們去開會{FULL_STOP}"
GERMAN_BODY = "Der Mietvertrag gilt."


@pytest.fixture(autouse=True)
def _cold_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every case resolves the settings itself, on an environment nobody else set."""
    for name in ("FINDLING_MIN_FREE_BYTES", "FINDLING_LANGUAGES"):
        monkeypatch.delenv(name, raising=False)
    settings.cache_clear()


def _languages(monkeypatch: pytest.MonkeyPatch, languages: str) -> None:
    monkeypatch.setenv("FINDLING_LANGUAGES", languages)
    settings.cache_clear()


def _fields_on_disk(directory: Path) -> int:
    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    return len(meta["schema"])


def _stage(index: Index, bodies: Mapping[int, str]) -> None:
    """Write documents the way the writer of schema 3 did on de,en: body_de stored, body_en beside it."""
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id, body in bodies.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.txt")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.txt")
        document.add_text(FIELD_EXT, "txt")
        document.add_text(FIELD_BODY_DE, body)
        document.add_text(FIELD_BODY_EN, body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()


def _schema_3_volume(volume: Path, marks: Mapping[str, str], bodies: Mapping[int, str]) -> Store:
    """A live directory of schema 3 with these documents, and a state database with these marks."""
    digest = write_wordlist(volume)
    live = open_schema_3_index(volume / "index")
    _stage(live, bodies)
    del live
    gc.collect()
    store = open_store(volume / "state.db", meta=expected_versions(digest, ",".join(settings().languages)))
    for key, value in marks.items():
        store.write_meta(key, value)
    return store


def _run(store: Store) -> str:
    """One run of the real band run, led by callbacks that do what a quiet poller does."""
    return rebuild_the_index(
        store,
        stand_down=lambda: True,
        arm=lambda: None,
        drop_read_side=lambda: None,
        let_read_side_open=lambda: None,
    )


def _live() -> Index:
    index = open_index(settings().index_dir, CONSTITUENTS)
    index.reload()
    return index


def _found(index: Index, text: str, plan: FieldPlan) -> set[int]:
    rewritten = build_query(index, text, plan=plan)
    assert rewritten.errors == []
    if rewritten.query is None:
        return set()
    searcher = index.searcher()
    hits = searcher.search(rewritten.query, limit=10).hits
    return {int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _score, address in hits}  # pyright: ignore[reportArgumentType]


def _vector_stock(volume: Path) -> Path:
    path = volume / "vectors.db"
    stock = open_vectors(path)
    stock.replace_chunks(
        1, [Chunk(ordinal=0, char_start=0, char_end=7, embedding=bytes(i % 256 for i in range(EMBEDDING_DIMENSIONS)))]
    )
    stock.close()
    return path


def _digest_of(path: Path) -> str:
    digest = hashlib.sha256()
    for part in sorted(path.parent.glob(path.name + "*")):
        digest.update(part.name.encode())
        digest.update(part.read_bytes())
    return digest.hexdigest()


# -- the stock: a schema 3 directory under the schema 4 code -------------------


def test_a_schema_3_stock_under_schema_4_code_is_not_rebuilt(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _languages(monkeypatch, "de,en")
    store = _schema_3_volume(volume, {SCHEMA_MARK: "3", LANGUAGES_MARK: "de,en"}, {1: GERMAN_BODY})
    before = store.read_meta()

    verdict = _run(store)
    after = store.read_meta()
    store.close()
    plan = field_plan_for(after, _live())

    assert verdict == NOTHING_TO_REBUILD
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_3
    assert after == before
    assert after[SCHEMA_MARK] == "3"
    assert not (volume / "index.rebuild").exists()
    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE)


def test_a_schema_3_stock_with_czech_keeps_czech_without_a_rebuild(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _languages(monkeypatch, "de,cs")
    store = _schema_3_volume(volume, {SCHEMA_MARK: "3", LANGUAGES_MARK: "de,cs"}, {1: "Smlouva platí."})

    verdict = _run(store)
    marks = store.read_meta()
    store.close()
    plan = field_plan_for(marks, _live())

    assert verdict == NOTHING_TO_REBUILD
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_3
    assert FIELD_BODY_CS in plan.fields
    assert FIELD_BODY_ZH not in plan.fields


def test_a_schema_3_stock_goes_on_writing_through_the_real_writer(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real path after the update: incremental indexing into the old directory.

    The writer of the schema 4 code adds body_zh only for a container that has
    zh switched on, so under de,en it never names the field the directory lacks,
    and a Chinese document goes in like any other.
    """
    _languages(monkeypatch, "de,en")
    store = _schema_3_volume(volume, {SCHEMA_MARK: "3", LANGUAGES_MARK: "de,en"}, {1: GERMAN_BODY})
    before = store.read_meta()
    index = _live()

    writer = IndexBatchWriter(index, directory=volume / "index", min_free_bytes=0)
    for file_id, body in ((2, "Die Mietverträgen liegen vor."), (3, CHINESE_BODY)):
        writer.add(
            IndexRecord(
                file_id=file_id,
                storage_id=1,
                name=f"Akte-{file_id}.txt",
                title=f"Akte {file_id}",
                path=f"/Akten/Akte-{file_id}.txt",
                ext="txt",
                body=body,
                mtime=1_700_000_000 + file_id,
            )
        )
    writer.flush()
    writer.close()
    index.reload()
    marks = store.read_meta()
    store.close()
    plan = field_plan_for(marks, index)

    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_3
    assert marks == before
    assert index.searcher().num_docs == 3
    # Mietvertrag of the stock document and Mietverträgen of the new one, both
    # through the German chain, as before the update.
    assert _found(index, "mietvertrag", plan) == {1, 2}


# -- zh on and off, over the band run -------------------------------------------


def _switch_zh_on(volume: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Store, str]:
    """A schema 3 stock on de,en with one Chinese and one German document, switched to de,en,zh."""
    _languages(monkeypatch, "zh,de,en")
    store = _schema_3_volume(volume, {SCHEMA_MARK: "3", LANGUAGES_MARK: "de,en"}, {1: CHINESE_BODY, 2: GERMAN_BODY})
    return store, _run(store)


def test_before_the_switch_the_chinese_word_is_not_found(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The counter probe of the case below: on the stock, the word inside the
    # run is reachable by no field, so a hit after the switch comes from body_zh.
    _languages(monkeypatch, "de,en")
    store = _schema_3_volume(volume, {SCHEMA_MARK: "3", LANGUAGES_MARK: "de,en"}, {1: CHINESE_BODY})
    marks = store.read_meta()
    store.close()
    index = _live()

    assert _found(index, "天氣", field_plan_for(marks, index)) == set()


def test_switching_zh_on_builds_fifteen_fields_and_finds_the_chinese_word(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, verdict = _switch_zh_on(volume, monkeypatch)
    marks = store.read_meta()
    store.close()
    index = _live()
    plan = field_plan_for(marks, index)

    assert settings().languages == ("de", "en", "zh")
    assert verdict == REBUILD_THROUGH
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_4
    assert marks[SCHEMA_MARK] == "4"
    assert marks[LANGUAGES_MARK] == "de,en,zh"
    assert FIELD_BODY_ZH in plan.fields
    assert plan.boosts[FIELD_BODY_ZH] == 0.6
    assert index.searcher().num_docs == 2
    assert _found(index, "天氣", plan) == {1}
    assert _found(index, "開會", plan) == {1}
    assert _found(index, "會議", plan) == set()
    assert _found(index, "台北 天氣", plan) == {1}
    # The German document is found the way it was found before.
    assert _found(index, "mietvertrag", plan) == {2}


def test_switching_zh_off_rebuilds_again_and_leaves_body_zh_empty(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, verdict_on = _switch_zh_on(volume, monkeypatch)
    _languages(monkeypatch, "de,en")

    verdict_off = _run(store)
    marks = store.read_meta()
    store.close()
    index = _live()
    plan = field_plan_for(marks, index)

    assert (verdict_on, verdict_off) == (REBUILD_THROUGH, REBUILD_THROUGH)
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_4
    assert marks[SCHEMA_MARK] == "4"
    assert marks[LANGUAGES_MARK] == "de,en"
    assert index.searcher().terms_with_prefix(FIELD_BODY_ZH, "", limit=1) == []
    assert FIELD_BODY_ZH not in plan.fields
    assert _found(index, "天氣", plan) == set()


def test_switching_zh_on_and_off_embeds_nothing_again(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _languages(monkeypatch, "zh,de,en")
    stock = _vector_stock(volume)
    before = _digest_of(stock)
    store, verdict_on = _switch_zh_on(volume, monkeypatch)
    after_on = _digest_of(stock)
    _languages(monkeypatch, "de,en")
    verdict_off = _run(store)
    store.close()
    after_off = _digest_of(stock)
    reopened = open_vectors(stock)
    chunks = reopened.chunk_count()
    reopened.close()

    assert (verdict_on, verdict_off) == (REBUILD_THROUGH, REBUILD_THROUGH)
    assert after_on == before
    assert after_off == before
    assert chunks == 1
