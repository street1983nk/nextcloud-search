"""The house rules of the operating scripts, as a gate instead of a review note.

scripts/ops holds the three shell scripts of the ARM load test: the memory
sampler, the tool that rents and returns a Hetzner box, and its AWS counterpart,
which exists because the arm machine of decision D-01 could not be rented for
months and the run moved to an m7g.large with the memory capped to 4 GB by the
kernel. None of them is reached by a Python test in the usual sense, and all of
them carry promises that are easy to break years later with a well meant edit.
Three of those promises are mechanical, so they are checked here rather than
remembered:

* No em dash and no en dash, which is a project wide typography rule, and no
  carriage return, because these files are read by /bin/sh on Ubuntu and a CR
  behind the shebang fails with an error that names an invisible character.
* The sampler reads the cgroup files itself and never asks the docker client for
  a memory figure. That client reports memory.current, which counts the page
  cache of the mmap index and would overstate the store claim by gigabytes.
* Neither box tool ever puts a credential into an output, and both label every
  resource they create, because a label is the only way to find a forgotten
  resource in an account that holds other things (T-05-17, T-05-19).

Since plan 06.1-11 the directory also holds a Python tool, search_load.py, and
the same three promises are asked of it plus a fourth that belongs to it alone:
no path of one particular machine in its source. That fourth one is why it
exists in scripts/ops at all rather than beside the measurement it grew out of.
The reference it was built from, 45-suchlast.py of the semantic run, put a
directory of the load test box into sys.path and imported a helper that lives
only there, which makes a tool that measures one machine and cannot be pointed
at another.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType

import pytest

OPS_DIR = Path(__file__).resolve().parents[2] / "scripts" / "ops"
RSS_SAMPLER = OPS_DIR / "rss_sampler.sh"
HETZNER_BOX = OPS_DIR / "hetzner_box.sh"
AWS_BOX = OPS_DIR / "aws_box.sh"
SEARCH_LOAD = OPS_DIR / "search_load.py"

# Assembled from code points so that this file does not carry the characters it
# forbids and fail on itself.
DASHES = (chr(0x2014), chr(0x2013))

# The two words the sampler may not contain, for the reason in the module
# docstring. Assembled for the same reason as the dashes.
DOCKER_MEMORY_SHORTCUT = "docker" + " " + "stats"

# The route a user takes. A load sample that called the container directly would
# leave out the two halves that decide what a search costs on a small box: the
# PHP process pool of the instance and the permission recheck of every candidate.
OCS_SEARCH_ROUTE = "/ocs/v2.php/search/providers/findling/search"

# The two headers a call into the container would carry, and their absence is
# what keeps the measurement on the route above.
CONTAINER_ONLY_HEADERS = ("EX-APP-ID", "AUTHORIZATION-APP-API")

# The shapes that tie a tool to one machine. A directory under a home and an
# entry pushed into sys.path are what the reference sample needed to reach its
# helper module on the load test box, and they are exactly what makes a tool
# unusable anywhere else.
MACHINE_SHAPES = ("/home/", "sys.path.insert", "sys.path.append", "drillhelfer")

# The name the load tool is imported under. A name and not a path, because a
# module whose name is not an identifier cannot be looked up in sys.modules,
# which the dataclass in the tool needs; see search_load_module below.
SEARCH_LOAD_MODULE = "findling_search_load"


def machine_shapes(text: str) -> list[str]:
    """Every machine shape the text carries, sorted, empty when it carries none."""
    return sorted(shape for shape in MACHINE_SHAPES if shape in text)


def imported_packages(text: str) -> set[str]:
    """The top level package of every import in the file.

    Read out of the syntax tree rather than out of the lines, because an import
    inside a function is still an import and a text search for "import " finds
    the word in every second docstring of this repository.
    """
    packages: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
    return packages


@pytest.fixture(params=[RSS_SAMPLER, HETZNER_BOX, AWS_BOX], ids=lambda path: path.name)
def script(request: pytest.FixtureRequest) -> Path:
    return Path(request.param)


def test_the_script_exists_and_starts_with_a_posix_shebang(script: Path) -> None:
    text = script.read_bytes()
    assert text.startswith(b"#!/bin/sh\n"), script.name


def test_the_script_carries_neither_a_dash_nor_a_carriage_return(script: Path) -> None:
    raw = script.read_bytes()
    assert b"\r" not in raw, script.name
    text = raw.decode("utf-8")
    for dash in DASHES:
        assert dash not in text, f"{dash!r} in {script.name}"


def test_the_script_stops_on_an_error_and_on_an_unset_variable(script: Path) -> None:
    """set -eu, because a sampler that runs on after a failed read writes fiction."""
    assert "\nset -eu\n" in script.read_text(encoding="utf-8"), script.name


def test_the_sampler_knows_both_cgroup_driver_layouts() -> None:
    """systemd on Ubuntu 24.04, cgroupfs elsewhere. Guessing one is a coin toss."""
    text = RSS_SAMPLER.read_text(encoding="utf-8")
    assert "system.slice/docker-" in text
    assert "/docker/$CONTAINER_ID" in text


def test_the_sampler_reads_the_cgroup_instead_of_asking_the_client() -> None:
    text = RSS_SAMPLER.read_text(encoding="utf-8")
    assert DOCKER_MEMORY_SHORTCUT not in text
    assert "memory.stat" in text
    assert "anon" in text


def test_the_sampler_refuses_rather_than_writing_zeroes() -> None:
    """The failure branch is the point of the script, so it is named explicitly."""
    text = RSS_SAMPLER.read_text(encoding="utf-8")
    assert "no readable memory.stat" in text
    assert "not one sample was written" in text


def test_the_box_tool_names_its_four_subcommands_in_the_usage() -> None:
    text = HETZNER_BOX.read_text(encoding="utf-8")
    for subcommand in ("prices", "create", "status", "destroy"):
        assert f"    {subcommand})" in text, subcommand
    assert "usage: hetzner_box.sh <prices|create|status|destroy>" in text


def test_the_box_tool_demands_the_token_and_never_prints_it() -> None:
    """The value goes into a curl config on standard input and nowhere else.

    Two places may mention the variable at all: the check that it is set, and the
    one line that hands it to curl. A third would be the beginning of a token in
    a log file (T-05-17).
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert ': "${HCLOUD_TOKEN:?token fehlt}"' in text
    expanding = [line for line in text.splitlines() if "$HCLOUD_TOKEN" in line or "${HCLOUD_TOKEN" in line]
    assert len(expanding) == 2, expanding
    assert not [line for line in text.splitlines() if "echo" in line and "HCLOUD_TOKEN" in line]


