from src.ingest import embedder, collection


def retrieve_chunks(query: str, n_results: int = 3,
                    filename_filter: str = None) -> list[dict]:
    """
    Convert query to embedding → find top-n similar chunks in ChromaDB.
    Optionally filter by filename.
    Returns list of dicts with text, metadata, and similarity score.
    """
    query_embedding = embedder.encode([query]).tolist()[0]

    where_filter = {"filename": filename_filter} if filename_filter else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        similarity = 1 - results["distances"][0][i]  # cosine distance → similarity
        chunks.append({
            "text":       results["documents"][0][i],
            "filename":   results["metadatas"][0][i]["filename"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "similarity": round(similarity, 4)
        })

    return chunks


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} — {chunk['filename']}, chunk {chunk['chunk_index']}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(context_parts)


if __name__ == "__main__":
    # Quick test — will return empty if no docs ingested
    test_query = "What is this document about?"
    chunks = retrieve_chunks(test_query, n_results=3)
    print(f"Query: {test_query}")
    print(f"Retrieved {len(chunks)} chunks")
    for c in chunks:
        print(f"  - [{c['filename']}] similarity: {c['similarity']}")
