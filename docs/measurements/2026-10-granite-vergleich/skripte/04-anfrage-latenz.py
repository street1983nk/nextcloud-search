#!/usr/bin/env python3
"""Single query latency of one embedding model, cold and warm, with onnxruntime directly.

Why not the search path of the product: its model wrapper is fixed to e5 (mean
pooling, the two prefixes, a pad token looked up as ``<pad>``), so granite does
not run through it without a code change, and plan 35-09 changes no product
code (pitfall 12). Both models therefore go through this one file, with the same
tokenizer handling and the same session options, so the comparison stays fair.

Cold is one process from its start: tokenizer and session are built, then the
first query is embedded. The script prints the three parts separately
(``load_ms`` for tokenizer plus session, ``first_query_ms``, and their sum
``cold_ms``), because the product loads its model lazily on the first search
and the sum is what that first search waits for. Run it once per fresh
container to get one cold sample.

Warm is the same session after ten throw away queries: ``--warm`` queries out
of the test set, one at a time, batch size one, as a search sends them. p50 and
p95 over those.

What this prints: numbers and switches. Never a query (T-02-14, T-06-11).

    python 04-anfrage-latenz.py --model /model/model.onnx --tokenizer /model \\
        --dataset /data/de.jsonl --pooling cls --prefix "" --warm 100
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path

STARTED = time.perf_counter()

MAX_SEQUENCE_TOKENS = 512
WARM_UP = 10


def pad_token(directory: Path) -> str:
    """The same order as scripts/dev/model_quality.py: the special tokens map, then the tokenizer config."""
    for name in ("special_tokens_map.json", "tokenizer_config.json"):
        source = directory / name
        if source.is_file():
            named = json.loads(source.read_text(encoding="utf-8")).get("pad_token")
            if isinstance(named, dict) and isinstance(named.get("content"), str):
                return named["content"]
            if isinstance(named, str):
                return named
    return "<pad>"


def percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--tokenizer", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--pooling", required=True, choices=("mean", "cls"))
    parser.add_argument("--prefix", required=True, help='query prefix, "query: " for e5, "" for granite')
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--warm", type=int, default=100)
    args = parser.parse_args()

    queries = [
        str(json.loads(line)["query"]) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    imported = time.perf_counter()

    import numpy
    import onnxruntime
    from tokenizers import Tokenizer

    load_started = time.perf_counter()
    tokenizer = Tokenizer.from_file(str(args.tokenizer / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=MAX_SEQUENCE_TOKENS)
    pad_name = pad_token(args.tokenizer)
    pad_id = tokenizer.token_to_id(pad_name)
    tokenizer.enable_padding(pad_id=1 if pad_id is None else int(pad_id), pad_token=pad_name)
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = args.threads
    options.inter_op_num_threads = 1
    session = onnxruntime.InferenceSession(str(args.model), options, providers=["CPUExecutionProvider"])
    accepted = {entry.name for entry in session.get_inputs()}
    load_ms = (time.perf_counter() - load_started) * 1000

    def embed(text: str) -> object:
        encoding = tokenizer.encode(args.prefix + text)
        ids = numpy.array([encoding.ids], dtype=numpy.int64)
        mask = numpy.array([encoding.attention_mask], dtype=numpy.int64)
        feed = {"input_ids": ids, "attention_mask": mask, "token_type_ids": numpy.zeros_like(ids)}
        hidden = session.run(None, {name: value for name, value in feed.items() if name in accepted})[0]
        if args.pooling == "cls":
            vector = hidden[:, 0, :]
        else:
            weights = mask[:, :, None].astype(numpy.float32)
            vector = (hidden * weights).sum(axis=1) / weights.sum(axis=1)
        return vector / numpy.linalg.norm(vector, axis=1, keepdims=True)

    first_started = time.perf_counter()
    embed(queries[0])
    first_query_ms = (time.perf_counter() - first_started) * 1000

    for number in range(WARM_UP):
        embed(queries[(1 + number) % len(queries)])
    durations: list[float] = []
    for number in range(args.warm):
        text = queries[number % len(queries)]
        started = time.perf_counter()
        embed(text)
        durations.append((time.perf_counter() - started) * 1000)

    lines = [
        f"cpus_visible={len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count()}",
        f"onnxruntime={onnxruntime.__version__}",
        f"threads={args.threads}",
        f"pooling={args.pooling}",
        f"prefix_chars={len(args.prefix)}",
        f"max_sequence_tokens={MAX_SEQUENCE_TOKENS}",
        f"startup_to_import_ms={(imported - STARTED) * 1000:.1f}",
        f"load_ms={load_ms:.1f}",
        f"first_query_ms={first_query_ms:.1f}",
        f"cold_ms={load_ms + first_query_ms:.1f}",
        f"warm_queries={len(durations)}",
        f"warm_p50_ms={statistics.median(durations):.2f}",
        f"warm_p95_ms={percentile(durations, 0.95):.2f}",
        f"warm_max_ms={max(durations):.2f}",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
