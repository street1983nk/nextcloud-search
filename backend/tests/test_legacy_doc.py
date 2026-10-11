"""FMT-03: Word 97 to 2003 documents (.doc), read without LibreOffice in the image.

Three kinds of input. The files under fixtures/legacy were written by
LibreOffice 26.2 from own content (scripts/dev/make_legacy_fixtures.py, origin in
fixtures/legacy/README.md); their digests are pinned below. LibreOffice stores
every piece as UTF-16 and keeps both small streams in the mini stream, so the
compressed 8 bit pieces and every broken structure of the Word side are built
here from the specification ([MS-DOC] 2.5.1 Fib, 2.5.2 FibBase, 2.9.38 Clx,
2.8.35 PlcPcd, 2.9.73 FcCompressed) on top of conftest.build_cfb, and the tests
that break the MiniFAT patch a LibreOffice file.

Every test of a broken sector chain has a limit of 5 s and a control next to it:
the same file without the defect is read, so the verdict belongs to the defect
and not to the builder.
"""

from __future__ import annotations

import hashlib
import io
import struct
import time
import tracemalloc
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import docx
import olefile
import pytest

from conftest import CFB_END_OF_CHAIN, build_cfb, cfb_with_difat
from findling.config import settings
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.legacy_doc import decode_compressed, extract_doc, extract_msword

FIXTURES = Path(__file__).parent / "fixtures" / "legacy"

# SHA-256 of the committed files. LibreOffice does not write the same bytes twice,
# so a new run of the fixture tool means new digests here, on purpose.
FIXTURE_DIGESTS = {
    "word97-latin.doc": "a353da53140613930e68eb7db478bc1e531defa0610e98b916d54a40c9834845",
    "word97-unicode.doc": "0dc7e408d9a46d74cd674ea28629dae2164de624ae665d27677aef3c2eb6faee",
    "word97-table-field.doc": "d662ad00e1997f8ef7944d5e449807a6bcfabbbda421971e6f3c6be728b3185c",
}

TIME_LIMIT_S = 5.0

# [MS-DOC] 2.5.2 FibBase and 2.9.73 FcCompressed.
_W_IDENT = 0xA5EC
_NFIB_WORD97 = 0x00C1
_F_ENCRYPTED = 0x0100
_F_WHICH_TBL_STM = 0x0200
_F_OBFUSCATED = 0x8000
_FC_COMPRESSED = 0x40000000
_TEXT_AT = 0x800


def word_streams(
    pieces: Sequence[str | bytes],
    *,
    w_ident: int = _W_IDENT,
    n_fib: int = _NFIB_WORD97,
    flags: int = _F_WHICH_TBL_STM,
    table_name: str | None = None,
    prcs: Sequence[bytes] = (),
    clx_at: int = 0,
    fc_clx: int | None = None,
    lcb_clx: int | None = None,
    pcdt_lcb: int | None = None,
    cps: Sequence[int] | None = None,
    fcs: dict[int, int] | None = None,
    reverse: bool = False,
    clx: bytes | None = None,
) -> dict[str, bytes]:
    """A WordDocument and a Table stream written from [MS-DOC], one piece per item.

    A str is a Unicode piece (UTF-16LE), bytes are a compressed piece (8 bit,
    fCompressed set). The text of the pieces lies in the WordDocument from 0x800
    on, in the order given or, with ``reverse``, the other way round, which is
    what a fast save leaves behind: the pieces stay in CP order, their fc do not.
    Every other switch breaks exactly one field.
    """
    encoded = [piece if isinstance(piece, bytes) else piece.encode("utf-16-le") for piece in pieces]
    lengths = [len(piece) for piece in pieces]
    order = list(range(len(pieces)))[::-1] if reverse else list(range(len(pieces)))
    offsets: dict[int, int] = {}
    body = bytearray()
    for index in order:
        offsets[index] = _TEXT_AT + len(body)
        body += encoded[index]
    raw_fcs = [
        offsets[index] * 2 | _FC_COMPRESSED if isinstance(piece, bytes) else offsets[index]
        for index, piece in enumerate(pieces)
    ]
    for index, value in (fcs or {}).items():
        raw_fcs[index] = value
    positions = list(cps) if cps is not None else [sum(lengths[:index]) for index in range(len(pieces) + 1)]

    plc = struct.pack(f"<{len(positions)}I", *positions)
    plc += b"".join(struct.pack("<HIH", 0, fc, 0) for fc in raw_fcs)
    if clx is None:
        declared = len(plc) if pcdt_lcb is None else pcdt_lcb
        clx = b"".join(prcs) + struct.pack("<BI", 0x02, declared) + plc
    table = bytes(clx_at) + clx

    fib_base = struct.pack("<7HI2B2H2I", w_ident, n_fib, 0, 0x0407, 0, flags, 0x00BF, 0, 0, 0, 0, 0, 0, 0)
    # csw 0x000E, cslw 0x0016, cbRgFcLcb 0x005D: the counts of 2.5.1 for nFib 0x00C1.
    rg_lw = [0] * 0x0016
    rg_lw[3] = positions[-1]  # ccpText
    blob = [0] * (2 * 0x005D)
    blob[66] = clx_at if fc_clx is None else fc_clx  # fcClx, pair 33 of FibRgFcLcb97
    blob[67] = len(clx) if lcb_clx is None else lcb_clx  # lcbClx
    fib = (
        fib_base
        + struct.pack("<H", 0x000E)
        + bytes(2 * 0x000E)
        + struct.pack("<H22I", 0x0016, *rg_lw)
        + struct.pack("<H186I", 0x005D, *blob)
        + struct.pack("<H", 0)
    )
    word = fib.ljust(_TEXT_AT, b"\0") + bytes(body)
    name = table_name or ("1Table" if flags & _F_WHICH_TBL_STM else "0Table")
    return {"WordDocument": word, name: table}


