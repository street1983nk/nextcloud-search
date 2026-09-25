"""The one place that opens an index, because opening is registering.

The schema persists the *name* of an analyzer and never the analyzer itself. An
index that is opened without registering those names answers the first
``parse_query`` with ``The tokenizer '"de"' for the field '"body_de"' is
unknown``, which looks like a broken index and is a missing line of setup.
Registration is therefore part of opening, and every other place in this project
that calls ``Index(...)`` or ``Index.open(...)`` is a defect; a test in
``tests/test_index_open.py`` walks the package and says so.

The German automaton costs 0.44 s and roughly 23 MB of resident memory that never
comes back, so this module asks :func:`findling.index.analyzer.cached_german_analyzer`
for it. A second ``open_index`` in the same process therefore reuses the
automaton rather than paying for it twice, which on the 4 GB box this project
targets is the difference between a search service and a memory problem.
"""

import hashlib
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

import tantivy
from tantivy import Filter, Index, Searcher, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import INDEX_VERSION, SCHEMA_VERSION, SNOWBALL_NAME
from findling.index.analyzer import (
    ANALYZER_VERSION,
    TOKENIZER_DE,
    TOKENIZER_EN,
    TOKENIZER_ES,
    TOKENIZER_IT,
    TOKENIZER_NAME,
    TOKENIZER_NL,
    TOKENIZER_PT,
    cached_german_analyzer,
    dutch_chain_for,
    english_analyzer,
    name_analyzer,
    snowball_analyzer,
)
from findling.index.schema import TOKENIZER_STORED_ONLY, build_schema
from findling.index.wordlist import wordlist_hash
from findling.index.wordlist_nl import DUTCH_LIST_OFF
from findling.store.repo import Store

LOGGER = logging.getLogger("findling.index.open")

# The mark that says which set of expected versions a rebuild is aimed at.
#
# It is not a version of anything and never compared against the code; it is a
# fingerprint, and its only job is to tell "a rebuild for exactly this code is
# already under way" from "the code changed again". Without it a container that
# restarts during a rebuild would raise the generation on every start and make
# the work of the previous start stale each time, which on a box that restarts
# often is a rebuild that never ends.
REBUILD_MARK: Final = "rebuild_for"

# The one mark that is never written by the stamp below, spelled out here so
# that the exception is visible next to the function that has to make it.
_LOCAL_GENERATION: Final = "index_version"

# The sixth mark, and the one that is easiest to read as the opposite of what it
# is. It names the language set the index on disk was BUILT with, and never the
# set the running container currently wishes for. The wish arrives as the second
# parameter of expected_versions below and stays on the expectation side of the
# comparison; the stored side is written once, by stamp_after_rebuild, after the
# work that makes it true is through.
#
# Two consequences follow from that and both are load bearing. The seed in
# findling.store.repo skips this key by name, because a seed that filled it in
# would write the wish as if it were a fact and silence the one mark built to
# speak up (threat T-18-05-01). And a missing value is read as legacy rather
# than as a difference, because up to 1.2.0 no released build could write a body
# field outside ("de", "en"); that exception lives next to the comparison, in
# findling.store.repo._languages_are_legacy, and nowhere else.
LANGUAGES_MARK: Final = "languages"

# The seventh mark, and it travels exactly like the sixth (decision D-06 of phase
# 21). It names the Dutch constituent list body_nl on disk was BUILT with, as
# "off" or "<chain version>:<digest>", and never the list the running container
# would use today. The wish arrives as the dutch_mark parameter of
# expected_versions below; the stored side is written only where a directory is
# built with that list, by stamp_a_new_directory here and behind the directory
# swap, and never by stamp_after_rebuild, which is why it stands in
# _MARKS_OF_A_DIRECTORY.
#
# The same two consequences as for the language mark follow. The seed in
# findling.store.repo skips this key by name, because a seeded mark would
# silence exactly the installation that switches Dutch on (threat T-18-05-01).
# And a missing value is legacy only while the expectation is "off": no build
# before phase 21 split body_nl with a list, so an absent mark and an expectation
# of off describe the same directory. That exception lives next to the comparison,
# in findling.store.repo._dutch_list_is_legacy, and nowhere else.
DUTCH_MARK: Final = "wordlist_hash_nl"

