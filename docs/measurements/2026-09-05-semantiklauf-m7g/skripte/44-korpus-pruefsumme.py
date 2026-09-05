#!/usr/bin/env python3
"""Recompute the listing checksum of the corpus that is already on the box.

The corpus is not rebuilt for this run. It is the same 50.000 files that plan
05-21 measured, and rebuilding them would cost 43 minutes and change nothing.
What has to be shown is that they are still the same bytes, so the checksum is
recomputed with the rule the generator uses: sha256 over the sorted lines
"name,size,sha256", ascii, joined by newline (scripts/dev/build_load_corpus.py).
"""

from __future__ import annotations

import hashlib
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
listing: list[str] = []
total = 0
for p in sorted(root.iterdir()):
    if not p.is_file():
        continue
    data = p.read_bytes()
    total += len(data)
    listing.append(f"{p.name},{len(data)},{hashlib.sha256(data).hexdigest()}")

checksum = hashlib.sha256("\n".join(sorted(listing)).encode("ascii")).hexdigest()
print(f"verify_load_corpus: dir={root} files={len(listing)} bytes={total} checksum={checksum}")
