[Deutsch](README.md) | English | [Français](README.fr.md)

# Findling

Zero-config full text and semantic search for Nextcloud.

Findling makes the Nextcloud search find what is inside your documents, including
scanned PDFs, without an Elasticsearch cluster and without a single required setting.
Results appear in the regular unified search bar, next to files, contacts and
calendar entries.

## What it finds

- **Words that stand in the document**, with German handling that a search needs:
  compounds through one of their parts, inflection, the written out umlaut,
  phrases, exclusions and a file type filter.
- **Text inside scanned pages**, through OCR, in German, English, French and
  the DACH spellings. All three are on out of the box, no setting has to be
  touched. The search itself stays tuned for German and English: a French page
  is read and found, but without French stemming.
- **Documents you describe instead of quote.** A query whose words do not stand
  in the document can still bring it back, because a local embedding model
  ranks by meaning next to the word index.

The honest sentence about the third one, and it is the same one in both store
descriptions: **semantic search covers the beginning of every document, full
text search still covers all of it.** How much "the beginning" is depends on the
document, and on the measured corpus it is 12.5 percent of an average one. The
model runs inside the container, on the CPU, and no text leaves the machine for
it. The details, the measured quality in three languages and the two proofs that
the container needs no network for any of it are in
[docs/embeddings.md](docs/embeddings.md).

Not every query gets that second list, and the two exceptions are deliberate. A
query with quotation marks, a minus, a field prefix, a file type or one of the
grammar words AND, OR and NOT is answered by the word index alone: whoever
searches like that has asked for exactness, and a list ranked by meaning does not
know about that request. A query of a single word is answered the same way,
because a single word is measurably no nearer to the document it means than an
unrelated one is, and the compound splitter, the stemmer and the umlaut variant
already cover it. A query of two words or more without such an operator is
answered by both halves together.

**Status: hardening before the first store release, not submitted yet.** Indexing,
OCR and search work and are measured on rented hardware, see below. The release
artefacts of both apps are being prepared; until they are in the store, do not
install this on a production server.

## The two app model

Findling ships as two store entries that belong together:

| Part | App id | Store section | What it does |
|------|--------|---------------|--------------|
| PHP companion | `findling` | Apps | Registers the search provider and proxies queries to the backend |
| Python ExApp | `findling_backend` | External Apps | Runs extraction, OCR and the search index inside a container |

Both entries must be installed, and both always carry the same major and minor
version. The companion is tiny on purpose: it owns the Nextcloud side, including the
permission check, because Nextcloud cannot register a search provider from an
external app. The container owns the heavy lifting.

## Requirements

- Nextcloud 33 to 35 (`min-version` 33, `max-version` 35). Nextcloud 32 left the
  window with the decision of 2026-09-06: it goes out of support in September 2026,
  this app is submitted in December, and an app that claims a server nobody
  supports any more claims something it cannot make good on.
- The AppAPI app, with HaRP as the deploy target
- Target hardware: 4 to 8 GB RAM, ARM64 and AMD64, CPU only, no GPU required

The project is built for self hosters and small organisations on ordinary hardware,
not for a search cluster.

## What it costs in memory, measured

**On a 4-GB ARM64 box with 51,961 indexed documents and the semantic search
active, the container peaked at 1,813 MB of resident anonymous memory, under a
hard 2 GB limit enforced by the kernel. The three kernel counters for memory
damage (`oom`, `oom_kill`, `oom_group_kill`) are zero, and the fourth counter
`max`, which counts how often the kernel had to push the container back against
its limit, is zero as well.** Measured on 07.09.2026
([docs/measurements/2026-09-nachmessung-m7g](docs/measurements/2026-09-nachmessung-m7g/)).

`max` is disclosed here rather than left out, because it was not zero in the
previous measurement: the file cache of the index pressed against the 2 GB limit
2,796 times back then. No process was killed, but the kernel had to work. This
time it did not have to, not once.

**The previous figure, as a comparison:** 1,838 MB, measured on 05.09.2026 in the
full semantic run
([docs/measurements/2026-09-05-semantiklauf-m7g](docs/measurements/2026-09-05-semantiklauf-m7g/)),
with `max 2,796`. The difference is not measurement noise: the search side loaded
a second copy of the model next to the one the indexer held. That copy is gone,
and the search phase fell from 1,838 MB to 1,125 MB because of it. That the
overall peak fell by only 25 MB has a reason of its own: it now arises in the OCR
phase rather than in the search, and the OCR has worked with three languages
instead of two since 06.09.2026. Both figures carry their date and their reason
in the measurement report.

**Concurrent searches:** up to **eight** hold the time budget of 2.5 seconds on
this box (95th percentile 1.9 s over 410 requests). At twelve it breaks. That is a
figure about this box and this instance: the Nextcloud search asks every provider
at once, so the PHP process pool of the instance sets a limit just as much, and
that pool is a different size everywhere.

**The full run the stock comes from:** 50,000 files and 20 GB, 18 hours 56 minutes
until the last vector, a 785 MB word index and a 69 MB vector store, and every
file with a verdict: 51,961 indexed and embedded, 37 skipped for a named reason,
**none failed**. A user search during the run answered in 1.1 seconds at the 95th
percentile, after the run in 0.5 seconds.

These are measurements and not estimates. They were taken on arm64 with 2 cores
and 4 GB, which is the hardware this app is built for. These runtimes are the
smallest supported target hardware and a deliberate lower bound: on modern,
powerful hardware indexing runs considerably faster, but no dedicated measurement
for that exists yet. One honest sentence belongs next to it: most of that memory
is the semantic search, not the indexing. The same full run without embeddings
peaked at 422 MB and took 12 hours 49 minutes on the same machine.

Method, both full curves, the corpus, the four part OOM proof, four failure drills
on the same machine (`docker kill` during OCR, a reboot of the whole machine,
backend gone, disk nearly full), the breakdown of what the semantic search costs
at idle and a side measurement with a second index worker are in
[docs/performance.md](docs/performance.md), including what each of them does not
prove.

## Privacy

- No file content leaves the server. Extraction, OCR, indexing and search all run
  inside the container on your own machine.
- What is stored is the extracted text. The text of every indexed document is kept
  in the backend app's own volume, because the excerpts shown under a search result
  are cut out of it on demand. A backup of that volume therefore contains the text
  of your indexed documents, and the index is not encrypted at rest, which is a
  matter for the host it runs on. The same paragraph stands in both store
  descriptions, in all three languages.
- No telemetry. The app does not phone home, not even for version checks.
- User files are never modified. Every file access goes through a read only content
  gateway, and a checksum gate in CI proves the invariant on a reference corpus.
- Permissions are enforced by Nextcloud itself. The final result filter runs in PHP
  against the user folder, so the index never becomes a second permission model.

## Repository layout

```
php/               PHP companion app, mapped to apps/findling in CI
backend/           Python ExApp, package under backend/src/findling/
testdata/corpus/   Reference corpus for the read only checksum gate
docs/              Process and operations documentation
.github/workflows/ CI: python, php, integration, docker
```

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