# The mark that names the layout of the schema the directory on disk was built
# under, and a public name since plan 19-03 because a second reader arrived.
#
# It used to be a literal in expected_versions below, which was defensible while
# exactly one place wrote it and exactly one place compared it. The field plan of
# findling.api.resources reads the very same key to decide which fields a bare
# word reaches into, and a key that is spelled out at every place that touches it
# drifts on the day one of them is renamed and nothing anywhere says so. This
# repo already answers that risk twice for the language pair, where
# LEGACY_LANGUAGES stands in findling.store.repo with a comment saying why the
# second spelling in findling.index.rebuild is held against it by a case; the
# schema key gets the cheaper version of the same answer, which is one name.
#
# findling.store.repo keeps its own _SCHEMA_MARK on purpose and that is not a
# fourth spelling of this one: that module does not import the index side at all
# (see its module docstring), and a case of the suite holds the two together.
SCHEMA_MARK: Final = "schema_version"

# Any token of one byte or more is dropped, which is every token there is. See
# stored_only_analyzer below for why that is the wanted behaviour.
_DROP_EVERY_TOKEN: Final = 1

# The banner of the extension module, measured as "tantivy v0.26.0, index_format
# v7". The type stub shipped with tantivy 0.26.0 does not declare the attribute,
# so the read is annotated for pyright rather than replaced by a lookup with a
# default: a fallback value here would turn a renamed attribute into a version
# mark that quietly says the wrong thing.
TANTIVY_VERSION: Final[str] = tantivy.__version__  # pyright: ignore[reportAttributeAccessIssue]


def stored_only_analyzer() -> TextAnalyzer:
    """Return the chain for a field that is stored and never searched.

    tantivy's Python bindings have no unindexed text field: ``index_option``
    accepts basic, freq and position, and nothing else, so every text field is
    indexed. A chain that returns the empty token list is the same thing where it
    matters, and it was measured that way: the value comes back out of the
    document store unchanged, while a query on the field finds nothing, neither
    for a word inside the value nor for the value in full.

    This is what the ``path`` field runs on. Paths are display and diagnosis.
    """
    return TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.remove_long(_DROP_EVERY_TOKEN)).build()


