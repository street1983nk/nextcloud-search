[Deutsch](README.md) | English | [Français](README.fr.md)

# Findling

[![Python gates](https://github.com/street1983nk/nextcloud-search/actions/workflows/python.yml/badge.svg)](https://github.com/street1983nk/nextcloud-search/actions/workflows/python.yml)
[![PHP and store metadata gates](https://github.com/street1983nk/nextcloud-search/actions/workflows/php.yml/badge.svg)](https://github.com/street1983nk/nextcloud-search/actions/workflows/php.yml)
[![Security scans](https://github.com/street1983nk/nextcloud-search/actions/workflows/security.yml/badge.svg)](https://github.com/street1983nk/nextcloud-search/actions/workflows/security.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/street1983nk/nextcloud-search/badge)](https://scorecard.dev/viewer/?uri=github.com/street1983nk/nextcloud-search)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/15327/badge)](https://www.bestpractices.dev/projects/15327)
[![Nextcloud App Store](https://img.shields.io/badge/App_Store-findling-0082c9)](https://apps.nextcloud.com/apps/findling)
[![Licence](https://img.shields.io/badge/Licence-AGPL--3.0--or--later-blue)](LICENSE)

Full text search, OCR and semantic search for Nextcloud, with zero
configuration. Results appear in the normal search bar.

**Findling + Nextcloud MCP Connector = the retrieval layer for your own RAG.**
The [MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) hands Findling's hits to any MCP client, with exactly the
rights of the asking user; measured by the
[fidelity test](https://github.com/street1983nk/nextcloud-mcp-connector/blob/main/tests/integration/test_content_hit_fidelity.py).
You bring the model, and no content leaves your server.

![Semantic search in the Nextcloud search bar: no word of the question appears in the found document, the hit comes through meaning](store/media/screenshot-search-v2.png)

## What Findling does

- Full text search with German word handling: compounds, inflection, umlauts,
  phrases, exclusions, a file type filter
- OCR for scanned PDFs and images: ten languages available (German, English,
  French, Spanish, Italian, Dutch, Portuguese, Danish, Estonian, Czech),
  German, English and French switched on by default
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own
- Performance profiles: Economy by default, Standard and Performance after a
  pre-check of the hardware
- Search model: int8 built in, the more accurate fp32 can be downloaded once
  under Standard and Performance

## Supported file types

PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP, HTML, RTF, TXT, Markdown,
CSV, and images (JPEG, PNG, TIFF, WebP) through OCR.

## Requirements

- Nextcloud 33 to 35 with the AppAPI app (HaRP as the deploy target)
- RAM: 4 GB is enough. On a 4-GB ARM64 box with 52,111 indexed documents and
  the semantic search active, the container peaked at 1,764 MB of resident
  anonymous memory, under a hard 2 GB limit enforced by the kernel.
- After an index run, with the model unloaded, the container sits at 730.2 MB
  of resident memory (measured 2026-09-26 on an m7g.large arm64 box against the
  v1.3 image, method and raw data in
  [docs/performance.md](docs/performance.md)).
- CPU: 2 cores are enough, amd64 and arm64, no GPU
- Without any change on your side, Findling keeps running as economically as
  before. Anyone with more hardware can use a profile to free at most half of
  the box (Standard profile) or everything but one core (Performance profile).
- The two additional profiles enable several OCR slots and a parallel embedding
  lane, which shortens indexing. Switch with one click in the admin settings
  under Findling; a suggestion matching your box is shown next to it.

## Installation

Install both store entries, always in the same version:
[Findling](https://apps.nextcloud.com/apps/findling) (Apps) and
[Findling Backend](https://apps.nextcloud.com/apps/findling_backend)
(External Apps). The first index run then starts on its own;
`occ findling:index --status` shows the progress. With many scanned documents
the first run can take a long time (OCR is compute heavy); measured run times
live in [docs/performance.md](docs/performance.md).

If the two apps run in different major or minor versions, the search answers
with nothing instead of possibly wrong results, and the admin page names both
version numbers.

## Architecture

Findling is two apps under one version:

- **findling** (store section Apps): the PHP companion app registers the
  search provider in the search bar and checks every hit against Nextcloud's
  permissions before it is shown.
- **findling_backend** (store section External Apps): the container does the
  work, text extraction, OCR (Tesseract), the full text index (Tantivy) and
  the semantic index (SQLite with sqlite-vec). It is reachable only through
  AppAPI/HaRP, and the routes that return content are not reachable from the
  browser.

The index lives in the app volume on your server; there is no service in
between and nothing leaves the instance.

## Privacy

Everything runs locally in the container, no telemetry, files are never
modified. What is stored is the extracted text, in the backend app's own data
area: a backup of that area contains it, and the index is not encrypted at
rest. The remedies, full disk encryption of the host and a deliberate backup
policy, are laid out with their reasoning in [docs/privacy.md](docs/privacy.md)
(German).

## Measurements

Every number (memory, run times, search load, failure drills, model quality)
lives with its method and raw data in [docs/performance.md](docs/performance.md)
and [docs/embeddings.md](docs/embeddings.md).

## Enterprise

Findling is and stays AGPL. Paid add-ons and support with agreed response
times are planned, but not available yet, for organisations that need them.

Request a quote: admin@infranode.dev

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE).
