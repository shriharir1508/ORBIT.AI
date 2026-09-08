from pathlib import Path
import sqlite3
from datetime import datetime
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"

DB_PATH = DATABASE_DIR / "orbit.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"


def load_csv(folder, filename):
    path = PROCESSED_DIR / folder / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path)


def create_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)

    return connection


def parse_status_date(value):
    """
    Convert the two date formats present in the source
    issue tracker into ISO format: YYYY-MM-DD.
    """

    value = str(value).strip()

    # Format:
    # 2026_01_06_00_00_00
    if value.startswith("2026_"):
        try:
            parsed = datetime.strptime(
                value,
                "%Y_%m_%d_%H_%M_%S"
            )
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # Format:
    # 6_13_2026
    try:
        parsed = datetime.strptime(
            value,
            "%m_%d_%Y"
        )
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        return None


def normalize_issue_history(issues):

    metadata_columns = {
        "s_no",
        "issue",
        "branch",
        "link"
    }

    status_columns = [
        column
        for column in issues.columns
        if column not in metadata_columns
    ]

    records = []

    for _, row in issues.iterrows():

        for status_column in status_columns:

            status = row[status_column]

            if pd.isna(status):
                status = None
            else:
                status = str(status).strip()

            records.append({
                "issue_id": row["s_no"],
                "issue": row["issue"],
                "branch": row["branch"],
                "link": row["link"],
                "status_date_raw": str(status_column),
                "status": status
            })

    history = pd.DataFrame(records)

    history["status_date"] = (
        history["status_date_raw"]
        .apply(parse_status_date)
    )

    return history[
        [
            "issue_id",
            "issue",
            "branch",
            "link",
            "status_date",
            "status"
        ]
    ]


def load_data(connection):

    # Branch master
    patients = load_csv(
        "DB1_PATIENTS",
        "patients_followup.csv"
    )

    branches = (
        patients[
            ["branch", "branch_city"]
        ]
        .drop_duplicates()
        .rename(
            columns={
                "branch": "branch_name",
                "branch_city": "city"
            }
        )
    )

    branches.to_sql(
        "branch_master",
        connection,
        if_exists="append",
        index=False
    )

    # Employees
    employees = load_csv(
        "DB4_OPERATIONS",
        "employee_list.csv"
    )

    employees = employees.rename(
        columns={
            "employee_id": "employee_id",
            "employee_name": "employee_name",
            "branch": "branch_name",
            "designation": "designation",
            "status": "status"
        }
    )

    employees.to_sql(
        "employee_master",
        connection,
        if_exists="append",
        index=False
    )

    # Patient followup
    patients.to_sql(
        "patient_followup",
        connection,
        if_exists="append",
        index=False
    )

    # Attrition reference
    attrition = load_csv(
        "DB1_PATIENTS",
        "patient_attrition_reasons.csv"
    )

    attrition.to_sql(
        "patient_attrition_reference",
        connection,
        if_exists="append",
        index=False
    )

    # Marketing
    marketing = load_csv(
        "DB2_MARKETING",
        "total_meta_leads.csv"
    )

    marketing.to_sql(
        "marketing_campaign",
        connection,
        if_exists="append",
        index=False
    )

    # Sales
    sales = load_csv(
        "DB3_SALES",
        "total_sales_report.csv"
    )

    sales.to_sql(
        "sales",
        connection,
        if_exists="append",
        index=False
    )

    # Brand assessment
    brand = load_csv(
        "DB3_SALES",
        "brand_assessment.csv"
    )

    brand.to_sql(
        "brand_assessment",
        connection,
        if_exists="append",
        index=False
    )

    # Issue management — preserve original source structure
    issues = load_csv(
        "DB4_OPERATIONS",
        "clinic_issues_manager.csv"
    )

    issues.to_sql(
        "issue_management",
        connection,
        if_exists="append",
        index=False
    )

    # Issue management — normalized history
    issue_history = normalize_issue_history(issues)

    issue_history.to_sql(
        "issue_management_history",
        connection,
        if_exists="replace",
        index=False
    )


def verify_database(connection):

    tables = [
        "branch_master",
        "employee_master",
        "patient_followup",
        "patient_attrition_reference",
        "marketing_campaign",
        "sales",
        "brand_assessment",
        "issue_management",
        "issue_management_history",
    ]

    print("\n" + "=" * 70)
    print("ORBIT.AI — DATABASE BUILD")
    print("=" * 70)

    for table in tables:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count} rows")

    print("=" * 70)
    print(f"Database created: {DB_PATH}")


def main():

    connection = create_database()

    try:
        load_data(connection)
        connection.commit()
        verify_database(connection)
    finally:
        connection.close()


if __name__ == "__main__":
    main()