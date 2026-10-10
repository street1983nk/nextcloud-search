"""Czech switched on and off over the band run, and the stock that never asks for it.

What this file proves, on a real tantivy directory and through the real band run
of :func:`findling.index.rebuild.rebuild_the_index` (CZ-02, ROADMAP SC2 and SC3
on code level, before the CI route of plans 30-06 and 30-07 shows the same on a
real Nextcloud):

* **The stock does not rebuild.** A directory of the thirteen field schema of
  1.3.0 to 1.4.2, whose marks say schema 2, is left as it is under the schema 3
  code: no band run, thirteen fields, the same marks, the same field plan. It
  goes on taking new documents through the real writer, and they are found the
  way they were found before the upgrade. The same holds for an extra language
  and for a 1.2.x directory of schema 1.
* **Switching cs on and off is a re-analysis.** The band run carries the stored
  body_de text into a fourteen field directory and lets the chain of every
  active language analyse it again, so cs arrives without a crawl and leaves
  without one, and the vector stock is not touched on either way.
* **The Czech chain on field level.** Stop words in both spellings leave no
  term, an inflection pair stays two terms (the documented limit, CZ-03), and
  the exception byt stays a content word.

**Why the proof of cs runs on de,cs and never on de,en,cs.** The English chain
folds accents in front of its stemmer (30-RESEARCH pitfall 5), so a Czech word
typed without its accent is already found through body_en. A case that kept en
in the set would be green with body_cs empty, and would prove nothing about it.

Accents appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

from __future__ import annotations

import gc
import hashlib
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tantivy import Document, Filter, Index, TextAnalyzerBuilder, Tokenizer

from conftest import CONSTITUENTS, open_schema_1_index, open_schema_2_index, write_wordlist
from findling.api.resources import field_plan_for
from findling.config import settings
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, expected_versions, fingerprint, open_index
from findling.index.rebuild import (
    NOTHING_TO_REBUILD,
    REBUILD_THROUGH,
    TARGET_MARK_FILE,
    _make_the_target_fit_this_code,
    rebuild_the_index,
)
from findling.index.schema import (
    FIELD_BODY_CS,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ES,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.stopwords_cs import CZECH_EXCEPTIONS
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.query.rewrite import LEGACY_PLAN, FieldPlan, build_query
from findling.store.repo import Store, open_store
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

LUCENE_ORIGINAL = Path(__file__).resolve().parent / "fixtures" / "lucene_cz_stopwords_10_5_2.txt"

# The field counts of the two layouts, written out rather than read from the
# schema module: the claim is about what lies on disk, and a count taken from
# build_schema() would move with it.
FIELDS_OF_SCHEMA_2 = 13
FIELDS_OF_SCHEMA_3 = 14

# The Czech document of the switch. The locative of smlouva, so the flat query
# smlouve reaches it only through a chain that folds, and German does not.
CZECH_BODY = "Smlouvě o nájmu"


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
    """How many fields the schema tantivy persisted in this directory carries."""
    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    return len(meta["schema"])


def _stage(index: Index, bodies: Mapping[int, str]) -> None:
    """Write documents the way the writer of 1.4.2 did: body_de stored, body_en beside it."""
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id, body in bodies.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.pdf")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.pdf")
        document.add_text(FIELD_EXT, "pdf")
        document.add_text(FIELD_BODY_DE, body)
        document.add_text(FIELD_BODY_EN, body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()


def _schema_2_volume(volume: Path, marks: Mapping[str, str], bodies: Mapping[int, str]) -> Store:
    """A live directory of schema 2 with these documents, and a state database with these marks.

    The marks are written after the seed, because the seed only fills what is
    missing: an installation of 1.4.2 has a database that already carries them.
    """
    digest = write_wordlist(volume)
    live = open_schema_2_index(volume / "index")
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
    """The file ids a search line finds through the search path, with this plan."""
    rewritten = build_query(index, text, plan=plan)
    assert rewritten.errors == []
    if rewritten.query is None:
        return set()
    searcher = index.searcher()
    hits = searcher.search(rewritten.query, limit=10).hits
    return {int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _score, address in hits}  # pyright: ignore[reportArgumentType]


def _found_in(index: Index, text: str, field: str) -> set[int]:
    """The file ids a search line finds in one field alone, analysed by its own chain."""
    searcher = index.searcher()
    hits = searcher.search(index.parse_query(text, [field]), limit=10).hits
    return {int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _score, address in hits}  # pyright: ignore[reportArgumentType]


def _vector_stock(volume: Path) -> Path:
    """A vector stock with one chunk of one document, closed again."""
    path = volume / "vectors.db"
    stock = open_vectors(path)
    stock.replace_chunks(
        1, [Chunk(ordinal=0, char_start=0, char_end=7, embedding=bytes(i % 256 for i in range(EMBEDDING_DIMENSIONS)))]
    )
    stock.close()
    return path


def _digest_of(path: Path) -> str:
    """One digest over the database and whatever sidecar files lie beside it."""
    digest = hashlib.sha256()
    for part in sorted(path.parent.glob(path.name + "*")):
        digest.update(part.name.encode())
        digest.update(part.read_bytes())
    return digest.hexdigest()


# -- the stock: a directory of 1.3.0 to 1.4.2 under the schema 3 code ----------


def test_a_schema_2_stock_under_schema_3_code_is_not_rebuilt(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _languages(monkeypatch, "de,en")
    store = _schema_2_volume(volume, {SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en"}, {1: "Der Mietvertrag gilt."})
    before = store.read_meta()

    verdict = _run(store)
    after = store.read_meta()
    store.close()
    plan = field_plan_for(after, _live())

    assert verdict == NOTHING_TO_REBUILD
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_2
    assert after == before
    assert after[SCHEMA_MARK] == "2"
    assert not (volume / "index.rebuild").exists()
    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE)


def test_a_schema_2_stock_goes_on_writing_through_the_real_writer(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real path after the upgrade: incremental indexing into the old directory.

    The writer of the schema 3 code adds body_cs only for a container that has
    cs switched on, so under de,en it never names the field the directory lacks.
    Mietverträgen is a form the German chain brings onto mietvertrag and the
    English chain does not, leased one the English chain brings onto lease and
    the German chain does not; the two counter probes say which field carries.
    """
    _languages(monkeypatch, "de,en")
    store = _schema_2_volume(volume, {SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en"}, {1: "Der Kaufvertrag gilt."})
    before = store.read_meta()
    index = _live()

    writer = IndexBatchWriter(index, directory=volume / "index", min_free_bytes=0)
    writer.add(
        IndexRecord(
            file_id=2,
            storage_id=1,
            name="Akte-2.pdf",
            title="Akte 2",
            path="/Akten/Akte-2.pdf",
            ext="pdf",
            body="Die Mietverträgen liegen vor. The flats were leased last year.",
            mtime=1_700_000_002,
        )
    )
    writer.flush()
    writer.close()
    index.reload()
    marks = store.read_meta()
    store.close()
    plan = field_plan_for(marks, index)

    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_2
    assert marks == before
    assert _found(index, "mietvertrag", plan) == {2}
    assert _found_in(index, "mietvertrag", FIELD_BODY_DE) == {2}
    assert _found_in(index, "mietvertrag", FIELD_BODY_EN) == set(), "body_de carries the German word"
    assert _found(index, "lease", plan) == {2}
    assert _found_in(index, "lease", FIELD_BODY_EN) == {2}
    assert _found_in(index, "lease", FIELD_BODY_DE) == set(), "body_en carries the English word"


def test_a_schema_2_stock_with_spanish_keeps_spanish_without_a_rebuild(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _languages(monkeypatch, "de,en,es")
    store = _schema_2_volume(volume, {SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en,es"}, {1: "El contrato rige."})

    verdict = _run(store)
    marks = store.read_meta()
    store.close()
    plan = field_plan_for(marks, _live())

    assert verdict == NOTHING_TO_REBUILD
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_2
    assert FIELD_BODY_ES in plan.fields
    assert FIELD_BODY_CS not in plan.fields


def test_a_1_2_stock_of_schema_1_is_not_rebuilt_and_keeps_the_legacy_plan(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """1.2.x straight to this code: schema mark 1 and no language mark at all."""
    _languages(monkeypatch, "de,en")
    digest = write_wordlist(volume)
    live = open_schema_1_index(volume / "index")
    _stage(live, {1: "Der Mietvertrag gilt."})
    del live
    gc.collect()
    stock_1_2 = {key: value for key, value in expected_versions(digest, "de,en").items() if key != LANGUAGES_MARK}
    stock_1_2[SCHEMA_MARK] = "1"
    store = open_store(volume / "state.db", meta=stock_1_2)
    assert LANGUAGES_MARK not in store.read_meta()

    verdict = _run(store)
    marks = store.read_meta()
    store.close()
    plan = field_plan_for(marks, _live())

    assert verdict == NOTHING_TO_REBUILD
    assert marks[SCHEMA_MARK] == "1"
    assert plan == LEGACY_PLAN


# -- cs on and off, over the band run -------------------------------------------


def _switch_cs_on(volume: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Store, str]:
    """A 1.4.2 stock on de,en with one Czech document, switched to de,cs and rebuilt."""
    _languages(monkeypatch, "cs,de")
    store = _schema_2_volume(
        volume, {SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en"}, {1: CZECH_BODY, 2: "Der Mietvertrag gilt."}
    )
    return store, _run(store)


def test_switching_cs_on_builds_fourteen_fields_and_finds_the_czech_word(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, verdict = _switch_cs_on(volume, monkeypatch)
    marks = store.read_meta()
    store.close()
    index = _live()
    plan = field_plan_for(marks, index)

    assert settings().languages == ("de", "cs")
    assert verdict == REBUILD_THROUGH
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_3
    assert marks[SCHEMA_MARK] == "3"
    assert marks[LANGUAGES_MARK] == "de,cs"
    assert FIELD_BODY_EN not in plan.fields
    assert FIELD_BODY_CS in plan.fields
    assert _found(index, "smlouve", plan) == {1}
    assert _found(index, "SMLOUVĚ", plan) == {1}


def test_after_switching_cs_on_body_de_alone_does_not_find_the_flat_czech_word(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The counter probe of the case above: without body_cs the flat spelling finds nothing."""
    store, verdict = _switch_cs_on(volume, monkeypatch)
    store.close()
    index = _live()

    assert verdict == REBUILD_THROUGH
    assert _found_in(index, "smlouve", FIELD_BODY_DE) == set()
    assert _found_in(index, "smlouve", FIELD_BODY_CS) == {1}


def test_switching_cs_off_rebuilds_again_and_leaves_body_cs_empty(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, verdict_on = _switch_cs_on(volume, monkeypatch)
    _languages(monkeypatch, "de,en")

    verdict_off = _run(store)
    marks = store.read_meta()
    store.close()
    index = _live()
    plan = field_plan_for(marks, index)

    assert verdict_on == REBUILD_THROUGH
    assert verdict_off == REBUILD_THROUGH
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_3
    assert marks[SCHEMA_MARK] == "3"
    assert marks[LANGUAGES_MARK] == "de,en"
    assert index.searcher().terms_with_prefix(FIELD_BODY_CS, "", limit=1) == []
    assert FIELD_BODY_CS not in plan.fields
    assert _found(index, "smlouve", plan) == {1}
    assert _found_in(index, "smlouve", FIELD_BODY_EN) == {1}


def test_no_switch_embeds_again_and_the_vector_stock_stays_as_it_was(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _languages(monkeypatch, "cs,de")
    stock = _vector_stock(volume)
    before = _digest_of(stock)
    store, verdict_on = _switch_cs_on(volume, monkeypatch)
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


def test_a_half_filled_target_of_the_schema_2_expectation_is_discarded(
    volume: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """T-30-22: a target filled by 1.4.2 code is not filled up by schema 3 code.

    The fingerprint in the target is the one of the same marks with schema 2,
    which is what the code before the upgrade wrote into a target it left half
    filled. Thirteen fields and two documents go in, fourteen fields and none
    come out, and the run of the whole band starts again from there.
    """
    _languages(monkeypatch, "cs,de")
    digest = write_wordlist(volume)
    languages = ",".join(settings().languages)
    wanted = fingerprint(expected_versions(digest, languages))
    old = fingerprint({**expected_versions(digest, languages), SCHEMA_MARK: "2"})
    assert old != wanted
    target = volume / "index.rebuild"
    half = open_schema_2_index(target)
    _stage(half, {1: CZECH_BODY, 2: "Der Mietvertrag gilt."})
    del half
    gc.collect()
    (target / TARGET_MARK_FILE).write_text(old, encoding="utf-8")
    assert _fields_on_disk(target) == FIELDS_OF_SCHEMA_2

    with caplog.at_level(logging.WARNING, logger="findling.index.rebuild"):
        _make_the_target_fit_this_code(target, CONSTITUENTS, wanted, dutch=None)
    fresh = open_index(target, CONSTITUENTS)
    fresh.reload()
    documents = fresh.searcher().num_docs
    del fresh
    gc.collect()

    assert _fields_on_disk(target) == FIELDS_OF_SCHEMA_3
    assert documents == 0
    assert (target / TARGET_MARK_FILE).read_text(encoding="utf-8") == wanted
    assert any("other version marks" in record.getMessage() for record in caplog.records)


def test_a_run_over_a_half_filled_schema_2_target_carries_everything_into_fourteen_fields(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, _unused = _switch_cs_on_over_a_stale_target(volume, monkeypatch)
    marks = store.read_meta()
    store.close()
    index = _live()

    assert marks[SCHEMA_MARK] == "3"
    assert _fields_on_disk(volume / "index") == FIELDS_OF_SCHEMA_3
    assert index.searcher().num_docs == 2
    assert _found_in(index, "smlouve", FIELD_BODY_CS) == {1}


def _switch_cs_on_over_a_stale_target(volume: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Store, str]:
    _languages(monkeypatch, "cs,de")
    store = _schema_2_volume(
        volume, {SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en"}, {1: CZECH_BODY, 2: "Der Mietvertrag gilt."}
    )
    target = volume / "index.rebuild"
    half = open_schema_2_index(target)
    _stage(half, {1: CZECH_BODY})
    del half
    gc.collect()
    digest = write_wordlist(volume)
    old = fingerprint({**expected_versions(digest, ",".join(settings().languages)), SCHEMA_MARK: "2"})
    (target / TARGET_MARK_FILE).write_text(old, encoding="utf-8")
    verdict = _run(store)
    assert verdict == REBUILD_THROUGH
    return store, verdict


# -- the Czech chain on field level, on de,cs ---------------------------------


def _czech_index(directory: Path, bodies: Mapping[int, str]) -> Index:
    """A fresh index of this code, written through the real writer under de,cs."""
    index = open_index(directory, CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=directory, min_free_bytes=0, languages=("de", "cs"))
    for file_id, body in bodies.items():
        writer.add(
            IndexRecord(
                file_id=file_id,
                storage_id=1,
                name=f"Akte-{file_id}.pdf",
                title=f"Akte {file_id}",
                path=f"/Akten/Akte-{file_id}.pdf",
                ext="pdf",
                body=body,
                mtime=1_700_000_000 + file_id,
            )
        )
    writer.flush()
    writer.close()
    index.reload()
    return index


def _fold(word: str) -> str:
    """The flat spelling of a word, by a chain that folds and does nothing else.

    Built here and not taken from czech_analyzer(), because that chain drops
    exactly the words this file asks about.
    """
    folding = TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase()).filter(Filter.ascii_fold()).build()
    (token,) = folding.analyze(word)
    return token


def _lucene_entries() -> Sequence[str]:
    """Every entry of the Lucene original whose flat spelling is not a named exception."""
    entries = [line.strip() for line in LUCENE_ORIGINAL.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [entry for entry in entries if _fold(entry) not in CZECH_EXCEPTIONS]


def test_czech_stop_words_in_both_spellings_leave_nothing_on_body_cs(tmp_path: Path) -> None:
    """Every entry of the original list, in its own and in its flat spelling.

    Two questions per spelling, because one of them alone is trivially green:
    the search line goes through the chain of the field and comes back empty
    for a stop word whatever the index holds, so the term dictionary is asked
    as well. The control document is found through a content word (positive
    control), which shows that the field is filled and the search reaches it.
    """
    entries = _lucene_entries()
    assert {"proč", "už", "jsem", "a", "nebo"} <= set(entries)
    index = _czech_index(tmp_path / "index", {1: "proč už jsem a nebo " + " ".join(entries), 2: "Pronájem kanceláře"})
    searcher = index.searcher()

    assert _found_in(index, "pronajem", FIELD_BODY_CS) == {2}
    assert searcher.doc_freq(FIELD_BODY_CS, "kancelare") == 1
    for entry in entries:
        for spelling in (entry, _fold(entry)):
            assert _found_in(index, spelling, FIELD_BODY_CS) == set(), spelling
            assert searcher.doc_freq(FIELD_BODY_CS, spelling) == 0, spelling


def test_an_inflection_pair_stays_two_terms_on_body_cs(tmp_path: Path) -> None:
    """CZ-03, the negative case: the documented limit of a chain without a stemmer, not a fault.

    smlouva and its locative smlouvě are two terms, so the one does not find
    the other. The accent pair of one form does land on one term: the locative
    is found through its flat spelling with a capital letter.
    """
    index = _czech_index(tmp_path / "index", {1: "smlouva", 2: "smlouvě"})

    assert _found_in(index, "smlouvě", FIELD_BODY_CS) == {2}
    assert 1 not in _found_in(index, "smlouvě", FIELD_BODY_CS)
    assert _found_in(index, "Smlouve", FIELD_BODY_CS) == {2}


def test_the_exception_byt_stays_a_content_word_on_body_cs(tmp_path: Path) -> None:
    """byt, flat, is the noun for a flat, and a lease for one has to be findable by it."""
    index = _czech_index(tmp_path / "index", {1: "Nájemní smlouva na byt"})

    assert "byt" in CZECH_EXCEPTIONS
    assert _found_in(index, "byt", FIELD_BODY_CS) == {1}
