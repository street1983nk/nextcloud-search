# ANALYZER_VERSION is deliberately not in this module. It lives in
# findling/index/analyzer.py, directly next to the filter chain it versions,
# because a version number that sits away from the thing it describes is a
# version number that stops being raised.
"""The single home of every cap and every path of phase 2.

Seven later plans read the same numbers. A second place holding the same number
is an operational fault in slow motion: the two copies agree on the day they are
written and disagree on the day one of them is tuned. So every cap is a named
constant here, every number carries the line of reasoning that produced it, and
nothing outside this module writes a literal for a limit.

Two design rules hold throughout.

*Unusable input never stops the container.* Numbers arrive from environment
variables that an admin edits by hand in the Nextcloud app settings. A typo in
``FINDLING_MAX_TEXT_CHARS`` must degrade to the measured default with a warning,
not into a crash loop on a box where nobody reads the boot log (T-02-13).

*The log names variables, never values.* The analysis path carries user content,
and a warning that echoes what somebody typed is the cheapest way to leak it
(T-02-14).
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

LOGGER = logging.getLogger("findling.config")

# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

# Layout of the tantivy schema. Raised when a field is added, removed or retyped;
# every raise forces a visible reindex rather than a silently mixed index.
SCHEMA_VERSION = 1

# Layout of the on disk index directory, including the tantivy index format.
# tantivy 0.26.0 reports index_format v7 and does not promise stability across
# its own releases, so this is persisted and checked on open.
INDEX_VERSION = 1

# ---------------------------------------------------------------------------
# Architecture, not configuration
# ---------------------------------------------------------------------------

# IDX-08. One indexing worker, always. OCR peaks at 300 to 600 MB for a single
# 300 dpi A4 page and the embedding model adds 250 to 400 MB; on the 4 GB box
# this project targets, those two peaks must never be allowed to meet. This is
# not a tuning knob and deliberately reads no environment variable, so that
# making it one is a code change somebody has to defend in review.
INDEX_WORKERS = 1

# ---------------------------------------------------------------------------
# Language
# ---------------------------------------------------------------------------

# Field order of the schema, not the order somebody types into the environment.
DEFAULT_LANGUAGES = ("de", "en")

# The two measured recipes of the constituent dictionary. full is recipe A
# (276496 entries, 14 of 16 test compounds), nouns is recipe C (86345 entries,
# 12 of 16) for boxes where the roughly 23 MB of the automaton hurt.
COMPOUND_DICT_VARIANTS = ("full", "nouns")
DEFAULT_COMPOUND_DICT = "full"

# ---------------------------------------------------------------------------
# Caps. Every number comes from the measurement table of the phase research.
# ---------------------------------------------------------------------------

# 50 MB. Enforced during the PHP crawl, at the moment a file is queued, because
# a file that is never queued costs the container nothing at all.
MAX_FILE_BYTES = 52_428_800

# One pull from the queue: at most 32 files or 64 MB, whichever comes first. The
# byte cap is the one that matters; 32 scanned PDFs are a different workload from
# 32 text files.
#
# The byte cap is also the knob for "the search hangs while the indexer commits",
# because it decides how much a single commit has to fsync. Plan 02-13 measured
# whether it has to be turned, in the shipping image on a disk throttled to
# 2 MB/s with docker run --device-write-bps, 200 searches per run:
#
#     p95 idle          0.196 ms
#     p95 under write   0.166 to 0.216 ms over three runs
#
# The two are indistinguishable, so the value stays at 64 MB. What the throttle
# does slow down is the writer, not the reader: the same measurement window holds
# 12 commits instead of 19. Smaller batches would buy nothing here and would cost
# more segments and more merges. The measurement job in .github/workflows/
# resilience.yml keeps producing both numbers, so the day this stops being true
# is a day somebody can see.
BATCH_FILES = 32
BATCH_MAX_BYTES = 67_108_864

# Wall clock budget of one extraction, enforced by Process.join(timeout) followed
# by kill(). Only kill() reliably ends a hung C extension.
EXTRACT_TIMEOUT_SECONDS = 120

# 512 MB address space for the extraction child, via RLIMIT_AS. Measured: 300 MB
# already produces MemoryError inside the child, so this leaves headroom while
# still bounding a runaway document.
EXTRACT_ADDRESS_SPACE_BYTES = 536_870_912

# Recycling threshold of the extraction child (plan 02-05). C extensions
# fragment their heap; a child that is replaced after 200 files never gets the
# chance to grow into the box.
EXTRACT_WORKER_MAX_FILES = 200

# 512 kB of characters per document, after which the state becomes truncated. A
# single 50 MB PDF would otherwise dominate the index on its own.
MAX_TEXT_CHARS = 524_288

# Cells per spreadsheet, counted inside the iter_rows loop. One export file with
# a million rows is the classic way to tip a small container over.
MAX_CELLS = 200_000

# Pages per PDF, after which the loop stops and the state becomes truncated.
MAX_PDF_PAGES = 500

# 500 MB of free disk before a commit. Below it the indexer goes to
# paused_low_disk instead of filling the volume the user's data lives on.
MIN_FREE_BYTES = 524_288_000

# tantivy writer heap. Below roughly 15 MB tantivy refuses outright; 50 MB is the
# measured small box setting that keeps the writer peak inside the RAM budget.
WRITER_HEAP_BYTES = 50_000_000

# Poll backoff of the queue worker: start at 15 s when the queue runs empty and
# back off to 120 s. Slow enough to be invisible on an idle instance, fast enough
# that a newly queued file is not left waiting for minutes.
POLL_COOLDOWN_START_SECONDS = 15
POLL_COOLDOWN_MAX_SECONDS = 120

# The candidate search asks tantivy for overfetch times the requested number of
# hits and repeats at most rounds times, because the ACL prefilter and the final
# PHP recheck both remove hits after ranking.
SEARCH_OVERFETCH = 4
SEARCH_ROUNDS = 3

# Characters per snippet. The unified search subline is a single line of text.
SNIPPET_CHARS = 200

# Upper bound of the limit a caller may request, mirrored by the API model.
SEARCH_LIMIT_MAX = 100

# Upper bound of the paging offset a caller may request (security audit C1). The
# endpoints carry access_level USER, so any signed-in account reaches them with a
# free JSON body; tantivy allocates (limit+offset)*24 bytes eagerly, and an
# unbounded offset therefore aborts the whole process with a Rust allocation
# failure that no Python handler can catch. No legitimate cursor ever climbs past
# a full result set of overfetched, multi-round candidates, so this ceiling is far
# above any real paging depth and still keeps the allocation in the kilobyte range.
SEARCH_OFFSET_MAX = SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS

# Upper bound on the length of a query string (security audit C2/M3). The query is
# expanded per token with umlaut variants across several boosted fields and then
# run against the live index with count=True, so a megabyte-long query is seconds
# of CPU per request; and the lenient parser descends recursively on parentheses,
# so a deeply nested query overflows the native stack of the same process the ASGI
# app runs in. 512 characters is longer than any real search line.
SEARCH_QUERY_MAX_CHARS = 512

# Maximum bracket nesting a query line may carry before the recursive-descent
# parser is even entered (security audit C2). Real queries never nest this deep.
SEARCH_QUERY_MAX_DEPTH = 32

# Subdirectory used when APP_PERSISTENT_STORAGE is absent, which is the case in
# tests and in a bare local run, never in a container deployed by AppAPI.
FALLBACK_STORAGE_DIRNAME = "findling"


@dataclass(frozen=True, slots=True)
class Settings:
    """The resolved caps and paths of one process.

    Frozen on purpose: a cap that can be reassigned at runtime is a cap that
    differs between two call sites, and the whole point of this module is that
    it cannot.
    """

    index_dir: Path
    state_db: Path
    dict_dir: Path
    tmp_dir: Path

    languages: tuple[str, ...]
    compound_dict: str

    max_file_bytes: int
    batch_files: int
    batch_max_bytes: int
    extract_timeout_seconds: int
    extract_address_space_bytes: int
    extract_worker_max_files: int
    max_text_chars: int
    max_cells: int
    max_pdf_pages: int
    min_free_bytes: int
    writer_heap_bytes: int
    poll_cooldown_start_seconds: int
    poll_cooldown_max_seconds: int
    search_overfetch: int
    search_rounds: int
    snippet_chars: int
    search_limit_max: int


def _int_from_environment(name: str, default: int) -> int:
    """Read a positive whole number, falling back to the measured default.

    Every failure path is the same: warn with the name of the variable and use
    the default. Raising here would turn one wrong character in an admin form
    into a container that will not start, on a machine with no operator watching.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        LOGGER.warning("%s is not a whole number, falling back to the built in default", name)
        return default
    if value < 1:
        LOGGER.warning("%s is not a positive number, falling back to the built in default", name)
        return default
    return value


