import json
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

out_html = repo_root / "sample-report.html"
# Verification config (manual sign-off)
verification_path = repo_root / "verification.json"
verification = {"checks": {}, "mismatches": []}
if verification_path.exists():
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
ver_checks = verification.get("checks", {})
ver_rows = verification.get("mismatches", [])
ver_rows_set = {(str(r.get("customer_id")), str(r.get("column")).lower())
                for r in ver_rows if r.get("verified")}



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

# row count (adjusted by allowlists)
adj_old = old_total - old_pk.isin(ALLOWED_DELETIONS).sum()
adj_new = new_total - new_pk.isin(ALLOWED_ADDITIONS).sum()
row_match = adj_old == adj_new
results.append(("Row count match", "PASS" if row_match else "FAIL",
                f"Old={old_total} (adj {adj_old}), New={new_total} (adj {adj_new})"))

# duplicate PK
old_dups_ct = old_pk.duplicated().sum()
new_dups_ct = new_pk.duplicated().sum()
pk_ok = (old_dups_ct == 0) and (new_dups_ct == 0)
results.append(("Primary key duplicates", "PASS" if pk_ok else "FAIL",
                f"Old dupes={old_dups_ct}, New dupes={new_dups_ct}"))

# nulls
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
results.append(("Nulls in required fields", "PASS" if null_ok else "WARN",
                "; ".join([f"{r['field']}: Old={r['old_nulls']}, New={r['new_nulls']}" for r in null_rows])))

# --------------------
# Membership deltas (excluding allowlists)
# --------------------
old_keys = set(old_pk)
new_keys = set(new_pk)

only_in_old_keys = (old_keys - new_keys) - ALLOWED_DELETIONS
only_in_new_keys = (new_keys - old_keys) - ALLOWED_ADDITIONS

only_in_old = old_df[old_df[primary_key].isin(only_in_old_keys)].copy()
only_in_new = new_df[new_df[primary_key].isin(only_in_new_keys)].copy()

# write CSVs
(only_in_old.sort_values(primary_key)
 .to_csv(out_dir / "only_in_old.csv", index=False))
(only_in_new.sort_values(primary_key)
 .to_csv(out_dir / "only_in_new.csv", index=False))

# for backward-compat links
only_in_old.to_csv(out_dir / "missing_in_new.csv", index=False)
only_in_new.to_csv(out_dir / "extra_in_new.csv", index=False)

# --------------------
# Cell-by-cell mismatches on intersection keys
# --------------------
# compare on keys that exist in BOTH, excluding allowlists
intersect_keys = (old_keys & new_keys) - ALLOWED_DELETIONS - ALLOWED_ADDITIONS
old_int = old_df[old_df[primary_key].isin(intersect_keys)].copy()
new_int = new_df[new_df[primary_key].isin(intersect_keys)].copy()

# ensure columns exist; keep only columns present in both
common_cols = [c for c in compare_columns if c in old_int.columns and c in new_int.columns]

merged = old_int[[primary_key] + common_cols].merge(
    new_int[[primary_key] + common_cols],
    on=primary_key, how="inner", suffixes=("_old", "_new")
)

mismatch_rows = []
for col in common_cols:
    a = merged[f"{col}_old"].fillna("")
    b = merged[f"{col}_new"].fillna("")
    diff_mask = (a != b)
    if diff_mask.any():
        tmp = merged.loc[diff_mask, [primary_key, f"{col}_old", f"{col}_new"]].copy()
        tmp.columns = [primary_key, "old_value", "new_value"]
        tmp.insert(1, "column", col)
        mismatch_rows.append(tmp)

if mismatch_rows:
    mismatches_df = pd.concat(mismatch_rows, ignore_index=True)
else:
    mismatches_df = pd.DataFrame(columns=[primary_key, "column", "old_value", "new_value"])

mismatch_count = len(mismatches_df)
mismatches_path = out_dir / "mismatches.csv"
mismatches_df.to_csv(mismatches_path, index=False)

# --------------------
# Other proof artifacts
# --------------------
# row counts proof
pd.DataFrame([
    {"dataset": "OLD", "raw_count": old_total,
     "allowlisted_ids": int(old_pk.isin(ALLOWED_DELETIONS).sum()),
     "adjusted_count": adj_old},
    {"dataset": "NEW", "raw_count": new_total,
     "allowlisted_ids": int(new_pk.isin(ALLOWED_ADDITIONS).sum()),
     "adjusted_count": adj_new},
]).to_csv(out_dir / "row_counts.csv", index=False)

# duplicates proof
def duplicate_rows(df, pk_series):
    dup_keys = pk_series[pk_series.duplicated(keep=False)]
    if dup_keys.empty:
        return pd.DataFrame(columns=df.columns)
    return df[df[primary_key].isin(set(dup_keys))].copy().sort_values(primary_key)

duplicate_rows(old_df, old_pk).to_csv(out_dir / "duplicates_old.csv", index=False)
duplicate_rows(new_df, new_pk).to_csv(out_dir / "duplicates_new.csv", index=False)

# nulls proof
pd.DataFrame(null_rows).to_csv(out_dir / "nulls_summary.csv", index=False)

# schema proof
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

# --------------------
# HTML helpers
# --------------------
def df_preview(df: pd.DataFrame, max_rows: int = INLINE_MAX_ROWS, cols=None) -> str:
    if df.empty:
        return "<em>None</em>"
    show = df if cols is None else df[[c for c in cols if c in df.columns]]
    if len(show) > max_rows:
        head = show.head(max_rows)
        html = head.to_html(index=False, border=0)
        return f'<div>{html}<div class="small">Showing first {max_rows} of {len(show)} rows</div></div>'
    return show.to_html(index=False, border=0)