def test_the_box_tool_labels_every_resource_it_creates() -> None:
    """Three create bodies, three label fields, one label (T-05-19).

    The count is the point and not a formality: it was two while the run created
    a box and a volume, and it went to three the moment a firewall came along.
    An unlabelled resource is one that a sweep by label does not find.
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert text.count('"labels":{"%s":"%s"}') == 3
    assert "LABEL='purpose=findling-phase5'" in text


def test_the_box_tool_injects_the_ssh_key_by_name() -> None:
    """Hetzner injects only the keys named in the create request itself.

    A box that came up without a key takes a password over the web console and
    nothing else, and it cannot be given a key afterwards without a reinstall.
    The AIO interface of the load test is reached through an ssh tunnel, so the
    field is load bearing and the name is checked against the account before the
    first paid request goes out.
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert "SSH_KEY_NAME='khaled-windows-ed25519'" in text
    assert '"ssh_keys":["%s"]' in text
    assert "/ssh_keys?name=$SSH_KEY_NAME" in text
    assert "has no ssh key named" in text


def test_the_box_tool_reads_the_stock_before_it_tries_to_rent() -> None:
    """The API blames the location when the truth is that the type is sold out.

    A create against a sold out arm type answers "unsupported location for
    server type", which reads like a wrong argument and sends the next reader
    to the location field. The availability flag sits on the server type, one
    per location, so it is read first and the state is said in words.
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert "/server_types?name=$SERVER_TYPE" in text
    assert "is out of stock in every location right now" in text
    assert "this is capacity, not a wrong argument" in text


def test_the_box_is_created_where_the_phase_decided() -> None:
    """Decision D-01 names Helsinki, and a server cannot move afterwards."""
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert "SERVER_LOCATION='hel1'" in text


def test_the_cost_line_does_not_read_the_answers_line_by_line() -> None:
    """The real API pretty prints, a stub does not, and one of them was believed.

    status handed three answers to one reader as three lines. Hetzner wraps its
    JSON over several lines, so the reader got an opening brace and died, and
    the command that produces the cost figure of the report had never once run
    against the real thing. The answers are passed as one array instead, which
    does not care about whitespace at all.
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert "printf '[%s,%s,%s]'" in text
    assert "sys.stdin.readline()" not in text


def test_the_firewall_is_created_and_taken_down_again() -> None:
    """A rule set on the box would not hold, and a free resource is the one that stays.

    Docker writes its published ports straight into iptables and walks past ufw,
    so the AIO interface on 8080 would be open to the world while ufw reports it
    closed. The filter therefore sits outside the machine (T-05-40). And because
    a firewall costs nothing, it is exactly the resource nobody misses, so the
    deletion covers it by id and, when no state file is left, by label (T-05-39).
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert '"direction":"in","protocol":"tcp","port":"22"' in text
    assert '"direction":"in","protocol":"tcp","port":"443"' in text
    # Three ports and no fourth. The interface of AIO is reached through the ssh
    # tunnel, and a rule for it would be the quiet end of that promise.
    assert text.count('"direction":"in","protocol":"tcp"') == 3
    assert "/firewalls?label_selector=$LABEL" in text
    assert "firewall ${firewall_id:-none} is gone, verified against the API" in text


def test_the_deletion_does_not_call_an_empty_answer_a_failure() -> None:
    """DELETE on a volume answers 204 with no body, and that is a success.

    The generic reader of this script calls an empty answer a request that never
    arrived, which is right everywhere except here: reported in the deletion it
    would print a sentence that reads like a lost volume on every clean run, and
    an operator learns fast to stop reading the output of the one step that has
    to be trusted (T-05-39).
    """
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert 'delete_error "$response"' in text
    assert "the volume was not deleted yet: $(delete_error" in text
    assert "the server was not deleted: $(delete_error" in text


def test_the_aws_tool_names_its_eight_subcommands_in_the_usage() -> None:
    """Eight and not five: the box lives between stop and start, and it outlives itself.

    The box of the ARM run was created by hand, so create is a record of what
    happened and refuses to make a second machine, while the volume that the
    corpus lives on is created by the tool and has to be findable in it. stop
    and start came late, in 06.1-18, because until then the box was parked and
    woken by hand, which meant past the cost arithmetic of this script. snapshot
    came last, in 11-12, because the corpus of the run has to survive the
    machine that carried it, and a snapshot taken by hand is a snapshot whose
    verification nobody keeps.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    for subcommand in ("prices", "create", "volume", "status", "stop", "start", "snapshot", "destroy"):
        assert f"    {subcommand})" in text, subcommand
    assert "usage: aws_box.sh <prices|create|volume|status|stop|start|snapshot|destroy>" in text


