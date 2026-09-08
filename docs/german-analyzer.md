# The German analysis chain

German search quality is the product promise of Findling, and it rests on one
data file and one filter order. Both are counter-intuitive, both were measured,
and this page records what was measured so that a later simplification has
something to argue against.

## The constituent list

| Property | Value |
|---|---|
| Debian package | `wngerman` 20161207-15, `Architecture: all` |
| Source package | `igerman98`, upstream Bjoern Jacke, Debian maintainer Roland Rosenfeld |
| File in the image | `/usr/share/dict/ngerman` |
| Installed by | `apt-get install -y --no-install-recommends wngerman`, never downloaded at runtime |

The list is a *constituent* dictionary, not a spell checker dictionary. The
recipe that turns one into the other is the whole trick.

### Recipe A, the one in the code

Take every word of the source, keep it only if it is alphabetic, lowercase it,
keep it only if it is between `MIN_LEN = 4` and `MAX_LEN = 14` characters long,
and add the six linking elements `s, es, n, en, er, ns` as entries of their own.
The list keeps its umlauts and its sharp s; it is never folded to plain letters.

### Recipes that were measured and rejected

| Recipe | Entries | Of the sixteen long compounds, findable through a part | Mis-splits |
|---|---|---|---|
| **A: all words, window 4 to 14, linking elements as own entries** | **276496** | **14 of 16** | **0** |
| B: nouns only, linking forms appended to each word, folded to plain ASCII | 222708 | 7 of 16 | yes, e.g. `haushaltss` + `atzung` |
| C: nouns only, window 4 to 14 | 86345 | 12 of 16 | 0 |
| D: nouns only, window 4 to 12 | 65693 | 12 of 16 | 0, but over-splits: `betrieb` + `kost` + `abrechn` |

The third column counts the sixteen compounds the phase 2 research measured,
and it is not a rate for German in general. Measured again on a wider set in
`docs/measurements/2026-09-komposita-rezept-a/`: of the **twenty one
administrative compounds of the guard table** in
`backend/tests/test_analyzer.py`, seven do not come apart at all under recipe A.
Those twenty one are the sixteen of the phase 2 research plus five short ones
this phase added: `Baugenehmigung`, `Bauantrag`, `Baukosten`, `Arbeitsvertrag`
and `Steuerbescheid`. They are deliberately **not** the twenty one of section
3.1 of the measurement report, which counts the inputs of that run producing
more than one token and is the same size by coincidence.

"14 of 16" is therefore a statement about the sixteen words of the earlier
research, most of them long and rare; "Known limits" below names the seven that
stay whole, and those are the short, frequent ones.

Recipe B is the one that suggests itself and the measurably worst one. It fails
precisely on the long administrative compounds the whole feature is about.
Recipe C ships as the frugal variant behind `FINDLING_COMPOUND_DICT=nouns`; the
default is `full`.

## Measured numbers

Measured with `scripts/dev/measure_wordlist.sh` in a throwaway
`python:3.13-slim-trixie` container, the same base image the ExApp ships on.

| Number | `full` | `nouns` |
|---|---|---|
| Lines of `/usr/share/dict/ngerman` | 356010 | 356010 |
| Bytes of `/usr/share/dict/ngerman` | 4725887 | 4725887 |
| Entries after filtering | 276496 | 86345 |
| Time to read and filter | 0.251 s | 0.118 s |
| Resident memory of the Python list | 19845120 B (18.9 MiB) | 13688832 B (13.1 MiB) |
| Time to build the automaton | 0.327 s | 0.136 s |
| Resident memory the process keeps | 43454464 B (41.4 MiB) | 7651328 B (7.3 MiB) |
| Throughput | 1781918 tokens/s | 1952990 tokens/s |
| Automata built per process | 1 | 1 |
| SHA-256 of the filtered list | `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` | `03c2b9b548d3be7374dccd2d704ca9b42d7db1a666de8fc9937d10f142a858c3` |

Entry counts, source size and the split results reproduce the numbers of the
phase research exactly. Build time came out faster than the 0.44 s the research
recorded, and throughput slightly lower than the 2.3 million tokens per second;
both are within the noise of a different machine and neither changes a decision.

