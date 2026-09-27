# ADB Toolkit CLI (Node)

Optional Node.js companion for the [Android ADB Toolkit](https://github.com/involvex/android-adb-toolkit) web app.

> Prefer the web UI (`python3 server.py`) or Python CLI (`python3 -m adb_toolkit`) unless you specifically want Node.

## Install

```bash
cd cli/
npm install
npm link   # makes `adb-toolkit` available globally
```

## Commands

```bash
adb-toolkit info                              # device summary
adb-toolkit screenshot                        # save screenshot to disk
adb-toolkit screenshot -o screen.png          # custom filename
adb-toolkit perms --pkg com.facebook.katana   # list dangerous perms
adb-toolkit perms --pkg com.facebook.katana --revoke
adb-toolkit packages --user                   # list user-installed apps
adb-toolkit packages --filter google          # search packages
adb-toolkit type "hello world"                # type text on device
```

Older root-level `cli.js` / `adb-cli.js` copies live under [`../legacy/cli/`](../legacy/cli/README.md).
