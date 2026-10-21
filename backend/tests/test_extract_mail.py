"""The mail reader (FMT-01, D-31-04).

Every mail here is built at run time, with email.message.EmailMessage where the
standard library can say what is meant and with raw bytes where the case is
about the bytes themselves (encoded words, an unknown charset, a pathological
structure). No mail of a third party is checked in.

The limits are the heart of this file: a mail is a container of user supplied
parts, and the parser of the standard library builds every part and recurses
per level before any loop of ours could count. Measured on CPython 3.13.13
(2026-10-11): 200 000 empty parts parse in 10.8 s, 1 000 nested levels end in
RecursionError inside the parser, a From header with 5 000 open parentheses
ends in RecursionError when it is read.
"""

from __future__ import annotations

import logging
import time
from email.message import EmailMessage, Message
from email.parser import BytesParser
from pathlib import Path
from typing import Any

import pytest

from findling.extract import mail
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.mail import MAX_MAIL_PARTS, clean_display_name, extract_eml

PDF_BYTES = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"


def _write(directory: Path, payload: bytes, name: str = "post.eml") -> str:
    path = directory / name
    path.write_bytes(payload)
    return str(path)


def _plain_mail() -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = "Angebot Dachsanierung"
    message["From"] = "Erika Mustermann <erika@example.org>"
    message["To"] = "max@example.org"
    message["Cc"] = "buero@example.org"
    message.set_content("Bitte bis Freitag die Grundstücksverkehrsgenehmigung prüfen.")
    return message


def _wide_mail(parts: int, declaration: bytes = b'boundary="b"') -> bytes:
    """One multipart/mixed mail with ``parts`` empty parts, built without objects."""
    head = (
        b"Subject: Sammelpost breit\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; " + declaration + b"\r\n\r\n"
    )
    return head + b"--b\r\n\r\n" * parts + b"--b--\r\n"


def _nested_mail(depth: int) -> bytes:
    """``depth`` levels of multipart/mixed, each holding the next one."""
    out = [b"Subject: Tiefe Post\r\nMIME-Version: 1.0\r\n"]
    out.extend(
        b'Content-Type: multipart/mixed; boundary="b%d"\r\n\r\n--b%d\r\n' % (level, level) for level in range(depth)
    )
    out.append(b"Content-Type: text/plain\r\n\r\nInnerster Text\r\n")
    out.extend(b"--b%d--\r\n" % level for level in reversed(range(depth)))
    return b"".join(out)


def _forwarded_mail(depth: int) -> bytes:
    """``depth`` levels of message/rfc822: nesting without a single boundary."""
    out = [b"Subject: Weitergeleitet\r\nMIME-Version: 1.0\r\n"]
    out.extend(b"Content-Type: message/rfc822\r\n\r\nSubject: Ebene %d\r\n" % level for level in range(depth))
    out.append(b"Content-Type: text/plain\r\n\r\nInnerster Text\r\n")
    return b"".join(out)


def _attachment_mail(count: int) -> bytes:
    message = EmailMessage()
    message["Subject"] = "Viele Belege"
    message.set_content("Anbei die Belege.")
    for number in range(count):
        message.add_attachment(b"x", maintype="application", subtype="octet-stream", filename=f"beleg{number}.bin")
    return message.as_bytes()


