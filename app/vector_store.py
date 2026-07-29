import json
import os
import math
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)

# Helper for API client
def get_client():
    load_dotenv(override=True)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key) if api_key else None

EMBEDDING_MODEL = "text-embedding-004"

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two vector embeddings."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a * a for a in v1))
    magnitude_v2 = math.sqrt(sum(b * b for b in v2))
    if not magnitude_v1 or not magnitude_v2:
        return 0.0
    return dot_product / (magnitude_v1 * magnitude_v2)

def generate_embedding(text: str) -> list[float]:
    """Generates vector embedding for a text string using text-embedding-004."""
    try:
        client = get_client()
        if not client:
            return []
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )
        if response.embedding and hasattr(response.embedding, "values"):
            return response.embedding.values
        elif isinstance(response.embedding, list):
            return response.embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
    return []

def search_relevant_chunks(query_text: str, candidates: list[dict], top_k: int = 3) -> list[dict]:
    """Given a query and a candidate list of chunks, returns top_k most semantically relevant chunks."""
    query_vector = generate_embedding(query_text)
    if not query_vector:
        return candidates[:top_k]

    scored = []
    for cand in candidates:
        text = cand.get("text", "")
        cand_vector = cand.get("vector")
        if not cand_vector:
            cand_vector = generate_embedding(text)
            cand["vector"] = cand_vector
        
        if cand_vector:
            sim = cosine_similarity(query_vector, cand_vector)
            scored.append((sim, cand))
        else:
            scored.append((0.0, cand))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_k]]
