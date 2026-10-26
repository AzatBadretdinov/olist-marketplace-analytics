-- Reporting cohort: purchases Jan 2017--Jul 2018. Money in BRL.
-- 1. Monthly delivered merchandise value and month-over-month change.
WITH monthly AS (
 SELECT purchase_month,SUM(all_orders) AS all_orders,SUM(delivered_orders) AS delivered_orders,
 SUM(delivered_gmv) AS delivered_gmv FROM analytics.monthly_state GROUP BY purchase_month
), previous AS (
 SELECT *,LAG(delivered_gmv) OVER(ORDER BY purchase_month) AS previous_gmv FROM monthly
)
SELECT *,delivered_gmv/NULLIF(delivered_orders,0) AS average_order_value,
 delivered_gmv/NULLIF(previous_gmv,0)-1 AS gmv_mom FROM previous ORDER BY purchase_month;

-- 2. Regional delivery performance: display denominators next to rates.
SELECT customer_state,SUM(delivered_orders) AS delivered_orders,SUM(delivered_gmv) AS delivered_gmv,
 SUM(delivery_eligible) AS delivery_eligible,SUM(late_orders) AS late_orders,
 SUM(late_orders)::numeric/NULLIF(SUM(delivery_eligible),0) AS late_rate,
 SUM(delivery_days_sum)/NULLIF(SUM(delivery_eligible),0) AS mean_delivery_days
FROM analytics.monthly_state GROUP BY customer_state ORDER BY late_orders DESC;

-- 3. Category contribution. Category order counts are NOT additive.
SELECT *,delivered_gmv/SUM(delivered_gmv) OVER() AS gmv_share,
 SUM(delivered_gmv) OVER(ORDER BY delivered_gmv DESC,category ROWS UNBOUNDED PRECEDING)
 /SUM(delivered_gmv) OVER() AS cumulative_gmv_share
FROM analytics.category_performance ORDER BY delivered_gmv DESC,category;

-- 4. Primary statistical sample: first eligible reviewed order per customer.
WITH eligible AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp,order_id) AS rn
 FROM analytics.order_fact WHERE order_purchase_timestamp>=TIMESTAMP '2017-01-01'
 AND order_purchase_timestamp<TIMESTAMP '2018-08-01' AND delivery_eligible
 AND low_review IS NOT NULL AND customer_unique_id IS NOT NULL
)
SELECT is_late,COUNT(*) AS reviewed_orders,COUNT(*) FILTER(WHERE low_review) AS low_reviews,
 AVG(low_review::int) AS low_review_rate FROM eligible WHERE rn=1 GROUP BY is_late ORDER BY is_late;

-- 5. Exclusions from delivery metrics.
SELECT order_status,COUNT(*) AS orders,
 COUNT(*) FILTER(WHERE order_delivered_customer_date IS NULL) AS missing_actual_delivery,
 COUNT(*) FILTER(WHERE delivery_eligible) AS usable_delivery_rows
FROM analytics.order_fact WHERE order_purchase_timestamp>=TIMESTAMP '2017-01-01'
 AND order_purchase_timestamp<TIMESTAMP '2018-08-01' GROUP BY order_status ORDER BY orders DESC;

-- 6. Check sparse tails and month coverage before comparing periods.
SELECT purchase_month,COUNT(*) AS all_orders,MIN(order_purchase_timestamp)::date AS first_purchase_day,
 MAX(order_purchase_timestamp)::date AS last_purchase_day
FROM analytics.order_fact GROUP BY purchase_month ORDER BY purchase_month;

