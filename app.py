from datetime import date
from pathlib import Path
import os
import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = BASE_DIR / "instance" / "library.db"

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    DATABASE=os.environ.get("DATABASE", str(DEFAULT_DB)),
)

# Five entities x four CRUD operation types = at least 20 implemented operations.
ENTITIES = {
    "books": {
        "title": "Книги", "singular": "книгу", "table": "books",
        "fields": [
            {"name": "title", "label": "Название", "type": "text", "required": True},
            {"name": "author_id", "label": "Автор", "type": "select", "ref": "authors", "required": True},
            {"name": "genre_id", "label": "Жанр", "type": "select", "ref": "genres", "required": True},
            {"name": "isbn", "label": "ISBN", "type": "text"},
            {"name": "year", "label": "Год издания", "type": "number", "step": "1"},
            {"name": "copies_total", "label": "Всего экземпляров", "type": "number", "step": "1", "required": True},
            {"name": "copies_available", "label": "Доступно экземпляров", "type": "number", "step": "1", "required": True},
            {"name": "description", "label": "Описание", "type": "textarea"},
        ],
        "columns": [
            ("title", "Название"), ("author_name", "Автор"), ("genre_name", "Жанр"),
            ("year", "Год"), ("copies_available", "Доступно"), ("copies_total", "Всего"),
        ],
        "search": ["title", "isbn"],
    },
    "authors": {
        "title": "Авторы", "singular": "автора", "table": "authors",
        "fields": [
            {"name": "full_name", "label": "ФИО", "type": "text", "required": True},
            {"name": "country", "label": "Страна", "type": "text"},
            {"name": "birth_year", "label": "Год рождения", "type": "number", "step": "1"},
        ],
        "columns": [("full_name", "ФИО"), ("country", "Страна"), ("birth_year", "Год рождения")],
        "search": ["full_name", "country"],
    },
    "genres": {
        "title": "Жанры", "singular": "жанр", "table": "genres",
        "fields": [
            {"name": "name", "label": "Название", "type": "text", "required": True},
            {"name": "description", "label": "Описание", "type": "textarea"},
        ],
        "columns": [("name", "Название"), ("description", "Описание")],
        "search": ["name", "description"],
    },
    "readers": {
        "title": "Читатели", "singular": "читателя", "table": "readers",
        "fields": [
            {"name": "full_name", "label": "ФИО", "type": "text", "required": True},
            {"name": "phone", "label": "Телефон", "type": "text"},
            {"name": "email", "label": "Электронная почта", "type": "email"},
            {"name": "library_card", "label": "Номер билета", "type": "text"},
        ],
        "columns": [
            ("full_name", "ФИО"), ("phone", "Телефон"),
            ("email", "Email"), ("library_card", "Билет"),
        ],
        "search": ["full_name", "phone", "email", "library_card"],
    },
    "loans": {
        "title": "Выдачи", "singular": "выдачу", "table": "loans",
        "fields": [
            {"name": "book_id", "label": "Книга", "type": "select", "ref": "books", "required": True},
            {"name": "reader_id", "label": "Читатель", "type": "select", "ref": "readers", "required": True},
            {"name": "loan_date", "label": "Дата выдачи", "type": "date", "required": True},
            {"name": "due_date", "label": "Срок возврата", "type": "date", "required": True},
            {"name": "returned_date", "label": "Фактическая дата возврата", "type": "date"},
            {"name": "status", "label": "Статус", "type": "select_values",
             "options": ["Выдана", "Возвращена", "Просрочена", "Отменена"], "required": True},
            {"name": "notes", "label": "Примечание", "type": "textarea"},
        ],
        "columns": [
            ("book_title", "Книга"), ("reader_name", "Читатель"),
            ("loan_date", "Выдана"), ("due_date", "Срок возврата"),
            ("status", "Статус"),
        ],
        "search": ["status", "loan_date", "due_date"],
    },
}

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT '',
    birth_year INTEGER
);
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE RESTRICT,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE RESTRICT,
    isbn TEXT NOT NULL DEFAULT '',
    year INTEGER,
    copies_total INTEGER NOT NULL CHECK(copies_total >= 0),
    copies_available INTEGER NOT NULL CHECK(copies_available >= 0 AND copies_available <= copies_total),
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS readers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    library_card TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    reader_id INTEGER NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
    loan_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    returned_date TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Выдана',
    notes TEXT NOT NULL DEFAULT '',
    CHECK(due_date >= loan_date)
);
"""


def get_db():
    db_path = Path(app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


def entity_or_404(entity):
    if entity not in ENTITIES:
        abort(404)
    return ENTITIES[entity]


def reference_options(field):
    ref = field.get("ref")
    if not ref:
        return []
    with get_db() as conn:
        if ref == "authors":
            rows = conn.execute("SELECT id, full_name AS label FROM authors ORDER BY full_name").fetchall()
        elif ref == "genres":
            rows = conn.execute("SELECT id, name AS label FROM genres ORDER BY name").fetchall()
        elif ref == "books":
            rows = conn.execute("SELECT id, title AS label FROM books ORDER BY title").fetchall()
        elif ref == "readers":
            rows = conn.execute("SELECT id, full_name AS label FROM readers ORDER BY full_name").fetchall()
        else:
            rows = []
    return rows


def decorate_fields(entity):
    config = ENTITIES[entity]
    result = []
    for original in config["fields"]:
        field = dict(original)
        if field["type"] == "select":
            field["options_data"] = reference_options(field)
        result.append(field)
    return result


def list_sql(entity, search=""):
    if entity == "books":
        sql = """SELECT b.*, a.full_name AS author_name, g.name AS genre_name
                 FROM books b
                 JOIN authors a ON a.id = b.author_id
                 JOIN genres g ON g.id = b.genre_id"""
    elif entity == "loans":
        sql = """SELECT l.*, b.title AS book_title, r.full_name AS reader_name
                 FROM loans l
                 JOIN books b ON b.id = l.book_id
                 JOIN readers r ON r.id = l.reader_id"""
    else:
        sql = f"SELECT * FROM {ENTITIES[entity]['table']}"
    params = []
    if search.strip():
        fields = ENTITIES[entity]["search"]
        clauses = [f"CAST({field} AS TEXT) LIKE ?" for field in fields]
        sql += " WHERE " + " OR ".join(clauses)
        params = [f"%{search.strip()}%"] * len(clauses)
    sql += " ORDER BY id DESC"
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def get_record(entity, record_id):
    table = ENTITIES[entity]["table"]
    with get_db() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
    if row is None:
        abort(404)
    return row


def prepare_values(entity, form):
    values = {}
    for field in ENTITIES[entity]["fields"]:
        name = field["name"]
        kind = field["type"]
        raw = form.get(name, "").strip()
        if kind == "checkbox":
            values[name] = 1 if form.get(name) == "on" else 0
            continue
        if field.get("required") and not raw:
            raise ValueError(f"Поле «{field['label']}» обязательно для заполнения.")
        if not raw:
            values[name] = 0 if kind == "number" else ""
            continue
        if kind == "number":
            try:
                value = float(raw) if "." in raw else int(raw)
            except ValueError:
                raise ValueError(f"Поле «{field['label']}» должно быть числом.")
            if value < 0:
                raise ValueError(f"Поле «{field['label']}» не может быть отрицательным.")
            values[name] = value
        elif kind == "select":
            try:
                values[name] = int(raw)
            except ValueError:
                raise ValueError(f"Выберите корректное значение поля «{field['label']}».")
        elif kind == "select_values":
            if raw not in field["options"]:
                raise ValueError(f"Недопустимое значение поля «{field['label']}».")
            values[name] = raw
        else:
            values[name] = raw

    # Special-case validation for the loans entity.
    if entity == "loans" and values.get("due_date") and values.get("loan_date"):
        if values["due_date"] < values["loan_date"]:
            raise ValueError("Срок возврата не может быть раньше даты выдачи.")

    return values


def save_record(entity, values, record_id=None):
    table = ENTITIES[entity]["table"]
    names = list(values.keys())
    try:
        with get_db() as conn:
            if record_id is None:
                placeholders = ", ".join("?" for _ in names)
                conn.execute(
                    f"INSERT INTO {table} ({', '.join(names)}) VALUES ({placeholders})",
                    [values[name] for name in names],
                )
            else:
                assignments = ", ".join(f"{name}=?" for name in names)
                conn.execute(
                    f"UPDATE {table} SET {assignments} WHERE id=?",
                    [values[name] for name in names] + [record_id],
                )
    except sqlite3.IntegrityError as exc:
        message = str(exc)
        if "UNIQUE" in message:
            raise ValueError("Запись с таким уникальным значением уже существует.") from exc
        if "FOREIGN KEY" in message:
            raise ValueError("Выбранная связанная запись не существует.") from exc
        if "CHECK constraint" in message:
            raise ValueError("Проверьте корректность дат и числовых значений.") from exc
        raise ValueError("Не удалось сохранить запись. Проверьте введённые данные.") from exc


@app.route("/")
def dashboard():
    with get_db() as conn:
        stats = {
            "books": conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
            "available": conn.execute("SELECT COALESCE(SUM(copies_available), 0) FROM books").fetchone()[0],
            "readers": conn.execute("SELECT COUNT(*) FROM readers").fetchone()[0],
            "active_loans": conn.execute("SELECT COUNT(*) FROM loans WHERE status='Выдана'").fetchone()[0],
        }
        recent = conn.execute(
            """SELECT l.id, b.title AS book_title, r.full_name AS reader_name,
                      l.loan_date, l.due_date, l.status
               FROM loans l
               JOIN books b ON b.id = l.book_id
               JOIN readers r ON r.id = l.reader_id
               ORDER BY l.id DESC LIMIT 5"""
        ).fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/<entity>")
def list_records(entity):
    config = entity_or_404(entity)
    search = request.args.get("q", "")
    rows = list_sql(entity, search)
    return render_template(
        "list.html", entity=entity, config=config, rows=rows,
        search=search, columns=config["columns"],
    )


@app.route("/<entity>/new", methods=["GET", "POST"])
def create_record(entity):
    config = entity_or_404(entity)
    fields = decorate_fields(entity)
    if request.method == "POST":
        try:
            values = prepare_values(entity, request.form)
            save_record(entity, values)
            flash("Запись успешно создана.", "success")
            return redirect(url_for("list_records", entity=entity))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template(
        "form.html", entity=entity, config=config, fields=fields,
        record=None, heading=f"Добавить: {config['singular']}",
    )


@app.route("/<entity>/<int:record_id>/edit", methods=["GET", "POST"])
def edit_record(entity, record_id):
    config = entity_or_404(entity)
    record = get_record(entity, record_id)
    fields = decorate_fields(entity)
    if request.method == "POST":
        try:
            values = prepare_values(entity, request.form)
            save_record(entity, values, record_id)
            flash("Изменения сохранены.", "success")
            return redirect(url_for("list_records", entity=entity))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template(
        "form.html", entity=entity, config=config, fields=fields,
        record=record, heading=f"Редактировать: {config['singular']}",
    )


@app.route("/<entity>/<int:record_id>/delete", methods=["POST"])
def delete_record(entity, record_id):
    config = entity_or_404(entity)
    get_record(entity, record_id)
    try:
        with get_db() as conn:
            conn.execute(f"DELETE FROM {config['table']} WHERE id=?", (record_id,))
        flash("Запись удалена.", "success")
    except sqlite3.IntegrityError:
        flash("Нельзя удалить запись: она используется в связанных данных.", "error")
    return redirect(url_for("list_records", entity=entity))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


def create_app():
    """Application factory used by gunicorn / flask CLI / tests."""
    init_db()
    return app


if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")