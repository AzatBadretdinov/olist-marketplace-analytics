# Словарь данных Olist

Сгенерировано data_understand.py. Исходные CSV не изменены.

## customers

Файл: `olist_customers_dataset.csv`.

Запись покупателя для связи с заказом. customer_unique_id объединяет записи одного покупателя.

Кандидат в ключ: customer_id. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| customer_id | str | 0 | 99441 |
| customer_unique_id | str | 0 | 96096 |
| customer_zip_code_prefix | string | 0 | 14994 |
| customer_city | str | 0 | 4119 |
| customer_state | str | 0 | 27 |

## orders

Файл: `olist_orders_dataset.csv`.

Один заказ.

Кандидат в ключ: order_id. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| order_id | str | 0 | 99441 |
| customer_id | str | 0 | 99441 |
| order_status | str | 0 | 8 |
| order_purchase_timestamp | str | 0 | 98875 |
| order_approved_at | str | 160 | 90733 |
| order_delivered_carrier_date | str | 1783 | 81018 |
| order_delivered_customer_date | str | 2965 | 95664 |
| order_estimated_delivery_date | str | 0 | 459 |

## order_items

Файл: `olist_order_items_dataset.csv`.

Одна товарная позиция заказа.

Кандидат в ключ: order_id, order_item_id. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| order_id | str | 0 | 98666 |
| order_item_id | int64 | 0 | 21 |
| product_id | str | 0 | 32951 |
| seller_id | str | 0 | 3095 |
| shipping_limit_date | str | 0 | 93318 |
| price | float64 | 0 | 5968 |
| freight_value | float64 | 0 | 6999 |

## order_payments

Файл: `olist_order_payments_dataset.csv`.

Одна запись об оплате заказа.

Кандидат в ключ: order_id, payment_sequential. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| order_id | str | 0 | 99440 |
| payment_sequential | int64 | 0 | 29 |
| payment_type | str | 0 | 5 |
| payment_installments | int64 | 0 | 24 |
| payment_value | float64 | 0 | 29077 |

## order_reviews

Файл: `olist_order_reviews_dataset.csv`.

Одна запись отзыва о заказе. Проверяем пару review_id и order_id как кандидат в ключ.

Кандидат в ключ: review_id, order_id. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| review_id | str | 0 | 98410 |
| order_id | str | 0 | 98673 |
| review_score | int64 | 0 | 5 |
| review_comment_title | str | 87656 | 4527 |
| review_comment_message | str | 58247 | 36159 |
| review_creation_date | str | 0 | 636 |
| review_answer_timestamp | str | 0 | 98248 |

## products

Файл: `olist_products_dataset.csv`.

Один товар.

Кандидат в ключ: product_id. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| product_id | str | 0 | 32951 |
| product_category_name | str | 610 | 73 |
| product_name_lenght | float64 | 610 | 66 |
| product_description_lenght | float64 | 610 | 2960 |
| product_photos_qty | float64 | 610 | 19 |
| product_weight_g | float64 | 2 | 2204 |
| product_length_cm | float64 | 2 | 99 |
| product_height_cm | float64 | 2 | 102 |
| product_width_cm | float64 | 2 | 95 |

## sellers

Файл: `olist_sellers_dataset.csv`.

Один продавец.

Кандидат в ключ: seller_id. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| seller_id | str | 0 | 3095 |
| seller_zip_code_prefix | string | 0 | 2246 |
| seller_city | str | 0 | 611 |
| seller_state | str | 0 | 23 |

## geolocation

Файл: `olist_geolocation_dataset.csv`.

Географическая запись для почтового префикса. Префикс может повторяться; ключ пока не выбран.

Кандидат в ключ: не выбран. Статус: NOT_SELECTED.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| geolocation_zip_code_prefix | string | 0 | 19015 |
| geolocation_lat | float64 | 0 | 717360 |
| geolocation_lng | float64 | 0 | 717613 |
| geolocation_city | str | 0 | 8011 |
| geolocation_state | str | 0 | 27 |

## category_translation

Файл: `product_category_name_translation.csv`.

Перевод названия категории с португальского на английский.

Кандидат в ключ: product_category_name. Статус: OK.

| Столбец | pandas | Пропуски | Уникальные без NA |
|---|---|---:|---:|
| product_category_name | str | 0 | 71 |
| product_category_name_english | str | 0 | 71 |

## Связи

Кратность измерена по непустым значениям текущей выгрузки, а не задана как бизнес-правило.

- `orders.customer_id` → `customers.customer_id`: 1:1; непустых строк без соответствия: 0.
- `order_items.order_id` → `orders.order_id`: many:1; непустых строк без соответствия: 0.
- `order_items.product_id` → `products.product_id`: many:1; непустых строк без соответствия: 0.
- `order_items.seller_id` → `sellers.seller_id`: many:1; непустых строк без соответствия: 0.
- `order_payments.order_id` → `orders.order_id`: many:1; непустых строк без соответствия: 0.
- `order_reviews.order_id` → `orders.order_id`: many:1; непустых строк без соответствия: 0.
- `products.product_category_name` → `category_translation.product_category_name`: many:1; непустых строк без соответствия: 13.
- `customers.customer_zip_code_prefix` → `geolocation.geolocation_zip_code_prefix`: many:many; непустых строк без соответствия: 278.
- `sellers.seller_zip_code_prefix` → `geolocation.geolocation_zip_code_prefix`: many:many; непустых строк без соответствия: 7.