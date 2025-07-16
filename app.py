import streamlit as st
from pdf2image import convert_from_path
from PIL import Image
import os

st.title("📄 PDF to Image Converter")

uploaded_file = st.file_uploader("Upload your invoice PDF", type="pdf")

if uploaded_file is not None:
    with open("uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    images = convert_from_path("uploaded.pdf")
    
    st.subheader("📸 Converted Pages:")
    for i, img in enumerate(images):
        img_path = f"page_{i+1}.jpg"
        img.save(img_path, "JPEG")
        st.image(img, caption=f"Page {i+1}", use_column_width=True)

    st.success("✅ Conversion complete!")
