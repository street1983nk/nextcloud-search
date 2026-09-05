"""The three numbers of wave 0, measured instead of estimated.

06-RESEARCH.md carries thirteen assumptions and four of them carry every decision
of phase 6. This module answers three of the four, and it exists because all
three are cheap now and expensive once a vector schema stands:

* ``chars-per-token`` (A1, "3,5 characters per token for German, range 3,0 to
  4,0"). It sets the token count per document, and through it the chunk count,
  the disk size and the run time of the second track, all three linearly. Thirty
  seconds of work decides a number the whole phase is planned against.
* ``tokens-per-second`` (A2 and A3, "30 to 100 GFLOP/s" and "800 to 2.000 tokens
  per second"). This is the measurement that decides whether the phase is doable
  in its current shape at all: the two independent estimates of 3.5 land at 54 to
  180 hours for a full pass, and D-01 caps the input at the first 1.024 tokens of
  a document to bring that down to an expected 7 to 24 hours. If even the capped
  figure comes out above a day, D-04 hands the potion question back to the owner.
* ``scan-latency`` (the ground under A4 and under the choice between int8, bit
  vectors and usearch). The yardstick is in this repository's own code and had
  never been connected to the vector side: ``php/lib/Search/Provider.php`` runs
  ``BUDGET_NANOSECONDS = 2_500_000_000`` and ``MAX_ROUNDS = 3``, so one user
  search can trigger three container rounds and each of them would contain a full
  scan. 06-RESEARCH.md 2.2 proposes 300 ms p95 per round as the abort criterion.

Numbers only, never a token and never a word from a document: this path would see
user content in a production index, and a measurement that prints what it read is
the cheapest way to leak it (T-02-14, T-06-06). ``chars-per-token`` is the one
mode that reads real German text, and it prints the file count and the character
total and no file name, ever. The text of ``tokens-per-second`` is synthetic and
fixed in this module, so that mode needs no corpus at all.

Every mode prints ``uname -m`` and the number of visible CPUs beside its result
(T-06-07). A number without its hardware is a claim that will be quoted at the
wrong machine, and all three of these are architecture dependent in a different
way: the tokenizer is not, the inference loop is, and the scan is bound by memory
bandwidth.

**One deliberate exception with notice.** All SQL of this application lives under
``store/``, and the vec0 statements below break that rule. They are allowed to,
because this file is a measuring tool and not a store: it owns a scratch database
in a temporary directory, it never touches the operating state, and the schema it
writes is thrown away at the end of the run. The productive vec0 SQL belongs in
``store/`` and is written by plan 06-04, which is also where the two findings of
the A12 probe apply: ``vec_int8()`` at the call site, and ``load_extension``
before ``PRAGMA query_only``.

Run it with::

    uv run python -m findling.embed.bench --mode chars-per-token
    uv run python -m findling.embed.bench --mode tokens-per-second --batch 8 --sequence 512
    uv run python -m findling.embed.bench --mode scan-latency --vector-type int8 --cache both
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Final

from tokenizers import Tokenizer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence

MODE_CHARS: Final = "chars-per-token"
MODE_TOKENS: Final = "tokens-per-second"
MODE_SCAN: Final = "scan-latency"

VECTOR_INT8: Final = "int8"
VECTOR_BIT: Final = "bit"

CACHE_WARM: Final = "warm"
CACHE_COLD: Final = "cold"
CACHE_BOTH: Final = "both"

# The width of intfloat/multilingual-e5-small and the width plan 06-04 proposes
# its vector column with. It is a constant of the model, not a knob.
DIMENSIONS: Final = 384

# k of the KNN query. 50 is the window depth a hybrid rank needs per source
# before the RRF merge of D-12 thins it out again, so it is the k a user search
# would really ask for rather than a round number.
NEIGHBOURS: Final = 50

# The series the scan is measured over.
#
# 100000 is in here by name and it is the one entry that is not free choice:
# success criterion 4 of this phase fixes the vector schema only after a load
# test over at least 50.000 synthetic documents, and at the two chunk cap of
# D-01 that is 100.000 chunks. The 1.000.000 at the end is the honest other
# side, roughly the full embedding of the same holding without the cap, and it
# is what says whether the brute force path has any headroom at all.
DEFAULT_SIZES: Final = (50_000, 100_000, 250_000, 1_000_000)

# A megabyte of German, which is what 06-RESEARCH.md 3.7 asks for. The reference
# corpus of this repository is far smaller than that, so the limit is a ceiling
# and the output states the number of characters that were really read.
DEFAULT_CHARACTER_LIMIT: Final = 1_000_000

# Batch size and sequence length are levers 4 and 5 of 06-RESEARCH.md 3.6, and
# they trade throughput against the activation peak. The defaults are the shape
# the small box variant of research/STACK.md names.
DEFAULT_BATCH: Final = 8
DEFAULT_SEQUENCE: Final = 512

# Two shared cores is the hardware assumption A2 is written against, so it is the
# default the number is produced under. Anything else has to be said out loud on
# the command line and travels into the output.
DEFAULT_THREADS: Final = 2

DEFAULT_SCAN_QUERIES: Final = 100
DEFAULT_TOKEN_ROUNDS: Final = 20

TABLE: Final = "chunk_vectors"
ROW_SCAN: Final = "scan"

SEED: Final = "phase6-welle0-bench"

# The kernel switch that empties the page cache. Writing "3" drops the clean page
# cache plus the dentry and inode caches. It needs root, it does not exist
# outside Linux, and both of those are ordinary outcomes rather than errors, see
# drop_page_cache below.
DROP_CACHES: Final = Path("/proc/sys/vm/drop_caches")

ENV_MODEL: Final = "FINDLING_EMBED_MODEL_DIR"
ENV_VEC0: Final = "FINDLING_VEC0_PATH"

# Fixed synthetic German prose for the throughput mode, written without umlauts
# the same way index/bench.py is, so that the workload is byte identical on every
# machine and reveals nothing about any real document.
_SENTENCES: Final = (
    "Die Kuendigungsfrist betraegt drei Monate und beginnt am Ersten des Monats.",
    "Die Rechnung wurde im Jahresabschluss der Verwaltung geprueft und freigegeben.",
    "Der Vertrag regelt die Betriebskosten, die Nebenkosten und die Kaution.",
    "Die Sitzungsvorlage des Ausschusses nennt den Haushalt und die Satzung.",
)

# Suffixes the character mode reads. Deliberately short: this mode measures a
# tokenizer over plain German, and an extraction pipeline in front of it would
# add its own decisions (page order, table flattening, OCR) to a number that is
# supposed to be about the tokenizer alone.
_TEXT_SUFFIXES: Final = (".txt", ".text", ".md")


class BenchError(Exception):
    """A named refusal: the tool is missing an input it cannot invent.

    Every one of these would otherwise end as a zero somewhere in the statistics,
    and a zero is the one value that looks like a measurement and is not.
    """


# -- hardware --------------------------------------------------------------


def architecture() -> str:
    """``uname -m``, which is the half of the hardware that decides two of three numbers."""
    return platform.machine()


def visible_cpus() -> int:
    """The CPUs this process may run on, not the ones the machine has.

    The difference is the whole point on a container with a cpu set and on the
    two shared cores A2 is written against: ``os.cpu_count`` reports the host,
    ``sched_getaffinity`` reports the allowance. The second is the number the
    throughput was really produced with.
    """
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        return len(affinity(0))
    return os.cpu_count() or 1


def hardware_lines() -> list[str]:
    return [
        f"arch={architecture()}",
        f"cpus={visible_cpus()}",
        f"python={sys.version.split()[0]}",
        f"sqlite={sqlite3.sqlite_version}",
    ]


def _percentile(samples: Sequence[float], fraction: float) -> float:
    """Nearest rank percentile, so a p95 over 100 samples is a real sample."""
    ordered = sorted(samples)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


# -- the two image constants -----------------------------------------------


def model_directory() -> Path:
    """Where the model is, and no guess if nobody said.

    In the image this is a constant set by the Dockerfile. Outside it there is no
    model at all, and a fallback that quietly reached for a download would turn a
    measurement of the shipped artefact into a measurement of whatever happened
    to be on the network that day.
    """
    value = os.environ.get(ENV_MODEL)
    if not value:
        raise BenchError(f"{ENV_MODEL} is not set, so there is no model to measure")
    directory = Path(value)
    if not directory.is_dir():
        raise BenchError(f"{ENV_MODEL} points at {value}, which is not a directory")
    return directory


def load_tokenizer(directory: Path) -> Tokenizer:
    path = directory / "tokenizer.json"
    if not path.is_file():
        raise BenchError(f"tokenizer.json is missing under {ENV_MODEL}")
    return Tokenizer.from_file(str(path))


def extension_path() -> str:
    """Where vec0 is. Same argument as above, and one more.

    The A12 probe falls back to the extension of the installed wheel so that it
    is not a test that quietly does nothing on a developer machine. This tool
    does not, because its output is a number that goes into a report: a scan
    latency measured against some other copy of the extension would be a number
    about a file nobody can name afterwards.
    """
    value = os.environ.get(ENV_VEC0)
    if not value:
        raise BenchError(f"{ENV_VEC0} is not set, so there is no extension to measure against")
    return value


# -- mode A: characters per token ------------------------------------------


def _decode(raw: bytes) -> str:
    """utf-8 first, cp1252 second, and never a dropped file.

    German holdings from before 2010 are full of cp1252, and the reference corpus
    carries one such file on purpose. A reader that only knew utf-8 would either
    raise or skip, and a skipped file is a silently smaller sample behind an
    unchanged looking number.
    """
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def _text_files(source: Path) -> Iterator[Path]:
    if source.is_file():
        yield source
        return
    for path in sorted(source.rglob("*")):
        if path.is_file() and path.suffix.lower() in _TEXT_SUFFIXES:
            yield path


def read_text(source: Path, limit: int) -> tuple[str, int]:
    """Read German text up to ``limit`` characters and say how many files it took.

    The return value carries the count and never the names. That is the whole
    contract of this function: the caller is a measurement whose output is
    published, and a file name in a published measurement is the leak T-06-06
    describes.
    """
    if not source.exists():
        raise BenchError(f"the text source does not exist ({ENV_MODEL} side inputs are not involved here)")

    collected: list[str] = []
    characters = 0
    files = 0
    for path in _text_files(source):
        try:
            piece = _decode(path.read_bytes())
        except OSError:
            continue
        if not piece:
            continue
        files += 1
        remaining = limit - characters
        if len(piece) > remaining:
            piece = piece[:remaining]
        collected.append(piece)
        characters += len(piece)
        if characters >= limit:
            break

    if characters == 0:
        raise BenchError("no readable text was found in the given source")
    return "".join(collected), files


def run_chars_per_token(model_dir: Path, source: Path, *, limit: int) -> list[str]:
    """A1. Characters divided by tokens, over real German, with nothing else printed.

    The quotient is formed over the totals and not as a mean of per file
    quotients: a mean would weight a two line note the same as a ten page
    decision, and the number is used to convert 1.355.205.169 characters into
    tokens.

    Special tokens are switched off. The real encoder adds ``<s>`` and ``</s>``
    per call, and counting those would make the ratio depend on how the text
    happened to be split into files.
    """
    tokenizer = load_tokenizer(model_dir)
    text, files = read_text(source, limit)

    started = time.perf_counter()
    tokens = len(tokenizer.encode(text, add_special_tokens=False).ids)
    elapsed = time.perf_counter() - started
    if tokens == 0:
        raise BenchError("the tokenizer produced no tokens for the text that was read")

    return [
        f"mode={MODE_CHARS}",
        *hardware_lines(),
        f"model_dir={model_dir}",
        f"vocabulary={tokenizer.get_vocab_size()}",
        f"files={files}",
        f"characters={len(text)}",
        f"tokens={tokens}",
        f"chars_per_token={len(text) / tokens:.4f}",
        f"tokenize_seconds={elapsed:.3f}",
    ]


# -- mode B: tokens per second ---------------------------------------------


def synthetic_batch(tokenizer: Tokenizer, *, batch: int, sequence: int) -> list[list[int]]:
    """``batch`` rows of exactly ``sequence`` token ids, with no padding anywhere.

    No padding is the point. A padded batch spends its arithmetic on positions
    that carry nothing, and the tokens per second would then be quoted over
    tokens that were never text. The fixed prose above is repeated until there
    are enough ids and then cut to length, so every row is full and every run on
    every machine sees the identical workload.
    """
    if batch < 1 or sequence < 1:
        raise BenchError(f"batch and sequence have to be positive, got batch={batch} sequence={sequence}")

    ids: list[int] = []
    round_number = 0
    while len(ids) < sequence:
        text = " ".join(_SENTENCES[(round_number + index) % len(_SENTENCES)] for index in range(len(_SENTENCES)))
        ids.extend(tokenizer.encode(text, add_special_tokens=False).ids)
        round_number += 1
        if round_number > sequence:  # pragma: no cover - a tokenizer that returns nothing
            raise BenchError("the tokenizer produced no ids for the synthetic text")
    return [ids[:sequence] for _ in range(batch)]


def run_tokens_per_second(
    model_dir: Path,
    *,
    run_batch: Callable[[list[list[int]]], None],
    batch: int,
    sequence: int,
    rounds: int,
    threads: int,
) -> list[str]:
    """A2 and A3. How many tokens a second this model produces on this hardware.

    ``run_batch`` is handed in rather than built here so that the arithmetic
    around it can be tested without the 118 MB model, which is a constant of the
    image and which no test in this repository downloads. :func:`main` builds the
    real one over onnxruntime.

    **Why onnxruntime directly and not fastembed**, stated because fastembed is
    what the search path will use. Two reasons, and the second is the deciding
    one. The batch size and the sequence length are levers 4 and 5 of
    06-RESEARCH.md 3.6 and this measurement exists to put numbers on them;
    fastembed picks both itself and offers no way to fix them. And the model is
    registered with fastembed by plan 06-05, which does not exist yet, so going
    through it would mean writing that registration here and measuring it twice.
    What the number therefore excludes is fastembed's own Python overhead around
    the session, which is a per batch cost and not a per token one. The report
    says so beside the number.

    One warm up round runs before the measured ones and is thrown away. The first
    call through onnxruntime allocates the arena and pages in the weights, so
    counting it would put the load time into the throughput.
    """
    if rounds < 1:
        raise BenchError(f"rounds has to be at least 1, got {rounds}")

    tokenizer = load_tokenizer(model_dir)
    ids = synthetic_batch(tokenizer, batch=batch, sequence=sequence)
    tokens_per_round = batch * sequence

    run_batch(ids)

    durations: list[float] = []
    started = time.perf_counter()
    for _ in range(rounds):
        round_started = time.perf_counter()
        run_batch(ids)
        durations.append((time.perf_counter() - round_started) * 1000)
    wall = time.perf_counter() - started

    p50 = statistics.median(durations)
    p95 = _percentile(durations, 0.95)
    return [
        f"mode={MODE_TOKENS}",
        *hardware_lines(),
        f"model_dir={model_dir}",
        f"batch={batch}",
        f"sequence={sequence}",
        f"threads={threads}",
        f"rounds={rounds}",
        f"tokens_per_round={tokens_per_round}",
        f"tokens_total={tokens_per_round * rounds}",
        f"p50_ms={p50:.3f}",
        f"p95_ms={p95:.3f}",
        f"max_ms={max(durations):.3f}",
        # The p95 duration is the slow round, so the throughput printed next to
        # it is the low one. A p95 of a throughput quoted from the fast end would
        # be the most flattering number in this file and the least useful.
        f"tokens_per_second_p50={tokens_per_round / (p50 / 1000):.1f}",
        f"tokens_per_second_p95={tokens_per_round / (p95 / 1000):.1f}",
        f"tokens_per_second_mean={tokens_per_round * rounds / wall:.1f}",
        f"wall_seconds={wall:.3f}",
    ]


def onnx_run_batch(model_dir: Path, threads: int) -> Callable[[list[list[int]]], None]:
    """The real inference call, one session, reused for every round.

    onnxruntime and numpy are imported here and not at the top of the module:
    they weigh well over a hundred megabytes together, and the scan latency mode
    has no use for either.
    """
    path = model_dir / "model.onnx"
    if not path.is_file():
        raise BenchError(f"model.onnx is missing under {ENV_MODEL}")

    import numpy
    import onnxruntime

    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    session = onnxruntime.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])
    accepted = {item.name for item in session.get_inputs()}
    outputs = [session.get_outputs()[0].name]

    def run_batch(ids: list[list[int]]) -> None:
        block = numpy.asarray(ids, dtype=numpy.int64)
        feed = {
            "input_ids": block,
            "attention_mask": numpy.ones_like(block),
            "token_type_ids": numpy.zeros_like(block),
        }
        session.run(outputs, {name: value for name, value in feed.items() if name in accepted})

    return run_batch


# -- mode C: scan latency ---------------------------------------------------


def vector(index: int, width: int) -> bytes:
    """One deterministic vector of ``width`` bytes.

    SHA-256 in counter mode rather than the standard library generator, the same
    construction the corpus builder and the A12 probe use: the bytes have to be
    identical on every machine and in every year, and both an int8 vector and a
    bit vector are raw bytes to sqlite-vec, so no float conversion sits in
    between.
    """
    raw = b""
    counter = 0
    while len(raw) < width:
        raw += hashlib.sha256(f"{SEED}:{index}:{counter}".encode()).digest()
        counter += 1
    return raw[:width]


def vector_bytes(vector_type: str) -> int:
    """384 bytes for int8, 48 for bit. The factor of eight is the whole comparison."""
    if vector_type == VECTOR_BIT:
        return DIMENSIONS // 8
    return DIMENSIONS


def _column(vector_type: str) -> str:
    return f"{TABLE} USING vec0(embedding {vector_type}[{DIMENSIONS}])"


def _wrap(vector_type: str) -> str:
    """sqlite-vec does not infer the element type from the column declaration.

    A bare blob in an int8 column is read as float32 and refused, which is a
    finding of the A12 probe and the reason this is a function rather than a
    literal in one place.
    """
    return "vec_bit" if vector_type == VECTOR_BIT else "vec_int8"


def open_database(database: Path, extension: str) -> sqlite3.Connection:
    """Open the scratch database with vec0 loaded, or say why it could not be."""
    connection = sqlite3.connect(database)
    try:
        connection.enable_load_extension(True)
        connection.load_extension(extension)
        connection.enable_load_extension(False)
    except (AttributeError, sqlite3.Error) as error:
        connection.close()
        named = f"{type(error).__name__}: {error}"
        raise BenchError(f"the extension at {extension} could not be loaded: {named}") from error
    return connection


def _rows_for(size: int, width: int) -> Iterable[tuple[int, bytes]]:
    """A generator, so a million vectors never stand in memory at once.

    At the largest size of the default series that would be 384 MB of Python
    objects next to the 384 MB the database file is about to hold, on a runner
    that also has to keep the page cache the measurement is about.
    """
    for index in range(size):
        yield index + 1, vector(index, width)


def fill(connection: sqlite3.Connection, *, size: int, vector_type: str) -> None:
    """Write ``size`` vectors into a fresh vec0 table.

    Journal and synchronous are switched off for the fill. This is a scratch
    database in a temporary directory that is deleted at the end of the run, so
    there is nothing to survive a crash, and the fill is not what is being
    measured.
    """
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute(f"CREATE VIRTUAL TABLE {_column(vector_type)}")
    with connection:
        # S608 is muted here and at the query below, and the reason is the same
        # in both places: the two interpolated pieces are a module constant and
        # the return value of _wrap, which is one of two literals chosen by a
        # value argparse restricted to int8 and bit. Nothing on this line ever
        # came from a request; this tool has no request path at all.
        connection.executemany(
            f"INSERT INTO {TABLE}(rowid, embedding) VALUES (?, {_wrap(vector_type)}(?))",  # noqa: S608
            _rows_for(size, vector_bytes(vector_type)),
        )


def query_once(connection: sqlite3.Connection, *, vector_type: str, number: int) -> int:
    """One KNN query for ``NEIGHBOURS`` neighbours, and how many came back.

    The query vector is derived from ``number`` so that a series of queries does
    not ask the same question a hundred times and measure a cache of answers. It
    is drawn from beyond the filled range, so it is never an exact hit.
    """
    rows = connection.execute(
        f"SELECT rowid FROM {TABLE} WHERE embedding MATCH {_wrap(vector_type)}(?) AND k = ?",  # noqa: S608
        (vector(-number - 1, vector_bytes(vector_type)), NEIGHBOURS),
    ).fetchall()
    return len(rows)


def drop_page_cache() -> tuple[bool, str | None]:
    """Try to empty the page cache and report whether it worked. Never raises.

    T-06-09 is the threat this pair exists for: a cold run that silently reports
    a warm number is the one failure of this tool nobody would notice, because
    the number looks perfectly reasonable. Three of the places this runs cannot
    do it at all (Windows, an unprivileged container, a machine without root),
    and all three are ordinary outcomes rather than errors, so the caller gets a
    fact it can write down instead of an exception it would have to swallow.
    """
    if not DROP_CACHES.exists():
        return False, f"{DROP_CACHES} does not exist on this system"
    # os.sync exists on POSIX only, and it has to run first: dirty pages are not
    # dropped, so an unflushed write would survive the drop and the next read
    # would come out of memory after all.
    flush = getattr(os, "sync", None)
    try:
        if flush is not None:
            flush()
        DROP_CACHES.write_text("3\n", encoding="ascii")
    except OSError as error:
        return False, f"{type(error).__name__}: {error}"
    return True, None


def _measure_series(
    database: Path,
    extension: str,
    *,
    vector_type: str,
    queries: int,
    cold: bool,
) -> tuple[list[float], int, str, str | None]:
    """One series of queries against one filled database, warm or cold.

    Cold means cold for every single query, not once at the start. Dropping the
    cache once and then running a hundred queries measures one cold query and
    ninety nine warm ones, and the p50 of that is a warm number wearing a cold
    label. So the cache is dropped and the connection reopened before each
    measured query, which is expensive and is the only version of "cold" that
    means anything.
    """
    durations: list[float] = []
    neighbours = 0
    dropped = True
    note: str | None = None

    if not cold:
        connection = open_database(database, extension)
        try:
            for warmup in range(3):
                neighbours = query_once(connection, vector_type=vector_type, number=warmup)
            for number in range(queries):
                started = time.perf_counter()
                neighbours = query_once(connection, vector_type=vector_type, number=number)
                durations.append((time.perf_counter() - started) * 1000)
        finally:
            connection.close()
        # Not "true": a warm series drops nothing, and a true here would read as
        # if it had. The field belongs to the cold series and says so.
        return durations, neighbours, "n/a", None

    for number in range(queries):
        this_drop, this_note = drop_page_cache()
        dropped = dropped and this_drop
        note = note or this_note
        connection = open_database(database, extension)
        try:
            started = time.perf_counter()
            neighbours = query_once(connection, vector_type=vector_type, number=number)
            durations.append((time.perf_counter() - started) * 1000)
        finally:
            connection.close()
    return durations, neighbours, "true" if dropped else "false", note


def run_scan_latency(
    extension: str,
    *,
    directory: Path,
    sizes: Sequence[int],
    queries: int,
    vector_type: str,
    cache: str,
) -> list[str]:
    """C. How long a full brute force scan takes, per size and per cache state.

    One fill per size, and the warm and the cold series run over that same fill
    when ``--cache both`` is given. Two separately filled tables would carry the
    fill variance into a difference that is supposed to be the cache and nothing
    else (06-RESEARCH.md 2.2: the difference is the statement, not the mean).

    The database file is deleted after each size. At the largest size of the
    default series it holds roughly 384 MB, and four of them at once on a runner
    would be the measurement competing with itself for the page cache.
    """
    if queries < 1:
        raise BenchError(f"queries has to be at least 1, got {queries}")
    if vector_type not in (VECTOR_INT8, VECTOR_BIT):
        raise BenchError(f"unknown vector type {vector_type!r}")

    states = {CACHE_WARM: [CACHE_WARM], CACHE_COLD: [CACHE_COLD], CACHE_BOTH: [CACHE_WARM, CACHE_COLD]}[cache]
    width = vector_bytes(vector_type)

    lines = [
        f"mode={MODE_SCAN}",
        *hardware_lines(),
        f"vec0_path={extension}",
        f"vector_type={vector_type}",
        f"dimensions={DIMENSIONS}",
        f"vector_bytes={width}",
        f"k={NEIGHBOURS}",
        f"queries={queries}",
        f"cache={cache}",
    ]

    for size in sizes:
        database = directory / f"scan-{vector_type}-{size}.db"
        database.unlink(missing_ok=True)
        connection = open_database(database, extension)
        fill_started = time.perf_counter()
        try:
            fill(connection, size=size, vector_type=vector_type)
        finally:
            connection.close()
        fill_seconds = time.perf_counter() - fill_started
        file_bytes = database.stat().st_size

        try:
            for state in states:
                durations, neighbours, dropped, note = _measure_series(
                    database,
                    extension,
                    vector_type=vector_type,
                    queries=queries,
                    cold=state == CACHE_COLD,
                )
                row = [
                    ROW_SCAN,
                    f"size={size}",
                    f"cache={state}",
                    f"cache_dropped={dropped}",
                    f"p50_ms={statistics.median(durations):.3f}",
                    f"p95_ms={_percentile(durations, 0.95):.3f}",
                    f"max_ms={max(durations):.3f}",
                    f"neighbours={neighbours}",
                    f"scanned_bytes={size * width}",
                    f"file_bytes={file_bytes}",
                    f"fill_seconds={fill_seconds:.3f}",
                ]
                lines.append(" ".join(row))
                if state == CACHE_COLD and dropped != "true":
                    # The word the report greps for. A cold series that could not
                    # be cold has to be unquotable as one, and a flag inside a
                    # row is easy to lose beside a plausible number.
                    lines.append(f"cold_not_enforced size={size} reason={note}")
        finally:
            database.unlink(missing_ok=True)

    return lines


# -- the command line -------------------------------------------------------


def _sizes(value: str) -> tuple[int, ...]:
    try:
        parsed = tuple(int(part) for part in value.split(",") if part.strip())
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"{value!r} is not a comma separated list of integers") from error
    if not parsed:
        raise argparse.ArgumentTypeError("at least one size is needed")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure the three wave 0 numbers of the semantic search.")
    parser.add_argument("--mode", choices=(MODE_CHARS, MODE_TOKENS, MODE_SCAN), default=MODE_CHARS)
    parser.add_argument(
        "--text-dir",
        type=Path,
        default=Path("testdata/corpus"),
        help="German text for chars-per-token, a directory or a single file",
    )
    parser.add_argument("--characters", type=int, default=DEFAULT_CHARACTER_LIMIT, help="ceiling for chars-per-token")
    parser.add_argument("--sizes", type=_sizes, default=DEFAULT_SIZES, help="vector counts for scan-latency")
    parser.add_argument(
        "--queries",
        type=int,
        default=None,
        help="measured repetitions: KNN queries for scan-latency, batches for tokens-per-second",
    )
    parser.add_argument("--vector-type", choices=(VECTOR_INT8, VECTOR_BIT), default=VECTOR_INT8)
    parser.add_argument("--cache", choices=(CACHE_WARM, CACHE_COLD, CACHE_BOTH), default=CACHE_BOTH)
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH, help="batch size for tokens-per-second")
    parser.add_argument("--sequence", type=int, default=DEFAULT_SEQUENCE, help="sequence length for tokens-per-second")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS, help="intra op threads for tokens-per-second")
    parser.add_argument("--db-dir", type=Path, default=None, help="reuse a directory instead of a temporary one")
    return parser


def _run(args: argparse.Namespace, scratch: Path) -> list[str]:
    if args.mode == MODE_CHARS:
        return run_chars_per_token(model_directory(), args.text_dir, limit=args.characters)
    if args.mode == MODE_TOKENS:
        model_dir = model_directory()
        return run_tokens_per_second(
            model_dir,
            run_batch=onnx_run_batch(model_dir, args.threads),
            batch=args.batch,
            sequence=args.sequence,
            rounds=DEFAULT_TOKEN_ROUNDS if args.queries is None else args.queries,
            threads=args.threads,
        )
    return run_scan_latency(
        extension_path(),
        directory=scratch,
        sizes=args.sizes,
        queries=DEFAULT_SCAN_QUERIES if args.queries is None else args.queries,
        vector_type=args.vector_type,
        cache=args.cache,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.db_dir is not None:
            # The directory has to exist already, and this module deliberately
            # does not create it. mkdir is a forbidden identifier of the
            # read-only gate (IDX-07, invariant 2), and a measuring tool is not a
            # good enough reason to add a fifth reviewed exception to a list that
            # exists to keep a Nextcloud write from hiding behind a local one.
            # The caller of the workflow owns the directory anyway.
            if not args.db_dir.is_dir():
                raise BenchError(f"--db-dir {args.db_dir} does not exist, and this tool does not create directories")
            lines = _run(args, args.db_dir)
        else:
            with tempfile.TemporaryDirectory(prefix="findling-embed-bench-", ignore_cleanup_errors=True) as scratch:
                lines = _run(args, Path(scratch))
    except BenchError as error:
        print(f"measurement refused: {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
