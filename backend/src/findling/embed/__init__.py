"""Embedding side of Findling: the semantic half of the search.

Nothing in here is imported by the extraction child process and nothing is
imported at start up. The two artefacts this package works with are constants of
the image and weigh together roughly 136 MB on disk (the int8 ONNX model and the
XLM-R tokenizer at ``$FINDLING_EMBED_MODEL_DIR``), and the inference runtime that
opens them adds a resident cost of its own. A caller that only wants to search
lexically must be able to do so without paying either, which is why the model is
opened where it is used and not where the package is imported.

The first module here is :mod:`findling.embed.bench`, and it is deliberately a
measuring tool rather than a piece of the search: wave 0 of phase 6 replaces the
three estimated numbers the phase is planned against before a vector schema
exists. It is the same order the index side was built in, where
:mod:`findling.index.bench` answered what a search costs during a commit before
the batch size was fixed.
"""
