def test_register_and_login(client):
    r = client.post("/auth/register", json={"username": "neil", "password": "neil456"})
    assert r.status_code in (200, 201)
    assert r.json() == {"ok": True}

    r2 = client.post("/auth/login", data={"username": "neil", "password": "neil456"})
    assert r2.status_code == 200
    data = r2.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_user(client):
    r1 = client.post("/auth/register", json={"username": "dup", "password": "p"})
    assert r1.status_code in (200, 201)

    r2 = client.post("/auth/register", json={"username": "dup", "password": "p"})
    assert r2.status_code == 409
    assert r2.json() == {
        "detail": {"code": "USERNAME_EXISTS", "message": "用户名已存在"}
    }


def test_login_invalid_credentials(client):
    r = client.post("/auth/login", data={"username": "nope", "password": "wrong"})
    assert r.status_code == 401
    assert r.json() == {
        "detail": {"code": "INVALID_CREDENTIALS", "message": "用户名或密码错误"}
    }
