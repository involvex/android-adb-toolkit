#!/usr/bin/env bun
/**
 * setup.ts — One-command local setup for the Android ADB Toolkit web UI.
 *
 *   bun setup.ts
 *   # or: bun run setup
 *
 * Fallback (no Bun required): python3 setup.py
 *
 * The server itself is Python stdlib only — this script just verifies the
 * environment and prints how to start.
 */

import { $ } from "bun";
import { existsSync } from "fs";
import { join } from "path";

const ROOT = import.meta.dir;
const URL = "http://127.0.0.1:8000/";

function ok(msg: string) {
  console.log(`  ✓ ${msg}`);
}
function warn(msg: string) {
  console.log(`  ! ${msg}`);
}
function fail(msg: string) {
  console.error(`  ✗ ${msg}`);
}

async function checkPython(): Promise<boolean> {
  try {
    const out = await $`python3 -c ${"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"}`.text();
    const ver = out.trim();
    const [maj, min] = ver.split(".").map(Number);
    if (maj < 3 || (maj === 3 && min < 8)) {
      fail(`Python 3.8+ required (found ${ver})`);
      return false;
    }
    ok(`Python ${ver}`);
    return true;
  } catch {
    fail("python3 not found — install Python 3.8+");
    return false;
  }
}

async function checkAdb(): Promise<boolean> {
  try {
    const out = await $`adb version`.text();
    const line = out.trim().split("\n")[0] || "adb";
    ok(line);
    return true;
  } catch {
    warn("adb not found on PATH");
    console.log("");
    console.log("    Install Android platform-tools, then re-run setup:");
    console.log("      macOS:   brew install android-platform-tools");
    console.log("      Windows: winget install Google.PlatformTools");
    console.log("      Debian:  sudo apt install adb");
    console.log("      Or:      https://developer.android.com/tools/releases/platform-tools");
    console.log("");
    return false;
  }
}

function checkTree(): boolean {
  const required = ["server.py", "adb_toolkit/server.py", "static/index.html"];
  let good = true;
  for (const rel of required) {
    if (existsSync(join(ROOT, rel))) ok(`found ${rel}`);
    else {
      fail(`missing ${rel} — run setup from the repo root`);
      good = false;
    }
  }
  return good;
}

function ensureEnvExample(): void {
  const example = join(ROOT, ".env.example");
  if (existsSync(example)) {
    ok(".env.example already present");
    return;
  }
  const body = `# Optional overrides for python3 server.py
# Copy to .env and export manually, or set in your shell:
ADB_TOOLKIT_HOST=127.0.0.1
ADB_TOOLKIT_PORT=8000
# ADB_PATH=adb
`;
  Bun.write(example, body);
  ok("wrote .env.example (optional — server uses stdlib defaults)");
}

async function smokeImport(): Promise<boolean> {
  try {
    await $`python3 -c ${"from adb_toolkit.server import main; print('ok')"}`.quiet();
    ok("adb_toolkit imports cleanly");
    return true;
  } catch {
    fail("could not import adb_toolkit — check you are in the repo root");
    return false;
  }
}

console.log("\nAndroid ADB Toolkit — local setup\n");

const pythonOk = await checkPython();
const treeOk = checkTree();
const importOk = pythonOk && treeOk ? await smokeImport() : false;
const adbOk = await checkAdb();
ensureEnvExample();

console.log("");
if (!pythonOk || !treeOk || !importOk) {
  fail("Setup incomplete. Fix the errors above, then re-run: bun setup.ts");
  console.log("");
  process.exit(1);
}

if (!adbOk) {
  warn("Setup OK for the server, but connect a device after installing ADB.\n");
} else {
  ok("Environment looks ready\n");
}

console.log("Next steps:\n");
console.log("  1. Start the local control panel:");
console.log("       python3 server.py\n");
console.log(`  2. Open:  ${URL}\n`);
console.log("  Optional:");
console.log("       python3 -m adb_toolkit devices");
console.log("       python3 wireless.py --list\n");
