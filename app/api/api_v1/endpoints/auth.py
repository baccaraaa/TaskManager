from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
)
from app.schemas.user import User as UserSchema, UserCreate
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_async_session)):
    return await auth_service.register_user(db, user_in)


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    user = await auth_service.authenticate_user(db, login_data.username, login_data.password)
    return auth_service.create_tokens(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    body: RefreshTokenRequest, db: AsyncSession = Depends(get_async_session)
):
    return await auth_service.refresh_access_token(db, body.refresh_token)


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    body: PasswordResetRequest, db: AsyncSession = Depends(get_async_session)
):
    await auth_service.request_password_reset(db, body.email)
    return {"message": "If that email is registered, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    body: PasswordResetConfirm, db: AsyncSession = Depends(get_async_session)
):
    await auth_service.confirm_password_reset(db, body.token, body.new_password)
    return {"message": "Password has been reset successfully"}
