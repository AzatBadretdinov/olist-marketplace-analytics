"""Olist: SQL exports -> validated analysis, statistics and report.
Run from any directory: python scripts/build_analysis.py
No database credentials or raw data changes.
"""
from pathlib import Path
import hashlib
import json
import math
import platform
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
START = pd.Timestamp("2017-01-01")
END = pd.Timestamp("2018-08-01")
TABLE_DIR = ROOT / "reports" / "tables"
FIG_DIR = ROOT / "reports" / "figures"
DOC_DIR = ROOT / "docs"
EXPORT_DIR = ROOT / "exports"
COLORS = {"main": "#245A81", "accent": "#DB7650", "neutral": "#78909C"}

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

def wilson(k, n, alpha=0.05):
    if n == 0:
        return (float("nan"), float("nan"))
    z = norm.ppf(1-alpha/2)
    p = k/n
    denominator = 1+z*z/n
    center = (p+z*z/(2*n))/denominator
    radius = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return center-radius, center+radius

def load_fact():
    df = pd.read_csv(EXPORT_DIR / "order_fact.csv", true_values=["t"], false_values=["f"])
    for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
                "order_delivered_customer_date", "order_estimated_delivery_date",
                "review_answer_timestamp", "purchase_month"]:
        df[col] = pd.to_datetime(df[col], format="mixed")
    for col in ["delivery_eligible", "is_late", "low_review"]:
        df[col] = df[col].astype("boolean")
    return df

