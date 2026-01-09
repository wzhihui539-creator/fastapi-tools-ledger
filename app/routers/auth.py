from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.db import get_session
from app.models import User
from app.schemas import UserCreate, Token
from app.security import hash_password, verify_password, create_access_token
from app.error import _auth_401

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(data: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=data.username, password_hash=hash_password(data.password))
    session.add(user)
    session.commit()
    return {"ok": True}

"""
这是一段基于 **FastAPI** 框架的用户注册接口代码，核心功能是接收用户注册请求、校验用户名唯一性、加密存储用户信息，简要解析如下：

### 1. 接口基本信息
- `@router.post("/register")`：定义一个 POST 类型的接口，访问路径为 `/register`（`router` 是 FastAPI 的路由实例，用于组织接口）。
- 接口接收的参数：
  - `data: UserCreate`：请求体数据，由 `UserCreate` 模型（Pydantic 模型）校验格式（比如用户名、密码的必填性、长度限制等）。
  - `session: Session = Depends(get_session)`：数据库会话（由 `get_session` 函数提供，通常是 SQLAlchemy 的数据库连接会话），用于操作数据库。

### 2. 核心逻辑步骤
#### （1）用户名唯一性校验
```python
existing = session.exec(select(User).where(User.username == data.username)).first()
```
- 通过 SQLAlchemy 的查询语法，查询数据库中是否存在与请求用户名（`data.username`）一致的 `User` 记录。
- `first()` 表示只取第一条匹配记录（不存在则返回 `None`）。

#### （2）冲突处理
```python
if existing:
    raise HTTPException(status_code=400, detail="Username already exists")
```
- 若查询到已有该用户名，抛出 400 错误（Bad Request），提示“用户名已存在”，终止接口流程。

#### （3）创建并存储用户
```python
user = User(username=data.username, password_hash=hash_password(data.password))
session.add(user)
session.commit()
```
- 若用户名唯一，创建 `User` 数据库模型实例：
  - 用户名直接使用请求中的 `data.username`。
  - 密码不直接存储明文，通过 `hash_password` 函数加密后存储为 `password_hash`（符合安全规范）。
- `session.add(user)`：将用户实例添加到数据库会话。
- `session.commit()`：提交会话，将数据持久化到数据库（真正执行插入操作）。

#### （4）返回结果
```python
return {"ok": True}
```
- 注册成功后，返回简单的成功响应（可扩展为返回用户 ID、token 等信息）。

### 3. 关键依赖/组件说明
- **FastAPI**：提供路由装饰器（`@router.post`）、请求体校验（`UserCreate`）、依赖注入（`Depends`）、异常处理（`HTTPException`）。
- **SQLAlchemy**：ORM 框架，通过 `Session` 操作数据库，`select` 语法用于查询，`add/commit` 用于数据插入。
- **Pydantic**：`UserCreate` 是 Pydantic 模型，用于校验请求体数据格式（比如确保 `username` 和 `password` 不为空）。
- **密码加密**：`hash_password` 是自定义加密函数（通常基于 bcrypt、passlib 等库），避免明文存储密码。

### 核心作用
实现“用户名唯一”的用户注册功能，兼顾数据校验、安全存储（密码加密）和友好的错误提示，是 Web 应用中最基础的用户模块接口之一。
"""


@router.post("/login")
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if (not user) or (not verify_password(form_data.password, user.password_hash)):
        raise _auth_401("INVALID_CREDENTIALS", "用户名或密码错误")

    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}