class _ParseSpy:
    """Counts every BytesParser.parse, split by the headersonly switch it was given.

    BytesHeaderParser.parse goes through BytesParser.parse with headersonly set,
    so one patched function sees both the full parse and the header parse.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.full = 0
        self.headers_only = 0
        original = BytesParser.parse

        def parse(parser: BytesParser, fp: Any, headersonly: bool = False) -> Message:
            if headersonly:
                self.headers_only += 1
            else:
                self.full += 1
            return original(parser, fp, headersonly=headersonly)

        monkeypatch.setattr(BytesParser, "parse", parse)


# -- what a mail yields --------------------------------------------------------


def test_a_plain_mail_yields_subject_sender_recipients_and_body(tmp_path: Path) -> None:
    outcome = extract_eml(_write(tmp_path, _plain_mail().as_bytes()))

    assert outcome.state is State.INDEXED
    assert outcome.reason is None
    for expected in (
        "Angebot Dachsanierung",
        "Erika Mustermann",
        "erika@example.org",
        "max@example.org",
        "buero@example.org",
        "Grundstücksverkehrsgenehmigung",
    ):
        assert expected in outcome.text


def test_bcc_and_the_received_chain_stay_out(tmp_path: Path) -> None:
    raw = (
        b"Received: from relay.intern.example by mx.example; Mon, 5 Oct 2026 10:00:00 +0200\r\n"
        b"Subject: Protokoll\r\nBcc: verdeckt@example.org\r\n\r\nText\r\n"
    )
    outcome = extract_eml(_write(tmp_path, raw))

    assert "Protokoll" in outcome.text
    assert "verdeckt@example.org" not in outcome.text
    assert "relay.intern.example" not in outcome.text


def test_encoded_words_are_decoded_in_utf_8_and_in_iso_8859_1(tmp_path: Path) -> None:
    raw = (
        b"Subject: =?utf-8?q?J=C3=BCrgen?= meldet sich\r\n"
        b"From: =?iso-8859-1?q?J=FCrgen_M=FCller?= <juergen@example.org>\r\n"
        b"To: info@example.org\r\n\r\nHallo\r\n"
    )
    outcome = extract_eml(_write(tmp_path, raw))

    assert "Jürgen meldet sich" in outcome.text
    assert "Jürgen Müller" in outcome.text
    assert "=?" not in outcome.text


def test_a_mail_with_only_html_yields_its_text_without_script_and_style(tmp_path: Path) -> None:
    message = EmailMessage()
    message["Subject"] = "Newsletter"
    message.set_content(
        "<html><head><style>p { color: rebeccapurple; }</style></head>"
        "<body><p>Sommerfest am Hafen</p><script>track('geheimeskript');</script></body></html>",
        subtype="html",
    )
    outcome = extract_eml(_write(tmp_path, message.as_bytes()))

    assert outcome.state is State.INDEXED
    assert "Sommerfest am Hafen" in outcome.text
    assert "rebeccapurple" not in outcome.text
    assert "geheimeskript" not in outcome.text
    assert "<p>" not in outcome.text


def test_an_xhtml_part_with_its_own_declaration_is_read(tmp_path: Path) -> None:
    # Pitfall 5 of phase 31 through the whole reader, not only through html_to_text.
    message = EmailMessage()
    message["Subject"] = "XHTML"
    message.set_content(
        '<?xml version="1.0" encoding="iso-8859-1"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Kündigungsfrist</p></body></html>',
        subtype="html",
    )
    outcome = extract_eml(_write(tmp_path, message.as_bytes()))

    assert "Kündigungsfrist" in outcome.text


def test_alternative_prefers_the_plain_part_and_reads_the_html_part_not_twice(tmp_path: Path) -> None:
    message = EmailMessage()
    message["Subject"] = "Zwei Fassungen"
    message.set_content("Die schlichte Fassung")
    message.add_alternative("<html><body><p>Die bunte Fassung</p></body></html>", subtype="html")
    outcome = extract_eml(_write(tmp_path, message.as_bytes()))

    assert "Die schlichte Fassung" in outcome.text
    assert "Die bunte Fassung" not in outcome.text


def test_an_unknown_charset_ends_in_the_text_and_not_in_an_error(tmp_path: Path) -> None:
    # Pitfall 4: get_content raises LookupError for a charset no codec knows.
    raw = (
        b"Subject: Zeichensatz\r\nMIME-Version: 1.0\r\n"
        b"Content-Type: text/plain; charset=x-unknown-zz\r\n"
        b"Content-Transfer-Encoding: 8bit\r\n\r\n"
        b"Die K\xc3\xbcndigungsfrist betr\xc3\xa4gt drei Monate.\r\n"
    )
    outcome = extract_eml(_write(tmp_path, raw))

    assert outcome.state is State.INDEXED
    assert "Kündigungsfrist" in outcome.text


def test_attachments_appear_with_their_names_and_never_with_their_content(tmp_path: Path) -> None:
    # D-31-04: names yes, content no. The text attachment is the load bearing
    # one, a reader that walked every text part would pick it up.
    message = _plain_mail()
    message.add_attachment(PDF_BYTES, maintype="application", subtype="pdf", filename="vertrag.pdf")
    message.add_attachment("geheimerinhalt im anhang", filename="notiz.txt")
    outcome = extract_eml(_write(tmp_path, message.as_bytes()))

    assert outcome.state is State.INDEXED
    assert "vertrag.pdf" in outcome.text
    assert "notiz.txt" in outcome.text
    assert "geheimerinhalt" not in outcome.text
    assert "Catalog" not in outcome.text


def test_an_attachment_name_loses_its_bidi_override(tmp_path: Path) -> None:
    message = _plain_mail()
    message.add_attachment(b"x", maintype="application", subtype="octet-stream", filename="rechnung\u202efdp.exe")
    outcome = extract_eml(_write(tmp_path, message.as_bytes()))

    assert "rechnungfdp.exe" in outcome.text
    assert "\u202e" not in outcome.text


def test_clean_display_name_removes_controls_and_bidi_and_caps_the_length() -> None:
    hidden = "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u200e\u200f"
    assert clean_display_name(f"a{hidden}b\x00\r\n\tc.pdf") == "abc.pdf"
    assert clean_display_name("  Übersicht 2026.pdf  ") == "Übersicht 2026.pdf"
    assert len(clean_display_name("x" * 1000)) == 255


def test_an_empty_mail_is_empty_text(tmp_path: Path) -> None:
    assert extract_eml(_write(tmp_path, b"")) == ExtractionOutcome.skipped(Reason.EMPTY_TEXT)


def test_a_broken_html_part_costs_the_body_and_not_the_headers(tmp_path: Path) -> None:
    # An XHTML part that the XML parser refuses: the subject still finds the mail.
    raw = (
        b"Subject: Kaputte Seite\r\nMIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        b'<?xml version="1.0"?><html><p>offenes Element\r\n'
    )
    outcome = extract_eml(_write(tmp_path, raw))

    assert outcome.state is State.INDEXED
    assert "Kaputte Seite" in outcome.text


def test_an_empty_html_part_is_no_error(tmp_path: Path) -> None:
    raw = b"Subject: Ohne Inhalt\r\nMIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
    outcome = extract_eml(_write(tmp_path, raw))

    assert outcome.state is State.INDEXED
    assert "Ohne Inhalt" in outcome.text


def test_a_header_that_beats_the_parser_is_left_out(tmp_path: Path) -> None:
    raw = b"Subject: Klammern\r\nFrom: " + b"(" * 5000 + b"a@example.org\r\n\r\nText bleibt\r\n"
    outcome = extract_eml(_write(tmp_path, raw))

    assert outcome.state is State.INDEXED
    assert "Klammern" in outcome.text
    assert "Text bleibt" in outcome.text
    assert "a@example.org" not in outcome.text


def test_nothing_of_the_mail_reaches_the_log(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    # T-31-12. The reader itself logs nothing, and neither may anything it calls.
    message = _plain_mail()
    message.add_attachment(PDF_BYTES, maintype="application", subtype="pdf", filename="vertrag.pdf")
    with caplog.at_level(logging.DEBUG):
        extract_eml(_write(tmp_path, message.as_bytes()))
        extract_eml(_write(tmp_path, _wide_mail(MAX_MAIL_PARTS + 1), "breit.eml"))

    logged = "\n".join(record.getMessage() for record in caplog.records)
    for secret in ("Dachsanierung", "erika@example.org", "vertrag.pdf", "Sammelpost"):
        assert secret not in logged


# -- the limits ----------------------------------------------------------------


def test_more_attachments_than_the_limit_are_truncated(tmp_path: Path) -> None:
    outcome = extract_eml(_write(tmp_path, _attachment_mail(MAX_MAIL_PARTS + 1)))

    assert outcome.state is State.INDEXED
    assert outcome.truncated
    assert "Viele Belege" in outcome.text


def test_the_attachment_loop_counts_as_well_when_the_count_before_parsing_misses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The second line of defence: should the rough count ever miss a structure,
    # the loop over the attachments stops at the same limit.
    monkeypatch.setattr(mail, "count_parts", lambda raw: 0)
    outcome = extract_eml(_write(tmp_path, _attachment_mail(MAX_MAIL_PARTS + 1)))

    assert outcome.state is State.INDEXED
    assert outcome.truncated
    assert f"beleg{MAX_MAIL_PARTS - 1}.bin" in outcome.text
    assert f"beleg{MAX_MAIL_PARTS}.bin" not in outcome.text


def test_exactly_the_limit_of_attachments_is_read_in_full(tmp_path: Path) -> None:
    # The body is a part of its own, so the limit minus one attachments make
    # exactly MAX_MAIL_PARTS parts.
    outcome = extract_eml(_write(tmp_path, _attachment_mail(MAX_MAIL_PARTS - 1)))

    assert outcome.state is State.INDEXED
    assert not outcome.truncated
    assert f"beleg{MAX_MAIL_PARTS - 2}.bin" in outcome.text


def test_two_hundred_thousand_parts_are_never_parsed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Befund 8 of the plan check. Without the count before parsing this mail
    # costs the parser 10.8 s (measured) and an object per part.
    spy = _ParseSpy(monkeypatch)
    path = _write(tmp_path, _wide_mail(200_000))

    started = time.monotonic()
    outcome = extract_eml(path)
    elapsed = time.monotonic() - started

    assert outcome.state is State.INDEXED
    assert outcome.truncated
    assert "Sammelpost breit" in outcome.text
    assert spy.full == 0
    assert spy.headers_only == 1
    assert elapsed < 5


@pytest.mark.parametrize(
    "declaration",
    [b'BOUNDARY="b"', b"boundary=b", b"boundary*=us-ascii''b", b'boundary*0="b"', b"boundary*0*=''b"],
    ids=["upper-case", "bare", "rfc2231-extended", "rfc2231-section", "rfc2231-extended-section"],
)
def test_every_spelling_of_the_boundary_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, declaration: bytes
) -> None:
    # The parser of the standard library accepts all five (measured), so the
    # count has to know all five, or a spelling is a way around it.
    spy = _ParseSpy(monkeypatch)
    outcome = extract_eml(_write(tmp_path, _wide_mail(MAX_MAIL_PARTS + 1, declaration)))

    assert outcome.truncated
    assert spy.full == 0


def test_a_boundary_split_into_sections_is_counted_as_the_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = (
        _wide_mail(MAX_MAIL_PARTS + 1, b'boundary*0="b"')
        .replace(b"--b", b"--bb")
        .replace(b'boundary*0="b"', b'boundary*0="b"; boundary*1="b"')
    )
    spy = _ParseSpy(monkeypatch)
    outcome = extract_eml(_write(tmp_path, raw))

    assert outcome.truncated
    assert spy.full == 0


def test_lines_that_only_look_like_delimiters_do_not_count(tmp_path: Path) -> None:
    # A signature separator is "-- ", and a mail can have thousands of them.
    message = EmailMessage()
    message["Subject"] = "Lange Signaturen"
    message.set_content("Erster Absatz\n" + "-- \nGruss\n" * 5000 + "Letzter Absatz\n")
    outcome = extract_eml(_write(tmp_path, message.as_bytes()))

    assert outcome.state is State.INDEXED
    assert not outcome.truncated
    assert "Letzter Absatz" in outcome.text


def test_delimiters_after_a_lone_carriage_return_count_as_well(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The parser of the standard library splits lines at a lone CR too.
    spy = _ParseSpy(monkeypatch)
    raw = _wide_mail(MAX_MAIL_PARTS + 1).replace(b"\r\n", b"\r")
    outcome = extract_eml(_write(tmp_path, raw))

    assert outcome.truncated
    assert spy.full == 0


def test_nine_hundred_nested_levels_are_read_without_a_crash(tmp_path: Path) -> None:
    outcome = extract_eml(_write(tmp_path, _nested_mail(900)))

    assert outcome.state is State.INDEXED
    assert "Tiefe Post" in outcome.text


def test_a_thousand_nested_levels_end_as_corrupt_with_the_name_of_the_error(tmp_path: Path) -> None:
    # Within the count of parts, beyond the recursion of the parser (measured).
    outcome = extract_eml(_write(tmp_path, _nested_mail(MAX_MAIL_PARTS)))

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT, detail="RecursionError")


def test_twenty_five_hundred_nested_levels_stop_at_the_count_before_parsing(tmp_path: Path) -> None:
    # Every level opens with a delimiter line of its own, so this structure is
    # over the count of parts before the parser could recurse at all.
    outcome = extract_eml(_write(tmp_path, _nested_mail(2500)))

    assert outcome.state is State.INDEXED
    assert outcome.truncated
    assert "Tiefe Post" in outcome.text


def test_twenty_five_hundred_forwarded_levels_end_as_mail_nesting(tmp_path: Path) -> None:
    # message/rfc822 nests without a boundary, so no count of parts sees it
    # coming: the catch around the parser ends it, and the count of forward
    # headers names it (D-36-17, plan 36-09).
    outcome = extract_eml(_write(tmp_path, _forwarded_mail(2500)))

    assert outcome == ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail="mail_nesting")


def _raise_recursion(*args: object, **kwargs: object) -> None:
    raise RecursionError


@pytest.mark.parametrize("method", ["get_body", "iter_attachments", "get_content"])
def test_a_recursion_error_in_every_access_ends_as_corrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    # get_body, iter_attachments and get_content recurse on their own and can
    # raise below the depth at which the parser does.
    message = _plain_mail()
    message.add_attachment(PDF_BYTES, maintype="application", subtype="pdf", filename="vertrag.pdf")
    path = _write(tmp_path, message.as_bytes())
    monkeypatch.setattr(EmailMessage, method, _raise_recursion)

    outcome = extract_eml(path)

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT, detail="RecursionError")
