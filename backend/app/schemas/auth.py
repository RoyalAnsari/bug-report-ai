import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Role = Literal["admin", "reviewer"]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(value):
    value = value.strip().lower()
    if len(value) > 254 or not EMAIL_PATTERN.match(value):
        raise ValueError("Enter a valid email address")
    return value


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value):
        return clean_email(value)


class UserCreate(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(min_length=1, max_length=100)
    role: Role = "reviewer"
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value):
        return clean_email(value)

    @field_validator("name")
    @classmethod
    def name_ok(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    role: Role | None = None
    is_active: bool | None = None


class PasswordSet(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    is_active: bool
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class MeOut(BaseModel):
    id: str
    email: str
    name: str
    role: Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class AuthConfig(BaseModel):
    auth_enabled: bool
