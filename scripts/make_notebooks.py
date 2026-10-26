"""Create and execute three explanatory notebooks; run with an available Jupyter kernel."""
from pathlib import Path
import os
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
def md(text): return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text)
setup="""from pathlib import Path
import sys
import pandas as pd
from IPython.display import display, Image
ROOT = Path.cwd()
if not (ROOT / 'data').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / 'scripts'))
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 160)
"""
notebooks={
"01_data_understanding.ipynb":[
 md("# Знакомство с данными Olist\n\nЦель — определить смысл строк, ключи и связи до расчёта бизнес-показателей. Исходные CSV не изменяем."),
 code(setup),
 md("## Размеры, пропуски и полные дубликаты\n\nПочтовые префиксы читаем как строки, чтобы сохранить ведущие нули."),
 code("""summary=[]
profiles=[]
for file in sorted((ROOT/'data').glob('*.csv')):
    cols=pd.read_csv(file,nrows=0).columns
    types={c:'string' for c in cols if 'zip_code_prefix' in c}
    df=pd.read_csv(file,dtype=types)
    summary.append({'file':file.name,'rows':len(df),'columns':len(df.columns),
                    'extra_full_duplicates':int(df.duplicated().sum())})
    for col in df:
        profiles.append({'file':file.name,'column':col,'dtype':str(df[col].dtype),
                         'missing':int(df[col].isna().sum()),
                         'unique_non_null':int(df[col].nunique())})
display(pd.DataFrame(summary))
display(pd.DataFrame(profiles).query('missing > 0'))
"""),
 md("## Ключи и идентификация покупателя\n\ncustomer_id связывает запись с заказом. customer_unique_id используется для уникальных покупателей."),
 code("""customers=pd.read_csv(ROOT/'data/olist_customers_dataset.csv',dtype={'customer_zip_code_prefix':'string'})
print('Записей покупателей:',len(customers))
print('Уникальных customer_id:',customers.customer_id.nunique())
print('Уникальных customer_unique_id:',customers.customer_unique_id.nunique())
display(customers.head())
items=pd.read_csv(ROOT/'data/olist_order_items_dataset.csv')
print('Повторяющихся строк составного ключа order_items:',
      items.duplicated(['order_id','order_item_id'],keep=False).sum())
print('order_id в позициях не уникален:',items.order_id.duplicated().any())
"""),
 md("## Связи и ограничения\n\nЗаказ может иметь несколько позиций, оплат и отзывов. Сначала агрегируем дочерние таблицы, затем JOIN. Геолокация содержит повторяющиеся префиксы и полные дубликаты, поэтому не присоединяем её напрямую. Подробные проверки сохранены в data_understanding."),
 code("""display(pd.read_csv(ROOT/'reports/data_understanding/relationships.csv'))
"""),
 md("## Следующий шаг\n\nSQL создаёт raw, загружает CSV, проверяет качество и формирует analytics.order_fact с одной строкой на заказ. Полный словарь: reports/data_understanding/data_dictionary.md.")
],
"02_marketplace_analysis.ipynb":[
 md("# Продажи, регионы и доставка\n\nПокупательские когорты: январь 2017–июль 2018. Валюта BRL. Стоимость товаров доставленных заказов не равна доходу платформы."),
 code(setup),
 code("""from build_analysis import load_fact, START, END
fact=load_fact()
cohort=fact.loc[fact.order_purchase_timestamp.ge(START)&fact.order_purchase_timestamp.lt(END)].copy()
monthly=pd.read_csv(ROOT/'reports/tables/monthly.csv',parse_dates=['purchase_month'])
states=pd.read_csv(ROOT/'reports/tables/states.csv')
categories=pd.read_csv(ROOT/'reports/tables/categories.csv')
print('Всего заказов в витрине:',len(fact),'В выбранном периоде:',len(cohort))
display(pd.read_csv(ROOT/'reports/tables/month_coverage.csv'))
"""),
 md("## Динамика\n\nЗаказы группируются по месяцу покупки. Для сравнения лет берём одинаковые месяцы, а не весь 2017 против части 2018."),
 code("""display(monthly[['purchase_month','delivered_orders','delivered_gmv','average_order_value','gmv_mom']])
jan_jul=monthly.loc[monthly.purchase_month.dt.month.le(7)].groupby(monthly.purchase_month.dt.year).delivered_gmv.sum()
print('GMV Jan-Jul YoY:',f'{jan_jul.loc[2018]/jan_jul.loc[2017]-1:.1%}')
display(Image(filename=str(ROOT/'reports/figures/01_monthly_gmv.png')))
"""),
 md("## Доставка\n\nОпоздание определяется календарными датами. Заказы с неизвестной датой получения не считаются своевременными."),
 code("""eligible=cohort.loc[cohort.delivery_eligible.fillna(False)]
delivered=cohort.loc[cohort.order_status.eq('delivered')]
print('Доставлено:',len(delivered),'Пригодно для доставки:',len(eligible))
print('Исключено:',len(delivered)-len(eligible))
print('Опоздавших:',int(eligible.is_late.sum()),'Доля:',f'{eligible.is_late.mean():.2%}')
print('Сроки, дни:',eligible.delivery_days.quantile([.5,.9,.99]).to_dict())
display(Image(filename=str(ROOT/'reports/figures/02_monthly_late_rate.png')))
display(Image(filename=str(ROOT/'reports/figures/06_delivery_distribution.png')))
"""),
 md("## Регионы\n\nОбъём проблем и доля проблем отвечают на разные вопросы. Порог 300 пригодных заказов здесь используется только для описательного сравнения долей; интервалы Wilson показывают неопределённость."),
 code("""display(states[['customer_state','delivery_eligible','late_orders','late_rate','late_ci_low','late_ci_high']].head(10))
display(states.loc[states.delivery_eligible.ge(300)].sort_values('late_rate',ascending=False).head(10))
display(Image(filename=str(ROOT/'reports/figures/03_state_late_orders.png')))
"""),
 md("## Категории\n\nСуммы GMV категорий складываются. Числа заказов по категориям не складываются: один заказ может включать несколько категорий."),
 code("""display(categories.head(10))
print('Доля десяти крупнейших категорий:',f'{categories.head(10).gmv_share.sum():.1%}')
display(Image(filename=str(ROOT/'reports/figures/04_categories_gmv.png')))
"""),
 md("## Контроль воспроизводимости\n\nНезависимые сверки SQL с raw CSV на уровне каждого заказа и итоговых агрегатов."),
 code("""import json
validation=json.loads((ROOT/'reports/validation.json').read_text(encoding='utf-8'))
display(pd.DataFrame(validation['checks']))
assert all(row['passed'] for row in validation['checks'])
"""),
 md("## Выводы\n\nКонкретные числа и рекомендации: reports/business_report.md. Ни региональные различия, ни динамика продаж не доказывают причину наблюдений. Отдельная статистическая проверка разобрана в следующем ноутбуке.")
],
"03_statistical_analysis.ipynb":[
 md("# Связь опоздания с низкими оценками\n\nЭто наблюдательное исследование, не A/B-тест. H0: доли низких оценок равны у late и on time. H1: отличаются. alpha=0.05, двусторонний тест."),
 code(setup),
 code("""from build_analysis import load_fact, START, END, statistical_analysis
fact=load_fact()
cohort=fact.loc[fact.order_purchase_timestamp.ge(START)&fact.order_purchase_timestamp.lt(END)].copy()
stats=statistical_analysis(cohort)
display(pd.read_csv(ROOT/'reports/tables/review_delivery_groups.csv'))
"""),
 md("## Выборка\n\nОдин первый пригодный заказ с отзывом на customer_unique_id в периоде. Это уменьшает зависимость повторных заказов одного покупателя. Общие продавцы и временные шоки всё ещё могут создавать зависимость."),
 code("""print('Пригодных заказов с отзывами:',stats['eligible_reviewed_orders'])
print('В основной выборке покупателей:',stats['primary_customers'])
print('Поздние:',stats['n_late'],'Своевременные:',stats['n_ontime'])
"""),
 md("## Размер эффекта и интервалы\n\nДоли сопровождаются 95% Wilson-интервалами, разность — Newcombe-интервалом. П.п. — процентные пункты, их нельзя путать с относительным изменением."),
 code("""print('Доля низких оценок late:',f"{stats['rate_late']:.2%}")
print('Доля низких оценок on time:',f"{stats['rate_ontime']:.2%}")
print('Разность:',f"{stats['risk_difference']*100:.2f}",'п.п.')
print('95% CI разности, п.п.:',[round(x*100,2) for x in stats['risk_difference_ci']])
print('Risk ratio:',round(stats['risk_ratio'],2))
print('p:',stats['p_display'],'log10(p):',round(stats['log10_p_value'],1))
display(Image(filename=str(ROOT/'reports/figures/05_reviews_and_delivery.png')))
"""),
 md("## Проверка чувствительности\n\nОсобенно важен момент написания отзыва. При отборе только ответов после получения меняется сама популяция, поэтому оценку нельзя напрямую трактовать как скорректированный причинный эффект."),
 code("""display(pd.DataFrame([{k:v for k,v in s.items() if k!='groups'} for s in stats['sensitivity']]))
print('Разность после стандартизации state × month:',f"{stats['standardized_state_month_rd']*100:.2f}",'п.п.')
print('Страт:',stats['standardized_strata'],'Наблюдений:',stats['standardized_sample_n'])
for sample in stats['sensitivity']:
    print(sample['sample'])
    display(pd.DataFrame(sample['groups']))
"""),
 md("## Интерпретация\n\nСвязь выражена, но её величина существенно чувствительна к времени отзыва. Малая p-value не устраняет смещение отбора, смешивающие факторы и зависимость наблюдений. Нельзя обещать, что устранение опозданий автоматически уменьшит низкие оценки на найденную разность. Следующий обоснованный шаг — детализация маршрутов и отдельно спроектированный пилот вмешательства.")
]
}
def main():
    directory=ROOT/"notebooks"; directory.mkdir(exist_ok=True)
    kernel=os.getenv("OLIST_KERNEL","python3")
    for filename,cells in notebooks.items():
        nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"name":kernel,"display_name":"Python (Olist)","language":"python"}})
        client=NotebookClient(nb,timeout=240,kernel_name=kernel,resources={"metadata":{"path":str(ROOT)}})
        client.execute()
        nb.metadata["kernelspec"] = {"name":"python3","display_name":"Python 3","language":"python"}
        nbf.validate(nb)
        nbf.write(nb,directory/filename)
        print("Executed",filename)
if __name__=="__main__":
    main()


