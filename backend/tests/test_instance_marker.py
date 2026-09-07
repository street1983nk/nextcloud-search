"""The instance marker in the volume (DI-06.1-22).

The defect this file is the answer to is not ours and cannot be fixed by us. A
deployed ExApp gets its data volume from AppAPI, and AppAPI names it after the
app and after nothing else: ``nc_app_findling_backend_data``. Two Nextcloud
instances on the same docker service therefore mount the same volume, and
``occ app_api:app:unregister findling_backend --rm-data`` in one of them deletes
the index, the state database and the vector stock of the other. On 7 September
2026 that is exactly what happened to a measurement volume.

What is in our hands is the warning. The container leaves a marker with the
identity of its own instance in the root of the volume and compares it on the
next start. A marker of another instance means the volume is shared, and a
container that finds one does not start indexing: it says what is going on and
lets the status page carry the reason, which is the same shape the model verdict
of plan 06.1-17 has.

Four claims carry the feature, and the fifth is the one that keeps it from
becoming a nuisance:

1. A fresh volume gets a marker.
2. Our own marker changes nothing at all.
3. A foreign marker stops the indexing and is named in the log.
4. An empty or broken marker counts as absent and is written again, because a
   marker that was interrupted halfway through must not turn into a permanent
   alarm.
5. Without an identity the whole mechanism is skipped in silence. AppAPI sets
   ``NEXTCLOUD_URL`` for every deployed container, so this is the case of a bare
   local run, and refusing to index because of it would be a regression for a
   deployment that has nothing wrong with it.

The identity is stored as a digest and never as the URL it came from. The
volume is readable by the container of the other instance, so a marker carrying
the address of instance A would hand it to instance B, and this project logs
type names rather than contents everywhere else for exactly that reason.
"""

import asyncio
import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from findling import instance
from findling.api import status
from findling.config import INSTANCE_MARKER_NAME, settings
from findling.main import APP

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# One instance and another one. Two ports on the same host is the constellation
# the incident happened in, and it is the one an admin sets up for a test run.
OWN_URL = "http://localhost:8080"
OTHER_URL = "http://localhost:8097"


