# `s0`: one hourly workflow in robot_sdk

The simplest thing that keeps the directory fresh. The code lives where it runs, in robot_sdk (this agent imports
packages and never the other way round), pinned in `meta.json`:

- [`.github/workflows/refresh-directory.yml`](https://github.com/zacharyyamaoka/robot_sdk/blob/main/.github/workflows/refresh-directory.yml):
  triggers on a cron (`17 * * * *`), on every push to robot_sdk main, on `workflow_dispatch`, and on a
  `repository_dispatch` of type `package-pushed` (nothing sends one yet: that is idea 1 in `ideas.md`).
- [`tools/refresh/refresh.py`](https://github.com/zacharyyamaoka/robot_sdk/blob/main/tools/refresh/refresh.py):
  reads the listed repos from robot_sdk's own `pyproject.toml` (`[tool.uv.sources]`) and README's agents table, clones
  each at main as a sibling, runs `python -m tools.sdk_graph build` and `check`, runs `site/build.py`, puts the graph at
  `site/_build/data/graph.json`, and commits `site/_build` onto gh-pages with a temporary index when the tree changed.
  An unchanged graph keeps its old bytes (and `generated`), so a no-op run commits nothing. A lint failure still
  publishes (the graph carries each package's lint status) and then turns the run red.

Never writes robot_sdk main: other lanes own `site/data/graph.json` there.

Known limits (what the next solutions attack): up to an hour (plus GitHub's cron delay) behind a package push; a
repo that starts using robot_msgs is never discovered (only the listed ones are cloned); GitHub disables a cron after
60 days without repo activity; `site/publish_pages.py` (the local publisher) now finds gh-pages ahead of its local
branch and must fetch first.