def verify_sources(fact, monthly_state, categories):
    """Independent raw-to-SQL checks catch duplicate joins and wrong aggregations."""
    checks = []
    def check(name, condition, detail):
        checks.append({"check": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(f"{name}: {detail}")
    orders = pd.read_csv(ROOT / "data/olist_orders_dataset.csv")
    items = pd.read_csv(ROOT / "data/olist_order_items_dataset.csv")
    payments = pd.read_csv(ROOT / "data/olist_order_payments_dataset.csv")
    reviews = pd.read_csv(ROOT / "data/olist_order_reviews_dataset.csv")
    check("one_row_per_order", fact.order_id.is_unique and len(fact)==len(orders), str(len(fact)))
    check("same_order_ids", set(fact.order_id)==set(orders.order_id), "raw vs SQL")
    for field, source, value_col in [("item_gmv",items,"price"),("freight_value",items,"freight_value"),
                                      ("payment_value",payments,"payment_value")]:
        expected = source.groupby("order_id")[value_col].sum().reindex(fact.order_id)
        actual = fact[field].to_numpy()
        # No items -> SQL coalesces merchandise and freight to zero; missing payments remain NULL.
        if field != "payment_value":
            expected = expected.fillna(0)
        check(field+"_per_order", np.allclose(actual,expected.to_numpy(),atol=1e-7,rtol=0,equal_nan=True),
              "Independent per-order raw aggregation")
    reviews["review_answer_timestamp"] = pd.to_datetime(reviews.review_answer_timestamp, format="mixed")
    reviews["review_creation_date"] = pd.to_datetime(reviews.review_creation_date, format="mixed")
    latest = reviews.sort_values(["order_id","review_answer_timestamp","review_creation_date","review_id"],
                                 ascending=[True,False,False,False],na_position="last").drop_duplicates("order_id")
    expected_scores = latest.set_index("order_id").review_score.reindex(fact.order_id)
    check("latest_review_selection", np.allclose(fact.review_score,expected_scores,equal_nan=True),
          "Latest answer timestamp; then creation date and review_id")
    cohort = fact.loc[fact.order_purchase_timestamp.ge(START)&fact.order_purchase_timestamp.lt(END)]
    delivered = cohort.loc[cohort.order_status.eq("delivered")]
    eligible = cohort.loc[cohort.delivery_eligible.fillna(False)]
    for name,a,b in [("cohort_orders",monthly_state.all_orders.sum(),len(cohort)),
                     ("delivered_orders",monthly_state.delivered_orders.sum(),len(delivered)),
                     ("eligible_delivery",monthly_state.delivery_eligible.sum(),len(eligible)),
                     ("late_orders",monthly_state.late_orders.sum(),int(eligible.is_late.sum())),
                     ("gmv_monthly",monthly_state.delivered_gmv.sum(),delivered.item_gmv.sum()),
                     ("gmv_categories",categories.delivered_gmv.sum(),delivered.item_gmv.sum())]:
        check(name, np.isclose(a,b,atol=.001,rtol=0), f"SQL aggregate={a}; fact={b}")
    valid = fact.loc[fact.delivery_eligible.fillna(False)]
    calendar_late = valid.order_delivered_customer_date.dt.normalize().gt(valid.order_estimated_delivery_date.dt.normalize())
    check("late_calendar_definition", np.array_equal(calendar_late.to_numpy(),valid.is_late.to_numpy()),
          "Date comparison, not midnight timestamp comparison")
    check("delivered_orders_have_items", delivered.item_count.gt(0).all(), "Required for merchandise AOV")
    return checks

def statistical_analysis(cohort):
    """One predeclared exploratory association test, alpha=.05, two-sided."""
    eligible = cohort.loc[cohort.delivery_eligible.fillna(False)&cohort.low_review.notna()
                           &cohort.customer_unique_id.notna()].copy()
    primary = eligible.sort_values(["order_purchase_timestamp","order_id"]).drop_duplicates("customer_unique_id")
    def group_counts(sample):
        return sample.groupby("is_late",observed=True).agg(
            reviewed_orders=("order_id","size"),low_reviews=("low_review","sum")).reset_index()
    counts = group_counts(primary)
    late = counts.loc[counts.is_late.eq(True)].iloc[0]
    ontime = counts.loc[counts.is_late.eq(False)].iloc[0]
    n1,n0 = int(late.reviewed_orders),int(ontime.reviewed_orders)
    k1,k0 = int(late.low_reviews),int(ontime.low_reviews)
    p1,p0 = k1/n1,k0/n0
    pooled = (k1+k0)/(n1+n0)
    se = math.sqrt(pooled*(1-pooled)*(1/n1+1/n0))
    z = (p1-p0)/se
    logp = float(math.log(2)+norm.logsf(abs(z)))
    p_value = float(2*norm.sf(abs(z)))
    l1,u1 = wilson(k1,n1); l0,u0 = wilson(k0,n0)
    rd = p1-p0
    # Newcombe hybrid-score interval for difference between two independent proportions.
    rd_low = rd-math.sqrt((p1-l1)**2+(u0-p0)**2)
    rd_high = rd+math.sqrt((u1-p1)**2+(p0-l0)**2)
    rr = p1/p0
    rr_se = math.sqrt(1/k1-1/n1+1/k0-1/n0)
    sensitivity = []
    for label,sample in [("all_eligible_reviewed_orders",eligible),
                          ("answers_on_or_after_actual_delivery", primary.loc[
                              primary.review_answer_timestamp.ge(primary.order_delivered_customer_date)])]:
        gc = group_counts(sample)
        rates = {bool(r.is_late):int(r.low_reviews)/int(r.reviewed_orders) for r in gc.itertuples()}
        sensitivity.append({"sample":label,"n":len(sample),
                            "groups":[{"is_late":bool(r.is_late),"n":int(r.reviewed_orders),"low_reviews":int(r.low_reviews)} for r in gc.itertuples()],
                            "risk_difference":rates.get(True,0)-rates.get(False,0)})
    # Descriptive standardization within state x purchase month; not a causal adjustment.
    strata = primary.groupby(["customer_state","purchase_month","is_late"],observed=True).agg(
        n=("order_id","size"),k=("low_review","sum")).reset_index()
    ns = strata.pivot(index=["customer_state","purchase_month"],columns="is_late",values="n")
    ks = strata.pivot(index=["customer_state","purchase_month"],columns="is_late",values="k")
    usable = ns.loc[ns[True].ge(10)&ns[False].ge(10)].index
    ns,ks = ns.loc[usable],ks.loc[usable]
    weights = ns.sum(axis=1)/ns.to_numpy().sum()
    adjusted_rd = float(((ks[True]/ns[True]-ks[False]/ns[False])*weights).sum())
    result = dict(alpha=.05,hypothesis="H0: P(low review | late) = P(low review | on time); H1: unequal",
        test="Two-sided pooled two-proportion z-test",
        primary_sample="First eligible reviewed order per customer in reporting cohort",
        n_late=n1,low_late=k1,n_ontime=n0,low_ontime=k0,
        rate_late=p1,rate_ontime=p0,rate_late_ci=[l1,u1],rate_ontime_ci=[l0,u0],
        risk_difference=rd,risk_difference_ci=[rd_low,rd_high],
        risk_ratio=rr,risk_ratio_ci=[math.exp(math.log(rr)-1.96*rr_se),math.exp(math.log(rr)+1.96*rr_se)],
        z_statistic=z,p_value=p_value,log10_p_value=logp/math.log(10),
        p_display="< 1e-300" if p_value==0 else f"{p_value:.3g}",
        sensitivity=sensitivity,standardized_state_month_rd=adjusted_rd,
        standardized_strata=len(usable),standardized_sample_n=int(ns.to_numpy().sum()),
        eligible_reviewed_orders=len(eligible),primary_customers=len(primary),
        independence_note="One observation per customer reduces repeat-customer dependence; shared seller/region/time shocks can still correlate outcomes.",
        interpretation="Association in an observational, reviewed-delivered sample; not an A/B test and not proof of causality.")
    counts["low_review_rate"] = counts.low_reviews/counts.reviewed_orders
    counts["ci_low"] = counts.apply(lambda r:wilson(int(r.low_reviews),int(r.reviewed_orders))[0],axis=1)
    counts["ci_high"] = counts.apply(lambda r:wilson(int(r.low_reviews),int(r.reviewed_orders))[1],axis=1)
    counts.to_csv(TABLE_DIR/"review_delivery_groups.csv",index=False)
    save_json(ROOT/"reports/statistics.json",result)
    return result

def make_figures(monthly,states,categories,stats,eligible):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                         "axes.spines.top":False,"axes.spines.right":False,
                         "figure.facecolor":"white","axes.titleweight":"bold"})
    def save(name):
        plt.tight_layout()
        plt.savefig(FIG_DIR/name,dpi=170,bbox_inches="tight")
        plt.close()
    fig,ax=plt.subplots(figsize=(10,4.4))
    ax.plot(monthly.purchase_month,monthly.delivered_gmv/1e6,color=COLORS["main"],marker="o",ms=4)
    ax.set(title="Delivered merchandise value by purchase month",ylabel="BRL million",xlabel="Purchase month")
    ax.grid(axis="y",alpha=.15); fig.autofmt_xdate()
    save("01_monthly_gmv.png")
    fig,ax=plt.subplots(figsize=(10,4.4))
    ax.plot(monthly.purchase_month,monthly.late_rate*100,color=COLORS["accent"],marker="o",ms=4)
    ax.set(title="Late delivery rate by purchase cohort",ylabel="% of delivery-eligible orders",xlabel="Purchase month")
    ax.set_ylim(bottom=0); ax.grid(axis="y",alpha=.15); fig.autofmt_xdate()
    save("02_monthly_late_rate.png")
    top=states.sort_values("late_orders",ascending=False).head(10).sort_values("late_orders")
    fig,ax=plt.subplots(figsize=(9,5))
    ax.barh(top.customer_state,top.late_orders,color=COLORS["main"])
    ax.set(title="States with the most late orders",xlabel="Late orders in reporting cohort",ylabel="Customer state")
    ax.grid(axis="x",alpha=.15); save("03_state_late_orders.png")
    top=categories.head(10).sort_values("delivered_gmv")
    fig,ax=plt.subplots(figsize=(10,5))
    ax.barh(top.category.str.replace("_"," "),top.delivered_gmv/1e6,color=COLORS["main"])
    ax.set(title="Top categories by delivered merchandise value",xlabel="BRL million",ylabel="")
    save("04_categories_gmv.png")
    fig,ax=plt.subplots(figsize=(7.5,4.5))
    rates=np.array([stats["rate_ontime"],stats["rate_late"]])
    low=np.array([stats["rate_ontime_ci"][0],stats["rate_late_ci"][0]])
    high=np.array([stats["rate_ontime_ci"][1],stats["rate_late_ci"][1]])
    ax.bar(["On time","Late"],rates*100,color=[COLORS["main"],COLORS["accent"]])
    ax.errorbar([0,1],rates*100,yerr=np.vstack([(rates-low)*100,(high-rates)*100]),
                fmt="none",ecolor="#263238",capsize=6)
    for i,p in enumerate(rates): ax.text(i,p*100+2,f"{p:.1%}",ha="center")
    ax.set(title="Low review rates and 95% Wilson intervals",ylabel="Reviews with score 1-2 (%)",
           xlabel="First eligible reviewed order per customer")
    ax.set_ylim(0,min(100,max(rates)*100+15)); save("05_reviews_and_delivery.png")
    fig,ax=plt.subplots(figsize=(9,4.5))
    values=eligible.delivery_days
    ax.hist(values,bins=np.arange(0,math.ceil(values.max())+5,5),color=COLORS["main"],edgecolor="white")
    ax.axvline(values.median(),color=COLORS["accent"],label=f"Median: {values.median():.1f} days")
    ax.set(title="Actual delivery duration",xlabel="Days from purchase to delivery",ylabel="Orders")
    ax.legend(frameon=False); save("06_delivery_distribution.png")

