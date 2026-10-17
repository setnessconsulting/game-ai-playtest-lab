<!--
Lab deviation (recorded in reports/gamegen-verifier-evaluation.md).

These are GAME-311's five locked behavioral keypoints. They are carried in the
pinned framework's keypoint format but they are deliberately only five, so this
file does not satisfy the framework's 30-40 keypoint distillation policy and is
not distilled or lint-gated. The lab adapter seeds
`runs/number_line_jumper/<run_id>/keypoints.snapshot.md` with this file and runs
the unmodified pinned harness with `--resume-run --min-keypoints 5`, which is
the framework's documented resume path for an already-frozen keypoint set.
-->

# Number Line Jumper — GAME-311 locked keypoints

## Keypoint 1: [Interaction Logic] A first-time player can begin from the visible surface alone

**Verification Focus:**
The evidence must distinguish "the framework could not reason about the UI" from "the game does not present a usable starting point". Report both the observed screen text and the interaction that followed.

**Precondition Game State Description:**
Cold load of the game URL with no prior interaction. The level-selection surface is visible: the "How do you want to play?" radios, the four grade-level buttons, the Explore button, and the two options checkboxes. No round is in progress.

**Instruction Description:**
Using only what is on screen, select the `Grades 1–2` level while leaving the default `Guided warm-up` mode selected, and read the resulting warm-up surface (the quick warm-up panel with its numbered tips, practice target and sample number line). Do not start the scored round yet. Place a sample estimate on the warm-up number line with real pointer input, then activate the warm-up reveal control and read the revealed response.

**Expected Result Description:**
The visible surface states the objective and presents a placeable number line without external instructions. The warm-up names the practice target and its range, the number line exposes an instruction that says where to place the sample estimate, and the reveal control produces a visible, explained response (the example target position and the percentage across the line). No dead end, no control that silently does nothing.

## Keypoint 2: [Interaction Logic] Pointer interaction places the estimate through the normal UI path

**Verification Focus:**
Placement must be produced by real pointer input on the number line control, not by writing the ARIA attribute or a DOM style directly. Record the before/after screenshots and the `aria-valuetext` readings.

**Precondition Game State Description:**
A scored round is running: `Grades 1–2` selected, `Challenge` mode selected, Trial 1 of 10 visible, and the number line slider present with the marker near the middle of the track.

**Instruction Description:**
With real pointer input, press on the slider track at roughly 20% of its width, release, and read the slider's `aria-valuetext`. Then press at roughly 80% of the track width, release, and read `aria-valuetext` again. Do not press `Land here` yet.

**Expected Result Description:**
Both placements move the visible marker and change the exposed represented value in the direction of the pointer position, staying inside the labelled range of the current line. No error state, no lost focus, and the value is consistent between the marker position and the exposed value text.

## Keypoint 3: [State Transition] Submitting an answer produces understandable visible feedback

**Verification Focus:**
Capture the feedback frame itself, not only the post-advance state. If the feedback panel is missed because of its dwell, say so in the reasoning and retry with `Wait for me after feedback (this session)` enabled.

**Precondition Game State Description:**
A scored round is running with a placement already made on the number line and the estimate value known from `aria-valuetext`.

**Instruction Description:**
Activate `Land here` and capture the visible result while the feedback panel is shown: the estimate, the target, the reported error, and the points awarded. Then confirm which trial is shown after the feedback.

**Expected Result Description:**
Feedback is visible and specific: it restates the placement, names the target, reports the distance or percentage error, and reports points for that placement. The trial counter or round summary advances only after the feedback. Submission never appears to do nothing and never awards feedback for a different placement than the one shown before submission.

## Keypoint 4: [Game Rule] Successful placements advance score and progress without a stuck state

**Verification Focus:**
This is a bounded progress check, not engine-correctness testing. Compare the score, trial counter, and clock across three submissions and report any contradiction between the visible values.

**Precondition Game State Description:**
A scored round is running: Trial 1 of 10, score 0, a positive number of seconds remaining, and the number line slider present.

**Instruction Description:**
Make three placements and press `Land here` after each. For each submission record the score shown, the trial counter, and the remaining seconds before and after. Allow the feedback dwell or press the continue control if `Wait for me after feedback (this session)` is enabled.

**Expected Result Description:**
The trial counter advances after every submission and the score is monotonic non-decreasing across the round. The clock keeps decreasing during play and the round ends only through the round summary. No trial regression, no repeated counting of a single placement, and no state where the round cannot be continued.

## Keypoint 5: [Boundary Condition] Restart and reload restore a valid playable state

**Verification Focus:**
Use the game's real surfaces (`Play again`, `Change level`, `Exit`, browser reload). Do not add or fabricate a reset control. Report any transient state that survives a restart.

**Precondition Game State Description:**
A scored round has ended and the round summary is visible with its points, trials, and average error, and the `Play again` / `Change level` / `All games` actions present.

**Instruction Description:**
Activate `Play again` and read the state of the new round (score, trial counter, target, presence of any leftover feedback or summary text). Then reload the page and read the resulting surface.

**Expected Result Description:**
`Play again` produces a fresh playable round with the score and trial counter reset and no leftover round-summary or feedback panel for the previous round. A page reload returns to a valid cold-start level-selection surface that can start a new round. No permanently stuck or unplayable state appears in either path.
