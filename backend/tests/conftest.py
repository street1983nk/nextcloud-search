"""What the three endpoint suites share: a signed header and a filled volume.

The fixtures here build the real thing rather than a stand-in. A fake index and
a fake permission table would answer every question except the one these suites
exist for: whether the endpoints wire the analyzer chain, the query rewriting and
the ACL prefilter together correctly. So ``indexed_volume`` writes a constituent
artifact, an index and a state database into a temporary directory and points
``APP_PERSISTENT_STORAGE`` at it, which is exactly the layout a deployed
container sees.

The constituent list is the fixture subset of the Debian word list, not the
system file: the recipe is measured elsewhere, and a test suite that needs
``/usr/share/dict/ngerman`` would only run inside the image.

The requests carry a real AppAPI header. It is base64 of ``username:app_secret``
and the middleware compares that secret against the environment, so the suites
exercise the same path a proxied request takes, including the empty user name of
the unauthorized case.
"""

import importlib.util
import sys
from base64 import b64encode
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient
from tantivy import Document

from findling.config import settings
from findling.embed.engine import note_cutter_failure
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
from findling.index.wordlist import DIGEST_SUFFIX, ENCODING, artifact_path, wordlist_hash
from findling.main import APP
from findling.store.repo import FileMeta, open_store
from findling.store.vectors import open_vectors

APP_ID = "findling_backend"
APP_VERSION = "0.1.0"
# Not a real credential: the middleware only checks equality against the
# environment it is given, so any value works as long as both sides agree.
APP_CREDENTIAL = "unit-test-credential"

CONSTITUENTS = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding=ENCODING).split()
)

# The corpus generator, which is a script and not a package, so it has to be
# loaded by path. Two test modules read FILES, _searchable_text, UNIQUE_TERMS and
# build_ground_truth out of it.
BUILD_CORPUS = Path(__file__).resolve().parents[2] / "scripts" / "dev" / "build_corpus.py"
BUILD_CORPUS_MODULE = "build_corpus_under_test"


@pytest.fixture(scope="session")
def corpus_generator() -> ModuleType:
    """``scripts/dev/build_corpus.py`` as a module, executed once per session.

    Importing it is not cheap and it is not a detail: ``FILES`` is built at
    module level, so every load produces all thirty nine corpus files, AES
    encryption, zip bomb and deeply nested PDF included. Measured with
    ``--durations`` before this fixture existed, the suite paid roughly 5.9
    seconds for each of five loads, about 35 s of a 180 s run, because two test
    modules each carried their own loader and called it once per test that
    needed it.

    One session scoped fixture is the whole fix, and the session scope is the
    part that matters: a module scoped one would still load it twice. Sharing
    one module object across tests is safe here because nothing in the generator
    keeps mutable state that a test writes to; the tests read constants and call
    pure builders.
    """
    specification = importlib.util.spec_from_file_location(BUILD_CORPUS_MODULE, BUILD_CORPUS)
    if specification is None or specification.loader is None:
        pytest.skip("the corpus generator is not where it is expected to be")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@dataclass(frozen=True, slots=True)
class Corpus:
    """The volume the endpoints read, and who may see what inside it.

    Three users, and the third one is the point: ``carol`` has no permission row
    at all, which is the shape a security claim is made against. ``alice`` sees
    the odd file ids, ``bob`` sees every document.
    """

    root: Path
    digest: str
    alice: str = "alice"
    bob: str = "bob"
    carol: str = "carol"
    documents: int = 12


def body_of(file_id: int) -> str:
    """A German sentence with two multi byte characters in front of the match.

    Without them a character offset and a byte offset look identical and the
    snippet assertions would be green either way.
    """
    tail = "Weitere Absätze folgen. " * (file_id % 3)
    return f"Für alle Beschäftigten gilt: die Kündigungsfrist im Vertrag {file_id} beträgt drei Monate. {tail}".strip()


def write_wordlist(root: Path) -> str:
    """Put the constituent artifact into the volume and return its digest.

    With the artifact and its digest in place ``build_artifact`` reads the file
    instead of running the recipe, so nothing here depends on a Debian package
    being installed on the machine that runs the suite.

    The name comes from ``artifact_path`` and is not spelled here: it carries the
    variant since bug audit H2 of plan 06.1-17, and a second spelling would leave
    the suite green while every container ran the recipe on every start. The root
    is passed in rather than read from the settings, because a fixture builds the
    volume before anything points at it.
    """
    target = root / "dict" / artifact_path().name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(CONSTITUENTS) + "\n", encoding=ENCODING)
    digest = wordlist_hash(CONSTITUENTS)
    target.with_name(target.name + DIGEST_SUFFIX).write_text(digest + "\n", encoding=ENCODING)
    return digest


