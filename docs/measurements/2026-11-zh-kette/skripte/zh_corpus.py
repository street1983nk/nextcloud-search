#!/usr/bin/env python3
"""Turn saved law.moj.gov.tw pages into one text file per article, and say what went in.

The corpus of this run is Taiwanese statutes, which are not protected by
copyright (Copyright Act of Taiwan, article 9). The pages are fetched by the
loop in the README of this run and saved under their pcode; this script reads
them, writes one text file per article into the output directory and prints a
manifest line per page: pcode, title, articles, characters and the sha256 of the
saved page, so that the corpus can be fetched again and compared.

Run from backend/, because lxml lives in that environment:

    uv run python -I ../docs/measurements/2026-11-zh-kette/skripte/zh_corpus.py <pages> <articles>
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from lxml import html


def main(pages: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for page in sorted(pages.glob("*.html")):
        raw = page.read_bytes()
        tree = html.fromstring(raw)
        title = "".join(tree.xpath("//a[@id='hlLawName']//text()")).strip()
        rows = tree.xpath("//div[contains(@class,'law-reg-content')]//div[@class='row']")
        articles = 0
        characters = 0
        for row in rows:
            number = "".join(row.xpath(".//div[contains(@class,'col-no')]//text()")).strip()
            lines = [text.strip() for text in row.xpath(".//div[contains(@class,'law-article')]//text()")]
            body = "\n".join(line for line in lines if line)
            if not body:
                continue
            articles += 1
            characters += len(body)
            (out / f"{page.stem}-{articles:04d}.txt").write_text(f"{title} {number}\n{body}\n", encoding="utf-8")
        total += characters
        print(f"{page.stem}\t{title}\t{articles}\t{characters}\t{hashlib.sha256(raw).hexdigest()}")
    print(f"total characters\t{total}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
