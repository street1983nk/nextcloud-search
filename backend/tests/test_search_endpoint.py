"""POST /search: candidates, page marks, and the three things that must not leak.

This suite replaces the phase 1 file ``test_search_canary.py``. Its six claims
are all still here, they are just made against the new protocol: a body may not
name a user, a request without an identity gets 401, and the canary text stays
free of markup because the unified search UI interpolates the subline as text.

Three of the assertions below are about things that must be *absent*, and they
are the reason this file exists rather than a single happy path test:

* a candidate carries no name, no path and no text, because the answer leaves the
  container before the permission recheck has run,
* an ordinary search never sees the canary, because a diagnostic hit that mixes
  into real results is a diagnostic nobody can trust,
* a missing index answers empty and degraded rather than raising, because the
  unified search calls every provider in parallel and a throwing provider costs
  the user the whole search.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from socket import gethostname
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api import resources
from findling.api import search as api_search
from findling.api.search import CANARY_TITLE, Candidate, SearchRequest, build_canary_hits
from findling.config import SEARCH_MTIME_MAX, SEARCH_TYPE_GROUPS_MAX, settings
from findling.embed.model import EmbedOutcome
from findling.store.repo import open_store

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

# Spelled out as a literal rather than read from the implementation: a test that
# reads the constant it guards follows a rename instead of catching it. The same
# string is frozen on the PHP side as ExAppService::CANARY_TITLE.
CANARY = "findling-canary"

TERM = "Kündigungsfrist"

# Two words without an operator, which is the one shape of line that still
# builds a vector half: one word is answered by the word index alone and an
# operator asks for a precision the model cannot honour.
TWO_WORD_TERM = "Kündigungsfrist Vertrag"

# A line with an exclusion, so the operator rule holds the vector half back
# before any switch of this phase is ever read.
OPERATOR_TERM = "bescheid -frist"


def _search(client: TestClient, headers: dict[str, str], **body: object) -> dict[str, Any]:
    response = client.post("/search", json={"query": TERM, **body}, headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


def test_a_candidate_carries_no_name_no_path_and_no_text(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob))

    candidates = answer["candidates"]
    assert candidates, "the corpus matches this term, so this must not be empty"
    for candidate in candidates:
        assert set(candidate) == {"fileId", "score", "mtime"}


def test_the_candidate_model_has_no_text_field() -> None:
    # The structural half of pitfall 5. A functional test cannot see this: the
    # result the user finally gets is filtered further down the line and looks
    # correct whether or not the model carries a text field.
    assert set(Candidate.model_fields) == {"fileId", "score", "mtime"}


def test_the_answer_carries_the_page_marks(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob), limit=3)

    assert answer["hasMore"] is True
    assert answer["nextOffset"] > 0
    assert answer["degraded"] is False


def test_the_next_page_does_not_repeat_the_first_one(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    headers = sign(indexed_volume.bob)
    first = _search(client, headers, limit=3)
    second = _search(client, headers, limit=3, offset=first["nextOffset"])

    ids_of_first = {candidate["fileId"] for candidate in first["candidates"]}
    ids_of_second = {candidate["fileId"] for candidate in second["candidates"]}
    assert ids_of_first
    assert ids_of_second
    assert ids_of_first & ids_of_second == set()


def test_a_candidate_is_only_returned_to_a_user_the_prefilter_confirms(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.alice), limit=100)

    file_ids = {candidate["fileId"] for candidate in answer["candidates"]}
    assert file_ids, "alice sees the odd file ids"
    assert all(file_id % 2 for file_id in file_ids)


def test_a_user_without_a_permission_row_gets_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Half the security claim of this endpoint: an empty answer, not an
    # exception, and above all not the unfiltered list.
    answer = _search(client, sign(indexed_volume.carol), limit=100)

    assert answer["candidates"] == []


def test_title_only_leaves_the_document_text_out_of_the_question(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    headers = sign(indexed_volume.bob)

    assert _search(client, headers, titleOnly=False)["candidates"] != []
    assert _search(client, headers, titleOnly=True)["candidates"] == []


def test_user_id_in_the_body_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post("/search", json={"query": "contract", "userId": "bob"}, headers=sign("alice"))

    assert response.status_code == 400
    assert response.json()["detail"] == "user identity is taken from the AppAPI header only"


def test_an_unknown_field_that_is_not_an_identity_stays_a_422(client: TestClient, sign: Sign) -> None:
    # A misspelled field is a typo, not an attack. Answering it with the identity
    # message would send whoever made the typo hunting for a security problem.
    response = client.post("/search", json={"query": "contract", "limitt": 5}, headers=sign("alice"))

    assert response.status_code == 422
    assert "limitt" in str(response.json()["detail"])


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_out_of_range_is_rejected(client: TestClient, sign: Sign, limit: int) -> None:
    response = client.post("/search", json={"query": "contract", "limit": limit}, headers=sign("alice"))

    assert response.status_code == 422


def test_a_negative_offset_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post("/search", json={"query": "contract", "offset": -1}, headers=sign("alice"))

    assert response.status_code == 422


def test_an_offset_past_the_ceiling_is_rejected(client: TestClient, sign: Sign) -> None:
    # Security audit C1: an unbounded offset makes tantivy allocate
    # (limit+offset)*24 bytes and aborts the process with a Rust allocation
    # failure no Python handler can catch. The model rejects it before the engine
    # is ever entered, so this stays a 422 and not a dead container.
    from findling.config import SEARCH_OFFSET_MAX

    response = client.post(
        "/search",
        json={"query": "contract", "offset": SEARCH_OFFSET_MAX + 1},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_the_documented_offset_ceiling_is_accepted(client: TestClient, sign: Sign) -> None:
    # The boundary itself is a legitimate cursor and must answer normally.
    from findling.config import SEARCH_OFFSET_MAX

    response = client.post(
        "/search",
        json={"query": "contract", "offset": SEARCH_OFFSET_MAX},
        headers=sign("alice"),
    )

    assert response.status_code == 200


def test_an_overlong_query_is_rejected(client: TestClient, sign: Sign) -> None:
    # Security audit C2/M3: a megabyte-long query is seconds of CPU per request,
    # and the expansion runs against the live index. The length ceiling stops it
    # at the model.
    from findling.config import SEARCH_QUERY_MAX_CHARS

    response = client.post(
        "/search",
        json={"query": "a" * (SEARCH_QUERY_MAX_CHARS + 1)},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_missing_user_id_is_unauthorized(client: TestClient, sign: Sign) -> None:
    # A signed header without a user name: the signature checks out, the identity
    # does not exist. Answering with results here would be the actual bug.
    response = client.post("/search", json={"query": "contract"}, headers=sign(""))

    assert response.status_code == 401


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.post("/search", json={"query": "contract"})

    assert response.status_code == 401


def test_a_request_with_the_wrong_secret_is_unauthorized(client: TestClient, sign: Sign) -> None:
    headers = sign("alice")
    # base64 of "alice:not-the-secret": right shape, wrong credential.
    headers["AUTHORIZATION-APP-API"] = "YWxpY2U6bm90LXRoZS1zZWNyZXQ="

    response = client.post("/search", json={"query": "contract"}, headers=headers)

    assert response.status_code == 401


def test_the_canary_answers_its_own_name(client: TestClient, sign: Sign, indexed_volume: Corpus) -> None:
    response = client.post("/search", json={"query": CANARY}, headers=sign(indexed_volume.bob))

    assert response.status_code == 200
    canaries = [candidate for candidate in response.json()["candidates"] if candidate["fileId"] == 0]
    assert len(canaries) == 1
    assert canaries[0]["title"] == CANARY
    assert indexed_volume.bob in canaries[0]["snippet"]


def test_an_ordinary_search_never_sees_the_canary(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob), limit=100)

    assert all(candidate["fileId"] > 0 for candidate in answer["candidates"])


def test_a_term_that_merely_contains_the_canary_word_does_not_summon_it(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The comparison is exact, not "contains". Otherwise the canary colours every
    # search that happens to carry the word, and the one diagnostic this project
    # has stops being evidence of anything.
    answer = _search(client, sign(indexed_volume.bob), query=f"{CANARY} Vertrag")

    assert all(candidate["fileId"] > 0 for candidate in answer["candidates"])


def test_surrounding_space_still_reaches_the_canary(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob), query=f"  {CANARY}  ")

    assert [candidate["fileId"] for candidate in answer["candidates"]] == [0]


def test_a_missing_index_answers_empty_and_degraded(client: TestClient, sign: Sign, volume: Path) -> None:
    # A fresh container, deployed and not yet indexed. The unified search calls
    # every provider in parallel, so a throwing provider costs the user the whole
    # search rather than one result group.
    assert not (volume / "index").exists()

    answer = _search(client, sign("alice"))

    assert answer["candidates"] == []
    assert answer["degraded"] is True
    assert answer["hasMore"] is False


def test_the_canary_answers_even_without_an_index(client: TestClient, sign: Sign, volume: Path) -> None:
    # The diagnostic has to survive exactly the situation it is used in: somebody
    # is asking whether the container answers at all.
    assert not (volume / "index").exists()

    response = client.post("/search", json={"query": CANARY}, headers=sign("alice"))

    assert [candidate["fileId"] for candidate in response.json()["candidates"]] == [0]


def test_a_version_drift_is_degraded_but_still_answers(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Pitfall 14: the word list changed and the index did not, so queries are
    # tokenised differently than the documents were. Hits are still better than
    # silence, but the caller has to be told.
    store = open_store(indexed_volume.root / "state.db")
    store.write_meta("analyzer_version", "99")
    store.close()

    answer = _search(client, sign(indexed_volume.bob))

    assert answer["degraded"] is True
    assert answer["candidates"] != []


def test_canary_hit_carries_host_time_and_user() -> None:
    hits = build_canary_hits("alice")

    assert len(hits) == 1
    snippet = hits[0].snippet
    assert gethostname() in snippet
    assert "alice" in snippet
    # Read the timestamp back independently instead of rebuilding the format
    # string of the implementation: a shared pattern would prove nothing.
    stamp = snippet.split(" at ", maxsplit=1)[1].split(" for user ", maxsplit=1)[0]
    assert datetime.fromisoformat(stamp).tzinfo is not None


def test_canary_hit_carries_the_title_the_php_companion_accepts() -> None:
    # The companion resolves every hit with a file id above zero through the
    # user's own folder and drops whatever does not resolve. A hit with file id 0
    # never resolves, so this exact title is the only reason it reaches the user.
    hit = build_canary_hits("alice")[0]

    assert hit.fileId == 0
    assert hit.title == CANARY
    assert CANARY_TITLE == CANARY


def test_canary_snippet_has_no_markup() -> None:
    snippet = build_canary_hits("alice")[0].snippet

    # The unified search UI renders the subline as Vue text interpolation, so a
    # tag would reach the user literally instead of being rendered.
    assert "<" not in snippet
    assert ">" not in snippet


# -- the structured filter and the sort order of the result page -----------
#
# Four new fields, and the negative cases carry the weight. The route lives
# behind access_level USER, so the body is untrusted, and a value set that fell
# back quietly instead of refusing would be a second way into the query builder
# next to the search line.


def test_the_four_new_fields_are_accepted_together(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(
        client,
        sign(indexed_volume.bob),
        types=["pdf", "documents"],
        sort="newest",
        since=1_700_000_000,
        until=1_700_000_100,
    )

    assert answer["candidates"] != []


def test_a_body_without_the_new_fields_means_no_filter_and_relevance() -> None:
    # The defaults are part of the wire contract: the PHP side sends the fields
    # only when the user set one, so an absent field has to mean "no filter" and
    # "the order this container had before the phase".
    body = SearchRequest(query=TERM)

    assert body.types == []
    assert body.sort == "relevance"
    assert body.since is None
    assert body.until is None


def test_a_type_group_narrows_the_answer_to_that_group(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The corpus carries pdf on the odd file ids and docx on the even ones, so
    # the claim is visible in the numbers rather than in a count.
    answer = _search(client, sign(indexed_volume.bob), types=["pdf"], limit=100)

    found = [candidate["fileId"] for candidate in answer["candidates"]]
    assert found != []
    assert all(file_id % 2 == 1 for file_id in found)


def test_the_newest_order_answers_by_date_and_not_by_score(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Every document of the corpus carries a later mtime than the one before it,
    # so the highest file id has to come first. The score is 0.0 under a sort,
    # for the reason written at _ranked in findling.index.search.
    answer = _search(client, sign(indexed_volume.bob), sort="newest", limit=100)

    found = [candidate["mtime"] for candidate in answer["candidates"]]
    assert found == sorted(found, reverse=True)
    assert all(candidate["score"] == 0.0 for candidate in answer["candidates"])


def test_an_unknown_group_name_is_refused_and_never_ignored(client: TestClient, sign: Sign) -> None:
    # The division of labour, and it is worth naming because both halves look
    # like the other one's bug. Falling back quietly is what the PHP side does
    # with an address somebody edited: an unknown chip disappears and the page
    # answers. The container refuses, because only its own page calls it, so an
    # unknown group here is a defect in that page and not a user typing.
    response = client.post(
        "/search",
        json={"query": TERM, "types": ["videos"]},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_an_unknown_sort_name_is_refused(client: TestClient, sign: Sign) -> None:
    # The engine falls back to relevance for a name it does not know, on
    # purpose: a second exception down there would turn a typo into an HTTP 500.
    # That fallback is only safe because this refusal happens first.
    response = client.post(
        "/search",
        json={"query": TERM, "sort": "largest"},
        headers=sign("alice"),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("since", [-1, SEARCH_MTIME_MAX + 1])
def test_a_time_edge_outside_its_bounds_is_refused(client: TestClient, sign: Sign, since: int) -> None:
    response = client.post("/search", json={"query": TERM, "since": since}, headers=sign("alice"))

    assert response.status_code == 422


def test_the_documented_time_ceiling_is_accepted(client: TestClient, sign: Sign) -> None:
    # The boundary itself is a legitimate edge and must answer normally, the
    # same claim the offset ceiling makes one section up.
    response = client.post("/search", json={"query": TERM, "until": SEARCH_MTIME_MAX}, headers=sign("alice"))

    assert response.status_code == 200


def test_more_group_names_than_the_vocabulary_holds_are_refused(client: TestClient, sign: Sign) -> None:
    # A caller may repeat a name, and every arm grows the Should group the query
    # builder assembles, so the list is bounded on top of its value set.
    response = client.post(
        "/search",
        json={"query": TERM, "types": ["pdf"] * (SEARCH_TYPE_GROUPS_MAX + 1)},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_a_range_that_ends_before_it_starts_answers_empty_and_not_with_an_error(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The container does not judge whether a period makes sense. An impossible
    # range is a range with nothing in it, and "no data" is the honest answer;
    # a 422 here would make the page explain a decision its user made.
    answer = _search(client, sign(indexed_volume.bob), since=1_700_000_010, until=1_700_000_002)

    assert answer["candidates"] == []
    assert answer["hasMore"] is False


# ---------------------------------------------------------------------------
# The release switch on the route with the ceiling (MEM-03)
# ---------------------------------------------------------------------------


class _LoadSwitchModel:
    """A stand-in that records what the round let it spend.

    It answers the ``embedding_unavailable`` verdict whatever it is told,
    because the claim of this block is about what reaches the model and not
    about what comes back: the merge becomes the identity on the lexical list
    either way, so the page of these cases is the page of a container without
    a model (D-19).
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
def test_the_search_route_hands_the_model_what_the_release_switch_says(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
    seconds: str,
    expected: bool,
) -> None:
    # Off is the shipped behaviour and has to stay byte for byte what it was.
    # On is the answer to 2026-09-10: 1838.4 ms against a ceiling of 1500 ms,
    # and this route is the one that carries it.
    model = _watch_the_load_switch(monkeypatch, seconds)

    api_search.one_round(indexed_volume.bob, TWO_WORD_TERM, 20, 0, False)

    assert model.seen == [expected]


