
import json
from io import BytesIO
from datetime import datetime

import pandas as pd
import numpy as np
import streamlit as st

# ---------------------- 基本設定 ----------------------
st.set_page_config(page_title="📦 保單策略規劃 | 永傳家族傳承教練", page_icon="📦", layout="wide")
st.title("📦 保單策略規劃｜永傳家族傳承教練")
st.caption("為高資產家庭設計最適保障結構，讓每一分資源，都能守護最重要的事。｜聯絡信箱：123@gracefo.com")

# ---------------------- 載入資料 ----------------------
@st.cache_data
def load_products(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # 清理欄位
    for col in ["premium_multiplier_male", "premium_multiplier_female"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(1.0)
    # 年期整數
    if "pay_term_years" in df.columns:
        df["pay_term_years"] = pd.to_numeric(df["pay_term_years"], errors="coerce").astype("Int64")
    # 年齡上下限
    for col in ["min_age", "max_age"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # 預設 JSON 欄位
    if "age_factor_json" in df.columns:
        df["age_factor_json"] = df["age_factor_json"].fillna("")
    else:
        df["age_factor_json"] = ""
    return df

df = load_products("products.csv")

if df.empty:
    st.warning("尚未載入任何商品資料。請先準備 products.csv。")
    st.stop()

# ---------------------- 側邊欄：輸入條件 ----------------------
st.sidebar.header("客戶條件")
gender = st.sidebar.selectbox("性別", ["男", "女"])
age = st.sidebar.number_input("年齡", min_value=0, max_value=100, value=45, step=1)
currency = st.sidebar.selectbox("幣別", ["TWD", "USD"])
pay_term = st.sidebar.selectbox("繳費年期（年）", sorted(df["pay_term_years"].dropna().unique().tolist()))
budget_mode = st.sidebar.selectbox("預算輸入方式", ["年繳", "月繳"])
budget_value = st.sidebar.number_input(f"{budget_mode}預算金額", min_value=0, value=500000 if budget_mode=="年繳" else 40000, step=1000)
budget_yearly = budget_value if budget_mode == "年繳" else budget_value * 12

purposes = st.sidebar.multiselect(
    "保險目的（可複選）",
    ["退休年金", "保障", "傳承", "資產配置", "高現金價值"],
    default=["傳承", "高現金價值"]
)
prefer_big_brand = st.sidebar.checkbox("偏好大型品牌", value=False)
need_high_cash = st.sidebar.checkbox("需要高現金價值", value=True)
scenario = st.sidebar.radio("情境", ["預定利率", "宣告利率"], horizontal=True)

st.sidebar.markdown("---")
st.sidebar.subheader("進階條件（可選）")
irr_floor = st.sidebar.number_input("IRR 下限（％，到 90 歲）", min_value=-5.0, max_value=15.0, value=0.0, step=0.1)
coverage_premium_ceiling = st.sidebar.number_input("保障/保費 比 上限（0 表示不限制）", min_value=0.0, value=0.0, step=0.1)

# ---------------------- 權重設定 ----------------------
st.sidebar.markdown("---")
st.sidebar.subheader("評分權重（合計 100）")
w_fit = st.sidebar.slider("目標適配度", 0, 100, 30)
w_ratio = st.sidebar.slider("保障/保費比", 0, 100, 25)
w_cash = st.sidebar.slider("90 歲解約金", 0, 100, 25)
w_irr  = st.sidebar.slider("IRR", 0, 100, 20)
w_sum = w_fit + w_ratio + w_cash + w_irr
if w_sum != 100:
    st.sidebar.error(f"權重合計需為 100，目前為 {w_sum}。")

# ---------------------- 資料過濾 ----------------------
work = df.copy()
work = work[(work["currency"] == currency)]
work = work[(work["pay_term_years"] == pay_term)]
work = work[(work["min_age"].fillna(0) <= age) & (work["max_age"].fillna(200) >= age)]
if gender == "男":
    gender_key = "M"
    gender_multiplier_col = "premium_multiplier_male"
else:
    gender_key = "F"
    gender_multiplier_col = "premium_multiplier_female"

def apply_age_factor(row, age):
    raw = row.get("age_factor_json", "")
    if not raw:
        return 1.0
    try:
        mapping = json.loads(raw)
    except Exception:
        return 1.0
    # key 形式 "40-49": 1.1
    for k, v in mapping.items():
        try:
            a, b = k.split("-")
            a, b = int(a), int(b)
            if a <= age <= b:
                return float(v)
        except Exception:
            continue
    return 1.0

# 年繳保費估算
work["annual_premium"] = (
    pd.to_numeric(work.get("annual_premium_base", 0), errors="coerce").fillna(0)
    * pd.to_numeric(work.get(gender_multiplier_col, 1.0), errors="coerce").fillna(1.0)
    * work.apply(lambda r: apply_age_factor(r, age), axis=1)
).round(0)
work["total_premium"] = (work["annual_premium"] * work["pay_term_years"]).round(0)

# 預算過濾（允許 +10% 彈性）
budget_upper = budget_yearly * 1.10
work = work[work["annual_premium"] <= budget_upper]

# 性別支援過濾
def gender_ok(v):
    v = str(v).upper()
    return v in ("ANY", "") or gender_key in v

work = work[work["gender_limit"].apply(gender_ok)]

# 指標選擇（情境切換）
cash_col  = "cash_value_90_predicted" if scenario == "預定利率" else "cash_value_90_declared"
death_col = "death_benefit_90_predicted" if scenario == "預定利率" else "death_benefit_90_declared"
irr_col   = "irr_to_90_predicted" if scenario == "預定利率" else "irr_to_90_declared"

for col in [cash_col, death_col, irr_col]:
    if col not in work.columns:
        work[col] = np.nan
    work[col] = pd.to_numeric(work[col], errors="coerce")

# 衍生指標
work["coverage_premium_ratio"] = work[death_col] / work["total_premium"]
work["irr_pct"] = work[irr_col] * 100.0

# 進階過濾
if irr_floor:
    work = work[work["irr_pct"].fillna(-999) >= irr_floor]
if coverage_premium_ceiling and coverage_premium_ceiling > 0:
    work = work[work["coverage_premium_ratio"].fillna(0) <= coverage_premium_ceiling]

if work.empty:
    st.warning("沒有符合條件的商品。建議：放寬預算、切換幣別或調整年期與權重後重試。")
    st.stop()

# 目標適配度：以 tags 與 highlight 關鍵詞粗略評分
def fit_score(row):
    tags = str(row.get("tags", "")).split(",")
    text = " ".join(tags) + " " + str(row.get("highlight", ""))
    score = 0
    for p in purposes:
        if p in text:
            score += 1
    if need_high_cash and "高現金價值" in text:
        score += 1
    if prefer_big_brand and ("大" in text or "旗艦" in text):
        score += 1
    # 歸一（最多 5 分 → 0~1）
    return min(score, 5) / 5.0

work["fit_norm"] = work.apply(fit_score, axis=1)

# 數值指標正規化（同幣別＆年期群組）
def minmax(s):
    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return None
    lo, hi = s.min(), s.max()
    if hi == lo:
        return None
    return (lo, hi)

mm_cash = minmax(work[cash_col])
mm_ratio = minmax(work["coverage_premium_ratio"])

def norm_val(v, mm):
    if mm is None or pd.isna(v):
        return 0.0
    lo, hi = mm
    return float((v - lo) / (hi - lo)) if hi > lo else 0.0

work["cash_norm"] = work[cash_col].apply(lambda v: norm_val(v, mm_cash))
work["ratio_norm"] = work["coverage_premium_ratio"].apply(lambda v: norm_val(v, mm_ratio))
work["irr_norm"] = work["irr_pct"].fillna(-999)
# IRR 直接用百分比映射到 0~1（-5%~15% 範圍）
work["irr_norm"] = work["irr_norm"].clip(-5, 15).apply(lambda x: (x + 5) / 20.0)

# 綜合分數（0~100）
work["score"] = (
    work["fit_norm"]  * w_fit +
    work["ratio_norm"]* w_ratio +
    work["cash_norm"] * w_cash  +
    work["irr_norm"]  * w_irr
).round(2)

# 排序
work = work.sort_values(["score", cash_col, "coverage_premium_ratio"], ascending=[False, False, False])

# ---------------------- 推薦區塊 ----------------------
st.subheader("🔎 系統推薦（Top 3）")
top3 = work.head(3).copy()

def reason_row(r):
    rs = []
    if r["fit_norm"] >= 0.8:
        rs.append("高度符合目標條件")
    if r["ratio_norm"] >= 0.7:
        rs.append("保障/保費比表現佳")
    if r["cash_norm"] >= 0.7:
        rs.append("長期現金價值較高")
    if (r.get("highlight") or "").strip():
        rs.append(str(r["highlight"]).strip())
    return "；".join(rs[:3]) if rs else "整體指標均衡表現"

cols = st.columns(3)
for i, (_, r) in enumerate(top3.iterrows()):
    with cols[i]:
        st.metric(f"{r['company']}｜{r['product_name']}", f"分數 {r['score']}")
        st.caption(reason_row(r))

# ---------------------- 結果表格 ----------------------
st.subheader("📊 商品比較")
display_cols = [
    "company","product_name","currency","pay_term_years","annual_premium","total_premium",
    cash_col, death_col, "coverage_premium_ratio","irr_pct","highlight"
]
rename = {
    "company":"公司","product_name":"商品","currency":"幣別","pay_term_years":"年期",
    "annual_premium":"年繳保費","total_premium":"總繳保費",
    cash_col:"90歲解約金", death_col:"90歲身故理賠",
    "coverage_premium_ratio":"保障/保費比","irr_pct":"IRR(%)","highlight":"亮點"
}
table = work[display_cols].rename(columns=rename).copy()
# 千分位格式化
for c in ["年繳保費","總繳保費","90歲解約金","90歲身故理賠"]:
    table[c] = table[c].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "-")
table["保障/保費比"] = work["coverage_premium_ratio"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "-")
table["IRR(%)"] = work["irr_pct"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

st.dataframe(table, use_container_width=True, height=420)

# ---------------------- 匯出區 ----------------------
st.markdown("### ⬇ 下載")
csv_bytes = work.to_csv(index=False).encode("utf-8-sig")
st.download_button("下載篩選結果（CSV）", data=csv_bytes, file_name="recommendations.csv", mime="text/csv")

# 簡易 PDF（使用 reportlab，如環境未安裝則提示）
if st.button("匯出精簡報告（PDF）"):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        W, H = A4

        # 頁眉
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20*mm, (H-20*mm), "保險商品推薦報告｜永傳家族傳承教練")
        c.setFont("Helvetica", 9)
        c.drawRightString(W-20*mm, (H-20*mm), datetime.now().strftime("%Y-%m-%d %H:%M"))

        # 客戶條件
        y = H - 32*mm
        c.setFont("Helvetica", 10)
        cond = f"條件：{gender}／{int(age)}歲／{currency}／{pay_term}年期／年預算≤{int(budget_yearly):,}"
        c.drawString(20*mm, y, cond); y -= 8*mm

        # Top 3
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20*mm, y, "系統推薦 Top 3"); y -= 6*mm
        c.setFont("Helvetica", 10)
        for _, r in top3.iterrows():
            line = f"- {r['company']}｜{r['product_name']}｜分數 {r['score']}｜亮點：{str(r.get('highlight') or '')[:40]}"
            c.drawString(20*mm, y, line[:95]); y -= 6*mm
        y -= 4*mm

        # 表格（精簡前 6 筆）
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20*mm, y, "精簡比較（前 6 筆）"); y -= 6*mm
        c.setFont("Helvetica", 9)
        header = ["公司","商品","年期","年繳","總繳","90歲解約","90歲身故","IRR%"]
        widths = [26,40,10,22,22,26,26,10]
        x0 = 20*mm
        def draw_row(vals, y):
            x = x0
            for val, w in zip(vals, widths):
                c.drawString(x, y, str(val)[:int(w)])
                x += w*mm

        draw_row(header, y); y -= 5*mm
        for _, r in work.head(6).iterrows():
            vals = [
                r["company"],
                r["product_name"],
                int(r["pay_term_years"]),
                f"{int(r['annual_premium']):,}",
                f"{int(r['total_premium']):,}",
                f"{int(r[cash_col]) if not pd.isna(r[cash_col]) else 0:,}",
                f"{int(r[death_col]) if not pd.isna(r[death_col]) else 0:,}",
                f"{float(r['irr_pct']):.2f}" if not pd.isna(r["irr_pct"]) else "-",
            ]
            draw_row(vals, y); y -= 5*mm
            if y < 20*mm:
                c.showPage(); y = H - 20*mm

        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()

        st.download_button(
            "下載 PDF 報告",
            data=pdf_bytes,
            file_name=f"Insurance_Recommendation_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error("目前環境未安裝 reportlab，或 PDF 產生失敗。請先在 requirements.txt 加入 reportlab 再部署。")

st.caption("© 永傳家族辦公室｜本工具僅供教育與比較參考，實際保障與數據以保險公司保單條款與試算為準。")
