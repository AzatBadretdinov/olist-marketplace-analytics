# Воспроизведение и зависимости

Фактический расчёт выполнен на девяти CSV из data/ через PostgreSQL 18.
Данные выгружены настоящим COPY из analytics views; pandas не подменяет SQL-этап.
SQL-результат сверки: 99 441 raw orders = 99 441 fact rows = 99 441 distinct order_id;
GMV, freight и payments совпадают с raw.
В Python прошли 14 дополнительных независимых проверок.

Тестированное окружение:
- Python 3.12.14
- pandas 3.0.1
- NumPy 2.5.4
- SciPy 1.18.1
- matplotlib 3.11.2
- psycopg 3.3.6
- nbformat 5.11.1
- nbclient 0.11.0
- ipykernel 7.4.0
- Node.js и @oai/artifact-tool для сборки Excel

requirements.txt задаёт совместимые диапазоны; requirements-lock.txt фиксирует основные версии расчёта.
Для чистого запуска сначала получи исходные CSV; exports/ генерируется заново.
Текущие SQL02 и SQL07 содержат локальный путь Windows. Переносимый путь — Python client-side COPY.

Первичный контроль качества выполнен 2026-10-26; полный анализ завершён 2026-10-27 (Europe/Moscow).
Даты проверки в комментариях SQL04 являются историческим снимком, а не автоматически обновляемыми значениями.

Excel проверен в Artifact Tool: пересчёт KPI, фильтры штата/месяца, ошибочный диапазон,
отсутствие ошибок формул, визуальный просмотр всех пяти листов и наличие native chart XML.
В настольном Excel книга в этой сессии не открывалась.


Дополнительно весь расчёт успешно выполнен в .venv проекта с pandas 3.1.0; остальные основные версии совпали. Сохранённый validation.json относится к этому финальному запуску.

## Дополнительная сборка Excel

Готовую книгу можно использовать в Excel без установки JavaScript-зависимостей.
Для повторной сборки scripts/build_dashboard.mjs нужен Node.js и отдельно доступный пакет @oai/artifact-tool.
Этот пакет не входит в Python requirements.txt. Сборщик ищет его среди локально установленных модулей.
При внешней установке задай ARTIFACT_NODE_MODULES — путь к каталогу node_modules:

```powershell
$env:ARTIFACT_NODE_MODULES = "C:/path/to/node_modules"
node scripts/build_dashboard.mjs
```

Результат по умолчанию: reports/marketplace_dashboard.xlsx.
Сборка использует exports/workbook_source.json, подготовленный Python-пайплайном.
Предпросмотры сохраняются в reports/workbook_previews/ и не нужны для использования готовой книги.
