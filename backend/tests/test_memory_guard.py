"""The RAM condition reads anon against memory.max, never memory.current (PAR-04).

The tantivy index is memory mapped, so its page cache shows up in
memory.current and in the ``file`` line of memory.stat. The kernel hands that
back under pressure, so counting it as used would refuse a second slot on
exactly the boxes that have room for one (25-RESEARCH.md, Pitfall 7). Every
file is read from a fake tree under ``tmp_path``; no real /sys is touched.

The second half is the fail safe direction: nothing readable means not
admitted, which leaves the work serial.
"""

from __future__ import annotations

from pathlib import Path

from findling.memory_guard import admits, anon_bytes, headroom_bytes

GIB = 1024**3
KIB = 1024


def _tree(
    root: Path,
    *,
    memory_max: str | None,
    anon: int | None = None,
    file_cache: int = 10 * GIB,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if memory_max is not None:
        (root / "memory.max").write_text(memory_max + "\n", encoding="ascii")
    if anon is not None:
        (root / "memory.stat").write_text(
            f"anon {anon}\nfile {file_cache}\nkernel 1048576\nshmem 0\n",
            encoding="ascii",
        )
    # A value no reader may trust. If memory.current were ever read, every
    # result below would be wrong.
    (root / "memory.current").write_text(f"{64 * GIB}\n", encoding="ascii")
    return root


def _meminfo(path: Path, available: int | None) -> Path:
    lines = ["MemTotal:       16000000 kB", "MemFree:         1000000 kB"]
    if available is not None:
        lines.append(f"MemAvailable:   {available // KIB} kB")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


def test_the_page_cache_does_not_count_as_used(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max=str(4 * GIB), anon=1 * GIB, file_cache=10 * GIB)
    meminfo = _meminfo(tmp_path / "meminfo", 8 * GIB)

    assert headroom_bytes(cgroup_root=root, meminfo=meminfo) == 3 * GIB


def test_the_smaller_of_limit_headroom_and_memavailable_wins(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max=str(4 * GIB), anon=1 * GIB)
    meminfo = _meminfo(tmp_path / "meminfo", 2 * GIB)

    assert headroom_bytes(cgroup_root=root, meminfo=meminfo) == 2 * GIB


def test_no_limit_means_memavailable(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max="max", anon=1 * GIB)
    meminfo = _meminfo(tmp_path / "meminfo", 5 * GIB)

    assert headroom_bytes(cgroup_root=root, meminfo=meminfo) == 5 * GIB


def test_a_missing_memory_stat_falls_back_to_memavailable(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max=str(4 * GIB))
    meminfo = _meminfo(tmp_path / "meminfo", 3 * GIB)

    assert headroom_bytes(cgroup_root=root, meminfo=meminfo) == 3 * GIB
    assert headroom_bytes(cgroup_root=root, meminfo=tmp_path / "absent") is None


def test_a_memory_stat_without_an_anon_line_falls_back_to_memavailable(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max=str(4 * GIB))
    (root / "memory.stat").write_text("file 1024\nkernel 2048\n", encoding="ascii")
    meminfo = _meminfo(tmp_path / "meminfo", 3 * GIB)

    assert anon_bytes(root) is None
    assert headroom_bytes(cgroup_root=root, meminfo=meminfo) == 3 * GIB
    assert headroom_bytes(cgroup_root=root, meminfo=_meminfo(tmp_path / "bare", None)) is None


def test_nothing_readable_is_none(tmp_path: Path) -> None:
    assert headroom_bytes(cgroup_root=tmp_path / "nowhere", meminfo=tmp_path / "nothing") is None


def test_anon_above_the_limit_is_no_headroom_rather_than_negative(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max=str(1 * GIB), anon=2 * GIB)
    meminfo = _meminfo(tmp_path / "meminfo", 8 * GIB)

    assert headroom_bytes(cgroup_root=root, meminfo=meminfo) == 0


def test_anon_is_read_from_memory_stat(tmp_path: Path) -> None:
    root = _tree(tmp_path / "cg", memory_max="max", anon=123_456)

    assert anon_bytes(root) == 123_456
    assert anon_bytes(tmp_path / "nowhere") is None


def test_admission_needs_a_readable_headroom_of_at_least_the_need() -> None:
    assert admits(None, need=1) is False
    assert admits(10, need=10) is True
    assert admits(9, need=10) is False
