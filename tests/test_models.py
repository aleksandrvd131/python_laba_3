
from dataclasses import FrozenInstanceError

import pytest

from book_catalog.exceptions import InvalidEntityError
from book_catalog.models import Book

VALID_BOOK_DATA = {
    "id": "B-1",
    "name": "Книга",
    "category": "Жанр",
    "year": 2020,
    "author": "Автор",
    "pages": 100,
}


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
    ("field_desc", "overrides"),
    [
        ("Пустой id", {"id": ""}),
        ("Пробельный id", {"id": "   "}),
        ("Нестроковый id", {"id": 123}),
        ("Пустое название", {"name": ""}),
        ("Пробельное название", {"name": " \t "}),
        ("Пустая категория", {"category": ""}),
        ("Пустой автор", {"author": "  "}),
        ("Слишком ранний год", {"year": 1200}),
        ("Год из далекого будущего", {"year": 3000}),
        ("Год как bool True", {"year": True}),
        ("Год как строка", {"year": "2020"}),
        ("Нулевые страницы", {"pages": 0}),
        ("Отрицательные страницы", {"pages": -50}),
        ("Страницы как float", {"pages": 120.5}),
        ("Страницы как bool True", {"pages": True}),
    ],
)
def test_create_invalid_book_raises(field_desc: str, overrides: dict) -> None:
    data = {**VALID_BOOK_DATA, **overrides}
    with pytest.raises(InvalidEntityError):
        Book(**data)


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
        Book.from_dict(
            {
                "id": "B-1",
                "name": "Книга",
                "category": "Жанр",
                "year": 2020,
                "author": "Автор",
                "pages": 100,
                "extra": "значение",
            }
        )
