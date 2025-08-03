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
# ... previous code ...

results.append((
    "Nulls in required fields",
    "PASS" if null_ok else "WARN",
    "; ".join([f"{r['field']}: Old={r['old_nulls']}, New={r['new_nulls']}” for r in null_rows])
))

# >>> PASTE PART 3 HERE <<<
# --------------------
# Membership deltas (excluding allowlists)
# --------------------
old_keys = set(old_pk)
new_keys = set(new_pk)

only_in_old_keys = (old_keys - new_keys) - ALLOWED_DELETIONS
only_in_new_keys = (new_keys - old_keys) - ALLOWED_ADDITIONS

only_in_old = old_df[old_df[primary_key].isin(only_in_old_keys)].copy()
only_in_new = new_df[new_df[primary_key].isin(only_in_new_keys)].copy()

# Save CSV proofs (and legacy names for compatibility)
(only_in_old.sort_values(primary_key)
 .to_csv(out_dir / "only_in_old.csv", index=False))
(only_in_new.sort_values(primary_key)
 .to_csv(out_dir / "only_in_new.csv", index=False))

only_in_old.to_csv(out_dir / "missing_in_new.csv", index=False)
only_in_new.to_csv(out_dir / "extra_in_new.csv", index=False)

# --------------------
# Other proof artifacts
# --------------------
import pandas as pd  # safe if already imported

row_counts = pd.DataFrame([
    {"dataset": "OLD", "raw_count": old_total,
     "allowlisted_ids": int(old_pk.isin(ALLOWED_DELETIONS).sum()),
     "adjusted_count": adj_old},
    {"dataset": "NEW", "raw_count": new_total,
     "allowlisted_ids": int(new_pk.isin(ALLOWED_ADDITIONS).sum()),
     "adjusted_count": adj_new},
])
row_counts.to_csv(out_dir / "row_counts.csv", index=False)

def duplicate_rows(df, pk_series):
    dup_keys = pk_series[pk_series.duplicated(keep=False)]
    if dup_keys.empty:
        return pd.DataFrame(columns=df.columns)
    return df[df[primary_key].isin(set(dup_keys))].copy().sort_values(primary_key)

duplicate_rows(old_df, old_pk).to_csv(out_dir / "duplicates_old.csv", index=False)
duplicate_rows(new_df, new_pk).to_csv(out_dir / "duplicates_new.csv", index=False)

pd.DataFrame(null_rows).to_csv(out_dir / "nulls_summary.csv", index=False)

all_cols = sorted(set(old_df.columns) | set(new_df.columns))
schema_rows = []
for c in all_cols:
    schema_rows.append({
        "column": c,
        "present_in_old": c in old_df.columns,
        "present_in_new": c in new_df.columns,
        "dtype_old": str(old_df[c].dtype) if c in old_df.columns else "",
        "dtype_new": str(new_df[c].dtype) if c in new_df.columns else "",
    })
pd.DataFrame(schema_rows).to_csv(out_dir / "schema_comparison.csv", index=False)

# ... next parts (mismatches, HTML) go below ...
