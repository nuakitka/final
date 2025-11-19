from enum import Enum
from typing import List, Dict, Set, Optional
from functools import wraps
from fastapi import HTTPException, status, Depends
from app.models.user import User
from app.core.security import get_current_user

class Permission(Enum):
    # Book permissions
    READ_BOOKS = "read_books"
    DOWNLOAD_BOOKS = "download_books"
    UPLOAD_BOOKS = "upload_books"
    EDIT_BOOKS = "edit_books"
    DELETE_BOOKS = "delete_books"
    
    # Category permissions
    READ_CATEGORIES = "read_categories"
    EDIT_CATEGORIES = "edit_categories"
    DELETE_CATEGORIES = "delete_categories"
    
    # Author permissions
    READ_AUTHORS = "read_authors"
    EDIT_AUTHORS = "edit_authors"
    DELETE_AUTHORS = "delete_authors"
    
    # Review permissions
    READ_REVIEWS = "read_reviews"
    WRITE_REVIEWS = "write_reviews"
    EDIT_REVIEWS = "edit_reviews"
    DELETE_REVIEWS = "delete_reviews"
    MODERATE_REVIEWS = "moderate_reviews"
    
    # User permissions
    READ_USERS = "read_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    MANAGE_ROLES = "manage_roles"
    
    # System permissions
    VIEW_ADMIN_PANEL = "view_admin_panel"
    MANAGE_SYSTEM = "manage_system"
    VIEW_STATISTICS = "view_statistics"

class Role(Enum):
    GUEST = "guest"
    READER = "reader"
    LIBRARIAN = "librarian"
    ADMIN = "admin"

# Role-based access control matrix
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.GUEST: {
        Permission.READ_BOOKS,
        Permission.READ_CATEGORIES,
        Permission.READ_AUTHORS,
        Permission.READ_REVIEWS,
    },
    
    Role.READER: {
        Permission.READ_BOOKS,
        Permission.DOWNLOAD_BOOKS,
        Permission.READ_CATEGORIES,
        Permission.READ_AUTHORS,
        Permission.READ_REVIEWS,
        Permission.WRITE_REVIEWS,
        Permission.EDIT_REVIEWS,  # Can edit own reviews
        Permission.DELETE_REVIEWS,  # Can delete own reviews
    },
    
    Role.LIBRARIAN: {
        Permission.READ_BOOKS,
        Permission.DOWNLOAD_BOOKS,
        Permission.UPLOAD_BOOKS,
        Permission.EDIT_BOOKS,
        Permission.READ_CATEGORIES,
        Permission.EDIT_CATEGORIES,
        Permission.READ_AUTHORS,
        Permission.EDIT_AUTHORS,
        Permission.READ_REVIEWS,
        Permission.WRITE_REVIEWS,
        Permission.EDIT_REVIEWS,
        Permission.DELETE_REVIEWS,
        Permission.MODERATE_REVIEWS,
        Permission.READ_USERS,
    },
    
    Role.ADMIN: {
        # Admin has all permissions
        Permission.READ_BOOKS,
        Permission.DOWNLOAD_BOOKS,
        Permission.UPLOAD_BOOKS,
        Permission.EDIT_BOOKS,
        Permission.DELETE_BOOKS,
        Permission.READ_CATEGORIES,
        Permission.EDIT_CATEGORIES,
        Permission.DELETE_CATEGORIES,
        Permission.READ_AUTHORS,
        Permission.EDIT_AUTHORS,
        Permission.DELETE_AUTHORS,
        Permission.READ_REVIEWS,
        Permission.WRITE_REVIEWS,
        Permission.EDIT_REVIEWS,
        Permission.DELETE_REVIEWS,
        Permission.MODERATE_REVIEWS,
        Permission.READ_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_ADMIN_PANEL,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_STATISTICS,
    }
}

def get_user_permissions(user: User) -> Set[Permission]:
    """Get all permissions for a user based on their role"""
    role = Role(user.role) if user.role else Role.GUEST
    return ROLE_PERMISSIONS.get(role, set())

def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has a specific permission"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions

def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions"""
    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in permissions)

def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """Check if user has all of the specified permissions"""
    user_permissions = get_user_permissions(user)
    return all(perm in user_permissions for perm in permissions)

def require_permission(permission: Permission):
    """Decorator to require a specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependencies
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {[p.value for p in permissions]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_all_permissions(permissions: List[Permission]):
    """Decorator to require all of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_all_permissions(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"All these permissions required: {[p.value for p in permissions]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: Role):
    """Decorator to require a specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = Role(current_user.role) if current_user.role else Role.GUEST
            if user_role != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_min_role(min_role: Role):
    """Decorator to require at least the specified role"""
    role_hierarchy = {
        Role.GUEST: 0,
        Role.READER: 1,
        Role.LIBRARIAN: 2,
        Role.ADMIN: 3
    }
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = Role(current_user.role) if current_user.role else Role.GUEST
            if role_hierarchy[user_role] < role_hierarchy[min_role]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Minimum role required: {min_role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# FastAPI dependency for checking permissions
def check_permission(permission: Permission):
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        return current_user
    return permission_checker

def check_role(role: Role):
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = Role(current_user.role) if current_user.role else Role.GUEST
        if user_role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}"
            )
        return current_user
    return role_checker

def check_min_role(min_role: Role):
    role_hierarchy = {
        Role.GUEST: 0,
        Role.READER: 1,
        Role.LIBRARIAN: 2,
        Role.ADMIN: 3
    }
    
    def min_role_checker(current_user: User = Depends(get_current_user)):
        user_role = Role(current_user.role) if current_user.role else Role.GUEST
        if role_hierarchy[user_role] < role_hierarchy[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Minimum role required: {min_role.value}"
            )
        return current_user
    return min_role_checker

# Resource ownership checking
def is_owner(user: User, resource_user_id: int) -> bool:
    """Check if user owns the resource"""
    return user.id == resource_user_id

def can_edit_review(user: User, review_user_id: int) -> bool:
    """Check if user can edit a review"""
    return is_owner(user, review_user_id) or has_permission(user, Permission.MODERATE_REVIEWS)

def can_delete_review(user: User, review_user_id: int) -> bool:
    """Check if user can delete a review"""
    return is_owner(user, review_user_id) or has_permission(user, Permission.MODERATE_REVIEWS)

# Utility functions
def get_permissions_for_role(role: Role) -> Set[Permission]:
    """Get all permissions for a role"""
    return ROLE_PERMISSIONS.get(role, set())

def get_all_permissions() -> Set[Permission]:
    """Get all available permissions"""
    all_perms = set()
    for perms in ROLE_PERMISSIONS.values():
        all_perms.update(perms)
    return all_perms

def get_role_hierarchy() -> Dict[Role, int]:
    """Get role hierarchy levels"""
    return {
        Role.GUEST: 0,
        Role.READER: 1,
        Role.LIBRARIAN: 2,
        Role.ADMIN: 3
    }
