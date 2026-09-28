"""The latency probe of D-26-12: percentiles, the report line and the credential.

The probe is loaded from its path, the way test_measurement_scripts.py loads the
status observer, because scripts/ops is not a package. Nothing here talks to a
network: the one request function is replaced by a stand-in.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROBE = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "latency_probe.py"

MARKED_PASSWORD = "Zq9-unmistakable-probe-secret"  # noqa: S105 - a test marker, not a credential
MARKED_USER = "probe-user-marker"
MARKED_TERM = "Kuendigung-marker"


def probe_module() -> ModuleType:
    specification = importlib.util.spec_from_file_location("latency_probe", PROBE)
    assert specification is not None, PROBE
    assert specification.loader is not None, PROBE
    module = importlib.util.module_from_spec(specification)
    sys.modules["latency_probe"] = module
    specification.loader.exec_module(module)
    return module


def test_percentiles_of_a_known_list() -> None:
    probe = probe_module()
    values = [float(v) for v in range(1, 101)]
    result = probe.percentiles(values)
    assert result.p50 == pytest.approx(50.5)
    assert result.p95 == pytest.approx(95.0)
    assert result.max == pytest.approx(100.0)


def test_percentiles_of_an_empty_list_are_zero() -> None:
    probe = probe_module()
    result = probe.percentiles([])
    assert (result.p50, result.p95, result.max) == (0.0, 0.0, 0.0)


def test_report_line_carries_only_figures() -> None:
    probe = probe_module()
    samples = [probe.Sample(ms=10.0, error=False), probe.Sample(ms=30.0, error=True)]
    line = probe.report_line("search", samples)
    assert line == "target search requests 2 p50_ms 20.0 p95_ms 30.0 max_ms 30.0 errors 1"
    assert "?" not in line
    assert "term" not in line.split(" requests")[1]


def test_targets_are_separate_series_and_a_timeout_counts_its_duration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    probe = probe_module()
    seen_urls: list[str] = []

    def fake_request(url: str, headers: dict[str, str], timeout: float) -> float:
        seen_urls.append(url)
        if len(seen_urls) == 2:
            raise TimeoutError
        return 0.012

    monkeypatch.setenv(probe.USER_ENV, MARKED_USER)
    monkeypatch.setenv(probe.PASSWORD_ENV, MARKED_PASSWORD)
    monkeypatch.setattr(probe, "_timed_request", fake_request)
    monkeypatch.setattr(probe.time, "sleep", lambda _seconds: None)

    assert (
        probe.main(
            [
                "--base-url",
                "http://localhost:8080",
                "--target",
                "status",
                "--requests",
                "3",
                "--timeout",
                "5",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out.strip()
    assert all(url.endswith("/status.php") for url in seen_urls)
    assert output.startswith("target status requests 3 ")
    assert output.endswith("max_ms 5000.0 errors 1")

    seen_urls.clear()
    monkeypatch.setattr(probe, "_timed_request", lambda url, headers, timeout: seen_urls.append(url) or 0.02)
    assert probe.main(["--base-url", "http://localhost:8080", "--target", "search", "--requests", "2"]) == 0
    output = capsys.readouterr().out.strip()
    assert all(probe.SEARCH_ROUTE in url for url in seen_urls)
    assert output.startswith("target search requests 2 ")


def test_credentials_never_reach_the_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    probe = probe_module()
    seen_headers: list[dict[str, str]] = []

    def fake_request(url: str, headers: dict[str, str], timeout: float) -> float:
        seen_headers.append(headers)
        raise OSError(f"failure at {url} for {MARKED_PASSWORD}")

    monkeypatch.setenv(probe.USER_ENV, MARKED_USER)
    monkeypatch.setenv(probe.PASSWORD_ENV, MARKED_PASSWORD)
    monkeypatch.setattr(probe, "_timed_request", fake_request)
    monkeypatch.setattr(probe.time, "sleep", lambda _seconds: None)

    probe.main(
        ["--base-url", "http://localhost:8080", "--target", "search", "--requests", "2", "--term", MARKED_TERM]
    )
    captured = capsys.readouterr()
    everything = captured.out + captured.err
    assert MARKED_PASSWORD not in everything
    assert MARKED_USER not in everything
    assert MARKED_TERM not in everything
    assert "Authorization" in seen_headers[0]


def test_search_without_credentials_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = probe_module()
    monkeypatch.delenv(probe.USER_ENV, raising=False)
    monkeypatch.delenv(probe.PASSWORD_ENV, raising=False)
    with pytest.raises(SystemExit):
        probe.main(["--base-url", "http://localhost:8080", "--target", "search", "--requests", "1"])
