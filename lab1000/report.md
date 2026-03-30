# **Отчет по лабораторной работе №1: API на FastAPI (Python) и API на Express (Node.js)**

## Сведения о студенте  
**Дата:** 2026-02-26  
**Семестр:** 2 курс, 2 семестр  
**Группа:** Пин-б-о-24-1  
**Дисциплина:** Технологии программирования  
**Студент:** Куйбышев Александр Максимович

---

## Цель работы

**Часть 1:** Практическое знакомство с созданием RESTful API на современном Python-фреймворке FastAPI. Освоение принципов валидации данных с помощью Pydantic, автоматической документации (Swagger UI / ReDoc) и асинхронной обработки HTTP-запросов. Разработка API для управления каталогом книг в библиотеке с реализацией CRUD-операций, заимствования/возврата книг и сбора статистики.

**Часть 2:** Практическое знакомство с созданием RESTful API на Node.js с использованием Express. Освоение middleware, валидации данных через Joi, работы с файловой системой для хранения данных и сравнение подходов разных фреймворков. Разработка API для управления задачами (Task Manager) с фильтрацией, сортировкой, пагинацией и полнотекстовым поиском.

---

### Часть 1: API библиотеки книг (book_api)

#### Структура проекта

```
book_api/
├── main.py          # FastAPI-приложение, CORS, подключение роутера
├── models.py        # Pydantic-модели: Genre, BookCreate, BookUpdate, BookResponse и др.
├── database.py      # Общее состояние: books_db, borrow_records, get_next_id()
├── routers.py       # 8 эндпоинтов API
└── requirements.txt # Зависимости 
```

#### Выполненные задачи

1. Настройка проекта(созданы файлы и настроен cors и swagger ui)
2. GET /books — список с фильтрацией и пагинацией
3. GET /books/{id} — книга по id (`HTTPException(404)` при отсутствии книги)
4. POST /books — создание книги (проверка уникальности isbn (если дубликат — `HTTPException(409 Conflict)`))
5. PUT /books/{id} — обновление книги (`HTTPException(404)` при отсутствии книги и проверка isbn при изменении)
6. DELETE /books/{id} — удаление книги (`HTTPException(404)` при отсутствии и `HTTPException(400)` при попытке удалить взятую книгу)
7. POST /books/{id}/borrow — взять книгу (`HTTPException(404)` при отсутствии и `HTTPException(400)` при попытке взять уже взятую книгу)
8. POST /books/{id}/return — вернуть книгу ((`HTTPException(404)` при отсутствии и `HTTPException(400)` при попытке вернуть не взятую книгу))
9. GET /stats — статистика (общее кол-во, количество изданий у автора)

#### Ключевые фрагменты кода (Часть 1)

**Фильтрация и пагинация (GET /books):**
```py
for book_id, book_data in books_db.items():
    if genre is not None and book_data["genre"] != genre:
        continue
    if author is not None and author.lower() not in book_data["author"].lower():
        continue
    if available_only and not book_data.get("available", True):
        continue
    filtered_books.append(book_to_response(book_id, book_data))

return filtered_books[skip: skip + limit]
```

**Заимствование книги (POST /books/{id}/borrow):**
```py
books_db[book_id]["available"] = False
today = date.today()
borrow_records[book_id] = {
    "borrower_name": borrow_request.borrower_name,
    "borrowed_date": today,
    "return_date": today + timedelta(days=borrow_request.return_days)
}
```

**Статистика (GET /stats):**
```py
genre_counter: Counter = Counter(b["genre"] for b in books_db.values())
author_counter: Counter = Counter(b["author"] for b in books_db.values())
most_prolific_author = author_counter.most_common(1)[0][0] if author_counter else None
```

---

### Часть 2: Task Manager API (task-api)

#### Структура проекта

```
task-api/
├── src/
│   ├── app.js                   # Express-приложение, middleware, маршруты
│   ├── server.js                # Запуск сервера
│   ├── routes/
│   │   └── tasks.js             # Эндпоинты задач
│   ├── middleware/
│   │   ├── validation.js        # Joi-схемы и middleware валидации
│   │   └── errorHandler.js      # 404 и общие ошибки
│   └── utils/
│       └── fileOperations.js    # Чтение и запись tasks.json
└── package.json
```

