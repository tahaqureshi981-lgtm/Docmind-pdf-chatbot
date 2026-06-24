import os
from groq import Groq
from src.retriever import retrieve_chunks, format_context

# ── Config ────────────────────────────────────────────────────────────────────
LLM_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a helpful document assistant. You answer questions based ONLY on the provided document context.

Rules:
- Only use information from the provided context
- If the answer is not in the context, say "I couldn't find this information in the uploaded documents."
- Always cite which source you used (Source 1, Source 2, etc.)
- Be concise and accurate
- Never make up information
"""


def ask(question: str, filename_filter: str = None,
        n_chunks: int = 3, chat_history: list = None) -> dict:
    """
    Full RAG pipeline:
    question → retrieve chunks → build prompt → Groq LLM → answer + citations
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    # Step 1 — Retrieve relevant chunks
    chunks = retrieve_chunks(question, n_results=n_chunks,
                             filename_filter=filename_filter)

    if not chunks:
        return {
            "answer": "No documents found. Please upload a PDF first.",
            "sources": [],
            "chunks_used": 0
        }

    # Step 2 — Format context
    context = format_context(chunks)

    # Step 3 — Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add chat history if provided (multi-turn conversations)
    if chat_history:
        for turn in chat_history[-4:]:  # last 4 turns only (token limit)
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Add current question with context
    user_message = f"""Context from documents:
{context}

Question: {question}

Answer based only on the context above:"""

    messages.append({"role": "user", "content": user_message})

    # Step 4 — Call Groq LLM
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,   # low = more factual, less creative
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    # Step 5 — Build sources for citation
    sources = [
        {
            "filename":    c["filename"],
            "chunk_index": c["chunk_index"],
            "similarity":  c["similarity"],
            "preview":     c["text"][:200] + "..."
        }
        for c in chunks
    ]

    return {
        "answer":      answer,
        "sources":     sources,
        "chunks_used": len(chunks),
        "model":       LLM_MODEL
    }


if __name__ == "__main__":
    import sys
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set")
        sys.exit(1)

    result = ask("What is this document about?")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {len(result['sources'])}")
    print(f"Model: {result['model']}")
