"""Two proofs that only the built image can give, run as a plain script.

Not named ``test_*`` on purpose: pytest must not collect it. Both steps build a
volume, and the offline one needs the 118 MB model that exists in the image and
on no development machine. The file still lives under ``tests`` because that is
the directory ``.github/workflows/docker.yml`` bind mounts into the container,
the same way ``test_vec_extension_probe.py`` travels in.

**Step one, offline.** ``HF_HUB_OFFLINE=1`` in ``backend/Dockerfile`` is a net
and not a proof, and the difference is the whole reason this step exists.
fastembed brought huggingface-hub and requests into an image that is not allowed
to speak to the outside world, the store text makes a statement about that, and
the only thing that can carry the statement is a container with its network cut
that answers a paraphrase anyway. Two runs, so that the answer cannot be an
accident: the same query against a volume without a vector stock has to find
nothing at all, and against a volume with one it has to put the paraphrased
document first.

One thing the step deliberately does not claim. It proves that no network is
needed, never that none is attempted. ``onnxruntime`` writes one line to stderr
in every run, "Failed to persist telemetry device ID", with the network cut as
well; it is a failed local file system write and not traffic (measured in plan
06-03). The line is expected here rather than surprising, because in a store
context it is exactly the sentence somebody reads the wrong way round.

**Step two, the model is gone.** Criterion 3 says the failure of the model costs
the semantics and never the search. A unit test with a stand-in proves that the
code knows the case; it does not prove that the built image behaves that way, and
pitfall 4 is precisely the mistake of believing the second follows from the
first. So the same image is started with an empty directory mounted over its
model directory, and the ordinary full text query has to come back with the same
hits as a run without any semantics at all, with the degraded mark, and above all
not empty and not as an error.

The empty answer is the trap of that step, and it has its own guard (T-06-49):
a step that is green because nothing was found would be green on a container
that answers nothing at all. The last thing this file does in that mode is
therefore to run the same verdict against a deliberately empty index and require
it to come back red.

Run it like this:

    docker run --rm --network none -v "$PWD/backend/tests:/probe:ro" \\
        --entrypoint python IMAGE /probe/probe_image_search.py offline

    docker run --rm --network none -v "$PWD/backend/tests:/probe:ro" \\
        -v "$PWD/empty:/usr/local/share/findling/model:ro" \\
        --entrypoint python IMAGE /probe/probe_image_search.py model-gone

The second mode needs no model, so it also runs on a development machine:

    cd backend && uv run python tests/probe_image_search.py model-gone
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tantivy import Document

from findling.api import resources
from findling.api.search import one_round
from findling.config import settings
from findling.embed.chunker import chunk_spans, make_splitter
from findling.embed.model import EmbeddingModel, open_tokenizer, to_int8
from findling.index.open import expected_versions, open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.wordlist import DIGEST_SUFFIX, ENCODING, wordlist_hash
from findling.store.repo import open_store
from findling.store.vectors import Chunk, open_vectors

CONSTITUENTS: Final = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding=ENCODING).split()
)

UID: Final = "probe-user"


@dataclass(frozen=True, slots=True)
class Passage:
    """One invented document of the probe corpus.

    ``subject`` is a label for the run log. Nothing here comes from a user: the
    five passages are written in this file and are the only text the probe ever
    touches.
    """

    file_id: int
    subject: str
    body: str


# Five subjects that have nothing to do with each other, so that "the nearest
# vector" is a question with an obvious answer. The first one is the target.
CORPUS: Final = (
    Passage(
        1,
        "employment",
        "Für alle Beschäftigten gilt: die Kündigungsfrist im Arbeitsvertrag beträgt drei Monate zum "
        "Quartalsende. Wer den Betrieb verlassen möchte, teilt das schriftlich mit und wartet die Frist ab.",
    ),
    Passage(
        2,
        "school roof",
        "Die Sanierung des Schuldaches beginnt in den Sommerferien; das Gerüst steht ab dem ersten Ferientag "
        "an der Nordseite und bleibt bis zum Herbst stehen.",
    ),
    Passage(
        3,
        "dog registration",
        "Wer einen Hund hält, meldet ihn binnen zwei Wochen beim Ordnungsamt an und entrichtet die jährliche "
        "Steuer für das Tier.",
    ),
    Passage(
        4,
        "bus timetable",
        "Die Buslinie zwölf fährt ab Montag im Zwanzigminutentakt und bedient zusätzlich den Feldweg am "
        "südlichen Ortsrand.",
    ),
    Passage(
        5,
        "library hours",
        "Die Stadtbibliothek öffnet ab Oktober auch am Samstagvormittag; die Rückgabe bleibt rund um die Uhr "
        "möglich, und der Lesesaal bleibt wie bisher bis achtzehn Uhr besetzt.",
    ),
)

TARGET_FILE_ID: Final = 1

# The paraphrase of criterion 1. Not one content word of it stands in the target
# passage, which is asserted at run time and not assumed: the control run below
# requires the lexical half to answer nothing at all, so a hit can only have come
# out of the vector half.
PARAPHRASE: Final = "Wann darf ich meinen Job aufgeben, und wie viel Zeit muss vorher vergehen?"

# An ordinary full text query. It stands in the target passage word for word,
# which is what makes it the right query for the model-gone step.
LEXICAL_TERM: Final = "Kündigungsfrist"


# -- the volume ------------------------------------------------------------


def write_volume(root: Path, passages: Sequence[Passage]) -> None:
    """Write the word list, the index and the state database into one directory.

    The layout is the one a deployed container sees, which is what makes the
    search path below the real one: ``resources.read_side`` finds an index, a
    state database and, in the offline mode, a vector stock, exactly where the
    settings say they are.

    The constituent artifact is written rather than built from
    ``/usr/share/dict/ngerman``, for the reason ``conftest.py`` gives: the
    digest in the state database has to describe the list the index was built
    with, or every run would report a version drift and the degraded mark would
    be true for a reason this probe is not about.
    """
    target = root / "dict" / "de.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(CONSTITUENTS) + "\n", encoding=ENCODING)
    digest = wordlist_hash(CONSTITUENTS)
    target.with_name(target.name + DIGEST_SUFFIX).write_text(digest + "\n", encoding=ENCODING)

    index = open_index(root / "index", CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for passage in passages:
        document = Document()
        # Field by field and never through keyword arguments: a keyword built
        # document puts an I64 into the U64 column of file_id and the indexing
        # thread panics after the Python call has already returned.
        document.add_unsigned(FIELD_FILE_ID, passage.file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{passage.file_id}.txt")
        document.add_text(FIELD_TITLE, f"Akte {passage.file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{passage.file_id}.txt")
        document.add_text(FIELD_EXT, "txt")
        document.add_text(FIELD_BODY_DE, passage.body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + passage.file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()

    store = open_store(root / "state.db", meta=expected_versions(digest))
    for passage in passages:
        store.replace_acl(passage.file_id, [UID])
    store.close()


def write_vector_stock(root: Path, passages: Sequence[Passage]) -> int:
    """Embed the corpus with the model of this image and return the chunk count.

    The same four steps the second track runs in ``worker/poller.py``: cut the
    stored body into passages, embed them as passages and not as queries, turn
    each vector into its int8 form, and write them under the file id. Anything
    else here would measure a path nobody uses.
    """
    resolved = settings()
    tokenizer = open_tokenizer(resolved.embed_model_dir)
    splitter = make_splitter(
        tokenizer,
        chunk_tokens=resolved.embed_chunk_tokens,
        overlap=resolved.embed_chunk_overlap,
    )
    model = EmbeddingModel(
        resolved.embed_model_dir,
        batch_size=resolved.embed_batch_size,
        sequence_len=resolved.embed_sequence_len,
    )
    stock = open_vectors(resolved.vectors_db)
    written = 0
    try:
        for passage in passages:
            spans = chunk_spans(
                passage.body,
                tokenizer=tokenizer,
                splitter=splitter,
                token_cap=resolved.embed_token_cap,
            )
            outcome = model.embed_passages([passage.body[span.char_start : span.char_end] for span in spans])
            if not outcome.available or len(outcome.vectors) != len(spans):
                raise RuntimeError(f"the model answered {len(outcome.vectors)} vectors for {len(spans)} passages")
            stock.replace_chunks(
                passage.file_id,
                [
                    Chunk(
                        ordinal=span.ordinal,
                        char_start=span.char_start,
                        char_end=span.char_end,
                        embedding=to_int8(vector),
                    )
                    for span, vector in zip(spans, outcome.vectors, strict=True)
                ],
            )
            written += len(spans)
    finally:
        stock.close()
    return written


def volume_for(passages: Sequence[Passage], *, embedding: bool) -> Path:
    """Build a fresh volume and point the process at it.

    A new directory per volume rather than a rebuilt one, because every cache in
    ``api/resources.py`` is keyed on a path: the read side on the index
    directory, the degraded verdict on the same, the marks on the dictionary
    directory. Reusing a directory would answer the second question with the
    handles of the first.
    """
    root = Path(tempfile.mkdtemp(prefix="findling-probe-"))
    os.environ["APP_PERSISTENT_STORAGE"] = str(root)
    os.environ["FINDLING_EMBED_ENABLED"] = "yes" if embedding else "no"
    settings.cache_clear()
    write_volume(root, passages)
    return root


# -- what one search came to -----------------------------------------------


@dataclass(frozen=True, slots=True)
class Answer:
    """One call of the search path, reduced to what the two steps judge."""

    file_ids: list[int]
    degraded: bool


def ask(text: str, *, label: str) -> Answer:
    """Run one round of the real search path and print what it came to.

    ``one_round`` is the function the HTTP handler calls, one level below the
    route. Everything the answer of a user is made of runs in here: the query
    rewriting, the engine, the vector branch, the merge and the one permission
    prefilter. Only the proxy hop is missing, and that hop is what the smoke
    test of the same workflow already covers.

    Printed are the label, the ids and the flag, never the query text and never
    a line of a document. The corpus is invented in this file, but the rule that
    a probe prints no text is the rule of every measuring tool in this project.
    """
    found = one_round(UID, text, 10, 0, False)
    file_ids = [candidate.fileId for candidate in found.candidates]
    print(f"{label:<28} file ids {file_ids}  degraded {found.degraded}")
    return Answer(file_ids=file_ids, degraded=found.degraded)


# -- step one: no network, and a paraphrase still finds the document --------


def judge_offline(control: Answer, lexical: Answer, semantic: Answer) -> list[str]:
    """One message per broken expectation, empty list when the step is clean."""
    messages: list[str] = []
    if control.file_ids:
        messages.append(
            "the paraphrase found something without a vector stock, so the corpus lost the property this "
            f"step rests on and a hit proves nothing about the model: {control.file_ids}"
        )
    if not lexical.file_ids:
        messages.append(
            "the ordinary full text query found nothing, so this volume cannot answer anything and the "
            "assertion below would be green on an empty container"
        )
    if not semantic.file_ids:
        messages.append(
            "the paraphrase found nothing with the vector stock in place, so this image cannot embed with "
            "the network cut, which is the whole statement of the offline step"
        )
    elif semantic.file_ids[0] != TARGET_FILE_ID:
        messages.append(
            f"the paraphrase ranked file id {semantic.file_ids[0]} first instead of {TARGET_FILE_ID}; a brute "
            "force neighbour search returns the whole stock, so the order is the only thing that says the "
            "model understood the question"
        )
    return messages


def offline_step() -> list[str]:
    """Build a volume, embed it, and ask the paraphrase with the network cut."""
    print("offline step: the image embeds and searches without a network")

    # The control comes first and it gets a volume of its own: the same corpus,
    # the same query, and no vector stock beside it. Whatever it finds is what
    # the lexical half of the search can find on its own.
    volume_for(CORPUS, embedding=True)
    control = ask(PARAPHRASE, label="paraphrase, no vectors")

    root = volume_for(CORPUS, embedding=True)
    chunks = write_vector_stock(root, CORPUS)
    print(f"vector stock                {chunks} chunks for {len(CORPUS)} documents")
    lexical = ask(LEXICAL_TERM, label="full text query")
    semantic = ask(PARAPHRASE, label="paraphrase, with vectors")

    return judge_offline(control, lexical, semantic)


# -- step two: the model is gone, and the search keeps its full text half ---


def judge_model_gone(reference: Answer, answer: Answer) -> list[str]:
    """One message per broken expectation, empty list when the step is clean."""
    messages: list[str] = []
    if not reference.file_ids:
        messages.append(
            "the reference run without any semantics found nothing, so there is nothing for the run with a "
            "missing model to be compared against (T-06-49)"
        )
    if not answer.file_ids:
        messages.append(
            "the query answered empty with the model gone, which is exactly what criterion 3 forbids: the "
            "failure of the model costs the semantics and never the search"
        )
    if answer.file_ids != reference.file_ids:
        messages.append(
            f"the answer with the model gone is {answer.file_ids} and the one without any semantics is "
            f"{reference.file_ids}; criterion 3 asks for the same hits and not for similar ones"
        )
    if not answer.degraded:
        messages.append(
            "the container did not call itself degraded although its vector stock is missing, so the PHP "
            "side would present an incomplete index as a complete one"
        )
    return messages


def model_gone_step() -> list[str]:
    """Ask an ordinary query in an image whose model directory is empty."""
    print("model-gone step: the image keeps its full text half")

    # The anti-vacuity clause of the whole step. With a model in place the run
    # below would prove nothing at all, so the absence is asked for rather than
    # assumed, and it is asked through the wrapper the search itself uses.
    volume_for(CORPUS, embedding=True)
    verdict = resources.query_model().embed_query(LEXICAL_TERM)
    print(f"model directory             {settings().embed_model_dir}")
    print(f"model answers available     {verdict.available}")
    if verdict.available:
        return [
            (
                "the model directory still carries a model, so this step is not the step it claims to be; "
                "mount an empty directory over it before running this mode"
            )
        ]

    volume_for(CORPUS, embedding=False)
    reference = ask(LEXICAL_TERM, label="no semantics at all")

    volume_for(CORPUS, embedding=True)
    answer = ask(LEXICAL_TERM, label="model gone, embedding on")

    messages = judge_model_gone(reference, answer)

    # The red proof, in the same run and against the same verdict function. An
    # empty index answers nothing, and nothing is what a broken step looks like;
    # if the judge stays quiet about it the two assertions above mean nothing.
    volume_for((), embedding=True)
    empty = ask(LEXICAL_TERM, label="deliberately empty index")
    if not judge_model_gone(empty, empty):
        messages.append(
            "an empty index passed the same verdict, so the judge of this step cannot tell a working "
            "container from one that answers nothing"
        )
    else:
        print("red proof                   an empty index is reported, the judge can fail")

    return messages


# -- the script ------------------------------------------------------------


MODES: Final = {"offline": offline_step, "model-gone": model_gone_step}


def main(argv: Sequence[str]) -> int:
    """Run one mode and return zero only when it had nothing to report."""
    if len(argv) != 2 or argv[1] not in MODES:
        print(f"usage: {Path(argv[0]).name} {{{'|'.join(MODES)}}}", file=sys.stderr)
        return 2

    messages = MODES[argv[1]]()
    for message in messages:
        print(f"FAILED: {message}", file=sys.stderr)
    if messages:
        return 1
    print(f"the {argv[1]} step is green")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
