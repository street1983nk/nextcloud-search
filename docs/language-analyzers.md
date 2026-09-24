# The Snowball analysis chains

This page describes the analysis chains of the five languages that come out of
one factory: Spanish, Italian, Dutch, Portuguese and, because it is the same
factory, English. German is the reasoned exception and has a page of its own in
`docs/german-analyzer.md`: it carries a compound splitter and no folding filter,
and neither of those decisions survives being copied here.

Everything below was measured rather than reasoned about. The run is
`docs/measurements/2026-09-analyseketten/` of 2026-09-23, and every number on
this page can be traced to a line of
`docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt`.

## Switching a language on, and when it takes effect

`FINDLING_LANGUAGES` takes a comma separated list out of `de`, `en`, `es`, `it`,
`nl` and `pt`, and the factory setting is `de,en`. Since plan 18-02 the value is
filtered against the set this build has a body field and a chain for, so all six
codes are real choices and none of them falls out in silence. The order you type
does not matter: the resolved set is always in schema field order, so `es,de` and
`de,es` are the same setting and neither of them rebuilds an index the other one
would have left alone. An empty or unknown value keeps `de,en` and logs a warning
that names the variable and never its value.

Two things are worth knowing before the variable is touched.

**The change takes effect when the container restarts, not when the value is
saved.** `findling.config.settings()` is resolved once per process and cached,
and the drift check that starts the rebuild sits in the start path of the poller.
A running container therefore keeps working on the set it started with. This is
the same behaviour every other `FINDLING_` variable has, it is not a defect, and
it is written here so that an admin who edits the value and watches nothing
happen knows that the restart is the missing step and not a broken setting.

**The upgrade to 1.3.0 leaves an unchanged installation alone, with one named
gap.** Since 2026-09-24 the language set is a version mark of its own (owner
decision E-17-4 option a). An installation coming from 1.2.0 carries no such
mark yet, and its absence is read as the pair `de,en` rather than as a
difference, because no release up to 1.2.0 could build a body field outside that
pair. So an installation on the factory setting and an installation pinned to
`de` both upgrade without a rebuild, while switching `es`, `it`, `nl` or `pt` on
is a difference and starts one. The gap this leaves open on purpose: an
installation running `de` alone that switches `en` on at the same upgrade gets no
rebuild either, because `de,en` is still inside the pair. That is the behaviour
of 1.2.0, where no mark exists at all, so nothing gets worse; it closes itself
the first time any other mark moves, because the first stamp writes the language
mark and from then on it is compared like every other one.

**The body languages and the OCR languages are two settings, and they are set
separately.** `FINDLING_LANGUAGES` decides which analysis chains an index
carries: `de`, `en`, `es`, `it`, `nl`, `pt`, factory setting `de,en`.
`FINDLING_OCR_LANGUAGES` decides which models tesseract loads when it reads a
scan: `deu`, `eng`, `fra`, `spa`, `ita`, `nld`, `por`, `dan`, `est`, factory
setting `deu+eng+fra`. Neither follows the other, and that is deliberate: an
instance with born digital Spanish documents needs the Spanish chain and no
Spanish scanner, and an instance that scans French post needs the French scanner
while French has no chain in this build at all.

The combination that goes wrong quietly is the other one: a body language whose
scanner is missing. Tesseract does not refuse a page in a language it was not
asked for, it reads it with the wrong model and returns plausible looking
rubbish, and that rubbish is extracted, indexed and searchable while nothing
says the document was never readable. Since 2026-09-24 the container says one
line about it at startup, it names the count and not the codes, and it refuses
nothing: an instance without scans is not broken by the combination. The names
of the uncovered languages are on the admin page.

Switching Spanish on therefore means two variables, not one:
`FINDLING_LANGUAGES=de,en,es` and `FINDLING_OCR_LANGUAGES=deu+eng+spa`. Every
additional OCR language loads another traineddata and makes every scanned page
slower, so the list stays as short as the documents on that instance allow.

**`body_de` is stored whatever the set says.** It is the only stored copy of the
extracted text in the whole system and the snippet generator cuts out of it, so
an instance running on `es` alone still writes it. Being stored and being
analysed by the German chain are two properties of that one field, and only the
second one follows the language set.

## The supplement list

The built in Snowball stop word lists compare strings exactly and they carry
real accents. The chain folds before it filters, so once the fold has run, an
accented entry never matches again and the flat form it folded into stands in no
list at all. The supplement closes that hole, and nothing else.

