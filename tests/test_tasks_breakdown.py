"""The scorecard's per-task breakdown (`tasks`, blackbox_agent CONTRACT §29): one entry per listed repo, a projection
of metrics the frozen scorer already computes. Not a ruler test (not hashed): it reads the scorer and the saved inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import backfill_tasks  # noqa: E402
from scorer.score import score  # noqa: E402


def test_a_scorecard_carries_a_well_formed_breakdown_whose_max_is_the_objective():
    cards = sorted(REPO.glob("solutions/*/scorecard*.json"))
    assert cards
    for path in cards:
        card = json.loads(path.read_text(encoding="utf-8"))
        fresh = backfill_tasks.rescore(path)
        assert fresh is not None, f"{path}: the saved inputs no longer re-score to the committed card"
        assert card["tasks"] == fresh["tasks"]
        ids = [t["task"] for t in card["tasks"]]
        assert len(ids) == len(set(ids)) and set(card["metrics"]["stale_hours"]) <= set(ids)
        assert {t["kind"] for t in card["tasks"]} <= {"package", "agent"}
        assert all(isinstance(v, bool) for t in card["tasks"] for v in t["verdicts"].values())
        known = [t["objective"] for t in card["tasks"] if t["objective"] is not None]
        if card["objective"]["value"] is not None:
            assert max(known) == card["objective"]["value"]


def test_no_inputs_still_gives_a_list_and_never_a_number():
    card = score({})
    assert card["tasks"] == [] and card["objective"]["value"] is None
