import pytest

from book_catalog.catalog import BookCatalog
from book_catalog.models import Book


@pytest.fixture
def sample_books() -> list[Book]:
    """Возвращает список тестовых книг с намеренно перемешанными ID"""
    return [
        Book(
            id="B-002",
            name="Чистый код",
            category="Программирование",
            year=2019,
            author="Роберт Мартин",
            pages=464,
        ),
        Book(
            id="B-001",
            name="Алгоритмы. Построение и анализ",
            category="Программирование",
            year=2022,
            author="Томас Кормен",
            pages=1328,
        ),
        Book(
            id="B-003",
            name="Мастер и Маргарита",
            category="Художественная литература",
            year=1967,
            author="Михаил Булгаков",
            pages=480,
        ),
        Book(
            id="B-004",
            name="Пикник на обочине",
            category="Фантастика",
            year=1972,
            author="Аркадий и Борис Стругацкие",
            pages=256,
        ),
    ]


@pytest.fixture
def filled_catalog(sample_books: list[Book]) -> BookCatalog:
    return BookCatalog(sample_books)
