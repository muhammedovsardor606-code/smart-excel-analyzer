"""
app.py — Smart Excel Analyzer
Excel yuklang -> avtomatik tahlil -> dashboard -> AI xulosa.
Ishga tushirish:  streamlit run app.py
"""
import streamlit as st

from analyzer.data_loader import get_sheet_names, load_excel
from analyzer.auto_analysis import run_full_analysis
from analyzer.charts import build_charts
from analyzer.ai_summary import ai_summary

# ---------- Sahifa sozlamalari ----------
st.set_page_config(page_title="Smart Excel Analyzer", page_icon="📊", layout="wide")

st.title("📊 Smart Excel Analyzer")
st.markdown(
    "Excel faylingizni yuklang — dastur uni **avtomatik tahlil qiladi**, "
    "**dashboard** chizadi va oddiy tilda **xulosa** beradi. "
    "Dasturlashni bilish shart emas. 👇"
)

# ---------- Fayl yuklash ----------
uploaded = st.file_uploader("Excel faylni tanlang (.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("⬆️ Boshlash uchun Excel fayl yuklang. "
            "Masalan: sotuvlar, xarajatlar yoki mijozlar jadvali.")
    st.stop()

# ---------- Varaqni tanlash ----------
sheets = get_sheet_names(uploaded)
if len(sheets) > 1:
    sheet = st.selectbox("Qaysi varaqni tahlil qilamiz?", sheets)
else:
    sheet = sheets[0] if sheets else 0

try:
    df = load_excel(uploaded, sheet_name=sheet)
except Exception as e:
    st.error(f"Faylni o'qishda xatolik: {e}")
    st.stop()

if df.empty:
    st.warning("Jadval bo'sh ko'rinadi. Boshqa fayl yoki varaqni sinab ko'ring.")
    st.stop()

# ---------- Ma'lumotni ko'rsatish ----------
st.subheader("1️⃣ Yuklangan ma'lumot")
st.dataframe(df.head(50), use_container_width=True)
st.caption(f"Jami {df.shape[0]} qator, {df.shape[1]} ustun ko'rsatildi (birinchi 50 tasi).")

# ---------- Tahlil ----------
analysis = run_full_analysis(df)
ov = analysis["overview"]

st.subheader("2️⃣ Asosiy ko'rsatkichlar")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Qatorlar", ov["rows"])
c2.metric("Ustunlar", ov["cols"])
c3.metric("Bo'sh kataklar", f'{ov["missing"]} ({ov["missing_pct"]}%)')
c4.metric("Takrorlar", ov["duplicates"])

# Raqamli ustunlar uchun tez ko'rsatkichlar
if analysis["numeric"]:
    st.markdown("**🔢 Raqamli ustunlar (yig'indi / o'rtacha):**")
    cols = st.columns(min(4, len(analysis["numeric"])))
    for i, (col, st_data) in enumerate(list(analysis["numeric"].items())[:4]):
        cols[i].metric(col, f"Σ {st_data['sum']:,.0f}", f"⌀ {st_data['mean']:,.1f}")

# ---------- Dashboard ----------
st.subheader("3️⃣ Dashboard")
charts = build_charts(df, analysis)
if not charts:
    st.info("Bu ma'lumot uchun avtomatik grafik yasab bo'lmadi "
            "(raqamli yoki sanali ustun topilmadi).")
else:
    # Grafiklarni 2 ustunli to'rda joylaymiz
    for i in range(0, len(charts), 2):
        row = st.columns(2)
        for j, (title, fig) in enumerate(charts[i:i+2]):
            with row[j]:
                st.markdown(f"**{title}**")
                st.plotly_chart(fig, use_container_width=True)

# ---------- AI xulosa ----------
st.subheader("4️⃣ Xulosa va tavsiyalar")
with st.spinner("Xulosa tayyorlanmoqda..."):
    summary_text, mode = ai_summary(df, analysis)

if mode == "ai":
    st.success("🤖 AI tahlili (Claude)")
else:
    st.info("💡 Avtomatik tahlil (bepul rejim)")

st.markdown(summary_text)

st.divider()
st.caption("Smart Excel Analyzer — kichik va o'rta biznes uchun avtomatik tahlil vositasi.")
