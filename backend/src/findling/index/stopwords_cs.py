"""The folded Czech stop word list of the cs chain, and nothing else.

Where it comes from: Apache Lucene, tag ``releases/lucene/10.5.2``, file
``lucene/analysis/common/src/resources/org/apache/lucene/analysis/cz/stopwords.txt``,
last changed in commit e8e4245d9b36123446546ff15967ac95429ea2b0, SHA-256 of the
original 61f06aa1e7567ee8c72e895ea33229033669ac1cc52c6d40369a9ee2b76ad915. The
original lies byte for byte in
``backend/tests/fixtures/lucene_cz_stopwords_10_5_2.txt``. What produced this
module: ``scripts/dev/czech_stopwords.py``. It is not edited by hand; a hand edit
is caught by the digest gate in ``backend/tests/test_czech_analyzer.py``.

License: Apache-2.0, Copyright The Apache Software Foundation (see
THIRD-PARTY.md and REUSE.toml). This is a modified version of the original in
the sense of Apache-2.0 section 4(b): every entry is folded to ASCII by the same
tantivy chain the index runs (lowercase, ascii_fold), the duplicates the fold
creates are dropped (172 lines, 171 unique, 169 folded), and the exceptions
below are removed. The order is the order of first appearance in the original.

Why one list and not a list plus a supplement as in :mod:`findling.index.stopwords`:
tantivy 0.26.2 carries no Czech list at all, so there is no built in list the
fold could tear. The folded list alone is what the cs chain filters, behind the
fold, at the same fold position as the Snowball chains.

**Exceptions.** Lucene's CzechAnalyzer filters unfolded, so its list was never
checked against what its entries become once the accents are gone. Every folded
form that is no entry of the original (67 of them) was reviewed one by one, and
the review is the table below. The single criterion: a form is an exception
exactly when the folded form is at the same time a common, standalone Czech
content word with a DIFFERENT meaning than the original entry, one that users
really search without accents (pattern: the verb "to be" folds into byt, which
is the noun "flat, apartment"). A folded form that is only the flat spelling of
the same word stays: it filters the word Lucene already filters, in the spelling
our fold leaves in the index. Content words of the original itself (strana,
zpravy, prvni and so on) stay as Lucene ships them. The meaning of every flat
form was looked up on en.wiktionary.org on 2026-10-10 ("wikt" below); the
original column spells each accented letter out, because accents appear nowhere
in this file, not even in a literal. Exceptions today: byt (flat, apartment)
and jez (weir).

Review table (form | original | verdict | reason):

    | timto | t(i-acute)mto | keep | same word, "hereby, by this"; wikt: no cs entry for the flat form |
    | budes | bude(s-caron) | keep | same word, "you will"; wikt: no cs entry for the flat form |
    | jses | jse(s-caron) | keep | same word, "you are (colloquial)"; wikt: no cs entry for the flat form |
    | muj | m(u-ring above)j | keep | same word, "my"; wikt: no cs entry for the flat form |
    | svym | sv(y-acute)m | keep | same word, "one's own"; wikt: no cs entry for the flat form |
    | proc | pro(c-caron) | keep | same word, "why"; wikt: no cs entry for the flat form |
    | mate | m(a-acute)te | keep | same word, "you have"; flat form also 3sg of mast, to confuse (wikt), rare |
    | kteri | kte(r-caron)(i-acute) | keep | same word, "who, which (pl.)"; wikt: no cs entry for the flat form |
    | nam | n(a-acute)m | keep | same word, "to us"; wikt: no cs entry for the flat form |
    | mit | m(i-acute)t | keep | same word, "to have"; wikt: no cs entry for the flat form |
    | protoze | proto(z-caron)e | keep | same word, "because"; wikt: no cs entry for the flat form |
    | nasi | na(s-caron)i | keep | same word, "our"; wikt: no cs entry for the flat form |
    | napiste | napi(s-caron)te | keep | same word, "write (imperative)"; wikt: no cs entry for the flat form |
    | coz | co(z-caron) | keep | same word, "which"; wikt: no cs entry for the flat form |
    | tim | t(i-acute)m | keep | same word, "by that"; wikt: no cs entry for the flat form |
    | takze | tak(z-caron)e | keep | same word, "so"; wikt: no cs entry for the flat form |
    | svych | sv(y-acute)ch | keep | same word, "one's own"; wikt: no cs entry for the flat form |
    | jeji | jej(i-acute) | keep | same word, "her"; wikt: no cs entry for the flat form |
    | svymi | sv(y-acute)mi | keep | same word, "one's own"; wikt: no cs entry for the flat form |
    | prave | prav(e-acute) | keep | same word, "right, genuine"; wikt: no cs entry for the flat form |
    | ci | (c-caron)i | keep | same word, "or"; wikt: no cs entry for the flat form |
    | tema | t(e-acute)ma | keep | same word, "topic"; wikt: no cs entry for the flat form |
    | pres | p(r-caron)es | keep | same word, "across, over"; flat form also informal pres, press (wikt), rare |
    | vam | v(a-acute)m | keep | same word, "to you"; wikt: no cs entry for the flat form |
    | kdyz | kdy(z-caron) | keep | same word, "when"; wikt: no cs entry for the flat form |
    | vsak | v(s-caron)ak | keep | same word, "however"; wikt: no cs entry for the flat form |
    | clanku | (c-caron)l(a-acute)nku | keep | same word, "article (gen./loc.)"; wikt: no cs entry for the flat form |
    | clanky | (c-caron)l(a-acute)nky | keep | same word, "articles"; wikt: no cs entry for the flat form |
    | pred | p(r-caron)ed | keep | same word, "before"; wikt: no cs entry for the flat form |
    | jeste | je(s-caron)t(e-caron) | keep | same word, "still, yet"; wikt: no cs entry for the flat form |
    | az | a(z-caron) | keep | same word, "until"; wikt: no cs entry for the flat form |
    | take | tak(e-acute) | keep | same word, "also"; wikt: no cs entry for the flat form |
    | prvni | prvn(i-acute) | keep | same word, "first"; wikt: no cs entry for the flat form |
    | vase | va(s-caron)e | keep | same word, "your"; wikt: no cs entry for the flat form |
    | ktera | kter(a-acute) | keep | same word, "which (f.)"; wikt: no cs entry for the flat form |
    | nas | n(a-acute)s | keep | same word, "us"; wikt: no cs entry for the flat form |
    | novy | nov(y-acute) | keep | same word, "new"; wikt: no cs entry for the flat form |
    | muze | m(u-ring above)(z-caron)e | keep | same word, "can"; wikt: no cs entry for the flat form |
    | sve | sv(e-acute) | keep | same word, "one's own"; wikt: no cs entry for the flat form |
    | jine | jin(e-acute) | keep | same word, "other"; wikt: no cs entry for the flat form |
    | zpravy | zpr(a-acute)vy | keep | same word, "news, messages"; wikt: no cs entry for the flat form |
    | nove | nov(e-acute) | keep | same word, "new"; wikt: no cs entry for the flat form |
    | neni | nen(i-acute) | keep | same word, "is not"; wikt: no cs entry for the flat form |
    | vas | v(a-acute)s | keep | same word, "you (acc.)"; wikt: no cs entry for the flat form |
    | uz | u(z-caron) | keep | same word, "already"; wikt: no cs entry for the flat form |
    | byt | b(y-acute)t | exception | "to be"; flat form is the noun byt, flat/apartment (wikt), common in leases |
    | vice | v(i-acute)ce | keep | same word, "more"; wikt: no cs entry for the flat form |
    | jiz | ji(z-caron) | keep | same word, "already"; wikt: no cs entry for the flat form |
    | nez | ne(z-caron) | keep | same word, "than"; wikt: no cs entry for the flat form |
    | ktery | kter(y-acute) | keep | same word, "which (m.)"; wikt: no cs entry for the flat form |
    | ktere | kter(e-acute) | keep | same word, "which"; wikt: no cs entry for the flat form |
    | ma | m(a-acute) | keep | same word, "has, my"; wikt: no cs entry for the flat form |
    | pri | p(r-caron)i | keep | same word, "at, during"; wikt: no cs entry for the flat form |
    | dalsi | dal(s-caron)(i-acute) | keep | same word, "next, further"; wikt: no cs entry for the flat form |
    | zpet | zp(e-caron)t | keep | same word, "back"; wikt: no cs entry for the flat form |
    | pricemz | p(r-caron)i(c-caron)em(z-caron) | keep | same word, "whereby"; wikt: no cs entry for the flat form |
    | ja | j(a-acute) | keep | same word, "I"; wikt: no cs entry for the flat form |
    | me | m(e-caron) | keep | same word, "me"; wikt: no cs entry for the flat form |
    | tem | t(e-caron)m | keep | same word, "to those"; wikt: no cs entry for the flat form |
    | temu | t(e-caron)mu | keep | same word, "to that (archaic)"; wikt: no cs entry for the flat form |
    | nemu | n(e-caron)mu | keep | same word, "to him"; wikt: no cs entry for the flat form |
    | nemuz | n(e-caron)mu(z-caron) | keep | same word, "to which"; wikt: no cs entry for the flat form |
    | jehoz | jeho(z-caron) | keep | same word, "whose"; wikt: no cs entry for the flat form |
    | jelikoz | jeliko(z-caron) | keep | same word, "since, because"; wikt: no cs entry for the flat form |
    | jez | je(z-caron) | exception | "which (relative)"; flat form is the noun jez, weir (wikt), a plain content word |
    | jakoz | jako(z-caron) | keep | same word, "as well as"; wikt: no cs entry for the flat form |
    | nacez | na(c-caron)e(z-caron) | keep | same word, "whereupon"; wikt: no cs entry for the flat form |

**The list digest is not a version mark, and it may never become one.** The
digest of ``CZECH_STOPWORDS_FOLDED`` stands in
``backend/tests/test_czech_analyzer.py`` as ``CZECH_FOLDED_SHA256`` and nowhere
else. In ``expected_versions()`` of :mod:`findling.index.open` it would be an
eighth mark that exists on no installation in the field, and
``Store.version_mismatch`` reads a missing mark as a difference. A later change
of this list moves the tokenisation of every body_cs field already written, so
it needs its own mark decision first (raise ANALYZER_VERSION or add a mark);
pulling the test constant alone is never enough.
"""