def open_index(path: Path, constituents: Sequence[str], *, dutch: str | None = None) -> Index:
    """Create or open the index at ``path`` and register its eight analyzers.

    ``constituents`` is the prepared word list from
    :func:`findling.index.wordlist.load_constituents`; it decides how German text
    is split and therefore what the index contains, which is why its digest is
    one of the version marks in :func:`expected_versions`.

    ``dutch`` is the digest of the Dutch constituent list from
    :func:`findling.index.wordlist_nl.dutch_digest_for`, or None while nl is not
    configured. It decides which chain stands behind the nl name and never
    whether one does. The default None is there for the roughly hundred test
    calls that open German indexes; every caller in src names the choice
    explicitly, and ``tests/test_index_open.py`` holds that with a gate
    (``test_every_caller_in_src_names_the_dutch_choice``), so no production path
    decides it silently.

    The directory is created when it is missing. It lives inside the container's
    own persistent volume and is never a Nextcloud node; the read-only gate holds
    a reviewed exception for exactly this line.
    """
    path.mkdir(parents=True, exist_ok=True)
    index = Index.open(str(path)) if Index.exists(str(path)) else Index(build_schema(), path=str(path))
    index.register_tokenizer(TOKENIZER_DE, cached_german_analyzer(wordlist_hash(constituents), constituents))
    index.register_tokenizer(TOKENIZER_EN, english_analyzer())
    # The four chains of the v1.3 languages, and they are registered whatever
    # FINDLING_LANGUAGES says. Measured on 2026-09-24 with tantivy 0.26.2: a
    # schema that carries a text field whose chain is not registered answers
    # every writer.add_document with "Schema error: 'Error getting tokenizer for
    # field: body_es'", and it does so even when the document does not carry
    # that field at all. Hanging these four lines on the active language set
    # would therefore stop the indexer on every installation that does not run
    # all six languages. The filling hangs on the language set, the registration
    # does not.
    #
    # It costs nothing. The Snowball chains are compiled into tantivy and bring
    # no data with them; the one chain that is expensive is the German one, with
    # its 0.44 s and roughly 23 MB of automaton, and that one is built in any
    # case. The language names come from SNOWBALL_NAME, the single place where a
    # field code turns into a tantivy language, and are never repeated here.
    index.register_tokenizer(TOKENIZER_ES, snowball_analyzer(SNOWBALL_NAME["es"]))
    index.register_tokenizer(TOKENIZER_IT, snowball_analyzer(SNOWBALL_NAME["it"]))
    # The Dutch chain follows the language set in its variant and never in its
    # presence, so the line stays free like the three around it. Without nl,
    # body_nl stays empty and field_plan_for in findling.api.resources never asks
    # it, so the plain Snowball variant is neutral there and saves the 17.6 MB of
    # the Dutch automaton; with nl the splitting chain answers, with the list
    # behind the folding (D-07). dutch_chain_for makes the choice, not this line.
    index.register_tokenizer(TOKENIZER_NL, dutch_chain_for(dutch))
    index.register_tokenizer(TOKENIZER_PT, snowball_analyzer(SNOWBALL_NAME["pt"]))
    index.register_tokenizer(TOKENIZER_NAME, name_analyzer())
    index.register_tokenizer(TOKENIZER_STORED_ONLY, stored_only_analyzer())
    return index


def open_reader(index: Index) -> Searcher:
    """Configure the index reader and hand out a first searcher.

    The reload policy is ``commit``: the reader picks up new segments after a
    commit, with a delay. A test that writes and searches in the same breath
    therefore calls ``index.reload()`` and asks for a fresh searcher, otherwise it
    asserts against the state before the commit and is green for the wrong reason.

    Call this once per index, not once per query. Measured on this machine:
    configuring the reader costs 0.10 ms while a whole search costs 0.005 ms, so
    a per query call would spend twenty times the search on the setup for it. A
    searcher is a snapshot; a long lived caller asks ``index.searcher()`` for a
    new one and pays nothing for it.
    """
    index.config_reader(reload_policy="commit")
    return index.searcher()


def expected_versions(digest: str, languages: str, *, dutch_mark: str = DUTCH_LIST_OFF) -> dict[str, str]:
    """Return the version marks an index built by this code must carry.

    The comparison itself lives in :meth:`findling.store.repo.Store.version_mismatch`:
    this module knows what the current code produces, the store knows what the
    existing index was built with, and only the caller that holds both may decide
    what a difference means. A mark that is missing counts as a difference there,
    which is why every value below is a string and none of them is optional.

    ``tantivy_version`` carries the full banner, including the index format, since
    tantivy makes no promise that its on disk format survives its own releases.

    Both arguments are handed in rather than read out of :func:`findling.config.settings`
    here, and that is the same decision twice. A module that read them itself
    would have no call site to look at, and these two are exactly the marks whose
    value depends on the environment of the caller: the digest belongs to the
    word list of one volume, the language set to the wish of one container. Every
    caller builds the second one as ``",".join(settings().languages)`` and none of
    them assembles the string any other way; ``_languages()`` iterates over
    SUPPORTED_LANGUAGES and not over the admin's input, so "es,de" and "de,es"
    arrive here as the same string and an index that never needed a rebuild is
    left alone (owner decision E-17-4 option a of 2026-09-23).

    ``dutch_mark`` is the third value that depends on the environment of the
    caller, and it is handed in for the same reason: it names the Dutch list of
    one volume, and only when the container wants Dutch at all. Every caller
    builds it as ``wordlist_nl.dutch_mark(settings().languages)``, which answers
    ``off`` without touching the volume when nl is inactive; a gate of plan
    21-06 holds that for every caller in src. The default ``off`` is the value of
    every installation without Dutch, and the mark stands last so that the order
    of the six older marks does not move.
    """
    return {
        SCHEMA_MARK: str(SCHEMA_VERSION),
        _LOCAL_GENERATION: str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,
        "tantivy_version": TANTIVY_VERSION,
        LANGUAGES_MARK: languages,
        DUTCH_MARK: dutch_mark,
    }