The digest is taken over the filtered list, not over the source file. A Debian
point release that only reorders lines must not force a reindex; a changed
window must. The digest and `ANALYZER_VERSION` therefore live in the metadata
table next to `schema_version`: if either changes, the tokenisation changes, and
an index built with the old one silently disagrees with the query parser.

## The filter order

```text
simple -> lowercase -> split_compound(list) -> custom_stopword(FUGEN)
       -> stopword("german") -> remove_long(48) -> stemmer("german")
```

| Position | Filter | Why exactly here |
|---|---|---|
| 1 | `lowercase` | Everything after this compares strings exactly, and the list is lowercase |
| 2 | `split_compound` | Needs the raw, unstemmed, unfolded token; the list is in exactly that form |
| 3 | `custom_stopword(FUGEN)` | Without it a bare token `s` lands in the index |
| 4 | `stopword("german")` | The built in list carries real umlauts and compares exactly |
| 5 | `remove_long(48)` | **After** the splitter. In front of it a 63 character compound is dropped whole |
| 6 | `stemmer("german")` | Last; a stemmed compound no longer matches any dictionary entry |

There is no `ascii_fold` in the German branch. The Snowball stemmer folds
umlauts and sharp s by itself, and folding before the splitter would make the
list, which carries umlauts, unmatchable. English and the file name branch do
keep the folding, because there a different algorithm stems or nothing stems at
all.

## The twenty one measured compounds

The table below is the one `backend/tests/test_analyzer.py` asserts as
`COMPOUNDS` since plan 08-04, line for line, with the tokens measured in
`docs/measurements/2026-09-komposita-rezept-a/rohdaten/tokens-rezept-a.tsv`
against the real Debian list. It guards **both** directions: a split that gets
lost fails here as loudly as a split that gets invented, because every line
names its tokens instead of counting them. The words are written with their real
umlauts, because the transcription with spelled out umlauts is a different word
to the index, see "Known limits" below.

| Input | Expected tokens |
|---|---|
| Grundstücksverkehrsgenehmigung | `grundstuck, verkehr, genehm` |
| Kündigungsfrist | `kundig, frist` |
| Sitzungsvorlage | `sitzung, vorlag` |
| Haushaltssatzung | `haushalt, satzung` |
| Jahresabschluss | `jahr, abschluss` |
| Betriebskostenabrechnung | `betriebskost, abrechn` |
| Krankenversicherung | `krank, versicher` |
| Rechnungsnummer | `rechnung, numm` |
| Datenschutzgrundverordnung | `datenschutz, grund, verordn` |
| Bundesausbildungsförderungsgesetz | `bund, ausbild, forder, gesetz` |
| Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz | `rindfleisch, etikettier, uberwach, aufgab, ubertrag, gesetz` |
| Dampfschifffahrt | `dampfschiff, fahrt` |
| Aufenthaltserlaubnis | `aufenthalt, erlaubnis` |
| Gewerbeanmeldung | `gewerb, anmeld` |
| Mietvertrag | `mietvertrag`, whole only |
| Bebauungsplan | `bebauungsplan`, whole only |
| Baugenehmigung | `baugenehm`, whole only |
| Bauantrag | `bauantrag`, whole only |
| Baukosten | `baukost`, whole only |
| Arbeitsvertrag | `arbeitsvertrag`, whole only |
| Steuerbescheid | `steuerbescheid`, whole only |

Two spellings stand outside this table because they say something about the
stemmer rather than about the splitter: `Strasse` with and without the sharp s
both become `strass`, and `Müller` and `Muller` both become `mull`. Both are
asserted in `test_analyzer.py`, in `test_nominal_inflection_collapses_into_one_term`
and `test_the_stemmer_folds_umlauts_without_a_folding_filter`.

## The ten words that must not fall apart

`Information`, `Vertrag`, `Rechnung`, `Sitzung`, `Kunde`, `Formular`, `Termin`,
`Ordnung`, `Beamter`, `Genehmigung`. Recipe A splits none of them. A recipe that
splits any of them is producing nonsense terms, not better recall, and the test
table in `backend/tests/test_analyzer.py` asserts both directions.

