"""The seed picture of the upgrade proof, held against what it has to be.

``.github/fixtures/upgrade-seed-grey-extra.tif`` is one of the two files
"Store upgrade 2b" of ``.github/workflows/deploy-harp.yml`` sows on the 1.3.2
installation (plan 29-11). The proof only means something if the picture is
exactly of the class of issue #18 that 1.3.2 cannot read and 1.4.0 can: grey
with one extra channel declared as unspecified, which Pillow 12.3.0 in the
image of 1.3.2 has no entry for. 1.4.0 read it through the shim of plan 29-07;
since plan 36-17 this code runs on Pillow 13.0.0, which maps the class itself
(python-pillow PR #10140). A picture that the Pillow of 1.3.2 could open would
let 1.3.2 index it, the seed word would answer before the upgrade, and the
recheck would prove nothing. A picture this code could not open would stay
failed after the upgrade and turn the proof red for the wrong reason.
Both are asked here, on the committed bytes, instead of in a CI run that costs
an hour to find out.

The last statement is about where the bytes come from: the generator runs
again and has to write the committed file byte for byte, so the fixture is
never a file nobody can reproduce.
"""

from __future__ import annotations

import email
import hashlib
import importlib.util
import io
import shutil
import time
import zipfile
from email import policy
from email.message import EmailMessage
from pathlib import Path
from types import ModuleType

import pytest
from PIL import Image, TiffImagePlugin, UnidentifiedImageError

from findling.extract import archive, dispatch, image
from findling.extract.errors import Reason, State

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / ".github" / "fixtures" / "upgrade-seed-grey-extra.tif"
GENERATOR = REPO_ROOT / "scripts" / "ci" / "make_upgrade_seed_tiff.py"

# Tags of the TIFF specification the class is defined by.
_TAG_BITS_PER_SAMPLE = 258
_TAG_COMPRESSION = 259
_TAG_PHOTOMETRIC = 262
_TAG_SAMPLES_PER_PIXEL = 277
_TAG_EXTRA_SAMPLES = 338
_TAG_FILL_ORDER = 266
_TAG_SAMPLE_FORMAT = 339

# Every key of ``TiffImagePlugin.OPEN_INFO`` in Pillow 12.3.0, the Pillow of
# v1.3.2, for grey (photometric 0 or 1) with two channels. Read once on
# 2026-10-21 in plan 36-17 with ``uv run --no-project --with pillow==12.3.0
# python -c`` over ``sorted(OPEN_INFO)``; only the unassociated alpha (2).
PILLOW_12_3_0_GREY_TWO_CHANNEL_KEYS: dict[tuple[object, ...], tuple[str, str]] = {
    (b"II", 1, (1,), 1, (8, 8), (2,)): ("LA", "LA"),
    (b"MM", 1, (1,), 1, (8, 8), (2,)): ("LA", "LA"),
}


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


