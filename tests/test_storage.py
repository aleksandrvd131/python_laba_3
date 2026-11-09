import json
from pathlib import Path
import pytest
from book_catalog import (
    Book,
    BookCatalog,
    CorruptedStorageError,
    DuplicateIdError,
    UnsupportedVersionError,
)


def test_json_round_trip(tmp_path: Path, filled_catalog: BookCatalog) -> None:
    file_path = tmp_path / "catalog.json"
    filled_catalog.save_to_json(file_path)

    # Проверяем структуру записанного JSON
    raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    assert raw_data["format_version"] == 1
    assert len(raw_data["items"]) == 4

    # Загружаем в новый каталог
    loaded_catalog = BookCatalog()
    loaded_catalog.load_from_json(file_path)

    assert len(loaded_catalog) == len(filled_catalog)
    assert list(loaded_catalog) == list(filled_catalog)


def test_corrupted_json_syntax(tmp_path: Path) -> None:
    bad_file = tmp_path / "syntax_error.json"
    bad_file.write_text("{невалидный json", encoding="utf-8")

    catalog = BookCatalog()
    with pytest.raises(CorruptedStorageError):
        catalog.load_from_json(bad_file)


def test_unsupported_format_version(tmp_path: Path) -> None:
    file_path = tmp_path / "v999.json"
    file_path.write_text(
        json.dumps({"format_version": 999, "items": []}),
        encoding="utf-8",
    )

    catalog = BookCatalog()
    with pytest.raises(UnsupportedVersionError):
        catalog.load_from_json(file_path)


def test_invalid_root_structure(tmp_path: Path) -> None:
    catalog = BookCatalog()

    # Не словарь, а список
    list_file = tmp_path / "list_root.json"
    list_file.write_text("[]", encoding="utf-8")
    with pytest.raises(CorruptedStorageError):
        catalog.load_from_json(list_file)

    # Отсутствует items
    no_items_file = tmp_path / "no_items.json"
    no_items_file.write_text(json.dumps({"format_version": 1}), encoding="utf-8")
    with pytest.raises(CorruptedStorageError):
        catalog.load_from_json(no_items_file)


def test_atomic_load_on_invalid_book(tmp_path: Path, filled_catalog: BookCatalog) -> None:
    """
    Каталог содержит 4 книги. В файле первая книга валидная, а вторая содержит pages=-10.
    После ошибки загрузки каталог обязан сохранить исходные 4 книги без частичного добавления
    """
    broken_file = tmp_path / "broken_item.json"
    broken_payload = {
        "format_version": 1,
        "items": [
            Book("B-999", "Новая книга", "Жанр", 2020, "Автор", 100).to_dict(),
            {
                "id": "B-1000",
                "name": "Битая книга",
                "category": "Жанр",
                "year": 2020,
                "author": "Автор",
                "pages": -10,
            },
        ],
    }
    broken_file.write_text(json.dumps(broken_payload), encoding="utf-8")

    initial_books = list(filled_catalog)
    with pytest.raises(CorruptedStorageError):
        filled_catalog.load_from_json(broken_file)

    # Проверка атомарности
    assert len(filled_catalog) == 4
    assert list(filled_catalog) == initial_books
    assert "B-999" not in filled_catalog


def test_atomic_load_on_duplicate_id_in_file(tmp_path: Path, filled_catalog: BookCatalog) -> None:
    """В файле присутствуют две книги с одинаковым ID."""
    dup_file = tmp_path / "duplicate_in_file.json"
    b = Book("B-1", "Книга", "Жанр", 2020, "Автор", 100)
    dup_payload = {
        "format_version": 1,
        "items": [b.to_dict(), b.to_dict()],
    }
    dup_file.write_text(json.dumps(dup_payload), encoding="utf-8")

    initial_books = list(filled_catalog)
    with pytest.raises(DuplicateIdError):
        filled_catalog.load_from_json(dup_file)

    assert len(filled_catalog) == 4
    assert list(filled_catalog) == initial_books


def test_save_to_json_io_error(filled_catalog: BookCatalog, tmp_path: Path) -> None:
    # Попытка записать в директорию как в файл
    with pytest.raises(CorruptedStorageError):
        filled_catalog.save_to_json(tmp_path)