def _write(tmp_path: Path, payload: bytes, name: str = "brief.doc") -> str:
    path = tmp_path / name
    path.write_bytes(payload)
    return str(path)


def _doc(tmp_path: Path, pieces: Sequence[str | bytes], **word: object) -> str:
    return _write(tmp_path, build_cfb([], streams=word_streams(pieces, **word)))  # pyright: ignore[reportArgumentType]


def _timed(path: str) -> ExtractionOutcome:
    started = time.perf_counter()
    outcome = extract_doc(path)
    assert time.perf_counter() - started < TIME_LIMIT_S
    return outcome


def _corrupt(outcome: ExtractionOutcome) -> bool:
    return outcome.state is State.FAILED and outcome.reason is Reason.CORRUPT


def _fixture(name: str) -> str:
    return str(FIXTURES / name)


# --- the LibreOffice files ---------------------------------------------------


@pytest.mark.parametrize(("name", "digest"), sorted(FIXTURE_DIGESTS.items()))
def test_every_fixture_is_the_committed_file(name: str, digest: str) -> None:
    assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == digest


def test_the_latin_document_keeps_umlauts_quotes_and_the_euro_sign() -> None:
    outcome = extract_doc(_fixture("word97-latin.doc"))

    assert outcome.state is State.INDEXED
    assert "wortquendel" in outcome.text
    assert "Gr\u00fc\u00dfe" in outcome.text
    assert "\u201eZitat\u201c und \u2018einfach\u2019" in outcome.text
    assert "42 \u20ac" in outcome.text
    assert "\u00e4\u00f6\u00fc \u00c4\u00d6\u00dc \u00df" in outcome.text


def test_paragraph_marks_become_line_breaks() -> None:
    lines = extract_doc(_fixture("word97-latin.doc")).text.splitlines()

    assert lines[0] == "Das wortquendel steht in einem Brief mit herzlichen Gr\u00fc\u00dfen."
    assert len(lines) == 3


def test_a_soft_hyphen_goes_and_a_non_breaking_hyphen_stays_a_hyphen() -> None:
    # Measured: LibreOffice writes U+00AD as 0x1F and U+2011 as 0x1E.
    text = extract_doc(_fixture("word97-latin.doc")).text

    assert "Silbentrennung und Bindestrich-fest." in text


def test_the_unicode_document_keeps_czech_and_greek() -> None:
    text = extract_doc(_fixture("word97-unicode.doc")).text

    assert "glyphquendel" in text
    assert "P\u0159\u00edli\u0161 \u017elu\u0165ou\u010dk\u00fd k\u016f\u0148" in text
    assert "\u039a\u03b1\u03bb\u03b7\u03bc\u03ad\u03c1\u03b1 \u03ba\u03cc\u03c3\u03bc\u03b5" in text


