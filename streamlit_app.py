"""
PDF 浮水印工具 - Streamlit App
支援文字浮水印、圖片浮水印
"""

import io
import os
import platform
import streamlit as st
import fitz
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="PDF 浮水印工具",
    page_icon="📄",
    layout="wide",
)

st.title("📄 PDF 浮水印工具")
st.divider()

# ── Helpers ──
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

# ── Sidebar controls ──
wm_text = ""
wm_color = "#888888"
font_size = 48
opacity = 20
rotation = -30
wm_image = None
img_width = 200

with st.sidebar:
    st.markdown("### 浮水印設定")

    wm_type = st.radio(
        "浮水印類型",
        ["文字浮水印", "圖片浮水印"],
        horizontal=True,
    )

    st.markdown("---")

    # ── Text watermark controls ──
    if wm_type == "文字浮水印":
        wm_text = st.text_area(
            "浮水印文字",
            value="機密文件",
            placeholder="輸入浮水印文字…",
            help="支援多行",
            key="wm_text",
        )

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
        selected_color_label = st.selectbox(
            "選擇顏色", list(color_options.keys()), index=0, key="color_sel"
        )
        wm_color = color_options[selected_color_label]

    # ── Image watermark controls ──
    else:
        wm_image = st.file_uploader(
            "上傳浮水印圖片",
            type=["png", "jpg", "jpeg", "svg", "webp"],
            help="支援 PNG / JPG / SVG / WebP，建議使用透明背景 PNG",
            key="wm_image",
        )

        if wm_image:
            img_data = Image.open(wm_image)
            st.image(img_data, caption="浮水印圖片預覽", width=160)

        st.markdown("#### 圖片寬度")
        img_width = st.slider("", 50, 800, 200, key="img_w")

        st.markdown("#### 透明度")
        opacity = st.slider("", 5, 100, 30, key="op_img")

        st.markdown("#### 旋轉角度")
        rotation = st.slider("", -90, 90, -30, key="rot_img")

    st.markdown("---")

# ── File upload ──
st.markdown("### 上傳 PDF")
uploaded_file = st.file_uploader(
    "選擇 PDF 檔案（拖放或點擊上傳）",
    type=["pdf"]
)

# ── Session state ──
for key, val in [("pdf_bytes", None), ("page_count", 0)]:
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
if st.session_state.pdf_bytes:
    text_ok = wm_type == "文字浮水印" and bool(wm_text and wm_text.strip())
    img_ok = wm_type == "圖片浮水印" and (wm_image is not None)

    if text_ok or img_ok:
        st.markdown("### 預覽（浮水印效果）")

        try:
            doc = fitz.open(stream=st.session_state.pdf_bytes)
            page = doc[0]
            mat = fitz.Matrix(1.5, 1.5)
            pix = page.get_pixmap(matrix=mat)
            preview_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            if wm_type == "文字浮水印":
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
                        fill=(r, g, b_val, int(255 * alpha)),
                    )

                if rotation != 0:
                    wm_img = wm_img.rotate(
                        -rotation, center=(cx, cy), expand=0, fillcolor=(0, 0, 0, 0)
                    )

                preview_img = preview_img.convert("RGBA")
                preview_img = Image.alpha_composite(preview_img, wm_img).convert("RGB")

            else:  # Image watermark
                alpha = opacity / 100
                wm_img_raw = Image.open(wm_image).convert("RGBA")

                # Scale image to target width
                ratio = wm_img_raw.height / wm_img_raw.width
                new_w = img_width
                new_h = int(new_w * ratio)
                wm_img_resized = wm_img_raw.resize((new_w, new_h), Image.LANCZOS)

                # Apply opacity
                alpha_layer = Image.new("L", wm_img_resized.size, int(255 * alpha))
                wm_img_resized.putalpha(alpha_layer)

                # Rotate
                if rotation != 0:
                    wm_img_resized = wm_img_resized.rotate(
                        -rotation, expand=0, fillcolor=(0, 0, 0, 0)
                    )

                # Paste onto preview centered
                px = (preview_img.width - wm_img_resized.width) // 2
                py = (preview_img.height - wm_img_resized.height) // 2
                preview_img = preview_img.convert("RGBA")
                preview_img.paste(wm_img_resized, (px, py), wm_img_resized)
                preview_img = preview_img.convert("RGB")

            buf = io.BytesIO()
            preview_img.save(buf, format="PNG")
            buf.seek(0)

            st.image(
                buf,
                caption=f"第 1 頁預覽（共 {st.session_state.page_count} 頁）",
                use_container_width=True,
            )
            doc.close()

        except Exception as e:
            st.error(f"預覽失敗：{e}")

    elif not text_ok and not img_ok:
        hint = (
            "請輸入浮水印文字" if wm_type == "文字浮水印"
            else "請上傳浮水印圖片"
        )
        st.info(hint)

elif not st.session_state.pdf_bytes:
    st.info("上傳 PDF 檔案後開始設定浮水印")

# ── Download ──
if st.session_state.pdf_bytes:
    text_ok = wm_type == "文字浮水印" and bool(wm_text and wm_text.strip())
    img_ok = wm_type == "圖片浮水印" and (wm_image is not None)

    if text_ok or img_ok:
        st.divider()

        label = (
            "⬇️ 下載含浮水印的 PDF"
            if wm_type == "文字浮水印"
            else "⬇️ 下載含圖片浮水印的 PDF"
        )

        if st.button(label, type="primary", use_container_width=True):
            with st.spinner("處理中…"):

                try:
                    doc = fitz.open(stream=st.session_state.pdf_bytes)

                    for page in doc:
                        w = page.rect.width
                        h = page.rect.height
                        cx = w / 2
                        cy = h / 2

                        if wm_type == "文字浮水印":
                            r = int(wm_color[1:3], 16)
                            g = int(wm_color[3:5], 16)
                            b_val = int(wm_color[5:7], 16)
                            page.insert_text(
                                (cx, cy),
                                wm_text,
                                fontsize=font_size,
                                color=(r/255, g/255, b_val/255),
                                opacity=opacity / 100,
                                rotation=rotation,
                                align=1,
                            )

                        else:  # Image watermark
                            img_pil = Image.open(wm_image).convert("RGBA")
                            ratio = img_pil.height / img_pil.width
                            new_w = img_width
                            new_h = int(new_w * ratio)
                            img_pil = img_pil.resize((new_w, new_h), Image.LANCZOS)

                            # Apply opacity
                            alpha_layer = Image.new("L", img_pil.size, int(255 * opacity / 100))
                            img_pil.putalpha(alpha_layer)

                            # Save to bytes
                            img_buf = io.BytesIO()
                            img_pil.save(img_buf, format="PNG")
                            img_buf.seek(0)

                            page.insert_image(
                                (cx - new_w / 2, cy - new_h / 2),
                                width=new_w,
                                height=new_h,
                                filename=img_buf,
                                rotate=rotation,
                                opacity=opacity / 100,
                            )

                    out_bytes = doc.tobytes()
                    doc.close()

                    st.success("浮水印 PDF 已產生！")

                    fname = (
                        "watermarked.pdf"
                        if wm_type == "文字浮水印"
                        else "watermarked_image.pdf"
                    )

                    st.download_button(
                        label="📥 點此下載",
                        data=out_bytes,
                        file_name=fname,
                        mime="application/pdf",
                        use_container_width=True,
                    )

                except Exception as e:
                    st.error(f"處理失敗：{e}")

st.divider()
st.caption("預覽僅供參考，實際輸出效果以下載的 PDF 為準")