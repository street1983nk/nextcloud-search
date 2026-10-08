# Changelog

All notable changes to Findling (the `findling` companion app and the
`findling_backend` External App) are documented here. Both apps carry the
same version. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- SECURITY.md with the two private reporting channels, CONTRIBUTING.md, and
  issue and pull request templates.
- CI security scans: CodeQL over the Python half and pip-audit over the
  locked dependency set, weekly on top of every push.
- This changelog; it travels with both store archives from the next release.

## [1.4.1] - 2026-10-08

### Fixed

- The App Store shows the current screenshots again. The store's image mirror
  keeps the first version it ever fetched of a URL and never refetches, so all
  four images now travel under versioned file names (`*-v2.png`); the images
  themselves are unchanged.

## [1.4.0] - 2026-10-06

### Added

- Performance profiles: Economy (the default, unchanged behaviour), Standard
  and Performance, each behind a hardware pre-check; under Standard and
  Performance, OCR can run in several slots, as many as the box carries.
- Search model choice: int8 stays built in, the more accurate fp32 can be
  chosen under Standard and Performance and is then downloaded once, with a
  digest check.
- `FINDLING_MAX_CELLS`: a whole number cap of cells per spreadsheet file
  (default 200000); a larger file is skipped with the reason `too_many_cells`
  instead of indexed in part (#21).

### Changed

- Reading and OCR processes run at lowered priority and are the first
  candidates for the kernel's out-of-memory killer; a reading process killed
  from outside is retried instead of recorded as damaged (#15, #18, #19).
- macOS AppleDouble files (`._*`) and Office lock files (`~$*`) are skipped as
  "System or helper file" and leave the index (#18, #22).
- A download that arrives shorter than the file is retried instead of
  recorded as damaged (#18).
- After the upgrade, a one time re-check hands the affected old stock back to
  the queue once; no full reindex is needed.

## [1.3.2] - 2026-09-30

### Fixed

- The backend routes that return indexed content (search and snippets) are no
  longer listed as reachable from the browser, and the extraction sandbox
  declares `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` with the measured image
  threshold. Thanks to andrewyager for the report and the fix (#20).

## [1.3.1] - 2026-09-29

### Fixed

- Files in team folders (groupfolders) whose advanced permissions grant read
  but not share are now indexed and found by their members; the update
  requeues the files that were skipped as unreadable once; the admin error
  list shows the file id of every entry and diagnoses by id. Thanks to
  budachst for the report (#14).

## [1.3.0] - 2026-09-27

### Fixed

- Files in team folders (groupfolders) that were wrongly skipped as deleted
  are now indexed; the update requeues the affected entries once. Thanks to
  budachst for the report (#14).

## [1.2.0] - 2026-09-21

### Added

- Nine OCR languages available; German, English and French stay the default.

### Changed

- The one measured figure in the store texts and READMEs is now the resident
  memory after an index run: 731.9 MB, measured on arm64 against the shipped
  image, under the hard 2 GB limit.

## [1.1.0] - 2026-09-11

### Added

- French: store texts, README.fr.md and the interface catalogues.
- Formal German (`de_DE`) interface catalogue.

### Changed

- Idle base load fell from 691.8 MB in v1.0 to 103.2 MB, minus 85.1 per cent
  (measured 2026-09-10).

## [1.0.0] - 2026-09-07

### Added

- First App Store release: full text search and semantic search in the normal
  Nextcloud search bar, OCR for scanned PDFs and images, zero configuration,
  and every result permission checked by Nextcloud. The patch releases 1.0.1
  to 1.0.3 of the same days carried store metadata and packaging fixes.

[1.4.1]: https://github.com/street1983nk/nextcloud-search/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.3.2...v1.4.0
[1.3.2]: https://github.com/street1983nk/nextcloud-search/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/street1983nk/nextcloud-search/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.0.3...v1.1.0
[1.0.0]: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.0.0
