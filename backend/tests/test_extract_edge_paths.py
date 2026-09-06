"""What a document becomes when its extension lies, and where a path may go.

Separate from ``test_extract_documents.py`` on purpose. That file says what a
healthy document turns into, one format per section, and it is read by whoever
adds a format. This one says what a document turns into when it is not what it
claims to be, and it is read by whoever has to explain a verdict on the status
page. Mixing the two would bury four edge paths in nine hundred lines about
paragraphs, tables and text frames.

**The type cases.** Nextcloud hands the mimetype over with the queue entry, so
the type is what the server determined and it is derived primarily from the file
name. A PDF called ``.txt`` therefore arrives at the text extractor, and a DOCX
called ``.pdf`` arrives at pdfium. Both have to end in a verdict of the closed
vocabulary. An exception escaping the extraction is the failure class the module
header of ``extract/errors.py`` names as "a wave of files marked corrupt": the
child dies, the batch is redelivered, and a whole shelf of documents is written
off for a reason nobody can read afterwards.

**The path gate.** The symlink question of the phase research is answered here
rather than dressed up as a test. Whether a symlink in a user folder leads out of
the instance is a statement about Nextcloud (assumption A2 of the research), and
this repository cannot test it. What it can test is its own side, and that is the
half the answer rests on: the container receives a stream and never a path, and
it writes into its own scratch directory alone. As long as no name and no path
out of a queue row reaches a file system call, a symlink in a user folder is not
a way out, because nothing here ever follows one.

Two invariants carry that, and both are worded fail closed:

1. No value that comes out of a queue row reaches a file system call. Judged
   through one level of local assignment, so ``target = job.path`` followed by
   ``Path(target)`` is reported as well.
2. The file travel path writes to disk in a counted number of places, and the
   list is pinned. A fifth write has to argue for itself here first, which is the
   moment at which "into which directory, and with what in its name" can still be
   asked.

Both are read off the syntax tree and not off the text of the file. That is the
comment hygiene rule of plan 06-10 in its strongest form: a comment is not part
of the tree, so a line that names ``job.path`` and ``open`` in prose cannot tip
either invariant, and the two self tests below show it rather than claim it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import docx
import pytest

from findling.extract.dispatch import extension_of, extract
from findling.extract.errors import ExtractionOutcome, Reason, State

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# The modules a file really travels through, from the queue row to the extractor,
# in posix spelling relative to the package root. The counting invariant judges
# these and no others: a benchmark that writes a database into a temporary
# directory is not on the way of a user document, and pinning its writes here
# would turn a security ratchet into a maintenance chore.
TRAVEL_PATH = ("worker/poller.py", "extract/")

# Names a queue row is bound to in this package. QueueJob arrives as "job"
# everywhere it is used, and a row of a file page of the reconcile is a "row".
# "entry" and "record" are the two further spellings a later phase would reach
# for, entered now so that the gate does not have to be widened under time
# pressure by whoever introduces one.
QUEUE_RECEIVERS = frozenset({"job", "jobs", "row", "rows", "entry", "record"})

# The fields of such a row that carry a string the user chose. QueueJob has
# exactly "path" and "title", and IndexRecord carries the same two values one
# step further, where the file name is called "name".
#
# The numeric fields are deliberately absent. A file id and a queue id come out
# of the database of Nextcloud as integers, they cannot carry a separator or a
# parent directory, and the scratch file of the poller is named after one of them
# on purpose.
USER_DATA_FIELDS = frozenset({"path", "title", "name"})

# Everything that turns a string into an operation on the file system. Reading
# entry points belong in the list as much as writing ones: this invariant is
# about where a path may point, and a read of /etc/shadow is the disclosure the
# threat register calls T-06.1-18, not a harmless call.
FILESYSTEM_CALLS = frozenset(
    {
        "Path",
        "open",
        "iterdir",
        "glob",
        "rglob",
        "scandir",
        "listdir",
        "stat",
        "lstat",
        "exists",
        "is_file",
        "is_dir",
        "resolve",
        "realpath",
        "expanduser",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
        "unlink",
        "rmdir",
        "rmtree",
        "mkdir",
        "makedirs",
        "touch",
        "chmod",
        "symlink_to",
        "hardlink_to",
        "copyfile",
        "copytree",
    }
)

# The file system calls whose bare name is an everyday method of something else.
# ``remove`` is how lxml takes an element out of a tree, ``replace`` is a method
# of every string in this package, and ``copy`` and ``move`` are common enough to
# be meaningless on their own. They are judged with their module in front, which
# is the only spelling that says what they do.
QUALIFIED_FILESYSTEM_CALLS: frozenset[tuple[str, str]] = frozenset(
    {
        ("os", "remove"),
        ("os", "rename"),
        ("os", "replace"),
        ("os", "mkdir"),
        ("os", "makedirs"),
        ("os", "rmdir"),
        ("os", "walk"),
        ("os", "listdir"),
        ("shutil", "rmtree"),
        ("shutil", "copy"),
        ("shutil", "copyfile"),
        ("shutil", "copytree"),
        ("shutil", "move"),
    }
)

# Pure path types are deliberately not in the list above. They compute a string
# and never open anything, and the package uses one of them on a file name on
# purpose: extension_of reads the suffix of the name a queue row carries, which
# is what the file type filter of SRCH-03 searches on. Putting them in would not
# tighten the invariant, it would force an exception entry for a call that cannot
# reach the file system in the first place.
PURE_PATH_TYPES = frozenset({"PurePath", "PurePosixPath", "PureWindowsPath"})

# Modes that make an open() a write. Everything else is a read, and a mode this
# gate cannot read is treated as a write, because a call that may write has to be
# counted as one.
_WRITING_MODE_CHARACTERS = "wax+"

# Calls that write to the file system, as the counting invariant sees them.
# Same split as above: the everyday method names are judged with their module.
WRITING_FILESYSTEM_CALLS = frozenset(
    {
        "write_bytes",
        "write_text",
        "unlink",
        "rmdir",
        "rmtree",
        "mkdir",
        "makedirs",
        "touch",
        "chmod",
        "symlink_to",
        "hardlink_to",
        "copyfile",
        "copytree",
    }
)

QUALIFIED_WRITING_CALLS: frozenset[tuple[str, str]] = frozenset(
    {
        ("os", "remove"),
        ("os", "rename"),
        ("os", "replace"),
        ("os", "mkdir"),
        ("os", "makedirs"),
        ("os", "rmdir"),
        ("shutil", "rmtree"),
        ("shutil", "copy"),
        ("shutil", "copyfile"),
        ("shutil", "copytree"),
        ("shutil", "move"),
    }
)

# The writes of the file travel path, measured against the package. Four, and
# every one of them is the container's own scratch volume or a read the gate
# cannot tell apart from a write:
#
#   extract/image.py: open        Image.open(path) on a picture. It reads, but
#                                 the mode of an open() is not readable off this
#                                 call, and a call that may write is counted as
#                                 one. It is listed rather than excused, because
#                                 an exception for a name would excuse the next
#                                 caller of the same name too.
#   worker/poller.py: mkdir       creates the scratch directory under
#                                 APP_PERSISTENT_STORAGE, out of findling.config
#                                 and never out of a queue row
#   worker/poller.py: open        the scratch file a document is streamed into.
#                                 It is handed to a worker thread as a reference
#                                 rather than called here, which is why the gate
#                                 counts a method reference as well.
#   worker/poller.py: unlink      removes one scratch file, in _discard. The
#                                 sweep of the files an earlier crash left
#                                 behind goes through the same function rather
#                                 than unlinking a second time, which is why one
#                                 entry covers both callers.
#
# This is a ratchet and not a tautology. A fifth entry means the container puts
# something on a disk in a place nobody has looked at yet, and the three
# questions that belong to it are which directory, what is in the name, and who
# chose that name. Failing here is the moment those questions can still be asked.
EXPECTED_TRAVEL_PATH_WRITES = (
    "extract/image.py: open",
    "worker/poller.py: mkdir",
    "worker/poller.py: open",
    "worker/poller.py: unlink",
)


def _is_pure_path_call(node: ast.Call) -> bool:
    """True for PurePosixPath(...) and its two siblings, whatever the spelling."""
    func = node.func
    name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
    return name in PURE_PATH_TYPES


def _called_name(node: ast.Call) -> str:
    """The bare name of a call, whether it is a function or a method."""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _module_qualified_name(node: ast.Call) -> tuple[str, str] | None:
    """(module, method) for a call written as ``os.remove(...)``, else None."""
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return (func.value.id, func.attr)
    return None


def _is_filesystem_call(node: ast.Call, unqualified: frozenset[str], qualified: frozenset[tuple[str, str]]) -> bool:
    """True when this call reaches the file system, under either spelling."""
    if _is_pure_path_call(node):
        return False
    return _called_name(node) in unqualified or _module_qualified_name(node) in qualified


def _queue_attributes(node: ast.AST) -> bool:
    """True when this subtree reads a user chosen string off a queue row."""
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Attribute)
            and child.attr in USER_DATA_FIELDS
            and isinstance(child.value, ast.Name)
            and child.value.id in QUEUE_RECEIVERS
        ):
            return True
    return False


def _tainted_names(tree: ast.AST) -> set[str]:
    """Local names that a queue row's user data was assigned to.

    One level, and that is a stated limit rather than an oversight. A value that
    travels through two assignments and a helper is beyond a gate that reads
    syntax, and pretending otherwise would be worse than saying so: the second
    invariant is what covers the rest, by keeping the number of places that write
    at all small enough to read.
    """
    tainted: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _queue_attributes(node.value):
            tainted.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign | ast.AugAssign):
            value = node.value
            if value is not None and _queue_attributes(value) and isinstance(node.target, ast.Name):
                tainted.add(node.target.id)
    return tainted


def _carries_user_path(node: ast.AST, tainted: set[str]) -> bool:
    """True when this subtree carries a user chosen string, directly or through a name."""
    if _queue_attributes(node):
        return True
    return any(isinstance(child, ast.Name) and child.id in tainted for child in ast.walk(node))


def user_path_violations(relative_path: str, source: str) -> list[str]:
    """Invariant 1: report every file system call that is handed a user string.

    The message names the consequence and not the count. A path out of user data
    in a file system call is a way out of the scratch directory, and that is what
    a reader of a failing gate has to understand in the first line.
    """
    normalized = relative_path.replace("\\", "/")
    tree = ast.parse(source, filename=relative_path)
    tainted = _tainted_names(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_filesystem_call(node, FILESYSTEM_CALLS, QUALIFIED_FILESYSTEM_CALLS):
            name = _called_name(node)
            if any(
                _carries_user_path(argument, tainted)
                for argument in [*node.args, *(keyword.value for keyword in node.keywords)]
            ):
                violations.append(
                    f"{normalized}:{node.lineno}: a path out of a queue row reaches {name}(), "
                    "which is a way out of the scratch directory"
                )
            receiver = node.func.value if isinstance(node.func, ast.Attribute) else None
            if receiver is not None and _carries_user_path(receiver, tainted):
                violations.append(
                    f"{normalized}:{node.lineno}: a path out of a queue row is the receiver of {name}(), "
                    "which is a way out of the scratch directory"
                )
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and _carries_user_path(node, tainted):
            violations.append(
                f"{normalized}:{node.lineno}: a name out of a queue row is joined onto a directory, "
                "which is a way out of the scratch directory"
            )

    return violations


def _is_writing_open(node: ast.Call) -> bool:
    """True when this open() writes. A mode the gate cannot read counts as a write."""
    mode: ast.expr | None = None
    if node.args:
        mode = node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode = keyword.value
    if mode is None:
        return False
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return any(character in mode.value for character in _WRITING_MODE_CHARACTERS)
    return True


def writing_calls(relative_path: str, source: str) -> list[str]:
    """Invariant 2: every place in this module that writes to the file system.

    A method reference counts as well, and it has to. The poller hands
    ``scratch.open`` to a worker thread rather than calling it, because a
    blocking open in the event loop is the same stall as a blocking write on the
    slow card this app runs from. A gate that only judged calls would see the one
    write that really matters as nothing at all.
    """
    normalized = relative_path.replace("\\", "/")
    tree = ast.parse(source, filename=relative_path)
    called: set[int] = set()
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called.add(id(node.func))
        name = _called_name(node)
        if (
            name in WRITING_FILESYSTEM_CALLS
            or _module_qualified_name(node) in QUALIFIED_WRITING_CALLS
            or (name == "open" and _is_writing_open(node))
        ):
            found.append(f"{normalized}: {name}")

    found += [
        f"{normalized}: {node.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and id(node) not in called
        and (node.attr in WRITING_FILESYSTEM_CALLS or node.attr == "open")
    ]
    return found


def _travel_path_modules() -> list[tuple[str, str]]:
    """Return (relative posix path, source) for every module a document travels through."""
    modules: list[tuple[str, str]] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        if relative.startswith(TRAVEL_PATH):
            modules.append((relative, path.read_text(encoding="utf-8")))
    return modules


def _package_modules() -> list[tuple[str, str]]:
    """Return (relative posix path, source) for every module of the package."""
    return [
        (path.relative_to(PACKAGE_ROOT).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(PACKAGE_ROOT.rglob("*.py"))
    ]


# -- the type cases: a document whose extension lies -------------------------


def _assemble_pdf(objects: list[bytes]) -> bytes:
    """Numbered objects plus a correct cross reference table, as in build_corpus.py.

    Built here rather than taken from the reference corpus, because these cases
    are about a byte pattern and not about the end to end route. Every corpus file
    travels through every read only gate run and has to be kept in the verdict
    table of CORPUS.md, and none of that would buy anything here.
    """
    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_offset = len(out)
    size = len(objects) + 1
    out += f"xref\n0 {size}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return bytes(out)


def _one_page_pdf(padding: bytes = b"") -> bytes:
    """A readable one page PDF, optionally with a binary blob riding along.

    The padding is what separates the two answers of the first case below: an
    uncompressed PDF is almost entirely ASCII, a real one carries compressed
    streams and is mostly not.
    """
    content = b"BT /F1 12 Tf 40 700 Td (Kuendigung des Mietverhaeltnisses zum Monatsende) Tj ET\n"
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    if padding:
        objects.append(b"<< /Length " + str(len(padding)).encode("ascii") + b" >>\nstream\n" + padding + b"\nendstream")
    return _assemble_pdf(objects)


def _write(directory: Path, name: str, payload: bytes) -> str:
    target = directory / name
    target.write_bytes(payload)
    return str(target)


def _docx(directory: Path, name: str) -> Path:
    document = docx.Document()
    document.add_paragraph("Aktenvermerk der Gemeinde zur Grundstuecksverkehrsgenehmigung.")
    target = directory / name
    document.save(str(target))
    return target


def test_a_pdf_announced_as_plain_text_ends_in_a_verdict_and_does_not_raise(tmp_path: Path) -> None:
    # An uncompressed PDF is almost entirely ASCII, so the text extractor reads
    # it and the index gets the structure of the file instead of its content.
    # That is pinned rather than repaired, and the reason is written down at
    # ALLOWED_MIMETYPES: the type comes from Nextcloud, and sniffing the first
    # bytes here would be a second type decision beside the one the server
    # already made. The cost is bounded, a handful of dictionary keys of one
    # file, and the benefit of the alternative is a format detector this
    # container would have to maintain for every format it accepts.
    #
    # What matters for the threat register is the line below: a verdict, no
    # exception, and nothing that ends the extraction child.
    outcome = extract(_write(tmp_path, "kuendigung.txt", _one_page_pdf()), "text/plain", 4096)

    assert outcome.state is State.INDEXED
    assert outcome.reason is None


def test_a_binary_pdf_announced_as_plain_text_is_refused_instead_of_indexed(tmp_path: Path) -> None:
    # The other half of the case above, and the half that carries the threat.
    # A PDF as it comes out of a word processor carries compressed streams, and
    # a compressed stream is not text under any encoding. The run of control
    # bytes below stands in for one, written out rather than compressed so that
    # the fixture is the same bytes on every machine. Without the printable share
    # of _decode this ends as an index entry made of control characters, which is
    # T-06.1-19: unreadable bytes indexed as noise instead of refused.
    payload = _one_page_pdf(padding=b"\x00\x01\x02\x03" * 2048)

    outcome = extract(_write(tmp_path, "bericht.txt", payload), "text/plain", len(payload))

    assert outcome == ExtractionOutcome.failed(Reason.ENCODING_UNKNOWN)


def test_a_docx_announced_as_a_pdf_is_failed_corrupt(tmp_path: Path) -> None:
    # The direction test_extract_documents.py does not cover: that file feeds a
    # non archive to the OOXML route, this one feeds an archive to the PDF route.
    # pypdf finds no header, raises PdfReadError, and extract_pdf turns it into a
    # verdict instead of letting it travel to the process boundary.
    source = _docx(tmp_path, "brief.docx")
    payload = source.read_bytes()

    outcome = extract(_write(tmp_path, "brief.pdf", payload), "application/pdf", len(payload))

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)


@pytest.mark.parametrize(
    ("name", "mime", "needle"),
    [
        ("aktenvermerk", "text/plain", "Monatsende"),
        ("kuendigung", "application/pdf", "Kuendigung"),
    ],
    ids=["plain-without-extension", "pdf-without-extension"],
)
def test_a_file_without_an_extension_is_judged_by_the_announced_type(
    name: str, mime: str, needle: str, tmp_path: Path
) -> None:
    # A file with no extension at all still has a type, because the type travels
    # with the queue entry. Nothing in the extraction path reads the name to
    # decide what to do, and the assertion on extension_of is what makes that
    # visible: the name says nothing, the document is extracted anyway.
    payload = b"Die Kuendigung wird zum Monatsende wirksam." if mime == "text/plain" else _one_page_pdf()

    outcome = extract(_write(tmp_path, name, payload), mime, len(payload))

    assert extension_of(name) == ""
    assert outcome.state is State.INDEXED
    assert needle in outcome.text


@pytest.mark.parametrize(
    ("name", "mime"),
    [
        ("brief.docx", "application/zip"),
        ("bericht.pdf", "application/x-msdownload"),
        ("notiz.txt", "application/vnd.ms-excel"),
    ],
    ids=["zip-called-docx", "binary-called-pdf", "legacy-office-called-txt"],
)
def test_a_type_outside_the_allowlist_is_skipped_whatever_the_name_says(name: str, mime: str, tmp_path: Path) -> None:
    # The allowlist decides, and it decides before a single byte is read. The
    # third row is the pre 2007 Office format, which is documented non support
    # rather than a gap: the name is the one an ordinary user would give it, and
    # it changes nothing.
    payload = b"PK\x03\x04 nothing that belongs in an index"

    outcome = extract(_write(tmp_path, name, payload), mime, len(payload))

    assert outcome == ExtractionOutcome.skipped(Reason.MIME_NOT_ALLOWED)


# -- invariant 1: no user path in a file system call -------------------------


def test_the_real_package_lets_no_queue_path_reach_a_filesystem_call() -> None:
    violations = [
        message for relative, source in _package_modules() for message in user_path_violations(relative, source)
    ]

    assert violations == [], "a path out of user data reaches the file system:\n" + "\n".join(violations)


def test_the_gate_reports_a_queue_path_handed_to_a_call() -> None:
    source = "def f(job):\n    return Path(job.path).read_bytes()\n"

    violations = user_path_violations("worker/poller.py", source)

    assert violations != []
    assert "way out of the scratch directory" in violations[0]


def test_the_gate_reports_a_queue_name_joined_onto_a_directory() -> None:
    # The shape the scratch file is built with. Today the join carries the
    # numeric queue id; with the file name in it, a name containing a parent
    # directory would write outside the scratch volume.
    source = 'def f(self, job):\n    return self._tmp_dir / f"job-{job.title}"\n'

    violations = user_path_violations("worker/poller.py", source)

    assert violations != []
    assert "joined onto a directory" in violations[0]


def test_the_gate_follows_one_assignment() -> None:
    # The bypass that a gate reading only call arguments walks past: the value is
    # parked in a local name first, and the call then looks harmless.
    source = "def f(job):\n    target = job.title\n    return Path(target).open('rb')\n"

    violations = user_path_violations("worker/poller.py", source)

    assert violations != []


def test_a_numeric_field_of_a_queue_row_is_not_a_path() -> None:
    # The scratch file of the poller, in the shape it really has. A file id and a
    # queue id come out of the database as integers and cannot carry a separator,
    # which is why the name is built from one of them.
    source = 'def f(self, job):\n    return self._tmp_dir / f"job-{job.queue_id}.part"\n'

    assert user_path_violations("worker/poller.py", source) == []


def test_a_pure_path_on_a_file_name_is_not_a_filesystem_call() -> None:
    # extension_of does exactly this, on the name of a queue row, and it has to
    # stay allowed: a pure path computes a string and opens nothing.
    source = "def f(job):\n    return PurePosixPath(job.title).suffix\n"

    assert user_path_violations("extract/dispatch.py", source) == []


def test_a_comment_that_names_a_queue_path_and_a_call_does_not_tip_the_gate() -> None:
    # The comment hygiene rule of plan 06-10, in the form a syntax tree gives it
    # for free. Both invariants read the tree, and a comment is not in the tree,
    # so a paragraph that explains why Path(job.path) must never be written
    # cannot make the gate report the paragraph.
    source = (
        "# Never write Path(job.path).read_bytes() here, and never\n"
        '# self._tmp_dir / f"job-{job.title}" either: both would leave the scratch.\n'
        "def f(job):\n"
        '    """Not Path(job.path), and not open(job.title) either."""\n'
        "    return job.file_id\n"
    )

    assert user_path_violations("worker/poller.py", source) == []


# -- invariant 2: the counted writes of the file travel path -----------------


def test_the_file_travel_path_writes_in_exactly_the_pinned_places() -> None:
    found = tuple(
        sorted(message for relative, source in _travel_path_modules() for message in writing_calls(relative, source))
    )

    assert found == EXPECTED_TRAVEL_PATH_WRITES, "the file travel path writes somewhere new:\n" + "\n".join(found)


def test_the_counting_invariant_sees_an_added_write() -> None:
    source = 'def f(target):\n    target.write_bytes(b"x")\n'

    assert writing_calls("extract/text.py", source) == ["extract/text.py: write_bytes"]


def test_a_read_with_a_readable_mode_is_not_counted_as_a_write() -> None:
    # Path(path).open("rb") in extract/office.py is a read and says so in its
    # own argument. Counting it would make the ratchet meaningless by making it
    # large, and a large list of reviewed exceptions is a list nobody reviews.
    source = 'def f(path):\n    return Path(path).open("rb")\n'

    assert writing_calls("extract/office.py", source) == []


def test_an_open_whose_mode_the_gate_cannot_read_is_counted_as_a_write() -> None:
    # A call that may write has to be counted as one, which is the same rule the
    # read only gate applies to an HTTP method it cannot read. Image.open(path)
    # of extract/image.py is the real instance of it, and it stands in the pinned
    # list above with the reason instead of being waved through.
    for source in (
        "def f(path, mode):\n    return Path(path).open(mode)\n",
        "def f(path):\n    return Image.open(path)\n",
    ):
        assert writing_calls("worker/poller.py", source) == ["worker/poller.py: open"]


def test_a_write_handed_on_as_a_method_reference_is_counted() -> None:
    # The shape of the one write that matters. The poller does not call
    # scratch.open, it hands the bound method to a worker thread, because a
    # blocking open in the event loop is the same stall as a blocking write.
    source = 'async def f(scratch):\n    return await asyncio.to_thread(scratch.open, "wb")\n'

    assert writing_calls("worker/poller.py", source) == ["worker/poller.py: open"]


def test_a_comment_line_does_not_change_the_count() -> None:
    # The counting half of the comment hygiene rule. The same source with three
    # comment lines that name every word the gate looks for produces the same
    # count, because the count is taken off the tree.
    plain = 'def f(target):\n    target.write_bytes(b"x")\n'
    commented = (
        "# write_text and unlink and mkdir and makedirs and rmtree\n"
        'def f(target):\n    # rename, replace, touch, symlink_to, open("wb")\n    target.write_bytes(b"x")\n'
    )

    assert writing_calls("extract/text.py", plain) == writing_calls("extract/text.py", commented)
