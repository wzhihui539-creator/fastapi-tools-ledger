from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.db import create_db_and_tables
from app.routers import auth, tools

class Settings(BaseSettings):
    # 声明.env里会出现的字段
    secret_key: str
    access_token_expire_minutes: int = 120

    # v2 写法：指定 env 文件 + 允许额外字段也不报错（可选）
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 读取.env（实例化时加载并校验）
settings = Settings()

app = FastAPI(title="FastAPI Starter - Tools Ledger")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router)
app.include_router(tools.router)

@app.get("/health")
def health():
    return {"ok": True}
