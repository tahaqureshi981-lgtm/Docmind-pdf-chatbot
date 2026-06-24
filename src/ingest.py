import os
import hashlib
from pathlib import Path

import PyPDF2
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# ── Config ────────────────────────────────────────────────────────────────────
VECTORSTORE_DIR = "vectorstore"
COLLECTION_NAME = "pdf_documents"
CHUNK_SIZE      = 500   # words per chunk
CHUNK_OVERLAP   = 50    # overlapping words between chunks
EMBED_MODEL     = "all-MiniLM-L6-v2"

# ── Init embedding model (loads once) ────────────────────────────────────────
print("⏳ Loading embedding model...")
embedder = SentenceTransformer(EMBED_MODEL)
print("✅ Embedding model loaded")

# ── Init ChromaDB ─────────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n[Page {page_num + 1}]\n{page_text}"
    return text.strip()


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE,
                      overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words  = text.split()
    chunks = []
    start  = 0

    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def get_pdf_hash(pdf_path: str) -> str:
    """Get MD5 hash of PDF to avoid re-ingesting same file."""
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def is_already_ingested(pdf_hash: str) -> bool:
    """Check if this PDF was already ingested into ChromaDB."""
    results = collection.get(where={"pdf_hash": pdf_hash}, limit=1)
    return len(results["ids"]) > 0


def ingest_pdf(pdf_path: str, filename: str) -> dict:
    """
    Full ingestion pipeline:
    PDF → text → chunks → embeddings → ChromaDB
    Returns summary dict.
    """
    pdf_hash = get_pdf_hash(pdf_path)

    if is_already_ingested(pdf_hash):
        print(f"⚠️  Already ingested: {filename}")
        existing = collection.get(where={"pdf_hash": pdf_hash})
        return {
            "filename": filename,
            "status": "already_exists",
            "chunks": len(existing["ids"])
        }

    print(f"📄 Extracting text from: {filename}")
    text = extract_text_from_pdf(pdf_path)

    if not text:
        return {"filename": filename, "status": "error", "message": "No text extracted"}

    print(f"✂️  Splitting into chunks...")
    chunks = split_into_chunks(text)
    print(f"   → {len(chunks)} chunks created")

    print(f"🔢 Generating embeddings...")
    embeddings = embedder.encode(chunks, show_progress_bar=True).tolist()

    print(f"💾 Storing in ChromaDB...")
    ids       = [f"{pdf_hash}_{i}" for i in range(len(chunks))]
    metadatas = [{"filename": filename, "pdf_hash": pdf_hash,
                  "chunk_index": i, "total_chunks": len(chunks)}
                 for i in range(len(chunks))]

    # ChromaDB has a 5461 item batch limit
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i:i+batch_size],
            documents=chunks[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )

    print(f"✅ Ingested {len(chunks)} chunks from {filename}")
    return {
        "filename": filename,
        "status": "success",
        "chunks": len(chunks),
        "characters": len(text),
        "pdf_hash": pdf_hash
    }


def list_ingested_documents() -> list[dict]:
    """List all unique documents in the vector store."""
    results = collection.get()
    if not results["ids"]:
        return []

    seen = {}
    for meta in results["metadatas"]:
        h = meta["pdf_hash"]
        if h not in seen:
            seen[h] = {
                "filename": meta["filename"],
                "chunks": meta["total_chunks"],
                "pdf_hash": h
            }
    return list(seen.values())


def delete_document(pdf_hash: str) -> bool:
    """Delete a document from the vector store by its hash."""
    results = collection.get(where={"pdf_hash": pdf_hash})
    if not results["ids"]:
        return False
    collection.delete(ids=results["ids"])
    print(f"🗑️  Deleted {len(results['ids'])} chunks for hash {pdf_hash}")
    return True


if __name__ == "__main__":
    # Quick test
    print("ChromaDB collection:", COLLECTION_NAME)
    print("Documents stored:", len(list_ingested_documents()))
