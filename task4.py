"""
csv_processor.py  —  Automate CSV cleaning & analysis
Dataset : Kaggle Superstore Sales Dataset
Columns used : Order ID, Customer Name, Order Date, Sales, Profit,
               Category, Region, Quantity, Discount

Usage:
    python csv_processor.py --input "Sample - Superstore.csv" --output clean_superstore.csv


"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Step 1 : Load ──────────────────────────────────────────────────────────────
def load_csv(path: Path) -> pd.DataFrame:
    log.info("Loading file: %s", path)
    # Superstore CSV is sometimes encoded in latin-1
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    log.info("  Rows loaded : %d  |  Columns : %d", len(df), len(df.columns))
    return df


# ── Step 2 : Clean ─────────────────────────────────────────────────────────────
def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    # Strip whitespace from all column names
    df.columns = df.columns.str.strip()

    # Drop rows missing critical columns
    df = df.dropna(subset=["Order ID", "Sales"])

    # Ensure Sales, Profit, Quantity, Discount are numeric
    for col in ["Sales", "Profit", "Quantity", "Discount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where Sales is still null after coercion
    df = df.dropna(subset=["Sales"])

    # Standardise Customer Name casing
    if "Customer Name" in df.columns:
        df["Customer Name"] = df["Customer Name"].str.strip().str.title()

    # Parse Order Date and Ship Date
    for datecol in ["Order Date", "Ship Date"]:
        if datecol in df.columns:
            df[datecol] = pd.to_datetime(df[datecol], errors="coerce", dayfirst=False)

    log.info("  Rows after cleaning : %d  (removed %d)", len(df), before - len(df))
    return df


# ── Step 3 : Enrich ────────────────────────────────────────────────────────────
def enrich(df: pd.DataFrame) -> pd.DataFrame:
    # Extract year-month from Order Date
    if "Order Date" in df.columns:
        df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)
        df["Order Year"]  = df["Order Date"].dt.year

    # Flag orders with negative profit (loss-making)
    if "Profit" in df.columns:
        df["Is Loss"] = df["Profit"] < 0

    # Revenue after discount
    if {"Sales", "Discount"}.issubset(df.columns):
        df["Net Revenue"] = (df["Sales"] * (1 - df["Discount"])).round(2)

    return df


# ── Step 4 : Summarise ─────────────────────────────────────────────────────────
def summarise(df: pd.DataFrame) -> None:
    print("\n" + "=" * 56)
    print("  SUPERSTORE SALES — SUMMARY REPORT")
    print("=" * 56)
    print(f"  Total orders      : {len(df):,}")
    print(f"  Total revenue     : ${df['Sales'].sum():,.2f}")

    if "Profit" in df.columns:
        total_profit = df["Profit"].sum()
        margin       = (total_profit / df["Sales"].sum()) * 100
        loss_rows    = df["Is Loss"].sum()
        print(f"  Total profit      : ${total_profit:,.2f}  (margin: {margin:.1f}%)")
        print(f"  Loss-making rows  : {loss_rows}")

    if "Category" in df.columns:
        print("\n  Sales by category:")
        cat = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
        for name, val in cat.items():
            bar = "█" * int(val / 50000)
            print(f"    {name:<20} {bar:<15}  ${val:,.0f}")

    if "Region" in df.columns:
        print("\n  Sales by region:")
        reg = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
        for name, val in reg.items():
            print(f"    {name:<15}  ${val:,.0f}")

    if "Customer Name" in df.columns:
        print("\n  Top 5 customers by spend:")
        top = (
            df.groupby("Customer Name")["Sales"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        for name, val in top.items():
            print(f"    {name:<25}  ${val:,.2f}")

    if "Order Month" in df.columns:
        print("\n  Monthly revenue (last 12 months):")
        monthly = df.groupby("Order Month")["Sales"].sum().tail(12)
        for month, rev in monthly.items():
            bar = "▓" * int(rev / 10000)
            print(f"    {month}  {bar}  ${rev:,.0f}")

    print("=" * 56 + "\n")


# ── Step 5 : Save ──────────────────────────────────────────────────────────────
def save(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)
    log.info("Clean file saved → %s  (%d rows)", path, len(df))


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean and analyse the Kaggle Superstore sales CSV."
    )
    parser.add_argument("--input",  required=True, help="Path to Superstore CSV")
    parser.add_argument("--output", required=True, help="Path for cleaned output CSV")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        log.error("File not found: %s", input_path)
        sys.exit(1)

    df = load_csv(input_path)
    df = clean(df)
    df = enrich(df)
    summarise(df)
    save(df, output_path)
    log.info("Done.")


if __name__ == "__main__":
    main()