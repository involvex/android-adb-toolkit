# ADB Toolkit API Reference

Base URL (default): `http://127.0.0.1:8000`

Authentication: none (local process). Keep the bind address on localhost unless you intentionally expose it.

All JSON error responses look like:

```json
{
  "error": "device_not_found",
  "message": "Device not found: emulator-5554",
  "status": 404,
  "details": "emulator-5554"
}
```

Common `error` codes: `adb_missing` (503), `device_not_found` / `no_device` (404), `invalid_param` / `invalid_serial` / `invalid_json` (400), `timeout` / `command_failed` (500), `not_found` (404).

---

## Health

### `GET /api/health`

```json
{ "status": "ok", "version": "1.1.0", "adb_available": true }
```

---

## Devices

### `GET /api/devices`

```json
{
  "count": 1,
  "devices": [
    {
      "serial": "emulator-5554",
      "status": "device",
      "model": "sdk gphone x86",
      "product": "sdk_gphone",
      "connection": "usb"
    }
  ]
}
```

### `GET /api/device/<serial>/info`

```json
{
  "serial": "emulator-5554",
  "model": "Pixel 6",
  "brand": "google",
  "android": "14",
  "api": "34",
  "build": "...",
  "battery": 87,
  "battery_status": "charging"
}
```

---

## Packages

### `GET /api/device/<serial>/packages?type=user|system|all`

```json
{ "packages": ["com.example.app"], "count": 1, "type": "user" }
```

### `POST /api/device/<serial>/uninstall`

```json
{ "package": "com.example.app" }
```

### `POST /api/device/<serial>/clear`

```json
{ "package": "com.example.app" }
```

### `POST /api/device/<serial>/install`

Raw APK body with `Content-Type: application/octet-stream` (or `application/vnd.android.package-archive`).

---

## Input & control

### `POST /api/device/<serial>/tap`

```json
{ "x": 540, "y": 960 }
```

### `POST /api/device/<serial>/swipe`

```json
{ "x1": 540, "y1": 1500, "x2": 540, "y2": 500, "duration": 300 }
```

### `POST /api/device/<serial>/text`

```json
{ "input": "hello world" }
```

### `POST /api/device/<serial>/key`

```json
{ "code": 4 }
```

(`3` Home, `4` Back, `26` Power, …)

---

## Screenshot

### `GET /api/device/<serial>/screenshot`

Default JSON:

```json
{ "image_base64": "...", "format": "png", "bytes": 12345 }
```

Add `?format=png` for a raw `image/png` response.

---

## Shell

### `POST /api/device/<serial>/shell`

```json
{ "command": "dumpsys battery", "timeout": 30 }
```

```json
{ "stdout": "...", "stderr": "", "returncode": 0, "success": true }
```

Commands run via `adb shell` on the device (no host `/bin/sh`).

---

## Files

### `GET /api/device/<serial>/files?path=/sdcard`

```json
{ "path": "/sdcard", "listing": "...", "returncode": 0 }
```

---

## Logcat

### `GET /api/device/<serial>/logcat?lines=100&level=V&tag=`

Buffered snapshot (`adb logcat -d -t N`). Optional `level` (`V|D|I|W|E|F|S`) and `tag`.

```json
{ "lines": ["..."], "returncode": 0 }
```

### `GET /api/device/<serial>/logcat/stream` (SSE)

Live Server-Sent Events stream of `adb logcat`. Query params:

| Param | Description |
|-------|-------------|
| `level` | Minimum priority: `V`, `D`, `I`, `W`, `E`, `F` (default `V`) |
| `tag` | Optional tag filter (other tags silenced) |
| `package` | Optional package name → filtered via `--pid` (process must be running) |
| `clear` | `1` to run `logcat -c` before streaming |

Example events:

```
event: status
data: {"state":"started","serial":"emulator-5554","level":"I"}

event: line
data: {"text":"I/ActivityManager: ..."}

event: status
data: {"state":"ended","returncode":0}
```

Closing the HTTP connection stops `adb logcat` on the server (SIGTERM/kill). Bind remains localhost by default. Invalid serial/level/tag/package return JSON `400` before the stream starts.

---

## Wireless ADB

### `POST /api/wireless/pair`

```json
{ "host": "192.168.1.20", "port": 37123, "pairing_code": "123456" }
```

### `POST /api/wireless/connect`

```json
{ "host": "192.168.1.20", "port": 5555 }
```

### `POST /api/wireless/disconnect`

```json
{ "target": "192.168.1.20:5555" }
```

Omit `target` (or send `{}`) to disconnect all wireless endpoints.

### `GET /api/wireless/status`

Lists devices and highlights wireless connections.