def _storage_root() -> Path:
    """Return the root of the persistent volume, or a temp directory in its place.

    AppAPI always sets APP_PERSISTENT_STORAGE for a deployed container. The
    fallback exists for tests and for a bare local run, and it is a directory of
    our own inside the system temp directory rather than the temp directory
    itself, so that a cleanup never reaches beyond what this app created.
    """
    configured = os.environ.get("APP_PERSISTENT_STORAGE", "").strip()
    if configured:
        return Path(configured)
    return Path(tempfile.gettempdir()) / FALLBACK_STORAGE_DIRNAME


def _languages() -> tuple[str, ...]:
    """Return the active language fields, in schema order.

    An empty or unrecognisable list keeps both fields. Dropping to no language at
    all would produce an index that cannot answer anything, which is a worse
    outcome than ignoring the variable.
    """
    requested = {part.strip().lower() for part in os.environ.get("FINDLING_LANGUAGES", "").split(",")}
    kept = tuple(language for language in DEFAULT_LANGUAGES if language in requested)
    if kept:
        return kept
    if requested - {""}:
        LOGGER.warning("FINDLING_LANGUAGES names no supported language, falling back to the built in default")
    return DEFAULT_LANGUAGES


def _compound_dict() -> str:
    """Return the constituent dictionary variant, full unless nouns is asked for."""
    requested = os.environ.get("FINDLING_COMPOUND_DICT", "").strip().lower()
    if requested in COMPOUND_DICT_VARIANTS:
        return requested
    if requested:
        LOGGER.warning("FINDLING_COMPOUND_DICT is not one of the measured variants, falling back to full")
    return DEFAULT_COMPOUND_DICT


