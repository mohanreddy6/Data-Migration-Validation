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

# Max rows to show inline for big tables
INLINE_MAX_ROWS = 20

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
# Proof artifacts (CSV files)
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
def df_preview(df: pd.DataFrame, max_rows: int = INLINE_MAX_ROWS, cols=None) -> str:
    if df.empty:
        return "<em>None</em>"
    show = df
    if cols:
        cols = [c for c in cols if c in df.columns]
        if cols:
            show = show[cols]
    if len(show) > max_rows:
        head = show.head(max_rows)
        html = head.to_html(index=False, border=0)
        return f'<div>{html}<div class="small">Showing first {max_rows} of {len(show)} rows</div></div>'
    return show.to_html(index=False, border=0)

def section_with_download(title: str, csv_href: str, table_html: str, count_note: str = "") -> str:
    note = f" — {count_note}" if count_note else ""
    # Use details/summary to make large sections collapsible
    return f"""
    <details class="section" open>
      <summary><strong>{title}</strong> <span class="small">{note}</span> — <a href="{csv_href}">download CSV</a></summary>
      <div style="margin-top:.75rem">{table_html}</div>
    </details>
    """

def badge(status: str) -> str:
    cls = "ok" if status == "PASS" else ("warn" if status == "WARN" else "fail")
    return f'<span class="{cls}">{status}</span>'

rows_html = "".join(
    f"<tr><td>{name}</td><td>{badge(status)}</td><td>{notes}</td></tr>"
    for name, status, notes in results
)

# Build each proof section (inline preview + download)
likely_cols = [primary_key, "email", "name", "first_name", "last_name"]

row_counts_html = df_preview(row_counts)
dups_old_html = df_preview(dups_old_df)
dups_new_html = df_preview(dups_new_df)
nulls_summary_html = df_preview(nulls_summary)
schema_cmp_html = df_preview(schema_cmp)
missing_html = df_preview(missing_in_new, cols=likely_cols)
extra_html   = df_preview(extra_in_new,   cols=likely_cols)

proof_sections = []

proof_sections.append(section_with_download(
    "Row counts (raw & adjusted)", "output/row_counts.csv", row_counts_html))

proof_sections.append(section_with_download(
    "Primary key duplicates — OLD", "output/duplicates_old.csv", dups_old_html,
    count_note=f"{len(dups_old_df)} rows"))

proof_sections.append(section_with_download(
    "Primary key duplicates — NEW", "output/duplicates_new.csv", dups_new_html,
    count_note=f"{len(dups_new_df)} rows"))

proof_sections.append(section_with_download(
    "Nulls in required fields", "output/nulls_summary.csv", nulls_summary_html))

proof_sections.append(section_with_download(
    "Schema comparison", "output/schema_comparison.csv", schema_cmp_html,
    count_note=f"{len(schema_cmp)} columns"))

# Differences only if non-empty (but still provide download sections)
if missing_count > 0 or extra_count > 0:
    proof_sections.append(section_with_download(
        "Missing in NEW (unexpected)", "output/missing_in_new.csv", missing_html,
        count_note=f"{missing_count} rows"))
    proof_sections.append(section_with_download(
        "Extra in NEW (unexpected)", "output/extra_in_new.csv", extra_html,
        count_note=f"{extra_count} rows"))
else:
    # still list as empty proofs for completeness
    proof_sections.append(section_with_download(
        "Missing in NEW (unexpected)", "output/missing_in_new.csv", "<em>None</em>", "0 rows"))
    proof_sections.append(section_with_download(
        "Extra in NEW (unexpected)", "output/extra_in_new.csv", "<em>None</em>", "0 rows"))

proofs_html = "\n".join(proof_sections)

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
    .section { margin-top: 1.25rem; }
    a { text-decoration: none; }
    .small { font-size: 0.9rem; color: #666; }
    details > summary { cursor: pointer; list-style: none; }
    details > summary::-webkit-details-marker { display: none; }
    details > summary::before { content: "▸ "; }
    details[open] > summary::before { content: "▾ "; }
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

    <div class="section">
      <h2>Proofs (inline previews + downloads)</h2>
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
    proofs_html=proofs_html,
)

out_html.write_text(html, encoding="utf-8")

print(f"Wrote: {out_html}")
print(f"Proofs saved to: {out_dir}")
