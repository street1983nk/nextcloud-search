"""POST /snippets: the only answer of this container that carries file content.

Which is why the claims here are mostly about who does not get one. A snippet is
document text, SRCH-02 says it is produced after the permission check and never
before, and this endpoint receives its file ids from another process. That the
caller only sends ids that survived its recheck is an assumption about a
different program running correctly, and an endpoint that relies on it is a
confused deputy: whoever reaches the proxy could ask for the content of any
document by its number.

The offsets are the second reason this file exists. The engine reports byte
ranges and the wire protocol promises characters, so the corpus puts two multi
byte characters in front of every match; without them both conventions produce
the same numbers and the assertion would be green either way.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus, body_of
from findling.api import resources
from findling.api import snippets as api_snippets
from findling.config import settings
from findling.embed.model import DIMENSIONS, EmbedOutcome
from findling.store.vectors import Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

TERM = "Kündigungsfrist"

# A line that occurs in no document of this corpus, which the floor assertion of
# the semantic case states rather than assumes.
PARAPHRASE = "Weltraumbahnhof"

# How much of the body the stored chunk of the semantic case covers. Short
# enough to be well under the excerpt cap, so the assertion is about the place
# of the cut and not about its length.
PASSAGE_CHARS = 30

# An odd file id, so alice may see it and bob may see it. Even ids belong to bob
# alone, which is what the prefilter claim below rests on.
ALICE_FILE = 1
BOB_FILE = 2


class _Model:
    """A stand-in that answers one vector, so no 118 MB artifact has to exist.

    The read side builds its model through ``resources.query_model``, and that
    is the seam these cases replace: constructing the real wrapper loads
    nothing, but a container without the artifact answers the honest
    ``embedding_unavailable`` verdict and the semantic path would never run.
    """

    def embed_query(self, text: str, *, may_load: bool = True) -> EmbedOutcome:
        return EmbedOutcome.ready([tuple(1.0 if index == 1 else 0.0 for index in range(DIMENSIONS))])


def _stock_one_chunk(root: Path) -> None:
    """Put one chunk over the opening of alice's document into the stock."""
    stock = open_vectors(root / "vectors.db")
    try:
        stock.replace_chunks(
            ALICE_FILE,
            [
                Chunk(
                    ordinal=0,
                    char_start=0,
                    char_end=PASSAGE_CHARS,
                    embedding=bytes(127 if index == 1 else 0 for index in range(DIMENSIONS)),
                )
            ],
        )
    finally:
        stock.close()


def _snippets(client: TestClient, headers: dict[str, str], **body: object) -> dict[str, Any]:
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": [ALICE_FILE], **body},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    return response.json()["snippets"]


