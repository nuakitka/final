# app/schemas/user.py

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    username: str
    email: str  # Изменили EmailStr на str для гибкости
    full_name: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Упрощенная валидация email
        if not v:
            raise ValueError('Email is required')
        if '@' not in v:
            raise ValueError('Invalid email format')
        # Удаляем пробелы и приводим к нижнему регистру
        v = v.strip().lower()
        return v


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None  # Здесь тоже меняем на str
    full_name: Optional[str] = None
    role: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None:
            return v
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.strip().lower()


class User(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None