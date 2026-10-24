
import os
import time
import random
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pinecone import Pinecone

from app.config import settings

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

if not settings.pinecone_api_key:
    raise ValueError("PINECONE_API_KEY is missing from .env")

gemini = genai.Client(api_key=gemini_api_key)
pc = Pinecone(api_key=settings.pinecone_api_key)


def ensure_index():
    return pc.Index(settings.pinecone_index)


def _embed_once(texts):
    """Make one Gemini embedding request and validate the response."""

    print(
        f"Requesting embeddings for {len(texts)} texts...",
        flush=True,
    )

    response = gemini.models.embed_content(
        model="gemini-embedding-2",
        contents=[
            types.Content(
                parts=[types.Part.from_text(text=text)]
            )
            for text in texts
        ],
        config=types.EmbedContentConfig(
            output_dimensionality=1536,
        ),
    )

    embeddings = response.embeddings or []
    vectors = [item.values for item in embeddings]

    print(f"Expected embeddings: {len(texts)}", flush=True)
    print(f"Received embeddings: {len(vectors)}", flush=True)

    if len(vectors) != len(texts):
        raise ValueError(
            f"Embedding count mismatch: expected {len(texts)}, "
            f"received {len(vectors)}"
        )

    return vectors


def embed(texts, max_attempts=8):
    """Retry temporary Gemini rate-limit errors automatically."""

    if not texts:
        return []

    for attempt in range(max_attempts):
        try:
            return _embed_once(texts)

        except Exception as exc:
            message = str(exc)
            is_rate_limit = (
                "429" in message
                or "RESOURCE_EXHAUSTED" in message
            )

            if not is_rate_limit:
                raise

            if attempt == max_attempts - 1:
                print(
                    "Gemini rate limit persisted after all retry attempts.",
                    flush=True,
                )
                raise

            # Use Google's suggested retry delay when available.
            match = re.search(
                r"retry in\s+(\d+(?:\.\d+)?)\s*s",
                message,
                re.IGNORECASE,
            )

            wait_seconds = (
                float(match.group(1))
                if match
                else min(60 * (2 ** attempt), 300)
            )

            # Small random buffer helps avoid retrying too early.
            wait_seconds += random.uniform(2, 6)

            print(
                f"Gemini rate limit reached. Waiting "
                f"{wait_seconds:.1f} seconds before retry "
                f"{attempt + 2}/{max_attempts}...",
                flush=True,
            )

            time.sleep(wait_seconds)

    raise RuntimeError("Embedding retries exhausted.")

def search_kb(question, top_k=5):
    """Retrieve relevant medical-book passages from Pinecone."""

    question = question.strip()
    if not question:
        return []

    # Use the same Gemini model and dimensions as ingestion.
    query_vector = embed([question])[0]

    index = ensure_index()

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    passages = []

    for match in results.matches:
        metadata = match.metadata or {}

        passages.append({
            "text": metadata.get("text", ""),
            "page": metadata.get("page"),
            "source": metadata.get("source", "medical_book.pdf"),
            "score": match.score,
        })

    return passages
