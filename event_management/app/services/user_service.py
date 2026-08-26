from sqlalchemy.orm import Session

from app.models.user import User


def search_users(db: Session, keyword: str | None, is_active: bool | None) -> list[User]:
    query = db.query(User)

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            (User.full_name.ilike(like_pattern)) | (User.email.ilike(like_pattern))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.order_by(User.id).all()
