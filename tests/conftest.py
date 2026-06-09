"""Shared pytest fixtures and module loading for the render_digest tests.

render_digest.py lives next to its shell scripts under install/session-digest/
and is meant to be run as a standalone script, so it isn't importable as a
normal package. We load it by file path with importlib and expose it as the
`rd` fixture (and module-level import target).
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDERER_PATH = REPO_ROOT / "install" / "session-digest" / "render_digest.py"


def _load_render_digest():
    spec = importlib.util.spec_from_file_location("render_digest", RENDERER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Loaded once at import time so tests can `from conftest import rd` if they like,
# but the fixture below is the supported access path.
render_digest = _load_render_digest()


@pytest.fixture
def rd():
    """The render_digest module under test."""
    return render_digest


@pytest.fixture
def write_jsonl(tmp_path):
    """Write a list of dict records as a .jsonl session file; return its path.

    By default writes into a Claude-style projects tree so it is picked up by
    the glob in main(): <tmp>/projects/<project>/<name>.jsonl
    """
    def _write(records, name="session.jsonl", project="proj", raw_lines=None):
        proj_dir = tmp_path / "projects" / project
        proj_dir.mkdir(parents=True, exist_ok=True)
        path = proj_dir / name
        with open(path, "w", encoding="utf-8") as fh:
            if raw_lines is not None:
                fh.write("\n".join(raw_lines) + "\n")
            else:
                for rec in records:
                    fh.write(json.dumps(rec) + "\n")
        return path

    return _write


def user_turn(text, **extra):
    """Build a 'user' transcript record with the given text content."""
    rec = {"type": "user", "message": {"role": "user", "content": text}}
    rec.update(extra)
    return rec


def assistant_turn(content, **extra):
    """Build an 'assistant' transcript record. `content` may be str or blocks."""
    rec = {"type": "assistant", "message": {"role": "assistant", "content": content}}
    rec.update(extra)
    return rec
