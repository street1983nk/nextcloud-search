"""The type switch of the acceptance trip of phase 28, plan 28-03.

00-typwechsel.sh of the v1.3 trip knew two fixed types and a fallback of its
own. The matrix of phase 28 runs six types on two boxes (D-28-03, D-28-04):
m7g.large and m7g.4xlarge on the arm box, c7a.xlarge up to c7a.8xlarge on the
x86 box. The successor takes the target type as an argument, refuses a switch
across the architecture (the image of an instance is fixed at its creation),
falls back to nothing without the owner, reads the public price card instead of
the price api the account may not read, and reads the vCPU quota and the zone
offering for free.

None of it has run yet. The runs below go against a stub of the aws command
line, a stub of aws_box.sh and a stub of curl; no account is reached. The house
rules of the directory (shebang, no carriage return, no dash, no machine path,
no password on a command line) come from test_measurement_scripts through
NARROW_SCOPE_DIRS.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_measurement_scripts import MEASUREMENTS_DIR, a_boxless_run

RUN_DIR = MEASUREMENTS_DIR / "2026-10-abnahme-anfahrt" / "skripte"
TYPE_SWITCH = RUN_DIR / "00-typwechsel.sh"

# Two values that stand for the credentials. They are no credentials of any
# account; the runs prove that neither reaches an output.
ACCESS_STAND_IN = "zugang-attrappe-2803b"
SIGNING_STAND_IN = "geheim-attrappe-2803b"
STUB_INSTANCE = "i-attrappe-v14"
STUB_ADDRESS = "10.0.0.2"

ALLOWED = ("m7g.large", "m7g.4xlarge", "c7a.xlarge", "c7a.2xlarge", "c7a.4xlarge", "c7a.8xlarge")
UTC = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"

needs_sh = pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")

STUB_AWS = """#!/bin/sh
printf '%s\\n' "$*" >>"$STUB/aufrufe"
case "$*" in
*get-service-quota*) printf '256.0\\n'; exit 0 ;;
*describe-instance-type-offerings*) printf 'eu-central-1c\\teu-central-1a\\n'; exit 0 ;;
*describe-instance-attribute*) printf '%s\\n' "$STUB_SHUTDOWN"; exit 0 ;;
*modify-instance-attribute*)
    [ "${STUB_KLEBT:-}" = 1 ] && exit 0
    for a in "$@"; do
        case "$a" in Value=*) printf '%s\\n' "${a#Value=}" >"$STUB/typ" ;; esac
    done
    exit 0 ;;
*InstanceType*) cat "$STUB/typ"; exit 0 ;;
*State.Name*)
    if [ -n "${STUB_ZUSTAND:-}" ]; then printf '%s\\n' "$STUB_ZUSTAND"; else cat "$STUB/zustand"; fi
    exit 0 ;;
*PublicIpAddress*) printf '%s\\n' "$STUB_ADRESSE"; exit 0 ;;
esac
exit 1
"""

# aws_box.sh, played the same way: stop parks, start fails for every type named
# in STUB_OHNE_KAPAZITAET, which is what a capacity shortage looks like.
STUB_AWS_BOX = """#!/bin/sh
printf 'aws_box %s\\n' "$1" >>"$STUB/aufrufe"
case "$1" in
stop) printf 'stopped\\n' >"$STUB/zustand"; exit 0 ;;
start)
    typ=$(cat "$STUB/typ")
    case " ${STUB_OHNE_KAPAZITAET:-} " in *" $typ "*) exit 1 ;; esac
    printf 'running\\n' >"$STUB/zustand"
    exit 0 ;;
esac
exit 2
"""

# curl, played by a script that hands out the staged price card.
STUB_CURL = """#!/bin/sh
printf 'curl %s\\n' "$*" >>"$STUB/aufrufe"
[ -f "$STUB/karte" ] || exit 22
ziel=''
while [ "$#" -gt 0 ]; do
    case "$1" in
    -o) shift; ziel=$1 ;;
    esac
    shift
done
if [ -n "$ziel" ]; then
    cat "$STUB/karte" >"$ziel"
else
    cat "$STUB/karte"
