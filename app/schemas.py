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

class MovementSort(str, Enum):
    id_desc = "id_desc"
    id_asc = "id_asc"
    created_desc = "created_desc"
    created_asc = "created_asc"


class ToolQuantityUpdate(BaseModel):
    action: MovementAction = Field(..., description="IN/OUT/ADJUST")
    delta: int = Field(..., ge=0, le=100000, description="IN/OUT=变更量(>0)，ADJUST=目标库存(>=0)")
    note: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"action": "IN", "delta": 5, "note": "入库5"},
                {"action": "OUT", "delta": 3, "note": "出库3"},
                {"action": "ADJUST", "delta": 0, "note": "清点归零"},
            ]
        }
    }


class MovementListResponse(BaseModel):
    items: list[MovementRead]
    total: int
    limit: int
    offset: int
