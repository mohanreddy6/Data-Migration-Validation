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
        if isinstance(old_row, pd.DataFrame):
            old_row = old_row.iloc[0]
        if isinstance(new_row, pd.DataFrame):
            new_row = new_row.iloc[0]
        if str(old_row.get(primary_key, "")).strip() != str(new_row.get(primary_key, "")).strip():
            rows.append({
                "email": em,
                "old_pk": str(old_row.get(primary_key, "")),
                "new_pk": str(new_row.get(primary_key, "")),
            })
    write_csv(possible_rekeys_csv, rows, fieldnames=["email", "old_pk", "new_pk"])
else:
    write_csv(possible_rekeys_csv, [], fieldnames=["email", "old_pk", "new_pk"])

# --------------------
# Manifest (reproducibility)
# --------------------
manifest = {
    "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    "system": {
        "python": platform.python_version(),
        "os": platform.platform(),
    },
    "git_commit": safe_get_git_commit(),
    "inputs": {
        "old_csv": {"path": str(old_csv), "sha256": sha256_file(old_csv)},
        "new_csv": {"path": str(new_csv), "sha256": sha256_file(new_csv)},
        "script":  {"path": str((repo_root / 'src' / 'validate.py')), "sha256": sha256_file(repo_root / 'src' / 'validate.py')},
    },
    "outputs": {
        "html": {"path": str(out_html), "sha256": None},  # filled after write
        "row_counts_csv": str(row_counts_csv),
        "duplicates_old_csv": str(duplicates_old_csv),
        "duplicates_new_csv": str(duplicates_new_csv),
        "nulls_summary_csv": str(nulls_summary_csv),
        "schema_comparison_csv": str(schema_csv),
        "missing_in_new_csv": str(missing_path),
        "extra_in_new_csv": str(extra_path),
        "possible_rekeys_csv": str(possible_rekeys_csv),
        "allowed_deletions": sorted(ALLOWED_DELETIONS),
        "allowed_additions": sorted(ALLOWED_ADDITIONS),
    }
}

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

# Differences section: show only if unexpected diffs exist
if missing_count == 0 and extra_count == 0:
    differences_section = ""
else:
    differences_section = f"""
    <div class="section">
      <h2>Key Differences</h2>
      <p><strong>Missing in NEW:</strong> {missing_count} rows &nbsp;—&nbsp;
         <a href="output/missing_in_new.csv">download CSV</a></p>
      {missing_preview}
      <p style="margin-top:1rem;"><strong>Extra in NEW:</strong> {extra_count} rows &nbsp;—&nbsp;
         <a href="output/extra_in_new.csv">download CSV</a></p>
      {extra_preview}
    </div>
    """

# Proofs section (always shown)
proof_links = [
    ('Row counts (CSV)', 'output/row_counts.csv'),
    ('Duplicates in OLD (CSV)', 'output/duplicates_old.csv'),
    ('Duplicates in NEW (CSV)', 'output/duplicates_new.csv'),
    ('Nulls summary (CSV)', 'output/nulls_summary.csv'),
    ('Schema comparison (CSV)', 'output/schema_comparison.csv'),
    ('Possible rekeys by email (CSV)', 'output/possible_rekeys.csv'),
]

proofs_html = "".join(
    f'<li><a href="{href}">{label}</a></li>' for (label, href) in proof_links
)

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
    .meta { color: #555; margin: .25rem 0 .5rem; }
    .section { margin-top: 1.5rem; }
    a { text-decoration: none; }
    .small { font-size: 0.9rem; color: #666; }
    ul { margin: .5rem 0 0 1.2rem; }
    code { background:#f6f6f6; padding:0 .25rem; border-radius:4px; }
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
      <h2>Proofs (downloadables)</h2>
      <ul>
        $proofs_html
        <li><a href="output/manifest.json">Manifest (JSON with SHA-256, env, commit)</a></li>
      </ul>
      <p class="small">Tip: open <code>manifest.json</code> to see file hashes and the exact environment used.</p>
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
manifest["outputs"]["html"]["sha256"] = sha256_file(out_html)

# Write manifest
manifest_path = out_dir / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print(f"Wrote: {out_html}")
print(f"Proofs:")
for p in [
    row_counts_csv, duplicates_old_csv, duplicates_new_csv, nulls_summary_csv,
    schema_csv, missing_path, extra_path, possible_rekeys_csv, manifest_path
]:
    print(f"  - {p.relative_to(repo_root)} (sha256={sha256_file(p)})")
