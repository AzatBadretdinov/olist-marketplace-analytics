"""Первичное обследование Olist: исходные CSV не изменяются."""
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
REPORT_DIR = PROJECT_DIR / "reports" / "data_understanding"

# Название: файл, кандидат в ключ, смысл одной строки.
TABLES = {
    "customers": ("olist_customers_dataset.csv", ["customer_id"], "Запись покупателя для связи с заказом. customer_unique_id объединяет записи одного покупателя."),
    "orders": ("olist_orders_dataset.csv", ["order_id"], "Один заказ."),
    "order_items": ("olist_order_items_dataset.csv", ["order_id", "order_item_id"], "Одна товарная позиция заказа."),
    "order_payments": ("olist_order_payments_dataset.csv", ["order_id", "payment_sequential"], "Одна запись об оплате заказа."),
    "order_reviews": ("olist_order_reviews_dataset.csv", ["review_id", "order_id"], "Одна запись отзыва о заказе. Проверяем пару review_id и order_id как кандидат в ключ."),
    "products": ("olist_products_dataset.csv", ["product_id"], "Один товар."),
    "sellers": ("olist_sellers_dataset.csv", ["seller_id"], "Один продавец."),
    "geolocation": ("olist_geolocation_dataset.csv", [], "Географическая запись для почтового префикса. Префикс может повторяться; ключ пока не выбран."),
    "category_translation": ("product_category_name_translation.csv", ["product_category_name"], "Перевод названия категории с португальского на английский."),
}
RELATIONS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("order_payments", "order_id", "orders", "order_id"),
    ("order_reviews", "order_id", "orders", "order_id"),
    ("products", "product_category_name", "category_translation", "product_category_name"),
    ("customers", "customer_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
    ("sellers", "seller_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
]


def main():
    missing = [name for name, _, _ in TABLES.values() if not (DATA_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Не найдены файлы в {DATA_DIR}: {missing}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frames, summaries, profiles = {}, [], []
    dictionary = ["# Словарь данных Olist", "", "Сгенерировано data_understand.py. Исходные CSV не изменены.", ""]

    for table, (filename, key, grain) in TABLES.items():
        # Почтовые коды читаем как строки, чтобы не потерять ведущие нули.
        header = pd.read_csv(DATA_DIR / filename, nrows=0).columns
        code_types = {col: "string" for col in header if "zip_code_prefix" in col}
        df = pd.read_csv(DATA_DIR / filename, dtype=code_types)
        frames[table] = df
        full_duplicates = int(df.duplicated().sum())
        null_key_rows = int(df[key].isna().any(axis=1).sum()) if key else None
        # keep=False считает ВСЕ строки повторяющихся ключей, не только лишние.
        duplicate_key_rows = int(df.duplicated(subset=key, keep=False).sum()) if key else None
        status = ("OK" if null_key_rows == 0 and duplicate_key_rows == 0 else "FAIL") if key else "NOT_SELECTED"
        summaries.append(dict(table=table, rows=len(df), columns=len(df.columns),
                              extra_full_duplicates=full_duplicates, candidate_key=", ".join(key),
                              null_key_rows=null_key_rows, all_duplicate_key_rows=duplicate_key_rows, key_status=status))
        print(f"\n{'=' * 70}\nТаблица: {table}")
        df.info()
        print(df.head().to_string(index=False))
        print("Размер:", df.shape, "| Полные дубликаты сверх первого:", full_duplicates)
        print("Пропуски:\n", df.isna().sum().to_string())
        print("Ключ:", key, "| Статус:", status, "| Пропуски:", null_key_rows, "| Строки повторяющихся ключей:", duplicate_key_rows)
        dictionary += [f"## {table}", "", f"Файл: `{filename}`.", "", grain, "",
                       f"Кандидат в ключ: {', '.join(key) or 'не выбран'}. Статус: {status}.", "",
                       "| Столбец | pandas | Пропуски | Уникальные без NA |", "|---|---|---:|---:|"]
        for col in df.columns:
            na_count, unique_count = int(df[col].isna().sum()), int(df[col].nunique())
            profiles.append(dict(table=table, column=col, dtype=str(df[col].dtype), missing_count=na_count,
                                 missing_pct=round(na_count / len(df) * 100, 3) if len(df) else 0,
                                 unique_non_null=unique_count))
            dictionary.append(f"| {col} | {df[col].dtype} | {na_count} | {unique_count} |")
        dictionary.append("")

    relations = []
    dictionary += ["## Связи", "", "Кратность измерена по непустым значениям текущей выгрузки, а не задана как бизнес-правило.", ""]
    for child, child_col, parent, parent_col in RELATIONS:
        source, target = frames[child][child_col], frames[parent][parent_col]
        unmatched = source.notna() & ~source.isin(target.dropna())
        child_unique = not source.dropna().duplicated().any()
        parent_unique = not target.dropna().duplicated().any()
        cardinality = ("1" if child_unique else "many") + ":" + ("1" if parent_unique else "many")
        relations.append(dict(child=child, child_column=child_col, parent=parent, parent_column=parent_col,
                              observed_cardinality_child_to_parent=cardinality, child_null_rows=int(source.isna().sum()),
                              unmatched_non_null_rows=int(unmatched.sum()),
                              unmatched_distinct_values=int(source[unmatched].nunique()), parent_non_null_unique=parent_unique))
        dictionary.append(f"- `{child}.{child_col}` → `{parent}.{parent_col}`: {cardinality}; непустых строк без соответствия: {int(unmatched.sum())}.")

    findings = ["# Результаты обследования Olist", "", "Данные не очищались. Проверено девять таблиц.", ""]
    for row in summaries:
        findings.append(f"- {row['table']}: {row['rows']:,} строк; лишних полных дубликатов {row['extra_full_duplicates']:,}; статус ключа {row['key_status']}; всех строк с повторяющимся ключом {row['all_duplicate_key_rows']}.")
    customers = frames["customers"]
    findings += ["", "## Покупатели", "",
                 f"Записей customers: {len(customers):,}; уникальных customer_unique_id без NA: {customers['customer_unique_id'].nunique():,}.",
                 "customer_id нужен для связи с orders; customer_unique_id — для подсчёта покупателей и повторных покупок.",
                 "", "## Связи", ""]
    findings += dictionary[dictionary.index("## Связи") + 2:]
    findings += ["", "## Что учесть перед PostgreSQL", "",
                 "- Повторы order_id в позициях, оплатах и отзывах сами по себе не являются ошибкой. Важны детализация и составной ключ.",
                 "- Прямой JOIN позиций, оплат и отзывов может перемножить строки и завысить суммы. Для анализа на уровне заказа сначала агрегируйте дочерние таблицы.",
                 "- Почтовый префикс geolocation нельзя автоматически назначать первичным ключом. Перед соединением нужна стратегия агрегации географии.",
                 "- FAIL означает, что кандидат в ключ не прошёл проверку. Нужно исследовать повторы до назначения ограничений.",
                 "- Пропуски и дубликаты только зафиксированы; правила обработки нужно обосновать отдельно.",
                 "- Почтовые префиксы прочитаны как строки для сохранения ведущих нулей. Остальные типы определены pandas, даты ещё не преобразованы.",
                 "- Предварительные типы PostgreSQL: идентификаторы и почтовые коды — TEXT; даты — TIMESTAMP после проверки формата и часового пояса; деньги — NUMERIC после проверки точности и диапазона; счётчики — INTEGER после проверки значений.", ""]
    for filename, rows in [("table_summary.csv", summaries), ("column_profile.csv", profiles), ("relationships.csv", relations)]:
        pd.DataFrame(rows).to_csv(REPORT_DIR / filename, index=False, encoding="utf-8-sig")
    (REPORT_DIR / "data_dictionary.md").write_text("\n".join(dictionary), encoding="utf-8")
    (REPORT_DIR / "findings.md").write_text("\n".join(findings), encoding="utf-8")
    print(f"\nОтчёты сохранены: {REPORT_DIR}")


if __name__ == "__main__":
    main()
