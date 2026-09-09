---
status: verifying
trigger: "CI red: Integration run 34310167720, job search-parity (stable34, 8.2), step 'Log every account in and keep its session': GET /apps/findling/?query=parityloginprobe answers 404 for owner, while the same route answers 200 on the local NC 34.0.3 instance"
created: 2026-09-09
updated: 2026-09-09
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "The 404 is the PHP builtin server's own 404 and not a Nextcloud route miss. `composer run serve` is `php -S`, which resolves a request path against the filesystem first. setup-test-nc does `mv findling-src/php apps/findling`, so `apps/findling` exists as a real directory and carries no index.php and no index.html. The builtin server therefore answers 404 itself and the request never reaches the front controller. Every other CI address works because it has no counterpart on disk and falls back to the docroot index.php."
  confirming_evidence:
    - "docker php:8.2-cli, docroot with an index.php and the real php/ tree copied to apps/findling: GET /apps/findling/?query=parityloginprobe answers 404 with the builtin server's own error page, GET /index.php/apps/findling/?query=parityloginprobe answers 200 and reaches the front controller with PATH_INFO=/apps/findling/"
    - "same repro: /login and /settings/user answer 200 and reach index.php, which is why the login POST of this very step succeeds two lines above the probe"
    - "local Apache instance (nextcloud:34.0.3-apache, port 8090) answers 401 on /apps/findling/, not 404, so the route itself resolves wherever a rewrite exists"
    - "CI log line 'findling 1.0.3 enabled' from occ app:enable -vvv -f findling, so the app is installed and enabled before the probe"
    - "deploy-harp.yml lines 703 and 736 already ask the other page route of this app as http://localhost:8080/index.php/apps/findling/admin/overview, on an instance set up by the same action, and that probe is green"
    - "no htaccess.IgnoreFrontController anywhere in .github, so /index.php/apps/findling/ is the address this instance advertises through IURLGenerator"
  falsification_test: "If the 404 came from Nextcloud's router, the same address would 404 under Apache as well. It answers 401 there. If it came from a staged or incomplete app copy, /index.php/apps/findling/ would 404 too."
  fix_rationale: "The two new curl calls in integration.yml glue an address together that this instance never hands out. Nothing in the product produces the bare form: the navigation entry and the form action both come from linkToRoute, which prepends /index.php on an instance without a rewrite. So the probe is what is wrong, and the fix is the front controller form that the rest of this repository already uses."
  blind_spots: "The repro runs a bare index.php rather than the Nextcloud front controller, so it proves where the 404 comes from and not that the page renders. That the page renders under a session is what the CI run itself has to show; it was verified on the Apache instance during 09-05 and 09-07."

next_action: change both call sites in integration.yml to the /index.php form and commit

## Symptoms

expected: GET http://localhost:8080/apps/findling/?query=parityloginprobe answers 200 with the result page for user owner (as it does on localhost:8090, NC 34.0.3)
actual: the route answers 404 for owner
errors: "the result page answered 404 for owner and not the page, so the session did not reach it"
reproduction: GitHub Actions workflow Integration, run 34310167720, commit c1b1c9b, job `search-parity (stable34, 8.2)`, step "Log every account in and keep its session". The four cookie logins themselves succeed.
started: first run of the new probe (wave 09-07, commit ff435dd "feat(09-07): probe the cookie login of the result page")

## Eliminated

- hypothesis: "(a) the app copy in CI is staged, incomplete or stale, so the route is missing"
  evidence: "setup-test-nc does a plain `mv findling-src/php apps/findling`, no staging and no filter. `occ app:enable -vvv -f findling` prints 'findling 1.0.3 enabled'. In the repro with the identical tree, /index.php/apps/findling/ answers 200 while /apps/findling/ answers 404, so the same files serve one address and not the other."
  timestamp: 2026-09-09

- hypothesis: "(b) attribute route scanning behaves differently on stable34 than on 34.0.3, or an empty routes.php suppresses it"
  evidence: "The same file set answers 401 rather than 404 on the local Apache 34.0.3 instance and reaches the front controller in the php -S repro. A router that had not seen the route would answer the same way under both web servers."
  timestamp: 2026-09-09

- hypothesis: "(c) an unchanged app version in info.xml lets a cache serve an older app half"
  evidence: "The instance is installed from scratch in the same job, there is no image layer and no previous installation to be stale against. The 404 body is the PHP builtin server's own error page, not a Nextcloud answer."
  timestamp: 2026-09-09

## Evidence

- checked: .github/actions/setup-test-nc/action.yml
  found: "the instance is served by `composer run serve`, which is `php -S`, and the companion is moved with `mv findling-src/php apps/findling`"
  implication: "the request path /apps/findling/ has a real directory behind it on this instance"

- checked: CI log of job 102335023919, setup steps
  found: "findling 1.0.3 enabled, no error in app:enable, the login POST of the failing step itself succeeds"
  implication: "the app is installed and the session exists, so neither is the cause"

- checked: docker php:8.2-cli, docroot with an index.php plus the real php/ tree copied to apps/findling
  found: "GET /apps/findling/?query=parityloginprobe answers 404 with the builtin server's error page; GET /index.php/apps/findling/?query=parityloginprobe answers 200 and reaches index.php with PATH_INFO=/apps/findling/; /login and /settings/user answer 200"
  implication: "the builtin server answers the 404 itself for paths that exist on disk without an index file; the request never reaches Nextcloud"

- checked: local Apache instance nextcloud:34.0.3-apache on port 8090
  found: "GET /apps/findling/ answers 401, GET /index.php/apps/findling/ answers 401"
  implication: "the route resolves wherever a rewrite exists, which is why the address works on the dev instance and not in CI"

- checked: .github/workflows/deploy-harp.yml lines 703 and 736
  found: "the admin route of the same app is asked as http://localhost:8080/index.php/apps/findling/admin/overview on an instance from the same action, and that probe is green"
  implication: "the front controller form is the shape this repository already relies on"

- checked: grep for htaccess.IgnoreFrontController across .github
  found: "not set anywhere"
  implication: "IURLGenerator prepends /index.php on this instance, so the bare form is an address the product never produces"

## Resolution

root_cause: "The two new curl calls of plan 09-07 ask for http://localhost:8080/apps/findling/. The CI instance is served by php -S, whose builtin server resolves a request path against the filesystem first. setup-test-nc moves the companion to apps/findling, so that directory exists and carries no index.php and no index.html, and the builtin server answers the path with its own 404 without ever reaching the Nextcloud front controller. Every other address of this job works because /login has no counterpart on disk and /ocs/v2.php and /remote.php are files. The local dev instance runs Apache, whose rewrite sends the same address into index.php, which is why it answers there."
fix: "Both call sites in integration.yml ask for /index.php/apps/findling/ instead, which is the address IURLGenerator hands out on an instance without a rewrite and the form deploy-harp.yml already uses for the admin route of the same app. The reason is written down at ask_page and referenced from the login probe. No product code changed."
verification: "Local repro in docker php:8.2-cli with the real php/ tree in apps/findling: the bare form 404s, the new form answers 200 and reaches the front controller with PATH_INFO=/apps/findling/. The workflow parses as YAML and both touched run blocks pass bash -n. That the page then renders under a session is what the next CI run shows; it was verified against the Apache dev instance during 09-05 and 09-07."
files_changed: [".github/workflows/integration.yml"]
