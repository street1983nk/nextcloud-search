"""The ACL prefilter: direction, declarativeness, and the name it carries.

The prefilter is the one piece of this project that is easiest to misunderstand
in a way that costs confidentiality. It looks like a permission check, it is not
one, and the tests below fix the three properties that keep it honest.

**Direction.** Given candidates, ask which of them are permitted. The inverse,
materialising every file a user can see, is the documented anti-pattern of the
app this one replaces: it grows with the instance instead of with the query.

**Declarative writes.** ``replace_acl`` deletes and re-inserts inside one
transaction, because the crawl transports the target state and not a delta. A
lost delta is wrong forever; a lost target state repairs itself with the next
delivery.

**The name.** ``prefilter_visible``, never ``check`` and never ``authorize``. The
last test in this file is a grep with a reason: once somebody believes the
backend already decided, the PHP recheck becomes an obvious thing to optimise
away, and that recheck is the only authority there is.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from findling.store import repo
from findling.store.repo import Store, open_store

PACKAGE_ROOT = Path(repo.__file__).resolve().parents[1]


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def test_replace_acl_writes_exactly_the_given_users(store: Store) -> None:
    store.replace_acl(1, ["anna", "bernd"])

    assert store.prefilter_visible("anna", [1]) == {1}
    assert store.prefilter_visible("bernd", [1]) == {1}
    assert store.prefilter_visible("carla", [1]) == set()


def test_replace_acl_is_declarative_and_drops_what_is_missing(store: Store) -> None:
    # The crawl hands over the target state. Bernd lost the share, and the second
    # delivery is all it takes for that to become true here.
    store.replace_acl(1, ["anna", "bernd"])
    store.replace_acl(1, ["anna"])

    assert store.prefilter_visible("anna", [1]) == {1}
    assert store.prefilter_visible("bernd", [1]) == set()


def test_replace_acl_with_an_empty_list_leaves_no_row(store: Store) -> None:
    store.replace_acl(1, ["anna"])
    store.replace_acl(1, [])

    assert store.prefilter_visible("anna", [1]) == set()
    assert store.acl_rows_per_document() == 0.0


def test_prefilter_visible_returns_only_the_permitted_candidates(store: Store) -> None:
    store.replace_acl(1, ["anna"])
    store.replace_acl(2, ["bernd"])
    store.replace_acl(3, ["anna", "bernd"])

    assert store.prefilter_visible("anna", [1, 2, 3, 4]) == {1, 3}


def test_prefilter_visible_of_a_user_without_rows_is_empty_and_not_an_error(store: Store) -> None:
    store.replace_acl(1, ["anna"])

    assert store.prefilter_visible("nobody", [1, 2, 3]) == set()


def test_prefilter_visible_with_no_candidates_does_not_touch_the_database(store: Store) -> None:
    statements: list[str] = []
    store.trace(statements.append)
    try:
        result = store.prefilter_visible("anna", [])
    finally:
        store.trace(None)

    assert result == set()
    assert statements == []


def test_prefilter_visible_bands_a_long_candidate_list(store: Store) -> None:
    # 5000 candidates fit into one IN list on this build, but the parameter limit
    # is a build option and this function must not depend on it.
    candidates = list(range(1, 5001))
    for file_id in candidates:
        if file_id % 7 == 0:
            store.replace_acl(file_id, ["anna"])

    statements: list[str] = []
    store.trace(statements.append)
    try:
        banded = store.prefilter_visible("anna", candidates)
    finally:
        store.trace(None)

    one_by_one = {file_id for file_id in candidates if store.prefilter_visible("anna", [file_id])}

    assert banded == one_by_one
    assert len(banded) == 714
    assert len(statements) == 5


def test_forget_acl_removes_every_row_of_one_file(store: Store) -> None:
    store.replace_acl(1, ["anna", "bernd", "carla"])
    store.replace_acl(2, ["anna"])

    removed = store.forget_acl(1)

    assert removed == 3
    assert store.prefilter_visible("anna", [1, 2]) == {2}


def test_acl_rows_per_document_is_the_status_figure(store: Store) -> None:
    store.replace_acl(1, ["anna", "bernd", "carla"])
    store.replace_acl(2, ["anna"])

    assert store.acl_rows_per_document() == 2.0


def test_the_prefilter_is_never_named_like_a_permission_check() -> None:
    source = (PACKAGE_ROOT / "store" / "repo.py").read_text(encoding="utf-8")

    assert "def prefilter_visible" in source
    assert "def check" not in source
    assert "def authorize" not in source


def test_the_package_never_claims_the_backend_already_checked() -> None:
    # The warning sign from the pitfall list, verbatim. Once this sentence stands
    # anywhere, somebody will read it as permission to drop the PHP recheck.
    offenders = [
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in sorted(PACKAGE_ROOT.rglob("*.py"))
        if "already checked" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