def test_the_pillow_of_1_3_2_has_no_entry_for_it(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1.3.2 runs with its own image and Pillow 12.3.0 in it (pin of the tag
    # v1.3.2), not with the Pillow of this code, which maps the class itself
    # since 13.0.0 (plan 36-17). So the statement is made against the table of
    # 12.3.0: its grey keys of two channels, written down here, and the key of
    # the seed missing among them. UnidentifiedImageError is what 1.3.2 books
    # as failed(corrupt), so the open over that table is asked as well.
    with Image.open(FIXTURE) as picture:
        assert isinstance(picture, TiffImagePlugin.TiffImageFile)
        tags = picture.tag_v2
        key = (
            b"MM",
            tags[_TAG_PHOTOMETRIC],
            tags.get(_TAG_SAMPLE_FORMAT, (1,) * tags[_TAG_SAMPLES_PER_PIXEL])[:1],
            tags.get(_TAG_FILL_ORDER, 1),
            tags[_TAG_BITS_PER_SAMPLE],
            tags[_TAG_EXTRA_SAMPLES],
        )
    assert key == (b"MM", 1, (1,), 1, (8, 8), (0,))
    assert key not in PILLOW_12_3_0_GREY_TWO_CHANNEL_KEYS

    table = {k: v for k, v in TiffImagePlugin.OPEN_INFO.items() if k[1] not in (0, 1) or len(k[4]) != 2}
    table.update(PILLOW_12_3_0_GREY_TWO_CHANNEL_KEYS)
    monkeypatch.setattr(TiffImagePlugin, "OPEN_INFO", table)
    with pytest.raises(UnidentifiedImageError):
        Image.open(FIXTURE)


def test_this_code_reads_it_and_it_turns_grey() -> None:
    # Pillow 13.0.0 opens the unspecified extra channel as grey and skips it
    # in the raw mode "LX" (python-pillow PR #10140), so the picture is "L".
    with Image.open(FIXTURE) as picture:
        assert picture.mode == "L"
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


# --- The seed of the new formats (plan 31-12, FMT-06) ------------------------
#
# Eight files the upgrade proof sows on the 1.4.2 installation, next to the two
# above: a mail with its word only in the HTML part, a ZIP file with its word in
# innen/notiz.txt, a Word 97 and an Excel 97 file, a HEIC photo with its word as
# pixels, a Word 97 file under a .docx name, a text file whose size in the file
# cache is made stale on purpose, and a small ZIP bomb without any word (depth 3
# alone since plan 36-08, D-36-17, answer O4 (a): no zero filler). What
# 1.4.2 makes of them is read out of the code of the tag (31-12-SUMMARY); what
# has to hold of the bytes is asked here, because a wrong seed would make the
# upgrade proof green or red for a reason that has nothing to do with 1.5.

FORMATS_DIR = REPO_ROOT / ".github" / "fixtures" / "upgrade-seed-formats"
FORMATS_GENERATOR = REPO_ROOT / "scripts" / "ci" / "make_upgrade_seed_formats.py"
LEGACY_DIR = REPO_ROOT / "backend" / "tests" / "fixtures" / "legacy"
CORPUS_DIR = REPO_ROOT / "testdata" / "corpus"

# The words of the plan, one per file, and the file that carries no word.
SEED_FORMAT_WORDS = {
    "seed-mail.eml": "mailquendel",
    "seed-archive.zip": "archivquendel",
    "seed-word.doc": "wortquendel",
    "seed-excel.xls": "zellquendel",
    "seed-photo.heic": "fotoquendel",
    "seed-ole-under-docx.docx": "hullequendel",
    "seed-stale-size.txt": "cachequendel",
}
SEED_BOMB = "seed-bomb.zip"

# The mimetype Nextcloud gives each name, the one the container is handed.
SEED_FORMAT_MIMES = {
    "seed-mail.eml": "message/rfc822",
    "seed-archive.zip": "application/zip",
    "seed-word.doc": "application/msword",
    "seed-excel.xls": "application/vnd.ms-excel",
    "seed-photo.heic": "image/heic",
    "seed-ole-under-docx.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "seed-stale-size.txt": "text/plain",
}

# Pinned, because their writers do not promise the same bytes twice: libheif
# with x265 for the photo, LibreOffice for the three legacy files.
SEED_FORMAT_PINS = {
    "seed-photo.heic": "a333c9cf42b320f02bf39308822a9e9d0f592e38421b1b54295c3c6cc2764b27",
    "seed-word.doc": "a353da53140613930e68eb7db478bc1e531defa0610e98b916d54a40c9834845",
    "seed-excel.xls": "77c04f4d82efe8ca60ea9ec442f3b59ccc5bd872d1663bcb5ea0edabb65c7b48",
    "seed-ole-under-docx.docx": "5fdf780437074dfee01ca1d7aebdb1bdb4b7c9e4be34a67a02950e8523727589",
}

# The copies and their originals among the unit fixtures of 31-05, 31-06 and
# this plan.
SEED_FORMAT_COPIES = {
    "seed-word.doc": "word97-latin.doc",
    "seed-excel.xls": "biff8-values.xls",
    "seed-ole-under-docx.docx": "word97-ole-seed.doc",
}

# Written by the generator byte for byte on every run.
SEED_FORMAT_DETERMINISTIC = ("seed-mail.eml", "seed-archive.zip", SEED_BOMB, "seed-stale-size.txt")

_OLE_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")
_SEED_MAX_BYTES = 256 * 1024
_BOMB_MAX_BYTES = 16 * 1024
_BOMB_SECONDS = 5.0

needs_engine = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="no tesseract on this machine; the container image carries it",
)


def _formats_generator() -> ModuleType:
    """The generator of the new formats as a module, loaded from its path."""
    spec = importlib.util.spec_from_file_location("make_upgrade_seed_formats", FORMATS_GENERATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed(name: str) -> Path:
    return FORMATS_DIR / name


def _copied(name: str, tmp_path: Path) -> Path:
    # The ZIP reader puts its scratch files next to the file it reads, so every
    # extraction runs on a copy and never next to the committed fixture.
    target = tmp_path / name
    shutil.copyfile(_seed(name), target)
    return target


def _all_texts(data: bytes) -> str:
    """The bytes read as UTF-8, UTF-16 and Latin-1, which covers every writer of the seed."""
    return data.decode("utf-8", "ignore") + data.decode("utf-16-le", "ignore") + data.decode("latin-1")


def _members_deep(data: bytes) -> list[bytes]:
    """Every member of a ZIP file, and of every ZIP file inside it, decompressed."""
    found: list[bytes] = []
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        for info in package.infolist():
            content = package.read(info)
            found.append(content)
            if info.filename.endswith(".zip"):
                found.extend(_members_deep(content))
    return found


def test_the_generator_names_the_words_of_the_plan() -> None:
    module = _formats_generator()
    assert module.SEED_WORDS == SEED_FORMAT_WORDS
    assert module.BOMB == SEED_BOMB


def test_the_eight_seed_files_are_there_and_small() -> None:
    for name in [*SEED_FORMAT_WORDS, SEED_BOMB]:
        path = _seed(name)
        assert path.is_file(), name
        assert path.stat().st_size < _SEED_MAX_BYTES, name
    assert _seed(SEED_BOMB).stat().st_size < _BOMB_MAX_BYTES
    assert sorted(path.name for path in FORMATS_DIR.iterdir()) == sorted([*SEED_FORMAT_WORDS, SEED_BOMB])


def test_the_generator_writes_the_deterministic_seed_files_again() -> None:
    rendered = _formats_generator().render_deterministic()
    assert sorted(rendered) == sorted(SEED_FORMAT_DETERMINISTIC)
    for name, data in rendered.items():
        assert data == _seed(name).read_bytes(), name


def test_the_pinned_seed_files_carry_their_digest() -> None:
    for name, digest in SEED_FORMAT_PINS.items():
        assert hashlib.sha256(_seed(name).read_bytes()).hexdigest() == digest, name


def test_the_legacy_seed_files_are_copies_of_the_unit_fixtures() -> None:
    for name, original in SEED_FORMAT_COPIES.items():
        assert _seed(name).read_bytes() == (LEGACY_DIR / original).read_bytes(), name
    # An old compound file under the new name, which is the whole point of it.
    assert _seed("seed-ole-under-docx.docx").read_bytes()[:8] == _OLE_SIGNATURE


def test_the_mail_carries_its_word_only_in_an_html_part() -> None:
    message = email.message_from_bytes(_seed("seed-mail.eml").read_bytes(), policy=policy.default)
    assert isinstance(message, EmailMessage)
    parts = list(message.walk())
    types = [part.get_content_type() for part in parts]
    assert "text/plain" not in types
    assert "text/html" in types
    word = SEED_FORMAT_WORDS["seed-mail.eml"]
    for header in ("Subject", "From", "To"):
        assert word not in str(message[header])
    html = [part for part in parts if part.get_content_type() == "text/html"]
    assert len(html) == 1
    body = html[0]
    assert isinstance(body, EmailMessage)
    assert word in str(body.get_content())


def test_the_archive_carries_its_word_in_the_inner_note() -> None:
    with zipfile.ZipFile(_seed("seed-archive.zip")) as package:
        assert package.namelist() == ["innen/notiz.txt"]
        note = package.read("innen/notiz.txt").decode("utf-8")
    assert SEED_FORMAT_WORDS["seed-archive.zip"] in note


def test_the_stale_size_file_carries_its_word() -> None:
    text = _seed("seed-stale-size.txt").read_text(encoding="utf-8")
    assert SEED_FORMAT_WORDS["seed-stale-size.txt"] in text


def test_the_bomb_carries_no_seed_word() -> None:
    data = _seed(SEED_BOMB).read_bytes()
    every_word = [*SEED_FORMAT_WORDS.values(), _generator().SEED_WORD]
    for content in [data, *_members_deep(data)]:
        text = _all_texts(content)
        for word in every_word:
            assert word not in text, word


def _over_the_ratio(info: zipfile.ZipInfo) -> bool:
    return info.file_size >= archive.ARCHIVE_RATIO_MIN_BYTES and info.file_size > archive.ARCHIVE_MAX_RATIO * max(
        info.compress_size, 1
    )


def test_the_bomb_is_three_levels_deep_without_a_member_over_the_ratio() -> None:
    # The one limit it crosses, read off the bytes rather than believed of the
    # generator: a ZIP in a ZIP in a ZIP that ends in a text file, exactly one
    # nested ZIP per level and no member over the ratio of 31-08 on any level
    # (D-36-17, plan 36-08, answer O4 (a): the zero member is gone).
    with zipfile.ZipFile(_seed(SEED_BOMB)) as outer:
        (middle_name,) = outer.namelist()
        assert middle_name.endswith(".zip")
        assert not any(_over_the_ratio(info) for info in outer.infolist())
        middle = outer.read(middle_name)
    with zipfile.ZipFile(io.BytesIO(middle)) as level_two:
        (inner_name,) = level_two.namelist()
        assert inner_name.endswith(".zip")
        assert not any(_over_the_ratio(info) for info in level_two.infolist())
        inner = level_two.read(inner_name)
    with zipfile.ZipFile(io.BytesIO(inner)) as level_three:
        (note,) = level_three.namelist()
        assert note.endswith(".txt")
        assert not any(_over_the_ratio(info) for info in level_three.infolist())
    assert archive.ARCHIVE_MAX_DEPTH == 2


def test_the_bomb_is_an_archive_limit_for_this_code(tmp_path: Path) -> None:
    path = _copied(SEED_BOMB, tmp_path)
    started = time.monotonic()
    outcome = archive.extract_zip(str(path))
    assert time.monotonic() - started < _BOMB_SECONDS
    assert outcome.state is State.SKIPPED
    assert outcome.reason is Reason.ARCHIVE_LIMIT


def test_the_depth_alone_judges_the_bomb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The depth alone, and with it lifted the file is an ordinary archive
    # again: the verdict above comes from this limit and from nothing else, so
    # a change to it turns this gate red. The ratio part of the gate is gone
    # with the zero member: the seed has no member over the ratio since
    # D-36-17 (plan 36-08, answer O4 (a)).
    path = _copied(SEED_BOMB, tmp_path)
    assert archive.extract_zip(str(path)).reason is Reason.ARCHIVE_LIMIT
    monkeypatch.setattr(archive, "ARCHIVE_MAX_DEPTH", 10)
    assert archive.extract_zip(str(path)).state is State.INDEXED
    monkeypatch.setattr(archive, "ARCHIVE_MAX_DEPTH", 2)
    assert archive.extract_zip(str(path)).reason is Reason.ARCHIVE_LIMIT


@pytest.mark.parametrize(
    "name",
    [
        "seed-mail.eml",
        "seed-archive.zip",
        "seed-word.doc",
        "seed-excel.xls",
        "seed-ole-under-docx.docx",
        "seed-stale-size.txt",
    ],
)
def test_the_extractors_of_this_code_read_the_seed_word(name: str, tmp_path: Path) -> None:
    path = _copied(name, tmp_path)
    outcome = dispatch.extract(str(path), SEED_FORMAT_MIMES[name], path.stat().st_size)
    assert outcome.state is State.INDEXED, outcome
    assert SEED_FORMAT_WORDS[name] in (outcome.text or "")


def test_the_photo_is_a_heic_of_a_readable_shape() -> None:
    with Image.open(_seed("seed-photo.heic")) as picture:
        assert picture.format == "HEIF"
        width, height = picture.size
    assert max(width, height) >= image._MIN_LONG_EDGE_PIXELS
    assert max(width, height) / min(width, height) <= image._MAX_ASPECT_RATIO
    module = _formats_generator()
    assert module.PHOTO_LINES.count(SEED_FORMAT_WORDS["seed-photo.heic"]) >= 2
    assert len(" ".join(module.PHOTO_LINES)) > image._MIN_OCR_CHARS


@needs_engine
def test_the_engine_reads_the_word_of_the_photo(tmp_path: Path) -> None:
    path = _copied("seed-photo.heic", tmp_path)
    outcome = dispatch.extract(str(path), "image/heic", path.stat().st_size)
    assert outcome.state is State.INDEXED, outcome
    assert SEED_FORMAT_WORDS["seed-photo.heic"] in (outcome.text or "").lower()


def test_each_seed_word_stands_in_exactly_one_seed_file(tmp_path: Path) -> None:
    # The text every file gives this code, the photo by the lines it was drawn
    # with (its word is pixels, not bytes), the bomb by every member it holds.
    texts: dict[str, str] = {}
    for name, mime in SEED_FORMAT_MIMES.items():
        if name == "seed-photo.heic":
            texts[name] = " ".join(_formats_generator().PHOTO_LINES)
            continue
        path = _copied(name, tmp_path)
        texts[name] = dispatch.extract(str(path), mime, path.stat().st_size).text or ""
    bomb = _seed(SEED_BOMB).read_bytes()
    texts[SEED_BOMB] = "".join(_all_texts(content) for content in [bomb, *_members_deep(bomb)])
    for word in SEED_FORMAT_WORDS.values():
        carriers = [name for name, text in texts.items() if word in text]
        assert len(carriers) == 1, (word, carriers)


def test_no_seed_word_stands_in_the_reference_corpus() -> None:
    # The corpus "Store upgrade 2" copies into the account, read as bytes in the
    # encodings its files use. A hit there would answer a seed word before the
    # seed was sown.
    for path in sorted(CORPUS_DIR.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        text = _all_texts(path.read_bytes()).lower()
        for word in SEED_FORMAT_WORDS.values():
            assert word not in text, (word, path.name)
