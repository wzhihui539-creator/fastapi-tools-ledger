from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.db import get_session
from app.models import Tool, User
from app.schemas import ToolCreate, ToolRead
from app.security import decode_token
from app.schemas import ToolQuantityUpdate

router = APIRouter(prefix="/tools", tags=["tools"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def require_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    try:
        username = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("", response_model=ToolRead)
def create_tool(
    data: ToolCreate,
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    tool = Tool(name=data.name, location=data.location, quantity=data.quantity)
    session.add(tool)
    session.commit()
    session.refresh(tool)
    return tool

@router.get("", response_model=list[ToolRead])
def list_tools(
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    return session.exec(select(Tool).order_by(Tool.id.desc())).all()

@router.get("/{tool_id}", response_model=ToolRead)
def get_tool(
    tool_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Not found")
    return tool

@router.put("/{tool_id}", response_model=ToolRead)
def update_tool(
    tool_id: int,
    data: ToolCreate,
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Not found")
    tool.name = data.name
    tool.location = data.location
    tool.quantity = data.quantity
    session.add(tool)
    session.commit()
    session.refresh(tool)
    return tool

@router.delete("/{tool_id}")
def delete_tool(
    tool_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(tool)
    session.commit()
    return {"ok": True}


@router.patch("/{tool_id}/quantity", response_model=ToolRead)
def update_tool_quantity(
    tool_id: int,
    body: ToolQuantityUpdate,
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Tool not found"})

    tool.quantity += body.delta
    session.add(tool)
    session.commit()
    session.refresh(tool)
    return tool