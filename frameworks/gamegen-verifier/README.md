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

Smoke mode makes no backend calls: it runs the framework's own unit tests and
`--help` on every public entry point. On this host it exited 0 with 9 tests
passing and all 7 entry points loading.

## Lab boundary

GAME-311 adapts the framework to the frozen Number Line Jumper build with the
smallest viable integration. The five locked keypoints are defined in GAME-308
and GAME-311. Do not expand the experiment into the upstream full generation
benchmark or build a custom OpenCode backend.

Codex is the primary backend where the framework natively supports it. OpenCode
remains an alternate lab reviewer/orchestrator rather than a required native
GameGen-Verifier backend.

## What this directory adds

| Path | Purpose |
| --- | --- |
| `prepare_workspace.py` | Builds `.frameworks/ggv-workspace/` from `workspace/` and links the pinned framework, failing closed when either pinned revision differs from `config/experiment.json`. |
| `run_keypoint_campaign.py` | Invokes the pinned harness for the five keypoints; the only place the documented flags are assembled. |
| `windows_posix_shim.py` | Windows-only launcher: the pinned harness starts its game server with a POSIX `.sh` lifecycle script, which Windows cannot exec (`WinError 193`). The shim translates that one call to `bash <script> <args>` and leaves the pinned checkout untouched. |
| `workspace/` | Lab-local inputs the pinned harness requires: the frozen-game description, the game directory (`package.json`, `dev-server.mjs`, `data.md`, `state_injection_api.md`, `keypoints.md`). |

The harness itself is **not** modified: the campaign uses its documented
`--resume-run` path with a pre-seeded `keypoints.snapshot.md` and
`--min-keypoints 5`, which is the framework's own way to reuse an existing
keypoint set instead of distilling 30-40 keypoints from a description.

## Measured results (GAME-311)

| Run | Keypoints | Result | Wall clock |
| --- | ---: | --- | ---: |
| `ggv-nlj-5kp-1` | 5 | 4 PASS / 1 FAIL (80.0%) | 58 min 34 s |
| `ggv-nlj-5kp-2` | 1 (keypoint 1 re-run) | 1 PASS (100%) | 28 min 9 s |

The run-1 FAIL was caused by this directory's keypoint-1 wording (it told the
worker to start the scored round and then press the warm-up reveal control) and
became PASS at confidence 97 after the wording was corrected. Verdicts,
findings, and the full reconciliation are in
[`reports/gamegen-verifier-evaluation.md`](../../reports/gamegen-verifier-evaluation.md).

## Runbook

```bash
# 1. Pin the framework (ignored tree) and a frozen game worktree at the GAME-308 SHA
git clone https://github.com/NetX-lab/GameGen-Verifier.git .frameworks/gamegen-verifier
git -C .frameworks/gamegen-verifier checkout 2604b6b7330ca93c2e9fcb1036daf8cdf660aade

# 2. Python + Playwright prerequisites
uv venv --python 3.12 .frameworks/ggv-venv
uv pip install --python .frameworks/ggv-venv/Scripts/python.exe -r .frameworks/gamegen-verifier/requirements.txt
cp .frameworks/ggv-venv/Scripts/python.exe .frameworks/ggv-venv/Scripts/python3.exe   # the harness shells out to `python3`
( cd .frameworks/gamegen-verifier/tools/playwright && npm install && npm run install:chromium )

# 3. Baseline smoke (no backend calls)
PATH="<abs>/.frameworks/ggv-venv/Scripts:$PATH" python3 .frameworks/gamegen-verifier/scripts/run_all_experiments.py --smoke

# 4. Build the workspace for the frozen game
python3 frameworks/gamegen-verifier/prepare_workspace.py \
  --frozen-game-root "<abs path of the frozen NLJ worktree @47a0548>" \
  --run-id ggv-nlj-5kp-1

# 5. Run the five locked keypoints through the pinned harness with Codex
#    `codex` must be on PATH, or pass --codex-bin <dir containing the CLI>.
python3 frameworks/gamegen-verifier/run_keypoint_campaign.py \
  --run-id ggv-nlj-5kp-1 \
  --step-timeout 1980 --screenshot-mode sequence --max-workers 1

# 6. Validate the artifacts (see deviation 4: the harness's own call is broken)
cd .frameworks/ggv-workspace
python3 .codex/skills/keypoint-orchestrator/scripts/validate_artifacts.py \
  --run-root runs/number_line_jumper/ggv-nlj-5kp-1 --test-mode normal --expected-count 5
```

Raw evidence lands under `.frameworks/ggv-workspace/runs/number_line_jumper/<run_id>/`
(git-ignored). Durable, normalized results belong in
`reports/gamegen-verifier-evaluation.md` and `reports/findings/`.

## Known platform deviations (Windows host)

1. `.sh` lifecycle script cannot be executed by `CreateProcess`; the lab shim
   runs it through Git Bash (`windows_posix_shim.py`).
2. The pinned stop path reports `STOP_RESULT=stopped` but terminates only the
   shell/npm wrapper, not the detached Vite grandchild: the game server stayed
   listening on 127.0.0.1:4173 / :4174 after both runs. Confirm and kill the
   listener by PID from `runs/.server_state/<game>.env` before re-running,
   otherwise the next run can silently reuse the previous server.
3. `python3` must resolve to the lab venv (the harness and its validators shell
   out to `python3`, not `sys.executable`).
4. The harness's final validation step passes `--repo-root/--game-name/
   --run-id/--expected-keypoint-count/--json-output`, while the workspace's
   installed `validate_artifacts.py` accepts `--run-root/--test-mode/
   --expected-count`. The step therefore always exits on an argparse usage
   error, every run reports `validation_failed=True`, and no
   `validation_report.json` is written. Validate manually with step 6 above;
   both GAME-311 runs passed. Tracked as `GGV-002`.
5. The frozen build has no state-injection API, so the framework's
   `generative-state-construction` step cannot inject a near-threshold prestate;
   workers establish scenarios through the normal UI and read DOM/ARIA state.
   See `workspace/games/number_line_jumper/state_injection_api.md` (`GGV-004`).
6. A worker writes its result and then does not exit, so each run waits out the
   full `--step-timeout` (24-27 idle minutes here) and still reports
   `worker_failures=1` for a complete keypoint. Tracked as `GGV-003`.
