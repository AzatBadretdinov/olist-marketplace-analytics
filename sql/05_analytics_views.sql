-- One row per order. Run in database olist. Raw data stays unchanged.
BEGIN;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE OR REPLACE VIEW analytics.order_fact AS
WITH item_totals AS (
 SELECT order_id, COUNT(*) AS item_count, SUM(price) AS item_gmv, SUM(freight_value) AS freight_value
 FROM raw.order_items GROUP BY order_id
), payment_totals AS (
 SELECT order_id, SUM(payment_value) AS payment_value FROM raw.payments GROUP BY order_id
), ranked_reviews AS (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC NULLS LAST,
 review_creation_date DESC NULLS LAST, review_id DESC) AS rn FROM raw.reviews
), base AS (
 SELECT o.*, c.customer_unique_id, c.customer_state,
 DATE_TRUNC('month',o.order_purchase_timestamp)::date AS purchase_month,
 COALESCE(i.item_count,0) AS item_count, COALESCE(i.item_gmv,0)::numeric(14,2) AS item_gmv,
 COALESCE(i.freight_value,0)::numeric(14,2) AS freight_value,
 p.payment_value,r.review_score,r.review_answer_timestamp,
 (o.order_status='delivered' AND o.order_purchase_timestamp IS NOT NULL
  AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
  AND o.order_delivered_customer_date>=o.order_purchase_timestamp
  AND o.order_estimated_delivery_date::date>=o.order_purchase_timestamp::date) AS delivery_eligible
 FROM raw.orders o LEFT JOIN raw.customers c USING(customer_id)
 LEFT JOIN item_totals i USING(order_id) LEFT JOIN payment_totals p USING(order_id)
 LEFT JOIN ranked_reviews r ON o.order_id=r.order_id AND r.rn=1
)
SELECT base.*,
 CASE WHEN delivery_eligible THEN order_delivered_customer_date::date>order_estimated_delivery_date::date END AS is_late,
 CASE WHEN delivery_eligible THEN EXTRACT(EPOCH FROM(order_delivered_customer_date-order_purchase_timestamp))/86400.0 END AS delivery_days,
 CASE WHEN delivery_eligible THEN GREATEST(order_delivered_customer_date::date-order_estimated_delivery_date::date,0) END AS late_days,
 CASE WHEN review_score BETWEEN 1 AND 5 THEN review_score<=2 END AS low_review
FROM base;

CREATE OR REPLACE VIEW analytics.monthly_state AS
SELECT purchase_month,customer_state, COUNT(*) AS all_orders,
 COUNT(*) FILTER(WHERE order_status='delivered') AS delivered_orders,
 COALESCE(SUM(item_gmv) FILTER(WHERE order_status='delivered'),0) AS delivered_gmv,
 COALESCE(SUM(freight_value) FILTER(WHERE order_status='delivered'),0) AS delivered_freight,
 COUNT(*) FILTER(WHERE delivery_eligible) AS delivery_eligible,
 COUNT(*) FILTER(WHERE is_late) AS late_orders,
 COALESCE(SUM(delivery_days),0) AS delivery_days_sum,
 COUNT(*) FILTER(WHERE order_status='delivered' AND low_review IS NOT NULL) AS reviewed_orders,
 COUNT(*) FILTER(WHERE order_status='delivered' AND low_review) AS low_reviews
FROM analytics.order_fact
WHERE order_purchase_timestamp>=TIMESTAMP '2017-01-01'
 AND order_purchase_timestamp<TIMESTAMP '2018-08-01'
GROUP BY purchase_month,customer_state;

CREATE OR REPLACE VIEW analytics.category_performance AS
SELECT COALESCE(t.product_category_name_english,p.product_category_name,'unknown') AS category,
 COUNT(*) AS item_count,COUNT(DISTINCT i.order_id) AS orders_with_category,
 SUM(i.price) AS delivered_gmv,SUM(i.freight_value) AS delivered_freight
FROM raw.order_items i JOIN analytics.order_fact o USING(order_id)
LEFT JOIN raw.products p USING(product_id)
LEFT JOIN raw.category_translation t USING(product_category_name)
WHERE o.order_status='delivered' AND o.order_purchase_timestamp>=TIMESTAMP '2017-01-01'
 AND o.order_purchase_timestamp<TIMESTAMP '2018-08-01'
GROUP BY COALESCE(t.product_category_name_english,p.product_category_name,'unknown');
COMMIT;

