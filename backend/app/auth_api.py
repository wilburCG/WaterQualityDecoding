"""M2 认证 API：手机号一键进入（新号自动注册）+ 管理员邮箱密码登录。"""
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
# 中国大陆手机号
_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


class PhoneAuthRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=32)
    display_name: str | None = Field(default=None, min_length=1, max_length=32)


class LoginRequest(BaseModel):
    email: str
    password: str


def _user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "phone": u.phone,
            "display_name": u.display_name, "role": u.role}


def _token_for(u: User) -> dict:
    return {"token": create_access_token(u.id, u.role), "user": _user_out(u)}


@router.post("/phone")
def phone_auth(req: PhoneAuthRequest):
    """手机号一键进入：已有账号直接登录；新手机号需带昵称，自动注册。"""
    phone = req.phone.strip()
    if not _PHONE_RE.match(phone):
        raise HTTPException(status_code=400, detail="请输入正确的 11 位手机号")

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.phone == phone))
        if user is not None:
            if not user.is_active:
                raise HTTPException(status_code=403, detail="账号已停用")
            return _token_for(user)

        name = (req.display_name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="首次进入请填写昵称")
        user = User(phone=phone, display_name=name, role="user")
        db.add(user)
        db.commit()
        db.refresh(user)
        return _token_for(user)
    finally:
        db.close()


@router.post("/login")
def login(req: LoginRequest):
    """管理员邮箱 + 密码登录。"""
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
