from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from sqlalchemy.schema import MetaData

# Определение соглашений об именовании
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

# 1. Создание Engine
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 2. Создание SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Базовый класс для всех моделей
Base = declarative_base(metadata=metadata)

def get_db():
    """Dependency для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def init_db():
    """
    Создает все таблицы в базе данных.
    """
    print("--- Инициализация базы данных: Проверка и создание таблиц ---")
    
    try:
        # Создаем все таблицы (если их нет)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✅ Таблицы созданы/проверены")
        
        # Проверяем наличие администратора
        check_admin_exists()
        
        # Только проверяем данные
        check_database_status()
        
    except Exception as e:
        print(f"⚠️ Ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
    
    print("--- Инициализация базы данных завершена ---")

def check_admin_exists():
    """Проверяем наличие администратора в системе"""
    db = SessionLocal()
    try:
        from app.models.user import User
        
        admins = db.query(User).filter(User.role == "admin").all()
        
        if admins:
            admin_names = ", ".join([a.username for a in admins])
            print(f"✅ Администраторы в системе: {admin_names}")
        else:
            print("⚠️  В системе нет администраторов!")
            print("ℹ️  Первый зарегистрированный пользователь станет администратором.")
            
    except Exception as e:
        print(f"⚠️ Ошибка проверки администраторов: {e}")
    finally:
        db.close()

def check_database_status():
    """Просто проверяем статус базы данных"""
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.models.book import Book, Category, Author
        
        users_count = db.query(User).count()
        books_count = db.query(Book).count()
        categories_count = db.query(Category).count()
        authors_count = db.query(Author).count()
        
        print(f"📊 Статистика базы данных:")
        print(f"  👥 Пользователей: {users_count}")
        print(f"  📚 Книг: {books_count}")
        print(f"  📁 Категорий: {categories_count}")
        print(f"  ✍️ Авторов: {authors_count}")
        
    except Exception as e:
        print(f"⚠️ Ошибка при проверке данных: {e}")
    finally:
        db.close()