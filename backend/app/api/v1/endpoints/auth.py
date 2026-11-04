from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool

from app.api.deps import CurrentUser, get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_dummy, verify_password
from app.repositories import users as users_repo
from app.schemas.auth import AuthConfig, LoginRequest, MeOut, PasswordChange, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

WRONG_LOGIN = "Incorrect email or password"
LOCKED_MESSAGE = "Too many failed sign-in attempts. Try again later."


def _as_utc(value):
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.get("/config", response_model=AuthConfig)
async def auth_config(request: Request):
    """Frontend isse janta hai ke login page dikhana hai ya nahi."""
    return AuthConfig(auth_enabled=request.app.state.config.auth_enabled)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginRequest, request: Request, db=Depends(get_db)):
    config = request.app.state.config
    if not config.auth_enabled:
        raise HTTPException(status_code=400, detail="Authentication is not enabled on this server")

    user = await users_repo.get_by_email(db, body.email)
    if user is None:
        await run_in_threadpool(verify_dummy, body.password)
        raise HTTPException(status_code=401, detail=WRONG_LOGIN)

    locked_until = _as_utc(user.get("locked_until"))
    now = datetime.now(timezone.utc)
    if locked_until is not None and locked_until > now:
        retry_after = int((locked_until - now).total_seconds()) + 1
        raise HTTPException(status_code=429, detail=LOCKED_MESSAGE, headers={"Retry-After": str(retry_after)})

    password_ok = await run_in_threadpool(verify_password, body.password, user["password_hash"])
    if not password_ok:
        await users_repo.register_failed_login(db, user["_id"], config.max_failed_logins, config.lockout_minutes)
        raise HTTPException(status_code=401, detail=WRONG_LOGIN)
    if not user.get("is_active", False):
        raise HTTPException(status_code=401, detail=WRONG_LOGIN)

    await users_repo.touch_login(db, user["_id"])
    token = create_access_token(user["_id"], user["role"], config.jwt_secret, config.access_token_minutes)
    return TokenOut(
        access_token=token,
        expires_in=config.access_token_minutes * 60,
        user=users_repo.to_public(user),
    )


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser = Depends(get_current_user)):
    return MeOut(id=user.id, email=user.email, name=user.name, role=user.role)


@router.post("/change-password", status_code=204)
async def change_password(
    body: PasswordChange,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    if not request.app.state.config.auth_enabled:
        raise HTTPException(status_code=400, detail="Authentication is not enabled on this server")
    if body.new_password == body.current_password:
        raise HTTPException(status_code=400, detail="The new password must be different")

    document = await users_repo.get_by_id(db, user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="User not found")
    current_ok = await run_in_threadpool(verify_password, body.current_password, document["password_hash"])
    if not current_ok:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = await run_in_threadpool(hash_password, body.new_password)
    await users_repo.set_password(db, user.id, new_hash)
    return Response(status_code=204)
