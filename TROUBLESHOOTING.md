
# 疑難排解

## 1) 卡在「baking in the oven」
- 在專案根目錄加入 `runtime.txt`，內容：`3.11`
- 使用這組相容的 `requirements.txt`：
  ```
  streamlit==1.36.0
  pandas==2.2.2
  numpy==1.26.4
  reportlab==4.2.0
  ```

## 2) KeyError: 'total_premium'
- 使用本專案的 `app.py`（已自動建立 `annual_premium` 與 `total_premium`）。
- 確認 `products.csv` 有 `pay_term_years`、`annual_premium_base` 等欄位。

## 3) PDF 下載按鈕不出現
- 代表 `reportlab` 未安裝或產生 PDF 失敗；請確認雲端有依 `requirements.txt` 安裝。
