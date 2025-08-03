import pandas as pd
from pathlib import Path
from string import Template

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
ALLOWED_DELETIONS = {"C100105", "C100521", "C100683", "C100690", "C100717"}
ALLOWED_ADDITIONS = {"NEW0", "NEW1", "NEW2"}

# --------------------
# Load
# --------------------
old_df = pd.read_csv(old_csv, dtype=str)
new_df = pd.read_csv(new_csv, dtype=str)

# Normalize PK for matching (strings, trimmed)
if primary_key not in old_df.columns:
    raise KeyError(f"Primary key '{primary_key}' not found in OLD CSV: {old_csv.name}")
if primary_key not in new_df.columns:
    raise KeyError(f"Primary key '{primary_key}' not found in NEW CSV: {new_csv.name}")

old_pk = old_df[primary_key].astype(str).str.strip()
new_pk = new_df[primary_key].astype(str).str.strip()

# --------------------
# Checks
# --------------------
results = []

# 1) Row count match (adjusted by allowlists)
adj_old = len(old_df) - old_pk.isin(ALLOWED_DELETIONS).sum()
adj_new = len(new_df) - new_pk.isin(ALLOWED_ADDITIONS).sum()
row_match = (adj_old == adj_new)
results.append((
    "Row count match",
    "PASS" if row_match else "FAIL",
    f"Old={len(old_df)} (adj {adj_old}), New={len(new_df)} (adj {adj_new})"
))

# 2) Primary key duplicates (on normalized PK)
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

# --------------------
# Deltas (exclude allowlisted IDs)
# --------------------
old_keys = set(old_pk)
new_keys = set(new_pk)

missing_mask = (~old_pk.isin(new_keys)) & (~old_pk.isin(ALLOWED_DELETIONS))  # in old not new, not allowed
extra_mask   = (~new_pk.isin(old_keys)) & (~new_pk.isin(ALLOWED_ADDITIONS))  # in new not old, not allowed

missing_in_new = old_df.loc[missing_mask].copy()
extra_in_new   = new_df.loc[extra_mask].copy()

# --------------------
# Proof artifacts
# --------------------
# Row counts (with adjustments)
row_counts = pd.DataFrame([
    {
        "dataset": "OLD",
        "raw_count": len(old_df),
        "allowlisted_ids": int(old_pk.isin(ALLOWED_DELETIONS).sum()),
        "adjusted_count": adj_old,
    },
    {
        "dataset": "NEW",
        "raw_count": len(new_df),
        "allowlisted_ids": int(new_pk.isin(ALLOWED_ADDITIONS).sum()),
        "adjusted_count": adj_new,
    },
])
row_counts_path = out_dir / "row_counts.csv"
row_counts.to_csv(row_counts_path, index=False)

# Duplicates detail (full rows for duplicated PKs)
def duplicate_rows(df, pk_series):
    dup_keys = pk_series[pk_series.duplicated(keep=False)]
    if dup_keys.empty:
        return pd.DataFrame(columns=df.columns)
    return df.loc[pk_series.isin(set(dup_keys))].copy().sort_values(by=pk_series.name)

dups_old_df = duplicate_rows(old_df, old_pk.rename(primary_key))
dups_new_df = duplicate_rows(new_df, new_pk.rename(primary_key))
duplicates_old_path = out_dir / "duplicates_old.csv"
duplicates_new_path = out_dir / "duplicates_new.csv"
dups_old_df.to_csv(duplicates_old_path, index=False)
dups_new_df.to_csv(duplicates_new_path, index=False)

# Nulls summary
nulls_summary = pd.DataFrame(null_rows)
nulls_summary_path = out_dir / "nulls_summary.csv"
nulls_summary.to_csv(nulls_summary_path, index=False)

# Schema comparison
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
schema_cmp = pd.DataFrame(schema_rows)
schema_cmp_path = out_dir / "schema_comparison.csv"
schema_cmp.to_csv(schema_cmp_path, index=False)

# Missing/Extra (unexpected only)
missing_path = out_dir / "missing_in_new.csv"
extra_path   = out_dir / "extra_in_new.csv"
missing_in_new.to_csv(missing_path, index=False)
extra_in_new.to_csv(extra_path, index=False)
missing_count = len(missing_in_new)
extra_count   = len(extra_in_new)

