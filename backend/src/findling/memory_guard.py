"""How much memory a further slot could still take, read from the cgroup (PAR-04).

The neutral reader under the RAM condition of the parallel lanes; phase 26
builds the memory guard on top of it. Same house rules as findling/hardware.py,
whose readers it reuses so that memory.max and MemAvailable have one spelling
each: standard library plus findling.hardware only, every path injectable so
tests run against fake trees, never raises, logs nothing.

The one new reader is the ``anon`` line of memory.stat. Why anon and not
``memory.current``: the tantivy index is memory mapped, and its page cache is
charged to the cgroup and shows in memory.current. The kernel reclaims that
cache under pressure, so counting it as used would refuse a second slot on
exactly the boxes that have room for one (25-RESEARCH.md, Pitfall 7). The
project measures anon throughout, the store figure and the rss sampler alike.

Known limit: only cgroup v2 carries memory.max and an anon line. On a v1 host
the limit is not read and the answer is MemAvailable, the same fallback as a
box without any limit.
"""

from pathlib import Path

from findling.hardware import CGROUP_ROOT, MEMINFO, meminfo_bytes, memory_limit

_STAT_FIELDS = 2  # "<name> <bytes>"


def anon_bytes(root: Path = CGROUP_ROOT) -> int | None:
    """The ``anon`` bytes of memory.stat, or None when the file or the line is unusable."""
    try:
        raw = (root / "memory.stat").read_text(encoding="ascii")
    except (OSError, ValueError):
        return None
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) != _STAT_FIELDS or fields[0] != "anon":
            continue
        try:
            value = int(fields[1])
        except ValueError:
            return None
        return value if value >= 0 else None
    return None


def headroom_bytes(*, cgroup_root: Path = CGROUP_ROOT, meminfo: Path = MEMINFO) -> int | None:
    """Bytes a further slot could take, or None when nothing usable is readable.

    With a limit and a readable anon: the limit minus anon, capped by
    MemAvailable when that is readable, because a limit above what the host
    still has is room that does not exist. Without a limit, or without a usable
    anon line, MemAvailable alone. Never negative.
    """
    available = meminfo_bytes(meminfo, "MemAvailable")
    limit = memory_limit(cgroup_root)
    if limit is None:
        return available
    # anon, not memory.current: the page cache of the mmap index is reclaimable
    # and must not count as used (see the module docstring).
    anon = anon_bytes(cgroup_root)
    if anon is None:
        return available
    within_limit = max(0, limit - anon)
    return within_limit if available is None else min(within_limit, available)


def admits(headroom: int | None, *, need: int) -> bool:
    """True when a readable headroom covers ``need``; unreadable is never admitted."""
    return headroom is not None and headroom >= need
