from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.book import Book, Category, Author, Review
from app.schemas.book import BookCreate, BookUpdate, BookSearch, ReviewCreate


def get_book(db: Session, book_id: int) -> Optional[Book]:
    return db.query(Book).filter(Book.id == book_id, Book.is_active == True).first()


def _apply_sort(query, sort: Optional[str]):
    if sort == "newest":
        return query.order_by(Book.created_at.desc(), Book.id.desc())
    if sort == "popular":
        return query.order_by(
            Book.view_count.desc(),
            Book.download_count.desc(),
            Book.rating.desc(),
            Book.id.desc(),
        )
    return query.order_by(Book.id.asc())


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _load_categories(db: Session, category_ids: List[int]) -> List[Category]:
    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    found_ids = {category.id for category in categories}
    missing_ids = sorted(set(category_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Категории не найдены: {', '.join(map(str, missing_ids))}"
        )
    return categories


def _load_authors(db: Session, author_ids: List[int]) -> List[Author]:
    authors = db.query(Author).filter(Author.id.in_(author_ids)).all()
    found_ids = {author.id for author in authors}
    missing_ids = sorted(set(author_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Авторы не найдены: {', '.join(map(str, missing_ids))}"
        )
    return authors


def get_books(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sort: Optional[str] = None,
) -> List[Book]:
    query = db.query(Book).filter(Book.is_active == True)
    query = _apply_sort(query, sort)
    return query.offset(skip).limit(limit).all()


def search_books(db: Session, search: BookSearch, skip: int = 0, limit: int = 100) -> List[Book]:
    query = db.query(Book).filter(Book.is_active == True)

    if search.query:
        text_query = f"%{search.query}%"
        query = query.outerjoin(Book.authors).outerjoin(Book.categories)
        query = query.filter(
            or_(
                Book.title.ilike(text_query),
                Book.description.ilike(text_query),
                Book.subtitle.ilike(text_query),
                Author.first_name.ilike(text_query),
                Author.last_name.ilike(text_query),
                Category.name.ilike(text_query),
            )
        )

    if search.category_id:
        query = query.join(Book.categories).filter(Category.id == search.category_id)

    if search.author_id:
        query = query.join(Book.authors).filter(Author.id == search.author_id)

    if search.language:
        query = query.filter(Book.language == search.language)

    if search.year_min:
        query = query.filter(Book.publication_year >= search.year_min)

    if search.year_max:
        query = query.filter(Book.publication_year <= search.year_max)

    query = _apply_sort(query.distinct(), "newest")
    return query.offset(skip).limit(limit).all()


def create_book(db: Session, book: BookCreate) -> Book:
    db_book = Book(
        title=book.title,
        subtitle=_normalize_optional_text(book.subtitle),
        isbn=_normalize_optional_text(book.isbn),
        description=_normalize_optional_text(book.description),
        publication_year=book.publication_year,
        language=book.language,
        pages=book.pages,
        file_url=_normalize_optional_text(book.file_url),
        cover_url=_normalize_optional_text(book.cover_url),
    )

    # Add categories
    if book.category_ids:
        categories = _load_categories(db, book.category_ids)
        db_book.categories = categories

    # Add authors
    if book.author_ids:
        authors = _load_authors(db, book.author_ids)
        db_book.authors = authors

    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book_update: BookUpdate) -> Optional[Book]:
    db_book = get_book(db, book_id)
    if not db_book:
        return None

    update_data = book_update.model_dump(exclude_unset=True)

    # Handle categories and authors separately
    category_ids = update_data.pop("category_ids", None)
    author_ids = update_data.pop("author_ids", None)

    # Update basic fields
    for field, value in update_data.items():
        if field in {"subtitle", "isbn", "description", "file_url", "cover_url"}:
            value = _normalize_optional_text(value)
        setattr(db_book, field, value)

    # Update categories if provided
    if category_ids is not None:
        categories = _load_categories(db, category_ids) if category_ids else []
        db_book.categories = categories

    # Update authors if provided
    if author_ids is not None:
        authors = _load_authors(db, author_ids) if author_ids else []
        db_book.authors = authors

    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int) -> bool:
    db_book = get_book(db, book_id)
    if not db_book:
        return False
    
    db_book.is_active = False
    db.commit()
    return True


def get_categories(db: Session) -> List[Category]:
    return db.query(Category).filter(Category.is_active == True).all()


def get_authors(db: Session) -> List[Author]:
    return db.query(Author).all()


def create_review(db: Session, review: ReviewCreate, user_id: int) -> Review:
    db_review = Review(
        book_id=review.book_id,
        user_id=user_id,
        rating=review.rating,
        title=review.title,
        content=review.content
    )
    db.add(db_review)
    
    # Update book rating
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.book_id == review.book_id,
        Review.is_approved == True
    ).scalar()
    
    book = db.query(Book).filter(Book.id == review.book_id).first()
    if book:
        book.rating = avg_rating or 0.0
    
    db.commit()
    db.refresh(db_review)
    return db_review


def get_book_reviews(db: Session, book_id: int, skip: int = 0, limit: int = 50) -> List[Review]:
    """Retrieves approved reviews for a specific book."""
    return db.query(Review).filter(
        Review.book_id == book_id, 
        Review.is_approved == True # Only show approved reviews by default
    ).offset(skip).limit(limit).all()
