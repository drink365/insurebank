
# 保險商品推薦工具（Streamlit MVP）

面向保險經紀人的原型：輸入客戶條件 → 自動比對多家商品 → 排序與推薦 → 匯出精簡 PDF 報告。

## 本地執行
1. 安裝套件：`pip install -r requirements.txt`
2. 啟動：`streamlit run app.py`
3. `products.csv` 放在同目錄作為資料來源（可自行替換/擴充）。

## 部署到 Streamlit Cloud
1. 將專案整包上傳到 GitHub（根目錄需包含：`app.py`、`products.csv`、`requirements.txt`、`runtime.txt`）。
2. 在 Streamlit Cloud 建立新 App，指向該 repo，主檔案 `app.py`。
3. Cloud 會讀取 `runtime.txt` → 使用 Python 3.11，自動安裝 `requirements.txt`。
4. 成功後即可分享公開連結給客戶或團隊。

## 欄位說明（products.csv，必要）
- `company, product_name, currency(TWD|USD), pay_term_years`
- 推薦加上：`annual_premium_base, premium_multiplier_male, premium_multiplier_female, age_factor_json`
- 結果比較指標：`cash_value_90_predicted/declared, death_benefit_90_predicted/declared, irr_to_90_predicted/declared`

> 若未提供某些欄位，系統會自動以空值處理；`annual_premium` 與 `total_premium` 會由系統推算。

## 注意
- 所有示例數據僅供展示；實際保障與數據以保險公司條款與試算為準。
- 可於側邊欄調整權重、條件與情境（預定/宣告）。