#### Выполненные задачи

1. Настройка проекта (`package.json` с зависимостями(express, cors, helmet, joi, uuid, express-rate-limit, dotenv))
2. GET /api/tasks — список с фильтрацией, сортировкой, пагинацией
3. GET /api/tasks/:id — задача по ID (`validateId` middleware проверяет корректность числового ID)
4. POST /api/tasks — создание задачи (через `validateCreateTask`)
5. PUT /api/tasks/:id — обновление задачи (404 при отсутствии, слияние `updates` с существующей задачей через spread-оператор)
6. PATCH /api/tasks/:id/complete — отметить выполненной (404 при отсутствии; устанавливает `completed: true` и `updatedAt`)
7. DELETE /api/tasks/:id — удаление (404 при отсутствии; удаляет элемент через `splice()`, сохраняет через `writeData()`)
8. GET /api/tasks/stats/summary — статистика (подсчёт: `total`, `completed`, `pending`, `overdue`, распределение по категориям и приоритетам)
9. GET /api/tasks/search/text — поиск (минимум 2 символа, регист не важен)
10. GET / и GET /health в app.js (информация об api)

#### Ключевые фрагменты кода (Часть 2)

**Фильтрация, сортировка, пагинация (GET /api/tasks):**
```js
if (sortBy) {
  const descending = sortBy.startsWith('-');
  const field = descending ? sortBy.slice(1) : sortBy;
  tasks.sort((a, b) => {
    let valA = a[field];
    let valB = b[field];
    if (field === 'dueDate' || field === 'createdAt') {
      valA = valA ? new Date(valA).getTime() : 0;
      valB = valB ? new Date(valB).getTime() : 0;
    }
    if (valA < valB) return descending ? 1 : -1;
    if (valA > valB) return descending ? -1 : 1;
    return 0;
  });
}

const pageNum = parseInt(page) || 1;
const limitNum = parseInt(limit) || 10;
const startIndex = (pageNum - 1) * limitNum;
const paginated = tasks.slice(startIndex, startIndex + limitNum);
```

**Статистика (GET /api/tasks/stats/summary):**
```js
for (const task of tasks) {
  if (task.completed) {
    stats.completed++;
  } else {
    stats.pending++;
    if (task.dueDate && new Date(task.dueDate) < now) {
      stats.overdue++;
    }
  }
  stats.byCategory[task.category] = (stats.byCategory[task.category] || 0) + 1;
  stats.byPriority[task.priority]++;
}
```

---

## Результаты выполнения

### Часть 1: FastAPI (book_api)

**Эндпоинты API:**

| Метод | Маршрут | Описание | Статус-коды |
|---|---|---|---|
| GET | `/api/v1/books` | Список книг с фильтрами | 200 |
| GET | `/api/v1/books/{id}` | Книга по ID | 200, 404 |
| POST | `/api/v1/books` | Создать книгу | 201, 409 |
| PUT | `/api/v1/books/{id}` | Обновить книгу | 200, 404, 409 |
| DELETE | `/api/v1/books/{id}` | Удалить книгу | 204, 400, 404 |
| POST | `/api/v1/books/{id}/borrow` | Взять книгу | 200, 400, 404 |
| POST | `/api/v1/books/{id}/return` | Вернуть книгу | 200, 400, 404 |
| GET | `/api/v1/stats` | Статистика библиотеки | 200 |

**Примеры ответов:**

Создание книги (`POST /api/v1/books`):
```json
{
  "id": 1,
  "title": "Преступление и наказание",
  "author": "Фёдор Достоевский",
  "genre": "fiction",
  "publication_year": 1866,
  "pages": 671,
  "isbn": "9781234567898",
  "available": true
}
```

Заимствование книги (`POST /api/v1/books/1/borrow`):
```json
{
  "id": 1,
  "title": "Преступление и наказание",
  "available": false,
  "borrowed_by": "Иван Иванов",
  "borrowed_date": "2026-03-04",
  "return_date": "2026-03-18"
}
```

