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

## Lab boundary

GAME-310 should add only the smallest GameWorld-specific configuration or adapter needed to exercise the frozen Number Line Jumper build. Do not fork GameWorld or add GameWorld runtime code to the shipping game merely to force Codex or OpenCode into the framework's native agent path.

Codex/Luna Max is the primary lab controller/reviewer. GameWorld may use one of its own supported gameplay-agent/provider paths for actual gameplay. The durable comparison is based on normalized evidence, not provider parity.

## Expected raw evidence

GameWorld upstream stores run metadata and interactions under `results/`. Bulk run artifacts stay local/gitignored; durable normalized reports belong under this repository's `reports/` tree.
