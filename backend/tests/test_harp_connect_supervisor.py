"""The tunnel watcher of docker/harp_connect.sh (ZERT-01, owner decision D-37-09).

Under HaRP the script no longer replaces itself with frpc. It stays in front of
it as a small watcher: it passes every frpc line through, recognises the x509
failure of a reissued HaRP CA and reports it with the remedy on a slowing
schedule, restarts frpc once when the files under /certs/frp change and settle,
caps those restarts per window, never switches to a weaker transport mode, and
never exits 0 while HaRP is the deployment, because docker/init.sh reads 0 as
"no HaRP here".

Every case runs a stub in place of frpc (FINDLING_FRPC_BIN) and shortened
timing knobs. The watcher needs bash, mkfifo, sha256sum and POSIX signals, so
the module runs on Linux only: in the gates job of python.yml, and on a
developer box under WSL. On Windows it is skipped as a whole.
"""

import contextlib
import os
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "docker" / "harp_connect.sh"
INIT = SCRIPT.with_name("init.sh")
BASH = shutil.which("bash") or "bash"

SHARED_KEY = "findling-38-secret-key"
CERT_FILES = ("ca.crt", "client.crt", "client.key")

REMEDY = "harp_connect: the tunnel certificate is possibly no longer accepted by HaRP"
RESTART = "restarting frpc"
FIRST_RESTART = "(restart 1 of at most"
CAP_LINE = "restart cap reached"
CONNECTED = "harp_connect: the tunnel is connected again"
MISSING = "missing or not readable"
NOT_WHOLE = "which is not a whole number"

pytestmark = [
    pytest.mark.skipif(
        sys.platform == "win32",
        reason="the watcher needs bash, a FIFO and POSIX signals; it is proven on Linux (python.yml gates, WSL)",
    ),
    pytest.mark.skipif(
        any(shutil.which(tool) is None for tool in ("bash", "mkfifo", "sha256sum")),
        reason="bash, mkfifo or sha256sum is missing on this machine",
    ),
]

# A stand-in for frpc 0.61.1. It records every start, reacts to TERM at once
# (every pause is a background sleep plus wait, so the trap is never stuck
# behind a foreground sleep), and prints the lines of the real binary from
# issue #33. It never prints the shared key.
STUB = r"""#!/bin/bash
printf 'start\n' >>"${STUB_LOG}"
sleeper=""
on_term() {
	printf 'term\n' >>"${STUB_LOG}"
	if [ -n "${sleeper}" ]; then
		kill "${sleeper}" 2>/dev/null
	fi
	exit 143
}
trap on_term TERM
pause() {
	sleep "$1" >/dev/null 2>&1 &
	sleeper=$!
	wait "${sleeper}"
	sleeper=""
}
config=""
if [ "${1:-}" = "-c" ]; then
	config="${2:-}"
fi
X509='[W] [client/service.go:298] [5f1c2a9b] connect to server error: tls: failed to verify certificate: '
X509+='x509: certificate signed by unknown authority (possibly because of "crypto/rsa: verification error" '
X509+='while trying to verify candidate authority certificate "harp.nc")'
SHUTDOWN='[W] [client/service.go:298] [5f1c2a9b] connect to server error: session shutdown'
REFUSED='[W] [client/service.go:298] [5f1c2a9b] connect to server error: '
REFUSED+='dial tcp 127.0.0.1:8782: connect: connection refused'
LOGIN='[I] [client/service.go:310] [5f1c2a9b] login to server success, get run id [5f1c2a9b]'
printf '%s\n' '[I] [client/service.go:295] [5f1c2a9b] try to connect to server...'
case "${STUB_BEHAVIOUR}" in
x509)
	while :; do
		printf '%s\n' "${X509}"
		pause 0.2
	done
	;;
shutdown)
	# Run 40704387898: after a reissue frps may refuse every dial before frpc
	# gets to verify the server, so no x509 line ever appears.
	while :; do
		printf '%s
' "${SHUTDOWN}"
		pause 0.2
	done
	;;
flaky)
	# Three refused logins, then a success, over and over: a tunnel that keeps
	# coming back is not a certificate problem.
	while :; do
		for _ in 1 2 3; do
			printf '%s
' "${SHUTDOWN}"
			pause 0.2
		done
		printf '%s
' "${LOGIN}"
		pause 0.2
	done
	;;
refused)
	while :; do
		printf '%s
' "${REFUSED}"
		pause 0.2
	done
	;;
exit0)
	exit 0
	;;
exit3)
	exit 3
	;;
quiet)
	while :; do
		pause 1
	done
	;;
auto)
	while :; do
		if grep -q certFile "${config}" && grep -q GOOD "${HP_FRP_CERT_DIR}/ca.crt" 2>/dev/null; then
			printf '%s\n' '[I] [client/service.go:310] [5f1c2a9b] login to server success, get run id [5f1c2a9b]'
			while :; do
				pause 1
			done
		fi
		printf '%s\n' "${X509}"
		pause 0.2
	done
	;;
esac
"""


