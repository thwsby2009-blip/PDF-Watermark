# PDF 浮水印工具

上傳 PDF 或圖片，自動加上文字浮水印。支援字體大小、透明度、旋轉角度、顏色調整，即時預覽後下載。

**線上版：** https://thwsby2009-blip.streamlit.app

---

## 功能

### PDF 浮水印
- 上傳 PDF 檔案
- 輸入浮水印文字（預設「機密文件」）
- 調整字體大小、透明度、旋轉角度、顏色
- 預覽第 1 頁效果
- 一鍵下載含浮水印的 PDF

### 圖片浮水印
- 上傳圖片（JPG / PNG / WebP / GIF）
- 同一組浮水印設定
- 即時預覽效果
- 一鍵下載浮水印圖片

### 可調整參數

| 參數 | 範圍 | 說明 |
|------|------|------|
| 字體大小 | 12–120 | 浮水印文字大小 |
| 透明度 | 5–100% | 浮水印顯色程度 |
| 旋轉角度 | -90°–90° | 浮水印傾斜程度 |
| 顏色 | 6 種 | 浮水印文字顏色 |

---

## 使用方式

**線上直接用：**
1. 前往 https://thwsby2009-blip.streamlit.app
2. 選擇「PDF 浮水印」或「圖片浮水印」
3. 上傳檔案，調整設定，預覽
4. 下載完成

**本地運行：**
```bash
git clone https://github.com/thwsby2009-blip/PDF-Watermark.git
cd PDF-Watermark
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## 技術

- **框架**：Streamlit（Python）
- **PDF 處理**：PyMuPDF（fitz）
- **圖片處理**：Pillow（PIL）
- **中文字型**：內建微軟正黑體（msjh.ttc）

## 注意事項

- 預覽僅供參考，實際輸出以下載檔案為準
- 大量頁面 PDF 處理可能需數秒
- 中文字型已內建，無需另外安裝