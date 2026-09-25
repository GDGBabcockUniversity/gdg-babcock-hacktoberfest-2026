from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.auth import hash_password
from app.dependencies import SessionDep, require_roles
from app.models import Role, User
from app.schemas import ActiveUpdate, AdminCreate

router = APIRouter(prefix="/admin/users", tags=["admin"])
SuperadminDep = Annotated[User, Depends(require_roles(Role.superadmin))]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_admin(payload: AdminCreate, session: SessionDep, superadmin: SuperadminDep):
    email = payload.email.lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=email, password_hash=hash_password(payload.password), role=Role.admin)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}


@router.patch("/{user_id}")
def set_admin_active(user_id: int, payload: ActiveUpdate, session: SessionDep,
                     superadmin: SuperadminDep):
    user = session.get(User, user_id)
    if user is None or user.role != Role.admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    user.is_active = payload.is_active
    session.add(user)
    session.commit()
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}

