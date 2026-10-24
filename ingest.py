import time
import argparse
import hashlib
from pathlib import Path

import pymupdf

from app.knowledge import ensure_index, embed


def chunks(text, size=1100, overlap=180):
    text = " ".join(text.split())
    step = size - overlap

    return [
        text[i:i + size]
        for i in range(0, len(text), step)
        if len(text[i:i + size]) > 80
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="data/medical_book.pdf")
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")

    pdf = Path(args.pdf)

    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    index = ensure_index()
    uploaded = 0
    skipped = 0

    def upsert_batch(items):
        nonlocal uploaded, skipped

        if not items:
            return

        # Check which chunks already exist in Pinecone.
        response = index.fetch(ids=[item[0] for item in items])
        existing = set(response.vectors.keys())

        pending = [
            item for item in items
            if item[0] not in existing
        ]

        skipped += len(items) - len(pending)

        if not pending:
            print("All chunks in this batch already exist.")
            return

        # Embed all pending texts in one Gemini request.
        vectors = embed([item[1] for item in pending])

        if len(vectors) != len(pending):
            raise ValueError("Embedding count mismatch")

        index.upsert(
            vectors=[
                {
                    "id": item[0],
                    "values": vector,
                    "metadata": item[2],
                }
                for item, vector in zip(pending, vectors)
            ]
        )

        uploaded += len(pending)
        print(
            f"Uploaded: {uploaded} | Already stored: {skipped}",
            flush=True,
        )

    with pymupdf.open(pdf) as doc:
        batch = []

        for page_number, page in enumerate(doc, start=1):
            for part, content in enumerate(
                chunks(page.get_text()), start=1
            ):
                chunk_id = hashlib.sha256(
                    f"{pdf.name}:{page_number}:{part}:{content}".encode(
                        "utf-8"
                    )
                ).hexdigest()

                metadata = {
                    "page": page_number,
                    "text": content,
                    "source": pdf.name,
                }

                batch.append((chunk_id, content, metadata))

                if len(batch) >= args.batch_size:
                    upsert_batch(batch)
                    time.sleep(10)
                    batch = []

            if page_number % 50 == 0:
                print(
                    f"Processed pages: {page_number}/{len(doc)}",
                    flush=True,
                )

        if batch:
            upsert_batch(batch)

    print("\nIngestion finished.")
    print(f"New chunks uploaded: {uploaded}")
    print(f"Existing chunks skipped: {skipped}")


if __name__ == "__main__":
    main()