def test_table_cells_are_separated_by_tabs() -> None:
    text = extract_doc(_fixture("word97-table-field.doc")).text

    assert "zellquendel" in text
    assert "Apfel\tBirne\t" in text
    assert "Kirsche\tPflaume\t" in text


def test_field_codes_go_and_field_results_stay() -> None:
    text = extract_doc(_fixture("word97-table-field.doc")).text

    assert "Seite 1 von hier." in text
    assert "Stand 11.10.26 ist fest." in text
    assert "PAGE" not in text
    assert "DATE" not in text
    assert "dd.MM" not in text


def test_the_msword_entry_reads_a_real_doc_like_the_doc_reader() -> None:
    path = _fixture("word97-unicode.doc")

    assert extract_msword(path) == extract_doc(path)


# --- pieces, compressed text and the special table -----------------------------


def test_a_compressed_piece_uses_the_special_table() -> None:
    assert decode_compressed(b"Gr\xfc\xdfe \x84Zitat\x93 \x96 Ende") == "Gr\u00fc\u00dfe \u201eZitat\u201c \u2013 Ende"


def test_byte_0x80_stays_u0080_and_is_not_the_euro_sign() -> None:
    assert decode_compressed(b"\x80\x82") == "\u0080\u201a"


# The table of [MS-DOC] 2.9.73, copied from the specification page and not from
# the module, so a wrong entry there is a red test here.
SPECIAL_TABLE = {
    0x82: 0x201A, 0x83: 0x0192, 0x84: 0x201E, 0x85: 0x2026, 0x86: 0x2020, 0x87: 0x2021,
    0x88: 0x02C6, 0x89: 0x2030, 0x8A: 0x0160, 0x8B: 0x2039, 0x8C: 0x0152, 0x91: 0x2018,
    0x92: 0x2019, 0x93: 0x201C, 0x94: 0x201D, 0x95: 0x2022, 0x96: 0x2013, 0x97: 0x2014,
    0x98: 0x02DC, 0x99: 0x2122, 0x9A: 0x0161, 0x9B: 0x203A, 0x9C: 0x0153, 0x9F: 0x0178,
}  # fmt: skip


def test_every_byte_of_a_compressed_piece_maps_as_the_specification_says() -> None:
    decoded = decode_compressed(bytes(range(256)))

    assert [ord(char) for char in decoded] == [SPECIAL_TABLE.get(byte, byte) for byte in range(256)]


def test_a_compressed_document_is_read(tmp_path: Path) -> None:
    outcome = extract_doc(_doc(tmp_path, [b"Das kompressquendel mit \x84Gr\xfc\xdfen\x93.\r"]))

    assert outcome == ExtractionOutcome.indexed("Das kompressquendel mit \u201eGr\u00fc\u00dfen\u201c.\n")


def test_pieces_are_read_in_cp_order_even_when_their_text_is_stored_backwards(tmp_path: Path) -> None:
    path = _doc(tmp_path, [b"erstes ", "zweites \u0159 ", b"drittes"], reverse=True)

    assert extract_doc(path).text == "erstes zweites \u0159 drittes"


def test_property_blocks_before_the_piece_table_are_skipped(tmp_path: Path) -> None:
    prcs = [struct.pack("<Bh", 0x01, 3) + b"\x01\x02\x03", struct.pack("<Bh", 0x01, 0)]

    assert extract_doc(_doc(tmp_path, ["prcquendel"], prcs=prcs)).text == "prcquendel"


def test_the_table_stream_follows_fwhichtblstm(tmp_path: Path) -> None:
    assert extract_doc(_doc(tmp_path, ["nulltabelle"], flags=0)).text == "nulltabelle"


def test_a_field_without_separator_is_dropped_whole(tmp_path: Path) -> None:
    assert extract_doc(_doc(tmp_path, ["vor\x13 TC eintrag \x15nach"])).text == "vornach"


def test_a_field_inside_field_instructions_goes_with_them(tmp_path: Path) -> None:
    text = "a\x13 IF \x13 PAGE \x141\x15 = 1 \x14ergebnis\x15b"

    assert extract_doc(_doc(tmp_path, [text])).text == "aergebnisb"


def test_a_field_inside_a_field_result_keeps_its_own_result(tmp_path: Path) -> None:
    text = "a\x13 HYPERLINK x \x14link \x13 PAGE \x147\x15 ende\x15b"

    assert extract_doc(_doc(tmp_path, [text])).text == "alink 7 endeb"


