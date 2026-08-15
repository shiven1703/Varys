"""User authentication and revocable PostgreSQL-backed sessions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

SESSION_COOKIE_NAME = "varys_session"
CSRF_HEADER_NAME = "X-CSRF-Token"
IDLE_TIMEOUT = timedelta(hours=12)
ABSOLUTE_SESSION_LIFETIME = timedelta(days=7)

_PASSWORD_HASHER = PasswordHasher(type=Type.ID)


class Base(DeclarativeBase):
    """Base for PostgreSQL operational-state models."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sessions: Mapped[list[AuthSession]] = relationship(back_populates="user")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(back_populates="sessions")


def validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters")


def hash_password(password: str) -> str:
    validate_password(password)
    return _PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def create_user(database: Session, username: str, password: str) -> User:
    normalized_username = username.strip()
    if not 1 <= len(normalized_username) <= 64:
        raise ValueError("username must be between 1 and 64 characters")
    now = _now()
    user = User(
        username=normalized_username,
        password_hash=hash_password(password),
        enabled=True,
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )
    database.add(user)
    return user


def login(
    database: Session, username: str, password: str, session_secret: str
) -> tuple[User, str, str] | None:
    user = database.scalar(select(User).where(User.username == username.strip()))
    if (
        user is None
        or not user.enabled
        or not verify_password(user.password_hash, password)
    ):
        return None

    now = _now()
    for existing in database.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)
        )
    ):
        existing.revoked_at = now
    session_token, csrf_token = token_urlsafe(32), token_urlsafe(32)
    database.add(
        AuthSession(
            user_id=user.id,
            token_hash=_token_hash(session_token, session_secret),
            csrf_token_hash=_token_hash(csrf_token, session_secret),
            created_at=now,
            last_seen_at=now,
            idle_expires_at=now + IDLE_TIMEOUT,
            absolute_expires_at=now + ABSOLUTE_SESSION_LIFETIME,
            revoked_at=None,
        )
    )
    user.last_login_at = now
    user.updated_at = now
    return user, session_token, csrf_token


def current_user(
    database: Session, session_token: str, session_secret: str
) -> User | None:
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _token_hash(session_token, session_secret),
            AuthSession.revoked_at.is_(None),
        )
    )
    if session is None:
        return None
    now = _now()
    if (
        not session.user.enabled
        or now >= session.idle_expires_at
        or now >= session.absolute_expires_at
    ):
        session.revoked_at = now
        return None
    session.last_seen_at = now
    session.idle_expires_at = min(now + IDLE_TIMEOUT, session.absolute_expires_at)
    return session.user


def revoke_session(
    database: Session, session_token: str, csrf_token: str, session_secret: str
) -> bool:
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _token_hash(session_token, session_secret),
            AuthSession.revoked_at.is_(None),
        )
    )
    if session is None or session.csrf_token_hash != _token_hash(
        csrf_token, session_secret
    ):
        return False
    session.revoked_at = _now()
    return True


def validate_csrf_token(
    database: Session, session_token: str, csrf_token: str, session_secret: str
) -> bool:
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _token_hash(session_token, session_secret),
            AuthSession.revoked_at.is_(None),
        )
    )
    return session is not None and session.csrf_token_hash == _token_hash(
        csrf_token, session_secret
    )


def _token_hash(token: str, session_secret: str) -> str:
    return sha256(f"{session_secret}:{token}".encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)
