# Measurements of the Chinese chain (issue #53), 2026-11-15

The figures that the pull request bringing `body_zh` quotes, in
`backend/src/findling/index/rebuild.py` (`GROWTH_PER_LANGUAGE`) and in the
section "Chinese" of `docs/language-analyzers.md`. Two questions, and nothing
more: what a filled `body_zh` costs on disk, measured against the reserve the
rebuild charges, and how much `body_zh` moves the order of English hits, for
the two variants of the chain. The full measurement report of issue #53, with a
labelled query set, latency and the snippet options, is a separate step.

Written in English, like `docs/l10n-chinese.md`, by a contributor who cannot
vouch for German prose.

## Environment

- Date: 2026-11-15
- Machine: AMD Ryzen 5 8500G, Linux 7.0.0 x86_64 (a desktop, not the target box)
- Python 3.13.13, tantivy-py 0.26.2 and lxml 6.1.3 out of `backend/uv.lock`
- Code: the branch of the pull request that adds `body_zh`, with
  `chinese_analyzer` as shipped (`ZH_PATTERN` Han and Latin)

## The corpora

**Taiwanese statutes.** Twelve laws and one regulation from the law database of
the Ministry of Justice, which are not protected by copyright (Copyright Act of
Taiwan, article 9). The pages were saved with

```bash
for p in B0000001 C0000001 J0070017 I0050021 N0030001 A0000001 D0050001 B0010001 C0010001 G0340003 K0020047 H0020001; do
  curl -sS -m 30 -A "Mozilla/5.0" -o "$p.html" "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=$p"
done
```

and turned into one text file per article by `skripte/zh_corpus.py`.
`rohdaten/korpus-gesetze.txt` carries per page the pcode, the title, the number
of articles, the characters and the sha256 of the saved page: 4306 articles,
411564 characters. The pages themselves are not checked in; the manifest is
what makes a later fetch comparable, and a law that was amended since will show
up there as another digest.

**Word list text.** 2000 documents of 450 words each, drawn from
`/usr/share/dict/american-english` (Debian `wamerican`, sha256 at the end of
`rohdaten/wachstum-wortliste.txt`) with Zipf weights and the seed `53`, by
`skripte/zh_growth.py`. It stands in for text without a single Han character.

**English documents.** The licence texts under `/usr/share/common-licenses` and
the README files one level under `/usr/share/doc` of the machine, listed in
`rohdaten/englisch-pfade.txt` with their sha256 in
`rohdaten/englisch-sha256.txt`: 593 files, of which 530 are longer than 400
characters and go in, cut at 20000 characters (1222722 characters). The list
was made with

```bash
(ls /usr/share/common-licenses/*; find /usr/share/doc -mindepth 2 -maxdepth 2 -type f -name 'README*' ! -name '*.gz') | LC_ALL=C sort
```

## 1. Space

**Question.** `findling.index.rebuild.may_rebuild` charges every newly filled
language 0.40 of the directory it finds (`GROWTH_PER_LANGUAGE`), measured on
German text for the Snowball chains and for Czech (0.358). Does that hold for a
chain that writes one posting per Han character?

**Method.** `skripte/zh_growth.py`: three directories over the same documents,
written through `IndexBatchWriter` as the container writes them, with the
languages `de,en`, `de,en,zh` and `de,en,cs`, and the size of each directory
after the writer is closed (`findling.store.repo.index_bytes`). The statutes are
joined in file order into documents of at least 3000 characters.

```bash
cd backend
uv run python ../docs/measurements/2026-11-zh-kette/skripte/zh_growth.py statutes <articles> 3000
uv run python ../docs/measurements/2026-11-zh-kette/skripte/zh_growth.py wordlist /usr/share/dict/american-english 53
```

**Result** (`rohdaten/wachstum-gesetze.txt`, `rohdaten/wachstum-wortliste.txt`):

| Corpus | Documents | `de,en` directory | growth by `zh` | growth by `cs` |
|---|---:|---:|---:|---:|
| Taiwanese statutes | 152 | 1.946 times the text | **0.253** | 0.371 |
| Word list text | 2000 | 1.335 times the text | **0.280** | 0.280 |

`zh` costs no more than `cs` on either corpus, so the reserve of 0.40 holds.
On Chinese text it costs less: one posting per character lands in a small term
dictionary of a few thousand characters, while every other chain keeps each
clause between two punctuation marks as a term of its own. The same reason
makes the `de,en` directory of the statutes large (1.946 times the text): the
German and the English chain write one long, nearly unique term per clause.
How large `body_zh` is against the text of a realistic mixed corpus is left to
the full report.

## 2. The order of English hits

**Question.** `body_zh` keeps runs of Latin letters and digits as words (Han and
Latin). An English word then scores on `body_zh` too, unstemmed, and tantivy
sums the scores of the fields. How much does switching `zh` on move the order of
English hits, and what does the weight of `body_zh` do to that? The alternative,
a chain that indexes Han characters only, is the control.

**Method.** `skripte/zh_rank.py`: one index over the English documents, written
with `de`, `en` and `zh` filled, and a second one whose `body_zh` chain cuts Han
characters only. Twenty English queries (in the script) go through
`findling.query.rewrite.build_query` with and without `body_zh` in the plan, and
the two top ten lists are compared: the mean share of the first list the second
one keeps, how often the first hit stays the same, and how often the lists are
identical.

```bash
cd backend
uv run python ../docs/measurements/2026-11-zh-kette/skripte/zh_rank.py ../docs/measurements/2026-11-zh-kette/rohdaten/englisch-pfade.txt
```

**Result** (`rohdaten/rangfolge.txt`):

| Chain | `body_zh` weight | `en` against `en,zh` | `de,en` against `de,en,zh` |
|---|---:|---|---|
| Han and Latin (shipped) | 0.6 (shipped) | overlap 0.685, first hit kept 9 of 20 | overlap 0.900, first hit kept 17 of 20 |
| Han and Latin | 0.3 | 0.715, 10 of 20 | 0.925, 19 of 20 |
| Han and Latin | 0.15 | 0.775, 13 of 20 | 0.965, 20 of 20 |
| Han and Latin | 0.05 | 0.860, 17 of 20 | 0.995, 20 of 20 |
| Han only | 0.6 | 1.000, 20 of 20, every list identical | 1.000, 20 of 20, every list identical |

**What this says and what it does not.** It measures how much the order moves,
not whether it gets better or worse: there are no relevance judgements behind
the twenty queries. The Han only chain leaves English results exactly as they
are, at the price named in `docs/language-analyzers.md` (a search term such as
`2026年` loses its number, and Latin words cannot be found in an installation
running `zh` alone). Lowering the weight of `body_zh` reduces the movement, much
more for `de,en,zh` than for `en,zh`. Which weight, or a disjunction max over
the body fields instead, is a question for the full report with labelled
queries.

## Raw data

| File | Content |
|---|---|
| `rohdaten/korpus-gesetze.txt` | output of `zh_corpus.py`: pcode, title, articles, characters, sha256 per page |
| `rohdaten/wachstum-gesetze.txt` | output of `zh_growth.py statutes` |
| `rohdaten/wachstum-wortliste.txt` | output of `zh_growth.py wordlist`, with the sha256 of the word list |
| `rohdaten/englisch-pfade.txt` | the file list of the English documents |
| `rohdaten/englisch-sha256.txt` | the sha256 of each of those files |
| `rohdaten/rangfolge.txt` | output of `zh_rank.py` |

Every script ran as it is checked in, and the files above are its output of
2026-11-15.
