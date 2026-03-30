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
