# The Dutch analysis chain

Dutch is the second compounding language Findling searches, and since phase 21
it gets its own constituent list and its own splitter. This page records the
list, the recipe, the filter order, the version mark and the limits, all of them
measured, so that a later change has something to argue against. It follows the
layout of `docs/german-analyzer.md`, and every number on it comes from
`docs/measurements/2026-09-komposita-nl/`.

The splitter is only active when `nl` is part of `FINDLING_LANGUAGES`. Without
`nl`, the Dutch field keeps the plain Snowball chain of phase 17: no list is
read, no automaton is built, no memory is paid.

## The constituent list

| Property | Value |
|---|---|
| Debian package | `wdutch` `1:2.20.19+1-3`, `Architecture: all`, pinned with its epoch in `backend/Dockerfile` |
| Upstream | OpenTaal |
| File in the image | `/usr/share/dict/dutch`, 413288 lines |
| Installed by | `apt-get install`, never downloaded at runtime; the image build fails closed if the list or its licence text is missing |
| Preparation code | `backend/src/findling/index/wordlist_nl.py` |

### Recipe B 4-14, the one in the code

Fold every line of the source through a tantivy analyzer
`simple -> lowercase -> ascii_fold` (exactly one token per line, no second fold
in Python), keep it only if it is alphabetic and between `MIN_LEN = 4` and
`MAX_LEN = 14` characters long before folding, and add the three linking
elements `s`, `e` and `en` (`TUSSENKLANKEN`) as entries of their own. Unlike the
German list, the Dutch list **is folded**: `coördinatiecentrum` and a user's flat
`coordinatiecentrum` meet the same entries.

The folded list is written as an artifact `dict/nl-full.txt` plus
`nl-full.txt.sha256` on the app's own volume. A tampered or truncated artifact
fails closed. Only the digest is cached per process, never the entries.

### Recipes that were measured and rejected

Excerpt of the eleven variants of the phase research; the full table stands in
the module docstring of `wordlist_nl.py` and in section 2 of the measurement
report.

| Recipe | Window | List | Split position | Entries | Compounds found through a part | Guards kept whole |
|---|---|---|---|---|---|---|
| no splitter (the phase 17 chain) | n/a | n/a | n/a | n/a | 0 of 28 | n/a |
| A 4-14 | 4 to 14 | raw | before the fold | 317320 | 20 of 28 | 32 of 33 |
| A 4-12 | 4 to 12 | raw | before the fold | 257766 | 24 of 28 | 31 of 33 |
| **B 4-14** | **4 to 14** | **folded** | **behind the fold** | **316740** | **21 of 28** | **32 of 33** |
| B 4-12 | 4 to 12 | folded | behind the fold | 257194 | 25 of 28 | 31 of 33 |
| B 4-16 | 4 to 16 | folded | behind the fold | 352737 | 16 of 28 | 33 of 33 |

Recipe B 4-14 was chosen by the owner on 2026-09-25 (D-03). The windows 4-12
and 4-13 find more, but they split `onderhandelingen` into `onderhandel, ing`,
a junk term in the index and the same pattern that rejected German recipe D.

## Measured numbers

Measured with `scripts/dev/measure_compounds_nl.sh` in a throwaway
`python:3.13-slim-trixie` container with `tantivy==0.26.2`, the pin of
`backend/pyproject.toml`. The probe `scripts/dev/compound_probe_nl.py` calls the
shipped functions and builds no chain of its own.

| Number | Value |
|---|---|
| Lines of `/usr/share/dict/dutch` | 413288 |
| Entries after recipe B 4-14 | **316740** |
| SHA-256 of the filtered list | `ee7f3b8380c752835692db8fbf1350786955d4fca13e94506812a23eece107a2` |
| Compounds found through a part, of 28 | **21** |
| Compounds found through a part without the splitter | **0** |
| Guards that stay one token, of 33 | **32** (`belastingplichtige` becomes `belast, plichtig`, a real compound) |
| Phase 17 form families where the splitter chain differs from the Snowball chain | 0 of 13 |
| Read, filter and build | 0.74 to 0.78 s |

The case list is `backend/tests/fixtures/compound_cases_nl.txt`, the tokens of
every case stand in `rohdaten/tokens-rezept-b.tsv`, and the table tests in
`backend/tests/test_dutch_analyzer.py` assert them line for line in both
directions. The test fixture `backend/tests/fixtures/constituents_nl.txt` carries
359 entries and was measured to tokenise all 101 words of both case files
exactly like the full list.