Статистика (`GET /api/v1/stats`):
```json
{
  "total_books": 3,
  "available_books": 2,
  "borrowed_books": 1,
  "books_by_genre": { "fiction": 2, "science": 1 },
  "most_prolific_author": "Фёдор Достоевский"
}
```

Ошибка удаления взятой книги (`DELETE /api/v1/books/1`):
```json
{
  "detail": "Невозможно удалить книгу, которая сейчас взята читателем"
}
```

### Часть 2: Express (task-api)

**Эндпоинты API:**

| Метод | Маршрут | Описание | Статус-коды |
|---|---|---|---|
| GET | `/api/tasks` | Список задач (фильтры, сортировка, пагинация) | 200 |
| GET | `/api/tasks/:id` | Задача по ID | 200, 404 |
| POST | `/api/tasks` | Создать задачу | 201, 400 |
| PUT | `/api/tasks/:id` | Обновить задачу | 200, 400, 404 |
| PATCH | `/api/tasks/:id/complete` | Отметить выполненной | 200, 404 |
| DELETE | `/api/tasks/:id` | Удалить задачу | 200, 404 |
| GET | `/api/tasks/stats/summary` | Статистика | 200 |
| GET | `/api/tasks/search/text?q=` | Поиск по тексту | 200, 400 |
| GET | `/` | Информация об API | 200 |
| GET | `/health` | Проверка работоспособности | 200 |

**Примеры ответов:**

Создание задачи (`POST /api/tasks`):
```json
{
  "success": true,
  "message": "Задача успешно создана",
  "data": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Купить продукты",
    "description": "Молоко, хлеб, яйца",
    "category": "shopping",
    "priority": 2,
    "dueDate": "2026-04-01T00:00:00.000Z",
    "completed": false,
    "createdAt": "2026-03-04T10:00:00.000Z",
    "updatedAt": "2026-03-04T10:00:00.000Z"
  }
}
```

Статистика (`GET /api/tasks/stats/summary`):
```json
{
  "success": true,
  "data": {
    "total": 5,
    "completed": 2,
    "pending": 3,
    "overdue": 1,
    "byCategory": { "work": 2, "personal": 2, "shopping": 1 },
    "byPriority": { "1": 0, "2": 1, "3": 3, "4": 1, "5": 0 }
  }
}
```

---

## Ответы на контрольные вопросы

### Часть 1 (FastAPI)

#### **В чём преимущества использования Pydantic моделей для валидации?**

**Ответ:**  
Pydantic позволяет описывать схему данных прямо в коде Python через аннотации типов. Преимущества: автоматическая валидация при создании объекта, понятные сообщения об ошибках, сериализация/десериализация JSON, генерация JSON-схемы (используется FastAPI для документации), работа с `Optional`, вложенными объектами и перечислениями.

#### **Как работает автоматическая документация в FastAPI?**

**Ответ:**  
FastAPI при старте приложения анализирует все зарегистрированные маршруты, типы параметров и `response_model` через рефлексию Python. На основе этих данных автоматически генерируется OpenAPI-схема (JSON). Swagger UI (`/docs`) и ReDoc (`/redoc`) отображают эту схему как интерактивную документацию, где можно выполнять запросы прямо из браузера.

#### **Почему важно проверять уникальность ISBN?**

**Ответ:**  
ISBN (International Standard Book Number) — уникальный идентификатор книги. Дублирование ISBN привело бы к неоднозначности: невозможно точно идентифицировать экземпляр, статус доступности стал бы некорректным, операции поиска и заимствования вернули бы неверные данные. В реальных системах уникальность ISBN обеспечивается на уровне БД (`UNIQUE` constraint).

#### **Какие HTTP статус-коды использовались и почему?**

**Ответ:**  
- `200 OK` — успешный GET или POST (borrow/return)
- `201 Created` — успешное создание ресурса (POST /books)
- `204 No Content` — успешное удаление (DELETE), тело ответа не нужно
- `400 Bad Request` — некорректный запрос (попытка взять уже взятую книгу, удалить взятую)
- `404 Not Found` — ресурс не найден по переданному ID
- `409 Conflict` — конфликт уникальности (дублирование ISBN)

