"""Every file under docs/, held against the secret rule of this project.

The occasion is finding M-02 of the phase 15 audit, and it is worth quoting
because it is the whole reason this module exists: **the secret rule is nowhere
in this project run as a gate, it is run per plan as a search over the files
that the plan itself names.** Whoever does not name a file does not check it.
The audit ran the same counter check a second time over the whole of ``docs/``
instead of over the eighty files of that phase, and found in eighteen files
fifty eight values of the kind the rule forbids, none of them from phase 15 and
all of them from the phases five to twelve.

The reach of this module is therefore not a list of file names. It is the
directory ``docs/``, recursively, every file, and the file that arrives
tomorrow is checked on the day it arrives without anybody adding it here.

**What it looks for.** Eight families out of section 3 of the audit, which
recognise a secret by its context or by a shape rather than by one form, plus
the pattern that the plans 15-09 to 15-14 ran as their own check. Every family
is a named constant with a comment that says what it looks for and what it
recognises it by.

**Why the samples are assembled from halves.** A gate that carries the thing it
keeps out is the next finding. The prefixes of the access keys and the key words
of the sixth family are therefore put together out of pieces, exactly as
``test_store_metadata.py`` does it with its blocked term and its dashes. The
trial run is made here rather than described: one case below runs this gate over
this file, and it comes back empty.

**Why there are self tests.** Without them a gate whose body was deleted can
report zero findings over zero files and look healthy, and a gate over a
directory that moved is green without saying anything. Both holes are closed,
the first by a clean and a mutated sample per family, the second by the floor
under the number of files.

**Why the exception list carries reasons.** A gate with a named exception list
is more honest than a rule without a gate; an exception list without reasons is
a silent switch off. Every entry therefore names its own reason in its own
sentence, and a case below holds the reasons against a minimum length.

**Why the reasons are English.** They are string literals in a Python module,
that is code, and the rule of this project puts real umlauts in German prose and
never in code. The names of the families are German and without umlauts,
because the plan and the audit name them that way, and a gate and its finding
report should speak one vocabulary.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# The reach of this gate. A directory and not a list of names: a list covers the
# files somebody remembered to add to it, and the next measurement brings a
# directory rather than an entry.
DOCS_DIR = REPO_ROOT / "docs"

# The floor under the number of files. Counted on 21.09.2026: 389 files under
# docs/ pass the two skip rules below. The floor sits under that number rather
# than on it, because a plan that adds files must not have to come here, while a
# gate that looks at a directory which was moved or emptied has to go red. A
# floor is the only thing that tells the two apart.
DOCS_FILES_FLOOR = 380

# Skipped by their suffix, and out in the open rather than inside a silent
# try/except: these are compiled or compressed bytes. Scanning them would turn
# their entropy into a finding per file and would say nothing about a secret,
# and a gate whose result is noise gets switched off within a week.
BINARY_SUFFIXES = frozenset(
    {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tar", ".woff2"}
)

# Skipped by their directory or file name, for one reason each: __pycache__ is
# the byte code of a script that is itself checked, and a name that starts with
# a dot is the marker of a tool and not an artefact this repository publishes.
# Both are outside the tree git tracks here, which is what makes the floor above
# a stable number rather than a property of the last test run.
SKIPPED_DIRECTORY_NAMES = frozenset({"__pycache__"})


# -- the nine shapes of a secret -----------------------------------------------

# 1. A private key of the PEM form. Recognised by its header line, which names
#    the kind of key between BEGIN and PRIVATE KEY. The body is not required:
#    the header alone in a public file is already the finding worth reading.
PEM_PRIVATE_KEY = re.compile(r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----")

# 2. SSH key material. Recognised by the type word of the line followed by the
#    base64 body, which always opens with AAAA because the first field of the
#    blob is the length of the type word. The type word on its own is prose.
SSH_KEY_MATERIAL = re.compile(r"ssh-(?:rsa|ed25519|dss)\s+AAAA[0-9A-Za-z+/=]{20,}")

# The eight prefixes an access key of the cloud provider can carry, each put
# together out of two halves. These are the pieces this file may not carry
# whole: a prefix without its tail is already half a credential, which is not
# true of the resource prefixes below, where snap or vpc without a hex tail is
# an ordinary word.
ACCESS_KEY_PREFIXES = (
    "AK" + "IA",
    "AS" + "IA",
    "AI" + "DA",
    "AR" + "OA",
    "AG" + "PA",
    "AN" + "PA",
    "AN" + "VA",
    "AP" + "KA",
)

# 3. An access key of the cloud provider. Recognised by one of the eight
#    prefixes with twelve or more following characters of the alphabet those
#    keys use. Twelve is the number of the audit, and it is under the real
#    length on purpose, so that a truncated key is still a finding.
AWS_ACCESS_KEY = re.compile(r"\b(?:" + "|".join(ACCESS_KEY_PREFIXES) + r")[0-9A-Z]{12,}\b")

# The resource prefixes of the counter check, deliberately the ones the pattern
# of the implementation does not know. The two it does know, the instance and
# the volume, belong to family nine, so that a finding says which of the two
# searches found it.
RESOURCE_PREFIXES = ("snap", "ami", "subnet", "sg", "eni", "acl", "rtb", "igw", "vpc", "pcx", "nat")

# 4. A resource identifier of the cloud provider. Recognised by one of those
#    prefixes, a hyphen and eight or more hex digits, which is the short form;
#    the long form is seventeen digits and is covered by the same expression.
AWS_RESOURCE_ID = re.compile(r"\b(?:" + "|".join(RESOURCE_PREFIXES) + r")-[0-9a-f]{8,}\b")

# 5. The machine name of a box. Three forms: the public name the provider hands
#    out, the internal name built out of the private address, and the internal
#    domain. Each of the three names one machine of one account and belongs in
#    no public file.
BOX_HOSTNAME = re.compile(
    r"(?:ec2-[0-9-]+\.[0-9a-z.-]*compute\.amazonaws\.com"
    r"|\bip-\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3}\b"
    r"|\b[0-9a-z-]+\.compute\.internal\b)"
)

# The key words of the sixth family, put together out of halves for the reason
# given in the module docstring. The order is the order of the audit; the longer
# word behind the shorter one costs nothing here, because the expression
# backtracks into it.
SECRET_KEY_WORDS = (
    "pass",
    "pass" + "wort",
    "pass" + "word",
    "sec" + "ret",
    "to" + "ken",
    "api" + "_key",
    "creden" + "tial",
    "p" + "wd",
)

# 6. A key word immediately in front of a colon or an equals sign and a value.
#    This is the family that recognises a secret by its context rather than by
#    its shape, and it is the reason a counter check is worth running: a
#    password that looks like a word is invisible to every other family here.
KEYWORD_WITH_VALUE = re.compile(r"(?i)\b(?:" + "|".join(SECRET_KEY_WORDS) + r")\s*[:=]\s*(\S+)")

# A value that opens with a dollar sign is a shell substitution or a variable
# reference. It names where the value comes from and never carries it, so it is
# no finding. A narrowing of the family and therefore a named rule with a
# reason, rather than a row of entries on the exception list.
VALUE_IS_A_REFERENCE = re.compile(r"\A[$]")

# 7. An IPv6 address, as four to eight groups of hex digits with colons. Four is
#    the floor of the audit, and it is what keeps a clock time out: hours,
#    minutes and seconds are three groups.
IPV6_ADDRESS = re.compile(r"(?<![0-9A-Za-z:])(?:[0-9A-Fa-f]{1,4}:){3,7}[0-9A-Fa-f]{1,4}(?![0-9A-Za-z:])")

# 8. A run of base64 characters from length forty. The catch all of the eight:
#    it recognises neither a context nor a form but the density of an encoded
#    blob, which is what a key, a session and a dumped token have in common.
BASE64_BLOCK = re.compile(r"(?<![0-9A-Za-z+/])[0-9A-Za-z+/]{40,}={0,2}")

# The first of the two false alarms of that catch all, both of them named by the
# audit itself and both narrowed here rather than carried as thirty entries on
# the exception list. A run of nothing but hex digits, or nothing but digits, is
# a checksum or an object name: thirty six of the thirty seven hits of the audit
# were sha256 sums.
RUN_IS_A_CHECKSUM = re.compile(r"(?i)\A(?:[0-9a-f]+|[0-9]+)\Z")


def run_is_a_path(run: str) -> bool:
    """Whether a run of base64 characters is a path rather than a block.

    The second false alarm. A run that slashes cut into pieces, none of which
    reaches forty, is a path: the one remaining hit of the audit was a path, and
    the slashes of that path are the only reason the expression picked it up at
    all. What this lets through is a real base64 secret whose longest slash free
    piece stays under forty characters; the shapes this project can actually
    leak are covered by families one and two, which do not care about slashes.
    """
    return "/" in run and all(len(piece) < 40 for piece in run.split("/"))


# 9. The pattern of the implementation, out of the plans 15-09 to 15-14: the
#    instance and the volume identifier, and the form of an IPv4 address. It
#    runs here next to the eight families and not instead of them, because a
#    counter check with the pattern of the implementation is no counter check.
IMPLEMENTATION_PATTERN = re.compile(
    r"\b(?:i-[0-9a-f]{8,}|vol-[0-9a-f]{8,}|(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}))\b"
)


def address_names_a_machine(groups: tuple[str | None, ...]) -> bool:
    """Whether the four groups of an IPv4 match name a machine on the internet.

    Two exclusions, both of them named by the audit. A group over 255 or with a
    leading zero is no address but a number written with the German thousands
    separator, which is how a byte count reaches four groups. And the
    unspecified address, the loopback, the three private ranges, the link local
    range, the carrier range and everything from 224 upwards name no machine of
    this account: the bridge address of the docker network and the bind address
    were three of the nine hits the audit explained.
    """
    pieces = [group for group in groups if group is not None]
    if len(pieces) != 4:
        return False
    if any(len(piece) > 1 and piece.startswith("0") for piece in pieces):
        return False
    numbers = [int(piece) for piece in pieces]
    if any(number > 255 for number in numbers):
        return False
    first, second = numbers[0], numbers[1]
    if first in (0, 10, 127) or first >= 224:
        return False
    if first == 172 and 16 <= second <= 31:
        return False
    if first == 192 and second == 168:
        return False
    if first == 169 and second == 254:
        return False
    return not (first == 100 and 64 <= second <= 127)


# The names of the families, in the order above. A finding names one of these,
# and so does every key of the exception list.
SECRET_FAMILIES = (
    "pem-privatschluessel",
    "ssh-schluesselmaterial",
    "aws-zugangskennung",
    "aws-ressourcenkennung",
    "rechnername-der-box",
    "schluesselwort-mit-wert",
    "ipv6-adresse",
    "base64-block-ab-40",
    "muster-der-umsetzung",
)
FAMILIES = SECRET_FAMILIES


# -- the staged samples of the self tests --------------------------------------

# One clean and one mutated sample per family. Without them a gate whose body
# was deleted reports zero findings over zero files and looks healthy, which is
# the second half of the same hole the floor above closes.
#
# Every sample is put together out of pieces, for the reason the module
# docstring gives: this file runs over itself in a case below, and a sample
# written whole would make that case red and this gate a carrier.
CLEAN_SAMPLES: dict[str, str] = {
    "pem-privatschluessel": "the key file opens with a header line, and this sentence is not that line",
    "ssh-schluesselmaterial": "ssh-" + "ed25519 is the type word of the line, and the body does not follow",
    "aws-zugangskennung": "AK" + "IA" + "SHORT is a prefix with a tail too short to be a key",
    "aws-ressourcenkennung": "snap" + "-0a1b2c3 has seven hex digits, one under the floor",
    "rechnername-der-box": "the box carries a name of the provider, and this sentence is not it",
    "schluesselwort-mit-wert": "a " + "to" + "ken is named here and no value follows the word",
    "ipv6-adresse": "ab" + ":cd:ef are three groups, one under the floor of four",
    "base64-block-ab-40": "0123456789abcdef" * 4,
    "muster-der-umsetzung": "i-" + "0a1b2c3 is too short, and " + "10.0.0.1" + " names no machine",
}

MUTATED_SAMPLES: dict[str, str] = {
    # mutated: the header line whole, which is the one line that matters
    "pem-privatschluessel": "-----" + "BEGIN OPENSSH PRIVATE KEY" + "-----",
    # mutated: the type word with the base64 body behind it
    "ssh-schluesselmaterial": "ssh-" + "ed25519 " + "AAAA" + "C3NzaC1lZDI1NTE5" + "ZZZZ",
    # mutated: the prefix with sixteen following characters
    "aws-zugangskennung": "AK" + "IA" + "EXAMPLEKEYVALUE1",
    # mutated: the prefix with a hex tail over the floor
    "aws-ressourcenkennung": "snap" + "-0a1b2c3d4e5f60718",
    # mutated: the public machine name of the provider, whole
    "rechnername-der-box": "ec2-" + "198-51-100-7.eu-central-1." + "compute.amazonaws.com",
    # mutated: the key word with an equals sign and a value behind it
    "schluesselwort-mit-wert": "to" + "ken" + "=" + "abcd1234",
    # mutated: eight groups instead of three
    "ipv6-adresse": "2001" + ":0db8:0000:0042" + ":0000:8a2e:0370:7334",
    # mutated: forty two characters that are not all hex and carry no slash
    "base64-block-ab-40": "Findling" + "Z" * 32 + "+g==",
    # mutated: the instance identifier with a hex tail over the floor
    "muster-der-umsetzung": "i-" + "0a1b2c3d4e5f60718",
}


# -- the exception list --------------------------------------------------------

# Every finding this gate sees today, by path and family, with its own reason in
# its own sentence. No entry quotes a value: a gate that carried the values it
# keeps out would be the nineteenth file that carries them, and the audit
# refused to be the nineteenth for the same reason.
#
# **This list shrinks in plan 16-05.** What leaves it are the documents that can
# still be edited: the audit reports, the guides, the READMEs of the
# measurements and the performance document. What stays are two kinds of entry.
# The raw data and the scripts of driven approaches stay, because a raw file
# that is edited after the run stops being evidence of that run. And the one
# publicly published image identifier I-01 stays, because it is meant to be
# public: it names the image a reader can start for themselves.
AUSNAHMEN: dict[tuple[str, str], str] = {
    # -- family 1, the header line of a private key
    ("runbook-messbox.md", "pem-privatschluessel"): (
        "The runbook says in prose that the key file of the box begins with this header line, "
        "and the line without its body is an instruction and no key."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/03-aufbau.txt", "pem-privatschluessel"): (
        "The build record of the driven v1.2 approach quotes the first line of the key file it created, "
        "and a raw file of a driven run is not edited afterwards."
    ),
    # -- family 4, the resource identifiers the pattern of the implementation does not know
    ("audits/2026-09-phase-15/README.md", "aws-ressourcenkennung"): (
        "The audit report names the publicly published image identifier I-01, which is meant to be readable "
        "because it lets a reader start the same image."
    ),
    ("measurements/2026-09-v12-messung/README.md", "aws-ressourcenkennung"): (
        "The report of the driven v1.2 approach names the snapshot it left behind, "
        "and the resource behind it was read back as torn down on 21.09.2026."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt", "aws-ressourcenkennung"): (
        "A raw file of reading probes of the driven v1.2 approach, which is evidence of what the account "
        "answered at that hour and is therefore not edited afterwards."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/02-vorbedingungen.txt", "aws-ressourcenkennung"): (
        "The preconditions record of the driven v1.2 approach, which names the resources it found before "
        "the run and is not edited afterwards."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/03-aufbau.txt", "aws-ressourcenkennung"): (
        "The build record of the driven v1.2 approach, which names the resources it created "
        "and is not edited afterwards."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/07-snapshot-und-abbau.txt", "aws-ressourcenkennung"): (
        "The teardown record of the driven v1.2 approach, whose whole point is naming what was released, "
        "and it is not edited afterwards."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/93-kosten-und-verbleib.txt", "aws-ressourcenkennung"): (
        "The cost and remainder record of the driven v1.2 approach, which names what stayed behind "
        "and is not edited afterwards."
    ),
    ("measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt", "aws-ressourcenkennung"): (
        "The teardown record of the driven tool fix approach, whose whole point is naming what was released, "
        "and it is not edited afterwards."
    ),
    ("performance.md", "aws-ressourcenkennung"): (
        "The performance document names the snapshot of the corpus in its provenance notes, "
        "and it is a document that plan 16-05 can still edit."
    ),
    ("runbook-messbox.md", "aws-ressourcenkennung"): (
        "The runbook names the resources of an approach in its instructions, "
        "and it is a document that plan 16-05 can still edit."
    ),
    # -- family 6, a key word in front of a value
    ("audits/2026-09-phase-10/README.md", "schluesselwort-mit-wert"): (
        "The phase 10 audit quotes an identifier of the source it judged, and the value behind it is a call "
        "and not a password."
    ),
    ("audits/2026-09-phase-15/README.md", "schluesselwort-mit-wert"): (
        "The phase 15 audit quotes the invented sample password of the gate that finds passwords, "
        "which is the same quotation this family exists to make visible."
    ),
    ("measurements/2026-09-05-welle0-arm64/README.md", "schluesselwort-mit-wert"): (
        "The report of the wave zero comparison quotes a type annotation of the code it measured, "
        "and a type is no value."
    ),
    ("measurements/2026-09-v12-messung/skripte/94b-grundlast-rueckkehr.sh", "schluesselwort-mit-wert"): (
        "The driven successor that measures the return to the base load, which reads its password out of a "
        "file and is frozen under DRIVEN_V12_FASSUNGEN."
    ),
    ("measurements/2026-09-v12-messung/skripte/95b-wiederaufwaermen.sh", "schluesselwort-mit-wert"): (
        "The driven successor that warms the container up again, which reads its password out of a file and "
        "is frozen under DRIVEN_V12_FASSUNGEN."
    ),
    ("measurements/2026-09-v12-messung/skripte/96d-statusbeobachter.py", "schluesselwort-mit-wert"): (
        "A driven script of the v1.2 approach, whose identifiers carry these names and whose values are "
        "function calls, frozen under DRIVEN_V12_FASSUNGEN."
    ),
    ("measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh", "schluesselwort-mit-wert"): (
        "The driven successor that measures filters and sorting, which reads its password out of a file "
        "rather than out of the environment, and is frozen under DRIVEN_V12_FASSUNGEN."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/skripte/96d-statusbeobachter.py", "schluesselwort-mit-wert"): (
        "The driven predecessor of the status observer, whose identifiers carry these names and whose values "
        "are function calls, and a driven script is not edited afterwards."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/skripte/99b-runden.sh", "schluesselwort-mit-wert"): (
        "The driven round script of the comparison approach, which hands a request token to a header "
        "and is not edited afterwards."
    ),
    ("measurements/2026-09-werkzeugfixe/skripte/72-fremdbestand.py", "schluesselwort-mit-wert"): (
        "A driven script of the tool fix approach, whose parameter carries this name and whose value is "
        "a type, and it is not edited afterwards."
    ),
    # -- family 8, a run of base64 characters from length forty
    ("german-analyzer.md", "base64-block-ab-40"): (
        "The analyser document quotes the long German compound this project tests its splitting with, "
        "and one German word is not an encoded block."
    ),
    ("measurements/2026-09-05-modellqualitaet/README.md", "base64-block-ab-40"): (
        "The model quality report quotes the address of the model file at the model host, "
        "whose revision part runs past forty characters."
    ),
    # -- family 9, the pattern of the implementation
    ("install-check.md", "muster-der-umsetzung"): (
        "The installation guide names version numbers of four groups, which the form of an address cannot "
        "be told apart from, and it is a document that plan 16-05 can still edit."
    ),
    ("measurements/2026-09-03-trockenlauf-cpx22/README.md", "muster-der-umsetzung"): (
        "The dry run report names a kernel version of four groups, which the form of an address cannot be "
        "told apart from."
    ),
    ("measurements/2026-09-04-grundlast-m7g/README.md", "muster-der-umsetzung"): (
        "The base load report names a kernel version of four groups, which the form of an address cannot be "
        "told apart from."
    ),
    ("measurements/2026-09-05-welle0-arm64/README.md", "muster-der-umsetzung"): (
        "The wave zero report names a kernel version of four groups, which the form of an address cannot be "
        "told apart from."
    ),
    ("measurements/2026-09-05-welle0-arm64/raw/amd64-machine.txt", "muster-der-umsetzung"): (
        "A raw machine record of the wave zero comparison, which holds the kernel version of the runner "
        "and is not edited afterwards."
    ),
    ("measurements/2026-09-nachmessung-m7g/README.md", "muster-der-umsetzung"): (
        "The remeasurement report names the public addresses of the box of 10.09.2026, which were handed out "
        "for the hours of that run and long since to somebody else."
    ),
    ("measurements/2026-09-nachmessung-m7g/rohdaten/80-arm64-vorbereiten.txt", "muster-der-umsetzung"): (
        "A raw file of the arm64 preparation, which holds a version of four groups and is not edited afterwards."
    ),
    ("measurements/2026-09-nachmessung-m7g/rohdaten/81-arm64-lauf.txt", "muster-der-umsetzung"): (
        "A raw file of the arm64 run, which holds a version of four groups and is not edited afterwards."
    ),
    ("measurements/2026-09-seitenbudget/README.md", "muster-der-umsetzung"): (
        "The page budget report names a version of four groups, which the form of an address cannot be told apart from."
    ),
    ("measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt", "muster-der-umsetzung"): (
        "A raw file of reading probes of the driven v1.2 approach, which holds the volume identifier the "
        "account answered with and is not edited afterwards."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md", "muster-der-umsetzung"): (
        "The one page verdict of the comparison run names the instance it was measured on, and the machine "
        "behind it was read back as torn down on 11.09.2026."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/README.md", "muster-der-umsetzung"): (
        "The report of the comparison run names the instance and the two volumes in its table of conditions, "
        "all three of them read back as torn down."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/rohdaten/89-anfahrt.txt", "muster-der-umsetzung"): (
        "The approach record of the comparison run, which is the file that documents how the box was reached "
        "and is not edited afterwards."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/rohdaten/93-kosten-und-verbleib.txt", "muster-der-umsetzung"): (
        "The cost and remainder record of the comparison run, which names the address the cost was booked "
        "against and is not edited afterwards."
    ),
    ("measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md", "muster-der-umsetzung"): (
        "The run plan that was driven with the comparison approach and carries the address it was driven "
        "against, frozen together with the scripts beside it."
    ),
    ("measurements/2026-09-werkzeugfixe/README.md", "muster-der-umsetzung"): (
        "The report of the tool fix approach names the public address of its box, which was handed out for "
        "the hours of that run and long since to somebody else."
    ),
    ("measurements/2026-09-werkzeugfixe/rohdaten/06-kosten.txt", "muster-der-umsetzung"): (
        "The cost record of the tool fix approach, which holds the instance and volume identifiers the "
        "status command printed and is not edited afterwards."
    ),
    ("measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt", "muster-der-umsetzung"): (
        "The teardown record of the tool fix approach, which holds the addresses the account answered with "
        "and is not edited afterwards."
    ),
    ("performance.md", "muster-der-umsetzung"): (
        "The performance document names public addresses of earlier boxes in its provenance notes, "
        "and it is a document that plan 16-05 can still edit."
    ),
}

# The shortest reason that can still be a reason. A sentence under this length
# is a label, and a label is what an exception list looks like shortly before it
# becomes a silent switch off.
REASON_MINIMUM_LENGTH = 20


# -- the scanners, none of which ever raises -----------------------------------


def docs_files() -> list[Path]:
    """Every file under docs/ this gate judges, sorted."""
    return sorted(
        path
        for path in DOCS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() not in BINARY_SUFFIXES
        and not any(
            part in SKIPPED_DIRECTORY_NAMES or part.startswith(".") for part in path.relative_to(DOCS_DIR).parts
        )
    )


def text_of(path: Path) -> str:
    """The text of a file, with undecodable bytes replaced rather than raised on.

    A file this gate cannot read is a blind spot and not a reason to stop, so
    the bytes come in and the decoder replaces what it cannot name. The binary
    suffixes are already out by then, so what arrives here is text with at worst
    a wrong encoding.
    """
    try:
        return path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return ""


def matches_of(family: str, text: str) -> int:
    """How often one family finds something in a text. Never raises."""
    if family == "pem-privatschluessel":
        return len(PEM_PRIVATE_KEY.findall(text))
    if family == "ssh-schluesselmaterial":
        return len(SSH_KEY_MATERIAL.findall(text))
    if family == "aws-zugangskennung":
        return len(AWS_ACCESS_KEY.findall(text))
    if family == "aws-ressourcenkennung":
        return len(AWS_RESOURCE_ID.findall(text))
    if family == "rechnername-der-box":
        return len(BOX_HOSTNAME.findall(text))
    if family == "schluesselwort-mit-wert":
        return sum(1 for found in KEYWORD_WITH_VALUE.finditer(text) if not VALUE_IS_A_REFERENCE.match(found.group(1)))
    if family == "ipv6-adresse":
        return len(IPV6_ADDRESS.findall(text))
    if family == "base64-block-ab-40":
        return sum(
            1
            for found in BASE64_BLOCK.finditer(text)
            if not RUN_IS_A_CHECKSUM.match(found.group(0)) and not run_is_a_path(found.group(0))
        )
    if family == "muster-der-umsetzung":
        return sum(
            1
            for found in IMPLEMENTATION_PATTERN.finditer(text)
            if found.group(1) is None or address_names_a_machine(found.groups())
        )
    return 0


def scan_secrets(name: str, text: str) -> list[str]:
    """Every family that finds something in this text, as one finding each.

    Returns a list and never raises, which is the house form of every text gate
    here: a scanner that throws on the first odd file turns a gate over four
    hundred files into a gate over the files before the odd one. The finding
    names the file and the family and never the value.
    """
    return [f"{name}: {family}" for family in FAMILIES if matches_of(family, text)]


def findings_of_family(family: str) -> list[str]:
    """Every file under docs/ in which one family finds something, sorted."""
    return [path.relative_to(DOCS_DIR).as_posix() for path in docs_files() if matches_of(family, text_of(path))]


# -- the anti vacuity clause ---------------------------------------------------


def test_the_gate_sees_at_least_the_floor_of_files() -> None:
    # Without this case a gate over a directory that was moved, renamed or
    # emptied reports zero findings over zero files and looks perfect. The floor
    # is the only thing that tells an empty result apart from a clean one.
    assert DOCS_DIR.is_dir()
    assert len(docs_files()) >= DOCS_FILES_FLOOR


# -- the real tree, one case per family ----------------------------------------


@pytest.mark.parametrize("family", FAMILIES)
def test_no_file_under_docs_carries_a_finding_outside_the_exception_list(family: str) -> None:
    unexcused = [name for name in findings_of_family(family) if (name, family) not in AUSNAHMEN]

    assert unexcused == []


@pytest.mark.parametrize("family", FAMILIES)
def test_every_exception_of_a_family_is_still_earning_its_place(family: str) -> None:
    # The other direction, and the reason the list can shrink at all: an entry
    # whose finding is gone is a line that says a file is dirty when it is
    # clean. Plan 16-05 cleans documents, and this case is what makes it take
    # their entries with it.
    found = set(findings_of_family(family))
    stale = sorted(name for (name, entry_family) in AUSNAHMEN if entry_family == family and name not in found)

    assert stale == []


def test_every_exception_names_a_file_that_exists() -> None:
    missing = sorted({name for name, _ in AUSNAHMEN if not (DOCS_DIR / name).is_file()})

    assert missing == []


def test_every_exception_carries_a_reason_of_its_own() -> None:
    # Two claims in one case, because they are the same claim: a reason under
    # the minimum length is a label, and a reason that stands twice is a
    # collective sentence and not a reason for this entry.
    reasons = list(AUSNAHMEN.values())
    too_short = sorted(
        f"{name} / {family}" for (name, family), reason in AUSNAHMEN.items() if len(reason) < REASON_MINIMUM_LENGTH
    )
    reused = sorted(reason for reason in set(reasons) if reasons.count(reason) > 1)

    assert too_short == []
    assert reused == []


def test_the_exception_list_quotes_no_value_it_exists_to_keep_out() -> None:
    # An exception list that carried the values would be the nineteenth file
    # that carries them, which is the sentence the audit wrote about itself.
    listed = "\n".join(f"{name} {family} {reason}" for (name, family), reason in AUSNAHMEN.items())

    assert scan_secrets("AUSNAHMEN", listed) == []


def test_this_gate_passes_its_own_rule() -> None:
    # The trial run the module docstring announces. A gate that carries the
    # thing it keeps out is the next finding, and the only way to know is to
    # point it at itself.
    assert scan_secrets(Path(__file__).name, text_of(Path(__file__))) == []


# -- the self tests, one clean and one mutated sample per family ---------------


def test_every_family_carries_a_clean_and_a_mutated_sample() -> None:
    # The case that keeps the two dictionaries above honest when a tenth family
    # arrives: a family without samples is a family whose body nobody checks.
    assert sorted(CLEAN_SAMPLES) == sorted(FAMILIES)
    assert sorted(MUTATED_SAMPLES) == sorted(FAMILIES)


@pytest.mark.parametrize("family", FAMILIES)
def test_the_clean_sample_of_a_family_produces_no_finding(family: str) -> None:
    # Held against every family and not only against its own, because a pattern
    # that fires on the clean sample of a neighbour is a pattern that will fire
    # on four hundred files of ordinary prose.
    assert scan_secrets(f"clean/{family}", CLEAN_SAMPLES[family]) == []


@pytest.mark.parametrize("family", FAMILIES)
def test_the_mutated_sample_of_a_family_produces_exactly_one_finding(family: str) -> None:
    # The other half of the self test. Exactly one, and by its own family: a
    # mutated sample that two families report says nothing about either of them.
    assert scan_secrets(f"mutated/{family}", MUTATED_SAMPLES[family]) == [f"mutated/{family}: {family}"]
    assert matches_of(family, MUTATED_SAMPLES[family]) == 1


def test_a_checksum_and_a_path_are_no_base64_block() -> None:
    # The two narrowings of the catch all, each with its own case, because both
    # were written from the explanation of a hit of the audit and an explanation
    # that nothing checks is a comment.
    checksum = "0123456789abcdef" * 4
    path = "/mnt/" + "x" * 30 + "/data/" + "y" * 30

    assert matches_of("base64-block-ab-40", checksum) == 0
    assert matches_of("base64-block-ab-40", path) == 0
    assert run_is_a_path(path)


def test_an_address_that_names_no_machine_is_no_finding() -> None:
    # The same for the ninth family. The bind address, the loopback, the bridge
    # address of the docker network and a byte count with thousands separators
    # were four of the nine hits the audit had to explain in prose.
    quiet = "0.0.0.0 127.0.0.1 " + "172.18.0.5 " + "192.168.1.1 " + "2.147.483.648"
    # In two pieces like every sample here, because whole it would be the one
    # shape this module may not carry, and the case below points this gate at
    # this file.
    loud = "203." + "0.113.7"

    assert matches_of("muster-der-umsetzung", quiet) == 0
    assert matches_of("muster-der-umsetzung", loud) == 1
