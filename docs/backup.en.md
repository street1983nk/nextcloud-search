[Deutsch](backup.md) | English | [Français](backup.fr.md)

# Backing up Findling

Two ways to back up the index volume consistently (issue #37).

## What lives where

- Settings (exclusions, size limit, Team Folders, External Storage, the pause wish) live in the
  `appconfig` of the Nextcloud database. Your regular Nextcloud database backup covers them.
- The volume `nc_app_findling_backend_data` holds `state.db`, `vectors.db` and the search index.
- The volume can be rebuilt completely from your files. A backup only saves the time for OCR and
  embeddings.
- The index contains the extracted text of your documents unencrypted. Protect the backup like your
  file backup (encrypted, access-restricted).

## Route A: stop the container

1. `docker stop nc_app_findling_backend`
2. Copy the volume `nc_app_findling_backend_data` (tar or your backup tool)
3. `docker start nc_app_findling_backend`

- The container closes the index and the databases cleanly on stop.
- Search is unavailable meanwhile.

## Route B: pause, search keeps working

1. `occ findling:pause --wait` returns only once the status says paused. Or set the switch "Pause
   indexing" on the admin page and wait until it says paused ([admin-page.md](admin-page.md)).
2. Copy the volume `nc_app_findling_backend_data`.
3. `occ findling:resume` or the switch "Resume indexing".

- When paused, indexing stops and everything is flushed to disk while search keeps working.
- Start the backup only at paused, not while pausing.
- Pausing lasts until the current batch is done, with OCR up to about 30 minutes.
- The pause survives restarts of the container and of Nextcloud. If the wish cannot be read yet
  after a restart, indexing stays stopped as well.
- The crawl jobs of the companion app keep running. They write only to the Nextcloud database, not
  to the volume; the queue is worked off after resuming.
- A running index rebuild stops between two bands and continues afterwards. A backup taken
  meanwhile contains two index directories ([uninstall.md](uninstall.md)).

## Restoring

1. `docker stop nc_app_findling_backend`
2. Restore the volume `nc_app_findling_backend_data`
3. `docker start nc_app_findling_backend`

- The pause wish is not in the volume but in the Nextcloud database. A restored volume follows the
  current switch; after route B, remember `occ findling:resume`.
