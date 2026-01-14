def _token(client):
    client.post("/auth/register", json={"username": "u2", "password": "p2"})
    r = client.post("/auth/login", data={"username": "u2", "password": "p2"})
    return r.json()["access_token"]

def test_list_movements(client):
    token = _token(client)
    h = {"Authorization": f"Bearer {token}"}

    # 新建一个刀具，quantity>0 会产生一条入库流水（按你当前逻辑）
    r = client.post("/tools", json={"name": "钻头", "location": "D1", "quantity": 3}, headers=h)
    assert r.status_code == 200

    r2 = client.get("/movements?limit=50&offset=0&sort=id_desc", headers=h)
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
