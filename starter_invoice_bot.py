import logging
import io
import pytesseract
import mimetypes
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import chromadb
from chromadb.config import Settings
import re
import cv2
import numpy as np
from together import Together

# Logging setup
logging.basicConfig(level=logging.INFO)

# Together API Key 🔐
together = Together(api_key="TOGETHER_API_KEY")

# Tesseract & Poppler paths
TESSERACT_PATH = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
POPPLER_PATH = r"C:\\Users\\Kittu\\Downloads\\Release-24.08.0-0 (1)\\poppler-24.08.0\\Library\\bin"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Chroma DB setup
chroma_client = chromadb.Client(Settings())
collection = chroma_client.get_or_create_collection("invoices")

# Fake embedding
def fake_embed(text):
    return [float(ord(c) % 10) for c in text[:10]] + [0.0] * (1536 - 10)

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def extract_text_from_pdf(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    raw_text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            raw_text += t
    if raw_text.strip():
        return raw_text, "pypdf"
    images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
    ocr_text = "\n".join(pytesseract.image_to_string(img, config="--psm 6") for img in images)
    return ocr_text, "ocr"

def extract_text_from_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(thresh, config="--psm 6")

def find_cost_in_excel(query):
    try:
        df = pd.read_excel("Electrical Items Master Sheet-2.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        query_clean = query.lower().replace("cost of", "").replace("price of", "").strip()

        if "issue description" not in df.columns:
            return "❌ Excel format error: 'issue description' column not found."

        for _, row in df.iterrows():
            item = str(row.get("issue description", "")).lower().strip()
            if query_clean in item or item in query_clean:
                cost = row.get("cost", "N/A")
                return f"✅ Cost of '{row['issue description']}': ₹{cost}"

        return "❌ No matching cost item found in the Excel sheet."
    except Exception as e:
        return f"❌ Excel processing error: {e}"

# Telegram Handlers
async def handle_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    filename = update.message.document.file_name
    mime_type, _ = mimetypes.guess_type(filename)

    try:
        if mime_type == "application/pdf":
            text, source = extract_text_from_pdf(file_bytes)
        else:
            text = extract_text_from_image(file_bytes)
            source = "ocr-image"

        cleaned_text = text.replace('\n', ' ').strip()
        logging.info(f"Extracted via {source}: {cleaned_text[:500]}")

        # ✅ Clear existing chunks
        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            embedding = fake_embed(chunk)
            collection.add(documents=[chunk], embeddings=[embedding], ids=[f"doc_{i}_{filename}"])

        await update.message.reply_text("✅ Text extracted and stored in vector DB.")

    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    try:
        if any(word in question.lower() for word in ["cost", "price", "rate"]):
            response = find_cost_in_excel(question)
            await update.message.reply_text(response)
            return

        query_embedding = fake_embed(question)
        results = collection.query(query_embeddings=[query_embedding], n_results=3)
        chunks = results['documents'][0]
        context_text = "\n".join(chunks)

        prompt = f"Use the context below to answer the question.\n\nContext:\n{context_text}\n\nQuestion: {question}\nAnswer:"

        response = together.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        await update.message.reply_text(response.choices[0].message.content)

    except Exception as e:
        await update.message.reply_text(f"❌ Q&A failed: {str(e)}")

# Start the bot
BOT_TOKEN = "7778798334:AAFraDW_pfKwE_N6WGAuX9Hb2V-xax59rt0"
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.Document.ALL, handle_invoice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
app.run_polling()
