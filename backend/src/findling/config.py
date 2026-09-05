# ANALYZER_VERSION is deliberately not in this module. It lives in
# findling/index/analyzer.py, directly next to the filter chain it versions,
# because a version number that sits away from the thing it describes is a
# version number that stops being raised.
"""The single home of every cap and every path of phase 2, and of the OCR caps
of phase 3.

Seven later plans read the same numbers. A second place holding the same number
is an operational fault in slow motion: the two copies agree on the day they are
written and disagree on the day one of them is tuned. So every cap is a named
constant here, every number carries the line of reasoning that produced it, and
nothing outside this module writes a literal for a limit.

Two design rules hold throughout.

*Unusable input never stops the container.* Numbers arrive from environment
variables that an admin edits by hand in the Nextcloud app settings. A typo in
``FINDLING_MAX_TEXT_CHARS`` must degrade to the measured default with a warning,
not into a crash loop on a box where nobody reads the boot log (T-02-13).

*The log names variables, never values.* The analysis path carries user content,
and a warning that echoes what somebody typed is the cheapest way to leak it
(T-02-14).
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

LOGGER = logging.getLogger("findling.config")

# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

# Layout of the tantivy schema. Raised when a field is added, removed or retyped;
# every raise forces a visible reindex rather than a silently mixed index.
SCHEMA_VERSION = 1

# Layout of the on disk index directory, including the tantivy index format.
# tantivy 0.26.0 reports index_format v7 and does not promise stability across
# its own releases, so this is persisted and checked on open.
INDEX_VERSION = 1

# ---------------------------------------------------------------------------
# Architecture, not configuration
# ---------------------------------------------------------------------------

# IDX-08. One indexing worker, always. OCR peaks at 300 to 600 MB for a single
# 300 dpi A4 page, and the embedding side adds two costs on top of it that are
# worth naming apart, because only one of them is measured today:
#
#   the model weights, 118101091 byte of int8 ONNX, measured in the shipping
#   image on 2026-09-05 (plan 06-01, quantisation 470268510 to 118101091 byte).
#   They are a resident load from the first embedding call on, not a peak.
#
#   the activations on top of them, which are a peak and are NOT measured. The
#   250 to 400 MB this comment used to name came from research/STACK.md and
#   describe batch 8 at sequence 512. Wave 0 measured time and not memory and
#   says so (docs/measurements/2026-09-05-welle0-arm64/README.md, 2026-09-05,
#   "Die RAM-Spitze beim Einbetten": A5 stays an estimate). What is decided by
#   measurement is the shape the peak is produced under, EMBED_BATCH_SIZE below,
#   and the number itself belongs to the load test of the second track.
#
# On the 4 GB box this project targets, the OCR peak and the embedding peak must
# never be allowed to meet, and the unmeasured half of that sentence is the
# reason this stays at one. This is not a tuning knob and deliberately reads no
# environment variable, so that making it one is a code change somebody has to
# defend in review.
INDEX_WORKERS = 1

# ---------------------------------------------------------------------------
# Language
# ---------------------------------------------------------------------------

# Field order of the schema, not the order somebody types into the environment.
DEFAULT_LANGUAGES = ("de", "en")

# The two measured recipes of the constituent dictionary. full is recipe A
# (276496 entries, 14 of 16 test compounds), nouns is recipe C (86345 entries,
# 12 of 16) for boxes where the roughly 23 MB of the automaton hurt.
COMPOUND_DICT_VARIANTS = ("full", "nouns")
DEFAULT_COMPOUND_DICT = "full"

# ---------------------------------------------------------------------------
# Caps. Every number comes from the measurement table of the phase research.
# ---------------------------------------------------------------------------

# 50 MB. Enforced during the PHP crawl, at the moment a file is queued, because
# a file that is never queued costs the container nothing at all.
MAX_FILE_BYTES = 52_428_800

# One pull from the queue: at most 32 files or 64 MB, whichever comes first. The
# byte cap is the one that matters; 32 scanned PDFs are a different workload from
# 32 text files.
#
# The byte cap is also the knob for "the search hangs while the indexer commits",
# because it decides how much a single commit has to fsync. Plan 02-13 measured
# whether it has to be turned, in the shipping image on a disk throttled to
# 2 MB/s with docker run --device-write-bps, 200 searches per run:
#
#     p95 idle          0.196 ms
#     p95 under write   0.166 to 0.216 ms over three runs
#
# The two are indistinguishable, so the value stays at 64 MB. What the throttle
# does slow down is the writer, not the reader: the same measurement window holds
# 12 commits instead of 19. Smaller batches would buy nothing here and would cost
# more segments and more merges. The measurement job in .github/workflows/
# resilience.yml keeps producing both numbers, so the day this stops being true
# is a day somebody can see.
BATCH_FILES = 32
BATCH_MAX_BYTES = 67_108_864

# Wall clock budget of one extraction, enforced by Process.join(timeout) followed
# by kill(). Only kill() reliably ends a hung C extension.
EXTRACT_TIMEOUT_SECONDS = 120

# 512 MB address space for the extraction child, via RLIMIT_AS. Measured: 300 MB
# already produces MemoryError inside the child, so this leaves headroom while
# still bounding a runaway document.
EXTRACT_ADDRESS_SPACE_BYTES = 536_870_912

# Recycling threshold of the extraction child (plan 02-05). C extensions
# fragment their heap; a child that is replaced after 200 files never gets the
# chance to grow into the box.
EXTRACT_WORKER_MAX_FILES = 200

# 512 kB of characters per document, after which the state becomes truncated. A
# single 50 MB PDF would otherwise dominate the index on its own.
MAX_TEXT_CHARS = 524_288

# Cells per spreadsheet, counted inside the iter_rows loop. One export file with
# a million rows is the classic way to tip a small container over.
MAX_CELLS = 200_000

# Pages per PDF, after which the loop stops and the state becomes truncated.
MAX_PDF_PAGES = 500

# 500 MB of free disk before a commit. Below it the indexer goes to
# paused_low_disk instead of filling the volume the user's data lives on.
MIN_FREE_BYTES = 524_288_000

# tantivy writer heap. Below roughly 15 MB tantivy refuses outright; 50 MB is the
# measured small box setting that keeps the writer peak inside the RAM budget.
WRITER_HEAP_BYTES = 50_000_000

# Poll backoff of the queue worker: start at 15 s when the queue runs empty and
# back off to 120 s. Slow enough to be invisible on an idle instance, fast enough
# that a newly queued file is not left waiting for minutes.
POLL_COOLDOWN_START_SECONDS = 15
POLL_COOLDOWN_MAX_SECONDS = 120

# The candidate search asks tantivy for overfetch times the requested number of
# hits and repeats at most rounds times, because the ACL prefilter and the final
# PHP recheck both remove hits after ranking.
SEARCH_OVERFETCH = 4
SEARCH_ROUNDS = 3

# Characters per snippet. The unified search subline is a single line of text.
SNIPPET_CHARS = 200

# Upper bound of the limit a caller may request, mirrored by the API model.
SEARCH_LIMIT_MAX = 100

# Upper bound of the paging offset a caller may request (security audit C1). The
# endpoints carry access_level USER, so any signed-in account reaches them with a
# free JSON body; the offset sizes the page the candidate scan has to fill, and
# an unbounded one would turn a single request into an unbounded amount of work.
# No legitimate cursor ever climbs past a full result set of overfetched,
# multi-round candidates, so this ceiling is far above any real paging depth.
SEARCH_OFFSET_MAX = SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS

# How many raw engine hits one candidate call may scan while it fills its page
# with prefiltered candidates. The cap exists for the pathological case of a user
# who may see almost nothing on an instance where almost everything matches; a
# tantivy top-k heap costs 24 bytes per slot, so the worst allocation stays in
# the low hundreds of kilobytes. Hitting the cap ends the page honestly with
# has_more=False rather than scanning without bound.
SEARCH_SCAN_MAX = 10_000

# Upper bound on the length of a query string (security audit C2/M3). The query is
# expanded per token with umlaut variants across several boosted fields and then
# run against the live index, so a megabyte-long query is seconds
# of CPU per request; and the lenient parser descends recursively on parentheses,
# so a deeply nested query overflows the native stack of the same process the ASGI
# app runs in. 512 characters is longer than any real search line.
SEARCH_QUERY_MAX_CHARS = 512

# Maximum bracket nesting a query line may carry before the recursive-descent
# parser is even entered (security audit C2). Real queries never nest this deep.
SEARCH_QUERY_MAX_DEPTH = 32

# Upper bound on the DECLARED uncompressed size of a single archive member
# before it is read (security audit M4). Office and OpenDocument files are ZIP
# archives, and a decompression bomb declares its real size in the directory:
# measured, an 815 kB ODT expanded to an 800 MB content.xml that RLIMIT_AS only
# caught after the worker slot and its timeout were already spent. Any XML part
# above this line would burst the extraction address space anyway, so skipping
# it as too_large is the honest verdict at the price of a directory read.
EXTRACT_ARCHIVE_MEMBER_MAX_BYTES = 64 * 1024 * 1024

# ---------------------------------------------------------------------------
# OCR. Every number below was measured on 2026-09-01 in the shipping image and
# is written up, with its command line, in docs/ocr.md.
# ---------------------------------------------------------------------------

# OCR is on out of the box, because "the search finds the content of scanned
# documents" is the core promise of the product and a feature an admin has to
# discover is a feature that is off on most instances.
OCR_ENABLED = True

# The languages tesseract is asked for, in the order it is asked for them: the
# first one weighs more, so this is an argument order, not the schema field
# order of DEFAULT_LANGUAGES above.
OCR_DEFAULT_LANGUAGES = ("deu", "eng")

# What the image actually carries, and therefore the only values that may ever
# reach the command line (T-03-502). Measured on 2026-09-01,
# `tesseract --list-langs` in the built image answers deu, eng and osd; osd is
# an orientation model, not a text language, so it is not offered here.
#
# This set is maintained together with the apt block in backend/Dockerfile.
# Switching on the Fraktur option means uncommenting tesseract-ocr-frk there and
# adding "frk" here, in the same change. Adding it here alone would produce a
# call that tesseract rejects on every page.
OCR_LANGUAGE_ALLOWLIST = frozenset({"deu", "eng"})

# Pages per document before the OCR loop stops and the state becomes truncated.
# 30, not the 100 that STACK.md names, and the deviation is deliberate: an OCR
# job may run up to OCR_JOB_SECONDS, QueueMapper::LOCK_TIMEOUT is 900 s, and two
# 100 page jobs in one claim would let the lock expire while work is in fact
# progressing. docs/ocr.md carries the full argument.
OCR_MAX_PAGES = 30

# Wall clock budget of a single page, enforced by subprocess.run(timeout=) in
# the child. Measured 2026-09-01: a rendered A4 page at 300 dpi takes a median
# of 1984 ms on an amd64 laptop core. The cap is fifteen times that, because the
# target hardware is a slower ARM box and a dense bad scan costs a multiple of a
# clean one. It is meant to cut off the outlier, not the normal case.
OCR_PAGE_SECONDS = 30

# Soft overall deadline inside the child. Reaching it ends the page loop and
# yields indexed(truncated), so the pages already read stay searchable.
OCR_JOB_SECONDS = 600

# How far the parent's hard deadline sits above the child's soft one. Derived
# rather than a second constant on purpose: if an admin raises the soft budget
# and the hard one stayed at its built in 660, the parent would kill the child
# before it could hand over its partial text and indexed(truncated) would stop
# occurring at all. The margin is the window in which the child pushes what it
# has through the pipe.
OCR_HARD_DEADLINE_MARGIN_SECONDS = 60

# Rendering resolution. "Tesseract works best on images which have a DPI of at
# least 300 dpi", and measured on 2026-09-01 an A4 page at 300 dpi finishes
# inside a 128 MB address space, well under the 512 MB the sandbox child grants.
OCR_DPI = 300

# The two PHP-side numbers the job ceiling below is derived from, mirrored here
# because a PHP constant cannot be imported: QueueMapper::LOCK_TIMEOUTS[ocr] and
# QueueService::KIND_BATCH[ocr]. A parity test in tests/test_config.py reads
# both out of the PHP sources and goes red the day one of them moves, the same
# construction that holds the two mimetype allowlists together.
OCR_LOCK_TIMEOUT_SECONDS = 1800
OCR_CLAIM_BATCH = 2

# The ceiling of the admin settable job budget, derived rather than chosen
# (review finding WR-04). One claim may hold OCR_CLAIM_BATCH rows, so each row
# owns OCR_LOCK_TIMEOUT_SECONDS / OCR_CLAIM_BATCH = 900 s of the claim. The
# parent's hard deadline is job plus the margin, and the download of the bytes
# runs inside the same claim, so a second margin is budgeted for it:
# 900 - 60 - 60 = 780. The old ceiling of 1800 declared a value valid at which
# a single job's hard deadline (1860 s) already outlived the lock: the rows
# reappeared as free, collected retries and ended as failed(repeatedly_stuck)
# while the engine was legitimately working, which is word for word the failure
# the bounded range exists to prevent (T-03-503).
OCR_JOB_SECONDS_MAX = OCR_LOCK_TIMEOUT_SECONDS // OCR_CLAIM_BATCH - 2 * OCR_HARD_DEADLINE_MARGIN_SECONDS

# Ranges an admin supplied number has to fall into. These are not taste: the
# rasterised page grows with the square of the dpi, so A4 at 1200 dpi is 137
# megapixels and bursts EXTRACT_ADDRESS_SPACE_BYTES, and a page or job budget
# far above the queue lock timeout reproduces exactly the stuck-claim failure
# the 30 page cap exists to avoid (T-03-503). Anything outside the range warns
# and degrades to the default.
OCR_MAX_PAGES_RANGE = (1, MAX_PDF_PAGES)
OCR_PAGE_SECONDS_RANGE = (1, 300)
OCR_JOB_SECONDS_RANGE = (1, OCR_JOB_SECONDS_MAX)
OCR_DPI_RANGE = (72, 600)

# ---------------------------------------------------------------------------
# The ETag reconcile. Events are an accelerator, never a guarantee; these five
# numbers decide how expensive the guarantee is allowed to be. The full argument,
# including why the cadence lives in the container rather than in a Nextcloud
# job, is in docs/reconcile.md.
# ---------------------------------------------------------------------------

# On out of the box. A container that only believes its events is the container
# this project was started to replace: a lost event is invisible, and the index
# stays wrong until somebody notices that a document cannot be found.
RECONCILE_ENABLED = True

# Container local hour the full cycle is preferred in. Nextcloud's own
# maintenance window is not a substitute: cron.php reads maintenance_window_start
# with the default 100 and only restricts anything at 23 or below, so a freshly
# installed instance has no maintenance window at all.
RECONCILE_HOUR = 2

# At most one full cycle per this many hours. The floor under the whole feature:
# without it the reconcile would walk the file list on every tick.
RECONCILE_MIN_INTERVAL_HOURS = 24

# Scheduled queue rows the reconcile tolerates before it stands down (D-03). One
# hundred is roughly three batches of the indexing worker: enough that ordinary
# event traffic does not block the repair, low enough that an initial index or an
# OCR backlog does.
RECONCILE_QUIET_MAX = 100

# Files per page of the file list. Matches the DEFAULT_SLICE of the PHP side, and
# the ceiling is its MAX_SLICE, which clamps anything larger anyway.
RECONCILE_SLICE = 500

RECONCILE_HOUR_RANGE = (0, 23)
RECONCILE_SLICE_RANGE = (1, 2000)

# ---------------------------------------------------------------------------
# Embeddings, phase 6. The second track: text becomes vectors after the full
# text and OCR pass, never beside it (D-15). Every number below carries where it
# came from, what a wrong value does, and the range that catches it, and the
# measured ones point at docs/measurements/2026-09-05-welle0-arm64/README.md.
#
# The whole block shares one property that the OCR block does not have: none of
# these values can fail loudly. A cap set too high buys hours of ARM time on a
# box nobody watches, a chunk larger than the window loses its tail at the
# session, and a missing model produces a search that finds less rather than an
# error. That is why every one of them has a range and a test.
# ---------------------------------------------------------------------------

# On out of the box, like OCR above and for the same reason: a feature an admin
# has to discover is a feature that is off on most instances.
#
# The honest half of D-01 belongs here rather than on the admin page. The token
# cap below is a setting and it can be turned up, but it is not advertised in
# the Nextcloud settings: it is a screw for the failure case, not a
# configuration task, and the zero config promise of this product is that nobody
# has to touch it. An operator with time and hardware who wants full embedding
# will find it in this file and in docs/embeddings.md.
EMBED_ENABLED = True

# The context window of intfloat/multilingual-e5-small. A property of the model
# and not a knob: everything past it is dropped by the session itself, without
# an error, which is why the two settings below are measured against it.
EMBED_CONTEXT_TOKENS = 512

# What the encoder puts around every text of its own accord, and therefore what
# the window has to have room for before a single word of the document fits.
# Measured in the shipping image on 2026-09-05: the tokenizer of this model adds
# two ids to an empty string, the opening and the closing marker.
#
# It is two rather than a rounder number and it still matters. A chunk of a full
# 512 content tokens would arrive at the session as 514 and lose its last two,
# silently and only in the documents whose chunks fill the window, which is the
# exact failure this whole block exists to make impossible.
EMBED_SPECIAL_TOKENS = 2

# D-01. The first 1024 tokens of a document, which is roughly one page.
#
# Measured, what this cap buys: 51269632 tokens over the 50068 documents of the
# reference corpus, so 100136 chunks, and an initial embedding run of 2 h 58 min
# to 4 h 09 min on native aarch64 instead of the 54 to 180 hours a full pass
# costs (wave 0, derivations 1 and 2, 2026-09-05). Measured, what it costs: a
# document is findable through its first 12.5 percent semantically, and through
# all of it lexically, which is the sentence D-17b puts in the store text.
#
# Turned too high it is the one setting in this file that can spend days of CPU
# on a box with two shared cores, so the ceiling of the range is not taste
# either: 8192 tokens is more than the 6691 to 8215 an average document of the
# measured corpus carries, so it already means "embed everything" for the normal
# case, and it is eight times the run time above, which lands at the day D-04
# treats as the pain threshold. Anything past it warns and falls back.
EMBED_TOKEN_CAP = 1024
EMBED_TOKEN_CAP_RANGE = (1, 8192)

# Chunk size inside that cap, and the number that decides how many rows every
# search has to scan for the rest of this product's life.
#
# 510 is the window minus what the encoder adds, so a chunk fills the model as
# far as it can be filled and never one token further. A document under the cap
# becomes two or three chunks, which is the order plan 06-04 measured its disk
# figure against (100136 chunks, 876.0 byte per document, 5.8 percent of the
# tantivy index) and the one the scan latency of wave 0 was read at (37.8 ms p95
# warm, 153.5 ms p95 cold on aarch64, against an abort criterion of 300 ms per
# round). Measured against the shipped tokenizer on 2026-09-05: a document of
# 18240 tokens capped at 1024 becomes three chunks of 500, 507 and 17 tokens,
# because the splitter cuts on sentence boundaries and the remainder is a chunk
# of its own. Two was the calculation, two to three is the measurement, and
# docs/embeddings.md carries the consequence for the disk figure.
#
# Halving it to 256 is tempting and is not done, and the trade is worth writing
# down because measurement B points the other way. At batch 2, sequence 256 is
# the fastest and leanest combination of the four measured (5700 against 3451
# tokens per second on x86, 4745 against 3640 on aarch64), so 256 would shorten
# the initial run by roughly an hour. It would also double the chunk count to
# 200000, double the vector file, double the scan every user search pays three
# times per query, and move the 250000 chunk threshold from 125000 documents
# down to 62500, which is barely above the corpus this project already measured.
# An hour paid once against a cost paid on every search forever is the wrong way
# round, so the sequence follows the chunk size here and not the other way.
EMBED_CHUNK_TOKENS = EMBED_CONTEXT_TOKENS - EMBED_SPECIAL_TOKENS
EMBED_CHUNK_TOKENS_RANGE = (16, EMBED_CONTEXT_TOKENS - EMBED_SPECIAL_TOKENS)

# Overlap between neighbouring chunks, in tokens. Zero is the default and a
# legitimate answer, which is why it has a reader of its own below: the ordinary
# one refuses zero on purpose, because a cap of nothing is a container that does
# nothing, and an overlap of nothing is simply no overlap.
#
# Zero, not a fashionable 10 percent, because the second chunk of a document
# starts at a sentence boundary the splitter chose and the cap of 1024 tokens is
# the scarce resource here: every overlapping token is a token of the document
# that does not get embedded. An operator who sees answers cut in half at chunk
# boundaries can raise it.
EMBED_CHUNK_OVERLAP = 0
EMBED_CHUNK_OVERLAP_RANGE = (0, EMBED_CONTEXT_TOKENS // 2)

# Lever 4 of 06-RESEARCH.md 3.6, and the one that shapes the activation peak:
# the research puts batch 2 at 40 to 80 MB of activations against 150 to 300 MB
# at batch 8, and it expected a small throughput loss for it. Measurement B of
# wave 0 found no loss at all: on aarch64 batch 2 and batch 8 are within
# 1.3 percent of each other at sequence 256, and on the x86 laptop batch 2 was a
# quarter faster. So the sparing choice costs nothing measurable in time, which
# is a rare shape and the reason this is 2 rather than the 8 STACK.md names.
EMBED_BATCH_SIZE = 2
EMBED_BATCH_SIZE_RANGE = (1, 32)

# Lever 5, the sequence length the session is fed. The attention matrix grows
# with its square, so halving it is a factor of four on that part of the peak
# and 37 to 40 percent of throughput (wave 0, measurement B, finding 1).
#
# It is not free to choose here, and that is the point of the coupling enforced
# in settings() below: a chunk longer than the sequence is cut at the session
# and the tail leaves the index without an error line. Whoever lowers this to
# save memory therefore lowers the chunk size with it.
EMBED_SEQUENCE_LEN = 512
EMBED_SEQUENCE_LEN_RANGE = (16, EMBED_CONTEXT_TOKENS)

# Where the model is in the shipping image, set by backend/Dockerfile as
# FINDLING_EMBED_MODEL_DIR and repeated here as the built in fallback. Outside
# the image there is usually no model at all, and that is a state and not an
# error: embed/model.py answers it with the embedding_unavailable verdict. This
# reader therefore never checks whether the directory exists, because a check
# here would move that verdict into the boot path of the container.
EMBED_MODEL_DIR = "/usr/local/share/findling/model"

# ---------------------------------------------------------------------------
# The hybrid read side, phase 6. What the merge in index/fusion.py is fed with,
# how the two halves are weighed against each other, and the one ceiling that
# keeps a user search from scanning the whole chunk stock without bound.
#
# None of the five below is advertised on the admin page, which is D-12 and the
# same rule the token cap above follows: they are screws for the failure case,
# not configuration tasks, and the zero config promise of this product is that
# nobody has to touch them.
# ---------------------------------------------------------------------------

# The rank constant of the reciprocal rank fusion. 60 is the documented default
# of the Elasticsearch implementation the formula was taken from word for word
# ("Defaults to 60", retrieved 2026-09-04), so it is a value with a source and
# not a preference.
#
# The range is tight around it because both of its ends stop being a ranking.
# Far below 60 the front ranks dominate so hard that the second list can no
# longer move a document at all; far above it every 1/(k+rank) approaches 1/k,
# the contributions of rank 1 and rank 100 stop being distinguishable, and the
# merge answers an arbitrary order while looking exactly as it always did. Ten
# times the documented default is well past the point where either is visible.
SEARCH_RRF_K = 60
SEARCH_RRF_K_RANGE = (1, 600)

# How many hits per source go into the merge at all (D-12).
#
# The reservation of D-12 belongs at this line, because this is the number it is
# about: the window interacts with the selectivity of the permission prefilter.
# Measured in the phase 2 research, 31 of 400 candidates survived it in the
# synthetic worst case, and at that selectivity a window of 100 per source
# yields fewer than ten permitted hits. The answer to that is not a deeper
# window, which pays the full ranking cost for hits nobody may see; it is the
# continuation scan behind the window in index/search.py, and that branch exists
# for this measurement and for no other reason.
#
# Bounded above by SEARCH_SCAN_MAX, because a window wider than the whole scan
# would be a promise the raw ceiling cannot keep.
SEARCH_RRF_WINDOW = 100
SEARCH_RRF_WINDOW_RANGE = (1, SEARCH_SCAN_MAX)

# The two weights the merge gives its sources. Elasticsearch has no such thing
# ("each child retriever carries an equal weight"), so both the values and their
# ranges are ours, and the two ranges are deliberately not the same.
#
# The semantic weight may be turned down to zero, which is the point of it
# existing: an administrator who sees the vector half push the wrong documents
# forward can damp it without switching the second track off, and zero is the
# far end of damping. index/fusion.py answers a weight of zero by dropping that
# list entirely rather than by scoring it with nothing, so the result set at
# zero is exactly the result set of a container without a vector stock.
#
# The lexical weight may not. Zero there would switch off the half of the search
# that always works, and the promise of criterion 3 is the opposite one: when
# the vector half is gone the answer is the unchanged full text ranking. A
# configuration value that can quietly break the fallback is not a weight, it is
# a second off switch nobody documented.
SEARCH_LEXICAL_WEIGHT = 1.0
SEARCH_LEXICAL_WEIGHT_RANGE = (0.1, 10.0)
SEARCH_SEMANTIC_WEIGHT = 1.0
SEARCH_SEMANTIC_WEIGHT_RANGE = (0.0, 10.0)

# The own ceiling of the vector half: how many chunk hits one candidate round
# may ask the vector store for.
#
# The security argument is the one SEARCH_OFFSET_MAX makes above. The endpoints
# carry access_level USER, so any signed in account reaches them with a free
# JSON body, and a vector query is not a top-k over an index: sqlite-vec visits
# every row of the stock and no parameter of that query changes it, which
# store/vectors.py::nearest states in its own docstring. With MAX_ROUNDS = 3 on
# the PHP side, mirrored here as SEARCH_ROUNDS, that scan is paid up to three
# times per user search, so it is the standard load of this container and not an
# edge case.
#
# 300, which is the window depth of 100 documents times the three chunks a
# capped document carries at most (measured 2026-09-05: two to three chunks per
# document under the 1024 token cap of D-01). Asking for more would buy a heap
# the merge cannot use, because the aggregation cuts back to the window anyway.
#
# The number this ceiling is measured against is the scan latency of wave 0: at
# 100136 chunks a full scan reads 38.4 MB and costs 37.8 ms p95 warm and
# 153.5 ms p95 cold on native aarch64, taken at k = 50
# (docs/measurements/2026-09-05-welle0-arm64/README.md, measurement C,
# 2026-09-05), against the abort criterion of 300 ms per round.
VECTOR_SCAN_MAX = 300
VECTOR_SCAN_MAX_RANGE = (1, SEARCH_SCAN_MAX)

# Subdirectory used when APP_PERSISTENT_STORAGE is absent, which is the case in
# tests and in a bare local run, never in a container deployed by AppAPI.
FALLBACK_STORAGE_DIRNAME = "findling"


@dataclass(frozen=True, slots=True)
class Settings:
    """The resolved caps and paths of one process.

    Frozen on purpose: a cap that can be reassigned at runtime is a cap that
    differs between two call sites, and the whole point of this module is that
    it cannot.
    """

    index_dir: Path
    state_db: Path
    # Beside state.db and not inside it (plan 06-04): the vector stock is
    # discardable without losing the full text half, and the ability to load a
    # binary extension stays away from the database the search reads.
    vectors_db: Path
    dict_dir: Path
    tmp_dir: Path

    languages: tuple[str, ...]
    compound_dict: str

    max_file_bytes: int
    batch_files: int
    batch_max_bytes: int
    extract_timeout_seconds: int
    extract_address_space_bytes: int
    extract_worker_max_files: int
    max_text_chars: int
    max_cells: int
    max_pdf_pages: int
    min_free_bytes: int
    writer_heap_bytes: int
    poll_cooldown_start_seconds: int
    poll_cooldown_max_seconds: int
    search_overfetch: int
    search_rounds: int
    snippet_chars: int
    search_limit_max: int
    search_rrf_k: int
    search_rrf_window: int
    search_lexical_weight: float
    search_semantic_weight: float
    vector_scan_max: int

    ocr_enabled: bool
    ocr_languages: tuple[str, ...]
    ocr_max_pages: int
    ocr_page_seconds: int
    ocr_job_seconds: int
    ocr_hard_deadline_seconds: int
    ocr_dpi: int

    reconcile_enabled: bool
    reconcile_hour: int
    reconcile_min_interval_hours: int
    reconcile_quiet_max: int
    reconcile_slice: int

    embed_enabled: bool
    embed_token_cap: int
    embed_chunk_tokens: int
    embed_chunk_overlap: int
    embed_batch_size: int
    embed_sequence_len: int
    embed_model_dir: Path


def _int_from_environment(name: str, default: int) -> int:
    """Read a positive whole number, falling back to the measured default.

    Every failure path is the same: warn with the name of the variable and use
    the default. Raising here would turn one wrong character in an admin form
    into a container that will not start, on a machine with no operator watching.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        LOGGER.warning("%s is not a whole number, falling back to the built in default", name)
        return default
    if value < 1:
        LOGGER.warning("%s is not a positive number, falling back to the built in default", name)
        return default
    return value