@dataclass
class Watcher:
    process: subprocess.Popen[str]
    stub_log: Path
    run_dir: Path
    cert_dir: Path
    lines: list[str] = field(default_factory=list)

    def output(self) -> list[str]:
        return list(self.lines)

    def count(self, needle: str) -> int:
        return sum(needle in line for line in self.output())

    def starts(self) -> int:
        if not self.stub_log.exists():
            return 0
        return self.stub_log.read_text(encoding="utf-8").splitlines().count("start")

    def config(self) -> str:
        return (self.run_dir / "frpc.toml").read_text(encoding="utf-8")


def _until(condition: Callable[[], bool], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.05)
    return condition()


def _replace(path: Path, text: str) -> None:
    # The documented copy path: write a temporary file next to the target and
    # move it over the target, so no reader ever sees half a file.
    temporary = path.with_name(f".{path.name}.new")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _write_certs(cert_dir: Path, tag: str) -> None:
    cert_dir.mkdir(parents=True, exist_ok=True)
    for name in CERT_FILES:
        _replace(cert_dir / name, f"{tag} {name}\n")


def _flap(cert_dir: Path, period: float, duration: float) -> None:
    start = time.monotonic()
    turn = 1
    while (due := start + turn * period) < start + duration:
        time.sleep(max(0.0, due - time.monotonic()))
        _write_certs(cert_dir, f"turn {turn}")
        turn += 1
    time.sleep(max(0.0, start + duration - time.monotonic()))


def _pump(process: subprocess.Popen[str], lines: list[str]) -> None:
    stream = process.stdout
    assert stream is not None
    for line in stream:
        lines.append(line.rstrip("\n"))


@contextlib.contextmanager
def _watch(tmp_path: Path, behaviour: str = "x509", **knobs: str | None) -> Iterator[Watcher]:
    stub = tmp_path / "frpc-stub"
    stub.write_text(STUB, encoding="utf-8", newline="\n")
    stub.chmod(0o755)
    run_dir = tmp_path / "run"
    cert_dir = tmp_path / "certs"
    stub_log = tmp_path / "stub.log"
    settings: dict[str, str | None] = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HP_SHARED_KEY": SHARED_KEY,
        "HP_FRP_ADDRESS": "127.0.0.1",
        "HP_FRP_PORT": "8782",
        "APP_PORT": "23000",
        "APP_ID": "findling_backend",
        "HP_FRP_CERT_DIR": str(cert_dir),
        "FINDLING_RUN_DIR": str(run_dir),
        "FINDLING_FRPC_BIN": str(stub),
        "FINDLING_HARP_CERT_POLL_SECONDS": "1",
        "FINDLING_HARP_RESTART_MIN_GAP_SECONDS": "0",
        "STUB_LOG": str(stub_log),
        "STUB_BEHAVIOUR": behaviour,
        **knobs,
    }
    environment = {name: value for name, value in settings.items() if value is not None}
    process = subprocess.Popen(  # noqa: S603 - an argument list, never a shell
        [BASH, str(SCRIPT)],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    watcher = Watcher(process=process, stub_log=stub_log, run_dir=run_dir, cert_dir=cert_dir)
    reader = threading.Thread(target=_pump, args=(process, watcher.lines), daemon=True)
    reader.start()
    try:
        yield watcher
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        reader.join(timeout=5)


def _run_to_exit(tmp_path: Path, behaviour: str = "x509", **knobs: str | None) -> tuple[int, Watcher]:
    with _watch(tmp_path, behaviour, **knobs) as watcher:
        code = watcher.process.wait(timeout=15)
    return code, watcher


def _running(watcher: Watcher) -> None:
    assert _until(lambda: watcher.starts() >= 1 and len(watcher.lines) >= 1, 10), watcher.output()


# Exit code contract with docker/init.sh


def test_without_a_shared_key_the_script_steps_aside_with_0(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, HP_SHARED_KEY=None)
    assert code == 0
    assert watcher.count("HP_SHARED_KEY is not set, no HaRP tunnel is opened") == 1
    assert watcher.starts() == 0


def test_a_missing_address_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, HP_FRP_ADDRESS=None)
    assert code == 78
    assert watcher.count("refusing to write a half configured tunnel") == 1
    assert watcher.starts() == 0


