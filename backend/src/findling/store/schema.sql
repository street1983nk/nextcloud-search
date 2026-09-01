-- The operating state of Findling: $APP_PERSISTENT_STORAGE/state.db
--
-- This file is an artifact on purpose and not a string inside repo.py. A schema
-- gets read, diffed and quoted in bug reports; a string literal gets none of
-- that. Every statement is IF NOT EXISTS, so applying it to an existing database
-- is a no-op and open_store can run it on every start.
--
-- The connection pragmas that belong to this database live in repo.py and not
-- here, for two reasons. They are per connection settings (query_only differs
-- between the writer and the reader), and journal_mode returns a value that has
-- to be evaluated: WAL needs shared memory, some file systems silently fall back
-- to DELETE, and a script that throws its result away could not notice.
--
-- What is deliberately absent: a work queue. Nextcloud owns the list of what is
-- still to do, and the crawl cursor lives in the argument of the next background
-- job. An open state here would be a second place that claims to know the
-- backlog, and the two would drift apart on the first hard kill.

-- The version marks. Every one of them can invalidate the Tantivy index on its
-- own: schema_version, index_version, analyzer_version, wordlist_hash,
-- tantivy_version, plus instance_id and created_at for provenance. Their names
-- are open on purpose, because phase 6 adds an embedding version and must not
-- need a migration to do so.
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- One row per file that has been judged. A file that is still to be processed
-- has no row here at all, which is why there is no fourth, open state: absence means
-- "not judged yet", and the queue that holds it lives in Nextcloud.
--
-- etag, ocr_used and deleted_at stay empty in phase 2. They exist now so that
-- phase 3 (events, ETag reconcile, deletions, OCR) does not have to migrate a
-- table that by then holds a hundred thousand rows on somebody's box.
--
-- reason is a code from the closed list in repo.py, never free text: these
-- values reach an admin page in phase 4, and a free field is the shortest path
-- to a file name in a place where no file name may appear.
CREATE TABLE IF NOT EXISTS files (
    file_id       INTEGER PRIMARY KEY,          -- the Nextcloud fileid, not a local one
    storage_id    INTEGER NOT NULL,
    root_id       INTEGER NOT NULL,
    path          TEXT    NOT NULL,
    title         TEXT,
    mime          TEXT    NOT NULL,
    size          INTEGER NOT NULL,
    mtime         INTEGER NOT NULL,
    etag          TEXT,                         -- phase 3 fills it
    content_hash  TEXT,                         -- lets an unchanged file skip the whole pipeline
    text_chars    INTEGER NOT NULL DEFAULT 0,
    state         TEXT    NOT NULL,             -- indexed | skipped | failed
    reason        TEXT,                         -- reason code, never a file name
    attempts      INTEGER NOT NULL DEFAULT 0,   -- the basis for giving up after three tries
    ocr_used      INTEGER NOT NULL DEFAULT 0,   -- phase 3, created now
    indexed_at    INTEGER,
    index_version INTEGER NOT NULL DEFAULT 0,
    deleted_at    INTEGER                       -- tombstone, written by Store.tombstone
);

-- files_state carries the status page: three counters over a hundred thousand
-- rows. files_storage carries the per mount view and the reset of one storage.
CREATE INDEX IF NOT EXISTS files_state   ON files (state);
CREATE INDEX IF NOT EXISTS files_storage ON files (storage_id);

-- The prefilter table. It carries no rowid because the composite key *is* the table:
-- an ordinary table would keep a second B-tree on an invisible rowid and pay for
-- it twice, once in space and once on every insert. Measured at 100k files and
-- 50 users: 335515 rows, 12.0 MB, 0.18 ms for a prefilter over 400 candidates.
--
-- No foreign key to files on purpose. Permissions arrive from the PHP crawl and
-- a file may be known to the ACL before it has been judged; a constraint here
-- would turn that ordinary race into an error.
CREATE TABLE IF NOT EXISTS acl (
    uid     TEXT    NOT NULL,
    file_id INTEGER NOT NULL,
    PRIMARY KEY (uid, file_id)
) WITHOUT ROWID;

-- The delete path asks by file_id, which the composite key cannot answer: its
-- leading column is uid. Without this index, forgetting one file would scan the
-- whole table.
CREATE INDEX IF NOT EXISTS acl_file ON acl (file_id);

-- The bookmark of the ETag reconcile, and the one table in this file that seems
-- to argue with the header above. It does not: what stands here is not a work
-- stock, it is a place in a walk. The list of what exists still lives in
-- Nextcloud, and this table only remembers which file id the last page of a
-- mount ended on, so that the next round does not start from the front again.
--
-- Losing it therefore costs a repetition and never work. The reconcile is pure,
-- idempotent repair: it reads the file list, compares, and turns differences
-- into queue jobs. A forgotten bookmark makes the next cycle walk a mount it had
-- already walked, which is slow and correct, while a forgotten crawl cursor
-- would be a document nobody ever indexes. That difference is the entire reason
-- this cursor may live in the container while the crawl cursor may not; the
-- argument is written out in docs/reconcile.md.
--
-- after_file_id back at 0 together with a finished_at is what "this mount is
-- done" means. started_at dates the walk that is running for a support case.
CREATE TABLE IF NOT EXISTS reconcile (
    storage_id    INTEGER PRIMARY KEY,
    after_file_id INTEGER NOT NULL DEFAULT 0,   -- 0 plus finished_at means: done
    started_at    INTEGER,
    finished_at   INTEGER
);

-- A mirror for the display, nothing else. The original of the crawl progress is
-- the last_file_id in the argument of the next StorageCrawlJob in Nextcloud, so
-- a container that loses this table loses a status number and no work.
CREATE TABLE IF NOT EXISTS mounts (
    storage_id     INTEGER PRIMARY KEY,
    root_id        INTEGER NOT NULL,
    cursor_file_id INTEGER NOT NULL DEFAULT 0,   -- mirror, PHP owns the original
    files_seen     INTEGER NOT NULL DEFAULT 0,
    updated_at     INTEGER NOT NULL
);
