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

from base64 import b64encode
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tantivy import Document

from findling.config import settings
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
from findling.main import APP
from findling.store.repo import FileMeta, open_store

APP_ID = "findling_backend"
APP_VERSION = "0.1.0"
# Not a real credential: the middleware only checks equality against the
# environment it is given, so any value works as long as both sides agree.
APP_CREDENTIAL = "unit-test-credential"

CONSTITUENTS = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding=ENCODING).split()
)


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
    """
    target = root / "dict" / "de.txt"
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
    """A volume with a word list, a committed index and a matching state database."""
    digest = write_wordlist(volume)
    corpus = Corpus(root=volume, digest=digest)
    write_index(volume, corpus.documents)
    write_state(volume, corpus)
    return corpus