def fingerprint(expected: Mapping[str, str]) -> str:
    """One short name for a whole set of expected marks.

    Only equality is ever asked of it, so any stable function of the values will
    do; a hash is used rather than the values themselves so that the mark stays
    one short row whatever a future mark carries.

    Two callers and two stores for the same short string. The one below writes
    it into ``state.db`` next to the raised generation, so that a container
    which restarts in the middle of a rebuild can tell "the same code is still
    at it" from "the code changed again". The rebuild of plan 18-09 writes it
    into the half filled target directory, so that a resume can tell "this
    directory is mine" from "this directory was filled by other code", which is
    the question the audit found nobody asking (H-18-02).
    """
    material = "\n".join(f"{key}={expected[key]}" for key in sorted(expected))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def start_rebuild_on_drift(
    store: Store, expected: Mapping[str, str], *, answered_elsewhere: frozenset[str] = frozenset()
) -> int | None:
    """Raise the local generation when the index was built by other code.

    Returns the new generation, or None when there is nothing to rebuild.

    **Why raising the generation is the rebuild.** The remedy the reindex banner
    names is ``occ findling:index --restart``, which queues a crawl of every
    mount, and until this plan that crawl did nothing at all: the fast path of
    the poller asks :meth:`findling.store.repo.Store.is_unchanged`, which
    compares the content hash and the generation, and an analyzer drift moves
    neither of them. Every file came back, matched, and was acknowledged without
    a byte being read. Raising the generation makes every stored verdict stale
    at once, so the crawl the admin asked for actually reads the documents again.

    **Why it happens once per drift and not once per start.** The fingerprint of
    the marks being rebuilt towards is written next to the generation. A
    container that restarts in the middle of a two day rebuild finds its own
    fingerprint, leaves the generation alone and carries on; a container whose
    code changed again finds a different one and starts a rebuild for the new
    code. Without that distinction a box that restarts nightly would make the
    work of every day stale on the next morning.

    **What it does not do is declare anything current.** The marks stay as they
    are, so the banner stays up for as long as the work is not through. That is
    :func:`stamp_after_rebuild`'s job and nobody else's.

    **Why a drift answered elsewhere must not raise the generation.**
    ``answered_elsewhere`` names the marks another remedy takes care of, and the
    poller hands in :data:`findling.index.rebuild.MARKS_A_REBUILD_ANSWERS`: the
    schema mark and the language mark, which the band run makes true by carrying
    the documents over. Raising the generation for one of those would turn the
    re-analysis the owner chose in phase 17 into a full reindex of every file on
    top of it. The planning probe of 2026-09-25 (a volume built under de,en,
    opened under de,en,nl) and CI run 36072411846 ("Store upgrade 5") both saw
    exactly that: the generation went from 1 to 2 on the opening alone. The
    exempted marks stay drifted, so the band run still sees what it has to
    answer, and a drift of any other mark still raises. The fingerprint is still
    taken over the whole expectation. The fallback branch of
    :func:`findling.index.rebuild.rebuild_the_index` calls this function without
    the argument on purpose, because there the crawl is the chosen remedy for
    the language drift as well.
    """
    if not [name for name in store.version_mismatch(expected) if name not in answered_elsewhere]:
        return None

    wanted = fingerprint(expected)
    if store.read_meta().get(REBUILD_MARK) == wanted:
        return None

    generation = store.index_version + 1
    store.write_meta(_LOCAL_GENERATION, str(generation))
    store.write_meta(REBUILD_MARK, wanted)
    LOGGER.warning(
        "the index was built by different code; raised the generation to %d so the next crawl rebuilds it",
        generation,
    )
    return generation


