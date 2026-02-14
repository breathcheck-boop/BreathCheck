from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
from typing import Optional, Tuple

try:  # pragma: no cover - optional dependency import
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover - fallback for missing dependency
    Fernet = None
    InvalidToken = Exception

import keyring

logger = logging.getLogger(__name__)


def get_api_key(service_name: str, username: str = "default") -> Optional[str]:
    try:
        return keyring.get_password(service_name, username)
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to read API key from keyring: %s", exc)
        return None


def set_api_key(service_name: str, api_key: str, username: str = "default") -> None:
    try:
        keyring.set_password(service_name, username, api_key)
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to store API key in keyring: %s", exc)


_ENC_PREFIX = "enc:"


def _service_name_from_env() -> str:
    return os.getenv("APP_NAME", "BreathCheck")


def _get_encryption_key(service_name: str) -> Optional[str]:
    try:
        return keyring.get_password(f"{service_name}-enc", "key")
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to read encryption key: %s", exc)
        return None


def ensure_encryption_key(service_name: str) -> bool:
    if Fernet is None:
        return False
    existing = _get_encryption_key(service_name)
    if existing:
        return True
    try:
        key = Fernet.generate_key().decode("utf-8")
        keyring.set_password(f"{service_name}-enc", "key", key)
        return True
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to store encryption key: %s", exc)
        return False


def delete_encryption_key(service_name: str) -> None:
    try:
        keyring.delete_password(f"{service_name}-enc", "key")
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to delete encryption key: %s", exc)


def _get_fernet(service_name: str) -> Optional[Fernet]:
    if Fernet is None:
        return None
    key = _get_encryption_key(service_name)
    if not key:
        if not ensure_encryption_key(service_name):
            return None
        key = _get_encryption_key(service_name)
    if not key:
        return None
    return Fernet(key.encode("utf-8"))


def encrypt_text(plain_text: str, service_name: str | None = None) -> str:
    if not plain_text:
        return ""
    if plain_text.startswith(_ENC_PREFIX):
        return plain_text
    service = service_name or _service_name_from_env()
    fernet = _get_fernet(service)
    if not fernet:
        return plain_text
    token = fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    return f"{_ENC_PREFIX}{token}"


def decrypt_text(cipher_text: str, service_name: str | None = None) -> str:
    if not cipher_text:
        return ""
    if not cipher_text.startswith(_ENC_PREFIX):
        return cipher_text
    service = service_name or _service_name_from_env()
    fernet = _get_fernet(service)
    if not fernet:
        return cipher_text
    token = cipher_text[len(_ENC_PREFIX) :].encode("utf-8")
    try:
        return fernet.decrypt(token).decode("utf-8")
    except InvalidToken:
        return cipher_text


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)


def get_master_password_hash(service_name: str) -> Optional[str]:
    try:
        return keyring.get_password(f"{service_name}-master", "hash")
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to read master password hash: %s", exc)
        return None


def set_master_password(service_name: str, password: str) -> None:
    salt = secrets.token_bytes(16)
    digest = _hash_password(password, salt)
    payload = f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"
    try:
        keyring.set_password(f"{service_name}-master", "hash", payload)
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to store master password hash: %s", exc)
    ensure_encryption_key(service_name)


def verify_master_password(service_name: str, password: str) -> bool:
    stored = get_master_password_hash(service_name)
    if not stored:
        return False
    try:
        salt_b64, digest_b64 = stored.split(":", 1)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        actual = _hash_password(password, salt)
        return secrets.compare_digest(expected, actual)
    except Exception:
        return False


def delete_master_password(service_name: str) -> None:
    try:
        keyring.delete_password(f"{service_name}-master", "hash")
    except Exception as exc:  # pragma: no cover - keyring backend variability
        logger.warning("Failed to delete master password: %s", exc)
