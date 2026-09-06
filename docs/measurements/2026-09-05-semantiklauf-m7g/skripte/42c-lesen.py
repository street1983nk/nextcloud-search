#!/usr/bin/env python3
"""Read one recording of the admin page and print three numbers for the watchman.

Three and not one: the watchman decides on the work stock, reports the first
track and waits for the second, and a shell that has to parse JSON three times
parses it wrong once. Output is "vorrat indexed embedded", or three times
"unklar" when the recording is missing, unparsable or carries an error, because
"not known" and "zero" are two different answers and the watchman must not treat
the first as the second.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    zeile = sys.stdin.read().strip()
    if not zeile:
        print("unklar unklar unklar")
        return 0
    try:
        d = json.loads(zeile)
    except ValueError:
        print("unklar unklar unklar")
        return 0
    if not isinstance(d, dict) or "fehler" in d:
        print("unklar unklar unklar")
        return 0
    vorrat = int(d.get("scheduled", 0)) + int(d.get("running", 0))
    # The counters of the second track live under "backend"; the top-level
    # "indexed" is the PHP half and stays 0 by design (see 00-start.txt).
    b = d.get("backend") or {}
    indexed = b.get("indexed", d.get("indexed", 0))
    embedded = b.get("embedded")
    print(vorrat, int(indexed or 0), "unklar" if embedded is None else int(embedded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
