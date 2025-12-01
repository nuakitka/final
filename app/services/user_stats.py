from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.book import ReadingSession, Review, Book
from app.models.user import User


def get_user_reading_stats(db: Session, user_id: int):
    """Получить статистику чтения пользователя"""
    try:
        # Количество завершенных книг
        completed_books = db.query(ReadingSession).filter(
            ReadingSession.user_id == user_id,
            ReadingSession.is_completed == True
        ).count()

        # Книги в процессе чтения
        reading_books = db.query(ReadingSession).filter(
            ReadingSession.user_id == user_id,
            ReadingSession.is_completed == False
        ).count()

        # Всего прочитанных страниц
        total_pages = db.query(func.sum(ReadingSession.pages_read)).filter(
            ReadingSession.user_id == user_id
        ).scalar() or 0

        # Количество рецензий
        reviews_count = db.query(Review).filter(Review.user_id == user_id).count()

        # Время чтения (в часах) - упрощенная версия
        reading_time_hours = completed_books * 2 + reading_books * 1

        return {
            "completed_books": completed_books,
            "reading_books": reading_books,
            "total_pages": total_pages,
            "reviews_count": reviews_count,
            "favorites_count": 0,  # Временно
            "reading_time_hours": reading_time_hours
        }
    except Exception as e:
        print(f"Ошибка в get_user_reading_stats: {e}")
        return {
            "completed_books": 0,
            "reading_books": 0,
            "total_pages": 0,
            "reviews_count": 0,
            "favorites_count": 0,
            "reading_time_hours": 0
        }


def ensure_reading_session(db: Session, user_id: int, book_id: int) -> ReadingSession:
    """Убедиться, что для пользователя и книги есть активная сессия чтения.

    Если активной сессии (is_completed == False) нет, создаём новую и возвращаем её.
    """
    try:
        session = db.query(ReadingSession).filter(
            ReadingSession.user_id == user_id,
            ReadingSession.book_id == book_id,
            ReadingSession.is_completed == False,
        ).first()

        if not session:
            session = ReadingSession(
                user_id=user_id,
                book_id=book_id,
                pages_read=0,
                progress_percentage=0,
                is_completed=False,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        return session
    except Exception as e:
        print(f"Ошибка в ensure_reading_session: {e}")
        db.rollback()
        raise


def update_reading_progress(
    db: Session,
    user_id: int,
    book_id: int,
    progress_percentage: int,
    pages_read: int | None = None,
    is_completed: bool | None = None,
) -> ReadingSession:
    """Обновить прогресс чтения книги для пользователя."""
    session = ensure_reading_session(db, user_id, book_id)

    session.progress_percentage = max(0, min(100, progress_percentage))
    if pages_read is not None:
        session.pages_read = max(0, pages_read)
    if is_completed is not None:
        session.is_completed = is_completed

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_reading_sessions(db: Session, user_id: int, active_only: bool = False):
    """Получить сессии чтения пользователя"""
    try:
        query = db.query(ReadingSession).filter(ReadingSession.user_id == user_id)
        
        if active_only:
            query = query.filter(ReadingSession.is_completed == False)
        
        sessions = query.order_by(ReadingSession.start_time.desc()).all()
        
        # Преобразуем сессии в удобный формат
        result = []
        for session in sessions:
            result.append({
                "id": session.id,
                "book": {
                    "id": session.book.id,
                    "title": session.book.title,
                    "author": get_book_author(session.book),
                    "cover_url": session.book.cover_url or "/static/images/book-placeholder.jpg"
                },
                "progress_percentage": session.progress_percentage or 0,
                "pages_read": session.pages_read or 0,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "is_completed": session.is_completed or False
            })
        
        return result
    except Exception as e:
        print(f"Ошибка в get_user_reading_sessions: {e}")
        return []

def get_book_author(book):
    """Вспомогательная функция для получения автора книги"""
    try:
        if book.authors and len(book.authors) > 0:
            author = book.authors[0]
            return f"{author.first_name} {author.last_name}"
        return "Неизвестный автор"
    except:
        return "Неизвестный автор"