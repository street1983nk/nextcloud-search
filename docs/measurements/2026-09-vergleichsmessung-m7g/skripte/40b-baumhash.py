#!/usr/bin/env python3
"""The tree hash of a package, as a callable file instead of a heredoc.

The recipe is word for word the one of 40-abbild.sh of the semantic run: sha256
over the sorted sequence of the relative posix path, a NUL byte, the sha256 of
the file content with CRLF folded to LF, and a newline. It must not be changed.
A different recipe yields a different hash, and the comparison against the
figures the predecessor reports quote, 278fab52 of the follow up measurement and
6c47cd21 of this tree, is the only thing that makes the sentence "the image and
the working tree are the same state" more than a claim. An improvement here
would quietly retire every number that was ever measured with it. The two output
labels are German for the same reason: the raw data of both predecessors are read
with those two words.

The script prints no file content. It prints the number of files and one hash,
and the per file digest never leaves the process, because the root it is pointed
at may be a directory of user documents rather than a python package.

Two positional arguments, the root directory and the glob, for instance "**/*.py"
for the python package and "**/*.php" for the php half. An empty result is a
failure and not a hash over nothing: a root that does not exist and a glob that
matches no file both end with exit code 2 and a diagnosis on standard error.
That is the failure of both predecessors turned around, where the step produced
no line at all and the report claimed the equality anyway.

Standard library only, because this runs inside the image and the image is
offline.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

TOOL = "40b-baumhash"


def tree_hash(root: Path, pattern: str) -> tuple[int, str]:
    """The number of files and the hex digest of the recipe above, over one root."""
    digest = hashlib.sha256()
    count = 0
    # Sorted by the relative posix path, which is the string the hash is built
    # from, and NOT by the Path object. That distinction is the whole recipe:
    # comparing Path objects compares a platform dependent form, because the
    # Windows flavour folds case and the posix one does not. Measured on
    # 2026-09-09 against php with its 58 files, whose content is byte identical
    # on both machines: Windows put tests/bootstrap.php before tests/Unit/... and
    # produced 26b55908..., the box put tests/Unit/... first and produced
    # 4a4c6f62..., and the box was right about the recipe. The tree hash is the
    # only proof that the image and the working tree are the same state, so a
    # hash that depends on the machine that computes it turns that proof into a
    # coin toss, and it had CI red on ubuntu since this file was added.
    # Nothing that was ever reported changes: the python package yields
    # 6c47cd21... under both sort keys on both platforms, so the comparability
    # against 278fab52 of the follow up measurement is untouched. The only figure
    # that moves is the php one, and it was never valid on more than one machine.
    for path in sorted(root.glob(pattern), key=lambda candidate: candidate.relative_to(root).as_posix()):
        # Only a regular file carries bytes. This guard cannot change the hash of
        # a python package or a php tree, it keeps a directory whose name happens
        # to end in the extension from ending the step with a stack trace.
        if not path.is_file():
            continue
        data = path.read_bytes().replace(b"\r\n", b"\n")
        digest.update(
            path.relative_to(root).as_posix().encode() + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n"
        )
        count += 1
    return count, digest.hexdigest()


def main(argv: list[str]) -> int:
    """The two lines of output, or a diagnosis and exit code 2."""
    if len(argv) != 3:
        print(f"{TOOL}: usage: {TOOL}.py <root> <glob>", file=sys.stderr)
        return 2
    root = Path(argv[1])
    pattern = argv[2]
    if not root.is_dir():
        print(f"{TOOL}: no such directory: {root}", file=sys.stderr)
        return 2
    count, hexdigest = tree_hash(root, pattern)
    if count == 0:
        print(f"{TOOL}: no file under {root} matches {pattern}", file=sys.stderr)
        return 2
    print("dateien:", count)
    print("baumhash:", hexdigest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
