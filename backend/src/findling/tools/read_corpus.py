"""Read every file of a corpus once, report what happened, change nothing.

This is the moving part of gate B (IDX-07). The workflow takes a checksum of the
reference corpus, runs this module over the very same files and takes the
checksum again. If anything in the read path ever writes back, the second
checksum says so. The tool itself therefore has exactly one job: touch every
file once, through the only channel the container has.

It is also the negative proof for COMP-02. Run with the id of a user who has no
access to the corpus, every single file has to come back as not accessible and
the byte count has to stay at zero.

The report is deliberately poor in content: file id, status, byte count. Never a
file name, never a byte of the file itself (T-01-32). The bodies land in a
temporary file in the runner scratch and are gone when the process ends.
"""

from __future__ import annotations

import argparse
import asyncio
import tempfile
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from findling.nc.client import (
    AsyncNextcloudApp,
    GatewayClient,
    create_app_client,
    fetch_file_stream,
    new_gateway_client,
)

STATUS_READ = "read"
STATUS_NOT_ACCESSIBLE = "not-accessible"
STATUS_ERROR = "error"


@dataclass(frozen=True)
class FileReadResult:
    """What one file id produced. ``detail`` carries an exception type, never data."""

    file_id: int
    status: str
    bytes_read: int
    detail: str = ""


async def read_one(
    nc: AsyncNextcloudApp,
    user_id: str,
    file_id: int,
    *,
    client: GatewayClient | None = None,
) -> FileReadResult:
    """Read a single file into scratch space and classify the outcome."""
    with tempfile.TemporaryFile() as scratch:
        try:
            written = await fetch_file_stream(nc, file_id, user_id, scratch, client=client)
        except Exception as error:
            # One unreadable file must not end the run: the whole point of the
            # gate is to see every file of the corpus, including the two that
            # are broken on purpose. The type name is enough to debug from.
            return FileReadResult(file_id, STATUS_ERROR, 0, type(error).__name__)
        if written is None:
            return FileReadResult(file_id, STATUS_NOT_ACCESSIBLE, 0)
        return FileReadResult(file_id, STATUS_READ, written)


async def read_files(
    nc: AsyncNextcloudApp,
    user_id: str,
    file_ids: Sequence[int],
    *,
    client: GatewayClient | None = None,
) -> list[FileReadResult]:
    """Read the given files one after another, in order.

    Sequential on purpose. The target hardware is a 4 GB box, and a gate that
    hides a memory problem behind concurrency would be worth less than none.

    One client for the whole run, not one per file: the corpus is read over a
    single keep alive connection, which is also the shape phase 2 needs when it
    walks tens of thousands of files.
    """
    if client is not None:
        return [await read_one(nc, user_id, file_id, client=client) for file_id in file_ids]

    async with new_gateway_client() as owned_client:
        return [await read_one(nc, user_id, file_id, client=owned_client) for file_id in file_ids]


def format_report(results: Sequence[FileReadResult]) -> str:
    """Render one line per file plus a machine readable summary line."""
    lines = []
    for result in results:
        detail = f" detail={result.detail}" if result.detail else ""
        lines.append(f"file {result.file_id} {result.status} bytes={result.bytes_read}{detail}")

    counts = Counter(result.status for result in results)
    total_bytes = sum(result.bytes_read for result in results)
    lines.append(
        f"summary files={len(results)}"
        f" {STATUS_READ}={counts[STATUS_READ]}"
        f" {STATUS_NOT_ACCESSIBLE}={counts[STATUS_NOT_ACCESSIBLE]}"
        f" {STATUS_ERROR}={counts[STATUS_ERROR]}"
        f" bytes={total_bytes}"
    )
    return "\n".join(lines)


def _parse_ids_file(ids_file: Path) -> list[int]:
    """Read whitespace separated positive file ids, or say which entry is wrong.

    The ids file in the workflow is produced by a shell pipeline over PROPFIND
    answers. When that pipeline breaks it does not produce an empty file, it
    produces a file with an error message or a stray zero in it, and the unchecked
    version turned that into a ValueError traceback out of a list comprehension.
    A zero would have been worse than a crash: the gateway answers 404 for it, so
    a broken pipeline would have read as "the user may not see this file".
    """
    try:
        text = ids_file.read_text(encoding="utf-8")
    except OSError as error:
        message = f"cannot read --ids-file {ids_file}: {error.strerror or type(error).__name__}"
        raise ValueError(message) from error

    file_ids: list[int] = []
    for position, token in enumerate(text.split(), start=1):
        if not token.isdigit() or int(token) <= 0:
            message = (
                f"--ids-file {ids_file}: entry {position} is {token!r}, expected whitespace separated positive integers"
            )
            raise ValueError(message)
        file_ids.append(int(token))
    return file_ids


def _collect_file_ids(inline: Sequence[int], ids_file: Path | None) -> list[int]:
    """Merge the ids given on the command line with those from a file."""
    file_ids = list(inline)
    if ids_file is not None:
        file_ids += _parse_ids_file(ids_file)
    return file_ids


def main(argv: Sequence[str] | None = None) -> int:
    """Run the corpus over the gateway and return a process exit code.

    A refused file is not a failure: exit code 1 is reserved for the unexpected,
    so the workflow can tell "the container may not read this" apart from "the
    container is broken".
    """
    parser = argparse.ArgumentParser(description="Read every file of a corpus through the Findling content gateway.")
    parser.add_argument("--user-id", required=True, help="the user whose permissions the gateway shall apply")
    parser.add_argument("--ids-file", type=Path, default=None, help="file with whitespace separated file ids")
    parser.add_argument("file_ids", nargs="*", type=int, help="file ids given directly")
    args = parser.parse_args(argv)

    try:
        file_ids = _collect_file_ids(args.file_ids, args.ids_file)
    except ValueError as error:
        # parser.error prints usage and exits with 2, which is what a command line
        # tool owes its caller. A traceback here would read like a defect in the
        # gate itself instead of a broken input file.
        parser.error(str(error))

    if not file_ids:
        parser.error("no file ids given, pass them as arguments or through --ids-file")

    results = asyncio.run(read_files(create_app_client(), args.user_id, file_ids))
    print(format_report(results))
    return 1 if any(result.status == STATUS_ERROR for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
