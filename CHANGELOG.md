# Changelog

All notable changes to Findling (the `findling` companion app and the
`findling_backend` External App) are documented here. Both apps carry the
same version. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.6.0] - 2026-10-28

### Added

- Discussion link to the forum thread in the store (both apps).
- Coverage on the admin page counts SMB and SFTP mounts with a per-user
  login once per share.
- A sentence on the admin page when nothing is left out on purpose.
- A hint on the admin page after a change of the exclusion rules, until
  the recount under the new rules is through.
- The tunnel watcher reports a reissued HaRP certificate, or a run of
  failed logins after one, with the remedy, and takes over new files under
  /certs/frp without a new registration or a container restart
  (docs/harp-tunnel.md).

### Changed

- The sentence about counting per mount no longer claims the search holds
  every file once.
- Dependencies: fastapi 0.161.1, pypdf 6.21.2, striprtf 0.0.34.

### Fixed

- A document with an XML element named "amplification" is no longer
  blocked as malicious.

### Security

- filelock 4.2.4 (CVE-2026-112907, -112913, -112940).

## [1.5.1] - 2026-10-22

### Changed

- Store name of the companion app is now "Findling Search" (de: "Findling
  Suche", fr: "Findling Recherche"); the navigation entry stays "Findling".
  No functional changes.

### Security

- pypdf 6.21.1 (CVE-2026-113786, -113789, -113790, -113791) and
  opentelemetry-api 1.45.1 (CVE-2026-114603).

## [1.5.0] - 2026-10-21

### Added

- Mails (.eml): subject, sender, recipients, text and the names of
  attachments; attachment content is not read.
- ZIP files: the text of the files inside, without OCR, within fixed limits
  (docs/formats.md); a ZIP file stands in no type filter group.
- Word 97 to 2003 (.doc) and Excel 97 to 2003 (.xls), read without
  LibreOffice; .xls under the cell limit of XLSX.
- HEIC and HEIF photos through OCR.
- The excerpt of a hit inside a ZIP file names the inner file.
- A one time catch up after the upgrade, without a full reindex: files of
  the new types, old Word and Excel files under OOXML names, and files given
  up as repeatedly stuck are read once more.
- Czech as a search language, without stemming, and Czech OCR; OCR
  offers ten languages (docs/language-analyzers.md).
- Unified search: filter Findling hits by type group (six entries) or by
  folder, sub folders included; unknown values are ignored
  (docs/search-filters.md).
- Exclusion patterns with `*` and `?` on the admin page, for example Mac
  bundles (`*.photoslibrary`) or build folders (`*/node_modules/*`); existing
  folder exclusions keep working. At most 32 patterns of 60 characters
  (docs/admin-page.md) (#22).
- The admin page shows the limits per file read only, with how to change
  them (#21).
- A migration page from fulltextsearch/Elasticsearch in German, English and
  French (docs/migrate-from-fulltextsearch.md).
- A banner on the admin page while fulltextsearch or files_fulltextsearch is
  enabled, with a link to that page.
- Similar documents: a link at every hit on the results page lists up
  to ten files with related content, only files the user can read.
- Hostile files end as skipped with the new code blocked_malicious and
  a detail code on the admin page (zip_ratio, zip_overlap, zip_traversal,
  package_entries, xml_entities, image_pixels, mail_nesting, cfb_cycle);
  files that are only large keep their old verdict (docs/formats.md).
- Index hygiene: documents of deleted users and deleted storages leave
  the index at the next reconcile; a storage that still exists in Nextcloud
  but is no longer mounted leaves after 30 days.
- Releases carry the source of the tag and the four corresponding
  source packages of the native libraries in the image.

### Changed

- Files under a rule leave the index at the next reconcile even when they
  did not change, and their old entries leave the error list (#22).
- The hint about too little hardware for a profile is reworded in all
  languages.
- The httpx and httpcore loggers run at WARNING in the image, so file
  ids and user ids no longer appear in the standard log; DEBUG still shows
  them.
- Store texts: the Standard profile frees at most half of the machine
  the backend runs on (was: half of the box).

### Fixed

- A file whose size in Nextcloud's file cache is larger than the file is now
  read when two downloads agree, instead of ending as repeatedly stuck
  (POL-02, F-29-03).

## [1.4.3] - 2026-10-12

### Fixed

- Result page: scrolling works again when results exceed the window height
  (#27).

## [1.4.2] - 2026-10-09

### Fixed

- The coverage denominator no longer counts storages that left the mount
  list: frozen rows of an old mount configuration padded it forever and the
  page answered 7 per cent on an instance whose coverage was complete (#25).
  The rows themselves stay, only the figure stops reading them.
- When external storages are mounted once per user, the same share is
  counted once per mount. The page now says so, in a sentence that appears
  only when everything is settled and a gap remains; a real dedup per mount
  configuration is a candidate for 1.5 because it has to answer the ACL
  question first (#25).

### Added

- SECURITY.md with the two private reporting channels, CONTRIBUTING.md, and
  issue and pull request templates.
- CI security scans: CodeQL over the Python half and pip-audit over the
  locked dependency set, weekly on top of every push.
- This changelog; it travels with both store archives from the next release.
- docs/privacy.md: what is stored where, who can read it, the remedies (host
  disk encryption, a deliberate backup policy), and why the app does not
  roll its own index encryption. The READMEs also name the lockstep guard:
  on a major or minor version mismatch between the two apps, the search
  answers with nothing instead of possibly wrong results.
- A weekly OpenSSF Scorecard run that publishes its result; the README
  carries the badge.

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

[1.5.1]: https://github.com/street1983nk/nextcloud-search/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.4.3...v1.5.0
[1.4.3]: https://github.com/street1983nk/nextcloud-search/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/street1983nk/nextcloud-search/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/street1983nk/nextcloud-search/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.3.2...v1.4.0
[1.3.2]: https://github.com/street1983nk/nextcloud-search/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/street1983nk/nextcloud-search/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/street1983nk/nextcloud-search/compare/v1.0.3...v1.1.0
[1.0.0]: https://github.com/street1983nk/nextcloud-search/releases/tag/v1.0.0
