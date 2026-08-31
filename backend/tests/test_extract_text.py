"""Plain text, HTML and RTF, including the German legacy encodings.

The cp1252 file and the broken RTF are written by the test rather than taken from
the reference corpus. Both cases are about a specific byte pattern, and a test
that depends on a corpus file for that is a test that starts passing for the wrong
reason the day somebody regenerates the corpus.

The three parser switches are checked by behaviour, not by reading the source: a
document that declares an external entity has to come back without the content of
that entity, whatever the parser decided to do about it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from findling import config
from findling.extract.dispatch import extract
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.text import extract_html, extract_plain, extract_rtf

GERMAN = (
    "Sehr geehrte Damen und Herren, die Kündigungsfrist für das Mietverhältnis "
    "beträgt drei Monate zum Monatsende. Bitte prüfen Sie die beigefügte Anlage "
    "und übersenden Sie uns eine kurze Bestätigung. Mit freundlichen Grüßen, Möller."
)

CORPUS = Path(__file__).resolve().parents[2] / "testdata" / "corpus"


def _write(directory: Path, name: str, payload: bytes) -> str:
    target = directory / name
    target.write_bytes(payload)
    return str(target)


def test_a_utf8_text_file_arrives_unchanged(tmp_path: Path) -> None:
    outcome = extract_plain(_write(tmp_path, "notes.txt", GERMAN.encode("utf-8")))

    assert outcome.state is State.INDEXED
    assert outcome.text == GERMAN
    assert outcome.truncated is False


def test_a_cp1252_file_with_german_umlauts_is_decoded_and_not_mangled(tmp_path: Path) -> None:
    # The one case that made charset detection non optional: every umlaut is a
    # single byte and invalid UTF-8, so the naive path turns the whole document
    # into replacement characters and the file becomes findable by nothing.
    outcome = extract_plain(_write(tmp_path, "alt.txt", GERMAN.encode("cp1252")))

    assert outcome.state is State.INDEXED
    assert "Kündigungsfrist" in outcome.text
    assert "Grüßen" in outcome.text
    assert "�" not in outcome.text


def test_the_legacy_encoding_file_of_the_reference_corpus_is_readable() -> None:
    outcome = extract_plain(str(CORPUS / "08-legacy-encoding.txt"))

    assert outcome.state is State.INDEXED
    assert "�" not in outcome.text


def test_bytes_that_are_no_text_at_all_end_as_encoding_unknown(tmp_path: Path) -> None:
    # Every high byte, in order: charset-normalizer has no answer and the UTF-8
    # fallback is nothing but replacement characters.
    payload = bytes(range(128, 256)) * 3
    outcome = extract_plain(_write(tmp_path, "unreadable.txt", payload))

    assert outcome == ExtractionOutcome.failed(Reason.ENCODING_UNKNOWN)


def test_html_yields_the_visible_text_only(tmp_path: Path) -> None:
    document = (
        "<html><head><title>Aktenvermerk</title>"
        "<style>body { color: rebeccapurple; }</style>"
        "<script>var geheim = 'nicht im index';</script></head>"
        "<body><h1>Grundstücksverkehrsgenehmigung</h1><p>Zweiter Absatz.</p></body></html>"
    )
    outcome = extract_html(_write(tmp_path, "seite.html", document.encode("utf-8")))

    assert outcome.state is State.INDEXED
    assert "Grundstücksverkehrsgenehmigung" in outcome.text
    assert "Zweiter Absatz." in outcome.text
    assert "rebeccapurple" not in outcome.text
    assert "nicht im index" not in outcome.text


def test_the_parser_resolves_no_external_entity_and_reaches_no_network(tmp_path: Path) -> None:
    # The entity points at a real file through an absolute URI, which is what makes
    # this test load bearing: measured against a parser built without the three
    # switches, the same document comes back as "Anlage TOPSECRET-PASSPHRASE".
    secret = tmp_path / "secret.txt"
    secret.write_bytes(b"TOPSECRET-PASSPHRASE")
    document = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!DOCTYPE html [\n"
        f'  <!ENTITY leak SYSTEM "{secret.as_uri()}">\n'
        '  <!ENTITY call SYSTEM "http://127.0.0.1:9/collect">\n'
        "]>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Anlage &leak; &call;</p></body></html>'
    )
    path = _write(tmp_path, "xxe.xhtml", document.encode("utf-8"))

    outcome = extract_html(path)

    assert "TOPSECRET" not in outcome.text
    assert "PASSPHRASE" not in outcome.text
    # The reference survives as text, which is the proof that the parser saw an
    # entity and declined to follow it rather than never noticing one.
    assert "&leak;" in outcome.text


def test_rtf_yields_its_text(tmp_path: Path) -> None:
    document = (
        r"{\rtf1\ansi\ansicpg1252\deff0 {\fonttbl {\f0 Times New Roman;}}"
        r"\f0\fs24 Sehr geehrte Damen und Herren, die K\'fcndigungsfrist "
        r"betr\'e4gt drei Monate.\par}"
    )
    outcome = extract_rtf(_write(tmp_path, "brief.rtf", document.encode("cp1252")))

    assert outcome.state is State.INDEXED
    assert "Kündigungsfrist" in outcome.text


def test_broken_rtf_is_skipped_instead_of_filling_the_index_with_nonsense(tmp_path: Path) -> None:
    # striprtf does not raise on this, it returns control characters. The share of
    # unprintable characters is the only defence there is.
    payload = b"{\\rtf1" + bytes(range(1, 128)) * 3
    outcome = extract_rtf(_write(tmp_path, "kaputt.rtf", payload))

    assert outcome == ExtractionOutcome.skipped(Reason.EMPTY_TEXT)


@pytest.mark.parametrize("payload", [b"", b"   \n\t  "])
def test_an_extraction_that_yields_nothing_is_skipped(payload: bytes, tmp_path: Path) -> None:
    outcome = extract_plain(_write(tmp_path, "leer.txt", payload))

    assert outcome == ExtractionOutcome.skipped(Reason.EMPTY_TEXT)


def test_text_over_the_character_cap_is_truncated(tmp_path: Path) -> None:
    cap = config.settings().max_text_chars
    payload = ("Aktenvermerk " * ((cap // 13) + 200)).encode("utf-8")
    outcome = extract_plain(_write(tmp_path, "lang.txt", payload))

    assert outcome.truncated is True
    assert outcome.text_chars == cap


@pytest.mark.parametrize(
    ("name", "mime", "payload", "needle"),
    [
        ("notes.txt", "text/plain", GERMAN.encode("utf-8"), "Mietverhältnis"),
        ("notes.md", "text/markdown", b"# Titel\n\nEin Absatz.", "Ein Absatz."),
        ("tabelle.csv", "text/csv", b"Name;Betrag\nMoeller;12", "Moeller"),
        ("seite.html", "text/html", b"<html><body><p>Ein Absatz.</p></body></html>", "Ein Absatz."),
        ("brief.rtf", "application/rtf", rb"{\rtf1\ansi Ein Absatz.\par}", "Ein Absatz."),
    ],
)
def test_the_dispatcher_reaches_all_three_text_routes(
    name: str, mime: str, payload: bytes, needle: str, tmp_path: Path
) -> None:
    outcome = extract(_write(tmp_path, name, payload), mime, len(payload))

    assert outcome.state is State.INDEXED
    assert needle in outcome.text
