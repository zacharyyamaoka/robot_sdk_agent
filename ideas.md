# Ideas (the queue)

Each idea says what it should move and by how much. Cross a line off with the solution id that tried it; never
delete it.

## I'll try

- [x] ~~The simplest thing: one hourly workflow in robot_sdk that clones every listed repo, regenerates graph.json,
  lints, rebuilds the page and publishes to gh-pages when it changed~~ → `s0`. Fresh (worst 0 h at scoring), lint
  clean, graph true, site current right after a run (ruler v2: 5 of 10 gates); fails coverage, the missing robot_collision upstream, links, CI and PyPI (none of which a cron can fix). A score taken minutes after a peer push fails site_current until the next run (04:39 vs 04:44 rows).
- [ ] **Push-triggered refresh**: a tiny workflow in each package (`on: push: branches: [main]`) that sends
  `repository_dispatch` (type `package-pushed`) to robot_sdk; s0's workflow already listens for it. Expect: worst
  staleness from ≤ ~1 h (cron) to ≤ ~2 min; `site_current` passes on most snapshots. Needs: a fine-grained token with
  `contents: write`/dispatch on robot_sdk stored as a secret in each package (Zach: a secret).
- [x] ~~Missing upstream: a package pinned before its first public push (robot_collision, 2026-11-24) crashed s0's clone and turned the run red~~ → s0 @ 101156e keeps it from the last good graph (`upstream: "missing"`); ruler v2 scores it once (`upstream_public`).
- [ ] **Missing-upstream nudge**: when `upstream_public` is red for more than a day, open an issue on robot_sdk naming the package and its publish script. Expect: the gate's red time shrinks; the push itself stays Zach's.
- [ ] **Weekly discovery sweep**: list the owner's public repos, flag any whose pyproject names robot-msgs or which
  carry a `robot-sdk.toml` and that the directory doesn't list; open an issue (or a PR adding the pin) on robot_sdk.
  Expect: `listed_all` red → issue within a week (today: dataclass_coverage, gripper-collision-tuner).
- [ ] **Dead-link PRs**: robotmsgs.com's per-type pages (`/types/<module>/<Type>/`) 404 for 13 types; either the
  robot_msgs site generates them or `docs_url` points where they exist. A PR to robot_msgs. Expect: `links_alive` green.
- [ ] **Release-lag PRs**: for each package whose pyproject version is ahead of PyPI, open an issue/PR that tags the
  release (the publish workflows run on `v*` tags). Expect: `pypi_current` from 13 lagging to 0. Needs: Zach's yes per
  release (a package release reaches other people).
- [ ] **CI-red triage**: for each listed package with a red workflow on main (robot_msgs `site`, robot_reach,
  sim2real, traj_compare at s0), open an issue with the failing job's log tail. Expect: `ci_green` moves only when
  the packages are fixed; the issue is the lever this agent owns.
- [ ] **Cron keepalive**: GitHub disables scheduled workflows after 60 days with no repo activity; the push trigger
  usually prevents it, but a monthly no-op commit or `gh workflow enable` check would make it certain.
- [ ] **Continuous scoring**: a scheduled workflow here that runs `tools/rda.py evaluate` every few hours and commits
  the row, so `max_stale_hours` becomes a distribution over time instead of one snapshot (ruler v2 could gate on its
  p95).
- [ ] **Commit the graph on robot_sdk main too**, once the lanes there stop editing it: keeps main's
  `site/data/graph.json` (and the generated README tables) current, not just the live site.
- [ ] **publish_pages.py interplay**: robot_sdk's local `site/publish_pages.py` builds on the *local* gh-pages ref,
  so after a bot publish its push is non-fast-forward until it fetches. A PR to the site lane: start from
  `origin/gh-pages`.
- [ ] **Adopt blackbox_agent's viewer** (fold + Pages workflow) instead of this repo's small page, once its fold
  reads a ledger with list-valued `failed_gates`.
