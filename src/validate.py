import pandas as pd
from pathlib import Path

# --- paths ---
repo_root = Path(__file__).resolve().parents[1]
old_csv = repo_root / "sample_data" / "old_customers.csv"
new_csv = repo_root / "sample_data" / "new_customers.csv"

# Output HTML must be at the REPO ROOT for the demo URL to work:
out_html = repo_root / "sample-report.html"

# --- load data ---
old_df = pd.read_csv(old_csv)
new_df = pd.read_csv(new_csv)

# --- checks (edit fields/keys to match your data) ---
primary_key = "customer_id"        # <-- change if different
required_fields = ["email"]        # <-- add more fields if needed

results = []

# 1) Row count match
row_match = len(old_df) == len(new_df)
results.append(("Row count match", "PASS" if row_match else "FAIL",
                f"Old={len(old_df)}, New={len(new_df)}"))

# 2) Primary key duplicates
old_dups = old_df[primary_key].duplicated().sum()
new_dups = new_df[primary_key].duplicated().sum()
pk_ok = (old_dups == 0) and (new_dups == 0)
results.append(("Primary key duplicates", "PASS" if pk_ok else "FAIL",
                f"Old dupes={old_dups}, New dupes={new_dups}"))

# 3) Nulls in required fields
null_notes = []
null_ok = True
for col in required_fields:
    old_nulls = old_df[col].isna().sum()
    new_nulls = new_df[col].isna().sum()
    if old_nulls or new_nulls:
        null_ok = False
    null_notes.append(f"{col}: Old={old_nulls}, New={new_nulls}")
results.append(("Nulls in required fields",
                "PASS" if null_ok else "WARN",
                "; ".join(null_notes) if null_notes else "n/a"))

# 4) Value range checks (example: ages 0–120) — edit or remove
if "age" in old_df.columns and "age" in new_df.columns:
    bad_old = ~old_df["age"].between(0, 120)
    bad_new = ~new_df["age"].between(0, 120)
    ok = (bad_old.sum() == 0) and (bad_new.sum() == 0)
    results.append(("Value range checks (age 0–120)",
                    "PASS" if ok else "FAIL",
                    f"Old out-of-range={bad_old.sum()}, New out-of-range={bad_new.sum()}"))

# --- build HTML ---
def badge(status: str) -> str:
    cls = "ok" if status == "PASS" else ("warn" if status == "WARN" else "fail")
    return f'<span class="{cls}">{status}</span>'

rows_html = "".join(
    f"<tr><td>{name}</td><td>{badge(status)}</td><td>{notes}</td></tr>"
    for name, status, notes in results
)

html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Sample Data Migration Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; max-width: 900px; }}
    h1 {{ margin-top: 0; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f6f6f6; }}
    .ok {{ color: #1a7f37; font-weight: 600; }}
    .warn {{ color: #d97706; font-weight: 600; }}
    .fail {{ color: #b91c1c; font-weight: 600; }}
    .meta {{ color: #555; margin-top: .5rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Data Migration Validation Report</h1>
    <div class="meta">Source files: {old_csv.name} → {new_csv.name}</div>
    <table>
      <thead>
        <tr><th>Check</th><th>Status</th><th>Notes</th></tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

out_html.write_text(html, encoding="utf-8")
print(f"Wrote: {out_html}")