def _bounded_int_from_environment(name: str, default: int, bounds: tuple[int, int]) -> int:
    """Read a whole number that also has to fall inside a measured range.

    Same contract as the reader above, one condition more. A number that is
    positive but absurd is not obviously a typo to a parser and is very much one
    in practice: 1200 dpi bursts the address space of the sandbox child, and a
    job budget above the queue lock timeout makes every large scan look stuck.
    """
    value = _int_from_environment(name, default)
    low, high = bounds
    if low <= value <= high:
        return value
    LOGGER.warning("%s is outside the range this build was measured for, falling back to the default", name)
    return default


def _bounded_float_from_environment(name: str, default: float, bounds: tuple[float, float]) -> float:
    """Read a fractional number that also has to fall inside a measured range.

    The same blueprint as the reader above and the same warning behaviour: never
    a refusal to start, always the built in default.

    It does not layer on a positive-only reader the way the integer one does,
    and that is the split ``_hour_from_environment`` and
    ``_overlap_from_environment`` make below, for the same reason. Zero is a
    legitimate answer here: a semantic weight of zero is an administrator
    damping the vector half down to nothing without switching the second track
    off, and a reader that treated it as a typo would take that setting away.

    The range check does a second job for free, and it is worth naming because
    it is invisible. ``float()`` happily parses ``nan`` and ``inf``, and either
    of them would poison every score the merge produces. A comparison against a
    NaN is false in both directions, so it falls back like any other value
    outside the range, and an infinity is above every high bound this module
    hands in.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        LOGGER.warning("%s is not a number, falling back to the built in default", name)
        return default
    low, high = bounds
    if low <= value <= high:
        return value
    LOGGER.warning("%s is outside the range this build was measured for, falling back to the default", name)
    return default


def _hour_from_environment(name: str, default: int) -> int:
    """Read an hour of the day, where zero is a legitimate answer.

    The reader above refuses zero on purpose: a cap of zero is a container that
    does nothing. An hour of zero is midnight, which is the first thing an admin
    who wants a quiet night types, so this one has its own bounds and its own
    function rather than a flag on the other.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        LOGGER.warning("%s is not a whole number, falling back to the built in default", name)
        return default
    low, high = RECONCILE_HOUR_RANGE
    if low <= value <= high:
        return value
    LOGGER.warning("%s is not an hour of the day, falling back to the built in default", name)
    return default