def test_a_port_that_is_not_a_number_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, HP_FRP_PORT="80a")
    assert code == 78
    assert watcher.count("which is not a port number") == 1


def test_a_restart_cap_that_is_not_a_number_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, FINDLING_HARP_RESTART_CAP="x")
    assert code == 78
    assert watcher.count(NOT_WHOLE) == 1
    assert watcher.starts() == 0


def test_a_poll_interval_of_zero_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, FINDLING_HARP_CERT_POLL_SECONDS="0")
    assert code == 78
    assert watcher.starts() == 0


def test_a_remedy_schedule_with_a_word_in_it_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, FINDLING_HARP_REMEDY_SCHEDULE="0,x")
    assert code == 78
    assert watcher.count("which is not a list of whole seconds") == 1
    assert watcher.starts() == 0


def test_a_suspect_threshold_of_zero_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, FINDLING_HARP_SUSPECT_AFTER_ERRORS="0")
    assert code == 78
    assert watcher.count("FINDLING_HARP_SUSPECT_AFTER_ERRORS") == 1
    assert watcher.starts() == 0


def test_a_cap_window_of_zero_is_a_configuration_error(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, FINDLING_HARP_CAP_WINDOW_SECONDS="0")
    assert code == 78
    assert watcher.starts() == 0


def test_an_unwritable_run_directory_exits_73_before_frpc_starts(tmp_path: Path) -> None:
    # A path below a regular file cannot be created, not even by root.
    blocker = tmp_path / "afile"
    blocker.write_text("not a directory\n", encoding="utf-8")
    code, watcher = _run_to_exit(tmp_path, FINDLING_RUN_DIR=str(blocker / "run"))
    assert code == 73
    assert watcher.count("harp_connect: cannot write") == 1
    assert watcher.starts() == 0


def test_frpc_ending_with_0_never_ends_the_script_with_0(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, "exit0")
    assert code == 1
    assert watcher.count("harp_connect: frpc exited with status 0") == 1


def test_frpc_ending_with_3_ends_the_script_with_3(tmp_path: Path) -> None:
    code, watcher = _run_to_exit(tmp_path, "exit3")
    assert code == 3
    assert watcher.count("harp_connect: frpc exited with status 3") == 1


def test_a_stop_signal_reaches_frpc_and_the_script_ends_with_0(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path) as watcher:
        assert _until(lambda: watcher.count("x509: ") >= 1, 10), watcher.output()
        watcher.process.send_signal(signal.SIGTERM)
        code = watcher.process.wait(timeout=5)
    assert code == 0
    assert "term" in watcher.stub_log.read_text(encoding="utf-8").splitlines()


# x509 recognition and the remedy line


def test_x509_with_unchanged_files_reports_once_and_never_restarts(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path) as watcher:
        _running(watcher)
        time.sleep(5)
        assert watcher.starts() == 1
        assert watcher.count(REMEDY) == 1
        assert watcher.count(RESTART) == 0
        assert watcher.count("x509: certificate signed by unknown authority") >= 10


def _errors_before_first_remedy(lines: list[str]) -> int:
    errors = 0
    for line in lines:
        if REMEDY in line:
            return errors
        if "connect to server error:" in line:
            errors += 1
    return -1


def test_x509_reports_at_the_very_first_error(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, FINDLING_HARP_SUSPECT_AFTER_ERRORS="5") as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()
        assert _errors_before_first_remedy(watcher.output()) == 1


def test_repeated_session_shutdown_reports_after_the_threshold(tmp_path: Path) -> None:
    # The shutdown path of run 40704387898: no x509 line at all.
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "shutdown", FINDLING_HARP_SUSPECT_AFTER_ERRORS="4") as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()
        assert _errors_before_first_remedy(watcher.output()) == 4
        time.sleep(3)
        assert watcher.count(REMEDY) == 1
        assert watcher.count(RESTART) == 0
        assert watcher.starts() == 1
        assert watcher.count("x509: ") == 0


