---
status: verifying
trigger: "CI red: HaRP deploy run 34059434556, step 'Store install 5, an archive without its routes block finds nothing' fails with a 200 and the canary hit"
created: 2026-09-06
updated: 2026-09-06
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "H3. The probe's premise is false. The companion reaches the container over the AppAPI signed path, and HaRP skips route checking for signed requests, so the routes block has no influence on the search at all."
  confirming_evidence:
    - "harp_agent (pinned image sha256:603fdf5..., HARP_VERSION 0.4.5) line 529-531: route_allowed = True with the comment 'We skip routes checking for AppAPI signed requests', taken whenever the six AppAPI headers are present"
    - "AppAPICommonService::buildAppAPIAuthHeaders sets exactly those six headers for a HaRP daemon"
    - "php ExAppService::proxyRequest calls PublicFunctions::exAppRequest, which goes to AppAPIService::requestToExApp, which never consults the route table"
    - "DockerActions::resolveExAppUrl returns {nextcloud_url}/exapps/{appId} for a HaRP daemon, so the call passes through HaRP"
    - "local replay of the HaRP route loop with Findling's five routes: no observable difference between the stripped and the full info.xml on either path"
  falsification_test: "If AppAPI took the routes from anywhere but the --info-xml file, oc_ex_apps_routes would carry rows after a registration with the stripped file. The new step measures exactly that."
  fix_rationale: "The step is rebuilt on the only place where the difference between the two archives is observable: the oc_ex_apps_routes table AppAPI fills from the file the registration is handed. Store install 6 counts the same table with the block in place, which makes it one differential measurement."
  blind_spots: "The bare path route urls (search, status) never match HaRP's re.match against /search, so the user facing path answers 404 with and without the block. Carried out as a separate finding, not fixed here."

## Symptoms

expected: search returns no entries after registering the ExApp from an info.xml with the routes block stripped
actual: HTTP 200 with entry title findling-canary on all three matrix legs
errors: "the search answered 200 with entries ... either AppAPI does not read the routes out of the archive or this probe is measuring the wrong answer"
reproduction: workflow legs stable33, stable34, stable35 of run 34059434556, commit ad5b09b
started: first run of this new step

## Eliminated

- hypothesis: H1, a stale registration was never removed before Store install 5
  evidence: Store install 2 runs app_api:app:unregister --rm-data and asserts no container, no volume, no companion directory. ExAppService::unregisterExApp deletes the route rows via removeExAppRoutes. The log prints "ExApp findling_backend successfully registered", which Register.php only reaches on a fresh registration.
  timestamp: 2026-09-06

- hypothesis: H2, the register call did not get the stripped info.xml
  evidence: ExAppService::getAppInfo does file_get_contents on the --info-xml path and only falls back to the store when that option is absent. The step itself asserts the stripped copy carries zero route elements, and the local replay of the same sed shows 5 routes to 0.
  timestamp: 2026-09-06

- hypothesis: H4, the answer came from a stale companion or a cache
  evidence: the subline carries the container timestamp 21:01:39, ten seconds after the step started, and the canary is produced inside the container (backend/src/findling/api/search.py CANARY_TITLE). All three legs show it, so it is deterministic rather than a leftover.
  timestamp: 2026-09-06

## Evidence

- checked: harp_agent of the pinned image
  found: HARP_VERSION 0.4.5, line 531 "route_allowed = True  # We skip routes checking for AppAPI signed requests"
  implication: the routes block cannot influence a call the companion makes

- checked: haproxy.cfg.template of the same image
  found: not_found returns 404, forbidden returns 403, bad_request is a silent-drop
  implication: a probe on /heartbeat would hang instead of answering

- checked: local replay of the HaRP route loop with Findling's routes
  found: "/search" unsigned answers 404 with the block and without it, because re.match("search", "/search") is None
  implication: there is no HTTP level difference to measure, only the database

## Resolution

root_cause: "The probe assumed the routes block gates the search. It does not. The companion calls the container over the AppAPI signed path, and HaRP 0.4.5 skips route checking for signed requests."
fix: "Store install 5 rebuilt onto oc_ex_apps_routes, Store install 6 counts the same table with the block in place, comments corrected."
verification: "local: sed strip 5 routes to 0, jq branch fail closed against real, empty and broken bodies, HaRP route loop replayed with the pinned agent code, bash -n and YAML parse clean. Open: the next CI run."
files_changed: [".github/workflows/deploy-harp.yml"]
