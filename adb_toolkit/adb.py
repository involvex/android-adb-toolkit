"""Safe ADB subprocess helpers.

All ADB invocations use argument lists (never shell=True) and enforce timeouts.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence

# Serials are alphanumeric with optional :port for wireless / emulator names.
_SERIAL_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_TAG_RE = re.compile(r"^[A-Za-z0-9_./+]{1,128}$")
_PACKAGE_RE = re.compile(r"^[A-Za-z0-9._]+$")
_LOG_LEVELS = frozenset({"V", "D", "I", "W", "E", "F", "S"})
DEFAULT_TIMEOUT = 30
ADB_BIN = os.environ.get("ADB_PATH", "adb")


class AdbError(Exception):
    """Raised when ADB is missing or a command fails unrecoverably."""

    def __init__(self, message: str, *, code: str = "adb_error", details: str = ""):
        super().__init__(message)
        self.code = code
        self.details = details
        self.message = message


@dataclass
class AdbResult:
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return self.stdout if self.stdout else self.stderr


def adb_available() -> bool:
    return shutil.which(ADB_BIN) is not None


def validate_serial(serial: Optional[str]) -> Optional[str]:
    if serial is None or serial == "":
        return None
    if not _SERIAL_RE.match(serial):
        raise AdbError("Invalid device serial", code="invalid_serial", details=serial)
    return serial


def run_adb(
    args: Sequence[str],
    *,
    serial: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    check: bool = False,
) -> AdbResult:
    """Run ``adb [ -s serial ] <args>`` without a shell.

    Raises:
        AdbError: if ADB is not installed, times out, or check=True and rc != 0.
    """
    if not adb_available():
        raise AdbError(
            "ADB not found in PATH. Install Android platform-tools.",
            code="adb_missing",
        )

    serial = validate_serial(serial)
    cmd: List[str] = [ADB_BIN]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(str(a) for a in args)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdbError(
            f"ADB command timed out after {timeout}s",
            code="timeout",
            details=" ".join(cmd),
        ) from exc
    except FileNotFoundError as exc:
        raise AdbError("ADB not found in PATH", code="adb_missing") from exc

    result = AdbResult(
        stdout=(proc.stdout or "").strip(),
        stderr=(proc.stderr or "").strip(),
        returncode=proc.returncode,
    )
    if check and not result.ok:
        raise AdbError(
            "ADB command failed",
            code="command_failed",
            details=result.stderr or result.stdout or f"exit {result.returncode}",
        )
    return result


def list_devices() -> List[dict]:
    """Return connected devices from ``adb devices -l``."""
    result = run_adb(["devices", "-l"], timeout=10)
    devices: List[dict] = []
    for line in result.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, status = parts[0], parts[1]
        if status not in ("device", "emulator", "unauthorized", "offline"):
            continue
        props = {}
        for token in parts[2:]:
            if ":" in token:
                key, _, value = token.partition(":")
                props[key] = value
        devices.append(
            {
                "serial": serial,
                "status": status,
                "model": props.get("model", "").replace("_", " "),
                "product": props.get("product", ""),
                "transport": props.get("transport_id", ""),
                "connection": "wireless" if ":" in serial else "usb",
            }
        )
    return devices


def get_prop(serial: Optional[str], prop: str, timeout: float = 10) -> str:
    result = run_adb(["shell", "getprop", prop], serial=serial, timeout=timeout)
    return result.stdout


def get_device_info(serial: Optional[str] = None) -> dict:
    """Collect common device properties and battery level."""
    if serial:
        validate_serial(serial)
    devices = list_devices()
    online = [d for d in devices if d["status"] in ("device", "emulator")]
    if serial:
        match = next((d for d in online if d["serial"] == serial), None)
        if not match:
            raise AdbError(
                f"Device not found: {serial}",
                code="device_not_found",
                details=serial,
            )
    elif not online:
        raise AdbError("No device connected", code="no_device")
    else:
        serial = online[0]["serial"]

    info = {
        "serial": serial,
        "model": get_prop(serial, "ro.product.model") or "Unknown",
        "brand": get_prop(serial, "ro.product.brand"),
        "android": get_prop(serial, "ro.build.version.release"),
        "api": get_prop(serial, "ro.build.version.sdk"),
        "build": get_prop(serial, "ro.build.display.id"),
        "manufacturer": get_prop(serial, "ro.product.manufacturer"),
        "battery": None,
        "battery_status": None,
    }

    bat = run_adb(["shell", "dumpsys", "battery"], serial=serial, timeout=15)
    statuses = {
        1: "unknown",
        2: "charging",
        3: "discharging",
        4: "not charging",
        5: "full",
    }
    for line in bat.stdout.splitlines():
        line = line.strip()
        if line.startswith("level:"):
            try:
                info["battery"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                info["battery"] = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            try:
                code = int(line.split(":", 1)[1].strip())
                info["battery_status"] = statuses.get(code, "unknown")
            except ValueError:
                pass

    return info


def list_packages(
    serial: Optional[str] = None,
    pkg_type: str = "user",
) -> List[str]:
    args = ["shell", "pm", "list", "packages"]
    if pkg_type == "user":
        args.append("-3")
    elif pkg_type == "system":
        args.append("-s")
    elif pkg_type != "all":
        raise AdbError(
            "type must be user, system, or all",
            code="invalid_param",
        )
    result = run_adb(args, serial=serial, timeout=60)
    packages = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line[len("package:") :])
    return packages


def shell_command(
    command: str,
    *,
    serial: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> AdbResult:
    """Run a device shell command safely (no host shell).

    The command is passed as a single argument to ``adb shell``, which avoids
    host-side injection. Empty commands are rejected.
    """
    command = (command or "").strip()
    if not command:
        raise AdbError("Empty shell command", code="invalid_param")
    if "\x00" in command:
        raise AdbError("Invalid shell command", code="invalid_param")
    # adb shell with one string arg runs via the device shell without host sh.
    return run_adb(["shell", command], serial=serial, timeout=timeout)


def screencap_png(serial: Optional[str] = None, timeout: float = 45) -> bytes:
    """Capture a screenshot as PNG bytes via ``adb exec-out screencap -p``."""
    if not adb_available():
        raise AdbError("ADB not found in PATH", code="adb_missing")

    serial = validate_serial(serial)
    cmd: List[str] = [ADB_BIN]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["exec-out", "screencap", "-p"])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdbError("Screenshot timed out", code="timeout") from exc

    if proc.returncode != 0 or not proc.stdout:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")
        raise AdbError(
            "Screenshot failed",
            code="command_failed",
            details=err or f"exit {proc.returncode}",
        )

    data = proc.stdout
    # Some devices/ADB bridges corrupt LF→CRLF; fix classic PNG header issue.
    if data.startswith(b"\r\n"):
        data = data.replace(b"\r\n", b"\n")
    return data


def tap(serial: Optional[str], x: int, y: int) -> AdbResult:
    return run_adb(
        ["shell", "input", "tap", str(int(x)), str(int(y))],
        serial=serial,
        timeout=10,
    )


def swipe(
    serial: Optional[str],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration_ms: int = 300,
) -> AdbResult:
    return run_adb(
        [
            "shell",
            "input",
            "swipe",
            str(int(x1)),
            str(int(y1)),
            str(int(x2)),
            str(int(y2)),
            str(int(duration_ms)),
        ],
        serial=serial,
        timeout=15,
    )


def input_text(serial: Optional[str], text: str) -> AdbResult:
    # Escape spaces for Android input text; keep as single argv element.
    escaped = (text or "").replace(" ", "%s").replace("'", "\\'")
    return run_adb(
        ["shell", "input", "text", escaped],
        serial=serial,
        timeout=15,
    )


def keyevent(serial: Optional[str], code: int) -> AdbResult:
    return run_adb(
        ["shell", "input", "keyevent", str(int(code))],
        serial=serial,
        timeout=10,
    )


def uninstall_package(serial: Optional[str], package: str) -> AdbResult:
    if not re.match(r"^[A-Za-z0-9._]+$", package or ""):
        raise AdbError("Invalid package name", code="invalid_param")
    return run_adb(["uninstall", package], serial=serial, timeout=60)


def clear_package(serial: Optional[str], package: str) -> AdbResult:
    if not re.match(r"^[A-Za-z0-9._]+$", package or ""):
        raise AdbError("Invalid package name", code="invalid_param")
    return run_adb(
        ["shell", "pm", "clear", package],
        serial=serial,
        timeout=60,
    )


def install_apk(serial: Optional[str], apk_path: str) -> AdbResult:
    if not os.path.isfile(apk_path):
        raise AdbError("APK file not found", code="invalid_param", details=apk_path)
    return run_adb(["install", "-r", apk_path], serial=serial, timeout=180)


def wireless_connect(host: str, port: int = 5555) -> AdbResult:
    if not re.match(r"^[\w.-]+$", host or ""):
        raise AdbError("Invalid host", code="invalid_param")
    target = f"{host}:{int(port)}"
    return run_adb(["connect", target], timeout=20)


def wireless_pair(host: str, port: int, pairing_code: str) -> AdbResult:
    if not re.match(r"^[\w.-]+$", host or ""):
        raise AdbError("Invalid host", code="invalid_param")
    if not re.match(r"^\d{6}$", pairing_code or ""):
        raise AdbError(
            "Pairing code must be 6 digits",
            code="invalid_param",
        )
    target = f"{host}:{int(port)}"
    return run_adb(["pair", target, pairing_code], timeout=30)


def wireless_disconnect(target: str = "") -> AdbResult:
    if target:
        if not re.match(r"^[\w.:-]+$", target):
            raise AdbError("Invalid disconnect target", code="invalid_param")
        return run_adb(["disconnect", target], timeout=10)
    return run_adb(["disconnect"], timeout=10)


def save_temp_upload(data: bytes, suffix: str = ".apk") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def validate_log_level(level: Optional[str]) -> str:
    value = (level or "V").strip().upper()
    if value not in _LOG_LEVELS:
        raise AdbError(
            "Invalid log level (use V, D, I, W, E, F, or S)",
            code="invalid_param",
            details=value,
        )
    return value


def validate_log_tag(tag: Optional[str]) -> Optional[str]:
    if tag is None or tag == "":
        return None
    tag = tag.strip()
    if not _TAG_RE.match(tag):
        raise AdbError("Invalid logcat tag", code="invalid_param", details=tag)
    return tag


def validate_package_name(package: Optional[str]) -> Optional[str]:
    if package is None or package == "":
        return None
    package = package.strip()
    if not _PACKAGE_RE.match(package):
        raise AdbError("Invalid package name", code="invalid_param", details=package)
    return package


def resolve_package_pid(serial: Optional[str], package: str) -> int:
    """Resolve a running package to a PID via ``adb shell pidof -s``."""
    package = validate_package_name(package)
    if not package:
        raise AdbError("Package required", code="invalid_param")
    result = run_adb(["shell", "pidof", "-s", package], serial=serial, timeout=10)
    pid_text = (result.stdout or "").strip().split()[0] if result.stdout else ""
    if not pid_text.isdigit():
        raise AdbError(
            f"No running process for package {package}",
            code="process_not_found",
            details=result.stderr or result.stdout,
        )
    return int(pid_text)


def build_logcat_args(
    *,
    level: str = "V",
    tag: Optional[str] = None,
    pid: Optional[int] = None,
    clear: bool = False,
    dump: bool = False,
    lines: Optional[int] = None,
) -> List[str]:
    """Build argv for ``adb logcat`` (without the leading ``adb`` / ``-s``)."""
    level = validate_log_level(level)
    tag = validate_log_tag(tag)
    args: List[str] = ["logcat"]
    if clear:
        # Caller typically runs clear as a separate one-shot; kept for completeness.
        return ["logcat", "-c"]
    if dump:
        args.append("-d")
    if lines is not None:
        count = max(1, min(int(lines), 2000))
        args.extend(["-t", str(count)])
    # Format includes priority/tag for UI filtering readability.
    args.extend(["-v", "brief"])
    if pid is not None:
        pid = int(pid)
        if pid <= 0:
            raise AdbError("Invalid pid", code="invalid_param")
        args.extend(["--pid", str(pid)])
    if tag:
        args.append(f"{tag}:{level}")
        if level != "S":
            args.append("*:S")
    else:
        args.append(f"*:{level}")
    return args


def open_logcat_stream(
    serial: Optional[str] = None,
    *,
    level: str = "V",
    tag: Optional[str] = None,
    package: Optional[str] = None,
    clear: bool = False,
) -> subprocess.Popen:
    """Start a live ``adb logcat`` process (stdout line-buffered text).

    Never uses a shell. Caller must ``terminate_process`` when done.
    """
    if not adb_available():
        raise AdbError(
            "ADB not found in PATH. Install Android platform-tools.",
            code="adb_missing",
        )

    serial = validate_serial(serial)
    package = validate_package_name(package)
    pid: Optional[int] = None
    if package:
        pid = resolve_package_pid(serial, package)

    if clear:
        run_adb(["logcat", "-c"], serial=serial, timeout=10)

    logcat_args = build_logcat_args(level=level, tag=tag, pid=pid)
    cmd: List[str] = [ADB_BIN]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(logcat_args)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise AdbError("ADB not found in PATH", code="adb_missing") from exc
    return proc


def terminate_process(proc: Optional[subprocess.Popen], *, grace: float = 1.0) -> None:
    """Terminate a child process and drain pipes (best-effort)."""
    if proc is None:
        return
    if proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGTERM)
    except (ProcessLookupError, OSError):
        return
    deadline = time.time() + grace
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    if proc.poll() is None:
        try:
            proc.kill()
        except (ProcessLookupError, OSError):
            pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    for pipe in (proc.stdout, proc.stderr):
        if pipe:
            try:
                pipe.close()
            except OSError:
                pass
