import logging
import pytesseract
import mimetypes
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from PIL import Image
import cv2
import numpy as np
import re
import io

# Setup logging
logging.basicConfig(level=logging.INFO)

# Paths
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Users\Kittu\Downloads\Release-24.08.0-0 (1)\poppler-24.08.0\Library\bin"

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

async def handle_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📥 Received a document!")

    # Download file
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    filename = update.message.document.file_name

    # Detect file type using mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    print(f"📎 Detected MIME type: {mime_type}")

    try:
        if mime_type == "application/pdf":
            from pdf2image import convert_from_bytes
            print("📂 Using Poppler Path:", POPPLER_PATH)
            images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
            img = images[0].convert("RGB")  # First page only
            text = pytesseract.image_to_string(img, config='--psm 6')
        else:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(img_cv, 150, 255, cv2.THRESH_BINARY)
            text = pytesseract.image_to_string(thresh, config='--psm 6')
    except Exception as e:
        print("❌ OCR Processing Error:", e)
        await update.message.reply_text("❌ Failed to extract text. Please ensure the document is a valid invoice image or PDF.")
        return

    print("🧠 Extracted Text:", text)

    cleaned_text = text.replace('\n', ' ').strip()

    # Extract fields
    invoice_number = re.search(r"Invoice\s+(Number|No\.?|#)?\s*[:\-]?\s*([A-Z0-9\-]+)", cleaned_text, re.IGNORECASE)
    date = re.search(r"(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})", cleaned_text, re.IGNORECASE)
    total = re.search(r"Total\s*\$?([0-9,]+\.\d{2}|[0-9,]+)", cleaned_text, re.IGNORECASE)

    # Format response
    response = f"📄 **Extracted Invoice Info:**\n"
    response += f"🧾 Invoice Number: {invoice_number.group(2) if invoice_number else 'Not Found'}\n"
    response += f"📅 Date: {date.group(1) if date else 'Not Found'}\n"
    response += f"💰 Total: ${total.group(1) if total else 'Not Found'}"

    await update.message.reply_text(response)

# Replace with your real token
BOT_TOKEN = "7778798334:AAFraDW_pfKwE_N6WGAuX9Hb2V-xax59rt0"

# Start the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.Document.ALL, handle_invoice))
app.run_polling()
