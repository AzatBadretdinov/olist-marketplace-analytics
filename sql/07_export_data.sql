-- Local Windows export. PostgreSQL service needs write access to exports/.
-- Rewrites generated exports; raw data remains unchanged.
COPY (SELECT * FROM analytics.order_fact ORDER BY order_purchase_timestamp,order_id)
TO 'D:/data_analyst/project1/exports/order_fact.csv' WITH(FORMAT csv,HEADER true,ENCODING 'UTF8');
COPY (SELECT * FROM analytics.monthly_state ORDER BY purchase_month,customer_state)
TO 'D:/data_analyst/project1/exports/monthly_state.csv' WITH(FORMAT csv,HEADER true,ENCODING 'UTF8');
COPY (SELECT * FROM analytics.category_performance ORDER BY delivered_gmv DESC,category)
TO 'D:/data_analyst/project1/exports/categories.csv' WITH(FORMAT csv,HEADER true,ENCODING 'UTF8');
SELECT (SELECT COUNT(*) FROM raw.orders) AS raw_orders,COUNT(*) AS fact_rows,
 COUNT(DISTINCT order_id) AS unique_fact_orders,
 SUM(item_gmv)=(SELECT SUM(price) FROM raw.order_items) AS gmv_reconciles,
 SUM(freight_value)=(SELECT SUM(freight_value) FROM raw.order_items) AS freight_reconciles,
 SUM(payment_value)=(SELECT SUM(payment_value) FROM raw.payments) AS payments_reconcile
FROM analytics.order_fact;

