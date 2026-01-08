from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str

class Tool(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    location: str = Field(default="unknown")
    quantity: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



class ToolMovement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    tool_id: int = Field(foreign_key="tool.id", index=True)

    action: str = Field(index=True)   # IN / OUT / ADJUST
    delta: int                        # +10 / -3

    note: Optional[str] = None
    operator: str = Field(index=True) # username

    created_at: datetime = Field(default_factory=datetime.utcnow)
