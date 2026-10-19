#!/usr/bin/env python3
"""The int8 L2 distances of relevant and of unrelated pairs, on the scale the stock ranks on.

One question is answered here, and it is the question a threshold needs answered
before it may exist: how far apart does this model put a query and the section it
means, and how far apart does it put a query and a section it has nothing to do
with. Without those two distributions any cutoff is a preference with a decimal
point.

**Two populations, and the second one is the one the defect is about.**

The first is the three language test set under ``testdata/semantik``. For every
query of one file: the distance to its own section (the relevant pair) and the
distances to every other section of the same file (the distractors). That
population says where a threshold may not be put, because a threshold below a
relevant pair costs a hit the search finds today.

The second is the end to end corpus of ``scripts/dev/build_corpus.py``. Its texts
are cut with the real chunker of this repository and embedded as passages, so the
numbers are the numbers of the stock and not of a reproduction. That population
says where a threshold has to be put, because the one word probes of the
integration run must not produce a single semantic candidate on it.

**The reservation belongs here and not in the small print.** The texts of the
image files are the intended texts of the generator, not the output of tesseract,
so this path carries no OCR noise. It decides the threshold, the end to end run
proves it.

**What this prints, and what it never prints.** Numbers, paths and identifiers.
Never a query and never a section, of either population. This path sees the same
shape of text a production index sees, and a measurement that prints what it read
is the cheapest way to lose content (T-02-14, T-06-11, T-06.1-86). A case is
named by its identifier, a corpus chunk by its file name and its ordinal.

**The distance is not recomputed here, it is verified against the store.** The
stock ranks under ``vec_distance_l2`` over an ``int8[384]`` column, and every
number below is computed in this process instead of in sqlite. ``--selftest``
therefore puts known vectors into a real :class:`~findling.store.vectors.VectorStore`,
lets ``nearest`` answer, and compares the two to the last digit. A tool that
rebuilds the metric of the stock instead of agreeing with it measures a search
this container does not run.

Run it, from anywhere, with the environment of the backend::

    cd backend
    uv run python ../scripts/dev/vector_distances.py --selftest
    uv run python ../scripts/dev/vector_distances.py --testset \\
        --model-dir /path/to/model --dataset-dir ../testdata/semantik
    uv run python ../scripts/dev/vector_distances.py --corpus \\
        --model-dir /path/to/model
    uv run python ../scripts/dev/vector_distances.py --derive \\
        --model-dir /path/to/model --dataset-dir ../testdata/semantik
    uv run python ../scripts/dev/vector_distances.py --similar --derive \\
        --model-dir /path/to/model --dataset-dir ../testdata/semantik \\
        --groups ../docs/measurements/2026-10-aehnlich-distanzen/gruppen.tsv

**The similar mode** (Plan 35-04) asks document against document instead of
query against section: the query text and the section of one case are both
embedded as passages, the sections of different cases are the unrelated pairs,
and the corpus documents are compared through
:func:`findling.index.fusion.centroid`, the very function the similar view
runs. Its rule stands in docs/measurements/2026-10-aehnlich-distanzen/README.md
and was committed before this mode existed.

**The version mode** (Plan 35-04B, the owner's way 2) measures real document
pairs: per language the sections of the test set are shuffled with seed 3504
into blocks of four, a base document joins the four, its version drops one
drawn section and reverses the other three. Base against version is the
related pair, documents of different blocks are the unrelated pairs, both
compared centroid against centroid. Its rule stands in section 10.1 of the same
report and was committed before this mode existed::

    uv run python ../scripts/dev/vector_distances.py --versions --derive \\
        --model-dir /path/to/model --dataset-dir ../testdata/semantik \\
        --groups ../docs/measurements/2026-10-aehnlich-distanzen/gruppen.tsv
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import random
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np

REPOSITORY: Final = Path(__file__).resolve().parents[2]
BACKEND_SOURCE: Final = REPOSITORY / "backend" / "src"
DEV_SCRIPTS: Final = REPOSITORY / "scripts" / "dev"

# The backend package and the corpus generator both live outside this file's own
# import root. Added here rather than expected from the caller, so that the tool
# runs the same way from anywhere, which is what makes a command line in the
# report reproducible.
for entry in (BACKEND_SOURCE, DEV_SCRIPTS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from findling.embed.chunker import chunk_spans, make_splitter  # noqa: E402
from findling.embed.model import DIMENSIONS, EmbeddingModel, open_tokenizer, to_int8  # noqa: E402
from findling.index.fusion import centroid  # noqa: E402

# The three files of the test set, in the order the report tabulates them.
LANGUAGES: Final = ("de", "en", "fr")

# The probes of the second population. Five one word lines out of the seven
# German cases of the integration run, plus the paraphrase of the two semantic
# steps. The one word probes must end with no neighbour at all under the ceiling;
# the paraphrase must keep its document.
ONE_WORD_PROBES: Final = ("Genehmigung", "Frist", "Mueller", "Vertrag", "bescheid")
PARAPHRASE_PROBE: Final = "Wann darf ich meinen Job aufgeben und wie lange muss ich vorher warten"
PARAPHRASE_WANTS: Final = "10-kuendigung.docx"

# How many neighbours of one probe the corpus table reports.
CORPUS_NEIGHBOURS: Final = 10

# The mimetype of every corpus file whose text is read with the real extractors
# of this container rather than taken from the generator's literals. The image
# files are absent on purpose: their text is the intended text, see the
# reservation in the module head.
CORPUS_MIMETYPES: Final = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text",
    "txt": "text/plain",
}

# The caps the container runs the second track under. Read from the settings of
# this process, so a measurement cannot silently use a different chunking than
# the stock it is meant to describe.
BATCH_SIZE: Final = 16

# The grid the derivation searches. The metric maxes out at 254 (two opposite
# int8 vectors of unit length), and the step is fine enough that the chosen pair
# is not an artefact of the raster.
GRID_STEP: Final = 0.5
METRIC_MAXIMUM: Final = 254.0

# How many digits every number of this tool carries. Four is one more than the
# report quotes, so that a rounded number in the prose can be checked against the
# output it came from.
DIGITS: Final = 4

# Floating point slack when two hit rates are compared, and nothing else. A
# permitted loss would be a way to soften constraint (A) without saying so.
TOLERANCE: Final = 1e-9


class MeasurementError(Exception):
    """A named refusal. Never a zero in the statistics, always a non zero exit."""


@dataclass(frozen=True)
class Summary:
    """One distribution, as the five numbers the report tabulates."""

    count: int
    minimum: float
    p05: float
    median: float
    p95: float
    maximum: float


@dataclass(frozen=True)
class LanguageMeasurement:
    """What one language file came to.

    ``matrix`` holds one row per query and one column per section of the same
    file, so row i column i is the relevant pair and every other column of that
    row is a distractor. The whole matrix is kept rather than two summaries of
    it, because the derivation below has to rank the surviving candidates of one
    query against each other and a summary cannot be ranked.
    """

    language: str
    identifiers: tuple[str, ...]
    matrix: np.ndarray

    @property
    def cases(self) -> int:
        return int(self.matrix.shape[0])

    @property
    def relevant(self) -> np.ndarray:
        """One distance per case: the query against the section it means."""
        return np.diagonal(self.matrix).copy()

    @property
    def distractors(self) -> np.ndarray:
        """Every other section of the same file, one row per case."""
        rows = [np.delete(self.matrix[position], position) for position in range(self.cases)]
        return np.array(rows, dtype=np.float64)

    @property
    def overlap(self) -> int:
        """How many distractors lie closer to a query than its own section."""
        closer = self.matrix < self.relevant[:, None]
        return int(np.count_nonzero(closer))


@dataclass(frozen=True)
class CorpusChunk:
    """One chunk of one corpus file, by name and ordinal. Never by text."""

    name: str
    ordinal: int
    vector: bytes


@dataclass(frozen=True)
class ProbeMeasurement:
    """One probe against the corpus stock, as its nearest neighbours."""

    probe: str
    names: tuple[str, ...]
    ordinals: tuple[int, ...]
    distances: tuple[float, ...]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure the int8 L2 distances of relevant and unrelated pairs.",
    )
    parser.add_argument("--selftest", action="store_true", help="verify the distance against a real vector store")
    parser.add_argument("--testset", action="store_true", help="the three language files of testdata/semantik")
    parser.add_argument("--corpus", action="store_true", help="the probes against the texts of the e2e corpus")
    parser.add_argument("--derive", action="store_true", help="both populations plus the admissible grid")
    parser.add_argument(
        "--similar",
        action="store_true",
        help="document against document, for the similar documents ceiling (with --derive: derive it)",
    )
    parser.add_argument(
        "--versions",
        action="store_true",
        help="a base document against its own version, for the ceiling of Plan 35-04B (with --derive: derive it)",
    )
    parser.add_argument("--groups", type=Path, default=None, help="the topic group table of the e2e corpus (tsv)")
    parser.add_argument("--model-dir", type=Path, default=None, help="the directory holding model.onnx and tokenizer")
    parser.add_argument("--dataset-dir", type=Path, default=None, help="the directory holding de.jsonl and friends")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# The metric, and the proof that it is the metric of the stock
# ---------------------------------------------------------------------------


def as_components(vector: bytes) -> np.ndarray:
    """The signed components of one stored vector, as float for the arithmetic."""
    if len(vector) != DIMENSIONS:
        message = f"a vector of {len(vector)} bytes, expected {DIMENSIONS}"
        raise MeasurementError(message)
    return np.frombuffer(vector, dtype=np.int8).astype(np.float64)


def l2_distance(left: bytes, right: bytes) -> float:
    """The distance ``vec_distance_l2`` answers for two ``int8[384]`` values.

    Euclidean over the stored components, which are whole numbers in [-128, 127]
    because :func:`findling.embed.model.to_int8` scales a normalised vector by
    127. The scale is what fixes the range of every threshold built on this
    number: 0 for identical, 127*sqrt(2) = 179.6 for orthogonal, 254 for
    opposite.
    """
    difference = as_components(left) - as_components(right)
    return float(np.sqrt(np.dot(difference, difference)))


def distances_to(query: bytes, stock: Sequence[bytes]) -> np.ndarray:
    """One row of distances, in the order of the stock."""
    return np.array([l2_distance(query, entry) for entry in stock], dtype=np.float64)


def _axis_vector(axis: int, sign: float = 1.0) -> bytes:
    """One normalised vector along a single axis, in the form the store takes."""
    return to_int8(tuple(sign if index == axis else 0.0 for index in range(DIMENSIONS)))


def _mixed_vector(first: int, second: int) -> bytes:
    """A normalised vector between two axes, so the selftest has a middle case."""
    share = 1.0 / np.sqrt(2.0)
    return to_int8(
        tuple(share if index in (first, second) else 0.0 for index in range(DIMENSIONS)),
    )


def selftest() -> str:
    """Compare this module's arithmetic against ``nearest`` of a real store.

    The one case of this tool that cannot be replaced by a stand-in. A stand-in
    would answer whatever this file computes, and the whole point of the
    comparison is that the stock has an opinion of its own: the metric is a
    property of the vec0 column, not of this process.
    """
    from findling.store.vectors import Chunk, open_vectors

    query = _axis_vector(0)
    stock = {
        1: _axis_vector(0),
        2: _mixed_vector(0, 1),
        3: _axis_vector(1),
        4: _axis_vector(0, sign=-1.0),
    }

    lines = ["selftest      the distance of this tool against nearest() of a real store"]
    with tempfile.TemporaryDirectory() as directory:
        vectors = open_vectors(Path(directory) / "vectors.db")
        try:
            for file_id, vector in stock.items():
                vectors.replace_chunks(file_id, [Chunk(ordinal=0, char_start=0, char_end=1, embedding=vector)])
            answered = vectors.nearest(query, len(stock), k_max=len(stock))
        finally:
            vectors.close()

    if len(answered) != len(stock):
        message = f"the store answered {len(answered)} neighbours for a stock of {len(stock)}"
        raise MeasurementError(message)

    ascending = [neighbour.distance for neighbour in answered]
    if ascending != sorted(ascending):
        message = "the store answered its neighbours out of order"
        raise MeasurementError(message)

    for neighbour in answered:
        own = l2_distance(query, stock[neighbour.file_id])
        lines.append(f"file {neighbour.file_id}        store {neighbour.distance:.{DIGITS}f}  own {own:.{DIGITS}f}")
        if abs(own - neighbour.distance) > 1e-4:
            message = f"file {neighbour.file_id}: the store says {neighbour.distance}, this tool says {own}"
            raise MeasurementError(message)

    lines.append(f"maximum       {max(ascending):.{DIGITS}f} of the metric maximum {METRIC_MAXIMUM:.{DIGITS}f}")
    lines.append("verdict       the tool and the store agree to four digits")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Population one: the three language test set
# ---------------------------------------------------------------------------


def load_dataset(path: Path) -> list[dict[str, str]]:
    """The cases of one language file, or a named refusal."""
    if not path.is_file():
        message = f"dataset not found: {path}"
        raise MeasurementError(message)
    records: list[dict[str, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            message = f"{path.name} line {number} is not valid JSON: {error.msg}"
            raise MeasurementError(message) from error
        missing = {"id", "query", "passage"} - set(record)
        if missing:
            message = f"{path.name} line {number} is missing the fields {sorted(missing)}"
            raise MeasurementError(message)
        records.append(record)
    if not records:
        message = f"dataset is empty: {path}"
        raise MeasurementError(message)
    return records


def _vectors_of(outcome_vectors: Sequence[Sequence[float]]) -> list[bytes]:
    return [to_int8(vector) for vector in outcome_vectors]


def _embed_passages(model: EmbeddingModel, texts: Sequence[str]) -> list[bytes]:
    outcome = model.embed_passages(list(texts))
    if not outcome.available or len(outcome.vectors) != len(texts):
        message = "the embedding engine did not answer one vector per text"
        raise MeasurementError(message)
    return _vectors_of(outcome.vectors)


def _embed_query(model: EmbeddingModel, text: str) -> bytes:
    outcome = model.embed_query(text)
    if not outcome.available or not outcome.vectors:
        message = "the embedding engine did not answer a query vector"
        raise MeasurementError(message)
    return to_int8(outcome.vectors[0])


def measure_language(model: EmbeddingModel, path: Path) -> LanguageMeasurement:
    """The two distributions of one language file."""
    records = load_dataset(path)
    passages = _embed_passages(model, [record["passage"] for record in records])
    queries = [_embed_query(model, record["query"]) for record in records]
    matrix = np.array([distances_to(query, passages) for query in queries], dtype=np.float64)

    return LanguageMeasurement(
        language=path.stem,
        identifiers=tuple(record["id"] for record in records),
        matrix=matrix,
    )


def summarise(values: np.ndarray) -> Summary:
    flat = values.reshape(-1)
    if flat.size == 0:
        message = "no values to summarise"
        raise MeasurementError(message)
    return Summary(
        count=int(flat.size),
        minimum=float(np.min(flat)),
        p05=float(np.percentile(flat, 5)),
        median=float(np.median(flat)),
        p95=float(np.percentile(flat, 95)),
        maximum=float(np.max(flat)),
    )


def _summary_line(label: str, summary: Summary) -> str:
    return (
        f"{label:<22}{summary.count:>7}"
        f"{summary.minimum:>12.{DIGITS}f}{summary.p05:>12.{DIGITS}f}"
        f"{summary.median:>12.{DIGITS}f}{summary.p95:>12.{DIGITS}f}{summary.maximum:>12.{DIGITS}f}"
    )


def testset_report(measurements: Sequence[LanguageMeasurement]) -> str:
    header = f"{'population':<22}{'n':>7}{'min':>12}{'p05':>12}{'median':>12}{'p95':>12}{'max':>12}"
    lines = [header]
    for measurement in measurements:
        lines.append(_summary_line(f"{measurement.language} relevant", summarise(measurement.relevant)))
        lines.append(_summary_line(f"{measurement.language} distractor", summarise(measurement.distractors)))
        lines.append(
            f"{measurement.language} overlap          "
            f"{measurement.overlap} distractors closer than their own relevant pair"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Population two: the texts of the end to end corpus
# ---------------------------------------------------------------------------


def corpus_texts() -> dict[str, str]:
    """The text of every corpus file that carries one, keyed by file name.

    The literals of the generator for the image files, the real extractors of
    this container for everything else. No OCR anywhere, which is the
    reservation of this whole path.
    """
    import build_corpus

    from findling.extract.dispatch import extension_of, extract

    texts: dict[str, str] = {}
    # ignore_cleanup_errors, because the twelve damaged files of the corpus are
    # handed to readers that keep a handle open on the failure path, and on
    # Windows an open handle makes the removal of the directory fail. A leftover
    # temporary file is not worth losing a measurement over.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        for name, payload in sorted(build_corpus.FILES.items()):
            rendered = build_corpus.RENDERED_TEXT.get(name)
            if rendered is not None:
                texts[name] = "\n".join(rendered)
                continue
            mimetype = CORPUS_MIMETYPES.get(extension_of(name))
            if mimetype is None or not payload:
                continue
            target = root / name
            target.write_bytes(payload)
            outcome = _quietly_extracted(extract, str(target), mimetype, len(payload))
            if outcome is not None and outcome.text.strip():
                texts[name] = outcome.text
    return texts


def _quietly_extracted(reader: Callable[..., object], path: str, mimetype: str, size: int) -> Any:
    """One extraction, with the complaints of the readers kept out of the report.

    The damaged files of the corpus make pypdf write to standard output, and this
    tool's output is a table that a report quotes verbatim. The complaints go to
    standard error instead of into the middle of a column, and a reader that
    raises is a case rather than a failure: twelve of the corpus files are broken
    on purpose.
    """
    buffer = io.StringIO()
    level = logging.root.manager.disable
    try:
        logging.disable(logging.CRITICAL)
        with contextlib.redirect_stdout(buffer):
            return reader(path, mimetype, size)
    except Exception as error:
        # A broken corpus file is a case and not a failure: twelve of them are
        # damaged on purpose. The type name goes to standard error, never the text.
        print(f"note: {Path(path).name} is not readable ({type(error).__name__})", file=sys.stderr)
        return None
    finally:
        logging.disable(level)
        noise = buffer.getvalue().strip()
        if noise:
            lines = len(noise.splitlines())
            print(f"note: {Path(path).name} produced {lines} line(s) of reader output", file=sys.stderr)


@dataclass(frozen=True)
class Chunker:
    """The chunker of the package, built once per run because the tokenizer is large."""

    tokenizer: Any
    splitter: Any
    token_cap: int


def open_chunker(model_dir: Path) -> Chunker:
    """The tokenizer and splitter the container cuts with, under its own settings."""
    from findling.config import settings

    resolved = settings()
    tokenizer = open_tokenizer(model_dir)
    splitter = make_splitter(
        tokenizer,
        chunk_tokens=resolved.embed_chunk_tokens,
        overlap=resolved.embed_chunk_overlap,
    )
    return Chunker(tokenizer=tokenizer, splitter=splitter, token_cap=resolved.embed_token_cap)


def corpus_stock(model: EmbeddingModel, model_dir: Path) -> list[CorpusChunk]:
    """Every corpus text, cut by the real chunker and embedded as a passage."""
    return chunk_and_embed(model, open_chunker(model_dir), sorted(corpus_texts().items()))


def chunk_and_embed(
    model: EmbeddingModel,
    chunker: Chunker,
    named_texts: Sequence[tuple[str, str]],
) -> list[CorpusChunk]:
    """Named texts, cut by the real chunker and embedded as passages, by name and ordinal."""
    pieces: list[tuple[str, int, str]] = []
    for name, text in named_texts:
        for span in chunk_spans(
            text,
            tokenizer=chunker.tokenizer,
            splitter=chunker.splitter,
            token_cap=chunker.token_cap,
        ):
            pieces.append((name, span.ordinal, text[span.char_start : span.char_end]))
    if not pieces:
        message = "the corpus produced no chunk at all"
        raise MeasurementError(message)

    vectors: list[bytes] = []
    for start in range(0, len(pieces), BATCH_SIZE):
        window = pieces[start : start + BATCH_SIZE]
        vectors.extend(_embed_passages(model, [piece[2] for piece in window]))
    return [
        CorpusChunk(name=name, ordinal=ordinal, vector=vector)
        for (name, ordinal, _), vector in zip(pieces, vectors, strict=True)
    ]


def measure_probe(model: EmbeddingModel, stock: Sequence[CorpusChunk], probe: str) -> ProbeMeasurement:
    """The nearest chunks of one probe, ascending, by name and ordinal."""
    query = _embed_query(model, probe)
    row = distances_to(query, [chunk.vector for chunk in stock])
    order = np.argsort(row, kind="stable")
    return ProbeMeasurement(
        probe=probe,
        names=tuple(stock[int(position)].name for position in order),
        ordinals=tuple(stock[int(position)].ordinal for position in order),
        distances=tuple(float(row[int(position)]) for position in order),
    )


def corpus_report(stock: Sequence[CorpusChunk], probes: Sequence[ProbeMeasurement]) -> str:
    files = sorted({chunk.name for chunk in stock})
    lines = [
        f"chunks        {len(stock)} over {len(files)} files",
        f"files         {', '.join(files)}",
        "",
        f"{'probe':<18}{'rank':>5}{'file':<32}{'chunk':>7}{'distance':>12}",
    ]
    for measurement in probes:
        for rank in range(min(CORPUS_NEIGHBOURS, len(measurement.names))):
            label = measurement.probe if rank == 0 else ""
            lines.append(
                f"{label:<18}{rank + 1:>5}{measurement.names[rank]:<32}"
                f"{measurement.ordinals[rank]:>7}{measurement.distances[rank]:>12.{DIGITS}f}"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The derivation: two numbers, two constraints, one margin
# ---------------------------------------------------------------------------


def near_enough_rows(rows: np.ndarray, *, ceiling: float, band: float) -> np.ndarray:
    """The mask the gate of ``index/fusion.py`` produces, one row of distances at a time.

    Written over a whole matrix rather than over one list, because the
    derivation evaluates it a few hundred thousand times and a Python loop over
    the grid would turn a measurement into an afternoon. The arithmetic is the
    arithmetic of the gate, and a test compares the two the day the gate exists.

    The band is measured against the smallest surviving distance of the row and
    not against its first entry: whether the caller handed the row in sorted
    order is not something a pure function may depend on.
    """
    under = rows <= ceiling
    guarded = np.where(under, rows, np.inf)
    best = np.min(guarded, axis=-1, keepdims=True)
    return under & (rows <= best + band)


def _ranks_under(matrix: np.ndarray, *, ceiling: float, band: float) -> tuple[np.ndarray, np.ndarray]:
    """The rank of the relevant section of every case, and whether it survived.

    Ties are counted against the tool, exactly as ``scripts/dev/model_quality.py``
    counts them: a section that sits at the same distance as the relevant one
    pushes the relevant one down. Anything else would flatter a model that maps
    everything onto one vector.
    """
    keep = near_enough_rows(matrix, ceiling=ceiling, band=band)
    correct = np.diagonal(matrix).copy()[:, None]
    survived = np.diagonal(keep).copy()
    better = np.count_nonzero(keep & (matrix < correct), axis=1)
    tied = np.count_nonzero(keep & (matrix == correct), axis=1) - 1
    return 1 + better + tied, survived


def metrics_under(measurement: LanguageMeasurement, *, ceiling: float, band: float) -> tuple[float, float, float]:
    """Recall@1, Recall@5 and MRR of one language under one pair of numbers.

    A case whose relevant section the gate removed counts as a miss in all
    three, which is the honest accounting: the search would not answer that
    document any more.
    """
    ranks, survived = _ranks_under(measurement.matrix, ceiling=ceiling, band=band)
    total = measurement.cases
    hit_at_1 = int(np.count_nonzero(survived & (ranks == 1)))
    hit_at_5 = int(np.count_nonzero(survived & (ranks <= 5)))
    reciprocal = float(np.sum(np.where(survived, 1.0 / ranks, 0.0)))
    return hit_at_1 / total, hit_at_5 / total, reciprocal / total


def _open_gate(measurement: LanguageMeasurement) -> tuple[float, float, float]:
    """The three numbers with the gate wide open, which is the state of today."""
    return metrics_under(measurement, ceiling=METRIC_MAXIMUM, band=METRIC_MAXIMUM)


def holds_a(measurements: Sequence[LanguageMeasurement], *, ceiling: float, band: float) -> bool:
    """Constraint (A): no language loses hit rate against the open gate.

    Read as the plan writes it, over the three aggregates and not over the
    single case: the gate removes distractors as well, so a case that loses its
    relevant section can in principle be paid for by a case whose rank improved.
    Whether it is paid for is a measurement and not an assumption, which is why
    this compares the numbers instead of the individual survivals.

    ``TOLERANCE`` is a floating point tolerance and not a permitted loss. The
    three aggregates are sums of fractions, so two runs of the same arithmetic
    can differ in the last bit, and a strict comparison would call that a
    regression.
    """
    for measurement in measurements:
        off = _open_gate(measurement)
        on = metrics_under(measurement, ceiling=ceiling, band=band)
        if any(value_on < value_off - TOLERANCE for value_on, value_off in zip(on, off, strict=True)):
            return False
    return True


def holds_b(probes: Sequence[ProbeMeasurement], *, ceiling: float, band: float) -> bool:
    """Constraint (B): nothing for the one word probes, the document for the paraphrase."""
    for measurement in probes:
        row = np.array(measurement.distances, dtype=np.float64)
        keep = near_enough_rows(row, ceiling=ceiling, band=band)
        if measurement.probe in ONE_WORD_PROBES:
            if bool(np.any(keep)):
                return False
            continue
        wanted = np.array([name == PARAPHRASE_WANTS for name in measurement.names])
        if not bool(np.any(keep & wanted)):
            return False
    return True


def _grid(low: float, high: float) -> list[float]:
    steps = round((high - low) / GRID_STEP)
    return [_rounded(low + step * GRID_STEP) for step in range(steps + 1)]


def _bounds_of(measurements: Sequence[LanguageMeasurement], probes: Sequence[ProbeMeasurement]) -> tuple[float, float]:
    """The two ends of the grid, taken from the data instead of from a preference."""
    low = min(float(np.min(measurement.matrix)) for measurement in measurements)
    high = max(float(np.max(measurement.matrix)) for measurement in measurements)
    for measurement in probes:
        low = min(low, min(measurement.distances))
        high = max(high, max(measurement.distances))
    return float(np.floor(low)), float(np.ceil(high))


@dataclass(frozen=True)
class Choice:
    """One pair of numbers, with the reason it is this pair and not a neighbour."""

    ceiling: float
    band: float
    ceiling_margin: float
    band_margin: float
    both: bool


def choose(measurements: Sequence[LanguageMeasurement], probes: Sequence[ProbeMeasurement]) -> Choice | None:
    """The pair of numbers the two constraints leave, or nothing at all.

    When both constraints hold the admissible set has two ends and the pair is
    placed between them, which is what the plan asks for. When only (A) can be
    met the set is open upwards, because every larger pair is a weaker gate: the
    tightest admissible pair is taken instead, and the margin reported is the
    distance to the boundary below it, which is the only end that exists.
    """
    low, high = _bounds_of(measurements, probes)
    ceilings = _grid(low, high)
    bands = _grid(0.0, high - low)

    with_both = [
        (ceiling, band)
        for ceiling in ceilings
        for band in bands
        if holds_b(probes, ceiling=ceiling, band=band) and holds_a(measurements, ceiling=ceiling, band=band)
    ]
    if with_both:
        ceiling_values = sorted({pair[0] for pair in with_both})
        band_values = sorted({pair[1] for pair in with_both})
        ceiling = _rounded((ceiling_values[0] + ceiling_values[-1]) / 2.0)
        band = _rounded((band_values[0] + band_values[-1]) / 2.0)
        return Choice(
            ceiling=ceiling,
            band=band,
            ceiling_margin=min(ceiling - ceiling_values[0], ceiling_values[-1] - ceiling),
            band_margin=min(band - band_values[0], band_values[-1] - band),
            both=True,
        )

    for ceiling in ceilings:
        for band in bands:
            if holds_a(measurements, ceiling=ceiling, band=band):
                return Choice(ceiling=ceiling, band=band, ceiling_margin=GRID_STEP, band_margin=GRID_STEP, both=False)
    return None


def _rounded(value: float) -> float:
    """One number of the grid, so the chosen pair is quotable rather than exact."""
    return round(round(value / GRID_STEP) * GRID_STEP, 4)


def _binding_numbers(measurements: Sequence[LanguageMeasurement], probes: Sequence[ProbeMeasurement]) -> list[str]:
    """The numbers the two constraints are built on, named so they can be checked."""
    one_word = min(
        (measurement.distances[0] for measurement in probes if measurement.probe in ONE_WORD_PROBES),
        default=METRIC_MAXIMUM,
    )
    wanted = METRIC_MAXIMUM
    for measurement in probes:
        if measurement.probe in ONE_WORD_PROBES:
            continue
        reachable = [
            distance
            for name, distance in zip(measurement.names, measurement.distances, strict=True)
            if name == PARAPHRASE_WANTS
        ]
        if reachable:
            wanted = min(wanted, min(reachable))
    relevant_max = max(float(np.max(measurement.relevant)) for measurement in measurements)
    distractor_min = min(float(np.min(measurement.distractors)) for measurement in measurements)
    return [
        f"(B) upper on the ceiling   {one_word:>10.{DIGITS}f}   the nearest chunk of the one word probes",
        f"(B) lower on the ceiling   {wanted:>10.{DIGITS}f}   the wanted document of the paraphrase probe",
        f"(A) widest relevant pair   {relevant_max:>10.{DIGITS}f}   over the three languages",
        f"(A) closest distractor     {distractor_min:>10.{DIGITS}f}   over the three languages",
    ]


def derivation_report(
    measurements: Sequence[LanguageMeasurement],
    probes: Sequence[ProbeMeasurement],
) -> str:
    lines = ["the four numbers the two constraints are built on", *_binding_numbers(measurements, probes), ""]
    chosen = choose(measurements, probes)
    if chosen is None:
        lines.append("verdict       no pair on the grid satisfies (A), so this measurement carries no threshold")
        return "\n".join(lines)

    if chosen.both:
        lines.append("verdict       both constraints hold, the pair sits between the two ends of the set")
    else:
        lines.append("verdict       (A) holds and (B) is EMPTY: the ceiling would have to lie below the one")
        lines.append("              word probes and above the paraphrase at the same time, and the two")
        lines.append("              numbers above make that impossible. (B) is reported as a finding.")

    lines.extend(
        [
            "",
            f"ceiling       {chosen.ceiling:.{DIGITS}f}   margin to the boundary {chosen.ceiling_margin:.{DIGITS}f}",
            f"band          {chosen.band:.{DIGITS}f}   margin to the boundary {chosen.band_margin:.{DIGITS}f}",
            _gate_effect(measurements, ceiling=chosen.ceiling, band=chosen.band),
            _probe_effect(probes, ceiling=chosen.ceiling, band=chosen.band),
        ]
    )
    return "\n".join(lines)


def _gate_effect(measurements: Sequence[LanguageMeasurement], *, ceiling: float, band: float) -> str:
    """What the chosen pair does to the hit rate of the test set, per language."""
    header = f"{'language':<10}{'cases':>7}{'R@1 off':>10}{'R@1 on':>10}{'R@5 off':>10}{'R@5 on':>10}"
    lines = ["", f"{header}{'MRR off':>10}{'MRR on':>10}{'cut':>10}"]
    for measurement in measurements:
        off = _open_gate(measurement)
        on = metrics_under(measurement, ceiling=ceiling, band=band)
        # What the gate actually removes, which the three hit rates cannot say:
        # they only see the relevant section, and the point of the gate is the
        # distractors it takes away from the merge.
        keep = near_enough_rows(measurement.matrix, ceiling=ceiling, band=band)
        distractors = measurement.matrix.size - measurement.cases
        removed = distractors - (int(np.count_nonzero(keep)) - int(np.count_nonzero(np.diagonal(keep))))
        lines.append(
            f"{measurement.language:<10}{measurement.cases:>7}"
            f"{off[0]:>10.{DIGITS}f}{on[0]:>10.{DIGITS}f}"
            f"{off[1]:>10.{DIGITS}f}{on[1]:>10.{DIGITS}f}"
            f"{off[2]:>10.{DIGITS}f}{on[2]:>10.{DIGITS}f}"
            f"{removed / distractors:>10.{DIGITS}f}"
        )
    return "\n".join(lines)


def _probe_effect(probes: Sequence[ProbeMeasurement], *, ceiling: float, band: float) -> str:
    """How many candidates every probe of the corpus keeps under the chosen pair."""
    lines = ["", f"{'probe':<18}{'kept':>6}  surviving files"]
    for measurement in probes:
        row = np.array(measurement.distances, dtype=np.float64)
        mask = near_enough_rows(row, ceiling=ceiling, band=band)
        names = sorted({measurement.names[position] for position in np.flatnonzero(mask)})
        label = measurement.probe if measurement.probe in ONE_WORD_PROBES else "the paraphrase"
        lines.append(f"{label:<18}{int(np.count_nonzero(mask)):>6}  {', '.join(names) or 'none'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The similar mode: document against document (Plan 35-04)
# ---------------------------------------------------------------------------

# The rule of docs/measurements/2026-10-aehnlich-distanzen/README.md, section 1,
# written down before the run. Named here so that the derivation below reads
# the rule rather than restating it in literals.
GERMAN_SIMILAR_CASES: Final = 42  # the first 42 lines of de.jsonl, which 35-03 keeps byte for byte
RELATED_SHARE: Final = 0.95  # (1) share of related pairs at or under the ceiling, every language
UNRELATED_CUT: Final = 0.90  # (2) share of unrelated pairs beyond the ceiling, every language
GROUP_SHARE: Final = 0.80  # (4) share of group pairs at or under the ceiling
FOREIGN_SHARE: Final = 0.10  # (4) share of foreign pairs at or under the ceiling, at most
A1_OVERLAP: Final = 0.8  # (3) mean overlap of the first ten neighbours, mean against minimum
SIMILAR_NEIGHBOURS: Final = 10  # the list of the view shows ten neighbours at most (D-35-03)
MINIMUM_GROUPS: Final = 3  # (4) is checkable with three groups of two files or more
NO_GROUP: Final = "ohne Gruppe"  # the group column of a file that belongs to no topic

# How many grid steps the report shows on either side of the derived value.
RASTER_STEPS: Final = 6


@dataclass(frozen=True)
class SimilarPopulation:
    """The two distributions of one language, as numbers only.

    ``related`` holds one distance per case: the query text and the section of
    the same case, both embedded as passages. ``unrelated`` holds one distance
    per unordered pair of sections of different cases.
    """

    language: str
    related: np.ndarray
    unrelated: np.ndarray


@dataclass(frozen=True)
class SimilarDerivation:
    """What the rule makes of the three populations."""

    candidate: float
    ceiling: float | None
    satisfied: bool
    cut: dict[str, float]
    fallback: float | None
    fallback_lost: dict[str, int]


@dataclass(frozen=True)
class GroupProbe:
    """The group probe of rule (4) under one ceiling."""

    ceiling: float
    group_pairs: int
    foreign_pairs: int
    group_share: float
    foreign_share: float


def similar_cases(records: Sequence[dict[str, str]], language: str) -> list[dict[str, str]]:
    """The fixed selection of the run: German is cut to its first 42 cases.

    Independent of the stand of Plan 35-03, which grows de.jsonl to about 120
    cases and keeps the first 42 lines byte for byte. English and French are
    taken whole.
    """
    if language == "de":
        return list(records[:GERMAN_SIMILAR_CASES])
    return list(records)


def similar_pairs(language: str, queries: Sequence[bytes], passages: Sequence[bytes]) -> SimilarPopulation:
    """The related and the unrelated pairs of one language, from stored vectors."""
    if len(queries) != len(passages):
        message = f"{language}: {len(queries)} query vectors against {len(passages)} sections"
        raise MeasurementError(message)
    related = np.array([l2_distance(query, passage) for query, passage in zip(queries, passages, strict=True)])
    unrelated = np.array(
        [
            l2_distance(passages[first], passages[second])
            for first in range(len(passages))
            for second in range(first + 1, len(passages))
        ],
        dtype=np.float64,
    )
    return SimilarPopulation(language=language, related=related.astype(np.float64), unrelated=unrelated)


def _share_at_or_under(values: np.ndarray, ceiling: float) -> float:
    if values.size == 0:
        return 0.0
    return float(np.count_nonzero(values <= ceiling)) / float(values.size)


def derive_similar(populations: Sequence[SimilarPopulation]) -> SimilarDerivation:
    """Rule (1) and (2), mechanically, on the grid of step 0.5.

    The candidate is the smallest grid value at or under which every language
    keeps 95 percent of its related pairs. It becomes the ceiling only when it
    cuts at least 90 percent of the unrelated pairs in every language. When it
    does not, the answer carries the two numbers of the owner question instead:
    the largest grid value that cuts 90 percent everywhere, and how many related
    pairs every language would lose under it.
    """
    grid = _grid(0.0, METRIC_MAXIMUM)
    candidate = next(
        value
        for value in grid
        if all(_share_at_or_under(population.related, value) >= RELATED_SHARE - TOLERANCE for population in populations)
    )
    cut = {population.language: 1.0 - _share_at_or_under(population.unrelated, candidate) for population in populations}
    satisfied = all(share >= UNRELATED_CUT - TOLERANCE for share in cut.values())

    admissible = [
        value
        for value in grid
        if all(
            1.0 - _share_at_or_under(population.unrelated, value) >= UNRELATED_CUT - TOLERANCE
            for population in populations
        )
    ]
    fallback = admissible[-1] if admissible else None
    fallback_lost = {
        population.language: (int(np.count_nonzero(population.related > fallback)) if fallback is not None else 0)
        for population in populations
    }
    return SimilarDerivation(
        candidate=candidate,
        ceiling=candidate if satisfied else None,
        satisfied=satisfied,
        cut=cut,
        fallback=fallback,
        fallback_lost=fallback_lost,
    )


def read_groups(path: Path) -> dict[str, str]:
    """The group table: file name to topic group, header line first."""
    if not path.is_file():
        message = f"group table not found: {path}"
        raise MeasurementError(message)
    groups: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        columns = line.split("\t")
        if len(columns) != 3:
            message = f"{path.name} line {number} has {len(columns)} columns, expected 3"
            raise MeasurementError(message)
        groups[columns[0]] = columns[1]
    return groups


def _group_split(groups: Mapping[str, str], centroids: Mapping[str, bytes]) -> tuple[np.ndarray, np.ndarray] | None:
    """The centroid distances of the group pairs and of the foreign pairs, or None.

    Files without a vector fall out of both counts. A file without a group is
    only ever a foreign partner. Fewer than three groups with two files each
    make the probe not checkable, which is None.
    """
    names = sorted(centroids)
    group_of = {name: groups.get(name, NO_GROUP) for name in names}
    sizes: dict[str, int] = {}
    for group in group_of.values():
        if group != NO_GROUP:
            sizes[group] = sizes.get(group, 0) + 1
    if sum(1 for size in sizes.values() if size >= 2) < MINIMUM_GROUPS:
        return None
    same: list[float] = []
    foreign: list[float] = []
    for first in range(len(names)):
        for second in range(first + 1, len(names)):
            left, right = names[first], names[second]
            distance = l2_distance(centroids[left], centroids[right])
            if group_of[left] == group_of[right] != NO_GROUP:
                same.append(distance)
            else:
                foreign.append(distance)
    return np.array(same, dtype=np.float64), np.array(foreign, dtype=np.float64)


def group_probe(groups: Mapping[str, str], centroids: Mapping[str, bytes], *, ceiling: float) -> GroupProbe | None:
    """Rule (4) under one ceiling, or None when the corpus cannot carry the probe."""
    split = _group_split(groups, centroids)
    if split is None:
        return None
    same, foreign = split
    return GroupProbe(
        ceiling=ceiling,
        group_pairs=int(same.size),
        foreign_pairs=int(foreign.size),
        group_share=_share_at_or_under(same, ceiling),
        foreign_share=_share_at_or_under(foreign, ceiling),
    )


def neighbour_overlap(
    documents: Mapping[str, Sequence[bytes]],
    *,
    neighbours: int = SIMILAR_NEIGHBOURS,
) -> dict[str, float]:
    """Assumption A1: how far the mean ranks like the minimum, per multi chunk document.

    The mean asks once: the centroid of the document against every chunk of the
    other documents, minimum per document, which is what the view runs. The
    minimum asks once per own chunk and keeps the smallest distance over both
    sides. The answer is the share of the first ``neighbours`` documents the two
    rankings have in common, between 0 and 1. Documents of one chunk have
    nothing to compare and are left out; ties go to the file name.
    """
    overlap: dict[str, float] = {}
    for name in sorted(documents):
        chunks = documents[name]
        others = [other for other in sorted(documents) if other != name]
        if len(chunks) < 2 or not others:
            continue
        query = centroid(chunks)
        if query is None:
            continue
        by_mean = sorted(
            others, key=lambda other: (min(l2_distance(query, chunk) for chunk in documents[other]), other)
        )
        by_minimum = sorted(
            others,
            key=lambda other: (min(l2_distance(own, chunk) for own in chunks for chunk in documents[other]), other),
        )
        depth = min(neighbours, len(others))
        overlap[name] = len(set(by_mean[:depth]) & set(by_minimum[:depth])) / depth
    return overlap


def measure_similar_language(model: EmbeddingModel, path: Path) -> SimilarPopulation:
    """The two populations of one language, query text and section both as passages."""
    records = similar_cases(load_dataset(path), path.stem)
    passages = _embed_passages(model, [record["passage"] for record in records])
    queries = _embed_passages(model, [record["query"] for record in records])
    return similar_pairs(path.stem, queries, passages)


def documents_of(stock: Sequence[CorpusChunk]) -> dict[str, list[bytes]]:
    """The chunk vectors of every corpus file, in the order of their ordinals."""
    grouped: dict[str, list[tuple[int, bytes]]] = {}
    for chunk in stock:
        grouped.setdefault(chunk.name, []).append((chunk.ordinal, chunk.vector))
    return {name: [vector for _, vector in sorted(entries)] for name, entries in sorted(grouped.items())}


def _quartile_line(label: str, values: np.ndarray) -> str:
    return (
        f"{label:<22}{values.size:>7}"
        f"{float(np.min(values)):>12.{DIGITS}f}{float(np.percentile(values, 25)):>12.{DIGITS}f}"
        f"{float(np.median(values)):>12.{DIGITS}f}{float(np.percentile(values, 75)):>12.{DIGITS}f}"
        f"{float(np.max(values)):>12.{DIGITS}f}"
    )


def similar_population_report(populations: Sequence[SimilarPopulation]) -> str:
    header = f"{'population':<22}{'n':>7}{'min':>12}{'p25':>12}{'median':>12}{'p75':>12}{'max':>12}"
    lines = [header]
    for population in populations:
        lines.append(_quartile_line(f"{population.language} related", population.related))
        lines.append(_quartile_line(f"{population.language} unrelated", population.unrelated))
    return "\n".join(lines)


def similar_corpus_report(documents: Mapping[str, Sequence[bytes]], overlap: Mapping[str, float]) -> str:
    chunks = sum(len(vectors) for vectors in documents.values())
    multi = sorted(name for name, vectors in documents.items() if len(vectors) > 1)
    lines = [
        f"corpus        {chunks} chunks over {len(documents)} files with text",
        f"multi chunk   {len(multi)} files: {', '.join(multi) or 'none'}",
    ]
    if not overlap:
        lines.append("A1            not checkable on the corpus: no file carries more than one chunk")
        return "\n".join(lines)
    for name, value in sorted(overlap.items()):
        lines.append(f"overlap       {name:<34}{value:>8.{DIGITS}f}")
    mean = sum(overlap.values()) / len(overlap)
    verdict = "holds" if mean >= A1_OVERLAP - TOLERANCE else "FAILS, owner question"
    lines.append(f"A1            mean overlap {mean:.{DIGITS}f} against {A1_OVERLAP}: {verdict}")
    return "\n".join(lines)


def _similar_raster_line(populations: Sequence[SimilarPopulation], value: float) -> str:
    related = "".join(f"{_share_at_or_under(population.related, value):>9.{DIGITS}f}" for population in populations)
    cut = "".join(f"{1.0 - _share_at_or_under(population.unrelated, value):>9.{DIGITS}f}" for population in populations)
    return f"{value:>8.1f}{related}  {cut}"


def similar_derivation_report(populations: Sequence[SimilarPopulation], derivation: SimilarDerivation) -> str:
    languages = [population.language for population in populations]
    header = (
        f"{'value':>8}"
        + "".join(f"{'rel ' + language:>9}" for language in languages)
        + "  "
        + "".join(f"{'cut ' + language:>9}" for language in languages)
    )
    lines = [
        (
            f"rule (1)      smallest grid value with {RELATED_SHARE:.2f} of related pairs at or under it: "
            f"{derivation.candidate:.1f}"
        ),
        "rule (2)      cut of unrelated pairs at that value: "
        + ", ".join(f"{language} {share:.{DIGITS}f}" for language, share in derivation.cut.items()),
    ]
    if derivation.satisfied:
        lines.append(f"verdict       (1) and (2) hold, candidate {derivation.candidate:.1f}")
    else:
        lines.append(f"verdict       Regel nicht erfuellbar: (2) needs {UNRELATED_CUT:.2f} cut in every language")
        if derivation.fallback is None:
            lines.append("owner         no grid value cuts 90 percent of the unrelated pairs in every language")
        else:
            lost = ", ".join(
                f"{language} {count} of {population.related.size}"
                for (language, count), population in zip(derivation.fallback_lost.items(), populations, strict=True)
            )
            lines.append(f"owner         {derivation.fallback:.1f} would cut 90 percent everywhere and lose {lost}")
    lines.extend(["", header])
    anchor = derivation.candidate
    marks = {anchor}
    if derivation.fallback is not None:
        marks.add(derivation.fallback)
    shown = sorted(
        {
            _rounded(mark + step * GRID_STEP)
            for mark in marks
            for step in range(-RASTER_STEPS, RASTER_STEPS + 1)
            if 0.0 <= mark + step * GRID_STEP <= METRIC_MAXIMUM
        }
    )
    lines.extend(_similar_raster_line(populations, value) for value in shown)
    return "\n".join(lines)


def group_report(
    groups: Mapping[str, str],
    centroids: Mapping[str, bytes],
    derivation: SimilarDerivation | None,
) -> str:
    split = _group_split(groups, centroids)
    if split is None:
        return "group probe   not checkable: fewer than three groups with two files that carry text"
    same, foreign = split
    lines = [f"group probe   {same.size} group pairs, {foreign.size} foreign pairs"]
    lines.append(_quartile_line("group pairs", same))
    lines.append(_quartile_line("foreign pairs", foreign))
    if derivation is not None:
        probe = group_probe(groups, centroids, ceiling=derivation.candidate)
        if probe is not None:
            holds = probe.group_share >= GROUP_SHARE - TOLERANCE and probe.foreign_share <= FOREIGN_SHARE + TOLERANCE
            lines.append(
                f"rule (4)      at {probe.ceiling:.1f}: group pairs under {probe.group_share:.{DIGITS}f}, "
                f"foreign pairs under {probe.foreign_share:.{DIGITS}f}: {'holds' if holds else 'FAILS'}"
            )
    lines.extend(["", f"{'value':>8}{'group':>9}{'foreign':>9}"])
    everything = np.concatenate([same, foreign])
    for value in _grid(float(np.floor(np.min(everything))), float(np.ceil(np.max(everything)))):
        lines.append(
            f"{value:>8.1f}{_share_at_or_under(same, value):>9.{DIGITS}f}"
            f"{_share_at_or_under(foreign, value):>9.{DIGITS}f}"
        )
    return "\n".join(lines)


def similar_verdict(
    derivation: SimilarDerivation,
    groups: Mapping[str, str] | None,
    centroids: Mapping[str, bytes],
) -> str:
    """The one line the report quotes: a value, or the rule that was not met."""
    if not derivation.satisfied:
        return "SIMILAR_CEILING   none: Regel nicht erfuellbar, (2) fails"
    if groups is None:
        return f"SIMILAR_CEILING   {derivation.candidate:.1f} under (1) and (2); (4) not run, --groups missing"
    probe = group_probe(groups, centroids, ceiling=derivation.candidate)
    if probe is None:
        return "SIMILAR_CEILING   none: Regel nicht erfuellbar, (4) not checkable on the corpus"
    if probe.group_share < GROUP_SHARE - TOLERANCE or probe.foreign_share > FOREIGN_SHARE + TOLERANCE:
        return "SIMILAR_CEILING   none: Regel nicht erfuellbar, (4) fails"
    return f"SIMILAR_CEILING   {derivation.candidate:.1f}"


def run_similar(args: argparse.Namespace, model: EmbeddingModel, model_dir: Path) -> str:
    populations = [measure_similar_language(model, path) for path in _languages(args.dataset_dir)]
    documents = documents_of(corpus_stock(model, model_dir))
    overlap = neighbour_overlap(documents)
    centroids = {name: vector for name, chunks in documents.items() if (vector := centroid(chunks)) is not None}
    groups = read_groups(args.groups) if args.groups is not None else None

    sections = [similar_population_report(populations), "", similar_corpus_report(documents, overlap)]
    derivation = derive_similar(populations) if args.derive else None
    if derivation is not None:
        sections.extend(["", similar_derivation_report(populations, derivation)])
    if groups is not None:
        sections.extend(["", group_report(groups, centroids, derivation)])
    if derivation is not None:
        sections.extend(["", similar_verdict(derivation, groups, centroids)])
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# The version mode: a base document against its own version (Plan 35-04B)
# ---------------------------------------------------------------------------

# The rule of docs/measurements/2026-10-aehnlich-distanzen/README.md, section
# 10.1, written down before this mode existed.
VERSION_SEED: Final = 3504  # (F0) one fresh random.Random(3504) per language
VERSION_BLOCK: Final = 4  # (F0) sections per base document
VERSION_JOIN: Final = "\n\n"  # (F0) sections are separated by one empty line
MINIMUM_VERSION_PAIRS: Final = 10  # (F4) fewer pairs in one language make the rule not checkable


@dataclass(frozen=True)
class VersionDerivation:
    """What rule (F1) to (F4) make of the three populations, as numbers only."""

    candidate: float
    upper: float | None
    ceiling: float | None
    satisfied: bool
    checkable: bool
    cut: dict[str, float]
    lost: dict[str, int]


def version_blocks(count: int) -> list[tuple[tuple[int, ...], int]]:
    """The blocks of one language: four shuffled positions each, and the drawn one.

    One generator per call, seeded with ``VERSION_SEED``: the positions are
    shuffled first, then one ``randrange(4)`` per block names the section the
    version drops. A rest below four falls away.
    """
    generator = random.Random(VERSION_SEED)  # noqa: S311 - a fixed measurement seed, no secret
    order = list(range(count))
    generator.shuffle(order)
    whole = count - count % VERSION_BLOCK
    return [
        (tuple(order[start : start + VERSION_BLOCK]), generator.randrange(VERSION_BLOCK))
        for start in range(0, whole, VERSION_BLOCK)
    ]


def version_documents(
    sections: Sequence[str],
    blocks: Sequence[tuple[tuple[int, ...], int]],
) -> list[tuple[str, str]]:
    """The base document and its version per block. Kept in memory, never printed."""
    documents: list[tuple[str, str]] = []
    for positions, dropped in blocks:
        base = [sections[position] for position in positions]
        kept = [section for index, section in enumerate(base) if index != dropped]
        documents.append((VERSION_JOIN.join(base), VERSION_JOIN.join(reversed(kept))))
    return documents


def version_pairs(language: str, documents: Sequence[tuple[bytes, bytes]]) -> SimilarPopulation:
    """Base against version per block, and every pair of documents of different blocks."""
    related = np.array([l2_distance(base, version) for base, version in documents], dtype=np.float64)
    flat = [(block, vector) for block, pair in enumerate(documents) for vector in pair]
    unrelated = np.array(
        [
            l2_distance(flat[first][1], flat[second][1])
            for first in range(len(flat))
            for second in range(first + 1, len(flat))
            if flat[first][0] != flat[second][0]
        ],
        dtype=np.float64,
    )
    return SimilarPopulation(language=language, related=related, unrelated=unrelated)


def _cut_everywhere(populations: Sequence[SimilarPopulation], value: float) -> bool:
    return all(
        1.0 - _share_at_or_under(population.unrelated, value) >= UNRELATED_CUT - TOLERANCE for population in populations
    )


def _floor_to_grid(value: float) -> float:
    return round(float(np.floor(value / GRID_STEP + TOLERANCE)) * GRID_STEP, 4)


def derive_versions(populations: Sequence[SimilarPopulation]) -> VersionDerivation:
    """Rule (F1) to (F4), mechanically, on the grid of step 0.5."""
    grid = _grid(0.0, METRIC_MAXIMUM)
    candidate = next(
        value
        for value in grid
        if all(_share_at_or_under(population.related, value) >= RELATED_SHARE - TOLERANCE for population in populations)
    )
    cut = {population.language: 1.0 - _share_at_or_under(population.unrelated, candidate) for population in populations}
    admissible = [value for value in grid if _cut_everywhere(populations, value)]
    upper = admissible[-1] if admissible else None
    lost = {
        population.language: (int(np.count_nonzero(population.related > upper)) if upper is not None else 0)
        for population in populations
    }
    checkable = all(population.related.size >= MINIMUM_VERSION_PAIRS for population in populations)
    satisfied = checkable and upper is not None and candidate <= upper
    ceiling = _floor_to_grid((candidate + upper) / 2.0) if satisfied and upper is not None else None
    return VersionDerivation(
        candidate=candidate,
        upper=upper,
        ceiling=ceiling,
        satisfied=satisfied,
        checkable=checkable,
        cut=cut,
        lost=lost,
    )


def version_report(populations: Sequence[SimilarPopulation], derivation: VersionDerivation | None) -> str:
    header = f"{'population':<22}{'n':>7}{'min':>12}{'p25':>12}{'median':>12}{'p75':>12}{'max':>12}"
    lines = [f"versions      seed {VERSION_SEED}, blocks of {VERSION_BLOCK}, one section dropped", "", header]
    for population in populations:
        lines.append(_quartile_line(f"{population.language} versions", population.related))
        lines.append(_quartile_line(f"{population.language} unrelated", population.unrelated))
    if derivation is None:
        return "\n".join(lines)

    upper = "none" if derivation.upper is None else f"{derivation.upper:.1f}"
    lines.extend(
        [
            "",
            (
                f"rule (F1)     smallest grid value with {RELATED_SHARE:.2f} of version pairs at or under it: "
                f"{derivation.candidate:.1f}"
            ),
            "              cut of unrelated pairs there: "
            + ", ".join(f"{language} {share:.{DIGITS}f}" for language, share in derivation.cut.items()),
            f"rule (F2)     largest grid value cutting {UNRELATED_CUT:.2f} of unrelated pairs everywhere: {upper}",
            "              version pairs beyond it: "
            + ", ".join(
                f"{language} {count} of {population.related.size}"
                for (language, count), population in zip(derivation.lost.items(), populations, strict=True)
            ),
            f"rule (F4)     at least {MINIMUM_VERSION_PAIRS} version pairs per language: "
            + ("met" if derivation.checkable else "NOT met"),
        ]
    )
    languages = [population.language for population in populations]
    lines.extend(
        [
            "",
            f"{'value':>8}"
            + "".join(f"{'ver ' + language:>9}" for language in languages)
            + "  "
            + "".join(f"{'cut ' + language:>9}" for language in languages),
        ]
    )
    marks = {derivation.candidate}
    if derivation.upper is not None:
        marks.add(derivation.upper)
    if derivation.ceiling is not None:
        marks.add(derivation.ceiling)
    shown = sorted(
        {
            _rounded(mark + step * GRID_STEP)
            for mark in marks
            for step in range(-RASTER_STEPS, RASTER_STEPS + 1)
            if 0.0 <= mark + step * GRID_STEP <= METRIC_MAXIMUM
        }
    )
    lines.extend(_similar_raster_line(populations, value) for value in shown)
    return "\n".join(lines)


def version_verdict(derivation: VersionDerivation) -> str:
    """The one line the report quotes: a value, or the rule that was not met."""
    if not derivation.checkable:
        return "SIMILAR_CEILING   none: Regel nicht erfuellbar, (F4) fewer than ten version pairs"
    if derivation.ceiling is None:
        return "SIMILAR_CEILING   none: Regel nicht erfuellbar, (F1) lies above (F2)"
    return f"SIMILAR_CEILING   {derivation.ceiling:.1f}"


def measure_version_language(model: EmbeddingModel, chunker: Chunker, path: Path) -> SimilarPopulation:
    """The version pairs and the unrelated pairs of one language file."""
    records = load_dataset(path)
    blocks = version_blocks(len(records))
    documents = version_documents([record["passage"] for record in records], blocks)
    named: list[tuple[str, str]] = []
    for block, (base, version) in enumerate(documents):
        named.append((f"{path.stem}-b{block:02d}-base", base))
        named.append((f"{path.stem}-b{block:02d}-version", version))
    chunks = documents_of(chunk_and_embed(model, chunker, named))
    pairs: list[tuple[bytes, bytes]] = []
    for block in range(len(documents)):
        base = centroid(chunks[f"{path.stem}-b{block:02d}-base"])
        version = centroid(chunks[f"{path.stem}-b{block:02d}-version"])
        if base is None or version is None:
            message = f"{path.stem} block {block}: a document without a vector"
            raise MeasurementError(message)
        pairs.append((base, version))
    return version_pairs(path.stem, pairs)


def run_versions(args: argparse.Namespace, model: EmbeddingModel, model_dir: Path) -> str:
    chunker = open_chunker(model_dir)
    populations = [measure_version_language(model, chunker, path) for path in _languages(args.dataset_dir)]
    derivation = derive_versions(populations) if args.derive else None
    sections = [version_report(populations, derivation)]
    if derivation is not None and derivation.ceiling is not None and args.groups is not None:
        # Information only, rule section 10.1: the group probe does not decide.
        documents = documents_of(chunk_and_embed(model, chunker, sorted(corpus_texts().items())))
        centroids = {name: vector for name, chunks in documents.items() if (vector := centroid(chunks)) is not None}
        probe = group_probe(read_groups(args.groups), centroids, ceiling=derivation.ceiling)
        if probe is not None:
            sections.extend(
                [
                    "",
                    (
                        f"information   group probe at {probe.ceiling:.1f} (not deciding): "
                        f"group pairs under {probe.group_share:.{DIGITS}f} of {probe.group_pairs}, "
                        f"foreign pairs under {probe.foreign_share:.{DIGITS}f} of {probe.foreign_pairs}"
                    ),
                ]
            )
    if derivation is not None:
        sections.extend(["", version_verdict(derivation)])
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------


def _model(model_dir: Path | None) -> tuple[EmbeddingModel, Path]:
    if model_dir is None:
        message = "--model-dir is required for a measurement"
        raise MeasurementError(message)
    if not model_dir.is_dir():
        message = f"model directory not found: {model_dir}"
        raise MeasurementError(message)

    from findling.config import settings

    resolved = settings()
    return (
        EmbeddingModel(model_dir, batch_size=BATCH_SIZE, sequence_len=resolved.embed_sequence_len),
        model_dir,
    )


def _languages(dataset_dir: Path | None) -> list[Path]:
    if dataset_dir is None:
        message = "--dataset-dir is required for the test set population"
        raise MeasurementError(message)
    return [dataset_dir / f"{language}.jsonl" for language in LANGUAGES]


def run(args: argparse.Namespace) -> str:
    if args.selftest:
        return selftest()

    model, model_dir = _model(args.model_dir)

    if args.versions:
        return run_versions(args, model, model_dir)

    if args.similar:
        return run_similar(args, model, model_dir)

    if args.testset:
        measurements = [measure_language(model, path) for path in _languages(args.dataset_dir)]
        return testset_report(measurements)

    stock = corpus_stock(model, model_dir)
    probes = [measure_probe(model, stock, probe) for probe in (*ONE_WORD_PROBES, PARAPHRASE_PROBE)]

    if args.corpus:
        return corpus_report(stock, probes)

    measurements = [measure_language(model, path) for path in _languages(args.dataset_dir)]
    return "\n".join(
        [
            testset_report(measurements),
            "",
            corpus_report(stock, probes),
            "",
            derivation_report(measurements, probes),
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if not (args.selftest or args.testset or args.corpus or args.derive or args.similar or args.versions):
        modes = "--selftest, --testset, --corpus, --derive, --similar or --versions"
        print(f"REFUSED: name one of {modes}", file=sys.stderr)
        return 2
    try:
        print(run(args))
    except MeasurementError as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
