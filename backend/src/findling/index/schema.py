"""The nine fields of the index, with the reason for every column of the table.

A tantivy schema is written once and read for the lifetime of the index: a field
that is added later means a reindex, and a field that is stored without being
needed is paid for on every disk of every installation. So this module is a table
with nine rows and a line of reasoning per row, and nothing else.

Two decisions carry real cost and are therefore measured rather than argued.

*body_de is stored.* The SnippetGenerator reads the text out of the stored
document, so the index holds one full copy of the extracted text. Measured: the
index grows to 0.374 times the extracted text with the store and to 0.076 times
without it, roughly 2100 byte per 600 word document. Projected for 100000 files
with 15 kB of text on average: about 560 MB of index directory. That the full
document text therefore lies inside the app volume is a deliberate trade for
snippets, and it belongs in the privacy statement rather than in a comment
(T-02-67, plan 02-07).

*body_en is not stored.* It carries the same text through the English pipeline,
so a second store would buy nothing but the 0.374 factor a second time.

The tokenizer names below are names only. The schema persists the name, never the
analyzer, which is why :mod:`findling.index.open` is the only place that opens an
index and why it registers before it hands the index out.
"""

from typing import Final

from tantivy import Schema, SchemaBuilder

from findling.index.analyzer import TOKENIZER_DE, TOKENIZER_EN, TOKENIZER_NAME

FIELD_FILE_ID: Final = "file_id"
FIELD_STORAGE_ID: Final = "storage_id"
FIELD_NAME: Final = "name"
FIELD_TITLE: Final = "title"
FIELD_PATH: Final = "path"
FIELD_EXT: Final = "ext"
FIELD_BODY_DE: Final = "body_de"
FIELD_BODY_EN: Final = "body_en"
FIELD_MTIME: Final = "mtime"

# In schema order. Callers that build documents read the names from here, because
# a field name that is written as a literal is a field name that is misspelled
# once: measured, Document.from_dict silently drops a name the schema does not
# know, and the value is gone without a single error anywhere.
FIELDS: Final = (
    FIELD_FILE_ID,
    FIELD_STORAGE_ID,
    FIELD_NAME,
    FIELD_TITLE,
    FIELD_PATH,
    FIELD_EXT,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_MTIME,
)

# Built into tantivy: one token, the whole field, unchanged. The right choice for
# a value that is compared and never read, such as a file extension.
TOKENIZER_RAW: Final = "raw"

# A chain that produces no token at all, registered by findling.index.open.
# tantivy's Python bindings cannot express a text field that is stored without
# being indexed: index_option accepts only basic, freq and position, and there is
# no way to leave the indexing options off. A field whose analyzer returns the
# empty token list is the same thing in practice, and it is the same thing where
# it matters: no posting is written, and no query of any shape matches it.
TOKENIZER_STORED_ONLY: Final = "stored_only"

# Terms only, no frequencies and no positions. Enough for an exact match on a
# field that nobody phrase searches, and it keeps the posting list minimal.
INDEX_OPTION_TERMS_ONLY: Final = "basic"


def build_schema() -> Schema:
    """Return the schema of the Findling index.

    Called exactly once per index directory, at creation time. Afterwards the
    schema is read back out of the index, which is why changing a line here means
    raising ``SCHEMA_VERSION`` in :mod:`findling.config` and reindexing rather
    than editing an index in place.
    """
    builder = SchemaBuilder()

    # The key. Indexed because delete_documents_by_term deletes through it, fast
    # because the search path reads it back for every hit without touching the
    # document store, stored so that a diagnosis can read a document on its own.
    builder.add_unsigned_field(FIELD_FILE_ID, stored=True, indexed=True, fast=True)
    # Held back for the mount prefilter of phase 5. It costs one column now and
    # would cost a full reindex later, which is the whole argument for it.
    builder.add_unsigned_field(FIELD_STORAGE_ID, stored=True, indexed=True, fast=True)
    # The file name, SRCH-03 "file name instead of content". Its own chain: folded
    # but neither stemmed nor stripped of stopwords, because a name is looked for
    # the way it is written.
    builder.add_text_field(FIELD_NAME, stored=True, tokenizer_name=TOKENIZER_NAME)
    # The document title from the metadata. German chain, weighted higher than the
    # body at query time, so it needs the same tokenisation as the body.
    builder.add_text_field(FIELD_TITLE, stored=True, tokenizer_name=TOKENIZER_DE)
    # Display and diagnosis, never a search term. Paths are not words: indexing
    # them would put every directory name into the term dictionary and let a
    # search for a common folder name outrank the content it was looking for.
    builder.add_text_field(FIELD_PATH, stored=True, tokenizer_name=TOKENIZER_STORED_ONLY)
    # SRCH-03 file type, measured as ext:pdf. One exact term, no analysis.
    builder.add_text_field(FIELD_EXT, stored=True, tokenizer_name=TOKENIZER_RAW, index_option=INDEX_OPTION_TERMS_ONLY)
    # The content, and the only stored copy of the text in the whole system. It
    # keeps positions because phrase queries and the snippet generator need them.
    builder.add_text_field(FIELD_BODY_DE, stored=True, tokenizer_name=TOKENIZER_DE)
    # The same text through the English pipeline. Not stored: the copy above is
    # the one snippets are cut from, and a second one would double the store.
    builder.add_text_field(FIELD_BODY_EN, stored=False, tokenizer_name=TOKENIZER_EN)
    # Display today, sorting and since/until later. Fast rather than indexed: a
    # range over a column is what a date filter needs, a term is not.
    builder.add_integer_field(FIELD_MTIME, stored=True, indexed=False, fast=True)

    return builder.build()
