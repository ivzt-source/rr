"""Unit tests for install/session-digest/render_digest.py.

These exercise the pure helpers (text extraction, turn classification,
timestamp formatting, truncation, session loading) plus an end-to-end run of
main() against a temporary Claude config directory.
"""
import json
import os
import time
from datetime import datetime, timezone

import pytest

from conftest import assistant_turn, user_turn


# --------------------------------------------------------------------------- #
# text_from_content
# --------------------------------------------------------------------------- #
class TestTextFromContent:
    def test_plain_string_passthrough(self, rd):
        assert rd.text_from_content("hello world") == "hello world"

    def test_text_blocks_joined(self, rd):
        content = [
            {"type": "text", "text": "first"},
            {"type": "text", "text": "second"},
        ]
        assert rd.text_from_content(content) == "first\n\nsecond"

    def test_tool_use_rendered_as_oneliner(self, rd):
        content = [{"type": "tool_use", "name": "Bash"}]
        assert rd.text_from_content(content) == "_🔧 used tool: `Bash`_"

    def test_tool_use_without_name_falls_back(self, rd):
        content = [{"type": "tool_use"}]
        assert "`tool`" in rd.text_from_content(content)

    def test_thinking_and_tool_result_blocks_skipped(self, rd):
        content = [
            {"type": "thinking", "thinking": "secret reasoning"},
            {"type": "tool_result", "content": "stdout"},
            {"type": "text", "text": "visible"},
        ]
        assert rd.text_from_content(content) == "visible"

    def test_non_dict_blocks_ignored(self, rd):
        content = ["not a dict", {"type": "text", "text": "kept"}]
        assert rd.text_from_content(content) == "kept"

    def test_whitespace_only_blocks_dropped(self, rd):
        content = [
            {"type": "text", "text": "   "},
            {"type": "text", "text": "real"},
        ]
        assert rd.text_from_content(content) == "real"

    def test_unknown_type_returns_empty_string(self, rd):
        assert rd.text_from_content(42) == ""


# --------------------------------------------------------------------------- #
# is_tool_result_turn
# --------------------------------------------------------------------------- #
class TestIsToolResultTurn:
    def test_true_when_tooluseresult_present(self, rd):
        assert rd.is_tool_result_turn({"toolUseResult": {"stdout": "x"}}) is True

    def test_true_when_content_all_tool_result(self, rd):
        obj = {"message": {"content": [
            {"type": "tool_result", "content": "a"},
            {"type": "tool_result", "content": "b"},
        ]}}
        assert rd.is_tool_result_turn(obj) is True

    def test_false_on_mixed_content(self, rd):
        obj = {"message": {"content": [
            {"type": "tool_result", "content": "a"},
            {"type": "text", "text": "hi"},
        ]}}
        assert rd.is_tool_result_turn(obj) is False

    def test_false_on_plain_text(self, rd):
        obj = {"message": {"content": "just text"}}
        assert rd.is_tool_result_turn(obj) is False

    def test_false_on_empty(self, rd):
        assert rd.is_tool_result_turn({}) is False


# --------------------------------------------------------------------------- #
# fmt_ts / day_of
# --------------------------------------------------------------------------- #
class TestTimestampFormatting:
    def test_fmt_ts_parses_zulu(self, rd):
        assert rd.fmt_ts("2026-06-09T07:30:00Z") == "2026-06-09 07:30"

    def test_fmt_ts_none_returns_question_mark(self, rd):
        assert rd.fmt_ts(None) == "?"

    def test_fmt_ts_bad_string_truncated_not_raised(self, rd):
        # Non-ISO string: falls back to first 16 chars, no exception.
        assert rd.fmt_ts("not-a-timestamp-at-all") == "not-a-timestamp-"

    def test_day_of_extracts_date(self, rd):
        assert rd.day_of("2026-06-09T23:59:00Z") == "2026-06-09"

    def test_day_of_none_is_unknown(self, rd):
        assert rd.day_of(None) == "unknown-date"

    def test_day_of_bad_string_is_unknown(self, rd):
        assert rd.day_of("garbage") == "unknown-date"


# --------------------------------------------------------------------------- #
# truncate
# --------------------------------------------------------------------------- #
class TestTruncate:
    def test_under_limit_unchanged(self, rd):
        assert rd.truncate("abc", 5) == "abc"

    def test_exactly_at_limit_unchanged(self, rd):
        assert rd.truncate("abcde", 5) == "abcde"

    def test_over_limit_truncated_with_suffix(self, rd):
        out = rd.truncate("abcdef", 5)
        assert out.startswith("abcde")
        assert "truncated 1 chars" in out


