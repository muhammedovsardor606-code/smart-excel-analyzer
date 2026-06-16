"""
auto_analysis.py
Excel ma'lumotlarini avtomatik tahlil qiladi:
ustun turlarini aniqlaydi, statistikani hisoblaydi, muhim ko'rsatkichlarni topadi.
"""
import warnings
import pandas as pd
import numpy as np

# Sana o'qishdagi keraksiz ogohlantirishlarni o'chiramiz
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")


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
