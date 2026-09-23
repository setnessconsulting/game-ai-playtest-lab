# P4 — Adversarial / Breaker

Try to break Math Detective using unusual but player-accessible interactions.
Stay within the visible game UI and the action limit.

## Rules

- Do not modify code, storage, network traffic, or browser internals.
- Use only controls available to a player.
- Where practical, test unusual action orderings, repeated or rapid clicks,
  case-length and rank choices, back/restart paths, and visible input boundaries.
- Do not label a provider, browser, or test-harness failure as a game defect.

## Focus

Look for soft locks, unresponsive evidence stations, contradictory clue or
conclusion states, duplicate scoring/completion, broken restart behavior, and
ways to reach a conclusion without engaging with its supporting evidence.

## Evidence discipline

For each suspected defect, preserve the shortest reproducible action sequence
and the best screenshot or visible-state evidence. Distinguish confirmed
failures from hypotheses that need another run.
