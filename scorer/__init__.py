"""The robot-sdk agent's frozen scorer (ruler v1, OBJECTIVES.md).

`collect.collect()` gathers the inputs from public data only (the live site, GitHub's public API, PyPI, a fresh
rebuild from public clones); `score.score(inputs)` turns them into a scorecard and never touches the network.
A solution never edits this folder: tests/test_scorer_frozen.py holds its sha256 to the one in OBJECTIVES.md.
"""

RULER = "v2"
OWNER = "zacharyyamaoka"
SDK_REPO = "robot_sdk"
SITE = "https://zacharyyamaoka.github.io/robot_sdk/"
INPUTS_SCHEMA = "robot-sdk-agent-inputs/1"
SCORECARD_SCHEMA = "robot-sdk-agent-scorecard/1"