def test_the_aws_snapshot_refuses_a_box_that_is_not_stopped() -> None:
    """A snapshot of an attached, written volume is crash consistent and nothing more.

    At a stopped instance the filesystem is quiet and the snapshot is clean, so
    the state is a precondition of the subcommand rather than a sentence in a
    plan. This is the one check that cannot be made up for afterwards: a broken
    snapshot looks exactly like a good one until it is restored (T-11-54).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_snapshot() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert "!= 'stopped'" in body
    # The refusal happens before anything is created, so the check stands in
    # front of the call that makes the snapshot.
    assert body.index("'stopped'") < body.index("create-snapshot")


def test_the_aws_snapshot_waits_with_the_waiter_and_reads_the_state_back_itself() -> None:
    """The waiter is the wait, the read back is the proof, and they are not the same.

    A waiter that returns says the api stopped answering pending; it does not
    say what the snapshot now is. The verification is therefore an independent
    describe with the fields the report quotes, and the order matters, because a
    read before the waiter would report a snapshot in progress as a result.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_snapshot() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert "ec2 wait snapshot-completed" in body
    assert body.index("wait snapshot-completed") < body.index("describe-snapshots")
    for field in ("State", "Progress", "VolumeSize", "VolumeId", "StartTime", "OwnerId", "Encrypted"):
        assert field in body, field
    # The figure the report is written from lands in the state file, next to the
    # id, because the state file is what the next reader quotes.
    assert "CORPUS_SNAPSHOT_ID=" in body


def test_the_aws_snapshot_can_read_back_one_that_outlasted_the_waiter() -> None:
    """The waiter gives up after ten minutes, and the snapshot of this box took hours.

    It stood at 8 percent when the waiter gave up on 2026-09-11. A subcommand
    that can only create would leave one way out of that state, and it would be
    a second snapshot and a second invoice. So the id can be handed in, and
    then the subcommand does only the part that was left over: the read back,
    the check that the snapshot belongs to this volume, and the state file.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_snapshot() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert 'snapshot_id="${1:-}"' in body
    # Handed in means created nothing, so the creation sits inside the branch
    # that only runs when no id was given.
    assert body.index('snapshot_id="${1:-}"') < body.index("create-snapshot")
    assert "was handed in, so nothing is created here" in body
    assert '"$snapshot_volume" != "$VOLUME_ID"' in body
    assert 'snapshot) cmd_snapshot "$@" ;;' in text


def test_the_aws_snapshot_carries_a_tag_the_sweep_of_destroy_does_not_trip_over() -> None:
    """The snapshot is the one resource of this run that is meant to outlive the box.

    The sweep of cmd_destroy lists every resource carrying purpose=findling-phase5
    and calls it a leftover. A snapshot with that tag would make a correct
    teardown end red and leave the state file lying around, so the snapshot
    carries its own tag and destroy knows the survivor by name (T-11-52).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "KEEP_TAG_VALUE='findling-corpus-keep'" in text
    snapshot = text.split("cmd_snapshot() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert "{Key=$TAG_KEY,Value=$KEEP_TAG_VALUE}]" in snapshot
    assert "Value=$TAG_VALUE}" not in snapshot
    destroy = text.split("cmd_destroy() {", 1)[1]
    # destroy asks for the survivor on purpose instead of relying on the filter
    # not seeing it, because a resource that carried both tags would otherwise
    # be reported as a leftover.
    assert '"Name=tag:$TAG_KEY,Values=$KEEP_TAG_VALUE"' in destroy
    assert "findling-corpus-keep" in text.split("cmd_snapshot() {", 1)[0]


