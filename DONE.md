# Completion Contract — game-ai-playtest-lab

**Standard:** Portfolio Completion Standard v1
**Date:** 2026-09-27

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

Foundation complete; full evaluations are GAME-310/311 scope.

## Acceptable limitations

No third framework, no second game, no automated Jira creation, no CI/nightly
playtesting, no dashboard, no model benchmarking, no production telemetry.

## Post-completion operating mode

Maintenance. The lab foundation is delivered; future evaluations use the
same harness.
