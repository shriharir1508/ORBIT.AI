from pathlib import Path
import pandas as pd
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


DATASETS = {
    "DB1_PATIENTS": "DB 1 - Patients Followup.xlsx",
    "DB2_MARKETING": "DB 2 - Total meta campaigns report.xlsx",
    "DB3_SALES": "DB 3 - Total Sales Report.xlsx",
    "DB4_OPERATIONS": "DB 4 - Operations Layer.xlsx",
}


# Operational sheets that require later structural interpretation.
OPERATIONAL_TEMPLATE_SHEETS = {
    "BO-FRM-01 Opening",
    "BO-FRM-07 A Housekeeping",
    "BO-FRM-07 B Housekeeping",
    "BO-FRM-07 B Housekeeping ",
    "BO-FRM-21 Closing",
    "BO-FRM-22A Branch Report",
    "BO-FRM-20B Petty Cash",
}


def standardize_column_name(column):
    """Convert column names into consistent snake_case."""
    column = str(column).strip()
    column = re.sub(r"[^A-Za-z0-9]+", "_", column)
    column = re.sub(r"_+", "_", column)
    return column.strip("_").lower()


def standardize_columns(df):
    df = df.copy()
    df.columns = [standardize_column_name(col) for col in df.columns]
    return df


def standardize_text(df):
    """Strip accidental whitespace from textual values."""
    df = df.copy()

    for column in df.columns:
        if pd.api.types.is_string_dtype(df[column]):
            df[column] = df[column].str.strip()

    return df


def standardize_known_branches(df):
    """
    Standardise only the known spelling variation.
    Never infer incomplete branch names.
    """
    df = df.copy()

    for column in df.columns:
        if "branch" in column:
            df[column] = df[column].replace({
                "Madurai Anna Bustand": "Madurai Anna Busstand"
            })

    return df


def clean_dataframe(df):
    """
    Safe standardisation only.
    No generic date parsing.
    No row deletion.
    No fabricated values.
    """
    df = standardize_columns(df)
    df = standardize_text(df)
    df = standardize_known_branches(df)

    return df


def process_workbook(dataset_name, filename):
    source_path = RAW_DATA_DIR / filename

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )

    workbook = pd.ExcelFile(
        source_path,
        engine="openpyxl"
    )

    output_directory = PROCESSED_DATA_DIR / dataset_name
    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for sheet_name in workbook.sheet_names:

        df = pd.read_excel(
            source_path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

        original_shape = df.shape

        cleaned_df = clean_dataframe(df)

        # Operational forms are preserved exactly as extracted.
        # Their rows will be structurally assessed before database loading.
        is_operational_template = (
            sheet_name.strip() in
            {s.strip() for s in OPERATIONAL_TEMPLATE_SHEETS}
        )

        output_file = output_directory / (
            f"{standardize_column_name(sheet_name)}.csv"
        )

        cleaned_df.to_csv(
            output_file,
            index=False
        )

        results.append({
            "sheet": sheet_name,
            "input_rows": original_shape[0],
            "input_columns": original_shape[1],
            "output_rows": cleaned_df.shape[0],
            "output_columns": cleaned_df.shape[1],
            "operational_template": is_operational_template,
        })

    return results


def main():
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\n" + "=" * 70)
    print("ORBIT.AI — DATA CLEANING")
    print("=" * 70)

    for dataset_name, filename in DATASETS.items():

        print(f"\nProcessing: {filename}")

        results = process_workbook(
            dataset_name,
            filename
        )

        for result in results:

            template_flag = (
                " [FORM — INSPECT BEFORE DATABASE]"
                if result["operational_template"]
                else ""
            )

            print(
                f"  {result['sheet']}: "
                f"{result['input_rows']} → "
                f"{result['output_rows']} rows | "
                f"{result['input_columns']} → "
                f"{result['output_columns']} columns"
                f"{template_flag}"
            )

    print("\n" + "=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)
    print(
        "Raw files were not modified."
    )
    print(
        "Operational forms require structural validation "
        "before database loading."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()