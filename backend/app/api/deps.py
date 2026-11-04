from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.repositories import users as users_repo

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    name: str
    role: str


# Jab AUTH_ENABLED=false ho (sirf development), har request ko admin maana jata hai.
ANONYMOUS = CurrentUser(id="anonymous", email="", name="Authentication disabled", role="admin")


def get_db(request: Request):
    """Endpoint ko database deta hai. Na ho to saaf 503 error."""
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    return db


def _unauthorized(message="Not authenticated"):
    return HTTPException(status_code=401, detail=message, headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """Token se user pehchanta hai. Role hamesha database se aata hai, token se nahi."""
    config = request.app.state.config
    if not config.auth_enabled:
        return ANONYMOUS
    if credentials is None:
        raise _unauthorized()
    payload = decode_access_token(credentials.credentials, config.jwt_secret)
    if payload is None:
        raise _unauthorized("Invalid or expired token")
    db = get_db(request)
    user = await users_repo.get_by_id(db, payload["sub"])
    if user is None or not user.get("is_active", False):
        raise _unauthorized("Invalid or expired token")
    return CurrentUser(id=user["_id"], email=user["email"], name=user["name"], role=user["role"])


def require_roles(*roles):
    async def checker(user: CurrentUser = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to do this")
        return user

    return checker


require_admin = require_roles("admin")
