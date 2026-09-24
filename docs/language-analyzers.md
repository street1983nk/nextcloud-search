# The Snowball analysis chains

This page describes the analysis chains of the five languages that come out of
one factory: Spanish, Italian, Dutch, Portuguese and, because it is the same
factory, English. German is the reasoned exception and has a page of its own in
`docs/german-analyzer.md`: it carries a compound splitter and no folding filter,
and neither of those decisions survives being copied here.

Everything below was measured rather than reasoned about. The run is
`docs/measurements/2026-09-analyseketten/` of 2026-09-23, rerun on 2026-09-24
after one Italian inflection family entered the fixture (section 9 of that
report), and every number on this page can be traced to a line of
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

**The schema mark of an unchanged installation stays at 1, and that is the
upgrade working.** The tantivy schema went from nine fields to thirteen with
1.3.0, so `findling.config.SCHEMA_VERSION` is 2, while the mark in the state
database of an installation that upgraded still says 1. It says the truth: the
directory on disk was written under the old layout, the container reads that
layout back when it opens the index, and the mark is rewritten only once a
rebuild has really produced a new directory. Every field a search names exists
in both layouts, so nothing is lost in the meantime, and the four body fields
the old layout lacks stay empty until a language outside `de,en` is switched on,
which is a difference of the language mark and starts the rebuild by itself. A
container that treated the stored 1 as a difference would raise the reindex
banner on every installation in the field and read every document again for
nothing; since 2026-09-24 it does not (`findling.store.repo._schema_is_legacy`).
The mark moves to 2 at the end of the rebuild and at no earlier moment, so an
admin who sees 1 on the status page after an upgrade is looking at an
installation that was left alone, not at one that failed to migrate.

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

**The index directory may not be a symbolic link.** Laying the index on a bigger
volume is a legitimate thing to do, and the way to do it is
`APP_PERSISTENT_STORAGE`, which points the whole volume of the container at that
disk. A symbolic link under the name `index` is the other way, and since
2026-09-24 the rebuild refuses it and says so in one line instead of running.
Three things go wrong on a linked directory and none of them can be repaired
from inside the run: the space check measures the file system the link points
at while the second directory is created next to the link, so it checks the
wrong disk; the swap renames the link out of the way and puts a real directory
in its place, so the index moves onto the parent volume without anybody asking;
and the removal behind the swap refuses a link outright, so the version marks
are never written and the whole run starts again at every container start. The
refusal costs the new chains until the link is replaced; nothing is created,
nothing is renamed and the search goes on answering out of the directory that is
there.

## What a question searches

A search line without a field name runs against the body fields of the languages
the index directory carries in its own stored language mark, and against the file
name and the title. Which fields those are and what each of them weighs is one
value, a `FieldPlan`, and `findling.api.resources.field_plan_for` computes it once
per opening of the reading half out of exactly two marks of that directory.

Four things are worth knowing about that.

**The mark of the directory decides, not the variable of the container.**
`FINDLING_LANGUAGES` is the wish of the container that happens to be running, the
`languages` mark is what the directory was really built with, and a question can
only be answered out of what was written. The two differ for as long as a rebuild
takes: whoever switches a language on searches in it once the rebuild is through
and not a moment earlier. That is not a delay somebody forgot to remove. It is
the only reading that cannot name a field the index does not carry, and naming a
field the index does not carry is the `ValueError` that leaves the search bar of
a live installation empty (measurement M-1 of the phase 19 research).

**The field list hangs on `schema_version`, and that gate falls closed.** If the
schema mark of the directory does not stand on the current generation, a question
searches exactly the fields every release up to 1.2.0 carried: `body_de`,
`body_en`, the file name and the title, held as
`findling.query.rewrite.LEGACY_PLAN`. Anything that is not literally the current
mark is read that way, which covers an absent mark, the intermediate `1` of every
installation that has not rebuilt yet, and any generation this code has never
seen. A state that cannot be read is no permission. Behind the marks the same
gate stands a second time: one `doc_freq(field, "")` per body field asks the
directory itself whether the field the mark promises is really in it, and one
field that raises drops the whole plan back to the legacy one, because half a
plan is not a plan. A `state.db` restored from a backup next to an older index
directory is exactly the shape that probe is there for.

**There is no language detection, neither of the document nor of the question.**
The field plan is the reason none is needed: the question runs through all active
fields and each of them analyses it with its own chain, so a Spanish word meets
the Spanish chain without anybody having to decide that it is Spanish. What
orders the results is the field boost, `body_de` 1.0, `body_en` 0.8 and the four
languages of this build out 0.6, so the new chains rank below English rather than
beside it. The absence is structural rather than a matter of discipline:
`field_plan_for` takes no search text in any shape, so a detector is not
forbidden here, it has nothing to attach to
(`backend/tests/test_no_language_detection.py`).

