import pytest
from .conftest import client


from app.db.init_db import get_db
from app.auth.password_handler import get_password_hash, verify_password
from app.db.models import User, RefreshToken
from app.schemas.auth import UserOut
from app.auth.token_handler import decode_token, hash_token

test_user = UserOut(
    id="1",
    username="test",
    email="test@example.com",
    created_at="2026-09-27 18:10:19.954582",
    password_hash="newpassword",
)


def test_password_hashing():
    password = "asf@2356.sawrA"
    password_hash = get_password_hash(password)

    assert password_hash != password
    assert password_hash


def test_correct_password_matching():
    password_hash = get_password_hash("asf@2356.sawrA")
    assert verify_password("asf@2356.sawrA", password_hash)


def test_wrong_password_matching():
    password_hash = get_password_hash("asf@2356.sawrA")
    assert not verify_password("asf@2356.swrA", password_hash)


def test_get_user(client):
    response = client.get("/auth/me")
    print(response.json())
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_success(client):
    password = "test-password"

    user = User(
        username="test",
        email="test@example.com",
        password_hash=get_password_hash(password),
        email_verified=True,
    )

    get_db.add(user)
    await get_db.commit()
    await get_db.refresh(user)

    response = client.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": password,
            "device_id": "test-device",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"]
    assert data["refresh_token"]


def test_validate_user_signup():
    pass


def test_login():
    pass


def test_signout():
    pass


def test_verification_email():
    pass


def test_register():
    pass


def test_refresh_token():
    pass
