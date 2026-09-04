# Findling

Zero-config full text search for Nextcloud.

Findling makes the Nextcloud search find what is inside your documents, including
scanned PDFs, without an Elasticsearch cluster and without a single required setting.
Results appear in the regular unified search bar, next to files, contacts and
calendar entries.

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

**A full index and OCR run over 50,000 files and 20 GB on a 4-GB box peaked at
429 MB of resident anonymous memory, under a hard 2 GB limit enforced by the
kernel, with no OOM kill.** The run took 10 hours 14 minutes, wrote a 726 MB index
and left every one of the 50,104 files with a verdict and none of them failed.

That is a measurement and not an estimate. Method, the full curve, the corpus, the
four part OOM proof and three failure drills on the same machine (`docker kill`
during OCR, backend gone, disk nearly full) are in
[docs/performance.md](docs/performance.md), including what each of them does not
prove.

The machine was a rented 4 GB x86 box running Nextcloud All-in-One. The repetition
on 4 GB ARM hardware is still open, and the report names every figure that it will
replace.

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
