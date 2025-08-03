import json
import pandas as pd
from pathlib import Path
from string import Template  # keep if you use it later

# --------------------
# Paths
# --------------------
repo_root = Path(__file__).resolve().parents[1]
old_csv = repo_root / "sample_data" / "old_customers.csv"
new_csv = repo_root / "sample_data" / "new_customers.csv"

out_dir = repo_root / "output"
out_dir.mkdir(exist_ok=True)

out_html = repo_root / "sample-report.html"

# --------------------
# Verification config (manual sign-off)
# --------------------
verification_path = repo_root / "verification.json"
verification = {"checks": {}, "mismatches": []}
if verification_path.exists():
    verification = json.loads(verification_path.read_text(encoding="utf-8"))

ver_checks = verification.get("checks", {})
ver_rows = verification.get("mismatches", [])
ver_rows_set = {
    (str(r.get("customer_id")), str(r.get("column", "")).lower())
    for r in ver_rows
    if r.get("verified")
}

# --------------------
# Config
# --------------------
primary_key = "customer_id"
required_fields = ["email"]
# columns to compare cell-by-cell (present in BOTH files)
compare_columns = ["name", "email", "dob", "balance", "status"]

# known, acceptable differences
ALLOWED_DELETIONS = {"C100105", "C100521", "C100683", "C100690", "C100717"}
ALLOWED_ADDITIONS = {"NEW0", "NEW1", "NEW2"}

# inline table row cap
INLINE_MAX_ROWS = 5000  # to match your "first 5000" feel

# --------------------
# Load
# --------------------
old_df = pd.read_csv(old_csv, dtype=str)
new_df = pd.read_csv(new_csv, dtype=str)

if primary_key not in old_df.columns or primary_key not in new_df.columns:
    raise KeyError("Primary key missing in one of the CSVs")

# normalize key
old_df[primary_key] = old_df[primary_key].astype(str).str.strip()
new_df[primary_key] = new_df[primary_key].astype(str).str.strip()

old_pk = old_df[primary_key]
new_pk = new_df[primary_key]

# basic counts (raw)
old_total = len(old_df)
new_total = len(new_df)

# --------------------
# Checks (row count, dups, nulls)
# --------------------
results = []

# 1) Row count match (adjusted by allowlists)
adj_old = old_total - old_pk.isin(ALLOWED_DELETIONS).sum()
adj_new = new_total - new_pk.isin(ALLOWED_ADDITIONS).sum()
row_match = adj_old == adj_new
results.append((
    "Row count match",
    "PASS" if row_match else "FAIL",
    f"Old={old_total} (adj {adj_old}), New={new_total} (adj {adj_new})"
))

# 2) Primary key duplicates
old_dups_ct = old_pk.duplicated().sum()
new_dups_ct = new_pk.duplicated().sum()
pk_ok = (old_dups_ct == 0) and (new_dups_ct == 0)
results.append((
    "Primary key duplicates",
    "PASS" if pk_ok else "FAIL",
    f"Old dupes={old_dups_ct}, New dupes={new_dups_ct}"
))

# 3) Nulls in required fields
null_rows = []
null_ok = True
for col in required_fields:
    old_val = old_df[col].isna().sum() if col in old_df.columns else "col-missing"
    new_val = new_df[col].isna().sum() if col in new_df.columns else "col-missing"
    if isinstance(old_val, int) and old_val > 0:
        null_ok = False
    if isinstance(new_val, int) and new_val > 0:
        null_ok = False
    null_rows.append({"field": col, "old_nulls": old_val, "new_nulls": new_val})

results.append((
    "Nulls in required fields",
    "PASS" if null_ok else "WARN",
    "; ".join([f"{r['field']}: Old={r['old_nulls']}, New={r['new_nulls']}" for r in null_rows])
))
