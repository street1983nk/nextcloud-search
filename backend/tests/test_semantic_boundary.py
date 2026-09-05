"""No second exit: the boundary of the semantic half, read out of the sources.

Pitfall 1 of the phase research says the vector branch gets built as a second
route, because that is the shortest way to a first result. The cost is not
performance and not tidiness. A second route would have to be given the
permission chain, the offset semantics and the parity test of phase 5 again, and
it would be believed without them: the parity job of plan 05-09 walks the one
search route, so a branch beside it is simply invisible to the job that is
supposed to prove criterion 2. That is why criterion 2 must be a property of the
structure and not of anybody's discipline.

**Why this file is a grep and not a functional test.** A functional test cannot
prove the absence of a route. It exercises what exists; a second route would sit
next to everything it touches and every single assertion would stay green. The
same holds for the number of places that ask the permission prefilter: two call
sites and three call sites behave identically in every scenario a test can
write down. So the assertions below read the sources, in the shape
``test_acl_prefilter.py`` invented for its own boundary and
``test_php_trust_boundary.py`` repeated against the PHP side.

**Grep hygiene is part of the job here, not a detail.** This phase writes a lot
of comments and docstrings that spell out the forbidden words in order to
explain them, and ``store/vectors.py`` alone mentions ``prefilter_visible`` five
times without calling it once. A counting assertion that trips over its own
explanatory text is an assertion somebody deletes, and they would be right to.
Every count below therefore runs over the code of a source with comments and
string literals removed, and two cases prove that the filter does what it says.

**What this file does not prove.** It says nothing about whether the one route
that exists filters correctly. That is the job of ``test_acl_prefilter.py``, of
the recheck on the PHP side and of the parity job in
``.github/workflows/integration.yml``.
"""

from __future__ import annotations

import ast
import io
import tokenize
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from findling.api.search import Candidate

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"
API_ROOT = PACKAGE_ROOT / "api"
SEARCH_SOURCE = PACKAGE_ROOT / "index" / "search.py"
FUSION_SOURCE = PACKAGE_ROOT / "index" / "fusion.py"
VECTORS_SOURCE = PACKAGE_ROOT / "store" / "vectors.py"
EMBED_ROOT = PACKAGE_ROOT / "embed"

# The name of the one permission question, and the name of the diagnosis helper
# that must never be reachable from a user answer (D-14).
PREFILTER = "prefilter_visible"
ORIGIN_MARK = "origins"

# A path carrying either word would be the second route of pitfall 1, announced
# by its own URL. Compared case insensitively, because a capital letter is not a
# defence.
FORBIDDEN_IN_A_ROUTE_PATH = ("semantic", "vector")

# The verbs a router method can carry. Anything else on a decorator is not a
# route declaration.
HTTP_VERBS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})

# Every route of the container, as of phase 6. The list is the anti-vacuity
# clause of the route scan below: a parser that stopped recognising decorators
# would find zero forbidden paths over zero routes and look perfectly healthy.
# Every plan that adds a route adds it here too, otherwise the clause stops
# being a ratchet.
KNOWN_ROUTES = ("/diagnose", "/rates", "/search", "/snippets", "/status")


# -- the hygienic readers --------------------------------------------------


def _significant_tokens(source: str) -> list[tokenize.TokenInfo]:
    """The names and operators of a source, comments and string literals gone.

    This is the whole of the grep hygiene, and it is done with the tokenizer
    rather than with a line filter on purpose. A line filter drops ``#`` lines
    and leaves docstrings standing, and docstrings are exactly where this phase
    spells out the forbidden words: five of the five mentions of
    ``prefilter_visible`` in ``store/vectors.py`` sit inside one.
    """
    return [
        token
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type in {tokenize.NAME, tokenize.OP}
    ]


def code_mentions(source: str, name: str) -> int:
    """How often an identifier stands in the *code* of a source.

    A mention is stronger than a call: it also catches an import, a getattr and
    a partial. Used where the assertion is "this module does not know the name
    at all".
    """
    return sum(1 for token in _significant_tokens(source) if token.type == tokenize.NAME and token.string == name)


def call_sites(source: str, name: str) -> int:
    """How often an identifier is *called* in the code of a source.

    A definition is not a call site, which is why ``def`` and ``class`` in front
    of the name end the match. Without that rule the declaration of a function
    would count against the budget of its callers.
    """
    tokens = _significant_tokens(source)
    counted = 0
    for index, token in enumerate(tokens):
        if token.type != tokenize.NAME or token.string != name:
            continue
        if index + 1 >= len(tokens) or tokens[index + 1].string != "(":
            continue
        if index and tokens[index - 1].string in {"def", "class"}:
            continue
        counted += 1
    return counted