### Часть 2 (Express / Node.js)

#### **Какие middleware вы использовали и для чего?**

**Ответ:**  
- `helmet` — установка HTTP-заголовков безопасности (X-Content-Type-Options, X-Frame-Options и др.)
- `cors` — настройка политики CORS для разрешения запросов с других доменов
- `express-rate-limit` — ограничение числа запросов с одного IP (100 запросов за 15 минут)
- `express.json()` — парсинг тела запроса из JSON в JavaScript-объект
- `validateCreateTask`, `validateUpdateTask` — валидация входных данных через Joi
- `validateId` — проверка, что параметр `:id` является положительным числом
- `notFoundHandler`, `errorHandler` — централизованная обработка ошибок

#### **Как работает валидация с Joi в сравнении с Pydantic?**

**Ответ:**  
Инструменты декларативно описывают схему и возвращают ошибки при несоответствии. Различия: Pydantic использует аннотации Python-типов и работает на уровне классов (модели используются и как схема, и как тип данных); Joi — JavaScript-библиотека для рантайм-валидации, схемы — это обычные объекты, их нужно явно применять через `schema.validate()`. Pydantic встроен в FastAPI и автоматически генерирует документацию; для Joi документацию нужно писать вручную.

#### **В чём преимущества файлового хранения для этого задания?**

**Ответ:**  
Простота развёртывания (не нужна СУБД), данные сохраняются между перезапусками сервера, файл можно легко прочитать и отредактировать вручную, минимальные накладные расходы для небольшого учебного проекта. Недостатки: нет поддержки параллельного доступа, нет транзакций, плохая масштабируемость при большом объёме данных.

#### **Как бы вы улучшили это API для production?**

**Ответ:**  
Заменить файловое хранилище на реляционную БД (PostgreSQL) или документоориентированную (MongoDB); добавить аутентификацию и авторизацию (JWT); использовать переменные окружения для конфигурации; настроить централизованное логирование (Winston/Pino); добавить автоматические тесты (Jest + Supertest); применить Docker и CI/CD; включить сжатие ответов (`compression` middleware).

---

## Приложения

### Приложение 1: Исходный код routers.py (book_api)

