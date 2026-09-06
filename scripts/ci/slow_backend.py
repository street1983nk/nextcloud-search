#!/usr/bin/env python3
"""A backend that answers /search too late, for the timeout proof (T2).

The unified search asks every provider and waits for all of them, so a slow
provider does not cost its own result group, it costs the whole search for the
user. ExAppService therefore passes one and a half seconds per call to AppAPI,
deliberately below the AppAPI default of three. A timeout that nobody has ever
seen work is a timeout nobody knows to work, which is what this stub is for.

It takes the place of the real backend on the same port, with the registration
left untouched.

**The budget chain this stub is pointed at**, from the tightest link outwards,
because the tightest one is not the one the name "budget" suggests:

* ``ExAppService::REQUEST_TIMEOUT_SECONDS`` is 1.5 seconds and it is the ceiling
  of ONE call. It is what a single /search runs into.
* ``Provider::BUDGET_NANOSECONDS`` is 2.5 seconds and it is the wall clock of
  the whole result group, across at most ``MAX_ROUNDS`` of three rounds and at
  most ``min(64, limit * 2)`` resolved nodes. Every call shrinks its own timeout
  to what is left of it, so this number can bound a call but never widen one.
* The AppAPI default of three seconds sits under both and is never reached.

**Two numbers and one stub, and that is deliberate.** The delay is read out of
the environment instead of standing in a constant, because the workflow asks two
different questions of the same process. The first is the total failure: an
answer after ten seconds, which is the default below and which no link of the
chain can survive. The second is the edge of the tightest link, and it takes two
runs: an answer just under 1.5 seconds has to arrive and be a hit, one just over
it has to cost the result group and nothing else. A second stub for that would
be a second file to keep in step with the shape of a candidate answer, and that
shape is the part which has to stay true.

**What it answers, and why it is not an empty list.** The canary is the one
title the PHP side accepts without a file behind it (``CANARY_TITLE`` in
``ExAppService`` and in ``backend/src/findling/api/search.py``), so it is the
only hit a stub can produce without an index, a file id and a permission
recheck. This stub used to answer a body that ``searchCandidates`` rejects as
malformed, which meant the empty result group of the ten second case could
equally well have come from the parser as from the timeout. A well formed hit
removes that reading: an empty group can now only mean the answer did not arrive
in time.

Standard library only, and no third party server: this has to start in a second
on a runner that already has enough to install.
"""

from __future__ import annotations

import http.server
import json
import os
import time
from typing import Any, Final

# The total failure, and the default of this stub. Well beyond every ceiling of
# the chain above, and still short enough that a workflow which does wait for it
# hits a visibly slow step rather than the job deadline. The assertion in the
# workflow is what turns that into a red run.
DELAY_SECONDS: Final = 10

# The same delay in milliseconds, because the edge cases live below the second
# and a whole number of seconds cannot express them. The default is the number
# above and it has not moved: the step that has always used this stub reads no
# environment variable and therefore still gets its ten seconds.
DELAY_MS: Final = int(os.environ.get("FINDLING_SLOW_BACKEND_DELAY_MS", str(DELAY_SECONDS * 1000)))

PORT: Final = int(os.environ.get("EXAPP_PORT", "10035"))

# Frozen on both sides. filterCandidates() keeps a candidate with file id 0 only
# under this exact title and only with a snippet, and drops everything else that
# carries an id which cannot point at a file.
CANARY_TITLE: Final = "findling-canary"


class Handler(http.server.BaseHTTPRequestHandler):
    """Answers the three shapes of request that reach a registered ExApp."""

    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # the method name is dictated by the base class
        """The search. This is the one that is late.

        One candidate and ``hasMore`` false, so the provider asks once and stops:
        a cursor that promised more would cost a second call and the measurement
        would be of two delays rather than of one.
        """
        time.sleep(DELAY_MS / 1000)
        self._answer(
            {
                "candidates": [
                    {
                        "fileId": 0,
                        "title": CANARY_TITLE,
                        "snippet": f"answered by slow_backend after {DELAY_MS}ms",
                    }
                ],
                "hasMore": False,
                "nextOffset": 0,
            }
        )

    def do_GET(self) -> None:  # the method name is dictated by the base class
        """The heartbeat, and it has to stay fast.

        AppAPI polls this one. A slow answer here would make the registration the
        thing under test instead of the search timeout.
        """
        self._answer({"status": "ok"})

    def do_PUT(self) -> None:  # the method name is dictated by the base class
        """/enabled, so nothing in AppAPI trips over a 501 while this stub runs."""
        self._answer({})

    def _answer(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - base class signature
        """Silence the per request log: the interesting output is the timing."""


if __name__ == "__main__":
    print(f"slow_backend: 127.0.0.1:{PORT}, /search answers after {DELAY_MS}ms", flush=True)
    # Threading, so the late answer does not block the heartbeat.
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
