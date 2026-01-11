from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Tool, User, ToolMovement
from app.schemas import MovementCreate, MovementRead, MovementListResponse, MovementAction


from app.deps import require_user

router = APIRouter(prefix="/movements", tags=["movements"])


@router.post("", response_model=MovementRead)
def create_movement(
    data: MovementCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user),
):
    tool = session.get(Tool, data.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    # 规则校验：用 Enum 比较
    if data.action in (MovementAction.IN, MovementAction.OUT) and data.delta <= 0:
        raise HTTPException(status_code=400, detail="delta must be > 0")

    if data.action == MovementAction.ADJUST and data.delta == 0:
        raise HTTPException(status_code=400, detail="ADJUST requires delta != 0")

    if data.action == MovementAction.IN:
        signed_delta = data.delta
    elif data.action == MovementAction.OUT:
        signed_delta = -data.delta
    else:
        signed_delta = data.delta

    tool.quantity += signed_delta
    if tool.quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    mv = ToolMovement(
        tool_id=tool.id,
        action=data.action.value,   # ✅ Enum -> str 入库
        delta=signed_delta,   # ✅ 这里必须是 signed_delta
        note=data.note,
        operator=user.username,
    )

    session.add(tool)
    session.add(mv)
    session.commit()
    session.refresh(mv)
    return mv


@router.get("", response_model=MovementListResponse)
@router.get("", response_model=MovementListResponse)
def list_movements(
    tool_id: int | None = None,
    action: MovementAction | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    stmt = select(ToolMovement)
    count_stmt = select(func.count()).select_from(ToolMovement)

    if tool_id is not None:
        stmt = stmt.where(ToolMovement.tool_id == tool_id)
        count_stmt = count_stmt.where(ToolMovement.tool_id == tool_id)

    if action is not None:
        stmt = stmt.where(ToolMovement.action == action.value)         # ✅ Enum -> str
        count_stmt = count_stmt.where(ToolMovement.action == action.value)

    total = session.exec(count_stmt).one()
    items = session.exec(
        stmt.order_by(ToolMovement.id.desc()).offset(offset).limit(limit)
    ).all()

    return {"items": items, "total": total, "limit": limit, "offset": offset}


