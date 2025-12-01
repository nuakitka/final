from fastapi import FastAPI, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.api import auth, books, users, admin 
from app.core.config import settings
from app.core.security import verify_token
from app.models import get_db, SessionLocal
from app.services.book import get_book
from app.models.user import User as UserModel

app = FastAPI(
    title="Online Library API",
    description="API for managing online library system",
    version="1.0.0"
)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware для добавления пользователя в запрос
@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    # Инициализируем пользователя
    request.state.user: Dict[str, Any] = {
        "is_authenticated": False, 
        "username": None,
        "role": None,
        "user_id": None
    }
    
    # Проверяем токен из cookie
    token = request.cookies.get("access_token")
    
    if token:
        try:
            payload = verify_token(token)
            username = payload.get("sub")
            if username:
                # Получаем пользователя из базы для проверки роли
                db = SessionLocal()
                try:
                    user = db.query(UserModel).filter(UserModel.username == username).first()
                    if user:
                        # Добавляем информацию о пользователе
                        request.state.user = {
                            "is_authenticated": True, 
                            "username": user.username,
                            "role": user.role,
                            "user_id": user.id,
                            "email": user.email
                        }
                finally:
                    db.close()
        except Exception:
            pass
    
    response = await call_next(request)
    return response

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Инициализация базы данных
from app.models import init_db
@app.on_event("startup")
async def startup_event():
    init_db()

# Подключаем API роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# HTML Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
    
@app.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request):
    return templates.TemplateResponse("catalog.html", {"request": request})
    
@app.get("/book/{book_id}", response_class=HTMLResponse)
async def book_detail(
    request: Request, 
    book_id: int,
    db: Session = Depends(get_db)
):
    """Страница деталей книги"""
    book = get_book(db, book_id)
    
    if not book:
        # Перенаправляем на каталог если книга не найдена
        return RedirectResponse(url="/catalog")
    
    # Преобразуем данные книги для шаблона
    book_data = {
        "id": book.id,
        "title": book.title,
        "subtitle": book.subtitle,
        "description": book.description or "Описание отсутствует.",
        "cover_url": book.cover_url or "/static/images/book-placeholder.jpg",
        "file_url": book.file_url,
        "publication_year": book.publication_year,
        "pages": book.pages,
        "language": book.language,
        "isbn": book.isbn,
        "rating": float(book.rating) if book.rating else 0.0,
        "view_count": book.view_count or 0,
        "download_count": book.download_count or 0,
        "created_at": book.created_at,
        "authors": [
            {
                "id": author.id,
                "first_name": author.first_name,
                "last_name": author.last_name
            }
            for author in book.authors
        ],
        "categories": [
            {
                "id": category.id,
                "name": category.name
            }
            for category in book.categories
        ]
    }
    
    return templates.TemplateResponse("book_detail.html", {
        "request": request,
        "book": book_data,
        "book_id": book_id
    })
    
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
    
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/add-book", response_class=HTMLResponse)
async def admin_add_book_page(request: Request):
    return templates.TemplateResponse("admin/add_book.html", {"request": request})

@app.get("/logout")
async def logout(response: Response):
    response = Response()
    response.delete_cookie("access_token")
    response.status_code = 302
    response.headers["Location"] = "/"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)