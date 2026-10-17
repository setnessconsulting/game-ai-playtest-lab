// Lab-local shim: serve the frozen Number Line Jumper checkout with its own
// documented dev command. This file contains no game code and does not modify
// the game repository. `prepare_workspace.py` writes `frozen-root.json` next to
// this file with the absolute path of the frozen worktree.
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));

function resolveFrozenRoot() {
  const fromEnv = process.env.NLJ_FROZEN_ROOT;
  if (fromEnv && fromEnv.trim()) return fromEnv.trim();
  const configPath = join(here, "frozen-root.json");
  const config = JSON.parse(readFileSync(configPath, "utf8"));
  if (!config.frozen_root) throw new Error(`${configPath} is missing frozen_root`);
  return String(config.frozen_root);
}

const frozenRoot = resolveFrozenRoot();
const forwarded = process.argv.slice(2);
const npm = process.platform === "win32" ? "npm.cmd" : "npm";

const child = spawn(npm, ["run", "dev", "--", ...forwarded], {
  cwd: frozenRoot,
  stdio: "inherit",
  shell: process.platform === "win32",
});

child.on("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  process.exit(code === null ? 1 : code);
});
