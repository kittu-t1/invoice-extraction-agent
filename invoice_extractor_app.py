import streamlit as st

# ✅ Streamlit config
st.set_page_config(page_title="Invoice Extraction Agent", page_icon="🧾")

import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import numpy as np
import cv2
import re

# 🪟 Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🧾 App Title
st.title("🧾 Invoice Extraction Agent")
st.write("Upload a PDF or Image of your invoice")

# 📂 File Upload
uploaded_file = st.file_uploader("Upload Invoice", type=["pdf", "png", "jpg", "jpeg", "webp"])

if uploaded_file:
    # 🖼️ Handle PDF or image
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
    else:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images = [img]

    # 🖼️ Display the first page
    st.image(images[0], caption="Uploaded Invoice", use_container_width=True)

    # 🔍 OCR Preprocessing
    st.subheader("🔍 Extracted Text")

    img_cv = np.array(images[0])
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    _, thresh = cv2.threshold(resized, 150, 255, cv2.THRESH_BINARY)

    # ✨ OCR Text
    extracted_text = pytesseract.image_to_string(thresh, config='--psm 6')
    st.text_area("Text from Invoice", extracted_text, height=250)

    # 🧹 Clean OCR output
    cleaned_text = extracted_text.replace('\n', ' ').replace('’', "'").replace('‘', "'").strip()

    # 📌 Field Extraction
    st.subheader("📌 Extracted Fields")

    # 🧠 Robust Patterns
    invoice_number = re.search(r"Invoice\s+(Number|No\.?|#)?\s*[:\-]?\s*([A-Z0-9]+)", cleaned_text, re.IGNORECASE)
    date = re.search(r"(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})", cleaned_text, re.IGNORECASE)
    total = re.search(r"Total\s*\$([0-9,]+\.\d{2}|[0-9,]+)", cleaned_text, re.IGNORECASE)

    # 🖊️ Display Extracted Fields
    st.write("**Invoice Number:**", invoice_number.group(2) if invoice_number else "Not Found")
    st.write("**Date:**", date.group(1) if date else "Not Found")
    st.write("**Total Amount:**", total.group(1) if total else "Not Found")

    if not (invoice_number or date or total):
        st.warning("⚠️ Fields not detected. Try a clearer invoice or a PDF version.")