class _FakePoller:
    """A poller that records the arming and opens nothing.

    The real one opens the index and the state database as soon as it is armed,
    and every claim here is about the arming and not about a pass.
    """

    def __init__(self) -> None:
        self.armed = False
        self.closed = False

    def arm(self) -> None:
        self.armed = True

    def silence(self) -> None:
        self.armed = False

    async def run(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await asyncio.sleep(0.001)

    async def unlock_held(self) -> int:
        return 0

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture
def own_instance(volume: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """An empty volume plus the identity AppAPI hands a deployed container."""
    monkeypatch.setenv("NEXTCLOUD_URL", OWN_URL)
    yield volume


@pytest.fixture
def armed_poller(volume: Path, monkeypatch: pytest.MonkeyPatch) -> _FakePoller:
    """A volume that was enabled before this start, so the arming is expected.

    Depends on ``volume`` rather than trusting the order of the test signature:
    without it the arming mark would land in the shared fallback directory of
    the system temp space and hand the next process an armed container.
    """
    del volume
    poller = _FakePoller()
    monkeypatch.setattr("findling.main.default_poller", lambda: poller)
    settings().armed_marker.write_text("", encoding="utf-8")
    return poller


def _plant(marker: Path, url: str) -> None:
    """Write the marker another instance would have left behind."""
    marker.write_text(json.dumps({"instance": instance.fingerprint_of(url)}), encoding="utf-8")


def _stored(marker: Path) -> str:
    return str(json.loads(marker.read_text(encoding="utf-8"))["instance"])


# -- claim 1: a fresh volume gets a marker -----------------------------------


def test_a_fresh_volume_gets_the_marker_of_this_instance(own_instance: Path) -> None:
    claim = instance.claim_the_volume()

    assert claim.other == ""
    assert settings().instance_marker.is_file()
    assert _stored(settings().instance_marker) == instance.fingerprint_of(OWN_URL)


def test_the_marker_carries_a_digest_and_never_the_address(own_instance: Path) -> None:
    # The volume is mounted by the container of the other instance too, so a
    # marker with the address of this one would hand that address over.
    instance.claim_the_volume()
    written = settings().instance_marker.read_text(encoding="utf-8")

    assert OWN_URL not in written
    assert "localhost" not in written


def test_the_marker_lands_beside_the_databases_and_not_inside_them(own_instance: Path) -> None:
    instance.claim_the_volume()

    assert settings().instance_marker.parent == own_instance
    assert settings().instance_marker == own_instance / INSTANCE_MARKER_NAME


# -- claim 2: our own marker changes nothing ---------------------------------


def test_our_own_marker_is_not_a_finding(own_instance: Path) -> None:
    # The ordinary case: a restart, an update, a re-register of the same
    # instance. Every one of those finds the marker it wrote itself, and none of
    # them may produce a single alarm.
    instance.claim_the_volume()

    claim = instance.claim_the_volume()

    assert claim.other == ""
    assert instance.volume_is_shared() is False


def test_our_own_marker_is_left_untouched(own_instance: Path) -> None:
    instance.claim_the_volume()
    before = settings().instance_marker.stat().st_mtime_ns

    instance.claim_the_volume()

    assert settings().instance_marker.stat().st_mtime_ns == before


def test_the_lifespan_still_arms_a_container_that_finds_its_own_marker(
    own_instance: Path, armed_poller: _FakePoller
) -> None:
    _plant(settings().instance_marker, OWN_URL)

    with TestClient(APP):
        assert armed_poller.armed is True


# -- claim 3: a foreign marker stops the indexing ----------------------------


def test_a_foreign_marker_is_reported_with_both_identities(own_instance: Path) -> None:
    _plant(settings().instance_marker, OTHER_URL)

    claim = instance.claim_the_volume()

    assert claim.other != ""
    assert claim.own != ""
    assert claim.other != claim.own
    assert instance.volume_is_shared() is True


def test_a_foreign_marker_is_not_overwritten(own_instance: Path) -> None:
    # Taking the volume over would delete the only evidence of the sharing and
    # would make the next start of the other container report the same finding
    # about us, forever alternating.
    _plant(settings().instance_marker, OTHER_URL)

    instance.claim_the_volume()

    assert _stored(settings().instance_marker) == instance.fingerprint_of(OTHER_URL)


def test_a_foreign_marker_keeps_the_indexing_off(own_instance: Path, armed_poller: _FakePoller) -> None:
    # The whole point. The arming mark of DI-05-36 says this container was
    # enabled, and it is still not allowed to index: the rows it would claim and
    # the index it would write belong to another instance.
    _plant(settings().instance_marker, OTHER_URL)

    with TestClient(APP):
        assert armed_poller.armed is False


def test_a_foreign_marker_leaves_the_server_up(own_instance: Path, armed_poller: _FakePoller) -> None:
    # Degraded and not dead, the shape the model verdict has: the status page is
    # the place an admin reads the reason, and a container that refused to start
    # could not show it.
    _plant(settings().instance_marker, OTHER_URL)

    with TestClient(APP) as client:
        assert client.get("/heartbeat").status_code == 200


def test_the_log_line_names_the_sharing_and_the_page_that_explains_it(
    own_instance: Path, armed_poller: _FakePoller, caplog: pytest.LogCaptureFixture
) -> None:
    _plant(settings().instance_marker, OTHER_URL)

    with caplog.at_level(logging.WARNING, logger="findling"), TestClient(APP):
        pass

    said = "\n".join(record.getMessage() for record in caplog.records)
    assert "volume" in said
    assert "docs/uninstall.md" in said


def test_the_log_line_leaks_neither_address_nor_the_path_of_the_volume(
    own_instance: Path, armed_poller: _FakePoller, caplog: pytest.LogCaptureFixture
) -> None:
    # The rule of this container's log: a type name, a counter or a shortened
    # digest. Never a path, never an address, not even one of our own.
    _plant(settings().instance_marker, OTHER_URL)

    with caplog.at_level(logging.WARNING, logger="findling"), TestClient(APP):
        pass

    said = "\n".join(record.getMessage() for record in caplog.records)
    assert OTHER_URL not in said
    assert OWN_URL not in said
    assert str(own_instance) not in said


def test_the_status_page_names_the_shared_volume(own_instance: Path) -> None:
    _plant(settings().instance_marker, OTHER_URL)

    answer = status.report()

    assert answer.note == status.VOLUME_SHARED


def test_the_status_page_says_nothing_about_sharing_on_our_own_volume(own_instance: Path) -> None:
    _plant(settings().instance_marker, OWN_URL)

    answer = status.report()

    assert answer.note != status.VOLUME_SHARED


# -- claim 4: a broken marker heals ------------------------------------------


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("", id="empty"),
        pytest.param("   ", id="whitespace"),
        pytest.param("{", id="truncated json"),
        pytest.param("{}", id="no identity"),
        pytest.param('{"instance": ""}', id="empty identity"),
        pytest.param('{"instance": null}', id="null identity"),
        pytest.param('["not", "an", "object"]', id="wrong shape"),
    ],
)
def test_a_broken_marker_counts_as_absent_and_is_written_again(own_instance: Path, content: str) -> None:
    # A kill between create and write leaves a zero byte file. Reading that as
    # "another instance" would turn one interrupted start into a container that
    # never indexes again, and nobody would be able to tell it apart from the
    # real finding.
    settings().instance_marker.write_text(content, encoding="utf-8")

    claim = instance.claim_the_volume()

    assert claim.other == ""
    assert _stored(settings().instance_marker) == instance.fingerprint_of(OWN_URL)


