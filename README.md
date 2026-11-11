# Библиотечная система (Flask + SQLite + Docker + Jenkins)

Учебный проект по дисциплине «Методология CI/CD».
Предметная область — библиотека книг: книги, авторы, жанры, читатели, выдачи.
Реализовано 5 сущностей × 4 CRUD-операции = 20 операций.

## Стек
- Python 3.12, Flask 3
- SQLite (стандартный модуль `sqlite3`)
- pytest (10 тестов)
- Docker + docker-compose + nginx (reverse proxy)
- Jenkins (Declarative Pipeline)

## Локальный запуск
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
flask --app app run --debug
```
Приложение: http://127.0.0.1:5000

## Тесты
```bash
pytest -v
```

## Запуск в Docker
```bash
docker compose up -d --build
```
Приложение: http://127.0.0.1:8080

## CI/CD
- `dev` и `feature/*` → стадии Checkout → Install → Test (CI).
- `main` → дополнительно Build Docker Image → Deploy (CD).
- Триггер: GitHub webhook `http://<jenkins>:8080/github-webhook/`.

## Ветки
- `main` — стабильная версия, деплой.
- `dev` — интеграционная ветка.
- `feature/library-entities` — переделка под библиотеку.