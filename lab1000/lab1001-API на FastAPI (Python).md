# **Лабораторная работа 2. Часть 1: API на FastAPI (Python)**

## **Тема:** Разработка REST API с использованием FastAPI

### **Цель работы:**
Практическое знакомство с созданием RESTful API на современном Python-фреймворке FastAPI. Освоение принципов валидации данных, автоматической документации и асинхронной обработки запросов.

---

## **Задание: API для управления книгами в библиотеке**

Разработайте REST API для управления каталогом книг в библиотеке с использованием FastAPI, Pydantic и Python.

### **1. Настройка проекта**

Откройте терминал в Ubuntu и выполните:

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install fastapi uvicorn pydantic python-multipart
pip install pytest httpx  # для тестирования

# Создание структуры проекта
mkdir book_api
cd book_api
touch main.py models.py routers.py requirements.txt
```

Создайте файл `requirements.txt`:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
```

### **2. Базовое API (70% предоставляется)**

**Файл: `models.py`**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import date

# Enum для жанров книг
class Genre(str, Enum):
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    SCIENCE = "science"
    FANTASY = "fantasy"
    MYSTERY = "mystery"
    BIOGRAPHY = "biography"

# Модель для создания книги
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Название книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор книги")
    genre: Genre = Field(..., description="Жанр книги")
    publication_year: int = Field(..., ge=1000, le=date.today().year, description="Год публикации")
    pages: int = Field(..., gt=0, description="Количество страниц")
    isbn: str = Field(..., pattern=r'^\d{13}$', description="ISBN (13 цифр)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Война и мир",
                "author": "Лев Толстой",
                "genre": "fiction",
                "publication_year": 1869,
                "pages": 1225,
                "isbn": "9781234567897"
            }
        }

# Модель для обновления книги (все поля опциональны)
class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    genre: Optional[Genre] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=date.today().year)
    pages: Optional[int] = Field(None, gt=0)
    isbn: Optional[str] = Field(None, pattern=r'^\d{13}$')

# Модель для ответа (с идентификатором)
class BookResponse(BookCreate):
    id: int
    available: bool = True  # доступна ли книга для выдачи
    
    class Config:
        from_attributes = True

# Модель для ответа с деталями о заимствовании
class BookDetailResponse(BookResponse):
    borrowed_by: Optional[str] = None
    borrowed_date: Optional[date] = None
    return_date: Optional[date] = None

# Модель для запроса на заимствование книги
class BorrowRequest(BaseModel):
    borrower_name: str = Field(..., min_length=1, max_length=100)
    return_days: int = Field(7, ge=1, le=30, description="Количество дней на возврат")
