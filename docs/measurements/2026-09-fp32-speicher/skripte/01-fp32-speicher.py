#!/usr/bin/env python3
"""Resident anonymous memory of e5-small, int8 against fp32, in one fresh process.

Research assumption A1 of phase 25 left the runtime memory of the fp32 weights
unmeasured, and D-25-01 wants the RAM gate of the embedding track to include the
fp32 extra. This script measures one precision per process: RssAnon before the
load, after the InferenceSession exists, and after the first batch. Then five
more batches give a rate in passages per second.

RssAnon and not VmRSS: the weights of an ONNX session end up in anonymous
memory, while file backed pages of shared libraries are reclaimable page cache
and would blur the comparison.

The session is opened with the options of the product, copied from
backend/src/findling/embed/model.py::_open_session (lines 334-340):
intra_op_num_threads = THREADS (2, model.py line 113), inter_op_num_threads = 1,
enable_cpu_mem_arena = False, CPUExecutionProvider only. They are copied rather
than imported so that the measurement does not depend on which revision of the
product the image carries.

The passages are fixed English sentences written into this file, long enough
that every one of them is truncated at the sequence length, which is the worst
case for the activations. No user data, no paths in the output, no network.
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

# Imported before the first reading on purpose: the libraries are the same for
# both precisions, and only the weights and the activations should show up in the
# deltas.
import numpy
import onnxruntime
from tokenizers import Tokenizer

from findling.config import settings

# model.py line 113.
THREADS = 2
BATCH = 8
EXTRA_BATCHES = 5
PASSAGE_PREFIX = "passage: "
TOKENIZER_FILE = "tokenizer.json"
PAD_MARKER = "<pad>"

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
# Long enough to hit the truncation for every passage.
PASSAGES = [sentence * 60 for sentence in _SENTENCES]


def rss_anon_kb() -> int:
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith("RssAnon:"):
            return int(line.split()[1])
    return -1


def open_encoder(model_dir: Path, sequence_len: int) -> Tokenizer:
    # Same shape as model.py::_open_encoder: truncated and padded.
    encoder = Tokenizer.from_file(str(model_dir / TOKENIZER_FILE))
    encoder.enable_truncation(max_length=sequence_len)
    pad_id = encoder.token_to_id(PAD_MARKER)
    if pad_id is None:
        pad_id = 0
    encoder.enable_padding(pad_id=pad_id, pad_token=PAD_MARKER)
    return encoder


def open_session(weights: Path) -> onnxruntime.InferenceSession:
    # model.py::_open_session, lines 336-340.
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = THREADS
    options.inter_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    return onnxruntime.InferenceSession(str(weights), options, providers=["CPUExecutionProvider"])


def run_batch(session: onnxruntime.InferenceSession, encoder: Tokenizer, texts: list[str]) -> int:
    encodings = encoder.encode_batch([PASSAGE_PREFIX + text for text in texts])
    ids = numpy.asarray([item.ids for item in encodings], dtype=numpy.int64)
    mask = numpy.asarray([item.attention_mask for item in encodings], dtype=numpy.int64)
    accepted = {item.name for item in session.get_inputs()}
    feed = {"input_ids": ids, "attention_mask": mask, "token_type_ids": numpy.zeros_like(ids)}
    outputs = [session.get_outputs()[0].name]
    hidden = session.run(outputs, {name: value for name, value in feed.items() if name in accepted})[0]
    weights = mask[:, :, None].astype(hidden.dtype)
    pooled = (hidden * weights).sum(axis=1) / numpy.clip(weights.sum(axis=1), 1e-9, None)
    return int(pooled.shape[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--label", required=True, choices=("int8", "fp32"))
    args = parser.parse_args()

    resolved = settings()
    sequence_len = resolved.embed_sequence_len
    encoder = open_encoder(resolved.embed_model_dir, sequence_len)

    before = rss_anon_kb()
    session = open_session(args.weights)
    after_session = rss_anon_kb()
    run_batch(session, encoder, PASSAGES[:BATCH])
    after_first = rss_anon_kb()

    durations: list[float] = []
    count = 0
    for _ in range(EXTRA_BATCHES):
        start = time.perf_counter()
        count += run_batch(session, encoder, PASSAGES[:BATCH])
        durations.append(time.perf_counter() - start)
    after_all = rss_anon_kb()

    rate = count / sum(durations)
    lines = [
        "label=" + args.label,
        "sequence_len=" + str(sequence_len),
        "embed_token_cap=" + str(resolved.embed_token_cap),
        "batch=" + str(BATCH),
        "threads=" + str(THREADS),
        "onnxruntime=" + onnxruntime.__version__,
        "rss_anon_before_kb=" + str(before),
        "rss_anon_session_kb=" + str(after_session),
        "rss_anon_first_batch_kb=" + str(after_first),
        "rss_anon_after_all_kb=" + str(after_all),
        "batch_seconds_median=" + format(statistics.median(durations), ".4f"),
        "passages_per_second=" + format(rate, ".3f"),
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
