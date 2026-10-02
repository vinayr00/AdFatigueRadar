"""Password hashing and verification using argon2-cffi."""
from __future__ import annotations

import argon2

_hasher = argon2.PasswordHasher()


def hash_password(password: str) -> str:
    """Securely hash a password with Argon2id."""
    return _hasher.hash(password)


def verify_password(a: str, b: str) -> bool:
    """Verify a password against an Argon2id hash (order-independent)."""
    if not a or not b:
        return False
    if a.startswith("$argon2"):
        password_hash, password = a, b
    elif b.startswith("$argon2"):
        password_hash, password = b, a
    else:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except Exception:
        return False
