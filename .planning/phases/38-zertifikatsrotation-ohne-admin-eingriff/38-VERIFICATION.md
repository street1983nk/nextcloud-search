---
phase: 38-zertifikatsrotation-ohne-admin-eingriff
verified: 2026-10-28T16:30:00Z
status: human_needed
score: 4/4 success criteria verified
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "SC2 probe flake / red main deploy-harp run (x509>=1 race)"
    - "SC1 warning: no remedy line in the session-shutdown-only race"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Post the Issue #33 answer (38-ENTWURF-ISSUE-33.md, Desktop/Findling_Issue33_Antwort_ENTWURF.md), 6 sentences, English"
    expected: "Owner posts it; only after that may a commit say Closes #33"
    why_human: "Owner task, outbound communication. Issue #33 still OPEN, no new comment (last 2026-10-24)"
  - test: "Re-read HaRP main, then send 38-ENTWURF-HARP-UPSTREAM.md (Desktop/Findling_HaRP_Upstream_Vorschlag_ENTWURF.md)"
    expected: "Owner decides and files the upstream issue; research valid until 2026-11-27"
    why_human: "Owner task, outbound communication"
---

# Phase 38: Zertifikatsrotation ohne Admin-Eingriff, Verification Report (re-verification)

**Phase Goal:** Backend detects an HaRP certificate change, reports it with remedy, and takes over new certificates under /certs/frp without unregister/register and without container restart; proven, capped, documented (D-37-09).
**Verified:** 2026-10-28
**Status:** human_needed (all automated criteria verified; only the two owner drafts remain)
**Re-verification:** Yes, after gap closure

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | x509 detection, rate-limited remedy, reconnect after file swap without re-register or container restart | VERIFIED | harp_connect.sh as before (two-digest stability, min gap, hourly cap, no downgrade, exit contract, env knobs). Warning closed: new knob FINDLING_HARP_SUSPECT_AFTER_ERRORS (default 6, validated >= 1, l.117-154) reports the remedy also for a run of failed logins without x509 (commits a06b241e tests, 6e98c525 fix). Proven in CI: run 40712263940 and main run 40717960907 each have legs with "0 x509 line(s), 7 failed dial(s) ... remedy line once". |
| 2 | CI probe with real CA reissue and positive control | VERIFIED | Dead window now judged by failed dials, no login and the remedy line, x509 informational (95ebc201, 297b69ba). Main run 40717960907 on 297b69ba: completed/success on all four legs (stable33, stable34 amd64, stable34 arm64, stable35); each leg: no login, remedy line once, no frpc restart, no container restart. Probe branch run 40712263940: 4/4 green. |
| 3 | No restart storm, state in log | VERIFIED | Unchanged; supervisor tests incl. new shutdown cases ran for real in Python gates 40717960901 on 297b69ba (success, 6336 passed, 253 skipped, none from the supervisor module). |
| 4 | Doc and drafts | VERIFIED | docs/harp-tunnel.md section and drafts as in the first pass (copy recipe, backendReachable wording, PLAINTEXT sentence, #6254, fallback without --rm-data). Issue #33 draft 6 sentences. Drafts in phase dir and on Desktop. |

## Evidence checks

| Check | Result |
|-------|--------|
| `pytest tests/test_cert_rotation_steps.py` (local) | 34 passed |
| Python gates 40717960901 (297b69ba) | success, 6336 passed |
| deploy-harp 40717960907 (297b69ba, main) | success, 4/4 legs |
| deploy-harp 40712263940 (probe branch) | success, 4/4 legs |
| Supervisor tests locally | not run (Windows, per instruction) |
| Commits on origin/main | 6e98c525, 95ebc201, 297b69ba, 4c8226a5 present; no "Closes #33" in any message |
| Issue #33 | still OPEN, nothing posted |

## Gaps Summary

None. Both earlier gaps closed and verified against repo and gh.

## Human Verification Required

1. Post the Issue #33 answer (owner sends; before any "Closes #33").
2. Review and send the HaRP upstream proposal after re-reading HaRP main.

---

_Verified: 2026-10-28_
_Verifier: Claude (gsd-verifier)_
