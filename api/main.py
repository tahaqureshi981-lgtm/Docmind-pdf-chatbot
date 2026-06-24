import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.ingest import ingest_pdf, list_ingested_documents, delete_document
from src.chain import ask

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PDF Chatbot API",
    description="Upload PDFs and chat with them using RAG + Groq LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    filename_filter: Optional[str] = None
    n_chunks: int = 3
    chat_history: list = []

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the main topic of this document?",
                "filename_filter": None,
                "n_chunks": 3,
                "chat_history": []
            }
        }


class ChatResponse(BaseModel):
    answer: str
    sources: list
    chunks_used: int
    model: str


class DocumentInfo(BaseModel):
    filename: str
    chunks: int
    pdf_hash: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "PDF Chatbot API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    docs = list_ingested_documents()
    return {
        "status": "ok",
        "documents_loaded": len(docs),
        "groq_key_set": bool(os.getenv("GROQ_API_KEY"))
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and ingest a PDF file."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save PDF to disk
    pdf_path = os.path.join(DATA_DIR, file.filename)
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest into ChromaDB
    result = ingest_pdf(pdf_path, file.filename)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Ingestion failed"))

    return {
        "message": f"Successfully ingested {file.filename}",
        "result": result
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Ask a question about uploaded documents."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = ask(
        question=request.question,
        filename_filter=request.filename_filter,
        n_chunks=request.n_chunks,
        chat_history=request.chat_history
    )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        model=result.get("model", "llama3-8b-8192")
    )


@app.get("/documents", response_model=list[DocumentInfo])
def get_documents():
    """List all ingested documents."""
    return list_ingested_documents()


@app.delete("/documents/{pdf_hash}")
def remove_document(pdf_hash: str):
    """Delete a document from the vector store."""
    success = delete_document(pdf_hash)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document deleted successfully."}


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
