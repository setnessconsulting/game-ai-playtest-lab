# Repository status — game-ai-playtest-lab

**Source snapshot:** live `main` at `af39d7fb4e4e61780e57b5bd09afd9c1f542d3d2`, checked 2026-10-17 (America/Los_Angeles).

## Scope and state

This is the bounded GAME-308 evaluation lab for one frozen Number Line Jumper revision (`47a05480d7c32cee8f0991d6f6c0410be90d678e`). Its purpose is to assess GameWorld and GameGen-Verifier evidence; it is not a general game-testing platform or a production release gate. `DONE.md` records the bounded evaluations as complete and places the repository in maintenance.

The one-game scope, no-production-telemetry boundary, and maintenance limits are documented in `README.md` and `DONE.md`. Any additional game or framework evaluation needs separately defined scope and evidence.

## Verification and merge gate

`.github/workflows/ci.yml` declares Python package installation and unit tests; the repository contract also names `python -m playtest_lab validate`, `smoke`, and `check-game`. These commands were not run for this status refresh, so no test result is claimed.

Live `main` protection requires `jenkins-pr-gate`. The live catalog lists this repository as qualified in `project-jenkins-config` main `170bcaafd620c1f12031e6e4ce06432b772a519c`; `project-jenkins` main read for this snapshot is `a447971ad8fdcfdc40ea20881a8af3c827e81d47`. A PR still needs a successful check from App `5043075` on its exact current head.
