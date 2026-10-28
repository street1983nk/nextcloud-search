---
phase: 38-zertifikatsrotation-ohne-admin-eingriff
verified: 2026-10-28T15:00:00Z
status: gaps_found
score: 3/4 success criteria verified (SC2 partial: probe flaky, main run red)
gaps:
  - truth: "SC2: A CI probe reissues the CA for real and proves reconnection with a positive control, reliably"
    status: partial
    reason: "Branch run 40696292903 is green on all four legs, but main run 40704387898 (cf13ee09, identical workflow and script) is RED on leg stable34/ubuntu-24.04 (amd64). The rotation step failed in its own dead-window precondition: '0 x509 line(s) and 12 failed dial(s) within 180 s'. The probe demands >= 1 x509 line, but the dials alternate between frpc-side x509 and frps-side 'session shutdown' and which speaks first is a race (the step comment already measured 1 in 9 on arm64). Three other legs of the same run passed with 1 x509 line each. Probe is flaky, not a product failure."
    artifacts:
      - path: ".github/workflows/deploy-harp.yml"
        issue: "Dead-window loop requires x509>=1 within 180 s; fails when frps refuses the old client cert every time"
    missing:
      - "Relax or restructure the dead-window precondition (e.g. accept N failed dials with no login, assert x509/remedy line separately or via a deterministic path), then get a green main deploy-harp run"
      - "Confirm run 40710049216 (f440a00a, in progress at verification time) or a rerun is green on all four legs"
  - truth: "SC1: reissue is detected via x509 pattern and reported with remedy (WARNING, not blocker)"
    status: partial
    reason: "Detection keys only on frpc lines containing 'connect to server error:' AND 'x509: '. The same CI run shows a reissue where all 12 dials said 'session shutdown' and 0 said x509; in that race the watcher prints no remedy line at all (the probe's own remedy-line-once assertion would also not be reached). Heal-by-copy still works (files are picked up by fingerprint), but the admin is not told."
    artifacts:
      - path: "backend/docker/harp_connect.sh"
        issue: "on_x509 triggered only by x509 lines (line ~451)"
    missing:
      - "Decide whether repeated 'session shutdown' failures with changed /certs on the HaRP side should also trigger the remedy line, or accept and document"
human_verification:
  - test: "Post the Issue #33 answer (38-ENTWURF-ISSUE-33.md, Desktop/Findling_Issue33_Antwort_ENTWURF.md), 6 sentences between the answer markers, English"
    expected: "Owner posts it; only after that may a commit say Closes #33"
    why_human: "Owner task, outbound communication; Issue #33 is still OPEN, last comments 2026-10-24, nothing posted for this phase"
  - test: "Re-read HaRP main, then send 38-ENTWURF-HARP-UPSTREAM.md (Desktop/Findling_HaRP_Upstream_Vorschlag_ENTWURF.md)"
    expected: "Owner decides and files upstream issue; research valid until 2026-11-27"
    why_human: "Owner task, outbound communication"
---

# Phase 38: Zertifikatsrotation ohne Admin-Eingriff, Verification Report