def test_field_marks_across_a_piece_boundary_still_pair(tmp_path: Path) -> None:
    assert extract_doc(_doc(tmp_path, [b"a\x13 PAGE ", "\x143\x15b"])).text == "a3b"


def test_stray_field_marks_are_dropped(tmp_path: Path) -> None:
    assert extract_doc(_doc(tmp_path, ["a\x15b\x14c"])).text == "abc"


def test_object_anchors_go_and_breaks_become_line_breaks(tmp_path: Path) -> None:
    text = "bild\x01 objekt\x08 fussnote\x02 kommentar\x05 zeile\x0bseite\x0czelle\x07ende"

    assert extract_doc(_doc(tmp_path, [text])).text == "bild objekt fussnote kommentar zeile\nseite\nzelle\tende"


# --- named verdicts on the Word side ------------------------------------------


def test_an_encrypted_document_is_skipped_as_encrypted(tmp_path: Path) -> None:
    path = _doc(tmp_path, ["geheim"], flags=_F_WHICH_TBL_STM | _F_ENCRYPTED)

    assert extract_doc(path) == ExtractionOutcome.skipped(Reason.ENCRYPTED)


def test_an_obfuscated_document_is_skipped_as_encrypted(tmp_path: Path) -> None:
    path = _doc(tmp_path, ["geheim"], flags=_F_WHICH_TBL_STM | _F_ENCRYPTED | _F_OBFUSCATED)

    assert extract_doc(path) == ExtractionOutcome.skipped(Reason.ENCRYPTED)


def test_fobfuscated_without_fencrypted_is_ignored_as_the_specification_says(tmp_path: Path) -> None:
    path = _doc(tmp_path, ["offen"], flags=_F_WHICH_TBL_STM | _F_OBFUSCATED)

    assert extract_doc(path).text == "offen"


@pytest.mark.parametrize("n_fib", [0x0065, 0x0068, 0x00C0])
def test_word_6_and_95_are_an_unsupported_variant(tmp_path: Path, n_fib: int) -> None:
    path = _doc(tmp_path, ["alt"], n_fib=n_fib)

    assert extract_doc(path) == ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def test_a_compound_file_without_worddocument_is_an_unsupported_variant(tmp_path: Path) -> None:
    path = _write(tmp_path, build_cfb([], streams={"Workbook": b"keine Textdatei"}))

    assert extract_doc(path) == ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def test_a_wrong_wident_is_corrupt(tmp_path: Path) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["x"], w_ident=0xA5DB)))


def test_a_missing_table_stream_is_corrupt(tmp_path: Path) -> None:
    path = _doc(tmp_path, ["x"], table_name="0Table")

    assert _corrupt(extract_doc(path))


@pytest.mark.parametrize("size", [20, 0x01A2 + 4])
def test_a_worddocument_shorter_than_the_fib_is_corrupt(tmp_path: Path, size: int) -> None:
    # build_cfb pads every stream to 4096 bytes, so the short stream is the
    # WordDocument of a LibreOffice file (it lives in the mini stream) with its
    # declared size cut down in the directory entry.
    data = bytearray((FIXTURES / "word97-latin.doc").read_bytes())
    entry = data.index("WordDocument".encode("utf-16-le") + b"\0\0")
    struct.pack_into("<I", data, entry + 0x78, size)

    assert _corrupt(extract_doc(_write(tmp_path, bytes(data))))


@pytest.mark.parametrize(
    ("at", "value"), [(0x20, 0x000D), (0x3E, 0x0015), (0x98, 0x0021)], ids=["csw", "cslw", "cbRgFcLcb"]
)
def test_a_fib_whose_counts_break_the_specification_is_corrupt(tmp_path: Path, at: int, value: int) -> None:
    # Only the count changes, the layout behind it stays, so the reader would
    # find the Clx where it always is if it did not check the count.
    streams = word_streams(["zaehlquendel"])
    word = bytearray(streams["WordDocument"])
    struct.pack_into("<H", word, at, value)
    streams["WordDocument"] = bytes(word)

    assert _corrupt(extract_doc(_write(tmp_path, build_cfb([], streams=streams))))


