-- Проверки качества данных Olist, база olist, схема raw.
-- Выполнено в PostgreSQL через pgAdmin 2026-10-26.
-- Все команды только читают данные. Комментарии с результатами — снимок на дату проверки.
-- issue_rows = количество строк, удовлетворяющих условию проверки.
-- Нулевой результат означает отсутствие указанной проблемы, а не полную гарантию качества.

BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;

-- ============================================================
-- 1. Ключи
-- ============================================================

-- Проверка: customers: строки с пропуском ключа.
SELECT COUNT(*) AS issue_rows
FROM raw.customers
WHERE customer_id IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Ключ должен быть заполнен во всех строках.

-- Проверка: customers: все строки с повторяющимся ключом.
SELECT COALESCE(SUM(group_rows), 0)::bigint AS issue_rows
FROM (
    SELECT customer_id, COUNT(*) AS group_rows
    FROM raw.customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) AS duplicates;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Считаются все строки повторяющихся групп, а не только лишние копии. Ключ должен быть уникален.

-- Проверка: orders: строки с пропуском ключа.
SELECT COUNT(*) AS issue_rows
FROM raw.orders
WHERE order_id IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Ключ должен быть заполнен во всех строках.

-- Проверка: orders: все строки с повторяющимся ключом.
SELECT COALESCE(SUM(group_rows), 0)::bigint AS issue_rows
FROM (
    SELECT order_id, COUNT(*) AS group_rows
    FROM raw.orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
) AS duplicates;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Считаются все строки повторяющихся групп, а не только лишние копии. Ключ должен быть уникален.

-- Проверка: order_items: строки с пропуском ключа.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE order_id IS NULL OR order_item_id IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Ключ должен быть заполнен во всех строках.

-- Проверка: order_items: все строки с повторяющимся ключом.
SELECT COALESCE(SUM(group_rows), 0)::bigint AS issue_rows
FROM (
    SELECT order_id, order_item_id, COUNT(*) AS group_rows
    FROM raw.order_items
    GROUP BY order_id, order_item_id
    HAVING COUNT(*) > 1
) AS duplicates;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Считаются все строки повторяющихся групп, а не только лишние копии. Ключ должен быть уникален.

-- ============================================================
-- 2. Связи
-- ============================================================

-- Проверка: orders.customer_id: пропуски поля связи.
SELECT COUNT(*) AS issue_rows
FROM raw.orders
WHERE customer_id IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Пропуски поля связи считаются отдельно от отсутствующих соответствий.

-- Проверка: orders.customer_id: непустые значения без соответствия в customers.
SELECT COUNT(*) AS issue_rows
FROM raw.orders AS child
WHERE child.customer_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM raw.customers AS parent
      WHERE parent.customer_id = child.customer_id
  );
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Считаются исходные строки без родительской записи. NOT EXISTS не размножает строки при повторах в родительской таблице.

-- Проверка: order_items.order_id: пропуски поля связи.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE order_id IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Пропуски поля связи считаются отдельно от отсутствующих соответствий.

-- Проверка: order_items.order_id: непустые значения без соответствия в orders.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items AS child
WHERE child.order_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM raw.orders AS parent
      WHERE parent.order_id = child.order_id
  );
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Считаются исходные строки без родительской записи. NOT EXISTS не размножает строки при повторах в родительской таблице.

-- Проверка: order_items.product_id: пропуски поля связи.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE product_id IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Пропуски поля связи считаются отдельно от отсутствующих соответствий.

-- Проверка: order_items.product_id: непустые значения без соответствия в products.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items AS child
WHERE child.product_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM raw.products AS parent
      WHERE parent.product_id = child.product_id
  );
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Считаются исходные строки без родительской записи. NOT EXISTS не размножает строки при повторах в родительской таблице.

-- ============================================================
-- 3. Значения
-- ============================================================

-- Проверка: order_items.price: отрицательные значения.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE price < 0;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Отрицательные суммы требуют проверки смысла записи. Нулевые значения этой проверкой не считаются ошибкой.

-- Проверка: order_items.price: пропуски.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE price IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: NULL не проходит условие < 0, поэтому пропуски проверяются отдельно.

-- Проверка: order_items.freight_value: отрицательные значения.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE freight_value < 0;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Отрицательные суммы требуют проверки смысла записи. Нулевые значения этой проверкой не считаются ошибкой.

-- Проверка: order_items.freight_value: пропуски.
SELECT COUNT(*) AS issue_rows
FROM raw.order_items
WHERE freight_value IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: NULL не проходит условие < 0, поэтому пропуски проверяются отдельно.

-- Проверка: payments.payment_value: отрицательные значения.
SELECT COUNT(*) AS issue_rows
FROM raw.payments
WHERE payment_value < 0;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Отрицательные суммы требуют проверки смысла записи. Нулевые значения этой проверкой не считаются ошибкой.

-- Проверка: payments.payment_value: пропуски.
SELECT COUNT(*) AS issue_rows
FROM raw.payments
WHERE payment_value IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: NULL не проходит условие < 0, поэтому пропуски проверяются отдельно.

-- Проверка: reviews: оценки вне диапазона 1–5.
SELECT COUNT(*) AS issue_rows
FROM raw.reviews
WHERE review_score NOT BETWEEN 1 AND 5;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Допустимая заполненная оценка — целое число от 1 до 5.

-- Проверка: reviews: пропуски оценки.
SELECT COUNT(*) AS issue_rows
FROM raw.reviews
WHERE review_score IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Пропуски оценки нельзя автоматически приравнивать к низким оценкам.

-- Проверка: orders: фактическая доставка раньше покупки.
SELECT COUNT(*) AS issue_rows
FROM raw.orders
WHERE order_delivered_customer_date < order_purchase_timestamp;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Отрицательная длительность доставки — хронологическая аномалия; такие записи нужно изучить отдельно.

-- Проверка: orders: пропуски времени покупки.
SELECT COUNT(*) AS issue_rows
FROM raw.orders
WHERE order_purchase_timestamp IS NULL;
-- Результат на 2026-10-26: 0 строк.
-- Интерпретация: Без времени покупки нельзя рассчитать длительность доставки.

-- Проверка: orders: статус delivered, но нет фактической даты доставки.
SELECT COUNT(*) AS issue_rows
FROM raw.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NULL;
-- Результат на 2026-10-26: 8 строк.
-- Интерпретация: Для доставленных заказов пропуск даты мешает вычислению срока и опоздания. Не все пропуски доставки во всех статусах являются ошибкой.
-- Решение для дальнейшего анализа: эти 8 заказов сохраняем в raw и учитываем
-- в количестве заказов согласно определению метрики. Их нельзя включать
-- в расчёт фактического срока и опоздания доставки: дата неизвестна.
-- В отчёте по доставке отдельно показываем число исключённых записей.

-- Просмотр найденных записей: запрос возвращает 8 заказов при текущих данных.
SELECT order_id, order_status, order_purchase_timestamp,
       order_delivered_carrier_date, order_delivered_customer_date,
       order_estimated_delivery_date
FROM raw.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NULL
ORDER BY order_purchase_timestamp, order_id;

COMMIT;

-- Итог: проверенные ключи и связи прошли проверки; отрицательных сумм,
-- некорректных оценок и доставки раньше покупки не обнаружено.
-- Найдено 8 delivered-заказов без фактической даты доставки.
-- Это ограниченный набор проверок: он не заменяет обследование всех полей,
-- статусов, временных последовательностей и согласованности сумм.

