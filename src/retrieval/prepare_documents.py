from pathlib import Path
import sqlite3
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "database" / "orbit.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "rag_documents.json"


def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def build_patient_documents(connection):
    rows = connection.execute(
        """
        SELECT
            rowid,
            branch,
            branch_city,
            disease,
            disease_category,
            sitting_count,
            followup_status,
            remark,
            days_since_first_sitting,
            engagement_level,
            contactability,
            followup_risk,
            treatment_continuation_status
        FROM patient_followup
        WHERE remark IS NOT NULL
          AND TRIM(remark) <> ''
          AND LOWER(TRIM(remark)) <> 'no remark'
        """
    ).fetchall()

    documents = []

    for row in rows:
        (
            record_id,
            branch,
            branch_city,
            disease,
            disease_category,
            sitting_count,
            followup_status,
            remark,
            days_since_first_sitting,
            engagement_level,
            contactability,
            followup_risk,
            treatment_continuation_status,
        ) = row

        text = (
            "Patient follow-up record. "
            f"Branch: {clean_text(branch)}. "
            f"City: {clean_text(branch_city)}. "
            f"Disease: {clean_text(disease)}. "
            f"Disease category: {clean_text(disease_category)}. "
            f"Sitting count: {clean_text(sitting_count)}. "
            f"Follow-up status: {clean_text(followup_status)}. "
            f"Engagement level: {clean_text(engagement_level)}. "
            f"Contactability: {clean_text(contactability)}. "
            f"Follow-up risk: {clean_text(followup_risk)}. "
            f"Treatment continuation status: "
            f"{clean_text(treatment_continuation_status)}. "
            f"Days since first sitting: "
            f"{clean_text(days_since_first_sitting)}. "
            f"Remark: {clean_text(remark)}."
        )

        documents.append({
            "document_id": f"PATIENT_{record_id}",
            "source_type": "patient_followup",
            "source_record_id": str(record_id),
            "text": text,
            "metadata": {
                "branch": clean_text(branch),
                "branch_city": clean_text(branch_city),
                "disease": clean_text(disease),
                "disease_category": clean_text(
                    disease_category
                ),
                "followup_risk": clean_text(
                    followup_risk
                ),
                "contactability": clean_text(
                    contactability
                ),
                "engagement_level": clean_text(
                    engagement_level
                ),
                "treatment_continuation_status": clean_text(
                    treatment_continuation_status
                ),
            }
        })

    return documents


def build_attrition_documents(connection):
    rows = connection.execute(
        """
        SELECT
            rank,
            patient_attrition_reason,
            reason_type,
            frequency
        FROM patient_attrition_reference
        ORDER BY rank
        """
    ).fetchall()

    documents = []

    for rank, reason, reason_type, frequency in rows:

        text = (
            "Patient attrition reference. "
            f"Attrition reason: {clean_text(reason)}. "
            f"Reason type: {clean_text(reason_type)}. "
            f"Frequency in source reference: "
            f"{clean_text(frequency)}."
        )

        documents.append({
            "document_id": f"ATTRITION_{rank}",
            "source_type": "patient_attrition_reference",
            "source_record_id": str(rank),
            "text": text,
            "metadata": {
                "reason_type": clean_text(reason_type),
                "frequency": frequency,
            }
        })

    return documents


def build_brand_documents(connection):
    rows = connection.execute(
        """
        SELECT
            rowid,
            dimension,
            parameter,
            score,
            date_assessed,
            findings
        FROM brand_assessment
        WHERE findings IS NOT NULL
          AND TRIM(findings) <> ''
        """
    ).fetchall()

    documents = []

    for (
        record_id,
        dimension,
        parameter,
        score,
        date_assessed,
        findings,
    ) in rows:

        text = (
            "Brand assessment finding. "
            f"Dimension: {clean_text(dimension)}. "
            f"Parameter: {clean_text(parameter)}. "
            f"Score recorded in source: {clean_text(score)}. "
            f"Assessment date: {clean_text(date_assessed)}. "
            f"Finding: {clean_text(findings)}."
        )

        documents.append({
            "document_id": f"BRAND_{record_id}",
            "source_type": "brand_assessment",
            "source_record_id": str(record_id),
            "text": text,
            "metadata": {
                "dimension": clean_text(dimension),
                "parameter": clean_text(parameter),
                "score": score,
                "date_assessed": clean_text(
                    date_assessed
                ),
            }
        })

    return documents


def build_issue_documents(connection):
    rows = connection.execute(
        """
        SELECT
            s_no,
            issue,
            branch,
            link
        FROM issue_management
        WHERE issue IS NOT NULL
          AND TRIM(issue) <> ''
        ORDER BY s_no
        """
    ).fetchall()

    documents = []

    for issue_id, issue, branch, link in rows:

        status_rows = connection.execute(
            """
            SELECT
                status_date,
                status
            FROM issue_management_history
            WHERE issue_id = ?
            ORDER BY status_date
            """,
            (issue_id,)
        ).fetchall()

        unresolved_dates = [
            date
            for date, status in status_rows
            if clean_text(status).lower() == "unresolved"
        ]

        latest_status = None

        for date, status in status_rows:
            if clean_text(status) != "":
                latest_status = clean_text(status)

        text = (
            "Operational issue. "
            f"Branch: {clean_text(branch)}. "
            f"Issue: {clean_text(issue)}. "
            f"Latest recorded status: "
            f"{clean_text(latest_status)}. "
            f"Number of unresolved status observations: "
            f"{len(unresolved_dates)}."
        )

        documents.append({
            "document_id": f"ISSUE_{issue_id}",
            "source_type": "operational_issue",
            "source_record_id": str(issue_id),
            "text": text,
            "metadata": {
                "branch": clean_text(branch),
                "link": clean_text(link),
                "latest_status": clean_text(
                    latest_status
                ),
                "unresolved_status_observations": len(
                    unresolved_dates
                ),
                "status_dates": unresolved_dates,
            }
        })

    return documents


def build_all_documents(connection):
    documents = []

    documents.extend(
        build_patient_documents(connection)
    )

    documents.extend(
        build_attrition_documents(connection)
    )

    documents.extend(
        build_brand_documents(connection)
    )

    documents.extend(
        build_issue_documents(connection)
    )

    return documents


def save_documents(documents):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2
        )


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — RAG DOCUMENT PREPARATION")
    print("=" * 70)

    connection = get_connection()

    try:
        documents = build_all_documents(
            connection
        )

        save_documents(documents)

        print(
            f"\nTotal RAG documents: {len(documents)}"
        )

        counts = {}

        for document in documents:
            source_type = document["source_type"]
            counts[source_type] = (
                counts.get(source_type, 0) + 1
            )

        print("\nDOCUMENT COUNTS")
        print("-" * 40)

        for source_type, count in counts.items():
            print(
                f"{source_type}: {count}"
            )

        print(
            f"\nOutput: {OUTPUT_FILE}"
        )

        print("\n" + "=" * 70)
        print("RAG DOCUMENT PREPARATION COMPLETE")
        print("=" * 70)

    finally:
        connection.close()


if __name__ == "__main__":
    main()