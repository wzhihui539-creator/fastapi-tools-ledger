from fastapi import HTTPException
from app.schemas import MovementAction


def abort(status_code: int, code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def calc_signed_delta_and_new_qty(
    action: MovementAction, delta: int, old_qty: int
) -> tuple[int, int]:
    # 统一口径：IN/OUT delta>0，ADJUST delta>=0(目标库存)
    if action in (MovementAction.IN, MovementAction.OUT) and delta <= 0:
        abort(400, "INVALID_DELTA", "IN/OUT 的 delta 必须 > 0")

    if action == MovementAction.ADJUST and delta < 0:
        abort(400, "INVALID_DELTA", "ADJUST 的 delta 必须 >= 0（目标库存）")

    if action == MovementAction.IN:
        signed_delta = delta
        new_qty = old_qty + delta
    elif action == MovementAction.OUT:
        signed_delta = -delta
        new_qty = old_qty - delta
    else:  # ADJUST：delta 是目标库存
        new_qty = delta
        signed_delta = new_qty - old_qty

    if new_qty < 0:
        abort(400, "INSUFFICIENT_STOCK", f"库存不足：当前 {old_qty}，要出库 {delta}")

    if signed_delta == 0:
        abort(400, "NO_CHANGE", "数量没有变化，无需提交")

    return signed_delta, new_qty


def build_note(
    action: MovementAction,
    input_delta: int,
    old_qty: int,
    new_qty: int,
    note: str | None,
) -> str:
    note_clean = (note or "").strip()
    if note_clean:
        return note_clean

    if action == MovementAction.IN:
        return f"入库 +{input_delta}（{old_qty}->{new_qty}）"
    if action == MovementAction.OUT:
        return f"出库 {input_delta}（{old_qty}->{new_qty}）"
    # ADJUST：input_delta 是目标库存
    return f"盘点调整为 {input_delta}（{old_qty}->{new_qty}）"