| Property | Value |
|---|---|
| Source | `quickwit-oss/tantivy`, tag 0.26.2, `src/tokenizer/stop_word_filter/stopwords.rs` |
| Licence of the source | BSD-3-Clause |
| Generated by | `scripts/dev/stopword_supplement.py`, never edited by hand |
| Shipped in | `backend/src/findling/index/stopwords.py`, as `FOLDED_STOPWORDS` |
| Built in list sizes of that tag | spanish 308, italian 279, portuguese 203, dutch 101, together 891 |

| Language | Supplement entries |
|---|---:|
| Spanish | 77 |
| Italian | 10 |
| Portuguese | 30 |
| Dutch | 0 |
| English | 0 |
| **Together** | **117** |

SHA-256 of the flattened list, in sorted language order:
`d056d4597f989c7e03113c529c92cef980254f72c4d4e5deace4588ea033311a`.

**This digest is not a version mark and it may never become one.** It describes
the supplement and it lives in `backend/tests/test_language_analyzers.py` as
`FOLDED_SUPPLEMENT_SHA256`. It must not reach `expected_versions()` of
`findling.index.open`: there it would be a sixth mark, a sixth mark exists on no
installation in the field, and `Store.version_mismatch` reads a missing mark as
a difference. Every stock installation would then reindex, measured at 19 h 20
min, for a constant that changes the tokenisation of no index already written.

Dutch and English have no accented entry in their built in list, so their
supplement is empty, and an empty `custom_stopword` filter is measured to be a
no-op over thirteen test words. That is the reason one factory can serve English
without moving the English tokenisation by a single byte.

## Measured numbers

Measured on 2026-09-23 with `scripts/dev/measure_chains.sh`, which runs
`scripts/dev/chain_probe.py`. No container is involved: all four Snowball stop
word lists and all four stemmers are compiled into tantivy, so `uv run` from
`backend/` is the whole harness. The full report is in
`docs/measurements/2026-09-analyseketten/`.

The metric counts form families. For every lemma, all spellings a human may type
or a document may carry, accented and flat, singular and plural, and counted are
the ordered pairs (typed form, form in the document) that share at least one
term. One hundred percent means every spelling finds every other one.

| Language | Families | Ordered pairs | `fold early` (A+) | `fold late` (C+) |
|---|---:|---:|---:|---:|
| es | 20 | 208 | **174** | 178 |
| it | 14 | 56 | **56** | 54 |
| nl | 13 | 81 | **57** | 57 |
| pt | 18 | 228 | **180** | 174 |
| **Together** | **65** | **573** | **467** | **463** |

Stop word leaks, counted as words of the built in list that still produce a term,
accented spelling and flat spelling separately:

| Language | Shipped chain (A+) | Same chain without the supplement (A) |
|---|---|---|
| es | **0 / 0** | 77 / 77 |
| it | **0 / 0** | 10 / 10 |
| nl | **0 / 0** | 0 / 0 |
| pt | **0 / 0** | 30 / 30 |

The supplement is therefore not a nicety. Without it, 117 published stop words
stand in the index as ordinary terms, in both spellings, and that is the one
result of the measurement that needed no trade-off at all.

## The filter order

```text
simple -> lowercase -> ascii_fold -> stopword(lang)
       -> custom_stopword(folded) -> remove_long(48) -> stemmer(lang)
```

| Position | Filter | Why exactly here |
|---|---|---|
| 1 | `lowercase` | Everything after it compares strings exactly, and both stop word lists are lowercase |
| 2 | `ascii_fold` | In front of the stop word list and thereby in front of the stemmer. Measured 467 of 573 ordered pairs against 463 for a late fold, and it is the only position that is tight in both spellings |
| 3 | `stopword(lang)` | The built in Snowball list of the language, which compares exactly and carries real accents |
| 4 | `custom_stopword(folded)` | Directly behind it, because the fold has just made the built in list miss its own accented entries. Without it 77 Spanish, 10 Italian and 30 Portuguese stop words reach the index |
| 5 | `remove_long(48)` | The same limit as every other chain. Nothing splits here, so there is no splitter it would have to stand behind |
| 6 | `stemmer(lang)` | Last, as in every chain of this project |

**Why these four chains fold at all, and why at the front.** The German chain has
no folding filter, because the German Snowball stemmer folds umlauts and sharp s
by itself and because folding would devalue the constituent list. Spanish,
Italian, Dutch and Portuguese are the opposite case: their stemmers do not fold,
so without the filter the accented and the flat spelling of the same word become
two terms, and a user who does not type accents finds nothing. The product also
reads OCR, and a scan that lost its accents is a document that has to remain
findable under the correct spelling.

