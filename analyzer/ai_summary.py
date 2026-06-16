"""
ai_summary.py
Tahlil natijasidan oddiy tilda (o'zbekcha) xulosa yozadi.

Ikki rejim:
  - BEPUL (standart): aqlli qoidalar asosida xulosa yozadi. API kalit kerak emas.
  - AI (ixtiyoriy): agar ANTHROPIC_API_KEY berilgan bo'lsa, Claude yanada
    tabiiy, professional xulosa yozadi.
"""
import os


def _fmt(num):
    """Katta raqamlarni o'qishga qulay ko'rinishda chiqaradi."""
    try:
        if abs(num) >= 1_000_000:
            return f"{num/1_000_000:.1f} mln"
        if abs(num) >= 1_000:
            return f"{num/1_000:.1f} ming"
        return f"{num:,.0f}" if num == int(num) else f"{num:,.2f}"
    except Exception:
        return str(num)


def rule_based_summary(df, analysis):
    """API'siz, mantiqqa asoslangan o'zbekcha xulosa."""
    ov = analysis["overview"]
    lines = []

    lines.append(
        f"📋 **Umumiy ko'rinish.** Jadvalda {ov['rows']} ta qator va "
        f"{ov['cols']} ta ustun bor."
    )

    # Bo'sh kataklar haqida ogohlantirish
    if ov["missing"] > 0:
        lines.append(
            f"⚠️ **Diqqat:** ma'lumotning {ov['missing_pct']}% qismi bo'sh "
            f"({ov['missing']} ta katak). Aniq xulosa uchun bo'sh joylarni "
            f"to'ldirish tavsiya etiladi."
        )
    else:
        lines.append("✅ Bo'sh kataklar yo'q — ma'lumot to'liq.")

    if ov["duplicates"] > 0:
        lines.append(
            f"🔁 {ov['duplicates']} ta takrorlangan qator topildi — "
            f"ularni tekshirib chiqing."
        )

    # Raqamli ustunlar bo'yicha asosiy xulosa
    numeric = analysis["numeric"]
    if numeric:
        lines.append("\n**🔢 Asosiy raqamli ko'rsatkichlar:**")
        for col, st in list(numeric.items())[:4]:
            lines.append(
                f"• **{col}**: jami {_fmt(st['sum'])}, o'rtacha {_fmt(st['mean'])}, "
                f"eng yuqori {_fmt(st['max'])}, eng past {_fmt(st['min'])}."
            )

    # Toifalar bo'yicha
    categorical = analysis["categorical"]
    if categorical:
        lines.append("\n**🏷 Toifalar bo'yicha:**")
        for col, st in list(categorical.items())[:3]:
            top = list(st["top_values"].items())
            if top:
                leader, cnt = top[0]
                lines.append(
                    f"• **{col}**: {st['unique']} xil qiymat. Eng ko'p uchragani — "
                    f"\"{leader}\" ({cnt} marta)."
                )

    # Bog'liqliklar
    corr = analysis["correlations"]
    if corr:
        lines.append("\n**🔗 Bog'liqliklar:**")
        for a, b, val in corr[:3]:
            yunalish = "to'g'ri" if val > 0 else "teskari"
            lines.append(
                f"• '{a}' va '{b}' o'rtasida {yunalish} bog'liqlik bor "
                f"(koeffitsiyent {val}). Biri o'zgarsa, ikkinchisi ham o'zgaradi."
            )

    lines.append(
        "\n💡 **Tavsiya:** eng yuqori va eng past ko'rsatkichlarga e'tibor bering — "
        "ular odatda biznesdagi asosiy imkoniyat yoki muammoni ko'rsatadi."
    )

    return "\n".join(lines)


def _build_prompt(analysis):
    """AI'ga yuboriladigan so'rov matnini tayyorlaydi (faqat tahlil natijasi)."""
    context = {
        "overview": analysis["overview"],
        "numeric": analysis["numeric"],
        "categorical": {k: v["top_values"] for k, v in analysis["categorical"].items()},
        "correlations": analysis["correlations"],
    }
    return (
        "Quyida Excel jadvalining avtomatik tahlil natijasi (JSON) berilgan. "
        "Kichik biznes egasi tushunadigan oddiy o'zbek tilida, qisqa va aniq "
        "xulosa yoz. Asosiy ko'rsatkichlarni ayt, e'tibor berish kerak bo'lgan "
        "joylarni ko'rsat va 2-3 ta amaliy tavsiya ber. Markdown ishlat.\n\n"
        f"Tahlil: {context}"
    )


def _key(name):
    """Kalitni avval Streamlit Secrets'dan, keyin muhitdan qidiradi."""
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def ai_summary(df, analysis):
    """
    Bepul AI xulosa (afzal: Groq). Tartib:
      1) GROQ_API_KEY bo'lsa  -> Groq (bepul, Llama 3.3)
      2) ANTHROPIC_API_KEY    -> Claude (pullik, ixtiyoriy)
      3) Hech biri bo'lmasa   -> bepul rule-based xulosa
    """
    prompt = _build_prompt(analysis)

    # --- 1) Groq (BEPUL) ---
    groq_key = _key("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content, "ai"
        except Exception:
            pass  # xato bo'lsa pastdagilarga o'tadi

    # --- 2) Anthropic (ixtiyoriy, pullik) ---
    anthropic_key = _key("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content if b.type == "text")
            return text, "ai"
        except Exception:
            pass

    # --- 3) Bepul rule-based ---
    return rule_based_summary(df, analysis), "rule"
