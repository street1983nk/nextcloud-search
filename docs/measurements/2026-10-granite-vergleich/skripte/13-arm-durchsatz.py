#!/usr/bin/env python3
"""Step 13 of the granite comparison: embedding throughput on the fixed sample of 500 documents.

The text of the sample was extracted once in step 7 (07-text.py), so this step
measures what depends on the model and nothing else: the cut of every document
into chunks with the tokenizer of the model, and the embedding of those chunks.

The cut is the product cut, imported from the image: findling.embed.chunker with
make_splitter and chunk_spans, the chunk size, overlap and token cap out of
findling.config (the 1024 token cap of D-01, counted in tokens of the model
itself, because a different tokenizer gives different chunk borders). The
embedding mirrors embed/model.py: batches of the configured batch size,
truncation at the configured sequence length, padding with the pad token of the
model, session options of _open_session. Pooling and prefix are the switches of
the comparison: e5 mean with "passage: ", granite cls without a prefix.

Printed: counts, times and rates, plus RssAnon and the cgroup peak at the end.
Never a text (T-02-14).

    python 13-arm-durchsatz.py --texts /work/text/texte.jsonl --model /work/e5/model.onnx \\
        --tokenizer /work/e5 --pooling mean --prefix "passage: " --label e5-int8
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

THREADS = 2
CGROUP = Path("/sys/fs/cgroup")


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
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--texts", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--tokenizer", required=True, type=Path)
    parser.add_argument("--pooling", required=True, choices=("mean", "cls"))
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    import numpy
    import onnxruntime
    from tokenizers import Tokenizer

    from findling.config import settings
    from findling.embed.chunker import chunk_spans, make_splitter

    resolved = settings()
    documents = [
        str(json.loads(line)["text"]) for line in args.texts.read_text(encoding="utf-8").splitlines() if line.strip()
    ]

    load_started = time.perf_counter()
    counter = Tokenizer.from_file(str(args.tokenizer / "tokenizer.json"))
    splitter = make_splitter(counter, chunk_tokens=resolved.embed_chunk_tokens, overlap=resolved.embed_chunk_overlap)
    encoder = Tokenizer.from_file(str(args.tokenizer / "tokenizer.json"))
    encoder.enable_truncation(max_length=resolved.embed_sequence_len)
    pad_name = pad_token(args.tokenizer)
    pad_id = encoder.token_to_id(pad_name)
    encoder.enable_padding(pad_id=1 if pad_id is None else int(pad_id), pad_token=pad_name)
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = THREADS
    options.inter_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    session = onnxruntime.InferenceSession(str(args.model), options, providers=["CPUExecutionProvider"])
    accepted = {entry.name for entry in session.get_inputs()}
    load_seconds = time.perf_counter() - load_started

    def embed(texts: list[str]) -> int:
        encodings = encoder.encode_batch([args.prefix + text for text in texts])
        ids = numpy.asarray([item.ids for item in encodings], dtype=numpy.int64)
        mask = numpy.asarray([item.attention_mask for item in encodings], dtype=numpy.int64)
        feed = {"input_ids": ids, "attention_mask": mask, "token_type_ids": numpy.zeros_like(ids)}
        hidden = numpy.asarray(session.run(None, {name: value for name, value in feed.items() if name in accepted})[0])
        if args.pooling == "cls":
            pooled = hidden[:, 0, :]
        else:
            weights = mask[:, :, None].astype(hidden.dtype)
            pooled = (hidden * weights).sum(axis=1) / numpy.clip(weights.sum(axis=1), 1e-9, None)
        norms = numpy.linalg.norm(pooled, axis=1, keepdims=True)
        return int((pooled / numpy.clip(norms, 1e-12, None)).shape[0])

    chunk_seconds = 0.0
    embed_seconds = 0.0
    chunks_per_document: list[int] = []
    embedded = 0
    started = time.perf_counter()
    for text in documents:
        cut_started = time.perf_counter()
        spans = chunk_spans(text, tokenizer=counter, splitter=splitter, token_cap=resolved.embed_token_cap)
        pieces = [text[span.char_start : span.char_end] for span in spans]
        chunk_seconds += time.perf_counter() - cut_started
        chunks_per_document.append(len(pieces))
        embed_started = time.perf_counter()
        for offset in range(0, len(pieces), resolved.embed_batch_size):
            embedded += embed(pieces[offset : offset + resolved.embed_batch_size])
        embed_seconds += time.perf_counter() - embed_started
    total_seconds = time.perf_counter() - started

    lines = [
        f"label={args.label}",
        f"onnxruntime={onnxruntime.__version__}",
        f"threads={THREADS}",
        f"pooling={args.pooling}",
        f"prefix_chars={len(args.prefix)}",
        f"embed_token_cap={resolved.embed_token_cap}",
        f"embed_chunk_tokens={resolved.embed_chunk_tokens}",
        f"embed_chunk_overlap={resolved.embed_chunk_overlap}",
        f"embed_sequence_len={resolved.embed_sequence_len}",
        f"embed_batch_size={resolved.embed_batch_size}",
        f"documents={len(documents)}",
        f"chunks={sum(chunks_per_document)}",
        f"vectors={embedded}",
        f"chunks_per_document_mean={statistics.fmean(chunks_per_document):.4f}",
        f"chunks_per_document_max={max(chunks_per_document)}",
        f"load_seconds={load_seconds:.2f}",
        f"chunk_seconds={chunk_seconds:.2f}",
        f"embed_seconds={embed_seconds:.2f}",
        f"total_seconds={total_seconds:.2f}",
        f"documents_per_minute={len(documents) / total_seconds * 60:.2f}",
        f"chunks_per_second={sum(chunks_per_document) / total_seconds:.3f}",
        f"rss_anon_end_kb={rss_anon_kb()}",
        f"cgroup_memory.max={cgroup_value('memory.max')}",
        f"cgroup_memory.peak={cgroup_value('memory.peak')}",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