## Licence and provenance

The word list is `/usr/share/dict/ngerman` from the Debian package `wngerman`,
source package `igerman98`, Copyright 1999 to 2016 Bjoern Jacke, licensed
**GPL-2+** according to `debian/copyright` (`Files: *`). Upstream additionally
offers an OASIS distribution licence as an alternative.

GPL-2+ permits moving to GPLv3, and GPLv3 is compatible with the AGPL-3.0 of
this project, so the list may ship inside the image. The obligations that follow
are not optional:

- the licence text ships in the image and is listed in `THIRD-PARTY.md`,
- the provenance above is stated wherever the list is described,
- the preparation code stays in the repository, in
  `backend/src/findling/index/wordlist.py` and
  `scripts/dev/measure_wordlist.sh`.

## Memory

The automaton is built **once per process**. Measured, the process keeps 41.4
MiB of resident memory for the `full` variant and 7.3 MiB for `nouns`, from the
start of the measurement until after the Python list has been dropped. That is an
upper bound rather than the size of the automaton alone: glibc does not return
freed arenas to the operating system, so the transient list is still counted. The
phase research arrived at roughly 23 MiB for the automaton itself with a
different method. Both numbers say the same thing about the budget of a 4 GB box:
this is affordable once and not twice.

`cached_german_analyzer` is therefore a per process singleton keyed on the digest
of the list, `build_count()` reports how often an automaton was really built, and
`test_analyzer_is_built_once` fails if a second one ever appears. For the same
reason the extraction child process of plan 02-05 must not import
`findling.index.analyzer` at all: it would pay these megabytes for every single
file it looks at, and it needs none of them.
`findling.index.wordlist` stays free of any import of the analyser so that a
caller who only needs the list or its digest can have it cheaply.

The resident memory of the running image is measured and recorded again in plan
02-13, against the real container rather than a measurement harness.

Admins who cannot afford the `full` variant set `FINDLING_COMPOUND_DICT=nouns`.
That is a measured trade, not a guess: two of the sixteen long compounds of the
recipe table stop being findable through one of their parts, and about 34 MiB
come back.

## The DACH cases (D-09)

Findling soll nicht nur bundesdeutsche Dokumente finden. Die Zusage aus D-09
lautet: ein Schweizer Dokument mit der Schreibweise ss ist ebenso auffindbar wie
ein deutsches mit dem scharfen s, und ein österreichisches Dokument ist über
seine eigene Wortform auffindbar. Was dabei belegt ist und was nicht, steht hier,
weil beides gemessen wurde.

Gemessen am 2026-09-01 mit dem Laufzeitimage: die drei gescannten Dokumente des
Referenzkorpus einmal durch OCR, der erkannte Text in einen echten Tantivy-Index
mit der echten Konstituentenliste, gefragt mit dem echten Abfrage-Parser.

| Gesucht | So steht es in der Datei | Datei | Treffer | Warum |
|---|---|---|---|---|
| `Strasse` | Strasse, Bahnhofstrasse | `15-schweiz-baubewilligung.pdf` | 1 | Term `strass`, direkt getroffen |
| `Straße` | Strasse, Bahnhofstrasse | `15-schweiz-baubewilligung.pdf` | 1 | Der Snowball-Stemmer faltet das scharfe s auf `ss`, beide Schreibweisen landen auf `strass` |
| `Jänner` | Jänner | `16-oesterreich-mitteilung.pdf` | 1 | Gewöhnlicher Termtreffer, der Stemmer entfernt nur den Umlautakzent |
| `Januar` | steht in keiner Datei | keine | 0 | Wäre Synonymie und ist in v1 nicht gebaut |
| `Bebauungsplan` | Bebauungsplan | `13-ratsvorlage-scan.pdf` | 1 | Steht selbst in der Liste, wird also nicht zerlegt |

Die Schweizer Zusage braucht keine zusätzliche Mechanik. In der deutschen Kette
steht kein `ascii_fold`, der Stemmer faltet Umlaute und das scharfe s selbst, und
die Abfrageseite bildet zusätzlich die Variante für ausgeschriebene Umlaute. Beide
Wege führen auf denselben Term, und die Zeile mit dem scharfen s im
Integrationslauf ist der Beleg dafür statt einer Ableitung aus der Doku.

