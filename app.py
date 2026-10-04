import io
import cv2
import numpy as np
import streamlit as st
from PIL import Image

# ضبط إعدادات الصفحة
st.set_page_config(
    page_title="برنامج ترتيب الهويات A4", page_icon="🪪", layout="wide"
)

st.title("🪪 برنامج ترتيب المستمسكات والهويات على ورقة A4")
st.write(
    "قم برفع صور الهويات (وجه وظهر)، وسيتم تحديد الحواف وترتيبها تلقائياً على ورقة A4 جاهزة للطباعة."
)


# دالة القص التلقائي للحواف باستخدام OpenCV
def auto_crop_card(image):
    try:
        img_np = np.array(image)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            # تجنب القص الخاطئ إذا المساحة صغيرة جداً
            if w > 100 and h > 100:
                cropped = img_np[y : y + h, x : x + w]
                return Image.fromarray(cropped)
    except Exception:
        pass
    return image


# شريط التحكم الجانبي للإعدادات
st.sidebar.header("⚙️ إعدادات الورقة والهويات")

use_auto_crop = st.sidebar.checkbox(
    "تفعيل القص التلقائي للحواف (Auto-Crop)", value=True
)

st.sidebar.subheader("📐 أبعاد الهوية (ملم)")
card_width_mm = st.sidebar.slider("عرض الهوية (ملم)", 50, 110, 85)
card_height_mm = st.sidebar.slider("ارتفاع الهوية (ملم)", 30, 80, 54)

st.sidebar.subheader("↔️ الهوامش والمسافات (ملم)")
margin_top_mm = st.sidebar.slider("الهامش العلوي (ملم)", 5, 50, 15)
margin_side_mm = st.sidebar.slider("الهامش الجانبي (ملم)", 5, 50, 15)
gap_x_mm = st.sidebar.slider("المسافة الأفقية بين الهويات (ملم)", 0, 30, 10)
gap_y_mm = st.sidebar.slider("المسافة العمودية بين الهويات (ملم)", 0, 30, 10)

# رفع الصور
uploaded_files = st.file_uploader(
    "اختر صور الهويات والمستمسكات (يمكنك اختيار عدة صور)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
    images = []
    for f in uploaded_files:
        img = Image.open(f).convert("RGB")
        if use_auto_crop:
            img = auto_crop_card(img)
        images.append(img)

    st.subheader("🔄 ترتيب الهويات والتعديل عليها")
    cols_order = st.columns(min(len(images), 4))

    # السماح للمستخدم بإعادة ترتيب الصور
    ordered_images = []
    order_indices = list(range(len(images)))

    st.write("أعد ترتيب الصور بسب الأسبقية:")
    for idx, img in enumerate(images):
        with cols_order[idx % 4]:
            st.image(
                img, caption=f"صورة رقم {idx + 1}", use_container_width=True
            )
            new_pos = st.number_input(
                f"موقع الصورة {idx + 1}",
                min_value=1,
                max_value=len(images),
                value=idx + 1,
                key=f"pos_{idx}",
            )
            order_indices[idx] = new_pos - 1

    # ترتيب الصور حسب اختيار المستخدم
    sorted_images = [x for _, x in sorted(zip(order_indices, images))]

    # إنشاء ورقة A4 بدقة 300 DPI (2480 x 3508 pixels)
    dpi = 300
    mm_to_px = lambda mm: int(mm * dpi / 25.4)

    a4_w_px = mm_to_px(210)
    a4_h_px = mm_to_px(297)

    a4_canvas = Image.new("RGB", (a4_w_px, a4_h_px), "white")

    c_w_px = mm_to_px(card_width_mm)
    c_h_px = mm_to_px(card_height_mm)

    margin_top_px = mm_to_px(margin_top_mm)
    margin_side_px = mm_to_px(margin_side_mm)
    gap_x_px = mm_to_px(gap_x_mm)
    gap_y_px = mm_to_px(gap_y_mm)

    # حساب مواقع الصور (عمودين: يمين ويسار)
    # العمود 0: يمين الصفحة، العمود 1: يسار الصفحة
    for idx, img in enumerate(sorted_images):
        row = idx // 2
        col = idx % 2

        # جهة اليمين أولاً ثم اليسار
        if col == 0:
            x_px = a4_w_px - margin_side_px - c_w_px
        else:
            x_px = margin_side_px

        y_px = margin_top_px + row * (c_h_px + gap_y_px)

        if y_px + c_h_px <= a4_h_px:
            resized_img = img.resize((c_w_px, c_h_px), Image.Resampling.LANCZOS)
            a4_canvas.paste(resized_img, (x_px, y_px))

    # عرض المعاينة النهائية
    st.subheader("🖼️ معاينة ورقة A4 الجاهزة للطباعة")
    st.image(
        a4_canvas,
        caption="معاينة A4 (اليمين واليسار متسلسلة)",
        use_container_width=True,
    )

    # تحويل إلى PDF للتحميل
    pdf_bytes = io.BytesIO()
    a4_canvas.save(pdf_bytes, format="PDF", resolution=300.0)
    pdf_bytes.seek(0)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.download_button(
            label="📥 تحميل ورقة A4 بملف PDF للطباعة",
            data=pdf_bytes,
            file_name="ID_Cards_A4.pdf",
            mime="application/pdf",
        )

    with col_btn2:
        img_bytes = io.BytesIO()
        a4_canvas.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        st.download_button(
            label="🖼️ تحميل المعاينة كصورة PNG",
            data=img_bytes,
            file_name="ID_Cards_A4.png",
            mime="image/png",
        )
