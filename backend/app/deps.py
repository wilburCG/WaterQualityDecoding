"""FastAPI 依赖：当前登录用户 / 管理员。"""
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db import SessionLocal
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> User:
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="未登录")
    try:
        payload = decode_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="登录已失效，请重新登录")
    db = SessionLocal()
    try:
        user = db.get(User, int(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="用户不存在或已停用")
        return user
    finally:
        db.close()


def get_optional_user(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[User]:
    if cred is None or not cred.credentials:
        return None
    try:
        payload = decode_token(cred.credentials)
    except jwt.PyJWTError:
        return None
    db = SessionLocal()
    try:
        return db.get(User, int(payload["sub"]))
    finally:
        db.close()


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="需要管理员权限")
    return user
