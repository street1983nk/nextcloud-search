"""Source probes and regression tests of the launch audit 1.5.0 (plan 36-12, HART-06).

The live half of the audit ran against the development instance on 8090 and is
recorded with commands and results in
``.planning/phases/36-haertung-und-store-einreichung-1-5-0/36-AUDIT.md``. What
stays here is the half a checkout can prove on its own, and one test per
finding of that report, named by its id.

Three probes read the sources in a way the tests of the building plans do not
(an independent pattern, not the one of the implementation):

* S4: every ``detail`` an extractor hands to a verdict is a code of the closed
  list of 36-WORTLAUT.md A3 or a class name, read out of the syntax tree rather
  than grepped, and both form checks refuse markup.
* S5: no code path of the reconcile deletes a storage without a walked round
  over a list that is neither empty nor short of a refused entry, as a syntax
  tree probe and with the sweep replaced by a recorder.
* S6: no extractor writes a file under a member name.

Only ASCII in this file, umlauts as escapes, like the other audit modules.
"""

from __future__ import annotations

import ast
import logging
import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileRow, GoneResult, Mount, MountResult, SliceResult
from findling.nc.queue import KIND_DELETE, CallResult, QueueStats
from findling.store import repo
from findling.store.repo import RECHECK_MARK, FileMeta, Store, open_store
from findling.worker import reconcile as reconcile_module
from findling.worker.reconcile import ROUND_WALKED, Reconcile

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "backend" / "src" / "findling"
EXTRACT = PACKAGE / "extract"
PHP_LIB = REPO / "php" / "lib"
RECONCILE_CONTROLLER = PHP_LIB / "Controller" / "ReconcileController.php"
QUEUE_CONTROLLER = PHP_LIB / "Controller" / "QueueController.php"
ADMIN_VIEW = PHP_LIB / "Service" / "AdminViewService.php"

# The closed list of detail codes, 36-WORTLAUT.md A3. Written out here and not
# imported: the probe asks whether the code matches the accepted wording, and
# a list read out of the code would agree with any code.
CLOSED_DETAILS = frozenset(
    {
        "zip_ratio",
        "zip_overlap",
        "zip_traversal",
        "package_entries",
        "xml_entities",
        "image_pixels",
        "mail_nesting",
        "cfb_cycle",
    }
)

# A class name in the form plan 29-06 stores: module.qualname, or a bare
# builtin class (RecursionError). Never a message.
CLASS_NAME = re.compile(r"(?:[a-z_][a-z0-9_]*\.)*[A-Z][A-Za-z0-9]*")


# -- S4: the detail codes ---------------------------------------------------------


def _module_strings(tree: ast.Module) -> dict[str, str]:
    """Module level names bound to one string literal (``X: Final = "..."`` or ``X = "..."``)."""
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = node.value
            name = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = node.value
            name = node.targets[0].id
        else:
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            found[name] = value.value
    return found