The alternative was measured and it is `fold late`, the chain that folds behind
the stemmer. It wins in Spanish by 4 of 208 ordered pairs, 1.9 points, and in a
second independent Spanish sample by 4 of 137, 2.9 points. It loses in Italian by
2 of 56, in Portuguese by 6 of 228, and it is level in Dutch. Four reasons
decided the uniform chain against that small Spanish lead:

1. The Spanish lead rests on exactly one word class, the accented Snowball
   ending, and the orphan does not disappear under either chain. It only moves:
   with `fold early` the correctly spelled plural is the orphan, with `fold late`
   the flatly typed singular.
2. `fold early` is the shape of the already shipped English chain, so one factory
   serves five languages instead of two factories with opposite orders.
3. The product reads OCR, and `fold late` gives up exactly the direction a scan
   needs.
4. `fold late` writes terms into the index that no question can reach. Measured
   on `één`: the shipped chain drops the word, the late fold stores `een` while
   the same query falls as a stop word on the question side.

Two candidates were measured and dropped. Folding twice, once in front and once
behind the stemmer, is token for token identical with the shipped chain in every
language and every word, so the second fold is dead weight. Folding between the
stop word filter and the stemmer scores the same as the shipped chain in the
family metric and differs only on the Dutch stress accents, where it is the
dirtier of the two.

None of these chains carries a word list, so none of them owns an automaton and
none of them costs resident memory worth budgeting. That is the whole reason
`snowball_analyzer` is not a cached singleton while `german_analyzer` has to be
one.

## The merged test table

The verdict per case, measured on 2026-09-23 under the shipped chain. Every row
is held by `backend/tests/test_language_analyzers.py`: rows 1, 3, 5, 6, 13, 14
and 15 as "same term", rows 7, 8 and 9 as "no token at all", rows 2 and 4 as a
loss with the exact measured terms, and rows 10 to 12 by the density gate, which
runs all 891 built in entries of the four languages in both spellings.

| # | Case | Source | Result under the shipped chain | green |
|---|---|---|---|---|
| 1 | `información` / `informacion` | STACK, LEX-01 | both `informacion` | yes |
| 2 | `información` / `informaciones` | PITFALLS, LEX-01 | `informacion` against `inform` | **no, documented loss** |
| 3 | `informação` / `informacao` | STACK, LEX-01 | both `informaca` | yes |
| 4 | `informação` / `informações` | PITFALLS, LEX-01 | `informaca` against `informaco` | **no, in every chain** |
| 5 | `informações` / `informacoes` | STACK | both `informaco` | yes |
| 6 | `año` / `ano` | PITFALLS, LEX-01 | both `ano`, a bought recall | yes |
| 7 | `perché` as a stop word, both spellings | FEATURES, PITFALLS, LEX-01 | both empty | yes |
| 8 | `più` as a stop word, both spellings | PITFALLS | both empty | yes |
| 9 | `één` / `een` | FEATURES, LEX-01 | both empty, no rubbish token | yes |
| 10 | accented Spanish stop words, all of them | FEATURES, LEX-01 | 0 leaks, accented and flat | yes |
| 11 | accented Portuguese stop words, all of them | FEATURES, LEX-01 | 0 leaks | yes |
| 12 | accented Italian stop words, all of them | FEATURES | 0 leaks | yes |
| 13 | `qualità` / `qualita` | new from this measurement | both `qual` | yes |
| 14 | `città` / `citta`, `società`, `università` | STACK | same term per pair | yes |
| 15 | `coördinatie` / `coordinatie`, `financiën` / `financien` | FEATURES | same term per pair | yes |

The two red rows are the price of the chain. They are not repairable without
making another row red, and the section below says what each of them costs.

## Known limits

These are measured, documented and deliberately not fixed here. Each one names
the alternative and why the alternative is more expensive.

**The number class with an accented suffix, Spanish.** `información` and
`informacion` share the term `informacion`, and `informaciones` produces
`inform`, so the plural does not meet its own singular. The Spanish Snowball
algorithm carries the ending with the accent in its suffix list and the plural
ending without it, so any fold that unites the two spellings separates the
number pair. The whole `-ción` class is affected: `administración`,
`facturación`, `resolución`, `notificación`. So is `alemán` against `alemanes`
(`alem` against `aleman`) and `capitán` against `capitanes` (`capit` against
`capitan`). The alternative is the late fold, which buys 4 of 208 pairs and
pays with the OCR direction, with Italian and Portuguese, and with terms in the
index that no question reaches. A second alternative would be an own stemmer,
which changes every term of every index and forces a full reindex.

