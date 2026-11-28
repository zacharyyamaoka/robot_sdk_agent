#!/usr/bin/env python3
"""Back-fill the per-task breakdown (`tasks`, blackbox_agent CONTRACT §29) into committed scorecards.

    python3 tools/backfill_tasks.py [--check]

Each card's own record is the inputs file saved beside it (solutions/<id>/runs/<t>.inputs.json, the one whose
`collected` is the card's). The frozen, pure scorer re-scores it offline; the card gets `tasks` only when every other
key of the re-score equals the committed card byte for byte (so nothing but the projection is new). Idempotent;
touches no other key. A card with no matching inputs, or whose re-score differs, is left as it is and counted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scorer.score import score  # noqa: E402


def rescore(path: Path) -> dict | None:
    card = json.loads(path.read_text(encoding="utf-8"))
    for saved in sorted((path.parent / "runs").glob("*.inputs.json"), reverse=True):
        inputs = json.loads(saved.read_text(encoding="utf-8"))
        if inputs.get("collected") == card.get("collected"):
            fresh = score(inputs)
            if {k: v for k, v in fresh.items() if k != "tasks"} == {k: v for k, v in card.items() if k != "tasks"}:
                return fresh
            return None
    return None


def main(argv: list[str]) -> int:
    filled = same = left = 0
    for path in sorted(REPO.glob("solutions/*/scorecard*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        fresh = rescore(path)
        if fresh is None:
            left += 1
            print("left (no matching inputs, or the re-score differs):", path.relative_to(REPO))
            continue
        if card.get("tasks") == fresh["tasks"]:
            same += 1
            continue
        card["tasks"] = fresh["tasks"]
        filled += 1
        if "--check" not in argv:
            path.write_text(json.dumps(card, indent=1) + "\n", encoding="utf-8")
    print(f"back-filled {filled}, already current {same}, left {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