def _detail_arguments(tree: ast.Module) -> Iterator[ast.expr]:
    """Every expression handed to a verdict as its detail, by keyword or by position."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "detail":
                yield keyword.value
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"skipped", "failed"} and len(node.args) > 1:
            yield node.args[1]


def _overlimit_codes(tree: ast.Module, strings: dict[str, str]) -> list[str | None]:
    """The first argument of every ``OverLimit(...)`` call, resolved; None stands for no signature."""
    codes: list[str | None] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "OverLimit":
            if not node.args:
                codes.append(None)
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                codes.append(first.value)
            elif isinstance(first, ast.Name) and first.id in strings:
                codes.append(strings[first.id])
            else:
                codes.append("<unresolved>")
    return codes


def _judge_detail(value: ast.expr, strings: dict[str, str], module: str) -> str | None:
    """None when the expression is a code of the closed list or a class name, else the reason."""
    if isinstance(value, ast.Constant):
        if value.value is None:
            return None
        if isinstance(value.value, str) and (value.value in CLOSED_DETAILS or CLASS_NAME.fullmatch(value.value)):
            return None
        return f"literal {value.value!r}"
    if isinstance(value, ast.Name):
        if value.id in strings:
            text = strings[value.id]
            return None if text in CLOSED_DETAILS or CLASS_NAME.fullmatch(text) else f"{value.id} = {text!r}"
        if value.id == "detail" and module == "errors.py":
            return None  # the parameter of the two class methods, and the class name of from_exception
        return f"unresolved name {value.id}"
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "_class_of":
        return None
    if isinstance(value, ast.Attribute) and value.attr == "signature" and module == "archive.py":
        return None  # the code an OverLimit carries; its sources are judged separately
    return f"expression {ast.unparse(value)}"


def _detail_findings(source: str, module: str) -> list[str]:
    tree = ast.parse(source)
    strings = _module_strings(tree)
    findings = [
        f"{module}:{value.lineno}: {reason}"
        for value in _detail_arguments(tree)
        if (reason := _judge_detail(value, strings, module)) is not None
    ]
    findings.extend(
        f"{module}: OverLimit({code!r})"
        for code in _overlimit_codes(tree, strings)
        if code is not None and code not in CLOSED_DETAILS
    )
    return findings


def test_every_detail_of_an_extractor_is_a_closed_code_or_a_class_name() -> None:
    """S4: nothing but the eight codes of A3 and class names reaches file_errors."""
    findings: list[str] = []
    seen = 0
    for path in sorted(EXTRACT.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        seen += sum(1 for _ in _detail_arguments(ast.parse(source)))
        findings.extend(_detail_findings(source, path.name))
    assert findings == []
    # The probe saw the call sites it is about: every code of the list and the
    # class name branches (a probe that reads nothing is green for nothing).
    assert seen >= 20
    every_literal = "\n".join(path.read_text(encoding="utf-8") for path in EXTRACT.glob("*.py"))
    for code in CLOSED_DETAILS:
        assert f'"{code}"' in every_literal, code


def test_the_detail_probe_reports_a_message_a_name_and_a_foreign_code() -> None:
    """Positive control of S4: the three ways a detail can go wrong are each reported."""
    source = (
        "_BAD: Final = 'see /home/alice/x.txt'\n"
        "def f(error, info):\n"
        "    a = ExtractionOutcome.failed(Reason.CORRUPT, detail=str(error))\n"
        "    b = ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail=info.filename)\n"
        "    c = ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail='zip_bomb')\n"
        "    d = ExtractionOutcome.failed(Reason.CORRUPT, detail=_BAD)\n"
        "    raise OverLimit('member name')\n"
    )
    findings = _detail_findings(source, "archive.py")
    assert len(findings) == 5, findings


def test_from_exception_builds_its_detail_out_of_the_type_alone() -> None:
    """S4: the one detail that is a variable in errors.py is the class, never the message."""
    source = (EXTRACT / "errors.py").read_text(encoding="utf-8")
    start = source.index("def from_exception(")
    end = source.index("\n\n\n", start)
    assert 'detail = f"{raised.__module__}.{raised.__qualname__}"' in source[start:end]
    assert "str(error)" not in source[start:end]
    body = (EXTRACT / "image.py").read_text(encoding="utf-8")
    start = body.index("def _class_of(")
    end = body.index("\ndef ", start + 1)
    assert "__qualname__" in body[start:end]
    assert "str(error)" not in body[start:end]


def _php_pattern(source: str, name: str) -> str:
    match = re.search(rf"const {name} = '([^']+)';", source)
    assert match is not None, name
    return match.group(1)


def _pcre(pattern: str) -> re.Pattern[str]:
    """A PHP preg pattern of the form /.../flags as a Python pattern with PCRE's dollar.

    Without the D flag PCRE lets ``$`` match before a final newline, and so does
    Python's ``$``; with D it matches at the very end only, which is ``\\Z``.
    """
    delimiter = pattern[0]
    body, flags = pattern[1:].rsplit(delimiter, 1)
    if "D" in flags and body.endswith("$"):
        body = body[:-1] + r"\Z"
    return re.compile(body)


def test_markup_in_a_detail_is_refused_by_both_form_checks() -> None:
    """S4, XSS probe: an errorClass carrying markup passes neither the store nor the companion."""
    php = _pcre(_php_pattern(ADMIN_VIEW.read_text(encoding="utf-8"), "ERROR_CLASS_PATTERN"))
    python_shape = repo._ERROR_CLASS_SHAPE  # the form check itself is the subject
    for hostile in ("<img src=x onerror=alert(1)>", "image_pixels<script>", "../x", "a b", ""):
        assert python_shape.fullmatch(hostile) is None, hostile
        assert php.search(hostile) is None, hostile
    for good in ("image_pixels", "findling.extract.image.HeaderEstimate", "RecursionError"):
        assert python_shape.fullmatch(good) is not None
        assert php.search(good) is not None


# -- L-36-01: the dollar of the PHP form checks ----------------------------------------

_PHP_LITERAL = re.compile(r"'(/\^[^'\n]*\$/[a-zA-Z]*)'")


def _anchored_without_d(source: str) -> list[str]:
    """Every /^...$/ literal of a PHP source that lacks the D flag."""
    return [literal for literal in _PHP_LITERAL.findall(source) if "D" not in literal.rsplit("/", 1)[1]]


def test_every_anchored_php_form_check_ends_at_the_very_end() -> None:
    """L-36-01: a form check anchored with $ carries D, so "14\\n" is not 14.

    Found live: ``?similar=14%0A`` opened the similar view of file 14 although
    the docblock of PageController::similarId names only canonical numbers.
    Harmless in that place, but the five checks of this kind guard values that
    cross a trust boundary, and the companion spells the rule with D elsewhere.
    Fixed in plan 36-12; after the fix the same address renders the start page.
    """
    findings: dict[str, list[str]] = {}
    anchored = 0
    for path in sorted(PHP_LIB.rglob("*.php")):
        source = path.read_text(encoding="utf-8")
        anchored += len(_PHP_LITERAL.findall(source))
        bad = _anchored_without_d(source)
        if bad:
            findings[str(path.relative_to(REPO))] = bad
    assert findings == {}
    # The five fixed checks and the four that carried D before: a probe that
    # finds no literal at all would be green for nothing.
    assert anchored >= 9
    php = _pcre(_php_pattern(ADMIN_VIEW.read_text(encoding="utf-8"), "ERROR_CLASS_PATTERN"))
    assert php.search("image_pixels\n") is None


def test_the_dollar_probe_tells_the_two_spellings_apart() -> None:
    """Positive control of L-36-01: a literal without D is reported, one with D is not."""
    source = "preg_match('/^[0-9]{3}$/', $a); preg_match('/^[0-9]{3}$/D', $b); $c = '/^x$/i';"
    assert _anchored_without_d(source) == ["/^[0-9]{3}$/", "/^x$/i"]
    assert _pcre("/^[0-9]{3}$/").search("123\n") is not None
    assert _pcre("/^[0-9]{3}$/D").search("123\n") is None


# -- L-36-02: canonical numbers at the container routes --------------------------------


def _php_method(source: str, signature: str) -> str:
    start = source.index(signature)
    tail = source[start:]
    after = re.search(r"\n\t(?:public|private|protected) ", tail[1:])
    return tail if after is None else tail[: after.start() + 1]


@pytest.mark.xfail(strict=True, reason="L-36-02")
def test_the_id_parsers_of_the_container_routes_take_canonical_numbers_only() -> None:
    """L-36-02: a digit string is an id only if it reads back as itself.

    Found live: ``ids[0]=12345678901234567890`` at ``GET /storages/gone``
    answered 200 with ``"gone": [9223372036854775807]``, because the cast
    clamps; ``014`` read as 14. The container intersects the answer with what it
    asked and never sends such a value, so nothing reached the index. The same
    parser shape stands in QueueController::positiveId.
    """
    for path, signature in (
        (RECONCILE_CONTROLLER, "private function storageIdList("),
        (QUEUE_CONTROLLER, "private function positiveId("),
    ):
        body = _php_method(path.read_text(encoding="utf-8"), signature)
        assert "ctype_digit(" in body, path.name
        assert "(string)$id === $value" in body, path.name


# -- S5: no deletion out of an unsure position --------------------------------------


def _run_once_tree() -> ast.AsyncFunctionDef:
    tree = ast.parse(Path(reconcile_module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_once":
            return node
    raise AssertionError("run_once not found")


def _calls_to(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        call
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == name
    ]


def test_the_sweep_is_reached_only_behind_a_full_walk_of_a_clean_list() -> None:
    """S5, syntax tree: one call of the sweep, under the guard, after the walk loop."""
    run_once = _run_once_tree()
    assert len(_calls_to(run_once, "_sweep_vanished")) == 1
    guarded = [node for node in run_once.body if isinstance(node, ast.If) and _calls_to(node, "_sweep_vanished")]
    assert len(guarded) == 1
    assert ast.unparse(guarded[0].test) == "found.mounts and (not found.discarded)"
    loop = next(node for node in run_once.body if isinstance(node, ast.For))
    assert ast.unparse(loop.iter) == "found.mounts"
    # An early end of a mount returns out of the loop, so the guard is behind
    # nothing but a complete walk.
    assert any(isinstance(node, ast.Return) for node in ast.walk(loop))
    assert run_once.body.index(loop) < run_once.body.index(guarded[0])
    unavailable = next(
        node for node in run_once.body if isinstance(node, ast.If) and ast.unparse(node.test) == "found.unavailable"
    )
    assert run_once.body.index(unavailable) < run_once.body.index(loop)


def test_delete_orders_of_the_reconcile_leave_through_one_place() -> None:
    """S5: KIND_DELETE is handed to the queue in _hand_over only; the sweep calls nothing else that deletes."""
    tree = ast.parse(Path(reconcile_module.__file__).read_text(encoding="utf-8"))
    users = {
        function.name
        for function in ast.walk(tree)
        if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef)
        for name in ast.walk(function)
        if isinstance(name, ast.Name) and name.id == "KIND_DELETE"
    }
    assert users == {"_hand_over"}
    sweep = next(
        node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef) and node.name == "_sweep_vanished"
    )
    assert not _calls_to(sweep, "requeue")
    assert len(_calls_to(sweep, "_hand_over")) == 1


CONTROL = 3


class _Queue:
    def __init__(self) -> None:
        self.requeues: list[tuple[list[int], str]] = []

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> CallResult:
        self.requeues.append((list(file_ids), kind))
        return CallResult(ok=True, count=len(file_ids))

    async def stats(self) -> QueueStats:
        return QueueStats(scheduled=0)


class _Files:
    def __init__(self, store: Store, listed: Sequence[int]) -> None:
        self._store = store
        self.listed = list(listed)
        self.discarded = 0
        self.unavailable = False
        self.page_unavailable = False

    async def mounts(self) -> MountResult:
        if self.unavailable:
            return MountResult(unavailable=True)
        mounts = tuple(Mount(storage_id=s, root_id=s * 10, overridden_root=s * 10 + 1) for s in self.listed)
        return MountResult(mounts=mounts, discarded=self.discarded)

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        del root, after, limit
        if self.page_unavailable:
            return SliceResult(unavailable=True)
        rows = tuple(
            FileRow(file_id=file_id, etag=f"e{file_id}", size=1024, mtime=1_700_000_000, mime="application/pdf")
            for file_id in self._store.living_file_ids(storage)
        )
        return SliceResult(files=rows, final=True)

    async def gone_storages(self, ids: Sequence[int]) -> GoneResult | None:
        return GoneResult(gone=frozenset(ids))


def _record(store: Store, storage_id: int, file_ids: Sequence[int]) -> None:
    for file_id in file_ids:
        meta = FileMeta(
            storage_id=storage_id,
            root_id=storage_id * 10,
            path=f"files/akte-{file_id}.pdf",
            title=f"akte-{file_id}.pdf",
            mime="application/pdf",
            size=1024,
            mtime=1_700_000_000,
            etag=f"e{file_id}",
        )
        store.record(file_id, meta, "indexed")


def _round(store: Store, files: _Files, queue: _Queue) -> Reconcile:
    return Reconcile(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", files),
        queue_factory=lambda nc: cast("Any", queue),
        slice_size=500,
        quiet_max=100,
        hour=2,
        min_interval_hours=24,
        pause_seconds=0.0,
        tick_seconds=0.01,
        clock=lambda: 1_800_000_000.0,
        hour_of=lambda: 2,
    )


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    opened.write_meta(RECHECK_MARK, "done")
    _record(opened, CONTROL, (1, 2))
    _record(opened, 14, (10, 11))
    yield opened
    opened.close()


@pytest.mark.parametrize("position", ["walked", "empty", "discarded", "unavailable", "ended_early"])
async def test_the_sweep_runs_for_a_walked_round_only(
    store: Store, monkeypatch: pytest.MonkeyPatch, position: str
) -> None:
    """S5 with the sweep replaced: only the walked round over a clean list reaches it.

    The positive control is the first parameter: the same store and the same
    deleted storage, a clean round, and the recorder is called exactly once.
    """
    reached: list[frozenset[int]] = []

    async def recorder(self: Reconcile, store: Store, files: object, queue: object, listed: frozenset[int]) -> None:
        del self, store, files, queue
        reached.append(listed)

    monkeypatch.setattr(Reconcile, "_sweep_vanished", recorder)
    files = _Files(store, [CONTROL])
    if position == "empty":
        files.listed = []
    elif position == "discarded":
        files.discarded = 1
    elif position == "unavailable":
        files.unavailable = True
    elif position == "ended_early":
        files.page_unavailable = True
    queue = _Queue()

    result = await _round(store, files, queue).run_once()

    if position == "walked":
        assert result.state == ROUND_WALKED
        assert reached == [frozenset({CONTROL})]
    else:
        assert reached == []
    assert [kind for _, kind in queue.requeues if kind == KIND_DELETE] == []


# -- L-36-03: the sweep line stays short ---------------------------------------------


@pytest.mark.xfail(strict=True, reason="L-36-03")
async def test_the_sweep_line_names_a_bounded_number_of_storages(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    """L-36-03: 300 removed storages are counted in full and named only in part.

    Found live (P3): a round with 300 deleted storages wrote one line with all
    300 ids, and a stamped storage is named again in every due round for 30
    days. The counters stay exact; the lists end after a fixed number.
    """
    for offset in range(300):
        _record(store, 900_001 + offset, (95_100_000 + offset,))
    files = _Files(store, [CONTROL])
    queue = _Queue()

    with caplog.at_level(logging.INFO, logger="findling.worker.reconcile"):
        await _round(store, files, queue).run_once()

    lines = [record.getMessage() for record in caplog.records if "storage sweep" in record.getMessage()]
    assert len(lines) == 1
    assert "removed=301" in lines[0]
    named = re.findall(r"\b9\d{5}\b|\b14\b", lines[0].split("removed=301", 1)[1])
    assert 0 < len(named) <= 20
    assert "281 more" in lines[0]
    assert len(lines[0]) < 400
    assert getattr(reconcile_module, "SWEEP_LOG_STORAGES", None) == 20


# -- S6: no member name becomes a path ---------------------------------------------


def test_no_extractor_unpacks_or_writes_under_a_member_name() -> None:
    """S6, Zip Slip: no extractall/extract, and the one write sink is a numbered scratch file."""
    writes: list[str] = []
    for path in sorted(EXTRACT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            assert node.func.attr not in {"extractall", "extract"}, f"{path.name}:{node.lineno}"
            if node.func.attr == "open" and any(
                isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "w" in arg.value for arg in node.args
            ):
                writes.append(f"{path.name}:{ast.unparse(node.func.value)}")
    assert writes == ["archive.py:member"]

    archive = (EXTRACT / "archive.py").read_text(encoding="utf-8")
    tree = ast.parse(archive)
    scratch = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "next_scratch")
    names = {node.attr for node in ast.walk(scratch) if isinstance(node, ast.Attribute)}
    names |= {node.id for node in ast.walk(scratch) if isinstance(node, ast.Name)}
    assert names.isdisjoint({"filename", "orig_filename", "info", "name"})
    reader = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_read_member")
    assignments = [
        ast.unparse(node.value)
        for node in ast.walk(reader)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "member" for t in node.targets)
    ]
    assert assignments == ["budget.next_scratch()"]


# -- F2 and F6 of the research: the two findings without a code test of their own ----

DEPLOY_HARP = REPO / ".github" / "workflows" / "deploy-harp.yml"
INFO_XMLS = (REPO / "backend" / "appinfo" / "info.xml", REPO / "php" / "appinfo" / "info.xml")
SIMILAR_LINE = {
    "en": "- Similar documents: ",
    "de": "- Ähnliche Dokumente: ",
    "fr": "- Documents similaires : ",
}


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.lstrip("v").split("."))


def test_the_upgrade_start_is_never_ahead_of_the_tree() -> None:
    """F2 (assigned to 36-13): UPGRADE_FROM_TAG moves to v1.4.3 only with or after the bump.

    Pitfall 8 of the research: a start tag newer than the version the tree
    carries lays an older companion over the installed one, and branch 1 of
    "Store upgrade 4" turns red. Until 36-13 both say 1.4.2; afterwards the
    tree says 1.5.0 and the start may be v1.4.3. Either state passes, the
    wrong order does not.
    """
    match = re.search(r"^\s*UPGRADE_FROM_TAG: (v[0-9.]+)\s*$", DEPLOY_HARP.read_text(encoding="utf-8"), re.M)
    assert match is not None
    start = _version(match.group(1))
    for path in INFO_XMLS:
        version = re.search(r"^\t<version>([0-9.]+)</version>", path.read_text(encoding="utf-8"), re.M)
        assert version is not None, path
        assert start <= _version(version.group(1)), path


def test_the_similar_documents_line_stands_in_all_six_descriptions_and_the_changelog() -> None:
    """F6 (closed by 36-11): the feature of phase 35 is named where a user reads about the release."""
    import xml.etree.ElementTree as ET

    for path in INFO_XMLS:
        root = ET.parse(path).getroot()  # noqa: S314 - a file of this repository
        # The English description is the one without a lang attribute.
        descriptions = {node.get("lang", "en"): node.text or "" for node in root.findall("description")}
        for lang, line in SIMILAR_LINE.items():
            assert descriptions[lang].count(line) == 1, (path.name, lang)
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    assert "- Similar documents: " in unreleased
