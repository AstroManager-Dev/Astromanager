from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

_RUNTIME_ROOT = Path(os.environ.get("RUNTIME_ROOT", "/runtime"))
_SECRET_FILE = _RUNTIME_ROOT / "device_credentials.key"


def _ensure_secret_key() -> bytes:
    if _SECRET_FILE.exists():
        value = _SECRET_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value.encode("utf-8")
    _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    value = Fernet.generate_key()
    _SECRET_FILE.write_text(value.decode("utf-8"), encoding="utf-8")
    try:
        os.chmod(_SECRET_FILE, 0o600)
    except OSError:
        pass
    return value


def _fernet() -> Fernet:
    return Fernet(_ensure_secret_key())


def encrypt_device_password(password: str | None) -> str:
    clean = str(password or "")
    if not clean:
        return ""
    return _fernet().encrypt(clean.encode("utf-8")).decode("utf-8")


def decrypt_device_password(value: str | None) -> str:
    token = str(value or "").strip()
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return token


def mask_device_password(value: str | None) -> str:
    plain = decrypt_device_password(value)
    if not plain:
        return "—"
    return "•" * min(max(len(plain), 6), 16)


def fingerprint_device_password(value: str | None) -> str:
    plain = decrypt_device_password(value)
    if not plain:
        return ""
    digest = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return digest[:12]
