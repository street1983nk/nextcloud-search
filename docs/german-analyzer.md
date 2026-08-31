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

| Recipe | Entries | Compounds findable through a part | Mis-splits |
|---|---|---|---|
| **A: all words, window 4 to 14, linking elements as own entries** | **276496** | **14 of 16** | **0** |
| B: nouns only, linking forms appended to each word, folded to plain ASCII | 222708 | 7 of 16 | yes, e.g. `haushaltss` + `atzung` |
| C: nouns only, window 4 to 14 | 86345 | 12 of 16 | 0 |
| D: nouns only, window 4 to 12 | 65693 | 12 of 16 | 0, but over-splits: `betrieb` + `kost` + `abrechn` |

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
| Time to read and filter | 0.312 s | 0.165 s |
| Resident memory of the Python list | 23736320 B (22.6 MiB) | measured after the `full` list was freed, so not comparable in the same process |
| SHA-256 of the filtered list | `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` | `03c2b9b548d3be7374dccd2d704ca9b42d7db1a666de8fc9937d10f142a858c3` |

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

## The sixteen test compounds

| Input | Expected tokens |
|---|---|
| Grundstuecksverkehrsgenehmigung | `grundstuck, verkehr, genehm` |
| Kuendigungsfrist | `kundig, frist` |
| Sitzungsvorlage | `sitzung, vorlag` |
| Haushaltssatzung | `haushalt, satzung` |
| Jahresabschluss | `jahr, abschluss` |
| Betriebskostenabrechnung | `betriebskost, abrechn` |
| Krankenversicherung | `krank, versicher` |
| Rechnungsnummer | `rechnung, numm` |
| Datenschutzgrundverordnung | `datenschutz, grund, verordn` |
| Bundesausbildungsfoerderungsgesetz | `bund, ausbild, forder, gesetz` |
| Rindfleischetikettierungsueberwachungsaufgabenuebertragungsgesetz | `rindfleisch, etikettier, uberwach, aufgab, ubertrag, gesetz` |
| Dampfschifffahrt | `dampfschiff, fahrt` |
| Mietvertrag | `mietvertrag`, whole only |
| Bebauungsplan | `bebauungsplan`, whole only |
| Strasse (with sharp s) | `strass` |
| Muell (with umlaut) | folded by the stemmer |

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

## Honest limits of the recipe

A compound of at most 14 characters that stands in the list itself is never
split, because the splitter matches leftmost-longest. `Mietvertrag` is eleven
characters, stands in the list, and is therefore **not** findable through
`Vertrag`. Shrinking the window would split more of these and start
over-splitting others, which is exactly what recipe D measures.
