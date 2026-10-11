"""HEIC in the built image (FMT-05, D-31-06): an OCR proof and a memory measurement.

Not named ``test_*`` on purpose: pytest must not collect it. It needs the
tesseract engine, the pillow-heif wheel of the image and a Linux
``/proc/self/status``, which exist in the image and on no development machine.
It lives under ``tests`` because that is the directory ``docker.yml`` bind mounts
into the container, the way ``probe_image_ocr_czech.py`` travels in.

**Part 1, the proof (a gate).** A HEIC with a rendered sentence is written by the
HEIF encoder in the wheel and read by ``findling.extract.image.extract_image`` in
a child that sets RLIMIT_AS to ``extract_address_space_bytes`` and pins the
native thread pools, as the extraction child of ``sandbox.py`` does. The verdict
has to be indexed and the text has to carry ``fotoquendel``. The empty answer is
the trap of every OCR proof (T-06-49), so a white HEIC of the same size has to
come back as skipped(empty_text). The child also states the four options the
opener was registered with. A miss in any of these ends the script with exit
code 1.

**Part 2, the measurement (no gate).** For 12, 24 and 48 megapixels (4032 x
3024, 5712 x 4284, 8064 x 6048, the three sizes of an iPhone camera), one HEIC
encoded as a grid of 512 pixel tiles like an Apple device writes it, and one
JPEG of the same canvas as the counter measurement. Each file is read in fresh
children, three times, and the median is printed:

- ``load``: a child without any cap imports the picture branch, reads VmSize and
  VmRSS from ``/proc/self/status``, runs ``Image.open(path).load()`` with no
  draft and reads VmPeak and VmHWM. vmpeak_delta is VmPeak after minus VmSize
  before, the extra address space the decode needed, which is what RLIMIT_AS
  counts; vmhwm_delta is VmHWM after minus VmRSS before, the resident side.
- ``load-capped``: the same load in a child under the real cap, without the
  estimate in front of it. It answers whether the decode fits under the cap at
  all (``ok``, or ``MemoryError``), which the estimate of the branch decides
  before a single row is decoded and which the checkpoint of plan 31-07 asks.
- ``extract``: a child under the real cap, set up like the one above, runs the
  full ``extract_image`` and states its verdict, the room the estimate saw, the
  estimate itself, and the same two deltas over the whole run.

For assumption A5 one more line, ``heic-threads``: the 24 MP HEIC loaded without
a cap with the library default of four decoder threads, against the one thread
the branch registers.

**Part 3, glibc malloc arenas (no gate, owner decision at the checkpoint of
plan 31-07).** The fixed part of the HEIF cost looked like the malloc arena of
the decoder thread. Each child of this part runs with ``MALLOC_ARENA_MAX``
unset, 1 or 2 in its environment, which glibc reads when the process starts and
which the tesseract grandchild inherits:

- ``heic-arena``: the HEIC of 12, 24 and 48 MP, loaded without a cap (VmPeak
  growth), and the full ``extract_image`` under the real cap with the estimate
  switched off (``full``), so the line says whether the whole way fits and how
  high the absolute VmPeak of the child went, against 90 percent of the cap.
- ``arena-path``: the ordinary text and OCR ways of the child through
  ``dispatch.extract`` on corpus files (text PDF, DOCX, scanned PDF on the OCR
  route, JPEG), with verdict, seconds, absolute VmPeak and VmHWM, so a cost of a
  smaller arena count on the rest of the child shows.

One line per size and format, starting with ``heic-ram``, so the report can
take them from the log. Nothing in part 2 fails the step: a child under the cap
that dies instead of answering is a finding and is printed as the verdict
``child_died``, and a run without an answer prints ``n/a``.

The sentence is self written and rendered with DejaVu Sans (``testdata/fonts``,
licence in ``COPYING.dejavu``); every picture is made at run time, nothing is a
photograph. Nothing recognised is printed except the expected word found.

Run it like this:

    docker run --rm --network none -v "$PWD/backend/tests:/probe:ro" \\
        -v "$PWD/testdata/fonts:/fonts:ro" -v "$PWD/testdata/corpus:/corpus:ro" \\
        --entrypoint python IMAGE /probe/probe_image_ocr_heic.py /fonts/DejaVuSans.ttf /corpus
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Final

import pillow_heif
from PIL import Image, ImageDraw, ImageFont

TERM: Final = "fotoquendel"
SENTENCE: Final = f"{TERM} im Kellerraum der Gemeinde"
DEFAULT_FONT: Final = "/fonts/DejaVuSans.ttf"

# The page of part 1: over the minimum edge of the picture branch, so it is a
# plausible document, and small enough to cost nothing.
PROOF_SIZE: Final = (1200, 300)

# The three iPhone sizes: 12 MP main camera, 24 MP default of the newer models,
# 48 MP "HEIF Max".
SIZES: Final = {12: (4032, 3024), 24: (5712, 4284), 48: (8064, 6048)}
REPEATS: Final = 3
THREADS_PROBE_MP: Final = 24

# Apple writes HEIC as a grid of 512 pixel tiles; the encoder in the wheel does
# the same when this option is set (pillow-heif options.GRID_TILE_SIZE).
GRID_TILE: Final = 512

# Self abort of every child, and the parent's wait on top of it. A child that
# hangs ends itself by SIGALRM; the parent does not wait longer than this.
CHILD_SECONDS: Final = 180
PARENT_SECONDS: Final = CHILD_SECONDS + 30

MIB: Final = 1024 * 1024

# Part 3: the values of MALLOC_ARENA_MAX, None for unset.
ARENAS: Final = (None, "1", "2")

# Part 3: the ordinary ways of the child, as (file in the corpus, mimetype,
# forced route or None). Text PDF, Office, the scan on the OCR route, a picture.
PATHS: Final = (
    ("01-text-layer.pdf", "application/pdf", None),
    ("10-kuendigung.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", None),
    ("13-ratsvorlage-scan.pdf", "application/pdf", "ocr"),
    ("17-beleg.jpg", "image/jpeg", None),
)
DEFAULT_CORPUS: Final = "/corpus"


def _status() -> dict[str, int]:
    """VmPeak, VmSize, VmHWM and VmRSS of this process in bytes."""
    wanted = ("VmPeak", "VmSize", "VmHWM", "VmRSS")
    values: dict[str, int] = {}
    for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
        name, _, rest = line.partition(":")
        if name in wanted:
            values[name] = int(rest.split()[0]) * 1024
    return values


def _child_setup(capped: bool) -> None:
    """What the extraction child of sandbox.py does before its first import, minus the session."""
    if sys.platform == "win32":
        raise SystemExit("this probe measures /proc/self/status and RLIMIT_AS, it runs in the Linux image")
    import signal

    signal.alarm(CHILD_SECONDS)
    if capped:
        import resource

        from findling.config import settings

        cap = settings().extract_address_space_bytes
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"


def _child_load(path: str, *, capped: bool, threads: int = 1) -> dict[str, object]:
    _child_setup(capped=capped)
    from findling.extract import image  # noqa: F401 - registers the HEIF opener

    if threads != 1:
        pillow_heif.register_heif_opener(decode_threads=threads)
    before = _status()
    try:
        with Image.open(path) as picture:
            picture.load()
        loaded = "ok"
    except MemoryError:
        loaded = "MemoryError"
    after = _status()
    return {
        "loaded": loaded,
        "vmpeak_delta": after["VmPeak"] - before["VmSize"],
        "vmhwm_delta": after["VmHWM"] - before["VmRSS"],
    }


def _child_extract(path: str) -> dict[str, object]:
    _child_setup(capped=True)
    from findling.config import settings
    from findling.extract import image

    before = _status()
    room = image._address_space_room()
    with Image.open(path) as picture:
        image._decode_smaller(picture)
        estimate = image._estimated_bytes(picture)
    try:
        outcome = image.extract_image(path)
        verdict = f"{outcome.state.value}/{outcome.reason.value if outcome.reason else '-'}"
        text = outcome.text
    except MemoryError:
        # What the child loop of sandbox.py turns into failed(out_of_memory).
        verdict = "failed/out_of_memory(MemoryError)"
        text = ""
    after = _status()
    return {
        "verdict": verdict,
        "found": TERM in text.lower(),
        "room": room,
        "estimate": estimate,
        "cap": settings().extract_address_space_bytes,
        "vmpeak_delta": after["VmPeak"] - before["VmSize"],
        "vmhwm_delta": after["VmHWM"] - before["VmRSS"],
        "options": [
            pillow_heif.options.THUMBNAILS,
            pillow_heif.options.DEPTH_IMAGES,
            pillow_heif.options.AUX_IMAGES,
            pillow_heif.options.DECODE_THREADS,
        ],
    }


def _child_full(path: str) -> dict[str, object]:
    """The whole picture branch under the cap, with the estimate switched off."""
    _child_setup(capped=True)
    from findling.extract import image

    image._over_address_space = lambda _picture: None
    before = _status()
    started = time.monotonic()
    try:
        outcome = image.extract_image(path)
        verdict = f"{outcome.state.value}/{outcome.reason.value if outcome.reason else '-'}"
    except MemoryError:
        verdict = "failed/out_of_memory(MemoryError)"
    seconds = time.monotonic() - started
    after = _status()
    return {
        "verdict": verdict,
        "seconds": seconds,
        "start": before["VmSize"],
        "vmpeak": after["VmPeak"],
        "vmhwm": after["VmHWM"],
        "vmpeak_delta": after["VmPeak"] - before["VmSize"],
    }


def _child_path(path: str, mime: str, route: str) -> dict[str, object]:
    """One file through dispatch.extract, the way the extraction child calls it."""
    _child_setup(capped=True)
    from findling.extract.dispatch import Route, extract

    before = _status()
    started = time.monotonic()
    try:
        outcome = extract(path, mime, Path(path).stat().st_size, Route(route) if route != "-" else None)
        verdict = f"{outcome.state.value}/{outcome.reason.value if outcome.reason else '-'}"
    except MemoryError:
        verdict = "failed/out_of_memory(MemoryError)"
    seconds = time.monotonic() - started
    after = _status()
    return {
        "verdict": verdict,
        "seconds": seconds,
        "start": before["VmSize"],
        "vmpeak": after["VmPeak"],
        "vmhwm": after["VmHWM"],
    }


def _ask(mode: str, path: Path, *extra: str, arena: str | None = None) -> dict[str, object] | None:
    """Run one child and return what it printed, or None when it gave no answer."""
    environment = dict(os.environ)
    environment.pop("MALLOC_ARENA_MAX", None)
    if arena is not None:
        environment["MALLOC_ARENA_MAX"] = arena
    try:
        finished = subprocess.run(  # noqa: S603 - our own interpreter and this very file
            [sys.executable, __file__, "--child", mode, str(path), *extra],
            capture_output=True,
            check=False,
            env=environment,
            timeout=PARENT_SECONDS,
            text=True,
        )
    except subprocess.TimeoutExpired:
        print(f"child {mode} {path.name}: no answer within {PARENT_SECONDS} s")
        return None
    lines = finished.stdout.strip().splitlines()
    if finished.returncode != 0 or not lines:
        tail = finished.stderr.strip().splitlines()[-1:] or ["(no stderr)"]
        print(f"child {mode} {path.name}: exit {finished.returncode}, {tail[0]}")
        return None
    answer = json.loads(lines[-1])
    assert isinstance(answer, dict)
    return answer


def _canvas(size: tuple[int, int], font_path: str | None) -> Image.Image:
    """A white RGB page, with the sentence on it when a font is given."""
    picture = Image.new("RGB", size, color="white")
    if font_path is not None:
        font = ImageFont.truetype(font_path, max(24, size[1] // 20))
        ImageDraw.Draw(picture).text((size[0] // 20, size[1] // 3), SENTENCE, fill="black", font=font)
    return picture


def _write_heic(path: Path, size: tuple[int, int], font_path: str | None, *, grid: bool) -> None:
    pillow_heif.options.GRID_TILE_SIZE = GRID_TILE if grid else 0
    with _canvas(size, font_path) as picture:
        pillow_heif.from_pillow(picture).save(path, quality=80, enc_params={"preset": "ultrafast"})


def _write_jpeg(path: Path, size: tuple[int, int], font_path: str) -> None:
    with _canvas(size, font_path) as picture:
        picture.save(path, format="JPEG", quality=85)


def _proof(folder: Path, font_path: str) -> bool:
    page = folder / "proof.heic"
    blank = folder / "blank.heic"
    _write_heic(page, PROOF_SIZE, font_path, grid=False)
    _write_heic(blank, PROOF_SIZE, None, grid=False)

    read = _ask("extract", page)
    white = _ask("extract", blank)
    if read is None or white is None:
        return False
    options = read["options"]
    print(f"heic opener options thumbnails,depth,aux,threads: {options}")
    print(f"heic page: verdict {read['verdict']}, {TERM} found: {read['found']}")
    print(f"white heic page: verdict {white['verdict']} (must be skipped/empty_text)")
    return (
        options == [False, False, False, 1]
        and read["verdict"] in ("indexed/-", "indexed/truncated")
        and read["found"] is True
        and white["verdict"] == "skipped/empty_text"
    )


def _threads(arch: str, path: Path) -> None:
    """Assumption A5: four decoder threads against one, the 24 MP HEIC without a cap."""
    for mode, threads in (("load", 1), ("load-threads4", 4)):
        loads = [answer for answer in (_ask(mode, path) for _ in range(REPEATS)) if answer is not None]
        print(
            f"heic-threads arch={arch} mp={THREADS_PROBE_MP} decode_threads={threads} "
            f"vmpeak_delta_mib={_mib(loads, 'vmpeak_delta')} vmhwm_delta_mib={_mib(loads, 'vmhwm_delta')} "
            f"loads={len(loads)}/{REPEATS}"
        )


def _seconds(answers: list[dict[str, object]]) -> str:
    values = [float(str(answer["seconds"])) for answer in answers if answer.get("seconds") is not None]
    return f"{statistics.median(values):.2f}" if values else "n/a"


def _arenas(folder: Path, font_path: str, corpus: Path) -> None:
    """Part 3: MALLOC_ARENA_MAX unset, 1 and 2, on the HEIC and on the ordinary ways."""
    arch = platform.machine()
    pictures = {megapixels: folder / f"arena-{megapixels}.heic" for megapixels in SIZES}
    for megapixels, size in SIZES.items():
        _write_heic(pictures[megapixels], size, font_path, grid=True)
    for arena in ARENAS:
        label = arena or "unset"
        for megapixels, path in pictures.items():
            loads = [answer for answer in (_ask("load", path, arena=arena) for _ in range(REPEATS)) if answer]
            fulls = [_ask("full", path, arena=arena) or {"verdict": "child_died"} for _ in range(REPEATS)]
            print(
                f"heic-arena arch={arch} arena={label} mp={megapixels} "
                f"load_vmpeak_delta_mib={_mib(loads, 'vmpeak_delta')} "
                f"load_vmhwm_delta_mib={_mib(loads, 'vmhwm_delta')} "
                f"full_start_mib={_mib(fulls, 'start')} "
                f"full_vmpeak_mib={_mib(fulls, 'vmpeak')} "
                f"full_vmpeak_delta_mib={_mib(fulls, 'vmpeak_delta')} "
                f"full_vmhwm_mib={_mib(fulls, 'vmhwm')} "
                f"full_seconds={_seconds(fulls)} "
                f"full_verdict={','.join(sorted({str(answer['verdict']) for answer in fulls}))}"
            )
        for name, mime, route in PATHS:
            source = corpus / name
            runs = [
                _ask("path", source, mime, route or "-", arena=arena) or {"verdict": "child_died"}
                for _ in range(REPEATS)
            ]
            print(
                f"arena-path arch={arch} arena={label} file={name} "
                f"start_mib={_mib(runs, 'start')} vmpeak_mib={_mib(runs, 'vmpeak')} "
                f"vmhwm_mib={_mib(runs, 'vmhwm')} seconds={_seconds(runs)} "
                f"verdict={','.join(sorted({str(answer['verdict']) for answer in runs}))}"
            )


def _mib(answers: list[dict[str, object]], key: str) -> str:
    """The median of one field over the answers, in MiB, or n/a without any."""
    values = [int(str(answer[key])) for answer in answers if answer.get(key) is not None]
    return f"{statistics.median(values) / MIB:.1f}" if values else "n/a"


def _measure(folder: Path, font_path: str) -> None:
    arch = platform.machine()
    for megapixels, size in SIZES.items():
        files = {"HEIF": folder / f"{megapixels}.heic", "JPEG": folder / f"{megapixels}.jpg"}
        _write_heic(files["HEIF"], size, font_path, grid=True)
        _write_jpeg(files["JPEG"], size, font_path)
        pixels = size[0] * size[1]
        for fmt, path in files.items():
            loads = [answer for answer in (_ask("load", path) for _ in range(REPEATS)) if answer is not None]
            capped = [_ask("load-capped", path) or {"loaded": "child_died"} for _ in range(REPEATS)]
            runs = [_ask("extract", path) or {"verdict": "child_died"} for _ in range(REPEATS)]
            peaks = [int(str(answer["vmpeak_delta"])) for answer in loads]
            per_pixel = f"{statistics.median(peaks) / pixels:.2f}" if peaks else "n/a"
            verdicts = sorted({str(answer["verdict"]) for answer in runs})
            print(
                f"heic-ram arch={arch} mp={megapixels} fmt={fmt} "
                f"vmpeak_delta_mib={_mib(loads, 'vmpeak_delta')} "
                f"vmhwm_delta_mib={_mib(loads, 'vmhwm_delta')} "
                f"bytes_per_pixel={per_pixel} "
                f"extract_vmpeak_delta_mib={_mib(runs, 'vmpeak_delta')} "
                f"extract_vmhwm_delta_mib={_mib(runs, 'vmhwm_delta')} "
                f"room_mib={_mib(runs, 'room')} "
                f"estimate_mib={_mib(runs, 'estimate')} "
                f"found={all(answer.get('found') is True for answer in runs)} "
                f"loads={len(loads)}/{REPEATS} "
                f"capped_load={','.join(sorted({str(answer['loaded']) for answer in capped}))} "
                f"capped_vmpeak_delta_mib={_mib(capped, 'vmpeak_delta')} "
                f"verdict={','.join(verdicts)}"
            )
            if fmt == "HEIF" and megapixels == THREADS_PROBE_MP:
                _threads(arch, path)
            path.unlink()


def main(argv: list[str]) -> int:
    """Run both parts and return the exit code."""
    if len(argv) >= 4 and argv[1] == "--child":
        mode, path = argv[2], argv[3]
        if mode == "extract":
            answer = _child_extract(path)
        elif mode == "full":
            answer = _child_full(path)
        elif mode == "path":
            answer = _child_path(path, argv[4], argv[5])
        else:
            answer = _child_load(path, capped=mode == "load-capped", threads=4 if mode == "load-threads4" else 1)
        print(json.dumps(answer))
        return 0

    font_path = argv[1] if len(argv) > 1 else DEFAULT_FONT
    if not Path(font_path).is_file():
        print(f"font missing: {font_path}")
        return 2
    corpus = Path(argv[2] if len(argv) > 2 else DEFAULT_CORPUS)

    with tempfile.TemporaryDirectory(prefix="heic-probe-") as name:
        folder = Path(name)
        proved = _proof(folder, font_path)
        print("heic ocr in the image: " + ("ok" if proved else "FAILED"))
        _measure(folder, font_path)
        if corpus.is_dir():
            _arenas(folder, font_path, corpus)
        else:
            print(f"corpus missing: {corpus}, part 3 skipped")
    return 0 if proved else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
