
# 保險商品推薦工具（Streamlit MVP）

這是一個面向保險經紀人的快速原型：輸入客戶條件 → 自動比對多家商品 → 產生排序與推薦 → 匯出精簡 PDF 報告。

## 本地執行
1. 安裝套件：`pip install -r requirements.txt`
2. 啟動：`streamlit run app.py`
3. 以 `products.csv` 放在同目錄下作為資料來源（可自行替換/擴充）。

## 檔案說明
- `app.py`：主程式（中文介面）。
- `products.csv`：示例商品 10 筆。
- `requirements.txt`：必要套件。
- `README.md`：說明文件。

## 注意
- 所有數據僅為示例，請以實際保險公司條款與試算為準。
- 可於側邊欄調整權重、條件與情境（預定/宣告）。
