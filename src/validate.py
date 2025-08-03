import csv
import json
import hashlib
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from string import Template

import pandas as pd

# --------------------
# Paths
# --------------------
repo_root = Path(__file__).resolve().parents[1]
old_csv = repo_root / "sample_data" / "old_customers.csv"
new_csv = repo_root / "sample_data" / "new_customers.csv"

out_dir = repo_root / "output"
out_dir.mkdir(exist_ok=True)

# HTML at repo root so GitHub Pages can serve it
out_html = repo_root / "sample-report.html"

# --------------------
# Config (edit for your data)
# --------------------
primary_key = "customer_id"        # change if needed
required_fields = ["email"]        # add more fields if needed

# Expected differences (allowlist)
# - Deletions: present in OLD, intentionally absent in NEW
# - Additions: present in NEW, intentionally absent in OLD
ALLOWED_DELETIONS = {"C100105", "C100521", "C100683", "C100690", "C100717"}
ALLOWED_ADDITIONS = {"NEW0", "NEW1", "NEW2"}

# --------------------
# Helpers
# --------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def df_to_csv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def safe_get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        return "unknown"

# --------------------
# Load
# --------------------
# Read as strings to avoid type coercion (e.g., leading zeros, large ints)
old_df = pd.read_csv(old_csv, dtype=str)
new_df = pd.read_csv(new_csv, dtype=str)

# Normalize PK for matching (strings, trimmed)
if primary_key not in old_df.columns:
    raise KeyError(f"Primary key '{primary_key}' not found in OLD CSV: {old_csv.name}")
if primary_key not in new_df.columns:
    raise KeyError(f"Primary key '{primary_key}' not found in NEW CSV: {new_csv.name}")

old_df[primary_key] = old_df[primary_key].astype(str).str.strip()
new_df[primary_key] = new_df[primary_key].astype(str).str.strip()

old_pk = old_df[primary_key]
new_pk = new_df[primary_key]

# --------------------
# Checks + Proofs
# --------------------
results = []

# Row counts (with allowlists)
allowed_del_count = old_pk.isin(ALLOWED_DELETIONS).sum()
allowed_add_count = new_pk.isin(ALLOWED_ADDITIONS).sum()
adj_old = len(old_df) - allowed_del_count
adj_new = len(new_df) - allowed_add_count
row_match = (adj_old == adj_new)
results.append((
    "Row count match",
    "PASS" if row_match else "FAIL",
    f"Old={len(old_df)} (adj {adj_old}; allowed deletions {allowed_del_count}), "
    f"New={len(new_df)} (adj {adj_new}; allowed additions {allowed_add_count})"
))

# Proof file: row counts
row_counts_csv = out_dir / "row_counts.csv"
write_csv(
    row_counts_csv,
    [{
        "old_rows": len(old_df),
        "new_rows": len(new_df),
        "allowed_deletions": int(allowed_del_count),
        "allowed_additions": int(allowed_add_count),
        "adjusted_old": int(adj_old),
        "adjusted_new": int(adj_new),
        "match": bool(row_match),
    }],
    fieldnames=["old_rows", "new_rows", "allowed_deletions", "allowed_additions",
                "adjusted_old", "adjusted_new", "match"]
)

# Duplicates
old_dup_mask = old_pk.duplicated(keep=False)
new_dup_mask = new_pk.duplicated(keep=False)
old_dups_df = old_df.loc[old_dup_mask].sort_values(by=primary_key)
new_dups_df = new_df.loc[new_dup_mask].sort_values(by=primary_key)
old_dups = old_dups_df.shape[0]
new_dups = new_dups_df.shape[0]
pk_ok = (old_dups == 0) and (new_dups == 0)
results.append(("Primary key duplicates", "PASS" if pk_ok else "FAIL",
                f"Old dupes={old_dups}, New dupes={new_dups}"))

# Proof files: duplicates
duplicates_old_csv = out_dir / "duplicates_old.csv"
duplicates_new_csv = out_dir / "duplicates_new.csv"
df_to_csv(duplicates_old_csv, old_dups_df)
df_to_csv(duplicates_new_csv, new_dups_df)

# Nulls in required fields
null_notes = []
null_rows = []
null_ok = True
for col in required_fields:
    old_nulls = old_df[col].isna().sum() if col in old_df.columns else None
    new_nulls = new_df[col].isna().sum() if col in new_df.columns else None
    null_notes.append(f"{col}: Old={old_nulls if old_nulls is not None else 'col-missing'}, "
                      f"New={new_nulls if new_nulls is not None else 'col-missing'}")
    if isinstance(old_nulls, int) and old_nulls > 0: null_ok = False
    if isinstance(new_nulls, int) and new_nulls > 0: null_ok = False
    null_rows.append({
        "field": col,
        "old_nulls": old_nulls if old_nulls is not None else "col-missing",
        "new_nulls": new_nulls if new_nulls is not None else "col-missing",
    })

results.append(("Nulls in required fields", "PASS" if null_ok else "WARN", "; ".join(null_notes)))

# Proof file: nulls
nulls_summary_csv = out_dir / "nulls_summary.csv"
write_csv(nulls_summary_csv, null_rows, fieldnames=["field", "old_nulls", "new_nulls"])

# Schema comparison (columns + dtypes)
old_cols = set(old_df.columns)
new_cols = set(new_df.columns)
schema_rows = []
for col in sorted(old_cols | new_cols):
    schema_rows.append({
        "column": col,
        "in_old": col in old_cols,
        "in_new": col in new_cols,
        "old_dtype": str(old_df[col].dtype) if col in old_cols else "",
        "new_dtype": str(new_df[col].dtype) if col in new_cols else "",
    })
schema_csv = out_dir / "schema_comparison.csv"
write_csv(schema_csv, schema_rows, fieldnames=["column", "in_old", "in_new", "old_dtype", "new_dtype"])

# Deltas (exclude allowlisted IDs)
old_keys = set(old_pk)
new_keys = set(new_pk)

missing_mask = (~old_pk.isin(new_keys)) & (~old_pk.isin(ALLOWED_DELETIONS))  # in old not new, not allowed
extra_mask   = (~new_pk.isin(old_keys)) & (~new_pk.isin(ALLOWED_ADDITIONS))  # in new not old, not allowed

missing_in_new = old_df.loc[missing_mask].copy()
extra_in_new   = new_df.loc[extra_mask].copy()

missing_path = out_dir / "missing_in_new.csv"
extra_path   = out_dir / "extra_in_new.csv"
df_to_csv(missing_path, missing_in_new)
df_to_csv(extra_path,   extra_in_new)

missing_count = len(missing_in_new)
extra_count   = len(extra_in_new)

# Optional: possible rekeys (same email, different PK)
possible_rekeys_csv = out_dir / "possible_rekeys.csv"
if "email" in old_df.columns and "email" in new_df.columns:
    old_email_map = old_df.set_index("email", drop=False)
    new_email_map = new_df.set_index("email", drop=False)
    shared_emails = old_email_map.index.intersection(new_email_map.index)
    rows = []
    for em in shared_emails:
        old_row = old_email_map.loc[em]
        new_row = new_email_map.loc[em]
        # handle potential duplicates by taking first occurrence
        if isinstance(old_row, pd.DataFrame):_