```

**Файл: `main.py`**

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import uvicorn
from datetime import date, timedelta

from models import BookCreate, BookResponse, BookUpdate, BorrowRequest, BookDetailResponse, Genre
from routers import router as books_router

app = FastAPI(
    title="Book Library API",
    description="API для управления библиотекой книг",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS для доступа с разных доменов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер
app.include_router(books_router, prefix="/api/v1", tags=["books"])

# Имитация базы данных (в памяти)
books_db: Dict[int, dict] = {}
borrow_records: Dict[int, dict] = {}
current_id = 1

# Вспомогательные функции для работы с "БД"
def get_next_id() -> int:
    global current_id
    id_ = current_id
    current_id += 1
    return id_

def book_to_response(book_id: int, book_data: dict) -> BookResponse:
    """Преобразует данные книги в модель ответа"""
    return BookResponse(
        id=book_id,
        title=book_data["title"],
        author=book_data["author"],
        genre=book_data["genre"],
        publication_year=book_data["publication_year"],
        pages=book_data["pages"],
        isbn=book_data["isbn"],
        available=book_data.get("available", True)
    )

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Добро пожаловать в API библиотеки книг!",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "timestamp": date.today().isoformat()}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

### **3. Задания для самостоятельного выполнения (30% дописать)**

#### **A. Реализуйте CRUD операции в роутере** (обязательно)

**Файл: `routers.py`**

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date

from models import BookCreate, BookResponse, BookUpdate, BorrowRequest, BookDetailResponse, Genre

router = APIRouter()

# Импортируем "базу данных" из main.py
from main import books_db, borrow_records, get_next_id, book_to_response

# GET /books - получение списка всех книг с фильтрацией
@router.get("/books", response_model=List[BookResponse])
async def get_books(
    genre: Optional[Genre] = Query(None, description="Фильтр по жанру"),
    author: Optional[str] = Query(None, description="Фильтр по автору"),
    available_only: bool = Query(False, description="Только доступные книги"),
    skip: int = Query(0, ge=0, description="Количество книг для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит книг на странице")
):
    """
    Получить список книг с возможностью фильтрации.
    """
    filtered_books = []
    
    for book_id, book_data in books_db.items():
        # TODO: Реализуйте фильтрацию по genre
        # TODO: Реализуйте фильтрацию по author (регистронезависимый поиск)
        # TODO: Реализуйте фильтрацию по available_only
        
        # Если книга проходит все фильтры, добавляем её
        filtered_books.append(book_to_response(book_id, book_data))
    
    # TODO: Реализуйте пагинацию (skip и limit)
    
    return filtered_books

# GET /books/{book_id} - получение книги по ID
@router.get("/books/{book_id}", response_model=BookDetailResponse)
async def get_book(book_id: int):
    """
    Получить информацию о книге по её ID.
    """
    # TODO: Проверьте, существует ли книга с таким ID
    # Если нет - вызовите HTTPException со статусом 404
    
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
    
    # TODO: Если книга взята, добавьте информацию о заимствовании
    # из borrow_records в ответ
    
    return response

# POST /books - создание новой книги
@router.post("/books", response_model=BookResponse, status_code=201)
async def create_book(book: BookCreate):
    """
    Создать новую книгу в библиотеке.
    """
    # TODO: Проверьте, нет ли уже книги с таким ISBN
    # ISBN должен быть уникальным
    
    book_id = get_next_id()
    
    # TODO: Сохраните книгу в books_db
    # Не забудьте добавить поле available=True
    
    return book_to_response(book_id, books_db[book_id])

# PUT /books/{book_id} - полное обновление книги
@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, book_update: BookUpdate):
    """
    Обновить информацию о книге.
    """
    # TODO: Проверьте, существует ли книга с таким ID
    
    # TODO: Получите текущие данные книги
    
    # TODO: Обновите только переданные поля
    # Используйте dict(exclude_unset=True) для получения только переданных полей
    
    # TODO: Если передается ISBN, проверьте его уникальность
    
    # TODO: Сохраните обновленную книгу
    
    return book_to_response(book_id, books_db[book_id])

# DELETE /books/{book_id} - удаление книги
@router.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: int):
    """
    Удалить книгу из библиотеки.
    """
    # TODO: Проверьте, существует ли книга с таким ID
    
    # TODO: Проверьте, не взята ли книга (available=False)
    # Если книга взята, нельзя её удалить
    
    # TODO: Удалите книгу из books_db
    # TODO: Если есть запись о заимствовании, удалите и её
    
    return None
```

#### **B. Реализуйте эндпоинт для заимствования книги** (обязательно)

В тот же файл `routers.py` добавьте:

```python
# POST /books/{book_id}/borrow - заимствование книги
@router.post("/books/{book_id}/borrow", response_model=BookDetailResponse)
async def borrow_book(book_id: int, borrow_request: BorrowRequest):
    """
    Взять книгу из библиотеки.
    """
    # TODO: Проверьте, существует ли книга с таким ID
    
    # TODO: Проверьте, доступна ли книга (available=True)
    # Если нет - верните ошибку 400 с сообщением
    
    # TODO: Обновите статус книги на недоступную
    
    # TODO: Создайте запись о заимствовании в borrow_records
    # Запись должна содержать:
    # - borrower_name (имя взявшего)
    # - borrowed_date (сегодняшняя дата)
    # - return_date (сегодня + return_days дней)
    
    # TODO: Верните обновленную информацию о книге
    # с деталями заимствования
```

#### **C. Реализуйте эндпоинт для возврата книги** (обязательно)

```python
# POST /books/{book_id}/return - возврат книги
@router.post("/books/{book_id}/return", response_model=BookResponse)
async def return_book(book_id: int):
    """
    Вернуть книгу в библиотеку.
    """
    # TODO: Проверьте, существует ли книга с таким ID
    
    # TODO: Проверьте, взята ли книга (available=False)
    # Если книга не взята - верните ошибку 400
    
    # TODO: Обновите статус книги на доступную
    
    # TODO: Удалите запись о заимствовании из borrow_records
    
    # TODO: Верните обновленную информацию о книге
```

#### **D. Добавьте статистику по библиотеке** (дополнительно)

