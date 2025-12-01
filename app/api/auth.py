from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.models import get_db
from app.schemas.user import UserCreate, UserLogin, Token, User
from app.services.auth import create_user, login_user, get_user_by_username, get_user_by_email
from app.core.security import verify_token, create_access_token, verify_password

router = APIRouter(tags=["authentication"])

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получаем текущего пользователя из токена"""
    try:
        # Получаем токен из заголовка или куки
        token = None
        
        # 1. Из заголовка Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        # 2. Из куки
        if not token:
            token = request.cookies.get("access_token")
        
        if not token:
            return None
        
        # Проверяем токен
        payload = verify_token(token)
        username = payload.get("sub")
        
        if not username:
            return None
        
        # Получаем пользователя из базы
        user = get_user_by_username(db, username=username)
        return user
        
    except HTTPException:
        # Если токен невалиден, возвращаем None
        return None
    except Exception as e:
        print(f"⚠️  Ошибка при получении пользователя: {e}")
        return None

def get_current_active_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Получаем активного пользователя"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован. Пожалуйста, войдите в систему."
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь неактивен"
        )
    
    return current_user

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

@router.post("/login", response_model=Token)
def login(
    user_login: UserLogin, 
    db: Session = Depends(get_db),
    response: Response = None
):
    """Вход в систему"""
    try:
        # Получаем пользователя по email или username
        user = get_user_by_username(db, user_login.username)
        if not user:
            user = get_user_by_email(db, user_login.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль"
            )
        
        # Проверяем пароль - ИСПРАВЛЕНО: используем hashed_password вместо password_hash
        if not verify_password(user_login.password, user.hashed_password):  # <-- ИСПРАВЛЕНО
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль"
            )
        
        # Проверяем активность пользователя
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь неактивен"
            )
        
        # Создаем токен
        access_token = create_access_token(
            data={"sub": user.username}
        )
        
        # Устанавливаем токен в cookie
        if response:
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                max_age=30 * 24 * 60 * 60,  # 30 дней
                path="/",
                samesite="lax"
            )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка при входе: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@router.post("/logout")
def logout(response: Response):
    """Выход из системы"""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Успешно вышли из системы"}

@router.post("/register", response_model=User)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем email
    if '@' not in user.email:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат email"
        )
    
    # Проверяем существование пользователя
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Имя пользователя уже занято"
        )
    
    db_email = get_user_by_email(db, user.email)
    if db_email:
        raise HTTPException(
            status_code=400,
            detail="Email уже зарегистрирован"
        )
    
    # Создаем пользователя
    return create_user(db, user)