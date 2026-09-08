from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

VECTOR_DB_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vector_db"
)

COLLECTION_NAME = "orbit_rag"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — SEMANTIC RETRIEVAL TEST")
    print("=" * 70)

    print("\nLoading embedding model...")

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    print(
        f"Indexed documents: {collection.count()}"
    )

    queries = [
        "patients who are at high risk of follow-up failure",
        "branch cleanliness and housekeeping problems",
        "patient attrition reasons",
        "brand communication and digital presence issues",
        "operational issues at Madurai Anna Nagar",
    ]

    for query in queries:

        query_embedding = model.encode(
            [query]
        ).tolist()

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=3
        )

        print("\n" + "-" * 70)
        print(f"QUERY: {query}")
        print("-" * 70)

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        for index, document in enumerate(documents):

            metadata = metadatas[index]
            distance = distances[index]

            print(
                f"\nRESULT {index + 1}"
            )

            print(
                f"Source type: "
                f"{metadata.get('source_type')}"
            )

            print(
                f"Source record: "
                f"{metadata.get('source_record_id')}"
            )

            print(
                f"Distance: {distance:.4f}"
            )

            print(
                f"Text: {document}"
            )

    print("\n" + "=" * 70)
    print("SEMANTIC RETRIEVAL TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()