# What is tested, and the one gap that is left

This document exists because of a single honest answer to the question "is the
PHP half tested?". It is not, not by a unit test, and `php -l` is a syntax check
and not a test. What follows is what covers which half, what the remaining gap
is, and what closes it.

## The two halves are not tested the same way

| Half | Gates | Runs where |
|---|---|---|
| Python backend | ruff, ruff format, pyright basic, vulture, pytest | locally before every commit, and in `python.yml` |
| PHP companion | `php -l`, plus both integration jobs end to end | `php.yml` and `integration.yml`, CI only |

The reason for the difference is not a decision, it is the development machine:
there is no PHP and no composer on it, and the local system Python is broken
which is why the backend runs through `uv`. Every PHP change in this repository
is therefore written once and verified in CI, never executed while it is written.
That is worth knowing when reading a PHP diff here.

## What the integration jobs do cover

`integration.yml` is not a smoke test, it exercises the PHP paths that matter,
through the real unified search API of a real Nextcloud:

- the search provider is registered and visible (`walking-skeleton`, canary step)
- a search returns exactly one canary hit whose subline can only have been
  produced inside the backend, for the user the signed header named
- the permission recheck lets that canary through, which is the one exception in
  `Provider::search` and the one entry `ExAppService::filterCandidates` accepts
  without a file behind it
- an ordinary search term does not see the canary, so the diagnostic hit cannot
  colour a normal search unnoticed
- the provider reports `term` and `title-only` as its filters, which is what
  keeps a client with a set filter from skipping the provider without a word
- a backend that hangs costs one result group and not the search: status 200, no
  entries, under six seconds against a stub that answers after ten
- a backend that is gone costs one result group and not the search, which is the
  `is_array($response)` branch
- the content gateway delivers every file of the reference corpus to its owner
  (`readonly-gate`)
- the same file ids answer 404 for a user who exists and owns nothing
- the same file ids answer 404 for a user id that does not exist at all, which is
  the case that used to answer 500 and told a caller which accounts exist
- not one byte and not one timestamp of the corpus moves in the process

## The gap

These behaviours of the PHP half have no test at all today. They are pure logic,
they are the parts a unit test covers well, and they are exactly the parts that
were added or changed by the security audit follow up, which is why they are
listed by name rather than summarised:

1. `ExAppService::filterCandidates` drops a candidate whose `fileId` is absent or
   is not an integer.
2. It drops a candidate with a non positive `fileId` whose title is not the
   canary.
3. It strips `title` and `snippet` off every candidate with a positive `fileId`,
   so nothing the container volunteers before the recheck can be displayed.
4. `Provider::search` drops a candidate whose node cannot be resolved through the
   user's own folder, and takes title and link from the resolved node.
5. It returns an empty result, not unchecked hits, when the user has no home
   folder.
6. `PlainText::bounded` strips control characters, keeps the tab, caps at the
   given length, cuts on character boundaries and refuses invalid UTF-8.
7. `ExAppService::searchCandidates` refuses an empty term without a round trip
   and clamps the limit into 1..100.
8. The answer body is refused above one megabyte, before it reaches
   `json_decode`.
9. `GatewayController::getFileContents` answers 403 when `EX-APP-ID` is not
   `findling_backend`.
10. `Provider::search` asks at most three times, resolves at most
    `min(64, limit * 2)` nodes per search, and stops asking when the wall clock
    of two and a half seconds is used up.
11. It requests excerpts only after the recheck, only for the surviving file
    ids, and not at all when the budget is gone, in which case the subline is
    the path.
12. `ExAppService::filterSnippets` drops an excerpt for a file id that was not
    asked for, and drops the highlight ranges of a text that the cleaning
    changed, because every offset behind the change would point elsewhere.

Number 9 is reachable over HTTP but not from the integration job as it stands: it
would need a second registered ExApp to call the gateway under a foreign app id.
The other eleven are unit test material.

## What closes it

A PHPUnit job in `php.yml`, CI only, following the pattern every Nextcloud app
uses: check out `nextcloud/server` at the same branch the integration jobs use,
place the app in `apps/findling`, add PHPUnit as a dev dependency to
`php/composer.json`, and run the suite with the server's `tests/bootstrap.php` so
that `OCP` is available and `IRootFolder`, `IUserManager`, `IAppManager`,
`IUserMountCache`, `IFileAccess` and `LoggerInterface` can be mocked with
`createMock`.

It is deliberately not part of the audit follow up. Writing a PHPUnit suite and a
new CI job without being able to run either of them once is how a workflow ends
up red for reasons that have nothing to do with the code under test, and the
twelve items above are the specification for whoever writes it with a PHP runtime
at hand. Until then the gap is here, in writing, and not in somebody's memory.
