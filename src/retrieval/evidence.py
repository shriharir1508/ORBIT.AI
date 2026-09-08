from dataclasses import dataclass, asdict


@dataclass
class EvidenceItem:
    source_type: str
    source_record_id: str
    evidence: str
    retrieval_method: str


class EvidencePackage:

    def __init__(self):
        self.items = []

    def add(
        self,
        source_type,
        source_record_id,
        evidence,
        retrieval_method
    ):

        item = EvidenceItem(
            source_type=str(source_type),
            source_record_id=str(
                source_record_id
            ),
            evidence=str(evidence),
            retrieval_method=str(
                retrieval_method
            )
        )

        self.items.append(item)

    def add_semantic_results(
        self,
        results
    ):

        for result in results:

            self.add(
                source_type=result[
                    "source_type"
                ],
                source_record_id=result[
                    "source_record_id"
                ],
                evidence=result["text"],
                retrieval_method="SEMANTIC"
            )

    def add_structured_results(
        self,
        results
    ):

        for result in results:

            source_type = result.get(
                "source_type",
                "structured"
            )

            source_record_id = result.get(
                "source_record_id",
                "N/A"
            )

            evidence = " | ".join(
                f"{key}: {value}"
                for key, value in result.items()
                if key not in {
                    "source_type",
                    "source_record_id"
                }
            )

            self.add(
                source_type=source_type,
                source_record_id=source_record_id,
                evidence=evidence,
                retrieval_method="STRUCTURED"
            )

    def count(self):
        return len(self.items)

    def to_dict(self):

        return [
            asdict(item)
            for item in self.items
        ]

    def to_text(self):

        if not self.items:
            return "No evidence retrieved."

        sections = []

        for index, item in enumerate(
            self.items,
            start=1
        ):

            sections.append(
                f"Evidence {index}\n"
                f"Source type: "
                f"{item.source_type}\n"
                f"Source record ID: "
                f"{item.source_record_id}\n"
                f"Retrieval method: "
                f"{item.retrieval_method}\n"
                f"Evidence: "
                f"{item.evidence}"
            )

        return "\n\n".join(sections)