fi
exit 0
"""


def a_price_card(rates: dict[str, str]) -> bytes:
    """A price card in the shape of the public one, gzipped as it is served."""
    entries = {
        f"{instance_type} Linux": {
            "rateCode": f"ATTRAPPE.{instance_type}",
            "price": rate,
            "Location": "EU (Frankfurt)",
            "Instance Type": instance_type,
            "Operating System": "Linux",
        }
        for instance_type, rate in rates.items()
    }
    card = {"manifest": {"publicationDate": "2026-09-25T17:45:21Z"}, "regions": {"EU (Frankfurt)": entries}}
    return gzip.compress(json.dumps(card).encode("utf-8"))


def a_stubbed_switch(
    tmp_path: Path,
    arguments: list[str],
    *,
    start_type: str = "m7g.large",
    umgebung: dict[str, str | None] | None = None,
    card: bytes | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path, list[str]]:
    """00-typwechsel.sh against the stubs, and the raw file and the calls it left."""
    stub = tmp_path / "stub"
    stub.mkdir(parents=True)
    (stub / "typ").write_text(f"{start_type}\n", encoding="utf-8", newline="\n")
    (stub / "zustand").write_text("running\n", encoding="utf-8", newline="\n")
    (stub / "aufrufe").write_text("", encoding="utf-8", newline="\n")
    if card is not None:
        (stub / "karte").write_bytes(card)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    # The python3 of the development machine may be a store stub; the tool gets
    # the interpreter of this test run under that name instead.
    python3 = f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "$@"\n'
    for name, body in (("aws", STUB_AWS), ("curl", STUB_CURL), ("python3", python3)):
        path = bin_dir / name
        path.write_text(body, encoding="utf-8", newline="\n")
        path.chmod(0o755)
    aws_box = tmp_path / "aws_box.sh"
    aws_box.write_text(STUB_AWS_BOX, encoding="utf-8", newline="\n")
    state = tmp_path / "zustand"
    state.mkdir()
    (state / "box.env").write_text(f"BOX_INSTANCE_ID={STUB_INSTANCE}\n", encoding="utf-8", newline="\n")
    out = tmp_path / "out"
    environment: dict[str, str | None] = {
        "PATH": f"{bin_dir.as_posix()}{os.pathsep}{os.environ.get('PATH', '')}",
        "AWS_ACCESS_KEY_ID": ACCESS_STAND_IN,
        "AWS_SECRET_ACCESS_KEY": SIGNING_STAND_IN,
        "AWS_CLI": (bin_dir / "aws").as_posix(),
        "AWS_BOX": aws_box.as_posix(),
        "FINDLING_LOADTEST_DIR": state.as_posix(),
        "STUB": stub.as_posix(),
        "STUB_SHUTDOWN": "stop",
        "STUB_ADRESSE": STUB_ADDRESS,
        **(umgebung or {}),
    }
    answer = a_boxless_run(TYPE_SWITCH, out, arguments, umgebung=environment)
    calls = (stub / "aufrufe").read_text(encoding="utf-8").splitlines()
    return answer, out / "00-typwechsel.txt", calls


def raw_of(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def code_of(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def aborts_in(code: str) -> set[str]:
    return set(re.findall(r"exit \d+", code))


def test_the_type_switch_says_once_that_it_never_runs_on_the_box() -> None:
    """The credentials write to EC2; the box must never see them (T-28-12)."""
    text = TYPE_SWITCH.read_text(encoding="utf-8")
    assert text.count("NIE AUF DER BOX") == 1
    assert "DIESE FASSUNG IST NICHT GEFAHREN" in text


def test_the_type_switch_turns_the_windows_path_rewriting_off() -> None:
    code = code_of(TYPE_SWITCH.read_text(encoding="utf-8"))
    assert "MSYS_NO_PATHCONV=1" in code
    assert "MSYS2_ARG_CONV_EXCL='*'" in code


def test_the_price_survives_the_windows_argument_and_path_handling() -> None:
    """Both failures of 30.09.2026: no path for curl, no backslash for python."""
    code = code_of(TYPE_SWITCH.read_text(encoding="utf-8"))
    fetch = next(line for line in code.splitlines() if "curl -sS" in line)
    assert " -o " not in fetch
    assert '>"$karte"' in fetch
    program = code.split('"$PYTHON" -c \'', 1)[1].split("'", 1)[0]
    assert "\\" not in program


def test_the_type_switch_is_executable_in_the_index() -> None:
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        ["git", "ls-files", "-s", TYPE_SWITCH.as_posix()],  # noqa: S607 - git from the path
        capture_output=True,
        text=True,
        check=False,
        cwd=RUN_DIR,
    )
    assert answer.stdout.startswith("100755"), answer.stdout


@needs_sh
@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["weg"],
        ["hin"],
        ["wechsel"],
        ["wechsel", "t3.micro"],
        ["wechsel", "m7g.2xlarge"],
        ["wechsel", "c7a.xlarge", "c7a.2xlarge"],
        ["vorpruefung", "jetzt"],
        ["preis"],
        ["preis", "M7G.large"],
        ["preis", "m7g large"],
        ["quota", ".c7a"],
    ],
    ids=[
        "none",
        "unknown",
        "old-hin",
        "wechsel-bare",
        "wechsel-foreign",
        "wechsel-not-in-matrix",
        "wechsel-two",
        "vorpruefung-extra",
        "preis-bare",
        "preis-upper",
        "preis-space",
        "quota-dot",
    ],
)
def test_the_type_switch_names_its_steps_and_refuses_everything_else(tmp_path: Path, arguments: list[str]) -> None:
    """2 and the usage, before a credential is asked for and before any file."""
    answer = a_boxless_run(TYPE_SWITCH, tmp_path, arguments)
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    for step in ("vorpruefung", "wechsel", "preis", "quota"):
        assert step in answer.stderr
    for allowed in ALLOWED:
        assert allowed in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_type_switch_demands_both_credentials_and_never_prints_them() -> None:
    text = TYPE_SWITCH.read_text(encoding="utf-8")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        assert f': "${{{name}:?' in text, name
        expanding = [line for line in text.splitlines() if f"${name}" in line or f"${{{name}" in line]
        assert len(expanding) == 1, expanding
        assert not [line for line in text.splitlines() if ("echo" in line or "printf" in line) and name in line]


@needs_sh
@pytest.mark.parametrize("missing", ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"])
def test_the_type_switch_refuses_to_run_without_a_credential(tmp_path: Path, missing: str) -> None:
    answer, raw, calls = a_stubbed_switch(tmp_path, ["wechsel", "m7g.4xlarge"], umgebung={missing: None})
    assert answer.returncode != 0, answer
    assert not raw.exists()
    assert calls == []


@needs_sh
@pytest.mark.parametrize("behaviour", ["terminate", "", "unlesbar"])
def test_the_precheck_ends_with_52_when_a_shutdown_would_not_be_a_stop(tmp_path: Path, behaviour: str) -> None:
    answer, raw, calls = a_stubbed_switch(tmp_path, ["vorpruefung"], umgebung={"STUB_SHUTDOWN": behaviour})
    assert answer.returncode == 52, answer
    text = raw_of(raw)
    assert "shutdown-ist-stopp nein" in text
    assert "vorpruefung-stop-ja" not in text
    assert not [call for call in calls if "modify-instance-attribute" in call or call.startswith("aws_box")]


@needs_sh
def test_the_precheck_writes_the_mark_the_chain_reads(tmp_path: Path) -> None:
    """vorpruefung-stop-ja <UTC> is what VORPRUEFUNG=stop-ja of 00-kette.sh is set from."""
    answer, raw, _ = a_stubbed_switch(tmp_path, ["vorpruefung"])
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "shutdown-verhalten stop" in text
    assert re.search(rf"^vorpruefung-stop-ja {UTC}$", text, re.MULTILINE), text


@needs_sh
@pytest.mark.parametrize(
    ("start_type", "target"),
    [
        ("m7g.large", "m7g.4xlarge"),
        ("m7g.4xlarge", "m7g.large"),
        ("c7a.xlarge", "c7a.2xlarge"),
        ("c7a.2xlarge", "c7a.4xlarge"),
        ("c7a.4xlarge", "c7a.8xlarge"),
    ],
)
def test_the_switch_goes_by_stop_modify_start_and_reads_type_and_state_back(
    tmp_path: Path, start_type: str, target: str
) -> None:
    answer, raw, calls = a_stubbed_switch(tmp_path, ["wechsel", target], start_type=start_type)
    assert answer.returncode == 0, answer
    precheck = next(n for n, call in enumerate(calls) if "describe-instance-attribute" in call)
    stop = calls.index("aws_box stop")
    modify = next(n for n, call in enumerate(calls) if "modify-instance-attribute" in call)
    start = calls.index("aws_box start")
    assert precheck < stop < modify < start
    assert f"Value={target}" in calls[modify]
    assert any("InstanceType" in call for call in calls[start:]), calls
    assert any("State.Name" in call for call in calls[start:]), calls
    text = raw_of(raw)
    wanted = rf"^typwechsel {re.escape(start_type)} -> {re.escape(target)} gestoppt {UTC} laeuft {UTC}$"
    assert re.search(wanted, text, re.MULTILINE), text
    assert f"typ-ist {target}" in text
    assert "TYPWECHSEL-FERTIG" in text
    assert "instanz <instanzkennung>" in text
    assert "adresse-neu <adresse-der-box>" in text
    assert STUB_INSTANCE not in text
    assert STUB_ADDRESS not in text
    # The address goes to the terminal, because the A record has to follow it.
    assert STUB_ADDRESS in answer.stderr


@needs_sh
@pytest.mark.parametrize(
    ("start_type", "target"),
    [("m7g.large", "c7a.xlarge"), ("m7g.4xlarge", "c7a.8xlarge"), ("c7a.xlarge", "m7g.large")],
)
def test_the_switch_refuses_to_cross_the_architecture_with_nothing_but_a_describe(
    tmp_path: Path, start_type: str, target: str
) -> None:
    """The architecture hangs on the image: arm to x86 is a second instance, not a modify (T-28-14)."""
    answer, raw, calls = a_stubbed_switch(tmp_path, ["wechsel", target], start_type=start_type)
    assert answer.returncode == 54, answer
    assert calls, calls
    for call in calls:
        assert call.startswith("--region"), call
        assert " describe-" in call, call
    text = raw_of(raw)
    assert f"typwechsel-verweigert architektur {start_type} -> {target}" in text
    assert "TYPWECHSEL-FERTIG" not in text


@needs_sh
def test_the_switch_to_the_type_it_already_has_does_nothing(tmp_path: Path) -> None:
    answer, raw, calls = a_stubbed_switch(tmp_path, ["wechsel", "c7a.xlarge"], start_type="c7a.xlarge")
    assert answer.returncode == 0, answer
    assert "typwechsel-unnoetig c7a.xlarge" in raw_of(raw)
    assert not [call for call in calls if call.startswith("aws_box") or "modify-instance-attribute" in call]


@needs_sh
def test_the_switch_without_capacity_leaves_the_box_stopped_and_falls_back_to_nothing(tmp_path: Path) -> None:
    """No silent fallback inside the matrix (D-28-04): its own exit, the box parked on its old type."""
    answer, raw, calls = a_stubbed_switch(
        tmp_path,
        ["wechsel", "c7a.8xlarge"],
        start_type="c7a.4xlarge",
        umgebung={"STUB_OHNE_KAPAZITAET": "c7a.8xlarge"},
    )
    assert answer.returncode == 55, answer
    text = raw_of(raw)
    assert "typwechsel-kapazitaet c7a.8xlarge" in text
    assert "TYPWECHSEL-FERTIG" not in text
    assert calls.count("aws_box start") == 1
    modifies = [call for call in calls if "modify-instance-attribute" in call]
    # The requested type and the way back to the old one, nothing else.
    assert len(modifies) == 2, modifies
    assert "Value=c7a.8xlarge" in modifies[0]
    assert "Value=c7a.4xlarge" in modifies[1]
    assert "typ-ist c7a.4xlarge" in text
    for other in ALLOWED:
        if other not in {"c7a.8xlarge", "c7a.4xlarge"}:
            assert not [call for call in calls if f"Value={other}" in call], other


@needs_sh
def test_the_switch_ends_with_53_when_a_failed_start_leaves_the_box_running(tmp_path: Path) -> None:
    answer, raw, calls = a_stubbed_switch(
        tmp_path,
        ["wechsel", "m7g.4xlarge"],
        umgebung={"STUB_OHNE_KAPAZITAET": "m7g.4xlarge", "STUB_ZUSTAND": "running"},
    )
    assert answer.returncode == 53, answer
    assert "zustand-abweichung gefordert stopped ist running" in raw_of(raw)
    assert len([call for call in calls if "modify-instance-attribute" in call]) == 1


@needs_sh
def test_the_switch_ends_with_53_when_the_type_read_back_differs(tmp_path: Path) -> None:
    answer, raw, _ = a_stubbed_switch(tmp_path, ["wechsel", "m7g.4xlarge"], umgebung={"STUB_KLEBT": "1"})
    assert answer.returncode == 53, answer
    text = raw_of(raw)
    assert "typ-abweichung gefordert m7g.4xlarge ist m7g.large" in text
    assert "TYPWECHSEL-FERTIG" not in text


@needs_sh
def test_the_switch_ends_with_53_when_the_box_does_not_run_after_the_start(tmp_path: Path) -> None:
    answer, raw, _ = a_stubbed_switch(tmp_path, ["wechsel", "m7g.4xlarge"], umgebung={"STUB_ZUSTAND": "pending"})
    assert answer.returncode == 53, answer
    assert "zustand-abweichung gefordert running ist pending" in raw_of(raw)


@needs_sh
def test_the_price_reads_the_public_card_for_every_type_it_is_given(tmp_path: Path) -> None:
    card = a_price_card({"c7a.xlarge": "0.2342600000", "c7a.8xlarge": "1.8740800000", "m7g.large": "0.0978000000"})
    answer, raw, calls = a_stubbed_switch(tmp_path, ["preis", "c7a.xlarge", "c7a.8xlarge"], card=card)
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "preis c7a.xlarge 0.2342600000" in text
    assert "preis c7a.8xlarge 1.8740800000" in text
    assert "preis-quelle 2026-09-25T17:45:21Z" in text
    assert "TYPWECHSEL-PREIS-FERTIG" in text
    fetches = [call for call in calls if call.startswith("curl ")]
    assert len(fetches) == 1, calls
    assert "b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current" in fetches[0]
    # No account call for a public card.
    assert not [call for call in calls if call.startswith("--region")], calls


@needs_sh
def test_the_price_ends_with_1_when_a_type_is_missing_from_the_card(tmp_path: Path) -> None:
    card = a_price_card({"c7a.xlarge": "0.2342600000"})
    answer, raw, _ = a_stubbed_switch(tmp_path, ["preis", "c7a.xlarge", "c7a.4xlarge"], card=card)
    assert answer.returncode == 1, answer
    text = raw_of(raw)
    assert "preis c7a.xlarge 0.2342600000" in text
    assert "preis c7a.4xlarge unlesbar" in text
    assert "TYPWECHSEL-PREIS-FERTIG" not in text


@needs_sh
def test_the_price_ends_with_1_when_the_card_cannot_be_fetched(tmp_path: Path) -> None:
    answer, raw, _ = a_stubbed_switch(tmp_path, ["preis", "c7a.xlarge"])
    assert answer.returncode == 1, answer
    assert "preis-karte unlesbar" in raw_of(raw)


@needs_sh
def test_the_quota_reads_the_vcpu_quota_and_the_zone_offering_without_identifiers(tmp_path: Path) -> None:
    answer, raw, calls = a_stubbed_switch(tmp_path, ["quota", "c7a.8xlarge"])
    assert answer.returncode == 0, answer
    text = raw_of(raw)
    assert "quota-vcpu-standard 256.0" in text
    assert "angebot c7a.8xlarge eu-central-1a eu-central-1c" in text
    assert STUB_INSTANCE not in text
    quota = next(call for call in calls if "get-service-quota" in call)
    assert "--service-code ec2" in quota
    assert "--quota-code L-1216C47A" in quota
    offering = next(call for call in calls if "describe-instance-type-offerings" in call)
    assert "--location-type availability-zone" in offering
    assert "Name=instance-type,Values=c7a.8xlarge" in offering
    assert "--region eu-central-1" in offering
    assert not [call for call in calls if call.startswith("aws_box")]


@needs_sh
@pytest.mark.parametrize(
    "step",
    [["vorpruefung"], ["wechsel", "m7g.4xlarge"], ["preis", "m7g.large"], ["quota", "m7g.large"]],
    ids=str,
)
def test_the_type_switch_never_prints_a_credential(tmp_path: Path, step: list[str]) -> None:
    card = a_price_card({"m7g.large": "0.0978000000"})
    answer, raw, calls = a_stubbed_switch(tmp_path, step, card=card)
    for sentinel in (ACCESS_STAND_IN, SIGNING_STAND_IN):
        assert sentinel not in answer.stdout
        assert sentinel not in answer.stderr
        assert sentinel not in raw_of(raw)
        assert not [call for call in calls if sentinel in call]


def test_the_type_switch_goes_through_aws_box_and_keeps_its_state_outside_the_tree() -> None:
    code = code_of(TYPE_SWITCH.read_text(encoding="utf-8"))
    assert 'AWS_BOX="${AWS_BOX:-$REPO/scripts/ops/aws_box.sh}"' in code
    assert 'sh "$AWS_BOX" "$@" >&2' in code
    assert 'STATE_DIR="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"' in code
    for forbidden in ("stop-instances", "start-instances", "terminate-instances", "run-instances", "pricing get"):
        assert forbidden not in code, forbidden
    assert {"exit 52", "exit 53", "exit 54", "exit 55"} <= aborts_in(code)
