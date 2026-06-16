"""
charts.py
Tahlil natijasiga qarab eng muhim grafiklarni avtomatik yasaydi.
Plotly figuralar ro'yxatini qaytaradi (sarlavha bilan).
"""
import plotly.express as px

# Yagona rang sxemasi (dashboard chiroyli ko'rinishi uchun)
COLOR_SEQ = px.colors.qualitative.Set2


def build_charts(df, analysis, max_charts=6):
    """
    Ma'lumot turlariga qarab grafiklar yasaydi:
    - Sana + raqam   -> trend (chiziqli grafik)
    - Toifa + raqam  -> taqqoslash (ustunli grafik)
    - Raqam          -> taqsimot (gistogramma)
    - Toifa          -> ulush (doiraviy/ustunli)
    """
    col_types = analysis["col_types"]
    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    datetime_cols = [c for c, t in col_types.items() if t == "datetime"]
    cat_cols = [c for c, t in col_types.items() if t == "categorical"]

    charts = []

    # 1) Vaqt bo'yicha trend (sana + birinchi raqamli ustun)
    if datetime_cols and numeric_cols:
        date_col = datetime_cols[0]
        for num_col in numeric_cols[:2]:
            tmp = df[[date_col, num_col]].dropna().sort_values(date_col)
            if len(tmp) > 1:
                fig = px.line(tmp, x=date_col, y=num_col, markers=True,
                              color_discrete_sequence=COLOR_SEQ)
                charts.append((f"📈 '{num_col}' vaqt bo'yicha o'zgarishi", fig))

    # 2) Toifa bo'yicha taqqoslash (toifa + raqam)
    if cat_cols and numeric_cols:
        for cat_col in cat_cols[:2]:
            if df[cat_col].nunique() <= 20:
                num_col = numeric_cols[0]
                grouped = (df.groupby(cat_col)[num_col]
                           .sum().sort_values(ascending=False).head(10).reset_index())
                fig = px.bar(grouped, x=cat_col, y=num_col,
                             color=cat_col, color_discrete_sequence=COLOR_SEQ)
                fig.update_layout(showlegend=False)
                charts.append((f"📊 '{cat_col}' bo'yicha '{num_col}' (yig'indi)", fig))

    # 3) Raqamli ustun taqsimoti (gistogramma)
    for num_col in numeric_cols[:2]:
        fig = px.histogram(df, x=num_col, nbins=20,
                           color_discrete_sequence=COLOR_SEQ)
        charts.append((f"📉 '{num_col}' taqsimoti", fig))

    # 4) Toifa ulushi (doiraviy)
    if cat_cols:
        cat_col = cat_cols[0]
        if 2 <= df[cat_col].nunique() <= 8:
            counts = df[cat_col].value_counts().reset_index()
            counts.columns = [cat_col, "soni"]
            fig = px.pie(counts, names=cat_col, values="soni", hole=0.4,
                         color_discrete_sequence=COLOR_SEQ)
            charts.append((f"🥧 '{cat_col}' ulushi", fig))

    return charts[:max_charts]


# ============================================================
#  v2 — Yangi grafik turlari
# ============================================================
def chart_keyword_groups(groups, metric_name):
    """Kalit so'z guruhlari bo'yicha gorizontal ustunli grafik (sohalar kabi)."""
    if not groups:
        return None
    labels = [g["guruh"] for g in groups]
    values = [g["yigindi"] for g in groups]
    fig = px.bar(x=values, y=labels, orientation="h",
                 color=labels, color_discrete_sequence=COLOR_SEQ)
    fig.update_layout(showlegend=False, yaxis_title="", xaxis_title=metric_name)
    fig.update_yaxes(categoryorder="total ascending")
    return fig


def chart_keyword_donut(groups):
    """Guruhlar ulushi — doiraviy (donut) grafik."""
    if not groups or len(groups) < 2:
        return None
    labels = [g["guruh"] for g in groups]
    values = [g["qatorlar"] for g in groups]
    fig = px.pie(names=labels, values=values, hole=0.45,
                 color_discrete_sequence=COLOR_SEQ)
    return fig


def chart_numeric_bins(bins, col_name):
    """Raqamli diapazon guruhlari bo'yicha ustunli grafik (quvvat guruhlari kabi)."""
    if not bins:
        return None
    fig = px.bar(x=bins["labels"], y=bins["values"],
                 color=bins["labels"], color_discrete_sequence=COLOR_SEQ)
    fig.update_layout(showlegend=False, xaxis_title=col_name, yaxis_title="Soni")
    return fig


def chart_top(top_dict, metric_name):
    """Eng yuqori qiymatli qatorlar reytingi."""
    if not top_dict:
        return None
    labels = list(top_dict.keys())
    values = list(top_dict.values())
    fig = px.bar(x=values, y=labels, orientation="h",
                 color_discrete_sequence=["#2E8B57"])
    fig.update_layout(showlegend=False, yaxis_title="", xaxis_title=metric_name)
    fig.update_yaxes(categoryorder="total ascending")
    return fig
