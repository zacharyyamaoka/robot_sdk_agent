"""Turn collected inputs into a scorecard. Pure: no network, no clock (time is the inputs' `collected`).

Every verdict fails closed: a missing or malformed input is a failed gate and a `None` metric, never a pass.
"""

from __future__ import annotations

import datetime

from . import RULER, SCORECARD_SCHEMA, SDK_REPO

GRAPH_SCHEMA = "robot-sdk-graph/1"
STALE_GATE_HOURS = 24.0
CI_OK = {"success", "skipped"}
GATES = ("fresh_24h", "lint_clean", "graph_true", "listed_all", "upstream_public", "declared_all", "links_alive",
         "ci_green", "pypi_current", "site_current")  # fmt: skip


def _time(text: object) -> datetime.datetime | None:
    if not isinstance(text, str):
        return None
    try:
        t = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else None


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def listed(graph: dict) -> list[str]:
    return [p.get("id") for p in _list(graph.get("packages"))] + [a.get("id") for a in _list(graph.get("agents"))]


def content(graph: dict, missing: frozenset = frozenset()) -> dict:
    """What a reader learns from the graph, minus when it was built and from which commits (freshness scores those),
    and minus the missing-upstream packages a fresh build can't see (ruler v2: `upstream_public` scores those)."""
    out = {k: v for k, v in graph.items() if k not in ("generated", "sources")}
    if missing:
        out["packages"] = [p for p in _list(out.get("packages")) if p.get("id") not in missing]
        kept = [u for u in _list(out.get("uses")) if u.get("package") not in missing]
        dropped = {u.get("type") for u in _list(out.get("uses")) if u.get("package") in missing}
        used = {u.get("type") for u in kept}
        out["uses"] = kept
        out["types"] = [x for x in _list(out.get("types")) if x.get("id") not in dropped - used]
    return out


def freshness(inputs: dict, graph: dict, truth: dict, missing: frozenset = frozenset()) -> dict:
    now = _time(inputs.get("collected"))
    ids = [i for i in dict.fromkeys(listed(truth) + listed(graph)) if i not in missing]
    behind = _dict(inputs.get("behind"))
    sources = _dict(graph.get("sources"))
    hours: dict[str, float | None] = {}
    for repo in ids:
        row = _dict(behind.get(repo))
        if now is None or not sources.get(repo) or row.get("graph_sha") != sources.get(repo):
            hours[repo] = None  # the directory doesn't record this repo, or the comparison wasn't made against it
        elif row.get("status") == "identical":
            hours[repo] = 0.0
        elif row.get("status") == "ahead" and now and _time(row.get("first_missed_t")):
            hours[repo] = max(0.0, (now - _time(row["first_missed_t"])).total_seconds() / 3600)
        else:
            hours[repo] = None  # dirty, diverged, unknown or not recorded: nobody can say it is current
    known = [h for h in hours.values() if h is not None]
    worst = max(known) if known and len(known) == len(hours) else None
    return {
        "stale_hours": hours,
        "max_stale_hours": worst,
        "stale_packages": sum(1 for h in hours.values() if h is None or h > 0) if hours else None,
        "listed": len(ids),
    }


def tasks(graph: dict, metrics: dict, lint: dict) -> list[dict]:
    """The per-task breakdown (blackbox_agent CONTRACT §29): one entry per listed repo, a projection of the metrics
    score() already computed. objective = the repo's own stale hours (the objective is their max; null when nobody can
    say it is current, as in `stale_hours`); kind = package or agent, as the directory lists it; verdicts = the gates
    that check that repo one by one. A missing upstream (`upstream_public`) has no freshness and objective null."""
    agents = {a.get("id") for a in _list(graph.get("agents"))}
    hours = _dict(metrics.get("stale_hours"))
    missing = set(_list(metrics.get("missing_upstream")))
    out = []
    for repo in dict.fromkeys(list(hours) + sorted(missing)):
        verdicts: dict[str, bool] = {}
        if repo in missing:
            verdicts["upstream_public"] = False
        else:
            verdicts["fresh_24h"] = hours.get(repo) is not None and hours[repo] <= STALE_GATE_HOURS
            if repo not in agents:
                for gate, metric in (("declared", "undeclared_packages"), ("ci_green", "ci_not_green"),
                                     ("pypi_current", "pypi_mismatch")):
                    if isinstance(metrics.get(metric), list):
                        verdicts[gate] = repo not in metrics[metric]
                if repo in lint:
                    verdicts["lint_pass"] = lint.get(repo) == "pass"
        out.append({"task": repo, "kind": "agent" if repo in agents else "package",
                    "objective": None if repo in missing else hours.get(repo), "verdicts": verdicts})
    return out


