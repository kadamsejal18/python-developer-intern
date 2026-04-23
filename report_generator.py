"""
report_generator.py  —  Auto-generate an HTML report from Superstore CSV
Reads the cleaned Superstore CSV and produces a self-contained HTML report
with KPI cards, category breakdown, and a top-customers table.

Usage:
    python report_generator.py --data clean_superstore.csv --output report.html

Install:
    pip install pandas jinja2
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Template

# ── HTML Template ──────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f4f6f9;
      color: #333;
      padding: 32px 24px;
    }
    .container { max-width: 1000px; margin: 0 auto; }

    /* Header */
    .header {
      background: #1a3c6e;
      color: white;
      padding: 28px 32px;
      border-radius: 12px;
      margin-bottom: 28px;
    }
    .header h1 { font-size: 26px; font-weight: 700; margin-bottom: 6px; }
    .header p  { font-size: 13px; opacity: 0.75; }

    /* KPI Cards */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }
    .kpi {
      background: white;
      border-radius: 10px;
      padding: 20px 22px;
      border-left: 4px solid #1a3c6e;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .kpi .value {
      font-size: 28px;
      font-weight: 700;
      color: #1a3c6e;
      margin-bottom: 4px;
    }
    .kpi .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }

    /* Section Cards */
    .card {
      background: white;
      border-radius: 10px;
      padding: 24px 28px;
      margin-bottom: 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .card h2 {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 18px;
      color: #1a3c6e;
      border-bottom: 2px solid #e8ecf2;
      padding-bottom: 10px;
    }

    /* Bar chart rows */
    .bar-row {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
      font-size: 13px;
    }
    .bar-label  { width: 160px; color: #555; flex-shrink: 0; }
    .bar-track  { flex: 1; background: #eef1f6; border-radius: 4px; height: 14px; margin: 0 12px; }
    .bar-fill   { height: 14px; border-radius: 4px; background: #1a3c6e; }
    .bar-value  { width: 90px; text-align: right; color: #333; font-weight: 500; }

    /* Tables */
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    thead tr { background: #f0f4fa; }
    th { padding: 10px 14px; text-align: left; font-weight: 600; color: #555;
         border-bottom: 2px solid #dde3ee; }
    td { padding: 9px 14px; border-bottom: 1px solid #eee; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #f8f9fc; }
    .profit-pos { color: #2e7d32; font-weight: 500; }
    .profit-neg { color: #c62828; font-weight: 500; }

    /* Footer */
    .footer {
      text-align: center;
      font-size: 12px;
      color: #aaa;
      margin-top: 32px;
    }
  </style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>{{ title }}</h1>
    <p>Generated on {{ generated_at }} &nbsp;|&nbsp; {{ total_rows }} orders analysed</p>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    {% for kpi in kpis %}
    <div class="kpi">
      <div class="value">{{ kpi.value }}</div>
      <div class="label">{{ kpi.label }}</div>
    </div>
    {% endfor %}
  </div>

  <!-- Sales by Category -->
  <div class="card">
    <h2>Sales by Category</h2>
    {% for row in category_rows %}
    <div class="bar-row">
      <span class="bar-label">{{ row.name }}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width: {{ row.pct }}%"></div>
      </div>
      <span class="bar-value">${{ row.value }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Sales by Region -->
  <div class="card">
    <h2>Sales by Region</h2>
    {% for row in region_rows %}
    <div class="bar-row">
      <span class="bar-label">{{ row.name }}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width: {{ row.pct }}%"></div>
      </div>
      <span class="bar-value">${{ row.value }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Top 10 Customers -->
  <div class="card">
    <h2>Top 10 Customers by Sales</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Customer Name</th>
          <th>Total Sales</th>
          <th>Total Profit</th>
          <th>Orders</th>
        </tr>
      </thead>
      <tbody>
        {% for row in top_customers %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ row.name }}</td>
          <td>${{ row.sales }}</td>
          <td class="{{ 'profit-pos' if row.profit_raw >= 0 else 'profit-neg' }}">${{ row.profit }}</td>
          <td>{{ row.orders }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Monthly Trend Table -->
  <div class="card">
    <h2>Monthly Sales Trend (last 12 months)</h2>
    <table>
      <thead><tr><th>Month</th><th>Revenue</th><th>Orders</th><th>Avg Order Value</th></tr></thead>
      <tbody>
        {% for row in monthly %}
        <tr>
          <td>{{ row.month }}</td>
          <td>${{ row.revenue }}</td>
          <td>{{ row.orders }}</td>
          <td>${{ row.avg }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="footer">
    Automated Report &mdash; Generated by report_generator.py &mdash; {{ generated_at }}
  </div>

</div>
</body>
</html>
"""


