"""Each gate goes red on the one fault it exists for (the ruler mutation-tested: a gate that can't fail measures nothing)."""

from __future__ import annotations

import pytest
from ruler_fixtures import passing, stale

from scorer.score import score


def failed(mutate) -> list[str]:
    inputs = passing()
    mutate(inputs)
    return score(inputs)["failed_gates"]


def test_two_hours_behind_is_fresh_but_the_site_is_not_current():
    inputs = stale(passing(), "robot_reach", "2026-11-24T10:00:00Z")
    card = score(inputs)
    assert card["objective"]["value"] == pytest.approx(2.0)
    assert card["failed_gates"] == ["site_current"]


def test_stale_beyond_24_hours():
    inputs = stale(passing(), "robot_reach", "2026-11-23T11:59:00Z")
    assert score(inputs)["failed_gates"] == ["fresh_24h", "site_current"]


def test_live_sources_differ_from_a_fresh_build():
    def m(i):
        i["rebuild"]["graph"]["sources"]["robot_sdk"] = "9999999"
    assert failed(m) == ["site_current"]


def test_dirty_or_unknown_source_is_not_fresh():
    def m(i):
        i["behind"]["robot_msgs"] = {"graph_sha": "bbbbbbb-dirty", "status": "unknown"}
    assert failed(m) == ["fresh_24h"]


def test_a_listed_repo_missing_from_the_sources_is_not_fresh():
    def m(i):
        del i["behind"]["some_agent"]
    assert failed(m) == ["fresh_24h"]


def test_lint_failure():
    def m(i):
        i["rebuild"]["lint"]["robot_reach"] = "fail"
        i["rebuild"]["lint_exit"] = 1
    assert failed(m) == ["lint_clean"]


def test_a_package_the_lint_never_reported_fails():
    def m(i):
        del i["rebuild"]["lint"]["robot_reach"]
    assert failed(m) == ["lint_clean"]


def test_graph_content_differs_from_a_fresh_build():
    def m(i):
        i["graph"]["uses"] = []
    assert failed(m) == ["graph_true"]


def test_an_unlisted_robot_msgs_repo():
    def m(i):
        i["repos"].append({"name": "new_thing", "uses_robot_msgs": True})
    assert failed(m) == ["listed_all"]


def test_a_package_without_a_declaration():
    def m(i):
        i["declarations"]["robot_reach"] = False
    assert failed(m) == ["declared_all"]


def test_a_dead_link_and_an_unreachable_one():
    def m(i):
        i["links"]["https://example.org/JointState/"] = 404
    assert failed(m) == ["links_alive"]

    def n(i):
        i["links"]["https://example.org/JointState/"] = None
    assert failed(n) == ["links_alive"]


def test_a_broken_relative_link():
    def m(i):
        i["rebuild"]["relative_links"]["README.md -> docs/x.md"] = False
    assert failed(m) == ["links_alive"]


def test_red_or_missing_ci():
    def m(i):
        i["ci"]["robot_msgs"] = {"test": "failure"}
    assert failed(m) == ["ci_green"]

    def n(i):
        i["ci"]["robot_msgs"] = {}
    assert failed(n) == ["ci_green"]


def test_pypi_behind_pyproject():
    def m(i):
        i["pypi"]["robot_msgs"]["pypi"] = "0.3.0"
    assert failed(m) == ["pypi_current"]


def test_site_page_not_built_from_main():
    def m(i):
        i["site"]["index_html_sha256"] = "0" * 64
    assert failed(m) == ["site_current"]


def test_scoring_main_instead_of_the_live_site():
    def m(i):
        i["directory"] = "main"
    assert failed(m) == ["site_current"]
