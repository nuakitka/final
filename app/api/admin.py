from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from uuid import uuid4
import shutil

from app.models import get_db
from app.schemas.user import User
from app.schemas.book import Book, BookCreate, BookUpdate
from app.services.book import get_books, create_book, update_book, delete_book
from app.services.auth import get_users
from app.models.user import User as UserModel
from app.models.book import Book as BookModel, Review, ReadingSession, Author as AuthorModel, Category as CategoryModel

router = APIRouter(tags=["admin"])

# Простая проверка через request.state.user
def check_admin(request: Request):
    """Проверка, что пользователь — администратор."""
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


def check_admin_or_librarian(request: Request):
    """Проверка, что пользователь — админ или библиотекарь.

    Используем для операций с книгами и загрузки файлов.
    """
    user = request.state.user
    print(f"🔍 Проверка staff (admin/librarian): user={user}")

    if not user or not user.get("is_authenticated"):
        print("❌ Пользователь не авторизован")
        raise HTTPException(status_code=401, detail="Не авторизован")

    if user.get("role") not in ("admin", "librarian"):
        print(f"❌ Недостаточно прав. Роль: {user.get('role')}")
        raise HTTPException(status_code=403, detail="Требуются права администратора или библиотекаря")

    print(f"✅ Доступ staff подтверждён: {user.get('username')} ({user.get('role')})")
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
    """Создать книгу (админ/библиотекарь). Любые ошибки БД заворачиваем в понятный JSON-ответ."""
    check_admin_or_librarian(request)

    try:
        created = create_book(db, book)
        return created
    except SQLAlchemyError as e:
        db.rollback()
        # Логируем подробности на сервере, но наружу отдаём аккуратное сообщение
        print(f"❌ Ошибка БД при создании книги: {e}")
        raise HTTPException(
            status_code=400,
            detail="Ошибка при сохранении книги в базу данных. Проверьте корректность автора, категории и других полей."
        )
    except Exception as e:
        db.rollback()
        print(f"❌ Неизвестная ошибка при создании книги: {e}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при создании книги. Попробуйте позже или проверьте логи."
        )


@router.post("/authors")
def admin_create_author(
    request: Request,
    first_name: str,
    last_name: str,
    db: Session = Depends(get_db)
):
    """Создать автора (админ)."""
    check_admin(request)

    author = AuthorModel(first_name=first_name, last_name=last_name)
    db.add(author)
    db.commit()
    db.refresh(author)
    return {
        "id": author.id,
        "first_name": author.first_name,
        "last_name": author.last_name,
    }


@router.delete("/authors/{author_id}")
def admin_delete_author(
    request: Request,
    author_id: int,
    db: Session = Depends(get_db)
):
    """Удалить автора (админ). Нельзя удалить, если к нему привязаны книги."""
    check_admin(request)

    author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Если у автора есть книги, не даём удалить, чтобы не ломать связи
    if author.books:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить автора, который привязан к книгам. Сначала отвяжите книги."
        )

    db.delete(author)
    db.commit()
    return {"detail": "Автор удалён"}


@router.post("/categories")
def admin_create_category(
    request: Request,
    name: str,
    description: str | None = None,
    db: Session = Depends(get_db)
):
    """Создать категорию (админ)."""
    check_admin(request)

    category = CategoryModel(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
    }


@router.delete("/categories/{category_id}")
def admin_delete_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db)
):
    """Удалить категорию (админ). Нельзя удалить, если к ней привязаны книги."""
    check_admin(request)

    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.books:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить категорию, которая привязана к книгам. Сначала отвяжите книги."
        )

    db.delete(category)
    db.commit()
    return {"detail": "Категория удалена"}


@router.post("/upload/book-file")
async def admin_upload_book_file(
    request: Request,
    file: UploadFile = File(...)
):
    """Загрузить файл книги (PDF/EPUB и т.п.). Только для админа.

    Возвращает URL, который можно сохранить в поле file_url книги.
    """
    check_admin(request)

    books_dir = Path("static") / "books"
    books_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix or ".pdf"
    filename = f"{uuid4().hex}{suffix}"
    dest_path = books_dir / filename

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/static/books/{filename}"}


@router.post("/upload/cover")
async def admin_upload_cover(
    request: Request,
    file: UploadFile = File(...)
):
    """Загрузить обложку книги (изображение). Только для админа.

    Возвращает URL, который можно сохранить в поле cover_url книги.
    """
    check_admin(request)

    covers_dir = Path("static") / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    dest_path = covers_dir / filename

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/static/covers/{filename}"}


@router.put("/books/{book_id}", response_model=Book)
def admin_update_book(
    request: Request,
    book_id: int,
    book: BookUpdate,
    db: Session = Depends(get_db)
):
    """Обновить книгу (админ/библиотекарь)"""
    check_admin_or_librarian(request)
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
    """Удалить книгу (админ/библиотекарь)"""
    check_admin_or_librarian(request)
    if not delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@router.delete("/reviews/{review_id}")
def admin_delete_review(
    request: Request,
    review_id: int,
    db: Session = Depends(get_db)
):
    """Удалить рецензию (только админ) и пересчитать рейтинг книги."""
    check_admin(request)

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    book_id = review.book_id

    db.delete(review)
    db.commit()

    # Пересчитываем средний рейтинг книги после удаления рецензии
    if book_id:
        book = db.query(BookModel).filter(BookModel.id == book_id).first()
        if book:
            avg_rating = db.query(func.avg(Review.rating)).filter(
                Review.book_id == book_id,
                Review.is_approved == True
            ).scalar()
            book.rating = avg_rating or 0.0
            db.commit()

    return {"detail": "Review deleted"}


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

