from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import get_db
from app.schemas.user import User, UserUpdate
from app.services.auth import get_user_by_username
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Only admins can view all users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # This would need to be implemented in the service layer
    # For now, returning empty list as placeholder
    return []


@router.get("/{username}", response_model=User)
def read_user(
    username: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Users can only view their own profile unless they're admin
    if current_user.username != username and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{username}", response_model=User)
def update_user(
    username: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Users can only update their own profile unless they're admin
    if current_user.username != username and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only admins can change roles
    if user_update.role and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions to change role")
    
    # Update user fields (this would need to be implemented in service layer)
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user