def test_repeated_session_shutdown_follows_the_remedy_schedule(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(
        tmp_path,
        "shutdown",
        FINDLING_HARP_SUSPECT_AFTER_ERRORS="2",
        FINDLING_HARP_REMEDY_SCHEDULE="0,2,4",
        FINDLING_HARP_REMEDY_REPEAT_SECONDS="3",
    ) as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()
        first = time.monotonic()
        time.sleep(max(0.0, first + 8.5 - time.monotonic()))
        assert watcher.count(REMEDY) == 4
        assert watcher.count(RESTART) == 0


def test_a_login_between_failures_resets_the_count(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "flaky", FINDLING_HARP_SUSPECT_AFTER_ERRORS="4") as watcher:
        assert _until(lambda: watcher.count("login to server success") >= 4, 10), watcher.output()
        assert watcher.count(REMEDY) == 0
        assert watcher.count(CONNECTED) == 0


def test_the_same_failures_without_the_logins_do_report(tmp_path: Path) -> None:
    # Positive control for the case above: the same threshold over shutdown
    # lines alone reports, so the case above is silent because of the logins.
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "shutdown", FINDLING_HARP_SUSPECT_AFTER_ERRORS="4") as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()


def test_a_refused_connection_is_not_taken_for_a_certificate_problem(tmp_path: Path) -> None:
    # "dial tcp ... connection refused" means HaRP is not up; the certificate
    # never got a say, so it does not count towards the threshold.
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "refused", FINDLING_HARP_SUSPECT_AFTER_ERRORS="2") as watcher:
        assert _until(lambda: watcher.count("connection refused") >= 10, 10), watcher.output()
        assert watcher.count(REMEDY) == 0


