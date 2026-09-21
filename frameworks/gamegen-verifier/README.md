# GameGen-Verifier evaluation notes

## Pinned upstream

- Repository: `NetX-lab/GameGen-Verifier`
- Revision: `2604b6b7330ca93c2e9fcb1036daf8cdf660aade`
- Role in GAME-308: bounded state-grounded verification with PASS/FAIL-style results and before/after evidence.

## Upstream baseline

At the pinned revision, upstream documents:

```bash
python3 -m pip install -r requirements.txt
( cd tools/playwright && npm install && npm run install:chromium )
python3 scripts/run_all_experiments.py --smoke
codex login
python3 scripts/run_all_experiments.py --games tetris --backend codex
```

Requirements documented upstream include Python 3.11+, Node.js 20+, npm, Chromium/Playwright dependencies, and an authenticated `codex` or `claude` CLI for full runs.

## Lab boundary

GAME-311 should adapt the framework to the frozen Number Line Jumper build using the smallest viable integration. The five locked keypoints are defined in Jira GAME-308/GAME-311. Do not expand the experiment into the upstream full generation benchmark or build a custom OpenCode backend unless it is trivially small and demonstrably useful.

Codex is the primary backend where the framework natively supports it. OpenCode remains an alternate lab reviewer/orchestrator rather than a required native GameGen-Verifier backend.

## Expected raw evidence

Upstream writes reports, per-keypoint JSON, and screenshots below `runs/` plus launch summaries below `experiments/`. Those bulky/generated trees remain local/gitignored; normalized durable findings belong in this repository.
