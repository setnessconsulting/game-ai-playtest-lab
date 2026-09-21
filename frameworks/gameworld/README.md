# GameWorld evaluation notes

## Pinned upstream

- Repository: `gameworld-project/GameWorld`
- Revision: `3c26bdab436800fd61ef40543b64ca40d12c7e4a`
- Role in GAME-308: exploratory gameplay, behavioral discovery, and replay/run evidence.

## Upstream baseline

At the pinned revision, upstream documents:

```bash
conda create -n gameworld python=3.12
conda activate gameworld
pip install -r requirements.txt
playwright install chromium

git clone https://github.com/gameworld-project/GameWorld-Games.git games/gameworld-games
python play.py --game 10_doodle-jump
python main.py --config 10_doodle-jump+10_01+gpt-5.2 --headed
```

The baseline must be smoke-tested before attributing a failed Number Line Jumper integration to the game.

### Baseline evidence from this host

- `python play.py --game 10_doodle-jump --headless` reached GameWorld's
  browser-launch path but the pinned Playwright Chromium binary failed with
  Windows `BrowserType.launch: spawn UNKNOWN`.
- A direct pinned-GameWorld baseline using the installed system Chrome binary
  (`C:/Program Files/Google/Chrome/Application/chrome.exe`) succeeded at
  `http://127.0.0.1:8101/index.html`: title `Doodle Jump`, `GAMEAPI` present,
  and the page reported score `0`.
- This is a host/browser launch deviation, not a change to the upstream
  revision. The system-Chrome path is recorded in each local run manifest.

## Lab boundary

GAME-310 should add only the smallest GameWorld-specific configuration or adapter needed to exercise the frozen Number Line Jumper build. Do not fork GameWorld or add GameWorld runtime code to the shipping game merely to force Codex or OpenCode into the framework's native agent path.

Codex/Luna Max is the primary lab controller/reviewer. GameWorld may use one of its own supported gameplay-agent/provider paths for actual gameplay. The durable comparison is based on normalized evidence, not provider parity.

## Expected raw evidence

GameWorld upstream stores run metadata and interactions under `results/`. Bulk run artifacts stay local/gitignored; durable normalized reports belong under this repository's `reports/` tree.

## Lab-local Number Line Jumper runner

`number_line_jumper_runner.py` reuses GameWorld's pinned `BrowserGameManager`
and `ActionExecutor` against the frozen game URL. It keeps the integration in
this lab repository, captures an action ledger plus screenshots under the
ignored `runs/gameworld/<run-id>/` tree, and never changes the game checkout.

The intended controller/reviewer is the authenticated Codex CLI. On the
evaluation host, nested Codex invocation from inside the GameWorld process
held the browser run open, so the captured four-persona evidence used the
runner's bounded fallback plans and independent Codex CLI screenshot reviews.
This limitation is explicit in each manifest and does not count as proof that
GameWorld's native provider path is available.

The pinned native GameWorld provider path was not run: no supported provider
API key or local model endpoint was available on the host. OpenCode was
checked once against an existing screenshot, but its configured run produced
no response within the bounded feasibility check and was not used for a
campaign.
