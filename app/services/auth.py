from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_password_hash,
)
from app.crud import user as user_crud
from app.db.models import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate


async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Check if email already exists
    existing = await user_crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    # Check if username already exists
    existing = await user_crud.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    user = await user_crud.create_user(db, user_in)

    # Send welcome email via Celery (non-blocking)
    try:
        from app.workers.tasks import send_welcome_email
        send_welcome_email.delay(user.email, user.username)
    except Exception:
        pass  # Don't fail registration if email fails

    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    user = await user_crud.get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


def create_tokens(user: User) -> Token:
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Token:
    payload = verify_token(refresh_token, token_type="refresh")
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user = await user_crud.get_user_by_username(db, username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return create_tokens(user)


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Request password reset. Always returns success to prevent email enumeration."""
    user = await user_crud.get_user_by_email(db, email)
    if user:
        token = create_password_reset_token(email)
        try:
            from app.workers.tasks import send_password_reset_email
            send_password_reset_email.delay(email, token)
        except Exception:
            pass


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    user = await user_crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
