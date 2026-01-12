from zoneinfo import ZoneInfo
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select
from app.db import get_session
from app.models import Tool, User, ToolMovement
from app.schemas import MovementCreate, MovementRead, MovementListResponse, MovementAction, MovementSort
from app.services.ledger import calc_signed_delta_and_new_qty, build_note, abort
from datetime import datetime, date, timedelta, timezone

def _get_zone(tz_str: Optional[str]) -> Optional[ZoneInfo]:
    if not tz_str:
        return None
    tz_str = tz_str.strip()
    if not tz_str:
        return None
    try:
        return ZoneInfo(tz_str)
    except Exception:
        abort(400, "BAD_REQUEST", f"tz 不合法：{tz_str}（例：Asia/Shanghai / Asia/Tokyo / UTC）")


def _parse_dt_or_date(s: str, *, is_end: bool, assume_tz: Optional[ZoneInfo]) -> datetime:
    """
    支持:
      - "YYYY-MM-DD"
      - ISO datetime: "YYYY-MM-DDTHH:MM:SS", "YYYY-MM-DDTHH:MM:SSZ", "YYYY-MM-DDTHH:MM:SS+08:00"
    规则:
      - 日期: start=当地00:00:00, end=次日00:00:00 (左闭右开)
      - datetime: 原样解释
      - 若输入不带时区: 使用 assume_tz；若 assume_tz 也没有，则按 UTC
      - 最终返回 UTC-naive（匹配你 DB 里的 utcnow() naive）
    """
    s = (s or "").strip()
    if not s:
        abort(400, "BAD_REQUEST", "start/end 不能为空")

    # 1) 纯日期
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        try:
            d = date.fromisoformat(s)
        except ValueError:
            abort(400, "BAD_REQUEST", f"日期格式错误：{s}，应为 YYYY-MM-DD")

        local_dt = datetime(d.year, d.month, d.day)
        if is_end:
            local_dt = local_dt + timedelta(days=1)

        # 给日期补时区（若没提供 tz，则按 UTC）
        tz = assume_tz or timezone.utc
        local_dt = local_dt.replace(tzinfo=tz)

        # 转 UTC -> 去 tzinfo
        return local_dt.astimezone(timezone.utc).replace(tzinfo=None)

    # 2) datetime（兼容 Z）
    try:
        iso = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
    except ValueError:
        abort(400, "BAD_REQUEST", f"时间格式错误：{s}，例：2026-01-12T08:30:00 或 2026-01-12T08:30:00Z")

    # 如果输入不带时区，就用 tz 参数；否则尊重输入自己的时区
    if dt.tzinfo is None:
        tz = assume_tz or timezone.utc
        dt = dt.replace(tzinfo=tz)

    # 转 UTC -> 去 tzinfo
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


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
        action=data.action.value,  # Enum -> str
        delta=signed_delta,  # ✅ 永远存“真实变化量”
        note=note,
        operator=user.username,
    )

    session.add(tool)
    session.add(mv)
    session.commit()
    session.refresh(mv)
    return mv


@router.get("", response_model=MovementListResponse)
def list_movements(
    tool_id: Optional[int] = Query(None, ge=1, description="按刀具ID过滤（可选）"),
    action: Optional[MovementAction] = Query(None, description="按动作过滤（可选）"),
    operator: Optional[str] = Query(None, min_length=1, max_length=50, description="按操作人过滤（可选）"),
    tz: Optional[str] = Query(None,
                              description="时区（可选）。例：Asia/Shanghai / Asia/Tokyo / UTC。若 start/end 不带时区则按该时区解释"),
    start: Optional[str] = Query(None, description="开始时间/日期。例：2026-01-12 或 2026-01-12T08:30:00（可配 tz）"),
    end: Optional[str] = Query(None, description="结束时间/日期（左闭右开）。例：2026-01-13 或 2026-01-12T20:00:00（可配 tz）"),
    sort: MovementSort = Query(MovementSort.id_desc, description="排序方式（可选）"),
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
        stmt = stmt.where(ToolMovement.action == action.value)
        count_stmt = count_stmt.where(ToolMovement.action == action.value)

    if operator is not None:
        op = operator.strip()
        if op:
            stmt = stmt.where(ToolMovement.operator == op)
            count_stmt = count_stmt.where(ToolMovement.operator == op)
    zone = _get_zone(tz)

    start_dt = None
    end_dt = None

    if start:
        start_dt = _parse_dt_or_date(start, is_end=False, assume_tz=zone)
        stmt = stmt.where(ToolMovement.created_at >= start_dt)
        count_stmt = count_stmt.where(ToolMovement.created_at >= start_dt)

    if end:
        end_dt = _parse_dt_or_date(end, is_end=True, assume_tz=zone)
        stmt = stmt.where(ToolMovement.created_at < end_dt)
        count_stmt = count_stmt.where(ToolMovement.created_at < end_dt)

    if start_dt is not None and end_dt is not None and start_dt >= end_dt:
        abort(400, "BAD_REQUEST", "start 必须早于 end")

    # ✅ sort: 统一入口切换 order_by
    if sort == MovementSort.id_desc:
        stmt = stmt.order_by(ToolMovement.id.desc())
    elif sort == MovementSort.id_asc:
        stmt = stmt.order_by(ToolMovement.id.asc())
    elif sort == MovementSort.created_desc:
        stmt = stmt.order_by(ToolMovement.created_at.desc(), ToolMovement.id.desc())
    elif sort == MovementSort.created_asc:
        stmt = stmt.order_by(ToolMovement.created_at.asc(), ToolMovement.id.asc())

    total = session.exec(count_stmt).one()
    items = session.exec(stmt.offset(offset).limit(limit)).all()

    return {"items": items, "total": total, "limit": limit, "offset": offset}