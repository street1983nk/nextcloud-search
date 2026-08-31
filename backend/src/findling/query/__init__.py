"""Everything that happens to a search line before the engine sees it.

One module, :mod:`findling.query.rewrite`. It turns what a user typed into a
tantivy query: the filter prefixes are cut out first, the written out umlaut
forms get an alternative second, and the lenient parser runs last. The endpoints
of plan 02-11 call it and do nothing else to the text.
"""
