from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.db import create_db_and_tables
from app.routers import auth, tools, movements

class Settings(BaseSettings):
    # 声明.env里会出现的字段
    secret_key: str
    access_token_expire_minutes: int = 120

    # v2 写法：指定 env 文件 + 允许额外字段也不报错（可选）
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 读取.env（实例化时加载并校验）
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # ✅ 启动阶段
    yield  # ✅ 应用开始处理请求
    # --- 关闭后执行的代码 (Shutdown) ---
    # 例如：可以在这里关闭数据库连接，你的项目暂时没有手动关闭逻辑，可以留空
    print("服务已关闭")

app = FastAPI(title="FastAPI Starter - Tools Ledger", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(tools.router)
app.include_router(movements.router)

@app.get("/health")
def health():
    return {"ok": True}