def test_a_confirmed_file_id_gets_a_fragment(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _snippets(client, sign(indexed_volume.alice))

    assert set(answer) == {str(ALICE_FILE)}
    assert TERM.lower() in answer[str(ALICE_FILE)]["text"].lower()


def test_the_highlights_count_characters_and_not_bytes(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Two umlauts stand in front of the match, so a byte range would cut two
    # characters too far to the right and the slice would start mid word.
    snippet = _snippets(client, sign(indexed_volume.alice))[str(ALICE_FILE)]

    assert snippet["highlights"], "the term is in the text, so it must be marked"
    for start, end in snippet["highlights"]:
        assert 0 <= start < end <= len(snippet["text"])
    marked = snippet["text"][snippet["highlights"][0][0] : snippet["highlights"][0][1]]
    assert marked.lower().startswith("kündigung")


def test_fragment_has_no_markup(client: TestClient, sign: Sign, indexed_volume: Corpus) -> None:
    # The unified search UI renders the subline as Vue text interpolation, so a
    # tag would reach the user literally instead of being rendered. The engine
    # offers to_html() and this path never calls it.
    text = _snippets(client, sign(indexed_volume.alice))[str(ALICE_FILE)]["text"]

    assert "<" not in text
    assert ">" not in text


def test_a_file_id_the_prefilter_does_not_confirm_is_absent(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # alice asks for a document only bob may see, together with one of her own.
    # The missing key is the whole answer: there is no message that would tell a
    # caller whether that file exists.
    answer = _snippets(client, sign(indexed_volume.alice), fileIds=[ALICE_FILE, BOB_FILE])

    assert set(answer) == {str(ALICE_FILE)}


def test_a_user_without_a_permission_row_gets_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _snippets(client, sign(indexed_volume.carol), fileIds=[ALICE_FILE, BOB_FILE])

    assert answer == {}


def test_an_unknown_file_id_is_simply_absent(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _snippets(client, sign(indexed_volume.bob), fileIds=[999_999])

    assert answer == {}


def test_user_id_in_the_body_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": [1], "userId": "bob"},
        headers=sign("alice"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "user identity is taken from the AppAPI header only"


def test_more_than_a_hundred_file_ids_are_rejected(client: TestClient, sign: Sign) -> None:
    # The provider never asks for more than its display limit, so this only
    # bounds a caller that has gone wrong.
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": list(range(1, 102))},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_exactly_a_hundred_file_ids_are_accepted(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": list(range(1, 101))},
        headers=sign(indexed_volume.bob),
    )

    assert response.status_code == 200
    assert len(response.json()["snippets"]) == indexed_volume.documents


def test_missing_user_id_is_unauthorized(client: TestClient, sign: Sign) -> None:
    response = client.post("/snippets", json={"query": TERM, "fileIds": [1]}, headers=sign(""))

    assert response.status_code == 401


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.post("/snippets", json={"query": TERM, "fileIds": [1]})

    assert response.status_code == 401


def test_a_missing_index_answers_without_snippets(client: TestClient, sign: Sign, volume: Path) -> None:
    # A hit without an excerpt is still a hit: the subline falls back to the path
    # on the PHP side. An exception here would cost the user the whole search.
    assert not (volume / "index").exists()

    assert _snippets(client, sign("alice")) == {}


def test_the_artificial_delay_costs_time_and_changes_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The measuring aid of plan 02-14: it proves that the provider keeps its
    # 2.5 second wall clock and shows hits without an excerpt rather than none.
    # It may delay and nothing else, which is what the second assertion states.
    headers = sign(indexed_volume.bob)
    undelayed = _snippets(client, headers)

    monkeypatch.setenv("FINDLING_ARTIFICIAL_DELAY_MS", "150")
    started = time.monotonic()
    delayed = _snippets(client, headers)
    elapsed = time.monotonic() - started

    assert elapsed >= 0.15
    assert delayed == undelayed


def test_a_line_that_is_in_no_document_gets_no_fragment(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The floor under the case below. Without it a green semantic excerpt could
    # just mean that the line matched lexically after all.
    answer = _snippets(client, sign(indexed_volume.alice), query=PARAPHRASE)

    assert answer[str(ALICE_FILE)]["text"] == ""


def test_the_route_hands_the_raw_line_and_the_stock_to_the_second_path(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The wiring of this plan, end to end: the route passes the raw search line
    # and the vector stock, so a hit whose words do not occur in the document
    # still shows the passage that matched. The rewritten query could not do
    # this: a model needs words and a parsed query is not text any more.
    _stock_one_chunk(indexed_volume.root)
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _snippets(client, sign(indexed_volume.alice), query=PARAPHRASE)

    assert answer[str(ALICE_FILE)]["text"] == body_of(ALICE_FILE)[:PASSAGE_CHARS]
    assert answer[str(ALICE_FILE)]["highlights"] == []


def test_the_second_path_hangs_on_the_same_permission_check(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The chunk sits on an odd file id, so bob and alice may see it and carol
    # may not. A second excerpt path that produced text for carol would be the
    # confused deputy this endpoint exists to not be.
    _stock_one_chunk(indexed_volume.root)
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _snippets(client, sign(indexed_volume.carol), query=PARAPHRASE)

    assert answer == {}


def test_an_unusable_delay_is_ignored(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Same rule as every other variable this container reads: a value that cannot
    # be used falls back to the default instead of stopping anything.
    monkeypatch.setenv("FINDLING_ARTIFICIAL_DELAY_MS", "-1")

    assert _snippets(client, sign(indexed_volume.alice)) != {}


# -- the structured filter, and the one field that is not here -------------
#
# This call builds the very same query a second time, so the three fields that
# touch the query builder belong here as well. The fourth one does not, and the
# case that proves it is the most important one of this section: a sort field
# over here would be a field that does nothing today and something at the next
# rebuild.


def test_the_three_query_fields_are_accepted(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The corpus puts pdf on the odd file ids, and ALICE_FILE is one of them, so
    # the excerpt survives a filter the document belongs to.
    answer = _snippets(
        client,
        sign(indexed_volume.alice),
        types=["pdf"],
        since=1_700_000_000,
        until=1_700_000_100,
    )

    assert set(answer) == {str(ALICE_FILE)}


def test_a_sort_field_in_the_excerpt_body_is_refused(client: TestClient, sign: Sign) -> None:
    # The whole point of the asymmetry, held as an HTTP case. An excerpt call
    # asks about named fileIds and answers a mapping, so it has no order to
    # change; sort is therefore the one named entry in FIELDS_THAT_MAY_DIFFER of
    # tests/test_search_fields_lockstep.py, and extra="forbid" is what turns
    # that decision into a refusal instead of a field nobody reads.
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": [ALICE_FILE], "sort": "newest"},
        headers=sign("alice"),
    )

    assert response.status_code == 422
    assert "sort" in str(response.json()["detail"])


def test_an_empty_group_list_behaves_like_no_filter_at_all(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The shape the page sends while no chip is set. It has to be the answer of
    # a call without the field, or every unfiltered search would lose its
    # excerpts the day the page starts sending the field always.
    headers = sign(indexed_volume.alice)

    assert _snippets(client, headers, types=[]) == _snippets(client, headers)


def test_a_filter_the_document_does_not_match_still_leaves_it_its_excerpt(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The claim that says what the three fields are for, and what they are not
    # for. They travel so that both calls build one query out of one body; they
    # do not select documents, because this call selects none: it quotes the
    # ids the search already handed out and the PHP recheck already confirmed.
    # A second cut here would take a displayed hit its subline away and hand
    # back nothing for it, which is the outcome the whole two call protocol
    # exists to avoid. ALICE_FILE carries pdf, so "images" is a filter it is
    # plainly outside of.
    answer = _snippets(client, sign(indexed_volume.alice), types=["images"])

    assert set(answer) == {str(ALICE_FILE)}


def test_a_range_that_ends_before_it_starts_is_no_error_either(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Same reading as the case above, and the same reading the candidate call
    # gives an impossible period: this container does not judge whether a period
    # makes sense, and over here it does not judge the excerpt by it at all.
    answer = _snippets(client, sign(indexed_volume.alice), since=1_700_000_010, until=1_700_000_002)

    assert set(answer) == {str(ALICE_FILE)}


# ---------------------------------------------------------------------------
# The release switch on the second route with a ceiling (MEM-03)
# ---------------------------------------------------------------------------


class _LoadSwitchModel:
    """A stand-in that records what the excerpt cut let it spend.

    It gives the ``embedding_unavailable`` verdict whatever it is told, which
    is the state of a container that has let go of its engine: every document
    then takes the first excerpt path and the answer is the one this route
    gave before the second path existed (D-13, D-19).
    """

    def __init__(self) -> None:
        self.seen: list[bool] = []

    def embed_query(self, text: str, *, may_load: bool = True) -> EmbedOutcome:
        self.seen.append(may_load)
        return EmbedOutcome.unavailable()


def _watch_the_load_switch(monkeypatch: pytest.MonkeyPatch, seconds: str) -> _LoadSwitchModel:
    """Set the release span, forget the cached settings, and watch the model."""
    monkeypatch.setenv("FINDLING_EMBED_IDLE_RELEASE_SECONDS", seconds)
    settings.cache_clear()
    model = _LoadSwitchModel()
    monkeypatch.setattr(resources, "query_model", lambda: model)
    return model


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [("0", True), ("900", False)],
    ids=["release-off", "release-on"],
)
def test_the_excerpt_route_hands_the_model_what_the_release_switch_says(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
    seconds: str,
    expected: bool,
) -> None:
    # The same ceiling as the search route, in its own constant:
    # ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS is 1.5 as well, and the
    # unified search asks this route for every page of hits it shows.
    _stock_one_chunk(indexed_volume.root)
    model = _watch_the_load_switch(monkeypatch, seconds)

    api_snippets.excerpts(indexed_volume.alice, PARAPHRASE, [ALICE_FILE], False)

    assert model.seen == [expected]


def test_the_excerpt_under_the_release_is_the_one_a_container_without_a_model_cuts(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Counted in excerpts and never in errors (pitfall 4). A refused load
    # costs the semantic passage and never the answer.
    _stock_one_chunk(indexed_volume.root)
    _watch_the_load_switch(monkeypatch, "900")

    cut = api_snippets.excerpts(indexed_volume.alice, TERM, [ALICE_FILE], False)

    assert [text.file_id for text in cut] == [ALICE_FILE]