```python
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import date, timedelta
from collections import Counter

from models import BookCreate, BookResponse, BookUpdate, BorrowRequest, BookDetailResponse, Genre
from database import books_db, borrow_records, get_next_id, book_to_response

router = APIRouter()


@router.get("/books", response_model=List[BookResponse])
async def get_books(
    genre: Optional[Genre] = Query(None, description="Фильтр по жанру"),
    author: Optional[str] = Query(None, description="Фильтр по автору"),
    available_only: bool = Query(False, description="Только доступные книги"),
    skip: int = Query(0, ge=0, description="Количество книг для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит книг на странице")
):
    """Получить список книг с возможностью фильтрации."""
    filtered_books: List[BookResponse] = []

    for book_id, book_data in books_db.items():
        if genre is not None and book_data["genre"] != genre:
            continue
        if author is not None and author.lower() not in book_data["author"].lower():
            continue
        if available_only and not book_data.get("available", True):
            continue
        filtered_books.append(book_to_response(book_id, book_data))

    return filtered_books[skip: skip + limit]


@router.get("/books/{book_id}", response_model=BookDetailResponse)
async def get_book(book_id: int):
    """Получить информацию о книге по её ID."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    book_data = books_db[book_id]
    response = BookDetailResponse(
        id=book_id,
        title=book_data["title"],
        author=book_data["author"],
        genre=book_data["genre"],
        publication_year=book_data["publication_year"],
        pages=book_data["pages"],
        isbn=book_data["isbn"],
        available=book_data.get("available", True)
    )

    if not book_data.get("available", True) and book_id in borrow_records:
        record = borrow_records[book_id]
        response.borrowed_by = record["borrower_name"]
        response.borrowed_date = record["borrowed_date"]
        response.return_date = record["return_date"]

    return response


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate):
    """Создать новую книгу в библиотеке."""
    for existing in books_db.values():
        if existing["isbn"] == book.isbn:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Книга с ISBN {book.isbn} уже существует"
            )

    book_id = get_next_id()
    books_db[book_id] = {
        "title": book.title,
        "author": book.author,
        "genre": book.genre,
        "publication_year": book.publication_year,
        "pages": book.pages,
        "isbn": book.isbn,
        "available": True
    }

    return book_to_response(book_id, books_db[book_id])


@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, book_update: BookUpdate):
    """Обновить информацию о книге."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    current_data = books_db[book_id]
    updates = book_update.model_dump(exclude_unset=True)

    if "isbn" in updates and updates["isbn"] != current_data["isbn"]:
        for existing_id, existing in books_db.items():
            if existing_id != book_id and existing["isbn"] == updates["isbn"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Книга с ISBN {updates['isbn']} уже существует"
                )

    current_data.update(updates)
    books_db[book_id] = current_data

    return book_to_response(book_id, books_db[book_id])


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int):
    """Удалить книгу из библиотеки."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    if not books_db[book_id].get("available", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно удалить книгу, которая сейчас взята читателем"
        )

    del books_db[book_id]
    borrow_records.pop(book_id, None)

    return None


@router.post("/books/{book_id}/borrow", response_model=BookDetailResponse)
async def borrow_book(book_id: int, borrow_request: BorrowRequest):
    """Взять книгу из библиотеки."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    if not books_db[book_id].get("available", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Книга уже взята другим читателем"
        )

    books_db[book_id]["available"] = False

    today = date.today()
    borrow_records[book_id] = {
        "borrower_name": borrow_request.borrower_name,
        "borrowed_date": today,
        "return_date": today + timedelta(days=borrow_request.return_days)
    }

    record = borrow_records[book_id]
    book_data = books_db[book_id]
    return BookDetailResponse(
        id=book_id,
        title=book_data["title"],
        author=book_data["author"],
        genre=book_data["genre"],
        publication_year=book_data["publication_year"],
        pages=book_data["pages"],
        isbn=book_data["isbn"],
        available=False,
        borrowed_by=record["borrower_name"],
        borrowed_date=record["borrowed_date"],
        return_date=record["return_date"]
    )


@router.post("/books/{book_id}/return", response_model=BookResponse)
async def return_book(book_id: int):
    """Вернуть книгу в библиотеку."""
    if book_id not in books_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    if books_db[book_id].get("available", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Книга не является взятой — вернуть невозможно"
        )

    books_db[book_id]["available"] = True
    borrow_records.pop(book_id, None)

    return book_to_response(book_id, books_db[book_id])


@router.get("/stats")
async def get_library_stats():
    """Получить статистику библиотеки."""
    total_books = len(books_db)
    available_books = sum(1 for b in books_db.values() if b.get("available", True))
    borrowed_books = total_books - available_books

    genre_counter: Counter = Counter(b["genre"] for b in books_db.values())
    books_by_genre = dict(genre_counter)

    author_counter: Counter = Counter(b["author"] for b in books_db.values())
    most_prolific_author: Optional[str] = author_counter.most_common(1)[0][0] if author_counter else None

    return {
        "total_books": total_books,
        "available_books": available_books,
        "borrowed_books": borrowed_books,
        "books_by_genre": books_by_genre,
        "most_prolific_author": most_prolific_author
    }
```

---

### Приложение 2: Исходный код src/routes/tasks.js (task-api)

