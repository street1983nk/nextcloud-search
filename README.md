# Findling

Zero-config full text search for Nextcloud.

Findling makes the Nextcloud search find what is inside your documents, including
scanned PDFs, without an Elasticsearch cluster and without a single required setting.
Results appear in the regular unified search bar, next to files, contacts and
calendar entries.

**Status: Phase 1, walking skeleton, not usable yet.** There is no indexing and no
real search in this phase. This repository currently proves the integration path
end to end and freezes the store identity. Do not install it on a production server.

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

## Privacy

- No file content leaves the server. Extraction, OCR, indexing and search all run
  inside the container on your own machine.
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
