"""The house rules of the measurement scripts, as a gate instead of a review note.

docs/measurements holds the scripts of every measurement this project has run,
next to the raw data they produced. They are copied onto a rented Linux box and
started there, which puts them under the same promises as the operating tools of
scripts/ops, and test_ops_scripts.py holds those promises only for that one
directory.

The part of this file that exists first is the recipe of the tree hash. Both
predecessor reports claim that the image and the working tree are the same state,
and in both the raw data of that step is empty: 40-abbild.log line 52 carries the
section title "Baumhash im Abbild" and nothing under it, and 61-wechsel.txt line
4 carries its English counterpart and nothing under it. The cause in 40-abbild.sh
is a docker run without -i, so the python in the image got no standard input and
read EOF at once. The answer of plan 10-01 is a recipe in a file that is called
with arguments, and these assertions are what keeps that recipe from drifting:
the two figures of this commit are written down, and a hash over nothing is a
failure rather than a result.

The rest of this file has two scopes of different width, and the difference is
the point rather than an oversight. Wide, over every .py and .sh under
docs/measurements/**/skripte/: no carriage return and no dash. Both hold for the
whole stock since plan 10-01 renormalised five files and added the checkout rule
that keeps them normalised, so the wide scope is a statement about the tree and
not a wager on it.

Narrow, over the run directories written under these rules: a shebang on the
first line, no path of one machine, and no password on a command line. It is
narrow because 45-suchlast.py of the semantic run puts "/home/ubuntu/work" into
sys.path and imports drillhelfer from it, drillhelfer does not live in this
repository, and that file is history with its raw data lying next to it. A gate
that demanded it be rewritten would blur the origin of those raw data to buy
nothing, so the three promises that only a new script can keep are asked of the
new scripts. Two directories are new in that sense today, and the second one
joined in plan 11-03: the successor fassung of the language case script lives in
a run directory of its own, and it would have carried none of the three
promises if the narrow scope had stayed a single directory.

The youngest part of this file is the watchman over the DRIVEN fassung of that
script. Scripts under docs/measurements/<lauf>/skripte/ are the fassungen that
really ran, and their raw data lie next to them; a script that is corrected
afterwards makes every figure beside it unsupported. That rule was a sentence in
a head comment until plan 11-03 turned it into a digest.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS_DIR = REPO_ROOT / "docs" / "measurements"
RUN_DIR = MEASUREMENTS_DIR / "2026-09-vergleichsmessung-m7g" / "skripte"
FIX_RUN_DIR = MEASUREMENTS_DIR / "2026-09-werkzeugfixe" / "skripte"
V12_RUN_DIR = MEASUREMENTS_DIR / "2026-09-v12-messung" / "skripte"
# The run directory of the two successor fassungen of A1, the acceptance of
# 21.09.2026. It holds no raw data and never will: neither of its files ran.
SUCCESSOR_RUN_DIR = MEASUREMENTS_DIR / "2026-09-nachfolgefassungen" / "skripte"
TREE_HASH = RUN_DIR / "40b-baumhash.py"
TREE_HASH_PROOF = RUN_DIR / "40b-baumhash.sh"
OPS_GATE = Path(__file__).resolve().parent / "test_ops_scripts.py"

# The directories the narrow scope covers. Written down as a tuple rather
# than globbed, because widening it is a decision and not a side effect of the
# next directory somebody creates: the semantic run of 05.09. must stay outside
# it, and the reason is in the docstring above.
#
# Three since plan 12-04, and the third one is such a decision rather than a
# consequence of its existence: the run directory of v1.2 is written from
# scratch under these rules, so every one of the three promises below can reach
# it. Its first file is the stock probe, which measures inside the container
# and therefore carries neither a route nor a password to begin with.
#
# Four since plan 16-03, and the fourth is the same kind of decision. The run
# directory of the successor fassungen of A1 holds 92c-wechsel.sh and
# 99d-filter-sortierung.sh, and the reason it belongs inside the narrow scope
# is 99d itself: its whole subject is where a password comes from, so the
# promise that no password stands on a command line has to reach it. The other
# two promises, no machine shape outside a comment and no carriage return,
# reach it for the same reason they reach the other three.
NARROW_SCOPE_DIRS = (RUN_DIR, FIX_RUN_DIR, V12_RUN_DIR, SUCCESSOR_RUN_DIR)

# The driven fassung of the language cases and its successor. The first one is
# evidence and must not move, the second one is the fix of DI-10-02.
DRIVEN_LANGUAGE_CASES = RUN_DIR / "98-sprachfaelle.sh"
SUCCESSOR_LANGUAGE_CASES = FIX_RUN_DIR / "98b-sprachfaelle.sh"

# The two successor fassungen of auflage A1 of the acceptance of 21.09.2026.
# 92c follows 92b for finding L-03, 99d follows 99c for finding L-04, and
# neither of them ran: the box was taken down on 21.09.2026, so their
# acceptance criterion was form, digest and static analysis. That sentence
# stands in the head of each file and is asserted below, because a fassung
# somebody later mistakes for a measured one is the finding these two would
# otherwise create.
SUCCESSOR_IMAGE_SWITCH = SUCCESSOR_RUN_DIR / "92c-wechsel.sh"
SUCCESSOR_FILTER_SORT = SUCCESSOR_RUN_DIR / "99d-filter-sortierung.sh"
NOT_DRIVEN = "DIESE FASSUNG IST NICHT GEFAHREN"

# The name of the path variable of the password file. It is the one
# 98c-sprachfaelle.sh of the same trip carries, which is why the gate holds
# both files against it: a successor that invented a third name would read the
# same file and be unreachable for the run plan that hands the old one over.
PWFILE_DEFAULT = 'PWFILE="${PWFILE:-'

# The line of 99d that asks the environment, written down so that the order of
# the two sources can be asserted rather than described. The environment stays
# the permitted shape of V14 and comes first; the file is the second way, the
# one the rest of the tools of that run directory go.
ENVIRONMENT_FIRST = r'''eval "printf '%s' \"\${$PASSWORT_ENV:-}\"" >"$PWFELD"'''
PWFILE_READ = 'sudo cat "$PWFILE"'

# The probe of the v1.2 run: the foreign stock, counted in the process of the
# container instead of over the capped OCS route (DI-10-02, DI-11-01).
STOCK_PROBE = V12_RUN_DIR / "73-bestand-sonde.py"

# The three refusal contracts of the v1.2 run that hold without a box: the
# language case fassung checks CI_LAUF before the first sudo, docker or curl
# call, the cron precheck decides its branch before everything else, and the
# rewarm tool of step 8 decides its auspraegung before it so much as creates a
# raw file.
V12_LANGUAGE_CASES = V12_RUN_DIR / "98c-sprachfaelle.sh"
V12_CRON_PRECHECK = V12_RUN_DIR / "97-cron-vorpruefung.sh"
V12_REWARM = V12_RUN_DIR / "95b-wiederaufwaermen.sh"

# The MEM-02 tool of step 8b, and the two figures its whole verdict hangs on.
# The measure is written down word for word, and so is the formulation it must
# never carry: the difference between the two is the difference between a
# measured saving and an invented one. docs/performance.md says so in the
# section that names the measure, and the tool repeats it rather than referring
# to it, because a raw file is read on its own.
V12_BASELOAD_RETURN = V12_RUN_DIR / "94b-grundlast-rueckkehr.sh"
MEASURE_OF_MEM_02 = "Rueckkehr zur Grundlast nach einem Indexlauf"
FORBIDDEN_MEASURE = "Grundlast minus"
BASELOAD_RETURN_ABORTS = ("exit 29", "exit 31", "exit 32", "exit 33")

# The two helpers of scripts/ops the MEM-02 tool calls, and the state they are
# in. Written down and not recomputed from the files under test, for the reason
# the two fassung watchmen above give: a gate that asks the file for its own
# expectation agrees with it whatever it comes to say.
#
# The digests are taken over the bytes with carriage returns folded away, which
# the two watchmen above do not need to do. rss_digest.py was checked out on
# this machine before scripts/ops/*.py got its eol=lf rule, so the working copy
# carries CRLF while the blob and every runner carry LF. A digest over the raw
# bytes would therefore be red on one of the two machines no matter which one
# it was measured on, and a gate that is red on a green tree is a gate somebody
# switches off.
RSS_SAMPLER = REPO_ROOT / "scripts" / "ops" / "rss_sampler.sh"
RSS_DIGEST = REPO_ROOT / "scripts" / "ops" / "rss_digest.py"
RSS_SAMPLER_SHA256 = "c10a7074a0e7900111a255753fff5f67f5f7169b99a629467cc1c50e3e1d9976"
RSS_DIGEST_SHA256 = "f845da16dff0cf6905f38d2618b757eddd32040491b2c2dd9f97d5373f774dd5"

# The filter and sort tool of step 6b, the block the owner ordered on
# 19.09.2026 (D-01), and the four names its two silent failures hang on.
#
# SORT_MODES_NAME is the table of the product, not a list repeated here: the
# gate below reads the three sort names out of the source of the package and
# holds them against the one place the tool writes them down. A fourth name in
# the tool would be a heading over figures that are relevance all along,
# because an unknown name falls back to relevance without saying so.
#
# NEXT_LINK_MARK is the markup the next link carries. Pulling it out of the
# answer is the whole difference between measuring the paging and measuring the
# silent fall back to page 1: a hand built address without the fingerprint gets
# thrown back, and the page answers 200 and fast while it does (13-08).
#
# LOAD_TOOL is the calibrated load tool of step 6. It asks the OCS route, and
# the OCS providers know neither types nor sort (13-12), so a call from this
# block would measure unfiltered and say so nowhere.
V12_FILTER_SORT = V12_RUN_DIR / "99c-filter-sortierung.sh"
SEARCH_MODULE = REPO_ROOT / "backend" / "src" / "findling" / "index" / "search.py"
SORT_MODES_NAME = "SORT_MODES"
SORT_MODES_IN_THE_TOOL = re.compile(r'SORTIERMODI="\$\{SORTIERMODI:-([^}]*)\}"')
NEXT_LINK_MARK = "findling-pager__step--next"
# The parameter that says WHERE inside a result somebody stands. Page 1 carries
# no position at all, so the tool may build its address; every later page has
# to come out of the answer, cursor and fingerprint included. This shape in the
# code of the tool is therefore a self built position and the gate is red.
BUILT_POSITION = "page="
LOAD_TOOL = "search_load.py"
FILTER_SORT_ABORTS = ("exit 29", "exit 34", "exit 35")

# The image switch of block 13b, plan 15-06, and the four names its refusals
# hang on.
#
# REQUIRED_DIGEST is the one input this tool has no default for. The pointer
# :dev moves with every green run of the image pipeline, and the path filter of
# docker.yml reaches into backend/**, so a new test file moves it without
# changing a line of the image. A default here would be a default for the
# measured object.
#
# THE_COUNT_BEFORE_RM_DATA is the call, not the definition of the function: a
# gate that accepted the definition would be green for a file that defines the
# count and never runs it. THE_DANGEROUS_SWITCH is the line of 07.09.2026, when
# a second Nextcloud on the same docker daemon removed the measuring volume of
# the first one, because the volume name of an ExApp follows from its app id
# alone.
#
# THE_TREE_HASH_PROOF is called as a script and never rebuilt inside the switch:
# a proof that brings its own arithmetic proves itself only.
V12_IMAGE_SWITCH = V12_RUN_DIR / "92b-wechsel.sh"
REQUIRED_DIGEST = "ABBILD_DIGEST"
THE_COUNT_BEFORE_RM_DATA = 'nextclouds_zaehlen >"$WORK/'
THE_DANGEROUS_SWITCH = "--rm-data"
# How far above the switch the count may stand, counted in code lines with the
# comments already removed. The runbook says "unmittelbar davor" and a gate that
# only asked for a count SOMEWHERE above would be green for a second --rm-data
# appended at the end of the file, which is the very shape this gate exists to
# catch. Ten lines is the section the switch lives in and not a round number: the
# two calls of the driven order stand four and five lines under their count.
THE_COUNT_IS_IMMEDIATE = 10
THE_TREE_HASH_PROOF = "40b-baumhash.sh"
THE_CGROUP = "/sys/fs/cgroup"
THE_HARD_LIMIT_IN_BYTES = "2147483648"
THE_LIMIT_OUT_OF_THE_CLIENT = ("HostConfig.Memory", ".Config.Memory")
IMAGE_SWITCH_ABORTS = ("exit 36", "exit 37", "exit 38", "exit 39")
# The cut of the first of the two pipelines this tool carries. Phase A judges
# without touching anything and ends here; the three refusals that have to fall
# before the first destructive command stand between this cut and the one of
# PIPELINE_CUT below.
VORLAUF_CUT = '} 2>&1 | tee "$WORK/vorlauf.txt"'

# The driven fassung of the image switch, the predecessor 92b-wechsel.sh was
# written after. It ran on 10.09.2026 and its raw data lie beside it, so it is
# evidence and not source: it is neither edited nor copied. Both figures are
# written down rather than recomputed from the file under test, for the reason
# the two language case watchmen give at their own definition.
DRIVEN_IMAGE_SWITCH = RUN_DIR / "92-wechsel.sh"
DRIVEN_IMAGE_SWITCH_SHA256 = "805d49fcfca8a3ee9f5ca5ae4cbdb26ec5da1c1b9d8fd5101669fd8b83837584"
DRIVEN_IMAGE_SWITCH_BYTES = 15705

# The user route the rewarm measurement reads its figures at, and the route it
# must never read them at. The second one is the trap of step 8: after a
# release the diagnosis route reports a full semantic side because it loads,
# while the user routes report an empty one because they are not allowed to.
USER_SEARCH_ROUTE = "/ocs/v2.php/search/providers/findling/search"
DIAGNOSIS_ROUTE = "/diagnose"

# The line the block of the rewarm tool ends on, and the three aborts that have
# to stand below it. The cut is written down rather than searched for loosely,
# because a gate that cut at the word "tee" would also cut at the sudo tee of
# drop_caches, which stands inside the block and is not an end of anything.
PIPELINE_CUT = '} 2>&1 | tee "$ZIEL"'
REWARM_ABORTS = ("exit 29", "exit 30", "exit 31")

# The eleven tools the trip of phase 15 took over from the run directory of
# v1.1. A copy is not a fork. It carries the figures of v1.1 with it, and the
# levels it drives stay comparable with the levels of the predecessor only for
# as long as it is the same file. A copy somebody adjusted quietly on the way
# would be a second object of measurement under the name of the first, and both
# sets of figures would end up in one report as though one tool had produced
# them. The order below is the order of their numbers, which is the order the
# measurement order of docs/runbook-messbox.md calls them in.
COPIED_TOOLS = (
    "40b-baumhash.py",
    "40b-baumhash.sh",
    "90-bestand.sh",
    "91-korpus.sh",
    "93-nullstand.sh",
    "95-spitze.sh",
    "96-volllauf.sh",
    "96b-waechter.sh",
    "96c-lesen.py",
    "96d-statusbeobachter.py",
    "97-nebenlaeufigkeit.sh",
)

# Every tool the measurement order of section 7 of the runbook names: the eleven
# copies above plus the files the run directory of v1.2 was written with.
# Written down rather than globbed, because the statement is that a tool the
# order names and the directory lacks is found on a rented box at the price of
# box time. Every entry joins this list in the commit that creates the file it
# names, which is why the rewarm tool of plan 15-03, the baseload return tool
# of plan 15-04, the filter and sort tool of plan 15-05 and the image switch of
# plan 15-06 arrived one by one rather than all at once.
TOOLS_THE_MEASUREMENT_ORDER_NAMES = (
    *COPIED_TOOLS,
    "73-bestand-sonde.py",
    "92b-wechsel.sh",
    "94b-grundlast-rueckkehr.sh",
    "95b-wiederaufwaermen.sh",
    "97-cron-vorpruefung.sh",
    "98c-sprachfaelle.sh",
    "99c-filter-sortierung.sh",
)

# The state of the driven fassung, measured on 2026-09-10 out of the file
# itself. Both figures are written down and neither is recomputed from the file
# under test, because a watchman that asks the file for its own expectation
# agrees with it no matter what it says. The bytes are the same on Windows and
# on a runner: .gitattributes checks every .sh out with LF endings.
DRIVEN_LANGUAGE_CASES_SHA256 = "5f9607fc6f00754b99eb9921aa6c3ce492e7eb3725f7efb2520be6c12f1ade1d"
DRIVEN_LANGUAGE_CASES_BYTES = 23479

# The state of the second driven fassung, measured on 2026-09-14 out of the file
# itself, and written down here for the same reason as the two figures above: a
# watchman that recomputes its expectation from the file under test agrees with
# that file whatever it comes to say. 98b-sprachfaelle.sh ran on 10.09.2026 and
# its raw data lie under 2026-09-werkzeugfixe/rohdaten/, so it is evidence as
# much as its predecessor is.
SUCCESSOR_LANGUAGE_CASES_SHA256 = "ef74a070502c2d05feeeba3dfe3d3c35076c912d17358ac486d5f01487c85669"
SUCCESSOR_LANGUAGE_CASES_BYTES = 35344

# The sentence the watchman says when it goes red. It is a constant so that the
# diagnosis cannot drift away from the rule it defends.
DRIVEN_FASSUNG_RULE = (
    "eine gefahrene Messfassung ist Teil des Belegs, und ein Fix entsteht als neue Datei in einem neuen Laufverzeichnis"
)

# The six fassungen the paid trip of phase 15 actually drove, with the sha256
# and the byte count of each. Plan 15-15, after the box was taken down.
#
# A driven measurement fassung is part of the evidence and is not touched
# afterwards. Whoever wants to change one of these six writes a successor with
# a new number in a new run directory, exactly as 98b followed 98 and 98c
# followed 98b. The reason is not tidiness: the raw files in
# docs/measurements/2026-09-v12-messung/rohdaten/ carry the figures of the trip,
# and every one of them is a statement about the script that produced it. A
# correction inside one of these files would turn each of those figures into a
# claim about a script that no longer exists, and the box that could settle the
# question does not exist any more either.
#
# Both figures are written down rather than recomputed from the file under
# test, for the reason the older watchmen give at their own definition: a gate
# that asks the file for its own expectation agrees with it no matter what it
# comes to say. The bytes are the same on Windows and on a runner, because
# .gitattributes checks every .sh out with LF endings.
#
# The order is the order of the numbers, which is the order the measurement
# order of docs/runbook-messbox.md calls them in, and not the order in which
# they ran.
DRIVEN_V12_FASSUNGEN: dict[str, tuple[str, int]] = {
    "92b-wechsel.sh": ("8d1f51997a1642eb0d4a1247975db73cdaa0000acf6bf70e9c74f34f165780fd", 30400),
    "94b-grundlast-rueckkehr.sh": ("a88a906201898e806f0361395b6f64b169086e78d6593ee171b7fed7f563b350", 36011),
    "95b-wiederaufwaermen.sh": ("791640fd01f0d56c5da344d12efe62198bc62f379e2721978a69489dbe952791", 30529),
    "97-cron-vorpruefung.sh": ("0c84c4ff1b47e23435428c5a58b0f28ab7397ba7e90c3912ab50392ba41eae72", 26252),
    "98c-sprachfaelle.sh": ("18ed06b498ad836fa9bb01b4f05a9fe99004eaaaae6743f73a6bfd44b1d87694", 44073),
    "99c-filter-sortierung.sh": ("dda76234d8ee7d8e54ebb73289c705509681cbd23d5646db3c60b1da36425d97", 29065),
}

# The two files of the full run that can be held to a promise without a box: the
# reader the watchman decides on, and the observer whose recordings are checked
# into this repository.
READER = RUN_DIR / "96c-lesen.py"
OBSERVER = RUN_DIR / "96d-statusbeobachter.py"

# The keys one recording of the observer may carry, and no others. Nine on the
# top level plus the nested one, which is where the counters of both tracks live.
# Written down here rather than read out of the observer, because a gate that
# asks the tool for its own contract agrees with it no matter what it writes.
RECORDING_KEYS = frozenset(
    {
        "at",
        "runState",
        "indexed",
        "indexedPercent",
        "embedded",
        "embeddedPercent",
        "scheduled",
        "running",
        "backendReachable",
        "backend",
    }
)
BACKEND_RECORDING_KEYS = frozenset({"indexed", "embedded"})

# The two kinds of file that are run. A directory of measurement scripts also
# holds other things, for instance the .claude-active of the semantic run, and a
# gate that read every file would fail on the first note somebody leaves there.
SCRIPT_SUFFIXES = frozenset({".py", ".sh"})

# The two shebangs a script of this run may carry.
SHEBANGS = (b"#!/bin/sh\n", b"#!/usr/bin/env python3\n")

# A password belongs in an environment variable, never in an argument, because an
# argument stands in the process list of the box and in every log that records the
# command. The permitted shape is the one search_load.py uses, --password-env,
# which carries the name of the variable and not the value, and which is not
# matched by either of these two because both demand a space or an equals sign
# where it carries a hyphen.
PASSWORD_OPTIONS = ("--password ", "--password=")

# The short form is a different problem. Written as a bare substring, "-p " means
# "create the parent directories" far more often than it means a password, and a
# gate that goes red on mkdir -p is a gate somebody switches off inside a week. So
# it counts only behind a program that really takes a password that way.
PASSWORD_SHORT_FORM = re.compile(r"\b(?:mysql|mariadb|mysqldump|redis-cli|smbclient)\b[^\n]*?\s-p\s*\S")
SHORT_FORM_NAME = "-p behind a program that takes a password"

# A variable with a default is the one place a path of the box may be written
# down, because it is the place a reader can change without reading the body.
DEFAULT_ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*="?\$\{[A-Za-z_][A-Za-z0-9_]*:-')

# The state this commit measures, nachgerechnet on 2026-09-09. They are written
# down here and not computed, because a test that recomputes the recipe it is
# guarding agrees with itself no matter what the recipe does.
PACKAGE_FILES = 54
PACKAGE_TREE_HASH = "6c47cd219c430bccc9d5d57b1de1d2ff9f8672fa4f42b1160d0a31efb9367476"
PHP_FILES = 58
# Corrected on 2026-09-09, on the box, and the old value is named here rather
# than dropped: 26b55908... was this same tree hashed on Windows, where the
# comparison of two Path objects folds case and put tests/bootstrap.php in front
# of tests/Unit/..., while the box and every ubuntu runner sorted the other way.
# The 58 files are byte identical on both machines, file by file, so only the
# order differed. 40b-baumhash.py now sorts by the relative posix path, which is
# the string it hashes and what its own docstring always specified, and this is
# the figure both platforms produce. PACKAGE_TREE_HASH is unaffected: the python
# package yields 6c47cd21... under either sort key on either platform.
PHP_TREE_HASH = "4a4c6f62598e2db036c0f75bf4dc6c7040c9fdafe4fb36798a8f09bb7509d9ed"

# The same recipe over the same directory, but over the working tree as it
# stands after plan 11-13, and it is a second constant rather than a new value
# in the first one. The figure above is a raw reading of the run of 09.09.2026;
# it is quoted in rohdaten/40b-baumhash.txt and in the table of
# docs/measurements/2026-09-vergleichsmessung-m7g/README.md, and overwriting it
# would retire a reported measurement figure, which this project does not do.
#
# The two parted on 10.09.2026, when plan 11-13 built the sentence of DI-07-03
# into the PHP half: eight of the 58 files changed their bytes and none of them
# came or went, so the count above still holds and only the hash moved. The four
# catalogue files of that plan are not in this reading at all, because the
# recipe reads **/*.php. Nothing about the report becomes untrue with it. The
# report says the hash of the working tree the report was written from, and
# that tree is the one above; a hash of a tree that has since moved on is a
# different statement and gets a different name.
#
# Both are asserted below, and each one asserts something the other cannot. The
# figure above keeps this file honest against the raw data of the run. The
# figure here keeps the recipe unchangeable against a real tree, which is what
# the assertion was for, and it is what the next change to the PHP half has to
# move.
#
# Moved on 11.09.2026 by plan 11-11, and this time the count moved with it: the
# migration Version001100Date20260911000000 and its test are two files that did
# not exist on 10.09.2026. So the count needs the same split the hash has had
# since the day before, for the same reason. PHP_FILES stays at the 58 of the
# run because "dateien: 58" stands in rohdaten/40b-baumhash.txt and a reported
# measurement figure is not rewritten when the code moves on.
# Moved on 2026-09-11 a second time, by the top-up route of the starvation fix
# (DI-10-04): CrawlAdvanceService.php and the two test files of the route are
# three files that did not exist before, and QueueController.php plus
# StorageCrawlJob.php changed their bytes.
# Moved on 2026-09-16 by plan 13-04, and the count moved once more: SearchFilters
# .php is a file that did not exist before, and ExAppService.php, SearchService
# .php, ExAppServiceTest.php and SearchServiceTest.php changed their bytes with
# the filter and sort fields of phase 13. So 63 becomes 64 and the hash follows.
# Moved on 2026-09-16 again, by plan 13-05, and this time the count stays at 64
# because no file was added or removed. Seven files changed their bytes:
# ApprovedHit.php got its fifth field, SearchService.php got the filters in its
# signature and the modification date out of the confirmed node, PageController
# .php and Provider.php hand the unnarrowed filter down until 13-06 and 13-07
# fill it, and SearchServiceTest.php, ProviderTest.php and PageControllerTest
# .php follow the two changed signatures.
# Moved on 2026-09-17 by plan 13-06, and the count stays at 64 for the same
# reason as the day before: no file came and none went. Two files changed their
# bytes. Provider.php declares the two built in date filters of the unified
# search dialog and reads them, which is the repair of FILT-03 on that side: an
# undeclared exclusive filter costs the whole result group, either because the
# surface stops asking this provider or because its group ends in a 400, and
# both looked to the user like Findling being gone whenever a date was set.
# ProviderTest.php follows with the cases for the four declared names, the two
# bounds as epochs, the value of the wrong kind that counts as not set, and the
# two clamps.
# Moved on 2026-09-17 again, by plan 13-07, and the count stays at 64 a third
# time because no file was added or removed. Two further files changed their
# bytes: PageController.php reads the five filter values out of its address and
# computes the calendar windows in the zone of the user, and PageControllerTest
# .php follows it with the two new doubles of the constructor.
# The figure below is neither of the two the plans wrote on their own branches.
# Both were measured against a tree that held only that plan's own change, and
# the hash is over the whole half, so the merge of the two is a third tree with
# a third hash. It was read off the merged tree with the same recipe.
# Moved on 2026-09-17 a third time, by plan 13-08, and the count stays at 64 for
# the fourth time running because no file was added or removed. The same two
# files changed their bytes as the day before: PageController.php builds the
# addresses of the filter row out of a second builder that cannot write a
# position, binds the cursor path to a fingerprint of the request state and
# hands the chips, the sort links, the reset link and the modification date to
# the template, and PageControllerTest.php follows it with the cases for all of
# them. This plan ran alone in its wave, so the figure was measured against the
# merged tree of the wave before it and needs no second correction.
# Moved on 2026-09-17 a fourth time, by plan 13-09, and the count stays at 64 for
# the fifth time running because no file was added or removed. Three files
# changed their bytes. search.php grew its sixth block, the filter row, together
# with the date line of a hit, the five hidden fields of the search form and the
# fourth variant of the empty state. PageController.php gained formFilters(),
# which is the filter list of an address in the shape the form needs it, and
# PageControllerTest.php follows with the two cases for it. This plan ran alone
# in its wave as well, so the figure was measured against the merged tree of the
# wave before it and needs no second correction.
# Moved on 2026-09-19 by plan 14-09, and the count stays at 64 for the sixth
# time running because no file was added or removed. Three of the 64 changed
# their bytes, all three for the sixth engine state: AdminViewService.php took
# 'unloaded' into its mirrored closed list, templates/admin.php got the seventh
# sentence for the sixth word, and AdminViewServiceTest.php follows with the
# sixth row of its data provider. The plan touches js/admin.js and the six
# catalogue files as well; the recipe globs **/*.php, so none of them is in
# this tree and none of them moves this figure.
# Moved on 2026-09-21 by plan 16-06, and the count stays at 64 for the seventh
# time running because this plan changes bytes and adds no file. Two of the 64
# changed. ExAppService.php got the measurement of A3: hrtime around the one
# proxyRequest call the 1.5 s ceiling belongs to, a log line above the new
# SLOW_CALL_LOG_MILLISECONDS and the measured duration in the failure paths of
# call(). ExAppServiceTest.php follows with the case for the line above the
# threshold, the case for the silence below it, and the normalisation that keeps
# a measured number out of a comparison of two failure paths. A3 is the open
# half of finding M-01: the raw files of the phase 15 trip carry the duration of
# the whole request on the user route and never the duration of the inner call,
# so the question MEM-03 asks could not be decided from them.
# Moved on 2026-09-21 a second time, by plan 16-07, and the count moves for the
# first time since 11.09.2026: 64 becomes 66, because two files arrived that did
# not exist before. Version001200Date20260921000000.php is the migration of the
# minor step from 1.1.0 to 1.2.0, which drops the recorded backend version for
# the reason its predecessor of 11.09.2026 states and deliberately writes no
# version in its place, and Version001200Date20260921000000Test.php is its unit
# test, the four cases of the predecessor plus the second run and the check that
# the constructor was handed nothing that could reach the container. No other
# file of the half changed its bytes: the bump of the three version places of
# the same plan lands in appinfo/info.xml, and the recipe globs **/*.php.
# Moved on 2026-09-24 by plan 18-10, and the count stays at 66 for the first
# time since 21.09.2026 because this plan changes bytes and adds no file. Two of
# the 66 changed. AdminViewService.php got one line per new status key in
# backend(), six in all, and the paragraph that says why none of them goes
# through optionalCounter(): each has a resting value a container reports while
# nothing is happening, so null would buy a distinction with no consequence
# anywhere. templates/admin.php got the sixth and the seventh banner next to the
# reindex banner and never in its place, the line of the language diagnosis, and
# the size formatter moved up next to the count formatter because the banner
# list of block one now needs it and is built before the variables of block two
# exist. The plan touches js/admin.js and the six catalogue files as well; the
# recipe globs **/*.php, so none of them is in this tree and none of them moves
# this figure.
# Moved on 2026-09-24 a second time, by plan 18-11, and the count moves for the
# second time since 11.09.2026: 66 becomes 68, because two files arrived that
# did not exist before and none went. Version001300Date20260924000000.php is the
# migration of the minor step from 1.2.0 to 1.3.0, a copy of the one of
# 21.09.2026 whose body is identical line for line and whose class comment
# gained one paragraph, the one that says the index rebuild of this phase is
# deliberately not in a migration; Version001300Date20260924000000Test.php is
# its unit test, the same six cases as its predecessor. No other file of the
# half changed its bytes: the bump of the version places belongs to the release
# phase and not to this plan, and the recipe globs **/*.php.
# Moved on 2026-09-24 a third time, by the fix of the audit finding M-18-05, and
# the count stays at 68 because this fix changes bytes and adds no file. One of
# the 68 changed. templates/admin.php got one sentence more in the text of the
# space banner: _BLOCKED_BYTES is reset only at the start of rebuild_the_index
# and that function runs once per container start, so an admin who frees the
# space and waits was waiting for nothing. The banner now names the restart, and
# it does so on both halves of its own advice, because a changed environment
# variable is not read without one either. The fix touches js/admin.js and the
# six catalogue files as well; the recipe globs **/*.php, so none of them is in
# this tree and none of them moves this figure.
PHP_FILES_TODAY = 68
PHP_TREE_HASH_TODAY = "a1339e70ac425db40dd4cf1163279413046075d27bc63c160240b0fab6a8abba"

# The python package needed no such split until 2026-09-11: nothing under
# backend/src/findling had changed since the run, so the figure of the run WAS
# the figure of the tree. The starvation fix of DI-10-04 parted them (three of
# the 54 files changed their bytes, none came or went: nc/client.py and
# nc/queue.py learned the top-up call, worker/poller.py the starved branch), and
# the split follows the same rule as the PHP one above: the figure of the run
# stays because it is quoted in rohdaten/40b-baumhash.txt and in the report, and
# this one is what the next change to the package has to move.
#
# Moved on 2026-09-16 by plan 13-01, and the count did not move with it: exactly
# one of the 54 files changed its bytes, query/rewrite.py, which learned the
# table of the six type groups, the range over the modification time and the
# three keyword arguments the result page filters with. No file came and none
# went, so PACKAGE_FILES stays at 54 and only the hash is a different statement
# than it was yesterday.
# Moved on 2026-09-16 a second time, by plan 13-02, and the count did not move
# with it either: exactly one of the 54 files changed its bytes,
# index/search.py, which learned the table of the three sort modes, the sorted
# round over the fast column and the filter clause for the semantic half. No
# file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-16 a third time, by plan 13-03, and this time four of the 54
# files changed their bytes: config.py learned the two new ceilings
# SEARCH_TYPE_GROUPS_MAX and SEARCH_MTIME_MAX, api/search.py the four wire
# fields and the sort term on the lexical_only line, api/snippets.py the three
# query fields without a sort, and api/diagnose.py the same three as query
# parameters. No file came and none went, so PACKAGE_FILES stays at 54 and only
# the hash is a different statement than it was an hour ago.
# Moved on 2026-09-18 by the follow up fix of 13-13: exactly one of the 54 files
# changed its bytes, index/search.py, whose sorted round now scans with a fixed
# portion stride instead of one that grew with the requested depth, because the
# moving portion boundaries repeated and skipped documents at page transitions
# over a tie group. No file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 by plan 14-03: exactly one of the 54 files changed its
# bytes, config.py, which learned the switch of MEM-01, namely the constant
# EMBED_IDLE_RELEASE_SECONDS with its range, the third reader of the module,
# which lets a zero through ahead of the range because zero is the word off
# here, and the settings field the release policy of 14-06 and 14-07 will read.
# No file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a second time, by plan 14-04: exactly one of the 54
# files changed its bytes, worker/poller.py, which got the public property
# busy, the honest answer to "is a pass at work" that the release of MEM-02
# needs and that the log marker _idle_announced cannot give. No file came and
# none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a third time, by the second half of plan 14-04:
# worker/poller.py again, this time with release_cutter, which drops the pair
# _chunker and _model together and leaves the two markers of the build
# standing. No file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a fourth time, by the first half of plan 14-05: exactly
# one of the 54 files changed its bytes, embed/model.py, which got the idle
# clock last_use(), the activity counter _in_flight and the switch may_load on
# embed_query and _embed. No file came and none went, so PACKAGE_FILES stays
# at 54.
# Moved on 2026-09-19 a fifth time, by the second half of plan 14-05:
# embed/model.py again, this time with release(), the monotonic counter
# _UNLOAD_COUNT with unload_count(), and _return_free_pages_to_the_system,
# which collects and then trims and stays quiet where the libc has no way to.
# No file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a sixth time, by the first task of plan 14-06: exactly
# one of the 54 files changed its bytes, embed/engine.py, which got
# query_may_load, the one place that says whether a search may pay for the
# weights, so that the three callers building a SemanticSide ask instead of
# repeating. No file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a seventh time, by the second task of plan 14-06:
# embed/engine.py again, this time with release_if_idle, which reads the
# holder through _held, holds the clock against the span, checks the identity
# of the instance under _LOCK and calls the release outside it, and with
# released_count beside it. No file came and none went, so PACKAGE_FILES
# stays at 54.
# Moved on 2026-09-19 an eighth time, by the third task of plan 14-06:
# embed/engine.py a third time, with request_warm, warm_wanted and warm, the
# two flags _WARM_WANTED and _WARMING beside the holder and the fixed line
# WARM_TEXT that a warm run embeds. No file came and none went, so
# PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a ninth time, by plan 14-07: exactly one of the 54 files
# changed its bytes, main.py, which got the third long lived task of the
# lifespan, _release_when_idle, with its tick RELEASE_TICK_SECONDS, its stop
# budget RELEASE_STOP_SECONDS and the fourth stop event beside the two that
# were already there. No file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a tenth time, by the first task of plan 14-08: exactly
# one of the 54 files changed its bytes, index/search.py, which got the
# keyword may_load on the QueryEmbedder protocol, the fourth field may_load
# on SemanticSide and the same keyword on both of its embed_query calls. No
# file came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 an eleventh time, by the second task of plan 14-08:
# three of the 54 files changed their bytes, api/search.py and
# api/snippets.py, which now ask query_may_load at the line that builds
# their SemanticSide, and api/diagnose.py, which got the comment saying
# why its own line deliberately does not. No file came and none went, so
# PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a twelfth time, by the third task of plan 14-08:
# exactly one of the 54 files changed its bytes, api/search.py, which now
# asks request_warm where the round is built without the weights and
# orders the warm run from the handler through asyncio.create_task, with
# the module set _WARM_TASKS holding the task while it runs. No file came
# and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-19 a thirteenth time, by the first task of plan 14-09:
# exactly one of the 54 files changed its bytes, embed/engine.py, which got
# the sixth word of ENGINE_STATES, ENGINE_UNLOADED, and the branch in
# engine_state that answers it behind loaded and in front of cold. No file
# came and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-21 a fourteenth time, by plan 16-10: exactly one of the 54
# files changed its bytes, config.py, whose OCR_LANGUAGE_ALLOWLIST grew from
# three entries to nine (spa, ita, nld, por, dan and est joined deu, eng and
# fra) while OCR_DEFAULT_LANGUAGES deliberately stayed at three. No file came
# and none went, so PACKAGE_FILES stays at 54.
# Moved on 2026-09-23 a fifteenth time, by plan 17-02: exactly one of the 54
# files changed its bytes, config.py, which gained LANGUAGE_ALLOWLIST (the 13
# name intersection of the two language sets tantivy serves), SUPPORTED_LANGUAGES
# and SNOWBALL_NAME beside DEFAULT_LANGUAGES, none of them read by a production
# path yet. No file came and none went, so PACKAGE_FILES stayed at 54.
# Moved on 2026-09-23 a sixteenth time, by the wave merge of plans 17-02 and
# 17-03: index/stopwords.py arrived (FOLDED_STOPWORDS, the 117 folded Snowball
# stop words the new chain needs, plus folded_stopwords_hash), so 54 becomes 55,
# and index/analyzer.py changed its bytes (factory snowball_analyzer and the
# second chain table in its module header). The hash below is the one figure
# over the merged tree that carries both plans at once; the per-plan figures
# from the two worktrees could not survive the merge because each was measured
# without the other plan's bytes. The figure of the run, PACKAGE_FILES, stays
# at 54 for the reason the PHP pair states: a reported measurement figure is
# not rewritten when the code moves on.
# Moved on 2026-09-23 a seventeenth time, by plan 17-07: exactly one of the 55
# files changed its bytes, store/repo.py, which gained _index_format_matches
# beside _generation_at_least and the second exception in
# Store.version_mismatch, so that only the index_format half of the tantivy
# banner decides (owner decision E-17-7 option a of 2026-09-23). No file came
# and none went, so PACKAGE_FILES_TODAY stays at 55.
# Moved on 2026-09-23 an eighteenth time, by the fix of the audit finding
# M-17-03: exactly one of the 55 files changed its bytes, index/analyzer.py,
# whose snowball_analyzer became one armed. It takes the language alone, lowers
# it once, refuses a name outside LANGUAGE_ALLOWLIST and a name without a
# measured supplement with a ValueError that says which, and looks the
# supplement up in FOLDED_STOPWORDS instead of taking it as a second parameter.
# The tokenisation of the one registered chain does not move by a byte, so
# ANALYZER_VERSION stays at 1. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 55.
# Moved on 2026-09-24 a nineteenth time, by plan 18-01: four of the 55 files
# changed their bytes. index/analyzer.py got the four chain names TOKENIZER_ES,
# TOKENIZER_IT, TOKENIZER_NL and TOKENIZER_PT beside the two that were there.
# index/schema.py got the four body fields body_es, body_it, body_nl and
# body_pt between body_en and mtime, all four unstored, the closed mapping
# BODY_FIELD from language code to field name, and a module header that carries
# the measurement of 2026-09-24 instead of the nine field count. index/open.py
# registers the four Snowball chains through snowball_analyzer and the names of
# SNOWBALL_NAME, unconditionally, because a text field whose chain is missing
# makes every add_document raise. config.py raised SCHEMA_VERSION from 1 to 2
# for the four new fields, under the owner decisions E-17-1 to E-17-4 of
# 2026-09-23. No file came and none went, so PACKAGE_FILES_TODAY stays at 55.
# Moved on 2026-09-24 a twentieth time, by plan 18-02: two of the 55 files
# changed their bytes. config.py filters _languages() against
# SUPPORTED_LANGUAGES instead of against DEFAULT_LANGUAGES, which is the one
# line between "six body fields exist" and "six languages are selectable";
# DEFAULT_LANGUAGES itself stays ("de", "en"), it is the factory setting and not
# the capability list. index/writer.py replaced the single English flag of its
# constructor with the language set: add() now loops over the active set and
# takes every field name out of BODY_FIELD, while body_de is written
# unconditionally because it is the one stored copy of the text. No file came
# and none went, so PACKAGE_FILES_TODAY stays at 55.
# Moved on 2026-09-24 a twenty first time, by plan 18-05: six of the 55 files
# changed their bytes, all six for the sixth version mark of owner decision
# E-17-4 option a. index/open.py got LANGUAGES_MARK and the second parameter of
# expected_versions, which takes the language set instead of reading it, so that
# the call sites stay visible. store/repo.py got _languages_are_legacy beside
# _generation_at_least and _index_format_matches, the third if line in the
# comparison loop of version_mismatch, LEGACY_LANGUAGES as its own tuple, and a
# _seed_meta that drops the mark even when a caller hands it in, which is the
# whole reason the mark can speak at all. api/resources.py, worker/poller.py and
# tools/one_load.py hand the set in at their four call sites, each of them as
# ",".join(settings().languages) and none of them assembling it differently.
# tools/index_status.py reports the mark as the sixth entry of _VERSION_KEYS,
# which is the visible difference between 1.2.0 and 1.3.0 the upgrade leg of the
# CI run reads. No file came and none went, so PACKAGE_FILES_TODAY stays at 55.
# Moved on 2026-09-24 a twenty second time, by plan 18-06, and this time the
# count moves with the hash: index/rebuild.py arrived, so 55 becomes 56. It
# carries the precheck of the volume (RebuildVerdict and may_rebuild, with the
# factor 0.40 for every newly filled chain on top of the unchanged
# MIN_FREE_BYTES floor), the band run over file_id with range_query and one
# commit per band of 500, the document rebuild _document_from over the eight
# stored fields with body_en fed out of body_de, the stateless resume
# _resume_cursor that reads the highest carried over file_id out of the half
# written target directory, and counts_match as the final probe the swap of
# plan 18-07 will hang on. config.py changed its bytes as the second file, for
# FINDLING_REBUILD_FALLBACK with its two positions and the rebuild_fallback
# field of Settings beside compound_dict. One file came and none went, so
# PACKAGE_FILES_TODAY moves to 56.
# Moved on 2026-09-24 a twenty third time, by plan 18-07: two of the 56 files
# changed their bytes and the count stays at 56. index/rebuild.py got the swap,
# which is two renames with nothing between them (swap_in over retire_directory
# and discard_directory, the retired name derived from the live one with
# with_name so that the path removed is never handed in), the six numbered steps
# of the order in its module header, and stamp_after_swap, a second and
# deliberately narrow stamper that writes the schema mark and the language mark
# and empties the rebuild mark once the swap is really through. api/resources.py
# got reset_read_side, which drops the handle, the version marks and the
# degraded verdict under the one lock and checks no path, because the swap puts
# the rebuilt directory under the very name the live one had and the
# invalidation branch of read_side therefore never fires. No file came and none
# went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a twenty fourth time, by plan 18-08: exactly one of the 56
# files changed its bytes, index/rebuild.py, which got the clean up path of the
# start. recover_the_index_directories reads what the volume holds, derives all
# three directory names from settings().index_dir with with_name and takes no
# path from anybody, and answers with one of five names: the ordinary start is
# left alone, a half filled index.rebuild beside a live index is kept because it
# is the progress record the next pass resumes in, an index.rebuild without a
# live index is raised to the live name because the missing live name is the
# proof that the swap had already begun, an index.retired without a live index is
# brought back because it is then the only complete holding, and an index.retired
# beside a live one is discarded as waste. Four of the five branches warn and
# name the state and never a path; the ordinary start says nothing, because a
# warning that appears on every start is not a warning. No file came and none
# went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a twenty fifth time, by plan 18-09: three of the 56 files
# changed their bytes and the count stays at 56. index/rebuild.py got
# rebuild_the_index, the one entry point that leads the seven steps of a run in
# the order of the ablauf diagram (drift, precheck, silence, band run, final
# probe, swap behind a dropped read side, stamp, arm), the poller reaching it as
# a callback pair rather than as an import, the named way out over
# FINDLING_REBUILD_FALLBACK, rebuild_progress as a process reading after the
# build of engine_state, and a should_stop that is asked between two bands.
# main.py got the fourth long lived lifespan task with REBUILD_STOP_SECONDS
# beside the three stop budgets that were there, the clean up path of plan 18-08
# called before the first task exists, and warn_on_uncovered_languages, the one
# line at startup that closes the Buchstabensalat trap with a count and never a
# code. config.py got TESSERACT_NAME, the closed mapping from body language code
# to tesseract name that the warning reads, and a name for the second position of
# the rebuild fallback switch. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a twenty sixth time, by plan 18-10: three of the 56 files
# changed their bytes and the count stays at 56. api/status.py got the five new
# fields of the answer, languagesActive and languagesFilled next to the four
# readings of the rebuild, each with its default and its paragraph, and the two
# lines in _volume() and _of() that carry them. api/resources.py got
# filled_languages(), the probe that asks the term dictionary of the six body
# chains whether anything is in them, behind a TTL cache of its own next to
# _DEGRADED and cleared by reset_read_side with it; the same file lost the call
# of Index.exists on a path that may not exist, which raises rather than
# answering False and therefore escaped a function whose contract is that it
# never raises. index/rebuild.py got rebuild_blocked_bytes(), the shortfall the
# precheck refused on, published the way the progress is. No file came and none
# went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a twenty seventh time, by the diagnosis of the CI leg
# "Store upgrade 5" (deploy-harp run 35989391950): one of the 56 files changed
# its bytes and the count stays at 56. store/repo.py got _SCHEMA_MARK and
# LEGACY_SCHEMA_STEPS, the fourth named exception _schema_is_legacy beside
# _generation_at_least, _index_format_matches and _languages_are_legacy, and the
# one line in version_mismatch that reads it. What it buys is success criterion
# 1 of this phase: a stored schema generation of 1 against the expected 2 is the
# state every installation upgrading from 1.2.0 is legitimately in, because
# Index.open reads the persisted schema back and the mark is only stamped after
# a rebuild, so calling it a drift raised the generation and the reindex banner
# on every volume in the field. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a twenty eighth time, by the fix of the audit findings
# C-18-01 and H-18-01: three of the 56 files changed their bytes and the count
# stays at 56. worker/poller.py got Poller.stand_down, which clears the armed
# flag, waits for the pass in flight on the new _in_flight field rather than on
# the held rows, hands the rows back and closes the IndexWriter, plus
# STAND_DOWN_SECONDS, STAND_DOWN_TICK_SECONDS, the pass_in_flight property and
# the branch in _open that builds a fresh writer while keeping the queue.
# index/rebuild.py replaced the silence callback of rebuild_the_index with a
# stand_down that answers whether the task really went quiet, got the verdict
# POLLER_STILL_WRITING for the answer False, caught the removal behind the two
# renames of swap_in so that a leftover cannot cost the stamp, and corrected the
# sentence of step 2 in its module header, which had claimed the writer was
# already closed. main.py replaced _silence_the_poller with
# _stand_the_poller_down, which takes the event loop because the rebuild runs in
# a worker thread and the stand down is a coroutine, and got
# STAND_DOWN_GRACE_SECONDS beside the three stop budgets. No file came and none
# went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a twenty ninth time, by the fix of the audit findings
# H-18-02 and H-18-04: two of the 56 files changed their bytes and the count
# stays at 56. index/open.py made _fingerprint public as fingerprint, because
# the rebuild is now its second caller. index/rebuild.py got TARGET_MARK_FILE
# and the pair _make_the_target_fit_this_code and _mark_in, which write the
# fingerprint of the expected marks into the half filled target and discard a
# target that carries another one or will not open at all; counts_match became
# "at least as many" with a line for the source that shrank under a delete job;
# and a pass that carried nothing over while the count is still short discards
# its target under the new verdict RUN_INCOMPLETE_TARGET_DISCARDED, which is the
# way out of the dead end the cursor and the equality used to build together. No
# file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a thirtieth time, by the fix of the audit finding H-18-03:
# two of the 56 files changed their bytes and the count stays at 56.
# index/rebuild.py got _discard_what_is_left, the catching half of
# discard_directory, and the two removals of recover_the_index_directories go
# through it, so a leftover the volume will not release can no longer take the
# rename beside it with it. main.py wraps the whole clean up call of the
# lifespan in a try that logs the type name and lets the start carry on: it used
# to travel out of the lifespan, which under AppAPI is a restart loop with no
# way out of it from inside the container, and in state 5 the search would have
# been fully able to answer. No file came and none went, so PACKAGE_FILES_TODAY
# stays at 56.
# Moved on 2026-09-24 a thirty first time, by the fix of the audit findings
# M-18-01 and M-18-08: exactly one of the 56 files changed its bytes,
# api/resources.py. filled_languages() asks one chain at a time in a try of its
# own, so an index of the old generation that raises for body_es no longer
# discards the measurement of all six and tells the admin page that no chain
# carries text; and it asks only the chains of _chains_worth_probing(), the
# active set plus German in schema order, because terms_with_prefix walks the
# whole term dictionary of every field it is given. No file came and none went,
# so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a thirty second time, by the fix of the audit findings
# M-18-02 and M-18-03: three of the 56 files changed their bytes and the count
# stays at 56. api/resources.py got ReadSide.generation and the module counter
# _GENERATION beside it, so degraded() and filled_languages(), which take their
# side outside the lock and write their cache entry inside it, hand a reading of
# a retired directory out and keep it out of the cache; and it got _SWAPPING
# with the pair hold_the_read_side_shut() and let_the_read_side_open(), which
# makes read_side() answer None for the width of the two renames, because
# emptying the caches leaves the window between the emptying and the first
# rename open and a handle taken in it answers out of a directory with no name
# until the container restarts. index/rebuild.py takes the second callback of
# that pair and puts it in a finally around swap_in, and its module header
# carries the reasoning at step 3. main.py hands in the two functions instead of
# reset_read_side. No file came and none went, so PACKAGE_FILES_TODAY stays
# at 56.
# Moved on 2026-09-24 a thirty third time, by the fix of the audit finding
# M-18-04: exactly one of the 56 files changed its bytes, index/rebuild.py,
# which got the verdict LIVE_IS_A_SYMLINK and the branch behind the live
# directory check that answers it. A linked index directory breaks all three
# halves of a run and none of them can be repaired from inside it: the precheck
# measures the file system the link points at while the second directory is
# created beside the link, the swap renames the link away and puts a real
# directory in its place, and rmtree refuses a link outright so the marks are
# never written. No file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a thirty fourth time, by the fix of the audit finding
# M-18-06: two of the 56 files changed their bytes and the count stays at 56.
# main.py catches (OSError, sqlite3.Error) at the open of _rebuild_is_due and
# sqlite3.Error at the drift read behind it, which stood in a bare finally;
# api/resources.py takes the same pair in report_version_drift. Both run in the
# lifespan, and the two shapes that escaped an except OSError are the two
# api/status.py already names: a file that is not a SQLite database raises
# DatabaseError from the PRAGMA journal_mode right after the connect, and a zero
# byte state.db from a hard kill opens cleanly and raises OperationalError on
# the first query. Either one used to be a container that does not start. No
# file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a thirty fifth time, by the fix of the audit finding
# M-18-07: two of the 56 files changed their bytes and the count stays at 56.
# index/rebuild.py takes the shutdown mark into swap_in, which now answers
# whether it swapped and reads that mark in front of the first rename and once
# more in front of the removal behind it, and rebuild_the_index reads it a third
# time between the final probe and the swap. main.py says what
# REBUILD_STOP_SECONDS really bounds: rebuilding.cancel() ends the awaiting task
# and not the worker thread, asyncio.run joins that thread at the end of the
# shutdown anyway, so the budget buys the ordered part of the shutdown and not a
# faster one, and what it now also buys is a detached thread that stops at the
# next cooperative point instead of renaming directories while the poller is
# being closed. No file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a thirty sixth time, by plan 19-01: exactly one of the 56
# files changed its bytes, query/rewrite.py. The three module constants
# DEFAULT_FIELDS, TITLE_ONLY_FIELDS and FIELD_BOOSTS are gone, their values now
# stand in one frozen value, the class FieldPlan and its instance LEGACY_PLAN,
# and build_query takes that value as a keyword only parameter whose default is
# the legacy plan itself. Measured, parse_query_lenient raises the same
# ValueError for a field name it does not know under field_boosts as it does
# under default_field_names, so a field list that had been made movable without
# its boosts would only have postponed the empty search bar rather than
# preventing it. No file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-24 a thirty seventh time, by plan 19-03: five of the 56 files
# changed their bytes and the count stays at 56. index/open.py gave the schema
# key the public name SCHEMA_MARK next to LANGUAGES_MARK, because the field plan
# became its second reader and a key spelled out at every place that touches it
# drifts on the day one of them is renamed. api/resources.py got field_plan_for,
# which answers what a bare word searches on a directory out of the two marks
# that directory stores, and ReadSide.field_plan, which carries that answer for
# as long as the handles beside it live: the plan is computed once per open
# rather than once per keystroke, and it hangs on the handles rather than in a
# cache of its own because the invalidation a third cache would need is the one
# reset_read_side() and ReadSide.generation already provide. api/search.py,
# api/snippets.py and api/diagnose.py hand that plan to build_query and do
# nothing else with it, so the reading of the marks stays in one place and the
# permission prefilter keeps the single call site test_semantic_boundary.py
# counts. The gate falls closed: anything that is not literally the current
# schema mark, which covers an absent mark and the intermediate 1 of every
# installation that has not rebuilt yet, is answered with the frozen legacy
# plan, and a doc_freq probe against the directory itself catches the one state
# the mark cannot see, a state.db restored beside an older index directory. No
# file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by the fix of audit finding H-19-01: three of the 56 files
# changed their bytes. index/rebuild.py stamps the schema mark and the language
# mark inside the try of the swap and in front of let_read_side_open() instead of
# behind it, so that the first search after the bar comes down computes its field
# list out of the marks of the directory that is there rather than out of the
# marks of the one that has just been retired. worker/poller.py took a
# marks_stamped callback, which it calls once when its own stamp answers that the
# marks are current again, because that stamp writes while the reading side is
# wide open and nothing dropped it afterwards. main.py hands
# resources.reset_read_side into default_poller, the same seam at which it hands
# the two halves of the bar into the rebuild, so the worker package goes on
# importing nothing from the API package. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by the fix of audit finding M-19-01: two of the 56 files
# changed their bytes. api/resources.py split field_plan_for into the two gates
# of the marks (_of_the_marks) and the probe at the directory (_probed), and the
# probe now runs over every name that reaches the parser, the file name and the
# title included, drops the ones the directory does not carry instead of dropping
# the whole plan, and runs under the fallback as well: the answer is the first of
# the computed plan, the legacy plan and the empty plan that keeps a field.
# query/rewrite.py got EMPTY_PLAN beside LEGACY_PLAN and the short circuit in
# build_query that turns it into the same empty answer a line without a term
# gets, because an empty field list is the one input that makes the lenient
# parser raise. No file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by the fix of audit finding M-19-05: exactly one of the 56
# files changed its bytes, index/open.py, where stamp_after_rebuild got
# _MARKS_OF_A_DIRECTORY and skips all three of them instead of the local
# generation alone. The schema mark and the language mark describe an index
# directory, that stamp stands behind a pass over the holdings in the directory
# that is already there, and index.rebuild.stamp_after_swap behind the swap is
# the one place where what the two claim is true. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by the fix of audit finding M-19-04: exactly one of the 56
# files changed its bytes, api/resources.py, whose outer catch in field_plan_for
# says error instead of warning and says a different sentence. Everything the
# two halves of a volume can disagree about is caught one level down and named
# per field, so what reaches the outer catch is this build contradicting itself;
# the two used to be one line and an operator could not tell them apart. No file
# came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by the fix of audit finding M-19-03: two of the 56 files
# changed their bytes. api/resources.py got plan_falls_short, which holds the
# plan that goes out against the plan the marks promise, ReadSide.plan_is_short,
# which carries that answer beside the plan it is about, searched_languages,
# which reads the codes a question reaches out of the plan, and a degraded() of
# five causes instead of four. api/status.py got languagesSearched beside
# languagesActive and languagesFilled, filled in the volume answer and carried
# over in the counting half like every other reading of this process. No file
# came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by the four LOW findings of the phase 19 audit that touch
# the package: two of the 56 files changed their bytes. api/resources.py reads
# the language mark stripped and lowered (L-19-01) and hands its boosts out
# behind a MappingProxyType (L-19-02). query/rewrite.py does the same for
# LEGACY_PLAN and EMPTY_PLAN, whose weights were an ordinary dict reachable from
# the whole process although the value exists to be the frozen fallback
# (L-19-02); the docstring of build_query now says that the lenient parser is
# lenient about a typed field name and not about one in the plan (L-19-04); and
# the two allocations per query are kept with the reason written beside them
# (L-19-03). No file came and none went, so PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by plan 21-01: two of the 56 files changed their bytes.
# index/open.py gave start_rebuild_on_drift a keyword-only answered_elsewhere,
# the marks another remedy answers and that therefore raise no generation, and
# worker/poller.py hands MARKS_A_REBUILD_ANSWERS in from _open_state, so a drift
# of the schema mark or the language mark alone is left to the band run instead
# of adding a full reindex behind it. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 56.
# Moved on 2026-09-25 by plan 21-03, task 1: one file came. index/wordlist_nl.py
# is the Dutch sibling of index/wordlist.py, recipe B 4-14 with a folded list,
# the linking elements s, e and en, an artifact that fails closed, a cache that
# keeps the digest and never the entries, and a language gate that reads nothing
# while nl is not configured. No caller in the running app uses it yet. None went,
# so PACKAGE_FILES_TODAY moves to 57.
# Moved on 2026-09-25 by plan 21-03, task 2: one of the 57 files changed its
# bytes. index/analyzer.py got the Dutch splitter chain dutch_analyzer behind the
# fold, its singleton cached_dutch_analyzer with dutch_build_count, the choice
# dutch_chain_for that keeps the plain Snowball chain without nl and fails closed
# on a digest the volume does not hold, and the docstring paragraph that names
# wordlist_hash_nl as the exception to raising ANALYZER_VERSION. No caller in
# the running app uses it yet. No file came and none went, so
# PACKAGE_FILES_TODAY stays at 57.
# Moved on 2026-09-25 by Plan 21-05: two of the 57 files changed their bytes.
# index/open.py got the seventh mark DUTCH_MARK ("wordlist_hash_nl"), the
# keyword-only dutch_mark of expected_versions with the default off, the mark in
# _MARKS_OF_A_DIRECTORY and its write in stamp_a_new_directory. store/repo.py
# spells the mark and its off value as literals, keeps the mark out of the seed
# and compares it through _dutch_list_is_legacy, under which only an absent mark
# against off is no drift. Every caller in src still takes the default. No file
# came and none went, so PACKAGE_FILES_TODAY stays at 57.
# Moved on 2026-09-25 by Plan 21-06, task 1: one of the 57 files changed its
# bytes. index/rebuild.py names DUTCH_MARK in MARKS_A_REBUILD_ANSWERS, so a
# Dutch drift is answered by the band run, and stamp_after_swap takes a
# keyword-only dutch_mark without a default and writes it behind the swap. No
# file came and none went, so PACKAGE_FILES_TODAY stays at 57.
# Moved on 2026-09-25 by Plan 21-06, task 2: four of the 57 files changed their
# bytes. worker/poller.py (three calls), api/resources.py and tools/one_load.py
# hand dutch_mark(languages) to expected_versions explicitly, and
# tools/index_status.py reports the seventh mark as wordlistHashNl. No file came
# and none went, so PACKAGE_FILES_TODAY stays at 57.
PACKAGE_FILES_TODAY = 57
PACKAGE_TREE_HASH_TODAY = "81587ca3fdf3df5eec2242dd311bec3cd8b7919789342e95bc2eb70515149536"

# The raw reading of the run, so that the constant above cannot drift away from
# the file it was read out of.
BAUMHASH_RAW = REPO_ROOT / "docs" / "measurements" / "2026-09-vergleichsmessung-m7g" / "rohdaten" / "40b-baumhash.txt"

# Assembled from code points so that this file does not carry the characters it
# forbids and fail on itself. Same construction as in test_ops_scripts.py.
DASHES = (chr(0x2014), chr(0x2013))

# Every diagnosis of the recipe names the tool first. The prefix is asserted and
# not decoration: CPython answers a missing script file with exit code 2 as well,
# so without it the two refusal assertions below would have been satisfied by the
# absence of the very script they are about.
DIAGNOSIS_PREFIX = "40b-baumhash:"


def constant_of_the_ops_gate(name: str) -> tuple[str, ...]:
    """One named tuple constant, read out of the syntax tree of test_ops_scripts.py.

    Read rather than imported, because tests/ is not a package: an import would
    work under pytest and not under pyright. Read rather than copied, because two
    definitions of the same list are two definitions that drift apart, and the
    whole point of taking it from there is that both gates forbid the same shapes.
    """
    tree = ast.parse(OPS_GATE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return tuple(ast.literal_eval(node.value))
    message = f"{name} is not defined in {OPS_GATE.name}"
    raise AssertionError(message)


# The shapes that tie a tool to one machine, from the gate that first wrote them
# down. Not a second copy: one definition, two gates.
MACHINE_SHAPES = constant_of_the_ops_gate("MACHINE_SHAPES")


def imported_packages(text: str) -> set[str]:
    """The top level package of every import in the file.

    Read out of the syntax tree rather than out of the lines, for the reason the
    same reader in test_ops_scripts.py gives: an import inside a function is
    still an import, and a text search for "import " finds the word in every
    second docstring of this repository.
    """
    packages: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
    return packages


def run_the_recipe(root: Path, pattern: str) -> subprocess.CompletedProcess[str]:
    """The recipe as a subprocess, in the shape the box runs it.

    Not imported: the file name begins with a digit and is therefore not a valid
    module name. Running it as a program is also the more honest test, because
    the exit code is half of what this script promises.
    """
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(TREE_HASH), str(root), pattern],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def reading(answer: subprocess.CompletedProcess[str]) -> tuple[int, str]:
    """The two lines the recipe prints, and the promise that there is no third."""
    assert answer.returncode == 0, answer.stderr
    lines = answer.stdout.splitlines()
    assert len(lines) == 2, lines
    assert lines[0].startswith("dateien: "), lines[0]
    assert lines[1].startswith("baumhash: "), lines[1]
    return int(lines[0].removeprefix("dateien: ")), lines[1].removeprefix("baumhash: ")


def stage_a_tree(root: Path, line_ending: bytes) -> None:
    """Three python files over two levels, written with the ending that is asked for."""
    (root / "paket").mkdir(parents=True)
    first = line_ending.join([b"# the head of the file", b"value = 1", b""])
    second = line_ending.join([b"value = 2", b""])
    (root / "eins.py").write_bytes(first)
    (root / "paket" / "zwei.py").write_bytes(first)
    (root / "paket" / "drei.py").write_bytes(second)


def test_the_recipe_ignores_the_line_ending_of_every_file(tmp_path: Path) -> None:
    """The whole reason the recipe normalises: the tree comes from Windows.

    The working tree of this project is checked out with core.autocrlf enabled,
    so the same commit carries CRLF here and LF in the image. Without the
    normalisation the proof of equal state would report two different hashes for
    one state, which is worse than no proof at all.
    """
    crlf = tmp_path / "crlf"
    lf = tmp_path / "lf"
    stage_a_tree(crlf, b"\r\n")
    stage_a_tree(lf, b"\n")

    crlf_count, crlf_hash = reading(run_the_recipe(crlf, "**/*.py"))
    lf_count, lf_hash = reading(run_the_recipe(lf, "**/*.py"))

    assert crlf_count == lf_count == 3
    assert crlf_hash == lf_hash


def test_the_recipe_notices_a_single_changed_byte(tmp_path: Path) -> None:
    """A proof that survives an edited file proves nothing."""
    before = tmp_path / "before"
    after = tmp_path / "after"
    stage_a_tree(before, b"\n")
    stage_a_tree(after, b"\n")
    (after / "paket" / "drei.py").write_bytes(b"value = 3\n")

    _, before_hash = reading(run_the_recipe(before, "**/*.py"))
    _, after_hash = reading(run_the_recipe(after, "**/*.py"))

    assert before_hash != after_hash


def test_the_recipe_notices_a_renamed_file(tmp_path: Path) -> None:
    """The relative path goes into the digest, so a move is a change.

    A recipe over contents alone would call a package with two swapped module
    names the same state, and that is exactly the sort of difference that makes
    an import fail in the image and not in the tree.
    """
    before = tmp_path / "before"
    after = tmp_path / "after"
    stage_a_tree(before, b"\n")
    stage_a_tree(after, b"\n")
    (after / "paket" / "drei.py").rename(after / "paket" / "vier.py")

    before_count, before_hash = reading(run_the_recipe(before, "**/*.py"))
    after_count, after_hash = reading(run_the_recipe(after, "**/*.py"))

    assert before_count == after_count == 3
    assert before_hash != after_hash


def test_the_recipe_reproduces_the_tree_hash_of_the_python_package() -> None:
    """The figure the report quotes, measured against the tree it came from.

    This is the assertion that makes the recipe unchangeable: an improvement to
    it would yield another hash and take the comparability against 278fab52 of
    the follow up measurement with it. Two figures since 2026-09-11, split for
    the same reason the PHP pair below was: the recipe is held against the tree
    as it stands today, and the figure of the run is held against the raw file
    it was read out of.
    """
    count, hexdigest = reading(run_the_recipe(REPO_ROOT / "backend" / "src" / "findling", "**/*.py"))
    assert count == PACKAGE_FILES_TODAY
    assert hexdigest == PACKAGE_TREE_HASH_TODAY

    raw = BAUMHASH_RAW.read_text(encoding="utf-8")
    assert f"baumhash: {PACKAGE_TREE_HASH}" in raw
    assert f"dateien: {PACKAGE_FILES}" in raw
    assert PACKAGE_TREE_HASH != PACKAGE_TREE_HASH_TODAY, (
        "the two figures are the same again, so the second one has lost its reason to exist"
    )


def test_the_recipe_reproduces_the_tree_hash_of_the_php_half() -> None:
    """The other half of the state, and it is measured with the same recipe.

    Two figures since 10.09.2026, and the reason they are two is written at
    their definition. The recipe is held against the tree as it stands today,
    because a recipe held against a tree that no longer exists is held against
    nothing. The figure of the run is held against the raw data it was read
    out of, because a reported measurement figure is not rewritten when the
    code moves on: plan 11-13 built the sentence of DI-07-03 into the PHP half,
    which changed the bytes of eight of these 58 files and the count of none,
    and plan 11-11 then added two files that did not exist at all.
    """
    count, hexdigest = reading(run_the_recipe(REPO_ROOT / "php", "**/*.php"))
    assert count == PHP_FILES_TODAY
    assert hexdigest == PHP_TREE_HASH_TODAY

    # And both figures of the run against the file they were read out of, so
    # that the constants and the report cannot part company unnoticed.
    raw = BAUMHASH_RAW.read_text(encoding="utf-8")
    assert f"baumhash: {PHP_TREE_HASH}" in raw
    assert f"dateien: {PHP_FILES}" in raw
    assert PHP_TREE_HASH != PHP_TREE_HASH_TODAY, (
        "the two figures are the same again, so the second one has lost its reason to exist"
    )


def test_the_recipe_sorts_by_the_posix_path_and_not_by_the_path_object(tmp_path: Path) -> None:
    """The same content must hash the same on Windows and on the box.

    Two Path objects compare in a platform dependent form: the Windows flavour
    folds case, the posix one does not. So a root that holds both an upper case
    directory and a lower case file beside it is ordered differently on the two
    machines, and the recipe hashes the order it walks. That is not a detail. The
    tree hash is the only proof that the image and the working tree are the same
    state, and it was measured on 2026-09-09 that php came out as 26b55908... on
    Windows and 4a4c6f62... on the box while all 58 files were byte identical.
    CI on ubuntu had been red on exactly this since the recipe was added.

    Staged here with the two names that caused it, Unit/ and bootstrap, and the
    expectation is computed with the posix ordering the docstring of the recipe
    specifies, so this test fails on either platform if the sort key goes back.
    """
    root = tmp_path / "halb"
    (root / "tests" / "Unit").mkdir(parents=True)
    members = {
        "tests/Unit/AlphaTest.php": b"<?php // eins\n",
        "tests/bootstrap.php": b"<?php // zwei\n",
        "lib/Service/Beta.php": b"<?php // drei\n",
    }
    for relative, content in members.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    expected = hashlib.sha256()
    # Sorted by the string, which is what the recipe promises to hash.
    for relative in sorted(members):
        body = hashlib.sha256(members[relative]).hexdigest().encode()
        expected.update(relative.encode() + b"\0" + body + b"\n")

    count, hexdigest = reading(run_the_recipe(root, "**/*.php"))
    assert count == len(members)
    assert hexdigest == expected.hexdigest()


def test_the_recipe_refuses_a_root_that_does_not_exist(tmp_path: Path) -> None:
    """A mistyped path must not answer with a hash over nothing.

    This is the failure of both predecessors turned around. There the step
    produced no line at all and the report claimed the equality anyway, so the
    empty result has to cost an exit code.
    """
    answer = run_the_recipe(tmp_path / "nowhere", "**/*.py")
    assert answer.returncode == 2, answer
    assert "baumhash:" not in answer.stdout
    assert answer.stderr.startswith(DIAGNOSIS_PREFIX), answer.stderr


def test_the_recipe_refuses_an_empty_result_instead_of_hashing_nothing(tmp_path: Path) -> None:
    """An existing directory in which the glob matches nothing is the same mistake."""
    empty = tmp_path / "leer"
    empty.mkdir()
    answer = run_the_recipe(empty, "**/*.py")
    assert answer.returncode == 2, answer
    assert "baumhash:" not in answer.stdout
    assert answer.stderr.startswith(DIAGNOSIS_PREFIX), answer.stderr


def test_the_recipe_brings_no_third_party_library() -> None:
    """Standard library only, because it runs inside an image that is offline.

    The image is started with --network none for this step, and backend/uv.lock
    does not move for a measurement script.
    """
    outside = sorted(imported_packages(TREE_HASH.read_text(encoding="utf-8")) - set(sys.stdlib_module_names))
    assert not outside, outside


def test_the_proof_calls_the_recipe_as_an_argument_and_not_over_a_heredoc() -> None:
    """The one line that separates this step from the two empty predecessors.

    40-abbild.sh handed the recipe to the python in the image on standard input
    and forgot -i, so the interpreter read EOF and printed nothing. An argument
    needs no standard input, so the shape itself is the fix.
    """
    text = TREE_HASH_PROOF.read_text(encoding="utf-8")
    assert TREE_HASH.name in text
    assert "<<'PY'" not in text
    assert "docker cp" in text or "-v " in text


def test_the_proof_checks_its_own_raw_file_for_three_tree_hashes() -> None:
    """Nobody looked at the raw file, so the script looks at it.

    Three sections, three hashes: the package inside the image, the package in
    the working tree, and the php half. A run that produced fewer has to end with
    an error rather than with a report that quotes a blank.
    """
    text = TREE_HASH_PROOF.read_text(encoding="utf-8")
    assert "40b-baumhash.txt" in text
    assert "baumhash:" in text
    assert "baumhash-gleich" in text


# The count that guards --rm-data. Pitfall 5 of the research turned into a gate,
# and it is the one assertion of this file that was written after a run had
# already been paid for: the default counted the images of the docker hub, this
# box runs its All-in-One instance from a release channel, and so the count came
# out 0 with exactly one server running. Refusing on 0 was safe. What is not safe
# is the other direction, and it is the reason this test exists: with the second,
# hand rolled Nextcloud of 07.09. on the daemon the old pattern counted exactly
# 1 and would have let --rm-data through, in precisely the situation the count
# was put there to stop.

# The nine images that really ran on the box on 2026-09-09, read out of docker ps.
RUNNING_IMAGES_OF_THE_BOX = (
    "ghcr.io/street1983nk/findling_backend:dev",
    "registry:2",
    "ghcr.io/nextcloud-releases/aio-apache:latest",
    "ghcr.io/nextcloud-releases/aio-nextcloud:latest",
    "ghcr.io/nextcloud-releases/aio-redis:latest",
    "ghcr.io/nextcloud-releases/aio-postgresql:latest",
    "ghcr.io/nextcloud-releases/aio-harp:latest",
    "ghcr.io/nextcloud-releases/aio-notify-push:latest",
    "nextcloud/all-in-one:latest",
)
# The shape the second instance had: a hand rolled server, straight from the hub.
THE_SECOND_INSTANCE_OF_07_09 = "nextcloud:34.0.3-apache"


def server_image_pattern(script: Path) -> str:
    """The SERVER_IMAGES default of a script, as the script really carries it."""
    text = script.read_text(encoding="utf-8")
    found = re.search(r'SERVER_IMAGES="\$\{SERVER_IMAGES:-(.*?)\}"', text)
    assert found is not None, f"{script.name} carries no SERVER_IMAGES default"
    return found.group(1)


@pytest.mark.parametrize("name", ["90-bestand.sh", "92-wechsel.sh"])
def test_the_server_count_finds_the_one_instance_of_this_box(name: str) -> None:
    """One server running has to count as one, on the registry path of this box.

    Both scripts carry the same default and both gate a step on it: 90-bestand.sh
    ends the inventory with 5, and 92-wechsel.sh refuses --rm-data with 5. A
    pattern that names one registry path counts the instance of another one as
    absent.
    """
    pattern = re.compile(server_image_pattern(RUN_DIR / name))
    hits = [image for image in RUNNING_IMAGES_OF_THE_BOX if pattern.search(image)]
    assert hits == ["ghcr.io/nextcloud-releases/aio-nextcloud:latest"], hits


@pytest.mark.parametrize("name", ["90-bestand.sh", "92-wechsel.sh"])
def test_the_server_count_sees_the_second_instance_that_did_the_damage(name: str) -> None:
    """Two servers have to count as two, or the guard passes the disaster.

    On 07.09. a second, hand rolled Nextcloud on the same docker daemon ran an
    unregister --rm-data and took the volume of the FIRST one with it, because the
    volume name of an ExApp follows from its app id alone. The count exists to
    stop exactly that, so the hand rolled shape stays in the pattern next to the
    All-in-One one, and two of them must not read as one.
    """
    pattern = re.compile(server_image_pattern(RUN_DIR / name))
    images = [*RUNNING_IMAGES_OF_THE_BOX, THE_SECOND_INSTANCE_OF_07_09]
    assert len([image for image in images if pattern.search(image)]) == 2


@pytest.mark.parametrize("name", ["90-bestand.sh", "92-wechsel.sh"])
def test_the_server_count_leaves_the_companion_containers_out(name: str) -> None:
    """The other AIO containers carry the word nextcloud and are not servers.

    Counting the mastercontainer, the AppAPI daemon or the notify-push helper as
    an instance would refuse every step of this run on a box that is set up
    correctly, which is the same outage as the bug above with the sign flipped.
    """
    pattern = re.compile(server_image_pattern(RUN_DIR / name))
    for image in (
        "nextcloud/all-in-one:latest",
        "ghcr.io/nextcloud/nextcloud-appapi-harp:release",
        "ghcr.io/nextcloud-releases/aio-notify-push:latest",
        "ghcr.io/nextcloud-releases/aio-harp:latest",
        "ghcr.io/nextcloud-releases/aio-domaincheck:latest",
    ):
        assert not pattern.search(image), image


# The reader of the watchman of the full run. These assertions are pitfall 8 of
# the research turned into a gate: 42c-lesen.py of the semantic run looked for
# indexed and embedded on the top level of the recording, where the indexed of
# the PHP half stands and stays 0 by design and where embedded does not stand at
# all. The watchman logged zeroes for a whole night while the container held
# 47.000 vectors, the search load sample of the trailing run never ran because
# its condition is embedded > 200, and the end of both tracks would have been
# noticed at the round cap some nine hours late. The lesson of the research is to
# drive the reader once against a known number before the run is triggered; here
# it is five known numbers, and none of them needs a box.


def read_a_recording(recording: str) -> list[str]:
    """The reader as a subprocess, fed one recording, split like the shell does.

    Not imported, for the two reasons the recipe above gives as well: the file
    name begins with a digit and is therefore no module name, and what the
    watchman consumes is three whitespace separated words on standard output.
    """
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(READER)],
        input=recording,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert answer.returncode == 0, answer.stderr
    return answer.stdout.split()


def read_without_standard_input() -> list[str]:
    """The same call with standard input closed, which must not wait for a line."""
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(READER)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert answer.returncode == 0, answer.stderr
    return answer.stdout.split()


def a_recording(**changes: object) -> str:
    """One recording of the admin page, in the shape the observer writes it.

    The two figures under "backend" are the ones the semantic run really stood
    at while its watchman logged zeroes, so a reader that reads the wrong level
    fails against the very numbers that failure cost.
    """
    recording: dict[str, object] = {
        "at": "2026-09-09T12:00:00Z",
        "runState": "running",
        "indexed": 0,
        "indexedPercent": 0,
        "embedded": 0,
        "embeddedPercent": 0,
        "scheduled": 1200,
        "running": 1,
        "backendReachable": True,
        "backend": {"indexed": 47000, "embedded": 12000},
    }
    recording.update(changes)
    return json.dumps(recording)


def test_the_reader_reads_indexed_and_embedded_under_backend() -> None:
    """The one reading the whole night of the semantic run turned on."""
    assert read_a_recording(a_recording()) == ["1201", "47000", "12000"]


def test_the_reader_never_reports_the_indexed_of_the_php_half() -> None:
    """The gate that goes red the moment somebody reads the top level again.

    The recording carries an indexed of eight on the top level and no backend at
    all. A reader that falls back to the top level answers "8" here, which is the
    number of the PHP half and not of the index; the honest answer is that both
    counters are unknown. The work stock stays a number, because scheduled and
    running really do live on the top level.
    """
    without_backend: dict[str, object] = json.loads(a_recording())
    del without_backend["backend"]
    without_backend["indexed"] = 8
    assert read_a_recording(json.dumps(without_backend)) == ["1201", "unklar", "unklar"]


def test_the_reader_answers_unklar_three_times_for_every_unusable_recording() -> None:
    """Not known and zero are two different answers, and the watchman acts on both.

    Three shapes of nothing: no line at all, because the observer has not written
    one yet; a line that is not JSON, because a recording can be cut in half by a
    kill; and a recording that carries the error key of a failed request, which
    is the shape the observer writes rather than leaving a gap.
    """
    assert read_a_recording("") == ["unklar", "unklar", "unklar"]
    assert read_a_recording('{"scheduled": 3, "runni') == ["unklar", "unklar", "unklar"]
    error = json.dumps({"at": "2026-09-09T12:00:00Z", "fehler": "HTTPError"})
    assert read_a_recording(error) == ["unklar", "unklar", "unklar"]


def test_the_reader_adds_scheduled_and_running_to_the_work_stock() -> None:
    """The stock is the sum of the two, and an empty stock is a zero and not a gap."""
    assert read_a_recording(a_recording(scheduled=3, running=1))[0] == "4"
    assert read_a_recording(a_recording(scheduled=0, running=0))[0] == "0"
    # Neither of the two is a number: an assumed zero here would let the watchman
    # declare the end of a run whose stock it never saw.
    assert read_a_recording(a_recording(scheduled=None, running=None))[0] == "unklar"


def test_the_reader_does_not_block_without_standard_input() -> None:
    """A reader that waits for a line it will never get hangs the whole watchman."""
    assert read_without_standard_input() == ["unklar", "unklar", "unklar"]


def observer_module() -> ModuleType:
    """The observer, loaded from its path under a name that is a valid module name.

    Loaded rather than run, because the projection of one answer into one
    recording is the part of it that can be held to a promise without an
    instance to log in to.
    """
    specification = importlib.util.spec_from_file_location("statusbeobachter", OBSERVER)
    assert specification is not None, OBSERVER
    assert specification.loader is not None, OBSERVER
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_the_recording_of_the_observer_carries_no_name_carrier() -> None:
    """T-10-21: the admin page knows example paths, and this file is checked in.

    The answer staged here carries three of them, in the three places the page
    really puts them: the error list of the container, the examples of the
    coverage block and an error list on the top level. None of the three may
    reach the recording, and the way that is kept is a projection onto a closed
    set of keys rather than a list of keys to drop.
    """
    module = observer_module()
    answer = {
        "at": "2026-09-09T11:59:00Z",
        "runState": "running",
        "indexed": 5,
        "indexedPercent": 1,
        "embedded": 3,
        "embeddedPercent": 1,
        "scheduled": 7,
        "running": 1,
        "backendReachable": True,
        "backend": {
            "indexed": 47000,
            "embedded": 12000,
            "errors": [{"path": "corpus/09-bescheid.pdf", "reason": "ocr_failed"}],
        },
        "coverage": {"examples": ["lasttest/files/loadtest/000001.pdf"]},
        "errorList": [{"path": "/lasttest/files/geheim.pdf", "fileid": 4711}],
    }

    recording = module.recording_of(answer)

    assert set(recording) == set(RECORDING_KEYS)
    assert set(recording["backend"]) == set(BACKEND_RECORDING_KEYS)
    text = json.dumps(recording)
    assert ".pdf" not in text
    assert "lasttest" not in text
    assert "/" not in text
    # The figures themselves have to survive the projection, or the observer
    # would be safe and useless at the same time.
    assert recording["backend"] == {"indexed": 47000, "embedded": 12000}
    assert recording["scheduled"] == 7
    assert recording["runState"] == "running"


def test_the_observer_writes_an_error_recording_instead_of_a_gap() -> None:
    """A failed request has to be visible in the row, because a gap is not.

    The watchman reads the last line and only the last line. An answer that is
    not the shape of the overview must therefore produce a recording with the
    error key, which is exactly what the reader above turns into three times
    unklar, and never a line that looks like a measurement.
    """
    module = observer_module()

    recording = module.recording_of("<html>a login form</html>")

    assert "fehler" in recording
    assert set(recording) <= set(RECORDING_KEYS) | {"fehler"}
    assert "indexed" not in recording


# The wide scope. Every .py and .sh under docs/measurements/**/skripte/, read out
# of the directories rather than out of a list of file names: a gate over a list
# covers the files somebody remembered to add to it, and the next measurement
# brings a directory rather than an entry.


def measurement_scripts() -> list[Path]:
    """Every script of every measurement this repository holds."""
    return sorted(path for path in MEASUREMENTS_DIR.glob("**/skripte/*") if path.suffix in SCRIPT_SUFFIXES)


def scripts_of_this_run() -> list[Path]:
    """Every script of the run directories written under these rules.

    Four directories since plan 16-03. The successor fassung of the language
    cases lives in one of its own since plan 11-03, and the three promises below
    have to reach it: it creates an account, it reads a password and it is
    copied onto the same box as the rest. The run directory of v1.2 came third,
    for the probe that counts the foreign stock inside the container. The run
    directory of the successor fassungen of A1 came fourth, and the reason is
    99d-filter-sortierung.sh: the whole subject of that file is where its
    password comes from, so the promise that none of them stands on a command
    line is the one that has to reach it.
    """
    return sorted(
        path for directory in NARROW_SCOPE_DIRS for path in directory.glob("*") if path.suffix in SCRIPT_SUFFIXES
    )


def carriage_returns_in(raw: bytes) -> int:
    """How many carriage returns the bytes carry, which has to be none.

    A CR behind the shebang makes the kernel look for an interpreter whose name
    ends in an invisible character, and the error message does not name it.
    """
    return raw.count(b"\r")


def dashes_in(text: str) -> list[str]:
    """Every forbidden dash the text carries, sorted, empty when it carries none."""
    return sorted(dash for dash in DASHES if dash in text)


def machine_shapes_in_code(text: str) -> list[str]:
    """Every machine shape the text carries in code, sorted.

    A shape inside a comment is prose and stays allowed, and so is a variable
    default with a comment over it. Those are the two places a path of the box may
    be named: one explains, the other can be changed without reading the body.
    Anywhere else it is a tool that measures one machine and cannot be pointed at
    another, which is the lesson 45-suchlast.py cost.
    """
    lines = text.splitlines()
    found: set[str] = set()
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#") or _is_a_commented_default(lines, index):
            continue
        found.update(shape for shape in MACHINE_SHAPES if shape in line)
    return sorted(found)


def _is_a_commented_default(lines: list[str], index: int) -> bool:
    """A variable default whose nearest non empty line above it is a comment."""
    if not DEFAULT_ASSIGNMENT.match(lines[index].strip()):
        return False
    for earlier in reversed(lines[:index]):
        stripped = earlier.strip()
        if stripped:
            return stripped.startswith("#")
    return False


def passwords_on_a_command_line(text: str) -> list[str]:
    """Every shape that hands a password to an argument, sorted.

    Found while writing this gate: the naive short form fired on mkdir -p "$OUT"
    of the very script it was written for. A false positive on the most common
    option in shell scripting is not a strict gate, it is one that gets deleted,
    so the short form was narrowed to the programs it means something for.
    """
    found = [shape for shape in PASSWORD_OPTIONS if shape in text]
    if PASSWORD_SHORT_FORM.search(text):
        found.append(SHORT_FORM_NAME)
    return sorted(found)


@pytest.fixture(params=measurement_scripts(), ids=lambda path: f"{path.parent.parent.name}/{path.name}")
def measurement_script(request: pytest.FixtureRequest) -> Path:
    return Path(request.param)


@pytest.fixture(params=scripts_of_this_run(), ids=lambda path: f"{path.parent.parent.name}/{path.name}")
def script_of_this_run(request: pytest.FixtureRequest) -> Path:
    return Path(request.param)


def test_the_wide_scope_covers_every_measurement_and_skips_what_is_not_a_script() -> None:
    """The gate reads directories, so this says which ones it found.

    Four runs have scripts today. The assertion is a floor and not an equality,
    because the next measurement is supposed to be picked up without an edit
    here, and the named file is the one that proved the suffix filter is needed.
    """
    found = measurement_scripts()
    directories = {path.parent.parent.name for path in found}
    assert directories >= {
        "2026-09-05-semantiklauf-m7g",
        "2026-09-grundlast-fein",
        "2026-09-nachmessung-m7g",
        "2026-09-vergleichsmessung-m7g",
    }
    assert not [path for path in found if path.name == ".claude-active"]
    assert TREE_HASH in found
    assert TREE_HASH_PROOF in found


def test_the_measurement_script_carries_no_carriage_return(measurement_script: Path) -> None:
    """Read as bytes, because a carriage return hides in a text read.

    True for the whole stock since plan 10-01: five files were renormalised and
    .gitattributes now carries the rule that keeps the next checkout from putting
    them back.
    """
    assert carriage_returns_in(measurement_script.read_bytes()) == 0, measurement_script.name


def test_the_measurement_script_carries_no_dash(measurement_script: Path) -> None:
    """The typography rule of this project, over the whole stock."""
    text = measurement_script.read_text(encoding="utf-8")
    assert dashes_in(text) == [], measurement_script.name


def test_the_script_of_this_run_starts_with_a_shebang(script_of_this_run: Path) -> None:
    """It is started on the box as ./<name>, so the first line decides."""
    raw = script_of_this_run.read_bytes()
    assert raw.startswith(SHEBANGS), (script_of_this_run.name, raw[:40])


def test_the_script_of_this_run_carries_no_path_of_one_machine(script_of_this_run: Path) -> None:
    """A tool with a machine path in it is a tool for one machine."""
    text = script_of_this_run.read_text(encoding="utf-8")
    assert machine_shapes_in_code(text) == [], script_of_this_run.name


def test_the_script_of_this_run_puts_no_password_on_a_command_line(script_of_this_run: Path) -> None:
    """An argument stands in the process list, and a log keeps it (T-10-03)."""
    text = script_of_this_run.read_text(encoding="utf-8")
    assert passwords_on_a_command_line(text) == [], script_of_this_run.name


def test_the_machine_shapes_come_from_the_gate_of_scripts_ops() -> None:
    """One definition for both gates, and this says what it currently reads.

    The list lives in test_ops_scripts.py and is read from there. This assertion
    pins what was read, so that widening or narrowing it over there is a decision
    somebody makes here as well instead of a side effect.
    """
    assert MACHINE_SHAPES == ("/home/", "sys.path.insert", "sys.path.append", "drillhelfer")


def test_the_carriage_return_gate_fires_on_a_staged_sample() -> None:
    """A gate whose only assertion is that today is fine stays green when it dies.

    The sample is the shape the five renormalised files had: a shebang that ends
    in a carriage return, which is the failure this whole rule is about.
    """
    staged = b"#!/usr/bin/env python3\r\nprint('hi')\r\n"
    assert carriage_returns_in(staged) == 2
    assert carriage_returns_in(b"#!/usr/bin/env python3\nprint('hi')\n") == 0


def test_the_dash_gate_fires_on_a_staged_sample() -> None:
    """Both dashes, assembled from code points so the sample is not the file."""
    staged = f"# a comment with an em dash {chr(0x2014)} in it\n"
    assert dashes_in(staged) == [chr(0x2014)]
    assert dashes_in(f"# and an en dash {chr(0x2013)} in this one\n") == [chr(0x2013)]
    assert dashes_in("# a comment with a plain hyphen - in it\n") == []


def test_the_machine_path_gate_fires_on_a_staged_sample() -> None:
    """The sample is 45-suchlast.py of the semantic run, in three lines.

    That file is why the narrow scope is narrow, and it is why the gate exists:
    it reached its helper through a directory of the load test box and became a
    tool that could not be pointed anywhere else.
    """
    staged = 'import sys\nsys.path.insert(0, "/home/ubuntu/work")\nfrom drillhelfer import suche\n'
    assert machine_shapes_in_code(staged) == ["/home/", "drillhelfer", "sys.path.insert"]

    # The two places the same shape stays allowed, and they have to stay allowed,
    # or the only way to name the box would be to hide it.
    assert machine_shapes_in_code("# the box keeps the repository under /home/ubuntu/work\n") == []
    assert machine_shapes_in_code('# the default of the box\nREPO="${REPO:-/home/ubuntu/work}"\n') == []
    # The same default without the comment over it is not exempt.
    assert machine_shapes_in_code('REPO="${REPO:-/home/ubuntu/work}"\n') == ["/home/"]


def test_the_password_gate_fires_on_a_staged_sample() -> None:
    """The three forbidden shapes, the way through, and the false positive.

    The last two lines are the ones that matter as much as the first three: the
    permitted --password-env must not be caught, and neither must mkdir -p, which
    is what the first draft of this gate did to the script it was written for.
    """
    assert passwords_on_a_command_line("occ user:resetpassword lasttest --password secret\n") == ["--password "]
    assert passwords_on_a_command_line("occ user:resetpassword --password=secret\n") == ["--password="]
    assert passwords_on_a_command_line('mysql -p "$PW" -e "select 1"\n') == [SHORT_FORM_NAME]

    assert passwords_on_a_command_line("search_load.py --password-env LASTTEST_PW\n") == []
    assert passwords_on_a_command_line('mkdir -p "$OUT"\n') == []


# The watchman over the driven fassung of the language cases, and the promises
# of its successor. Plan 11-03, deferred item DI-10-02.
#
# The rule these assertions defend was prose until now: a script under
# docs/measurements/<lauf>/skripte/ is the fassung that really ran, and the raw
# data next to it are only worth as much as the certainty that the two belong
# together. 98-sprachfaelle.sh of 10.09.2026 is the file that produced the
# balance line "sprachfaelle bestanden 6 von 10", and correcting it in place
# would have left that line standing next to a script that never produced it.


def test_the_narrow_scope_covers_the_four_run_directories_written_under_these_rules() -> None:
    """Widening the narrow scope is a decision, so it is pinned here.

    The semantic run of 05.09. stays outside on purpose (45-suchlast.py reaches
    its helper through a directory of the box), and the run directory of the
    tool fixes joined in plan 11-03 because its script is new and can keep all
    three promises. The run directory of v1.2 joined in plan 12-04 for the same
    reason, and its probe is named here so that the widening is checked against
    a file rather than against a directory that may still be empty. The run
    directory of the successor fassungen joined in plan 16-03, and both of its
    files are named here for that same reason.
    """
    assert NARROW_SCOPE_DIRS == (RUN_DIR, FIX_RUN_DIR, V12_RUN_DIR, SUCCESSOR_RUN_DIR)
    found = scripts_of_this_run()
    assert SUCCESSOR_LANGUAGE_CASES in found
    assert DRIVEN_LANGUAGE_CASES in found
    assert STOCK_PROBE in found
    assert SUCCESSOR_IMAGE_SWITCH in found
    assert SUCCESSOR_FILTER_SORT in found
    assert not [path for path in found if path.parent.parent.name == "2026-09-05-semantiklauf-m7g"]


def test_the_driven_language_case_script_stays_byte_identical() -> None:
    """The fassung of 10.09.2026 is evidence, and evidence does not get edited.

    Its raw file rohdaten/98-sprachfaelle.txt carries the balance line of that
    run and the four red cases DI-10-02 is about. A correction inside this file
    would make every one of those figures a claim about a script that no longer
    exists, so the fix of DI-10-02 is a new file in a new run directory and this
    digest is what keeps it that way.
    """
    assert DRIVEN_LANGUAGE_CASES.is_file(), DRIVEN_LANGUAGE_CASES
    raw = DRIVEN_LANGUAGE_CASES.read_bytes()
    assert len(raw) == DRIVEN_LANGUAGE_CASES_BYTES, DRIVEN_FASSUNG_RULE
    assert hashlib.sha256(raw).hexdigest() == DRIVEN_LANGUAGE_CASES_SHA256, DRIVEN_FASSUNG_RULE


def test_the_successor_language_case_script_stays_byte_identical() -> None:
    """The second driven fassung is evidence too, and it did not carry a digest until now.

    98b-sprachfaelle.sh ran on 10.09.2026 and wrote rohdaten/98b-sprachfaelle.txt
    beside itself, the raw file DI-10-02 and DI-11-01 are read out of. The
    correction of this phase is therefore 98c in a new run directory and not a
    change inside 98b, exactly as the rule below says, and this digest is what
    keeps the difference between the two from being a matter of good intentions.
    """
    assert SUCCESSOR_LANGUAGE_CASES.is_file(), SUCCESSOR_LANGUAGE_CASES
    raw = SUCCESSOR_LANGUAGE_CASES.read_bytes()
    assert len(raw) == SUCCESSOR_LANGUAGE_CASES_BYTES, DRIVEN_FASSUNG_RULE
    assert hashlib.sha256(raw).hexdigest() == SUCCESSOR_LANGUAGE_CASES_SHA256, DRIVEN_FASSUNG_RULE


def test_the_watchman_of_the_driven_fassung_fires_on_a_single_added_character() -> None:
    """A watchman whose only assertion is that today is fine stays green when it dies.

    The staged sample is the smallest edit somebody could make to that file, a
    single character, and the digest has to notice it. Measured against the real
    bytes rather than against an invented sample, because what is being shown
    here is that THIS digest separates THIS file from a changed one.
    """
    raw = DRIVEN_LANGUAGE_CASES.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == DRIVEN_LANGUAGE_CASES_SHA256
    assert hashlib.sha256(raw + b" ").hexdigest() != DRIVEN_LANGUAGE_CASES_SHA256
    assert hashlib.sha256(raw.replace(b"set -eu", b"set -e", 1)).hexdigest() != DRIVEN_LANGUAGE_CASES_SHA256


def test_the_successor_points_at_the_driven_fassung_and_lives_beside_it() -> None:
    """The successor names its original, and it does not lie in the same directory."""
    text = SUCCESSOR_LANGUAGE_CASES.read_text(encoding="utf-8")
    assert "2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh" in text
    assert "DI-10-02" in text
    assert SUCCESSOR_LANGUAGE_CASES.parent != DRIVEN_LANGUAGE_CASES.parent
    # The one sentence of the finding, in the words of the deferred item: the
    # account separates the permission and not the index.
    assert "PERMISSION and not the INDEX" in text


def test_the_successor_checks_the_foreign_stock_before_the_first_case() -> None:
    """The order of the two verdicts is the fix, so the order is asserted.

    A pre check that ran after the cases would produce the same figures and none
    of the meaning: the point is that a case which cannot carry a statement is
    never given one.
    """
    text = SUCCESSOR_LANGUAGE_CASES.read_text(encoding="utf-8")
    vorpruefung = text.index("Abschnitt 0: die Vorpruefung des Fremdbestands")
    erster_fall = text.index("\n    FALL=1\n")
    assert vorpruefung < erster_fall
    # Every case asks the pre check first, and there are ten of them.
    assert text.count("if messbar ") == 10
    assert "fremdbestand %s %s (Seite der Faelle)" in text


def test_the_successor_judges_three_valued_and_balances_with_two_figures() -> None:
    """GRUEN, ROT and NICHT MESSBAR, and a balance line that carries both counts.

    The last assertion is the one DI-10-02 asks for by name: the line the run of
    10.09. printed carried a single figure, and a single figure is exactly the
    misreading that turned four unmeasurable cases into four red ones.
    """
    text = SUCCESSOR_LANGUAGE_CASES.read_text(encoding="utf-8")
    assert "NICHT MESSBAR (Fremdbestand %s Treffer)" in text
    assert "sprachfall %s GRUEN" in text
    assert "sprachfall %s ROT:" in text
    assert "sprachfaelle bestanden %s von 10, davon %s nicht messbar" in text
    # The count of cases and the count of assertions stay two different numbers,
    # which is the reading plan 10-04 settled on.
    assert "rote faelle %s, nicht messbare faelle %s, rote zusicherungen %s" in text
    # A run whose CI proof is missing must not be able to say so in a raw file
    # and carry on; it ends instead, so the word of that note has no place left.
    assert "unbekannt" not in text


def test_the_successor_keeps_the_defaults_the_box_plan_hands_over() -> None:
    """Changed defaults would cost the comparability with the original.

    Plan 11-06 hands over FRIST=60 RUNDEN=10, so both stay variables with the
    defaults of the driven fassung. The threshold of the foreign stock is the
    ceiling on examined candidates of php/lib/Search/Provider.php, and it is a
    variable for the same reason: a figure a reader can change without reading
    the body.
    """
    text = SUCCESSOR_LANGUAGE_CASES.read_text(encoding="utf-8")
    for default in ('FRIST="${FRIST:-360}"', 'RUNDEN="${RUNDEN:-40}"', 'RUNDENFRIST="${RUNDENFRIST:-60}"'):
        assert default in text, default
    assert 'FREMD_SCHWELLE="${FREMD_SCHWELLE:-64}"' in text
    assert 'FREMD_TIEFE="${FREMD_TIEFE:-64}"' in text
    # The ceiling the threshold is taken from, read out of the PHP side so that
    # the derivation in the head cannot quietly stop being true.
    provider = (REPO_ROOT / "php" / "lib" / "Search" / "Provider.php").read_text(encoding="utf-8")
    assert "MAX_RECHECKS_ABSOLUTE = 64;" in provider


def a_run_of_the_successor(out: Path, ci_lauf: str | None) -> subprocess.CompletedProcess[str]:
    """The successor as a program, with the run number set, empty or absent.

    Run rather than read, because the refusal is half of what this script
    promises and because a POSIX shell is the only reader that can tell whether
    the head of the file survives a shell that is not bash. It never reaches a
    network call: the run number is checked before anything else happens.
    """
    shell = shutil.which("sh")
    assert shell is not None
    environment = {**os.environ, "OUT": out.as_posix(), "PWFILE": (out / "kein-passwort").as_posix()}
    for name in ("CI_LAUF", "FINDLING_LOAD_PASSWORD"):
        environment.pop(name, None)
    if ci_lauf is not None:
        environment["CI_LAUF"] = ci_lauf
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shell, SUCCESSOR_LANGUAGE_CASES.as_posix()],
        # Closed on purpose: the pre check reads the load test password with
        # sudo, and a sudo that finds a terminal would ask for a password and
        # hang this test instead of failing it.
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=environment,
    )


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("ci_lauf", [None, "", "   ", "letzter", "34339346666x"])
def test_the_successor_refuses_a_run_without_a_ci_run_number(tmp_path: Path, ci_lauf: str | None) -> None:
    """No run number, no run, and the refusal comes before the first case.

    Five shapes of nothing, because the note of 10.09. came out of exactly one
    of them: the variable was never set. An empty value, a blank one and a value
    that is no run number have to end the same way, or the required input would
    be a required input in name only. The raw file must not even be created:
    a run that ended before its first measurement has nothing to write down.
    """
    answer = a_run_of_the_successor(tmp_path, ci_lauf)
    assert answer.returncode == 22, answer
    assert "integration.yml" in answer.stderr
    assert "98b-sprachfaelle:" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(
    shutil.which("sh") is None or shutil.which("jq") is None,
    reason="no POSIX shell or no jq on this machine",
)
def test_the_successor_stops_when_the_foreign_stock_cannot_be_asked(tmp_path: Path) -> None:
    """The other side of the refusal, and the second fail closed path.

    A gate that fires on everything proves nothing about the input it is meant
    to accept, so this run hands over a real run number and gets past the first
    check. What it does not get is the password of the load test account: the
    file PWFILE points at does not exist. Without it the pre check cannot ask
    how much foreign stock stands in front of each term, and a verdict without
    that number is the two valued verdict of 10.09. all over again. The run
    therefore ends with 19, before the 39 files are uploaded, and it says so in
    its own raw file.
    """
    answer = a_run_of_the_successor(tmp_path, "34339346666")
    assert answer.returncode == 19, answer
    assert "CI_LAUF" not in answer.stderr
    raw = (tmp_path / "05-sprachfaelle.txt").read_text(encoding="utf-8")
    assert "ci-beleg: integration.yml Lauf 34339346666" in raw
    assert "Abschnitt 0: die Vorpruefung des Fremdbestands" in raw
    # It ended before the account section, so nothing on any box was touched.
    assert "Section 1: the account" not in raw


def a_boxless_run(
    script: Path,
    out: Path,
    arguments: list[str],
    ci_lauf: str | None = None,
    umgebung: dict[str, str | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    """A v1.2 script as a program, without a box, a container or a network.

    Run rather than read, for the same reason as a_run_of_the_successor: the
    refusal is half of what these scripts promise, and a POSIX shell is the
    only reader that can tell whether the head of the file survives a shell
    that is not bash. Neither refusal under test reaches a sudo, a docker or a
    curl call, so no box is needed and none must be reachable.
    """
    shell = shutil.which("sh")
    assert shell is not None
    environment = {**os.environ, "OUT": out.as_posix()}
    environment.pop("CI_LAUF", None)
    if ci_lauf is not None:
        environment["CI_LAUF"] = ci_lauf
    # A name whose value is None is REMOVED rather than set to an empty string.
    # The two are different inputs: the image switch refuses both, and a helper
    # that could only produce one of them would test one of them.
    for name, wert in (umgebung or {}).items():
        if wert is None:
            environment.pop(name, None)
        else:
            environment[name] = wert
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shell, script.as_posix(), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=environment,
    )


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("ci_lauf", [None, "", "   ", "letzter", "34339346666x"])
def test_the_v12_fassung_refuses_a_run_without_a_ci_run_number(tmp_path: Path, ci_lauf: str | None) -> None:
    """The v1.2 fassung keeps the exit 22 contract of 98b, checked as behaviour.

    The five shapes of nothing are the ones the 98b test pins, because the
    contract is the same on purpose: no run number, no run, no raw file, and
    the refusal comes before the first sudo, docker or curl call. Had this
    test existed for 98c from the start, the missing early abort of section 0
    would have stood out as a deviation from the 98b pattern (CR-01 of the
    phase 12 review), which is why the refusal paths are tested and not only
    the text gates.
    """
    answer = a_boxless_run(V12_LANGUAGE_CASES, tmp_path, [], ci_lauf)
    assert answer.returncode == 22, answer
    assert "integration.yml" in answer.stderr
    assert "98c-sprachfaelle:" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("zweig", [None, "", "beides", "nachher"])
def test_the_cron_precheck_refuses_a_run_without_a_known_branch(tmp_path: Path, zweig: str | None) -> None:
    """No branch, no run: the usage contract of 97, checked as behaviour.

    The branch decides which of the two halves runs, and a run without a
    protocolled interval counts as incomplete (D-07), so an absent, an empty
    and an unknown branch all end with 2 and the usage on stderr, before
    anything is measured and before any file is written.
    """
    arguments = [] if zweig is None else [zweig]
    answer = a_boxless_run(V12_CRON_PRECHECK, tmp_path, arguments)
    assert answer.returncode == 2, answer
    assert "Benutzung: 97-cron-vorpruefung.sh" in answer.stderr
    assert "vorher" in answer.stderr
    assert "waehrend" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


# The refusal paths of the rewarm measurement of step 8. Plan 15-03.
#
# Section 7.1 of the runbook says no tool is changed during the paid trip, so
# the three aborts of this one have to be shown before the box stands. Two of
# the three need a container to fire; what holds without one is where they
# stand, and that is the half that was wrong in v1.1: an abort inside the block
# leaves the subshell only, and the refusal becomes a line in a raw file nobody
# reads.


def the_two_halves_of(text: str) -> tuple[str, str]:
    """The code above and below the tee pipeline, comments removed.

    The comments have to go before anything is counted. The head of the file
    explains the rule this gate defends and names the exit codes while doing
    it, so a gate that read them would be red at exactly the paragraph that
    exists to keep it green. That is the trap aria-current fell into in plan
    13-09, and it is cheaper to remember it here than to debug it again.
    """
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    above, marker, below = code.partition(PIPELINE_CUT)
    return above, below if marker else ""


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("auspraegung", [None, "", "   ", "0", "5", "eins"])
def test_the_rewarm_tool_refuses_a_run_without_a_known_auspraegung(tmp_path: Path, auspraegung: str | None) -> None:
    """No auspraegung, no run, no raw file, and no foreign call before that.

    The six shapes of nothing are the ones the two refusals above pin, and the
    promise is the same one: the decision is taken before the first sudo, the
    first docker and the first curl, so this runs on a machine with no box
    behind it. It matters more here than in the other two, because one run of
    this tool is one branch of an A/B comparison: a run that started on the
    wrong number would produce a raw file whose figures belong to neither half.
    """
    arguments = [] if auspraegung is None else [auspraegung]
    answer = a_boxless_run(V12_REWARM, tmp_path, arguments)
    assert answer.returncode == 2, answer
    assert "Benutzung: 95b-wiederaufwaermen.sh" in answer.stderr
    for erlaubt in ("1", "2", "3", "4"):
        assert erlaubt in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_rewarm_tool_names_its_three_abort_paths_below_the_pipeline() -> None:
    """Where an abort stands decides whether it is an abort at all.

    The return code of a pipeline that ends in tee belongs to tee. An exit
    inside the block would leave the subshell, tee would end with nought, and
    the run would look green with its refusal printed in the raw file. So the
    three aborts are read out of work files below the cut, and this gate holds
    the position rather than the presence.
    """
    text = V12_REWARM.read_text(encoding="utf-8")
    above, below = the_two_halves_of(text)
    assert below, "the file does not carry the tee pipeline this gate cuts at"
    for abort in REWARM_ABORTS:
        assert abort in below, abort
        assert abort not in above, abort

    # The staged probe, because a gate whose only assertion is that today is
    # fine stays green when it dies: an abort inside the block is found above
    # the cut, which is what would make the three assertions above red.
    staged = f'    echo "es ging schief"\n    exit 29\n{PIPELINE_CUT}\nexit 30\n'
    staged_above, staged_below = the_two_halves_of(staged)
    assert "exit 29" in staged_above
    assert "exit 29" not in staged_below
    # And the comment that explains the rule does not count as an abort.
    commented_above, commented_below = the_two_halves_of(f"#   exit 29 die fehlende Pflichtzeile\n{PIPELINE_CUT}\n")
    assert "exit 29" not in commented_above
    assert "exit 29" not in commented_below


def test_the_rewarm_tool_reads_the_semantic_side_at_the_user_route() -> None:
    """The one trap of step 8 that produces a figure instead of an error.

    After a release the diagnosis route reports a full semantic side because it
    loads, and the user routes report an empty one at the same moment because
    they are not allowed to load. Whoever mixes the two measures two different
    things and calls them one figure. So the tool asks the OCS route, and the
    diagnosis route appears in it as a search pattern over docker logs only,
    which is the watchman of return code 30 and not a source of figures.
    """
    text = V12_REWARM.read_text(encoding="utf-8")
    assert USER_SEARCH_ROUTE in text
    diagnosis_lines = [line for line in text.splitlines() if DIAGNOSIS_ROUTE in line]
    assert diagnosis_lines, DIAGNOSIS_ROUTE
    assert all("docker logs" in line for line in diagnosis_lines), diagnosis_lines


def test_the_rewarm_tool_writes_the_mandatory_switch_line() -> None:
    """A run without the position of the switch is incomplete, not wrong.

    Section 6.4 of the runbook makes entladeschalter-ist a mandatory line for
    every measuring block, and step 8 is the one that compares two positions of
    that very switch: two figures with their positions are a comparison, two
    figures without them are two figures. The rest period joins it, because the
    trip drives 120 s instead of the 900 s of the proposed value (D-02) and an
    unexplained deviation would make the two halves incomparable as well.
    """
    text = V12_REWARM.read_text(encoding="utf-8")
    assert "entladeschalter-ist" in text
    assert "ruhezeit-ist" in text
    assert "ruhezeit-abweichung-grund" in text


# The refusal paths and the measure gate of the MEM-02 block of step 8b.
# Plan 15-04.
#
# MEM-02 is the one requirement the acceptance of phase 14 left open, and it
# falls on this box or not at all. What can be held without a box is the shape
# of its tool: that it takes no argument, that it names its measure and never
# the formulation that would turn a measured saving into an invented one, that
# its four aborts stand where an abort is one, and that the two helpers it
# leans on are the same files the predecessor runs leaned on.


def lf_bytes_of(path: Path) -> bytes:
    """The bytes of a file with carriage returns folded away.

    See the comment over RSS_SAMPLER_SHA256: one of the two files under this
    gate sits in the working copy with CRLF and in the blob with LF, so a
    digest over the raw bytes would depend on the machine that took it.
    """
    return path.read_bytes().replace(b"\r\n", b"\n")


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("argument", ["vorher", "nachher", "--help", "1"])
def test_the_baseload_return_tool_refuses_any_argument(tmp_path: Path, argument: str) -> None:
    """No argument at all, and the two that look most plausible least of all.

    A second branch would be the obvious cut of this tool, and it is the wrong
    one: the difference between the two marks is a statement only inside ONE
    life of the container. Spread over two runs it would span two of them, and
    a container that was rebuilt in between starts on its base load rather than
    where the first run left off, so the figure would be a restart and not a
    release. vorher and nachher are therefore refused by name, and so is
    anything else: the refusal falls before the first sudo, the first docker and
    the first curl, and before a raw file exists.
    """
    answer = a_boxless_run(V12_BASELOAD_RETURN, tmp_path, [argument])
    assert answer.returncode == 2, answer
    assert "Benutzung: 94b-grundlast-rueckkehr.sh" in answer.stderr
    assert "Ohne Argument" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_baseload_return_tool_names_the_measure_and_never_its_opposite() -> None:
    """The measure is the tool, and the other formulation is a different figure.

    The base load of a container that has never embedded anything is already
    measured WITHOUT the model and WITHOUT the cutter, because the lazy build of
    plan 07-03 puts neither of them into the process until the first chunker
    run. A difference against that figure would subtract something that is not
    in it. So the tool has to carry the name of its measure word for word, and
    the other formulation nowhere.

    Comment lines are deliberately NOT taken out before this gate looks, which
    is the opposite of what the_two_halves_of does for the gate below. The
    forbidden formulation must not stand in an explanation either: the next
    reader quotes an explanation as a definition, and a raw file is read on its
    own, away from the document that would have put the sentence right. The
    staged probe below shows that difference instead of asserting it.
    """
    text = V12_BASELOAD_RETURN.read_text(encoding="utf-8")
    assert MEASURE_OF_MEM_02 in text
    assert FORBIDDEN_MEASURE not in text

    staged = f"# Die Gegenrichtung, also {FORBIDDEN_MEASURE} X, ist hier verboten.\n"
    assert FORBIDDEN_MEASURE in staged
    assert FORBIDDEN_MEASURE not in "".join(the_two_halves_of(staged))


def test_the_baseload_return_tool_keeps_its_four_abort_paths_below_the_pipeline() -> None:
    """Where an abort stands decides whether it is an abort at all.

    The same rule as for the rewarm tool of plan 15-03, and the same reason: the
    return code of a pipeline that ends in tee belongs to tee, so an exit inside
    the block would leave the subshell only and the run would look green with
    its refusal printed in the raw file.

    exit 2 is the one that stands ABOVE the cut, and that is not an oversight. A
    call with an argument disputes the cut of the whole tool, and a dispute must
    not write a raw file; the pipeline writes one. The same split drives
    95b-wiederaufwaermen.sh since plan 15-03.
    """
    text = V12_BASELOAD_RETURN.read_text(encoding="utf-8")
    above, below = the_two_halves_of(text)
    assert below, "the file does not carry the tee pipeline this gate cuts at"
    for abort in BASELOAD_RETURN_ABORTS:
        assert abort in below, abort
        assert abort not in above, abort
    assert "exit 2" in above
    assert "exit 2\n" not in f"{below}\n"

    # The staged probe, because a gate whose only assertion is that today is
    # fine stays green when it dies: an abort inside the block is found above
    # the cut, which is what would make the assertions above red.
    staged = f'    echo "es ging schief"\n    exit 31\n{PIPELINE_CUT}\nexit 32\n'
    staged_above, staged_below = the_two_halves_of(staged)
    assert "exit 31" in staged_above
    assert "exit 31" not in staged_below


def test_the_baseload_return_tool_calls_the_two_ops_helpers_unchanged() -> None:
    """A changed sampler makes this figure incomparable with the predecessors.

    The series of rss_sampler.sh and the headings of rss_digest.py are the
    comparison keys against the runs of v1.1 and v1.0. An adjusted helper would
    be a second object of measurement under the name of the first (T-15-11), so
    the tool names both and neither file has moved.
    """
    text = V12_BASELOAD_RETURN.read_text(encoding="utf-8")
    assert RSS_SAMPLER.name in text
    assert RSS_DIGEST.name in text
    assert hashlib.sha256(lf_bytes_of(RSS_SAMPLER)).hexdigest() == RSS_SAMPLER_SHA256, DRIVEN_FASSUNG_RULE
    assert hashlib.sha256(lf_bytes_of(RSS_DIGEST)).hexdigest() == RSS_DIGEST_SHA256, DRIVEN_FASSUNG_RULE


# The refusal paths and the two drift gates of the filter and sort block of
# step 6b. Plan 15-05.
#
# The block exists because the owner ordered it on 19.09.2026 (D-01): sorting
# on a large stock and paging under a filter, measured rather than estimated.
# Phase 13 built both and checked them on a development instance; the full
# stock of 52.111 documents lives on this one box and only for the length of
# this trip, so the tool has to be right before the first paid minute runs.
#
# Two of its failures produce a figure instead of an error, and those are the
# two the gates below defend. A measurement over the OCS route would answer the
# question unfiltered and look like a filter measurement while doing it, and a
# hand built page address without the fingerprint would measure the silent fall
# back to page 1 at 200 and fast.


def sort_mode_names_of_the_package() -> tuple[str, ...]:
    """The keys of SORT_MODES, read out of the source of the package.

    Read and not repeated: a list of three words written down in this file
    would agree with itself on the day somebody adds a fourth name to the
    product, and the measuring tool would carry a heading over figures that are
    relevance all along.
    """
    tree = ast.parse(SEARCH_MODULE.read_text(encoding="utf-8"))
    tables = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == SORT_MODES_NAME
    ]
    assert len(tables) == 1, SORT_MODES_NAME
    table = tables[0].value
    assert isinstance(table, ast.Dict), SORT_MODES_NAME
    names: list[str] = []
    for key in table.keys:
        assert isinstance(key, ast.Constant), SORT_MODES_NAME
        assert isinstance(key.value, str), SORT_MODES_NAME
        names.append(key.value)
    return tuple(names)


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("argument", ["pdf", "--help", "1"])
def test_the_filter_sort_tool_refuses_any_argument(tmp_path: Path, argument: str) -> None:
    """No argument at all, and the three that look most plausible least of all.

    A type group, a help switch and a block number are the three shapes a hand
    on the box would reach for, and all three are refused by name. The two
    blocks measure the same stock in the same warm up; a cut into two runs
    would put the figures of two stocks under one heading. The refusal falls
    before the first sudo, the first docker and the first curl, and before a
    raw file exists, which is what makes it checkable without a box.
    """
    answer = a_boxless_run(V12_FILTER_SORT, tmp_path, [argument])
    assert answer.returncode == 2, answer
    assert "Benutzung: 99c-filter-sortierung.sh" in answer.stderr
    assert "Ohne Argument" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_filter_sort_tool_knows_the_three_sort_names_and_no_fourth() -> None:
    """The tool cannot drift against the sort names of the product.

    The three names are read out of backend/src/findling/index/search.py and
    held against the one line the tool writes them down in. A fourth name in
    the tool is red, and so is a missing one: an unknown name falls back to
    relevance inside the product without saying so, so a row called after it
    would be relevance under a false heading, and a missing name would be a
    mode nobody measured on the one box that has the stock.
    """
    names = sort_mode_names_of_the_package()
    assert names == ("relevance", "newest", "oldest"), names

    text = V12_FILTER_SORT.read_text(encoding="utf-8")
    match = SORT_MODES_IN_THE_TOOL.search(text)
    assert match is not None, "the tool does not carry the one line its sort names live in"
    in_the_tool = tuple(match.group(1).split())
    assert in_the_tool == names, (in_the_tool, names)


def test_the_filter_sort_tool_pulls_the_next_link_instead_of_building_it() -> None:
    """A built address measures the fall back, not the paging.

    The result page hangs a cursor and a fingerprint on every paging step, and
    the fingerprint runs over the raw values of the address. A hand built
    address without it throws the visitor back to page 1 SILENTLY: the page
    answers 200, it is fast, and a pretty figure for a thing that never
    happened would end up in the protocol (13-08). So the tool names the markup
    of the next link and builds no address of its own beyond page 1, which is
    the only one that carries no position at all.

    Comment lines go before this gate looks, because the head of the file
    explains the rule and would otherwise be red at exactly the paragraph that
    exists to keep it green.
    """
    text = V12_FILTER_SORT.read_text(encoding="utf-8")
    assert NEXT_LINK_MARK in text
    code = "\n".join(the_two_halves_of(text))
    built = [line for line in code.splitlines() if BUILT_POSITION in line]
    assert built == [], built

    # The staged probe, because a gate whose only assertion is that today is
    # fine stays green when it dies.
    staged = 'adresse="$ADRESSE/apps/findling/?query=$BEGRIFF&' + BUILT_POSITION + '2"\n'
    staged_code = "\n".join(the_two_halves_of(staged))
    assert [line for line in staged_code.splitlines() if BUILT_POSITION in line]


def test_the_filter_sort_tool_keeps_its_abort_paths_below_the_pipeline() -> None:
    """Where an abort stands decides whether it is an abort at all.

    The same rule as for the two tools of plans 15-03 and 15-04, and the same
    reason: the return code of a pipeline that ends in tee belongs to tee, so
    an exit inside the block would leave the subshell only and the run would
    look green with its refusal printed in the raw file.

    exit 2 stands ABOVE the cut on purpose. A call with an argument disputes
    the cut of the whole tool, and a dispute must not write a raw file; the
    pipeline writes one.
    """
    text = V12_FILTER_SORT.read_text(encoding="utf-8")
    above, below = the_two_halves_of(text)
    assert below, "the file does not carry the tee pipeline this gate cuts at"
    for abort in FILTER_SORT_ABORTS:
        assert abort in below, abort
        assert abort not in above, abort
    assert "exit 2" in above

    # The staged probe, for the same reason as in the two gates above it.
    staged = f'    echo "es ging schief"\n    exit 34\n{PIPELINE_CUT}\nexit 35\n'
    staged_above, staged_below = the_two_halves_of(staged)
    assert "exit 34" in staged_above
    assert "exit 34" not in staged_below


def test_the_filter_sort_tool_never_calls_the_load_tool() -> None:
    """The load tool is calibrated and it asks a route that has no filters.

    scripts/ops/search_load.py drives the levels of step 6 and is the
    comparison key against the runs of v1.1, so it is neither changed nor
    pointed at a new question. It asks the OCS route, and the two OCS providers
    know neither types nor sort (13-12): a call from this block would measure
    unfiltered and say so nowhere, which is the one failure of step 6b that
    produces a plausible figure instead of an error (T-15-13).

    Its name may stand in the head of the tool, because a reader who wonders
    why the obvious tool is missing deserves the answer in the file. It may not
    stand anywhere a shell would read it.
    """
    text = V12_FILTER_SORT.read_text(encoding="utf-8")
    carrying = [line for line in text.splitlines() if LOAD_TOOL in line]
    assert carrying, LOAD_TOOL
    assert all(line.lstrip().startswith("#") for line in carrying), carrying


# The refusal paths and the gates of the image switch of block 13b. Plan 15-06.
#
# This is the one tool of the trip that destroys something: it runs
# unregister --rm-data, and on 07.09.2026 that switch removed the measuring
# volume of the wrong Nextcloud. Everything about it that can be held without a
# box is held here, before the box stands, because section 7.1 of the runbook
# says no tool is changed during the paid trip.


def the_three_parts_of(text: str) -> tuple[str, str, str]:
    """The code above the first pipeline, between the two, and below the second.

    The image switch carries two pipelines rather than one: phase A judges
    without touching anything and ends in a work file, phase B changes the box
    and ends in the raw file. Where an abort stands decides whether it is an
    abort at all AND whether it falls before or after the first destructive
    command, so this tool needs three parts where the others need two.

    Comment lines go first, for the reason the two part cutter above gives: the
    head of the file names every exit code while explaining it, so a gate that
    read the comments would be red at exactly the paragraph that exists to keep
    it green.
    """
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    vorlauf, erster, rest = code.partition(VORLAUF_CUT)
    if not erster:
        return code, "", ""
    mitte, zweiter, unten = rest.partition(PIPELINE_CUT)
    return vorlauf, mitte, unten if zweiter else ""


def lines_carrying(code: str, needle: str) -> list[int]:
    """The indexes of the code lines that carry a string, in the order they run."""
    return [index for index, line in enumerate(code.splitlines()) if needle in line]


def switches_that_run(code: str) -> list[int]:
    """The indexes of the code lines that really RUN unregister --rm-data.

    A line that only prints the name of the switch is not the switch. Both
    refusals of this tool quote it on stderr, because a diagnosis that does not
    name the command it refused is half a diagnosis, and counting those as
    occurrences would force a count in front of every error message.
    """
    return [
        index
        for index, line in enumerate(code.splitlines())
        if THE_DANGEROUS_SWITCH in line and not line.strip().startswith(("echo", "printf"))
    ]


def switches_without_their_count(code: str) -> list[int]:
    """Every run of the switch that has no count of the instances right above it."""
    counts = lines_carrying(code, THE_COUNT_BEFORE_RM_DATA)
    found: list[int] = []
    for switch in switches_that_run(code):
        above = [count for count in counts if count < switch]
        if not above or switch - max(above) > THE_COUNT_IS_IMMEDIATE:
            found.append(switch)
    return found


def aborts_of(part: str) -> set[str]:
    """Every exit of a part of the code, read line by line.

    Line by line rather than by substring: exit 2 is a substring of exit 29 and
    of exit 22, and a gate that read it as one would be green for a file that
    carries neither.
    """
    return {line.strip() for line in part.splitlines() if line.strip().startswith("exit ")}


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("digest", [None, ""])
def test_the_image_switch_refuses_a_run_without_a_digest(tmp_path: Path, digest: str | None) -> None:
    """No digest, no run, no raw file, and no foreign call before that.

    The two shapes of nothing are the absent variable and the empty one, and
    both have to end the same way or the required input would be required in
    name only.

    The reason there is no default at all is the moving pointer. :dev moves
    with every green run of the image pipeline, and the path filter of
    docker.yml reaches into backend/**, so a new test file in this very
    directory moves the digest without changing a line of the image. A report
    that names :dev names no state, and a default in this variable would
    quietly decide what the trip measures.
    """
    answer = a_boxless_run(V12_IMAGE_SWITCH, tmp_path, [], umgebung={REQUIRED_DIGEST: digest})
    assert answer.returncode == 2, answer
    assert REQUIRED_DIGEST in answer.stderr
    assert "Benutzung:" in answer.stderr
    assert answer.stdout == ""
    assert list(tmp_path.iterdir()) == []


def test_the_image_switch_counts_the_nextclouds_before_every_rm_data() -> None:
    """The most dangerous line of the whole trip cannot stand without its count.

    On 07.09.2026 a second, hand rolled Nextcloud on the same docker daemon ran
    unregister --rm-data and took the volume of the FIRST one with it, because
    the volume name of an ExApp follows from its app id alone. The count exists
    to stop exactly that, and this gate holds its POSITION: every line that
    carries the switch has a CALL of the count above it, in the order the file
    runs. A second --rm-data added later without a count of its own turns this
    red, which is the case the gate is written for.

    The call and not the definition, because a file that defines the count and
    never runs it would otherwise pass. The pattern of the count is asserted
    against the driven fassung as well: the default was corrected at the box on
    09.09.2026 after it had counted 0 servers with exactly one running, and a
    successor that quietly carried a different pattern would count the hand
    rolled shape of 07.09. as absent.
    """
    text = V12_IMAGE_SWITCH.read_text(encoding="utf-8")
    code = "\n".join(the_three_parts_of(text))
    assert switches_that_run(code), THE_DANGEROUS_SWITCH
    assert lines_carrying(code, THE_COUNT_BEFORE_RM_DATA), THE_COUNT_BEFORE_RM_DATA
    assert switches_without_their_count(code) == []

    assert server_image_pattern(V12_IMAGE_SWITCH) == server_image_pattern(DRIVEN_IMAGE_SWITCH)

    # The staged probe, and it is the real file with the real mistake in it
    # rather than an invented sample: a second switch appended below everything
    # has a count somewhere above it and none immediately above it, which is
    # exactly the shape that would pass a gate asking only for presence.
    staged = code + '\nocc app_api:app:unregister "$APP_ID" --rm-data\n'
    assert switches_without_their_count(staged) != []


def test_the_image_switch_reads_the_hard_limit_out_of_the_cgroup() -> None:
    """A run that measures against 4 GB while it means 2 GiB measures nothing.

    A register throws the limit away, so it is set again afterwards, and it is
    read back OUT OF THE CGROUP and never out of the docker client. The client
    answers with what it was asked to do; the cgroup answers with what
    happened. Both fields are named, memory.max and memory.swap.max, because a
    limit without the swap field is no limit on a box that has swap.
    """
    text = V12_IMAGE_SWITCH.read_text(encoding="utf-8")
    code = "\n".join(the_three_parts_of(text))
    for name in (THE_CGROUP, "memory.max", "memory.swap.max", THE_HARD_LIMIT_IN_BYTES):
        assert name in code, name
    for forbidden in THE_LIMIT_OUT_OF_THE_CLIENT:
        assert forbidden not in code, forbidden


def test_the_image_switch_expects_zero_swap_out_of_the_cgroup() -> None:
    """The swap field of a 2g/2g update reads 0, and 0 is the correct machine.

    docker update --memory=2g --memory-swap=2g names a SUM, so the swap share
    of the cgroup is 0, and the v1.1 box recorded exactly that
    (2026-09-vergleichsmessung-m7g/rohdaten/90-bestand.txt: memory.swap.max=0
    next to memory.max=2147483648). The first version of this tool expected
    the hard limit in BOTH fields and would have refused every correct
    machine with 39; found on the paid box on 2026-09-20, fixed with the
    owner's word. This test pins the repaired semantics: an own expectation
    for the swap share, defaulting to 0, and no comparison of the swap
    reading against the hard limit.
    """
    text = V12_IMAGE_SWITCH.read_text(encoding="utf-8")
    code = "\n".join(the_three_parts_of(text))
    assert 'ERWARTETER_SWAP="${ERWARTETER_SWAP:-0}"' in code
    assert '"$gemessener_swap" = "$ERWARTETER_SWAP"' in code
    assert '"$gemessener_swap" = "$ERWARTETE_GRENZE"' not in code


def test_the_image_switch_calls_the_tree_hash_as_a_script() -> None:
    """The proof is called and not rebuilt, or it proves only itself.

    40b-baumhash.sh produced the comparison figures of the predecessor runs. A
    switch that rebuilt its arithmetic as a heredoc would compute something
    that looks the same and hold it against a number it did not produce, and a
    difference between the two would read as a difference in the image.

    The second half of the gate is the absence of an own computation over the
    working tree. The sha256sum that stays is the one INSIDE the image, over
    the int8 model file, and that is a reading of the image content rather than
    a tree hash of the checkout.
    """
    text = V12_IMAGE_SWITCH.read_text(encoding="utf-8")
    code = "\n".join(the_three_parts_of(text))
    assert THE_TREE_HASH_PROOF in code
    assert 'sh "$SKRIPTE/' + THE_TREE_HASH_PROOF + '"' in code
    for line in code.splitlines():
        if "sha256sum" not in line:
            continue
        for tree in ("$REPO", "backend/src", "/php"):
            assert tree not in line, line

    # The staged probe, for the same reason as in the gate above it.
    staged = 'find "$REPO/backend/src" -name "*.py" -exec sha256sum {} +'
    assert "sha256sum" in staged
    assert "$REPO" in staged


def test_the_image_switch_keeps_its_abort_paths_below_its_pipelines() -> None:
    """Where an abort stands decides whether it is an abort at all.

    The return code of a pipeline that ends in tee belongs to tee, so an exit
    inside a block would leave the subshell only, tee would end with nought,
    and the run would look green with its refusal printed in the raw file.

    This tool has two blocks and therefore three positions. The three refusals
    of phase A stand between the two cuts, which is after their readings and
    BEFORE the first command that changes anything on the box. The two of phase
    B stand below the second cut. exit 2 stands above both on purpose: a call
    without a digest disputes the measured object itself, and a dispute must
    not write a raw file, while a pipeline writes one.
    """
    text = V12_IMAGE_SWITCH.read_text(encoding="utf-8")
    vorlauf, mitte, unten = the_three_parts_of(text)
    assert mitte, "the file does not carry the first pipeline this gate cuts at"
    assert unten, "the file does not carry the second pipeline this gate cuts at"

    assert aborts_of(vorlauf) == {"exit 2"}
    assert aborts_of(mitte) == {"exit 36", "exit 37", "exit 38"}
    assert aborts_of(unten) == {"exit 36", "exit 37", "exit 39"}
    assert set(IMAGE_SWITCH_ABORTS) <= aborts_of(mitte) | aborts_of(unten)

    # The staged probe, because a gate whose only assertion is that today is
    # fine stays green when it dies.
    staged = "    exit 37\n" + VORLAUF_CUT + "\n    exit 38\n" + PIPELINE_CUT + "\nexit 39\n"
    staged_vorlauf, staged_mitte, staged_unten = the_three_parts_of(staged)
    assert aborts_of(staged_vorlauf) == {"exit 37"}
    assert aborts_of(staged_mitte) == {"exit 38"}
    assert aborts_of(staged_unten) == {"exit 39"}


def test_the_driven_image_switch_of_the_predecessor_stays_byte_identical() -> None:
    """A fassung that ran is part of the evidence, so it does not move.

    92-wechsel.sh drove the image switch of the follow up measurement and its
    raw data lie beside it. The successor of plan 15-06 is a new file in the
    run directory of v1.2 for exactly that reason, and this watchman is what
    turns that rule from an intention into a gate.
    """
    raw = DRIVEN_IMAGE_SWITCH.read_bytes()
    assert len(raw) == DRIVEN_IMAGE_SWITCH_BYTES, DRIVEN_FASSUNG_RULE
    assert hashlib.sha256(raw).hexdigest() == DRIVEN_IMAGE_SWITCH_SHA256, DRIVEN_FASSUNG_RULE

    # The mutation probe, after the pattern of the two watchmen above: what is
    # shown here is that THIS comparison separates THIS file from a file that
    # has drifted by a single character.
    assert hashlib.sha256(raw + b" ").hexdigest() != DRIVEN_IMAGE_SWITCH_SHA256
    assert hashlib.sha256(raw.replace(b"set -eu", b"set -e", 1)).hexdigest() != DRIVEN_IMAGE_SWITCH_SHA256


# The watchman over the eleven tools the trip took over. Plan 15-01.
#
# The three watchmen above hold a fassung that ran against its own past. This
# one holds a copy against its original, which is the same rule read from the
# other end: the copies drive the levels of this trip, and their figures are
# only comparable with the figures of v1.1 for as long as the two files are one
# file. There is no raw data beside them yet, and that is the point of putting
# the gate in before the box stands rather than after.


@pytest.mark.parametrize("name", COPIED_TOOLS, ids=COPIED_TOOLS)
def test_the_copied_tools_of_the_v12_run_are_byte_identical_to_their_original(name: str) -> None:
    """A copy carries the figures of its original with it, so it stays the same file.

    Both sides are asserted to exist before they are compared. A digest taken
    from a missing original would raise rather than judge, and a deleted
    original must not be able to make this gate quiet.
    """
    original = RUN_DIR / name
    copy = V12_RUN_DIR / name
    assert original.is_file(), original
    assert copy.is_file(), copy
    original_digest = hashlib.sha256(original.read_bytes()).hexdigest()
    copy_digest = hashlib.sha256(copy.read_bytes()).hexdigest()
    # DRIVEN_FASSUNG_RULE is the reason and it is handed over as the diagnosis:
    # a fassung that runs is part of the evidence, so a change belongs in a new
    # file in a new run directory and never inside this one.
    assert copy_digest == original_digest, DRIVEN_FASSUNG_RULE


def test_the_copy_watchman_fires_on_a_single_added_character() -> None:
    """A watchman whose only assertion is that today is fine stays green when it dies.

    Staged against the real bytes of the full run script rather than against an
    invented sample, for the same reason as the mutation probe of the driven
    fassung: what is shown here is that THIS comparison separates THIS pair of
    files from a pair that has drifted apart by a single character.
    """
    original = (RUN_DIR / "96-volllauf.sh").read_bytes()
    copy = (V12_RUN_DIR / "96-volllauf.sh").read_bytes()
    original_digest = hashlib.sha256(original).hexdigest()
    assert hashlib.sha256(copy).hexdigest() == original_digest
    assert hashlib.sha256(copy + b" ").hexdigest() != original_digest
    assert hashlib.sha256(copy.replace(b"set -eu", b"set -e", 1)).hexdigest() != original_digest


def test_the_run_directory_of_the_trip_carries_every_tool_the_measurement_order_names() -> None:
    """A tool the order names and the directory lacks is paid for in box time.

    Section 7 of docs/runbook-messbox.md names a tool for every one of its ten
    blocks, and the run directory of v1.2 held three of them before plan 15-01.
    A name enters this list in the commit that creates the file, never before
    it: a list that named a file which does not exist yet would be red for a
    reason that is not a finding. The rewarm tool of step 8 is in it since plan
    15-03, the baseload return tool of step 8b since plan 15-04, the filter and
    sort tool of step 6b since plan 15-05, and the image switch of block 13b
    since plan 15-06, because the files they name exist since those plans.
    """
    assert len(COPIED_TOOLS) == 11
    assert len(set(COPIED_TOOLS)) == len(COPIED_TOOLS)
    assert len(TOOLS_THE_MEASUREMENT_ORDER_NAMES) == 18
    missing = [name for name in TOOLS_THE_MEASUREMENT_ORDER_NAMES if not (V12_RUN_DIR / name).is_file()]
    assert missing == [], missing


# The watchmen over the six fassungen the paid trip of phase 15 drove. Plan 15-15.
#
# The three watchmen further up hold a fassung of an earlier trip against its
# own past, and the copy watchman holds a copy against its original. These six
# are the same rule applied to the run directory of v1.2 itself: the raw files
# of the trip lie beside these scripts, the box they ran on is gone, and from
# today a change inside one of them is a red test rather than a matter of good
# intentions.


@pytest.mark.parametrize("name", sorted(DRIVEN_V12_FASSUNGEN), ids=sorted(DRIVEN_V12_FASSUNGEN))
def test_the_driven_v12_fassung_stays_byte_identical(name: str) -> None:
    """A fassung that ran on the paid box is evidence, and evidence does not get edited.

    Every one of these six wrote a raw file in
    docs/measurements/2026-09-v12-messung/rohdaten/ between 20.09. and
    21.09.2026, and the report reads its figures out of those raw files. The
    box was taken down on 21.09.2026, so a figure that turns out to be a claim
    about a changed script cannot be measured again.
    """
    digest, size = DRIVEN_V12_FASSUNGEN[name]
    path = V12_RUN_DIR / name
    assert path.is_file(), path
    raw = path.read_bytes()
    # DRIVEN_FASSUNG_RULE is the reason and it is handed over as the diagnosis:
    # a fix belongs in a successor with a new number in a new run directory.
    assert len(raw) == size, DRIVEN_FASSUNG_RULE
    assert hashlib.sha256(raw).hexdigest() == digest, DRIVEN_FASSUNG_RULE


def test_the_watchman_of_the_driven_v12_fassungen_fires_on_a_single_added_byte() -> None:
    """A watchman whose only assertion is that today is fine stays green when it dies.

    Staged against the real bytes of all six rather than against an invented
    sample, after the pattern of the mutation probes above: what is shown here
    is that THESE digests separate THESE files from files that have drifted by
    a single character.
    """
    assert len(DRIVEN_V12_FASSUNGEN) == 6
    for name, (digest, size) in DRIVEN_V12_FASSUNGEN.items():
        raw = (V12_RUN_DIR / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        assert len(raw + b" ") != size
        assert hashlib.sha256(raw + b" ").hexdigest() != digest
        assert hashlib.sha256(raw.replace(b"set -eu", b"set -e", 1)).hexdigest() != digest


def test_the_six_driven_v12_fassungen_are_the_ones_the_run_order_names() -> None:
    """The six are named by section 5 of 00-ablauf.md, and they are not the copies.

    The copy watchman of plan 15-01 holds eleven files that came over from the
    run directory of v1.1 unchanged; these six were written for this trip and
    have no original to be held against. The two sets must stay disjoint, or a
    file would be judged twice under two different rules.
    """
    assert set(DRIVEN_V12_FASSUNGEN).isdisjoint(COPIED_TOOLS)
    assert set(DRIVEN_V12_FASSUNGEN) <= set(TOOLS_THE_MEASUREMENT_ORDER_NAMES)
    # The stock probe is the only tool of the run directory that is neither a
    # copy nor one of the six: it ran inside the container as section 0 of the
    # language case fassung and carries no raw file of its own.
    assert STOCK_PROBE.name not in DRIVEN_V12_FASSUNGEN


# The watchmen over the two successor fassungen of auflage A1, plan 16-03.
#
# The six watchmen above keep the driven fassungen of the trip byte identical.
# These four keep the other half of the same rule: a fix of a driven fassung
# exists, it carries a new number in a new run directory, it names the file it
# follows and the finding it answers, and it holds the property that finding is
# about. Without the second pair a successor could point at its original and
# carry none of the fix.
#
# DRIVEN_V12_FASSUNGEN deliberately does NOT grow by these two files. Those six
# digests are the evidence of a paid trip; a seventh entry would freeze a
# fassung that never ran and put it on the same shelf as the ones that did.


def test_the_successor_of_the_image_switch_points_at_the_driven_fassung_and_lives_beside_it() -> None:
    """92c names 92b with its full path, names L-03, and says that it never ran."""
    text = SUCCESSOR_IMAGE_SWITCH.read_text(encoding="utf-8")
    assert "docs/measurements/2026-09-v12-messung/skripte/92b-wechsel.sh" in text
    assert "L-03" in text
    assert SUCCESSOR_IMAGE_SWITCH.parent != V12_IMAGE_SWITCH.parent
    # The sentence of pitfall 7, in the file itself and not only in a summary:
    # a raw file is read on its own, and so is a script.
    assert NOT_DRIVEN in text


def test_the_successor_of_the_image_switch_checks_the_occ_return_before_the_filter() -> None:
    """The fix of L-03 is an order of steps, so the order is what is asserted.

    Run 1 of the trip ended with nought without having registered anything: the
    call stood in the block whose output runs through tee, the return value of a
    pipeline belongs to its last command, and sh knows no pipefail. So the call
    writes into a file of its own, the return value is checked immediately after
    it, and only then does the output run into the raw file.
    """
    text = SUCCESSOR_IMAGE_SWITCH.read_text(encoding="utf-8")
    aufruf = text.index('occ app_api:app:register "$APP_ID" "$DAEMON"')
    geprueft = text.index("register_status=$?")
    gefiltert = text.index('cat "$registerlog"')
    gemerkt = text.index(': >"$WORK/registrierung-fehlt"')
    verweigert = text.index('if [ -f "$WORK/registrierung-fehlt" ]; then')
    assert aufruf < geprueft < gefiltert < gemerkt < verweigert
    # The call itself carries no pipe: it redirects into the file instead.
    zeilen = [line for line in text.splitlines() if "occ app_api:app:register" in line]
    assert len(zeilen) == 1, zeilen
    assert "|" not in zeilen[0], zeilen[0]
    assert '--wait-finish >"$registerlog" 2>&1' in text
    # The refusal below the pipeline carries the abort code of that spot, which
    # is the one 92b already gave a container on a foreign image identity: what
    # would be measured is a state the tree hash never covered.
    block = text[verweigert : text.index("\nfi\n", verweigert)]
    assert "exit 36" in block


def test_the_successor_of_the_filter_sort_tool_points_at_the_driven_fassung_and_lives_beside_it() -> None:
    """99d names 99c with its full path, names L-04, and says that it never ran."""
    text = SUCCESSOR_FILTER_SORT.read_text(encoding="utf-8")
    assert "docs/measurements/2026-09-v12-messung/skripte/99c-filter-sortierung.sh" in text
    assert "L-04" in text
    assert SUCCESSOR_FILTER_SORT.parent != V12_FILTER_SORT.parent
    assert NOT_DRIVEN in text


def test_the_successor_of_the_filter_sort_tool_reads_the_password_out_of_the_password_file() -> None:
    """The environment stays the first source, and it is no longer the only one.

    L-04 is a break of uniformity and not a security defect: the environment is
    the permitted shape of V14. What 99c lacked was the second way the rest of
    the tools of that run directory go, so a run that had deposited the file and
    left the variable unset logged in as nobody and measured the login page.
    """
    text = SUCCESSOR_FILTER_SORT.read_text(encoding="utf-8")
    # The path variable is the one 98c-sprachfaelle.sh of the same trip carries.
    assert PWFILE_DEFAULT in text
    assert PWFILE_DEFAULT in V12_LANGUAGE_CASES.read_text(encoding="utf-8")
    # The driven fassung knows neither the variable nor the file, which is the
    # finding, and this assertion is what keeps the two files apart.
    assert PWFILE_DEFAULT not in V12_FILTER_SORT.read_text(encoding="utf-8")
    umgebung = text.index(ENVIRONMENT_FIRST)
    datei = text.index(PWFILE_READ)
    assert umgebung < datei
    # An empty field after both sources is a refusal and not a run: the field is
    # asked twice, once to reach the file and once to decide.
    assert text.count('if [ ! -s "$PWFELD" ]; then') == 2
    assert "exit 2" in text[datei:]