def badge(status: str) -> str:
    cls = "ok" if status == "PASS" else ("warn" if status == "WARN" else "fail")
    return f'<span class="{cls}">{status}</span>'

rows_html = "".join(
    f"<tr><td>{name}</td><td>{badge(status)}</td><td>{notes}</td></tr>"
    for name, status, notes in results
)

# badge-like pills summary
pills_html = f"""
  <span class="pill">Primary key: <strong>{primary_key}</strong></span>
  <span class="pill">Columns: {', '.join(common_cols) or '—'}</span>
  <span class="pill">OLD total: <strong>{old_total}</strong></span>
  <span class="pill">NEW total: <strong>{new_total}</strong></span>
  <span class="pill">Only in OLD: <strong>{len(only_in_old)}</strong></span>
  <span class="pill">Only in NEW: <strong>{len(only_in_new)}</strong></span>
  <span class="pill">Mismatches: <strong>{mismatch_count}</strong></span>
"""

# mismatches table (first N)
mismatches_html = df_preview(mismatches_df, max_rows=INLINE_MAX_ROWS,
                             cols=[primary_key, "column", "old_value", "new_value"])

# proof sections (collapsible)
def section_dl(title, path_rel, table_html, note=""):
    small = f' <span class="small">{note}</span>' if note else ""
    return f"""
    <details class="section" open>
      <summary><strong>{title}</strong>{small} — <a href="{path_rel}">download CSV</a></summary>
      <div style="margin-top:.75rem">{table_html}</div>
    </details>
    """

proofs_html = "\n".join([
    section_dl("Row counts (raw & adjusted)", "output/row_counts.csv",
               df_preview(pd.read_csv(out_dir / "row_counts.csv"))),
    section_dl("Primary key duplicates — OLD", "output/duplicates_old.csv",
               df_preview(pd.read_csv(out_dir / "duplicates_old.csv")),
               note=f"{len(pd.read_csv(out_dir / 'duplicates_old.csv'))} rows"),
    section_dl("Primary key duplicates — NEW", "output/duplicates_new.csv",
               df_preview(pd.read_csv(out_dir / "duplicates_new.csv")),
               note=f"{len(pd.read_csv(out_dir / 'duplicates_new.csv'))} rows"),
    section_dl("Nulls in required fields", "output/nulls_summary.csv",
               df_preview(pd.read_csv(out_dir / "nulls_summary.csv"))),
    section_dl("Schema comparison", "output/schema_comparison.csv",
               df_preview(pd.read_csv(out_dir / "schema_comparison.csv")),
               note=f"{len(pd.read_csv(out_dir / 'schema_comparison.csv'))} columns"),
    section_dl("Only in OLD (unexpected)", "output/only_in_old.csv",
               df_preview(only_in_old)),
    section_dl("Only in NEW (unexpected)", "output/only_in_new.csv",
               df_preview(only_in_new)),
    section_dl("Mismatched Cells", "output/mismatches.csv",
               mismatches_html, note=f"first {min(INLINE_MAX_ROWS, mismatch_count)} of {mismatch_count}")
])

# --------------------
# HTML
# --------------------
html_tpl = Template("""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Data Migration Validation Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; color:#111; }
    .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem; max-width: 1100px; }
    h1 { margin: 0 0 1rem 0; font-size: 2.2rem; }
    .pill { display:inline-block; background:#f3f4f6; border:1px solid #e5e7eb; padding:.35rem .6rem; border-radius:999px; margin:.2rem .25rem; font-size:.95rem; }
    table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
    th, td { border: 1px solid #e5e7eb; padding: 10px; text-align: left; }
    th { background: #f9fafb; }
    .ok { color: #16a34a; font-weight: 700; }
    .warn { color: #d97706; font-weight: 700; }
    .fail { color: #dc2626; font-weight: 700; }
    .meta { color: #4b5563; margin-top: .25rem; }
    .section { margin-top: 1.25rem; }
    .small { font-size: .9rem; color:#6b7280; }
    a { text-decoration: none; color:#2563eb; }
    details > summary { cursor: pointer; list-style: none; }
    details > summary::-webkit-details-marker { display: none; }
    details > summary::before { content: "▸ "; }
    details[open] > summary::before { content: "▾ "; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Data Migration Validation Report</h1>
    <div>$pills_html</div>

    <table>
      <thead><tr><th>Check</th><th>Status</th><th>Notes</th></tr></thead>
      <tbody>$rows_html</tbody>
    </table>

    <div class="section">
      <h2>Mismatched Cells (first ${inline_cap})</h2>
      $mismatches_html
      <div class="small"><a href="output/mismatches.csv">Download full mismatches CSV</a></div>
    </div>

    <div class="section">
      <h2>Proofs (inline previews + downloads)</h2>
      $proofs_html
    </div>

    <div class="meta small">
      Exceptions applied — Allowed deletions: $allowed_deletions | Allowed additions: $allowed_additions
    </div>
  </div>
</body>
</html>
""")

html = html_tpl.substitute(
    pills_html=pills_html,
    rows_html=rows_html,
    mismatches_html=mismatches_html,
    inline_cap=INLINE_MAX_ROWS,
    proofs_html=proofs_html,
    allowed_deletions=", ".join(sorted(ALLOWED_DELETIONS)) or "None",
    allowed_additions=", ".join(sorted(ALLOWED_ADDITIONS)) or "None",
)

out_html.write_text(html, encoding="utf-8")
print(f"Wrote: {out_html}")
print(f"Mismatches: {mismatch_count} -> {mismatches_path}")
