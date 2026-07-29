# Multi-modal RAG for Technical Support

An AI-powered technical support assistant that combines **Retrieval-Augmented Generation (RAG)** with **Google Gemini** to answer troubleshooting queries using both **PDF manuals** and **product images**.

## Overview

This application allows users to:

- Upload a product's technical manual (PDF)
- Upload one or more product images
- Ask troubleshooting questions in natural language
- Receive context-aware answers generated from the manual and image analysis

The system retrieves the most relevant sections from the uploaded manual using vector search and combines them with image understanding to generate accurate responses.

---

## Features

- PDF manual upload and indexing
- Product image upload with preview
- Semantic search using FAISS
- Google Gemini Vision + Text integration
- Context-aware troubleshooting responses
- Responsive React interface
- FastAPI REST backend
- Session-based chat history
- Reset functionality

---

## Tech Stack

### Frontend

- React
- JavaScript
- CSS

### Backend

- Python
- FastAPI

### AI

- Google Gemini API
- Gemini Embedding API

### Vector Search

- FAISS

### PDF Processing

- PyMuPDF

---

## Project Structure

```
backend/
    server.py
    rag.py
    pdf_loader.py
    embeddings.py
    vector_store.py
    gemini.py
    image_processor.py

frontend/
    React application

manuals/
uploads/
vector_store/
```

---

## Workflow

```
Upload PDF
      │
      ▼
Extract Text
      │
      ▼
Split into Chunks
      │
      ▼
Generate Embeddings
      │
      ▼
Store in FAISS
      │
      ▼
User Question + Product Image
      │
      ▼
Retrieve Relevant Chunks
      │
      ▼
Gemini
      │
      ▼
Generate Final Answer
```

---

## Local Setup

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn server:app --reload
```

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

### Frontend

```bash
cd frontend

yarn install
yarn start
```

Update the backend URL inside:

```
frontend/.env
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/upload-pdf` | Upload and index PDF |
| `/api/upload-image` | Upload product image |
| `/api/ask` | Ask troubleshooting question |
| `/api/reset` | Reset current session |
| `/api/status` | Check backend status |

---

## Future Improvements

- Support multiple manuals
- OCR support for scanned PDFs
- Conversation memory
- User authentication
- Cloud vector database
- Multi-language support

---

## License

This project is intended for educational purposes.
