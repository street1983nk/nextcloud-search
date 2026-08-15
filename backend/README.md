# findling backend

Python part of Findling, the zero-config search app for Nextcloud. It runs as an
AppAPI external app under the store id `findling_backend` and is reached only
through the PHP companion app `findling`.

## Development

Everything runs through `uv`; there is no supported path that uses a system
Python.

```bash
cd backend
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run vulture src tests --min-confidence 80
uv run pytest -q
```

All five gates must be green locally before a commit. The same five steps run in
`.github/workflows/python.yml`.

## Read-only invariant

User files are never modified. `tests/test_readonly_gate.py` parses every module
under `src/findling` and fails the build when a write path appears, before any
read path exists. See `docs/store-identity.md` for the frozen app ids.

## License

AGPL-3.0-or-later, see `../LICENSE`.
