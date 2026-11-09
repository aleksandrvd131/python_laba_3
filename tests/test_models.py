from dataclasses import FrozenInstanceError
import pytest
from book_catalog import Book, InvalidEntityError


def test_create_valid_book() -> None:
    book = Book(
        id="B-100",
        name="Преступление и наказание",
        category="Классика",
        year=1866,
        author="Фёдор Достоевский",
        pages=672,
    )
    assert book.id == "B-100"
    assert book.name == "Преступление и наказание"
    assert book.category == "Классика"
    assert book.year == 1866
    assert book.author == "Фёдор Достоевский"
    assert book.pages == 672


@pytest.mark.parametrize(
    ("field_desc", "kwargs"),
    [
        ("Пустой id", {"id": "", "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 100}),
        ("Пробельный id", {"id": "   ", "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 100}),
        ("Нестроковый id", {"id": 123, "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 100}),
        ("Пустое название", {"id": "B-1", "name": "", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 100}),
        ("Пробельное название", {"id": "B-1", "name": " \t ", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 100}),
        ("Пустая категория", {"id": "B-1", "name": "Книга", "category": "", "year": 2020, "author": "Автор", "pages": 100}),
        ("Пустой автор", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 2020, "author": "  ", "pages": 100}),
        ("Слишком ранний год", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 1200, "author": "Автор", "pages": 100}),
        ("Год из далекого будущего", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 3000, "author": "Автор", "pages": 100}),
        ("Год как bool True", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": True, "author": "Автор", "pages": 100}),
        ("Год как строка", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": "2020", "author": "Автор", "pages": 100}),
        ("Нулевые страницы", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 0}),
        ("Отрицательные страницы", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": -50}),
        ("Страницы как float", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": 120.5}),
        ("Страницы как bool True", {"id": "B-1", "name": "Книга", "category": "Жанр", "year": 2020, "author": "Автор", "pages": True}),
    ],
)
def test_create_invalid_book_raises(field_desc: str, kwargs: dict) -> None:
    with pytest.raises(InvalidEntityError):
        Book(**kwargs)


def test_book_immutability() -> None:
    book = Book(
        id="B-1",
        name="Книга",
        category="Жанр",
        year=2020,
        author="Автор",
        pages=100,
    )
    with pytest.raises(FrozenInstanceError):
        book.name = "Новое название"  # type: ignore[misc]


def test_book_to_dict_and_from_dict() -> None:
    original = Book(
        id="B-42",
        name="Автостопом по галактике",
        category="Фантастика",
        year=1979,
        author="Дуглас Адамс",
        pages=224,
    )
    data = original.to_dict()
    assert data == {
        "id": "B-42",
        "name": "Автостопом по галактике",
        "category": "Фантастика",
        "year": 1979,
        "author": "Дуглас Адамс",
        "pages": 224,
    }

    reconstructed = Book.from_dict(data)
    assert reconstructed == original


def test_from_dict_invalid_data() -> None:
    with pytest.raises(InvalidEntityError):
        Book.from_dict("не словарь")

    with pytest.raises(InvalidEntityError):
        Book.from_dict({"id": "B-1", "name": "Неполная схема"})

    with pytest.raises(InvalidEntityError):
        # Лишнее поле
        Book.from_dict({
            "id": "B-1",
            "name": "Книга",
            "category": "Жанр",
            "year": 2020,
            "author": "Автор",
            "pages": 100,
            "extra": "значение",
        })
