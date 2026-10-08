"""M2 认证 API：注册 / 登录 / 当前用户。"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.security import create_access_token, hash_password, verify_password
from app.db import SessionLocal
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/auth")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=32)


class LoginRequest(BaseModel):
    email: str
    password: str


def _user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "display_name": u.display_name,
            "role": u.role}


def _token_for(u: User) -> dict:
    return {"token": create_access_token(u.id, u.role), "user": _user_out(u)}


@router.post("/register")
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    db = SessionLocal()
    try:
        exists = db.scalar(select(User).where(func.lower(User.email) == email))
        if exists is not None:
            raise HTTPException(status_code=409, detail="该邮箱已注册")
        user = User(
            email=email,
            display_name=req.display_name.strip(),
            password_hash=hash_password(req.password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return _token_for(user)
    finally:
        db.close()


@router.post("/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user is None or not user.password_hash \
                or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已停用")
        return _token_for(user)
    finally:
        db.close()


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
