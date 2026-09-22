# GAME-310 — GameWorld evaluation

Status: OpenCode gameplay evidence captured; acceptance remains blocked pending
the final determination that the lab-local provider adapter satisfies the
pinned GameWorld supported-agent-path gate.

## Frozen inputs

| Input | Revision / value |
| --- | --- |
| Game | Number Line Jumper |
| Game revision | `47a05480d7c32cee8f0991d6f6c0410be90d678e` |
| GameWorld revision | `3c26bdab436800fd61ef40543b64ca40d12c7e4a` |
| Game URL | `http://127.0.0.1:5173/` |
| Browser viewport | 1280×720 |
| Run seed | 42 |

The game ran from a clean detached worktree at the frozen SHA. Node.js was
`v24.15.0`; `npm ci` completed successfully; the local Vite server returned
HTTP 200. No game files, deployment state, or gameplay telemetry were changed.

## Upstream baseline

The pinned GameWorld repository and GameWorld-Games were cloned and installed
in the lab's ignored `.frameworks/` tree. The documented
`python play.py --game 10_doodle-jump --headless` path failed at the pinned
Playwright Chromium launch with Windows `BrowserType.launch: spawn UNKNOWN`.
That was isolated from the game: direct GameWorld `GameLauncher` plus the
installed system Chrome binary opened the same pinned Doodle Jump baseline at
`http://127.0.0.1:8101/index.html`, with title `Doodle Jump`, a `GAMEAPI`
object, and page score `0`.

The evaluation therefore records a system-Chrome browser deviation in the
local manifests; it does not patch or fork GameWorld.

## Baseline Codex persona runs

Each run used the same frozen URL, viewport, seed, and GameWorld action
executor. The raw action ledgers and screenshots remain under the ignored
`runs/gameworld/` tree.

| Persona | Run | Actions captured | Observed progression | Codex screenshot review |
| --- | --- | ---: | --- | --- |
| First-time | `gw-first-time-20260921-final` | 8/8 successful | Grades 1–2 → guided round → two landings; first feedback was Spot on at target 5; score reached 12 before exit | No retained finding |
| Normal | `gw-normal-20260921-final` | 11/11 successful | Grades 3–4 → guided round → three landings with continuation; first feedback showed target 1/8, estimate 0.5, score 2 | No retained finding |
| Expert | `gw-expert-20260921-final` | 11/11 successful | Grades 5–6 → guided round → three landings with continuation; first feedback showed target 0, estimate 5, score 2 | No retained finding |
| Adversarial | `gw-adversarial-20260921-final` | 7/7 successful | Grades 7–8 → rapid keys → repeated Land actions advanced through trials without a soft lock; exit returned to level selection | One low-severity coaching-copy finding, [`GW-001`](findings/gameworld-adversarial-001.json) |

Codex reviewed the first feedback frame for each persona. The first-time,
normal, and expert frames produced no concrete finding. The adversarial frame
retained only GW-001; the review explicitly rejected generic claims about
sound, timer, score, slider, and duplicate-action processing.

## OpenCode/DeepSeek primary persona runs

The user-directed provider campaign used the same frozen game, GameWorld
revision, 1280×720 viewport, seed 42, and pinned `ActionExecutor`. The
provider configuration was OpenCode Go Chat Completions with model
`deepseek-v4.1-flash`, `reasoning_effort=max`, `tool_choice=auto`, and an
8192-token request bound. The smoke run preceded the primary campaign.

| Persona | Run | Actions / valid calls | Visible result | Codex review |
| --- | --- | ---: | --- | --- |
| Smoke / first-time | `gw-opencode-first-time-smoke` | 8/8 | 8 semantic actions executed; scroll, clicks, and keyboard input reached the frozen surface | Transport and action-contract smoke passed |
| First-time | `gw-opencode-first-time-primary` | 20/20 | Remained in guided warm-up; target 20 and estimate near 10 remained visible; timed round was not started | Placement/control limitation; no retained game finding |
| Normal | `gw-opencode-normal-primary` | 20/20 | Reached Trial 1 of 10 with score 0 and 53 seconds remaining; did not advance a trial | Incomplete controller outcome; no retained game finding |
| Expert | `gw-opencode-expert-primary` | 20/20 | Reached round summary with score 10, one close landing, and 0.1% average error | Completed visible flow; no retained game finding |
| Adversarial | `gw-opencode-adversarial-primary` | 20/20 | Reached a zero-play round summary showing 0 of 10 trials and 0 points | Incomplete controller outcome; no retained game finding |

All five runs produced manifests, JSONL action ledgers, and screenshots under
the ignored `runs/gameworld/` tree. Every primary event had a valid semantic
function call and no provider error. The incomplete outcomes are recorded as
gameplay-agent limitations, not game defects. The existing normalized finding
`GW-001` remains the only retained finding; no new OpenCode screenshot was
strong enough to add another finding.

## Controller and alternate-runtime evidence

The original Codex-controlled four-persona baseline remains in the report for
comparison. Independent Codex screenshot reviews also covered the OpenCode
primary final frames. The reviews rejected claims about scoring, timing,
accessibility, or game defects when the screenshot only demonstrated an
incomplete controller outcome.

The OpenCode adapter uses the pinned GameWorld `GeneralAgent` semantic
contract but is intentionally lab-local; it does not register a new upstream
adapter in GameWorld's checkout. OpenCode Go returned valid Chat Completions
function calls for all 88 provider requests: 8 smoke steps plus 80 primary
steps. No request fell back to another provider. The manifests do not contain
the API key or hidden reasoning text.

The earlier pinned Gemini attempt remains a separate provider-gate result:
`gemini_general` with `gemini-3-flash-preview` returned HTTP 402
`RESOURCE_EXHAUSTED` because the account's prepayment credits were depleted.
The earlier one-shot OpenCode alternate review of the Codex adversarial frame
is also retained as historical evidence and is not mixed into the primary
campaign findings.

Operationally, the new campaign required 88 bounded model requests and all
five sessions completed without browser or provider failure. Exact monetary
usage was not available in the local response artifacts, so this report does
not invent a dollar estimate.

## GAME-310 acceptance state

The browser integration, upstream baseline, four Codex baseline captures, four
OpenCode/DeepSeek primary captures, evidence ledgers, and normalized finding
contract are complete. GAME-310 is not marked Done because the OpenCode path
is a lab-local adapter implementing the pinned contract rather than an
upstream GameWorld adapter loaded through the pinned catalog path. This status
preserves the distinction between successful lab evidence and the remaining
supported-agent-path gate.

Required next action: decide whether this explicitly documented lab-local
OpenCode adapter is acceptable for the GAME-310 supported-agent-path gate. If
not, provide an approved upstream-supported provider or local endpoint and
rerun the four personas with the same frozen SHA. Do not advance GAME-311
until GAME-310 is closed.