def test_the_clx_offsets_of_the_fib_are_those_of_fibrgfclcb97(tmp_path: Path) -> None:
    # Assumption A1 of 31-RESEARCH: fcClx at 0x01A2, lcbClx at 0x01A6 of the
    # WordDocument stream. The builder above writes the Fib field by field, so a
    # reader at another offset finds a zero length and calls the file corrupt.
    streams = word_streams(["offset"])

    assert struct.unpack_from("<II", streams["WordDocument"], 0x01A2) == (0, len(streams["1Table"]))
    assert extract_doc(_doc(tmp_path, ["offset"])).text == "offset"


def test_the_clx_offsets_hold_in_a_file_that_libreoffice_wrote() -> None:
    # The same assumption against a writer that is not this test: at 0x01A2
    # stands an offset into 1Table where a Pcdt starts (0x02), at 0x01A6 its
    # length, which ends inside the stream.
    with olefile.OleFileIO(_fixture("word97-latin.doc")) as ole:
        word = ole.openstream("WordDocument").read()
        table = ole.openstream("1Table").read()
    fc_clx, lcb_clx = struct.unpack_from("<II", word, 0x01A2)

    assert table[fc_clx] == 0x02
    assert 0 < fc_clx + lcb_clx <= len(table)


def test_a_clx_past_the_table_stream_is_corrupt(tmp_path: Path) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["x"], fc_clx=1 << 20)))


def test_a_huge_lcbclx_is_corrupt_without_reading_it(tmp_path: Path) -> None:
    path = _doc(tmp_path, ["x"], lcb_clx=0xFFFFFFFF)

    tracemalloc.start()
    try:
        outcome = _timed(path)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert _corrupt(outcome)
    assert peak < 4 * 1024 * 1024


def test_a_zero_lcbclx_is_corrupt(tmp_path: Path) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["x"], lcb_clx=0)))


@pytest.mark.parametrize(
    "clx",
    [
        b"\x03\x00\x00\x00\x00",  # neither Prc nor Pcdt
        struct.pack("<Bh", 0x01, -4) + bytes(8),  # negative cbGrpprl
        struct.pack("<Bh", 0x01, 0x3FA3) + bytes(0x3FA3),  # cbGrpprl over 0x3FA2
        struct.pack("<Bh", 0x01, 40) + bytes(4),  # Prc running past the Clx
        struct.pack("<BI", 0x02, 64) + bytes(16),  # Pcdt longer than the Clx
        struct.pack("<BI", 0x02, 20) + bytes(20),  # not 4 + 12 n bytes
        struct.pack("<BI", 0x02, 4) + bytes(4),  # no piece at all
        b"\x01",  # Prc cut after its type byte
    ],
    ids=["clxt", "negative", "over-0x3fa2", "prc-past-end", "pcdt-past-end", "not-4-12n", "no-piece", "cut-prc"],
)
def test_a_broken_clx_is_corrupt(tmp_path: Path, clx: bytes) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["x"], clx=clx)))


def test_cps_that_do_not_ascend_are_corrupt(tmp_path: Path) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["ab", "cd"], cps=[0, 2, 2])))


@pytest.mark.parametrize("fc", [0x00100000, 0x00100000 | _FC_COMPRESSED, 0x3FFFFFFF])
def test_a_piece_past_the_end_of_worddocument_is_corrupt(tmp_path: Path, fc: int) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["text"], fcs={0: fc})))


def test_a_piece_longer_than_worddocument_is_corrupt(tmp_path: Path) -> None:
    assert _corrupt(extract_doc(_doc(tmp_path, ["text"], cps=[0, 0x7FFFFFFF])))


def test_reading_stops_at_the_character_cap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_MAX_TEXT_CHARS", "1024")
    settings.cache_clear()
    path = _doc(tmp_path, [b"x" * 100] * 30)

    outcome = extract_doc(path)

    assert outcome.truncated
    assert outcome.text == "x" * 1024


def test_a_cut_after_removed_field_codes_is_still_marked_truncated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FINDLING_MAX_TEXT_CHARS", "1024")
    settings.cache_clear()
    path = _doc(tmp_path, [b"\x13" + b" CODE" * 300 + b"\x14kurz\x15", b"rest" * 300])

    outcome = extract_doc(path)

    assert outcome.truncated
    assert outcome.text.startswith("kurzrest")