**Der eigentliche DACH-Risikopunkt liegt nicht in dieser Kette, sondern in der
OCR-Qualität.** Tesseract verwechselt bei schlechten Scans regelmäßig Zeichen;
gemessen liest die Engine des Images die fette Überschrift einer Korpusdatei als
"Ubermittlungsprotokoll", ohne die beiden Punkte. Deshalb läuft die Abnahme über
auffindbare Suchbegriffe und niemals über einen Vergleich des OCR-Rohtextes: ein
Rohtextvergleich wäre ein Test gegen die Version der Engine und beim nächsten
Debian-Punktrelease rot. `docs/ocr.md` führt dieselbe Begründung an der Stelle,
an der die Engine beschrieben wird.

## What splitting costs at ranking time

When the splitter succeeds, the original token is **thrown away**: the whole
compound does not stand in the index, only its parts do. Measured in
`docs/measurements/2026-09-komposita-rezept-a/`: `Kündigungsfrist` yields
`kundig, frist` and nothing else, so there is no term for the whole word left to
match.

A search for the whole word still works, because the query side runs the same
analyser and produces the same parts. It works as a **conjunction over the
parts**, however, not as one term: the query parser of
`backend/src/findling/query/rewrite.py` is built with
`conjunction_by_default=True`. A document that happens to carry all the parts in
unrelated places therefore competes with the document that carries the whole
word, and nothing in the scoring knows that the parts stood next to each other
in one of them.

That is the price of splitting. It is paid deliberately, because the alternative
is not finding the document at all, and it is written down here so that a later
ranking complaint has a cause to look at rather than a mystery.

## Known limits

These six are measured, documented and deliberately not fixed here.

**D2, verb forms.** The Snowball stemmer unifies the infinitive and the noun but
not the past tense or the participle: `suchen` and `Suche` both become `such`,
`suchte` becomes `sucht`, and `gesucht` stays `gesucht`. This cannot be fixed
without replacing the stemmer, which would change every term in the index. The
acceptance criterion of `02-CONTEXT.md` is therefore restated: it is checked on
**nominal inflection** (`Haus` against `Haeuser`, `Vertrag` against `Vertraege`,
`Strasse` with and without the sharp s), not on `suchte` against `suchen`.

**D3, the spelled out umlaut.** `Mueller` becomes `muell` and `Mueller` written
with the umlaut becomes `mull`. To a human these are one name, to the index they
are two terms. The fix belongs on the query side and lands in plan 02-09: a query
containing `ue`, `oe`, `ae` or `ss` also gets the umlaut variant, and both
branches are joined with `Occur.Should`. That costs no index space, acts only on
queries, and an occasionally meaningless variant simply produces an empty branch.
Indexing both forms instead would work as well and would cost index space
permanently for a rarer case.

**D-09, the Austrian month name.** `Jänner` is stemmed and is findable through
`Jänner`. A search for `Januar` does not find it, and it is not meant to: the two
are different words, and joining them is synonymy. A synonym list would be a
second data file with a second licence, it would act on every query of every
language branch, and the first entry always drags a hundred more behind it. What
would be affected is a handful of Austrian month names and a few
Austrian and Swiss administrative terms, so the trade is a whole mechanism
against a small, nameable set. The measured table above records the zero rather
than hiding it, and `testdata/CORPUS.md` names the one file the Austrian word
stands in, so whoever builds synonymy in a later version has both the case and
the counter case ready.

**Compounds that stand in the list themselves.** A compound of at most 14
characters that is an entry of the list is never split, because the splitter
matches leftmost-longest. `Mietvertrag` is eleven characters, stands in the list,
and is therefore **not** findable through `Vertrag`. Shrinking the window would
split more of these and start over-splitting others, which is exactly what recipe
D measures. `backend/tests/test_analyzer.py` asserts this limit in both
directions rather than leaving it as folklore.

