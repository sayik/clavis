import pytest
from .conftest import client

from app.auth.password_handler import get_password_hash, verify_password
from app.db.models import User
from app.schemas.auth import UserOut

test_user = UserOut(
    id="1",
    username="test",
    email="test@example.com",
    created_at="2026-09-27 18:10:19.954582",
    password_hash="newpassword",
)


def test_password_hashing():
    assert get_password_hash("asf@2356.sawrA")


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
