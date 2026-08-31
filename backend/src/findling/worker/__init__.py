"""The background half of the container: one task that turns queued files into
index entries.

There is exactly one module in here and there should stay exactly one. IDX-08
allows a single indexing worker on the four gigabyte box this project targets,
because the OCR peak of three to six hundred megabytes for one page and the
embedding model of two-fifty to four hundred must never be allowed to meet. A
second poller would not announce itself as a memory problem, it would announce
itself as a container the kernel killed.

The order of one pass is the subject of :mod:`findling.worker.poller` and it is
written out there. In one line: commit first, then the verdict, then the
acknowledgement, because that is the only arrangement in which every possible
moment of an abort is harmless.
"""