**Phase Goal:** Backend detects an HaRP certificate change, reports it with remedy, and takes over new certificates under /certs/frp without unregister/register and without container restart; proven, capped, documented (D-37-09).
**Verified:** 2026-10-28
**Status:** gaps_found (one CI-proof gap, one detection warning)
**Re-verification:** No, initial

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | x509 detection, rate-limited remedy, reconnect after file swap without re-register or container restart | VERIFIED with WARNING | harp_connect.sh: x509 match (l.451), on_x509 with schedule 0,300,900,3600 then hourly (l.119-120, 338-356), remedy line names the docs anchor. Restart only after two equal digests in a row (l.405), MIN_GAP (l.410), hourly cap with single cap line (l.416-425), no downgrade when files vanish (l.395-402). Exit contract: exit 0 only when `stopping`; frpc rc 0 is mapped to 1 (l.497-505). Env knobs present and validated (l.107-155, exit EXIT_CONFIG on bad value). Branch-run legs show heal 8-19 s after copy, 0 container restarts. WARNING: detection is x509-only, see gap 2. |
| 2 | CI probe with real CA reissue and positive control | PARTIAL | Step "Certificate rotation..." in deploy-harp.yml: rm -rf /certs/frp, restart HaRP, asserts new CA hash, dead window (no login, empty/err search, remedy once, 0 frpc restarts, RestartCount/StartedAt unchanged), copy, heal, log assertions. Branch run 40696292903: 4/4 legs green (1 x509 line each, heal 8-19 s). Main run 40704387898: 3/4 legs green, stable34/amd64 RED in the dead-window precondition (0 x509, 12 failed dials). Same workflow content as the green branch run (no diff in .github or backend/docker between 2aa19a29 and cf13ee09), so this is flake in the probe, but main is red. Run 40710049216 (f440a00a) still in_progress at verification: the single open confirmation. |
| 3 | No restart storm: cap limits repeats and messages, state visible in log | VERIFIED | Cap, min gap, window, single cap line (above); stub-frpc tests cover flapping files stopping at cap, window reset, one swap = one restart, x509 with unchanged files = one report and no restart (test names l.326-483). Probe asserts 0 restarts with unchanged files and <=1 remedy line. Diagnose integration: not claimed beyond log (criterion says "falls vorhanden"). |
| 4 | Doc + two drafts | VERIFIED | docs/harp-tunnel.md: section "Repair without re-registering" with the docker exec cat | docker exec -i copy recipe (umask 077, tmp name + mv -f), `backendReachable` false / "backend answered: no" but not the cause, TrueNAS fix PR #6254, fallback "unregister without --rm-data", PLAINTEXT upgrade sentence (l.76-78). Both drafts in the phase dir and on the Desktop (14:08). Issue #33 answer: 6 sentences between markers (limit 8), English, no em dash. |

## Behavioral and CI evidence

| Check | Result |
|-------|--------|
| `pytest tests/test_cert_rotation_steps.py` (run locally) | 31 passed |
| Python gates run 40695322746 on 0f04885a | success, 6264 passed, 253 skipped; 49 SKIPPED lines in -rs output, none from test_harp_connect_supervisor.py or test_cert_rotation_steps.py, so the supervisor tests ran for real on Linux (module has only the win32 and missing-tool skipifs) |
| shellcheck step (`shellcheck docker/harp_connect.sh docker/init.sh`) in same run | present and run, job success; also asserted by test_both_scripts_pass_shellcheck |
| Python gates 40704387890 on cf13ee09 | success |
| deploy-harp branch run 40696292903 (2aa19a29) | success, 4/4 legs, rotation step success on each |
| deploy-harp main run 40704387898 (cf13ee09) | FAILURE, leg stable34/ubuntu-24.04, rotation step |
| deploy-harp run 40710049216 (f440a00a, docs-only commit) | in_progress, not yet judged |
| Supervisor tests run locally | not run, per instruction |

## Housekeeping

- 10 commits with "38-0" in the subject are on origin/main; main == origin/main (0 ahead, 0 behind).
- No "Closes #33" / "Fixes #33" in any commit message. Issue #33 still OPEN; no comment posted by this phase.
- Untracked `backend/.coverage` in working tree (harmless, not committed).

## Anti-patterns

No TBD/FIXME/XXX markers checked beyond the touched files' grep scope; none relevant found in findings above. No stubs: harp_connect.sh and tests are substantive.

## Gaps Summary

1. BLOCKER (CI proof): Probe flake turned main's HaRP deploy red. The x509>=1 requirement in the dead-window loop is a known race (documented in the step comment) and it fired on main after passing on the branch. Fix the precondition, then require a green deploy-harp on main (run 40710049216 would be the first sample, but it only samples the same flaky code; a pass proves nothing about the race).
2. WARNING (detection coverage): in the "session shutdown only" race the watcher gives no remedy line. Accept and document, or extend the trigger.

Not in scope here: Phase 40 requires all CI workflows green on the release commit, so gap 1 must close before then.

_Verified: 2026-10-28_
_Verifier: Claude (gsd-verifier)_
