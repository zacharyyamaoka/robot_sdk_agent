"""The ruler's first test: with every input missing, nothing passes. Then: each input missing fails its own gates."""

from __future__ import annotations

import pytest
from ruler_fixtures import passing

from scorer.score import GATES, score


@pytest.mark.parametrize("empty", [None, {}, [], "", {"schema": "robot-sdk-agent-inputs/1"}])
def test_every_input_missing_passes_nothing(empty):
    card = score(empty)
    assert card["admissible"] is False
    assert card["gates"] == {gate: False for gate in GATES}
    assert card["gate_pass_rate"] == 0
    assert card["objective"]["value"] is None


def test_the_passing_fixture_passes():
    card = score(passing())
    assert card["failed_gates"] == []
    assert card["admissible"] is True
    assert card["objective"]["value"] == 0.0


# Each input, removed alone, must fail at least the gates that read it.
NEEDS = {
    "collected": {"fresh_24h"},
    "graph": set(GATES),  # no directory: nothing about it can be true
    "rebuild": {"lint_clean", "graph_true", "upstream_public", "links_alive", "site_current"},
    "behind": {"fresh_24h"},
    "repos": {"listed_all"},
    "declarations": {"declared_all"},
    "links": {"links_alive"},
    "ci": {"ci_green"},
    "pypi": {"pypi_current"},
    "site": {"site_current"},
    "directory": {"site_current"},
}


@pytest.mark.parametrize("key", sorted(NEEDS))
def test_each_missing_input_fails_its_gates(key):
    inputs = passing()
    del inputs[key]
    card = score(inputs)
    assert NEEDS[key] <= set(card["failed_gates"]), card["failed_gates"]
    assert card["admissible"] is False