This limit is wider than it used to read here. Measured in
`docs/measurements/2026-09-komposita-rezept-a/`, section 3.2: of the twenty one
administrative compounds of the guard table `COMPOUNDS`, **seven** do not come
apart, and those seven are the short, frequent ones that people actually type.
"Everyday" belongs to these seven and not to the whole table: sixteen of the
twenty one are the long, rare words the paragraph on the recipes above calls
exactly that, and
`Rindfleischetikettierungsueberwachungsaufgabenuebertragungsgesetz` is nobody's
everyday compound.

| Compound | Characters | Token | Why it stays whole |
|---|---|---|---|
| `Mietvertrag` | 11 | `mietvertrag` | entry of the list |
| `Bebauungsplan` | 13 | `bebauungsplan` | entry of the list |
| `Baugenehmigung` | 14 | `baugenehm` | entry of the list, at the upper edge of the window |
| `Bauantrag` | 9 | `bauantrag` | entry of the list |
| `Arbeitsvertrag` | 14 | `arbeitsvertrag` | entry of the list |
| `Steuerbescheid` | 14 | `steuerbescheid` | entry of the list |
| `Baukosten` | 9 | `baukost` | **no** entry: `bau` has three characters and `MIN_LEN` is four, so the splitter never reaches the second part |

`Baukosten` is the one that does not explain itself through list membership at
all. The lower bound is a second, independent lock, and whoever reads only the
entry column misses half of the cases. All seven stand in
`backend/tests/test_analyzer.py` as `COMPOUNDS` lines with exactly one token, so
a change that makes one of them splittable has to say so out loud instead of
sliding through. `Baugenehmigung` in particular is the reason the phase success
criterion was reworded: a search for `Genehmigung` produces `genehm`, the
document produces `baugenehm`, and the two terms share nothing.

**Spelled out umlauts on the index side.** The ASCII transcription of a compound
is split by none of the measured recipes.
`Grundstuecksverkehrsgenehmigung` stays the single token
`grundstuecksverkehrsgenehm`, while `Grundstücksverkehrsgenehmigung` with real
umlauts comes apart into `grundstuck, verkehr, genehm`
`[docs/measurements/2026-09-komposita-rezept-a/, section 3.2]`. The constituent
list carries its umlauts and the splitter compares exactly, so a transcribed
word matches no entry at all. This is not the same thing as D3 above: D3 costs a
term, this costs the whole split. `add_umlaut_variants` of plan 02-09 does not
reach it either, because it widens the **question** and the index side has no
counterpart. A document out of a legacy system or out of an OCR run that lost
its umlaut dots is therefore findable under its whole word only.
`test_the_transcribed_umlaut_costs_the_split_not_only_the_term` in
`backend/tests/test_analyzer.py` nails both spellings down side by side.

**More entries can mean less splitting.** The list is not monotonic: adding
entries can take a split away. Measured with `remove_long` switched off so that
the cause is unambiguous, recipe A splits the 63 character compound into its
parts, while recipe A3, which does nothing but lower the window to three
characters and therefore only adds entries, leaves it as one 63 character token
`[docs/measurements/2026-09-komposita-rezept-a/, section 4, and
.planning/phases/08-deutsche-komposita-ohne-behelf/08-RESEARCH.md]`. The split
does not become different, it **fails**, because a longer match further left can
lead the leftmost-longest walk into a dead end it cannot back out of. With
`remove_long(48)` switched on again the token is then dropped and the document is
findable under none of its six parts.

The rule that follows: **a change to the list is a data migration, not a
tweak.** It moves `wordlist_hash`, it forces a reindex, and it may only be run
against the full measured case collection in both directions, gained and lost
splits. `scripts/dev/measure_compounds.sh --against LIST` is the run that
answers this question, and `COMPOUNDS` in `backend/tests/test_analyzer.py` is the
collection.

The shipped test fixture `backend/tests/fixtures/constituents_de.txt` went
through exactly that run. It carries **223 entries**, the union of the 194 the
probe generated with the 172 the suite already had, and the union was measured
rather than assumed: over all 48 cases it produces byte for byte the same tokens
as the full 276496 entry list. Output line and command stand in section 6.1 of
`docs/measurements/2026-09-komposita-rezept-a/`.
