from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserUpdate
from app.core.security import verify_password, get_password_hash, create_access_token
from datetime import timedelta  
from app.core.config import settings
from typing import List, Optional

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    # Проверяем, есть ли уже пользователи в системе
    total_users = db.query(User).count()
    
    # Первый пользователь становится администратором
    user_role = "admin" if total_users == 0 else "reader"
    
    # Check if user already exists
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user_role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Логируем роль
    if user_role == "admin":
        print(f"✅ Первый пользователь создан как администратор: {user.username}")
    else:
        print(f"✅ Новый пользователь создан как читатель: {user.username}")
    
    return db_user

def authenticate_user(db: Session, user_login: UserLogin) -> Optional[User]:
    """Аутентификация пользователя с обработкой ошибок"""
    user = get_user_by_username(db, user_login.username)
    if not user:
        print(f"Пользователь не найден: {user_login.username}")
        return None
    
    try:
        # Пробуем проверить пароль
        if verify_password(user_login.password, user.hashed_password):
            print(f"Пароль верный для пользователя: {user.username}")
            return user
        else:
            print(f"Неверный пароль для пользователя: {user.username}")
            return None
    except Exception as e:
        print(f"Ошибка при проверке пароля для пользователя {user.username}: {e}")
        return None

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Получить список пользователей"""
    return db.query(User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    return db.query(User).filter(User.id == user_id).first()

def update_user(db: Session, user_id: int, user_update: dict) -> Optional[User]:
    """Обновить пользователя"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Не позволяем изменять пароль через эту функцию
    if "password" in user_update:
        user_update.pop("password")
    
    for field, value in user_update.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """Удалить пользователя"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Получить пользователя по ID (альтернативная версия)"""
    return db.query(User).filter(User.id == user_id).first()

def login_user(db: Session, user_login: UserLogin) -> dict:
    """Логин пользователя"""
    print(f"Попытка входа пользователя: {user_login.username}")
    
    user = authenticate_user(db, user_login)
    if not user:
        print(f"Аутентификация не удалась для: {user_login.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        print(f"Пользователь неактивен: {user_login.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен"
        )
    
    print(f"Пользователь успешно аутентифицирован: {user.username}")
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    # Создаем токен
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "user_id": user.id,
            "email": user.email
        }, 
        expires_delta=access_token_expires
    )
    
    print(f"Создан токен для пользователя: {user.username}")
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }