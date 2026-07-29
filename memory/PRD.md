# Multi-modal RAG for Technical Support

## Problem
Web app that accepts a PDF technical manual + product images and answers troubleshooting questions using RAG (FAISS + sentence-transformers) plus Gemini multimodal (vision + text).

## Stack
- Backend: FastAPI, PyMuPDF, sentence-transformers, FAISS, google-genai SDK, Gemini `gemini-flash-latest`
- Frontend: React (CRA/craco template, dark theme, tailwind + shadcn available)
- Storage: FAISS on disk in `vector_store/`; PDFs in `manuals/`; images in `uploads/`
- No auth, session-only chat history (browser state)

## Modules (backend/)
- pdf_loader.py — PyMuPDF text extraction + chunking
- embeddings.py — sentence-transformers all-MiniLM-L6-v2
- vector_store.py — FAISS IndexFlatIP with pickle chunks
- image_processor.py — PIL image save/load
- gemini.py — google-genai client, gemini-flash-latest
- rag.py — orchestrator (index_pdf, get_context, answer)
- server.py — FastAPI /api routes

## Endpoints
- POST /api/upload-pdf
- POST /api/upload-image
- POST /api/ask (question + image_paths)
- POST /api/reset
- GET  /api/status

## Env
- backend/.env: GEMINI_API_KEY (user-provided)

## Implemented (2026-02)
- End-to-end RAG flow with retrieved context display
- Multi-image upload and analysis
- Dark modern UI with in-line source chunks
- Session-only chat history

## Backlog
- P1: Streaming responses for faster perceived latency
- P1: Multiple PDF support / manual switching
- P2: Highlight source excerpts inside chat
- P2: Deployment