# ── Data helpers ───────────────────────────────────────────────────────────────
def fmt(value: float) -> str:
    return f"{value:,.0f}"


def build_bar_rows(series: pd.Series) -> list[dict]:
    max_val = series.max()
    return [
        {
            "name":  name,
            "value": fmt(val),
            "pct":   round(val / max_val * 100) if max_val else 0,
        }
        for name, val in series.items()
    ]


def build_kpis(df: pd.DataFrame) -> list[dict]:
    kpis = [
        {"label": "Total Orders",   "value": f"{len(df):,}"},
        {"label": "Total Revenue",  "value": f"${df['Sales'].sum():,.0f}"},
    ]
    if "Profit" in df.columns:
        profit  = df["Profit"].sum()
        margin  = (profit / df["Sales"].sum() * 100) if df["Sales"].sum() else 0
        kpis += [
            {"label": "Total Profit",  "value": f"${profit:,.0f}"},
            {"label": "Profit Margin", "value": f"{margin:.1f}%"},
        ]
    if "Customer Name" in df.columns:
        kpis.append({"label": "Unique Customers", "value": f"{df['Customer Name'].nunique():,}"})
    return kpis


def build_top_customers(df: pd.DataFrame) -> list[dict]:
    grp = df.groupby("Customer Name").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
        orders=("Order ID", "nunique"),
    ).sort_values("sales", ascending=False).head(10)

    rows = []
    for name, r in grp.iterrows():
        rows.append({
            "name":       name,
            "sales":      fmt(r["sales"]),
            "profit":     fmt(r["profit"]),
            "profit_raw": r["profit"],
            "orders":     int(r["orders"]),
        })
    return rows


def build_monthly(df: pd.DataFrame) -> list[dict]:
    if "Order Month" not in df.columns:
        return []
    grp = df.groupby("Order Month").agg(
        revenue=("Sales", "sum"),
        orders=("Order ID", "nunique"),
    ).tail(12)
    rows = []
    for month, r in grp.iterrows():
        rows.append({
            "month":   month,
            "revenue": fmt(r["revenue"]),
            "orders":  int(r["orders"]),
            "avg":     fmt(r["revenue"] / r["orders"]) if r["orders"] else "0",
        })
    return rows


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML report from cleaned Superstore CSV.")
    parser.add_argument("--data",   required=True, help="Path to cleaned CSV (output of csv_processor.py)")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--title",  default="Superstore Sales Report")
    args = parser.parse_args()

    data_path   = Path(args.data)
    output_path = Path(args.output)

    if not data_path.exists():
        print(f"ERROR: File not found: {data_path}")
        raise SystemExit(1)

    df = pd.read_csv(data_path)
    # Re-parse date column if present
    if "Order Date" in df.columns:
        df["Order Date"]  = pd.to_datetime(df["Order Date"],  errors="coerce")
        df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)

    html = Template(HTML_TEMPLATE).render(
        title          = args.title,
        generated_at   = datetime.now().strftime("%d %b %Y  %H:%M"),
        total_rows     = f"{len(df):,}",
        kpis           = build_kpis(df),
        category_rows  = build_bar_rows(df.groupby("Category")["Sales"].sum().sort_values(ascending=False))
                         if "Category" in df.columns else [],
        region_rows    = build_bar_rows(df.groupby("Region")["Sales"].sum().sort_values(ascending=False))
                         if "Region" in df.columns else [],
        top_customers  = build_top_customers(df) if "Customer Name" in df.columns else [],
        monthly        = build_monthly(df),
    )

    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport saved → {output_path}  ({len(html):,} bytes)")
    print("Open the file in any browser to view your report.\n")


if __name__ == "__main__":
    main()
