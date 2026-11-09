import json
from pathlib import Path
from typing import Any

from .exceptions import CorruptedStorageError, UnsupportedVersionError


def migrate_v1_to_v2_payload(payload: dict[str, Any], default_language: str = "ru") -> dict[str, Any]:
    match payload:
        case {"format_version": 1, "items": list(raw_items)}:
            migrated_items = [
                {**item, "language": item.get("language", default_language)}
                for item in raw_items
            ]
            return {
                "format_version": 2,
                "items": migrated_items,
            }
        case {"format_version": int(v)}:
            raise UnsupportedVersionError(f"Ожидалась версия 1 для миграции, получена версия {v}.")
        case _:
            raise CorruptedStorageError("Некорректная структура JSON для миграции.")


def migrate_file(source_path: str | Path, target_path: str | Path) -> None:

    src = Path(source_path)
    try:
        content = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorruptedStorageError(f"Не удалось прочитать исходный файл '{src}': {exc}") from exc

    migrated = migrate_v1_to_v2_payload(content)
    try:
        Path(target_path).write_text(
            json.dumps(migrated, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise CorruptedStorageError(f"Не удалось записать целевой файл '{target_path}': {exc}") from exc
