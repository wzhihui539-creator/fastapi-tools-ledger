from pydantic import BaseModel, Field
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ToolCreate(BaseModel):
    name: str
    location: str = "unknown"
    quantity: int = 0

class ToolRead(BaseModel):
    id: int
    name: str
    location: str
    quantity: int
    updated_at: datetime

class ToolQuantityUpdate(BaseModel):
    delta: int = Field(..., ge=-100000, le=100000, description="数量变更（可正可负）")

class ToolListItem(BaseModel):
    id: int
    name: str
    location: str | None = None
    quantity: int


class ToolListResponse(BaseModel):
    items: list[ToolListItem]
    total: int
    limit: int
    offset: int
    q: str | None = None