## The filter order

```text
simple -> lowercase -> ascii_fold -> split_compound(list)
       -> custom_stopword(TUSSENKLANKEN) -> stopword("dutch")
       -> custom_stopword(folded Dutch stop words) -> remove_long(48)
       -> stemmer("dutch")
```

| Position | Filter | Why exactly here |
|---|---|---|
| 1 | `lowercase` | Everything after this compares strings exactly, and the list is lowercase |
| 2 | `ascii_fold` | **In front of** the splitter (D-07). The list is folded, so the token must be too; otherwise `coördinatiecentrum` and `coordinatiecentrum` split differently |
| 3 | `split_compound` | Needs the unstemmed token; a stemmed compound no longer matches any entry |
| 4 | `custom_stopword(TUSSENKLANKEN)` | Without it a bare `s`, `e` or `en` lands in the index |
| 5 | `stopword("dutch")` | The built in Snowball list, as in the phase 17 chain |
| 6 | `custom_stopword(...)` | The folded supplement of the Dutch stop words, as in the phase 17 chain |
| 7 | `remove_long(48)` | **After** the splitter, so a long compound is split before it could be dropped whole |
| 8 | `stemmer("dutch")` | Last |

This is the opposite of the German decision. The German list keeps its umlauts
and the German chain has no fold, because the Snowball stemmer folds by itself
and a folded token would not match the list. The Dutch list is folded on
purpose, so the fold has to come first. Measured: with the splitter in front of
the fold (recipe A), the flat spelling of a user who does not type the diaeresis
stays whole.

The chain is built by `dutch_analyzer` in `backend/src/findling/index/analyzer.py`,
once per process (`cached_dutch_analyzer`, counted by `dutch_build_count`), and
chosen by `dutch_chain_for(digest)`: with a digest it is the splitter chain,
without one (`nl` not active) it is the unchanged `snowball_analyzer("dutch")`.
The registration under the nl tokenizer name is unconditional; only the chain
behind it changes. An AST test pins the order and the arguments of both
`custom_stopword` filters.

The German list is never applied to Dutch text. It would produce wrong splits
rather than missing ones, and a wrong split is harder to notice than an unsplit
word.

## The version mark `wordlist_hash_nl`

A list or a chain change alters the terms of `body_nl`, and an index built with
the old terms silently disagrees with the query parser. The seventh version mark
records which Dutch chain wrote the index.

| Property | Value |
|---|---|
| Name | `wordlist_hash_nl` (`DUTCH_MARK` in `findling.index.open`) |
| Value without `nl` | `off` |
| Value with `nl` | `<DUTCH_CHAIN_VERSION>:<digest>`, today `1:ee7f3b83...` |
| Seeded into a new store | **no**; like the languages mark it is written only behind a newly built directory or behind a rebuild swap |
| Absent mark, expected `off` | legacy, **no drift**: no build before phase 21 split `body_nl` with a list (`_dutch_list_is_legacy` in `store/repo.py`) |
| Absent mark, expected a digest | drift |
| Written `off`, empty value, different digest | compared as written; a difference is drift |
| Reported as | `wordlistHashNl` in the index status report |

The mark causes a rebuild when `nl` is switched on, when the list changes under
an active `nl` (a new Debian pin, a new window) and when `nl` is switched off
again. An installation without `nl` expects `off`, finds the mark absent, and
sees no banner and no run; this is the D-09 promise and the CI step "Store
upgrade 5" asserts it after every push.

`ANALYZER_VERSION` does **not** rise for Dutch (D-05). Raising it would move
every installation into a full reindex of roughly 19 hours on the reference box,
including the ones that never enable `nl`. The Dutch mark is the named exception
to the rule that a changed tokenisation raises `ANALYZER_VERSION`; the module
docstring of `analyzer.py` says so. In return, `DUTCH_CHAIN_VERSION` in
`wordlist_nl.py` **must** rise with every change to the Dutch chain itself
(filter, order, arguments), because the digest only covers the list.

## The rebuild path