# The marks :func:`stamp_after_rebuild` never writes, because none of them is a
# statement about the pass that stamp stands behind.
#
# ``index_version`` is the local generation, which stands above the baseline of
# the code precisely because a rebuild happened; writing the baseline back would
# make every verdict of the finished run look stale.
#
# The other three describe an index DIRECTORY: the layout it was built under,
# the body chains that were written into it, and the Dutch list body_nl was
# split with. They are written behind the directory swap and in front of the
# creation of a new directory, because those are the only places where what
# they claim is true (audit finding M-19-05, decision D-06 of phase 21).
_MARKS_OF_A_DIRECTORY: Final = frozenset({_LOCAL_GENERATION, SCHEMA_MARK, LANGUAGES_MARK, DUTCH_MARK})


def stamp_a_new_directory(store: Store, path: Path, expected: Mapping[str, str]) -> bool:
    """Write the three marks of an index directory that is about to be built empty.

    Schema, language set and, since plan 21-05, the Dutch list; the paragraphs
    below were written when there were two and hold for the third unchanged.

    Answers True when it wrote them and False when ``path`` already holds an
    index, which is every start of every container after the first one.

    **The one gap the fix of M-19-05 left, named as such.** That finding took
    the two marks above out of :func:`stamp_after_rebuild`, and the reason it
    gives is sound: that stamp stands behind a pass over the holdings in a
    directory that was already there, and no pass over documents makes a claim
    about the layout of a directory true. What the fix did not see is that the
    same stamp was also the only writer of those two marks on a volume that
    never had an index at all, because no rebuild runs there either
    (:func:`findling.index.rebuild.rebuild_the_index` answers such a volume with
    NO_LIVE_DIRECTORY). A fresh installation therefore carried no language mark
    at all, :func:`findling.api.resources.field_plan_for` read the absent mark
    as ``LEGACY_LANGUAGES``, and a bare word reached ``body_de`` and ``body_en``
    for the life of the installation whatever FINDLING_LANGUAGES said. The CI
    leg "Language proof, the four new chains answer on the ordinary search
    route" of deploy-harp run 36086044755 answered all four new chains with
    nothing, on all four legs, and it is the only leg that asks in a language
    outside the legacy pair.

    **Why this place may make a claim the other one may not.** There is no
    directory here. The caller creates it in the next line out of
    :func:`findling.index.schema.build_schema`, under the schema of this code
    and with every chain of this code registered, so an empty directory of the
    current layout and the current language set is precisely what the two marks
    say. The other stamp describes work over documents that somebody else's code
    may have written; this one describes a directory that does not exist yet and
    can therefore hold nothing that contradicts it. The refusal above is what
    keeps it that way: a directory that is already there is never restamped
    here, whatever it carries, so the upgrade path of M-19-05 passes this
    function untouched.

    **It is asked in front of the creation and not behind it.** The reading side
    of the container opens as soon as the directory is there and computes its
    field list once per opening, so a stamp behind the creation leaves a window
    in which a search reads marks nobody has written yet and keeps that list for
    as long as its handles live. That is the same window audit finding H-19-01
    closed on the other side of the swap, and the cheapest way not to have it
    here is to write first.

    ``index_version`` is not among the two, for the reason the comment on
    :data:`_MARKS_OF_A_DIRECTORY` gives: the stored generation is a floor and
    the expected one is the baseline of the code.
    """
    if path.is_dir() and Index.exists(str(path)):
        return False
    store.write_meta(SCHEMA_MARK, expected[SCHEMA_MARK])
    store.write_meta(LANGUAGES_MARK, expected[LANGUAGES_MARK])
    # The seventh mark belongs to the same directory for the same reason: the
    # directory about to be built is split with the Dutch list of this code, or
    # with none when the mark is off (decision D-06 of phase 21).
    store.write_meta(DUTCH_MARK, expected[DUTCH_MARK])
    LOGGER.info(
        "this volume holds no index yet; the schema, language and dutch list marks of the new directory are written"
    )
    return True


