from src.retrieval.retriever import HybridRetriever
from src.retrieval.evidence import EvidencePackage


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — EVIDENCE PACKAGE TEST")
    print("=" * 70)

    retriever = HybridRetriever()
    evidence = EvidencePackage()

    try:

        # Structured evidence
        sales = retriever.sales_by_branch(
            "Chennai Alandur"
        )

        evidence.add_structured_results(
            sales
        )

        # Semantic evidence
        semantic_results = (
            retriever.semantic_search(
                "patients who did not respond to follow-up",
                n_results=3
            )
        )

        evidence.add_semantic_results(
            semantic_results
        )

        print(
            f"\nEvidence items collected: "
            f"{evidence.count()}"
        )

        print("\n" + "-" * 70)
        print("EVIDENCE PACKAGE")
        print("-" * 70)

        print(
            evidence.to_text()
        )

        print("\n" + "-" * 70)
        print("DICTIONARY FORMAT")
        print("-" * 70)

        for item in evidence.to_dict():
            print(item)

        print("\n" + "=" * 70)
        print("EVIDENCE PACKAGE TEST COMPLETE")
        print("=" * 70)

    finally:
        retriever.close()


if __name__ == "__main__":
    main()