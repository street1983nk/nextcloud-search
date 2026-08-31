"""Index side of Findling: word list, analysers, schema, writer.

Importing :mod:`findling.index.analyzer` builds nothing on its own, but the
factory in there holds roughly 23 MB of automaton once it has run. The
extraction child process of plan 02-05 must therefore never import from this
package: it would pay those megabytes for every file it looks at, and it needs
none of them.

:mod:`findling.index.wordlist` is the exception and stays cheap on purpose. It
imports only the standard library and never reaches into the analyser, so a
caller that only needs the constituent list or its digest can have it without
dragging the automaton along.
"""
