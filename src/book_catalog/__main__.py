
import sys
from pathlib import Path

from .catalog import BookCatalog
from .exceptions import DuplicateIdError, InvalidEntityError, ItemNotFoundError
from .models import Book


def main() -> None:
    print("=" * 60)
    print(" Демонстрация работы BookCatalog (Python 3.14)")
    print("=" * 60)

    catalog = BookCatalog()

    sample_books = [
        Book("B-03", "Мастер и Маргарита", "Художественная литература", 1967, "Михаил Булгаков", 480),
        Book("B-01", "Чистый код", "Программирование", 2019, "Роберт Мартин", 464),
        Book("B-02", "Алгоритмы. Построение и анализ", "Программирование", 2022, "Томас Кормен", 1328),
        Book("B-04", "Пикник на обочине", "Фантастика", 1972, "Аркадий и Борис Стругацкие", 256),
    ]

    print("[1] Добавление книг в каталог")
    for b in sample_books:
        catalog.add(b)
        print(f"  + Добавлена: [{b.id}] «{b.name}» ({b.author}, {b.year})")

    print(f"Всего книг в каталоге: {len(catalog)}")

    print("[2] Проверка детерминированной итерации (по возрастанию ID):")
    for b in catalog:
        print(f"  - {b.id}: {b.name}")

    print("[3] Поиск по категории 'Программирование' (через индекс O(k log k)):")
    for b in catalog.find_by_category("Программирование"):
        print(f"  * [{b.id}] {b.name} ({b.pages} стр.)")

    print("[4] Регистронезависимый поиск по подстроке 'маргарита':")
    for b in catalog.find_by_name("маргарита"):
        print(f"  * [{b.id}] {b.name}")

    print("[5] Демонстрация undo() (+3 балла):")
    b_temp = Book("B-99", "Временная книга", "Тест", 2024, "Неизвестный", 100)
    catalog.add(b_temp)
    print(f"  Добавили {b_temp.id}. Размер каталога: {len(catalog)}")
    catalog.undo()
    print(f"  Выполнили catalog.undo(). Размер каталога: {len(catalog)}, 'B-99' in catalog: {'B-99' in catalog}")

    print("[6] Демонстрация транзакций (+5 баллов Challenge):")
    try:
        with catalog.transaction():
            catalog.add(Book("B-10", "Книга в транзакции", "Наука", 2023, "Автор 1", 200))
            print("  Внутри транзакции добавили B-10. Вызываем намеренную ошибку дубликата...")
            catalog.add(Book("B-01", "Дубликат B-01", "Наука", 2023, "Автор 2", 200))
    except DuplicateIdError:
        print("  Поймана DuplicateIdError! Транзакция откатила состояние.")

    print(f"  Размер каталога после отката транзакции: {len(catalog)} ('B-10' in catalog: {'B-10' in catalog})")

    demo_path = Path("/tmp/demo_catalog.json")
    print(f"\n[7] Сохранение каталога в JSON: {demo_path}")
    catalog.save_to_json(demo_path)

    new_cat = BookCatalog()
    new_cat.load_from_json(demo_path)
    print(f"  Загружено книг из файла: {len(new_cat)}")
    demo_path.unlink(missing_ok=True)

    print("\n" + "=" * 60)
    print(" Все демонстрационные сценарии успешно выполнены!")
    print("=" * 60)


if __name__ == "__main__":
    main()
