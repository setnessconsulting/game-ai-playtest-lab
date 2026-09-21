# GAME-308 experiment contract

This document freezes the common inputs for the AI Playtest Lab MVP. Changing any pinned revision after one framework has been evaluated invalidates direct comparison until both framework paths have been rerun against the same inputs.

## Frozen game

| Field | Value |
| --- | --- |
| Game | Number Line Jumper |
| Repository | `setnessconsulting/game-number-line-jumper` |
| Revision | `47a05480d7c32cee8f0991d6f6c0410be90d678e` |
| Frozen date | 2026-09-20 |
| Node runtime | `24.x` |
| Install | `npm ci` |
| Local dev | `npm run dev -- --host 127.0.0.1` |
| Default lab URL | `http://127.0.0.1:5173/` |

The pinned game README states that the production learner build has no remote gameplay telemetry. This lab does not change that boundary.

### Clean launch procedure

```bash
git clone https://github.com/setnessconsulting/game-number-line-jumper.git
cd game-number-line-jumper
git checkout 47a05480d7c32cee8f0991d6f6c0410be90d678e
npm ci
npm run dev -- --host 127.0.0.1
```

The lab assumes the game is reachable at `http://127.0.0.1:5173/` unless a run explicitly records another URL.

## Pinned frameworks

| Framework | Repository | Revision | Evaluation role |
| --- | --- | --- | --- |
| GameWorld | `gameworld-project/GameWorld` | `3c26bdab436800fd61ef40543b64ca40d12c7e4a` | exploratory gameplay and replay evidence |
| GameGen-Verifier | `NetX-lab/GameGen-Verifier` | `2604b6b7330ca93c2e9fcb1036daf8cdf660aade` | bounded state-grounded verification |

## Standard personas

The canonical prompts are:

- `personas/first-time-player.md`
- `personas/normal-player.md`
- `personas/expert-player.md`
- `personas/adversarial-player.md`

Framework wrappers may add operational instructions, but they may not change the persona intent to favor a framework.

## Runner policy

- `codex` is the default lab runner/reviewer. The repository intentionally does not hard-code a Codex model identifier; use the owner's authenticated Luna Max configuration.
- `opencode` is the alternate runner/reviewer. Supply an available model identifier at runtime when needed. The repository does not require a specific Muse Spark or DeepSeek identifier because provider/model IDs can change.
- The MVP does not benchmark model quality.

## Evidence policy

Retained findings must be grounded in a specific run artifact and conform to `schemas/finding.schema.json`. Generic advice without observed evidence is excluded.

Large raw videos/screenshots/traces remain under gitignored run directories. Durable Markdown/JSON summaries and small uniquely useful evidence may be committed.
