# Multi-modal RAG for Technical Support

A simple web app that:
- Reads a PDF technical manual
- Looks at product images
- Answers troubleshooting questions using retrieved manual context + image understanding

## Modules

### Backend (`backend/`)

- **`pdf_loader.py`** – opens the PDF with PyMuPDF, extracts all text, and splits it into overlapping word chunks.
- **`embeddings.py`** – wraps `sentence-transformers` (`all-MiniLM-L6-v2`) to turn text into vectors.
- **`vector_store.py`** – builds / loads a FAISS inner-product index on disk (`vector_store/`) and does top-k search.
- **`image_processor.py`** – saves uploaded images to `uploads/` and loads them as PIL images.
- **`gemini.py`** – calls Google Gemini with a prompt and optional images.
- **`rag.py`** – ties it all together: index a PDF, retrieve chunks for a query, and ask Gemini with retrieved chunks + images.
- **`server.py`** – FastAPI endpoints (`/api/upload-pdf`, `/api/upload-image`, `/api/ask`, `/api/reset`, `/api/status`).

### Frontend (`frontend/`)

React app with a dark UI. One page with three parts:
1. Upload PDF (indexes it)
2. Upload product images (keeps previews)
3. Chat panel — ask a question, get an answer with expandable source chunks

Chat history lives only in browser state (session-only, resets on reload).

## Setup (local)

### Backend

```bash
cd backend
pip install -r requirements.txt
# add your key to backend/.env
# GEMINI_API_KEY=your_key_here
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd frontend
yarn install
yarn start
```

Set `REACT_APP_BACKEND_URL` in `frontend/.env` to point at the backend.

## Notes

- The FAISS index and chunks live under `vector_store/`. Uploading a new PDF replaces the index.
- Uploaded images live under `uploads/`. Manual PDFs live under `manuals/`.
- Uses `gemini-flash-latest` for both vision and text.
