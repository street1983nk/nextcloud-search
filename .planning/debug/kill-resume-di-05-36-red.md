---
status: investigating
trigger: "Resilience job kill-resume (stable34, 8.2), step DI-05-36, run 34056709826 on 96d798b: RED exit 1"
created: 2026-09-06
updated: 2026-09-06
---

## Current Focus

hypothesis: |
  H1 (kill mechanism): exapp.pid holds the PID of `uv`, not of the python server.
  `uv run python -m findling.main &` makes $! the uv PID; uv spawns python as a
  child. kill/kill -9 on that PID does not take the server down. Every restart in
  this job therefore starts a SECOND server that cannot bind 10035, dies, and
  leaves the original process serving. The gate never tested a restarted container.
  H2 (silent success signal): the step counts "pass finished" lines. run_once
  returns ROUND_EMPTY before that log call, so an armed poller with an empty queue
  is completely silent. The queue was already drained at the moment of the kill.
test: run `uv run python -c print(os.getpid())` backgrounded in git-bash and compare $! with the reported pid
expecting: $! differs from the python pid -> H1 confirmed
next_action: run the uv pid experiment locally

## Symptoms

expected: DI-05-36 step passes, restarted container indexes by itself
actual: "the container came up unarmed and stayed that way for 300 seconds", exit 1
errors: |
  claimed=2 indexed=0 skipped=0 failed=2 (loop)
  ERROR: [Errno 98] address already in use ('127.0.0.1', 10035)  x2
  ERROR:findling.worker.poller:indexing pass ended in an unexpected IndexLockedError
reproduction: CI run 34056709826; green comparison 34055850111
started: between ee09672 (green) and 96d798b (red)

## Eliminated

- hypothesis: 06.1-21 (french OCR language) caused the failures
  evidence: green run at ee09672 already had ocr_unavailable=154; red has 144. resilience.yml installs no tesseract in either run, so OCR was unavailable before the change too.
  timestamp: 2026-09-06

- hypothesis: the poller loop dies on IndexLockedError
  evidence: poller.run catches every Exception, logs the type name, calls _back_off and continues. The loop survives.
  timestamp: 2026-09-06

## Evidence

- checked: red log, counters at the moment of the kill (20:03:41) vs counters in the failure dump (20:08:43)
  found: byte identical. indexed 193, failed 216, skipped 60 = 469 = every file in the account. Work stock scheduled 0, handed to the worker 0.
  implication: the queue was ALREADY fully drained when the kill happened. The restarted container had nothing to index, so it could not write a "pass finished" line.

- checked: red log, restarted container startup lines
  found: "findling backend was enabled before this start, indexing continues without a switch"
  implication: the arming worked. The step's verdict "came up unarmed" is false.

- checked: crawl step, both runs, time from the last "waiting for the middle" line to the counters group
  found: red 20:03:11.4 -> 20:03:41.6 = 30.2 s; green 19:46:13.4 -> 19:46:43.7 = 30.3 s
  implication: the `curl heartbeat || break` loop ran all 30 iterations in both runs. The server kept answering after `kill -9 $(cat exapp.pid)`. The pid in the file is not the server.

- checked: "the container answers again" timestamp vs the step start
  found: red 20:03:41.6621 vs step endgroup 20:03:41.6500 = 12 ms; green 35 ms
  implication: no fresh python+uvicorn+276k wordlist start is possible in 12 ms. The heartbeat was answered by the process that was supposed to be dead.

- checked: red exapp.log tail
  found: exactly two "[Errno 98] address already in use" and one IndexLockedError
  implication: two subsequent start attempts (Start the container again, DI-05-36) both failed to bind against the surviving original, and the second one could not take the tantivy writer lock either because the original holds it.

- checked: green run, drain step after the negative control
  found: "draining: open=0 indexed=169 docs=169", "the queue is empty after 1 seconds"
  implication: green was equally drained. Its "1 passes after 5 seconds" was a leftover pass of the surviving original process, not proof of a restarted container. Green was green for the wrong reason.

## Resolution

root_cause: |
  Two defects in the gate, neither in the indexing itself.

  A) The success signal is silent when there is no work. The step counts the
  poller line "pass finished", which run_once writes only for a pass that
  claimed rows; the empty branch returns ROUND_EMPTY before that call. In run
  34056709826 all 469 files had reached a terminal verdict before the kill even
  happened (counters at 20:03:41 identical to those at 20:08:43, queue at 0), so
  the correctly armed restarted container wrote nothing at all and the step
  reported the very defect it exists to catch.

  B) The pidfile does not name the server. `uv run python -m findling.main &`
  followed by `echo $!` records the pid of uv, which starts python as a child.
  kill and kill -9 against it take uv down and leave the server holding port
  10035 and the tantivy writer lock. Consequence in both runs: the heartbeat
  kept answering for the full 30 s wait loop after the hard kill, "the container
  answers again" was printed 12 ms into the next step, and every later start
  died with EADDRINUSE and IndexLockedError. The gate has been measuring the
  process it believed it had replaced, which is also why ee09672 was green.

fix: |
  - poller.py: an armed pass over an empty work stock logs one line per arming,
    "indexing is armed and the work stock is empty, ...". A silenced poller never
    enters the pass, so the line separates armed-and-idle from silenced.
  - resilience.yml DI-05-36 and the negative control count both lines.
  - all four server starts resolve the interpreter first
    (uv run python -c 'import sys; print(sys.executable)') and start it directly,
    so $! is the server.

verification: |
  - test_an_armed_container_with_an_empty_work_stock_says_so_once_per_arming is
    red without the poller change (assert 0 == 1) and green with it.
  - ruff, ruff format --check, pyright, vulture clean; 1573 passed, 13 skipped.
  - local probe: $! = 1237358, uv = 30648, python = 11908, three distinct pids.

files_changed:
  - backend/src/findling/worker/poller.py
  - backend/tests/test_poller.py
  - .github/workflows/resilience.yml
  - .github/actions/setup-test-nc/action.yml
