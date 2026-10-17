# Frozen Number Line Jumper — state-injection status

**Status: no state injection API exists in the frozen build.**

The pinned learner build
(`47a05480d7c32cee8f0991d6f6c0410be90d678e`) was written for players, not for
verifiers. It exposes:

- no `window.gameReady` flag;
- no `window.injectGameState(state)`;
- no `window.getGameState()`;
- no query-string or storage-based scenario setup.

The GAME-308 boundary forbids adding instrumentation to the shipping bundle, so
this lab adapter does not add any. Verification must therefore use the surfaces
the game already exposes.

## Supported substitute for injection

1. **Establish the precondition through the real UI.** Cold-load the game URL,
   choose the level (`Grades 1–2` … `Grades 7–8`) and the mode
   (`Guided warm-up` / `Challenge`). Allow a few seconds for React to render and
   for the Vite dev server to serve the first module graph.
   One ordering trap: `Reveal example` and `Start guided round` are both on the
   warm-up surface, but starting the guided round removes the reveal control.
   A keypoint that needs the reveal must read it *before* starting a round; do
   not sequence the two actions and then look for the control that the first
   action removed (see `GGV-001` in `reports/findings/`).
2. **Place the answer with real input.** Use real pointer input
   (`page.mouse`) or keyboard input on `[role=slider]`; do not set the DOM
   attribute directly. `aria-valuetext` gives the represented value.
3. **Read state from the DOM.** See `data.md`. Because values come from visible
   text and ARIA attributes rather than a runtime object, record the exact
   strings in `test_result.json`.
4. **Capture before/after screenshots.** The normal-mode artifact contract is
   unchanged: `screenshots/before.png` immediately before the first action and
   `screenshots/after.png` after the interaction settles, plus
   `frame_*.png` sequence frames when `screenshot_mode=sequence`.
5. **Record the absence of injection truthfully.** In `result.json`, note in
   `reasoning`/`explanation` that the precondition was established through the
   normal UI because the build has no injection API. Do **not** write
   `INCOMPLETE` for that reason: `INCOMPLETE` is reserved for harness-level
   breakage (browser launch failure, server unreachable, worker timeout). If the
   UI cannot reach the scenario, that is a `FAIL` observation under the
   framework's normal-mode decision policy, reported as such.

## Why injection is not injected here

`generative-state-construction` prefers an injectable near-threshold prestate.
With no injection seam the smallest correct approach is to exercise the real
flow the player uses. Where a keypoint needs a specific phase (feedback frame,
round summary), reach it by real play and capture the frame while it is shown
(optional in-game `Wait for me after feedback (this session)` keeps the feedback
panel on screen).

## Known timing notes

- The reveal/feedback panel dwells for ~0.9–1.7 s before the next trial unless
  `Wait for me after feedback (this session)` is enabled.
- The scored round ends at 60 s or 10 trials, whichever comes first; the round
  summary then offers `Play again` and `Change level`.
- `Sound` is off by default; it is irrelevant to every keypoint here.
