"""Shared native-messaging transport helpers.

This module is intentionally stdlib-only. It is imported by both the GUI
controller and the browser native-host process, so it must not print to stdout.
"""

from __future__ import annotations

import contextlib
import json
import os
import stat
import tempfile
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import Any

from . import config
from .app_paths import choose_settings_dir, resolve_global_settings_dir

HOST_NAME = "com.firedm.nativehost"
SECRET_FILENAME = "native_host_secret"
MAX_NATIVE_MESSAGE_BYTES = 1024 * 1024


def resolve_native_settings_folder() -> Path:
    """Return the same settings folder policy as `setting.py` without logging."""

    if config.sett_folder:
        return Path(config.sett_folder)

    global_folder = resolve_global_settings_dir(
        config.APP_NAME,
        config.operating_system,
        current_directory=config.current_directory,
    )
    settings_folder = choose_settings_dir(config.current_directory, global_folder)
    config.global_sett_folder = os.fspath(global_folder)
    config.sett_folder = os.fspath(settings_folder)
    return Path(settings_folder)


def native_secret_path(settings_folder: str | os.PathLike[str] | None = None) -> Path:
    folder = Path(settings_folder) if settings_folder else resolve_native_settings_folder()
    return folder / SECRET_FILENAME


def load_or_create_secret(settings_folder: str | os.PathLike[str] | None = None) -> bytes:
    path = native_secret_path(settings_folder)
    if path.is_file():
        return path.read_bytes()

    path.parent.mkdir(parents=True, exist_ok=True)
    secret = os.urandom(32)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(os.fspath(path), flags, 0o600)
    except FileExistsError:
        return path.read_bytes()
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(secret)
    except Exception:
        with contextlib.suppress(OSError):
            os.close(fd)
        raise

    with contextlib.suppress(OSError):
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return secret


def controller_address() -> str:
    if config.operating_system == "Windows":
        return r"\\.\pipe\FireDM_Controller"
    return os.path.join(tempfile.gettempdir(), "firedm_controller.sock")


def cleanup_stale_controller_endpoint(address: str | None = None) -> None:
    address = address or controller_address()
    if config.operating_system != "Windows" and os.path.exists(address):
        os.unlink(address)


def make_listener(authkey: bytes) -> Listener:
    cleanup_stale_controller_endpoint()
    return Listener(controller_address(), authkey=authkey)


def send_to_controller(message: dict[str, Any], authkey: bytes, timeout: float = 5.0) -> bool:
    encoded = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_NATIVE_MESSAGE_BYTES:
        raise ValueError("native message too large")

    conn = Client(controller_address(), authkey=authkey)
    try:
        _ = timeout
        conn.send_bytes(encoded)
    finally:
        conn.close()
    return True


def decode_controller_payload(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_NATIVE_MESSAGE_BYTES:
        raise ValueError("native message too large")
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("native message must be a JSON object")
    return payload
