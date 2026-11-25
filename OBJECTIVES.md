# Objectives & Gates (ruler v1, frozen 2026-11-24)

The outside of the black box: what the directory must be, how a script measures it from public data, and how a
solution is scored. Nothing here says how a solution keeps the directory current. Changing anything in this file or
in the ruler files makes **ruler v2**: a new section below, a new hash, and every solution re-scored on it.
A solution never edits this file, `scorer/`, `tests/ruler_fixtures.py` or `tests/test_scorer_*.py`.

ruler sha256: `cbe90a9978ccd813c2e56b7281e0bf953b7fbbeaa15a401b62e459089ebf19a7`

(`python3 tests/test_scorer_frozen.py` prints it; `tests/test_scorer_frozen.py` fails when the files and this line
disagree.)

WHY (Zach, 2026-11-24): *"One of the goals of course is kinda like that the information is kept up to date."* Each
package describes itself in its own `robot-sdk.toml`; robot_sdk aggregates them into `graph.json` and lint-verifies
them; keeping that aggregate fresh is an agent's job with a metric.

## 1. The black box

```text
IN (given; a solution never changes them)
  the robot-* repos on github.com/zacharyyamaoka, each at its main branch     (public)
  robot_sdk's generator and lint: python -m tools.sdk_graph build | check   (robot_sdk main; its contract,
                                                                              docs/graph-schema.md, robot-sdk-graph/1)
  robot_sdk's page builder: site/publish_dashboard.py (else site/build.py)

THE BLACK BOX: whatever keeps the directory current (a workflow, a bot, webhooks, PRs to packages ...)

OUT: the directory
  https://zacharyyamaoka.github.io/robot_sdk/data/graph.json     the published graph (robot-sdk-graph/1)
  https://zacharyyamaoka.github.io/robot_sdk/                    the landing page beside it
```

- **The directory is what the world reads: the live site.** A graph committed on robot_sdk main but not published is
  scored only as the `none` baseline (`--directory main`), and fails `site_current`.
- **The truth is a fresh build.** The scorer clones robot_sdk and every repo it lists at main into an empty temp dir
  and runs robot_sdk's own `tools.sdk_graph build`, `check` and `site/build.py` there. What that produces is what the
  directory should say right now.
- **A solution may change the packages** (a PR that adds a `robot-sdk.toml`, fixes CI, cuts a release) and robot_sdk
  outside the lanes' files. It never changes the ruler, and it never changes what `tools.sdk_graph` means by a pass.
- **Public data only.** Every input is a public URL, a public API endpoint or a public clone; a token, if present, is
  used only for GitHub's rate limit.

## 2. The metrics (each computed by `scorer/collect.py` + `scorer/score.py`)