```python
# GET /stats - статистика библиотеки
@router.get("/stats")
async def get_library_stats():
    """
    Получить статистику библиотеки.
    """
    stats = {
        "total_books": 0,
        "available_books": 0,
        "borrowed_books": 0,
        "books_by_genre": {},
        "most_prolific_author": None
    }
    
    # TODO: Реализуйте подсчет статистики
    # 1. Общее количество книг
    # 2. Количество доступных книг
    # 3. Количество взятых книг
    # 4. Распределение книг по жанрам
    # 5. Автор с наибольшим количеством книг
    
    return stats
```

### **4. Запуск и тестирование API**

```bash
# Запуск сервера разработки
python main.py

# Или альтернативный способ
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API будет доступно по адресу:
# http://localhost:8000/docs - интерактивная документация Swagger UI
# http://localhost:8000/redoc - альтернативная документация ReDoc
```

**Тестирование через curl:**
```bash
# Получить все книги
curl -X GET "http://localhost:8000/api/v1/books"

# Создать новую книгу
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Преступление и наказание",
    "author": "Фёдор Достоевский",
    "genre": "fiction",
    "publication_year": 1866,
    "pages": 671,
    "isbn": "9781234567898"
  }'

# Взять книгу
curl -X POST "http://localhost:8000/api/v1/books/1/borrow" \
  -H "Content-Type: application/json" \
  -d '{"borrower_name": "Иван Иванов", "return_days": 14}'
```

### **5. Что должно быть в отчёте:**

1. **Исходный код:**
   - Полные файлы `routers.py` и `models.py` с вашими дополнениями
   - Примеры запросов и ответов API

2. **Скриншоты:**
   - Интерфейс Swagger UI с документацией вашего API
   - Успешное создание книги (POST /books)
   - Успешное заимствование книги
   - Обработка ошибок (например, попытка удалить взятую книгу)

3. **Ответы на вопросы:**
   - В чем преимущества использования Pydantic моделей для валидации?
   - Как работает автоматическая документация в FastAPI?
   - Почему важно проверять уникальность ISBN?
   - Какие статус-коды HTTP вы использовали и почему?

### **6. Критерии оценивания:**

#### **Обязательные требования (минимум для зачета):**
- **CRUD операции:** Реализованы все CRUD операции (GET, POST, PUT, DELETE)
- **Заимствование и возврат:** Работают эндпоинты borrow и return
- **Валидация данных:** Правильная обработка и валидация входных данных
- **Обработка ошибок:** Корректные HTTP статус-коды и сообщения об ошибках
- **API работает:** Все эндпоинты доступны и работают через Swagger UI

#### **Дополнительные критерии (для повышения оценки):**
- **Статистика:** Реализован эндпоинт /stats с подсчетом метрик библиотеки
- **Фильтрация:** Полноценная работа фильтров в GET /books
- **Тесты:** Написаны автоматические тесты для API (используя pytest)
- **Качество кода:** Чистый, документированный код с типами Python

#### **Неприемлемые ошибки:**
- Нарушение уникальности ISBN
- Возможность удалить взятую книгу
- Отсутствие проверки существования книги
- Критические ошибки при запуске API

### **7. Полезные команды для Ubuntu:**

```bash
# Активация виртуального окружения
source venv/bin/activate

# Проверка установленных пакетов
pip list

# Запуск с подробным логированием
uvicorn main:app --reload --log-level debug

# Тестирование с помощью HTTPie (альтернатива curl)
pip install httpie
http GET http://localhost:8000/api/v1/books
```

### **8. Структура проекта:**

```
book_api/
├── main.py              # Основное приложение FastAPI
├── models.py            # Pydantic модели данных
├── routers.py           # Роутер с эндпоинтами API
├── requirements.txt     # Зависимости проекта
├── tests/               # Тесты (опционально)
│   └── test_api.py
└── venv/                # Виртуальное окружение
```

### **9. Советы по выполнению:**

1. **Начните с простого:** Сначала реализуйте базовые CRUD операции без фильтрации
2. **Тестируйте через Swagger UI:** Визуальный интерфейс упрощает отладку
3. **Обрабатывайте крайние случаи:** Что если книга уже взята? Что если ISBN не уникален?
4. **Используйте типы Python:** Это поможет избежать многих ошибок
5. **Читайте сообщения об ошибках:** FastAPI дает подробные сообщения при ошибках валидации

**Примечание:** В задании предоставлено ~70% кода. Ваша задача — понять логику FastAPI и дописать недостающие ~30% эндпоинтов, следуя принципам REST и хорошим практикам разработки API.
