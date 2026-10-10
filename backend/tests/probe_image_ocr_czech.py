"""Czech OCR in the built image (CZ-01), run as a plain script.

Not named ``test_*`` on purpose: pytest must not collect it. It needs the
tesseract engine and the ``ces`` traineddata, which exist in the image and on
no development machine. The file lives under ``tests`` because that is the
directory ``.github/workflows/docker.yml`` bind mounts into the container, the
same way ``probe_image_search.py`` travels in.

What it proves: the package ``tesseract-ocr-ces`` is in the image (``tesseract
--list-langs`` names ``ces``), and a rendered Czech page read with ``-l ces``
comes back as text whose tokens, through the stemmerless chain ``cs`` of
``findling.index.analyzer.czech_analyzer``, contain the expected folded words.
That is the chain from a scan to search terms, minus the index itself.

What the words alone do not prove: that the Czech model read them. The chain
folds the accents away before the comparison, and the English model reads the
same strip as "Najemni smlouva na byt v Brné, ucetni rizeni, rijen", which
folds to the same four words (finding WR-02 of the phase 30 review). So the raw
text is checked as well, before any folding, for letters only a model with the
Czech alphabet writes (``CZECH_ONLY``: r, e, c, u, s, z and n with caron or
ring, none of which English, German or French use). The rendered sentence
carries four of them; at least three are required.

And so that this second check cannot be green for a reason of its own, the
same strip is read once more with ``eng`` and has to yield none of those
letters. That is the positive control of the distinction: the check tells the
two models apart on this very page, so a later change that drops ``-l ces`` or
swaps the model fails it.

What it does not prove: character accuracy. The sentence is self written
(no user data), rendered with DejaVu Sans (``testdata/fonts``, licence in
``COPYING.dejavu``) at a size equivalent to 300 dpi body text, and both
thresholds leave room for one misread character, so that a point release of
the engine or of the traineddata that misreads one diacritic does not turn the
step red.

The empty answer is the trap of every OCR proof (T-06-49): a verdict that only
looks for words would be green on an engine that returns nothing as long as the
check is wrong. So the same call is made on a white page of the same size, and
that one has to yield zero tokens. The script is green only if every check holds.

Nothing recognised is printed except counts and the expected words found
(T-30-10).

Run it like this:

    docker run --rm --network none -v "$PWD/backend/tests:/probe:ro" \\
        -v "$PWD/testdata/fonts:/fonts:ro" \\
        --entrypoint python IMAGE /probe/probe_image_ocr_czech.py /fonts/DejaVuSans.ttf
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from findling.extract.ocr import read_page
from findling.index.analyzer import czech_analyzer

# Self written, with the diacritics the folding has to undo (test data, like
# the Czech samples in test_czech_analyzer.py).
SENTENCE: Final = "Nájemní smlouva na byt v Brně, účetní řízení, říjen"
EXPECTED: Final = ("smlouva", "ucetni", "rizeni", "rijen")
REQUIRED_HITS: Final = 3

# Letters of the Czech alphabet outside every Latin alphabet the default models
# cover. SENTENCE carries four of them (r caron twice, e caron, c caron).
CZECH_ONLY: Final = "řěčůšžň"
REQUIRED_CZECH_LETTERS: Final = 3

# Roughly 13 pt at 300 dpi; the canvas is a strip of an A4 page, not a whole
# page, because the only thing that matters is the line and its size.
FONT_PIXELS: Final = 56
WIDTH: Final = 2000
HEIGHT: Final = 300
PAGE_SECONDS: Final = 30
DEFAULT_FONT: Final = "/fonts/DejaVuSans.ttf"


def _png(font_path: str | None) -> bytes:
    """A white strip, with the sentence on it when a font is given."""
    image = Image.new("L", (WIDTH, HEIGHT), color=255)
    if font_path is not None:
        font = ImageFont.truetype(font_path, FONT_PIXELS)
        ImageDraw.Draw(image).text((80, 110), SENTENCE, fill=0, font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", dpi=(300, 300))
    return buffer.getvalue()


def _ces_is_listed() -> bool:
    """True when the installed engine names ces as one of its languages."""
    finished = subprocess.run(
        ["tesseract", "--list-langs"],  # noqa: S607 - the engine is on PATH in the image
        capture_output=True,
        check=False,
        timeout=PAGE_SECONDS,
    )
    listing = (finished.stdout + finished.stderr).decode("utf-8", errors="replace")
    return "ces" in {line.strip() for line in listing.splitlines()}


def _czech_letters(raw: str) -> int:
    """How many letters of the raw text only a Czech model writes."""
    return sum(raw.count(letter) for letter in CZECH_ONLY)


def main(argv: list[str]) -> int:
    """Run all three halves and return the exit code."""
    font_path = argv[1] if len(argv) > 1 else DEFAULT_FONT
    if not Path(font_path).is_file():
        print(f"font missing: {font_path}")
        return 2

    listed = _ces_is_listed()
    print(f"tesseract --list-langs names ces: {listed}")

    chain = czech_analyzer()
    page = _png(font_path)
    raw = read_page(page, "ces", PAGE_SECONDS)
    tokens = chain.analyze(raw)
    found = [word for word in EXPECTED if word in tokens]
    print(f"czech page: {len(tokens)} tokens, {len(found)} of {len(EXPECTED)} expected: {', '.join(found)}")
    letters = _czech_letters(raw)
    print(f"czech page: {letters} letters only a Czech model writes (at least {REQUIRED_CZECH_LETTERS})")

    control = _czech_letters(read_page(page, "eng", PAGE_SECONDS))
    print(f"same page read with eng: {control} such letters (must be 0)")

    blank = chain.analyze(read_page(_png(None), "ces", PAGE_SECONDS))
    print(f"white page: {len(blank)} tokens")

    ok = listed and len(found) >= REQUIRED_HITS and letters >= REQUIRED_CZECH_LETTERS and control == 0 and not blank
    print("czech ocr in the image: " + ("ok" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
