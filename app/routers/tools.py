from datetime import datetime
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from fastapi.responses import Response
from sqlalchemy import or_
from app.db import get_session
from app.models import Tool, User
from app.schemas import ToolCreate, ToolRead
from app.security import decode_token
from app.schemas import ToolQuantityUpdate
from app.schemas import ToolListItem



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



@router.get("/lite", response_model=list[ToolListItem])
def list_tools_lite(
    session: Session = Depends(get_session),
    _user: User = Depends(require_user),
):
    stmt = select(Tool).order_by(Tool.id.desc())
    return session.exec(stmt).all()


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
                Tool.vendor.contains(q),
                Tool.model.contains(q),
                Tool.remark.contains(q),
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
        row.append(norm_int(d.get("id"), 0))                      # 编号
        row.append(norm_str(d.get("name"), "未命名"))              # 名称
        row.append(norm_str(d.get("location"), "未知"))            # 库位
        row.append(norm_int(d.get("quantity"), 0))                 # 数量
        row.append(norm_str(d.get("vendor"), ""))                  # 品牌
        row.append(norm_str(d.get("model"), ""))                   # 型号
        row.append(norm_str(d.get("remark"), ""))                  # 备注
        row.append(norm_dt(d.get("updated_at")))                   # 更新时间
        writer.writerow(row)

    # ✅ 最后一行：导出时间（可选，本地化小彩蛋，不影响Excel读）
    writer.writerow([])
    writer.writerow(["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    csv_bytes = buf.getvalue().encode("utf-8-sig")  # ✅ Excel 打开中文不乱码
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="刀具台账.csv"'},
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

