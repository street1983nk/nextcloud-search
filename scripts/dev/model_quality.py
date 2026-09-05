#!/usr/bin/env python3
"""Recall@1, Recall@5 and MRR for one model file, one language, one prefix setting and one vector dtype.

Two questions are answered with this tool, and both of them fail silently when
nobody measures them.

**The first is the model quantisation.** The image built in plan 06-01 carries an
int8 file this repository produced itself out of the fp32 original, because the
int8 file upstream ships is AVX512-VNNI and unusable on the ARM board this app
targets. Elastic measured almost no loss for German on a quantisation of the very
same model, but with a per layer procedure rather than a bare quantize_dynamic
call, and for French they publish no number at all. A strong hint is not a proof
of our procedure, so this tool runs both files against the same cases.

**The second is the pair of E5 prefixes.** The model expects ``query: `` in front
of a question and ``passage: `` in front of a section. fastembed adds them for
its built in models only, and the model here is registered by hand. Nothing fails
when they are missing, the quality simply drops, which is why ``--prefixes off``
exists: the difference between on and off is the evidence that they arrive where
they are supposed to arrive.

**A second quantisation is deliberately not confused with the first.** The switch
``--vector-dtype int8`` quantises the *produced vectors* before they are
compared, which is what the vec0 table will hold. That is the second stage,
and the 1.05 percent Elastic reports for scalar quantisation refers to **this**
one and not to the quantisation of the weights. The two are mixed up regularly;
they are measured separately here so that a report can say which of them cost
what.

**What this prints, and what it never prints.** Numbers, paths, and the
identifiers out of the data file. Never a query and never a passage. This path
sees the same shape of text a production index would see, and a measurement that
prints what it read is the cheapest way to lose content (T-02-14, T-06-11). A
case with a bad rank is therefore reported through its id.

Why onnxruntime directly and not fastembed: the switch ``--model`` takes the path
of an ONNX file, and comparing two files of the same model is exactly what
fastembed's model registration does not offer. The tokenizer is the one that
travels with the model directory, so both runs see identical tokens and the only
difference between them is the weights.

Run it, from anywhere, with the environment of the backend::

    cd backend
    uv run python ../scripts/dev/model_quality.py \\
        --model /model/int8/model.onnx \\
        --tokenizer /model \\
        --dataset /testdata/semantik/de.jsonl \\
        --prefixes on \\
        --vector-dtype fp32
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np

# The two strings that decide whether this model performs or merely runs.
QUERY_PREFIX: Final = "query: "
PASSAGE_PREFIX: Final = "passage: "

# The context window of the XLM-RoBERTa architecture behind multilingual-e5-small.
# Every passage of the test set is far shorter; the cap is here so that a longer
# one later fails on quality rather than on a shape mismatch.
MAX_SEQUENCE_TOKENS: Final = 512
BATCH_SIZE: Final = 16

# The vectors are L2 normalised, so every component sits in [-1, 1] and a fixed
# symmetric scale of 127 is the natural one. This is the scale a vec0 int8 column
# is fed with, which is the point: the number this switch produces is meant to
# predict what the store will do, not to explore quantisation schemes.
INT8_SCALE: Final = 127.0

# How many badly ranked cases are named. Named by identifier, never by text.
WORST_CASES_REPORTED: Final = 5

PREFIX_CHOICES: Final = ("on", "off")
VECTOR_DTYPE_CHOICES: Final = ("fp32", "int8")


class MeasurementError(Exception):
    """A named refusal. Never a zero in the statistics, always a non zero exit."""


@dataclass(frozen=True)
class Metrics:
    """What one run answers. Three numbers and the size of the ground they cover."""

    cases: int
    recall_at_1: float
    recall_at_5: float
    mrr: float


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure Recall@1, Recall@5 and MRR of one ONNX model against one language file.",
    )
    parser.add_argument("--model", required=True, type=Path, help="the ONNX file to measure")
    parser.add_argument("--tokenizer", required=True, type=Path, help="the directory holding tokenizer.json")
    parser.add_argument("--dataset", required=True, type=Path, help="one .jsonl file out of testdata/semantik")
    parser.add_argument(
        "--prefixes",
        required=True,
        choices=PREFIX_CHOICES,
        help="whether the E5 prefixes query: and passage: are set",
    )
    parser.add_argument(
        "--vector-dtype",
        required=True,
        choices=VECTOR_DTYPE_CHOICES,
        help="fp32 leaves the produced vectors alone, int8 quantises them before the comparison",
    )
    parser.add_argument(
        "--per-case",
        action="store_true",
        help="also print the rank of every case, keyed by identifier, so two runs can be compared pairwise",
    )
    return parser.parse_args(argv)


def load_dataset(path: Path) -> list[dict[str, str]]:
    """The cases of one language, or a named refusal."""
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


def load_tokenizer(directory: Path) -> Any:
    """The tokenizer that travels with the model, or a named refusal.

    Imported inside the function on purpose: the pure parts of this module are
    under test without onnxruntime and without a model on disk, and importing the
    runtime for that would cost a second and prove nothing.
    """
    if not directory.is_dir():
        message = f"tokenizer directory not found: {directory}"
        raise MeasurementError(message)
    tokenizer_file = directory / "tokenizer.json"
    if not tokenizer_file.is_file():
        message = f"tokenizer.json not found in {directory}"
        raise MeasurementError(message)

    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(tokenizer_file))
    tokenizer.enable_truncation(max_length=MAX_SEQUENCE_TOKENS)
    tokenizer.enable_padding(pad_id=_pad_id(tokenizer, directory), pad_token=_pad_token(directory))
    return tokenizer


def _pad_token(directory: Path) -> str:
    special = directory / "special_tokens_map.json"
    if special.is_file():
        mapping = json.loads(special.read_text(encoding="utf-8"))
        token = mapping.get("pad_token")
        if isinstance(token, dict):
            return str(token.get("content", "<pad>"))
        if isinstance(token, str):
            return token
    return "<pad>"


def _pad_id(tokenizer: Any, directory: Path) -> int:
    identifier = tokenizer.token_to_id(_pad_token(directory))
    return 1 if identifier is None else int(identifier)


def embed(texts: Sequence[str], model: Path, tokenizer: Any) -> np.ndarray:
    """Mean pooled, L2 normalised sentence vectors, one row per text."""
    if not model.is_file():
        message = f"model not found: {model}"
        raise MeasurementError(message)

    import onnxruntime

    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = 2
    session = onnxruntime.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])
    wanted = {entry.name for entry in session.get_inputs()}

    rows: list[np.ndarray] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = tokenizer.encode_batch(list(texts[start : start + BATCH_SIZE]))
        input_ids = np.array([encoding.ids for encoding in batch], dtype=np.int64)
        attention_mask = np.array([encoding.attention_mask for encoding in batch], dtype=np.int64)
        feed: dict[str, np.ndarray] = {}
        if "input_ids" in wanted:
            feed["input_ids"] = input_ids
        if "attention_mask" in wanted:
            feed["attention_mask"] = attention_mask
        if "token_type_ids" in wanted:
            feed["token_type_ids"] = np.zeros_like(input_ids)
        hidden = session.run(None, feed)[0]
        rows.append(mean_pool(np.asarray(hidden, dtype=np.float32), attention_mask))
    return normalise(np.concatenate(rows, axis=0))


def mean_pool(hidden: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    """The average over the tokens that are not padding. Padding averaged in is a quiet quality loss."""
    mask = attention_mask[:, :, None].astype(np.float32)
    summed = (hidden * mask).sum(axis=1)
    counted = np.clip(mask.sum(axis=1), 1e-9, None)
    return summed / counted


def normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.clip(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12, None)
    return (matrix / norms).astype(np.float32)


def quantise_to_int8(matrix: np.ndarray) -> np.ndarray:
    """The second quantisation stage: the vectors, not the weights.

    Symmetric, one fixed scale for every component, which is what a vec0 int8
    column receives. The result is handed back as float so that the comparison
    below is the ordinary one and the only difference to an fp32 run is the
    information that the rounding threw away.
    """
    quantised = np.clip(np.rint(matrix * INT8_SCALE), -128, 127).astype(np.int8)
    return quantised.astype(np.float32) / INT8_SCALE


def ranks_of(queries: np.ndarray, passages: np.ndarray) -> list[int]:
    """The rank of the correct passage for every query, counted from 1.

    Row i of ``queries`` belongs to row i of ``passages``; every other row of
    ``passages`` is a distractor. Ties are counted against the tool rather than
    for it: a passage that scores exactly as high as the correct one pushes the
    correct one down. A tie broken the other way would flatter a degenerate model
    that maps everything onto the same vector.
    """
    if queries.shape[0] != passages.shape[0]:
        message = f"{queries.shape[0]} queries against {passages.shape[0]} passages"
        raise MeasurementError(message)
    similarity = normalise(queries) @ normalise(passages).T
    ranks: list[int] = []
    for index, row in enumerate(similarity):
        correct = row[index]
        better = int(np.count_nonzero(row > correct))
        tied = int(np.count_nonzero(row == correct)) - 1
        ranks.append(1 + better + tied)
    return ranks


def metrics_of(ranks: Sequence[int]) -> Metrics:
    if not ranks:
        message = "no ranks to summarise"
        raise MeasurementError(message)
    total = len(ranks)
    return Metrics(
        cases=total,
        recall_at_1=sum(1 for rank in ranks if rank == 1) / total,
        recall_at_5=sum(1 for rank in ranks if rank <= 5) / total,
        mrr=sum(1.0 / rank for rank in ranks) / total,
    )


def worst_cases(ranked: Sequence[tuple[str, int]]) -> list[tuple[str, int]]:
    """The cases the model got most wrong, by identifier. Never by text."""
    missed = [pair for pair in ranked if pair[1] > 1]
    missed.sort(key=lambda pair: (-pair[1], pair[0]))
    return missed[:WORST_CASES_REPORTED]


def format_report(
    model: Path,
    tokenizer: Path,
    dataset: Path,
    prefixes: str,
    vector_dtype: str,
    metrics: Metrics,
    ranked: Sequence[tuple[str, int]],
    per_case: bool = False,
) -> str:
    lines = [
        f"model         {model}",
        f"tokenizer     {tokenizer}",
        f"dataset       {dataset.name}",
        f"prefixes      {prefixes}",
        f"vector-dtype  {vector_dtype}",
        f"cases         {metrics.cases}",
        f"Recall@1      {metrics.recall_at_1:.4f}",
        f"Recall@5      {metrics.recall_at_5:.4f}",
        f"MRR           {metrics.mrr:.4f}",
    ]
    missed = worst_cases(ranked)
    if missed:
        named = ", ".join(f"{identifier} rank {rank}" for identifier, rank in missed)
        lines.append(f"worst ranks   {named}")
    if per_case:
        # Every rank, keyed by identifier. Two summaries of two runs cannot be
        # compared case by case, and a difference of a few hundredths in MRR over
        # 42 cases is exactly the kind of number that has to be readable as
        # "three cases moved" rather than believed as a decimal. Still only
        # identifiers and integers, so the privacy contract is unchanged.
        pairs = ", ".join(f"{identifier} {rank}" for identifier, rank in ranked)
        lines.append(f"per case      {pairs}")
    return "\n".join(lines)


def measure(
    model: Path,
    tokenizer_dir: Path,
    dataset: Path,
    prefixes: str,
    vector_dtype: str,
) -> tuple[Metrics, list[tuple[str, int]]]:
    # Cheapest check first, and the one that costs the most to discover late: a
    # missing model file would otherwise surface after the tokenizer has been
    # read, which on this model is seventeen megabytes of JSON.
    if not model.is_file():
        message = f"model not found: {model}"
        raise MeasurementError(message)
    records = load_dataset(dataset)
    tokenizer = load_tokenizer(tokenizer_dir)

    query_prefix = QUERY_PREFIX if prefixes == "on" else ""
    passage_prefix = PASSAGE_PREFIX if prefixes == "on" else ""
    passages = embed([passage_prefix + record["passage"] for record in records], model, tokenizer)
    queries = embed([query_prefix + record["query"] for record in records], model, tokenizer)

    if vector_dtype == "int8":
        passages = quantise_to_int8(passages)
        queries = quantise_to_int8(queries)

    ranks = ranks_of(queries, passages)
    ranked = list(zip((record["id"] for record in records), ranks, strict=True))
    return metrics_of(ranks), ranked


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        metrics, ranked = measure(args.model, args.tokenizer, args.dataset, args.prefixes, args.vector_dtype)
    except MeasurementError as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    print(
        format_report(
            args.model,
            args.tokenizer,
            args.dataset,
            args.prefixes,
            args.vector_dtype,
            metrics,
            ranked,
            args.per_case,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