A Dutch drift is answered by the band rebuild (`findling.index.rebuild`), the
same path as a language switch: `DUTCH_MARK` stands in
`MARKS_A_REBUILD_ANSWERS`. The rebuild re-analyses the stored text of every
document through the target chains into a second directory and swaps it in.
There is **no download, no OCR and no new embedding**. `stamp_after_swap` writes
the mark behind the swap and takes it as a keyword-only argument without a
default, so no caller can stamp a value it did not build.

Since plan 21-01 a drift the band rebuild answers no longer raises the
generation when the poller opens its state. Before that fix, switching on `nl`
would have forced a full crawl as a side effect.

### The limit of the full reindex way out (D-08)

`FINDLING_REBUILD_FALLBACK=fullreindex` is the named way out for a volume that
cannot hold a second directory. Measured in plan 21-01 and asserted by
`test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were` in
`backend/tests/test_index_rebuild.py`: under this way out the marks of a
directory are **not** stamped. After the generation was raised, the crawl ran
through and `stamp_after_rebuild` ran, `languages` still carries its old value,
`wordlist_hash_nl` still carries its old value, and `version_mismatch` still
names both. `stamp_after_rebuild` does clear the rebuild mark, so the next start
falls into the way out again and raises the generation once more.

Under `fullreindex`, switching `nl` on or changing the Dutch list therefore
costs one full crawl per container start until the setting is taken back or the
band rebuild is allowed. The band rebuild is the regular answer and stamps the
mark correctly.

## The seven named limits

Of the 28 compounds of the case list, seven cannot be found through their part.

**Six compounds stand in the list themselves.** The splitter matches
leftmost-longest and never splits an entry.

| Compound | Token | Part that finds nothing |
|---|---|---|
| `bouwvergunning` | `bouwvergunn` | `vergunning` |
| `huurtoeslag` | `huurtoeslag` | `toeslag` |
| `verkeersboete` | `verkeersboet` | `boete` |
| `jaarrekening` | `jaarreken` | `rekening` |
| `factuurnummer` | `factuurnummer` | `nummer` |
| `opzegtermijn` | `opzegtermijn` | `termijn` |

These are short, frequent everyday compounds, and they are findable only under
their whole word, exactly as without the splitter. This is the same property the
German recipe A has.

**`onroerendezaakbelasting` fails at `zaakbelasting`.** It becomes
`onroer, zaakbelast`: `zaakbelasting` is itself an entry, the longer match wins,
and `belast` never appears. A search for `belasting` does not find it.

All seven stand in the table tests with their measured tokens, so a list change
that makes one of them splittable has to say so out loud.

**Recipe B pays two short stems for its recall.** `huurovereenkomst` produces
`hur, overeenkomst` and `koopovereenkomst` produces `kop, overeenkomst`: the
Snowball stemmer shortens the first part after the split. The query side runs
the same chain, so `huur` still finds the document; the stems are recorded here
because they look like errors in a term listing.

## What splitting costs at ranking time

As in German, a successful split throws the original token away:
`gemeentebelastingen` stands in the index as `gemeent, belast` only. A search
for the whole word works as a conjunction over the parts, because the query side
produces the same parts, and a document that happens to carry the parts in
unrelated places competes with the one that carries the compound. The section of
the same name in `docs/german-analyzer.md` explains the trade.

## Memory

The Dutch automaton is built once per process and only when `nl` is active.
Measured in section 4 of `docs/measurements/2026-09-komposita-nl/`, product
near, behind a built German automaton, with the Dutch list released: **24.2 to
25.3 MB** of resident memory the process keeps (amd64). The automaton alone is
15 to 16 MB; the rest is freed heap glibc does not return. The budget
calculation against the 2,000 MB limit stands in `docs/performance.md`, section
"Nachtrag vom 25.09.2026: der niederländische Automat". The native ARM figure is
measured again in phase 22.

## Licence and provenance

The word list is `/usr/share/dict/dutch` from the Debian package `wdutch`,
upstream OpenTaal, word list files licensed **CC-BY-3.0** according to
`debian/copyright` (`Files: wordlist/*`). The licence text ships in the image as
`/usr/local/share/findling/COPYING.wdutch`, the CI gate on the pushed image
checks it, and `THIRD-PARTY.md` carries the attribution to OpenTaal.

## Reservation A4

No native speaker has read the cases (as of 2026-09-25). The compounds and
their parts come from administrative vocabulary, the tokens are measured, and
the question whether a Dutch user would search this way is open.
