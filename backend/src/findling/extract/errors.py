"""The closed list of verdicts and the one place that reads an exception.

Every file this container looks at is judged exactly once and carries one pair of
state and reason. The pairs are closed and they are the payload of IDX-06:
``skipped`` means "we decided not to index this", ``failed`` means "we wanted to
and could not". Only ``failed`` is an error on the status page, and only
``skipped(no_text_layer)`` is the list phase 3 reads to learn which PDFs need
OCR. A file in the wrong bucket does not raise anything, it makes two numbers on
the admin page lie, which is why a pair that does not exist cannot be built here.

**The same list lives in findling/store/repo.py as STATE_REASONS.** Whoever adds
a pair here has to add it there in the same commit. Two lists that drift apart
break the return channel to Nextcloud silently: this side produces a verdict the
store refuses to write, and the file ends up with no verdict at all. A test
compares both mappings so the duplication cannot rot unnoticed.

**This module imports the standard library only, on purpose.** It runs in the
extraction child, and the child is recycled regularly, so every import here is
paid again on every recycle. That is also why the exception table matches fully
qualified class names instead of importing zipfile, lxml and python-docx just to
name three classes. The names are matched along the whole inheritance chain, and
the tests build the real exception objects, so a renamed class shows up as a red
test rather than as a wave of files marked corrupt.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final


class State(StrEnum):
    """The three outcomes a file can have. There is no fourth and no pending.

    A file that is still to be done has no row in the state store at all, so
    "queued" is the absence of a verdict rather than a verdict of its own.
    """

    INDEXED = "indexed"
    SKIPPED = "skipped"
    FAILED = "failed"


class Reason(StrEnum):
    """Why a file ended up in its state.

    English identifiers because they are code; the German labels of the admin
    page are built in phase 4 from these values. A reason is never composed at
    runtime and never carries a path, a file name or an exception message
    (T-02-56): the code is the whole message.
    """

    # indexed
    TRUNCATED = "truncated"

    # skipped, the deliberate decisions
    TOO_LARGE = "too_large"
    MIME_NOT_ALLOWED = "mime_not_allowed"
    ENCRYPTED = "encrypted"
    NO_TEXT_LAYER = "no_text_layer"
    EMPTY_TEXT = "empty_text"
    TOO_MANY_CELLS = "too_many_cells"
    GONE = "gone"
    IMAGE_NOT_OCRABLE = "image_not_ocrable"  # a picture too small or too flat to carry text

    # failed, the things we wanted to do and could not
    EMPTY_FILE = "empty_file"
    CORRUPT = "corrupt"
    XML_INVALID = "xml_invalid"
    ENCODING_UNKNOWN = "encoding_unknown"
    TIMEOUT = "timeout"
    OUT_OF_MEMORY = "out_of_memory"
    GATEWAY_ERROR = "gateway_error"
    REPEATEDLY_STUCK = "repeatedly_stuck"
    OCR_FAILED = "ocr_failed"  # the engine ended with a non zero code or was killed by a signal
    OCR_UNAVAILABLE = "ocr_unavailable"  # no engine and no language data in this image


# The closed list. Kept word for word identical with STATE_REASONS in
# findling/store/repo.py, see the module docstring above.
STATE_REASONS: Final[Mapping[State, frozenset[Reason | None]]] = {
    State.INDEXED: frozenset({None, Reason.TRUNCATED}),
    State.SKIPPED: frozenset(
        {
            Reason.TOO_LARGE,
            Reason.MIME_NOT_ALLOWED,
            Reason.ENCRYPTED,
            Reason.NO_TEXT_LAYER,  # the bridge to phase 3: these are the OCR candidates
            Reason.EMPTY_TEXT,
            Reason.TOO_MANY_CELLS,
            Reason.GONE,
            Reason.IMAGE_NOT_OCRABLE,
        }
    ),
    State.FAILED: frozenset(
        {
            Reason.EMPTY_FILE,
            Reason.CORRUPT,
            Reason.XML_INVALID,
            Reason.ENCODING_UNKNOWN,
            Reason.TIMEOUT,
            Reason.OUT_OF_MEMORY,
            Reason.GATEWAY_ERROR,
            Reason.REPEATEDLY_STUCK,
            Reason.OCR_FAILED,
            Reason.OCR_UNAVAILABLE,
        }
    ),
}


# Fully qualified exception class names, measured against the reference corpus and
# against deliberately broken inputs in python:3.13-slim-trixie. Matched along the
# inheritance chain, so a library specific subclass lands on the same reason.
#
# pypdf.errors.EmptyFileError arrived with plan 02-08. The PDF extractor catches
# it itself, so this entry is the net under the day somebody reorders that
# function: a zero byte file that escapes should still be empty_file and not the
# blanket corrupt.
#
# FileNotDecryptedError is deliberately **not** in this table, although the note
# of plan 02-05 proposed it. This function only ever builds a failed verdict, and
# encrypted belongs to skipped: the pair failed(encrypted) does not exist, so the
# entry would not translate an exception, it would raise a ValueError inside the
# error handler. A password protected file is a decision, and a decision is made
# where the file is opened, not where an exception is read.
#
# image_not_ocrable of phase 3 is the same rule a second time: a picture that is
# too small to carry text is a decision made where the picture is measured, and
# the pair failed(image_not_ocrable) does not exist either. Only failed reasons
# belong in this table, and a test walks its values to keep it that way.
_EXCEPTION_REASONS: Final[Mapping[str, Reason]] = {
    "builtins.MemoryError": Reason.OUT_OF_MEMORY,
    "zipfile.BadZipFile": Reason.CORRUPT,
    "docx.opc.exceptions.PackageNotFoundError": Reason.CORRUPT,
    "pptx.exc.PackageNotFoundError": Reason.CORRUPT,
    "lxml.etree.XMLSyntaxError": Reason.XML_INVALID,
    "pypdf.errors.EmptyFileError": Reason.EMPTY_FILE,
}


@dataclass(frozen=True, slots=True)
class ExtractionOutcome:
    """One judged file: a state, its reason, and the text if there is any.

    Frozen because a verdict that can be edited after the fact is a verdict two
    call sites disagree about. Built through the three classmethods rather than
    directly, so that the pair is validated in one place and a caller cannot
    accidentally attach text to a failure.
    """

    state: State
    reason: Reason | None = None
    text: str = field(default="", repr=False)
    text_chars: int = 0

    def __post_init__(self) -> None:
        allowed = STATE_REASONS.get(self.state)
        if allowed is None:
            raise ValueError(f"unknown state {self.state!r}")
        if self.reason not in allowed:
            raise ValueError(f"reason {self.reason!r} does not belong to state {self.state!r}")

    @property
    def truncated(self) -> bool:
        """True when the text was cut at the character cap (pitfall 12)."""
        return self.reason is Reason.TRUNCATED

    @classmethod
    def indexed(cls, text: str, *, truncated: bool = False) -> ExtractionOutcome:
        """A file with text. The character count is stored, never recomputed later."""
        return cls(
            state=State.INDEXED,
            reason=Reason.TRUNCATED if truncated else None,
            text=text,
            text_chars=len(text),
        )

    @classmethod
    def skipped(cls, reason: Reason) -> ExtractionOutcome:
        """A file we decided not to index. Carries no text, by construction."""
        return cls(state=State.SKIPPED, reason=reason)

    @classmethod
    def failed(cls, reason: Reason) -> ExtractionOutcome:
        """A file we wanted to index and could not. This is what the status page counts."""
        return cls(state=State.FAILED, reason=reason)

    @classmethod
    def from_exception(cls, error: BaseException) -> ExtractionOutcome:
        """Translate a library exception into a verdict, never re-raise it.

        This is the only place in the extraction path that knows exception types.
        The format modules raise whatever their library raises and stay free of
        the taxonomy, which is what keeps a new format from inventing a new state.

        Anything unknown becomes failed(corrupt): an exception that escaped a
        parser means the document beat the parser, and letting it travel further
        would end the child process for a reason nobody can read off the status
        page afterwards.
        """
        for klass in type(error).__mro__:
            reason = _EXCEPTION_REASONS.get(f"{klass.__module__}.{klass.__qualname__}")
            if reason is not None:
                return cls.failed(reason)
        return cls.failed(Reason.CORRUPT)