Let *listed* = every package (robot_sdk's pins) and agent (a public repo of the owner whose own `robot-sdk.toml` says `role = "agent"`) id in the fresh build's graph or in the published graph (robot_sdk itself is
not listed: it is the directory). `now` = the time the inputs were collected.

| Metric | How it is computed | Source |
|---|---|---|
| **`max_stale_hours`** (the objective) | For each listed repo: 0 if the published graph's `sources[repo]` is main's head; else hours from the **first push to main the graph missed** to `now` (GitHub's repo activity API: the push after the one whose `after` is the recorded sha; if that sha was mid-push or is older than the activity window, the committer date of the first newer commit from the compare API). The worst repo. `None` (= ∞) when any listed repo is missing from `sources`, recorded `-dirty`, diverged, or not comparable. | `/repos/o/r/commits/main`, `/compare/a...b`, `/activity?ref=refs/heads/main` |
| `stale_packages` | count of listed repos with staleness > 0 or unknown | same |
| `lint_failures`, `lint_pass_rate` | robot_sdk's `python -m tools.sdk_graph check` on the fresh build: packages not `pass` (an `undeclared` one is counted under coverage instead); a package the check never names counts as a failure | fresh build |
| `graph_matches_rebuild` | the published graph equals the fresh build's, ignoring `generated` and `sources` (freshness scores those) | live graph vs fresh build |
| `unlisted_repos` | public, non-fork, non-archived repos of the owner whose `pyproject.toml` on the default branch names `robot-msgs`/`robot_msgs`, or which carry a `robot-sdk.toml`, and are not listed (nor robot_sdk) | `/users/o/repos`, raw.githubusercontent.com |
| `undeclared_packages` | listed packages with no `robot-sdk.toml` on main | raw.githubusercontent.com |
| `dead_links` | every `repo_url` and `docs_url` in the published graph and every absolute link in robot_sdk's `README.md` and `skill/SKILL.md` (a `../<repo>` link = that repo's GitHub URL) that answers ≥ 400 or not at all (HEAD, then GET when HEAD is refused); plus every other relative link there that names no file in the fresh clone | the links themselves |
| `ci_not_green` | listed packages where, on main, the newest completed run of any workflow is not `success`/`skipped`, or where there is no completed run on main | `/repos/o/r/actions/runs?branch=main&status=completed` |
| `pypi_mismatch` | listed packages whose PyPI latest version ≠ the `version` in `pyproject.toml` on main (either missing counts) | pypi.org JSON API, raw pyproject |
| `site_serves_graph` | the live `data/graph.json` parses with schema `robot-sdk-graph/1` | live site |
| `site_sources_match_rebuild` | the live graph's `sources` (robot_sdk's and every listed repo's commit) equal the fresh build's: the site is built from the latest graph | live graph vs fresh build |
| `site_page_matches_main` | the live `index.html` equals robot_sdk main's page builder output on the fresh clone (`site/publish_dashboard.py`, the V5 dashboard that reads `data/graph.json` at runtime, when main has it; else `site/build.py`), with any footer build date blanked | live site vs fresh build |

## 3. The gates (a solution is *admissible* only if every gate passes)

| Gate | Pass when | Why |
|---|---|---|
| `fresh_24h` | `max_stale_hours` ≤ 24 | Zach's "kept up to date": nothing in the directory is more than a day behind its repo |
| `lint_clean` | `lint_failures` = 0 and the check exits 0 | a declaration that lies about the code is worse than none |
| `graph_true` | `graph_matches_rebuild` | the published facts are the facts a fresh build gives |
| `listed_all` | `unlisted_repos` empty | a robot_msgs package the directory doesn't list is invisible |
| `declared_all` | `undeclared_packages` empty | each package describes itself (decentralized self-description) |
| `links_alive` | `dead_links` empty (and ≥ 1 link checked) | a directory that points nowhere |
| `ci_green` | `ci_not_green` empty | a listed package should build on main |
| `pypi_current` | `pypi_mismatch` empty | what the directory lists is what `pip install` gets |
| `site_current` | `site_serves_graph`, `site_sources_match_rebuild` and `site_page_matches_main` | the live site is built from the latest graph and main, right now (stricter than `fresh_24h`: any push the site hasn't caught yet fails it) |

**Every verdict fails closed:** a missing or malformed input is a failed gate and a `None` metric, never a pass. With
no published graph at all, every gate fails. `tests/test_scorer_fail_closed.py` holds this, first.

**Ranking:** admissible first; then by gate pass rate (higher first); then by `max_stale_hours` (lower first, `None`
last). The *best* solution is the top row.

**A score is a snapshot of the world.** The world moves (a peer pushes, CI goes red), so a solution is scored by
`tools/rda.py evaluate <id>`, which saves the exact inputs beside it (`solutions/<id>/runs/<t>.inputs.json`); any row
re-derives offline with `python -m scorer score <that file>`. Compare solutions on scores taken close in time, and
prefer several snapshots over one.

## 4. Deferred to ruler v2 (named so nobody thinks they were forgotten)

Freshness of the robot_sdk README/skill prose (only its links are checked); a staleness *distribution* over a window
instead of a snapshot (needs a scheduled scorer); agents' own declarations (the `role = "agent"` format is being
defined in tools/sdk_graph); repos outside the owner; CI on pull requests; the PyPI wheel's content vs main.
