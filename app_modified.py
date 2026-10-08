import os
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="E-Commerce Executive Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# ============================================================
# DATABASE
# ============================================================

@st.cache_resource
def create_db_engine():
    required = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
    ]

    missing = [
        item
        for item in required
        if not os.getenv(item)
    ]

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )

    user = quote_plus(
        os.getenv("POSTGRES_USER", "")
    )

    password = quote_plus(
        os.getenv("POSTGRES_PASSWORD", "")
    )

    host = os.getenv(
        "POSTGRES_HOST",
        "localhost",
    )

    port = os.getenv(
        "POSTGRES_PORT",
        "5432",
    )

    database = os.getenv(
        "POSTGRES_DB",
        "ecommerce_bi",
    )

    database_url = (
        "postgresql+psycopg2://"
        f"{user}:{password}"
        f"@{host}:{port}/{database}"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


try:
    engine = create_db_engine()

except Exception as exc:
    st.error("Database configuration error.")
    st.exception(exc)
    st.stop()


# ============================================================
# DARK EXECUTIVE THEME
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL APPLICATION
       ======================================================== */

    .stApp {
        background-color: #070b14;
        color: #e5e7eb;
    }

    .main {
        background-color: #070b14;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    footer {
        visibility: hidden;
    }

    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background-color: #050912;
        border-right: 1px solid #1e293b;
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
        font-weight: 700 !important;
    }

    /* ========================================================
       GENERAL TEXT
       ======================================================== */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: #f8fafc !important;
    }

    p,
    li {
        color: #cbd5e1;
    }

    /* ========================================================
       METRICS
       ======================================================== */

    div[data-testid="stMetric"] {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 1rem;
        min-height: 115px;
        box-shadow:
            0 8px 24px rgba(0, 0, 0, 0.22);
    }

    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.68rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 1.75rem !important;
        font-weight: 850 !important;
        letter-spacing: -0.035em;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
    }

    /* ========================================================
       CONTAINERS
       ======================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0f172a;
        border-color: #1e293b;
        border-radius: 14px;
    }

    /* ========================================================
       INPUTS
       ======================================================== */

    input,
    textarea {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border-color: #334155 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border-color: #334155 !important;
        color: #f8fafc !important;
    }

    /* ========================================================
       BUTTONS
       ======================================================== */

    button[kind="primary"] {
        background-color: #4f46e5 !important;
        border-color: #4f46e5 !important;
        color: #ffffff !important;
    }

    button[kind="secondary"] {
        background-color: #111827 !important;
        border-color: #334155 !important;
        color: #e5e7eb !important;
    }

    .stButton > button {
        border-radius: 9px;
        font-weight: 750;
    }

    /* ========================================================
       ALERTS
       ======================================================== */

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* ========================================================
       TABLES
       ======================================================== */

    div[data-testid="stDataFrame"] {
        border: 1px solid #1e293b;
        border-radius: 12px;
        overflow: hidden;
    }

    /* ========================================================
       DIVIDERS
       ======================================================== */

    hr {
        border-color: #1e293b !important;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    /* ========================================================
       SMALL LABELS
       ======================================================== */

    .eyebrow {
        color: #818cf8;
        font-size: 0.65rem;
        font-weight: 900;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }

    .muted {
        color: #64748b;
        font-size: 0.75rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_sql(query, params=None):
    """
    Execute a read-only SQL query and return a DataFrame.
    """

    return pd.read_sql(
        text(query),
        engine,
        params=params or {},
    )


def safe_float(value):
    """
    Convert a value safely to float.
    """

    try:
        if pd.isna(value):
            return 0.0

        return float(value)

    except Exception:
        return 0.0


def percentage_change(current, previous):
    """
    Calculate percentage change.
    """

    current = safe_float(current)
    previous = safe_float(previous)

    if previous == 0:
        return 0.0

    return (
        (current - previous)
        / abs(previous)
        * 100
    )


def format_rupees(value):
    """
    Format INR as a whole-number amount.
    """

    value = safe_float(value)

    return f"₹{value:,.0f}"


def format_lakh(value):
    """
    Format INR in lakh units.
    """

    value = safe_float(value)

    return f"₹{value / 100000:.2f}L"


def format_crore(value):
    """
    Format INR in crore units.
    """

    value = safe_float(value)

    return f"₹{value / 10000000:.2f}Cr"


def format_business_amount(value):
    """
    Use crore for large values and lakh otherwise.
    """

    value = safe_float(value)

    if abs(value) >= 10000000:
        return format_crore(value)

    return format_lakh(value)


def format_number(value):
    """
    Format integer-like values.
    """

    try:
        return f"{int(round(float(value))):,}"

    except Exception:
        return "0"


def format_metric_value(metric, value):
    """
    Format AI business-analysis results based on metric type.
    """

    value = safe_float(value)

    if metric in {
        "revenue",
        "profit",
        "discounts",
        "spend",
        "cost",
    }:
        return format_business_amount(value)

    if metric in {
        "orders",
        "customers",
        "units_sold",
    }:
        return format_number(value)

    if metric in {
        "margin",
        "margin_percent",
        "conversion_rate",
        "return_rate",
        "ctr",
    }:
        return f"{value:.2f}%"

    if metric == "roas":
        return f"{value:.2f}x"

    if metric == "cac":
        return format_rupees(value)

    return f"{value:,.2f}"


def section(title, description=None):
    """
    Native Streamlit section heading.

    No custom HTML is used here.
    """

    st.markdown("---")

    st.markdown(
        f"## {title}"
    )

    if description:
        st.caption(description)


def signal_message(
    title,
    body,
    level="warning",
):
    """
    Native executive signal.
    """

    if level == "success":
        st.success(
            f"**{title}**\n\n{body}"
        )

    elif level == "error":
        st.error(
            f"**{title}**\n\n{body}"
        )

    elif level == "info":
        st.info(
            f"**{title}**\n\n{body}"
        )

    else:
        st.warning(
            f"**{title}**\n\n{body}"
        )


def build_driver_signals(row):
    """
    Identify the strongest observed signals
    for a category.
    """

    signals = []

    return_change = safe_float(
        row.get(
            "return_rate_change",
            0,
        )
    )

    margin_change_value = safe_float(
        row.get(
            "margin_change",
            0,
        )
    )

    discount_change = safe_float(
        row.get(
            "discount_rate_change",
            0,
        )
    )

    revenue_change_value = safe_float(
        row.get(
            "revenue_change_percent",
            0,
        )
    )

    if return_change >= 2:
        signals.append(
            f"Returns ↑ {return_change:.2f} pp"
        )

    if margin_change_value <= -0.5:
        signals.append(
            f"Margin ↓ {abs(margin_change_value):.2f} pp"
        )

    if discount_change >= 0.3:
        signals.append(
            f"Discount ↑ {discount_change:.2f} pp"
        )

    if revenue_change_value < -3:
        signals.append(
            f"Revenue ↓ {abs(revenue_change_value):.2f}%"
        )

    return signals[:3]


def make_action_from_category(row):
    """
    Build a concise management action from
    observed category evidence.

    This is a display fallback only.
    Backend agent recommendations are used
    when the AI endpoint is queried.
    """

    category = str(
        row.get("category", "Category")
    )

    profit_change_value = safe_float(
        row.get("profit_change", 0)
    )

    profit_change_percent = safe_float(
        row.get(
            "profit_change_percent",
            0,
        )
    )

    return_change = safe_float(
        row.get(
            "return_rate_change",
            0,
        )
    )

    margin_change_value = safe_float(
        row.get(
            "margin_change",
            0,
        )
    )

    discount_change = safe_float(
        row.get(
            "discount_rate_change",
            0,
        )
    )

    if return_change >= 2:

        title = (
            f"Investigate {category} returns"
        )

        problem = (
            f"Profit declined "
            f"{abs(profit_change_percent):.2f}% "
            f"and return rate increased "
            f"{return_change:.2f} percentage points."
        )

        action = (
            f"Review the highest-returning "
            f"{category} products and return reasons. "
            f"Check product quality, listing accuracy "
            f"and fulfillment issues."
        )

        objective = (
            f"Protect approximately "
            f"{format_rupees(abs(profit_change_value))} "
            f"of category profit."
        )

    elif discount_change >= 0.3:

        title = (
            f"Protect {category} margin"
        )

        problem = (
            f"Profit declined "
            f"{abs(profit_change_percent):.2f}% "
            f"while discount rate increased "
            f"{discount_change:.2f} percentage points."
        )

        action = (
            f"Review discount depth and promotional "
            f"products in {category}. Reduce discounts "
            f"where incremental volume does not "
            f"compensate for lost margin."
        )

        objective = (
            "Restore contribution margin."
        )

    elif margin_change_value < 0:

        title = (
            f"Restore {category} profitability"
        )

        problem = (
            f"Profit declined "
            f"{abs(profit_change_percent):.2f}% "
            f"and margin decreased "
            f"{abs(margin_change_value):.2f} percentage points."
        )

        action = (
            f"Review product pricing, supplier cost "
            f"and discount pressure within {category}."
        )

        objective = (
            "Restore category margin and profit."
        )

    else:

        title = (
            f"Investigate {category} profitability"
        )

        problem = (
            f"Profit declined "
            f"{abs(profit_change_percent):.2f}%."
        )

        action = (
            f"Drill into product, pricing, cost and "
            f"volume drivers within {category}."
        )

        objective = (
            f"Recover approximately "
            f"{format_rupees(abs(profit_change_value))} "
            f"in category profit pressure."
        )

    return {
        "title": title,
        "problem": problem,
        "action": action,
        "objective": objective,
    }


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### E-COMMERCE BI"
    )

    st.markdown(
        "**Executive Command Center**"
    )

    st.caption(
        "Founder / CEO Decision Support"
    )

    st.markdown("---")

    st.markdown(
        "#### Analysis Period"
    )

    start_date = st.date_input(
        "Start Date",
        value=date(2026, 9, 1),
        key="analysis_start_date",
    )

    end_date = st.date_input(
        "End Date",
        value=date(2026, 9, 30),
        key="analysis_end_date",
    )

    st.caption(
        "All executive metrics use the selected "
        "period and its comparable previous period."
    )

    st.markdown("---")

    st.markdown(
        "#### Decision Flow"
    )

    st.info(
        "SEE\n\n↓\n\nUNDERSTAND\n\n↓\n\nACT"
    )

    st.caption(
        "Numbers → Visualization → Insight → Action"
    )


# ============================================================
# DATE VALIDATION
# ============================================================

if end_date < start_date:

    st.error(
        "End Date must be greater than or equal to Start Date."
    )

    st.stop()


# ============================================================
# COMPARABLE PERIOD
# ============================================================

period_days = (
    end_date - start_date
).days + 1

previous_end = (
    start_date - timedelta(days=1)
)

previous_start = (
    previous_end
    - timedelta(days=period_days - 1)
)

period_label = (
    f"{start_date.strftime('%d %b %Y')}"
    f" – "
    f"{end_date.strftime('%d %b %Y')}"
)

previous_period_label = (
    f"{previous_start.strftime('%d %b %Y')}"
    f" – "
    f"{previous_end.strftime('%d %b %Y')}"
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="eyebrow">EXECUTIVE DECISION SUPPORT</div>',
    unsafe_allow_html=True,
)

st.title(
    "E-Commerce Executive Intelligence"
)

st.caption(
    f"{period_label}  ·  "
    "India Online Retail  ·  "
    "Founder / CEO View"
)


# ============================================================
# 1. BUSINESS HEALTH
# ============================================================

section(
    "Business Health",
    "The numbers management should see first.",
)


current_query = """
SELECT
    COALESCE(SUM(oi.revenue), 0) AS revenue,
    COALESCE(SUM(oi.profit), 0) AS profit,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(DISTINCT o.customer_id) AS customers

FROM orders o

JOIN order_items oi
    ON o.order_id = oi.order_id

WHERE o.order_status = 'Delivered'

  AND o.order_date >= :start_date

  AND o.order_date < (
      :end_date + INTERVAL '1 day'
  )
"""


previous_query = """
SELECT
    COALESCE(SUM(oi.revenue), 0) AS revenue,
    COALESCE(SUM(oi.profit), 0) AS profit,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(DISTINCT o.customer_id) AS customers

FROM orders o

JOIN order_items oi
    ON o.order_id = oi.order_id

WHERE o.order_status = 'Delivered'

  AND o.order_date >= :start_date

  AND o.order_date < (
      :end_date + INTERVAL '1 day'
  )
"""


try:

    current = read_sql(
        current_query,
        {
            "start_date": start_date,
            "end_date": end_date,
        },
    ).iloc[0]

    previous = read_sql(
        previous_query,
        {
            "start_date": previous_start,
            "end_date": previous_end,
        },
    ).iloc[0]

except Exception as exc:

    st.error(
        "Unable to load business health data."
    )

    st.exception(exc)

    st.stop()


revenue = safe_float(
    current["revenue"]
)

profit = safe_float(
    current["profit"]
)

orders = int(
    safe_float(
        current["orders"]
    )
)

customers = int(
    safe_float(
        current["customers"]
    )
)

previous_revenue = safe_float(
    previous["revenue"]
)

previous_profit = safe_float(
    previous["profit"]
)

previous_orders = int(
    safe_float(
        previous["orders"]
    )
)

previous_customers = int(
    safe_float(
        previous["customers"]
    )
)


revenue_change = percentage_change(
    revenue,
    previous_revenue,
)

profit_change = percentage_change(
    profit,
    previous_profit,
)

orders_change = percentage_change(
    orders,
    previous_orders,
)

customer_change = percentage_change(
    customers,
    previous_customers,
)


profit_margin = (
    profit / revenue * 100
    if revenue != 0
    else 0
)

previous_profit_margin = (
    previous_profit
    / previous_revenue
    * 100
    if previous_revenue != 0
    else 0
)

margin_change = (
    profit_margin
    - previous_profit_margin
)


health_cols = st.columns(
    4,
    gap="medium",
)

with health_cols[0]:

    st.metric(
        "Revenue",
        format_business_amount(
            revenue
        ),
        f"{revenue_change:+.2f}%",
    )

with health_cols[1]:

    st.metric(
        "Profit",
        format_business_amount(
            profit
        ),
        f"{profit_change:+.2f}%",
    )

with health_cols[2]:

    st.metric(
        "Profit Margin",
        f"{profit_margin:.2f}%",
        f"{margin_change:+.2f} pp",
    )

with health_cols[3]:

    st.metric(
        "Orders",
        format_number(orders),
        f"{orders_change:+.2f}%",
    )


# ============================================================
# 2. CATEGORY ANALYSIS
# ============================================================

category_query = """
WITH current_period AS (

    SELECT
        p.category,

        SUM(oi.revenue) AS revenue,

        SUM(oi.profit) AS profit,

        SUM(
            oi.unit_price
            * oi.quantity
            * oi.discount_percent
            / 100
        ) AS discounts

    FROM order_items oi

    JOIN orders o
        ON oi.order_id = o.order_id

    JOIN products p
        ON oi.product_id = p.product_id

    WHERE o.order_status = 'Delivered'

      AND o.order_date >= :current_start

      AND o.order_date <= :current_end

    GROUP BY p.category
),

previous_period AS (

    SELECT
        p.category,

        SUM(oi.revenue) AS revenue,

        SUM(oi.profit) AS profit,

        SUM(
            oi.unit_price
            * oi.quantity
            * oi.discount_percent
            / 100
        ) AS discounts

    FROM order_items oi

    JOIN orders o
        ON oi.order_id = o.order_id

    JOIN products p
        ON oi.product_id = p.product_id

    WHERE o.order_status = 'Delivered'

      AND o.order_date >= :previous_start

      AND o.order_date <= :previous_end

    GROUP BY p.category
),

current_returns AS (

    SELECT
        p.category,

        SUM(r.refund_amount) AS returns

    FROM returns r

    JOIN products p
        ON r.product_id = p.product_id

    WHERE r.return_date >= :current_start

      AND r.return_date <= :current_end

    GROUP BY p.category
),

previous_returns AS (

    SELECT
        p.category,

        SUM(r.refund_amount) AS returns

    FROM returns r

    JOIN products p
        ON r.product_id = p.product_id

    WHERE r.return_date >= :previous_start

      AND r.return_date <= :previous_end

    GROUP BY p.category
)

SELECT

    COALESCE(
        c.category,
        p.category
    ) AS category,

    COALESCE(
        c.revenue,
        0
    ) AS current_revenue,

    COALESCE(
        p.revenue,
        0
    ) AS previous_revenue,

    COALESCE(
        c.profit,
        0
    ) AS current_profit,

    COALESCE(
        p.profit,
        0
    ) AS previous_profit,

    COALESCE(
        c.discounts,
        0
    ) AS current_discounts,

    COALESCE(
        p.discounts,
        0
    ) AS previous_discounts,

    COALESCE(
        cr.returns,
        0
    ) AS current_returns,

    COALESCE(
        pr.returns,
        0
    ) AS previous_returns

FROM current_period c

FULL OUTER JOIN previous_period p
    ON c.category = p.category

LEFT JOIN current_returns cr
    ON COALESCE(
        c.category,
        p.category
    ) = cr.category

LEFT JOIN previous_returns pr
    ON COALESCE(
        c.category,
        p.category
    ) = pr.category

ORDER BY
    COALESCE(
        c.category,
        p.category
    )
"""


try:

    categories = read_sql(
        category_query,
        {
            "current_start": start_date,
            "current_end": end_date,
            "previous_start": previous_start,
            "previous_end": previous_end,
        },
    )

except Exception as exc:

    st.error(
        "Unable to load category analysis."
    )

    st.exception(exc)

    st.stop()


if categories.empty:

    st.warning(
        "No category data is available for the selected period."
    )

    categories = pd.DataFrame()

else:

    numeric_columns = [
        "current_revenue",
        "previous_revenue",
        "current_profit",
        "previous_profit",
        "current_discounts",
        "previous_discounts",
        "current_returns",
        "previous_returns",
    ]

    for column in numeric_columns:

        categories[column] = pd.to_numeric(
            categories[column],
            errors="coerce",
        ).fillna(0)

    categories["profit_change"] = (
        categories["current_profit"]
        - categories["previous_profit"]
    )

    categories["profit_change_percent"] = (
        (
            categories["current_profit"]
            - categories["previous_profit"]
        )
        /
        categories["previous_profit"]
        .abs()
        .replace(0, pd.NA)
        * 100
    ).fillna(0)

    categories["revenue_change_percent"] = (
        (
            categories["current_revenue"]
            - categories["previous_revenue"]
        )
        /
        categories["previous_revenue"]
        .abs()
        .replace(0, pd.NA)
        * 100
    ).fillna(0)

    current_margin = (
        categories["current_profit"]
        /
        categories["current_revenue"]
        .replace(0, pd.NA)
        * 100
    )

    previous_margin = (
        categories["previous_profit"]
        /
        categories["previous_revenue"]
        .replace(0, pd.NA)
        * 100
    )

    categories["margin_change"] = (
        current_margin
        - previous_margin
    ).fillna(0)

    current_return_rate = (
        categories["current_returns"]
        /
        categories["current_revenue"]
        .replace(0, pd.NA)
        * 100
    )

    previous_return_rate = (
        categories["previous_returns"]
        /
        categories["previous_revenue"]
        .replace(0, pd.NA)
        * 100
    )

    categories["return_rate_change"] = (
        current_return_rate
        - previous_return_rate
    ).fillna(0)

    current_discount_rate = (
        categories["current_discounts"]
        /
        categories["current_revenue"]
        .replace(0, pd.NA)
        * 100
    )

    previous_discount_rate = (
        categories["previous_discounts"]
        /
        categories["previous_revenue"]
        .replace(0, pd.NA)
        * 100
    )

    categories["discount_rate_change"] = (
        current_discount_rate
        - previous_discount_rate
    ).fillna(0)


declining = (
    categories[
        categories["profit_change"] < 0
    ]
    .sort_values(
        "profit_change"
    )
    if not categories.empty
    else pd.DataFrame()
)


growing = (
    categories[
        categories["profit_change"] > 0
    ]
    .sort_values(
        "profit_change",
        ascending=False,
    )
    if not categories.empty
    else pd.DataFrame()
)


# ============================================================
# 3. EXECUTIVE BRIEF
# ============================================================

section(
    "Executive Brief",
    "One-sentence management interpretation of the current business position.",
)


if (
    profit_change < 0
    and not declining.empty
):

    largest_pressure = declining.iloc[0]

    brief = (
        f"Profit is {format_business_amount(profit)} "
        f"and declined {abs(profit_change):.2f}% "
        f"versus the previous comparable period. "
        f"{largest_pressure['category']} is the largest "
        f"identified category-level pressure, with "
        f"approximately "
        f"{format_rupees(abs(largest_pressure['profit_change']))} "
        f"in profit decline."
    )

    if not growing.empty:

        strongest_growth = growing.iloc[0]

        brief += (
            f" {strongest_growth['category']} partially "
            f"offset the decline with "
            f"{strongest_growth['profit_change_percent']:+.2f}% "
            f"profit growth."
        )

    signal_message(
        "Profit requires attention",
        brief,
        level="error",
    )

elif profit_change > 0:

    strongest_growth = (
        growing.iloc[0]
        if not growing.empty
        else None
    )

    brief = (
        f"Profit increased "
        f"{profit_change:.2f}% to "
        f"{format_business_amount(profit)}."
    )

    if strongest_growth is not None:

        brief += (
            f" {strongest_growth['category']} "
            f"is the strongest positive category."
        )

    signal_message(
        "Profit is improving",
        brief,
        level="success",
    )

else:

    signal_message(
        "Profit is stable",
        f"Current profit is "
        f"{format_business_amount(profit)}.",
        level="info",
    )


# ============================================================
# 4. TARGET POSITION
# ============================================================

section(
    "Target Position",
    "Actual performance against the applicable monthly business targets.",
)


try:

    targets = read_sql(
        """
        SELECT
            month,
            revenue_target,
            profit_target,
            orders_target,
            customer_target

        FROM targets

        ORDER BY month
        """
    )

except Exception:

    targets = pd.DataFrame()


target_row = None


if not targets.empty:

    targets["month_parsed"] = pd.to_datetime(
        targets["month"],
        errors="coerce",
    )

    matching_target = targets[
        (
            targets["month_parsed"].dt.year
            == start_date.year
        )
        &
        (
            targets["month_parsed"].dt.month
            == start_date.month
        )
    ]

    if not matching_target.empty:

        target_row = matching_target.iloc[0]


if target_row is None:

    st.info(
        "No target record is available for the selected month."
    )

else:

    target_items = [
        (
            "Revenue",
            revenue,
            safe_float(
                target_row["revenue_target"]
            ),
            True,
        ),
        (
            "Profit",
            profit,
            safe_float(
                target_row["profit_target"]
            ),
            True,
        ),
        (
            "Orders",
            orders,
            safe_float(
                target_row["orders_target"]
            ),
            False,
        ),
        (
            "Customers",
            customers,
            safe_float(
                target_row["customer_target"]
            ),
            False,
        ),
    ]

    target_cols = st.columns(
        4,
        gap="medium",
    )

    for column, (
        metric_name,
        actual,
        target,
        currency,
    ) in zip(
        target_cols,
        target_items,
    ):

        achievement = (
            actual / target * 100
            if target != 0
            else 0
        )

        gap = actual - target

        if currency:

            actual_text = format_business_amount(
                actual
            )

            target_text = format_business_amount(
                target
            )

            gap_text = format_business_amount(
                gap
            )

        else:

            actual_text = format_number(
                actual
            )

            target_text = format_number(
                target
            )

            gap_text = format_number(
                gap
            )

        with column:

            st.metric(
                metric_name,
                actual_text,
                f"{achievement:.1f}% of target",
            )

            st.caption(
                f"Target: {target_text}  ·  "
                f"Gap: {gap_text}"
            )


# ============================================================
# 5. PROFIT POSITION
# ============================================================

section(
    "Profit Position",
    f"Previous comparable period "
    f"({previous_period_label}) versus the selected period.",
)


profit_cols = st.columns(
    3,
    gap="medium",
)

with profit_cols[0]:

    st.metric(
        "Previous Profit",
        format_business_amount(
            previous_profit
        ),
    )

with profit_cols[1]:

    st.metric(
        "Current Profit",
        format_business_amount(
            profit
        ),
    )

with profit_cols[2]:

    st.metric(
        "Profit Movement",
        format_business_amount(
            profit - previous_profit
        ),
        f"{profit_change:+.2f}%",
    )


# ============================================================
# 6. PROFIT IMPACT BY CATEGORY
# ============================================================

section(
    "Profit Impact by Category",
    "Contribution of each category to the overall profit movement.",
)


if not categories.empty:

    impact = categories[
        [
            "category",
            "profit_change",
        ]
    ].copy()

    impact = impact.sort_values(
        "profit_change"
    )

    chart = go.Figure()

    chart.add_trace(
        go.Bar(
            x=impact["profit_change"],
            y=impact["category"],
            orientation="h",
            text=[
                format_rupees(value)
                for value in impact["profit_change"]
            ],
            textposition="outside",
            cliponaxis=False,
            marker=dict(
                color=[
                    "#ef4444"
                    if value < 0
                    else "#22c55e"
                    for value
                    in impact["profit_change"]
                ]
            ),
            hovertemplate=(
                "%{y}"
                "<br>Profit change: ₹%{x:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    chart.add_vline(
        x=0,
        line_width=1,
        line_color="#64748b",
    )

    chart.update_layout(
        height=370,
        margin=dict(
            l=10,
            r=80,
            t=15,
            b=15,
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f172a",
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        font=dict(
            color="#cbd5e1",
        ),
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


# ============================================================
# 7. WHY DID PROFIT CHANGE?
# ============================================================

section(
    "Why Did Profit Change?",
    "The three largest identified category-level drivers.",
)


top_declining = (
    declining.head(3)
    if not declining.empty
    else pd.DataFrame()
)


if top_declining.empty:

    st.info(
        "No category-level profit decline was identified."
    )

else:

    driver_columns = st.columns(
        len(top_declining),
        gap="medium",
    )

    for column, (_, row) in zip(
        driver_columns,
        top_declining.iterrows(),
    ):

        with column:

            with st.container(border=True):

                st.markdown(
                    f"### {row['category']}"
                )

                st.metric(
                    "Profit Impact",
                    format_business_amount(
                        abs(
                            row["profit_change"]
                        )
                    ),
                    f"{row['profit_change_percent']:+.2f}%",
                )

                signals = build_driver_signals(
                    row
                )

                if signals:

                    for signal in signals:

                        st.caption(
                            f"• {signal}"
                        )

                else:

                    st.caption(
                        "Further product-level investigation "
                        "is required."
                    )


# ============================================================
# 8. PRODUCT-LEVEL INTELLIGENCE
# ============================================================

section(
    "Product-Level Intelligence",
    "Products contributing most to current-period profit deterioration.",
)


product_query = """
WITH current_products AS (

    SELECT
        p.product_id,
        p.product_name,
        p.category,

        SUM(oi.revenue) AS current_revenue,

        SUM(oi.profit) AS current_profit,

        SUM(oi.quantity) AS current_units

    FROM order_items oi

    JOIN orders o
        ON oi.order_id = o.order_id

    JOIN products p
        ON oi.product_id = p.product_id

    WHERE o.order_status = 'Delivered'

      AND o.order_date >= :current_start

      AND o.order_date <= :current_end

    GROUP BY
        p.product_id,
        p.product_name,
        p.category
),

previous_products AS (

    SELECT
        p.product_id,

        SUM(oi.revenue) AS previous_revenue,

        SUM(oi.profit) AS previous_profit

    FROM order_items oi

    JOIN orders o
        ON oi.order_id = o.order_id

    JOIN products p
        ON oi.product_id = p.product_id

    WHERE o.order_status = 'Delivered'

      AND o.order_date >= :previous_start

      AND o.order_date <= :previous_end

    GROUP BY p.product_id
)

SELECT

    cp.product_id,

    cp.product_name,

    cp.category,

    cp.current_revenue,

    cp.current_profit,

    cp.current_units,

    COALESCE(
        pp.previous_revenue,
        0
    ) AS previous_revenue,

    COALESCE(
        pp.previous_profit,
        0
    ) AS previous_profit,

    cp.current_profit
    -
    COALESCE(
        pp.previous_profit,
        0
    ) AS profit_change

FROM current_products cp

LEFT JOIN previous_products pp
    ON cp.product_id = pp.product_id

WHERE (
    cp.current_profit
    -
    COALESCE(
        pp.previous_profit,
        0
    )
) < 0

ORDER BY profit_change

LIMIT 10
"""


try:

    products_df = read_sql(
        product_query,
        {
            "current_start": start_date,
            "current_end": end_date,
            "previous_start": previous_start,
            "previous_end": previous_end,
        },
    )

except Exception:

    products_df = pd.DataFrame()


if products_df.empty:

    st.info(
        "No current-period products show negative profit movement "
        "against the previous comparable period."
    )

else:

    display_products = products_df.copy()

    display_products["Current Revenue"] = (
        display_products["current_revenue"]
        .apply(format_rupees)
    )

    display_products["Current Profit"] = (
        display_products["current_profit"]
        .apply(format_rupees)
    )

    display_products["Profit Change"] = (
        display_products["profit_change"]
        .apply(format_rupees)
    )

    display_products["Units Sold"] = (
        display_products["current_units"]
        .apply(format_number)
    )

    display_products = display_products[
        [
            "product_name",
            "category",
            "Current Revenue",
            "Current Profit",
            "Profit Change",
            "Units Sold",
        ]
    ]

    display_products.columns = [
        "Product",
        "Category",
        "Current Revenue",
        "Current Profit",
        "Profit Change",
        "Units Sold",
    ]

    st.dataframe(
        display_products,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 9. REGIONAL INTELLIGENCE
# ============================================================

section(
    "Regional Intelligence",
    "States contributing most to profit movement.",
)


regional_query = """
WITH current_region AS (

    SELECT
        o.shipping_state AS state,

        SUM(oi.revenue) AS current_revenue,

        SUM(oi.profit) AS current_profit

    FROM orders o

    JOIN order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'Delivered'

      AND o.order_date >= :current_start

      AND o.order_date <= :current_end

    GROUP BY o.shipping_state
),

previous_region AS (

    SELECT
        o.shipping_state AS state,

        SUM(oi.revenue) AS previous_revenue,

        SUM(oi.profit) AS previous_profit

    FROM orders o

    JOIN order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'Delivered'

      AND o.order_date >= :previous_start

      AND o.order_date <= :previous_end

    GROUP BY o.shipping_state
)

SELECT

    COALESCE(
        c.state,
        p.state
    ) AS state,

    COALESCE(
        c.current_revenue,
        0
    ) AS current_revenue,

    COALESCE(
        p.previous_revenue,
        0
    ) AS previous_revenue,

    COALESCE(
        c.current_profit,
        0
    ) AS current_profit,

    COALESCE(
        p.previous_profit,
        0
    ) AS previous_profit,

    COALESCE(
        c.current_profit,
        0
    )
    -
    COALESCE(
        p.previous_profit,
        0
    ) AS profit_change

FROM current_region c

FULL OUTER JOIN previous_region p
    ON c.state = p.state

ORDER BY profit_change

LIMIT 10
"""


try:

    regional_df = read_sql(
        regional_query,
        {
            "current_start": start_date,
            "current_end": end_date,
            "previous_start": previous_start,
            "previous_end": previous_end,
        },
    )

except Exception:

    regional_df = pd.DataFrame()


if regional_df.empty:

    st.info(
        "Regional profit movement is unavailable."
    )

else:

    regional_display = regional_df.copy()

    regional_display["Current Revenue"] = (
        regional_display["current_revenue"]
        .apply(format_rupees)
    )

    regional_display["Current Profit"] = (
        regional_display["current_profit"]
        .apply(format_rupees)
    )

    regional_display["Profit Change"] = (
        regional_display["profit_change"]
        .apply(format_rupees)
    )

    regional_display = regional_display[
        [
            "state",
            "Current Revenue",
            "Current Profit",
            "Profit Change",
        ]
    ]

    regional_display.columns = [
        "State",
        "Current Revenue",
        "Current Profit",
        "Profit Change",
    ]

    st.dataframe(
        regional_display,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 10. MANAGEMENT ACTION PLAN
# ============================================================

section(
    "Management Action Plan",
    "Prioritized actions based on the strongest observed business signals.",
)


if top_declining.empty:

    st.success(
        "No major category-level profit pressure was identified."
    )

else:

    action_columns = st.columns(
        len(top_declining),
        gap="medium",
    )

    for index, (
        column,
        (_, row),
    ) in enumerate(
        zip(
            action_columns,
            top_declining.iterrows(),
        ),
        start=1,
    ):

        action = make_action_from_category(
            row
        )

        with column:

            with st.container(border=True):

                st.caption(
                    f"ACTION {index:02d}"
                )

                st.markdown(
                    f"### {action['title']}"
                )

                st.error(
                    "HIGH PRIORITY"
                )

                st.markdown(
                    "**Problem**"
                )

                st.write(
                    action["problem"]
                )

                st.markdown(
                    "**Recommended Action**"
                )

                st.write(
                    action["action"]
                )

                st.markdown(
                    "**Objective**"
                )

                st.info(
                    action["objective"]
                )


# ============================================================
# 11. GROWTH OPPORTUNITY
# ============================================================

section(
    "Growth Opportunity",
    "The strongest category-level positive movement.",
)


if growing.empty:

    st.info(
        "No category currently shows positive profit movement."
    )

else:

    opportunity = growing.iloc[0]

    with st.container(border=True):

        st.success(
            "PROFITABLE GROWTH"
        )

        st.markdown(
            f"### {opportunity['category']}"
        )

        growth_cols = st.columns(
            3,
            gap="medium",
        )

        with growth_cols[0]:

            st.metric(
                "Revenue Movement",
                f"{opportunity['revenue_change_percent']:+.2f}%",
            )

        with growth_cols[1]:

            st.metric(
                "Profit Movement",
                f"{opportunity['profit_change_percent']:+.2f}%",
            )

        with growth_cols[2]:

            st.metric(
                "Margin Movement",
                f"{opportunity['margin_change']:+.2f} pp",
            )

        st.info(
            "Management consideration: evaluate controlled "
            "growth while monitoring margin and return performance."
        )


# ============================================================
# 12. MARKETING ANALYSIS
# ============================================================

section(
    "Marketing Efficiency",
    "Marketing-channel performance for the selected period.",
)


marketing_query = """
SELECT

    channel,

    SUM(spend) AS spend,

    SUM(revenue_generated) AS revenue_generated,

    SUM(conversions) AS conversions,

    SUM(new_customers) AS new_customers,

    SUM(impressions) AS impressions,

    SUM(clicks) AS clicks

FROM marketing_campaigns

WHERE campaign_date >= :start_date

  AND campaign_date <= :end_date

GROUP BY channel

ORDER BY revenue_generated DESC
"""


try:

    marketing_df = read_sql(
        marketing_query,
        {
            "start_date": start_date,
            "end_date": end_date,
        },
    )

except Exception:

    marketing_df = pd.DataFrame()


if marketing_df.empty:

    st.info(
        "No marketing data is available for the selected period."
    )

else:

    numeric_marketing_columns = [
        "spend",
        "revenue_generated",
        "conversions",
        "new_customers",
        "impressions",
        "clicks",
    ]

    for column in numeric_marketing_columns:

        marketing_df[column] = pd.to_numeric(
            marketing_df[column],
            errors="coerce",
        ).fillna(0)

    marketing_df["roas"] = (
        marketing_df["revenue_generated"]
        /
        marketing_df["spend"]
        .replace(0, pd.NA)
    ).fillna(0)

    marketing_df["conversion_rate"] = (
        marketing_df["conversions"]
        /
        marketing_df["clicks"]
        .replace(0, pd.NA)
        * 100
    ).fillna(0)

    marketing_df["cac"] = (
        marketing_df["spend"]
        /
        marketing_df["new_customers"]
        .replace(0, pd.NA)
    ).fillna(0)

    marketing_df["ctr"] = (
        marketing_df["clicks"]
        /
        marketing_df["impressions"]
        .replace(0, pd.NA)
        * 100
    ).fillna(0)

    total_spend = safe_float(
        marketing_df["spend"].sum()
    )

    total_marketing_revenue = safe_float(
        marketing_df["revenue_generated"].sum()
    )

    overall_roas = (
        total_marketing_revenue
        / total_spend
        if total_spend
        else 0
    )

    best_roas = (
        marketing_df
        .sort_values(
            "roas",
            ascending=False,
        )
        .iloc[0]
    )

    lowest_roas = (
        marketing_df
        .sort_values(
            "roas",
            ascending=True,
        )
        .iloc[0]
    )

    marketing_cols = st.columns(
        4,
        gap="medium",
    )

    with marketing_cols[0]:

        st.metric(
            "Overall ROAS",
            f"{overall_roas:.2f}x",
        )

    with marketing_cols[1]:

        st.metric(
            "Best ROAS",
            f"{safe_float(best_roas['roas']):.2f}x",
            str(best_roas["channel"]),
        )

    with marketing_cols[2]:

        st.metric(
            "Lowest ROAS",
            f"{safe_float(lowest_roas['roas']):.2f}x",
            str(lowest_roas["channel"]),
        )

    with marketing_cols[3]:

        st.metric(
            "Marketing Spend",
            format_business_amount(
                total_spend
            ),
        )

    marketing_chart_df = marketing_df.sort_values(
        "roas"
    )

    marketing_chart = go.Figure()

    marketing_chart.add_trace(
        go.Bar(
            x=marketing_chart_df["roas"],
            y=marketing_chart_df["channel"],
            orientation="h",
            text=[
                f"{value:.2f}x"
                for value
                in marketing_chart_df["roas"]
            ],
            textposition="outside",
            cliponaxis=False,
            marker_color="#6366f1",
            hovertemplate=(
                "%{y}"
                "<br>ROAS: %{x:.2f}x"
                "<extra></extra>"
            ),
        )
    )

    marketing_chart.update_layout(
        height=360,
        margin=dict(
            l=10,
            r=60,
            t=15,
            b=15,
        ),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f172a",
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        font=dict(
            color="#cbd5e1",
        ),
    )

    st.plotly_chart(
        marketing_chart,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


# ============================================================
# 13. RISK RADAR
# ============================================================

section(
    "Risk Radar",
    "Operational and financial signals requiring management attention.",
)


risk_items = []


# ------------------------------------------------------------
# Marketing risk
# ------------------------------------------------------------

if not marketing_df.empty:

    lowest_roas_row = (
        marketing_df
        .sort_values(
            "roas"
        )
        .iloc[0]
    )

    highest_spend_row = (
        marketing_df
        .sort_values(
            "spend",
            ascending=False,
        )
        .iloc[0]
    )

    if (
        str(lowest_roas_row["channel"])
        ==
        str(highest_spend_row["channel"])
    ):

        risk_items.append(
            {
                "level": "ATTENTION",
                "title": (
                    f"{lowest_roas_row['channel']} efficiency"
                ),
                "detail": (
                    f"Highest spend channel at "
                    f"{format_business_amount(highest_spend_row['spend'])} "
                    f"with ROAS "
                    f"{safe_float(lowest_roas_row['roas']):.2f}x."
                ),
                "action": (
                    "Review campaign efficiency before "
                    "increasing spend."
                ),
            }
        )


# ------------------------------------------------------------
# Inventory risk
# ------------------------------------------------------------

try:

    inventory_query = """
    WITH latest AS (

        SELECT DISTINCT ON (product_id)

            product_id,
            closing_stock,
            reorder_level,
            date

        FROM inventory

        WHERE date <= :end_date

        ORDER BY
            product_id,
            date DESC
    )

    SELECT
        COUNT(*) AS risk_products

    FROM latest

    WHERE closing_stock <= reorder_level
    """

    inventory_risk = read_sql(
        inventory_query,
        {
            "end_date": end_date,
        },
    ).iloc[0]

    risk_products = int(
        safe_float(
            inventory_risk["risk_products"]
        )
    )

    if risk_products >= 10:

        risk_items.append(
            {
                "level": "WATCH",
                "title": "Inventory pressure",
                "detail": (
                    f"{risk_products} products are "
                    f"at or below reorder level."
                ),
                "action": (
                    "Prioritize replenishment for "
                    "high-demand SKUs."
                ),
            }
        )

except Exception:
    pass


# ------------------------------------------------------------
# Category return risk
# ------------------------------------------------------------

if not categories.empty:

    highest_return_pressure = categories.sort_values(
        "return_rate_change",
        ascending=False,
    ).iloc[0]

    return_pressure = safe_float(
        highest_return_pressure[
            "return_rate_change"
        ]
    )

    if return_pressure >= 2:

        risk_items.append(
            {
                "level": "ATTENTION",
                "title": (
                    f"{highest_return_pressure['category']} "
                    "return pressure"
                ),
                "detail": (
                    f"Return rate increased "
                    f"{return_pressure:.2f} "
                    f"percentage points."
                ),
                "action": (
                    "Investigate return reasons and "
                    "top-returning SKUs."
                ),
            }
        )


if not risk_items:

    st.success(
        "No configured major risk threshold was breached."
    )

else:

    risk_columns = st.columns(
        min(
            len(risk_items),
            3,
        ),
        gap="medium",
    )

    for column, risk in zip(
        risk_columns,
        risk_items[:3],
    ):

        with column:

            with st.container(border=True):

                if risk["level"] == "ATTENTION":

                    st.error(
                        risk["level"]
                    )

                else:

                    st.warning(
                        risk["level"]
                    )

                st.markdown(
                    f"### {risk['title']}"
                )

                st.write(
                    risk["detail"]
                )

                st.caption(
                    f"Action: {risk['action']}"
                )


# ============================================================
# 14. BUSINESS TRENDS
# ============================================================

section(
    "Business Trends",
    "Monthly revenue and profit movement around the selected period.",
)


trend_query = """
SELECT

    DATE_TRUNC(
        'month',
        o.order_date
    ) AS month,

    SUM(oi.revenue) AS revenue,

    SUM(oi.profit) AS profit

FROM orders o

JOIN order_items oi
    ON o.order_id = oi.order_id

WHERE o.order_status = 'Delivered'

  AND o.order_date >= (
      :start_date
      - INTERVAL '11 months'
  )

  AND o.order_date < (
      :end_date
      + INTERVAL '1 day'
  )

GROUP BY 1

ORDER BY 1
"""


try:

    trend_df = read_sql(
        trend_query,
        {
            "start_date": start_date,
            "end_date": end_date,
        },
    )

except Exception:

    trend_df = pd.DataFrame()


if trend_df.empty:

    st.info(
        "Trend data is unavailable."
    )

else:

    trend_df["month"] = pd.to_datetime(
        trend_df["month"]
    )

    trend_df["revenue"] = pd.to_numeric(
        trend_df["revenue"],
        errors="coerce",
    ).fillna(0)

    trend_df["profit"] = pd.to_numeric(
        trend_df["profit"],
        errors="coerce",
    ).fillna(0)

    trend_columns = st.columns(
        2,
        gap="medium",
    )

    # --------------------------------------------------------
    # Revenue trend
    # --------------------------------------------------------

    with trend_columns[0]:

        revenue_chart = go.Figure()

        revenue_chart.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["revenue"],
                mode="lines+markers",
                name="Revenue",
                line=dict(
                    color="#6366f1",
                    width=3,
                ),
                marker=dict(
                    size=6,
                ),
                hovertemplate=(
                    "%{x|%b %Y}"
                    "<br>Revenue: ₹%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )

        revenue_chart.update_layout(
            title="Revenue Trend",
            height=330,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0f172a",
            showlegend=False,
            hovermode="x",
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(
                l=15,
                r=15,
                t=50,
                b=15,
            ),
            font=dict(
                color="#cbd5e1",
            ),
        )

        st.plotly_chart(
            revenue_chart,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

    # --------------------------------------------------------
    # Profit trend
    # --------------------------------------------------------

    with trend_columns[1]:

        profit_chart = go.Figure()

        profit_chart.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["profit"],
                mode="lines+markers",
                name="Profit",
                line=dict(
                    color="#22c55e",
                    width=3,
                ),
                marker=dict(
                    size=6,
                ),
                hovertemplate=(
                    "%{x|%b %Y}"
                    "<br>Profit: ₹%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )

        profit_chart.update_layout(
            title="Profit Trend",
            height=330,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0f172a",
            showlegend=False,
            hovermode="x",
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(
                l=15,
                r=15,
                t=50,
                b=15,
            ),
            font=dict(
                color="#cbd5e1",
            ),
        )

        st.plotly_chart(
            profit_chart,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )


# ============================================================
# 15. ASK EXECUTIVE AI
# ============================================================

section(
    "Ask Executive AI",
    "Ask a natural-language business question. "
    "The Agentic AI workflow determines which analytical "
    "agents are required and investigates the available evidence.",
)


with st.container(border=True):

    st.markdown(
        "### 🤖 Executive AI"
    )

    st.caption(
        "Example: Why did profit decrease in September "
        "and what should management do next?"
    )

    question = st.text_input(
        "Business Question",
        placeholder=(
            "Why did profit decrease in September "
            "and what should management do next?"
        ),
        key="executive_question",
    )

    analyze_button = st.button(
        "Analyze Business Question",
        type="primary",
        use_container_width=True,
        key="executive_ai_button",
    )


if analyze_button:

    if not question.strip():

        st.warning(
            "Please enter a business question."
        )

    else:

        payload = {
            "question": question.strip(),
            "start_date": str(start_date),
            "end_date": str(end_date),
        }

        try:

            with st.spinner(
                "Executive AI is investigating the business evidence..."
            ):

                response = requests.post(
                    f"{API_BASE_URL}/api/agent/ask",
                    json=payload,
                    timeout=90,
                )

            response.raise_for_status()

            result = response.json()

        except requests.exceptions.RequestException as exc:

            st.error(
                "Unable to connect to the Agentic AI backend."
            )

            st.caption(
                f"Backend: {API_BASE_URL}"
            )

            st.exception(exc)

        except ValueError as exc:

            st.error(
                "The Agentic AI backend returned an invalid response."
            )

            st.exception(exc)

        else:

            # ==================================================
            # ORCHESTRATION
            # ==================================================

            orchestration = (
                result.get(
                    "orchestration"
                )
                or {}
            )

            plan = (
                orchestration.get(
                    "plan"
                )
                or []
            )

            executed_stages = (
                orchestration.get(
                    "executed_stages"
                )
                or []
            )

            evidence = (
                orchestration.get(
                    "evidence"
                )
                or {}
            )

            reasoning = (
                orchestration.get(
                    "reasoning"
                )
                or []
            )


            if plan:

                with st.expander(
                    "View Agentic Investigation",
                    expanded=False,
                ):

                    # --------------------------------------------------
                    # OBJECTIVE
                    # --------------------------------------------------

                    st.markdown(
                        "#### Objective"
                    )

                    st.write(
                        orchestration.get(
                            "objective",
                            "Business analysis",
                        )
                    )

                    # --------------------------------------------------
                    # PLANNED AGENTS
                    # --------------------------------------------------

                    st.markdown(
                        "#### Planned Agents / Stages"
                    )

                    st.info(
                        " → ".join(
                            plan
                        )
                    )

                    # --------------------------------------------------
                    # EXECUTED AGENTS
                    # --------------------------------------------------

                    if executed_stages:

                        st.markdown(
                            "#### Executed Stages"
                        )

                        st.success(
                            " → ".join(
                                executed_stages
                            )
                        )

                    # --------------------------------------------------
                    # ORCHESTRATOR REASONING
                    # --------------------------------------------------

                    if reasoning:

                        st.markdown(
                            "#### Why These Agents Were Selected"
                        )

                        for item in reasoning:

                            st.write(
                                f"• {item}"
                            )

                    # --------------------------------------------------
                    # EVIDENCE
                    # --------------------------------------------------

                    st.markdown(
                        "#### Evidence Collected"
                    )

                    if isinstance(
                        evidence,
                        dict,
                    ):

                        evidence_sufficient = (
                            evidence.get(
                                "sufficient"
                            )
                        )

                        if evidence_sufficient is True:

                            st.success(
                                "Sufficient analytical evidence was collected."
                            )

                        elif evidence_sufficient is False:

                            st.warning(
                                "Additional analytical evidence may be required."
                            )

                        evidence_items = (
                            evidence.get(
                                "evidence",
                                [],
                            )
                            or []
                        )

                        if evidence_items:

                            for item in evidence_items:

                                readable_item = (
                                    str(item)
                                    .replace(
                                        "_",
                                        " ",
                                    )
                                    .title()
                                )

                                st.write(
                                    f"• {readable_item}"
                                )

                        missing_evidence = (
                            evidence.get(
                                "missing",
                                [],
                            )
                            or []
                        )

                        if missing_evidence:

                            st.warning(
                                "Missing evidence:"
                            )

                            for item in missing_evidence:

                                readable_item = (
                                    str(item)
                                    .replace(
                                        "_",
                                        " ",
                                    )
                                    .title()
                                )

                                st.write(
                                    f"• {readable_item}"
                                )

                        evidence_reason = (
                            evidence.get(
                                "reason"
                            )
                        )

                        if evidence_reason:

                            st.caption(
                                evidence_reason
                            )

                    elif isinstance(
                        evidence,
                        list,
                    ):

                        for item in evidence:

                            readable_item = (
                                str(item)
                                .replace(
                                    "_",
                                    " ",
                                )
                                .title()
                            )

                            st.write(
                                f"• {readable_item}"
                            )

            # ==================================================
            # INTENT
            # ==================================================

            intent = (
                result.get(
                    "intent"
                )
                or {}
            )

            metric = intent.get(
                "metric"
            )

            # ==================================================
            # BUSINESS ANALYSIS
            # ==================================================

            analysis = (
                result.get(
                    "analysis"
                )
                or {}
            )

            if analysis:

                st.markdown(
                    "### Business Result"
                )

                current_result = safe_float(
                    analysis.get(
                        "current_value",
                        profit,
                    )
                )

                previous_result = safe_float(
                    analysis.get(
                        "previous_value",
                        previous_profit,
                    )
                )

                result_change = safe_float(
                    analysis.get(
                        "change_percent",
                        percentage_change(
                            current_result,
                            previous_result,
                        ),
                    )
                )

                analysis_cols = st.columns(
                    3,
                    gap="medium",
                )

                with analysis_cols[0]:

                    st.metric(
                        "Current Result",
                        format_metric_value(
                            metric or "profit",
                            current_result,
                        ),
                    )

                with analysis_cols[1]:

                    st.metric(
                        "Previous Result",
                        format_metric_value(
                            metric or "profit",
                            previous_result,
                        ),
                    )

                with analysis_cols[2]:

                    st.metric(
                        "Movement",
                        f"{result_change:+.2f}%",
                    )

            # ==================================================
            # ROOT CAUSE
            # ==================================================

            root_cause = (
                result.get(
                    "root_cause"
                )
                or {}
            )

            root_categories = (
                root_cause.get(
                    "categories"
                )
                or []
            )

            if root_categories:

                st.markdown(
                    "### Root Cause"
                )

                root_df = pd.DataFrame(
                    root_categories
                )

                if not root_df.empty:

                    columns_to_show = [
                        "category",
                        "profit_change",
                        "profit_change_percent",
                        "margin_change_percentage_points",
                        "return_rate_change_percentage_points",
                        "discount_rate_change_percentage_points",
                    ]

                    available_columns = [
                        column
                        for column
                        in columns_to_show
                        if column in root_df.columns
                    ]

                    if available_columns:

                        display_root = root_df[
                            available_columns
                        ].copy()

                        rename_map = {
                            "category": "Category",
                            "profit_change": "Profit Change",
                            "profit_change_percent": "Profit Change %",
                            "margin_change_percentage_points": "Margin Change (pp)",
                            "return_rate_change_percentage_points": "Return Rate Change (pp)",
                            "discount_rate_change_percentage_points": "Discount Rate Change (pp)",
                        }

                        display_root = display_root.rename(
                            columns=rename_map
                        )

                        if "Profit Change" in display_root.columns:

                            display_root[
                                "Profit Change"
                            ] = display_root[
                                "Profit Change"
                            ].apply(
                                format_rupees
                            )

                        st.dataframe(
                            display_root,
                            use_container_width=True,
                            hide_index=True,
                        )

            # ==================================================
            # RECOMMENDATIONS
            # ==================================================

            # ==================================================
            # RECOMMENDATIONS
            # ==================================================

            # The backend may return recommendations at the top
            # level or inside the recommendation agent result.
            # Normalize both formats before rendering.

            recommendations = (
                result.get(
                    "recommendations"
                )
                or []
            )

            if not recommendations:

                recommendation_result = (
                    result.get(
                        "recommendation"
                    )
                    or {}
                )

                if isinstance(
                    recommendation_result,
                    dict,
                ):

                    recommendations = (
                        recommendation_result.get(
                            "recommendations"
                        )
                        or recommendation_result.get(
                            "actions"
                        )
                        or []
                    )

                elif isinstance(
                    recommendation_result,
                    list,
                ):

                    recommendations = (
                        recommendation_result
                    )

            # Some backend responses may wrap the list one level
            # deeper under "result".

            if (
                not recommendations
                and isinstance(
                    result.get("recommendation"),
                    dict,
                )
            ):

                nested_recommendation = (
                    result.get("recommendation")
                )

                nested_result = (
                    nested_recommendation.get(
                        "result"
                    )
                    or {}
                )

                if isinstance(
                    nested_result,
                    dict,
                ):

                    recommendations = (
                        nested_result.get(
                            "recommendations"
                        )
                        or nested_result.get(
                            "actions"
                        )
                        or []
                    )

            if recommendations:

                st.markdown(
                    "### Recommended Actions"
                )

                for index, recommendation in enumerate(
                    recommendations[:5],
                    start=1,
                ):

                    if not isinstance(
                        recommendation,
                        dict,
                    ):

                        recommendation = {
                            "action": str(
                                recommendation
                            )
                        }

                    action = (
                        recommendation.get(
                            "action"
                        )
                        or recommendation.get(
                            "title"
                        )
                        or recommendation.get(
                            "recommendation"
                        )
                        or "Management action"
                    )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### {index:02d}. {action}"
                        )

                        priority = str(
                            recommendation.get(
                                "priority",
                                ""
                            )
                        ).strip()

                        if priority:

                            if priority.lower() == "high":

                                st.error(
                                    f"{priority.upper()} PRIORITY"
                                )

                            elif priority.lower() == "medium":

                                st.warning(
                                    f"{priority.upper()} PRIORITY"
                                )

                            else:

                                st.info(
                                    f"{priority.upper()} PRIORITY"
                                )

                        reason = (
                            recommendation.get(
                                "reason"
                            )
                            or recommendation.get(
                                "problem"
                            )
                        )

                        if reason:

                            st.write(
                                f"**Reason:** {reason}"
                            )

                        recommended_action = (
                            recommendation.get(
                                "recommended_action"
                            )
                            or recommendation.get(
                                "action_detail"
                            )
                        )

                        if recommended_action:

                            st.write(
                                f"**Recommended Action:** "
                                f"{recommended_action}"
                            )

                        expected_impact = (
                            recommendation.get(
                                "expected_impact"
                            )
                            or recommendation.get(
                                "objective"
                            )
                        )

                        if expected_impact:

                            st.write(
                                f"**Expected Impact:** "
                                f"{expected_impact}"
                            )

                        time_horizon = (
                            recommendation.get(
                                "time_horizon"
                            )
                        )

                        if time_horizon:

                            st.write(
                                f"**Time Horizon:** "
                                f"{time_horizon}"
                            )

                        owner = (
                            recommendation.get(
                                "owner"
                            )
                        )

                        if owner:

                            st.caption(
                                f"Owner: {owner}"
                            )

            else:

                st.info(
                    "No specific management recommendations "
                    "were returned by the Agentic AI workflow."
                )

            # ==================================================
            # STRATEGY
            # ==================================================

            strategies = (
                result.get(
                    "strategies"
                )
                or {}
            )

            if strategies:

                st.markdown(
                    "### Strategic Priorities"
                )

                strategy_columns = st.columns(
                    3,
                    gap="medium",
                )

                strategy_groups = [
                    (
                        strategy_columns[0],
                        "Profit Recovery",
                        strategies.get(
                            "profit_recovery",
                            [],
                        ),
                    ),
                    (
                        strategy_columns[1],
                        "Profitable Growth",
                        strategies.get(
                            "profitable_growth",
                            [],
                        ),
                    ),
                    (
                        strategy_columns[2],
                        "Risk Protection",
                        strategies.get(
                            "risk_protection",
                            [],
                        ),
                    ),
                ]

                for column, title, items in strategy_groups:

                    with column:

                        st.markdown(
                            f"#### {title}"
                        )

                        if not items:

                            st.caption(
                                "No priority identified."
                            )

                        else:

                            for item in items[:3]:

                                if isinstance(
                                    item,
                                    dict,
                                ):

                                    strategy_text = (
                                        item.get(
                                            "action"
                                        )
                                        or item.get(
                                            "strategy"
                                        )
                                        or item.get(
                                            "title"
                                        )
                                        or str(item)
                                    )

                                else:

                                    strategy_text = str(
                                        item
                                    )

                                st.write(
                                    f"• {strategy_text}"
                                )

            # ==================================================
            # MARKETING
            # ==================================================

            marketing_result = (
                result.get(
                    "marketing"
                )
                or {}
            )

            marketing_analysis = (
                marketing_result.get(
                    "analysis"
                )
                or {}
            )

            marketing_channels = (
                marketing_analysis.get(
                    "channels"
                )
                or []
            )

            if marketing_channels:

                st.markdown(
                    "### Marketing Evidence"
                )

                marketing_result_df = pd.DataFrame(
                    marketing_channels
                )

                if not marketing_result_df.empty:

                    selected_columns = [
                        "channel",
                        "spend",
                        "revenue_generated",
                        "roas",
                        "conversion_rate",
                        "customer_acquisition_cost",
                    ]

                    selected_columns = [
                        column
                        for column
                        in selected_columns
                        if column
                        in marketing_result_df.columns
                    ]

                    display_marketing = (
                        marketing_result_df[
                            selected_columns
                        ].copy()
                    )

                    display_marketing = (
                        display_marketing.rename(
                            columns={
                                "channel": "Channel",
                                "spend": "Spend",
                                "revenue_generated": "Revenue Generated",
                                "roas": "ROAS",
                                "conversion_rate": "Conversion Rate",
                                "customer_acquisition_cost": "CAC",
                            }
                        )
                    )

                    if "Spend" in display_marketing.columns:

                        display_marketing[
                            "Spend"
                        ] = display_marketing[
                            "Spend"
                        ].apply(
                            format_rupees
                        )

                    if "Revenue Generated" in display_marketing.columns:

                        display_marketing[
                            "Revenue Generated"
                        ] = display_marketing[
                            "Revenue Generated"
                        ].apply(
                            format_rupees
                        )

                    if "ROAS" in display_marketing.columns:

                        display_marketing[
                            "ROAS"
                        ] = display_marketing[
                            "ROAS"
                        ].apply(
                            lambda value:
                            f"{safe_float(value):.2f}x"
                        )

                    if "Conversion Rate" in display_marketing.columns:

                        display_marketing[
                            "Conversion Rate"
                        ] = display_marketing[
                            "Conversion Rate"
                        ].apply(
                            lambda value:
                            f"{safe_float(value):.2f}%"
                        )

                    if "CAC" in display_marketing.columns:

                        display_marketing[
                            "CAC"
                        ] = display_marketing[
                            "CAC"
                        ].apply(
                            format_rupees
                        )

                    st.dataframe(
                        display_marketing,
                        use_container_width=True,
                        hide_index=True,
                    )

            # ==================================================
            # CROSS DOMAIN
            # ==================================================

            cross_domain = (
                result.get(
                    "cross_domain"
                )
                or {}
            )

            cross_recommendations = (
                cross_domain.get(
                    "recommendations"
                )
                or []
            )

            causality_note = (
                cross_domain.get(
                    "causality_note"
                )
            )

            if cross_recommendations:

                st.markdown(
                    "### Cross-Domain Signals"
                )

                for recommendation in cross_recommendations[:5]:

                    if isinstance(
                        recommendation,
                        dict,
                    ):

                        title = (
                            recommendation.get(
                                "action"
                            )
                            or recommendation.get(
                                "title"
                            )
                            or "Cross-domain signal"
                        )

                        reason = (
                            recommendation.get(
                                "reason"
                            )
                        )

                        st.write(
                            f"**{title}**"
                        )

                        if reason:

                            st.caption(
                                reason
                            )

                    else:

                        st.write(
                            f"• {recommendation}"
                        )

            if causality_note:

                st.info(
                    causality_note
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "E-Commerce Agentic BI  ·  "
    "Executive Decision Support  ·  "
    "SEE → UNDERSTAND → ACT"
)