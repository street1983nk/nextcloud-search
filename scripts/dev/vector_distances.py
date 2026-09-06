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
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import sys
import tempfile
from collections.abc import Callable, Sequence
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


def corpus_stock(model: EmbeddingModel, model_dir: Path) -> list[CorpusChunk]:
    """Every corpus text, cut by the real chunker and embedded as a passage."""
    from findling.config import settings

    resolved = settings()
    tokenizer = open_tokenizer(model_dir)
    splitter = make_splitter(
        tokenizer,
        chunk_tokens=resolved.embed_chunk_tokens,
        overlap=resolved.embed_chunk_overlap,
    )

    pieces: list[tuple[str, int, str]] = []
    for name, text in sorted(corpus_texts().items()):
        for span in chunk_spans(text, tokenizer=tokenizer, splitter=splitter, token_cap=resolved.embed_token_cap):
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
    if not (args.selftest or args.testset or args.corpus or args.derive):
        print("REFUSED: name one of --selftest, --testset, --corpus or --derive", file=sys.stderr)
        return 2
    try:
        print(run(args))
    except MeasurementError as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
