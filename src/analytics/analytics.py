from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "database" / "orbit.db"


def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    return sqlite3.connect(DB_PATH)


def patient_kpis(conn):
    df = pd.read_sql_query(
        "SELECT * FROM patient_followup",
        conn
    )

    return {
        "total_patient_records": len(df),

        "high_followup_risk": int(
            (
                df["followup_risk"]
                .astype(str)
                .str.strip()
                .str.lower()
                == "high"
            ).sum()
        ),

        "active_followup": int(
            df["followup_status"]
            .astype(str)
            .str.contains(
                "active",
                case=False,
                na=False
            )
            .sum()
        ),

        "continuing_treatment": int(
            df["treatment_continuation_status"]
            .astype(str)
            .str.contains(
                "continue",
                case=False,
                na=False
            )
            .sum()
        ),
    }


def branch_patient_summary(conn):
    return pd.read_sql_query(
        """
        SELECT
            branch AS branch_name,
            COUNT(*) AS patient_records
        FROM patient_followup
        GROUP BY branch
        ORDER BY patient_records DESC
        """,
        conn
    )


def sales_kpis(conn):
    df = pd.read_sql_query(
        "SELECT * FROM sales",
        conn
    )

    return {
        "total_sales": float(
            df["total_sales"].sum()
        ),

        "total_treatment_sales": float(
            df["total_treatment"].sum()
        ),

        "total_medicine_sales": float(
            df["total_medicine_sales"].sum()
        ),
    }


def branch_sales_summary(conn):
    return pd.read_sql_query(
        """
        SELECT
            branch AS branch_name,
            SUM(total_sales) AS total_sales,
            SUM(total_treatment) AS total_treatment,
            SUM(total_medicine_sales) AS medicine_sales
        FROM sales
        GROUP BY branch
        ORDER BY total_sales DESC
        """,
        conn
    )


def marketing_kpis(conn):
    df = pd.read_sql_query(
        "SELECT * FROM marketing_campaign",
        conn
    )

    return {
        "campaign_records": len(df),

        "total_impressions": int(
            df["impressions"].sum()
        ),

        "total_reach": int(
            df["reach"].sum()
        ),

        "total_spend": float(
            df["total_amount"].sum()
        ),

        "total_results": int(
            df["results"].sum()
        ),
    }


def attrition_summary(conn):
    return pd.read_sql_query(
        """
        SELECT
            rank,
            patient_attrition_reason,
            reason_type,
            frequency
        FROM patient_attrition_reference
        ORDER BY rank
        """,
        conn
    )


def issue_summary(conn):
    df = pd.read_sql_query(
        "SELECT * FROM issue_management",
        conn
    )

    metadata_columns = {
        "s_no",
        "issue",
        "branch",
        "link"
    }

    status_columns = [
        column
        for column in df.columns
        if column not in metadata_columns
    ]

    unresolved_status_entries = 0

    for column in status_columns:
        unresolved_status_entries += int(
            df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("unresolved")
            .sum()
        )

    return {
        "total_issue_records": len(df),

        "unresolved_status_entries": (
            unresolved_status_entries
        ),

        "status_columns_checked": len(
            status_columns
        ),
    }


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — ANALYTICS ENGINE")
    print("=" * 70)

    conn = get_connection()

    try:

        patients = patient_kpis(conn)
        sales = sales_kpis(conn)
        marketing = marketing_kpis(conn)
        issues = issue_summary(conn)

        print("\nPATIENT KPIs")
        print("-" * 40)

        for key, value in patients.items():
            print(f"{key}: {value}")

        print("\nSALES KPIs")
        print("-" * 40)

        for key, value in sales.items():
            print(f"{key}: {value:,.2f}")

        print("\nMARKETING KPIs")
        print("-" * 40)

        for key, value in marketing.items():
            print(f"{key}: {value}")

        print("\nISSUE KPIs")
        print("-" * 40)

        for key, value in issues.items():
            print(f"{key}: {value}")

        print("\nBRANCH PATIENT SUMMARY")
        print("-" * 40)

        print(
            branch_patient_summary(conn)
            .to_string(index=False)
        )

        print("\nBRANCH SALES SUMMARY")
        print("-" * 40)

        print(
            branch_sales_summary(conn)
            .to_string(index=False)
        )

        print("\nATTRITION REFERENCE")
        print("-" * 40)

        print(
            attrition_summary(conn)
            .to_string(index=False)
        )

        print("\n" + "=" * 70)
        print("ANALYTICS CHECK COMPLETE")
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()