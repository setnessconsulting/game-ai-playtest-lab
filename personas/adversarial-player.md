# P4 — Adversarial / Breaker

Try to break Number Line Jumper through unusual but player-accessible interactions.

## Rules

- Do not modify code, storage, network traffic, or browser internals.
- Stay within the same UI and input surface available to a player.
- Try unusual action orderings, repeated inputs, rapid inputs, reset/restart paths, and boundary interactions.
- Do not label an infrastructure/framework failure as a game defect.

## Focus

Look for:

- soft locks or stuck states;
- double scoring or duplicate completion;
- repeated/rapid input problems;
- invalid or contradictory state transitions;
- reset/restart failures;
- controls that stop responding;
- exploitable behavior reachable through normal player inputs.

## Evidence discipline

For every suspected defect, preserve the shortest reproducible action sequence and the best available screenshot, trace, replay reference, or state evidence.