# --------------------------------------------------------------------------- #
# load_session
# --------------------------------------------------------------------------- #
class TestLoadSession:
    def test_basic_user_and_assistant_turns(self, rd, write_jsonl):
        path = write_jsonl([
            user_turn("what is 2+2?", cwd="/repo", gitBranch="main",
                      sessionId="abc123", timestamp="2026-06-09T07:00:00Z"),
            assistant_turn("4", timestamp="2026-06-09T07:00:05Z"),
        ])
        s = rd.load_session(str(path))
        assert s is not None
        assert s["turns"] == [("user", "what is 2+2?"), ("assistant", "4")]
        assert s["first_user"] == "what is 2+2?"
        assert s["cwd"] == "/repo"
        assert s["branch"] == "main"
        assert s["sid"] == "abc123"
        assert s["ts_first"] == "2026-06-09T07:00:00Z"
        assert s["ts_last"] == "2026-06-09T07:00:05Z"

    def test_malformed_lines_are_skipped(self, rd, write_jsonl):
        path = write_jsonl(None, raw_lines=[
            "not json at all",
            "",
            json.dumps(user_turn("real prompt")),
            "{ broken json",
        ])
        s = rd.load_session(str(path))
        assert s is not None
        assert s["turns"] == [("user", "real prompt")]

    def test_tool_result_user_turns_filtered(self, rd, write_jsonl):
        path = write_jsonl([
            {"type": "user", "toolUseResult": {"stdout": "x"},
             "message": {"role": "user", "content": [
                 {"type": "tool_result", "content": "x"}]}},
            user_turn("actual question"),
        ])
        s = rd.load_session(str(path))
        assert s["turns"] == [("user", "actual question")]

    def test_local_command_stdout_noise_skipped(self, rd, write_jsonl):
        path = write_jsonl([
            user_turn("<local-command-stdout>output here</local-command-stdout>"),
            user_turn("genuine prompt"),
        ])
        s = rd.load_session(str(path))
        assert s["turns"] == [("user", "genuine prompt")]
        assert s["first_user"] == "genuine prompt"

    def test_empty_session_returns_none(self, rd, write_jsonl):
        path = write_jsonl([
            {"type": "summary", "summary": "noise"},
            user_turn("   "),  # whitespace-only, dropped
        ])
        assert rd.load_session(str(path)) is None

    def test_metadata_taken_from_first_available(self, rd, write_jsonl):
        path = write_jsonl([
            user_turn("q1", cwd="/first", sessionId="sid-1"),
            user_turn("q2", cwd="/second", sessionId="sid-2"),
        ])
        s = rd.load_session(str(path))
        assert s["cwd"] == "/first"
        assert s["sid"] == "sid-1"


# --------------------------------------------------------------------------- #
# main (end-to-end)
# --------------------------------------------------------------------------- #
class TestMain:
    def _run_main(self, rd, claude_dir, out_dir, days=7, monkeypatch=None, max_chars=6000):
        argv = ["render_digest.py", "--claude-dir", str(claude_dir),
                "--days", str(days), "--out", str(out_dir),
                "--max-chars", str(max_chars)]
        monkeypatch.setattr("sys.argv", argv)
        rd.main()

    def test_renders_index_and_session_files(self, rd, tmp_path, write_jsonl, monkeypatch):
        write_jsonl([
            user_turn("hello there", sessionId="sess1234",
                      timestamp="2026-06-09T07:00:00Z"),
            assistant_turn("hi back", timestamp="2026-06-09T07:00:01Z"),
        ], name="a.jsonl")
        out = tmp_path / "out"
        self._run_main(rd, tmp_path, out, monkeypatch=monkeypatch)

        readme = (out / "README.md").read_text()
        assert "last 7 days" in readme
        assert "1 session(s)" in readme
        assert "2026-06-09" in readme

        session_files = list((out / "sessions").glob("*.md"))
        assert len(session_files) == 1
        body = session_files[0].read_text()
        assert "hello there" in body
        assert "hi back" in body
        assert "sess1234" in body

    def test_old_sessions_filtered_by_days_cutoff(self, rd, tmp_path, write_jsonl, monkeypatch):
        old = write_jsonl([user_turn("ancient", timestamp="2000-01-01T00:00:00Z")],
                          name="old.jsonl")
        # Force an old mtime well outside the window.
        old_time = time.time() - 30 * 86400
        os.utime(old, (old_time, old_time))

        write_jsonl([user_turn("recent", timestamp="2026-06-09T07:00:00Z")],
                    name="new.jsonl")

        out = tmp_path / "out"
        self._run_main(rd, tmp_path, out, days=7, monkeypatch=monkeypatch)

        readme = (out / "README.md").read_text()
        assert "1 session(s)" in readme
        assert "recent" in readme
        assert "ancient" not in readme

    def test_empty_input_writes_no_sessions_notice(self, rd, tmp_path, monkeypatch):
        (tmp_path / "projects").mkdir()
        out = tmp_path / "out"
        self._run_main(rd, tmp_path, out, monkeypatch=monkeypatch)
        readme = (out / "README.md").read_text()
        assert "No sessions in the last 7 days" in readme

    def test_stale_session_files_cleared_each_run(self, rd, tmp_path, write_jsonl, monkeypatch):
        out = tmp_path / "out"
        sessions_dir = out / "sessions"
        sessions_dir.mkdir(parents=True)
        stale = sessions_dir / "2020-01-01-deadbeef.md"
        stale.write_text("# stale leftover\n")

        write_jsonl([user_turn("fresh", timestamp="2026-06-09T07:00:00Z")],
                    name="fresh.jsonl")
        self._run_main(rd, tmp_path, out, monkeypatch=monkeypatch)

        assert not stale.exists()
        remaining = list(sessions_dir.glob("*.md"))
        assert len(remaining) == 1
        assert "fresh" in remaining[0].read_text()

    def test_long_message_body_truncated(self, rd, tmp_path, write_jsonl, monkeypatch):
        long_text = "x" * 100
        write_jsonl([user_turn(long_text, timestamp="2026-06-09T07:00:00Z")],
                    name="long.jsonl")
        out = tmp_path / "out"
        self._run_main(rd, tmp_path, out, monkeypatch=monkeypatch, max_chars=10)

        body = next((out / "sessions").glob("*.md")).read_text()
        assert "truncated 90 chars" in body
