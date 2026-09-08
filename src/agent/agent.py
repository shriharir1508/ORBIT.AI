from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai

from src.retrieval.query_router import route_query
from src.retrieval.retriever import HybridRetriever
from src.retrieval.evidence import EvidencePackage


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class OrbitAgent:

    def __init__(self):

        load_dotenv(ENV_FILE)

        self.api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        if self.api_key.startswith("PASTE_"):
            raise ValueError(
                "GEMINI_API_KEY still contains "
                "the placeholder value."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

        self.retriever = HybridRetriever()

    def detect_branch(self, query):

        branches = [
            "Madurai Anna Nagar",
            "Madurai Anna Busstand",
            "Chennai Anna Nagar",
            "Chennai Alandur",
        ]

        normalized_query = query.lower()

        for branch in branches:

            if branch.lower() in normalized_query:
                return branch

        return None

    def collect_evidence(
        self,
        query,
        route
    ):

        evidence = EvidencePackage()

        branch = self.detect_branch(query)

        normalized_query = query.lower()

        is_sales_question = (
            "sales" in normalized_query
            or "revenue" in normalized_query
        )

        is_risk_question = (
            "high risk" in normalized_query
            or "follow-up risk" in normalized_query
            or "follow up risk" in normalized_query
        )

        is_attrition_question = (
            "attrition" in normalized_query
        )

        is_marketing_question = (
            "marketing" in normalized_query
            or "campaign" in normalized_query
            or "impressions" in normalized_query
            or "reach" in normalized_query
            or "spend" in normalized_query
        )

        is_issue_question = (
            "issue" in normalized_query
            or "issues" in normalized_query
            or "problem" in normalized_query
            or "problems" in normalized_query
            or "cleanliness" in normalized_query
            or "housekeeping" in normalized_query
        )

        # ---------------------------------------------------------
        # STRUCTURED RETRIEVAL
        # ---------------------------------------------------------

        if is_sales_question:

            sales = (
                self.retriever.sales_by_branch(branch)
                if branch
                else self.retriever.sales_by_branch()
            )

            evidence.add_structured_results(
                sales
            )

        if is_risk_question:

            patients = (
                self.retriever.high_risk_patients(
                    branch_name=branch,
                    limit=20
                )
            )

            for patient in patients:

                evidence.add_structured_results(
                    [patient]
                )

        if is_attrition_question:

            attrition = (
                self.retriever.attrition_reasons()
            )

            evidence.add_structured_results(
                attrition
            )

        if is_marketing_question:

            marketing = (
                self.retriever.marketing_summary()
            )

            evidence.add_structured_results(
                [{
                    "source_type":
                        "marketing_campaign",
                    "source_record_id":
                        "AGGREGATE",
                    **marketing
                }]
            )

        if is_issue_question and branch:

            issues = (
                self.retriever.branch_issues(
                    branch
                )
            )

            evidence.add_structured_results(
                issues
            )

        # ---------------------------------------------------------
        # SEMANTIC RETRIEVAL
        # ---------------------------------------------------------

        should_use_semantic = (
            route in {
                "SEMANTIC",
                "HYBRID"
            }
        )

        if (
            should_use_semantic
            and not (
                is_issue_question
                and branch
            )
            and not is_attrition_question
            and not is_risk_question
        ):

            semantic_results = (
                self.retriever.semantic_search(
                    query,
                    n_results=5
                )
            )

            evidence.add_semantic_results(
                semantic_results
            )

        return evidence

    def build_prompt(
        self,
        query,
        route,
        evidence
    ):

        evidence_text = evidence.to_text()

        prompt = f"""
You are ORBIT.AI, an organisational intelligence
and management decision-support assistant.

User question:
{query}

Query route:
{route}

Retrieved evidence:
{evidence_text}

STRICT EVIDENCE RULES:

1. Use only the retrieved evidence above.

2. Never invent facts, figures, branches,
   patient information, causes, or business
   conditions.

3. Treat structured evidence as authoritative
   for numerical values, counts, branch filters,
   and categorical values.

4. When a specific branch is named, do not
   introduce evidence from another branch unless
   the user explicitly asks for comparison.

5. When patient records are provided as a subset,
   explicitly state that they are a subset.

6. Do not present an inference as a FACT.

7. Use exactly these labels:

FACT:
Directly supported facts.

INFERENCE:
Reasonable interpretation, or None.

UNKNOWN:
Important information not established by
the evidence, or None.

MANAGEMENT IMPLICATION:
Evidence-based management implication or
practical option.

8. Do not infer profit margins, profitability,
   causal relationships, treatment effectiveness,
   inventory requirements, or other business
   conditions unless the evidence directly
   supports them.

9. Do not claim patient-level marketing
   attribution.

10. Do not treat attrition reference frequencies
    as direct attribution to individual patient
    records.

11. Do not treat blank operational issue
    statuses as resolved.

12. Recommendations must be framed as options
    derived from the evidence, not established
    facts.

13. Keep the response concise and management
    oriented.
"""

        return prompt

    def ask(self, query):

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        routing = route_query(query)

        route = routing["route"]

        evidence = self.collect_evidence(
            query,
            route
        )

        prompt = self.build_prompt(
            query,
            route,
            evidence
        )

        interaction = (
            self.client.interactions.create(
                model=self.model,
                input=prompt
            )
        )

        return {
            "query": query,
            "route": route,
            "evidence_count":
                evidence.count(),
            "evidence":
                evidence.to_dict(),
            "answer":
                interaction.output_text,
        }

    def close(self):

        self.retriever.close()