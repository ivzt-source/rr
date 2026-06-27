# Tests

Automated tests for this repo. Currently covers `render_digest.py`, the
session-transcript renderer with the most parsing/formatting logic.

## Run

```bash
pip install -r ../requirements-dev.txt   # one-time
python -m pytest                          # from the repo root
```

## Layout

| File | Covers |
|------|--------|
| `test_render_digest.py` | text extraction, turn classification, timestamp formatting, truncation, session loading, and an end-to-end `main()` run |
| `conftest.py` | loads `render_digest.py` by path and provides JSONL fixture helpers |

`render_digest.py` is a standalone script (not an installed package), so
`conftest.py` loads it via `importlib` from `install/session-digest/`.

## CI

`.github/workflows/ci.yml` runs `pytest` and `shellcheck` (warning severity)
on every push and pull request.

## Not yet covered

See the test-coverage analysis for the fuller backlog — notably the idempotent
JSON merge in `install-remote-control.sh`, config parsing and the git-push
retry in `session-digest.sh`, and the `desktop-remote-control.sh` env gating.