def stamp_after_rebuild(store: Store, expected: Mapping[str, str]) -> bool:
    """Write the marks of the running code once the rebuild is through.

    Returns True when the marks are current afterwards, which includes the
    ordinary case of an index that never drifted, and False while there is still
    work to do. A caller that polls this may stop the moment it answers True.

    **What "through" means here, exactly.** Not the end of the command and not
    an empty queue: the state in which no living file carries a verdict of an
    earlier generation any more, which is what
    :meth:`findling.store.repo.Store.verdicts_older_than` counts. Every writer
    of a verdict stamps the generation that is running, so a file that ends as
    indexed, skipped or failed under this code leaves the count, and a file that
    was never touched again keeps it above zero.

    **The limit of that definition, named as the plan requires.** It is the
    second best form, because it can only see files this container has heard of.
    A file that was deleted in Nextcloud without a delete job reaching the
    container keeps its old row and holds the count above zero until the nightly
    reconcile turns it into a tombstone, which the count leaves out. So the
    stamp can be a night late on an instance where documents were deleted during
    an update. That is the direction to be late in: a mark written too early
    declares half an index complete and takes away the one banner that told the
    admin why hits are missing (T-05-48).

    **The generation is deliberately not written back.** ``index_version`` in
    the expected marks is the baseline of the code, while the stored one is the
    local generation, and after a rebuild the local one stands above it. The
    store reads that mark as a floor rather than as an equality for exactly this
    reason. Writing the baseline back would make every row of the rebuild that
    just finished look stale and start the whole thing over.

    **This is not the seed and must never move into it.** ``_seed_meta`` fills
    in a mark that is missing and touches nothing that is there, because an
    existing database has to keep the marks its index was really built with.
    This function is the opposite operation and therefore a separate one.

    **Four marks are deliberately left out**, and the list is
    :data:`_MARKS_OF_A_DIRECTORY`. The generation for the reason above; the
    schema mark and the language mark since audit finding M-19-05, because they
    describe an index directory and this stamp runs after a pass over the
    holdings **in the directory that is already there**. Writing them here is
    the "two stampers under one name" that
    :func:`findling.index.rebuild.stamp_after_swap` exists to avoid (T-18-07-03):
    a run that ended in RUN_INCOMPLETE or RUN_STOPPED_EARLY gives the poller
    back, the next idle pass finds an empty queue, and both marks would then
    declare a directory current that was never rebuilt. Since phase 19 those two
    also decide which fields a search reaches, so the claim would not merely be
    wrong, it would be acted on. The Dutch list mark joined them in plan 21-05
    for the same reason: a pass over the holdings does not split body_nl with a
    new list.

    **A consequence of that, named because the Dutch mark inherits it** (finding
    of plan 21-01): the fingerprint below is emptied although a skipped mark may
    still drift, so under the fullreindex way out the next start raises the
    generation again. Held by a case in ``tests/test_index_rebuild.py``; the
    band run of plan 21-06 is the answer that writes the mark behind the swap.
    """
    stored = store.read_meta()
    if not store.version_mismatch(expected) and not stored.get(REBUILD_MARK):
        # Nothing drifted and nothing is being rebuilt, so there is nothing to
        # write. Said here rather than at the call site because a caller that
        # had to know this would be a second place deciding what a current index
        # looks like, and it saves the count below on every ordinary instance.
        return True

    generation = store.index_version
    remaining = store.verdicts_older_than(generation)
    if remaining > 0:
        return False

    for key, value in expected.items():
        if key in _MARKS_OF_A_DIRECTORY:
            continue
        store.write_meta(key, value)
    store.write_meta(REBUILD_MARK, "")
    LOGGER.info("the rebuild is through at generation %d; the version marks are current again", generation)
    return True
