from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.book import Book, Category, Author, Review
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate, BookSearch, ReviewCreate


def get_book(db: Session, book_id: int) -> Optional[Book]:
    return db.query(Book).filter(Book.id == book_id, Book.is_active == True).first()


def get_books(db: Session, skip: int = 0, limit: int = 100) -> List[Book]:
    return db.query(Book).filter(Book.is_active == True).offset(skip).limit(limit).all()


def search_books(db: Session, search: BookSearch, skip: int = 0, limit: int = 100) -> List[Book]:
    query = db.query(Book).filter(Book.is_active == True)
    
    if search.query:
        # Basic text search (can be enhanced with full-text search)
        query = query.filter(
            or_(
                Book.title.ilike(f"%{search.query}%"),
                Book.description.ilike(f"%{search.query}%"),
                Book.subtitle.ilike(f"%{search.query}%")
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
    
    return query.offset(skip).limit(limit).all()


def create_book(db: Session, book: BookCreate) -> Book:
    db_book = Book(
        title=book.title,
        subtitle=book.subtitle,
        isbn=book.isbn,
        description=book.description,
        publication_year=book.publication_year,
        language=book.language,
        pages=book.pages
    )
    
    # Add categories
    if book.category_ids:
        categories = db.query(Category).filter(Category.id.in_(book.category_ids)).all()
        db_book.categories = categories
    
    # Add authors
    if book.author_ids:
        authors = db.query(Author).filter(Author.id.in_(book.author_ids)).all()
        db_book.authors = authors
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book_update: BookUpdate) -> Optional[Book]:
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    
    update_data = book_update.dict(exclude_unset=True)
    
    # Handle categories and authors separately
    category_ids = update_data.pop("category_ids", None)
    author_ids = update_data.pop("author_ids", None)
    
    # Update basic fields
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    # Update categories if provided
    if category_ids is not None:
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        db_book.categories = categories
    
    # Update authors if provided
    if author_ids is not None:
        authors = db.query(Author).filter(Author.id.in_(author_ids)).all()
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
    return db.query(Review).filter(
        Review.book_id == book_id,
        Review.is_approved == True
    ).offset(skip).limit(limit).all()
