import os
import sys
import tempfile
from pathlib import Path


TEST_DB_PATH = Path(tempfile.gettempdir()) / "library_app_smoke.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def create_client() -> TestClient:
    return TestClient(app)


def register_user(client: TestClient, username: str, email: str, password: str = "password123"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": f"{username} Fullname",
        },
    )


def login_user(client: TestClient, username: str, password: str = "password123"):
    return client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )


def test_public_pages_and_seed_data_are_available():
    with create_client() as client:
        for path in ["/", "/catalog", "/login", "/register"]:
            response = client.get(path)
            assert response.status_code == 200

        books_response = client.get("/api/books")
        assert books_response.status_code == 200

        books = books_response.json()
        assert len(books) >= 1
        assert books[0]["title"] == "Война и мир"
        assert books[0]["file_url"] == "/static/demo-book.txt"


def test_auth_profile_and_admin_flow():
    with create_client() as client:
        register_response = register_user(client, "admin_user", "admin@example.com")
        assert register_response.status_code == 200
        assert register_response.json()["role"] == "admin"

        login_response = login_user(client, "admin_user")
        assert login_response.status_code == 200
        assert login_response.cookies.get("access_token")

        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 200
        me_payload = me_response.json()
        assert me_payload["username"] == "admin_user"
        assert me_payload["role"] == "admin"

        profile_response = client.get("/profile")
        assert profile_response.status_code == 200

        stats_response = client.get("/api/admin/stats")
        assert stats_response.status_code == 200
        assert "total_books" in stats_response.json()

    with create_client() as anonymous_client:
        redirect_response = anonymous_client.get("/profile", follow_redirects=False)
        assert redirect_response.status_code == 302
        assert redirect_response.headers["location"] == "/login"


def test_reading_progress_and_review_submission_flow():
    with create_client() as client:
        register_response = register_user(client, "reader_user", "reader@example.com")
        assert register_response.status_code == 200

        login_response = login_user(client, "reader_user")
        assert login_response.status_code == 200

        books_response = client.get("/api/books")
        books = books_response.json()
        book_id = books[0]["id"]

        progress_response = client.post(
            f"/api/users/me/reading-sessions/{book_id}/progress",
            json={
                "progress_percentage": 100,
                "pages_read": 50,
                "is_completed": True,
            },
        )
        assert progress_response.status_code == 200
        assert progress_response.json()["is_completed"] is True

        review_response = client.post(
            f"/api/books/{book_id}/reviews",
            json={
                "book_id": book_id,
                "rating": 5,
                "title": "Отлично",
                "content": "Тестовый отзыв после чтения.",
            },
        )
        assert review_response.status_code == 200
        assert review_response.json()["book_id"] == book_id

        reviews_response = client.get(f"/api/books/{book_id}/reviews")
        assert reviews_response.status_code == 200
        assert any(review["content"] == "Тестовый отзыв после чтения." for review in reviews_response.json())
