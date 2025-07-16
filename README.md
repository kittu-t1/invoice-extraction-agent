# Invoice Extraction Agent

An AI-powered Python assistant that extracts key information from invoices using OCR and allows querying via LLMs.  
It supports both scanned PDFs and native PDFs, saving parsed data to a Chroma vector store for RAG-style answering.

---

 Features

-  Extracts text from invoices (PDF/images)
-  OCR with Tesseract for scanned invoices
-  Text layer reading for digital PDFs
-  Embeds chunks into a vector database (ChromaDB)
-  Allows asking natural-language questions about uploaded invoices
-  LLM responses are grounded via Retrieval-Augmented Generation (RAG)
-  Supports both CLI and Telegram-based interface

---

 Technologies Used

- `Python 3.10+`
- `pytesseract`, `pdfplumber`, `pdf2image` – for OCR and PDF parsing
- `Together AI` – for LLM queries
- `Chroma` – vector DB for storage and similarity search
- `Poppler` – for PDF image conversion (Windows binaries required)
- `Tesseract OCR` – for extracting text from scanned images

---

 Getting Started

1. Clone the repository
```bash
git clone https://github.com/kittu-t1/invoice-extraction-agent.git
cd invoice-extraction-agent
