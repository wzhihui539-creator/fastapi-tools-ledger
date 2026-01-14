from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.models import User
from app.schemas import UserCreate, Token
from app.security import hash_password, verify_password, create_access_token
from app.error import _auth_401
from app.services.ledger import abort   # ✅ 复用你现成的统一错误格式

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(data: UserCreate, session: Session = Depends(get_session)):
    # 1) 用户名重复（先查一遍，给友好提示）
    existing = session.exec(select(User).where(User.username == data.username)).first()
    if existing:
        abort(409, "USERNAME_EXISTS", "用户名已存在")

    # 2) 可选：bcrypt 的“72 bytes”坑（你之前踩过，很值）
    if len(data.password.encode("utf-8")) > 72:
        abort(400, "PASSWORD_TOO_LONG", "密码太长（bcrypt 限制 72 bytes），请缩短后再试")

    user = User(username=data.username, password_hash=hash_password(data.password))
    session.add(user)

    # 3) 再兜底一次：并发/竞态下 unique 冲突
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        abort(409, "USERNAME_EXISTS", "用户名已存在")

    return {"ok": True}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if (not user) or (not verify_password(form_data.password, user.password_hash)):
        raise _auth_401("INVALID_CREDENTIALS", "用户名或密码错误")

    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}
