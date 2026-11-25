"""A small, made-up world in which every gate passes (everything current): the base each mutation test breaks one way."""

from __future__ import annotations

import copy

T = "2026-11-24T12:00:00+00:00"


def graph() -> dict:
    return {
        "schema": "robot-sdk-graph/1",
        "generated": "2026-11-24T11:00:00+00:00",
        "sources": {"robot_sdk": "aaaaaaa", "robot_msgs": "bbbbbbb", "robot_reach": "ccccccc", "some_agent": "ddddddd"},
        "packages": [
            {"id": "robot_msgs", "pypi": "robot-msgs", "repo_url": "https://github.com/o/robot_msgs", "lint": "pass"},
            {"id": "robot_reach", "pypi": "robot-reach", "repo_url": "https://github.com/o/robot_reach", "lint": "pass"},
        ],
        "types": [{"id": "robot_msgs.JointState", "docs_url": "https://example.org/JointState/"}],
        "uses": [{"package": "robot_reach", "type": "robot_msgs.JointState", "kind": "consumes"}],
        "agents": [{"id": "some_agent", "repo_url": "https://github.com/o/some_agent"}],
    }


def passing() -> dict:
    g = graph()
    truth = copy.deepcopy(g)
    truth["generated"] = "2026-11-24T11:59:00+00:00"
    return {
        "schema": "robot-sdk-agent-inputs/1",
        "ruler": "v1",
        "collected": T,
        "directory": "live",
        "graph": g,
        "site": {"index_status": 200, "index_html_sha256": "f" * 64},
        "rebuild": {
            "graph": truth,
            "cloned": {"robot_msgs": True, "robot_reach": True, "some_agent": True},
            "lint_exit": 0,
            "lint": {"robot_msgs": "pass", "robot_reach": "pass"},
            "index_html_sha256": "f" * 64,
            "relative_links": {"README.md -> docs/x.md": True},
        },
        "behind": {
            "robot_msgs": {"graph_sha": "bbbbbbb", "status": "identical", "ahead_by": 0, "first_missed_t": None},
            "robot_reach": {"graph_sha": "ccccccc", "status": "identical", "ahead_by": 0, "first_missed_t": None},
            "some_agent": {"graph_sha": "ddddddd", "status": "identical", "ahead_by": 0, "first_missed_t": None},
        },
        "repos": [
            {"name": "robot_msgs", "uses_robot_msgs": False, "has_declaration": True},
            {"name": "robot_reach", "uses_robot_msgs": True, "has_declaration": True},
            {"name": "some_agent", "uses_robot_msgs": True, "has_declaration": False},
            {"name": "robot_sdk", "uses_robot_msgs": True, "has_declaration": False},
            {"name": "a_fork", "fork": True, "uses_robot_msgs": True},
            {"name": "unrelated", "uses_robot_msgs": False, "has_declaration": False},
        ],
        "declarations": {"robot_msgs": True, "robot_reach": True},
        "links": {"https://github.com/o/robot_msgs": 200, "https://example.org/JointState/": 301},
        "ci": {"robot_msgs": {"test": "success"}, "robot_reach": {"test": "success", "docs": "skipped"}},
        "pypi": {"robot_msgs": {"pyproject": "0.3.1", "pypi": "0.3.1"}, "robot_reach": {"pyproject": "0.1.0", "pypi": "0.1.0"}},
    }


def stale(inputs: dict, repo: str, since: str, new_sha: str = "eeeeeee") -> dict:
    """Main moved past what the directory records: the fresh build now names new_sha for the repo."""
    inputs["behind"][repo].update(status="ahead", ahead_by=1, first_missed_t=since)
    inputs["rebuild"]["graph"]["sources"][repo] = new_sha
    return inputs


def missing_upstream(inputs: dict, repo: str = "robot_new") -> dict:
    """A pinned package with no public repo yet: the directory carries it from its last good graph, the fresh build
    can't clone it, and nothing about its repo can be fetched."""
    inputs["graph"]["packages"].append({"id": repo, "pypi": "robot-new", "repo_url": f"https://github.com/o/{repo}",
                                        "lint": "pass", "upstream": "missing"})  # fmt: skip
    inputs["graph"]["uses"].append({"package": repo, "type": "robot_msgs.Only", "kind": "consumes"})
    inputs["graph"]["types"].append({"id": "robot_msgs.Only", "docs_url": None})
    inputs["graph"]["sources"][repo] = "1234567"
    inputs["rebuild"]["cloned"][repo] = False
    inputs["links"][f"https://github.com/o/{repo}"] = 404
    inputs["declarations"][repo] = False
    inputs["behind"][repo] = {"graph_sha": "1234567", "status": "unknown"}
    return inputs
