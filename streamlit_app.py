"""
PDF 浮水印工具 - Streamlit App
功能：上傳 PDF → 設定浮水印參數 → 預覽 → 下載含浮水印的 PDF
"""

import io
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="PDF 浮水印工具",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ──
st.markdown("""
<style>
  .main-header {
    font-size: 1.6rem;
    font-weight: 700;
    color: #4a6fa5;
    letter-spacing: 0.02em;
  }
  .stApp > header {
    background: #f5f3ef;
    border-bottom: 1px solid #e2ddd6;
  }
  .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📄 PDF 浮水印工具</div>', unsafe_allow_html=True)
st.divider()

# ── Sidebar controls ──
with st.sidebar:
    st.markdown("### ⚙️ 浮水印設定")

    wm_text = st.text_area(
        "浮水印文字",
        value="機密文件",
        placeholder="輸入浮水印文字…",
        help="支援多行文字，每行獨立浮水印",
    )

    st.markdown("---")
    st.markdown("#### 字體大小")
    font_size = st.slider("", 12, 120, 48, help="字體大小（px）", key="fs")

    st.markdown("#### 透明度")
    opacity = st.slider("", 5, 100, 20, help="浮水印透明度（%）", key="op")

    st.markdown("#### 旋轉角度")
    rotation = st.slider("", -90, 90, -30, help="浮水印旋轉角度", key="rot")

    st.markdown("#### 浮水印顏色")
    color_options = {
        "灰色": "#888888",
        "紅色": "#cc4444",
        "藍色": "#4466cc",
        "綠色": "#44aa66",
        "黑色": "#333333",
        "白色": "#ffffff",
    }
    selected_color_label = st.selectbox("選擇顏色", list(color_options.keys()), index=0, key="color_sel")
    wm_color = color_options[selected_color_label]

    color_div = (
        '<div style="display:flex;align-items:center;gap:8px;margin-top:4px;">'
        '<div style="width:24px;height:24px;background:{color};"'
        'style="border-radius:4px;border:1px solid #e2ddd6;"></div>'
        '<span style="font-size:12px;color:#7a756e;">{color}</span>'
        '</div>'
    )
    st.markdown(color_div.format(color=wm_color), unsafe_allow_html=True)

    st.markdown("---")

# ── File upload ──
st.markdown("### 📂 上傳 PDF")
uploaded_file = st.file_uploader(
    "選擇 PDF 檔案",
    type=["pdf"],
    help="拖放或點擊上傳",
)

# ── State management ──
for key, val in [
    ("pdf_bytes", None),
    ("page_count", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Load PDF ──
if uploaded_file is not None:
    st.session_state.pdf_bytes = uploaded_file.getvalue()
    doc_temp = fitz.open(stream=st.session_state.pdf_bytes)
    st.session_state.page_count = doc_temp.page_count
    doc_temp.close()
    st.success(f"已載入：{uploaded_file.name}（{st.session_state.page_count} 頁）")

# ── Preview ──
if st.session_state.pdf_bytes and wm_text.strip():
    st.markdown("### 🖼️ 預覽（浮水印效果）")

    try:
        doc = fitz.open(stream=st.session_state.pdf_bytes)
        page = doc[0]
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        preview_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Draw watermark
        try:
            img_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            img_font = ImageFont.load_default()

        wm_img = Image.new("RGBA", preview_img.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_img, "RGBA")

        cx = preview_img.width // 2
        cy = preview_img.height // 2

        r = int(wm_color[1:3], 16)
        g = int(wm_color[3:5], 16)
        b_val = int(wm_color[5:7], 16)
        alpha = opacity / 100

        lines = wm_text.strip().split("\n")
        line_h = font_size + 8
        total_h = len(lines) * line_h
        start_y = cy - total_h // 2

        for i, line in enumerate(lines):
            line_y = start_y + i * line_h
            wm_draw.text(
                (cx - preview_img.width // 4, line_y),
                line,
                font=img_font,
                fill=(r, g, b_val, int(255 * alpha))
            )

        if rotation != 0:
            wm_img = wm_img.rotate(-rotation, center=(cx, cy), expand=1, fillcolor=(0, 0, 0, 0))

        preview_img = preview_img.convert("RGBA")
        preview_img = Image.alpha_composite(preview_img, wm_img)
        preview_img = preview_img.convert("RGB")

        buf = io.BytesIO()
        preview_img.save(buf, format="PNG")
        buf.seek(0)

        st.image(buf, caption=f"第 1 頁預覽（共 {st.session_state.page_count} 頁）", use_container_width=True)
        doc.close()

    except Exception as e:
        st.error(f"預覽失敗：{e}")

elif st.session_state.pdf_bytes and not wm_text.strip():
    st.info("請輸入浮水印文字")

elif not st.session_state.pdf_bytes:
    st.info("👆 上傳 PDF 檔案後開始設定浮水印")

# ── Download ──
if st.session_state.pdf_bytes and wm_text.strip():
    st.divider()

    if st.button("⬇️ 下載含浮水印的 PDF", type="primary", use_container_width=True):
        with st.spinner("處理中，請稍候…"):

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

# ── Footer ──
st.divider()
st.caption("預覽僅供參考，實際輸出效果以下載的 PDF 為準")