from typing import Final

CZECH_EXCEPTIONS: Final[tuple[str, ...]] = (
    "byt",
    "jez",
)

CZECH_STOPWORDS_FOLDED: Final[tuple[str, ...]] = (
    "a",
    "s",
    "k",
    "o",
    "i",
    "u",
    "v",
    "z",
    "dnes",
    "cz",
    "timto",
    "budes",
    "budem",
    "byli",
    "jses",
    "muj",
    "svym",
    "ta",
    "tomto",
    "tohle",
    "tuto",
    "tyto",
    "jej",
    "zda",
    "proc",
    "mate",
    "tato",
    "kam",
    "tohoto",
    "kdo",
    "kteri",
    "mi",
    "nam",
    "tom",
    "tomuto",
    "mit",
    "nic",
    "proto",
    "kterou",
    "byla",
    "toho",
    "protoze",
    "asi",
    "ho",
    "nasi",
    "napiste",
    "re",
    "coz",
    "tim",
    "takze",
    "svych",
    "jeji",
    "svymi",
    "jste",
    "aj",
    "tu",
    "tedy",
    "teto",
    "bylo",
    "kde",
    "ke",
    "prave",
    "ji",
    "nad",
    "nejsou",
    "ci",
    "pod",
    "tema",
    "mezi",
    "pres",
    "ty",
    "pak",
    "vam",
    "ani",
    "kdyz",
    "vsak",
    "neg",
    "jsem",
    "tento",
    "clanku",
    "clanky",
    "aby",
    "jsme",
    "pred",
    "pta",
    "jejich",
    "byl",
    "jeste",
    "az",
    "bez",
    "take",
    "pouze",
    "prvni",
    "vase",
    "ktera",
    "nas",
    "novy",
    "tipy",
    "pokud",
    "muze",
    "strana",
    "jeho",
    "sve",
    "jine",
    "zpravy",
    "nove",
    "neni",
    "vas",
    "jen",
    "podle",
    "zde",
    "uz",
    "vice",
    "bude",
    "jiz",
    "nez",
    "ktery",
    "by",
    "ktere",
    "co",
    "nebo",
    "ten",
    "tak",
    "ma",
    "pri",
    "od",
    "po",
    "jsou",
    "jak",
    "dalsi",
    "ale",
    "si",
    "se",
    "ve",
    "to",
    "jako",
    "za",
    "zpet",
    "ze",
    "do",
    "pro",
    "je",
    "na",
    "atd",
    "atp",
    "jakmile",
    "pricemz",
    "ja",
    "on",
    "ona",
    "ono",
    "oni",
    "ony",
    "my",
    "vy",
    "me",
    "mne",
    "jemu",
    "tomu",
    "tem",
    "temu",
    "nemu",
    "nemuz",
    "jehoz",
    "jelikoz",
    "jakoz",
    "nacez",
)
