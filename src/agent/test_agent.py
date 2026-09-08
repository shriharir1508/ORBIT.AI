from src.agent.agent import OrbitAgent


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — AGENT END-TO-END TEST")
    print("=" * 70)

    agent = OrbitAgent()

    test_queries = [
        "What are the total sales of Chennai Alandur?",
        "What are the key operational problems at Madurai Anna Nagar?",
        "What are the main patient attrition reasons?",
        "Which patients are at high follow-up risk?",
    ]

    try:

        for query in test_queries:

            print("\n" + "-" * 70)
            print(f"QUESTION: {query}")
            print("-" * 70)

            result = agent.ask(query)

            print(
                f"ROUTE: {result['route']}"
            )

            print(
                f"EVIDENCE ITEMS: "
                f"{result['evidence_count']}"
            )

            print("\nANSWER:")
            print(result["answer"])

    finally:

        agent.close()

    print("\n" + "=" * 70)
    print("AGENT END-TO-END TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()