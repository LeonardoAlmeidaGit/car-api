from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSchema(BaseModel):
    username: str = Field(max_length=30)
    email: EmailStr
    password: str

    @field_validator('username')
    def username_min_length(cls, v):
        if len(v) < 5:
            raise ValueError('Username deve ter pelo menos 5 caracteres')
        return v

    @field_validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        return v


class UserPublicSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class UserUpdateSchema(BaseModel):
    username: Optional[str] = Field(default=None, max_length=30)
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @field_validator('username')
    def username_min_length(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError('Username deve ter pelo menos 5 caracteres')
        return v

    @field_validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        return v


class UserListPublicSchema(BaseModel):
    users: List[UserPublicSchema]
    offset: int
    limit: int
