from enum import Enum
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from app.api.auth import get_current_active_user
from app.schemas.user import User

# Определяем роли
class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    LIBRARIAN = "librarian"
    ADMIN = "admin"

# Определяем разрешения
class Permission(str, Enum):
    # Основные разрешения
    VIEW_BOOKS = "view_books"
    READ_BOOKS = "read_books"
    
    # Управление контентом
    WRITE_REVIEWS = "write_reviews"
    UPLOAD_BOOKS = "upload_books"
    EDIT_BOOKS = "edit_books"
    DELETE_BOOKS = "delete_books"
    
    # Административные
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"

# Карта ролей и их разрешений
ROLE_PERMISSIONS = {
    Role.GUEST: [
        Permission.VIEW_BOOKS,
    ],
    Role.READER: [
        Permission.VIEW_BOOKS,
        Permission.READ_BOOKS,
        Permission.WRITE_REVIEWS,
    ],
    Role.LIBRARIAN: [
        Permission.VIEW_BOOKS,
        Permission.READ_BOOKS,
        Permission.WRITE_REVIEWS,
        Permission.UPLOAD_BOOKS,
        Permission.EDIT_BOOKS,
    ],
    Role.ADMIN: [
        Permission.VIEW_BOOKS,
        Permission.READ_BOOKS,
        Permission.WRITE_REVIEWS,
        Permission.UPLOAD_BOOKS,
        Permission.EDIT_BOOKS,
        Permission.DELETE_BOOKS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_SYSTEM,
    ],
}

def get_user_permissions(user: Optional[User]) -> List[Permission]:
    """Получает список разрешений пользователя"""
    if not user:
        # Если пользователь не авторизован, возвращаем разрешения гостя
        return ROLE_PERMISSIONS[Role.GUEST]
    
    try:
        role = Role(user.role) if user.role else Role.GUEST
        return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS[Role.GUEST])
    except (ValueError, AttributeError):
        # Если роль неизвестна, возвращаем разрешения гостя
        return ROLE_PERMISSIONS[Role.GUEST]

def has_permission(user: Optional[User], permission: Permission) -> bool:
    """Проверяет, есть ли у пользователя указанное разрешение"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions

def check_permission(permission: Permission):
    """Dependency для проверки разрешений с улучшенной обработкой ошибок"""
    async def permission_checker(
        current_user: Optional[User] = Depends(get_current_active_user)
    ) -> User:
        # Если пользователь не найден, вызываем исключение
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Не авторизован"
            )
        
        # Проверяем разрешение
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется разрешение: {permission.value}"
            )
        
        return current_user
    
    return permission_checker