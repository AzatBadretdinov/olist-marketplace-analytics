"""Refresh analytics views and export via client-side COPY. No passwords in code."""
from pathlib import Path
from getpass import getpass
import os
import psycopg

ROOT = Path(__file__).resolve().parents[1]

def connection_options():
    return dict(host=os.getenv("PGHOST", "127.0.0.1"),
                port=os.getenv("PGPORT", "5432"), dbname=os.getenv("PGDATABASE", "olist"),
                user=os.getenv("PGUSER", "postgres"),
                password=os.getenv("PGPASSWORD") or getpass("PostgreSQL password: "))

def main():
    exports = ROOT / "exports"
    exports.mkdir(exist_ok=True)
    with psycopg.connect(**connection_options(), autocommit=True) as conn:
        conn.execute((ROOT/"sql/05_analytics_views.sql").read_text(encoding="utf-8-sig"), prepare=False)
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            for name,query in {
                "order_fact.csv":"SELECT * FROM analytics.order_fact ORDER BY order_purchase_timestamp,order_id",
                "monthly_state.csv":"SELECT * FROM analytics.monthly_state ORDER BY purchase_month,customer_state",
                "categories.csv":"SELECT * FROM analytics.category_performance ORDER BY delivered_gmv DESC,category"
            }.items():
                with conn.cursor() as cur, (exports/name).open("wb") as target:
                    with cur.copy(f"COPY ({query}) TO STDOUT WITH(FORMAT csv,HEADER true,ENCODING 'UTF8')") as copy:
                        for block in copy:
                            target.write(block)
                print(f"Exported {name}")
if __name__ == "__main__":
    main()

