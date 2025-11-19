# Онлайн-библиотека

Система управления онлайн-библиотекой на основе FastAPI и PostgreSQL.

## Архитектура

- **Бэкенд**: FastAPI (Python)
- **База данных**: PostgreSQL
- **Фронтенд**: HTML/CSS/JavaScript (MPA)
- **Развертывание**: Docker/Docker Compose

## Установка и запуск

1. Клонировать репозиторий
2. Создать файл `.env` на основе `.env.example`
3. Запустить с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```
4. Выполнить миграции базы данных:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

## Запуск с Docker

### Разработка
```bash
# Создать файл .env с переменными окружения
cp .env.example .env

# Запустить в режиме разработки
docker-compose -f docker-compose.dev.yml up -d

# Остановить
docker-compose -f docker-compose.dev.yml down
```

### Продакшн
```bash
# Создать файл .env с переменными окружения для продакшн
cp .env.example .env
# Отредактируйте .env с реальными значениями

# Запустить в продакшн режиме
docker-compose -f docker-compose.prod.yml up -d

# Остановить
docker-compose -f docker-compose.prod.yml down
```

### Полный продакшн стек с Nginx
```bash
# Запустить все сервисы включая Nginx
docker-compose up -d

# Просмотр логов
docker-compose logs -f api

# Выполнить миграции
docker-compose exec api alembic upgrade head

# Создать суперпользователя
docker-compose exec api python -c "
from app.services.auth import create_user
from app.core.config import settings
print('Admin user created:', create_user('admin', 'admin@library.local', 'Admin User', 'admin123'))
"
```

## Запуск без Docker

### Установка
```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Linux/Mac)
source venv/bin/activate
# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

### Запуск PostgreSQL
```bash
# Установить PostgreSQL и создать базу данных
createdb library_db

# Или использовать Docker для PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=library_db \
  -e POSTGRES_USER=library_user \
  -e POSTGRES_PASSWORD=library_password \
  -p 5432:5432 \
  postgres:15-alpine
```

### Миграции базы данных
```bash
# Инициализировать Alembic
alembic init alembic

# Создать первую миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграции
alembic upgrade head
```

### Запуск приложения
```bash
# Запустить сервер разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Или использовать скрипт
python -m app.main
```

## Структура проекта

```
vproject/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── books.py
│   │   └── users.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── user.py
│   │   └── book.py
│   ├── schemas/
│   │   ├── user.py
│   │   └── book.py
│   ├── services/
│   │   ├── auth.py
│   │   └── book.py
│   └── main.py
├── static/
├── templates/
├── alembic/
├── docker-compose.yml
└── requirements.txt
```

## Роли пользователей

- **Гость**: Поиск и просмотр каталога
- **Читатель**: Управление избранным, отзывы
- **Библиотекарь**: Модерация, каталогизация
- **Администратор**: Полный контроль системы
