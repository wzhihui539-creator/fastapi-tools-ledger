from sqlmodel import SQLModel, Session, create_engine
from fastapi import HTTPException
import uuid


DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    sid = uuid.uuid4().hex[:6]
    # print(f">>> open session {sid}")
    session = Session(engine)
    try:
        yield session
    except HTTPException:
        # ✅ 业务/鉴权错误：直接抛出，不做 rollback（通常没必要）
        raise
    except Exception as e:
        # ✅ 其他异常：更像程序错误/DB错误，回滚更合理
        session.rollback()
        print("rollback:", type(e), e)
        raise
    finally:
        session.close()
        # print(f"<<< close session {sid}")
"""
这是一个 Python 中基于 SQLAlchemy（ORM 框架）的**数据库会话生成器函数**，核心作用是安全、复用性地创建数据库会话（Session），简要解析如下：

### 1. 核心组件说明
- `def get_session():`：定义一个生成器函数（用 `yield` 而非 `return`），用于提供数据库会话实例。
- `Session(engine)`：SQLAlchemy 中创建数据库会话的类，`engine` 是数据库连接引擎（已提前配置，包含数据库地址、账号密码等信息），会话是与数据库交互的核心载体（执行增删改查）。
- `with ... as session:`：使用 `with` 上下文管理器，**自动管理会话的生命周期**：
  - 进入 `with` 块时：创建会话实例并赋值给 `session`；
  - 退出 `with` 块时：自动关闭会话（无论是否报错），避免资源泄露。
- `yield session`：生成器的核心，暂停函数执行并返回当前会话实例，供外部代码使用；外部使用完后，函数会回到 `with` 块末尾，自动关闭会话。

### 2. 核心作用与优势
- **安全管理资源**：通过 `with` 自动关闭会话，无需手动调用 `session.close()`，避免遗漏导致的数据库连接泄露。
- **复用性**：封装会话创建逻辑，外部代码无需重复写 `with Session(engine)`，直接调用 `get_session()` 即可获取可用会话。
- **生成器特性**：每次调用 `get_session()` 都会生成一个新的独立会话（通过 `next()` 或 `for` 循环获取），互不干扰，适合多并发场景。

### 3. 典型使用场景
```python
# 外部使用示例（配合 SQLAlchemy 操作数据库）
for session in get_session():
    # 用会话执行查询/新增等操作
    result = session.query(User).filter_by(id=1).first()
# 退出 for 循环后，会话自动关闭
```

### 总结
该函数是 SQLAlchemy 开发中的常见封装，核心目标是**简化会话创建、自动管理资源**，让开发者更专注于数据库业务逻辑，而非会话的开启/关闭细节。
"""