def test_many_pieces_over_one_long_text_stop_at_the_cap_in_time(tmp_path: Path) -> None:
    # 4000 pieces that each name the same 100 000 characters would be 400
    # million characters; the reader takes the cap and stops.
    fc = _TEXT_AT * 2 | _FC_COMPRESSED
    positions = [100_000 * index for index in range(4001)]
    plc = struct.pack(f"<{len(positions)}I", *positions) + struct.pack("<HIH", 0, fc, 0) * 4000
    streams = word_streams([b"y" * 100_000], clx=struct.pack("<BI", 0x02, len(plc)) + plc)
    path = _write(tmp_path, build_cfb([], streams=streams))

    outcome = _timed(path)

    assert outcome.truncated
    assert outcome.text_chars == settings().max_text_chars


# --- sector chains of the compound file ----------------------------------------


# olefile's chain tables are not in its typeshed stub, so the tests read them
# untyped, like the module does.


def _start_of(payload: bytes, name: str) -> int:
    with olefile.OleFileIO(io.BytesIO(payload)) as ole:
        root: Any = ole.root
        return root.kids_dict[name.lower()].isectStart


def _word_payload(**cfb: object) -> bytes:
    streams = word_streams(["kettenquendel " * 400])
    return build_cfb([], streams=streams, **cfb)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("stream", ["WordDocument", "1Table"])
def test_a_fat_cycle_is_corrupt_in_time(tmp_path: Path, stream: str) -> None:
    start = _start_of(_word_payload(), stream)

    cycled = _timed(_write(tmp_path, _word_payload(fat={start + 3: start + 1}), "kreis.doc"))
    control = _timed(_write(tmp_path, _word_payload(), "heil.doc"))

    assert _corrupt(cycled)
    assert "kettenquendel" in control.text


def test_a_fat_chain_past_the_end_of_the_file_is_corrupt_in_time(tmp_path: Path) -> None:
    start = _start_of(_word_payload(), "WordDocument")

    assert _corrupt(_timed(_write(tmp_path, _word_payload(fat={start + 2: 50_000}))))


def test_a_fat_chain_that_ends_early_is_corrupt_in_time(tmp_path: Path) -> None:
    start = _start_of(_word_payload(), "WordDocument")

    assert _corrupt(_timed(_write(tmp_path, _word_payload(fat={start + 2: CFB_END_OF_CHAIN}))))


def test_a_difat_cycle_is_corrupt_in_time(tmp_path: Path) -> None:
    # 110 FAT sectors need a file of about 7 MB before a DIFAT sector is due at all.
    payload = _word_payload()

    cycled = _timed(_write(tmp_path, cfb_with_difat(payload, sectors=13_960, fat_count=110, last_next=None), "a.doc"))
    control = _timed(
        _write(tmp_path, cfb_with_difat(payload, sectors=13_960, fat_count=110, last_next=CFB_END_OF_CHAIN), "b.doc")
    )

    assert _corrupt(cycled)
    assert "kettenquendel" in control.text


