import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

ALGORITHM = "HS256"

_hasher = PasswordHasher()
# Jab email maujood nahi hota tab bhi itna hi waqt lagta hai, taake pata na chale ke email sahi tha ya nahi.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing-only")


def hash_password(password):
    return _hasher.hash(password)


def verify_password(password, password_hash):
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_dummy(password):
    verify_password(password, _DUMMY_HASH)
    return False


def create_access_token(user_id, role, secret, minutes, now=None):
    now = now or datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token, secret):
    """Sahi token ka payload wapas deta hai, warna None (ghalat, tampered ya expired)."""
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    if not isinstance(payload.get("sub"), str):
        return None
    return payload
