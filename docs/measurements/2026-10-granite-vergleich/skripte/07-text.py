#!/usr/bin/env python3
"""Step 7 of the granite comparison: the text of the 500 sample files, once.

Runs inside the shipped image, so the text is what the product would index: the
extractor of findling.extract.dispatch, and for a PDF without a text layer or a
picture the OCR route behind it, the same second track the product runs. The
text does not depend on the embedding model, so it is taken once and the arm
box only embeds it; the README names this as a deviation.

Output: one JSON line per file with name, state, reason, character count and the
text, into ``--out`` (outside the repository). The raw data get name, state,
reason, characters and the sha256 of the text, never the text itself.

    python 07-text.py --corpus /corpus --out /out/texte.jsonl --report /out/07-text.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

MIMETYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "txt": "text/plain",
    "md": "text/markdown",
    "csv": "text/csv",
    "jpg": "image/jpeg",
    "png": "image/png",
    "tif": "image/tiff",
    "webp": "image/webp",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    from findling.extract.dispatch import IMAGE_MIMETYPES, Route, extract
    from findling.extract.errors import Reason

    files = sorted((path for path in args.corpus.iterdir() if path.is_file()), key=lambda p: p.name.encode("utf-8"))
    states: Counter[str] = Counter()
    rows: list[str] = []
    total_chars = 0
    started = time.perf_counter()
    with args.out.open("w", encoding="utf-8", newline="\n") as sink:
        for path in files:
            mime = MIMETYPES[path.suffix.removeprefix(".").lower()]
            size = path.stat().st_size
            outcome = extract(str(path), mime, size)
            route_label = "inhalt"
            if outcome.reason in {Reason.NO_TEXT_LAYER} or (not outcome.text and mime in IMAGE_MIMETYPES):
                outcome = extract(str(path), mime, size, route=Route.OCR)
                route_label = "ocr"
            state = f"{outcome.state.value}/{outcome.reason.value if outcome.reason else '-'}"
            states[f"{route_label} {state}"] += 1
            total_chars += len(outcome.text)
            digest = hashlib.sha256(outcome.text.encode("utf-8")).hexdigest()
            rows.append(f"{path.name},{route_label},{state},{len(outcome.text)},{digest}")
            sink.write(json.dumps({"name": path.name, "state": state, "text": outcome.text}, ensure_ascii=False) + "\n")
    elapsed = time.perf_counter() - started

    header = [
        "schritt 7 text der stichprobe, im ausgelieferten image, findling.extract.dispatch",
        f"dateien {len(files)}, zeichen gesamt {total_chars}, dauer {elapsed:.1f} s",
        *(f"zustand {key} {states[key]}" for key in sorted(states)),
        "name,weg,zustand,zeichen,sha256_text",
    ]
    args.report.write_text("\n".join([*header, *rows]) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(header))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
