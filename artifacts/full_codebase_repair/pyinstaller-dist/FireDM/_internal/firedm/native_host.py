#!/usr/bin/env python3
"""FireDM native messaging host - stdio protocol per browser specs."""

import hashlib
import hmac
import json
import os
import struct
import sys

FIREDM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if FIREDM_DIR not in sys.path:
    sys.path.insert(0, FIREDM_DIR)

from firedm.native_messaging import MAX_NATIVE_MESSAGE_BYTES, load_or_create_secret, send_to_controller


def _log_error(*parts):
    print(*parts, file=sys.stderr)


def _verify_origin(msg, secret):
    """HMAC-SHA256 of origin + nonce using shared secret."""
    origin = msg.get("origin", "")
    nonce = msg.get("nonce", "")
    signature = msg.get("signature", "")
    expected = hmac.new(secret, f"{origin}:{nonce}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _read_message():
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len:
        return None
    length = struct.unpack("=I", raw_len)[0]
    if length > MAX_NATIVE_MESSAGE_BYTES:
        raise ValueError("native message too large")
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def _write_message(msg):
    encoded = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("=I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _send_to_controller(msg):
    """Forward to FireDM controller via authenticated local pipe/socket."""
    try:
        secret = load_or_create_secret()
        send_to_controller(msg, authkey=secret, timeout=5.0)
        return True
    except Exception as e:
        _log_error("Native host controller send failed:", e)
        return False


def main():
    while True:
        try:
            msg = _read_message()
        except Exception as exc:
            _write_message({"error": "invalid_message"})
            _log_error("Native host read failed:", exc)
            continue

        if msg is None:
            break

        if not isinstance(msg, dict):
            _write_message({"error": "invalid_message"})
            continue

        if _send_to_controller(msg):
            _write_message({"status": "ok"})
        else:
            _write_message({"error": "controller_unavailable"})


if __name__ == "__main__":
    main()
