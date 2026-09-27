#!/usr/bin/env node
/**
 * Deprecated root shim.
 * Prefer the Node CLI in ./cli/  (npm install && npm link inside cli/)
 * or the Python CLI: python3 -m adb_toolkit
 *
 * Previous implementation: legacy/cli/cli.js
 */
console.error(
  "NOTE: root cli.js is deprecated.\n" +
    "  Node CLI:  cd cli && npm install && npm link   →  adb-toolkit info\n" +
    "  Python CLI: python3 -m adb_toolkit devices\n" +
    "  Web UI:     python3 server.py\n"
);
process.exit(2);
