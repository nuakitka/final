from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import get_db
from app.schemas.user import User, UserUpdate
from app.schemas.book import Book
from app.services.auth import get_user_by_username, get_users
from app.services.book import get_book
from app.services.user_stats import get_user_reading_stats, get_user_reading_sessions

router = APIRouter(tags=["users"])

# Простая проверка аутентификации через request.state.user
def get_current_user_from_request(request: Request):
    """Получить текущего пользователя из request.state.user"""
    user = request.state.user
    if not user or not user.get("is_authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован"
        )
    return user

# Проверка активного пользователя
def get_current_active_user(request: Request):
    """Получить текущего активного пользователя"""
    user = get_current_user_from_request(request)
    
    # Здесь можно добавить проверку is_active, если есть в данных
    # if not user.get("is_active", True):
    #     raise HTTPException(status_code=400, detail="Пользователь неактивен")
    
    return user

@router.get("/me/stats")
def get_my_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить статистику чтения текущего пользователя"""
    user = get_current_active_user(request)
    
    # Получаем объект пользователя из базы
    user_obj = get_user_by_username(db, user.get("username"))
    if not user_obj:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return get_user_reading_stats(db, user_obj.id)

@router.get("/me/reading-sessions")
def get_my_reading_sessions(
    request: Request,
    active: bool = Query(False, description="Только активные сессии"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Получить сессии чтения текущего пользователя"""
    user = get_current_active_user(request)
    
    # Получаем объект пользователя из базы
    user_obj = get_user_by_username(db, user.get("username"))
    if not user_obj:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    sessions = get_user_reading_sessions(db, user_obj.id, active_only=active)
    
    # Применяем пагинацию
    paginated_sessions = sessions[skip:skip + limit]
    
    return {
        "sessions": paginated_sessions,
        "total": len(sessions),
        "skip": skip,
        "limit": limit
    }

@router.get("/", response_model=List[User])
def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей (админ)"""
    user = get_current_active_user(request)
    
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    
    return get_users(db, skip=skip, limit=limit)


@router.get("/me/favorites", response_model=List[Book])
def get_my_favorites(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить избранные книги текущего пользователя"""
    user = get_current_active_user(request)

    user_obj = get_user_by_username(db, user.get("username"))
    if not user_obj:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # user_obj.favorites уже содержит связанные книги
    return user_obj.favorites


@router.post("/me/favorites/{book_id}", response_model=Book)
def add_favorite_book(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Добавить книгу в избранное текущего пользователя"""
    user = get_current_active_user(request)

    user_obj = get_user_by_username(db, user.get("username"))
    if not user_obj:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    book = get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    if book not in user_obj.favorites:
        user_obj.favorites.append(book)
        db.commit()
        db.refresh(user_obj)

    return book


@router.delete("/me/favorites/{book_id}")
def remove_favorite_book(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Удалить книгу из избранного текущего пользователя"""
    user = get_current_active_user(request)

    user_obj = get_user_by_username(db, user.get("username"))
    if not user_obj:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Удаляем книгу из списка избранного, если она там есть
    user_obj.favorites = [b for b in user_obj.favorites if b.id != book_id]
    db.commit()
    db.refresh(user_obj)

    return {"detail": "Книга удалена из избранного"}

@router.get("/{username}", response_model=User)
def read_user(
    username: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить профиль пользователя"""
    current_user = get_current_active_user(request)
    
    # Проверяем права
    is_self = current_user.get("username") == username
    has_read_other_perm = current_user.get("role") in ["admin", "librarian"]
    
    if not is_self and not has_read_other_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра других профилей"
        )
    
    user_obj = get_user_by_username(db, username)
    if user_obj is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user_obj

@router.put("/{username}", response_model=User)
def update_user(
    username: str,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновить профиль пользователя"""
    current_user = get_current_active_user(request)
    
    is_self = current_user.get("username") == username
    has_edit_perm = current_user.get("role") == "admin"
    
    # 1. Проверяем права на обновление
    if not is_self and not has_edit_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления этого пользователя"
        )
    
    user_obj = get_user_by_username(db, username)
    if user_obj is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # 2. Проверяем права на изменение роли
    if user_update.role is not None:
        if not has_edit_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администраторы могут изменять роли"
            )
        
        # Предотвращаем изменение своей собственной роли
        if is_self and user_update.role != current_user.get("role"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Администраторы не могут изменять свою собственную роль"
            )
    
    # Обновляем поля
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user_obj, field):
            setattr(user_obj, field, value)
    
    db.commit()
    db.refresh(user_obj)
    
    return user_obj