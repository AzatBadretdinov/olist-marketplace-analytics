-- Compare PostgreSQL counts with the original CSV counts.
WITH actual AS (
SELECT 'customers' AS table_name, count(*) AS rows FROM raw.customers
UNION ALL
SELECT 'orders' AS table_name, count(*) AS rows FROM raw.orders
UNION ALL
SELECT 'order_items' AS table_name, count(*) AS rows FROM raw.order_items
UNION ALL
SELECT 'payments' AS table_name, count(*) AS rows FROM raw.payments
UNION ALL
SELECT 'reviews' AS table_name, count(*) AS rows FROM raw.reviews
UNION ALL
SELECT 'products' AS table_name, count(*) AS rows FROM raw.products
UNION ALL
SELECT 'sellers' AS table_name, count(*) AS rows FROM raw.sellers
UNION ALL
SELECT 'geolocation' AS table_name, count(*) AS rows FROM raw.geolocation
UNION ALL
SELECT 'category_translation' AS table_name, count(*) AS rows FROM raw.category_translation
), expected(table_name, expected_rows) AS (VALUES
('customers', 99441::bigint),
('orders', 99441::bigint),
('order_items', 112650::bigint),
('payments', 103886::bigint),
('reviews', 99224::bigint),
('products', 32951::bigint),
('sellers', 3095::bigint),
('geolocation', 1000163::bigint),
('category_translation', 71::bigint)
)
SELECT a.table_name, a.rows AS actual_rows, e.expected_rows,
       a.rows = e.expected_rows AS matches_csv
FROM actual a JOIN expected e USING (table_name)
ORDER BY a.table_name;