@pytest.mark.parametrize("seconds", ["0", "900"], ids=["release-off", "release-on"])
def test_a_line_that_asks_for_precision_asks_the_model_nothing_either_way(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
    seconds: str,
) -> None:
    # The operator rule sits above the switch and is untouched by it: no
    # vector half is built at all, so there is nothing to hand a switch to.
    model = _watch_the_load_switch(monkeypatch, seconds)

    api_search.one_round(indexed_volume.bob, OPERATOR_TERM, 20, 0, False)

    assert model.seen == []


def test_a_round_under_the_release_answers_the_way_a_container_without_a_model_does(
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Counted in hits and never in errors (pitfall 4): the route answers HTTP
    # 200 whatever happens, so a case that watched a failure count would be
    # green over an aborted call.
    off = _watch_the_load_switch(monkeypatch, "0")
    shipped = api_search.one_round(indexed_volume.bob, TWO_WORD_TERM, 20, 0, False)

    _watch_the_load_switch(monkeypatch, "900")
    released = api_search.one_round(indexed_volume.bob, TWO_WORD_TERM, 20, 0, False)

    assert off.seen == [True]
    assert [hit.fileId for hit in shipped.candidates] != []
    assert [hit.fileId for hit in released.candidates] == [hit.fileId for hit in shipped.candidates]
    assert released.degraded is False
