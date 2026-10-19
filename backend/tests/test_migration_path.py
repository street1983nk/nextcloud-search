"""The migration pages from fulltextsearch, held against the wording the owner accepted.

Phase 34 (UMST-01) ships one page in three languages, ``docs/migrate-from-
fulltextsearch.md`` (German, the default like ``README.md``), ``.en.md`` and
``.fr.md``. The owner accepted the wording on 19.10.2026 (``34-WORTLAUT.md``,
answers O2 to O5), and this module keeps what that acceptance fixed:

* **The pages.** All three exist, and line 1 of each is the language switch of
  the READMEs: the own language without a link, the two others linked to the
  sibling files (D-34-01).
* **The formula.** Each page carries the accepted formula of its language at
  least once (O2). Markdown wraps lines, a reader does not see the wrap, so the
  check runs over the text with its whitespace collapsed.
* **The forbidden phrase.** No shipped text claims that Findling is the one and
  only OCR, in German, English or French (O3). The reach is the list of O3 and
  is a set of directories and not of names, so the file of tomorrow is read on
  the day it arrives; a floor under the number of files keeps an emptied reach
  from looking green. The one legitimate sentence that a plain substring search
  would hit, "keine einzige OCR-Seite" in ``docs/performance.md``, is read as a
  positive control: the lookahead lets it pass, and a mutated sentence per
  language is exactly one finding.
* **Honesty on the pages.** fulltextsearch is maintained again, so no orphan
  wording; it does not need Elasticsearch, only its platform app
  fulltextsearch_elasticsearch needs an Elasticsearch service; similar
  documents belong to phase 35 and are not delivered yet; the placeholders of
  the wording draft are gone; no en or em dash. Required are a date line, the
  loss of Deck cards and the default of external storage.
* **Links.** Every relative link of a page points at a file that exists, every
  absolute link is https.

The shape is the shape of the other textual gates (``test_store_metadata.py``,
``test_public_artifacts.py``): pure scan functions that return findings naming
the file and the reason, tests on top of them, and self tests against mutated
samples so that a gate whose body was deleted cannot report zero findings and
look healthy. The forbidden words are assembled from halves and the non ASCII
characters are escapes, so that this module does not carry what it keeps out
and stays ASCII. The scan of the phase 35 wording is a function of its own,
because plan 34-04 applies it to the README lines and the store draft as well.

Test names carry fixed prefixes, so a plan selects them without guessing:
``test_pages_*``, ``test_forbidden_*``, ``test_positive_control_*``,
``test_mutated_*`` and ``test_honesty_*``.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"

# The three pages of D-34-01, keyed by language.
PAGES: dict[str, Path] = {
    "de": DOCS_DIR / "migrate-from-fulltextsearch.md",
    "en": DOCS_DIR / "migrate-from-fulltextsearch.en.md",
    "fr": DOCS_DIR / "migrate-from-fulltextsearch.fr.md",
}

# Line 1 of each page, exactly as README.md:1 does it.
_FRANCAIS = "Fran\u00e7ais"
SWITCH_LINES: dict[str, str] = {
    "de": f"Deutsch | [English](migrate-from-fulltextsearch.en.md) | [{_FRANCAIS}](migrate-from-fulltextsearch.fr.md)",
    "en": f"[Deutsch](migrate-from-fulltextsearch.md) | English | [{_FRANCAIS}](migrate-from-fulltextsearch.fr.md)",
    "fr": f"[Deutsch](migrate-from-fulltextsearch.md) | [English](migrate-from-fulltextsearch.en.md) | {_FRANCAIS}",
}

# The formula of UMST-01 in German, and its English and French form as accepted
# in O2 on 19.10.2026.
FORMULAS: dict[str, str] = {
    "de": "OCR ohne Datei\u00e4nderung und ohne Elasticsearch",
    "en": "OCR without changing files and without Elasticsearch",
    "fr": "OCR sans modifier les fichiers et sans Elasticsearch",
}

# The forbidden claim of uniqueness, one pattern per language (O3, answer b).
# The lookahead lets a hyphenated continuation pass ("keine einzige OCR-Seite"
# counts pages, it does not describe Findling). Assembled from halves.
_OCR = "O" + "CR"
FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "de": re.compile(r"\b" + "einz" + r"ig\w*\s+" + _OCR + r"(?![-\w])", re.IGNORECASE),
    "en": re.compile(r"\b" + "on" + r"ly\s+" + _OCR + r"(?![-\w])", re.IGNORECASE),
    "fr": re.compile(r"\b" + "seu" + r"le?s?\s+" + _OCR + r"(?![-\w])", re.IGNORECASE),
}

# The reach of O3: per root the suffixes that are text. Directories and not
# names; images and other bytes are left out by their suffix.
_TEXT = frozenset({".md", ".txt", ".xml", ".json", ".html"})
SCOPE_DIRS: tuple[tuple[Path, frozenset[str]], ...] = (
    (DOCS_DIR, _TEXT),
    (REPO_ROOT / "php" / "templates", frozenset({".php", *_TEXT})),
    (REPO_ROOT / "php" / "l10n", frozenset({".js", ".json"})),
    (REPO_ROOT / "store", _TEXT),
)
SCOPE_EXCLUDED_DIRS: tuple[Path, ...] = (DOCS_DIR / "measurements",)
SCOPE_FILES: tuple[Path, ...] = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "README.en.md",
    REPO_ROOT / "README.fr.md",
    REPO_ROOT / "CHANGELOG.md",
    REPO_ROOT / "php" / "appinfo" / "info.xml",
    REPO_ROOT / "backend" / "appinfo" / "info.xml",
)

# Counted on 19.10.2026 before the pages existed: 39 text files under docs/
# outside measurements/, 2 templates, 16 catalogues, 1 file under store/ and
# the 6 named files, 64 in all. The floor sits under that number, so that a plan
# adding files never has to come here, while an emptied reach goes red.
SCOPE_FLOOR = 60

# The positive control of O3: the one sentence in the reach that a substring
# search for the forbidden phrase would hit, and that the lookahead lets pass.
CONTROL_FILE = DOCS_DIR / "performance.md"
CONTROL_SENTENCE = "keine " + "einz" + "ige " + _OCR + "-Seite"

# One mutated sentence per language; each must be exactly one finding.
MUTATED_SENTENCES: dict[str, str] = {
    "de": "Findling ist die " + "einz" + "ige " + _OCR + ".",
    "en": "Findling is the " + "on" + "ly " + _OCR + " for Nextcloud.",
    "fr": "Findling est la " + "seu" + "le " + _OCR + " pour Nextcloud.",
}

# Orphan wording, forbidden on the pages: fulltextsearch is maintained again
# (releases of 20.09.2026 and 07.10.2026). Stems where a language inflects.
ORPHAN_WORDS: tuple[re.Pattern[str], ...] = (
    re.compile("verw" + "aist", re.IGNORECASE),
    re.compile(r"nicht\s+" + "gepf" + "legt", re.IGNORECASE),
    re.compile(r"\b" + "t" + r"ot\b", re.IGNORECASE),
    re.compile("orph" + "aned", re.IGNORECASE),
    re.compile("aband" + "oned", re.IGNORECASE),
    re.compile("unmain" + "tained", re.IGNORECASE),
    re.compile("aband" + "onn", re.IGNORECASE),
    re.compile("orphe" + "lin", re.IGNORECASE),
)

# The wording of phase 35, which is not delivered yet. Case does not matter,
# whitespace is collapsed before the search.
PHASE35_WORDS: tuple[str, ...] = (
    "\u00c4hnliche " + "Dokumente",
    "Similar " + "documents",
    "Documents " + "similaires",
)

# The claim that fulltextsearch needs Elasticsearch, inside one sentence. The
# word boundary keeps fulltextsearch_elasticsearch and files_fulltextsearch out,
# because the underscore is a word character.
_NEED_VERBS = r"(?:braucht|ben\u00f6tigt|requires?|needs?|n\u00e9cessite|exige|besoin)"
NEEDS_ELASTICSEARCH = re.compile(
    r"\bfulltextsearch\b.*?\b" + _NEED_VERBS + r"\b.*?Elasticsearch",
    re.IGNORECASE,
)
# A sentence ends at . ! ? or ; followed by whitespace, at a blank line, and at
# the start of a list item.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?;])\s+|\n\s*\n|\n\s*(?:[-*]|\d+\.)\s+")

# Leftovers of the wording draft in all three languages, and its marker O5.
PLACEHOLDERS: tuple[str, ...] = ("[Be" + "leg", "[Evi" + "dence", "[Pre" + "uve", "[O" + "5]")

EN_DASH = "\u2013"
EM_DASH = "\u2014"

# Required on each page: the date line, the loss of Deck cards and the default
# of external storage, in the words of the accepted wording.
DATE_LINES: dict[str, re.Pattern[str]] = {
    "de": re.compile(r"^Stand: \d{2}\.\d{2}\.\d{4}$", re.MULTILINE),
    "en": re.compile(r"^As of: \d{1,2} [A-Z][a-z]+ \d{4}$", re.MULTILINE),
    "fr": re.compile(r"^Situation au \d{1,2} [a-z\u00e9\u00fb]+ \d{4}$", re.MULTILINE),
}
DECK_WORD = "Deck"
EXTERNAL_STORAGE: dict[str, str] = {
    "de": "externe speicher",
    "en": "external storage",
    "fr": "stockage externe",
}

_MD_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _flat(text: str) -> str:
    """Collapse every run of whitespace into one space, as a reader sees it."""
    return " ".join(text.split())


def _rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def scope_files() -> list[Path]:
    """Every file of the O3 reach that exists, sorted."""
    found: set[Path] = {path for path in SCOPE_FILES if path.is_file()}
    for root, suffixes in SCOPE_DIRS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(root).parts):
                continue
            if any(path.is_relative_to(excluded) for excluded in SCOPE_EXCLUDED_DIRS):
                continue
            found.add(path)
    return sorted(found)


def scan_forbidden(text: str, where: str) -> list[str]:
    """One finding per occurrence of the forbidden claim of uniqueness."""
    findings: list[str] = []
    for language, pattern in FORBIDDEN_PATTERNS.items():
        findings.extend(f"{where}: forbidden claim ({language}) {match.group(0)!r}" for match in pattern.finditer(text))
    return findings


def scan_phase35_wording(text: str, where: str) -> list[str]:
    """One finding per occurrence of the phase 35 wording (reused by plan 34-04)."""
    flat = _flat(text).casefold()
    return [
        f"{where}: phase 35 wording {word!r}"
        for word in PHASE35_WORDS
        for _ in re.finditer(re.escape(word.casefold()), flat)
    ]


def scan_needs_elasticsearch(text: str, where: str) -> list[str]:
    """One finding per sentence that says fulltextsearch needs Elasticsearch."""
    findings: list[str] = []
    for sentence in _SENTENCE_BREAK.split(text):
        flat = _flat(sentence)
        if NEEDS_ELASTICSEARCH.search(flat):
            findings.append(f"{where}: claims that fulltextsearch needs Elasticsearch: {flat[:120]!r}")
    return findings


def scan_honesty(language: str, text: str, where: str) -> list[str]:
    """The forbidden and required words of the leitplanken on one page."""
    flat = _flat(text)
    findings = [f"{where}: orphan wording {m.group(0)!r}" for p in ORPHAN_WORDS for m in p.finditer(flat)]
    findings += scan_phase35_wording(text, where)
    findings += scan_needs_elasticsearch(text, where)
    findings += [f"{where}: placeholder {p!r} left over" for p in PLACEHOLDERS if p in text]
    findings += [f"{where}: dash U+{ord(d):04X}" for d in (EN_DASH, EM_DASH) if d in text]
    if not DATE_LINES[language].search(text):
        findings.append(f"{where}: no date line matching {DATE_LINES[language].pattern!r}")
    if DECK_WORD not in text:
        findings.append(f"{where}: the loss of {DECK_WORD} cards is not named")
    if EXTERNAL_STORAGE[language] not in flat.casefold():
        findings.append(f"{where}: the external storage default ({EXTERNAL_STORAGE[language]!r}) is not named")
    return findings


def scan_page(language: str) -> list[str]:
    """Existence, switch line and formula of one page."""
    path = PAGES[language]
    where = _rel(path)
    if not path.is_file():
        return [f"{where}: missing"]
    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0] if text else ""
    findings: list[str] = []
    if first != SWITCH_LINES[language]:
        findings.append(f"{where}: line 1 is {first!r}, expected {SWITCH_LINES[language]!r}")
    if FORMULAS[language] not in _flat(text):
        findings.append(f"{where}: the formula {FORMULAS[language]!r} is missing")
    return findings


def scan_links(path: Path) -> list[str]:
    """Relative links must hit an existing file in the repository, absolute ones must be https."""
    where = _rel(path)
    if not path.is_file():
        return [f"{where}: missing"]
    findings: list[str] = []
    for target in _MD_LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith("https://"):
            continue
        if "://" in target or target.startswith(("http:", "mailto:", "//")):
            findings.append(f"{where}: link {target!r} is not https")
            continue
        file_part = target.split("#", 1)[0]
        if not file_part:
            continue
        resolved = (path.parent / file_part).resolve()
        if not resolved.is_relative_to(REPO_ROOT) or not resolved.is_file():
            findings.append(f"{where}: link {target!r} points at no file of the repository")
    return findings


def _page_text(language: str) -> str | None:
    path = PAGES[language]
    return path.read_text(encoding="utf-8") if path.is_file() else None


# --- pages ------------------------------------------------------------------


def test_pages_exist_with_switch_line_and_formula() -> None:
    findings = [finding for language in PAGES for finding in scan_page(language)]
    assert findings == [], "\n".join(findings)


def test_pages_links_resolve_and_are_https() -> None:
    findings = [finding for path in PAGES.values() for finding in scan_links(path)]
    assert findings == [], "\n".join(findings)


# --- forbidden phrase over the shipped scope --------------------------------


def test_forbidden_scope_is_not_empty() -> None:
    files = scope_files()
    assert len(files) >= SCOPE_FLOOR, f"only {len(files)} files in the O3 reach, floor {SCOPE_FLOOR}"
    assert CONTROL_FILE in files, f"{_rel(CONTROL_FILE)} is not in the reach"
    assert not any(path.is_relative_to(DOCS_DIR / "measurements") for path in files)
    assert not any(path.suffix == ".png" for path in files)


def test_forbidden_claim_occurs_in_no_shipped_file() -> None:
    findings = [
        finding for path in scope_files() for finding in scan_forbidden(path.read_text(encoding="utf-8"), _rel(path))
    ]
    assert findings == [], "\n".join(findings)


# --- positive control -------------------------------------------------------


def test_positive_control_performance_sentence_passes() -> None:
    lines = CONTROL_FILE.read_text(encoding="utf-8").splitlines()
    hits = [(number, line) for number, line in enumerate(lines, start=1) if CONTROL_SENTENCE in line]
    # Independent of the gate pattern: the sentence is there exactly once and a
    # plain substring search for the forbidden phrase would hit it.
    assert len(hits) == 1, f"expected one line with {CONTROL_SENTENCE!r}, found {len(hits)}"
    number, line = hits[0]
    assert ("einz" + "ige " + _OCR) in line
    assert scan_forbidden(line, f"{_rel(CONTROL_FILE)}:{number}") == []


def test_positive_control_platform_app_sentence_passes() -> None:
    # The accepted wording says the platform app needs Elasticsearch; that is
    # true and must not be read as a claim about fulltextsearch itself.
    sample = (
        "- fulltextsearch_elasticsearch: Releases [v35.0.1 und v34.0.3]"
        "(https://github.com/nextcloud/fulltextsearch_elasticsearch/releases) am\n"
        "  07.10.2026; diese Plattform-App braucht einen Elasticsearch-Dienst\n"
        "- fulltextsearch: Release [v35.0.0](https://github.com/nextcloud/fulltextsearch/releases)\n"
    )
    assert scan_needs_elasticsearch(sample, "sample") == []


# --- mutated samples --------------------------------------------------------


def test_mutated_forbidden_sentence_is_one_finding_per_language() -> None:
    for language, sentence in MUTATED_SENTENCES.items():
        findings = scan_forbidden(sentence, f"mutated-{language}")
        assert len(findings) == 1, (language, findings)
        assert f"({language})" in findings[0]


def test_mutated_forbidden_sentence_across_a_line_break_is_found() -> None:
    sentence = "Findling ist die " + "einz" + "ige\n" + _OCR + " im Store."
    assert len(scan_forbidden(sentence, "mutated-wrap")) == 1


def test_mutated_needs_elasticsearch_is_one_finding() -> None:
    for sentence in (
        "fulltextsearch braucht Elasticsearch.",
        "Note that fulltextsearch requires a running Elasticsearch.",
        "fulltextsearch n\u00e9cessite Elasticsearch.",
    ):
        assert len(scan_needs_elasticsearch(sentence, "mutated")) == 1, sentence


def test_mutated_phase35_wording_is_one_finding_per_language() -> None:
    for word in PHASE35_WORDS:
        sentence = f"Neu: {word.upper()} in der Suchleiste."
        assert len(scan_phase35_wording(sentence, "mutated")) == 1, word


def test_mutated_honesty_page_reports_each_rule() -> None:
    page = "fulltextsearch ist " + "verw" + "aist" + ". [Be" + "leg 34-02] " + EM_DASH + "\n"
    findings = scan_honesty("de", page, "mutated")
    reasons = " ".join(findings)
    for expected in ("orphan wording", "placeholder", "dash", "date line", "Deck", "external storage"):
        assert expected in reasons, (expected, findings)


# --- honesty on the pages ---------------------------------------------------


def test_honesty_pages_keep_the_leitplanken() -> None:
    findings: list[str] = []
    for language, path in PAGES.items():
        text = _page_text(language)
        if text is None:
            findings.append(f"{_rel(path)}: missing")
            continue
        findings += scan_honesty(language, text, _rel(path))
    assert findings == [], "\n".join(findings)