**A question of one word is answered out of the word index alone.** The search is
hybrid, and `findling.api.search` builds no vector half for a single word at all
(`lexical_only`, the one term rule of plan 06.1-20). Two things follow. A one
word question shows the plain field behaviour described above, while a longer one
shows the fused behaviour of both halves. And the before and after proof of the
upgrade path rests on exactly that condition: the CI step that asks `alemanes`
against a Spanish document and demands nothing before the rebuild and one hit
after it is a statement about body fields only while the question stays one word.
With two words the vector half joins in, the Spanish document is a near neighbour
of the question whatever the fields say, measured at 68 to 77 on the int8 L2
scale against an upper bound of 86.5
(`docs/measurements/2026-09-06-vektordistanzen`), and the proof would turn into a
statement about distances without saying so.

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

Measured on 2026-09-23 and rerun on 2026-09-24 with
`scripts/dev/measure_chains.sh`, which runs `scripts/dev/chain_probe.py`. The
Italian row and the totals are the ones of the rerun; every other number is the
one of 2026-09-23, unmoved. No container is involved: all four Snowball stop
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
| it | 15 | 60 | **60** | 58 |
| nl | 13 | 81 | **57** | 57 |
| pt | 18 | 228 | **180** | 174 |
| **Together** | **66** | **577** | **471** | **467** |

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

Two numbers of phase 19 belong here as well. They come out of runs of their own,
so each of them carries its own date and its own harness.

**The boost at which the ranking turns over: 0.81.** Measured on 2026-09-24
against tantivy 0.26.2 by the ranking probe
`backend/tests/test_field_plan_ranking.py`, a sweep over 101 values on a real
index of three documents with six filled body fields. Below that value the better
English hit stays in front of a document that meets the same question through
three additional chains; from it on the ranking turns over. The shipped weight of
the four new body fields is 0.6, so it stands 0.21 below the measured edge, which
is why plan 19-04 moved no weight. The figure is the input for the
`disjunction_max` decision of phase 22 (MESS-09), and it is worth exactly what it
says and no more: tantivy adds the field contributions up (measurement M-3 of the
phase 19 research), so a boost damps a multi field hit and never removes it, and
an index with more filled body fields moves the edge.

**The cost of the field plan: one `read_meta()` plus one `doc_freq` probe per
body field, at 0.26 us a call.** Measurement M-2 of the phase 19 research,
2026-09-24, 20000 runs against tantivy 0.26.2, next to 2.26 us for
`parse_query_lenient` on the same index. It is paid once per opening of the
reading half and never once per question, which is the whole reason the field
plan hangs on `ReadSide` and carries no cache of its own.

## The filter order

```text
simple -> lowercase -> ascii_fold -> stopword(lang)
       -> custom_stopword(folded) -> remove_long(48) -> stemmer(lang)
```

| Position | Filter | Why exactly here |
|---|---|---|
| 1 | `lowercase` | Everything after it compares strings exactly, and both stop word lists are lowercase |
| 2 | `ascii_fold` | In front of the stop word list and thereby in front of the stemmer. Measured 471 of 577 ordered pairs against 467 for a late fold, and it is the only position that is tight in both spellings |
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

**A hit found through a new language field alone comes back without an excerpt.**
Measured on 2026-09-24 (measurement M-4 of the phase 19 research): an index with
`body_de`, `body_en` and `body_es`, one document carrying "Esta es una carta de la
empresa alemana sobre el contrato de arrendamiento." in all three fields, and the
question `alemanes` over the full field plan. It is one hit, and
`SnippetGenerator.create(..., FIELD_BODY_DE)` (`index/search.py:875`) answers with
`fragment() == ''` and no highlight at all, while the control question `contrato`,
which the German chain meets as a raw token, returns the full fragment. The reason
is that `body_de` is the only stored copy of the extracted text, so a question that
meets the document term through the Spanish chain alone has nothing to mark in the
German one. The hit itself is not lost: "a hit without a snippet is still a hit,
and the subline falls back to the path on the PHP side", as the docstring of that
function puts it, and the companion does exactly that. The alternative is an
excerpt path per body field, which means six stored copies of every text instead
of one, and the price is the size of the index on the machines this product is
built for. Because of that price the limit is documented rather than repaired, and
it is one of the entries phase 23 writes into the documentation and the store text
(REL-03 criterion 2).

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
