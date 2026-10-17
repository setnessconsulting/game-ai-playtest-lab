# GAME-311 — GameGen-Verifier evaluation

Status: The bounded GameGen-Verifier evaluation is complete. The pinned
framework runs unmodified on its supported baseline and produced one campaign
across the five GAME-311 keypoints against the frozen Number Line Jumper build,
with per-keypoint PASS/FAIL verdicts, before/after screenshots, DOM/ARIA
observations, and four normalized framework findings. The single in-campaign
FAIL was traced to the lab's own keypoint wording and was corrected and re-run
to PASS on the same pinned inputs; it is not a game defect.

Scope note: this evaluation verifies the pinned framework's *verification* path
(keypoint → generated Playwright script → screenshot/DOM evidence → contract
decision). It does not exercise the upstream game-generation, keypoint
distillation, or ablation benchmarks, and it does not claim upstream catalog
registration or provider parity.

## Frozen inputs

| Input | Revision / value |
| --- | --- |
| Game | Number Line Jumper |
| Game revision | `47a05480d7c32cee8f0991d6f6c0410be90d678e` |
| Game worktree | `_worktrees/game-number-line-jumper/game-308-frozen-opencode` (clean, detached at the frozen SHA) |
| GameGen-Verifier | `NetX-lab/GameGen-Verifier` @ `2604b6b7330ca93c2e9fcb1036daf8cdf660aade` |
| Lab base revision | `6e9fd11ca8e07436ca0be6c37ae9a7efc545138e` (`origin/main`) |
| Backend | `codex` (`codex-cli 0.163.0-alpha.10.2`), `--reasoning-effort high`, no `--model` override |
| Screenshot mode | `sequence`, 200 ms interval |
| Browser | Framework-bundled headless Chromium (Playwright), 1280×720 viewport |
| Runs | `ggv-nlj-5kp-1` (five keypoints), `ggv-nlj-5kp-2` (keypoint 1 re-run) |

`prepare_manifest.json` in each run directory records the same game revision,
framework revision, frozen game root, and workspace path, written by
`frameworks/gamegen-verifier/prepare_workspace.py`, which fails closed when
`config/experiment.json` and the two checkouts disagree.

The game repository was not modified. Its frozen worktree is clean at
`47a0548`, and the GAME-311 worktree branch `codex/game-311-gamegen-verifier`
is based on live `origin/main` (`6e9fd11`).

## Prerequisites and setup

1. Python 3.12.13 venv (`uv venv .frameworks/ggv-venv`), pinned framework
   `requirements.txt` installed.
2. `python3.exe` copied beside the venv's `python.exe`: the pinned harness and
   its validation step shell out to the literal command `python3`.
3. Playwright Chromium installed through the framework's own
   `tools/playwright` scripts.
4. Codex CLI (version above) authenticated through the owner's existing Codex
   configuration. No API key was copied into the workspace.
5. Windows launcher shim (`frameworks/gamegen-verifier/windows_posix_shim.py`):
   the pinned harness starts the game server through a POSIX `.sh` lifecycle
   script, which Windows cannot exec (`WinError 193`). The shim translates that
   one call to `bash <script> <args>` and leaves the pinned checkout untouched.
6. Workspace prepared by `frameworks/gamegen-verifier/prepare_workspace.py`,
   which copies the lab's `workspace/` inputs (frozen-game description, game
   package + dev-server shim, `data.md`, `state_injection_api.md`,
   `keypoints.md`) and pre-seeds `keypoints.snapshot.md` for the harness's
   documented `--resume-run` path.

No part of `.frameworks/gamegen-verifier` was edited; `git -C
.frameworks/gamegen-verifier status` stays clean across the campaign.

## Upstream baseline result

