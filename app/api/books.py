from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import get_db
from app.schemas.book import Book, BookCreate, BookUpdate, BookSearch, Review, ReviewCreate, Category, Author
from app.services.book import (
    get_book, get_books, search_books, create_book, update_book, delete_book,
    get_categories, get_authors, create_review, get_book_reviews
)
from app.api.auth import get_current_active_user, get_current_user

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=List[Book])
def read_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    return get_books(db, skip=skip, limit=limit)


@router.get("/search", response_model=List[Book])
def search_books_endpoint(
    query: str = Query(..., min_length=1),
    category_id: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    language: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    search_params = BookSearch(
        query=query,
        category_id=category_id,
        author_id=author_id,
        language=language,
        year_min=year_min,
        year_max=year_max
    )
    return search_books(db, search_params, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    book = get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=Book)
def create_book_endpoint(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if user has permission to create books
    if current_user.role not in ["librarian", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return create_book(db, book)


@router.put("/{book_id}", response_model=Book)
def update_book_endpoint(
    book_id: int,
    book: BookUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if user has permission to update books
    if current_user.role not in ["librarian", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
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
    # Check if user has permission to delete books
    if current_user.role not in ["librarian", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@router.get("/categories/", response_model=List[Category])
def get_categories_endpoint(db: Session = Depends(get_db)):
    return get_categories(db)


@router.get("/authors/", response_model=List[Author])
def get_authors_endpoint(db: Session = Depends(get_db)):
    return get_authors(db)


@router.post("/{book_id}/reviews", response_model=Review)
def create_review_endpoint(
    book_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if book exists
    book = get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    review.book_id = book_id
    return create_review(db, review, current_user.id)


@router.get("/{book_id}/reviews", response_model=List[Review])
def get_book_reviews_endpoint(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Check if book exists
    book = get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return get_book_reviews(db, book_id, skip=skip, limit=limit)
