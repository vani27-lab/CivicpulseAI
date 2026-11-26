from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, require_roles
from app.core.security import hash_password
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter(
    prefix="/users",
    tags=["Users (admin only)"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)


@router.get("", response_model=list[UserOut])
def list_users(db: DbSession) -> list[User]:
    return list(db.scalars(select(User).order_by(User.role, User.full_name)))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession) -> User:
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

    if payload.role == UserRole.OFFICER:
        if payload.department_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "An officer must belong to a department.")
        if db.get(Department, payload.department_id) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "That department does not exist.")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        department_id=payload.department_id if payload.role == UserRole.OFFICER else None,
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
