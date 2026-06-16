"""
data_loader.py
Excel faylni o'qish va varaqlarni boshqarish.
"""
import pandas as pd


def get_sheet_names(file):
    """Excel faylidagi barcha varaqlar (sheet) nomlarini qaytaradi."""
    try:
        xls = pd.ExcelFile(file, engine="openpyxl")
        return xls.sheet_names
    except Exception:
        return []


def load_excel(file, sheet_name=0):
    """
    Tanlangan varaqni DataFrame ko'rinishida o'qiydi.
    Bo'sh ustun/qatorlarni tozalaydi.
    """
    df = pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl")

    # To'liq bo'sh ustun va qatorlarni olib tashlaymiz
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    # Ustun nomlarini matnga aylantiramiz (raqamli sarlavhalar bo'lsa)
    df.columns = [str(c).strip() for c in df.columns]

    return df
