"""
PDF 浮水印工具 + 圖片浮水印工具
"""

import io, os, platform
import streamlit as st
import fitz
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="浮水印工具", page_icon="📄", layout="wide")
st.title("📄 浮水印工具")
st.divider()

# ── 找中文字型 ──
def get_font(size):
    bundled = os.path.join(os.path.dirname(__file__), "msjh.ttc")
    if os.path.exists(bundled):
        try:
            return ImageFont.truetype(bundled, size)
        except Exception:
            pass
    sys_plat = platform.system()
    paths = {
        "Linux": [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "Windows": [
            "C:\\Windows\\Fonts\\msjh.ttc",
            "C:\\Windows\\Fonts\\simsun.ttc",
            "C:\\Windows\\Fonts\\mingliu.ttc",
        ],
        "Darwin": [
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ],
    }
    for p in paths.get(sys_plat, []):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None

# ── 共用浮水印參數 ──
with st.sidebar:
    st.markdown("### 浮水印設定")
    mode = st.radio("浮水印類型", ["PDF 浮水印", "圖片浮水印"], horizontal=True, key="mode")

    wm_text = st.text_area("浮水印文字", value="機密文件", placeholder="輸入浮水印文字…", key="wm_text")

    st.markdown("#### 字體大小")
    font_size = st.slider("", 12, 120, 48, key="fs")

    st.markdown("#### 透明度")
    opacity = st.slider("", 5, 100, 25, key="op")

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
    wm_color = color_options[st.selectbox("選擇顏色", list(color_options.keys()), index=0)]

    st.markdown("---")

# ──  Helper：製作浮水印 PIL Image ──
def make_watermark_pil(text, size, alpha_val, rot, color_hex, page_w, page_h):
    """傳回一個 RGBA PIL Image（浮水印在透明背景上）"""
    img_font = get_font(size)
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)

    # 建立足夠大的透明畫布（旋轉 expand 用）
    canvas_size = max(page_w, page_h) * 2
    wm = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wm)
    cx, cy = canvas_size // 2, canvas_size // 2

    lines = text.strip().split("\n")
    line_h = size + 8
    total_h = len(lines) * line_h
    start_y = cy - total_h // 2

    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=img_font)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw = size * len(line) // 2
        draw.text((cx - tw // 2, start_y + i * line_h), line, font=img_font, fill=(r, g, b, int(255 * alpha_val)))

    if rot != 0:
        wm = wm.rotate(rot, center=(cx, cy), expand=0, fillcolor=(0, 0, 0, 0))

    return wm

# ══════════════════════════════════════════
#  PDF 浮水印模式
# ══════════════════════════════════════════
if mode == "PDF 浮水印":
    st.markdown("### 上傳 PDF")
    uploaded_file = st.file_uploader("選擇 PDF 檔案", type=["pdf"])

    for k, v in [("pdf_bytes", None), ("pdf_page_count", 0)]:
        if k not in st.session_state:
            st.session_state[k] = v

    if uploaded_file:
        st.session_state.pdf_bytes = uploaded_file.getvalue()
        doc_temp = fitz.open(stream=st.session_state.pdf_bytes)
        st.session_state.pdf_page_count = doc_temp.page_count
        doc_temp.close()
        st.success(f"已載入：{uploaded_file.name}（{st.session_state.pdf_page_count} 頁）")

    # Preview
    if st.session_state.pdf_bytes and wm_text.strip():
        st.markdown("### 預覽")
        try:
            doc = fitz.open(stream=st.session_state.pdf_bytes)
            page = doc[0]
            mat = fitz.Matrix(1.5, 1.5)
            pix = page.get_pixmap(matrix=mat)
            preview = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            alpha_val = opacity / 100
            wm_pil = make_watermark_pil(wm_text, font_size, alpha_val, rotation, wm_color, pix.width, pix.height)

            # 疊加到預覽
            preview = preview.convert("RGBA")
            wm_pil = wm_pil.resize((preview.width, preview.height), Image.LANCZOS)
            preview = Image.alpha_composite(preview, wm_pil).convert("RGB")

            buf = io.BytesIO()
            preview.save(buf, "PNG")
            buf.seek(0)
            st.image(buf, caption=f"第 1 頁預覽（共 {st.session_state.pdf_page_count} 頁）", use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"預覽失敗：{e}")

    elif st.session_state.pdf_bytes and not wm_text.strip():
        st.info("請輸入浮水印文字")
    elif not st.session_state.pdf_bytes:
        st.info("上傳 PDF 檔案後開始")

    # Download
    if st.session_state.pdf_bytes and wm_text.strip():
        st.divider()
        if st.button("⬇️ 下載含浮水印的 PDF", type="primary", use_container_width=True):
            with st.spinner("處理中…"):
                try:
                    doc = fitz.open(stream=st.session_state.pdf_bytes)
                    alpha_val = opacity / 100

                    for page in doc:
                        w = int(page.rect.width)
                        h = int(page.rect.height)

                        # 用 PIL 做透明浮水印圖，再寫入 PDF
                        wm_pil = make_watermark_pil(wm_text, font_size, alpha_val, rotation, wm_color, w, h)
                        wm_buf = io.BytesIO()
                        wm_pil.save(wm_buf, "PNG")
                        wm_buf.seek(0)

                        # 置中放進 PDF（img 會墊在文字底下）
                        page.insert_image(
                            (w // 2 - wm_pil.width // 2, h // 2 - wm_pil.height // 2),
                            filename=wm_buf,
                            keep_proportion=False,
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

# ══════════════════════════════════════════
#  圖片浮水印模式
# ══════════════════════════════════════════
else:
    st.markdown("### 上傳圖片")
    img_file = st.file_uploader("選擇圖片檔案（支援 JPG / PNG / WebP / GIF）", type=["jpg", "jpeg", "png", "webp", "gif"])

    if img_file:
        try:
            orig = Image.open(img_file).convert("RGB")
            st.success(f"已載入：{img_file.name}（{orig.width}×{orig.height}）")

            # Preview with watermark
            alpha_val = opacity / 100
            wm_pil = make_watermark_pil(wm_text, font_size, alpha_val, rotation, wm_color, orig.width, orig.height)

            result = orig.convert("RGBA")
            result = Image.alpha_composite(result, wm_pil).convert("RGB")

            buf = io.BytesIO()
            result.save(buf, "PNG")
            buf.seek(0)
            st.markdown("### 預覽")
            st.image(buf, use_container_width=True)

            # Download
            if st.button("⬇️ 下載浮水印圖片", type="primary", use_container_width=True):
                out_buf = io.BytesIO()
                # 輸出格式與原圖一致
                fmt = "PNG" if img_file.type == "image/png" else "JPEG"
                result.save(out_buf, format=fmt, quality=95)
                out_buf.seek(0)
                ext = "png" if fmt == "PNG" else "jpg"
                st.download_button(
                    label="📥 點此下載",
                    data=out_buf,
                    file_name=f"watermarked.{ext}",
                    mime="image/png" if fmt == "PNG" else "image/jpeg",
                    use_container_width=True,
                )

        except Exception as e:
            st.error(f"處理失敗：{e}")
    else:
        st.info("上傳圖片後開始設定浮水印")

st.divider()
st.caption("預覽僅供參考，實際輸出效果以下載的檔案為準")