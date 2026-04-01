from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import declarative_base

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
engine_kwargs = {"pool_pre_ping": True}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

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
        from app.models import user as user_models  # noqa: F401
        from app.models import book as book_models  # noqa: F401

        # Создаем все таблицы (если их нет)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✅ Таблицы созданы/проверены")

        seed_initial_data()

        # Проверяем наличие администратора
        check_admin_exists()

        # Только проверяем данные
        check_database_status()

    except Exception as e:
        print(f"⚠️ Ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        raise

    print("--- Инициализация базы данных завершена ---")


def seed_initial_data():
    """Создаем демонстрационные записи для пустой базы."""
    db = SessionLocal()
    try:
        from app.models.book import Book, Category, Author

        if db.query(Book).count() > 0:
            return

        category = db.query(Category).filter(Category.name == "Художественная литература").first()
        if not category:
            category = Category(
                name="Художественная литература",
                description="Романы, повести и рассказы",
                is_active=True,
            )
            db.add(category)
            db.flush()

        author = db.query(Author).filter(
            Author.first_name == "Лев",
            Author.last_name == "Толстой"
        ).first()
        if not author:
            author = Author(
                first_name="Лев",
                last_name="Толстой",
                bio="Великий русский писатель.",
            )
            db.add(author)
            db.flush()

        sample_book = Book(
            title="Война и мир",
            subtitle="Демонстрационная книга",
            isbn="978-5-17-070490-3",
            description="Тестовая запись для проверки работы каталога, чтения и рецензий.",
            publication_year=1869,
            language="ru",
            pages=1225,
            file_format="TXT",
            file_url="/static/demo-book.txt",
            rating=4.8,
            download_count=0,
            view_count=0,
            is_active=True,
            is_featured=True,
        )
        sample_book.categories = [category]
        sample_book.authors = [author]

        db.add(sample_book)
        db.commit()
        print("✅ Добавлены демонстрационные данные")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Не удалось добавить демонстрационные данные: {e}")
    finally:
        db.close()

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
