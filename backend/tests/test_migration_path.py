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
* **README sections (UMST-03, plan 34-04).** Each README carries the short
  section the owner chose in O9 (variant 2, directly before "Installation") in
  the accepted wording, and links the page of its own language with a relative
  link exactly once; a link to the page of another language is one finding.
* **Store draft (plan 34-04).** ``docs/store-listing.md`` carries the section
  ``# Entwurf v1.5.0 (Teil Phase 34)`` once, with the head sentence naming the
  owner acceptance of 19.10.2026 (plan 34-05), and one table row per language
  of the store descriptions: the accepted line, a tag URL of v1.5.0 on the page
  of that language, no digit in the prose. ``info.xml`` stays unchanged until
  REL-05, so the gate reads the languages from it and never the line.

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
``test_mutated_*``, ``test_honesty_*``, ``test_readme_*`` and ``test_draft_*``.
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


# --- README sections and store draft (plan 34-04) ----------------------------

STORE_LISTING = DOCS_DIR / "store-listing.md"
INFO_XMLS: tuple[Path, ...] = (
    REPO_ROOT / "php" / "appinfo" / "info.xml",
    REPO_ROOT / "backend" / "appinfo" / "info.xml",
)

# The page of each language, as a README beside the repository root links it.
_PAGE_STEM = "migrate-from-fulltextsearch"
PAGE_NAMES: dict[str, str] = {language: path.name for language, path in PAGES.items()}

# Variant 2 of O9, accepted on 19.10.2026: a short section of its own directly
# before "Installation", heading and one line, character for character from
# 34-WORTLAUT.md section (C).
_A_GRAVE = "à"
README_SECTIONS: dict[str, tuple[Path, str, str]] = {
    "de": (
        REPO_ROOT / "README.md",
        "## Umstieg von fulltextsearch",
        (
            "Schritte zum Abschalten von fulltextsearch/Elasticsearch und was sich ändert: "
            "[docs/migrate-from-fulltextsearch.md](docs/migrate-from-fulltextsearch.md)."
        ),
    ),
    "en": (
        REPO_ROOT / "README.en.md",
        "## Switching from fulltextsearch",
        (
            "Steps to switch off fulltextsearch/Elasticsearch and what changes: "
            "[docs/migrate-from-fulltextsearch.en.md](docs/migrate-from-fulltextsearch.en.md)."
        ),
    ),
    "fr": (
        REPO_ROOT / "README.fr.md",
        f"## Passer de fulltextsearch {_A_GRAVE} Findling",
        (
            "Étapes pour désactiver fulltextsearch/Elasticsearch et ce qui change : "
            "[docs/migrate-from-fulltextsearch.fr.md](docs/migrate-from-fulltextsearch.fr.md)."
        ),
    ),
}
README_NEXT_HEADING = "## Installation"

DRAFT_OF_PHASE_34 = "# Entwurf v1.5.0 (Teil Phase 34)"
# The draft was accepted by the owner in the acceptance round of plan 34-05;
# the formal release step (info.xml) stays with REL-05 in phase 36.
DRAFT_HEAD = "Owner-Abnahme 19.10.2026"
TAG_BASE = "https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/"

# The store line of 34-WORTLAUT.md section (D), one per description language;
# a language without a page of its own links the English one.
_URL_SLOT = "<URL>"
STORE_LINES: dict[str, str] = {
    "en": f"Switching from fulltextsearch/Elasticsearch: [steps in the documentation]({_URL_SLOT})",
    "de": f"Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation]({_URL_SLOT})",
    "fr": f"Passer de fulltextsearch/Elasticsearch {_A_GRAVE} Findling : [étapes dans la documentation]({_URL_SLOT})",
}

_DESCRIPTION_TAG = re.compile(r'<description(?: lang="([A-Za-z_]+)")?><!\[CDATA\[')
_URL = re.compile(r"https?://[^\s)>`\]]+")
_LINK_TARGET = re.compile(r"\]\([^)\s]*\)")
_DRAFT_ROW = re.compile(r"^\| ([A-Za-z_]+) \| `(.*)` \|$", re.MULTILINE)


def tag_url(language: str) -> str:
    """The v1.5.0 tag URL of the page of one language (English for the rest)."""
    return TAG_BASE + PAGE_NAMES.get(language, PAGE_NAMES["en"])


