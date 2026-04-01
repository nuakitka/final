from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import get_db
from app.schemas.book import Book, BookCreate, BookUpdate, BookSearch, Review, ReviewCreate, Category, Author
from app.services.book import (
    get_book, get_books, search_books, create_book, update_book, delete_book,
    get_categories, get_authors, create_review, get_book_reviews
)
from app.api.auth import get_current_active_user

router = APIRouter(tags=["books"])

# ==============================================================================
# 1. СТАТИЧЕСКИЕ МАРШРУТЫ БЕЗ PATH-ПАРАМЕТРОВ (ВЫСШИЙ ПРИОРИТЕТ)
# Эти маршруты должны идти перед любыми маршрутами типа /{id}
# ==============================================================================

@router.get("/categories", response_model=List[Category])
@router.get("/categories/", response_model=List[Category])
def get_categories_endpoint(db: Session = Depends(get_db)):
    """Получить список всех категорий."""
    return get_categories(db)


@router.get("/authors", response_model=List[Author])
@router.get("/authors/", response_model=List[Author])
def get_authors_endpoint(db: Session = Depends(get_db)):
    """Получить список всех авторов."""
    return get_authors(db)


@router.get("", response_model=List[Book])
@router.get("/", response_model=List[Book])
def read_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Получить список книг (корневой маршрут)."""
    # Public endpoint, no authentication required
    return get_books(db, skip=skip, limit=limit, sort=sort)


@router.get("/search", response_model=List[Book])
def search_books_endpoint(
    query: str = Query("", min_length=0),  # Измените на пустую строку по умолчанию
    category_id: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    language: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Поиск книг по различным параметрам."""
    search_params = BookSearch(
        query=query,
        category_id=category_id,
        author_id=author_id,
        language=language,
        year_min=year_min,
        year_max=year_max
    )
    return search_books(db, search_params, skip=skip, limit=limit)

@router.get("/stats")
def get_books_stats(db: Session = Depends(get_db)):
    """Получить статистику по книгам"""
    from app.models.book import Book, Author, Category
    
    total_books = db.query(Book).filter(Book.is_active == True).count()
    total_authors = db.query(Author).count()
    total_categories = db.query(Category).filter(Category.is_active == True).count()
    
    return {
        "total_books": total_books,
        "total_authors": total_authors,
        "total_categories": total_categories
    }

# ==============================================================================
# 2. ДИНАМИЧЕСКИЕ МАРШРУТЫ С PATH-ПАРАМЕТРАМИ (НИЗШИЙ ПРИОРИТЕТ)
# ==============================================================================

@router.get("/{book_id}", response_model=Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    """Получить книгу по ID."""
    book = get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# В функции create_review_endpoint добавьте логирование:
@router.post("/{book_id}/reviews", response_model=Review)
def create_review_endpoint(
    book_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Создать рецензию для книги"""
    print(f"📝 Начало создания рецензии для книги {book_id}")
    print(f"👤 Текущий пользователь: {current_user.username} (ID: {current_user.id})")
    print(f"📊 Данные рецензии: {review.model_dump()}")
    
    # Check if book exists
    book = get_book(db, book_id)
    if not book:
        print(f"❌ Книга {book_id} не найдена")
        raise HTTPException(status_code=404, detail="Book not found")
    
    print(f"✅ Книга найдена: {book.title}")
    
    # Проверяем, что пользователь действительно читал книгу (есть завершённая сессия чтения)
    from app.models.book import Review, ReadingSession

    has_completed_session = db.query(ReadingSession).filter(
        ReadingSession.book_id == book_id,
        ReadingSession.user_id == current_user.id,
        ReadingSession.is_completed == True,
    ).first()

    if not has_completed_session:
        print(f"⚠️  Пользователь {current_user.username} пытается оставить отзыв без завершённого чтения книги {book_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Оставлять отзывы можно только после прочтения книги"
        )

    # Проверяем, не оставлял ли уже пользователь рецензию на эту книгу
    existing_review = db.query(Review).filter(
        Review.book_id == book_id,
        Review.user_id == current_user.id
    ).first()
    
    if existing_review:
        print(f"⚠️  Пользователь {current_user.username} уже оставлял рецензию на эту книгу")
        raise HTTPException(
            status_code=400,
            detail="Вы уже оставляли рецензию на эту книгу"
        )
    
    # Создаем рецензию
    try:
        db_review = Review(
            book_id=book_id,
            user_id=current_user.id,
            rating=review.rating,
            title=review.title or "",
            content=review.content,
            is_approved=True
        )
        
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        # После создания рецензии пересчитаем средний рейтинг книги,
        # чтобы он корректно отображался в каталоге и других списках
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.book_id == book_id,
            Review.is_approved == True
        ).scalar()

        book.rating = avg_rating or 0.0
        db.commit()
        
        print(f"✅ Рецензия создана успешно: ID {db_review.id}")
        
        # Возвращаем рецензию
        return {
            "id": db_review.id,
            "book_id": db_review.book_id,
            "user_id": db_review.user_id,
            "rating": db_review.rating,
            "title": db_review.title,
            "content": db_review.content,
            "created_at": db_review.created_at,
            "is_approved": db_review.is_approved
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании рецензии: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании рецензии: {str(e)}"
        )
    
@router.get("/{book_id}/reviews", response_model=List[Review])
def get_book_reviews_endpoint(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Получить рецензии для книги."""
    # Public read access (implicit READ_REVIEWS)
    # Check if book exists
    book = get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return get_book_reviews(db, book_id, skip=skip, limit=limit)


@router.post("/", response_model=Book)
def create_book_endpoint(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)  # Простая проверка авторизации
):
    """Создать новую книгу (требуется авторизация и права администратора/библиотекаря)"""
    # Проверяем права через роль пользователя
    if not current_user or current_user.role not in ["admin", "librarian"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора или библиотекаря"
        )
    
    return create_book(db, book)

@router.put("/{book_id}", response_model=Book)
def update_book_endpoint(
    book_id: int,
    book: BookUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Обновить существующую книгу"""
    if not current_user or current_user.role not in ["admin", "librarian"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора или библиотекаря"
        )
    
    updated_book = update_book(db, book_id, book)
    if updated_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@router.delete("/{book_id}")
def delete_book_endpoint(
    book_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Удалить книгу"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    
    if not delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}
