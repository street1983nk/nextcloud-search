-- The vector half of the store: $APP_PERSISTENT_STORAGE/vectors.db
--
-- A file of its own, next to state.db and not inside it. Three reasons, and all
-- three are properties this project already relies on elsewhere. It can be
-- thrown away without losing a single full text verdict, which makes "rebuild
-- the semantic half" an rm and not a migration. It keeps the read side decision
-- of probe A12 away from state.db: the vector connection has to load a
-- shared library before it may ask anything, and state.db has no reason to be
-- able to do that at all. And vectors.py takes its path as an argument exactly
-- like repo.py does, so this choice stays reversible without a rewrite.
--
-- Like schema.sql, this file is an artifact on purpose and not a string inside
-- vectors.py: a schema gets read, diffed and quoted in bug reports, a string
-- literal gets none of that. Every statement is IF NOT EXISTS, so open_vectors
-- applies it on every start.
--
-- The connection pragmas belong to vectors.py for the same reason they belong
-- to repo.py: they are per connection settings, and query_only differs between
-- the writer and the reader.

-- The vectors themselves. int8 with 384 dimensions is D-07, and the size of
-- that decision is measured against this very schema rather than estimated:
--
--   384 byte of vector payload per chunk (384 dimensions, one byte each)
--   2 chunks per document at the 1024 token cap of D-01. Measured against
--   the shipped tokenizer on 2026-09-05 (plan 06-05) it is 2 to 3, because
--   the splitter cuts on sentence boundaries and the remainder becomes a
--   chunk of its own. The figures below are therefore a floor; the upper
--   end and the scan latency that goes with it stand in docs/embeddings.md
--   100136 chunks over the 50068 documents of the measured corpus
--   43859968 byte on disk, so 438.0 byte per chunk, 876.0 byte per document
--   and 54.0 byte of overhead per chunk (measured 2026-09-05; the phase
--   research had estimated 432, 864 and 48)
--   5.8 percent of the 761374910 byte tantivy index of the same corpus
--
-- The full calculation, the command line of that measurement and the two
-- fallback paths that are deliberately not built stand in docs/embeddings.md.
-- What a full brute force scan reads is the payload alone: 38.4 MB, measured at
-- 37.8 ms p95 warm and 153.5 ms p95 cold on native aarch64
-- (docs/measurements/2026-09-05-welle0-arm64/).
--
-- No index and no ORDER BY on this table. vec0 answers a KNN query itself, and
-- the k of that query is a constraint in the WHERE clause rather than a LIMIT;
-- the module is the only place that knows this, which is the point of D-08.
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(embedding int8[384]);

-- The bridge from a vector back to a document and to a place in its text.
-- chunk_id is the rowid of the row above, which is what makes the two tables one
-- record split over two storage engines.
--
-- char_start and char_end are CHARACTER offsets into the stored body_de, never
-- byte offsets. The distinction is not pedantic here: this project has measured
-- the confusion once already (index/search.py: the engine reports (35, 51)
-- where the character range is (35, 50)), and an offset in the wrong unit cuts
-- every semantic snippet in the wrong place, silently and only in documents
-- that carry non ascii text, which in German is all of them.
--
-- Why they exist at all: a purely semantic hit has by definition no literal
-- overlap with the query, so the SnippetGenerator returns an empty fragment and
-- the user sees a hit without any preview. For semantic hits that is the normal
-- case and not the exception (D-13).
--
-- No foreign key to files on purpose, and for a stronger reason than the acl
-- table has: that table lives in another database file, so a constraint here
-- would not be enforceable at all. The delete paths are explicit calls
-- (drop_vectors, forget_all, replace_chunks) and they are wired into the delete
-- path of the container in plan 06-07.
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   INTEGER PRIMARY KEY,          -- equals the rowid in chunk_vectors
    file_id    INTEGER NOT NULL,             -- the Nextcloud fileid, as everywhere
    ordinal    INTEGER NOT NULL,             -- position of the chunk in the document
    char_start INTEGER NOT NULL,             -- characters, not bytes
    char_end   INTEGER NOT NULL              -- characters, not bytes
);

-- The delete path asks by file_id, which the primary key cannot answer: it
-- leads with chunk_id. Without this index, forgetting one file would scan the
-- whole table, and the delete path runs once per changed, renamed or unshared
-- document.
CREATE INDEX IF NOT EXISTS chunks_file ON chunks (file_id);
