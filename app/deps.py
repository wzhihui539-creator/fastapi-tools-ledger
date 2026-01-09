from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.db import get_session
from app.models import User
from app.security import decode_token
from app.error import _auth_401

# ✅ 关键：auto_error=False，让我们接管“没带token”的错误格式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def require_user(
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    # 1) 没带 token / Swagger 授权丢了 / 地址栏直接访问
    if not token:
        raise _auth_401("NOT_AUTHENTICATED", "未登录或登录已失效，请重新登录")

    # 2) token 无效 / 过期 / secret_key 不一致
    try:
        username = decode_token(token)
    except Exception:
        raise _auth_401("INVALID_TOKEN", "Token 无效或已过期，请重新登录")

    # 3) token 验过了，但用户在库里不存在（账号被删/数据被清空）
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise _auth_401("USER_NOT_FOUND", "用户不存在或已被删除")

    return user
