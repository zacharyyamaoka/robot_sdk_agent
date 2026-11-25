# Robot SDK Agent

**[▶ Live page](https://zacharyyamaoka.github.io/robot_sdk_agent/)**, redeployed from `main` on every push · a black-box agent repo in the trajectory_tracking_agent format

An agent that keeps [robot-sdk](https://github.com/zacharyyamaoka/robot_sdk) a true, current directory of the robot-*
packages. Each package describes itself in its own `robot-sdk.toml`; robot_sdk aggregates those into `graph.json`
and lints them against the code. This agent's job is to keep that aggregate, and the live site built from it, fresh,
true and complete. A frozen scorer measures it from public data only; a population of refresh mechanisms competes on it.

| File | What's in it |
|---|---|
| [`OBJECTIVES.md`](OBJECTIVES.md) | **Objectives & gates**: the black box, every metric and how it is computed, the gates, the frozen ruler's hash |
| [`AGENTS.md`](AGENTS.md) | How an agent works here: the loop and its rules |
| [`PROGRESS.md`](PROGRESS.md) | Where the search stands (generated from `ledger.jsonl`) |
| [`ideas.md`](ideas.md) | The experiment queue |
| [`REFERENCES.md`](REFERENCES.md) | Prior art and what this builds on |
| [`solutions/`](solutions/) | The population: one folder per solution, its lineage, scorecard and the saved inputs of every score |
| [`scorer/`](scorer/) | The frozen ruler: `collect.py` (public data in) and `score.py` (pure scorecard out) |
| [`site/`](site/) | The live page: reads only `ledger.jsonl` and `status.json` |

```bash
python3 tools/rda.py evaluate s0
```

Stdlib only (Python ≥ 3.11, `git`); `gh auth token` or `GITHUB_TOKEN` is used only for GitHub's rate limit.
Part of [robot-sdk](https://github.com/zacharyyamaoka/robot_sdk): packages are what agents build; agents are what
build them. It imports no package; robot_sdk's generator is run as a subprocess on public clones.
