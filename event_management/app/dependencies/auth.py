from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)



def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Chưa xác thực hoặc token không hợp lệ")
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Token không hợp lệ")
    except JWTError:
        raise UnauthorizedException("Token không hợp lệ hoặc đã hết hạn")
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedException("Token không hợp lệ")
    user = db.get(User, user_id_int)
    if user is None:
        raise UnauthorizedException("Người dùng không tồn tại")
    if not user.is_active:
        raise UnauthorizedException("Tài khoản đã bị vô hiệu hóa")
    return user
