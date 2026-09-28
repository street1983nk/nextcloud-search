"""What the container may use, read once and returned as a frozen snapshot (HW-01).

The profile suggestion (D-24-06) and the slot formula of Standard and
Performance need two numbers, cores and memory, and both lie inside a
container. Measured in the Findling image under three docker run variants
(24-RESEARCH.md, Pattern 5):

* ``os.process_cpu_count`` follows a cpu set (``--cpuset-cpus``) but ignores a
  quota (``--cpus``); ``os.cpu_count`` reports the host. The cores are therefore
  the minimum of the affinity count and the cpu.max quota.
* ``/proc/meminfo`` shows the host inside a container. A memory limit only
  exists in memory.max.
* AppAPI daemons set no ``resourceLimits`` by default (A9), so on most boxes
  both files say "max" and the host numbers are the honest answer.

The module is neutral on purpose: stdlib only, no import from the rest of
Findling, every path injectable so tests run against fake trees. It follows the
house rule of findling/config.py: unusable input never stops the container.
Every unreadable or garbled file becomes None for the field it feeds, and
``detect`` never raises. It logs nothing, neither paths nor values.
"""

import math
import os
import platform
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

CGROUP_ROOT: Final = Path("/sys/fs/cgroup")
MEMINFO: Final = Path("/proc/meminfo")

_KIB: Final = 1024

# The cgroup v1 spelling of "no limit" is a huge page aligned number (for
# example 9223372036854771712, PAGE_COUNTER_MAX). Anything at or above this
# floor is that sentinel, not a limit an admin could plausibly have set, and
# must become None even when MemTotal is unreadable and the comparison against
# it cannot run (fail-safe direction of D-24-06).
_V1_NO_LIMIT_FLOOR: Final = 1 << 60


def _read(path: Path) -> str | None:
    """The stripped content of a small kernel file, or None if it cannot be read."""
    try:
        return path.read_text(encoding="ascii").strip()
    except (OSError, ValueError):
        return None


def _positive_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def cpu_quota(root: Path) -> float | None:
    """The cpu.max quota in cores, or None for "max", a zero period or garbage.

    cpu.max holds "<quota> <period>": "max 100000" is no quota, "150000 100000"
    is 1.5 cores.
    """
    raw = _read(root / "cpu.max")
    if raw is None:
        return None
    parts = raw.split()
    if len(parts) != 2:  # the two fields of cpu.max
        return None
    quota = _positive_int(parts[0])
    period = _positive_int(parts[1])
    if quota is None or period is None:
        return None
    return quota / period


def memory_limit(root: Path) -> int | None:
    """The memory.max limit in bytes, or None for "max" or garbage."""
    return _positive_int(_read(root / "memory.max"))


def meminfo_bytes(path: Path, key: str) -> int | None:
    """One field of /proc/meminfo in bytes (the file speaks kB), or None."""
    raw = _read(path)
    if raw is None:
        return None
    for line in raw.splitlines():
        name, _, rest = line.partition(":")
        if name.strip() != key:
            continue
        fields = rest.split()
        if not fields:
            return None
        value = _positive_int(fields[0])
        return None if value is None else value * _KIB
    return None


def _cpu_quota_v1(root: Path) -> float | None:
    """The cgroup v1 quota in cores; a quota of -1 means none."""
    quota = _positive_int(_read(root / "cpu" / "cpu.cfs_quota_us"))
    period = _positive_int(_read(root / "cpu" / "cpu.cfs_period_us"))
    if quota is None or period is None:
        return None
    return quota / period


def _memory_limit_v1(root: Path, total: int | None) -> int | None:
    """The cgroup v1 memory limit; a value at or above MemTotal means none.

    v1 reports "no limit" as a huge page aligned number rather than "max". That
    sentinel is filtered on its own size first, so it never survives as a limit
    when /proc/meminfo is unreadable and the MemTotal comparison cannot run.
    """
    limit = _positive_int(_read(root / "memory" / "memory.limit_in_bytes"))
    if limit is None or limit >= _V1_NO_LIMIT_FLOOR:
        return None
    if total is not None and limit >= total:
        return None
    return limit


@dataclass(frozen=True, slots=True)
class Hardware:
    """One reading of the container's resources. Numbers only, no paths."""

    cpu_count: int | None
    cpu_quota: float | None
    cores: float | None
    memory_limit_bytes: int | None
    memory_available_bytes: int | None
    memory_total_bytes: int | None
    architecture: str
    cgroup: str

    @property
    def cores_whole(self) -> int | None:
        """The cores as a whole number for reporting, at least one."""
        if self.cores is None:
            return None
        return max(1, math.floor(self.cores))

    @property
    def threshold_memory_bytes(self) -> int | None:
        """Memory for the suggestion thresholds: memory.max, else MemTotal.

        A nominal 6 GB box has to read as a 6 GB box, which MemAvailable on a
        busy all-in-one host would not (24-CONTEXT.md, research recommendation).
        """
        if self.memory_limit_bytes is not None:
            return self.memory_limit_bytes
        return self.memory_total_bytes

    @property
    def formula_memory_bytes(self) -> int | None:
        """Memory for the slot formula: min(memory.max, MemAvailable), else the known one."""
        known = [value for value in (self.memory_limit_bytes, self.memory_available_bytes) if value is not None]
        return min(known) if known else None


def _call_cpu_count(cpu_count: Callable[[], int | None]) -> int | None:
    try:
        value = cpu_count()
    except Exception:  # detection must never stop the container
        return None
    return value if isinstance(value, int) and value > 0 else None


def _call_machine(machine: Callable[[], str]) -> str:
    try:
        value = machine()
    except Exception:  # detection must never stop the container
        return ""
    return value if isinstance(value, str) else ""


def detect(
    cgroup_root: Path = CGROUP_ROOT,
    meminfo: Path = MEMINFO,
    cpu_count: Callable[[], int | None] = os.process_cpu_count,
    machine: Callable[[], str] = platform.machine,
) -> Hardware:
    """Read cores, memory and architecture once. Never raises, never logs.

    cgroup v1 is only consulted when neither cpu.max nor memory.max exists.
    """
    count = _call_cpu_count(cpu_count)
    total = meminfo_bytes(meminfo, "MemTotal")
    available = meminfo_bytes(meminfo, "MemAvailable")

    if (cgroup_root / "cpu.max").exists() or (cgroup_root / "memory.max").exists():
        cgroup = "v2"
        quota = cpu_quota(cgroup_root)
        limit = memory_limit(cgroup_root)
    elif (cgroup_root / "cpu" / "cpu.cfs_quota_us").exists() or (
        cgroup_root / "memory" / "memory.limit_in_bytes"
    ).exists():
        cgroup = "v1"
        quota = _cpu_quota_v1(cgroup_root)
        limit = _memory_limit_v1(cgroup_root, total)
    else:
        cgroup = "none"
        quota = None
        limit = None

    known = [value for value in (float(count) if count is not None else None, quota) if value is not None]
    cores = min(known) if known else None

    return Hardware(
        cpu_count=count,
        cpu_quota=quota,
        cores=cores,
        memory_limit_bytes=limit,
        memory_available_bytes=available,
        memory_total_bytes=total,
        architecture=_call_machine(machine),
        cgroup=cgroup,
    )
