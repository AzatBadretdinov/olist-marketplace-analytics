-- Run in pgAdmin Query Tool connected to database olist.
-- Server-side COPY: PostgreSQL must be able to read D:/data_analyst/project1/data/.
-- One atomic DO statement: errors roll back all changes in this load.
-- Empty tables are loaded; tables with expected row counts are skipped.
-- Matching row counts alone do not prove content equality.
DO $load$
DECLARE n bigint;
BEGIN
    LOCK TABLE raw.customers IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.customers;
    IF n = 0 THEN
        COPY raw.customers FROM 'D:/data_analyst/project1/data/olist_customers_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.customers;
        IF n <> 99441 THEN
            RAISE EXCEPTION 'customers: expected 99441 rows, got %', n;
        END IF;
        RAISE NOTICE 'customers: loaded % rows', n;
    ELSIF n = 99441 THEN
        RAISE NOTICE 'customers: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'customers: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.orders IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.orders;
    IF n = 0 THEN
        COPY raw.orders FROM 'D:/data_analyst/project1/data/olist_orders_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.orders;
        IF n <> 99441 THEN
            RAISE EXCEPTION 'orders: expected 99441 rows, got %', n;
        END IF;
        RAISE NOTICE 'orders: loaded % rows', n;
    ELSIF n = 99441 THEN
        RAISE NOTICE 'orders: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'orders: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.order_items IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.order_items;
    IF n = 0 THEN
        COPY raw.order_items FROM 'D:/data_analyst/project1/data/olist_order_items_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.order_items;
        IF n <> 112650 THEN
            RAISE EXCEPTION 'order_items: expected 112650 rows, got %', n;
        END IF;
        RAISE NOTICE 'order_items: loaded % rows', n;
    ELSIF n = 112650 THEN
        RAISE NOTICE 'order_items: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'order_items: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.payments IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.payments;
    IF n = 0 THEN
        COPY raw.payments FROM 'D:/data_analyst/project1/data/olist_order_payments_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.payments;
        IF n <> 103886 THEN
            RAISE EXCEPTION 'payments: expected 103886 rows, got %', n;
        END IF;
        RAISE NOTICE 'payments: loaded % rows', n;
    ELSIF n = 103886 THEN
        RAISE NOTICE 'payments: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'payments: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.reviews IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.reviews;
    IF n = 0 THEN
        COPY raw.reviews FROM 'D:/data_analyst/project1/data/olist_order_reviews_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.reviews;
        IF n <> 99224 THEN
            RAISE EXCEPTION 'reviews: expected 99224 rows, got %', n;
        END IF;
        RAISE NOTICE 'reviews: loaded % rows', n;
    ELSIF n = 99224 THEN
        RAISE NOTICE 'reviews: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'reviews: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.products IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.products;
    IF n = 0 THEN
        COPY raw.products FROM 'D:/data_analyst/project1/data/olist_products_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.products;
        IF n <> 32951 THEN
            RAISE EXCEPTION 'products: expected 32951 rows, got %', n;
        END IF;
        RAISE NOTICE 'products: loaded % rows', n;
    ELSIF n = 32951 THEN
        RAISE NOTICE 'products: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'products: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.sellers IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.sellers;
    IF n = 0 THEN
        COPY raw.sellers FROM 'D:/data_analyst/project1/data/olist_sellers_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.sellers;
        IF n <> 3095 THEN
            RAISE EXCEPTION 'sellers: expected 3095 rows, got %', n;
        END IF;
        RAISE NOTICE 'sellers: loaded % rows', n;
    ELSIF n = 3095 THEN
        RAISE NOTICE 'sellers: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'sellers: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.geolocation IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.geolocation;
    IF n = 0 THEN
        COPY raw.geolocation FROM 'D:/data_analyst/project1/data/olist_geolocation_dataset.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.geolocation;
        IF n <> 1000163 THEN
            RAISE EXCEPTION 'geolocation: expected 1000163 rows, got %', n;
        END IF;
        RAISE NOTICE 'geolocation: loaded % rows', n;
    ELSIF n = 1000163 THEN
        RAISE NOTICE 'geolocation: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'geolocation: unexpected existing row count %; investigate before loading', n;
    END IF;
    LOCK TABLE raw.category_translation IN SHARE ROW EXCLUSIVE MODE;
    SELECT count(*) INTO n FROM raw.category_translation;
    IF n = 0 THEN
        COPY raw.category_translation FROM 'D:/data_analyst/project1/data/product_category_name_translation.csv'
            WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
        SELECT count(*) INTO n FROM raw.category_translation;
        IF n <> 71 THEN
            RAISE EXCEPTION 'category_translation: expected 71 rows, got %', n;
        END IF;
        RAISE NOTICE 'category_translation: loaded % rows', n;
    ELSIF n = 71 THEN
        RAISE NOTICE 'category_translation: skipped, already % rows', n;
    ELSE
        RAISE EXCEPTION 'category_translation: unexpected existing row count %; investigate before loading', n;
    END IF;
END
$load$;

