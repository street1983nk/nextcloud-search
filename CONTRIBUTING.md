# Contributing

Thanks for considering a contribution. Findling is solo-maintained with hard
quality gates; small, focused pull requests get reviewed fastest.

## The shape of the repository

Findling is two apps under one version: the `findling` companion app under
`php/` (registers the search provider, filters every hit through Nextcloud's
permissions) and the `findling_backend` External App under `backend/`
(extraction, OCR, the index). `docs/dev-setup.md` describes the development
stack; a disposable Nextcloud is required for anything beyond unit tests.

## The gates

Backend (from `backend/`, green locally before you push):

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright
uv run vulture src tests --min-confidence 80
```

Companion: `php -l` over every file and the PHPUnit suite under `php/tests`;
CI (`php.yml`) runs both plus the store metadata validation.

## Pull requests

- One concern per pull request, with tests; a behaviour change without a test
  will be asked for one.
- Every search result must stay permission checked by Nextcloud; anything
  that answers from the index without the PHP-side filter is rejected.
- The store texts (`docs/store-listing.md` and both `info.xml`) are
  owner-gated and travel with releases; do not edit them in a feature PR.
- Both apps carry the same version; version changes belong to releases, not
  to feature PRs.
- Dependencies are locked in `backend/uv.lock`; change it only through `uv`
  and say why in the commit message.

## Security problems

See [SECURITY.md](SECURITY.md); please do not open a public issue.
