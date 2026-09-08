from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


DATASETS = {
    "DB1_PATIENTS": "DB 1 - Patients Followup.xlsx",
    "DB2_MARKETING": "DB 2 - Total meta campaigns report.xlsx",
    "DB3_SALES": "DB 3 - Total Sales Report.xlsx",
    "DB4_OPERATIONS": "DB 4 - Operations Layer.xlsx",
}


def load_workbook(filename: str) -> dict[str, pd.DataFrame]:
    """Load every sheet from an Excel workbook without modifying the source."""
    filepath = RAW_DATA_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Source file not found: {filepath}")

    workbook = pd.ExcelFile(filepath, engine="openpyxl")

    return {
        sheet_name: pd.read_excel(
            filepath,
            sheet_name=sheet_name,
            engine="openpyxl",
        )
        for sheet_name in workbook.sheet_names
    }


def load_all_datasets() -> dict[str, dict[str, pd.DataFrame]]:
    """Load all four ORBIT.AI source workbooks."""
    datasets = {}

    for dataset_name, filename in DATASETS.items():
        datasets[dataset_name] = load_workbook(filename)

    return datasets


def print_inventory(datasets: dict[str, dict[str, pd.DataFrame]]) -> None:
    """Print a simple source inventory."""
    print("\n" + "=" * 70)
    print("ORBIT.AI — SOURCE DATA INVENTORY")
    print("=" * 70)

    for dataset_name, sheets in datasets.items():
        print(f"\n{dataset_name}")

        for sheet_name, dataframe in sheets.items():
            print(
                f"  {sheet_name}: "
                f"{dataframe.shape[0]} rows × {dataframe.shape[1]} columns"
            )

    print("\n" + "=" * 70)
    print("INGESTION CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    all_data = load_all_datasets()
    print_inventory(all_data)