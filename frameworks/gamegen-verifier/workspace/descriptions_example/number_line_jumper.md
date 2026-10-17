# Number Line Jumper (frozen GAME-308 build)

| Field | Value |
| --- | --- |
| **Title** | Number Line Jumper |
| **Genre Family** | Casual |
| **Repository** | `setnessconsulting/game-number-line-jumper` |
| **Frozen revision** | `47a05480d7c32cee8f0991d6f6c0410be90d678e` |
| **Runtime** | Node.js 24.x, Vite 8, React 19 |
| **Entry** | `npm run dev -- --host 127.0.0.1 --port <port> --strictPort` |

This file exists because GameGen-Verifier's harness requires a description at
`descriptions_example/<game_name>.md`. It describes the **already-frozen**
browser build; it is not a generation prompt and it must not be used to
regenerate or redesign the game.

## Summary

A number-sense estimation game. A target number and a labelled number line are
shown; the learner places a marker on the line and submits it. The game reveals
the true position and reports distance/direction feedback. Scored play runs a
bounded round (60 seconds or 10 tries, whichever comes first); explore mode is
untimed and unscored.

## Modes and levels

- Level selection: `Grades 1–2` (whole numbers on 0–10, 0–20, 0–100),
  `Grades 3–4` (fractions and wholes on 0–1 and 0–2), `Grades 5–6` (decimals and
  fractions on 0–1 and 0–10), `Grades 7–8` (negatives, larger ranges, mixed forms).
- Mode selection: `Guided warm-up` (practice, no score/timer) or `Challenge`
  (scored round immediately), with `Explore an untimed line` as a separate
  unscored surface.
- The guided warm-up shows a practice target and a sample line, with
  `Reveal example` and `Start guided round`.

## Session facts

- Session-only play. No accounts, trackers, or gameplay network requests.
- Scored round: target, trial counter (`Trial N of 10`), score, and remaining
  seconds are visible; `Land here` submits the current placement.
- Feedback after a placement: the estimate, the target, a percentage/units
  error, points awarded for that placement, and a short coaching hint.
- Round summary: points, trials, close landings, average error, visit/session
  bests, and `Play again` / `Change level` / `All games` actions.
