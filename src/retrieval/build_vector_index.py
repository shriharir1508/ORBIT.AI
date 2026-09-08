from pathlib import Path
import json
import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAG_DOCUMENT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rag_documents.json"
)

VECTOR_DB_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vector_db"
)

COLLECTION_NAME = "orbit_rag"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_documents():
    if not RAG_DOCUMENT_FILE.exists():
        raise FileNotFoundError(
            f"RAG document file not found: {RAG_DOCUMENT_FILE}"
        )

    with open(
        RAG_DOCUMENT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        documents = json.load(file)

    if not documents:
        raise ValueError("No RAG documents found.")

    return documents


def build_vector_index(documents):

    VECTOR_DB_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nLoading embedding model...")
    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    print("Creating ChromaDB...")
    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "ORBIT.AI semantic retrieval index"
        }
    )

    # Rebuild the collection to keep the index
    # synchronized with the current RAG document file.
    existing_ids = collection.get()["ids"]

    if existing_ids:
        collection.delete(
            ids=existing_ids
        )

    ids = [
        document["document_id"]
        for document in documents
    ]

    texts = [
        document["text"]
        for document in documents
    ]

    metadatas = [
        {
            "source_type": document["source_type"],
            "source_record_id": document[
                "source_record_id"
            ],
        }
        for document in documents
    ]

    print(
        f"Generating embeddings for "
        f"{len(texts)} documents..."
    )

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    ).tolist()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return collection


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — VECTOR INDEX BUILD")
    print("=" * 70)

    documents = load_documents()

    print(
        f"\nRAG documents loaded: {len(documents)}"
    )

    collection = build_vector_index(
        documents
    )

    print("\nVECTOR INDEX")
    print("-" * 40)
    print(
        f"Collection: {COLLECTION_NAME}"
    )
    print(
        f"Indexed documents: {collection.count()}"
    )
    print(
        f"Embedding model: {EMBEDDING_MODEL}"
    )
    print(
        f"Vector database: {VECTOR_DB_DIR}"
    )

    print("\n" + "=" * 70)
    print("VECTOR INDEX BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()