"""Portable CSV -> PostgreSQL loader. Create database olist separately first.
Loads only empty tables, validates headers/counts, never deletes existing data.
"""
from pathlib import Path
import csv
import psycopg
from psycopg import sql
from refresh_from_postgres import connection_options

ROOT = Path(__file__).resolve().parents[1]
FILES = {
 "customers":"olist_customers_dataset.csv", "orders":"olist_orders_dataset.csv",
 "order_items":"olist_order_items_dataset.csv", "products":"olist_products_dataset.csv",
 "payments":"olist_order_payments_dataset.csv", "reviews":"olist_order_reviews_dataset.csv",
 "sellers":"olist_sellers_dataset.csv", "geolocation":"olist_geolocation_dataset.csv",
 "category_translation":"product_category_name_translation.csv"
}
def main():
    with psycopg.connect(**connection_options()) as conn:
        conn.execute((ROOT/"sql/01_create_tables.sql").read_text(encoding="utf-8-sig"), prepare=False)
        for table,filename in FILES.items():
            path=ROOT/"data"/filename
            with path.open(encoding="utf-8-sig",newline="") as source:
                reader=csv.reader(source)
                header=next(reader)
                expected=sum(1 for _ in reader)
            db_header=[r[0] for r in conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='raw' AND table_name=%s ORDER BY ordinal_position",
                (table,))]
            if header != db_header:
                raise ValueError(f"{table}: CSV header does not match database schema")
            conn.execute(sql.SQL("LOCK TABLE raw.{} IN SHARE ROW EXCLUSIVE MODE").format(sql.Identifier(table)))
            existing=conn.execute(sql.SQL("SELECT COUNT(*) FROM raw.{}").format(sql.Identifier(table))).fetchone()[0]
            if existing==expected:
                print(f"{table}: skipped, already {existing} rows (count only, not a content hash)")
                continue
            if existing:
                raise ValueError(f"{table}: unexpected {existing} existing rows; no changes committed")
            with conn.cursor() as cur, path.open("rb") as source:
                command=sql.SQL("COPY raw.{} FROM STDIN WITH(FORMAT csv,HEADER true,ENCODING 'UTF8')").format(sql.Identifier(table))
                with cur.copy(command) as copy:
                    while block := source.read(1024*1024):
                        copy.write(block)
            loaded=conn.execute(sql.SQL("SELECT COUNT(*) FROM raw.{}").format(sql.Identifier(table))).fetchone()[0]
            if loaded != expected:
                raise ValueError(f"{table}: loaded {loaded}, expected {expected}")
            print(f"{table}: loaded {loaded}")
    print("Committed. Raw files were not changed.")
if __name__=="__main__":
    main()

