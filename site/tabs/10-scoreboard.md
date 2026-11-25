# Scoreboard

The directory this agent keeps true and current: **[robot-sdk](https://zacharyyamaoka.github.io/robot_sdk/)** ([graph.json](https://zacharyyamaoka.github.io/robot_sdk/data/graph.json), [repo](https://github.com/zacharyyamaoka/robot_sdk)). Every gate and how it is measured: [OBJECTIVES.md](https://github.com/zacharyyamaoka/robot_sdk_agent/blob/main/OBJECTIVES.md).

Generated with PROGRESS.md by `python3 tools/rda.py progress` from `ledger.jsonl` (ruler v2); never edit by hand.

**Best: `s0`**, 5 of 10 gates, worst staleness **0.00 h** (not admissible: ci_green, links_alive, listed_all, pypi_current, upstream_public), scored 2026-11-25T04:44:03+00:00.

## Solutions (newest score of each, best first)

| solution | scored | max stale (h) | gates passed | failed gates |
|---|---|---|---|---|
| `s0` | 2026-11-25T04:44:03+00:00 | 0.00 | 5/10 | ci_green, links_alive, listed_all, pypi_current, upstream_public |
| `none` | 2026-11-25T04:36:01+00:00 | 0.07 | 3/10 | ci_green, graph_true, links_alive, listed_all, pypi_current, site_current, upstream_public |

## Gate matrix (newest score of each)

| solution | `fresh_24h` | `lint_clean` | `graph_true` | `listed_all` | `upstream_public` | `declared_all` | `links_alive` | `ci_green` | `pypi_current` | `site_current` |
|---|---|---|---|---|---|---|---|---|---|---|
| `s0` | pass | pass | pass | **fail** | **fail** | pass | **fail** | **fail** | **fail** | pass |
| `none` | pass | pass | **fail** | **fail** | **fail** | pass | **fail** | **fail** | **fail** | **fail** |

## Last 10 ledger rows

| t | solution | directory | max stale (h) | lint fails | unlisted | undeclared | dead links | CI not green | PyPI behind |
|---|---|---|---|---|---|---|---|---|---|
| 2026-11-25T04:28:33+00:00 | `none` | main | — | 0 | 3 | 0 | 13 | 4 | 13 |
| 2026-11-25T04:30:08+00:00 | `s0` | live | 0.00 | 0 | 2 | 0 | 13 | 4 | 13 |
| 2026-11-25T04:36:01+00:00 | `none` | main | 0.07 | 0 | 2 | 0 | 15 | 4 | 13 |
| 2026-11-25T04:39:27+00:00 | `s0` | live | 0.03 | 0 | 2 | 0 | 15 | 4 | 13 |
| 2026-11-25T04:44:03+00:00 | `s0` | live | 0.00 | 0 | 2 | 0 | 15 | 4 | 13 |
