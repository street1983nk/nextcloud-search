"""Extraction side of Findling: the verdict, the allowlist, the process guard.

Everything in this package runs, or is meant to run, inside the extraction child
process. Two rules follow from that and hold for every module here.

*Nothing in this package imports the analysis half of Findling.* The compound
automaton costs roughly 23 MB of resident memory and a third of a second to
build, measured in plan 02-01. The child needs none of it, and a child that is
recycled every 200 files would pay for it again and again. The rule is checked
from the outside, by a test that asks a running child which modules it has
loaded, because a rule that is only a comment survives exactly until the next
convenient import.

*A document is untrusted input for somebody else's parser.* pypdfium2 and lxml
are C extensions, so a hang inside them cannot be interrupted from Python and a
runaway allocation cannot be caught by a try block. The guard is therefore not
written in this package at all: it is a process boundary, a kernel enforced
address space limit and a kill after a deadline.
"""
