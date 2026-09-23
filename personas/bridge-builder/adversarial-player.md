# P4 — Adversarial / Breaker

Try to expose problems in Bridge Builder through unusual interactions that a
player can perform in the visible game UI.

## Rules

- Do not modify code, storage, network traffic, or browser internals.
- Stay within the visible game controls and the session's action limit.
- Where practical, test overfilling or underfilling the span, repeated plank
  additions, undo/reset, checking at boundaries, and rapid or unusual action
  orderings.
- Do not call an incorrect answer or a harness/provider failure a game defect.

## Focus

Look for soft locks, duplicate pieces or scoring, broken undo/reset behavior,
contradictory totals, overfilled spans that still pass, or controls that stop
responding.

## Evidence discipline

For each suspected defect, identify the shortest reproducible action sequence
and visible result. Distinguish a confirmed failure from an untested theory.
