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
- **Text inside scanned pages**, through OCR, in German, English and the DACH
  spellings.
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

- Nextcloud 32 to 35 (`min-version` 32, `max-version` 35)
- The AppAPI app, with HaRP as the deploy target
- Target hardware: 4 to 8 GB RAM, ARM64 and AMD64, CPU only, no GPU required

The project is built for self hosters and small organisations on ordinary hardware,
not for a search cluster.

## What it costs in memory, measured

**A full index, OCR and embedding run over 50,000 files and 20 GB on a 4-GB ARM64
box peaked at 1,838 MB of resident anonymous memory, under a hard 2 GB limit
enforced by the kernel, with no OOM kill and no restart.** The run took 18 hours
56 minutes until the last vector, wrote a 785 MB word index and a 69 MB vector
store, and left every file with a verdict: 51,961 indexed and embedded, 37
skipped for a named reason, **none failed**. A user search during the run
answered in 1.1 seconds at the 95th percentile, after the run in 0.5 seconds.

That is a measurement and not an estimate. It was taken on arm64 with 2 cores and
4 GB, which is the hardware this app is built for. Two honest sentences belong
next to it. First: the kernel counters for memory damage (`oom`, `oom_kill`,
`oom_group_kill`) are zero, but the `max` counter is not, because the file cache
of the index pressed against the 2 GB limit 2,796 times while the semantic search
held 1.5 to 1.8 GB of its own; the limit was respected, it was not left untouched.
Second: most of that memory is the semantic search, not the indexing. The same
run without embeddings peaked at 422 MB and took 12 hours 49 minutes on the same
machine, and about 276 MB of the difference is a second copy of the model that the
search side loads next to the one the indexer holds. That is a known finding and
it is being addressed in the hardening before the first release.

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
