"""The seed picture of the upgrade proof, held against what it has to be.

``.github/fixtures/upgrade-seed-grey-extra.tif`` is one of the two files
"Store upgrade 2b" of ``.github/workflows/deploy-harp.yml`` sows on the 1.3.2
installation (plan 29-11). The proof only means something if the picture is
exactly of the class of issue #18 that 1.3.2 cannot read and 1.4.0 can: grey
with one extra channel declared as unspecified, which Pillow 12.3.0 has no
entry for and which the shim of plan 29-07 maps. A picture that Pillow could
open on its own would let 1.3.2 index it, the seed word would answer before the
upgrade, and the recheck would prove nothing. A picture the shim could not open
would stay failed after the upgrade and turn the proof red for the wrong reason.
Both are asked here, on the committed bytes, instead of in a CI run that costs
an hour to find out.

The last statement is about where the bytes come from: the generator runs
again and has to write the committed file byte for byte, so the fixture is
never a file nobody can reproduce.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from PIL import Image, TiffImagePlugin, UnidentifiedImageError

from findling.extract import image

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / ".github" / "fixtures" / "upgrade-seed-grey-extra.tif"
GENERATOR = REPO_ROOT / "scripts" / "ci" / "make_upgrade_seed_tiff.py"

# Tags of the TIFF specification the class is defined by.
_TAG_BITS_PER_SAMPLE = 258
_TAG_COMPRESSION = 259
_TAG_PHOTOMETRIC = 262
_TAG_SAMPLES_PER_PIXEL = 277
_TAG_EXTRA_SAMPLES = 338


def _generator() -> ModuleType:
    """The generator script as a module, loaded from its path."""
    spec = importlib.util.spec_from_file_location("make_upgrade_seed_tiff", GENERATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_fixture_is_there_and_small() -> None:
    assert FIXTURE.is_file()
    assert FIXTURE.stat().st_size < 1024 * 1024


def test_the_fixture_is_big_endian_grey_with_an_unspecified_extra_channel() -> None:
    # The key (MM, 1, (1,), 1, (8, 8), (0,)) of the budachst dump, read off the
    # file rather than believed of the generator.
    assert FIXTURE.read_bytes()[:4] == b"MM\x00*"
    with Image.open(FIXTURE) as picture:
        assert isinstance(picture, TiffImagePlugin.TiffImageFile)
        tags = picture.tag_v2
        assert tags[_TAG_EXTRA_SAMPLES] == (0,)
        assert tags[_TAG_BITS_PER_SAMPLE] == (8, 8)
        assert tags[_TAG_SAMPLES_PER_PIXEL] == 2
        assert tags[_TAG_PHOTOMETRIC] == 1
        assert tags[_TAG_COMPRESSION] == 1


def test_without_the_shim_pillow_cannot_open_it(monkeypatch: pytest.MonkeyPatch) -> None:
    # A fresh copy of the table without the keys the shim added, which is the
    # table 1.3.2 runs with. UnidentifiedImageError is what 1.3.2 books as
    # failed(corrupt).
    assert image._SHIM_KEYS
    untouched = {key: value for key, value in TiffImagePlugin.OPEN_INFO.items() if key not in image._SHIM_KEYS}
    monkeypatch.setattr(TiffImagePlugin, "OPEN_INFO", untouched)

    with pytest.raises(UnidentifiedImageError):
        Image.open(FIXTURE)


def test_with_the_shim_it_is_read_and_turns_grey() -> None:
    with Image.open(FIXTURE) as picture:
        assert picture.mode == "LA"
        grey = picture.convert("L")
    # White paper and black writing, so the engine gets a page and not a void.
    assert grey.getextrema() == (0, 255)


def test_the_picture_passes_the_shape_rules_of_the_image_path() -> None:
    # Under the long edge minimum or over the aspect ratio the picture would
    # be skipped before the engine sees it, and the seed word would never be
    # found after the upgrade.
    with Image.open(FIXTURE) as picture:
        width, height = picture.size
    assert max(width, height) >= image._MIN_LONG_EDGE_PIXELS
    assert max(width, height) / min(width, height) <= image._MAX_ASPECT_RATIO


def test_the_generator_writes_the_committed_bytes_again() -> None:
    assert _generator().render() == FIXTURE.read_bytes()


def test_the_seed_word_is_drawn_more_than_once() -> None:
    # One misread line must still leave the word findable, and the text of the
    # picture has to clear the twenty characters a picture needs.
    module = _generator()
    assert module.LINES.count(module.SEED_WORD) >= 2
    assert len(" ".join(module.LINES)) > image._MIN_OCR_CHARS