def store_languages() -> list[str]:
    """The languages of the store descriptions of both info.xml, read and not assumed."""
    found: set[str] = set()
    for path in INFO_XMLS:
        text = path.read_text(encoding="utf-8")
        found.update(match.group(1) or "en" for match in _DESCRIPTION_TAG.finditer(text))
    return sorted(found)


def _mask_targets(text: str) -> str:
    """Replace every markdown link target by one slot, so wording and target are checked apart."""
    return _LINK_TARGET.sub(f"]({_URL_SLOT})", text)


def strip_urls(line: str) -> str:
    """The line without its URLs and link targets; a tag URL carries 1.5.0, no number of the text."""
    return _URL.sub("", _LINK_TARGET.sub("]()", line))


def scan_digits(line: str, where: str) -> list[str]:
    """One finding for a line whose prose carries a digit once the URLs are gone."""
    prose = strip_urls(line)
    return [f"{where}: a number in the text {prose!r}"] if re.search(r"\d", prose) else []


def scan_readme_links(language: str, text: str, where: str) -> list[str]:
    """The README links the page of its own language exactly once, and no other language's page."""
    own = f"docs/{PAGE_NAMES[language]}"
    targets = [target for target in _MD_LINK.findall(text) if _PAGE_STEM in target]
    if not targets:
        return [f"{where}: no link to {own}"]
    findings = [
        f"{where}: links {target!r}, the page of another language (expected {own!r})"
        for target in targets
        if target != own
    ]
    if not findings and len(targets) != 1:
        findings.append(f"{where}: links {own} {len(targets)} times, expected once")
    return findings


def scan_readme(language: str, text: str, where: str) -> list[str]:
    """Section of O9 in the accepted wording, before Installation, without number, and its link."""
    _, heading, line = README_SECTIONS[language]
    findings: list[str] = []
    lines = text.splitlines()
    if lines.count(heading) != 1:
        findings.append(f"{where}: no single section {heading!r}")
    else:
        start = lines.index(heading) + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith("#")), len(lines))
        after = lines[end] if end < len(lines) else None
        if after != README_NEXT_HEADING:
            findings.append(f"{where}: {heading!r} is followed by {after!r}, expected {README_NEXT_HEADING!r}")
        body = "\n".join(lines[start:end])
        if _mask_targets(_flat(body)) != _mask_targets(line):
            findings.append(f"{where}: the section reads {_flat(body)!r}, expected {line!r}")
        findings += scan_digits(_flat(body), where)
        findings += scan_phase35_wording(body, where)
    findings += scan_readme_links(language, text, where)
    return findings


def draft_section(listing: str) -> str | None:
    """The section of phase 34 in the store listing, cut like test_store_metadata.py does it."""
    if listing.splitlines().count(DRAFT_OF_PHASE_34) != 1:
        return None
    return listing.split(f"\n{DRAFT_OF_PHASE_34}\n", 1)[1].split("\n# ", 1)[0]


def scan_draft(listing: str, languages: list[str], where: str) -> list[str]:
    """Head sentence, one row per store language with its tag URL, and no main or relative link."""
    section = draft_section(listing)
    if section is None:
        return [f"{where}: no single section {DRAFT_OF_PHASE_34!r}"]
    findings: list[str] = []
    if DRAFT_HEAD not in _flat(section):
        findings.append(f"{where}: the head sentence {DRAFT_HEAD!r} is missing")
    matches = list(_DRAFT_ROW.finditer(section))
    rows = {match.group(1): match.group(2) for match in matches}
    for language in languages:
        row = rows.get(language)
        if row is None:
            findings.append(f"{where}: no store line for {language}")
            continue
        expected = STORE_LINES.get(language, STORE_LINES["en"])
        if _mask_targets(row) != expected:
            findings.append(f"{where}: the {language} line reads {row!r}, expected {expected!r}")
        targets = _MD_LINK.findall(row)
        if targets != [tag_url(language)]:
            findings.append(f"{where}: the {language} line links {targets!r}, expected [{tag_url(language)!r}]")
        findings += scan_digits(row, f"{where} ({language})")
    spans = [match.span() for match in matches]
    for link in _MD_LINK.finditer(section):
        if any(start <= link.start() < end for start, end in spans):
            continue
        target = link.group(1)
        if not target.startswith("https://"):
            findings.append(f"{where}: relative link {target!r} in the draft")
        elif "/blob/main/" in target:
            findings.append(f"{where}: link {target!r} on blob/main in the draft")
    findings += scan_phase35_wording(section, where)
    return findings


