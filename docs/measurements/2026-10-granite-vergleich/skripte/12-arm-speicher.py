#!/usr/bin/env python3
"""Step 12 of the granite comparison: anonymous memory of one model, in one fresh process.

The method of docs/measurements/2026-09-fp32-speicher/, section 3, widened to a
second model: RssAnon out of /proc/self/status at five points, and at the end
the memory.peak of the cgroup the container runs in.

    start      the interpreter, nothing of the model stack imported
    libs       numpy, onnxruntime and tokenizers imported
    tokenizer  the tokenizer of the model loaded and configured
    session    the InferenceSession created (the weights)
    batch1     after the first batch of eight passages at 512 tokens
    batch6     after five more batches, which also give a rate

The README asks for "before the load, after the session, after the first
batch"; "before the load" is the reading tokenizer, so that the delta to session
is the weights alone, as in September. The others are written for context.

Session options as the product (embed/model.py::_open_session): two intra op
threads, one inter op thread, memory arena off, CPU provider only. The passages
are fixed sentences in this file, long enough to be cut at 512 tokens for every
one of them, the worst case of the activations. No user data, no paths printed.

    python 12-arm-speicher.py --model /work/granite-int8-a/model.onnx --tokenizer /work/granite \\
        --pooling cls --prefix "" --label granite-int8
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

THREADS = 2
BATCH = 8
EXTRA_BATCHES = 5
SEQUENCE = 512
CGROUP = Path("/sys/fs/cgroup")

_SENTENCES = (
    "The quarterly report lists every invoice that was paid after its due date. ",
    "A tenant may terminate the lease with three months of notice in writing. ",
    "The meeting minutes record who attended and which decisions were taken. ",
    "Scanned receipts are kept for ten years to satisfy the tax authority. ",
    "The maintenance contract covers the heating system and the water pipes. ",
    "Every employee receives the updated travel policy by the end of the month. ",
    "The project plan names the milestones, the owners and the open risks. ",
    "Insurance claims need a copy of the police report and a list of damages. ",
)
PASSAGES = [sentence * 60 for sentence in _SENTENCES]


def rss_anon_kb() -> int:
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith("RssAnon:"):
            return int(line.split()[1])
    return -1


def cgroup_value(name: str) -> str:
    source = CGROUP / name
    return source.read_text(encoding="utf-8").strip() if source.is_file() else "fehlt"


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


def main() -> int:
    readings = {"start": rss_anon_kb()}
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--tokenizer", required=True, type=Path)
    parser.add_argument("--pooling", required=True, choices=("mean", "cls"))
    parser.add_argument("--prefix", required=True, help='passage prefix, "passage: " for e5, "" for granite')
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    import numpy
    import onnxruntime
    from tokenizers import Tokenizer

    readings["libs"] = rss_anon_kb()

    encoder = Tokenizer.from_file(str(args.tokenizer / "tokenizer.json"))
    encoder.enable_truncation(max_length=SEQUENCE)
    pad_name = pad_token(args.tokenizer)
    pad_id = encoder.token_to_id(pad_name)
    encoder.enable_padding(pad_id=1 if pad_id is None else int(pad_id), pad_token=pad_name)
    readings["tokenizer"] = rss_anon_kb()

    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = THREADS
    options.inter_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    session = onnxruntime.InferenceSession(str(args.model), options, providers=["CPUExecutionProvider"])
    accepted = {entry.name for entry in session.get_inputs()}
    readings["session"] = rss_anon_kb()

    def run_batch() -> int:
        encodings = encoder.encode_batch([args.prefix + text for text in PASSAGES[:BATCH]])
        ids = numpy.asarray([item.ids for item in encodings], dtype=numpy.int64)
        mask = numpy.asarray([item.attention_mask for item in encodings], dtype=numpy.int64)
        feed = {"input_ids": ids, "attention_mask": mask, "token_type_ids": numpy.zeros_like(ids)}
        hidden = numpy.asarray(session.run(None, {name: value for name, value in feed.items() if name in accepted})[0])
        if args.pooling == "cls":
            pooled = hidden[:, 0, :]
        else:
            weights = mask[:, :, None].astype(hidden.dtype)
            pooled = (hidden * weights).sum(axis=1) / numpy.clip(weights.sum(axis=1), 1e-9, None)
        return int(pooled.shape[0])

    run_batch()
    readings["batch1"] = rss_anon_kb()
    durations: list[float] = []
    count = 0
    for _ in range(EXTRA_BATCHES):
        started = time.perf_counter()
        count += run_batch()
        durations.append(time.perf_counter() - started)
    readings["batch6"] = rss_anon_kb()

    lines = [
        f"label={args.label}",
        f"pooling={args.pooling}",
        f"prefix_chars={len(args.prefix)}",
        f"sequence={SEQUENCE}",
        f"batch={BATCH}",
        f"threads={THREADS}",
        f"onnxruntime={onnxruntime.__version__}",
        *(f"rss_anon_{key}_kb={value}" for key, value in readings.items()),
        f"delta_session_kb={readings['session'] - readings['tokenizer']}",
        f"delta_batch1_kb={readings['batch1'] - readings['tokenizer']}",
        f"cgroup_memory.max={cgroup_value('memory.max')}",
        f"cgroup_memory.swap.max={cgroup_value('memory.swap.max')}",
        f"cgroup_memory.peak={cgroup_value('memory.peak')}",
        f"cgroup_memory.current={cgroup_value('memory.current')}",
        f"batch_seconds_median={statistics.median(durations):.4f}",
        f"passages_per_second={count / sum(durations):.3f}",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