def _called_name(node: ast.expr) -> str:
    """The bare name a call expression ends in, or an empty string."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def functions_calling(source: str, name: str) -> list[str]:
    """The names of the functions that call an identifier, sorted.

    The count alone would be satisfied by two call sites in the wrong two
    places, and "the candidate round and the snippet cut" is the part of the
    statement that carries meaning.
    """
    tree = ast.parse(source)
    callers: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if any(isinstance(inner, ast.Call) and _called_name(inner.func) == name for inner in ast.walk(node)):
            callers.append(node.name)
    return sorted(callers)


def route_paths(source: str) -> list[str]:
    """Every HTTP path one module declares, in declaration order."""
    tree = ast.parse(source)
    paths: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not decorator.args:
                continue
            called = decorator.func
            if not isinstance(called, ast.Attribute) or called.attr.lower() not in HTTP_VERBS:
                continue
            first = decorator.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                paths.append(first.value)
    return paths


def offending_routes(paths: Iterable[str]) -> list[str]:
    """Every path that announces a second route by its own name."""
    return [path for path in paths if any(word in path.lower() for word in FORBIDDEN_IN_A_ROUTE_PATH)]


def field_names(model: type[BaseModel]) -> set[str]:
    """The field names of a pydantic model, as a set."""
    return set(model.model_fields)


def _api_sources() -> list[tuple[str, str]]:
    """Every module of the API layer, as (file name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(API_ROOT.glob("*.py"))]


def _embed_sources() -> list[tuple[str, str]]:
    """Every module of the embedding package, as (file name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(EMBED_ROOT.glob("*.py"))]


# -- there is no second route ----------------------------------------------


def test_no_route_of_the_api_layer_announces_a_semantic_or_vector_path() -> None:
    declared = [(name, route_paths(source)) for name, source in _api_sources()]
    offenders = [f"{name}: {path}" for name, paths in declared for path in offending_routes(paths)]

    assert offenders == [], (
        "criterion 2 protects the search by having exactly one route through the permission chain; "
        f"a path of its own for the vector half would bypass the parity job of phase 5: {offenders}"
    )


def test_the_api_layer_declares_exactly_the_routes_this_gate_knows() -> None:
    # The anti-vacuity clause. Without it a parser that lost the ability to see
    # a decorator would report no offenders over no routes and stay green while
    # the second route sits right next to it.
    declared = sorted(path for _, source in _api_sources() for path in route_paths(source))

    assert declared == sorted(KNOWN_ROUTES), (
        "the route scan has to see every route the container declares, otherwise its silence means nothing; "
        f"seen {declared}, expected {sorted(KNOWN_ROUTES)}"
    )


_SECOND_ROUTE = '''"""A module that does what pitfall 1 describes."""

ROUTER = APIRouter()


@ROUTER.post("/semantic-search")
async def semantic_search(body: object) -> object:
    """The shortest way to a first result, and the end of criterion 2."""
    return body
'''


def test_the_route_scan_reports_a_second_route_when_there_is_one() -> None:
    # The red proof of the two assertions above. A gate whose only evidence is
    # "the current tree is clean" is green on the day somebody empties its body.
    paths = route_paths(_SECOND_ROUTE)

    assert paths == ["/semantic-search"], f"the scan has to find a declared route at all, it found {paths}"
    assert offending_routes(paths) == ["/semantic-search"], (
        "a path that carries the word semantic is the second route this gate exists for"
    )


# -- the permission prefilter is asked at two places, and at which two -------


def test_the_permission_prefilter_is_called_at_exactly_two_places() -> None:
    source = SEARCH_SOURCE.read_text(encoding="utf-8")

    counted = call_sites(source, PREFILTER)

    assert counted == 2, (
        "every place that asks who may see a document is a place that decides it, and a third one would be "
        f"green in every functional test; index/search.py calls {PREFILTER} {counted} times instead of twice"
    )


def test_the_two_call_sites_are_the_candidate_round_and_the_snippet_cut() -> None:
    # The count alone would be happy with two calls in two wrong places. The
    # candidate round asks through the one helper both halves of its loop share
    # (plan 06-06), so the enclosing function is _permit and not candidates.
    source = SEARCH_SOURCE.read_text(encoding="utf-8")

    callers = functions_calling(source, PREFILTER)

    assert callers == ["_permit", "snippets_for"], (
        "the two permitted places are the candidate round, through its one helper, and the snippet cut; "
        f"found {callers}"
    )


_THIRD_CALL_SITE = '''


def a_second_gate(store: object, uid: str, file_ids: list[int]) -> object:
    """Another place that decides what a user may see."""
    return store.prefilter_visible(uid, file_ids)
'''


def test_a_third_call_site_makes_the_count_red() -> None:
    # The red proof of the count, against the real source plus one function.
    grown = SEARCH_SOURCE.read_text(encoding="utf-8") + _THIRD_CALL_SITE

    assert call_sites(grown, PREFILTER) == 3, (
        "a third call site has to move the number, otherwise the assertion above is decoration"
    )
    assert functions_calling(grown, PREFILTER) == ["_permit", "a_second_gate", "snippets_for"], (
        "and it has to be named, so that the next reader does not have to search for it"
    )


def test_the_merge_the_embedder_and_the_vector_store_never_ask_who_may_see_a_document() -> None:
    # The other half of the same statement, and the reason the hygiene above
    # exists: all five mentions in store/vectors.py sit inside a docstring that
    # explains the direction the prefilter asks in.
    inspected = [
        ("index/fusion.py", FUSION_SOURCE.read_text(encoding="utf-8")),
        ("store/vectors.py", VECTORS_SOURCE.read_text(encoding="utf-8")),
        *((f"embed/{name}", source) for name, source in _embed_sources()),
    ]

    offenders = [name for name, source in inspected if code_mentions(source, PREFILTER)]

    assert offenders == [], (
        "the merge, the model and the vector store answer questions about numbers and text; a permission "
        f"question in any of them would be a second authority nobody asked for: {offenders}"
    )


# -- the answer of the search path stays three values -----------------------


def test_the_answer_model_of_the_search_path_carries_three_fields() -> None:
    names = field_names(Candidate)

    assert names == {"fileId", "score", "mtime"}, (
        "a candidate leaves the container before the permission recheck has run, so every additional field "
        f"is a statement about a document this user may not be allowed to know exists; found {sorted(names)}"
    )


class _CandidateWithAFourthField(Candidate):
    """The shape of the mistake: one more field, and nothing else changes."""

    path: str = ""


def test_a_fourth_field_on_the_answer_model_makes_the_gate_red() -> None:
    # The red proof of the assertion above, and it is not hypothetical: the
    # phase added a snippet path for hits only the vector branch found, and the
    # rank chunk of such a hit is exactly the kind of value somebody would be
    # tempted to hand along here.
    names = field_names(_CandidateWithAFourthField)

    assert names != {"fileId", "score", "mtime"}, "a fourth field has to move the set, otherwise the gate is blind"
    assert names == {"fileId", "score", "mtime", "path"}


# -- the origin mark stays in the admin diagnosis ---------------------------


def test_the_origin_mark_is_never_called_on_the_search_path() -> None:
    # D-14. ``fusion.origins`` says which half of the search contributed a
    # document, which is a statement about how well it matched. Plan 06-09 put
    # it on the admin diagnosis and nowhere else, and the two source files a
    # user answer travels through must not know the name at all.
    inspected = [
        ("api/search.py", (API_ROOT / "search.py").read_text(encoding="utf-8")),
        ("index/search.py", SEARCH_SOURCE.read_text(encoding="utf-8")),
    ]

    counted = [(name, code_mentions(source, ORIGIN_MARK)) for name, source in inspected]
    offenders = [f"{name}: {mentions} mentions" for name, mentions in counted if mentions]

    assert offenders == [], (
        "the origin of a hit is an admin answer and never part of a user answer, because it says how well a "
        f"document matched and Candidate is deliberately silent about that: {offenders}"
    )


# -- the hygiene of every count above ---------------------------------------


_HYGIENE_SAMPLE = '''"""A module whose docstring names prefilter_visible and origins on purpose.

