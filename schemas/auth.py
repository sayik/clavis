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


class UserOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    created_at: datetime
