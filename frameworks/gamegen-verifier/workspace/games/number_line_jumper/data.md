# Frozen Number Line Jumper — observable data schema (read-only)

This file is lab-local adapter documentation for GameGen-Verifier's
`generative-state-construction` and `short-interaction-verification` skills.
It describes what the **frozen** build
(`setnessconsulting/game-number-line-jumper@47a05480d7c32cee8f0991d6f6c0410be90d678e`)
actually exposes to a browser automation worker.

## Ground rule

The frozen learner build ships **no test hook**. It does not define
`window.gameReady`, `window.injectGameState(...)`, `window.getGameState()`, or
any equivalent. Do not wait for or call them; do not fake them. See
`state_injection_api.md` for the supported substitute.

## Observable state surfaces

All values below are readable from the live DOM. There is no runtime state
object, so the DOM/ARIA text *is* the state.

| Surface | How to read it | Notes |
| --- | --- | --- |
| Placement value | `[role=slider]` → `aria-valuenow` (0–100) and `aria-valuetext` (e.g. `8.09 on a line from 0 to 10`) | `aria-valuenow` is the marker position as a percentage of the track; `aria-valuetext` is the represented mathematical value and is the value to record |
| Marker position | `.nl-marker` inline style `transform: translateX(<pct>%)` | Visual confirmation that a pointer placement landed |
| Current target | heading text `Land on <value>` inside the game region | Warm-up uses `Practice target <value>` |
| Trial counter | text `Trial <n> of 10` | Scored round only |
| Score | the score value shown next to `Number Line Jumper · Score` | Scored round only |
| Clock | `<n>s left` next to `role="timer"` | Scored round only |
| Feedback panel | rendered after `Land here` for the timed dwell: `Your estimate`, `Target`, `Off by <pct>% · +<points> points`, `Spot on!`, `Try this next time:` | Screenshot it immediately after submitting; with `Wait for me after feedback` enabled it stays until the learner continues |
| Round summary | `ROUND COMPLETE`, `You scored <n> points.`, `Trials <n> of 10`, `Close landings`, `Avg. error` | Reached when the clock or the 10-try bound ends the round |

## Actions available through the normal UI

- Level selection buttons: `Grades 1–2`, `Grades 3–4`, `Grades 5–6`, `Grades 7–8`.
- Mode radios: `Guided warm-up` (default) and `Challenge`; `Explore an untimed line` is a separate button.
- Warm-up: `Reveal example`, `Start guided round`.
- Placement: pointer down/move/up on `[role=slider]`, or keyboard (`ArrowLeft`, `ArrowRight`, `Home`, `End`; `Shift` for larger steps).
- Submit: `Land here`.
- Help: `Show midpoint hint`.
- Exit: `Exit` (returns to level selection).
- Restart: `Play again` (same level, fresh round) and `Change level` on the round summary; `Back to levels` in the warm-up.

## Non-goals

This schema is documentation only. Nothing here adds telemetry, a test API, or
any runtime dependency to the learner bundle.
