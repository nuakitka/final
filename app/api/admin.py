from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from app.models import get_db
from app.schemas.user import User
from app.schemas.book import Book, BookCreate, BookUpdate
from app.services.book import get_books, create_book, update_book, delete_book
from app.services.auth import get_users
from app.models.user import User as UserModel
from app.models.book import Book as BookModel, Review, ReadingSession

router = APIRouter(tags=["admin"])

# Простая проверка через request.state.user
def check_admin(request: Request):
    """Упрощенная проверка администратора"""
    user = request.state.user
    print(f"🔍 Проверка администратора: user={user}")
    
    if not user or not user.get("is_authenticated"):
        print("❌ Пользователь не авторизован")
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    if user.get("role") != "admin":
        print(f"❌ Недостаточно прав. Роль: {user.get('role')}")
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    
    print(f"✅ Администратор подтвержден: {user.get('username')}")
    return True

@router.get("/stats")
def admin_get_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить статистику системы (админ)"""
    check_admin(request)
    
    total_users = db.query(UserModel).count()
    total_books = db.query(BookModel).filter(BookModel.is_active == True).count()
    total_reviews = db.query(Review).count()
    total_reading_sessions = db.query(ReadingSession).count()
    
    # Самые популярные книги
    popular_books = db.query(BookModel).filter(
        BookModel.is_active == True
    ).order_by(BookModel.view_count.desc()).limit(5).all()
    
    return {
        "total_users": total_users,
        "total_books": total_books,
        "total_reviews": total_reviews,
        "total_reading_sessions": total_reading_sessions,
        "popular_books": [
            {
                "id": book.id,
                "title": book.title,
                "views": book.view_count or 0,
                "downloads": book.download_count or 0
            }
            for book in popular_books
        ]
    }

@router.get("/users", response_model=List[User])
def admin_get_users(
    request: Request,
    db: Session = Depends(get_db)
):
    """Список всех пользователей (только для админа, для админ-панели)"""
    check_admin(request)
    return get_users(db, skip=0, limit=100)

@router.post("/books", response_model=Book)
def admin_create_book(
    request: Request,
    book: BookCreate,
    db: Session = Depends(get_db)
):
    """Создать книгу (админ)"""
    check_admin(request)
    return create_book(db, book)


@router.put("/books/{book_id}", response_model=Book)
def admin_update_book(
    request: Request,
    book_id: int,
    book: BookUpdate,
    db: Session = Depends(get_db)
):
    """Обновить книгу (админ)"""
    check_admin(request)
    updated_book = update_book(db, book_id, book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@router.delete("/books/{book_id}")
def admin_delete_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db)
):
    """Удалить книгу (админ)"""
    check_admin(request)
    if not delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@router.patch("/users/{user_id}/role", response_model=User)
def admin_update_user_role(
    request: Request,
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db)
):
    """Изменить роль пользователя (только админ)."""
    check_admin(request)

    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    user_obj.role = new_role
    db.commit()
    db.refresh(user_obj)
    return user_obj


@router.patch("/users/{user_id}/status", response_model=User)
def admin_update_user_status(
    request: Request,
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """Активировать/деактивировать пользователя (только админ)."""
    check_admin(request)

    user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    user_obj.is_active = is_active
    db.commit()
    db.refresh(user_obj)
    return user_obj

# Отладочный эндпоинт
@router.get("/debug")
def admin_debug(request: Request, db: Session = Depends(get_db)):
    """Отладочная информация"""
    return {
        "request_user": dict(request.state.user) if hasattr(request.state, 'user') else None,
        "is_admin": request.state.user.get("role") == "admin" if hasattr(request.state, 'user') else False,
        "total_users": db.query(UserModel).count(),
        "admin_users": [u.username for u in db.query(UserModel).filter(UserModel.role == "admin").all()]
    }

