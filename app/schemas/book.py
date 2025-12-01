from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class Category(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    bio: Optional[str] = None


class Author(AuthorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BookBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    publication_year: Optional[int] = None
    language: str = "ru"
    pages: Optional[int] = None
    file_url: Optional[str] = None
    cover_url: Optional[str] = None


class BookCreate(BookBase):
    category_ids: Optional[List[int]] = []
    author_ids: Optional[List[int]] = []


class BookUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    publication_year: Optional[int] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    file_url: Optional[str] = None
    cover_url: Optional[str] = None
    category_ids: Optional[List[int]] = None
    author_ids: Optional[List[int]] = None


class Book(BookBase):
    id: int
    rating: float
    download_count: int
    view_count: int
    is_active: bool
    is_featured: bool
    created_at: datetime
    categories: List[Category] = []
    authors: List[Author] = []

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    rating: int
    title: Optional[str] = None
    content: str


class ReviewCreate(ReviewBase):
    book_id: int


class Review(ReviewBase):
    id: int
    book_id: int
    user_id: int
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BookSearch(BaseModel):
    query: str
    category_id: Optional[int] = None
    author_id: Optional[int] = None
    language: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
