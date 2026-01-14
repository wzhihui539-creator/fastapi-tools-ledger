def _token(client):
    client.post("/auth/register", json={"username": "u1", "password": "p1"})
    r = client.post("/auth/login", data={"username": "u1", "password": "p1"})
    return r.json()["access_token"]

def _h(token: str):
    return {"Authorization": f"Bearer {token}"}

def test_create_tool_and_list(client):
    token = _token(client)

    r = client.post("/tools", json={"name": "麻花钻", "location": "A1", "quantity": 5}, headers=_h(token))
    assert r.status_code == 200
    tool = r.json()
    assert tool["name"] == "麻花钻"
    assert tool["quantity"] == 5

    r2 = client.get("/tools?limit=50&offset=0&sort=id_desc", headers=_h(token))
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

def test_update_quantity_in_out_adjust(client):
    token = _token(client)
    h = _h(token)

    r = client.post("/tools", json={"name": "丝锥", "location": "B2", "quantity": 0}, headers=h)
    tool_id = r.json()["id"]

    r = client.patch(f"/tools/{tool_id}/quantity", json={"action": "IN", "delta": 10}, headers=h)
    assert r.status_code == 200
    assert r.json()["quantity"] == 10

    r = client.patch(f"/tools/{tool_id}/quantity", json={"action": "OUT", "delta": 3}, headers=h)
    assert r.status_code == 200
    assert r.json()["quantity"] == 7

    r = client.patch(f"/tools/{tool_id}/quantity", json={"action": "ADJUST", "delta": 20}, headers=h)
    assert r.status_code == 200
    assert r.json()["quantity"] == 20

def test_out_not_enough_stock(client):
    token = _token(client)
    h = _h(token)

    r = client.post("/tools", json={"name": "铣刀", "location": "C1", "quantity": 2}, headers=h)
    tool_id = r.json()["id"]

    r2 = client.patch(f"/tools/{tool_id}/quantity", json={"action": "OUT", "delta": 999}, headers=h)
    assert r2.status_code == 400
