"""
auto_analysis.py
Excel ma'lumotlarini avtomatik tahlil qiladi:
ustun turlarini aniqlaydi, statistikani hisoblaydi, muhim ko'rsatkichlarni topadi.
"""
import warnings
import pandas as pd
import numpy as np

# Sana o'qishdagi keraksiz ogohlantirishlarni o'chiramiz
warnings.filterwarnings("ignore", category=UserWarning)


def detect_column_types(df):
    """
    Har bir ustunni turga ajratadi:
    - 'numeric'      -> raqamli (sotuv, narx, miqdor)
    - 'datetime'     -> sana/vaqt
    - 'categorical'  -> matnli toifa (shahar, mahsulot)
    """
    types = {}
    for col in df.columns:
        s = df[col]

        # Sana ekanligini tekshiramiz
        if pd.api.types.is_datetime64_any_dtype(s):
            types[col] = "datetime"
            continue

        # Raqam ekanligini tekshiramiz
        if pd.api.types.is_numeric_dtype(s):
            types[col] = "numeric"
            continue

        # Matnni sanaga aylantirib ko'ramiz (masalan "2024-01-05")
        try:
            converted = pd.to_datetime(s, errors="raise")
            # Agar ko'pchiligi sanaga aylansa -> datetime
            if converted.notna().mean() > 0.8:
                df[col] = converted
                types[col] = "datetime"
                continue
        except Exception:
            pass

        types[col] = "categorical"
    return types


def basic_overview(df):
    """Jadval haqida umumiy ma'lumot: qatorlar, ustunlar, bo'sh kataklar."""
    total_cells = df.shape[0] * df.shape[1] if df.shape[1] else 0
    missing = int(df.isna().sum().sum())
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing": missing,
        "missing_pct": round((missing / total_cells * 100), 1) if total_cells else 0.0,
        "duplicates": int(df.duplicated().sum()),
    }


def numeric_stats(df, col_types):
    """Raqamli ustunlar bo'yicha statistika (yig'indi, o'rtacha, min, max)."""
    stats = {}
    for col, t in col_types.items():
        if t == "numeric":
            s = df[col].dropna()
            if len(s) == 0:
                continue
            stats[col] = {
                "sum": float(s.sum()),
                "mean": float(s.mean()),
                "min": float(s.min()),
                "max": float(s.max()),
                "median": float(s.median()),
            }
    return stats


def categorical_stats(df, col_types, top_n=5):
    """Toifa ustunlari bo'yicha eng ko'p uchraydigan qiymatlar."""
    stats = {}
    for col, t in col_types.items():
        if t == "categorical":
            s = df[col].dropna().astype(str)
            if len(s) == 0:
                continue
            counts = s.value_counts().head(top_n)
            stats[col] = {
                "unique": int(s.nunique()),
                "top_values": counts.to_dict(),
            }
    return stats


def find_correlations(df, col_types, threshold=0.5):
    """Raqamli ustunlar orasidagi kuchli bog'liqliklarni topadi."""
    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    results = []
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                val = corr.iloc[i, j]
                if pd.notna(val) and abs(val) >= threshold:
                    results.append((numeric_cols[i], numeric_cols[j], round(float(val), 2)))
    return sorted(results, key=lambda x: abs(x[2]), reverse=True)


def run_full_analysis(df):
    """Hamma tahlilni birlashtirib bitta natija qaytaradi."""
    col_types = detect_column_types(df)
    return {
        "col_types": col_types,
        "overview": basic_overview(df),
        "numeric": numeric_stats(df, col_types),
        "categorical": categorical_stats(df, col_types),
        "correlations": find_correlations(df, col_types),
    }


# ============================================================
#  v2 — Kuchaytirilgan tahlil funksiyalari
# ============================================================
import re
from collections import Counter

# O'zbek/rus/ingliz keng tarqalgan "ahamiyatsiz" so'zlar (toifa uchun kerakmas)
_STOPWORDS = {
    "tuman", "tumani", "shahar", "shahri", "sonli", "viloyati", "viloyat",
    "and", "the", "for", "ltd", "mchj", "ooo", "yj", "filiali",
}

# "Asosiy ko'rsatkich" bo'lishi mumkin bo'lgan ustun nomlari (ustuvor)
_METRIC_HINTS = [
    "summa", "jami", "total", "narx", "price", "daromad", "revenue", "sales",
    "soni", "miqdor", "amount", "quvvat", "value", "qiymat", "balans",
]


