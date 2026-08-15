"""Boundary package towards Nextcloud.

Everything that talks to the AppAPI client library lives in
:mod:`findling.nc.client`. Gate A (``tests/test_readonly_gate.py``, invariant 1)
rejects that import anywhere else, so this package stays the single seam between
Findling and the AppAPI runtime.

The docstrings in this package deliberately avoid spelling out the library name
outside :mod:`findling.nc.client`, so that a plain ``grep`` over the sources
answers the boundary question as clearly as the AST gate does.
"""
