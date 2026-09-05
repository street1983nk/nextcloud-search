#!/usr/bin/env python3
"""Quantise the fp32 ONNX model to int8 and refuse to hand over a file of the wrong size.

This is one build step of backend/Dockerfile and it exists twice over: once to
make the model small enough for a 4 GB ARM box, and once to make the failure of
that first job loud instead of silent.

**Why the image quantises at all.** intfloat/multilingual-e5-small ships an int8
file of its own, `onnx/model_qint8_avx512_vnni.onnx`. It carries AVX512-VNNI in
its name and it means it: on the ARM board this app targets that file is either
unusable or pathologically slow. So the build starts from the fp32 original and
does the work itself.

**Why the size is checked, and checked on both sides.** The arithmetic is
simple and it is the whole argument:

    fp32 model.onnx          470_268_510 bytes   (HuggingFace API, 2026-09-04)
    a complete int8 pass     470_268_510 / 4  =  117_567_128 bytes expected
    what intfloat's own int8 file weighs        118_346_824 bytes

The factor is exactly four, which is the evidence that a complete pass also
quantises the embedding table. That table is 250_002 x 384 = 96_000_768
parameters, which is **81.7 percent of every parameter in this model**. The
transformer arithmetic runs on the remaining 21.6 million.

And that is the trap. `quantize_dynamic` rewrites `MatMul`; whether it also
rewrites the `Gather` of the embedding table is not visible at the call site. If
it does not, the table stays fp32, the result weighs about 384 MB instead of
about 118 MB, **nothing fails**, and 266 MB sit in the image and then
permanently in the resident memory of a box that has four gigabytes in total.
There is no exception, no warning and no log line that says so. The only thing
that says so is the size of the file, which is why it is measured here and why
a violation ends the build.

The lower bound is not symmetry for its own sake. A file far below the expected
weight means the pass did something other than what was asked, and a model that
is too small is exactly as much a finding as one that is too large. A gate that
can only fire in one direction is half a gate.

**What this script prints:** sizes, bounds and paths. It never opens the model
for reading and it never prints anything derived from its contents.

Run it, from anywhere, with the environment of the backend plus the build time
group that carries `onnx`:

    cd backend
    uv run --group quantize python ../scripts/dev/quantize_model.py \\
        --input /model/fp32/model.onnx --output /model/model.onnx

    uv run --group quantize python ../scripts/dev/quantize_model.py \\
        --input /model/fp32/model.onnx --output /model/model.onnx --max-bytes 1

The second form is how the gate is shown to be able to go red: it asks for an
impossible ceiling, and the script has to exit non zero and leave no output
file behind.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from onnxruntime.quantization import QuantType, quantize_dynamic

# 470_268_510 / 4. Not a target the script enforces, a number it reports next to
# what actually came out, so that a run that drifts is readable before it is
# outside the bounds.
EXPECTED_BYTES = 117_567_128

# The window, and where its edges come from. The ceiling is 130 MiB: about 11
# percent of headroom over the expected value, and far below the roughly 384 MB
# an unquantised embedding table would produce, so the gate separates the two
# cases it exists to separate. The floor is a round 100 MB, comfortably under
# the expected value and comfortably over anything that could be called a
# complete model of this architecture.
DEFAULT_MIN_BYTES = 100_000_000
DEFAULT_MAX_BYTES = 136_314_880


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Quantise an fp32 ONNX model to int8 and verify the size of the result.",
    )
    parser.add_argument("--input", required=True, type=Path, help="the fp32 model.onnx to read")
    parser.add_argument("--output", required=True, type=Path, help="the int8 model.onnx to write")
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=DEFAULT_MIN_BYTES,
        help=f"reject a result smaller than this (default {DEFAULT_MIN_BYTES})",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"reject a result larger than this (default {DEFAULT_MAX_BYTES})",
    )
    return parser.parse_args(argv)


def check_size(size: int, minimum: int, maximum: int) -> str | None:
    """The verdict on one file size, or None when it is inside the window."""
    if size > maximum:
        return (
            f"the quantised model weighs {size} bytes, more than the ceiling of {maximum}. "
            "The usual cause is an embedding table that stayed fp32, which is 81.7 percent of "
            "this model and about 266 MB of image and of permanent resident memory."
        )
    if size < minimum:
        return (
            f"the quantised model weighs {size} bytes, less than the floor of {minimum}. "
            "A model this small is not a complete model of this architecture."
        )
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input.is_file():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2
    if args.min_bytes > args.max_bytes:
        print(f"the floor {args.min_bytes} is above the ceiling {args.max_bytes}", file=sys.stderr)
        return 2

    source_size = args.input.stat().st_size
    print(f"input       {args.input}")
    print(f"input size  {source_size} bytes")
    # Two separate numbers, because conflating them would misreport every input
    # that is not the model this window was measured for: EXPECTED_BYTES is the
    # constant from the research, and a quarter of the input at hand is what a
    # complete pass over *this* file should weigh.
    print(f"expected    {EXPECTED_BYTES} bytes, the value this window was measured for")
    print(f"input / 4   {source_size // 4} bytes")
    print(f"window      {args.min_bytes} to {args.max_bytes} bytes")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    quantize_dynamic(args.input, args.output, weight_type=QuantType.QInt8)

    if not args.output.is_file():
        print(f"the quantisation wrote no file at {args.output}", file=sys.stderr)
        return 1

    size = args.output.stat().st_size
    print(f"output      {args.output}")
    print(f"output size {size} bytes")
    print(f"ratio       {source_size / size:.2f} to 1")

    verdict = check_size(size, args.min_bytes, args.max_bytes)
    if verdict is not None:
        # The bad file is removed rather than left lying next to a failed exit
        # code. A later COPY in the same build cannot pick up what is not there,
        # so the gate stays closed even if somebody ignores the exit code.
        args.output.unlink()
        print(f"REJECTED: {verdict}", file=sys.stderr)
        print(f"the output file {args.output} was removed", file=sys.stderr)
        return 1

    print("accepted: the quantised model is inside the size window")
    return 0


if __name__ == "__main__":
    sys.exit(main())