def pick_main_metric(numeric_stats_dict, col_types):
    """Eng muhim raqamli ustunni tanlaydi (nom bo'yicha yoki eng katta yig'indi)."""
    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    if not numeric_cols:
        return None
    # 1) Nomi muhim ko'rsatkichga o'xshasa
    for col in numeric_cols:
        low = col.lower()
        if any(h in low for h in _METRIC_HINTS):
            return col
    # 2) Aks holda eng katta yig'indiga ega ustun
    return max(numeric_stats_dict, key=lambda c: abs(numeric_stats_dict[c]["sum"]),
              default=numeric_cols[0])


def extract_keywords(series, top_n=8):
    """
    Matnli ustundan eng ko'p uchraydigan kalit so'zlarni topadi.
    Masalan obyekt nomlaridan: maktab, dispanser, OP, kolleji...
    """
    words = []
    for val in series.dropna().astype(str):
        tokens = re.findall(r"[\w\u02bb\u2019']+", val.lower())
        for t in tokens:
            t = t.strip("\u02bb\u2019'")
            if len(t) > 2 and not t.isdigit() and t not in _STOPWORDS:
                words.append(t)
    return Counter(words).most_common(top_n)


def keyword_groups(df, text_col, metric_col, top_n=8):
    """
    Matn ustunidagi kalit so'zlar bo'yicha qatorlarni guruhlab,
    asosiy ko'rsatkichni yig'adi (artifactdagi "sohalar" kabi).
    """
    keywords = [w for w, _ in extract_keywords(df[text_col], top_n=top_n)]
    rows = []
    for kw in keywords:
        mask = df[text_col].astype(str).str.lower().str.contains(re.escape(kw), na=False)
        sub = df[mask]
        if len(sub) == 0:
            continue
        rows.append({
            "guruh": kw,
            "qatorlar": int(len(sub)),
            "yigindi": float(sub[metric_col].sum()) if metric_col else 0.0,
        })
    return sorted(rows, key=lambda r: r["yigindi"], reverse=True)


def numeric_bins(df, col, n_bins=6):
    """Raqamli ustunni diapazonlarga (guruhlarga) bo'ladi."""
    s = df[col].dropna()
    if len(s) < 5 or s.nunique() < 3:
        return None
    try:
        binned = pd.cut(s, bins=min(n_bins, s.nunique()))
        counts = binned.value_counts().sort_index()
        labels = [f"{int(iv.left)}–{int(iv.right)}" if iv.right > 5
                  else f"{iv.left:.2f}–{iv.right:.2f}" for iv in counts.index]
        return {"labels": labels, "values": [int(v) for v in counts.values]}
    except Exception:
        return None


def top_bottom(df, text_col, metric_col, n=5):
    """Asosiy ko'rsatkich bo'yicha eng yuqori va eng past qatorlar."""
    if not text_col or not metric_col:
        return None
    tmp = df[[text_col, metric_col]].dropna()
    grouped = tmp.groupby(text_col)[metric_col].sum().sort_values(ascending=False)
    return {
        "top": grouped.head(n).to_dict(),
        "bottom": grouped.tail(n).to_dict(),
    }


def find_issues(df, analysis):
    """Shubhali / tekshirish kerak bo'lgan qatorlarni topadi (Xatoliklar tabi)."""
    issues = []
    ov = analysis["overview"]
    if ov["missing"] > 0:
        issues.append(f"{ov['missing']} ta bo'sh katak ({ov['missing_pct']}%) — to'ldirish kerak.")
    if ov["duplicates"] > 0:
        issues.append(f"{ov['duplicates']} ta to'liq takrorlangan qator bor.")
    # Raqamli ustunlarda g'alati (chetdagi) qiymatlar
    for col, t in analysis["col_types"].items():
        if t == "numeric":
            s = df[col].dropna()
            if len(s) < 10:
                continue
            mean, std = s.mean(), s.std()
            if std and std > 0:
                outliers = s[(s < mean - 3 * std) | (s > mean + 3 * std)]
                if len(outliers) > 0:
                    issues.append(
                        f"'{col}' ustunida {len(outliers)} ta g'ayrioddiy qiymat "
                        f"(o'rtachadan juda uzoq) — tekshirib chiqing."
                    )
            negatives = s[s < 0]
            if len(negatives) > 0:
                issues.append(f"'{col}' ustunida {len(negatives)} ta manfiy qiymat bor.")
    if not issues:
        issues.append("✅ Jiddiy muammo topilmadi — ma'lumot toza ko'rinadi.")
    return issues