def write_index(root: Path, documents: int) -> None:
    """Write the documents the endpoint suites search in, and commit them."""
    index = open_index(root / "index", CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id in range(1, documents + 1):
        document = Document()
        # Field by field, never through keyword arguments: a keyword built
        # document puts an I64 into the U64 column of file_id and the indexing
        # thread panics after the Python call has already returned.
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.pdf")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_PATH, f"/Akten/Akte-{file_id}.pdf")
        document.add_text(FIELD_EXT, "pdf" if file_id % 2 else "docx")
        document.add_text(FIELD_BODY_DE, body_of(file_id))
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()


def write_state(root: Path, corpus: Corpus) -> None:
    """Write the verdicts and the permission rows that belong to the index."""
    store = open_store(root / "state.db", meta=expected_versions(corpus.digest))
    for file_id in range(1, corpus.documents + 1):
        store.replace_acl(file_id, [corpus.alice, corpus.bob] if file_id % 2 else [corpus.bob])
        store.record(file_id, _meta_of(file_id), "indexed")
    store.close()


def write_vectors(root: Path) -> None:
    """Create the vector stock beside the state database, empty.

    Empty on purpose, and present on purpose. What the endpoint suites need
    from it is that it exists: a container whose second track has not written
    anything yet still has the file, and ``degraded`` reads a missing file as
    "the semantic half of this container is not there" rather than as "nothing
    similar was found". Without this the whole suite would run against a
    container that calls itself degraded, which is a different container from
    the one those tests are about.
    """
    open_vectors(root / "vectors.db").close()


def _meta_of(file_id: int) -> FileMeta:
    return FileMeta(
        storage_id=1,
        root_id=1,
        path=f"/Akten/Akte-{file_id}.pdf",
        title=f"Akte-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000 + file_id,
    )


@pytest.fixture(autouse=True)
def forget_the_cutter_notice() -> Iterator[None]:
    """No case inherits the failed cutter build of the case before it.

    The notice of ``embed/engine.py`` is a module global, because it describes
    this process the way the engine holder does. In a container that is one
    fact; in a suite it is a fact that outlives the test which produced it, and
    a poller case that lets a build throw would otherwise decide what the admin
    page reports three files later. Cleared on both sides, so the order the
    suite happens to run in cannot be read off any answer.
    """
    note_cutter_failure(None)
    yield
    note_cutter_failure(None)


@pytest.fixture
def appapi_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The four variables the AppAPI middleware and the client library read."""
    monkeypatch.setenv("APP_ID", APP_ID)
    monkeypatch.setenv("APP_VERSION", APP_VERSION)
    monkeypatch.setenv("APP_SECRET", APP_CREDENTIAL)
    monkeypatch.setenv("NEXTCLOUD_URL", "http://localhost:8080")


@pytest.fixture
def sign() -> Callable[[str], dict[str, str]]:
    """Build the signed header AppAPI would send for a user."""

    def headers(user_id: str) -> dict[str, str]:
        authorization = b64encode(f"{user_id}:{APP_CREDENTIAL}".encode()).decode()
        return {
            "EX-APP-ID": APP_ID,
            "EX-APP-VERSION": APP_VERSION,
            "AUTHORIZATION-APP-API": authorization,
        }

    return headers


@pytest.fixture
def client() -> TestClient:
    # No context manager on purpose: the lifespan belongs to the handshake tests,
    # the routers are mounted at import time and need nothing from it.
    return TestClient(APP)


@pytest.fixture
def volume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """An empty persistent volume, which is what a fresh container has.

    The settings cache is cleared on both sides of the test: it is resolved once
    per process by design, and a test that changed the environment without
    clearing it would hand its paths to the next one.
    """
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(tmp_path))
    settings.cache_clear()
    yield tmp_path
    settings.cache_clear()


@pytest.fixture
def indexed_volume(volume: Path) -> Corpus:
    """A volume with a word list, an index, a state database and a vector stock."""
    digest = write_wordlist(volume)
    corpus = Corpus(root=volume, digest=digest)
    write_index(volume, corpus.documents)
    write_state(volume, corpus)
    write_vectors(volume)
    return corpus
