## What this changes

<!-- One concern per pull request. Say what changes for a user or admin. -->

## Checklist

- [ ] Backend gates are green locally (`pytest -q`, `ruff check .`,
      `ruff format --check .`, `pyright` at the CI version, `vulture`)
- [ ] PHP half: `php -l` clean and the PHPUnit suite green, if touched
- [ ] A behaviour change carries a test that fails without it
- [ ] Every result path stays permission checked by Nextcloud
- [ ] Store texts and versions untouched (they belong to releases)