def write_report(kpi,monthly,states,categories,stats,exclusions):
    top_state=states.sort_values("late_orders",ascending=False).iloc[0]
    high_rate=states.loc[states.delivery_eligible.ge(300)].sort_values("late_rate",ascending=False).iloc[0]
    focus_state=states.sort_values("late_excess_vs_overall",ascending=False).iloc[0]
    peak=monthly.loc[monthly.delivered_gmv.idxmax()]
    late_peak=monthly.loc[monthly.late_rate.idxmax()]
    top_cat=categories.iloc[0]
    yoy=(monthly.loc[monthly.purchase_month.between("2018-01-01","2018-07-01"),"delivered_gmv"].sum()
         /monthly.loc[monthly.purchase_month.between("2017-01-01","2017-07-01"),"delivered_gmv"].sum()-1)
    kpi["gmv_yoy_jan_jul"]=float(yoy)
    def num(x):return f"{x:,.0f}".replace(","," ")
    report=f"""# Olist: продажи, доставка и клиентский опыт

Период покупок: 01.01.2017–31.07.2018. Валюта: BRL.
Источник: девять локальных CSV Olist, загруженных в PostgreSQL.
Это исторический учебный бизнес-кейс; выводы не описывают текущую работу Olist.

## Основные результаты

- Заказов в периоде: **{num(kpi['all_orders'])}**, доставленных: **{num(kpi['delivered_orders'])}**.
- Стоимость товаров в доставленных заказах: **{num(kpi['delivered_gmv'])} BRL**. Средний чек товаров: **{kpi['average_order_value']:.2f} BRL**. Это не выручка платформы и не прибыль.
- Для оценки доставки пригодны {num(kpi['delivery_eligible'])} заказов. Опоздало {num(kpi['late_orders'])}: **{kpi['late_rate']:.2%}**.
- Медианный срок доставки: **{kpi['median_delivery_days']:.1f} дня**, 90-й процентиль: **{kpi['p90_delivery_days']:.1f} дня**.
- Стоимость доставленных товаров за январь–июль 2018 выше января–июля 2017 на **{yoy:.1%}**. Это сравнение одинаковых календарных месяцев, но не доказательство органического роста: состав покрытия выгрузки мог меняться.
- Наибольшая месячная стоимость доставленных товаров: {peak.purchase_month:%Y-%m}, **{num(peak.delivered_gmv)} BRL**. Наибольшая доля опозданий: {late_peak.purchase_month:%Y-%m}, **{late_peak.late_rate:.1%}**.
- Больше всего опоздавших заказов в **{top_state.customer_state}**: {num(top_state.late_orders)} при доле {top_state.late_rate:.1%}. Среди штатов с минимум 300 пригодными заказами самая высокая доля в **{high_rate.customer_state}**: {high_rate.late_rate:.1%} при n={num(high_rate.delivery_eligible)}.
- По сочетанию объёма и превышения общей доли выделяется **{focus_state.customer_state}**: {num(focus_state.late_orders)} опозданий из {num(focus_state.delivery_eligible)} ({focus_state.late_rate:.1%}). Превышение общей доли — ориентир для приоритизации, не оценка предотвратимых опозданий.
- Категория с наибольшей стоимостью товаров: **{top_cat.category}**, {num(top_cat.delivered_gmv)} BRL ({top_cat.gmv_share:.1%} периода). Суммарная доля десяти крупнейших категорий: {categories.head(10).gmv_share.sum():.1%}.

## Статистическая проверка

В качестве основной выборки взят первый пригодный заказ с отзывом каждого покупателя в периоде.
Низкая оценка — 1 или 2. Опоздание определяется по календарной дате, поэтому доставка вечером обещанного дня считается своевременной.

| Группа | Заказов | Низких оценок | Доля |
|---|---:|---:|---:|
| В срок | {num(stats['n_ontime'])} | {num(stats['low_ontime'])} | {stats['rate_ontime']:.2%} |
| С опозданием | {num(stats['n_late'])} | {num(stats['low_late'])} | {stats['rate_late']:.2%} |

Разность долей: **{stats['risk_difference']*100:.2f} п.п.**, 95% интервал Newcombe:
**[{stats['risk_difference_ci'][0]*100:.2f}; {stats['risk_difference_ci'][1]*100:.2f}] п.п.**
Отношение долей: **{stats['risk_ratio']:.2f}**.
Двусторонний z-тест двух долей: p **{stats['p_display']}** при alpha=0.05.
При численном округлении p до нуля отдельно сохранён log10(p)={stats['log10_p_value']:.1f}.
Эффект по величине и интервалу важнее самого факта малого p-value.

Описательная стандартизация по штату и месяцу даёт разность
{stats['standardized_state_month_rd']*100:.2f} п.п. на {stats['standardized_strata']} стратах с минимум 10 заказами в каждой группе.
Она относится к подвыборке {num(stats['standardized_sample_n'])} покупателей и не устраняет все смешивающие факторы.

Проверка чувствительности к времени отзыва: если оставить только ответы после фактического получения,
разность долей уменьшается до **{stats['sensitivity'][1]['risk_difference']*100:.2f} п.п.**
при n={num(stats['sensitivity'][1]['n'])}. На всех пригодных заказах с отзывами она составляет
{stats['sensitivity'][0]['risk_difference']*100:.2f} п.п.
Сильное изменение указывает на важность времени ответа и отбора наблюдений:
часть отзывов написана ещё до получения заказа. Основную оценку нельзя переносить на впечатления после получения.

Это **связь, а не установленная причина**. Выборка ограничена доставленными заказами с отзывом,
а оценка может зависеть от товара, продавца, обещанного срока и других факторов.
Один заказ на покупателя уменьшает зависимость наблюдений, но общие продавцы и временные шоки всё ещё могут её создавать.

## Рекомендации и способ проверки

| Приоритет | Действие | Основание | Как оценить результат |
|---|---|---|---|
| 1 | Проверить маршруты и продавцов в {focus_state.customer_state}; сопоставить с {top_state.customer_state} и изучить высокую долю в {high_rate.customer_state} | В одном случае большой объём опозданий, в другом высокая доля на достаточной выборке | Доля опозданий, p90 срока, стоимость доставки; сравнивать сопоставимые маршруты и месяцы |
| 2 | Проверить обещанные сроки и коммуникацию по задержанным заказам | Низкие оценки существенно чаще у опоздавших заказов | Провести отдельный контролируемый пилот коммуникации; заранее выбрать метрику и единицу рандомизации |
| 3 | Ввести ежемесячный мониторинг доставки и полноты дат | Показатели меняются по месяцам; есть пропуски дат | Следить за числителем, знаменателем и исключениями; при изменении исследовать состав заказов |
| 4 | Использовать крупные категории для дальнейшей детализации, не сокращая малые автоматически | Высокая концентрация стоимости товаров | Проверить маржу, возвраты и стоимость привлечения после получения дополнительных данных |

Снижение опозданий может быть полезным направлением, но экономический эффект по этой выгрузке не рассчитан:
нет комиссий, себестоимости, затрат на вмешательство и достоверных данных о возвратах.
Нельзя умножать наблюдаемую разность оценок на все опоздания и называть это доказанным эффектом.

## Ограничения и качество

- Полные операционные месяцы для отчёта выбраны консервативно: январь 2017–июль 2018.
  Все месяцы, включая разреженные края, оставлены в таблице покрытия и исходной витрине.
- Отбор по дате покупки, а не по дате получения; доля опозданий относится к покупательским когортам.
- В периоде {exclusions['delivered_ineligible']} доставленных заказов исключено из расчётов доставки из-за отсутствующих или некорректных дат.
- Отсутствующие отзывы не считаются низкими оценками. Покрытие отзывами среди доставленных заказов: {kpi['review_coverage']:.1%}.
- При нескольких отзывах выбран последний по времени ответа, затем создания, затем review_id; другие способы агрегации могут изменить результат.
- Полные дубликаты геолокации сохранены в raw. Геолокация не присоединяется напрямую: анализ регионов использует customer_state.
- Население регионов неизвестно: объём заказов не интерпретируется как спрос на душу населения.
- Нулевые суммы допустимы как наблюдения; они не удаляются автоматически.
- Независимая сверка SQL с CSV проверяет каждую сумму на уровне заказа, выбор отзыва и итоги категорий/месяцев.

## Воспроизведение

Определения: ../docs/metrics.md. Запросы: ../sql/05_analytics_views.sql и ../sql/06_business_analysis.sql.
Расчёты и чувствительность: statistics.json и таблицы в tables/.
Графики: figures/. Интерактивный отчёт: marketplace_dashboard.xlsx.
"""
    (ROOT/"reports/business_report.md").write_text(report,encoding="utf-8")
    return report

