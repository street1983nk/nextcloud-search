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
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

OPS_DIR = Path(__file__).resolve().parents[2] / "scripts" / "ops"
RSS_SAMPLER = OPS_DIR / "rss_sampler.sh"
HETZNER_BOX = OPS_DIR / "hetzner_box.sh"
AWS_BOX = OPS_DIR / "aws_box.sh"
SEARCH_LOAD = OPS_DIR / "search_load.py"
# The two samplers of phase 22, W1 and W2. Same frame as the memory sampler and
# therefore in the same fixture below.
CPU_SAMPLER = OPS_DIR / "cpu_sampler.sh"
PROC_ANON_SAMPLER = OPS_DIR / "proc_anon_sampler.sh"

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


@pytest.fixture(
    params=[RSS_SAMPLER, HETZNER_BOX, AWS_BOX, CPU_SAMPLER, PROC_ANON_SAMPLER],
    ids=lambda path: path.name,
)
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


# W1, the core usage sampler of phase 22. Its promises are the ones of the memory
# sampler with cpu.stat in place of memory.stat, plus one of its own: a container
# rebuild removes the cgroup halfway through a run, and the sampler has to end
# that run with a closing line rather than die quietly under set -eu (22-RESEARCH
# pitfall 4).


def test_the_cpu_sampler_knows_both_cgroup_driver_layouts() -> None:
    text = CPU_SAMPLER.read_text(encoding="utf-8")
    assert "system.slice/docker-" in text
    assert "/docker/$CONTAINER_ID" in text


def test_the_cpu_sampler_reads_the_cgroup_instead_of_asking_the_client() -> None:
    text = CPU_SAMPLER.read_text(encoding="utf-8")
    assert DOCKER_MEMORY_SHORTCUT not in text
    assert "cpu.stat" in text
    assert "usage_usec" in text
    assert "/proc/stat" in text
    assert "PREFIX='findling-cpu'" in text


def test_the_cpu_sampler_refuses_rather_than_writing_zeroes() -> None:
    text = CPU_SAMPLER.read_text(encoding="utf-8")
    assert "no readable cpu.stat" in text
    assert "not one sample was written" in text


def test_the_cpu_sampler_checks_the_cgroup_before_every_read() -> None:
    """The check sits inside the loop and leads to the closing line, not to a crash."""
    text = CPU_SAMPLER.read_text(encoding="utf-8")
    loop = text[text.index("while :; do") :]
    assert '[ ! -r "$CGROUP/cpu.stat" ]' in loop
    assert "finish 'cgroup gone'" in loop
    assert "trap 'finish signal' INT TERM" in text


def test_the_cpu_sampler_ends_without_a_data_line_when_there_is_no_cpu_stat(tmp_path: Path) -> None:
    """Behaviour, not text: a staged docker and a cgroup directory without cpu.stat.

    The cgroup directory exists and is empty, which is the shape a cgroup v1 host
    or a nested setup leaves behind. The sampler has to refuse with a non zero
    return and without writing a single line into its output file.
    """
    shell = shutil.which("sh")
    if shell is None:
        pytest.skip("no POSIX sh on this machine, the text gates above still hold")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_docker = bin_dir / "docker"
    fake_docker.write_text("#!/bin/sh\necho 0123abcd\n", encoding="utf-8", newline="\n")
    fake_docker.chmod(0o755)
    cgroup_root = tmp_path / "cgroup"
    (cgroup_root / "system.slice" / "docker-0123abcd.scope").mkdir(parents=True)
    output = tmp_path / "cpu.csv"
    environment = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        "FINDLING_CGROUP_ROOT": cgroup_root.as_posix(),
    }
    finished = subprocess.run(  # noqa: S603 - fixed argument list, no shell string
        [shell, CPU_SAMPLER.as_posix(), "staged", "1", output.as_posix()],
        capture_output=True,
        text=True,
        env=environment,
        timeout=30,
        check=False,
    )
    assert finished.returncode != 0, finished.stderr
    assert "no readable cpu.stat" in finished.stderr
    assert not output.exists() or output.read_text(encoding="utf-8") == ""


# W2, the per process anon sampler. The one promise that is its own: it reads
# three fields of the status file and never the argument list of a process,
# which can carry file paths of the instance being indexed (T-02-14).

# Assembled so this file does not carry the word it forbids in a script.
PROC_ARGUMENT_FILE = "cmd" + "line"


