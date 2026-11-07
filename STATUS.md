# Repository status — game-ai-playtest-lab

**Source snapshot:** live `main` at `8b50f8c2645b9016dde2239d372f1f82bee44fbc`, checked 2026-11-06 (America/Los_Angeles).

**Assessment standard:** Portfolio Completion Standard v1. The owner decided on 2026-11-06 to retain the completed pre-cutoff milestone under its existing v1 contract. Project Meta `main` (`74c969d4687dd7f63350207d0047ae84bf0c8b58`) records this repository as `defined`, `portfolio-v1`, and `secondary`; it does not record a finalized delivery state or finalization entry.

## Scope and outcome

This repository began as the GAME-308 evaluation MVP. The bounded work was completed through GAME-309 (lab and common contract), GAME-310 (GameWorld), GAME-311 (GameGen-Verifier), and GAME-312 (comparison and recommendation). Live Jira readback on 2026-11-06 showed all four issues Done. GAME-355, the one retained Number Line Jumper finding from the GameWorld evaluation, is also Done.

The experiment remains limited to Number Line Jumper revision `47a05480d7c32cee8f0991d6f6c0410be90d678e`, GameWorld, and GameGen-Verifier. The comparison selected GameWorld only as a research path for a separately scoped future evaluation. It does not establish broad cross-game effectiveness or add a production dependency, release gate, schedule, telemetry, second game, dashboard, or autonomous Jira creation.

The repository's post-completion mode is maintenance. This research completion does not mean the portfolio's nine-gate finalization has been approved.

## Verification

The documented locked setup completed with `uv` 0.13.5. The default `uv` on this host is 0.11.17 and refused the project's required version; the matching 0.13.5 executable was used for the successful setup and checks below.

- `uv run --locked --extra test --group build --no-sync python -m unittest discover -s tests -p "test_*.py" -v` — **PASS**, 36 tests.
- `uv run --locked --extra test --group build --no-sync python -m playtest_lab validate` — **PASS**, contract and sample finding valid.
- `uv run --locked --extra test --group build --no-sync python -m playtest_lab smoke` — **PASS**, contract and sample finding valid; Codex and OpenCode CLIs found.
- `uv run --locked --extra test --group build --no-sync python -m playtest_lab check-game` — **NOT RUN**; the frozen game was not launched at the documented local URL.

The check-game run remains conditional on launching the frozen Number Line Jumper revision as documented in `docs/EXPERIMENT.md`. No experiment campaign was rerun for this closeout.

## Portfolio completion gates

Assessment against the source snapshot above, with this closeout documentation correction applied:

| Gate | Result | Evidence and remaining gap |
| --- | --- | --- |
| 1. Jobs to be done | Pass | `DONE.md` names the operator jobs; GAME-310/311/312 completed the bounded evaluation and comparison. |
| 2. Required functionality | Pass | The lab provides the pinned experiment contract, persona prompts, adapters, planning/validation CLI, finding schema, and research reports. |
| 3. Critical behavior | Pass | The documented unit suite passed all 36 tests, including pinned-input validation, finding checks, URL validation, and adapter safety cases. |
| 4. Reproducible build and verification | Pass | The README and CI workflow document the locked environment, pinned GameWorld checkout, and repeatable test commands. |
| 5. Operational truth | Pass | This status replaces the 2026-10-17 snapshot, distinguishes the GAME-308 umbrella from its completed GAME-310/311 evaluations and GAME-312 comparison, and matches the maintenance decision in `DONE.md`. |
| 6. Failure and recovery | Pass | The docs pin external revisions, require proving each framework's own baseline before diagnosing integration failures, and define which generated artifacts stay local. |
| 7. Completion-blocking defects | Pass | The retained GAME-355 finding is Done; GameGen-Verifier reliability limits are documented and excluded by the comparison decision; no lab-labeled Jira issue remains open. Under the selected v1 contract, the later v1.1 AI-Slop scan rule is not a separate requirement. |
| 8. Stability has evidence | Pass | The v1 contract defines stability for this research lab as completing both bounded evaluations and their comparison. GAME-310/311/312 are Done; `reports/recommendation.md` records the real GameWorld and GameGen-Verifier campaigns and their limitations. This is campaign evidence, not a claim of broad cross-game or production reliability. |
| 9. Post-completion mode | Pass | `DONE.md` sets maintenance as the post-completion mode and rules out an open-ended platform expansion. |

**Gate result:** 9 of 9 gates pass under the selected v1 contract. This evidence assessment does not itself declare the repository finalized; no finalization date or Project Meta metadata change is recorded.

### Gate 8 standard decision

On 2026-11-06, the owner chose to retain this completed October milestone under its existing v1 contract. The v1.1 tiered exact-SHA baseline clause is not being introduced by reopening this milestone. The frozen Number Line Jumper SHA `47a05480d7c32cee8f0991d6f6c0410be90d678e` remains the experiment's **game input**, not a lab-repository baseline. No new lab baseline, tier, or scenario inventory is asserted. No baseline run or new playtest campaign was started for this closeout.

## CI and merge authority

Refreshed 2026-11-06 against live GitHub and the live Jenkins catalog:

- Repository risk tier is LOW. `.github/workflows/ci.yml` is the routine same-repository PR lane; documentation-only changes skip checkout, build, and test steps.
- Live `main` branch protection has no required status checks, and the repository has no applicable rulesets. GitHub Actions and Jenkins are therefore not required merge checks at this snapshot.
- The live Jenkins profile `game-ai-playtest-lab-python312` is `qualified` with evidence `docs/jenkins-phase-ten-game-ai-playtest-lab-cutover-2026-10-05.md`. Qualification is supplemental because protection does not require `jenkins-pr-gate`.
- The owner-controlled exact-SHA Actions fallback remains `.github/workflows/jenkins-fallback.yml`. No Jenkins or Actions workflow was manually dispatched for this closeout.
- Jenkins source revisions read for this task: `setnessconsulting/project-jenkins` `main` at `0d4dc634685c3d31e67428130c0d07327065de8c`; `setnessconsulting/project-jenkins-config` `main` at `503e1d1d0466e1df6527362f2698d57169770bfa`.
