# game-ai-playtest-lab

A deliberately small evaluation lab for **GAME-308**. Its purpose is to determine whether GameWorld, GameGen-Verifier, or a narrowly defined combination of their proven capabilities produces enough evidence-backed value to improve Setness games.

The MVP tests **one game only: Number Line Jumper**. It is not a general AI game-testing platform.

## Locked scope

- Game: `setnessconsulting/game-number-line-jumper`
- Frozen game revision: `47a05480d7c32cee8f0991d6f6c0410be90d678e`
- Frameworks: GameWorld and GameGen-Verifier only
- Primary lab runner/reviewer: Codex using the owner's authenticated Luna Max configuration
- Alternate runner/reviewer: OpenCode with a model selected at runtime
- Personas: First-Time, Normal, Expert/Optimizer, Adversarial/Breaker
- Production boundary: no AI runtime or remote gameplay telemetry is added to Number Line Jumper

See [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md) for the authoritative frozen experiment inputs.

## Repository layout

```text
config/                    frozen experiment configuration
personas/                  four canonical persona prompts
frameworks/                pinned upstream setup/integration notes
playtest_lab/               tiny standard-library validation/planning CLI
reports/examples/          contract-only sample finding
reports/templates/         reusable durable report template
schemas/                   normalized finding schema
tests/                     local contract tests
runs/                      raw/generated runs (gitignored)
```

## Why the lab is separate

Number Line Jumper's production architecture remains governed by GAME-3. The game intentionally does not ship remote gameplay telemetry. All AI-playtest orchestration, prompts, framework adapters, screenshots, replays, logs, and normalized reports belong here instead of in the learner bundle.

## Local lab contract checks

The lab utility has no third-party Python dependencies and requires Python 3.11+.

```bash
python -m unittest discover -s tests -v
python -m playtest_lab validate
python -m playtest_lab smoke
```

`smoke` validates the frozen contract and reports whether `codex` and `opencode` are present on the local `PATH`. A missing CLI is reported but is not a contract failure unless explicitly required:

```bash
python -m playtest_lab smoke --require-runner codex
python -m playtest_lab smoke --require-runner opencode
```

After launching Number Line Jumper locally, verify the real browser target rather than relying on configuration alone:

```bash
python -m playtest_lab check-game
```

The GAME-309 local acceptance gate can be run as one command once Codex and the frozen game are available:

```bash
python -m playtest_lab smoke --require-runner codex --check-game
```

## Create a normalized run plan

The planner does **not** invoke a framework or model. It produces a deterministic run envelope that records the frozen game/framework revisions and chosen persona/runner.

```bash
python -m playtest_lab plan \
  --framework gameworld \
  --persona first-time
```

OpenCode model selection is runtime-only:

```bash
python -m playtest_lab plan \
  --framework gamegen-verifier \
  --persona adversarial \
  --runner opencode \
  --model provider/model-id
```

Persist a plan under the gitignored run tree when executing an experiment:

```bash
python -m playtest_lab plan \
  --framework gameworld \
  --persona normal \
  --output runs/gameworld/normal/plan.json
```

## Validate a normalized finding

```bash
python -m playtest_lab validate-finding reports/examples/sample-finding.json
```

The sample is explicitly synthetic. It proves the reporting contract and must never be counted as a real Number Line Jumper finding.

## Launch the frozen Number Line Jumper build

Number Line Jumper requires Node.js 24.x.

```bash
git clone https://github.com/setnessconsulting/game-number-line-jumper.git
cd game-number-line-jumper
git checkout 47a05480d7c32cee8f0991d6f6c0410be90d678e
npm ci
npm run dev -- --host 127.0.0.1
```

Default lab target: `http://127.0.0.1:5173/`.

Use a different URL only when the individual run records the override.

## Framework baselines

Before diagnosing a Number Line Jumper integration failure, prove the pinned upstream framework works in its own baseline flow.

- [`frameworks/gameworld/README.md`](frameworks/gameworld/README.md)
- [`frameworks/gamegen-verifier/README.md`](frameworks/gamegen-verifier/README.md)

GAME-310 owns the real GameWorld integration and four persona runs. GAME-311 owns the GameGen-Verifier integration and five locked behavioral keypoints. This repository foundation intentionally stops before those full evaluations.

## Evidence rules

A retained finding must include:

- concrete observed behavior;
- framework and persona;
- artifact/evidence reference;
- severity and confidence;
- a specific recommended improvement;
- expected benefit;
- a reproducible verification approach;
- exact game revision and run identity.

Generic advice that is not grounded in an actual run does not count.

## Artifact policy

Commit durable source/configuration, normalized reports, and small uniquely useful evidence. Keep bulk videos, screenshots, browser traces, raw logs, framework workspaces, and generated run directories local under gitignored paths.

Never commit API keys, authentication files, or provider credentials.

## Non-goals for this MVP

This repo does not add:

- a third framework or second game;
- automated Jira creation;
- autonomous game code changes;
- CI/nightly playtesting;
- a dashboard or hosted service;
- model-quality benchmarking;
- model training/fine-tuning;
- production telemetry or AI code in Number Line Jumper.
