from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select
from datetime import datetime
from app.db import get_session
from app.models import Tool, User, ToolMovement
from app.schemas import MovementCreate, MovementRead, MovementListResponse, MovementAction
from app.services.ledger import calc_signed_delta_and_new_qty, build_note, abort

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
        abort(404, "NOT_FOUND", "Tool not found")

    old_qty = tool.quantity
    signed_delta, new_qty = calc_signed_delta_and_new_qty(data.action, data.delta, old_qty)

    tool.quantity = new_qty
    tool.updated_at = datetime.utcnow()

    note = build_note(data.action, data.delta, old_qty, new_qty, data.note)

    mv = ToolMovement(
        tool_id=tool.id,
        action=data.action.value,   # Enum -> str
        delta=signed_delta,         # ✅ 永远存“真实变化量”
        note=note,
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
        stmt = stmt.where(ToolMovement.action == action.value)  # ✅ Enum -> str
        count_stmt = count_stmt.where(ToolMovement.action == action.value)

    total = session.exec(count_stmt).one()
    items = session.exec(
        stmt.order_by(ToolMovement.id.desc()).offset(offset).limit(limit)
    ).all()

    return {"items": items, "total": total, "limit": limit, "offset": offset}