def score(inputs: object) -> dict:
    inputs = _dict(inputs)
    graph = _dict(inputs.get("graph"))
    rebuild = _dict(inputs.get("rebuild"))
    truth = _dict(rebuild.get("graph"))
    metrics: dict = {}

    cloned = rebuild.get("cloned")
    # ruler v2: a listed repo the fresh build could not clone (not on GitHub yet, or private) is a missing upstream,
    # scored once by `upstream_public` and left out of the checks that need its repo
    missing = frozenset(r for r, ok in cloned.items() if ok is not True) if isinstance(cloned, dict) else frozenset()
    metrics["missing_upstream"] = sorted(missing) if isinstance(cloned, dict) and cloned else None
    fresh = freshness(inputs, graph, truth, missing)
    metrics.update(fresh)

    lint = _dict(rebuild.get("lint"))
    truth_packages = [p.get("id") for p in _list(truth.get("packages"))]
    if truth_packages and lint:
        metrics["lint_failures"] = sum(1 for pkg in truth_packages if lint.get(pkg) not in ("pass", "undeclared"))
        metrics["lint_pass_rate"] = sum(1 for pkg in truth_packages if lint.get(pkg) == "pass") / len(truth_packages)
    else:
        metrics["lint_failures"] = metrics["lint_pass_rate"] = None
    mine, theirs = content(graph, missing), content(truth, missing)
    metrics["graph_matches_rebuild"] = bool(graph and truth) and mine == theirs
    metrics["graph_differs_in"] = sorted(k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k))

    ids = set(listed(graph)) | {SDK_REPO}
    repos = inputs.get("repos")
    if isinstance(repos, list) and graph:
        candidates = [r for r in repos if isinstance(r, dict) and not r.get("fork") and not r.get("archived")
                      and not r.get("private") and (r.get("uses_robot_msgs") or r.get("has_declaration"))]  # fmt: skip
        metrics["unlisted_repos"] = sorted(r["name"] for r in candidates if r.get("name") not in ids)
    else:
        metrics["unlisted_repos"] = None
    declarations = inputs.get("declarations")
    packages = [p.get("id") for p in _list(graph.get("packages")) if p.get("id") not in missing]
    missing_urls = {p.get("repo_url") for p in _list(graph.get("packages")) if p.get("id") in missing}
    if isinstance(declarations, dict) and packages:
        metrics["undeclared_packages"] = sorted(p for p in packages if declarations.get(p) is not True)
    else:
        metrics["undeclared_packages"] = None
    links = inputs.get("links")
    relative = rebuild.get("relative_links")
    if isinstance(links, dict) and links and isinstance(relative, dict) and graph:
        dead = [u for u, s in links.items() if (not isinstance(s, int) or s >= 400) and u not in missing_urls]
        dead += [k for k, ok in relative.items() if ok is not True]
        metrics["dead_links"] = sorted(dead)
        metrics["links_checked"] = len(links) + len(relative)
    else:
        metrics["dead_links"], metrics["links_checked"] = None, 0

    ci, pypi = inputs.get("ci"), inputs.get("pypi")
    if isinstance(ci, dict) and packages:
        metrics["ci_not_green"] = sorted(p for p in packages if not ci.get(p) or not isinstance(ci.get(p), dict)
                                         or any(c not in CI_OK for c in ci[p].values()))  # fmt: skip
    else:
        metrics["ci_not_green"] = None
    if isinstance(pypi, dict) and packages:
        mismatch = []
        for p in packages:
            row = _dict(pypi.get(p))
            if not row.get("pyproject") or not row.get("pypi") or row["pyproject"] != row["pypi"]:
                mismatch.append(p)
        metrics["pypi_mismatch"] = sorted(mismatch)
    else:
        metrics["pypi_mismatch"] = None

    site = _dict(inputs.get("site"))
    metrics["site_serves_graph"] = inputs.get("directory") == "live" and graph.get("schema") == GRAPH_SCHEMA
    # the live graph was built from the same commit of every repo as a fresh build now (coordinator, 2026-11-24)
    live_sources = {k: v for k, v in _dict(graph.get("sources")).items() if k not in missing}
    built_sources = {k: v for k, v in _dict(truth.get("sources")).items() if k not in missing}
    metrics["site_sources_match_rebuild"] = bool(live_sources) and live_sources == built_sources
    page, built = site.get("index_html_sha256"), rebuild.get("index_html_sha256")
    metrics["site_page_matches_main"] = bool(page and built and page == built)

    def empty(name: str) -> bool:
        return isinstance(metrics[name], list) and not metrics[name]

    gates = {
        "fresh_24h": metrics["max_stale_hours"] is not None and metrics["max_stale_hours"] <= STALE_GATE_HOURS,
        "lint_clean": metrics["lint_failures"] == 0 and rebuild.get("lint_exit") == 0,
        "graph_true": metrics["graph_matches_rebuild"],
        "listed_all": empty("unlisted_repos"),
        "upstream_public": empty("missing_upstream"),
        "declared_all": empty("undeclared_packages"),
        "links_alive": empty("dead_links") and metrics["links_checked"] > 0,
        "ci_green": empty("ci_not_green"),
        "pypi_current": empty("pypi_mismatch"),
        "site_current": metrics["site_serves_graph"] and metrics["site_sources_match_rebuild"]
        and metrics["site_page_matches_main"],
    }
    # WHY: with no directory to score, nothing about it can be true, including the lint verdicts it should carry
    gates = {name: bool(gates[name]) and bool(graph) for name in GATES}
    return {
        "schema": SCORECARD_SCHEMA,
        "ruler": RULER,
        "collected": inputs.get("collected"),
        "directory": inputs.get("directory"),
        "objective": {"name": "max_stale_hours", "value": metrics["max_stale_hours"], "direction": "down"},
        "admissible": all(gates.values()),
        "gate_pass_rate": sum(gates.values()) / len(gates),
        "gates": gates,
        "failed_gates": sorted(name for name, ok in gates.items() if not ok),
        "metrics": metrics,
        "tasks": tasks(graph, metrics, lint),
    }