def test_a_broken_marker_does_not_stop_the_indexing(own_instance: Path, armed_poller: _FakePoller) -> None:
    settings().instance_marker.write_text("", encoding="utf-8")

    with TestClient(APP):
        assert armed_poller.armed is True


# -- claim 5: no identity, no mechanism --------------------------------------


def test_without_an_identity_no_marker_is_written(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A bare local run. AppAPI sets NEXTCLOUD_URL for every deployed container,
    # so this is not a deployment this check has anything to say about.
    monkeypatch.delenv("NEXTCLOUD_URL", raising=False)

    claim = instance.claim_the_volume()

    assert claim == instance.Claim()
    assert not settings().instance_marker.exists()


def test_without_an_identity_a_foreign_marker_is_not_a_finding(
    volume: Path, monkeypatch: pytest.MonkeyPatch, armed_poller: _FakePoller, caplog: pytest.LogCaptureFixture
) -> None:
    # Silently skipped, and that word is the decision: a container that cannot
    # name itself cannot tell "somebody else's volume" from "my own volume", and
    # guessing would either block a healthy deployment or cry wolf.
    monkeypatch.delenv("NEXTCLOUD_URL", raising=False)
    _plant(settings().instance_marker, OTHER_URL)

    with caplog.at_level(logging.WARNING, logger="findling"), TestClient(APP):
        assert armed_poller.armed is True

    assert instance.volume_is_shared() is False
    assert not any("volume" in record.getMessage() for record in caplog.records)


# -- the failures of the volume itself ---------------------------------------


def test_a_volume_that_cannot_be_written_costs_neither_the_start_nor_the_arming(
    own_instance: Path, armed_poller: _FakePoller, caplog: pytest.LogCaptureFixture
) -> None:
    # A directory where the file belongs, because that fails with an OSError on
    # every platform this suite runs on. What it stands for is a volume that is
    # full, read only or gone. The marker is a warning mechanism, and a warning
    # mechanism that can stop a container is worse than no warning at all.
    settings().instance_marker.mkdir()

    with caplog.at_level(logging.WARNING, logger="findling"), TestClient(APP):
        assert armed_poller.armed is True

    assert not any(str(own_instance) in record.getMessage() for record in caplog.records)


def test_a_root_that_does_not_exist_yet_is_not_a_finding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The first start of a fresh deployment. AppAPI creates the volume before it
    # starts the container, so this is the case that only happens outside one,
    # and a verdict about a volume that is not there would be invented.
    monkeypatch.setenv("NEXTCLOUD_URL", OWN_URL)
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(tmp_path / "not-created-yet"))
    settings.cache_clear()
    try:
        claim = instance.claim_the_volume()

        assert claim.other == ""
        assert instance.volume_is_shared() is False
    finally:
        settings.cache_clear()


# -- the identity, and where it comes from -----------------------------------


def test_the_identity_is_normalised_the_way_the_client_library_normalises_it() -> None:
    # AppAPI hands the same instance through with and without a trailing slash
    # and with and without index.php in it, and the client library strips all
    # three. A digest over the raw value would make one instance look like two
    # and would produce a finding on a restart.
    plain = instance.fingerprint_of("http://localhost:8080")

    assert instance.fingerprint_of("http://localhost:8080/") == plain
    assert instance.fingerprint_of("http://localhost:8080/index.php") == plain
    assert instance.fingerprint_of("http://localhost:8080/index.php/") == plain


def test_two_instances_on_the_same_host_are_two_identities() -> None:
    assert instance.fingerprint_of(OWN_URL) != instance.fingerprint_of(OTHER_URL)


def test_no_file_name_is_spelled_out_beside_the_settings() -> None:
    # The same rule the arming mark follows: the layout of the volume is decided
    # in config.py and nowhere else, otherwise the two places drift the first
    # time the volume is rearranged.
    for module in ("main.py", "instance.py"):
        source = (PACKAGE_ROOT / module).read_text(encoding="utf-8")

        assert f'"{INSTANCE_MARKER_NAME}"' not in source, module
        assert f"'{INSTANCE_MARKER_NAME}'" not in source, module


# -- the mutation probe ------------------------------------------------------


def test_the_foreign_verdict_goes_red_when_the_comparison_stops_comparing(
    own_instance: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Red capability of the third claim, shown rather than asserted. With a
    # digest that ignores its input every instance looks like the same instance,
    # the foreign marker turns into our own and the finding disappears. So the
    # claim above fails when the comparison is broken, which is what makes it a
    # test and not a decoration.
    _plant(settings().instance_marker, OTHER_URL)
    monkeypatch.setattr(instance, "fingerprint_of", lambda url: "the same for everybody")

    claim = instance.claim_the_volume()

    assert claim.other == ""
