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
import sys
from pathlib import Path

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


def test_the_load_tool_names_its_three_knobs_in_the_usage() -> None:
    """Concurrency, rounds and target, because --help is the whole manual."""
    text = SEARCH_LOAD.read_text(encoding="utf-8")
    for option in ("--concurrency", "--rounds", "--base-url"):
        assert f'"{option}"' in text, option
