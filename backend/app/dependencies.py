from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth import decode_access_token
from app.database import get_session
from app.models import Role, User

bearer_scheme = HTTPBearer()
SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
                     session: SessionDep) -> User:
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims.get("sub", ""))
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


def require_roles(*roles: Role):
    def guard(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return guard