`python3 scripts/run_all_experiments.py --smoke` exited 0 on the pinned
revision: the framework's 9 unit tests passed, and all 7 public entry points
(`run_all_experiments`, `run_normal_eval`, `run_recheck_eval`,
`prepare/generate_games`, `prepare/distill_keypoints`,
`prepare/export_clean_games`, `ablation/parallel_keypoints`) loaded with
`--help` without error. Log: `.frameworks/logs/smoke-baseline.log`.

Smoke mode is explicitly documented upstream as making no backend calls, so it
proves installation and entry-point integrity, not verification behavior. The
verification path itself was then proven by the campaign below, which drove the
unmodified harness end to end (server lifecycle → keypoint worker → generated
Playwright script → screenshots → contract decision → reports).

## Campaign

Both runs used the framework's own session bounds: `--keypoints-per-session 1`,
`--max-workers 1`, `--resume-run`, `--min-keypoints 5`, pre-seeded keypoints.
That is the framework's documented path for an already-frozen keypoint set; the
lab did not run the 30–40-keypoint distillation stage (see deviations).

### Run `ggv-nlj-5kp-1` — all five keypoints

Wall clock 16:59:14 → 17:57:48 local. Sequential batches, one keypoint per
session.

| Keypoint | Category | Verdict | Confidence | What the artifact demonstrates |
| --- | --- | ---: | ---: | --- |
| 1 — first-time start | Interaction Logic | FAIL | 88 | Cold-load surface usable; the generated script clicked `Start guided round` and then timed out looking for `Reveal example` (script lines 58 and 67), so `Reveal produced a visible response: false` and a forbidden observation tripped |
| 2 — pointer placement | Interaction Logic | PASS | 96 | Two real pointer placements moved the marker and changed `aria-valuetext` in the expected direction; range, focus, and no-error checks held; `Land here` not pressed |
| 3 — answer feedback | State Transition | PASS | 98 | Placement 6.24 → feedback named target 2, reported 42% (4.24 units) error, awarded 2 points; trial 1 stayed visible while feedback was open, trial 2 after `Continue` |
| 4 — progress/state | Game Rule | PASS | 96 | Three submissions advanced trials once each; score 0→2→8→10 monotonic; active-play clock 60→58→57→55 s; still playable at trial 4 of 10 |
| 5 — restart/recovery | Boundary Condition | PASS | 92 | Timed round ended on its summary (points, trials, average error); `Play again` opened a fresh round at score 0 / trial 1; reload returned to level selection |

Aggregate from the harness's own `summary_report.md`: 5 keypoints, 4 passed, 1
failed, 0 incomplete, 80.0% pass rate. Harness execution line:
`worker_failures=1, missing_results=0, contract_failures=0, validation_failed=True`.

### Run `ggv-nlj-5kp-2` — keypoint 1 re-run

Wall clock 17:32:57 → 18:01:06 local, keypoint 1 only, same pins, backend,
model, browser, and viewport. The only change was the lab's keypoint 1
instruction wording (do not start the scored round; use the warm-up reveal
control). Verdict: PASS, confidence 97 — first attempt, no retry: cold-start
surface exposed mode choice, four grade buttons, Explore, and both settings;
Grades 1–2 opened the warm-up with objective, three numbered tips, practice
target/range and placement instruction; real pointer input placed 3.66 on a
0–10 line; `Reveal example` rendered the target marker and explained its
position.

### Keypoint 1 FAIL → PASS reconciliation

The FAIL is fully explained by the lab's keypoint text, not the game. The
original instruction told the worker to activate `Start guided round` and then
press `Reveal example`. Starting the scored round removes the warm-up reveal
control, so the generated script's locator timed out. The worker recorded the
contract honestly (`Reveal produced a visible response: false`,
`forbidden_triggered: true`) but the failure mode was never surfaced as an
*instruction* problem: `error_type` is null and nothing in `result.json`
distinguishes "the game is missing a control" from "the instruction's own
sequence removed the control". Only the artifact review (`test_script.mjs`
lines 58/67) made the cause visible. This is retained as `GGV-001`.

## Persona review lenses

