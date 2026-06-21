"""
PDF 浮水印工具 - Streamlit App
上傳 PDF → 設定浮水印 → 預覽 → 下載含浮水印的 PDF
"""

import io
import os
import platform
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="PDF 浮水印工具",
    page_icon="📄",
    layout="wide",
)

st.title("📄 PDF 浮水印工具")
st.divider()

# 自動偵測系統合適的中文字型
def get_system_font(font_size):
    sys_plat = platform.system()
    font_paths = {
        "Windows": "C:\\Windows\\Fonts\\msjh.ttc",
        "Darwin": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "Linux": "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    }
    font_path = font_paths.get(sys_plat, "")
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None

# Sidebar controls
with st.sidebar:
    st.markdown("### 浮水印設定")

    wm_text = st.text_area(
        "浮水印文字",
        value="機密文件",
        placeholder="輸入浮水印文字…",
        help="支援多行",
    )

    st.markdown("---")
    st.markdown("#### 字體大小")
    font_size = st.slider("", 12, 120, 48, key="fs")

    st.markdown("#### 透明度")
    opacity = st.slider("", 5, 100, 20, key="op")

    st.markdown("#### 旋轉角度")
    rotation = st.slider("", -90, 90, -30, key="rot")

    st.markdown("#### 浮水印顏色")
    color_options = {
        "灰色": "#888888",
        "紅色": "#cc4444",
        "藍色": "#4466cc",
        "綠色": "#44aa66",
        "黑色": "#333333",
        "白色": "#ffffff",
    }
    selected_color_label = st.selectbox("選擇顏色", list(color_options.keys()), index=0)
    wm_color = color_options[selected_color_label]

    st.markdown("---")

# File upload
st.markdown("### 上傳 PDF")
uploaded_file = st.file_uploader("選擇 PDF 檔案（拖放或點擊上傳）", type=["pdf"])

# Initialize session state
for key, val in [("pdf_bytes", None), ("page_count", 0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# Load PDF
if uploaded_file is not None:
    st.session_state.pdf_bytes = uploaded_file.getvalue()
    doc_temp = fitz.open(stream=st.session_state.pdf_bytes)
    st.session_state.page_count = doc_temp.page_count
    doc_temp.close()
    st.success(f"已載入：{uploaded_file.name}（{st.session_state.page_count} 頁）")

# Preview
if st.session_state.pdf_bytes and wm_text.strip():
    st.markdown("### 預覽（浮水印效果）")

    try:
        doc = fitz.open(stream=st.session_state.pdf_bytes)
        page = doc[0]
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        preview_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        img_font = get_system_font(font_size)

        r = int(wm_color[1:3], 16)
        g = int(wm_color[3:5], 16)
        b_val = int(wm_color[5:7], 16)
        alpha = opacity / 100

        wm_img = Image.new("RGBA", preview_img.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_img, "RGBA")
        cx, cy = preview_img.width // 2, preview_img.height // 2

        lines = wm_text.strip().split("\n")
        line_h = font_size + 8
        total_h = len(lines) * line_h
        start_y = cy - total_h // 2

        for i, line in enumerate(lines):
            try:
                bbox = wm_draw.textbbox((0, 0), line, font=img_font)
                text_w = bbox[2] - bbox[0]
            except AttributeError:
                text_w = font_size * len(line) // 2

            wm_draw.text(
                (cx - text_w // 2, start_y + i * line_h),
                line,
                font=img_font,
                fill=(r, g, b_val, int(255 * alpha))
            )

        if rotation != 0:
            wm_img = wm_img.rotate(
                -rotation, center=(cx, cy), expand=0, fillcolor=(0, 0, 0, 0)
            )

        preview_img = preview_img.convert("RGBA")
        preview_img = Image.alpha_composite(preview_img, wm_img).convert("RGB")

        buf = io.BytesIO()
        preview_img.save(buf, format="PNG")
        buf.seek(0)

        st.image(
            buf,
            caption=f"第 1 頁預覽（共 {st.session_state.page_count} 頁）",
            use_container_width=True
        )
        doc.close()

    except Exception as e:
        st.error(f"預覽失敗：{e}")

elif st.session_state.pdf_bytes and not wm_text.strip():
    st.info("請輸入浮水印文字")

elif not st.session_state.pdf_bytes:
    st.info("上傳 PDF 檔案後開始設定浮水印")

# Download
if st.session_state.pdf_bytes and wm_text.strip():
    st.divider()

    if st.button("⬇️ 下載含浮水印的 PDF", type="primary", use_container_width=True):
        with st.spinner("處理中…"):

            try:
                doc = fitz.open(stream=st.session_state.pdf_bytes)

                r = int(wm_color[1:3], 16)
                g = int(wm_color[3:5], 16)
                b_val = int(wm_color[5:7], 16)

                for page in doc:
                    w = page.rect.width
                    h = page.rect.height
                    page.insert_text(
                        (w / 2, h / 2),
                        wm_text,
                        fontsize=font_size,
                        color=(r/255, g/255, b_val/255),
                        opacity=opacity / 100,
                        rotation=rotation,
                        align=1,
                    )

                out_bytes = doc.tobytes()
                doc.close()

                st.success("浮水印 PDF 已產生！")

                st.download_button(
                    label="📥 點此下載浮水印 PDF",
                    data=out_bytes,
                    file_name="watermarked.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            except Exception as e:
                st.error(f"處理失敗：{e}")

st.divider()
st.caption("預覽僅供參考，實際輸出效果以下載的 PDF 為準")