# --------------------
# HTML helpers
# --------------------
def df_html_preview(df, cols=None, n=10):
    if df.empty:
        return "<em>None</em>"
    if cols:
        cols = [c for c in cols if c in df.columns]
        if cols:
            df = df[cols]
    return df.head(n).to_html(index=False, border=0)

def badge(status: str) -> str:
    cls = "ok" if status == "PASS" else ("warn" if status == "WARN" else "fail")
    return f'<span class="{cls}">{status}</span>'

rows_html = "".join(
    f"<tr><td>{name}</td><td>{badge(status)}</td><td>{notes}</td></tr>"
    for name, status, notes in results
)

likely_cols = [primary_key, "email", "name", "first_name", "last_name"]
missing_preview = df_html_preview(missing_in_new, cols=likely_cols)
extra_preview   = df_html_preview(extra_in_new,   cols=likely_cols)

# Differences section (show only if non-empty)
if missing_count == 0 and extra_count == 0:
    differences_section = ""
else:
    differences_section = f"""
    <div class="section">
      <h2>Key Differences (unexpected)</h2>
      <p><strong>Missing in NEW:</strong> {missing_count} rows &nbsp;—&nbsp;
         <a href="output/missing_in_new.csv">download CSV</a></p>
      {missing_preview}
      <p style="margin-top:1rem;"><strong>Extra in NEW:</strong> {extra_count} rows &nbsp;—&nbsp;
         <a href="output/extra_in_new.csv">download CSV</a></p>
      {extra_preview}
    </div>
    """

# Proofs section (always shown)
proofs = [
    ("Row counts (raw/adjusted)", "output/row_counts.csv"),
    ("Primary key duplicates — OLD", "output/duplicates_old.csv"),
    ("Primary key duplicates — NEW", "output/duplicates_new.csv"),
    ("Nulls in required fields", "output/nulls_summary.csv"),
    ("Schema comparison", "output/schema_comparison.csv"),
    ("Missing in NEW (unexpected)", "output/missing_in_new.csv"),
    ("Extra in NEW (unexpected)", "output/extra_in_new.csv"),
]
proofs_html = "<ul>" + "".join(
    f'<li><a href="{href}">{label}</a></li>' for label, href in proofs
) + "</ul>"

# --------------------
# Build HTML (Template is safe with CSS braces and %)
# --------------------
html_tpl = Template("""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Data Migration Validation Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; max-width: 1100px; }
    h1 { margin-top: 0; }
    table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f6f6f6; }
    .ok { color: #1a7f37; font-weight: 600; }
    .warn { color: #d97706; font-weight: 600; }
    .fail { color: #b91c1c; font-weight: 600; }
    .meta { color: #555; margin-top: .5rem; }
    .section { margin-top: 1.5rem; }
    a { text-decoration: none; }
    .small { font-size: 0.9rem; color: #666; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Data Migration Validation Report</h1>
    <div class="meta">Source files: $old_name → $new_name</div>
    <div class="small meta">
      Exceptions applied:
      <strong>Allowed deletions</strong> = $allowed_deletions &nbsp; | &nbsp;
      <strong>Allowed additions</strong> = $allowed_additions
    </div>

    <table>
      <thead>
        <tr><th>Check</th><th>Status</th><th>Notes</th></tr>
      </thead>
      <tbody>
        $rows_html
      </tbody>
    </table>

    $differences_section

    <div class="section">
      <h2>Proofs (downloadable)</h2>
      $proofs_html
    </div>
  </div>
</body>
</html>
""")

html = html_tpl.substitute(
    old_name=old_csv.name,
    new_name=new_csv.name,
    rows_html=rows_html,
    allowed_deletions=", ".join(sorted(ALLOWED_DELETIONS)) or "None",
    allowed_additions=", ".join(sorted(ALLOWED_ADDITIONS)) or "None",
    differences_section=differences_section,
    proofs_html=proofs_html,
)

out_html.write_text(html, encoding="utf-8")

print(f"Wrote: {out_html}")
print(f"Row counts -> {row_counts_path}")
print(f"Duplicates OLD -> {duplicates_old_path} | NEW -> {duplicates_new_path}")
print(f"Nulls summary -> {nulls_summary_path}")
print(f"Schema comparison -> {schema_cmp_path}")
print(f"Missing in NEW -> {missing_path}")
print(f"Extra in NEW   -> {extra_path}")
