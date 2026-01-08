from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Tool, User, ToolMovement
from app.schemas import MovementCreate, MovementRead, MovementListResponse

# 复用你现有的 require_user（现在在 tools.py）
from app.routers.tools import require_user

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

    # 小约束：让 delta 和 action 更直观（不想要也可以删掉这段）
    if data.action == "IN" and data.delta <= 0:
        raise HTTPException(status_code=400, detail="IN requires delta > 0")
    if data.action == "OUT" and data.delta >= 0:
        raise HTTPException(status_code=400, detail="OUT requires delta < 0")

    new_qty = tool.quantity + data.delta
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot go below 0")

    tool.quantity = new_qty
    tool.updated_at = __import__("datetime").datetime.utcnow()  # 保持你项目风格：utcnow（无时区）

    mv = ToolMovement(
        tool_id=data.tool_id,
        action=data.action,
        delta=data.delta,
        note=data.note,
        operator=user.username,
    )

    session.add(tool)
    session.add(mv)
    session.commit()
    session.refresh(mv)
    return mv


@router.get("", response_model=MovementListResponse)
def list_movements(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    total = session.exec(select(func.count()).select_from(ToolMovement)).one()
    items = session.exec(
        select(ToolMovement).order_by(ToolMovement.id.desc()).offset(offset).limit(limit)
    ).all()

    return {"items": items, "total": total, "limit": limit, "offset": offset}
