from pathlib import Path

import pytest

from book_catalog.catalog import BookCatalog, ReadOnlyCatalogView
from book_catalog.exceptions import (
    CatalogError,
    DuplicateIdError,
    UnsupportedVersionError,
)
from book_catalog.migration import migrate_file, migrate_v1_to_v2_payload
from book_catalog.models import Book


def test_bonus_category_index_consistency(sample_books: list[Book]) -> None:
    """Проверка актуальности индекса категорий при добавлении удалении и перезаписи"""
    catalog = BookCatalog()
    catalog.add(sample_books[0])  # B-002: Программирование
    catalog.add(sample_books[1])  # B-001: Программирование
    catalog.add(sample_books[2])  # B-003: Художественная литература

    assert [b.id for b in catalog.find_by_category("Программирование")] == ["B-001", "B-002"]

    # Удаляем одну книгу и проверяем, что индекс обновился
    catalog.remove("B-001")
    assert [b.id for b in catalog.find_by_category("Программирование")] == ["B-002"]

    # Удаляем вторую книгу
    catalog.remove("B-002")
    assert catalog.find_by_category("Программирование") == []


def test_bonus_undo(sample_books: list[Book]) -> None:
    """Проверка механизма отката операций undo()."""
    catalog = BookCatalog()

    # Попытка вызвать undo при пустом стеке
    with pytest.raises(CatalogError):
        catalog.undo()

    # Откат добавления
    catalog.add(sample_books[0])
    assert len(catalog) == 1
    catalog.undo()
    assert len(catalog) == 0
    assert sample_books[0].id not in catalog

    # Откат удаления
    catalog.add(sample_books[0])
    catalog.remove(sample_books[0].id)
    assert len(catalog) == 0
    catalog.undo()
    assert len(catalog) == 1
    assert catalog.get(sample_books[0].id) == sample_books[0]


def test_bonus_read_only_view(filled_catalog: BookCatalog) -> None:
    """Проверка ReadOnlyCatalogView (+2 балла)."""
    view = filled_catalog.read_only
    assert isinstance(view, ReadOnlyCatalogView)

    assert len(view) == len(filled_catalog)
    assert "B-001" in view
    assert view.get("B-001") == filled_catalog.get("B-001")
    assert len(view.find_by_category("Программирование")) == 2
    assert len(view.find_by_name("чистый")) == 1
    assert list(view) == list(filled_catalog)

    # Проверяем отсутствие методов мутации
    assert not hasattr(view, "add")
    assert not hasattr(view, "remove")
    assert not hasattr(view, "load_from_json")
    assert not hasattr(view, "undo")

    # Мутация исходного каталога немедленно видна во view
    new_book = Book("B-999", "Новая", "Тест", 2024, "Автор", 100)
    filled_catalog.add(new_book)
    assert "B-999" in view
    assert len(view) == 5


def test_bonus_transaction_commit_and_rollback(filled_catalog: BookCatalog) -> None:
    """Проверка транзакций с автоматическим rollback"""
    new_b1 = Book("B-101", "Книга 1", "Жанр", 2020, "Автор", 100)
    new_b2 = Book("B-102", "Книга 2", "Жанр", 2020, "Автор", 100)

    # Успешный коммит транзакции
    with filled_catalog.transaction():
        filled_catalog.add(new_b1)
        filled_catalog.add(new_b2)

    assert "B-101" in filled_catalog
    assert "B-102" in filled_catalog
    assert len(filled_catalog) == 6

    # Транзакция с ошибкой (дубликат ID) -> rollback
    with pytest.raises(DuplicateIdError), filled_catalog.transaction():
        filled_catalog.add(Book("B-103", "Книга 3", "Жанр", 2020, "Автор", 100))
        # Вызываем ошибку
        filled_catalog.add(new_b1)

    # B-103 не должна остаться в каталоге после отката
    assert "B-103" not in filled_catalog
    assert len(filled_catalog) == 6


def test_bonus_migration_v1_to_v2(tmp_path: Path, filled_catalog: BookCatalog) -> None:
    """Проверка миграции формата хранилища из версии 1 в версию 2"""
    v1_file = tmp_path / "catalog_v1.json"
    v2_file = tmp_path / "catalog_v2.json"
    filled_catalog.save_to_json(v1_file)

    migrate_file(v1_file, v2_file)

    import json

    v2_data = json.loads(v2_file.read_text(encoding="utf-8"))
    assert v2_data["format_version"] == 2
    assert len(v2_data["items"]) == 4
    for item in v2_data["items"]:
        assert item["language"] == "ru"

    # Проверка ошибки миграции для неподдерживаемой версии
    with pytest.raises(UnsupportedVersionError):
        migrate_v1_to_v2_payload({"format_version": 99, "items": []})
