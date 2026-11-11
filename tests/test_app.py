import pytest
from app import app as flask_app, init_db


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.sqlite"
    flask_app.config.update(TESTING=True, DATABASE=str(db_path), SECRET_KEY="test-secret")
    init_db()
    with flask_app.test_client() as client:
        yield client


# ---------- seed helpers ----------

def seed_author(client):
    return client.post("/authors/new", data={
        "full_name": "Лев Толстой", "country": "Россия", "birth_year": "1828"
    }, follow_redirects=True)


def seed_genre(client):
    return client.post("/genres/new", data={
        "name": "Роман", "description": "Крупное прозаическое произведение"
    }, follow_redirects=True)


def seed_book(client):
    seed_author(client)
    seed_genre(client)
    return client.post("/books/new", data={
        "title": "Война и мир", "author_id": "1", "genre_id": "1",
        "isbn": "978-5-00-000000-0", "year": "1869",
        "copies_total": "5", "copies_available": "5",
        "description": "Тестовая книга"
    }, follow_redirects=True)


def seed_reader(client):
    return client.post("/readers/new", data={
        "full_name": "Иван Иванов", "phone": "+7 900 000-00-00",
        "email": "ivan@example.com", "library_card": "CARD-001"
    }, follow_redirects=True)


# ---------- dashboard ----------

def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Библиотечная система".encode() in response.data


# ---------- authors CRUD ----------

def test_author_create_read_update_delete(client):
    response = seed_author(client)
    assert response.status_code == 200
    assert "Лев Толстой".encode() in response.data

    response = client.post("/authors/1/edit", data={
        "full_name": "Лев Николаевич Толстой", "country": "Россия", "birth_year": "1828"
    }, follow_redirects=True)
    assert "Лев Николаевич Толстой".encode() in response.data

    response = client.post("/authors/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


# ---------- genres CRUD ----------

def test_genre_create_read_update_delete(client):
    seed_genre(client)
    assert "Роман".encode() in client.get("/genres").data

    response = client.post("/genres/1/edit", data={
        "name": "Исторический роман", "description": "Обновлено"
    }, follow_redirects=True)
    assert "Исторический роман".encode() in response.data

    response = client.post("/genres/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


# ---------- books CRUD ----------

def test_book_create_read_update_delete(client):
    seed_book(client)
    assert "Война и мир".encode() in client.get("/books").data

    response = client.post("/books/1/edit", data={
        "title": "Война и мир (том 1)", "author_id": "1", "genre_id": "1",
        "isbn": "978-5-00-000000-0", "year": "1869",
        "copies_total": "5", "copies_available": "4",
        "description": "Обновлённое описание"
    }, follow_redirects=True)
    assert "Война и мир (том 1)".encode() in response.data

    response = client.post("/books/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


# ---------- readers CRUD ----------

def test_reader_create_read_update_delete(client):
    seed_reader(client)
    assert "Иван Иванов".encode() in client.get("/readers").data

    response = client.post("/readers/1/edit", data={
        "full_name": "Пётр Петров", "phone": "+7 911 111-11-11",
        "email": "petr@example.com", "library_card": "CARD-002"
    }, follow_redirects=True)
    assert "Пётр Петров".encode() in response.data

    response = client.post("/readers/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


# ---------- loans CRUD ----------

def test_loan_create_read_update_delete(client):
    seed_book(client)
    seed_reader(client)
    data = {
        "book_id": "1", "reader_id": "1",
        "loan_date": "2026-10-10", "due_date": "2026-10-24",
        "returned_date": "", "status": "Выдана", "notes": ""
    }
    client.post("/loans/new", data=data, follow_redirects=True)
    assert "Война и мир".encode() in client.get("/loans").data

    data["status"] = "Возвращена"
    data["returned_date"] = "2026-10-20"
    response = client.post("/loans/1/edit", data=data, follow_redirects=True)
    assert "Возвращена".encode() in response.data

    response = client.post("/loans/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


# ---------- negative cases ----------

def test_invalid_loan_dates_are_rejected(client):
    seed_book(client)
    seed_reader(client)
    response = client.post("/loans/new", data={
        "book_id": "1", "reader_id": "1",
        "loan_date": "2026-10-15", "due_date": "2026-10-10",
        "status": "Выдана"
    }, follow_redirects=True)
    assert "Срок возврата не может быть раньше даты выдачи".encode() in response.data


def test_negative_copies_is_rejected(client):
    seed_author(client)
    seed_genre(client)
    response = client.post("/books/new", data={
        "title": "Книга", "author_id": "1", "genre_id": "1",
        "copies_total": "-1", "copies_available": "0"
    }, follow_redirects=True)
    assert "не может быть отрицательным".encode() in response.data


def test_borrowed_book_cannot_be_deleted(client):
    """FK RESTRICT: книгу, на которую есть выдача, удалить нельзя."""
    seed_book(client)
    seed_reader(client)
    client.post("/loans/new", data={
        "book_id": "1", "reader_id": "1",
        "loan_date": "2026-10-10", "due_date": "2026-10-24",
        "status": "Выдана"
    }, follow_redirects=True)

    response = client.post("/books/1/delete", follow_redirects=True)
    assert "Нельзя удалить запись".encode() in response.data
    # книга всё ещё на месте
    assert "Война и мир".encode() in client.get("/books").data