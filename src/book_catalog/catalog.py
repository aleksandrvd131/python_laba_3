import json
from collections import defaultdict
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .exceptions import (
    CatalogError,
    CorruptedStorageError,
    DuplicateIdError,
    InvalidEntityError,
    ItemNotFoundError,
    UnsupportedVersionError,
)
from .models import Book, BookId, Category


class ReadOnlyCatalogView:
    __slots__ = ("_catalog",)

    def __init__(self, catalog: BookCatalog) -> None:
        self._catalog = catalog

    def get(self, item_id: BookId) -> Book:
        return self._catalog.get(item_id)

    def find_by_category(self, category: Category) -> list[Book]:
        return self._catalog.find_by_category(category)

    def find_by_name(self, query: str) -> list[Book]:
        return self._catalog.find_by_name(query)

    def __len__(self) -> int:
        return len(self._catalog)

    def __iter__(self) -> Iterator[Book]:
        return iter(self._catalog)

    def __contains__(self, item_id: object) -> bool:
        return item_id in self._catalog


class BookCatalog:
    FORMAT_VERSION = 1

    def __init__(self, items: Iterable[Book] = ()) -> None:
        self._items: dict[BookId, Book] = {}
        self._by_category: defaultdict[Category, set[BookId]] = defaultdict(set)
        self._undo_stack: list[dict[BookId, Book]] = []

        for book in items:
            self.add(book)
        self._undo_stack.clear()

    def _save_snapshot(self) -> None:
        """Сохраняет снимок текущего состояния для поддержки undo"""
        # Book неизменяем (frozen=True), поэтому поверхностная копия словаря безопасна и O(N).
        self._undo_stack.append(self._items.copy())

    def _rebuild_state(self, new_items: dict[BookId, Book]) -> None:
        """Атомарно обновляет внутреннее хранилище и перестраивает индекс категорий"""
        new_category_index: defaultdict[Category, set[BookId]] = defaultdict(set)
        for book in new_items.values():
            new_category_index[book.category].add(book.id)

        self._items = new_items
        self._by_category = new_category_index

    def add(self, item: Book) -> None:
        if not isinstance(item, Book):
            raise InvalidEntityError(
                f"В каталог можно добавлять только экземпляры Book, получен {type(item).__name__}."
            )
        if item.id in self._items:
            raise DuplicateIdError(f"Книга с ID '{item.id}' уже существует в каталоге")

        self._save_snapshot()
        self._items[item.id] = item
        self._by_category[item.category].add(item.id)

    def get(self, item_id: BookId) -> Book:
        """Возвращает книгу по её айди за время O(1)"""
        try:
            return self._items[item_id]
        except KeyError as exc:
            raise ItemNotFoundError(f"Книга с ID '{item_id}' не найдена в каталоге.") from exc

    def remove(self, item_id: BookId) -> Book:
        book = self.get(item_id)
        self._save_snapshot()
        del self._items[item_id]
        self._by_category[book.category].discard(item_id)
        return book

    def find_by_category(self, category: Category) -> list[Book]:

        ids = self._by_category.get(category, set())
        return [self._items[book_id] for book_id in sorted(ids)]

    def find_by_name(self, query: str) -> list[Book]:

        if not isinstance(query, str):
            return []
        folded_query = query.casefold()
        return [book for book in self if folded_query in book.name.casefold()]

    def undo(self) -> None:

        if not self._undo_stack:
            raise CatalogError("История операций пуста, откат невозможен.")
        previous_state = self._undo_stack.pop()
        self._rebuild_state(previous_state)

    @property
    def read_only(self) -> ReadOnlyCatalogView:
        """Возвращает безопасное представление каталога только для чтения"""
        return ReadOnlyCatalogView(self)

    @contextmanager
    def transaction(self) -> Iterator[BookCatalog]:
        """Транзакционный контекстный менеджер с откатом при ошибке"""
        snapshot = self._items.copy()
        stack_depth = len(self._undo_stack)
        try:
            yield self
        except Exception:
            self._rebuild_state(snapshot)
            del self._undo_stack[stack_depth:]
            raise

    def __len__(self) -> int:
        """Возвращает общее количество книг в каталоге"""
        return len(self._items)

    def __iter__(self) -> Iterator[Book]:
        """элементы обходятся в порядке возрастания строкового ID книги"""
        for item_id in sorted(self._items):
            yield self._items[item_id]

    def __contains__(self, item_id: object) -> bool:
        """Проверяет наличие книги с данным ID в каталоге"""
        return isinstance(item_id, str) and item_id in self._items

    def save_to_json(self, file_path: str | Path) -> None:
        payload: dict[str, Any] = {
            "format_version": self.FORMAT_VERSION,
            "items": [book.to_dict() for book in self],
        }
        path = Path(file_path)
        try:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise CorruptedStorageError(f"Ошибка записи файла '{path}': {exc}") from exc

    def load_from_json(self, file_path: str | Path) -> None:
        path = Path(file_path)
        try:
            raw_text = path.read_text(encoding="utf-8")
            raw_data = json.loads(raw_text)
        except (OSError, json.JSONDecodeError) as exc:
            raise CorruptedStorageError(f"Не удалось прочитать JSON из '{path}': {exc}") from exc

        match raw_data:
            case {"format_version": version, "items": list(raw_items)} if type(version) is int:
                if version != self.FORMAT_VERSION:
                    raise UnsupportedVersionError(
                        f"Неподдерживаемая версия: {version} (ожидалась {self.FORMAT_VERSION})"
                    )
            case {"format_version": _}:
                raise CorruptedStorageError(
                    "Некорректный тип поля 'format_version' или отсутствует список 'items'"
                )
            case _:
                raise CorruptedStorageError(
                    "Корень JSON-документа должен содержать поля 'format_version' и 'items'"
                )

        staged_items: dict[BookId, Book] = {}
        for index, raw_entry in enumerate(raw_items):
            try:
                book = Book.from_dict(raw_entry)
            except InvalidEntityError as exc:
                err = CorruptedStorageError(
                    f"Повреждённая запись книги с индексом {index} в файле {path}"
                )
                err.add_note(f"Детали ошибки валидации: {exc}")
                raise err from exc

            if book.id in staged_items:
                raise DuplicateIdError(
                    f"Дубликат ID '{book.id}' обнаружен внутри загружаемого файла"
                )
            staged_items[book.id] = book

        # Атомарное обновление только после валидации всех элементов
        self._save_snapshot()
        self._rebuild_state(staged_items)
