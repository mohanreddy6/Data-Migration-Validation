import pandas as pd
from pathlib import Path
from string import Template

# --- paths ---
repo_root = Path(__file__).resolve().parents[1]
old_csv = repo_root / "sample_data" / "old_customers.csv"
new_csv = repo_root / "sample_data" / "new_customers.csv"

out_dir = repo_root / "output"
out_dir.mkdir(exist_ok=True)

# HTML at repo root so GitHub Pages can serve it
out_html = repo_root / "sample-report.html"

# --- config: adjust if your columns differ ---
primary_key = "customer_id"          # <-- change if needed
required_fields = ["email"]          # <-- add more required fields if needed

# --- load ---
old_df = pd.read_csv(old_csv)
new_df = pd.read_csv(new_csv)

# normalize PK for matching (strings, trimmed)
old_pk = old_df[primary_key].astype(str).str.strip()
new_pk = new_df[primary_key].astype(str).str.strip()

# --- checks ---
results = []

# 1) Row count match
row_match = len(old_df) == len(new_df)
results.append(("Row count match", "PASS" if row_match else "FAIL",
                f"Old={len(old_df)}, New={len(new_df)}"))

# 2) Primary key duplicates
old_dups = old_pk.duplicated().sum()
new_dups = new_pk.duplicated().sum()
pk_ok = (old_dups == 0) and (new_dups == 0)
results.append(("Primary key duplicates", "PASS" if pk_ok else "FAIL",
                f"Old dupes={old_dups}, New dupes={new_dups}"))

# 3) Nulls in required fields
null_notes = []
null_ok = True
for col in required_fields:
    old_nulls = old_df[col].isna().sum() if col in old_df.columns else "col-missing"
    new_nulls = new_df[col].isna().sum() if col in new_df.columns else "col-missing"
    if isinstance(old_nulls, int) and old_nulls > 0: null_ok = False
    if isinstance(new_nulls, int) and new_nulls > 0: null_ok = False
    null_notes.append(f"{col}: Old={old_nulls}, New={new_nulls}")
results.append(("Nulls in required fields",
                "PASS" if null_ok else "WARN",
                "; ".join(null_notes)))

# --- delta: which rows differ by primary key ---
old_keys = set(old_pk)
new_keys = set(new_pk)

missing_mask = ~old_pk.isin(new_keys)     # in old, not in new
extra_mask   = ~new_pk.isin(old_keys)     # in new, not in old

missing_in_new = old_df.loc[missing_mask].copy()
extra_in_new   = new_df.loc[extra_mask].copy()

# save detailed CSVs
missing_path = out_dir / "missing_in_new.csv"
extra_path   = out_dir / "extra_in_new.csv"
missing_in_new.to_csv(missing_path, index=False)
extra_in_new.to_csv(extra_path, index=False)

# prepare preview tables (first 10 rows)
def df_html_preview(df, cols=None, n=10):
    if df.empty:
        return "<em>None</em>"
    if cols:
        cols = [c for c in cols if c in df.columns]
        if cols:
            df = df[cols]
    return df.head(n).to_html(index=False, border=0)

missing_count = len(missing_in_new)
extra_count   = len(extra_in_new)

def badge(status: str) -> str:
    cls = "ok" if status == "PASS" else ("warn" if status == "WARN" else "fail")
    return f'<span class="{cls}">{status}</span>'

rows_html = "".join(
    f"<tr><td>{name}</td><td>{badge(status)}</td><td>{notes}</td></tr>"
    for name, status, notes in results
)

# try to show PK + a couple of helpful columns in previews
likely_cols = [primary_key, "email", "name", "first_name", "last_name"]
missing_preview = df_html_preview(missing_in_new, cols=likely_cols)
extra_preview   = df_html_preview(extra_in_new,   cols=likely_cols)

# --- build HTML using string.Template (safe with CSS braces and % signs) ---
html_tpl = Template("""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Data Migration Validation Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; max-width: 1000px; }
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
  </style>
</head>
<body>
  <div class="card">
    <h1>Data Migration Validation Report</h1>
    <div class="meta">Source files: $old_name → $new_name</div>

    <table>
      <thead>
        <tr><th>Check</th><th>Status</th><th>Notes</th></tr>
      </thead>
      <tbody>
        $rows_html
      </tbody>
    </table>

    <div class="section">
      <h2>Key Differences</h2>
      <p><strong>Missing in NEW:</strong> $missing_count rows &nbsp;—&nbsp;
         <a href="output/missing_in_new.csv">download CSV</a></p>
      $missing_preview
      <p style="margin-top:1rem;"><strong>Extra in NEW:</strong> $extra_count rows &nbsp;—&nbsp;
         <a href="output/extra_in_new.csv">download CSV</a></p>
      $extra_preview
    </div>
  </div>
</body>
</html>
""")

html = html_tpl.substitute(
    old_name=old_csv.name,
    new_name=new_csv.name,
    rows_html=rows_html,
    missing_count=missing_count,
    extra_count=extra_count,
    missing_preview=missing_preview,
    extra_preview=extra_preview,
)

out_html.write_text(html, encoding="utf-8")
print(f"Wrote: {out_html}")
print(f"Missing in new: {missing_count} → {missing_path}")
print(f"Extra in new:   {extra_count} → {extra_path}")
