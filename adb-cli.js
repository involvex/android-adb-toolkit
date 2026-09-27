#!/usr/bin/env node
/**
 * Deprecated root shim. See cli/ for the Node CLI, or python3 -m adb_toolkit.
 * Previous implementation: legacy/cli/adb-cli.js
 */
console.error(
  "NOTE: adb-cli.js is deprecated.\n" +
    "  Node CLI:   cd cli && npm install && npm link\n" +
    "  Python CLI: python3 -m adb_toolkit\n"
);
process.exit(2);
