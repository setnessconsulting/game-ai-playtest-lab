# Completion Contract — game-ai-playtest-lab

**Standard:** Portfolio Completion Standard v1
**Date:** 2026-10-16

## Intended outcome

A deliberately small evaluation lab that determines whether GameWorld,
GameGen-Verifier, or a combination produces enough evidence-backed value to
improve Setness games. Tests one game (Number Line Jumper) at a frozen
revision.

## Jobs to be done

Run AI playtests via Codex or OpenCode using four personas; produce
normalized evidence-backed findings.

## Required functionality

Persona framework, playtest runner, validation and smoke commands, game
checker, report generation.

## Automated verification

```
python -m unittest discover -s tests -v
python -m playtest_lab validate
python -m playtest_lab smoke
python -m playtest_lab check-game
```

## External/runtime checks

None. Local-only Python CLI.

## Stability evidence

The foundation and bounded GAME-310/311 evaluations are complete. GAME-312 selects the minimal lab-local GameWorld path for separately scoped future evaluations. Its one low-severity game finding led to GAME-355 and is fixed on current Number Line Jumper main. GameGen-Verifier produced four framework findings and no confirmed game defect. This one-game experiment does not establish broad cross-game effectiveness.

## Acceptable limitations

No third framework, no second game, no automated Jira creation, no CI/nightly
playtesting, no dashboard, no model benchmarking, no production telemetry.

## Post-completion operating mode

Maintenance. Keep the reports and minimal GameWorld adapter as research
artifacts. Do not treat the lab as a production release gate or add scheduled
playtesting. A later game evaluation needs its own scope and evidence; stop if
its findings do not justify the upkeep.