The four canonical personas were used as review lenses over the campaign
evidence, not as a 20-run matrix. Each lens attributes the findings it raised.

| Lens | Evidence reviewed | Gameplay conclusion | Framework finding |
| --- | --- | --- | --- |
| First-time | Keypoint 1 (both runs), cold-start frames | No game defect. The visible surface states the objective, names grades, and the warm-up explains itself; the run-2 PASS is the representative first-time outcome | `GGV-001` (verdict integrity: instruction-induced failure recorded as a game FAIL) |
| Normal | Keypoints 2 and 3, plus run operations | No game defect. Pointer placement and feedback are specific and legible; the clock pausing during feedback is consistent behavior, not a stuck state | `GGV-003` (workers write a verdict then never exit; run stalls to the step timeout and is counted as a worker failure) |
| Expert | Keypoint 4, harness report files, framework exit status | No game defect. Score monotonicity, trial advancement, and clock decrease are mutually consistent across three submissions | `GGV-002` (the harness's final artifact-validation step errors out before validating anything) |
| Adversarial | All five artifacts, `state_injection_api.md`, preconditions | No game defect. Boundary states are only reachable in real time, so near-threshold claims are not asserted | `GGV-004` (the skill set assumes a state-injection seam a frozen external build does not have) |

Rejected candidates are recorded here so they are not silently dropped: the
same-tab "resume or discard the prior guided round" prompt seen after reload in
keypoint 5 is a deliberate session-restore affordance and was not retained as a
defect; keypoint 3's feedback dwell (the panel is only briefly visible unless
`Wait for me after feedback` is enabled) is a configuration choice, not a
missing response; and no evidence supported claims about scoring accuracy,
sound, or timer correctness beyond what keypoint 4 measured.

## Findings

Four normalized findings were retained. Raw evidence stays under the ignored
`.frameworks/ggv-workspace/runs/` tree; the JSON files are the durable records.

| ID | Severity | Confidence | Lens | Summary |
| --- | --- | --- | --- | --- |
| [`GGV-001`](findings/gamegen-verifier-001.json) | medium | high | first-time | A keypoint instruction that removes its own target control yields a game FAIL with no ambiguity signal |
| [`GGV-002`](findings/gamegen-verifier-002.json) | medium | high | expert | The harness's artifact-validation step is invoked with the wrong CLI, so it always errors and no `validation_report.json` is produced |
| [`GGV-003`](findings/gamegen-verifier-003.json) | low | high | normal | Workers that finish writing their verdict but never exit stall the run for the full step timeout and are counted as worker failures |
| [`GGV-004`](findings/gamegen-verifier-004.json) | low | high | adversarial | Keypoint preconditions assume a state-injection seam that frozen external builds do not expose |

Framework-level observations that did not warrant their own finding:

- Headline reports (`summary_report.md`, `evaluation_report.md`) are written
  once at the end of each invocation from that invocation's keypoint set. For
  the ~50 minutes before run 1's final invocation wrote the complete report,
  the on-disk `summary_report.md` described a single keypoint
  (`Total Keypoints: 1`, `Pass Rate: 100.0%`). The final aggregate is correct
  (5 keypoints, 4 passed); the hazard is a reader or CI sampling the run
  directory mid-run. Recorded as an observation in `GGV-003`'s neighborhood, not
  as a separate finding, because the completed artifact is accurate.
- Two artifacts validated cleanly against the framework's own validator
  (`PASS: validated 5 keypoint artifact directories`, and 1 for run 2) once it
  was invoked with the CLI the script actually defines. The artifacts are
  well-formed; only the harness's invocation of the validator is wrong
  (`GGV-002`).

## Cost and throughput (measured)

| Run | Keypoints | Wall clock | Productive span | Idle at step timeout |
| --- | ---: | ---: | ---: | ---: |
| `ggv-nlj-5kp-1` | 5 | 58 min 34 s | last verdict written 17:30:40 | ~27 min (1980 s timeout) |
| `ggv-nlj-5kp-2` | 1 | 28 min 9 s | artifacts complete 17:37:05 | ~24 min (1680 s timeout) |

