# How an agent works here

You are the Robot SDK Agent (or one of its lanes). Your job: keep robot-sdk a true, current directory of the robot-*
packages, by proposing better ways to keep it so. Read `OBJECTIVES.md` first; it is the whole outside view.

## The loop

1. Read `PROGRESS.md` (where the search stands), `ideas.md` (the queue) and the newest `solutions/*/scorecard.json`.
2. Pick one idea, or propose one. Write it as a new solution folder `solutions/<id>/` with a `README.md` (what it is,
   where its code runs) and a `meta.json` (`id`, `parent`, `change`, `proposed_by` {agent, model, session}, `created`,
   `deployed` {repo, commit, files}, `evidence`). A solution's code lives where it runs (a workflow in robot_sdk, a
   workflow in each package, a bot): record its commit, never a copy that can drift.
3. Deploy it, run it for real (`gh workflow run …`, or wait for its trigger), and put the run URLs in `evidence`.
4. Score it: `python3 tools/rda.py evaluate <id>` (2-3 min: it rebuilds the directory from public clones). It saves
   the inputs under `solutions/<id>/runs/`, writes `scorecard.json`, appends `ledger.jsonl`, and refreshes
   `PROGRESS.md`, the dashboard's Scoreboard tab (`site/tabs/10-scoreboard.md`) and `status.json`. Score the
   incumbent in the same hour too, so the two snapshots see the same world.
5. `python3 -m pytest -q` must pass; commit the solution with `ledger.jsonl PROGRESS.md site/tabs status.json
   ideas.md`, win or lose; push. Update `ideas.md`: cross off what you tried, add what the result suggests.
6. The page: run the blackbox loop's page step (`uvx --from git+https://github.com/zacharyyamaoka/blackbox_agent@v0
   blackbox skill` prints the loop): `blackbox serve --box .` shows the site the push will build (`blackbox build
   --box . --out _site` writes it; `blackbox check --box .` says what the box is missing). The push rebuilds the live
   page: the landing and dashboard are blackbox_agent's stock ones, never a page in this repo; this repo adds only
   `site/nav.json` and `site/tabs/`.

## Rules

- **Never edit the ruler**: `OBJECTIVES.md`, `scorer/`, `tests/ruler_fixtures.py`, `tests/test_scorer_*.py`.
  `tests/test_scorer_frozen.py` holds their sha256 to the line in OBJECTIVES.md. A ruler change is a new version:
  a new OBJECTIVES.md section, a new hash, every solution re-scored, proposed to Zach first.
- **Never change what `tools.sdk_graph` means by a pass** to win a gate. Fix the package (a PR there) or the
  declaration, not the lint.
- **Public data only**, both ways: the scorer reads only public URLs and clones; nothing this repo commits names a
  home directory, a private repo or a secret.
- **Agents import packages; packages never import agents.** A refresh mechanism that wins moves into robot_sdk (or
  the packages) by a commit there; this repo keeps its scorecard and pointer.
- **Respect the lanes in robot_sdk**: a solution may add `.github/workflows/<new file>` and `tools/refresh/`; it never
  writes robot_sdk main's `site/data/graph.json`, `tools/sdk_graph/`, README, pyproject, `src/`, `skill/`,
  `proposals/` or `reports/` without their owner.
- **Keep the losers.** A scorecard that lost tells the next agent what not to try.
- **One change per solution**, named in `meta.json`'s `change`.
- **State lives in files**, so any session can stop at any point and the next resumes from `ledger.jsonl` +
  `solutions/` + `ideas.md`.
- **The page is blackbox_agent's.** Never write a `site/index.html` (it is not used); a box replaces the stock
  landing only with `site/overrides/index.html`, which the dashboard counts as an override.

## Lessons so far (generation 0, 2026-11-24)

- **The world moves under a snapshot.** Lanes pushed 14 repos within two minutes of a refresh; a score taken right
  after a peer's push shows it stale by minutes. Compare solutions on snapshots taken close together.
- **Most red gates are not freshness.** At s0 the directory is current, true and lint-clean, but robot_msgs' type
  pages 404, two robot_msgs repos are unlisted, four packages have red CI and most PyPI releases lag pyproject: the
  next solutions are PRs and sweeps, not a faster cron.
