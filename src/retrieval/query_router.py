import re


STRUCTURED_PATTERNS = [
    r"\bsales\b",
    r"\brevenue\b",
    r"\bmedicine sales\b",
    r"\btreatment sales\b",
    r"\bspend\b",
    r"\bcampaign\b",
    r"\bimpressions\b",
    r"\breach\b",
    r"\bresults\b",
    r"\bpatients?\b",
    r"\bhigh[- ]follow[- ]up risk\b",
    r"\bfollow[- ]up risk\b",
    r"\battrition\b",
    r"\bfrequency\b",
    r"\bemployees?\b",
    r"\bbranch(?:es)?\b",
]


SEMANTIC_PATTERNS = [
    r"\bremark\b",
    r"\bfeedback\b",
    r"\bfinding(?:s)?\b",
    r"\bexperience\b",
    r"\bbrand(?:ing)?\b",
    r"\bcommunication\b",
    r"\bdigital presence\b",
    r"\bcontent\b",
    r"\btestimonial(?:s)?\b",
    r"\bhousekeeping\b",
    r"\bcleanliness\b",
]


HYBRID_PATTERNS = [
    r"\bissue(?:s)?\b",
    r"\bproblem(?:s)?\b",
    r"\breason(?:s)?\b",
    r"\bwhy\b",
    r"\bneed attention\b",
]


BRANCH_PATTERNS = [
    r"madurai anna nagar",
    r"madurai anna busstand",
    r"chennai anna nagar",
    r"chennai alandur",
]


def normalize_query(query):
    return re.sub(
        r"\s+",
        " ",
        str(query).strip().lower()
    )


def find_matches(query, patterns):

    return [
        pattern
        for pattern in patterns
        if re.search(pattern, query)
    ]


def route_query(query):

    normalized = normalize_query(query)

    structured_matches = find_matches(
        normalized,
        STRUCTURED_PATTERNS
    )

    semantic_matches = find_matches(
        normalized,
        SEMANTIC_PATTERNS
    )

    hybrid_matches = find_matches(
        normalized,
        HYBRID_PATTERNS
    )

    branch_matches = find_matches(
        normalized,
        BRANCH_PATTERNS
    )

    # Explicit qualitative/problem language
    # requires semantic evidence.
    if hybrid_matches:
        route = "HYBRID"

    # A known branch combined with a
    # semantic question requires both
    # structured filtering and semantic retrieval.
    elif branch_matches and semantic_matches:
        route = "HYBRID"

    # Pure structured questions.
    elif structured_matches and not semantic_matches:
        route = "STRUCTURED"

    # Pure semantic questions.
    elif semantic_matches and not structured_matches:
        route = "SEMANTIC"

    # Questions containing both kinds of
    # evidence requirements.
    elif structured_matches and semantic_matches:
        route = "HYBRID"

    # Ambiguous questions use both retrieval
    # methods rather than making a risky assumption.
    else:
        route = "HYBRID"

    return {
        "query": query,
        "route": route,
        "structured_matches": structured_matches,
        "semantic_matches": semantic_matches,
        "hybrid_matches": hybrid_matches,
        "branch_matches": branch_matches,
    }


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — QUERY ROUTER TEST")
    print("=" * 70)

    test_queries = [
        "What are the total sales by branch?",
        "Which patients are at high follow-up risk?",
        "What are the main patient attrition reasons?",
        "What are the major brand communication problems?",
        "What operational and patient issues need attention?",
        "What are the key problems at Madurai Anna Nagar?",
        "What are the cleanliness findings at Chennai Alandur?",
        "Give me an overview of the organisation.",
    ]

    for query in test_queries:

        result = route_query(query)

        print("\n" + "-" * 70)
        print(f"QUERY: {result['query']}")
        print(f"ROUTE: {result['route']}")

        print(
            f"STRUCTURED MATCHES: "
            f"{result['structured_matches']}"
        )

        print(
            f"SEMANTIC MATCHES: "
            f"{result['semantic_matches']}"
        )

        print(
            f"HYBRID MATCHES: "
            f"{result['hybrid_matches']}"
        )

        print(
            f"BRANCH MATCHES: "
            f"{result['branch_matches']}"
        )

    print("\n" + "=" * 70)
    print("QUERY ROUTER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()