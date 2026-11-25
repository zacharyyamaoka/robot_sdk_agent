"""PROGRESS.md and the dashboard's Scoreboard tab (site/tabs/10-scoreboard.md) are what `python3 tools/rda.py progress`
writes from ledger.jsonl: generated, never a hand-edited copy that drifts from the ledger."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def rda():
    spec = importlib.util.spec_from_file_location("rda", REPO / "tools" / "rda.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_progress_and_the_scoreboard_tab_are_current_with_the_ledger():
    tool = rda()
    lines, _ = tool.progress_lines(tool.rows())
    assert (REPO / "PROGRESS.md").read_text(encoding="utf-8") == "\n".join(lines) + "\n", "run: python3 tools/rda.py progress"
    assert tool.SCOREBOARD.read_text(encoding="utf-8") == tool.scoreboard(lines), "run: python3 tools/rda.py progress"


def test_the_scoreboard_tab_links_the_directory_and_shows_the_gate_matrix():
    text = rda().SCOREBOARD.read_text(encoding="utf-8")
    assert text.startswith("# Scoreboard\n")
    assert "https://zacharyyamaoka.github.io/robot_sdk/" in text
    assert "## Gate matrix" in text
