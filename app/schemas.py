from typing import Optional
from enum import Enum
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
    note: str | None = Field(default=None, description="备注：变更原因（可选）")


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


class MovementAction(str, Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"


class MovementCreate(BaseModel):
    tool_id: int
    action: MovementAction
    delta: int
    note: Optional[str] = None


class MovementRead(BaseModel):
    id: int
    tool_id: int
    action: MovementAction
    delta: int
    note: Optional[str] = None
    operator: str
    created_at: datetime


class MovementListResponse(BaseModel):
    items: list[MovementRead]
    total: int
    limit: int
    offset: int