def _overlap_from_environment(name: str, default: int, bounds: tuple[int, int]) -> int:
    """Read a whole number where zero is a legitimate answer, inside a range.

    The same split ``_hour_from_environment`` makes, for the same reason and a
    different value. ``_int_from_environment`` refuses zero because a cap of
    nothing is a container that does nothing; an overlap of nothing is simply no
    overlap, and it is the default of this build, so it may not travel through a
    reader that treats it as a typo.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        LOGGER.warning("%s is not a whole number, falling back to the built in default", name)
        return default
    low, high = bounds
    if low <= value <= high:
        return value
    LOGGER.warning("%s is outside the range this build was measured for, falling back to the default", name)
    return default


def _embed_model_dir() -> Path:
    """Return the model directory, which is an image constant with a fallback.

    No existence check on purpose. Whether there is a model behind this path is
    the question :mod:`findling.embed.model` answers with its
    ``embedding_unavailable`` verdict, and a reader that refused to resolve here
    would turn a running search without semantics into a container that does not
    start.
    """
    configured = os.environ.get("FINDLING_EMBED_MODEL_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(EMBED_MODEL_DIR)


# What an admin may type into a yes or no field. Everything else warns.
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})


def _bool_from_environment(name: str, default: bool) -> bool:
    """Read a switch, falling back to the built in position.

    Same reason as everywhere else in this module: an unreadable switch is a
    warning, never a refusal to start.
    """
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    LOGGER.warning("%s is not a yes or no value, falling back to the built in default", name)
    return default


def _storage_root() -> Path:
    """Return the root of the persistent volume, or a temp directory in its place.

    AppAPI always sets APP_PERSISTENT_STORAGE for a deployed container. The
    fallback exists for tests and for a bare local run, and it is a directory of
    our own inside the system temp directory rather than the temp directory
    itself, so that a cleanup never reaches beyond what this app created.
    """
    configured = os.environ.get("APP_PERSISTENT_STORAGE", "").strip()
    if configured:
        return Path(configured)
    return Path(tempfile.gettempdir()) / FALLBACK_STORAGE_DIRNAME


def _languages() -> tuple[str, ...]:
    """Return the active language fields, in schema order.

    An empty or unrecognisable list keeps both fields. Dropping to no language at
    all would produce an index that cannot answer anything, which is a worse
    outcome than ignoring the variable.
    """
    requested = {part.strip().lower() for part in os.environ.get("FINDLING_LANGUAGES", "").split(",")}
    kept = tuple(language for language in DEFAULT_LANGUAGES if language in requested)
    if kept:
        return kept
    if requested - {""}:
        LOGGER.warning("FINDLING_LANGUAGES names no supported language, falling back to the built in default")
    return DEFAULT_LANGUAGES


def _compound_dict() -> str:
    """Return the constituent dictionary variant, full unless nouns is asked for."""
    requested = os.environ.get("FINDLING_COMPOUND_DICT", "").strip().lower()
    if requested in COMPOUND_DICT_VARIANTS:
        return requested
    if requested:
        LOGGER.warning("FINDLING_COMPOUND_DICT is not one of the measured variants, falling back to full")
    return DEFAULT_COMPOUND_DICT


def _ocr_languages() -> tuple[str, ...]:
    """Return the OCR languages, filtered down to what this image actually has.

    Two jobs in one function. The obvious one is usability: a language the image
    does not carry makes tesseract reject every single page, so a typo would
    turn OCR off silently instead of loudly.

    The other one is the security boundary (T-03-502). This value ends up in the
    argument list of a subprocess. The call site uses a list and never a shell,
    which already closes the classic hole, but an argument that starts with a
    dash is still an option to tesseract, not a language. A closed allowlist is
    the answer that does not depend on the call site staying careful.

    Unlike ``_languages`` above, the admin's order is preserved: the schema field
    order is ours to decide, a tesseract language order is not, and the first
    language in the list is the one the engine weighs most.
    """
    raw = os.environ.get("FINDLING_OCR_LANGUAGES", "").strip()
    if not raw:
        return OCR_DEFAULT_LANGUAGES

    kept: list[str] = []
    dropped = False
    for part in raw.split("+"):
        candidate = part.strip().lower()
        if not candidate:
            continue
        if candidate not in OCR_LANGUAGE_ALLOWLIST:
            dropped = True
            continue
        if candidate not in kept:
            kept.append(candidate)

    if not kept:
        LOGGER.warning("FINDLING_OCR_LANGUAGES names no installed language, falling back to the built in default")
        return OCR_DEFAULT_LANGUAGES
    if dropped:
        LOGGER.warning("FINDLING_OCR_LANGUAGES names a language this image does not carry, ignoring that entry")
    return tuple(kept)


@lru_cache(maxsize=1)
def settings() -> Settings:
    """Resolve the settings once per process.

    Cached because the environment does not change while the process runs and
    because two callers seeing two different Settings objects would reintroduce
    exactly the drift this module exists to prevent. Tests clear the cache.
    """
    root = _storage_root()
    ocr_job_seconds = _bounded_int_from_environment("FINDLING_OCR_JOB_SECONDS", OCR_JOB_SECONDS, OCR_JOB_SECONDS_RANGE)
    embed_sequence_len = _bounded_int_from_environment(
        "FINDLING_EMBED_SEQUENCE_LEN", EMBED_SEQUENCE_LEN, EMBED_SEQUENCE_LEN_RANGE
    )
    embed_chunk_tokens = _bounded_int_from_environment(
        "FINDLING_EMBED_CHUNK_TOKENS", EMBED_CHUNK_TOKENS, EMBED_CHUNK_TOKENS_RANGE
    )
    embed_chunk_ceiling = embed_sequence_len - EMBED_SPECIAL_TOKENS
    if embed_chunk_tokens > embed_chunk_ceiling:
        # The two values are read independently and are not independent. An
        # admin who lowers the sequence to save memory and leaves the chunk size
        # alone would feed 510 token chunks into a 256 token session, and half of
        # every chunk would leave the index with nothing failing. Clamping rather
        # than falling back to the default keeps the intent of the change that
        # was made, and the warning names the variable that moved. The two
        # special tokens are subtracted here for the same reason they are
        # subtracted from the default: the encoder adds them, so they take room
        # from the document and not from the session.
        LOGGER.warning(
            "FINDLING_EMBED_CHUNK_TOKENS is larger than the sequence the session is fed, lowering it to the sequence"
        )
        embed_chunk_tokens = embed_chunk_ceiling
    embed_chunk_overlap = _overlap_from_environment(
        "FINDLING_EMBED_CHUNK_OVERLAP", EMBED_CHUNK_OVERLAP, EMBED_CHUNK_OVERLAP_RANGE
    )
    if embed_chunk_overlap >= embed_chunk_tokens:
        # An overlap that is not smaller than the chunk never advances: the
        # splitter would hand out the same window forever.
        LOGGER.warning("FINDLING_EMBED_CHUNK_OVERLAP is not smaller than the chunk, falling back to no overlap")
        embed_chunk_overlap = EMBED_CHUNK_OVERLAP
    return Settings(
        index_dir=root / "index",
        state_db=root / "state.db",
        vectors_db=root / "vectors.db",
        dict_dir=root / "dict",
        tmp_dir=root / "tmp",
        languages=_languages(),
        compound_dict=_compound_dict(),
        max_file_bytes=_int_from_environment("FINDLING_MAX_FILE_BYTES", MAX_FILE_BYTES),
        batch_files=_int_from_environment("FINDLING_BATCH_FILES", BATCH_FILES),
        batch_max_bytes=_int_from_environment("FINDLING_BATCH_MAX_BYTES", BATCH_MAX_BYTES),
        extract_timeout_seconds=_int_from_environment("FINDLING_EXTRACT_TIMEOUT_SECONDS", EXTRACT_TIMEOUT_SECONDS),
        extract_address_space_bytes=_int_from_environment(
            "FINDLING_EXTRACT_ADDRESS_SPACE_BYTES", EXTRACT_ADDRESS_SPACE_BYTES
        ),
        extract_worker_max_files=_int_from_environment("FINDLING_EXTRACT_WORKER_MAX_FILES", EXTRACT_WORKER_MAX_FILES),
        max_text_chars=_int_from_environment("FINDLING_MAX_TEXT_CHARS", MAX_TEXT_CHARS),
        max_cells=_int_from_environment("FINDLING_MAX_CELLS", MAX_CELLS),
        max_pdf_pages=_int_from_environment("FINDLING_MAX_PDF_PAGES", MAX_PDF_PAGES),
        min_free_bytes=_int_from_environment("FINDLING_MIN_FREE_BYTES", MIN_FREE_BYTES),
        writer_heap_bytes=_int_from_environment("FINDLING_WRITER_HEAP_BYTES", WRITER_HEAP_BYTES),
        poll_cooldown_start_seconds=_int_from_environment(
            "FINDLING_POLL_COOLDOWN_START_SECONDS", POLL_COOLDOWN_START_SECONDS
        ),
        poll_cooldown_max_seconds=_int_from_environment(
            "FINDLING_POLL_COOLDOWN_MAX_SECONDS", POLL_COOLDOWN_MAX_SECONDS
        ),
        search_overfetch=_int_from_environment("FINDLING_SEARCH_OVERFETCH", SEARCH_OVERFETCH),
        search_rounds=_int_from_environment("FINDLING_SEARCH_ROUNDS", SEARCH_ROUNDS),
        snippet_chars=_int_from_environment("FINDLING_SNIPPET_CHARS", SNIPPET_CHARS),
        search_limit_max=_int_from_environment("FINDLING_SEARCH_LIMIT_MAX", SEARCH_LIMIT_MAX),
        search_rrf_k=_bounded_int_from_environment("FINDLING_SEARCH_RRF_K", SEARCH_RRF_K, SEARCH_RRF_K_RANGE),
        search_rrf_window=_bounded_int_from_environment(
            "FINDLING_SEARCH_RRF_WINDOW", SEARCH_RRF_WINDOW, SEARCH_RRF_WINDOW_RANGE
        ),
        search_lexical_weight=_bounded_float_from_environment(
            "FINDLING_SEARCH_LEXICAL_WEIGHT", SEARCH_LEXICAL_WEIGHT, SEARCH_LEXICAL_WEIGHT_RANGE
        ),
        search_semantic_weight=_bounded_float_from_environment(
            "FINDLING_SEARCH_SEMANTIC_WEIGHT", SEARCH_SEMANTIC_WEIGHT, SEARCH_SEMANTIC_WEIGHT_RANGE
        ),
        vector_scan_max=_bounded_int_from_environment(
            "FINDLING_VECTOR_SCAN_MAX", VECTOR_SCAN_MAX, VECTOR_SCAN_MAX_RANGE
        ),
        ocr_enabled=_bool_from_environment("FINDLING_OCR_ENABLED", OCR_ENABLED),
        ocr_languages=_ocr_languages(),
        ocr_max_pages=_bounded_int_from_environment("FINDLING_OCR_MAX_PAGES", OCR_MAX_PAGES, OCR_MAX_PAGES_RANGE),
        ocr_page_seconds=_bounded_int_from_environment(
            "FINDLING_OCR_PAGE_SECONDS", OCR_PAGE_SECONDS, OCR_PAGE_SECONDS_RANGE
        ),
        ocr_job_seconds=ocr_job_seconds,
        ocr_hard_deadline_seconds=ocr_job_seconds + OCR_HARD_DEADLINE_MARGIN_SECONDS,
        ocr_dpi=_bounded_int_from_environment("FINDLING_OCR_DPI", OCR_DPI, OCR_DPI_RANGE),
        reconcile_enabled=_bool_from_environment("FINDLING_RECONCILE_ENABLED", RECONCILE_ENABLED),
        reconcile_hour=_hour_from_environment("FINDLING_RECONCILE_HOUR", RECONCILE_HOUR),
        reconcile_min_interval_hours=_int_from_environment(
            "FINDLING_RECONCILE_MIN_INTERVAL_HOURS", RECONCILE_MIN_INTERVAL_HOURS
        ),
        reconcile_quiet_max=_int_from_environment("FINDLING_RECONCILE_QUIET_MAX", RECONCILE_QUIET_MAX),
        reconcile_slice=_bounded_int_from_environment(
            "FINDLING_RECONCILE_SLICE", RECONCILE_SLICE, RECONCILE_SLICE_RANGE
        ),
        embed_enabled=_bool_from_environment("FINDLING_EMBED_ENABLED", EMBED_ENABLED),
        embed_token_cap=_bounded_int_from_environment(
            "FINDLING_EMBED_TOKEN_CAP", EMBED_TOKEN_CAP, EMBED_TOKEN_CAP_RANGE
        ),
        embed_chunk_tokens=embed_chunk_tokens,
        embed_chunk_overlap=embed_chunk_overlap,
        embed_batch_size=_bounded_int_from_environment(
            "FINDLING_EMBED_BATCH_SIZE", EMBED_BATCH_SIZE, EMBED_BATCH_SIZE_RANGE
        ),
        embed_sequence_len=embed_sequence_len,
        embed_model_dir=_embed_model_dir(),
    )
