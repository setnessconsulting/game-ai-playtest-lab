# GAME-312 — AI playtest framework comparison

**Date:** 2026-10-16

**Game:** Number Line Jumper, frozen revision `47a05480d7c32cee8f0991d6f6c0410be90d678e`

**GameWorld:** `3c26bdab436800fd61ef40543b64ca40d12c7e4a`

**GameGen-Verifier:** `2604b6b7330ca93c2e9fcb1036daf8cdf660aade`

## Executive conclusion

**Selected outcome: A — GameWorld.** Retain the small lab-local GameWorld path as the preferred basis for future, separately scoped exploratory playtests. Do not adopt GameGen-Verifier for ongoing use and do not maintain a hybrid.

GameWorld produced one concrete, high-confidence game improvement: for target 173, the coaching hint did not name the useful comparison values. That finding became [GAME-355](https://setnessconsulting.atlassian.net/browse/GAME-355), which is Done. At the comparison's game-main readback, `23561cd229291b4baaf28c99511c41cb9413cc29` contained the nearby anchors and regression cases for 173, 514, and 500. Main has since advanced to `ae72d446c1d8aa4e9d8c974b0e42c499cabcc5ed` through [documentation-only PR #46](https://github.com/setnessconsulting/game-number-line-jumper/pull/46), which changed only `docs/games/number-line-jumper/STATUS.md`; the game implementation did not change. This comparison inspected the implementation and cases but did not rerun tests. The finding has a concrete implementation and regression coverage; its original evidence remains one low-severity observation on the frozen build.

GameGen-Verifier produced a stronger structured verification trace across five UI keypoints, but no confirmed game defect. Its four retained findings describe reliability and integration problems in the framework. The broken validator call, worker timeouts, and missing state-injection assumption would add upkeep without a demonstrated additional game improvement. The evaluation does not justify carrying that integration forward.

This is a bounded research recommendation from one game. It is not a claim that GameWorld is proven for every Setness game, a production dependency, or a release gate. Any next game evaluation or productionization needs its own scope and evidence.

## Experiment summary

Both framework reports use the same frozen game SHA and their pinned upstream revisions. The game repository was not changed by either campaign, and no telemetry or production integration was added.

| Path | Observed result |
| --- | --- |
| GameWorld | Four Codex persona runs captured real action ledgers and screenshots. The primary OpenCode/DeepSeek campaign made 88 valid calls; one persona completed the visible flow, while the other outcomes remained incomplete or limited. One high-confidence, low-severity game finding was retained: `GW-001`. No exact provider cost was recorded. |
| GameGen-Verifier | The pinned baseline smoke passed 9 framework tests and loaded 7 entry points. One five-keypoint campaign returned 4 PASS / 1 FAIL; review traced the FAIL to the lab's own instruction, and the corrected keypoint passed on the same pins. The four persona viewpoints were reviews of the evidence, not 20 separate campaigns. Four framework findings were retained; no game defect was confirmed. |

The GameGen-Verifier runs took 58 minutes 34 seconds for five keypoints and 28 minutes 9 seconds for the one-keypoint rerun. Each included 24–27 minutes waiting after the worker had already written its result. Token and dollar totals are incomplete; no aggregate cost is inferred.

## Comparable finding ledger

| ID | Source | Severity | Disposition |
| --- | --- | ---: | --- |
| `GW-001` | GameWorld, adversarial persona; screenshot `gw-adversarial-20260921-final/screenshots/04-duplicate_land.png` | Low | Concrete target anchors were missing from the hint for 173. GAME-355 closed the issue after the code and regression cases were added. No duplicate follow-up is needed. |
| `GGV-001` | GameGen-Verifier, first-time lens | Medium | An instruction-induced missing control was reported as a game FAIL without an ambiguity signal. The lab corrected its keypoint wording and reran it; this is a verifier reliability limitation. |
| `GGV-002` | GameGen-Verifier, expert lens | Medium | The pinned harness passes arguments its artifact validator does not accept. Both run artifacts passed when manually checked with the validator's actual CLI. |
| `GGV-003` | GameGen-Verifier, normal-player lens | Low | Completed workers did not exit, causing long idle timeouts and a worker-failure signal despite written results. |
| `GGV-004` | GameGen-Verifier, adversarial lens | Low | Framework guidance assumes state injection; this frozen game exposes only its normal UI. The campaign worked through the UI, with near-boundary coverage limited. |

The first four GGV findings concern the framework or its integration, not Number Line Jumper. They are kept in the research report and do not justify a framework fork within this experiment.

## Fixed-weight rubric

Scores use a 1–5 judgment scale: 1 means little demonstrated value or high friction, 3 means useful with material limits, and 5 means strong, repeatable value with low friction. The Epic fixes the weights but defines no numeric adoption threshold; these scores organize the evidence and are not statistical measurements.

| Criterion | Weight | GameWorld | GameGen-Verifier |
| --- | ---: | --- | --- |
| Useful game-improvement discoveries | 35% | **3/5** — one actionable, high-confidence low-severity finding; it led to GAME-355, but the sample was one observation. | **1/5** — no game defect was confirmed; its four useful findings concern the verifier. |
| Ability to evaluate/play Number Line Jumper | 25% | **3/5** — the Codex runs drove the visible game and recorded progression; the alternate OpenCode campaign had incomplete outcomes. | **4/5** — five bounded UI keypoints produced evidence; the instruction-induced false failure was isolated and corrected. |
| Evidence quality and traceability | 20% | **4/5** — frozen identities, action ledgers, screenshots, and a directly cited game finding. | **4/5** — keypoint results, screenshots, DOM/ARIA observations, and normalized findings; the harness's final validator invocation required manual correction. |
| Integration and ongoing maintenance | 10% | **3/5** — a small lab-local adapter uses GameWorld's pinned interfaces without a fork; Windows required system Chrome after the pinned Chromium launch failed. | **2/5** — a Windows lifecycle shim, seeded keypoints, manual validator call, and known upstream liveness/integration defects remain. |
| Runtime/model cost and operational effort | 10% | **2/5** — 88 OpenCode calls and incomplete outcomes; exact cost was not recorded. | **2/5** — long wall time was dominated by post-verdict timeouts; only partial token usage was available. |
| **Weighted result** | **100%** | **3.10/5 (62%)** | **2.55/5 (51%)** |

The weighted result favors GameWorld because it found a real game improvement. The decision also considers that GameGen-Verifier's stronger keypoint trace did not add a game finding and carried documented reliability work. The scores do not compare model quality.

## Codex and OpenCode feasibility

- The GameWorld report records four Codex persona runs and Codex evidence review. The separate OpenCode/DeepSeek campaign exercised the alternate adapter successfully at the transport/action level, but most gameplay outcomes were incomplete. This supports alternate-path feasibility only; it is not a model-quality comparison.
- The GameGen-Verifier campaign used the Codex CLI as its primary backend with no model override and completed the bounded verification path. The saved records do not identify a model version, so this report makes no claim about model-specific performance.
- The comparison consumes the recorded runs and findings; it launches no new model campaign and ranks no models.

## Decision boundaries and follow-on work

Carry forward only the minimal GameWorld adapter and the shared frozen-input/evidence contract for a future, explicitly scoped exploratory evaluation. Keep the existing reports as research records. Do not add a dashboard, hosted service, CI schedule, second framework, production telemetry, or automatic Jira creation.

No new Jira issue is proposed from this comparison. The only retained game finding is already addressed by GAME-355, and the verifier findings do not justify adopting or forking GameGen-Verifier. A later evaluation may choose to stop if a new game produces only generic, unsupported, or low-value output.
