import pytest
from book_catalog import (
    Book,
    BookCatalog,
    DuplicateIdError,
    InvalidEntityError,
    ItemNotFoundError,
)


def test_add_get_remove_lifecycle(sample_books: list[Book]) -> None:
    catalog = BookCatalog()
    book = sample_books[0]

    assert len(catalog) == 0
    assert book.id not in catalog

    # Добавление
    catalog.add(book)
    assert len(catalog) == 1
    assert book.id in catalog
    assert catalog.get(book.id) == book

    # Удаление
    removed = catalog.remove(book.id)
    assert removed == book
    assert len(catalog) == 0
    assert book.id not in catalog

    # Повторная попытка получить или удалить
    with pytest.raises(ItemNotFoundError):
        catalog.get(book.id)

    with pytest.raises(ItemNotFoundError):
        catalog.remove(book.id)


def test_add_invalid_type_raises() -> None:
    catalog = BookCatalog()
    with pytest.raises(InvalidEntityError):
        catalog.add({"id": "B-1", "name": "Не объект Book"})  # type: ignore[arg-type]


def test_duplicate_id_forbidden(sample_books: list[Book]) -> None:
    catalog = BookCatalog()
    catalog.add(sample_books[0])

    clone = Book(
        id=sample_books[0].id,
        name="Другая книга с тем же ID",
        category="Другое",
        year=2021,
        author="Другой автор",
        pages=100,
    )
    with pytest.raises(DuplicateIdError):
        catalog.add(clone)


def test_find_by_category(filled_catalog: BookCatalog) -> None:
    prog_books = filled_catalog.find_by_category("Программирование")
    assert len(prog_books) == 2
    assert [b.id for b in prog_books] == ["B-001", "B-002"]

    empty_res = filled_catalog.find_by_category("Несуществующая категория")
    assert empty_res == []


def test_find_by_name_case_insensitive(filled_catalog: BookCatalog) -> None:
    # Поиск "маргарита" в разном регистре
    res_upper = filled_catalog.find_by_name("МАРГАРИТА")
    assert len(res_upper) == 1
    assert res_upper[0].id == "B-003"

    res_lower = filled_catalog.find_by_name("мастер")
    assert len(res_lower) == 1
    assert res_lower[0].id == "B-003"

    # Нестроковый запрос
    assert filled_catalog.find_by_name(None) == []  # type: ignore[arg-type]


def test_search_methods_immutability(filled_catalog: BookCatalog) -> None:
    """Методы поиска не должны возвращать внутренний изменяемый список каталога."""
    found = filled_catalog.find_by_category("Программирование")
    assert len(found) == 2

    # Мутируем полученный список
    found.clear()

    # Проверяем, что каталог не изменился
    assert len(filled_catalog.find_by_category("Программирование")) == 2
    assert len(filled_catalog) == 4


def test_deterministic_iteration_order(sample_books: list[Book]) -> None:

    catalog = BookCatalog()
    for book in sample_books:
        catalog.add(book)

    iterated_ids = [book.id for book in catalog]
    assert iterated_ids == ["B-001", "B-002", "B-003", "B-004"]
