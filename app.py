"""
app.py — Smart Excel Analyzer v2
Excel yuklang -> avtomatik tahlil -> KPI -> dashboard -> reyting -> xulosa.
Ishga tushirish:  streamlit run app.py
"""
import streamlit as st

from analyzer.data_loader import get_sheet_names, load_excel
from analyzer.auto_analysis import (
    run_full_analysis, pick_main_metric, keyword_groups,
    numeric_bins, top_bottom, find_issues,
)
from analyzer.charts import (
    build_charts, chart_keyword_groups, chart_keyword_donut,
    chart_numeric_bins, chart_top,
)
from analyzer.ai_summary import ai_summary

# ---------- Sahifa sozlamalari ----------
st.set_page_config(page_title="Smart Excel Analyzer", page_icon="📊", layout="wide")

# ---------- Ozgina chiroyli uslub (CSS) ----------
st.markdown("""
<style>
    .main-title { font-size: 2.4rem; font-weight: 800; margin-bottom: 0; }
    .subtitle { color: #8aa; font-size: 1.05rem; margin-top: .2rem; }
    div[data-testid="stMetric"] {
        background: rgba(46,139,87,0.08);
        border: 1px solid rgba(46,139,87,0.25);
        border-radius: 14px; padding: 14px 16px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.7rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Smart Excel Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Excel faylingizni yuklang — dastur uni avtomatik '
            'tahlil qiladi, dashboard chizadi va oddiy tilda xulosa beradi.</div>',
            unsafe_allow_html=True)
st.write("")

# ---------- Fayl yuklash ----------
uploaded = st.file_uploader("Excel faylni tanlang (.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("⬆️ Boshlash uchun Excel fayl yuklang. "
            "Masalan: sotuvlar, xarajatlar, obyektlar yoki mijozlar jadvali.")
    st.stop()

# ---------- Varaqni tanlash ----------
sheets = get_sheet_names(uploaded)
sheet = st.selectbox("Qaysi varaqni tahlil qilamiz?", sheets) if len(sheets) > 1 else (sheets[0] if sheets else 0)

try:
    df = load_excel(uploaded, sheet_name=sheet)
except Exception as e:
    st.error(f"Faylni o'qishda xatolik: {e}")
    st.stop()

if df.empty:
    st.warning("Jadval bo'sh ko'rinadi. Boshqa fayl yoki varaqni sinab ko'ring.")
    st.stop()

# ---------- Tahlil ----------
analysis = run_full_analysis(df)
ov = analysis["overview"]
col_types = analysis["col_types"]
main_metric = pick_main_metric(analysis["numeric"], col_types)

# Asosiy matn ("o'lcham") ustunini tanlaymiz — eng ko'p xil qiymatli matn ustuni
text_cols = [c for c, t in col_types.items() if t == "categorical"]
main_text = max(text_cols, key=lambda c: df[c].nunique(), default=None) if text_cols else None

# ---------- KPI kartalar ----------
st.subheader("📌 Asosiy ko'rsatkichlar")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Qatorlar", f"{ov['rows']:,}")
k2.metric("Ustunlar", ov["cols"])
k3.metric("Bo'sh kataklar", f"{ov['missing']} ({ov['missing_pct']}%)")
k4.metric("Takrorlar", ov["duplicates"])

if analysis["numeric"]:
    cols = st.columns(min(4, len(analysis["numeric"])))
    for i, (col, sd) in enumerate(list(analysis["numeric"].items())[:4]):
        cols[i].metric(f"Σ {col}", f"{sd['sum']:,.0f}", f"⌀ {sd['mean']:,.1f}")

st.divider()

# ---------- TABLAR ----------
tab1, tab2, tab3, tab4 = st.tabs(["🗂 Umumiy", "📊 Dashboard", "🏆 Reyting", "⚠️ Xatoliklar"])

# === TAB 1: Umumiy ===
with tab1:
    st.markdown("**Yuklangan ma'lumot (birinchi 50 qator):**")
    st.dataframe(df.head(50), use_container_width=True)
    st.caption(f"Jami {df.shape[0]:,} qator, {df.shape[1]} ustun.")

    st.markdown("**Ustun turlari:**")
    type_uz = {"numeric": "🔢 Raqam", "datetime": "📅 Sana", "categorical": "🏷 Matn/Toifa"}
    cols_info = st.columns(min(4, len(col_types)))
    for i, (col, t) in enumerate(col_types.items()):
        cols_info[i % len(cols_info)].markdown(f"**{col}**\n\n{type_uz.get(t, t)}")

# === TAB 2: Dashboard ===
with tab2:
    rendered = False

    # 1) Kalit so'z guruhlari (matn nomlaridan sohalar) + donut
    if main_text and main_metric and df[main_text].nunique() > 12:
        groups = keyword_groups(df, main_text, main_metric, top_n=8)
        if groups:
            rendered = True
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**🔑 '{main_text}' bo'yicha asosiy guruhlar ('{main_metric}' yig'indisi)**")
                fig = chart_keyword_groups(groups, main_metric)
                if fig: st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("**🥧 Guruhlar ulushi**")
                fig = chart_keyword_donut(groups)
                if fig: st.plotly_chart(fig, use_container_width=True)

    # 2) Raqamli guruhlar (diapazonlar)
    bin_cols = [c for c, t in col_types.items() if t == "numeric"]
    bin_charts = []
    for col in bin_cols[:2]:
        bins = numeric_bins(df, col)
        if bins:
            bin_charts.append((col, bins))
    if bin_charts:
        rendered = True
        st.markdown("**📊 Qiymat guruhlari (diapazonlar bo'yicha)**")
        cc = st.columns(len(bin_charts))
        for i, (col, bins) in enumerate(bin_charts):
            with cc[i]:
                st.markdown(f"_{col}_")
                fig = chart_numeric_bins(bins, col)
                if fig: st.plotly_chart(fig, use_container_width=True)

    # 3) Standart grafiklar (trend, taqqoslash va h.k.)
    charts = build_charts(df, analysis)
    if charts:
        rendered = True
        for i in range(0, len(charts), 2):
            row = st.columns(2)
            for j, (title, fig) in enumerate(charts[i:i + 2]):
                with row[j]:
                    st.markdown(f"**{title}**")
                    st.plotly_chart(fig, use_container_width=True)

    if not rendered:
        st.info("Bu ma'lumot uchun avtomatik grafik yasab bo'lmadi.")

# === TAB 3: Reyting ===
with tab3:
    if main_text and main_metric:
        tb = top_bottom(df, main_text, main_metric, n=8)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🔝 Eng yuqori '{main_metric}' ('{main_text}' bo'yicha)**")
            fig = chart_top(tb["top"], main_metric)
            if fig: st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown(f"**🔻 Eng past '{main_metric}'**")
            st.table({k: f"{v:,.1f}" for k, v in tb["bottom"].items()})
    else:
        st.info("Reyting uchun matnli (nom) va raqamli ustun kerak.")

# === TAB 4: Xatoliklar ===
with tab4:
    st.markdown("**Tekshirish kerak bo'lgan joylar:**")
    for issue in find_issues(df, analysis):
        st.markdown(f"- {issue}")

st.divider()

# ---------- AI xulosa ----------
st.subheader("🤖 Xulosa va tavsiyalar")
with st.spinner("Xulosa tayyorlanmoqda..."):
    summary_text, mode = ai_summary(df, analysis)
if mode == "ai":
    st.success("🤖 AI tahlili (Claude)")
else:
    st.info("💡 Avtomatik tahlil (bepul rejim)")
st.markdown(summary_text)

st.divider()
st.caption("Smart Excel Analyzer v2 — kichik va o'rta biznes uchun avtomatik tahlil vositasi.")