def test_a_fat_declared_larger_than_the_file_is_corrupt_in_time(tmp_path: Path) -> None:
    # Measured on olefile 0.47: 20 000 declared FAT sectors in a file of 180 kB,
    # each pointing at sector 0, cost 29 s before olefile reports anything, and
    # the cost grows with the square of the count.
    payload = cfb_with_difat(_word_payload(), sectors=200, fat_count=20_000, last_next=CFB_END_OF_CHAIN)
    grown = bytearray(payload)
    for difat in range(200, len(grown) // 512 - 1):
        struct.pack_into("<127I", grown, (difat + 1) * 512, *([0] * 127))

    assert _corrupt(_timed(_write(tmp_path, bytes(grown))))


def test_a_directory_tree_too_deep_for_olefile_is_corrupt_in_time(tmp_path: Path) -> None:
    payload = build_cfb([f"S{index}" for index in range(3000)], streams=word_streams(["tief"]))

    outcome = _timed(_write(tmp_path, payload))

    assert _corrupt(outcome)
    assert outcome.detail == "builtins.RecursionError"


def _mini_chain(path: str, name: str) -> tuple[int, list[int]]:
    """File offset of the MiniFAT and the mini sector chain of stream ``name``."""
    with olefile.OleFileIO(path) as opened:
        ole: Any = opened
        entry = ole.root.kids_dict[name.lower()]
        assert entry.is_minifat
        ole.openstream(name).read()
        assert ole.num_mini_fat_sectors == 1
        chain = [entry.isectStart]
        for _ in range(-(-entry.size // 64) - 1):
            chain.append(ole.minifat[chain[-1]])
        return (ole.first_mini_fat_sector + 1) * ole.sectorsize, chain


def _patched(tmp_path: Path, offset: int, value: int) -> str:
    data = bytearray((FIXTURES / "word97-latin.doc").read_bytes())
    struct.pack_into("<I", data, offset, value)
    return _write(tmp_path, bytes(data), "patched.doc")


# The cycle sits behind everything the reader parses (the Fib and the Clx), in
# the text of WordDocument and in a part of 1Table that is never read, so
# without the walk over the chain the file would come out as indexed text.
@pytest.mark.parametrize(("stream", "at", "back"), [("WordDocument", 50, 40), ("1Table", 20, 15)])
def test_a_minifat_cycle_is_corrupt_in_time(tmp_path: Path, stream: str, at: int, back: int) -> None:
    minifat_at, chain = _mini_chain(_fixture("word97-latin.doc"), stream)
    assert len(chain) > at

    outcome = _timed(_patched(tmp_path, minifat_at + 4 * chain[at], chain[back]))

    assert _corrupt(outcome)
    assert "wortquendel" in _timed(_fixture("word97-latin.doc")).text


def test_a_minifat_chain_past_the_mini_stream_is_corrupt_in_time(tmp_path: Path) -> None:
    minifat_at, chain = _mini_chain(_fixture("word97-latin.doc"), "WordDocument")

    assert _corrupt(_timed(_patched(tmp_path, minifat_at + 4 * chain[3], 0x0FFFFFF0)))


def test_a_cycle_in_the_chain_of_the_mini_stream_itself_is_corrupt_in_time(tmp_path: Path) -> None:
    with olefile.OleFileIO(_fixture("word97-latin.doc")) as opened:
        ole: Any = opened
        chain = [ole.root.isectStart]
        for _ in range(-(-ole.root.size // ole.sectorsize) - 1):
            chain.append(ole.fat[chain[-1]])
        fat_at = (struct.unpack_from("<I", (FIXTURES / "word97-latin.doc").read_bytes(), 0x4C)[0] + 1) * 512

    assert _corrupt(_timed(_patched(tmp_path, fat_at + 4 * chain[5], chain[2])))


# --- the sniff in front of the OLE reader --------------------------------------


def test_rtf_under_a_doc_name_is_read_as_rtf(tmp_path: Path) -> None:
    path = _write(tmp_path, b"{\\rtf1\\ansi rtfquendel im Text\\par}")

    assert "rtfquendel" in extract_msword(path).text


def test_docx_under_a_doc_name_is_read_as_docx(tmp_path: Path) -> None:
    document = docx.Document()
    document.add_paragraph("docxquendel im Absatz")
    buffer = io.BytesIO()
    document.save(buffer)
    path = _write(tmp_path, buffer.getvalue())

    assert "docxquendel" in extract_msword(path).text


@pytest.mark.parametrize("prefix", [b"", b"  \r\n\t", b"\xef\xbb\xbf"], ids=["bare", "whitespace", "bom"])
def test_html_under_a_doc_name_is_read_as_html(tmp_path: Path, prefix: bytes) -> None:
    path = _write(tmp_path, prefix + b"<html><body><p>htmlquendel</p><script>skript()</script></body></html>")

    outcome = extract_msword(path)

    assert "htmlquendel" in outcome.text
    assert "skript" not in outcome.text


@pytest.mark.parametrize(
    "payload", [b"", bytes(range(256)) * 4, b"Nur ein Text ohne Auszeichnung."], ids=["empty", "binary", "plain"]
)
def test_anything_else_under_a_doc_name_is_an_unsupported_variant(tmp_path: Path, payload: bytes) -> None:
    assert extract_msword(_write(tmp_path, payload)) == ExtractionOutcome.skipped(Reason.UNSUPPORTED_VARIANT)


def test_a_failure_names_the_class_and_nothing_of_the_file(tmp_path: Path) -> None:
    path = _doc(tmp_path, ["vertraulichquendel"], fcs={0: 0x00100000})

    outcome = extract_doc(path)

    assert outcome.detail is not None
    assert outcome.detail.endswith("CorruptDocument")
    assert "vertraulichquendel" not in outcome.detail
    assert str(tmp_path) not in outcome.detail
