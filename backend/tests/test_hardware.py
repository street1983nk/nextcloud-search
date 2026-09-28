"""Hardware detection reads what the container may use, never what the host has.

The measured facts behind the tests (24-RESEARCH.md, three docker run variants
in the Findling image): ``os.process_cpu_count`` follows a cpu set but ignores
``--cpus``, and ``/proc/meminfo`` shows the host inside a container. So the
cores come from the minimum of the affinity count and the cpu.max quota, and a
memory limit comes from memory.max. Every file is read from a fake tree under
``tmp_path``; no real /sys is touched, which is why this runs on Windows too.

The second half is the house rule: unusable input never stops the container.
A missing, empty or garbled file is None for the field it feeds, never an
exception.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from findling.hardware import CGROUP_ROOT, MEMINFO, Hardware, cpu_quota, detect, meminfo_bytes, memory_limit

KIB = 1024
MEM_TOTAL_KB = 7_970_000
MEM_AVAILABLE_KB = 5_800_000


def _meminfo(path: Path, total_kb: int = MEM_TOTAL_KB, available_kb: int = MEM_AVAILABLE_KB) -> Path:
    path.write_text(
        f"MemTotal:       {total_kb} kB\nMemFree:         1000000 kB\nMemAvailable:   {available_kb} kB\n",
        encoding="ascii",
    )
    return path


def _v2_tree(root: Path, cpu_max: str, memory_max: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cpu.max").write_text(cpu_max + "\n", encoding="ascii")
    (root / "memory.max").write_text(memory_max + "\n", encoding="ascii")
    return root


def test_the_default_paths_are_the_kernel_paths() -> None:
    assert Path("/sys/fs/cgroup") == CGROUP_ROOT
    assert Path("/proc/meminfo") == MEMINFO


@pytest.mark.parametrize(
    ("variant", "cpu_max", "memory_max", "affinity", "cores", "quota", "limit"),
    [
        ("no options", "max 100000", "max", 12, 12.0, None, None),
        ("--memory 2g --cpus 1.5", "150000 100000", "2147483648", 12, 1.5, 1.5, 2_147_483_648),
        ("--cpuset-cpus 0,1", "max 100000", "max", 2, 2.0, None, None),
    ],
)
def test_the_three_measured_docker_run_variants(
    tmp_path: Path,
    variant: str,
    cpu_max: str,
    memory_max: str,
    affinity: int,
    cores: float,
    quota: float | None,
    limit: int | None,
) -> None:
    root = _v2_tree(tmp_path / "cgroup", cpu_max, memory_max)
    meminfo = _meminfo(tmp_path / "meminfo")

    found = detect(cgroup_root=root, meminfo=meminfo, cpu_count=lambda: affinity, machine=lambda: "aarch64")

    assert variant
    assert found.cgroup == "v2"
    assert found.cpu_count == affinity
    assert found.cpu_quota == quota
    assert found.cores == cores
    assert found.memory_limit_bytes == limit
    assert found.memory_total_bytes == MEM_TOTAL_KB * KIB
    assert found.memory_available_bytes == MEM_AVAILABLE_KB * KIB
    assert found.architecture == "aarch64"
    if limit is None:
        assert found.threshold_memory_bytes == MEM_TOTAL_KB * KIB
        assert found.formula_memory_bytes == MEM_AVAILABLE_KB * KIB
    else:
        assert found.threshold_memory_bytes == limit
        assert found.formula_memory_bytes == min(limit, MEM_AVAILABLE_KB * KIB)


def test_an_empty_tree_never_raises(tmp_path: Path) -> None:
    found = detect(cgroup_root=tmp_path, meminfo=tmp_path / "missing", cpu_count=lambda: 4, machine=lambda: "x86_64")

    assert found.cgroup == "none"
    assert found.cores == 4.0
    assert found.cpu_quota is None
    assert found.memory_limit_bytes is None
    assert found.memory_available_bytes is None
    assert found.memory_total_bytes is None
    assert found.threshold_memory_bytes is None
    assert found.formula_memory_bytes is None


def test_no_cpu_count_and_no_quota_means_no_cores(tmp_path: Path) -> None:
    found = detect(cgroup_root=tmp_path, meminfo=tmp_path / "missing", cpu_count=lambda: None, machine=lambda: "")

    assert found.cores is None
    assert found.cores_whole is None


def test_a_raising_callable_is_absorbed(tmp_path: Path) -> None:
    def broken() -> int | None:
        raise RuntimeError

    def broken_machine() -> str:
        raise RuntimeError

    found = detect(cgroup_root=tmp_path, meminfo=tmp_path / "missing", cpu_count=broken, machine=broken_machine)

    assert found.cpu_count is None
    assert found.architecture == ""


def test_the_quota_alone_gives_the_cores(tmp_path: Path) -> None:
    root = _v2_tree(tmp_path, "250000 100000", "max")

    found = detect(cgroup_root=root, meminfo=tmp_path / "missing", cpu_count=lambda: None, machine=lambda: "")

    assert found.cores == 2.5
    assert found.cores_whole == 2


@pytest.mark.parametrize("content", ["abc", "0 0", "150000 0", "", "max", "0 100000", "-1 100000", "1 2 3"])
def test_a_broken_cpu_max_is_no_quota(tmp_path: Path, content: str) -> None:
    (tmp_path / "cpu.max").write_text(content, encoding="ascii")

    assert cpu_quota(tmp_path) is None


@pytest.mark.parametrize("content", ["abc", "", "max", "0", "-5", "1.5"])
def test_a_broken_memory_max_is_no_limit(tmp_path: Path, content: str) -> None:
    (tmp_path / "memory.max").write_text(content, encoding="ascii")

    assert memory_limit(tmp_path) is None


def test_garbled_files_leave_detect_standing(tmp_path: Path) -> None:
    root = _v2_tree(tmp_path / "cgroup", "abc", "")
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal: lots kB\nMemAvailable:\n", encoding="ascii")

    found = detect(cgroup_root=root, meminfo=meminfo, cpu_count=lambda: 8, machine=lambda: "x86_64")

    assert found.cores == 8.0
    assert found.memory_limit_bytes is None
    assert found.memory_total_bytes is None
    assert found.memory_available_bytes is None


def test_meminfo_reads_kilobytes_as_bytes(tmp_path: Path) -> None:
    path = _meminfo(tmp_path / "meminfo")

    assert meminfo_bytes(path, "MemTotal") == MEM_TOTAL_KB * KIB
    assert meminfo_bytes(path, "MemAvailable") == MEM_AVAILABLE_KB * KIB
    assert meminfo_bytes(path, "SwapTotal") is None
    assert meminfo_bytes(tmp_path / "missing", "MemTotal") is None


def test_a_directory_in_place_of_a_file_is_none(tmp_path: Path) -> None:
    (tmp_path / "cpu.max").mkdir()
    (tmp_path / "memory.max").mkdir()

    assert cpu_quota(tmp_path) is None
    assert memory_limit(tmp_path) is None


def test_cgroup_v1_without_limits(tmp_path: Path) -> None:
    (tmp_path / "cpu").mkdir()
    (tmp_path / "memory").mkdir()
    (tmp_path / "cpu" / "cpu.cfs_quota_us").write_text("-1\n", encoding="ascii")
    (tmp_path / "cpu" / "cpu.cfs_period_us").write_text("100000\n", encoding="ascii")
    # v1 reports "no limit" as a huge page aligned number, above MemTotal.
    (tmp_path / "memory" / "memory.limit_in_bytes").write_text("9223372036854771712\n", encoding="ascii")
    meminfo = _meminfo(tmp_path / "meminfo")

    found = detect(cgroup_root=tmp_path, meminfo=meminfo, cpu_count=lambda: 6, machine=lambda: "x86_64")

    assert found.cgroup == "v1"
    assert found.cpu_quota is None
    assert found.memory_limit_bytes is None
    assert found.cores == 6.0


def test_cgroup_v1_no_limit_sentinel_without_meminfo_is_no_limit(tmp_path: Path) -> None:
    # The v1 "no limit" sentinel must be discarded even when /proc/meminfo is
    # unreadable and the MemTotal comparison cannot run. Otherwise the sentinel
    # becomes a ~9.2 EB "limit" and the suggestion jumps to performance on a
    # box the detection knows nothing about, against the fail-safe direction
    # of D-24-06.
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "memory.limit_in_bytes").write_text("9223372036854771712\n", encoding="ascii")

    found = detect(cgroup_root=tmp_path, meminfo=tmp_path / "missing", cpu_count=lambda: 6, machine=lambda: "x86_64")

    assert found.cgroup == "v1"
    assert found.memory_limit_bytes is None
    assert found.threshold_memory_bytes is None
    assert found.formula_memory_bytes is None


def test_cgroup_v1_with_limits(tmp_path: Path) -> None:
    (tmp_path / "cpu").mkdir()
    (tmp_path / "memory").mkdir()
    (tmp_path / "cpu" / "cpu.cfs_quota_us").write_text("200000\n", encoding="ascii")
    (tmp_path / "cpu" / "cpu.cfs_period_us").write_text("100000\n", encoding="ascii")
    (tmp_path / "memory" / "memory.limit_in_bytes").write_text("1073741824\n", encoding="ascii")
    meminfo = _meminfo(tmp_path / "meminfo")

    found = detect(cgroup_root=tmp_path, meminfo=meminfo, cpu_count=lambda: 6, machine=lambda: "x86_64")

    assert found.cgroup == "v1"
    assert found.cpu_quota == 2.0
    assert found.cores == 2.0
    assert found.memory_limit_bytes == 1_073_741_824
    assert found.formula_memory_bytes == 1_073_741_824


def test_v1_is_not_read_when_v2_files_exist(tmp_path: Path) -> None:
    _v2_tree(tmp_path, "max 100000", "max")
    (tmp_path / "cpu").mkdir()
    (tmp_path / "cpu" / "cpu.cfs_quota_us").write_text("100000\n", encoding="ascii")
    (tmp_path / "cpu" / "cpu.cfs_period_us").write_text("100000\n", encoding="ascii")

    found = detect(cgroup_root=tmp_path, meminfo=tmp_path / "missing", cpu_count=lambda: 4, machine=lambda: "")

    assert found.cgroup == "v2"
    assert found.cpu_quota is None
    assert found.cores == 4.0


@pytest.mark.parametrize(("cores", "whole"), [(0.5, 1), (1.5, 1), (2.0, 2), (7.9, 7), (None, None)])
def test_cores_whole_is_at_least_one(cores: float | None, whole: int | None) -> None:
    hardware = Hardware(
        cpu_count=None,
        cpu_quota=None,
        cores=cores,
        memory_limit_bytes=None,
        memory_available_bytes=None,
        memory_total_bytes=None,
        architecture="",
        cgroup="none",
    )

    assert hardware.cores_whole == whole


def test_formula_memory_falls_back_to_the_known_half() -> None:
    limit_only = Hardware(
        cpu_count=None,
        cpu_quota=None,
        cores=None,
        memory_limit_bytes=2_000,
        memory_available_bytes=None,
        memory_total_bytes=None,
        architecture="",
        cgroup="v2",
    )

    assert limit_only.formula_memory_bytes == 2_000
    assert limit_only.threshold_memory_bytes == 2_000


def test_the_snapshot_is_frozen(tmp_path: Path) -> None:
    found = detect(cgroup_root=tmp_path, meminfo=tmp_path / "missing", cpu_count=lambda: 1, machine=lambda: "")

    with pytest.raises(AttributeError):
        found.cores = 3.0  # type: ignore[misc]
