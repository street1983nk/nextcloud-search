"""The optional fp32 weights of the embedding model, the file side (MOD-02).

The image ships the int8 model only. An admin who wants the fp32 original can
have the container fetch it from the project's own GitHub release, or put the
file into the volume by hand. Either way the file has exactly one identity: the
sha256 and the length recorded below, the same file the image build quantises
from (``backend/Dockerfile``, stage model, ``onnx/model.onnx`` of
intfloat/multilingual-e5-small at revision 614241f). There is no fallback to
Hugging Face and no other source (D-25-05).

This module is the file side only. It imports neither of the two network
libraries gate A reserves for the client module (invariant 1): the bytes arrive through a ``fetch`` callable the caller injects,
in the running app ``findling.nc.client.fetch_release_asset``. Nothing here runs
on start or in the background; every function is a building block that plan
25-11 calls on an admin action and nowhere else.

Three rules carry the design:

* A download is written to ``model.onnx.part``, hashed and counted while it
  streams, and only renamed to ``model.onnx`` after length and digest match,
  with an fsync in front of the rename. A killed container leaves a ``.part``
  at most, and :func:`clear_leftovers` removes it (T-25-24).
* Every failure is a value out of :data:`PROCURE_OUTCOMES`, never an exception
  the caller has to know, and no failure leaves a file behind (D-25-04).
* A file the admin placed by hand is verified against the same digest before it
  counts, without a single request (D-25-06). The verdict is remembered against
  the size and the modification time of the file, so a second look is one stat.

Logs carry type names at most, never a path, a digest or a URL.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import shutil
import threading
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import IO, Final

LOGGER = logging.getLogger(__name__)

# The release of plan 25-01. Digest and length are the ones of the file the
# image build fetches from Hugging Face and quantises; the release asset is that
# file byte for byte, uploaded once under a tag that names the model revision.
FP32_SHA256: Final = "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"
FP32_BYTES: Final = 470_268_510
FP32_RELEASE_TAG: Final = "model-e5-small-fp32-614241f"
FP32_ASSET_NAME: Final = "multilingual-e5-small-fp32-614241f.onnx"
FP32_ASSET_URL: Final = (
    f"https://github.com/street1983nk/nextcloud-search/releases/download/{FP32_RELEASE_TAG}/{FP32_ASSET_NAME}"
)

FP32_DIR_NAME: Final = "multilingual-e5-small-fp32"
FP32_FILE_NAME: Final = "model.onnx"
PART_SUFFIX: Final = ".part"

# The closed set of outcomes of procure_fp32. A caller maps each to one line of
# the admin page; there is no fifth.
PROCURED: Final = "procured"
UNAVAILABLE: Final = "unavailable"
WRONG_DIGEST: Final = "wrong_digest"
NO_ROOM: Final = "no_room"
PROCURE_OUTCOMES: Final = frozenset({PROCURED, UNAVAILABLE, WRONG_DIGEST, NO_ROOM})

# The shape of findling.nc.client.fetch_release_asset: (url, write, *, cap).
FetchAsset = Callable[..., Awaitable[None]]

# Block size of the hash over a file on the volume. One mebibyte, the same block
# the download uses, so a 470 MB file costs about 450 reads and one block of
# memory.
_HASH_CHUNK: Final = 1024 * 1024

# The verdict cache. At most one entry, keyed on the identity of the file: its
# path, size and modification time, plus the digest it was compared against.
# Absence is never a key, so a file that disappears is looked at again rather
# than answered out of memory. Same shape as the cache in index/wordlist.py.
_VerdictKey = tuple[str, int, int, str]
_VERDICTS: dict[_VerdictKey, bool] = {}
_VERDICT_LOCK = threading.Lock()

# How often this process hashed a whole file. The number that makes the cache
# checkable from the outside, like wordlist.read_count().
_HASH_COUNT = 0


def hash_count() -> int:
    """Return how often this process has hashed a weights file."""
    return _HASH_COUNT


def forget_verdicts() -> None:
    """Drop every remembered verdict, so the next look hashes again."""
    with _VERDICT_LOCK:
        _VERDICTS.clear()


def fp32_weights_path(models_dir: Path) -> Path:
    """Where the fp32 weights live under the models directory of the volume."""
    return models_dir / FP32_DIR_NAME / FP32_FILE_NAME


def _part_path(models_dir: Path) -> Path:
    target = fp32_weights_path(models_dir)
    return target.with_name(target.name + PART_SUFFIX)


def _verdict_key(target: Path, status: os.stat_result) -> _VerdictKey:
    return (str(target), status.st_size, status.st_mtime_ns, FP32_SHA256)


def _file_digest(target: Path) -> str:
    """The sha256 of a file, read in blocks."""
    global _HASH_COUNT

    digest = hashlib.sha256()
    with target.open("rb") as source:
        while block := source.read(_HASH_CHUNK):
            digest.update(block)
    _HASH_COUNT += 1
    return digest.hexdigest()


def fp32_verified(models_dir: Path) -> bool:
    """True when the fp32 file on the volume is exactly the recorded one.

    Synchronous on purpose: the first look hashes 470 MB, so an async caller
    runs this in ``asyncio.to_thread``. No request of any kind, which is what
    makes a sideload work on a box without internet (D-25-06).

    A missing file costs one stat and is False. A file of the wrong size is
    False without a hash. Otherwise the verdict is remembered against size and
    modification time, so an unchanged file is hashed once per process.
    """
    target = fp32_weights_path(models_dir)
    try:
        status = target.stat()
    except OSError:
        return False
    if status.st_size != FP32_BYTES:
        return False

    key = _verdict_key(target, status)
    with _VERDICT_LOCK:
        cached = _VERDICTS.get(key)
        if cached is not None:
            return cached
        try:
            verdict = _file_digest(target) == FP32_SHA256
        except OSError as error:
            # A read error is no verdict about the file, so it is not remembered.
            LOGGER.warning("fp32 weights could not be read for verification (%s)", type(error).__name__)
            return False
        _VERDICTS.clear()
        _VERDICTS[key] = verdict
        return verdict


def _remember_verified(target: Path) -> None:
    """Record a file that was just installed after its digest matched."""
    try:
        status = target.stat()
    except OSError:
        return
    with _VERDICT_LOCK:
        _VERDICTS.clear()
        _VERDICTS[_verdict_key(target, status)] = True


def clear_leftovers(models_dir: Path) -> int:
    """Remove a ``model.onnx.part`` a killed download left, return how many went.

    Only that one name. Every other file in the directory stays where it is,
    including the finished weights.
    """
    part = _part_path(models_dir)
    try:
        part.unlink()
    except FileNotFoundError:
        return 0
    except OSError as error:
        LOGGER.warning("fp32 weights: leftover could not be removed (%s)", type(error).__name__)
        return 0
    return 1


def remove_fp32_weights(models_dir: Path) -> bool:
    """Remove the fp32 weights and any ``.part``, return whether weights were there.

    The way back of D-25-09, and it removes a file the admin placed by hand as
    well: the choice of fp32 is withdrawn, and a file nobody uses is 470 MB on
    the volume for nothing.
    """
    target = fp32_weights_path(models_dir)
    existed = target.exists()
    target.unlink(missing_ok=True)
    _part_path(models_dir).unlink(missing_ok=True)
    forget_verdicts()
    return existed


def _seal(sink: IO[bytes]) -> None:
    """Flush and fsync, so the rename below never publishes a file still in a cache."""
    sink.flush()
    os.fsync(sink.fileno())


def _drop_part(models_dir: Path) -> None:
    """Remove a ``.part`` synchronously, safe to run while a task is being cancelled."""
    try:
        _part_path(models_dir).unlink(missing_ok=True)
    except OSError as error:
        LOGGER.warning("fp32 weights: partial download could not be removed (%s)", type(error).__name__)


def _log_unavailable(error: BaseException) -> None:
    LOGGER.warning("fp32 weights could not be fetched (%s)", type(error).__name__)


async def _download(models_dir: Path, fetch: FetchAsset) -> str:
    """Stream the asset into the ``.part`` file and install it when it matches."""
    part = _part_path(models_dir)
    target = fp32_weights_path(models_dir)
    try:
        sink = await asyncio.to_thread(part.open, "wb")
    except OSError as error:
        _log_unavailable(error)
        return UNAVAILABLE

    digest = hashlib.sha256()
    received = 0

    async def write(chunk: bytes) -> None:
        nonlocal received
        received += len(chunk)
        digest.update(chunk)
        await asyncio.to_thread(sink.write, chunk)

    try:
        try:
            await fetch(FP32_ASSET_URL, write, cap=FP32_BYTES)
        except Exception as error:
            # Every failure of the fetch is the same outcome for the admin: the
            # asset is not reachable from this box right now. CancelledError is
            # a BaseException and passes through, so a shutdown stays a shutdown.
            _log_unavailable(error)
            return UNAVAILABLE
        if received != FP32_BYTES or digest.hexdigest() != FP32_SHA256:
            LOGGER.warning("fp32 weights: the download does not match the recorded digest")
            return WRONG_DIGEST
        await asyncio.to_thread(_seal, sink)
    finally:
        sink.close()

    try:
        await asyncio.to_thread(os.replace, part, target)
    except OSError as error:
        _log_unavailable(error)
        return UNAVAILABLE
    _remember_verified(target)
    return PROCURED


async def procure_fp32(models_dir: Path, fetch: FetchAsset, *, min_free_bytes: int) -> str:
    """Fetch the fp32 weights into the volume, return one of :data:`PROCURE_OUTCOMES`.

    ``fetch`` is called once as ``fetch(FP32_ASSET_URL, write, cap=FP32_BYTES)``.
    Before that the free space of the volume is compared against the size of the
    asset plus ``min_free_bytes``, so a full disk is NO_ROOM without a request
    (T-25-23). No outcome other than PROCURED leaves a file, and the ``.part``
    is removed on every way out, a cancellation included.
    """
    directory = fp32_weights_path(models_dir).parent
    try:
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        usage = await asyncio.to_thread(shutil.disk_usage, directory)
    except OSError as error:
        _log_unavailable(error)
        return UNAVAILABLE
    if usage.free < FP32_BYTES + min_free_bytes:
        LOGGER.warning("fp32 weights: not enough free space on the volume")
        return NO_ROOM

    try:
        return await _download(models_dir, fetch)
    finally:
        _drop_part(models_dir)
