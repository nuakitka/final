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