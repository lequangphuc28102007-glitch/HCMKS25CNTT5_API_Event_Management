from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.schemas.user import UserResponse
from app.models.user import User
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user



@router.get("/users", response_model=List[UserResponse])
def get_users(
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    query = db.query(User)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    if status:
        query = query.filter(User.status == status)

    return query.all()