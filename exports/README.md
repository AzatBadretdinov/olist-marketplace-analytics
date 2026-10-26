# Выгрузки PostgreSQL

Generated snapshots; не редактировать вручную.
- order_fact.csv — одна строка на заказ, вся история.
- monthly_state.csv — месяц × штат, основной период.
- categories.csv — категории доставленных товаров, основной период.
- workbook_source.json — небольшие агрегаты и метаданные для Excel.

Обновление: python scripts/refresh_from_postgres.py.
Client-side COPY не требует доступа PostgreSQL к папкам компьютера.
Альтернатива для текущего локального пути: sql/07_export_data.sql.

