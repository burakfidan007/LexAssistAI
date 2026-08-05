import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "exp", "iat", "iss", "aud"]},
        )
        return payload.get("sub")
    except JWTError:
        return None


def generate_secure_token() -> str:
    """One-time token for password reset / email verification links.

    Deliberately not a JWT: it must be single-use and revocable by deleting
    its hash from MongoDB, which a stateless JWT can't do without a
    denylist. The existing JWT session flow is untouched by this.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    # Reset/verification tokens are stored hashed, same reasoning as
    # password hashing: a DB leak alone shouldn't let anyone use them.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
