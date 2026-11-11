import os
from app import get_db, init_db

def seed_data():
    # Инициализируем таблицы (если их нет)
    init_db()
    
    with get_db() as conn:
        # Проверяем, есть ли уже данные в таблице авторов
        count = conn.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
        if count > 0:
            print("База данных уже содержит данные. Пропускаем заполнение.")
            return

        print("Заполняем базу тестовыми данными...")

        # 1. Добавляем авторов
        authors = [
            ("Лев Толстой", "Россия", 1828),
            ("Фёдор Достоевский", "Россия", 1821),
            ("Джордж Оруэлл", "Великобритания", 1903)
        ]
        conn.executemany("INSERT INTO authors (full_name, country, birth_year) VALUES (?, ?, ?)", authors)

        # 2. Добавляем жанры
        genres = [
            ("Роман", "Крупное прозаическое произведение"),
            ("Антиутопия", "Жанр художественной литературы"),
            ("Классика", "Образцовые произведения")
        ]
        conn.executemany("INSERT INTO genres (name, description) VALUES (?, ?)", genres)

        # 3. Добавляем книги
        books = [
            ("Война и мир", 1, 1, "978-5-00-000000-1", 1869, 5, 5, "Эпопея"),
            ("Преступление и наказание", 2, 1, "978-5-00-000000-2", 1866, 3, 3, "Психологический роман"),
            ("1984", 3, 2, "978-5-00-000000-3", 1949, 4, 4, "Антиутопия о тоталитаризме")
        ]
        conn.executemany("""INSERT INTO books (title, author_id, genre_id, isbn, year, copies_total, copies_available, description) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", books)

        # 4. Добавляем читателей
        readers = [
            ("Иван Иванов", "+7 900 111-22-33", "ivan@example.com", "CARD-001"),
            ("Мария Петрова", "+7 900 444-55-66", "maria@example.com", "CARD-002")
        ]
        conn.executemany("INSERT INTO readers (full_name, phone, email, library_card) VALUES (?, ?, ?, ?)", readers)

        # 5. Добавляем выдачи
        loans = [
            (1, 1, "2026-10-01", "2026-10-15", "", "Выдана", "Книга в отличном состоянии"),
            (3, 2, "2026-10-05", "2026-10-20", "", "Выдана", "")
        ]
        conn.executemany("""INSERT INTO loans (book_id, reader_id, loan_date, due_date, returned_date, status, notes) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)""", loans)

        print("Тестовые данные успешно добавлены!")

if __name__ == "__main__":
    seed_data()