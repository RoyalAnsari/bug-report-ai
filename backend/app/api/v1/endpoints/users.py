from fastapi import APIRouter, Depends, HTTPException, Response
from starlette.concurrency import run_in_threadpool

from app.api.deps import CurrentUser, get_current_user, get_db
from app.core.security import hash_password
from app.repositories import users as users_repo
from app.schemas.auth import PasswordSet, UserCreate, UserOut, UserUpdate

# Yeh router router.py mein sirf admin ke liye lagaya gaya hai.
router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(db=Depends(get_db)):
    return [users_repo.to_public(doc) for doc in await users_repo.list_users(db)]


@router.post("", response_model=UserOut, status_code=201)
async def create_user(body: UserCreate, db=Depends(get_db)):
    password_hash = await run_in_threadpool(hash_password, body.password)
    created = await users_repo.create_user(db, body.email, body.name, body.role, password_hash)
    if created is None:
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    return users_repo.to_public(created)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db=Depends(get_db),
    admin: CurrentUser = Depends(get_current_user),
):
    fields = body.model_dump(exclude_none=True)
    if user_id == admin.id and ("role" in fields or "is_active" in fields):
        # Admin khud ko hata de to koi admin na bache.
        raise HTTPException(status_code=400, detail="You cannot change your own role or deactivate yourself")
    if not fields:
        existing = await users_repo.get_by_id(db, user_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="User not found")
        return users_repo.to_public(existing)
    updated = await users_repo.update_user(db, user_id, fields)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return users_repo.to_public(updated)


@router.put("/{user_id}/password", status_code=204)
async def reset_password(user_id: str, body: PasswordSet, db=Depends(get_db)):
    password_hash = await run_in_threadpool(hash_password, body.new_password)
    if not await users_repo.set_password(db, user_id, password_hash):
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=204)