**The number class with an accented suffix, Portuguese.** `informação` produces
`informaca`, `informações` produces `informaco`, and no measured chain brings the
two together, because the stem itself differs before any fold runs.
`administração` against `administrações` is the same case. Here even the late
fold does not help, so the only alternative would be a different stemmer, at the
price named above. The flat spellings behave exactly like the accented ones, so
a document written without accents is no worse off than a correct one.

**`año` equals `ano`, a bought recall.** The fold puts `año` and `ano` on the
term `ano`, so a search for "year" also finds the word for "anus". This is
deliberate. The alternative is to keep the tilde, which would mean no fold at
all in Spanish, and that would cost the accent convergence of the whole `-ción`
class and every OCR document that lost its accents. One ambiguous word against a
language wide loss is not a close call.

**Irregular Spanish plurals.** `ciudad` produces `ciud` and `ciudades` produces
`ciudad`; `joven` produces `jov` and `jóvenes` produces `joven`; `imagen`
produces `imag` and `imágenes` produces `imagen`; `examen` produces `exam` and
`exámenes` produces `examen`. These fall apart in every one of the seven
measured chains, because the stemmer removes a different suffix from the two
forms. The alternative is a synonym or lemma list, which is a second data file
with a second licence acting on every query of every language, and the first
entry always drags a hundred more behind it.

**Dutch plurals with a vowel change.** `huis` produces `huis` and `huizen`
produces `huiz`; `bedrijf` produces `bedrijf` and `bedrijven` produces
`bedrijv`; `gemeente` produces `gemeent` and `gemeentes` produces `gemeentes`.
The Dutch Snowball stemmer does not undo the consonant change, and no fold
position changes that: Dutch scores the same in all seven candidates because its
stemmer already folds by itself. The alternative is again a lemma list, at the
same price as above.

**`café` and `cafés` in Dutch.** `café` produces `caf` and `cafés` produces
`cafes`, so the two do not meet. The same word pair is unproblematic in
Portuguese, where both produce `caf`, which is why this limit is named with its
language and not in general. The alternative would be a Dutch specific rule in
front of the stemmer, and a per language exception rule is the beginning of a
second stemmer.

**No Portuguese orthographic unification.** The chains do not translate between
the spellings of the pre-reform and post-reform orthography, and they do not
unify European and Brazilian variants beyond what the shared stemmer does
anyway. A mapping table would be a data file with its own provenance, its own
maintenance and its own licence, for a class of documents this product has not
measured. The pair that matters most in practice, accented against flat, is
handled by the fold and is asserted in rows 3 and 5 of the table above.

**Compounds are German only.** `Filter.split_compound` runs in the German chain
alone, because it needs a constituent list and the project ships exactly one.
Dutch is the other compounding language in this set and it gets nothing here;
the Dutch constituent list is scheduled for phase 21 and is deliberately not
improvised now. The alternative would be to run the German list against Dutch
text, which produces wrong splits rather than missing ones, and a wrong split is
harder to notice than an unsplit word.

**Five words that fall through every list.** `già`, `però` and `così` in
Italian and `aún` and `sólo` in Spanish are in no built in Snowball list, so
they produce the terms `gia`, `per`, `cos`, `aun` and `sol` in every chain. They
are function words, and seeing them as terms looks like a leak of the density
gate, which is why they are named here: the gate covers the published lists and
these words are not on them. An own stop word list would close it, and that list
would be a product decision rather than a chain problem: it needs a maintainer,
it needs a provenance, it moves the supplement digest, and from the moment it
exists, every later Snowball update has to be compared against it. Five words do
not pay for that.

**Footnote on the length of this page.** The owner rule of 07.09.2026 applies to
store descriptions and READMEs, which are short lists of facts. This file is
`docs/`, where the reasoning belongs, so it is allowed to be long. The short
version for HART-05 is written in phase 23 and is put to the owner before it is
published.

## Licence and provenance

The Snowball stop word lists and the Snowball stemmers are compiled into
tantivy. They are not downloaded, not unpacked at runtime and not shipped as a
separate artifact. tantivy is BSD-3-Clause, which is compatible with the
AGPL-3.0 of this project.

The supplement adds no new word list either. It is derived mechanically from
those same built in lists by `scripts/dev/stopword_supplement.py`, it contains
only folded forms of entries that already exist there, and it is therefore
covered by the same licence and the same provenance. No new PyPI package, no new
data file and no own vocabulary enters the image because of this page.

The preparation and measurement code stays in the repository:
`backend/src/findling/index/analyzer.py`,
`backend/src/findling/index/stopwords.py`, `scripts/dev/stopword_supplement.py`,
`scripts/dev/chain_probe.py` and `scripts/dev/measure_chains.sh`.
