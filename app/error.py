from fastapi import HTTPException

def _auth_401(code: str, message: str) -> HTTPException:
    # ✅ 建议保留 WWW-Authenticate，符合 Bearer 规范，也有利于工具识别
    return HTTPException(
        status_code=401,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )

