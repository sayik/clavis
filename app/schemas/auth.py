from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserSignup(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6)


# class UserLogin(BaseModel):
#     username: str = Field(min_length=3, max_length=30)
#     password: str
"""
Currently commented out because signup will be handled by my code 
but the login is handled by fastapi HTTP Basic authentication.
User data will be saved to database with signup endpoint
"""


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class Login(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    created_at: datetime


class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description="The refresh token issued during login.",
    )
    device_id: str = Field(
        ...,
        description="Unique identifier of the client device.",
        max_length=64,
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token issued during login.")
    device_id: str = Field(description="Unique identifier of the client device.")


class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class LogoutResponse(BaseModel):
    message: str