```javascript
const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const { validateCreateTask, validateUpdateTask, validateId } = require('../middleware/validation');
const { initializeDataFile, readData, writeData, getNextId } = require('../utils/fileOperations');

initializeDataFile();

// GET /api/tasks/stats/summary — регистрируется ДО /:id
router.get('/stats/summary', async (req, res, next) => {
  try {
    const data = await readData();
    const tasks = data.tasks;
    const now = new Date();

    const stats = {
      total: tasks.length,
      completed: 0,
      pending: 0,
      overdue: 0,
      byCategory: {},
      byPriority: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
    };

    for (const task of tasks) {
      if (task.completed) {
        stats.completed++;
      } else {
        stats.pending++;
        if (task.dueDate && new Date(task.dueDate) < now) stats.overdue++;
      }
      stats.byCategory[task.category] = (stats.byCategory[task.category] || 0) + 1;
      if (task.priority >= 1 && task.priority <= 5) stats.byPriority[task.priority]++;
    }

    res.json({ success: true, data: stats });
  } catch (error) { next(error); }
});

// GET /api/tasks/search/text — регистрируется ДО /:id
router.get('/search/text', async (req, res, next) => {
  try {
    const { q } = req.query;
    if (!q || q.trim().length < 2) {
      return res.status(400).json({ success: false, error: 'Запрос должен содержать минимум 2 символа' });
    }
    const data = await readData();
    const searchTerm = q.toLowerCase().trim();
    const results = data.tasks.filter(task =>
      (task.title && task.title.toLowerCase().includes(searchTerm)) ||
      (task.description && task.description.toLowerCase().includes(searchTerm))
    );
    res.json({ success: true, count: results.length, data: results });
  } catch (error) { next(error); }
});

// GET /api/tasks — список с фильтрацией, сортировкой, пагинацией
router.get('/', async (req, res, next) => {
  try {
    const { category, completed, priority, sortBy, page, limit } = req.query;
    const data = await readData();
    let tasks = [...data.tasks];

    if (category) tasks = tasks.filter(t => t.category === category);
    if (completed !== undefined) tasks = tasks.filter(t => t.completed === (completed === 'true'));
    if (priority !== undefined) {
      const p = parseInt(priority);
      if (!isNaN(p)) tasks = tasks.filter(t => t.priority === p);
    }
    if (sortBy) {
      const desc = sortBy.startsWith('-');
      const field = desc ? sortBy.slice(1) : sortBy;
      tasks.sort((a, b) => {
        let va = a[field], vb = b[field];
        if (field === 'dueDate' || field === 'createdAt') {
          va = va ? new Date(va).getTime() : 0;
          vb = vb ? new Date(vb).getTime() : 0;
        }
        if (va < vb) return desc ? 1 : -1;
        if (va > vb) return desc ? -1 : 1;
        return 0;
      });
    }

    const pageNum = parseInt(page) || 1;
    const limitNum = parseInt(limit) || 10;
    const paginated = tasks.slice((pageNum - 1) * limitNum, pageNum * limitNum);

    res.json({ success: true, count: paginated.length, total: tasks.length,
      page: pageNum, totalPages: Math.ceil(tasks.length / limitNum), data: paginated });
  } catch (error) { next(error); }
});
```

---

### **Запуск**

#### Часть 1: FastAPI (book_api)

```bash
cd lab-11/book_api
python -m venv venv
source venv/bin/activate      # Linux/Mac
# или: venv\Scripts\activate  # Windows

pip install -r requirements.txt
python main.py
```

API будет доступно по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Эндпоинты: http://localhost:8000/api/v1/books

Примеры запросов:
```bash
# Создать книгу
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{"title":"Война и мир","author":"Лев Толстой","genre":"fiction","publication_year":1869,"pages":1225,"isbn":"9781234567897"}'

# Взять книгу
curl -X POST "http://localhost:8000/api/v1/books/1/borrow" \
  -H "Content-Type: application/json" \
  -d '{"borrower_name":"Иван Иванов","return_days":14}'

# Статистика
curl http://localhost:8000/api/v1/stats
```

#### Часть 2: Express (task-api)

```bash
cd lab-11/task-api
npm install
npm run dev
```

API будет доступно по адресу: http://localhost:3000

Примеры запросов:
```bash
# Создать задачу
curl -X POST "http://localhost:3000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title":"Купить продукты","category":"shopping","priority":2}'

# Список с фильтром и сортировкой
curl "http://localhost:3000/api/tasks?category=work&sortBy=-priority&page=1&limit=5"

# Статистика
curl http://localhost:3000/api/tasks/stats/summary

# Поиск
curl "http://localhost:3000/api/tasks/search/text?q=купить"
```
