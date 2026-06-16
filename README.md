# 📊 Smart Excel Analyzer

Kichik va o'rta biznes egalari hamda data-analitiklar uchun **avtomatik Excel tahlil vositasi**.

Foydalanuvchi Excel faylini yuklaydi — dastur uni **avtomatik tahlil qiladi**, **dashboard** chizadi va oddiy o'zbek tilida **xulosa va tavsiyalar** beradi. Dasturlashni bilish shart emas.

## ✨ Imkoniyatlari

- 📤 `.xlsx` fayl yuklash (ko'p varaqli fayllar ham qo'llab-quvvatlanadi)
- 🔍 Ustun turlarini avtomatik aniqlash (raqam / sana / toifa)
- 📈 Asosiy statistika: yig'indi, o'rtacha, min, max, bo'sh kataklar, takrorlar
- 📊 Avtomatik dashboard: trend, taqqoslash, taqsimot va ulush grafiklari
- 🤖 Oddiy tilda xulosa va amaliy tavsiyalar
- 💡 AI rejimi ixtiyoriy (Claude API) — yoki butunlay bepul ishlaydi

## 🚀 Ishga tushirish (kompyuterda)

```bash
# 1. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 2. Ilovani ishga tushirish
streamlit run app.py
```

Brauzerda `http://localhost:8501` avtomatik ochiladi. `sample_data/example.xlsx` faylini sinab ko'ring.

## 🤖 AI rejimini yoqish (ixtiyoriy)

AI yanada tabiiy xulosa yozishi uchun Anthropic API kalitini bering:

```bash
# Windows
set ANTHROPIC_API_KEY=sizning_kalitingiz

# Mac/Linux
export ANTHROPIC_API_KEY=sizning_kalitingiz
```

Kalit berilmasa, dastur **bepul** avtomatik tahlil rejimida ishlayveradi.

## 🛠 Texnologiyalar

Python · Streamlit · pandas · openpyxl · Plotly · Anthropic API

## 📁 Tuzilishi

```
smart-excel-analyzer/
├── app.py                  # asosiy Streamlit ilova
├── requirements.txt
├── analyzer/
│   ├── data_loader.py      # Excel o'qish
│   ├── auto_analysis.py    # avtomatik tahlil
│   ├── charts.py           # grafiklar
│   └── ai_summary.py       # xulosa
└── sample_data/
    └── example.xlsx        # namuna fayl
```