def main():
    for path in [TABLE_DIR,FIG_DIR,DOC_DIR]: path.mkdir(parents=True,exist_ok=True)
    fact=load_fact()
    ms=pd.read_csv(EXPORT_DIR/"monthly_state.csv",parse_dates=["purchase_month"])
    categories=pd.read_csv(EXPORT_DIR/"categories.csv")
    checks=verify_sources(fact,ms,categories)
    cohort=fact.loc[fact.order_purchase_timestamp.ge(START)&fact.order_purchase_timestamp.lt(END)].copy()
    delivered=cohort.loc[cohort.order_status.eq("delivered")].copy()
    eligible=cohort.loc[cohort.delivery_eligible.fillna(False)].copy()
    numeric=[c for c in ms if c not in ["purchase_month","customer_state"]]
    monthly=ms.groupby("purchase_month")[numeric].sum().reset_index()
    # Explicit calendar prevents missing months being mistaken for adjacent months.
    calendar=pd.date_range(START,END-pd.Timedelta(days=1),freq="MS")
    monthly=monthly.set_index("purchase_month").reindex(calendar).rename_axis("purchase_month").reset_index()
    if monthly.all_orders.isna().any(): raise AssertionError("Missing operating month in SQL export")
    states=ms.groupby("customer_state")[numeric].sum().reset_index()
    for data in [monthly,states]:
        data["late_rate"]=data.late_orders/data.delivery_eligible.replace(0,np.nan)
        data["average_order_value"]=data.delivered_gmv/data.delivered_orders.replace(0,np.nan)
        data["mean_delivery_days"]=data.delivery_days_sum/data.delivery_eligible.replace(0,np.nan)
        data["low_review_rate"]=data.low_reviews/data.reviewed_orders.replace(0,np.nan)
    monthly["gmv_mom"]=monthly.delivered_gmv.pct_change(fill_method=None)
    monthly["gmv_cumulative"]=monthly.delivered_gmv.cumsum()
    for i,row in states.iterrows():
        lo,hi=wilson(int(row.late_orders),int(row.delivery_eligible))
        states.loc[i,"late_ci_low"]=lo; states.loc[i,"late_ci_high"]=hi
    states["late_excess_vs_overall"]=(states.late_orders-states.delivery_eligible*eligible.is_late.mean()).clip(lower=0)
    states=states.sort_values("late_orders",ascending=False)
    categories=categories.sort_values(["delivered_gmv","category"],ascending=[False,True]).reset_index(drop=True)
    categories["gmv_share"]=categories.delivered_gmv/categories.delivered_gmv.sum()
    categories["cumulative_gmv_share"]=categories.gmv_share.cumsum()
    exclusions={"delivered_ineligible":int((delivered.delivery_eligible.fillna(False)==False).sum()),
                "delivered_missing_review":int(delivered.review_score.isna().sum())}
    kpi=dict(all_orders=len(cohort),delivered_orders=len(delivered),
             delivered_gmv=float(delivered.item_gmv.sum()),delivered_freight=float(delivered.freight_value.sum()),
             average_order_value=float(delivered.item_gmv.sum()/len(delivered)),
             delivery_eligible=len(eligible),late_orders=int(eligible.is_late.sum()),
             late_rate=float(eligible.is_late.mean()),mean_delivery_days=float(eligible.delivery_days.mean()),
             median_delivery_days=float(eligible.delivery_days.median()),p90_delivery_days=float(eligible.delivery_days.quantile(.9)),
             review_coverage=float(delivered.review_score.notna().mean()),
             low_review_rate=float(delivered.low_review.mean()),
             unique_buyers=int(cohort.customer_unique_id.nunique()))
    coverage=fact.groupby("purchase_month").agg(orders=("order_id","size"),
              first_day=("order_purchase_timestamp","min"),last_day=("order_purchase_timestamp","max")).reset_index()
    coverage["in_reporting_period"]=coverage.purchase_month.ge(START)&coverage.purchase_month.lt(END)
    for filename,data in [("monthly.csv",monthly),("states.csv",states),("categories.csv",categories),
                           ("month_coverage.csv",coverage),
                           ("status_counts.csv",cohort.groupby("order_status").size().rename("orders").reset_index())]:
        data.to_csv(TABLE_DIR/filename,index=False,encoding="utf-8-sig")
    stats=statistical_analysis(cohort)
    make_figures(monthly,states,categories,stats,eligible)
    write_report(kpi,monthly,states,categories,stats,exclusions)
    save_json(ROOT/"reports/kpis.json",kpi)
    manifest={}
    for path in sorted((ROOT/"data").glob("*.csv")):
        manifest[path.name]={"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    save_json(ROOT/"reports/source_manifest.json",manifest)
    save_json(ROOT/"reports/validation.json",{"checks":checks,"exclusions":exclusions,
              "python":platform.python_version(),"pandas":pd.__version__,"numpy":np.__version__,
              "sql_source":"Actual PostgreSQL COPY exports from analytics views",
              "report_start":str(START.date()),"report_end_exclusive":str(END.date())})
    # Workbook source stays small: aggregate counts and sums, not 100k raw orders.
    rows=ms.copy(); rows.purchase_month=rows.purchase_month.dt.strftime("%Y-%m")
    payload={"monthly_state":json.loads(rows.to_json(orient="records")),
             "categories":json.loads(categories.to_json(orient="records")),
             "stats":stats,"kpis":kpi,"months":[d.strftime("%Y-%m") for d in calendar],
             "states":sorted(ms.customer_state.dropna().unique().tolist())}
    save_json(EXPORT_DIR/"workbook_source.json",payload)
    print(json.dumps({"kpis":kpi,"statistics":stats,"validation_checks":len(checks)},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

