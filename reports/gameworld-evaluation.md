# GAME-310 — GameWorld evaluation

Status: partial evidence captured; blocked on the pinned native provider path.

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

## Persona runs

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

## Controller and alternate-runtime evidence

The host is logged into the Codex CLI, and independent Codex screenshot reviews
completed for all four runs. The in-process runner's nested Codex invocation
held the browser process open on this Windows host, so the captured action
plans used the runner's bounded deterministic fallback sequences. That is an
integration limitation, not a claim of native GameWorld agent parity.

GameWorld's native provider clients were not run: the host had no supported
provider API key and no local vLLM-compatible endpoint. The available
OpenCode CLI reported version `1.18.31`, and its protected credential store
provided a working OpenCode Go credential without exposing the key. One
bounded alternate review completed successfully against the existing
adversarial screenshot using
`opencode-go/deepseek-v4-flash-vision-exp`.

OpenCode returned a concrete candidate finding from
`gw-adversarial-20260921-final/screenshots/04-duplicate_land.png`: the
feedback panel awarded `+2 points` and used encouraging copy for an estimate
that was `33% away (327 units)`. This was retained as alternate-review
evidence, not as a second normalized finding, because the GAME-310 ledger is
Codex-led and no four-persona OpenCode campaign was requested. The result
demonstrates the alternate review path; it does not make OpenCode a native
GameWorld provider.

At follow-up, the user-supplied alternate API key was loaded only in memory
and used against the OpenCode Go Responses endpoint with `gpt-5.6-luna` for
the same screenshot. The request returned HTTP `200` and valid JSON; that
review found no additional candidate finding from the single frame. This
confirms the supplied key is usable for the alternate review path without
changing the native GameWorld-provider blocker.

## GAME-310 acceptance state

The browser integration, upstream baseline, four persona captures, evidence
ledger, and normalized finding contract are complete. GAME-310 is not marked
Done because the acceptance criteria require the pinned GameWorld-supported
agent path, and that path is owner/provider-gated on this host.

Required next action: make one supported GameWorld provider available (a
credentialed provider account or a supported local model endpoint), then rerun
the four personas with the same frozen SHA and compare those native-agent
artifacts against this baseline. Do not advance GAME-311 until GAME-310 is
closed.
