from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class UserRole(StrEnum):
    """用户角色枚举：student / tech / admin。"""

    STUDENT = "student"
    TECH = "tech"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    username: str
    password: str


class User(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: int
    username: str
    display_name: str
    role: str


class TokenResponse(BaseModel):
    token: str
    user: User