@lru_cache(maxsize=1)
def settings() -> Settings:
    """Resolve the settings once per process.

    Cached because the environment does not change while the process runs and
    because two callers seeing two different Settings objects would reintroduce
    exactly the drift this module exists to prevent. Tests clear the cache.
    """
    root = _storage_root()
    return Settings(
        index_dir=root / "index",
        state_db=root / "state.db",
        dict_dir=root / "dict",
        tmp_dir=root / "tmp",
        languages=_languages(),
        compound_dict=_compound_dict(),
        max_file_bytes=_int_from_environment("FINDLING_MAX_FILE_BYTES", MAX_FILE_BYTES),
        batch_files=_int_from_environment("FINDLING_BATCH_FILES", BATCH_FILES),
        batch_max_bytes=_int_from_environment("FINDLING_BATCH_MAX_BYTES", BATCH_MAX_BYTES),
        extract_timeout_seconds=_int_from_environment("FINDLING_EXTRACT_TIMEOUT_SECONDS", EXTRACT_TIMEOUT_SECONDS),
        extract_address_space_bytes=_int_from_environment(
            "FINDLING_EXTRACT_ADDRESS_SPACE_BYTES", EXTRACT_ADDRESS_SPACE_BYTES
        ),
        extract_worker_max_files=_int_from_environment("FINDLING_EXTRACT_WORKER_MAX_FILES", EXTRACT_WORKER_MAX_FILES),
        max_text_chars=_int_from_environment("FINDLING_MAX_TEXT_CHARS", MAX_TEXT_CHARS),
        max_cells=_int_from_environment("FINDLING_MAX_CELLS", MAX_CELLS),
        max_pdf_pages=_int_from_environment("FINDLING_MAX_PDF_PAGES", MAX_PDF_PAGES),
        min_free_bytes=_int_from_environment("FINDLING_MIN_FREE_BYTES", MIN_FREE_BYTES),
        writer_heap_bytes=_int_from_environment("FINDLING_WRITER_HEAP_BYTES", WRITER_HEAP_BYTES),
        poll_cooldown_start_seconds=_int_from_environment(
            "FINDLING_POLL_COOLDOWN_START_SECONDS", POLL_COOLDOWN_START_SECONDS
        ),
        poll_cooldown_max_seconds=_int_from_environment(
            "FINDLING_POLL_COOLDOWN_MAX_SECONDS", POLL_COOLDOWN_MAX_SECONDS
        ),
        search_overfetch=_int_from_environment("FINDLING_SEARCH_OVERFETCH", SEARCH_OVERFETCH),
        search_rounds=_int_from_environment("FINDLING_SEARCH_ROUNDS", SEARCH_ROUNDS),
        snippet_chars=_int_from_environment("FINDLING_SNIPPET_CHARS", SNIPPET_CHARS),
        search_limit_max=_int_from_environment("FINDLING_SEARCH_LIMIT_MAX", SEARCH_LIMIT_MAX),
    )
