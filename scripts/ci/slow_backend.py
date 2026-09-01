#!/usr/bin/env python3
"""A backend that answers /search far too late, for the timeout proof (T2).

The unified search asks every provider and waits for all of them, so a slow
provider does not cost its own result group, it costs the whole search for the
user. ExAppService therefore passes a two second timeout to AppAPI, deliberately
below the AppAPI default of three. A timeout that nobody has ever seen work is a
timeout nobody knows to work, which is what this stub is for.

It takes the place of the real backend on the same port, with the registration
left untouched, and answers /search after ten seconds. The integration workflow
then measures how long the search takes and insists on an empty result group in
far less than that.

Standard library only, and no third party server: this has to start in a second
on a runner that already has enough to install.
"""

from __future__ import annotations

import http.server
import json
import os
import time
from typing import Any

# Well beyond the two second provider timeout, and still short enough that a
# workflow which does wait for it does not hit the job timeout but a visibly slow
# step. The assertion in the workflow is what turns that into a red run.
DELAY_SECONDS = 10

PORT = int(os.environ.get("EXAPP_PORT", "10035"))


class Handler(http.server.BaseHTTPRequestHandler):
    """Answers the three shapes of request that reach a registered ExApp."""

    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # the method name is dictated by the base class
        """The search. This is the one that is late."""
        time.sleep(DELAY_SECONDS)
        self._answer({"results": []})

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
    print(f"slow_backend: 127.0.0.1:{PORT}, /search answers after {DELAY_SECONDS}s", flush=True)
    # Threading, so the ten second answer does not block the heartbeat.
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
