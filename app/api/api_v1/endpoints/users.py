from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin_user
from app.crud import user as user_crud
from app.db.database import get_async_session
from app.db.models import User
from app.schemas.user import User as UserSchema, UserUpdate, UserWithStats

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await user_crud.update_user(db, current_user, user_in)


@router.get("/", response_model=list[UserSchema])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_user),
):
    return await user_crud.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserSchema)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_user),
):
    user = await user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