def _sample_draft() -> str:
    rows = "\n".join(
        f"| {language} | `{STORE_LINES[language].replace(_URL_SLOT, tag_url(language))}` |" for language in STORE_LINES
    )
    return (
        "# Vorher\n\nText.\n\n"
        f"{DRAFT_OF_PHASE_34}\n\n**{DRAFT_HEAD}.**\n\n| Sprache | Wortlaut |\n|---|---|\n{rows}\n\n"
        "# Danach\n"
    )


def _sample_readme(language: str) -> str:
    _, heading, line = README_SECTIONS[language]
    return f"# Findling\n\n## Anforderungen\n\n- RAM\n\n{heading}\n\n{line}\n\n{README_NEXT_HEADING}\n\nText.\n"


def test_readme_sections_link_the_page_of_their_language() -> None:
    findings: list[str] = []
    for language, (path, _, _) in README_SECTIONS.items():
        findings += scan_readme(language, path.read_text(encoding="utf-8"), _rel(path))
    assert findings == [], "\n".join(findings)


def test_readme_links_resolve() -> None:
    findings = [finding for path, _, _ in README_SECTIONS.values() for finding in scan_links(path)]
    assert findings == [], "\n".join(findings)


def test_draft_section_of_phase_34_carries_a_tag_link_per_language() -> None:
    languages = store_languages()
    assert languages == ["de", "en", "fr"], languages
    findings = scan_draft(STORE_LISTING.read_text(encoding="utf-8"), languages, _rel(STORE_LISTING))
    assert findings == [], "\n".join(findings)


def test_draft_tag_links_point_at_pages_that_exist() -> None:
    for language in store_languages():
        name = tag_url(language).removeprefix(TAG_BASE)
        assert (DOCS_DIR / name).is_file(), name


def test_positive_control_samples_are_clean() -> None:
    assert scan_draft(_sample_draft(), ["de", "en", "fr"], "sample") == []
    for language in README_SECTIONS:
        assert scan_readme(language, _sample_readme(language), f"sample-{language}") == [], language


def test_positive_control_digit_only_in_url_is_clean() -> None:
    line = f"Umstieg: [Schritte]({tag_url('de')}) und {tag_url('fr')}"
    assert re.search(r"\d", line)
    assert scan_digits(line, "sample") == []


def test_mutated_digit_in_prose_is_one_finding() -> None:
    line = f"Umstieg in 3 Schritten: [Schritte]({tag_url('de')})"
    assert len(scan_digits(line, "mutated")) == 1


def test_mutated_draft_without_section_is_one_finding() -> None:
    sample = _sample_draft().replace(f"{DRAFT_OF_PHASE_34}\n", "")
    assert len(scan_draft(sample, ["de", "en", "fr"], "mutated")) == 1


def test_mutated_draft_on_blob_main_is_one_finding() -> None:
    sample = _sample_draft().replace(tag_url("fr"), tag_url("fr").replace("/blob/v1.5.0/", "/blob/main/"))
    findings = scan_draft(sample, ["de", "en", "fr"], "mutated")
    assert len(findings) == 1, findings
    assert "fr line links" in findings[0]


def test_mutated_draft_without_head_sentence_is_one_finding() -> None:
    sample = _sample_draft().replace(DRAFT_HEAD, "Abgenommen")
    assert len(scan_draft(sample, ["de", "en", "fr"], "mutated")) == 1


def test_mutated_readme_on_the_english_page_is_one_finding() -> None:
    sample = _sample_readme("de").replace(
        "](docs/migrate-from-fulltextsearch.md)", "](docs/migrate-from-fulltextsearch.en.md)"
    )
    findings = scan_readme("de", sample, "mutated")
    assert len(findings) == 1, findings
    assert "another language" in findings[0]


def test_mutated_readme_phase35_wording_is_found() -> None:
    line = README_SECTIONS["en"][2]
    sample = _sample_readme("en").replace(line, line + " " + PHASE35_WORDS[1] + ".")
    findings = scan_readme("en", sample, "mutated")
    assert any("phase 35 wording" in finding for finding in findings), findings
