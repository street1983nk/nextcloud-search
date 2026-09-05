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
"""

from __future__ import annotations

from pathlib import Path

import pytest

OPS_DIR = Path(__file__).resolve().parents[2] / "scripts" / "ops"
RSS_SAMPLER = OPS_DIR / "rss_sampler.sh"
HETZNER_BOX = OPS_DIR / "hetzner_box.sh"
AWS_BOX = OPS_DIR / "aws_box.sh"

# Assembled from code points so that this file does not carry the characters it
# forbids and fail on itself.
DASHES = (chr(0x2014), chr(0x2013))

# The two words the sampler may not contain, for the reason in the module
# docstring. Assembled for the same reason as the dashes.
DOCKER_MEMORY_SHORTCUT = "docker" + " " + "stats"


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


def test_the_aws_tool_names_its_five_subcommands_in_the_usage() -> None:
    """Five and not four: the data volume is its own step on this provider.

    The box of the ARM run was created by hand, so create is a record of what
    happened and refuses to make a second machine, while the volume that the
    corpus lives on is created by the tool and has to be findable in it.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    for subcommand in ("prices", "create", "volume", "status", "destroy"):
        assert f"    {subcommand})" in text, subcommand
    assert "usage: aws_box.sh <prices|create|volume|status|destroy>" in text


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
