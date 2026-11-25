"""Gather the scorer's inputs from public data only. Everything a value comes from is a public URL or a public clone.

Each fetch that fails leaves its value `None`; score.py fails every check that needed it (fail closed).
GitHub's API is read with a token when one is in GITHUB_TOKEN / GH_TOKEN or `gh auth token` (only for the rate limit:
60 requests an hour unauthenticated); every endpoint read is public.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

from . import INPUTS_SCHEMA, OWNER, RULER, SDK_REPO, SITE

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
UA = "robot-sdk-agent-scorer"
DEPENDS_ON_MSGS = re.compile(r"""["']robot[-_]msgs(?:[\s<>=~!\[;@,"']|$)""", re.I)
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _token() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        done = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        return done.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


TOKEN = _token()


def fetch(url: str, *, api: bool = False, timeout: float = 30) -> tuple[int | None, bytes | None]:
    headers = {"User-Agent": UA}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        if TOKEN:
            headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, None


def fetch_json(url: str, **kw) -> object | None:
    status, body = fetch(url, **kw)
    if status != 200 or body is None:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def gh(path: str) -> object | None:
    return fetch_json(f"{API}/{path}", api=True)


def raw(repo: str, path: str, ref: str = "main") -> bytes | None:
    status, body = fetch(f"{RAW}/{OWNER}/{repo}/{ref}/{path}")
    return body if status == 200 else None


def link_status(url: str) -> int | None:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as error:
        if error.code in (403, 405, 429):  # some hosts refuse HEAD; ask again with GET
            return fetch(url, timeout=20)[0]
        return error.code
    except (urllib.error.URLError, TimeoutError, OSError):
        return fetch(url, timeout=20)[0]


def sha256(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def page_sha256(html: bytes | None) -> str | None:
    """The page's hash with its footer's build date blanked: the same commit built on another day (or in another
    timezone, CI runs in UTC) is the same page."""
    if html is None:
        return None
    return sha256(re.sub(rb"built \d{4}-\d{2}-\d{2}", b"built <date>", html))


def listed_ids(graph: dict | None) -> list[str]:
    if not graph:
        return []
    return [p["id"] for p in graph.get("packages", [])] + [a["id"] for a in graph.get("agents", [])]


def main_head(repo: str) -> dict | None:
    commit = gh(f"repos/{OWNER}/{repo}/commits/main")
    if not isinstance(commit, dict) or "sha" not in commit:
        return None
    return {"sha": commit["sha"], "committed": commit["commit"]["committer"]["date"]}


def behind(repo: str, graph_sha: str | None, head: dict | None) -> dict:
    """How far main has moved past the sha the directory records, and since when (the first push it missed)."""
    out = {"graph_sha": graph_sha, "status": "unknown", "ahead_by": None, "first_missed_t": None, "how": None}
    if not graph_sha or not head or not re.fullmatch(r"[0-9a-f]{7,40}", graph_sha):
        return out  # absent, or "<sha>-dirty": the directory recorded a tree nobody can fetch
    if head["sha"].startswith(graph_sha):
        out.update(status="identical", ahead_by=0)
        return out
    compare = gh(f"repos/{OWNER}/{repo}/compare/{graph_sha}...{head['sha']}")
    if not isinstance(compare, dict):
        return out
    out.update(status=compare.get("status"), ahead_by=compare.get("ahead_by"))
    if out["status"] != "ahead":
        return out
    pushes = gh(f"repos/{OWNER}/{repo}/activity?ref=refs/heads/main&per_page=100")
    if isinstance(pushes, list):
        pushes = sorted(pushes, key=lambda a: a["timestamp"])
        for i, push in enumerate(pushes):
            if push["after"].startswith(graph_sha) and i + 1 < len(pushes):
                out.update(first_missed_t=pushes[i + 1]["timestamp"], how="push after the recorded sha")
                return out
    commits = compare.get("commits") or []
    if commits:  # the recorded sha was mid-push or older than the activity window: its first successor's commit time
        out.update(first_missed_t=commits[0]["commit"]["committer"]["date"], how="first newer commit's date")
    return out


def owner_repos() -> list[dict] | None:
    repos, page = [], 1
    while True:
        batch = gh(f"users/{OWNER}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(batch, list):
            return None
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def repo_facts(repo: dict) -> dict:
    name = repo["name"]
    pyproject = raw(name, "pyproject.toml", repo.get("default_branch") or "main")
    declaration = raw(name, "robot-sdk.toml", repo.get("default_branch") or "main")
    return {
        "name": name,
        "fork": repo.get("fork"),
        "archived": repo.get("archived"),
        "private": repo.get("private"),
        "uses_robot_msgs": bool(pyproject and DEPENDS_ON_MSGS.search(pyproject.decode("utf-8", "replace"))),
        "has_declaration": declaration is not None,
    }


def ci_on_main(repo: str) -> dict | None:
    runs = gh(f"repos/{OWNER}/{repo}/actions/runs?branch=main&status=completed&per_page=100")
    if not isinstance(runs, dict):
        return None
    newest: dict[str, str] = {}
    for run in runs.get("workflow_runs", []):  # newest first
        newest.setdefault(run["name"], run["conclusion"])
    return newest


def pypi_versions(repo: str, pypi_name: str | None) -> dict:
    out = {"pyproject": None, "pypi": None, "pypi_name": pypi_name}
    text = raw(repo, "pyproject.toml")
    if text:
        try:
            project = tomllib.loads(text.decode("utf-8"))["project"]
            out["pyproject"] = project.get("version")
            out["pypi_name"] = pypi_name or project.get("name")
        except (tomllib.TOMLDecodeError, KeyError):
            pass
    if out["pypi_name"]:
        info = fetch_json(f"https://pypi.org/pypi/{out['pypi_name']}/json")
        if isinstance(info, dict):
            out["pypi"] = info.get("info", {}).get("version")
    return out


def agent_names(repos: list[dict] | None) -> list[str]:
    """The owner's public repos whose robot-sdk.toml on the default branch says role = "agent" (tools.sdk_graph
    discovers agents among sibling checkouts, so the fresh build must clone them)."""
    found = []
    for repo in repos or []:
        if repo.get("fork") or repo.get("archived") or repo.get("private"):
            continue
        body = raw(repo["name"], "robot-sdk.toml", repo.get("default_branch") or "main")
        try:
            if body and tomllib.loads(body.decode("utf-8")).get("role") == "agent":
                found.append(repo["name"])
        except (tomllib.TOMLDecodeError, UnicodeDecodeError):
            continue
    return sorted(found)


def rebuild(agents: list[str]) -> dict | None:
    """A fresh build from public clones at main: robot_sdk's own generator and lint, and its own page builder
    (site/publish_dashboard.py when main has it, else site/build.py)."""
    with tempfile.TemporaryDirectory(prefix="rsa-rebuild-") as scratch:
        root = Path(scratch)
        sdk = root / SDK_REPO

        def git_clone(repo: str) -> bool:
            done = subprocess.run(["git", "clone", "--quiet", "--depth", "1", f"https://github.com/{OWNER}/{repo}.git",
                                   str(root / repo)], capture_output=True, text=True)  # fmt: skip
            return done.returncode == 0

        if not git_clone(SDK_REPO):
            return None
        meta = tomllib.loads((sdk / "pyproject.toml").read_text(encoding="utf-8"))
        repos = [Path(s["path"]).name for s in meta.get("tool", {}).get("uv", {}).get("sources", {}).values() if "path" in s]
        cloned = {repo: git_clone(repo) for repo in dict.fromkeys(repos + agents)}
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        build = subprocess.run([sys.executable, "-m", "tools.sdk_graph", "build"], cwd=sdk, capture_output=True, text=True, env=env)
        check = subprocess.run([sys.executable, "-m", "tools.sdk_graph", "check"], cwd=sdk, capture_output=True, text=True, env=env)
        builder = "site/publish_dashboard.py" if (sdk / "site" / "publish_dashboard.py").exists() else "site/build.py"
        page = subprocess.run([sys.executable, builder], cwd=sdk, capture_output=True, text=True, env=env)
        graph_path = sdk / "site" / "data" / "graph.json"
        lint = {}
        for line in check.stdout.splitlines():
            match = re.match(r"(pass|fail|undeclared)\s+(\S+)$", line)
            if match:
                lint[match.group(2)] = match.group(1)
        links: list[str] = []
        relative: dict[str, bool] = {}
        for doc in ("README.md", "skill/SKILL.md"):
            path = sdk / doc
            if not path.exists():
                continue
            for target in MD_LINK.findall(path.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://")):
                    links.append(target)
                elif not target.startswith(("#", "mailto:")):
                    local = (path.parent / target.split("#", 1)[0]).resolve()
                    sibling = local.relative_to(root).parts[0] if local.is_relative_to(root) else None
                    # a ../<repo>/ link is a sibling checkout: alive when that repo exists on GitHub (checked as a URL)
                    if sibling and sibling != SDK_REPO:
                        links.append(f"https://github.com/{OWNER}/{sibling}")
                    else:
                        relative[f"{doc} -> {target}"] = local.exists()
        index = sdk / "site" / "_build" / "index.html"
        return {
            "cloned": cloned,
            "build_exit": build.returncode,
            "graph": json.loads(graph_path.read_text(encoding="utf-8")) if build.returncode == 0 and graph_path.exists() else None,
            "lint_exit": check.returncode,
            "lint": lint,
            "page_builder": builder,
            "page_exit": page.returncode,
            "index_html_sha256": page_sha256(index.read_bytes()) if page.returncode == 0 and index.exists() else None,
            "doc_links": sorted(set(links)),
            "relative_links": relative,
        }


def collect(directory: str = "live") -> dict:
    """directory="live": score the graph the live site serves. "main": robot_sdk main's committed graph (the status quo
    before any refresh solution, kept as a diagnostic and for the no-solution baseline)."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    live_graph = fetch_json(f"{SITE}data/graph.json")
    status, index_html = fetch(SITE)
    main_raw = raw(SDK_REPO, "site/data/graph.json")
    main_graph = json.loads(main_raw) if main_raw else None
    graph = live_graph if directory == "live" else main_graph
    repos = owner_repos()
    public = [r for r in repos or [] if not r.get("private")]
    built = rebuild(agent_names(public)) if repos is not None else None
    truth_graph = built and built["graph"]
    ids = list(dict.fromkeys(listed_ids(truth_graph) + listed_ids(graph)))
    heads = {repo: main_head(repo) for repo in ids}
    sources = (graph or {}).get("sources", {})
    pypi_of = {p["id"]: p.get("pypi") for p in (truth_graph or graph or {}).get("packages", [])}
    package_ids = list(pypi_of)
    urls = set((built or {}).get("doc_links", []))
    for node in (graph or {}).get("packages", []) + (graph or {}).get("agents", []):
        if node.get("repo_url"):
            urls.add(node["repo_url"])
    for node in (graph or {}).get("types", []):
        if node.get("docs_url"):
            urls.add(node["docs_url"])
    return {
        "schema": INPUTS_SCHEMA,
        "ruler": RULER,
        "collected": now,
        "directory": directory,
        "graph": graph,
        "live_graph_sources": (live_graph or {}).get("sources"),
        "main_graph_sources": (main_graph or {}).get("sources"),
        "site": {"index_status": status, "index_html_sha256": page_sha256(index_html)},
        "rebuild": built,
        "heads": heads,
        "behind": {repo: behind(repo, sources.get(repo), heads.get(repo)) for repo in ids},
        "repos": [repo_facts(r) for r in public] if repos is not None else None,
        "declarations": {pkg: raw(pkg, "robot-sdk.toml") is not None for pkg in package_ids} if package_ids else None,
        "links": {url: link_status(url) for url in sorted(urls)} if urls else None,
        "ci": {pkg: ci_on_main(pkg) for pkg in package_ids} if package_ids else None,
        "pypi": {pkg: pypi_versions(pkg, pypi_of[pkg]) for pkg in package_ids} if package_ids else None,
    }