Per worker, a keypoint's artifacts appear within roughly 4–7 minutes; the
harness then waits out the entire step timeout because the worker process does
not exit (`GGV-003`). Token usage is only reported for some workers in the
logs (`70,168` for keypoint 2, `98,630` for keypoint 4 in run 1), so this
report does not invent an aggregate or a dollar figure.

## Deviations and limitations

1. **Windows server lifecycle.** The pinned harness starts the game with a
   POSIX `.sh` script, which Windows cannot exec. The lab shim runs that one
   call through Git Bash; the pinned checkout is unmodified.
2. **Stale game listener.** Both runs reported `STOP_RESULT=stopped`, but the
   Vite grandchild survived and kept listening on 127.0.0.1:4173 / :4174. Both
   listeners were confirmed to be the frozen game's Vite processes and were
   terminated by PID after the campaign. The next run on the same port would
   otherwise silently reuse the previous server.
3. **Broken validation invocation.** The harness calls its validator with
   `--repo-root/--game-name/--run-id/--test-mode/--expected-keypoint-count/--json-output`,
   while the workspace's installed `validate_artifacts.py` defines
   `--run-root/--test-mode/--expected-count`. Every run therefore records
   `validation_failed=True` and prints a `validation_report.json` path that is
   never created (`GGV-002`). The lab validated both runs manually with the
   correct CLI; this is documented in the framework README runbook.
4. **Five keypoints instead of 30–40.** The framework's distillation stage
   targets 30–40 keypoints from a game description. GAME-311 fixes five
   behavioral keypoints, so the adapter pre-seeds `keypoints.snapshot.md` and
   uses the documented `--resume-run --min-keypoints 5` path. The keypoint file
   deliberately does not satisfy the upstream distillation policy and is not
   lint-gated.
5. **No state injection.** The frozen build exposes no injection hook, so all
   five workers established their scenarios through the visible UI. Near-
   threshold states (last-second timer boundary, the tenth trial) can only be
   reached in real time; keypoint 4 stopped at trial 4 of 10 by design and
   keypoint 5 reached its summary by letting the clock run out. Claims that
   would need injected states are not made (`GGV-004`).
6. **One backend, one model, one repeat.** The campaign used Codex with the
   owner's authenticated default configuration and no `--model` override. No
   second provider, no repeats, and no variance estimate are claimed. OpenCode
   was not built as a GameGen-Verifier backend.
7. **Screenshot volume.** Sequence mode produced 173 / 5 / 8 / 49 / 211
   screenshots for keypoints 1–5 in run 1 and 6 for the run-2 re-run. They stay
   in the ignored tree; only verdicts, confidences, and cited paths are
   durable.

## GAME-311 acceptance state

- Pinned inputs confirmed and recorded; the game worktree is clean at
  `47a0548`, the framework checkout is clean at `2604b6b`.
- The pinned framework's supported baseline was proven (smoke: 9 tests, 7
  entry points, exit 0) and its verification path was driven end to end.
- One campaign covers all five bounded keypoints, with per-keypoint verdicts,
  confidence values, and screenshot/DOM evidence.
- The four personas were applied as review lenses; four findings are
  normalized into the existing `schemas/finding.schema.json` contract with
  concrete artifact references.
- The one FAIL is explained, corrected at the lab's keypoint text, and re-run
  to PASS on identical pins; no game defect is claimed from it.
- No game repository change, no custom OpenCode backend, no unrelated
  benchmark suite, no telemetry, and no production or deployment change.

The comparison conclusion GAME-308 ultimately needs is still a judgement to be
made against the GAME-310 GameWorld report; this document supplies the
GameGen-Verifier half of that comparison and the framework defects an adopting
team would have to live with or fix.
