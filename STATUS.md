# Repository status — game-ai-playtest-lab

**Source snapshot:** live `main` at `af39d7fb4e4e61780e57b5bd09afd9c1f542d3d2`, checked 2026-10-17 (America/Los_Angeles).

## Scope and state

This is the bounded GAME-308 evaluation lab for one frozen Number Line Jumper revision (`47a05480d7c32cee8f0991d6f6c0410be90d678e`). Its purpose is to assess GameWorld and GameGen-Verifier evidence; it is not a general game-testing platform or a production release gate. `DONE.md` records the bounded evaluations as complete and places the repository in maintenance.

The one-game scope, no-production-telemetry boundary, and maintenance limits are documented in `README.md` and `DONE.md`. Any additional game or framework evaluation needs separately defined scope and evidence.

## Verification and merge gate

Refreshed 2026-11-03 against live GitHub protection and the current Jenkins catalog. This LOW-risk repository uses `.github/workflows/ci.yml` for same-repository, non-draft pull requests. Documentation-only changes receive a successful job while checkout, build, and test steps skip; fork pull requests fail before checkout.

Live `main` protection currently requires no status check, so the new Actions `test` result is supplemental. The live Jenkins profile `game-ai-playtest-lab-python312` remains `qualified` with evidence `docs/jenkins-phase-ten-game-ai-playtest-lab-cutover-2026-10-05.md`; that profile evidence does not make Jenkins the PR gate. Jenkins E2E is separate and owner-triggered when an approved current route exists. `.github/workflows/jenkins-fallback.yml` remains an owner-controlled manual exact-SHA Actions fallback. No Jenkins job was dispatched for this status update.

The 2026-10-17 source snapshot above predates the current PR policy and is historical; live protection and the live catalog control each PR review.
