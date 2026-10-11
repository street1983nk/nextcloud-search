"""The excerpt of a ZIP hit names the inner file (FMT-02, D-30-03, plan 31-09).

The text of a ZIP file is a row of sections, each one starting with
ARCHIVE_MEMBER_MARK (U+001C), the display name of the member and a line break
(plan 31-08). There is no schema field for the inner file (D-30-08): the excerpt
code finds the fragment in the stored body, looks for the last mark before the
first highlight and puts the name in front of the fragment.

Three things are held here beyond the name itself. The highlights still point at
the searched words once the prefix moved them (pitfall 14), so every test reads
the marked words out of the delivered text. The mark never reaches the user.
And the prefix exists for documents with the extension zip only: a text file
indexed before 1.5 may carry U+001C in its stored body, and a stray line of such
a file must never turn into the name of an inner file (finding 15).
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from tantivy import Document, Index, Query

from findling.config import ARCHIVE_MEMBER_MARK, SCHEMA_VERSION, settings
from findling.extract.dispatch import extract
from findling.extract.errors import State
from findling.index import search as index_search
from findling.index.open import open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
    FIELDS,
)
from findling.index.search import SnippetText, snippets_for
from findling.query.rewrite import build_query
from findling.store.repo import Store, open_store
from findling.store.vectors import BestChunk

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

OWNER = "owner"
MARK = ARCHIVE_MEMBER_MARK

TWO_MEMBERS = f"{MARK}a.txt\nerstes\n\n{MARK}innen/rechnung.txt\narchivquendel und mehr\n\n"
SAME_WORD_TWICE = f"{MARK}erste.txt\ndoppelquendel hier\n\n{MARK}zweite.txt\ndoppelquendel dort\n\n"
# What a text file indexed by 1.4.2 may have stored: U+001C in the middle of its
# own text, followed by something that looks like a name.
STOCK_WITH_MARK = f"vorher{MARK}name.txt\nnachher bestandquendel"
PLAIN = "Herr Müller hat die Grundstücksverkehrsgenehmigung im März beantragt."

CORPUS = (
    (10, "pack.zip", "zip", TWO_MEMBERS),
    (11, "doppelt.zip", "zip", SAME_WORD_TWICE),
    (12, "alt.txt", "txt", STOCK_WITH_MARK),
    (13, "alt.zip", "zip", STOCK_WITH_MARK),
    (14, "Antrag.pdf", "pdf", PLAIN),
)


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("archive-snippet-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id, name, ext, body in CORPUS:
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, name)
        document.add_text(FIELD_TITLE, name.rsplit(".", maxsplit=1)[0])
        document.add_text(FIELD_PATH, f"/Akten/{name}")
        document.add_text(FIELD_EXT, ext)
        document.add_text(FIELD_BODY_DE, body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    for file_id, _, _, _ in CORPUS:
        opened.replace_acl(file_id, [OWNER])
    yield opened
    opened.close()


def _query(index: Index, text: str) -> Query:
    rewritten = build_query(index, text)
    assert rewritten.query is not None
    return rewritten.query


def _one(index: Index, store: Store, text: str, file_id: int) -> SnippetText:
    found = snippets_for(index, store, OWNER, _query(index, text), [file_id])
    assert len(found) == 1
    return found[0]


def _marked(snippet: SnippetText) -> list[str]:
    return [snippet.text[start:end] for start, end in snippet.highlights]


def test_a_hit_in_the_second_member_names_the_second_member(index: Index, store: Store) -> None:
    snippet = _one(index, store, "archivquendel", 10)

    assert snippet.text.startswith("innen/rechnung.txt: ")
    assert _marked(snippet) == ["archivquendel"]


def test_a_hit_in_the_first_member_names_the_first_member(index: Index, store: Store) -> None:
    snippet = _one(index, store, "erstes", 10)

    assert snippet.text.startswith("a.txt: ")
    assert _marked(snippet) == ["erstes"]


def test_the_mark_never_reaches_the_delivered_text(index: Index, store: Store) -> None:
    for text, file_id in (("archivquendel", 10), ("erstes", 10), ("doppelquendel", 11), ("bestandquendel", 13)):
        snippet = _one(index, store, text, file_id)
        assert MARK not in snippet.text


def test_a_word_in_two_members_is_named_after_the_first_place(index: Index, store: Store) -> None:
    # The documented limit of a lookup without a schema field: the first place
    # in the stored text decides, so the subline may name a neighbour with the
    # same words (31-RESEARCH, pattern 4).
    snippet = _one(index, store, "doppelquendel", 11)

    assert snippet.text.startswith("erste.txt: ")
    assert set(_marked(snippet)) == {"doppelquendel"}


def test_a_text_file_with_the_mark_in_its_stock_text_gets_no_prefix(index: Index, store: Store) -> None:
    # Finding 15: indexed before this plan, U+001C still in the stored body.
    snippet = _one(index, store, "bestandquendel", 12)

    assert not snippet.text.startswith("name.txt: ")
    assert MARK not in snippet.text
    assert snippet.text == "vorhername.txt\nnachher bestandquendel"
    assert _marked(snippet) == ["bestandquendel"]


def test_the_same_stored_text_as_a_zip_file_gets_the_prefix(index: Index, store: Store) -> None:
    snippet = _one(index, store, "bestandquendel", 13)

    assert snippet.text.startswith("name.txt: ")
    assert _marked(snippet) == ["bestandquendel"]


def test_a_new_text_file_with_the_mark_is_found_without_it(tmp_path: Path) -> None:
    # Extraction and search in one go: what dispatch makes of a .txt carrying
    # U+001C is indexed and searched like any other text file.
    payload = f"Sehr geehrte Damen und Herren, vorher{MARK}name.txt\nnachher neuquendel im Schreiben.".encode()
    source = tmp_path / "brief.txt"
    source.write_bytes(payload)
    outcome = extract(str(source), "text/plain", len(payload))
    assert outcome.state is State.INDEXED
    assert MARK not in outcome.text

    built = open_index(tmp_path / "index", CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, 20)
    document.add_unsigned(FIELD_STORAGE_ID, 1)
    document.add_text(FIELD_NAME, "brief.txt")
    document.add_text(FIELD_TITLE, "brief")
    document.add_text(FIELD_PATH, "/Akten/brief.txt")
    document.add_text(FIELD_EXT, "txt")
    document.add_text(FIELD_BODY_DE, outcome.text)
    document.add_integer(FIELD_MTIME, 1_700_000_020)
    writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    built.reload()
    opened = open_store(tmp_path / "state.db")
    try:
        opened.replace_acl(20, [OWNER])
        found = snippets_for(built, opened, OWNER, _query(built, "neuquendel"), [20])
    finally:
        opened.close()

    assert len(found) == 1
    assert MARK not in found[0].text
    assert not found[0].text.startswith("name.txt: ")
    assert _marked(found[0]) == ["neuquendel"]


def test_a_document_without_a_mark_keeps_its_excerpt_byte_for_byte(index: Index, store: Store) -> None:
    # Both values were read from snippets_for before this plan changed it.
    one = _one(index, store, "Genehmigung", 14)
    two = _one(index, store, "Müller März", 14)

    assert one.text == "Herr Müller hat die Grundstücksverkehrsgenehmigung im März beantragt"
    assert one.highlights == [(20, 50)]
    assert two.text == one.text
    assert two.highlights == [(5, 11), (54, 58)]


def test_a_fragment_that_is_not_in_the_stored_text_has_no_name() -> None:
    # The generator cuts its fragment out of the stored text, so this does not
    # happen today; should a normalisation ever sit between the two, the excerpt
    # stays what it was instead of naming a wrong member or failing.
    assert index_search._member_of(TWO_MEMBERS, "nicht vorhanden", 0) is None


def test_a_stored_text_without_a_mark_has_no_name() -> None:
    assert index_search._member_of(PLAIN, "Grundstücksverkehrsgenehmigung", 0) is None


def test_the_semantic_passage_names_the_inner_file(index: Index) -> None:
    document = index_search._document_for(index, 10)
    assert document is not None
    start = TWO_MEMBERS.index("archivquendel")
    chunk = BestChunk(file_id=10, char_start=start, char_end=len(TWO_MEMBERS))

    passage = index_search._passage_of(document, chunk, limit=settings().snippet_chars)

    assert passage.startswith("innen/rechnung.txt: archivquendel")
    assert MARK not in passage


def test_the_semantic_passage_of_a_stock_text_file_gets_no_prefix(index: Index) -> None:
    document = index_search._document_for(index, 12)
    assert document is not None
    chunk = BestChunk(file_id=12, char_start=0, char_end=len(STOCK_WITH_MARK))

    passage = index_search._passage_of(document, chunk, limit=settings().snippet_chars)

    assert passage == "vorhername.txt\nnachher bestandquendel"


def test_a_search_for_the_name_of_an_inner_file_finds_the_archive(index: Index) -> None:
    searcher = index.searcher()
    hits = searcher.search(_query(index, "rechnung.txt"), 10).hits
    found = {searcher.doc(address).get_first(FIELD_FILE_ID) for _, address in hits}

    assert 10 in found
    # The negative control: the same query does not find a ZIP file whose
    # members are named differently.
    assert 11 not in found


def test_no_schema_field_and_no_schema_version_moved() -> None:
    # D-30-08: the inner file is read out of the stored text, never out of a
    # field of its own.
    assert SCHEMA_VERSION == 3
    assert FIELDS == (
        "file_id",
        "storage_id",
        "name",
        "title",
        "path",
        "ext",
        "body_de",
        "body_en",
        "body_es",
        "body_it",
        "body_nl",
        "body_pt",
        "body_cs",
        "mtime",
    )
