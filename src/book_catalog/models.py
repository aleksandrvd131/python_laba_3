from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Self

from .exceptions import InvalidEntityError

type BookId = str
type Category = str


def _is_real_int(value: object) -> bool:
    """Проверяет, что значение является целым числом и не является булевым флагом"""
    return type(value) is int


@dataclass(frozen=True, slots=True)
class Book:
    id: BookId
    name: str
    category: Category
    year: int
    author: str
    pages: int

    def __post_init__(self) -> None:
        text_fields = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "author": self.author,
        }
        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise InvalidEntityError(
                    f"Поле '{field_name}' должно быть непустой строкой"
                )

        max_year = date.today().year + 1
        if not _is_real_int(self.year) or not (1450 <= self.year <= max_year):
            raise InvalidEntityError(
                f"Год издания должен быть целым числом в диапазоне 1450..{max_year}"
            )

        if not _is_real_int(self.pages) or self.pages <= 0:
            raise InvalidEntityError(
                "Количество страниц должно быть положительным целым числом"
            )

    def to_dict(self) -> dict[str, Any]:
        """Преобразует сущность в словарь для сериализации"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: object) -> Self:
        """Создает экземпляр Book из словаря с проверкой схемы через патерны"""
        match data:
            case {
                "id": str(book_id),
                "name": str(name),
                "category": str(category),
                "year": year,
                "author": str(author),
                "pages": pages,
                **extra,
            } if not extra and _is_real_int(year) and _is_real_int(pages):
                return cls(
                    id=book_id,
                    name=name,
                    category=category,
                    year=year,
                    author=author,
                    pages=pages,
                )
            case _:
                raise InvalidEntityError(
                    "Данные книги не соответствуют схеме Book или содержат некорректные типы"
                )
