[Deutsch](README.md) | English | [Français](README.fr.md)

# Findling

Full text search, OCR and semantic search for Nextcloud, with zero
configuration. Results appear in the normal search bar.

## What Findling does

- Full text search with German word handling: compounds, inflection, umlauts,
  phrases, exclusions, a file type filter
- OCR for scanned PDFs and images: German, English, French
- Semantic search: finds documents through paraphrases
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own

## Supported file types

PDF (scanned too), DOCX, PPTX, XLSX, ODT, ODS, ODP, HTML, RTF, TXT, Markdown,
CSV, and images (JPEG, PNG, TIFF, WebP) through OCR.

## Requirements

- Nextcloud 33 to 35 with the AppAPI app (HaRP as the deploy target)
- RAM: 4 GB is enough. On a 4-GB ARM64 box with 51,961 indexed documents and
  the semantic search active, the container peaked at 1,813 MB of resident
  anonymous memory, under a hard 2 GB limit enforced by the kernel.
- CPU: 2 cores are enough, amd64 and arm64, no GPU

## Installation

Install both store entries, always in the same version:
[Findling](https://apps.nextcloud.com/apps/findling) (Apps) and
[Findling Backend](https://apps.nextcloud.com/apps/findling_backend)
(External Apps). The first index run then starts on its own;
`occ findling:index --status` shows the progress.

## Privacy

Everything runs locally in the container, no telemetry, files are never
modified. What is stored is the extracted text, in the backend app's own data
area: a backup of that area contains it, and the index is not encrypted at
rest.

## Measurements

Every number (memory, run times, search load, failure drills, model quality)
lives with its method and raw data in [docs/performance.md](docs/performance.md)
and [docs/embeddings.md](docs/embeddings.md).

## Licence

AGPL-3.0-or-later. See [LICENSE](LICENSE).