def test_the_remedy_line_follows_its_schedule(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(
        tmp_path,
        FINDLING_HARP_REMEDY_SCHEDULE="0,2,4",
        FINDLING_HARP_REMEDY_REPEAT_SECONDS="3",
    ) as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()
        first = time.monotonic()
        time.sleep(max(0.0, first + 8.5 - time.monotonic()))
        # Offsets 0, 2 and 4 from the list, then 7 after the repeat interval;
        # the next one, at 10, lies outside the window.
        assert watcher.count(REMEDY) == 4
        assert watcher.count(RESTART) == 0
        assert watcher.starts() == 1


def test_the_remedy_schedule_starts_over_after_the_tunnel_healed(tmp_path: Path) -> None:
    cert_dir = tmp_path / "certs"
    _write_certs(cert_dir, "OLD")
    with _watch(
        tmp_path,
        "auto",
        FINDLING_HARP_REMEDY_SCHEDULE="0,30",
        FINDLING_HARP_REMEDY_REPEAT_SECONDS="30",
    ) as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()
        _replace(cert_dir / "ca.crt", "GOOD ca.crt\n")
        assert _until(lambda: watcher.count(CONNECTED) >= 1 and watcher.count(RESTART) >= 1, 10), watcher.output()
        time.sleep(0.5)
        assert watcher.count(REMEDY) == 1
        _replace(cert_dir / "ca.crt", "OLD again ca.crt\n")
        # Without the reset the next line would be due 30 s after the first x509.
        assert _until(lambda: watcher.count(REMEDY) >= 2, 8), watcher.output()
        assert watcher.count(CONNECTED) == 1


def test_a_healed_tunnel_is_reported_once(tmp_path: Path) -> None:
    cert_dir = tmp_path / "certs"
    _write_certs(cert_dir, "OLD")
    with _watch(tmp_path, "auto") as watcher:
        assert _until(lambda: watcher.count(REMEDY) >= 1, 10), watcher.output()
        _replace(cert_dir / "ca.crt", "GOOD ca.crt\n")
        assert _until(lambda: watcher.count(CONNECTED) >= 1, 10), watcher.output()
        time.sleep(3)
        assert watcher.count(CONNECTED) == 1


# Taking over new files under /certs/frp


def test_certificates_that_appear_later_switch_frpc_to_mutual_tls_once(tmp_path: Path) -> None:
    with _watch(tmp_path, "quiet") as watcher:
        _running(watcher)
        assert "certFile" not in watcher.config()
        _write_certs(watcher.cert_dir, "NEW")
        assert _until(lambda: watcher.starts() >= 2, 10), watcher.output()
        time.sleep(1.5)
        assert watcher.starts() == 2
        config = watcher.config()
        assert "transport.tls.certFile" in config
        assert "transport.tls.keyFile" in config
        assert "transport.tls.trustedCaFile" in config
        assert watcher.count(FIRST_RESTART) == 1


def test_one_swap_of_the_files_restarts_frpc_exactly_once(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "quiet") as watcher:
        _running(watcher)
        time.sleep(1.5)
        _write_certs(watcher.cert_dir, "NEW")
        time.sleep(5)
        assert watcher.starts() == 2
        assert watcher.count(FIRST_RESTART) == 1
        assert watcher.count(RESTART) == 1


def test_a_vanished_key_never_downgrades_the_tunnel(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "quiet") as watcher:
        _running(watcher)
        time.sleep(1.5)
        (watcher.cert_dir / "client.key").unlink()
        time.sleep(4)
        assert watcher.starts() == 1
        assert watcher.count(RESTART) == 0
        assert "transport.tls.certFile" in watcher.config()
        assert watcher.count(MISSING) >= 1


# The restart cap


def test_flapping_files_stop_at_the_restart_cap(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "quiet", FINDLING_HARP_RESTART_CAP="2") as watcher:
        _running(watcher)
        _flap(watcher.cert_dir, 2.5, 12)
        assert watcher.count(RESTART) == 2
        assert watcher.starts() == 3
        assert watcher.count(CAP_LINE) == 1


def test_without_a_tight_cap_the_same_flapping_restarts_more_often(tmp_path: Path) -> None:
    # Positive control for the case above: the same run with a cap that is
    # never reached restarts at least three times, so the case above stops at
    # the cap and not at a loop that never restarts at all.
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(tmp_path, "quiet", FINDLING_HARP_RESTART_CAP="1000") as watcher:
        _running(watcher)
        _flap(watcher.cert_dir, 2.5, 12)
        assert watcher.count(RESTART) >= 3
        assert watcher.count(CAP_LINE) == 0


def _cap_lines_are_separated_by_restarts(lines: list[str]) -> bool:
    restarted_since_cap = True
    for line in lines:
        if RESTART in line:
            restarted_since_cap = True
        elif CAP_LINE in line:
            if not restarted_since_cap:
                return False
            restarted_since_cap = False
    return True


def test_the_cap_window_resets_and_reports_once_per_window(tmp_path: Path) -> None:
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(
        tmp_path,
        "quiet",
        FINDLING_HARP_RESTART_CAP="1",
        FINDLING_HARP_CAP_WINDOW_SECONDS="6",
    ) as watcher:
        _running(watcher)
        _flap(watcher.cert_dir, 2.5, 16)
        lines = watcher.output()
    restarts = sum(RESTART in line for line in lines)
    caps = sum(CAP_LINE in line for line in lines)
    assert 2 <= restarts <= 3, lines
    assert 1 <= caps <= 3, lines
    assert _cap_lines_are_separated_by_restarts(lines), lines


def test_with_an_hour_long_window_the_same_run_restarts_once(tmp_path: Path) -> None:
    # Positive control for the window case: without the short window the cap of
    # one is reached once and stays reached.
    _write_certs(tmp_path / "certs", "OLD")
    with _watch(
        tmp_path,
        "quiet",
        FINDLING_HARP_RESTART_CAP="1",
        FINDLING_HARP_CAP_WINDOW_SECONDS="3600",
    ) as watcher:
        _running(watcher)
        _flap(watcher.cert_dir, 2.5, 16)
        lines = watcher.output()
    assert sum(RESTART in line for line in lines) == 1, lines
    assert sum(CAP_LINE in line for line in lines) == 1, lines


# Secrets and file modes


def test_the_shared_key_never_reaches_the_output_and_the_files_are_private(tmp_path: Path) -> None:
    with _watch(tmp_path, "auto") as watcher:
        assert _until(lambda: watcher.count("x509: ") >= 1, 10), watcher.output()
        _write_certs(watcher.cert_dir, "GOOD")
        assert _until(lambda: watcher.count(CONNECTED) >= 1, 10), watcher.output()
        assert watcher.count(FIRST_RESTART) == 1
        assert stat.S_IMODE(os.stat(watcher.run_dir / "frpc.toml").st_mode) == 0o600
        assert stat.S_IMODE(os.stat(watcher.run_dir / "frpc.fifo").st_mode) == 0o600
        assert SHARED_KEY in watcher.config()
    assert all(SHARED_KEY not in line for line in watcher.output())


# Static checks of both scripts


def test_both_scripts_parse_in_bash() -> None:
    for script in (SCRIPT, INIT):
        done = subprocess.run(  # noqa: S603 - an argument list, never a shell
            [BASH, "-n", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == 0, done.stderr


def test_both_scripts_pass_shellcheck() -> None:
    shellcheck = shutil.which("shellcheck")
    if shellcheck is None:
        pytest.skip("shellcheck is not installed here; the step in python.yml enforces it")
    done = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shellcheck, str(SCRIPT), str(INIT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