It also talks about a semantic route and a vector route, because this is the
text that explains why neither may exist. Under a naive count that sentence is
indistinguishable from the thing it warns about.
"""

# prefilter_visible, prefilter_visible, origins: a comment line spelling out the
# forbidden words, which is what the comments of this phase actually look like.

MESSAGE = "prefilter_visible and origins in a string literal"


def only_one_real_call(store: object, uid: str, file_ids: list[int]) -> object:
    """Calls prefilter_visible once and names prefilter_visible twice in here."""
    return store.prefilter_visible(uid, file_ids)
'''


def test_a_comment_line_full_of_the_forbidden_words_moves_no_count() -> None:
    naive = _HYGIENE_SAMPLE.count(PREFILTER)

    assert naive >= 6, "the sample has to be far off under a naive count, otherwise it proves nothing"
    assert call_sites(_HYGIENE_SAMPLE, PREFILTER) == 1, (
        "a counting gate that trips over its own explanatory text is a gate somebody deletes, and this phase "
        f"writes exactly that text; the naive count says {naive}"
    )


def test_a_docstring_and_a_string_literal_full_of_the_forbidden_words_move_no_count() -> None:
    # The half a line filter would miss, and the half that matters in this tree:
    # store/vectors.py mentions the prefilter five times and every one of them
    # sits inside a docstring.
    assert code_mentions(_HYGIENE_SAMPLE, ORIGIN_MARK) == 0, (
        "the diagnosis helper is named three times in this sample and called nowhere; a filter that counted "
        "docstrings would report the explanation as the offence"
    )
    assert _HYGIENE_SAMPLE.count(ORIGIN_MARK) >= 3, "the sample has to name it often enough to be a real test"
