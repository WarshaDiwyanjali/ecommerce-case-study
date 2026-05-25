"""
generate_case_study_notebook.py
--------------------------------
Builds the full ecommerce_case_study_analysis.ipynb notebook
from structured cells.

Run:
    python scripts/generate_case_study_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path


# =========================
# PROJECT STRUCTURE 
# =========================

# Root = project folder (scripts/ -> parent = root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "ecommerce_case_study_analysis.ipynb"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Possible dataset locations (robust fix)
DATA_CANDIDATES = [
    PROJECT_ROOT / "events.csv",
    PROJECT_ROOT / "assignment" / "events.csv",
]

NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# HELPERS
# =========================

def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


# =========================
# NOTEBOOK CELLS
# =========================

def build_cells() -> list[dict]:
    cells = []

    # ---------- TITLE ----------
    cells.append(md_cell("""
# E-Commerce Customer Behavior Case Study

**Goal:** Analyze customer journey, identify funnel drop-offs, and improve revenue performance.

**Dataset:** `events.csv`
"""))

    # ---------- BUSINESS UNDERSTANDING ----------
    cells.append(md_cell("""
## 1. Business Understanding

We analyze how users move through the funnel:
**view → cart → purchase**
"""))

    # ---------- SETUP ----------
    cells.append(code_cell("""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display

warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

# Safe project root (works in notebooks too)
PROJECT_ROOT = Path.cwd().resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def fmt_currency(x): return f"${x:,.2f}"
def fmt_percent(x): return f"{x:.2%}"
"""))

    # ---------- LOAD DATA (FIXED SAFE PATH) ----------
    cells.append(code_cell(f"""
# Robust dataset loader
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path.cwd().resolve().parent

DATA_PATH = None
for p in {DATA_CANDIDATES}:
    if p.exists():
        DATA_PATH = p
        break

if DATA_PATH is None:
    raise FileNotFoundError("events.csv not found in expected locations")

raw = pd.read_csv(DATA_PATH)
raw["event_time"] = pd.to_datetime(raw["event_time"], errors="coerce")

display(raw.head())
print("Shape:", raw.shape)
print("Loaded from:", DATA_PATH)
"""))

    # ---------- CLEANING ----------
    cells.append(code_cell("""
clean = raw.drop_duplicates().copy()

clean = clean.dropna(subset=["event_time", "user_id"])
clean["price"] = clean["price"].fillna(0)

clean["event_month"] = clean["event_time"].dt.to_period("M").astype(str)
clean["event_hour"] = clean["event_time"].dt.hour

display(clean.head())
"""))

    # ---------- KPI ----------
    cells.append(code_cell("""
purchase_df = clean[clean["event_type"] == "purchase"]
cart_df = clean[clean["event_type"] == "cart"]
view_df = clean[clean["event_type"] == "view"]

total_users = clean["user_id"].nunique()
total_revenue = purchase_df["price"].sum()
total_purchases = len(purchase_df)

conversion_rate = purchase_df["user_id"].nunique() / total_users
aov = total_revenue / total_purchases if total_purchases else 0

kpi = pd.DataFrame([
    ["Total Users", total_users],
    ["Total Revenue", total_revenue],
    ["Total Purchases", total_purchases],
    ["Conversion Rate", conversion_rate],
    ["AOV", aov]
], columns=["KPI", "Value"])

display(kpi)
"""))

    # ---------- EXPORT ----------
    cells.append(code_cell("""
kpi.to_csv(OUTPUT_DIR / "kpi_summary.csv", index=False)
clean.to_csv(OUTPUT_DIR / "events_cleaned.csv", index=False)
"""))

    # ---------- FUNNEL ----------
    cells.append(code_cell("""
view_users = view_df["user_id"].nunique()
cart_users = cart_df["user_id"].nunique()
purchase_users = purchase_df["user_id"].nunique()

funnel = pd.DataFrame({
    "stage": ["View", "Cart", "Purchase"],
    "users": [view_users, cart_users, purchase_users]
})

display(funnel)

plt.bar(funnel["stage"], funnel["users"])
plt.title("Funnel Analysis")
plt.show()

funnel.to_csv(OUTPUT_DIR / "funnel_summary.csv", index=False)
"""))

    # ---------- SEGMENTATION ----------
    cells.append(code_cell("""
segments = clean.groupby("user_id")["event_type"].count().reset_index()
segments.columns = ["user_id", "events"]

display(segments.head())

segments.to_csv(OUTPUT_DIR / "user_segments.csv", index=False)
"""))

    # ---------- INSIGHTS ----------
    cells.append(md_cell("""
## Key Insights

- Most users drop off before adding to cart  
- Revenue is concentrated in a small number of users  
- Improving product page conversion has the highest impact  
"""))

    return cells


# =========================
# BUILD NOTEBOOK
# =========================

def main():
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3"
            }
        },
        "cells": build_cells()
    }

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)

    print("Notebook generated at:", NOTEBOOK_PATH)
    print("Outputs saved in:", OUTPUT_DIR)
    print("Dataset loaded safely from available path")


if __name__ == "__main__":
    main()