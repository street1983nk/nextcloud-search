[Deutsch](migrate-from-fulltextsearch.md) | English | [Français](migrate-from-fulltextsearch.fr.md)

# Switching from fulltextsearch/Elasticsearch

This page is for admins who use Nextcloud's full text search (fulltextsearch) with Elasticsearch or
another platform app and want to switch to Findling. Findling brings full text search, semantic
search and OCR without changing files and without Elasticsearch in one container, and its results
appear in the normal search bar.

As of: 19 October 2026

## What Findling brings

- Full text search with German word handling: compounds, inflection, umlauts
  ([german-analyzer.md](german-analyzer.md))
- OCR for scanned PDFs and images; the recognised text goes into the index only, the file stays
  unchanged ([ocr.md](ocr.md))
- Semantic search: finds documents through paraphrases ([embeddings.md](embeddings.md))
- File types from PDF and office documents to mails (EML), the contents of ZIP files, DOC, XLS and
  HEIC ([formats.md](formats.md))
- Filters by file type and folder in the search bar ([search-filters.md](search-filters.md))
- Exclusion of folders and patterns on the administration page ([admin-page.md](admin-page.md))
- Every result is permission-checked by Nextcloud ([privacy.md](privacy.md))
- No configuration: the first index run starts on its own ([admin-page.md](admin-page.md))
- Performance profiles Economy, Standard and Performance ([profiles.md](profiles.md))

## What changes when you switch

- **Deck cards:** Deck hands its cards to fulltextsearch
  ([source](https://github.com/nextcloud/deck/blob/main/appinfo/info.xml)). Findling indexes files
  only. After the switch, Deck cards are no longer in a full text index; Deck's own search stays.
- **External storage:** off by default in Findling, Team Folders on. Switch it on with "Index
  external storage" on the administration page ([admin-page.md](admin-page.md)).
- **Requirements:** Nextcloud 33 to 35 with the AppAPI app and HaRP as the deploy target (Docker).
  Findling consists of two store entries, `findling` and `findling_backend`, always in the same
  version. One container runs instead of a search service.
- **Search bar:** Findling's results appear in the group "File contents", no longer in the group of
  fulltextsearch ("Full Text Search").

## Maintenance status of fulltextsearch

fulltextsearch is maintained by Nextcloud. This page describes the switch, it does not judge the
app. Queried on 19 October 2026 from the App Store and GitHub:

- fulltextsearch: release [v35.0.0](https://github.com/nextcloud/fulltextsearch/releases) on
  20.09.2026; in the [App Store](https://apps.nextcloud.com/apps/fulltextsearch) 33.0.3
  (20.09.2026) for Nextcloud 33 to 35, plus 34.0.2 and 35.0.0 (18.09.2026)
- files_fulltextsearch: in the [App Store](https://apps.nextcloud.com/apps/files_fulltextsearch)
  34.0.1 (06.08.2026) for Nextcloud 34 and 35.0.0 (18.09.2026) for Nextcloud 35
- fulltextsearch_elasticsearch: releases
  [v35.0.1 and v34.0.3](https://github.com/nextcloud/fulltextsearch_elasticsearch/releases) on
  07.10.2026; this platform app needs an Elasticsearch service
- files_fulltextsearch_tesseract, the OCR of the fulltextsearch stack: in the
  [App Store](https://apps.nextcloud.com/apps/files_fulltextsearch_tesseract) only one release for
  Nextcloud 32 (32.0.0, 19.01.2026), none for Nextcloud 33 to 35
- Third-party platform apps without a search service:
  [fulltextsearch_sql](https://apps.nextcloud.com/apps/fulltextsearch_sql) 1.5.1 (14.10.2026) and
  [fulltextsearch_postgresql](https://apps.nextcloud.com/apps/fulltextsearch_postgresql) 0.1.4
  (10.10.2026)

## Steps

Keep the order: Findling first, then switch off, so the search is never empty.

1. Install Findling (both store entries) and wait for the first index run; the coverage on the
   administration page shows how far it is. While both systems run, the administration page shows
   a notice.
2. Stop running indexing of fulltextsearch: `occ fulltextsearch:stop`. If
   `occ fulltextsearch:live` runs as a systemd service, stop and disable that service, otherwise
   systemd starts it again and again
   ([Commands](https://github.com/nextcloud/fulltextsearch/wiki/Commands),
   [Basic Installation](https://github.com/nextcloud/fulltextsearch/wiki/Basic-Installation)).
3. Delete the index while the apps and the search service still run: `occ fulltextsearch:reset`.
   The command asks for a typed confirmation. It removes the index on the platform (with
   Elasticsearch the index and the ingest pipeline) and empties the index table of fulltextsearch.
   With `--no-interaction` the command stops without asking and deletes nothing. Without a
   configured platform it ends after the confirmation with the error
   `Admin have not selected any IFullTextSearchPlatform` and deletes nothing either (checked with
   Nextcloud 34.0.3 and fulltextsearch 34.0.2).
4. Disable the apps, several in one call:
   `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch`. Instead of
   `fulltextsearch_elasticsearch` name the platform app in use, and `files_fulltextsearch_tesseract`
   if present. The next time the administration page loads, Findling's notice is gone.
5. Optionally remove the apps: `occ app:remove <app-id>`. The tables `oc_fulltextsearch_index` and
   `oc_fulltextsearch_ticks` and their entries in `oc_migrations` stay (checked with Nextcloud
   34.0.3). To remove them, back up the database first and then run these statements; `oc_` is the
   default prefix, an instance with another prefix uses its own:

   ```sql
   DROP TABLE oc_fulltextsearch_index;
   DROP TABLE oc_fulltextsearch_ticks;
   DELETE FROM oc_migrations WHERE app = 'fulltextsearch';
   ```

   A later reinstall of fulltextsearch creates the tables again.
6. Stop the Elasticsearch service outside Nextcloud and remove its data, unless it serves something
   else. With a platform app without a search service this step does not apply.
7. Nextcloud AIO: deselect the option "Fulltextsearch" in the AIO interface. AIO turns a plain
   `occ app:disable` back at the next container start as long as the option is selected
   ([entrypoint.sh](https://github.com/nextcloud/all-in-one/blob/main/Containers/nextcloud/entrypoint.sh)).
