class CatalogError(Exception):
    """Базовое исключение для всех ошибок домена каталога"""


class InvalidEntityError(CatalogError):
    """Нарушение инвариантов сущности Book при создании или валидации"""


class DuplicateIdError(CatalogError):
    """Попытка добавления книги с идентификатором, который уже есть в каталоге"""


class ItemNotFoundError(CatalogError):
    """Книга с указанным идентификатором не найдена в каталоге"""


class UnsupportedVersionError(CatalogError):
    """Версия формата файла хранилища не поддерживается данным каталогом"""


class CorruptedStorageError(CatalogError):
    """Файл хранилища повреждён, недоступен или нарушает ожидаемую схему JSON"""
