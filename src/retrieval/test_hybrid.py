from src.retrieval.retriever import HybridRetriever


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():

    print_section("ORBIT.AI — HYBRID RETRIEVAL TEST")

    retriever = HybridRetriever()

    try:

        # ---------------------------------------------------------
        # TEST 1 — EXACT BRANCH ISSUE RETRIEVAL
        # ---------------------------------------------------------

        print_section(
            "TEST 1 — MADURAI ANNA NAGAR ISSUES"
        )

        issues = retriever.branch_issues(
            "Madurai Anna Nagar"
        )

        print(
            f"Exact issues found: {len(issues)}"
        )

        for issue in issues:
            print(
                f"\nIssue {issue['source_record_id']}: "
                f"{issue['issue']}"
            )
            print(
                f"Branch: {issue['branch']}"
            )

        # ---------------------------------------------------------
        # TEST 2 — HIGH-RISK PATIENTS
        # ---------------------------------------------------------

        print_section(
            "TEST 2 — HIGH-RISK PATIENTS"
        )

        patients = retriever.high_risk_patients()

        print(
            f"High-risk patient records: "
            f"{len(patients)}"
        )

        for patient in patients[:5]:
            print(
                f"\nRecord: "
                f"{patient['source_record_id']}"
            )
            print(
                f"Branch: {patient['branch']}"
            )
            print(
                f"Disease: {patient['disease']}"
            )
            print(
                f"Risk: {patient['followup_risk']}"
            )
            print(
                f"Contactability: "
                f"{patient['contactability']}"
            )

        # ---------------------------------------------------------
        # TEST 3 — BRANCH SALES
        # ---------------------------------------------------------

        print_section(
            "TEST 3 — CHENNAI ALANDUR SALES"
        )

        sales = retriever.sales_by_branch(
            "Chennai Alandur"
        )

        for row in sales:
            print(
                f"Branch: {row['branch']}"
            )
            print(
                f"Total sales: "
                f"{row['total_sales']:,.2f}"
            )
            print(
                f"Treatment sales: "
                f"{row['total_treatment']:,.2f}"
            )
            print(
                f"Medicine sales: "
                f"{row['medicine_sales']:,.2f}"
            )

        # ---------------------------------------------------------
        # TEST 4 — ATTRITION
        # ---------------------------------------------------------

        print_section(
            "TEST 4 — ATTRITION REFERENCE"
        )

        attrition = retriever.attrition_reasons()

        print(
            f"Attrition reference rows: "
            f"{len(attrition)}"
        )

        for row in attrition[:5]:
            print(
                f"{row['reason']}: "
                f"{row['frequency']}"
            )

        # ---------------------------------------------------------
        # TEST 5 — SEMANTIC RETRIEVAL
        # ---------------------------------------------------------

        print_section(
            "TEST 5 — SEMANTIC RETRIEVAL"
        )

        results = retriever.semantic_search(
            "patients who did not respond to follow-up",
            n_results=3
        )

        for index, result in enumerate(
            results,
            start=1
        ):
            print(
                f"\nResult {index}"
            )
            print(
                f"Source: "
                f"{result['source_type']}"
            )
            print(
                f"Record: "
                f"{result['source_record_id']}"
            )
            print(
                f"Distance: "
                f"{result['distance']:.4f}"
            )
            print(
                f"Text: "
                f"{result['text']}"
            )

        print_section(
            "HYBRID RETRIEVAL TEST COMPLETE"
        )

    finally:
        retriever.close()


if __name__ == "__main__":
    main()