def test_the_anon_sampler_reads_three_fields_and_never_the_argument_list() -> None:
    text = PROC_ANON_SAMPLER.read_text(encoding="utf-8")
    assert "RssAnon" in text
    assert "VmHWM" in text
    assert "/status" in text
    assert PROC_ARGUMENT_FILE not in text
    assert "/environ" not in text


def test_the_anon_sampler_refuses_rather_than_writing_zeroes() -> None:
    text = PROC_ANON_SAMPLER.read_text(encoding="utf-8")
    assert "PREFIX='findling-anon'" in text
    assert "not one sample was written" in text
    assert DOCKER_MEMORY_SHORTCUT not in text


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


def test_the_aws_tool_names_its_nine_subcommands_in_the_usage() -> None:
    """Nine and not five: the box lives between stop and start, and it outlives itself.

    The box of the ARM run was created by hand, so create is a record of what
    happened and refuses to make a second machine, while the volume that the
    corpus lives on is created by the tool and has to be findable in it. stop
    and start came late, in 06.1-18, because until then the box was parked and
    woken by hand, which meant past the cost arithmetic of this script. snapshot
    came in 11-12, because the corpus of the run has to survive the machine that
    carried it, and a snapshot taken by hand is a snapshot whose verification
    nobody keeps.

    restore is the ninth and it came in 12-03, because the corpus really did
    outlive the machine and there was no way back: volume creates an empty one,
    and the only path from the snapshot to a mounted corpus was a create-volume
    typed by hand on the day the measurement box is paid for by the hour. The
    rule of this phase is that no tool is touched during a paid run, so the way
    back is built here and not there.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    for subcommand in ("prices", "create", "volume", "restore", "status", "stop", "start", "snapshot", "destroy"):
        assert f"    {subcommand})" in text, subcommand
    assert "usage: aws_box.sh <prices|create|volume|restore|status|stop|start|snapshot|destroy>" in text


def test_the_aws_restore_reads_the_snapshot_before_it_creates_anything() -> None:
    """A volume out of an unfinished snapshot is missing blocks and says nothing about it.

    The refusal therefore stands in front of the first call that costs money,
    exactly as the stopped check does in the snapshot subcommand: State has to
    read completed, and the size of the snapshot has to fit the size this script
    asks for, because the api refuses the second one after the request rather
    than before it. The zone is asserted with it: a volume can only be attached
    inside its own zone and it cannot be moved afterwards (T-12-13).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_restore() {", 1)[1].split("\ncmd_status() {", 1)[0]
    assert "--snapshot-id" in body
    assert '--availability-zone "$ZONE"' in body
    # Read first, create second, and the refusal in between.
    assert body.index("describe-snapshots") < body.index("create-volume")
    assert body.index("!= 'completed'") < body.index("create-volume")
    assert body.index("-gt") < body.index("create-volume")
    # The waiters of the cli and no loop of its own, house rule since 2026-09-04.
    assert "ec2 wait volume-available" in body
    assert "ec2 wait volume-in-use" in body
    assert body.index("wait volume-available") < body.index("attach-volume")
    # The snapshot the corpus lands from is written down next to the volume,
    # because a measurement against a restored corpus has to name the corpus.
    assert "VOLUME_FROM_SNAPSHOT=$snapshot_id" in body


def test_the_aws_restore_retags_the_volume_and_reads_the_tags_back() -> None:
    """The inherited tag turns a restored volume into an invoice nobody looks for.

    The snapshot carries purpose=findling-corpus-keep on purpose, because it is
    the one resource of the run that is meant to outlive the box. A volume
    restored from it inherits exactly that tag, and on a volume it is the
    opposite of harmless: the sweep of cmd_destroy searches for
    purpose=findling-phase5, so the volume survives a teardown that reports
    itself clean and goes on being billed. The retagging is therefore a step of
    the subcommand and not a line in a runbook, and the read back is what
    decides, because an accepted api call does not say what the resource now
    carries (T-12-10).
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_restore() {", 1)[1].split("\ncmd_status() {", 1)[0]
    assert body.index("create-volume") < body.index("create-tags")
    assert body.index("create-tags") < body.index("describe-tags")
    assert '"Key=$TAG_KEY,Value=$TAG_VALUE"' in body
    # The abort names the inherited value, so a volume that still carries it
    # never reaches the attach.
    assert "KEEP_TAG_VALUE" in body
    assert body.index("KEEP_TAG_VALUE") < body.index("attach-volume")
    assert "CORPUS_SNAPSHOT_DEFAULT='snap-03f1d1d9ad9262704'" in text


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


def test_the_aws_destroy_takes_the_key_pair_with_it_and_reads_it_back() -> None:
    """L-07: the teardown left the key pair behind, and 15-14 closed it by hand.

    Two promises and not one, because a fassung that only calls delete would
    pass a test for the call alone while leaving the same finding open. The
    account answers the delete before it has forgotten anything, so the proof in
    this script is the read back, exactly as it is for the instance, the volume
    and the security group.

    The order is asserted as well. The pair goes after the instance and after
    the volume: an abort between the calls would otherwise leave a running box
    whose key is gone, which is a worse state than the leftover this closes.
    """
    text = AWS_BOX.read_text(encoding="utf-8")
    body = text.split("cmd_destroy() {", 1)[1]
    # A failure is an answer here, the same as for the two other deletions, so
    # that a pair which is already gone does not end the teardown.
    assert "ec2_soft delete-key-pair" in body
    assert 'resource_gone "$(ec2_soft describe-key-pairs' in body
    # After instance and volume, and the read back after the deletion.
    assert body.index("terminate-instances") < body.index("delete-key-pair")
    assert body.index("delete-volume") < body.index("delete-key-pair")
    assert body.index("delete-key-pair") < body.index("describe-key-pairs")
    # A read back whose result goes nowhere is not a proof either.
    assert "key pair $SSH_KEY_NAME is gone, verified against the api" in body
    assert body.index("describe-key-pairs") < body.index('rm -f "$STATE_FILE"')
    # The finding stands in the file, so the next reader of this block knows
    # which hand grip it replaces.
    assert "L-07" in text


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


# DI-11-03, the pre-run probe. The block below asks the tool what it decides,
# in the same shape as the block above it, because the finding of DI-11-03 is a
# decision and not a line: a term without stock and an aborted call arrive at
# this tool as the same answer, and only something asked before the run can tell
# them apart.


def stage_probe(monkeypatch: pytest.MonkeyPatch, module: ModuleType, returncode: int, stdout: str) -> None:
    """Put a staged answer of the container in front of the probe.

    The name subprocess is rebound in the module under test rather than the run
    of the real subprocess module, so that nothing outside this test sees a
    different subprocess while it runs. SubprocessError travels along because the
    probe catches it by that name.
    """

    def answer(*_unused: object, **_unused_keywords: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(
        module,
        "subprocess",
        SimpleNamespace(run=answer, SubprocessError=subprocess.SubprocessError),
    )


def test_the_probe_names_the_terms_the_index_holds_nothing_for(monkeypatch: pytest.MonkeyPatch) -> None:
    """One line per term, and the terms without stock named in the head of it.

    The stock figure comes out of the process of the container over ranked_sides,
    which is the same question 73-bestand-sonde.py asks, because from outside
    there is no answer at all: the OCS route answers an aborted call and a search
    that found nothing with the same 200 and the same result group without a
    container part.
    """
    module = search_load_module()
    stock = dict.fromkeys(module.TERMS, 7)
    stock[module.TERMS[5]] = 0
    stage_probe(
        monkeypatch,
        module,
        0,
        "".join(f"stock={number} window={min(number, 100)} term={term}\n" for term, number in stock.items()),
    )

    stockless, lines = module._probe("nc_app_findling_backend")

    assert stockless == frozenset({module.TERMS[5]})
    assert lines[0].startswith("vorlaufsonde ")
    assert f"ohne treffer: {module.TERMS[5]}" in lines
    # One line per term, so a reader sees the stock and not only the verdict.
    for term in module.TERMS:
        assert any(line.startswith("bestand=") and line.endswith(f"begriff={term}") for line in lines), term


def test_the_probe_that_does_not_answer_says_so_instead_of_guessing(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-16-13: a silent return to the old counting is the finding itself.

    Three ways of not answering are asked, because they arrive on three different
    paths and all three have to end in the same line: no container was named, the
    program in the container failed, and the program answered for some of the
    terms. None of them may hand back the empty set, which would say every term
    has stock.
    """
    module = search_load_module()

    stockless, lines = module._probe(None)
    assert stockless is None
    assert lines[0] == "vorlaufsonde: nicht verfuegbar"

    stage_probe(monkeypatch, module, 2, "")
    stockless, lines = module._probe("nc_app_findling_backend")
    assert stockless is None
    assert lines[0] == "vorlaufsonde: nicht verfuegbar"

    stage_probe(monkeypatch, module, 0, f"stock=0 window=0 term={module.TERMS[0]}\n")
    stockless, lines = module._probe("nc_app_findling_backend")
    assert stockless is None
    assert lines[0] == "vorlaufsonde: nicht verfuegbar"


def test_the_report_splits_the_empty_groups_by_what_the_probe_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ohne-treffer and fehlschlag apart, and the total still beside them.

    Two answers below the switch, one of them for a term the probe reported as
    stockless. The total stays where it was so that a raw file of this tool can
    be read against one from before 21.09.2026, which is the half of DI-10-01
    that must not be lost while DI-11-03 is closed.
    """
    module = search_load_module()
    monkeypatch.setenv("FINDLING_LOAD_PASSWORD", "gestellt")
    terms = module.TERMS
    stage_hits_per_term(monkeypatch, {terms[0]: 0, terms[1]: 0, terms[2]: 5})
    monkeypatch.setattr(module, "_probe", lambda _container: (frozenset({terms[0]}), ["vorlaufsonde gestellt"]))
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
    assert report["vorlaufsonde"] == ["vorlaufsonde gestellt"]
    assert report["failures"] == 2
    assert report["failure_kinds"] == {"EmptyResultGroup": 2}
    assert report["empty_result_groups"] == {"gesamt": 2, "ohne-treffer": 1, "fehlschlag": 1}


def test_a_report_without_a_probe_carries_the_line_and_no_split(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The raw file of a run without the probe says which reading it was written under.

    No container is named here, which is the ordinary way to run this tool
    against an instance whose container is out of reach, and the split then has
    to be absent by name rather than quietly identical to the old counting.
    """
    module = search_load_module()
    monkeypatch.setenv("FINDLING_LOAD_PASSWORD", "gestellt")
    stage_one_answer(monkeypatch, staged_group(0))
    report_file = tmp_path / "report.json"

    module.main(
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

    raw = report_file.read_text(encoding="utf-8")
    report = json.loads(raw)
    assert report["vorlaufsonde"][0] == "vorlaufsonde: nicht verfuegbar"
    assert "vorlaufsonde: nicht verfuegbar" in raw
    assert "ohne-treffer" not in report["empty_result_groups"]
    assert report["empty_result_groups"]["gesamt"] == 2


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
    # DI-11-03: the probe belongs in the head of the file, in front of every
    # measured figure, because its list is what the figures below have to be read
    # with. A list at the end would be a footnote to a number nobody re-reads.
    assert keys.index("vorlaufsonde") == 0, keys
    assert keys.index("empty_result_groups") == keys.index("failure_kinds") + 1, keys


# W3 of phase 22, the OCR slot probe. It runs inside the product image with
# scripts/ops mounted read only, so the house rules of the load tool apply to it
# with one difference that is named rather than hidden: it imports the product,
# because driving the product's own extraction child is the whole point of it.

OCR_SLOT_PROBE = OPS_DIR / "ocr_slot_probe.py"
OCR_SLOT_PROBE_MODULE = "findling_ocr_slot_probe"

# The two packages outside the standard library the probe may import, each
# inside a function and never at module level. findling is the product under
# measurement. pypdfium2 renders the page of the single mode exactly the way
# findling.extract.raster does, which takes a document of that library.
OCR_SLOT_PROBE_PACKAGES = frozenset({"findling", "pypdfium2"})

# The resource counter that misses the tesseract grandchildren of a long lived
# worker child, assembled so this file does not carry the name it forbids.
CHILD_RESOURCE_COUNTER = "RUSAGE_" + "CHILDREN"


def ocr_slot_probe_module() -> ModuleType:
    """The probe, loaded from its path, in the shape of search_load_module."""
    specification = importlib.util.spec_from_file_location(OCR_SLOT_PROBE_MODULE, OCR_SLOT_PROBE)
    assert specification is not None, OCR_SLOT_PROBE
    assert specification.loader is not None, OCR_SLOT_PROBE
    module = importlib.util.module_from_spec(specification)
    sys.modules[OCR_SLOT_PROBE_MODULE] = module
    specification.loader.exec_module(module)
    return module


def test_the_slot_probe_starts_with_a_python_shebang() -> None:
    assert OCR_SLOT_PROBE.read_bytes().startswith(b"#!/usr/bin/env python3\n")


def test_the_slot_probe_carries_neither_a_dash_nor_a_carriage_return() -> None:
    raw = OCR_SLOT_PROBE.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    for dash in DASHES:
        assert dash not in text, f"{dash!r} in {OCR_SLOT_PROBE.name}"


def test_the_slot_probe_carries_no_path_of_one_machine() -> None:
    assert machine_shapes(OCR_SLOT_PROBE.read_text(encoding="utf-8")) == []


def test_the_slot_probe_imports_the_product_only_inside_functions() -> None:
    """Module level is standard library only; the two named exceptions come late.

    Late, so the argument check and the report can be loaded and tested on a
    machine without the product, and so a run that fails its arguments has not
    paid for the import of the extraction stack.
    """
    text = OCR_SLOT_PROBE.read_text(encoding="utf-8")
    outside = imported_packages(text) - set(sys.stdlib_module_names)
    assert outside <= OCR_SLOT_PROBE_PACKAGES, sorted(outside)
    top_level: set[str] = set()
    for node in ast.parse(text).body:
        if isinstance(node, ast.Import):
            top_level.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            top_level.add(node.module.split(".")[0])
    assert not top_level - set(sys.stdlib_module_names), sorted(top_level)


def test_the_slot_probe_drives_the_extraction_worker_over_the_ocr_route() -> None:
    text = OCR_SLOT_PROBE.read_text(encoding="utf-8")
    assert "ExtractionWorker" in text
    assert 'route="ocr"' in text
    assert "sched_getaffinity" in text
    assert "cpu.stat" in text
    assert "memory.stat" in text
    assert CHILD_RESOURCE_COUNTER not in text


def test_the_slot_probe_refuses_zero_slots_and_a_missing_scan(tmp_path: Path) -> None:
    probe = ocr_slot_probe_module()
    scan = tmp_path / "scan-8.pdf"
    scan.write_bytes(b"%PDF-1.4\n")
    assert probe.main(["--slots", "0", "--scan", str(scan)]) == 2
    assert probe.main(["--slots", "1"]) == 2
    assert probe.main(["--slots", "1", "--scan", str(tmp_path / "absent.pdf")]) == 2


def test_the_slot_probe_loads_and_refuses_without_importing_the_product(tmp_path: Path) -> None:
    """In a fresh interpreter, where findling is importable and nothing has imported it yet."""
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location({OCR_SLOT_PROBE_MODULE!r}, {OCR_SLOT_PROBE.as_posix()!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        f"sys.modules[{OCR_SLOT_PROBE_MODULE!r}] = module\n"
        "spec.loader.exec_module(module)\n"
        f"code = module.main(['--slots', '0', '--scan', {tmp_path.as_posix()!r}])\n"
        "print(code, 'findling' in sys.modules)\n"
    )
    finished = subprocess.run(  # noqa: S603 - fixed argument list, no shell string
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False
    )
    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.split() == ["2", "False"], finished.stdout


def test_the_slot_probe_reports_numbers_and_never_the_text() -> None:
    """The report of a staged series: exactly the named lines, no extracted text."""
    probe = ocr_slot_probe_module()
    extracted = "Grundstuecksverkehrsgenehmigung der Familie Beispiel"
    indexed = SimpleNamespace(state="indexed", reason=None, text=extracted)
    cut = SimpleNamespace(state="indexed", reason="truncated", text=extracted)
    rounds = [
        probe.round_from_outcomes(1, 10.0, 8, [indexed, indexed], 1_000, 2_000_000),
        probe.round_from_outcomes(2, 8.0, 8, [indexed, indexed], None, None),
        probe.round_from_outcomes(3, 16.0, 8, [indexed, cut], -5, 1_500_000),
    ]
    lines = probe.report_lines("aarch64", 2, 2, rounds)
    assert extracted not in "\n".join(lines)
    assert [line.split()[0] for line in lines] == [
        "arch",
        "cpus_visible",
        "slots",
        "round",
        "round",
        "round",
        "pages_per_second_median",
    ]
    for line in lines[3:6]:
        words = line.split()
        assert "anon_bytes_delta" in words, line
        assert "cpu_usec" in words, line
    assert lines[3] == (
        "round 1 wall_seconds 10.000 pages_per_second 1.600 anon_bytes_delta 1000 cpu_usec 2000000 failed_slots 0"
    )
    assert "anon_bytes_delta na cpu_usec na" in lines[4]
    # The truncated slot is a lost slot: its pages are not counted.
    assert lines[5].endswith("failed_slots 1")
    assert lines[6] == "pages_per_second_median 1.600"
