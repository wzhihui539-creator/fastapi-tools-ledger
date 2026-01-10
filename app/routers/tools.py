from datetime import datetime
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from fastapi.responses import Response
from sqlalchemy import func, or_
from app.db import get_session
from app.models import Tool, User, ToolMovement
from app.schemas import ToolCreate, ToolRead, ToolListResponse
from app.schemas import ToolQuantityUpdate
from app.schemas import ToolListItem
from app.deps import require_user
from urllib.parse import quote


router = APIRouter(prefix="/tools", tags=["tools"])


from app.models import Tool, ToolMovement, User  # 确保引入 ToolMovement

@router.post("", response_model=ToolRead)
def create_tool(
        data: ToolCreate,
        session: Session = Depends(get_session),
        _user: User = Depends(require_user),
):
    tool = Tool(
        name=data.name,
        location=data.location,
        quantity=data.quantity,
    )
    session.add(tool)

    # ✅ flush 让 tool.id 生成，但不提交
    session.flush()

    # ✅ 新建即入库：写一条流水
    mv = ToolMovement(
        tool_id=tool.id,
        action="IN",
        delta=tool.quantity,
        note="新建入库",
        operator=_user.username,
    )
    session.add(mv)

    # ✅ 一次提交，保证原子性
    session.commit()

    session.refresh(tool)
    return tool



@router.get("", response_model=ToolListResponse)
def list_tools(
        q: str | None = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        sort: str = Query(
            "id_desc",
            description="排序：id_desc/id_asc/name_asc/name_desc/qty_asc/qty_desc",
        ),
        session: Session = Depends(get_session),
        _user: User = Depends(require_user),
):
    conds = []
    if q:
        conds.append(or_(Tool.name.contains(q), Tool.location.contains(q)))

    # total
    count_stmt = select(func.count()).select_from(Tool)
    if conds:
        count_stmt = count_stmt.where(*conds)
    total = session.exec(count_stmt).one()

    # order by
    order_map = {
        "id_desc": Tool.id.desc(),
        "id_asc": Tool.id.asc(),
        "name_asc": Tool.name.asc(),
        "name_desc": Tool.name.desc(),
        "qty_asc": Tool.quantity.asc(),
        "qty_desc": Tool.quantity.desc(),
    }
    order_by = order_map.get(sort, Tool.id.desc())

    # items
    items_stmt = select(Tool)
    if conds:
        items_stmt = items_stmt.where(*conds)

    items = session.exec(items_stmt.order_by(order_by).offset(offset).limit(limit)).all()

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "q": q,
    }


@router.get("/lite", response_model=list[ToolListItem])
def list_tools_lite(
        session: Session = Depends(get_session),
        _user: User = Depends(require_user),
):
    stmt = select(Tool).order_by(Tool.id.desc())
    return session.exec(stmt).all()


30
@router.get("/export.csv")
def export_tools_csv(
        q: str | None = None,  # ✅ 可选：按关键词导出
        session: Session = Depends(get_session),
        _user: User = Depends(require_user),
):
    stmt = select(Tool).order_by(Tool.id.asc())
    if q:
        stmt = stmt.where(
            or_(
                Tool.name.contains(q),
                Tool.location.contains(q),
            )
        )
    tools = session.exec(stmt).all()

    # 英文字段（取值）
    fields = ["id", "name", "location", "quantity", "vendor", "model", "remark", "updated_at"]
    # 中文表头（显示）
    header_cn = ["编号", "名称", "库位", "数量", "品牌", "型号", "备注", "更新时间"]

    def norm_str(v, default: str) -> str:
        if v is None:
            return default
        s = str(v).strip()
        return s if s else default

    def norm_int(v, default: int = 0) -> int:
        if v is None:
            return default
        try:
            return int(v)
        except Exception:
            return default

    def norm_dt(v) -> str:
        if v is None:
            return ""
        if hasattr(v, "isoformat"):
            return v.isoformat(sep=" ", timespec="seconds")
        return str(v)

    buf = io.StringIO(newline="")
    writer = csv.writer(buf)

    # ✅ 第一行：中文列名
    writer.writerow(header_cn)

    for t in tools:
        d = t.model_dump()
        row = []
        row.append(norm_int(d.get("id"), 0))  # 编号
        row.append(norm_str(d.get("name"), "未命名"))  # 名称
        row.append(norm_str(d.get("location"), "未知"))  # 库位
        row.append(norm_int(d.get("quantity"), 0))  # 数量
        row.append(norm_str(d.get("vendor"), ""))  # 品牌
        row.append(norm_str(d.get("model"), ""))  # 型号
        row.append(norm_str(d.get("remark"), ""))  # 备注
        row.append(norm_dt(d.get("updated_at")))  # 更新时间
        writer.writerow(row)

    # ✅ 最后一行：导出时间（可选，本地化小彩蛋，不影响Excel读）
    writer.writerow([])
    writer.writerow(["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    cn_filename = "刀具台账.csv"
    quoted = quote(cn_filename)
    headers = {
        # 兜底（给不支持 filename* 的客户端）
        "Content-Disposition": f"attachment; filename=\"tools.csv\"; filename*=UTF-8''{quoted}"
    }
    csv_bytes = buf.getvalue().encode("utf-8-sig")  # ✅ Excel 打开中文不乱码
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


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
    # 查询资源：session.get(Tool, tool_id)
    # 通过 tool_id 从数据库中查询 Tool 模型对应的记录（get 方法按主键查询，效率高于 filter）
    if not tool:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(tool)
    session.commit()
    return {"ok": True}


from datetime import datetime
from app.models import ToolMovement

@router.patch("/{tool_id}/quantity", response_model=ToolRead)
def update_tool_quantity(
        tool_id: int,
        body: ToolQuantityUpdate,
        session: Session = Depends(get_session),
        user: User = Depends(require_user),
):
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Tool not found"})

    if body.delta == 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "BAD_REQUEST", "message": "delta cannot be 0"},
        )

    old_qty = tool.quantity
    new_qty = old_qty + body.delta
    if new_qty < 0:
        raise HTTPException(status_code=400, detail={"code": "BAD_REQUEST", "message": "Quantity cannot go below 0"})

    # action：根据 delta 自动推断
    if body.delta > 0:
        action = "IN"
    elif body.delta < 0:
        action = "OUT"
    # 写这条只是为了看着更直观，永远不会出现，前边被拦住了，如果delta=0会被拦住400报警
    else:
        action = "ADJUST"

    # note：你没填就自动生成一条“台账风格”的备注
    note = (body.note or "").strip()
    if not note:
        if action == "IN":
            note = f"入库 +{body.delta}（{old_qty}->{new_qty}）"
        elif action == "OUT":
            note = f"出库 {body.delta}（{old_qty}->{new_qty}）"  # delta 本身是负数，直观看
        else:
            note = f"盘点调整（{old_qty}->{new_qty}）"

    tool.quantity = new_qty
    tool.updated_at = datetime.utcnow()

    mv = ToolMovement(
        tool_id=tool_id,
        action=action,
        delta=body.delta,
        note=note,
        operator=user.username,
    )

    session.add(tool)
    session.add(mv)
    session.commit()
    session.refresh(tool)
    return tool



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