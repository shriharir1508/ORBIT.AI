from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"


def load_csv(folder, filename):
    path = PROCESSED_DIR / folder / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing processed file: {path}")

    return pd.read_csv(path)


def check_madipakkam(df, name):
    """Check every text field for unexpected Madipakkam references."""
    findings = []

    for column in df.select_dtypes(include=["string"]).columns:
        mask = df[column].str.contains(
            "madipakkam",
            case=False,
            na=False
        )

        count = int(mask.sum())

        if count:
            findings.append(
                f"{name}.{column}: {count} Madipakkam occurrence(s)"
            )

    return findings


def check_duplicates(df, name):
    duplicate_count = int(df.duplicated().sum())

    return (
        f"{name}: {duplicate_count} fully duplicated row(s)"
    )


def check_missing(df, name):
    missing = int(df.isna().sum().sum())

    return (
        f"{name}: {missing} missing cell(s)"
    )


def validate_patients(report):
    df = load_csv(
        "DB1_PATIENTS",
        "patients_followup.csv"
    )

    report.append(
        f"PATIENTS: {len(df)} rows × {len(df.columns)} columns"
    )

    report.append(
        check_duplicates(df, "Patients Followup")
    )

    report.append(
        check_missing(df, "Patients Followup")
    )

    if "patient_id" in df.columns:
        duplicate_patient_ids = int(
            df["patient_id"].duplicated().sum()
        )

        report.append(
            f"Patient ID repeated rows: "
            f"{duplicate_patient_ids}"
        )

    report.extend(
        check_madipakkam(
            df,
            "Patients Followup"
        )
    )


def validate_marketing(report):
    df = load_csv(
        "DB2_MARKETING",
        "total_meta_leads.csv"
    )

    report.append(
        f"MARKETING: {len(df)} rows × {len(df.columns)} columns"
    )

    report.append(
        check_duplicates(
            df,
            "Total Meta Leads"
        )
    )

    report.append(
        check_missing(
            df,
            "Total Meta Leads"
        )
    )

    report.append(
        "Marketing attribution: "
        "No reliable patient-level or branch-level "
        "attribution field identified."
    )

    report.extend(
        check_madipakkam(
            df,
            "Total Meta Leads"
        )
    )


def validate_sales(report):
    df = load_csv(
        "DB3_SALES",
        "total_sales_report.csv"
    )

    report.append(
        f"SALES: {len(df)} rows × {len(df.columns)} columns"
    )

    report.append(
        check_duplicates(
            df,
            "Total Sales Report"
        )
    )

    report.append(
        check_missing(
            df,
            "Total Sales Report"
        )
    )

    required = {
        "standard_treatment",
        "variable_treatment",
        "total_treatment",
        "total_medicine_sales",
        "total_sales",
    }

    if required.issubset(df.columns):

        treatment_check = (
            df["standard_treatment"]
            + df["variable_treatment"]
            == df["total_treatment"]
        )

        sales_check = (
            df["total_treatment"]
            + df["total_medicine_sales"]
            == df["total_sales"]
        )

        report.append(
            f"Treatment reconciliation failures: "
            f"{int((~treatment_check).sum())}"
        )

        report.append(
            f"Total sales reconciliation failures: "
            f"{int((~sales_check).sum())}"
        )

    report.extend(
        check_madipakkam(
            df,
            "Total Sales Report"
        )
    )


def validate_operations(report):
    folder = PROCESSED_DIR / "DB4_OPERATIONS"

    files = list(folder.glob("*.csv"))

    report.append(
        f"OPERATIONS: {len(files)} processed sheets"
    )

    operational_forms = {
        "bo_frm_01_opening.csv",
        "bo_frm_07_a_housekeeping.csv",
        "bo_frm_07_b_housekeeping.csv",
        "bo_frm_21_closing.csv",
        "bo_frm_22a_branch_report.csv",
        "bo_frm_20b_petty_cash.csv",
    }

    for file in sorted(files):

        df = pd.read_csv(file)

        report.append(
            f"{file.name}: "
            f"{len(df)} rows × {len(df.columns)} columns"
        )

        report.append(
            check_duplicates(
                df,
                file.stem
            )
        )

        report.extend(
            check_madipakkam(
                df,
                file.stem
            )
        )

        if file.name in operational_forms:
            non_empty_rows = int(
                df.dropna(how="all").shape[0]
            )

            report.append(
                f"{file.name}: "
                f"{non_empty_rows} non-empty extracted row(s); "
                f"requires structural form inspection before "
                f"database loading."
            )


def validate_employee_data(report):
    df = load_csv(
        "DB4_OPERATIONS",
        "employee_list.csv"
    )

    report.append(
        f"EMPLOYEES: {len(df)} rows × {len(df.columns)} columns"
    )

    report.append(
        check_duplicates(
            df,
            "Employee List"
        )
    )

    if "employee_id" in df.columns:
        report.append(
            f"Unique Employee IDs: "
            f"{df['employee_id'].nunique()}"
        )


def main():

    VALIDATION_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report = []

    report.append("ORBIT.AI — DATA VALIDATION REPORT")
    report.append("=" * 70)

    validate_patients(report)
    validate_marketing(report)
    validate_sales(report)
    validate_operations(report)
    validate_employee_data(report)

    report.append("")
    report.append("VALIDATION COMPLETE")
    report.append(
        "No source files were modified."
    )

    output_path = (
        VALIDATION_DIR /
        "validation_report.txt"
    )

    output_path.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\n".join(report))
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()