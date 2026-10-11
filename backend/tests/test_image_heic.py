"""HEIC and HEIF through the hardened picture branch of extract/image.py (FMT-05).

A phone photograph from an iPhone arrives as HEIC, and since plan 31-07 the
picture branch opens it with pillow-heif registered as a Pillow plugin. The
registration is a module side effect of ``findling.extract.image``, next to the
bomb guard, so these tests import that module and nothing else.

Every picture here is written at test time with the HEIF encoder that ships in
the pillow-heif wheel (x265), from a canvas drawn in this file with DejaVu Sans
(``testdata/fonts``, licence in ``COPYING.dejavu``). No photograph of anybody,
no file from the internet, and nothing to keep in sync with a fixture on disk.

The engine is replaced by a stand in for ``subprocess.run`` exactly as in
test_ocr.py, so the path up to the engine call holds on every machine; the one
test that needs the real tesseract is marked and runs in the container. The
binding proof on both architectures is the image probe
``probe_image_ocr_heic.py`` in docker.yml.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import pillow_heif
import pytest
from PIL import Image, ImageDraw, ImageFont

from findling.extract import image, ocr
from findling.extract.errors import Reason, State

FONT = Path(__file__).resolve().parents[2] / "testdata" / "fonts" / "DejaVuSans.ttf"

# The word the engine has to find, made up so that it stands in no dictionary
# and in no other file of the repository, like the -quendel words of 31-05/06.
TERM = "fotoquendel"
SENTENCE = f"{TERM} im Kellerarchiv der Gemeinde"

# Over the minimum edge of 640 pixels and well under the aspect ratio cap, so
# the picture is a plausible document and reaches the engine.
PAGE = (1200, 300)

needs_engine = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="no tesseract on this machine; the container runs this test for real",
)


@dataclass(frozen=True, slots=True)
class _Finished:
    returncode: int = 0
    stdout: bytes = b""
    stderr: bytes = b""


@dataclass(slots=True)
class _Engine:
    """A stand in for the engine that records what it was given, as in test_ocr.py."""

    answers: Callable[[int], _Finished]
    calls: list[dict[str, object]] = field(default_factory=list)

    def run(self, argv: list[str], **options: object) -> _Finished:
        self.calls.append({"argv": argv, **options})
        return self.answers(len(self.calls) - 1)


def _install_engine(monkeypatch: pytest.MonkeyPatch) -> _Engine:
    engine = _Engine(lambda _number: _Finished(stdout=f"{SENTENCE}, Seite eins\n".encode()))
    monkeypatch.setattr(ocr.subprocess, "run", engine.run)
    return engine


def _handed_over(engine: _Engine) -> Image.Image:
    payload = engine.calls[0]["input"]
    assert isinstance(payload, bytes)
    return Image.open(BytesIO(payload))


def _canvas(size: tuple[int, int]) -> Image.Image:
    """A white RGB page with the sentence on it, left half dark so a turn would show."""
    picture = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(picture)
    font = ImageFont.truetype(str(FONT), max(12, size[1] // 6))
    draw.text((size[0] // 20, size[1] // 3), SENTENCE, fill="black", font=font)
    draw.rectangle((0, 0, size[0] // 10, size[1]), fill="black")
    return picture


def _heic(tmp_path: Path, name: str, size: tuple[int, int] = PAGE, orientation: int | None = None) -> Path:
    """A HEIC written by the encoder in the pillow-heif wheel."""
    path = tmp_path / name
    with _canvas(size) as picture:
        extra: dict[str, object] = {}
        if orientation is not None:
            exif = Image.Exif()
            exif[0x0112] = orientation
            extra["exif"] = exif.tobytes()
        pillow_heif.from_pillow(picture).save(path, quality=80, **extra)
    return path


def _jpeg(tmp_path: Path, name: str, size: tuple[int, int] = PAGE, orientation: int | None = None) -> Path:
    """The same canvas as a JPEG, the reference every HEIC verdict is compared with."""
    path = tmp_path / name
    with _canvas(size) as picture:
        extra: dict[str, object] = {}
        if orientation is not None:
            exif = Image.Exif()
            exif[0x0112] = orientation
            extra["exif"] = exif.tobytes()
        picture.save(path, format="JPEG", quality=80, **extra)
    return path


def test_a_heic_opens_as_heif_after_the_import(tmp_path: Path) -> None:
    path = _heic(tmp_path, "klein.heic", (400, 200))

    with Image.open(path) as picture:
        assert picture.format == "HEIF"
        assert picture.size == (400, 200)


def test_the_opener_is_registered_with_the_four_options() -> None:
    # Pitfall 11: no thumbnail may stand in for the picture, no depth or
    # auxiliary image is decoded at all, and one decoder thread lives under
    # RLIMIT_AS (assumption A5). The library defaults are True, True, True and 4.
    assert pillow_heif.options.THUMBNAILS is False
    assert pillow_heif.options.DEPTH_IMAGES is False
    assert pillow_heif.options.AUX_IMAGES is False
    assert pillow_heif.options.DECODE_THREADS == 1


def test_a_heic_reaches_the_engine_upright_and_whole(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _install_engine(monkeypatch)

    outcome = image.extract_image(str(_heic(tmp_path, "seite.heic")))

    assert outcome.state is State.INDEXED
    assert TERM in outcome.text
    assert len(engine.calls) == 1
    with _handed_over(engine) as handed:
        assert handed.size == PAGE
        assert handed.mode == "L"


@needs_engine
def test_the_engine_reads_the_word_of_a_heic(tmp_path: Path) -> None:
    outcome = image.extract_image(str(_heic(tmp_path, "seite.heic")))

    assert outcome.state is State.INDEXED
    assert TERM in outcome.text.lower()


@pytest.mark.parametrize("declared_over", [1.5, 3.0], ids=["warning-range", "error-range"])
def test_a_heic_over_the_pixel_cap_gets_the_verdict_of_a_jpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, declared_over: float
) -> None:
    # The cap is lowered instead of writing a fifty megapixel file, which would
    # allocate the memory the rule exists to prevent. Pillow warns from
    # MAX_IMAGE_PIXELS on and raises at twice it; both halves are covered, and
    # the JPEG of the same size is the reference.
    engine = _install_engine(monkeypatch)
    cap = int(PAGE[0] * PAGE[1] / declared_over)
    monkeypatch.setattr(image, "_MAX_PIXELS", cap)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", cap)

    heic = image.extract_image(str(_heic(tmp_path, "gross.heic")))
    jpeg = image.extract_image(str(_jpeg(tmp_path, "gross.jpg")))

    assert (heic.state, heic.reason) == (State.SKIPPED, Reason.TOO_LARGE)
    assert (heic.state, heic.reason, heic.detail) == (jpeg.state, jpeg.reason, jpeg.detail)
    assert engine.calls == []


def test_a_heic_cut_at_the_end_is_corrupt_and_not_a_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The header parses, the pixel data is gone: libheif reports that as a
    # ValueError from load() (31-RESEARCH, Muster 7), not as the OSError every
    # other decoder of this branch raises.
    engine = _install_engine(monkeypatch)
    whole = _heic(tmp_path, "ganz.heic").read_bytes()
    cut = tmp_path / "abgeschnitten.heic"
    cut.write_bytes(whole[: len(whole) // 2])

    outcome = image.extract_image(str(cut))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT
    assert outcome.detail == "builtins.ValueError"
    assert engine.calls == []


def test_a_heic_cut_in_its_header_is_what_an_unidentified_picture_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 300 bytes keep the ftyp box and part of the meta box; the plugin refuses
    # it while opening, which Pillow reports as UnidentifiedImageError.
    engine = _install_engine(monkeypatch)
    whole = _heic(tmp_path, "ganz.heic").read_bytes()
    cut = tmp_path / "kopf.heic"
    cut.write_bytes(whole[:300])

    outcome = image.extract_image(str(cut))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT
    assert outcome.detail == "PIL.UnidentifiedImageError"
    assert engine.calls == []


def test_an_orientation_of_six_turns_a_heic_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # libheif applies the turn the encoder wrote and the plugin sets the EXIF
    # orientation back to 1, so exif_transpose in the branch must not turn the
    # picture a second time. The reference is the JPEG of the same canvas with
    # the same orientation, which the branch turns exactly once.
    engine = _install_engine(monkeypatch)
    image.extract_image(str(_jpeg(tmp_path, "hochkant.jpg", orientation=6)))
    image.extract_image(str(_heic(tmp_path, "hochkant.heic", orientation=6)))

    assert len(engine.calls) == 2
    sizes = []
    dark_left = []
    for number in range(2):
        payload = engine.calls[number]["input"]
        assert isinstance(payload, bytes)
        with Image.open(BytesIO(payload)) as handed:
            sizes.append(handed.size)
            # The dark band was the left tenth of the canvas; turned by 270
            # degrees (orientation 6) it is the top tenth.
            dark_left.append(handed.getpixel((handed.size[0] // 2, 2)))
    assert sizes[0] == sizes[1] == (PAGE[1], PAGE[0])
    assert dark_left[0] == dark_left[1]


def test_the_estimate_of_a_heif_is_larger_than_of_a_jpeg(tmp_path: Path) -> None:
    with Image.open(_heic(tmp_path, "a.heic")) as heic, Image.open(_jpeg(tmp_path, "a.jpg")) as jpeg:
        assert heic.size == jpeg.size
        assert heic.mode == jpeg.mode == "RGB"
        assert image._estimated_bytes(heic) > image._estimated_bytes(jpeg)


def test_a_heic_over_the_free_address_space_is_too_large(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Between the two estimates: the JPEG fits, the HEIC does not. A HEIC has
    # no draft, so its decoded size is the size of the file and no other child
    # under the same cap reads it: a decision an admin can act on, not a death
    # (Pitfall 12).
    engine = _install_engine(monkeypatch)
    heic_path = _heic(tmp_path, "foto.heic")
    jpeg_path = _jpeg(tmp_path, "foto.jpg")
    with Image.open(heic_path) as heic, Image.open(jpeg_path) as jpeg:
        room = (image._estimated_bytes(heic) + image._estimated_bytes(jpeg)) // 2
    monkeypatch.setattr(image, "_address_space_room", lambda: room)

    heic_outcome = image.extract_image(str(heic_path))
    jpeg_outcome = image.extract_image(str(jpeg_path))

    assert (heic_outcome.state, heic_outcome.reason) == (State.SKIPPED, Reason.TOO_LARGE)
    assert jpeg_outcome.state is State.INDEXED
    assert len(engine.calls) == 1
