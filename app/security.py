import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from uuid import uuid4

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    secret = os.getenv("secret_key", "dev_secret")
    expire_minutes = int(os.getenv("access_token_expire_minutes", "120"))

    now = datetime.now(timezone.utc)
    iat = int(now.timestamp())
    exp = iat + expire_minutes * 60
    jti = uuid4().hex

    payload = {
        "sub": subject,
        "iat": iat,      # ✅ issued at：签发时间
        "exp": exp,      # ✅ expire：过期时间
        "jti": jti,      # ✅ token id：唯一编号
        "type": "access" # ✅ 可选：标记 token 类型
    }
    return jwt.encode(payload, secret, algorithm="HS256")



def decode_token(token: str) -> str:
    secret = os.getenv("secret_key", "dev_secret")
    payload = jwt.decode(token, secret, algorithms=["HS256"])

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Missing subject")

    # ✅ 可选：如果你写了 type，就顺手检查一下（不想严格也可以删掉）
    if payload.get("type") not in (None, "access"):
        raise ValueError("Invalid token type")
    print(jwt.decode(token, secret, algorithms=["HS256"]))
    return sub
