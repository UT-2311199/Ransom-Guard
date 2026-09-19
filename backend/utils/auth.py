import datetime
from datetime import timezone
import hashlib
import os
import jwt
from typing import Optional, Dict, Any

# JWT Secret and Algorithm
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ransomguard-super-secret-jwt-key-2026-prod")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REMEMBER_ME_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


def hash_password(password: str) -> str:
    """Hash password using bcrypt or secure salted SHA-256 fallback."""
    if HAS_BCRYPT:
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")
    else:
        salt = os.urandom(16).hex()
        digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"sha256${salt}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    if not hashed_password:
        return False
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$") or hashed_password.startswith("$2y$"):
            if HAS_BCRYPT:
                return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            return False
        elif hashed_password.startswith("sha256$"):
            parts = hashed_password.split("$")
            if len(parts) == 3:
                salt, stored_digest = parts[1], parts[2]
                computed = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
                return computed == stored_digest
        # Direct comparison fallback if plain (e.g. legacy/testing)
        return plain_password == hashed_password
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Create a new signed JWT access token."""
    to_encode = data.copy()
    now = datetime.datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": "RansomGuard Security Node",
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