def test_the_aws_destroy_reads_every_tag_hit_back_before_it_calls_it_a_leftover() -> None:
    """describe-tags lags, and a lagging index made a correct teardown end red.

    On 2026-09-11 the sweep reported both volumes of the box as leftovers while
    the api answered InvalidVolume.NotFound for each of them: the tags of a
    resource deleted moments ago keep coming back, exactly as the tags of the
    terminated instance do. A check that cries wolf is a check nobody reads, so
    every hit is read back by its own type. What cannot be read stays a
    leftover, because that is the direction an error has to fall in here.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_destroy() {", 1)[1]
    assert "for hit in $remaining; do" in body
    assert "the resource itself is gone" in body
    # Read back by type, and an unknown type is not read back into innocence.
    for kind in ("instance)", "volume)", "security-group)"):
        assert kind in body, kind
    assert "*) hit_state='there' ;;" in body
    # The strict end is still there: something that answers is still a leftover.
    assert body.index("for hit in $remaining; do") < body.index("something still carries the tag")


def test_the_aws_destroy_refuses_to_remove_the_state_file_without_a_backup() -> None:
    """box.env is the whole cost and damage history of this box, and destroy deletes it.

    Instance and volume, every stop and start with its run time and its cost,
    the damage report of 2026-09-07 and the DI-05-36 finding live in that file
    and nowhere else. destroy therefore demands the path of a backup, checks
    that it exists and is not empty, and refuses before it terminates anything
    rather than after it has removed the file (T-11-53).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_destroy() {", 1)[1]
    assert "FINDLING_STATE_BACKUP" in body
    # Exists and is not empty, and both before the first destructive call.
    assert '[ ! -f "$backup" ]' in body
    assert '[ ! -s "$backup" ]' in body
    assert body.index("FINDLING_STATE_BACKUP") < body.index("terminate-instances")
    assert body.index('[ ! -s "$backup" ]') < body.index('rm -f "$STATE_FILE"')


def test_the_aws_stop_writes_the_uptime_it_closes_into_the_state_file() -> None:
    """A parked box cannot be asked afterwards what it cost while it ran.

    The figure has to be taken from the api before the call that stops it, and
    it has to land in the state file, because the state file is what the next
    report quotes. Both are asserted here, and the order is the point: reading
    the LaunchTime after the stop yields a number that looks right and is not.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "BOX_LAST_UPTIME_HOURS=$uptime_hours" in text
    assert "BOX_LAST_UPTIME_COST_USD=$uptime_cost" in text
    assert "BOX_PARKED_COST_USD_PER_DAY=$parked_per_day" in text
    assert "ec2 wait instance-stopped" in text
    body = text.split("cmd_stop() {", 1)[1].split("\ncmd_start() {", 1)[0]
    assert body.index("describe-instances") < body.index("stop-instances")


def test_the_aws_status_calls_the_time_since_the_launch_an_uptime_only_while_running() -> None:
    """The trap cmd_stop is built around, one subcommand further along.

    A stopped instance keeps answering with the LaunchTime of its last start, so
    the distance from it to now counts every parked hour as an hour of uptime.
    On 2026-09-09 status reported 52.3 hours and 5.80 USD for a box that had run
    1.95 hours and been parked since 2026-09-07T06:56:42Z. That is the figure a
    cost ceiling gets checked against, so the arithmetic is gated on the state
    and the parked case says what it is instead of adding days up.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_status() {", 1)[1].split("\ncmd_stop() {", 1)[0]
    assert "running = state == 'running'" in body
    assert "if running:" in body
    # The two sentences that keep a reader from quoting the wrong number.
    assert "are NOT an uptime" in body
    assert "a stopped instance keeps its launchtime" in body.lower()
    # The parked branch charges the disks and nothing else, and it refuses to
    # pretend it knows how many days they have been parked for.
    assert "per day while parked" in body
    assert "does not add the parked days up" in body


def test_the_aws_start_moves_the_ssh_rule_and_revokes_before_it_authorizes() -> None:
    """An ssh rule on a lease that moved on is an open port for its new holder.

    The address of the owner comes from a carrier lease and it changed between
    every single run of this phase. start reads the current one and moves the
    rule, and it revokes the stale rule before it authorizes the new one: the
    other order leaves both open for the duration of one api call (T-06.1-78).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "api.ipify.org" in text
    body = text.split("cmd_start() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert "ec2 wait instance-running" in body
    assert body.index("revoke-security-group-ingress") < body.index("authorize-security-group-ingress")
    # The address is validated as an address rather than pasted into a filter.
    assert "ipaddress.IPv4Address(candidate)" in body


def test_the_aws_start_names_the_three_things_a_start_does_not_do_by_itself() -> None:
    """The assurance that goes red when start stops saying what is left.

    Three handles were forgotten at every wake up of this box: the address in
    the state file, the ssh rule of the security group, and the A record of the
    load test. start does the first two and has to name all three, otherwise the
    next person reads them out of a note in a planning file again.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_start() {", 1)[1].split("\n# Gone has three shapes", 1)[0]
    assert "BOX_IP: done" in body
    assert "the ssh rule of the security group for port 22: done" in body
    assert "the A record loadtest.infranode.dev: OPEN" in body
    # The two that belong to the container, and that cost a run each when they
    # were missed: DI-05-36 and the limit that a register throws away.
    assert "DI-05-36" in body
    assert "docker update --memory=2g --memory-swap=2g" in body


def test_the_aws_tool_demands_both_credentials_and_never_prints_them() -> None:
    """Two names, one mention each, and no line that echoes either of them.

    The CLI reads the values out of the environment by itself, so unlike the
    Hetzner tool this one never has to hand a secret to a program at all. That
    makes exactly one mention per name the right count: the check that it is set
    (T-05-17).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        assert f': "${{{name}:?' in text, name
        expanding = [line for line in text.splitlines() if f"${name}" in line or f"${{{name}" in line]
        assert len(expanding) == 1, expanding
        assert not [line for line in text.splitlines() if "echo" in line and name in line]


def test_the_aws_tool_tags_the_volume_it_creates() -> None:
    """One tag, on every resource this tool makes, or a sweep will not find it."""
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "TAG_KEY='purpose'" in text
    assert "TAG_VALUE='findling-phase5'" in text
    assert "ResourceType=volume,Tags=[{Key=$VOLUME_NAME" not in text
    assert "{Key=$TAG_KEY,Value=$TAG_VALUE}]" in text


def test_the_aws_tool_counts_the_public_address() -> None:
    """The item that understated the Hetzner half of this report by eight percent.

    A public IPv4 has been its own line on an AWS invoice since 2024-02-01. The
    rate is pinned with its source, and status only adds it when the box really
    carries an address.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "PRICE_IPV4_HOURLY='0.0050'" in text
    assert "if instance.get('PublicIpAddress') else 0.0" in text


def test_the_aws_tool_refuses_to_create_a_second_box() -> None:
    """create documents and does not act, because the box exists and costs money."""
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "this command will not make one" in text
    # The recipe quotes run-instances as text for a human to read. What must not
    # exist is a call through the wrapper of this script, which would really
    # start a machine.
    assert "ec2 run-instances" not in text.replace("  aws ec2 run-instances", "")


def test_the_aws_tool_names_the_memory_cap_that_makes_the_parity() -> None:
    """An m7g.large has 8 GB, and the whole claim rests on it behaving like 4.

    The cap is a kernel parameter, it is the difference between this measurement
    and a meaningless one, and it is read back before every run. So the tool
    that rents the box carries both the drop-in and the three numbers.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "mem=4G" in text
    assert "99-mem4g.cfg" in text
    assert "capped to 4096 MiB by the kernel" in text


def test_the_aws_tool_switches_off_the_windows_path_rewriting() -> None:
    """Git for Windows turned /dev/sdf into C:/Program Files/Git/dev/sdf.

    The attach was refused with a message that names the value and not the
    cause, and the volume was already created at that point. This one line is
    the fix, and it is easy to remove as noise years later.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "MSYS2_ARG_CONV_EXCL='*'" in text
    assert "export MSYS2_ARG_CONV_EXCL" in text


def test_the_aws_destroy_checks_all_three_resources_and_sweeps_by_tag() -> None:
    """Instance, volume and security group, each verified, plus the tag sweep.

    Gone has a different shape here than at Hetzner: a terminated instance keeps
    answering the api for up to an hour, so state=terminated is the proof and
    not_found is not available. That difference is the reason this is a test and
    not a reading of the Hetzner cases.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "instance $instance_id is gone, verified against the api" in text
    assert "volume ${volume_id:-none} is gone, verified against the api" in text
    assert "security group ${group_id:-none} is gone, verified against the api" in text
    assert "if [ \"$state\" = 'terminated' ]; then" in text
    assert '--filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE"' in text
    assert "something is left over" in text
    # Since 11-12 the sweep has two expected survivors instead of one: the
    # terminated instance, whose tags fall off within the hour, and the snapshot
    # of the corpus, which is the point of the whole exercise.
    body = text.split("cmd_destroy() {", 1)[1]
    assert "keepers" in body
    assert body.index("keepers") < body.index("something still carries the tag")


def test_the_aws_tool_keeps_the_state_out_of_the_repo() -> None:
    text = AWS_BOX.read_text(encoding="utf-8")
    assert 'STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"' in text
    assert "umask 077" in text


def test_the_aws_tool_waits_with_the_waiters_and_not_with_a_loop() -> None:
    """The rate limit rule of 2026-09-04, as a gate on the one script that polls.

    A diagnostic run that asked a foreign api sixty times a minute against a
    limit of one got a production address blocked. The waiters of the CLI poll on
    a fixed interval and give up after a bounded number of tries, so this script
    has no hand rolled wait loop at all.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    assert "ec2 wait volume-available" in text
    assert "ec2 wait volume-in-use" in text
    assert "ec2 wait instance-terminated" in text
    assert "ec2 wait snapshot-completed" in text
    # Only statements, because the prose above them may well contain the word.
    loops = [
        line for line in text.splitlines() if line.strip().startswith("while ") or line.strip().startswith("until ")
    ]
    assert not loops, loops


def test_the_box_tool_verifies_the_deletion_and_keeps_the_state_out_of_the_repo() -> None:
    text = HETZNER_BOX.read_text(encoding="utf-8")
    assert "is gone, verified against the API" in text
    assert "something is left over" in text
    # The state file is under HOME, and the only other path in it is the override
    # a test uses. Neither is inside the working tree.
    assert 'STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"' in text
    assert "umask 077" in text


# The load tool of plan 06.1-11. Its own block rather than an entry in the
# fixture above, because that fixture asks every script for a POSIX shebang and
# for "set -eu", and neither sentence means anything in Python.


def test_the_load_tool_starts_with_a_python_shebang() -> None:
    """Read as bytes, so a carriage return behind the shebang cannot hide.

    The tool is run on a Linux box as ./search_load.py, and a CR at the end of
    that first line fails with an error that names an invisible character. The
    checkout rule that keeps it out lives in .gitattributes; this is the gate
    that notices when it stops working.
    """
    assert SEARCH_LOAD.read_bytes().startswith(b"#!/usr/bin/env python3\n")


def test_the_load_tool_carries_neither_a_dash_nor_a_carriage_return() -> None:
    raw = SEARCH_LOAD.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    for dash in DASHES:
        assert dash not in text, f"{dash!r} in {SEARCH_LOAD.name}"


def test_the_load_tool_asks_over_the_ocs_route_and_not_into_the_container() -> None:
    """The route a user takes, with an explicit limit, and nothing else.

    A sample that spoke to the container port would measure the search engine.
    What this tool is for is the other question: what the whole chain costs when
    several people search at once, and the PHP process pool and the permission
    recheck are the halves of it that only the OCS route contains.
    """
    text = SEARCH_LOAD.read_text(encoding="utf-8")
    assert OCS_SEARCH_ROUTE in text
    assert "OCS-APIRequest" in text
    assert '"limit"' in text
    for header in CONTAINER_ONLY_HEADERS:
        assert header not in text, header


def test_the_load_tool_reads_the_cgroup_instead_of_asking_the_client() -> None:
    """Same rule as the sampler, same reason: the client reports memory.current.

    That figure counts the page cache of the mmap index, and a brute force vector
    scan under load pulls the whole stock into the page cache of the very same
    cgroup. Both numbers are read here on purpose, anon and current, because the
    distance between them is what the load does to the file cache.
    """
    text = SEARCH_LOAD.read_text(encoding="utf-8")
    assert DOCKER_MEMORY_SHORTCUT not in text
    assert "memory.stat" in text
    assert "memory.current" in text
    assert "anon" in text
    # Both cgroup driver layouts, as in rss_sampler.sh. Guessing one is a coin
    # toss between Ubuntu and everything else.
    assert "system.slice/docker-" in text
    assert "/docker/" in text


def test_the_load_tool_reads_the_memory_before_during_and_after() -> None:
    """Three readings, because one of them alone answers a different question."""
    text = SEARCH_LOAD.read_text(encoding="utf-8")
    for phase in ('"before"', '"during"', '"after"'):
        assert phase in text, phase


def test_the_machine_path_gate_fires_on_a_staged_sample() -> None:
    """The self test of the gate below, in the shape every textual gate here has.

    A gate whose only assertion is "the current tree is clean" stays green on the
    day somebody deletes its body. The sample is the shape of the reference this
    tool was built from.
    """
    staged = 'import sys\nsys.path.insert(0, "/home/ubuntu/work")\nfrom drillhelfer import suche\n'
    assert machine_shapes(staged) == ["/home/", "drillhelfer", "sys.path.insert"]


def test_the_load_tool_carries_no_path_of_one_machine() -> None:
    """A tool with a machine path in it is a tool for one machine."""
    assert machine_shapes(SEARCH_LOAD.read_text(encoding="utf-8")) == []


def test_the_load_tool_brings_no_third_party_library() -> None:
    """Standard library only, and the point is what is NOT installed for it.

    A third load test tool in this project would be a foreign body for one loop,
    with an installation of its own in an environment that is supposed to work
    offline. The concurrency is a thread pool out of the standard library, and
    backend/uv.lock does not move for this file.
    """
    outside = sorted(imported_packages(SEARCH_LOAD.read_text(encoding="utf-8")) - set(sys.stdlib_module_names))
    assert not outside, outside


def test_the_load_tool_keeps_the_credential_inside_one_function() -> None:
    """The value exists under one name, in one function, and reaches no output.

    Same rule as the two box tools (T-05-17) and the same reason: an output of an
    operating tool ends up in a terminal that is being logged somewhere, and a
    credential that got there once cannot be taken back.
    """
    tree = ast.parse(SEARCH_LOAD.read_text(encoding="utf-8"))
    holders = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and any(isinstance(inner, ast.Name) and inner.id == "secret" for inner in ast.walk(node))
    }
    assert holders == {"_authorization"}, holders

    printing = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        and any(isinstance(inner, ast.Name) and inner.id == "secret" for inner in ast.walk(node))
    ]
    assert not printing, printing


def test_the_load_tool_promises_no_concurrency_number() -> None:
    """It measures, it does not undertake. The number follows in plan 06.1-18.

    A concurrency figure written down before it was measured would be exactly the
    sort of number this project refuses everywhere else, so the module header has
    to say both things: where the number comes from, and what a run of this tool
    does not prove.
    """
    text = SEARCH_LOAD.read_text(encoding="utf-8")
    assert "06.1-18" in text
    assert "does not prove" in text


def test_the_load_tool_names_its_four_knobs_in_the_usage() -> None:
    """Concurrency, rounds, limit and min hits, because --help is the manual.

    The number in the name and the number in the tuple are the same one, and
    that friction is the point of this test: the fourth knob arrived with the
    fix of DI-10-01, and a knob that nobody can see in --help is a knob that
    nobody sets. The address is not one of them; it is the target, and the
    tests that stage a run pass it on every call.
    """
    text = SEARCH_LOAD.read_text(encoding="utf-8")
    knobs = ("--concurrency", "--rounds", "--limit", "--min-hits")
    assert len(knobs) == 4
    for option in knobs:
        assert f'"{option}"' in text, option


# DI-10-01, the counting of an aborted container call. The block below asks the
# tool what it decides rather than what its source says, because the finding was
# never visible in the source: every line of it was doing what it said, and the
# empty list was a list.


def search_load_module() -> ModuleType:
    """The load tool, loaded from its path under a name that is a valid one.

    Loaded rather than run, in the shape test_measurement_scripts.py loads the
    status observer. scripts/ops is not a package and never becomes one for a
    test: the tool is run as ./search_load.py on a box and an __init__.py beside
    it would be a file that exists for this file alone.

    The entry in sys.modules is not decoration. Sample is a dataclass with
    slots, and building one of those means building the class a second time,
    for which dataclasses looks its own module up by name. Without the entry
    the import ends in an AttributeError inside dataclasses.py that names
    neither this file nor the tool.
    """
    specification = importlib.util.spec_from_file_location(SEARCH_LOAD_MODULE, SEARCH_LOAD)
    assert specification is not None, SEARCH_LOAD
    assert specification.loader is not None, SEARCH_LOAD
    module = importlib.util.module_from_spec(specification)
    sys.modules[SEARCH_LOAD_MODULE] = module
    specification.loader.exec_module(module)
    return module


class StagedAnswer:
    """What urlopen hands back: a context manager whose read gives bytes.

    The body is staged as text and encoded here, because that is the way round
    the real answer arrives and a test that handed over a dict would skip the
    json.loads the tool really does.
    """

    def __init__(self, body: str) -> None:
        self.body = body.encode("utf-8")

    def __enter__(self) -> StagedAnswer:
        return self

    def __exit__(self, *_unused: object) -> None:
        """Nothing to close: the body is a string that was in memory all along."""

    def read(self) -> bytes:
        return self.body


def staged_group(hits: int) -> str:
    """An OCS answer carrying that many entries, in the shape the route sends."""
    entries = [{"title": f"treffer {number}", "subline": "gestellt"} for number in range(hits)]
    return json.dumps({"ocs": {"meta": {"status": "ok"}, "data": {"entries": entries}}})


def stage_one_answer(monkeypatch: pytest.MonkeyPatch, body: str) -> None:
    """Point urlopen at one staged body, whatever it is asked for.

    A monkeypatch on urllib.request.urlopen rather than a pure function pulled
    out of _one_search: the decision under test is one comparison inside that
    function, and a helper extracted for the test alone would be a second
    abstraction in a tool whose whole point is that it has none.
    """

    def answer(request: object, **_unused: object) -> StagedAnswer:
        return StagedAnswer(body)

    monkeypatch.setattr(urllib.request, "urlopen", answer)


def stage_hits_per_term(monkeypatch: pytest.MonkeyPatch, hits: Mapping[str, int]) -> None:
    """Stage a hit count per search term, so a run is the same in any order.

    The pool runs the terms concurrently. A staging that counted calls would
    hand out its numbers in the order the threads happen to arrive and make the
    assertion below a coin toss.
    """

    def answer(request: urllib.request.Request, **_unused: object) -> StagedAnswer:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)
        return StagedAnswer(staged_group(hits[query["term"][0]]))

    monkeypatch.setattr(urllib.request, "urlopen", answer)


def test_the_load_tool_counts_a_result_group_without_a_container_part_as_a_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DI-10-01: a 200 with an empty result group is an aborted container call.

    The OCS route answers such a call with a status of 200 and a result group
    that has no container part, so the tool used to see a search that found
    nothing. On 10.09.2026 that put 17 aborted calls of level 16 into the
    Nextcloud log next to "failures": 0 in
    rohdaten/97-stufe-16.json.
    """
    module = search_load_module()
    stage_one_answer(monkeypatch, staged_group(0))

    elapsed_ms, hits, failure = module._one_search("http://localhost:8080/ocs?term=x", "Basic staged", 1)

    assert failure == "EmptyResultGroup"
    assert hits == 0
    assert elapsed_ms >= 0


def test_the_load_tool_takes_min_hits_zero_as_the_reading_from_before(monkeypatch: pytest.MonkeyPatch) -> None:
    """The way out for an instance whose stock does not carry the ten terms.

    Same staged answer as above and the opposite verdict, because the switch is
    the whole difference. Without this direction the fix would be a rule with
    no exception, and an instance that legitimately finds nothing would report
    a hundred percent failures while being perfectly healthy.
    """
    module = search_load_module()
    stage_one_answer(monkeypatch, staged_group(0))

    _, hits, failure = module._one_search("http://localhost:8080/ocs?term=x", "Basic staged", 0)

    assert failure is None
    assert hits == 0


def test_the_load_tool_still_calls_a_body_of_the_wrong_shape_malformed(monkeypatch: pytest.MonkeyPatch) -> None:
    """The older branch keeps its name and keeps standing in front of the new one.

    Both readings of the switch are asked, because the order of the two
    branches is what decides here: a broken route answering with a string where
    the entries belong must not be filed under the empty result group of a
    container that was too slow.
    """
    module = search_load_module()
    stage_one_answer(monkeypatch, json.dumps({"ocs": {"data": {"entries": "kein Container"}}}))

    for min_hits in (0, 1):
        _, hits, failure = module._one_search("http://localhost:8080/ocs?term=x", "Basic staged", min_hits)
        assert failure == "MalformedAnswer", min_hits
        assert hits == 0, min_hits


def test_the_load_tool_counts_a_full_result_group_as_answered(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ordinary case, so that the new comparison cannot pass by failing everything."""
    module = search_load_module()
    stage_one_answer(monkeypatch, staged_group(5))

    _, hits, failure = module._one_search("http://localhost:8080/ocs?term=x", "Basic staged", 1)

    assert failure is None
    assert hits == 5


def test_the_load_tool_reports_a_transport_failure_under_its_own_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """A request that never arrived is not an empty result group either.

    Three kinds of failure now exist and each keeps its own name, because a
    report that threw them together would say that something went wrong and
    nothing about where to look.
    """
    module = search_load_module()

    def refuse(request: object, **_unused: object) -> StagedAnswer:
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    _, hits, failure = module._one_search("http://localhost:8080/ocs?term=x", "Basic staged", 1)

    assert failure == "URLError"
    assert hits == 0


def test_the_report_carries_the_hits_per_request_and_the_switch_it_counted_with(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The fingerprint of DI-10-01, readable without a Nextcloud log.

    Three requests, two of them with five hits and one with none, so the
    quotient is not a whole number and the rounding is part of the assertion.
    The failure and the hits of the same request are both counted: an aborted
    call contributed zero hits and it still happened.
    """
    module = search_load_module()
    monkeypatch.setenv("FINDLING_LOAD_PASSWORD", "gestellt")
    terms = module.TERMS
    stage_hits_per_term(monkeypatch, {terms[0]: 5, terms[1]: 5, terms[2]: 0})
    report_file = tmp_path / "report.json"

    code = module.main(
        [
            "--base-url",
            "http://localhost:8080",
            "--user",
            "lasttest",
            "--concurrency",
            "3",
            "--rounds",
            "1",
            "--json",
            str(report_file),
        ]
    )

    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert code == 0
    assert report["requests"] == 3
    assert report["hits_total"] == 10
    assert report["hits_per_request"] == 3.33
    assert report["min_hits"] == 1
    assert report["failures"] == 1
    assert report["failure_kinds"] == {"EmptyResultGroup": 1}


def test_the_report_says_zero_hits_per_request_and_keeps_the_switch_it_was_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A run with --min-hits 0 stays readable as such after the fact.

    The value stands in the report, so a raw file found years later carries its
    own reading and nobody has to guess which command line produced it. Nothing
    failed here and nothing was found either, which is exactly the state the
    switch exists for.
    """
    module = search_load_module()
    monkeypatch.setenv("FINDLING_LOAD_PASSWORD", "gestellt")
    stage_one_answer(monkeypatch, staged_group(0))
    report_file = tmp_path / "report.json"

    code = module.main(
        [
            "--base-url",
            "http://localhost:8080",
            "--user",
            "lasttest",
            "--concurrency",
            "2",
            "--rounds",
            "1",
            "--min-hits",
            "0",
            "--json",
            str(report_file),
        ]
    )

    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert code == 0
    assert report["min_hits"] == 0
    assert report["failures"] == 0
    assert report["hits_total"] == 0
    assert report["hits_per_request"] == 0.0


def test_a_run_of_nothing_but_empty_result_groups_ends_with_an_exit_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Every request aborted is the one failure this tool has always known.

    With the default switch such a run has no answered request left, and the
    rule of the measuring steps holds: a bad number is a result, an absent one
    is a broken run.
    """
    module = search_load_module()
    monkeypatch.setenv("FINDLING_LOAD_PASSWORD", "gestellt")
    stage_one_answer(monkeypatch, staged_group(0))
    report_file = tmp_path / "report.json"

    code = module.main(
        [
            "--base-url",
            "http://localhost:8080",
            "--user",
            "lasttest",
            "--concurrency",
            "2",
            "--rounds",
            "1",
            "--json",
            str(report_file),
        ]
    )

    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert code == 1
    assert report["failures"] == 2
    assert report["answered"] == 0
    assert report["failure_kinds"] == {"EmptyResultGroup": 2}


def report_keys(text: str) -> list[str]:
    """The keys of the report dictionary of main, in the order they are written.

    Read out of the syntax tree and not with a text search, which is the grep
    hygiene this repository settled on in plan 06-10: the module header of this
    tool discusses failures, hits and the switch at length, so a count of the
    word would count the explanation of it. The tree carries the order too, and
    the order is half of what is asserted below.
    """
    for node in ast.walk(ast.parse(text)):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "report"
            and isinstance(node.value, ast.Dict)
        ):
            written = node.value.keys
            return [key.value for key in written if isinstance(key, ast.Constant) and isinstance(key.value, str)]
    return []


def test_the_report_key_reader_fires_on_a_staged_sample() -> None:
    """The self test of the gate below, in the shape every reader here has.

    A reader whose body was deleted would return the empty list and make the
    assertions below fail closed, which is the wanted direction; the staged
    sample says so rather than leaving it to be assumed.
    """
    staged = 'def main() -> int:\n    report: dict[str, object] = {"erst": 1, "dann": 2}\n    return 0\n'
    assert report_keys(staged) == ["erst", "dann"]
    assert report_keys("report = 5\n") == []


def test_the_report_puts_the_hits_per_request_next_to_the_hits_total() -> None:
    """The fingerprint stands beside the sum it is built from, and the switch with it.

    Beside it and not somewhere in the document, because a reader who finds the
    sum and has to hunt for the quotient will do the division by hand, which is
    exactly how the table of 00-kernaussage.md came about. min_hits belongs in
    the same dictionary for the other half of DI-10-01: a raw file has to carry
    the reading it was written under.
    """
    keys = report_keys(SEARCH_LOAD.read_text(encoding="utf-8"))
    assert "hits_total" in keys, keys
    assert keys.index("hits_per_request") == keys.index("hits_total") + 1, keys
    assert "min_hits" in keys, keys
